# M2 Verification Architecture

**Status:** DRAFT — VERIFICATION DESIGN COMPLETE — HEALTH/CLI/RUNTIME HOOK REVIEW PASSED — FINAL CLOSURE / IMPLEMENTATION EVIDENCE PENDING

**Authority:** NORMATIVE M2 ARCHITECTURE DRAFT

## Authority and scope

This document owns the M2 verification architecture for:

```text
verification layers and evidence policy
stable acceptance-evidence bundle identifiers
deterministic PostgreSQL scenario registry
lock-planner and failure-classification verification
schema, migration and startup-guard evidence
Health, CLI, packaging and Linux operating evidence
AS-IS regression and negative-surface closure
contract / architecture / implementation traceability
final acceptance-gate evidence requirements
```

Its implementation authority, once the complete M2 architecture set is frozen, is:

```text
docs/architecture/verification.md
    delivered verification AS-IS
+
docs/architecture/verification-concurrency-registry.md
    delivered canonical PostgreSQL scenarios and recipes
+
docs/general/technology_baseline.md
    ratified testing and quality toolchain
+
docs/milestones/M2/contract.md
    FINAL / FROZEN outcomes and acceptance criteria
+
the complete M2 architecture set
    normative realization obligations
+
this document
    M2 verification delta and evidence registry
```

This document does not redefine domain, API, persistence, concurrency, Health, CLI or runtime behavior. It defines the evidence required to prove those owners.

Concrete pytest module/function names, command results and commit-specific pass records are implementation/delivery evidence. They do not replace the stable identifiers and assertions defined here.

---

## 1. Verification gate model

M2 has three distinct verification gates.

### 1.1 Architecture verification-design gate

Before the architecture set may freeze:

```text
every M2-OUT-* has a normative architecture owner
every M2-AC-* has one stable M2-VER-* evidence bundle
every non-trivial concurrency rule has a stable scenario ID
every scenario defines predicates, recipe and required assertions
every negative/non-goal boundary has a verification path
no outcome, criterion, scenario or architecture requirement is orphaned
```

This gate freezes **what evidence must be produced**. It does not require not-yet-authorized M2 implementation code to have already produced that evidence.

### 1.2 Implementation-slice verification gate

After `steps.md` is frozen, each implementation slice must:

```text
implement the evidence targets assigned to that slice
pass every directly affected deterministic check
preserve all previously passing AS-IS regression evidence
leave no unexplained skipped, xfailed or flaky normative scenario
```

A slice is not complete merely because its code path appears functional.

### 1.3 Final acceptance and delivery gate

M2 delivery requires executed evidence against one identified candidate commit and the wheel built from it:

```text
all M2-VER-01 ... M2-VER-32 = PASS
all canonical concurrency scenarios = PASS
all required blocking/progress assertions = PASS
no supported scenario returns SQLSTATE 40P01
AS-IS regression closure = PASS
schema / metadata drift = []
installed-wheel / startup / Health / CLI / Linux evidence = PASS
no blocking finding remains open
```

The concrete form of the final gate—dedicated final slice or external post-slice gate—remains owned by the future frozen `steps.md`.

### 1.4 Governance clarification

Earlier M2 drafts may use phrases such as:

```text
verification supplies deterministic evidence
real PostgreSQL scenarios confirm the realization
```

For architecture freeze, these phrases mean:

```text
deterministic scenario and evidence obligations are completely designed,
registered and traceable
```

Executed implementation evidence is mandatory for slice completion and final delivery, not a prerequisite for authorizing implementation. This separation removes a circular gate while preserving every contract acceptance requirement.

---

## 2. Evidence states and durability

Every stable evidence bundle or scenario has one state in a candidate evidence ledger:

```text
DESIGNED
    normative assertions and ownership are frozen

IMPLEMENTED
    one or more concrete evidence targets exist and are traceable

PASS
    every required target passed for the candidate commit/artifact

FAIL
    at least one required target failed

BLOCKED
    environment or prerequisite prevented execution
```

Only `PASS` satisfies final acceptance.

`SKIP`, `XFAIL`, timeout, infrastructure error or missing target does not count as `PASS` for a normative requirement.

Architecture documents contain durable obligations. Commit-specific commands, timestamps, environment metadata, counts and artifact hashes belong to a final evidence record under:

```text
docs/milestones/M2/evidence/
```

The exact record filename may include the candidate commit or release version. Evidence records never become a competing semantic authority.

---

## 3. Verification layers

M2 preserves the delivered T0–T7 stack and adds three M2 integration layers.

### T0 — Pure domain

Proves:

```text
plain-Python entity/value semantics
canonicalization and validation
version/property evolution rules
DATA_CHANGE and SCHEMA_CHANGE pure transformations
lifecycle transition shape
closure and semantic-view derivation
```

No PostgreSQL claim may rely solely on T0.

### T1 — Application and Unit-of-Work orchestration

Proves:

```text
transport-neutral command/query behavior
candidate construction and failure selection
one semantic operation / one UoW intent
no-op and restart decisions
store/lifecycle coordination contracts
```

Mocks/fakes may be used only where the asserted property is independent of PostgreSQL.

### T2 — Real PostgreSQL persistence integration

Proves:

```text
SQLAlchemy metadata and live schema behavior
PK / UNIQUE / FK / CHECK / CASCADE / RESTRICT
canonical JSONB persistence
complete aggregate commit/rollback
lock-plan SQL and constraint classification
read-snapshot behavior
```

T2 requires real PostgreSQL through `TEST_DATABASE_URL`.

### T3 — Deterministic real-PostgreSQL concurrency

Proves:

```text
supported interleavings
required blocking and required progress
fresh post-wait reads
advisory-gate visibility
PK / UNIQUE / FK arbitration
bounded whole-UoW restart
absence of supported-path deadlocks
```

T3 uses independent sessions and deterministic orchestration. Stress is not a substitute.

### T4 — Public HTTP contract and integration

Proves:

```text
exact route inventory
strict request carriers
omission versus explicit null
status / body / Location
finite error catalog and bounded details
projection, filter, order and cursor behavior
Health wire behavior
no unintended public surface
```

HTTPX `AsyncClient` plus `ASGITransport` remains the in-process API baseline. Lifespan-sensitive tests run the real ASGI lifespan.

### T5 — Alembic, schema lifecycle and startup compatibility

Proves:

```text
fresh root migration
head/base/repeatability
exact live schema and zero metadata drift
installed migration graph
unique shipped head
startup revision guard
no automatic migration
```

