# M2 — Independent Current Architecture Consistency Closure Report

**Status:** CANDIDATE READY FOR REVIEW

This report is gate evidence. It does not own product semantics and does not
replace the current architecture under `docs/architecture/`.

## Audit identity and boundary

```text
starting reviewer-rejection HEAD   5dc216f50b8fc4616c112e61ada8cfede28fc729
rejected closure candidate         3e8f575ac66ed46be7d8c014ee82d4e71905e937
AUDITED_ASIS_SHA                   4115ec0c001dc00bb6f6014aebaa6eff7d61297e
publication/evidence boundary      this report/status publication commit
branch                             M2
AS-IS consolidation                COMPLETED
consistency closure                CANDIDATE READY FOR REVIEW
M2                                 NOT DELIVERED
merge                              NOT EXECUTED
```

The current-owner hashes were reverified against the exact
`AUDITED_ASIS_SHA`. The complete review-fix gate was executed from branch `M2`
at the reviewer review-fix base with only the two authorized evidence files
modified. No owner or permanent-test correction was required.

## Exact current-owner inventory and hashes

| Current file | SHA-256 |
|---|---|
| `docs/architecture/README.md` | `7dd998d53e388e9fe0be2c5dd71fc4b20a88cb6de8e9ee6b9af73376ccd1a7c4` |
| `docs/architecture/datatype.md` | `4aac554d92ef8ec0cbbd78db851f192a8b508f3d4f691ed5ee0b316250ec0dc7` |
| `docs/architecture/objecttemplate.md` | `9f5c1b7d62ae8088369313afbcec9013d7c081dedfce5ff33f6248a066fc6e53` |
| `docs/architecture/object.md` | `fe46bd7dd23df55ced205fc604cea0682da512bc82227216c9dd211e3d0fc3b4` |
| `docs/architecture/relationship.md` | `ecc18f34c2b4469c9061de72e20ed04e5d502745644b70e0a0416a4ecf4462d1` |
| `docs/architecture/persistence.md` | `8040ae143c4116928c516c7c52d71aea937b501b63b90181737ed7b93754eef3` |
| `docs/architecture/concurrency-matrix.md` | `ca82af4a11254fedcb6476832b1cfa4d0ea012e3f28cd5ce14e978d7b90ec70c` |
| `docs/architecture/concurrency.md` | `177d931699ae58e6b3a7b9bd2b68782e66ada6d68900dfa7de351181b32eb25a` |
| `docs/architecture/api.md` | `007201f578f088c329c8e704895fb6bd819e73102970af3ed78180bb50f6758d` |
| `docs/architecture/health.md` | `a9a708f271934c71b29bed7c59db9f91b4c267ad1588c056e22f430a08534a5a` |
| `docs/architecture/cli.md` | `132fcdefc577053b7b5064ed8fb683e19091545ed0cb5b0011d43c8132c9c8bf` |
| `docs/architecture/runtime-deployment.md` | `c36b6928739e34854bc7f72f7a20b56cc8c64fb80e4d81b608522f7241edbc8d` |
| `docs/architecture/linux-operating-baseline.md` | `119c4171005408cbd3cad7c169360e478a368daca18930dea4af8ee3d5a43756` |
| `docs/architecture/verification.md` | `2df18553b2be40080c6543d8ba057f15e1e6fcafc9f4c1b76b8356a7cd7d897a` |
| `docs/architecture/verification-concurrency-registry.md` | `dcdaf535477112bc921cd9c2727f87b58e02aa6d2ea72cef6c34a317d2a581aa` |

The inventory contains exactly 15 files.

## Consistency matrix

