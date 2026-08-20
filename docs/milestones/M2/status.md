# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S08 CANDIDATE READY FOR REVIEW

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S08 — CANDIDATE READY FOR REVIEW
current task    reviewer inspection of the published M2-S08 candidate
blockers        M2-S09 remains blocked on reviewer-owned M2-S08 completion
```

The M2 contract, architecture set and implementation decomposition are `FINAL / FROZEN`.

Implementation or review-fix work is authorized only for the exact slice marked `READY`, `IN PROGRESS` or `REVIEW CHANGES REQUIRED` here. `REVIEW CHANGES REQUIRED` authorizes only bounded corrective work for the recorded findings inside the same slice. No later slice may begin before its predecessor is reviewer-owned `COMPLETED`.

## Design and delivery gates

| Gate | State |
|---|---|
| Contract | FINAL / FROZEN |
| Architecture set | FINAL / FROZEN |
| Implementation steps | FINAL / FROZEN |
| Implementation | AUTHORIZED — `M2-S08` ONLY |
| Final acceptance | BLOCKED — requires `M2-S00 ... M2-S08` reviewer-owned `COMPLETED` |
| AS-IS consolidation | NOT STARTED |
| Delivery | NOT DELIVERED |

## Slice registry

| Slice | State | Dependency |
|---|---|---|
| `M2-S00` | COMPLETED | none |
| `M2-S01` | COMPLETED | `M2-S00 COMPLETED` |
| `M2-S02` | COMPLETED | `M2-S01 COMPLETED` |
| `M2-S03` | COMPLETED | `M2-S02 COMPLETED` |
| `M2-S04` | COMPLETED | `M2-S03 COMPLETED` |
| `M2-S05` | COMPLETED | `M2-S04 COMPLETED` |
| `M2-S06` | COMPLETED | `M2-S05 COMPLETED` |
| `M2-S07` | COMPLETED | `M2-S06 COMPLETED` |
| `M2-S08` | CANDIDATE READY FOR REVIEW | `M2-S07 COMPLETED` |
| `M2-S09` | BLOCKED | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00` through `M2-S07` are reviewer-owned `COMPLETED`. No later implementation slice is completed.

## Current blockers and findings

No contract, architecture, implementation-planning, technology, infrastructure or verification blocker is open in the M2-S08 candidate. Reviewer inspection is pending.

`M2-S08` is limited to integrated regression, complete machine-checkable traceability, the M2 delta allowlist and positive/negative surface closure. It must preserve the completed kernel, runtime, Health, CLI and installed-release capabilities. It must not begin `M2-S09` final acceptance before reviewer-owned completion of S08.

Any implementation finding that exposes an incomplete or contradictory frozen decision places the affected work in `STOP` and follows the explicit reopen/revalidate/propagate/re-freeze process.

## M2-S08 candidate record

Candidate state:

```text
M2-S08                         CANDIDATE READY FOR REVIEW
starting prompt ancestry       1f8e82de73d953830a6b31045ec96dfe19116dd9
starting synchronized HEAD     8ee9e540d24ecf07c8688350a03162a89d0991ce
implementation/tests commit    3d794d25317425254440f4e4b711ebfb63113edf
candidate evidence/status      recorded by the commit containing this status
M2-S09                         BLOCKED / not started
review decision                pending / reviewer-owned
```

### Closed S08 obligations

The singular registry in `tests/test_m2_traceability.py` now owns and machine-checks:

```text
M2 outcomes                    16 / 16
M2 acceptance criteria         32 / 32
M2 evidence bundles            32 / 32, all IMPLEMENTED and non-empty
canonical scenarios            83 / 83
safety predicates              21 / 21
business HTTP operations       63 / 63 CLI remote mappings
primary bundle owners          32 / 32 across M2-S01 ... M2-S08
preserved AS-IS guarantees     18 / 18 with concrete collected targets
contract/verification negatives 131 / 131 with concrete assertion ownership
contract quality gates         10 / 10 with concrete collected targets
```

The permanent graph includes exact architecture-owner and inverse maps, capability portfolio/trace, delivered-scenario retention, the seven authorized scenario deltas, high-level/public-wire/schema-runtime delta allowlists, WIP provenance, normative-placeholder policy and exact positive/negative API, CLI, schema, Alembic, runtime and trust surfaces.

S08 adds only test/evidence-format material. Production code, application behavior, public API/CLI registries, SQLAlchemy metadata, migration DDL, dependencies, `uv.lock` and the embedded runtime lock are unchanged.

