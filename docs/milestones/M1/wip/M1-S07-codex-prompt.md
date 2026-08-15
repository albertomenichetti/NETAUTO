# Codex implementation prompt — M1-S07

**Status:** NON-NORMATIVE IMPLEMENTATION PROMPT.

This file is an execution aid for Codex. It does not override `AGENTS.md`, the frozen M1 contract/architecture/steps, or the ratified technology baseline.

## Assignment

Implement exactly:

```text
M1-S07 — Runtime Relationship and relationship lifecycle vertical slice
```

from `docs/milestones/M1/steps.md`.

M1-S00 through M1-S06 are complete. Do not implement the final M1-S08 `Object.DELETE`/cross-domain closure or broaden the Relationship model beyond the frozen M1 runtime contract.

## Mandatory pre-flight

Before changing implementation files, re-read and obey at minimum:

```text
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md
docs/milestones/M1/contract.md
docs/milestones/M1/architecture/README.md
docs/milestones/M1/architecture/m1-final-consistency-review.md
docs/milestones/M1/steps.md
docs/milestones/M1/status.md

docs/milestones/M1/architecture/relationship.md
docs/milestones/M1/architecture/relationship-definition.md
docs/milestones/M1/architecture/relationship-resolution.md
docs/milestones/M1/architecture/relationship-runtime.md
docs/milestones/M1/architecture/relationship-concurrency.md
docs/milestones/M1/architecture/relationship-consistency-review.md
docs/milestones/M1/architecture/object-lifecycle-changelog.md
docs/milestones/M1/architecture/object.md
docs/milestones/M1/architecture/persistence-model.md
docs/milestones/M1/architecture/persistence-uow-concurrency.md
docs/milestones/M1/architecture/concurrency-semantic-matrix.md
docs/milestones/M1/architecture/concurrency-postgresql-realization-matrix.md
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
M1 architecture  = globally FROZEN as a set
M1 steps         = FINAL / FROZEN
M1-S00..S06      = COMPLETED
current step     = M1-S07
STACK-01..09     = RATIFIED
```

The S07 pre-flight corrected only verification decomposition: semantic `REF-03` (`REL.CREATE × OBJ.DELETE`) and Relationship `REF-05` (`REL.DELETE × OBJ.DELETE`) are now explicitly deferred to S08 because final `Object.DELETE` is delivered there. Do not introduce a private/fake Object delete merely to execute those IDs in S07.

If normative authorities conflict, stop the affected behavior and report the contradiction instead of choosing an implementation interpretation.

## Objective

Deliver the complete factual Relationship vertical capability:

```text
exact RelationshipResolution selector
+ stable Object endpoint assignments
-> endpoint admission
-> deterministic complete RuntimeRelationshipResolution closure
-> exact-view factual arbitration / semantic convergence
-> factual Relationship identity
-> semantic factual/Object-relative reads
-> complete Relationship lifecycle semantic-view event set
-> exact-ID idempotent / ABA-safe DELETE
```

At the end of S07, a caller can create, converge on, read, navigate and delete current factual Relationships without exposing raw runtime rows or weakening the frozen model-plane certification.

## Hard scope boundary

S07 MUST NOT implement or introduce:

```text
final Object.DELETE
private/test-only semantic Object DELETE command
ObjectTemplate/DataType destructive-operation closure owned by S08
new RelationshipDefinition mutation semantics
RelationshipDefinitionVersion / typed Relationship properties
Relationship property storage
new persistence tables/columns or Alembic migration
new advisory gate / global Relationship graph lock
endpoint-pair hash lock / canonical endpoint-pair identity
runtime source/target or forward/reverse semantics
caller-supplied Relationship id
public RuntimeRelationshipResolution CRUD/read resource
standalone RelationshipResolution CRUD
partial runtime-row repair/merge
ON CONFLICT DO NOTHING row-by-row aggregate assembly
generic repository framework
generic retry middleware
SERIALIZABLE baseline
ORM Session / AsyncSession
background jobs / 202 semantics
Docker/Testcontainers/test-DB provisioning
```

