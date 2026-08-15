"""RelationshipDefinition model-plane application capability."""

from uuid import UUID

from netauto.application.cursors import Page, decode_cursor, encode_cursor
from netauto.domain.primitives import JsonValue
from netauto.domain.relationships import (
    RelationshipCapability,
    RelationshipDefinition,
    RelationshipDefinitionValidationError,
    RelationshipPerspective,
    ResolutionRename,
    first_conflict,
    new_non_symmetric_definition,
    new_symmetric_definition,
    rename_non_symmetric,
    rename_symmetric,
    semantic_signature,
    validate_definition,
    validate_lineage_graph,
)
from netauto.failures import ApplicationFailure, FailureClass
from netauto.persistence.gates import AdvisoryGate, acquire_advisory_gate
from netauto.persistence.objecttemplates import ObjectTemplateStore
from netauto.persistence.relationships import (
    RelationshipDefinitionDeleteReferenceError,
    RelationshipDefinitionStore,
    RelationshipEndpointReferenceError,
)
from netauto.persistence.uow import UnitOfWorkFactory


def _not_found(definition_id: UUID) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.NOT_FOUND,
        "resource_not_found",
        "The requested RelationshipDefinition does not exist.",
        {"resource_type": "relationship_definition", "id": str(definition_id)},
    )


def _template_not_found(template_id: UUID) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.NOT_FOUND,
        "resource_not_found",
        "The requested ObjectTemplate does not exist.",
        {"resource_type": "object_template", "id": str(template_id)},
    )


def _referenced_template(template_id: UUID | None = None) -> ApplicationFailure:
    details: dict[str, JsonValue] = {"resource_type": "object_template"}
    if template_id is not None:
        details["id"] = str(template_id)
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "referenced_resource_not_found",
        "A referenced ObjectTemplate lineage does not exist.",
        details,
    )


def _semantic(error: RelationshipDefinitionValidationError) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "semantic_validation_failed",
        "The RelationshipDefinition candidate is not semantically valid.",
        {"violations": [{"path": error.path, "rule": error.rule}]},
    )


def _state(
    code: str, message: str, details: dict[str, JsonValue]
) -> ApplicationFailure:
    return ApplicationFailure(FailureClass.STATE_CONFLICT, code, message, details)


def _internal(message: str) -> ApplicationFailure:
    return ApplicationFailure(FailureClass.INTERNAL_FAILURE, "internal_error", message)


def _validate_persisted(value: RelationshipDefinition) -> None:
    try:
        validate_definition(value)
    except RelationshipDefinitionValidationError as error:
        raise _internal(
            "A persisted RelationshipDefinition aggregate is invalid."
        ) from error


