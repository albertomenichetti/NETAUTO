# M3 — Cursor Identity Audit

**Status:** CONSOLIDATED DISCOVERY CROSS-CHECK / NON-NORMATIVE

**Role:** final cross-check of every public paginated GET/read route that emits or accepts an opaque keyset cursor. This document does not authorize implementation and does not replace the future M3 contract, architecture set or implementation steps.

## 1. Audit rule

The current cursor codec serializes:

```text
version
route
filters
key
```

and accepts a cursor only when `route` and `filters` exactly match the current query.

For M3, the complete semantic identity rule is:

```text
cursor query identity
    = route identity
    + every path target that changes collection membership
    + every query filter that changes collection membership
    + any explicit presence bit needed to distinguish semantically different carriers

cursor position key
    = the complete canonical keyset ordering tuple

limit
    = not part of semantic query identity
```

`cursor` itself is not part of query identity. `limit` remains intentionally changeable between pages.

If a future architecture change alters a route's canonical ordering or cursor semantics, the cursor codec/version contract must be reconsidered rather than silently accepting old tokens under a different ordering.

## 2. Complete cursor-bearing public route census

There are 12 canonical public paginated GET/read routes.

| # | Public route | Current cursor filters | Keyset key | Audit |
|---:|---|---|---|---|
| 1 | `GET /api/v1/core/datatypes` | `namespace`, `name` | `(namespace, name)` | PASS |
| 2 | `GET /api/v1/core/datatypes/{datatype_id}/versions` | `datatype_id`, `status` | `(version)` | PASS |
| 3 | `GET /api/v1/core/object-templates` | `namespace`, `name`, `abstract`, `parent_template_id`, `parent_filter_set` | `(namespace, name)` | PASS |
| 4 | `GET /api/v1/core/object-templates/{template_id}/versions` | `template_id`, `status` | `(version)` | PASS |
| 5 | `GET /api/v1/core/object-templates/{template_id}/relationship-capabilities` | `template_id`, `name` | `(resolution_id)` | PASS |
| 6 | `GET /api/v1/core/objects` | `template_id`, `template_version`, `canonical_name` | `(id)` | PASS |
| 7 | `GET /api/v1/core/objects/{parent_object_id}/components` | **currently `slot_name` only** | `(child_object_id)` | **FAIL — missing `parent_object_id`** |
| 8 | `GET /api/v1/core/objects/{object_id}/relationships` | **currently `relationship_definition_id`, `name` only** | `(relationship_id, destination_object_id, name)` | **FAIL — missing `object_id`** |
| 9 | `GET /api/v1/core/objects/{object_id}/lifecycle-events` | lifecycle filters + `involving_object_id=<path object>` | `(occurred_at, id)` DESC | PASS |
| 10 | `GET /api/v1/core/relationship-definitions` | none | `(id)` | PASS |
| 11 | `GET /api/v1/core/relationship-definitions/{relationship_definition_id}/versions` | `definition_id`, `status` | `(version)` | PASS |
| 12 | `GET /api/v1/core/lifecycle-events` | all global lifecycle filters + `involving_object_id=null` | `(occurred_at, id)` DESC | PASS |

No additional cursor identity defect was found beyond the two already recorded during the GET/read walkthrough.

## 3. Confirmed correct path-target binding

The following path-scoped collections already include their path target in `filters`:

```text
DataType versions
    datatype_id

ObjectTemplate versions
    template_id

ObjectTemplate relationship capabilities
    template_id

RelationshipDefinition versions
    definition_id

Object-scoped lifecycle
    involving_object_id
```

Object-scoped lifecycle deliberately uses the internal filter key `involving_object_id` rather than the public path parameter spelling `object_id`. This is correct because it records the actual membership semantics and distinguishes the object-scoped route from the global lifecycle route.

## 4. Confirmed defects

### 4.1 OBJ-GET-03 — components

Current identity:

```text
filters = {
    slot_name
}
```

Required target identity:

```text
filters = {
    parent_object_id,
    slot_name
}
```

Without `parent_object_id`, a cursor issued for parent A can be accepted on parent B when `slot_name` is unchanged.

