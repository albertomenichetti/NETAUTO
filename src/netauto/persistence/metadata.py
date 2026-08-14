"""Authoritative SQLAlchemy Core metadata for the frozen M1 schema."""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID

metadata = MetaData()

IDENTIFIER_PATTERN = r"^[a-z][a-z0-9_]{0,63}$"
NAMESPACE_PATTERN = r"^[a-z][a-z0-9_]{0,63}(\.[a-z][a-z0-9_]{0,63})*$"
PRIMITIVE_TYPES = (
    "core.string",
    "core.integer",
    "core.number",
    "core.boolean",
    "core.date",
    "core.datetime",
    "core.ip",
    "core.ip_prefix",
    "core.byte_size",
)
VERSION_STATUSES = ("DRAFT", "PUBLISHED", "DEPRECATED")
VALUE_MODES = ("SCALAR", "LIST")
EVENT_KINDS = (
    "CREATED",
    "RENAME",
    "DATA_CHANGE",
    "SCHEMA_CHANGE",
    "ATTACH_TO",
    "DETACH_FROM",
    "RELATIONSHIP_CREATED",
    "RELATIONSHIP_DELETED",
    "DELETED",
)


def _quoted(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def _identifier_check(column: str, constraint_name: str) -> CheckConstraint:
    return CheckConstraint(f"{column} ~ '{IDENTIFIER_PATTERN}'", name=constraint_name)


def _namespace_check(column: str, constraint_name: str) -> CheckConstraint:
    return CheckConstraint(
        f"length({column}) <= 255 AND {column} ~ '{NAMESPACE_PATTERN}'",
        name=constraint_name,
    )


datatypes = Table(
    "datatypes",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("namespace", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text),
    Column("default_version", Integer),
    _namespace_check("namespace", "ck_datatypes_namespace"),
    _identifier_check("name", "ck_datatypes_name"),
    CheckConstraint(
        "default_version IS NULL OR default_version > 0",
        name="ck_datatypes_default_version_positive",
    ),
    UniqueConstraint("namespace", "name", name="uq_datatypes_namespace_name"),
)

datatype_versions = Table(
    "datatype_versions",
    metadata,
    Column("datatype_id", UUID(as_uuid=True), primary_key=True),
    Column("version", Integer, primary_key=True),
    Column("revision", Integer, nullable=False),
    Column("status", Text, nullable=False),
    Column("base_type", Text, nullable=False),
    Column("constraints", JSONB, nullable=False),
    CheckConstraint("version > 0", name="ck_datatype_versions_version_positive"),
    CheckConstraint("revision > 0", name="ck_datatype_versions_revision_positive"),
    CheckConstraint(
        f"status IN ({_quoted(VERSION_STATUSES)})",
        name="ck_datatype_versions_status",
    ),
    CheckConstraint(
        f"base_type IN ({_quoted(PRIMITIVE_TYPES)})",
        name="ck_datatype_versions_base_type",
    ),
    CheckConstraint(
        "jsonb_typeof(constraints) = 'object'",
        name="ck_datatype_versions_constraints_object",
    ),
    ForeignKeyConstraint(
        ["datatype_id"],
        ["datatypes.id"],
        name="fk_datatype_versions_datatype",
        ondelete="CASCADE",
    ),
)

datatypes.append_constraint(
    ForeignKeyConstraint(
        ["id", "default_version"],
        ["datatype_versions.datatype_id", "datatype_versions.version"],
        name="fk_datatypes_default_version",
        ondelete="RESTRICT",
        use_alter=True,
    )
)

object_templates = Table(
    "object_templates",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("namespace", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text),
    Column("abstract", Boolean, nullable=False),
    Column("default_version", Integer),
    Column(
        "parent_template_id",
        UUID(as_uuid=True),
        ForeignKey(
            "object_templates.id",
            name="fk_object_templates_parent",
            ondelete="RESTRICT",
        ),
    ),
    _namespace_check("namespace", "ck_object_templates_namespace"),
    _identifier_check("name", "ck_object_templates_name"),
    CheckConstraint(
        "default_version IS NULL OR default_version > 0",
        name="ck_object_templates_default_version_positive",
    ),
    UniqueConstraint("namespace", "name", name="uq_object_templates_namespace_name"),
)

object_template_versions = Table(
    "object_template_versions",
    metadata,
    Column("template_id", UUID(as_uuid=True), primary_key=True),
    Column("version", Integer, primary_key=True),
    Column("revision", Integer, nullable=False),
    Column("status", Text, nullable=False),
    Column("parent_template_id", UUID(as_uuid=True)),
    Column("parent_version", Integer),
    CheckConstraint("version > 0", name="ck_object_template_versions_version_positive"),
    CheckConstraint(
        "revision > 0", name="ck_object_template_versions_revision_positive"
    ),
    CheckConstraint(
        f"status IN ({_quoted(VERSION_STATUSES)})",
        name="ck_object_template_versions_status",
    ),
    CheckConstraint(
        "(parent_template_id IS NULL AND parent_version IS NULL) OR "
        "(parent_template_id IS NOT NULL AND parent_version IS NOT NULL)",
        name="ck_object_template_versions_parent_pair",
    ),
    CheckConstraint(
        "parent_version IS NULL OR parent_version > 0",
        name="ck_object_template_versions_parent_version_positive",
    ),
    ForeignKeyConstraint(
        ["template_id"],
        ["object_templates.id"],
        name="fk_object_template_versions_template",
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["parent_template_id", "parent_version"],
        ["object_template_versions.template_id", "object_template_versions.version"],
        name="fk_object_template_versions_parent_version",
        ondelete="RESTRICT",
    ),
)

object_templates.append_constraint(
    ForeignKeyConstraint(
        ["id", "default_version"],
        ["object_template_versions.template_id", "object_template_versions.version"],
        name="fk_object_templates_default_version",
        ondelete="RESTRICT",
        use_alter=True,
    )
)

object_template_properties = Table(
    "object_template_properties",
    metadata,
    Column("template_id", UUID(as_uuid=True), primary_key=True),
    Column("template_version", Integer, primary_key=True),
    Column("name", Text, primary_key=True),
    Column("position", Integer, nullable=False),
    Column("datatype_id", UUID(as_uuid=True), nullable=False),
    Column("datatype_version", Integer, nullable=False),
    Column("value_mode", Text, nullable=False),
    Column("required", Boolean, nullable=False),
    Column("migration_default", JSONB),
    _identifier_check("name", "ck_object_template_properties_name"),
    CheckConstraint(
        "template_version > 0",
        name="ck_object_template_properties_template_version_positive",
    ),
    CheckConstraint(
        "datatype_version > 0",
        name="ck_object_template_properties_datatype_version_positive",
    ),
    CheckConstraint(
        "position > 0", name="ck_object_template_properties_position_positive"
    ),
    CheckConstraint(
        f"value_mode IN ({_quoted(VALUE_MODES)})",
        name="ck_object_template_properties_value_mode",
    ),
    CheckConstraint(
        "required OR migration_default IS NULL",
        name="ck_object_template_properties_optional_default",
    ),
    UniqueConstraint(
        "template_id",
        "template_version",
        "position",
        name="uq_object_template_properties_position",
    ),
    ForeignKeyConstraint(
        ["template_id", "template_version"],
        ["object_template_versions.template_id", "object_template_versions.version"],
        name="fk_object_template_properties_version",
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["datatype_id", "datatype_version"],
        ["datatype_versions.datatype_id", "datatype_versions.version"],
        name="fk_object_template_properties_datatype_version",
        ondelete="RESTRICT",
    ),
)

object_template_components = Table(
    "object_template_components",
    metadata,
    Column("template_id", UUID(as_uuid=True), primary_key=True),
    Column("template_version", Integer, primary_key=True),
    Column("name", Text, primary_key=True),
    Column("position", Integer, nullable=False),
    Column("target_template_id", UUID(as_uuid=True), nullable=False),
    _identifier_check("name", "ck_object_template_components_name"),
    CheckConstraint(
        "template_version > 0",
        name="ck_object_template_components_template_version_positive",
    ),
    CheckConstraint(
        "position > 0", name="ck_object_template_components_position_positive"
    ),
    UniqueConstraint(
        "template_id",
        "template_version",
        "position",
        name="uq_object_template_components_position",
    ),
    ForeignKeyConstraint(
        ["template_id", "template_version"],
        ["object_template_versions.template_id", "object_template_versions.version"],
        name="fk_object_template_components_version",
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["target_template_id"],
        ["object_templates.id"],
        name="fk_object_template_components_target",
        ondelete="RESTRICT",
    ),
)

relationship_definitions = Table(
    "relationship_definitions",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("symmetric", Boolean, nullable=False),
)

relationship_resolutions = Table(
    "relationship_resolutions",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("relationship_definition_id", UUID(as_uuid=True), nullable=False),
    Column("from_template_id", UUID(as_uuid=True), nullable=False),
    Column("to_template_id", UUID(as_uuid=True), nullable=False),
    Column("name", Text, nullable=False),
    _identifier_check("name", "ck_relationship_resolutions_name"),
    UniqueConstraint(
        "relationship_definition_id",
        "from_template_id",
        "to_template_id",
        "name",
        name="uq_relationship_resolutions_semantic_child",
    ),
    UniqueConstraint(
        "id",
        "relationship_definition_id",
        name="uq_relationship_resolutions_id_definition",
    ),
    ForeignKeyConstraint(
        ["relationship_definition_id"],
        ["relationship_definitions.id"],
        name="fk_relationship_resolutions_definition",
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["from_template_id"],
        ["object_templates.id"],
        name="fk_relationship_resolutions_from_template",
        ondelete="RESTRICT",
    ),
    ForeignKeyConstraint(
        ["to_template_id"],
        ["object_templates.id"],
        name="fk_relationship_resolutions_to_template",
        ondelete="RESTRICT",
    ),
)

objects = Table(
    "objects",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("canonical_name", Text, nullable=False),
    Column("template_id", UUID(as_uuid=True), nullable=False),
    Column("template_version", Integer, nullable=False),
    Column("properties", JSONB, nullable=False),
    CheckConstraint(
        "length(canonical_name) BETWEEN 1 AND 255",
        name="ck_objects_canonical_name_length",
    ),
    CheckConstraint(
        "template_version > 0", name="ck_objects_template_version_positive"
    ),
    CheckConstraint(
        "jsonb_typeof(properties) = 'object'", name="ck_objects_properties_object"
    ),
    ForeignKeyConstraint(
        ["template_id", "template_version"],
        ["object_template_versions.template_id", "object_template_versions.version"],
        name="fk_objects_template_version",
        ondelete="RESTRICT",
    ),
)

object_components = Table(
    "object_components",
    metadata,
    Column("child_object_id", UUID(as_uuid=True), primary_key=True),
    Column("parent_object_id", UUID(as_uuid=True), nullable=False),
    Column("slot_name", Text, nullable=False),
    _identifier_check("slot_name", "ck_object_components_slot_name"),
    CheckConstraint(
        "parent_object_id <> child_object_id", name="ck_object_components_not_self"
    ),
    ForeignKeyConstraint(
        ["child_object_id"],
        ["objects.id"],
        name="fk_object_components_child",
        ondelete="RESTRICT",
    ),
    ForeignKeyConstraint(
        ["parent_object_id"],
        ["objects.id"],
        name="fk_object_components_parent",
        ondelete="RESTRICT",
    ),
)

relationships = Table(
    "relationships",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("relationship_definition_id", UUID(as_uuid=True), nullable=False),
    UniqueConstraint(
        "id",
        "relationship_definition_id",
        name="uq_relationships_id_definition",
    ),
    ForeignKeyConstraint(
        ["relationship_definition_id"],
        ["relationship_definitions.id"],
        name="fk_relationships_definition",
        ondelete="RESTRICT",
    ),
)

runtime_relationship_resolutions = Table(
    "runtime_relationship_resolutions",
    metadata,
    Column("relationship_id", UUID(as_uuid=True), nullable=False),
    Column("relationship_definition_id", UUID(as_uuid=True), nullable=False),
    Column("resolution_id", UUID(as_uuid=True), primary_key=True),
    Column("from_object_id", UUID(as_uuid=True), primary_key=True),
    Column("to_object_id", UUID(as_uuid=True), primary_key=True),
    ForeignKeyConstraint(
        ["relationship_id", "relationship_definition_id"],
        ["relationships.id", "relationships.relationship_definition_id"],
        name="fk_runtime_resolutions_relationship_definition",
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["resolution_id", "relationship_definition_id"],
        [
            "relationship_resolutions.id",
            "relationship_resolutions.relationship_definition_id",
        ],
        name="fk_runtime_resolutions_resolution_definition",
        ondelete="RESTRICT",
    ),
    ForeignKeyConstraint(
        ["from_object_id"],
        ["objects.id"],
        name="fk_runtime_resolutions_from_object",
        ondelete="RESTRICT",
    ),
    ForeignKeyConstraint(
        ["to_object_id"],
        ["objects.id"],
        name="fk_runtime_resolutions_to_object",
        ondelete="RESTRICT",
    ),
)

object_lifecycle_events = Table(
    "object_lifecycle_events",
    metadata,
    Column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    ),
    Column(
        "occurred_at",
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("transaction_timestamp()"),
    ),
    Column("kind", Text, nullable=False),
    Column("object_id", UUID(as_uuid=True), nullable=False),
    Column("canonical_name", Text, nullable=False),
    Column("destination_object_id", UUID(as_uuid=True)),
    Column("destination_canonical_name", Text),
    Column("slot_declaring_template_id", UUID(as_uuid=True)),
    Column("slot_name", Text),
    Column("relationship_id", UUID(as_uuid=True)),
    Column("relationship_definition_id", UUID(as_uuid=True)),
    Column("relationship_name", Text),
    Column("before_state", JSONB),
    Column("after_state", JSONB),
    CheckConstraint(
        f"kind IN ({_quoted(EVENT_KINDS)})", name="ck_lifecycle_events_kind"
    ),
    CheckConstraint(
        "length(canonical_name) BETWEEN 1 AND 255",
        name="ck_lifecycle_events_canonical_name_length",
    ),
    CheckConstraint(
        "destination_canonical_name IS NULL OR "
        "length(destination_canonical_name) BETWEEN 1 AND 255",
        name="ck_lifecycle_events_destination_name_length",
    ),
    CheckConstraint(
        f"slot_name IS NULL OR slot_name ~ '{IDENTIFIER_PATTERN}'",
        name="ck_lifecycle_events_slot_name",
    ),
    CheckConstraint(
        f"relationship_name IS NULL OR relationship_name ~ '{IDENTIFIER_PATTERN}'",
        name="ck_lifecycle_events_relationship_name",
    ),
    CheckConstraint(
        "(kind IN ('CREATED', 'RENAME', 'DATA_CHANGE', 'SCHEMA_CHANGE', 'DELETED') "
        "AND destination_object_id IS NULL "
        "AND destination_canonical_name IS NULL "
        "AND slot_declaring_template_id IS NULL AND slot_name IS NULL "
        "AND relationship_id IS NULL AND relationship_definition_id IS NULL "
        "AND relationship_name IS NULL) OR "
        "(kind IN ('ATTACH_TO', 'DETACH_FROM') "
        "AND destination_object_id IS NOT NULL "
        "AND destination_canonical_name IS NOT NULL "
        "AND slot_declaring_template_id IS NOT NULL AND slot_name IS NOT NULL "
        "AND relationship_id IS NULL AND relationship_definition_id IS NULL "
        "AND relationship_name IS NULL AND before_state IS NULL "
        "AND after_state IS NULL) OR "
        "(kind IN ('RELATIONSHIP_CREATED', 'RELATIONSHIP_DELETED') "
        "AND destination_object_id IS NOT NULL "
        "AND destination_canonical_name IS NOT NULL "
        "AND relationship_id IS NOT NULL "
        "AND relationship_definition_id IS NOT NULL "
        "AND relationship_name IS NOT NULL "
        "AND slot_declaring_template_id IS NULL AND slot_name IS NULL "
        "AND before_state IS NULL AND after_state IS NULL)",
        name="ck_lifecycle_events_family_shape",
    ),
    CheckConstraint(
        "(kind = 'CREATED' AND before_state IS NULL AND after_state IS NOT NULL) OR "
        "(kind IN ('RENAME', 'DATA_CHANGE', 'SCHEMA_CHANGE') "
        "AND before_state IS NOT NULL AND after_state IS NOT NULL) OR "
        "(kind = 'DELETED' AND before_state IS NOT NULL AND after_state IS NULL) OR "
        "kind IN ('ATTACH_TO', 'DETACH_FROM', 'RELATIONSHIP_CREATED', "
        "'RELATIONSHIP_DELETED')",
        name="ck_lifecycle_events_state_shape",
    ),
    CheckConstraint(
        "before_state IS NULL OR jsonb_typeof(before_state) = 'object'",
        name="ck_lifecycle_events_before_state_object",
    ),
    CheckConstraint(
        "after_state IS NULL OR jsonb_typeof(after_state) = 'object'",
        name="ck_lifecycle_events_after_state_object",
    ),
)

