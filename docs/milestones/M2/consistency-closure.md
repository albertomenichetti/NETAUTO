# M2 — Current architecture consistency-closure gate

**Status:** FINAL — reviewer-owned post-consolidation closure specification.

## Purpose and authority boundary

This document owns the **procedure, scope, evidence shape and acceptance
conditions** for the independent consistency closure of the accepted current
architecture under `docs/architecture/`.

The accepted AS-IS baseline is:

```text
consolidation candidate
    f8caa2d56a099561b53da0c2ad32b43a91b6dafb

consolidation acceptance
    4fd0f38fc804a494d1d0ce0fd251c49119b14127
```

This gate does not define product semantics and cannot override:

```text
docs/architecture/
    accepted current semantic and technical owners

docs/general/technology_baseline.md
    ratified project-wide technology decisions

docs/milestones/M2/contract.md
    FINAL / FROZEN historical milestone contract

docs/milestones/M2/architecture/
    FINAL / FROZEN historical M2 TO-BE owners

docs/milestones/M2/acceptance.md
    accepted final implementation evidence
```

The frozen M2 authorities, accepted implementation, schema, public registries,
package metadata, tests and final evidence are **cross-check evidence**. They do
not become new current semantic owners.

The closure must not reconstruct the current architecture as a sequence of M1/M2
changes. It audits whether the accepted current owners form one complete,
non-contradictory representation of the system that exists now.

## Closure objective

The closure passes only when a future cycle can start from
`docs/architecture/README.md`, follow the owner map and obtain one coherent answer
to every current question about:

```text
domain state and identity
version lifecycle and exact bindings
canonical values and property semantics
persistence, schema and migrations
transaction and concurrency guarantees
public HTTP behavior and failures
Health, CLI and read projections
runtime, distribution, trust and Linux operation
verification layers, finite registries and negative surfaces
```

The consistency closure is not:

```text
a second consolidation rewrite
a stylistic polishing pass
a milestone delta review
a replacement for final implementation acceptance
a new architecture design phase
a license to align documentation to convenient code behavior
```

## Gate lifecycle

```text
READY
    reviewer has accepted the consolidation and opened this independent gate

IN PROGRESS
    the auditor is reading the whole corpus and deriving the finite closure

CANDIDATE READY FOR REVIEW
    one complete report and any bounded lossless corrections are pushed
    all required exact-candidate and exact-remote gates are green

REVIEW CHANGES REQUIRED
    reviewer rejects the closure candidate
    bounded corrections remain inside this gate

COMPLETED
    reviewer accepts the independent closure
    the separate delivery decision may start
```

The coding agent may publish only `CANDIDATE READY FOR REVIEW`. It must not mark
this gate `COMPLETED`, mark M2 `DELIVERED`, update the root README to a delivered
state or merge.

## Evidence precedence and mandatory STOP

For every shared claim, use this reasoning order:

```text
1. identify the current owner in docs/architecture/README.md
2. read that owner and every declared dependent owner
3. compare with other current owners
4. compare with the ratified technology baseline where applicable
5. use frozen M2 documents and accepted implementation/evidence as cross-checks
6. classify any mismatch before changing anything
```

A mismatch is classified as one of:

```text
current-document projection defect
    one current owner is unambiguous and a dependent projection is stale
    -> bounded lossless correction may be proposed inside this gate

current-owner incompleteness
    accepted authorities and implementation establish one unambiguous current
    meaning, but the owning current document omits it
    -> bounded lossless owner correction may be proposed inside this gate

implementation defect
    current authorities agree, implementation/schema/public surface does not
    -> STOP; do not rewrite current architecture to match the defect

architecture contradiction or missing decision
    current/frozen authorities admit more than one meaning or no complete meaning
    -> STOP; formal architecture reopen is required

new capability or improvement opportunity
    not required for consistency of the accepted boundary
    -> record out of scope; do not implement or design it here
```

Recency, code behavior, test expectations, a prompt, Git history or reviewer
convenience never provides implicit precedence.

## Audit universe

