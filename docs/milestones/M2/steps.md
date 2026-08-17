# M2 — Implementation Steps

**Status:** FINAL / FROZEN

**Authority:** NORMATIVE M2 IMPLEMENTATION DECOMPOSITION — FINAL / FROZEN

## 1. Purpose and authority

This document decomposes the frozen M2 contract and architecture into implementation slices.

It does not introduce or reinterpret domain semantics, public contracts, persistence guarantees, concurrency guarantees, technology choices or verification obligations. Implementation authority is composed from:

```text
current delivered AS-IS
    -> docs/architecture/

M2 contract
    -> docs/milestones/M2/contract.md
    -> FINAL / FROZEN

M2 architecture
    -> docs/milestones/M2/architecture/
    -> FINAL / FROZEN

project-wide technologies
    -> docs/general/technology_baseline.md
    -> STACK-01 ... STACK-10 RATIFIED

this document, after freeze
    -> implementation order, slice scope, evidence assignment
       and completion conditions
```

The M2 `wip/` directory is historical discovery and review evidence only. No slice may use a WIP file as its normative owner.

The implementation traceability chain is:

```text
M2-OUT
    -> M2-AC
    -> M2-VER
    -> frozen architecture owner
    -> M2-Snn
    -> implementation mechanism
    -> executed evidence
```

## 2. Global implementation rules

### 2.1 Mandatory pre-flight

Before starting or resuming any slice, the implementer must re-read the repository and verify:

```text
root README identifies active cycle M2 on branch M2
contract.md remains FINAL / FROZEN
architecture/README.md remains FINAL / FROZEN
steps.md remains FINAL / FROZEN
status.md authorizes the exact slice
all slice dependencies are reviewer-owned COMPLETED
all owning architecture documents are still frozen
no relevant authority is PARTIALLY REOPENED
required M2-VER bundles and canonical scenarios are known
required PostgreSQL/runtime infrastructure is available
```

A contradiction, missing decision or reopened authority puts the affected work in `STOP`. It is never resolved by choosing a convenient implementation.

### 2.2 Vertical completion

Except for `M2-S00`, which is the single explicit cross-cutting foundation slice, every slice is vertically complete for its bounded capability.

Where applicable, a slice must leave mutually coherent:

```text
domain semantics
application command/query behavior
one semantic operation / one UoW
persistence and relational authority
PostgreSQL concurrency realization
HTTP/CLI boundary
failure mapping
read and lifecycle projections
deterministic evidence
```

A table, DTO, helper, route, test scaffold or command registry alone does not satisfy a slice.

### 2.3 Preserve the delivered baseline

Every delivered AS-IS guarantee remains mandatory unless the frozen M2 delta register explicitly changes it.

Implementation must not:

```text
restore removed compatibility layers
add an in-place M1 -> M2 migration
retain the disposable M1 Alembic chain
invent a second persistence or semantic authority
weaken strict request or finite-error behavior
replace deterministic PostgreSQL evidence with mocks or stress
add auth, native server TLS, orchestration or observability scope
derive requirements from M2/wip
```

### 2.4 Transaction and concurrency discipline

Every affected mutation must implement the frozen M2 plan:

```text
complete LockPlan before current-state DML
at most one transaction advisory gate
gate before row locks
coalesced sufficient initial row-lock modes
canonical row ordering
fresh protected reread after every wait
no normal lock upgrade
no post-DML lock-plan expansion
deterministic child / closure / event ordering
one complete UoW commit or rollback
bounded whole-UoW restart only for approved causes
no automatic retry of SQLSTATE 40P01 or 40001
```

A supported-path `40P01` is a blocking implementation finding.

### 2.5 Verification discipline

Each slice implements and executes its assigned evidence targets.

Rules:

```text
real PostgreSQL for T2/T3/T5 claims
no SQLite fallback
no sleep-based correctness orchestration
timeouts are hang guards only
no unexplained SKIP/XFAIL for normative evidence
no generic flaky-test retry
all previously passing AS-IS regressions remain passing
Ruff and Pyright strict remain green
```

The smallest focused evidence runs first; the slice then runs every cross-boundary gate required by its completion condition.

### 2.6 Candidate and reviewer ownership

The implementer produces a candidate and reports verified facts.

The reviewer owns:

```text
REVIEW CHANGES REQUIRED
COMPLETED
final acceptance approval
DELIVERED
```

A review correction remains inside the same slice. No additional slice is created merely to address findings on the current candidate.

### 2.7 Documentation and evidence

Implementation may update:

```text
status.md
active execution aids
machine-checkable traceability registries
candidate/final evidence records
operator documentation assigned by a slice
```

It must not change frozen contract or architecture to fit the code. A genuine design defect requires formal reopen, propagation, consistency closure and re-freeze.

Commit-specific evidence belongs under:

```text
docs/milestones/M2/evidence/
```

and does not become a competing semantic authority.

## 3. Slice dependency graph

M2 uses one intentionally linear implementation path:

```text
M2-S00
    -> M2-S01
    -> M2-S02
    -> M2-S03
    -> M2-S04
    -> M2-S05
    -> M2-S06
    -> M2-S07
    -> M2-S08
    -> M2-S09
```

The order prevents a later public/runtime surface from being implemented against temporary schema, transaction or transport assumptions.

```text
M2-S00
    cross-cutting transaction foundation

M2-S01 ... M2-S08
    implementation slices

M2-S09
    dedicated final acceptance and delivery-candidate gate
```

