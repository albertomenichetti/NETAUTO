# M4 WIP — Object SCHEMA_CHANGE lifecycle payload

Status: RATIFIED SCHEMA_CHANGE LIFECYCLE INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the lifecycle payload semantics ratified for:

```http
POST /api/v1/core/objects/{object_id}/schema
```

It supersedes the earlier full-intrinsic-before/after snapshot direction for SCHEMA_CHANGE.

Everything under `wip/` remains globally non-normative and does not authorize implementation.

## Governing principle

M4 uses the general lifecycle rule:

```text
lifecycle payload
    = complete exact semantic transition owned by the operation

not automatically
    = complete aggregate before snapshot
      + complete aggregate after snapshot
```

SCHEMA_CHANGE owns the transition from one exact ObjectTemplate binding to another and the concrete runtime-property changes produced by that migration.

It does not own unrelated unchanged intrinsic fields, ownership membership, Relationship state or a duplicated copy of the derived current slot materialization.

## Event cardinality

Exactly one successful real schema migration produces:

```text
kind = SCHEMA_CHANGE
```

No lifecycle event is emitted for:

```text
equal-target semantic no-op
semantic migration failure
TARGET admission failure
slot blocker failure
stale expected_revision attempt
rolled-back persistence failure
```

A successful real migration emits one event even when no runtime property value changes, because the exact binding itself changed.

## Canonical semantic payload

Conceptually:

```text
SCHEMA_CHANGE event
    object_id = O

    binding transition
        template_id = T
        source_version = VS
        target_version = VT

    changed runtime properties only
        PropertySemanticKey
            declaring_template_id
            property_name

        before
            canonical value | ABSENT

        after
            canonical value | ABSENT
```

The exact JSON/typed persistence carrier remains Lifecycle architecture/API work. The semantic information above is fixed by the SCHEMA_CHANGE owner.

`template_id` is stable across this route because SCHEMA_CHANGE changes only the exact version inside the Object's existing ObjectTemplate lineage.

## Binding transition is always historical state

For every successful real migration:

```text
source_version != target_version
```

and the lifecycle event records that exact binding transition even when:

```text
target_properties == source_properties
```

or no property transition needs to be listed.

Example:

```text
T@4 -> T@5
property_changes = []
```

is still a real SCHEMA_CHANGE event.

The exact SOURCE/TARGET versions identify the immutable schema semantics that governed the transition historically.

## Property delta contains actual runtime changes only

SCHEMA_CHANGE candidate construction already transforms the current SOURCE property map into the complete canonical TARGET property map.

During that same preparation, lifecycle material should retain only semantic properties whose runtime state actually changes.

Examples:

```text
ADD required with migration_default
    ABSENT -> canonical default

REMOVE existing property
    canonical value -> ABSENT

SCALAR -> LIST
    x -> [x]

lossless LIST -> SCALAR
    [x] -> x

exact DTV change with different canonical representation
    old canonical value -> new canonical value
```

If one continuous property has exactly the same canonical runtime value before and after migration, it is omitted from the property delta.

The lifecycle event is not a raw MigrationPlan dump and does not list schema rules that produced no runtime property-state change.

## Property semantic identity

Property history uses:

```text
PropertySemanticKey
    = (declaring_template_id, property_name)
```

Textual name equality alone does not establish continuity.

Therefore semantic replacement is represented as two distinct state transitions when runtime values exist.

Example:

```text
SOURCE
    (Device, hostname) = "srv01"

TARGET
    (Server, hostname) = "unknown"
```

records conceptually:

```text
(Device, hostname)
    "srv01" -> ABSENT

(Server, hostname)
    ABSENT -> "unknown"
```

It must not be collapsed into a false single-property transition merely because both properties use the JSON key `hostname`.

`ABSENT` is distinct from JSON `null`; runtime null is not a valid Object property state.

## Component-slot delta is not duplicated in SCHEMA_CHANGE lifecycle

SCHEMA_CHANGE atomically maintains current:

```text
object_component_slots
```

so that:

```text
MaterializedSlots(O)
    == EffectiveComponentSlots(T@V)
```

for the new exact binding.

Those rows are derived current-state materialization, not an independent semantic history authority.

The lifecycle event therefore does not duplicate a slot diff such as:

```text
slot added
slot removed
target widened
position changed
semantic slot replacement
```

The exact immutable binding transition:

```text
T@VS -> T@VT
```

is sufficient historical schema context to determine the SOURCE/TARGET effective-slot contract when model-plane history is inspected.

SCHEMA_CHANGE also does not modify current `object_components` membership on successful normal migration. REMOVE or semantic replacement with an existing edge fails instead of implicitly DETACHing/rebinding children.

Ownership history remains owned by `ATTACH_TO` / `DETACH_FROM` lifecycle events.

## Explicit exclusions

SCHEMA_CHANGE lifecycle does not duplicate:

```text
canonical_name
revision
complete properties before snapshot
complete properties after snapshot
unchanged properties
object_component_slots materialized rows
object_components / ownership membership
owner projection
Relationships
template_name
ObjectTemplate status/default/description/revision
effective-schema snapshots
```

`object_id` already identifies the event subject.

`canonical_name` is unchanged by SCHEMA_CHANGE and is not required merely for payload uniformity.

Technical `objects.revision` is concurrency/persistence metadata and is not semantic lifecycle state.

## Preparation and freshness

Lifecycle delta construction happens while applying the immutable MigrationPlan to one coherent current intrinsic Object generation:

```text
SOURCE properties from revision R
+ MigrationPlan(T, VS, VT)
    -> target_properties
    -> changed-property semantic delta
```

The prepared lifecycle material may commit only if the final intrinsic mutation succeeds against:

```text
expected_revision = R
```

If revision is stale:

```text
no Object mutation
no slot mutation
no lifecycle event
```

and a fresh attempt rebuilds any Object-dependent lifecycle delta from the new current generation.

No fingerprint/canonical-JSON/SHA mechanism is part of the current lifecycle freshness contract.

## Atomicity

For one successful real migration, these become durable atomically:

```text
Object exact target binding
canonical target properties
revision := R + 1
current object_component_slots delta
exactly one SCHEMA_CHANGE lifecycle event
```

If lifecycle persistence fails, the Object/slot migration must not commit.

If the Object/slot migration fails, no SCHEMA_CHANGE event may commit.

## Ratified rule

```text
SCHEMA_CHANGE lifecycle
    -> exactly one event for a successful real SOURCE != TARGET migration
    -> exact binding transition T@VS -> T@VT
    -> exact delta of runtime properties that actually changed
    -> property identity uses (declaring_template_id, property_name)
    -> value-vs-ABSENT preserved exactly
    -> no full intrinsic Object snapshots
    -> no derived component-slot delta duplication
    -> no ownership membership duplication
    -> no revision/canonical_name duplication
    -> equal-target no-op and failed/rolled-back attempts emit no event
```
