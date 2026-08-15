# Codex review-fix prompt — M1-S07 verification closure

**Status:** NON-NORMATIVE REVIEW-FIX PROMPT.

This file is an execution aid only. It does not override `AGENTS.md`, the frozen M1 contract/architecture/steps, or the ratified technology baseline.

## Assignment

Close the remaining **verification-only** findings for:

```text
M1-S07 — Runtime Relationship and relationship lifecycle vertical slice
```

Accepted implementation candidate:

```text
27150496d460a5eed0ca025b176ec52324e948a4
```

The reviewer found no current production-semantic blocker in that candidate. Start from the assumption that the fix is test-only. Modify production code only if a newly added deterministic regression proves that the implementation is actually wrong.

Do not add M1-S08 behavior, Object.DELETE, new routes, tables, columns, gates, Relationship semantics or normative architecture changes.

## Mandatory pre-flight

Re-read at minimum:

```text
AGENTS.md
docs/general/technology_baseline.md
docs/milestones/M1/contract.md
docs/milestones/M1/steps.md
docs/milestones/M1/status.md
docs/milestones/M1/architecture/README.md
docs/milestones/M1/architecture/m1-final-consistency-review.md
docs/milestones/M1/architecture/relationship-concurrency.md
docs/milestones/M1/architecture/concurrency-postgresql-realization-relationship.md
docs/milestones/M1/architecture/concurrency-postgresql-test-matrix.md
docs/milestones/M1/architecture/object-lifecycle-changelog.md
docs/milestones/M1/architecture/api-read-contract.md
docs/milestones/M1/architecture/api-list-contract.md
docs/milestones/M1/architecture/api-error-contract.md
```

Preserve the re-frozen PAR-02 physical correction and migration `0002_resolution_name_nonkey` exactly. Do not reintroduce `uq_relationship_resolutions_semantic_child` at head.

## Finding 1 — missing REALIZE-15 non-serialization regressions

The S07 resume prompt required explicit real-PostgreSQL protection that runtime Relationship CREATE is not artificially serialized by non-key Object mutations where no other predicate applies.

Add deterministic tests for both:

```text
REL.CREATE × OBJ.DATA_CHANGE
REL.CREATE × OBJ.SCHEMA_CHANGE
```

Required mechanism evidence:

- use independent PostgreSQL sessions/UoWs;
- hold the Object mutation transaction open **after** its non-key UPDATE has executed;
- while that transaction remains open, prove `REL.CREATE` can progress/complete;
- no `sleep()` correctness orchestration;
- do not weaken Object writer ownership or Relationship FK semantics;
- do not introduce a runtime Relationship gate.

These are REALIZE-15 mechanism regressions, not new canonical PGTEST IDs. Existing `PAR-01`, `PAR-02`, `PAR-05` remain unchanged.

## Finding 2 — missing CREATE lifecycle-failure atomic rollback proof

S07 requires:

```text
Relationship header
+ complete runtime closure
+ complete RELATIONSHIP_CREATED event set
```

to commit or rollback together.

Add a direct real-PostgreSQL regression that forces a narrow failure **after the complete Relationship closure has been inserted successfully but before the creation event set can commit**, for example by intercepting `RuntimeRelationshipStore.insert_lifecycle_events` only for `RELATIONSHIP_CREATED`.

Assert after failure:

```text
candidate Relationship header absent
all candidate runtime closure rows absent
no candidate RELATIONSHIP_CREATED events committed
```

The test must demonstrate rollback of the real semantic UoW, not fake an earlier validation failure.

Keep existing `ATOMIC-02` later-row PK collision and `ATOMIC-03` DELETE rollback tests unchanged; this is complementary coverage for the post-closure CREATE/event boundary explicitly required by REALIZE-14/S07.

## Finding 3 — lifecycle API evidence against real Relationship events

The Relationship producer now populates lifecycle metadata, but the completion suite must exercise the frozen API filters/timeline semantics with **actual S07-created events**.

Extend/add API tests to prove:

### Global lifecycle filters

Against a real factual Relationship event set, verify exact filtering by:

```text
relationship_id
relationship_definition_id
relationship_name
```

Use at least one positive and one excluding/mismatch assertion where useful so a silently ignored filter cannot pass.

### Object-specific lifecycle involvement

For a normal non-symmetric two-object Relationship, query:

```text
GET /api/v1/core/objects/{endpoint_id}/lifecycle-events
```

and prove each endpoint timeline includes the Relationship structural events where the endpoint appears either as:

```text
object_id
OR destination_object_id
```

For the two-perspective non-symmetric fact, this should make both semantic Relationship event perspectives visible to each involved Object timeline, subject to the existing lifecycle ordering/filter contract.

Also keep the exact Relationship lifecycle DTO field-shape assertion already present.

## Finding 4 — cheap strict Relationship CREATE body closure

The S07 prompt explicitly requested unknown/null/wrong carriers to be rejected. Unknown-field coverage already exists. Add bounded API regressions for at least:

```text
null UUID operand
non-string/wrong UUID carrier
```

and assert the frozen invalid-request boundary (`400 invalid_request`). Do not add coercion.

## Scope discipline

Do not change:

```text
Relationship domain semantics
RelationshipDefinition semantics
PAR-02 contract
0001 migration
0002 upgrade/downgrade meaning
runtime exact-view PK authority
one-statement lifecycle metadata observation
API route inventory
Object.DELETE / S08 behavior
REF-03 / Relationship REF-05 deferral
```

No normative documentation edits.

## Verification

Run at minimum:

```text
uv lock --check
uv sync --locked
uv build
Ruff format/check
Pyright strict
non-PostgreSQL suite
real-PostgreSQL suite serially using TEST_DATABASE_URL
S07 deterministic concurrency selection
migration/schema/drift tests
```

Report PostgreSQL server version and exact pass counts.

At completion, commit and push the review fix to `core_review` and report:

- commit SHA;
- changed files;
- confirmation whether the patch was test-only;
- exact new tests added;
- quality/test counts;
- confirmation that `REF-03` and Relationship `REF-05` remain deferred to S08;
- confirmation of no new architecture contradiction.

Do not mark `docs/milestones/M1/status.md` COMPLETED; reviewer owns completion status.