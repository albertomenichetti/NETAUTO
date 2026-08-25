# M3 — Official CLI Architecture

**Status:** DESIGN IN PROGRESS — ADP-06 CLOSED; ADP-07 OPEN

**Authority:** M3 TO-BE ARCHITECTURE — OFFICIAL CLI OWNER

## Purpose and authority boundary

This document owns the M3 TO-BE CLI deltas for:

```text
ADP-06 — nullable selector/query carrier for ObjectTemplate root filtering
ADP-07 — post-create Location materialization grammar
```

It derives from the frozen M3 contract and changes only the explicit M3 CLI deltas. The delivered official CLI remains an HTTP-only client driven by one static registry. Existing command grammar, selector kinds, transport behavior, output modes, error catalogue and 63-operation registry remain owned by the delivered AS-IS except where this document explicitly changes them.

Implementation remains unauthorized while the M3 architecture set is not frozen.

## Frozen contract inputs

This owner realizes CLI-side portions of:

```text
M3-OUT-01 — Truthful CLI create success
M3-OUT-02 — Exact CLI protocol failure preservation
M3-OUT-07 — ObjectTemplate root-only public filter
M3-OUT-08 — Regression and traceability closure

M3-AC-01 — Eight-operation create success coverage
M3-AC-02 — Exact Location protocol failures
M3-AC-03 — Interactive/non-interactive create truthfulness
M3-AC-16 — CLI ObjectTemplate parent-filter tri-state
M3-AC-17 — CLI explicit-null no-selector-lookup behavior
M3-AC-18 — Complete outcome traceability
```

The HTTP lexical carrier for `parent_template_id=null` is already frozen by `api.md` / ADP-05. This document must produce exactly that public carrier from the official CLI.

# ADP-06 — CLOSED — CLI nullable selector/query carrier

## 1. Preserve the delivered CLI grammar

The canonical remote grammar remains:

```text
<resource> <operation> [selector] [parameter=value ...]
```

M3 does not introduce a new flag, root-filter command, alternate sentinel or command-specific syntax.

The delivered parser already owns the generic rule:

```text
raw parameter value == "null"
    AND ParameterSpec.nullable == true
        -> parsed value None

raw parameter value == "null"
    AND ParameterSpec.nullable == false
        -> cli_invalid_parameter
```

ADP-06 reuses this grammar unchanged.

## 2. Registry delta

Only the ObjectTemplate list parent-filter parameter changes registry nullability:

```text
command      object-template list
parameter    parent_template_id
kind         STRING
location     QUERY
selector     OBJECT_TEMPLATE
nullable     true
```

The `STRING` kind is preserved because non-null values continue to accept both:

```text
UUID
accepted ObjectTemplate human selector <namespace>.<name>
```

The parameter must not be changed to UUID-only and no second public root-filter parameter is introduced.

No unrelated selector-capable registry parameter becomes nullable merely because ADP-06 adds common nullable-selector handling.

## 3. Parsed intent states

For the affected parameter, parser output is exactly:

```text
parameter omitted
    -> key absent from ParsedCommand.parameters

parent_template_id=null
    -> key present
    -> value None

parent_template_id=<non-null text>
    -> key present
    -> value str
```

Omission and explicit null must never collapse into one parsed command state.

## 4. Direct selector-target construction

Selector discovery is metadata-driven.

For a direct selector-capable ParameterSpec:

```text
parameter absent
    -> no selector target

parameter present with non-null value
    -> normal selector target
    -> existing selector lookup behavior

parameter present with value None
    AND parameter.nullable == true
        -> terminal explicit-null carrier
        -> no selector target
        -> value remains None

parameter present with value None
    AND parameter.nullable == false
        -> invalid parsed/registry state
```

Therefore `None` is not sent to `_lookup()` merely because `selector_kind` is set.

This rule is generic for direct selector-capable parameters and is driven by `ParameterSpec.nullable`; implementation must not special-case the name `parent_template_id`.

