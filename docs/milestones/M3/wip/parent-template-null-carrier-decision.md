# M3 — `parent_template_id = null` public carrier decision

**Status:** CONSOLIDATED DISCOVERY INPUT / NON-NORMATIVE

**Role:** Area C discovery decision. This file records the reviewed public carrier semantics and boundary realization for ObjectTemplate root-only filtering. It does not authorize implementation and does not replace the future M3 contract, architecture set or implementation steps.

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

`parent_filter_set` remains an internal application/cursor representation detail and is **not** exposed as a second public query parameter.

No `root=true`, `has_parent=false`, empty-string sentinel, uppercase magic value or other alternate encoding is introduced.

## 3. HTTP boundary

The HTTP adapter must continue to distinguish omission from explicit presence through the raw query-parameter set:

```text
"parent_template_id" not present
    -> parent_filter_set = false

"parent_template_id" present
    -> parent_filter_set = true
```

The typed query carrier must accept exactly:

```text
literal "null"
    -> Python None

canonical valid UUID lexical value
    -> UUID
```

Malformed values other than the exact lowercase `null` sentinel remain invalid request carriers and map through the existing request-validation boundary to `invalid_request / 400`.

Target HTTP behavior:

```text
GET /api/v1/core/object-templates
    -> parent_template_id = None
    -> parent_filter_set = false
    -> no parent predicate

GET /api/v1/core/object-templates?parent_template_id=<valid UUID>
    -> parent_template_id = UUID
    -> parent_filter_set = true
    -> exact parent predicate

GET /api/v1/core/object-templates?parent_template_id=null
    -> parent_template_id = None
    -> parent_filter_set = true
    -> IS NULL parent predicate

parent_template_id=
parent_template_id=NULL
parent_template_id=root
parent_template_id=<malformed UUID>
    -> invalid_request / 400
```

A dedicated strict query carrier / `BeforeValidator`-style adapter is the expected realization pattern. The exact helper name remains an implementation detail.

## 4. CLI boundary

The CLI canonical grammar already defines `parameter=null` as explicit null for nullable registry parameters. Area C reuses that grammar rather than adding a special command syntax.

The ObjectTemplate list registry parameter remains selector-capable for non-null values and becomes nullable:

```text
parent_template_id
    location = query
    selector = ObjectTemplate
    nullable = true
```

Target CLI behavior:

```text
object-template list
    -> omit parent_template_id
    -> no parent query pair

object-template list parent_template_id=<UUID|namespace.name>
    -> normal ObjectTemplate selector resolution
    -> emit exact UUID query pair

object-template list parent_template_id=null
    -> parser materializes explicit None
    -> no ObjectTemplate selector lookup
    -> emit query pair parent_template_id=null
```

Two common CLI boundaries must therefore understand nullable selector query carriers:

### Selector resolution

A selector-capable parameter with a non-null value retains existing selector resolution.

A selector-capable parameter whose value is explicit `None` is valid only when that parameter is nullable; it is a terminal carrier value and must not be sent through selector lookup.

This must be common metadata-driven behavior, not a branch hard-coded to `parent_template_id`.

### Request planning

Explicit `None` must not become a globally accepted path/query scalar.

The location-aware rule is:

```text
nullable QUERY parameter + explicit None
    -> lexical query value "null"

nullable BODY parameter + explicit None
    -> JSON null under existing body DTO rules

PATH parameter + None
    -> invalid / impossible registry-plan state
```

The existing scalar wire helper must therefore not simply be broadened globally to `_wire_string(None) -> "null"`.

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

No new cursor format or version is required for this semantic distinction. The existing route/filter equality check already makes cursors from the three states mutually incompatible where their query identity differs.

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

already maps `None` to SQL `IS NULL` and correctly implements root-only filtering.

Area C therefore requires no domain-model, persistence-query or cursor-codec redesign.

## 7. Public-contract delta

The authoritative AS-IS API documentation lists `parent_template_id` as an ObjectTemplate lineage filter but does not define a lexical root-only representation.

M3 must freeze this wire meaning explicitly:

```text
parent_template_id query carrier
    omitted -> no parent filter
    UUID    -> direct children of that parent
    null    -> root ObjectTemplates only
```

The official CLI must expose the same tri-state through its existing `parameter=value` grammar.

This is a public carrier-contract correction, not a persistence or domain-semantics change.

## 8. Candidate acceptance evidence

Later contract/steps should include at least:

```text
HTTP omission -> unfiltered parent dimension
HTTP valid UUID -> direct children only
HTTP literal null -> roots only
HTTP empty string -> invalid_request / 400
HTTP uppercase NULL -> invalid_request / 400
HTTP other non-UUID sentinel -> invalid_request / 400
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

Regression evidence should also prove that no selector-discovery GET is performed for CLI `parent_template_id=null`.

## 9. Consolidated Area C direction

```text
KEEP
    one public filter name: parent_template_id
    existing application tri-state
    existing persistence tri-state
    existing cursor filter identity and parent_filter_set distinction
    exact UUID parent filtering
    strict duplicate/unknown query handling

ADD / CHANGE
    canonical public root-only carrier: parent_template_id=null
    HTTP nullable UUID query parsing with exact lowercase null sentinel
    CLI registry marks the selector-capable query parameter nullable
    common selector resolver skips explicit null for nullable selector parameters
    request planner emits lexical null only for nullable query parameters
    public API/CLI documentation and regression evidence

DO NOT
    expose parent_filter_set publicly
    use empty string as root sentinel
    add a second root=true / has_parent=false filter
    add magic non-UUID strings such as ROOT
    collapse explicit null into omission
    globally allow None as an arbitrary path/query scalar
    alter persistence/domain semantics to solve a carrier problem
```

This decision closes both the public lexical representation and the HTTP/CLI boundary realization questions for Area C.