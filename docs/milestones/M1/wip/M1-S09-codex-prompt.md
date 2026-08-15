# Codex implementation prompt — M1-S09 full acceptance and delivery gate

**Status:** NON-NORMATIVE IMPLEMENTATION / ACCEPTANCE PROMPT.

This file is an execution aid only. It does not override `AGENTS.md`, the FINAL/FROZEN M1 contract/steps, the globally FROZEN M1 architecture, or the ratified technology baseline.

## Assignment

Execute exactly:

```text
M1-S09 — Full M1 acceptance, regression and delivery gate
```

M1-S00 through M1-S08 are complete and accepted. S09 introduces **no new kernel capability**. Its purpose is to prove that the integrated repository satisfies the entire frozen M1 contract, close machine-checkable verification/traceability, update delivery documentation, and produce the final acceptance candidate for reviewer approval.

Accepted S08 implementation baseline:

```text
678da20904bec7eb16a6baff45f26a80890dbcae
+
30fa3be16bef705c1e7df1d4c4e66679badf8c72
    REF-06 verification-closure review fix
```

The S07 physical correction remains part of the frozen baseline:

```text
RelationshipResolution.name = mutable non-key metadata
0002_relationship_resolution_name_nonkey.py
    upgrade   -> drops uq_relationship_resolutions_semantic_child
    downgrade -> restores exactly that constraint
```

Do not rewrite `0001` or `0002`.

---

# 1. Mandatory pre-flight

Before changing any repository file, re-read and obey at minimum:

```text
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

docs/milestones/M1/contract.md
docs/milestones/M1/steps.md
docs/milestones/M1/status.md

docs/milestones/M1/architecture/README.md
docs/milestones/M1/architecture/m1-final-consistency-review.md
docs/milestones/M1/architecture/concurrency-semantic-matrix.md
docs/milestones/M1/architecture/concurrency-postgresql-realization-matrix.md
docs/milestones/M1/architecture/concurrency-postgresql-test-matrix.md
docs/milestones/M1/architecture/persistence-model.md
docs/milestones/M1/architecture/persistence-uow-concurrency.md

docs/milestones/M1/architecture/api-contract.md
docs/milestones/M1/architecture/api-wire-contract.md
docs/milestones/M1/architecture/api-read-contract.md
docs/milestones/M1/architecture/api-list-contract.md
docs/milestones/M1/architecture/api-error-contract.md
```

Also inspect all owning DataType/ObjectTemplate/Object/Relationship documents when building AC traceability or when a verification result depends on their invariant semantics.

Confirm from the repository itself:

```text
M1 contract      FINAL / FROZEN
M1 architecture  globally FROZEN as a set
M1 steps         FINAL / FROZEN
M1-S00..S08      COMPLETED
current step     M1-S09
STACK-01..09     RATIFIED
```

Important set-level freeze rule:

> individual architecture documents may still carry older authoring labels such as `DRAFT`; `architecture/README.md` + FREEZE-01 are the authoritative global freeze state. Do not treat those headers as open design and do not mass-edit them merely to make labels look uniform.

If the acceptance gate exposes a genuine semantic/technical contradiction in the frozen architecture, stop the affected work and report it. Do not weaken tests or silently change semantics to obtain a green gate.

---

# 2. S09 scope discipline

S09 is verification/delivery closure, not feature work.

Expected changes are primarily:

```text
machine-checkable acceptance/traceability tests
README delivery/run/test documentation
M1 acceptance evidence document
small test/evidence corrections if a coverage gap exists
editorial-only documentation cleanup for demonstrably stale implementation markers
```

Production code may change **only** if the full acceptance gate exposes a real implementation defect against already-frozen behavior. Any such fix must include the smallest permanent regression proving the defect and must not broaden M1 scope.

Do not add:

```text
new domain capability
new API route
new persistence backend
new table/column/gate
new framework/tool dependency without a ratified need
JSON Schema capability
Object/Relationship functionality beyond frozen M1
M2/RFE implementation
```

No architecture semantics may be changed under the guise of a documentation sweep.

---

# 3. Machine-checkable canonical PGTEST traceability

M1-S09 must not rely on a prose assertion that the concurrency suite is complete.

The canonical authority is:

```text
44 correctness scenario IDs
+ 7 T-PAR IDs
= 51 canonical scenario IDs
```

Families/counts:

```text
ROW-01..ROW-17       17
ARB-01..ARB-07        7
REF-01..REF-06        6
GATE-01..GATE-06      6
SNAP-01..SNAP-04      4
ATOMIC-01..ATOMIC-04  4
PAR-01..PAR-07        7
                      --
                      51
```

The 19 non-I safety predicates are exactly:

```text
NU VS DG LS DV BA AM RL AL ML OS PO OF SO OC RC RF RA ES
```

## 3.1 Add a durable traceability test/registry

Create a cheap, non-PostgreSQL test module such as:

```text
tests/test_m1_traceability.py
```

(or an equivalently clear test/support split) that contains an explicit registry from every canonical PGTEST ID to one or more real pytest test functions/nodes that exercise it.

Requirements:

- exact canonical ID set is asserted to contain all and only the 51 IDs above;
- every canonical ID maps to at least one concrete current test target;
- mapped test targets must actually exist in the repository; validate this mechanically (for example by AST/function discovery or another deterministic collection-safe method), not with unvalidated comments/strings;
- one concrete test may legitimately map to multiple canonical IDs when it intentionally proves multiple authorities, e.g. a combined GATE/fresh-snapshot regression;
- variants A/B/C remain under the canonical parent ID where frozen PGTEST does so; do not invent new canonical scenario IDs;
- do not rename away existing canonical IDs merely to satisfy the registry;
- the registry is traceability evidence, not a substitute for running the real PostgreSQL tests.

## 3.2 Predicate coverage registry

In the same acceptance/traceability surface, retain an explicit mapping for all 19 safety predicates to canonical scenario IDs matching the frozen `concurrency-postgresql-test-matrix.md` coverage map.

Mechanically assert:

```text
predicate set == exact 19 IDs
all mapped scenario IDs are in the exact 51-ID canonical set
no predicate has an empty scenario set
```

Do not invent a twentieth predicate or reinterpret `I` cells as safety predicates.

## 3.3 Discover gaps rather than hiding them

Audit the current tests before writing the final registry.

If any canonical ID is not truly exercised by an existing deterministic real-PG test, add the smallest missing regression against the already-frozen authority. Do not map an unrelated test merely because its final state happens to look similar.

Mechanism-sensitive scenarios must retain actual evidence for their frozen mechanism where required, including:

```text
row-lock rendezvous / fresh post-wait state
FK / PK / UNIQUE arbitration
advisory-gate blocking + post-gate fresh snapshot
over-serialization probes
non-blocking probes
fresh semantic-UoW convergence
one-statement metadata snapshot behavior
atomic rollback
```

No sleep-based correctness orchestration.

---

# 4. M1 acceptance evidence document

Create:

```text
docs/milestones/M1/acceptance.md
```

This is a **verification/delivery record**, not a new semantic architecture authority. Say so explicitly near the top.

It must contain concise but explicit final evidence for:

## 4.1 AC-01..AC-10 traceability

For each acceptance criterion:

```text
AC-01 PostgreSQL authority
AC-02 valid domain states
AC-03 cross-domain consistency
AC-04 transactional atomicity
AC-05 concurrent correctness
AC-06 persistence enforcement
AC-07 API semantics
AC-08 verification/invariant traceability
AC-09 runtime/test DB separation
AC-10 no alternative-backend burden
```

record:

- the relevant frozen authority/authorities;
- implementation evidence at a useful bounded level;
- concrete test files / canonical PGTEST IDs / acceptance checks that prove it;
- final result PASS only when the corresponding gate has actually run successfully.

Do not use vague text such as “covered by tests”.

## 4.2 STACK-07 layer closure

Record evidence for the complete M1 verification model:

```text
T0 pure domain
T1 application/orchestration
T2 real-PG persistence
T3 deterministic real-PG concurrency
T4 API contract/integration
T5 migration/schema
T6 targeted Hypothesis properties
```

The layers need not be disjoint; a direct application-service test backed by real PostgreSQL may contribute to both orchestration and integration evidence. Do not create artificial fake-backed tests solely to make the layer labels disjoint.

T7 stress/randomized concurrency is supplementary and is not required to claim the deterministic M1 gate.

## 4.3 PGTEST + predicate closure

Record the exact final:

```text
51 / 51 canonical PGTEST IDs traceable and passing
19 / 19 non-I predicates traceable
```

with a pointer to the machine-checkable registry/test and the real-PG execution command/result.

## 4.4 API closure

Record the existing exact census:

```text
32 mutation routes
20 read routes
23 public error codes
```

plus strict input/omission/null, PrimitiveType lexical, expected_revision, success/Location, forbidden PUT/PATCH/autonomous-child and no-JSON-Schema surface evidence.

