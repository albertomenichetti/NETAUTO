# M4 — Initial Discovery Trace

**Status:** WIP / NON-NORMATIVE

**Role:** exploration aid only. This document records the initial problem framing, workload assumptions, evidence and hypotheses that motivated M4. It does not define the M4 contract, TO-BE architecture, implementation scope or acceptance criteria.

The delivered AS-IS under `docs/architecture/` remains authoritative until M4 explicitly freezes a TO-BE delta.

## 1. Initial motivation

M4 starts from a workload-oriented observation about the current NETAUTO kernel:

```text
MODEL PLANE
    DataType
    ObjectTemplate
    RelationshipDefinition

    expected mutation frequency: low / very low

DATA PLANE
    Object
    ownership
    factual Relationship

    expected operation frequency: high / very high
```

This is currently a workload hypothesis rather than a delivered semantic requirement, but it provides the lens for evaluating trade-offs.

The key design question is therefore not whether every operation can be made uniformly cheaper. It is whether NETAUTO can deliberately move computational, certification and persistence cost from frequent data-plane paths to rare model-plane mutation paths when doing so preserves correctness and materially reduces runtime work.

A desirable trade-off may therefore make, for example, `ObjectTemplate.PUBLISH` more expensive if it substantially reduces the recurring cost of `Object.CREATE`, `Object.DATA_CHANGE`, ownership operations or `Relationship.CREATE`.

## 2. Generic M4 objective — working formulation

A possible generic objective for M4 is:

> Re-evaluate the complete currently defined REST business-operation surface and, consequently, the relational persistence model and runtime data-access model, with the goal of denormalizing/materializing where doing so makes data loading materially more efficient and of caching locally every semantic construct whose correctness does not require distributed cache-coherency protocols.

This wording is intentionally broad and does not yet prescribe closure tables, compiled schemas, cache implementation or individual operation changes.

The investigation should remain operation-driven: first identify what each current operation actually reads, derives, locks and writes; only then select persistence and caching changes that have systemic value.

## 3. Emerging architectural hypothesis

The initial exploration suggests a useful separation:

```text
CURRENT MUTABLE TRUTH
────────────────────────────────
PostgreSQL

examples:
    lifecycle/admission state
    default pointers
    current Object state
    current Relationship state
    ownership facts
    mutable display metadata
    concurrency/reference lifetime


IMMUTABLE KNOWLEDGE
────────────────────────────────
durable materialization where useful
            +
worker-local cache

examples under investigation:
    stable ObjectTemplate ancestry
    exact ObjectTemplateVersion ancestry
    exact effective schemas
    exact DataType semantics
    compiled runtime validators
    other derived facts immutable for their key
```

A concise form of the hypothesis is:

```text
PostgreSQL = current truth
local cache = immutable knowledge
```

The local cache must never become an authority for current existence, lifecycle eligibility, current default selection or another fact that can change for the same key.

## 4. Cache-coherency boundary

The intended cache exploration is deliberately narrower than a generic distributed cache design.

Candidate worker-local entries should satisfy the property:

> Once the cache key denotes the intended semantic identity, the cached payload cannot become semantically stale for that identity.

Examples currently considered strong candidates:

```text
(ObjectTemplate id, exact version)
    -> immutable effective schema / compiled Object validator

(DataType id, exact version)
    -> immutable primitive + exact constraints / compiled validator

(RelationshipDefinition id, exact version)
    -> immutable exact property schema

ObjectTemplate stable lineage id
    -> stable ancestor chain, if represented in the immutable direction
```

Non-candidates include current facts such as:

```text
default_version
current PUBLISHED vs DEPRECATED admission state
mutable description
RelationshipResolution current name
complete descendant sets that can grow through future lineage creation
```

The cache model currently envisioned for exploration is intentionally simple:

```text
per worker / process
lazy population
process restart -> empty cache
local eviction allowed as a performance policy
no correctness dependence on cache presence
no TTL required for semantic freshness
no Redis / pub-sub / distributed invalidation required
```

