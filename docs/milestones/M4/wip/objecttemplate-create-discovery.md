# ObjectTemplate.CREATE discovery — WIP / NON-NORMATIVE

## Scope

This note records first-phase M4 discovery for `ObjectTemplate.CREATE` and the immediately related denormalization/cache questions. It is non-normative. Lock redesign remains deferred to the global concurrency phase.

## Current semantic baseline

An ObjectTemplate lineage owns stable identity and stable inheritance:

- `id`
- `namespace`
- `name`
- `abstract`
- `parent_template_id`

with mutable non-semantic `description` and mutable nullable `default_version`.

Each exact ObjectTemplateVersion owns:

- `(template_id, version)` identity
- `revision`
- lifecycle `status`
- exact `(parent_template_id, parent_version)` pin for non-root versions
- local properties
- local components

DRAFT is mutable but must remain well-formed. PUBLISHED and DEPRECATED are immutable semantic snapshots.

## AS-IS CREATE flow

Before the retrying UoW:

- validate qualified name;
- allocate `template_id`.

Inside each semantic UoW attempt:

1. resolve parent selection;
2. resolve DataType dependencies for properties;
3. validate/canonicalize migration defaults;
4. resolve component target lineages;
5. build DRAFT v1 candidate;
6. derive and acquire dependency lock plan;
7. repeat parent/property/component resolution under the acquired plan;
8. verify the dependency lock plan is unchanged;
9. validate the complete effective candidate through the exact parent chain;
10. persist lineage, exact version and local declarations;
11. commit.

The two resolution passes are not treated as accidental duplication in this phase: they are part of the current lock-plan stabilization mechanism and must not be removed locally before the global concurrency redesign.

## Data-access finding: admission vs immutable semantics

Current code often loads complete ObjectTemplateVersion aggregates while only part of the information is needed for current admission.

Examples of current mutable/admission facts:

- parent lineage exists now;
- parent default currently identifies a version when default selection is requested;
- selected exact parent is currently PUBLISHED for a new binding;
- selected DataType default is current;
- selected exact DataTypeVersion is currently PUBLISHED for a new binding;
- component target lineage exists now.

Examples of immutable semantic knowledge after publication:

- exact parent pin;
- local ObjectTemplate property declarations;
- local ObjectTemplate component declarations;
- flattened/effective ObjectTemplate schema;
- DataType exact constraints and primitive semantics.

Working principle:

> PostgreSQL remains authority for current existence, current lifecycle/admission and current defaults. Worker-local cache may hold immutable semantic knowledge but never proves current existence or current admissibility.

## Reuse of the DataType cache

ObjectTemplate property resolution currently needs the selected DataTypeVersion semantic payload to canonicalize/validate `migration_default`.

For an explicitly pinned PUBLISHED DataTypeVersion, the already-proposed DataType immutable cache can supply:

- stable `base_type` from the DataType lineage cache;
- immutable exact constraints / compiled validator from the DataType version cache.

This can move migration-default semantic validation out of repeated PostgreSQL semantic-payload loads. Current PUBLISHED admission and current default selection remain PostgreSQL concerns.

## Candidate ObjectTemplate cache split

Stable lineage cache candidate:

```text
StableObjectTemplateCache[template_id]
    id
    namespace
    name
    abstract
    parent_template_id
```

Do not treat cache presence as proof that the lineage still exists.

Immutable exact-version cache candidate, only for PUBLISHED/DEPRECATED:

```text
ImmutableObjectTemplateVersionCache[(template_id, version)]
    exact parent identity
    effective properties
    effective components
    optional compiled/runtime structures
```

DRAFT exact semantics are not cacheable.

## Stable lineage denormalization

Stable inheritance is a strong candidate for closure materialization because `parent_template_id` is immutable during normal lineage lifetime.

Candidate shape:

```text
object_template_ancestry
    descendant_template_id
    ancestor_template_id
    depth
```

This can support repeated descendant/ancestor compatibility checks without recursive traversal. The closure is a strong candidate for PostgreSQL materialization and worker-local immutable caching.

