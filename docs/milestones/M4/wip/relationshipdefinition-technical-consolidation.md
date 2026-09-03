# M4 WIP — RelationshipDefinition technical discovery consolidation

**Status:** ACTIVE TECHNICAL CONSOLIDATION / SUPPORTING LEDGER / SUBORDINATE TO `relationshipdefinition.md` / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This file persists the RelationshipDefinition technical-discovery checkpoints ratified during the current M4 consolidation sweep so they are not left only in conversation state.

It is intentionally **not** a competing family owner. The single family owner remains:

```text
relationshipdefinition.md
```

At the end of the technical sweep, the contents of this ledger must be absorbed coherently into that owner and this supporting file may then be retired or reduced to historical evidence.

Where this ledger records a later explicit revalidation that conflicts with older wording still present in the owner or distributed discovery files, the later checkpoint is marked clearly so the pending owner absorption cannot silently restore the stale assumption.

Final SQL, DDL, PK/FK/UNIQUE/index choices, lock/wait/retry/deadlock protocols and migration/backfill remain architecture work unless explicitly stated otherwise.

---

# 1. `relationship_definition_space` classification — RATIFIED

`relationship_definition_space` is the complete current certified derived semantic closure for one RelationshipDefinition.

Logical source:

```text
compact RelationshipDefinition stable topology/names
+
current stable ObjectTemplate ancestry
```

Conceptual invariant:

```text
MaterializedSpace(D)
 ==
Expand(
    D.symmetric,
    D.endpoint_a_template_id,
    D.endpoint_b_template_id,
    D.name_a_to_b,
    D.name_b_to_a,
    current stable ObjectTemplate descendant sets
)
```

It is independent from:

```text
RelationshipDefinition.default_version
RDV lifecycle/status
RDV revision
RDV properties
```

The space exists from RelationshipDefinition CREATE even though v1 is DRAFT and `default_version = null`, because semantic-cell ownership belongs to the stable Definition rather than to a published exact version.

RelationshipDefinition-owned effects:

```text
CREATE Definition
    -> create complete space

CREATE_NEXT
REVISE
PUBLISH
SET_DEFAULT
CLEAR_DEFAULT
DEPRECATE
DELETE_DRAFT
    -> no space change

DELETE Definition
    -> remove owned space
```

Stable ObjectTemplate ancestry changes may require maintenance of the derived space, but that is an external maintenance dependency rather than a reason to move ObjectTemplate into the active RelationshipDefinition review.

Classification:

```text
derived/materialized trusted current model knowledge
NOT a second semantic authority
may be relational arbitration authority for exact semantic-cell ownership
```

Physical PK/UNIQUE/constraint realization remains architecture work.

## 1.1 Coherence invariant — RATIFIED

There must be no committed state in which stable ObjectTemplate ancestry has changed while `relationship_definition_space` remains stale.

```text
relationship_definition_space
    must always be coherent with
compact RelationshipDefinition state
+
current stable ObjectTemplate ancestry
```

A descendant lineage that appears only through derived expansion must not become an independent root-lineage lifetime blocker merely because it is present in the materialized space.

## 1.2 RelationshipDefinition consumers — RATIFIED

Within the RelationshipDefinition family, the space is **not** a general read model.

```text
CREATE Definition
    -> YES
       candidate-cell derivation
       semantic conflict arbitration
       complete space persistence

GET Definition detail
    -> NO full space scan
    -> use endpoint roots + stable ancestry descendant sets

LIST Definitions
GET/LIST versions
CREATE_NEXT
REVISE
PUBLISH
SET_DEFAULT
CLEAR_DEFAULT
DEPRECATE
DELETE_DRAFT
    -> NO space

DELETE Definition
    -> owned derived cleanup only
```

Primary roles:

```text
WRITE / ARBITRATION on CREATE
OWNED CLEANUP on DELETE
EXTERNAL coherence maintenance when stable ancestry changes
```

---

# 2. CREATE RelationshipDefinition — technical discovery CLOSED except concurrency/physical realization

## 2.1 Semantic preparation boundary — RATIFIED

CREATE uses the same broad separation already established for Object commands:

```text
STEP 1 — current dependency resolution
STEP 2 — semantic preparation outside mutation UoW
STEP 3 — short mutation UoW / final current admission / persistence
```

