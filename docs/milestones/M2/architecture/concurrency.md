# M2 Concurrency and PostgreSQL Realization

**Status:** DRAFT — POSTGRESQL REALIZATION COMPLETE — DEADLOCK PROOF PASSED — VERIFICATION REVIEW PENDING

**Authority:** NORMATIVE M2 ARCHITECTURE DRAFT

## Authority and scope

This document is the normative M2 PostgreSQL concurrency realization for the semantic matrix in `concurrency-matrix.md`.

It owns:

```text
semantic Unit-of-Work boundaries
write/read isolation
advisory-gate registry and acquisition discipline
row-lock modes and canonical ordering
complete pre-DML lock-plan realization
fresh-state re-evaluation
PK / UNIQUE / FK arbitration
whole-UoW restart and retry policy
intentional blocking and non-blocking behavior
deadlock-prevention proof
PostgreSQL failure classification
```

Its implementation authority, once the complete M2 architecture set is frozen, is:

```text
docs/architecture/concurrency.md
    delivered transaction and lock baseline
+
docs/milestones/M2/contract.md
    FINAL / FROZEN outcomes
+
concurrency-matrix.md
    complete 41-mutation semantic matrix
+
persistence.md
    physical authorities and deadlock-safe constraints
+
this document
    exact M2 PostgreSQL realization
```

This document does not redefine domain or HTTP outcomes. `relationship.md` owns Relationship semantics, `api.md` owns public mapping, `persistence.md` owns schema and current/history authorities, and `verification.md` owns deterministic evidence.

The proof applies to supported NETAUTO write paths operating through the application Unit of Work. Arbitrary external SQL writers, concurrent runtime DDL and manually altered constraints are outside the supported concurrency model.

---

## 1. Governing transaction contract

One semantic mutation is exactly one PostgreSQL write Unit of Work.

```text
one command
-> one AsyncConnection
-> one database transaction
-> zero nested semantic transactions
-> one explicit commit or complete rollback
```

A mutation UoW contains, as applicable:

```text
non-locking discovery
complete lock-plan construction
gate and row stabilization
fresh protected re-read
candidate rederivation and validation
current-state DML
complete lifecycle event set
commit
```

Stores:

```text
do not commit
do not open independent transactions
do not retry fragments
do not recover an aborted transaction through a savepoint
```

Pure transport parsing and validation independent of mutable persisted state may occur before the UoW. Every default, lifecycle, dependency, current-state, graph, factual-uniqueness or blocker predicate is resolved inside the UoW.

### 1.1 Mutation isolation

The mutation baseline remains:

```text
READ COMMITTED
```

M2 does not adopt a global `SERIALIZABLE` baseline.

Correctness is provided by:

```text
explicit predicate owners
transaction advisory gates
row locks of sufficient initial strength
fresh post-wait reads
PK / UNIQUE / FK authority
generation checks
whole-UoW restart for the two approved restart causes
```

Every protected predicate is re-read in a statement issued after gate/row acquisition. A candidate derived only from an optimistic pre-lock snapshot cannot be written.

### 1.2 Read isolation

```text
single-statement read
    -> ordinary READ COMMITTED statement snapshot

multi-statement aggregate/projection requiring one snapshot
    -> REPEATABLE READ READ ONLY UoW
```

A coherent read UoW sets its transaction mode before the first semantic query. Reads acquire no write-oriented row locks and provide no repeatability across separate HTTP requests.

### 1.3 Runtime DDL exclusion

Serving and schema mutation are not concurrent supported activities.

```text
Alembic DDL
    -> explicit administrative operation
    -> no serving workers

serving workers
    -> exact shipped-head startup gate passed
    -> no runtime DDL
```

This removes DDL table-lock edges from the supported runtime wait graph.

---

## 2. Central lock-planner boundary

M2 introduces one conceptual persistence boundary:

```text
src/netauto/persistence/locking.py
```

It owns:

```text
AdvisoryGate
RowLockMode
RowLockClass
RowLockKey
RowLockIntent
LockPlan
LockPlanStale
acquire_lock_plan
classify_postgresql_failure
```

The existing `gates.py` may be subsumed by this module or remain a thin delegating wrapper. Gate keys and behavior have one authority.

Application services describe semantic lock intents. Stores provide exact single-table lock statements and current-state reloads. No service may hand-code a different acquisition order.

### 2.1 Row identity

Canonical row identities are:

```text
ObjectTemplate header
    (OT, template_id, HEADER)

ObjectTemplateVersion
    (OT, template_id, VERSION, version)

DataType header
    (DT, datatype_id, HEADER)

DataTypeVersion
    (DT, datatype_id, VERSION, version)

RelationshipDefinition header
    (RD, relationship_definition_id, HEADER)

RelationshipDefinitionVersion
    (RD, relationship_definition_id, VERSION, version)

Object
    (OBJECT, object_id)

factual Relationship
    (RELATIONSHIP, relationship_id)
```