A cache miss should reload authoritative committed information from PostgreSQL. A cache hit should remove repeated immutable-model reads or recomputation, never current-state admission checks.

## 5. Candidate durable denormalization/materialization directions

No item in this section is yet a decision.

### 5.1 Stable ObjectTemplate ancestry

A candidate closure representation:

```text
object_template_ancestry

    descendant_template_id
    ancestor_template_id
    depth
```

with reflexive rows such as `(T,T,0)`.

Potential value:

- replace repeated stable-lineage recursive traversal;
- support ancestor/descendant compatibility queries efficiently;
- simplify selected lock-planning and Relationship capability paths;
- provide an efficient cold-load source for immutable stable ancestry.

The current ObjectTemplate parent lineage is stable for the lineage lifetime, which makes this materially different from a frequently reparented general-purpose tree.

### 5.2 Exact ObjectTemplateVersion ancestry

A distinct candidate exact closure:

```text
object_template_version_ancestry

    descendant_template_id
    descendant_version
    ancestor_template_id
    ancestor_version
    depth
```

Stable ancestry and exact ancestry should be treated as different semantic relations. Deriving stable ancestry by scanning exact-version ancestry with `DISTINCT` is not currently considered attractive because it couples two different identities and expands the read set unnecessarily.

### 5.3 Effective-schema materialization

A stronger candidate is to materialize the result that data-plane operations actually need rather than only the exact ancestry required to derive it.

For an exact non-DRAFT ObjectTemplateVersion, a durable runtime-oriented projection could contain enough information to load in one statement:

```text
effective properties
    declaring_template_id
    name
    position / semantic ordering data where required
    value_mode
    required
    migration_default where relevant
    datatype_id
    datatype_version
    primitive type / constraints, directly or via a join

effective components
    declaring_template_id
    name
    target_template_id
```

The exact physical shape remains open. The important hypothesis is that publication/certification can perform expensive derivation once and runtime operations can consume an immutable result many times.

Working principle:

```text
compile / certify once on model plane
consume many times on data plane
```

## 6. Relationship with M2 and M3

M4 should preserve delivered semantic guarantees unless its contract and frozen architecture explicitly redefine them, but it may reconsider realization mechanisms.

Examples:

```text
PRESERVE AS REQUIRED GUARANTEES
    concurrency safety predicates
    exact binding semantics
    reference lifetime
    atomic mutation + lifecycle events
    avoidance of unnecessary REPEATABLE READ
    bounded failure behavior

ALLOW M4 TO RE-EVALUATE, IF EXPLICITLY DESIGNED
    current lock sets
    discovery/fresh-reread mechanisms
    ancestry traversal used only for lock ordering
    one-statement GET realization introduced by M3
    normalized-only persistence shapes
    repeated runtime semantic derivation
```

M3's important result is not assumed to be that one SQL statement is inherently optimal forever. The result to preserve is coherent reads without unnecessary multi-statement `REPEATABLE READ` transactions. M4 may investigate whether a read can safely combine one coherent observation of mutable current facts with immutable exact knowledge loaded from durable materialization or worker-local cache.

Working phrase:

```text
mutable snapshot + immutable knowledge
```

## 7. Operation-by-operation discovery method

The current business surface has 63 operations: 41 mutations and 22 public business GETs. M4 discovery should evaluate them individually before fixing a target architecture.

For each operation, record at least:

```text
workload classification
current mutable facts read
immutable exact/stable facts read
derived immutable work repeated at runtime
SQL statement count / round trips
query growth variables
recursive traversals
lock set and lock duration
transaction duration contributors
current correctness guarantees
candidate durable denormalization/materialization
candidate worker-local cache use
expected cold-cache path
expected warm-cache path
open concurrency questions
```

A working matrix may eventually use columns such as:

| Operation | Workload | Mutable current state | Immutable reads | Derived work | SQL/round trips | Locks | Candidate direction |
|---|---|---|---|---|---|---|---|
| `OBJ.C` explicit | hot | exact OTV admission | effective schema / DTV semantics | exact-chain/schema rebuild | measured/derived | OTV-related | materialize/cache |
| `OBJ.C` implicit | hot | default + exact OTV admission | same | same | TBD | TBD | same + current-default admission |
| `OBJ.DC` | very hot | Object state | pinned schema | TBD | TBD | Object | cache |
| `OBJ.A` | hot | Objects/ownership | effective slots/stable ancestry | TBD | TBD | gate/Object | closure/cache |
| `REL.C` | hot | RD admission + Objects | topology/schema/ancestry | runtime closure derivation | TBD | TBD | materialize/cache |
| model publication | rare | model current state | dependencies | certification | TBD | TBD | may absorb more cost |

## 8. First practical case — `Object.CREATE` with explicit exact version

The first inspected path is:

```text
POST /objects
    template_id = T
    template_version = 7
```

### 8.1 Semantic observation

For exact `(T,7)`:

- if it is PUBLISHED or DEPRECATED, the exact version snapshot is immutable;
- its exact parent-version chain is immutable;
- every non-DRAFT ancestor exact snapshot in that chain is immutable;
- local/effective declarations for those exact snapshots are immutable;
- every exact DataTypeVersion pinned by those property declarations is immutable in semantic content;
- lifecycle/admission is different: `T/7` can transition from PUBLISHED to DEPRECATED, so whether it may receive a new direct Object binding is current mutable truth.

Therefore candidate validation and current binding admission can potentially be separated:

```text
cache / immutable knowledge
    -> is the candidate Object semantically valid for exact T/7?

PostgreSQL UoW / current truth
    -> may a new Object bind to T/7 now and through commit?
```

If validation succeeds from cache but `T/7` is deprecated before admission, the UoW simply fails. The cached schema has not become incorrect.

### 8.2 Current AS-IS cost — working evidence

Inspection of the current implementation suggests the successful first-attempt path performs repeated target loads, lock-plan ancestry loading, effective exact-chain reconstruction and per-distinct-DataType loads before the two actual writes.

Using:

```text
d = number of exact ancestors above the selected leaf OTV
u = number of distinct exact DataTypeVersions used by the effective properties
```

working call-count analysis produced:

```text
17 + 4d + u
```

SQL `execute` calls on the successful path, excluding the commit command itself and external pool/protocol details.

Only two of these are the essential business writes:

```text
INSERT objects
INSERT object_lifecycle_events (CREATED)
```

This formula is discovery evidence derived from the current code and must be revalidated by instrumentation or focused PostgreSQL evidence before it becomes an acceptance baseline.

Important observed contributors include:

- repeated full loading of the selected ObjectTemplateVersion;
- stable ancestry query performed by the generalized lock planner;
- repeated exact parent-chain loading;
- effective schema reconstruction for every Object creation;
- individual exact DataTypeVersion loads;
- repeated validation that already-certified persisted DataType constraints remain canonical;
- keeping the mutation transaction and exact-version admission lock open while performing immutable schema reconstruction and candidate validation.

### 8.3 Candidate warm-cache shape

A possible target worth proving, not yet adopting, is:

```text
OUTSIDE MUTATION TRANSACTION
    lookup CompiledEffectiveSchema[(T,7)]
    validate/canonicalize caller properties locally

INSIDE MUTATION TRANSACTION
    acquire fresh protected exact OTV admission
    require current status PUBLISHED
    INSERT Object
    INSERT lifecycle CREATED
    COMMIT
```

The important change is that effective-schema interpretation no longer occurs while the lifecycle-sensitive admission lock is held.

### 8.4 Candidate cache-miss shape

If stable/exact ancestry and the effective schema are durably materialized, the cold worker path could potentially become:

```text
cache miss (T,7)
    -> one PostgreSQL statement loads the complete immutable effective runtime schema
    -> compile local runtime representation
    -> cache[(T,7)]
    -> validate candidate locally
    -> enter the short current-admission/write UoW
```

