# PostgreSQL Concurrency and Unit of Work — Current AS-IS

## Purpose and authority

This document owns the PostgreSQL realization of the semantic interaction rules
in [`concurrency-matrix.md`](concurrency-matrix.md). It defines transaction,
locking, ordering, arbitration and restart mechanisms. It does not create domain
outcomes; persistence shapes are owned by [`persistence.md`](persistence.md), and
deterministic evidence by
[`verification-concurrency-registry.md`](verification-concurrency-registry.md).

## Unit of Work boundary

One semantic mutation is one write Unit of Work. An attempt contains, as
applicable:

```text
candidate discovery
complete lock-plan construction
advisory-gate acquisition
ordered row-lock acquisition
fresh protected-state reread
dependency admission and semantic validation
header/current-state DML
deterministic child or closure DML
complete lifecycle-event insertion
one commit or complete rollback
```

Mutation isolation is PostgreSQL `READ COMMITTED`. Correctness comes from the
complete lock plan, database constraints and fresh post-wait derivation, not from
an initial read snapshot. The canonical public business GET census uses one
authoritative projection statement and its PostgreSQL statement snapshot.
Multi-statement coherent reads outside that census use `REPEATABLE READ READ
ONLY` where their owner requires one transaction snapshot.

The transaction baseline has no generic `SERIALIZABLE` retry policy. SQLSTATE
`40P01` and `40001` are never automatically retried.

## Centralized LockPlan

Every one of the 41 mutation primitives is registered with one centralized
planner. Before current-state DML, the application constructs one complete,
immutable `LockPlan`:

```text
optional AdvisoryGate
ordered tuple of RowLockIntent(RowLockKey, RowLockMode)
```

The plan is acquired once. Lock intent cannot be appended after DML begins. If a
fresh protected reread reveals a different dependency set, the attempt raises
`LockPlanStale`, rolls back completely and may start a fresh Unit of Work within
the bounded policy.

Duplicate row intents coalesce to the strongest required mode. A normal path
does not acquire a weaker mode and later upgrade it.

## Row-lock modes

The exact mode vocabulary and SQL are:

| Code | PostgreSQL clause | Purpose |
|---|---|---|
| `KS` | `FOR KEY SHARE` | Hold referenced identity/key lifetime while allowing non-key updates. |
| `S` | `FOR SHARE` | Stabilize lifecycle/admission state that must remain unchanged through commit. |
| `NKU` | `FOR NO KEY UPDATE` | Serialize non-key current-state mutation. |
| `U` | `FOR UPDATE` | Delete, key-affecting mutation and strongest owner serialization. |

Lock SQL identifies one table explicitly with `OF`, uses deterministic ordering,
and contains no `NOWAIT` or `SKIP LOCKED`. Missing planned rows are returned to
the caller as protected-state absence; they are not silently ignored.

## Canonical row ordering

Every plan uses this exact global row-class order:

```text
10  ObjectTemplate headers and exact versions
20  DataType headers and exact versions
30  RelationshipDefinition headers and exact versions
40  Object rows
50  factual Relationship rows
```

Within a versioned owner, the header precedes its exact versions and exact
versions are ordered by increasing version number. ObjectTemplate ancestors are
ordered root-to-leaf before descendants. Unrelated owners and ordinary Object or
Relationship rows use UUID ascending as the deterministic tie-break.

A direct-FK target is locked before its existing mutable owner. This applies to
ObjectTemplate parent-version rebind, Object schema change and Relationship
schema change. A child/reference target is locked before the child DML that
creates or reinserts its reference. Duplicate intents coalesce to the strongest
initial mode. A normal path performs no row-lock upgrade and adds no explicit row
lock after DML begins.

The same ordering applies regardless of discovery order or input array order.

## Advisory gates

At most one transaction-scoped advisory gate may appear in a plan. It is always
acquired before any NETAUTO row lock.

