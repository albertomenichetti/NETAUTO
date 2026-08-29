# M4 WIP — Object SCHEMA_CHANGE consolidated discovery

**Status:** SCHEMA_CHANGE OWNER / EXACT-TARGET COMMAND SEMANTICS REVALIDATED / MIGRATION MATRIX ACTIVE REVALIDATION / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This document is the consolidated working owner for detailed M4 `Object.SCHEMA_CHANGE` discovery.

Public route shape and Object-family navigation are owned by [`object.md`](object.md). Cross-operation current component persistence is owned by [`object-components-persistence.md`](object-components-persistence.md). Cross-operation intrinsic Object generation/freshness is owned by [`object-revision.md`](object-revision.md) and takes precedence over older fingerprint-era realization material retained in this file pending its focused execution-path revalidation.

Everything under `wip/` remains non-normative and does not authorize implementation.

The lossless comparison pass against the current `object-schema-change-*` WIPs is complete. Subsequent top-down revalidation has now superseded the older assumption that Object schema migration is ordered by numeric version. Version numbers identify exact versions and creation/allocation order only; SCHEMA_CHANGE owns the separate exact SOURCE -> TARGET migrability question.

Current ownership of this file includes:

```text
exact-target command semantics
SOURCE/TARGET exact-effective-schema comparison
semantic member identity
delta classification
immutable reusable MigrationPlan
bounded immutable cache fills
property migration rules
component-slot migration rules
intrinsic Object preparation/freshness
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
    property migration rules where explicitly defined
    immutable reusable MigrationPlan
    READY-cache execution model
    final current TARGET PUBLISHED admission
    PreparedSchemaChange pattern
    bounded stale-success protection principle
    intrinsic lifecycle responsibility pending focused payload revalidation

SUPERSEDE / REOPEN
    numeric-forward-only command semantics
    target_version > current_version as migration admission
    target_version <= current_version as automatic semantic failure
    standalone preliminary TARGET admission query
    outgoing ownership edges in normal optimistic fingerprint
    preparatory edge snapshot as REMOVE/replacement blocker authority
    ATTACH/DETACH parent-lock rendezvous solely for slot continuity
    mandatory post-lock Object+edge reread justified by unprotected edges
    intrinsic SHA/fingerprint as current freshness authority
        -> object-revision.md now owns intrinsic generation freshness
    final business write touching only objects + lifecycle
    old route-total warm/full-cold counts 6 / 9

ACTIVE MIGRATION-MATRIX REVALIDATION
    exact SOURCE -> TARGET pairs may expose
    LIST -> SCALAR or component-target narrowing/unrelated relation
    regardless of numeric version ordering
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

The command keeps the stable `template_id` and selects one exact ObjectTemplateVersion target inside that lineage.

Success:

```http
204 No Content
```

The resulting state is read through:

```text
GET /objects/{id}
GET /objects/{id}/schema
```

# 2. Ratified exact-target command semantics

SCHEMA_CHANGE is an **exact-target migration command**, not a numeric-forward migration command and not a generic inference from version ordering.

For current exact binding:

```text
SOURCE = T@VS
```

and request:

```text
target_version = VT
TARGET = T@VT
```

canonical interpretation is:

```text
version number
    = exact-version identity
    + creation/allocation order within lineage T

version number
    != semantic evolution order
    != compatibility order
    != migration order
```

Therefore the numeric relation between `VS` and `VT` is not itself an admission predicate.

## 2.1 Equal target is a semantic no-op

```text
VT == VS
    -> 204 No Content
    -> no Object mutation
    -> no revision increment
    -> no SCHEMA_CHANGE lifecycle event
    -> no MigrationPlan required
```

This is convergent assignment to the Object's already-current exact schema binding.

The no-op is linearizable at the coherent current binding observation. A concurrent later intrinsic mutation does not make the response incorrect because this command committed no state transition.

No expected-revision CAS or extra database statement is required solely to preserve the no-op through response time.

## 2.2 Different exact target is a migration candidate

```text
VT != VS
    -> exact SOURCE -> exact TARGET migration candidate
```

This is true whether:

```text
VT > VS
VT < VS
```

The words "upgrade" and "downgrade" must not be inferred from the numeric relation alone.

Migrability is determined by:

```text
exact SOURCE semantics
exact TARGET semantics
concrete Object state where the migration rule requires it
```

and not by version-number ordering.

## 2.3 Intermediate versions are not executed

For any distinct exact endpoints:

```text
T@VS -> T@VT
    = compare EffectiveSchema(T@VS) directly with EffectiveSchema(T@VT)
