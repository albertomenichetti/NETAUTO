# M3 — OBJ-GET-01 Consolidated Decision

**Status:** CONSOLIDATED / WIP / NON-NORMATIVE

**Route:** `GET /api/v1/core/objects`

**Application:** `ObjectService.list_objects`

This note records the consolidated M3 discovery decision for OBJ-GET-01 until all reviewed Object routes are folded into the main GET/read census.

## Current read shape

```text
request/filter validation
-> cursor validation
-> ordinary UnitOfWork
-> one ObjectStore.list_objects() call
-> one SELECT over objects
-> limit + 1 pagination
-> next cursor from last returned Object id
```

The request rule `template_version requires template_id` is request validation and remains valid.

The cursor query identity is bound to:

```text
template_id
template_version
canonical_name
```

with one UUID key (`Object.id`) for keyset continuation.

## Persistence shape

`ObjectStore.list_objects()` already projects only the fields required by `ObjectSummary`:

```text
id
canonical_name
template_id
template_version
```

It conditionally applies the requested filters and the `after` keyset predicate, then orders by `objects.id` and applies `LIMIT`.

The persistence path is one SQL statement.

## Consolidated decision

```text
persisted-state semantic revalidation   NONE / KEEP NONE
coherent_read()                         NONE / DO NOT INTRODUCE
current persistence statements          1
target persistence statements           1
projection                              MINIMAL / COMPLETE
request validation                       PRESERVE
filter semantics                         PRESERVE
keyset pagination                        PRESERVE
M3 behavioral change                     NONE
```

An unknown `template_id` used as a collection filter naturally yields `200` with an empty collection; it is not a URI/path target and does not require a separate existence lookup.

OBJ-GET-01 already matches the M3 read principles and should remain structurally unchanged except for incidental refactoring required by shared implementation work.