### Evidence-record schema

`docs/milestones/M2/evidence/README.md` and `tests/support/m2_evidence.py` define and validate the future S09 record shape. Validation requires exact 32-bundle, 83-scenario and 21-predicate ledgers; candidate/artifact hashes; command and runtime censuses; schema/Alembic, operation and T9 facts; stable serialization; secret exclusion; and a null reviewer-owned decision.

No candidate-specific evidence record and no `acceptance.md` were created. S09 remains the owner of candidate-record population and final acceptance evidence.

### Pre-publication verification

Quality and collection:

```text
uv lock --check                PASS — 46 packages resolved
uv sync --locked               PASS — 44 packages checked
uv build                       PASS — sdist and wheel
Ruff format / lint             PASS — 235 files / no findings
Pyright strict                 PASS — 0 errors / 0 warnings
pytest collection              816 tests
```

Focused, traceability and exact inventories:

```text
focused S08 + M1/S00 trace     60 passed — 26.94 s
M2-VER-31 selected/unique/pass 31 / 31 / 39 parametrized — 22.35 s
M2-VER-32 selected/unique/pass 23 / 23 / 27 parametrized — 14.70 s
51 delivered scenarios         51 IDs / 91 unique targets / 95 passed — 59.89 s
all S05                        126 passed — 19.15 s
all S06                         72 passed — 4.83 s
all S07/T9                      18 passed — 40.86 s
schema/migration/runtime/Health 106 passed — 10.48 s
delivered regression           396 passed — 108.31 s
complete M2                    420 passed — 155.00 s
```

Integrated gates against the externally supplied real PostgreSQL target:

```text
PostgreSQL suite               254 passed / 562 deselected — 199.02 s
non-PostgreSQL suite           562 passed / 254 deselected — 79.79 s
complete repository            816 passed — 268.69 s final status-inclusive rerun
skip / xfail / rerun           0 / 0 / 0
warnings                       1 unchanged third-party Starlette deprecation
supported 40P01 / 40001        0 / 0
negative-control 40P01 / 40001 1 / 2, expected finite census
schema drift                   []
```

Candidate artifact and environment reused from the unchanged S07 release boundary:

```text
release                         0.2.0
wheel                           netauto-0.2.0-py3-none-any.whl
wheel size / members            165978 bytes / 77
wheel SHA-256                   38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60
runtime lock                    src/netauto/release/runtime.pylock.toml
runtime lock size               48238 bytes
runtime packages                29 total / 27 applicable on Linux CPython
runtime lock SHA-256            0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf
CPython / uv / Hatchling        3.14.7 / 0.12.3 / 1.32.0
PostgreSQL                      16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
Linux                           Ubuntu 24.04.4 LTS / kernel 6.8.0-134-generic
```

No PR, GitHub Actions workflow, tag, GitHub Release or artifact publication is part of this candidate. M2-S08 is not `COMPLETED`, M2-S09 has not started and no final milestone acceptance is claimed.

## M2-S07 final completion record

Reviewer result:

```text
M2-S07                         COMPLETED
original implementation prompt bf498153c458f585cd1a6914a9ac4aa904ebd34c
initial implementation         0934671324cca40e8e5e0608449c5a5b3524e662
initial evidence/status        dd58e8b342fae12639a731b86953a323e3da5b62
continuation implementation    a81dd3a4b85795d4f153580d2b9407bd482df363
first candidate evidence       c8402a222c537ab6d874b0d7bdb2b4ec6d23f7f8
superseded acceptance          a487e7c51c0b6ff0b15e1f3cfcb3702a9618f7ef
review reopen                  1558d5cd1a7125e5810d923274e5809852061214
review-fix prompt              9e4544e4919af233c8444999c9bbc908d8207440
review-fix implementation      e6de007f34d081c8a898c7a5453f54f0413b661e
corrected candidate evidence   f6ea47f73b2f7c4594cbd56f54f57a0823335bcd
review acceptance              recorded by the commit containing this status
closed findings                S07-RF-01 / S07-RF-02
M2-S08                         READY / not started
```

The earlier acceptance `a487e7c51c0b6ff0b15e1f3cfcb3702a9618f7ef` remains in immutable history for provenance. It was superseded by the reviewer-owned reopen and is replaced operationally by this final corrected acceptance. No history was rewritten, reverted or force-pushed.

