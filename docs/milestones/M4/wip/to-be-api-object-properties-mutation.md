# M4 TO-BE API — Object properties mutation

Status: ROUTE-LOCAL FULL-SWEEP CLOSED / M4 WIP / NON-NORMATIVE GLOBALLY

This file records the completed route-local M4 full sweep of Object property mutation before lossless absorption into the consolidated Object owner.

Everything under `wip/` remains globally non-normative and does not authorize implementation. Exact SQL, lock modes, indexes and measured physical plans remain architecture work unless explicitly frozen here.

Cross-operation intrinsic-generation semantics are owned by [`object-revision.md`](object-revision.md) and take precedence over older route-local freshness/fingerprint mechanisms.

---

# 1. Public contract

## Signature

```http
POST /api/v1/core/objects/{object_id}/properties
Content-Type: application/json
```

Path:

```text
object_id: UUID
```

Query parameters: none.

The former public route `/data-change` is intentionally replaced by `/properties` because the caller-facing operation mutates only Object runtime properties. `DATA_CHANGE` remains a useful internal/domain transition name.

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

Conceptual transport model:

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
    non-empty

same property
    at most one operation per request

SET
    requires value

REMOVE
    value forbidden

array order
    no semantic mutation-order meaning
```

The request is one atomic semantic operation set, not an ordered patch script. There is no partial success.

No new wire-level property-name regex is introduced. `property` is structurally a string; whether that name exists in the selected exact effective schema is semantic validation, not transport grammar.

Static malformed request shape belongs to:

```text
400 invalid_request
```

including malformed carriers, empty/missing `operations`, unknown `op`, duplicate property operations, SET without `value`, REMOVE with `value`, and unknown body fields.

A JSON `null` supplied as SET `value` is a structurally interpretable JSON value but is semantically invalid runtime state. It is never interpreted as REMOVE or omission.

---

# 2. Sparse property semantics

Object runtime properties remain sparse canonical JSONB.

Ratified semantics:

```text
REMOVE optional property
    -> resulting key absent

SET optional LIST = []
    -> canonical semantic effect is key absence

SET runtime JSON null
    -> semantic validation failure
    -> never interpreted as REMOVE

REMOVE required property
    -> semantic validation failure

SET required LIST = []
    -> semantic validation failure
```

Because exact ObjectTemplate semantics are known during operation preparation, REMOVE of a required property can be rejected without inspecting that property's current persisted value.

---

# 3. Success and semantic no-op

Successful execution returns:

```http
204 No Content
```

Response body: none.

Current representation remains the responsibility of:

```http
GET /api/v1/core/objects/{object_id}
```

A semantic no-op also returns `204 No Content`.

## Ratified no-op cost rule

DATA_CHANGE is expected to be a high-frequency data-plane operation. Avoiding a no-op write is useful only when recognizing the no-op falls naturally out of work already required by the normal application-side mutation path.

Canonical rule:

```text
if no-op recognition falls out of normal operation application
    -> no Object UPDATE
    -> no revision increment
    -> no DATA_CHANGE lifecycle event

if distinguishing no-op would require material additional work
    -> normal persisted mutation is allowed
    -> do not spend throughput solely to preserve no-op elision
```

No-op recognition must not introduce solely for classification:

```text
additional PostgreSQL statement
additional lock / lock round trip
additional semantic-cache/model lookup
second full-property-map equality pass
whole-Object recertification
```

With the ratified application-layer full-property mutation path, the cheap classification occurs while applying the requested operations to the already-loaded current property map:

```text
SET p = canonical V
    current p already equals V
        -> SET contributes no change

REMOVE p
    p already absent
        -> REMOVE contributes no change
```

A changed flag/delta is accumulated from those per-operation observations. No separate `candidate_properties == current_properties` full-map pass is required solely to discover a no-op.

Examples:

```text
SET hostname to its already-current canonical value
REMOVE an already-absent optional property
SET optional LIST to [] when already canonically absent
```

If every requested operation is a no-op, the command can return after the application-side derivation step with no final mutation statement and no revision recheck.

A concurrent intrinsic mutation occurring after the coherent generation read does not make that response incorrect: the no-op is serially explainable before that later mutation because this command committed no state transition.

---

# 4. Explicit semantic non-effects

DATA_CHANGE semantically changes only Object runtime properties.

It does not directly change or re-certify:

```text
Object id
canonical_name
ObjectTemplate lineage
ObjectTemplate exact version
components / ownership
Relationships
```

A persisted DATA_CHANGE also advances the technical intrinsic `objects.revision` generation token according to the cross-operation revision contract. `revision` is concurrency metadata, not additional business state owned by DATA_CHANGE.

---

# 5. Ratified execution model

The preferred logical path has three stages:

```text
STEP 1 — read one current intrinsic Object generation
    PostgreSQL