### 4.2 OBJ-GET-06 — object-relative relationships

Current identity:

```text
filters = {
    relationship_definition_id,
    name
}
```

Required target identity:

```text
filters = {
    object_id,
    relationship_definition_id,
    name
}
```

Without `object_id`, a cursor issued for object A can be accepted on object B when the optional filters are unchanged.

These remain the only two cursor filter corrections required by the current 12-route census.

## 5. `parent_template_id = null` interaction

Area C does not introduce a new cursor defect.

The ObjectTemplate lineage cursor already carries both:

```text
parent_template_id
parent_filter_set
```

which distinguishes:

```text
filter omitted
    parent_template_id = null
    parent_filter_set = false

root-only
    parent_template_id = null
    parent_filter_set = true

exact parent
    parent_template_id = UUID
    parent_filter_set = true
```

Therefore the new public `parent_template_id=null` carrier can reuse the existing cursor identity model unchanged.

## 6. Lifecycle route separation

Global and object-scoped lifecycle use the same internal cursor route identifier, but their `filters` remain distinct:

```text
global lifecycle
    involving_object_id = null
    object_id may be a global query filter

object-scoped lifecycle
    involving_object_id = <path object UUID>
    object_id = null
```

A cursor from the global route is therefore incompatible with an object-scoped request, and a cursor for object A is incompatible with object B.

## 7. Keyset-key completeness

The cursor position keys match the canonical public ordering tuples.

```text
DataType lineages                 (namespace, name)
DataType versions                 (version)
ObjectTemplate lineages           (namespace, name)
ObjectTemplate versions           (version)
Relationship capabilities         (resolution_id)
Objects                            (id)
Object components                 (child_object_id)
Object relationships              (relationship_id, destination_object_id, name)
RelationshipDefinitions           (id)
RelationshipDefinition versions   (version)
lifecycle                         (occurred_at, id) DESC
```

For path-scoped version lists, the lineage/definition identity is correctly carried in `filters`, so the local `version` key is sufficient.

For object-relative Relationship views, the persistence query applies `DISTINCT` to the public view projection and uses the same `(relationship_id, destination_object_id, name)` tuple for ordering/keyset continuation. With `object_id` added to query identity, the cursor key remains complete.

No keyset-key extension is required by M3.

## 8. Current test coverage finding

Existing API coverage proves several filter-identity properties, including:

```text
Object list cursor rejected when canonical_name changes
global lifecycle cursor rejected when kind changes
object-relative Relationship cursor rejected when name changes
```

The current tests located during this audit do not exercise the missing path-target dimension for the two defective routes. In particular, the object-relative Relationship cursor test continues on the same object and checks a changed `name`, while component coverage does not provide a cross-parent cursor rejection case.

This explains why both defects can coexist with otherwise useful cursor regression coverage.

## 9. Required downstream verification matrix

The future M3 contract/architecture/steps should require a closed cursor identity matrix across all 12 routes.

At minimum:

```text
positive
    same route + same path target + same filters -> continuation accepted
    limit may change between pages

negative route identity
    cursor from another cursor-bearing route -> invalid_cursor

negative path identity
    every path-scoped paginated route rejects a cursor issued for a different path target

negative filter identity
    changing any membership-affecting query filter -> invalid_cursor

ObjectTemplate parent tri-state
    omitted cursor rejected under root-only
    root-only cursor rejected under omitted
    exact parent A cursor rejected under exact parent B

lifecycle
    global cursor rejected on object-scoped route
    object A cursor rejected for object B

key shape
    malformed / wrong-length / wrong-type key -> invalid_cursor
```

The two identified fixes must have explicit API-level regression cases, not only unit-level cursor codec tests.

## 10. Consolidated conclusion

```text
cursor-bearing public routes audited      12 / 12
complete current identities               10 / 12
known incomplete identities                2 / 12
new defects found by this cross-check       0
keyset-key defects                           0

required M3 corrections
    OBJ-GET-03 add parent_object_id
    OBJ-GET-06 add object_id
```

This audit confirms the cursor portion of Area B and provides a single complete matrix for M3 contract, architecture and implementation evidence.
