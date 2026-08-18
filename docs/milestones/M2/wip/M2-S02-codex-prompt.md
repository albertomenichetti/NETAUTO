# Codex implementation prompt — M2-S02

**Status:** NON-NORMATIVE IMPLEMENTATION PROMPT.

This file is an execution aid for Codex. It narrows the authorized implementation task but does not override `AGENTS.md`, the delivered AS-IS, the FINAL/FROZEN M2 contract, architecture or steps, the active milestone status, or the ratified technology baseline.

## Assignment

Implement exactly:

```text
M2-S02 — Factual Relationship mutations, lifecycle and coherent reads
```

Work directly on branch:

```text
M2
```

The reviewer-owned implementation baseline is:

```text
24e7b788b6b7f54d96614ef2c37bffbeb25ebd8b
docs(m2): accept S01 and open S02
```

Start from the current `origin/M2` tip containing this prompt. That tip must be `24e7b788...` or a direct descendant. Do not reset, rebase, force-push or rewrite the published S00/S01 history.

Current authorization is:

```text
M2-S00    reviewer-owned COMPLETED
M2-S01    reviewer-owned COMPLETED
M2-S02    READY, authorized
M2-S03    BLOCKED
```

The publication action is:

```text
perform the mandatory repository pre-flight
implement M2-S02 vertically and completely
add permanent deterministic evidence
run every focused and complete mandatory gate
commit intentionally
push normally to origin/M2
verify local/remote synchronization and a clean working tree
publish an M2-S02 candidate for reviewer inspection
```

Do not create a pull request. Do not merge to `master`, force-push, rewrite published history, tag or release.

Do not add or use GitHub Actions, workflow-dispatched implementation, CI-driven commits, encoded patches or artifact-mediated source publication.

---

# 1. Mandatory pre-flight

Before modifying code, tests, status or evidence, read and obey at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

# Current delivered AS-IS
docs/architecture/README.md
docs/architecture/object.md
docs/architecture/relationship.md
docs/architecture/persistence.md
docs/architecture/api.md
docs/architecture/concurrency-matrix.md
docs/architecture/concurrency.md
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
docs/milestones/M2/steps.md
docs/milestones/M2/status.md

# Active execution aid
docs/milestones/M2/wip/M2-S02-codex-prompt.md
```

Read owning sections dependency-first. Frozen documents are authority. This prompt is only an execution aid. Do not derive implementation requirements from historical discovery or cross-check files under `docs/milestones/M2/wip/`; `architecture/provenance.md` removes those files from implementation authority.

Confirm from the repository itself that:

```text
checked-out branch                  = M2
README active cycle                 = M2 / IMPLEMENTATION / branch M2
origin/M2 ancestry                  includes 24e7b788...
M2 contract                         = FINAL / FROZEN
M2 architecture set                 = FINAL / FROZEN
M2 steps                            = FINAL / FROZEN
M2-S00                              = reviewer-owned COMPLETED
M2-S01                              = reviewer-owned COMPLETED
M2-S02                              = READY or IN PROGRESS
M2-S03                              = BLOCKED
relevant architecture reopen        = none
STACK-01 ... STACK-10               = RATIFIED
```

Inspect at least these implementation boundaries before editing:

```text
src/netauto/domain/primitives.py
src/netauto/domain/objects.py
src/netauto/domain/relationships.py

src/netauto/application/objects.py
src/netauto/application/relationships.py
src/netauto/application/relationshipdefinitions.py

src/netauto/persistence/uow.py
src/netauto/persistence/locking.py
src/netauto/persistence/metadata.py
src/netauto/persistence/objects.py
src/netauto/persistence/relationships.py

src/netauto/entrypoints/api/common.py
src/netauto/entrypoints/api/errors.py
src/netauto/entrypoints/api/objects.py
src/netauto/entrypoints/api/relationships.py
src/netauto/entrypoints/http.py

 tests/test_relationship_domain.py
 tests/test_relationship_api.py
 tests/test_relationshipdefinition_api.py
 tests/test_relationship_semantic_concurrency.py
 tests/test_m2_s01_semantic_concurrency.py
 tests/test_m2_traceability.py
 tests/support/semantic_concurrency.py
 tests/support/pg_harness.py
