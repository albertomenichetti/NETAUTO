# M1 Architecture — Coding Baseline Index

**Status:** DRAFT architecture baseline — domain semantics, PostgreSQL persistence/concurrency/test architecture and the complete public HTTP/JSON API contract (API-01..03.11B) are substantially closed. The only explicitly remaining pre-freeze architecture question is the JSON Schema compiler surface/role, if retained in M1.

## 1. Purpose

`docs/milestones/M1/architecture/` is the normative architecture baseline from which M1 implementation is derived.

Implementation must follow:

```text
domain invariant / contract
-> semantic concurrency rule
-> PostgreSQL persistence/realization contract
-> real PostgreSQL test contract
-> application/API contract
-> code
```

A contradiction between architecture documents is an **architecture defect**. It is never an implementation choice and must be resolved in documentation before coding the affected behavior.

Do not infer authority from commit recency or from whichever document was read last.

## 2. Normative document map

### Cross-cutting persistence and concurrency

```text
persistence-model.md
    PostgreSQL authoritative tables, keys, FK/CHECK/delete/index layout,
    primitive persistence codec and denormalizations. PERSIST-01..15.

persistence-uow-concurrency.md
    UoW, READ COMMITTED baseline, owner lock strength/order,
    lifecycle admission and logical gates. PERSIST-16..20 + REALIZE-15.

concurrency-semantic-matrix.md
    32-operation semantic census and 19 safety predicates.
    Authority for what must remain true, independent of PostgreSQL.

concurrency-postgresql-realization-matrix.md
    Canonical REALIZE-01..15 index and cross-cutting realization registry.

concurrency-postgresql-realization-object-ownership.md
    Detailed REALIZE-08..11 plus Object/ownership REALIZE-15 impact.

concurrency-postgresql-realization-relationship.md
    Detailed REALIZE-12..14 plus Relationship REALIZE-15 impact.

concurrency-postgresql-test-matrix.md
    PGTEST-01..04 real-PostgreSQL scenario census, coverage mapping,
    deterministic harness contract and reusable execution recipes.
```

### Public/application API

```text
api-contract.md
    Application-command/query boundary, HTTP/JSON adapter principles,
    /api/v1/core capability namespace, canonical 32-mutation route inventory,
    semantic read projections and complete public success/failure boundary.
    API-01..02 plus API-03 integration.

api-wire-contract.md
    API-03 command/wire registry: API-03.1 strict caller-intent,
    API-03.2 expected_revision query placement, API-03.3 selectors,
    API-03.4 DataType command DTO, API-03.5 ObjectTemplate command DTO,
    API-03.6 Object command DTO, API-03.7 Relationship command DTO,
    API-03.8 PrimitiveType public lexical forms + byte-size contract,
    API-03.9 read registry, API-03.10 list registry,
    API-03.11 complete error/success registry.

api-read-contract.md
    API-03.9 canonical single-resource/projection read DTO: DataType,
    ObjectTemplate local/effective schema, capabilities, Object intrinsic,
    ownership, Relationship aggregate/views and lifecycle event union.

api-list-contract.md
    API-03.10 collection envelope, opaque keyset pagination, fixed canonical
    ordering, bounded summary/full list-item policy, route-specific exact
    filters and concurrent-page semantics.

api-error-contract.md
    API-03.11 failure boundary: transport-neutral failure classes,
    finite concrete public error-code catalog, bounded details schemas,
    HTTP status mapping and success body/status/Location policy.
```

### DataType

```text
datatype.md
```

### ObjectTemplate

```text
objecttemplate.md
objecttemplate-lifecycle.md
objecttemplate-properties.md
objecttemplate-components.md
objecttemplate-effective-schema.md
```

### Object / ownership / lifecycle

```text
object.md
object-runtime-state.md
object-schema-change.md
object-ownership.md
object-lifecycle-changelog.md
object-consistency-review.md
```

### Relationship R2

```text
relationship.md
relationship-definition.md
relationship-resolution.md
relationship-runtime.md
relationship-concurrency.md
relationship-consistency-review.md
```

## 3. Closed M1 architecture areas

The following are not implementation-choice TODOs anymore:

- PostgreSQL-only authoritative persistence model and 13-table authority map;
- exact DTV/OTV identities and stable-lineage/exact-pin representation;
- Object canonical JSONB state and `canonical_name` bound `1..255`;
- ownership persistence, child PK single-owner authority, FK `RESTRICT` lifetime;
- Relationship R2 physical authority, exact runtime-view PK and Definition/Resolution same-definition constraints;
- typed lifecycle-event persistence, historical non-FK identities and `transaction_timestamp()` semantics;
- primitive persistence codec including exact-decimal JSON string, datetime UTC `Z`, integer byte-size;
- DB-vs-UoW enforcement boundary and no-constraint-trigger baseline;
- semantic write UoW and `READ COMMITTED` mutation isolation;
- all 19 semantic concurrency predicate realizations (REALIZE-01..15);
- non-key owner `FOR NO KEY UPDATE` vs delete/key-changing `FOR UPDATE` distinction;
- lifecycle-sensitive dependency `FOR SHARE` admission/certification;
- active-model direct-dependency synchronization without a global model gate;
- immediate FK `RESTRICT` reference-lifetime authority;
- ownership cycle transaction advisory gate and post-wait fresh-snapshot rule;
- RelationshipDefinition conflict transaction advisory gate and post-wait fresh-snapshot rule;
- runtime Relationship exact-view arbitration, fresh-UoW convergence and exact-ID ABA semantics;
- Relationship lifecycle one-statement metadata snapshot semantics;
- canonical real-PostgreSQL concurrency scenario census and 19-predicate coverage mapping (PGTEST-01..02);
- deterministic real-PostgreSQL concurrency harness contract, blocker observation, timeout/isolation/diagnostic rules and stress-vs-contract separation (PGTEST-03);
- eight reusable deterministic execution recipes and complete 51-scenario recipe mapping (PGTEST-04);
- API/application boundary: command/query contracts authoritative, HTTP/JSON adapter, operation-specific command DTO principle, no generic PATCH, transport-neutral failure boundary (API-01);
- public kernel capability namespace `/api/v1/core`, canonical POST-command/GET/DELETE method convention, complete 32-mutation route inventory, semantic read projections and forbidden generic CRUD/owned-child mutation surface (API-02);
- API-03.1 strict request intent rules: unknown fields/coercion prohibited, omission distinct from explicit caller intent, defaults only fill omission, explicit invalid values fail, JSON null valid only as an actual nullable semantic state;
- Object CREATE `canonical_name` omission -> UUID-string fallback while explicit null/empty/invalid input fails;
- API-03.2 uniform required positive-integer `expected_revision` query parameter for DTV/OTV REVISE, PUBLISH and DELETE_DRAFT, with no ETag/If-Match reinterpretation;
- API-03.3 type-specific exact/implicit selector contract: omission resolves a default only for Object CREATE OTV selection, ObjectTemplate parent-version selection and property DTV binding/rebinding; CREATE_NEXT, SET_DEFAULT and Object SCHEMA_CHANGE remain exact-only; no generic default/latest/highest selector token;
- API-03.4 DataType command DTO contract: CREATE builds lineage + v1 DRAFT, optional `constraints` defaults to `{}`, REVISE requires complete `constraints`, command-specific DTOs never expose caller-controlled id/version/revision/status/default state;
- API-03.5 ObjectTemplate command DTO contract: CREATE requires explicit `abstract`, optional declaration collections default to `[]`, property/component declaration DTOs are strict, `position` is the ordering authority, and REVISE requires complete local property/component arrays;
- API-03.6 Object command DTO contract: CREATE properties omission means zero supplied values, DATA_CHANGE is a non-empty unordered per-property `SET|REMOVE` operation set with no duplicate property operations, SCHEMA_CHANGE has exact target only, ATTACH/DETACH use strict slot+child bodies, DELETE has no cascade/force options;
- API-03.7 RelationshipDefinition/Relationship command DTO contract: symmetric/non-symmetric Definition CREATE/RENAME shapes follow the resolved aggregate semantics, Definition/Resolution/Relationship create-time IDs are kernel-generated, runtime Relationship CREATE accepts exactly resolution/from/to Object IDs, self-loop is not structurally forbidden, and deletes expose no cascade/semantic-tuple alternatives;
- API-03.8 PrimitiveType public lexical contract: one parser/canonicalizer per primitive across Object values, constraints/enums and migration defaults; exact-decimal `core.number` is string-only without exponent; date/datetime/IP/prefix carrier grammars and canonicalization are fixed;
- `core.byte_size` public input accepts exact integer bytes or strict SI/IEC quantity strings, with canonical response/persistence always exact integer bytes;
- API-03.9 canonical single/projection read DTO contract: no generic data envelope for single reads; stable/exact/effective projections remain distinct; Object GET is intrinsic-only; ownership and Relationship reads are semantic projections; detached owner is `200 null`; lifecycle read is a discriminated event-family union;
- API-03.10 collection/list contract: uniform `{items,next_cursor}` envelope, opaque keyset cursor only, default `limit=100`/max 500, fixed route-specific ordering, bounded list summaries for DTV/OTV/Object, exact route-specific filters, no generic sort/query DSL, no cross-request snapshot promise;
- Object collection pagination key is immutable `id ASC`, while exact `canonical_name` filter is supported independently;
- Object-specific lifecycle route means events involving the Object (`object_id=X OR destination_object_id=X`) and lifecycle ordering is `(occurred_at,id) DESC`;
- API-03.10 PERSIST-15 read-path indices are normative: `objects(canonical_name,id)`, `object_lifecycle_events(kind,occurred_at,id)`, and partial `object_lifecycle_events(relationship_name,occurred_at,id) WHERE relationship_name IS NOT NULL`;
- API-03.11 failure classes/status baseline is frozen: `INVALID_REQUEST=400`, `NOT_FOUND=404`, `SEMANTIC_VALIDATION=422`, `STATE_CONFLICT=409`, `INTERNAL_FAILURE=500`;
- API-03.11 reserves 404 for missing URI/path target identity; missing command operands use `referenced_resource_not_found`/422; malformed `expected_revision` is 400 while stale well-formed revision is `stale_revision`/409;
- API-03.11 finite public error-code catalog is frozen; known M1 lifecycle/default/dependency/ownership/schema-change/Relationship conflicts use dedicated stable codes and no generic conflict escape hatch;
- API-03.11 canonical error DTO is flat `{code,message,details}`, with bounded semantic details and no SQL/stack/constraint leakage; `internal_error` is the only public 500 code;
- domain-defined idempotent no-op/convergence remains success and is never reclassified as conflict solely because no persistence row changed;
- API-03.11 success policy is frozen: GET=200; newly created public resource=201 + `Location`; normal semantic mutation=200 with resulting projection; ATTACH=200; DETACH=204 including detached no-op; DELETE=204; Relationship CREATE convergence=200 vs new fact=201; absent exact Relationship DELETE=204; no `202` asynchronous kernel success;
- DT/OT CREATE return command-specific lineage + v1 DRAFT results; DT/OT CREATE_NEXT returns the new exact-version DTO; generic success/changed flags and SQL affected-row responses are forbidden.

