# M3 — Current architecture consistency-closure gate

**Status:** FINAL — reviewer-owned post-consolidation closure specification.

## Purpose and authority boundary

This document owns the **procedure, scope, evidence shape and acceptance conditions** for the independent consistency closure of the reviewer-accepted M3 current architecture under `docs/architecture/`.

Accepted post-implementation baseline:

```text
final implementation acceptance
    M3-S07 COMPLETED / ACCEPTED
    replacement candidate 58c2789f2433fbaf1a79a9f870970f7bdc2e73b1

AS-IS consolidation candidate
    d5b73b892defe554e21dff0c29d1e0e221157d9a

AS-IS consolidation acceptance
    cb444bbe797f6ff74df833b512667876188c150d
```

This gate does **not** define product semantics and cannot override:

```text
docs/architecture/
    reviewer-accepted current semantic and technical owners

docs/general/technology_baseline.md
    ratified project-wide technology decisions

docs/milestones/M3/contract.md
    FINAL / FROZEN historical M3 contract

docs/milestones/M3/architecture/
    FINAL / FROZEN historical M3 TO-BE owners

docs/milestones/M3/acceptance.md
    reviewer-owned final implementation acceptance

docs/milestones/M3/as-is-consolidation.md
    reviewer-owned consolidation procedure and acceptance conditions
```

Frozen M3 authorities, accepted implementation, schema, public registries, package metadata, tests and accepted evidence are **cross-check evidence**. They do not become competing current semantic owners.

The closure audits whether the accepted current owners form one complete, autonomous and non-contradictory description of NETAUTO as it exists now. It must not reconstruct that architecture as a sequence of M1/M2/M3 deltas.

## Closure objective

The gate passes only when a future milestone or fix can start from `docs/architecture/README.md`, follow the owner map and obtain one coherent answer to every current question about:

```text
domain state and identity
exact versioning, lifecycle and defaults
canonical values and property semantics
trusted public read responsibility
single-request PostgreSQL statement-snapshot coherence
cursor identity and keyset position
historical lifecycle decoding
ObjectTemplate parent filtering in HTTP and CLI
CLI create-response Location validation
persistence, schema and migrations
transaction and mutation concurrency guarantees
public HTTP behavior and failures
Health, runtime, CLI and Linux operation
verification layers, finite registries and negative surfaces
```

The consistency closure is **not**:

```text
a second AS-IS rewrite
a style-polishing exercise
a milestone delta review
a replacement for final implementation acceptance
a new architecture-design phase
a software implementation phase
a license to align documentation to convenient current code behavior
```

## Gate lifecycle

```text
READY
    reviewer has accepted AS-IS consolidation and authorized this gate

IN PROGRESS
    auditor reads the complete current corpus and derives the finite closure

CANDIDATE READY FOR REVIEW
    one complete report and any bounded lossless corrections are pushed
    all required exact-candidate and exact-remote gates are green

REVIEW CHANGES REQUIRED
    reviewer rejects the closure candidate
    bounded corrections remain inside this gate

COMPLETED
    reviewer accepts the independent closure
    a separate delivery decision may then be authorized
```

The coding agent may publish only `CANDIDATE READY FOR REVIEW`. It may not mark the gate `COMPLETED`, mark M3 `DELIVERED`, update the root README to delivered state, create a PR, merge, tag, release or publish artifacts.

`M3-S07` remains `COMPLETED` throughout this gate. Software implementation remains `NOT AUTHORIZED`.

## Evidence precedence and mandatory STOP

For every shared claim:

```text
1. identify the current owner in docs/architecture/README.md
2. read that owner and every declared dependent owner
3. compare current owners with one another
4. compare with technology baseline where applicable
5. use frozen M3 authorities and accepted implementation/evidence as cross-checks
6. classify any mismatch before changing anything
```

Mismatch classes:

```text
current-document projection defect
    one current owner is unambiguous and a dependent projection is stale
    -> bounded lossless correction may be proposed inside this gate

current-owner incompleteness
    accepted authorities establish one unambiguous current meaning but the
    current owner omits it
    -> bounded lossless owner correction may be proposed inside this gate

implementation defect
    current authorities agree but implementation/schema/public surface differs
    -> STOP; do not rewrite architecture to fit the defect

architecture contradiction or missing decision
    current/frozen authorities admit multiple meanings or no complete meaning
    -> STOP; formal architecture reopen is required

new capability or improvement opportunity
    not required for consistency of the accepted boundary
    -> out of scope; do not implement or design it here
```

Recency, code behavior, tests, prompts, Git history or convenience never provide implicit semantic precedence.

## Audit universe

Read in full, dependency-first:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

docs/architecture/README.md
all fourteen owner/projection files linked by its owner map

docs/milestones/M3/contract.md
docs/milestones/M3/architecture/README.md
all normative files under docs/milestones/M3/architecture/
docs/milestones/M3/steps.md
docs/milestones/M3/status.md
docs/milestones/M3/acceptance.md
docs/milestones/M3/as-is-consolidation.md
docs/milestones/M3/evidence/M3-S06-candidate.md
docs/milestones/M3/evidence/M3-S07-candidate.md

