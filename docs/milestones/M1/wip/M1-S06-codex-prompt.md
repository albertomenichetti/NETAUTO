# Codex implementation prompt — M1-S06

**Status:** NON-NORMATIVE IMPLEMENTATION PROMPT.

This file is an execution aid for Codex. It does not override `AGENTS.md`, the frozen M1 contract/architecture/steps, or the ratified technology baseline.

## Assignment

Implement exactly:

```text
M1-S06 — RelationshipDefinition model-plane and capability vertical slice
```

from `docs/milestones/M1/steps.md`.

M1-S00 through M1-S05 are complete. Do not implement M1-S07 runtime Relationship behavior, Relationship lifecycle events, Object relationship projections, or final M1-S08 destructive-operation closure.

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
docs/milestones/M1/architecture/relationship-concurrency.md
docs/milestones/M1/architecture/relationship-consistency-review.md
docs/milestones/M1/architecture/objecttemplate.md
docs/milestones/M1/architecture/objecttemplate-lifecycle.md
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
M1-S00..S05      = COMPLETED
current step     = M1-S06
STACK-01..09     = RATIFIED
```

If normative authorities conflict, stop the affected behavior and report the contradiction instead of choosing an implementation interpretation.

## Objective

Deliver the complete certified Relationship model-plane vertical capability:

```text
RelationshipDefinition candidate
-> deterministic complete RelationshipResolution set
-> aggregate shape validation
-> endpoint lineage references
-> global semantic-equivalence / Resolution-conflict certification
-> atomic CREATE / RENAME / DELETE
-> RelationshipDefinition GET/list
-> ObjectTemplate relationship-capabilities projection/list
-> deterministic real-PostgreSQL gate/lifetime verification
```

At the end of S06 the committed Definition set must be globally conflict-free and immediately consumable by the future S07 runtime Relationship slice without any model reinterpretation.

## Hard scope boundary

S06 MUST NOT implement:

```text
runtime Relationship CREATE / DELETE / GET
RuntimeRelationshipResolution application behavior
Object /relationships projection
Relationship lifecycle event production or public Relationship event DTOs
Relationship factual convergence / ABA
Relationship exact-view arbitration
Object DELETE
RelationshipDefinition versioning
Relationship typed properties
source/target or forward/reverse semantics
public RelationshipResolution CRUD/read resource
new persistence tables/columns or Alembic migration
new advisory gate/key
ancestry closure/materialized path authority
JSON Schema
ORM Session / AsyncSession
generic repository framework
generic command bus / DI container
background jobs / 202 semantics
Docker/Testcontainers/test-DB provisioning
```

The physical S01 Relationship tables already exist. S06 uses `relationship_definitions` and `relationship_resolutions`; the `relationships` table is consulted only for Definition DELETE safety. Do not expose or implement S07 semantic runtime operations merely because their physical tables already exist.

## 1. Domain model — plain Python only

Add the smallest plain-Python Relationship model needed for S06, preserving the existing layer rules.

Conceptual aggregate:

```text
RelationshipDefinition
    id: UUID
    symmetric: bool
    resolutions: complete tuple[RelationshipResolution, ...]

RelationshipResolution
    id: UUID
    relationship_definition_id: UUID
    from_template_id: UUID
    to_template_id: UUID
    name: str
```

Rules:

- Definition and Resolution IDs are kernel-generated UUIDv4;
- IDs, symmetry, Resolution membership and Resolution endpoints are immutable;
- only Resolution names are mutable via Definition RENAME;
- name grammar is `[a-z][a-z0-9_]{0,63}` with no normalization;
- no source/target, forward/reverse or standalone Resolution lifecycle exists.

Domain modules must not import FastAPI, Pydantic or SQLAlchemy and must perform no I/O.

## 2. Deterministic aggregate derivation

### Non-symmetric CREATE

Public semantic input is an unordered pair of perspectives:

```text
symmetric = false
perspectives = exactly two {template_id, name}
```

Names are distinct. For perspectives `(A,name_a)` and `(B,name_b)`, derive exactly:

```text
A -> B / name_a
B -> A / name_b
```

If `A == B`, both Resolution rows have the same from/to lineage pair but distinct names.

Input array order is not semantic authority. Reversing the two perspectives yields the same complete semantic Resolution set/signature.

### Symmetric CREATE

Input:

```text
symmetric = true
endpoint_template_ids = exactly two unordered lineage UUIDs
name = one semantic name
```

If endpoints are equal:

```text
T == T
-> exactly one Resolution T -> T / name
```

If endpoints differ:

```text
A != B
-> exactly two reciprocal Resolutions
   A -> B / name
   B -> A / name
