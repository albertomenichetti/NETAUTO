# M4 WIP — Object SCHEMA_CHANGE consolidated discovery

**Status:** ACTIVE CONSOLIDATION / CURRENT LOGICAL CANDIDATE RECONCILED / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This document is the consolidated working owner for the detailed M4 `Object.SCHEMA_CHANGE` discovery.

Public route shape and Object-family navigation remain owned by [`object.md`](object.md). The cross-operation runtime component persistence boundary is owned by [`object-components-persistence.md`](object-components-persistence.md).

This file owns the current detailed candidate for:

```text
forward target-version semantics
source/target effective-schema delta taxonomy
immutable reusable MigrationPlan
MigrationPlan/cache resolution
property migration semantics
component-slot migration semantics
optimistic Object preparation
intrinsic concurrency fingerprint
final target admission
slot-delta maintenance
bounded retry
SCHEMA_CHANGE lifecycle
architecture handoff
```

Everything under `wip/` remains non-normative. This file does not authorize implementation.

A major purpose of this consolidation is to separate two classes of earlier findings:

```text
RETAIN
    immutable SOURCE/TARGET delta semantics
    semantic member identity
    property migration rules
    MigrationPlan reuse/cache direction
    forward-only target semantics
    final current target PUBLISHED admission
    prepared-candidate pattern
    bounded intrinsic-state stale-success protection
    intrinsic lifecycle snapshots

REOPEN / SUPERSEDE
    outgoing ownership edges in the optimistic fingerprint
    component blocker admission from preparatory edge snapshot
    ATTACH/DETACH rendezvous through parent Object lock solely for slot continuity
    mandatory post-lock aggregate reread justified by non-locked ownership rows
    final write touching only objects + lifecycle
    old route-total 6-warm / 9-full-cold statement counts
    standalone preliminary target-admission query
```

# 1. Public command boundary

Detailed public surface is summarized in `object.md`:

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

The command changes only the exact ObjectTemplateVersion inside the Object's existing stable ObjectTemplate lineage.

It does not select another `template_id`.

Successful execution returns:

```http
204 No Content
```

There is no response representation; callers read current state through:

```text
GET /objects/{id}
GET /objects/{id}/schema
```

# 2. Forward-only target semantics

`SCHEMA_CHANGE` is a forward migration command, not a generic exact-version setter.

Given current source version `VS` and requested target version `VT`:

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

Canonical semantic rule:

```text
target_version must be greater than current_version
```

A valid request may skip intermediate versions:

```text
Server v3 -> Server v7
```

The migration algorithm does not execute:

```text
v3 -> v4 -> v5 -> v6 -> v7
```

It compares SOURCE exact effective schema directly with TARGET exact effective schema.

# 3. Exact effective-schema comparison and semantic identity

Source and target are:

```text
SOURCE = (template_id, source_version)
TARGET = (template_id, target_version)
```

The planner compares only:

```text
EffectiveSchema(SOURCE)
vs
EffectiveSchema(TARGET)
```

It does not derive runtime rules from:

```text
version adjacency
intermediate-version history
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

Inheritance provenance does not create a special runtime delta class. A delta caused by a different exact parent-version pin is classified from the two complete effective schemas exactly like an equivalent local effective delta.

# 4. Delta taxonomy retained

## 4.1 Property deltas admitted by normal model evolution

MigrationPlan must understand at least:

```text
ADD optional
ADD required
REMOVE optional
REMOVE required
optional -> required
required -> optional
SCALAR -> LIST
exact DataTypeVersion change within same stable datatype_id
migration_default change
position change
semantic-identity replacement
```

Normal evolution does not admit:

```text
LIST -> SCALAR
datatype_id change
PrimitiveType change
property rename
```

Remove/re-add under the same declaring lineage and same name retains the same historical semantic identity; it cannot reset stable DataType lineage or monotonic evolution rules.

## 4.2 Component-slot deltas admitted by normal model evolution

MigrationPlan must understand:

```text
ADD
REMOVE
continuous target widening toward an ancestor lineage
position change
semantic-identity replacement
```

Normal evolution does not admit:

```text
target narrowing toward a descendant
unrelated target-lineage change
slot rename
```

Remove/re-add by the same declaring lineage/name retains historical semantic identity and target-evolution history.

# 5. Immutable reusable MigrationPlan

For one exact migration pair:

```text
(template_id, source_version, target_version)
```

both SOURCE and TARGET semantic schemas are immutable exact snapshots once certified.

Therefore:

```text
MigrationPlan(source,target)
    = f(EffectiveSchema(source), EffectiveSchema(target))
