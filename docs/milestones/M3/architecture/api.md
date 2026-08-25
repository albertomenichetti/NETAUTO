# M3 — Public API and Cursor Architecture

**Status:** DESIGN IN PROGRESS — ADP-04 CLOSED; ADP-05 OPEN

**Authority:** M3 TO-BE ARCHITECTURE — PUBLIC API / CURSOR OWNER

## Purpose and authority boundary

This document owns the M3 TO-BE public cursor-identity realization and, when ADP-05 is closed, the HTTP lexical carrier for the ObjectTemplate `parent_template_id` tri-state.

It derives from the frozen M3 contract and changes only the explicit M3 public API deltas. Delivered route identities, DTOs, pagination model, limit semantics, error catalogue and strict query handling remain owned by the current AS-IS except where the frozen contract explicitly changes them.

Current design ownership:

```text
ADP-04 — Cursor identity realization                    CLOSED
ADP-05 — ObjectTemplate nullable HTTP query carrier     OPEN
```

Implementation remains unauthorized while the M3 architecture set is not frozen.

## Frozen contract inputs

This owner realizes the API-side portions of:

```text
M3-OUT-04 — Public read compatibility
M3-OUT-05 — Complete cursor query identity
M3-OUT-07 — ObjectTemplate root-only public filter
M3-OUT-08 — Regression and traceability closure

M3-AC-09 — Complete twelve-route cursor binding
M3-AC-10 — Object components cross-parent cursor rejection
M3-AC-11 — Object Relationship cross-object cursor rejection
M3-AC-12 — Cursor keyset completeness
```

The ObjectTemplate HTTP `parent_template_id=null` lexical parser itself remains ADP-05 and is not closed by this document yet.

# ADP-04 — CLOSED — Cursor identity realization

## 1. Preserve the delivered opaque cursor codec

M3 keeps the delivered version-1 opaque cursor payload:

```text
v
route
filters
key
```

The current codec behavior remains the target:

```text
decode accepts only when
    payload version matches
    route matches exactly
    filters match exactly
    key is a list

malformed or incompatible token
    -> 400 invalid_cursor
```

M3 does not introduce a new cursor format, cursor service, client-authored cursor, cursor introspection API or cross-release compatibility promise.

No cursor codec version bump is required by ADP-04 because the payload structure and comparison semantics do not change. Tokens whose semantic `filters` no longer match a corrected M3 query identity are rejected naturally as incompatible.

## 2. Canonical cursor identity construction

For every cursor-bearing route, application code constructs one canonical query identity after lexical request parsing and application request-semantics validation.

Logical flow:

```text
HTTP lexical carrier parsing
    -> application request semantics
    -> canonical cursor identity
         route
         filters
    -> decode incoming cursor against that identity
    -> persistence page using decoded key
    -> encode next cursor using the SAME canonical identity
```

The architectural requirement is one semantic identity construction reused for both decode and encode. M3 does not require a new Python class if the existing `route: str` plus `filters: dict[str, JsonValue]` representation remains sufficient.

Two independently constructed identities for decode versus encode are not allowed when they can diverge semantically.

## 3. Frozen identity rule

For every public paginated route:

```text
cursor query identity
    = route identity
    + every path target that changes collection membership
    + every active query filter that changes collection membership
    + any explicit presence bit required to distinguish semantically different filter states

cursor position key
    = complete canonical keyset-ordering tuple

limit
    = excluded from semantic query identity
```

`cursor` itself is not part of query identity.

Changing `limit` between page requests remains valid when the semantic query identity is unchanged.

## 4. Canonical filter carriers

Cursor `filters` are built from already-parsed semantic request values, not raw lexical spellings.

Canonical internal carriers are:

```text
UUID       -> str(UUID)
enum       -> enum.value
datetime   -> existing canonical UTC timestamp carrier
bool       -> bool
int        -> int
string     -> string value
absent     -> None
```

This preserves semantic identity rather than raw textual identity. Equivalent accepted lexical forms that parse to the same semantic value converge to the same internal cursor filter carrier.