Only the exact slice marked `READY` or `IN PROGRESS` by `status.md` is authorized.

## 4. Slice registry

| Slice | Title | Depends on | Primary evidence |
|---|---|---|---|
| `M2-S00` | LockPlan and AS-IS transaction-hardening foundation | none | supporting foundation for concurrency and regression bundles |
| `M2-S01` | Durable relational baseline and versioned Relationship model plane | `M2-S00` | `M2-VER-01..07`, `10`, `20`, `21` |
| `M2-S02` | Factual Relationship mutations, lifecycle and coherent reads | `M2-S01` | `M2-VER-08`, `09`, `11..14` |
| `M2-S03` | Complete kernel concurrency and deadlock-evidence closure | `M2-S02` | `M2-VER-15..19` |
| `M2-S04` | Runtime settings, startup revision guard and Core Health | `M2-S03` | `M2-VER-22`, `23` |
| `M2-S05` | Official CLI HTTP core and non-interactive mode | `M2-S04` | `M2-VER-27` |
| `M2-S06` | Official CLI interactive REPL and formatted experience | `M2-S05` | `M2-VER-25`, `26`, `28` |
| `M2-S07` | Versioned wheel, installed Alembic and Linux operating baseline | `M2-S06` | `M2-VER-24`, `29`, `30` |
| `M2-S08` | Integrated regression, traceability and negative-surface closure | `M2-S07` | `M2-VER-31`, `32` |
| `M2-S09` | Full M2 acceptance and delivery-candidate gate | `M2-S08` and all prior slices reviewer-owned `COMPLETED` | all `M2-VER-01..32` re-executed and accepted |

Each `M2-VER-*` bundle has exactly one primary implementation slice. Supporting verification may be implemented earlier or re-executed later without changing primary ownership.

---

## M2-S00 — LockPlan and AS-IS transaction-hardening foundation

### Objective

Introduce the cross-cutting PostgreSQL transaction foundation required by the frozen 41-mutation M2 design, while preserving the delivered M1 public behavior.

This is the only foundation exception to vertical-slice preference. It introduces no new M2 business route, domain operation or schema capability.

### Dependencies

```text
none
```

### Normative authorities

```text
docs/architecture/concurrency.md
docs/architecture/concurrency-matrix.md
docs/architecture/persistence.md
docs/architecture/verification-concurrency-registry.md

docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/concurrency-matrix.md
docs/milestones/M2/architecture/concurrency.md
docs/milestones/M2/architecture/verification.md

docs/general/technology_baseline.md
```

### Deliverables

Implement one centralized transaction lock-planning boundary that owns:

```text
AdvisoryGate
RowLockMode
RowLockClass
RowLockKey
RowLockIntent
LockPlan
LockPlanStale
canonical intent coalescence and ordering
gate-first acquisition
row-lock SQL construction
finite PostgreSQL failure classification
bounded whole-UoW restart
```

Realize exactly the three transaction-scoped advisory gates:

```text
OWNERSHIP_GRAPH_WRITE_GATE
RELATIONSHIP_DEFINITION_CONFLICT_GATE
MODEL_ROOT_DELETE_GATE
```

Realize the four PostgreSQL row-lock modes and their exact SQLAlchemy compilation:

```text
FOR KEY SHARE
FOR SHARE
FOR NO KEY UPDATE
FOR UPDATE
```

Retrofit the delivered 32 mutation paths to the frozen M2 physical discipline, including:

```text
stable header participation in exact-version mutations
target-before-existing-owner direct FK rebind
target-before-child DML for inserted/reinserted references
differential ObjectTemplate declaration replacement
CREATE_NEXT cloned-reference lifetime holds
model-root delete serialization
Relationship endpoint lifetime holds before closure writes
Definition RENAME gate-first + header KEY SHARE
ownership edge addition gate-first
deterministic declaration / closure / event order
non-locking reverse active-consumer scans
```

Implement the bounded attempt policy:

```text
MAX_SEMANTIC_UOW_ATTEMPTS = 4

automatic whole-UoW restart only for:
    LOCK_PLAN_STALE
    exact-view collision whose current owner disappeared

no retry for:
    semantic failure
    40P01
    40001
```

No new M2 schema, RDV surface, Health route or CLI command is added in this slice.

### Required verification

At minimum:

```text
PLAN-01 ... PLAN-06
```

including:

```text
lock-mode SQL compilation
coalescence and canonical sort properties
ancestor/header/version/UUID ordering
gate-before-row and at-most-one-gate assertions
no normal lock upgrade
no post-DML lock append
LockPlanStale complete rollback + fresh UoW
finite constraint/SQLSTATE classifier
four-attempt restart budget
no retry of 40P01 / 40001
```

Run affected delivered concurrency and transaction regressions, especially:

```text
ownership gate scenarios
Definition conflict-gate scenarios
root/reference lifetime scenarios
Relationship CREATE rename-progress scenarios
aggregate rollback scenarios
```

Run Ruff format/check, Pyright strict and all non-PostgreSQL plus affected real-PostgreSQL suites.

### Completion condition

A reviewer may mark `M2-S00` `COMPLETED` only when:

```text
every delivered mutation uses or is proven compatible with the central planner
all required hardening is present
PLAN-01 ... PLAN-06 pass
affected delivered concurrency scenarios pass
no supported scenario produces 40P01
no public M1 behavior changed outside the frozen M2 delta
no M2 business capability has been prematurely exposed
```

Primary outcome support:

```text
M2-OUT-08
M2-OUT-16
```

---

## M2-S01 — Durable relational baseline and versioned Relationship model plane

### Objective

Replace the disposable development schema with the first durable 15-table baseline and deliver the complete versioned `RelationshipDefinition` model plane, including the exact factual Relationship pin/properties changes required for CREATE/GET/DELETE.

### Dependencies

```text
M2-S00 COMPLETED
```

### Normative authorities

```text
docs/architecture/relationship.md
docs/architecture/persistence.md
docs/architecture/api.md

docs/milestones/M2/architecture/relationship.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/concurrency-matrix.md
docs/milestones/M2/architecture/concurrency.md
docs/milestones/M2/architecture/verification.md
docs/milestones/M2/architecture/provenance.md
```

### Deliverables

#### Durable relational baseline

Implement final SQLAlchemy metadata for exactly 15 authoritative tables, including:

```text
relationship_definition_versions
relationship_definition_properties
relationship_definitions.default_version
relationships.relationship_definition_version
relationships.properties
final lifecycle vocabulary/checks
final PK / UNIQUE / CHECK / FK / CASCADE / RESTRICT
final explicit and partial indexes
negative index contract
```

Replace the disposable migration chain with one installed-package root revision:

```text
one base
one head
down_revision = None
fresh empty database -> complete M2 schema
```

Remove the old development revision files from the shipped graph. Do not implement M1 backfill, stamp or in-place upgrade.

Implement:

```text
base -> head
head -> base
base -> head -> base -> head
metadata drift == []
external sentinel preservation
```

#### RelationshipDefinitionVersion domain/application model

Implement:

```text
RDV exact composite identity
DRAFT / PUBLISHED / DEPRECATED
revision and expected_revision
CREATE initial v1 DRAFT revision 1
CREATE_NEXT
REVISE complete semantic replacement
PUBLISH
SET_DEFAULT
CLEAR_DEFAULT
DEPRECATE
DELETE_DRAFT
```

Implement property declarations with:

```text
exact DataTypeVersion pins
optional-only, present values non-nullable
SCALAR / LIST
position ordering
historical semantic continuity
SCALAR -> LIST only
remove/re-add continuity
PUBLISHED active-dependency behavior
```

Implement version-history recertification and differential physical declaration replacement.

#### Public model-plane API and reads

Implement all new/changed RelationshipDefinition/RDV routes and DTOs, strict omission/null behavior, success statuses, Location, errors, version list/filter/cursor, exact version reads and stable Definition/default projections.

Update relationship capabilities:

```text
requires at least one PUBLISHED RDV
default_version exposed separately
one item per Resolution
no inline schema/version list
```

Implement uniform defensive default-pointer validation for DataType, ObjectTemplate and RelationshipDefinition coherent reads.

#### Factual Relationship baseline delta

Update existing factual Relationship CREATE/GET/DELETE to:

```text
persist and expose exact RDV pin
persist and expose canonical properties
explicit or default PUBLISHED selection
201 only for a new fact
duplicate/current fact -> relationship_fact_conflict
missing DELETE target -> resource_not_found / 404
created/deleted factual lifecycle snapshots
preserved stable factual identity and deterministic closure
```

The property state in this slice is initial/final factual state. DATA_CHANGE and SCHEMA_CHANGE are delivered in `M2-S02`.

### Required verification

Primary bundles:

```text
M2-VER-01
M2-VER-02
M2-VER-03
M2-VER-04
M2-VER-05
M2-VER-06
M2-VER-07
M2-VER-10
M2-VER-20
M2-VER-21
```

Implement and run the applicable deterministic scenarios, including:

```text
ROW-18 ... ROW-25
ROW-30 CREATE variants
ARB-05 ... ARB-08
REF-03
REF-04
REF-07
REF-09
ATOMIC-02
ATOMIC-03
ATOMIC-05
```

Verify exact schema/index positive and negative inventories, downgrade isolation, repeatability and zero drift on real PostgreSQL.

Run all affected domain, application, API, migration, property and AS-IS regression suites plus Ruff/Pyright.

### Completion condition

A reviewer may mark `M2-S01` `COMPLETED` only when:

```text
the unique root revision creates the exact final 15-table schema
old development revisions are absent from the shipped graph
RDV lifecycle/default/property behavior is complete end to end
Relationship CREATE/GET/DELETE expose exact pin/properties
duplicate CREATE and missing DELETE have exact M2 outcomes
capability/read projections are coherent and corruption-safe
all ten primary M2-VER bundles pass
all assigned scenarios pass without 40P01
no legacy migration bridge or dual decoder exists
```

Primary outcome support:

```text
M2-OUT-01
M2-OUT-02
M2-OUT-03
M2-OUT-04
M2-OUT-05
M2-OUT-06
M2-OUT-09
```

---

## M2-S02 — Factual Relationship mutations, lifecycle and coherent reads

### Objective

Complete the factual Relationship data plane with DATA_CHANGE, SCHEMA_CHANGE, unified lifecycle persistence and coherent current/history reads.

### Dependencies

```text
M2-S01 COMPLETED
```

### Normative authorities

```text
docs/architecture/object.md
docs/architecture/relationship.md
docs/architecture/persistence.md
docs/architecture/api.md

docs/milestones/M2/architecture/relationship.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/concurrency-matrix.md
docs/milestones/M2/architecture/concurrency.md
docs/milestones/M2/architecture/verification.md
```

### Deliverables

Implement `Relationship.DATA_CHANGE`:

