# M4 WIP — Object SCHEMA_CHANGE bounded retry policy

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the bounded optimistic-retry policy for:

```http
POST /api/v1/core/objects/{object_id}/schema
```

It refines the optimistic-preparation/fingerprint protocol already frozen for Object schema migration.

## Retry budget

The command permits exactly **two total attempts**:

```text
attempt 1
    -> initial preparation + mutation UoW

attempt 2
    -> at most one complete fresh retry
```

This is not `initial attempt + two retries`.

The maximum is:

```text
2 total attempts
=
1 initial attempt
+
1 possible retry
```

## Only retry trigger

The only condition that may trigger the internal automatic retry is:

```text
protected_current_fingerprint != prepared_expected_fingerprint
```

That mismatch means the prepared success candidate was derived from an Object aggregate generation that is no longer current after the parent Object concurrency owner has been acquired and the fresh protected fingerprint has been recomputed.

No other domain, lifecycle, dependency, persistence or concurrency outcome is automatically retried by this route.

In particular:

```text
semantic preparation failure
    -> return failure
    -> no retry

target <= current version
    -> return failure
    -> no retry

preliminary target absent/non-PUBLISHED
    -> return classified failure
    -> no retry

final target admission failure
    -> return classified failure
    -> no retry

property/component migration blocker
    -> return classified failure
    -> no retry

unexpected final-write invariant failure
    -> rollback/classify according to its owning failure contract
    -> not a fingerprint retry
```

This deliberately supersedes any earlier exploratory suggestion that an unrelated target-lifetime race should itself consume the optimistic retry budget.

## Attempt behavior

### Attempt 1 fingerprint matches

```text
prepare candidate C1 from snapshot S1
enter UoW
lock required authorities
compute protected F(S1')

F(S1') == F(S1)
    -> proceed with prepared candidate
    -> no retry
```

### Attempt 1 fingerprint mismatches

```text
F(S1') != F(S1)
    -> no Object/lifecycle DML
    -> rollback attempt 1 completely
    -> start attempt 2 from a new coherent Object aggregate snapshot S2
```

Attempt 2 is a complete fresh attempt. It does not reuse mutable conclusions from attempt 1.

It may reuse immutable/cacheable knowledge where identities still match, for example exact immutable ObjectTemplate/DataType semantics or an immutable MigrationPlan for the same source/target pair, but every mutable Object-state decision is rederived from the fresh second snapshot.

### Attempt 2 fingerprint mismatches

```text
F(S2') != F(S2)
    -> no Object/lifecycle DML
    -> rollback attempt 2 completely
    -> retry budget exhausted
    -> return a concurrency/state failure to the caller
```

There is no third attempt.

## Public retry-exhaustion mapping

Exhaustion of the two-attempt budget is a current-state concurrency conflict, not a semantic-invalid-request outcome and not an internal server failure.

The public mapping is:

```text
HTTP 409 STATE_CONFLICT
code = schema_change_blocked
```

No new public error code is introduced solely for optimistic retry exhaustion.

The response details must make the cause distinguishable from a value/attachment migration blocker while preserving the same top-level code. Conceptually:

```json
{
  "code": "schema_change_blocked",
  "message": "The Object changed concurrently while the schema migration was being prepared.",
  "details": {
    "object_id": "<uuid>",
    "target_version": 8,
    "blocker_type": "concurrent_object_change"
  }
}
```

The caller may choose to issue a new request. The server does not perform a third internal attempt.

This mapping reflects the semantics already chosen for the route:

```text
same requested semantic migration
+
continuing mutable Object contention
-> meaningful command currently blocked
-> STATE_CONFLICT / 409
```

## Why two attempts

The policy deliberately favors a short, bounded request over indefinite optimistic spinning.

The expected normal case is:

```text
attempt 1 succeeds
```

A first mismatch captures a real concurrent Object-generation change and permits one fresh rederivation. A second mismatch indicates continuing contention during the request; the caller receives a failure rather than the kernel repeatedly extending request latency and lock activity.

## Safety property

Retry exhaustion can only cause a false/conservative failure. It cannot create a false success or inconsistent persisted state.

Every mismatch path rolls back before Object/lifecycle DML. A successful commit still requires:

```text
prepared candidate derived from S
+
protected current fingerprint == F(S)
+
required Object/model-plane locks held through write/commit
```

Therefore the governing priority remains:

```text
false success
    -> prevented STRONGLY

false failure under contention
    -> acceptable
```

## Frozen decision

```text
MAX TOTAL ATTEMPTS = 2

automatic retry trigger = protected fingerprint mismatch ONLY

attempt 1 mismatch
    -> rollback
    -> one complete fresh retry

attempt 2 mismatch
    -> rollback
    -> HTTP 409 STATE_CONFLICT
    -> code schema_change_blocked
    -> blocker_type concurrent_object_change

all other failures
    -> no automatic retry
```
