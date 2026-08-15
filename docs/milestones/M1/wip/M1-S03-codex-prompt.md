# Codex implementation prompt — M1-S03

**Status:** NON-NORMATIVE IMPLEMENTATION PROMPT.

This file is an execution aid for Codex. It does not override `AGENTS.md`, the frozen M1 contract/architecture/steps, or the ratified technology baseline.

## Assignment

Implement exactly:

```text
M1-S03 — ObjectTemplate and active model graph vertical slice
```

from `docs/milestones/M1/steps.md`.

M1-S00, M1-S01 and M1-S02 are complete. Do not implement M1-S04 or any later Object/ownership/Relationship capability.

## Mandatory pre-flight

Before changing files, read and obey:

```text
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md
docs/milestones/M1/contract.md
docs/milestones/M1/architecture/README.md
docs/milestones/M1/steps.md
docs/milestones/M1/status.md

docs/milestones/M1/architecture/objecttemplate.md
docs/milestones/M1/architecture/objecttemplate-lifecycle.md
docs/milestones/M1/architecture/objecttemplate-properties.md
docs/milestones/M1/architecture/objecttemplate-components.md
docs/milestones/M1/architecture/objecttemplate-effective-schema.md
docs/milestones/M1/architecture/datatype.md
docs/milestones/M1/architecture/persistence-model.md
docs/milestones/M1/architecture/persistence-uow-concurrency.md
docs/milestones/M1/architecture/concurrency-semantic-matrix.md
docs/milestones/M1/architecture/concurrency-postgresql-realization-matrix.md
docs/milestones/M1/architecture/concurrency-postgresql-test-matrix.md
docs/milestones/M1/architecture/api-contract.md
docs/milestones/M1/architecture/api-wire-contract.md
docs/milestones/M1/architecture/api-read-contract.md
docs/milestones/M1/architecture/api-list-contract.md
docs/milestones/M1/architecture/api-error-contract.md
```

Confirm from the repository itself that:

```text
M1 contract      = FINAL / FROZEN
M1 architecture  = globally FROZEN as a set
M1 steps         = FINAL / FROZEN
M1-S00           = COMPLETED
M1-S01           = COMPLETED
M1-S02           = COMPLETED
current step     = M1-S03
STACK-01..09     = RATIFIED
```

Individual architecture files may still carry historical authoring labels such as `DRAFT`; the frozen architecture index is the set-level authority. Do not reinterpret those labels as open design.

If normative authorities conflict, stop the affected work and report the contradiction instead of choosing one. Do not use historical implementation from Git history as a template.

## Objective

Deliver a complete usable M1 ObjectTemplate model-plane capability:

```text
plain-Python ObjectTemplate semantics
-> inheritance + local declarations
-> derived effective schema
-> DataType/parent exact admission on caller-owned UoW
-> active-model-graph lifecycle certification
-> PostgreSQL aggregate persistence/concurrency
-> public ObjectTemplate HTTP read/write/list/effective-schema API
-> deterministic real-PostgreSQL verification
```

At the end of S03, DataType/ObjectTemplate cross-domain correctness must be fully active. A caller can define, version, revise, publish, default, deprecate, read/list and delete permitted ObjectTemplate state and obtain deterministic effective schemas through `/api/v1/core`.

## Hard scope boundary

S03 MUST NOT implement:

```text
Object runtime CREATE / RENAME / DATA_CHANGE / SCHEMA_CHANGE / DELETE
runtime Object property state
runtime ownership ATTACH / DETACH
Object lifecycle event production
RelationshipDefinition commands
runtime Relationship commands
ObjectTemplate relationship-capability semantics
GET /object-templates/{template_id}/relationship-capabilities as a fake/empty placeholder
JSON Schema compiler/projection
persistent effective-schema cache
ancestry closure table
reverse-dependency authority table
new schema tables or a migration solely for S03
ORM Session / AsyncSession
generic repository/DAO framework
generic command bus / service container
background jobs / 202 semantics
Docker/Testcontainers/database provisioning
```