### T6 — Targeted property-based verification

Applies where algebraic coverage is materially stronger than examples, including:

```text
PrimitiveType value canonicalization
Relationship property carrier maps
DATA_CHANGE operation combinations
schema migration preserve-or-fail properties
cursor encode/decode binding
lock-plan sorting/coalescence properties
```

T6 supplements deterministic examples.

### T7 — Supplementary stress/randomized verification

Used only for discovery. Any material race or invariant violation is reduced to a deterministic stable scenario where reasonably possible.

### T8 — CLI client, terminal and process contract

Proves:

```text
parser and selector behavior
REPL state machine
terminal editing and history
HTTP exchange trace
stdout/stderr and process exit contract
same-release CLI/server integration
HTTPS verification behavior
```

Pure CLI logic may use controlled transports. Public-authority claims require HTTP, never application-service or database calls.

### T9 — Installed artifact and Linux operating baseline

Proves against a wheel installed outside the repository checkout:

```text
package contents and entrypoints
Alembic graph/resource discovery
server start/stop/restart
worker startup guard
configuration and pool realization
readiness verification
orderly resource release
documented manual procedure
```

### T10 — Static traceability, negative surface and documentation policy

Proves finite inventories and absences that are cheaper and safer to check statically:

```text
OUT / AC / VER / scenario coverage
route and CLI operation set equality
constraint/index positive and negative inventories
forbidden auth/TLS/CLI options
no direct CLI kernel imports
no automatic migration call path
no unresolved normative placeholder
trusted-boundary documentation rules
```

T10 does not replace runtime evidence where behavior is material.

---

## 4. Environment and isolation contract

### 4.1 Canonical toolchain

The ratified toolchain remains:

```text
CPython 3.14.x
uv with committed uv.lock
pytest + pytest-asyncio
HTTPX
real PostgreSQL
Hypothesis where justified
Ruff
Pyright strict
coverage.py as diagnostic evidence
```

Canonical quality commands are derived from `pyproject.toml` and the technology baseline, conceptually:

```text
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest ...
```

A final evidence ledger records the exact commands actually executed.

### 4.2 PostgreSQL target

```text
NETAUTO_DATABASE_URL
    runtime / application / administrative migration target

TEST_DATABASE_URL
    automated real-PostgreSQL evidence target
```

Automated verification never silently falls back to SQLite or an in-process fake.

### 4.3 Database isolation

```text
parallel real-PG worker
    -> isolated PostgreSQL database

deterministic concurrency scenario
    -> unique semantic identifiers
    -> independent sessions
    -> cleanup only after participating sessions terminate
```

When isolated databases are unavailable, interfering PostgreSQL suites execute without cross-worker database parallelism.

### 4.4 Installed-artifact isolation

T9 evidence uses:

```text
built wheel
clean target directory/environment
no repository import path
no retained source checkout requirement
dedicated test database
operator-like configuration and secret locations
```

The test harness may create disposable local files and processes but does not require Docker, Testcontainers or a process manager.

### 4.5 HTTPS evidence

CLI HTTPS verification uses a controlled test CA and local HTTPS endpoint.

Required variants:

```text
trusted CA + matching hostname
    -> success

untrusted CA
    -> transport failure

hostname mismatch
    -> transport failure

insecure bypass option
    -> absent from parser/help/public contract
```

No public external network dependency is required.

---

## 5. Machine-checkable traceability registries

M2 implementation must provide one machine-checkable registry, conceptually in:

```text
tests/test_m2_traceability.py
```

or an equivalent test-only module with the same authority.

It contains exact sets/maps for:

```text
M2_OUTCOMES
    M2-OUT-01 ... M2-OUT-16

M2_ACCEPTANCE_CRITERIA
    M2-AC-01 ... M2-AC-32

M2_EVIDENCE_BUNDLES
    M2-VER-01 ... M2-VER-32

M2_CONCURRENCY_SCENARIOS
    canonical 83-ID registry

M2_OUTCOME_TO_ACCEPTANCE
M2_ACCEPTANCE_TO_EVIDENCE
M2_EVIDENCE_TO_TARGETS
M2_PREDICATE_TO_SCENARIOS
PUBLIC_HTTP_OPERATIONS
CLI_REMOTE_OPERATION_COVERAGE
NEGATIVE_SURFACE_CONTRACT
```

Machine checks require:

```text
exact identifier census
no missing or extra key
every mapped target exists
every target name is unique within its declared role
every predicate has scenario coverage
every non-trivial scenario has a recipe and target
every public business HTTP operation has one CLI mapping
no acceptance bundle is empty
```

The registry should be inspected statically rather than importing and starting the application merely to discover test names.

Concrete test function names may change, but stable contract/evidence/scenario identifiers may not be silently renamed or deleted.

---

## 6. Stable acceptance-evidence bundles

Every contract acceptance criterion owns exactly one stable bundle:

```text
M2-AC-xx -> M2-VER-xx
```

A bundle may require several layers and several concrete targets. It passes only when all required parts pass.

### M2-VER-01 — Initial Definition version

Layers:

```text
T0 + T1 + T2 + T4
```

Required evidence:

```text
stable Definition + complete Resolution set + RDV v1 created atomically
v1 = DRAFT, revision = 1
initial declarations equal canonical complete candidate
omitted declarations mean exact empty schema
default_version = null
response contains Definition and exact version
no capability before first PUBLISHED RDV
forced child/version failure leaves no partial aggregate
```

### M2-VER-02 — DRAFT generation lifecycle

Layers:

```text
T0 + T1 + T2 + T3 + T4
```

Required evidence:

```text
CREATE_NEXT clones exact PUBLISHED/DEPRECATED source
new version allocation uses fresh max(existing)+1
REVISE is complete semantic replacement and increments once
PUBLISH/DELETE_DRAFT consume exact expected generation
stale revision, lifecycle conflict and second-delete outcomes are exact
no mixed declaration generation
```

Concurrency:

```text
ROW-18
ROW-19
ROW-20
ATOMIC-05
```

### M2-VER-03 — Publication, default and deprecation

Layers:

```text
T0 + T1 + T2 + T3 + T4
```

Required evidence:

```text
only admissible DRAFT publishes
first serial publication establishes missing default
later publication preserves existing default
SET_DEFAULT accepts exact same-Definition PUBLISHED target
CLEAR_DEFAULT yields null
current default cannot deprecate
deprecation is irreversible and revision-stable
no latest/highest fallback
```

