# M4 WIP — Object component-slot navigation cursor

Status: CURSOR CONTRACT REVALIDATED / M4 WIP / ALWAYS NON-NORMATIVE

## Scope

This note records the ratified route-local cursor semantics for:

```http
GET /api/v1/core/objects/{parent_object_id}/components/{slot_name}
    ?cursor=...
    &limit=...
```

It is an M4 discovery checkpoint only. It does not authorize implementation and does not modify the global AS-IS cursor contract.

Public route ownership remains in:

```text
object-components-navigation-public-contract.md
```

The one-statement runtime path is owned by:

```text
object-components-navigation-data-path.md
```

## Ratified cursor rule

The cursor identifies one semantic slot collection and one keyset position. It is not a snapshot of the parent Object generation or of cross-request membership.

```text
codec route identity
    object_component_slot_children

semantic collection identity
    parent_object_id
    slot_name
    slot_declaring_template_id

position
    child_object_id ASC

limit
    excluded from semantic identity
```

`slot_declaring_template_id` remains internal opaque cursor material. Its presence in the cursor does not justify exposing it as a public path/query parameter or response field.

The public pair `(parent_object_id, slot_name)` is not sufficient across `SCHEMA_CHANGE`, because the same public path can later resolve to a different semantic slot declaration. Binding `slot_declaring_template_id` prevents continuation against a replacement collection.

Example:

```text
issued cursor
    parent = P
    slot_name = interfaces
    slot_declaring_template_id = A

current same-name slot after SCHEMA_CHANGE
    parent = P
    slot_name = interfaces
    slot_declaring_template_id = B

A != B
    -> 400 invalid_cursor
```

## Deliberately excluded identity material

The cursor does not bind:

```text
parent template_version
parent revision
target_template_id
effective ordinal / position
child canonical_name
```

Rationale:

- the parent exact version may change while preserving the same semantic slot;
- `revision` is intrinsic Object-row freshness metadata, not collection identity;
- target widening preserves semantic slot identity and must not invalidate pagination merely because the accepted target lineage broadens;
- component position is not route ordering or semantic slot identity;
- child `canonical_name` is projected display state and does not affect membership identity or keyset position.

Therefore these changes preserve cursor compatibility when `(slot_declaring_template_id, slot_name)` remains unchanged:

```text
parent SCHEMA_CHANGE preserving the semantic slot
component target widening
ATTACH
DETACH
child RENAME
```

## Public opacity and encoding direction

The public contract exposes only an opaque cursor string. Callers must not inspect or construct its internal representation.

The existing cursor envelope remains an acceptable M4 realization candidate:

```json
{
  "v": 1,
  "route": "object_component_slot_children",
  "filters": {
    "parent_object_id": "<uuid>",
    "slot_name": "interfaces",
    "slot_declaring_template_id": "<uuid>"
  },
  "key": ["<child-object-uuid>"]
}
```

Current implementation-direction properties remain:

```text
canonical JSON
URL-safe Base64
stripped Base64 padding
no server-side cursor state
no route-specific signing requirement
new route identity
no global envelope-version bump
```

Those carrier details are implementation/codec direction, not caller-visible semantics.

## Failure precedence

Static cursor validation occurs before database access.

Any cursor that is malformed or statically incompatible with the request returns:

```text
400 invalid_cursor
```

including:

```text
invalid Base64 / JSON / envelope version
wrong codec route identity
different parent_object_id
different slot_name
missing/wrong-type slot_declaring_template_id
wrong-length/wrong-type/malformed child_object_id position key
```

Changing `limit` does not invalidate the cursor.

A structurally valid cursor is then compared with current slot state inside the same authoritative PostgreSQL statement that reads the page:

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

No preliminary or diagnostic-only database lookup is introduced solely for cursor validation.

## Cross-request semantics

The cursor is a continuation token, not a repeatable dataset snapshot, export token or CDC token.

Between pages:

```text
DETACH of a future child
    -> that child may disappear from later pages

ATTACH with child_object_id > cursor position
    -> may appear in a later page

ATTACH with child_object_id <= cursor position
    -> may not be observed by that continuation

child RENAME
    -> later page may expose the new canonical_name
```

This is ordinary keyset behavior over current state.

Semantic slot replacement is different from membership churn and invalidates the token. Current slot removal yields `404 object_component_slot` because the nested resource is absent in that request snapshot.

If a slot with the same semantic identity is later present again, an older cursor may again be semantically compatible. M4 does not add parent revision/version solely to encode temporal continuity that the cursor contract does not promise.

## next_cursor generation

The route reads at most:

```text
limit + 1 children
```

Then:

```text
returned row count <= limit
    -> next_cursor = null

returned row count > limit
    -> return first limit children
    -> next_cursor built from:
         parent_object_id
         slot_name
         current slot_declaring_template_id
         last returned child_object_id
```

No additional database statement, model-plane lookup or cache lookup is required to generate the token.

## Cost consequence

Cursor support adds:

```text
PostgreSQL statements          +0
model-plane reads              +0
cache lookups                  +0
recursive traversal            +0
explicit locks                 +0
server-side cursor storage     +0
```

Only small encode/decode work and the normal current semantic-id equality/keyset predicates are added.

## Required verification matrix

Positive cases:

```text
same route + parent + slot + semantic slot identity
    -> continuation accepted

limit changed
    -> accepted

ATTACH/DETACH between requests
    -> cursor structurally remains valid

child RENAME
    -> remains valid

target widening preserving semantic slot identity
    -> remains valid

parent schema-version change preserving semantic slot identity
    -> remains valid
```

Negative/static cases:

```text
old AS-IS generic object_components cursor
wrong route
wrong parent
wrong slot name
malformed semantic-id carrier
malformed position key
    -> 400 invalid_cursor
```

Current-state cases:

```text
parent absent
    -> 404 object

slot absent
    -> 404 object_component_slot

same public parent/slot path but declaring-template identity changed
    -> 400 invalid_cursor
```

## Ratified discovery takeaway

```text
cursor identifies semantic slot collection,
not parent generation and not membership snapshot

identity
    parent_object_id
    slot_name
    slot_declaring_template_id

position
    child_object_id ASC

limit
    not identity

slot removal
    -> 404 object_component_slot

same-name semantic replacement
    -> 400 invalid_cursor

same semantic slot across SCHEMA_CHANGE/widening
    -> cursor remains valid

ATTACH / DETACH / child RENAME
    -> do not structurally invalidate cursor

public cursor remains opaque
runtime DB/model/cache overhead for cursor generation
    -> zero additional reads
```