Read in full, dependency-first:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

docs/architecture/README.md
all fourteen owning/projection files linked by its owner map

docs/milestones/M2/contract.md
docs/milestones/M2/architecture/README.md
all normative files under docs/milestones/M2/architecture/
docs/milestones/M2/steps.md
docs/milestones/M2/status.md
docs/milestones/M2/acceptance.md
docs/milestones/M2/as-is-consolidation.md

accepted production modules, SQLAlchemy metadata, the installed Alembic graph,
public API/CLI registries, Settings, package metadata, runtime lock and permanent
verification registries needed to cross-check the current owners
```

Historical files under `docs/milestones/M2/wip/` may be inspected only to prove
that they are retired or non-authoritative. They are not semantic input and must
not be copied into current owners.

## Exact current owner set

The accepted current corpus contains exactly these fifteen Markdown files:

```text
docs/architecture/README.md
docs/architecture/datatype.md
docs/architecture/objecttemplate.md
docs/architecture/object.md
docs/architecture/relationship.md
docs/architecture/persistence.md
docs/architecture/concurrency-matrix.md
docs/architecture/concurrency.md
docs/architecture/api.md
docs/architecture/health.md
docs/architecture/cli.md
docs/architecture/runtime-deployment.md
docs/architecture/linux-operating-baseline.md
docs/architecture/verification.md
docs/architecture/verification-concurrency-registry.md
```

The owner map must link every file exactly once in its appropriate role.
`linux-operating-baseline.md` is an operator projection;
`runtime-deployment.md` remains the owning runtime/deployment authority.

No new current owner is introduced automatically. A demonstrated need to split or
add authority is an architecture finding and requires explicit reviewer action.

## Finite consistency matrix

The closure report must contain exactly the following matrix keys and a result
for each:

```text
CC-01  authority topology and owner uniqueness
CC-02  stable identity, exact versioning, lifecycle and default policy
CC-03  PrimitiveType, cardinality, canonical value and JSON representation
CC-04  ObjectTemplate inheritance, declarations and effective schema
CC-05  Object factual state, schema change, ownership and intrinsic lifecycle
CC-06  RelationshipDefinition, RDV, factual Relationship and event semantics
CC-07  relational schema, constraints, indexes, codecs and Alembic authority
CC-08  semantic concurrency matrix, lock plans, ordering and restart policy
CC-09  HTTP routes, DTOs, selectors, failures, reads and pagination
CC-10  Health semantics, startup compatibility and shared runtime resources
CC-11  CLI registry, selectors, session state, rendering and process behavior
CC-12  Settings, distribution, installed migration, trust and Linux operation
CC-13  verification layers, registries, environments and release gates
CC-14  exclusions, negative surfaces and technology-boundary coherence
CC-15  documentation hygiene, links, provenance and historical-authority isolation
```

Allowed matrix results are:

```text
PASS
FAIL:<finding-id>
BLOCKED:<finding-id>
```

A candidate may be handed off only with all fifteen results `PASS` and zero open
findings.

## CC-01 — authority topology and owner uniqueness

Verify:

```text
exact fifteen-file corpus
README owner map links every owner/projection exactly once
one primary owner for every architectural decision
no owner claims superseded or competing authority
projection documents identify their owning source
no semantic dependency cycle between owners
no current owner depends on milestone WIP as authority
```

Cross-document references may coordinate a decision but must not create two
independent normative definitions.

## CC-02 — identity, versions, lifecycle and defaults

Across `datatype.md`, `objecttemplate.md`, `relationship.md`, `object.md`,
`persistence.md`, `api.md` and `concurrency.md`, verify one exact meaning for:

```text
stable lineage/root identity versus exact version identity
positive lineage-local version numbers
DRAFT revision freshness
DRAFT -> PUBLISHED -> DEPRECATED monotonic lifecycle
immutable PUBLISHED/DEPRECATED snapshots
nullable exact same-lineage default pointers
first-publication default policy
explicit versus implicit binding
exact persisted pins and absence of floating latest/default references
PUBLISHED admission for new lifecycle-sensitive bindings
historical exact binding validity after deprecation
delete-DRAFT versus whole-root deletion
```

Object and factual Relationship current state must bind exact model versions.

## CC-03 — PrimitiveType, cardinality and canonical representation

Verify one shared contract across `datatype.md`, `objecttemplate.md`, `object.md`,
`relationship.md`, `api.md` and `persistence.md` for:

```text
exact nine-value PrimitiveType catalog
accepted lexical input versus canonical domain value versus persisted JSON value
SCALAR / LIST ownership by property declarations
ObjectTemplateVersion and RelationshipDefinitionVersion property consumers
constraint and enum canonicalization
no domain JSON null carrier
optional value/key-absence rules
ObjectTemplate migration defaults
Object and Relationship current property maps
lifecycle before_state / after_state codecs
```

No owner may imply a second Relationship codec, JSON Schema authority or runtime
property EAV authority.

## CC-04 — ObjectTemplate consistency

Verify agreement on:

```text
stable parent lineage and exact parent version pins
root/non-root rules
local property/component physical and semantic identity
effective inheritance and declaring-template identity
position and name uniqueness
required/migration-default semantics
CREATE_NEXT clone behavior
REVISE complete semantic replacement with differential physical DML
PUBLISH history recertification
active dependency and default behavior
abstract-template admission
component target lifetime and delete blockers
```

The current lock-plan owner and persistence delta must agree on unchanged,
removed, inserted and physically reinserted declarations.

## CC-05 — Object and ownership consistency

Verify agreement on:

```text
Object stable UUID and non-unique canonical name
exact ObjectTemplateVersion pin and canonical property map
CREATE / RENAME / DATA_CHANGE / SCHEMA_CHANGE / DELETE
no-op DATA_CHANGE behavior
preserve-or-fail schema migration
single-owner physical authority
SlotSemanticKey derivation from current effective schema
ATTACH cycle and slot admission
DETACH exact-edge behavior
Object delete blockers and exact-ID/ABA safety
atomic intrinsic and ownership lifecycle event sets
coherent Object reads and corruption boundary
```

## CC-06 — Relationship consistency

Verify agreement on:

```text
stable Definition identity, symmetry and complete Resolution membership
Resolution stable identity and mutable non-key name
RDV lifecycle, revision, default and property history
capability admission through PUBLISHED RDV
factual Relationship stable ID
exact RDV pin and canonical current properties
complete deterministic runtime closure
symmetric/non-symmetric factual uniqueness and self-loop rules
CREATE / DATA_CHANGE / SCHEMA_CHANGE / DELETE
relationship_fact_conflict and schema_change_blocked
no-op DATA_CHANGE versus real pin-changing SCHEMA_CHANGE
complete Object-relative relationship lifecycle fan-out
factual and model delete blockers
absence of autonomous Resolution/declaration CRUD
```

## CC-07 — persistence, schema and Alembic consistency

Verify current documents, SQLAlchemy metadata and installed migration agree on:

```text
exact fifteen tables
exact columns, types, nullability and server defaults
PK / UNIQUE / CHECK / FK identities and delete actions
exact twenty-nine explicit indexes, order, predicates and INCLUDE columns
owned CASCADE versus cross-aggregate RESTRICT
canonical JSONB top-level shapes and primitive codec
one semantic mutation / one caller-owned transaction
one migration file and one base/head/current: 0001_m2_kernel
down_revision None
empty database -> head and owned head -> base behavior
compare_metadata == []
no automatic migration, stamp, repair or alternate compatibility path
startup exact revision equality before serving
```

No undocumented schema object, duplicate authority, GIN/expression property index
or materialized cache is part of the accepted boundary.

## CC-08 — concurrency consistency

Verify exact equality and compatible meaning across `concurrency-matrix.md`,
`concurrency.md`, `verification-concurrency-registry.md`, implementation planner
registries and permanent tests:

```text
41 mutation primitives
15 semantic family blocks
861 unordered interaction cells
21 safety predicates
83 canonical scenarios
11 primary recipes
three advisory gates and stable keys
five global row families 10 / 20 / 30 / 40 / 50
KS / S / NKU / U sufficient initial modes
one complete immutable pre-DML plan per mutation
gate-before-row discipline
header/version and ObjectTemplate ancestry order
target-before-existing-owner and target-before-child-DML rules
differential declaration lock semantics
fresh protected reread and LockPlanStale handling
maximum four whole-UoW attempts for approved restart causes only
no automatic 40P01 or 40001 retry
finite constraint/SQLSTATE classification
supported wait-for graph acyclic by construction
```

Semantic matrix classification owns required outcomes; PostgreSQL realization
owns the mechanism. Neither may silently strengthen or weaken the other.

## CC-09 — HTTP consistency

Verify equality among the current API owner, FastAPI routes, DTOs, error registry,
OpenAPI and CLI remote registry:

```text
63 business operations = 41 mutation + 22 read
GET /health/core as the sole operational route
64 total public HTTP operations
strict operation-specific request carriers
omission distinct from explicit null/input
exact stable/version/resource selectors
success status, body and Location behavior
23 public error codes and finite status mapping
bounded safe error details with no SQL/internal leakage
route-specific deterministic ordering
opaque keyset cursor binding and pagination
single-request coherent reads
absence of generic PUT/PATCH/action/query/sort/bulk protocols
```

Health is not counted as a business operation.

## CC-10 — Health and startup consistency

Verify one separation of responsibility across `health.md`, `api.md`,
`runtime-deployment.md`, `linux-operating-baseline.md` and implementation:

```text
startup revision guard executes before serving
startup never migrates, stamps or repairs
Health uses the same worker engine/pool as business work
Health executes exact bounded SELECT 1
one fixed deadline covers pool acquisition plus query
200/503 safe response mapping
no schema/Alembic check inside Health
no auth, migration, repair, secret or driver detail in Health
server remains HTTP-capable for Health 503 after later database transport loss
```

## CC-11 — CLI consistency

Verify the current CLI owner, parser/registry, transport and process tests agree on:

```text
63 remote operations exactly equal to the business API
8 local commands
HTTP-only execution and no direct kernel/database import path
non-interactive and asynchronous REPL modes
exact selector planning and persisted identity behavior
one persistent AsyncClient per REPL session
fresh command-local trace ledger and memo state
FORMATTED and JSON modes
no mutation enrichment
bounded GET-only presentation enrichment with identity validation
verified HTTPS and no insecure bypass
no endpoint/credential/history persistence
process-local history and Ctrl-C / Ctrl-D / Ctrl-R behavior
stdout / stderr / exit-status contract
```

Client presentation must not absorb hidden domain or persistence authority.

## CC-12 — runtime, distribution and Linux consistency

Verify agreement among runtime owner, operator projection, Settings,
`pyproject.toml`, wheel contents, installed Alembic and runtime lock:

```text
exact seven Settings fields, defaults, strict validation and source precedence
explicit secret-directory composition
one process-local engine/pool per worker and bounded disposal
pool-capacity formula and separate Alembic administrative connection
one wheel with server, CLI, neutral DTOs, migration graph and runtime lock
no operator-supplied values, secrets or deployment assets in the wheel
installed package-resource Alembic discovery and unique head
exact PEP 751 runtime lock derived from uv.lock
wheel-only source-isolated installation
explicit migration, start, readiness, stop and restart procedure
trusted-boundary HTTP and external TLS termination responsibility
verified CLI HTTPS
no bundled daemon, supervisor, container, firewall, backup or orchestration product
```

The Linux guide is actionable projection and may not redefine runtime semantics.

## CC-13 — verification consistency

Verify the current verification owners and permanent registries agree on:

```text
T0, T1, T2, T3, T4, T5, T6, T7, T8, T9, T10
real PostgreSQL requirements for material database claims
T9 wheel-installed/source-isolated operation
T10 finite inventory and negative-surface responsibility
exact 41 / 15 / 861 / 21 / 83 / 15 / 63 / 1 / 63 / 8 / 23 inventories
one primary deterministic recipe per scenario
all predicates mapped to scenarios
skip / xfail / rerun are never normative PASS
sleep, stress and automatic rerun are not correctness authorities
supported-path 40P01 and unexpected 40001 are zero
negative controls use an exact separate census
compare_metadata == []
artifact reproducibility/invariance where applicable
```

Cycle-specific `M2-VER`, `M2-AC`, slice IDs, candidate hashes and pass durations
remain evidence/history and do not become current architecture identifiers.

## CC-14 — exclusions and technology boundaries

Verify current owners, technology baseline, dependencies, entrypoints and tracked
assets do not imply an implemented surface for:

```text
runtime property EAV, generic property search or search-index management
autonomous Resolution/declaration CRUD
event-sourced current state or event-set resource
generic query/sort/PATCH/bulk/action DSL
native authentication, authorization, credentials or security schemes
native server TLS or insecure CLI mode
container/orchestrator/process-manager/deployment pipeline
cluster, HA, multi-region or replica orchestration
backup/restore/PITR/disaster-recovery automation
metrics/tracing/dashboard/log-shipping platform
automatic migration/stamp/repair
multiple migration heads or alternate schema compatibility
```

A future opportunity mentioned conversationally or in historical WIP is not part
of the current architecture.

## CC-15 — documentation hygiene and history isolation

Audit the complete current corpus for:

```text
internal Markdown links and anchors
exact owner-file inventory
TBD / TODO / FIXME / placeholder / unresolved-open wording
temporal or before/after change-log language in semantic sections
milestone/slice/review-fix/candidate identifiers in current semantics
pass counts, command durations or commit hashes in current owners
references to WIP as semantic authority
stale active-status wording
contradictory status headers and body sections
duplicate finite inventories with different values
```

The concise M1/M2 provenance table in `docs/architecture/README.md` is the only
allowed cycle-name use for current architecture navigation, apart from links to
historical records where semantically necessary.

## Write scope and correction discipline

### Default write scope

Without a discovered consistency finding, the coding agent may create or update
only:

```text
docs/milestones/M2/consistency-closure-report.md
docs/milestones/M2/status.md
```

### Conditional lossless correction scope

A current owner may be modified only when all conditions hold:

```text
one concrete finding ID exists
the owning document is unambiguous
the accepted implementation and frozen authorities confirm the same meaning
the edit is lossless clarification or propagation, not new semantics
every dependent current owner has been re-read
the finding and correction are recorded in the report
```

Only the implicated file under `docs/architecture/` may be changed. Other owners
remain untouched.

A permanent current-AS-IS regression may be strengthened only when the finding
demonstrates a verification gap. The preferred existing owners are:

```text
tests/test_m2_s08_regression.py
    positive finite inventory and cross-owner equality

