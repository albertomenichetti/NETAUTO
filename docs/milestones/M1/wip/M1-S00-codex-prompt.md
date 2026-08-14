# Codex implementation prompt — M1-S00

**Status:** NON-NORMATIVE IMPLEMENTATION PROMPT.

This file is an execution aid for Codex. It does not override `AGENTS.md`, the frozen M1 contract/architecture/steps, or the ratified technology baseline.

## Assignment

Implement exactly:

```text
M1-S00 — Clean-slate project bootstrap and quality/test runtime
```

from `docs/milestones/M1/steps.md`.

Do not implement M1-S01 or any domain capability.

## Mandatory pre-flight

Before changing files, read and obey:

```text
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md
docs/milestones/M1/contract.md
docs/milestones/M1/architecture/README.md
docs/milestones/M1/steps.md
docs/milestones/M1/status.md
```

Confirm from the repository itself that:

```text
M1 contract      = FINAL / FROZEN
M1 architecture  = globally FROZEN
M1 steps         = FINAL / FROZEN
current step     = M1-S00
STACK-01..09     = RATIFIED
```

If those authorities conflict with this prompt, the repository authorities win. If two normative authorities conflict with each other, stop the affected work and report the contradiction instead of choosing an interpretation.

Do not use removed historical code or Git history as an implementation template.

## Objective

Create a clean, reproducible Python project environment and the minimal composition/test scaffolding required for subsequent M1 implementation.

S00 is infrastructure/bootstrap only. It must leave the repository ready for S01 without implementing kernel domain behavior.

## Hard scope boundary

S00 MUST NOT implement any of the following:

```text
DataType / PrimitiveType semantics
ObjectTemplate semantics
Object semantics
ownership semantics
Relationship semantics
M1 PostgreSQL authority tables
M1 schema constraints/indexes
semantic Unit of Work operations
M1 API routes under /api/v1/core
JSON Schema compiler/projection
custom NETAUTO CLI
Typer
Docker/Testcontainers/embedded PostgreSQL provisioning
background jobs/queues
OpenTelemetry/Prometheus/structlog
Gunicorn
FastAPI CLI wrappers
```

Alembic scaffolding is in scope, but no M1 schema revision is created in S00.

## Required project/runtime baseline

### Python and packaging

Create project metadata with:

```text
implementation   CPython
supported minor  3.14.x only
requires-python  >=3.14,<3.15
project manager  uv
lockfile          uv.lock committed
build backend     Hatchling
layout            src/
```

Add `.python-version` for Python 3.14.

Use `pyproject.toml` as the primary configuration location.

Do not introduce Poetry, PDM, setuptools-specific project machinery, pre-commit as a correctness dependency, or a second lockfile.

### Runtime dependencies

Add only dependencies justified by STACK-01..09 and S00/S01 bootstrap needs:

```text
FastAPI
Uvicorn
Pydantic 2.x
pydantic-settings 2.x
SQLAlchemy 2.x
Psycopg 3
Alembic
```

Use Psycopg 3, not psycopg2/asyncpg. The canonical SQLAlchemy URL form for this project is:

```text
postgresql+psycopg://...
```

The initial M1 environment may use the Psycopg binary installation extra so the project has a reproducible developer/test installation without requiring a locally compiled adapter. Do not add the Psycopg pool package: SQLAlchemy owns the normal pool baseline.

HTTPX is a test dependency, not a runtime outbound-client dependency in M1-S00.

Do not add `jsonschema`, Typer, a DI container, structlog, OpenTelemetry, Prometheus, Testcontainers or alternative DB drivers.

### Development/test dependencies

Add the ratified quality/testing toolset required to make S00 immediately enforceable:

```text
pytest
pytest-asyncio
pytest-xdist
pytest-timeout
Hypothesis
coverage.py
HTTPX
Ruff
Pyright
```

The project must expose the canonical tools through `uv run ...`.

## Static quality configuration

### Ruff

Use Ruff for formatter, linting and import ordering.

