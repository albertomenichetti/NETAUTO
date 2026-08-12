# Roadmap

## Current Milestone State

```text
M1 — Functional Core                     COMPLETE

M2 — Hardening current model             COMPLETE
     relational integrity
     lifecycle hardening
     model-plane serialization
     data-plane concurrency characterization
     Object optimistic concurrency
     ownership graph coordination
     fail-closed concurrency composition

M2.5 — PostgreSQL Transactional Foundation
                                         NEXT
     authoritative SQL backend transition
     Alembic introduction
     PostgreSQL repository parity
     PostgreSQL concurrency characterization
     cross-plane binding inventory and protocol
     SQLite removal

M3 — Real-world dogfooding               BLOCKED BY M2.5

M4 — Candidate Data-Model Freeze         FUTURE

M5 — Integrity Verifier                  FUTURE / AFTER FREEZE

M6 — Full destructive/adversarial certification
                                         FUTURE

M7 — Expansion / further platform evolution
                                         FUTURE
```

## Sequencing Realignment

The previously accepted order was:

```text
dogfooding
-> model evolution
-> candidate model freeze
-> integrity verifier
-> destructive certification
-> Alembic/PostgreSQL
```

That sequencing has now been superseded.

Recent concurrency analysis identified cross-plane transactional invariants
that cannot be characterized or certified adequately on the current SQLite
backend. SQLite's physical single-writer behavior can hide races that the
intended architecture treats as logically independent. As a result, the
project no longer treats PostgreSQL and Alembic as late backend-port work.

The current accepted order is:

```text
PostgreSQL transactional foundation
-> PostgreSQL concurrency hardening
-> M3 real-world dogfooding
-> model evolution through migrations
-> candidate freeze
-> integrity verifier
-> full destructive/adversarial certification
-> expansion
```

M3 is therefore blocked until M2.5 closes.

## M2.5 — PostgreSQL Transactional Foundation

M2.5 is a transition-and-hardening milestone. It changes the accepted
persistence direction of the project before any dogfooding work resumes.

Current implementation fact:

- PostgreSQL connectivity, engine support, and real integration-test
  infrastructure are implemented
- PostgreSQL is the default runtime backend
- PostgreSQL is authoritative for integration and concurrency validation
- Alembic baseline is implemented and certifies empty-schema PostgreSQL upgrade
  to the current ORM schema
- DataType repository parity on PostgreSQL is complete
- ObjectTemplate repository parity on PostgreSQL is complete
- Object, ObjectChange, and ComponentMembership repository parity on
  PostgreSQL are complete
- RelationshipDefinition and runtime Relationship repository parity on
  PostgreSQL are complete
- PostgreSQL repository parity across current DataType/ObjectTemplate/Object/
  ObjectChange/ComponentMembership/RelationshipDefinition/Relationship
  persistence is complete
- PostgreSQL `MODEL_PLANE_GUARD` is implemented with a transaction-scoped
  advisory lock
- PostgreSQL `OWNERSHIP_GRAPH_GUARD` is implemented with a distinct
  transaction-scoped advisory lock
- application composition can now run on PostgreSQL via `DATABASE_URL`
- PostgreSQL guard UoWs are wired into the real FastAPI composition
- API, application, and CLI acceptance baselines now run on PostgreSQL
- PostgreSQL tests are not opt-in
- SQLite remains transitional explicit compatibility only until M2.5.12

Accepted direction:

- PostgreSQL becomes the authoritative and only intended supported SQL backend
- SQLite is deprecated transitional code and scheduled for removal
- Alembic moves before dogfooding and becomes the authoritative schema
  evolution mechanism
- M3 dogfooding resumes only after the transactional foundation is real

### M2.5.0 — Documentation realignment

- docs only
- new PostgreSQL-authoritative ADR
- roadmap/architecture/ADR reconciliation
- no implementation

### M2.5.1 — PostgreSQL dependency and configuration

- PostgreSQL driver
- `DATABASE_URL` / configuration
- general engine construction
- no backend switch yet
- no Alembic

### M2.5.2 — PostgreSQL integration-test harness

- reproducible PostgreSQL test instance/lifecycle
- database/schema setup fixture
- one connection/smoke test
- no application migration yet

### M2.5.3 — Current ORM schema compatibility

- create current SQLAlchemy schema on PostgreSQL
- verify PK/FK/unique/check/index behavior
- no Alembic yet
- no new domain semantics

### M2.5.4 — Alembic baseline

- introduce Alembic
- baseline current PostgreSQL schema
- upgrade from empty DB to head
- no SQLite data migration
- no attempt at long historical migration compatibility

### M2.5.5 — Model-plane repository parity

- DataType repositories
- ObjectTemplate repositories
- PostgreSQL integration coverage
- no new concurrency behavior
- complete

### M2.5.6 — Object-plane repository parity

- Object
- ObjectChange
- ComponentMembership
- PostgreSQL integration coverage
- no new concurrency semantics
- complete

### M2.5.7 — Relationship repository parity

- RelationshipDefinition
- runtime Relationship
- PostgreSQL integration coverage
- complete

### M2.5.8 — PostgreSQL MODEL_PLANE_GUARD

- implement only global model-writer serialization
- transaction scoped
- before first decision read
- prove model-writer vs model-writer serialization
- do not add cross-plane binding guard yet
- complete