```

is immutable and Object-independent.

Conceptual cache key:

```text
ObjectTemplateMigrationPlanCache[
    (template_id, source_version, target_version)
]
```

The plan may precompile Object-independent semantic work such as:

```text
PROPERTY
    continuity / replacement
    add/remove rules
    requiredness transition
    SCALAR -> LIST transformation
    target exact-DTV validation/canonicalization
    canonical TARGET migration_default behavior

COMPONENT SLOT
    continuity / replacement
    ADD / REMOVE
    target widening
    position-only classification
    current object_component_slots delta to apply
```

The plan does not contain one Object's mutable state.

It must not contain:

```text
current Object properties
current Object canonical_name
current ownership membership
current target lifecycle status
```

# 6. MigrationPlan cache-resolution model

Normal execution consumes a READY immutable plan regardless of whether it was already cached or became READY during the request.

```text
MigrationPlan HIT
    -> consume plan

MigrationPlan MISS
    -> ensure every immutable input READY
    -> compile plan in memory
    -> cache plan
    -> consume same plan path
```

Required immutable inputs include:

```text
complete SOURCE exact effective ObjectTemplate closure
complete TARGET exact effective ObjectTemplate closure
all exact DataTypeVersion semantics referenced by SOURCE union TARGET
stable ObjectTemplate ancestry needed for component target-widening classification
```

Cold fill rules retained:

```text
load only missing immutable entries
bulk-load homogeneous misses
no N+1 exact-DTV queries
no runtime inheritance reconstruction merely because MigrationPlan is absent
no alternate one-off semantic execution path from raw DB rows
```

Once READY, plan work is reusable across all Objects migrating through the same exact pair on that worker.

The cold semantic cost is therefore principally per:

```text
(worker, template_id, source_version, target_version)
```

rather than per Object, subject to worker restart/eviction.

# 7. Standalone preliminary target admission is removed

An earlier route-local candidate performed an unlocked exact target existence/status lookup before immutable preparation.

That extra normal round trip is superseded.

Current sequence does **not** require a dedicated preliminary target-lifecycle query.

```text
initial Object binding
-> forwardness check
-> obtain/build immutable MigrationPlan
-> prepare Object candidate
-> enter UoW
-> final exact TARGET admission is the current lifecycle authority
```

On a cold exact TARGET closure load, the same bounded loader may incidentally discover that the exact target is absent or has no certified immutable closure; no additional preliminary admission statement is introduced solely for that purpose.

A cached immutable TARGET schema or MigrationPlan may remain semantically valid after TARGET becomes DEPRECATED. Cache presence never proves current new-binding admission.

# 8. Property migration semantics retained

The complete TARGET property map is built from TARGET semantic properties, not by replaying textual JSON-key edits over SOURCE state.

For each TARGET semantic property the compiled rule yields one of:

```text
preserved/transformed SOURCE information
canonical TARGET migration_default
absence
```

SOURCE-only semantic properties are omitted from target state.

## 8.1 ADD / REMOVE

```text
ADD optional
    -> target key absent

ADD required
    -> canonical TARGET migration_default

REMOVE optional
    -> existing value dropped if present

REMOVE required
    -> existing value dropped
```

Removed information is not moved to an archive/extras bucket and is not replaced by a default.

## 8.2 Requiredness transitions

```text
optional -> required
    SOURCE value present
        -> preserve existing information
        -> apply all other TARGET transformations/validation
        -> incompatibility = migration failure
        -> never fallback to migration_default

    SOURCE value absent
        -> canonical TARGET migration_default

