# M4 WIP — Object DELETE FK failure mapping

Status: RETAINED FAILURE-MAPPING DISCOVERY INPUT / SUPERSEDED IN DATA-PATH SEQUENCING / M4 WIP / ALWAYS NON-NORMATIVE

## Scope

This note preserves the accepted route-local failure-mapping finding for M4 `Object.DELETE`.

The current route-local consolidation owner is:

```text
docs/milestones/M4/wip/to-be-api-object-delete.md
```

That consolidation supersedes this file only where older revisions described a separate:

```text
Q1 DELETE
-> Q2 lifecycle INSERT
```

The accepted FK classification and lifetime-enforcement findings below remain discovery inputs.

## Public command surface

```http
DELETE /api/v1/core/objects/{object_id}
```

The current consolidated candidate performs the root Object deletion and the required `DELETED` lifecycle insertion in one data-modifying PostgreSQL statement.

## Retained failure-mapping finding

The semantic meaning of a PostgreSQL FK failure is interpreted in the context of the root deletion of the selected `objects` row.

Candidate outcomes remain:

```text
no deleted Object row / no success carrier
    -> 404 resource_not_found

foreign_key_violation / SQLSTATE 23503
caused by the root DELETE FROM objects
    -> 409 delete_blocked

successful deleted Object row + lifecycle insertion
    -> COMMIT
    -> 204 No Content

any other unexpected PostgreSQL failure
    -> normal bounded persistence/internal-failure classification
```

No additional PostgreSQL query is executed to diagnose the blocking reference.

## Public `delete_blocked` contract

The public failure is intentionally independent of the concrete inbound FK that blocks deletion:

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

## Constraint-name independence

The delivered AS-IS persistence implementation translates a finite whitelist of known Object-reference FK constraint names.

The M4 candidate does not require that whitelist for semantic correctness.

If a future TO-BE relational structure introduces another current Object lifetime reference such as:

```text
new_current_fact.object_id
    -> objects.id
    ON DELETE RESTRICT / NO ACTION
```

then root Object deletion should naturally remain blocked without route-specific code solely to recognize the new constraint name.

Constraint names may still be used for observability and verification.

## Important qualification after statement fusion

The consolidated candidate now combines root Object deletion and lifecycle insertion in one PostgreSQL statement.

Therefore generic statement-level:

```text
23503 -> delete_blocked
```

is valid only if a `23503` from that statement can be attributed safely to the root Object lifetime delete.

The current lifecycle model supports this because historical lifecycle identity/name/snapshot fields deliberately have no live FKs back to current Object/model rows.

Architecture closure must preserve one of these properties:

```text
A. the lifecycle INSERT branch cannot generate an unrelated FK violation;

or

B. the persistence boundary can distinguish the failure source without
   issuing a diagnostic-only PostgreSQL query.
```

An unrelated persistence defect must never be exposed as `409 delete_blocked` merely because it shares SQLSTATE `23503`.

## Architecture handoff — complete Object lifetime enforcement

The direct-DML candidate is safe only if every TO-BE current reference that semantically requires Object lifetime is protected by an enforcement mechanism that arbitrates with Object DELETE.

The architecture phase must enumerate every TO-BE current Object reference and verify:

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

The final architecture must preserve the `RL` outcomes:

```text
reference commits first
    -> Object DELETE cannot commit

Object DELETE commits first
    -> new reference cannot commit

reference removal commits first
    -> Object DELETE may become admissible
```

## Retained discovery takeaway

```text
root Object DELETE lifetime failure
    -> 409 delete_blocked

no public blocker type/count
no constraint-name whitelist required for semantic correctness
no diagnostic-only PostgreSQL query

statement-fusion qualification:
    unrelated lifecycle FK failures must not be misclassified as delete_blocked

architecture handoff:
    every TO-BE Object lifetime dependency must have DELETE-arbitrating enforcement
```
