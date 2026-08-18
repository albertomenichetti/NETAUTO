# Codex implementation prompt — M2-S01

**Status:** NON-NORMATIVE IMPLEMENTATION PROMPT.

This file is an execution aid for Codex. It narrows the authorized implementation task but does not override `AGENTS.md`, the delivered AS-IS, the FINAL/FROZEN M2 contract, architecture or steps, the active milestone status, or the ratified technology baseline.

## Assignment

Implement exactly:

```text
M2-S01 — Durable relational baseline and versioned Relationship model plane
```

from `docs/milestones/M2/steps.md`.

Work directly on branch:

```text
M2
```

The reviewed starting point is:

```text
d225faee6faf5fbebd36ce68db6c3b2c537323d0
docs(m2): accept S00 and open S01
```

`M2-S00` is reviewer-owned `COMPLETED`. `M2-S01` is the only authorized slice. Do not start `M2-S02` and do not expose any later Health, CLI, startup-guard, packaging or factual DATA_CHANGE/SCHEMA_CHANGE capability.

The required publication action is:

```text
perform the mandatory repository pre-flight
implement the complete vertical M2-S01 candidate
implement all assigned permanent evidence
run the mandatory quality, migration, API and real-PostgreSQL gates
commit intentionally
push normally to origin/M2
leave the branch synchronized and the working tree clean
leave the candidate ready for reviewer inspection
```

Do not create a pull request. Do not merge to `master`, force-push, rewrite published history, tag or release.

Do not add or use GitHub Actions, workflow-dispatched implementation, CI-driven commits, encoded patches or artifact-mediated source publication.

---

# 1. Mandatory pre-flight

Before changing implementation, schema, migrations, tests or status, read and obey at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

# Current delivered AS-IS
docs/architecture/README.md
docs/architecture/datatype.md
docs/architecture/objecttemplate.md
docs/architecture/object.md
docs/architecture/relationship.md
docs/architecture/persistence.md
docs/architecture/concurrency-matrix.md
docs/architecture/concurrency.md
docs/architecture/api.md
docs/architecture/verification.md
docs/architecture/verification-concurrency-registry.md

# Active M2 authority
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/README.md
docs/milestones/M2/architecture/relationship.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/concurrency-matrix.md
docs/milestones/M2/architecture/concurrency.md
docs/milestones/M2/architecture/verification.md
docs/milestones/M2/architecture/provenance.md
docs/milestones/M2/architecture/runtime-deployment.md
docs/milestones/M2/steps.md
docs/milestones/M2/status.md

# Current execution aid
docs/milestones/M2/wip/M2-S01-codex-prompt.md
```

Read owning sections dependency-first. Do not derive requirements from summaries in this prompt or from any other file under `docs/milestones/M2/wip/`. WIP material is historical/non-normative and `provenance.md` explicitly removes it from implementation authority.

Confirm from the repository itself that:

```text
checked-out branch       = M2
README active cycle      = M2 / IMPLEMENTATION / branch M2
origin/M2 baseline       = d225faee... or a direct descendant containing no unreviewed S01 work
M2 contract              = FINAL / FROZEN
M2 architecture set      = FINAL / FROZEN
M2 steps                 = FINAL / FROZEN
M2-S00                    = reviewer-owned COMPLETED
current authorized slice = M2-S01 only
M2-S01 state             = READY or IN PROGRESS
M2-S02                    = BLOCKED
relevant reopen          = none
STACK-01 ... STACK-10    = RATIFIED
```

Inspect the working tree, local/remote relationship, current migration graph, SQLAlchemy metadata, API route inventory and current test organization before modifying anything.

Also verify that the obsolete S00 Actions/payload mechanism remains absent:

```text
.github/m2-s00-payload/
.github/workflows/materialize-verify-m2-s00.yml
.github/workflows/export-m2-worktree.yml
```

If README, branch, `status.md`, frozen authorities or dependency state disagree, stop before implementation and report the mismatch. If two normative authorities conflict or fail to determine one required behavior, stop only the affected work and report an architecture/documentation finding. Do not choose the newest, easiest or currently implemented interpretation.

Code, tests, migration history, Git history, this prompt and previous reports are evidence or execution aids, not semantic authority.

A valid externally supplied real PostgreSQL target through `TEST_DATABASE_URL` is mandatory for completing this slice. Verify its availability during pre-flight. Do not provision PostgreSQL, use Docker/Testcontainers, invent credentials, fall back to localhost, fall back to `NETAUTO_DATABASE_URL`, or substitute SQLite.

---

# 2. Slice objective and hard boundary

M2-S01 is one vertical slice with four inseparable outcomes:

```text
A. the first durable final fifteen-table PostgreSQL baseline
B. complete RelationshipDefinitionVersion model-plane behavior
C. exact S01 HTTP/read/capability surface
D. the factual Relationship CREATE/GET/DELETE baseline delta
```

The slice is not complete if only schema, domain classes, routes or test scaffolding are added.

Preserve the completed S00 transaction foundation:

```text
central prepare_lock_plan / LockPlan authority
three frozen transaction advisory gates
four exact PostgreSQL row-lock modes
canonical row-class and intra-class order
targeted ObjectTemplate ancestry preparation
gate before rows
one complete pre-DML acquisition phase
fresh protected reread
no normal lock upgrade
no post-DML explicit lock
finite PostgreSQL failure classification
four-attempt whole-UoW restart only for approved causes
no retry of 40P01 or 40001
```

## 2.1 Explicitly in scope

```text
final SQLAlchemy metadata for exactly fifteen authoritative tables
one self-contained durable Alembic root revision, one base and one head
removal of the disposable M1 development revision chain
RelationshipDefinitionVersion domain/application/persistence/API
Relationship property declarations and historical evolution
RelationshipDefinition default policy
model-plane reads and capability predicate/projection
uniform defensive default-pointer validation for DT / OT / RD reads
factual Relationship exact RDV pin and canonical properties
factual Relationship CREATE, GET and DELETE M2 deltas
CREATED/DELETED factual lifecycle snapshots required by those operations
M2-VER-01..07, M2-VER-10, M2-VER-20 and M2-VER-21
assigned deterministic PostgreSQL scenarios
```

## 2.2 Explicitly out of scope

Do not implement:

```text
Relationship.DATA_CHANGE
Relationship.SCHEMA_CHANGE
public DATA_CHANGE or SCHEMA_CHANGE routes
DATA_CHANGE or SCHEMA_CHANGE application commands
current-state transition logic for those operations
Health API
runtime pool/settings expansion
startup schema-revision guard
CLI core or REPL
runtime.pylock.toml export
installed-wheel/Linux operating evidence
server/CLI release packaging work assigned to S07
native authentication/authorization/TLS
M1 -> M2 data backfill or compatibility bridge
dual schema, dual decoder or legacy event decoder
stamp-based conversion of an old physical database
new dependency or convenience framework
```

The final database lifecycle vocabulary must already contain the frozen M2 Relationship event kinds because S01 creates the final durable schema. That does not authorize the S02 DATA_CHANGE/SCHEMA_CHANGE operations.

No dependency or `uv.lock` change is expected. If implementation appears to require one, stop and prove from a ratified technology decision and frozen S01 scope why it is necessary before changing it.

---

# 3. First durable fifteen-table relational baseline

Implement the exact final SQLAlchemy Core metadata owned by `architecture/persistence.md`.

The authoritative table census is exactly:

```text
Model plane — 10
    datatypes
    datatype_versions
    object_templates
    object_template_versions
    object_template_properties
    object_template_components
    relationship_definitions
    relationship_resolutions
    relationship_definition_versions
    relationship_definition_properties

