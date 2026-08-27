# M4 WIP — Object SCHEMA_CHANGE property migration semantics

Status: PARTIAL FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the Object runtime-property migration semantics frozen incrementally for `Object.SCHEMA_CHANGE` after the source/target effective-schema delta taxonomy was established.

The migration planner compares immutable exact effective schemas and identifies property continuity through:

```text
PropertySemanticKey = (declaring_template_id, property_name)
```

Name equality alone never establishes continuity.

## ADD optional property

A property whose semantic key is absent from SOURCE and present as optional in TARGET is classified as an immutable plan operation:

```text
ADD_OPTIONAL
    semantic_key
    target_name
```

Runtime effect:

```text
resulting Object property state -> key absent
```

No placeholder is materialized. In particular, Object sparse JSONB semantics forbid inventing either JSON null or an artificial empty/default value for a newly added optional property.

Example:

```text
SOURCE effective schema
    hostname required

TARGET effective schema
    hostname required
    description optional
```

```json
before = {
  "hostname": "srv01"
}
```

migrates to:

```json
after = {
  "hostname": "srv01"
}
```

No per-Object decision is required for this delta class.

## ADD required property

A property whose semantic key is absent from SOURCE and present as required in TARGET is classified as an immutable plan operation:

```text
ADD_REQUIRED
    semantic_key
    target_name
    canonical_target_migration_default
```

Runtime effect:

```text
resulting Object property state
    -> add target property with TARGET migration_default
```

Example:

```text
SOURCE effective schema
    hostname required

TARGET effective schema
    hostname required
    asset_id required
        migration_default = "unknown"
```

```json
before = {
  "hostname": "srv01"
}
```

migrates to:

```json
after = {
  "hostname": "srv01",
  "asset_id": "unknown"
}
```

The `migration_default` belongs to an exact immutable TARGET ObjectTemplateVersion and was already parsed, canonicalized and certified against its exact target DataTypeVersion/value mode as part of model publication. Object migration must therefore consume the already canonical target default; it must not re-certify that model-plane declaration for every Object.

No per-Object decision is required for this delta class.

## REMOVE property

A property whose semantic key is present in SOURCE and absent from TARGET is classified as an immutable plan operation:

```text
REMOVE
    semantic_key
    source_name
```

Runtime effect:

```text
TARGET Object property state
    -> property does not exist
```

The removal rule is independent of SOURCE requiredness.

### SOURCE optional

If the optional SOURCE value is present, it is dropped. If it is already absent in the sparse runtime state, there is nothing to remove.

```text
optional SOURCE property
    value present -> drop
    value absent  -> no runtime action
```

### SOURCE required

A valid SOURCE Object has the required value present. The value is dropped because requiredness constrains state only while that semantic property belongs to the governing schema.

```text
required SOURCE property
    -> drop
```

No archive, extras bucket, migration default or side-channel preservation is produced for removed properties.

Example:

```text
SOURCE effective schema
    hostname required
    description optional

TARGET effective schema
    hostname required
```

```json
before = {
  "hostname": "srv01",
  "description": "core server"
}
```

migrates to:

```json
after = {
  "hostname": "srv01"
}
```

The plan decision itself is deterministic from SOURCE/TARGET immutable semantics; current Object state only determines whether an optional removed JSON key happens to be present when the plan is applied.

## OPTIONAL -> REQUIRED

A continuous semantic property may change from optional in SOURCE to required in TARGET:

```text
SOURCE required = false
TARGET required = true
```

The immutable MigrationPlan can precompute the rule and carry the canonical TARGET `migration_default`, but it cannot choose the concrete branch for one Object because that depends on whether the current sparse SOURCE state contains a value.

Conceptual plan operation:

```text
OPTIONAL_TO_REQUIRED
    semantic_key
    target_name
    canonical_target_migration_default
    target value-mode / exact-DTV validation rule as applicable
```

### Current value present

If the protected current Object state contains the continuous semantic property's value, existing information is preserved.

```text
current value present
    -> preserve existing source information
    -> apply any other TARGET migration/validation rules for this same continuous property
    -> never replace it with migration_default merely because the TARGET is required
```

Example:

```text
SOURCE
    location optional

TARGET
    location required
    migration_default = "unknown"
```

```json
before = {
  "hostname": "srv01",
  "location": "rome"
}
```

migrates, assuming the existing value is admissible under all other TARGET semantics, to:

```json
after = {
  "hostname": "srv01",
  "location": "rome"
}
```

If the existing value is incompatible with another simultaneous TARGET change such as a narrower exact DataTypeVersion, the schema change fails. The migration default is not a remediation fallback for incompatible existing information.

### Current value absent

If the protected current sparse Object state does not contain the property, TARGET requiredness needs a value and the canonical TARGET `migration_default` is used.

```text
current value absent
    -> TARGET migration_default
```

Example:

```json
before = {
  "hostname": "srv01"
}
```

migrates to:

```json
after = {
  "hostname": "srv01",
  "location": "unknown"
}
```

### UoW placement

The `OPTIONAL -> REQUIRED` branch decision is explicitly a mutation-UoW responsibility.

Outside the Object lock, the immutable MigrationPlan may know:

```text
if value present -> preserve
if value absent  -> use canonical TARGET migration_default
```

but it must not decide which condition is true from an earlier unlocked Object snapshot.

The actual presence/absence test is performed only after the schema-change UoW has obtained the fresh protected current Object state. This guarantees that a concurrent property mutation cannot change presence between decision and commit.

Therefore:

```text
outside UoW / cacheable
    immutable OPTIONAL_TO_REQUIRED rule
    canonical TARGET migration_default
    compiled TARGET validation semantics

inside protected schema-change UoW
    read fresh current properties
    determine present vs absent
    preserve or default accordingly
```