Concurrency:

```text
ROW-21
ROW-23
ROW-25
```

### M2-VER-04 — Property declaration semantics

Layers:

```text
T0 + T1 + T2 + T3 + T4 + T6
```

Required evidence:

```text
exact DTV pin materialization for explicit/default selection
optional and non-nullable present values
SCALAR/LIST structural rules
unique name and position
canonical property-name and PrimitiveType behavior
historical name/DataType-lineage continuity
SCALAR -> LIST allowed
LIST -> SCALAR rejected
remove/re-add preserves historical semantic identity
differential physical replacement preserves complete semantic replacement
```

Concurrency/lifetime:

```text
ROW-22
ROW-23
ROW-24
REF-07
REF-09
```

### M2-VER-05 — Model-plane reads and capabilities

Layers:

```text
T2 + T4
```

Required evidence:

```text
Definition GET/list returns stable aggregate + default and no inline versions
exact RDV GET returns declarations by position
version list is version-ascending with exact status/cursor binding
capability absent with only DRAFT/DEPRECATED versions
capability present with at least one PUBLISHED version
null default remains observable and does not remove explicit capability
one capability item per Resolution
one coherent read snapshot and corruption-to-internal_error boundary
```

### M2-VER-06 — New factual Relationship creation

Layers:

```text
T0 + T1 + T2 + T3 + T4
```

Required evidence:

```text
explicit and implicit exact RDV selection
PUBLISHED admission through commit
canonical complete initial properties
exact persisted pin
unchanged delivered factual identity and deterministic complete closure
201 + exact Location + complete projection
complete CREATED event set
endpoint/Definition lifetime arbitration
```

Concurrency:

```text
ROW-30
REF-03
REF-04
```

### M2-VER-07 — Duplicate factual creation

Layers:

```text
T1 + T2 + T3 + T4
```

Required evidence:

```text
current semantic fact -> 409 relationship_fact_conflict
bounded current relationship_id detail
no property/pin mutation of current owner
no loser header, closure row or event
equivalent and partially overlapping candidate closures
winner-current and winner-disappeared fresh classification
```

Concurrency:

```text
ARB-05
ARB-07
ARB-08
ATOMIC-02
```

### M2-VER-08 — Relationship DATA_CHANGE

Layers:

```text
T0 + T1 + T2 + T3 + T4 + T6
```

Required evidence:

```text
non-empty unique SET/REMOVE operation set
fresh complete-state derivation
whole canonical JSONB replacement only on real change
pin and closure unchanged
SET-same and REMOVE-absent no-op
no-op writes no UPDATE and no event
real change emits complete event set
```

Concurrency/atomicity:

```text
ROW-26
ATOMIC-06
```

### M2-VER-09 — Relationship SCHEMA_CHANGE

Layers:

```text
T0 + T1 + T2 + T3 + T4 + T6
```

Required evidence:

```text
explicit exact same-Definition forward target
target PUBLISHED through commit
direct source-to-target migration
compatible preservation and target recanonicalization
SCALAR -> LIST widening
new optional absent, source-only removed
incompatibility -> schema_change_blocked and unchanged source
pin + properties one-row atomic update
closure unchanged
event emitted even with equal property map
```

Concurrency/lifetime/atomicity:

```text
ROW-27
ROW-28
ROW-30
REF-10
ATOMIC-07
```

### M2-VER-10 — Relationship DELETE

Layers:

```text
T1 + T2 + T3 + T4
```

Required evidence:

```text
exact current UUID -> 204, header/closure removal and one event set
absent UUID -> 404 and no event
same-ID concurrent delete -> one 204 + one 404
late DELETE(X) never removes recreated Y
forced event failure rolls back fact and closure
```

Concurrency:

```text
ARB-06
ARB-07
ROW-29
ATOMIC-03
```

### M2-VER-11 — Relationship read coherence and corruption boundary

Layers:

```text
T2 + T3 + T4
```

Required evidence:

```text
GET and Object-relative pages see complete before or complete after
no mixed pin/properties/header/closure generation
REPEATABLE READ READ ONLY is used for multi-statement aggregate validation
one corrupt fact fails the complete aggregate/page
no fallback, repair or partial output
cursor identity excludes mutable pin/properties
```

Deterministic read cuts cover DATA_CHANGE, SCHEMA_CHANGE and DELETE commits.

### M2-VER-12 — Exact lifecycle event shapes

Layers:

```text
T0 + T2 + T4
```

Required evidence:

```text
sole M2 discriminated codec
exact factual snapshot keys
CREATED / DATA_CHANGE / SCHEMA_CHANGE / DELETED nullability
same-version/different-properties DATA_CHANGE rule
forward-version SCHEMA_CHANGE rule
invalid persisted transition fails whole page
```

### M2-VER-13 — Semantic-view fan-out

Layers:

```text
T0 + T2 + T4
```

Required evidence:

```text
one event per distinct Object-relative semantic view
non-symmetric ordinary fact
symmetric distinct endpoints
symmetric self-loop
inheritance-overlap raw-row deduplication
deterministic view order
```

### M2-VER-14 — Event-set atomicity and historical independence

Layers:

```text
T2 + T3 + T4
```

Required evidence:

```text
CREATE / DATA_CHANGE / SCHEMA_CHANGE / DELETE failure injection
current transition and complete event set commit or roll back together
no partial batch
historical decoder performs no live model lookup
history remains readable after current Relationship/Definition/RDV/DTV/Object deletion
global history remains available; Object-specific route retains current-target semantics
```

Concurrency/atomicity:

```text
ATOMIC-02
ATOMIC-03
ATOMIC-06
ATOMIC-07
```

### M2-VER-15 — DRAFT lost-update prevention

Layers:

```text
T3
```

Required evidence:

```text
same-generation REVISE/REVISE
REVISE/PUBLISH
PUBLISH/DELETE_DRAFT
fresh generation/lifecycle result
no hybrid candidate
```

Concurrency:

```text
ROW-03
ROW-04
ROW-20
ATOMIC-01
ATOMIC-05
```

### M2-VER-16 — Model admission stability

Layers:

```text
T2 + T3
```

Required evidence:

```text
default validity through commit
explicit/implicit exact admission
publisher/deprecator rendezvous
active-consumer removal semantics
VH historical recertification
no PUBLISHED consumer with non-PUBLISHED direct dependency
no new fact bound to a target that lost PUBLISHED
```

Concurrency:

```text
ROW-07 ... ROW-10
ROW-21 ... ROW-25
ROW-30
```

### M2-VER-17 — Concurrent factual CREATE

Layers:

```text
T3
```

Required evidence:

```text
at most one factual identity
one complete closure
one complete creation event set
all losing physical work rolled back
winner current -> relationship_fact_conflict
winner disappeared -> bounded fresh-UoW restart
no supported 40P01
```

Concurrency:

```text
ARB-05
ARB-07
ARB-08
ATOMIC-02
PLAN-05
```

### M2-VER-18 — Concurrent factual mutations and deletion

Layers:

```text
T3
```

Required evidence:

```text
DATA_CHANGE/DATA_CHANGE
DATA_CHANGE/SCHEMA_CHANGE
SCHEMA_CHANGE/SCHEMA_CHANGE
DATA_CHANGE/DELETE
SCHEMA_CHANGE/DELETE
DELETE/DELETE
fresh-state serial explanation
204/404 exact delete outcome
no supported 40P01
```

Concurrency:

```text
ROW-26
ROW-27
ROW-28
ROW-29
ARB-06
```

### M2-VER-19 — Coherent historical metadata

Layers:

```text
T3 + T4
```

Required evidence:

```text
all real Relationship transition families
Object rename races
Resolution rename races
independent endpoint rename combinations
one authoritative metadata statement
all event rows share one committed observation
required rename/create progress remains possible
```

Concurrency:

```text
SNAP-01 ... SNAP-05
PAR-01
PAR-02
PAR-08
```

### M2-VER-20 — Fresh durable schema realization

Layers:

```text
T2 + T5 + T10
```

Required evidence:

```text
empty PostgreSQL -> unique root head
exactly 15 authoritative tables
exact columns/types
named PK/UNIQUE/CHECK/FK and delete actions
final lifecycle vocabulary
final explicit indexes, partial predicates and INCLUDE columns
negative GIN/expression/default/duplicate index contract
one Alembic head
compare_metadata == []
migration imports no mutable application metadata
```

### M2-VER-21 — Baseline downgrade and repeatability

Layers:

```text
T5
```

Required evidence:

```text
head -> base removes all and only NETAUTO structures
external sentinel survives
base -> head -> base -> head reproduces exact schema
failure rollback leaves base without partial schema
no old M1 revision/stamp/in-place path is accepted or tested as supported
```

### M2-VER-22 — Exact startup revision gate

Layers:

```text
T2 + T5 + T9
```

Required evidence:

```text
unique shipped head discovery
actual == expected -> serving enters lifespan
unreachable / no version table / base / old / newer / unknown / multiple /
indeterminate -> startup failure
every worker performs its own guard
no business or Health endpoint serves on failure
no startup path invokes Alembic upgrade
```

### M2-VER-23 — Core readiness contract

Layers:

```text
T1 + T2 + T4 + T9
```

Required evidence:

```text
healthy app+DB -> 200 complete body
DB error -> 503 complete body
dedicated two-second timeout -> 503 bounded body
integer execution_time_ms from monotonic elapsed measurement
safe optional messages and no sensitive/internal leakage
active PostgreSQL query
Cache-Control no-store where owned by API architecture
malformed request remains invalid_request, not readiness 503
no Alembic query or remediation
```

### M2-VER-24 — One versioned distribution

Layers:

```text
T5 + T8 + T9 + T10
```

Required evidence:

```text
one wheel contains server, netauto CLI and complete Alembic graph
one release version is observable across components
install succeeds outside Git checkout
server start, CLI invocation, explicit Alembic and unique-head discovery work
installation does not migrate
CLI invocation does not initialize server/database
server does not depend on CLI
```

### M2-VER-25 — Interactive CLI state machine

Layers:

```text
T8
```

Required evidence:

```text
initial DISCONNECTED / FORMATTED
required local command inventory
persistent REPL after local/remote errors
session history and chronological /history
Ctrl-R reverse search
Ctrl-D on empty prompt
/clear preserves state/history
no implicit endpoint/profile
```

PTY/process evidence on Linux supplements pure state-machine tests.

### M2-VER-26 — Interactive connection behavior

Layers:

```text
T4 + T8
```

Required evidence:

```text
/connect uses exactly GET /health/core
valid Health 200 -> CONNECTED
timeout, invalid body, 503 or other failure -> DISCONNECTED
failed replacement connection does not restore previous endpoint
/status disconnected -> no request
/status connected -> Health revalidation
business HTTP error preserves CONNECTED
transport failure clears connection
```

### M2-VER-27 — Non-interactive CLI contract

Layers:

```text
T8 + T9
```

Required evidence:

```text
exactly one requested command
no prompt/confirmation/missing-value interaction
no mandatory Health preflight
stdout always one structured JSON result on success and failure
stderr reserved for process diagnostics
zero/nonzero exit status
trace contains all and only actual exchanges in order
local syntax failure has empty exchange list
```

### M2-VER-28 — CLI coverage and authority boundary

Layers:

```text
T4 + T8 + T10
```

Required evidence:

```text
exact 63 business HTTP operations == exact remote CLI mapping set
/health/core covered by /connect and /status
selector zero/one/many behavior
no invented identity or ambiguity guessing
FORMATTED enrichment is GET-only, complete-or-fail
no hidden post-mutation GET
JSON trace matches real exchanges
CLI execution path imports/uses no application service, persistence or DB driver
same-release wheel CLI/server compatibility
no cross-release guarantee test is inferred
```

### M2-VER-29 — Linux operating procedure

Layers:

```text
T9 + T10
```

Required evidence:

```text
documented build/install/configure/migrate/start/stop/restart/Health sequence
dedicated clean Linux environment
database_url and pool setting defaults/validation
serving settings remain external
workers × (pool_size + max_overflow) capacity warning present
protected secret-file procedure and no DB URL in canonical command line
orderly shutdown disposes owned resources
no Git checkout required
```

The procedure is executed, not merely spell-checked, for final acceptance.

### M2-VER-30 — Trust and transport boundary

Layers:

```text
T8 + T9 + T10
```

Required evidence:

```text
no native auth/authorization/credential storage surface
no 401/403 contract introduced
deployment examples do not present unprotected universal exposure as safe
HTTP examples remain within trusted boundary
HTTPS CLI verifies certificate and hostname
no insecure/skip-verify option
database transport remains solely database_url
no server certificate lifecycle settings
no secrets or connection internals in Health/logging evidence
```

### M2-VER-31 — AS-IS regression closure

