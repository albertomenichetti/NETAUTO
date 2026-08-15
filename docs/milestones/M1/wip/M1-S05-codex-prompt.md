# Codex implementation prompt — M1-S05

**Status:** NON-NORMATIVE IMPLEMENTATION PROMPT.

This file is an execution aid for Codex. It does not override `AGENTS.md`, the frozen M1 contract/architecture/steps, or the ratified technology baseline.

## Assignment

Implement exactly:

```text
M1-S05 — Ownership and Object schema-change vertical slice
```

from `docs/milestones/M1/steps.md`.

M1-S00 through M1-S04 are complete. Do not implement M1-S06+ RelationshipDefinition/Relationship behavior and do not implement final `Object.DELETE`, which remains owned by M1-S08.

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

docs/milestones/M1/architecture/object.md
docs/milestones/M1/architecture/object-runtime-state.md
docs/milestones/M1/architecture/object-schema-change.md
docs/milestones/M1/architecture/object-ownership.md
docs/milestones/M1/architecture/object-lifecycle-changelog.md
docs/milestones/M1/architecture/objecttemplate-components.md
docs/milestones/M1/architecture/objecttemplate-properties.md
docs/milestones/M1/architecture/objecttemplate-effective-schema.md
docs/milestones/M1/architecture/objecttemplate-lifecycle.md
docs/milestones/M1/architecture/persistence-model.md
docs/milestones/M1/architecture/persistence-uow-concurrency.md
docs/milestones/M1/architecture/concurrency-semantic-matrix.md
docs/milestones/M1/architecture/concurrency-postgresql-realization-matrix.md
docs/milestones/M1/architecture/concurrency-postgresql-realization-object-ownership.md
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
M1-S00..S04      = COMPLETED
current step     = M1-S05
STACK-01..09     = RATIFIED
```

The 2026-08-15 ownership current-edge authority clarification in `m1-final-consistency-review.md` is part of the frozen baseline. Do not resurrect the stale DETACH wording that allowed a normal legacy edge absent from the parent current schema.

If normative authorities conflict, stop the affected behavior and report the contradiction rather than choosing an implementation interpretation.

## Objective

Deliver the complete S05 vertical capability:

```text
current ownership fact
-> ATTACH / DETACH
-> current SlotSemanticKey interpretation
-> single-owner + acyclic graph
-> structural lifecycle events
-> components / owner projections

plus

Object current intrinsic state
-> forward same-lineage SCHEMA_CHANGE
-> exact source/target schema closures
-> deterministic property migration
-> outgoing ownership preservation validation
-> atomic SCHEMA_CHANGE lifecycle event
```

At the end of S05, Objects can participate in strongly consistent component ownership and can migrate forward between exact versions of their stable ObjectTemplate lineage without losing current information, silently detaching children or leaving ownership edges that no longer have a meaning in the parent current schema.

## Hard scope boundary

S05 MUST NOT implement:

```text
final Object.DELETE
RelationshipDefinition CREATE/RENAME/DELETE
ObjectTemplate relationship-capabilities
runtime Relationship CREATE/DELETE/GET
Object relationship projections
Relationship lifecycle events
RelationshipDefinition conflict gate
Relationship exact-view arbitration
cross-lineage Object reclassification
schema downgrade / rollback
schema-change remediation payloads or scripts
implicit detach during schema change
atomic ownership MOVE primitive
ownership_edge_id
slot_declaring_template_id column in object_components
new persistence tables/columns or Alembic migration
JSON Schema compiler/projection
persistent effective-schema cache
ORM Session / AsyncSession
generic repository framework
generic command bus / DI container
background jobs / 202 semantics
Docker/Testcontainers/test-DB provisioning
```

Do not register fake S06+ or final Object.DELETE routes. `REF-02` / `REF-05` semantic variants are intentionally deferred to M1-S08 because final `Object.DELETE` is not delivered here. S05 may and should prove raw/current ownership FK `RESTRICT` mechanics at persistence level without inventing a private semantic DELETE operation.

## 1. Preserve the accepted S04 boundaries

Build on the accepted S04 implementation rather than creating parallel Object machinery.

Reuse/refactor narrowly as required:

```text
src/netauto/domain/objects.py
src/netauto/application/objects.py
src/netauto/application/objecttemplates.py
src/netauto/persistence/objects.py
src/netauto/persistence/objecttemplates.py
src/netauto/entrypoints/api/objects.py
```

Important existing seams:

- Object current state remains exactly `id, canonical_name, template_id, template_version, properties`;
- `resolve_exact_effective_schema(store, exact_otv)` resolves exact parent pins on the caller-owned connection and opens no nested UoW;
- PrimitiveType/DTV validation remains the S02 authority;
- Object non-delete current-state owner remains `FOR NO KEY UPDATE`;
- lifecycle event id/time remain PostgreSQL-generated;
- the S04 lifecycle public DTO is already a discriminated intrinsic family and must be extended, not replaced by a wide persistence-shaped record;
- `CoherentReadUnitOfWork` is available for composite multi-row reads where one consistent read snapshot is required.

Do not call an application service from inside another semantic mutation when doing so would open/commit an independent UoW.

## 2. Current ownership authority — newly clarified frozen rule

The physical current ownership fact remains exactly:

```text
object_components(
    child_object_id,
    parent_object_id,
    slot_name
)
```

with:

```text
PRIMARY KEY(child_object_id)
parent/child Object FK RESTRICT
no ownership_edge_id
no slot_declaring_template_id column
```

The runtime row is a **current fact**, not an historical pin to the declaration that existed when ATTACH occurred.

Semantic interpretation is always:

```text
parent current exact ObjectTemplateVersion
-> exact effective schema
-> component declaration with name = edge.slot_name
-> current SlotSemanticKey
   (declaring_template_id, slot_name)