```

Search the complete repository for all lifecycle readers/writers, `EventKind`, `LifecycleEvent`, `RelationshipFactualState`, `object_lifecycle_events`, `insert_intrinsic_event`, `insert_ownership_event`, `insert_lifecycle_events`, `lifecycle_views`, `list_events`, `Relationship(...)` and `ObjectRelationshipView(...)` construction sites. The list above is not exhaustive.

Verify the accepted S01 baseline before changing it:

```text
durable revision                    = 0001_m2_kernel
Alembic graph                       = one base / one head
authoritative table census          = exactly 15
metadata drift                      = []
Relationship CREATE/GET/DELETE      = complete S01 behavior
factual exact RDV pin               = required and persisted
factual properties                  = canonical JSONB
S01 review-fix registries           = present and passing
```

Also verify that obsolete S00 implementation material remains absent:

```text
.github/m2-s00-payload/
.github/workflows/materialize-verify-m2-s00.yml
.github/workflows/export-m2-worktree.yml
```

A valid externally supplied real PostgreSQL target through `TEST_DATABASE_URL` is mandatory for a complete S02 candidate. Verify availability during pre-flight. Do not provision PostgreSQL, use Docker/Testcontainers, invent credentials, fall back to localhost, fall back to `NETAUTO_DATABASE_URL`, or substitute SQLite.

If README, branch, `status.md`, frozen authorities, candidate ancestry or required infrastructure disagree, stop before modifying the affected work and report the mismatch. If normative authorities conflict or do not determine one material behavior, stop only the affected point and report an architecture/documentation finding. Do not silently choose a convenient interpretation.

Code, tests, Git history, candidate reports and this prompt are evidence or execution aids, not semantic authority.

---

# 2. Slice scope and hard boundary

M2-S02 is a vertical business slice. It is not satisfied by route scaffolding, DTOs, store methods or test placeholders alone.

## 2.1 Explicitly in scope

```text
Relationship.DATA_CHANGE domain/application/persistence/HTTP behavior
Relationship.SCHEMA_CHANGE domain/application/persistence/HTTP behavior

one shared lifecycle persistence boundary for all event families
shared historical runtime-property carrier codec
four factual Relationship transition writers
coherent Relationship/current-history reads
strict corruption-to-internal_error behavior

ROW-26
ROW-27
ROW-28
ROW-29
ROW-30 SCHEMA_CHANGE variants
REF-10 Relationship rebind variants
SNAP-05
ATOMIC-06
ATOMIC-07

M2-VER-08
M2-VER-09
M2-VER-11
M2-VER-12
M2-VER-13
M2-VER-14

exact public business-operation inventory after S02
machine-checkable S02 traceability
complete regression closure
```

## 2.2 Explicitly out of scope

Do not introduce or implement:

```text
M2-S03 complete 861-cell concurrency closure beyond S02-assigned evidence
Core Health
startup schema-revision guard
runtime settings or pool changes
CLI or REPL
packaging/Linux operating capability
native authentication, authorization or TLS termination
new advisory gates
new row-lock modes
new retry causes or generic retry middleware
Relationship endpoint mutation/reversal/move
bulk mutation, PATCH or generic action APIs
property-value search or runtime-property indexing
standalone Relationship lifecycle timeline
event-set resource or event_set_id
M1 -> M2 bridge, backfill, stamp path or dual decoder
```

No schema, migration, dependency or `uv.lock` change is expected or authorized for S02. S01 already installed the final 15-table schema, the final lifecycle vocabulary and the required current/history columns and checks.

The following must remain unchanged unless a genuine frozen-authority contradiction is discovered and reported before editing:

```text
src/netauto/persistence/metadata.py table/constraint/index meaning
src/netauto/migrations/ durable root graph
pyproject.toml dependency set
uv.lock
```

If a schema, migration or dependency change appears necessary, stop and identify the exact frozen authority requiring it. Do not modify the durable baseline merely to make an implementation convenient.

Do not modify the frozen contract, architecture or `steps.md` to fit code.

---

# 3. Shared correctness constraints

Every S02 path must preserve the completed S00/S01 foundation:

```text
one semantic mutation / one UoW / one connection / one transaction
READ COMMITTED mutation baseline
central prepare_lock_plan / LockPlan authority
three frozen transaction advisory gates only
four frozen PostgreSQL row-lock modes only
canonical class and intra-class order
gate before rows
one complete pre-DML acquisition phase
fresh protected reread after waits
no normal lock upgrade
no explicit post-DML lock
finite SQLSTATE + constraint-name classification
four total attempts only for the two frozen restart causes
no retry of 40P01 or 40001
one complete current-state + event-set commit or rollback
no SQL, constraint, table, column, URL, credential or stack leakage
```

Do not weaken existing tests to accommodate the implementation. Preserve every accepted S00/S01 behavior, including duplicate CREATE conflict, exact-ID DELETE 204/404, collision restart, exact factual pins, S01 blocker diagnostics, durable schema and all existing event snapshots.

Application/domain modules remain free of FastAPI, Pydantic, SQLAlchemy and Psycopg imports. Stores do not commit or open nested semantic transactions.

Avoid preventable N+1 queries. Correctness under concurrency must be proved with independent PostgreSQL sessions and deterministic orchestration. Sleep-only scheduling and generic reruns are forbidden.

---

# 4. Replace distributed lifecycle ownership with one LifecycleStore

The current S01 code already contains the final event enum and DTO shapes, but lifecycle ownership is still distributed:

```text
src/netauto/persistence/objects.py
    event types and codecs
    intrinsic/ownership event INSERT
    lifecycle page SELECT/decode

src/netauto/persistence/relationships.py
    Relationship metadata projection
    Relationship event batch INSERT
```

That is an intermediate implementation state, not the final S02 architecture.

## 4.1 Required boundary

Introduce one shared persistence authority, expected at:

```text
src/netauto/persistence/lifecycle.py
```

owned by a single `LifecycleStore` or an equivalent singular boundary.

It must own all of the following:

```text
EventKind
IntrinsicLifecycleEvent
OwnershipLifecycleEvent
RelationshipFactualState
RelationshipLifecycleEvent
LifecycleEvent union

