# M4 TO-BE API — Object properties mutation

Status: PARTIAL ROUTE-LOCAL FREEZE / M4 WIP / NON-NORMATIVE GLOBALLY

This file records the caller-facing contract and the execution decisions already frozen for the Object property-mutation route during the M4 top-down TO-BE sweep. Final mutation-statement/index closure remains to be completed before marking the route locally complete.

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

# TO-BE execution model

The execution path is derived from what the operation needs rather than from the current implementation shape.

```text
STEP 1 — current Object existence + exact binding
    PostgreSQL

STEP 2 — operation semantic preparation
    worker-local READY cache

STEP 3 — short mutation Unit of Work
    PostgreSQL
```

## STEP 1 — resolve current exact ObjectTemplate binding, but do not load current properties

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

The intended minimal lookup is conceptually:

```sql
SELECT template_id, template_version
FROM objects
WHERE id = :object_id;
```

The exact SQL remains subject to implementation review, but STEP 1 must remain a minimal PK-rooted lookup and must not load the current JSONB property state.

No `PUBLISHED` check is required for the Object's current exact binding: an existing Object may legitimately remain pinned to a `DEPRECATED` ObjectTemplateVersion.

## STEP 2 — validate/canonicalize requested operations from READY exact-version cache

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

A missing or partial cache is completed first. Validation does not fall back to ad-hoc direct ObjectTemplate/DataType traversal.

STEP 2 produces a prepared mutation tied to the exact binding used for validation:

```text
PreparedPropertyMutation
    prepared_for = (template_id, template_version)
    canonical SET effects
    REMOVE effects
```

No Object row lock is held while cache lookup, cold fill, compilation or operation validation occurs.

## STEP 3 — current properties are read only inside the short mutation UoW

The complete current Object property state becomes necessary only when the command is ready to perform the actual mutation.

Inside the mutation UoW, the command obtains one protected fresh Object generation containing at least:

```text
id
canonical_name
template_id
template_version
properties
```

Conceptually:

```sql
SELECT id, canonical_name, template_id, template_version, properties
FROM objects
WHERE id = :object_id
FOR NO KEY UPDATE;
```

The exact production statement remains subject to implementation review; the frozen requirement is a fresh protected current Object generation that serializes intrinsic Object mutation.

## Binding-stability rule against concurrent SCHEMA_CHANGE

The first check after protecting the current Object is:

```text
protected current binding
    ==
PreparedPropertyMutation.prepared_for
```

If equal, the prepared operations may be applied to the fresh current properties.

If not equal, no mutation is applied in that UoW.

Example:

```text
STEP 1
    Object -> Server v4

STEP 2
    prepare operations using READY Server v4 validation cache

concurrent SCHEMA_CHANGE
    Object -> Server v5
    commits

STEP 3
    protected current Object says Server v5
```

The Server-v4-prepared mutation must not be applied under Server v5 semantics.

The command releases/rolls back the short UoW and performs a bounded restart:

```text
STEP 1
    observe current Server v5 binding

STEP 2
    ensure Server v5 validation facet READY
    prepare operations again under v5 semantics

STEP 3
    retry against a fresh protected Object generation
```

Crucial rule:

> Cache fill or semantic recompilation is never performed while holding the Object row lock.

Retries are bounded. Exhaustion is an internal/concurrency failure rather than an unbounded wait loop.

## Candidate derivation from the protected fresh state

Once binding equality is confirmed:

```text
before = complete current sparse properties

after = before
        + prepared canonical SET effects
        - prepared REMOVE effects
```

Untouched properties are preserved exactly from the protected current generation.

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
REMOVE location
```

produces:

```json
after = {
  "hostname": "srv02",
  "serial": "ABC"
}
```

Persisted untouched values were already admitted under the same exact immutable schema binding. The operation does not reconstruct ObjectTemplate/DataType semantics from persistence or re-certify every untouched value merely because one property changes.

The resulting complete candidate must satisfy the exact schema requirements relevant to the operation. In particular, removing a required property is rejected when the complete `after` state is derived.

## No-op semantics

The protected current state is also the authority for changedness.

```text
after.properties == before.properties
    -> successful 204 No Content
    -> no UPDATE
    -> no DATA_CHANGE lifecycle event
