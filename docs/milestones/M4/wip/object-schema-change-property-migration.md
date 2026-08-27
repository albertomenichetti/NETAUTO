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

These delta classes are deterministic from immutable SOURCE/TARGET effective schemas and can therefore be compiled once into the reusable migration plan:

```text
ObjectTemplateMigrationPlanCache[
    (template_id, source_version, target_version)
]
```

For the classes frozen in this note, the plan does not need current Object property state to decide the semantic action. Current state is needed later only to apply the complete plan atomically to a specific Object.

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

removed property
    -> no archive/extras/default/remediation behavior

same name but different PropertySemanticKey
    -> no carry-forward by name coincidence

target-state construction
    -> build from TARGET semantic properties, not naive JSON-key mutation order
```

Still to define incrementally:

```text
optional -> required
required -> optional
SCALAR -> LIST
exact DataTypeVersion change
combined deltas on one continuous semantic property
```
