# Codex implementation prompt — M1-S04

**Status:** NON-NORMATIVE IMPLEMENTATION PROMPT.

This file is an execution aid for Codex. It does not override `AGENTS.md`, the frozen M1 contract/architecture/steps, or the ratified technology baseline.

## Assignment

Implement exactly:

```text
M1-S04 — Object intrinsic state and intrinsic lifecycle vertical slice
```

from `docs/milestones/M1/steps.md`.

M1-S00 through M1-S03 are complete. Do not implement M1-S05 or later Object ownership/schema-change/Relationship behavior.

## Mandatory pre-flight

Before changing implementation files, re-read and obey:

```text
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md
docs/milestones/M1/contract.md
docs/milestones/M1/architecture/README.md
docs/milestones/M1/steps.md
docs/milestones/M1/status.md

docs/milestones/M1/architecture/object.md
docs/milestones/M1/architecture/object-runtime-state.md
docs/milestones/M1/architecture/object-lifecycle-changelog.md
docs/milestones/M1/architecture/objecttemplate-effective-schema.md
docs/milestones/M1/architecture/objecttemplate-lifecycle.md
docs/milestones/M1/architecture/objecttemplate-properties.md
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

Confirm from the repository itself:

```text
M1 contract      = FINAL / FROZEN
M1 architecture  = globally FROZEN as a set
M1 steps         = FINAL / FROZEN
M1-S00..S03      = COMPLETED
current step     = M1-S04
STACK-01..09     = RATIFIED
```

Individual architecture documents may retain historical `DRAFT` headers; the architecture index is the set-level freeze authority.

If normative authorities conflict, stop the affected work and report the contradiction rather than choosing an interpretation. Do not use historical Git code as an implementation baseline.

## Objective

Deliver the complete S04 intrinsic Object vertical capability:

```text
kernel-generated Object identity
-> exact published ObjectTemplateVersion admission
-> definitive exact schema closure
-> canonical runtime property state
-> Object CREATE / RENAME / DATA_CHANGE
-> atomic intrinsic lifecycle event persistence
-> Object GET/list
-> lifecycle list/read machinery for intrinsic events
-> deterministic real-PostgreSQL concurrency verification
```

At the end of S04 a caller must be able to create, read, rename and data-mutate an Object through `/api/v1/core` while current state and intrinsic lifecycle history remain canonical, atomically consistent and PostgreSQL-concurrency-correct.

## Hard scope boundary

S04 MUST NOT implement:

```text
Object SCHEMA_CHANGE
Object ATTACH / DETACH
Object DELETE
runtime ownership semantics
ownership graph gate use
component/owner public projections
RelationshipDefinition behavior
runtime Relationship behavior
Object relationship reads
structural ownership lifecycle event production
Relationship lifecycle event production
subtree delete / cascade / force semantics
cross-lineage Object reclassification
Object state_revision / ETag / If-Match
JSON Schema compiler/projection
persistent effective-schema cache
new persistence tables or S04 schema migration
ORM Session / AsyncSession
generic repository framework
generic command bus / DI container
background jobs / 202 semantics
Docker/Testcontainers/test-DB provisioning
```

Do not register fake implementations for S05+ Object routes. In particular do not add placeholder `/schema-change`, `/attach`, `/detach`, Object DELETE, `/components`, `/owner` or `/relationships` behavior merely because the full M1 route inventory contains them.

The lifecycle table already exists physically from S01. S04 writes only intrinsic `CREATED`, `RENAME` and `DATA_CHANGE` transitions. It may implement the common intrinsic read representation needed for the already-frozen intrinsic family, but it must not invent ownership/Relationship event-generation semantics.

## 1. Object domain model and identity

Implement one plain-Python Object domain representation containing exactly the intrinsic current snapshot:

```text
id
canonical_name
template_id
template_version
properties
```

Rules:

- `id` is application/kernel-generated UUIDv4 and immutable;
- caller never supplies `id`;
- `template_id` is the immutable stable ObjectTemplate lineage assignment;
- `template_version` is the exact current OTV pin;
- no Object `state_revision` exists;
- ownership and Relationships are not fields of this intrinsic Object snapshot;
- domain code has no FastAPI/Pydantic/SQLAlchemy dependency.

### canonical_name

```text
CREATE omitted
    -> str(Object.id)

