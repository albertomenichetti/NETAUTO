# M4 TO-BE API — Object properties mutation

Status: ROUTE-LOCAL ACTIVE REVALIDATION / M4 WIP / NON-NORMATIVE GLOBALLY

This file records the caller-facing contract and current TO-BE execution direction for the Object property-mutation route during the M4 top-down sweep. The route has been reopened for a full-sweep pass; later sections that have not yet been explicitly revalidated remain discovery input rather than frozen current authority. Physical SQL/index design remains an explicit handoff to the subsequent architecture phase.

Cross-operation intrinsic-generation semantics are owned by [`object-revision.md`](object-revision.md) and take precedence over older route-local freshness/fingerprint mechanisms.

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
    -> no revision increment

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

The intended cheap case is per-operation detection while the route already applies requested effects to the current property state of the generation being committed:

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

Only Object runtime property state is in scope semantically. A persisted DATA_CHANGE also advances the technical intrinsic `objects.revision` generation token.

# TO-BE execution model — active revalidation

The three-stage model remains the current working direction:

```text
STEP 1 — current Object generation identity + exact binding
    PostgreSQL

STEP 2 — operation preparation
    worker-local READY semantic cache

STEP 3 — short expected-revision mutation Unit of Work
    PostgreSQL
```

The current full-sweep pass must still confirm final hot/cold SQL/data-carrier shape, statement-cost direction and failure closure before this route returns to closed/full-sweep status.

## STEP 1 — minimal Object generation/binding lookup

Before semantic preparation the command needs only:

```text
Object exists
current exact ObjectTemplate binding
current intrinsic revision
```

Required output:

```text
ObjectBindingGeneration
    object_id
    template_id
    template_version
    revision
```

Conceptual persistence shape:

```sql
SELECT template_id, template_version, revision
FROM objects
WHERE id = :object_id;
```

Important negative requirement:

> STEP 1 does not load current `properties`.

An existing Object may remain pinned to a `DEPRECATED` exact ObjectTemplateVersion. Property mutation is not a new model-plane binding admission and therefore does not require current `PUBLISHED` status or current default resolution.

The observed revision becomes:

```text
expected_revision = R
```

for the final mutation attempt.

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

Prepared operation state must retain the semantic property identity required later by lifecycle construction:

```text
PropertySemanticKey
    declaring_template_id
    property_name
```

Example:

```text
input
    SET hostname = "srv02"
    REMOVE description

prepared mutation for (Server,4)
    SET (declaring_template_id, hostname) = canonical("srv02")
    REMOVE (declaring_template_id, description)
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
prepared generation is identified by revision R
requested effects are independently valid/canonical under T@V
final commit requires current revision == R

therefore
    no committed intrinsic mutation changed binding/properties/name
    between observation and this successful mutation generation
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

## STEP 3 — universal expected-revision mutation boundary

The final mutation attempt is governed by the cross-operation Object revision contract.

Logical rule:

```text
current revision == expected_revision R
    -> this is still the intrinsic Object generation observed in STEP 1
    -> final operation may proceed

current revision != R
    -> stale attempt
    -> no Object mutation
    -> no DATA_CHANGE lifecycle event for this failed attempt
    -> rollback/end attempt
    -> bounded retry from STEP 1
```

This universal generation check replaces the former separate route-local binding-stability protocol.

Because every committed SCHEMA_CHANGE changes the intrinsic `objects` row and increments revision:

```text
revision still R
    -> exact binding is still the T@V used for preparation
```

No second independent binding freshness check is required for the same attempt.

The revision token also intentionally invalidates DATA_CHANGE after a concurrent RENAME or another DATA_CHANGE, even when that mutation touched an otherwise independent intrinsic field. Those conservative false-positive retries are accepted in exchange for one simple intrinsic-generation protocol.

No semantic cache fill occurs inside a stale/retry commit boundary; retry returns to STEP 1 and then reuses or resolves the appropriate READY exact semantics outside the final mutation UoW.

### Current-state application and hot-path carrier — still open physically

A successful expected-revision attempt must apply the prepared effects against the properties of exactly generation `R`, preserve untouched keys, derive the actually changed-property delta, and atomically write the next generation when needed.

Required logical inputs at the final mutation boundary are only:

```text
expected_revision R
prepared exact binding T@V
prepared SET/REMOVE effects
semantic property identities
current values/existence of the requested properties in generation R
```

DATA_CHANGE does not need `canonical_name` or unrelated Object state solely for lifecycle construction.

Preferred performance direction remains to avoid transferring/revalidating the complete property map merely to apply a small operation set. Whether PostgreSQL performs a DB-internal JSONB patch/delta derivation or architecture chooses another equivalent carrier is still open until the hot-path statement analysis is completed.

The final realization must not lose concurrent updates: a writer can commit only from the expected intrinsic generation, and a revision mismatch retries against the newer generation.

### No-op under expected revision

If the normal application of requested effects against generation `R` discovers zero actual property changes:

```text
expected revision matched
zero changed properties
    -> 204
    -> no Object UPDATE
    -> no revision increment
    -> no DATA_CHANGE lifecycle event