Use the frozen S01 physical tables unchanged.

## 1. Preserve and extend the accepted S06 model-plane

Build on the accepted S06 `src/netauto/domain/relationships.py`, `src/netauto/application/relationshipdefinitions.py` and `src/netauto/persistence/relationships.py`. Do not create a competing Relationship model-plane representation.

Add only the runtime concepts required by M1, conceptually:

```text
Relationship
    id: UUID
    relationship_definition_id: UUID

RuntimeRelationshipResolution
    relationship_id: UUID
    relationship_definition_id: UUID
    resolution_id: UUID
    from_object_id: UUID
    to_object_id: UUID

RelationshipView / ObjectRelationshipView
    semantic projections, not persistence rows
```

Relationship id is kernel-generated UUIDv4 and immutable. Runtime resolution rows have no surrogate id and no independent lifecycle.

Domain code remains plain synchronous Python with no SQLAlchemy/Pydantic/FastAPI imports.

## 2. CREATE selector and operand boundary

Public route:

```text
POST /api/v1/core/relationships
```

Strict body exactly:

```json
{
  "resolution_id": "<uuid>",
  "from_object_id": "<uuid>",
  "to_object_id": "<uuid>"
}
```

No Relationship id, definition id, names, template metadata or extra fields are caller-supplied. `from_object_id == to_object_id` is transport-valid.

Missing body operands are referenced-resource failures, not path 404:

```text
missing selected resolution -> 422 referenced_resource_not_found
    resource_type = relationship_resolution
    id = supplied resolution_id

missing from/to Object -> 422 referenced_resource_not_found
    resource_type = object
    id = supplied Object UUID
```

Preserve the supplied semantic selector in FK-race translations as well; do not leak constraint names.

## 3. Endpoint admission

Selected `RelationshipResolution R` must exist as part of one valid complete certified Definition aggregate.

Admission is based only on stable Object template lineage:

```text
from_object.template_id == R.from_template_id
OR descendant-of R.from_template_id

to_object.template_id == R.to_template_id
OR descendant-of R.to_template_id
```

Do not inspect or admit exact ObjectTemplate versions, Object properties, canonical name or OTV lifecycle/default state.

Do not take explicit lifecycle `FOR SHARE` locks on endpoint Object/Definition rows merely to establish stable FK references. Final current-reference lifetime arbitration remains the immediate PostgreSQL FK/KEY SHARE machinery.

Endpoint incompatibility is `422 semantic_validation_failed`, with bounded violations such as `from_object_id` / `to_object_id` + a stable lineage compatibility rule.

Self-loop succeeds when both endpoint admission predicates hold.

Persisted malformed Definition/Resolution membership or inheritance state is `internal_error`, not caller validation.

## 4. Factual semantics — non-symmetric

For a non-symmetric Definition with reciprocal Resolutions `R1` and `R2`, selected Resolution orientation is factual semantics.

Given CREATE through:

```text
R1 / A -> B
```

derive exactly:

```text
R1 / A -> B
R2 / B -> A
```

Do not add inverse assignments merely because inheritance overlap makes them type-compatible. Such inversions would represent the opposite factual Relationship.

For a self-loop, the two Resolution IDs still produce two exact runtime rows when the Definition has two distinct non-symmetric perspectives.

## 5. Factual semantics — symmetric

For `symmetric=true`, the factual endpoint pair is unordered.

Given endpoint Objects A/B, derive the complete set of all distinct exact tuples:

```text
(resolution_id, from_object_id, to_object_id)
```

obtained from every model Resolution and both assignments `(A,B)` / `(B,A)` that satisfy that Resolution's stable-lineage admission.

Expected bounded shapes include:

```text
same-template, A != B
    -> 2 runtime rows using one Resolution id

same-template self-loop
    -> 1 exact runtime row

different-template disjoint spaces
    -> normally 2 reciprocal rows

different-template inheritance-overlap spaces
    -> up to 4 distinct runtime rows
```

Exact-deduplicate the closure, then canonical-sort it by:

```text
(resolution_id, from_object_id, to_object_id)
```

before persistence insertion. This ordering is an implementation/deadlock/debug determinism rule, not semantic orientation.

## 6. Complete closure validation

Every current factual Relationship must have exactly the deterministic closure derived from its Definition + factual endpoint pair.

No supported current state may contain:

```text
header without complete runtime child set
partial closure
rows from another Definition
mixed factual endpoint pair
extra inverse non-symmetric row
missing applicable symmetric row
```

The composite FK denormalized `relationship_definition_id` remains mandatory and authoritative as defined by PERSIST-07. Do not remove it.

For current factual reads/convergence/delete, validate persisted aggregate coherence strongly enough that a DB-valid but semantically incomplete/mixed runtime aggregate maps to `internal_error` rather than being silently projected as valid.

A useful validation seam is to choose one exact current runtime row as a factual selector, load its complete Definition and endpoint stable lineage facts, rederive the expected closure, and compare exact sets. For collection reads, bulk validation is preferable to an avoidable per-item N+1 when straightforward, but correctness takes priority over speculative abstraction.

## 7. Exact-view authority

Final factual uniqueness authority is unchanged:

```text
runtime_relationship_resolutions
PRIMARY KEY (resolution_id, from_object_id, to_object_id)
```

No global Relationship lock is added.

Before attempting a new fact, query the caller-selected exact view:

```text
(resolution_id, from_object_id, to_object_id)
```

If it is already current:

- load/validate its complete factual Relationship;
- converge on that exact Relationship id;
- no current-state mutation;
- no lifecycle event;
- public result is 200, not 409.

## 8. Candidate-closure conflict boundary

After deriving a candidate closure, inspect current exact rows as useful before insertion.

The frozen public distinction is:

```text
selected exact view is current
    -> semantic convergence on its factual Relationship

selected exact view absent,
but another candidate closure view is current under a distinct fact
    -> 409 relationship_fact_conflict
    -> never merge/reparent/repair partial facts
```

In a valid complete committed dataset, an equivalent factual winner normally contains the selected view too. The `relationship_fact_conflict` branch remains the bounded defensive semantic outcome for a candidate closure that collides with a distinct current factual fact rather than the selected-view convergence case.

Unexpected persisted partial/incoherent aggregate state remains `internal_error`; do not use `relationship_fact_conflict` to hide corruption that violates the complete-closure invariant.

## 9. New factual CREATE transaction

A single candidate attempt uses one write UoW at `READ COMMITTED`:

```text
load selected Resolution + complete Definition
load from/to Objects
validate selected endpoint admission
lookup selected exact view
    current -> converge/no-op
    absent  -> continue
derive complete deterministic closure
validate closure/current conflict facts
create new kernel Relationship UUID
INSERT Relationship header
INSERT complete closure in canonical exact-row order
if all exact-view inserts succeed:
    ONE lifecycle metadata observation statement over complete closure
    derive complete distinct RELATIONSHIP_CREATED semantic-view event set
    INSERT complete event set
COMMIT
```

No lifecycle metadata SELECT occurs before complete closure insertion has succeeded.

## 10. PK collision and semantic-UoW restart

An exact-view PK collision is a specific expected arbitration signal, not a row-level merge signal.

If any runtime closure INSERT hits the exact-view PK:

```text
abort/escape the candidate transaction
-> rollback the ENTIRE candidate UoW
   (header + every earlier closure row + any current writes)
-> start a FRESH semantic UoW
-> re-read caller-selected exact view and all current state required by CREATE
```

Never catch the PostgreSQL unique violation and continue querying inside the aborted transaction.

Never use per-row `ON CONFLICT DO NOTHING`, savepoint partial merge, or attach candidate rows to the winner.