### Closed finding `S07-RF-01`

The Linux operating guide now documents the exact installed Settings contract:

```text
NETAUTO_DATABASE_URL
    required; exact postgresql+psycopg SQLAlchemy URL

NETAUTO_LOG_LEVEL
    default INFO; CRITICAL | ERROR | WARNING | INFO | DEBUG

NETAUTO_POOL_SIZE
    default 10; integer >= 1

NETAUTO_MAX_OVERFLOW
    default 20; integer >= 0; -1 / unlimited forbidden

NETAUTO_POOL_TIMEOUT
    default 5.0 seconds; finite and > 0

NETAUTO_POOL_RECYCLE
    disabled when omitted; positive whole seconds when supplied

NETAUTO_POOL_PRE_PING
    default false; canonical true | false source values
```

The guide keeps application Settings separate from Uvicorn host, port and worker count; makes `NETAUTO_LOG_LEVEL=INFO` explicit in the canonical start procedure; and distinguishes bootstrap failure, schema-guard failure and post-start Health 503 behavior.

Installed-wheel evidence executes outside the checkout and proves:

```text
exact field inventory and aliases
exact installed defaults
guide-to-model correspondence
representative invalid boundary rejection
no network or PostgreSQL I/O during Settings validation
bounded safe diagnostics
no URL, password or sentinel leakage
no host / port / workers application Settings
```

### Closed finding `S07-RF-02`

The primary bundle registries now own the complete frozen evidence:

```text
M2-VER-24
    wheel/version and exact runtime lock
    outside-checkout wheel-only install
    installed CLI invocation
    installed unique Alembic graph
    explicit installed Alembic realization
    installed server lifecycle
    no implicit cross-action
    installed server import/composition independent from netauto.cli

M2-VER-29
    complete Linux guide
    installed Settings defaults and invalid-boundary evidence
    explicit migration
    start / Health / stop / restart
    orderly disposal
    protected secret and capacity guidance

M2-VER-30
    trusted-boundary documentation
    verified HTTPS and no insecure bypass
    no native credential/auth surface
    no OpenAPI security scheme or security requirement
    no header credential parameter
    no 401 / 403 public contract
    no login/logout/token/account/role route
    real lifecycle and transport-cut secret non-leakage
```

The permanent `S07_REVIEW_FIX_TARGETS` registry contains exactly `S07-RF-01` and `S07-RF-02`. Its dedicated traceability test verifies target existence and collection, obligation-specific cross-membership, preservation of S05 support, preservation of installed support for `M2-VER-22`, `23`, `25`, `26`, `27` and `28`, and continued S08 ownership of `M2-VER-31` and `M2-VER-32`.

## Accepted S07 capability

```text
release version                 0.2.0
canonical artifact              netauto-0.2.0-py3-none-any.whl
one version authority           installed distribution metadata
wheel content                   server + CLI + neutral DTOs + installed Alembic graph
embedded runtime lock           netauto/release/runtime.pylock.toml, PEP 751
runtime installation            exact lock sync, then wheel install --no-deps
installed isolation             outside checkout, no PYTHONPATH or editable install
installed Alembic               netauto:migrations, one base and one head
schema administration           explicit installed alembic upgrade head only
startup behavior                exact installed-head guard; no migrate/stamp/repair
Linux operating baseline        versioned layout, protected secret, foreground Uvicorn
process lifecycle               start / Health / orderly stop / fresh restart
runtime failure                 post-start real-PG transport cut -> bounded Health 503
installed CLI                   interactive PTY and non-interactive public HTTP
trust boundary                  trusted HTTP; external TLS; verified CLI HTTPS
security surface                no native auth, credential storage or insecure bypass
connection capacity             workers * (pool_size + max_overflow)
```

## Accepted verification

Quality and collection evidence produced by the corrected candidate:

```text
uv lock --check                  PASS — 46 packages resolved
uv sync --locked                 PASS — 44 packages checked
uv build                         PASS — sdist and wheel
Ruff format / lint               PASS — 230 files / no findings
Pyright strict                   PASS — 0 errors / 0 warnings
pytest collection                785 tests
```

Focused, bundle and installed/T9 evidence:

```text
focused review-fix union         8 passed
M2-VER-24 selected/unique/pass   18 / 18 / 18
M2-VER-29 selected/unique/pass   7 / 7 / 7
M2-VER-30 selected/unique/pass   15 / 15 / 38 parametrized
installed support selected/uniq  13 / 7; 7 passed
S07/T9 + M2 traceability         40 passed
M2 traceability                  22 passed
```

