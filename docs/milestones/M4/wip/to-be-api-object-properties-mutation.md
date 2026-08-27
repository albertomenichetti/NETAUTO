# M4 TO-BE API — Object properties mutation

Status: PARTIAL ROUTE-LOCAL FREEZE / M4 WIP / NON-NORMATIVE GLOBALLY

This file records the caller-facing contract and the execution decisions already frozen for the Object property-mutation route during the M4 top-down TO-BE sweep. Concurrency realization and final persistence/index closure remain to be completed before marking the route locally complete.

## Signature

```http
POST /api/v1/core/objects/{object_id}/properties
Content-Type: application/json
```

Path parameters:

```text
object_id: UUID
```

Query parameters: none.

The former public route name `/data-change` is intentionally replaced by `/properties` because the public operation mutates only Object runtime properties. `DATA_CHANGE` may remain an internal/domain transition name.

## Request

```json
{
  "operations": [
    {
      "op": "SET",
      "property": "hostname",
      "value": "srv02"
    },
    {
      "op": "REMOVE",
      "property": "description"
    }
  ]
}
```

Conceptual wire model:

```text
ObjectPropertiesMutationBody
    operations: PropertyOperation[1..N]

PropertyOperation
    SET
        property: string
        value: JsonValue

    REMOVE
        property: string
```

## Operation semantics

Frozen request-shape rules:

```text
operations
    required
    at least one item

same property
    at most one operation in one request

SET
    requires value

REMOVE
    has no value

array order
    has no semantic mutation-order meaning
```

The command is applied as one semantic candidate over the Object's complete current property state; it is not a sequential patch script whose array order changes the result.

Examples:

```json
{
  "operations": [
    {
      "op": "SET",
      "property": "tags",
      "value": ["core", "prod"]
    }
  ]
}
```

```json
{
  "operations": [
    {
      "op": "REMOVE",
      "property": "location"
    }
  ]
}
```

## Interaction with sparse property semantics

The Object runtime property map remains sparse canonical JSONB.

Therefore:

```text
REMOVE optional property
    -> resulting canonical key absent

SET optional LIST = []
    -> canonicalizes to key absent

REMOVE required property
    -> request is structurally valid
    -> resulting candidate fails semantic validation because required state is missing

SET runtime JSON null
    -> invalid according to Object runtime-value semantics
```

The public command describes desired property operations; final admissibility is determined against the Object's current exact ObjectTemplateVersion semantics.

## Success response

Successful execution returns:

```http
204 No Content
```

Response body: none.

The mutation endpoint acknowledges command success. The canonical current Object representation remains the responsibility of:

```http
GET /api/v1/core/objects/{object_id}
```

## Explicit non-effects

This route does not directly change:

```text
Object id
canonical_name
ObjectTemplate lineage
ObjectTemplate exact version
components / ownership
Relationships
```

Only the Object runtime property state is in scope.

# TO-BE execution decisions frozen so far

The execution path is derived from what the operation needs rather than from the current implementation shape.

## Step 1 — resolve current exact ObjectTemplate binding, but do not load current properties

Before semantic preparation, the command needs to know which exact ObjectTemplateVersion governs the target Object.

Required output:

```text
ObjectBinding
    object_id
    template_id
    template_version
```

This step also proves that the target Object currently exists.

Important negative requirement:

> The command does not need the Object's current `properties` before semantic preparation.

The current property state is deliberately not loaded at this stage because the caller operations can be schema-checked and value-canonicalized from the exact ObjectTemplate validation cache without knowing untouched current values.

Example:

```json
{
  "operations": [
    {"op": "SET", "property": "hostname", "value": "srv02"},
    {"op": "REMOVE", "property": "description"}
  ]
}
```

Given the exact binding `(Server,4)`, the application can determine from cached exact semantics whether:

```text
hostname exists
hostname accepts SET
srv02 is valid/canonical

description exists
description is optional / REMOVE may yield a valid candidate
```

without loading unrelated current properties such as `serial_number`, `location` or `tags`.

