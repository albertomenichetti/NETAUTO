# M4 WIP — Object SCHEMA_CHANGE consolidated discovery

**Status:** SCHEMA_CHANGE OWNER / EXACT-TARGET + MIGRATION MATRIX + EXECUTION/RETRY + FAILURE SEMANTICS REVALIDATED / LIFECYCLE ACTIVE REVALIDATION / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This document is the consolidated working owner for detailed M4 `Object.SCHEMA_CHANGE` discovery.

Public route shape and Object-family navigation are owned by [`object.md`](object.md). Cross-operation current component persistence is owned by [`object-components-persistence.md`](object-components-persistence.md). Cross-operation intrinsic Object generation/freshness is owned by [`object-revision.md`](object-revision.md).

Everything under `wip/` remains non-normative and does not authorize implementation.

The lossless comparison pass against the current `object-schema-change-*` WIPs is complete. Subsequent top-down revalidation has superseded the older assumptions that Object schema migration is ordered by numeric version, that current ownership membership belongs in normal semantic preparation, that an intrinsic aggregate fingerprint is needed for stale-success protection, and that continuing intrinsic contention is a public `409` business conflict. Version numbers identify exact versions and creation/allocation order only; SCHEMA_CHANGE owns exact SOURCE -> TARGET migrability, while `objects.revision` owns intrinsic-generation freshness.

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
TARGET admission
slot-delta maintenance
bounded retry
failure semantics and precedence
SCHEMA_CHANGE lifecycle
architecture handoff
```

## Retained vs superseded findings

```text
RETAIN
    exact SOURCE/TARGET effective-schema comparison
    semantic member identity
    revalidated property migration matrix
    revalidated component migration matrix
    immutable reusable MigrationPlan
    READY-cache execution model
    current TARGET PUBLISHED admission for real new bindings
    PreparedSchemaChange pattern
    bounded stale-success protection principle
    intrinsic lifecycle responsibility pending focused payload revalidation

RATIFIED EXECUTION/RETRY REVALIDATION
    one coherent intrinsic Object generation read per attempt
    application-side candidate preparation from generation R
    expected_revision = R as the only intrinsic-row freshness token
    semantic failure may return without a revision refresh
    stale expected_revision triggers a complete fresh bounded retry
    fresh retry reuses/rebuilds MigrationPlan according to fresh SOURCE identity
    retry observing SOURCE == TARGET returns 204 semantic no-op
    retry exhaustion maps to 500 internal_error

RATIFIED FAILURE REVALIDATION
    early TARGET existence/status observation may be folded into STEP 1
        -> no standalone preliminary TARGET round trip
    equal-target 204 no-op does not re-admit TARGET PUBLISHED status
    distinct TARGET absent -> 422 referenced_resource_not_found
    distinct TARGET DRAFT/DEPRECATED -> 409 dependency_not_admissible
    immutable unsupported migration pair -> 422 semantic_validation_failed
    supported migration blocked by concrete Object property state
        -> 409 schema_change_blocked
    final slot REMOVE/replacement FK blocker
        -> 409 schema_change_blocked with bounded semantic-slot detail
        -> no child/count diagnostic read required
    stale expected_revision is internal retry control flow only
    final TARGET absence is classified normally, not converted into revision retry
    retry exhaustion -> 500 internal_error

SUPERSEDE / REOPEN
    numeric-forward-only command semantics
    target_version > current_version as migration admission
    target_version <= current_version as automatic semantic failure
    standalone preliminary TARGET admission query
    separate lightweight binding read followed by a second Object preparation read
    outgoing ownership edges in normal semantic preparation/fingerprint
    preparatory edge snapshot as REMOVE/replacement blocker authority
    ATTACH/DETACH parent-lock rendezvous solely for slot continuity
    mandatory post-lock Object+edge reread justified by unprotected edges
    intrinsic SHA/fingerprint as current freshness authority
    fixed two-attempt fingerprint retry policy
    retry-exhaustion 409 schema_change_blocked / concurrent_object_change
    TARGET disappearance as a fingerprint/stale retry trigger
    child-specific diagnostics as a requirement for final slot blockers
    final business write touching only objects + lifecycle
    old route-total warm/full-cold counts 6 / 9