```

Endpoint input order is not semantic authority.

Generate IDs only for the complete candidate being attempted. UUID values never participate in semantic equivalence.

## 3. Aggregate validation and semantic signatures

Validate every loaded/candidate Definition as a complete aggregate.

Frozen shape:

```text
non-symmetric
    -> exactly 2 reciprocal Resolutions
    -> distinct names

symmetric same-template
    -> exactly 1 Resolution

symmetric different-template
    -> exactly 2 reciprocal Resolutions
    -> identical name
```

Definition semantic signature is:

```text
(
    symmetric,
    unordered complete set of
        (from_template_id, to_template_id, name)
)
```

Definition/Resolution UUIDs and array order do not participate.

Persisted aggregates that violate the frozen shape are internal invariant corruption on reads/certification; do not reinterpret malformed child state into a caller validation failure.

## 4. Endpoint lineage semantics

Resolution endpoints reference stable ObjectTemplate lineage, never exact OTV.

Valid referenced lineage may be:

```text
abstract
without default_version
without any current PUBLISHED OTV
```

Do not resolve or admit an exact OTV and do not consult ObjectTemplate defaults/latest versions.

These are **pure stable-lineage reference-lifetime dependencies**. Preserve the frozen minimal mechanism:

- ordinary existence/ancestry reads for semantic validation;
- immediate PostgreSQL FK `RESTRICT` as final lifetime race authority;
- no generic explicit `FOR SHARE` lifecycle lock on endpoint ObjectTemplate lineage merely to create a Resolution reference.

A Definition CREATE that loses an endpoint-lineage delete race must translate the known FK/reference failure to `422 referenced_resource_not_found` without exposing constraint names.

## 5. Lineage-space overlap

With the frozen single stable ObjectTemplate inheritance graph, spaces `A` and `B` overlap iff:

```text
A == B
OR A descendant-of B
OR B descendant-of A
```

Parent lineage is immutable in normal M1 operation. Do not introduce an ancestry closure table/cache authority.

Reuse the existing ObjectTemplate persistence ancestry seam or add only the smallest concrete Relationship-specific query/helper needed. Persisted ancestry corruption/missing internal dependency where a committed certified Definition should be valid is `internal_error`.

For CREATE candidate endpoints that disappeared as command operands, use `referenced_resource_not_found` rather than internal corruption.

## 6. Cross-Definition conflict rule

Two Resolutions belonging to **different** Definitions conflict iff all are true:

```text
same name
AND from-template spaces overlap
AND to-template spaces overlap
```

Resolutions of the same Definition are never conflict-checked against each other; intentional overlap inside one aggregate is allowed and will be handled by S07 runtime closure semantics.

Semantic equivalence and conflict are distinct checks. Check equivalence first so an exact duplicate Definition maps to:

```text
409 relationship_definition_equivalent
```

A non-equivalent candidate with at least one cross-Definition conflicting Resolution maps to:

```text
409 relationship_definition_conflict
```

Use bounded semantic details only, for example the existing conflicting/equivalent Definition ID and relevant name where useful. Do not expose raw table/constraint data or unbounded conflict dumps.

## 7. Certified-set authority and conflict gate

The authority is the current committed certified set:

```text
RelationshipDefinition headers
+
complete authoritative RelationshipResolution child sets
```

Use the existing frozen gate:

```text
AdvisoryGate.RELATIONSHIP_DEFINITION_CONFLICT_GATE
= 0x4E45544100000002
```

via transaction-level `pg_advisory_xact_lock`.

Do not invent another gate.

### Mandatory gate rule

For both CREATE and RENAME:

```text
statement 1
    acquire RELATIONSHIP_DEFINITION_CONFLICT_GATE

