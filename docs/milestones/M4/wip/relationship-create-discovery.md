# M4 — Relationship.CREATE discovery

**Status:** WIP / NON-NORMATIVE

## Scope

This note records the first-phase M4 audit of the first half of factual `Relationship.CREATE`, up to deterministic runtime-closure derivation and relationship-property canonicalization. Concurrency/lock redesign remains deferred to the global second phase.

## AS-IS shape

Before fact-conflict checks and DML, current `Relationship.CREATE`:

1. resolves `resolution_id` to the complete RelationshipDefinition aggregate;
2. resolves explicit/default RelationshipDefinitionVersion and loads its complete property declarations;
3. performs lock-plan stabilization and repeats Definition/version reads;
4. loads endpoint Objects -> stable ObjectTemplate lineage ids;
5. loads the complete ObjectTemplate parent graph;
6. derives the deterministic runtime closure in Python by ancestry walking;
7. calls `_relationship_specs()`, which loads the exact RelationshipDefinitionVersion again, then loads exact DataTypeVersion dependencies, then builds runtime property specs;
8. canonicalizes the supplied relationship property map.

Duplicated reads that exist only because of current lock-plan stabilization are not classified here; they remain deferred to the concurrency phase.

## Finding 1 — redundant schema reload

After stabilization, the application already has the complete exact RelationshipDefinitionVersion `target`, including all property declarations. `_relationship_specs()` currently reloads that same exact version before resolving DataType semantics.

This third exact-version load is redundant independently of any future cache design.

Minimum improvement without cache:

```text
stabilized target RDV
+
DataType semantic payloads
-> resolved runtime Relationship schema
```

## Finding 2 — immutable RDV runtime cache is a direct hot-path fit

`PUBLISHED` and `DEPRECATED` RelationshipDefinitionVersion property schemas are immutable. Unlike ObjectTemplate, there is no distinction between local declarations and an effective inherited schema: the exact RDV declaration set is already the complete relationship-property schema.

Candidate cache:

```text
ImmutableRelationshipDefinitionVersionCache[(definition_id, version)]
    ordered properties:
        name
        position
        datatype_id
        datatype_version
        value_mode
    runtime property specs / validator linkage / compiled semantic structures
```

This cache must exclude current mutable state such as `status` and Definition `default_version`.

On the hot Relationship data-plane, this cache should eliminate repeated reads of:

- `relationship_definition_properties`;
- immutable DataType semantic payloads already compiled/resolved;
- repeated `RuntimePropertySpec` construction.

Current admission remains PostgreSQL-owned. For a new factual binding the selected RDV must still be currently `PUBLISHED`, and direct exact DataType dependencies must still satisfy the required current admission state. Cache presence never proves current admissibility or current existence.

## Finding 3 — full ObjectTemplate graph load must leave the data-plane

Current `Relationship.CREATE` loads every ObjectTemplate `(id, parent_template_id)` and performs ancestry walking in Python to decide endpoint compatibility and symmetric closure membership.

The actual predicates are bounded and local:

```text
resolution.from_template_id ancestor-of from_object.template_id
resolution.to_template_id   ancestor-of to_object.template_id
```

plus the reciprocal/both-assignment checks required by the at-most-two Resolution definition shape.

The M4 candidate stable closure:

```text
object_template_ancestry
    descendant_template_id
    ancestor_template_id
    depth
```

with self rows `(T,T,0)` directly answers these predicates.

Because descendant -> ancestor membership is stable for the lifetime of a lineage, a worker-local cache is also natural:

```text
StableObjectTemplateAncestryCache[template_id]
    -> ancestor_template_ids (including self)
```

Together with the stable RelationshipDefinition topology cache:

```text
StableRelationshipDefinitionTopologyCache[definition_id]
    id
    symmetric
    resolutions:
        resolution_id
        from_template_id
        to_template_id
```

the deterministic runtime closure can be derived in memory without loading the complete ObjectTemplate graph and without mutable Resolution names.

## Candidate warm-path separation

```text
PostgreSQL current admission
    resolution / Definition current existence
    explicit or current default selection
    selected RDV currently PUBLISHED
    direct DTV admission as required
    endpoint Object existence + template_id

worker-local stable / immutable caches
    RelationshipDefinition topology
    ObjectTemplate ancestry
    compiled immutable RDV schema
        -> derive deterministic runtime closure
        -> canonicalize relationship properties
```

The exact current-admission projection and lock/concurrency rendezvous remain open until the global second phase.

## Explicit non-decisions

- No lock redesign in this note.
- No cache presence may prove current resource existence or admission.
- No full resolved applicability materialization per RelationshipResolution is proposed; stable ObjectTemplate ancestry remains the single owner of lineage closure.
- Fact-conflict detection, runtime closure persistence, lifecycle event projection, and CREATE collision classification are audited separately in the next step.