```text
non-empty unique SET / REMOVE operations
fresh complete-state derivation
exact current RDV only
canonical complete JSONB replacement on real change
SET-same / REMOVE-absent semantic no-op
no UPDATE and no event for a no-op
pin and closure unchanged
```

Implement `Relationship.SCHEMA_CHANGE`:

```text
explicit exact same-Definition forward target
target PUBLISHED through commit
source PUBLISHED or DEPRECATED
direct source-to-target migration
preserve compatible values
SCALAR -> LIST widening
target recanonicalization
new optional property absent
source-only property removed
incompatibility -> schema_change_blocked
exact pin + properties atomic update
closure unchanged
event even when properties remain equal
```

Introduce or complete one shared lifecycle persistence boundary for all event families, with:

```text
shared historical runtime-property carrier codec
RelationshipFactualState exact shape
four Relationship event kinds
exact before/after transition validation
one coherent metadata projection statement
semantic-view deduplication
deterministic event order
complete batch insertion
no event_set_id
no live historical FK
```

Complete coherent reads:

```text
Relationship GET
Object-relative Relationship pages
Definition/default reads
exact RDV reads
lifecycle pages
```

using the required statement snapshot or `REPEATABLE READ READ ONLY` boundary. One corrupt represented aggregate/event fails the complete response with `internal_error`; no repair or partial page is allowed.

### Required verification

Primary bundles:

```text
M2-VER-08
M2-VER-09
M2-VER-11
M2-VER-12
M2-VER-13
M2-VER-14
```

Implement and run:

```text
ROW-26
ROW-27
ROW-28
ROW-29
ROW-30 SCHEMA_CHANGE variants
REF-10 Relationship rebind variants
SNAP-05
ATOMIC-06
ATOMIC-07
```

Extend fan-out evidence for:

```text
non-symmetric fact
symmetric distinct endpoints
symmetric self-loop
inheritance-overlap deduplication
```

Inject lifecycle writer failures into all four factual transitions and prove complete rollback.

Run T0/T1/T2/T3/T4/T6 targets, affected AS-IS lifecycle/read regressions and Ruff/Pyright.

### Completion condition

A reviewer may mark `M2-S02` `COMPLETED` only when:

```text
DATA_CHANGE and SCHEMA_CHANGE are complete public mutations
no-op and preserve-or-fail semantics are exact
all four Relationship event families use one rigorous codec/writer
event fan-out and metadata are coherent
current reads observe complete before or after states only
historical reads require no live model lookup
all six primary M2-VER bundles pass
all assigned scenarios pass without 40P01
```

Primary outcome support:

```text
M2-OUT-03
M2-OUT-04
M2-OUT-05
M2-OUT-06
M2-OUT-07
```

---

## M2-S03 — Complete kernel concurrency and deadlock-evidence closure

### Objective

Complete the implementation and deterministic proof of the frozen 41-mutation, 861-cell concurrency design across the entire kernel.

### Dependencies

```text
M2-S02 COMPLETED
```

### Normative authorities

```text
docs/architecture/concurrency-matrix.md
docs/architecture/concurrency.md
docs/architecture/verification-concurrency-registry.md

docs/milestones/M2/architecture/concurrency-matrix.md
docs/milestones/M2/architecture/concurrency.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/verification.md
```

### Deliverables

Complete implementation coverage for:

```text
41 / 41 mutation lock plans
21 / 21 semantic safety predicates
3 / 3 advisory gates
4 / 4 row-lock modes
one canonical row order
approved restart and failure-classification boundaries
```

Complete the deterministic test registry:

```text
51 delivered scenario IDs preserved
32 M2 scenario IDs added
83 / 83 total scenarios implemented
```

Ensure the harness supports:

```text
independent PostgreSQL sessions
stable phase/interceptor vocabulary
pg_blocking_pids() blocking proof
positive progress proof
fresh post-wait reread assertions
worker SQLSTATE capture
complete rollback observation
```

Close every required concurrency family, including:

```text
RDV version/generation/default/history races
RDV/DTV admission and active graph
clone/reference lifetime
direct rebind versus target delete
mutual model-root delete
Relationship CREATE arbitration
Relationship state mutation/delete serialization
metadata rename cuts
required parallelism
LockPlan stale/restart/classification/budget
```

### Required verification

Primary bundles:

```text
M2-VER-15
M2-VER-16
M2-VER-17
M2-VER-18
M2-VER-19
```

Execute all canonical scenarios:

```text
ROW-01 ... ROW-30
ARB-01 ... ARB-08
REF-01 ... REF-11
GATE-01 ... GATE-07
SNAP-01 ... SNAP-05
ATOMIC-01 ... ATOMIC-07
PAR-01 ... PAR-09
PLAN-01 ... PLAN-06
```

For every supported scenario:

```text
semantic result is exact
required blocking/progress is observed
complete rollback/atomicity holds
no worker returns SQLSTATE 40P01
```

Run the complete real-PostgreSQL concurrency suite and affected full regression suite, plus Ruff/Pyright.

### Completion condition

A reviewer may mark `M2-S03` `COMPLETED` only when:

```text
41 / 41 mutation plans are implemented
83 / 83 canonical scenarios are implemented and passing
21 / 21 predicates have passing deterministic evidence
every required blocking and progress assertion passes
no supported scenario observes 40P01
no correctness path relies on retrying a deadlock victim
the physical wait graph remains consistent with the frozen proof
all five primary M2-VER bundles pass
```

