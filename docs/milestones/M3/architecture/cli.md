# M3 — Official CLI Architecture

**Status:** DESIGN IN PROGRESS — ADP-06 / ADP-07 CLOSED

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

The HTTP lexical carrier for `parent_template_id=null` is frozen by `api.md` / ADP-05. This document produces exactly that public carrier from the official CLI and freezes the common expected-Location materializer used by registered `201 Created` operations.

# ADP-06 — CLOSED — CLI nullable selector/query carrier

## Preserve the delivered CLI grammar

The canonical remote grammar remains:

```text
<resource> <operation> [selector] [parameter=value ...]
```

M3 introduces no new flag, root-filter command, alternate sentinel or command-specific syntax.

The delivered parser retains the generic rule:

```text
raw parameter value == "null"
    AND ParameterSpec.nullable == true
        -> parsed value None

raw parameter value == "null"
    AND ParameterSpec.nullable == false
        -> cli_invalid_parameter
```

## Registry delta

Only the ObjectTemplate list parent-filter parameter changes registry nullability:

```text
command      object-template list
parameter    parent_template_id
kind         STRING
location     QUERY
selector     OBJECT_TEMPLATE
nullable     true
```

`STRING` is preserved because non-null values continue to accept both a UUID and the delivered ObjectTemplate human selector `<namespace>.<name>`. No unrelated selector-capable registry parameter becomes nullable merely because ADP-06 adds common nullable-selector handling.

## Parsed intent states

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

Omission and explicit null never collapse into one parsed-command state.

## Direct selector-target construction

Selector discovery is metadata-driven. For a direct selector-capable `ParameterSpec`:

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

`None` is therefore never sent to selector lookup merely because `selector_kind` is set. This rule is generic for direct selector-capable parameters and must not special-case the name `parent_template_id`.

ADP-06 does not create a nullable grammar for arbitrary nested selector locations inside JSON objects/arrays. Nested selector metadata has no independent nullable bit; future nullable nested-selector semantics require explicit design rather than inference.

## Non-null selector behavior is unchanged

For a non-null `parent_template_id`:

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

M3 does not change selector precedence, ambiguity handling, memoization or error codes.

For:

```text
object-template list parent_template_id=null
```

the selector phase performs zero ObjectTemplate selector-discovery GETs. Explicit null is terminal metadata-driven intent, not a human selector string.

## Location-aware request planning

`None` is not a globally valid path/query scalar. Request planning interprets explicit `None` using registry nullability and parameter location:

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
    -> cli_invalid_parameter if caller-reachable
```

M3 explicitly does not broaden the delivered scalar serializer into `_wire_string(None) -> "null"`. Lexical `"null"` is emitted only by location-aware planning for nullable QUERY parameters.

## Complete ObjectTemplate CLI parent tri-state

```text
object-template list
    -> no parent selector lookup
    -> no parent query pair

object-template list parent_template_id=<UUID>
    -> exact selector resolution
    -> canonical UUID query pair

object-template list parent_template_id=<namespace>.<name>
    -> normal ObjectTemplate discovery
    -> resolved UUID query pair

object-template list parent_template_id=null
    -> parsed None
    -> zero selector-discovery GETs
    -> query pair parent_template_id=null
```

The server then realizes the ADP-05 / ADP-04 states:

```text
omitted       -> parent_template_id=None, parent_filter_set=False
exact parent  -> parent_template_id=UUID, parent_filter_set=True
root-only     -> parent_template_id=None, parent_filter_set=True
```

## Failure and trace preservation

ADP-06 adds no CLI error code. Existing local/selector failures remain authoritative. The primary HTTP request trace records the actual query pair; for explicit null:

```text
query.parent_template_id == ["null"]
```

Interactive and non-interactive modes use the same parser/resolver/planner pipeline and therefore observe the same carrier semantics.

ADP-06 changes no HTTP route, application signature, cursor codec/identity, persistence filter, domain model, selector API route, transport policy or command grammar.

# ADP-07 — CLOSED — CLI Location materialization grammar

## 1. Preserve the registered Location contract

M3 keeps the delivered eight `201 Created` operations and their existing `location_template` metadata. It does not flatten response DTOs, change public `Location` values or weaken exact same-release response validation.

A registered `location_template` is declarative NETAUTO CLI metadata. It is **not** Python `str.format()` syntax.

The common protocol path remains:

```text
primary HTTP response observed
    -> exact status validation
    -> canonical response DTO validation
    -> expected Location materialization
    -> exact actual Location validation
    -> success / cli_protocol_error