accepted production modules and DTOs
SQLAlchemy metadata and installed Alembic graph
public API/OpenAPI and CLI registries
Settings and package metadata
runtime lock
permanent M1/M2/M3/current-AS-IS verification and concurrency registries
```

Historical files under `docs/milestones/M3/wip/` are non-authoritative execution/history material. They may be inspected to prove retirement or historical isolation but must not supply current semantics.

## Exact current owner set

The accepted corpus contains exactly these fifteen Markdown files:

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

The owner map must link every file exactly once in its role. `linux-operating-baseline.md` is an operator projection; `runtime-deployment.md` remains the owning runtime/deployment authority.

No new current owner may be introduced automatically. A demonstrated need to add/split authority is an architecture finding and STOP condition.

# Finite consistency matrix

The closure report must contain exactly these matrix keys:

```text
CC-01  authority topology and owner uniqueness
CC-02  stable identity, exact versioning, lifecycle and default policy
CC-03  PrimitiveType, cardinality, canonical value and JSON representation
CC-04  ObjectTemplate inheritance, declarations, effective schema and trusted reads
CC-05  Object factual state, ownership, lifecycle and trusted projections
CC-06  RelationshipDefinition, RDV, factual Relationship and historical decoding
CC-07  relational schema, codecs, Alembic and public read projection realization
CC-08  mutation concurrency, lock plans and statement-snapshot boundary
CC-09  HTTP routes, DTOs, failures, trusted reads, parent filter and cursor protocol
CC-10  Health semantics, startup compatibility and shared runtime resources
CC-11  CLI registry, selectors, nullable carriers, Location protocol and process behavior
CC-12  Settings, distribution, installed migration, trust and Linux operation
CC-13  verification layers, exact registries, environments and release gates
CC-14  exclusions, negative surfaces and technology-boundary coherence
CC-15  documentation hygiene, links, provenance and historical-authority isolation
```

Allowed results:

```text
PASS
FAIL:<finding-id>
BLOCKED:<finding-id>
```

A candidate may be handed off only with all fifteen results `PASS` and zero open findings.

## CC-01 — authority topology and owner uniqueness

Verify:

```text
exact fifteen-file corpus
README owner map links every owner/projection exactly once
one primary owner for each architectural decision
no owner claims superseded or competing authority
projection documents identify their owning source
no semantic dependency cycle between owners
no current owner depends on milestone WIP as semantic authority
M1/M2/M3 provenance appears only as historical navigation
```

Cross-document references may coordinate one decision but must not create two independent definitions.

## CC-02 — identity, exact versions, lifecycle and defaults

Across `datatype.md`, `objecttemplate.md`, `relationship.md`, `object.md`, `persistence.md`, `api.md` and `concurrency.md`, verify one meaning for:

```text
stable lineage/root identity versus exact version identity
positive lineage-local version numbers for admitted current model state
DRAFT revision freshness
DRAFT -> PUBLISHED -> DEPRECATED monotonic lifecycle
immutable PUBLISHED/DEPRECATED model snapshots
nullable exact same-lineage default pointers
first-publication default policy
explicit versus implicit new binding
exact persisted pins and no floating latest/default references
PUBLISHED admission for new lifecycle-sensitive bindings
historical exact binding validity after deprecation
delete-DRAFT versus whole-root deletion
```

Object and factual Relationship current state must bind exact model versions.

Historical read decoder tolerance must not be misread as weakening mutation/model invariants.

## CC-03 — PrimitiveType, cardinality and canonical representation

Verify one shared current contract across `datatype.md`, `objecttemplate.md`, `object.md`, `relationship.md`, `api.md` and `persistence.md` for:

```text
exact nine-value PrimitiveType catalog
accepted lexical input versus canonical domain value versus persisted JSON value
SCALAR / LIST ownership by property declarations
ObjectTemplateVersion and RelationshipDefinitionVersion property consumers
constraint and enum canonicalization
no domain JSON-null runtime value carrier
optional value/key-absence rules
ObjectTemplate migration defaults
Object and Relationship current property maps
lifecycle before_state / after_state persistence codecs
historical JsonValue decoding boundary distinct from current runtime admission
```

No owner may imply a second Relationship codec, JSON Schema authority or runtime property EAV authority.

## CC-04 — ObjectTemplate consistency

Verify agreement on:

```text
stable parent lineage and exact parent-version pins
root/non-root rules
local property/component physical and semantic identity
effective inheritance and declaring-template identity
position and name uniqueness
required/migration-default semantics
CREATE_NEXT clone behavior
REVISE complete semantic replacement and differential physical DML
PUBLISH history recertification
active dependency/default behavior
abstract-template admission
component target lifetime/delete blockers
trusted exact-version aggregate projection
effective schema follows exact persisted parent-version chain
relationship capability membership follows stable lineage ancestry
GET does not replay inheritance/default/declaration mutation certification
```

The lock-plan owner and persistence model must agree on unchanged, removed, inserted and physically reinserted declarations.

## CC-05 — Object and ownership consistency

Verify agreement on:

```text
Object stable UUID and non-unique canonical name
exact ObjectTemplateVersion pin and canonical current property map
CREATE / RENAME / DATA_CHANGE / SCHEMA_CHANGE / DELETE
no-op DATA_CHANGE behavior
preserve-or-fail schema migration
single-owner physical authority
SlotSemanticKey derivation from current effective schema
ATTACH cycle/slot admission and DETACH exact-edge behavior
Object delete blockers
atomic intrinsic and ownership lifecycle event sets
intrinsic GET does not re-certify ObjectTemplate/DataType closure
components/owner use exact-chain context only to materialize mandatory slot declaration
absent target vs empty page vs detached null remain distinct
Object-relative Relationship projection deduplicates before keyset/limit
historical Object/lifecycle JsonValue decoding tolerates representable semantic surprises
materially undecodable mandatory context fails boundedly
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
complete semantic lifecycle fan-out
factual/model delete blockers
absence of autonomous Resolution/declaration CRUD
Definition/RDV/Relationship GETs trust persisted facts rather than mutation recertification
factual Relationship root may project views=[] when no view is materializable
historical Relationship factual state decodes integer + recursive JsonValue carriers
historical GET does not replay changedness/version-increase/current-schema certification
```

## CC-07 — persistence, schema, Alembic and read projection realization

Verify current owners, SQLAlchemy metadata and installed migration agree on:

```text
exact fifteen tables
exact columns, types, nullability and server defaults
PK / UNIQUE / CHECK / FK identities and delete actions
exact explicit index inventory, order, predicates and INCLUDE columns
owned CASCADE versus cross-aggregate RESTRICT
canonical JSONB top-level shapes and primitive codec
one semantic mutation / one caller-owned write transaction
one migration file and one base/head/current = 0001_m2_kernel
down_revision None
empty database -> head and owned head -> base behavior
compare_metadata == []
no automatic migration/stamp/repair/alternate compatibility path
startup exact revision equality before serving
22 canonical public GETs each use one ordinary read UoW and exactly one authoritative business SQL statement
parent-rooted queries preserve target absence independently from empty/null public state
aggregate paging applies keyset/limit to public/root items before child expansion where required
read projectors perform typed carrier materialization without mutation-semantic recertification
coherent_read() remains valid only where an owner outside the canonical GET census requires it
```

No undocumented schema object, materialized read cache or second semantic-certification layer belongs to the accepted boundary.

## CC-08 — concurrency and statement-snapshot boundary

Verify equality and compatible meaning across `concurrency-matrix.md`, `concurrency.md`, `verification-concurrency-registry.md`, planner registries and permanent tests:

```text
41 mutation primitives
15 semantic family blocks
861 unordered interaction cells
21 safety predicates
83 canonical scenarios
three advisory gates and stable keys
five global row families 10 / 20 / 30 / 40 / 50
KS / S / NKU / U initial modes
one complete immutable pre-DML plan per supported mutation
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

