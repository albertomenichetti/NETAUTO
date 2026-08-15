# NETAUTO

> **Candidate replacement for `README.md`.** Until this file is reviewed and promoted, the existing root `README.md` remains the repository operational entry point. Promotion of this candidate also assumes that `AGENTS_v2.md` is reviewed and promoted to `AGENTS.md`.

NETAUTO is a REST-API-first dynamic infrastructure modeling kernel.

The current delivered baseline is correctness-first and PostgreSQL-only. It models four core concepts:

```text
DataType
ObjectTemplate
Object
Relationship
```

The public kernel API is exposed below:

```text
/api/v1/core
```

## Current operational state

This section is the repository-level current-state projection. It must be updated whenever the active baseline, cycle, branch, phase, slice, execution aid or immediate next action changes.

| Field | Current value |
|---|---|
| Delivered baseline | `M1 — Kernel Consistency Baseline` |
| Baseline status | `DELIVERED` |
| Current AS-IS authority | [`docs/architecture/README.md`](docs/architecture/README.md) |
| Active code cycle | None |
| Active branch | `core_review` |
| Current phase | Post-delivery governance/documentation consolidation and formal branch closure |
| Active slice | None |
| Current task | Review and promote `AGENTS_v2.md` and `README_v2.md`, complete the reference sweep, then close the branch through the human-owned merge process |
| Active execution aids | [`AGENTS_v2.md`](AGENTS_v2.md), `README_v2.md` |
| Code changes currently permitted | No. A new code change requires an explicitly opened milestone `Mx` or fix `Fx-y` cycle |
| Immediate next action | Reviewer comparison and promotion of the candidate root documents |
| Merge ownership | Human only; coding agents never merge the cycle branch to `master` |

The detailed delivered M1 state remains authoritative in [`docs/milestones/M1/status.md`](docs/milestones/M1/status.md).

This README is a navigator and operational status projection, not a semantic authority. If this section disagrees with the current Git branch or an active cycle's authoritative `status.md`, stop and reconcile the repository state before continuing.

## How to start repository work

1. Read this README to determine the current baseline, cycle, phase, branch, slice, task and immediate next action.
2. Coding agents must then read [`AGENTS.md`](AGENTS.md) before modifying the repository.
3. Read [`docs/general/linee_guida_progetto.md`](docs/general/linee_guida_progetto.md) for milestone/fix governance, freeze, review and closure rules.
4. Enter the current delivered architecture through [`docs/architecture/README.md`](docs/architecture/README.md).
5. If a milestone or fix is active, follow the linked active-cycle contract/defect scope, frozen architecture where applicable, `steps.md`, `status.md` and current execution aid.
6. Read every ratified technology decision applicable to the task in [`docs/general/technology_baseline.md`](docs/general/technology_baseline.md).
7. If README, branch, active-cycle documents or task instructions disagree, do not infer intent from recency, code or chat history; stop and report the mismatch.

## Documentation map

| Source | Responsibility |
|---|---|
| [`README.md`](README.md) | Operational entry point: current baseline, active cycle, phase, branch, slice, task and next action. |
| [`AGENTS.md`](AGENTS.md) | Repository operating contract for coding agents. It governs how agents work, not what the system means. |
| [`docs/general/linee_guida_progetto.md`](docs/general/linee_guida_progetto.md) | General governance for milestone and fix cycles, documentation roles, freeze/reopen, reviewer ownership, final gates and closure. |
| [`docs/architecture/README.md`](docs/architecture/README.md) | Entry point and authority map for the current delivered AS-IS. |
| [`docs/architecture/`](docs/architecture/) | Current semantic, persistence, concurrency, API and verification architecture. |
| [`docs/general/technology_baseline.md`](docs/general/technology_baseline.md) | Project-wide implementation technologies and tooling; only ratified `STACK-*` decisions are authoritative while the document remains DRAFT. |
| `docs/milestones/<Mx>/` | Active milestone TO-BE and permanent historical milestone record after delivery. |
| `docs/fixes/<Fx-y>/` | Active corrective scope/design and permanent historical fix record after delivery. |
| active `steps.md` | Frozen implementation decomposition and traceability for the current cycle. |
| active `status.md` | Detailed current operational state; reviewer-owned completion and delivery status. |
| active `wip/` | Temporary, non-normative execution aids. |
| code, tests, schema, OpenAPI and Git history | Implementation and evidence sources; never autonomous semantic authority. |

A future milestone starts from `docs/architecture/` and may diverge from it only through an explicit contract-derived, frozen TO-BE decision. A fix corrects behavior already owed by the delivered baseline and cannot be used to introduce a new capability or intentional public-contract change.

## Delivered baseline: M1

M1 established the PostgreSQL-backed kernel baseline for:

- versioned scalar `DataType` semantics and canonical primitive values;
- versioned `ObjectTemplate` schemas, inheritance, properties and component slots;
- runtime `Object` state, schema migration, ownership and lifecycle history;
- `RelationshipDefinition` / `RelationshipResolution` model-plane semantics;
- factual runtime `Relationship` closure and navigation;
- cross-domain reference and deletion integrity;
- strict HTTP/JSON command, read, list and failure contracts;
- deterministic real-PostgreSQL concurrency verification.