It is valid and required for ObjectTemplate deprecation/delete safety to query physical tables belonging to later capabilities when those tables already exist from S01 and are current FK/reverse-reference authority. This does not make the later capability implemented.

Do not register the `relationship-capabilities` route until M1-S06 can implement its real semantics.

## 1. Stable ObjectTemplate lineage and version semantics

Implement the stable lineage state:

```text
id
namespace
name
description
abstract
parent_template_id
in-memory/public default_version
```

Preserve:

- application/kernel-generated immutable UUID;
- immutable namespace/name/abstract/parent lineage;
- `(namespace,name)` uniqueness within ObjectTemplate;
- the same identifier/namespace grammar already used by DataType;
- `core` / `core.*` reserved from public/user admission;
- nullable LWW description with no lineage revision token;
- root lineage has `parent_template_id = null`;
- non-root lineage chooses one existing parent lineage at CREATE and never changes it through normal M1 mutation.

Each ObjectTemplateVersion has exact tuple identity:

```text
(template_id, version)
```

with positive version, positive DRAFT revision and lifecycle:

```text
DRAFT -> PUBLISHED -> DEPRECATED
```

PUBLISHED/DEPRECATED snapshots are structurally immutable.

## 2. Parent lineage and exact parent-version pinning

A non-root exact OTV must persist:

```text
parent_template_id == stable lineage parent_template_id
parent_version
```

The equality between OTV `parent_template_id` and lineage `parent_template_id` is UoW-enforced, not a new DB trigger/check.

Public CREATE selector semantics:

```text
parent_template_id omitted
    -> root
    -> parent_version forbidden

parent_template_id present + parent_version omitted
    -> implicit parent.default_version

parent_template_id present + parent_version present
    -> explicit exact parent OTV

explicit null is not omission
```

A newly selected/rebound exact parent must remain PUBLISHED until the semantic UoW commits.

Public REVISE never accepts `parent_template_id`:

```text
root lineage
    -> parent_version forbidden

non-root + parent_version omitted
    -> intentional rebind through current parent default

non-root + explicit parent_version
    -> exact parent selection
```

Preserving an unchanged exact parent pin is different from selecting/rebinding a new parent version. Do not gratuitously re-certify an unchanged historical exact pin during ordinary DRAFT revise; a DRAFT may remain well-formed with an unchanged parent pin that has since become DEPRECATED, but that DRAFT is not publishable until its final direct dependency is PUBLISHED.

`CREATE_NEXT` clones the source exact parent pin unchanged and does not resolve the parent default again.

Inheritance must remain acyclic. Supported normal operations preserve this by construction because parent lineage is immutable and parent must already exist, but the effective-schema/ancestry resolver must defensively detect impossible persisted cycles and fail as an internal invariant problem rather than recurse forever.

Do not impose a hard-coded inheritance depth limit.

## 3. Property declarations

Implement local ObjectTemplateProperty state exactly:

```text
name
position
datatype_id
datatype_version
value_mode
required
migration_default
```

### Exact DTV pinning

Every persisted property always contains an exact `(datatype_id, datatype_version)` pin.

Public declaration rules:

```text
name          required
position      required positive integer
datatype_id   required
value_mode    required SCALAR|LIST
required      required boolean
datatype_version omitted
    -> intentional implicit DataType default binding/rebinding
explicit datatype_version
    -> exact selection
```

For every **new/rebound** DTV selection, use the S02 caller-owned-UoW persistence admission seam on the same semantic transaction:

```text
explicit
    -> exact DTV FOR SHARE
    -> fresh PUBLISHED check

implicit
    -> DataType lineage FOR SHARE
    -> resolve default
    -> exact DTV FOR SHARE
    -> fresh PUBLISHED check
```

The lock must live until the ObjectTemplate mutation commits. Do not reintroduce an application helper that opens a private short-lived DataType UoW.

An unchanged historical exact pin is not a new admission and is not opportunistically re-certified during DRAFT revise. `CREATE_NEXT` also clones historical pins without opportunistic upgrades.

### Value mode and migration_default

Support only:

```text
SCALAR
LIST
```

`required` means at least one value.

`migration_default` rules:

```text
required=false
    -> field MUST be absent at public candidate boundary
    -> persistence NULL

required=true + SCALAR
    -> field required
    -> exactly one non-null primitive value

required=true + LIST
    -> field required
    -> non-empty ordered list
```

Use the single PrimitiveType authority implemented in S02 for every migration-default value. Read the pinned DTV primitive/constraints and canonicalize/validate through that same domain path. LIST order is preserved and duplicate list items are allowed; M1 does not introduce SET/unique-items semantics.

`migration_default` is schema-migration metadata only. Do not treat it as Object creation state or implement Object behavior in S03.

### Property identity/evolution

For a local property never present in any PUBLISHED snapshot of the declaring lineage, DRAFT edits remain editorial: name, datatype lineage/version, value mode, required/default and position may change as long as each committed candidate is well-formed.

After first publication, historical semantic identity is:

```text
(declaring_template_id, name)
```

and normal evolution must preserve:

```text
name          stable for that historical semantic property
datatype_id   stable
value_mode    same OR SCALAR -> LIST
```

while datatype_version/required/migration_default/position may evolve subject to normal validity/admission rules.

Removal of a local historical property is allowed. Reintroduction later with the same name on the same declaring lineage resumes the same historical semantic identity; a remove/re-add gap MUST NOT reset datatype/name/value-mode evolution rules.

Do not create stable property UUIDs.

## 4. Component-slot declarations

Implement local ObjectTemplateComponent state exactly:

```text
name
position
target_template_id
```

A component target is a stable ObjectTemplate lineage, not an exact version.

New/changed target requirements:

- target lineage must exist;
- no default/PUBLISHED target version is required;
- abstract target lineages are valid compatibility contracts;
- current FK RESTRICT remains final lifetime authority under delete races.

For a slot never present in a PUBLISHED snapshot of the declaring lineage, DRAFT edits remain editorial.

After first publication, historical semantic identity is:

```text
(declaring_template_id, name)
```

Normal target evolution permits only:

```text
same target
OR
target widening to an ancestor of the historical/current target lineage
```

Normal narrowing or movement to an unrelated lineage is invalid.

Removal is allowed. Reintroduction with the same name on the same declaring lineage preserves historical semantic identity and cannot bypass the widening-only rule.

`position` is positive and unique only among local component declarations. Property positions and component positions are separate ordering domains.

Do not create slot UUIDs or exact-version component target pins.

## 5. Shared effective member namespace and candidate well-formedness

Properties and component slots share one effective member-name namespace.

A committed DRAFT must be well-formed. Validate the complete effective candidate so that there is no:

```text
property/property collision
component/component collision
property/component collision
inherited override
inherited shadowing
child removal of an inherited member
```

A child may remove only its own previously local declarations in a later local snapshot; it cannot cancel a member declared by an ancestor exact snapshot.

Request array order is never semantic authority. Local declaration ordering comes from explicit positive `position`.

Reject local duplicate names/positions as semantic candidate validation before relying on DB PK/UNIQUE errors for normal caller input. DB constraints remain defensive/final structural authority.

## 6. Derived effective schema

Implement one deterministic resolver with source of truth:

```text
exact parent chain
+
local declaration rows at each exact OTV
```

No authoritative materialized/cached effective schema.

Resolution order is exact root -> leaf.

Public effective property output contains:

```text
declaring_template_id
name
position
datatype_id
datatype_version
value_mode
required
migration_default only when semantically present
```

Public effective component output contains:

```text
declaring_template_id
name
position
target_template_id
```

Ordering:

```text
ancestor/root property blocks -> ... -> leaf property block
within each block position ASC

ancestor/root component blocks -> ... -> leaf component block
within each block position ASC
```

Property and component ordering remain separate.

The exact OTV GET is a **local snapshot**, not the effective schema.

### Read snapshot coherence

ObjectTemplate exact-version and effective-schema reads are composite multi-row reads. They MUST NOT expose a header/revision from one candidate generation with property/component rows from another committed generation.