shared historical runtime-property carrier validation
Object historical snapshot encode/decode
Relationship factual-state encode/decode
complete lifecycle row decode

intrinsic event insertion
ownership event insertion
Relationship metadata projection
Relationship event-set validation and batch insertion
lifecycle page query and decode
```

After the refactor:

```text
ObjectStore
    owns current Object and ownership persistence only

RuntimeRelationshipStore
    owns current factual Relationship header/closure persistence only

LifecycleStore
    owns every object_lifecycle_events read/write and historical codec
```

Current-state stores must not own separate lifecycle SQL. Add a static regression that prevents `object_lifecycle_events` DML/SELECT ownership from returning to `ObjectStore` or `RuntimeRelationshipStore`.

A thin import re-export is acceptable only when required to migrate internal imports without creating a second registry or codec. Duplicate implementations, copied validators or two independent event writers are forbidden.

Update all production and test imports to the final authority. Do not preserve a compatibility implementation merely because an old internal module path existed.

## 4.2 Shared historical property carrier

Use exactly one historical runtime-property carrier validator for Object and Relationship snapshots.

Allowed scalar carriers:

```text
string
integer, excluding boolean
boolean
```

Allowed LIST carrier:

```text
non-empty
ordered
homogeneous scalar carrier kind
```

Forbidden historical carrier state:

```text
JSON null
float
object/map as a property value
nested list
empty list
heterogeneous list
invalid property-name key
```

The decoder validates self-contained carrier integrity only. It never infers PrimitiveType from a string and never loads a live DataTypeVersion, ObjectTemplateVersion, RelationshipDefinitionVersion or current aggregate.

Relationship factual historical state has exactly these keys:

```text
relationship_definition_version
properties
```

`relationship_definition_version` is a positive non-boolean integer. Extra or missing keys are corruption.

The fresh durable baseline accepts only canonical M2 event shapes. Do not add a legacy or dual decoder.

## 4.3 Relationship metadata projection

Implement one SQL statement that joins the complete current runtime closure to:

```text
RelationshipResolution names
from Object canonical names
to Object canonical names
```

The result is the authoritative metadata observation for the complete transition event set and, for mutation responses, the current semantic `views` names.

Requirements:

```text
one statement snapshot
structural keys checked against the already validated closure
one semantic row per distinct Object-relative view
raw-row overlap deduplicated
non-empty complete view set
deterministic order:
    (object_id, destination_object_id, relationship_name)
```

A concurrent Object or Resolution rename may yield the coherent old generation, coherent new generation, or an independently committed combination that actually coexisted in that one statement snapshot. Mixed rows assembled from separate metadata statements are forbidden.

## 4.4 Relationship event writer

Implement one `insert_relationship_event_set`-style operation that accepts:

```text
kind
Relationship identity + stable Definition identity
validated before factual state or null
validated after factual state or null
complete unique semantic metadata views
```

It must enforce:

```text
RELATIONSHIP_CREATED
    before null
    after factual

RELATIONSHIP_DATA_CHANGE
    before and after factual
    same exact version
    different properties

RELATIONSHIP_SCHEMA_CHANGE
    before and after factual
    after version > before version
    properties may be equal

RELATIONSHIP_DELETED
    before factual
    after null
```

It validates the complete non-empty unique view set, sorts it deterministically and performs one batch INSERT. Event identity and timestamp remain database-generated UUID and `transaction_timestamp()`.

There is no `event_set_id`, no live FK, no `ON CONFLICT` behavior and no partial best-effort insert.

Refactor existing Relationship CREATE and DELETE to this same projection/writer. Refactor existing Object intrinsic and ownership transitions to the same `LifecycleStore` without changing their public semantics.

---

# 5. Relationship DATA_CHANGE

## 5.1 Public command semantics

Implement:

```text
POST /api/v1/core/relationships/{relationship_id}/data-change
```

Body:

```json
{
  "operations": [
    {"op": "SET", "property": "weight", "value": 10},
    {"op": "REMOVE", "property": "comment"}
  ]
}
```

Transport rules:

```text
operations required and non-empty
at most one operation per property
operation order non-semantic
SET exactly op + property + value
REMOVE exactly op + property; value forbidden
unknown fields forbidden
unknown or repeated query parameters forbidden
no expected_revision or schema selector
SET null is syntactically carried and fails semantic validation
```

Duplicate property operations and malformed request shape are `400 invalid_request`. Unknown properties, null values and values invalid under the pinned exact schema are `422 semantic_validation_failed` with bounded path/rule details.

Success is `200` with the current canonical factual Relationship DTO.

## 5.2 Domain/application behavior

DATA_CHANGE operates only under the already-pinned exact RDV.

It must:

```text
require current exact relationship_id
load and validate the complete factual aggregate
allow source RDV status PUBLISHED or DEPRECATED
apply SET/REMOVE to fresh current properties
validate/canonicalize the complete resulting map under the exact pinned schema
preserve stable Definition, exact pin and complete runtime closure
introduce no factual revision or expected_revision
```

Use or extract the delivered pure runtime-property mechanics where semantically equivalent. Do not reuse Object schema-migration rules that depend on declaring-template identity, required properties or migration defaults.

The direct application boundary must also reject an empty or duplicate operation set even when bypassing HTTP. Preserve the public `invalid_request` versus semantic-validation distinction.

## 5.3 Lock and write pipeline

Use exactly:

```text
factual Relationship owner = FOR NO KEY UPDATE
```

Pipeline:

```text
build complete plan
-> acquire Relationship NKU
-> fresh complete aggregate validation
-> derive complete canonical candidate
-> candidate == current:
       success
       no UPDATE
       no lifecycle event