Fresh semantic restart outcomes:

```text
winner selected view still current
    -> validate winner aggregate
    -> converge 200 on winner id
    -> no second event set

winner disappeared before fresh convergence read
    -> reevaluate from current state
    -> may create a NEW Relationship Y with a new UUID

selected view absent but distinct current closure conflict remains
    -> relationship_fact_conflict
```

If another exact arbitration collision occurs during a legitimately restarted candidate, restart the complete semantic UoW again under this same narrow collision contract; this is not generic transient/deadlock retry middleware.

The UUID generated by every rolled-back loser candidate is discarded and must never become a current identity.

## 11. Persistence collision/error translation

Add bounded persistence signals for at least:

```text
exact runtime-view PK collision
selected/model Resolution or Definition reference loss
from/to Object reference loss
unexpected aggregate/reference corruption
```

Translate only known constraints. Preserve semantic operand UUIDs in public details where known. Unexpected `IntegrityError` remains internal.

Current Definition/Object FKs are `RESTRICT`; runtime rows continue to use the frozen composite same-Definition FKs.

No migration.

## 12. Lifecycle semantic-view observation — hard requirement

Relationship lifecycle event metadata uses **exactly one SQL metadata-observation statement per real factual transition**.

The statement must observe, in one READ COMMITTED MVCC snapshot, all metadata required by the complete event set:

```text
all current runtime semantic access rows of Relationship X
current relationship_resolutions.name for each row
from Object canonical_name
to Object canonical_name
```

For CREATE it runs only after the complete candidate closure has been inserted successfully.

For DELETE it runs before the current closure is removed.

Do not build the event set with separate per-row Resolution/Object metadata SELECTs.

Do not acquire `FOR SHARE`/`FOR UPDATE` merely to freeze event display metadata.

It is acceptable and often preferable for the one statement to return one metadata row per runtime closure row and perform semantic dedup in pure/domain/application code, as long as every row comes from that same statement snapshot. The one-statement rule concerns the observation boundary, not whether SQL `DISTINCT` or Python performs final dedup.

## 13. Lifecycle semantic-view dedup and shape

One factual transition emits one event for every distinct:

```text
(object_id, destination_object_id, relationship_name)
```

not one event per RuntimeRelationshipResolution row.

Relationship event fields exactly:

```text
id                         PostgreSQL generated
occurred_at                transaction_timestamp()
kind                       RELATIONSHIP_CREATED | RELATIONSHIP_DELETED
object_id
canonical_name
destination_object_id
destination_canonical_name
relationship_id
relationship_definition_id
relationship_name
```

No:

```text
before / after
slot fields
resolution_id
source/target
forward/reverse
direction
```

Sort the derived semantic event views deterministically before event insertion, e.g. `(object_id,destination_object_id,relationship_name)`, without making that ordering a semantic identity.

Event id/time remain PostgreSQL-generated from the existing table defaults.

Examples to verify:

```text
ordinary non-symmetric two-object fact -> normally 2 events
symmetric same-template distinct objects -> 2 events
symmetric self-loop -> 1 event
non-symmetric self-loop -> 2 events with distinct names
symmetric inheritance-overlap closure with 4 raw rows -> typically 2 semantic events after dedup
```

## 14. Historical metadata snapshot semantics

`relationship_name`, `canonical_name` and `destination_canonical_name` become historical event metadata after insertion.

A concurrent Definition RENAME or Object RENAME may cause the event set to contain the complete committed old metadata snapshot or a later complete committed metadata snapshot according to the one observation statement.

For non-symmetric Definition RENAME, one Relationship event set must never contain a half-old/half-new Resolution-name generation.

If two endpoints are renamed independently, any name pair that genuinely existed in the single committed database snapshot used by the observation statement is valid. Combining values from two separate statement snapshots is forbidden.

A rename committed after the lifecycle observation statement but before Relationship commit does not invalidate the captured event set.