```

This current parent schema is the sole semantic authority of the current edge.

Never:

- persist `slot_declaring_template_id` in `object_components`;
- search old ObjectTemplate versions for a "last known" slot;
- reconstruct current ownership semantics from lifecycle history;
- allow a supported "legacy edge" that no longer resolves in the parent current schema.

If a persisted current edge cannot be resolved to exactly one current effective slot of its parent, the dataset violates M1 invariants. Map that condition to `internal_error`, not `ownership_slot_unavailable`, `ownership_mismatch`, or a historical fallback.

## 3. Effective component resolution helpers

Introduce only the smallest pure/application helper(s) needed to interpret effective components on the caller-owned connection.

A useful semantic projection is a resolved slot containing at least:

```text
SlotSemanticKey:
    declaring_template_id
    name

target_template_id
```

Use the effective-schema declaration's `declaring_template_id`; do not infer it from the leaf ObjectTemplate lineage.

Current ownership projections and migration continuity use `(declaring_template_id, name)`, not `name` alone.

For reads/mutations encountering an impossible persisted exact schema or ambiguous/missing current slot for an existing edge, use internal invariant failure.

## 4. ATTACH semantics

Command:

```text
ATTACH(P, S, C)
```

Public path/body:

```text
POST /api/v1/core/objects/{parent_object_id}/attach

{
  "slot_name": "...",
  "child_object_id": "<uuid>"
}
```

Static wire shape is strict; unknown fields forbidden.

### Semantic admission

For a new edge require:

```text
parent P exists
child C exists
P != C
S exists in P current exact effective component schema
C.template_id == slot.target_template_id
    OR C.template_id is descendant of slot.target_template_id
C current ownership = detached
candidate P -> C does not create an ownership cycle
```

Do not consult defaults/latest versions. Parent interpretation uses its already-persisted exact current OTV, including when that OTV is DEPRECATED.

Child compatibility depends only on stable `child.template_id`; do not inspect child `template_version`, properties or Relationships for ATTACH compatibility.

### Failure boundary

Use the existing finite catalog:

- missing parent path target -> `404 resource_not_found`;
- missing child body operand -> `422 referenced_resource_not_found`;
- self-attachment / lineage incompatibility -> `422 semantic_validation_failed`;
- slot absent in the parent's current effective schema for a requested ATTACH -> `409 ownership_slot_unavailable`;
- child currently owned by a different parent/slot -> `409 ownership_conflict`;
- cycle candidate -> `409 ownership_cycle`;
- persisted impossible current schema/edge state -> `500 internal_error`.

No generic conflict code.

### Exact ATTACH idempotency

Current child ownership cases:

```text
detached
    -> real edge-add candidate

exact (P,S)
    -> success/no-op
    -> return the canonical component projection
    -> no gate
    -> no new lifecycle event

different (P',S')
    -> ownership_conflict
    -> no implicit MOVE
