# M1 — Acceptance Candidate Evidence

**Record status:** S09 ACCEPTANCE CANDIDATE — verification record, not semantic
authority and not a declaration that M1 is delivered.

This document records bounded evidence produced from the integrated M1-S09 candidate.
It does not amend the frozen contract, architecture, API, persistence, concurrency or
technology decisions. Reviewer-owned delivery state remains in `status.md`; M1-S09 is
still `IN PROGRESS` until review completes.

## Authority and candidate boundary

The pre-flight confirmed:

```text
docs/milestones/M1/contract.md                FINAL / FROZEN
docs/milestones/M1/architecture/README.md     FROZEN as a set
docs/milestones/M1/steps.md                   FINAL / FROZEN
docs/general/technology_baseline.md            STACK-01..STACK-09 RATIFIED
docs/milestones/M1/status.md                  S00..S08 completed; S09 in progress
```

The owning architecture was re-read through the architecture index, semantic and
PostgreSQL realization/test matrices, persistence model/UoW contracts, API contract,
wire/read/list/error contracts and applicable domain contracts. No contradiction or
reopened design point was found. S09 adds traceability and delivery documentation; it
does not add or alter a kernel capability.

## Acceptance criteria

| Criterion | Result | Bounded implementation and verification evidence |
| --- | --- | --- |
| AC-01 PostgreSQL authority | PASS | `src/netauto/persistence/`, `Settings` Psycopg URL validation, the PostgreSQL-only dependency audit, `test_postgresql_support.py`, and 143 real-PostgreSQL tests. |
| AC-02 valid domain states | PASS | Domain and API suites for DataType, ObjectTemplate, Object and Relationship; targeted primitive properties; persistence metadata and constraint checks. |
| AC-03 cross-domain consistency | PASS | Canonical ROW-07..14 and REF-01..06 nodes in `test_m1_traceability.py`; ObjectTemplate/Object/Relationship API integration suites. |
| AC-04 transactional atomicity | PASS | ATOMIC-01..04 registry targets, `test_uow.py`, rollback paths in Object and Relationship API/semantic concurrency tests. |
| AC-05 concurrent correctness | PASS | Exact 51-ID PGTEST registry, exact 19-predicate map, 106 deterministic real-PostgreSQL concurrency tests, and 79 passing unique registry target nodes. |
| AC-06 persistence enforcement | PASS | `test_migrations.py`, `test_schema_metadata.py`, `test_persistence_constraints.py`; authoritative 13-table SQLAlchemy metadata and PostgreSQL PK/UNIQUE/FK/CHECK/index checks. |
| AC-07 API semantics | PASS | Exact OpenAPI census of 32 mutation and 20 read routes plus 23 public codes in `test_object_scope.py`; 30 real-PostgreSQL API tests across all four kernel domains. |
| AC-08 verification/invariant traceability | PASS | `test_m1_traceability.py` mechanically checks the exact 51 scenarios, concrete pytest node existence/PostgreSQL markers, and exact closed 19-predicate map. T0..T6 evidence is recorded below. |
| AC-09 runtime/test database separation | PASS | `NETAUTO_DATABASE_URL` is owned by runtime/settings/Alembic; `TEST_DATABASE_URL` is read only by test support. `test_settings.py`, `test_postgresql_support.py`, and `test_http_composition.py` verify separation and external provisioning. |
| AC-10 no alternative-backend burden | PASS | Dependency/source audit found no supported SQLite/in-memory backend or portability framework. Plain domain boundaries remain verified by scope tests. |

## STACK-07 verification layers

| Layer | Result | Evidence |
| --- | --- | --- |
| T0 pure domain | PASS | `test_primitives.py`, `test_object_domain.py`, `test_objecttemplate_domain.py`, `test_relationship_domain.py`, `test_relationshipdefinition_domain.py`. |
| T1 application/orchestration | PASS | Direct service orchestration in the four `test_*_semantic_concurrency.py` suites plus explicit UoW tests. |
| T2 real-PostgreSQL persistence | PASS | API integration, persistence constraint, schema metadata, UoW and PostgreSQL support tests. |
| T3 deterministic real-PostgreSQL concurrency | PASS | 106 `postgresql and concurrency` tests; independent sessions, observed blockers/gates/constraints and no correctness `sleep()`. |
| T4 API contract/integration | PASS | 30 `postgresql and api` tests plus the cheap exact OpenAPI/error-catalog scope test. |
| T5 migration/schema | PASS | Clean base→head, 0001→0002, downgrade/upgrade, schema structure and empty metadata-drift checks. |
| T6 targeted properties | PASS | 4 Hypothesis tests for exact number, byte-size and primitive canonicalization properties. |
| T7 randomized/stress | Supplementary only | Not required or used as a substitute for T3; no T7 result is claimed by this acceptance candidate. |

