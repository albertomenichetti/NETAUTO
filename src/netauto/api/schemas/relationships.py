"""Pydantic DTOs for relationship definition and runtime relationship REST endpoints."""

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


class CreateRelationshipRequest(ApiModel):
    relationship_definition_id: UUID
    source_object_id: UUID
    target_object_id: UUID


class RelationshipResponse(ApiModel):
    id: UUID
    relationship_definition_id: UUID
    source_object_id: UUID
    target_object_id: UUID


class EffectiveRelationshipDefinitionResponse(ApiModel):
    relationship_definition_id: UUID
    direction: StrictStr
    name: str
    related_template_id: UUID


class RelationshipNavigationResponse(ApiModel):
    relationship_id: UUID
    relationship_definition_id: UUID
    source_object_id: UUID
    target_object_id: UUID
    direction: StrictStr
    name: str
    related_object_id: UUID
