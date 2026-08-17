# M2 Concurrency-Matrix Cross-Check

**Status:** PASS — SEMANTIC MATRIX COMPLETE — POSTGRESQL REALIZATION PENDING

**Authority:** REVIEW EVIDENCE — NON-NORMATIVE

## Review target

```text
docs/milestones/M2/architecture/concurrency-matrix.md
```

The review compares the M2 matrix with:

```text
docs/architecture/concurrency-matrix.md
docs/architecture/concurrency.md
docs/architecture/verification-concurrency-registry.md

docs/milestones/M2/contract.md
docs/milestones/M2/architecture/relationship.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/persistence.md
```

## Closure summary

```text
canonical M2 mutation census                PASS — 41/41
delivered mutation preservation             PASS — 32/32
new mutation classification                 PASS — 9/9
family-block coverage                       PASS — 15/15
unordered pair classification               PASS — 861/861
AS-IS predicate preservation                PASS — 19/19
new predicate justification                 PASS — VH, RS
M2 public outcome alignment                 PASS
persistence hardening compatibility         PASS
root/reference lifetime coverage            PASS
intended semantic independence              PASS
unclassified mutation/pair                  0
open semantic concurrency point             0
```

## Material findings

### 1. Published schema-history coherence required an explicit predicate

ObjectTemplate and RelationshipDefinition permit multiple DRAFT versions and property/member evolution constraints that survive remove/re-add.

Concurrent publication of distinct versions must not allow both candidates to validate against the same old history and commit a published history impossible under every serial order.

The matrix introduces:

```text
VH — versioned schema-history coherence
```

This makes an already-required invariant explicit. The persistence architecture's stable-header participation and fresh re-certification can realize it without changing the public contract.

### 2. Factual Relationship state required an Object-equivalent predicate

M2 adds:

```text
REL.DATA_CHANGE
REL.SCHEMA_CHANGE
```

The delivered `OS` predicate is Object-specific and cannot be stretched without losing ownership clarity.

The matrix introduces:

```text
RS — complete factual Relationship state
```

It owns fresh-state serialization, exact-pin/property atomicity, mutation/delete ordering and matching lifecycle snapshots for one `relationship_id`.

### 3. Delivered Relationship outcomes were updated only where frozen

```text
RF loser
    M1 -> successful convergence
    M2 -> relationship_fact_conflict

RA same-ID delete waiter
    M1 -> idempotent success
    M2 -> resource_not_found
```

No other delivered predicate outcome changed.

### 4. CREATE_NEXT clone lifetime is now explicit

CREATE_NEXT is not a new PUBLISHED admission, but it creates new physical exact references.

The matrix classifies clone versus target-root deletion through `RL` for:

```text
OT.CN -> cloned parent/component/DTV references
RD.CN -> cloned DTV references
```

This aligns with the persistence requirement to hold cloned targets before insertion.

### 5. Model-root delete serialization remains physical over-serialization

`MODEL_ROOT_DELETE_GATE` does not create a new semantic predicate.

Unrelated model-root deletes remain `I`; referenced roots use `RL`; same-root operations use `AL`; Definition blocker removal may use `RC`.

This prevents implementation hardening from silently redefining domain interaction.

## Cross-domain result

```text
DT × DT    complete
DT × OT    complete
DT × OBJ   evaluated all-I
DT × RD    complete
DT × REL   evaluated all-I

OT × OT    complete
OT × OBJ   complete
OT × RD    complete
OT × REL   evaluated all-I

OBJ × OBJ  complete
OBJ × RD   evaluated all-I
OBJ × REL  complete

RD × RD    complete
RD × REL   complete

REL × REL  complete
```

## Persistence/deadlock handoff

The matrix is compatible with the previously approved architecture-level deadlock proof.

The following remain mandatory realization constraints:

```text
complete pre-DML lock plan
gate before rows
one gate maximum
no normal lock upgrade
canonical row order
target before existing owner
target before child insertion/reinsertion
differential declaration replacement
deterministic closure/event order
fresh whole-UoW restart
no correctness dependency on 40P01 victim selection
```

Semantic `I` cells that require physical care are explicitly registered, including Object/Relationship schema change versus root delete and rename/progress contracts.

## Verification handoff

The matrix requires new deterministic PostgreSQL evidence for:

```text
VH publication races
RDV version/default/lifecycle races
RDV/DTV admission and active-graph races
RS factual state races
RF conflict semantics
RA 404 delete semantics
expanded ES rename races
CREATE_NEXT clone lifetime
root-delete reciprocal references
absence of supported-path SQLSTATE 40P01
```

Stable scenario identifiers and concrete orchestration recipes remain owned by `verification.md`.

## Final result

```text
semantic concurrency matrix   COMPLETE
AS-IS compatibility           PASS
frozen contract compatibility PASS
persistence compatibility     PASS
contract reopening            NOT REQUIRED
PostgreSQL realization        PENDING concurrency.md
deterministic evidence         PENDING verification.md
```
