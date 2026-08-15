"""Complete M1 ObjectTemplate semantic application capability."""

from dataclasses import dataclass
from typing import Final, cast
from uuid import UUID, uuid4

from sqlalchemy import text

from netauto.application.cursors import Page, decode_cursor, encode_cursor
from netauto.domain.datatypes import (
    DataTypeVersion,
    VersionStatus,
    validate_qualified_name,
)
from netauto.domain.objecttemplates import (
    CreateObjectTemplateResult,
    EffectiveSchema,
    LocalComponent,
    LocalProperty,
    ObjectTemplate,
    ObjectTemplateValidationError,
    ObjectTemplateVersion,
    ObjectTemplateVersionSummary,
    ValueMode,
    resolve_effective_schema,
    validate_local_declarations,
)
from netauto.domain.primitives import (
    JsonValue,
    PrimitiveValidationError,
    validate_value,
)
from netauto.failures import ApplicationFailure, FailureClass
from netauto.persistence.datatypes import DataTypeStore
from netauto.persistence.objecttemplates import (
    ObjectTemplateDeleteReferenceError,
    ObjectTemplateQualifiedNameError,
    ObjectTemplateStore,
)
from netauto.persistence.uow import UnitOfWorkFactory

MISSING: Final = object()


@dataclass(frozen=True, slots=True)
class PropertyCandidate:
    name: str
    position: int
    datatype_id: UUID
    datatype_version: int | None
    value_mode: ValueMode
    required: bool
    migration_default: object = MISSING


@dataclass(frozen=True, slots=True)
class ComponentCandidate:
    name: str
    position: int
    target_template_id: UUID


def _not_found(template_id: UUID, version: int | None = None) -> ApplicationFailure:
    details: dict[str, JsonValue] = {
        "resource_type": "object_template"
        if version is None
        else "object_template_version",
        "id": str(template_id),
    }
    if version is not None:
        details["version"] = version
    return ApplicationFailure(
        FailureClass.NOT_FOUND,
        "resource_not_found",
        "The requested ObjectTemplate resource does not exist.",
        details,
    )


def _referenced(
    kind: str, resource_id: UUID, version: int | None = None
) -> ApplicationFailure:
    details: dict[str, JsonValue] = {"resource_type": kind, "id": str(resource_id)}
    if version is not None:
        details["version"] = version
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "referenced_resource_not_found",
        "A referenced resource does not exist.",
        details,
    )


def _semantic(
    error: ObjectTemplateValidationError | PrimitiveValidationError | ValueError,
) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.SEMANTIC_VALIDATION,
        "semantic_validation_failed",
        "The ObjectTemplate candidate is not semantically valid.",
        {
            "violations": [
                {
                    "path": getattr(error, "path", "object_template"),
                    "rule": getattr(error, "rule", str(error)),
                }
            ]
        },
    )


def _state(
    code: str, message: str, details: dict[str, JsonValue]
) -> ApplicationFailure:
    return ApplicationFailure(FailureClass.STATE_CONFLICT, code, message, details)


def _internal(message: str) -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.INTERNAL_FAILURE,
        "internal_error",
        message,
    )