### STEP 1 — exact dependency selection

For every property:

```text
explicit datatype_version
    -> select exact DTV

omitted datatype_version
    -> resolve current DataType.default_version
    -> materialize one exact DTV pin
```

Once an omitted default has resolved to an exact DTV, a later default change must **not** retarget the in-flight command.

Endpoint ObjectTemplate roots are also resolved as current existing lineages.

### STEP 2 — complete DTV semantic preparation

For **all** selected exact DataTypeVersions:

```text
load semantic payload
compile required DataType semantics/validators
make validation semantics READY
```

Then build and validate the complete v1 DRAFT property candidate and compact RelationshipDefinition candidate.

This work stays outside the mutation UoW.

CREATE v1 has no prior committed RelationshipDefinition property history, therefore:

```text
NO published/deprecated history lookup for v1
```

### STEP 3 — short mutation UoW

Final mutable/current admission includes at least:

```text
endpoint roots still current/existing
all newly selected exact DTV pins still admissible/PUBLISHED
```

The exact DTV semantic payload is **not** reloaded or recompiled inside the mutation UoW.

## 2.2 Endpoint-topology validation boundary — RATIFIED

CREATE does not load the full ObjectTemplate graph or descendant sets into the worker.

For symmetric topology validation the worker only needs the stable relation between endpoint roots A/B:

```text
A == B
A ancestor-of B
B ancestor-of A
neither ancestry direction
```

The existing stable ObjectTemplate ancestry cache may answer that bounded predicate. With single inheritance:

```text
symmetric + A == B
    -> identical spaces: valid

symmetric + one root is a strict ancestor of the other
    -> distinct-but-overlapping: invalid

symmetric + neither is ancestor of the other
    -> disjoint: valid
```

The stable A/B ancestry relation need not be re-proved in the final mutation UoW if both endpoints still exist; endpoint existence remains current PostgreSQL admission.

## 2.3 Candidate semantic closure generation — RATIFIED

Potentially large candidate semantic cells must remain DB-internal:

```text
DB -> worker -> DB candidate closure
    -> NO

PostgreSQL set-based derivation from
    compact candidate
    + object_template_ancestry
    -> YES
```

The worker owns the compact candidate and bounded failure information, not the Cartesian exact-template cell set.

## 2.4 Conflict path — RATIFIED

For an intrinsically valid candidate:

```text
CandidateSpace(D)
INTERSECT
current relationship_definition_space
```

is the conflict test.

If non-empty, the ordinary arbitration path needs at most one witness:

```text
existing relationship_definition_id
from_template_id
name
to_template_id
```

matching the reviewed REST error:

```text
409 relationship_definition_conflict
```

No conflict count, full conflicting Definition load, all-cell enumeration or equivalence-specific second path is required.

Candidate-internal duplication/malformed closure remains intrinsic semantic validation, not a current ownership conflict.

The mechanism that makes this correct under concurrent CREATE operations remains a concurrency/physical handoff.

## 2.5 Logical write set and cost invariant — RATIFIED

CREATE logically writes:

```text
relationship_definitions
last_versions
relationship_definition_versions
relationship_definition_properties
relationship_definition_space
```

The first exact version initializes the shared no-reuse allocator consistently with version 1.

Target DML cost invariant for P properties and N semantic cells:

```text
application persistence round trips
    -> bounded / constant in P and N

physical row writes
    -> O(P + N)
```

Required direction:

```text
bulk property persistence
set-based DB-internal space derivation/persistence
```

Forbidden hot shape:

```text
one statement per property
one statement per semantic cell
```

No requirement exists to compress the whole model-plane CREATE into one mega-statement; the requirement is bounded statement count and no N+1.

## 2.6 CREATE cache boundary — RATIFIED

CREATE may reuse/fill immutable exact-DTV semantic/compiled cache entries.

It does **not** publish a RelationshipDefinitionVersion immutable cache entry because the newly created v1 is DRAFT.

It does not create a worker cache for `relationship_definition_space`.

No dedicated stable RelationshipDefinition topology cache is justified by CREATE itself without a concrete consumer.

---

# 3. RelationshipDefinition GET family — technical checkpoints

## 3.1 LIST Definitions — RATIFIED