```

## 5. ATTACH concurrency and ownership graph gate

ATTACH follows the frozen ordering exactly:

```text
parent Object FOR NO KEY UPDATE
-> reload parent current state
-> resolve current parent exact schema / slot
-> observe child current Object metadata/type without taking a generic child owner lock
-> read current child ownership fact
-> exact-no-op / conflict fast exit if applicable
-> acquire OWNERSHIP_GRAPH_WRITE_GATE with pg_advisory_xact_lock
-> SEPARATE subsequent statement: fresh READ COMMITTED re-read of child ownership
-> SEPARATE subsequent statement(s): fresh authoritative graph/cycle read
-> INSERT edge
-> INSERT ATTACH_TO lifecycle event
-> COMMIT
```

Use the existing S01 constant:

```text
OWNERSHIP_GRAPH_WRITE_GATE = 0x4E45544100000001
```

Do not invent another gate/key/table.

### Gate rules

- gate acquisition is a standalone persistence statement;
- the authoritative protected read cannot be combined with gate acquisition into one SQL statement;
- after any gate wait, child ownership is re-read on a fresh statement snapshot;
- cycle traversal is performed after gate acquisition from the current committed `object_components` graph;
- candidate `P -> C` is valid iff P is not reachable from C;
- gate remains held until commit/rollback;
- only **real edge-add candidates** acquire the gate;
- no-op/conflicting/invalid ATTACH must not acquire it;
- DETACH never acquires it.

Use a recursive query/CTE inside persistence as appropriate. Do not add closure tables/materialized paths or application-process graph locks.

## 6. Single-owner authority

Final database authority is still:

```text
PRIMARY KEY(child_object_id)
```

on `object_components`.

Do not replace it with an absent-row `SELECT ... FOR UPDATE` or a child Object lock.

The global graph gate may mask same-child PK arbitration on the semantic ATTACH path, so retain/add a direct real-PostgreSQL persistence test proving the PK itself rejects two different current owner rows for the same child.

Translate expected semantic kernel outcomes without leaking constraint names publicly.

## 7. DETACH semantics

Command:

```text
DETACH(P,S,C)
```

Public route/body:

```text
POST /api/v1/core/objects/{parent_object_id}/detach

{
  "slot_name": "...",
  "child_object_id": "<uuid>"
}
```

Success is always `204 No Content` for both real removal and already-detached no-op.

### Current ownership decision table

After stabilizing the parent Object with `FOR NO KEY UPDATE`:

```text
child current fact = exact (P,S)
    -> resolve S in P current exact effective schema
    -> if resolvable: real delete + DETACH_FROM event
    -> if not resolvable: internal invariant failure

child current fact = detached
    -> idempotent 204 no-op
    -> no event

child current fact = different (P',S')
    -> ownership_mismatch
    -> never remove that other edge