`occurred_at` is transaction-start time. Tests must include the valid case where an event's `occurred_at` precedes a metadata rename that commits before the later metadata observation whose value the event captures.

## 15. Relationship CREATE lifecycle atomicity

Current factual header + complete runtime closure + complete creation event set are one semantic write UoW.

Any event-observation or event-insert failure after candidate closure insertion must rollback the entire factual candidate.

A convergence/no-op CREATE produces zero new lifecycle events.

## 16. Exact Relationship DELETE

Public route:

```text
DELETE /api/v1/core/relationships/{relationship_id}
```

No request body and no semantic-tuple alternative.

Concurrency owner:

```text
Relationship header FOR UPDATE
```

Transaction:

```text
SELECT exact Relationship X FOR UPDATE
absent
    -> 204 idempotent no-op
    -> no lifecycle event
present
    -> load/validate complete current closure
    -> ONE lifecycle metadata observation statement over current closure
    -> capture complete distinct RELATIONSHIP_DELETED semantic event set
    -> DELETE Relationship header
       (owned runtime closure CASCADE)
    -> INSERT captured complete event set
    -> COMMIT
```

The semantic projection must be captured before closure removal.

No individual runtime row delete surface exists.

## 17. DELETE concurrency and ABA

Concurrent `DELETE(X) × DELETE(X)`:

```text
one locks/removes X + one complete deletion event set
waiter observes X absent
waiter -> 204 no-op / no second event set
```

Recreating the same semantic association after X is deleted creates a new Relationship UUID Y.

A late `DELETE(X)` after Y exists is a no-op and cannot delete Y.

Validate both:

```text
CREATE converges on X -> DELETE X -> final absent
DELETE X -> recreate Y -> late DELETE X -> Y remains current
```

## 18. Factual Relationship GET

Implement:

```text
GET /api/v1/core/relationships/{relationship_id}
```

Missing exact path identity -> 404 `resource_not_found`.

Canonical response:

```json
{
  "id": "<uuid>",
  "relationship_definition_id": "<uuid>",
  "views": [
    {
      "object_id": "<uuid>",
      "destination_object_id": "<uuid>",
      "name": "hosts"
    }
  ]
}
```

`views` is the distinct current semantic-view set, not raw runtime closure rows. Current names come from current RelationshipResolution metadata; historical event names are separate.

Use a coherent SQL statement or existing `CoherentReadUnitOfWork` for any multi-statement validation/projection so a factual GET cannot expose a partial/mixed aggregate snapshot.

Return views deterministically for reproducibility, but do not invent forward/reverse semantic ordering.

Persisted incomplete/mixed closure -> `internal_error`.

## 19. Object-relative Relationship read

Implement the previously deferred route:

```text
GET /api/v1/core/objects/{object_id}/relationships
```

Missing path Object -> 404 `resource_not_found`.

Projection item exactly:

```json
{
  "relationship_id": "<uuid>",
  "relationship_definition_id": "<uuid>",
  "object_id": "<path object uuid>",
  "destination_object_id": "<uuid>",
  "name": "hosts"
}
```

Raw discovery uses current runtime rows with:

```text
from_object_id = path object
```

then semantic-deduplicates overlapping exact runtime paths.

List contract:

```text
ordering = (relationship_id, destination_object_id, name) ASC
filters  = exact relationship_definition_id, exact name
page     = {items,next_cursor}
limit    = default 100, max 500
cursor   = opaque keyset, route/filter-specific; limit excluded from query identity
```

One page must be snapshot-coherent. Current Definition rename may affect membership/order between separate page requests according to the already-frozen concurrent-page semantics.

Do not expose raw runtime resolution IDs.

## 20. Extend lifecycle public read union

The S05 lifecycle response union currently contains intrinsic + ownership families. Extend it with exactly the Relationship structural family:

```text
RELATIONSHIP_CREATED
RELATIONSHIP_DELETED
```