statement 2+
    authoritative certified-set read on a fresh READ COMMITTED statement snapshot
```

Gate acquisition and the protected read MUST NOT be collapsed into one SQL statement. The gate stays held until commit/rollback.

### Coherent certified-set read

Because `RD.DELETE` intentionally does **not** take the conflict gate, do not assemble a protected certified set from header/Resolution reads that can mix statement snapshots while a DELETE cascades its child rows.

Prefer one persistence statement that returns the complete current Definition+Resolution certified set for conflict analysis. An equivalent concrete representation is acceptable only if it guarantees one coherent committed snapshot for every aggregate in the set at this read boundary.

A single statement may observe a concurrently deleting Definition either entirely before or entirely after its delete; it must not manufacture a half-aggregate generation.

Validate the persisted aggregate shapes after decoding. Corrupt committed certified state is internal failure.

## 8. RelationshipDefinition CREATE UoW

Conceptual transaction:

```text
strict transport / local candidate shape
-> construct complete candidate with kernel UUIDs
-> validate candidate local aggregate semantics
-> acquire RD conflict gate
-> fresh coherent certified-set read (separate statement)
-> resolve/revalidate candidate endpoint lineage existence + ancestry facts as needed
-> semantic-equivalence check
-> global Resolution conflict check
-> INSERT Definition header
-> INSERT complete Resolution child set
-> COMMIT while gate remains held
```

No partial Definition or Resolution set may commit.

Endpoint FK insertion remains final reference-lifetime authority against concurrent ObjectTemplate whole-lineage delete.

Success:

```text
201 Created
Location: /api/v1/core/relationship-definitions/{id}
body: complete RelationshipDefinition aggregate DTO
```

## 9. RelationshipDefinition RENAME UoW

Public RENAME changes only names.

Start with the exact Definition owner:

```text
relationship_definitions(D) FOR NO KEY UPDATE
```

Then load/re-read the complete own aggregate. Same-Definition RENAME writers and RENAME×DELETE must rendezvous on this header owner.

### Non-symmetric body

```text
{
  "resolutions": [
    {"resolution_id": "...", "name": "..."},
    {"resolution_id": "...", "name": "..."}
  ]
}
```

Rules:

- exactly 2 entries;
- duplicate resolution IDs malformed transport input;
- supplied IDs must cover exactly the current Definition Resolution set;
- names valid and distinct;
- no endpoint/symmetry/membership mutation.

A supplied ID set not equal to the target Definition's own complete Resolution set is semantic validation failure; RelationshipResolution is not a standalone public resource whose cross-aggregate existence should be exposed here.

### Symmetric body

```text
{"name": "..."}
```

Apply the same name to the Definition's one or two current Resolution rows.

The two RENAME transport shapes are both valid request forms. A well-formed shape that does not match the target Definition's current `symmetric` value is `422 semantic_validation_failed`, not a transport schema rewrite of current state.

### Rename conflict transaction

```text
Definition D FOR NO KEY UPDATE
-> load/validate own complete aggregate
-> build complete renamed candidate with same stable IDs/endpoints
-> acquire RD conflict gate
-> fresh coherent certified-set read (separate statement)
-> exclude D itself from equivalence/cross-Definition conflict checks
-> validate candidate against all other committed Definitions
-> update complete relevant Resolution-name set atomically
-> COMMIT while gate remains held
```

Prefer a concrete persistence operation that updates the complete name set in one statement where straightforward; transaction-level atomicity remains mandatory either way.

Success:

```text
200 OK
complete resulting RelationshipDefinition aggregate DTO
```

Do not emit Object lifecycle events for Definition RENAME.

## 10. RelationshipDefinition DELETE UoW

DELETE does not introduce Resolution conflict and therefore MUST NOT acquire `RELATIONSHIP_DEFINITION_CONFLICT_GATE`.

Transaction:

```text
relationship_definitions(D) FOR UPDATE
-> absent path target => 404 resource_not_found
-> determine current factual Relationship reference count
-> if any current factual Relationship references D:
       409 delete_blocked