class RelationshipDefinitionService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def _certify(
        self,
        store: RelationshipDefinitionStore,
        candidate: RelationshipDefinition,
        *,
        create_operands: bool,
    ) -> None:
        certified = await store.certified_set()
        parent_by_id = await store.lineage_parents()
        try:
            validate_lineage_graph(parent_by_id)
        except RelationshipDefinitionValidationError as error:
            raise _internal(
                "The persisted ObjectTemplate ancestry graph is invalid."
            ) from error
        for existing in certified:
            _validate_persisted(existing)
            for resolution in existing.resolutions:
                if (
                    resolution.from_template_id not in parent_by_id
                    or resolution.to_template_id not in parent_by_id
                ):
                    raise _internal(
                        "A persisted RelationshipDefinition endpoint is missing."
                    )

        for resolution in candidate.resolutions:
            for template_id in (
                resolution.from_template_id,
                resolution.to_template_id,
            ):
                if template_id not in parent_by_id:
                    if create_operands:
                        raise _referenced_template(template_id)
                    raise _internal(
                        "A persisted RelationshipDefinition endpoint is missing."
                    )

        candidate_signature = semantic_signature(candidate)
        for existing in certified:
            if existing.id == candidate.id:
                continue
            if semantic_signature(existing) == candidate_signature:
                raise _state(
                    "relationship_definition_equivalent",
                    "An equivalent RelationshipDefinition already exists.",
                    {"relationship_definition_id": str(existing.id)},
                )

        try:
            for existing in certified:
                if existing.id == candidate.id:
                    continue
                conflict = first_conflict(candidate, existing, parent_by_id)
                if conflict is not None:
                    candidate_resolution, _ = conflict
                    raise _state(
                        "relationship_definition_conflict",
                        "A RelationshipDefinition Resolution conflicts with the "
                        "certified set.",
                        {
                            "relationship_definition_id": str(existing.id),
                            "name": candidate_resolution.name,
                        },
                    )
        except RelationshipDefinitionValidationError as error:
            raise _internal(
                "The persisted ObjectTemplate ancestry graph is invalid."
            ) from error

    async def create_non_symmetric(
        self,
        perspectives: tuple[RelationshipPerspective, RelationshipPerspective],
    ) -> RelationshipDefinition:
        try:
            candidate = new_non_symmetric_definition(perspectives)
        except RelationshipDefinitionValidationError as error:
            raise _semantic(error) from error
        return await self._create(candidate)

    async def create_symmetric(
        self, endpoint_template_ids: tuple[UUID, UUID], name: str
    ) -> RelationshipDefinition:
        try:
            candidate = new_symmetric_definition(endpoint_template_ids, name)
        except RelationshipDefinitionValidationError as error:
            raise _semantic(error) from error
        return await self._create(candidate)

    async def _create(
        self, candidate: RelationshipDefinition
    ) -> RelationshipDefinition:
        async with self._uow_factory() as uow:
            await acquire_advisory_gate(
                uow.connection,
                AdvisoryGate.RELATIONSHIP_DEFINITION_CONFLICT_GATE,
            )
            store = RelationshipDefinitionStore(uow.connection)
            await self._certify(store, candidate, create_operands=True)
            try:
                await store.insert(candidate)
            except RelationshipEndpointReferenceError as error:
                raise _referenced_template(error.template_id) from error
            await uow.commit()
            return candidate

    async def rename_non_symmetric(
        self,
        definition_id: UUID,
        updates: tuple[ResolutionRename, ResolutionRename],
    ) -> RelationshipDefinition:
        return await self._rename(definition_id, updates=updates, name=None)

    async def rename_symmetric(
        self, definition_id: UUID, name: str
    ) -> RelationshipDefinition:
        return await self._rename(definition_id, updates=None, name=name)

    async def _rename(
        self,
        definition_id: UUID,
        *,
        updates: tuple[ResolutionRename, ResolutionRename] | None,
        name: str | None,
    ) -> RelationshipDefinition:
        async with self._uow_factory() as uow:
            store = RelationshipDefinitionStore(uow.connection)
            if not await store.lock_no_key(definition_id):
                raise _not_found(definition_id)
            current = await store.get(definition_id)
            if current is None:
                raise _internal(
                    "A locked RelationshipDefinition aggregate could not be loaded."
                )
            _validate_persisted(current)
            try:
                if updates is not None:
                    candidate = rename_non_symmetric(current, updates)
                elif name is not None:
                    candidate = rename_symmetric(current, name)
                else:
                    raise RuntimeError("rename candidate is missing")
            except RelationshipDefinitionValidationError as error:
                raise _semantic(error) from error

            await acquire_advisory_gate(
                uow.connection,
                AdvisoryGate.RELATIONSHIP_DEFINITION_CONFLICT_GATE,
            )
            await self._certify(store, candidate, create_operands=False)
            try:
                await store.update_names(candidate)
            except RuntimeError as error:
                raise _internal(
                    "The complete RelationshipDefinition rename could not be applied."
                ) from error
            await uow.commit()
            return candidate

    async def delete(self, definition_id: UUID) -> None:
        async with self._uow_factory() as uow:
            store = RelationshipDefinitionStore(uow.connection)
            if not await store.lock_update(definition_id):
                raise _not_found(definition_id)
            current = await store.get(definition_id)
            if current is None:
                raise _internal(
                    "A locked RelationshipDefinition aggregate could not be loaded."
                )
            _validate_persisted(current)
            relationship_count = await store.current_relationship_count(definition_id)
            if relationship_count:
                raise _state(
                    "delete_blocked",
                    "Current Relationships prevent RelationshipDefinition deletion.",
                    {
                        "resource_type": "relationship_definition",
                        "id": str(definition_id),
                        "blockers": [
                            {"type": "relationship", "count": relationship_count}
                        ],
                    },
                )
            try:
                await store.delete(definition_id)
            except RelationshipDefinitionDeleteReferenceError as error:
                raise _state(
                    "delete_blocked",
                    "A concurrent current Relationship prevented deletion.",
                    {
                        "resource_type": "relationship_definition",
                        "id": str(definition_id),
                        "blockers": [{"type": "relationship", "count": 1}],
                    },
                ) from error
            await uow.commit()

    async def get(self, definition_id: UUID) -> RelationshipDefinition:
        async with self._uow_factory.coherent_read() as uow:
            value = await RelationshipDefinitionStore(uow.connection).get(definition_id)
            if value is None:
                raise _not_found(definition_id)
            _validate_persisted(value)
            return value

    async def list_definitions(
        self, *, cursor: str | None, limit: int
    ) -> Page[RelationshipDefinition]:
        filters: dict[str, JsonValue] = {}
        after: UUID | None = None
        if cursor is not None:
            key = decode_cursor(cursor, "relationship_definitions", filters)
            if len(key) != 1 or not isinstance(key[0], str):
                raise ApplicationFailure(
                    FailureClass.INVALID_REQUEST,
                    "invalid_cursor",
                    "The cursor is malformed or incompatible with this query.",
                )
            try:
                after = UUID(key[0])
            except ValueError as error:
                raise ApplicationFailure(
                    FailureClass.INVALID_REQUEST,
                    "invalid_cursor",
                    "The cursor is malformed or incompatible with this query.",
                ) from error
        async with self._uow_factory.coherent_read() as uow:
            rows = list(
                await RelationshipDefinitionStore(uow.connection).list_definitions(
                    after=after, limit=limit + 1
                )
            )
            for item in rows:
                _validate_persisted(item)
        more = len(rows) > limit
        items = rows[:limit]
        next_cursor = (
            encode_cursor("relationship_definitions", filters, [str(items[-1].id)])
            if more
            else None
        )
        return Page(items, next_cursor)

    async def list_capabilities(
        self,
        template_id: UUID,
        *,
        name: str | None,
        cursor: str | None,
        limit: int,
    ) -> Page[RelationshipCapability]:
        filters: dict[str, JsonValue] = {
            "template_id": str(template_id),
            "name": name,
        }
        after: UUID | None = None
        if cursor is not None:
            key = decode_cursor(cursor, "relationship_capabilities", filters)
            if len(key) != 1 or not isinstance(key[0], str):
                raise ApplicationFailure(
                    FailureClass.INVALID_REQUEST,
                    "invalid_cursor",
                    "The cursor is malformed or incompatible with this query.",
                )
            try:
                after = UUID(key[0])
            except ValueError as error:
                raise ApplicationFailure(
                    FailureClass.INVALID_REQUEST,
                    "invalid_cursor",
                    "The cursor is malformed or incompatible with this query.",
                ) from error

        async with self._uow_factory.coherent_read() as uow:
            template_store = ObjectTemplateStore(uow.connection)
            current = await template_store.get_lineage(template_id)
            if current is None:
                raise _template_not_found(template_id)
            ancestors: list[UUID] = []
            seen: set[UUID] = set()
            while True:
                if current.id in seen:
                    raise _internal(
                        "The persisted ObjectTemplate inheritance graph is invalid."
                    )
                seen.add(current.id)
                ancestors.append(current.id)
                if current.parent_template_id is None:
                    break
                parent = await template_store.get_lineage(current.parent_template_id)
                if parent is None:
                    raise _internal(
                        "The persisted ObjectTemplate inheritance graph is invalid."
                    )
                current = parent
            rows = list(
                await RelationshipDefinitionStore(uow.connection).list_capabilities(
                    applicable_from_template_ids=ancestors,
                    name=name,
                    after=after,
                    limit=limit + 1,
                )
            )
        more = len(rows) > limit
        items = rows[:limit]
        next_cursor = (
            encode_cursor(
                "relationship_capabilities", filters, [str(items[-1].resolution_id)]
            )
            if more
            else None
        )
        return Page(items, next_cursor)