The general information-preservation invariant remains:

```text
migration_default fills absence only
migration_default never overwrites existing incompatible information
```

## REQUIRED -> OPTIONAL

A continuous semantic property may change from required in SOURCE to optional in TARGET:

```text
SOURCE required = true
TARGET required = false
```

A valid SOURCE Object necessarily contains the property value. Making the property optional in TARGET relaxes the presence requirement; it does not authorize discarding information that already exists.

Frozen rule:

```text
required -> optional
    -> preserve existing SOURCE value
    -> apply any other TARGET migration/validation rules for the same semantic property
    -> never drop merely because TARGET permits absence
    -> no migration_default
```

Example:

```text
SOURCE
    location required

TARGET
    location optional
```

```json
before = {
  "hostname": "srv01",
  "location": "rome"
}
```

migrates, assuming all other TARGET semantics remain satisfied, to:

```json
after = {
  "hostname": "srv01",
  "location": "rome"
}
```

If another simultaneous TARGET delta changes how the continuous semantic property is represented, that rule is also applied. For example:

```text
SOURCE
    required SCALAR

TARGET
    optional LIST
```

preserves the information through the allowed widening:

```text
"rome" -> ["rome"]
```

Likewise, if the TARGET exact DataTypeVersion changes, the existing value must satisfy the TARGET contract after any allowed shape transformation. If it does not, schema migration fails.

The migration must not interpret optional TARGET cardinality as permission to repair incompatibility by dropping a present source value:

```text
existing value incompatible with TARGET
    -> migration failure
    -> NOT automatic absence
```

There is no migration default in TARGET because optional declarations do not carry one.

### UoW placement

The semantic plan for `REQUIRED -> OPTIONAL` is immutable and reusable, but the concrete SOURCE value is read from fresh protected Object state during the schema-change UoW together with the rest of the migration.

Unlike `OPTIONAL -> REQUIRED`, there is no normal present/absent branch to choose for valid SOURCE state: SOURCE requiredness guarantees presence. The UoW consumes that fresh value, applies any simultaneous TARGET migration rules and validates the resulting TARGET representation.

Therefore:

```text
outside UoW / cacheable
    immutable REQUIRED_TO_OPTIONAL preservation rule
    compiled TARGET transformation/validation semantics as applicable

inside protected schema-change UoW
    read fresh current value
    preserve/transform it
    validate it against TARGET
```

The information-preservation invariant is:

```text
TARGET allowing absence does not authorize loss of existing SOURCE information
```

## Same name without semantic continuity

If SOURCE and TARGET expose the same effective property name under different semantic keys, the value is never carried forward merely because the JSON key text is equal.

Example:

```text
SOURCE
    (Device, hostname)

TARGET
    (Server, hostname)
```

is:

```text
REMOVE (Device, hostname)
ADD    (Server, hostname)
```

not one continuous property.

Consequences:

```text
new TARGET property optional
    -> old semantic value is discarded
    -> TARGET property is absent

new TARGET property required
    -> old semantic value is discarded
    -> TARGET migration_default is used
```

For example, if SOURCE contains:

```json
{
  "hostname": "srv01"
}
```

but TARGET replaces `(Device, hostname)` with required `(Server, hostname)` whose migration default is `"unknown"`, the result is:

```json
{
  "hostname": "unknown"
}
```

not `"srv01"`.

This rule prevents accidental preservation across semantic-identity replacement.

## Target-state construction rule

The migration must not be implemented conceptually as an unsafe sequence of JSON-key edits where textual name collisions can accidentally transfer values across semantic identities.

The target property state is derived from TARGET semantic properties. For each TARGET semantic key, the migration plan decides whether the target state must:

```text
preserve a value from the continuous SOURCE semantic property
use the canonical TARGET migration_default
remain absent
```

SOURCE-only semantic properties are not selected into the target state.

This target-oriented construction rule makes semantic identity authoritative even when a removed SOURCE property and an added TARGET property use the same JSON field name.

## MigrationPlan consequence

These delta classes are derived from immutable SOURCE/TARGET effective schemas and can therefore be compiled into the reusable migration plan:

```text
ObjectTemplateMigrationPlanCache[
    (template_id, source_version, target_version)
]
```

Some plan operations are fully deterministic without current Object state (`ADD`, `REMOVE` semantic action). Others carry immutable rules that are applied to fresh protected per-Object state inside the schema-change UoW.

## Frozen in this increment

```text
ADD optional
    -> resulting key absent

ADD required
    -> resulting value = canonical TARGET migration_default

REMOVE optional
    -> present value dropped; absent remains absent

REMOVE required
    -> value dropped

OPTIONAL -> REQUIRED
    current value present
        -> preserve existing information
        -> validate/migrate under other TARGET deltas
        -> never fallback to migration_default if incompatible

    current value absent
        -> canonical TARGET migration_default

    presence/absence branch
        -> decided only from fresh protected Object state inside schema-change UoW

REQUIRED -> OPTIONAL
    -> preserve existing SOURCE information
    -> apply simultaneous TARGET transformation/validation rules
    -> never drop merely because TARGET permits absence
    -> incompatibility causes migration failure
    -> no migration_default
    -> concrete value consumed from fresh protected Object state in UoW

removed property
    -> no archive/extras/default/remediation behavior

same name but different PropertySemanticKey
    -> no carry-forward by name coincidence

target-state construction
    -> build from TARGET semantic properties, not naive JSON-key mutation order
```

Still to define incrementally:

```text
SCALAR -> LIST
exact DataTypeVersion change
combined deltas on one continuous semantic property
```