Layers:

```text
T0 ... T10 as applicable
```

Required evidence:

```text
all delivered suites remain passing or are changed only by the frozen delta allowlist
all 51 delivered concurrency scenario IDs remain represented
stable topology, Resolution identity, closure and lineage admission preserved
business failure classes and bounded envelope preserved
keyset pagination and error non-leakage preserved
exact route/error/schema differences match the M2 delta registry
no unrelated public or persistence divergence
```

### M2-VER-32 — Complete outcome traceability

Layers:

```text
T10
```

Required evidence:

```text
16/16 M2 outcomes present
32/32 acceptance criteria present
32/32 M2-VER bundles present
83/83 canonical concurrency/lock-plan scenario IDs present
21/21 safety predicates mapped
every outcome -> owner -> AC -> VER -> concrete target
every preserved AS-IS guarantee -> regression target
every public operation -> CLI mapping
every negative surface -> assertion
no orphan or unauthorized architecture requirement
no unresolved normative TBD/TODO/open point at freeze
```

---

## 7. Outcome-to-evidence coverage

| Outcome | Primary architecture owners | Acceptance / evidence bundles |
|---|---|---|
| `M2-OUT-01` | `relationship.md`, `api.md`, `persistence.md` | `M2-VER-01` ... `M2-VER-05` |
| `M2-OUT-02` | `relationship.md`, `concurrency-matrix.md`, `concurrency.md` | `M2-VER-02`, `03`, `04`, `15`, `16` |
| `M2-OUT-03` | `relationship.md`, `persistence.md`, `api.md` | `M2-VER-06`, `08`, `09`, `11` |
| `M2-OUT-04` | `relationship.md`, `api.md`, concurrency owners | `M2-VER-06` ... `M2-VER-10`, `17`, `18` |
| `M2-OUT-05` | `relationship.md`, `persistence.md` | `M2-VER-06`, `07`, `09`, `10`, `13`, `31` |
| `M2-OUT-06` | `api.md`, `persistence.md` | `M2-VER-05`, `11`, `12`, `13` |
| `M2-OUT-07` | `relationship.md`, `api.md`, `persistence.md` | `M2-VER-08` ... `M2-VER-14`, `19` |
| `M2-OUT-08` | `concurrency-matrix.md`, `concurrency.md`, `persistence.md` | `M2-VER-15` ... `M2-VER-19` |
| `M2-OUT-09` | `persistence.md` | `M2-VER-20`, `21` |
| `M2-OUT-10` | `runtime-deployment.md`, `persistence.md` | `M2-VER-22` |
| `M2-OUT-11` | `health.md`, `api.md` | `M2-VER-23` |
| `M2-OUT-12` | `cli.md`, `api.md` | `M2-VER-25` ... `M2-VER-28` |
| `M2-OUT-13` | `runtime-deployment.md`, `cli.md` | `M2-VER-24` |
| `M2-OUT-14` | `runtime-deployment.md` | `M2-VER-29` |
| `M2-OUT-15` | `runtime-deployment.md`, `cli.md` | `M2-VER-30` |
| `M2-OUT-16` | `verification.md`, all owners | `M2-VER-31`, `32`, plus every bundle |

No outcome is accepted through documentation-only assertion when observable runtime or PostgreSQL behavior is involved.

---

## 8. Canonical deterministic concurrency registry

### 8.1 Composition and census

The final M2 registry is:

```text
delivered stable scenario IDs    51
new M2 scenario IDs              32
                                ----
canonical M2 total               83
```

Family census:

```text
ROW       30
ARB        8
REF       11
GATE       7
SNAP       5
ATOMIC     7
PAR        9
PLAN       6
          --
total     83
```

The 51 delivered IDs retain their stable names and baseline assertions except for the explicit M2 delta below.

### 8.2 Modified delivered scenario obligations

```text
ARB-05
    delivered loser convergence
    -> M2 loser relationship_fact_conflict
    -> no loser mutation/event

ARB-06
    delivered same-ID delete waiter no-op success
    -> M2 waiter resource_not_found / HTTP 404

ARB-07
    retains exact-ID ABA and winner-disappearance restart
    -> current winner classifies as conflict, never successful convergence

SNAP-01
    Definition/Resolution rename variants retain CREATE/DELETE
    and add DATA_CHANGE/SCHEMA_CHANGE real transitions

SNAP-02
    Object rename variants retain CREATE/DELETE
    and add DATA_CHANGE/SCHEMA_CHANGE real transitions

ATOMIC-02
    collision rollback remains; public loser classification is M2 conflict

ATOMIC-03
    delete rollback remains; successful same-ID waiter semantics are 204/404
```

No other delivered scenario obligation changes.

### 8.3 New `ROW` scenarios

| ID | Predicates | Required obligation |
|---|---|---|
| `ROW-18` | `VS` | Same-Definition `RD.CN × RD.CN` allocates serially distinct versions from a fresh version set. |
| `ROW-19` | `VS` | `RD.CN` racing with relevant `RD.DD` or source `RD.P` re-evaluates max/source eligibility after wait. |
| `ROW-20` | `DG + LS` | Same exact RDV generation `REVISE/PUBLISH/DELETE_DRAFT` has one valid generation consumer and exact stale/lifecycle/absence loser. |
| `ROW-21` | `DV + LS` | RD publication/default/set/clear/deprecate races preserve null-or-PUBLISHED same-Definition default. |
| `ROW-22` | `VH` | Distinct ObjectTemplateVersion publications re-certify member history; no non-serial published history commits. |
| `ROW-23` | `VH (+ DV)` | Distinct RDV publications re-certify property history and first-default policy serially. |
| `ROW-24` | `BA + DV` | RD CREATE/REVISE explicit or default DTV binding stabilizes the selected target and materializes one coherent exact pin. |
| `ROW-25` | `AM` | RDV PUBLISH and DTV DEPRECATE rendezvous; active consumer removal variants permit success or conservative conflict. |
| `ROW-26` | `RS` | `REL.DC × REL.DC` uses fresh properties; no lost update and a waiter may become a semantic no-op. |
| `ROW-27` | `RS` | `REL.DC × REL.SC` produces a serial factual history under the fresh pin/state. |
| `ROW-28` | `RS + BA` | `REL.SC × REL.SC` re-evaluates source and exact target; only valid forward transitions commit. |
| `ROW-29` | `RS` | `REL.DC/REL.SC × REL.DEL` yields mutation-then-delete or delete-then-not-found with matching events. |
| `ROW-30` | `BA + DV` | Explicit/implicit `REL.C` and `REL.SC` arbitrate correctly with RDV publish/deprecate/default changes. |