STEP 2 — semantic preparation + complete property candidate derivation
    worker-local READY semantic cache + application layer

STEP 3 — short expected-revision commit UoW for real changes only
    PostgreSQL
```

The key ownership split is:

```text
PostgreSQL
    -> authoritative current state
    -> expected-revision CAS / generation arbitration
    -> atomic current-state + lifecycle persistence

application/domain layer
    -> SET/REMOVE semantics
    -> requested-effect validation/canonicalization
    -> current-property transformation
    -> semantic no-op detection
    -> exact DATA_CHANGE delta derivation
    -> complete candidate `properties` construction
```

M4 therefore does **not** choose PostgreSQL JSONB mutation primitives as the normal DATA_CHANGE semantic-mutation layer. The database receives the complete application-derived `properties` candidate for a real change.

This keeps JSON mutation semantics out of SQL and avoids adding operation logic to a database that already owns persistence, MVCC/concurrency, referential integrity and lifecycle atomicity.

A future benchmark may motivate reopening this realization, but DB-side JSON mutation is not the current M4 baseline.

---

# 6. STEP 1 — current generation read

Before semantic preparation/application the route reads one coherent current intrinsic Object generation.

Required output:

```text
ObjectMutationGeneration
    object_id
    template_id
    template_version
    revision
    properties
```

Conceptually:

```sql
SELECT
    template_id,
    template_version,
    revision,
    properties
FROM objects
WHERE id = :object_id;
```

This is an unlocked current-state read. Exact SQL and transaction realization remain architecture work.

Absent Object:

```text
404 resource_not_found
```

The observed revision becomes:

```text
expected_revision = R
```

for any subsequent persisted mutation attempt.

An existing Object may remain pinned to a DEPRECATED exact ObjectTemplateVersion. DATA_CHANGE is not a new model-plane binding admission and therefore does not require:

```text
current PUBLISHED status
current default resolution
latest/highest version selection
```

The exact persisted binding merely selects the immutable semantics under which the requested operations must be validated.

---

# 7. STEP 2 — requested-effect validation and application-layer mutation

## 7.1 READY exact semantics

The exact binding read in STEP 1 selects the validation-ready ObjectTemplate capability used by runtime Object validation.

DATA_CHANGE must not traverse ObjectTemplate/DataType persistence ad hoc for each request. Missing immutable semantic knowledge is brought to READY cache state outside the commit UoW.

Required immutable knowledge includes:

```text
effective property declaration
    declaring_template_id
    property name
    value_mode
    required
    exact datatype_id/version pin

exact DataTypeVersion semantics
    primitive/base type
    canonical constraints

compiled/runtime validators where useful
```

No Object row lock is held during semantic cache fill, validation, canonicalization or application-side candidate construction.

## 7.2 Ratified validation responsibility — requested effects only

DATA_CHANGE validates/canonicalizes exactly the semantic effects requested by the caller.

Canonical boundary:

```text
DATA_CHANGE validation
    = requested operations only

DATA_CHANGE validation
    != complete persisted property-map recertification
    != complete resulting property-map recanonicalization
    != whole-Object consistency sweep
```

For:

```text
SET p = raw_value
```

DATA_CHANGE validates:

```text
p exists in effective schema
SCALAR/LIST shape
exact PrimitiveType parsing/canonicalization
exact DataTypeVersion constraints
required LIST is non-empty
optional LIST = [] -> prepared REMOVE/canonical absence
JSON null -> invalid
```

For:

```text
REMOVE p
```

DATA_CHANGE validates only:

```text
p exists
p.required == false
```

Unknown property, REMOVE-required, JSON null, invalid SCALAR/LIST shape, invalid primitive/constraint value and required LIST=[] are semantic failures:

```text
422 semantic_validation_failed
```

A certified persisted semantic dependency unexpectedly missing/corrupt is an internal invariant failure rather than caller semantic failure.

A semantic failure proven from the coherent generation observed in STEP 1 may be returned immediately. DATA_CHANGE does not perform a revision recheck solely to discover whether a concurrent mutation made a later retry valid. This is an accepted conservative stale-failure policy because no state transition is being committed.

## 7.3 Untouched properties are trusted current state

Untouched persisted properties are preserved exactly without semantic revalidation:

```text
untouched property
    -> preserve current value
    -> no PrimitiveType reparse
    -> no DTV constraint recheck
    -> no recanonicalization
