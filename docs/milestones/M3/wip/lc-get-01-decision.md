# LC-GET-01 — `GET /lifecycle-events`

Status: **CONSOLIDATED**

## Current path

The global lifecycle collection is exposed through `GET /lifecycle-events` and calls `ObjectService.list_events(...)` with `involving_object_id=None`.

The cursor identity binds all public filters:

- `kind`
- `object_id`
- `destination_object_id`
- `relationship_id`
- `relationship_definition_id`
- `relationship_name`
- canonical `occurred_from`
- canonical `occurred_to`
- `involving_object_id` (always `None` for this route)

The keyset cursor uses `(occurred_at, id)` and the persistence query orders by `occurred_at DESC, id DESC`.

Because the global route supplies `involving_object_id=None`, the object-existence read used by the object-scoped lifecycle route is skipped. `LifecycleStore.list_events(...)` is therefore already the only database read for this route.

## Consolidated decision

### Preserve

- all public filters;
- complete cursor/filter binding;
- route identity `lifecycle_events`;
- keyset `(occurred_at, id)`;
- descending ordering;
- `limit + 1` pagination;
- the existing single persistence SELECT;
- historical carrier decoding required to materialize typed lifecycle output;
- application mapping of materially undecodable persisted carriers to internal failure.

### Remove

The GET path must not re-certify persisted lifecycle semantics. Remove from the shared lifecycle decoder / HTTP projection path:

- before/after transition semantic certification;
- intrinsic `RENAME`, `DATA_CHANGE`, and `SCHEMA_CHANGE` invariants;
- Relationship lifecycle transition invariants;
- snapshot-vs-outer-row identity/name coherence checks;
- duplicated lifecycle family/state-shape checks already owned by database constraints;
- HTTP before/after presence checks that merely re-certify persisted event shape.

Keep only mechanical historical carrier decoding needed to construct typed Python/domain/DTO values, including necessary UUID and primitive conversions.

### UoW

`coherent_read()` is not justified for this global route because the target projection is already one statement. Use an ordinary read UoW.

## Statement target

- Current database statements: **1**
- Target database statements: **1** (existing query retained)

No SQL recomposition is required for LC-GET-01.

## Relationship to OBJ-GET-05

The lifecycle decoder cleanup is shared with OBJ-GET-05. OBJ-GET-05 additionally requires composing path-target existence and the event page into one statement; LC-GET-01 does not, because it has no URI/path target identity.
