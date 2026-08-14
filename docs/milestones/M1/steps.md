# M1 — Implementation Steps

**Status:** FINAL / FROZEN — implementation decomposition ratified from the `FINAL / FROZEN` M1 contract and globally `FROZEN` M1 architecture. M1 implementation is authorized to proceed step-by-step from `M1-S00`, subject to the mandatory pre-flight and verification gates defined here.

## 1. Purpose and authority

This document decomposes the M1 deliverable into coherent implementation/review steps.

It does **not** introduce new domain, persistence, concurrency or API semantics. Those are already authoritative in:

```text
docs/milestones/M1/contract.md
docs/milestones/M1/architecture/README.md
and the normative architecture documents indexed there
```

Project-wide implementation technology is governed by:

```text
docs/general/technology_baseline.md
```

Only explicitly ratified STACK decisions may be used. If an M1 step discovers a real need for an unratified technology choice, the technology decision is resolved and consolidated before that dependency is introduced.

The expected traceability is:

```text
M1 acceptance criterion / invariant
    -> frozen architecture contract
    -> implementation step
    -> implementation mechanism
    -> deterministic verification
```

## 2. Global implementation rules

The following rules apply to every step.

### 2.1 Mandatory pre-flight

Before starting a step, Codex/implementer must re-read the normative documents identified by that step and verify that no architecture reopening or documentation contradiction affects the work.

Conversation history, previous implementation and Git history are not architecture authority.

### 2.2 Vertical completion

Except for the explicit bootstrap/foundation steps, implementation should be vertical.

A capability is not complete merely because one layer exists. Where applicable, the step must leave coherent:

```text
domain semantics
application command/query boundary
semantic Unit of Work
PostgreSQL realization
public HTTP adapter
failure mapping
read/list projection
deterministic tests
```

A table, DTO or repository method alone is never considered delivery of a semantic operation.

### 2.3 No speculative abstractions

Implementation derives only what current M1 contracts require.

Do not introduce future plugin systems, generic repository frameworks, generic PATCH/update models, alternate persistence backends, job/queue infrastructure, CLI frameworks, observability frameworks or compatibility layers for the removed historical implementation.

### 2.4 PostgreSQL correctness

Any guarantee attributed to PostgreSQL, transactions, locks, FK/PK/UNIQUE arbitration, MVCC or advisory gates is verified against real PostgreSQL through externally supplied test configuration.

No SQLite/fake database substitute may certify such behavior.

### 2.5 Concurrency implementation discipline

The 51 canonical PGTEST scenario IDs in `concurrency-postgresql-test-matrix.md` are stable verification authorities.

Scenarios are implemented progressively when all capabilities needed by the race exist. A scenario spanning two later slices is not duplicated prematurely with a fake operand. The final M1 gate requires the complete canonical census.

`sleep()` is never a correctness orchestration primitive.

### 2.6 Quality gate per step

Every step runs the smallest verification set that proves its contracts, including as applicable:

```text
Ruff format/lint
Pyright strict
unit/domain tests
Hypothesis properties
real-PostgreSQL integration tests
migration/schema tests
API contract tests
deterministic PG concurrency scenarios
```

No generic flaky-test rerun is accepted as correctness treatment.

### 2.7 Documentation changes during implementation

Implementation may update operational decomposition/status documentation, test traceability and implementation notes where appropriate.

If coding reveals a genuine semantic/technical contradiction in frozen architecture, the affected implementation stops. The architecture is explicitly reopened, revalidated, realigned and frozen again before implementation continues.

## 3. Step map

```text
M1-S00  Clean-slate project bootstrap and quality/test runtime
M1-S01  PostgreSQL schema, migration, UoW and deterministic-test foundation
M1-S02  PrimitiveType and DataType vertical slice
M1-S03  ObjectTemplate and active model graph vertical slice
M1-S04  Object intrinsic state and intrinsic lifecycle vertical slice
M1-S05  Ownership and Object schema-change vertical slice
M1-S06  RelationshipDefinition model-plane and capability vertical slice
M1-S07  Runtime Relationship and relationship lifecycle vertical slice
M1-S08  Cross-domain integrity, destructive-operation and API/read closure
M1-S09  Full M1 acceptance, regression and delivery gate
```

