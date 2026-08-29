# M4 WIP — Object SCHEMA_CHANGE consolidated discovery

**Status:** SCHEMA_CHANGE OWNER CONSOLIDATED / SOURCE→TARGET MONOTONICITY POLICY REOPENED / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This document is the consolidated working owner for detailed M4 `Object.SCHEMA_CHANGE` discovery.

Public route shape and Object-family navigation are owned by [`object.md`](object.md). Cross-operation current component persistence is owned by [`object-components-persistence.md`](object-components-persistence.md).

Everything under `wip/` remains non-normative and does not authorize implementation.

The lossless comparison pass against the current `object-schema-change-*` WIPs is complete. It preserved the non-superseded semantic/cache findings, removed old realization assumptions invalidated by `object_component_slots`, and exposed one genuine semantic inconsistency that remains OPEN: numeric forward version order does not necessarily imply semantic monotonicity in the same direction as ObjectTemplate publication history.

Current ownership of this file includes:

```text
forward target-version command semantics
SOURCE/TARGET exact-effective-schema comparison
semantic member identity
delta classification
immutable reusable MigrationPlan
bounded immutable cache fills
property migration rules
component-slot migration rules
optimistic intrinsic Object preparation/fingerprint
final TARGET admission
slot-delta maintenance
bounded retry
SCHEMA_CHANGE lifecycle
architecture handoff
```

## Retained vs superseded findings

```text
RETAIN
    exact SOURCE/TARGET effective-schema comparison
    semantic member identity
    property migration rules
    immutable reusable MigrationPlan
    READY-cache execution model
    final current TARGET PUBLISHED admission
    PreparedSchemaChange pattern
    bounded stale-success protection
    intrinsic lifecycle snapshots

SUPERSEDE / REOPEN
    standalone preliminary TARGET admission query
    outgoing ownership edges in normal optimistic fingerprint
    preparatory edge snapshot as REMOVE/replacement blocker authority
    ATTACH/DETACH parent-lock rendezvous solely for slot continuity
    mandatory post-lock Object+edge reread justified by unprotected edges
    final business write touching only objects + lifecycle
    old route-total warm/full-cold counts 6 / 9

NEWLY REOPENED BY LOSSLESS COMPARISON
    assumption that numeric-forward Object migration can never expose
    LIST -> SCALAR or component-target narrowing/unrelated relation
```

# 1. Public command boundary

```http
POST /api/v1/core/objects/{object_id}/schema
Content-Type: application/json
```

Request:

```json
{
  "target_version": 5
}
```

The command keeps the stable `template_id` and changes only the exact ObjectTemplateVersion binding.

Success:

```http
204 No Content
```

The resulting state is read through:

```text
GET /objects/{id}
GET /objects/{id}/schema
```

# 2. Forward target-version command semantics

The route is a forward numeric migration command, not a generic version setter.

For current version `VS` and requested `VT`:

```text
VT > VS
    -> forward candidate

VT == VS
    -> 422 semantic_validation_failed
    -> NOT an idempotent no-op

VT < VS
    -> 422 semantic_validation_failed
    -> downgrade unsupported
```

Intermediate versions are not executed:

```text
v3 -> v7
    = compare effective(v3) directly with effective(v7)
    != execute v3->v4->v5->v6->v7
```

Important distinction after the comparison pass:

```text
numeric-forward
    != automatically semantic-monotone-forward
```

That distinction is detailed in section 4.

# 3. Exact effective-schema comparison and semantic identity

For:

```text
SOURCE = (template_id, source_version)
TARGET = (template_id, target_version)
```

the planner compares:

```text
EffectiveSchema(SOURCE)
vs
EffectiveSchema(TARGET)
```

It does not derive migration behavior from:

