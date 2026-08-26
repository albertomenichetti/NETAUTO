# ObjectTemplate LIST lineages — M4 discovery

Status: WIP / NON-NORMATIVE

## Scope

Discovery note for the public ObjectTemplate lineage list read. This note records candidate M4 data-access/cache implications only; it does not freeze architecture or concurrency behavior.

## Current behavior

`LIST ObjectTemplate lineages` is already implemented as one PostgreSQL query over `object_templates`, with optional filters on `namespace`, `name`, `abstract`, `parent_template_id`, keyset pagination on `(namespace, name)`, and ordering by `(namespace, name)`.

The returned lineage payload contains both stable and mutable/current fields.

Stable lineage descriptor:

```text
id
namespace
name
abstract
parent_template_id
```

Mutable/current state:

```text
description
default_version
```

## M4 finding

The public read should remain PostgreSQL-backed because current existence, `description`, and `default_version` cannot be inferred from immutable/stable cache state.

The query already returns the complete stable descriptor, therefore it may opportunistically populate a worker-local stable ObjectTemplate descriptor cache without adding a database round-trip:

```text
StableObjectTemplateCache[id]
    id
    namespace
    name
    abstract
    parent_template_id
```

Because this is a bulk/list operation, cache population is a policy choice rather than an architectural requirement; large catalog scans should not be required to populate or pollute the runtime cache.

The existing `parent_template_id` filter means direct child only. The candidate stable ancestry closure is not required by this operation and must not be loaded merely to warm cache state.

## Candidate data path

```text
PostgreSQL object_templates
    -> one filtered/keyset-paginated query
    -> current public response
    -> optional stable-descriptor cache fill using already-returned columns
```

## Non-findings / deferred

- No new denormalization is justified by this operation.
- No stable ancestry lookup is needed for the current direct-parent filter.
- Cache fill policy remains open and should be chosen with cache-pressure/runtime usage in mind.