The order is intentional. Later steps may depend on earlier public/application contracts, but earlier layers must not invent weaker placeholder semantics merely to make a later step easier.

---

## M1-S00 — Clean-slate project bootstrap and quality/test runtime

### Objective

Create the new implementation environment from the ratified technology baseline without introducing kernel domain behavior.

### Normative authorities

```text
docs/general/technology_baseline.md
    STACK-01..STACK-09 as ratified

docs/general/linee_guida_progetto.md
AGENTS.md
```

### Deliverables

Create the minimal clean project structure required for later steps, including:

- CPython 3.14 project metadata (`>=3.14,<3.15`) and local runtime pin;
- `uv` project/dependency workflow and committed `uv.lock`;
- Hatchling build backend and `src/` layout;
- minimal `netauto` package structure with explicit layer boundaries;
- Ruff formatter/linter configuration;
- Pyright strict configuration for `src` and `tests`;
- pytest, pytest-asyncio, Hypothesis, coverage and timeout/xdist testing dependencies required by STACK-07;
- FastAPI/Uvicorn dependencies and an explicit application factory/composition entrypoint;
- `pydantic-settings` process-settings bootstrap with only settings actually consumed at this stage;
- centralized stdlib logging bootstrap;
- lightweight request-id infrastructure only if needed by the initial HTTP composition;
- Alembic project skeleton, without inventing schema beyond the frozen persistence contract;
- test configuration boundary for externally supplied `TEST_DATABASE_URL`;
- explicit separation between runtime database configuration and test database configuration.

There is no custom M1 CLI and no Typer dependency.

### Required verification

At minimum:

- `uv sync --locked` succeeds from the clean repository;
- Ruff format/check passes;
- Pyright strict passes on the new skeleton;
- pure pytest smoke suite runs without PostgreSQL;
- PostgreSQL-required test selection fails clearly when explicitly requested without required DB configuration and never falls back to another backend;
- application factory can be constructed under valid process settings without import-time composition side effects;
- no migration is run automatically by application startup/lifespan.

### Exit criteria

The repository has a reproducible, strictly checked environment suitable for kernel implementation, but exposes no invented M1 domain behavior.

Primary acceptance support: `AC-09`, foundation for all other ACs.

---

## M1-S01 — PostgreSQL schema, migration, UoW and deterministic-test foundation

### Objective

Realize the frozen PostgreSQL physical authority and the minimum transaction/test substrate needed by all subsequent vertical slices.

This is an explicit foundation step: physical structures may exist before every semantic operation that will eventually use them. Their presence does not make those future capabilities implemented.

### Normative authorities

```text
persistence-model.md
persistence-uow-concurrency.md
concurrency-semantic-matrix.md
concurrency-postgresql-realization-matrix.md
concurrency-postgresql-realization-object-ownership.md
concurrency-postgresql-realization-relationship.md
concurrency-postgresql-test-matrix.md
```

### Deliverables

- SQLAlchemy Core `MetaData` representation of the complete frozen 13-table M1 authority map;
- all normative PK, UNIQUE, FK, CHECK, `NOT NULL`, delete actions and PERSIST-15 indexes;
- PostgreSQL-native UUID/timestamp/JSONB and closed-vocabulary representation required by PERSIST-01..15;
- one coherent Alembic head capable of constructing the frozen M1 schema from a clean PostgreSQL database (revision decomposition is implementation detail);
- async SQLAlchemy/Psycopg engine/connection composition;
- minimal semantic UoW transaction substrate: explicit async connection/transaction ownership, commit/rollback controlled by application operation rather than repository/session magic;
- no ORM `Session`/identity map/lazy loading;
- persistence helpers only where they express a concrete repeated boundary; no generic repository framework created speculatively;
- deterministic PostgreSQL test harness foundation implementing the PGTEST conceptual roles (`CTL`, `OBS`, optional `B`, `T1/T2/T3`), worker PID/application-name diagnostics and blocker observation support;
- reusable infrastructure for canonical barriers/recipes without production-only pause hooks.