-> DELETE Definition header
   -> CASCADE complete owned Resolution set
-> COMMIT
```

No runtime Relationship is deleted implicitly.

Historical lifecycle rows do not block Definition delete.

Use `relationships.relationship_definition_id` as the current factual blocker authority even though S07 does not yet expose semantic Relationship CREATE. S07 will add factual-reference semantic regression coverage; S06 must already implement the final delete rule against the physical authority.

A concurrent factual reference insertion race remains finally arbitrated by immediate FK `RESTRICT`; translate the known delete-side FK loss to `delete_blocked` rather than leaking SQL.

Successful delete: `204 No Content`.

Absent Definition path target is NOT idempotent and remains `404 resource_not_found`.

## 11. Persistence layer

Use the existing S01 tables unchanged:

```text
relationship_definitions(id, symmetric)
relationship_resolutions(
    id,
    relationship_definition_id,
    from_template_id,
    to_template_id,
    name
)
```

No migration.

Preserve:

- Definition PK UUID;
- Resolution PK UUID;
- Definition -> Resolution `CASCADE`;
- endpoint ObjectTemplate lineage FK `RESTRICT`;
- defensive semantic-child UNIQUE;
- technical `(id, relationship_definition_id)` UNIQUE;
- existing PERSIST-15 indices.

Add only concrete helpers needed for S06, such as:

```text
insert complete Definition aggregate
load exact complete aggregate
lock Definition NO KEY / UPDATE
coherent certified-set read
update complete Resolution names
current factual Relationship blocker count
delete Definition
list Definition headers/aggregates
list applicable relationship capabilities
```

No generic repository base.

Known expected integrity/race failures may be translated only at the bounded persistence boundary; unexpected IntegrityError is internal failure.

## 12. Read consistency

### Definition GET

`GET /api/v1/core/relationship-definitions/{id}` returns one complete aggregate snapshot:

```json
{
  "id": "<uuid>",
  "symmetric": false,
  "resolutions": [
    {
      "resolution_id": "<uuid>",
      "name": "hosts",
      "from_template_id": "<uuid>",
      "to_template_id": "<uuid>"
    }
  ]
}
```

No nested `relationship_definition_id` field. No forward/reverse role/order field.

Use one coherent SQL statement or the existing `CoherentReadUnitOfWork` for multi-row aggregate reads. Persisted malformed aggregate => `500 internal_error`.

Nested Resolution order has no semantic role. Return it deterministically (for example by `resolution_id`) without exposing direction/orientation semantics.

### Definition collection

```text
GET /api/v1/core/relationship-definitions
```

Rules:

- `{items,next_cursor}` envelope;
- fixed `id ASC` keyset ordering;
- each list item is the complete bounded aggregate DTO;
- no baseline filters beyond `cursor` / `limit`;
- default limit 100, max 500;
- cursor route-specific; limit excluded from query identity.

Use one coherent read snapshot for each page's headers + complete child sets.

## 13. ObjectTemplate relationship-capabilities

Implement the previously deferred route:

```text
GET /api/v1/core/object-templates/{template_id}/relationship-capabilities
```

A Resolution is applicable to route lineage `T` iff:

```text
T == resolution.from_template_id
OR T descendant-of resolution.from_template_id
```

Capability item exactly:

```json
{
  "resolution_id": "<uuid>",
  "relationship_definition_id": "<uuid>",
  "name": "hosts",
  "from_template_id": "<uuid>",
  "to_template_id": "<uuid>"
}
```

Rules:

- route ObjectTemplate lineage must exist or `404 resource_not_found`;
- applicability depends only on stable lineage ancestry, not exact OTV/default/PUBLISHED state;
- abstract route lineage is valid;
- ordering `resolution_id ASC`;
- optional exact `name` filter;
- standard `{items,next_cursor}` envelope;
- default limit 100, max 500;
- cursor identity must include the path `template_id` and active `name` filter; limit excluded;
- no Resolution standalone API is introduced.

If a concrete ancestry query/join can produce the same Resolution through more than one traversal row, de-duplicate by `resolution_id` only. Do **not** collapse two distinct applicable Resolution IDs merely because they share Definition/name or overlap through inheritance; the frozen capability primitive is "all applicable RelationshipResolution".

Use a coherent request snapshot (single statement or existing coherent-read UoW) so Resolution names/membership and ancestry interpretation do not mix committed generations during concurrent Definition rename/delete.

## 14. Public API surface delivered in S06

Add exactly:

```text
POST   /api/v1/core/relationship-definitions
POST   /api/v1/core/relationship-definitions/{relationship_definition_id}/rename
DELETE /api/v1/core/relationship-definitions/{relationship_definition_id}
GET    /api/v1/core/relationship-definitions
GET    /api/v1/core/relationship-definitions/{relationship_definition_id}
GET    /api/v1/core/object-templates/{template_id}/relationship-capabilities
```

Do NOT add successful S07 runtime routes:

```text
POST   /api/v1/core/relationships
DELETE /api/v1/core/relationships/{relationship_id}
GET    /api/v1/core/relationships/{relationship_id}
GET    /api/v1/core/objects/{object_id}/relationships
```

Do not extend lifecycle response DTOs with Relationship event kinds in S06. The persistence EventKind/filter vocabulary may already know those frozen values, but public Relationship lifecycle response variants belong to S07 when the producer exists.

## 15. Strict transport DTOs

### CREATE union

Non-symmetric branch:

```json
{
  "symmetric": false,
  "perspectives": [
    {"template_id": "<uuid>", "name": "..."},
    {"template_id": "<uuid>", "name": "..."}
  ]
}
```

Exactly two perspectives; names distinct; extra fields forbidden. Perspective order has no semantic meaning.

Symmetric branch:

```json
{
  "symmetric": true,
  "endpoint_template_ids": ["<uuid>", "<uuid>"],
  "name": "..."
}
```

Exactly two endpoint IDs; equal IDs allowed; extra fields forbidden. Endpoint order has no semantic meaning.

Use the required `symmetric` boolean as the Pydantic discriminator. Generic scalar coercion remains forbidden.

### RENAME union

Non-symmetric branch:

```json
{
  "resolutions": [
    {"resolution_id": "<uuid>", "name": "..."},
    {"resolution_id": "<uuid>", "name": "..."}
  ]
}
```

Exactly two; duplicate resolution IDs invalid request; extra fields forbidden.

Symmetric branch:

```json
{"name": "..."}
```

The body deliberately does not resend `symmetric`. Route target state determines whether the chosen well-formed body shape is semantically applicable.

### DELETE

No body, no cascade/force option.

## 16. Failure mapping

Preserve the finite API-03.11 catalog.

At minimum:

```text
missing Definition path target
    -> 404 resource_not_found

