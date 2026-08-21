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
an initial read snapshot. Multi-statement coherent public reads use
`REPEATABLE READ READ ONLY`; a single authoritative projection statement may use
its statement snapshot.

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

Rows are sorted by a fixed class order:

```text
ObjectTemplate lineage headers and ancestors
DataType lineage headers
RelationshipDefinition headers
Object headers
Relationship headers
exact version rows within their owner
owned declaration / closure authorities where explicitly locked
```

Within a class, owner UUID, exact version and remaining key components use a
stable ascending order. ObjectTemplate ancestors are ordered root-to-leaf before
the dependent lineage. Target identity is locked before an existing owner when a
direct FK is rebound. A child/reference target is locked before child DML.

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

## Versioned model realization

### Allocation and DRAFT generations

CREATE_NEXT serializes on the stable lineage header, rereads the version set and
allocates `max(existing) + 1`. Cloned exact dependency targets receive lifetime
holds in the initial plan.

REVISE, PUBLISH and DELETE_DRAFT lock the stable header before the exact DRAFT,
stabilize the generation and recheck `expected_revision` and status. Differential
declaration replacement locks retained/inserted targets before child DML and
performs deterministic delete/upsert ordering. It never creates a transient
logical gap visible to a competing target delete.

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