### Required verification

- clean real PostgreSQL database -> `alembic upgrade head` succeeds;
- schema/constraint/index shape matches the frozen persistence model and authoritative SQLAlchemy metadata without unexplained drift;
- targeted raw persistence tests prove representative PK/UNIQUE/FK/CHECK enforcement and rollback behavior;
- UoW failure rollback leaves no partial committed state;
- independent test connections/transactions are demonstrably independent;
- PGTEST harness can deterministically prove a simple real PostgreSQL blocking relation through `pg_blocking_pids()` without sleep-based orchestration;
- Ruff/Pyright/ordinary tests remain green.

### Exit criteria

The complete physical authority exists and can be rebuilt from an empty PostgreSQL database. Subsequent steps may implement semantic operations against it without changing the frozen table/constraint meaning.

Primary acceptance support: `AC-01`, `AC-04`, `AC-06`, `AC-09`, `AC-10`.

---

## M1-S02 — PrimitiveType and DataType vertical slice

### Objective

Deliver the complete M1 `PrimitiveType` and `DataType` capability end to end.

### Normative authorities

```text
datatype.md
persistence-model.md
persistence-uow-concurrency.md
concurrency-* matrices relevant to DT/version/default/binding
api-contract.md
api-wire-contract.md
api-read-contract.md
api-list-contract.md
api-error-contract.md
```

### Deliverables

#### Primitive semantics

Implement the closed M1 primitive catalog and one authoritative parser/canonicalizer/validator path for:

```text
core.string
core.integer
core.number
core.boolean
core.date
core.datetime
core.ip
core.ip_prefix
core.byte_size
```

Implement the frozen constraint matrix, enum canonicalization/duplicate rules, Python `re.fullmatch` pattern semantics and the canonical persistence/API representations.

No JSON Schema compiler, projection or second validation language is introduced.

#### DataType semantics

Implement all DataType/DataTypeVersion application operations:

```text
CREATE
CREATE_NEXT
REVISE
PUBLISH
SET_DEFAULT
CLEAR_DEFAULT
DEPRECATE
DELETE_DRAFT
DELETE_LINEAGE
SET_DESCRIPTION
```

including version allocation, DRAFT revision freshness, first-publish auto-default, explicit/implicit pinning rules, lifecycle monotonicity and delete safety.

#### Persistence and UoW

Implement the exact DataType UoW/locking mechanisms from the frozen realization: lineage/version owners, `FOR NO KEY UPDATE`/`FOR UPDATE`/`FOR SHARE` distinctions, fresh post-lock validation and READ COMMITTED semantics.

#### Public API

Implement all DataType write/read/list routes under `/api/v1/core`, including:

- strict Pydantic request/response DTOs;
- omission-vs-null behavior;
- positive query `expected_revision` where required;
- lineage/exact-version projections;
- opaque keyset pagination and canonical ordering/filtering;
- concrete public error-code/status/success/`Location` mapping.

Shared cursor/error/transport utilities may be introduced here only to the extent required by the frozen API contracts and then reused by later slices.

### Required verification

- exhaustive example tests for frozen primitive edge cases;
- targeted Hypothesis properties for canonicalization/idempotence/round-trip/constraint domains;
- DataType domain/application tests for every mutation and failure family;
- real PostgreSQL persistence/UoW tests;
- API contract tests for all DataType routes, strict wire behavior, statuses and failure mapping;
- deterministic PGTEST scenarios applicable once DataType exists, including the DataType side of shared version/default scenarios (`ROW-01..08` as applicable), `ROW-15`, `ROW-16`, `ARB-01`, and relevant `PAR-06/PAR-07` probes;
- cross-domain active-consumer scenarios that require ObjectTemplate are explicitly completed in M1-S03 rather than simulated here.

### Exit criteria

DataType is a complete usable vertical capability. A caller can define, version, publish, select, deprecate, read/list and delete allowed DataType state through the public API with canonical primitive semantics and PostgreSQL-backed concurrency correctness.

