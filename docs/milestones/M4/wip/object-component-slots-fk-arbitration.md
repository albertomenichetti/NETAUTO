# M4 WIP — Object component-slot FK arbitration evidence

Status: FROZEN DISCOVERY INPUT / M4 WIP / ALWAYS NON-NORMATIVE

## Scope

This note records the PostgreSQL-level evidence supporting the current `object_component_slots` candidate as the narrow ATTACH / SCHEMA_CHANGE arbitration boundary.

It does not freeze the global M4 concurrency architecture. It proves only that the candidate relational key can distinguish the two classes of slot transition that need different concurrency behavior.

## Candidate relation

Conceptually:

```text
object_component_slots
    object_id
    slot_declaring_template_id
    slot_name
    target_template_id
```

Ownership edge:

```text
object_components
    child_object_id
    parent_object_id
    slot_declaring_template_id
    slot_name
```

Candidate FK:

```text
(parent_object_id, slot_declaring_template_id, slot_name)
    ->
(object_id, slot_declaring_template_id, slot_name)
```

The referenced columns are the current semantic slot identity for one Object.

`target_template_id` is deliberately not part of the referenced key.

## PostgreSQL FK insert behavior

PostgreSQL referential-integrity checking for an INSERT into the referencing table performs the referenced-row existence check using a `FOR KEY SHARE` lookup on the referenced row.

The important row-lock semantics are:

```text
FOR KEY SHARE
    blocks DELETE of the referenced row
    blocks UPDATE that changes referenced key values
    does NOT block ordinary non-key UPDATE
```

An UPDATE that does not modify a key usable by a foreign key uses the weaker `FOR NO KEY UPDATE` class and does not conflict with the key-share lock.

This matches the desired semantic split.

## REMOVE slot

REMOVE means deleting the current slot row.

Race:

```text
ATTACH edge INSERT
    -> FK check / key-share protection of current slot identity

SCHEMA_CHANGE REMOVE
    -> DELETE current slot row
```

Possible serial outcomes:

```text
REMOVE commits first
    -> later ATTACH cannot satisfy FK

ATTACH commits first
    -> REMOVE cannot delete referenced slot while edge exists
```

No complete parent Object binding lock is required merely to obtain this arbitration.

## Semantic identity replacement

A same-name slot with a different declaring lineage is a different semantic slot.

Replacement changes:

```text
slot_declaring_template_id
```

which participates in the referenced FK key.

Therefore replacement is a key-changing transition.

Race:

```text
ATTACH references old semantic key
vs
SCHEMA_CHANGE changes old semantic key to new one
```

The key-share / key-changing-update conflict prevents an old edge from being silently reinterpreted under the new declaring lineage.

If the old slot has no edge, the key transition may proceed.

## Target widening

Normal ObjectTemplate slot evolution may widen:

```text
old target descendant
    -> new target ancestor
```

`target_template_id` is intentionally a non-key column on `object_component_slots`.

Therefore:

```text
ATTACH FK key-share
```

does not inherently block:

```text
SCHEMA_CHANGE non-key UPDATE target_template_id
```

This concurrency is semantically safe because every child compatible with the old narrower target remains compatible with the new wider target.

Thus the relational shape avoids a false dependency:

```text
parent template version changed
    !=
ATTACH must fail
```

Only a current semantic-slot identity change/removal must arbitrate with the edge INSERT.

## Position/order updates

Current candidate does not persist effective slot ordering in `object_component_slots` because no identified runtime hot path consumes it.

If ordering is later materialized as another non-key column, position-only changes would likewise not need to conflict with ATTACH membership insertion.

## DETACH interaction

DETACH deletes the referencing edge.

A concurrent SCHEMA_CHANGE REMOVE/replacement is therefore naturally ordered by FK enforcement:

```text
DETACH commits first
    -> last reference may disappear
    -> slot transition may proceed

slot transition attempts first while edge remains
    -> FK prevents invalid removal/key change
```

This supports reopening the generic parent Object lock previously used only as a SCHEMA_CHANGE rendezvous on DETACH.

## What this evidence does NOT prove

This note does not by itself prove:

```text
global deadlock freedom
full ATTACH/DETACH/SCHEMA_CHANGE lock ordering
Object DELETE composition
graph-gate composition
constraint failure -> public error mapping
final isolation level / transaction shape
```

Those remain architecture-phase obligations.

It does establish that the candidate slot FK is technically capable of replacing the **specific parent-binding stabilization mechanism used only to protect slot semantic continuity**.

## Discovery takeaway

The current candidate aligns PostgreSQL locking granularity with domain semantics:

```text
referenced key
    = (object_id, slot_declaring_template_id, slot_name)
    = current semantic slot identity

DELETE / key change
    = slot removal or semantic replacement
    = must conflict with ATTACH

non-key target_template_id UPDATE
    = monotonic target widening
    = need not conflict with ATTACH
```

This is stronger and less conservative than serializing ATTACH against every parent Object `template_version` change.