required -> optional
    -> preserve existing information
    -> apply TARGET transformations/validation
    -> incompatibility = migration failure
    -> never drop merely because TARGET permits absence
```

`migration_default` fills absence only. It is never remediation for incompatible existing information.

## 8.3 SCALAR -> LIST

For a continuous semantic property:

```text
SOURCE value present
    x -> [x]
    -> TARGET exact-DTV validation/canonicalization

SOURCE optional value absent
    -> remains absent unless TARGET requiredness independently supplies its canonical migration_default
```

`LIST -> SCALAR` is not a normal admitted evolution.

## 8.4 Exact DataTypeVersion change

A continuous property may change exact DataTypeVersion only inside the same stable `datatype_id` lineage.

PrimitiveType remains stable.

```text
existing value
    -> preserve information
    -> validate/canonicalize against TARGET exact DTV

TARGET incompatible
    -> migration failure

LIST value
    -> preserve order
    -> validate every element
```

No cross-DataType-lineage conversion and no primitive conversion are performed.

## 8.5 Combined property deltas

Multiple simultaneous differences on one continuous property are compiled as **one target-oriented rule**, not an artificial ordered script.

Conceptual rule:

```text
ContinuousPropertyMigrationRule
    semantic_key
    source semantics
    target semantics
    compiled target validation/canonicalization
    canonical target migration_default where applicable
```

Object application order is logically:

```text
1. establish semantic continuity
2. inspect SOURCE value presence
3. preserve existing information when present
4. apply allowed information-preserving shape change
5. validate/canonicalize against complete TARGET exact-DTV semantics
6. materialize canonical sparse TARGET state
```

## 8.6 Same name, different semantic identity

For example:

```text
SOURCE (Device, hostname)
TARGET (Server, hostname)
```

means:

```text
REMOVE old semantic property
ADD new semantic property
```

The old value is not carried forward by name coincidence.

# 9. Component-slot migration semantics after materialization

`object_component_slots` changes the **runtime realization**, not the SOURCE/TARGET semantic classification.

Current slot delta applied during successful migration:

```text
ADD
    -> INSERT current object_component_slots row
    -> new semantic slot starts empty

REMOVE
    -> DELETE current slot row
    -> no implicit DETACH
    -> existing edge reference is final blocker authority

continuous target widening
    -> UPDATE target_template_id
    -> existing ownership edges preserved
    -> no per-child runtime compatibility revalidation

semantic replacement
    -> old semantic identity removed/replaced
    -> key-changing slot_declaring_template_id transition
       + target_template_id as required
    -> no implicit rebinding
    -> existing old semantic edge is final blocker
    -> new semantic slot starts empty

position-only change
    -> no slot-row DML
    -> ownership edges unchanged
```

Normal successful SCHEMA_CHANGE does not mutate `object_components`.

## 9.1 REMOVE / replacement blocker authority moved

Earlier WIPs read current outgoing edges during optimistic preparation and returned a conservative failure when a removed/replaced semantic slot had children.

That is no longer the preferred current candidate.

With:

```text
object_components semantic-slot FK
    -> object_component_slots current semantic key
```

final slot DELETE/key-changing transition becomes the authoritative blocker boundary.

Therefore:

```text
DETACH removes last old edge before final slot transition
    -> SCHEMA_CHANGE may succeed

old edge still references slot at final transition
    -> slot REMOVE/replacement cannot commit
    -> SCHEMA_CHANGE fails/rolls back