```

If revision does not match, the attempt is stale and follows the universal bounded retry rule before classifying the fresh request as no-op or real change.

## Ratified DATA_CHANGE lifecycle — exact changed-property delta

DATA_CHANGE lifecycle follows the M4 operation-owned lifecycle principle. It records the complete exact semantic transition owned by DATA_CHANGE rather than complete Object before/after snapshots.

The transition is the set of semantic properties whose current state actually changed.

Event context includes:

```text
object_id
exact ObjectTemplate binding:
    template_id
    template_version
```

The exact binding gives the historical schema context under which the delta was validated and committed.

Each changed property is identified semantically by:

```text
PropertySemanticKey
    = (declaring_template_id, property_name)
```

For each changed property the event records:

```text
exact before
    canonical value | ABSENT

exact after
    canonical value | ABSENT
```

`ABSENT` is a semantic state distinct from JSON `null`; runtime `null` is not a valid property value.

Examples:

```text
SET previously absent p = V
    before = ABSENT
    after  = canonical V

SET existing p = V2
    before = canonical V1
    after  = canonical V2

REMOVE existing optional p
    before = canonical V
    after  = ABSENT
```

Only properties that actually changed are included. If one request contains no-op and real-change operations, no-op operations are omitted from lifecycle history.

Example:

```text
request
    SET hostname = srv01      # already current
    SET location = milan      # current rome
    REMOVE description        # already absent

DATA_CHANGE lifecycle delta
    location: rome -> milan
```

Therefore lifecycle history records semantic state transition, not the raw command/request audit trail.

DATA_CHANGE lifecycle must not duplicate merely for uniformity:

```text
canonical_name
revision
unchanged properties
components / ownership
Relationships
complete Object before snapshot
complete Object after snapshot
```

`revision` is technical generation metadata and is not automatically part of the semantic lifecycle payload.

The delta is naturally derivable while the final mutation path already examines each requested operation against current generation `R`. Lifecycle-delta construction must not introduce a second full-property-map pass solely for history.

The exact persistence/DTO carrier remains lifecycle architecture/API work. Equivalent realizations may use kind-specific JSON carriers or another typed representation, but they must preserve:

```text
exact binding context
semantic property identity
exact value-or-ABSENT before/after
only actually changed properties
```

### Real mutation

For a real property change the logical persistence transition is:

```text
expected revision R matches
+
apply actual property delta
+
revision := R + 1
+
append exactly one DATA_CHANGE event carrying the exact changed-property delta
+
COMMIT
```

Current property mutation, generation increment and DATA_CHANGE event are atomic. If lifecycle persistence fails, the new Object generation must not commit.

## Concurrency direction under universal revision

All intrinsic Object writers participate in the same generation protocol.

### DATA_CHANGE × DATA_CHANGE

```text
both observe revision R
first successful writer
    -> commits properties + revision R+1 + lifecycle

second writer still expects R
    -> stale mismatch
    -> no mutation/lifecycle
    -> bounded retry against R+1
```

The retried operation is re-applied to the newer current generation, so no JSONB update is lost.

### DATA_CHANGE × RENAME

```text
one commits first and increments revision
other stale attempt fails expected_revision
    -> bounded retry
```

This retry is deliberately conservative even though name and properties are semantically independent. The simplicity of one intrinsic-generation rule is preferred over operation-specific freshness exceptions unless measured contention later disproves the trade-off.

### DATA_CHANGE × SCHEMA_CHANGE

```text
DATA_CHANGE commits first
    -> revision advances
    -> SCHEMA_CHANGE prepared from older generation must retry/reprepare as required

SCHEMA_CHANGE commits first
    -> revision advances
    -> DATA_CHANGE prepared under prior exact binding cannot commit
    -> DATA_CHANGE retries from new generation/binding
```

No operation prepared under one exact binding can commit its property effects under another exact binding.

### DATA_CHANGE × DELETE

```text
DATA_CHANGE commits first
    -> DELETE may subsequently remove that resulting generation

