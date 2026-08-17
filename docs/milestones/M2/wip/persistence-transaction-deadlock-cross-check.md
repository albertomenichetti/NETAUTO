# M2 Persistence Transaction and Deadlock Cross-Check

**Status:** PASS — ARCHITECTURE-LEVEL PROOF COMPLETE — IMPLEMENTATION EVIDENCE PENDING

**Authority:** REVIEW EVIDENCE — NON-NORMATIVE

## Review target

This report records the critical cross-check performed for:

```text
docs/milestones/M2/architecture/persistence.md
```

It compares the M2 persistence design with the delivered Unit-of-Work, isolation, lock-strength, FK lifetime, aggregate atomicity and deterministic-concurrency architecture.

The report is review evidence. Normative requirements are owned by the architecture documents.

## Inputs

```text
docs/architecture/persistence.md
docs/architecture/concurrency.md
docs/architecture/concurrency-matrix.md
docs/architecture/verification-concurrency-registry.md

docs/milestones/M2/contract.md
docs/milestones/M2/architecture/relationship.md
docs/milestones/M2/architecture/api.md

docs/milestones/M2/wip/relationship-properties-persistence.md
docs/milestones/M2/wip/relationship-properties-lifecycle.md
docs/milestones/M2/wip/relationship-properties-indexes.md
docs/milestones/M2/wip/relationship-properties-alembic-baseline.md

current application/store/UoW realization on branch M2
```

## Closure summary

```text
one-mutation / one-UoW correspondence        PASS
READ COMMITTED mutation compatibility        PASS
REPEATABLE READ coherent-read compatibility  PASS
current-state/event atomicity                 PASS
FK lifetime and CASCADE/RESTRICT validity     PASS
new exact-version/default references          PASS
fresh collision restart boundary              PASS
multi-resource deterministic ordering         PASS
advisory-gate wait graph                       PASS with gate-first discipline
row/FK wait graph                              PASS after normative hardening
unique-index wait graph                        PASS
root-delete cycle handling                     PASS
Alembic transactional posture                  PASS
architectural wait-for graph                   ACYCLIC
open persistence transaction points            0
```

## Material findings

A mechanical copy of every current physical implementation would not be accepted as the first durable M2 baseline.

Three deadlock classes were identified and closed by normative hardening.

### 1. Blind declaration replacement

A blind:

```text
delete all declaration children
then
reinsert the complete candidate
```

can create a parent-delete / child-reinsert wait cycle when a referenced target is concurrently deleted.

### 2. Existing-owner FK rebind

Locking a mutable child owner before its target can create:

```text
rebind
    holds child owner
    waits target delete

target delete
    holds target
    waits child owner during FK checking
```

This affects at least ObjectTemplate parent-version rebind/publication, Object SCHEMA_CHANGE and Relationship SCHEMA_CHANGE.

### 3. Concurrent model-root delete

Two model roots connected by reciprocal or mutually blocking FK references can each hold its own root while waiting on the other's owned child rows. Mutually targeting ObjectTemplate component declarations are the canonical example.

The semantic AS-IS remains valid. The first durable physical baseline therefore requires internal transaction hardening with no public contract change.

## Required hardening accepted by the review

```text
complete lock plan is built before current-state DML
any advisory gate is acquired before row locks
one operation acquires at most one advisory gate
MODEL_ROOT_DELETE_GATE serializes model-plane whole-root deletes
row intents are coalesced before acquisition; normal lock upgrade is forbidden
ObjectTemplate rows are ordered ancestor-before-descendant
row classes then follow the frozen persistence order
stable aggregate headers participate in exact-version mutations
existing-owner FK targets are acquired before the owner
inserted/reinserted child FK targets are acquired before child DML
complete declaration replacement uses differential physical DML
CREATE_NEXT cloned targets receive lifetime holds before insertion
Relationship CREATE holds endpoint Object lifetimes before closure insertion
RelationshipDefinition RENAME uses gate-first + header KEY SHARE
ownership edge addition uses gate-first row acquisition
closure and event rows use deterministic ordering
active-consumer reverse scans remain non-locking
stale optimistic lock plans restart the complete UoW
```

## Deadlock proof

The prescribed acquisition graph is:

```text
optional one advisory gate
-> complete canonical row-lock plan
-> fresh protected re-read
-> deterministic current-state DML
-> append-only event batch
-> commit
```

No gate or row lock is acquired after DML starts, and no normal lock upgrade is performed.

### Existing-owner FK races

The parent/model target is owned before the mutable referencing row. A target delete either wins before the child owner is taken, or waits before checking/removing the target. It cannot hold the target while waiting on a child that waits back on that target.

### Child-table FK races

Every inserted/reinserted target is held before child DML. Pure reference removal takes no target lock. Blind delete/reinsert is forbidden.

### Model root deletes

DataType, ObjectTemplate and RelationshipDefinition whole-root deletes share one transaction advisory gate acquired before rows. Only one such delete can perform incoming-reference checks/cascades at a time, so reciprocal model references cannot form a delete/delete cycle.

### Multi-row and unique races

Overlapping closure rows are inserted in exact PK order, so competing candidates meet at the same first common key and cannot hold later common keys in opposite order.

### Active dependency races

Consumer publication holds dependencies before activation. Dependency deprecation owns the dependency and scans consumers without row-locking them. There is no dependency/consumer lock inversion.

### Advisory gates

Each operation takes at most one gate and takes it before rows. A gate waiter therefore contributes no row edge to a cycle. Operations using different gates are governed by the canonical row plan.

### Lifecycle

Lifecycle event rows have no live FKs and are appended last in one batch; they cannot close a current-state lock cycle.

## Proof result

```text
architectural wait-for graph  ACYCLIC
transactional validity        PASS
public semantic changes       NONE beyond frozen contract
```

The proof is architecture-level. Implementation is not yet written and cannot be claimed verified until deterministic independent-session PostgreSQL scenarios assert both semantic outcomes and absence of SQLSTATE `40P01`.

## AS-IS compatibility

The hardening preserves delivered semantic and blocking contracts:

```text
one semantic mutation remains one UoW
no generic SERIALIZABLE baseline
FK remains final lifetime authority
Relationship CREATE remains globally ungated
Object RENAME remains compatible with Relationship endpoint lifetime holds
Definition RENAME remains compatible with Relationship CREATE
Definition and ownership global predicates retain their existing advisory authorities
model-plane root deletion gains one conservative internal gate
exact-view PK remains factual arbitration authority
```

The RENAME header lock is weakened from NO KEY UPDATE to KEY SHARE because the global Definition gate already serializes candidate names and only root lifetime must be protected. This preserves the delivered non-blocking Relationship CREATE × Definition RENAME contract while allowing implicit default selection to stabilize the Definition header safely.

## Remaining evidence obligation

The architecture proof does not claim that not-yet-written implementation code has already been exercised.

Before freeze/delivery, real-PostgreSQL deterministic tests must verify every required lock rendezvous, both FK winner orders, intended progress and explicit absence of SQLSTATE `40P01`.

A deadlock observed in a supported deterministic scenario reopens the concurrency/persistence realization; it is not normalized as an expected business conflict.

## Final result

```text
transactional design validity  PASS
deadlock-free lock ordering     PASS at architecture level
implementation evidence         PENDING verification owner and code realization
```

No contract reopening is required.