```

No post-mutation GET is added to discover or repair a Location identity.

## 2. Tiny Location-template grammar

A template is literal path text plus zero or more token occurrences.

Token grammar:

```text
{segment}
{segment.segment...}

segment = [a-z][a-z0-9_]*
```

Valid examples include:

```text
{id}
{version}
{datatype_id}
{datatype.id}
{object_template.id}
{relationship_definition.id}
```

A dot has one meaning only: traversal through nested JSON objects in the validated response fallback path.

Unsupported syntax includes, among other malformed forms:

```text
{}
{a..b}
{a[0]}
{a!r}
{a:b}
{{a}}
{a.}
{.a}
```

M3 does not support array indexing, wildcards, attribute access, conversion flags, format specifications or any other Python formatting feature.

## 3. Static registry validity

Registry verification must treat `location_template` syntax as closed metadata.

For every registered Location template, static evidence must reject:

```text
unbalanced braces
empty tokens
unsupported token characters
empty path segments
Python-format conversion/spec syntax
any token form outside the grammar above
```

Every `201 Created` operation must have exactly one non-null registered Location template; non-201 operations retain their delivered metadata rules.

Static validation proves syntax only. Runtime materializability against canonical request/response examples is separate ADP-08 evidence.

## 4. Token lookup precedence

For every token `T`, resolution is deterministic:

```text
1. if request_values contains exact key T
       select that exact request value
       do NOT inspect the response for T

2. otherwise
       resolve T as a dot-separated JSON-object path
       in the already validated canonical response body
```

Request precedence is based on exact key presence, not on whether the selected request value is convenient to serialize.

Therefore:

```text
request_values contains T but value is non-materializable
    -> token is non-materializable
    -> no fallback to response path T
```

This preserves the delivered request-before-response precedence without opportunistic ambiguity.

Examples:

```text
{datatype_id}
    -> request_values["datatype_id"] when present

{version}
    -> request_values["version"] when present
       otherwise response["version"]

{id}
    -> response["id"] when no exact request key exists

{datatype.id}
    -> response["datatype"]["id"]

{object_template.id}
    -> response["object_template"]["id"]

{relationship_definition.id}
    -> response["relationship_definition"]["id"]
```

## 5. Response JSON-path traversal

Response fallback traverses only JSON objects:

```text
a.b.c
    -> response["a"]["b"]["c"]
```

Every intermediate segment must resolve to a JSON object/dict containing the next segment.

The materializer does not perform:

```text
array indexing
wildcard traversal
attribute lookup
case conversion
implicit flattening
alternative-field guessing
```

A missing segment or traversal through a non-object carrier makes the token non-materializable; it does not raise an ordinary local exception.

## 6. Materializable scalar carrier

A Location token may materialize only from:

```text
str
int, excluding bool
```

The exact text inserted is `str(value)` after this type check.

The following are non-materializable token values:

```text
None
bool
float
list
object/dict
```

This carrier set is sufficient for the complete eight-operation registry: UUID-like identities are JSON/request strings and versions are integers.

## 7. Literal materialization

After token resolution, materialization performs literal replacement only:

```text
rendered = template
for each distinct token occurrence:
    value = resolve(token)
    if non-materializable:
        return NON_MATERIALIZABLE
    rendered = rendered.replace("{" + token + "}", scalar_text)
