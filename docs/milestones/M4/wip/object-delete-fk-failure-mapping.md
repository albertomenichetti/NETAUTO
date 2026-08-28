# M4 WIP — Object DELETE FK failure mapping

Status: FROZEN DISCOVERY INPUT / M4 WIP / ALWAYS NON-NORMATIVE

## Scope

This note records the current route-local candidate for PostgreSQL foreign-key failure mapping in M4 `Object.DELETE`.

Public command surface:

```http
DELETE /api/v1/core/objects/{object_id}
```

The current M4 DELETE candidate performs the root Object deletion directly and uses the deleted row returned by PostgreSQL as the authoritative historical `before` snapshot for the `DELETED` lifecycle event.

## Candidate root statement

Conceptually:

```text
Q1
    DELETE FROM objects
    WHERE id = :object_id
    RETURNING
        id,
        canonical_name,
        template_id,
        template_version,
        properties
```

The semantic meaning of a PostgreSQL failure is interpreted in the context of this specific root DELETE statement.

## Candidate failure mapping

```text
Q1 returns 0 rows
    -> 404 resource_not_found

Q1 fails with SQLSTATE 23503 / foreign_key_violation
    -> 409 delete_blocked

Q1 returns exactly 1 row
    -> continue to DELETED lifecycle write

any other unexpected PostgreSQL failure
    -> normal bounded persistence/internal-failure classification
```

No additional PostgreSQL query is executed to diagnose the blocking reference.

## Public delete_blocked contract

The public failure is intentionally independent of the concrete inbound FK that blocked deletion:

```json
{
  "code": "delete_blocked",
  "details": {
    "resource_type": "object",
    "id": "<uuid>"
  }
}
```

The public contract does not require:

- blocker identity lists;
- blocker type enumeration;
- exact blocker counts;
- PostgreSQL constraint names.

## Why SQLSTATE is sufficient here

The rule is statement-specific:

```text
foreign_key_violation
DURING the root DELETE FROM objects
    -> a current inbound reference still protects Object lifetime
    -> deletion is blocked
```

It is not a generic rule that every `23503` in every mutation maps to `delete_blocked`.

An outbound Object FK such as the Object's exact ObjectTemplateVersion pin cannot block removal of the referencing Object row itself. A `23503` raised by the root Object DELETE therefore represents an inbound FK reference that prevents the Object row from being removed.

This lets PostgreSQL remain the final relational lifetime authority without a route-local blocker precheck.

## Constraint-name independence

The current AS-IS persistence implementation translates a finite whitelist of known Object-reference FK constraint names, currently ownership and factual-Relationship endpoint references.

The M4 candidate does not require that whitelist for semantic correctness.

If a future TO-BE relational structure introduces another current Object lifetime reference, for example:

```text
new_current_fact.object_id
    -> objects.id
    ON DELETE RESTRICT / NO ACTION
```

then the same root DELETE naturally fails with `23503` and continues to map to `409 delete_blocked` without a route-specific code change solely to recognize the new constraint name.

Constraint names may still be useful for logging, diagnostics or verification, but they are not part of the required public semantic classification.

## Architecture handoff — complete Object lifetime enforcement

The direct-DML candidate is safe only if every TO-BE current reference that semantically requires Object lifetime is protected by an enforcement mechanism that arbitrates with Object DELETE.

The architecture phase must therefore enumerate every TO-BE current Object reference and verify:

```text
must this reference keep the Object alive?
    |
    +-- no
    |    -> irrelevant to Object.DELETE admission
    |
    +-- yes
         -> does an atomic DELETE-arbitrating mechanism exist?
              |
              +-- preferably immediate FK RESTRICT / NO ACTION
              +-- or another globally proven equivalent mechanism
```

A current semantic reference that must block deletion but is not represented by an FK or equivalent atomic arbitration mechanism would invalidate the assumption that `DELETE ... RETURNING` alone can safely perform lifetime admission.

The final architecture must preserve the `RL` reference-lifetime outcomes:

```text
reference commits first
    -> Object DELETE cannot commit

Object DELETE commits first
    -> a new reference cannot commit

reference removal commits first
    -> Object DELETE may become admissible
```

## Candidate data-path consequence

No blocker-count query and no constraint-name-specific semantic branch are required on the route-local candidate path:

```text
BEGIN

Q1 DELETE Object ... RETURNING before snapshot
    -> 0 rows = 404
    -> 23503 = 409 delete_blocked
    -> 1 row = continue

Q2 INSERT DELETED lifecycle event

COMMIT
```

## Frozen discovery takeaway

```text
Object.DELETE root DML owns reference-blocker classification

SQLSTATE 23503 on root DELETE
    -> 409 delete_blocked

no public blocker type/count
no constraint-name whitelist required for semantic correctness
no diagnostic-only PostgreSQL query

architecture handoff:
    every TO-BE Object lifetime dependency must have DELETE-arbitrating enforcement
```