Primary recipe:

```text
ROW-18 ... ROW-30 -> REC-LOCK
```

`ROW-22/23` additionally assert historical re-certification after wake-up.

### 8.4 New arbitration scenario

| ID | Predicates | Required obligation |
|---|---|---|
| `ARB-08` | `RF` | Non-equivalent candidate closures sharing any exact runtime-view key commit at most one complete fact; loser rolls back and reports the current owner conflict. |

Recipe:

```text
REC-UNIQUE + REC-ROLLBACK
```

### 8.5 New reference-lifetime scenarios

| ID | Predicates | Required obligation |
|---|---|---|
| `REF-07` | `RL` | `RD.CN` cloned DTV references versus DataType root delete, both winner orders. |
| `REF-08` | `RL` | `OT.CN` cloned parent/component/DTV references versus target root delete, both winner orders. |
| `REF-09` | `RL` | Differential OT/RDV declaration replacement or reinsertion versus target delete; no transient gap, dangling reference or deadlock. |
| `REF-10` | `RL` or realization-critical `I` | Direct owner rebind versus target root delete for OT parent, Object schema and Relationship schema, both winner orders and no `40P01`. |
| `REF-11` | `RL` + physical gate | Mutually referencing model roots delete through `MODEL_ROOT_DELETE_GATE`; serially valid result, no partial aggregate and no `40P01`. |

Primary recipe:

```text
REF-07 ... REF-10 -> REC-FK
REF-11            -> REC-GATE + REC-FK
```

### 8.6 New gate scenario

| ID | Predicate | Required obligation |
|---|---|---|
| `GATE-07` | physical root-delete serialization | A `MODEL_ROOT_DELETE_GATE` waiter owns no NETAUTO row lock, acquires the gate after release and performs a fresh blocker/aggregate read. |

Recipe:

```text
REC-GATE
```

The scenario does not invent a public busy/conflict result for semantically independent root deletes.

### 8.7 New metadata scenario

| ID | Predicate | Required obligation |
|---|---|---|
| `SNAP-05` | `ES` | Real Relationship DATA_CHANGE and SCHEMA_CHANGE racing with Object and Resolution renames produce one coherent all-row metadata observation and preserve required progress. |

Recipe:

```text
REC-CUT
```

### 8.8 New atomicity scenarios

| ID | Predicates | Required obligation |
|---|---|---|
| `ATOMIC-05` | `DG` | RDV differential declaration failure rolls back revision and complete child generation. |
| `ATOMIC-06` | `RS` | Forced Relationship DATA_CHANGE event failure leaves exact pin/properties/closure unchanged and no new event. |
| `ATOMIC-07` | `RS` | Forced Relationship SCHEMA_CHANGE event failure rolls back exact pin and properties and writes no event. |

Recipe:

```text
REC-ROLLBACK
```

### 8.9 New parallelism scenarios

| ID | Required obligation |
|---|---|
| `PAR-08` | Definition RENAME remains compatible with RDV revise/default/deprecate and factual Relationship CREATE where architecture requires progress. |
| `PAR-09` | Distinct exact RDV deprecations and distinct DRAFT revisions make progress under compatible stable-header locks. |

Recipe:

```text
REC-PROGRESS
```

### 8.10 Lock-planner and failure scenarios

| ID | Layer/recipe | Required obligation |
|---|---|---|
| `PLAN-01` | T0/T2, `REC-PLAN` | SQL compilation proves exact KS/S/NKU/U mapping, one-table `OF`, explicit order and no NOWAIT/SKIP LOCKED. |
| `PLAN-02` | T0/T6, `REC-PLAN` | Intent coalescence, class ordering, OT ancestor ordering, header/version ordering and UUID tie-breaks are deterministic. |
| `PLAN-03` | T1/T2, `REC-RESTART` | Changed dependency set raises `LockPlanStale`, rolls back the whole attempt and starts a new UoW; no post-DML lock append. |
| `PLAN-04` | T1/T2, `REC-CLASSIFY` | Finite SQLSTATE + constraint-name registry maps known races only after rollback; unknown names become internal error. |
| `PLAN-05` | T1/T2/T3, `REC-RESTART` | Exactly four total attempts; no retry after semantic failure, `40P01` or `40001`; exact-view owner-current/disappeared paths are distinct. |
| `PLAN-06` | T0/T2/T3, `REC-PLAN` | At most one gate, gate before rows, no normal upgrade, no explicit row lock after DML and no supported row→gate edge. |

### 8.11 Predicate coverage

```text
NU  -> ARB-01
VS  -> ROW-01, ROW-02, ROW-18, ROW-19
DG  -> ROW-03, ROW-04, ROW-20, ATOMIC-01, ATOMIC-05
LS  -> ROW-04, ROW-06, ROW-20, ROW-21
DV  -> ROW-05, ROW-06, ROW-08, ROW-21, ROW-23, ROW-24, ROW-30
VH  -> ROW-22, ROW-23
BA  -> ROW-07, ROW-08, ROW-12, ROW-24, ROW-28, ROW-30
AM  -> ROW-09, ROW-10, ROW-25
RL  -> REF-01 ... REF-11
AL  -> ROW-16, ROW-17; RD variants included in ROW-16
ML  -> ROW-15
OS  -> ROW-11, ROW-12, ATOMIC-04
RS  -> ROW-26 ... ROW-29, ATOMIC-06, ATOMIC-07
PO  -> ROW-13, ROW-14
OF  -> ARB-03, ARB-04, ATOMIC-04
SO  -> ARB-02
OC  -> GATE-01, GATE-02, GATE-03, PAR-04
RC  -> GATE-04, GATE-05, GATE-06, ATOMIC-04
RF  -> ARB-05, ARB-07, ARB-08, ATOMIC-02
RA  -> ARB-06, ARB-07, ATOMIC-03
ES  -> SNAP-01 ... SNAP-05, PAR-01, PAR-02, PAR-08
```

All 21 predicates have deterministic scenario coverage.

---

## 9. Deterministic harness and recipes

### 9.1 Roles

```text
CTL
    orchestration controller; never a semantic transaction

OBS
    fresh observer/introspection connection

B
    optional real PostgreSQL blocker/control transaction

T1 / T2 / optional T3
    independent semantic worker sessions/UoWs
```