The compact Definition model removes the AS-IS Resolution row multiplication.

Target path:

```text
relationship_definitions D
JOIN endpoint ObjectTemplate root A
JOIN endpoint ObjectTemplate root B
keyset on D.id
LIMIT limit + 1
```

One DB row corresponds to one Definition. The worker performs only bounded perspective projection:

```text
asymmetric
    -> 2 perspectives

symmetric + A != B
    -> 2 reciprocal perspectives with same name

symmetric + A == B
    -> 1 perspective
```

No `relationship_definition_space`, ancestry, version, DataType or worker-cache read is needed.

Qualified endpoint names are resolved by the same bounded query; no endpoint N+1.

## 3.2 GET Definition detail — RATIFIED

The detail requires factored applicability, therefore the correct cost is:

```text
O(|Desc(A)| + |Desc(B)|)
```

not:

```text
O(|Desc(A)| * |Desc(B)|)
```

One authoritative PostgreSQL read obtains:

```text
compact Definition
endpoint-root references
complete current descendants of each distinct endpoint root
```

using `object_template_ancestry` by `ancestor_template_id` plus descendant ObjectTemplate references.

If A == B the descendant set is obtained once and reused.

The GET must not read `relationship_definition_space` and refactor an N×M cell set back into two arrays.

The existing worker ancestry cache is not authoritative for complete **descendant enumeration** because new descendants can appear over time; PostgreSQL remains the current source for this read.

## 3.3 LIST exact versions — RATIFIED

Keep one root-preserving authoritative PostgreSQL statement that distinguishes:

```text
Definition absent -> 404
Definition present + no matching versions -> empty page
```

Projection is only:

```text
version
revision
status
```

with optional status predicate, keyset by version and `limit + 1`.

No properties, DataType, topology, space, ancestry or cache involvement.

## 3.4 GET exact RDV — RATIFIED

Public exact-version GET stays PostgreSQL-authoritative rather than bifurcating into cache-hit/cache-miss DTO paths.

One statement projects:

```text
Definition existence sentinel
exact RDV header
ordered properties
DataType lineage namespace/name for qualified_name
```

Property payload:

```text
name
internal ordinal
value_mode
datatype_id
datatype_version
DataType namespace/name
```

The public DTO omits ordinal but preserves its order.

No DataTypeVersion semantic payload or validator compilation is required for this read.

The immutable RDV cache is runtime-oriented and is not a required public GET source.

---

# 4. CREATE_NEXT RelationshipDefinitionVersion — technical discovery CLOSED except concurrency/physical realization

## 4.1 Immutable source and preferred cache path — RATIFIED

Eligible source state:

```text
PUBLISHED | DEPRECATED
```

therefore the complete source declaration snapshot is immutable.

Preferred direction is to exploit the immutable RDV cache and build the next DRAFT in application/domain state outside the mutation UoW rather than using DB-side `INSERT ... SELECT` as the primary clone mechanism.

Conceptual cache facets:

```text
ImmutableRelationshipDefinitionVersionCache[(definition_id, version)]

snapshot READY
    ordered properties
        name
        ordinal
        datatype_id
        datatype_version
        value_mode

compiled READY
    RuntimePropertySpec / validators / DTV semantic linkage
```

CREATE_NEXT requires only `snapshot READY`.

On cache miss:

```text
bounded cold load of exact immutable snapshot
-> publish snapshot facet
```

No DTV semantic load/compile is required merely to clone.

## 4.2 Prepared next candidate — RATIFIED

Outside the mutation UoW the application may build:

```text
PreparedRelationshipDefinitionVersion
    status = DRAFT
    revision = 1
    properties = exact ordered source snapshot clone
    version = not allocated yet
```

The new version number remains unassigned until the shared `last_versions` allocator is advanced in the mutation UoW.

## 4.3 Final UoW — RATIFIED at logical level

Short mutation UoW must establish at least:

```text
Definition still exists
source exact version still exists
source.status still in {PUBLISHED, DEPRECATED}
allocate next version through last_versions
bulk insert new RDV + cloned properties
```

No source-property reread, DTV reread, DTV compilation or historical continuity validation is required inside the UoW.

A concurrent:

```text
PUBLISHED -> DEPRECATED
```

of the source is semantically harmless because both source states are eligible.

