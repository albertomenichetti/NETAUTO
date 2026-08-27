# M4 TO-BE API — Object properties mutation

Status: PARTIAL ROUTE-LOCAL FREEZE / M4 WIP / NON-NORMATIVE GLOBALLY

This file records the caller-facing contract frozen for the Object property-mutation route during the M4 top-down TO-BE sweep. Execution path, cache use, concurrency and persistence realization remain to be closed before marking the route locally complete.

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
- GET remains the representation surface.

Still to close:

```text
what current Object state must be read
how exact OTV validation cache is used/fill-completed
candidate derivation
no-op semantics
short mutation UoW
lost-update/concurrent DATA_CHANGE handling
interaction with concurrent SCHEMA_CHANGE / DELETE
lifecycle write semantics
TO-BE cost
physical index review handoff
```