```

DETACH does **not** perform ATTACH-style child compatibility validation and does not require that the slot would be admissible for a new ATTACH. Its schema resolution for an existing edge exists only to interpret the current fact/SlotSemanticKey and materialize the structural projection/event.

Never use old OTV versions or lifecycle rows as fallback slot identity authority.

DETACH:

- no graph traversal;
- no ownership graph gate;
- no implicit MOVE;
- no event on no-op.

## 8. Structural ownership lifecycle events

A real ATTACH emits exactly one:

```text
ATTACH_TO
```

A real DETACH emits exactly one:

```text
DETACH_FROM
```

Shape:

```text
id                        PostgreSQL generated
occurred_at               PostgreSQL transaction_timestamp()
kind                      ATTACH_TO | DETACH_FROM
object_id                 child
canonical_name            child historical display metadata
destination_object_id     parent
destination_canonical_name parent display metadata from stabilized parent row
slot_declaring_template_id current resolved declaring lineage
slot_name                 current resolved slot name
```

No `before`/`after` fields for ownership public DTOs and no relationship fields.

`slot_declaring_template_id + slot_name` is resolved from the current exact parent schema at transition time. It becomes historical event metadata after commit; it is not a persisted current-edge authority.

### Display metadata observation

- parent canonical name comes from the parent row already stabilized by `FOR NO KEY UPDATE`;
- child canonical name is a committed observation after parent stabilization;
- do not lock the child merely to freeze display metadata;
- concurrent child RENAME may yield old or new committed child name according to the observation point;
- edge + full event commit/rollback atomically.

Extend the S04 lifecycle semantic/persistence/read types so the read path can represent intrinsic **and ownership** event families. Do not add Relationship event public variants in S05.

The global and Object-specific lifecycle routes must now serialize ownership events using the frozen structural DTO. The Object-specific involving predicate already includes `destination_object_id`, so the parent must see its ATTACH/DETACH events.

## 9. Ownership public reads

Implement:

```text
GET /api/v1/core/objects/{parent_object_id}/components
GET /api/v1/core/objects/{child_object_id}/owner
```

### Components

Canonical projection item exactly:

```json
{
  "slot_declaring_template_id": "<uuid>",
  "slot_name": "interfaces",
  "child_object_id": "<uuid>"
}
```

Rules:

- path parent must exist or `404 resource_not_found`;
- ordering `child_object_id ASC`;
- optional exact `slot_name` filter;
- standard `{items,next_cursor}` envelope;
- opaque route/filter-specific keyset cursor; default limit 100, max 500;
- each current row's SlotSemanticKey is resolved against the parent current exact effective schema;
- an unresolvable current row is `internal_error`, never silently omitted.

### Owner

Canonical projection when owned:

```json
{
  "parent_object_id": "<uuid>",
  "slot_declaring_template_id": "<uuid>",
  "slot_name": "interfaces"
}
```

Existing detached Object:

```text
HTTP 200
body = null
```

Missing child path Object -> `404 resource_not_found`.

If an ownership row exists, load the parent current exact schema and resolve the row's current SlotSemanticKey. Missing parent/impossible slot state is internal invariant failure.

### Read consistency

These are multi-row/composite current projections. Do not expose a mixed generation of parent intrinsic schema pin + ownership rows + effective slot interpretation under concurrent SCHEMA_CHANGE/ATTACH/DETACH.

Use either one coherent SQL statement or the existing `CoherentReadUnitOfWork` (`REPEATABLE READ READ ONLY`) for a request-level coherent snapshot. Mutation isolation remains READ COMMITTED.

## 10. SCHEMA_CHANGE command and target admission

Public command:

```text
POST /api/v1/core/objects/{object_id}/schema-change