```

# 1. Public command boundary

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

The current exact binding may already be DEPRECATED. Equal-target success does not create a new binding and therefore does not re-admit PUBLISHED status merely to return `204`.

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

Because this is a real new exact binding, TARGET must exist and be PUBLISHED through commit.

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

# 4. Ratified exact-pair migration matrix

## 4.1 Property rules

The current reusable plan has defined runtime behavior for:

```text
ADD optional
ADD required
REMOVE optional
REMOVE required
optional -> required
required -> optional
SCALAR -> LIST
LIST -> SCALAR with concrete lossless-admission rule
exact DataTypeVersion change within the same datatype_id lineage
migration_default change as part of TARGET semantics
position-only change
semantic-identity replacement
```

Those rules apply to exact SOURCE -> TARGET pairs that exhibit the corresponding deltas. Their validity does not depend on the relative numeric version numbers.

The model-plane publication contract remains separate from runtime migrability. A valid published exact version does not imply that every concrete Object can migrate to it from every other exact version.

`LIST -> SCALAR` is intentionally Object-dependent: immutable schema comparison identifies the shape delta, while the concrete current Object value decides whether the transformation can preserve all information.

## 4.2 Component-slot rules

The component matrix is closed for continuous and replacement cases:

```text
ADD
    -> supported

REMOVE
    -> supported
    -> existing edge through removed semantic slot blocks final removal

same semantic slot + equal target
    -> supported

same semantic slot + target widening toward ancestor
    -> supported

same semantic slot + target narrowing toward descendant
    -> categorically unsupported exact-pair migration

same semantic slot + unrelated SOURCE/TARGET targets
    -> categorically unsupported exact-pair migration

position-only change
    -> supported

semantic-identity replacement
    -> REMOVE old + ADD new
    -> existing edge through old semantic slot blocks replacement
```

These are SOURCE -> TARGET delta rules, not numeric-forward rules.

The categorical rejection of narrowing/unrelated relations is a semantic migration rule, not a performance shortcut. A continuous slot that becomes more restrictive or moves to an unrelated lineage does not become an admitted evolution merely because one particular Object's children happen to fit the TARGET today.

Therefore SCHEMA_CHANGE does **not** perform conditional child admission for these exact-pair relations:

```text
no current child read
no child-lineage compatibility sweep
no "all current children happen to fit" success path
no membership-dependent MigrationPlan executability
```

The immutable MigrationPlan can classify the relation and reject the pair before any Object child/membership inspection.

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

## 4.4 Matrix closure consequence

The migration matrix is semantically closed at this level:

```text
properties
    -> concrete rules above, including conditional lossless LIST -> SCALAR

component slots
    -> supported equal/widening/add/remove/replacement/position cases
    -> narrowing/unrelated categorically unsupported
```

This preserves an intrinsic-only Object preparation boundary for normal semantic candidate construction:

```text
property migrability may depend on current Object.properties
component-pair support does not depend on current children
```

Current ownership membership remains relevant only at the final relational slot boundary for REMOVE/semantic replacement blockers, not for deciding whether a narrowed/unrelated target relation is semantically acceptable.

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
conditional LIST -> SCALAR cardinality rule
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

For `LIST -> SCALAR`, the plan contains the immutable transformation/admission rule but not the concrete cardinality outcome. That outcome is selected when the plan is applied to the current Object generation.

For component target narrowing/unrelated relation, the plan can contain an immutable non-executable/rejection classification. No current child state is needed to reach that result.

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

# 7. Folded early TARGET observation and final TARGET authority

The old standalone preliminary TARGET query is removed. The route may still avoid expensive semantic preparation for an obviously unusable distinct target by **folding requested TARGET existence/status into the same STEP-1 PostgreSQL statement that reads the current Object generation**.

Logical STEP-1 information is therefore:

```text
Object root/current generation
    existence
    template_id = T
    template_version = VS
    properties
    revision = R