CREATE explicitly supplied
    -> exact supplied string
    -> length 1..255
    -> no trim/casefold/normalization

explicit null
    -> invalid caller intent

RENAME
    -> exact explicit string 1..255
    -> changes only canonical_name
```

`canonical_name` is not unique and is not Object identity.

## 2. Definitive exact schema closure

Every Object interpretation is anchored by the persisted exact `(template_id, template_version)`.

The definitive closure is:

```text
exact OTV
-> exact parent OTV chain
-> effective properties
-> each property's exact DTV
```

Never consult during definitive closure resolution:

```text
ObjectTemplate.default_version
DataType.default_version
latest/highest versions
```

except when resolving the **new Object CREATE selector itself** before the exact Object pin exists.

The target OTV's effective component slots are not part of Object property validation in S04; a newly created Object is detached.

### Reuse the S03 resolver without nested UoWs

S04 must not call `ObjectTemplateService.get_effective_schema()` from inside an Object semantic mutation, because that method owns a separate UoW/read transaction.

If needed, refactor the smallest concrete shared helper that:

- accepts the already-owned caller `ObjectTemplateStore` / connection;
- follows exact persisted parent pins;
- reuses the plain-Python `resolve_effective_schema` authority;
- performs no commit and opens no second UoW;
- maps impossible persisted closure state to internal invariant failure, not caller semantic validation.

Do not create a generic repository/schema-service framework merely for this reuse.

For Object property validation load the exact DTV snapshot referenced by every effective property using the same caller UoW connection. Missing/corrupt exact dependencies that should exist by frozen invariants are `internal_error` conditions.

## 3. Object CREATE target admission

Public CREATE selector:

```text
template_id required

template_version present
    -> explicit exact OTV selection

template_version omitted
    -> resolve ObjectTemplate.default_version
    -> no highest/latest fallback