Owned declaration, Resolution, ownership, runtime-closure and lifecycle rows are not independent semantic lock owners. Their DML is protected by the owning root/version row, a gate or a final constraint authority, and follows deterministic physical ordering.

### 2.2 Lock-intent coalescence

A plan may request several reasons/modes for one row. Before acquisition they are coalesced to one sufficient initial mode:

```text
FOR UPDATE
    > FOR NO KEY UPDATE
    > FOR SHARE
    > FOR KEY SHARE
```

The strongest required mode is acquired once. Normal row-lock upgrades are forbidden.

This precedence is a planning rule, not a claim that PostgreSQL lock modes form a general mathematical total order. It is the sufficient-mode order for the predicates owned by NETAUTO.

### 2.3 Planning phases

Every write path follows:

```text
1. begin READ COMMITTED UoW
2. perform non-locking discovery only
3. build complete gate + row plan
4. coalesce repeated row intents
5. acquire optional gate
6. acquire all rows in canonical order
7. verify every planned row was acquired
8. re-read all mutable protected state
9. rederive and revalidate the full candidate
10. if a new lock identity would be required:
        rollback whole UoW
        restart from step 1
11. perform deterministic DML
12. insert complete event set
13. commit
```

No current-state DML occurs before step 11.

After DML begins:

```text
no new gate
no explicit row lock
no normal lock upgrade
no change to the planned dependency set
```

FK and UNIQUE enforcement may take PostgreSQL-internal locks, but every expected FK target has already been explicitly stabilized.

### 2.4 Missing and changed rows

After acquisition:

```text
planned path target absent
    -> resource_not_found

planned body/command operand absent
    -> referenced_resource_not_found

default became null or target became ineligible
    -> owning semantic conflict/validation result

DRAFT generation changed
    -> stale_revision or lifecycle_state_conflict

optimistic discovery identifies a different valid dependency set
    -> LockPlanStale
    -> whole-UoW restart
```

Even when a newly discovered lock would sort after all current locks, it is not appended. Restart is mandatory so the proof has one acquisition phase.

---

## 3. Advisory-gate registry

All gates use signed PostgreSQL `BIGINT` transaction advisory locks:

```sql
SELECT pg_advisory_xact_lock(:stable_key)
```

They are released automatically at transaction end.

Canonical keys:

```text
OWNERSHIP_GRAPH_WRITE_GATE
    0x4E45544100000001

RELATIONSHIP_DEFINITION_CONFLICT_GATE
    0x4E45544100000002

MODEL_ROOT_DELETE_GATE
    0x4E45544100000003
```

The keys are stable architecture values and must not be generated from process hash functions.

### 3.1 Gate discipline

```text
at most one gate per semantic UoW
gate acquired before every row lock
gate waiter holds no NETAUTO row lock
fresh protected read issued after acquisition
no session-level advisory lock
no try-lock / skip behavior
```

### 3.2 Gate ownership

```text
OWNERSHIP_GRAPH_WRITE_GATE
    -> real OBJ.ATTACH edge-add candidates only

RELATIONSHIP_DEFINITION_CONFLICT_GATE
    -> RD.CREATE
    -> RD.RENAME

MODEL_ROOT_DELETE_GATE
    -> DT.DELETE_LINEAGE
    -> OT.DELETE_LINEAGE
    -> RD.DELETE_DEFINITION
```

`DETACH` does not take the ownership graph gate because edge removal cannot create a cycle.

Definition deletion does not take the Definition conflict gate because removal cannot introduce an equivalence/conflict. It takes only the model-root delete gate.

Unrelated model-root deletes are semantically independent but intentionally physically serialized. This gate must not produce a new public conflict.

---

## 4. PostgreSQL row-lock modes

Canonical modes and SQLAlchemy Core rendering:

| Architecture mode | PostgreSQL | SQLAlchemy `with_for_update` |
|---|---|---|
| `KS` | `FOR KEY SHARE` | `read=True, key_share=True` |
| `S` | `FOR SHARE` | `read=True` |
| `NKU` | `FOR NO KEY UPDATE` | `key_share=True` |
| `U` | `FOR UPDATE` | no flags |

The counter-intuitive SQLAlchemy `key_share=True` mapping for `NKU` must be covered by a static/SQL compilation test.

### 4.1 Mode meaning

```text
KS
    stable identity/lifetime only
    compatible with non-key metadata/state updates
    conflicts with key-changing update and delete

S
    lifecycle-sensitive exact PUBLISHED admission
    blocks status change/delete through commit

NKU
    complete non-key current-state owner
    serializes competing owner mutation

U
    delete, root deletion or key-changing owner
```

`FOR KEY SHARE` is insufficient for a new PUBLISHED binding because status is a non-key field. `FOR SHARE` is required.

### 4.2 Lock statements

Lock statements:

```text
select from exactly one table
select only primary/exact key columns
use OF <target table> where supported
contain explicit ORDER BY matching the canonical key
perform no join that can accidentally lock another table
do not use NOWAIT
do not use SKIP LOCKED
```

Contiguous planned rows with the same table and mode may be locked in one ordered statement. Mixed-mode runs remain separate and preserve global order.

Returned keys must equal planned keys. A missing row is handled before DML.

---

## 5. Canonical row order

Every plan uses one global class order:

```text
10  ObjectTemplate headers and exact versions
20  DataType headers and exact versions
30  RelationshipDefinition headers and exact versions
40  Object rows
50  factual Relationship rows
```

No supported operation acquires a lower class after a higher class.

### 5.1 ObjectTemplate order

For all planned ObjectTemplate lineages:

1. validate the stable parent graph;
2. topologically order ancestor before descendant;
3. break unrelated-lineage ties by UUID ascending;
4. within one lineage:
   - header first;
   - exact versions by version ascending.

Stable parent lineage is immutable, so the topological relation cannot be changed by another normal mutation. Missing/corrupt ancestry after locking aborts before DML.

Component-target lineages do not create ordering edges. They participate as ordinary lineage rows under the deterministic topological/UUID order.

### 5.2 DataType and RelationshipDefinition order

```text
lineage/Definition UUID ascending
-> header
-> exact versions ascending
```

### 5.3 Object and Relationship order

```text
UUID ascending
```

When one Object appears with several intents, for example parent `NKU` and endpoint lifetime `KS`, the plan coalesces the row before sorting.

### 5.4 Direct-FK target-before-owner rule

For a foreign key stored directly on an already-existing mutable owner row, the target is always earlier than the owner:

```text
ObjectTemplateVersion parent rebind
    -> ancestor parent OTV
    -> descendant/current OTV owner

Object SCHEMA_CHANGE
    -> target OTV
    -> Object owner

Relationship SCHEMA_CHANGE
    -> target RDV
    -> factual Relationship owner
```

This is compatible with the class/topological order above.

For child-table declarations, the referenced target need only be acquired before child DML. The exact version owner may be earlier in the class order. This distinction avoids target/owner cycles while retaining one global order.

---

## 6. Common exact-binding rules

### 6.1 Explicit new binding

```text
stable target header KS
exact target version S
recheck exact membership and PUBLISHED after acquisition
persist exact pin
```

### 6.2 Implicit default binding

```text
stable target header S
freshly read default_version
exact target version S
recheck:
    default still identifies the planned version
    target is PUBLISHED
persist exact pin
```

If the fresh default identifies another version not in the plan, restart the whole UoW. If it is null, return `default_version_unavailable`.

### 6.3 Historical clone lifetime

CREATE_NEXT copies already-owned exact references but creates new physical FK rows.

```text
stable target header KS
exact target version KS
```

PUBLISHED status is not required. The target must still exist through insertion.

### 6.4 Differential declaration target

For an inserted/reinserted declaration:

```text
new or rebound exact dependency
    -> target S

same exact dependency reinserted only because another field changed
    -> target KS

unchanged physical row
    -> no outgoing target lock
    -> no child DML

removed row
    -> no outgoing target lock
```

All target locks precede child DML.

---

## 7. Canonical 41-mutation lock registry

Notation:

```text
H   stable header/root row
V   exact version row
KS/S/NKU/U lock mode

implicit target
    H S + V S

explicit new target
    H KS + V S

historical cloned target
    H KS + V KS
```

Candidate-dependent rows are included only when the command actually references them.

### 7.1 DataType — 10

| Mutation | Gate | Complete explicit row plan |
|---|---|---|
| `DT.C` | none | none; qualified-name UNIQUE is final arbitration |
| `DT.CN` | none | own `DT.H NKU`; exact source `DT.V KS` |
| `DT.R` | none | own `DT.H KS`; exact DRAFT `DT.V NKU` |
| `DT.P` | none | own `DT.H NKU`; exact DRAFT `DT.V NKU` |
| `DT.SD` | none | own `DT.H NKU`; target `DT.V S` |
| `DT.CD` | none | own `DT.H NKU` |
| `DT.D` | none | own `DT.H S`; target `DT.V NKU`; active-consumer scan is non-locking |
| `DT.DD` | none | own `DT.H NKU`; exact DRAFT `DT.V U` |
| `DT.DL` | `MODEL_ROOT_DELETE_GATE` | root `DT.H U` |
| `DT.DESC` | none | own `DT.H NKU` |

`DT.CN`, `DT.P`, `DT.DD` serialize version-set/source eligibility through the header. Distinct-version deprecations use compatible header `S` locks and distinct exact owners.

### 7.2 ObjectTemplate — 10