```

This removes the need to force a conservative false failure from an earlier ownership snapshot.

## 9.2 Continuous widening remains monotonic

For:

```text
SOURCE target = descendant
TARGET target = ancestor
```

all SOURCE-admissible child lineages remain TARGET-admissible by model-plane certification.

Existing ownership therefore remains valid without rereading child Objects or checking each current child lineage.

`target_template_id` is a non-semantic-key field in the current persistence candidate, so target widening need not conflict merely because ATTACH references the slot key.

# 10. Current optimistic preparation boundary

The earlier whole-Object snapshot/fingerprint included all outgoing ownership edges.

That scope is superseded by the current slot-materialization/FK candidate.

The preferred mutable preparation input now focuses on intrinsic Object state:

```text
id
canonical_name
template_id
template_version
properties
```

Current preferred per-attempt sequence:

```text
1. minimal Object binding lookup
       -> object existence
       -> template_id
       -> source_version

2. classify target_version > source_version

3. obtain/build READY immutable MigrationPlan

4. read one current intrinsic Object snapshot S
       id
       canonical_name
       template_id
       template_version
       properties

5. require S binding still matches the source identity used by the plan

6. compute intrinsic expected fingerprint F(S)

7. apply MigrationPlan.property_rules to S.properties
       -> complete target_properties

8. carry/reference MigrationPlan component slot delta
       -> final object_component_slots maintenance

9. build complete PreparedSchemaChange
```

No current child Object read, ownership-edge scan, effective-schema reread or ancestry reread is required during normal Object-specific candidate construction.

A component blocker is no longer certified from preparatory ownership membership.

# 11. PreparedSchemaChange current candidate

Conceptually:

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
        or immutable reference to the corresponding MigrationPlan rules

    lifecycle_before
    lifecycle_after
```

The candidate is mechanically applicable after final mutable protections succeed.

No expensive semantic migration or TARGET property validation should be repeated merely because the mutation UoW begins.

# 12. Intrinsic Object fingerprint

The optimistic fingerprint remains useful, but its current preferred scope shrinks to intrinsic Object state.

Logical state:

```text
id
canonical_name
template_id
template_version
properties
```

Explicitly excluded from the current preferred scope:

```text
outgoing object_components membership
child canonical names
public GET components projection
Relationship state
lifecycle history
```

The existing deterministic realization remains a useful retained candidate:

```text
canonical logical Object representation
-> canonical JSON
-> UTF-8
-> SHA-256
-> 32-byte digest
```

The same canonical encoder must be used during preparation and protected comparison.

Why membership may leave the fingerprint:

```text
preserved/widened slot membership
    -> ATTACH/DETACH does not invalidate property migration candidate

REMOVE/replacement
    -> final slot FK arbitrates old semantic edge existence
```

This reduces row volume, hashing work, lock coupling and false retry pressure relative to the earlier Object+all-outgoing-edges fingerprint.

# 13. Final target admission

TARGET exact ObjectTemplateVersion is a lifecycle-sensitive **new binding**.

A successful mutation must protect the exact target current lifecycle authority through commit and require:

```text
same template_id
exact target_version
status == PUBLISHED
```

Conceptually:

```text
exact TARGET ObjectTemplateVersion @ SHARE-equivalent protection
    -> require PUBLISHED
    -> retain protection through Object binding + slot delta + lifecycle commit
```

SOURCE exact ObjectTemplateVersion is an already-existing binding. It may be PUBLISHED or DEPRECATED and does not require new-binding PUBLISHED admission merely because the Object is migrating away from it.

Current final outcomes retained where unambiguous:

```text
TARGET exists + PUBLISHED
    -> may proceed while protected

TARGET exists + DRAFT/DEPRECATED
    -> 409 dependency_not_admissible
```

The exact classification of an unexpectedly absent target at final protected admission remains to be reconciled with final model-plane lifetime/delete-lineage architecture.

It must **not** silently consume the Object fingerprint retry budget: the bounded retry policy reserves automatic retry for protected Object-fingerprint mismatch only.

# 14. Short mutation-UoW logical responsibilities

The old four-statement UoW shape is reopened because two of its reasons changed:

```text
old Q3
    mandatory new post-lock statement to reread non-locked outgoing ownership

old Q4
    fused Object UPDATE + lifecycle only
```

Outgoing ownership is no longer part of the preferred fingerprint and final mutation now maintains `object_component_slots`.