```

### Explicit selection

Within the Object CREATE UoW:

```text
exact target OTV FOR SHARE
-> fresh PUBLISHED check
-> read stable target lineage metadata
-> require abstract=false
-> keep the exact OTV SHARE lock until Object + CREATED event commit
```

Stable `abstract` is immutable metadata; do not add an unnecessary lineage lifecycle lock for explicit selection.

### Implicit selection

Use the existing caller-owned-UoW ObjectTemplate admission seam:

```text
ObjectTemplate lineage FOR SHARE
-> read current default_version
-> exact default OTV FOR SHARE
-> fresh PUBLISHED check
-> require abstract=false
-> materialize the selected exact version into the Object row
-> keep locks through commit
```

Failure semantics:

- missing referenced lineage/exact body operand -> `referenced_resource_not_found` / 422;
- implicit selection with `default_version = NULL` -> `default_version_unavailable` / 409;
- exact target exists but is not PUBLISHED -> `dependency_not_admissible` / 409;
- abstract target lineage -> `semantic_validation_failed` / 422;
- impossible persisted active-model/effective-schema corruption -> `internal_error` / 500.

A PUBLISHED OTV is the consistency anchor. Do not recursively lifecycle-lock every parent OTV or DTV during Object CREATE. S03's active-model-graph invariant already certifies the direct/transitive closure.

The existing Object -> exact OTV composite FK remains final referential-lifetime authority against target lineage delete races. Translate known FK race loss into the frozen semantic failure boundary without SQL/constraint leakage.

## 4. Canonical runtime-property authority

Implement one plain-Python Object runtime-state validator/canonicalizer that reuses the S02 `validate_value()` PrimitiveType authority. Do not create another primitive parser or JSON Schema representation.

For each effective property:

```text
SCALAR optional -> 0..1
SCALAR required -> exactly 1
LIST optional   -> 0..N
LIST required   -> 1..N
```

Rules:

- request `properties` is keyed by effective property name;
- unknown property -> semantic validation failure;
- JSON null is never a runtime value;
- SCALAR accepts one primitive carrier, never a list as a scalar shortcut;
- LIST requires a JSON array and validates/canonicalizes each item independently;
- LIST order is preserved;
- LIST duplicates are allowed;
- all values use the exact pinned DTV's `base_type` and canonical constraints;
- optional LIST `[]` canonicalizes to key absence;
- all semantic zero-cardinality state is persisted as key absence;
- any persisted LIST value that is present is therefore non-empty;
- required LIST `[]` is invalid;
- `migration_default` is NEVER used by Object CREATE;
- `properties` omitted on CREATE means `{}` and therefore does not satisfy required members automatically.

Persist only the complete canonical JSON-compatible property object.

A useful plain-Python design is a resolved runtime-property specification derived from effective member + exact DTV state, followed by one candidate canonicalization/validation function. Keep I/O outside that pure validation layer.

## 5. CREATE semantic transaction

CREATE must execute as one semantic UoW:

```text
parse static request intent
-> generate Object UUIDv4
-> resolve/admit target exact OTV on this UoW
-> derive definitive effective property closure
-> load exact DTV semantics on this UoW
-> build complete canonical Object candidate
-> validate candidate
-> INSERT Object current row
-> INSERT CREATED lifecycle event
-> commit
```

Any failure rolls back both Object and event.

Object is born detached; do not insert `object_components` state.

### CREATED event

```text
kind           = CREATED
object_id      = Object.id
canonical_name = created/final canonical_name
before_state   = NULL
after_state    = complete canonical Object snapshot
```

All structural/Relationship columns are absent/NULL according to the frozen table CHECKs.

Event `id` and `occurred_at` use the PostgreSQL server defaults already present:

```text
id          -> gen_random_uuid()
occurred_at -> transaction_timestamp()
```

Do not generate lifecycle event UUID/timestamp in application code.

## 6. RENAME

RENAME body is exactly:

```json
{"canonical_name":"..."}
```

Transaction:

```text
Object row FOR NO KEY UPDATE
-> re-read complete current Object snapshot after lock
-> build before snapshot
-> update only canonical_name
-> build after snapshot from the same serialized transition
-> insert one RENAME event
-> commit
```

Do not modify `template_id`, `template_version`, `properties`, ownership or any other state.

Use `FOR NO KEY UPDATE`, not `FOR UPDATE`. This lock-strength distinction is part of REALIZE-15 and must remain compatible with future FK key-share parallelism.

## 7. DATA_CHANGE

Public body is a strict required non-empty operations array.

Operation variants:

```text
SET
    exactly: op, property, value

REMOVE
    exactly: op, property
    value forbidden
```

The same property may occur at most once in one request. Duplicate property operations and empty operation sets are malformed transport input (`invalid_request` / 400), not domain merge semantics.

Array order is not semantic authority.

### DATA_CHANGE transaction

```text
Object row FOR NO KEY UPDATE
-> re-read complete current Object after lock
-> resolve its CURRENT persisted exact OTV closure
-> load exact historical DTV semantics
-> apply all SET/REMOVE operations in memory
-> canonicalize affected values through S02 PrimitiveType authority
-> validate the COMPLETE final Object property state
-> compare final canonical state with current canonical state
-> if identical: return current Object success, no state write and no lifecycle event
-> otherwise persist complete canonical properties
-> insert one DATA_CHANGE event
-> commit
```

Do not use current ObjectTemplate/DataType defaults. An Object already pinned to a DEPRECATED OTV remains mutable through RENAME/DATA_CHANGE; existing historical exact bindings are not new admission and are not re-certified as PUBLISHED.

SET semantics:

- effective property must exist;
- replaces the property's whole semantic value;
- LIST SET replaces the whole list;
- optional LIST `SET []` converges to absence;
- `SET null` is semantic invalid input;
- no append/index/item mutation exists.

REMOVE semantics:

- effective property must exist;
- removes the property from the candidate;
- final full-state validation decides whether removal is legal;
- removing a required property therefore fails.

A non-empty request that canonicalizes to the identical semantic property state is a valid `200` no-op and emits **no** lifecycle event.

### DATA_CHANGE event

For a real transition:

```text
kind = DATA_CHANGE
before_state = complete canonical Object snapshot before
                (same id/name/template exact pin/current properties)
