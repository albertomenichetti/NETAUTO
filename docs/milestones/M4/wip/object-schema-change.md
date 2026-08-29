# M4 WIP — Object SCHEMA_CHANGE consolidated discovery

**Status:** FULL-SWEEP COMPLETE / REVIEWED BASELINE CANDIDATE / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This document is the consolidated M4 working owner for detailed `Object.SCHEMA_CHANGE` semantics and logical execution.

Public Object-family navigation is owned by [`object.md`](object.md). Cross-operation current component persistence is owned by [`object-components-persistence.md`](object-components-persistence.md). Cross-operation intrinsic Object generation/freshness is owned by [`object-revision.md`](object-revision.md). General version and lifecycle principles are owned by [`general-domain-principles.md`](general-domain-principles.md).

Everything under `wip/` remains globally non-normative and does not authorize implementation.

The top-down SCHEMA_CHANGE full sweep is complete. Older `object-schema-change-*`, optimistic-fingerprint and aggregate-fingerprint micro-WIPs are historical/source evidence only and may be removed after the final lossless reference cleanup. Git history remains the historical record.

# 1. Public contract

```http
POST /api/v1/core/objects/{object_id}/schema
Content-Type: application/json
```

Path:

```text
object_id: UUID
```

Query parameters: none.

Request:

```json
{
  "target_version": 5
}
```

Conceptual transport model:

```text
ObjectSchemaMutationBody
    target_version: positive integer
```

Unknown/malformed request carriers remain normal static invalid-request input.

The operation keeps the Object's stable `template_id` and selects one exact ObjectTemplateVersion inside that lineage.

Success:

```http
204 No Content
```

The resulting current state is read through:

```text
GET /objects/{id}
GET /objects/{id}/schema
```

# 2. Exact-target command semantics

For current exact binding:

```text
SOURCE = T@VS
```

and request:

```text
TARGET = T@VT
```

SCHEMA_CHANGE is an **exact-target migration command**.

Canonical version rule:

```text
version number
    = exact-version identity
    + creation/allocation order within one lineage

version number
    != genealogy
    != semantic evolution order
    != compatibility order
    != migration order
    != publication order
```

Therefore:

```text
VT > VS
VT < VS
```

carry no migration-admission meaning by themselves. Terms such as upgrade/downgrade must not be inferred from the numeric relation alone.

Intermediate numeric versions are never replayed:

```text
T@VS -> T@VT
    = compare EffectiveSchema(T@VS) directly with EffectiveSchema(T@VT)
```

## 2.1 Equal target is a semantic no-op

```text
VT == VS
    -> 204 No Content
    -> no MigrationPlan
    -> no Object UPDATE
    -> no slot DML
    -> no revision increment
    -> no SCHEMA_CHANGE lifecycle
```

The no-op is serially explainable at the coherent current generation observation. No final revision refresh/CAS is added solely to preserve the no-op through response time.

The current exact version may already be DEPRECATED. Equal-target success creates no new binding and therefore does not re-admit PUBLISHED status.

## 2.2 Distinct target is a real new binding

```text
VT != VS
    -> exact SOURCE -> TARGET migration candidate
```

The real migration owns two separate questions:

```text
TARGET admission
    -> does exact T@VT exist and remain PUBLISHED through commit?

SOURCE -> TARGET migrability
    -> can this exact schema pair, and where required this concrete Object state,
       be migrated according to the rules below?
```

SOURCE is an already-current binding and may be PUBLISHED or DEPRECATED. It does not need a new PUBLISHED admission merely because the Object is leaving it.

# 3. Exact schema comparison and semantic identity

The immutable planner compares:

```text
EffectiveSchema(SOURCE)
vs
EffectiveSchema(TARGET)
```

It does not derive runtime migration behavior from:

```text
numeric version order
version adjacency
intermediate versions
local declarations alone
name equality alone
current defaults
```

Property continuity:

```text
PropertySemanticKey
    = (declaring_template_id, property_name)
```