Primary outcome support:

```text
M2-OUT-02
M2-OUT-04
M2-OUT-08
M2-OUT-16
```

---

## M2-S04 — Runtime settings, startup revision guard and Core Health

### Objective

Deliver the frozen runtime configuration model, exact pre-serving schema compatibility guard and `/health/core` readiness capability on one worker-owned engine/pool.

### Dependencies

```text
M2-S03 COMPLETED
```

### Normative authorities

```text
docs/architecture/persistence.md
docs/architecture/api.md

docs/milestones/M2/architecture/runtime-deployment.md
docs/milestones/M2/architecture/health.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/verification.md

docs/general/technology_baseline.md
```

### Deliverables

Implement exact application settings and precedence:

```text
database_url
log_level
pool_size = 10
max_overflow = 20
pool_timeout = 5.0
pool_recycle = null
pool_pre_ping = false

constructor/test injection
    > NETAUTO_* environment
    > explicit NETAUTO_SECRETS_DIR file
    > safe defaults
```

Enforce finite pool validation and use one `AsyncEngine`/pool per worker for:

```text
business UoWs
coherent reads
startup revision inspection
Health probe
```

Implement installed-graph expected-head discovery and same-engine actual-head inspection with:

```text
one base
one shipped head
actual singleton == expected singleton
ten-second whole startup guard
no serving on mismatch/failure
no automatic migration
engine disposal on startup failure
```

Implement:

```text
GET /health/core
```

with:

```text
same engine/pool
exact SELECT 1
two-second whole-probe deadline including checkout
monotonic execution_time_ms
200 healthy
503 expected DB not-ready with complete body
safe controlled messages
Cache-Control: no-store
strict no body/query
no Alembic check/remediation
```

### Required verification

Primary bundles:

```text
M2-VER-22
M2-VER-23
```

Verify startup against:

```text
expected head
database unreachable
missing alembic_version
base
old/different/newer/unknown revision
multiple current heads
invalid installed graph
timeout
```

Verify Health with fake and real PostgreSQL probes, including deterministic pool starvation where `pool_timeout > 2` but Health returns around the dedicated two-second boundary.

Run lifespan-aware HTTP tests, real-PG integration, runtime cleanup tests, negative startup/migration path assertions, affected regressions and Ruff/Pyright.

### Completion condition

A reviewer may mark `M2-S04` `COMPLETED` only when:

```text
settings and pool behavior match the frozen inventory
one engine/pool owns all four runtime consumers
every worker refuses serving on revision mismatch
startup never migrates or repairs
Health uses exact SELECT 1 and the full two-second deadline
healthy/unhealthy/malformed/internal outcomes are exact and non-leaking
both primary M2-VER bundles pass
```

Primary outcome support:

```text
M2-OUT-10
M2-OUT-11
M2-OUT-14
M2-OUT-15
```

---

## M2-S05 — Official CLI HTTP core and non-interactive mode

### Objective

Deliver the official HTTP-only CLI core, exact static operation registry, deterministic selector/input/trace behavior and the complete non-interactive process contract.

### Dependencies

```text
M2-S04 COMPLETED
```

### Normative authorities

```text
docs/milestones/M2/architecture/cli.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/health.md
docs/milestones/M2/architecture/runtime-deployment.md
docs/milestones/M2/architecture/verification.md

docs/general/technology_baseline.md
    STACK-10
```

### Deliverables

Move/share wire DTOs through a neutral transport package that contains no FastAPI request object, application service, SQLAlchemy, Psycopg or persistence import.

Promote HTTPX to the runtime dependency set and implement one transparent async HTTP client with:

```text
verified HTTPS
hostname verification
no insecure bypass
no redirect following
no cookie persistence
no automatic retry
finite connect/pool/read/write timeouts
```

Implement one immutable registry containing exactly 63 business operations and owning:

```text
grammar
help metadata
selector traversal
HTTP dispatch
success response validation
FORMATTED renderer selection
coverage evidence
```

Implement:

```text
<resource> <operation> [selector] [parameter=value ...]
```

with:

```text
strict omission versus explicit null
inline JSON
@file.json
top-level and nested human selector resolution
zero / one / many selector outcomes
per-command lookup memoization only
no invented domain identity
```

Deliver the exact non-interactive invocation:

```text
netauto -n <endpoint-root> <resource> <operation>
    [selector] [parameter=value ...]
```

with:

```text
one command
no prompt or confirmation
no mandatory Health preflight
one structured JSON result on stdout
zero/nonzero exit status
stderr only for external process diagnostics
all and only actual HTTP exchanges in order
```

The CLI must execute only public HTTP and must not import or call application/persistence/database execution paths.

### Required verification

Primary bundle:

```text
M2-VER-27
```

Supporting evidence for:

```text
M2-VER-24
M2-VER-28
M2-VER-30
```

Verify parser, local validation, structured input, every selector family, trace schema, transport/application/protocol/local errors, TLS verification and absence of forbidden options/import paths.

Machine-check:

```text
63 API business operations == 63 CLI remote specifications
```

Run controlled HTTP integration and non-interactive subprocess tests, affected API regressions and Ruff/Pyright.

### Completion condition

A reviewer may mark `M2-S05` `COMPLETED` only when:

```text
the 63-operation registry is the sole CLI command authority
netauto -n performs exactly one requested business command
no Health preflight, redirect, cookie or retry is hidden
stdout/stderr/exit/trace contracts are exact
human and nested selectors never guess
HTTPS verification is mandatory
the CLI execution path is HTTP-only
M2-VER-27 passes and supporting evidence paths are implemented
```