## Step 2 — validate/canonicalize requested operations from READY exact-version cache

The selected exact ObjectTemplateVersion uses the same validation-ready cache capability established for `Object.CREATE`.

The cache supplies complete immutable/stable property semantics and exact DataTypeVersion validation knowledge for `(template_id, template_version)`.

The operation-preparation rule is:

```text
ensure exact OTV validation facet READY
    -> validate requested property names/operation shapes
    -> validate/canonicalize SET values
    -> normalize sparse-state consequences where determinable
```

No current Object property read is required during this step.

Examples:

```text
SET optional LIST tags = []
    -> prepared semantic effect is key absence

SET hostname = "srv02"
    -> prepared canonical SET value

REMOVE unknown property
    -> semantic validation failure before mutation UoW
```

A structurally valid operation whose validity depends on the complete resulting Object state, such as removing a required property, is finally adjudicated when the current state is combined with the prepared operations in the mutation UoW.

As with CREATE, a missing or partial cache is completed first. Validation does not fall back to ad-hoc direct ObjectTemplate/DataType traversal.

## Step 3 — current properties are read only inside the short mutation UoW

The complete current Object property state becomes necessary only when the command is ready to perform the actual mutation.

Inside the mutation UoW, the command must obtain one protected current Object generation containing at least:

```text
id
template_id
template_version
properties
```

The exact binding must still match the binding whose semantics were used in Step 2. If another operation changed the Object's exact version before Step 3, the command cannot apply a candidate prepared for stale schema semantics and must follow the final concurrency contract defined later in this route closure.

From the protected current state, the application derives:

```text
before = complete current sparse properties

after = before
        + prepared SET effects
        - prepared REMOVE effects
```

Untouched properties are preserved exactly.

Example:

```json
before = {
  "hostname": "srv01",
  "serial": "ABC",
  "location": "rome"
}
```

with:

```text
SET hostname = srv02
```

produces:

```json
after = {
  "hostname": "srv02",
  "serial": "ABC",
  "location": "rome"
}
```

The same protected `before` state is also required for:

```text
no-op detection
lifecycle before snapshot
lifecycle after snapshot
```

Therefore the route intentionally does not pay for a current-property read before cache preparation and does not hold the Object row lock while cache fill/validation may occur.

## Why complete current-state revalidation is not required before mutation

Persisted untouched properties were already admitted under the Object's exact immutable schema binding. The property mutation therefore does not need to re-run full semantic certification over every untouched property before entering the mutation UoW.

The expensive immutable schema semantics belong to the READY cache. The mutation UoW combines the fresh protected current state with the already prepared requested changes and validates the resulting candidate as required by the exact schema contract.

This keeps the intended separation:

```text
Step 1
    current Object existence + exact binding

Step 2
    immutable semantic preparation from cache

Step 3
    fresh protected current properties
    derive before -> after atomically
    persist real change + lifecycle
```

## Partial route-local freeze

Frozen so far:

- `POST /api/v1/core/objects/{object_id}/properties`;
- no query parameters;
- non-empty `operations` array;
- discriminated `SET` and `REMOVE` operations;
- at most one operation per property per request;
- operation-array order has no semantic meaning;
- sparse canonical property-state consequences;
- `204 No Content` on success;
- GET remains the representation surface;
- pre-mutation preparation requires Object existence + exact OTV binding, not current properties;
- exact property/DataType semantics are consumed from a complete READY cache;
- current properties are loaded only inside the short mutation UoW;
- no Object row lock is held during cache fill/operation validation;
- untouched properties are preserved from the fresh protected current state;
- the protected current state supplies both no-op detection and lifecycle `before/after` derivation.

Still to close:

```text
exact Step-1 minimal lookup shape/cost
final binding-stability behavior if SCHEMA_CHANGE races between Step 1 and Step 3
exact short mutation UoW / row-lock realization
candidate validation inside Step 3
no-op success semantics and lifecycle suppression
concurrent property-mutation lost-update handling
interaction with concurrent DELETE
lifecycle write semantics
TO-BE warm/cold cost
physical index review handoff
```
