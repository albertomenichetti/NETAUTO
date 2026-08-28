# M4 WIP — Object component-slot navigation public contract

Status: FROZEN DISCOVERY INPUT / M4 WIP / ALWAYS NON-NORMATIVE

## Scope

This note records the accepted route-local public-surface direction for Object direct-component navigation during the M4 top-down sweep.

It freezes only the current discovery checkpoint. Full data path, exact failure code for a nonexistent slot, pagination cursor encoding, physical indexes and global read-coherence realization remain subject to later route-local and architecture closure.

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

## Slot existence distinction

The route must preserve the semantic distinction between:

```text
parent exists + slot exists + zero current children
    -> successful empty page

parent exists + requested slot does not exist in the parent's current exact effective schema
    -> explicit slot-not-found style failure
```

The exact HTTP status/code for the second case remains open for the next route-local micro-decision.

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

ObjectTemplate / exact ObjectTemplateVersion is the schema authority:

```text
which component slots are defined?
which lineage declares the slot?
what target ObjectTemplate lineage is allowed?
what is the slot's exact model-plane contract/position?
```

Object GET is the runtime instance projection:

```text
which effective slots does this particular Object expose
under its current exact ObjectTemplateVersion?
which child Objects are attached to each slot now?
```

Therefore:

```text
ObjectTemplate
    = component-slot definition / contract

Object
    = effective runtime slot set + current membership
```

Object GET intentionally exposes empty effective slots but does not duplicate model-plane details such as `target_template_id`, `slot_declaring_template_id`, declaration position or other ObjectTemplate metadata. Consumers needing those schema details use the ObjectTemplate APIs.

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
empty valid slot != nonexistent slot

ObjectTemplate = slot definition/contract authority
Object GET      = all effective runtime slots, including empty []
slot navigation = paginated current membership of one slot
```