Component-slot continuity:

```text
SlotSemanticKey
    = (declaring_template_id, slot_name)
```

The same effective name under a different declaring lineage is semantic replacement, not continuity.

Differences caused by different exact parent-version pins are classified solely from the resolved SOURCE/TARGET effective schemas; declaration/inheritance provenance is not a separate runtime migration class.

# 4. Immutable reusable MigrationPlan

For one exact pair:

```text
(template_id, source_version, target_version)
```

certified SOURCE/TARGET semantics are immutable. Therefore:

```text
MigrationPlan(T, VS, VT)
    = f(EffectiveSchema(T@VS), EffectiveSchema(T@VT))
```

is immutable and Object-independent.

Conceptual cache:

```text
ObjectTemplateMigrationPlanCache[(T, VS, VT)]
```

A READY plan may contain compiled immutable rules for:

```text
property semantic continuity/replacement
requiredness/add/remove
SCALAR/LIST transformation
conditional LIST -> SCALAR cardinality rule
TARGET exact-DTV validation/canonicalization
TARGET migration_default behavior
component semantic continuity/replacement
slot ADD/REMOVE/widening/position changes
categorically unsupported component target relations
current object_component_slots delta
```

It must not contain one Object's mutable:

```text
properties
canonical_name
ownership membership
revision
current TARGET lifecycle status
```

# 5. MigrationPlan cache resolution

Normal execution consumes the same READY-plan path whether the plan was already cached or became READY during the request.

```text
HIT
    -> consume plan

MISS
    -> make required immutable semantic inputs READY
    -> compile/cache plan
    -> consume plan
```

Required immutable inputs are bounded by semantic class:

```text
SOURCE/TARGET certified exact effective ObjectTemplate closures
exact DataTypeVersion semantics referenced by SOURCE union TARGET
stable ObjectTemplate lineage ancestry required for component-target relation
```

Cold-loading rules:

```text
load only missing immutable entries
bulk homogeneous misses
no per-property DTV query
no per-slot ancestry query
no recursive inheritance reconstruction fallback
no one-off raw-DB planner path
```

Current cold upper-bound direction:

```text
missing SOURCE/TARGET exact closures
    -> at most 1 bounded bulk semantic-loader statement

missing exact DTV semantics
    -> at most 1 bounded bulk semantic-loader statement

missing stable ancestry sources
    -> at most 1 bounded bulk semantic-loader statement
```

Thus cold preparation adds `0..3` bounded semantic-loader classes, independent in round-trip count from inheritance depth and effective-member count. Payload naturally scales with returned semantics.

For certified PUBLISHED/DEPRECATED exact versions, unexpectedly missing/incomplete immutable materialization or referenced exact DTV state is an internal invariant failure. Runtime does not substitute default/latest/another exact version and does not fall back to recursive reconstruction.

# 6. Property migration matrix

Target properties are built **from TARGET semantic properties**. The migration is not a textual JSON-key patch program.

For each TARGET semantic property, preparation selects exactly one of:

```text
preserved/transformed SOURCE semantic information
canonical TARGET migration_default
absence
```

SOURCE-only semantic properties are not selected into the target state.

## 6.1 Add/remove

```text
ADD optional
    -> absent

ADD required
    -> canonical TARGET migration_default

REMOVE optional/required
    -> SOURCE semantic value omitted from TARGET state
```

Removed data is not archived or copied to an extras bucket.

## 6.2 Requiredness

```text
optional -> required
    SOURCE value present
        -> preserve information
        -> apply all simultaneous TARGET transformations/validation
        -> incompatibility blocks this Object migration
        -> never replace existing incompatible information with migration_default

    SOURCE value absent
        -> canonical TARGET migration_default

required -> optional
    -> preserve existing information
    -> apply all simultaneous TARGET transformations/validation
    -> incompatibility blocks this Object migration
    -> never drop merely because TARGET permits absence
```