Use either:

- one coherent SQL statement/observation that returns the needed aggregate snapshot; or
- a dedicated coherent read transaction such as `REPEATABLE READ READ ONLY` where multiple statements are genuinely clearer.

Do not change mutation isolation from READ COMMITTED. Do not assume that several ordinary READ COMMITTED SELECTs automatically form one snapshot.

## 7. CREATE ObjectTemplate

CREATE atomically creates:

```text
stable lineage
+
v1 DRAFT revision=1
+
exact parent pin when non-root
+
local properties
+
local components
```

Public body:

```text
namespace required
name required
abstract required; no omitted->false default
description omitted -> null
properties omitted -> []
components omitted -> []
parent selector per API-03.3
```

Generate the ObjectTemplate UUID in kernel/application code.

Perform all persisted-state-dependent admission/validation inside one semantic UoW. Any failure rolls back the entire aggregate; a lineage without v1 is never a valid committed CREATE result.

Qualified-name UNIQUE is final arbitration authority for concurrent CREATE and must map to `qualified_name_conflict`, never leak constraint names.

Component target existence and parent/DTV referenced operands use semantic not-found/failure mapping; a concurrent deletion must be translated through the frozen failure taxonomy without SQL leakage while FK RESTRICT/existence remains final race authority.

CREATE does not auto-publish.

## 8. CREATE_NEXT

`CREATE_NEXT` body is exactly:

```json
{"source_version": N}
```

Source must exist in the same lineage and be PUBLISHED or DEPRECATED, never DRAFT, and need not be max version.

Canonical sequence:

```text
lineage header FOR NO KEY UPDATE
-> fresh current version/source state
-> allocate max(existing)+1
-> clone source exact parent pin
-> clone source local property/component persisted declarations
-> insert complete new DRAFT revision=1 atomically
```

Do not re-resolve parent/DataType defaults or re-admit unchanged cloned dependencies. Do not store `derived_from`.

Deleting a maximum DRAFT may allow that version number to be reused later.

## 9. REVISE complete candidate

REVISE is complete local-candidate replacement, not PATCH.

Public body:

```text
properties required, including []
components required, including []
parent_version according to root/non-root rules
```

The body never carries stable lineage metadata, abstract, parent_template_id, lifecycle/default state or expected_revision.

Required transaction flow:

```text
exact DRAFT FOR NO KEY UPDATE
-> fresh status/revision check
-> read current complete local candidate/history required for evolution
-> resolve requested parent/DTV selectors
-> acquire new/rebound dependency admission locks in deterministic resource order
-> build the complete candidate in memory
-> resolve complete effective candidate
-> validate well-formedness + historical evolution
-> replace the complete persisted local declaration snapshot atomically
-> update parent_version when applicable
-> increment header revision exactly once
-> commit
```

A failed validation or later persistence failure leaves the old revision/header/properties/components unchanged.

Do not increment revision once per child-row mutation.

For explicit exact selectors that preserve an unchanged current exact pin, do not manufacture a new dependency admission. For omitted version fields, follow the public contract: omission is intentional implicit rebinding where API-03 defines it, not "keep current".

Acquire multi-dependency locks deterministically; request array order must not determine lock order.

## 10. PUBLISH and active model graph certification

PUBLISH canonical ownership:

```text
consumer lineage header FOR NO KEY UPDATE
-> exact DRAFT OTV FOR NO KEY UPDATE
-> fresh status/revision/candidate checks
```

Then stabilize every **direct lifecycle-sensitive exact dependency** with `FOR SHARE` in deterministic resource order and re-check PUBLISHED:

```text
exact parent OTV, when non-root
local exact DTV property pins
```

Do not recursively lock transitive inherited dependency closure. The direct active graph invariant is sufficient.

Certification must validate the complete effective candidate and historical/evolution rules. At success:

```text
DRAFT revision=N -> PUBLISHED revision=N
```

Publish never increments structural revision.

If lineage default is NULL, the first serial successful publisher becomes default. Later publish does not replace an existing default.