{"target_version": N}
```

Body contains exactly mandatory positive `target_version`. No remediation/override/detach/cross-lineage fields.

Transaction order:

```text
Object row FOR NO KEY UPDATE
-> reload complete current Object state
-> derive SourceClosure from current exact persisted pin
-> validate target_version > current_version
-> admit exact target OTV FOR SHARE on same stable template_id
-> fresh target PUBLISHED recheck
-> derive TargetClosure from exact pins
-> migrate properties
-> validate current outgoing attachments against target closure
-> validate complete target canonical Object state
-> update template_version + properties atomically
-> insert one SCHEMA_CHANGE event
-> commit
```

The source OTV may be PUBLISHED or DEPRECATED and is not a new admission. The target is a new binding and must remain PUBLISHED until Object commit.

Do not consult ObjectTemplate/DataType defaults during migration.

Missing target exact OTV is a referenced command operand failure (`422 referenced_resource_not_found`). Existing but non-PUBLISHED target -> `409 dependency_not_admissible`. Non-forward target -> `422 semantic_validation_failed`.

## 11. SCHEMA_CHANGE property migration

Migration identity is:

```text
PropertySemanticKey = (declaring_template_id, name)
```

Do not carry values by runtime JSON name alone.

For every target effective property:

### Matching source semantic key with a value present

Allowed shape transitions:

```text
SCALAR -> SCALAR    preserve scalar
LIST   -> LIST      preserve ordered list
SCALAR -> LIST      wrap source value as singleton list
```

Validate/canonicalize the resulting value against the **target exact DTV**.

If an existing source value is incompatible with the target declaration/constraint:

```text
SCHEMA_CHANGE fails
-> 409 schema_change_blocked
```

Never replace an existing incompatible value with `migration_default`.

`LIST -> SCALAR` is not a supported normal evolution.

### Matching source semantic key with no value present

```text
target optional -> absent
target required -> use target migration_default
```

### Target semantic key new relative to source

```text
target optional -> absent
target required -> use target migration_default
```

### Source-only key

Drop it from target runtime state. Historical before snapshot preserves the old value.

### Same effective name / different semantic key

Treat source as removed and target as new. Name equality alone does not carry a value.

`migration_default` is only absence fill for a required target property. Reuse the exact PrimitiveType/DTV canonical validation path; persisted/certified target declaration corruption is internal failure, not caller `schema_change_blocked`.

Return a complete canonical Object candidate; no partial JSONB mutation.

## 12. SCHEMA_CHANGE ownership preservation

While the migrating Object is stabilized as the parent concurrency owner, read its complete current outgoing ownership set.

For every outgoing current row:

1. resolve `slot_name` in the **source** exact effective schema to a source `SlotSemanticKey`;
2. if it cannot resolve, current persisted state is already corrupt -> `internal_error`;
3. find the same `SlotSemanticKey` in the target effective schema;
4. if absent -> `409 schema_change_blocked`;
5. if present, verify the child current stable `template_id` is equal to or descendant of target slot `target_template_id`;
6. if incompatible -> `409 schema_change_blocked`.

No implicit detach, rebind or remediation.

A successful SCHEMA_CHANGE therefore guarantees every retained `object_components` row remains semantically interpretable against the new current exact parent schema. There is no supported legacy edge state after migration.

Incoming ownership does not require revalidation because the migrating Object's stable `template_id` does not change.

Relationships are not implemented here and normal same-lineage schema change would not change endpoint lineage compatibility anyway.

### `schema_change_blocked` details

Use bounded semantic details, for example one sufficient blocker:

```json
{
  "object_id": "<uuid>",
  "target_version": 8,
  "blocker_type": "attachment",
  "member_name": "interfaces",
  "child_object_id": "<uuid>"
}
```

For property blockers use the same finite code with bounded property/member context; do not dump all blockers or SQL details.

## 13. SCHEMA_CHANGE lifecycle event

A successful migration produces exactly one intrinsic:

```text
SCHEMA_CHANGE
```

with:

```text
before = complete canonical source Object snapshot
after  = complete canonical target Object snapshot
```

`template_id` unchanged; `template_version` increases. Do not emit separate DATA_CHANGE events for deterministic carry/default work performed inside migration.

Current Object update + event insert are one UoW and must rollback together.

S04 already exposes the SCHEMA_CHANGE intrinsic response variant; S05 now starts producing it.

## 14. API surface delivered in S05

Add exactly:

```text
POST /api/v1/core/objects/{object_id}/schema-change
POST /api/v1/core/objects/{parent_object_id}/attach
POST /api/v1/core/objects/{parent_object_id}/detach
GET  /api/v1/core/objects/{parent_object_id}/components
GET  /api/v1/core/objects/{child_object_id}/owner
```

Extend lifecycle list response union with ownership structural variants.

Do NOT add:

```text
DELETE /objects/{object_id}
/objects/{object_id}/relationships
RelationshipDefinition routes
Relationship routes
ObjectTemplate relationship-capabilities
```

Success mapping:

```text
SCHEMA_CHANGE -> 200 + Object DTO
ATTACH real/new or exact-idempotent -> 200 + component projection item
DETACH real/no-op -> 204 no body
components -> 200 page
owner owned -> 200 projection
owner detached -> 200 null
```

Keep strict query/body handling and existing canonical error adapter.

## 15. Deterministic real-PostgreSQL concurrency verification

Use external `TEST_DATABASE_URL`, independent UoWs/connections, deterministic cuts/blockers and `pg_blocking_pids()` for expected blocker relations. No `sleep()` orchestration. Narrow test-only interception around real persistence phases is allowed only where necessary; no production debug hooks.

Implement all S05-realizable canonical scenarios and mechanism regressions below.

### ROW-12 — Object schema/current-state races

A. `DATA_CHANGE × SCHEMA_CHANGE`, same Object:

- same Object `FOR NO KEY UPDATE` owner;
- waiter re-reads complete state after wake-up;
- migration/data candidate derives from winner's committed state;
- no lost value or stale source migration;
- lifecycle snapshots form a serially explainable sequence.

B. `SCHEMA_CHANGE × SCHEMA_CHANGE`, same Object:

- same owner serialization;
- waiter re-evaluates current source version after wake-up;
- no stale migration candidate can overwrite winner;
- only serially valid success/failure combinations.

Also prove target exact OTV `FOR SHARE` admission remains live through schema-change commit against concurrent target OTV DEPRECATE. A waiter must not commit a new Object binding to a target that was already non-PUBLISHED before its admission/commit.

### ROW-13 — ATTACH × SCHEMA_CHANGE(parent)

Use a target version that removes/changes the relevant slot so ordering is observable:

```text
ATTACH first
    -> schema change observes edge and blocks if target cannot preserve it