```text
version adjacency
intermediate version traversal
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

Same effective name under a different declaring lineage is semantic replacement, not continuity.

Effective deltas caused by different exact parent-version pins are classified from the resolved SOURCE and TARGET effective schemas exactly like equivalent locally-originated deltas. Declaration provenance is not a separate runtime migration class.

# 4. Delta taxonomy and publication-order revalidation

## 4.1 Property rules already defined for SCHEMA_CHANGE

The current reusable plan has defined runtime behavior for:

```text
ADD optional
ADD required
REMOVE optional
REMOVE required
optional -> required
required -> optional
SCALAR -> LIST
exact DataTypeVersion change within the same datatype_id lineage
migration_default change as part of TARGET semantics
position-only change
semantic-identity replacement
```

The model-plane historical rule forbids a newly published declaration from changing `datatype_id`, changing PrimitiveType lineage, renaming a historical property, or evolving latest-published LIST state back to SCALAR.

## 4.2 Component rules already defined for SCHEMA_CHANGE

The current plan has defined runtime behavior for:

```text
ADD
REMOVE
same semantic slot + equal target
same semantic slot + target widening toward ancestor
position-only change
semantic-identity replacement
```

The model-plane historical rule allows component target evolution only by widening from the latest immutable declaration; it forbids a newly published declaration from narrowing or moving to an unrelated target relative to that publication-history predecessor.

## 4.3 Critical finding: publication order can differ from numeric version order

The comparison pass revalidated an older component-discovery finding against current ObjectTemplate behavior.

`CREATE_NEXT` may clone any eligible PUBLISHED/DEPRECATED source, not only the highest version, while allocating the new version as `max(existing)+1`. Therefore multiple DRAFT versions can coexist and be published later in a different order from their numeric version numbers.

ObjectTemplate historical validation compares a candidate declaration with the **latest published declaration**, not with every numerically lower/higher version.

Consequently, this sequence is possible in principle:

```text
v3 DRAFT exists
v4 is published first
v3 is later revised and published
```

If `v4` has:

```text
property mode = SCALAR
```

then later publication of `v3` as:

```text
property mode = LIST
```

is a valid publication-history widening (`SCALAR -> LIST`). But an Object migration:

```text
v3 -> v4
```

is numerically forward and semantically:

```text
LIST -> SCALAR
```

Likewise for a component slot:

```text
v4 published target = Server
v3 later published target = Device
Device is ancestor of Server
```

The later `v3` publication is a history-valid widening from `Server` to `Device`, while Object migration:

```text
v3 -> v4
```

is a target narrowing from `Device` to `Server`.

Therefore the former blanket statements:

```text
forward Object migration can never contain LIST -> SCALAR
forward Object migration can never contain component target narrowing/unrelated change
```

are not justified by the current model-plane publication contract.

## 4.4 OPEN source→target policy

This comparison intentionally does **not** invent the missing policy.

For an exact numeric-forward pair whose resolved SOURCE/TARGET schemas contain a reverse-monotonic delta, M4 still has to decide explicitly what `Object.SCHEMA_CHANGE` does.

At minimum the open cases are:

```text
continuous property:
    SOURCE LIST -> TARGET SCALAR

continuous component slot:
    SOURCE target ancestor -> TARGET target descendant
    SOURCE/TARGET targets unrelated
```

Candidate policy families to evaluate later include:

```text
A. reject such migration pairs categorically
   because normal Object SCHEMA_CHANGE supports only information-preserving
   monotone transformations

B. define additional controlled per-Object migration/admission semantics
   where safe
```

No choice is made here.

This matters operationally: if conditional component narrowing were ever allowed, current child compatibility would become mutable admission state again and the intrinsic-only preparation/fingerprint boundary would need to be revalidated. Until this semantic point is closed, claims of "no child compatibility read" apply only to pairs classified as equal-target/widening or otherwise already-covered slot deltas.

# 5. Immutable reusable MigrationPlan

For one exact pair:

```text
(template_id, source_version, target_version)
```

SOURCE and TARGET certified semantics are immutable. Therefore:

```text
MigrationPlan(source,target)
    = f(EffectiveSchema(source), EffectiveSchema(target))
