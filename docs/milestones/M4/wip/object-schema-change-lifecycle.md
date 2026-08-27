# M4 WIP — Object SCHEMA_CHANGE lifecycle payload

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note freezes the lifecycle payload construction for:

```http
POST /api/v1/core/objects/{object_id}/schema
```

## Event cardinality

A successful Object schema migration produces exactly one intrinsic lifecycle event:

```text
kind = SCHEMA_CHANGE
```

A failed or rolled-back migration produces no lifecycle event.

## Historical snapshot shape

`SCHEMA_CHANGE` stores the complete canonical intrinsic Object snapshot before and after the migration.

The historical snapshot contains exactly:

```text
id
canonical_name
template_id
template_version
properties
```

It deliberately excludes enriched/current projections and unrelated aggregates:

```text
components
owner
relationships
effective schema
template_name
ObjectTemplate status/revision/description/default
```

Ownership history remains represented by ATTACH/DETACH lifecycle events rather than being copied into intrinsic SCHEMA_CHANGE snapshots.

## before_state

`before_state` is derived directly from the coherent preparatory Object aggregate snapshot `S`:

```text
before_state
    id               = S.id
    canonical_name   = S.canonical_name
    template_id      = S.template_id
    template_version = S.template_version
    properties       = S.properties
```

Conceptual example:

```json
{
  "id": "server-id",
  "canonical_name": "server-1",
  "template_id": "server-template-id",
  "template_version": 4,
  "properties": {
    "hostname": "srv01"
  }
}
```

## after_state

`after_state` is constructed during preparation from the same stable identity/display metadata plus the already-prepared target binding and canonical target properties:

```text
after_state
    id               = S.id
    canonical_name   = S.canonical_name
    template_id      = S.template_id
    template_version = target_version
    properties       = target_properties
```

Conceptual example:

```json
{
  "id": "server-id",
  "canonical_name": "server-1",
  "template_id": "server-template-id",
  "template_version": 5,
  "properties": {
    "hostname": "srv01",
    "environment": "production"
  }
}
```

## Preparation-time construction

Both historical snapshots are fully materialized before entering the short mutation UoW:

```text
S
    -> lifecycle_before

S + target_version + target_properties
    -> lifecycle_after
```

No lifecycle-state reconstruction is performed after the protected fingerprint check.

A successful preparation therefore conceptually carries:

```text
PreparedSchemaChange
    object_id
    canonical_name

    template_id
    source_version
    target_version

    expected_object_fingerprint

    target_properties

    lifecycle_before
    lifecycle_after
```

`canonical_name` is included explicitly because it is also persisted as historical display metadata on the lifecycle row.

## Why preparation-time snapshots are safe

The agreed whole-Object aggregate fingerprint covers intrinsic Object state including:

```text
id
canonical_name
template_id
template_version
properties
```

plus the complete outgoing ownership facts used by SCHEMA_CHANGE admission.

Therefore a concurrent intrinsic mutation such as:

```text
RENAME server-1 -> server-prod-1
```

changes the protected aggregate fingerprint.

If the current protected fingerprint differs from the prepared fingerprint:

```text
prepared lifecycle snapshots are stale
-> rollback
-> optional bounded retry according to the dedicated retry policy
-> no Object/lifecycle DML
```

If the fingerprint matches, the UoW may consume the already-prepared `lifecycle_before` and `lifecycle_after` without rereading or rebuilding them.

## Final write consumption

After target admission, Object-owner locking and protected fingerprint equality, the fused final statement consumes the prepared lifecycle data directly:

```text
WITH mutated AS (
    UPDATE objects ...
)
INSERT object_lifecycle_events
    kind           = SCHEMA_CHANGE
    object_id      = prepared.object_id
    canonical_name = prepared.canonical_name
    before_state   = prepared.lifecycle_before
    after_state    = prepared.lifecycle_after
FROM mutated
```

The lifecycle insert is driven by the successfully mutated Object row, so zero Object rows mutated means zero lifecycle rows inserted.

The lifecycle row identity and timestamp remain PostgreSQL-authoritative according to the common lifecycle persistence contract:

```text
id
    -> PostgreSQL-generated UUID row identity

occurred_at
    -> transaction timestamp semantics
```

## Frozen rule

```text
SCHEMA_CHANGE lifecycle
    -> exactly one intrinsic event on successful real transition
    -> complete canonical intrinsic before/after Object snapshots
    -> snapshots prepared outside UoW
    -> fingerprint protects their freshness
    -> no components/owner/relationships/effective schema in snapshots
    -> no lifecycle reconstruction after fingerprint match
```