requested exact TARGET T@VT
    existence
    current status
```

The exact SQL/join/root-preserving carrier is architecture work. The semantic requirement is one authoritative Object-generation round trip, not a second preliminary admission statement.

Evaluation order after that coherent observation is:

```text
Object absent
    -> 404 resource_not_found

VT == VS
    -> 204 semantic no-op
    -> TARGET status is not re-admitted

VT != VS + TARGET absent
    -> 422 referenced_resource_not_found

VT != VS + TARGET DRAFT/DEPRECATED
    -> 409 dependency_not_admissible

VT != VS + TARGET PUBLISHED
    -> continue immutable semantic preparation
```

The early PUBLISHED observation is only a cost-saving current-state observation. It is **not** success authority. A real new binding must pass final protected TARGET admission inside the short mutation UoW.

Cached TARGET semantics/MigrationPlan may remain semantically valid if TARGET later becomes DEPRECATED. Cache presence never proves current new-binding admissibility.

# 8. Property migration semantics retained and revalidated

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

## 8.7 Ratified conditional LIST -> SCALAR

A continuous semantic property may change from LIST in SOURCE to SCALAR in TARGET. SCHEMA_CHANGE admits this shape change only when it can preserve the complete concrete Object information.

Canonical rule for the current semantic SOURCE value:

```text
SOURCE value absent
    -> TARGET remains absent
       unless independent TARGET requiredness supplies
       the canonical TARGET migration_default

SOURCE value = [x]
    -> TARGET candidate scalar = x
    -> validate/canonicalize x under the complete TARGET exact-DTV semantics

SOURCE value contains more than one item
    -> migration not admissible for this Object
    -> no arbitrary collapse
```

The exact cardinality condition is literal:

```text
len(current_list) == 1
```

Therefore:

```text
[x, x]
    -> still two items
    -> not lossless as LIST -> SCALAR
```

LIST order and multiplicity are information in the current runtime model; duplicate values are allowed unless independently forbidden. SCHEMA_CHANGE must not deduplicate merely to make the conversion succeed.

The route never performs:

```text
first-item selection
last-item selection
arbitrary item choice
deduplication then collapse
drop-to-absence because TARGET is optional
migration_default replacement for incompatible existing information
```

The transformation is only one stage of the complete target-oriented rule. Simultaneous TARGET changes still apply. In particular:

```text
[x]
    -> x
    -> complete TARGET exact-DTV validation/canonicalization
```

If `x` is incompatible with TARGET constraints, the migration fails even though the list cardinality was one.

This decision deliberately separates:

```text
schema-pair classification
    -> immutable plan knows LIST -> SCALAR rule

concrete Object migrability
    -> current value cardinality + TARGET value validity
```

No additional PostgreSQL statement is introduced solely for LIST -> SCALAR admission because SCHEMA_CHANGE already needs the current property map to construct the complete TARGET candidate.

# 9. Component-slot migration after current-slot materialization

For supported slot deltas:

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

## 9.3 Ratified narrowing/unrelated rejection

For one continuous semantic slot, an exact SOURCE/TARGET pair may classify as:

```text
SOURCE target ancestor
TARGET target descendant
    -> narrowing

SOURCE/TARGET targets unrelated
    -> unrelated relation
```

Both are categorically non-migrable through normal Object.SCHEMA_CHANGE:

```text
narrowing
    -> reject migration pair

unrelated
    -> reject migration pair
```

This classification is independent of current membership. SCHEMA_CHANGE must not inspect current children to rescue the pair:

```text
all current children compatible with narrower TARGET
    != migration admission

zero current children
    != migration admission
```

The rule preserves the distinction between semantic continuity/evolution of the slot contract and incidental compatibility of one current Object state.

Operational consequence:

```text
MigrationPlan relation classification
    -> sufficient to reject narrowing/unrelated pair

