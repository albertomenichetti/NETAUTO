# M4 WIP — Object component-slot navigation cursor

Status: FROZEN DISCOVERY INPUT / M4 WIP / ALWAYS NON-NORMATIVE

## Scope

This note records the current route-local cursor candidate for:

```http
GET /api/v1/core/objects/{parent_object_id}/components/{slot_name}
    ?cursor=...
    &limit=...
```

It is a discovery checkpoint only. It does not authorize implementation and does not modify the global AS-IS cursor contract.

Public route ownership remains in:

```text
object-components-navigation-public-contract.md
```

The one-statement runtime path is owned by:

```text
object-components-navigation-data-path.md
```

The semantic slot materialization used by this candidate is owned by:

```text
object-component-slots-data-plane-materialization.md
```

## Revalidated cursor rule

The consolidated AS-IS rule remains the baseline:

```text
cursor query identity
    = route identity
    + every membership-affecting path target
    + every membership-affecting query filter
    + required semantic identity/presence material

cursor position
    = complete canonical ordering tuple

limit
    = not semantic identity
```

The M4 route changes one important detail relative to the AS-IS generic Object-components route: the public path identifies one current semantic slot collection.

A public path pair:

```text
(parent_object_id, slot_name)
```

is not sufficient to identify that collection across Object `SCHEMA_CHANGE`, because the same path can later resolve to a semantically different slot declaration.

The semantic slot key remains:

```text
(slot_declaring_template_id, slot_name)
```

Therefore the cursor must also bind the current internal `slot_declaring_template_id`.

## Candidate query identity and position

```text
codec route identity
    object_component_slot_children

semantic query identity
    parent_object_id
    slot_name
    slot_declaring_template_id

position
    child_object_id ASC

limit
    excluded from semantic identity
```

`slot_declaring_template_id` remains internal semantic identity material. Its presence in an opaque cursor does not justify exposing it as a normal public response field or request parameter.

## Why `slot_declaring_template_id` is required

Consider a first page produced from:

```text
parent_object_id = P
slot_name = interfaces
slot_declaring_template_id = A
last child = C100
```

A later `SCHEMA_CHANGE` may replace the current slot so that the same public path now resolves to:

```text
parent_object_id = P
slot_name = interfaces
slot_declaring_template_id = B
```

If the cursor carried only `P + interfaces`, the old token could continue with:

```text
child_object_id > C100
```

against a different semantic slot collection.

That is not ordinary cross-request membership churn. It is continuation of a keyset position against a different nested semantic resource.

Binding `slot_declaring_template_id` makes the replacement detectable and yields `400 invalid_cursor`.

## Deliberately excluded identity material

The cursor does not bind:

```text
parent template_version
target_template_id
effective_ordinal / position
child canonical_name
```

Rationale:

- parent `template_version` may change while preserving the same semantic slot;
- `target_template_id` is intentionally non-key in the current slot/FK candidate and target widening must not invalidate pagination by itself;
- effective ordinal/position is not currently materialized and is not part of route ordering;
- child `canonical_name` is projected display state and does not affect collection identity or keyset ordering.

This preserves cursor compatibility across changes that do not replace the semantic slot identity.

## Opaque encoding candidate

The existing cursor envelope remains sufficient:

```json
{
  "v": 1,
  "route": "object_component_slot_children",
  "filters": {
    "parent_object_id": "<uuid>",
    "slot_name": "interfaces",
    "slot_declaring_template_id": "<uuid>"
  },
  "key": [
    "<child-object-uuid>"
  ]
}
```

The candidate retains:

```text
canonical JSON
URL-safe Base64
stripped Base64 padding
no server-side cursor state
no cursor signing requirement introduced by this checkpoint
```

A new codec route identity is preferred over reusing AS-IS `object_components` because the public collection semantics changed from a generic cross-slot route with an optional slot filter to one exact slot collection.

No global cursor envelope version bump is justified by this local semantic change. `v = 1` remains suitable while the envelope structure and decoding rules remain unchanged.

A future change to envelope semantics, canonical ordering or position shape must reopen codec/version compatibility explicitly.

## Failure precedence

Transport/request validation remains separate from current-resource classification.

### Before database access

Any cursor that is structurally malformed or statically incompatible with the request is rejected as:

```text
400 invalid_cursor
```

This includes:

```text
invalid Base64/JSON/envelope version
wrong codec route identity
different parent_object_id
different slot_name
missing/wrong-type slot_declaring_template_id carrier
wrong-length/wrong-type/malformed child_object_id position key
```