Data plane — 4
    objects
    object_components
    relationships
    runtime_relationship_resolutions

History — 1
    object_lifecycle_events
```

There must be no sixteenth persistence authority, EAV property table, schema cache, event-set table, provenance table or surrogate RDV/property/runtime-resolution identity.

## 3.1 New/changed core authorities

Realize exactly, without competing representations:

```text
relationship_definitions.default_version
relationship_definition_versions
relationship_definition_properties
relationships.relationship_definition_version
relationships.properties
final object_lifecycle_events vocabulary and transition-shape checks
```

Key requirements include:

```text
RelationshipDefinitionVersion identity
    (relationship_definition_id, version)

RelationshipDefinitionProperty physical identity
    (relationship_definition_id,
     relationship_definition_version,
     name)

Relationship factual exact binding
    (relationship_definition_id,
     relationship_definition_version)

Relationship factual properties
    JSONB NOT NULL
    explicit {} or canonical non-empty object on every INSERT
    no server default
```

Implement the exact named PK, UNIQUE, CHECK, FK, CASCADE and RESTRICT authorities from the frozen persistence owner. Preserve every delivered constraint that remains part of the final baseline.

In particular:

```text
Definition default
    -> exact same-Definition RDV
    -> ON DELETE RESTRICT

RDV
    -> stable Definition
    -> ON DELETE CASCADE

RD property
    -> exact owning RDV ON DELETE CASCADE
    -> exact DTV ON DELETE RESTRICT

Relationship
    -> exact same-Definition RDV ON DELETE RESTRICT

runtime closure
    -> Relationship owned CASCADE
    -> Resolution and endpoint Object lifetime RESTRICT

history
    -> no live FK to current rows
```

`relationship_definition_properties` has no:

```text
required
nullable
default_value
create_default
migration_default
surrogate ID
```

The lifecycle table must support the final frozen kind vocabulary and exact structural/nullability rules. For S01, real Relationship CREATED and DELETED rows must carry factual after/before state respectively. Do not invent a transitional legacy shape.

## 3.2 Final index contract

Implement the exact positive inventory in `architecture/persistence.md`, including the new/changed indexes:

```text
ix_relationship_definition_versions_status_definition_version
ix_relationship_definition_properties_datatype_version
ix_relationship_definition_properties_semantic_history
ix_relationship_resolutions_definition_id
ix_relationship_resolutions_name_id
ix_relationships_definition_version
ix_runtime_resolutions_from_object_page
    with the exact INCLUDE column
ix_runtime_resolutions_to_object_relationship
ix_runtime_resolutions_relationship
```

Also implement the frozen cross-domain status/history hardening and the exact partial lifecycle selector indexes.

Do not duplicate PK/UNIQUE-owned indexes.

Prove the negative inventory. The final schema must not contain:

```text
superseded development indexes
runtime-property or lifecycle-snapshot GIN/expression indexes
standalone default_version index
duplicate PUBLISHED-only partial index
second factual-identity index
event-set grouping index
```

Do not freeze PostgreSQL cost estimates or one exact plan tree. Representative plan evidence may disable sequential scans only to prove eligibility of an approved index.

## 3.3 Metadata quality

Use one authoritative SQLAlchemy `MetaData` graph. The live schema produced by the root revision must satisfy:

```text
compare_metadata == []
```

No application/domain code may define a second physical schema inventory.

Use explicit stable names for every relevant constraint and explicit index. Preserve PostgreSQL-specific types and dialect options where frozen, including JSONB, partial predicates and INCLUDE columns.

---

# 4. Replace the disposable migration chain with one durable root

The current baseline contains repository-root development revisions such as:

```text
migrations/versions/0001_m1_schema_initial_m1_schema.py
migrations/versions/0002_relationship_resolution_name_nonkey.py
```

They are disposable development history and must be removed from the shipped graph.

Create the canonical final migration environment under the installed package boundary:

```text
src/netauto/migrations/
    __init__.py
    env.py
    script.py.mako
    versions/
        __init__.py
        <one durable root revision>.py