class ObjectTemplateService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    @staticmethod
    def _require_draft(current: ObjectTemplateVersion, expected_revision: int) -> None:
        if current.status is not VersionStatus.DRAFT:
            raise _state(
                "lifecycle_state_conflict",
                "The operation requires a DRAFT ObjectTemplateVersion.",
                {"id": str(current.template_id), "version": current.version},
            )
        if current.revision != expected_revision:
            raise _state(
                "stale_revision",
                "The draft revision does not match the expected revision.",
                {
                    "expected_revision": expected_revision,
                    "current_revision": current.revision,
                },
            )

    @staticmethod
    def _require_published_dependency(
        dependency: ObjectTemplateVersion | DataTypeVersion,
        resource_id: UUID,
        version: int,
    ) -> None:
        if dependency.status is not VersionStatus.PUBLISHED:
            raise _state(
                "dependency_not_admissible",
                "The selected dependency version is not PUBLISHED.",
                {"id": str(resource_id), "version": version},
            )

    async def _resolve_parent(
        self,
        store: ObjectTemplateStore,
        lineage: ObjectTemplate,
        requested_version: int | None,
        current: ObjectTemplateVersion | None,
    ) -> tuple[UUID | None, int | None]:
        parent_id = lineage.parent_template_id
        if parent_id is None:
            if requested_version is not None:
                raise _semantic(
                    ObjectTemplateValidationError(
                        "parent_version", "root_parent_version_forbidden"
                    )
                )
            return None, None
        if (
            requested_version is not None
            and current is not None
            and current.parent_version == requested_version
        ):
            return parent_id, requested_version
        if requested_version is not None:
            parent = await store.admit_exact(parent_id, requested_version)
            if parent is None:
                raise _referenced(
                    "object_template_version", parent_id, requested_version
                )
            self._require_published_dependency(parent, parent_id, requested_version)
            return parent_id, requested_version
        admitted = await store.admit_default(parent_id)
        if admitted is None:
            raise _referenced("object_template", parent_id)
        _, parent = admitted
        if parent is None:
            raise _state(
                "default_version_unavailable",
                "The selected parent ObjectTemplate has no default version.",
                {"id": str(parent_id)},
            )
        self._require_published_dependency(parent, parent_id, parent.version)
        return parent_id, parent.version

    async def _resolve_properties(
        self,
        connection_store: ObjectTemplateStore,
        candidates: tuple[PropertyCandidate, ...],
        current: ObjectTemplateVersion | None,
    ) -> tuple[LocalProperty, ...]:
        datatype_store = DataTypeStore(connection_store.connection)
        current_by_name = (
            {} if current is None else {item.name: item for item in current.properties}
        )
        resolved_versions: dict[tuple[UUID, int | None], DataTypeVersion] = {}
        for candidate in sorted(
            candidates,
            key=lambda item: (
                str(item.datatype_id),
                item.datatype_version or 0,
                item.name,
            ),
        ):
            old = current_by_name.get(candidate.name)
            if (
                candidate.datatype_version is not None
                and old is not None
                and old.datatype_id == candidate.datatype_id
                and old.datatype_version == candidate.datatype_version
            ):
                existing = await datatype_store.get_version(
                    candidate.datatype_id, candidate.datatype_version
                )
                if existing is None:
                    raise _internal("A persisted DataType dependency is missing.")
                resolved_versions[
                    (candidate.datatype_id, candidate.datatype_version)
                ] = existing
                continue
            key = (candidate.datatype_id, candidate.datatype_version)
            if key in resolved_versions:
                continue
            if candidate.datatype_version is None:
                admitted = await datatype_store.admit_default(candidate.datatype_id)
                if admitted is None:
                    raise _referenced("datatype", candidate.datatype_id)
                _, selected = admitted
                if selected is None:
                    raise _state(
                        "default_version_unavailable",
                        "The selected DataType has no default version.",
                        {"id": str(candidate.datatype_id)},
                    )
            else:
                selected = await datatype_store.admit_exact(
                    candidate.datatype_id, candidate.datatype_version
                )
                if selected is None:
                    raise _referenced(
                        "datatype_version",
                        candidate.datatype_id,
                        candidate.datatype_version,
                    )
            self._require_published_dependency(
                selected, candidate.datatype_id, selected.version
            )
            resolved_versions[key] = selected

        properties: list[LocalProperty] = []
        for candidate in candidates:
            selected = resolved_versions[
                (candidate.datatype_id, candidate.datatype_version)
            ]
            raw_default = candidate.migration_default
            if candidate.required:
                if raw_default is MISSING or raw_default is None:
                    raise _semantic(
                        ObjectTemplateValidationError(
                            f"properties.{candidate.name}.migration_default",
                            "required_migration_default",
                        )
                    )
                if candidate.value_mode is ValueMode.LIST:
                    if not isinstance(raw_default, list) or not raw_default:
                        raise _semantic(
                            ObjectTemplateValidationError(
                                f"properties.{candidate.name}.migration_default",
                                "non_empty_list_required",
                            )
                        )
                    raw_items = cast(list[object], raw_default)
                    canonical: JsonValue = [
                        validate_value(
                            selected.base_type,
                            item,
                            selected.constraints,
                            f"properties.{candidate.name}.migration_default.{index}",
                        )
                        for index, item in enumerate(raw_items)
                    ]
                else:
                    canonical = validate_value(
                        selected.base_type,
                        raw_default,
                        selected.constraints,
                        f"properties.{candidate.name}.migration_default",
                    )
            else:
                if raw_default is not MISSING:
                    raise _semantic(
                        ObjectTemplateValidationError(
                            f"properties.{candidate.name}.migration_default",
                            "optional_default_must_be_absent",
                        )
                    )
                canonical = None
            properties.append(
                LocalProperty(
                    candidate.name,
                    candidate.position,
                    candidate.datatype_id,
                    selected.version,
                    candidate.value_mode,
                    candidate.required,
                    canonical,
                )
            )
        return tuple(sorted(properties, key=lambda item: item.position))

    async def _resolve_components(
        self,
        store: ObjectTemplateStore,
        candidates: tuple[ComponentCandidate, ...],
    ) -> tuple[LocalComponent, ...]:
        for target_id in sorted(
            {item.target_template_id for item in candidates}, key=str
        ):
            if not await store.lock_lineage_share(target_id):
                raise _referenced("object_template", target_id)
        return tuple(
            sorted(
                (
                    LocalComponent(item.name, item.position, item.target_template_id)
                    for item in candidates
                ),
                key=lambda item: item.position,
            )
        )

    async def _effective_chain(
        self,
        store: ObjectTemplateStore,
        leaf: ObjectTemplateVersion,
        leaf_lineage: ObjectTemplate | None = None,
    ) -> tuple[ObjectTemplateVersion, ...]:
        chain = [leaf]
        current = leaf
        seen = {leaf.template_id}
        while current.parent_template_id is not None:
            parent_id = current.parent_template_id
            parent_version = current.parent_version
            if parent_version is None or parent_id in seen:
                raise _internal(
                    "The persisted ObjectTemplate inheritance graph is invalid."
                )
            lineage = (
                leaf_lineage
                if leaf_lineage is not None and current.template_id == leaf.template_id
                else await store.get_lineage(current.template_id)
            )
            if lineage is None or lineage.parent_template_id != parent_id:
                raise _internal(
                    "A persisted exact parent pin contradicts its stable lineage."
                )
            parent = await store.get_version(parent_id, parent_version)
            if parent is None:
                raise _internal("A persisted exact parent version is missing.")
            seen.add(parent_id)
            chain.append(parent)
            current = parent
        root_lineage = (
            leaf_lineage
            if leaf_lineage is not None and current.template_id == leaf.template_id
            else await store.get_lineage(current.template_id)
        )
        if (
            root_lineage is None
            or root_lineage.parent_template_id is not None
            or current.parent_version is not None
        ):
            raise _internal("The persisted ObjectTemplate root is invalid.")
        return tuple(reversed(chain))

    async def _validate_candidate(
        self,
        store: ObjectTemplateStore,
        candidate: ObjectTemplateVersion,
        *,
        history: bool,
        leaf_lineage: ObjectTemplate | None = None,
    ) -> EffectiveSchema:
        try:
            validate_local_declarations(candidate.properties, candidate.components)
            schema = resolve_effective_schema(
                candidate.template_id,
                candidate.version,
                await self._effective_chain(store, candidate, leaf_lineage),
            )
            if history:
                for item in candidate.properties:
                    previous = await store.latest_published_property(
                        candidate.template_id, item.name
                    )
                    if previous is not None:
                        if previous.datatype_id != item.datatype_id:
                            raise ObjectTemplateValidationError(
                                f"properties.{item.name}.datatype_id",
                                "property_datatype_lineage_changed",
                            )
                        if (
                            previous.value_mode is ValueMode.LIST
                            and item.value_mode is ValueMode.SCALAR
                        ):
                            raise ObjectTemplateValidationError(
                                f"properties.{item.name}.value_mode",
                                "list_to_scalar_forbidden",
                            )
                for item in candidate.components:
                    previous_component = await store.latest_published_component(
                        candidate.template_id, item.name
                    )
                    if previous_component is not None and not await store.is_ancestor(
                        item.target_template_id, previous_component.target_template_id
                    ):
                        raise ObjectTemplateValidationError(
                            f"components.{item.name}.target_template_id",
                            "component_target_not_widened",
                        )
            return schema
        except ObjectTemplateValidationError as error:
            raise _semantic(error) from error
        except RuntimeError as error:
            raise _internal(str(error)) from error

    async def create(
        self,
        namespace: str,
        name: str,
        abstract: bool,
        description: str | None,
        parent_template_id: UUID | None,
        parent_version: int | None,
        properties: tuple[PropertyCandidate, ...],
        components: tuple[ComponentCandidate, ...],
    ) -> CreateObjectTemplateResult:
        try:
            validate_qualified_name(namespace, name, public=True)
        except ValueError as error:
            raise _semantic(error) from error
        template_id = uuid4()
        try:
            async with self._uow_factory() as uow:
                store = ObjectTemplateStore(uow.connection)
                if parent_template_id is None:
                    if parent_version is not None:
                        raise _semantic(
                            ObjectTemplateValidationError(
                                "parent_version", "parent_template_required"
                            )
                        )
                    resolved_parent = (None, None)
                else:
                    parent_lineage = await store.get_lineage(parent_template_id)
                    if parent_lineage is None:
                        raise _referenced("object_template", parent_template_id)
                    temporary = ObjectTemplate(
                        template_id,
                        namespace,
                        name,
                        description,
                        abstract,
                        parent_template_id,
                        None,
                    )
                    resolved_parent = await self._resolve_parent(
                        store, temporary, parent_version, None
                    )
                lineage = ObjectTemplate(
                    template_id,
                    namespace,
                    name,
                    description,
                    abstract,
                    resolved_parent[0],
                    None,
                )
                local_properties = await self._resolve_properties(
                    store, properties, None
                )
                local_components = await self._resolve_components(store, components)
                version = ObjectTemplateVersion(
                    template_id,
                    1,
                    1,
                    VersionStatus.DRAFT,
                    *resolved_parent,
                    local_properties,
                    local_components,
                )
                await self._validate_candidate(
                    store, version, history=False, leaf_lineage=lineage
                )
                await store.create(lineage, version)
                await uow.commit()
                return CreateObjectTemplateResult(lineage, version)
        except ObjectTemplateQualifiedNameError as error:
            raise _state(
                "qualified_name_conflict",
                "The qualified ObjectTemplate name is already in use.",
                {"namespace": namespace, "name": name},
            ) from error

    async def create_next(
        self, template_id: UUID, source_version: int
    ) -> ObjectTemplateVersion:
        async with self._uow_factory() as uow:
            store = ObjectTemplateStore(uow.connection)
            if not await store.lock_lineage_no_key(template_id):
                raise _not_found(template_id)
            source = await store.get_version(template_id, source_version)
            if source is None:
                raise _referenced(
                    "object_template_version", template_id, source_version
                )
            if source.status not in {VersionStatus.PUBLISHED, VersionStatus.DEPRECATED}:
                raise _state(
                    "version_source_conflict",
                    "The selected version is not eligible as a create-next source.",
                    {"id": str(template_id), "source_version": source_version},
                )
            created = ObjectTemplateVersion(
                template_id,
                await store.next_version(template_id),
                1,
                VersionStatus.DRAFT,
                source.parent_template_id,
                source.parent_version,
                source.properties,
                source.components,
            )
            await store.insert_version(created)
            await uow.commit()
            return created

    async def revise(
        self,
        template_id: UUID,
        version: int,
        expected_revision: int,
        parent_version: int | None,
        properties: tuple[PropertyCandidate, ...],
        components: tuple[ComponentCandidate, ...],
    ) -> ObjectTemplateVersion:
        async with self._uow_factory() as uow:
            store = ObjectTemplateStore(uow.connection)
            if not await store.lock_version_no_key(template_id, version):
                raise _not_found(template_id, version)
            lineage = await store.get_lineage(template_id)
            current = await store.get_version(template_id, version)
            if lineage is None or current is None:
                raise _not_found(template_id, version)
            self._require_draft(current, expected_revision)
            resolved_parent = await self._resolve_parent(
                store, lineage, parent_version, current
            )
            local_properties = await self._resolve_properties(
                store, properties, current
            )
            local_components = await self._resolve_components(store, components)
            candidate = ObjectTemplateVersion(
                template_id,
                version,
                current.revision + 1,
                VersionStatus.DRAFT,
                *resolved_parent,
                local_properties,
                local_components,
            )
            await self._validate_candidate(store, candidate, history=True)
            await store.replace_candidate(candidate)
            revised = await store.get_version(template_id, version)
            if revised is None:
                raise _internal("The revised ObjectTemplateVersion disappeared.")
            await uow.commit()
            return revised

    async def publish(
        self, template_id: UUID, version: int, expected_revision: int
    ) -> ObjectTemplateVersion:
        async with self._uow_factory() as uow:
            store = ObjectTemplateStore(uow.connection)
            if not await store.lock_lineage_no_key(template_id):
                raise _not_found(template_id)
            if not await store.lock_version_no_key(template_id, version):
                raise _not_found(template_id, version)
            lineage = await store.get_lineage(template_id)
            current = await store.get_version(template_id, version)
            if lineage is None or current is None:
                raise _not_found(template_id, version)
            self._require_draft(current, expected_revision)
            await self._validate_candidate(store, current, history=True)
            dependencies: list[tuple[str, UUID, int]] = [
                ("datatype", item.datatype_id, item.datatype_version)
                for item in current.properties
            ]
            if (
                current.parent_template_id is not None
                and current.parent_version is not None
            ):
                dependencies.append(
                    (
                        "object_template",
                        current.parent_template_id,
                        current.parent_version,
                    )
                )
            datatype_store = DataTypeStore(uow.connection)
            for kind, resource_id, dependency_version in sorted(
                dependencies, key=lambda item: (item[0], str(item[1]), item[2])
            ):
                dependency = (
                    await datatype_store.admit_exact(resource_id, dependency_version)
                    if kind == "datatype"
                    else await store.admit_exact(resource_id, dependency_version)
                )
                if dependency is None:
                    raise _internal("A persisted direct dependency is missing.")
                self._require_published_dependency(
                    dependency, resource_id, dependency_version
                )
            await store.set_status(template_id, version, VersionStatus.PUBLISHED)
            if lineage.default_version is None:
                await store.set_default(template_id, version)
            published = await store.get_version(template_id, version)
            if published is None:
                raise _internal("The published ObjectTemplateVersion disappeared.")
            await uow.commit()
            return published

    async def set_default(self, template_id: UUID, version: int) -> ObjectTemplate:
        async with self._uow_factory() as uow:
            store = ObjectTemplateStore(uow.connection)
            if not await store.lock_lineage_no_key(template_id):
                raise _not_found(template_id)
            target = await store.admit_exact(template_id, version)
            if target is None:
                raise _referenced("object_template_version", template_id, version)
            self._require_published_dependency(target, template_id, version)
            lineage = await store.set_default(template_id, version)
            await uow.commit()
            return lineage

    async def clear_default(self, template_id: UUID) -> ObjectTemplate:
        async with self._uow_factory() as uow:
            store = ObjectTemplateStore(uow.connection)
            if not await store.lock_lineage_no_key(template_id):
                raise _not_found(template_id)
            lineage = await store.set_default(template_id, None)
            await uow.commit()
            return lineage

    async def deprecate(self, template_id: UUID, version: int) -> ObjectTemplateVersion:
        async with self._uow_factory() as uow:
            store = ObjectTemplateStore(uow.connection)
            if not await store.lock_lineage_share(template_id):
                raise _not_found(template_id)
            if not await store.lock_version_no_key(template_id, version):
                raise _not_found(template_id, version)
            lineage = await store.get_lineage(template_id)
            current = await store.get_version(template_id, version)
            if lineage is None or current is None:
                raise _not_found(template_id, version)
            if current.status is not VersionStatus.PUBLISHED:
                raise _state(
                    "lifecycle_state_conflict",
                    "Only a PUBLISHED ObjectTemplateVersion can be deprecated.",
                    {"id": str(template_id), "version": version},
                )
            if lineage.default_version == version:
                raise _state(
                    "default_version_conflict",
                    "The current default version cannot be deprecated.",
                    {"id": str(template_id), "version": version},
                )
            if await store.has_active_child(template_id, version):
                raise _state(
                    "active_dependency_conflict",
                    "A PUBLISHED child ObjectTemplateVersion depends on this version.",
                    {"id": str(template_id), "version": version},
                )
            await store.set_status(template_id, version, VersionStatus.DEPRECATED)
            deprecated = await store.get_version(template_id, version)
            if deprecated is None:
                raise _internal("The deprecated ObjectTemplateVersion disappeared.")
            await uow.commit()
            return deprecated

    async def delete_draft(
        self, template_id: UUID, version: int, expected_revision: int
    ) -> None:
        async with self._uow_factory() as uow:
            store = ObjectTemplateStore(uow.connection)
            if not await store.lock_lineage_no_key(template_id):
                raise _not_found(template_id)
            if not await store.lock_version_update(template_id, version):
                raise _not_found(template_id, version)
            current = await store.get_version(template_id, version)
            if current is None:
                raise _not_found(template_id, version)
            self._require_draft(current, expected_revision)
            await store.delete_draft(template_id, version)
            await uow.commit()

    async def delete_lineage(self, template_id: UUID) -> None:
        async with self._uow_factory() as uow:
            store = ObjectTemplateStore(uow.connection)
            if not await store.lock_lineage_update(template_id):
                raise _not_found(template_id)
            blockers = await store.external_reference_counts(template_id)
            blockers = {key: value for key, value in blockers.items() if value}
            if blockers:
                raise _state(
                    "delete_blocked",
                    "Current references prevent ObjectTemplate deletion.",
                    {
                        "resource_type": "object_template",
                        "id": str(template_id),
                        "blockers": [
                            {"type": key, "count": value}
                            for key, value in sorted(blockers.items())
                        ],
                    },
                )
            try:
                await store.delete_lineage(template_id)
            except ObjectTemplateDeleteReferenceError as error:
                raise _state(
                    "delete_blocked",
                    "A concurrent current reference prevented ObjectTemplate deletion.",
                    {"resource_type": "object_template", "id": str(template_id)},
                ) from error
            await uow.commit()

    async def set_description(
        self, template_id: UUID, description: str | None
    ) -> ObjectTemplate:
        async with self._uow_factory() as uow:
            lineage = await ObjectTemplateStore(uow.connection).set_description(
                template_id, description
            )
            if lineage is None:
                raise _not_found(template_id)
            await uow.commit()
            return lineage

    async def get_lineage(self, template_id: UUID) -> ObjectTemplate:
        async with self._uow_factory() as uow:
            lineage = await ObjectTemplateStore(uow.connection).get_lineage(template_id)
            if lineage is None:
                raise _not_found(template_id)
            return lineage

    async def get_version(
        self, template_id: UUID, version: int
    ) -> ObjectTemplateVersion:
        async with self._uow_factory() as uow:
            await uow.connection.execute(
                text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            )
            current = await ObjectTemplateStore(uow.connection).get_version(
                template_id, version
            )
            if current is None:
                raise _not_found(template_id, version)
            return current

    async def get_effective_schema(
        self, template_id: UUID, version: int
    ) -> EffectiveSchema:
        async with self._uow_factory() as uow:
            await uow.connection.execute(
                text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            )
            store = ObjectTemplateStore(uow.connection)
            current = await store.get_version(template_id, version)
            if current is None:
                raise _not_found(template_id, version)
            return await self._validate_candidate(store, current, history=False)

    async def list_lineages(
        self,
        *,
        namespace: str | None,
        name: str | None,
        abstract: bool | None,
        parent_template_id: UUID | None,
        parent_filter_set: bool,
        cursor: str | None,
        limit: int,
    ) -> Page[ObjectTemplate]:
        filters: dict[str, JsonValue] = {
            "namespace": namespace,
            "name": name,
            "abstract": abstract,
            "parent_template_id": None
            if not parent_filter_set
            else str(parent_template_id)
            if parent_template_id is not None
            else None,
            "parent_filter_set": parent_filter_set,
        }
        after: tuple[str, str] | None = None
        if cursor is not None:
            key = decode_cursor(cursor, "object_templates", filters)
            if len(key) != 2 or not all(isinstance(item, str) for item in key):
                raise ApplicationFailure(
                    FailureClass.INVALID_REQUEST,
                    "invalid_cursor",
                    "The cursor is malformed or incompatible with this query.",
                )
            after = cast(tuple[str, str], (key[0], key[1]))
        async with self._uow_factory() as uow:
            rows = list(
                await ObjectTemplateStore(uow.connection).list_lineages(
                    namespace=namespace,
                    name=name,
                    abstract=abstract,
                    parent_template_id=parent_template_id,
                    parent_filter_set=parent_filter_set,
                    after=after,
                    limit=limit + 1,
                )
            )
        more = len(rows) > limit
        items = rows[:limit]
        next_cursor = (
            encode_cursor(
                "object_templates", filters, [items[-1].namespace, items[-1].name]
            )
            if more
            else None
        )
        return Page(items, next_cursor)

    async def list_versions(
        self,
        template_id: UUID,
        *,
        status: VersionStatus | None,
        cursor: str | None,
        limit: int,
    ) -> Page[ObjectTemplateVersionSummary]:
        filters: dict[str, JsonValue] = {
            "template_id": str(template_id),
            "status": None if status is None else status.value,
        }
        after: int | None = None
        if cursor is not None:
            key = decode_cursor(cursor, "object_template_versions", filters)
            if len(key) != 1 or isinstance(key[0], bool) or not isinstance(key[0], int):
                raise ApplicationFailure(
                    FailureClass.INVALID_REQUEST,
                    "invalid_cursor",
                    "The cursor is malformed or incompatible with this query.",
                )
            after = key[0]
        async with self._uow_factory() as uow:
            store = ObjectTemplateStore(uow.connection)
            if await store.get_lineage(template_id) is None:
                raise _not_found(template_id)
            rows = list(
                await store.list_versions(
                    template_id, status=status, after=after, limit=limit + 1
                )
            )
        more = len(rows) > limit
        items = rows[:limit]
        next_cursor = (
            encode_cursor("object_template_versions", filters, [items[-1].version])
            if more
            else None
        )
        return Page(items, next_cursor)