Lifecycle timestamp filters and position timestamps continue to use the delivered canonical datetime representation used by the application cursor path.

## 5. Complete twelve-route matrix

| # | Public route | Codec route id | Canonical semantic `filters` | Complete position key |
|---:|---|---|---|---|
| 1 | `GET /api/v1/core/datatypes` | `datatypes` | `namespace`, `name` | `(namespace, name)` |
| 2 | `GET /api/v1/core/datatypes/{datatype_id}/versions` | `datatype_versions` | `datatype_id`, `status` | `(version)` |
| 3 | `GET /api/v1/core/object-templates` | `object_templates` | `namespace`, `name`, `abstract`, `parent_template_id`, `parent_filter_set` | `(namespace, name)` |
| 4 | `GET /api/v1/core/object-templates/{template_id}/versions` | `object_template_versions` | `template_id`, `status` | `(version)` |
| 5 | `GET /api/v1/core/object-templates/{template_id}/relationship-capabilities` | `relationship_capabilities` | `template_id`, `name` | `(resolution_id)` |
| 6 | `GET /api/v1/core/objects` | `objects` | `template_id`, `template_version`, `canonical_name` | `(id)` |
| 7 | `GET /api/v1/core/objects/{parent_object_id}/components` | `object_components` | `parent_object_id`, `slot_name` | `(child_object_id)` |
| 8 | `GET /api/v1/core/objects/{object_id}/relationships` | `object_relationships` | `object_id`, `relationship_definition_id`, `name` | `(relationship_id, destination_object_id, name)` |
| 9 | `GET /api/v1/core/objects/{object_id}/lifecycle-events` | `lifecycle_events` | lifecycle filters + `involving_object_id=<path object>` | `(occurred_at, id)` DESC |
| 10 | `GET /api/v1/core/relationship-definitions` | `relationship_definitions` | `{}` | `(id)` |
| 11 | `GET /api/v1/core/relationship-definitions/{relationship_definition_id}/versions` | `relationship_definition_versions` | `definition_id`, `status` | `(version)` |
| 12 | `GET /api/v1/core/lifecycle-events` | `lifecycle_events` | all global lifecycle filters + `involving_object_id=None` | `(occurred_at, id)` DESC |

This matrix is complete for the frozen twelve-route cursor census. No additional cursor-bearing public route is introduced by M3.

## 6. M3 cursor correction — Object components

Delivered incomplete identity:

```text
route = object_components
filters = {
    slot_name
}
```

M3 target identity:

```text
route = object_components
filters = {
    parent_object_id: str(parent_object_id),
    slot_name: slot_name,
}
key = [str(child_object_id)]
```

Therefore:

```text
same parent + same filters
    -> continuation compatible

parent A cursor on parent B
    -> 400 invalid_cursor
```

The position key remains `child_object_id`; M3 adds no keyset component for the path target because path identity belongs in semantic `filters`, not position.

## 7. M3 cursor correction — Object-relative Relationships

Delivered incomplete identity:

```text
route = object_relationships
filters = {
    relationship_definition_id,
    name,
}
```

M3 target identity:

```text
route = object_relationships
filters = {
    object_id: str(object_id),
    relationship_definition_id:
        None or str(relationship_definition_id),
    name: name,
}
key = [
    str(relationship_id),
    str(destination_object_id),
    name,
]
```

Therefore:

```text
same Object + same filters
    -> continuation compatible

object A cursor on object B
    -> 400 invalid_cursor
```

The complete canonical position remains:

```text
(relationship_id, destination_object_id, name)
```

ADP-02 already freezes semantic-view derivation/deduplication before this public keyset/order/limit stage.

## 8. ObjectTemplate parent-filter tri-state in cursor identity

The existing internal cursor identity model is retained:

```text
parent filter omitted
    parent_template_id = None
    parent_filter_set  = False

root-only filter
    parent_template_id = None
    parent_filter_set  = True

exact parent filter
    parent_template_id = str(parent_uuid)
    parent_filter_set  = True
```

This guarantees:

```text
omitted cursor != root-only cursor
root-only cursor != exact-parent cursor
parent A cursor != parent B cursor
```

