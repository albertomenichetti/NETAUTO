# M4 WIP — Object ATTACH bulk child/current-owner read

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the preliminary bulk read shape for the TO-BE batch ATTACH operation:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

with a non-empty `child_object_ids` collection.

## Decision

After the parent exact binding has been read and the requested component slot has been resolved through the READY `component_schema` cache facet, ATTACH performs one bulk PostgreSQL statement over all requested child ids.

That same statement obtains both:

- current child Object facts required for semantic validation;
- current ownership facts, when present.

There is no separate current-owner query after the child read.

Conceptually:

```text
requested child ids
    -> one bulk read

for each requested child id:
    child Object
        id
        template_id
        canonical_name

    current object_components row, if any
        parent_object_id
        slot_declaring_template_id
        slot_name
```

The exact SQL realization may use `LEFT JOIN object_components ON object_components.child_object_id = objects.id` or an equivalent one-statement shape.

## Why combine the reads

ATTACH already needs the current child rows to answer:

```text
does every requested child exist?
is any requested child equal to the parent?
which stable template_id does each child have?
which DISTINCT child template lineages require compatibility evaluation?
what canonical_name is required for edge-oriented lifecycle metadata?
```

Current ownership is keyed by the same child identity because `object_components.child_object_id` is the one-owner authority.

Therefore a second query solely to discover owner state would add a round trip without introducing a distinct semantic source or consistency requirement at this preparatory stage.

## Preliminary classifications

The combined read allows the application to classify the requested batch in memory:

```text
missing child
    -> semantic failure for the atomic batch

child == parent
    -> invalid self ownership

no current ownership row
    -> candidate new attachment

current ownership row matches requested semantic edge
    -> already-current / convergent member

current ownership row differs
    -> currently owned elsewhere / conflicting semantic edge
```

The requested semantic edge is known after parent-slot cache resolution:

```text
parent_object_id
slot_declaring_template_id
slot_name
child_object_id
```

The preliminary current-owner observation is not by itself the final concurrency authority. Final arbitration for concurrent ATTACH/DETACH/ownership races remains to be frozen in the mutation UoW design.

## Minimal child columns

The normal preparatory path does not require child:

```text
template_version
properties
```

Slot compatibility depends on the child's stable `template_id`, not its exact ObjectTemplateVersion.

The useful child payload is therefore bounded to:

```text
id
template_id
canonical_name
```

`canonical_name` is retained because ATTACH lifecycle events currently carry historical child display metadata.

## Compatibility handoff

After this one bulk read:

```text
collect DISTINCT child.template_id
    -> check stable ancestry cache against slot.target_template_id
    -> fill missing ancestry knowledge in bounded bulk on cache miss
```

Different child template lineages may coexist in the same request.

## Frozen conclusion

```text
child existence + stable lineage + lifecycle name + current owner
    -> one PostgreSQL bulk statement
```

No N+1 child reads and no second current-owner round trip are part of the TO-BE ATTACH preparatory path.
