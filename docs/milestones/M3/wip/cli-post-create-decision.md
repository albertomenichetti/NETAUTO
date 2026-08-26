# M3 — CLI post-create correctness decision

**Status:** CONSOLIDATED DISCOVERY INPUT / NON-NORMATIVE

**Role:** Area A discovery decision. This file records the reviewed scope, root cause and target behavior for CLI `201 Created` / `Location` processing. It does not authorize implementation and does not replace the future M3 contract, architecture set or implementation steps.

## 1. Observed defect

A create operation can complete successfully on the remote HTTP API, persist the resource and return the expected `201 Created` response, while the CLI subsequently reports `cli_internal_error` during local `Location` validation.

The defect is deterministic for registry `Location` templates that use a nested response path token such as:

```text
{datatype.id}
{object_template.id}
{relationship_definition.id}
```

The current materializer first resolves those tokens correctly through JSON-object traversal, but then passes a mapping keyed by the literal dotted token to `str.format_map()`. Python formatting interprets the dot as attribute access rather than as part of the mapping key, so a valid response can raise `KeyError` locally after the successful remote exchange.

## 2. Complete `201 Created` / `Location` census

The static CLI registry contains eight operations with `201 Created` and a `Location` template.

### Nested response-path tokens — affected by the current defect

```text
datatype create
    /api/v1/core/datatypes/{datatype.id}

object-template create
    /api/v1/core/object-templates/{object_template.id}

relationship-definition create
    /api/v1/core/relationship-definitions/{relationship_definition.id}
```

These three commands return wrapper DTOs whose exact public response contains the corresponding nested identity path.

### Flat tokens — not affected by this specific defect

```text
datatype create-next
    /api/v1/core/datatypes/{datatype_id}/versions/{version}

object-template create-next
    /api/v1/core/object-templates/{template_id}/versions/{version}

object create
    /api/v1/core/objects/{id}

relationship-definition create-next
    /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}

relationship create
    /api/v1/core/relationships/{id}
```

The Area A fix must be common infrastructure work, not three registry-specific patches.

## 3. Post-success boundary audit

The create/mutation execution pipeline was reviewed for other local work that could convert an already observed successful mutation response into a false negative.

```text
presentation target construction
    -> occurs before the primary HTTP exchange
    -> cannot misreport an already committed remote success

status/body/Location validation
    -> occurs after the primary response
    -> current nested-token defect is here

FORMATTED enrichment
    -> mutation operations are not in the enrichment whitelist
    -> no post-success enrichment GET is performed for creates/mutations

rendering
    -> serializes the already validated result
    -> no current data-driven mutation-specific defect identified
```

The current concrete Area A scope is therefore the common `Location` materialization/validation path plus durable registry/test coverage for all registered `201` operations.

A general CLI rendering redesign is not added to M3 by this finding.

## 4. Consolidated token grammar

A `Location` template token is declarative CLI metadata. It is **not** Python `str.format()` syntax.

Supported semantics:

```text
{token}
    -> first resolve `token` as one exact key in request values
    -> otherwise resolve `token` as a dot-separated JSON-object path in the canonical response
```

Examples:

```text
{datatype_id}
    -> request value `datatype_id`

{version}
    -> request value when present, otherwise response field `version`

{id}
    -> response field `id` when no request key exists

{datatype.id}
    -> response["datatype"]["id"]

{object_template.id}
    -> response["object_template"]["id"]

{relationship_definition.id}
    -> response["relationship_definition"]["id"]
```

The current request-before-response precedence is preserved.

Dots have only one meaning in this grammar: navigation through nested JSON objects. They must never acquire Python attribute-access semantics.

## 5. Target materializer behavior

For every token found in a registered `Location` template:

1. resolve the token according to the request-key / response-JSON-path rule above;
2. require the resolved value to be an accepted scalar carrier that can be represented in the path;
3. substitute the exact literal `{token}` occurrence with that resolved value;
4. never pass the template through `str.format()` / `str.format_map()` or any formatter that reinterprets dots;
5. if a token cannot be resolved, return a non-materializable expected location to the protocol validator rather than raising an ordinary local exception.

Conceptually:

```python
rendered = template
for token in tokens:
    value = resolve_location_token(token, request_values, result)
    if value is None:
        return None
    rendered = rendered.replace("{" + token + "}", value)
return rendered
```

The exact helper names and implementation structure remain implementation details.

## 6. Public outcome semantics

Exact `Location` validation remains part of the supported same-release CLI protocol contract.

```text
valid canonical 201 response + exactly matching Location
    -> CLI success

201 response with missing, duplicate, malformed, non-materializable or mismatching Location
    -> cli_protocol_error

valid canonical 201 response + correct Location
    -> must not become cli_internal_error because of local materializer behavior
```

M3 must not weaken `Location` validation merely to avoid the false negative. The fix is to make the local validator implement the registered grammar correctly and fail through the existing structured protocol path when the server actually violates the contract.

## 7. Registry invariants and durable evidence

The current registry tests strongly validate request path metadata but do not provide equivalent coverage for `location_template` materializability. M3 should add a closed invariant/evidence set for the complete eight-operation census.

Candidate acceptance evidence:

```text
all 8 registered 201 operations have exactly one registered Location template
all 8 canonical success responses materialize their expected Location
all 3 nested response-path templates are exercised explicitly
all 5 flat-token templates remain covered
correct Location -> success
missing Location -> cli_protocol_error
duplicate Location -> cli_protocol_error
mismatching Location -> cli_protocol_error
unresolvable expected Location -> cli_protocol_error
valid canonical nested-token success never raises and never yields cli_internal_error
interactive and non-interactive boundaries both preserve the structured result
```

Static registry verification should also reject malformed or unsupported `Location` token syntax before runtime.

## 8. Consolidated Area A implementation direction

```text
KEEP
    existing public HTTP Location contract
    existing eight registry Location templates
    nested response-path tokens
    exact same-release response validation
    request-before-response token precedence
    cli_protocol_error for genuine protocol mismatch

CHANGE
    common Location materializer semantics
    remove use of Python format grammar
    add closed static/dynamic coverage for all eight 201 operations

DO NOT
    patch only DataType
    flatten the three wrapper response templates merely to work around format_map
    disable or relax Location validation
    turn a valid committed remote success into cli_internal_error due to local post-success processing
```

This decision closes the materializer design question for Area A. Area A remains in discovery until the remaining contract/acceptance implications are fully folded into the milestone discovery summary and freeze inputs.