`parent_filter_set` remains internal only. It is not a public HTTP query parameter, response field or CLI parameter.

ADP-05 must define the HTTP lexical parser that produces the root-only internal state from exact lowercase `parent_template_id=null`; ADP-05 must not redefine this cursor identity model.

## 9. Lifecycle route separation

Global and Object-scoped lifecycle continue to share:

```text
route = lifecycle_events
```

They remain semantically distinct through `filters`:

```text
global lifecycle
    involving_object_id = None
    object_id may be an ordinary global query filter

Object-scoped lifecycle for Object A
    involving_object_id = str(A)
    object_id = None
```

Therefore:

```text
global cursor on Object-scoped route
    -> invalid_cursor

Object A cursor on Object B
    -> invalid_cursor
```

No separate lifecycle codec route identifier is required.

## 10. Position-key completeness

M3 changes no canonical keyset ordering tuple.

The position key must always equal the complete tuple used by the public collection's keyset predicate and canonical `ORDER BY`:

```text
DataType lineages                 (namespace, name)
DataType versions                 (version)
ObjectTemplate lineages           (namespace, name)
ObjectTemplate versions           (version)
Relationship capabilities         (resolution_id)
Objects                            (id)
Object components                 (child_object_id)
Object Relationships              (relationship_id, destination_object_id, name)
RelationshipDefinitions           (id)
RelationshipDefinition versions   (version)
lifecycle                         (occurred_at, id) DESC
```

Path targets for lineage-local collections remain semantic identity filters and do not need to be duplicated inside local position keys.

## 11. Cursor key decoding

After route/filter compatibility succeeds, each application route validates the decoded `key` as the exact carrier shape required by its canonical ordering tuple.

Wrong length, wrong scalar type, unparsable UUID/timestamp or otherwise incompatible key carrier remains:

```text
400 invalid_cursor
```

M3 does not add cursor-specific diagnostic variants or expose internal payload details.

## 12. Limit semantics

`limit` remains deliberately absent from `filters` and `key`.

```text
same semantic query + different limit
    -> valid continuation
```

The new limit changes only page size, not collection membership identity or current keyset position.

## 13. Cross-release behavior

M3 preserves the public non-goal of cursor compatibility across future releases.

Because codec structure remains `v=1`, existing tokens may continue incidentally when their route/filters/key remain semantically identical. No client guarantee is created.

For the two corrected M3 identities, an older token that lacks the required path target in `filters` no longer matches the target identity and is correctly rejected as `invalid_cursor`.

# ADP-05 — OPEN — ObjectTemplate nullable HTTP query carrier

ADP-05 must define the strict HTTP lexical carrier for:

```text
parent_template_id omitted
parent_template_id=<UUID>
parent_template_id=null
```

while preserving repeated/malformed query rejection and producing exactly the internal cursor/persistence state frozen above.

ADP-05 must not expose `parent_filter_set` publicly and must not introduce any alternate root sentinel.

# Downstream verification constraints

`verification.md` / ADP-08 must prove for all twelve routes:

```text
same route + same path target + same membership filters
    -> continuation accepted

different route identity
    -> invalid_cursor

different path target on every path-scoped cursor route
    -> invalid_cursor

changing any membership-affecting filter
    -> invalid_cursor

changing limit only
    -> continuation accepted

ObjectTemplate tri-state
    omitted != root-only != exact parent A != exact parent B

lifecycle
    global != Object-scoped
    Object A != Object B

malformed / wrong-length / wrong-type key
    -> invalid_cursor
```

The two M3 path-binding corrections require explicit API-level regression evidence.

# Preserved AS-IS responsibilities

ADP-04 does not change:

```text
opaque cursor transport
base64/JSON implementation as a public non-contract detail
codec payload field meanings
codec version = 1
canonical route ordering
public pagination limit defaults/range
public DTOs
strict query validation
finite invalid_cursor failure surface
```

# ADP status

```text
ADP-04  CLOSED
ADP-05  OPEN
```

No implementation authority is created by this closure. The architecture set remains `DESIGN IN PROGRESS — NOT FROZEN`.