```

The graph must have:

```text
one base
one root
one head
down_revision = None
```

Remove the old repository-root revision graph so there is no second Alembic authority. A repository-root `alembic.ini` may remain only as a non-secret operator/development configuration pointing to:

```text
script_location = netauto:migrations
```

It must contain no database URL, expected-head constant or source-tree migration path assumption.

S07 will prove the installed-wheel operating procedure. S01 must nevertheless create the graph in its final package-resource location now; do not create a temporary source-only migration layout that a later slice must semantically move.

## 4.1 Root revision contract

The root revision must:

```text
be self-contained physical DDL
create the exact final fifteen-table schema directly
use explicit stable constraint and index names
follow dependency-safe creation order
handle the three cyclic default-version FKs explicitly
create final lifecycle checks/indexes
import no mutable application metadata, domain or store code
use no IF EXISTS / IF NOT EXISTS to conceal drift
perform no legacy backfill, stamp or runtime repair
execute transactionally on PostgreSQL
```

The root revision may use SQLAlchemy/Alembic DDL primitives and frozen literal values. It must not derive its DDL from the current mutable `MetaData` at upgrade time.

The production migration environment must use explicit validated configuration, a synchronous SQLAlchemy engine with `NullPool`, and support a test-injected synchronous connection. It must not start ASGI, construct the business `AsyncEngine`, import application services or run migrations at server startup.

## 4.2 Supported transitions and permanent evidence

Implement real-PostgreSQL tests for:

```text
empty database -> head
head -> base
base -> head -> base -> head
```

Prove:

```text
exact one-base/one-head graph
exact final table/column/type/constraint/index inventory
zero metadata drift
old revision files absent from the graph and source candidate
external sentinel structures survive head -> base
repeat upgrade reproduces the exact schema
forced migration failure leaves base with no committed partial NETAUTO schema
corrected rerun succeeds from base
```

Do not test or document populated-M1 upgrade, stamp, backfill or data-preserving downgrade as supported behavior.

Automated migration tests use only the externally supplied `TEST_DATABASE_URL` boundary and explicit test injection. They must not silently read runtime configuration or a localhost fallback.

---

# 5. RelationshipDefinitionVersion domain model

Keep the domain plain Python. Domain modules must remain free of FastAPI, Pydantic, SQLAlchemy and Psycopg imports.

Implement semantic representations for at least:

```text
stable RelationshipDefinition with default_version
RelationshipDefinitionVersion
RelationshipDefinitionVersionSummary
RelationshipDefinitionProperty declaration
complete CREATE result containing stable Definition + v1
application candidates/selectors that preserve omission intent
```

Use one canonical version-status authority. Reuse or move the delivered plain-domain `VersionStatus` only if this preserves a single unambiguous semantic owner and does not introduce persistence/transport coupling.

## 5.1 Exact identity and allocation

```text
exact identity = (relationship_definition_id, version)
version > 0
version local to one Definition
no version UUID
max(current existing versions) + 1
version gaps allowed
highest deleted DRAFT number may be reused later
multiple concurrent DRAFT versions allowed
no persisted derived_from/source/provenance field
```

## 5.2 Lifecycle

```text
DRAFT -> PUBLISHED -> DEPRECATED
```

Rules:

```text
DRAFT
    mutable only through complete REVISE
    positive revision

PUBLISHED / DEPRECATED
    immutable

expected_revision required for
    REVISE
    PUBLISH
    DELETE_DRAFT

PUBLISH / DEPRECATE
    do not increment revision

lifecycle commands
    are not idempotent state setters
```

Missing exact URI targets are `resource_not_found`; missing body operands such as CREATE_NEXT source are `referenced_resource_not_found`; stale generation and lifecycle/source/default/dependency failures use the exact frozen finite code catalog.

## 5.3 CREATE and CREATE_NEXT

RelationshipDefinition CREATE atomically creates:

```text
stable Definition header
complete certified Resolution set
v1 DRAFT revision 1
complete canonical initial declaration set
default_version = null
```

Omitted initial properties means exact `[]`, not an absent version resource.

CREATE_NEXT:

```text
accepts exact same-Definition PUBLISHED or DEPRECATED source
rejects DRAFT source
clones the complete declaration snapshot exactly
retains exact historical DTV pins
creates one new DRAFT revision 1
does not change stable topology or default
does not persist source provenance
```

A cloned DTV may now be DEPRECATED. The clone remains a valid persisted DRAFT candidate, but final publication is blocked until every direct dependency is PUBLISHED.

## 5.4 REVISE and publication history

REVISE is complete semantic replacement:

```text
properties member required
[] means exact empty schema
request order non-semantic
position is the ordering authority
successful REVISE increments revision exactly once
equal canonical replacement still increments revision
stable topology is unchanged
```

Every persisted DRAFT must remain well formed.

Publication re-certifies the complete property history after waits. Implement the exact frozen historical semantics, including:

```text
editorial freedom before first publication
semantic key = (relationship_definition_id, name)
name and datatype lineage stable after publication
exact DTV may evolve according to the owning rules
position may change
SCALAR -> LIST allowed
LIST -> SCALAR forbidden
remove/re-add retains historical identity and constraints
out-of-order publication cannot commit a non-serial history
```

Do not invent stronger or weaker rules from convenience. Re-read the owning Relationship architecture for every history predicate.

---

# 6. Relationship property declarations and canonical factual values

One exact RDV declaration contains only:

```text
name
position
datatype_id
datatype_version
value_mode
```

## 6.1 Declaration rules

```text
name
    [a-z][a-z0-9_]{0,63}