```

This relies on the current property model having no independent cross-property invariant that must be recomputed after every SET/REMOVE. If such an invariant is introduced, DATA_CHANGE must be reopened.

Semantic validation work therefore remains proportional to requested effects:

```text
K = requested operation count

semantic validation
    O(K + supplied-value size)
```

The **complete candidate materialization** for a real mutation is separately proportional to the current property-map size because the application intentionally constructs a complete replacement JSON object. That is a persistence/application cost, not whole-map semantic recertification.

## 7.4 Prepared operations retain semantic identity

Prepared operations retain the identity needed for lifecycle construction:

```text
PropertySemanticKey
    = (declaring_template_id, property_name)
```

Example:

```text
input
    SET hostname = "srv02"
    REMOVE description

prepared under Server@4
    SET (Server-declaring-lineage, hostname) = canonical("srv02")
    REMOVE (declaring-lineage, description)
```

## 7.5 Application-side candidate and delta derivation

The application applies prepared operations to the complete current `properties` value read from revision `R`.

Conceptually:

```text
current_properties_R
    + PreparedOperations(T@V)
    -> candidate_properties
    -> changed flag
    -> exact changed-property delta
```

Example:

```json
current = {
  "hostname": "srv01",
  "serial": "ABC",
  "location": "rome"
}
```

Prepared operations:

```text
SET hostname = srv02
REMOVE location
```

Application candidate:

```json
{
  "hostname": "srv02",
  "serial": "ABC"
}
```

`serial` is copied/preserved but not revalidated.

During the same per-operation application the application records:

```text
old value | ABSENT
new value | ABSENT
changed yes/no
```

for the requested semantic properties. This single pass provides both cheap no-op classification and lifecycle delta material.

If `changed == false` for every operation:

```text
return 204
no STEP 3
no UPDATE
no revision increment
no lifecycle
```

---

# 8. STEP 3 — expected-revision complete replacement

STEP 3 occurs only for a real application-derived property transition.

Input prepared outside the commit UoW:

```text
object_id
expected_revision = R
complete candidate_properties
exact DATA_CHANGE lifecycle delta
exact binding context T@V
```

The final mutation must be generation-guarded:

```text
current revision == R
    -> candidate was derived from the still-current intrinsic generation
    -> persist if remaining database constraints succeed

current revision != R
    -> stale attempt
    -> persist nothing
    -> emit no lifecycle
    -> bounded retry
```

Successful logical mutation:

```text
properties := complete candidate_properties
revision   := R + 1
append exactly one DATA_CHANGE lifecycle delta
COMMIT
```

Properties replacement, revision increment and lifecycle append are atomic.

The logical target is one final PostgreSQL business statement for the real-change CAS/write+lifecycle branch where practical, but exact DML/CTE/RETURNING fusion remains architecture work. M4 does not require PostgreSQL-major-specific OLD/NEW RETURNING facilities.

The final database statement does not own JSON mutation semantics. It persists the already-derived complete candidate and uses the revision predicate to reject stale candidates.

If the final CAS mutates no generation, DATA_CHANGE does not issue a diagnostic query merely to distinguish concurrent DELETE from a revision change. It returns to the normal retry STEP 1:

```text
fresh STEP 1 finds Object absent
    -> 404 resource_not_found

fresh STEP 1 finds Object present at newer revision
    -> continue bounded retry
```

Thus absence-vs-staleness classification reuses the normal retry read and introduces no special diagnostic round trip.

---

# 9. Universal revision consequence

The expected-revision check replaces route-specific freshness protection.

If STEP 1 observed:

```text
binding = T@V
revision = R
```

and final persistence still sees:

```text
revision = R
```

then no committed intrinsic Object mutation has occurred between those points. In particular, no SCHEMA_CHANGE changed the exact binding because SCHEMA_CHANGE must advance revision.

Therefore DATA_CHANGE does not need a second independent final binding-freshness query/predicate in addition to the universal revision rule.

The protocol intentionally allows conservative retries after otherwise-independent mutations:

```text
DATA_CHANGE prepared from R
concurrent RENAME commits R -> R+1
DATA_CHANGE CAS on R fails
    -> retry
