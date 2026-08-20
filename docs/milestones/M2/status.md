# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S08 REVIEW CHANGES REQUIRED

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S08 — REVIEW CHANGES REQUIRED
current task    close S08-VRF-05 package-aware relative-import analysis
blockers        M2-S09 remains blocked; one verification-harness finding is open
```

The M2 contract, architecture set and implementation decomposition are `FINAL / FROZEN`.

Implementation or review-fix work is authorized only for the exact slice marked `READY`, `IN PROGRESS` or `REVIEW CHANGES REQUIRED` here. `REVIEW CHANGES REQUIRED` authorizes only bounded corrective work for the recorded finding inside the same slice. No later slice may begin before its predecessor is reviewer-owned `COMPLETED`.

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
| `M2-S08` | REVIEW CHANGES REQUIRED | `M2-S07 COMPLETED` |
| `M2-S09` | BLOCKED | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00` through `M2-S07` are reviewer-owned `COMPLETED`. No later implementation slice is completed.

## Current blocker and reviewer finding

No contract, architecture, implementation-planning, technology or infrastructure blocker is open.

The candidate below closes the previously identified package-parent initializer omission, the abstract-negative capability audit, reviewer-acceptance coherence and the preserved S06 PTY gate. One bounded defect remains in the test-only Alembic mutation analysis:

```text
S08-VRF-05  OPEN
    package-aware relative-import closure

S08-VRF-06  CLOSED
    finite abstract-negative capability audit

S08-VRF-07  CLOSED
    reviewer ACCEPTED all-pass coherence

preserved S06 PTY regression  CLOSED
    pending-aware reader and structured Ctrl-R proof accepted
```

Python resolves relative imports against `__package__`. For an ordinary module, `__package__` is the parent package; for a package initializer represented by `__init__.py`, `__package__` is the module name itself. The current test helper stores package initializers under names such as `sample` or `sample.api` but does not retain that package identity. Consequently, relative imports executed from package initializers can be resolved as top-level names and their reachable Alembic mutation can be omitted.

Representative false-negative shapes:

```text
sample/__init__.py
    from . import migrator

sample/migrator.py
    import-time alembic.command.upgrade(...)

sample/api/__init__.py
    from .. import migrator

sample/migrator.py
    import-time alembic.command.stamp(...)
```

The bounded correction must preserve explicit package metadata in the synthetic and real production source inventories, use it in both import-edge and import-alias resolution, and retain all previously accepted module/class/package-parent, alias, wrapper, call-path and PTY behavior.

This is a verification-harness defect only. It does not reopen the frozen architecture and does not authorize production, API, CLI, Health, schema, migration, dependency, lock or artifact changes.

`TEST_DATABASE_URL` is externally supplied when it is explicitly provided by the environment and NETAUTO test code does not provision, invent or silently substitute it. A loopback or local hostname is not itself a blocker. The implementer must verify that the configured URL uses the supported PostgreSQL/Psycopg form, reaches real PostgreSQL, and identifies the dedicated test target required by the existing test-support safety checks.

## M2-S08 review chain

```text
original execution aid         8ee9e540d24ecf07c8688350a03162a89d0991ce
initial implementation         3d794d25317425254440f4e4b711ebfb63113edf
first candidate evidence       b8c78c712d61514998281ea170e7606e1eb99781
first PTY correction           9027b02b7f2b949cd7674adfa7c3fe3758eacda3
corrective handoff             02a3a98ce5fc14419bcc795a8520ad1659140805
verification review-fix        42843b4c885ee550a3e7b3dfc21896d9ae8a1ba1
corrected candidate evidence   e39f1aca2f2f4ad4f14d3487b8b0c0c8918964b5
reviewer-aid format            a070391d3ffdf3540bc7ceaecfd9cb24d44cfe67
remaining verification fixes  c159dd9e38c4a6650669166499958f2d436d9e62
candidate evidence             fc81d55a84eddbe441b3e4e078aa57874a83481c
package-parent review reopen   3e57bd2b7e604803defc676d1afecfa19351ea68
package-parent test fix        29e47eca66667b0e8ba8aefea410476d6dd0710f
package-parent candidate       b53de79eb831c8da6fd965fa07c0562f2b010482
failed exact-remote record     3bfa3ab62e28c6309dde8c8d916cb3b0fada07bb
PTY deterministic test fix     954fd86f576f3b4a0ec4efb8849cf059c801dfef
PTY-closure candidate          c4cd4e633afaafa395a67f2b9efcc396906052e1
current review reopen          recorded by the commit containing this status
M2-S09                         BLOCKED / not started
review decision                REVIEW CHANGES REQUIRED / reviewer-owned
```

The immutable history preserves every prior candidate and failed gate. No reset, rebase or force-push is authorized.