The PostgreSQL concurrency/test architecture is therefore considered closed for M1. A PGTEST-05 is not planned merely to design fixtures, helper classes or test-file structure: those are implementation-decomposition concerns as long as they preserve PGTEST-01..04. Reopen the PGTEST architecture only for a genuine architecture-level gap or retroactive finding.

Reopening any closed area requires an explicit architecture change, not a local implementation optimization.

## 4. Remaining pre-coding/final-freeze work

At the current checkpoint the only explicitly documented architecture question remaining before final M1 freeze is:

```text
JSON Schema compiler surface/role, if retained in M1
```

If that capability is removed from M1 rather than retained, document the removal explicitly rather than leaving it as an implementation-choice TODO.

If later review discovers a new architecture gap, add it here and to the owning domain/cross-cutting document in the same documentation cycle.

## 5. Documentation alignment invariant

A cross-cutting decision is considered consolidated only after all documents that state the affected assumption are aligned.

For example a lock-strength or public-route change must update, as applicable:

```text
canonical realization/index document
persistence UoW or API baseline
Object/ownership or Relationship companion/domain document
PostgreSQL test matrix
public API contract
```

Stale phrases such as “mechanism still to be finalized” must not remain when that mechanism has become normative elsewhere.

Architecture review before implementation must actively search for such stale-open markers.

If a new design point reveals a retroactive finding, the design sequence is interrupted: the finding is propagated immediately to every affected normative document before the next design point is ratified. Deferring propagation to a later sweep is not allowed when the affected baseline is already known.

### 5.1 Pre-flight revalidation before every dependent design point

Before starting design point `N+1`, identify which already-consolidated M1 assumptions the new point depends on and **re-read the corresponding normative repository documents** before deriving the new design.

The chat history, summaries and remembered decisions are navigation aids, not the authoritative source for this pre-flight.

The scope is dependency-driven rather than mechanically global. A point that touches only one narrow contract may require a small re-read; a cross-cutting point must revalidate every affected authority. Typical sources include:

```text
owning domain document
cross-domain contract involved by the point
persistence/concurrency/API contract whose representation/mechanism is assumed
this architecture index for closed/open status
```

The required sequence is:

```text
N+1 dependencies identified
-> authoritative docs re-read
-> assumptions checked against current baseline
-> any drift/conflict/stale-open marker fixed and propagated
-> only then N+1 design begins/continues
```

Particular care is required where multiple representations exist. The pre-flight must not conflate:

```text
domain accepted-input semantics
canonical in-memory/domain state
canonical persistence representation
public API wire representation
```

A new transport or implementation decision may choose a representation for its own boundary, but may not silently narrow or widen an already-ratified domain contract.

## 6. Coding gate

Before creating implementation `steps.md` or coding M1 behavior, verify:

1. owning domain contract is frozen enough for the change;
2. persistence authority is identified;
3. every relevant non-`I` concurrency predicate maps to a REALIZE mechanism;
4. required real-PG scenario IDs, deterministic harness contract and execution recipe mapping exist;
5. application/API route, DTO and failure contract are defined for exposed behavior and preserve the semantic operation boundary;
6. no architecture document states a contradictory or still-open version of the same decision.

If any item fails, return to architecture rather than deciding in code.
