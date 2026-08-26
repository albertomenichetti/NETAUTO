# M4 — DataType REVISE discovery

**Status:** WIP / NON-NORMATIVE

**Role:** bounded discovery note for `DataType.REVISE`. This document records AS-IS evidence, findings and working hypotheses only. It does not define the M4 contract, TO-BE architecture, persistence schema, cache contract or concurrency realization.

The delivered AS-IS under `docs/architecture/` remains authoritative until M4 explicitly freezes a TO-BE delta.

## 1. Scope

This note intentionally covers only the points discussed while analysing `DataType.REVISE`:

- semantic ownership of `base_type`;
- responsibility of `canonicalize_constraints()`;
- whether candidate constraint canonicalization belongs before the write UoW;
- worker-local cache behavior needed to make that possible without distributed cache coherence;
- compilation of immutable runtime validation artifacts when data enters the cache.

Lock simplification, exact UoW SQL shape, DELETE races and wider DataType lifecycle redesign are deliberately left open.

## 2. AS-IS semantic facts

Current DataType architecture states that one stable DataType lineage has immutable `id`, `namespace` and `name`, while every version in that lineage uses the same `PrimitiveType`. Cross-primitive evolution is not part of the current architecture.

Current persistence nevertheless stores `base_type` on each `datatype_versions` row. Application flows preserve the stable-type invariant by cloning the source `base_type` on `CREATE_NEXT` and by not allowing `REVISE` to change it.

Current `REVISE` stabilizes the exact DRAFT generation, reloads the version, verifies `status == DRAFT` and `revision == expected_revision`, then calls `canonicalize_constraints(current.base_type, candidate)` while the write UoW is already open.

## 3. Finding: `base_type` is stable-lineage semantics

Working finding:

> `PrimitiveType` is semantically a stable DataType-lineage fact, while the current relational model stores it redundantly as exact-version state.

Conceptually the semantic ownership is closer to:

```text
DataType stable lineage
    id
    namespace
    name
    base_type
```

than to:

```text
DataTypeVersion
    version
    base_type
```

The current physical placement is therefore a candidate M4 schema-design issue. No TO-BE schema change is frozen by this note.

## 4. What `canonicalize_constraints()` does

`canonicalize_constraints()` is pure with respect to runtime state. Its result depends only on:

```text
PrimitiveType
+
candidate constraints
```

It performs complete constraint-contract validation/canonicalization for that primitive, including as applicable:

- candidate object/key validation;
- rejection of unsupported constraints for the primitive;
- `min_length` / `max_length` validation;
- regex syntax validation through `re.compile()`;
- `ip_version` validation;
- canonicalization of `minimum` / `maximum` values through primitive semantics;
- contradiction checks such as `minimum <= maximum` and `min_length <= max_length`;
- primitive canonicalization of every enum member;
- duplicate enum detection after canonicalization;
- validation of enum members against the remaining constraints;
- canonical ordering of the persisted enum representation.

It does not require current lifecycle status, current revision, default state, locks or any other PostgreSQL observation.

## 5. Working conclusion: canonicalize before the UoW

Because constraint canonicalization depends only on a stable `PrimitiveType` plus caller input, the working M4 direction is:

```text
resolve stable base_type
    -> canonicalize candidate constraints
    -> only then open the mutation UoW
```

The write UoW should remain responsible for current mutable truth, in particular the exact DRAFT existence/lifetime, lifecycle state and `expected_revision` freshness.

This separates:

```text
candidate semantic validation
    = pure CPU work over stable/immutable knowledge

current mutation admission
    = PostgreSQL authority inside the UoW
```

## 6. Worker-local DataType cache hypothesis

The cache is intended to contain only knowledge that does not require a distributed coherence protocol.

### Stable lineage descriptor

A stable descriptor may be cached by `datatype_id` and may include at least:

```text
datatype_id
namespace
name
base_type
```

Once created, these facts are immutable under the current semantic model. Therefore the descriptor remains useful even when the lineage currently has no PUBLISHED or DEPRECATED version.

A cached descriptor is knowledge about an immutable identity, not proof that the lineage still exists. If the lineage is later deleted, a subsequent write UoW remains responsible for detecting current absence.

### Exact immutable version semantics

Exact versions may enter the semantic cache only after leaving DRAFT:

```text
PUBLISHED
DEPRECATED
```

The cacheable semantic payload is the immutable exact contract, for example:

```text
datatype_id
version
canonical constraints
```

with the lineage `base_type` supplied by the stable descriptor.

Current lifecycle admission is deliberately separate. `PUBLISHED -> DEPRECATED` must not require invalidating the semantic cache because the exact constraint contract does not change.

DRAFT exact semantics are not cached because their constraints and revision are mutable and the version can be deleted/reused according to current version-allocation semantics.

## 7. Cache-miss load hypothesis

For a cache miss on a DataType lineage, one PostgreSQL statement should be able to load:

```text
stable DataType lineage facts
+
all exact PUBLISHED / DEPRECATED semantic versions
```

The result is consumed as follows:

```text
stable descriptor
    -> cache even if there are zero immutable exact versions

PUBLISHED / DEPRECATED exact semantic versions
    -> cache

DRAFT versions
    -> do not enter the semantic cache
```

This is a general DataType model-plane cache fill, not a query designed specifically for `REVISE`.

## 8. Compile on cache entry

Cache population is also the compilation boundary for immutable runtime validation structures.

PostgreSQL remains authoritative for the canonical persistent semantic representation. The worker-local cache may derive an execution-oriented representation from it, including for example:

```text
canonical pattern source
+
compiled re.Pattern
```

and analogous preprocessed structures where they materially reduce repeated validation work.

Therefore validation against an already cached exact DataTypeVersion should ideally consume a ready runtime validator rather than repeatedly interpreting the persisted constraint document or recompiling regexes.

Compiled objects are intentionally process-local and disposable:

```text
worker restart
    -> empty cache
    -> reload canonical immutable semantics
    -> compile locally again
```

No compiled Python artifact becomes persistence authority and no cross-worker invalidation/distribution protocol is required.

## 9. Candidate `REVISE` flow

The current working flow is:

```text
REVISE(DT, draft_version, candidate_constraints)

1. lookup DataType stable descriptor in worker cache

2. cache HIT
       -> obtain base_type

   cache MISS
       -> one DB load of stable lineage + all immutable exact versions
       -> cache stable descriptor
       -> cache/compile PUBLISHED + DEPRECATED exact semantics
       -> obtain base_type

3. canonicalize_constraints(base_type, candidate_constraints)
   outside the write UoW

4. open write UoW

5. establish current exact DRAFT generation
       version exists
       status == DRAFT
       revision == expected_revision

6. persist canonical constraints and advance revision

7. commit
```

If cache knowledge refers to a lineage that has since been deleted, step 3 may perform harmless CPU work against historical immutable knowledge; step 5 remains authoritative and must fail on current absence.

## 10. Explicitly open points

This note does **not** yet decide:

- the final relational relocation of `base_type`;
- the exact cache class/object layout;
- cache size/eviction policy;
- the exact SQL projection used for cold loading;
- whether additional immutable DataType-derived structures should be compiled;
- the final locking and SQL realization of the `REVISE` UoW;
- whether current LockPlan mechanisms can or should be simplified;
- behavior of other DataType operations beyond the dependencies needed to reason about `REVISE`.

These remain discovery/design work for subsequent discussion.