0 current child reads
0 per-child compatibility checks
0 membership freshness/protection introduced for this admission
```

# 10. Ratified Object-generation preparation boundary

Each attempt begins with **one coherent current intrinsic Object generation statement**, which may also carry the requested TARGET existence/status observation described in section 7.

The path `object_id` is already known from the request. The intrinsic generation projection needs:

```text
template_id
template_version = VS
properties
revision = R
```

It does not need `canonical_name` merely to decide or execute SCHEMA_CHANGE, and it does not read current ownership membership.

Conceptual attempt sequence:

```text
STEP 1 — current generation + folded TARGET observation
    read T, VS, properties, revision=R
    observe requested exact TARGET existence/status in same DB statement

    Object absent
        -> 404 resource_not_found

    target_version == VS
        -> 204 semantic no-op
        -> no TARGET re-admission
        -> no MigrationPlan
        -> no revision refresh

    distinct TARGET absent
        -> 422 referenced_resource_not_found

    distinct TARGET DRAFT/DEPRECATED
        -> 409 dependency_not_admissible

STEP 2 — immutable semantic preparation
    SOURCE = T@VS
    TARGET = T@VT

    obtain/build READY MigrationPlan(T, VS, VT)

    categorically unsupported component relation
        -> 422 semantic_validation_failed
        -> no child/membership read

    otherwise apply MigrationPlan to properties from generation R
        -> property add/remove/requiredness rules
        -> SCALAR <-> LIST transformations
        -> exact TARGET DTV validation/canonicalization
        -> conditional LIST -> SCALAR cardinality admission
        -> complete target_properties
        -> component_slot_delta

    concrete current-property incompatibility
        -> 409 schema_change_blocked

    build PreparedSchemaChange(expected_revision=R)

STEP 3 — real migration UoW only
    final protected TARGET admission
    + expected_revision freshness
    + relational slot arbitration
    + atomic Object/slot/lifecycle transition
```

There is no separate lightweight binding read followed by a second intrinsic snapshot. The first authoritative Object generation already contains the exact SOURCE identity and properties needed for concrete preparation.

Normal preparation reads no:

```text
current child Objects
object_components membership
current object_component_slots for semantic reconstruction
Relationship state
lifecycle state
```

The slot delta comes from immutable SOURCE/TARGET semantics. Current ownership affects only final relational REMOVE/replacement arbitration through the edge -> slot dependency.

## 10.1 Semantic failure from generation R

A semantic migration failure or concrete current-state blocker proved from one coherent current generation may return immediately without an additional revision read solely to see whether concurrent state later changed the answer.

Examples include:

```text
categorically unsupported component target relation
    -> 422 semantic_validation_failed

LIST -> SCALAR with current multi-item list
existing property value incompatible with TARGET exact DTV
    -> 409 schema_change_blocked
```

A later concurrent intrinsic mutation may make a new caller attempt succeed, but the current outcome remains serially explainable at generation R and commits no stale state.

Canonical rule:

```text
expected-revision CAS is required for writes
not for conservative semantic failures/blockers that persist nothing
```

This mirrors the already-ratified DATA_CHANGE stale-failure boundary.

# 11. PreparedSchemaChange

Current conceptual candidate:

```text
PreparedSchemaChange
    object_id

    template_id
    source_version
    target_version

    expected_revision

    target_properties

    component_slot_delta
        or immutable MigrationPlan reference

    lifecycle material
        exact shape pending focused lifecycle revalidation
```

It should be mechanically applicable once final mutable protections/admissions succeed. Expensive schema comparison, property transformation and TARGET value validation are not repeated merely because the mutation UoW begins.

Categorically unsupported component relations and concrete property migration blockers never produce an executable PreparedSchemaChange.

# 12. Intrinsic Object freshness — revision is the only intrinsic authority

Older SCHEMA_CHANGE WIPs used a deterministic intrinsic Object fingerprint over intrinsic state and, in earlier variants, outgoing ownership membership.

That historical mechanism is no longer current authority.

[`object-revision.md`](object-revision.md) owns the universal rule:

```text
prepare from intrinsic generation R
final intrinsic mutation commits only if current revision == R
stale revision -> no mutation/lifecycle -> bounded retry/reprepare
successful intrinsic mutation -> revision := R + 1 atomically
```

A successful `revision == R` check proves that the exact binding and complete intrinsic properties used for preparation still belong to the current Object generation. No second binding fingerprint, canonical JSON encoding or SHA comparison is required for the same intrinsic interval.

Revision proves freshness only for the intrinsic `objects` row. It does not replace relational admission/protection for current component-slot/ownership facts outside that row.

Historical SHA/canonical-JSON fingerprint details remain source evidence only and should be removed during final SCHEMA_CHANGE lossless cleanup.

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

Ratified final outcomes:

```text
TARGET exists + PUBLISHED
    -> may proceed while protected