Source/root disappearance remains a concurrency realization concern.

The new DRAFT is not published into immutable RDV cache.

---

# 5. REVISE RelationshipDefinitionVersion — technical discovery CLOSED except concurrency/physical realization

## 5.1 Preparation boundary — RATIFIED

REVISE starts from the current exact DRAFT snapshot so the application knows:

```text
status
revision
complete ordered current properties
```

This supports early target-state/revision checks, classification of unchanged vs new/changed exact bindings, and declaration-delta computation.

Outside the mutation UoW:

```text
complete request properties[]
    -> resolve every exact DTV pin
       explicit version or current DataType.default_version
    -> once resolved, default changes do not retarget the candidate
    -> load + compile ALL selected exact DTV semantics
    -> build/validate complete replacement candidate
```

Lifecycle admission differs by binding class:

```text
unchanged exact DTV pin
    -> semantic load/compile YES
    -> current PUBLISHED requirement NO

new property / changed exact DTV pin
    -> semantic load/compile YES
    -> current PUBLISHED admission YES
```

Omitted `datatype_version` is always a fresh default-selection instruction, not shorthand for preserving the current exact pin.

## 5.2 Historical continuity — LATER REVALIDATION RATIFIED

The older RelationshipDefinition REST/discovery wording that forbids committed-history `LIST -> SCALAR` is **superseded by the current M4 revalidation and must be corrected when this ledger is absorbed into the owner**.

Current rule:

```text
same historical property name
    -> DataType lineage (`datatype_id`) remains stable

exact datatype_version
    -> may change

value_mode
    -> may change SCALAR -> LIST
    -> may change LIST -> SCALAR
```

Why `LIST -> SCALAR` is no longer a model-plane publication/revision prohibition:

```text
validity of an exact RDV
    !=
ability of every current factual Relationship to migrate to it
```

A factual `Relationship.SCHEMA_CHANGE` pays concrete preserve-or-fail migration admission for the selected source/target and can reject a multi-item LIST when targeting SCALAR. The model-plane exact target need not be globally banned merely because some facts cannot migrate to it.

DataType lineage continuity remains because same-name factual property continuity currently treats cross-DataType-lineage change as a different/unsupported semantic property transition.

## 5.3 Historical conflict probe — RATIFIED

Do not materialize full committed history in the worker.

The only remaining committed-history violation is:

```text
historical.name == candidate.name
AND historical.datatype_id != candidate.datatype_id
```

Detection should be set-based, candidate-name scoped, and may stop at one violating fact.

No history-summary materialization is justified for this rare model-plane operation.

An early fail-fast probe may run before expensive semantic preparation, but commit legality must still reflect all PUBLISHED/DEPRECATED history at the final admission boundary. A concurrent PUBLISH of another RDV may add committed history while the candidate is being prepared.

The exact concurrency mechanism remains architecture work.

## 5.4 Persistence delta — RATIFIED

The application already owns both:

```text
current DRAFT snapshot
prepared complete candidate
```

so persistence must not reread properties merely to compute the delta.

Classify by property name:

```text
unchanged
removed
added
changed
```

where `changed` includes changes to exact pin, value mode or ordinal.

Short-UoW DML direction:

```text
<= 1 bulk DELETE for removed + changed
<= 1 bulk INSERT for added + changed
1 RDV revision UPDATE
```

Delete-before-insert naturally supports ordinal swaps and uniqueness-sensitive replacement.

Identical complete replacement:

```text
property delta empty
DELETE 0
INSERT 0
revision still +1
```

because every successful REVISE consumes exactly one DRAFT generation.

No full delete/reinsert is preferred when most rows are unchanged; differential DML preserves bounded statement count while reducing row/index/FK churn.

No post-mutation reload is required for the 204 response.

## 5.5 Final admission ordering — RATIFIED at logical level

Logical short-UoW ordering:

```text
1. target-generation gate
       exact RDV still exists
       status == DRAFT
       revision == expected_revision

2. final dependency admission
       every new/changed exact DTV binding still admissible/PUBLISHED

3. final historical admission
       candidate remains compatible with all committed
       PUBLISHED/DEPRECATED same-name history
       under the current datatype-lineage-only continuity rule

4. persist declaration delta

5. consume exactly one revision generation
       result revision = expected_revision + 1
```

