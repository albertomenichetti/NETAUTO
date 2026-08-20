# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S08 READY

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S08 — READY
current task    prepare the M2-S08 Codex implementation prompt and execute the authorized slice
blockers        none
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
| `M2-S08` | READY | `M2-S07 COMPLETED` |
| `M2-S09` | BLOCKED | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00` through `M2-S07` are reviewer-owned `COMPLETED`. No later implementation slice is completed.

## Current blockers and findings

No contract, architecture, implementation-planning, technology, infrastructure or verification blocker is open for starting `M2-S08`.

`M2-S08` is limited to integrated regression, complete machine-checkable traceability, the M2 delta allowlist and positive/negative surface closure. It must preserve the completed kernel, runtime, Health, CLI and installed-release capabilities. It must not begin `M2-S09` final acceptance before reviewer-owned completion of S08.

Any implementation finding that exposes an incomplete or contradictory frozen decision places the affected work in `STOP` and follows the explicit reopen/revalidate/propagate/re-freeze process.

## M2-S07 completion record

Reviewer result:

```text
M2-S07                         COMPLETED
original prompt                bf498153c458f585cd1a6914a9ac4aa904ebd34c
initial implementation         0934671324cca40e8e5e0608449c5a5b3524e662
initial evidence/status        dd58e8b342fae12639a731b86953a323e3da5b62
corrective implementation      a81dd3a4b85795d4f153580d2b9407bd482df363
corrected candidate evidence   c8402a222c537ab6d874b0d7bdb2b4ec6d23f7f8
review acceptance              recorded by the commit containing this status
M2-S08                         READY / not started
```

Closed continuation findings:

```text
PTY split sentinel
    PtyProcess.read_until retains one contiguous pending buffer, recognizes a
    sentinel split across several reads and preserves every byte after the match.
    Permanent pure evidence forces b"netau" + b"to>tail" and verifies exact tail
    reuse without loss, duplication or reordering.

Linux lock regeneration
    The documented uv export uses the same relative pylock carrier as permanent
    regeneration evidence, so the generated header and committed runtime lock are
    byte-comparable.

Linux target ownership and release selection
    The operator procedure separates privileged /opt/netauto creation from the
    unprivileged release workflow, uses the newly-created venv Python to extract
    the lock and selects current atomically only after verification and successful
    explicit migration.

Installed Alembic secret composition
    The installed migration environment uses load_settings(), so direct
    NETAUTO_* values and explicit NETAUTO_SECRETS_DIR files follow the same
    validated production source composition as server startup.

Orderly process shutdown and disposal
    T9 sends SIGTERM to the installed Uvicorn process, requires the NETAUTO and
    Uvicorn shutdown markers, and observes disappearance of the worker's dedicated
    PostgreSQL sessions. Observer engines use a distinct application identity.
```

Accepted S07 capability:

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

Accepted verification produced by the candidate before publication:

```text
uv lock --check                  PASS — 46 packages resolved
uv sync --locked                 PASS — 44 packages checked
uv build / verbose build         PASS — sdist + wheel; Hatchling 1.32.0
Ruff format / lint               PASS — 230 files / no findings
Pyright strict                   PASS — 0 errors / warnings / informations
pytest collection                781 tests / 1 locked warning
PTY + guide + registry           3 passed
S07 PostgreSQL                   3 passed
S07 non-PostgreSQL               12 passed
S07 complete / T9                15 passed
M2-VER-24 primary + support      14 passed
M2-VER-29 primary                5 passed
M2-VER-30 primary + support      34 passed
installed support 22/23/25-28   7 passed
M2 traceability                  21 passed
schema / runtime / migration     123 passed
all S05                          126 passed
all S06                          72 passed
Health / S04                     39 passed
PostgreSQL concurrency           182 passed
all non-PostgreSQL               527 passed
complete repository              781 passed — 243.80 s
skip / xfail / rerun             0 / 0 / 0
warning census                   1 locked StarletteDeprecationWarning
supported 40P01 / 40001          0 / 0
negative-control 40P01 / 40001   1 / 2, expected
```

Exact-remote post-push verification accepted for the reviewed candidate:

```text
runtime-lock equality            1 passed
S07 / T9 complete                15 passed — 40.30 s
required bundle union            51 passed — 58.61 s
M2 traceability                  21 passed
PostgreSQL / concurrency         182 passed — 117.45 s
non-PostgreSQL                   527 passed — 62.32 s
complete repository              781 passed — 250.73 s
skip / xfail / rerun             0 / 0 / 0
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
CPython                          3.14.7
uv                               0.12.3
Hatchling                        1.32.0
PostgreSQL                       16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
Linux                            Ubuntu 24.04.4 LTS / kernel 6.8.0-134-generic
```

Unchanged boundaries:

```text
authoritative tables             15
Alembic graph                    one base / one head (0001_m2_kernel)
migration DDL                    unchanged
compare_metadata                 []
third-party uv.lock records      45 unchanged
business HTTP operations         41 mutations + 22 reads = 63
operational HTTP operations      1 Health; total public HTTP = 64
CLI local / remote operations    8 / 63
registry examples                65
canonical scenarios/predicates   83 / 21
GitHub Actions / PR / tag        absent
published release/artifact       absent
```

`M2-VER-24`, `M2-VER-29` and `M2-VER-30` are accepted as the primary S07 bundles. Installed-artifact support for `M2-VER-22`, `23`, `25`, `26`, `27` and `28` is accepted without transferring primary ownership. `M2-VER-31` and `M2-VER-32` remain owned by S08.

Reviewer inspection verified the published commit chain, wheel and runtime-lock realization, exact version delta, installed Alembic composition, PTY buffering, Linux procedure, installed-process lifecycle, real-PostgreSQL T9 harness, HTTPS/secret boundary and traceability registration. The reviewer did not independently re-execute the 781-test suite; the accepted execution results are the candidate's exact-remote evidence.

No blocking review finding remains open for `M2-S07`.

The concluded S07 execution aid is retired from the working tree by the same reviewer-owned acceptance commit:

```text
docs/milestones/M2/wip/M2-S07-codex-prompt.md
```

## Prior reviewer-owned completion ledger

Detailed implementation, finding and evidence records remain in their acceptance commits and repository history.

| Slice | Reviewer acceptance | Accepted full-suite census |
|---|---|---:|
| `M2-S06` | `b105e774765e7d8a2c68ab14501cfd6043eadf13` | 765 |
| `M2-S05` | `e1f11b8bf655079ed7c8aff99b56c2b2e4d17c03` | 691 |
| `M2-S04` | `bd342146679e405365ab93e4a60ca85b60834161` | 561 |
| `M2-S03` | `2b89f4ce79272554721ff694dd8ae8e32e7fab25` | 446 |
| `M2-S02` | `850abd97ece1aadeae65aa090d86c7ec4982751f` | 411 |
| `M2-S01` | `24e7b788b6b7f54d96614ef2c37bffbeb25ebd8b` | 349 |
| `M2-S00` | `d225faee6faf5fbebd36ce68db6c3b2c537323d0` | 314 |

## Immediate next action

Prepare and execute the implementation prompt for:

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