The current architecture is consolidated in [`docs/architecture/`](docs/architecture/). The M1 directory is the permanent historical record of how that baseline was designed, implemented and accepted:

- [`contract.md`](docs/milestones/M1/contract.md) — frozen scope, non-goals and acceptance criteria;
- [`architecture/README.md`](docs/milestones/M1/architecture/README.md) — frozen M1 architecture-set index;
- [`steps.md`](docs/milestones/M1/steps.md) — frozen implementation decomposition;
- [`status.md`](docs/milestones/M1/status.md) — delivered milestone state;
- [`acceptance.md`](docs/milestones/M1/acceptance.md) — final acceptance evidence.

Historical milestone documents do not replace the current AS-IS in `docs/architecture/`.

## Repository layout

```text
src/netauto/
    kernel implementation

migrations/
    explicit Alembic schema history

tests/
    domain, application, real-PostgreSQL, concurrency,
    API, migration and property verification

docs/architecture/
    current delivered AS-IS

docs/general/
    project governance and technology baseline

docs/milestones/
    milestone TO-BE and historical records

docs/fixes/
    fix-cycle scope/design and historical records, when present
```

## Requirements

- CPython `3.14.x`;
- `uv`;
- an externally provisioned PostgreSQL database.

PostgreSQL URLs use SQLAlchemy's Psycopg driver form:

```text
postgresql+psycopg://user:password@host/database
```

Runtime and automated-test database targets are separate:

```text
NETAUTO_DATABASE_URL
    -> application runtime and explicit Alembic administration target

TEST_DATABASE_URL
    -> automated real-PostgreSQL verification target
```

The application and test suite do not provision PostgreSQL. Application startup never applies migrations implicitly.

## Setup and build

Reproduce the committed environment and build the project artifacts:

```bash
uv lock --check
uv sync --locked
uv build
```

## Database migration

Set the explicit runtime/administrative target and apply the committed Alembic history:

```bash
export NETAUTO_DATABASE_URL='postgresql+psycopg://user:password@host/runtime_database'
uv run alembic upgrade head
```

Migration is an explicit administrative operation. Do not point the command at a database whose contents may be discarded unless that is intentional.

## Run the API

After migrating the runtime database, start the explicit Uvicorn application factory:

```bash
export NETAUTO_DATABASE_URL='postgresql+psycopg://user:password@host/runtime_database'
uv run uvicorn netauto.entrypoints.http:create_app --factory
```

The kernel API is available below `/api/v1/core`.

## Verification

### Static, build and non-PostgreSQL gates

```bash
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -q -m 'not postgresql'
```

The current delivered-baseline traceability registry can be verified independently:

```bash
uv run pytest -q tests/test_m1_traceability.py
```

### Complete real-PostgreSQL suite

Provide a dedicated external test database and run the complete suite:

```bash
export TEST_DATABASE_URL='postgresql+psycopg://user:password@host/test_database'
uv run pytest -q
```

When only one test database is available, run PostgreSQL tests serially. Do not add `-n`/xdist unless every worker receives an externally managed isolated PostgreSQL database target.

### Focused selections

```bash
uv run pytest -q -m 'postgresql and concurrency'
uv run pytest -q -m 'postgresql and api'
uv run pytest -q -m 'postgresql and migration'
uv run pytest -q -m property
```

The owning verification requirements are documented in:

- [`docs/architecture/verification.md`](docs/architecture/verification.md);
- [`docs/architecture/verification-concurrency-registry.md`](docs/architecture/verification-concurrency-registry.md);
- the active cycle's frozen steps and acceptance/regression requirements, when a cycle is open.

A command that cannot be run must be reported explicitly; unavailable PostgreSQL infrastructure is never replaced by SQLite or another backend.

## Repository operating rules

- Code-base changes occur only inside an explicitly opened milestone `Mx` or fix `Fx-y` cycle.
- Each cycle uses a dedicated branch and zero-padded slice identifiers such as `M2-S01` or `F1-1-S01`.
- Coding agents follow `AGENTS.md` and produce review candidates; they do not self-assign `COMPLETED`, `DELIVERED` or `ACCEPTED`.
- A documentation contradiction is not an implementation choice. Affected work stops until the owning authorities are reconciled and, when required, re-frozen.
- The merge to `master` is always human-owned.
- Git history is available for deliberate evidence or historical inspection, but removed historical code is not an implicit compatibility target or architecture authority.

## Maintaining this README

This README must remain concise, current and operational.

Update the **Current operational state** section whenever any of these change:

```text
delivered baseline
active cycle
active branch
phase
slice or task
status
execution aid
immediate next action
```

The README should link to owning authorities rather than duplicate their detailed semantics. Active-cycle `status.md` remains the detailed operational authority; `docs/architecture/` remains the delivered semantic authority. A mismatch between this README and those sources is a repository-state defect that must be resolved before dependent work continues.