Primary outcome support:

```text
M2-OUT-12
M2-OUT-13
M2-OUT-15
```

---

## M2-S06 — Official CLI interactive REPL and formatted experience

### Objective

Deliver the stateful official REPL on the same CLI core without creating a second command or semantic authority.

### Dependencies

```text
M2-S05 COMPLETED
```

### Normative authorities

```text
docs/milestones/M2/architecture/cli.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/health.md
docs/milestones/M2/architecture/verification.md

docs/general/technology_baseline.md
    STACK-10
```

### Deliverables

Implement the `prompt_toolkit` asynchronous REPL:

```text
netauto
netauto>
```

with initial state:

```text
DISCONNECTED
FORMATTED
empty in-memory history
```

Implement the exact local command inventory:

```text
/connect
/disconnect
/status
/output
/help
/history
/clear
/exit
```

Implement connection transitions:

```text
/connect -> exact GET /health/core
/status disconnected -> no request
/status connected -> Health revalidation
business HTTP error -> remain CONNECTED
protocol-invalid business response -> remain CONNECTED
transport failure -> DISCONNECTED
failed replacement /connect -> old endpoint not restored
```

Implement terminal behavior:

```text
Ctrl-R reverse search
Ctrl-C cancels current edit/command without exiting
Ctrl-D on empty prompt exits
command error returns to prompt
/clear preserves state and history
history is process-local only
```

Implement output modes:

```text
FORMATTED
JSON
```

FORMATTED rules:

```text
mutation -> direct result only, no hidden GET
list/page -> primary page only
single-resource read -> bounded registered GET-only enrichment
required enrichment failure -> whole command failure
```

JSON mode uses the same exact exchange trace as non-interactive mode.

### Required verification

Primary bundles:

```text
M2-VER-25
M2-VER-26
M2-VER-28
```

Use pure state-machine tests, controlled HTTP transport tests and Linux PTY/subprocess tests for editing/history/signals/exit behavior.

Verify complete help/registry consistency, Health connection behavior, bounded enrichment, no hidden mutation GET, no persistent profile/history/credential surface and no direct kernel imports.

Run full CLI T8 coverage, affected API/Health regressions and Ruff/Pyright.

### Completion condition

A reviewer may mark `M2-S06` `COMPLETED` only when:

```text
interactive initial and connection states are exact
all eight local commands behave as frozen
terminal/history/key bindings are deterministic
FORMATTED enrichment is bounded and transparent
JSON trace remains the real exchange record
the REPL survives command failures
all three primary M2-VER bundles pass
```

Primary outcome support:

```text
M2-OUT-12
M2-OUT-15
```

---

## M2-S07 — Versioned wheel, installed Alembic and Linux operating baseline

### Objective

Deliver one reproducible release artifact containing server, CLI and Alembic graph, and prove the documented manual Linux operating procedure outside the repository checkout.

### Dependencies

```text
M2-S06 COMPLETED
```

### Normative authorities

```text
docs/milestones/M2/architecture/runtime-deployment.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/health.md
docs/milestones/M2/architecture/cli.md
docs/milestones/M2/architecture/verification.md

docs/general/technology_baseline.md
```

### Deliverables

Package in one versioned wheel:

```text
server runtime
netauto console entrypoint
neutral transport DTOs
installed netauto:migrations package resource
complete single-root Alembic graph
release metadata
embedded runtime.pylock.toml exported from committed uv.lock
```

Implement a reproducible artifact process that:

```text
builds one wheel
extracts the embedded runtime lock
uv pip syncs a clean target environment
installs the wheel --no-deps
requires no Git checkout or source project
```

Provide an operator-owned non-secret Alembic configuration using:

```text
script_location = netauto:migrations
```

and preserve explicit administration:

```text
alembic upgrade head
```

Implement and document the Linux release layout and procedure:

```text
install
configure application and serving settings
provide protected database_url secret
apply schema
start foreground Uvicorn
verify /health/core
stop
restart
verify resource disposal
```

Document finite connection capacity:

```text
workers * (pool_size + max_overflow)
```

and the trust/transport boundary:

```text
HTTP only inside trusted administrative boundary
external TLS across untrusted segments
CLI HTTPS verification mandatory
no native auth/authorization
database transport solely through database_url
```

### Required verification

Primary bundles:

```text
M2-VER-24
M2-VER-29
M2-VER-30
```

Run T9 in a clean environment outside the repository import path:

```text
wheel content and metadata inspection
runtime lock equality/reproducibility
installed server/CLI/Alembic entrypoints
installed unique-head discovery
explicit migration
server start/stop/restart
startup mismatch failure
Health readiness and later DB failure
CLI interactive/non-interactive installed invocation
secret and command-line non-leakage
HTTPS trust/mismatch/untrusted cases
```

Re-execute the installed-artifact parts required by `M2-VER-22`, `23`, `25`, `26`, `27`, `28`.

Run build, locked dependency, Ruff and Pyright gates.

### Completion condition

A reviewer may mark `M2-S07` `COMPLETED` only when:

```text
one wheel contains every required first-party component
exact runtime dependencies are reproducible from the embedded lock
installed Alembic works without checkout and remains explicit
installed startup/Health/CLI behavior matches the frozen contracts
the manual Linux procedure has been executed successfully
trust/TLS/secret boundaries are both documented and enforced
all three primary M2-VER bundles pass
```

