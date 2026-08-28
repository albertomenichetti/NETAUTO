# M4 WIP — Object component-slot navigation public contract

Status: PUBLIC CONTRACT FROZEN DISCOVERY INPUT / DATA PATH CHECKPOINT ADDED / M4 WIP / ALWAYS NON-NORMATIVE

## Scope

This note records the accepted route-local public-surface direction for Object direct-component navigation during the M4 top-down sweep.

The public contract remains a local discovery checkpoint only.

The current data-path candidate is now recorded separately in:

```text
object-components-navigation-data-path.md
```

and uses the per-Object current-slot materialization from:

```text
object-component-slots-data-plane-materialization.md
```

Current remaining route-local open points are:

```text
pagination cursor identity/encoding and invalid-cursor semantics
final physical indexes / EXPLAIN evidence
```

The previous generic global read-coherence question is narrowed by the new one-statement data path: all mutable route response facts are intended to come from one PostgreSQL statement snapshot.

## Candidate route

```http
GET /api/v1/core/objects/{parent_object_id}/components/{slot_name}?cursor=...&limit=...
```

Path parameters:

```text
parent_object_id: UUID
slot_name: component-slot name
```

Query parameters:

```text
cursor: optional pagination cursor
limit: bounded page size
```

No request body is accepted.

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
    = current child collection of that exact effective component slot
```

This yields a consistent ownership API family:

```http
GET  /objects/{parent}/components/{slot}
POST /objects/{parent}/components/{slot}/attach
POST /objects/{parent}/components/{slot}/detach
```

The path therefore identifies the collection; query parameters describe how that collection is read.

## Query-parameter role

The accepted query parameters are pagination controls:

```text
cursor
limit
```

No additional filter is introduced by this checkpoint.

A future filter such as child `canonical_name` may be considered only if a concrete consumer requirement emerges; it is not part of the current M4 candidate.

## Candidate response role

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

It must not create a second poorer or differently shaped public child representation.

`slot_declaring_template_id` remains internal semantic identity material and is not justified as a normal public child field.

## Slot existence and not-found semantics

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

Candidate bounded detail:

```json
{
  "resource_type": "object_component_slot",
  "parent_object_id": "<uuid>",
  "slot_name": "interfaces"
}
```

This remains intentionally distinct from mutation-side `ownership_slot_unavailable` semantics.

A malformed `slot_name` transport carrier is rejected by normal request validation before semantic lookup and does not become a semantic slot-not-found result.

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

The new `object_component_slots` relation is only the transactionally maintained current runtime derivative of that contract for a particular Object.

Object GET answers:

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

Object GET intentionally does not expose model-plane details such as `target_template_id` or `slot_declaring_template_id` merely because they are materialized internally.

## Current data-path checkpoint

Current candidate from `object-components-navigation-data-path.md`:

```text
one PostgreSQL statement

objects parent PK lookup
LEFT JOIN requested object_component_slots row by (object_id, slot_name)
LEFT/LATERAL bounded object_components page
JOIN child objects for current canonical_name
```

Normal runtime path:

```text
0 component-schema cache lookups
0 ObjectTemplate effective-schema reads
0 recursive traversal
0 explicit locks
```

All mutable response facts come from one statement snapshot.

## Supersession

This checkpoint supersedes the AS-IS public shape:

```http
GET /objects/{parent_object_id}/components?slot_name=...
```

where `slot_name` is optional and omission means cross-slot listing.

It retains the useful AS-IS pagination concepts `cursor` and `limit` but scopes them to one semantic slot collection.

## Frozen discovery takeaway

```text
Object component navigation

GET /objects/{parent_object_id}/components/{slot_name}
    ?cursor=...
    &limit=...

slot_name in path
cursor/limit in query
no public generic cross-slot /components collection
same {id, canonical_name} child representation as Object GET

malformed slot carrier
    -> normal 400 invalid_request boundary

parent absent
    -> 404 resource_not_found / object

parent exists + slot absent
    -> 404 resource_not_found / object_component_slot

parent exists + slot exists + empty
    -> 200 empty page

parent exists + slot exists + children
    -> 200 page

current data-path candidate
    -> 1 PostgreSQL statement
    -> current materialized slot row
    -> bounded membership page
    -> no component-schema cache/model-plane lookup

next open micro-point
    -> cursor identity/encoding/semantics
```