after_state  = complete canonical Object snapshot after
```

`canonical_name`, `template_id` and `template_version` remain unchanged between before/after.

## 8. Object persistence

Use the existing S01 physical `objects` table and exact metadata. No migration.

Add only concrete persistence helpers needed for S04, for example:

```text
insert/load Object
Object non-key owner lock
update canonical_name
update canonical properties
Object keyset list query
insert/read lifecycle event
lifecycle keyset list query
```

No generic repository base.

The Object current row remains:

```text
id UUID PK
canonical_name TEXT 1..255, non-unique
template_id UUID
template_version positive INTEGER
properties JSONB object
composite exact OTV FK RESTRICT
```

Unexpected integrity errors are internal failures unless the frozen contract identifies a specific expected race to translate.

## 9. Intrinsic lifecycle persistence/read model

Use the existing typed `object_lifecycle_events` table. Do not introduce a generic event payload.

For intrinsic rows:

```text
id
occurred_at
kind
object_id
canonical_name
before_state
after_state
```

Structural fields remain NULL.

Persist `before_state` / `after_state` as canonical JSONB Object snapshots with the same semantic shape as Object GET:

```json
{
  "id": "<uuid>",
  "canonical_name": "...",
  "template_id": "<uuid>",
  "template_version": 1,
  "properties": {}
}
```

Lifecycle historical UUIDs remain plain historical values with no live FK semantics.

S04 produces only:

```text
CREATED
RENAME
DATA_CHANGE
```

The intrinsic read representation may support the already-frozen intrinsic family (`CREATED`, `RENAME`, `DATA_CHANGE`, `SCHEMA_CHANGE`, `DELETED`) because they share the canonical before/after snapshot DTO, but S04 must not implement future SCHEMA_CHANGE/DELETE mutations.

Do not implement ownership or Relationship event generation in S04.

Persisted lifecycle rows that violate the frozen family/snapshot semantics are server invariant corruption and must surface as `internal_error`, not caller `semantic_validation_failed`.

Append-only behavior remains application/kernel-owned: no public lifecycle UPDATE/DELETE/CREATE operation.

## 10. Public Object API delivered in S04

Register exactly the S04 Object write/read capability:

```text
POST /api/v1/core/objects
POST /api/v1/core/objects/{object_id}/rename
POST /api/v1/core/objects/{object_id}/data-change

GET  /api/v1/core/objects
GET  /api/v1/core/objects/{object_id}
```

Do not register S05+ Object mutation/projection placeholders.

### CREATE request

Strict Pydantic transport model:

```text
template_id required UUID carrier
template_version optional positive integer; explicit null forbidden
canonical_name optional strict string 1..255; explicit null forbidden
properties optional JSON object; omission -> {}; explicit null forbidden
unknown top-level fields forbidden
```

`properties` values remain raw JSON carriers until mapped to the application/domain PrimitiveType authority. Pydantic must not duplicate primitive semantics.

### RENAME request

Exactly one strict `canonical_name:string` 1..255.

### DATA_CHANGE request

Strict discriminated `SET|REMOVE` operation models, extra fields forbidden, non-empty array, one operation per property.

Transport rejects malformed shape with the existing `invalid_request` mapping; semantic Object/property failures use `semantic_validation_failed`.

### Success

```text
Object.CREATE
    -> 201 Created
    -> Location=/api/v1/core/objects/{id}
    -> canonical Object DTO