```

is immutable and Object-independent.

Conceptual cache:

```text
ObjectTemplateMigrationPlanCache[
    (template_id, source_version, target_version)
]
```

The plan may contain/point to compiled immutable rules for:

```text
property semantic continuity/replacement
add/remove/requiredness behavior
shape transformation
TARGET exact-DTV validation/canonicalization
TARGET migration_default behavior
component semantic continuity/replacement
slot ADD/REMOVE
actual SOURCE->TARGET target-lineage relation
position-only classification
current object_component_slots delta
```

It must not contain one Object's mutable:

```text
properties
canonical_name
ownership membership
current TARGET lifecycle status
```

The newly reopened reverse-monotonic cases are plan classification outcomes whose runtime policy remains OPEN; they must not be silently normalized into widening.

# 6. MigrationPlan cache-resolution model

Normal execution consumes a READY plan regardless of whether it was already cached or became READY during the request.

```text
MigrationPlan HIT
    -> consume plan

MigrationPlan MISS
    -> make every required immutable input READY
    -> compile plan in memory
    -> cache plan
    -> consume the same plan path
```

Required semantic inputs:

```text
SOURCE exact effective ObjectTemplate closure
TARGET exact effective ObjectTemplate closure
all exact DataTypeVersion semantics referenced by SOURCE ∪ TARGET
stable ObjectTemplate lineage ancestry needed for target-relation classification
```

General cold-fill rules:

```text
load only missing immutable entries
bulk homogeneous misses
no N+1 semantic loading
no inheritance reconstruction fallback
no one-off planner path consuming uncached raw DB structures
```

## 6.1 Exact ObjectTemplate closure cold fill

The closure consumer uses certified immutable materializations:

```text
object_template_effective_properties
object_template_effective_components
```

anchored by:

```text
object_template_versions
```

When SOURCE and TARGET closures are both missing, the loader should retrieve the requested exact versions together through one bounded loader/query boundary where practical. Round-trip growth must be independent of inheritance depth and effective-member count; payload naturally grows with the returned effective schema.

This SCHEMA_CHANGE consumer does **not** require an exact-version ancestry materialization. Exact parent-chain interpretation was already paid when the effective schemas were certified/materialized.

The exact-version anchor is required to distinguish:

```text
existing exact version + zero effective members
    -> valid empty closure

absent exact version
    -> missing exact version
```

For a certified PUBLISHED/DEPRECATED exact version, an unexpectedly missing/incomplete effective materialization is an internal invariant failure. Runtime must not fall back to recursive inheritance reconstruction.

The DB result fills the immutable closure cache; MigrationPlan compilation resumes from READY cache state.

## 6.2 Exact DataTypeVersion cold fill

Required exact pins are:

```text
DISTINCT(
    SOURCE effective-property pins
    UNION
    TARGET effective-property pins
)
```

Subtract already READY entries before DB access.

```text
0 missing
    -> 0 DB statements

1..N missing
    -> one bounded bulk exact-DTV load for the missing set
```

The same bulk load should include stable DataType lineage payload required by runtime semantics (including stable base/primitive type) rather than issuing a second lookup per DTV.

This is semantic payload loading, not current lifecycle/default admission. PUBLISHED -> DEPRECATED does not invalidate exact immutable DataType semantics referenced by a certified ObjectTemplate closure.

If a certified exact DTV pin unexpectedly has no persisted row, that is an internal reference/invariant failure. The loader must never substitute:

```text
default_version
latest version
another PUBLISHED version
```

## 6.3 Stable ObjectTemplate ancestry fill

Component target relation requires stable lineage ancestry such as:

```text
EthernetInterface descendant-of NetworkInterface ?
```

Durable source:

```text
object_template_ancestry(
    descendant_template_id,
    ancestor_template_id,
    depth
)
```

with reflexive lineage facts.

No exact-version ancestry is required.

```text
all required ancestry READY
    -> 0 DB statements

one or more missing ancestry sources
    -> one bounded bulk ancestry load
