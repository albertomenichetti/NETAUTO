# M4 WIP — Object component-slot navigation public contract

Status: PUBLIC CONTRACT REVALIDATED / CURSOR + DATA PATH ACTIVE REVALIDATION / M4 WIP / ALWAYS NON-NORMATIVE

## Scope

This note records the ratified route-local public contract for Object direct-component navigation during the M4 top-down sweep.

The public contract is a reviewed local discovery checkpoint only; everything under `wip/` remains globally non-normative and does not authorize implementation.

The current data-path candidate is recorded separately in:

```text
object-components-navigation-data-path.md
```

The current cursor candidate is recorded separately in:

```text
object-components-navigation-cursor.md
```

Both use the per-Object current-slot materialization owned by the current Object component-persistence direction.

After the public-contract revalidation, the remaining route-local review is:

```text
cursor semantic identity / continuation behavior
data path / coherence confirmation
failure precedence integration
cost + architecture handoff
final physical indexes / EXPLAIN evidence
```

The previous generic global read-coherence question is narrowed by the one-statement data-path candidate: all mutable route response facts and current semantic-slot cursor validation are intended to come from one PostgreSQL statement snapshot.

## Ratified route

```http
GET /api/v1/core/objects/{parent_object_id}/components/{slot_name}
    ?cursor=...
    &limit=...
```

Path parameters:

```text
parent_object_id
    UUID

slot_name
    canonical component-slot name
    ^[a-z][a-z0-9_]{0,63}$
```

Query parameters:

```text
cursor
    opaque pagination cursor
    optional

limit
    positive integer
    1..500
    optional
    default 100
```

No request body is accepted.

Unknown or repeated query parameters are invalid request input. No additional child filter is part of the M4 contract.

## No public cross-slot collection

The TO-BE public surface does not retain a generic cross-slot navigation route of the form:

```http
GET /api/v1/core/objects/{parent_object_id}/components
```

and does not model `slot_name` as an optional query filter on that route.

Reason:

- TO-BE `GET /objects/{object_id}` already exposes every effective direct component slot and all direct children in the complete first-level Object representation;
- the specialized navigation endpoint is justified by selective, paginated access to one potentially large slot;
- a cross-slot page would duplicate the Object GET representation while introducing an artificial heterogeneous pagination order across unrelated semantic slots.

## Why `slot_name` is a path parameter

`slot_name` identifies the semantic child collection being navigated; it is not merely an arbitrary search filter.

Conceptually:

```text
/objects/{parent}/components/{slot}
    = current child collection of that effective component slot
```

This yields a consistent ownership API family:

```http
GET  /objects/{parent}/components/{slot}
POST /objects/{parent}/components/{slot}/attach
POST /objects/{parent}/components/{slot}/detach
```

The path therefore identifies the nested collection; query parameters only control how that collection is paged.

## Query-parameter role

The only accepted query parameters are pagination controls:

```text
cursor
limit
```

`limit` follows the shared bounded-page contract:

```text
1..500
default 100
```

No filter such as child `canonical_name` is introduced without a concrete later consumer requirement.

## Candidate cursor contract — active revalidation

The route retains opaque keyset pagination. The current candidate binds the token to the exact current semantic slot collection.

Candidate identity:

```text
codec route
    object_component_slot_children

semantic query identity
    parent_object_id
    slot_name
    slot_declaring_template_id

position
    child_object_id ASC

limit
    not semantic identity
```

`slot_declaring_template_id` remains internal opaque cursor material, not a public path/query parameter or response field.

The rationale is that the same public `(parent_object_id, slot_name)` path can resolve after `SCHEMA_CHANGE` to a different semantic slot declaration. A cursor issued for the previous declaring lineage must not silently continue against a replacement collection.

The current candidate reuses the existing versioned canonical-JSON + URL-safe-Base64 cursor envelope with a new codec route identity; no global envelope-version bump is justified by this local route change.

Static malformed/incompatible cursor carriers remain candidate:

```text
400 invalid_cursor
```

Current-state candidate precedence is:

```text
parent absent
    -> 404 resource_not_found / object

parent exists + current slot absent
    -> 404 resource_not_found / object_component_slot

parent exists + current slot present
+ cursor slot_declaring_template_id differs from current slot
    -> 400 invalid_cursor

matching semantic slot identity
    -> normal keyset continuation
```

Target widening, ATTACH/DETACH, child RENAME, or parent schema-version movement that preserves the same semantic slot identity are candidate cases that should not invalidate the cursor merely because membership/display state changed. Cross-request repeatable membership remains intentionally unpromised.

Detailed encoding, cost and verification cases are owned by `object-components-navigation-cursor.md` and are the next focused review block.

## Ratified response role

The endpoint is a paginated view of the same direct-child representation already used by Object GET:

```json
{
  "items": [
    {
      "id": "<child-object-id>",
      "canonical_name": "eth0"
    }
  ],
  "next_cursor": null
}
```

Canonical ordering is:

```text
child_object_id ASC
```

The route must not create a second poorer or differently shaped public child representation.

The response does not expose:

```text
slot_declaring_template_id
target_template_id
child ObjectTemplate binding
child properties
child components
```

`slot_declaring_template_id` remains internal semantic identity material and is not justified as a normal public child field.

## Ratified slot existence and not-found semantics

The route preserves three distinct public outcomes.

### Parent Object absent

```text
parent Object does not exist
    -> 404 resource_not_found
    -> resource_type = object
```

### Effective slot exists but is empty

```text
parent exists
+ requested slot exists in the parent's current effective slot materialization
+ zero current attached children
    -> 200 OK
    -> {"items": [], "next_cursor": null}
```

An empty valid slot is successful collection navigation, never a not-found result.

### Requested effective slot absent

A syntactically valid `slot_name` that is not present in the existing parent's current effective slot set identifies no nested component-slot resource:

```text
parent exists
+ requested effective slot absent
    -> 404 resource_not_found
    -> resource_type = object_component_slot
```

Bounded detail direction:

```json
{
  "resource_type": "object_component_slot",
  "parent_object_id": "<uuid>",
  "slot_name": "interfaces"
}
```

This is intentionally distinct from mutation-side `ownership_slot_unavailable` semantics.

A malformed `slot_name` transport carrier is rejected by normal request validation before semantic lookup and does not become a semantic slot-not-found result.

## Static request failures ratified in this block

```text
400 invalid_request
    malformed parent_object_id carrier
    malformed slot_name carrier
    malformed/out-of-range limit
    unknown/repeated query parameter
    unsupported request body

400 invalid_cursor
    malformed or statically incompatible cursor
```

The detailed distinction between static cursor incompatibility and current semantic-slot mismatch remains part of the active cursor block.

## Relationship to Object GET

TO-BE Object GET remains the complete first-level representation surface:

```text
GET /objects/{id}
    -> all effective component slots
    -> all direct children
    -> empty valid slots represented as []
```

A caller can therefore distinguish directly from the Object representation:

```text
"disks": []
    -> disks is a valid effective slot and is currently empty

slot key absent
    -> the slot is not part of this Object's current exact effective schema
```

The component-slot navigation endpoint exists for bounded selective access/pagination of one slot, not to compensate for missing component-slot state in Object GET.

## Authority split: ObjectTemplate vs Object instance

The public surfaces answer different questions and are intentionally not duplicates.

ObjectTemplate / exact ObjectTemplateVersion remains the semantic schema authority:

```text
which component slots are defined?
which lineage declares the slot?
what target ObjectTemplate lineage is allowed?
what is the slot's exact model-plane contract?
```

`object_component_slots` is the transactionally maintained current runtime derivative of that contract for a particular Object.

Object runtime reads answer:

```text
which effective slots does this particular Object expose now?
which child Objects are attached to each slot now?
```

Therefore:

```text
ObjectTemplate
    = semantic component-slot definition / contract authority

object_component_slots
    = current per-Object derived data-plane materialization

Object
    = effective runtime slot set + current membership
```

Object GET and this navigation route intentionally do not expose model-plane details such as `target_template_id` or `slot_declaring_template_id` merely because they are materialized internally.

## Current data-path checkpoint — active revalidation

Current candidate from `object-components-navigation-data-path.md`:

```text
one PostgreSQL statement

objects parent PK lookup
LEFT JOIN requested object_component_slots row by (object_id, slot_name)
LEFT/LATERAL bounded object_components page
JOIN child objects for current canonical_name
```

Normal runtime candidate:

```text
0 component-schema cache lookups
0 ObjectTemplate effective-schema reads
0 recursive traversal
0 explicit locks
```

All mutable response facts and current semantic-slot cursor compatibility are intended to come from one statement snapshot.

Cursor generation candidate adds:

```text
0 PostgreSQL statements
0 model-plane reads
0 cache lookups
```

and only small application serialization/transport work.

## Supersession

The ratified public contract supersedes the AS-IS public shape:

```http
GET /objects/{parent_object_id}/components?slot_name=...
```

where `slot_name` is optional and omission means cross-slot listing.

It retains the useful AS-IS pagination concepts `cursor` and `limit` but scopes them to one semantic slot collection. Cursor codec identity/compatibility is finalized by the active cursor review.

## Ratified Block 1 takeaway

```text
Object component-slot navigation public contract

GET /objects/{parent_object_id}/components/{slot_name}
    ?cursor=...
    &limit=...

parent_object_id
    -> UUID

slot_name
    -> ^[a-z][a-z0-9_]{0,63}$

cursor
    -> optional opaque token

limit
    -> 1..500
    -> default 100

no request body
no additional filters
no public generic cross-slot /components collection
same {id, canonical_name} child representation as Object GET
child ordering = child_object_id ASC

malformed request carrier
    -> 400 invalid_request

malformed/static incompatible cursor
    -> 400 invalid_cursor

parent absent
    -> 404 resource_not_found / object

parent exists + slot absent
    -> 404 resource_not_found / object_component_slot

parent exists + slot exists + empty
    -> 200 empty page

parent exists + slot exists + children
    -> 200 bounded page

next focused review
    -> cursor semantic identity and SCHEMA_CHANGE compatibility
```