Primary outcome support:

```text
M2-OUT-10
M2-OUT-11
M2-OUT-12
M2-OUT-13
M2-OUT-14
M2-OUT-15
```

---

## M2-S08 — Integrated regression, traceability and negative-surface closure

### Objective

Close the complete machine-checkable M2 traceability graph, AS-IS regression allowlist and all positive/negative surface inventories before the final candidate gate.

### Dependencies

```text
M2-S07 COMPLETED
```

### Normative authorities

```text
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/README.md
docs/milestones/M2/architecture/provenance.md
docs/milestones/M2/architecture/verification.md
all frozen M2 architecture owners

docs/architecture/README.md
all delivered AS-IS owners
docs/general/technology_baseline.md
```

### Deliverables

Implement a machine-checkable registry containing exact sets/maps for:

```text
16 M2-OUT identifiers
32 M2-AC identifiers
32 M2-VER identifiers
83 canonical scenario identifiers
21 safety predicates
63 public business HTTP operations
63 CLI remote operation mappings

OUT -> AC
AC -> VER
VER -> concrete evidence targets
predicate -> scenarios
AS-IS guarantee -> regression targets
negative surface -> assertions
```

Require:

```text
no missing or extra identifier
no empty bundle
no orphan target
no duplicate command/route identity
no architecture requirement outside contract authority
```

Implement the exact M2 delta allowlist and prove that every other delivered behavior remains passing.

Close positive and negative static/runtime inventories for:

```text
routes
error codes
tables/constraints/indexes
Alembic graph
auth/authorization absence
TLS/insecure-option absence
CLI direct-kernel import absence
automatic migration absence
WIP authority absence
normative placeholder absence
```

Prepare the final acceptance evidence harness and record schema under:

```text
docs/milestones/M2/evidence/
```

without yet claiming final acceptance.

### Required verification

Primary bundles:

```text
M2-VER-31
M2-VER-32
```

Run:

```text
complete delivered regression suite
complete M2 functional suite
all static T10 registries
route/API/CLI equality checks
schema positive and negative checks
authority/provenance checks
Ruff
Pyright strict
locked environment/build checks
```

All 51 delivered concurrency IDs must remain represented; full 83-scenario execution is re-run in `M2-S09`.

### Completion condition

A reviewer may mark `M2-S08` `COMPLETED` only when:

```text
16/32/32/83/21/63 censuses are exact
every frozen requirement has a concrete target
every preserved AS-IS guarantee has regression evidence
the delta allowlist contains only frozen M2 changes
all negative surfaces are asserted
no slice or implementation target depends normatively on WIP
M2-VER-31 and M2-VER-32 pass
no blocker remains for one identified final candidate run
```

Primary outcome support:

```text
M2-OUT-16
```

---

## M2-S09 — Full M2 acceptance and delivery-candidate gate

### Objective

Execute the dedicated final acceptance gate against one identified candidate commit and the wheel built from that commit.

This slice introduces no production capability. It may correct acceptance-harness or documentation defects within its scope, but a production finding is returned to the owning implementation slice or triggers the required architecture reopen.

### Dependencies and pre-flight

All prior slices must be reviewer-owned `COMPLETED`:

```text
M2-S00
M2-S01
M2-S02
M2-S03
M2-S04
M2-S05
M2-S06
M2-S07
M2-S08
```

Before execution, verify:

```text
contract FINAL / FROZEN
architecture set FINAL / FROZEN
steps FINAL / FROZEN
no partial reopen
candidate commit identified
working tree clean
wheel built from that exact commit
real PostgreSQL target identified
supported CPython/Linux environment recorded
```

### Normative authorities

```text
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/README.md
docs/milestones/M2/architecture/verification.md
all frozen M2 architecture owners
docs/general/technology_baseline.md
this steps.md final-gate contract
```

### Deliverables

Create durable evidence for the exact candidate under:

```text
docs/milestones/M2/evidence/
docs/milestones/M2/acceptance.md
```

Record:

```text
candidate commit SHA
wheel filename and cryptographic hash
NETAUTO version
CPython version
PostgreSQL version
Linux environment
exact commands
exact pass/fail counts
blocked or not-executed evidence with reason
schema/head identifiers
```

Execute all required layers:

```text
T0
T1
T2
T3
T4
T5
T6
T8
T9
T10
```

T7 remains supplementary and cannot replace deterministic evidence.

### Required verification

The final gate requires:

```text
M2-VER-01 ... M2-VER-32 = PASS
M2-AC-01 ... M2-AC-32 = PASS
M2-OUT-01 ... M2-OUT-16 covered

83 / 83 canonical concurrency scenarios PASS
21 / 21 predicates PASS
all required blocking/progress assertions PASS
no supported SQLSTATE 40P01
AS-IS regression closure PASS
schema / metadata drift == []
one root / one head PASS
15-table positive and negative schema inventory PASS
63 API / 63 CLI equality PASS
installed wheel / startup / Health / CLI / Linux PASS
Ruff format/check PASS
Pyright strict PASS
uv locked sync/build/reproducibility PASS
no blocking finding open
```

The evidence must come from the exact candidate and installed artifact; prior slice runs are supporting evidence, not a substitute.

### Completion condition

`M2-S09` becomes `COMPLETED` only through reviewer approval of the final gate.

The implementer may report:

```text
final acceptance candidate ready for reviewer inspection
```

but may not declare:

```text
M2-S09 COMPLETED
M2 DELIVERED
```

