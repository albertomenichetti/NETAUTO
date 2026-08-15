# M1 — Object Consistency Review

**Status:** REVIEW COMPLETE — semantic findings integrated; persistence/concurrency/API/test closure is aligned with the current M1 architecture baseline.

## 1. Result

The ratified Object semantics are internally coherent with the current M1 `DataType`, `ObjectTemplate`, persistence, concurrency and public API architecture.

No blocking semantic contradiction was found.

The PostgreSQL realization and real-PG test contract have subsequently been completed through REALIZE-01..15 and PGTEST-01..04. The public Object/API contract is also closed through API-03.11. This review therefore carries no unresolved Object architecture item.

## 2. Required ObjectTemplate amendments

Two clarifications discovered during Object migration design belong normatively to the model-plane and are reflected in:

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

## 4. Persistence implementation obligations — architecture resolved

The following were gaps in the pre-M1 implementation, **not open architecture choices**. Their target state is now normative in `persistence-model.md` and the concurrency realization.

### Ownership FK semantics

Required M1 target:

```text
object_components.parent_object_id -> objects.id RESTRICT
object_components.child_object_id  -> objects.id RESTRICT
```

No implicit ownership cleanup on Object delete.

### Lifecycle changelog shape

The M1 target is the single typed `object_lifecycle_events` table with structural fields including:

```text
destination_object_id
destination_canonical_name
slot_declaring_template_id
slot_name
relationship_id
relationship_definition_id
relationship_name
before_state
after_state
```

Historical identifiers are not live FK blockers. Event identity is PostgreSQL-generated UUID and `occurred_at` is `transaction_timestamp()`.

### Object current-state shape

Implementation must match the ratified state:

```text
id UUID
canonical_name TEXT, semantic bound 1..255
(template_id, template_version) exact OTV FK
properties canonical JSONB object
```

No `Object.state_revision` M1.

## 5. High-risk concurrency work — resolution map

The formerly open concurrency mechanisms are now closed:

```text
parent schema vs ATTACH/DETACH
    -> REALIZE-09/10/15
    -> parent Object FOR NO KEY UPDATE owner

single-owner child
    -> REALIZE-10
    -> PK(child_object_id)

ownership cycle prevention
    -> REALIZE-11
    -> OWNERSHIP_GRAPH_WRITE_GATE via pg_advisory_xact_lock
       + post-gate fresh snapshot

DATA_CHANGE vs SCHEMA_CHANGE
    -> REALIZE-09
    -> same Object FOR NO KEY UPDATE owner + post-lock re-derivation

DELETE vs concurrent references
    -> REALIZE-07
    -> immediate FK RESTRICT final authority

exact target OTV admission
    -> REALIZE-05
    -> target exact FOR SHARE + PUBLISHED recheck
```

The corresponding normative real-PostgreSQL scenario census, deterministic harness contract and reusable execution recipes are all closed in `concurrency-postgresql-test-matrix.md` through PGTEST-01..04.

Any implementation that reopens these choices is an architecture change, not an implementation detail.

## 6. Final review state

No Object-specific architecture question remains open before the global M1 architecture consistency/freeze decision.
