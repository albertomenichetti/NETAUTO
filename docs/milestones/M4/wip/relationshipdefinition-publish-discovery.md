# RelationshipDefinition PUBLISH — M4 discovery

Status: **TECHNICAL DISCOVERY CLOSED / CONCURRENCY-PHYSICAL REALIZATION DEFERRED / WIP / NON-NORMATIVE**

This note is operation-specific source/evidence subordinate to the current RelationshipDefinition family owner and to the technical consolidation ledger. It persists the PUBLISH technical-discovery checkpoints ratified during the current M4 sweep; it does not authorize implementation or freeze architecture-level locking/DDL choices.

## Current semantic boundary

Publishing a `RelationshipDefinitionVersion` converts one exact DRAFT snapshot into an immutable PUBLISHED snapshot. Property declarations are already the complete exact relationship schema; unlike `ObjectTemplate`, there is no inherited/effective schema that needs a separate relational materialization.

Publication must still certify the candidate against complete committed `PUBLISHED` / `DEPRECATED` property history because distinct versions may be published out of numeric order. Under the current M4 revalidation, historical continuity means:

```text
same property name
    -> stable DataType lineage (`datatype_id`)

exact datatype_version
    -> may change

value_mode
    -> may change SCALAR -> LIST
    -> may change LIST -> SCALAR
```

The older RelationshipDefinition rule that globally forbade historical `LIST -> SCALAR` is superseded. Whether a concrete factual Relationship can migrate to a SCALAR target remains a factual `Relationship.SCHEMA_CHANGE` preserve-or-fail question and is not a model-plane validity prohibition.

Every exact DataTypeVersion directly pinned by the DRAFT must still be currently `PUBLISHED` at the final publication admission boundary.

## AS-IS observations retained as evidence

The current application path loads the complete `RelationshipDefinition` aggregate and the complete exact DRAFT before lock-plan stabilization, then reloads both after stabilization. The complete Definition payload is larger than publication semantics require: outside concurrency realization, publication needs current Definition existence/default interaction and the exact target generation, not the complete old autonomous-Resolution aggregate.

History validation currently loads the complete PUBLISHED/DEPRECATED property history. The current M4 direction replaces this with a set-based historical-conflict probe scoped to candidate property names.

Current DataType dependency certification loads exact referenced versions and checks current lifecycle. The same immutable semantic payload is also the input needed to compile runtime property validators/specifications.

The AS-IS DML path performs response/helper reloads that are not semantically required; PUBLISH returns `204 No Content`, so no post-mutation exact-version or Definition reconstruction is needed solely for the response.

---

# RATIFIED PUBLISH-TECH-01 — semantic preparation outside the mutation UoW

PUBLISH does not author a new property schema. It takes the current exact DRAFT generation and prepares the immutable runtime representation that will become valid only if final publication admission succeeds.

## Step 1 — authoritative current DRAFT snapshot

Before expensive semantic preparation, obtain the exact current target state needed by PUBLISH:

```text
RelationshipDefinition exists
exact target version exists
status = DRAFT
revision = R
complete ordered property snapshot
```

The complete stable Definition topology, `relationship_definition_space`, ObjectTemplate ancestry and other topology data are not publication inputs.

## Step 2 — immutable semantic preparation outside the mutation UoW

For **all** exact DataTypeVersion pins in the DRAFT:

```text
load exact immutable DataTypeVersion semantic payload
compile required validators/runtime semantic structures
```

Then prepare the complete immutable runtime RDV representation in application/worker state.

Conceptually:

```text
PreparedPublishedRDV
    relationship_definition_id
    version
    source_revision = R
    ordered property snapshot
        name
        ordinal
        datatype_id
        datatype_version
        value_mode
    compiled RuntimePropertySpec / validators / semantic linkage
```

This expensive immutable semantic preparation remains outside the short mutation UoW.

An early set-based historical-continuity probe may also run here for fail-fast behavior. It needs only detect, for candidate property names, a committed `PUBLISHED`/`DEPRECATED` declaration with a different `datatype_id`.

PUBLISH preparation does **not** require:

```text
whole RelationshipDefinition aggregate
relationship_definition_space
ObjectTemplate ancestry
full committed-history materialization in the worker
```

## Why compilation may happen before final stabilization

Exact DataTypeVersion semantic payload is immutable. Therefore compilation does not need to hold publication locks or keep the mutation transaction open.

A concurrent REVISE of the target DRAFT is handled by the final exact-generation gate:

```text
prepared source revision = R
final target revision != R
    -> publication cannot commit this prepared candidate
```

Preparation against an older DRAFT generation is therefore harmless as long as cache publication does not occur before the successful PUBLISH commit.

---

# RATIFIED PUBLISH-TECH-02 — short final publication UoW

The final mutation UoW begins only after the immutable semantic candidate has been prepared.

Logical admission order/invariants:

```text
1. target exact version still exists
2. target status still DRAFT
3. target revision == expected_revision == prepared source revision R
4. every pinned exact DataTypeVersion is still PUBLISHED
5. committed-history DataType-lineage continuity is still valid at the publication boundary
6. persist DRAFT -> PUBLISHED
7. revision remains unchanged
8. if Definition.default_version is still NULL
       -> set it to this exact version
   else
       -> leave it unchanged
9. commit
```

The exact SQL/lock/rendezvous mechanism that keeps DTV admission and committed-history certification valid through commit remains architecture/concurrency work.

The final UoW does **not** reload or recompile DataType semantic payload.

There is no `relationship_definition_space` maintenance because RDV publication does not alter stable Definition topology/name semantic-cell ownership.

---

# RATIFIED PUBLISH-TECH-03 — cache publication boundary