position
    positive
    unique within one exact RDV

value_mode
    SCALAR | LIST

datatype binding
    exact persisted (datatype_id, datatype_version)
```

All Relationship properties are optional.

```text
absent property
    valid

present concrete canonical value
    valid when exact DTV accepts it

present JSON null
    invalid
```

There is no Relationship property required flag, nullable flag, create default or migration default.

## 6.2 Explicit versus default DTV selection

Application and API candidates must distinguish:

```text
datatype_version omitted
    -> deliberately resolve current DataType.default_version

explicit positive datatype_version
    -> select that exact version

explicit null
    -> invalid_request
```

Every new or rebound selection must target a PUBLISHED DTV through commit. Persist the resolved exact pin; never store a floating default/latest/highest reference.

Historical clone lifetime uses the S00 frozen `KS` rule and does not require the target to remain PUBLISHED. Every persisted declaration still protects physical DTV lifetime.

## 6.3 Factual property canonicalization

For factual CREATE, validate a complete property object against the selected exact RDV and exact DTVs:

```text
unknown property
    invalid semantic candidate

JSON null
    invalid

SCALAR declaration
    one canonical PrimitiveType value

LIST declaration
    non-empty ordered values
    every item canonical under the exact DTV

empty optional LIST
    canonical property absence

omitted properties body field
    {}
```

Reuse the delivered PrimitiveType lexical/canonical contract. Do not create a second value parser, JSON Schema authority or persistence-level semantic validator.

Factual properties are shared fact-level state. They never belong to individual Resolution or runtime-closure rows.

---

# 7. Differential RDV declaration persistence

Create a dedicated persistence boundary for exact RDV headers/declarations/history/dependency reads, or an equally clear decomposition preserving the conceptual ownership in the frozen persistence architecture.

Stores use the caller-owned connection and never commit, open nested transactions or retry fragments.

REVISE must be semantically complete replacement but physically differential:

```text
load complete current set
resolve complete desired set
classify unchanged / removed / replaced / new
leave unchanged rows untouched
delete removed/replaced rows in deterministic PK/name order
delete every replaced row before any replacement insert
insert replaced/new rows in deterministic PK/name order
increment revision only after all child DML succeeds
commit atomically
```

Any persisted-field change, including `position`, makes the row physically replaced. Position swaps must succeed without a transient UNIQUE violation.

Target-lock rules are exact:

```text
new or rebound exact DTV
    -> target header KS + exact DTV S

same exact DTV reinserted only because another field changed
    -> target header KS + exact DTV KS

unchanged row
    -> no target lock and no child DML

removed row
    -> no outgoing target lock
```

Add forced-failure evidence proving complete rollback of declarations and revision (`ATOMIC-05`). Do not weaken atomicity tests by moving injection before real child DML.

Batch or otherwise bound dependency/history reads. Do not introduce preventable per-declaration N+1 behavior.

---

# 8. Model-plane application and lock plans

Every mutation follows the completed S00 planner discipline. Extend the central row target registry so `RowLockClass.RELATIONSHIP_DEFINITION_VERSION` has one exact single-table PostgreSQL lock statement over the new table.

Do not call old store `lock_*` helpers from application code and do not hand-code acquisition order.

Implement exactly these plans and fresh rereads:

## 8.1 Definition CREATE

```text
RELATIONSHIP_DEFINITION_CONFLICT_GATE
endpoint ObjectTemplate headers KS
initial declaration DTV targets using explicit/default binding rules
fresh post-gate certified topology and dependency recheck
stable Definition + complete Resolutions + v1 + declarations
```

The candidate must be completely valid and globally certified before current-state DML. One failure leaves no partial Definition, Resolution, v1 or declaration.

## 8.2 Definition RENAME

Preserve the completed S00 behavior:

```text
RELATIONSHIP_DEFINITION_CONFLICT_GATE first
Definition header KS
fresh complete aggregate/certified-set read
complete deterministic Resolution-name update
```

Rename changes no version/default/property/factual state.

## 8.3 RDV CREATE_NEXT

```text
cloned DTV targets KS
Definition header NKU
exact source RDV KS
fresh source/version-set read
fresh max(existing)+1
```

If optimistic discovery no longer describes the plan, restart the whole UoW. Do not append locks.

## 8.4 RDV REVISE

```text
desired declaration DTV targets using differential rules
Definition header KS
exact DRAFT RDV NKU
fresh DRAFT/revision/declarations/history/dependency reread
```

## 8.5 RDV PUBLISH

```text
direct DTV headers KS and exact versions S
Definition header NKU
exact DRAFT RDV NKU
fresh generation, complete history and dependency certification
status transition + first-default-if-null in one UoW
```

No PUBLISHED RDV may commit with a non-PUBLISHED direct DTV dependency.

## 8.6 Default, deprecate and delete-DRAFT

```text
SET_DEFAULT
    Definition H NKU
    exact target RDV S

CLEAR_DEFAULT
    Definition H NKU

DEPRECATE
    Definition H S
    exact target RDV NKU
    current default blocks deprecation

DELETE_DRAFT
    Definition H NKU
    exact DRAFT RDV U
    pure declaration removal takes no outgoing DTV lock
```

Re-read exact status/revision/default after waits.

## 8.7 Whole Definition DELETE

```text
MODEL_ROOT_DELETE_GATE
Definition H U
fresh complete aggregate and blocker read
transactional default clear
root delete
owned Resolution/RDV/property CASCADE
current factual Relationship RESTRICT arbitration
```

The default clear and root deletion are one atomic operation. A later failure rolls the clear back. Root deletion never cascades factual Relationships, endpoint ObjectTemplates, DTVs or history.

## 8.8 Active DTV consumer semantics

Extend DataTypeVersion deprecation admission so a PUBLISHED RDV direct property dependency is an active consumer.

```text
PUBLISHED RDV dependency
    blocks DTV deprecation