| Key | Result | Verified boundary |
|---|---|---|
| `CC-01` | PASS | Exact corpus, owner map, owner/projection roles, dependency direction and WIP isolation. |
| `CC-02` | PASS | Stable and exact identity, lifecycle, revision freshness, default selection, admission, historical pins and deletion semantics. |
| `CC-03` | PASS | Nine primitive types, lexical/canonical/persistence separation, declaration-owned cardinality and one primitive codec. |
| `CC-04` | PASS | ObjectTemplate inheritance, declarations, effective schema, revision/publication, migration defaults and blockers. |
| `CC-05` | PASS | Object factual state, schema migration, ownership graph, events, reads and corruption boundary. |
| `CC-06` | PASS | RelationshipDefinition/RDV, Resolution membership, factual Relationships, closure, events, conflicts and blockers. |
| `CC-07` | PASS | Fifteen tables, 29 indexes, constraints/codecs, one Alembic revision, transaction boundary and exact metadata equality. |
| `CC-08` | PASS | 41 mutations, 15 family blocks, 861 cells, 21 predicates, 83 scenarios, 11 recipes, three gates and complete lock plans. |
| `CC-09` | PASS | 63 business routes, 41 mutations, 22 reads, one Health route, 23 errors, DTOs, pagination and public failure safety. |
| `CC-10` | PASS | Exact startup revision guard, no startup migration, shared runtime engine/pool and bounded `SELECT 1` Health semantics. |
| `CC-11` | PASS | 63 remote operations, eight local commands, HTTP-only client, selectors, session, rendering, PTY and trust behavior. |
| `CC-12` | PASS | Seven Settings fields, 77-member wheel, 29-package runtime lock, installed migrations, trust boundary and Linux projection. |
| `CC-13` | PASS | Exact T0–T10 layers, finite registries, real-PostgreSQL/T9/T10 requirements and release-gate censuses. |
| `CC-14` | PASS | Exact negative-surface registry and absence of excluded product/deployment capabilities. |
| `CC-15` | PASS | Links, owner references, placeholders, temporal wording, milestone leakage, finite inventories and historical isolation. |

```text
CC-01 ... CC-15  PASS
open findings    0
```

## Finding registry

### `M2-CC-F01`

```text
matrix key       CC-15
classification   current-document projection defect
evidence         duplicated ambiguous historical self-reference
resolution       exact consolidation acceptance SHA recorded by reviewer transition
changed file     docs/milestones/M2/status.md
closed by        5dc216f50b8fc4616c112e61ada8cfede28fc729
status           CLOSED
```

### `M2-CC-F02`

```text
matrix key       CC-15
classification   gate-evidence completeness defect
evidence         aggregate labels without executable pytest argv
resolution       exact executable command ledger plus complete rerun
changed file     docs/milestones/M2/consistency-closure-report.md
status           CLOSED
```

```text
finding count    2
open findings    0
```

No current-owner incompleteness, implementation defect, architecture
contradiction or in-scope new opportunity was found.

## Owner and dependency audit

- `docs/architecture/README.md` links every one of the fourteen current owner or
  projection documents exactly once in the owner map.
- Each shared claim resolves to one primary owner; dependent documents project
  that claim without creating a competing owner or semantic dependency cycle.
- `runtime-deployment.md` owns runtime and deployment semantics;
  `linux-operating-baseline.md` is its executable operator projection.
- Domain owners, persistence, concurrency matrix/mechanism, public API, Health,
  CLI, runtime/deployment and verification documents agree on their shared
  identities, lifecycles, exact pins, failure boundaries and finite registries.
- No current owner depends normatively on `docs/milestones/M2/wip/`.

## Implementation, schema and public-registry cross-check

```text
PrimitiveType catalog                         9
business HTTP operations                    63
business mutations / reads               41 / 22
Health operations                            1
total public HTTP operations                64
public error codes                          23
CLI remote / local                       63 / 8
tables / explicit indexes                15 / 29
migration files                              1
base / head / current             0001_m2_kernel
down_revision                              None
compare_metadata                              []
Settings fields                               7
mutation / family / cell census       41 / 15 / 861
scenario / predicate / recipe census  83 / 21 / 11
advisory gates / row families              3 / 5
maximum semantic UoW attempts                  4
negative surfaces                           131
verification layers                      T0–T10
```

Metadata, migration, production registries, generated OpenAPI and CLI registry
were used only as cross-check evidence. They did not replace the current owners.

## Documentation hygiene and historical isolation

```text
current files / local links / unresolved links   15 / 35 / 0
owner-map targets / competing owners              14 / 0
temporal or delta wording findings                     0
milestone, slice, candidate or SHA leakage             0
TODO / TBD / FIXME / unresolved open point             0
WIP authority references                               0
contradictory header/body findings                      0
finite inventories with different values                0
```

Semantic uses of words such as “before”, “after” and “candidate” were classified
as domain or concurrency language, not change-log wording. The concise M1/M2
provenance remains confined to the dedicated section of
`docs/architecture/README.md`.

## Verification environment

```text
OS                    Linux 6.8.0-134-generic x86_64
Python                3.14.7
uv                    0.12.3
pytest                8.4.2
Ruff                  0.16.3
Pyright               1.1.411
PostgreSQL            16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
database identity     netautotest
bounded SELECT 1      PASS
database provisioning external to the NETAUTO test process
```

The probe used the environment-provided `TEST_DATABASE_URL` with the exact
`postgresql+psycopg` driver. No URL, userinfo or credential is recorded here.
No PostgreSQL provisioning, Docker, Testcontainers, SQLite or fallback was used.