| Mutation | Gate | Complete explicit row plan |
|---|---|---|
| `OT.C` | none | parent/component target OT headers `KS`; parent exact OTV `S` for a new binding; implicit parent header `S`; DTV header/exact targets using §6 |
| `OT.CN` | none | cloned parent/component/DTV targets `KS`; own `OT.H NKU`; exact source OTV `KS` |
| `OT.R` | none | candidate parent/component/DTV targets using §6; own `OT.H KS`; exact DRAFT `OT.V NKU` |
| `OT.P` | none | target parent/DTV headers `KS` and exact versions `S`; own `OT.H NKU`; exact DRAFT `OT.V NKU` |
| `OT.SD` | none | own `OT.H NKU`; target `OT.V S` |
| `OT.CD` | none | own `OT.H NKU` |
| `OT.D` | none | own `OT.H S`; target `OT.V NKU`; active-child scan is non-locking |
| `OT.DD` | none | own `OT.H NKU`; exact DRAFT `OT.V U` |
| `OT.DL` | `MODEL_ROOT_DELETE_GATE` | root `OT.H U` |
| `OT.DESC` | none | own `OT.H NKU` |

Additional rules:

- parent OTV target is ancestor-ordered before the current version owner;
- component targets are stable-header lifetime locks only;
- `OT.R` touches declarations differentially;
- unchanged direct parent FK requires no target reacquisition; a rebind requires `S`;
- `OT.P` re-certifies complete member history after `OT.H NKU`, realizing `VH`;
- component target existence remains a stable-lifetime predicate, not active-version admission.

### 7.3 Object and ownership — 7

| Mutation | Gate | Complete explicit row plan |
|---|---|---|
| `OBJ.C` | none | selected OTV header/exact target using explicit/implicit §6 rules |
| `OBJ.RN` | none | Object `NKU` |
| `OBJ.DC` | none | Object `NKU` |
| `OBJ.SC` | none | target OTV header `KS`, target exact OTV `S`, then Object `NKU` |
| `OBJ.A` | `OWNERSHIP_GRAPH_WRITE_GATE` | parent Object `NKU`; child Object `KS`; coalesced and UUID ordered |
| `OBJ.DET` | none | parent Object `NKU`; pure reference removal takes no child target lock |
| `OBJ.DEL` | none | Object `U` |

After the ownership gate and Object locks, `OBJ.A` re-reads the current ownership fact and entire cycle predicate in a subsequent statement before inserting.

`OBJ.DET` uses the parent as semantic owner. The current edge FK protects child lifetime until removal; coherent child metadata is obtained through the event projection rather than a generic child writer lock.

### 7.4 RelationshipDefinition and exact versions — 10

| Mutation | Gate | Complete explicit row plan |
|---|---|---|
| `RD.C` | `RELATIONSHIP_DEFINITION_CONFLICT_GATE` | endpoint ObjectTemplate headers `KS`; initial property DTV targets using §6 |
| `RD.RN` | `RELATIONSHIP_DEFINITION_CONFLICT_GATE` | Definition `H KS` |
| `RD.CN` | none | cloned DTV targets `KS`; own Definition `H NKU`; exact source RDV `KS` |
| `RD.R` | none | declaration DTV targets using §6; own Definition `H KS`; exact DRAFT RDV `NKU` |
| `RD.P` | none | target DTV headers `KS` and exact versions `S`; own Definition `H NKU`; exact DRAFT RDV `NKU` |
| `RD.SD` | none | own Definition `H NKU`; target RDV `S` |
| `RD.CD` | none | own Definition `H NKU` |
| `RD.D` | none | own Definition `H S`; target RDV `NKU` |
| `RD.DD` | none | own Definition `H NKU`; exact DRAFT RDV `U` |
| `RD.DL` | `MODEL_ROOT_DELETE_GATE` | root Definition `H U` |

`RD.RN` uses only `KEY SHARE` on the stable header because the Definition gate serializes certified-set writers and the command updates non-key Resolution names. This remains compatible with exact-version state operations and Relationship creation.

`RD.P` serializes distinct publication in one Definition through `H NKU`, then re-certifies complete historical property continuity, realizing `VH`.

### 7.5 Factual Relationship — 4

| Mutation | Gate | Complete explicit row plan |
|---|---|---|
| `REL.C` | none | Definition `H KS` for explicit selection or `H S` for implicit selection; exact target RDV `S`; endpoint Objects `KS` in UUID order |
| `REL.DC` | none | factual Relationship `NKU` |
| `REL.SC` | none | Definition `H KS`; target RDV `S`; factual Relationship `NKU` |
| `REL.DEL` | none | factual Relationship `U` |

No factual CREATE takes a global Relationship gate.

Resolution rows are not explicitly locked for CREATE. Their identity/FK key is stable; FK `KEY SHARE` is compatible with non-key name updates. The event metadata statement provides `ES` coherence.

Existing exact pins and endpoint references protect model/Object lifetime for `REL.DC`, `REL.SC` and `REL.DEL`; only a new target binding requires `S`.

---

## 8. Protected re-read and candidate derivation

After plan acquisition, each family reloads the state below.

### 8.1 Versioned aggregates