Also verify the current read/concurrency boundary:

```text
canonical public GETs do not acquire mutation lock plans merely for consistency
one authoritative GET statement observes one PostgreSQL statement snapshot
writer-before-execute -> complete AFTER projection
writer-after-statement-before-return -> complete BEFORE projection
no mixed generation from the authoritative statement
no cross-request repeatable membership or snapshot-token guarantee
multi-statement coherent reads outside the census may still use their owned snapshot mechanism
```

Mutation semantic matrix owns mutation outcomes; PostgreSQL realization owns mechanisms; public read projection owns its statement-snapshot guarantee. These responsibilities must not be conflated.

## CC-09 — HTTP, trusted reads, parent filter and cursor protocol

Verify equality among current API owner, FastAPI routes, DTOs, error registry, OpenAPI, cursor codec/registries and CLI remote registry:

```text
63 business operations = 41 mutation + 22 read
GET /health/core sole operational route
64 total public HTTP operations
strict operation-specific request carriers
omission distinct from explicit null/input
exact stable/version/resource selectors
success status/body/Location behavior
23 public error codes and finite status mapping
bounded safe error details
22 trusted GETs with typed projection boundary
representable persisted semantic surprises readable
materially undecodable mandatory carriers -> bounded internal_error
12 exact cursor-bearing routes
query identity = route + membership path/filter/presence inputs
position = complete canonical keyset tuple
limit excluded from semantic identity
Object components cursor binds parent_object_id
Object-relative Relationship cursor binds object_id
lifecycle global/Object scope differs through involving_object_id
ObjectTemplate parent filter distinguishes omitted / UUID / exact lowercase null
cursor codec v1 opaque and unchanged
changed limit accepted; changed membership identity or malformed key rejected
no offset/page-number/generic query/sort/bulk protocol
```

Health is not counted as a business operation.

## CC-10 — Health and startup consistency

Verify one separation across `health.md`, `api.md`, `runtime-deployment.md`, `linux-operating-baseline.md` and implementation:

```text
startup revision guard before serving
startup never migrates/stamps/repairs
Health uses same worker engine/pool as business work
Health executes exact bounded SELECT 1
one fixed deadline covers pool acquisition + query
200/503 safe response mapping
no schema/Alembic check inside Health
no auth/migration/repair/secret/driver detail in Health
server remains HTTP-capable for Health 503 after later DB transport loss
```

## CC-11 — CLI consistency

Verify current CLI owner, parser/registry, transport and process tests agree on:

```text
63 remote operations exactly equal business API
8 local commands
HTTP-only execution; no direct kernel/database path
non-interactive and asynchronous REPL modes
exact selector planning and persisted identity behavior
one persistent AsyncClient per REPL session
fresh command-local trace ledger and memo state
FORMATTED and JSON modes
bounded GET-only presentation enrichment; no mutation enrichment
verified HTTPS and no insecure bypass
no endpoint/credential/history persistence
process-local history and Ctrl-C / Ctrl-D / Ctrl-R behavior
stdout/stderr/exit-status contract
ObjectTemplate parent nullable QUERY tri-state
explicit null -> parsed None -> zero selector discovery -> lexical query null
nullable BODY None -> JSON null; PATH None invalid
generic scalar serializer does not accept None globally
exact eight registered 201 + Location operations
closed Location token grammar {segment(.segment)*}
request_values exact-key presence before response JSON dotted traversal
materializable token carrier = str or int excluding bool
literal replacement only; no Python format grammar
exactly one actual Location equal to expected; protocol failure otherwise
no hidden post-mutation GET
```

Client presentation must not absorb domain/persistence authority.

## CC-12 — runtime, distribution and Linux consistency

Verify agreement among runtime owner, operator projection, Settings, `pyproject.toml`, wheel contents, installed Alembic and runtime lock:

```text
exact seven Settings fields/defaults/strict validation/source precedence
explicit secret-directory composition
one process-local engine/pool per worker and bounded disposal
pool-capacity formula and separate Alembic administrative connection
one wheel with server, CLI, neutral DTOs, migration graph and runtime lock
installed package-resource Alembic discovery and unique head
exact runtime lock derived from uv.lock
wheel-only source-isolated installation
explicit migration/start/readiness/stop/restart procedure
trusted-boundary HTTP and external TLS termination responsibility
verified CLI HTTPS
no bundled daemon/supervisor/container/firewall/backup/orchestration product
```

The Linux guide is an actionable projection and may not redefine runtime semantics.

## CC-13 — verification consistency

Verify current verification owners and permanent registries agree on:

```text
T0 through T10
real PostgreSQL required for material database claims
T9 wheel-installed/source-isolated operation
T10 finite inventory and negative-surface responsibility
exact current inventories:
    mutation primitives 41
    semantic family blocks 15
    unordered interaction cells 861
    safety predicates 21
    canonical concurrency scenarios 83
    authoritative tables 15
    business HTTP operations 63
    Health operations 1
    canonical GETs 22
    cursor routes 12
    CLI remote operations 63
    CLI 201 + Location operations 8
    CLI local commands 8
    public error codes 23
all scenarios mapped to deterministic evidence/recipes
all predicates mapped to scenarios
skip/xfail/rerun never normative PASS
sleep/stress/automatic rerun not correctness authorities
supported-path 40P01 = 0
unexpected 40001 = 0
negative controls separate and exact
compare_metadata == []
22/22 one-business-statement evidence
representative BEFORE/AFTER statement-snapshot evidence
trusted-read positive/negative boundary evidence
12-route cursor true-multipage/binding evidence
HTTP/CLI ObjectTemplate parent-tri-state evidence
8-operation Location protocol evidence
artifact reproducibility/invariance where applicable
```

Cycle-specific M3 outcome/AC/VER/CQG IDs, slice names, review findings, candidate hashes and pass durations remain history/evidence rather than current architecture identifiers.

## CC-14 — exclusions and technology boundaries

Verify current owners, technology baseline, dependencies, entrypoints and tracked assets do not imply implemented surface for:

```text
runtime property EAV or generic property search
autonomous Resolution/declaration CRUD
event-sourced current state or event-set resource
generic query/sort/PATCH/bulk/action DSL
cross-request database snapshot tokens/repeatable-membership promise
native authentication/authorization/credentials/security schemes
native server TLS or insecure CLI mode
container/orchestrator/process-manager/deployment pipeline
cluster/HA/multi-region/replica orchestration
backup/restore/PITR/disaster-recovery automation
metrics/tracing/dashboard/log-shipping platform
automatic migration/stamp/repair
multiple migration heads or alternate schema compatibility
```