DRAFT or DEPRECATED RDV dependency
    does not block
```

The deprecator owns the DTV and performs a non-locking reverse-consumer scan. It must not lock consumer rows or invert dependency/consumer order. Consumer removal may allow success or a conservative conflict according to the frozen matrix.

---

# 9. Model-plane reads, capability and corruption boundary

Implement coherent transport-neutral reads for:

```text
RelationshipDefinition GET / list
RelationshipDefinitionVersion exact GET
RelationshipDefinitionVersion summary list
Relationship capability collection
```

## 9.1 Stable Definition projection

Return exactly:

```text
id
symmetric
default_version
complete resolutions ordered by resolution_id
```

Do not inline versions or property declarations.

## 9.2 Exact version projection

Full exact RDV:

```text
relationship_definition_id
version
revision
status
properties ordered by position
```

Summary:

```text
relationship_definition_id
version
revision
status
```

Version list is ordered by version, supports exact status filter, opaque cursor and limit rules, and distinguishes a missing path Definition from an empty matching page.

## 9.3 Capability predicate and shape

A capability item appears only when:

```text
Resolution topologically applicable
AND
its Definition owns at least one PUBLISHED RDV
```

A null default does not suppress explicit capability.

Return one item per applicable Resolution, ordered by `resolution_id`, containing exactly:

```text
resolution_id
relationship_definition_id
name
from_template_id
to_template_id
default_version
```

Do not multiply rows by version count and do not inline version summaries, declarations or counts. Use an efficient `EXISTS`/equivalent query and preserve cursor identity.

## 9.4 Uniform default-pointer validation

For every stable DataType, ObjectTemplate and RelationshipDefinition GET/list projection that observes a non-null `default_version`, validate in the same coherent read snapshot that the target:

```text
exists
belongs to the same lineage/Definition
is PUBLISHED
```

Missing, cross-lineage, DRAFT or DEPRECATED default is persisted corruption:

```text
500 internal_error
no fallback
no repair
no pointer clearing
no latest/highest substitution
```

Collection/page validation must fail the complete result, not return partial items. Use bounded/batched validation and do not introduce one query per row.

---

# 10. Factual Relationship S01 delta

S01 changes the delivered factual CREATE/GET/DELETE baseline. It does not add DATA_CHANGE or SCHEMA_CHANGE.

## 10.1 Persisted factual state

Every current Relationship owns:

```text
id
relationship_definition_id
relationship_definition_version
properties
complete delivered deterministic runtime closure
```

A current pin is PUBLISHED or DEPRECATED, never DRAFT. New CREATE may bind only to PUBLISHED.

Exact pin and properties appear once on the factual header and are never duplicated on runtime closure rows.

## 10.2 CREATE selection and validation

Public/application CREATE accepts:

```text
resolution_id
from_object_id
to_object_id
optional relationship_definition_version
optional complete properties
```

Selection semantics:

```text
explicit version
    -> exact same-Definition PUBLISHED RDV
    -> Definition H KS + target RDV S

version omitted
    -> resolve Definition.default_version once
    -> Definition H S + target RDV S

explicit null
    -> invalid_request

omitted properties
    -> {}

explicit properties null
    -> invalid_request
```

After locks, re-read Definition/default/RDV/endpoints and rederive the full candidate. No latest/highest fallback.

Validate endpoint, RDV and complete canonical property candidate **before** factual uniqueness classification. An invalid candidate must not become a duplicate/conflict solely because a similar fact exists.

Preserve stable factual identity, symmetric/non-symmetric uniqueness, self-loop semantics, endpoint lineage admission and deterministic complete closure exactly as delivered.

## 10.3 New conflict semantics

M2 does not retain successful duplicate convergence.

```text
unoccupied valid semantic fact
    -> create one new factual identity
    -> 201

same fact or required exact runtime view already current
    -> relationship_fact_conflict
    -> bounded current relationship_id detail
    -> no current-state mutation
    -> no lifecycle event
```

Update the S00 exact-view collision classification accordingly:

```text
failed candidate UoW rolls back completely
fresh classification UoW locks every current factual owner with Relationship KS
owner set is reread and validated while held
current owner -> relationship_fact_conflict
owner disappeared/expanded -> approved bounded whole-UoW restart
```

Do not reintroduce M1 convergence, a global Relationship gate, an unbounded retry or a success body for the loser.

## 10.4 CREATE lifecycle

A new fact writes one complete deterministic CREATED event set atomically with header and closure.

Each distinct Object-relative semantic view receives one row. Historical factual transition shape is:

```text
before = null
after = {
    relationship_definition_version,
    properties
}
```

No loser event survives a collision.

## 10.5 GET and Object-relative projections

Relationship GET returns exactly:

```text
id
relationship_definition_id
relationship_definition_version
properties
views ordered by (object_id, destination_object_id, name)
```

Object-relative Relationship items add:

```text
relationship_definition_version
properties
```

while preserving item identity/order/cursor:

```text
(relationship_id, destination_object_id, name)
```

Mutable pin/properties do not enter cursor identity.

Use a coherent `REPEATABLE READ READ ONLY` UoW for multi-statement aggregate validation. Validate the exact RDV/declarations/DTVs, canonical properties, closure and endpoint lineage state. One corrupt fact fails the complete aggregate/page with `internal_error`; do not repair or return partial output.

## 10.6 DELETE

DELETE targets one exact Relationship UUID.

```text
current exact ID
    -> Relationship U
    -> fresh complete aggregate/state/metadata read
    -> delete header + owned closure
    -> append complete DELETED event set
    -> 204