```

The route does not execute or replay numerically intermediate exact versions.

Example:

```text
v3 -> v7
    = compare effective(v3) directly with effective(v7)
    != execute v3->v4->v5->v6->v7
```

Likewise a numerically lower target is not reached by replaying versions backward.

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
numeric version order
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

# 4. Delta taxonomy and exact-pair migrability revalidation

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

Those rules remain candidates for exact SOURCE -> TARGET pairs that exhibit the corresponding deltas. Their validity does not depend on the relative numeric version numbers.

The model-plane publication contract remains separate from runtime migrability. A valid published exact version does not imply that every concrete Object can migrate to it from every other exact version.

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

Again, these are SOURCE -> TARGET delta rules, not numeric-forward rules.

## 4.3 Why numeric order cannot decide the migration matrix

`CREATE_NEXT` may clone an eligible PUBLISHED/DEPRECATED source while allocating a new monotonically increasing version number, and publication order need not match numeric allocation order.

More generally, the ratified cross-domain version principle already forbids using the numeric relation as genealogy, semantic evolution or migrability order.

Therefore exact pairs can legitimately expose deltas such as:

```text
continuous property:
    SOURCE LIST -> TARGET SCALAR

continuous component slot:
    SOURCE target ancestor -> TARGET target descendant
    SOURCE/TARGET targets unrelated
```

whether the target version number is greater or smaller than the source version number.

The earlier warning about out-of-order publication remains useful evidence, but it is no longer needed as an exception to a forward-only rule: the general rule is simply that exact-pair migrability must be evaluated independently of version-number ordering.

## 4.4 OPEN exact-pair migration policy

The current migration semantics intentionally do not yet define every possible exact SOURCE -> TARGET delta.

At minimum the still-open cases are:

```text
continuous property:
    SOURCE LIST -> TARGET SCALAR

continuous component slot:
    SOURCE target ancestor -> TARGET target descendant
    SOURCE/TARGET targets unrelated
```

Candidate policy families to evaluate in the next review block include:

```text
A. reject such exact migration pairs categorically
   because normal Object SCHEMA_CHANGE supports only the currently defined
   information-preserving transformations

B. define additional controlled per-Object migration/admission semantics
   where safe
```

No choice is made by the exact-target command decision itself.

This matters operationally: if conditional component narrowing were ever allowed, current child compatibility would become mutable admission state again and the preparation/concurrency boundary would need to account for it. Until this semantic point is closed, claims of "no child compatibility read" apply only to exact pairs classified as equal-target/widening or otherwise already-covered slot deltas.

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

Unsupported/open exact-pair deltas are plan classification outcomes whose runtime policy remains OPEN; they must not be silently normalized into a supported widening/transformation.

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

Current high-level sequence after the exact-target revalidation:

```text
initial Object binding
-> target == current ? 204 semantic no-op
-> otherwise identify exact SOURCE/TARGET pair
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

## 8.7 LIST -> SCALAR remains explicitly OPEN

The existing migration semantics intentionally do not define information-losing LIST -> SCALAR conversion.

Under exact-target semantics this is simply one possible SOURCE/TARGET delta, independent of whether the target version number is greater or smaller than the source version number.

Therefore:

```text
LIST -> SCALAR observed in SOURCE/TARGET pair
    -> current SCHEMA_CHANGE migration policy OPEN
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

An exact SOURCE/TARGET pair may classify as:

```text
SOURCE target ancestor
TARGET target descendant
```

or another unsupported relation irrespective of numeric version ordering.

Current policy is OPEN.

If M4 chooses categorical rejection, no current-child admission is needed. If M4 chooses conditional admission, the mutable preparation/concurrency design must be reopened because the current edge FK protects slot existence/semantic identity, not child compatibility with a narrowed `target_template_id`.

# 10. Object-specific preparation boundary — execution details still under focused revalidation

The exact-target command decision does not by itself freeze the final preparation/freshness protocol.

For currently covered migration pairs, the existing candidate keeps Object-specific semantic preparation intrinsic-only:

```text
id
canonical_name
template_id
template_version
properties
```

Current conceptual sequence, pending replacement of fingerprint-era freshness by the ratified universal revision protocol:

```text
1. read current Object binding
       -> existence, template_id, source_version

2. if target_version == source_version
       -> 204 semantic no-op

3. otherwise obtain/build READY immutable MigrationPlan
       for exact SOURCE -> TARGET

4. read/retain the current intrinsic Object generation needed for preparation

5. require prepared SOURCE identity to match that generation

6. apply supported property rules
       -> target_properties

7. carry supported current-slot delta from MigrationPlan