A historical unchanged pin that was permitted to remain in a DRAFT but is now DEPRECATED makes publication fail `dependency_not_admissible`; publication never commits an active edge to DEPRECATED exact state.

Publication does not scan/migrate runtime Objects and does not detach anything.

## 11. SET_DEFAULT / CLEAR_DEFAULT / DEPRECATE

Use the same frozen version/default mechanics as DataType on ObjectTemplate rows.

SET_DEFAULT:

```text
lineage FOR NO KEY UPDATE
-> target exact OTV FOR SHARE
-> fresh PUBLISHED check
-> set exact default
```

CLEAR_DEFAULT:

```text
lineage FOR NO KEY UPDATE
-> set NULL
```

DEPRECATE:

```text
lineage FOR SHARE
-> target exact PUBLISHED OTV FOR NO KEY UPDATE
-> fresh lifecycle/default check
-> direct reverse active-consumer lookup
```

A PUBLISHED child OTV that pins the target as its exact parent blocks deprecation. DRAFT/DEPRECATED child consumers do not block. Lineage-level component references do not block OTV deprecation.

Existing runtime Objects do not block OTV deprecation.

Do not add a reverse dependency table/cache or graph-wide gate.

## 12. DELETE_DRAFT / DELETE_LINEAGE / SET_DESCRIPTION

DELETE_DRAFT:

```text
lineage FOR NO KEY UPDATE
-> exact DRAFT FOR UPDATE
-> fresh status/revision check
-> delete owned property/component rows by existing CASCADE
```

Only DRAFT is individually deletable and `expected_revision` is mandatory.

Whole-lineage DELETE:

```text
lineage header FOR UPDATE
-> bounded semantic external-reference precheck
-> neutralize internal default pointer as needed
-> delete root and owned versions/declarations atomically
```

External/current references must block, including physical authorities already present for later slices, such as applicable:

- child ObjectTemplate stable parent lineage / exact parent version;
- another OTV component target lineage;
- Object exact OTV pins;
- RelationshipResolution endpoint lineage references;
- any other current cross-aggregate FK represented in the frozen 13-table schema.

Internal own versions/declarations/default are not blockers.

The immediate FK `RESTRICT` graph is final race authority against a concurrent reference that wins after the semantic precheck. Translate expected races to bounded `delete_blocked`; never leak SQL/table/constraint details.

SET_DESCRIPTION is nullable atomic last-write-wins metadata with no lineage revision and must preserve the PAR-07 lock topology.

## 13. Failure taxonomy

Reuse the S02 transport-neutral `ApplicationFailure` boundary and shared HTTP handlers. Do not duplicate a second error framework.

Use the frozen codes as applicable, including:

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
qualified_name_conflict
default_version_conflict
active_dependency_conflict
delete_blocked
internal_error
```

Examples:

- missing path ObjectTemplate/OTV -> `resource_not_found` / 404;
- missing parent/DTV/component target supplied as command operand -> `referenced_resource_not_found` / 422;
- malformed/colliding/evolution-invalid/effective-schema candidate -> `semantic_validation_failed` / 422 with bounded violations;
- implicit parent/DTV binding with no default -> `default_version_unavailable` / 409;
- selected exact parent/DTV exists but is not admissible PUBLISHED for a new binding/certification -> `dependency_not_admissible` / 409;
- stale DRAFT generation -> `stale_revision` / 409;
- wrong lifecycle/source state -> specific lifecycle/version-source conflict;
- current default blocker -> `default_version_conflict`;
- direct active child blocker -> `active_dependency_conflict`;
- cross-domain delete refs -> `delete_blocked`.

Do not create generic `conflict` escape codes. Unexpected impossible persisted-state/effective-schema corruption is `internal_error`, not caller validation.

## 14. Public HTTP API

Implement exactly these ObjectTemplate routes in S03:

```text
POST   /api/v1/core/object-templates
POST   /api/v1/core/object-templates/{template_id}/create-next
POST   /api/v1/core/object-templates/{template_id}/versions/{version}/revise
POST   /api/v1/core/object-templates/{template_id}/versions/{version}/publish
POST   /api/v1/core/object-templates/{template_id}/set-default
POST   /api/v1/core/object-templates/{template_id}/clear-default
POST   /api/v1/core/object-templates/{template_id}/versions/{version}/deprecate
DELETE /api/v1/core/object-templates/{template_id}/versions/{version}
DELETE /api/v1/core/object-templates/{template_id}
POST   /api/v1/core/object-templates/{template_id}/set-description