## 5. Nested selector scope

ADP-06 does not create a nullable grammar for arbitrary nested selector locations inside JSON objects/arrays.

Nested selector metadata currently identifies traversal path and selector kind, but does not define independent nullability for one nested target. M3 must not infer or broaden such semantics.

If future work needs nullable nested selectors, that requires an explicit registry/contract design rather than silent reuse of the direct-parameter rule.

## 6. Non-null selector behavior is unchanged

When `parent_template_id` has a non-null string value, delivered selector semantics remain authoritative:

```text
syntactically valid UUID
    -> exact-ID precedence
    -> normalized UUID
    -> no discovery GET

<namespace>.<name>
    -> ObjectTemplate selector discovery
    -> GET /api/v1/core/object-templates
       namespace=<namespace>
       name=<name>
       limit=2
    -> exactly one match => resolved UUID
    -> zero/multiple => existing structured selector error
```

M3 does not change selector precedence, ambiguity handling, selector memoization or error codes.

## 7. Explicit null performs zero selector lookup

For:

```text
object-template list parent_template_id=null
```

the selector phase must perform:

```text
0 ObjectTemplate selector-discovery GETs
```

The explicit-null value is terminal metadata-driven intent, not a human selector string.

No fallback UUID parse, namespace/name discovery, enrichment lookup or hidden GET is permitted merely to interpret this null carrier.

## 8. Location-aware request planning

`None` is not a globally valid path/query scalar. Request planning interprets explicit `None` using both registry nullability and parameter location.

Frozen rule:

```text
parameter omitted
    -> omit HTTP carrier

QUERY + value None + nullable=true
    -> emit lexical query pair
       (parameter.name, "null")

QUERY + value None + nullable=false
    -> cli_invalid_parameter / invalid plan

BODY + value None + nullable=true
    -> retain None in body candidate
    -> request DTO validation/serialization emits JSON null where allowed

BODY + value None + nullable=false
    -> request DTO validation or local invalid-parameter boundary

PATH + value None
    -> invalid / impossible valid registry plan
    -> cli_invalid_parameter if reached as caller-controlled state
```

The exact helper/function decomposition remains implementation-local.

## 9. Scalar wire helper remains non-null

M3 explicitly does **not** broaden the delivered scalar serializer into:

```text
_wire_string(None) -> "null"
```

The generic non-null scalar helper continues handling ordinary string/numeric/boolean query/path values only.

The lexical `"null"` query value is emitted by location-aware planning only when:

```text
parameter.location == QUERY
AND parameter.nullable == true
AND parsed/resolved value is None
```

This prevents accidental acceptance of `None` in PATH parameters or non-nullable query parameters.

## 10. BODY nullable behavior is preserved

Existing nullable BODY parameters retain their delivered semantics:

```text
parameter=null
    -> parser None
    -> body candidate contains field: None
    -> request annotation validates it when field is nullable
    -> JSON body contains null
```

ADP-06 introduces no second BODY-null encoding and does not transform JSON null into the lexical string `"null"`.

## 11. Complete ObjectTemplate CLI parent tri-state

The official CLI now realizes exactly the HTTP tri-state frozen by ADP-05.

### Omitted

```text
object-template list
```

produces:

```text
no parent_template_id selector lookup
no parent_template_id query pair
```

Server semantics:

```text
parent_template_id=None
parent_filter_set=False
no parent predicate
```

### Exact UUID

```text
object-template list parent_template_id=<UUID>
```

produces:

```text
normal exact selector resolution
parent_template_id=<canonical UUID> query pair
```

Server semantics:

```text
parent_template_id=UUID
parent_filter_set=True
exact direct-parent predicate
```

### Human ObjectTemplate selector

```text
object-template list parent_template_id=<namespace>.<name>
```

produces:

```text
normal ObjectTemplate discovery GET
resolved UUID
parent_template_id=<resolved UUID> query pair
```

Server semantics are the same exact-parent state as the UUID form.