```

Examples include:

```text
SET hostname to its already-current canonical value
REMOVE an already-absent optional property
SET optional LIST to [] when the canonical current state is already absent
```

No fake lifecycle transition is emitted for a semantic no-op.

## Concurrency outcomes

### Property mutation × property mutation

Both operations protect the same Object row in STEP 3.

The waiter reads the fresh committed properties after acquiring protection and derives its `before -> after` transition from that state. This prevents lost JSONB updates and keeps lifecycle snapshots serially explainable.

### Property mutation × SCHEMA_CHANGE

```text
property mutation wins STEP 3 first
    -> commits under the current exact binding
    -> later SCHEMA_CHANGE migrates that committed state

SCHEMA_CHANGE wins first
    -> property mutation observes a changed binding in STEP 3
    -> bounded restart prepares against the new exact binding
```

No stale-schema prepared mutation commits against a newer ObjectTemplateVersion.

### Property mutation × RENAME

Intrinsic Object mutations serialize on the current Object generation. Lifecycle snapshots therefore observe one serially coherent canonical name/state combination.

### Property mutation × DELETE

```text
property mutation protects/commits first
    -> DELETE follows the committed mutation

DELETE wins first
    -> later property mutation observes Object absence and returns the normal not-found outcome
```

No mutation resurrects a deleted Object.

## Lifecycle persistence

For a real change, the same short mutation UoW persists:

```text
UPDATE objects.properties
+
DATA_CHANGE lifecycle event with coherent before/after Object snapshots
```

and commits them atomically.

Conceptually:

```text
BEGIN

protect/read fresh current Object
verify prepared binding still matches
apply prepared operations
validate complete resulting candidate

if no-op
    success without UPDATE/event
else
    UPDATE objects.properties
    INSERT DATA_CHANGE lifecycle event

COMMIT
```

If lifecycle persistence fails, the Object property update rolls back too.

## Cost direction

Warm-cache normal path:

```text
STEP 1
    one minimal Object PK lookup returning exact binding only

STEP 2
    READY cache hit
    CPU-only operation validation/canonicalization

STEP 3
    one protected fresh Object-row read
    application merge/no-op detection
    UPDATE + lifecycle INSERT only for a real change
    COMMIT
```

Cold/partial cache path adds only the reusable semantic-cache fill before STEP 3. The mutation UoW is identical once the cache is READY.

## Physical index review handoff

Physical indexing remains for the subsequent architecture-wide review.

This route specifically requires review/proof that:

```text
STEP 1 Object-id -> exact binding lookup is optimal through Object PK access
STEP 3 protected Object-id lookup is optimal through Object PK access
JSONB property UPDATE/search-index costs remain acceptable with future M5 indexing
```

No route-local extra index is introduced merely for this operation without checking the whole Object/M5 workload.

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
- STEP 1 requires only Object existence + exact OTV binding, not current properties;
- existing Objects do not require current exact OTV `PUBLISHED` admission for property mutation;
- exact property/DataType semantics are consumed from a complete READY cache;
- current properties are loaded only inside the short mutation UoW;
- no Object row lock is held during cache fill/operation validation;
- prepared operations are tied to the exact binding used for preparation;
- STEP 3 must compare the protected current binding with the prepared binding;
- binding mismatch caused by concurrent SCHEMA_CHANGE triggers a bounded restart with no mutation under the stale binding;
- untouched properties are preserved from the fresh protected current state;
- concurrent property mutations serialize on the Object row and derive from fresh committed state;
- semantic no-op returns `204` without UPDATE or lifecycle event;
- real change persists Object properties and lifecycle before/after atomically;
- cache fill is never performed while holding the Object row lock;
- physical index definitions remain deferred to architecture-wide review.

Still to close before marking the route `ROUTE-LOCAL CLOSED`:

```text
exact production mutation SQL/statement count where architecture-significant
final bounded-retry policy classification
final warm/cold statement-count target
confirm no additional cross-route blocker emerges from SCHEMA_CHANGE/DELETE review
```