8. build PreparedSchemaChange
```

No normal current child read, ownership-edge scan, effective-schema reread or ancestry reread occurs in this covered path.

### Binding drift before protected UoW

The older source material used a special pre-UoW fingerprint/binding-drift failure. That behavior is **not current authority** after the universal Object revision decision and will be revalidated in the execution/concurrency block.

The required invariant already known is only:

```text
candidate prepared from stale intrinsic Object generation
    -> must not commit stale state/lifecycle
```

Exact retry/reprepare behavior belongs to the upcoming revision-alignment block.

If M4 later chooses conditional support for component narrowing/unrelated target migration, this intrinsic-only boundary must also be revalidated because current membership may become semantic admission input.

# 11. PreparedSchemaChange

Current conceptual candidate:

```text
PreparedSchemaChange
    object_id
    canonical_name

    template_id
    source_version
    target_version

    expected_revision / intrinsic generation identity

    target_properties

    component_slot_delta
        or immutable MigrationPlan reference

    lifecycle material
        exact shape pending focused lifecycle revalidation
```

It should be mechanically applicable once final mutable protections/admissions succeed. Expensive schema comparison, property transformation and TARGET value validation are not repeated merely because the mutation UoW begins.

A plan that contains an OPEN exact-pair delta must not produce an executable PreparedSchemaChange until the policy for that delta is deliberately closed.

# 12. Intrinsic Object freshness — fingerprint source material superseded by revision

Older SCHEMA_CHANGE WIPs used a deterministic intrinsic Object fingerprint over:

```text
id
canonical_name
template_id
template_version
properties
```

That historical mechanism is no longer current authority for intrinsic-row freshness.

[`object-revision.md`](object-revision.md) now owns the universal rule:

```text
prepare from intrinsic generation R
final intrinsic mutation commits only if current revision == R
stale revision -> no mutation/lifecycle -> bounded retry/reprepare
successful intrinsic mutation -> revision := R + 1 atomically
```

Revision proves freshness only for the intrinsic `objects` row. It does not replace relational admission/protection for current component-slot/ownership facts outside that row.

Historical SHA/canonical-JSON fingerprint details remain source evidence only and should be removed during final SCHEMA_CHANGE lossless cleanup once the focused execution block is closed.

# 13. Final TARGET admission

The exact TARGET ObjectTemplateVersion is a lifecycle-sensitive **new binding** whenever TARGET differs from SOURCE.

A successful real migration must require current exact TARGET:

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

The equal-target no-op never creates a new binding and therefore does not re-admit current PUBLISHED status merely to return `204`.

Unexpected exact TARGET absence at final protected admission remains a failure-classification point to close. It must not be confused with intrinsic revision retry control flow.

The final lookup must semantically distinguish existing-but-inadmissible TARGET from absent TARGET; exact textual SQL/lock mode/order is architecture work.

# 14. Short mutation-UoW logical responsibilities

The old fixed four-statement realization is not retained as current authority.

Current logical requirements for a real SOURCE != TARGET migration:

```text
A. protect current TARGET PUBLISHED admission through commit

B. verify expected intrinsic Object revision/generation

C. on fresh generation, atomically commit:
       Object target template_version
       canonical target properties
       revision := expected_revision + 1
       current object_component_slots delta
       exactly one SCHEMA_CHANGE lifecycle event

D. keep object_components membership unchanged for covered successful deltas,
   while referenced old semantic slots may block REMOVE/replacement
```

The Object remains the intrinsic mutation concurrency owner. Parent Object locking solely to serialize ATTACH/DETACH for slot continuity is superseded by the narrower slot-FK boundary for the covered component cases.

Architecture decides:

```text
exact expected-revision SQL/row protection realization
TARGET/Object/slot lock ordering
slot-delta statement decomposition/fusion
final FK behavior/failure translation
```

## Final-write invariants retained

```text
final Object transition must apply to the expected Object/source generation
no SCHEMA_CHANGE lifecycle event may commit unless the owning Object/slot transition commits
```

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

# 16. Bounded intrinsic-generation retry — details still to revalidate

The universal Object revision rule replaces fingerprint mismatch as the intrinsic stale-attempt signal.

Required generic behavior is already fixed cross-operation:

```text
expected_revision = R
current revision != R
    -> no Object/slot/lifecycle mutation for that stale attempt
    -> bounded retry from a fresh Object generation
