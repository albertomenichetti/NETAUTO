# DataType LIST lineages discovery

Status: WIP / NON-NORMATIVE

## Scope

First-phase M4 audit of `LIST DataType lineages`. This note intentionally does not redesign the locking/concurrency model.

## AS-IS

The operation performs one PostgreSQL query against `datatypes`, with optional `namespace` / `name` filters, keyset pagination on `(namespace, name)`, and a limit.

The current public lineage representation exposes:

- `id`
- `namespace`
- `name`
- `description`
- `default_version`

M4 discovery has already identified `base_type` as stable lineage state rather than exact-version state, so the candidate lineage representation also includes `base_type`.

## Data-access finding

One SQL statement remains the correct target. With `base_type` moved onto `datatypes`, no join is required and there is no material redundant payload in the lineage list itself.

## Cache classification

Each row naturally contains both immutable and current information:

Immutable / stable:

- `id`
- `namespace`
- `name`
- `base_type`

Current mutable:

- `description`
- `default_version`

Therefore the list result could populate worker-local stable DataType cache entries without any additional database query.

However, unlike a single-lineage GET, a lineage LIST may touch many DataTypes that the worker will never use semantically. Warming all returned entries could therefore cause unnecessary cache pollution.

Current discovery position:

- LIST lineages MAY opportunistically populate the stable cache because all required immutable facts are already available.
- This is a cache policy choice, not an architectural requirement.
- The LIST must never load extra data solely to warm the cache.
- Final behavior should be decided together with cache capacity / eviction policy.

## Open items

- Final worker-local cache capacity / eviction policy.
- Whether LIST-driven stable cache population is enabled by default, selective, or disabled.
- Locking/concurrency questions remain deferred to the second-phase global audit.