TARGET exists + DRAFT/DEPRECATED
    -> 409 dependency_not_admissible

TARGET absent
    -> 422 referenced_resource_not_found
    -> resource_type = object_template_version
```

The equal-target no-op never creates a new binding and therefore does not re-admit current PUBLISHED status merely to return `204`.

Final TARGET disappearance is not an intrinsic-generation retry trigger. If final protected admission observes absence, the route returns the normal referenced-target classification and performs no Object/slot/lifecycle mutation. No diagnostic query is added solely to reinterpret that absence as another failure class.

The final lookup must semantically distinguish existing-but-inadmissible TARGET from absent TARGET; exact textual SQL/lock mode/order is architecture work.

# 14. Ratified short mutation-UoW responsibilities

For a real SOURCE != TARGET migration, the short final UoW owns:

```text
A. protect current TARGET PUBLISHED admission through commit

B. verify expected_revision = R against the current intrinsic Object generation

C. apply the prepared current-slot delta subject to relational FK arbitration

D. on fresh/admissible state, atomically commit:
       Object template_version := target_version
       Object properties       := target_properties
       Object revision         := R + 1
       current object_component_slots delta
       exactly one SCHEMA_CHANGE lifecycle event

E. keep object_components membership unchanged for supported successful deltas,
   while referenced old semantic slots may block REMOVE/replacement
```

No model-plane cache fill, MigrationPlan compilation, property transformation, TARGET value validation or lifecycle semantic reconstruction belongs inside the final protected write path.

If expected revision is stale:

```text
no Object mutation
no slot mutation
no lifecycle event
```

The attempt is discarded and handled by the bounded retry protocol below.

If a current edge prevents a slot REMOVE/semantic replacement, the entire transaction is rolled back and classified as `409 schema_change_blocked`; no partial Object/slot/lifecycle state may commit.

Architecture decides only the physical realization:

```text
exact expected-revision SQL / row protection
TARGET/Object/slot lock and wait ordering
slot-delta statement decomposition/fusion
final FK timing/actions and failure translation
```

Final invariants that realization must preserve:

```text
prepared candidate can never overwrite a newer intrinsic generation
Object binding/properties/revision + current slot set + lifecycle become visible atomically
no SCHEMA_CHANGE lifecycle commits without its owning state transition
no partial slot delta commits when a blocker rejects the migration
```

# 15. ATTACH / DETACH interaction

For supported slot cases:

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

Narrowing/unrelated component relations never enter this concurrency path because they are rejected from immutable plan classification before child/membership admission is considered.

# 16. Ratified bounded intrinsic-generation retry

The automatic retry trigger for SCHEMA_CHANGE intrinsic preparation is exactly the universal stale-generation condition:

```text
expected_revision = R
current revision != R
```

A stale attempt commits nothing and starts a complete fresh attempt from STEP 1.

The retry is **bounded**, but discovery does not freeze the exact retry count or backoff policy. Those are architecture realization choices. The semantic protocol is:

```text
stale expected_revision
    -> no Object/slot/lifecycle mutation
    -> fresh current intrinsic generation read
    -> rederive every mutable conclusion from that generation
```

Immutable work may be reused only when its identities still apply.

## 16.1 Fresh retry with unchanged SOURCE

```text
fresh template_id/source_version == previous SOURCE
    -> existing READY MigrationPlan(T, SOURCE, TARGET) remains reusable
    -> apply it to fresh properties
    -> recompute concrete property migrability
       including LIST -> SCALAR cardinality
    -> build a fresh candidate with fresh expected_revision
