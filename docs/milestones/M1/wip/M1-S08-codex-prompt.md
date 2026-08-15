# Codex implementation prompt — M1-S08

**Status:** NON-NORMATIVE IMPLEMENTATION PROMPT.

This file is an execution aid for Codex. It does not override `AGENTS.md`, the FINAL/FROZEN M1 contract/steps, the globally FROZEN M1 architecture, or the ratified technology baseline.

## Assignment

Implement exactly:

```text
M1-S08 — Cross-domain integrity, destructive-operation and API/read closure
```

M1-S00 through M1-S07 are complete. S08 is a **closure** step, not a feature-expansion step. Implement the final frozen Object DELETE primitive and close the already-defined cross-domain reference/delete/API/read contracts. Do not start M1-S09 delivery/documentation work beyond what S08 itself requires.

## Mandatory pre-flight

Before changing implementation files, re-read and obey at minimum:

```text
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md
docs/milestones/M1/contract.md
docs/milestones/M1/steps.md
docs/milestones/M1/status.md

docs/milestones/M1/architecture/README.md
docs/milestones/M1/architecture/m1-final-consistency-review.md

docs/milestones/M1/architecture/datatype.md
docs/milestones/M1/architecture/objecttemplate.md
docs/milestones/M1/architecture/objecttemplate-lifecycle.md
docs/milestones/M1/architecture/object.md
docs/milestones/M1/architecture/object-runtime-state.md
docs/milestones/M1/architecture/object-ownership.md
docs/milestones/M1/architecture/object-lifecycle-changelog.md
docs/milestones/M1/architecture/relationship.md
docs/milestones/M1/architecture/relationship-definition.md
docs/milestones/M1/architecture/relationship-runtime.md

docs/milestones/M1/architecture/persistence-model.md
docs/milestones/M1/architecture/persistence-uow-concurrency.md
docs/milestones/M1/architecture/concurrency-semantic-matrix.md
docs/milestones/M1/architecture/concurrency-postgresql-realization-matrix.md
docs/milestones/M1/architecture/concurrency-postgresql-realization-object-ownership.md
docs/milestones/M1/architecture/concurrency-postgresql-realization-relationship.md
docs/milestones/M1/architecture/concurrency-postgresql-test-matrix.md

docs/milestones/M1/architecture/api-contract.md
docs/milestones/M1/architecture/api-wire-contract.md
docs/milestones/M1/architecture/api-read-contract.md
docs/milestones/M1/architecture/api-list-contract.md
docs/milestones/M1/architecture/api-error-contract.md
```

Confirm from the repository itself:

```text
M1 contract      = FINAL / FROZEN
M1 architecture  = globally FROZEN, including the S07 PAR-02 correction
M1 steps         = FINAL / FROZEN
M1-S00..S07      = COMPLETED
current step     = M1-S08
STACK-01..09     = RATIFIED
```

If another genuine frozen-architecture contradiction appears, stop the affected behavior and report it rather than choosing an implementation interpretation.

## Objective

At S08 exit:

```text
Object.DELETE is fully implemented and race-safe
+
DT/OT/RD whole-aggregate deletes account for every current M1 external reference shape
+
all remaining REF-01..06 semantic variants are executable and deterministic
+
lifecycle/read/list/error/public-route closure matches API-03
```

No supported mutation/delete may leave another current M1 domain invalid.

---

# 1. Final Object.DELETE capability

Implement public route exactly:

```text
DELETE /api/v1/core/objects/{object_id}
```

No body. No cascade/force/recursive/remediation options.

Missing current path Object:

```text
404 resource_not_found
{
  "resource_type": "object",
  "id": "<object uuid>"
}
```

Unlike Relationship DELETE, Object DELETE is **not** absence-idempotent.

Successful current delete:

```text
204 No Content
```

## 1.1 Object concurrency owner

Use the frozen owner:

```text
objects(O) FOR UPDATE
```

because DELETE removes the referenced Object identity.

The Object row is locked before current-state-dependent delete decisions. After any wait, use the current committed state observed through the acquired owner; do not derive deletion from a stale pre-lock snapshot.

## 1.2 Validate final intrinsic snapshot

The locked Object snapshot must be validated through the existing exact ObjectTemplate/DataType closure before it becomes the historical `DELETED.before` snapshot.

Persisted invalid/corrupt Object state remains:

```text
500 internal_error
```

Do not delete corrupt current state while silently writing a historical event that pretends it was valid.