Primary acceptance support: `AC-02`, `AC-04`, `AC-05`, `AC-06`, `AC-07`, `AC-08`.

---

## M1-S03 — ObjectTemplate and active model graph vertical slice

### Objective

Deliver ObjectTemplate versioning, inheritance, properties/components, effective schema and active model graph semantics end to end, using the DataType capability from M1-S02.

### Normative authorities

```text
objecttemplate.md
objecttemplate-lifecycle.md
objecttemplate-properties.md
objecttemplate-components.md
objecttemplate-effective-schema.md
datatype.md
persistence/concurrency authorities
API-03 companion contracts
```

### Deliverables

Implement:

- stable ObjectTemplate lineage identity/naming/abstract/parent-lineage semantics;
- exact parent-version pinning and acyclic inheritance;
- CREATE / CREATE_NEXT / REVISE / PUBLISH / SET_DEFAULT / CLEAR_DEFAULT / DEPRECATE / DELETE_DRAFT / DELETE_LINEAGE / SET_DESCRIPTION;
- property declaration semantics: exact DTV binding, `SCALAR`/`LIST`, `required`, `migration_default`, position and historical/evolution rules;
- component slot declaration semantics, target lineage compatibility/evolution and shared effective member namespace;
- derived effective schema from exact parent chain + local declarations;
- DRAFT well-formedness and publication certification;
- direct active model graph lifecycle guarantees and reverse-consumer admission/deprecation checks;
- no authoritative effective-schema cache and no JSON Schema representation.

Implement all ObjectTemplate public routes except `relationship-capabilities`, which becomes semantically complete in M1-S06 when certified RelationshipDefinitions exist. The route must not be filled with a fake placeholder representation.

### Required verification

- inheritance/effective-schema domain tests, including cycle and namespace/member collision failures;
- property/component evolution and migration-default tests;
- explicit/implicit DTV binding tests with canonical primitive values;
- real PostgreSQL aggregate atomicity and reference tests;
- API tests for all implemented OT writes, lineage/exact/effective-schema reads and lists;
- deterministic concurrency scenarios covering shared DT/OT version mechanics plus active graph, including `ROW-01..10`, `ROW-16`, `ARB-01`, `ATOMIC-01`, relevant `REF-01`, `PAR-06/PAR-07` and any equivalent variants required by the canonical matrix;
- specifically prove `OTV PUBLISH consumer × DTV DEPRECATE` cannot commit an active edge to a deprecated dependency.

### Exit criteria

ObjectTemplate is a complete model-plane schema capability, with lifecycle-certified direct dependencies and deterministic effective schema. DataType/ObjectTemplate cross-domain correctness is fully active.

Primary acceptance support: `AC-02`, `AC-03`, `AC-04`, `AC-05`, `AC-06`, `AC-07`, `AC-08`.

---

## M1-S04 — Object intrinsic state and intrinsic lifecycle vertical slice

### Objective

Deliver runtime Object identity, canonical intrinsic state and intrinsic lifecycle events on top of published ObjectTemplate schemas.

Object ownership and schema migration are intentionally deferred to M1-S05 because their correctness contracts are coupled.

### Normative authorities

```text
object.md
object-runtime-state.md
object-lifecycle-changelog.md
objecttemplate-effective-schema.md
persistence/UoW/concurrency authorities
API-03 companion contracts
```

### Deliverables

Implement:

- kernel-generated immutable Object identity;
- stable `template_id` and exact current OTV pin;
- Object CREATE with explicit/implicit OTV selection, concrete/published target admission and caller-properties validation;
- canonical runtime property state using the same primitive semantic path as DataType constraints/defaults;
- canonical zero-cardinality and no-null rules;
- RENAME;
- DATA_CHANGE with non-empty `SET|REMOVE` operation set, one operation per property, current-state rederivation and semantic no-op behavior;
- intrinsic lifecycle event production and atomic state/event commit;
- Object intrinsic GET and Object collection list/filter/pagination contracts;
- lifecycle read machinery sufficient to expose intrinsic events through the canonical event DTO family without inventing future structural event types.