SCHEMA_CHANGE first
    -> ATTACH validates against new current schema and fails if slot unavailable
```

Prove both rendezvous on parent Object `FOR NO KEY UPDATE` and no invalid edge/current-schema state commits.

### ROW-14 — DETACH × SCHEMA_CHANGE(parent)

Use an existing edge that blocks migration because target removes the slot.

```text
DETACH first
    -> edge removal commits
    -> schema change may then succeed

SCHEMA_CHANGE first while edge current
    -> migration cannot commit target without preserving edge
```

DETACH takes no graph gate.

### ARB-02 — different ATTACH, same child

- kernel semantic behavior: at most one distinct current owner;
- direct raw persistence test proves `PRIMARY KEY(child_object_id)` is the final single-owner authority independent of the graph gate.

### ARB-03 — identical ownership mutation

A. identical ATTACH:

- exactly one real edge creation + ATTACH_TO event;
- other converges success/no-op with no duplicate event.

B. identical DETACH:

- exactly one real removal + DETACH_FROM event;
- other converges `204` no-op, no duplicate event.

### ARB-04 — ATTACH × DETACH exact fact

Only serially explainable fact/event sequences. DETACH must never remove a different owner/slot fact.

### GATE-01 — opposite edge-add

`A -> B` × `B -> A`:

- at most one can commit;
- committed graph remains acyclic;
- prove actual global advisory-gate serialization.

### GATE-02 — nontrivial graph

A. longer cycle candidate must be rejected.

B. cycle check concurrent with DETACH removing a path:

- safe success after visible removal or conservative cycle rejection are allowed;
- never a committed cycle.

### GATE-03 — fresh post-gate visibility

A. waiter on `OWNERSHIP_GRAPH_WRITE_GATE` must observe the previous holder's committed edge in a **statement after gate acquisition**. Design the test so it would fail if gate acquisition and protected read were collapsed into one stale-snapshot SQL statement.

B. child ownership changes while ATTACH waits for the gate; waiter must re-read child ownership after gate acquisition and react to the committed fact.

Add mechanism evidence that:

- gate is acquired only by real edge-add candidates;
- no-op/conflict ATTACH does not take gate;
- DETACH does not take gate;
- rollback releases gate and rolled-back edge is invisible;
- parent owner is acquired before graph gate;
- gate is transaction-level, not session-level.

### SNAP-04 — ownership structural event display metadata

Concurrent child RENAME with real ATTACH and/or DETACH:

- do not lock child solely for display metadata;
- event may capture old or new **committed** child canonical name according to observation point;
- parent name comes from stabilized parent state;
- event SlotSemanticKey remains the current resolved slot identity.

### ATOMIC-04B — ownership edge/event atomicity

Force a narrow test-only failure after real edge DML and before/while structural lifecycle insert. Prove edge + event rollback all-or-nothing. Cover at least one real add/remove shape; stronger coverage may exercise both.

### PAR-03 — intentional parent over-serialization

`OBJ.RENAME(parent) × ATTACH(parent)` must contend because both use the shared parent Object non-key owner. Prove the intended blocker relation.

### PAR-04 — global ownership-gate over-serialization

Two unrelated real ATTACH operations on disjoint graph regions still serialize on `OWNERSHIP_GRAPH_WRITE_GATE`. Prove the gate blocker relation.

### REF boundary for S05

Do **not** claim canonical semantic `REF-02` / `REF-05` complete here: they require final `Object.DELETE` and belong to S08 under updated frozen `steps.md`.

S05 must still prove:

- parent and child ownership FK are immediate `RESTRICT` current-reference authorities;
- no CASCADE cleanup;
- direct FK/PK rollback mechanics on real PostgreSQL.

## 16. Required domain/application/persistence tests

### Ownership domain/application

Cover at minimum:

- exact slot resolution including inherited declaring lineage;
- compatible child same lineage and descendant lineage;
- incompatible child rejection;
- self-attach rejection;
- exact attach idempotency;
- different-owner/slot conflict;
- detached DETACH no-op;
- exact DETACH removal;
- wrong-owner/slot DETACH mismatch;
- DETACH does not do child compatibility admission;
- unresolvable persisted current edge -> internal failure;
- cycle detection and longer path cycles;
- no implicit MOVE.

### SCHEMA_CHANGE pure/application semantics

Cover at minimum:

- same-lineage forward-only target;
- source PUBLISHED and source DEPRECATED;
- target exact PUBLISHED admission;
- source-to-target direct migration skipping intermediate versions;
- property continuity by `PropertySemanticKey`;
- SCALAR->SCALAR, LIST->LIST, SCALAR->LIST singleton carry;
- target DTV canonical/constraint revalidation;
- incompatible existing value blocks; migration_default never replaces it;
- required missing/new target property receives target migration_default;
- optional missing/new target property stays absent;
- source-only property is removed;
- same effective name/different declaring lineage does not carry;
- no implicit defaults/latest lookup during migration;
- complete target state canonicalization;
- outgoing slot continuity by `SlotSemanticKey`;
- slot removed -> migration blocked while edge exists;
- target-compatible widened slot preserves edge;
- child incompatibility under target slot blocks migration;
- incoming ownership does not block/revalidate;
- no implicit detach/remediation/downgrade.

### Persistence/lifecycle

Cover:

- `object_components` round trip contains only child/parent/slot_name;
- no `slot_declaring_template_id` current-edge persistence;
- raw PK single-owner authority;
- parent/child FK RESTRICT and rollback;
- recursive cycle query correctness;
- transaction-level advisory gate acquisition/release;
- ATTACH_TO/DETACH_FROM typed row shape;
- structural event PostgreSQL id/time defaults;
- no-op ownership produces no event;
- SCHEMA_CHANGE current Object + event atomicity;
- DB-valid but semantically corrupt edge/current-schema state maps internal on DETACH/components/owner rather than historical fallback.

## 17. API verification

Exercise every S05 route and all relevant failure families:

```text
POST /objects/{id}/schema-change
POST /objects/{id}/attach
POST /objects/{id}/detach
GET  /objects/{id}/components
GET  /objects/{id}/owner
GET  /lifecycle-events
GET  /objects/{id}/lifecycle-events
```

Verify:

- strict request/query shape and unknown fields;
- exact success statuses/bodies (`200`, `204`, owner `200 null`);
- missing path Object vs missing child operand boundary;
- `ownership_slot_unavailable`, `ownership_conflict`, `ownership_mismatch`, `ownership_cycle`, `schema_change_blocked` mappings;
- internal invariant corruption does not leak SQL/table/constraint details;
- components ordering/filter/keyset cursor and summary/projection exact shape;
- owner current projection exact shape;
- structural lifecycle DTO has no meaningless `before`/`after` fields;
- global lifecycle response union now includes intrinsic + ownership families only;
- ATTACH/DETACH events appear on both child and parent Object-specific lifecycle timelines because parent is `destination_object_id`;
- no S06+ or final Object.DELETE route appears as a successful capability.

## 18. Scope and architecture regression checks

Keep/add cheap regressions proving:

- domain/application Object modules do not import FastAPI/Pydantic/SQLAlchemy;
- application layer does not construct SQLAlchemy statements;
- no `state_revision` / ownership_edge_id / slot-declaring current-edge column is introduced;
- no migration added;
- exactly the S05 routes are added;
- no Relationship/Definition route or Object DELETE is introduced;
- lifecycle OpenAPI union includes intrinsic and ownership event variants, but no Relationship structural variants yet;
- persistence metadata still matches the frozen 13-table authority.

## 19. Quality gates

Run and report at minimum:

```text
uv lock --check or the repository's canonical lock validation
uv sync --locked
uv build
Ruff format/check
Pyright strict
non-PostgreSQL suite
real-PostgreSQL suite on TEST_DATABASE_URL
```

PostgreSQL-required tests must use the externally supplied dedicated target. Do not provision Docker/Testcontainers and do not fall back to SQLite/another backend.

With one shared `TEST_DATABASE_URL`, do not use cross-worker PostgreSQL xdist execution that violates the database-isolation contract.

No generic retries or `sleep()`-based correctness orchestration.

## 20. Documentation / completion discipline

Do not mark `docs/milestones/M1/status.md` complete. The reviewer owns completion status.

Do not modify frozen normative architecture merely to match implementation. If a new contradiction is discovered, stop the affected implementation and report it.

No normative documentation change is expected if implementation follows the clarified and re-frozen baseline.

At completion report:

- implementation commit SHA;
- changed file summary;
- exact quality/test results;
- PostgreSQL version;
- canonical PGTEST scenarios implemented with semantic + mechanism evidence;
- confirmation that no migration/S06+/Object.DELETE behavior was introduced;
- any unverified requirement or newly discovered contradiction.
