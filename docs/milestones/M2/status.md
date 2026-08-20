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
current task    reviewer inspection of the package-closure corrected S08 candidate
blockers        M2-S09 remains blocked pending reviewer-owned S08 completion
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

No contract, architecture, implementation-planning, technology or infrastructure blocker is open. The bounded package-parent initializer defect in `S08-VRF-05` is corrected in the candidate below; `S08-VRF-06` and `S08-VRF-07` remain closed. Reviewer inspection of S08 is pending and M2-S09 remains dependency-blocked.

`TEST_DATABASE_URL` is externally supplied when it is explicitly provided by the environment and NETAUTO test code does not provision, invent or silently substitute it. A loopback or local hostname is not itself a blocker. The implementer must verify that the configured URL uses the supported PostgreSQL/Psycopg form, reaches real PostgreSQL, and identifies the dedicated test target required by the existing test-support safety checks.

`M2-S08` remains limited to integrated regression, complete machine-checkable traceability, the M2 delta allowlist and positive/negative surface closure. It must preserve the completed kernel, runtime, Health, CLI and installed-release capabilities. It must not begin `M2-S09` final acceptance before reviewer-owned completion of S08.

Any implementation finding that exposes an incomplete or contradictory frozen decision places the affected work in `STOP` and follows the explicit reopen/revalidate/propagate/re-freeze process.

## M2-S08 candidate record

Candidate state:

```text
M2-S08                         CANDIDATE READY FOR REVIEW
starting prompt ancestry       1f8e82de73d953830a6b31045ec96dfe19116dd9
starting synchronized HEAD     8ee9e540d24ecf07c8688350a03162a89d0991ce
implementation/tests commit    3d794d25317425254440f4e4b711ebfb63113edf
first candidate evidence       b8c78c712d61514998281ea170e7606e1eb99781
post-push corrective commit    9027b02b7f2b949cd7674adfa7c3fe3758eacda3
corrective handoff              02a3a98ce5fc14419bcc795a8520ad1659140805
verification review-fix        42843b4c885ee550a3e7b3dfc21896d9ae8a1ba1
corrected candidate evidence   e39f1aca2f2f4ad4f14d3487b8b0c0c8918964b5
review reopen                  recorded by the earlier reviewer-owned status commit
reviewer-aid format commit     a070391d3ffdf3540bc7ceaecfd9cb24d44cfe67
final review-fix commit        c159dd9e38c4a6650669166499958f2d436d9e62
candidate evidence/status      fc81d55a84eddbe441b3e4e078aa57874a83481c
package-closure review reopen  3e57bd2b7e604803defc676d1afecfa19351ea68
package-closure test commit    29e47eca66667b0e8ba8aefea410476d6dd0710f
package-closure evidence       recorded by the commit containing this status
M2-S09                         BLOCKED / not started
review decision                pending / reviewer-owned
```

Reviewer outcome for `fc81d55a84eddbe441b3e4e078aa57874a83481c`:

```text
S08-VRF-05  OPEN — add existing package-parent initializers to root and import closure
S08-VRF-06  CLOSED — finite abstract-negative capability audit remains accepted
S08-VRF-07  CLOSED — reviewer ACCEPTED all-pass coherence remains accepted
```

The rejected defect was test-only. Python imports existing parent package initializers before a submodule, but the permanent Alembic mutation audit could omit those parents when only the deepest module was a root or imported target. The bounded correction now adds parent-to-child initializer closure without inventing absent namespace-package initializers, without adding a new finding identifier and without modifying production, API, CLI, schema, migration, dependencies or locks.

### Package-parent initializer corrected candidate

The synchronized starting HEAD and reviewer reopen is
`3e57bd2b7e604803defc676d1afecfa19351ea68`, which contains the rejected
candidate baseline `fc81d55a84eddbe441b3e4e078aa57874a83481c`. The test-only
implementation is `29e47eca66667b0e8ba8aefea410476d6dd0710f`; the candidate
evidence/status commit is the commit containing this record.