### M2.5.9 — PostgreSQL OWNERSHIP_GRAPH_GUARD

- implement only ownership-topology coordination
- prove ownership-vs-ownership serialization
- preserve logical independence from `MODEL_PLANE_GUARD`
- complete

### M2.5.10 — PostgreSQL application composition

- wire application/FastAPI/UoWs to PostgreSQL
- real API smoke coverage
- SQLite not removed yet
- complete

### M2.5.11 — PostgreSQL becomes authoritative runtime/test backend

- main integration validation uses PostgreSQL
- development/runtime default becomes PostgreSQL
- SQLite no longer defines authoritative concurrency behavior
- complete

### M2.5.12 — SQLite removal

- remove SQLite engine helpers
- remove SQLite-specific UoWs
- remove `SQLITE_BUSY` retry behavior
- remove SQLite-specific tests/docs/configuration
- no supported dual-backend contract remains

### M2.5.13 — Cross-plane binding inventory

Documentation/analysis milestone only. No fixes yet.

Inventory every data-plane workflow that creates or changes a persistent or
semantically stable dependency on model-plane state.

For each case, classify:

- model resource depended upon
- identity vs exact-version dependency
- admission predicate
- whether predicate is mutable
- whether binding remains valid after predicate later becomes false
- physical FK/constraint coverage
- competing model-plane mutation
- stale decision-read risk
- required transactional property

Expected starting cases include:

- Object create with explicit `ObjectTemplateVersion`
- Object create with omitted version / highest `PUBLISHED` resolution
- Object migration target version
- runtime Relationship creation vs RelationshipDefinition lifecycle/delete
- model deletes vs new data-plane references
- component/ownership workflows where model state participates in compatibility

### M2.5.14 — PostgreSQL concurrency primitive characterization

- experimental/integration characterization only
- advisory locks
- row lock modes
- lock compatibility
- set/predicate races
- transaction isolation
- `SERIALIZABLE` behavior where relevant
- deadlock behavior
- no broad production concurrency redesign yet

### M2.5.15 — Cross-plane binding concurrency ADR

- formalize general protocol based on M2.5.13 + M2.5.14
- define resource/admission semantics
- define lock acquisition ordering
- define failure semantics
- define what belongs to FK vs transactional admission guard
- still avoid unrelated implementation

### M2.5.16 — Object create, explicit exact-version pin

- protect only create `Object(T, vN)`
- admission must be linearizable against model-plane invalidation of `vN`
- real PostgreSQL concurrent tests

### M2.5.17 — Object create, implicit version resolution

- protect create `Object(T)` using highest `PUBLISHED` resolution
- address concurrent publish/deprecate/version-set changes
- keep separate from explicit pin because this is a set/predicate problem

### M2.5.18 — Object migration target binding

- protect only migration onto the target `ObjectTemplateVersion`
- target must satisfy admission semantics transactionally
- PostgreSQL concurrent tests

### M2.5.19 — Runtime RelationshipDefinition binding

- characterize/fix runtime Relationship creation vs concurrent definition delete
- preserve semantic errors plus physical FK integrity

### M2.5.20 — ObjectTemplate destructive cross-plane races

- model-plane ObjectTemplate deletion vs creation of new runtime bindings
- make decision-read/mutation protocol safe
- scope only to identified ObjectTemplate destructive races

### M2.5.21 — Cross-plane concurrency certification

- execute final known race matrix with real PostgreSQL transactions
- verify intended linearizable/serializable outcomes
- verify lock ordering
- verify no unmanaged deadlock cases in supported workflows
- no new domain feature work

### M2.5.22 — M2.5 closeout

- documentation reconciliation against actual final implementation
- architecture/ADR/roadmap cleanup
- confirm SQLite is absent from supported runtime
- M3 becomes `NEXT` only after this milestone closes

## M3 — Real-World Dogfooding

M3 is no longer the immediate next milestone. It resumes only after M2.5 has
implemented and certified the PostgreSQL transactional foundation.

Once unblocked, the next step is not speculative feature growth in the
abstract. It is using the platform to model a real NETAUTO domain and
learning where the current model is strong, awkward, or insufficient.

The likely first dogfood domain is:

- `Site`
- `Device`
- `Interface`
- `VLAN`
- `IP Address`

Dogfooding findings should be classified as:

- `A. model cannot express the case`
- `B. model can express it but unnaturally`
- `C. model is adequate but application/API/CLI ergonomics are poor`

This distinction matters. A model gap, an awkward modeling pattern, and an
ergonomic issue should not be treated as the same kind of future work.

## M4 — Candidate Data-Model Freeze

After real dogfooding and resulting model evolution, the project can define a
candidate freeze for the structural model and its invariants.

That freeze is the prerequisite for later integrity-verifier and adversarial
hardening work.

## M5 — Integrity Verifier

The integrity verifier remains intentionally sequenced after the candidate
freeze. It should verify the model that the project actually intends to
stabilize, rather than a still-moving target.

## M6 — Full Destructive / Adversarial Certification

Destructive and adversarial persistence certification remains sequenced after
freeze and verifier work.

## M7 — Expansion

Further platform expansion remains future work guided by dogfooding and the
actual needs discovered there.

Speculative ideas such as component cardinality, relationship cardinality,
natural keys, tags, relationship attributes, ordered components, or bulk
operations are not committed roadmap items today. They remain possible
discoveries, not current promises.