GET    /api/v1/core/object-templates
GET    /api/v1/core/object-templates/{template_id}
GET    /api/v1/core/object-templates/{template_id}/versions
GET    /api/v1/core/object-templates/{template_id}/versions/{version}
GET    /api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema
```

Do **not** implement/register `GET .../relationship-capabilities` in S03.

### Strict transport DTOs

Use strict Pydantic 2.x only at HTTP boundary. Forbid unknown fields and generic scalar coercion; validate transport carrier/static shape without creating a second domain validation language.

Preserve omission vs explicit null exactly. In particular:

- abstract is required;
- parent/DTV implicit selectors use omission, never null;
- CREATE properties/components omission -> `[]`; null invalid;
- REVISE properties/components always required;
- optional property migration_default must be absent, not null;
- required migration_default must be present and non-null;
- request array order is not semantic authority;
- expected_revision is a required positive query parameter only for REVISE/PUBLISH/DELETE_DRAFT;
- no-body commands reject request bodies.

### Success/read DTOs

OT.CREATE:

```text
201 + Location=/api/v1/core/object-templates/{id}
body = {
  "object_template": <canonical ObjectTemplate lineage DTO>,
  "version": <canonical exact v1 OTV local DTO>
}
```

`object_template` and `version` are literal public fields.

CREATE_NEXT:

```text
201 + exact-version Location
body = exact local OTV DTO
```

REVISE / PUBLISH / DEPRECATE:

```text
200 + exact local OTV DTO
```

SET_DEFAULT / CLEAR_DEFAULT / SET_DESCRIPTION:

```text
200 + ObjectTemplate lineage DTO
```

DELETE_DRAFT / DELETE_LINEAGE:

```text
204, no body
```

Lineage DTO:

```text
id
namespace
name
description
abstract
parent_template_id nullable
default_version nullable
```

Exact local OTV DTO:

```text
template_id
version
revision
status
parent_template_id nullable
parent_version nullable
properties []
components []
```

Local declaration arrays are canonical `position ASC`. Optional properties omit `migration_default`; do not serialize meaningless `null` there.

Effective schema projection contains only template_id/version plus effective properties/components with `declaring_template_id` and the frozen ordering.

## 15. Collection/list behavior

Reuse the S02 cursor/error utilities rather than creating a second incompatible pagination format.

ObjectTemplate lineage collection:

```text
{items,next_cursor}
order (namespace,name) ASC
filters: namespace, name, abstract, parent_template_id
```

Nested OTV collection:

```text
order version ASC
filter: status
summary excludes local properties/components
root summary parent_template_id/parent_version = null
```

Common:

```text
limit omitted -> 100
range 1..500
opaque route/filter/order-specific keyset cursor
limit may change across pages
offset/page/generic sort forbidden
cursor/filter mismatch -> invalid_cursor
```

Each page is independently snapshot-consistent; cursor is not a snapshot token.

## 16. Required pure/domain/application tests

Add focused tests for at least:

- root vs child stable parent semantics;
- explicit parent exact selection;
- implicit parent default selection and default-unavailable failure;
- exact selected parent not-PUBLISHED rejection;
- `CREATE_NEXT` exact clone without opportunistic parent/DTV upgrade;
- DRAFT well-formed but not publishable with unchanged historical DEPRECATED parent/DTV pin;
- defensive cycle detection in effective resolver;
- effective root->leaf ordering;
- local and inherited property/property, component/component and property/component collision rejection;
- local position uniqueness per declaration family;
- property required/SCALAR/LIST cardinality metadata rules;
- migration_default canonicalization through the S02 primitive/DTV constraint authority;
- optional migration_default absence and required non-null behavior;
- explicit and implicit DTV binding/rebinding semantics;
- preserving unchanged exact pins vs omission-triggered default rebinding;
- first-publication property editorial freedom;
- published property stable name/datatype lineage;
- SCALAR->LIST allowed and LIST->SCALAR rejected;
- historical property remove/re-add does not reset evolution constraints;
- first-publication component editorial freedom;
- component target same/widen-to-ancestor allowed; narrowing/unrelated rejected;
- historical component remove/re-add does not reset widening rule;
- inherited members cannot be overridden/removed by child;
- publish requires every direct exact parent/local-DTV dependency PUBLISHED;
- first publish auto-default; later publish keeps current default;
- OTV default/deprecate/delete semantics;
- PUBLISHED exact parent active consumer blocks dependency OTV deprecation;
- DRAFT/DEPRECATED consumers do not block;
- lineage delete blockers across current physical reference families;
- exact/local/effective read DTO semantics and snapshot coherence.

Property-based testing is useful for pure ancestry/effective-schema/history invariants where it adds meaningful state-space coverage, but does not replace explicit frozen examples.

## 17. Required API/PostgreSQL integration tests

Against real externally supplied `TEST_DATABASE_URL`, verify at least:

- atomic CREATE lineage + v1 + declarations;
- canonical migration_default persistence/read round-trip;
- exact parent/DTV composite FK behavior;
- stable component-target FK behavior;
- complete local candidate replacement and one revision increment;
- failed candidate validation/persistence leaves old aggregate generation intact;
- CREATE_NEXT version allocation and complete declaration clone;
- effective-schema read from exact parent chain;
- PUBLISH/default/deprecate/delete reference behavior;
- active direct PUBLISHED child-parent blocker;
- DTV active PUBLISHED property blocker now works through real ObjectTemplate publication;
- whole-lineage delete blocked by current external references and not by own default/children;
- all OT routes/status/Location/body contracts;
- strict unknown/missing/null/query/no-body handling;
- lineage/version list order, filters, summaries, cursor continuation and cursor/filter mismatch;
- no relationship-capabilities placeholder route implementation.

With one `TEST_DATABASE_URL`, PostgreSQL-required tests remain serial with respect to pytest-xdist.

## 18. Deterministic PGTEST coverage required in S03

Use the S01 harness and stable canonical scenario IDs. Preserve the PGTEST rule:

```text
semantic outcome/final-state assertions are mandatory
+
mechanism/blocker assertions where the mechanism is normative
```

Do not claim a canonical scenario merely because a low-level lock primitive blocks.

### Shared ObjectTemplate version/default/lifetime scenarios

Implement real ObjectTemplate semantic-operation variants sufficient to prove the S03 aggregate and persistence shape for:

```text
ROW-01  OT CREATE_NEXT × CREATE_NEXT
ROW-02  OT CREATE_NEXT × DELETE_DRAFT(max)
ROW-03  OT REVISE × REVISE same DRAFT generation
ROW-04A OT REVISE × PUBLISH
ROW-04B OT PUBLISH × DELETE_DRAFT
ROW-05  OT PUBLISH(vA) × PUBLISH(vB), default NULL
ROW-06  OT SET_DEFAULT(v) × DEPRECATE(v)
ROW-15  OT SET_DESCRIPTION × SET_DESCRIPTION
ROW-16  OT REVISE × DELETE_LINEAGE
ARB-01  OT CREATE × CREATE same qualified name
PAR-06  OT DEPRECATE(v1) × DEPRECATE(v2), same lineage
PAR-07A OT SET_DESCRIPTION × SET_DEFAULT
PAR-07B OT SET_DESCRIPTION × REVISE
```

Do not gratuitously duplicate S02 DataType tests, but do not use S02 coverage as a substitute where ObjectTemplate's physical multi-row aggregate/reverse-reference shape is materially different.

### Complete the DataType binding scenarios deferred from S02

Use actual ObjectTemplate candidate operations on caller-owned UoWs:

```text
ROW-07  explicit new property DTV binding × target DTV DEPRECATE
ROW-08A implicit property DTV binding × DT SET_DEFAULT
ROW-08B implicit property DTV binding × DT CLEAR_DEFAULT
```

Assert exact materialization and only serially explainable outcomes. The ObjectTemplate commit must hold the relevant DataType `FOR SHARE` protection until its own commit.

### Active model graph

Implement:

```text
ROW-09  OTV PUBLISH consumer × dependency DEPRECATE
```

At minimum exercise both distinct direct-dependency physical shapes:

1. published consumer property -> exact DTV, racing DTV DEPRECATE;
2. published child OTV -> exact parent OTV, racing parent OTV DEPRECATE.

Allowed outcomes are only:

```text
publish wins -> dependency deprecate fails active_dependency_conflict
OR
deprecate wins -> publish fails dependency_not_admissible
```

Never commit `PUBLISHED consumer -> DEPRECATED dependency`.

Also implement `ROW-10` active blocker removal against dependency deprecation, including the canonical variants:

```text
A consumer DEPRECATE × dependency DEPRECATE
B consumer DELETE_LINEAGE × dependency DEPRECATE
```

Assert only removal-first success or conservative dependency failure according to the frozen contract.

### Referential lifetime

Implement the S03-realizable `REF-01` reference-vs-delete behavior through actual ObjectTemplate operations, including at least:

- OT property exact DTV reference creation/rebinding × DataType lineage delete (exact/composite FK shape);
- an ObjectTemplate stable-lineage reference path available in S03 (for example component target) × target ObjectTemplate lineage delete, so the stable-lineage FK lifetime shape is exercised without inventing RelationshipDefinition behavior.

Use semantic prechecks for quality but prove the immediate FK is final race authority.

### Atomic multi-row aggregate

Implement `ATOMIC-01` for the OTV multi-row candidate shape. Prove a forced/natural failure after a partial persistence phase cannot commit a mixed generation across:

```text
OTV header/revision/status
properties
components
```

A narrow test-only persistence phase interception is permitted only under the frozen PGTEST escape-hatch rules: test code may pause/fail around a real production persistence call, but must not create a different production SQL/semantic path or add `if TESTING` hooks to production.

### Orchestration rules

All canonical concurrency scenarios use:

- real PostgreSQL;
- independent connections/transactions;
- deterministic DB blocker/barrier orchestration;
- `pg_blocking_pids()` for positive blocker proof where blocking is normative;
- no `sleep()` correctness orchestration;
- bounded timeouts only as safety nets;
- allowed outcome/forbidden state assertions rather than arbitrary winner assumptions;
- cleanup only after participating sessions terminate.

If two variants truly share the same authority/mechanism/orchestration, keep them traceable under the canonical scenario ID rather than inventing new PGTEST IDs.

## 19. Quality gates

Run and report at least:

```text
uv lock
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -m "not postgresql"
uv run pytest -m postgresql
```

PostgreSQL verification is mandatory for S03. Do not substitute SQLite/fakes/mocks for FK/locking/MVCC correctness.

Do not mark S03 `COMPLETED`; completion is a review decision after the pushed delta and verification evidence are inspected.

## Completion report

At the end provide:

- commit SHA and confirmation pushed to `origin/core_review`;
- concise files/layers added/changed;
- ObjectTemplate domain/application/persistence/API structure;
- effective-schema resolution strategy and how composite reads are snapshot-coherent;
- exact parent and DTV admission strategy proving locks live on the caller-owned UoW;
- historical property/component evolution strategy, including remove/re-add continuity;
- active-model-graph publication/deprecation realization;
- exact PGTEST IDs/variants implemented and semantic outcomes asserted;
- full quality-gate results and PostgreSQL version;
- any Ruff/Pyright suppression, test-only interceptor, retry or unusual workaround;
- any architecture/documentation contradiction found;
- confirmation no Object runtime/ownership/Relationship/relationship-capabilities or JSON Schema behavior was implemented;
- confirmation `status.md` was not marked completed by Codex.