## 1.3 Structural isolation precondition

DELETE requires exactly:

```text
incoming ownership edges = 0
outgoing ownership edges = 0
current factual Relationship associations = 0
```

No implicit DETACH, Relationship DELETE, subtree cleanup, move or remediation.

Count blockers semantically:

```text
ownership
    = count current object_components rows where
      child_object_id = O OR parent_object_id = O

relationship
    = count DISTINCT current factual relationship_id associated with O
      through runtime_relationship_resolutions.from_object_id/to_object_id
```

Do **not** count raw runtime-resolution rows as multiple Relationship blockers for one factual Relationship.

Normal pre-check failure:

```text
409 delete_blocked
{
  "resource_type": "object",
  "id": "<uuid>",
  "blockers": [
    {"type": "ownership", "count": N},
    {"type": "relationship", "count": M}
  ]
}
```

Include only non-zero blocker entries, in stable deterministic type order.

## 1.4 FK RESTRICT remains final race authority

The semantic pre-check is for deterministic diagnostics; it is not the final lifetime authority.

Current external Object references remain protected by immediate PostgreSQL FK `RESTRICT`:

```text
object_components.child_object_id
object_components.parent_object_id
runtime_relationship_resolutions.from_object_id
runtime_relationship_resolutions.to_object_id
```

If a reference wins after the pre-check but before physical DELETE, the Object DELETE must lose on the bounded known FK constraint and return `409 delete_blocked`, never expose SQL/table/constraint names.

Add a bounded persistence error carrying at least the semantic blocker type:

```text
ownership
relationship
```

A race-loser delete may report bounded `count=1`; it need not perform an unsafe/unbounded post-error scan inside an aborted transaction.

Unexpected IntegrityError remains `500 internal_error` through the existing outer failure boundary.

## 1.5 DELETE + lifecycle atomicity

For a real delete:

```text
locked final canonical Object snapshot = before

physical current Object delete
-> append DELETED event
-> commit
```

Event semantics:

```text
kind   = DELETED
before = final complete canonical Object snapshot
after  = null
```

No ownership or Relationship structural events are generated by Object DELETE because all such facts must already be absent.

Deletion and DELETED event are one semantic UoW. A forced event failure after the physical DELETE statement must rollback the deletion completely.

Historical lifecycle events have no live Object FK and survive Object deletion.

After Object deletion:

```text
GET /objects/{id}                       -> 404
GET /objects/{id}/lifecycle-events      -> 404 path target absent
GET /lifecycle-events?object_id={id}    -> historical events remain queryable
```

The global lifecycle changelog is historical authority; the nested route does not become a historical Object reconstruction API.

---

# 2. Cross-domain whole-lineage delete closure

Do not change the frozen domain delete semantics. Strengthen existing DataType/ObjectTemplate/RelationshipDefinition delete implementations and tests so every current M1 external reference shape is covered.

## 2.1 DataType DELETE_LINEAGE

External current authority remains exact ObjectTemplate property bindings:

```text
object_template_properties(datatype_id, datatype_version)
```

This includes declarations owned by DRAFT, PUBLISHED and DEPRECATED OTVs: a persisted DRAFT reference is still a real reference.

Normal `external_reference_count()` diagnostics remain bounded:

```text
blocker type = object_template_property
```

On a concurrent FK-race loser, preserve API-03.11 `delete_blocked.details.blockers`; do not return a bare `{resource_type,id}` details object. Translate the known FK to at least:

```text
{"type":"object_template_property","count":1}
```

Do not weaken `lineage header FOR UPDATE`, internal default cleanup or owned-version CASCADE.

## 2.2 ObjectTemplate DELETE_LINEAGE

Final M1 external blocker shapes are at least:

```text
child ObjectTemplate lineage / exact parent dependency
external ObjectTemplate component target
current Object exact OTV pin
RelationshipResolution endpoint lineage
```

The current pre-check already exposes semantic blocker categories; preserve/verify them.

Self-owned declarations/versions/default pointer are internal aggregate state and do not become external blockers.

On a concurrent FK-race loser, map the known constraint to the same bounded semantic blocker category and return API-03.11-conformant `blockers` with `count=1` rather than a bare delete_blocked details object.

Do not expose whether the losing FK was the stable parent FK or exact-parent composite FK as raw persistence detail; both are the same semantic child-ObjectTemplate dependency category.

## 2.3 RelationshipDefinition DELETE

Preserve accepted S06/S07 behavior:

```text
current factual Relationship count > 0
    -> 409 delete_blocked

no current factual Relationship
    -> delete Definition + owned Resolution set
```

Current factual Relationship FK `RESTRICT` remains final race authority. Keep the bounded relationship blocker count behavior already reviewed.

Historical lifecycle events never block RD.DELETE.

---

# 3. No semantic cascade across domains

Audit every root/owned-child `CASCADE` against external `RESTRICT`.

Owned-state CASCADE is allowed only after semantic root-delete admission:

```text
DataType              -> DataTypeVersion
ObjectTemplate        -> ObjectTemplateVersion
ObjectTemplateVersion -> local Property/Component
RelationshipDefinition-> RelationshipResolution
Relationship          -> RuntimeRelationshipResolution
```

Cross-domain/current references are never cleaned up by those cascades.

S08 must prove that external `RESTRICT` prevents the root delete before an internal CASCADE can erase evidence needed by another current domain.

---

# 4. Canonical T-REF completion

Use real PostgreSQL, independent transactions/UoWs, deterministic phase cuts and `pg_blocking_pids()` whenever blocking is an expected mechanism assertion. No `sleep()` correctness orchestration.

Audit the existing canonical census first. Reuse already-correct tests; do not duplicate IDs pointlessly. Add/complete the variants that only became fully semantic with final Object.DELETE.

## REF-01 — model reference creation × target lineage delete

Final census must have real semantic coverage for:

```text
OBJ.CREATE -> exact OTV      × OT.DELETE_LINEAGE
OT.REVISE  -> exact DTV      × DT.DELETE_LINEAGE
RD.CREATE  -> OT lineage     × OT.DELETE_LINEAGE
```

For each required variant, both relevant lifetime orders must be represented strongly enough that the FK is proven as final authority:

```text
reference wins -> delete blocked
root delete wins -> reference creation fails with bounded semantic missing-reference outcome
```

Do not claim coverage from a raw FK test when a real semantic operation for both operands now exists.

## REF-02 — ATTACH × OBJ.DELETE

Implement both variants:

```text
A parent deletion
B child deletion
```

Required outcomes:

```text
ATTACH/reference wins
    -> Object DELETE fails delete_blocked ownership

Object DELETE wins
    -> ATTACH cannot establish the reference
       parent path missing -> 404 when parent was deleted
       child operand missing -> 422 referenced_resource_not_found when child was deleted
```

Use actual FK/lock evidence, not process-local synchronization alone.

## REF-03 — REL.CREATE × OBJ.DELETE(endpoint)

Complete the S07-deferred semantic scenario.

Required outcomes:

```text
REL.CREATE current reference wins
    -> Object DELETE blocked by relationship

Object DELETE wins
    -> REL.CREATE cannot establish endpoint FK
    -> missing body endpoint remains 422 referenced_resource_not_found
```

Prove actual runtime Object FK arbitration.

## REF-04 — REL.CREATE × RD.DELETE

Already implemented in S07. Keep it green and include it in the final S08 REF census; do not rewrite working semantics.

## REF-05 — reference removal × OBJ.DELETE

Complete both variants:

```text
A DETACH × OBJ.DELETE
B REL.DELETE × OBJ.DELETE
```

The frozen allowed-outcome rule is:

```text
removal commits first
    -> Object DELETE may succeed

Object DELETE checks while current blocker is still committed
    -> conservative delete_blocked is allowed
```

No implicit waiting/remediation contract beyond the existing row/FK mechanics is invented.

Use deterministic ordering to prove the removal-first success case and at least one conservative/current-blocker case.

## REF-06 — aggregate CASCADE × external RESTRICT

Prove on real PostgreSQL that owned-state CASCADE never bypasses an external current reference.

Cover the aggregate shapes strongly, preferably bounded A/B/C variants under the same canonical authority:

```text
A DataType lineage with owned versions + external OTV property reference
B ObjectTemplate lineage with owned versions/declarations + external current reference
C RelationshipDefinition with owned Resolutions + external factual Relationship
```

For each, failed root delete leaves the root and its owned children intact; no partial cascade is committed.

At least one test must prove the actual PostgreSQL blocker relation/constraint behavior, not only application pre-check output.

---

# 5. Object DELETE concurrency regressions beyond canonical REF IDs

REALIZE-09 requires same-Object intrinsic mutation/delete serial composability.

Add deterministic owner-lock regressions covering Object DELETE against the non-key intrinsic writers:

```text
RENAME
DATA_CHANGE
SCHEMA_CHANGE
```

A parametrized/mechanically shared test is acceptable if each operand is a real semantic operation.

Required property:

```text
non-key writer first
    -> DELETE waits on Object owner, then deletes the committed latest state
       and DELETED.before reflects that latest state

DELETE first
    -> later intrinsic mutation observes current Object absent and fails 404
```

Do not introduce state_revision/CAS.

Add forced DELETED-event failure rollback proof:

```text
Object physically deleted inside UoW
-> event insert forced to fail
-> rollback
-> Object current state still exists
-> no DELETED event committed
```

---

# 6. Delete/reference diagnostic matrix

Create a bounded cross-domain test matrix asserting normal blocker details and race-loser mappings.

At minimum:

```text
DT.DELETE_LINEAGE
    object_template_property

OT.DELETE_LINEAGE
    child_object_template
    object_template_component
    object
    relationship_resolution

RD.DELETE
    relationship

OBJ.DELETE
    ownership
    relationship
```

Counts are semantic current blockers, not raw SQL affected-row counts.

For normal pre-check paths, assert exact counts where deterministic.

For race-loser FK translation, count `1` is acceptable when the exact current total is not safely available after the failed statement, but the blocker `type` must be semantically correct.

Every `delete_blocked` public response must follow the frozen shape:

```json
{
  "code": "delete_blocked",
  "message": "...",
  "details": {
    "resource_type": "...",
    "id": "...",
    "blockers": [
      {"type": "...", "count": 1}
    ]
  }
}
```

No constraint/table/column name may leak.

---

# 7. Lifecycle/read closure

Most lifecycle/read producers already exist from S04/S05/S07. S08 audits and completes, rather than inventing a second read model.

## 7.1 Global lifecycle route

Keep:

```text
GET /api/v1/core/lifecycle-events
ordering = (occurred_at,id) DESC
```

Verify exact first-class filters with real mixed-family data:

```text
kind
object_id
destination_object_id
relationship_id
relationship_definition_id
relationship_name
occurred_from
occurred_to
```

Positive and excluding/mismatch cases must be sufficient to prove each filter is actually applied.

Verify cursor/filter identity and keyset continuation.

## 7.2 Object-specific lifecycle route

Keep semantic predicate exactly:

```text
object_id = X OR destination_object_id = X
```

Verify mixed intrinsic + ownership + Relationship histories.

For a deleted Object:

```text
nested current-resource route -> 404
```

while global historical filtering still returns its historical events including DELETED and earlier structural events.

## 7.3 PERSIST-15 read-path indices

Do not add speculative indices.

Schema/metadata verification must continue to assert the frozen lifecycle indices, including:

```text
(occurred_at,id)
(object_id,occurred_at,id)
(destination_object_id,occurred_at,id)
(relationship_id,occurred_at,id)
(relationship_definition_id,occurred_at,id)
(kind,occurred_at,id)
partial (relationship_name,occurred_at,id) WHERE relationship_name IS NOT NULL
```

Do not write brittle tests requiring PostgreSQL's planner to choose a specific index for tiny test datasets; prove structural presence and compatible query shape.

---

# 8. API surface closure

## 8.1 Canonical 32 mutation census

Build an explicit expected method/path inventory from API-02 and assert every mutation exists exactly once after Object DELETE is added.

The 32 semantic mutations are the frozen census; do not derive scope from whatever OpenAPI happens to contain.

Object DELETE is the final missing public mutation surface:

```text
DELETE /api/v1/core/objects/{object_id}
```

## 8.2 Frozen read/list routes

Audit all API-03.9/API-03.10 routes and ensure every read intentionally deferred until producer availability is now present.

Assert expected path/method pairs for:

```text
DataType lineage/version reads/lists
ObjectTemplate lineage/version/effective-schema/capability reads
Object intrinsic/list/components/owner/relationships/lifecycle reads
RelationshipDefinition reads/list
Relationship factual GET
Global lifecycle list
```

## 8.3 Forbidden public surface

Assert globally:

```text
no PUT
no PATCH
no generic /actions
no standalone RelationshipResolution CRUD
no RuntimeRelationshipResolution public route
no object_components CRUD route
no lifecycle mutation/detail CRUD
no generic property/slot child mutation CRUD
no Object cascade/force delete route
no JSON Schema compiler/projection endpoint
```

## 8.4 OpenAPI smoke

Perform a bounded OpenAPI review/test:

- route inventory matches the frozen surface;
- command bodies remain strict;
- lifecycle discriminated union contains all nine M1 event kinds in the correct family DTOs;
- Object DELETE has no request body and 204 success;
- no persistence-shaped runtime child DTO is exposed.

OpenAPI is an adapter smoke artifact, not semantic authority.

---

# 9. Error catalog closure

Audit API-03.11 finite code/status mapping across the integrated API.

Create an explicit expected catalog/mapping test or equivalent traceable census for all frozen codes:

```text
400 invalid_request
400 invalid_cursor
404 resource_not_found
422 referenced_resource_not_found
422 semantic_validation_failed
409 stale_revision
409 lifecycle_state_conflict
409 version_source_conflict
409 default_version_unavailable
409 dependency_not_admissible
409 qualified_name_conflict
409 default_version_conflict
409 active_dependency_conflict
409 delete_blocked
409 ownership_slot_unavailable
409 ownership_conflict
409 ownership_mismatch
409 ownership_cycle
409 schema_change_blocked
409 relationship_definition_equivalent
409 relationship_definition_conflict
409 relationship_fact_conflict
500 internal_error
```

Reuse existing API tests where they already provide strong semantic evidence; add missing observations rather than duplicating everything.

Verify:

```text
404 only for missing URI/path target identity
missing command operands -> 422
idempotent domain no-op/convergence -> success
unexpected server/invariant failure -> only internal_error/500
```

No generic `conflict`/`state_conflict` escape-hatch code is allowed.

Add representative assertions that public failure bodies never contain raw SQL text, table/column names, PostgreSQL constraint names or stack traces.

---

# 10. Earlier-slice cross-domain regression closure

Run/reinforce earlier delete/reference behavior now that all producer domains exist:

- DT whole-lineage delete with every current exact DTV property reference shape;
- OT whole-lineage delete with child lineage, component target, Object pin and Resolution endpoint references;
- RD delete with real factual Relationship blocker;
- ObjectTemplate deprecation remains unaffected by runtime Object or stable-lineage Resolution refs where the frozen lifecycle rules say they do not block;
- historical lifecycle events never act as current FK blockers;
- removing the final current blocker through the correct semantic operation enables the corresponding root delete.

Do not add implicit cross-domain cleanup.

---

# 11. Persistence/migration boundary

No new table or column is expected in S08.

Do not rewrite `0001` or `0002_resolution_name_nonkey`.

A new migration is **not** expected unless an actual frozen-schema contradiction is discovered, in which case stop and report it instead of silently changing persistence.

Preserve:

```text
13 authoritative tables
current PK/FK/CHECK/index meanings
PAR-02 corrected RelationshipResolution non-key name schema
```

---

# 12. Scope and layer discipline

Do not introduce:

```text
new domain capability beyond frozen S08 closure
subtree/cascade Object delete
delete orchestration endpoint
force/remediation flags
new advisory gate
global Object/Relationship lock
Object state_revision / ETag
generic repository framework
ORM Session / AsyncSession
SERIALIZABLE baseline
generic retry middleware
new public child CRUD
Relationship versioning/properties
source/target or forward/reverse semantics
historical Object reconstruction API
background jobs / 202 behavior
Docker/Testcontainers
```

Application/domain modules remain free of FastAPI/Pydantic/SQLAlchemy imports. SQLAlchemy remains persistence-only.

---

# 13. Verification gate

Use external `TEST_DATABASE_URL`; PostgreSQL tests run serially on one shared DB unless isolated DB targets are explicitly provided.

Run and report at minimum:

```text
uv lock --check
uv sync --locked
uv build
Ruff format/check
Pyright strict
non-PostgreSQL suite
full real-PostgreSQL suite
S08 / complete T-REF deterministic concurrency selection
migration/schema/drift tests
OpenAPI/API closure tests
```

Report exact PostgreSQL server version and exact pass counts.

No `sleep()` correctness orchestration and no generic flaky reruns.

At completion report:

- implementation commit SHA;
- changed-file summary;
- exact quality/test results;
- PostgreSQL version;
- Object DELETE semantics/mechanism summary;
- canonical REF-01..06 final variant census and mechanism evidence;
- cross-domain blocker detail matrix covered;
- API 32-mutation/read-route/error-catalog closure results;
- confirmation no new table/column/gate/migration/S09 capability was added;
- any unverified requirement or newly discovered architecture contradiction.

Do not mark `docs/milestones/M1/status.md` COMPLETED; reviewer owns completion status.