-> real change:
       begin DML
       replace the complete properties JSONB in one owner-row UPDATE
       project metadata in one statement
       write complete RELATIONSHIP_DATA_CHANGE event batch
       commit
```

A no-op must not call the current-state UPDATE or Relationship event writer. A metadata read used solely to return a coherent response is allowed, but no event is emitted.

No-op examples include:

```text
SET whose canonical value equals current state
REMOVE of an already absent property
```

A real change event uses:

```text
before = same exact pin + old properties
after  = same exact pin + changed properties
```

The mutation response `views` must use one coherent current metadata observation; do not combine names from unrelated statements.

---

# 6. Relationship SCHEMA_CHANGE

## 6.1 Public command semantics

Implement:

```text
POST /api/v1/core/relationships/{relationship_id}/schema-change
```

Body:

```json
{"target_version": 3}
```

The body contains exactly one positive non-boolean `target_version`.

It accepts no:

```text
target Definition ID
default/latest/highest token
expected_revision
property overrides
remediation values
extra query parameters
```

Success is `200` with the migrated factual Relationship DTO.

Failure mapping:

```text
missing path Relationship
    -> 404 resource_not_found

missing exact target RDV command operand
    -> 422 referenced_resource_not_found
    -> resource_type, Definition id, target version

same/lower/non-forward target or invalid semantic candidate
    -> 422 semantic_validation_failed

existing target not PUBLISHED through admission
    -> 409 dependency_not_admissible

current information cannot be preserved
    -> 409 schema_change_blocked

persisted model/fact corruption
    -> 500 internal_error
```

`schema_change_blocked` exposes exactly one deterministic sufficient bounded blocker:

```text
relationship_id
target_version
blocker_type = property
member_name
```

Choose the blocker deterministically from target declaration order and name. Do not expose primitive exceptions, DTV identity, constraint names or raw values.

## 6.2 Target and source rules

Source is the fresh current exact factual pin and must be:

```text
PUBLISHED or DEPRECATED
```

Target must be:

```text
same stable RelationshipDefinition
exact target_version
strictly greater than source version
PUBLISHED through commit
```

Migration is direct source-to-target. Never consult:

```text
Definition default
latest/highest version
intermediate versions
```

Validate persisted source/target RDV structure, exact DTV dependencies and historical property continuity. A malformed persisted model is `internal_error`; it is not converted into a caller blocker.

## 6.3 Preserve-or-fail migration

Relationship property semantic identity is:

```text
(relationship_definition_id, property name)
```

For every target property:

```text
matching source property with a current value
    -> preserve the value
    -> wrap SCALAR as one-element LIST when target widens to LIST
    -> validate and canonicalize through target exact DTV
    -> any incompatibility blocks the complete migration

matching source property without a current value
    -> remain absent

new target property
    -> absent

source-only property
    -> removed