```

This accepted false-positive retry is the price of one uniform intrinsic Object generation mechanism.

---

# 10. Retry behavior and exhaustion

Revision mismatch is an internal stale-attempt outcome, never permission to commit a candidate derived from an older generation.

Retry is bounded.

After stale mismatch:

```text
re-read current Object generation
    -> new binding
    -> new revision
    -> new full properties
```

If the exact binding is unchanged:

```text
same T@V
    -> immutable prepared semantic operations remain reusable
    -> re-apply them to the new current properties
    -> derive a new candidate/delta/no-op outcome
```

No revalidation against immutable exact semantics is necessary merely because an unrelated intrinsic mutation advanced revision.

If the exact binding changed:

```text
T@V -> T@W
    -> old prepared operations cannot be assumed valid under T@W
    -> resolve READY T@W semantics
    -> revalidate/canonicalize the original requested effects
    -> apply them to the newly read current properties
```

No cache fill occurs while holding a final commit lock/CAS boundary.

If bounded revision retries are exhausted:

```text
500 internal_error
```

The exhaustion is not exposed as `409 concurrent_modification` or another caller state conflict. It is failure of the internal optimistic-generation protocol to stabilize within its bounded attempt budget.

Exact retry count/backoff remains architecture/implementation work.

---

# 11. Ratified DATA_CHANGE lifecycle

Lifecycle follows the M4 operation-owned transition principle.

DATA_CHANGE records the exact delta of only semantic properties that actually changed.

Event context:

```text
object_id
exact ObjectTemplate binding:
    template_id
    template_version
```

Each changed property identity:

```text
PropertySemanticKey
    declaring_template_id
    property_name
```

Each changed property records:

```text
before
    canonical value | ABSENT

after
    canonical value | ABSENT
```

`ABSENT` is distinct from JSON `null`; runtime null is not a valid property state.

Examples:

```text
SET previously absent p = V
    ABSENT -> canonical V

SET p = V2
    canonical V1 -> canonical V2

REMOVE existing optional p
    canonical V -> ABSENT
```

Only actual state changes appear in the event. Lifecycle is semantic history, not a raw command/request audit log.

Example:

```text
request
    SET hostname = srv01      # already current
    SET location = milan      # current rome
    REMOVE description        # already absent

lifecycle delta
    location: rome -> milan
```

DATA_CHANGE lifecycle does not duplicate:

```text
canonical_name
revision
unchanged properties
components / ownership
Relationships
complete Object before snapshot
complete Object after snapshot
```

`revision` is technical concurrency metadata and is not automatically semantic lifecycle payload.

The exact public/persistence carrier remains lifecycle architecture/API work, but it must preserve the exact binding context, semantic property identity, value-vs-ABSENT state and only the actually changed properties.

---

# 12. Concurrency outcomes

All intrinsic Object writers participate in the universal revision protocol.

## DATA_CHANGE × DATA_CHANGE

```text
both read revision R

first real writer
    -> complete properties replacement
    -> revision R+1
    -> lifecycle

second still expects R
    -> CAS stale
    -> no write/lifecycle
    -> retry from R+1
    -> re-apply requested effects to fresh full properties
```

Thus complete JSONB replacement cannot lose the first writer's committed state.

## DATA_CHANGE × RENAME

```text
one commits first and advances revision
other stale attempt retries
```

Even though name/properties are semantically independent, the conservative retry is intentional under the universal generation model.

## DATA_CHANGE × SCHEMA_CHANGE

```text
DATA_CHANGE commits first
    -> SCHEMA_CHANGE prepared from older generation cannot commit unchanged

SCHEMA_CHANGE commits first
    -> revision advances
    -> DATA_CHANGE prepared against old binding cannot commit
    -> DATA_CHANGE retries against new generation/binding
```

No operation prepared under one exact schema can persist its property candidate over another committed schema generation.

## DATA_CHANGE × DELETE

```text
DATA_CHANGE commits first
    -> DELETE may subsequently remove that resulting generation

DELETE wins first
    -> Object absent
    -> DATA_CHANGE cannot CAS/update or resurrect it
```

Exact SQL locking/wait behavior remains architecture work.

---

# 13. Cache behavior

Warm exact binding:

```text
STEP 1
    read full current Object mutation generation

STEP 2
    READY semantic-cache hit
    validate/canonicalize requested effects
    apply operations in application

no-op
    -> return

real change
    -> STEP 3 CAS full replacement + lifecycle
```

Cold/partial exact binding:

```text
STEP 1
    same current generation read

