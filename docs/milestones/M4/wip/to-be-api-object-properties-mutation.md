# M4 TO-BE API — Object properties mutation

Status: ROUTE-LOCAL ACTIVE REVALIDATION / M4 WIP / NON-NORMATIVE GLOBALLY

This file records the caller-facing contract and current TO-BE execution direction for the Object property-mutation route during the M4 top-down sweep. The route has been reopened for a full-sweep pass; later sections that have not yet been explicitly revalidated remain discovery input rather than frozen current authority. Physical SQL/index design remains an explicit handoff to the subsequent architecture phase.

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

Ratified request-shape rules:

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

The request is one atomic semantic operation set, not an ordered patch script. There is no partial success.

Static malformed request shape belongs to `400 invalid_request`; property existence and runtime value admissibility are semantic validation questions.

## Sparse property semantics

Object runtime properties remain sparse canonical JSONB.

Ratified semantic direction:

```text
REMOVE optional property
    -> resulting key absent

SET optional LIST = []
    -> canonical semantic effect is key absence

SET runtime JSON null
    -> invalid semantic value; never interpreted as REMOVE

REMOVE required property
    -> semantic validation failure

SET required LIST = []
    -> semantic validation failure
```

Because exact ObjectTemplate semantics are known during operation preparation, `REMOVE` of a required property can be rejected without reading the current value of that property.

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

A semantic no-op also returns `204 No Content`.

### Ratified no-op cost rule

DATA_CHANGE is expected to be a high-frequency operation. Avoiding a no-op write is therefore useful only when recognition of the no-op does not add material work to the normal mutation path.

Canonical rule:

```text
if no-op recognition falls out of work already required
for applying the requested operations
    -> no UPDATE
    -> no DATA_CHANGE lifecycle event

if distinguishing no-op would require material extra work
    -> perform the normal mutation path
    -> do not spend throughput solely to preserve no-op elision
```

In particular, no-op elision must not require solely for that purpose:

```text
an additional PostgreSQL statement
an additional lock or lock round trip
an additional semantic-cache/model lookup
a second full-property-map comparison pass
an additional whole-Object recertification
```

The intended cheap case is per-operation detection while the route already applies requested effects to the fresh current property state:

```text
SET p = canonical V
    current p already equals canonical V
        -> that SET contributes no change

REMOVE p
    p already absent
        -> that REMOVE contributes no change
```

With `K = number of requested operations`, no-op recognition should be bounded by the requested effects themselves rather than by an additional whole-state equality pass performed solely to classify the outcome.

Examples that may therefore be elided when detected on the normal apply path include:

```text
SET hostname to its already-current canonical value
REMOVE an already-absent optional property
SET optional LIST to [] when the property is already canonically absent
```

This cost rule supersedes the previous unconditional requirement to construct a complete candidate and then perform `after == before` solely to decide whether to skip persistence.

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

# TO-BE execution model — active revalidation

The three-stage model remains the current working direction:

```text
STEP 1 — current Object existence + exact binding
    PostgreSQL

STEP 2 — operation preparation
    worker-local READY semantic cache

STEP 3 — short mutation Unit of Work
    PostgreSQL + application merge
```

The current full-sweep pass must still confirm lifecycle payload, final data path and concurrency consequences before this route returns to closed/full-sweep status.

## STEP 1 — minimal Object binding lookup candidate

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

STEP 1 should remain a cheap primary-key lookup. Exact physical indexing is deferred to the architecture-wide index review.

## STEP 2 — prepare requested operations from READY exact semantics

The exact binding obtained in STEP 1 selects the validation-ready ObjectTemplate capability established for Object runtime consumers.

Current rule:

> Property mutation must not traverse ObjectTemplate/DataType persistence ad hoc for every request. Missing or partial semantic knowledge is brought to READY immutable/stable cache state before the short mutation UoW.

The cache supplies the exact semantic knowledge required to validate the requested operations, including effective property declarations, exact DataTypeVersion semantics and compiled validators.

Preparation rules:

```text
SET
    property must exist
    validate SCALAR/LIST shape
    validate exact DTV contract
    canonicalize supplied value

    optional LIST = []
        -> prepared REMOVE

    required LIST = []
        -> semantic validation failure

REMOVE
    property must exist
    required
        -> semantic validation failure
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

No current Object property read and no Object row lock is required merely to validate/canonicalize the request effects during this preparation stage.

### Ratified validation responsibility — requested effects only

DATA_CHANGE validates and canonicalizes exactly the semantic effects requested by the caller. It does not revalidate untouched persisted properties and does not re-certify the complete Object.

Canonical boundary:

```text
DATA_CHANGE validation
    = requested operations only

DATA_CHANGE validation
    != complete persisted property-map recertification
    != complete resulting property-map recanonicalization
    != domain consistency sweep
```

For `SET p = value`, DATA_CHANGE owns validation of:

```text
p exists in the effective schema of the prepared exact binding
requested SCALAR/LIST shape matches p.value_mode
supplied value satisfies exact PrimitiveType parsing/canonicalization
supplied value satisfies exact DataTypeVersion constraints
required LIST is non-empty
optional LIST = [] becomes canonical absence / prepared REMOVE
JSON null is invalid and is never interpreted as absence
```

For `REMOVE p`, DATA_CHANGE owns validation of:

```text
p exists
p.required == false
```

A required property cannot be removed regardless of its current persisted value, so no current-property read is required merely to reject that operation during preparation.

Untouched current properties are trusted as already-admitted current state under the Object's exact binding and are preserved without semantic revalidation:

```text
untouched persisted property
    -> preserve current canonical value as-is
    -> no PrimitiveType reparse
    -> no exact DTV constraint recheck
    -> no recanonicalization
```

The proof obligation is deliberately narrow:

```text
current Object properties were admitted under exact binding T@V
prepared binding remains T@V at mutation time
requested effects are independently valid/canonical under T@V
untouched values are not changed

therefore
    applying the requested effects preserves the property-state contract
```

This relies on the current Object property model having no independent cross-property invariant that must be recomputed after every SET/REMOVE. If such a cross-property invariant is introduced later, DATA_CHANGE must be revalidated rather than silently retaining this local-validation proof.

Impossible corruption encountered incidentally on state already required by the normal path remains an internal invariant failure; this does not authorize additional scans or revalidation solely to search for corruption.

Performance consequence:

```text
K = requested operation count

semantic validation work
    -> O(K + supplied value size)

not
    -> O(total effective property count)
    -> O(total persisted property count)
```

## STEP 3 — existing candidate: short protected mutation UoW

The route obtains a fresh protected Object generation after operation preparation.

Conceptually the required current facts include:

```text
fresh exact binding
fresh current sparse properties
```

The old full-snapshot lifecycle requirement is no longer assumed: after the ratified operation-owned lifecycle principle, DATA_CHANGE lifecycle payload must be revalidated independently during this full sweep.

### Binding-stability candidate

The exact binding in the protected current Object must match the binding whose semantics prepared the requested operations:

```text
protected binding == prepared binding
    -> proceed

protected binding != prepared binding
    -> do not apply operations prepared against stale semantics
    -> release/end current UoW
    -> bounded re-resolution/restart candidate
```

No semantic cache fill should occur while holding the final Object mutation protection.

### Fresh-state application

With unchanged binding, requested prepared effects are applied to the fresh current property state while preserving untouched keys exactly.

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

`serial` is copied/preserved from current state; it is not semantically revalidated because DATA_CHANGE did not change it.

No-op recognition, when retained, follows the ratified zero-material-extra-work rule above. The route must not add a second complete-map comparison pass solely to decide whether to skip persistence.

### Real mutation — subject to lifecycle revalidation

The current persistence direction for a real property change remains:

```text
update current Object properties atomically
+
append the required DATA_CHANGE lifecycle fact(s)
+
COMMIT
```

The previous assumption that DATA_CHANGE must persist complete Object `before` / `after` snapshots is explicitly reopened. The final lifecycle payload will be derived from the semantic transition DATA_CHANGE itself owns.

## Concurrency guarantees — pending current full-sweep revalidation

The previous candidate established the important current-state guarantees:

```text
DATA_CHANGE x DATA_CHANGE
    -> no lost property updates

