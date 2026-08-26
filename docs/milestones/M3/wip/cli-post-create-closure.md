# M3 — CLI Post-Create Correctness Closure

**Status:** CONSOLIDATED DISCOVERY INPUT / NON-NORMATIVE

**Role:** Area A closure record and downstream planning input. This document does not authorize implementation and does not replace the future M3 contract, architecture set or implementation steps.

## 1. Closure statement

Area A — CLI post-create correctness is complete at discovery level.

The repository audit identified the complete `201 Created` / `Location` surface, the deterministic root cause of the observed false-negative, the affected command set, the common implementation boundary, the public outcome semantics to preserve and the durable evidence required later.

No further Area A discovery is required unless Area C or the contract/architecture consistency review reveals a direct conflict.

## 2. Complete `201 Created` / `Location` census

The static CLI registry contains eight operations with `201 Created` and an exact `Location` contract.

```text
datatype create
    nested response token: {datatype.id}
    affected by current materializer defect

datatype create-next
    flat tokens: {datatype_id}, {version}

object-template create
    nested response token: {object_template.id}
    affected by current materializer defect

object-template create-next
    flat tokens: {template_id}, {version}

object create
    flat token: {id}

relationship-definition create
    nested response token: {relationship_definition.id}
    affected by current materializer defect

relationship-definition create-next
    flat tokens: {relationship_definition_id}, {version}

relationship create
    flat token: {id}
```

The current defect is therefore bounded to three of the eight registered `201` operations, while the corrective work belongs to the shared materializer rather than to those three registry entries individually.

## 3. Root cause

The current materializer already resolves dotted tokens as JSON paths, but then stores the resolved value under the literal dotted token and passes the template to `str.format_map()`.

Python formatting reinterprets a token such as `datatype.id` as key `datatype` followed by attribute access `.id`, not as the literal mapping key `datatype.id`. A canonical server response can therefore raise `KeyError` locally after the successful remote exchange.

This is a CLI implementation defect, not an API defect and not a registry-contract defect.

## 4. Consolidated token grammar

A registered `Location` token is declarative CLI metadata, not Python format syntax.

```text
{token}
    -> first resolve token as an exact request-value key
    -> otherwise resolve token as a dot-separated JSON-object path in the canonical response
```

Request-before-response precedence is preserved.

A dot has exactly one meaning in a `Location` token: JSON-object traversal.

Examples:

```text
{datatype_id}                  request value when present
{version}                      request value when present, otherwise response field
{id}                           response field when no request value exists
{datatype.id}                  response["datatype"]["id"]
{object_template.id}           response["object_template"]["id"]
{relationship_definition.id}   response["relationship_definition"]["id"]
```

## 5. Target materialization rule

The common materializer must:

1. enumerate registered `{token}` occurrences;
2. resolve each token by the grammar above;
3. accept only scalar path carriers supported by the existing protocol contract;
4. substitute the literal `{token}` occurrence directly;
5. never invoke Python `str.format()` / `str.format_map()` or another formatter that assigns special semantics to dots;
6. return a non-materializable expected location when a token cannot be resolved rather than raising an ordinary local exception.

The exact helper structure remains an implementation detail.

## 6. Public outcome semantics to preserve

M3 must retain exact same-release `Location` validation.

```text
canonical 201 body + exactly matching Location
    -> success

missing / duplicate / malformed / mismatching Location
    -> cli_protocol_error

expected Location cannot be materialized from the canonical response/request values
    -> cli_protocol_error

canonical 201 body + correct Location
    -> must not become cli_internal_error due to local materializer behavior
```

The fix must not weaken protocol validation or flatten the three nested registry templates merely to accommodate Python formatting behavior.

## 7. Post-success boundary conclusion

The wider create/mutation post-success path was audited.

```text
presentation-target construction
    -> before the primary HTTP exchange
    -> cannot misreport an already observed remote success

status/body/Location validation
    -> after the primary response
    -> concrete Area A defect lives here

FORMATTED enrichment
    -> create/mutation operations are not in the enrichment whitelist
    -> no post-success enrichment GET applies

rendering
    -> serializes the already validated mutation result
    -> no current data-driven mutation-specific false-negative path identified
```

A general rendering redesign is therefore outside Area A and outside the current M3 scope.

## 8. Registry and regression evidence required downstream

Later contract/steps should require at minimum:

```text
all 8 registered 201 operations have exactly one Location template
all 8 canonical success responses materialize the expected Location
all 3 nested response-path templates are exercised explicitly
all 5 flat-token templates remain covered
correct Location -> success
missing Location -> cli_protocol_error
duplicate Location -> cli_protocol_error
mismatching Location -> cli_protocol_error
unresolvable expected Location -> cli_protocol_error
valid nested-token success never raises and never yields cli_internal_error
interactive and non-interactive boundaries preserve the structured result
static registry evidence rejects malformed / unsupported Location token syntax
```

## 9. Downstream contract / architecture inputs

The future M3 contract should freeze the observable rule that a valid committed remote create with a canonical `201` response and correct `Location` is a CLI success, while genuine same-release response violations remain `cli_protocol_error`.

The future M3 CLI architecture should define the `Location` token grammar and shared materialization boundary explicitly, preserving the existing static registry and HTTP-only client model.

The future implementation steps should assign the shared materializer correction and the complete eight-operation evidence set without introducing command-specific workarounds.

## 10. Scope impact

No Area A discovery finding requires a database schema, migration, dependency or lockfile change.

Expected implementation touchpoints are limited to CLI protocol/registry verification and tests, subject to the normal M3 freeze and authorization gates.