STEP 2
    bounded immutable semantic cache fill
    no Object lock held
    validate/canonicalize requested effects
    apply in application

STEP 3 only if real change
```

A stale retry with unchanged exact binding reuses READY immutable semantics and already-canonical prepared operations, but must re-read and re-apply against the newer full current property state.

---

# 14. Cost direction

## Warm real change

Current target:

```text
S1
    one Object PK read:
        template_id
        template_version
        revision
        full properties

STEP 2
    cache HIT
    requested-effect validation/canonicalization
    application-side full candidate construction
    lifecycle delta derivation

S2
    expected-revision complete properties replacement
    + revision increment
    + DATA_CHANGE lifecycle append

COMMIT
```

Target:

```text
2 PostgreSQL business statements + COMMIT
```

The application/transport cost includes full current JSONB DB -> worker and full candidate JSONB worker -> DB for a real mutation.

## Warm semantic no-op

```text
S1
    full current generation read

STEP 2
    operation application discovers zero changes

return 204
```

Target:

```text
1 PostgreSQL business statement
0 UPDATE
0 lifecycle INSERT
0 revision increment
```

This improves on the previous protected-read no-op candidate because no final CAS statement is required when the command commits no state transition.

## Cold cache

Cold semantic preparation adds only the bounded immutable-cache load outside the commit UoW. Exact semantic loader cost remains a cross-domain ObjectTemplate architecture handoff.

## Important physical trade-off

Application-side full replacement intentionally pays:

```text
full properties DB -> application
application deserialization/copy/mutation
full candidate serialization
full candidate application -> DB
```

in exchange for:

```text
simple SQL persistence boundary
semantic mutation logic remaining in application/domain code
no JSONB patch-program logic in PostgreSQL
clear testability and ownership
```

PostgreSQL still incurs its normal MVCC/storage/WAL work for the updated JSONB value. M4 does not assume that DB-side JSONB mutation would eliminate that internal write cost; measured evidence would be required to reopen the application-side choice.

Architecture must benchmark realistic property-map sizes and write concurrency before final physical freeze, especially:

```text
JSONB size distribution
DATA_CHANGE frequency
same-Object write contention
network payload
Python encode/decode/copy CPU
PostgreSQL CPU
WAL/TOAST behavior
p50/p95/p99 latency
```

But the current M4 direction is application-layer JSON mutation + complete-field replacement guarded by revision CAS.

---

# 15. Data structures and persistence implications

Current Object row:

```text
objects
    id
    canonical_name
    template_id
    template_version
    properties JSONB
    revision BIGINT NOT NULL
```

DATA_CHANGE adds no route-specific table or denormalization.

Authoritative mutable state touched:

```text
objects
    read binding/revision/full properties
    complete properties replacement on real change
    atomic revision increment

object_lifecycle_events
    exactly one DATA_CHANGE event on real change
```

Immutable semantic dependencies:

```text
worker-local ObjectTemplate effective-property validation facet
worker-local exact DataTypeVersion semantics/validators
bounded certified semantic loader for cold fills
```

Normal DATA_CHANGE does not require:

```text
object_components
Relationship runtime state
ObjectTemplate current default
ObjectTemplate current lifecycle status
```

The shared lifecycle persistence must support the ratified changed-property delta. Exact JSON/typed carrier, constraints and indexes remain lifecycle/persistence architecture work.

No route-specific index is semantically required by DATA_CHANGE. STEP 1 is Object PK access; STEP 3 selects one Object identity and checks its revision as the generation predicate. Architecture must evaluate the physical plan and may choose supporting structures only from measured whole-workload evidence.

---

# 16. Final public failure mapping and precedence

Public failure set:

```text
400 invalid_request
    malformed/static request shape

404 resource_not_found
    selected Object absent on the authoritative observed/retry generation

422 semantic_validation_failed
    unknown property
    REMOVE required property
    SET null
    SCALAR/LIST shape mismatch
    primitive validation failure
    exact DTV constraint failure
    required LIST = []

500 internal_error
    impossible persisted semantic/reference/invariant failure encountered on required path
    unexpected persistence/lifecycle failure
    bounded revision retry exhaustion
```

There is no normal public `409` for DATA_CHANGE. Revision mismatch is an internal stale-attempt condition, not a business state conflict.

Precedence on the normal path:

```text
1. static request invalid
       -> 400 invalid_request
       -> no DB work

2. STEP 1 finds Object absent
       -> 404 resource_not_found

3. coherent generation exists but request is semantically invalid
       -> 422 semantic_validation_failed
       -> no revision recheck solely to refresh the failure