absent exact ID
    -> resource_not_found / 404
    -> no event
```

DELETED historical factual state is:

```text
before = {
    relationship_definition_version,
    properties
}
after = null
```

Two concurrent same-ID deletes produce one real 204 transition/event set and one 404 waiter. A late delete for old UUID X never removes a later equivalent UUID Y.

Forced event failure must roll back the factual header and complete closure (`ATOMIC-03`).

---

# 11. HTTP and DTO contract

Use strict Pydantic 2 transport models only at the HTTP boundary. Preserve caller omission distinctly from explicit null and map explicitly into ordinary application candidates.

Unknown fields are forbidden. Unknown/repeated query parameters remain rejected. Positive integers reject booleans, zero, negative and malformed path/query lexical forms. No-body commands reject every non-empty body, including `{}`.

## 11.1 RelationshipDefinition CREATE

Retain delivered topology discriminators and add optional top-level `properties`.

```text
properties omitted -> []
properties = []    -> exact empty v1 schema
properties = null  -> invalid_request
```

Caller cannot supply IDs, version, revision, status or default.

Success:

```text
201 Created
Location: /api/v1/core/relationship-definitions/{id}
body: {
    relationship_definition: <stable DTO>,
    version: <full exact v1 DTO>
}
```

## 11.2 Exact RDV routes

Implement exactly:

```text
POST   /api/v1/core/relationship-definitions/{id}/create-next
POST   /api/v1/core/relationship-definitions/{id}/set-default
POST   /api/v1/core/relationship-definitions/{id}/clear-default
POST   /api/v1/core/relationship-definitions/{id}/versions/{version}/revise
POST   /api/v1/core/relationship-definitions/{id}/versions/{version}/publish
POST   /api/v1/core/relationship-definitions/{id}/versions/{version}/deprecate
DELETE /api/v1/core/relationship-definitions/{id}/versions/{version}
GET    /api/v1/core/relationship-definitions/{id}/versions
GET    /api/v1/core/relationship-definitions/{id}/versions/{version}
```

Exact carriers/statuses:

```text
CREATE_NEXT
    body exactly {source_version}
    201 + exact nested Location

REVISE
    required expected_revision query
    body exactly {properties: [...]}
    200

PUBLISH
    required expected_revision query
    no body
    200

DEPRECATE
    no body/query
    200

DELETE_DRAFT
    required expected_revision query
    no body
    204

SET_DEFAULT
    body exactly {version}
    200 stable Definition DTO

CLEAR_DEFAULT
    no body/query
    200 stable Definition DTO
```

Property request contains exactly:

```text
name
position
datatype_id
optional non-null datatype_version
value_mode
```

## 11.3 Stable Definition routes

Preserve/create exact behavior for:

```text
POST   /relationship-definitions
POST   /relationship-definitions/{id}/rename
DELETE /relationship-definitions/{id}
GET    /relationship-definitions
GET    /relationship-definitions/{id}
```

Stable DTO adds `default_version` and never inlines versions.

## 11.4 Factual routes in S01

Implement/update only:

```text
POST   /api/v1/core/relationships
GET    /api/v1/core/relationships/{relationship_id}
DELETE /api/v1/core/relationships/{relationship_id}
```

Do not add the S02 DATA_CHANGE/SCHEMA_CHANGE routes.

CREATE success is always `201` with exact `Location`. Duplicate is `409 relationship_fact_conflict`, never `200` convergence. DELETE absent is `404`, never idempotent `204`.

Update Object-relative Relationship and lifecycle projections required by the new factual state, without adding a standalone Relationship timeline.

## 11.5 Failure mapping

Use only the frozen 23-code catalog. Do not introduce a new public code.

At minimum preserve exact distinctions for:

```text
invalid_request
invalid_cursor
resource_not_found
referenced_resource_not_found
semantic_validation_failed
stale_revision
lifecycle_state_conflict
version_source_conflict
default_version_unavailable
dependency_not_admissible
default_version_conflict
active_dependency_conflict
delete_blocked
relationship_definition_equivalent
relationship_definition_conflict
relationship_fact_conflict
internal_error
```

`relationship_fact_conflict.details` contains the bounded current `relationship_id`. `delete_blocked` contains bounded blocker type/count entries. No SQLSTATE, constraint, SQL, table, column, driver, URL, credential or stack detail may cross the public boundary.

---

# 12. Historical carrier and lifecycle discipline

The fresh durable baseline admits canonical M2 history only. Do not retain a permanent M1/M2 dual decoder or synthetic backfill.

Implement the minimum shared historical runtime-property carrier validation needed by S01 CREATED/DELETED factual snapshots while preserving every delivered Object/ownership event shape.

The historical Relationship factual snapshot has exact keys:

```text
relationship_definition_version
properties
```

Validate it self-containedly:

```text
positive non-boolean version
canonical property-name grammar
canonical JSON carrier shape
no live RDV/DTV lookup during historical decode
```

The final table vocabulary may include future S02 Relationship kinds, but S01 must not create those transitions or expose their mutation routes.

Current-state semantic validation remains against live exact RDV/DTV state. Historical decoding never infers current schema, repairs values or follows live defaults.

---

# 13. Required deterministic evidence

Implement and machine-map all primary S01 bundles:

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

Each bundle must have concrete, collected targets for every required layer. Do not mark a bundle PASS from one cheap surrogate.

## 13.1 Required scenario set

Implement or update deterministic real-PostgreSQL targets for all applicable S01 scenarios:

```text
ROW-18
ROW-19
ROW-20
ROW-21
ROW-22
ROW-23
ROW-24
ROW-25
ROW-30 factual CREATE variants only