`SCHEMA_CHANGE`, `ATTACH`, `DETACH` and final `Object.DELETE` are not considered delivered in this step.

### Required verification

- Object create/runtime-state domain tests against exact effective schemas;
- primitive canonicalization reuse tests (no parallel parser semantics);
- DATA_CHANGE no-op and invalid-candidate tests;
- lifecycle intrinsic event shape/atomicity tests;
- real PostgreSQL target-OTV admission and exact-FK tests;
- API tests for CREATE/RENAME/DATA_CHANGE, intrinsic GET and Object collection behavior;
- deterministic scenarios available at this stage, including `ROW-11`, `ATOMIC-04A` and the Object exact-OTV variant of `REF-01`;
- races requiring schema-change or Relationship state are completed only when those operations exist.

### Exit criteria

An Object can be created, read, renamed and semantically data-mutated with exact schema validity, canonical persistence and atomic intrinsic lifecycle history.

Primary acceptance support: `AC-02`, `AC-03`, `AC-04`, `AC-05`, `AC-06`, `AC-07`, `AC-08`.

---

## M1-S05 — Ownership and Object schema-change vertical slice

### Objective

Deliver component ownership and forward intra-lineage Object schema migration as one coupled vertical slice.

They are grouped because schema-change validity depends on preservation/validation of outgoing ownership slots, and the frozen concurrency architecture shares the parent Object as the relevant owner.

### Normative authorities

```text
object-schema-change.md
object-ownership.md
object-lifecycle-changelog.md
objecttemplate-components.md
objecttemplate-effective-schema.md
concurrency-postgresql-realization-object-ownership.md
persistence/UoW baseline
API-03 companion contracts
```

### Deliverables

Implement:

- Object `ATTACH` / `DETACH` semantic operations;
- single-owner authority, slot semantic-key interpretation, lineage-polymorphic child compatibility and exact no-op semantics;
- ownership acyclicity with the frozen transaction advisory graph gate;
- required post-gate fresh-statement re-read discipline;
- Object `SCHEMA_CHANGE` only forward within the stable template lineage;
- definitive exact source/target schema closures;
- property carry-forward by semantic identity, migration-default fill-on-absence only and target-incompatible-value rejection;
- preservation/validation of existing attachments by slot semantic continuity;
- no implicit detach/remediation/downgrade;
- parent-owner lock semantics for ATTACH/DETACH/SCHEMA_CHANGE;
- structural ownership lifecycle event sets with the frozen historical display metadata semantics;
- Object components and owner read/list projections;
- public API routes/status/error behavior for `SCHEMA_CHANGE`, `ATTACH`, `DETACH`.

### Required verification

- ownership semantic/domain tests including polymorphism, single-owner conflicts, no-op attach/detach and cycle rejection;
- schema migration property/slot continuity tests;
- real PostgreSQL ownership FK/PK and rollback tests;
- lifecycle structural-event atomicity and display-metadata tests;
- API tests for schema-change, attach/detach, components and owner projections;
- deterministic canonical scenarios including `ROW-12..14`, `ARB-02..04`, ownership variants of `REF-02`/`REF-05`, `GATE-01..03`, `SNAP-04`, `ATOMIC-04B`, `PAR-03` and `PAR-04`;
- gate fresh-snapshot scenarios must prove the read occurs in a statement subsequent to advisory-gate acquisition.

### Exit criteria

Objects can evolve schema and participate in strongly consistent acyclic single-owner composition without losing information, silently detaching state or violating current parent schema.

Primary acceptance support: `AC-02`, `AC-03`, `AC-04`, `AC-05`, `AC-06`, `AC-07`, `AC-08`.

---

## M1-S06 — RelationshipDefinition model-plane and capability vertical slice

### Objective

Deliver the certified Relationship model-plane: complete RelationshipDefinition aggregates, resolved semantic perspectives, global conflict freedom and ObjectTemplate capability reads.

### Normative authorities

```text
relationship.md
relationship-definition.md
relationship-resolution.md
relationship-concurrency.md
concurrency-postgresql-realization-relationship.md
objecttemplate lifecycle/inheritance authorities
persistence/UoW baseline
API-03 companion contracts
```