```

There is no migration default, caller remediation payload, implicit coercion or extras bucket.

Implement the transformation as a pure Relationship-specific domain function with direct T0/T6 evidence. Do not use Object `migrate_properties` unchanged because Object semantic identity, required state and migration-default behavior are materially different.

## 6.4 Lock and write pipeline

Use optimistic discovery only to identify the stable Definition required for the plan.

Complete lock plan:

```text
RelationshipDefinition header    FOR KEY SHARE
exact target RDV                  FOR SHARE
factual Relationship owner       FOR NO KEY UPDATE
```

Canonical target-before-owner ordering is mandatory.

Pipeline:

```text
optimistically discover current stable Definition
-> build complete Definition/target/Relationship plan
-> acquire plan
-> fresh source fact, source schema and target schema reload
-> require same Definition, forward target and target PUBLISHED
-> rederive preserve-or-fail candidate
-> require the same complete plan
-> begin DML
-> one owner-row UPDATE of exact pin + complete properties
-> leave closure rows untouched
-> one metadata projection
-> complete RELATIONSHIP_SCHEMA_CHANGE event batch
-> commit
```

If protected reread requires a different Definition/target lock set, raise `LockPlanStale` before DML and use the existing shared whole-UoW restart budget. Do not append locks and do not add a third restart cause.

A valid schema change is always a real transition because the exact pin changes, even when the migrated property map equals the source property map. It always emits the complete event set.

Event state:

```text
before = source exact pin + source properties
after  = target exact pin + migrated properties
```

Relationship identity, stable Definition, endpoint pair and complete closure remain unchanged.

---

# 7. Current-state persistence and projection

Extend `RuntimeRelationshipStore` only for current factual state and closure responsibilities.

Add the smallest set-based methods needed for:

```text
optimistic factual header discovery
exact owner-row properties replacement
exact owner-row pin + properties replacement
rowcount/invariant checks
set-based aggregate/page loading
```

Requirements:

```text
DATA_CHANGE updates only properties
SCHEMA_CHANGE updates pin + properties in one row statement
no closure DELETE/INSERT/UPDATE for either command
no server-side default for properties
no partial JSON patch authority
no EAV/property-value rows
```

A locked owner update affecting zero or more than one row is an invariant failure.

Current-state persistence must not insert or query lifecycle rows after the LifecycleStore refactor.

Mutation responses must use:

```text
current factual identity/pin/properties
+
one coherent semantic metadata projection
```

Do not return raw runtime rows.

---

# 8. Coherent reads and corruption boundary

## 8.1 Relationship GET

`Relationship.GET` is a multi-statement aggregate read and must use:

```text
REPEATABLE READ READ ONLY
```

within `UnitOfWorkFactory.coherent_read()` before the first semantic query.

In one snapshot validate and project:

```text
factual header
stable Definition and complete Resolutions
exact pinned RDV and complete declarations
exact DTV dependencies
canonical properties
complete runtime closure
endpoint Objects and stable lineage compatibility
deduplicated semantic views
```

A read observes a complete committed state before or after a concurrent transition, never a hybrid.

## 8.2 Object-relative Relationship pages

For:

```text
GET /api/v1/core/objects/{object_id}/relationships
```

use one coherent read snapshot to:

```text
validate the current path Object
load limit + 1 ordered distinct page view identities
collect every represented Relationship aggregate
batch-load and validate all represented facts/model dependencies/endpoints
rebuild or verify each returned item from validated aggregate state
fail the complete page if one represented fact is corrupt
```

Do not execute one full aggregate query sequence per Relationship. Avoid a page-size N+1. Batch exact pins, declarations, DTVs, closure rows and endpoint state by the finite represented set; load the ObjectTemplate parent graph at most once per page when required for closure validation.

Ordering and cursor identity remain exactly:

```text
(relationship_id, destination_object_id, name) ASC
```

Mutable `relationship_definition_version` and `properties` remain excluded from cursor identity.

## 8.3 Definition/default and exact RDV reads

Preserve and verify the S01 coherent-read behavior for:

```text
DataType stable/default reads
ObjectTemplate stable/default reads
RelationshipDefinition stable/default reads
exact RelationshipDefinitionVersion reads/lists
```

Do not regress batched defensive default validation. Add deterministic read cuts where S02 evidence requires proof that a concurrent commit cannot produce mixed default/header/version state.

## 8.4 Lifecycle pages

The global lifecycle page must decode every selected row rigorously. One corrupt row fails the complete page with `internal_error`; no partial `items` response is allowed.

The Object-specific lifecycle route retains current-target semantics:

```text
current path Object exists
    -> return involving historical page

path Object absent
    -> 404 resource_not_found
```

When Object existence and event selection require multiple statements, use one coherent read snapshot. The global history route does not require any current resource to exist.

## 8.5 No repair

Reads and mutations must never:

```text
repair closure rows
remove unknown properties
recanonicalize and persist corrupted state
rebind to default/latest/highest
ignore missing dependencies
return a partial page or partial event set
```

Persisted corruption maps to bounded `500 internal_error` without internal leakage.

---

# 9. Public API and exact surface

Add exactly these two public routes:

```text
POST /api/v1/core/relationships/{relationship_id}/data-change
POST /api/v1/core/relationships/{relationship_id}/schema-change
```

Use operation-specific strict Pydantic 2 request carriers and existing canonical error handling. Do not add PUT, PATCH, bulk or generic action routes.

After S02, the public business API must be exactly:

```text
41 mutation operations
22 read operations
63 /api/v1/core operations
```

`GET /health/core` is still absent until M2-S04. No CLI surface is introduced.

Add exact router/OpenAPI/static inventory evidence. Minimum-count assertions are forbidden. Assert the two routes above are present and every unauthorized future/negative route remains absent.

For every new route cover at least:

```text
unknown body field
unknown/repeated query
malformed relationship UUID
bool/zero/negative target_version
missing/empty operations
invalid closed operation vocabulary
duplicate property operation
REMOVE with value
SET without value
explicit null behavior
body and response DTO exact fields
status and bounded error details
```

No SQL, table, column, constraint or stack detail may appear in public bodies.

---

# 10. Required deterministic PostgreSQL scenarios

Implement every assigned S02 scenario with stable IDs and real independent sessions.

## 10.1 ROW-26 — DATA_CHANGE × DATA_CHANGE

Prove:

```text
same factual owner serializes on Relationship NKU
waiter reloads fresh properties
no lost update
serially compatible disjoint changes are both represented
SET-same or equivalent canonical waiter may become a semantic no-op
no-op writes no UPDATE and no event
real transitions have exact before/after event state
```

Use `pg_blocking_pids()` for required blocking and exact final-state/event assertions.

## 10.2 ROW-27 — DATA_CHANGE × SCHEMA_CHANGE

Exercise both winner orders and prove one serial factual history under the fresh pin/state.

Required outcomes include:

```text
DATA_CHANGE first
    -> SCHEMA_CHANGE migrates the fresh changed properties