## Exact executable command ledger and pre-publication results

Every command in this ledger was printed before execution and then run with the
same argv. Commands are relative to the repository root. No command or output
contains `TEST_DATABASE_URL`, userinfo or credentials.

### Static document, owner-hash and evidence audit

```bash
uv run python - <<'PY'
import hashlib
import re
from pathlib import Path
from urllib.parse import unquote

root = Path(".")
architecture = root / "docs/architecture"
report_path = root / "docs/milestones/M2/consistency-closure-report.md"
status_path = root / "docs/milestones/M2/status.md"
expected_files = {
    "README.md": "7dd998d53e388e9fe0be2c5dd71fc4b20a88cb6de8e9ee6b9af73376ccd1a7c4",
    "api.md": "007201f578f088c329c8e704895fb6bd819e73102970af3ed78180bb50f6758d",
    "cli.md": "132fcdefc577053b7b5064ed8fb683e19091545ed0cb5b0011d43c8132c9c8bf",
    "concurrency-matrix.md": "ca82af4a11254fedcb6476832b1cfa4d0ea012e3f28cd5ce14e978d7b90ec70c",
    "concurrency.md": "177d931699ae58e6b3a7b9bd2b68782e66ada6d68900dfa7de351181b32eb25a",
    "datatype.md": "4aac554d92ef8ec0cbbd78db851f192a8b508f3d4f691ed5ee0b316250ec0dc7",
    "health.md": "a9a708f271934c71b29bed7c59db9f91b4c267ad1588c056e22f430a08534a5a",
    "linux-operating-baseline.md": "119c4171005408cbd3cad7c169360e478a368daca18930dea4af8ee3d5a43756",
    "object.md": "fe46bd7dd23df55ced205fc604cea0682da512bc82227216c9dd211e3d0fc3b4",
    "objecttemplate.md": "9f5c1b7d62ae8088369313afbcec9013d7c081dedfce5ff33f6248a066fc6e53",
    "persistence.md": "8040ae143c4116928c516c7c52d71aea937b501b63b90181737ed7b93754eef3",
    "relationship.md": "ecc18f34c2b4469c9061de72e20ed04e5d502745644b70e0a0416a4ecf4462d1",
    "runtime-deployment.md": "c36b6928739e34854bc7f72f7a20b56cc8c64fb80e4d81b608522f7241edbc8d",
    "verification-concurrency-registry.md": "dcdaf535477112bc921cd9c2727f87b58e02aa6d2ea72cef6c34a317d2a581aa",
    "verification.md": "2df18553b2be40080c6543d8ba057f15e1e6fcafc9f4c1b76b8356a7cd7d897a",
}
files = {path.name: path for path in architecture.glob("*.md")}
assert set(files) == set(expected_files)
for name, expected_hash in expected_files.items():
    assert hashlib.sha256(files[name].read_bytes()).hexdigest() == expected_hash

readme = files["README.md"].read_text()
owner_map = readme.split("## Owner map\n", 1)[1].split("\n## ", 1)[0]
owner_targets = re.findall(r"\]\(([^)#]+\.md)\)", owner_map)
assert len(owner_targets) == 14
assert set(owner_targets) == set(expected_files) - {"README.md"}

links = []
unresolved = []
for source in files.values():
    body = source.read_text()
    for target in re.findall(r"(?<!!)\[[^]]+\]\(([^)]+)\)", body):
        raw = target.split()[0].strip("<>")
        if raw.startswith(("http://", "https://", "mailto:")):
            continue
        links.append((source, raw))
        relative, _, fragment = raw.partition("#")
        destination = source.parent / (unquote(relative) if relative else source.name)
        if not destination.exists():
            unresolved.append((source, raw, "file"))
            continue
        if fragment:
            anchors = {
                re.sub(r"[^a-z0-9 _-]", "", heading.lower())
                .strip()
                .replace(" ", "-")
                for heading in re.findall(
                    r"^#{1,6}\s+(.+?)\s*#*$", destination.read_text(), re.MULTILINE
                )
            }
            if unquote(fragment).lower() not in anchors:
                unresolved.append((source, raw, "anchor"))
assert len(links) == 35
assert unresolved == []

temporal = re.compile(
    r"\b(previously|newly|changed from|preserved from|before M2|after M2|"
    r"during M2|M2 delta|to be implemented)\b",
    re.IGNORECASE,
)
historical = re.compile(
    r"\b(?:M2-S\d+|M2-CC-F\d+|M2-(?:OUT|AC|VER)-\d+|[0-9a-f]{40})\b"
)
placeholder = re.compile(
    r"\b(?:TODO|TBD|FIXME|OPEN QUESTION|PARTIALLY REOPENED)\b",
    re.IGNORECASE,
)
for name, source in files.items():
    body = source.read_text()
    assert temporal.search(body) is None
    assert placeholder.search(body) is None
    assert "docs/milestones/M2/wip/" not in body
    if name != "README.md":
        assert historical.search(body) is None

report = report_path.read_text()
status = status_path.read_text()
assert set(re.findall(r"^\| `(CC-\d{2})` \| PASS \|", report, re.MULTILINE)) == {
    f"CC-{number:02d}" for number in range(1, 16)
}
for finding in ("M2-CC-F01", "M2-CC-F02"):
    section = report.split(f"### `{finding}`\n", 1)[1].split("\n### ", 1)[0]
    assert re.search(r"^status\s+CLOSED$", section, re.MULTILINE)
assert "finding count    2" in report
assert "open findings    0" in report
assert "consolidation acceptance commit    4fd0f38fc804a494d1d0ce0fd251c49119b14127" in status
assert "consistency closure — CANDIDATE READY FOR REVIEW" in status
assert "M2                          NOT DELIVERED" in status
assert "merge                       NOT EXECUTED" in status
print("files=15 owner_targets=14 links=35 unresolved=0")
print("owner_hashes=15 temporal=0 leakage=0 placeholders=0 wip=0")
print("CC=15_PASS findings=2_CLOSED open_findings=0 lifecycle=PASS")
PY
```

