# M3 — Parent Template Null Carrier Closure

**Status:** CONSOLIDATED DISCOVERY INPUT / NON-NORMATIVE

**Role:** Area C closure record and downstream planning input. This document does not authorize implementation and does not replace the future M3 contract, architecture set or implementation steps.

## 1. Closure statement

Area C — public `parent_template_id = null` carrier is complete at discovery level.

The review established that the application, cursor identity and persistence layers already model the intended parent-filter tri-state correctly. The defect is confined to the public carrier boundary: current HTTP and CLI surfaces cannot express the existing root-only state.

The canonical public correction is now closed:

```text
parent_template_id omitted
    -> no parent filter

parent_template_id=<UUID>
    -> direct children of that parent

parent_template_id=null
    -> root ObjectTemplates only
```

No second public filter is introduced.

## 2. Current internal state is already correct

Application state:

```text
parent_template_id: UUID | None
parent_filter_set: bool
```

Persistence state:

```text
parent_filter_set = false
    -> no parent predicate

parent_filter_set = true + UUID
    -> parent_template_id = UUID

parent_filter_set = true + None
    -> parent_template_id IS NULL
```

Cursor query identity already records both `parent_template_id` and `parent_filter_set`, so omission and explicit root-only filtering are distinct identities without a cursor-version change.

## 3. Current public gap

The current HTTP adapter types `parent_template_id` as `UUID | None` while separately observing whether the query parameter is present.

As a result:

```text
omitted
    -> reachable no-filter state

valid UUID
    -> reachable exact-parent state

literal null / empty / non-UUID sentinel
    -> request validation failure
```

The current CLI registry also marks the parameter as selector-capable but not nullable, so `parent_template_id=null` is rejected before a request can be built.

Therefore the third internal state is unreachable from both supported public clients.

## 4. Consolidated public carrier

The only public filter name remains:

```text
parent_template_id
```

The exact lowercase lexical token `null` is the root-only sentinel.

This choice preserves a single coherent tri-state and avoids conflicting or redundant combinations such as `root=true + parent_template_id=<UUID>`.

`parent_filter_set` remains internal only.

## 5. HTTP target boundary

Expected realization:

```text
query omitted
    -> typed value None
    -> presence false

query value "null"
    -> typed value None
    -> presence true

query value valid UUID
    -> typed UUID
    -> presence true

all other lexical values
    -> invalid_request / 400
```

The adapter continues to derive `parent_filter_set` from raw query presence.

A strict nullable-UUID query carrier / `BeforeValidator`-style parser is the expected pattern; the exact helper name is not part of discovery authority.

## 6. CLI target boundary

The registry marks `parent_template_id` nullable while retaining ObjectTemplate selector semantics for non-null values.

Common CLI behavior becomes:

```text
nullable selector parameter + non-null value
    -> normal selector resolution

nullable selector parameter + explicit null
    -> terminal None carrier
    -> no selector lookup
```

Request planning is location-aware:

```text
nullable query + None
    -> emit lexical "null"

nullable body + None
    -> existing JSON null behavior

path + None
    -> invalid/impossible plan
```

This must be metadata-driven common behavior rather than a command-specific special case.

## 7. Public and cursor semantics to preserve

```text
omitted parent filter
    -> all parent dimensions eligible

UUID parent filter
    -> direct children only

null parent filter
    -> roots only
```

Cursor continuation remains bound to the exact semantic filter state:

```text
omitted cursor != root-only cursor
root-only cursor != exact-parent cursor
exact-parent A cursor != exact-parent B cursor
```

`limit` remains outside semantic cursor identity as in the existing pagination contract.

## 8. Downstream contract / architecture inputs

The future M3 contract should freeze the three public meanings of `parent_template_id` and the strict invalid lexical cases.

The future HTTP architecture should own the exact nullable UUID query carrier and preserve raw presence as the omission-vs-null discriminator.

The future CLI architecture should own nullable selector-carrier behavior and location-aware null query encoding.

The application/persistence architecture should record that no semantic redesign is required below the public boundary.

## 9. Candidate acceptance evidence

At minimum:

```text
HTTP omitted / UUID / null cover all three states
empty / uppercase NULL / malformed UUID remain 400
repeated parent_template_id remains 400

CLI omitted sends no query pair
CLI UUID/human selector resolves to UUID
CLI null performs no selector GET and sends parent_template_id=null

root-only page contains only lineages with parent_template_id = null
root-only continuation preserves root-only membership
cross-state cursors fail with invalid_cursor
```

## 10. Scope impact

Area C requires no schema, migration, dependency or lockfile change.

Expected later implementation touchpoints are limited to:

```text
HTTP ObjectTemplate query carrier
CLI registry/parser selector metadata handling
CLI selector resolver
CLI request planner
API/CLI regression tests
cursor-state regression evidence
public documentation
```

Application tri-state, persistence filtering and cursor codec semantics remain intact.

No further Area C discovery is required unless contract/architecture consistency review exposes a direct conflict.