PUBLISH is the natural boundary for creating the immutable exact-RDV worker cache entry, but the prepared entry becomes consumable **only after successful commit**.

Conceptual cache:

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

PUBLISH normally has all information required to make both facets READY because all pinned exact DTV semantics were loaded and compiled during preparation.

After successful commit:

```text
PreparedPublishedRDV
    -> publish immutable cache entry
```

No post-commit PostgreSQL reload or recompilation is required.

Before commit:

```text
prepared candidate
    -> NOT visible as a PUBLISHED/cache-authoritative RDV entry
```

The cache excludes mutable/current state:

```text
RDV.status
RelationshipDefinition.default_version
```

Cache presence never proves current existence or lifecycle admission.

---

# RATIFIED PUBLISH-TECH-04 — immutable cache lifecycle across DEPRECATE/DELETE

The immutable exact-RDV cache follows semantic immutability, not current lifecycle state.

```text
DRAFT
    -> not eligible for immutable RDV cache publication

PUBLISHED
    -> immutable exact RDV cacheable

PUBLISHED -> DEPRECATED
    -> immutable cache entry remains valid
    -> no semantic cache invalidation
```

DEPRECATE changes only current admission state. It does not change:

```text
ordered properties
ordinal
exact DTV pins
value_mode
compiled validators/runtime specs
immutable exact semantic payload
```

This allows the same immutable entry to serve at least:

```text
existing factual Relationships pinned to a DEPRECATED exact RDV
CREATE_NEXT whose source may be PUBLISHED or DEPRECATED
```

The cache is never authority for:

```text
RDV current existence
RDV current PUBLISHED/DEPRECATED status
RelationshipDefinition current existence
RelationshipDefinition.default_version
```

Therefore complete RelationshipDefinition deletion does not require correctness-driven distributed invalidation. An old local entry may be evicted opportunistically; it cannot prove resource existence, and lineage UUID/exact-version identities are not reused for another semantic resource.

Cache facets remain independent:

```text
snapshot READY
    -> sufficient for CREATE_NEXT cloning

compiled READY
    -> required by factual runtime consumers that need compiled validation semantics
```

PUBLISH normally makes both facets READY. A bounded cold loader may later complete a missing facet without invalidating or rebuilding an already READY immutable facet.

Lifecycle interaction summary:

```text
PUBLISH
    -> publish/complete immutable entry only after successful commit

DEPRECATE
    -> no semantic cache mutation/invalidation

root DELETE
    -> optional local eviction only
    -> not a correctness prerequisite
```

---

# RATIFIED PUBLISH-TECH-05 — default interaction and logical DML/cost closure

`default_version` does not need to be read during semantic preparation. Publication does not decide the default outcome from a stale pre-read; it owns one conditional current-state transition at the publication boundary:

```text
if Definition.default_version is still NULL
    -> set default_version = published version

otherwise
    -> leave the existing non-null default unchanged
```

Logical mutation direction:

```text
1. perform final generation/dependency/history admission

2. UPDATE exact RDV
       DRAFT -> PUBLISHED
       revision unchanged

3. conditional UPDATE RelationshipDefinition
       SET default_version = :version
       WHERE id = :definition_id
         AND default_version IS NULL

4. COMMIT
```

The conditional default mutation may affect one or zero rows:

```text
1 row
    -> this publication established the first current default

0 rows
    -> another/default value already exists
    -> publication remains valid
```

The `204 No Content` response does not require learning which branch occurred and does not justify a post-mutation Definition reload.

For concurrent publications while the default is initially NULL, at most one publication may claim the NULL -> exact-version transition; another publication may still succeed without replacing the already-established default. Exact serialization/locking remains architecture work.

PUBLISH owns this narrow first-default transition directly rather than invoking the public `SET_DEFAULT` command/helper if that helper would introduce command-specific reads/admission/reloads not required by publication.

Cost shape:

```text
READ / PREPARATION
    O(P) exact property snapshot
    bounded/bulk exact-DTV semantic preparation
    set-based historical conflict probe

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

Statement count for mutation is constant in property count.

---

## No new relational denormalization at PUBLISH

No additional relational materialization is justified merely by PUBLISH. `relationship_definition_properties` already persists the complete exact schema snapshot. Runtime optimization is worker-local immutable compilation/cache reuse, not another relational copy of the same RDV schema.

## PUBLISH technical closure checkpoint

PUBLISH technical discovery is closed for the current M4 pass, except for architecture/concurrency/physical realization.

Ratified direction:

```text
outside mutation UoW
    -> load exact DRAFT generation
    -> load + compile all pinned exact DTV semantics
    -> prepare immutable RDV runtime/cache candidate
    -> optional early set-based history fail-fast

inside short mutation UoW
    -> exact DRAFT/expected_revision gate
    -> every pinned DTV still PUBLISHED
    -> committed-history datatype-lineage continuity still valid
    -> DRAFT -> PUBLISHED, revision unchanged
    -> conditional NULL-only first-default establishment

post commit
    -> publish immutable RDV cache entry

NO
    -> relationship_definition_space work
    -> property rewrite
    -> DTV recompilation inside mutation UoW
    -> default pre-read requirement
    -> response-only post-commit reload
```

## Still deferred

The following remain architecture/concurrency handoffs:

```text
exact lock/wait/retry protocol
PUBLISH vs concurrent REVISE
PUBLISH vs PUBLISH of another exact version in the same Definition
PUBLISH vs DTV DEPRECATE
PUBLISH vs SET_DEFAULT/CLEAR_DEFAULT/DEPRECATE
exact first-default conditional SQL/lock realization
physical indexes/constraints
```

The technical sweep must preserve the logical invariants above without silently selecting those physical mechanisms during discovery.