| Gate | Stable signed key | Scope |
|---|---:|---|
| `OWNERSHIP_GRAPH_WRITE_GATE` | `0x4E45544100000001` | Ownership edge addition and cycle-safe graph certification. |
| `RELATIONSHIP_DEFINITION_CONFLICT_GATE` | `0x4E45544100000002` | Global Definition equivalence/conflict candidate set. |
| `MODEL_ROOT_DELETE_GATE` | `0x4E45544100000003` | Model-root deletion where mutually referencing roots could invert row order. |

A gate waiter owns no planned NETAUTO row lock. After gate acquisition it reads
the protected predicate from a fresh statement. Gates are internal
serialization mechanisms, not public busy/conflict outcomes.

## Complete initial lock-plan registry

This registry is the current finite authority for all 41 mutation primitives.
`H` denotes a stable header and `V` an exact version row. Dependency targets
follow these reusable initial intents:

```text
explicit new or rebound exact dependency  target H@KS + target V@S
implicit new or rebound exact dependency  target H@S  + target V@S
same-pin physical reinsertion             target H@KS + target V@KS
unchanged physical declaration/reference  no outgoing target lock
removed declaration/reference             no outgoing target lock
historical clone into a new physical row  target H@KS + target V@KS
```

Every target whose reference is created or physically reinserted, together with
every target required by the command's semantic admission, is included in the
complete initial plan. An unchanged reference receives no outgoing target lock.
A removed reference receives no outgoing target lock.

Target acquisition precedes the DML that creates or reinserts the reference. A
changed target set discovered by the protected reread makes the plan stale and
restarts the whole Unit of Work before DML; the current attempt never appends a
lock after DML or upgrades a normal-path row lock.

