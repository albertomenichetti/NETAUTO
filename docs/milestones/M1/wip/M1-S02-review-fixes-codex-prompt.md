# Codex review-fix prompt — M1-S02

**Status:** NON-NORMATIVE REVIEW-FIX PROMPT.

This file is an execution aid for Codex. It does not override `AGENTS.md`, the frozen M1 contract/architecture/steps, or the ratified technology baseline.

## Assignment

Continue the current implementation step:

```text
M1-S02 — PrimitiveType and DataType vertical slice
```

The implementation commit under review is:

```text
97ab77defc77f6cd51492c6ba209dbfce8dd918f
```

Do not start M1-S03. Preserve the existing S02 implementation unless a change is required by the review findings below.

## Mandatory pre-flight

Re-read and obey at minimum:

```text
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md
docs/milestones/M1/steps.md
docs/milestones/M1/status.md

docs/milestones/M1/architecture/datatype.md
docs/milestones/M1/architecture/persistence-uow-concurrency.md
docs/milestones/M1/architecture/concurrency-postgresql-realization-matrix.md
docs/milestones/M1/architecture/concurrency-postgresql-test-matrix.md
docs/milestones/M1/architecture/api-contract.md
docs/milestones/M1/architecture/api-wire-contract.md
docs/milestones/M1/architecture/api-read-contract.md
docs/milestones/M1/architecture/api-list-contract.md
docs/milestones/M1/architecture/api-error-contract.md
```

No architecture contradiction was found by the review. These are implementation/verification findings only.

## Review finding 1 — canonical PGTEST IDs are not yet semantically complete

`tests/test_datatype_concurrency.py` currently uses canonical scenario IDs such as `ROW-01..06`, `ROW-15`, `ROW-16`, `ARB-01`, `PAR-06`, `PAR-07`, but most assertions exercise only raw lock/UNIQUE mechanics.

The frozen PGTEST contract requires both:

```text
semantic outcome assertions
+
mechanism assertions where the mechanism is normative
```

Semantic outcome assertions are always required. A test that only proves that two lock primitives block is not complete coverage of a canonical PGTEST scenario.

### Required correction

Keep useful persistence-level mechanism probes if desired, but do not treat them as complete canonical scenario coverage by themselves.

For each S02-realizable canonical scenario, add deterministic kernel/application-level coverage using the actual DataType semantic operations, independent real PostgreSQL UoWs/connections, and final semantic assertions:

```text
ROW-01  CREATE_NEXT × CREATE_NEXT same lineage
ROW-02  CREATE_NEXT × DELETE_DRAFT(max)
ROW-03  REVISE × REVISE same DRAFT generation
ROW-04A REVISE × PUBLISH same DRAFT generation
ROW-04B PUBLISH × DELETE_DRAFT same DRAFT generation
ROW-05  PUBLISH(vA) × PUBLISH(vB), default initially null
ROW-06  SET_DEFAULT(v) × DEPRECATE(v)
ROW-15  SET_DESCRIPTION × SET_DESCRIPTION
ROW-16  REVISE × DELETE_LINEAGE same aggregate
ARB-01  CREATE × CREATE same qualified name
PAR-06  DEPRECATE(v1) × DEPRECATE(v2), same lineage
PAR-07A SET_DESCRIPTION × SET_DEFAULT
PAR-07B SET_DESCRIPTION × REVISE
```

The tests must assert allowed serial outcomes and forbidden states, not a predetermined arbitrary winner.

Examples of required semantic properties:

- `ROW-01`: two successful serially explainable CREATE_NEXT operations allocate distinct versions; no duplicate allocation.
- `ROW-02`: waiter recomputes the current version set after wake-up; max-DRAFT deletion/reuse remains serially explainable.
- `ROW-03`: one revision based on generation N succeeds; the competing stale intent cannot also apply to the same generation; final constraints/revision equal one allowed winner state.
- `ROW-04A/B`: at most one operation based on the same DRAFT generation can win before the loser re-observes the committed lifecycle/generation state.
- `ROW-05`: both versions may become PUBLISHED serially, but exactly the first serial publish when default was null establishes the default; later publish does not replace it.
- `ROW-06`: never commit `default_version=v` together with `v=DEPRECATED`; one operation may force the other to fail according to the current state it sees.
- `ROW-15`: final description is one complete committed writer value; normal atomic LWW semantics only.
- `ROW-16`: no partial aggregate state; outcome must be serially explainable as revise-before-delete or delete-before-revise.
- `ARB-01`: exactly one qualified-name CREATE wins; the loser is translated to `qualified_name_conflict`, and no orphan/duplicate v1 state remains.
- `PAR-06`: both independent deprecations can make progress at the lineage-share level and both final states are valid when no blockers/default apply.
- `PAR-07A`: test the actual pair `SET_DESCRIPTION × SET_DEFAULT`, not `SET_DESCRIPTION × SET_DESCRIPTION`; header contention is intentional.
- `PAR-07B`: actual description mutation and DRAFT revise remain free of artificial lineage-owner serialization and both semantic outcomes remain correct.

