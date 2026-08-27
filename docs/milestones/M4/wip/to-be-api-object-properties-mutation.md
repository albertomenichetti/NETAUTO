# M4 TO-BE API — Object properties mutation

Status: ROUTE-LOCAL CLOSED / M4 WIP / NON-NORMATIVE GLOBALLY

This file records the frozen caller-facing contract and TO-BE execution model for the Object property-mutation route during the M4 top-down sweep. Physical SQL/index design remains an explicit handoff to the subsequent architecture phase and does not reopen the semantic/data-path decisions recorded here.

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

The request is one semantic operation set, not an ordered patch script.

## Sparse property semantics

Object runtime properties remain sparse canonical JSONB.

Consequences:

```text
REMOVE optional property
    -> resulting key absent

SET optional LIST = []
    -> prepared semantic effect is key absence

SET runtime JSON null
    -> invalid

REMOVE required property
    -> semantic validation failure

SET required LIST = []
    -> semantic validation failure
```

Because exact ObjectTemplate semantics are known during operation preparation, `REMOVE` of a required property is rejected before the mutation UoW; current property values are not needed to determine that invalidity.

## Success response

Successful execution returns:

```http
204 No Content
```

Response body: none.

The canonical current Object representation remains the responsibility of:

```http
GET /api/v1/core/objects/{object_id}
```

A semantic no-op also returns `204 No Content` and emits no fake lifecycle transition.

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

Only Object runtime property state is in scope.

# TO-BE execution model

The route has three deliberately separate stages:

```text
STEP 1 — current Object existence + exact binding
    PostgreSQL

STEP 2 — operation preparation
    worker-local READY semantic cache

STEP 3 — short mutation Unit of Work
    PostgreSQL + application merge
```

## STEP 1 — minimal Object binding lookup

Before semantic preparation the command needs only:

```text
Object exists
current exact ObjectTemplate binding
```

Required output:

```text
ObjectBinding
    object_id
    template_id
    template_version
```

Conceptual persistence shape:

```sql
SELECT template_id, template_version
FROM objects
WHERE id = :object_id;
```

Important negative requirement:

> STEP 1 does not load current `properties`.

An existing Object may remain pinned to a `DEPRECATED` exact ObjectTemplateVersion. Property mutation is not a new model-plane binding admission and therefore does not require current `PUBLISHED` status or current default resolution.

STEP 1 must be a cheap primary-key lookup. Exact physical indexing is deferred to the architecture-wide index review.

## STEP 2 — prepare operations only from READY cache semantics

The exact binding obtained in STEP 1 selects the same validation-ready ObjectTemplate capability established for `Object.CREATE`.

Strong rule:

> Property mutation never traverses ObjectTemplate/DataType persistence ad hoc for validation. Missing or partial semantic knowledge is first brought to READY cache state; operation preparation starts only from READY cache semantics.

The cache supplies the exact immutable/stable knowledge required to validate the requested operations, including effective properties, exact DataTypeVersion semantics and compiled validators.

Preparation rules:

```text
SET
    property must exist
    validate SCALAR/LIST shape
    validate exact DTV contract
    canonicalize value

    optional LIST = []
        -> prepared REMOVE

    required LIST = []
        -> error

REMOVE
    property must exist
    required
        -> error
    optional
        -> prepared REMOVE
```

Example:

```text
input
    SET hostname = "srv02"
    REMOVE description

prepared mutation for (Server,4)
    SET hostname = canonical("srv02")
    REMOVE description
```

No current Object property read and no Object row lock occurs during this stage.

### Why full Object revalidation is unnecessary

If:

```text
1. persisted current properties were previously admitted under exact binding (T,V),
2. the exact binding remains unchanged,
3. every requested operation is prepared and validated against the exact immutable semantics of (T,V),
```

then untouched persisted properties remain valid by construction and only the requested semantic effects need to be applied.

The hot path therefore does not re-certify the complete Object or untouched values.