SCHEMA_CHANGE first
    -> DATA_CHANGE validates under the fresh target schema

no hybrid pin/property state
matching ordered lifecycle snapshots
closure unchanged
```

## 10.3 ROW-28 — SCHEMA_CHANGE × SCHEMA_CHANGE

Prove:

```text
same factual owner serialization
fresh source pin reread
target exact admission through commit
only still-forward transitions commit
same/lower target after wake-up receives the frozen semantic result
no stale-source migration
closure unchanged
no 40P01
```

## 10.4 ROW-29 — mutation × DELETE

Cover both:

```text
DATA_CHANGE × DELETE
SCHEMA_CHANGE × DELETE
```

and both winner orders:

```text
mutation commits first
    -> DELETE captures the resulting final state and emits matching DELETED events

delete commits first
    -> mutation returns resource_not_found and emits no event
```

Preserve exact 204/404 behavior and ABA-safe exact identity.

## 10.5 ROW-30 — SCHEMA_CHANGE admission variants

Add the SCHEMA_CHANGE variants to the existing stable `ROW-30` registry.

Prove at minimum:

```text
explicit target PUBLISHED through commit
SCHEMA_CHANGE versus target RDV DEPRECATE, both winner orders
recheck after wait
Definition default changes do not select or rewrite SCHEMA_CHANGE target
no latest/highest/default fallback
```

Use the exact frozen outcome for a target that is no longer admissible.

## 10.6 REF-10 — Relationship direct rebind versus root delete

Implement the Relationship schema-rebind variants of `REF-10` in both winner orders.

Prove:

```text
Definition/target RDV locks precede factual owner
current fact lifetime continues to block Definition root deletion
root deletion cannot create a target/owner wait cycle
SCHEMA_CHANGE either commits against the live target or returns the defined outcome
delete blocker/result is semantically bounded
no partial state
no 40P01
```

Do not invent a new scenario ID for this assigned variant.

## 10.7 SNAP-05 — coherent metadata

For real DATA_CHANGE and SCHEMA_CHANGE transitions, race with:

```text
from Object rename
to Object rename
RelationshipResolution/Definition rename
independent endpoint rename combinations
```

Prove:

```text
required rename/mutation progress remains possible
one metadata statement owns the event observation
all rows in one event set reflect one committed observation
no mixed independently fetched old/new metadata
mutation response views use the same authoritative current name observation where applicable
```

Use deterministic phase cuts, not sleep.

## 10.8 ATOMIC-06 and ATOMIC-07

Inject failure after real current-state DML and through the real shared Relationship event writer.

```text
ATOMIC-06
    DATA_CHANGE event failure
    -> old pin/properties/closure remain
    -> no new event row survives

ATOMIC-07
    SCHEMA_CHANGE event failure
    -> source pin/properties/closure remain
    -> no new event row survives