ARB-05
ARB-06
ARB-07
ARB-08

REF-03
REF-04
REF-07
REF-09

ATOMIC-02
ATOMIC-03
ATOMIC-05
```

Preserve stable scenario IDs. Update delivered ARB behavior only through the explicit M2 delta:

```text
ARB-05 current winner -> relationship_fact_conflict
ARB-06 same-ID delete waiter -> resource_not_found / 404
ARB-07 current winner -> conflict; disappeared winner -> bounded restart
ATOMIC-02 loser classification -> conflict after complete rollback
ATOMIC-03 second successful-delete semantics -> 204/404
```

Do not implement ROW-26..29 or the DATA_CHANGE/SCHEMA_CHANGE portions of ROW-30; those belong to S02.

## 13.2 Required scenario properties

Evidence must prove, among other required assertions:

```text
serial RDV version allocation and max/source reread
one exact generation consumer for revise/publish/delete
first-default and deprecation races
complete historical recertification
explicit/default DTV binding through commit
PUBLISHED RDV active-consumer rendezvous
CREATE endpoint and Definition lifetime
clone and differential declaration target lifetime
one factual winner, conflict loser and no loser event
partially overlapping closure arbitration
exact-ID 204/404 delete and ABA safety
complete child/header/event rollback
absence of supported-path 40P01
```

Use independent PostgreSQL sessions and the canonical REC-LOCK, REC-UNIQUE, REC-FK, REC-ROLLBACK, REC-ABA and progress/gate recipes. Use `pg_blocking_pids()` for positive blocking. Timeouts are hang guards only. Do not use sleep-based scheduling, generic reruns or stress as normative proof.

## 13.3 Schema and migration evidence

For M2-VER-20/21, machine-check exact positive and negative inventories:

```text
15 tables exactly
columns and PostgreSQL types
named PK / UNIQUE / CHECK / FK
ON DELETE actions
explicit index names/keys/order/include/predicates
forbidden index absence
one root/base/head
old revisions absent
compare_metadata == []
head/base/repeatability/sentinel/failure rollback
```

## 13.4 Domain, application and HTTP evidence

Add focused T0/T1/T4 tests for:

```text
RDV lifecycle/generation/history
property declaration candidates and omission/null
factual property canonicalization
strict bodies/queries/no-body commands
exact success body/status/Location
exact finite failures and bounded details
version-list filter/order/cursor
capability membership/default projection
coherent default-pointer corruption failures
factual GET/Object-relative projection
CREATED/DELETED factual snapshots
```

Use Hypothesis where it materially strengthens property-map canonicalization, history/evolution or cursor binding. Do not use it as a substitute for concrete public and PostgreSQL examples.

---

# 14. Traceability and AS-IS regression discipline

Create or extend one machine-checkable M2 traceability registry in a test-only module.

It must contain the full frozen identifier census and concrete S01 mappings, including:

```text
M2-OUT-01 ... M2-OUT-16
M2-AC-01 ... M2-AC-32
M2-VER-01 ... M2-VER-32
canonical 83 scenario IDs
S01 evidence target maps
S01 route/schema delta maps
```

For future bundles not yet implemented, represent their state honestly as DESIGNED rather than inventing dummy tests or claiming PASS. Every S01 bundle and scenario target must resolve to a real collected test.

Preserve the completed S00 PLAN registry and evidence. Do not orphan or silently rename `PLAN-01 ... PLAN-06`.

Existing tests are evidence, not semantic authority. Apply this rule:

```text
existing test matches preserved AS-IS or frozen S01 requirement
    -> fix implementation; do not weaken test

existing test asserts an M1 behavior explicitly changed by frozen M2
    -> update it to the exact M2 delta while preserving stable identity/evidence

unclear whether test or implementation is wrong
    -> re-read owning authorities; stop on unresolved contradiction
```

All delivered guarantees outside the explicit S01 delta remain passing, including topology, Resolution identity, closure derivation, endpoint lineage admission, failure classes, bounded details, pagination and no internal leakage.

Do not delete deterministic scenario coverage merely because the schema or lock cut changed. Re-anchor the test to the frozen mechanism.

---

# 15. Toolchain and implementation discipline

Use only the ratified baseline:

```text
CPython 3.14.x
native asyncio
uv with committed uv.lock
SQLAlchemy Core 2.x
Psycopg 3
Alembic
FastAPI / Pydantic 2
pytest / pytest-asyncio
HTTPX ASGITransport for API tests
Hypothesis where justified
real PostgreSQL through TEST_DATABASE_URL
Ruff
Pyright strict
```

Do not use:

```text
SQLAlchemy ORM Session / AsyncSession
SQLite
Docker
Testcontainers
sleep-based concurrency orchestration
SERIALIZABLE as a substitute for the planner
new advisory gates
new retry middleware
generic ON CONFLICT DO NOTHING aggregate writes
new dependency for convenience
global Ruff/Pyright relaxation
broad warning/error suppression
GitHub Actions
```

Application/domain modules remain free of FastAPI, Pydantic, SQLAlchemy and Psycopg imports. Transport DTOs do not become domain models. Persistence rows do not cross the API boundary.

Keep local suppressions narrow and justify each one in the handoff.

Avoid preventable N+1 paths in declarations, history certification, default validation, capability queries and aggregate/page reads. No quantitative latency SLA is defined, but bounded deliberate query paths are mandatory.

---

# 16. Required verification commands

Run focused gates first, then the complete repository gate. Report exact commands, pass/fail counts and durations where available.

At minimum run the concrete repository equivalents of:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright

# focused pure/domain/application evidence
uv run pytest -q <RDV domain/application/property targets>

# focused HTTP contract evidence
uv run pytest -q <RelationshipDefinition/RDV/Relationship S01 API targets>

# migration/schema targets on real PostgreSQL
uv run pytest -q <M2-VER-20 and M2-VER-21 targets>

# focused S01 PostgreSQL concurrency/atomicity
uv run pytest -q <ROW-18..25, ROW-30 CREATE, ARB-05..08,
                  REF-03, REF-04, REF-07, REF-09,
                  ATOMIC-02, ATOMIC-03, ATOMIC-05 targets>

# all PostgreSQL concurrency
uv run pytest -q -m "postgresql and concurrency" -ra

# all non-PostgreSQL regressions
uv run pytest -q -m "not postgresql" -ra

# complete repository suite, including PostgreSQL-marked tests
uv run pytest -q -ra
```

