# M3 — `parent_template_id = null` public carrier decision

**Status:** CONSOLIDATED DISCOVERY INPUT / NON-NORMATIVE

**Role:** Area C discovery decision. This file records the reviewed public carrier semantics for ObjectTemplate root-only filtering. It does not authorize implementation and does not replace the future M3 contract, architecture set or implementation steps.

## 1. Problem statement

The ObjectTemplate lineage list path already models a three-state parent filter internally:

```text
parent filter absent
    -> no parent predicate

parent filter present with UUID
    -> parent_template_id = UUID

parent filter present with None
    -> parent_template_id IS NULL
    -> root ObjectTemplates only
```

Application cursor identity also distinguishes omission from explicit root-only filtering through `parent_filter_set`.

The current public HTTP and CLI carriers expose only two reachable states: omission and UUID. There is no canonical public lexical representation for the third state.

## 2. Consolidated public carrier

The canonical public representation for root-only filtering is:

```text
parent_template_id=null
```

The complete public tri-state is therefore:

```text
parameter omitted
    -> no parent filter

parent_template_id=<UUID>
    -> only direct children of the selected parent ObjectTemplate

parent_template_id=null
    -> only root ObjectTemplates
```

No second `root=true` style query parameter, empty-string sentinel, uppercase magic value or other alternate encoding is introduced.

## 3. HTTP semantics

Target HTTP behavior:

```text
GET /api/v1/core/object-templates
    -> parent_filter_set = false
    -> parent_template_id = None
    -> no parent predicate

GET /api/v1/core/object-templates?parent_template_id=<valid UUID>
    -> parent_filter_set = true
    -> parent_template_id = UUID
    -> exact parent predicate

GET /api/v1/core/object-templates?parent_template_id=null
    -> parent_filter_set = true
    -> parent_template_id = None
    -> IS NULL parent predicate
```

Malformed values other than the exact accepted `null` sentinel remain invalid request carriers and map to the existing canonical `invalid_request / 400` response.

The HTTP adapter must preserve the distinction between omission and explicit `null` using query-parameter presence, because both materialize as `None` at the typed Python value level.

## 4. CLI semantics

The CLI canonical grammar already defines `parameter=null` as explicit null for nullable registry parameters. Area C reuses that grammar rather than adding a special command syntax.

Target CLI behavior:

```text
object-template list
    -> omit parent_template_id
    -> no parent filter

object-template list parent_template_id=<UUID|namespace.name>
    -> normal ObjectTemplate selector resolution
    -> exact UUID query carrier

object-template list parent_template_id=null
    -> explicit None
    -> do not invoke ObjectTemplate selector resolution for this value
    -> emit the HTTP query pair parent_template_id=null
```

The registry parameter therefore becomes nullable while remaining selector-capable for non-null values.

A nullable selector parameter with an explicit `None` value must be treated as a terminal carrier value rather than as a selector target. This should be expressed by common selector-resolution semantics, not by a one-off branch specific to `parent_template_id`.

## 5. Cursor identity

The existing application cursor identity is retained:

```text
no parent filter
    parent_template_id = null
    parent_filter_set = false

root-only filter
    parent_template_id = null
    parent_filter_set = true

exact parent filter
    parent_template_id = <UUID>
    parent_filter_set = true
```

This means no new cursor format or version is required for the semantic distinction itself. A cursor issued for one state must remain incompatible with the other states under the existing route/filter equality check.

## 6. Application and persistence boundary

No semantic redesign is required below the HTTP/CLI carrier boundary.

The existing application signature:

```text
parent_template_id: UUID | None
parent_filter_set: bool
```

already represents the intended tri-state.

The existing persistence condition:

```text
if parent_filter_set:
    parent_template_id == supplied value
```

already maps `None` to SQL `IS NULL` and therefore correctly implements root-only filtering.

Area C must preserve that existing internal model.

## 7. Public-contract delta

Current authoritative AS-IS documentation lists `parent_template_id` as an ObjectTemplate lineage filter but does not define a lexical root-only representation.

M3 must make the new wire meaning explicit:

```text
parent_template_id query carrier
    UUID  -> direct children of that parent
    null  -> root ObjectTemplates only
    omitted -> no parent filter
```

This is a public carrier-contract clarification/correction, not a database or domain-model change.

## 8. Candidate acceptance evidence

Later contract/steps should include evidence for at least:

```text
HTTP omission -> unfiltered parent dimension
HTTP valid UUID -> direct children only
HTTP literal null -> roots only
HTTP empty string -> invalid_request / 400
HTTP other non-UUID non-null sentinel -> invalid_request / 400
HTTP duplicate parent_template_id -> invalid_request / 400

CLI omission -> no parent query pair
CLI UUID selector -> exact UUID query pair
CLI human ObjectTemplate selector -> resolved UUID query pair
CLI explicit null -> literal null query pair with no selector lookup
CLI invalid selector/value -> existing structured CLI error

cursor from omitted state rejected under root-only state
cursor from root-only state rejected under omitted state
cursor from exact-parent A rejected under exact-parent B
root-only cursor continues root-only pagination successfully
```

## 9. Consolidated Area C direction

```text
KEEP
    existing application tri-state
    existing persistence tri-state
    existing cursor filter identity and parent_filter_set distinction
    exact UUID parent filtering
    strict duplicate/unknown query handling

ADD / CHANGE
    canonical public root-only carrier: parent_template_id=null
    HTTP nullable UUID query parsing with exact null sentinel
    CLI nullable selector-carrier support
    common selector resolver skips explicit null values for nullable selector parameters
    public API/CLI documentation and regression evidence

DO NOT
    use empty string as root sentinel
    add a second root=true filter
    add magic non-UUID strings such as ROOT
    collapse explicit null into omission
    alter persistence/domain semantics to solve a carrier problem
```

This decision closes the public lexical representation question for Area C. The remaining Area C discovery work is to consolidate the exact HTTP and CLI boundary realization and acceptance implications before marking the workstream closed.