```

## 16.2 Fresh retry with changed SOURCE

```text
fresh SOURCE != previous SOURCE
```

The old exact-pair plan is not the plan for the new current state. The retry resolves/builds:

```text
MigrationPlan(T, fresh_source_version, requested_target_version)
```

and reruns semantic candidate preparation against the fresh properties.

The retry may therefore produce a different normal outcome, including a semantic migration failure or current-state blocker that was not true on the first attempt.

## 16.3 Fresh retry finds TARGET already current

If another SCHEMA_CHANGE committed the requested exact target while this request was preparing:

```text
fresh source_version == requested target_version
    -> 204 semantic no-op
    -> no new mutation
    -> no revision increment
    -> no SCHEMA_CHANGE lifecycle event
```

This is the convergent exact-target semantics applied to the fresh generation.

## 16.4 Retry exhaustion

Inability to stabilize one current intrinsic Object generation within the bounded internal retry policy is not a stable business/domain conflict.

Canonical public mapping:

```text
bounded retry exhausted
    -> 500 internal_error
```

There is no route-specific normal:

```text
409 concurrent_modification
409 schema_change_blocked / blocker_type=concurrent_object_change
```

The stale expected-revision result itself is internal control flow and is never exposed directly.

This aligns SCHEMA_CHANGE with the universal intrinsic-generation policy already used by RENAME and DATA_CHANGE rather than preserving a fingerprint-era exception.

## 16.5 Failures that do not consume retry solely by themselves

The intrinsic retry budget exists to handle stale prepared generations. Other outcomes are classified by their own route semantics rather than being converted into stale retries merely because they occur during the same request:

```text
semantic migration failure
TARGET absent/inadmissible
slot REMOVE/replacement blocker
unexpected persistence/invariant failure
```

A fresh retry caused by a preceding stale revision may naturally encounter one of those outcomes, but they are not independent retry triggers.

# 17. Ratified failure semantics and precedence

## 17.1 Public failure set

The current bounded public set is:

```text
400 invalid_request

404 resource_not_found

422 referenced_resource_not_found
422 semantic_validation_failed

409 dependency_not_admissible
409 schema_change_blocked

500 internal_error
```

There is no public concurrent-modification error for stale revision itself.

## 17.2 Static/request failures

Malformed request carriers are:

```text
400 invalid_request
```

This includes malformed path/body carriers, absent/invalid `target_version`, unsupported body/query fields and other transport-shape failures owned by the request model.

## 17.3 Path Object absence

```text
Object absent on authoritative STEP 1 or a fresh retry
    -> 404 resource_not_found
```

The Object is the URI/path target and therefore owns `404` semantics.

## 17.4 Referenced TARGET absence

A distinct requested exact ObjectTemplateVersion is a referenced command operand, not the path resource.

Therefore:

```text
TARGET absent on folded early observation
    -> 422 referenced_resource_not_found

TARGET absent on final protected admission
    -> 422 referenced_resource_not_found
```

Bounded detail identifies:

```text
resource_type = object_template_version
template_id
target_version
```

No additional query is required solely to enrich that detail.

## 17.5 TARGET lifecycle inadmissibility

For a real SOURCE != TARGET migration:

```text
TARGET exists but status is DRAFT or DEPRECATED
    -> 409 dependency_not_admissible