`migration_default` fills absence only; it is never remediation for incompatible existing information.

## 6.3 SCALAR -> LIST

```text
SOURCE value present x
    -> [x]
    -> complete TARGET validation/canonicalization

SOURCE optional value absent
    -> absent unless independent TARGET requiredness supplies migration_default
```

## 6.4 Conditional lossless LIST -> SCALAR

A continuous LIST property may migrate to SCALAR only when the concrete Object transformation preserves all information.

```text
SOURCE value absent
    -> TARGET absent
       unless independent TARGET requiredness supplies canonical migration_default

SOURCE value = [x]
    -> TARGET candidate x
    -> complete TARGET exact-DTV validation/canonicalization

SOURCE value contains more than one item
    -> 409 schema_change_blocked for this Object
```

Cardinality is literal:

```text
[x, x]
    -> two items
    -> not lossless
    -> blocked
```

LIST order and multiplicity are semantic runtime information. SCHEMA_CHANGE never performs:

```text
first-item selection
last-item selection
arbitrary item selection
deduplicate-then-collapse
drop-to-absence because TARGET is optional
migration_default replacement of incompatible existing information
```

## 6.5 Exact DataTypeVersion change

For a continuous semantic property within the same stable `datatype_id` lineage:

```text
existing information
    -> preserve/shape-transform as applicable
    -> validate/canonicalize under TARGET exact DTV

TARGET incompatibility
    -> 409 schema_change_blocked for this Object
```

LIST order is preserved. No cross-DataType-lineage or cross-PrimitiveType conversion is invented by Object migration.

## 6.6 Semantic replacement

Same textual name with different `PropertySemanticKey` means:

```text
REMOVE old semantic property
ADD new semantic property
```

No value carry-forward occurs merely because JSON field names match.

# 7. Component-slot migration matrix

Current component runtime state uses the reviewed `object_component_slots` / `object_components` boundary.

For supported SOURCE -> TARGET slot deltas:

```text
ADD
    -> INSERT current slot row
    -> new semantic slot starts empty

REMOVE
    -> DELETE current slot row
    -> no implicit DETACH
    -> referenced old edge blocks final removal

same SlotSemanticKey + equal target
    -> preserve slot/edges

same SlotSemanticKey + target widening toward ancestor
    -> UPDATE target_template_id
    -> preserve edges
    -> no current-child compatibility revalidation

position-only
    -> no current-slot DML
    -> ownership unchanged

semantic replacement
    -> old semantic identity removed + new semantic identity added/replaced
    -> no implicit rebind/detach+reattach
    -> referenced old edge blocks replacement
    -> new semantic slot starts empty
```

Successful normal SCHEMA_CHANGE does not rewrite `object_components` membership.

## 7.1 Categorically unsupported relations

For one continuous slot:

```text
SOURCE target ancestor
TARGET target descendant
    -> narrowing

SOURCE/TARGET targets unrelated
    -> unrelated relation
```

Both exact-pair relations are categorically non-migrable through normal SCHEMA_CHANGE:

```text
narrowing  -> 422 semantic_validation_failed
unrelated  -> 422 semantic_validation_failed
```

Current children never rescue the pair:

```text
zero children
all current children happen to satisfy narrower TARGET
```

are irrelevant to migration admission.

Operational consequence:

```text
0 current child reads
0 per-child compatibility checks
0 membership freshness/protection for component-target admission
```

The immutable MigrationPlan is sufficient to reject the pair.

## 7.2 REMOVE/replacement blocker authority

Current membership matters only at the final relational slot boundary for REMOVE/semantic replacement.

With the reviewed edge -> current semantic-slot dependency:

```text
DETACH removes last old edge first
    -> slot removal/replacement may proceed

old edge still references slot at final transition
    -> slot DELETE/key change cannot commit
    -> 409 schema_change_blocked
```

No preparatory ownership snapshot, child list, blocker count or child-specific diagnostic read is required.

# 8. One-generation preparation path