Do not create a second API authority; point to the existing API contracts and tests.

## 4.5 Database/migration closure

Record:

```text
PostgreSQL server version used
clean schema -> Alembic head result
0001 + 0002 head chain
metadata vs migrated schema drift result
representative persistence constraint checks
startup/factory does not run migrations implicitly
```

## 4.6 Reproducibility/static closure

Record exact successful commands and final counts/results for the gates in section 6 below.

Do not include secrets or the actual credential-bearing database URL.

---

# 5. README delivery closure

Update root `README.md` from the old clean-slate/bootstrap wording to the **actual M1 repository**.

The README must remain concise and operationally truthful. Include at minimum:

## 5.1 Prerequisites

```text
CPython 3.14.x
uv
externally managed PostgreSQL
```

No Docker/Testcontainers provisioning claim.

## 5.2 Environment boundaries

Explain separately:

```text
NETAUTO_DATABASE_URL
    runtime / explicit administrative migration target

TEST_DATABASE_URL
    dedicated automatic-test PostgreSQL target
```

Both use `postgresql+psycopg://...`.

Do not imply that the application provisions PostgreSQL or falls back to SQLite.

## 5.3 Reproducible setup/build

Use verified real commands, including:

```text
uv sync --locked
uv build
```

Mention the repository `.python-version` / project Python 3.14 constraint as appropriate.

## 5.4 Explicit migrations

Document the verified administrative command, conceptually:

```text
NETAUTO_DATABASE_URL='postgresql+psycopg://...' uv run alembic upgrade head
```

State clearly that application startup/lifespan does not auto-run migrations.

## 5.5 Run the API

Document the verified Uvicorn factory command, conceptually:

```text
NETAUTO_DATABASE_URL='postgresql+psycopg://...' \
uv run uvicorn netauto.entrypoints.http:create_app --factory
```

Mention `/api/v1/core` as the public kernel namespace. Do not add an application CLI that M1 does not have.

## 5.6 Verification commands

Document at least:

```text
uv run pytest -m 'not postgresql'
TEST_DATABASE_URL='postgresql+psycopg://...' uv run pytest
uv run ruff format --check .
uv run ruff check .
uv run pyright
```

Optionally document useful focused PostgreSQL/concurrency/migration/property selections if verified.

Warn that with one `TEST_DATABASE_URL`, PostgreSQL suites run serially; do not recommend `-n auto` for the shared PG target.

Do not claim M1 is reviewer-delivered in README before reviewer approval. Prefer wording that points to `docs/milestones/M1/status.md` for authoritative operational delivery state.

---

# 6. Required final verification commands

Use the committed project environment and the externally supplied `TEST_DATABASE_URL`.

## 6.1 Runtime/toolchain/reproducibility

Run and report at minimum:

```text
uv lock --check
uv sync --locked
uv run python --version
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
```

Confirm Python resolves to CPython 3.14.x and agrees with `.python-version`, `requires-python`, Ruff and Pyright targets.

Audit direct project dependencies/tooling against STACK-01..09. Confirm no obsolete alternative persistence/framework/tool authority has re-entered (e.g. runtime SQLite/in-memory backend, ORM Session authority, Gunicorn requirement, duplicate formatter/type-checker stack).

Do not flag transitive dependencies merely by name without understanding why they are present.

## 6.2 Test layers and full suite

Run at minimum:

```text
uv run pytest -m 'not postgresql'

TEST_DATABASE_URL='...' uv run pytest

TEST_DATABASE_URL='...' uv run pytest -m 'postgresql and concurrency'
TEST_DATABASE_URL='...' uv run pytest -m api
TEST_DATABASE_URL='...' uv run pytest -m migration
uv run pytest -m property
```

Use serial execution for the real-PG suite when only the single externally supplied test database is available. Do not use xdist in a way that violates the database isolation contract.

If a marker selection legitimately includes tests that do not require PostgreSQL, that is fine; report actual collected/pass counts rather than inventing disjoint layer counts.

Also run the new cheap M1 traceability/acceptance tests directly.

## 6.3 Coverage diagnostic

Because branch coverage is part of STACK-07 review tooling, produce a coverage diagnostic for the integrated suite, preferably against the full suite with the test PostgreSQL target:

```text
TEST_DATABASE_URL='...' uv run coverage run -m pytest
uv run coverage report
```