A future opportunity or historical WIP note is not current architecture.

## CC-15 — documentation hygiene and history isolation

Audit the complete current corpus for:

```text
internal Markdown links and anchors
exact owner-file inventory
TBD / TODO / FIXME / placeholder / unresolved-open wording
temporal/before-after/change-log language in semantic sections
milestone/slice/review-fix/candidate identifiers in current semantics
pass counts, command durations or commit hashes in current owners
references to WIP as semantic authority
stale active-status wording
contradictory status headers/body sections
duplicate finite inventories with different values
```

The concise M1/M2/M3 provenance table in `docs/architecture/README.md` is the only normal cycle-name use for current architecture navigation, apart from explicit links to historical records where needed.

# Write scope and correction discipline

## Default write scope

Without a discovered consistency finding, the coding agent may create/update only:

```text
docs/milestones/M3/consistency-closure-report.md
docs/milestones/M3/status.md
```

## Conditional lossless correction scope

A current owner under `docs/architecture/` may be modified only when all conditions hold:

```text
one concrete finding ID exists
the owning current document is unambiguous
accepted/frozen/implementation evidence confirms the same meaning
edit is lossless clarification/propagation, not new semantics
every dependent current owner has been re-read
finding and correction are recorded in the closure report
```

Only implicated `docs/architecture/*.md` files may change.

Tests, production, schema, migration, dependency, lockfile, frozen M3 authority and technology-baseline changes are **not authorized** by this gate. If a permanent regression appears necessary, report the gap and STOP for reviewer authorization rather than modifying tests implicitly.

## Mandatory STOP scope

Stop without correction when a finding would require:

```text
changing product behavior or public contract
changing tests to redefine accepted semantics
changing schema/migration/index/dependency content
choosing among multiple plausible semantics
reopening frozen M3 authority
adding a new current owner
changing technology baseline
weakening an accepted verification guarantee
```

# Finding registry

Finding IDs use:

```text
M3-CC-F01
M3-CC-F02
...
```

Each record contains:

```text
ID
matrix key
classification
owners involved
exact contradiction or missing projection
accepted/frozen/implementation evidence used
resolution or STOP reason
files changed, if any
status OPEN / CLOSED / BLOCKED
```

Finding IDs are historical gate evidence and must not appear in `docs/architecture/`.

# Required closure report

The candidate must create:

```text
docs/milestones/M3/consistency-closure-report.md
```

The report is evidence, not semantic authority. It must contain:

```text
Status: CANDIDATE READY FOR REVIEW
starting reviewer-authorized consistency HEAD
AUDITED_ASIS_SHA
publication/evidence HEAD
exact fifteen-file inventory and content hashes
CC-01 .. CC-15 matrix
finding registry and open-finding count
owner/dependency audit summary
implementation/schema/public-registry cross-check summary
read/cursor/CLI protocol cross-check summary
document hygiene and WIP-isolation audit
commands, environment and exact results
wheel identity and source-archive identity
scope and changed-file inventory
reviewer boundary
```

It must not claim reviewer acceptance, consistency completion, M3 delivery or merge.

# Candidate publication model

Define:

```text
AUDITED_ASIS_SHA
    exact commit containing the AS-IS and any bounded owner corrections
    before report/status publication
```

If no correction is required, `AUDITED_ASIS_SHA` is the exact current closure work HEAD before publication. The fifteen current architecture file hashes must match the accepted consolidation corpus unless a recorded bounded correction exists.

If correction is required:

```text
1. record/classify the finding
2. apply only the bounded lossless current-owner correction
3. commit correction
4. freeze that commit as AUDITED_ASIS_SHA
5. restart the complete closure gate on that exact commit
```

Run the complete gate from a clean worktree at `AUDITED_ASIS_SHA`. During the gate, do not edit files. If anything changes, create a new audited SHA and restart.