tests/test_m2_s08_negative_surface.py
    negative surfaces and absence claims
```

No production, schema, migration, dependency, lock or release change is
authorized. No new semantic owner or test framework may be introduced without
reviewer authorization.

### Mandatory STOP scope

Stop without correction when a finding would require:

```text
changing product behavior or a public contract
changing schema, migration, index or dependency content
choosing among multiple plausible semantics
reopening a frozen M2 authority
adding a new current owner
changing the ratified technology baseline
weakening an accepted verification guarantee
```

## Finding registry

Finding IDs use:

```text
M2-CC-F01
M2-CC-F02
...
```

Every finding record contains:

```text
ID
matrix key
classification
owners involved
exact contradictory statements or missing projection
accepted/frozen/implementation evidence used
resolution or STOP reason
files changed, if any
permanent regression, if any
status OPEN / CLOSED / BLOCKED
```

Finding IDs are historical gate evidence. They must not appear in
`docs/architecture/`.

## Required closure report

The candidate must create:

```text
docs/milestones/M2/consistency-closure-report.md
```

The report is evidence, not semantic authority. It must contain:

```text
Status: CANDIDATE READY FOR REVIEW
starting reviewer-acceptance HEAD
AUDITED_ASIS_SHA
publication/evidence HEAD
exact fifteen-file inventory and content hashes
CC-01 ... CC-15 matrix
finding registry and open-finding count
owner/dependency audit summary
implementation/schema/public-registry cross-check summary
document hygiene and WIP-isolation audit
commands, environment and exact results
artifact identity
scope and changed-file inventory
reviewer boundary
```

The report must not claim reviewer acceptance, closure completion, M2 delivery or
merge.

## Candidate publication model

Define:

```text
AUDITED_ASIS_SHA
    exact commit containing the AS-IS and any bounded owner/test corrections
    before the report/status publication commit