Current logical responsibilities are instead:

```text
A. protect final TARGET PUBLISHED admission through commit

B. protect/revalidate the current intrinsic Object generation
   before applying PreparedSchemaChange

C. reject/retry if protected intrinsic state no longer matches
   expected_intrinsic_fingerprint

D. atomically apply:
       Object target template_version
       canonical migrated properties
       current object_component_slots delta
       exactly one SCHEMA_CHANGE lifecycle event

E. preserve object_components membership unchanged
   except that referenced old semantic slots may block REMOVE/replacement
```

The Object remains the concurrency owner for intrinsic mutation. The old parent-Object lock role as a generic ATTACH/DETACH rendezvous solely for ownership-slot continuity is superseded by the narrower slot-FK arbitration boundary.

The exact PostgreSQL realization is deliberately not frozen here:

```text
exact Object row-lock mode
whether lock acquisition and intrinsic fingerprint read can be fused safely
exact target-vs-Object lock order in the final global wait-for plan
number of slot-delta statements
whether Object UPDATE + slot delta + lifecycle can be fused partly or fully
constraint handling and retry/error mapping
```

These are architecture-phase realization questions as long as the logical responsibilities above are preserved.

# 15. ATTACH / DETACH interaction after slot materialization

## ATTACH

ATTACH no longer has to fail merely because the parent exact `template_version` changed.

Relevant cases:

```text
SCHEMA_CHANGE REMOVE/replacement reaches slot key transition first
    -> old-slot ATTACH cannot satisfy/reference the old current key

ATTACH edge references old semantic slot first
    -> REMOVE/replacement cannot remove/change referenced key

target widening
    -> non-key target update
    -> child admitted under old narrower target remains valid
```

Therefore ATTACH/SCHEMA_CHANGE synchronization should be as narrow as the actual semantic slot transition.

## DETACH

DETACH removes the referencing edge.

```text
DETACH first
    -> may remove final blocker
    -> REMOVE/replacement may then succeed

slot transition while edge remains
    -> FK blocks invalid transition
```

DETACH does not need to invalidate a prepared SCHEMA_CHANGE property candidate merely because ordinary preserved-slot membership changed.

# 16. Bounded optimistic retry retained

Automatic internal retry is allowed only for:

```text
protected_intrinsic_fingerprint
    !=
PreparedSchemaChange.expected_intrinsic_fingerprint
```

Retry budget:

```text
2 total attempts
=
1 initial attempt
+
1 complete fresh retry
```

Attempt 1 mismatch:

```text
no Object/slot/lifecycle DML
rollback
start one complete fresh attempt
```

The second attempt rederives all mutable Object conclusions. Immutable cache entries and a MigrationPlan may be reused only when their identities still match the newly observed source/target pair.

Attempt 2 mismatch:

```text
rollback
no third attempt
HTTP 409 STATE_CONFLICT
code = schema_change_blocked
blocker_type = concurrent_object_change
```

No other failure consumes this retry budget.

In particular:

```text
non-forward target
semantic property migration failure
slot REMOVE/replacement FK blocker
final target non-PUBLISHED admission
persistence failure
```

are not Object-fingerprint retry triggers.

# 17. Lifecycle retained

One successful real schema migration produces exactly one intrinsic lifecycle event:

```text
kind = SCHEMA_CHANGE
```

Failed/rolled-back migration produces no event.

Historical before/after snapshots contain exactly intrinsic Object state:

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
template_name
ObjectTemplate lifecycle/display metadata
```

Preparation constructs:

```text
lifecycle_before
    -> SOURCE intrinsic snapshot

lifecycle_after
    -> same Object identity/display name
    -> target_version
    -> target_properties
