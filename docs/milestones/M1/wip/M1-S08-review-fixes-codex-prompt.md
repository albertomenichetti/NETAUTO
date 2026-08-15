# Codex review-fix prompt — M1-S08 REF-06 verification closure

**Status:** NON-NORMATIVE REVIEW-FIX PROMPT.

This file is an execution aid only. It does not override `AGENTS.md`, the FINAL/FROZEN M1 contract/steps, the globally FROZEN M1 architecture, or the ratified technology baseline.

## Assignment

Close the remaining **verification/traceability-only** finding for:

```text
M1-S08 — Cross-domain integrity, destructive-operation and API/read closure
```

Accepted implementation candidate under review:

```text
678da20904bec7eb16a6baff45f26a80890dbcae
```

The reviewer found no production-semantic defect in the S08 candidate. Start from the assumption that this review fix is test-only. Modify production code only if a new real-PostgreSQL regression proves a genuine defect.

Do not add M1-S09 capability, routes, migrations, tables, columns, gates, or normative architecture changes.

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
docs/milestones/M1/architecture/persistence-model.md
docs/milestones/M1/architecture/persistence-uow-concurrency.md
docs/milestones/M1/architecture/concurrency-postgresql-test-matrix.md
docs/milestones/M1/architecture/api-error-contract.md
```

Preserve the accepted S08 production behavior, including Object DELETE, bounded FK race-loser mappings, the 32/20 route census, the 23-code public error catalog and the S07 `0002_resolution_name_nonkey` correction.

## Review finding — REF-06 lacks explicit canonical mechanism evidence

The current S08 suite has strong real-PG coverage for `REF-01..05`. Existing `REF-01` / `REF-04` races also exercise pieces of the same PostgreSQL FK machinery needed by `REF-06`, and the S08 blocker matrix proves normal pre-check integrity.

However, the canonical scenario:

```text
REF-06  aggregate CASCADE × external RESTRICT
```

is not yet explicitly traceable as a canonical test, and the completion gate requires direct proof that an attempted root delete which reaches the physical delete/CASCADE path and loses on an external current FK leaves both the root and its **owned children** intact.

This is a verification-completeness issue, not a new semantic requirement.

## Required REF-06 coverage

Add explicit real-PostgreSQL canonical coverage for the three M1 aggregate shapes below. A single parametrized test with clear variants is acceptable, or three tests named `test_ref_06a...`, `test_ref_06b...`, `test_ref_06c...`.

### REF-06A — DataType aggregate CASCADE × external OTV property RESTRICT

Construct:

```text
DataType lineage D
+ at least one owned DataTypeVersion
+ external ObjectTemplate property exact-DTV reference to D@V
```

The test must exercise the **physical root DELETE attempt**, not stop only at `external_reference_count()`.

Use deterministic concurrent orchestration so the DataType delete pre-check sees no blocker, then a concurrent semantic/reference operation commits the OTV property reference before the physical root DELETE executes. The delete must lose on the actual PostgreSQL FK authority.

Assert after the failed delete:

```text
DataType root still exists
owned DataTypeVersion(s) still exist
external OTV/property reference remains current
public/semantic outcome = delete_blocked with bounded object_template_property blocker
```

No partial owned-child CASCADE may remain committed.

### REF-06B — ObjectTemplate aggregate CASCADE × external current RESTRICT

Construct an ObjectTemplate root aggregate with owned state, ideally:

```text
ObjectTemplate lineage T
+ owned ObjectTemplateVersion
+ at least one owned local declaration where practical
```

Then create one external current reference after the delete pre-check but before physical root delete. Prefer an already-supported real semantic reference path that strongly proves the root->owned-child CASCADE cannot bypass external RESTRICT, for example:

```text
Object CREATE -> exact OTV
```

or another frozen external OT reference shape.

Assert after the physical delete loses:

```text
ObjectTemplate root still exists
owned version(s) still exist
owned local declaration(s), if seeded, still exist
external reference remains current
semantic outcome = delete_blocked with correct bounded blocker type
```

Do not satisfy this only with the normal pre-check blocker matrix.

### REF-06C — RelationshipDefinition aggregate CASCADE × factual Relationship RESTRICT

Construct:

```text
RelationshipDefinition D
+ complete owned RelationshipResolution set
```

Use deterministic concurrent ordering so `RD.DELETE` passes its current factual-Relationship pre-check, then a real `REL.CREATE` commits a factual Relationship referencing D before the Definition root DELETE reaches the physical statement.

Assert after the failed root delete:

```text
RelationshipDefinition root still exists
complete owned RelationshipResolution set still exists
factual Relationship remains current
semantic outcome = delete_blocked with relationship blocker
```

This variant may reuse/extend the existing `REF-04` mechanism seam, but it must be explicitly traceable to `REF-06C` and must assert owned Resolution survival, not only root survival.

## Mechanism requirements

For all variants:

- use real PostgreSQL and independent transactions/UoWs;
- use deterministic phase cuts; no sleep-based correctness orchestration;
- ensure the delete pre-check happens before the external reference becomes current;
- ensure the physical root DELETE is attempted after the reference commits;
- prove the PostgreSQL FK/RESTRICT is the final loser authority;
- assert root + owned children remain intact after the failed statement/UoW;
- do not weaken or bypass application semantics merely to manufacture an impossible state;
- do not rewrite migrations or add triggers/constraints.

It is acceptable to reuse existing persistence cut seams or introduce test-only interception around `delete_lineage` / Definition delete so long as the actual SQL DELETE and FK failure occur.

## Preserve existing coverage

Keep all accepted S08 behavior/tests green, including:

```text
REF-01..05
Object DELETE owner/FK/event semantics
normal DT/OT/RD/Object blocker detail matrix
bounded race-loser count=1 mappings
lifecycle/read closure
32 mutation routes
20 read routes
23 public error codes
PERSIST-15 index verification
forbidden surface checks
```

Do not rename away existing canonical test IDs.

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
canonical REF selection including explicit REF-06A/B/C
migration/schema/drift selection
```

Report exact pass counts and PostgreSQL server version.

## Completion report

Commit and push the review fix directly to `core_review` and report:

- commit SHA;
- changed files;
- confirmation whether patch is test-only;
- exact `REF-06A/B/C` tests added or extended;
- how each forces the physical root DELETE to lose on external RESTRICT after pre-check;
- assertions proving root + owned-child survival;
- full/non-PG/PG/REF verification counts;
- confirmation no production/migration/normative docs changed;
- confirmation no new architecture contradiction.

Do not mark `docs/milestones/M1/status.md` COMPLETED; reviewer owns completion status.