```

If no correction is required, `AUDITED_ASIS_SHA` is the starting consistency
closure HEAD.

If correction is required:

```text
1. record finding in a draft report/status
2. apply only the bounded owner/test correction
3. commit the correction
4. freeze that commit as AUDITED_ASIS_SHA
```

Run the complete closure gate from a clean detached worktree at
`AUDITED_ASIS_SHA`. Only after it passes may the agent publish the report and
candidate-ready status.

The publication commit may modify only:

```text
docs/milestones/M2/consistency-closure-report.md
docs/milestones/M2/status.md
```

After publication, rerun the integrity and required regression gates on the exact
remote HEAD. The report records candidate-SHA commands; post-publication results
are recorded in `status.md` and the handoff without recursively rewriting the
report.

## Static and repository audits

The closure must execute deterministic bounded audits for:

```text
exact fifteen-file owner corpus
README owner map completeness and uniqueness
Markdown link/anchor validity
temporal/delta wording
milestone/review/candidate leakage
TBD/TODO/FIXME/placeholders/open points
duplicate or conflicting finite inventories
current owner references to WIP authority
CC-01 ... CC-15 matrix completeness
finding registry completeness
```

Temporary scripts may be used but must not be committed unless they become a
justified permanent regression under the conditional scope.

## Required repository verification

Use the accepted ratified environment and execute at least:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q

current-AS-IS regression and negative-surface tests
M1/M2 traceability and S09 lifecycle/evidence tests
schema, metadata, migration and startup-revision tests
API, DTO, error, OpenAPI and CLI registry/process tests
Health and runtime composition tests
installed-wheel/Linux T9 tests
real-PostgreSQL concurrency tests
non-PostgreSQL suite
full repository suite
```