### Deliverables

Implement:

- RelationshipDefinition CREATE for symmetric and non-symmetric forms;
- kernel-generated stable Definition/Resolution identities;
- complete deterministic Resolution-set derivation;
- semantic equivalence rejection and cross-definition conflict detection over lineage-overlap spaces;
- global RelationshipDefinition transaction advisory conflict gate;
- mandatory fresh certified-set read in a statement after gate acquisition;
- complete aggregate RENAME and DELETE semantics;
- model-plane lineage references and FK lifetime safety;
- RelationshipDefinition GET/list DTOs;
- ObjectTemplate `relationship-capabilities` semantic projection/list using certified Resolutions;
- no autonomous public RelationshipResolution CRUD.

DELETE is implemented against current persistence authority here and receives additional factual-reference regression coverage once runtime Relationship exists in M1-S07.

### Required verification

- symmetric/non-symmetric aggregate-shape tests;
- equivalence/conflict/lineage-overlap tests;
- capability inheritance/deduplication tests;
- real PostgreSQL aggregate/reference tests;
- API tests for Definition create/rename/delete/get/list and OT capability reads;
- deterministic scenarios including `ROW-17`, RD/OT-lineage `REF-01`, `GATE-04..06` and `ATOMIC-04C`;
- fresh-snapshot `GATE-06A` protection must fail if gate acquisition and authoritative certified-set read are accidentally collapsed into one stale-snapshot statement.

### Exit criteria

The Relationship model-plane is a globally conflict-free certified set of complete Definitions/Resolutions and can expose semantic capabilities to ObjectTemplate lineages.

Primary acceptance support: `AC-02`, `AC-03`, `AC-04`, `AC-05`, `AC-06`, `AC-07`, `AC-08`.

---

## M1-S07 — Runtime Relationship and relationship lifecycle vertical slice

### Objective

Deliver factual runtime Relationships, exact-view convergence, Object-relative relationship navigation and complete Relationship lifecycle event semantics.

### Normative authorities

```text
relationship.md
relationship-runtime.md
relationship-concurrency.md
relationship-resolution.md
object-lifecycle-changelog.md
concurrency-postgresql-realization-relationship.md
persistence/UoW baseline
API-03 companion contracts
```

### Deliverables

Implement:

- Relationship CREATE from exact `resolution_id + from_object_id + to_object_id`;
- lineage-polymorphic endpoint admission using stable Object template lineage;
- symmetric/non-symmetric role semantics and allowed self-loops;
- deterministic complete runtime-resolution closure;
- exact resolved-view PK arbitration;
- whole-UoW rollback and fresh-UoW convergence after concurrent equivalent CREATE collision;
- exact Relationship-id DELETE with idempotent absence and ABA-safe behavior;
- factual Relationship GET semantic aggregate projection;
- Object-relative relationship projection with semantic deduplication;
- Relationship create/delete lifecycle semantic-view event sets;
- one-statement coherent display-metadata observation required by lifecycle semantics;
- Definition/Object FK lifetime interactions and strengthened RD.DELETE safety.

### Required verification

- runtime closure/admission/symmetry/self-loop/idempotency domain tests;
- exact-view uniqueness/convergence and rollback persistence tests;
- Relationship/Object-relative read DTO tests;
- lifecycle semantic-view cardinality and atomicity tests;
- API tests for Relationship CREATE/GET/DELETE and Object relationship reads, including `201` new vs `200` convergence and `204` absent delete;
- deterministic canonical scenarios including `ARB-05..07`, `REF-03`, `REF-04`, relationship variant of `REF-05`, `SNAP-01..03`, `ATOMIC-02`, `ATOMIC-03`, `PAR-01`, `PAR-02` and `PAR-05`;
- lifecycle metadata snapshot tests must validate allowed committed snapshot combinations rather than requiring unrelated row locks.

### Exit criteria

Factual Relationships are complete, convergent, referentially safe and observable through semantic rather than raw persistence views, with lifecycle history committed atomically.