## PGTEST and safety-predicate closure

`tests/test_m1_traceability.py` holds the durable registry. Its keys are mechanically
checked against this exact census:

```text
ROW     17 / 17
ARB      7 / 7
REF      6 / 6
GATE     6 / 6
SNAP     4 / 4
ATOMIC   4 / 4
PAR      7 / 7
total   51 / 51
```

Variants are values under their canonical parent IDs; they do not inflate the census.
The registry currently resolves to 79 unique concrete pytest functions. Every target
exists and carries the real-PostgreSQL marker; the direct target selection passed all
79 nodes.

The same file checks this exact non-`I` predicate set and requires every mapping to be
non-empty and refer only to canonical scenario IDs:

```text
NU VS DG LS DV BA AM RL AL ML OS PO OF SO OC RC RF RA ES
= 19 / 19
```

The mapping is identical to PGTEST-02: `RL` spans REF-01..06, while composed ATOMIC
and PAR evidence remains beneath canonical parent IDs. No missing canonical scenario
or predicate required a production change.

## API closure

The generated OpenAPI surface is compared to exact sets, not minimum counts:

```text
mutation routes     32 / 32
read/list routes    20 / 20
public error codes  23 / 23
namespace           /api/v1/core
```

`test_object_scope.py::test_s08_public_route_and_error_catalog_closure` also rejects
PUT/PATCH, action DSLs, autonomous RelationshipResolution/ObjectComponent mutation
routes and JSON Schema endpoints. Domain API suites verify strict bodies, unknown-field
and coercion rejection, omission versus explicit null, positive exact `expected_revision`,
selector rules, PrimitiveType lexical/canonical forms, success bodies/status/`Location`,
bounded error details and the frozen list/cursor/filter behavior.

## Database and migration closure

Verification used externally supplied PostgreSQL
`16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)` through `TEST_DATABASE_URL`; no credential or
database URL is recorded here.

`test_initial_revision_structure_drift_and_owned_downgrade` proved:

- clean Alembic `base` → `head` succeeds;
- committed `0001_m1_schema` and `0002_relationship_resolution_name_nonkey` compose;
- the 0002 downgrade restores exactly the prior semantic-child UNIQUE and re-upgrade
  removes it;
- migrated schema versus authoritative metadata has no differences;
- the 13 tables, keys, FKs, constraints and PERSIST-15 indices have the frozen shapes;
- Alembic downgrade removes only NETAUTO-owned objects and preserves an external
  sentinel;
- application lifespan does not invoke Alembic or otherwise migrate implicitly.

The focused migration/schema/persistence/composition/surface group passed 15 tests.

## Reproducibility and final command ledger

Commands were run from the repository root with one externally managed PostgreSQL
test target, serially and without xdist:

| Command | Result |
| --- | --- |
| `uv lock --check` | PASS — 44 packages resolved |
| `uv sync --locked` | PASS — 42 packages checked |
| `uv run python --version` | PASS — Python 3.14.7 |
| `uv build` | PASS — sdist and wheel built |
| `uv tree --depth 1` | PASS — ratified runtime/dev stack only |
| `uv run ruff format --check .` | PASS — 114 files formatted |
| `uv run ruff check .` | PASS |
| `uv run pyright` | PASS — 0 errors, 0 warnings |
| `uv run pytest -q tests/test_m1_traceability.py` | PASS — 3 passed |
| `uv run pytest -q -m 'not postgresql'` | PASS — 125 passed, 143 deselected |
| `uv run pytest -q` | PASS — 268 passed |
| `uv run pytest -q -m postgresql` | PASS — 143 passed, 125 deselected |
| `uv run pytest -q -m 'postgresql and concurrency'` | PASS — 106 passed, 162 deselected |
| `uv run pytest -q -m 'postgresql and api'` | PASS — 30 passed, 238 deselected |
| `uv run pytest -q -m 'postgresql and migration'` | PASS — 1 passed, 267 deselected |
| `uv run pytest -q -m property` | PASS — 4 passed, 264 deselected |
| direct unique registry-target selection | PASS — 79 passed |
| focused migration/schema/persistence/composition/surface selection | PASS — 15 passed |
| `uv run coverage run -m pytest -q` | PASS — 268 passed |
| `uv run coverage report` | PASS — 3,749 statements, 87% branch-aware aggregate |

The coverage missing-branch report was inspected. Remaining uncovered lines are
predominantly defensive validation/error branches and do not expose a missing frozen
acceptance behavior; coverage is supplementary evidence and no threshold was invented.

The documentation stale-marker sweep found only normative workflow text and the
reviewer-owned `IN PROGRESS` state. No frozen semantic document was edited to match an
implementation accident. The root README now records the verified CPython/uv setup,
explicit Alembic administration, Uvicorn factory, runtime/test database separation and
serial real-PostgreSQL verification commands.
