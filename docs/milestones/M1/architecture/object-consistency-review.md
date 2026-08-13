# M1 — Object Consistency Review

**Status:** REVIEW COMPLETE — input for Object architecture DRAFT

## 1. Result

The ratified OBJ-01..OBJ-10 semantics are internally coherent with the current M1 `DataType` and `ObjectTemplate` architecture.

No blocking semantic contradiction was found.

## 2. Required ObjectTemplate amendments

Two clarifications discovered during Object migration design belong normatively to the model-plane and are therefore reflected in replacement copies of:

- `objecttemplate-properties.md`
- `objecttemplate-components.md`

### PropertySemanticKey

Historical/migration continuity is:

```text
(declaring_template_id, property_name)
```

not effective name alone.

A remove/re-add with the same name from the same declaring lineage preserves historical identity/evolution constraints.

### SlotSemanticKey

Historical/runtime slot continuity is:

```text
(declaring_template_id, slot_name)
```

not effective slot name alone.

A remove/re-add with the same name from the same declaring lineage preserves historical identity/evolution constraints.

## 3. Historical contracts superseded by M1 Object architecture

The new architecture intentionally supersedes older baseline semantics where they differ, including:

- Object create implicit resolution by `highest/latest PUBLISHED`: replaced by `ObjectTemplate.default_version`;
- normal Object `SCHEMA_CHANGE` changing `template_id`: forbidden; normal M1 schema change is same-lineage exact-version repin;
- subtree delete: forbidden;
- implicit detach/cascade cleanup during Object delete: forbidden.

The stable `Object.template_id` decision aligns Object with lineage-based Relationship/component compatibility.

## 4. Current persistence gaps to address during implementation design

These are implementation/schema deltas, not new domain decisions.

### Ownership FK cascade

Current persistence uses `ON DELETE CASCADE` from `object_components` to both parent and child Object rows.

M1 Object DELETE semantics require no implicit detach, therefore ownership references must have `RESTRICT`-equivalent semantics.

### Lifecycle changelog shape

Current `object_changes` lacks the structural event fields required by M1:

```text
destination_object_id
destination_canonical_name
slot_declaring_template_id
slot_name
```

It must also support `ATTACH_TO` and `DETACH_FROM`.

Lifecycle references are historical identifiers and must not become live FK blockers to Object/ObjectTemplate deletion.

### Object current-state shape

Implementation must be aligned to the ratified canonical Object state, including `canonical_name`, exact OTV pin and canonical property persistence.

## 5. High-risk concurrency work still open

The domain semantics are frozen enough to proceed, but the following mechanisms remain intentionally unresolved until the concurrency architecture:

- parent schema vs outgoing ATTACH/DETACH serialization;
- single-owner child authority;
- ownership cycle prevention with global graph write gate;
- DATA_CHANGE vs SCHEMA_CHANGE stale-state prevention;
- DELETE vs concurrent new references;
- target OTV admission stabilization.

These require real PostgreSQL integration/concurrency tests.