```

This applies both to the folded early observation and to final protected admission. Early observation is a cost filter; final protected admission remains success authority.

## 17.6 Immutable migration-pair rejection

A migration relation that is categorically unsupported by the SCHEMA_CHANGE contract independently of the current Object value is:

```text
422 semantic_validation_failed
```

Current cases include:

```text
continuous component target narrowing
continuous component SOURCE/TARGET targets unrelated
```

The bounded violation should identify the semantic member/rule needed for callers to understand the rejected migration pair. Exact JSON detail carrier naming remains part of the later shared failure DTO realization; no child inspection is performed.

## 17.7 Concrete Object-state property blockers

When the SOURCE/TARGET rule is supported but the current Object value cannot migrate under that rule, the command is currently blocked by Object state:

```text
409 schema_change_blocked
```

Current examples include:

```text
LIST -> SCALAR with more than one current item
existing continuous property value fails TARGET exact-DTV constraints
other supported property transformation cannot preserve/validate current information
```

Conceptual bounded detail:

```text
object_id
target_version
blocker_type = property
member_name / semantic member identity
```

The route does not use `migration_default`, optional TARGET absence or destructive transformation as remediation for incompatible existing information.

## 17.8 Current component-slot blockers

REMOVE and semantic replacement are semantically supported pair deltas, but a current ownership edge may prevent the final slot DELETE/key change through the edge -> slot FK dependency.

That outcome is:

```text
409 schema_change_blocked
```

Conceptual bounded detail identifies only the blocked semantic slot, for example:

```text
blocker_type = component_slot_in_use
slot_declaring_template_id
slot_name
```

The contract does **not** require:

```text
child_object_id
all child ids
exact blocker count
constraint name
```

and no PostgreSQL statement may be added solely to discover/enrich those diagnostics.

## 17.9 Intrinsic stale generation and retry exhaustion

```text
expected_revision stale
    -> internal retry control flow
    -> no public failure yet

bounded retry exhausted
    -> 500 internal_error
```

Stale revision never maps directly to `409 schema_change_blocked`.

## 17.10 Internal invariant/persistence failures

```text
required persisted immutable dependency unexpectedly missing/corrupt
certified effective materialization unexpectedly invalid/incomplete
unexpected persistence/lifecycle/integrity failure
    -> 500 internal_error
```

Normal hot-path logic must not add diagnostic consistency scans solely to discover such corruption.

## 17.11 Normal-path precedence

Canonical normal-path precedence is:

```text
1. static request invalid
       -> 400 invalid_request

2. STEP 1 Object absent
       -> 404 resource_not_found

3. target_version == current source_version
       -> 204 semantic no-op
       -> no TARGET status admission

4. distinct TARGET absent
       -> 422 referenced_resource_not_found

5. distinct TARGET exists but non-PUBLISHED
       -> 409 dependency_not_admissible

6. immutable MigrationPlan relation categorically unsupported
       -> 422 semantic_validation_failed

7. supported migration blocked by concrete current property state
       -> 409 schema_change_blocked

8. prepared real candidate enters final UoW
       final TARGET absent
           -> 422 referenced_resource_not_found

       final TARGET non-PUBLISHED
           -> 409 dependency_not_admissible

       final TARGET PUBLISHED + expected_revision stale
           -> no mutation/lifecycle
           -> bounded fresh retry from STEP 1

       final TARGET PUBLISHED + fresh revision + slot FK blocker
           -> rollback whole attempt
           -> 409 schema_change_blocked

       final TARGET PUBLISHED + fresh revision + slot delta admissible
           -> atomic transition
           -> 204

9. bounded intrinsic retry exhaustion
       -> 500 internal_error

10. unexpected invariant/persistence failure
       -> 500 internal_error
```

No diagnostic-only read is introduced merely to choose among failures that are already distinguishable from the normal authoritative operations above.

# 18. Lifecycle — pending focused revalidation

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

# 19. Cost interpretation after execution/failure revalidation

The previous totals:

```text
warm first-attempt success = 6 PostgreSQL business statements
full cold first Object     = 9 PostgreSQL business statements
```

are superseded because they assumed:

```text
numeric-forward preclassification
standalone preliminary TARGET lookup
separate lightweight binding read + later Object aggregate read
Object + outgoing-edge preparation snapshot
parent-lock ATTACH/DETACH rendezvous
mandatory fresh Object+edge fingerprint statement
Object+lifecycle-only final mutation
```

Retained cost properties now are:

```text
one authoritative intrinsic Object generation statement per attempt
    may also carry the requested TARGET existence/status observation