After approval, the next governance phase is separate from this slice:

```text
consolidate the delivered M2 semantics into docs/architecture/
perform AS-IS consistency closure
reviewer marks M2 DELIVERED
human merges M2
```

Primary outcome support:

```text
M2-OUT-01 ... M2-OUT-16
```

---

## 5. Primary evidence ownership matrix

Every `M2-VER-*` bundle has one primary implementation slice:

| Slice | Primary bundles |
|---|---|
| `M2-S01` | `M2-VER-01`, `M2-VER-02`, `M2-VER-03`, `M2-VER-04`, `M2-VER-05`, `M2-VER-06`, `M2-VER-07`, `M2-VER-10`, `M2-VER-20`, `M2-VER-21` |
| `M2-S02` | `M2-VER-08`, `M2-VER-09`, `M2-VER-11`, `M2-VER-12`, `M2-VER-13`, `M2-VER-14` |
| `M2-S03` | `M2-VER-15`, `M2-VER-16`, `M2-VER-17`, `M2-VER-18`, `M2-VER-19` |
| `M2-S04` | `M2-VER-22`, `M2-VER-23` |
| `M2-S05` | `M2-VER-27` |
| `M2-S06` | `M2-VER-25`, `M2-VER-26`, `M2-VER-28` |
| `M2-S07` | `M2-VER-24`, `M2-VER-29`, `M2-VER-30` |
| `M2-S08` | `M2-VER-31`, `M2-VER-32` |

```text
primary bundles assigned exactly once     32 / 32
unassigned primary bundle                  0
duplicate primary ownership                0
```

`M2-S00` provides shared implementation/evidence foundations. `M2-S09` re-executes and accepts every bundle.

## 6. Outcome-to-slice coverage

| Outcome | Primary implementation coverage |
|---|---|
| `M2-OUT-01` | `M2-S01` |
| `M2-OUT-02` | `M2-S01`, `M2-S03` |
| `M2-OUT-03` | `M2-S01`, `M2-S02` |
| `M2-OUT-04` | `M2-S01`, `M2-S02`, `M2-S03` |
| `M2-OUT-05` | `M2-S01`, `M2-S02` |
| `M2-OUT-06` | `M2-S01`, `M2-S02` |
| `M2-OUT-07` | `M2-S02` |
| `M2-OUT-08` | `M2-S00`, `M2-S03` |
| `M2-OUT-09` | `M2-S01` |
| `M2-OUT-10` | `M2-S04`, `M2-S07` |
| `M2-OUT-11` | `M2-S04`, `M2-S07` |
| `M2-OUT-12` | `M2-S05`, `M2-S06`, `M2-S07` |
| `M2-OUT-13` | `M2-S07` |
| `M2-OUT-14` | `M2-S07` |
| `M2-OUT-15` | `M2-S04`, `M2-S05`, `M2-S06`, `M2-S07` |
| `M2-OUT-16` | all slices; primary closure in `M2-S08` and `M2-S09` |

No outcome is accepted through documentation alone when runtime, PostgreSQL, HTTP, CLI or installed-artifact behavior is material.

## 7. Final acceptance gate model

M2 uses a dedicated final slice:

```text
M2-S09
    -> full acceptance and delivery-candidate gate
```

The model is unambiguous:

```text
M2-S00 ... M2-S08
    -> implementation and evidence production

reviewer marks every prior slice COMPLETED
    -> M2-S09 may start

M2-S09 candidate evidence
    -> reviewer approval required

reviewer marks M2-S09 COMPLETED
    -> AS-IS consolidation may start

AS-IS consolidation + closure
    -> reviewer may mark M2 DELIVERED

merge
    -> human-owned
```

Completing implementation slices does not itself accept or deliver the milestone.

## 8. Steps consistency closure

The non-normative review record is:

```text
docs/milestones/M2/wip/steps-consistency-closure.md
```

Closure result:

```text
frozen contract dependency                 PASS
frozen architecture dependency             PASS
slice census                               PASS — M2-S00 ... M2-S09
dependency graph                           PASS — directed / acyclic / complete
single foundation exception                PASS — M2-S00
primary M2-VER ownership                   PASS — 32 / 32 exactly once
M2-OUT coverage                            PASS — 16 / 16
canonical concurrency assignment           PASS — 83 / 83
API / CLI / Health / schema / runtime       PASS
AS-IS regression and negative surface      PASS
final acceptance model                     PASS — dedicated M2-S09
WIP authority dependency                   PASS — 0
unresolved normative placeholder           PASS — 0
open implementation-planning finding       0
contract or architecture reopening         NOT REQUIRED
```

## 9. Freeze declaration and change control

The complete implementation decomposition and its consistency closure were explicitly approved after the M2 contract and architecture set became `FINAL / FROZEN`.

```text
contract.md                 FINAL / FROZEN
architecture/README.md      FINAL / FROZEN
steps.md                    FINAL / FROZEN
initial authorized slice    M2-S00
later slices                BLOCKED by predecessor completion
```

`status.md` is the sole operational authority for the slice currently authorized. At initial freeze it marks only `M2-S00` as `READY`.

After freeze, any of the following requires formal `steps.md` reopening and a renewed consistency closure:

```text
new slice
scope expansion
primary evidence reassignment
dependency change
completion-condition weakening
final-gate model change
```

Any change affecting semantics, guarantees, public behavior, persistence, concurrency, security boundary or project-wide technology also requires reopening the owning frozen contract, architecture or technology authority before this document can be re-frozen.