RENAME / DATA_CHANGE
    -> 200
    -> canonical Object DTO
```

Object DTO is exactly:

```text
id
canonical_name
template_id
template_version
properties
```

No owner/components/relationships/lifecycle are embedded.

## 11. Object collection

Implement:

```text
GET /api/v1/core/objects
```

Envelope:

```json
{"items": [...], "next_cursor": null}
```

Summary item exactly:

```text
id
canonical_name
template_id
template_version
```

`properties` omitted from list summary.

Canonical ordering:

```text
id ASC
```

Exact filters:

```text
template_id=<uuid>
template_version=<positive-int>
canonical_name=<exact string>
```

`template_version` without `template_id` is `invalid_request` / 400.

Pagination:

```text
opaque route/filter/order-specific keyset cursor
limit default 100
limit 1..500
no offset/page/sort
```

`canonical_name` is only an exact filter, never identity or primary ordering.

Reuse the S02/S03 cursor utilities; do not create a second cursor framework.

## 12. Lifecycle public reads delivered in S04

Implement the frozen read-only routes needed to expose committed intrinsic events:

```text
GET /api/v1/core/lifecycle-events
GET /api/v1/core/objects/{object_id}/lifecycle-events
```

There is no exact lifecycle-event detail route and no lifecycle mutation route.

Return the normal API-03.10 page envelope with complete discriminated intrinsic event items.

Canonical ordering:

```text
(occurred_at, id) DESC
```

The event UUID is only a deterministic tie-breaker, not a time sequence.

Global route filters:

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

The S04-supported dataset contains intrinsic events, so structural/Relationship-oriented filters normally yield no rows until later slices; implementing those query fields does not authorize structural event production.

Object-specific route means:

```text
object_id = path_id
OR
destination_object_id = path_id
```

It does not accept a second `object_id` query parameter. Other lifecycle filters may remain available according to API-03.10.

The path Object is a normal URI-selected resource: if it is absent, use `resource_not_found` / 404. (S04 does not implement Object DELETE, so supported S04 lifecycle rows always concern current Objects.)

`occurred_from` / `occurred_to` must reuse API-03.8/core.datetime lexical/canonical parsing; do not create a second permissive datetime grammar.

Lifecycle cursor identity includes route + all active filters; the Object-specific route identity must include the path Object id. `limit` is not part of query identity.

Do not treat lifecycle pagination as a transaction snapshot, CDC cursor or strict commit-order feed.

## 13. Failure boundary

Application/domain remains HTTP-agnostic.

S04 must use the existing finite failure catalog, including as applicable:

```text
invalid_request
invalid_cursor
resource_not_found
referenced_resource_not_found
semantic_validation_failed
default_version_unavailable
dependency_not_admissible
delete_blocked only when exercising target lineage delete from existing OT behavior
internal_error
```

Do not invent an Object-specific generic conflict code.

Examples:

```text
path Object missing
    -> 404 resource_not_found

CREATE referenced template missing
    -> 422 referenced_resource_not_found

CREATE abstract template
unknown/missing/invalid runtime property
constraint/cardinality/null failure
    -> 422 semantic_validation_failed

implicit target default unavailable
    -> 409 default_version_unavailable

explicit/selected OTV no longer PUBLISHED
    -> 409 dependency_not_admissible

persisted impossible exact schema/lifecycle state
unexpected persistence invariant
    -> 500 internal_error