Regression and exact-remote final evidence:

```text
all S05 + all S06                198 passed
Settings/runtime/schema/Health   151 passed
PostgreSQL + concurrency         182 passed
non-PostgreSQL                   531 passed
complete repository              785 passed — 251.90 s post-push
skip / xfail / rerun             0 / 0 / 0
warnings                         1 unchanged third-party Starlette deprecation
supported 40P01 / 40001          0 / 0
negative-control 40P01 / 40001   1 / 2, expected
```

Candidate artifact and environment:

```text
wheel                            netauto-0.2.0-py3-none-any.whl
wheel size / members             165978 bytes / 77
wheel SHA-256                    38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60
runtime lock size                48238 bytes
runtime package census           29 total / 27 applicable on Linux CPython
runtime lock SHA-256             0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf
migration checksum               379165a1eda83c226a6c1e5dc4f493c7fa0d0c8dba39449a1d004751aaa39c57
CPython / uv / Hatchling         3.14.7 / 0.12.3 / 1.32.0
PostgreSQL                       16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
Linux                            Ubuntu 24.04.4 LTS / kernel 6.8.0-134-generic
```

Unchanged boundaries:

```text
authoritative tables             15
Alembic graph                    one base / one head (0001_m2_kernel)
migration DDL                    unchanged
compare_metadata                 []
third-party uv.lock records      unchanged
business HTTP operations         41 mutations + 22 reads = 63
operational HTTP operations      1 Health; total public HTTP = 64
CLI local / remote operations    8 / 63
registry examples                65
canonical scenarios/predicates   83 / 21
native auth / server TLS         absent
GitHub Actions / PR / tag        absent
published release/artifact       absent
```

Reviewer inspection verified the published commit chain, bounded delta, complete Settings documentation, installed Settings evidence, installed server/CLI independence, absence of native-security/401/403 surfaces, complete bundle membership and permanent traceability registration. The reviewer did not independently re-execute the 785-test suite; the accepted runtime results are the implementer's exact-remote evidence.

No blocking review finding remains open for `M2-S07`.

The concluded S07 review-fix execution aid is retired from the working tree:

```text
docs/milestones/M2/wip/M2-S07-review-fixes-codex-prompt.md
```

## Prior reviewer-owned completion ledger

Detailed implementation, finding and evidence records remain in their acceptance commits and repository history.

| Slice | Reviewer acceptance | Accepted full-suite census |
|---|---|---:|
| `M2-S07` | recorded by the commit containing this status | 785 |
| `M2-S06` | `b105e774765e7d8a2c68ab14501cfd6043eadf13` | 765 |
| `M2-S05` | `e1f11b8bf655079ed7c8aff99b56c2b2e4d17c03` | 691 |
| `M2-S04` | `bd342146679e405365ab93e4a60ca85b60834161` | 561 |
| `M2-S03` | `2b89f4ce79272554721ff694dd8ae8e32e7fab25` | 446 |
| `M2-S02` | `850abd97ece1aadeae65aa090d86c7ec4982751f` | 411 |
| `M2-S01` | `24e7b788b6b7f54d96614ef2c37bffbeb25ebd8b` | 349 |
| `M2-S00` | `d225faee6faf5fbebd36ce68db6c3b2c537323d0` | 314 |

## Immediate next action

Review the published candidate for:

```text
M2-S08 — Integrated regression, traceability and negative-surface closure
```

Do not start `M2-S09` before reviewer-owned completion of `M2-S08`.

## Current status vocabulary

```text
READY
    -> authorized to start after mandatory pre-flight

IN PROGRESS
    -> implementer work is active inside the exact slice scope

CANDIDATE READY FOR REVIEW
    -> implementation/evidence candidate published; reviewer decision pending

REVIEW CHANGES REQUIRED
    -> reviewer-owned result; bounded corrections remain in the same slice

COMPLETED
    -> reviewer-owned acceptance of the slice

BLOCKED
    -> dependency, infrastructure or authority condition prevents start/progress

FINAL / FROZEN
    -> normative authority; change requires formal reopening

NOT STARTED
    -> gate or activity has not begun

NOT AUTHORIZED
    -> activity must not begin

NOT DELIVERED
    -> final gate and closure have not completed
```

`M2-S09`, milestone delivery and merge remain reviewer/human-owned according to project governance.