4. application derives semantic no-op
       -> 204 No Content
       -> no revision recheck
       -> no UPDATE / lifecycle / revision increment

5. application derives real mutation
       -> STEP 3 expected-revision CAS

6. CAS succeeds
       -> complete properties + revision+1 + lifecycle commit atomically
       -> 204 No Content

7. CAS is stale / mutates no generation
       -> no state/lifecycle committed by this attempt
       -> normal bounded retry from STEP 1

8. retry STEP 1 finds Object absent
       -> 404 resource_not_found

9. retry observes changed exact binding
       -> revalidate original requested effects under new exact semantics
       -> resulting current semantic outcome may be 422 / no-op 204 / real mutation

10. retry budget exhausted
       -> 500 internal_error
```

This precedence deliberately permits conservative semantic failures/no-op results from one coherent observed generation without paying an extra freshness round trip when no state transition is being committed.

---

# 17. Architecture handoff

Discovery intentionally does not freeze:

```text
exact SQL/SQLAlchemy syntax
exact CAS UPDATE + lifecycle fusion carrier
exact lock/wait behavior produced by PostgreSQL under contention
retry count/backoff
physical indexes
EXPLAIN/BUFFERS evidence
JSONB/TOAST/WAL measured costs
lifecycle physical detail carrier
```

Architecture must preserve:

```text
application owns JSON mutation semantics
application derives complete candidate from one observed generation
application validates only requested effects
untouched values are preserved without recertification
real write is guarded by expected_revision
stale candidate can never overwrite newer intrinsic state
real DATA_CHANGE atomically writes properties + revision+1 + exact lifecycle delta
cheap semantic no-op performs no write/revision/lifecycle
revision contention is retried internally and is not exposed as normal 409
```

No unresolved route-local relational or cache denormalization is required before architecture. The remaining physical choices above do not reopen the ratified DATA_CHANGE semantic/data-path contract unless measurement proves the application-side full-JSON replacement materially unsuitable.

---

# 18. Route-local full-sweep closure

Ratified for this route:

- `POST /api/v1/core/objects/{object_id}/properties`;
- non-empty unordered atomic SET/REMOVE operation set;
- at most one operation per property;
- `property` remains a string carrier with semantic schema lookup rather than a new wire regex;
- sparse canonical property semantics;
- `204 No Content` on success;
- semantic no-op elision only when recognition adds no material work;
- no second whole-map comparison solely for no-op detection;
- semantic validation/canonicalization applies only to requested effects;
- semantic failure may return from the coherent observed generation without a revision refresh;
- untouched persisted properties are preserved without semantic revalidation;
- no complete property-map recanonicalization or whole-Object consistency sweep;
- DATA_CHANGE lifecycle is the exact delta of only actually changed semantic properties;
- lifecycle property identity is `(declaring_template_id, property_name)`;
- lifecycle distinguishes canonical value from `ABSENT`;
- lifecycle omits unchanged properties, canonical_name and technical revision;
- universal intrinsic `revision` is read with the source generation;
- real persisted mutation uses `expected_revision` and advances revision atomically;
- revision mismatch emits no mutation/lifecycle and causes bounded retry;
- revision freshness subsumes a separate final exact-binding freshness mechanism;
- conservative false-positive retries after unrelated intrinsic mutations are accepted;
- the complete current `properties` map is read in STEP 1;
- SET/REMOVE application, no-op detection, lifecycle-delta derivation and complete candidate construction occur in the application/domain layer;
- real DATA_CHANGE persists the complete application-derived `properties` value rather than using PostgreSQL JSONB mutation primitives as the normal semantic path;
- warm real-change target is 2 PostgreSQL business statements + COMMIT;
- warm application-detected no-op target is 1 PostgreSQL business statement;
- no-op returns without revision CAS because it commits no transition;
- stale CAS classification reuses normal STEP 1 rather than a diagnostic query;
- retry with same exact binding reuses immutable prepared operations;
- retry with changed exact binding revalidates the original request;
- retry exhaustion maps to `500 internal_error`;
- DATA_CHANGE introduces no normal public `409`;
- no route-specific relational denormalization or index is required by discovery;
- physical SQL/fusion/index/EXPLAIN/retry-count and JSONB storage measurements remain architecture handoffs.

The route-local sweep is complete. Next maintenance step: perform a lossless comparison/absorption into [`object.md`](object.md), update navigation, and remove route-only source files when safe. Git history remains the historical record.
