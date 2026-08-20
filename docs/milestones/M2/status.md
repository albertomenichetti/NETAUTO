# M2 — Milestone Status

**Milestone status:** IMPLEMENTATION — M2-S07 REVIEW CHANGES REQUIRED

## Cycle identity

```text
cycle       M2
cycle type  milestone
branch      M2
```

## Current operational state

```text
phase           IMPLEMENTATION
current slice   M2-S07 — REVIEW CHANGES REQUIRED
current task    close S07-RF-01 and S07-RF-02, then republish the exact candidate
blockers        none inside the bounded S07 correction; M2-S08 is dependency-blocked
```

The M2 contract, architecture set and implementation decomposition are `FINAL / FROZEN`.

Implementation or review-fix work is authorized only for the exact slice marked `READY`, `IN PROGRESS` or `REVIEW CHANGES REQUIRED` here. `REVIEW CHANGES REQUIRED` authorizes only bounded corrective work for the recorded findings inside the same slice. No later slice may begin before its predecessor is reviewer-owned `COMPLETED`.

## Design and delivery gates

| Gate | State |
|---|---|
| Contract | FINAL / FROZEN |
| Architecture set | FINAL / FROZEN |
| Implementation steps | FINAL / FROZEN |
| Implementation | REVIEW CHANGES REQUIRED — `M2-S07` ONLY |
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
| `M2-S07` | REVIEW CHANGES REQUIRED | `M2-S06 COMPLETED` |
| `M2-S08` | BLOCKED | `M2-S07 COMPLETED` |
| `M2-S09` | BLOCKED | `M2-S00 ... M2-S08 COMPLETED` |

`M2-S00` through `M2-S06` are reviewer-owned `COMPLETED`. `M2-S07` is reopened only for the bounded findings below. No later implementation slice is completed or authorized.

## Current blockers and reviewed findings

No contract, architecture, implementation-planning, technology or infrastructure contradiction is open. The S07 wheel, installed Alembic realization, Linux T9 harness, PostgreSQL lifecycle evidence and trust/TLS behavior remain the candidate baseline.

A late reviewer inspection found two bounded completion gaps after candidate commit `c8402a222c537ab6d874b0d7bdb2b4ec6d23f7f8`:

```text
S07-RF-01
    The Linux operating guide does not document the complete installed Settings
    contract required by M2-AC-29 / M2-VER-29: canonical environment names,
    required/default values, validation boundaries and fail-fast consequences.

S07-RF-02
    The S07 primary bundle registries do not assign all already-required evidence
    to M2-VER-24 / 29 / 30, and lack explicit installed evidence for server
    independence from CLI plus absence of a 401/403/native-auth contract.
```

The reviewer-owned acceptance commit:

```text
a487e7c51c0b6ff0b15e1f3cfcb3702a9618f7ef
docs(m2): accept S07 and open S08
```

was appended before these late findings were recorded. It remains in immutable history but is superseded operationally by the later commit containing this status. No history is rewritten, reverted or force-pushed. `M2-S08` returns to `BLOCKED / not started` until S07 is accepted again.

Any implementation finding that exposes a genuinely incomplete or contradictory frozen decision places the affected work in `STOP` and follows the explicit reopen/revalidate/propagate/re-freeze process. The two current findings do not require an architecture reopen.

## M2-S07 reopened review record

Reviewer result:

```text
M2-S07                         REVIEW CHANGES REQUIRED
original implementation prompt bf498153c458f585cd1a6914a9ac4aa904ebd34c
initial implementation         0934671324cca40e8e5e0608449c5a5b3524e662
initial evidence/status        dd58e8b342fae12639a731b86953a323e3da5b62
continuation implementation    a81dd3a4b85795d4f153580d2b9407bd482df363
candidate evidence/status      c8402a222c537ab6d874b0d7bdb2b4ec6d23f7f8
superseded acceptance          a487e7c51c0b6ff0b15e1f3cfcb3702a9618f7ef
reopen record                  recorded by the commit containing this status
M2-S08                         BLOCKED / not started
```

### `S07-RF-01` — Installed Settings contract is incomplete in operator guidance

Frozen acceptance requires the Linux procedure to cover the database URL, pool settings, log level, bind, workers, explicit Alembic, orderly shutdown and Health. Verification additionally requires `database_url` and pool defaults/validation.

The guide currently lists logical setting names and demonstrates some values, but it does not present one complete operator-facing inventory for:

```text
NETAUTO_DATABASE_URL
    required
    canonical SQLAlchemy URL
    driver postgresql+psycopg

NETAUTO_LOG_LEVEL
    default INFO
    CRITICAL | ERROR | WARNING | INFO | DEBUG

NETAUTO_POOL_SIZE
    default 10
    integer >= 1

NETAUTO_MAX_OVERFLOW
    default 20
    integer >= 0
    -1 / unlimited forbidden

NETAUTO_POOL_TIMEOUT
    default 5.0 seconds
    finite and > 0

NETAUTO_POOL_RECYCLE
    default disabled / omitted
    positive whole seconds when present

NETAUTO_POOL_PRE_PING
    default false
    canonical true | false source values
```

Required correction:

```text
Linux guide
    -> document canonical environment name, required/default value,
       validation boundary and fail-fast behavior for every installed setting
    -> distinguish application Settings from Uvicorn host/port/workers
    -> make the canonical log-level behavior explicit in text or command

installed evidence
    -> inspect the Settings model from the wheel-installed environment
    -> prove documented defaults equal installed defaults
    -> exercise representative invalid boundaries for every constrained field
    -> prove invalid configuration fails before serving and does not leak secrets
```

Documentation string-presence checks alone are insufficient.

### `S07-RF-02` — Primary bundle membership is not complete against frozen obligations

The current tests largely implement the required behavior, but primary bundle ownership is incomplete.

Required `M2-VER-24` membership must include evidence for:

```text
one wheel and one version
installed unique graph
explicit installed Alembic
installed server start/lifecycle
installed CLI invocation
no implicit cross-action
server import/composition independent from netauto.cli
```

At minimum, add the existing explicit-Alembic and installed server lifecycle targets to `S07_PRIMARY_BUNDLE_TARGETS["M2-VER-24"]`, and add one explicit installed server-with-CLI-blocked import/composition target.

Required `M2-VER-29` membership must include one installed Settings/default/invalid-boundary target that is also correlated with the operator guide.

Required `M2-VER-30` membership must include evidence for:

```text
no native auth / authorization / credential surface
no 401 / 403 public contract
verified HTTPS without bypass
trusted-boundary documentation
real Health/logging secret non-leakage
```

At minimum, add an installed finite no-401/403/no-security-scheme target and include the existing real-PG lifecycle/transport-cut targets that prove secrets are absent from process output and Health failure bodies.

Create a permanent review-fix registry:

```text
S07_REVIEW_FIX_TARGETS = {
    "S07-RF-01": frozenset({...}),
    "S07-RF-02": frozenset({...}),
}
```

and machine-check that each finding target exists, is collected and belongs to the required complete bundle union. Tests may legitimately belong to more than one evidence bundle.

The traceability gate must assert the required cross-memberships explicitly; merely proving that every `test_m2_s07_*` function occurs somewhere is not sufficient.

## Candidate capability retained during correction

The following candidate realization remains the bounded starting point and must not be redesigned:

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

Candidate execution evidence already produced and requiring preservation/re-execution:

```text
pytest collection                781 tests
S07 / T9 complete                15 passed
M2-VER-24 reported union         14 passed
M2-VER-29 reported primary       5 passed
M2-VER-30 reported union         34 passed
installed support 22/23/25-28   7 passed
PostgreSQL / concurrency         182 passed
non-PostgreSQL                   527 passed
complete repository              781 passed
skip / xfail / rerun             0 / 0 / 0
supported 40P01 / 40001          0 / 0
negative-control 40P01 / 40001   1 / 2, expected
```

These results remain valid execution facts for their actual targets but do not close the two reviewed completion gaps.

Candidate artifact facts before the bounded correction:

```text
wheel                            netauto-0.2.0-py3-none-any.whl
wheel size / members             165978 bytes / 77
wheel SHA-256                    38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60
runtime lock size                48238 bytes
runtime package census           29 total / 27 applicable on Linux CPython
runtime lock SHA-256             0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf
migration checksum               379165a1eda83c226a6c1e5dc4f493c7fa0d0c8dba39449a1d004751aaa39c57
CPython / uv / Hatchling         3.14.7 / 0.12.3 / 1.32.0
PostgreSQL                       16.14
```

## Unchanged boundaries

The review correction must preserve:

```text
project version                  0.2.0
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

No dependency, runtime-lock, wheel-content, schema, migration, API, Health or CLI-semantic change is expected for these findings. If such a change appears necessary, stop and report before expanding scope.

## Prior reviewer-owned completion ledger

| Slice | Reviewer acceptance | Accepted full-suite census |
|---|---|---:|
| `M2-S06` | `b105e774765e7d8a2c68ab14501cfd6043eadf13` | 765 |
| `M2-S05` | `e1f11b8bf655079ed7c8aff99b56c2b2e4d17c03` | 691 |
| `M2-S04` | `bd342146679e405365ab93e4a60ca85b60834161` | 561 |
| `M2-S03` | `2b89f4ce79272554721ff694dd8ae8e32e7fab25` | 446 |
| `M2-S02` | `850abd97ece1aadeae65aa090d86c7ec4982751f` | 411 |
| `M2-S01` | `24e7b788b6b7f54d96614ef2c37bffbeb25ebd8b` | 349 |
| `M2-S00` | `d225faee6faf5fbebd36ce68db6c3b2c537323d0` | 314 |

The superseded S07 acceptance remains recorded at `a487e7c51c0b6ff0b15e1f3cfcb3702a9618f7ef` for provenance; it is not the current operational authority.

## Immediate next action

Execute only the bounded S07 review-fix prompt, close `S07-RF-01` and `S07-RF-02`, rerun all mandatory focused/T9/PostgreSQL/full gates on the exact remote candidate, and publish:

```text
M2-S07 — CANDIDATE READY FOR REVIEW
```

not `COMPLETED`.

Do not start `M2-S08` or `M2-S09`.

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

`M2-S08`, `M2-S09`, milestone delivery and merge remain blocked or human/reviewer-owned according to project governance.