```

Never expose SQL, constraint/table names or stack traces publicly.

## 14. Concurrency realization

### Object current-state owner

RENAME and DATA_CHANGE use:

```text
Object row FOR NO KEY UPDATE
```

After a wait, reload the complete Object row and derive the transition from that fresh committed state.

Do not use process-local locks and do not strengthen this to `FOR UPDATE`.

### Object CREATE binding admission

Use the target OTV `FOR SHARE` semantics described above and keep protection to Object commit. Existing exact parent/DTV closure is interpretation state, not a set of new bindings from Object CREATE.

### No automatic retry

Do not automatically replay caller intent after lock waits/deadlocks/stale state. PG deadlock detection remains fallback failure behavior, not normal serialization machinery.

## 15. Required deterministic PostgreSQL scenarios

Real PostgreSQL is mandatory through external `TEST_DATABASE_URL`.

### ROW-11 — DATA_CHANGE × DATA_CHANGE

Use two independent semantic UoWs against the same Object.

Prefer an initial Object with at least two mutable properties and concurrent changes to different properties so a stale whole-JSONB overwrite would lose one update.

Prove:

```text
T1 acquires Object FOR NO KEY UPDATE and reaches deterministic cut
T2 waits on same Object owner
pg_blocking_pids(T2_pid) contains T1_pid
T1 commits
T2 wakes and re-reads the committed Object
T2 applies intent to the fresh state
final canonical properties contain both serial changes
```

Also assert the two DATA_CHANGE lifecycle snapshots form a serially explainable sequence; no event may describe an impossible before/after state.

No sleep orchestration.

### Object target-admission race

Add deterministic evidence that Object CREATE's exact OTV SHARE protection remains live until Object commit against concurrent target `OT.DEPRECATE`.

Allowed serial outcomes include:

```text
CREATE admits/commits while target is PUBLISHED
-> later DEPRECATE may succeed (existing Object does not block OTV deprecation)

DEPRECATE wins before CREATE admission
-> CREATE fails dependency_not_admissible
```

Never commit a new Object whose target was already non-PUBLISHED before its admission/commit.

For implicit binding, add at least one deterministic default-policy race (`SET_DEFAULT` or `CLEAR_DEFAULT`) proving selection is coherent and the resulting Object pin is exact/materialized. Reuse canonical ROW-07/ROW-08 traceability only when the concrete scenario genuinely matches the PGTEST authority/mechanism.

### REF-01 — Object exact-OTV variant

Implement the canonical Object variant:

```text
OBJ.CREATE -> exact OTV
×
OT.DELETE_LINEAGE(target)
```

Exercise the real exact/composite FK and target lifetime authority with independent transactions and `pg_blocking_pids()` where blocking is expected.

Cover both explainable directions where practical:

```text
reference/create wins
    -> target delete cannot commit (`delete_blocked`)

target delete wins
    -> Object create cannot commit; referenced target failure, no orphan Object/event