```text
stable header and default
complete current version set when allocation is relevant
exact source/target/DRAFT header
DRAFT revision and status
complete current declarations
resolved implicit-default targets
historical published/deprecated member continuity
direct exact dependency status
```

`CREATE_NEXT` recomputes `max(existing)+1` and source eligibility.

`REVISE` derives a fresh differential declaration plan from the locked current DRAFT.

`PUBLISH` re-certifies:

```text
DRAFT generation
local structural validity
historical member evolution
all direct dependencies PUBLISHED
default policy
```

### 8.2 Object

```text
complete intrinsic Object state
current exact source schema
target exact schema when SCHEMA_CHANGE
outgoing ownership facts when parent migration is relevant
```

### 8.3 Ownership

```text
parent current exact schema
child current stable lineage
current ownership fact
fresh protected graph reachability
```

### 8.4 RelationshipDefinition certification

After the Definition gate:

```text
complete current certified stable Definition set
current ObjectTemplate ancestry graph
candidate endpoint existence
same-Definition current aggregate for rename
```

The protected read is a statement after gate acquisition. Definition deletion may cause success or conservative conflict according to the matrix; no second gate is taken.

### 8.5 Factual Relationship

```text
complete current header
exact source RDV and declaration/DTV closure
canonical current properties
complete deterministic runtime-resolution closure
endpoint stable template lineages
target RDV for SCHEMA_CHANGE
```

`REL.DC`, `REL.SC` and `REL.DEL` derive from the freshly locked factual row, realizing `RS`.

---

## 9. Differential declarations and physical DML

`OT.R` and `RD.R` remain complete semantic replacements. Physical replacement is differential.

```text
unchanged
removed
replaced
new
```

Rules:

1. unchanged rows are not updated or deleted;
2. removed/replaced rows are deleted in physical PK order;
3. all replaced rows are deleted before any replacement insert;
4. replacement/new rows are inserted in physical PK order;
5. exact target locks are already held;
6. owner revision is incremented only after all child DML succeeds;
7. one failure rolls back owner revision and the complete child set.

For ObjectTemplate:

```text
properties first, ordered by (template_id, template_version, name)
components second, ordered by (template_id, template_version, name)
```

For RDV:

```text
properties ordered by
(relationship_definition_id, relationship_definition_version, name)
```

Position swaps are legal because all replaced rows are removed before reinsertion.

Blind `DELETE all + INSERT all` is forbidden.

---

## 10. Lifecycle and metadata realization

Every real state transition and its complete required lifecycle set use the same UoW.

```text
current-state DML
-> one coherent metadata projection statement
-> deterministic semantic-view derivation
-> complete event batch
-> commit
```

Relationship metadata projection joins:

```text
runtime closure
RelationshipResolution names
from/to Object canonical names
```

It runs as one statement and is the authoritative event/response metadata observation for the transition.

Allowed rename race observations:

```text
all old
all new
or, for independent renames, a combination that coexisted
in the statement snapshot
```

Mixed rows from independently issued metadata statements are forbidden.

Event rows:

```text
have no live FKs
are inserted last
use one batch INSERT
use DB-generated UUID and transaction_timestamp()
```

Conflict-sensitive current rows are ordered before insertion:

```text
runtime closure
    (resolution_id, from_object_id, to_object_id)

Relationship semantic event views
    (object_id, destination_object_id, relationship_name)
```

For the at-most-four runtime closure rows, M2 uses sequential exact-key INSERT statements in sorted order. A single multi-values statement may replace them only after verification proves equivalent unique-index probe ordering.

---

## 11. Safety-predicate realization map

| Predicate | PostgreSQL realization |
|---|---|
| `NU` | qualified-name UNIQUE; aggregate rollback on loser |
| `VS` | stable header `NKU`; fresh max/source read |
| `DG` | exact DRAFT `NKU/U`; fresh `expected_revision` check |
| `LS` | exact version owner plus fresh status; header where default policy participates |
| `DV` | stable header `NKU/S`; target exact `S`; fresh default/target recheck |
| `VH` | stable OT/RD header `NKU` serializes publication; fresh complete historical certification |
| `BA` | stable target header plus exact target `S`; PUBLISHED recheck through commit |
| `AM` | publisher holds dependency `S`; deprecator owns dependency `NKU` and performs non-locking reverse-consumer `EXISTS` |
| `RL` | explicit lifetime locks, immediate non-deferrable FK `RESTRICT`, target-before-DML, model-root gate |
| `AL` | root `U` versus every internal operation's header lifetime/owner lock |
| `ML` | stable header `NKU`; atomic complete field update |
| `OS` | Object `NKU/U`; fresh complete state; atomic state/event write |
| `RS` | Relationship `NKU/U`; fresh exact pin/properties/closure; atomic state/event write |
| `PO` | parent Object `NKU` shared by schema change and ownership operations |
| `OF` | parent owner lock, fresh ownership fact, ownership PK, exact-edge delete |
| `SO` | `object_components` PK on child plus fresh arbitration |
| `OC` | ownership graph gate, post-gate graph read, one edge insert |
| `RC` | Definition conflict gate, post-gate certified-set read, complete rename/create |
| `RF` | exact-view PK, sorted full-closure insert, full rollback and fresh-UoW classification |
| `RA` | exact Relationship UUID `U`, one real delete, UUID-specific late delete |
| `ES` | one metadata statement; compatible `KS` lifetime locks; no generic rename serialization |

