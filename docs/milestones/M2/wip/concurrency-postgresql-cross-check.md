# M2 PostgreSQL Concurrency Realization Cross-Check

**Status:** PASS — POSTGRESQL DESIGN COMPLETE — DETERMINISTIC IMPLEMENTATION EVIDENCE PENDING

**Authority:** REVIEW EVIDENCE — NON-NORMATIVE

## Review target

```text
docs/milestones/M2/architecture/concurrency.md
```

The review compares the PostgreSQL realization with:

```text
docs/architecture/concurrency.md
docs/architecture/concurrency-matrix.md
docs/architecture/persistence.md
docs/architecture/verification-concurrency-registry.md

docs/milestones/M2/contract.md
docs/milestones/M2/architecture/relationship.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/concurrency-matrix.md

current UoW, store, gate and concurrency-test realization on branch M2
```

## Closure summary

```text
mutation lock-plan coverage                    PASS — 41/41
semantic predicate realization                PASS — 21/21
advisory-gate registry                        PASS — 3/3
row-lock mode mapping                         PASS — 4/4
global row-order consistency                  PASS
direct FK target-before-owner coverage        PASS
child-table target-before-DML coverage        PASS
fresh post-wait re-evaluation                 PASS
constraint arbitration                        PASS
whole-UoW restart boundary                    PASS
retry policy                                  PASS
required progress preservation                PASS
intentional over-serialization classification PASS
root-delete cycle exclusion                   PASS
wait-for graph                                ACYCLIC
open PostgreSQL design point                  0
contract reopening                            NOT REQUIRED
```

## Material findings

### 1. Lock planning must be centralized

The existing AS-IS uses correct local lock concepts but allows each service/store path to sequence calls directly.

The M2 persistence graph contains enough cross-domain targets that local sequencing is no longer a safe authority.

The normative design therefore requires one complete pre-DML `LockPlan`:

```text
optional gate
+
all row identities
+
coalesced sufficient modes
+
one canonical order
```

A service may declare intents but may not acquire them ad hoc.

### 2. `VH` requires a stable publication owner

The semantic matrix introduced:

```text
VH — versioned schema-history coherence
```

Distinct ObjectTemplateVersion or RelationshipDefinitionVersion publications in one aggregate must serialize on the stable header with `FOR NO KEY UPDATE`, then re-certify historical member continuity.

Exact DRAFT locks alone would protect generations but would not protect the shared published-history predicate.

### 3. `RS` maps exactly to the factual Relationship row

The semantic matrix introduced:

```text
RS — complete factual Relationship state
```

The factual `relationships` row is the correct owner:

```text
DATA_CHANGE / SCHEMA_CHANGE
    -> FOR NO KEY UPDATE

DELETE
    -> FOR UPDATE
```

Fresh exact pin, properties and closure are reloaded after acquisition. This is the direct Relationship analogue of the delivered Object-state owner.

### 4. Target-before-owner has two distinct forms

The review distinguishes:

```text
direct FK on an existing owner row
    -> target row before owner row

FK on declaration child rows
    -> target row before child DML
    -> version owner may precede target under global class order
```

This resolves a potential contradiction between the canonical class order and deadlock prevention.

Direct rebind cases are:

```text
ObjectTemplateVersion parent rebind
Object SCHEMA_CHANGE
Relationship SCHEMA_CHANGE
```

Declaration replacement is protected through differential DML and target holds before child writes.

### 5. Root-delete deadlocks require one physical gate

Mutually referencing model roots can produce reciprocal FK/cascade waits even when each delete is semantically valid to attempt.

The stable gate:

```text
MODEL_ROOT_DELETE_GATE = 0x4E45544100000003
```

is acquired before any row and serializes DataType, ObjectTemplate and RelationshipDefinition root deletion.

It is physical over-serialization only and creates no new public conflict.

### 6. Deadlock detection must not be a retry mechanism

The architecture is intended to be deadlock-free on supported paths.

Therefore:

```text
SQLSTATE 40P01
    -> no automatic retry
    -> internal_error
    -> blocking architecture/implementation finding
```

Retrying `40P01` would hide an invalid wait graph and make correctness depend on victim selection.

### 7. Semantic restart is narrow and bounded

Only two causes restart automatically:

```text
LOCK_PLAN_STALE
EXACT_VIEW_COLLISION with disappeared owner
```

The fixed total budget is:

```text
MAX_SEMANTIC_UOW_ATTEMPTS = 4
```

Every attempt is a fresh UoW. There is no savepoint or store-fragment retry.

## Lock-mode cross-check

| Purpose | Required mode | Result |
|---|---|---|
| identity/lifetime compatible with non-key mutation | `FOR KEY SHARE` | PASS |
| exact PUBLISHED admission | `FOR SHARE` | PASS |
| complete non-key owner mutation | `FOR NO KEY UPDATE` | PASS |
| delete/key-changing owner | `FOR UPDATE` | PASS |

The SQLAlchemy mapping is explicitly frozen because `key_share=True` without `read=True` renders PostgreSQL `FOR NO KEY UPDATE`.

## Gate wait-graph cross-check

```text
OWNERSHIP_GRAPH_WRITE_GATE
RELATIONSHIP_DEFINITION_CONFLICT_GATE
MODEL_ROOT_DELETE_GATE
```

Rules:

```text
one gate maximum
gate before rows
transaction-scoped
waiter holds no row
```

Consequently no supported `row -> gate` or `gate -> gate` edge exists.

## Row wait-graph cross-check

Canonical order:

```text
ObjectTemplate
-> DataType
-> RelationshipDefinition
-> Object
-> factual Relationship
```

Within families:

```text
OT ancestor before descendant
unrelated UUID order
header before exact version
version ascending
Object/Relationship UUID ascending
```

Repeated intents are coalesced before acquisition and no normal lock upgrade is allowed.

All 41 mutation plans were checked against this order.

## FK and DML cross-check

### Direct owner rebind

```text
target
-> owner
-> UPDATE
```

No owner can be held while waiting on a target delete that waits back on that owner.

### Child declarations

```text
owner may be held
-> every target acquired
-> child delete/insert
```

Because no child DML occurs before target acquisition, a target delete cannot wait on a child mutation that is waiting back on that target.

### Relationship closure

Rows are inserted by:

```text
(resolution_id, from_object_id, to_object_id)
```

Sequential ordered exact-key inserts ensure overlapping candidates cannot own common unique keys in opposite order.

### Lifecycle

Event rows have no live FK and are appended last. They cannot create a current-state wait edge.

## Predicate realization audit

```text
NU  -> UNIQUE
VS  -> stable version-set owner
DG  -> exact DRAFT owner + generation recheck
LS  -> exact lifecycle owner
DV  -> header/default owner + exact target admission
VH  -> stable header publication serialization
BA  -> exact target SHARE
AM  -> dependency rendezvous + non-locking reverse scan
RL  -> lifetime locks + immediate FK + root gate
AL  -> root UPDATE vs internal header holds
ML  -> header non-key owner
OS  -> Object row owner
RS  -> Relationship row owner
PO  -> parent Object owner
OF  -> parent owner + ownership fact
SO  -> ownership PK
OC  -> ownership graph gate
RC  -> Definition conflict gate
RF  -> exact-view PK + rollback/reclassification
RA  -> exact UUID delete owner
ES  -> one coherent metadata statement
```

Every predicate has one concrete realization and no predicate requires `SERIALIZABLE`.

## AS-IS compatibility

Preserved:

```text
one semantic mutation / one transaction
READ COMMITTED mutation baseline
fresh re-read after wait
FK as final lifetime authority
PK/UNIQUE arbitration
Relationship CREATE without global graph gate
Object rename compatible with endpoint lifetime hold
Definition rename compatible with Relationship CREATE
distinct-version deprecation progress
coherent historical metadata without generic writer serialization
```

Required internal hardening does not change public semantics.

## Remaining evidence obligation

This review is an architecture proof, not a claim about not-yet-written M2 code.

Before freeze/delivery, deterministic independent-session PostgreSQL scenarios must verify:

```text
every required lock rendezvous
every required progress path
both target-delete/rebind winner orders
VH re-certification
RS serial histories
RF conflict and owner-disappearance restart
RA 204/404 behavior
model-root reciprocal references
retry budget
constraint classification
absence of SQLSTATE 40P01
```

A supported scenario that deadlocks reopens `concurrency.md` or its realization. It is not normalized as an expected outcome.

## Final result

```text
PostgreSQL realization design  COMPLETE
semantic-matrix compatibility  PASS
persistence compatibility      PASS
AS-IS compatibility            PASS
deadlock proof                  PASS at architecture level
implementation evidence         PENDING verification.md and code
```