## STEP 3 — short protected mutation UoW

Only after operations are prepared does the command enter its true mutation UoW.

The first statement obtains a fresh protected Object generation, conceptually:

```sql
SELECT
    id,
    canonical_name,
    template_id,
    template_version,
    properties
FROM objects
WHERE id = :object_id
FOR NO KEY UPDATE;
```

The protected state supplies:

```text
fresh exact binding
fresh complete sparse properties
canonical_name required by intrinsic lifecycle snapshots
```

### Binding-stability rule

The exact binding in the protected Object must equal the binding whose READY cache semantics prepared the operation set.

```text
protected binding == prepared binding
    -> proceed

protected binding != prepared binding
    -> perform no mutation
    -> end/rollback current UoW
    -> bounded restart from STEP 1
```

A restart may require loading the newly observed exact binding into cache, but no cache fill is ever performed while holding the Object row lock.

Representative race:

```text
STEP 1
    Object -> Server v4

STEP 2
    prepare against Server v4 cache

concurrent SCHEMA_CHANGE
    Object -> Server v5

STEP 3
    protected Object says Server v5
    -> no mutation
    -> release lock/UoW
    -> restart on v5
```

The restart policy is bounded. Exhaustion is an internal/concurrency failure, not permission to apply operations prepared under stale schema semantics.

### Fresh-state derivation

With unchanged binding:

```text
before = fresh protected properties

after = apply PreparedOperations(before)
```

Untouched keys are preserved exactly.

Example:

```json
before = {
  "hostname": "srv01",
  "serial": "ABC",
  "location": "rome"
}
```

Prepared effects:

```text
SET hostname = srv02
REMOVE location
```

Result:

```json
after = {
  "hostname": "srv02",
  "serial": "ABC"
}
```

No full ObjectTemplate/DataType validation pass is performed under the lock.

### No-op semantics

If:

```text
after == before
```

then:

```text
return 204
no UPDATE
no DATA_CHANGE lifecycle event
```

Examples include:

```text
SET hostname to its already-current canonical value
REMOVE an already-absent optional property
SET optional LIST to [] when the property is already absent
```

### Real mutation

For a real change the UoW is conceptually:

```text
BEGIN

S1
    SELECT protected complete Object
    FOR NO KEY UPDATE
    verify exact binding unchanged
    derive before -> after in application

S2
    UPDATE objects.properties = after

S3
    INSERT intrinsic DATA_CHANGE lifecycle event
        before snapshot
        after snapshot

COMMIT
```

Object update and lifecycle event are atomic. If lifecycle persistence fails, the Object update rolls back.

## Concurrency guarantees

### Property mutation × property mutation

Both operations protect the same Object row during STEP 3.

The waiter receives a fresh current generation and applies its already-prepared semantic effects to that fresh state. This prevents lost JSONB updates and produces a serially explainable `before -> after` lifecycle sequence.

### Property mutation × SCHEMA_CHANGE

```text
property mutation final lock first
    -> it commits against the current exact binding
    -> SCHEMA_CHANGE subsequently migrates that committed state

SCHEMA_CHANGE first
    -> property mutation sees binding mismatch
    -> releases the UoW and restarts against the new exact binding
```

No cache fill is performed while waiting on or holding the Object lock.

### Property mutation × RENAME

The operations serialize on the Object row where required by the mutation realization. The DATA_CHANGE lifecycle snapshot obtains one coherent protected `canonical_name` together with the property state used for before/after.

### Property mutation × DELETE

```text
property mutation protects Object first
    -> mutation commits before a later delete

delete wins first
    -> property mutation observes Object absence and returns the normal not-found outcome
```

No mutation may resurrect a deleted Object.

## Cache behavior

Warm exact binding:

```text
STEP 1
    PK Object binding lookup

STEP 2
    READY cache hit
    CPU-only operation validation/canonicalization

STEP 3
    short mutation UoW
```