Whether revision CAS is physically performed at the initial gate or after equivalent protection is architecture work; the invariant is that a successful REVISE starts from exactly `expected_revision` and commits exactly the prepared complete candidate as `expected_revision + 1`.

The concurrency realization must also ensure that a newly committed incompatible publication cannot invalidate the historical admission between check and commit.

---

# 6. PUBLISH RelationshipDefinitionVersion — technical discovery CLOSED except concurrency/physical realization

## 6.1 Semantic preparation outside mutation UoW — RATIFIED

PUBLISH starts from one authoritative exact current DRAFT generation:

```text
Definition exists
exact target exists
status = DRAFT
revision = R
complete ordered properties
```

For **all** exact DTV pins in that DRAFT, outside the mutation UoW:

```text
load immutable exact DataTypeVersion semantic payload
compile validators/runtime semantic structures
prepare complete immutable RDV runtime representation
```

Conceptual prepared value:

```text
PreparedPublishedRDV
    relationship_definition_id
    version
    source_revision = R
    ordered property snapshot
    compiled RuntimePropertySpec / validators / exact-DTV linkage
```

An early set-based historical continuity probe may fail fast. Under the current revalidated history rule it needs only detect same-name historical declarations with a different `datatype_id`.

No complete RelationshipDefinition topology, `relationship_definition_space`, ObjectTemplate ancestry or full committed-history materialization is required.

Compilation can occur before final stabilization because exact DTV semantics are immutable. A concurrent REVISE is rejected by the final generation gate if target revision no longer equals prepared revision R.

## 6.2 Short final publication UoW — RATIFIED at logical level

Logical final admission:

```text
1. exact target still exists
2. status still DRAFT
3. revision == expected_revision == prepared source revision R
4. every pinned exact DTV is still PUBLISHED
5. committed-history datatype-lineage continuity is still valid
6. DRAFT -> PUBLISHED
7. revision unchanged
8. if Definition.default_version is still NULL
       -> set this version as default
   else
       -> leave current default unchanged
9. commit
```

No DTV semantic reload/recompile belongs inside the mutation UoW.

No `relationship_definition_space` maintenance occurs because RDV publication does not change stable Definition topology/name semantic ownership.

Exact locking/rendezvous mechanics remain architecture/concurrency work.

## 6.3 Immutable RDV cache publication — RATIFIED

The prepared immutable RDV becomes consumable in worker-local cache **only after successful PUBLISH commit**.

Conceptual facets:

```text
ImmutableRelationshipDefinitionVersionCache[(definition_id, version)]

snapshot READY
    ordered properties
        name
        ordinal
        datatype_id
        datatype_version
        value_mode

compiled READY
    RuntimePropertySpec / validators / exact-DTV semantic linkage
```

PUBLISH normally makes both facets READY from already prepared in-memory state. No post-commit DB reload or recompilation is required.

The cache excludes mutable/current state:

```text
RDV.status
RelationshipDefinition.default_version
```

Cache presence never proves current existence or current lifecycle admission.

## 6.4 Cache lifecycle across DEPRECATE/DELETE — RATIFIED

The immutable RDV cache follows semantic immutability rather than lifecycle state:

```text
DRAFT
    -> not immutable-cacheable

PUBLISHED
    -> immutable-cacheable

PUBLISHED -> DEPRECATED
    -> entry remains semantically valid
    -> no invalidation
```

DEPRECATE changes only current admission state and does not change the exact property snapshot or compiled semantics.

The same immutable entry can therefore serve existing factual Relationships pinned to a DEPRECATED version and CREATE_NEXT sources in either PUBLISHED or DEPRECATED state.

Complete Definition deletion does not require correctness-driven distributed cache invalidation because cache presence is never existence authority and UUID/exact-version identities are not reused. Local eviction may be opportunistic.

Facet consumers remain distinct:

```text
snapshot READY
    -> sufficient for CREATE_NEXT

compiled READY
    -> required by factual runtime consumers
```

## 6.5 No new relational RDV materialization — RATIFIED

`relationship_definition_properties` already stores the complete exact schema snapshot. PUBLISH does not justify another persisted copy merely to accelerate runtime compilation. Optimization is worker-local immutable cache reuse.

## 6.6 Default interaction and DML/cost closure — RATIFIED