missing endpoint ObjectTemplate command operand
    -> 422 referenced_resource_not_found

invalid aggregate/name/body semantic candidate
    -> 422 semantic_validation_failed
    (pure malformed DTO shape remains 400 invalid_request)

well-formed RENAME body shape incompatible with current symmetry
    -> 422 semantic_validation_failed

non-symmetric supplied Resolution set != target aggregate's complete set
    -> 422 semantic_validation_failed

equivalent Definition candidate
    -> 409 relationship_definition_equivalent

cross-Definition Resolution conflict
    -> 409 relationship_definition_conflict

Definition DELETE blocked by factual Relationship
    -> 409 delete_blocked

persisted malformed certified/read aggregate or impossible ancestry state
    -> 500 internal_error
```

No generic `conflict` code and no SQL/constraint leakage.

## 17. Deterministic real-PostgreSQL verification

Use external `TEST_DATABASE_URL`, truly independent UoWs/connections, deterministic barriers/cuts and `pg_blocking_pids()` for expected blocking. No `sleep()` correctness orchestration, generic retry loops or production debug hooks.

Implement all S06-realizable canonical scenarios plus the required REALIZE-12 regressions.

### ROW-17 — RD.RENAME × RD.DELETE same Definition

Prove same header lifetime serialization:

```text
RENAME owner = FOR NO KEY UPDATE
DELETE owner = FOR UPDATE
```

Exercise serially valid outcomes and verify no partial renamed/deleted aggregate.

### REF-01 — RD.CREATE -> ObjectTemplate stable lineage

Exercise both directions of Definition reference creation vs endpoint ObjectTemplate `DELETE_LINEAGE`:

```text
CREATE/reference first
    -> lineage delete blocks/fails through FK RESTRICT

