# Codex review-fix prompt — M1-S06

**Status:** NON-NORMATIVE REVIEW-FIX PROMPT.

This execution aid does not override `AGENTS.md`, the frozen M1 contract/architecture/steps, or the ratified technology baseline.

## Assignment

Close the two public error-detail conformance findings from the M1-S06 implementation review. Preserve the accepted S06 domain, persistence, concurrency and API behavior unless a regression test exposes a genuine defect.

Implementation under review:

```text
1c21ac046505e383b707b3f7e328b82921257673
```

Before changing code, re-read at minimum:

```text
AGENTS.md
docs/milestones/M1/architecture/api-error-contract.md
docs/milestones/M1/architecture/relationship-definition.md
docs/milestones/M1/architecture/relationship-concurrency.md
docs/milestones/M1/architecture/concurrency-postgresql-realization-relationship.md
docs/milestones/M1/steps.md
docs/milestones/M1/status.md
```

Do not modify normative architecture. No architecture contradiction is currently known.

## Finding 1 — RD.DELETE `delete_blocked` details

Current `RelationshipDefinitionService.delete()` returns `delete_blocked` with only:

```json
{
  "resource_type": "relationship_definition",
  "id": "..."
}
```

when current factual Relationship headers reference the Definition.

API-03.11 section 11.4 requires `delete_blocked` to expose bounded blocker type/count information. Align RD.DELETE with that canonical shape.

For the normal pre-check, use the exact current count already read from `relationships.relationship_definition_id`, e.g.:

```json
{
  "resource_type": "relationship_definition",
  "id": "...",
  "blockers": [
    {"type": "relationship", "count": N}
  ]
}
```

Do not expose relationship IDs, SQL constraints or raw persistence structure.

Keep the final FK `RESTRICT` authority. If the defensive delete-side FK race translation remains reachable, its public `delete_blocked` details must still satisfy the bounded blocker contract; do not weaken the Definition `FOR UPDATE` owner or add retries/gates.

Add API/application regression coverage asserting the exact bounded details shape for a Definition blocked by current factual Relationship rows.

## Finding 2 — concurrent endpoint-lineage loss must retain semantic selector

Normal pre-certification missing endpoint handling already returns:

```text
422 referenced_resource_not_found
resource_type = object_template
id = missing template UUID
```

But if an ObjectTemplate lineage wins the REF-01 race after candidate validation and the Resolution INSERT loses on one of the endpoint FKs, the current `RelationshipEndpointReferenceError` discards which endpoint UUID failed and `_referenced_template()` returns only `resource_type`.

API-03.11 not-found details preserve the semantic resource selector fields known at the bounded persistence boundary. Keep the FK translation bounded, but carry the failed endpoint `template_id` through the persistence exception and return:

```json
{
  "resource_type": "object_template",
  "id": "<failed endpoint uuid>"
}
```

Do not expose the constraint name. It is acceptable to use the known from/to FK constraint internally to select the corresponding semantic endpoint UUID.

Add/strengthen deterministic REF-01 or focused persistence/API regression coverage proving the delete-first/concurrent-FK-loss path returns the missing endpoint UUID in `details.id`.

## Preserve all accepted S06 behavior

Do not change:

- Definition/Resolution aggregate semantics;
- symmetric/non-symmetric derivation;
- semantic signature/equivalence/conflict rules;
- ancestry overlap semantics;
- `RELATIONSHIP_DEFINITION_CONFLICT_GATE` ordering or lifetime;
- coherent one-statement certified-set read;
- RENAME `FOR NO KEY UPDATE` / DELETE `FOR UPDATE` owner modes;
- endpoint lineage pure-FK lifetime strategy;
- capability inheritance/pagination;
- routes or success statuses;
- schema/migrations;
- S07 runtime Relationship behavior;
- lifecycle Relationship DTOs.

## Verification

Run and report at minimum:

```text
uv lock --check
uv sync --locked
uv build
Ruff format/check
Pyright strict
non-PostgreSQL suite
real-PostgreSQL suite on TEST_DATABASE_URL
```

Retain the existing S06 deterministic ROW-17, REF-01, GATE-04/05/06, ATOMIC-04C and REALIZE-12 regressions. No sleep-based orchestration or generic retries.

At completion report:

- corrective commit SHA;
- changed files;
- exact quality/test counts and PostgreSQL version;
- confirmation that both public error-detail findings are closed;
- confirmation that no migration, normative-doc, S07 or lifecycle Relationship behavior was added.