Reverse-consumer scans deliberately do not lock consumer rows. This is required to avoid dependency/consumer lock inversion:

```text
publisher wins dependency S
    -> deprecator waits and then sees active consumer

deprecator wins dependency NKU
    -> publisher waits and then fails PUBLISHED recheck

consumer removal races
    -> deprecator may fail conservatively
```

---

## 12. Constraint arbitration

All current semantic FKs are immediate and non-deferrable.

Expected arbitration authorities:

```text
qualified-name UNIQUE
    -> qualified_name_conflict

object ownership PK
    -> fresh ownership classification
    -> convergent success or ownership_conflict

runtime exact-view PK
    -> rollback complete REL.C candidate
    -> fresh conflict/restart path

root-delete FK RESTRICT
    -> delete_blocked

target FK during new binding
    -> target-won referenced resource failure
    -> normally detected before DML by the lock plan
```

A failed PostgreSQL transaction is never queried. Store code captures only an internal classifier and semantic selectors, exits the UoW, rolls back, and then either maps the failure or opens a fresh UoW.

### 12.1 SQLSTATE policy

```text
23505 unique_violation
    -> classify by the finite known constraint registry

23503 foreign_key_violation
    -> classify target/reference/root-delete authority

23514 check_violation
23502 not_null_violation
    -> internal_error unless explicitly identified as transport input
       before persistence; DB discovery of such state is an invariant defect

40P01 deadlock_detected
    -> no automatic retry
    -> internal_error
    -> architecture/implementation finding

40001 serialization_failure
    -> unexpected under READ COMMITTED baseline
    -> no automatic retry
    -> internal_error

55P03 lock_not_available
57014 query_canceled
    -> operational/internal failure
    -> no semantic remapping
```

No SQLSTATE, constraint, table, column or stack detail reaches the public API.

### 12.2 Constraint-name registry

Constraint names are explicit persistence metadata and may be used internally for finite classification. Unknown or mismatched constraint names are `internal_error`, not a generic conflict escape hatch.

A version-allocation PK collision, default FK violation after stabilization, partial closure constraint failure or lifecycle shape failure is always an invariant defect.

---

## 13. Whole-UoW restart and retry policy

M2 permits automatic restart only for:

```text
LOCK_PLAN_STALE
    optimistic discovery no longer describes the complete required lock set

EXACT_VIEW_COLLISION
    REL.C lost exact-view PK arbitration and the conflicting owner
    disappeared before fresh classification
```

Shared budget:

```text
MAX_SEMANTIC_UOW_ATTEMPTS = 4
```

This means one initial attempt plus at most three complete restarts.

Rules:

```text
each attempt uses a new connection transaction/UoW
no savepoint retry
no store-fragment retry
no sleep-based scheduling
no retry after a public semantic failure
no retry for 40P01 or 40001
```

After an exact-view collision:

1. the failed UoW rolls back completely;
2. a fresh UoW loads the current exact-view owner;
3. owner still current:
   - validate the current aggregate;
   - return `relationship_fact_conflict`;
4. owner absent:
   - consume one restart attempt;
   - rederive a new candidate from current state.

After four unsuccessful attempts, the operation returns `internal_error` with no concurrency internals in public details. Exhaustion is a bounded-livelock safety outcome, not a new business conflict.

`stale_revision`, lifecycle conflict, default conflict, schema-change blocker and not-found are final semantic outcomes and are never automatically retried.

---

## 14. Detailed factual Relationship pipelines

### 14.1 CREATE

```text
attempt begins
-> discover selected Resolution / Definition
-> discover explicit or implicit RDV target
-> build RD + endpoint Object lock plan
-> acquire plan
-> fresh Definition/default/RDV/Object re-read
-> require target PUBLISHED
-> validate initial canonical properties
-> derive complete closure
-> pre-read current exact-view owners
-> if any owner exists:
       validate current aggregate
       relationship_fact_conflict
-> insert factual header
-> insert every closure row in exact-key order
-> one metadata projection
-> insert complete CREATED event batch
-> commit
```

An exact-view unique collision aborts the entire attempt. No header, earlier closure row or event survives.

Unrelated CREATE operations have no shared gate and progress unless their concrete row/unique/FK sets overlap.

### 14.2 DATA_CHANGE

```text
Relationship NKU
-> fresh complete aggregate validation
-> derive canonical SET/REMOVE candidate
-> candidate == current:
       success
       no UPDATE
       no metadata query required for an event
       no event
-> real change:
       replace complete JSONB properties
       one metadata projection
       complete DATA_CHANGE event batch
       commit
```