Each attempt begins with one coherent current intrinsic Object generation read.

Required Object projection:

```text
template_id = T
template_version = VS
properties
revision = R
```

`object_id` is already the path target. `canonical_name` is not required by SCHEMA_CHANGE semantics/lifecycle. Current ownership membership is not part of normal preparation.

The same STEP 1 may also observe requested distinct TARGET existence/current status so that obviously unusable targets can be rejected before semantic preparation **without adding a standalone preliminary TARGET round trip**.

Conceptual flow:

```text
STEP 1 — one authoritative current-generation statement
    Object generation T@VS + properties + revision R
    optionally requested TARGET header/existence/status in same bounded statement

    Object absent
        -> 404 resource_not_found

    VT == VS
        -> 204 semantic no-op

    VT != VS + TARGET absent
        -> 422 referenced_resource_not_found

    VT != VS + TARGET DRAFT/DEPRECATED
        -> 409 dependency_not_admissible

STEP 2 — worker/application semantic preparation
    obtain/build READY MigrationPlan(T, VS, VT)
    reject categorically unsupported component pair
    apply plan to current properties
    derive complete canonical target_properties
    derive actual changed-property lifecycle delta
    retain immutable/current-slot delta
    build PreparedSchemaChange(expected_revision=R)

STEP 3 — short real-migration UoW
    final protected TARGET PUBLISHED admission
    expected_revision freshness
    relational slot arbitration/maintenance
    atomic Object + revision + slots + lifecycle persistence
```

Normal preparation reads no:

```text
child Objects
object_components membership
Relationship state
lifecycle state
current object_component_slots for semantic reconstruction
```

## 8.1 Conservative semantic failures

A semantic failure derived from coherent generation `R` may return immediately without a final revision refresh solely to discover whether a concurrent later mutation changed the answer.

Examples:

```text
multi-item LIST -> SCALAR
current property value incompatible with TARGET exact DTV
categorically unsupported component target relation
```

These paths commit no stale state. The response is serially explainable at the generation observed.

Canonical principle:

```text
expected-revision CAS is required for writes
not for no-op or semantic failure paths that persist nothing
```

# 9. PreparedSchemaChange

Conceptually:

```text
PreparedSchemaChange
    object_id
    template_id
    source_version
    target_version
    expected_revision
    target_properties
    component_slot_delta | MigrationPlan reference
    lifecycle binding transition
    lifecycle changed-property delta
```

It is mechanically applicable once final mutable admissions succeed. Expensive schema comparison, property migration and TARGET value validation are not repeated simply because the final UoW begins.

# 10. Final TARGET admission and short UoW

A real distinct TARGET is a lifecycle-sensitive new binding.

Final success requires exact TARGET:

```text
same template_id
exact requested target_version
current status == PUBLISHED
```

protected through the binding commit by a SHARE-equivalent semantic hold or another architecture-proven mechanism.

The final short UoW owns:

```text
A. protect/re-admit TARGET PUBLISHED through commit

B. require current Object revision == expected_revision R

C. apply current object_component_slots delta subject to DB referential arbitration

D. atomically commit:
       objects.template_version := VT
       objects.properties       := complete target_properties
       objects.revision         := R + 1
       complete current slot delta
       exactly one SCHEMA_CHANGE lifecycle event

E. leave object_components membership unchanged
```

No cache fill, MigrationPlan compilation, property transformation, TARGET value validation, child scan or lifecycle semantic reconstruction belongs inside the final protected path.

Exact SQL/lock/statement fusion remains architecture work.

# 11. Intrinsic freshness and retry

`objects.revision` is the only intrinsic-row freshness token.

```text
candidate prepared from generation R

current revision == R
    -> exact intrinsic generation used for preparation is still current

current revision != R
    -> stale attempt
    -> no Object mutation
    -> no slot mutation
    -> no lifecycle
    -> bounded fresh retry from STEP 1
```

No canonical-JSON/SHA fingerprint or second binding-specific freshness mechanism is retained.

