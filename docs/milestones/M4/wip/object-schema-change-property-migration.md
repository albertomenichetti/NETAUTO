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

This rule prevents accidental preservation across semantic-identity replacement.

## MigrationPlan consequence

These delta classes are completely deterministic from immutable SOURCE/TARGET effective schemas and can therefore be compiled once into the reusable migration plan:

```text
ObjectTemplateMigrationPlanCache[
    (template_id, source_version, target_version)
]
```

For the classes frozen in this note, the plan needs no current Object property state to decide the action. Current state is only needed later when applying the full plan atomically to a specific Object.

## Frozen in this increment

```text
ADD optional
    -> resulting key absent

ADD required
    -> resulting value = canonical TARGET migration_default

same name but different PropertySemanticKey
    -> no carry-forward by name coincidence
```

Still to define incrementally:

```text
REMOVE property
optional -> required
required -> optional
SCALAR -> LIST
exact DataTypeVersion change
combined deltas on one continuous semantic property
```
