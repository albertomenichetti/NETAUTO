# M3 — Public API and Cursor Architecture

**Status:** DESIGN IN PROGRESS — ADP-04 / ADP-05 CLOSED

**Authority:** M3 TO-BE ARCHITECTURE — PUBLIC API / CURSOR OWNER

## Purpose and authority boundary

This document owns the M3 TO-BE public cursor-identity realization and the HTTP lexical carrier for the ObjectTemplate `parent_template_id` tri-state.

It derives from the frozen M3 contract and changes only the explicit M3 public API deltas. Delivered route identities, DTOs, pagination model, limit semantics, error catalogue and strict query handling remain owned by the current AS-IS except where the frozen contract explicitly changes them.

Current design ownership:

```text
ADP-04 — Cursor identity realization                    CLOSED
ADP-05 — ObjectTemplate nullable HTTP query carrier     CLOSED
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
M3-AC-13 — ObjectTemplate HTTP parent-filter tri-state
M3-AC-14 — ObjectTemplate parent-filter malformed/duplicate rejection
M3-AC-15 — ObjectTemplate parent-filter cursor distinction
```

The corresponding official-CLI explicit-null realization is owned by `cli.md` / ADP-06.

# ADP-04 — CLOSED — Cursor identity realization

## Preserve the delivered opaque cursor codec

M3 keeps the delivered version-1 opaque cursor payload:

```text
v
route
filters
key
```

Decode accepts only when payload version, route and filters match the current canonical query identity and `key` is a list. Malformed or incompatible tokens remain:

```text
400 invalid_cursor
```

M3 introduces no new cursor format, cursor service, client-authored cursor, introspection API or cross-release compatibility promise. No codec version bump is required because payload structure and comparison semantics do not change.

## Canonical cursor identity construction

For every cursor-bearing route, application constructs one canonical query identity after lexical request parsing and request-semantics validation and reuses that exact identity for both incoming decode and outgoing encode:

```text
HTTP lexical carrier parsing
    -> application request semantics
    -> canonical cursor identity
         route
         filters
    -> decode incoming cursor against that identity
    -> persistence page using decoded key
    -> encode next cursor using the SAME identity
```

The implementation may continue using the delivered `route: str` plus `filters: dict[str, JsonValue]` representation. A new identity class is not required.

## Frozen identity rule

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

`cursor` itself is not part of query identity. Changing `limit` alone between pages remains valid.

## Canonical filter carriers

Cursor filters are built from already-parsed semantic values rather than raw lexical spellings:

```text
UUID       -> str(UUID)
enum       -> enum.value
datetime   -> existing canonical UTC timestamp carrier
bool       -> bool
int        -> int
string     -> string value
absent     -> None
```

Lifecycle timestamp filters and cursor position timestamps retain the delivered canonical datetime representation.

## Complete twelve-route matrix

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

## M3 path-target corrections

Object components target identity becomes:

```text
route = object_components
filters = {
    parent_object_id: str(parent_object_id),
    slot_name: slot_name,
}
key = [str(child_object_id)]
```

A cursor issued for parent A is incompatible with parent B. The path target is identity, not position, so the position remains `child_object_id`.

Object-relative Relationship target identity becomes:

```text
route = object_relationships
filters = {
    object_id: str(object_id),
    relationship_definition_id: None or str(relationship_definition_id),
    name: name,
}
key = [str(relationship_id), str(destination_object_id), name]
```

A cursor issued for Object A is incompatible with Object B. The complete position remains `(relationship_id, destination_object_id, name)`; ADP-02 already freezes public semantic deduplication before keyset/order/limit.

## ObjectTemplate tri-state cursor identity

The internal identity model is:

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

Therefore omission, root-only and exact-parent queries are cursor-distinct, as are exact parent A and exact parent B. `parent_filter_set` remains internal only.

## Lifecycle route separation

Global and Object-scoped lifecycle continue to share `route=lifecycle_events`. Their semantic identities remain distinct through `involving_object_id`:

```text
global lifecycle
    involving_object_id = None

Object-scoped lifecycle for A
    involving_object_id = str(A)
```

A global cursor is incompatible with an Object-scoped request, and Object A is incompatible with Object B. No new lifecycle route id is required.

## Position-key and failure rules

M3 changes no canonical keyset tuple. Each decoded `key` is validated as the exact carrier shape required by the issuing route. Wrong length/type, unparsable UUID/timestamp, route mismatch, filter mismatch or malformed payload remains `400 invalid_cursor`.

The public position key must always equal the complete tuple used by the public keyset predicate and canonical `ORDER BY`. Path targets belong in semantic query identity and are not duplicated into local position keys.

# ADP-05 — CLOSED — ObjectTemplate nullable HTTP query carrier

## Public lexical grammar

`GET /api/v1/core/object-templates` exposes one parent filter only:

```text
parent_template_id
```

Its complete M3 HTTP grammar is exactly:

```text
parameter omitted
    -> no parent filter

parent_template_id=<valid UUID carrier>
    -> direct children of that stable ObjectTemplate parent

parent_template_id=null
    -> root ObjectTemplates only
```

