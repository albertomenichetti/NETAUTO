"""Strict public HTTP adapter for intrinsic Object state and lifecycle reads."""

from datetime import datetime
from typing import Annotated, Literal, Self, cast
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response, status
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    field_serializer,
    model_validator,
)

from netauto.application.cursors import Page
from netauto.application.objects import (
    ComponentProjection,
    ObjectService,
    OwnerProjection,
)
from netauto.domain.objects import (
    DataChangeKind,
    DataChangeOperation,
    Object,
    ObjectSummary,
)
from netauto.domain.primitives import JsonValue, PrimitiveType, validate_value
from netauto.entrypoints.api.common import (
    PageLimit,
    PositiveInteger,
    StrictBody,
    validate_query,
)
from netauto.persistence.engine import RuntimeContext
from netauto.persistence.objects import (
    EventKind,
    LifecycleEvent,
    OwnershipLifecycleEvent,
    RelationshipLifecycleEvent,
)

router = APIRouter(prefix="/api/v1/core", tags=["objects"])


def _uuid_carrier(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    if not isinstance(value, str):
        raise ValueError("uuid_required")
    return UUID(value)


def _datetime_carrier(value: object) -> datetime:
    canonical = validate_value(PrimitiveType.DATETIME, value, {}, "datetime")
    return datetime.fromisoformat(str(canonical).replace("Z", "+00:00"))


BodyUUID = Annotated[UUID, BeforeValidator(_uuid_carrier)]
QueryDateTime = Annotated[datetime, BeforeValidator(_datetime_carrier), Query()]
CanonicalNameQuery = Annotated[str, Query(min_length=1, max_length=255)]
RelationshipNameQuery = Annotated[str, Query(pattern=r"^[a-z][a-z0-9_]{0,63}$")]


class ObjectCreateBody(StrictBody):
    template_id: BodyUUID
    template_version: PositiveInteger | None = None
    canonical_name: str | None = Field(default=None, min_length=1, max_length=255)
    properties: dict[str, JsonValue] | None = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def omission_is_not_null(cls, value: object) -> object:
        result: object = value
        if isinstance(value, dict):
            raw = cast(dict[object, object], value)
            for field in ("template_version", "canonical_name", "properties"):
                if field in raw and raw[field] is None:
                    raise ValueError(f"{field}_null_forbidden")
        return result


class RenameBody(StrictBody):
    canonical_name: str = Field(min_length=1, max_length=255)


class SetOperationBody(StrictBody):
    op: Literal["SET"]
    property: str
    value: JsonValue


class RemoveOperationBody(StrictBody):
    op: Literal["REMOVE"]
    property: str


OperationBody = Annotated[
    SetOperationBody | RemoveOperationBody, Field(discriminator="op")
]


class DataChangeBody(StrictBody):
    operations: list[OperationBody] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_properties(self) -> Self:
        names = [item.property for item in self.operations]
        if len(names) != len(set(names)):
            raise ValueError("duplicate_property_operation")
        return self


class SchemaChangeBody(StrictBody):
    target_version: PositiveInteger


class OwnershipBody(StrictBody):
    slot_name: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")
    child_object_id: BodyUUID


class ObjectDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    canonical_name: str
    template_id: UUID
    template_version: int
    properties: dict[str, JsonValue]


class ObjectSummaryDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    canonical_name: str
    template_id: UUID
    template_version: int


class ObjectPageDto(BaseModel):
    items: list[ObjectSummaryDto]
    next_cursor: str | None


class ComponentProjectionDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slot_declaring_template_id: UUID
    slot_name: str
    child_object_id: UUID


class ComponentPageDto(BaseModel):
    items: list[ComponentProjectionDto]
    next_cursor: str | None


class OwnerProjectionDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parent_object_id: UUID
    slot_declaring_template_id: UUID
    slot_name: str


class IntrinsicLifecycleEventBaseDto(BaseModel):
    id: UUID
    occurred_at: datetime
    object_id: UUID
    canonical_name: str

    @field_serializer("occurred_at")
    def serialize_occurred_at(self, value: datetime) -> str:
        return str(
            validate_value(
                PrimitiveType.DATETIME, value.isoformat(timespec="microseconds"), {}
            )
        )


class CreatedLifecycleEventDto(IntrinsicLifecycleEventBaseDto):
    kind: Literal["CREATED"]
    before: None
    after: ObjectDto


class ChangedLifecycleEventDto(IntrinsicLifecycleEventBaseDto):
    kind: Literal["RENAME", "DATA_CHANGE", "SCHEMA_CHANGE"]
    before: ObjectDto
    after: ObjectDto


class DeletedLifecycleEventDto(IntrinsicLifecycleEventBaseDto):
    kind: Literal["DELETED"]
    before: ObjectDto
    after: None


class OwnershipLifecycleEventDto(IntrinsicLifecycleEventBaseDto):
    kind: Literal["ATTACH_TO", "DETACH_FROM"]
    destination_object_id: UUID
    destination_canonical_name: str
    slot_declaring_template_id: UUID
    slot_name: str


class RelationshipLifecycleEventDto(IntrinsicLifecycleEventBaseDto):
    kind: Literal["RELATIONSHIP_CREATED", "RELATIONSHIP_DELETED"]
    destination_object_id: UUID
    destination_canonical_name: str
    relationship_id: UUID
    relationship_definition_id: UUID
    relationship_name: str


type LifecycleEventDto = Annotated[
    CreatedLifecycleEventDto
    | ChangedLifecycleEventDto
    | DeletedLifecycleEventDto
    | OwnershipLifecycleEventDto
    | RelationshipLifecycleEventDto,
    Field(discriminator="kind"),
]


class LifecyclePageDto(BaseModel):
    items: list[LifecycleEventDto]
    next_cursor: str | None


def _service(request: Request) -> ObjectService:
    runtime = cast(RuntimeContext, request.app.state.runtime)
    return ObjectService(runtime.uow_factory)


def _object(value: Object) -> ObjectDto:
    return ObjectDto.model_validate(value)


def _summary(value: ObjectSummary) -> ObjectSummaryDto:
    return ObjectSummaryDto.model_validate(value)


def _event(value: LifecycleEvent) -> LifecycleEventDto:
    if isinstance(value, RelationshipLifecycleEvent):
        relationship_kind = cast(
            Literal["RELATIONSHIP_CREATED", "RELATIONSHIP_DELETED"],
            value.kind.value,
        )
        return RelationshipLifecycleEventDto(
            id=value.id,
            occurred_at=value.occurred_at,
            kind=relationship_kind,
            object_id=value.object_id,
            canonical_name=value.canonical_name,
            destination_object_id=value.destination_object_id,
            destination_canonical_name=value.destination_canonical_name,
            relationship_id=value.relationship_id,
            relationship_definition_id=value.relationship_definition_id,
            relationship_name=value.relationship_name,
        )
    if isinstance(value, OwnershipLifecycleEvent):
        ownership_kind = cast(Literal["ATTACH_TO", "DETACH_FROM"], value.kind.value)
        return OwnershipLifecycleEventDto(
            id=value.id,
            occurred_at=value.occurred_at,
            kind=ownership_kind,
            object_id=value.object_id,
            canonical_name=value.canonical_name,
            destination_object_id=value.destination_object_id,
            destination_canonical_name=value.destination_canonical_name,
            slot_declaring_template_id=value.slot_declaring_template_id,
            slot_name=value.slot_name,
        )
    if value.kind is EventKind.CREATED and value.after is not None:
        return CreatedLifecycleEventDto(
            id=value.id,
            occurred_at=value.occurred_at,
            kind="CREATED",
            object_id=value.object_id,
            canonical_name=value.canonical_name,
            before=None,
            after=_object(value.after),
        )
    if value.kind in {
        EventKind.RENAME,
        EventKind.DATA_CHANGE,
        EventKind.SCHEMA_CHANGE,
    } and (value.before is not None and value.after is not None):
        changed_kind = cast(
            Literal["RENAME", "DATA_CHANGE", "SCHEMA_CHANGE"], value.kind.value
        )
        return ChangedLifecycleEventDto(
            id=value.id,
            occurred_at=value.occurred_at,
            kind=changed_kind,
            object_id=value.object_id,
            canonical_name=value.canonical_name,
            before=_object(value.before),
            after=_object(value.after),
        )
    if value.kind is EventKind.DELETED and value.before is not None:
        return DeletedLifecycleEventDto(
            id=value.id,
            occurred_at=value.occurred_at,
            kind="DELETED",
            object_id=value.object_id,
            canonical_name=value.canonical_name,
            before=_object(value.before),
            after=None,
        )
    raise RuntimeError("unsupported intrinsic lifecycle response state")


def _object_page(value: Page[ObjectSummary]) -> ObjectPageDto:
    return ObjectPageDto(
        items=[_summary(item) for item in value.items],
        next_cursor=value.next_cursor,
    )


def _event_page(value: Page[LifecycleEvent]) -> LifecyclePageDto:
    return LifecyclePageDto(
        items=[_event(item) for item in value.items],
        next_cursor=value.next_cursor,
    )


def _component(value: ComponentProjection) -> ComponentProjectionDto:
    return ComponentProjectionDto.model_validate(value)


def _component_page(value: Page[ComponentProjection]) -> ComponentPageDto:
    return ComponentPageDto(
        items=[_component(item) for item in value.items],
        next_cursor=value.next_cursor,
    )


def _owner(value: OwnerProjection | None) -> OwnerProjectionDto | None:
    return None if value is None else OwnerProjectionDto.model_validate(value)


def _operation(value: OperationBody) -> DataChangeOperation:
    if isinstance(value, SetOperationBody):
        return DataChangeOperation(DataChangeKind.SET, value.property, value.value)
    return DataChangeOperation(DataChangeKind.REMOVE, value.property)


@router.post("/objects", response_model=ObjectDto, status_code=status.HTTP_201_CREATED)
async def create_object(
    body: ObjectCreateBody, request: Request, response: Response
) -> ObjectDto:
    validate_query(request, ())
    value = await _service(request).create(
        body.template_id,
        body.template_version,
        body.canonical_name,
        cast(dict[str, object], body.properties),
    )
    response.headers["Location"] = f"/api/v1/core/objects/{value.id}"
    return _object(value)


@router.get("/objects", response_model=ObjectPageDto)
async def list_objects(
    request: Request,
    template_id: UUID | None = None,
    template_version: Annotated[PositiveInteger | None, Query()] = None,
    canonical_name: CanonicalNameQuery | None = None,
    cursor: str | None = None,
    limit: PageLimit = 100,
) -> ObjectPageDto:
    validate_query(
        request,
        ("template_id", "template_version", "canonical_name", "cursor", "limit"),
    )
    return _object_page(
        await _service(request).list_objects(
            template_id=template_id,
            template_version=template_version,
            canonical_name=canonical_name,
            cursor=cursor,
            limit=limit,
        )
    )


@router.get("/objects/{object_id}", response_model=ObjectDto)
async def get_object(object_id: UUID, request: Request) -> ObjectDto:
    validate_query(request, ())
    return _object(await _service(request).get(object_id))


@router.post("/objects/{object_id}/rename", response_model=ObjectDto)
async def rename_object(
    object_id: UUID, body: RenameBody, request: Request
) -> ObjectDto:
    validate_query(request, ())
    return _object(await _service(request).rename(object_id, body.canonical_name))


@router.post("/objects/{object_id}/data-change", response_model=ObjectDto)
async def data_change_object(
    object_id: UUID, body: DataChangeBody, request: Request
) -> ObjectDto:
    validate_query(request, ())
    return _object(
        await _service(request).data_change(
            object_id, tuple(_operation(item) for item in body.operations)
        )
    )


@router.post("/objects/{object_id}/schema-change", response_model=ObjectDto)
async def schema_change_object(
    object_id: UUID, body: SchemaChangeBody, request: Request
) -> ObjectDto:
    validate_query(request, ())
    return _object(
        await _service(request).schema_change(object_id, body.target_version)
    )


@router.post(
    "/objects/{parent_object_id}/attach", response_model=ComponentProjectionDto
)
async def attach_object(
    parent_object_id: UUID, body: OwnershipBody, request: Request
) -> ComponentProjectionDto:
    validate_query(request, ())
    return _component(
        await _service(request).attach(
            parent_object_id, body.slot_name, body.child_object_id
        )
    )


@router.post(
    "/objects/{parent_object_id}/detach", status_code=status.HTTP_204_NO_CONTENT
)
async def detach_object(
    parent_object_id: UUID, body: OwnershipBody, request: Request
) -> Response:
    validate_query(request, ())
    await _service(request).detach(
        parent_object_id, body.slot_name, body.child_object_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/objects/{parent_object_id}/components", response_model=ComponentPageDto)
async def list_object_components(
    parent_object_id: UUID,
    request: Request,
    slot_name: Annotated[str | None, Query(pattern=r"^[a-z][a-z0-9_]{0,63}$")] = None,
    cursor: str | None = None,
    limit: PageLimit = 100,
) -> ComponentPageDto:
    validate_query(request, ("slot_name", "cursor", "limit"))
    return _component_page(
        await _service(request).list_components(
            parent_object_id,
            slot_name=slot_name,
            cursor=cursor,
            limit=limit,
        )
    )


@router.get(
    "/objects/{child_object_id}/owner", response_model=OwnerProjectionDto | None
)
async def get_object_owner(
    child_object_id: UUID, request: Request
) -> OwnerProjectionDto | None:
    validate_query(request, ())
    return _owner(await _service(request).get_owner(child_object_id))


async def _lifecycle_page(
    request: Request,
    *,
    kind: EventKind | None,
    object_id: UUID | None,
    destination_object_id: UUID | None,
    relationship_id: UUID | None,
    relationship_definition_id: UUID | None,
    relationship_name: str | None,
    occurred_from: datetime | None,
    occurred_to: datetime | None,
    involving_object_id: UUID | None,
    cursor: str | None,
    limit: int,
) -> LifecyclePageDto:
    return _event_page(
        await _service(request).list_events(
            kind=kind,
            object_id=object_id,
            destination_object_id=destination_object_id,
            relationship_id=relationship_id,
            relationship_definition_id=relationship_definition_id,
            relationship_name=relationship_name,
            occurred_from=occurred_from,
            occurred_to=occurred_to,
            involving_object_id=involving_object_id,
            cursor=cursor,
            limit=limit,
        )
    )


@router.get("/lifecycle-events", response_model=LifecyclePageDto)
async def list_lifecycle_events(
    request: Request,
    kind: EventKind | None = None,
    object_id: UUID | None = None,
    destination_object_id: UUID | None = None,
    relationship_id: UUID | None = None,
    relationship_definition_id: UUID | None = None,
    relationship_name: RelationshipNameQuery | None = None,
    occurred_from: QueryDateTime | None = None,
    occurred_to: QueryDateTime | None = None,
    cursor: str | None = None,
    limit: PageLimit = 100,
) -> LifecyclePageDto:
    validate_query(
        request,
        (
            "kind",
            "object_id",
            "destination_object_id",
            "relationship_id",
            "relationship_definition_id",
            "relationship_name",
            "occurred_from",
            "occurred_to",
            "cursor",
            "limit",
        ),
    )
    return await _lifecycle_page(
        request,
        kind=kind,
        object_id=object_id,
        destination_object_id=destination_object_id,
        relationship_id=relationship_id,
        relationship_definition_id=relationship_definition_id,
        relationship_name=relationship_name,
        occurred_from=occurred_from,
        occurred_to=occurred_to,
        involving_object_id=None,
        cursor=cursor,
        limit=limit,
    )


@router.get("/objects/{object_id}/lifecycle-events", response_model=LifecyclePageDto)
async def list_object_lifecycle_events(
    object_id: UUID,
    request: Request,
    kind: EventKind | None = None,
    destination_object_id: UUID | None = None,
    relationship_id: UUID | None = None,
    relationship_definition_id: UUID | None = None,
    relationship_name: RelationshipNameQuery | None = None,
    occurred_from: QueryDateTime | None = None,
    occurred_to: QueryDateTime | None = None,
    cursor: str | None = None,
    limit: PageLimit = 100,
) -> LifecyclePageDto:
    validate_query(
        request,
        (
            "kind",
            "destination_object_id",
            "relationship_id",
            "relationship_definition_id",
            "relationship_name",
            "occurred_from",
            "occurred_to",
            "cursor",
            "limit",
        ),
    )
    return await _lifecycle_page(
        request,
        kind=kind,
        object_id=None,
        destination_object_id=destination_object_id,
        relationship_id=relationship_id,
        relationship_definition_id=relationship_definition_id,
        relationship_name=relationship_name,
        occurred_from=occurred_from,
        occurred_to=occurred_to,
        involving_object_id=object_id,
        cursor=cursor,
        limit=limit,
    )
