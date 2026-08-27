# M4 WIP — Object SCHEMA_CHANGE delta taxonomy

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the agreed taxonomy of schema differences that may exist between the exact source and target ObjectTemplateVersion of one `Object.SCHEMA_CHANGE`.

It is intentionally defined before the migration execution path. Its purpose is to state what kinds of effective-schema delta the migration planner must understand, independently of how runtime Object state is later transformed or admitted.

## Comparison scope

`Object.SCHEMA_CHANGE` is a forward migration inside one stable ObjectTemplate lineage:

```text
source = (template_id, source_version)
target = (template_id, target_version)
target_version > source_version
```

The migration planner compares only:

```text
SOURCE exact effective schema
vs
TARGET exact effective schema
```

It does not traverse or execute intermediate ObjectTemplateVersions as an artificial migration chain.

For example:

```text
Object currently bound to Server v3
caller requests Server v7

planner compares:
    effective(Server,v3)
    vs
    effective(Server,v7)

planner does NOT execute:
    v3 -> v4 -> v5 -> v6 -> v7
```

Intermediate version history may explain how the model evolved, but it is not part of the runtime schema-change algorithm.

## Semantic identity

Property continuity is based on:

```text
PropertySemanticKey = (declaring_template_id, property_name)
```

Component-slot continuity is based on:

```text
SlotSemanticKey = (declaring_template_id, slot_name)
```

Name equality alone does not establish continuity.

Example:

```text
SOURCE effective member:
    (Device, hostname)

TARGET effective member:
    (Server, hostname)
```

is classified as:

```text
REMOVE (Device, hostname)
ADD    (Server, hostname)
```

not as mutation of one property merely because the effective name is identical.

Remove/re-add by the same declaring lineage retains the same historical semantic identity and therefore does not reset the evolution rules associated with that member.

# Allowed ObjectTemplateVersion deltas

## Properties

### Add optional property

Allowed.

```text
SOURCE: absent
TARGET: property required=false
```

Optional properties have no `migration_default`.

### Add required property

Allowed.

```text
SOURCE: absent
TARGET: property required=true
```

The target declaration must contain a valid `migration_default` matching its exact DataTypeVersion and value mode.

### Remove optional property

Allowed.

A previously published property may be absent from a later version.

### Remove required property

Allowed.

`required` constrains Object state while the property belongs to the effective schema; it does not prevent a later ObjectTemplateVersion from removing that property.

### Optional -> required

Allowed.

The target required declaration must contain a valid `migration_default`.

### Required -> optional

Allowed.

The target optional declaration must not contain a `migration_default`.

### SCALAR -> LIST

Allowed normal evolution.

This is the current monotonic value-mode widening supported after publication.

### LIST -> SCALAR

Not allowed by normal ObjectTemplate evolution.

It requires a future explicit controlled migration capability and therefore is outside the current M4 normal evolution contract.

### Change exact DataTypeVersion

Allowed, provided the property remains bound to the same stable `datatype_id` lineage and the target exact DataTypeVersion satisfies normal model-plane admission.

Therefore the atomic value domain may become wider, narrower or otherwise different through a new exact constraint snapshot.

### Change DataType lineage

Not allowed by normal evolution after the property has been published.

`datatype_id` is stable historical property identity state.

Cross-DataType-lineage migration requires a future explicit controlled migration capability.

### Change PrimitiveType

Not allowed.

All versions of one DataType lineage use the same PrimitiveType, and normal property evolution cannot change DataType lineage.

### Change requiredness

Allowed in either direction, subject to the target `migration_default` rules described above.

### Change migration_default

Allowed when the declaration is required, provided the new default is canonical and valid under the exact target DataTypeVersion/value mode.

Optional declarations must not have a migration default.

### Change position

Allowed.

`position` is ordering/presentation state and does not define runtime semantic identity.

### Rename property

Not allowed after first publication.

The name is stable historical semantic identity state.

### Remove and later re-add same property

Allowed, but when the same declaring lineage re-adds the same name it is the same historical semantic property.

Remove/re-add cannot reset stable `datatype_id`, the SCALAR->LIST monotonicity rule, or other historical evolution constraints.

## Component slots

### Add component slot

Allowed.

A component slot is always a `0..N` ownership slot.

### Remove component slot

Allowed.

Model-plane publication may remove a slot even while older-version Objects still have ownership edges through that slot. Those Objects remain pinned to their older exact schema until explicitly migrated.

### Widen component target toward an ancestor lineage

Allowed normal evolution.

Example:

```text
SOURCE target = LinuxServer
TARGET target = Server
```

The target accepts a superset of stable child lineages.

### Narrow component target toward a descendant lineage

Not allowed by normal evolution.

It may invalidate currently admissible ownership state and requires a future explicit controlled workflow.

### Change component target to unrelated lineage

Not allowed by normal evolution for the same reason.

### Change position

Allowed.

It is ordering/presentation state only.

### Rename component slot

Not allowed after first publication.

The name is stable historical semantic identity state.

### Remove and later re-add same slot

Allowed, but when reintroduced by the same declaring lineage under the same name it retains the same historical semantic identity and target-evolution history.

Remove/re-add cannot bypass normal target-widening constraints.

# Inheritance-driven effective delta

The stable ObjectTemplate parent lineage cannot change through normal evolution:

```text
parent_template_id = stable lineage state
```

However each exact ObjectTemplateVersion may pin a different exact parent version:

```text
SOURCE Server v4 -> Device v2
TARGET Server v5 -> Device v3
```

Therefore the effective schema may change even when `Server` itself has no relevant local declaration change.

Any effective property/component delta introduced through a different exact parent-version pin is classified using exactly the same semantic-key taxonomy above.

The migration planner must not distinguish between:

```text
local delta
inherited delta
```

when deciding runtime continuity. It compares the two complete exact effective schemas.

# Stable lineage fields that do not vary between versions

The following ObjectTemplate lineage state is not an exact-version delta under normal operation:

```text
id
namespace
name
abstract
parent_template_id
```

`description` and `default_version` may change at lineage level but are not part of Object runtime exact-schema semantics and are irrelevant to Object SCHEMA_CHANGE state migration.

# Frozen delta classes for MigrationPlan

The M4 migration planner must be able to reason about at least the following effective-schema delta classes:

```text
PROPERTY
    ADD optional
    ADD required
    REMOVE optional
    REMOVE required
    optional -> required
    required -> optional
    SCALAR -> LIST
    exact DataTypeVersion change
    migration_default change
    position change
    semantic-identity replacement

COMPONENT SLOT
    ADD
    REMOVE
    target widening
    position change
    semantic-identity replacement

INHERITANCE
    different exact parent-version pin
        -> translated into the same effective property/slot deltas above
```

The following are not normal source/target deltas admitted by the current model contract:

```text
PROPERTY
    LIST -> SCALAR
    datatype_id change
    property rename

COMPONENT SLOT
    target narrowing
    unrelated target migration
    slot rename

OBJECT TEMPLATE LINEAGE
    parent_template_id change
    abstract change
    lineage rename/reclassification
```

# Consequence for Object.SCHEMA_CHANGE design

The runtime migration algorithm must be derived from:

```text
source exact effective schema
+
target exact effective schema
+
semantic member identity
+
fresh protected Object/runtime ownership state
```

It must not be derived from:

```text
version-number adjacency
intermediate version traversal
local declarations alone
name equality alone
current ObjectTemplate/DataType defaults
```

This taxonomy is now a frozen discovery input for the next step: define, delta class by delta class, what Object property state and current ownership state must do during migration.