Set the Python target to 3.14.

Keep the rule set curated rather than enabling `ALL`. At minimum include the ratified families:

```text
E
F
I
UP
B
RUF
ASYNC
```

Prefer Ruff formatter defaults unless a current frozen project document explicitly requires a different style value. Do not resurrect style settings solely because they existed before the clean-slate reset.

### Pyright

Configure Pyright in `pyproject.toml`:

```text
pythonVersion     3.14
typeCheckingMode  strict
include           src, tests
```

Do not substitute mypy or basedpyright. Do not globally relax strict mode to work around one local typing issue.

## Pytest/test baseline

Configure pytest in `pyproject.toml`.

Use `pytest-asyncio` as the canonical async test plugin with asyncio-only semantics and auto mode. Default async test loop scope should remain function-scoped unless a concrete fixture requires otherwise.

Register the project marker vocabulary needed by STACK-07, including at least:

```text
postgresql
concurrency
api
migration
property
stress
slow
```

Enable strict marker handling.

Configure coverage with branch measurement. Do not invent a percentage threshold in S00.

## Process settings

Implement a minimal process-settings boundary using `pydantic-settings`.

Requirements:

```text
prefix            NETAUTO_
construction      explicit at bootstrap/composition
lifetime          immutable after construction
failure           fail fast on invalid/missing required process configuration
import behavior   no Settings() singleton at module import
```

For S00, keep settings minimal. The only required runtime DB setting should be the externally supplied database URL:

```text
NETAUTO_DATABASE_URL
```

Do not provide a localhost/default database URL.

A small log-level setting with a safe default such as `INFO` is acceptable because S00 actually configures logging.

Do not implement dotenv auto-discovery, layered dev/staging/prod profiles, secret-manager integrations, runtime reload, nested settings hierarchies, or speculative settings.

## Test database boundary

Test database configuration is deliberately separate from runtime process settings.

The test environment/operator supplies:

```text
TEST_DATABASE_URL
```

Requirements:

- no fallback to `NETAUTO_DATABASE_URL`;
- no fallback to localhost;
- no SQLite fallback;
- no automatic DB provisioning;
- no Docker;
- no Testcontainers;
- reject a non-PostgreSQL/non-Psycopg test target clearly;
- PostgreSQL-marked tests obtain the URL through one explicit test-support boundary/fixture rather than ad-hoc `os.environ` reads throughout the suite.

Create a minimal PostgreSQL availability smoke test that does not create schema or data beyond what is required for a harmless connectivity check. It may use Psycopg directly because this is a test-environment availability check, not kernel persistence implementation.

Behavior must be explicit:

```text
uv run pytest -m "not postgresql"
    -> runs without PostgreSQL

uv run pytest -m postgresql
    -> if TEST_DATABASE_URL is absent, fail clearly and intentionally
    -> if TEST_DATABASE_URL is supplied, connect to that real PostgreSQL target
       and run the availability smoke test
```

Do not silently skip a deliberately selected PostgreSQL suite because the URL is missing.

## Minimal package/composition structure

Create only the package structure needed now. Preserve clear boundaries without manufacturing empty framework abstractions.

A reasonable minimal shape is conceptually:

```text
src/netauto/
    __init__.py
    settings.py
    logging.py
    entrypoints/
        __init__.py
        http.py
    persistence/
        __init__.py
        metadata.py
```

Equivalent naming is acceptable if it is simpler and keeps the same boundaries.

Do not create repository interfaces, domain base classes, service registries, generic command buses, containers or placeholder aggregate models.

### SQLAlchemy metadata seam

S00 may define one empty authoritative SQLAlchemy `MetaData` object as the seam that Alembic and S01 will share.

Do not define any M1 table in S00.

## FastAPI/Uvicorn composition

Provide an explicit no-argument FastAPI application factory suitable for direct Uvicorn factory loading, for example conceptually:

```text
netauto.entrypoints.http:create_app
```

The canonical server style must work as:

```text
uv run uvicorn netauto.entrypoints.http:create_app --factory
```

The factory must perform explicit composition rather than relying on an import-time `app = build_everything()` singleton.

Use an explicit FastAPI lifespan seam for process startup/shutdown concerns. In S00 it should remain minimal: logging/lifecycle setup only. Do not create a DB engine or run Alembic migrations from lifespan; engine/pool composition belongs to S01.

Do not add public M1 domain routes merely to test the app. In particular, do not invent `/api/v1/core` placeholder endpoints.

## Logging

Use Python stdlib `logging` only.

Configure logging centrally from composition/bootstrap. Modules may obtain hierarchical loggers but must not install independent handlers/configuration.

Human-readable logging is sufficient. No JSON logging contract, tracing abstraction or metrics framework.

Do not duplicate Uvicorn access logging.

Request-id middleware is optional in S00 and should be omitted unless a concrete S00 HTTP/logging test actually needs it; do not add it just because it is permitted by STACK-06.

## Alembic scaffold

Create the minimum Alembic project scaffold required for S01.

Requirements:

- use the same SQLAlchemy metadata seam that S01 will populate;
- obtain the migration database URL from explicit NETAUTO process configuration rather than hardcoding a local URL;
- do not create M1 tables or a fake initial schema revision in S00;
- do not run migrations during FastAPI import, `create_app()`, or lifespan;
- migration execution remains an explicit admin/deployment command.

## Repository hygiene

Update `.gitignore` for the new environment as needed, including generated/local artifacts such as:

```text
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
.hypothesis/
.coverage
htmlcov/
.env
```

Never commit environment secrets or `TEST_DATABASE_URL`/`NETAUTO_DATABASE_URL` values.

Do not create a GitHub Actions workflow in S00: CI provider/workflow layout is not part of the frozen S00 deliverables.

Do not edit frozen M1 semantic architecture to match implementation details.

Do not mark M1-S00 `COMPLETED`; completion is a review decision after the delta and verification evidence are inspected.

## Required S00 tests

Implement focused tests proving at least:

1. Settings are not instantiated as an import-time global side effect.
2. Explicit settings construction/injection can be used in tests.
3. Required runtime DB configuration has no localhost/default fallback.
4. Runtime DB configuration and `TEST_DATABASE_URL` are independent.
5. PostgreSQL test support refuses a missing explicitly required test URL clearly.
6. PostgreSQL test support refuses a non-PostgreSQL/non-Psycopg target.
7. Application factory can be constructed with valid injected/composed settings without connecting to PostgreSQL in S00.
8. FastAPI composition does not execute Alembic migrations.
9. Importing the package does not perform DB/network I/O.
10. The PostgreSQL-marked availability smoke test uses only `TEST_DATABASE_URL` when selected.

Keep these tests small; S00 is not a place to test future domain behavior.

## Required verification commands

Run and report the exact result of at least:

```text
uv lock
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -m "not postgresql"
```

Also prove the required failure behavior with `TEST_DATABASE_URL` absent when the PostgreSQL suite is explicitly selected.

If a real externally supplied `TEST_DATABASE_URL` is available in the Codex environment, also run:

```text
uv run pytest -m postgresql
```

If it is not available, do not fabricate one, do not start PostgreSQL, and do not claim the real-DB smoke test passed. Report it explicitly as not executed because external test infrastructure was unavailable; the missing-URL failure-path verification must still be performed.

## Completion report

At the end, provide:

- concise list of files created/changed;
- dependency/runtime choices actually materialized;
- commands executed and pass/fail results;
- explicit statement whether a real `TEST_DATABASE_URL` was available;
- any local suppression/config exception added for Ruff/Pyright and why;
- any authority/documentation contradiction encountered;
- confirmation that no S01/domain/schema capability was implemented;
- confirmation that `status.md` was not marked completed by the implementation itself.

If any mandatory non-PostgreSQL quality gate fails, fix it within S00 scope before presenting the work for review.
