# M1 Architecture — Coding Baseline Index

**Status:** DRAFT architecture baseline — domain semantics and PostgreSQL persistence/concurrency/test architecture are substantially closed; remaining pre-freeze work is explicitly tracked below.

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
    route/DTO/failure contract as API-01+ are ratified.
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
- API/application boundary: command/query contracts authoritative, HTTP/JSON adapter, operation-specific command DTO, no generic PATCH, transport-neutral failure boundary (API-01).

The PostgreSQL concurrency/test architecture is therefore considered closed for M1. A PGTEST-05 is not planned merely to design fixtures, helper classes or test-file structure: those are implementation-decomposition concerns as long as they preserve PGTEST-01..04. Reopen the PGTEST architecture only for a genuine architecture-level gap or retroactive finding.

Reopening any closed area requires an explicit architecture change, not a local implementation optimization.

## 4. Remaining pre-coding/final-freeze work

Only explicitly documented open areas remain candidates for design work. At the current checkpoint these include primarily:

```text
API-02+ route inventory / DTO and wire shapes
public error/status taxonomy
remaining API wire-format decisions where distinct from canonical persistence
JSON Schema compiler surface/role if retained in M1
```

If later review discovers a new architecture gap, add it here and to the owning domain/cross-cutting document in the same documentation cycle.

## 5. Documentation alignment invariant

A cross-cutting decision is considered consolidated only after all documents that state the affected assumption are aligned.

For example a lock-strength change must update, as applicable:

```text
canonical realization index
persistence UoW baseline
Object/ownership or Relationship realization companion
owning domain concurrency/lifecycle document
PostgreSQL test matrix
```

Stale phrases such as “mechanism still to be finalized” must not remain when that mechanism has become normative elsewhere.

Architecture review before implementation must actively search for such stale-open markers.

If a new design point reveals a retroactive finding, the design sequence is interrupted: the finding is propagated immediately to every affected normative document before the next design point is ratified. Deferring propagation to a later sweep is not allowed when the affected baseline is already known.

## 6. Coding gate

Before creating implementation `steps.md` or coding M1 behavior, verify:

1. owning domain contract is frozen enough for the change;
2. persistence authority is identified;
3. every relevant non-`I` concurrency predicate maps to a REALIZE mechanism;
4. required real-PG scenario IDs, deterministic harness contract and execution recipe mapping exist;
5. application/API surface preserves the semantic operation boundary;
6. no architecture document states a contradictory or still-open version of the same decision.

If any item fails, return to architecture rather than deciding in code.