Canonical DTO fields are the Relationship event fields from §13; no meaningless `before`/`after` nulls or slot fields.

The existing global and Object-specific lifecycle routes must now parse/serialize Relationship event rows. Existing relationship filters (`relationship_id`, `relationship_definition_id`, `relationship_name`) become meaningfully populated and should be exercised.

Object-specific timeline semantics remains:

```text
object_id = path Object
OR destination_object_id = path Object
```

so both endpoint perspectives are visible. Do not add a standalone lifecycle detail route.

## 21. HTTP success/error mapping

Relationship CREATE:

```text
new factual Relationship
    -> 201 Created
    -> Location: /api/v1/core/relationships/{id}
    -> factual Relationship DTO

selected exact-view convergence on current fact
    -> 200 OK
    -> same factual Relationship DTO
    -> no duplicate event set
```

Do not advertise a newly-created Location requirement on the 200 convergence path.

Relationship DELETE:

```text
current exact id -> 204 No Content
already absent exact id -> 204 No Content
```

Relationship GET missing -> 404 `resource_not_found`.

Known CREATE failures:

```text
missing selected resolution / missing Objects
    -> 422 referenced_resource_not_found

endpoint lineage incompatibility
    -> 422 semantic_validation_failed

candidate closure conflicts with distinct current factual Relationship
    -> 409 relationship_fact_conflict

persisted impossible aggregate/closure/metadata state
    -> 500 internal_error
```

Never expose SQL/table/constraint details.

## 22. RD.DELETE strengthening in S07

S06 already implements RD.DELETE against the physical `relationships.relationship_definition_id` blocker authority. Now add semantic/API regression coverage using **real S07-created factual Relationships**:

```text
current factual Relationship exists
    -> RD.DELETE = 409 delete_blocked with bounded relationship blocker count

REL.DELETE removes final factual blocker
    -> subsequent RD.DELETE may succeed
```

Also execute canonical `REF-04 REL.CREATE × RD.DELETE` in both relevant serial orders using real semantic operations and actual FK lifetime arbitration.

Do not acquire the RelationshipDefinition conflict gate from runtime Relationship CREATE/DELETE.

## 23. Object DELETE scenario boundary

Per corrected frozen `steps.md`, do not claim semantic `REF-03` or Relationship `REF-05` complete in S07 because final `Object.DELETE` is S08.

S07 must nevertheless prove directly on real PostgreSQL that current RuntimeRelationshipResolution Object references are immediate `RESTRICT` authorities and rollback correctly. Use raw/persistence-level target deletion attempts where needed, without exposing a private application `Object.DELETE` capability.

S08 will execute the final semantic races:

```text
REF-03 REL.CREATE × OBJ.DELETE(endpoint)
REF-05B REL.DELETE × OBJ.DELETE
```

## 24. Deterministic real-PostgreSQL verification

Use external `TEST_DATABASE_URL`, independent UoWs/connections and the existing deterministic semantic-concurrency harness. Use `pg_blocking_pids()` for expected blocker relations. No `sleep()` orchestration, no generic retries, no production pause/debug hooks.

Implement all S07-realizable canonical scenarios and mechanism regressions.

### ARB-05 — equivalent Relationship CREATE

A. non-symmetric reciprocal selectors:

```text
R1 / A -> B
×
R2 / B -> A
```

must converge to one factual Relationship, one complete closure and one creation event set.

B. symmetric inverse assignment must converge to one fact.

C. inheritance-overlap symmetric multi-view case must converge with complete bounded closure and semantic event dedup.

Prove actual exact-view PK arbitration, not a process-local lock.

### ARB-06 — identical exact-ID DELETE

Concurrent `DELETE(X) × DELETE(X)` -> one real deletion/event set + one 204 no-op.

### ARB-07 — ABA / restart

A. delete X, recreate same semantic association as Y, late delete X -> Y survives.