```

No query-per-slot/target/pair path is allowed.

## 6.4 Amortization

Once:

```text
MigrationPlanCache[(T, source, target)] = READY
```

subsequent Objects on that worker reuse all immutable comparison/compilation work for the same pair.

Cold semantic cost is therefore primarily per:

```text
(worker, template_id, source_version, target_version)
```

not per Object, subject to cache eviction/process restart.

The old route-total `9`-statement full-cold number is not retained because the mutable/UoW realization has changed. What remains retained is the bounded semantic fill: at most one bulk load per missing semantic class in the current candidate.

# 7. Standalone preliminary TARGET admission is removed

An earlier candidate issued an unconditional unlocked exact TARGET existence/status read before semantic preparation. That standalone round trip is superseded.

Current sequence:

```text
initial Object binding
-> numeric forwardness check
-> obtain/build immutable MigrationPlan
-> prepare concrete Object candidate
-> enter mutation UoW
-> final protected exact TARGET admission is current lifecycle authority
```

A cold TARGET closure load may incidentally discover absent/non-certifiable target state as part of the same bounded semantic loader; no extra query is issued solely as preliminary lifecycle admission.

Cached TARGET semantics/MigrationPlan may remain semantically valid if TARGET later becomes DEPRECATED. Cache presence never proves current new-binding admissibility.

# 8. Property migration semantics retained

The target property map is built **from TARGET semantic properties**, not by replaying JSON-key edits over SOURCE state.

For each TARGET semantic property the plan/application yields:

```text
preserved/transformed SOURCE information
canonical TARGET migration_default
absence
```

SOURCE-only semantic properties are omitted.

## 8.1 Add/remove

```text
ADD optional
    -> absent

ADD required
    -> canonical TARGET migration_default

REMOVE optional/required
    -> SOURCE value is not selected into target state
```

Removed information is not archived or moved to an extras bucket.

## 8.2 Requiredness

```text
optional -> required
    value present
        -> preserve information
        -> apply all TARGET transformations/validation
        -> incompatibility = migration failure
        -> never fallback to migration_default

    value absent
        -> canonical TARGET migration_default

required -> optional
    -> preserve existing information
    -> apply TARGET transformations/validation
    -> incompatibility = migration failure
    -> never drop merely because TARGET permits absence
```

`migration_default` fills absence only; it is never remediation for incompatible existing information.

## 8.3 SCALAR -> LIST

```text
SOURCE value present
    x -> [x]
    -> validate/canonicalize under complete TARGET semantics

SOURCE optional value absent
    -> remains absent unless TARGET requiredness supplies its canonical default
```

## 8.4 Exact DataTypeVersion change

For continuous semantic identity and the same stable `datatype_id`:

```text
existing value
    -> preserve
    -> validate/canonicalize under TARGET exact DTV

TARGET incompatible
    -> migration failure

LIST value
    -> preserve item order
    -> validate all elements
```

No cross-DataType-lineage or cross-PrimitiveType conversion is performed.

## 8.5 Combined deltas

One continuous semantic property compiles one target-oriented rule rather than an artificial script of independent mutations.

Logical application:

```text
1. establish semantic continuity
2. inspect SOURCE presence
3. preserve existing information when present
4. apply supported information-preserving shape transformation
5. validate/canonicalize under complete TARGET exact-DTV semantics
6. materialize canonical sparse TARGET state
```

## 8.6 Same name, different semantic key

```text
SOURCE (Device, hostname)
TARGET (Server, hostname)
```

is:

```text
REMOVE old semantic property
ADD new semantic property
```

The old value is not carried forward because the JSON name happens to match.

## 8.7 LIST -> SCALAR now explicitly OPEN for numeric-forward pair

The existing migration semantics intentionally do not define information-losing LIST -> SCALAR conversion.

The comparison pass proves this delta can nevertheless appear between two numerically forward exact versions because publication order may differ from version order.

Therefore:

```text
LIST -> SCALAR observed in SOURCE/TARGET pair
    -> current SCHEMA_CHANGE policy OPEN