## 11.1 Retry with unchanged SOURCE

```text
fresh SOURCE == previous SOURCE
    -> existing READY MigrationPlan(T, SOURCE, TARGET) reusable
    -> reapply to fresh properties
    -> recompute concrete migration outcome and lifecycle delta
```

## 11.2 Retry with changed SOURCE

```text
fresh SOURCE != previous SOURCE
    -> old exact-pair plan not applicable
    -> resolve/build MigrationPlan(T, fresh_SOURCE, requested_TARGET)
    -> reprepare from fresh properties
```

## 11.3 Retry reaches requested TARGET

```text
fresh source_version == requested target_version
    -> 204 semantic no-op
    -> no new mutation/revision/lifecycle
```

## 11.4 Retry exhaustion

Retry is bounded. Exact count/backoff is architecture work.

If the internal policy cannot stabilize one intrinsic generation:

```text
-> 500 internal_error
```

There is no public route-specific `409 concurrent_modification` or `schema_change_blocked/concurrent_object_change` for stale revision contention.

Only stale `expected_revision` is an automatic intrinsic retry trigger. TARGET absence/inadmissibility, semantic migration failure, slot blocker and persistence defects retain their own normal classifications.

# 12. Failure semantics and precedence

Public failure families:

```text
400 invalid_request
404 resource_not_found
422 referenced_resource_not_found
422 semantic_validation_failed
409 dependency_not_admissible
409 schema_change_blocked
500 internal_error
```

Normal precedence:

```text
1. malformed/static request carrier
    -> 400 invalid_request

2. current Object absent on authoritative generation read/retry
    -> 404 resource_not_found

3. target_version == current source_version
    -> 204 semantic no-op

4. distinct exact TARGET absent
    -> 422 referenced_resource_not_found
       resource_type = object_template_version
       id = template_id
       version = target_version

5. distinct exact TARGET exists but is DRAFT/DEPRECATED
    -> 409 dependency_not_admissible

6. immutable SOURCE -> TARGET migration relation categorically unsupported
    -> 422 semantic_validation_failed
    -> bounded violation identifies the unsupported schema-change rule/member

7. supported migration pair blocked by concrete current Object property state
    -> 409 schema_change_blocked
    -> blocker_type = property
    -> bounded semantic property identity/name detail

8. final TARGET re-admission
    TARGET became DRAFT/DEPRECATED
        -> 409 dependency_not_admissible

    TARGET absent
        -> 422 referenced_resource_not_found
        -> not a revision retry trigger

9. expected_revision stale
    -> internal bounded retry from STEP 1

10. final slot REMOVE/replacement blocked by current edge reference
    -> 409 schema_change_blocked
    -> blocker_type = component_slot_in_use
    -> bounded slot semantic identity detail
    -> no blocker count/child-id diagnostic query required

11. bounded revision retry exhausted
    -> 500 internal_error

12. unexpected persistence/cache/materialization/invariant failure
    -> 500 internal_error
```

A TARGET observation made during STEP 1 is only an early failure filter. Successful real migration still depends on final protected PUBLISHED admission.

No diagnostic-only DB read is introduced merely to enrich a failure.

# 13. SCHEMA_CHANGE lifecycle

A successful real `SOURCE != TARGET` migration appends exactly one:

```text
kind = SCHEMA_CHANGE
```

Equal-target no-op, semantic failure, blocked migration and rolled-back attempts emit no SCHEMA_CHANGE event.

The event follows the general operation-owned lifecycle principle and does **not** persist full intrinsic Object before/after snapshots.

Canonical semantic payload:

```text
SCHEMA_CHANGE event
    object_id = O

    binding transition
        template_id = T
        source_version = VS
        target_version = VT

    changed runtime properties only
        PropertySemanticKey
            declaring_template_id
            property_name

        before
            canonical value | ABSENT

        after
            canonical value | ABSENT
```

The binding transition is always present for a real migration, even when no runtime property value changes:

```text
T@4 -> T@5
property_changes = []
```

is still a real historical SCHEMA_CHANGE.

Property deltas record actual semantic value transitions only. Unchanged property values are omitted.

Examples:

```text
ADD required via migration_default
    ABSENT -> canonical default

REMOVE present property
    canonical value -> ABSENT

SCALAR -> LIST
    x -> [x]

LIST -> SCALAR
    [x] -> x

DTV change that changes canonical representation
    old canonical -> new canonical
```

For semantic replacement, identical textual names do not merge identities. Example:

```text
(Device, hostname): "srv01" -> ABSENT
(Server, hostname): ABSENT -> "unknown"
```

rather than a false single-property rename/value change.

`ABSENT` is distinct from JSON null; null remains invalid runtime property state.

Lifecycle does not duplicate:

```text
canonical_name
revision
full properties before/after
unchanged properties
object_component_slots rows
components/ownership membership
Relationships
template display/status/default/description metadata
effective-schema snapshots
```

The slot delta is derived current-state materialization of the exact binding transition and is not copied into lifecycle. Ownership membership is unchanged by successful SCHEMA_CHANGE and ownership history remains owned by ATTACH/DETACH events.

Lifecycle binding + changed-property delta is derived during normal application-side MigrationPlan application; no second full-property-map pass or extra DB statement is required solely to build history.

Object binding/properties/revision, current slot materialization and the lifecycle event commit atomically.

# 14. Concurrency outcomes

## Intrinsic writers

```text
SCHEMA_CHANGE x RENAME
SCHEMA_CHANGE x DATA_CHANGE
SCHEMA_CHANGE x SCHEMA_CHANGE
```

share the universal revision protocol. One committed intrinsic writer advances revision; a candidate based on the prior generation becomes stale and retries from fresh current state.

No lost intrinsic transition or stale full-properties overwrite is allowed.

## DELETE

```text
SCHEMA_CHANGE commits first
    -> DELETE may remove the resulting generation

DELETE commits first
    -> fresh SCHEMA_CHANGE retry observes Object absence
    -> 404
```

No mutation-after-delete or resurrection is permitted.

## ATTACH/DETACH

For preserved/equal/widened slots, membership changes do not invalidate an intrinsic property candidate merely because membership changed.

For REMOVE/replacement:

```text
ATTACH old slot commits first
    -> referenced slot cannot be removed/key-changed
    -> SCHEMA_CHANGE blocked

SCHEMA_CHANGE slot removal/replacement commits first
    -> later old-slot ATTACH cannot satisfy current semantic-slot FK

DETACH first
    -> may remove the final relational blocker
```

No parent Object revision bump or generic parent-lock rendezvous is required solely for slot continuity.

# 15. Cost profile

## 15.1 Equal-target no-op

```text
1 authoritative Object generation statement
0 MigrationPlan work
0 semantic-loader work
0 final UoW
0 UPDATE
0 slot DML
0 lifecycle
0 revision increment
```

## 15.2 Warm real migration

With `MigrationPlan(T, VS, VT)` READY:

```text
1 preparation statement
    -> current Object generation
    -> optional distinct TARGET early existence/status observation in same statement

0 semantic-loader statements

application/worker CPU
    -> apply MigrationPlan
    -> construct complete target_properties
    -> derive actual changed-property lifecycle delta
    -> retain slot delta

1 bounded short final UoW + COMMIT
    -> final TARGET admission
    -> expected_revision freshness
    -> set-based slot maintenance / FK arbitration
    -> Object binding + full properties + revision + lifecycle persistence
```

Discovery deliberately does not freeze the physical statement count inside the final UoW. Architecture may safely fuse/decompose DML/protection while preserving the semantic contract. The UoW statement count must remain bounded independently of schema member count and child count.

## 15.3 Cold preparation

Cold semantic work adds at most:

```text
0..1 exact closure bulk load
0..1 exact DTV bulk load
0..1 stable ancestry bulk load
```