The bounded audit now computes the deterministic parent-to-child chain of
only those module initializers present in the supplied module-source map. It
applies that chain to root and import closure, preserves relative and absolute
import handling, terminates on cycles, deduplicates findings, and bounds
diagnostic call paths to eight entries. Permanent regressions cover root,
imported and nested parent initializers, safe and missing namespace chains,
cycles, and the real NETAUTO root families. The real production audit remains
empty.

```text
S08-VRF-05 focused             13 selected / 13 unique / 14 passed — 1.75 s
S08 review-fix registry        7 exact keys / 25 selected / 24 unique / 37 passed — 2.30 s
M2-VER-31                      31 selected / 31 unique / 39 passed — 22.62 s
M2-VER-32                      47 selected / 47 unique / 64 passed — 17.25 s
S08/T10 and traceability       114 passed — 32.95 s
51 delivered scenarios        51 IDs / 91 unique targets / 95 passed — 60.11 s
complete S06                   72 passed — 5.10 s
complete S07/T9                18 passed — 42.53 s
API/error/CLI                  246 passed / 1 known warning — 50.09 s
schema/Alembic                 28 passed / compare_metadata [] — 13.70 s
runtime/schema-guard/Health    121 passed / 1 known warning — 15.51 s
PostgreSQL/concurrency         254 passed / 599 deselected / 1 known warning — 190.16 s
non-PostgreSQL                 599 passed / 254 deselected / 1 known warning — 79.06 s
complete repository           853 passed / 1 known warning — 265.87 s
collection                    853 — 1.78 s
skip / xfail / rerun          0 / 0 / 0
supported 40P01 / 40001       0 / 0
negative controls             40P01 x1 / 40001 x2, exact expected census
```

`uv lock --check`, `uv sync --locked`, `uv build`, Ruff format, Ruff lint and
Pyright pass. The release remains version `0.2.0`; the wheel remains
`netauto-0.2.0-py3-none-any.whl`, 165978 bytes / 77 members, SHA-256
`38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60`.
The embedded runtime lock remains 48238 bytes, SHA-256
`0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf`.
The externally supplied real target reports PostgreSQL 16.14
(`16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)`), database identity `netautotest`,
and a successful bounded `SELECT 1` probe. The only warning is the already
censused Starlette/FastAPI TestClient deprecation.

Production, API, CLI, Health, metadata, schema, migration, dependencies,
`uv.lock`, the embedded runtime lock and wheel content are unchanged. No PR,
GitHub Actions workflow or run, tag, GitHub Release, acceptance record or
artifact publication was created. M2-S08 is not `COMPLETED`; M2-S09 remains
`BLOCKED` and has not started.

Prior reviewer outcome for `e39f1aca2f2f4ad4f14d3487b8b0c0c8918964b5`:

```text
S08-VRF-05  detect mutating Alembic calls executed during module/class initialization
S08-VRF-06  give abstract deployment/security/data-protection negatives sufficient semantic audits
S08-VRF-07  allow reviewer ACCEPTED only for an internally all-pass final-evidence record
```

The findings are implementation defects in the S08 test/evidence harness. They do not reopen the frozen architecture and do not authorize production, schema, migration, API, CLI, dependency or lock changes. The previous corrective execution aid remains non-normative historical support:

```text
docs/milestones/M2/wip/M2-S08-review-fixes-codex-prompt.md
```

The current bounded authorization is this reviewer-owned status plus the package-initializer correction instructions supplied to the implementer.

### Final S08-VRF-05 / 06 / 07 corrective candidate

The synchronized starting HEAD is
`e5b30e6725c13f3e065ef90cc3cdf41995d0e55e`, which contains the required
`e39f1aca2f2f4ad4f14d3487b8b0c0c8918964b5` ancestry and the reviewer-owned
reopen. The corrected candidate closes the three bounded findings without
changing production, API, CLI, schema, migration, dependency or lock content:

```text
S08-VRF-05  module/class initialization, definition-time calls and lexical alias scope covered
S08-VRF-06  finite capability policy plus required synthetic positive/negative counterexamples covered
S08-VRF-07  reviewer ACCEPTED conditional all-pass coherence covered
focused S08-VRF-05/06/07      13 selected / 13 unique / 24 passed — 1.76 s
review-fix registry            7 exact keys / 19 selected / 18 unique / 31 passed — 2.24 s
M2-VER-31                      31 selected / 31 unique / 39 passed — 22.46 s
M2-VER-32                      41 selected / 41 unique / 58 passed — 16.83 s
S08/T10 and traceability       91 passed — 28.84 s
51 delivered scenarios        51 IDs / 91 unique targets / 95 passed — 59.16 s
complete S06                   72 passed — 5.12 s
complete S07/T9               18 passed — 42.03 s
API/error/CLI                  61 passed / 1 known warning — 28.80 s
schema/Alembic                22 passed / compare_metadata [] — 11.46 s
runtime/schema-guard/Health   107 passed / 1 known warning — 9.78 s
PostgreSQL/concurrency        254 passed / 593 deselected / 1 known warning — 190.42 s
non-PostgreSQL                593 passed / 254 deselected / 1 known warning — 78.45 s
complete repository          847 passed / 1 known warning — 266.14 s
collection                   847 — 1.82 s
skip / xfail / rerun          0 / 0 / 0
supported 40P01 / 40001       0 / 0
negative controls             40P01 x1 / 40001 x2, exact expected census
```

`uv lock --check`, `uv sync --locked`, `uv build`, Ruff format, Ruff lint and
Pyright pass. The reviewer-authorized execution aid formatting commit
`a070391d3ffdf3540bc7ceaecfd9cb24d44cfe67` contains only the mechanical Ruff
formatter delta in
`docs/milestones/M2/wip/M2-S08-review-fixes-codex-prompt.md`.
The artifact remains 165978 bytes / 77 members with SHA-256
`38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60`;
the 48238-byte embedded lock remains SHA-256
`0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf`.
The real external test target reports PostgreSQL 16.14 and database identity
`netautotest`; the bounded `SELECT 1` probe succeeds.

The candidate was published for reviewer inspection only; it is superseded operationally by the package-closure reopen above. M2-S08 is not `COMPLETED`, no final acceptance is claimed, and M2-S09 remains `BLOCKED`.

The first post-push repository gate on `b8c78c712d61514998281ea170e7606e1eb99781` produced `815 passed / 1 failed`: `tests/test_m2_s06_process.py::test_ctrl_r_searches_only_current_in_memory_history` waited for a literal prompt repaint after cancelling reverse search. Prompt Toolkit may legally perform a differential terminal redraw without retransmitting that literal. The bounded test-only correction synchronizes on the structured `/exit` acknowledgement after Ctrl-C, which proves that reverse search was cancelled and command input resumed. That failed candidate was not handed off; its execution correctly returned S08 to `IN PROGRESS` before the later authorized continuation recorded below.

Post-push and corrective evidence:

```text
b8c78c7 VER-31                 31 selected / 31 unique / 39 passed — 22.67 s
b8c78c7 VER-32                 23 selected / 23 unique / 27 passed — 15.46 s
b8c78c7 S08/T10 + trace        60 passed — 27.56 s
b8c78c7 51 delivered scenarios 51 IDs / 91 unique targets / 95 passed — 61.04 s
b8c78c7 API/error/CLI equality  37 passed — 3.07 s
b8c78c7 schema/Alembic         28 passed — 6.74 s
b8c78c7 S07/T9                 18 passed — 42.11 s
b8c78c7 PostgreSQL             254 passed / 562 deselected — 189.36 s
b8c78c7 non-PostgreSQL         562 passed / 254 deselected — 76.75 s
b8c78c7 repository             815 passed / 1 PTY failure — 273.24 s
9027b02 corrected PTY target    1 passed — 1.28 s
9027b02 complete S06            72 passed — 4.85 s
9027b02 quality/collection      PASS / 816 collected
9027b02 S08/T10 + trace         60 passed — 26.19 s
9027b02 repository             816 passed — 260.67 s
9027b02 skip / xfail / rerun    0 / 0 / 0
9027b02 supported 40P01/40001   0 / 0
9027b02 negative controls       40P01 x1 / 40001 x2, exact expected census
```