Primary acceptance support: `AC-02`, `AC-03`, `AC-04`, `AC-05`, `AC-06`, `AC-07`, `AC-08`.

---

## M1-S08 — Cross-domain integrity, destructive-operation and API/read closure

### Objective

Close the remaining behavior whose correctness can only be proven once all four M1 domains exist simultaneously.

This is not a feature-expansion step. It completes already-frozen cross-domain contracts and destructive-operation safety.

### Normative authorities

```text
M1 contract AC-01..AC-10
all four domain architecture indexes
persistence-model.md / persistence-uow-concurrency.md
concurrency semantic/realization/test matrices
api-contract.md + API-03 companion contracts
m1-final-consistency-review.md
```

### Deliverables

- final `Object.DELETE` implementation with zero incoming/outgoing ownership and zero current factual Relationship association, no subtree/cascade semantics;
- full cross-domain whole-lineage/delete-reference behavior for DataType and ObjectTemplate against every current external M1 reference shape;
- full RelationshipDefinition delete/reference behavior against factual Relationships;
- ensure declarative `RESTRICT` remains the final race authority for cross-aggregate lifetime;
- complete global lifecycle-event read route and Object-specific lifecycle semantics (`object_id = X OR destination_object_id = X`);
- complete lifecycle filters, ordering and PERSIST-15 read-path index use;
- close any list/read route intentionally deferred until its producer domain existed;
- audit all API-03 request/response/error mapping against the finite M1 catalog;
- verify all 32 mutation routes exist exactly once and forbidden generic/child mutation surfaces do not exist;
- verify no persistence row or SQL/constraint detail leaks into public DTO/error representation;
- reinforce earlier delete operations with regression tests for reference types introduced by later steps.

### Required verification

- cross-domain deletion/reference matrix tests;
- `REF-01..06` complete variants, especially `REF-06` aggregate-CASCADE vs external-RESTRICT;
- Object DELETE races against ATTACH/DETACH/Relationship CREATE/DELETE as prescribed by the canonical PGTEST authorities;
- global/Object lifecycle list/filter/pagination API tests;
- complete API route inventory and negative-surface tests;
- complete error-code/status/detail conformance tests;
- OpenAPI smoke review for public M1 routes/DTOs without treating OpenAPI as semantic authority;
- all earlier slice regression suites remain green.

### Exit criteria

No M1 domain can be made invalid by deleting or mutating another domain through any supported operation, and the complete public read/write/error surface matches the frozen API contract.

Primary acceptance support: `AC-02`, `AC-03`, `AC-04`, `AC-05`, `AC-06`, `AC-07`, `AC-08`.

---

## M1-S09 — Full M1 acceptance, regression and delivery gate

### Objective

Demonstrate that the integrated clean-slate implementation satisfies the complete frozen M1 contract and is ready to become the M1 deliverable.

No new capability is introduced in this step.

### Normative authorities

```text
docs/milestones/M1/contract.md
docs/milestones/M1/architecture/README.md
m1-final-consistency-review.md
concurrency-postgresql-test-matrix.md
api-* contracts
docs/general/technology_baseline.md
this steps.md once frozen
```

### Required verification gate

#### Static/reproducibility

- clean CPython 3.14 environment can be reproduced from committed project metadata and `uv.lock`;
- `uv sync --locked` succeeds;
- Ruff formatting/linting passes;
- Pyright strict passes on `src` and `tests`;
- no obsolete historical dependencies/frameworks have re-entered the environment.

#### Database/migrations

- externally supplied dedicated real PostgreSQL test target is required for DB suites;
- empty/clean DB -> Alembic head succeeds;
- authoritative SQLAlchemy metadata and migrated schema show no unexplained drift;
- PostgreSQL remains the only supported runtime persistence backend;
- application startup does not run migrations implicitly.

#### Test layers

Run/close the complete STACK-07 test model:

```text
T0 pure domain
T1 application/orchestration
T2 real-PG persistence
T3 deterministic real-PG concurrency
T4 API contract/integration
T5 migration/schema
T6 targeted Hypothesis properties
```