`limit` may change between pages and does not make the cursor incompatible.

### In the authoritative PostgreSQL statement snapshot

A cursor can be structurally valid and still need comparison with current slot state. The single route statement must classify in this order:

```text
parent absent
    -> 404 resource_not_found / object

parent exists + requested current slot absent
    -> 404 resource_not_found / object_component_slot

parent exists + slot exists
+ cursor slot_declaring_template_id != current slot_declaring_template_id
    -> 400 invalid_cursor

parent exists + slot exists
+ cursor semantic identity matches
    -> normal keyset continuation
```

This ordering intentionally treats current resource absence as current-resource absence, while semantic replacement of an existing path target is an incompatible continuation token.

No diagnostic-only query is introduced.

## Single-statement validation

The cursor's internal semantic identity must not create a preliminary lookup.

The route statement already reads the current materialized slot row:

```text
object_component_slots
    object_id
    slot_declaring_template_id
    slot_name
```

Therefore it can compare:

```text
current slot_declaring_template_id
    vs
cursor slot_declaring_template_id
```

inside the same PostgreSQL statement snapshot that supplies current membership and child names.

The bounded membership branch may additionally be gated by the matching semantic identity so that a stale/replaced-slot cursor does not scan a page that will be rejected.

## Concurrency interpretation

The cursor is not a transaction snapshot and does not promise repeatable membership across requests.

Concurrent:

```text
ATTACH
DETACH
child RENAME
```

may change later pages according to normal keyset semantics.

A target widening or parent schema-version transition that preserves:

```text
(slot_declaring_template_id, slot_name)
```

keeps the cursor semantically compatible.

A semantic slot replacement that changes `slot_declaring_template_id` invalidates the old cursor.

A current slot removal yields `404 object_component_slot` because the nested resource does not exist in that request's statement snapshot.

If a slot with the same semantic identity is later present again, an older cursor can again be semantically compatible. This is consistent with the global rule that cursors are not cross-request snapshots and membership stability is not guaranteed.

## Cost model

Cursor generation does not add a database statement or model-plane lookup.

All required values are already available from the page request:

```text
parent_object_id
slot_name
slot_declaring_template_id
last child_object_id
```

Candidate runtime delta:

```text
PostgreSQL statements          +0
model-plane reads              +0
cache lookups                  +0
recursive traversal            +0
explicit locks                 +0
server-side cursor storage     +0

application work
    small canonical-JSON serialization
    small URL-safe Base64 encode/decode

continuation DB work
    one UUID semantic-identity equality check
    normal child_object_id keyset predicate
```

The token becomes modestly larger because it carries one additional UUID. This is intentionally preferred over an extra runtime read or weakening semantic isolation.

## Required downstream verification matrix

Positive cases:

```text
same codec route + parent + slot + semantic slot identity
    -> continuation accepted

limit changed
    -> continuation accepted

ATTACH/DETACH between requests
    -> cursor remains structurally compatible

child RENAME between requests
    -> cursor remains structurally compatible

target widening preserving semantic slot identity
    -> cursor remains compatible

parent schema-version change preserving semantic slot identity
    -> cursor remains compatible
```

Negative/static cases:

```text
AS-IS object_components cursor on new route
    -> invalid_cursor

different route
    -> invalid_cursor

different parent
    -> invalid_cursor

different slot name
    -> invalid_cursor

malformed semantic-id carrier
malformed/wrong-length/wrong-type position key
    -> invalid_cursor
```

Current-state cases:

```text
parent absent
    -> 404 object

parent exists + slot absent
    -> 404 object_component_slot

same public parent/slot path but current declaring-template id changed
    -> invalid_cursor
```

The semantic-replacement case requires explicit API-level regression evidence; codec-only tests are insufficient because current slot identity is a database fact.

## Frozen discovery takeaway

```text
Object component-slot cursor

codec route
    object_component_slot_children

identity
    parent_object_id
    slot_name
    slot_declaring_template_id

position
    child_object_id ASC

limit
    not identity

semantic replacement
    -> 400 invalid_cursor

current slot removal
    -> 404 object_component_slot

target widening / same semantic slot
    -> cursor remains compatible

encoding
    existing v1 canonical-JSON + base64url envelope
    new route identity
    no global version bump

runtime cost
    +0 PostgreSQL statements
    +0 model-plane reads
    +0 cache lookups
    small serialization/transport overhead only

validation
    current semantic slot comparison remains inside the same authoritative one-statement snapshot
```