```

If protected intrinsic fingerprint matches, the prepared historical snapshots remain applicable; they do not need to be semantically rebuilt inside the UoW.

Object binding/properties, current slot materialization and SCHEMA_CHANGE lifecycle must commit atomically.

# 18. Cost and cache interpretation after revalidation

The old route-local totals:

```text
warm successful first attempt = 6 DB statements
full cold first Object         = 9 DB statements
```

were derived from the previous realization:

```text
Object + outgoing-edge preparation snapshot
parent Object ATTACH/DETACH rendezvous
separate fresh Object+edge fingerprint statement
final Object+lifecycle-only write
```

They are therefore **superseded as current route-total costs**.

The current design still preserves the valuable amortization property:

```text
MigrationPlan semantic compilation
    -> once per worker cache residency per exact migration pair

subsequent Objects using same pair
    -> reuse immutable plan
```

But final current warm/cold statement count must be derived only after architecture chooses the intrinsic Object protection/fingerprint and slot-delta statement realization.

Current qualitative cost shift:

```text
LESS
    outgoing-edge rows in preparation/protected fingerprint
    hashing of membership
    false retry coupling to preserved-slot ATTACH/DETACH
    generic parent-lock ownership coordination

MORE
    object_component_slots delta DML on SCHEMA_CHANGE

UNCHANGED IN PRINCIPLE
    immutable MigrationPlan reuse
    property migration outside critical section
    final target PUBLISHED protection
    one intrinsic SCHEMA_CHANGE lifecycle transition
```

# 19. Current open points / architecture handoff

The logical candidate above is the current discovery direction. Later architecture must close at least:

```text
final PostgreSQL statement decomposition
exact Object row-lock/protection mode
final target/Object/slot lock ordering and wait-for graph
deadlock freedom with ATTACH / DETACH / DELETE / intrinsic mutations
whether Object lock + fresh intrinsic fingerprint can be safely combined
exact object_component_slots delta DML/fusion
FK constraint timing/actions
slot blocker constraint -> public error mapping
unexpected final TARGET absence classification
final warm/cold route statement count
final physical indexes / DDL
EXPLAIN / BUFFERS evidence
storage/write measurements
bounded retry verification under final realization
```

Discovery must not restore outgoing ownership to the fingerprint merely to preserve an older UoW shape. Any broader fingerprint or parent-lock coupling must be re-justified against the final persistence/concurrency model.

# 20. Consolidation / supersession map

This first consolidated owner absorbs retained findings from at least:

```text
object-schema-change-delta-taxonomy.md
object-schema-change-property-migration.md
object-schema-change-dtv-migration.md
object-schema-change-property-rule-composition.md
object-schema-change-immutable-migration-plan.md
object-schema-change-cache-resolution.md
object-schema-change-migration-plan-amortization.md
object-schema-change-target-version-semantics.md
object-schema-change-target-admission.md
object-schema-change-remove-preliminary-target-admission.md
object-schema-change-preparation-properties.md
object-schema-change-prepared-candidate.md
object-schema-change-lifecycle.md
object-schema-change-bounded-retry.md
object-schema-change-q3-fingerprint-outcome.md
object-schema-change-uow.md
object-schema-change-warm-cost.md
object-schema-change-component-migration.md
object-schema-change-component-admission-from-snapshot.md
object-optimistic-preparation-fingerprint.md
object-aggregate-fingerprint-canonical-json.md
object-aggregate-fingerprint-sha256.md
```

Current supersession direction caused by `object_component_slots`:

```text
old component preparation
    current outgoing-edge scan used as blocker authority
        -> superseded

old aggregate fingerprint
    intrinsic Object + all outgoing ownership edges
        -> superseded by preferred intrinsic-only scope

old parent lock role
    ATTACH/DETACH rendezvous required for slot continuity
        -> superseded by preferred slot-FK arbitration

old mandatory separate protected aggregate statement
    required because ownership rows were not protected by Object row lock
        -> justification removed; final realization reopened

old final Q4
    Object UPDATE + lifecycle only
        -> reopened because slot delta must be maintained atomically

old warm/cold route totals
    6 / 9
        -> superseded until final realization is chosen

old standalone preliminary target query
        -> superseded / removed
```

Older source WIPs remain temporarily in the repository until a lossless comparison pass is completed. Git history remains the historical record after cleanup.
