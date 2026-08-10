"""Pydantic DTOs for relationship definition REST endpoints."""

from uuid import UUID

from pydantic import StrictStr

from netauto.api.schemas.objecttemplates import ApiModel


class CreateRelationshipDefinitionRequest(ApiModel):
    source_template_id: UUID
    target_template_id: UUID
    forward_name: StrictStr
    reverse_name: StrictStr


class RelationshipDefinitionResponse(ApiModel):
    id: UUID
    source_template_id: UUID
    target_template_id: UUID
    forward_name: str
    reverse_name: str