Only after all requirements pass may the agent publish the report and candidate-ready status. The publication commit may modify only:

```text
docs/milestones/M3/consistency-closure-report.md
docs/milestones/M3/status.md
```

After publication, verify local/origin/remote equality and rerun bounded integrity/lifecycle checks on exact remote HEAD. Post-publication status may be reported in `status.md`/handoff without recursively rewriting the audited report.

# Static and repository audits

Execute deterministic bounded audits for:

```text
exact fifteen-file owner corpus
README owner map completeness/uniqueness
Markdown link/anchor validity
temporal/delta wording
milestone/review/candidate leakage
TBD/TODO/FIXME/placeholders/open points
duplicate/conflicting finite inventories
current owner references to WIP authority
CC-01 .. CC-15 completeness
finding registry completeness
```

Temporary scripts may be used but must not be committed unless separately authorized.

# Required repository verification

Use the ratified environment and real externally supplied `TEST_DATABASE_URL` for PostgreSQL claims.

Run at minimum:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q

current-AS-IS/documentation regression and negative-surface tests
M1/M2/M3 traceability and M3-S07 lifecycle/evidence tests
accepted M3 evidence selection
schema/metadata/migration/startup-revision tests
API/DTO/error/OpenAPI/CLI registry and protocol tests
Health/runtime composition tests
installed-wheel/Linux T9 tests
real-PostgreSQL mutation/concurrency tests
22-route statement and T3 snapshot evidence
non-PostgreSQL suite
full repository suite
```

A missing PostgreSQL environment blocks the gate; it is not a PASS.

# Required outcome

A candidate may be published only with:

```text
CC-01 .. CC-15                    PASS
open consistency findings          0
exact current architecture files  15 / 15
broken internal links              0
semantic milestone leakage         0
unresolved normative placeholder   0
business HTTP / Health             63 / 1 exact
canonical GET routes               22 exact
cursor routes                      12 exact
CLI 201 + Location operations       8 exact
metadata tables                    15
Alembic root/head/current           0001_m2_kernel exact
canonical scenarios                83 exact
safety predicates                  21 exact
normative skip / xfail / rerun      0 / 0 / 0
supported-path 40P01                0
unexpected 40001                    0
negative-control SQLSTATE           exact expected census
compare_metadata                    []
new unexplained warnings            0
Ruff / Pyright / build / collection PASS
production/schema/dependencies      unchanged
```

The reviewed Starlette deprecation may remain the sole known third-party warning.

Invariant binary/runtime identities from accepted S07 remain:

```text
project version
    0.2.0

wheel
    netauto-0.2.0-py3-none-any.whl
    170185 bytes
    SHA-256 428a2fe05a9905f3794dd15de65667d5506fa5bef2f0568d1ca1dd2b59fb0ba2

pyproject.toml blob
    d20bbb94739a74ebfb0bd27291b6e4f130d24c5f

uv.lock blob
    0aa980926fda5f42ee3a7d3cedc64f9fcf8c2d23

0001 migration blob
    27fc85e0b4411332fce87c406b6216b35db6eb20
```

The sdist byte identity is **not** invariant across documentation/report commits; record its exact candidate identity but do not require equality with the S07 sdist.

# Candidate state and reviewer boundary

If a required gate fails or is blocked:

```text
AS-IS consolidation    COMPLETED
consistency closure    IN PROGRESS or BLOCKED
M3                     NOT DELIVERED
```

Record the exact blocker and do not hand off a false candidate.

If all gates pass, the coding agent may publish only:

```text
AS-IS consolidation    COMPLETED
consistency closure    CANDIDATE READY FOR REVIEW
M3                     NOT DELIVERED
merge                   NOT EXECUTED
```

Reviewer acceptance is required for:

```text
consistency closure    COMPLETED
```

Only after reviewer acceptance may a separate reviewer-owned M3 delivery decision be prepared. Delivery does not imply merge; merge remains human-owned.