No N+1 query growth is allowed.

## 15.4 Application complexity

Let:

```text
P = effective property count involved in target-oriented candidate construction
V = size of current/target property values processed
D = component-slot delta size
```

Application semantic/candidate work is bounded by:

```text
O(P + V + D)
```

It does not scale with:

```text
current child count
ownership depth
Relationship count
lifecycle-event count
ObjectTemplate inheritance depth
```

LIST -> SCALAR needs no extra DB read because current list state is already in the full property map.

Slot maintenance must be set-based/bulk; M4 does not accept one PostgreSQL statement per slot as the intended architecture direction.

## 15.5 Full property replacement trade-off

SCHEMA_CHANGE intentionally reads the full current property map and writes the full canonical TARGET map:

```text
PostgreSQL -> application
    full current properties

application/domain
    MigrationPlan application
    TARGET canonicalization/validation
    lifecycle property delta

application -> PostgreSQL
    complete target properties
```

This is appropriate because schema migration may affect the whole property contract. PostgreSQL remains current-state/CAS/referential/atomicity authority; application/domain code owns migration semantics.

Architecture must measure realistic:

```text
JSONB payload size
network transfer
Python decode/encode/CPU
PostgreSQL CPU
TOAST/WAL amplification
p50/p95/p99 latency
same-Object contention/retry amplification
```

before physical freeze.

# 16. Architecture handoff

SCHEMA_CHANGE route semantics are full-sweep complete. Deferred to architecture-wide realization only:

```text
exact SQL / SQLAlchemy carriers
exact STEP-1 root/TARGET join carrier
final-UoW statement fusion/decomposition
exact TARGET/Object/slot lock modes
wait-for ordering and deadlock proof
exact bounded retry count/backoff
slot-delta set-based DML realization
PK/UNIQUE/FK actions/timing/constraint names
constraint/SQLSTATE -> ratified public failure translation
lifecycle JSON/typed persistence carrier
cache layout/eviction/local fill coordination
final physical indexes
EXPLAIN/BUFFERS evidence
JSONB/TOAST/WAL/storage/runtime measurements
```

Architecture must preserve:

```text
exact-target semantics; numeric order never decides migrability
equal-target one-read 204 no-op
one authoritative intrinsic Object generation read per attempt
no standalone preliminary TARGET query
bounded bulk immutable semantic fills; no N+1
application-side target-oriented property migration
conditional lossless LIST -> SCALAR only
categorical component target narrowing/unrelated rejection
no child/ownership semantic-preparation scan
expected_revision as only intrinsic freshness authority
bounded fresh retry; exhaustion -> 500
final protected TARGET PUBLISHED admission for real bindings
set-based current-slot maintenance
edge->slot FK final REMOVE/replacement arbitration
no diagnostic-only queries
atomic binding + properties + revision + current slots + lifecycle
operation-owned lifecycle binding transition + changed-property delta
no ownership membership rewrite on successful normal SCHEMA_CHANGE
```

# 17. Full-sweep closure

The logical `POST /objects/{id}/schema` route is **full-sweep complete** on:

```text
public route/body/success contract
exact-target and equal-target no-op semantics
SOURCE/TARGET semantic identity and exact-pair planning
immutable MigrationPlan/cache boundary
property migration matrix including lossless LIST -> SCALAR
component migration matrix including categorical narrowing/unrelated rejection
single-generation Object preparation
TARGET early/final admission responsibilities
universal revision CAS + bounded retry/reprepare
slot FK arbitration and no child-preparation scan
public failure taxonomy/precedence
operation-owned lifecycle payload
concurrency outcomes
no-op/warm/cold cost character
architecture handoff
```

Older SCHEMA_CHANGE/fingerprint micro-WIPs are superseded wherever they conflict with this owner. Non-superseded semantic/cache/concurrency/cost findings have been absorbed here. After reference cleanup they may be deleted; Git history remains the historical reasoning record.