`default_version` is not a semantic-preparation input and does not require a pre-read.

PUBLISH owns one conditional current-state transition at its final publication boundary:

```text
if Definition.default_version is still NULL
    -> set default_version = this published version

otherwise
    -> leave the current non-null default unchanged
```

Logical mutation direction:

```text
1. final generation/dependency/history admission
2. UPDATE exact RDV DRAFT -> PUBLISHED, revision unchanged
3. conditional UPDATE Definition
       SET default_version = :version
       WHERE id = :definition_id
         AND default_version IS NULL
4. COMMIT
```

The conditional default update may affect one or zero rows. Zero rows does not invalidate publication; it means a default already exists. The `204 No Content` response does not require learning or re-projecting which case occurred.

Concurrent publications against an initially NULL default must preserve a NULL-only claim invariant: at most one publication establishes the first default, while another publication may still succeed without replacing it. Exact serialization remains architecture work.

PUBLISH should own this narrow first-default transition directly rather than routing through the public `SET_DEFAULT` helper if that helper introduces command-specific reads/admission/reloads not required by publication.

Cost shape:

```text
READ / PREPARATION
    O(P) exact property snapshot
    bounded/bulk exact-DTV semantic preparation
    set-based history probe

MUTATION DML
    1 RDV status UPDATE
    <= 1 conditional Definition default UPDATE

property writes
    0
relationship_definition_space writes
    0
post-mutation reads
    0
```

Mutation statement count is constant in property count.

---

# 7. SET_DEFAULT — technical discovery CLOSED except concurrency/physical realization

`SET_DEFAULT` changes only current mutable selection state on the RelationshipDefinition lineage.

Admission:

```text
RelationshipDefinition exists
selected exact RDV exists in the same Definition
selected exact RDV status == PUBLISHED
```

No semantic-preparation phase is required. The operation does not consume RDV properties, DTV semantics, compiled caches, topology, ancestry, history or revision.

Logical short-UoW path:

```text
current admission
    Definition exists
    exact target exists/status == PUBLISHED

mutation
    default_version = selected version

commit
```

The command is idempotent when the selected version is already the current default. The `204 No Content` response requires no aggregate reconstruction or post-write reload.

No cache fill/invalidation or `relationship_definition_space` maintenance occurs.

Concurrency handoff:

```text
SET_DEFAULT(D@V) vs DEPRECATE(D@V)

SET_DEFAULT wins
    -> V becomes current default
    -> DEPRECATE cannot commit while V remains default

DEPRECATE wins
    -> V no longer PUBLISHED
    -> SET_DEFAULT cannot commit V as default
```

Exact rendezvous realization remains architecture work.

---

# 8. CLEAR_DEFAULT — technical discovery CLOSED except concurrency/physical realization

`CLEAR_DEFAULT` changes only the current mutable default pointer and has no exact-version operand.

Admission:

```text
RelationshipDefinition exists
```

Mutation:

```text
default_version -> NULL
```

The command is idempotent when the default is already NULL. A physical implementation may avoid a real row rewrite in that case, but must still distinguish an absent Definition (404) from a present Definition whose default is already NULL (204).

No semantic preparation, exact-version read, property/DTV/history/topology/space read, cache interaction, new denormalization or post-write reload is required.

External concurrency handoff:

```text
after CLEAR_DEFAULT commits
    -> a new factual Relationship.CREATE implicit-version resolution
       cannot obtain the old default
    -> absent current default yields default_version_unavailable
```

The fate of a factual CREATE that had already resolved an exact default before CLEAR_DEFAULT commits belongs to later cross-family concurrency closure.

---

# 9. Current technical frontier

Closed in this consolidation pass:

```text
relationship_definition_space classification/coherence/consumer boundary
CREATE
GET Definition LIST
GET Definition detail
GET RDV LIST
GET exact RDV
CREATE_NEXT
REVISE
PUBLISH
SET_DEFAULT
CLEAR_DEFAULT
```

Still to review technically:

```text
DEPRECATE
DELETE_DRAFT
DELETE root
cross-operation consistency sweep
```

`RelationshipDefinition` must not be promoted to REVIEWED BASELINE until those remaining operation points, the consistency sweep and explicit concurrency/architecture handoffs are complete.
