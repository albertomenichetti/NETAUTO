# RelationshipDefinition PUBLISH — M4 discovery

Status: **ACTIVE TECHNICAL REVIEW / RATIFIED PREPARATION CHECKPOINT / WIP / NON-NORMATIVE**

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

A later `PUBLISHED -> DEPRECATED` transition does not change the immutable exact property/compiled semantics; the lifecycle/cache behavior is the next focused PUBLISH/DEPRECATE checkpoint and is not further frozen here.

---

## No new relational denormalization at PUBLISH

No additional relational materialization is justified merely by PUBLISH. `relationship_definition_properties` already persists the complete exact schema snapshot. Runtime optimization is worker-local immutable compilation/cache reuse, not another relational copy of the same RDV schema.

## Still deferred

The following remain architecture/concurrency handoffs:

```text
exact lock/wait/retry protocol
PUBLISH vs concurrent REVISE
PUBLISH vs PUBLISH of another exact version in the same Definition
PUBLISH vs DTV DEPRECATE
PUBLISH vs SET_DEFAULT/CLEAR_DEFAULT/DEPRECATE
exact first-default conditional statement
physical indexes/constraints
```

The technical sweep must preserve the logical invariants above without silently selecting those physical mechanisms during discovery.