The root sentinel is the exact lowercase lexical token `null`.

M3 does not add or accept alternate root sentinels such as:

```text
NULL
None
root
ROOT
empty string
```

No whitespace trimming, case folding or sentinel normalization is introduced.

## HTTP parse pipeline

The adapter preserves raw query-parameter presence separately from the parsed value:

```text
raw parent_template_id ABSENT
    -> parent_template_id = None
    -> parent_filter_set  = False

raw parent_template_id PRESENT and exactly "null"
    -> parent_template_id = None
    -> parent_filter_set  = True

raw parent_template_id PRESENT and valid UUID
    -> parent_template_id = UUID
    -> parent_filter_set  = True

raw parent_template_id PRESENT and anything else
    -> 400 invalid_request
```

The semantic distinction between omission and explicit root-only filtering therefore does not rely on `UUID | None` alone. Both materialize `None`; raw presence supplies the required internal presence bit.

## Nullable UUID lexical adapter

The HTTP typing boundary uses a small nullable-UUID query carrier whose only M3-specific lexical behavior is:

```text
raw value == "null"
    -> Python None

otherwise
    -> delegate unchanged to the delivered FastAPI/Pydantic UUID parser
```

This may be realized with a `BeforeValidator`-style helper or an equivalent local typed adapter. The helper name is implementation-local.

M3 does not introduce a custom UUID grammar. Every non-`null` value is accepted or rejected by the same UUID parsing behavior used by the delivered API.

Consequently:

```text
"null"          -> accepted as explicit root-only carrier
valid UUID      -> accepted as exact parent carrier
""              -> invalid_request
"NULL"          -> invalid_request
"None"          -> invalid_request
"root"          -> invalid_request
malformed UUID  -> invalid_request
```

## Strict duplicate and unknown query handling

The delivered strict query contract remains authoritative. `validate_query()` continues to reject repeated or unknown query parameters before the request is accepted semantically.

Therefore repeated `parent_template_id` remains:

```text
400 invalid_request
```

M3 adds no special `invalid_parent_filter` error code and exposes no parser-internal details.

FastAPI/Pydantic query parsing failures continue through the delivered request-validation handler and map to:

```text
400
code = invalid_request
message = request path/query/body malformed boundary
```

## Layer boundary

ADP-05 is a wire-carrier change only:

```text
HTTP adapter
    omitted / exact lowercase "null" / UUID
        -> UUID | None + parent_filter_set

application
    existing semantic tri-state unchanged

cursor
    ADP-04 identity unchanged

persistence
    existing tri-state unchanged
    parent_filter_set=True + parent_template_id=None -> SQL IS NULL semantics
```

No domain, persistence or cursor-codec redesign is authorized by ADP-05.

`parent_filter_set` remains an internal application/cursor representation detail. It is not added as a public query parameter, body field, DTO field or CLI parameter.

## Cursor interaction

The HTTP carrier maps exactly into the ADP-04 frozen identity:

```text
HTTP omitted
    -> parent_template_id=None
    -> parent_filter_set=False

HTTP parent_template_id=null
    -> parent_template_id=None
    -> parent_filter_set=True

HTTP parent_template_id=<UUID A>
    -> parent_template_id=str(A) in cursor filters
    -> parent_filter_set=True
```

Thus:

```text
omitted cursor != root-only cursor
root-only cursor != exact-parent cursor
parent A cursor != parent B cursor
```

No cursor format/version change is required.

## Downstream CLI consistency constraint

ADP-06 must expose the same public semantics through the official CLI:

```text
parameter omitted
    -> no query pair

UUID / accepted human ObjectTemplate selector
    -> exact UUID query pair

explicit null
    -> lexical query pair parent_template_id=null
    -> no selector lookup
```

ADP-06 may not introduce an alternate CLI root sentinel or expose `parent_filter_set`.

# Downstream verification constraints

`verification.md` / ADP-08 must prove at minimum:

```text
HTTP omission
    -> no parent predicate

HTTP valid UUID
    -> direct children only

HTTP exact lowercase null
    -> roots only

HTTP empty / NULL / None / root / malformed UUID
    -> 400 invalid_request

HTTP repeated parent_template_id
    -> 400 invalid_request

cursor tri-state
    omitted != root-only != exact parent A != exact parent B
    root-only continues root-only pagination successfully
```

ADP-08 must also retain the twelve-route cursor evidence frozen by ADP-04, including changed-limit continuation and the two M3 path-target rejection cases.

# Preserved AS-IS responsibilities

ADP-04 / ADP-05 do not change:

```text
opaque cursor transport and codec v1 structure
public DTOs and route identities
canonical route ordering
public pagination limit defaults/range
strict unknown/repeated query validation
finite invalid_cursor and invalid_request failure surfaces
application ObjectTemplate parent-filter signature
persistence parent-filter semantics
schema / migration / dependency baseline
```

# ADP status

```text
ADP-04  CLOSED
ADP-05  CLOSED
```

No implementation authority is created by these closures. The architecture set remains `DESIGN IN PROGRESS — NOT FROZEN`.