DATA_CHANGE x SCHEMA_CHANGE
    -> operations validated under one exact binding must not commit under another

DATA_CHANGE x DELETE
    -> no mutation-after-delete / no resurrection
```

The exact coordination required with RENAME is reduced by the ratified operation-specific lifecycle principle: DATA_CHANGE must not read/stabilize `canonical_name` merely to populate a generic full Object lifecycle snapshot. Any remaining concurrency interaction must follow actual field/invariant ownership rather than historical payload uniformity.

Exact lock/wait/restart realization remains architecture work.

## Cache behavior — current candidate

Warm exact binding:

```text
STEP 1
    PK Object binding lookup

STEP 2
    READY cache hit
    CPU-only requested-operation validation/canonicalization

STEP 3
    short mutation UoW
```

Cold/partial exact binding:

```text
STEP 1
    same PK binding lookup

STEP 2
    complete READY cache using the shared efficient ObjectTemplate exact-version loader
    no Object mutation lock held
    prepare operations

STEP 3
    identical short mutation UoW
```

The route depends on the shared bounded ObjectTemplate semantic loader/cache capability. Exact loader/fill architecture remains a cross-domain handoff.

## Cost direction — reopened

The old cost target was:

```text
warm real change
    4 PostgreSQL business statements + COMMIT

warm no-op
    2 PostgreSQL statements
```

Those counts are not re-ratified yet because lifecycle payload and mutation statement fusion are being revisited.

The current ratified performance requirements are:

```text
requested-effect validation
    -> proportional to requested operations/supplied values
    -> no untouched-property recertification

no-op classification itself
    -> 0 extra DB statements
    -> 0 extra locks
    -> 0 extra cache/model loads
    -> no extra whole-state equality pass solely for classification
```

If architecture later finds that preserving no-op elision would materially worsen the preferred hot mutation path, the elision requirement must be reconsidered rather than forcing extra work into every DATA_CHANGE.

## Data structures touched — current direction

Authoritative data-plane state:

```text
objects
    current exact binding
    current properties
    property mutation

object_lifecycle_events
    DATA_CHANGE event for real changes according to the revalidated lifecycle contract
```

Immutable semantic dependencies:

```text
worker-local ObjectTemplate validation facet
worker-local exact DataTypeVersion semantics/validators
bounded ObjectTemplate effective-property materialization used by cold fill
```

The route does not semantically require normal reads/mutations of:

```text
object_components
runtime Relationship state
ObjectTemplate current default
ObjectTemplate current lifecycle status
```

## Relational/schema implications

No new Object relational column or route-specific denormalization has been identified.

The current Object shape remains:

```text
objects
    id
    canonical_name
    template_id
    template_version
    properties JSONB
```

Whether final DATA_CHANGE uses complete JSONB replacement or a narrower PostgreSQL JSONB update realization remains an architecture/data-path question to re-evaluate after the semantic/lifecycle blocks close; current-state authority remains the canonical `properties` value on the Object.

## Revalidation status

Ratified in the current full-sweep pass so far:

- `POST /api/v1/core/objects/{object_id}/properties`;
- non-empty unordered atomic SET/REMOVE operation set;
- at most one operation per property;
- sparse property semantics direction;
- `204 No Content` on success;
- semantic no-op may avoid UPDATE/lifecycle only when recognition adds no material work to the normal path;
- no extra query/lock/cache/model load or whole-state equality pass solely for no-op classification;
- mutation scope is Object runtime properties only;
- semantic validation/canonicalization applies only to requested effects;
- untouched persisted properties are trusted as already-admitted current state and preserved without revalidation;
- no complete property-map recanonicalization or whole-Object consistency sweep;
- requested-effect validation cost is proportional to requested operations/supplied values.

Still to revalidate before full-sweep closure:

```text
exact DATA_CHANGE lifecycle payload
final hot/cold data path and statement-cost direction
binding-change/retry behavior
concurrency matrix/failure mapping
physical persistence handoff
```