delete first
    -> Definition CREATE fails referenced_resource_not_found
```

Use actual PostgreSQL reference arbitration. Do not add explicit generic endpoint lineage `FOR SHARE` just to make the test easy.

### GATE-04A — equivalent concurrent CREATE

Two semantically equivalent candidates with reordered unordered inputs:

- global gate serializes certification;
- exactly one Definition commits;
- loser observes winner in fresh certified set;
- loser -> `relationship_definition_equivalent`;
- no partial losing aggregate.

### GATE-04B — non-equivalent conflicting concurrent CREATE

Construct distinct semantic signatures with at least one cross-Definition conflict via same name + overlapping from/to spaces.

Exactly one conflicting set may commit; loser -> `relationship_definition_conflict`.

### GATE-05A — CREATE × RENAME to conflict

Create candidate and rename an existing Definition so both cannot coexist. Prove global candidate serialization and only a certified conflict-free final set.

### GATE-05B — RENAME(D1) × RENAME(D2)

Rename different Definitions toward conflicting state. Both may own their separate headers, but global certification gate allows only a conflict-free committed result.

Also add a same-Definition RENAME×RENAME regression proving header owner serialization occurs before the global gate.

### GATE-06A — explicit fresh post-gate snapshot

Design a deterministic test that would fail if gate acquisition and certified-set read were accidentally one stale-snapshot statement.

A waiter must block on the gate, previous holder commits a new certified Definition, waiter acquires gate, then a **subsequent statement** must observe that committed Definition and produce the corresponding equivalence/conflict outcome.

Assert the PostgreSQL blocker relation around the gate where applicable.

### GATE-06B — blocker DELETE concurrent with CREATE/RENAME

DELETE does not acquire the conflict gate.

Exercise visibility/order so that:

```text
blocker delete committed before candidate fresh read
    -> candidate may become admissible

candidate reads blocker before delete commit
    -> conservative equivalent/conflict failure is allowed
