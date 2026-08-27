# M4 WIP — Object SCHEMA_CHANGE warm-path cost

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the warm-path statement-count and cost character for:

```http
POST /api/v1/core/objects/{object_id}/schema
```

## Warm-path assumptions

The warm path assumes:

```text
MigrationPlanCache[(template_id, source_version, target_version)] = HIT
```

Therefore no ObjectTemplate closure, exact DataTypeVersion semantics or stable ancestry cold-fill statement is required during this request.

The separately frozen preliminary unlocked target admission lookup has been removed. Current target lifecycle admission is checked only by the final protected UoW statement on the exact target ObjectTemplateVersion.

## Successful first-attempt warm path

Excluding transaction control (`BEGIN` / `COMMIT`), the route performs six PostgreSQL business statements:

```text
1. initial Object binding lookup
   -> Object PK lookup
   -> obtain template_id + source template_version

2. optimistic complete Object aggregate read
   -> Object PK lookup
   -> current Object properties
   -> current attached ownership edges by parent_object_id
   -> build S + expected SHA-256
   -> apply already-cached MigrationPlan in application
   -> build PreparedSchemaChange

3. Q1 exact TARGET OTV @ FOR SHARE
   -> exact composite-key lookup
   -> require current status PUBLISHED
   -> hold through COMMIT

4. Q2 Object @ FOR NO KEY UPDATE
   -> Object PK lookup / concurrency rendezvous

5. Q3 fresh protected Object aggregate read
   -> new READ COMMITTED statement snapshot
   -> Object PK lookup
   -> current attached ownership edges by parent_object_id
   -> recompute SHA-256
   -> compare with PreparedSchemaChange.expected_object_fingerprint

6. Q4 fused mutation + lifecycle write
   -> UPDATE objects(template_version, properties)
   -> INSERT one SCHEMA_CHANGE lifecycle event
   -> one PostgreSQL business statement
```

## Cost character

The architectural value is not only the count `6`, but the fact that the six statements are bounded and structurally simple.

There is no warm-path:

```text
recursive ObjectTemplate traversal
exact parent-chain reconstruction
per-property DataType lookup
per-edge child Object lookup
N+1 semantic loading
runtime schema re-certification
object_components DML on successful migration
```

The expected access patterns are conceptually:

```text
Object binding/read/lock
    -> objects PK(object_id)

current attached ownership
    -> object_components by parent_object_id

TARGET admission
    -> object_template_versions exact PK(template_id, version)
```

The two aggregate reads are bounded by the size of the actual Object aggregate rather than model depth:

```text
payload/work ~ Object properties + number of currently attached ownership edges
```

Q4 naturally scales with the size of:

```text
target properties JSONB
lifecycle before_state snapshot
lifecycle after_state snapshot
```

Therefore "lightweight" here means bounded/simple access path with no repeated semantic interpretation, not constant byte size independent of Object aggregate size.

## Retry impact

This file freezes only the successful first-attempt warm-path count.

The separately frozen retry policy remains:

```text
attempt 1 fingerprint mismatch
    -> rollback before Q4
    -> one complete fresh second attempt

attempt 2 fingerprint mismatch
    -> rollback
    -> 409 schema_change_blocked
```

## Physical verification handoff

The architecture-wide physical review must prove with PostgreSQL evidence that the intended bounded paths are realized efficiently, especially:

```text
objects PK lookup by object_id
object_template_versions exact composite-key lookup
object_components lookup by parent_object_id
```

No new route-local index is frozen here.

## Frozen conclusion

```text
successful first-attempt warm path
    = 6 PostgreSQL business statements
      excluding BEGIN/COMMIT

all six statements
    = bounded/simple data access or one fused write

no warm-path model-plane traversal or semantic N+1 work
```