### 9.2 Phase vocabulary

M2 extends the delivered phase vocabulary:

```text
UOW_STARTED
DISCOVERY_COMPLETE
LOCK_PLAN_BUILT
GATE_WAITING
GATE_ACQUIRED
ROW_LOCK_WAITING
ROW_LOCKS_ACQUIRED
PROTECTED_STATE_REREAD
LOCK_PLAN_STALE
DEPENDENCIES_STABILIZED
CANDIDATE_WRITTEN
CLOSURE_WRITTEN
METADATA_SNAPSHOT_CAPTURED
EVENT_SET_WRITTEN
CONSTRAINT_ARBITRATED
BEFORE_COMMIT
COMMITTED
ROLLED_BACK
UOW_RESTARTED
```

A test-only interceptor may pause/observe a named phase only when no canonical real PostgreSQL construction is practical. It may not:

```text
change candidate data
issue semantic SQL
acquire another production lock
alter isolation
commit/rollback
change failure mapping
select a different production path
use sleep as ordering authority
```

### 9.3 Preserved recipes

```text
REC-LOCK
REC-UNIQUE
REC-FK
REC-GATE
REC-CUT
REC-ROLLBACK
REC-PROGRESS
REC-ABA
```

retain their delivered meaning.

### 9.4 M2 recipes

```text
REC-PLAN
    pure/static construction and SQL compilation of LockPlan

REC-CLASSIFY
    induce or construct a finite known PostgreSQL failure,
    leave the failed transaction, then verify semantic classification

REC-RESTART
    force an approved restart cause, prove complete rollback,
    new connection/UoW, bounded attempt count and fresh derivation
```

### 9.5 Blocking and progress evidence

Required blocking is proved primarily by:

```text
pg_blocking_pids(waiter_pid)
    contains known blocker PID
```

`pg_stat_activity` and `pg_locks` provide diagnostics, not a brittle reconstructed blocker authority.

Required progress is proved by a positive production-path phase reached while the other transaction remains open.

Timeouts are hang guards only. No normative scenario is automatically rerun to hide flakiness.

### 9.6 Deadlock assertion

Every T3 worker result captures PostgreSQL SQLSTATE when present.

For every supported canonical scenario:

```text
40P01 observed by any worker
    -> scenario FAIL
    -> architecture/implementation finding
    -> no automatic retry
```

`REF-11`, `REF-10`, `PLAN-06` and the complete registry jointly protect the deadlock proof. Stress runs supplement but do not weaken this requirement.

---

## 10. Relationship functional and persistence evidence

### 10.1 Domain equivalence with Object patterns

Property/version tests must compare equivalent problems directly:

```text
DataTypeVersion / ObjectTemplateVersion / RDV
    lifecycle, default, exact pins, DRAFT generation

Object / Relationship
    canonical state, DATA_CHANGE, SCHEMA_CHANGE, DELETE
```

Equivalent cases expose equivalent outcomes unless `contract.md` names a genuine Relationship delta.

### 10.2 Current-state codec

Real PostgreSQL tests insert and read:

```text
empty properties {}
every PrimitiveType canonical carrier
SCALAR and non-empty LIST
optional empty LIST -> absence
deprecated exact RDV/DTV historical pins
```

Negative corruption fixtures cover:

```text
DRAFT factual pin
unknown property
JSON null
wrong carrier
non-canonical value
missing exact dependency
incomplete/mismatched closure
same-Definition mismatch
```

Public reads fail as `internal_error`; they never repair fixtures.

### 10.3 Lifecycle codec

Pure and persistence tests cover:

```text
exact snapshot keys
positive non-bool version
allowed scalar/list carriers
forbidden null/float/object/nested/empty-list values
four transition invariants
complete semantic-view batch
transaction_timestamp identity
deterministic ordering
```

### 10.4 Read coherence

Composite aggregate/page reads use an instrumented cut where a writer commits between individual physical reads. The delivered implementation must still expose one repeatable before/after snapshot, proving that a coherent-read UoW—not fortunate statement timing—owns consistency.

---

## 11. API evidence and finite surface closure

### 11.1 Exact operation inventory

The final expected inventory is:

```text
/api/v1/core
    41 mutation operations
    22 read operations
    63 business operations

/health/core
    1 operational operation

total
    64 public HTTP operations
```

Generated OpenAPI and router inspection must equal the frozen set exactly. Minimum-count assertions are forbidden.

### 11.2 Strict input matrix

For every new/modified route:

```text
unknown body field
unknown/repeated query parameter
malformed UUID
bool-as-int
zero/negative version/revision/position
explicit null where omission-only
body on no-body command
invalid closed vocabulary
```

maps to the finite public contract.

### 11.3 Failure catalog

The exact finite public error-code/status registry remains machine checked.

Every failure test asserts:

```text
status
code
message safety
bounded semantic details
absence of SQL/constraint/table/column/stack content
```

Unknown application code/class pairs and unknown constraint classifications become `internal_error`.

### 11.4 Negative public surface

Explicitly absent:

```text
generic PUT/PATCH
bulk/batch transaction endpoint
generic health aggregate
standalone RelationshipResolution CRUD
standalone property declaration CRUD
property-value search
event-set resource
auth/login/token routes
schema migration endpoint
```

---

## 12. Schema, Alembic and startup evidence

### 12.1 Live schema contract

Introspection verifies exact:

```text
table set
column names/types/nullability/defaults
PK/UNIQUE/CHECK/FK names and definitions
CASCADE/RESTRICT actions
index keys/order/predicate/INCLUDE
```

Constraint-owned indexes are not duplicated.

### 12.2 Negative index contract

Absent:

```text
GIN on objects/relationships properties
GIN/expression indexes on lifecycle snapshots
standalone default_version indexes
duplicate PUBLISHED-only indexes
second factual identity index
event-set grouping index
```

### 12.3 Alembic graph contract

The installed release has:

```text
one root revision
one head
no executable disposable M1 development revisions
self-contained migration code
```

Tests execute the graph from the installed package resources.

### 12.4 Startup guard process evidence

A process/lifespan harness distinguishes:

```text
application factory construction
lifespan startup
serving readiness
```

Failure before serving is proved by:

```text
lifespan/startup failure
no successful request to business or Health route
no migration DDL observed
```

For multi-worker evidence, each worker independently records/checks the expected/actual revision without making process-local state a cross-worker authority.

---

## 13. Health evidence

Health application tests separate:

```text
app operation reached
PostgreSQL query result
timeout wrapper
HTTP mapping
```

