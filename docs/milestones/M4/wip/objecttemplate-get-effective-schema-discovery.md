# ObjectTemplate GET effective-schema — M4 discovery

Status: WIP / NON-NORMATIVE

## Scope

Operation-by-operation M4 discovery for `GET /object-templates/{template_id}/versions/{version}/effective-schema`.

This note records current observations and candidate directions only. It does not authorize implementation and does not replace the current architecture documents.

## AS-IS

M3 resolves the complete effective schema with one authoritative SQL statement using a recursive CTE over the exact parent-version chain, then joins local property/component declarations along that chain.

The public DTO exposes the merged effective properties/components and their `declaring_template_id`; it does not expose lifecycle status.

## M4 materialization direction

Strong candidate: immutable exact ObjectTemplate versions (`PUBLISHED` and `DEPRECATED`) own persisted derived effective-schema rows created atomically at publication time.

Candidate tables:

```text
object_template_effective_properties
    template_id
    template_version
    ordinal
    declaring_template_id
    name
    position
    datatype_id
    datatype_version
    value_mode
    required
    migration_default

object_template_effective_components
    template_id
    template_version
    ordinal
    declaring_template_id
    name
    position
    target_template_id
```

`position` remains the original local declaration position. `ordinal` is derived effective-order state and preserves the current root-to-leaf merge order without requiring ancestry traversal at read time.

These rows are derived owned state, not an independent semantic authority.

## DRAFT parent admission decision

Current code admits a newly selected exact parent only when that parent is `PUBLISHED`. A DRAFT child may later retain the same exact parent after the parent transitions to `DEPRECATED`; the parent semantic snapshot remains immutable.

The current architecture documentation is less explicit about this rule, so M4 records the following intentional direction:

```text
new exact parent binding:
    parent exact version must be PUBLISHED

existing DRAFT binding:
    parent may later become DEPRECATED
    semantic snapshot remains valid

DRAFT -> DRAFT exact parent binding:
    unsupported in M4
```

Allowing `DRAFT -> DRAFT` would require additional semantics for dependent-DRAFT invalidation/freshness, cascading revision effects, publication ordering, collision revalidation after ancestor edits, and mutable effective-schema dependency handling. Current assessment: unfavorable cost/value for M4.

This rule should be made explicit in normative architecture during the later freeze phase.

## Candidate read path

### PUBLISHED / DEPRECATED target

Read the target exact version's own persisted effective-schema materialization directly.

No recursive exact ancestry traversal is needed.

On an immutable worker-cache hit, cache data may serve the semantic payload, but current exact existence must still be checked in PostgreSQL because cache presence is not proof of current existence.

### DRAFT root target

Derive the effective schema from current local DRAFT declarations only.

### DRAFT child target

Because the exact parent is necessarily an immutable snapshot (`PUBLISHED` when bound, possibly later `DEPRECATED`):

```text
EffectiveSchema(current DRAFT)
    =
EffectiveSchema(parent exact, materialized/immutable)
    +
current local DRAFT declarations
```

No recursive exact ancestry traversal is needed for the DRAFT child either.

The DRAFT effective result remains transient and must not be persisted as long-lived materialized state or worker-cached as immutable.

## Cache behavior

For `PUBLISHED`/`DEPRECATED`, the materialized effective schema is a natural cold-load source for the runtime-oriented immutable ObjectTemplate cache.

Cache warm-up may be opportunistic when the necessary semantic payload is already read. Do not add extra queries solely to warm the cache.

For DRAFT, no immutable cache entry is allowed.

## Exact-version ancestry closure

This finding further weakens the case for a separate `object_template_version_ancestry` table. The main consumers identified so far need the merged exact effective result, not the explicit list of exact ancestor versions.

Stable lineage closure remains a separate strong candidate for lineage-level compatibility and widening questions.

## Open for later concurrency phase

- exact current-existence check semantics on immutable cache hit;
- interaction of DRAFT reads with concurrent revise/delete/publish;
- statement shape needed to preserve one coherent public read under PostgreSQL;
- whether locking is required for any consumer path (not redesigned in this discovery phase).
