# M4 WIP — RelationshipDefinitionVersion LIST discovery

Status: WIP / NON-NORMATIVE

## Scope

Audit the current RelationshipDefinitionVersion LIST read path for data actually needed, mutable vs immutable state, cacheability, redundant reads, and denormalization opportunities. Concurrency redesign remains out of scope for this first phase.

## Current AS-IS

The persistence `list_versions()` query performs one `LEFT JOIN` from `relationship_definitions` to `relationship_definition_versions`, with optional lifecycle status filter, cursor predicate, ordering by version, and limit. It also selects a `parent_id` sentinel from the Definition header so the application can distinguish an absent Definition from an existing Definition whose filtered version set is empty.

The summary payload contains only:

- `relationship_definition_id`
- `version`
- `revision`
- `status`

No property declarations are loaded.

## Findings

### One-statement projection is already minimal

The current query preserves, in one authoritative read, the distinction between:

- missing RelationshipDefinition -> 404;
- existing RelationshipDefinition with no matching versions -> empty page.

The selected exact-version fields are exactly those required by the public summary DTO. `parent_id` is a useful existence sentinel rather than semantic over-read.

### Cache has no useful role

The list mixes lifecycle states. DRAFT `revision` is mutable and exact `status` is current mutable state because `PUBLISHED -> DEPRECATED` is allowed. Therefore PostgreSQL remains the correct authority for the summary projection.

The query carries no declaration payload and no DataType semantic payload, so it should not be expanded merely to warm the immutable runtime cache.

### No denormalization

No new denormalization is justified for this read. Existing relational state already provides the minimal authoritative summary.

## M4 candidate direction

Keep the current one-statement summary projection essentially unchanged:

- preserve Definition existence discrimination;
- read only summary fields;
- no property/dependency reads;
- no cache fill;
- no new denormalization.