Exact pin and runtime closure remain unchanged.

### 14.3 SCHEMA_CHANGE

```text
optimistic current Definition discovery
-> Definition KS
-> target RDV S
-> Relationship NKU
-> fresh source fact and target reload
-> require same Definition and forward PUBLISHED target
-> preserve-or-fail migration
-> one-row atomic update of exact pin + properties
-> closure unchanged
-> one metadata projection
-> complete SCHEMA_CHANGE event batch
-> commit
```

If current state now requires another target/Definition lock, restart before DML.

### 14.4 DELETE

```text
Relationship U
-> absent: resource_not_found
-> validate complete current fact
-> capture final factual state
-> one metadata projection before physical removal
-> delete header
-> owned closure CASCADE
-> complete DELETED event batch
-> commit
```

A same-ID waiter acquires no row after the first commit, returns `resource_not_found` and writes no event.

---

## 15. Model-plane root deletion

Every model root deletion follows:

```text
MODEL_ROOT_DELETE_GATE
-> root header U
-> fresh owned aggregate and blocker read
-> clear internal default pointer in the same transaction
-> root DELETE
-> owned CASCADE
-> immediate external FK RESTRICT arbitration
-> commit or full rollback
```

The gate covers DataType, ObjectTemplate and RelationshipDefinition roots.

### 15.1 Why one gate is required

Mutually referencing roots can otherwise form:

```text
DELETE A
    holds root A
    waits on a referencing child owned by B

DELETE B
    holds root B
    waits on a referencing child owned by A
```

With gate-first acquisition, only one root delete can enter FK/cascade work. The waiter holds no row, so the cycle cannot form.

### 15.2 No semantic change

```text
same root
    -> AL outcomes

referenced roots
    -> RL outcomes

unrelated roots
    -> semantic I
    -> physical serialization only
```

The gate produces no public “root delete busy” result.

---

## 16. Deadlock-prevention proof

The supported acquisition graph is:

```text
optional one advisory gate
-> globally ordered explicit row locks
-> fresh protected reads
-> deterministic child/current-state DML
-> append-only lifecycle batch
-> commit
```

### 16.1 Advisory edges

A gate waiter owns no row. Each operation takes at most one gate. Therefore:

```text
gate -> row
```

may exist, but no supported:

```text
row -> gate
gate A -> gate B
```

edge exists.

### 16.2 Explicit row edges

All transactions use the same class and intra-class order. The first incompatible common planned row is encountered in the same order.

No normal lock upgrade creates a backwards edge.

### 16.3 Direct existing-owner FK rebind

The exact target is locked before the mutable owner. Therefore the owner is never held while waiting for a target delete that can wait back on the owner.

This covers:

```text
ObjectTemplate parent-version rebind
Object SCHEMA_CHANGE
Relationship SCHEMA_CHANGE
```

### 16.4 Child-table FK DML

Every inserted/reinserted target is stabilized before child DML. Pure removal takes no outgoing target lock. No DML happens while an expected target lock is still pending.

The owner row may precede a child-table target in the global class order, for example OT owner before DTV. This is safe because the target delete cannot wait on an unmodified child row owned by the transaction; child DML begins only after the target is held.

### 16.5 Active dependencies

Publisher:

```text
dependency S
-> consumer activation
```

Deprecator:

```text
dependency NKU
-> non-locking reverse scan
```

The deprecator never waits on a consumer owner, so dependency/consumer inversion is absent.

### 16.6 Root deletes

`MODEL_ROOT_DELETE_GATE` removes root-delete/root-delete cycles. Internal mutation/root delete follows root-header lock compatibility plus target-before-DML rules.

### 16.7 Unique-index arbitration

- qualified-name candidates insert one conflicting key;
- ownership inserts one child PK;
- runtime closure rows are inserted in one global exact-key order.

Two overlapping closure candidates cannot hold later common keys in opposite order.

### 16.8 Lifecycle rows

Lifecycle rows:

```text
have no live FK
have independent DB-generated IDs
are appended after current-state DML
```

They add no edge back to model/current-state rows.

### 16.9 PostgreSQL implicit/table locks

Expected FK target locks are pre-held. Runtime DML table-level `ROW EXCLUSIVE`/`ROW SHARE` locks are mutually compatible for supported DML, and runtime DDL is excluded.

### 16.10 Proof result

Under the mandatory rules:

```text
supported application wait-for graph = acyclic by construction
```

PostgreSQL deadlock detection remains a safety net. A supported deterministic scenario returning `40P01` disproves the realization and blocks architecture freeze/delivery.

Correctness never depends on PostgreSQL selecting and retrying a deadlock victim.

---

## 17. Intentional parallelism and over-serialization

### 17.1 Required progress

The realization must preserve:

```text
REL.C unrelated fact × REL.C unrelated fact
    -> no global Relationship gate

REL.C × OBJ.RN(endpoint)
    -> Object KS compatible with Object NKU

REL.C × RD.RN
    -> Definition KS/S compatible with rename KS
    -> runtime Resolution FK KS compatible with name NKU

RD.RN × RD exact-version/default/lifecycle operations
    -> header KS compatible with their non-delete modes

distinct-version DT/OT/RD DEPRECATE
    -> shared header S + distinct version owners

distinct DRAFT REVISE operations
    -> shared header KS + distinct version owners
```

### 17.2 Intentional serialization

```text
all real ownership edge additions
    -> ownership graph gate

all RelationshipDefinition CREATE/RENAME candidates
    -> Definition conflict gate

all model root deletes
    -> model-root gate

parent Object rename/data mutation × ATTACH
    -> shared parent NKU owner

description × default/header policy mutation
    -> shared header owner
```

A verification failure in either direction—missing required blocking or unexpected prohibited blocking—is an architecture regression.

---

## 18. Verification handoff

`verification.md` must map every non-trivial matrix rule to real PostgreSQL evidence and must extend the delivered recipes.

At minimum:

```text
VH
    distinct OT publication
    distinct RD publication

VS/DG/LS/DV
    every RDV version/default lifecycle family

BA/AM
    RDV properties vs DTV lifecycle/default
    REL CREATE/SCHEMA_CHANGE vs RDV lifecycle/default

RL/AL
    CREATE_NEXT cloned references vs target delete
    declaration rebind/reinsert vs target delete
    direct owner rebind vs root delete, both winner orders
    root/internal mutation
    mutually referencing root deletes

RS/RA
    REL.DC × REL.DC
    REL.DC × REL.SC
    REL.SC × REL.SC
    mutation × DELETE
    DELETE × DELETE with 204/404

RF
    equivalent and partially overlapping closure candidates
    winner persistence and winner disappearance

ES
    all four real Relationship transitions vs Object/Resolution rename

parallelism
    required progress contracts above

deadlock
    every supported scenario asserts no SQLSTATE 40P01
```

Tests use independent sessions and real locks/constraints. Sleep-only scheduling cannot establish the required order.

The lock planner itself requires:

```text
unit tests for intent coalescence and canonical sorting
SQL compilation tests for all four lock modes
integration tests that inspect blocking PIDs
failure-classification tests by SQLSTATE + constraint registry
restart-budget tests
```

---

## 19. AS-IS preservation and M2 hardening

Preserved:

```text
one mutation / one UoW
READ COMMITTED writes
REPEATABLE READ read-only composite reads
fresh post-wait validation
PK / UNIQUE / FK final authority
no generic SERIALIZABLE retry loop
exact-view factual arbitration
ownership and Definition advisory predicates
coherent metadata snapshots without generic rename serialization
```

M2-required internal hardening:

```text
central complete lock planner
gate-first discipline
MODEL_ROOT_DELETE_GATE
no normal lock upgrade
stable header in every exact-version mutation
VH publication owner on OT/RD header
target-before-existing-owner direct FK rebind
differential declaration replacement
cloned-reference lifetime locks
endpoint Object lifetime locks before closure insertion
deterministic conflict-key DML
bounded whole-UoW semantic restart
no 40P01 retry
```

Public semantic changes remain only those frozen in the contract:

```text
REL.C loser -> relationship_fact_conflict
REL.DEL waiter -> resource_not_found
new RDV and factual mutation behavior
```

---

## 20. Contract traceability and closure

Primary ownership:

```text
M2-OUT-02
M2-OUT-04
M2-OUT-08
```

Direct realization for:

```text
M2-AC-15
M2-AC-16
M2-AC-17
M2-AC-18
M2-AC-19
```

It also supplies the transaction mechanism for:

```text
M2-AC-01 ... M2-AC-10
M2-AC-13 ... M2-AC-14
M2-AC-31
```

Architecture-draft closure:

```text
UoW and isolation model                     CLOSED
gate registry and stable keys               CLOSED
four row-lock modes                         CLOSED
complete lock-planner algorithm             CLOSED
global row order                            CLOSED
all 41 mutation lock plans                  CLOSED
all 21 predicate realizations               CLOSED
constraint arbitration                      CLOSED
restart/retry policy                        CLOSED
Relationship factual pipelines              CLOSED
model-root delete realization               CLOSED
intended blocking/non-blocking contract      CLOSED
deadlock wait-graph proof                    PASS
AS-IS cross-check                            PASS
frozen-contract cross-check                  PASS
```

No PostgreSQL-concurrency design point remains open in this owner.

This document remains `NOT FROZEN` until:

- `verification.md` registers deterministic evidence for every non-trivial matrix rule;
- implementation-oriented architecture owners confirm the lock planner/module boundaries;
- real PostgreSQL scenarios confirm required blocking/progress and no supported `40P01`;
- the complete M2 architecture set passes final consistency closure.