## Rejected candidate evidence

The rejected `c4cd4e633afaafa395a67f2b9efcc396906052e1` candidate produced the following exact-remote evidence. The results remain valid for the material they cover but do not close the relative-import false negative above.

```text
focused Ctrl-R target          1 passed
complete PTY process file      7 passed
complete S06                   73 passed
package-initializer focused    6 passed
S08-VRF-05                     13 targets / 14 passed
S08 review-fix registry        7 exact keys / 25 unique targets / 38 passed
M2-VER-31                      31 targets / 39 passed
M2-VER-32                      47 targets / 64 passed
S08/T10 and traceability       114 passed
51 delivered scenarios        91 unique targets / 95 passed
complete S07/T9                18 passed
API/error/CLI                  247 passed
schema/Alembic                 28 passed / compare_metadata []
runtime/schema-guard/Health    121 passed
PostgreSQL/concurrency         254 passed / 600 deselected
non-PostgreSQL                 600 passed / 254 deselected
complete repository            854 passed
collection                    854
skip / xfail / rerun          0 / 0 / 0
warnings                      1 unchanged third-party Starlette deprecation
supported 40P01 / 40001       0 / 0
negative controls             40P01 x1 / 40001 x2, exact expected census
```

Quality and artifact evidence:

```text
uv lock --check               PASS
uv sync --locked              PASS
uv build                      PASS
Ruff format / lint            PASS
Pyright strict                PASS — 0 errors / 0 warnings
release                       0.2.0
wheel                         netauto-0.2.0-py3-none-any.whl
wheel size / members          165978 bytes / 77
wheel SHA-256                 38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60
runtime lock size             48238 bytes
runtime lock SHA-256          0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf
PostgreSQL                    16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
database identity             netautotest
bounded SELECT 1              PASS
```

Production, API, CLI behavior and grammar, Health, metadata, schema, migration, dependencies, `uv.lock`, the embedded runtime lock and artifact content were unchanged. No PR, GitHub Actions workflow or run, tag, GitHub Release, acceptance record or artifact publication was created.

## Authorized bounded continuation

The only active non-normative execution aid is:

```text
docs/milestones/M2/wip/M2-S08-review-fixes-codex-prompt.md
```

The aid authorizes only the package-aware relative-import continuation of `S08-VRF-05`. It must not be used as semantic authority and must remain subordinate to the frozen contract, architecture, steps and this reviewer-owned status.

Permitted implementation files are limited to:

```text
tests/support/s08_static.py
tests/test_m2_s08_negative_surface.py
tests/test_m2_traceability.py
docs/milestones/M2/status.md
```

The implementer must preserve:

```text
S08_REVIEW_FIX_TARGETS         exact S08-VRF-01 ... S08-VRF-07
M2-VER-31                      IMPLEMENTED and non-empty
M2-VER-32                      IMPLEMENTED and non-empty
negative-surface identifiers   131
canonical scenarios            83
safety predicates              21
business HTTP operations       63
Health operations              1
CLI remote / local operations  63 / 8
public error codes             23
authoritative tables           15
Alembic base / head            1 / 1, 0001_m2_kernel
release                        0.2.0
```

The only permitted implementer handoff is:

```text
M2-S08    CANDIDATE READY FOR REVIEW
M2-S09    BLOCKED
```

`M2-S08 COMPLETED`, final acceptance, delivery, merge, tag, Release and the start of M2-S09 remain reviewer/human-owned.

## Prior reviewer-owned completion ledger

Detailed implementation, finding and evidence records remain in their acceptance commits and repository history.

| Slice | Reviewer acceptance | Accepted full-suite census |
|---|---|---:|
| `M2-S07` | `1f8e82de73d953830a6b31045ec96dfe19116dd9` | 785 |
| `M2-S06` | `b105e774765e7d8a2c68ab14501cfd6043eadf13` | 765 |
| `M2-S05` | `e1f11b8bf655079ed7c8aff99b56c2b2e4d17c03` | 691 |
| `M2-S04` | `bd342146679e405365ab93e4a60ca85b60834161` | 561 |
| `M2-S03` | `2b89f4ce79272554721ff694dd8ae8e32e7fab25` | 446 |
| `M2-S02` | `850abd97ece1aadeae65aa090d86c7ec4982751f` | 411 |
| `M2-S01` | `24e7b788b6b7f54d96614ef2c37bffbeb25ebd8b` | 349 |
| `M2-S00` | `d225faee6faf5fbebd36ce68db6c3b2c537323d0` | 314 |

## Immediate next action

Execute the bounded corrective aid for:

```text
S08-VRF-05 — package-aware relative-import closure
```

Do not start M2-S09 before reviewer-owned completion of M2-S08.

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