return rendered
```

Equivalent implementation is allowed, but it must preserve exact literal token replacement semantics.

The materializer must never call Python `str.format()`, `str.format_map()` or another formatter that assigns special semantics to dots or braces.

If the same token occurs multiple times, every exact literal occurrence uses the same resolved scalar value.

The materializer is total over runtime response/request data: it returns either one expected Location string or a non-materializable result. Data-driven missing/non-scalar token state must not escape as an ordinary local exception.

## 8. Complete eight-operation Location matrix

| Operation | Frozen Location template | Token source |
|---|---|---|
| `datatype create` | `/api/v1/core/datatypes/{datatype.id}` | nested response path |
| `datatype create-next` | `/api/v1/core/datatypes/{datatype_id}/versions/{version}` | request `datatype_id`; response `version` unless exact request key exists |
| `object-template create` | `/api/v1/core/object-templates/{object_template.id}` | nested response path |
| `object-template create-next` | `/api/v1/core/object-templates/{template_id}/versions/{version}` | request `template_id`; response `version` unless exact request key exists |
| `object create` | `/api/v1/core/objects/{id}` | response top-level |
| `relationship-definition create` | `/api/v1/core/relationship-definitions/{relationship_definition.id}` | nested response path |
| `relationship-definition create-next` | `/api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}` | request definition id; response `version` unless exact request key exists |
| `relationship create` | `/api/v1/core/relationships/{id}` | response top-level |

The three nested wrapper identities are intentionally preserved. The five flat-token cases remain covered by the same common materializer.

## 9. Protocol outcome semantics

Location validation occurs only after the successful response status/body has passed canonical same-release validation.

For a registered Location template:

```text
actual Location header count == 1
AND expected Location is materializable
AND actual Location == expected Location exactly
    -> protocol success
```

Any of the following remains a structured protocol failure:

```text
Location missing
Location repeated
Location value mismatches expected
expected token absent
expected token traverses an invalid response path
expected token resolves to a non-materializable carrier
```

All such cases produce:

```text
cli_protocol_error
```

No new public CLI error code is introduced.

A canonical same-release `201 Created` body plus exactly matching Location must never become `cli_internal_error` solely because of local expected-Location processing.

## 10. Exact validation is not normalization

ADP-07 does not normalize or reinterpret the actual Location header.

It does not add:

```text
URI canonicalization
case folding
trailing-slash repair
percent-encoding repair
alternate Location guessing
hidden identity lookup
hidden post-create GET
```

The expected registered Location is materialized deterministically and compared exactly to the one actual header value.

## 11. Shared infrastructure boundary

ADP-07 is common CLI protocol infrastructure. Implementation must not patch only the three currently affected nested templates or add command-specific materializers.

Valid implementation-local choices include helper names, token-scan mechanics and internal sentinel representation, provided they preserve:

```text
closed token grammar
request-key presence precedence
response object-path fallback
str/int(non-bool) scalar rule
literal replacement
no Python format grammar
non-materializable -> protocol result, not local exception
exact one-header comparison
all eight registered creates
```

The registry templates themselves remain unchanged unless a separate governance reopen authorizes a public contract change.

# Downstream verification constraints

`verification.md` / ADP-08 must prove both ADP-06 and ADP-07.

For the ObjectTemplate CLI parent tri-state:

```text
omission -> no parent query pair
UUID -> canonical UUID query pair
human selector -> required selector discovery -> resolved UUID query pair
explicit null -> literal lowercase null query pair -> zero selector discovery
explicit null on non-nullable parameter -> cli_invalid_parameter
BODY nullable null regression
PATH None rejection/invariant
interactive/non-interactive carrier equivalence
root-only cursor identity differs from omitted identity
```

For Location materialization:

```text
registry 201/Location census = 8 / 8
all eight canonical successes materialize exact expected Location
three nested response-path templates explicitly covered
five flat-token templates covered
request-before-response precedence covered
request key present but non-materializable does not fall back
missing Location -> cli_protocol_error
repeated Location -> cli_protocol_error
mismatching Location -> cli_protocol_error
unresolvable/non-scalar expected token -> cli_protocol_error
valid nested-token success -> success, never cli_internal_error
interactive and non-interactive create truthfulness
no hidden post-mutation GET
static registry token syntax rejection
```

# Preserved AS-IS responsibilities

ADP-06 / ADP-07 do not change:

```text
HTTP-only CLI boundary
63-operation static registry census
remote command grammar
selector kinds and non-null resolution semantics
selector GET routes and ambiguity rules
transport behavior
structured result/error surface
BODY DTO validation
request/response trace model
interactive/non-interactive shared execution pipeline
same-release exact status/body validation
existing eight Location templates
exact actual Location contract
mutation operations having no formatted post-success enrichment GET
```

# ADP status

```text
ADP-06  CLOSED
ADP-07  CLOSED
```

No implementation authority is created by these closures. The architecture set remains `DESIGN IN PROGRESS — NOT FROZEN` until ADP-08 and the architecture consistency/freeze gates are complete.