| Mutation | Gate | Complete initial row plan | Candidate-dependent targets | Fresh recheck / arbitration boundary |
|---|---|---|---|---|
| `DT.C` | `none` | none; the lineage row is new | none | qualified-name uniqueness is final arbitration |
| `DT.CN` | `none` | own `DT.H@NKU`; exact source `DT.V@KS` | exact source | version set, maximum and source eligibility |
| `DT.R` | `none` | own `DT.H@KS`; exact DRAFT `DT.V@NKU` | exact DRAFT | revision, status and complete constraints |
| `DT.P` | `none` | own `DT.H@NKU`; exact DRAFT `DT.V@NKU` | exact DRAFT | revision, status, history and default policy |
| `DT.SD` | `none` | own `DT.H@NKU`; target `DT.V@S` | selected exact version | same-lineage PUBLISHED target and default policy |
| `DT.CD` | `none` | own `DT.H@NKU` | none | current default policy |
| `DT.D` | `none` | own `DT.H@S`; target `DT.V@NKU` | selected exact version | lifecycle/default plus non-locking active-consumer scan |
| `DT.DD` | `none` | own `DT.H@NKU`; exact DRAFT `DT.V@U` | exact DRAFT | revision, status and aggregate membership |
| `DT.DL` | `MODEL_ROOT_DELETE_GATE` | root `DT.H@U` | root lineage | owned aggregate and fresh external blockers; FK RESTRICT arbitrates |
| `DT.DESC` | `none` | own `DT.H@NKU` | none | current lineage and complete metadata value |
| `OT.C` | `none` | parent/component target `OT.H@KS`; new explicit parent `OT.V@S`; implicit parent `OT.H@S + OT.V@S`; property target `DT.H@KS + DT.V@S`, or `DT.H@S + DT.V@S` when implicit | declared parent, component and property targets | name, ancestry, target existence and exact PUBLISHED admission |
| `OT.CN` | `none` | cloned parent/component `OT.H@KS`; cloned parent `OT.V@KS`; cloned property `DT.H@KS + DT.V@KS`; own `OT.H@NKU`; exact source `OT.V@KS` | exact source and all cloned references | version set, source eligibility and target lifetime |
| `OT.R` | `none` | unchanged parent: no target reacquisition; changed explicit parent: `OT.H@KS + OT.V@S`; changed implicit parent: `OT.H@S + OT.V@S`; changed or physically reinserted component declaration: `OT.H@KS`; unchanged physical component declaration: no outgoing target lock; removed component declaration: no outgoing target lock; unchanged property declaration: no outgoing target lock; removed property declaration: no outgoing target lock; same-pin physical reinsertion: `DT.H@KS + DT.V@KS`; explicit new/rebound property: `DT.H@KS + DT.V@S`; implicit new/rebound property: `DT.H@S + DT.V@S`; own `OT.H@KS`; exact DRAFT `OT.V@NKU` | changed or physically reinserted declarations, changed parent selection and semantic-admission targets | revision, status, ancestry and differential target set |
| `OT.P` | `none` | parent target `OT.H@KS + OT.V@S`; property target `DT.H@KS + DT.V@S`; own `OT.H@NKU`; exact DRAFT `OT.V@NKU` | complete effective parent/property dependency set | revision, complete member history, PUBLISHED dependencies and default policy |
| `OT.SD` | `none` | own `OT.H@NKU`; target `OT.V@S` | selected exact version | same-lineage PUBLISHED target and default policy |
| `OT.CD` | `none` | own `OT.H@NKU` | none | current default policy |
| `OT.D` | `none` | own `OT.H@S`; target `OT.V@NKU` | selected exact version | lifecycle/default plus non-locking active-child scan |
| `OT.DD` | `none` | own `OT.H@NKU`; exact DRAFT `OT.V@U` | exact DRAFT | revision, status and aggregate membership |
| `OT.DL` | `MODEL_ROOT_DELETE_GATE` | root `OT.H@U` | root lineage | owned aggregate and fresh external blockers; FK RESTRICT arbitrates |
| `OT.DESC` | `none` | own `OT.H@NKU` | none | current lineage and complete metadata value |
| `OBJ.C` | `none` | selected target `OT.H@KS + OT.V@S`, or `OT.H@S + OT.V@S` when implicit | selected/default ObjectTemplateVersion | default identity, non-abstract lineage and exact PUBLISHED admission |
| `OBJ.RN` | `none` | Object `OBJ@NKU` | exact Object | current complete Object state |
| `OBJ.DC` | `none` | Object `OBJ@NKU` | exact Object | complete properties and exact schema pin; no-op arbitration |
| `OBJ.SC` | `none` | target `OT.H@KS + OT.V@S`; then Object `OBJ@NKU` | exact target ObjectTemplateVersion | fresh source state, forward target and preserve-or-fail migration |
| `OBJ.A` | `OWNERSHIP_GRAPH_WRITE_GATE` | parent Object `OBJ@NKU`; child Object `OBJ@KS`; coalesced and UUID ordered | parent, child and current slot | current ownership fact, effective slot and complete cycle predicate |
| `OBJ.DET` | `none` | parent Object `OBJ@NKU` | parent and requested exact edge | current exact ownership fact; removal takes no child target lock |
| `OBJ.DEL` | `none` | Object `OBJ@U` | exact Object | complete reference blockers; FK RESTRICT arbitrates |
| `RD.C` | `RELATIONSHIP_DEFINITION_CONFLICT_GATE` | endpoint `OT.H@KS`; property target `DT.H@KS + DT.V@S`, or `DT.H@S + DT.V@S` when implicit | endpoint lineages and initial properties | certified Definition set, topology and exact PUBLISHED dependencies |
| `RD.RN` | `RELATIONSHIP_DEFINITION_CONFLICT_GATE` | Definition `RD.H@KS` | exact Definition | complete certified Definition/Resolution set after the gate |
| `RD.CN` | `none` | cloned property `DT.H@KS + DT.V@KS`; own `RD.H@NKU`; exact source `RD.V@KS` | exact source and all cloned property targets | version set, source eligibility and target lifetime |
| `RD.R` | `none` | unchanged property declaration: no outgoing target lock; removed property declaration: no outgoing target lock; same-pin physical reinsertion: `DT.H@KS + DT.V@KS`; explicit new/rebound property: `DT.H@KS + DT.V@S`; implicit new/rebound property: `DT.H@S + DT.V@S`; own `RD.H@KS`; exact DRAFT `RD.V@NKU` | changed or physically reinserted properties and semantic-admission targets | revision, status, complete history and differential target set |
| `RD.P` | `none` | property target `DT.H@KS + DT.V@S`; own `RD.H@NKU`; exact DRAFT `RD.V@NKU` | complete property dependency set | revision, complete property history, PUBLISHED dependencies and default policy |
| `RD.SD` | `none` | own `RD.H@NKU`; target `RD.V@S` | selected exact version | same-Definition PUBLISHED target and default policy |
| `RD.CD` | `none` | own `RD.H@NKU` | none | current default policy |
| `RD.D` | `none` | own `RD.H@S`; target `RD.V@NKU` | selected exact version | lifecycle and default; existing factual pins remain valid |
| `RD.DD` | `none` | own `RD.H@NKU`; exact DRAFT `RD.V@U` | exact DRAFT | revision, status and aggregate membership |
| `RD.DL` | `MODEL_ROOT_DELETE_GATE` | root Definition `RD.H@U` | root Definition | owned aggregate and fresh factual/external blockers; FK RESTRICT arbitrates |
| `REL.C` | `none` | Definition `RD.H@KS` for explicit selection or `RD.H@S` for implicit selection; exact target `RD.V@S`; endpoint Objects `OBJ@KS` in UUID order | selected/default RDV and endpoint pair | default, exact PUBLISHED schema, endpoints, complete closure and exact-view ownership |
| `REL.DC` | `none` | factual Relationship `REL@NKU` | exact Relationship | complete exact pin/properties/closure; no-op arbitration |
| `REL.SC` | `none` | Definition `RD.H@KS`; target `RD.V@S`; factual Relationship `REL@NKU` | exact target RelationshipDefinitionVersion | fresh source fact, forward PUBLISHED target and preserve-or-fail migration |
| `REL.DEL` | `none` | factual Relationship `REL@U` | exact Relationship | exact-ID presence, complete fact and deletion event state |