MigrationPlan comparison/compilation amortized per worker + exact pair
semantic cold fill bounded and bulk
property migration in application outside the critical section
normal preparation does not scan outgoing edges or children
slot delta adds bounded SCHEMA_CHANGE DML
equal-target no-op stops after STEP 1
LIST -> SCALAR adds no extra PostgreSQL read
component narrowing/unrelated rejection adds no child/ownership read
slot-blocker diagnostics add no diagnostic-only query
stale retry repeats only bounded attempt work and may reuse applicable immutable cache state
```

Warm real-migration route statement count remains an architecture handoff because final TARGET admission, expected-revision write, slot delta and lifecycle may be fused/decomposed in multiple equivalent ways. Discovery does not restore the obsolete 6/9 totals merely to produce a fixed number.

Cold semantic preparation may add at most one bounded bulk load per missing immutable semantic class under the cache rules in section 6.

# 20. Current open points

## Closed in the current full sweep so far

```text
exact-target command semantics
migration matrix
single-generation Object preparation boundary
revision-based stale-success protection
bounded retry/reprepare semantics
retry exhaustion -> 500 internal_error
TARGET absence/lifecycle failure classification
migration-pair vs concrete-state failure distinction
slot blocker bounded failure mapping
route failure precedence
```

## Active next review — SCHEMA_CHANGE lifecycle

The next full-sweep block must close:

```text
complete exact semantic transition owned by SCHEMA_CHANGE
binding context needed in lifecycle history
property before/after representation
whether slot-contract deltas belong in SCHEMA_CHANGE lifecycle payload
what unchanged intrinsic fields must be excluded
```

## Subsequent cost/closure review

After lifecycle semantics, the full sweep still must close the final warm/no-op/cold cost profile and architecture handoff wording before lossless absorption/cleanup.

## Architecture handoff after semantic closure

Architecture still must close:

```text
final PostgreSQL statement decomposition
exact Object expected-revision/row-protection realization
bounded retry count/backoff
TARGET/Object/slot wait-for ordering
deadlock freedom with ATTACH/DETACH/DELETE/intrinsic mutations
exact object_component_slots delta DML/fusion
FK timing/actions
constraint/SQLSTATE -> public failure realization
final physical DDL/indexes
EXPLAIN/BUFFERS evidence
storage/write measurements
```

# 21. Lossless comparison / supersession map

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

LIST -> SCALAR categorically outside normal migration contract
    -> superseded by conditional lossless per-Object admission

conditional current-child compatibility admission for component narrowing/unrelated
    -> explicitly rejected
    -> unsupported relation determined from immutable SOURCE/TARGET semantics

separate initial binding read + second preparation Object read
    -> superseded by one coherent intrinsic generation read per attempt

standalone preliminary TARGET admission statement
    -> superseded by optional folded TARGET observation in STEP 1
    -> final protected TARGET admission remains success authority

TARGET disappearance as stale/fingerprint retry
    -> superseded by normal 422 referenced_resource_not_found classification

preparatory outgoing-edge blocker authority
    -> superseded for REMOVE/replacement by final slot-FK arbitration

child-object/count diagnostic requirement for slot blocker
    -> rejected; bounded semantic-slot detail only

whole Object + outgoing-edge fingerprint
intrinsic canonical-JSON/SHA fingerprint
    -> superseded by `objects.revision` for intrinsic freshness

parent Object lock as mandatory ATTACH/DETACH slot-continuity rendezvous
    -> superseded for supported slot cases

separate post-lock Object+edge fingerprint statement
    -> removed from current protocol

fixed two-total-attempt fingerprint retry
    -> superseded by bounded retry with exact count/backoff deferred to architecture

retry exhaustion -> 409 schema_change_blocked/concurrent_object_change
    -> superseded by 500 internal_error

Object+lifecycle-only final write
    -> superseded because current slot delta and revision must commit atomically too

old 6/9 route totals
    -> superseded
```

### Historical evidence retained

The legacy source family remains useful for rationale and lossless comparison, but statements inside those files marked `FROZEN` do not override the revalidated owner above. Git history remains the historical record after later cleanup.
