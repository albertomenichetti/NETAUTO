# Object.SCHEMA_CHANGE components discovery — WIP / NON-NORMATIVE

## Scope

This note records first-phase M4 discovery for `Object.SCHEMA_CHANGE` as it interacts with ownership/components. It assumes the current working M4 candidate that `object_components` persists the stable slot semantic identity:

```text
child_object_id
parent_object_id
slot_declaring_template_id
slot_name
```

`slot_declaring_template_version` is intentionally not persisted because the current ownership fact must survive parent Object schema changes without being rewritten.

Lock/concurrency redesign remains deferred to the global second phase.

## AS-IS component validation

Current SCHEMA_CHANGE loads the source effective schema, then for every outgoing ownership edge:

```text
edge.slot_name
    -> resolve source slot
    -> discover declaring_template_id
    -> form semantic key

semantic key
    -> lookup in target effective schema

load child Object
    -> child.template_id

check target slot target lineage
    vs child.template_id
```

This produces per-edge source-schema rediscovery plus per-child reads and lineage checks.

## Semantic identity should come from the persisted edge

With the M4 edge candidate, each current ownership fact already carries:

```text
SlotSemanticKey = (
    slot_declaring_template_id,
    slot_name
)
```

Therefore SCHEMA_CHANGE must not rediscover the source slot identity from the source effective schema.

The source schema is still required for intrinsic property migration, but not to identify current ownership edges.

## Child compatibility cannot be removed universally

Normal component target evolution is widening toward an ancestor. If publication/version order were strictly aligned, a child admitted to the source target would remain compatible after widening.

However ObjectTemplate versions may be published out of numeric order. Therefore a strictly forward Object version move may still be a semantic narrowing relative to that Object's current source version.

Example:

```text
v4 published first:
    slot -> Server

v3 published later:
    slot -> Device

Device ancestor-of Server
```

Publishing v3 may be valid as a widening relative to the latest published declaration at that time. But an Object currently on v3 moving forward to v4 would see `Device -> Server`, which is narrower for that Object.

Therefore SCHEMA_CHANGE must still verify that every current child remains compatible with the target slot contract.

## Set-based blocker projection

The AS-IS N+1 pattern should be replaced by one set-based blocker predicate using:

```text
object_components
    current semantic edge identity

objects
    child.template_id

object_template_effective_components
    target exact effective slot contract

object_template_ancestry
    stable descendant -> ancestor compatibility
```

Conceptual predicate:

```text
for every outgoing edge:
    target effective component with same
        (slot_declaring_template_id, slot_name)
    must exist

    AND

    child.template_id must be descendant-or-self of
        target_slot.target_template_id
```

A query should return the first blocker (or bounded blocker projection) rather than loading and checking every child in application code.

Conceptual SQL shape:

```sql
SELECT
    edge.child_object_id,
    edge.slot_declaring_template_id,
    edge.slot_name
FROM object_components AS edge
JOIN objects AS child
  ON child.id = edge.child_object_id
LEFT JOIN object_template_effective_components AS target_slot
  ON target_slot.template_id = :template_id
 AND target_slot.template_version = :target_version
 AND target_slot.declaring_template_id = edge.slot_declaring_template_id
 AND target_slot.name = edge.slot_name
LEFT JOIN object_template_ancestry AS ancestry
  ON ancestry.descendant_template_id = child.template_id
 AND ancestry.ancestor_template_id = target_slot.target_template_id
WHERE edge.parent_object_id = :object_id
  AND (
      target_slot.name IS NULL
      OR ancestry.ancestor_template_id IS NULL
  )
LIMIT 1;
```

Exact SQL and indexes remain design work; this is a conceptual data-path target.

## Candidate SCHEMA_CHANGE path

```text
current Object
    PostgreSQL current truth
        id
        template_id
        source_version
        properties

target current admission
    PostgreSQL
        exact target exists
        target PUBLISHED

source compiled exact OTV schema
    read-through immutable cache

target compiled exact OTV schema
    read-through immutable cache

migrate intrinsic properties
    source -> target

one set-based attachment blocker check
    current edges
    + target effective components
    + child template ids
    + stable ancestry materialization

if blocker:
    schema_change_blocked

else:
    one UPDATE objects
        template_version = target
        properties = migrated

    object_components: NO UPDATE

    one SCHEMA_CHANGE lifecycle event
```

## Important invariant

A successful Object schema change does not mutate ownership facts whose semantic slot identity survives. `object_components` remains unchanged; only the current exact contract used to interpret the stable edge changes.

## Working conclusion

> `Object.SCHEMA_CHANGE` should validate current attachments directly from the semantic key materialized on each ownership edge. Child compatibility remains necessary, but the current per-edge source-slot rediscovery and N+1 child/lineage validation should become one set-based blocker projection over target effective components plus stable ancestry. The ownership rows themselves are not rewritten on successful schema change.
