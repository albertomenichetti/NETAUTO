# ObjectTemplate GET lineage discovery

Status: WIP / NON-NORMATIVE

## Scope

Audit of ObjectTemplate lineage GET during M4 design discovery. This document records candidate findings only; it is not an implementation contract.

## Current data path

Public GET of an ObjectTemplate lineage is already one PostgreSQL read of `object_templates` by id.

The public DTO currently exposes:

- `id`
- `namespace`
- `name`
- `description`
- `abstract`
- `parent_template_id`
- `default_version`

## Stable vs current fields

Stable for lineage lifetime:

- `id`
- `namespace`
- `name`
- `abstract`
- `parent_template_id`

Current mutable state:

- `description`
- `default_version`

Because the public response includes current mutable state and current existence, the GET cannot be served entirely from an immutable/stable worker cache.

## Candidate cache fill

The existing lineage query already returns the complete stable lineage descriptor, so it can opportunistically populate a worker-local stable cache without any extra database round trip:

```text
StableObjectTemplateCache[template_id]
    id
    namespace
    name
    abstract
    parent_template_id
```

`description` and `default_version` must not be included in that stable cache.

Cache presence is not proof of current existence.

## Stable ancestry

The proposed lineage ancestry closure is a distinct derived structure:

```text
object_template_ancestry
    descendant_template_id
    ancestor_template_id
    depth
```

A normal lineage GET only needs the direct lineage row and should not be widened to load the full ancestry closure solely for cache warming.

The closure should be loaded/cached only when an operation actually needs ancestry information.

## Candidate M4 direction

- Keep the public lineage GET as one PostgreSQL statement.
- Use the returned immutable/stable subset to populate `StableObjectTemplateCache` opportunistically.
- Do not add queries merely to warm the ancestry cache.
- Keep current mutable state and existence authoritative in PostgreSQL.