The desired database-round-trip property is therefore potentially `O(1)` with respect to inheritance depth for cache fill, while payload size naturally remains proportional to the effective schema size.

### 8.5 Explicit-version admission hypothesis

For an explicit version, the current default pointer is irrelevant. A strong hypothesis is that the mutation UoW can use the exact ObjectTemplateVersion row itself as the admission anchor.

A locking read conceptually equivalent to:

```sql
SELECT status
FROM object_template_versions
WHERE template_id = :template_id
  AND version = :version
FOR SHARE;
```

could simultaneously establish current existence, read lifecycle status and hold PUBLISHED admission stable through commit.

If this is sufficient, the warm-cache path could approach:

```text
1 exact OTV admission/lock statement
1 Object INSERT
1 lifecycle INSERT
COMMIT
```

This would be three SQL statements plus commit, independent of exact inheritance depth and number of pinned DataTypeVersions.

### 8.6 Open concurrency point: stable-header lock

The current explicit `OBJ.C` lock plan includes both stable ObjectTemplate header `KEY SHARE` and exact OTV `SHARE`.

A current M4 hypothesis is that the stable-header lifetime lock may be redundant for explicit-version Object creation if all of the following remain true:

- the exact OTV row is locked for admission through commit;
- OTV is aggregate-owned by the stable ObjectTemplate lineage;
- Object has a `RESTRICT` foreign key to the exact OTV;
- lineage deletion cascades only aggregate-owned OTV state after admission;
- PostgreSQL lock/FK interaction preserves the required `OBJ.C × OT.DELETE_LINEAGE` reference-lifetime outcomes.

This is **not a decision**. It requires deterministic real-PostgreSQL concurrency proof before any M4 architecture could rely on it.

## 9. Questions M4 discovery must answer

The initial exploration leaves several open questions:

1. Which of the 63 operations materially benefit from stable ancestry, exact ancestry or effective-schema materialization?
2. Is exact-version ancestry independently useful once effective schemas are materialized, or should it exist only where another operation needs it directly?
3. Which effective-schema data should be duplicated into the materialization versus joined from immutable exact DataType rows during one cache-fill query?
4. Should compiled local validators contain precompiled regex/enumeration lookup structures or only decoded semantic DTOs?
5. Which stable-lineage facts are safe for process-lifetime caching, and which directions of a relation can grow over time and therefore are not immutable snapshots?
6. Which current M2 lock intents are semantically necessary versus conservative realization artifacts after immutable-model work leaves the UoW?
7. Which M3 one-statement reads can remain as-is, and which could be simpler/faster under a mutable-snapshot-plus-immutable-cache contract?
8. What durable consistency mechanism guarantees that materialized derived rows are created/updated atomically with the rare model-plane mutation that makes them authoritative inputs?
9. What verification should measure cold-cache equivalence, warm-cache equivalence, query-count bounds, lock-hold duration and deterministic concurrency behavior?
10. What explicit non-goals are needed to prevent M4 from becoming an unconstrained general performance rewrite?

## 10. Current non-decisions

At this discovery stage M4 has **not** decided to:

- add any particular closure table;
- materialize effective schemas in a particular relational or JSON shape;
- introduce any cache library;
- introduce Redis or another distributed cache;
- remove any current lock;
- weaken any M2 concurrency predicate;
- remove M3's one-statement GET rule globally;
- change any public REST operation or failure contract;
- change isolation levels;
- modify schema or migrations;
- implement software.

All such choices require a frozen M4 contract and architecture set before implementation.

## 11. Immediate discovery continuation

Continue with concrete operation analysis rather than solution-first schema design.

The next useful cases are expected to include:

```text
Object.CREATE implicit version
Object.DATA_CHANGE
Object.ATTACH
Relationship.CREATE
```

with special attention to where they repeatedly consume exact immutable model information and how much of that work could be moved to rare model-plane certification/materialization plus worker-local immutable caches.