```

SCHEMA_CHANGE still has to close route-specific details such as:

```text
retry budget/backoff
when a fresh SOURCE binding permits MigrationPlan reuse
when changed SOURCE requires a new exact-pair plan
how a retry that now observes TARGET == current becomes 204 no-op
final retry-exhaustion public mapping
interaction with TARGET admission and slot blockers
```

Older `2 total attempts` / fingerprint-specific `409 schema_change_blocked` material is retained only as source evidence until this block is explicitly revalidated; it is not current authority over [`object-revision.md`](object-revision.md).

# 17. Lifecycle — pending focused revalidation

Exactly one successful real schema migration produces:

```text
kind = SCHEMA_CHANGE
```

Failed/rolled-back migration and equal-target semantic no-op produce no lifecycle event.

Older SCHEMA_CHANGE material proposed complete intrinsic Object before/after snapshots:

```text
id
canonical_name
template_id
template_version
properties
```

The general lifecycle principle now requires the payload to be revalidated as the complete exact semantic transition owned by SCHEMA_CHANGE, not preserved merely for historical uniformity.

Therefore the exact lifecycle payload is **OPEN for the dedicated lifecycle block**. Whatever shape is ratified must commit atomically with Object binding/properties/revision and current slot materialization.

Technical `revision` is not automatically semantic lifecycle payload.

# 18. Cost interpretation

The previous totals:

```text
warm first-attempt success = 6 PostgreSQL business statements
full cold first Object     = 9 PostgreSQL business statements
```

are superseded because they assumed:

```text
numeric-forward preclassification
Object + outgoing-edge preparation snapshot
parent-lock ATTACH/DETACH rendezvous
mandatory fresh Object+edge fingerprint statement
Object+lifecycle-only final mutation
```

Current route-total counts remain OPEN until the expected-revision/slot-delta realization is closed.

Retained cost properties:

```text
MigrationPlan comparison/compilation is amortized per worker + exact pair
semantic cold fill is bounded and bulk
property migration happens outside critical section
normal covered preparation no longer scans outgoing edges
slot delta adds bounded SCHEMA_CHANGE DML
equal-target no-op requires no MigrationPlan or mutation UoW
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

Additional exact-pair migration policies may change this cost and must be accounted for after the migration matrix is closed.

# 19. Current open points

## Active semantic review — exact-pair migration matrix

The exact-target command boundary is now ratified:

```text
target == current
    -> 204 no-op

target != current
    -> evaluate exact SOURCE -> TARGET migrability
    -> numeric version relation is irrelevant to admission
```

Before SCHEMA_CHANGE can be route-semantically closed, M4 must explicitly choose behavior for still-unsupported exact-pair deltas including:

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

## Subsequent execution/lifecycle/failure review

After the migration matrix, the full sweep still must close:

```text
current intrinsic Object generation read/preparation
expected-revision retry/reprepare details
final TARGET absence classification
slot blocker failure mapping
SCHEMA_CHANGE lifecycle payload
route failure precedence
warm/no-op/cold cost targets
```

## Architecture handoff after semantic closure

Architecture still must close:

```text
final PostgreSQL statement decomposition
exact Object expected-revision/row-protection realization
TARGET/Object/slot wait-for ordering
deadlock freedom with ATTACH/DETACH/DELETE/intrinsic mutations
exact object_component_slots delta DML/fusion
FK timing/actions
constraint failure -> public error mapping
final physical DDL/indexes
EXPLAIN/BUFFERS evidence
storage/write measurements
bounded retry verification
```

# 20. Lossless comparison / supersession map

This owner has been compared against and absorbs the non-superseded findings from the legacy set, including:

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

### Superseded semantic/realization directions

```text
forward-only target-version semantics
    -> superseded by exact-target migration semantics
    -> numeric relation carries no migration admission meaning

equal target -> 422
    -> superseded by 204 semantic no-op

preparatory outgoing-edge blocker authority
    -> superseded for REMOVE/replacement by final slot-FK arbitration

whole Object + outgoing-edge fingerprint
    -> superseded by intrinsic revision for Object-row freshness

parent Object lock as mandatory ATTACH/DETACH slot-continuity rendezvous
    -> superseded for covered slot cases

separate post-lock Object+edge fingerprint statement
    -> old justification removed; realization reopened around revision CAS

Object+lifecycle-only final write
    -> reopened because current slot delta and revision must commit atomically

standalone preliminary TARGET admission
    -> removed

old 6/9 route totals
    -> superseded
```

### Historical evidence retained

The legacy component discovery correctly warned that numeric allocation/publication order could expose semantically restrictive SOURCE/TARGET relations. The current reviewed baseline generalizes that finding: numeric version order never encoded migration order in the first place.

Older micro-WIPs remain source material for now. Cleanup should occur only after the active SCHEMA_CHANGE full sweep is complete and the consolidated owners are losslessly self-consistent; Git history remains the historical record afterward.