Also execute explicit migration graph/introspection commands or tests proving one base/head and report the exact PostgreSQL server version used.

The final full suite must include PostgreSQL-marked tests. Collection, static compilation or a non-PG-only run is not the complete gate.

Report explicitly:

```text
CPython version
PostgreSQL server version
M2-VER-01..07 / 10 / 20 / 21 result individually
assigned scenario result individually or by exact target registry
schema drift result
one-base/one-head result
skips / xfails / reruns census
whether any supported path returned SQLSTATE 40P01
```

No unexplained skip, xfail, flaky rerun or generic retry is permitted for normative S01 evidence.

If `TEST_DATABASE_URL` becomes unavailable or any mandatory real-PG gate is blocked/failing:

```text
implement only what can be verified honestly
leave M2-S01 IN PROGRESS
record the exact blocker/finding in status.md
push only if the partial candidate is useful and explicitly labelled
never claim CANDIDATE READY FOR REVIEW
```

Do not fabricate evidence or substitute another backend.

---

# 17. Documentation and status discipline

Do not modify the frozen M2 contract, architecture or `steps.md` to fit implementation.

Do not rewrite the delivered AS-IS as if the unreviewed M2 candidate were already delivered.

Do not create M2 final-delivery acceptance evidence or begin AS-IS consolidation.

Keep this prompt in `docs/milestones/M2/wip/` until it is superseded or the reviewer accepts S01. Do not delete it in the implementation candidate.

Update `docs/milestones/M2/status.md` only with verified operational facts:

```text
implementation begins
    -> M2-S01 IN PROGRESS

implementation or any mandatory verification incomplete/failing
    -> M2-S01 IN PROGRESS
    -> record exact open finding/blocker

all S01 implementation and mandatory gates pass,
candidate committed and pushed
    -> M2-S01 CANDIDATE READY FOR REVIEW
    -> reviewer decision pending
```

Never mark:

```text
M2-S01 COMPLETED
M2 DELIVERED
review ACCEPTED
```

Those states are reviewer/human-owned.

Do not open `M2-S02`.

Commit-specific execution evidence may be recorded under `docs/milestones/M2/evidence/` when useful, but it must contain verified facts and must not become a competing semantic authority.

---

# 18. Git and publication discipline

Before publication:

```text
review the complete diff from d225faee...
review staged diff
exclude unrelated changes
verify no secret or database URL is present
verify obsolete Actions/payload material remains absent
verify this active prompt remains present
verify old disposable migration revisions are absent
verify exactly one durable revision graph exists
run git diff --check
```

Use one or more intentional coherent commits. Suitable titles include:

```text
db(m2-s01): establish durable kernel baseline
feat(m2-s01): add versioned relationship model plane
test(m2-s01): complete assigned acceptance evidence
```

Do not split the work in a way that leaves a published commit claiming a ready candidate while schema, API or evidence are incomplete.

Push normally to:

```text
origin/M2
```

After push verify:

```text
local HEAD SHA
origin/M2 SHA
local/remote synchronization
working tree clean
```

Do not create a PR, merge, force-push, tag or release.

---

# Completion report

At the end provide a reviewer-oriented handoff containing only verified facts:

- cycle `M2`, slice `M2-S01`, branch `M2`;
- candidate commit SHA(s);
- push, local/remote synchronization and working-tree state;
- concise changed-file/category inventory;
- final fifteen-table census;
- new/changed table, constraint and index summary;
- exact negative-index inventory result;
- durable revision ID, base/head census and old-revision removal;
- migration transition, sentinel, rollback and metadata-drift results;
- RDV domain/application lifecycle summary;
- property declaration, historical continuity and differential-DML summary;
- exact lock plans and active DTV dependency realization;
- stable Definition/version/default/capability read behavior;
- uniform DT/OT/RD default-pointer validation result;
- factual Relationship CREATE/GET/DELETE exact-pin/property changes;
- duplicate CREATE conflict and missing DELETE behavior;
- CREATED/DELETED factual lifecycle snapshot result;
- exact S01 HTTP route/DTO/status/Location/failure result;
- exact target/result for every `M2-VER-01..07`, `10`, `20`, `21`;
- exact assigned scenario results;
- complete quality/test commands, counts and durations;
- CPython and PostgreSQL versions;
- full-suite result and explicit supported-path `40P01` result;
- skip/xfail/rerun census;
- schema/migration changes: expected and described;
- dependency/lockfile changes: expected `none`;
- confirmation that no M1 bridge/backfill/stamp/dual decoder exists;
- confirmation that no S02 DATA_CHANGE/SCHEMA_CHANGE, Health, CLI or startup capability was introduced;
- confirmation that Actions/payload material remains absent;
- every unexecuted requirement and exact reason;
- every residual risk or architecture/documentation finding;
- final `status.md` state without claiming reviewer-owned completion.

Use the wording:

```text
M2-S01 candidate implemented and ready for reviewer inspection
```

only when every mandatory S01 gate has passed against real PostgreSQL and the candidate has been pushed.