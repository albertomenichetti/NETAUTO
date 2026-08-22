# M2 — Independent Current Architecture Consistency Closure Report

**Status:** CANDIDATE READY FOR REVIEW

This report is gate evidence. It does not own product semantics and does not
replace the current architecture under `docs/architecture/`.

## Audit identity and boundary

```text
starting reviewer-acceptance HEAD  4115ec0c001dc00bb6f6014aebaa6eff7d61297e
AUDITED_ASIS_SHA                   4115ec0c001dc00bb6f6014aebaa6eff7d61297e
publication/evidence HEAD          this publication commit
branch                             M2
AS-IS consolidation                COMPLETED
consistency closure                CANDIDATE READY FOR REVIEW
M2                                 NOT DELIVERED
merge                              NOT EXECUTED
```

The complete gate was executed from a clean detached worktree at the exact
`AUDITED_ASIS_SHA`. No owner or permanent-test correction was required between
the starting boundary and the audited tree.

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

No `M2-CC-Fnn` finding was opened. The exact finding registry is empty and the
open finding count is zero. No current-document projection defect,
current-owner incompleteness, implementation defect, architecture contradiction
or in-scope new opportunity was found.

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

## Commands and exact pre-publication results

All commands below ran in the clean detached worktree at
`4115ec0c001dc00bb6f6014aebaa6eff7d61297e`.

```text
bounded static owner/link/hygiene audits           PASS
bounded PostgreSQL version/database/SELECT 1       PASS
uv lock --check                                    PASS
uv sync --locked                                   PASS
uv build                                           PASS
uv run ruff format --check .                       PASS (245 files)
uv run ruff check .                                PASS
uv run pyright                                     PASS (0 errors, 0 warnings)
uv run pytest --collect-only -q                    PASS (896 collected; 7.86s)

tests/test_m2_s08_regression.py                      4 passed; 4.57s
tests/test_m2_s08_negative_surface.py               41 passed; 4.45s
M1/M2 traceability + S09 lifecycle/evidence         72 passed; 33.52s
schema / metadata / migration / startup revision    33 passed; 19.54s
API / DTO / error / CLI                            277 passed; 68.71s
Health / runtime / schema guard                    121 passed; 15.90s
installed-wheel / Linux T9                          18 passed; 43.49s
PostgreSQL / concurrency                           254 passed; 198.23s
non-PostgreSQL                                     642 passed; 89.31s
full repository                                    896 passed; 281.25s
```

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