B. CREATE loser experiences real exact-view collision; winner disappears before the loser's fresh convergence read; loser restarts from current state and may create Y. Prove old loser candidate UUID/partial rows are absent.

### REF-04 — REL.CREATE × RD.DELETE

Both lifetime orders:

```text
CREATE current reference wins
    -> RD.DELETE blocked/fails

RD.DELETE wins
    -> CREATE cannot establish selected Resolution/Definition reference
```

Use actual FK/lock blocker evidence.

### SNAP-01 — RD.RENAME × real REL.CREATE/DELETE

Prove entire event set uses one committed old-name generation OR one committed new-name generation, never half-old/half-new. Cover both transition directions strongly enough to protect CREATE-after-closure and DELETE-before-removal observation ordering.

### SNAP-02 — OBJ.RENAME × real REL.CREATE/DELETE

No Object lock solely for event metadata. Event captures a committed old/new endpoint display snapshot according to the observation point.

### SNAP-03 — two endpoint renames / one statement snapshot

Create deterministic cuts around the single metadata observation statement and independent endpoint renames. Assert only canonical-name combinations that existed in that one committed statement snapshot. Include the valid `occurred_at`-before-later-metadata-observation case using PostgreSQL clock observations rather than sleep timing.

### ATOMIC-02 — later closure-row collision rollback

Force/prove a **real PostgreSQL exact-view PK collision on a later candidate closure row** after the candidate header and at least one earlier closure row have been written. The whole candidate UoW must rollback: no loser header, no earlier loser rows, no loser events.

A targeted persistence setup may create the bounded DB state necessary to force the later-row database collision; do not weaken production aggregate semantics or fake the IntegrityError in memory.

### ATOMIC-03 — DELETE rollback

Force a narrow failure after factual removal work begins / before complete deletion event set commits. X + its complete closure remain current and no deletion event commits.

Also add direct CREATE event failure rollback coverage if not already subsumed by another strong test.

### PAR-01 — REL.CREATE × OBJ.RENAME

Must not block solely because runtime FKs protect Object identity. Event metadata uses SNAPSHOT semantics rather than writer serialization.

### PAR-02 — REL.CREATE × RD.RENAME

Must not block solely because runtime FKs protect Definition/Resolution identity. Non-key RD rename remains compatible with FK key protection.

### PAR-05 — unrelated REL.CREATE × unrelated REL.CREATE

No global runtime Relationship serialization. Prove disjoint facts can progress concurrently; runtime operations do not acquire `RELATIONSHIP_DEFINITION_CONFLICT_GATE`.

## 25. Additional REALIZE-13/14/15 mechanism regressions

Beyond the canonical IDs above, protect the detailed realization:

- closure rows inserted in canonical exact-key order;
- collision on first and later closure row causes whole-UoW rollback;
- no row-per-row `ON CONFLICT` merge;
- rolled-back loser UUID never becomes current;
- fresh-UoW convergence only after rollback;
- delete absent is no-op/no event;
- CREATE-converge-then-DELETE valid final absent;
- metadata observation CREATE occurs after complete closure insertion;
- metadata observation DELETE occurs before closure removal;
- exactly one metadata observation statement is used per real transition;
- event semantic dedup is from that one snapshot;
- runtime mutation does not take RD conflict gate;
- `REL.CREATE × OBJ.DATA_CHANGE` and `REL.CREATE × OBJ.SCHEMA_CHANGE` do not artificially serialize solely on Object FK protection where no other predicate applies;
- Relationship FK/reference mechanics still block delete/lifetime operations where required;
- no metadata row locks are added solely for lifecycle projection.

## 26. Domain/application/persistence verification

Cover at minimum:

### Runtime domain

- selected Resolution membership/Definition coherence;
- non-symmetric reciprocal closure;
- same-template non-symmetric self-loop;
- symmetric same-template distinct pair;
- symmetric same-template self-loop;
- symmetric different-template disjoint pair;
- symmetric inheritance-overlap closure up to four exact rows;
- exact tuple dedup and canonical ordering;
- stable-lineage endpoint compatibility/rejection;
- no exact OTV dependency;
- semantic lifecycle-view dedup cardinalities.