Use the S01 harness and `pg_blocking_pids()` for positive blocker proof where applicable. Prefer real PostgreSQL blockers/constraints as orchestration. If a deterministic semantic interleaving cannot reasonably be cut at the required phase through PostgreSQL alone, the narrow test-only persistence phase interceptor permitted by PGTEST may be used; do not add production `if TESTING` hooks or sleep-based scheduling.

### ROW-07 / ROW-08 DataType-side mechanism

Do not manufacture a fake ObjectTemplate consumer.

The reusable persistence primitives already exist conceptually as caller-UoW operations:

```text
exact admission:
    exact DTV FOR SHARE -> fresh PUBLISHED validation

implicit admission:
    lineage FOR SHARE -> fresh default read -> exact DTV FOR SHARE -> fresh PUBLISHED validation
```

It is acceptable in S02 to prove the DataType-side lock mechanism at persistence level by keeping the caller UoW open while a competing lifecycle/default operation attempts to proceed. The full committed consumer scenario remains S03.

## Review finding 2 — remove misleading application-level binding helpers

`DataTypeService.admit_exact_binding()` and `DataTypeService.admit_default_binding()` each open their own UoW and return only after that UoW exits. Therefore the `FOR SHARE` locks are released before a future consumer could persist its exact binding and commit.

They must not be presented as the strong-consistency binding-admission capability.

Required correction:

- remove these two application-service convenience methods unless there is a concrete S02 caller that can preserve the same UoW;
- retain/reuse the persistence-level `DataTypeStore.admit_exact()` / `admit_default()` (or equivalent) on the **caller-owned semantic UoW connection**;
- S03 must be able to perform admission and consumer write in the same transaction without a lock gap;
- do not introduce a generic repository/DI abstraction to solve this.

## Review finding 3 — required S02 verification coverage is incomplete

Add focused tests for the requirements explicitly listed by the S02 step/prompt but not currently demonstrated.

### Primitive examples / properties

At minimum add explicit examples for the still-uncovered frozen cases:

```text
core.number
    reject NaN / Infinity lexical forms

core.date
    accepted lower/upper supported Gregorian bounds
    rejected out-of-range/zero-year values

core.datetime
    leap-second rejection
    >6 fractional digits all-zero acceptance
    >6 fractional digits non-zero rejection
    offset -> UTC conversion edge examples

core.ip / core.ip_prefix
    IPv4 and IPv6 examples
    netmask-alias rejection for prefix

core.byte_size
    SI vs IEC distinction
    case sensitivity / alias rejection
    zero-or-one ASCII-space rule, double-space rejection
    leading-plus / exponent / negative-string rejection
    exact fractional conversion success/failure

regex
    explicit fullmatch behavior (not substring search)
```

Add targeted Hypothesis coverage for byte-size/exact conversion and at least one canonical constraint/value idempotence/round-trip property in addition to the existing number property.

### DataType application/persistence/API cases

Add direct real-PostgreSQL/application/API evidence for at least:

```text
canonical constraint persistence round-trip
atomic CREATE lineage + v1
max-DRAFT deletion followed by version-number reuse
create-next missing source -> referenced_resource_not_found
create-next DRAFT source -> version_source_conflict
revise/publish/delete-draft lifecycle + stale-generation failures
set-default missing version / non-PUBLISHED target
first-publish auto-default and later-publish stability
clear-default
current-default deprecate blocker
PUBLISHED raw OTV property consumer -> active_dependency_conflict
DRAFT/DEPRECATED raw OTV consumer -> does not block deprecate
whole-lineage delete with internal default -> succeeds when no external refs
whole-lineage delete with external DTV reference -> delete_blocked / FK final authority
SET_DESCRIPTION nullable LWW behavior
exact GET and nested version summary/list behavior
lineage filters/order/keyset continuation
version status filter
cursor reused with changed filters -> invalid_cursor
missing/malformed expected_revision -> invalid_request
strict unknown/repeated body/query behavior as applicable
public errors never expose SQL/constraint internals
```

Tests may seed raw ObjectTemplate physical rows only where needed to exercise the already-frozen DataType active/reference authority. Do not implement ObjectTemplate commands or claim S03 capability.

## Quality gates

Run and report all of:

```text
uv lock
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -m "not postgresql"
uv run pytest -m postgresql
```

`TEST_DATABASE_URL` must point to the externally supplied dedicated real PostgreSQL target. Keep the PostgreSQL suite serial with respect to xdist when only one test DB is supplied.

## Completion report

Return:

- new commit SHA and confirmation pushed to `origin/core_review`;
- files changed;
- exact canonical PGTEST IDs now covered semantically and which ROW-07/08 pieces remain intentionally deferred to S03;
- verification command results and PostgreSQL version;
- confirmation the two misleading application binding helpers were removed or corrected to preserve caller-UoW lock lifetime;
- any architecture contradiction discovered;
- confirmation S03+ behavior was not implemented;
- confirmation `status.md` remains not-completed pending review.
