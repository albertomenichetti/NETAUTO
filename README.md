# NETAUTO

NETAUTO is a REST-API-first dynamic infrastructure modeling kernel.

The M1 kernel implementation has been rebuilt from a frozen design baseline. The previous implementation was intentionally removed: current code derives from the normative repository documentation rather than from historical package structure or behavior.

## Current milestone

M1 — **Kernel Consistency Baseline** — consolidates the four core concepts:

- `DataType`;
- `ObjectTemplate`;
- `Object`;
- `Relationship`.

M1 is correctness-first and PostgreSQL-only. Domain semantics, persistence, Unit of Work boundaries, concurrency guarantees, HTTP API contracts and verification requirements form one coherent kernel baseline.

**M1 is delivered.** The milestone contract is `FINAL / FROZEN`, the M1 architecture is globally `FROZEN`, the implementation decomposition in `docs/milestones/M1/steps.md` is `FINAL / FROZEN`, and all implementation/acceptance steps `M1-S00..M1-S09` are complete.

## Documentation authority

Repository documentation is the source of truth for implementation.

Start here:

- [`AGENTS.md`](AGENTS.md) — operating rules for Codex/coding agents;
- [`docs/general/linee_guida_progetto.md`](docs/general/linee_guida_progetto.md) — project workflow, freeze and documentation-alignment rules;
- [`docs/general/technology_baseline.md`](docs/general/technology_baseline.md) — project-wide technology decisions; only explicitly ratified STACK decisions are authoritative while the document remains DRAFT;
- [`docs/milestones/M1/contract.md`](docs/milestones/M1/contract.md) — frozen M1 scope and acceptance criteria;
- [`docs/milestones/M1/architecture/README.md`](docs/milestones/M1/architecture/README.md) — frozen M1 architecture index and normative document map;
- [`docs/milestones/M1/steps.md`](docs/milestones/M1/steps.md) — frozen implementation decomposition;
- [`docs/milestones/M1/status.md`](docs/milestones/M1/status.md) — final operational milestone state;
- [`docs/milestones/M1/acceptance.md`](docs/milestones/M1/acceptance.md) — final bounded acceptance and verification record.

If documentation authorities conflict, the conflict is an architecture/documentation defect. It must be resolved in the documentation before affected behavior is changed.

## Requirements

- CPython 3.14;
- [uv](https://docs.astral.sh/uv/);
- an externally provisioned PostgreSQL database.

PostgreSQL URLs must use SQLAlchemy's Psycopg driver form:

```text
postgresql+psycopg://user:password@host/database
```

Runtime and test databases are configured separately. The application and Alembic read `NETAUTO_DATABASE_URL`; the test suite reads only `TEST_DATABASE_URL`. Neither path provisions PostgreSQL, and application startup never runs migrations.

## Setup and build

Reproduce the locked development environment and build both distribution artifacts:

```bash
uv sync --locked
uv build
```

## Database migration

Set the explicit administrative/runtime target, then migrate it to Alembic head:

```bash
export NETAUTO_DATABASE_URL='postgresql+psycopg://user:password@host/runtime_database'
uv run alembic upgrade head
```

Migrations are an explicit administrative operation. The committed M1 chain is `0001` followed by `0002`; do not point this command at a database whose contents may be discarded unless that is intentional.

## Run the API

After migrating the runtime database, start the Uvicorn application factory:

```bash
export NETAUTO_DATABASE_URL='postgresql+psycopg://user:password@host/runtime_database'
uv run uvicorn netauto.entrypoints.http:create_app --factory
```

The kernel API is served below `/api/v1/core`.

## Verification

Cheap verification does not require a database:

```bash
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -q -m 'not postgresql'
uv run pytest -q tests/test_m1_traceability.py
```

The complete suite requires a dedicated, externally supplied real PostgreSQL test database:

```bash
export TEST_DATABASE_URL='postgresql+psycopg://user:password@host/test_database'
uv run pytest -q
```

Run PostgreSQL tests serially when only one test database is available. Do not add `-n`/xdist unless each worker has an externally managed isolated database target.

Focused verification is available through the registered markers:

```bash
uv run pytest -q -m 'postgresql and concurrency'
uv run pytest -q -m 'postgresql and api'
uv run pytest -q -m 'postgresql and migration'
uv run pytest -q -m property
```

The final M1 acceptance record documents the verified full-suite, PGTEST, API, migration, property, static-analysis and coverage results.

## Implementation state

M1-S00 through M1-S09 are complete and M1 is delivered. Future work must start from the frozen M1 contract/architecture and follow the repository milestone/reopening rules rather than changing M1 semantics implicitly.

## Historical implementation

Git history remains available for deliberate historical inspection, but previous code is not a compatibility target and must not be reconstructed merely because it existed before the M1 reset.