Index(
    "ix_object_template_properties_datatype_version",
    object_template_properties.c.datatype_id,
    object_template_properties.c.datatype_version,
)
Index(
    "ix_object_template_versions_parent_version",
    object_template_versions.c.parent_template_id,
    object_template_versions.c.parent_version,
)
Index("ix_object_templates_parent", object_templates.c.parent_template_id)
Index(
    "ix_object_template_components_target",
    object_template_components.c.target_template_id,
)
Index(
    "ix_relationship_resolutions_from_template",
    relationship_resolutions.c.from_template_id,
)
Index(
    "ix_relationship_resolutions_to_template",
    relationship_resolutions.c.to_template_id,
)
Index("ix_objects_template_version", objects.c.template_id, objects.c.template_version)
Index("ix_objects_canonical_name_id", objects.c.canonical_name, objects.c.id)
Index(
    "ix_object_components_parent_slot_child",
    object_components.c.parent_object_id,
    object_components.c.slot_name,
    object_components.c.child_object_id,
)
Index(
    "ix_runtime_resolutions_from_object",
    runtime_relationship_resolutions.c.from_object_id,
)
Index(
    "ix_runtime_resolutions_to_object",
    runtime_relationship_resolutions.c.to_object_id,
)
Index(
    "ix_runtime_resolutions_relationship",
    runtime_relationship_resolutions.c.relationship_id,
)
Index("ix_relationships_definition", relationships.c.relationship_definition_id)
Index(
    "ix_lifecycle_events_occurred",
    object_lifecycle_events.c.occurred_at,
    object_lifecycle_events.c.id,
)
Index(
    "ix_lifecycle_events_object",
    object_lifecycle_events.c.object_id,
    object_lifecycle_events.c.occurred_at,
    object_lifecycle_events.c.id,
)
Index(
    "ix_lifecycle_events_destination",
    object_lifecycle_events.c.destination_object_id,
    object_lifecycle_events.c.occurred_at,
    object_lifecycle_events.c.id,
)
Index(
    "ix_lifecycle_events_relationship",
    object_lifecycle_events.c.relationship_id,
    object_lifecycle_events.c.occurred_at,
    object_lifecycle_events.c.id,
)
Index(
    "ix_lifecycle_events_definition",
    object_lifecycle_events.c.relationship_definition_id,
    object_lifecycle_events.c.occurred_at,
    object_lifecycle_events.c.id,
)
Index(
    "ix_lifecycle_events_kind",
    object_lifecycle_events.c.kind,
    object_lifecycle_events.c.occurred_at,
    object_lifecycle_events.c.id,
)
Index(
    "ix_lifecycle_events_relationship_name",
    object_lifecycle_events.c.relationship_name,
    object_lifecycle_events.c.occurred_at,
    object_lifecycle_events.c.id,
    postgresql_where=object_lifecycle_events.c.relationship_name.is_not(None),
)
