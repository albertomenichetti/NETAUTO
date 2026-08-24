# OBJ-GET-05 — Object lifecycle-events read decision

Status: CONSOLIDATED — M3 discovery WIP, non-normative until milestone freeze.

## Public route

`GET /api/v1/core/objects/{object_id}/lifecycle-events`

Application path: `ObjectService.list_events(..., involving_object_id=object_id, ...)`.

## Current shape

The object-scoped route already binds the cursor identity to `involving_object_id`, along with all other lifecycle filters. The keyset is `(occurred_at, id)` in descending order.

The current read uses `coherent_read()` because it performs two separate reads:

1. load the path-target Object solely to preserve `404` semantics;
2. load the matching lifecycle-event page.

`LifecycleStore.list_events()` itself is one statement, but every returned row is passed through `decode_lifecycle_event()`, which currently mixes carrier decoding with persisted semantic revalidation. The HTTP `_event()` adapter repeats some `before`/`after` presence checks.

## Consolidated decisions

### Preserve request and cursor behavior

Preserve:

- all public filters;
- `involving_object_id` in cursor filter identity;
- keyset `(occurred_at, id)`;
- descending order on both key fields;
- `limit + 1` pagination;
- existing path-target semantics: missing Object => `404`, existing Object with no matching events => `200 []`.

### Collapse target existence and event page into one statement

Target one persistence statement that includes path-target existence and the filtered lifecycle page, using either a target row/marker projection or an equivalent single-statement representation.

The persistence result must distinguish:

- missing Object;
- existing Object with no matching events;
- existing Object with event rows.

Once the read is single-statement, use an ordinary UoW and remove `coherent_read()` from this GET path.

### Preserve carrier decoding, remove semantic revalidation

Trust persisted lifecycle state. Reading historical JSONB still requires decoding an untyped carrier into Python/domain objects; that is not semantic revalidation.

Preserve only carrier-decoding responsibilities such as:

- `kind` conversion to `EventKind`;
- decoding required JSON object fields;
- UUID string -> `UUID` conversion where snapshots store UUIDs as strings;
- extracting primitive Python values needed to construct the historical projection;
- decoding a properties JSON object into `dict[str, JsonValue]`.

Remove read-side semantic certification such as:

- re-validating historical property-name identifier grammar;
- re-validating historical runtime list homogeneity/non-emptiness beyond what is required to decode `JsonValue`;
- re-validating snapshot canonical-name bounds or positive versions;
- checking `before.id` / `after.id` against the outer event Object id;
- checking `after.canonical_name` against the outer event name;
- re-certifying mutation transition semantics for `RENAME`, `DATA_CHANGE`, `SCHEMA_CHANGE`;
- re-certifying Relationship transition semantics such as unchanged/increased definition versions or changed properties;
- generic persisted-state "incoherent event" failures whose only purpose is to prove that the mutation wrote a semantically valid event.

Database constraints already carry structural responsibilities including allowed event kinds, family-specific NULL/NOT NULL shape, before/after state presence, and JSON object carrier shape. Mutation paths remain responsible for semantic correctness of historical transitions.

### HTTP adapter

`_event()` should select the DTO from the already-decoded event kind/type without re-checking persisted `before`/`after` presence.

Where typing requires narrowing, use typing casts or an equivalent programmer-facing exhaustiveness mechanism rather than runtime persisted-state certification. HTTP DTO projection remains required.

## Target summary

- semantic persisted-state revalidation: remove;
- historical carrier decoding: preserve, but make it decoding-only;
- HTTP DTO projection: preserve, without duplicated state certification;
- current DB statements: 2 at application level;
- target DB statements: 1;
- current `coherent_read()`: justified by fragmented read;
- target `coherent_read()`: remove;
- public request/filter/cursor/pagination/404 semantics: preserve.