```

No silent first-item selection, list collapse, default substitution or other conversion is inferred.

# 9. Component-slot migration after current-slot materialization

For already-covered slot deltas:

```text
ADD
    -> INSERT current object_component_slots row
    -> new semantic slot starts empty

REMOVE
    -> DELETE current slot row
    -> no implicit DETACH
    -> referenced old edge is final blocker

same semantic slot + equal target
    -> preserve slot/edges

same semantic slot + target widening
    -> UPDATE target_template_id
    -> preserve edges
    -> no per-child runtime compatibility revalidation

semantic replacement
    -> old semantic identity removed/replaced
    -> key-changing declaring-lineage transition + target as required
    -> no implicit rebind
    -> referenced old edge is final blocker
    -> new semantic slot starts empty

position-only
    -> no current-slot DML
    -> ownership unchanged
```

Normal successful migration does not rewrite `object_components` membership.

## 9.1 REMOVE / semantic replacement blocker authority

The earlier preparatory outgoing-edge blocker scan is superseded.

With the edge-to-current-slot relational dependency:

```text
DETACH removes last old edge before final slot transition
    -> REMOVE/replacement may succeed

old edge still references semantic slot at transition
    -> slot DELETE/key change cannot commit
    -> SCHEMA_CHANGE rolls back/fails
```

Thus REMOVE/replacement admission occurs at the final relational slot boundary rather than from a potentially stale preparatory edge snapshot.

## 9.2 Widening

When the actual exact pair is classified:

```text
SOURCE target = descendant-or-self
TARGET target = ancestor
```

all SOURCE-admitted children remain TARGET-admissible. No current child read is required for that delta.

`target_template_id` is not part of the semantic FK key, so a target widening need not conflict solely because ATTACH references the slot identity.

## 9.3 Narrowing/unrelated exact-pair relation is OPEN

Because publication order can differ from numeric order, an exact forward pair may classify as:

```text
SOURCE target ancestor
TARGET target descendant
```

or potentially another unsupported relation even though each exact version was valid when published.

Current policy is OPEN.

Until closed, this document does not claim that every numeric-forward schema change can preserve membership without child compatibility admission.

If M4 chooses categorical rejection, no current-child admission is needed. If M4 chooses conditional admission, the mutable preparation/concurrency design must be reopened because the current edge FK protects slot existence/semantic identity, not child compatibility with a narrowed `target_template_id`.

# 10. Optimistic Object preparation boundary

For currently covered migration pairs, the preferred Object-specific mutable preparation is intrinsic-only:

```text
id
canonical_name
template_id
template_version
properties
```

Current per-attempt sequence:

```text
1. minimal Object binding read
       -> existence, template_id, source_version

2. require target_version > source_version

3. obtain/build READY immutable MigrationPlan

4. read current intrinsic Object snapshot S
       id, canonical_name, template_id, template_version, properties

5. require S binding == source identity used by the plan

6. compute expected intrinsic fingerprint F(S)

7. apply supported property rules
       -> target_properties

8. carry supported current-slot delta from MigrationPlan

9. build PreparedSchemaChange
```

No normal current child read, ownership-edge scan, effective-schema reread or ancestry reread occurs in this covered path.

### Binding drift before protected UoW

If the second intrinsic read no longer matches the binding used to select the plan:

```text
binding differs
    -> fail current request conservatively
    -> do not use fingerprint for stale plan
    -> do not automatically re-plan/restart inside this attempt
```

This is distinct from the protected fingerprint retry described later. A new caller request naturally resolves a plan from the new source binding.

If M4 later chooses conditional support for reverse-monotonic component target migration, this intrinsic-only boundary must be revalidated.

# 11. PreparedSchemaChange

Current conceptual candidate:

```text
PreparedSchemaChange
    object_id
    canonical_name

    template_id
    source_version
    target_version

    expected_intrinsic_fingerprint

    target_properties

    component_slot_delta
        or immutable MigrationPlan reference

    lifecycle_before
    lifecycle_after