```

Cover CREATE and/or RENAME sufficiently to protect the no-gate DELETE rule; stronger coverage should exercise both candidate mutation shapes.

### ATOMIC-04C — complete Definition/Resolution mutation

Force a narrow test failure around a complete non-symmetric RENAME and prove no half-renamed Resolution set can commit. If rename is a single SQL statement, force rollback after the statement and before commit and verify the whole aggregate remains old.

Also verify symmetric two-row rename updates both Resolution names atomically where that shape exists.

## 18. Additional REALIZE-12 mechanism regressions

Add deterministic evidence for the frozen realization where not already subsumed by the canonical scenarios:

- unrelated RD.CREATE operations still serialize on the global conflict gate (intentional over-serialization);
- gate remains held through candidate commit/rollback;
- rollback releases the gate and leaves no partial certified candidate;
- RD.DELETE does not acquire the conflict gate;
- certified-set read does not take fan-out `FOR UPDATE` locks on unrelated Definitions;
- endpoint overlap covers equality, ancestor and descendant cases;
- complete non-symmetric and symmetric rename shape remains coherent;
- current runtime Relationship mutation is not implemented in S06 and therefore no S07 PAR/SNAP scenario is faked here.

## 19. Domain/application/persistence tests

Cover at minimum:

### Definition/Resolution pure semantics

- non-symmetric derivation, including same-template endpoints;
- symmetric same-template one-Resolution derivation;
- symmetric different-template reciprocal two-Resolution derivation;
- input order independence;
- stable IDs excluded from semantic signature;
- aggregate corruption/shape rejection;
- rename keeps IDs/endpoints/membership fixed;
- exact equivalence;
- conflict: same name + both spaces overlap;
- no conflict when name differs;
- no conflict when only from or only to overlaps;
- same-Definition internal Resolution overlap is not treated as cross-Definition conflict.

### Endpoint/reference semantics

- abstract ObjectTemplate endpoints accepted;
- endpoint with no default accepted;
- endpoint with no PUBLISHED exact version accepted;
- missing endpoint rejected as referenced operand;
- exact OTV lifecycle changes do not affect Definition validity;
- ObjectTemplate whole-lineage delete is blocked by committed Resolution references.

### Definition application/persistence

- CREATE inserts header + exact complete child set atomically;
- RENAME non-symmetric complete set;
- RENAME symmetric one/two physical rows;
- wrong RENAME shape for current symmetry;
- non-symmetric wrong/missing Resolution membership;
- DELETE absent path target vs successful delete;
- raw current factual `relationships` blocker -> `delete_blocked`;
- owned Resolution rows CASCADE only when Definition delete is admitted;
- corrupted persisted aggregate GET/certified-set interpretation -> internal failure;
- no standalone Resolution mutation surface.

## 20. API verification

Exercise every S06 public route:

```text
POST   /relationship-definitions
POST   /relationship-definitions/{id}/rename
DELETE /relationship-definitions/{id}
GET    /relationship-definitions
GET    /relationship-definitions/{id}
GET    /object-templates/{template_id}/relationship-capabilities
```

Verify:

- strict CREATE discriminated union and no scalar coercion;
- strict RENAME shapes and symmetry mismatch semantic failure;
- exact success statuses/body/Location;
- complete aggregate DTO with no nested definition ID and no forward/reverse fields;
- Definition list `id ASC`, full bounded aggregate items, cursor behavior;
- capability ancestor applicability and exact `name` filter;
- capability `resolution_id ASC`, cursor bound to path template + name filter;
- applicable distinct Resolution IDs are preserved even if names/compatibility spaces overlap;
- missing path resource vs missing body endpoint operand boundary;
- equivalent/conflict/delete-blocked finite error codes;
- malformed persisted state -> internal_error without persistence leakage;
- no public RelationshipResolution CRUD;
- no S07 runtime Relationship or Object-relationship routes;
- lifecycle response union remains intrinsic + ownership only in S06.

## 21. Scope/layer regressions

Keep/add cheap regressions proving:

- Relationship domain/application modules do not import FastAPI/Pydantic/SQLAlchemy;
- application layer constructs no SQLAlchemy statements;
- only the two frozen advisory gates exist;
- no migration is added;
- 13-table persistence authority remains unchanged;
- no source/target or forward/reverse fields are introduced;
- no RelationshipResolution standalone route exists;
- no runtime Relationship behavior is registered;
- no JSON Schema/ORM/generic repository abstraction appears.

## 22. Quality gates

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

PostgreSQL-required tests use the externally supplied dedicated target. With one shared `TEST_DATABASE_URL`, keep PostgreSQL suites serial with respect to xdist unless the environment supplies isolated DB targets per worker.

No generic retries and no sleep-based correctness coordination.

## 23. Documentation / completion discipline

Do not mark `docs/milestones/M1/status.md` complete. Reviewer owns completion status.

Do not modify frozen normative architecture merely to fit implementation. If implementation uncovers a genuine contradiction, stop the affected behavior and report it.

No normative architecture change is expected for S06 if the frozen design is followed.

At completion report:

- implementation commit SHA;
- changed-file summary;
- complete domain/application/persistence/API capability delivered;
- exact quality/test results and PostgreSQL version;
- canonical PGTEST scenarios + mechanism evidence;
- confirmation of no migration / S07 runtime behavior / standalone Resolution API / lifecycle Relationship variants;
- any unverified requirement or newly discovered contradiction.