Cold/partial exact binding:

```text
STEP 1
    same PK binding lookup

STEP 2
    complete READY cache using the shared efficient ObjectTemplate exact-version loader
    no Object lock held
    prepare operations

STEP 3
    identical short mutation UoW
```

This route depends on the same cross-domain ObjectTemplate capability already tracked by M4: an efficient bounded/bulk load must be formally defined and normalized when the ObjectTemplate TO-BE architecture is reviewed.

## Cost target

Warm real change:

```text
STEP 1
    S1  PK lookup -> exact binding

STEP 2
    cache hit + CPU

STEP 3
    S2  protected complete Object read
    S3  UPDATE complete properties JSONB
    S4  DATA_CHANGE lifecycle INSERT
    COMMIT
```

Target: **4 simple PostgreSQL statements** on the warm real-change path.

Warm semantic no-op:

```text
S1  initial binding lookup
S2  protected complete Object read
```

Target: **2 PostgreSQL statements**, no UPDATE and no lifecycle INSERT.

Cold cache adds the bounded semantic-cache load outside the mutation UoW; the final mutation path is unchanged.

A binding-mismatch race adds a bounded restart and repeats STEP 1/2 for the newly observed exact binding.

## Data structures touched

Authoritative data-plane state:

```text
objects
    STEP 1 exact binding
    STEP 3 protected current state + property UPDATE

object_lifecycle_events
    DATA_CHANGE event for real changes only
```

Immutable semantic dependencies:

```text
worker-local ObjectTemplate validation facet
worker-local exact DTV semantics/validators
ObjectTemplate effective-property materialization used by cold fill
```

This route does not read or mutate:

```text
object_components
relationships
runtime_relationship_resolutions
ObjectTemplate current default
ObjectTemplate current lifecycle status
```

## Relational/schema implications

No new Object relational column or denormalization is required by this route.

The agreed Object shape remains:

```text
objects
    id
    canonical_name
    template_id
    template_version
    properties JSONB
```

Complete-property JSONB replacement remains the authoritative mutation model.

## Physical index review handoff

Physical indexing is intentionally not frozen route-locally.

The subsequent architecture phase must validate the complete workload and confirm that at least these accesses are efficient:

```text
STEP 1 objects PK -> template_id/template_version
STEP 3 objects PK protected read
Object update by PK
lifecycle write/index maintenance
future M5 JSONB GIN/search workload
```

The index review may change physical definitions but must not change the frozen data path or authority split.

## Route-local closure

Frozen for this route:

- `POST /api/v1/core/objects/{object_id}/properties`;
- non-empty unordered semantic SET/REMOVE operation set;
- at most one operation per property;
- sparse canonical property semantics;
- `204 No Content` on success, including semantic no-op;
- STEP 1 reads only Object existence + exact binding;
- no pre-mutation current-property read;
- STEP 2 consumes only complete READY exact-version cache semantics;
- required REMOVE and invalid SET cases are rejected during preparation;
- missing/partial semantic cache is completed before validation;
- no Object row lock is held during cache fill or operation preparation;
- STEP 3 reads one fresh protected complete Object generation;
- binding mismatch causes no mutation and a bounded restart;
- unchanged binding allows direct application of prepared effects without full Object revalidation;
- untouched properties are preserved from fresh protected state;
- semantic no-op performs no UPDATE and emits no lifecycle event;
- real mutation performs complete JSONB UPDATE + DATA_CHANGE lifecycle atomically;
- concurrent property mutations cannot lose updates;
- SCHEMA_CHANGE either follows the property change or causes the property command to restart on the new binding;
- warm real-change target is 4 simple DB statements; warm no-op target is 2;
- no new Object relational column is required;
- physical indexes remain subject to architecture-wide workload review;
- efficient ObjectTemplate exact-version semantic loading remains an explicit ObjectTemplate architecture dependency to define/norm later.