```

It should be mechanically applicable once final mutable protections/admissions succeed. Expensive schema comparison, property transformation and TARGET value validation are not repeated merely because the mutation UoW begins.

A plan that contains an OPEN reverse-monotonic delta must not produce an executable PreparedSchemaChange until the policy for that delta is deliberately closed.

# 12. Intrinsic Object fingerprint

Current preferred logical scope:

```text
id
canonical_name
template_id
template_version
properties
```

Excluded for currently covered pairs:

```text
outgoing object_components membership
child canonical names
public components projection
Relationship state
lifecycle history
```

Why membership can be excluded for the covered component cases:

```text
preserved/equal/widened membership
    -> does not invalidate property migration candidate

REMOVE/replacement
    -> final slot FK arbitrates old references
```

The retained deterministic encoding candidate is:

```text
canonical intrinsic Object logical representation
-> canonical JSON
-> UTF-8
-> SHA-256
-> raw 32-byte digest
```

The same canonical encoder/hash is used at preparation and protected comparison. The earlier ownership-array portion of the old fingerprint representation is superseded for this route candidate.

Current discovery does not require PostgreSQL-specific hashing, `pgcrypto`, a persisted Object revision/hash column, Python `repr`, pickle or implementation-specific binary serialization merely to realize this fingerprint.

If reverse-monotonic component migration is later conditionally admitted based on current membership, this fingerprint scope may need to expand or a different relational admission/protection mechanism must be proven.

# 13. Final TARGET admission

The exact TARGET ObjectTemplateVersion is a lifecycle-sensitive **new binding**.

A successful mutation must require current exact TARGET:

```text
same template_id
exact target_version
status == PUBLISHED
```

and protect that admission through binding/slot/lifecycle commit with a SHARE-equivalent semantic hold or another architecture-proven mechanism.

SOURCE is an already-existing exact binding and may be PUBLISHED or DEPRECATED; it does not require a new PUBLISHED admission merely because the Object is leaving it.

Retained outcomes:

```text
TARGET exists + PUBLISHED
    -> may proceed while protected

TARGET exists + DRAFT/DEPRECATED
    -> 409 dependency_not_admissible
```

Unexpected exact TARGET absence at final protected admission remains an OPEN lifetime/failure-classification question. It must not silently consume the Object fingerprint retry budget; automatic retry is reserved for protected Object fingerprint mismatch.

The final lookup must semantically distinguish existing-but-inadmissible TARGET from absent TARGET; exact textual SQL/lock mode/order is architecture work.

# 14. Short mutation-UoW logical responsibilities

The old fixed four-statement realization is not retained as current authority.

Current logical requirements:

```text
A. protect current TARGET PUBLISHED admission through commit

B. protect/revalidate current intrinsic Object generation

C. compare protected intrinsic state with expected fingerprint

D. on match, atomically commit:
       Object target template_version
       canonical target properties
       current object_component_slots delta
       exactly one SCHEMA_CHANGE lifecycle event

E. keep object_components membership unchanged for covered successful deltas,
   while referenced old semantic slots may block REMOVE/replacement
```

The Object remains the intrinsic mutation concurrency owner. Parent Object locking solely to serialize ATTACH/DETACH for slot continuity is superseded by the narrower slot-FK boundary for the covered component cases.

Architecture decides:

```text
exact Object row protection/lock mode
whether protection + intrinsic fingerprint read can be fused safely
TARGET/Object/slot lock ordering
slot-delta statement decomposition/fusion
final FK behavior/failure translation
```

## Final-write invariants retained

Even though old Q4 is reopened, two logical properties remain useful:

```text
final Object transition must apply to the expected Object/source binding
no SCHEMA_CHANGE lifecycle event may commit unless the owning Object/slot transition commits
```

Defensive expected-source predicates may realize the first property cheaply; exact SQL remains architecture work.

No model-plane cache fill, MigrationPlan compilation, property transformation, TARGET value validation or lifecycle reconstruction belongs inside the final protected write path.

# 15. ATTACH / DETACH interaction

For currently covered slot cases:

```text
ATTACH old semantic slot commits first
    -> REMOVE/replacement cannot remove/change referenced slot key