Status: strong candidate, not yet frozen.

## Exact-version ancestry denormalization

A separate exact closure could represent:

```text
object_template_version_ancestry
    descendant_template_id
    descendant_version
    ancestor_template_id
    ancestor_version
    depth
```

However, this is not yet justified independently. If the hot-path need is the final effective schema, direct effective-schema materialization may remove most demand for exact-chain traversal.

Status: open / not justified yet.

## Full effective-schema materialization

The strongest current denormalization candidate is materializing the flattened effective schema of immutable ObjectTemplateVersions.

Candidate effective property projection:

```text
object_template_effective_properties
    template_id
    template_version
    name
    position
    declaring_template_id
    datatype_id
    datatype_version
    value_mode
    required
    migration_default
```

Candidate effective component projection:

```text
object_template_effective_components
    template_id
    template_version
    name
    position
    declaring_template_id
    target_template_id
```

The authoritative semantic state remains stable lineage + exact parent pin + local declarations. Effective-schema rows are derived/materialized state, not an independent semantic authority.

### Cross-aggregate boundary

Do **not** copy DataType semantic payload into effective ObjectTemplate rows.

Effective ObjectTemplate properties should persist exact DataType pins only:

```text
(datatype_id, datatype_version)
```

`base_type`, constraints and compiled validation structures remain owned by the DataType model/cache. This avoids duplicating immutable DataType semantics inside ObjectTemplate materialization.

## DRAFT vs PUBLISHED materialization decision

Current preferred direction:

```text
DRAFT
    effective schema derived transiently/on demand
    NOT materialized as the long-lived effective projection
    NOT worker-cacheable

PUBLISHED
    effective schema materialized atomically as part of publication
    immutable and worker-cacheable

DEPRECATED
    keep the same immutable materialization
    no semantic cache invalidation
```

Rationale:

- DRAFT is mutable/editorial and repeated materialization maintenance would add write complexity to CREATE/REVISE/DELETE_DRAFT;
- CREATE/REVISE must already build the effective candidate in memory to prove it is well-formed;
- PUBLISH is the natural certification/compilation point at which the exact schema becomes immutable and repeatedly consumable;
- PUBLISHED -> DEPRECATED changes lifecycle policy, not semantic payload.

This supersedes the earlier exploration of materializing DRAFT effective projections.

## GET effective-schema corner case

A caller does not know in advance whether an exact version is DRAFT or immutable. The persistence read should route based on current exact-version status.

Conceptual cache-miss path:

```text
read exact version status
    DRAFT
        -> derive effective schema dynamically from exact chain + local declarations
    PUBLISHED / DEPRECATED
        -> read materialized effective schema
        -> optional immutable cache fill
```

The routing can be implemented as one authoritative PostgreSQL business statement (for example with a target CTE and mutually exclusive DRAFT/materialized branches), preserving the current one-business-statement read objective.

Conceptual immutable-cache-hit path:

```text
cache HIT for (template_id, version)
    -> semantic payload is known immutable
    -> PostgreSQL still verifies current existence when the public read contract requires it
    -> return cached effective schema if exact version still exists
```

A cache hit does not prove current existence. The current distinction PUBLISHED vs DEPRECATED is not needed merely to interpret the immutable effective-schema payload.

## CREATE cache fill

After successful CREATE, the new lineage can opportunistically populate the stable ObjectTemplate cache because all stable fields are already available.

The initial exact version is DRAFT v1 and must not populate the immutable exact-version cache.

## Open items

- physical schema and constraints for stable closure materialization;
- whether stable closure contains self rows (`depth=0`) or strict ancestors only;
- exact publication DML needed to build immutable effective projections;
- whether effective-schema cache entry also stores compiled runtime property/slot lookup structures;
- cache capacity/eviction policy;
- whether exact-version ancestry materialization is needed by any operation after the full operation audit;
- bulk DML optimization for local declaration inserts (`2 + P + C` AS-IS statements);
- all lock simplification and concurrency realization questions remain deferred to the second/global phase.
