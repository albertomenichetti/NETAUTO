# M4 WIP — Object SCHEMA_CHANGE Q4 final mutation

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the final business statement of the successful short UoW for:

```http
POST /api/v1/core/objects/{object_id}/schema
```

## Preconditions

Q4 is reached only after:

```text
Q1 target exact ObjectTemplateVersion @ FOR SHARE
    current status == PUBLISHED

Q2 Object @ FOR NO KEY UPDATE

Q3 fresh protected aggregate read
    protected SHA-256 == PreparedSchemaChange.expected_object_fingerprint
```

Therefore the expensive semantic work is already complete and the prepared candidate is still current.

## Q4 responsibility

Q4 performs only the already-prepared state transition:

```text
objects.template_version
    source_version -> target_version

objects.properties
    current source properties -> prepared target_properties

object_lifecycle_events
    insert exactly one SCHEMA_CHANGE event
    using prepared lifecycle_before/lifecycle_after
```

A successful normal M4 Object.SCHEMA_CHANGE performs no `object_components` DML. Ownership edges were only an admission condition during optimistic preparation and part of the protected aggregate fingerprint.

## Preferred PostgreSQL statement shape

Object mutation and lifecycle persistence are one business statement so they cannot diverge:

```sql
WITH mutated AS (
    UPDATE objects
    SET
        template_version = :target_version,
        properties = :target_properties
    WHERE id = :object_id
      AND template_id = :template_id
      AND template_version = :source_version
    RETURNING id
)
INSERT INTO object_lifecycle_events (
    object_id,
    event_type,
    before_state,
    after_state
)
SELECT
    id,
    'SCHEMA_CHANGE',
    :lifecycle_before,
    :lifecycle_after
FROM mutated
RETURNING id;
```

Exact lifecycle column names remain subject to the final relational freeze, but the one-statement mutation/event coupling is frozen.

## Defensive source predicates

Even after a matching protected fingerprint, Q4 retains:

```text
id == object_id
template_id == prepared.template_id
template_version == prepared.source_version
```

These are defensive stale/invariant guards rather than another semantic validation stage.

If `mutated` returns zero rows:

```text
no lifecycle event is inserted
transaction rolls back
classify as final-write invariant/stale-protection failure
```

This condition is not a fingerprint-retry trigger.

## No semantic work in Q4

Q4 must not:

```text
rebuild or revalidate MigrationPlan
re-read ObjectTemplate/DataType semantic caches
re-run property migration
re-run component admission
re-read ownership edges
recompute lifecycle snapshots
perform ObjectTemplate inheritance traversal
```

All required values come from `PreparedSchemaChange`.

## Commit

After Q4 succeeds:

```text
COMMIT
```

The exact target OTV SHARE lock and Object NO KEY UPDATE lock remain held through commit.

Successful UoW therefore remains:

```text
BEGIN
Q1 target exact OTV SHARE + require PUBLISHED
Q2 Object NO KEY UPDATE
Q3 fresh aggregate read + SHA-256 compare
Q4 fused Object UPDATE + SCHEMA_CHANGE lifecycle INSERT
COMMIT
```

## Frozen decision

```text
Q4 = one PostgreSQL business statement

writes:
    Object.template_version
    Object.properties
    one SCHEMA_CHANGE lifecycle event

writes no ownership edges
performs no new semantic validation
uses PreparedSchemaChange directly
retains defensive source identity predicates
zero-row mutation = invariant/stale-protection failure, not automatic retry
```