Result: exit status `0`; `15` exact owner hashes, `35` links with `0`
unresolved, `CC-01...CC-15 PASS`, `2` findings `CLOSED`, `0` open findings.

### PostgreSQL identity and bounded probe

```bash
timeout 15s uv run python - <<'PY'
import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

raw = os.environ.get("TEST_DATABASE_URL")
if raw is None:
    raise SystemExit("TEST_DATABASE_URL absent")
url = make_url(raw)
if url.drivername != "postgresql+psycopg":
    raise SystemExit(f"unexpected driver: {url.drivername}")
engine = create_engine(url, connect_args={"connect_timeout": 5})
try:
    with engine.connect() as connection:
        version = connection.execute(text("select version()" )).scalar_one()
        database = connection.execute(text("select current_database()" )).scalar_one()
        probe = connection.execute(text("select 1" )).scalar_one()
finally:
    engine.dispose()
print("PostgreSQL=" + version.split(",")[0])
print("database=" + database)
print("SELECT 1=" + str(probe))
PY
```

Result: exit status `0`; PostgreSQL 16.15, database `netautotest`, `SELECT 1=1`.

### Locked environment, build and quality

```bash
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

Results, in command order: all exit status `0`; lock resolved 46 packages;
locked sync checked 44 packages; wheel and sdist built; Ruff format checked 246
files; Ruff lint passed; Pyright reported `0 errors, 0 warnings`; pytest
collected `896` tests in 2.17s with the one reviewed Starlette warning.

### Current architecture, negative surfaces and traceability

```bash
uv run pytest -q \
  tests/test_m2_s08_regression.py \
  tests/test_m2_s08_negative_surface.py \
  tests/test_m1_traceability.py \
  tests/test_m2_s00_traceability.py \
  tests/test_m2_traceability.py \
  tests/test_m2_s09_acceptance.py
```

Result: exit status `0`; `117 passed in 37.32s`.

### Schema, metadata, migration and startup revision guard

```bash
uv run pytest -q \
  tests/test_migrations.py \
  tests/test_schema_metadata.py \
  tests/test_persistence_constraints.py \
  tests/test_m2_s07_alembic.py \
  tests/test_runtime_schema_guard.py \
  tests/test_m2_s04_installed.py \
  tests/test_m2_s04_scope.py