REMOVE/replacement commits first
    -> later old-slot ATTACH cannot satisfy current semantic-slot FK

target widening
    -> non-key target update
    -> old-admitted child remains valid

DETACH first
    -> may remove last REMOVE/replacement blocker

ordinary ATTACH/DETACH on preserved slot
    -> need not invalidate intrinsic property candidate merely because membership changed
```

If conditional component narrowing is later supported, these guarantees are insufficient by themselves because child compatibility becomes relevant mutable state.

# 16. Bounded optimistic retry

Automatic internal retry trigger:

```text
protected_intrinsic_fingerprint
    !=
PreparedSchemaChange.expected_intrinsic_fingerprint
```

Budget:

```text
2 total attempts
= 1 initial attempt + 1 fresh retry
```

Attempt 1 protected mismatch:

```text
no Object/slot/lifecycle DML
rollback
start one complete fresh attempt
```

The new attempt re-discovers mutable source state and may resolve a different MigrationPlan if the source binding changed. Immutable cache entries are reusable only when their identities still apply.

Attempt 2 protected mismatch:

```text
rollback
no third attempt
HTTP 409 STATE_CONFLICT
code = schema_change_blocked
blocker_type = concurrent_object_change
```

No other result consumes this retry budget.

In particular:

```text
preparation-time binding drift
non-forward target
unsupported/open SOURCE->TARGET delta
property migration failure
slot REMOVE/replacement FK blocker
TARGET non-PUBLISHED admission
persistence failure
```

are not fingerprint retry triggers.

This distinction is deliberate:

```text
pre-UoW binding mismatch
    -> conservative request failure; no automatic re-plan

protected fingerprint mismatch
    -> one internal full retry
```

# 17. Lifecycle

Exactly one successful real schema migration produces:

```text
kind = SCHEMA_CHANGE
```

Failed/rolled-back migration produces no lifecycle event.

Historical snapshots contain only intrinsic Object state:

```text
id
canonical_name
template_id
template_version
properties
```

They exclude:

```text
components
owner
relationships
effective schema
template display/lifecycle metadata
```

Preparation builds:

```text
lifecycle_before
    -> SOURCE intrinsic snapshot

lifecycle_after
    -> same identity/canonical_name
    -> target_version
    -> target_properties
```

A successful protected intrinsic fingerprint match permits reuse of those prepared snapshots without semantic reconstruction. Object binding/properties, current slot materialization and lifecycle must commit atomically.

# 18. Cost interpretation

The previous totals:

```text
warm first-attempt success = 6 PostgreSQL business statements
full cold first Object     = 9 PostgreSQL business statements
```

are superseded because they assumed:

```text
Object + outgoing-edge preparation snapshot
parent-lock ATTACH/DETACH rendezvous
mandatory fresh Object+edge fingerprint statement
Object+lifecycle-only final mutation
```

Current route-total counts remain OPEN until architecture fixes the intrinsic protection/fingerprint and slot-delta realization.

Retained cost properties:

```text
MigrationPlan comparison/compilation is amortized per worker + exact pair
semantic cold fill is bounded and bulk
property migration happens outside critical section
normal covered preparation no longer scans outgoing edges
slot delta adds bounded SCHEMA_CHANGE DML
```

Qualitative shift for covered deltas:

```text
LESS
    ownership rows transferred/hashed for optimistic generation
    retry coupling to preserved-slot ATTACH/DETACH
    generic ownership lock coupling

MORE
    object_component_slots delta writes