A real PostgreSQL blocker or controlled query path proves the dedicated two-second timeout independently of normal pool timeout.

Safe-message tests use representative:

```text
connection refused
authentication/driver error
query timeout
pool acquisition failure
```

and assert no raw detail escapes.

Health success/failure always returns the complete bounded DTO. It never queries Alembic state and never mutates the database.

---

## 14. CLI evidence

### 14.1 Pure parser and state machine

Pure tests cover:

```text
local vs remote namespace
singular lowercase/kebab tokens
one optional positional selector
parameter=value
inline JSON
@file JSON
duplicate/unknown/missing parameters
URL normalization and validation
connection/output/history transitions
```

### 14.2 HTTP authority

A transport recorder proves every CLI command issues only public HTTP requests.

Static dependency checks reject production CLI imports from:

```text
netauto.application
netauto.persistence
PostgreSQL driver modules
```

except neutral DTO/value helpers explicitly owned by the CLI architecture.

### 14.3 Selector resolution

For DataType/ObjectTemplate qualified names and Object name/UUID selectors:

```text
zero matches
one match
multiple matches
exact UUID
```

are deterministic. RelationshipDefinition and factual Relationship remain UUID-selected.

### 14.4 FORMATTED and JSON

FORMATTED read enrichment:

```text
GET-only
actual exchange order recorded
complete-or-fail
no partial complete-looking representation
```

Mutations perform no hidden post-mutation GET.

JSON output records exactly the exchanges that occurred; explicit debug output is not conflated with safe operational logging.

### 14.5 Terminal/process

Linux PTY/process evidence covers:

```text
prompt persistence
Ctrl-R
Ctrl-D
stdout/stderr
exit status
one-shot non-interactive behavior
```

Toolkit-specific unit tests may supplement but never replace process-visible behavior.

---

## 15. Packaging, runtime and trust-boundary evidence

### 15.1 Wheel inspection

The built wheel is inspected for:

```text
netauto package
server factory/runtime modules
netauto console entrypoint
Alembic environment and revision graph
release version metadata
required package resources
```

It must not depend on repository-relative paths.

### 15.2 Clean installation

A clean environment outside the checkout proves:

```text
install wheel
invoke netauto help/REPL/non-interactive path
discover Alembic head
apply explicit migration
start server
query Health
stop and restart
```

### 15.3 Configuration

Tests cover defaults and invalid values for:

```text
pool_size
max_overflow
pool_timeout
pool_recycle
pool_pre_ping
log level
database_url source
```

Serving host/port/workers remain deployment inputs, not duplicated application settings.

### 15.4 Secret and documentation policy

T10 checks the canonical operating documentation for:

```text
protected local secret file
dedicated user
no secret on command line
no repository secret
trusted-boundary warning
external TLS requirement for untrusted segments
worker/pool capacity multiplication
explicit migration before start
```

A manual/documented procedure is not accepted solely through prose: T9 executes the material steps.

---

## 16. AS-IS regression and delta allowlist

The final regression comparison uses an explicit allowlist containing only the frozen M2 deltas:

```text
Definition CREATE includes v1 DRAFT
capability requires one PUBLISHED RDV
Relationship CREATE request/projection exact pin + properties
duplicate Relationship CREATE -> conflict
missing Relationship DELETE -> not found
Relationship lifecycle before/after + new kinds
startup exact-revision guard
fresh durable Alembic root baseline
new Health / CLI / runtime surfaces
```

Any other difference in:

```text
route
status/error
DTO field
semantic outcome
table/constraint/index
concurrency predicate
blocking/progress contract
```

is a regression or requires formal contract reopening.

Existing AS-IS tests may be refactored, but their stable scenario and guarantee coverage cannot disappear.

---

## 17. Contract quality-gate verification

`M2-VER-32` includes machine checks for all ten contract quality gates.

```text
M2-CQG-01
    candidate capability classification exact and closed

M2-CQG-02
    no normative TBD/TODO/open contract point

M2-CQG-03
    AS-IS guarantee/delta allowlist closure

M2-CQG-04
    capability -> objective -> outcome -> AC -> VER coverage

M2-CQG-05
    dependency graph and authority direction consistency

M2-CQG-06
    Scope / Non-goal / trust-boundary consistency

M2-CQG-07
    cross-cutting atomicity/canonicalization/coherence obligations covered

M2-CQG-08
    deferred decisions remain architecture/implementation-only

M2-CQG-09
    canonical vocabulary and stable identifiers

M2-CQG-10
    frozen-change control and reopening rules present
```

These checks validate the frozen contract; they do not reopen it.

---

## 18. Final acceptance evidence record

The final record contains at least:

```text
candidate commit SHA
release version
wheel filename and cryptographic hash
Python / uv / PostgreSQL versions
locked-environment confirmation
exact commands and exit statuses
test and scenario ledger
M2-VER-01 ... M2-VER-32 status
83-scenario status
21-predicate coverage result
schema drift result
OpenAPI / CLI coverage result
installed-wheel procedure result
known skipped/non-applicable supplementary tests
open findings
final acceptance decision
```

Normative scenarios may not be marked non-applicable merely because implementation chose another internal layout. When the architecture changes, the owning document and scenario registry must be updated before acceptance.

Coverage percentage and raw test count are diagnostics; they cannot override a missing semantic bundle.

---

## 19. Architecture closure status

Verification-design closure:

```text
verification gate separation                  CLOSED
T0 ... T10 layer model                       CLOSED
environment/isolation policy                 CLOSED
32 acceptance evidence bundles               CLOSED
16 outcome coverage map                      CLOSED
83 canonical scenario registry               CLOSED
21 predicate coverage                        CLOSED
lock-planner/SQLSTATE/restart evidence        CLOSED
API/schema/startup/Health evidence design     CLOSED
CLI/package/Linux/trust evidence design       CLOSED
AS-IS regression and negative-surface design CLOSED
final acceptance record contract             CLOSED
governance circularity                       CLOSED
dependent-owner implementation-hook review          CLOSED
```

No verification-design decision remains open inside this owner.

This document remains `NOT FROZEN` until:

- every M2 architecture owner confirms its outcomes and acceptance criteria are correctly represented;
- the complete architecture set passes contract, AS-IS, authority, terminology and normative-hygiene consistency closure.

Executed M2 implementation evidence remains intentionally pending until implementation is authorized. It is required by implementation-slice completion and final delivery, not by architecture design authorization.