All row identities above are sorted through the global class and intra-class
rules before acquisition. CREATE_NEXT holds every cloned reference for physical
lifetime; differential declaration replacement holds every inserted or
reinserted target before child DML. Active-consumer reverse scans remain
non-locking so dependency ownership cannot invert into consumer ownership.

## Versioned model realization

### Allocation and DRAFT generations

CREATE_NEXT serializes on the stable lineage header, rereads the version set and
allocates `max(existing) + 1`. Cloned exact dependency targets receive lifetime
holds in the initial plan.

REVISE, PUBLISH and DELETE_DRAFT lock the stable header before the exact DRAFT,
stabilize the generation and recheck `expected_revision` and status. Differential
declaration replacement locks every target for a physically inserted or
reinserted declaration before child DML and performs deterministic delete/upsert
ordering. Unchanged and removed declarations take no outgoing target lock. The
replacement never creates a transient logical gap visible to a competing target
delete.

### Publication, defaults and active graph

Publication re-certifies the complete version/member history while holding the
lineage/version authorities required by `VH`. Exact direct dependencies are held
`FOR SHARE` and rechecked PUBLISHED. Default set/clear, first publication and
deprecation serialize the stable header/default predicate.

A PUBLISHED consumer and dependency deprecation rendezvous through compatible
header/version locks and a fresh reverse active-consumer scan. The scan does not
invent a reverse-dependency table.

### Root deletion and reference lifetime

Model-root deletion acquires `MODEL_ROOT_DELETE_GATE`, then the complete aggregate
in canonical order and performs fresh blocker reads. Cross-aggregate references
remain protected by target-before-child planning and PostgreSQL `RESTRICT`.
CASCADE removes only owned child state after semantic admission.