### Explicit root-only null

```text
object-template list parent_template_id=null
```

produces:

```text
parsed value None
zero selector-discovery GETs
query pair parent_template_id=null
```

Server semantics:

```text
parent_template_id=None
parent_filter_set=True
root-only IS NULL predicate
```

## 12. Failure preservation

ADP-06 introduces no new public CLI error code.

Existing failures remain:

```text
non-null malformed selector
    -> cli_selector_invalid / existing selector failure

unknown parameter
    -> cli_unexpected_parameter

duplicate parameter
    -> cli_duplicate_parameter

explicit null on non-nullable parameter
    -> cli_invalid_parameter

invalid planner state
    -> bounded local cli_invalid_parameter where caller-reachable
```

Transport/remote/protocol failures remain unchanged.

## 13. Request and trace truthfulness

The command's primary HTTP request trace must record the actual query pair emitted.

For explicit null:

```text
query.parent_template_id == ["null"]
```

Selector exchanges must contain no ObjectTemplate lookup attributable to that parameter.

Interactive and non-interactive modes use the same parser/resolver/planner pipeline and therefore must observe identical carrier semantics.

## 14. No lower-layer redesign

ADP-06 changes only official CLI registry/resolution/planning behavior.

It does not change:

```text
HTTP API route or query parameter names
application ObjectTemplate list signature
parent_filter_set visibility
cursor codec or cursor identity model
persistence filtering
ObjectTemplate domain model
selector API routes
CLI transport policy
CLI command grammar
```

The final chain is:

```text
CLI omitted / UUID-or-human / explicit null
    -> metadata-driven parser + selector resolution + request planner
    -> HTTP omitted / UUID / lowercase null
    -> ADP-05 HTTP adapter
    -> UUID|None + parent_filter_set
    -> ADP-04 cursor identity + existing application/persistence tri-state
```

## 15. Implementation-local choices

Architecture does not require specific helper names or one exact patch shape.

Equivalent implementation is valid only if it preserves:

```text
registry-driven nullability
no name-based special case
zero selector lookup for nullable direct None
QUERY-only lexical null handling
BODY JSON null handling
PATH None rejection
unchanged non-null selector behavior
```

# ADP-07 — OPEN — CLI Location materialization grammar

ADP-07 must freeze the expected-Location materialization algorithm used after successful registered `201 Created` responses.

It must define:

```text
location_template token grammar
request-value precedence
response JSON-path lookup
scalar/materializable carrier rule
literal token replacement
missing/unresolvable token behavior
exact actual Location validation
all eight registered 201 operations
no hidden post-mutation GET
```

A valid canonical same-release 201 response must not become `cli_internal_error` because of local expected-Location formatting.

# Downstream verification constraints

`verification.md` / ADP-08 must prove at minimum:

```text
CLI omission
    -> no parent query pair

CLI UUID
    -> canonical UUID query pair

CLI human selector
    -> exactly the required selector discovery
    -> resolved UUID query pair

CLI explicit null
    -> literal lowercase null query pair
    -> zero selector discovery for that parameter

explicit null on non-nullable parameter
    -> cli_invalid_parameter

no global _wire_string(None) behavior
BODY nullable null regression
PATH None rejection/invariant
interactive and non-interactive carrier equivalence
```

Cursor verification must also prove that the resulting root-only request produces the ADP-04 root-only cursor identity rather than the omitted identity.

# Preserved AS-IS responsibilities

ADP-06 does not change:

```text
HTTP-only CLI boundary
63-operation static registry census
remote command grammar
selector kinds and non-null resolution semantics
selector GET routes and ambiguity rules
transport behavior
structured result/error surface
BODY DTO validation
request trace model
interactive/non-interactive shared execution pipeline
```

# ADP status

```text
ADP-06  CLOSED
ADP-07  OPEN
```

No implementation authority is created by this closure. The architecture set remains `DESIGN IN PROGRESS — NOT FROZEN`.