### Application/persistence

- missing resolution/Object operand boundaries;
- selected exact-view convergence;
- candidate closure conflict boundary;
- current factual aggregate corruption -> internal;
- DB-valid incomplete closure -> internal on GET/convergence/delete/Object-relative read;
- same-Definition composite FK integrity;
- Object FK `RESTRICT` and rollback mechanics;
- Definition FK `RESTRICT` and strengthened RD.DELETE behavior;
- exact-view PK authority;
- fresh semantic UoW restart after collision;
- exact-ID DELETE no-op/ABA;
- lifecycle event family row shape and DB id/time defaults;
- lifecycle create/delete event-set atomicity;
- historical events survive current Relationship deletion.

## 27. API verification

Exercise:

```text
POST   /api/v1/core/relationships
GET    /api/v1/core/relationships/{relationship_id}
DELETE /api/v1/core/relationships/{relationship_id}
GET    /api/v1/core/objects/{object_id}/relationships
GET    /api/v1/core/lifecycle-events
GET    /api/v1/core/objects/{object_id}/lifecycle-events
```

Verify:

- strict Relationship CREATE body, unknown/null/wrong carriers rejected;
- self-loop not transport-rejected;
- 201 + Location new vs 200 convergence;
- exact factual GET projection and semantic view dedup;
- DELETE current and absent both 204 no body;
- Object-relative list ordering/filter/cursor contract;
- missing path Relationship/Object vs missing body operand distinction;
- `relationship_fact_conflict` finite mapping;
- relationship lifecycle DTO has no intrinsic/ownership-only fields;
- global lifecycle filters `relationship_id`, `relationship_definition_id`, `relationship_name` work against produced Relationship events;
- Object-specific timelines expose both endpoint perspectives;
- no standalone Resolution/runtime-row route appears;
- no final Object.DELETE success capability is introduced by S07.

## 28. Scope/layer regressions

Keep/add cheap checks proving:

- domain/application Relationship modules do not import FastAPI/Pydantic/SQLAlchemy;
- application code constructs no SQLAlchemy statements;
- no new migration/table/column/gate;
- runtime Relationship routes are exactly the S07 surface;
- no public RuntimeRelationshipResolution/standalone RelationshipResolution CRUD;
- no source/target/forward/reverse public fields;
- lifecycle OpenAPI discriminated union now includes intrinsic + ownership + Relationship families, with exact kind mappings;
- persistence metadata remains the frozen 13-table authority.

## 29. Quality gates

Run and report at minimum:

```text
uv lock --check
uv sync --locked
uv build
Ruff format/check
Pyright strict
non-PostgreSQL suite
real-PostgreSQL suite on TEST_DATABASE_URL
```

Use PostgreSQL 16+ as provided by the external test target and report the exact server version.

With one shared `TEST_DATABASE_URL`, do not run PostgreSQL tests across xdist workers unless the external environment supplies isolated targets compatible with STACK-07.

No generic flaky retry or `sleep()` correctness orchestration.

## 30. Documentation / completion discipline

Do not mark `docs/milestones/M1/status.md` complete; the reviewer owns completion status.

Do not modify frozen normative architecture merely to match implementation. If a new contradiction is discovered, stop the affected behavior and report it.

No normative architecture change or migration is expected if implementation follows the corrected frozen baseline.

At completion report:

- implementation commit SHA;
- changed-file summary;
- exact quality/test results;
- PostgreSQL version;
- canonical PGTEST IDs/variants implemented and mechanism evidence;
- explicit confirmation that `REF-03` / Relationship `REF-05` remain deferred to S08 with Object.DELETE;
- confirmation of no migration/new gate/S08 behavior;
- any unverified requirement or newly discovered contradiction.