```

Do not replace the actual FK mechanism with an artificial lifecycle lock solely for the test.

### ATOMIC-04A — intrinsic Object state/event atomicity

Force a test-only failure at a narrow persistence phase around a real intrinsic transition, preferably after current-state DML and before/while lifecycle insert.

Prove rollback leaves:

```text
old current Object state intact
no corresponding lifecycle event committed
```

The test-only interception must not alter production SQL/transaction semantics and must not create a production pause hook.

Also prove Object CREATE + CREATED event rollback all-or-nothing on a suitable forced-failure path or equivalent aggregate/event atomicity evidence if it adds distinct value.

### Additional same-owner regression

Add a targeted RENAME × DATA_CHANGE same-Object scenario or equivalent evidence that both use the same Object non-key owner and their current-state/event snapshots remain serially explainable.

## 16. Required domain/application/API tests

### Pure/domain

Cover at minimum:

- canonical name creation fallback is application-owned and explicit values are preserved;
- runtime SCALAR/LIST shape validation;
- required/optional cardinality;
- unknown properties;
- JSON null rejection;
- optional LIST absent vs `[]` canonical convergence;
- required LIST empty rejection;
- duplicate LIST items preserved;
- representative primitive canonicalization reuse: exact decimal, datetime, IP/prefix, byte size;
- exact DTV constraints and enum behavior reused from S02;
- complete final-state validation after DATA_CHANGE;
- SET/REMOVE semantics and optional-list `SET []` -> absence;
- DATA_CHANGE semantic no-op detection.

Use targeted Hypothesis only where it tests a meaningful pure invariant (for example Object candidate canonicalization idempotence or LIST item canonicalization). Do not add property tests mechanically.

### Application/persistence

Cover:

- explicit and implicit OTV selection/materialization;
- missing default, abstract target, non-PUBLISHED target;
- PUBLISHED target active-graph interpretation without redundant transitive lifecycle locks;
- Object create on exact effective inherited schema;
- migration_default is not a creation default;
- canonical Object JSONB round-trip;
- existing Object on DEPRECATED OTV can RENAME/DATA_CHANGE using immutable historical exact schema;
- object owner lock strength is `FOR NO KEY UPDATE` behavior, not `FOR UPDATE`;
- DB-generated lifecycle id/time defaults;
- typed intrinsic event row shape and historical no-live-FK semantics where applicable;
- no-op DATA_CHANGE inserts no event;
- persistence/invariant corruption maps internal rather than caller semantic failure.

### API

Cover every S04 route and relevant failures:

```text
POST /objects
POST /objects/{id}/rename
POST /objects/{id}/data-change
GET  /objects
GET  /objects/{id}
GET  /lifecycle-events
GET  /objects/{id}/lifecycle-events
```

Verify:

- strict body/query/path behavior and unknown fields;
- omission vs explicit null;
- CREATE 201 + exact Location + DTO;
- RENAME/DATA_CHANGE 200 + Object DTO;
- DATA_CHANGE no-op 200 and no new lifecycle row;
- Object list summary/order/filters/keyset cursor/filter mismatch;
- dependent `template_version` filter rule;
- lifecycle discriminated intrinsic DTOs;
- CREATED before=null; RENAME/DATA_CHANGE before+after complete;
- lifecycle ordering/filtering/cursor identity;
- object-specific involving predicate;
- no fake S05+ routes are registered as successful capabilities.

## 17. Scope/architecture regression tests

Add or preserve cheap tests that ensure S04 does not accidentally introduce:

```text
SQLAlchemy imports in domain/application semantic modules
Pydantic/FastAPI imports in domain/application modules
ORM Session / AsyncSession
Object state_revision
Object DELETE/SCHEMA_CHANGE/ATTACH/DETACH implementation
ownership gate use
Relationship behavior
lifecycle public mutation routes
generic event payload
migration/schema changes
JSON Schema
```

Application may depend on concrete persistence stores/UoW abstractions; it must not build SQLAlchemy statements itself.

## 18. Required quality gates

With the real test PostgreSQL target supplied through `TEST_DATABASE_URL`, run at least:

```bash
uv lock
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -m "not postgresql"
uv run pytest -m postgresql
```

PostgreSQL-required tests remain serial with respect to xdist when only one `TEST_DATABASE_URL` is supplied.

Report exact commands/results and PostgreSQL server version.

No missing PostgreSQL run is accepted for S04 completion.

## 19. Completion report

At the end report:

- commit SHA and confirmation pushed to `origin/core_review`;
- files/layers added/changed;
- Object domain/current-state representation;
- exact OTV admission strategy and proof lock lifetime is caller-UoW-owned;
- definitive effective-schema + DTV resolution strategy without nested UoW/default lookup;
- canonical runtime property pipeline and no-op logic;
- lifecycle current-state/event atomicity strategy and DB-generated event identity/time;
- Object/lifecycle API routes implemented;
- exact deterministic PGTEST IDs/variants/equivalent probes implemented and semantic outcomes asserted;
- full quality-gate results and PostgreSQL version;
- confirmation that no S05+ capability was implemented;
- any requirement that could not be verified.

Do not mark `docs/milestones/M1/status.md` complete yourself. Reviewer controls step completion.