The corrective SHA was not promoted by that superseded execution. The subsequent authorized continuation from `02a3a98ce5fc14419bcc795a8520ad1659140805` closed the four bounded verification findings below and executed a fresh complete candidate cycle. No final-acceptance claim is made.

### S08 verification review continuation

Closed findings:

```text
S08-VRF-01  WIP census accepts the active S08 aid and its reviewer-owned removal
S08-VRF-02  131 negative surfaces have entry-specific semantic target ownership
S08-VRF-03  automatic-migration absence is alias-safe and call-graph-aware
S08-VRF-04  evidence validation separates implementer and reviewer phases
```

The WIP proof preserves exactly 19 historical disposition rows and the two permanent closure records while treating only `M2-S08-codex-prompt.md` as optional. The prompt-present test and a real temporary prompt-absent execution both pass.

The negative-surface registry remains exactly 131 entries and now contains 65 distinct target sets over 47 concrete domain, API, CLI, schema, migration, runtime and T9 test targets. Deployment inspection evaluates forbidden basenames and path components recursively.

The automatic-migration audit follows the complete server/lifespan/runtime/CLI import and call closure, resolves aliased `alembic.command` imports and local wrappers, rejects mutating upgrade/downgrade/stamp/revision/merge calls and permits only non-mutating Config/ScriptDirectory/MigrationContext introspection.

Evidence validation now requires null `reviewer_decision` in implementer phase and one of `ACCEPTED` / `REVIEW CHANGES REQUIRED` in reviewer phase. It rejects database URLs, DSNs, URL userinfo and secret-bearing values while accepting HTTP/HTTPS endpoints without userinfo.

Review-fix pre-publication evidence:

```text
focused four findings           20 passed — 2.52 s
real prompt-absent WIP proof     1 passed — 1.66 s
M2-VER-31 selected/unique/pass  31 / 31 / 39 — 21.90 s
M2-VER-32 selected/unique/pass  29 / 29 / 35 — 15.72 s
S08/T10 + M1/S00/M2 trace       68 passed — 27.67 s
51 delivered scenarios          51 IDs / 91 unique targets / 95 passed — 58.50 s
complete S06                    72 passed — 4.98 s
complete S07/T9                 18 passed — 41.11 s
API/error/CLI equality          37 passed — 3.02 s
schema/Alembic positive/negative 32 passed — 7.00 s
PostgreSQL suite               254 passed / 570 deselected — 185.68 s
non-PostgreSQL suite           570 passed / 254 deselected — 77.46 s
complete repository            824 passed — 260.23 s
skip / xfail / rerun             0 / 0 / 0
warnings                         1 unchanged third-party Starlette deprecation
supported 40P01 / 40001          0 / 0
negative-control 40P01 / 40001   1 / 2, exact expected census
```

Quality and candidate artifact:

```text
uv lock --check / sync / build PASS
Ruff format / lint             PASS — 236 files / no findings
Pyright strict                 PASS — 0 errors / 0 warnings
pytest collection              824 tests
wheel size / members           165978 bytes / 77
wheel SHA-256                  38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60
runtime lock size              48238 bytes
runtime lock SHA-256           0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf
```

Production, schema, migration, public API, CLI, dependencies, `uv.lock` and the embedded runtime lock remain unchanged. No candidate-specific evidence record or `acceptance.md` exists; M2-S09 remains blocked.

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

Review the published package-closure corrected candidate for:

```text
S08-VRF-05 — import-time Alembic mutation closure
```

The exact correction is the existing package initializer chain for roots and imported modules under `S08-VRF-05`; the finding registry remains exactly `S08-VRF-01 ... S08-VRF-07`. The implementer handoff is `M2-S08 CANDIDATE READY FOR REVIEW`. Do not start `M2-S09` before reviewer-owned completion of `M2-S08`.

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
