# M4 WIP — Object SCHEMA_CHANGE Q3 fingerprint outcome

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note connects the already-frozen bounded retry policy to the concrete Q3 statement of the `Object.SCHEMA_CHANGE` mutation UoW.

## UoW position

```text
BEGIN
Q1 exact TARGET ObjectTemplateVersion @ FOR SHARE
Q2 Object @ FOR NO KEY UPDATE
Q3 fresh READ COMMITTED aggregate read + application SHA-256
```

Q3 is a new PostgreSQL statement after Q2 has completed, so it observes a fresh READ COMMITTED snapshot after any wait required to acquire the Object concurrency-owner lock.

Q3 reads the complete authoritative Object aggregate fingerprint scope:

```text
Object intrinsic state
    id
    canonical_name
    template_id
    template_version
    properties

current attached ownership edges where Object is parent
    child_object_id
    slot_declaring_template_id
    slot_name
```

The application canonicalizes this state using the same encoder used during optimistic preparation and computes:

```text
protected_fingerprint = SHA-256(canonical_json(current_aggregate))
```

It compares that value with:

```text
PreparedSchemaChange.expected_object_fingerprint
```

## Q3 outcome

### Fingerprints equal

```text
protected_fingerprint == expected_object_fingerprint
    -> PreparedSchemaChange is still current
    -> proceed directly to the final mutation statement
```

No semantic migration, property validation, component interpretation or cache work is repeated inside the UoW after a successful equality check.

### Fingerprints differ on attempt 1

```text
protected_fingerprint != expected_object_fingerprint
    -> perform no Object/lifecycle DML
    -> ROLLBACK attempt 1
    -> start exactly one complete fresh attempt 2
```

Attempt 2 repeats the caller-side process from the beginning of mutable-state discovery. Immutable cache entries and an immutable MigrationPlan may be reused only when their identities remain applicable, but no mutable conclusion from attempt 1 is reused.

### Fingerprints differ on attempt 2

```text
protected_fingerprint != expected_object_fingerprint
    -> perform no Object/lifecycle DML
    -> ROLLBACK attempt 2
    -> no third attempt
    -> return HTTP 409 STATE_CONFLICT
       code = schema_change_blocked
       blocker_type = concurrent_object_change
```

## Relationship with other stale observations

The automatic retry budget is consumed only by the protected Q3 fingerprint mismatch.

In particular, the already-agreed earlier case:

```text
initial binding lookup
    source_version = V1

MigrationPlan(V1 -> target) selected/compiled

later optimistic complete Object aggregate read
    current template_version != V1
```

fails the request conservatively and does not trigger automatic re-planning within the same request.

This remains distinct from Q3: Q3 is the protected post-lock equality guard of an already-completed `PreparedSchemaChange`.

## Frozen decision

```text
Q3 SHA equal
    -> final mutation may execute

Q3 SHA mismatch, attempt 1
    -> rollback
    -> one complete fresh retry

Q3 SHA mismatch, attempt 2
    -> rollback
    -> 409 schema_change_blocked

MAX TOTAL ATTEMPTS = 2
```