```

Reverse-monotonic policy may change this cost again and must be accounted for after it is closed.

# 19. Current open points

## Discovery semantic blocker found by comparison

Before this SCHEMA_CHANGE owner can be considered route-semantically closed, M4 must explicitly choose behavior for numeric-forward pairs containing reverse-monotonic deltas caused by out-of-order publication:

```text
LIST -> SCALAR
component target narrowing/unrelated relation
```

That choice must state:

```text
admitted vs rejected
failure class/detail when rejected
whether any per-Object data transformation or child compatibility check exists
concurrency consequences if conditional admission uses mutable membership
```

Do not assume publication-history monotonicity implies numeric-version monotonicity.

## Architecture handoff after semantic closure

Architecture still must close:

```text
final PostgreSQL statement decomposition
exact Object protection/lock mode
TARGET/Object/slot wait-for ordering
deadlock freedom with ATTACH/DETACH/DELETE/intrinsic mutations
whether Object protection + fresh intrinsic fingerprint can be fused
exact object_component_slots delta DML/fusion
FK timing/actions
constraint failure -> public error mapping
unexpected final TARGET absence classification
final warm/cold route statement count
final physical DDL/indexes
EXPLAIN/BUFFERS evidence
storage/write measurements
bounded retry verification
```

# 20. Lossless comparison / supersession map

This owner has now been compared against and absorbs the non-superseded findings from the active legacy set, including:

```text
object-schema-change-ancestry-cache-fill.md
object-schema-change-bounded-retry.md
object-schema-change-cache-resolution.md
object-schema-change-component-admission-from-snapshot.md
object-schema-change-component-migration.md
object-schema-change-components-discovery.md
object-schema-change-delta-taxonomy.md
object-schema-change-dtv-cache-fill.md
object-schema-change-dtv-cold-fill.md
object-schema-change-dtv-migration.md
object-schema-change-exact-closure-cold-load.md
object-schema-change-immutable-migration-plan.md
object-schema-change-lifecycle.md
object-schema-change-migration-plan-amortization.md
object-schema-change-preparation-aggregate-read.md
object-schema-change-preparation-properties.md
object-schema-change-preparation-snapshot.md
object-schema-change-prepared-candidate.md
object-schema-change-property-migration.md
object-schema-change-property-rule-composition.md
object-schema-change-protected-fingerprint-read.md
object-schema-change-q3-fingerprint-outcome.md
object-schema-change-q4-final-mutation.md
object-schema-change-remove-preliminary-target-admission.md
object-schema-change-target-admission.md
object-schema-change-target-version-semantics.md
object-schema-change-uow-object-lock.md
object-schema-change-uow-target-admission.md
object-schema-change-uow.md
object-schema-change-warm-cost.md
object-optimistic-preparation-fingerprint.md
object-aggregate-fingerprint-canonical-json.md
object-aggregate-fingerprint-sha256.md
```

### Superseded realization directions

```text
preparatory outgoing-edge blocker authority
    -> superseded for REMOVE/replacement by final slot-FK arbitration

whole Object + outgoing-edge fingerprint
    -> superseded by intrinsic-only preferred scope for currently covered deltas

parent Object lock as mandatory ATTACH/DETACH slot-continuity rendezvous
    -> superseded for covered slot cases

separate post-lock Object+edge Q3 as mandatory statement
    -> old justification removed; realization reopened

Object+lifecycle-only Q4
    -> reopened because current slot delta must commit atomically

standalone preliminary TARGET admission
    -> removed

old 6/9 route totals
    -> superseded
```

### Historical finding restored rather than discarded

`object-schema-change-components-discovery.md` contained the warning that a numeric-forward pair can semantically narrow when versions are published out of numeric order. Later WIPs effectively assumed that this could not occur. The comparison against current ObjectTemplate creation/publication logic shows the warning is still material, so this owner restores it as the explicit OPEN source→target monotonicity policy above.

Older micro-WIPs remain in the tree for now. Cleanup should occur only after this newly exposed semantic point is deliberately resolved and the three consolidated Object owners are made self-consistent; Git history remains the historical record afterward.