Use only the externally supplied real `TEST_DATABASE_URL`. A local hostname is
acceptable when it reaches the dedicated real PostgreSQL target and the tests do
not provision or substitute it.

## Required outcome

A candidate may be published only with:

```text
CC-01 ... CC-15                    PASS
open consistency findings          0
normative skip / xfail / rerun      0 / 0 / 0
supported-path 40P01                0
unexpected 40001                    0
negative-control SQLSTATE           exact expected census
compare_metadata                    []
new unexplained warnings            0
Ruff / Pyright / build / collection PASS
artifact identity                   unchanged
production/schema/dependencies      unchanged
```

The reviewed Starlette deprecation may remain the only known warning.

Expected invariant artifact identity is:

```text
wheel
    netauto-0.2.0-py3-none-any.whl
    165978 byte
    77 members
    SHA-256 38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60

runtime lock
    48238 byte
    29 packages
    SHA-256 0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf
```

## Candidate state and reviewer boundary

If any gate fails:

```text
AS-IS consolidation    COMPLETED
consistency closure    IN PROGRESS
M2                     NOT DELIVERED
```

The exact blocker is recorded; no candidate is handed off.

If all gates pass, the coding agent may publish only:

```text
AS-IS consolidation    COMPLETED
consistency closure    CANDIDATE READY FOR REVIEW
M2                     NOT DELIVERED
merge                   NOT EXECUTED
```

Reviewer acceptance is required for:

```text
consistency closure    COMPLETED
```

Only after that acceptance may a separate reviewer-owned delivery decision be
prepared. Delivery does not imply merge; merge remains human-owned.