## Object and ownership realization

The Object row is the concurrency owner for its complete current exact schema and
canonical property map. RENAME, DATA_CHANGE, SCHEMA_CHANGE and DELETE reread it
after locking. Real transitions and their lifecycle event sets commit atomically;
a DATA_CHANGE no-op performs neither UPDATE nor event insertion.

ATTACH plans the ownership gate first, then all relevant parent/child and template
rows. It certifies one current slot and a cycle-free graph from a fresh snapshot.
The `object_components` child primary key is final single-owner arbitration.
DETACH never removes a different edge and does not acquire the graph gate because
removal cannot create a cycle.

## RelationshipDefinition realization

CREATE and RENAME use `RELATIONSHIP_DEFINITION_CONFLICT_GATE` and certify the
complete Definition/Resolution set. Resolution names are non-key metadata;
Definition identity and membership remain stable.

Exact-version mutations lock Definition header before exact version. CREATE_NEXT,
REVISE, PUBLISH, defaults, deprecation and DRAFT deletion follow the versioned
model rules above. RDV property publication uses history recertification and
exact DataTypeVersion admission/lifetime holds.

Definition deletion uses the model-root gate, locks its aggregate and relies on
non-cascading factual and cross-model references as blockers. It does not use the
conflict gate: removing a Definition cannot introduce a conflicting candidate.

## Factual Relationship realization

CREATE stabilizes Resolution, endpoint Objects, Definition header, selected exact
RDV and exact DTV dependencies before DML. It derives one deterministic complete
runtime closure and inserts header, closure and CREATED events atomically.

The exact runtime-view primary key
`(resolution_id, from_object_id, to_object_id)` is final factual arbitration.
After any collision the failed transaction is rolled back before classification.
If a current owner exists, the loser reports `relationship_fact_conflict`. If the
owner disappeared, the approved fresh-UoW restart path may rederive the fact.

DATA_CHANGE and SCHEMA_CHANGE lock the factual Relationship row, reread exact pin
and complete properties, derive from that state and update the one factual row.
SCHEMA_CHANGE also stabilizes the exact target PUBLISHED RDV and dependencies.
DELETE locks the exact factual ID and never targets a recreated equivalent ID.
Closure rows remain unchanged for data/schema changes and cascade only after
successful factual DELETE admission.

Relationship event metadata is captured through one coherent statement. Object
or Resolution rename may progress where required; the event set sees one
committed metadata observation and is never half-old/half-new.

## Bounded whole-UoW restart

The maximum is exactly four total attempts. Restart is permitted only for:

```text
LockPlanStale
exact-view collision whose observed owner no longer exists
```

Every restart uses a fresh connection/Unit of Work and redoes discovery,
planning, locking, validation and candidate derivation. It is forbidden for:

```text
semantic/application failure
known current-owner uniqueness conflict
unknown constraint or SQLSTATE
40P01 deadlock
40001 serialization failure
```

Constraint classification occurs only after rollback and uses a finite mapping of
known SQLSTATE plus exact constraint name. Unknown names or failure shapes cross
the safe internal-error boundary.

## Wait-for graph and parallelism

Supported paths have no row-to-gate edge, use one gate at most, acquire canonical
row classes once and order target before owner/child. The resulting supported
wait-for graph is acyclic by construction. Any observed supported-path `40P01` is
an architecture or implementation defect, never a transient success path.

Locks protect semantic predicates, not a goal of maximum serialization. Distinct
lineages, exact versions, factual Relationships and metadata operations make
progress where the matrix classifies them independent. Physical
over-serialization is permitted only when documented and must not be reinterpreted
as a domain invariant.

## Verification boundary

The 83 stable scenarios and 21 predicates in
[`verification-concurrency-registry.md`](verification-concurrency-registry.md)
prove blocking, progress, arbitration, rollback, restart and deadlock absence on
real PostgreSQL. Timeouts are hang guards; sleep and automatic rerun are not
ordering or correctness authorities.
