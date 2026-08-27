# M4 WIP — Object LIST discovery

Status: WIP / NON-NORMATIVE

## Scope

This note records the M4 discovery conclusion for `GET /objects` after reopening the public shape of exact `GET /objects/{id}`.

## Concrete API role

The collection endpoint is intentionally different from the exact Object GET.

Concrete consumer use:

```text
GET /objects
    -> search/filter/page Object identities and lightweight current metadata

GET /objects/{id}
    -> inspect one Object in detail, including its properties and candidate complete first-level component projection
```

The collection therefore remains lightweight even if the exact GET becomes richer.

Candidate list item:

```text
id
canonical_name
template_id
template_version
```

No `properties` and no direct `components` are added to collection items.

## Why not expand collection items

A page can contain many Objects, and each Object can itself have many direct children. Expanding properties/components for every list item would multiply result size and turn a search/navigation endpoint into a potentially very large aggregate projection.

Example:

```text
100 Server Objects
x 50 Interface children
x 20 Disk children
```

A rich collection page would need to project thousands of child references even when the caller only wants to find one Server.

## Persistence consequence

The current one-statement projection over `objects` remains the preferred shape:

```text
objects
    -> optional template_id/template_version/canonical_name filters
    -> keyset by id
    -> ORDER BY id
    -> LIMIT limit + 1
```

No ObjectTemplate cache, effective-schema materialization, ownership join, or child-name join belongs in this collection path.

## Abstract architectural reading

Collection and exact-resource representations do not need identical payload richness. The collection is a bounded discovery/navigation surface; the exact GET is the detailed resource projection.

## Candidate first-phase conclusion

Keep `GET /objects` structurally lightweight with current `ObjectSummary` fields only, while allowing `GET /objects/{id}` to evolve independently into a richer first-level Object representation.