```

The injection must exercise real SQL before raising and rely on transaction rollback. Do not fake the current-state mutation or replace the real PostgreSQL authority.

Re-run existing CREATE/DELETE event-failure scenarios `ATOMIC-02` and `ATOMIC-03` against the shared LifecycleStore to prove all four factual transitions use one atomic writer boundary.

## 10.9 Harness rules

Use the existing deterministic harness and phase vocabulary. A test-only interceptor may observe/pause production phases but may not:

```text
change candidate data
issue semantic SQL
acquire production locks
change isolation
commit or rollback
change failure mapping
choose another production path
use sleep as ordering authority
```

Required blocking is proved primarily by `pg_blocking_pids()`. Required progress is proved by a positive production phase reached while the other transaction remains open. Timeouts are hang guards only.

Every worker captures SQLSTATE when present. Any supported-path `40P01` fails the scenario and blocks candidate readiness; it is never retried.

---

# 11. Functional, codec, fan-out and read evidence

## 11.1 T0/T6 DATA_CHANGE evidence

Add deterministic and property-based evidence for:

```text
operation order independence with unique property operands
SET/REMOVE complete-state derivation
unknown property
null and invalid value rejection
canonical SET-same no-op
REMOVE-absent no-op
SCALAR/LIST validation
pin/closure preservation
```

Hypothesis supplements concrete examples; it does not replace exact examples or PostgreSQL assertions.

## 11.2 T0/T6 SCHEMA_CHANGE evidence

Cover:

```text
same-mode compatible preservation
SCALAR -> LIST widening
new target optional property absent
source-only property removed
matching absent property remains absent
target exact DTV recanonicalization
constraint incompatibility -> deterministic property blocker
equal resulting property map still real because pin changes
non-forward target rejection
no intermediate/default consultation
```

Add algebraic properties that materially strengthen preserve-or-fail coverage without creating a parallel schema language.

## 11.3 Lifecycle codec evidence

Cover the shared codec directly and through real PostgreSQL rows:

```text
exact RelationshipFactualState keys
positive non-boolean exact version
allowed scalar carriers
non-empty homogeneous LIST carrier
forbidden null/float/object/nested/empty/heterogeneous carrier
Object snapshots use the same property carrier
all four transition nullability rules
DATA_CHANGE same-version/different-properties rule
SCHEMA_CHANGE forward-version rule
one invalid row fails the complete page
no live model lookup during historical decode
```

## 11.4 Semantic-view fan-out

For the complete event writer prove one event row per distinct semantic view for:

```text
non-symmetric ordinary fact
symmetric distinct endpoints
symmetric self-loop
inheritance-overlap raw-row deduplication
```

Assert deterministic semantic-view order and that raw closure cardinality is not exposed as event cardinality.

Exercise the writer across all real factual transition families, not only CREATE.

## 11.5 Historical independence

Create real factual history, then remove current resources through authorized operations in dependency-safe order.

Prove:

```text
global history remains readable after current Relationship deletion
history remains readable after Definition/RDV/DTV and endpoint Object deletion
historical state requires no live schema lookup
historical names and factual snapshots remain exact
Object-specific lifecycle route still requires a current path Object
```

Use dedicated resources so unrelated references do not weaken the assertion.

## 11.6 Read-coherence cuts

Instrument multi-statement reads so a writer commits between physical reads.

Cover complete before-or-after behavior for:

```text
Relationship GET versus DATA_CHANGE
Relationship GET versus SCHEMA_CHANGE
Relationship GET versus DELETE
Object-relative page versus DATA_CHANGE
Object-relative page versus SCHEMA_CHANGE
Object-relative page versus DELETE
```

Also prove one corrupt represented fact fails the entire Object-relative page and that mutable pin/properties are not part of cursor identity.

---

# 12. Traceability requirements

Extend the existing machine-checkable M2 registry; do not create an untracked S02-only evidence island.

Add exact concrete target maps for:

```text
M2-VER-08
M2-VER-09
M2-VER-11
M2-VER-12
M2-VER-13
M2-VER-14
```

Each bundle must contain every required T0/T1/T2/T3/T4/T6 target and is `IMPLEMENTED` only when all concrete targets exist.

Add machine-resolvable scenario target sets for:

```text
ROW-26
ROW-27
ROW-28
ROW-29
ROW-30 SCHEMA_CHANGE variants
REF-10 Relationship variants
SNAP-05
ATOMIC-06
ATOMIC-07
```

Preserve and extend, rather than replace:

```text
all S00 PLAN-01 ... PLAN-06 targets
all S01 bundle targets
S01-RF-01 ... S01-RF-03 targets
ROW-18 ... ROW-25
ROW-30 CREATE variants
ARB-05 ... ARB-08
REF-03, REF-04, REF-07, REF-09
ATOMIC-02, ATOMIC-03, ATOMIC-05
```

When one stable scenario owns several required variants, represent every variant in a set of concrete targets. Do not hide mandatory variants behind one undocumented primary target.

Preserve the exact frozen census:

```text
16 outcomes
32 acceptance criteria
32 evidence bundles
83 canonical scenarios
21 safety predicates
```

Do not mark M2-S03-owned bundles or complete 861-cell closure PASS merely because S02 tests exist.

Add exact public operation inventory evidence for the 63 business operations now implemented. Health and CLI mappings remain future/designed evidence and must not be falsely marked complete.

Every mapped target must resolve to a real collected test. No empty bundle, placeholder, source-text-only claim or minimum-count assertion is sufficient.

---

# 13. Verification requirements

Run focused gates first, then every cross-boundary and complete repository gate. Report exact commands, counts and durations where available.

At minimum run the concrete repository equivalents of:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright

# S02 pure/domain/property evidence
uv run pytest -q \
  tests/test_relationship_domain.py \
  <new or extended S02 property/domain targets> -ra

# factual Relationship HTTP and lifecycle contracts
uv run pytest -q \
  tests/test_relationship_api.py \
  tests/test_relationshipdefinition_api.py \
  <lifecycle API targets> -ra

# S02 real PostgreSQL persistence/read/codec evidence
uv run pytest -q \
  <S02 persistence, lifecycle, fan-out and read-coherence targets> -ra

# S02 deterministic concurrency
uv run pytest -q \
  <ROW-26 ... ROW-30, REF-10, SNAP-05, ATOMIC-06/07 targets> -ra

# shared writer regressions
uv run pytest -q \
  <existing CREATE/DELETE atomicity and Object lifecycle targets> -ra

# traceability and exact route inventory
uv run pytest -q \
  tests/test_m2_traceability.py \
  <route/negative-surface targets> -ra

# unchanged durable schema assurance
uv run pytest -q \
  tests/test_schema_metadata.py \
  tests/test_migrations.py -ra

# complete PostgreSQL concurrency
uv run pytest -q -m "postgresql and concurrency" -ra

# complete non-PostgreSQL regression
uv run pytest -q -m "not postgresql" -ra

# complete repository suite, including PostgreSQL tests
uv run pytest -q -ra
```

Replace placeholders in the actual handoff with exact collected targets. Do not duplicate a test file on one command line merely because it belongs to several categories.

Report explicitly:

```text
CPython version
PostgreSQL server version
M2-VER-08 result and targets
M2-VER-09 result and targets
M2-VER-11 result and targets
M2-VER-12 result and targets
M2-VER-13 result and targets
M2-VER-14 result and targets
ROW-26 ... ROW-30 results
REF-10 Relationship results
SNAP-05 results
ATOMIC-06 / ATOMIC-07 results
CREATE/DELETE shared-writer atomicity regression results
read-coherence cut results
fan-out shape results
historical-independence result
exact 63-business-route inventory result
schema drift result
one-base / one-head result
full-suite count and duration
skips / xfails / reruns census
whether any supported path returned SQLSTATE 40P01
```

No unexplained skip, xfail, flaky rerun or generic retry is permitted for normative evidence.

If `TEST_DATABASE_URL` is unavailable or any mandatory real-PostgreSQL/full gate is blocked or failing:

```text
leave M2-S02 IN PROGRESS
record the exact blocker/failure in status.md
do not claim CANDIDATE READY FOR REVIEW
push a partial implementation only when useful and explicitly labelled
never fabricate evidence or substitute another backend
```

---

# 14. Documentation and status discipline

Do not modify frozen contract, architecture or `steps.md`.

Keep this execution aid in:

```text
docs/milestones/M2/wip/M2-S02-codex-prompt.md
```

until reviewer acceptance. Do not delete it in the implementation candidate.

Update `docs/milestones/M2/status.md` only with verified operational facts.

During active work:

```text
M2-S02 IN PROGRESS
M2-S03 BLOCKED
```

Only when the entire vertical slice and every mandatory gate pass against real PostgreSQL may Codex set:

```text
M2-S02 CANDIDATE READY FOR REVIEW
reviewer decision pending
```

Never mark:

```text
M2-S02 COMPLETED
M2-S03 READY or IN PROGRESS
M2 DELIVERED
review ACCEPTED
```

Those states are reviewer/human-owned.

The candidate record must include implementation/status commit identities, exact evidence commands/results and environment versions. Do not overwrite the S00/S01 completion records.

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
Hypothesis where justified
HTTPX ASGITransport
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
SERIALIZABLE as a substitute for explicit locking
new advisory gates
new automatic retry causes
ON CONFLICT DO NOTHING aggregate writes
JSONB patching as a second state authority
new dependency for convenience
global Ruff/Pyright relaxation
broad warning/error suppression
GitHub Actions
```

Keep any unavoidable suppression narrow, local and justified in the handoff.

---

# 16. Git and publication discipline

Before publication:

```text
review the complete diff from the prompt-publication baseline
review staged diff
exclude unrelated changes
verify no secret or database URL is present
verify no schema/migration/dependency/lockfile drift
verify M2-S02 prompt remains present
verify S00/S01 completion records remain intact
verify obsolete Actions/payload material remains absent
run git diff --check
```

Use one or more coherent intentional commits. Suitable titles include:

```text
feat(m2-s02): complete factual relationship mutations

refactor(m2-s02): centralize lifecycle persistence

test(m2-s02): prove factual state and lifecycle semantics

docs(m2): publish S02 candidate
```

Push normally to:

```text
origin/M2
```

After push verify:

```text
local HEAD SHA
origin/M2 SHA
remote branch SHA
local/remote synchronization
working tree clean
```

Do not create a PR, merge, force-push, tag or release.

---

# Completion report

At the end provide a reviewer-oriented handoff containing only verified facts:

- cycle `M2`, slice `M2-S02`, branch `M2`;
- implementation and status/evidence commit SHA(s);
- push, local/remote synchronization and working-tree state;
- concise changed-file/category inventory;
- DATA_CHANGE domain/application/persistence/API summary;
- no-op proof: no UPDATE and no event;
- SCHEMA_CHANGE target, preserve-or-fail and exact blocker summary;
- target-before-owner lock-plan summary;
- proof that pin/properties update is atomic and closure unchanged;
- LifecycleStore ownership and migrated Object/Relationship writers/readers;
- proof that current-state stores no longer own lifecycle SQL;
- shared historical carrier and transition-codec results;
- coherent GET/page/lifecycle read results;
- fan-out results for all four required fact shapes;
- historical-independence result;
- exact new/updated traceability target maps;
- exact route inventory and negative-surface result;
- ROW-26 ... ROW-30, REF-10, SNAP-05, ATOMIC-06/07 results;
- confirmation that S00/S01 evidence remains passing;
- schema/migration result: unchanged, 15 tables, one base/head, drift `[]`;
- dependency/lockfile result: unchanged;
- complete quality/test commands, counts and durations;
- CPython and PostgreSQL versions;
- full-suite result and explicit supported-path `40P01` result;
- skip/xfail/rerun census;
- confirmation that no Health, startup, CLI, packaging or S03 capability was introduced;
- confirmation that no M1 bridge/backfill/stamp/dual decoder exists;
- confirmation that Actions/payload material remains absent;
- every unexecuted requirement and exact reason;
- every residual risk or architecture/documentation finding;
- final `status.md` state without claiming reviewer-owned completion.

Use the wording:

```text
M2-S02 candidate implemented and ready for reviewer inspection
```

only when every mandatory slice and full gate has passed against real PostgreSQL and the candidate has been pushed.
