# M4 WIP — Object components physical schema discovery

Status: WIP / NON-NORMATIVE

## Scope

This note records the current M4 discovery candidate for the runtime ownership table `object_components`. It is intentionally limited to physical shape, semantic identity materialization, read/write consequences, migration direction, and one still-open FK question. Lock/concurrency redesign remains deferred to the global phase.

## Current problem

Current persistence stores:

```text
object_components
    child_object_id      PK
    parent_object_id
    slot_name
```

The business invariant `child has at most one owner` is well represented by `child_object_id` as the primary key, and parent/child object lifetime is protected by RESTRICT foreign keys.

The under-materialized part is the slot identity. ObjectTemplate architecture defines ownership-slot semantic continuity through:

```text
SlotSemanticKey = (declaring_template_id, slot_name)
```

but the runtime edge currently persists only `slot_name`.

Consequences of the missing declaring lineage include:

- component-list reads recursively rebuild the parent exact ObjectTemplate inheritance chain only to discover `slot_declaring_template_id`;
- owner reads perform the same model-plane reconstruction;
- DETACH reloads the parent effective schema to recover the same semantic identity for lifecycle metadata;
- SCHEMA_CHANGE must first map `slot_name` through the source effective schema to rediscover the semantic key before checking the target schema;
- current facts therefore force repeated reinterpretation of model-plane state after admission.

## Candidate runtime edge

Preferred current direction:

```text
object_components
    child_object_id              PK
    parent_object_id             NOT NULL
    slot_declaring_template_id   NOT NULL
    slot_name                    NOT NULL
```

Retain:

```text
PK child_object_id
FK child_object_id -> objects.id RESTRICT
FK parent_object_id -> objects.id RESTRICT
CHECK parent_object_id <> child_object_id
slot_name identifier validation
```

The new `slot_declaring_template_id` persists the semantic identity resolved during ATTACH.

## Explicitly not persisted

Do not persist:

```text
slot_declaring_template_version
target_template_id
parent template_id/template_version copies
slot position
```

Rationale:

- `slot_declaring_template_version` is not part of slot semantic identity and would turn normal parent Object SCHEMA_CHANGE into ownership-edge rewrites or stale exact-schema pins;
- `target_template_id` is exact-schema contract state that may evolve while the ownership fact remains the same;
- parent exact schema identity already belongs to the parent Object;
- presentation position is schema metadata, not factual ownership identity.

The current ownership fact should survive schema evolution without DML whenever the same semantic slot remains valid.

## ATTACH consequence

ATTACH becomes the resolution/materialization boundary:

```text
current parent Object
    -> compiled exact effective ObjectTemplate schema
    -> resolve requested slot_name
    -> obtain (declaring_template_id, slot_name, target_template_id)

current child Object
    -> stable-lineage compatibility check against target_template_id

current ownership/cycle checks

INSERT object_components(
    child_object_id,
    parent_object_id,
    slot_declaring_template_id,
    slot_name
)
```

Idempotent same-edge comparison should use the full semantic key, not name equality alone.

## DETACH consequence

Once the edge stores the semantic identity, DETACH does not need the parent ObjectTemplate effective schema. It identifies and removes the current fact directly and uses the persisted `(slot_declaring_template_id, slot_name)` for lifecycle metadata.

Removing an ownership edge cannot introduce a new ownership/schema violation, so the AS-IS pre-delete recertification that the slot is still materializable from the parent schema is a candidate for removal.

## SCHEMA_CHANGE consequence

For every outgoing edge, the semantic key is already:

```text
(edge.slot_declaring_template_id, edge.slot_name)
```

SCHEMA_CHANGE therefore checks this key directly against the target effective-component materialization.

Child compatibility must still be checked because forward numeric version order does not guarantee widening of the slot target contract when versions can be published out of numeric order.

The preferred data-access direction is one set-based blocker query joining:

```text
object_components
objects child
object_template_effective_components(target exact version)
object_template_ancestry
```

rather than the AS-IS per-edge source-slot lookup + child GET + lineage check loop.

A successful Object SCHEMA_CHANGE does not update `object_components`.

## Read consequence

`components` and `owner` become pure current-fact projections.

### Components

A page requires only:

```text
parent existence
child_object_id
slot_declaring_template_id
slot_name
```

No exact ObjectTemplate recursive traversal is required.

### Owner

A single LEFT JOIN from the child Object to `object_components` can distinguish:

```text
child absent -> 404
child present with no edge -> null owner
child present with edge -> OwnerProjection
```

No ObjectTemplate cache or model-plane reconstruction is needed.

## Index direction

Keep the existing conceptual parent-page access path:

```text
(parent_object_id, slot_name, child_object_id)
```

because it supports parent component listing, optional slot-name filtering, and child-id keyset pagination.

Do not add `slot_declaring_template_id` to the key merely because it is now persisted. An `INCLUDE (slot_declaring_template_id)` optimization may be evaluated later with PostgreSQL EXPLAIN evidence but is not an architectural requirement.

## Direct FK to declaring lineage — OPEN

A direct constraint such as:

```text
FK slot_declaring_template_id -> object_templates.id RESTRICT
```

remains open rather than decided.

Reasoning against adding it immediately:

- a valid declaring lineage must be the parent lineage itself or a stable ancestor;
- if it is the parent lineage, current parent Objects already protect that lineage lifetime;
- if it is an ancestor, the stable child-lineage graph already blocks deletion of the ancestor;
- the FK therefore appears to duplicate lifetime authority rather than introduce a genuinely new semantic rule;
- it could also introduce an additional low-level delete-blocker constraint that must be mapped into diagnostics despite an already-existing blocker necessarily being present.

Reasoning in favor remains the usual local referential-integrity value of preventing an orphan UUID. This tradeoff must be resolved explicitly in later persistence/concurrency design.

No assumption is made yet.

## Migration direction

Backfill the new column from current admitted state.

Preferred sequence after immutable effective-component materialization exists:

```text
old edge
    (parent_object_id, child_object_id, slot_name)

JOIN parent Object
    -> (template_id, template_version)

JOIN object_template_effective_components
    ON parent exact template/version
   AND effective.name = edge.slot_name

SET edge.slot_declaring_template_id = effective.declaring_template_id
```

Every old edge must resolve to exactly one effective component declaration. Zero or multiple matches indicate pre-existing invariant corruption and the migration should fail rather than invent a value.

## Candidate conclusion

The ownership table should remain relational and separate from `objects`; the issue is not separation but under-materialization.

Current preferred shape:

```text
object_components
    child_object_id              PK + FK Object
    parent_object_id             FK Object
    slot_declaring_template_id   NOT NULL
    slot_name                    NOT NULL
```

with:

- no slot declaring version;
- no target-template copy;
- no parent exact-schema copy;
- no mandatory new index beyond the existing parent/slot/child path;
- direct FK on `slot_declaring_template_id` still OPEN.

This follows the M4 principle that model interpretation should happen on the admission/mutation path and stable resolved runtime identity should then be persisted for direct consumption by hot reads and subsequent mutations.