```

Result: exit status `0`; `33 passed in 18.85s`; `compare_metadata == []`.

### API, DTO, error, OpenAPI and CLI

```bash
uv run pytest -q \
  tests/test_datatype_api.py \
  tests/test_health_api.py \
  tests/test_object_api.py \
  tests/test_objecttemplate_api.py \
  tests/test_relationship_api.py \
  tests/test_relationshipdefinition_api.py \
  tests/test_object_scope.py \
  tests/test_relationshipdefinition_scope.py \
  tests/test_s08_delete_diagnostics.py \
  tests/test_s08_persistence_error_mapping.py \
  tests/test_m2_s05_http_client.py \
  tests/test_m2_s05_installed.py \
  tests/test_m2_s05_model.py \
  tests/test_m2_s05_parser.py \
  tests/test_m2_s05_process.py \
  tests/test_m2_s05_registry.py \
  tests/test_m2_s05_residual_review_fixes.py \
  tests/test_m2_s05_review_fixes.py \
  tests/test_m2_s05_tls.py \
  tests/test_m2_s06_connection.py \
  tests/test_m2_s06_process.py \
  tests/test_m2_s06_rendering.py \
  tests/test_m2_s06_review_fixes.py \
  tests/test_m2_s06_state.py \
  tests/test_m2_s07_trust.py
```

Result: exit status `0`; `277 passed, 1 warning in 68.95s`.

### Health, runtime and schema guard

```bash
uv run pytest -q \
  tests/test_bootstrap_diagnostics.py \
  tests/test_health.py \
  tests/test_health_api.py \
  tests/test_health_postgresql.py \
  tests/test_health_probe.py \
  tests/test_http_composition.py \
  tests/test_runtime_engine.py \
  tests/test_runtime_schema_guard.py \
  tests/test_settings.py \
  tests/test_m2_s04_installed.py \
  tests/test_m2_s04_scope.py
```

Result: exit status `0`; `121 passed, 1 warning in 15.23s`.

### Installed-wheel and Linux T9

```bash
uv run pytest -q \
  tests/test_m2_s07_alembic.py \
  tests/test_m2_s07_distribution.py \
  tests/test_m2_s07_linux.py \
  tests/test_m2_s07_trust.py
```

Result: exit status `0`; `18 passed in 41.32s`.

### PostgreSQL and concurrency

```bash
uv run pytest -q -m 'postgresql or concurrency'
```

The selection uses the repository-registered `postgresql` and `concurrency`
markers and the environment-provided PostgreSQL target. Result: exit status
`0`; `254 passed, 642 deselected, 1 warning in 188.98s`.

### Non-PostgreSQL partition

```bash
uv run pytest -q -m 'not postgresql and not concurrency'
```

Result: exit status `0`; `642 passed, 254 deselected, 1 warning in 88.23s`.

### Full repository

```bash
uv run pytest -q
```

Result: exit status `0`; `896 passed, 1 warning in 272.99s`.

### Artifact identity

```bash
uv run python - <<'PY'
import hashlib
import tomllib
import zipfile
from pathlib import Path

wheel = Path("dist/netauto-0.2.0-py3-none-any.whl")
lock = Path("src/netauto/release/runtime.pylock.toml")
with zipfile.ZipFile(wheel) as archive:
    members = len(archive.namelist())
values = (
    wheel.stat().st_size,
    members,
    hashlib.sha256(wheel.read_bytes()).hexdigest(),
    lock.stat().st_size,
    len(tomllib.loads(lock.read_text())["packages"]),
    hashlib.sha256(lock.read_bytes()).hexdigest(),
)
expected = (
    165978,
    77,
    "38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60",
    48238,
    29,
    "0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf",
)
assert values == expected
print("wheel=165978 bytes/77 members/" + values[2])
print("runtime_lock=48238 bytes/29 packages/" + values[5])
PY
```

Result: exit status `0`; wheel and runtime-lock identity match the expected
size, member/package census and SHA-256. Generated wheel and sdist files were
removed after verification.

The repository-wide final census was:

```text
skip / xfail / rerun                   0 / 0 / 0
supported-path 40P01                             0
unexpected 40001                                 0
negative-control SQLSTATE          40P01 x1 / 40001 x2
compare_metadata                                  []
warnings                                           1
new unexplained warnings                           0
```

The sole warning is the already reviewed Starlette/FastAPI `TestClient`
deprecation.

## Artifact identity

```text
wheel              netauto-0.2.0-py3-none-any.whl
wheel size         165978 byte
wheel members      77
wheel SHA-256      38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60
runtime lock size  48238 byte
runtime packages   29
lock SHA-256       0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf
```

## Changed-file and reviewer boundary

The publication changes only:

```text
docs/milestones/M2/consistency-closure-report.md
docs/milestones/M2/status.md
```

Production, API/CLI/Health implementation, schema, migration, dependencies,
locks, release artifacts, frozen M2 authorities and the fifteen current owners
are unchanged. No PR, GitHub Action, tag, Release, artifact publication or
merge is part of this candidate.

This is implementer evidence for reviewer inspection. It does not assign
reviewer acceptance, mark consistency closure `COMPLETED`, deliver M2 or execute
the merge.