T7 randomized/stress concurrency may run as supplementary evidence but is not a substitute for T3.

#### PGTEST closure

All canonical PGTEST IDs must be implemented and passing:

```text
44 correctness scenarios
+ 7 T-PAR probes
= 51 canonical scenario IDs
```

All 19 non-`I` safety predicates remain traceable to their canonical scenario coverage. Required mechanism assertions (row locking, FK/PK/UNIQUE arbitration, advisory-gate visibility/fresh snapshot, intentional blocking/non-blocking) are verified, not only final functional outcomes.

#### API closure

- all canonical 32 mutation routes and all frozen read/list routes are present;
- strict input, omission/null, PrimitiveType lexical forms and `expected_revision` behavior match API-03;
- success status/body/`Location` policy matches API-03.11B;
- complete finite public error catalog maps to the correct failure class/status/details;
- forbidden generic PATCH/PUT and autonomous child-resource mutation surfaces are absent;
- no JSON Schema compiler/projection endpoint exists.

#### Acceptance-criterion closure

Produce/verify an explicit traceability check for:

```text
AC-01 PostgreSQL authority
AC-02 valid domain states
AC-03 cross-domain consistency
AC-04 transactional atomicity
AC-05 concurrent correctness
AC-06 persistence enforcement
AC-07 API semantics
AC-08 verification/invariant traceability
AC-09 runtime/test DB separation
AC-10 no alternative-backend burden
```

Any uncovered acceptance criterion blocks M1 completion.

### Delivery/doc closure

- update root README with actual reproducible bootstrap/run/test commands now that they exist;
- create/update `docs/milestones/M1/status.md` with final operational state and completed step registry;
- ensure frozen architecture has not drifted to describe implementation accidents;
- record any intentionally deferred RFE only in the appropriate existing architecture/RFE authority, never by expanding M1 scope;
- perform a final documentation consistency sweep for stale TODO/open markers introduced during implementation.

### Exit criteria

M1 is complete only when the full acceptance and regression gate passes on the integrated repository and documentation remains coherent with the frozen contract/architecture.

At that point `status.md` may mark M1 delivered. Any semantic architecture change required to make the gate pass must follow the explicit reopen/re-freeze process; the test gate may not be weakened to fit the implementation.

Primary acceptance support: `AC-01..AC-10`.

---

## 4. Cross-step PGTEST allocation rule

The scenario references above are implementation-planning guidance, not a replacement for the canonical PGTEST matrix.

The authoritative requirement is always the complete mapping in `concurrency-postgresql-test-matrix.md`.

If a scenario's two operations become available in different steps:

```text
first operation implemented
    -> test its local/unit/persistence contract

both operations implemented
    -> add the canonical concurrency scenario immediately

M1-S09
    -> verify complete 51-ID census and 19-predicate coverage
```

Do not create a fake implementation of the missing operation merely to claim early scenario coverage.

## 5. Step completion and sequencing rule

Steps are intended to execute in order unless an explicit review determines that two implementation activities are independent **and** reordering cannot alter a frozen dependency or verification gate.

A step is complete only when:

1. its required implementation exists;
2. all applicable verification passes;
3. no known architecture contradiction remains;
4. later-step placeholders have not been used to mask incomplete semantics;
5. the repository remains runnable/testable at that checkpoint.

The next step starts only from a coherent repository state.

## 6. Freeze rule for this document

This `steps.md` is **FINAL / FROZEN**.

The prerequisites for implementation are satisfied:

- the M1 contract is `FINAL / FROZEN`;
- the M1 architecture is globally `FROZEN`;
- the decomposition has been reviewed and explicitly ratified;
- every technology choice required by `M1-S00` is explicitly ratified in `technology_baseline.md` (`STACK-01..STACK-09`);
- `docs/milestones/M1/status.md` identifies `M1-S00` as the current operational step.

Implementation may therefore begin with `M1-S00`.

After freeze, changing step boundaries or verification decomposition is allowed only when it does not reinterpret scope or frozen semantics. A genuine semantic/technical gap still follows the architecture reopening and re-freeze process before affected implementation continues.