DELETE wins first
    -> expected Object row is absent
    -> DATA_CHANGE cannot commit or resurrect it
```

DELETE remains governed by its database lifetime arbitration in addition to intrinsic-generation semantics.

Exact SQL locking/waiting and bounded retry realization remain architecture work.

## Cache behavior

Warm exact binding:

```text
STEP 1
    PK Object generation/binding lookup

STEP 2
    READY cache hit
    CPU-only requested-operation validation/canonicalization

STEP 3
    expected-revision mutation attempt
```

Cold/partial exact binding:

```text
STEP 1
    same PK generation/binding lookup

STEP 2
    complete READY cache using the shared efficient ObjectTemplate exact-version loader
    no Object mutation lock held
    prepare operations

STEP 3
    identical expected-revision mutation attempt
```

A revision mismatch restarts from STEP 1. If the exact binding remains the same, the already-READY immutable semantics remain reusable; if SCHEMA_CHANGE changed the binding, the new exact semantics are resolved outside the final mutation UoW.

The route depends on the shared bounded ObjectTemplate semantic loader/cache capability. Exact loader/fill architecture remains a cross-domain handoff.

## Cost direction — still open for final hot-path closure

The former 4-statement real-change candidate is no longer the preferred baseline.

Current ratified performance requirements are:

```text
STEP 1
    one minimal generation/binding PK lookup

requested-effect validation
    -> proportional to requested operations/supplied values
    -> no untouched-property recertification

final mutation
    -> expected-revision guarded
    -> no separate binding-freshness query

lifecycle delta construction
    -> derived from requested-operation application
    -> no second full-property-map history pass

no-op classification itself
    -> 0 extra DB statements
    -> 0 extra locks
    -> 0 extra cache/model loads
    -> no extra whole-state equality pass solely for classification
```

A strong current target remains:

```text
warm normal attempt
    S1 generation/binding lookup
    STEP 2 cache/CPU
    S2 expected-revision guarded property mutation + revision advance + lifecycle delta
    COMMIT

~2 PostgreSQL business statements + COMMIT
```

but the exact final S2 SQL/carrier is not yet ratified. Architecture/discovery must confirm that the fused direction can derive requested old values, no-op/real-change outcome, JSONB mutation and lifecycle delta without introducing a worse hot path.

Retry adds another bounded attempt only when a concurrent intrinsic mutation changed revision.

## Data structures touched

Authoritative data-plane state:

```text
objects
    current exact binding
    current revision
    current properties
    property mutation
    atomic revision increment on persisted change

object_lifecycle_events
    one DATA_CHANGE event for a real change
    with operation-specific delta payload
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

The Object row now follows the shared M4 intrinsic-generation direction:

```text
objects
    id
    canonical_name
    template_id
    template_version
    properties JSONB
    revision BIGINT NOT NULL
```

`revision` is cross-operation technical state, not a DATA_CHANGE-specific denormalization.

The shared lifecycle persistence carrier must become capable of representing the ratified DATA_CHANGE property delta. Exact JSON/typed columns, constraints and indexes remain lifecycle/persistence architecture work.

Whether final DATA_CHANGE uses a DB-internal JSONB patch or another equivalent physical realization remains open; current-state authority remains the canonical `properties` value on the Object.

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
- requested-effect validation cost is proportional to requested operations/supplied values;
- DATA_CHANGE lifecycle is an exact delta of only actually changed properties;
- lifecycle context includes the exact ObjectTemplate binding used for validation;
- changed property identity is `(declaring_template_id, property_name)`;
- lifecycle before/after distinguish canonical value from semantic `ABSENT`;
- unchanged properties, `canonical_name` and technical `revision` are omitted from DATA_CHANGE history;
- lifecycle delta construction must fall out of the normal per-operation apply path rather than add a full-map pass;
- STEP 1 resolves exact binding + universal intrinsic `revision`;
- final mutation attempts use `expected_revision` as the universal intrinsic-generation freshness predicate;
- revision mismatch cannot mutate state or emit lifecycle and causes bounded retry;
- successful expected-revision check subsumes separate exact-binding freshness for the observed generation;
- persisted DATA_CHANGE advances revision atomically with properties + lifecycle;
- cheap no-op elision does not advance revision;
- conservative false-positive retries after concurrent RENAME/other intrinsic mutation are intentionally accepted.

Still to revalidate before full-sweep closure:

```text
final fused hot-path SQL/data-carrier feasibility and exact statement-cost direction
bounded retry exhaustion/failure mapping
remaining public failure precedence
physical persistence/index handoff
```