No arbitrary percentage threshold is introduced. Report the result and inspect missing branches in critical domain/application/persistence/error paths for obvious acceptance gaps. A low-risk uncovered utility branch is not by itself an architecture defect; a critical untested semantic branch is.

Do not run a coverage-only subset as a substitute for the ordinary full suite.

## 6.4 Migrations/schema

Run the existing real-PG migration/schema/drift tests from a clean schema and report exact counts.

Confirm:

```text
empty/base -> head succeeds
head includes 0001 + 0002
metadata matches migrated head with no unexplained drift
0002 downgrade restoration behavior remains covered
application factory/lifespan does not execute migrations
```

Do not add a migration merely because S09 exists.

## 6.5 Canonical PGTEST gate

Run all actual real-PG tests referenced by the 51-ID traceability registry and prove every mapped target passes.

A practical implementation may generate a deterministic node list from the registry for an explicit focused run, or may prove that the full concurrency selection contains all mapped targets. In either case the acceptance record must make it auditable that all 51 canonical IDs were represented by passing real-PG tests.

Do not confuse “51 canonical IDs” with “exactly 51 pytest functions”: A/B/C variants and combined authority tests may produce a different pytest function/item count.

---

# 7. Final documentation consistency sweep

Search the **current** repository documentation for implementation-era stale markers such as, where contextually relevant:

```text
TODO
FIXME
TBD
OPEN
still to be finalized
next API point
not implemented yet
placeholder
```

Evaluate context; do not mechanically replace words.

Rules:

- historical/Git-removed docs are not restored;
- `docs/milestones/M1/wip/` is non-normative and the S09 prompt itself is expected while work is active;
- old individual architecture `Status: DRAFT` labels do **not** imply open architecture because global FREEZE-01 is authoritative;
- RFE/future-work text is not stale merely because it describes intentionally deferred capability;
- if a sentence incorrectly describes an already-implemented M1 item as open, make the smallest editorial correction consistent with existing frozen semantics;
- editorial correction must not change domain/API/persistence/concurrency meaning;
- any change that would alter a frozen decision is an architecture finding: stop and report instead of editing it through S09.

Do not create new RFEs merely to tidy wording. Existing deferred items remain in their owning architecture/RFE sections.

---

# 8. Status ownership

Do **not** mark M1-S09 `COMPLETED` and do **not** mark M1 `DELIVERED` in `docs/milestones/M1/status.md`.

Final completion/delivery status is reviewer-owned after GitHub delta review and verification-evidence review.

The reviewer will perform the final required `status.md` transition after accepting the S09 candidate.

Do not modify status merely to echo this prompt.

---

# 9. Failure handling during S09

If a test/gate fails:

```text
implementation defect against frozen contract
    -> add/keep deterministic regression
    -> make smallest implementation fix
    -> rerun affected + full gates

verification/traceability gap only
    -> add explicit durable evidence/test mapping
    -> do not change production behavior

true architecture contradiction/missing frozen decision
    -> STOP affected work
    -> report exact conflicting authorities
    -> do not weaken test or choose semantics in code
```

Do not hide failures with skips, xfails, reruns or broader exception handling unless such behavior is already a frozen contract.

---

# 10. Expected final repository shape

A clean successful S09 candidate should normally include:

```text
README.md                                  updated operational delivery README
docs/milestones/M1/acceptance.md          explicit acceptance/traceability evidence
tests/test_m1_traceability.py             durable 51-ID / 19-predicate registry checks
```

plus only the smallest additional tests/editorial corrections that the final gate proves necessary.

Production-code changes are not expected and must be called out explicitly if they become necessary.

No new migration is expected.

---

# 11. Completion report

After all required gates pass:

1. commit and push directly to `core_review` (no PR);
2. leave the working tree clean and synchronized with remote;
3. report:

```text
commit SHA
changed files
whether production code changed
whether normative architecture docs changed (and why, if editorial-only)
README update summary
acceptance.md summary
51/51 PGTEST traceability result
19/19 predicate traceability result
AC-01..AC-10 result
T0..T6 evidence summary
32 mutation / 20 read / 23 error-code census result
Python version
PostgreSQL version
uv lock/sync/build result
Ruff result
Pyright strict result
non-PG pass count
full-suite pass count
real-PG/concurrency/API/migration/property selection counts
coverage branch diagnostic
migration/head/drift result
confirmation application startup does not migrate
confirmation no alternative backend burden returned
confirmation no architecture contradiction remains
```

Do not mark the milestone delivered yourself. Reviewer owns the final acceptance and status transition.
