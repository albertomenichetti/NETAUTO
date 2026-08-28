# M4 WIP — Per-Object component-slot data-plane materialization

Status: ACTIVE REVALIDATION / M4 WIP / ALWAYS NON-NORMATIVE

## Why this point is reopened

This candidate is a direct application of the M4 continuous-discovery revalidation rule.

The earlier Object/ownership WIPs converged on:

```text
objects
    current intrinsic Object state

object_components
    only current attached ownership edges
    + materialized stable slot semantic identity

object_template_effective_components
    immutable exact effective slot contract

worker-local cache
    warm exact effective component schema
```

That direction made existing ownership facts cheap, but empty effective slots still existed only as model-plane knowledge. The top-down Object GET and component-slot navigation work then exposed a repeated data-plane need to distinguish:

```text
slot absent
!=
slot present but empty
```

A further workload input materially changes the trade-off:

```text
Object.SCHEMA_CHANGE : Object.ATTACH
    approximately 1 : 100
```

This means that moving bounded current-slot maintenance onto rare Object CREATE / SCHEMA_CHANGE paths may be preferable if it removes repeated model-plane/cache work from ATTACH and frequent reads.

The earlier route-local checkpoints are therefore not treated as constraints. This note revalidates the persistence/materialization boundary across the Object operation family.

## Candidate concept

Introduce an owned derived data-plane relation containing one row for every component slot currently effective for one Object, including empty slots.

Current preferred candidate:

```text
object_component_slots
    object_id                    NOT NULL
    slot_declaring_template_id   NOT NULL
    slot_name                    NOT NULL
    target_template_id           NOT NULL
```

Meaning:

```text
one row
    = this Object currently exposes this exact effective semantic slot
      and this is the current stable target-lineage contract for ATTACH
```

This is not a new independent semantic authority. The semantic source remains the Object's current exact ObjectTemplateVersion and its certified immutable effective schema.

The slot table is an **owned derived runtime materialization** maintained atomically when the Object binding is created or changed.

## Why this is intentionally more than an existence table

A minimal materialization would persist only:

```text
object_id
slot_declaring_template_id
slot_name
```

The current stronger candidate also persists:

```text
target_template_id
```

because ATTACH consumes the target lineage on every admission, while normal target evolution is rare and monotonic widening. Paying one row UPDATE during a rare SCHEMA_CHANGE can therefore remove exact component-schema resolution/cache work from a much more frequent mutation.

## Field challenge

### Materialize `target_template_id` — YES candidate

Current consumers:

```text
ATTACH
    -> child stable-lineage compatibility admission

runtime diagnostics / future internal slot projection
    -> current slot target contract without model-plane reconstruction
```

Maintenance trigger:

```text
CREATE
    -> initial materialization

SCHEMA_CHANGE
    -> UPDATE only when a continuous slot target widens
```

Normal target evolution is widening toward an ancestor lineage. A child valid against the old narrower target remains valid against the new wider target.

### Materialize `effective_ordinal` / `position` — NOT CURRENTLY JUSTIFIED

This was evaluated as part of the non-minimal candidate and is currently rejected.

Current Object GET explicitly gives no contract meaning to JSON component-key order. Slot navigation pages children, not slots. ATTACH and DETACH do not consume slot ordering.

Persisting effective ordering would therefore add:

```text
storage
position-only SCHEMA_CHANGE updates
extra consistency surface
```

without removing work from a currently identified hot data-plane path.

If a future runtime consumer needs deterministic effective slot ordering as a contract, this field can be reopened.

### Still not materialized

No current benefit justifies copying:

```text
parent template_id
parent template_version
slot_declaring_template_version
child canonical names
components JSONB
```

The current Object binding remains owned by `objects`. Child names remain mutable Object state. Slot semantic identity is stable-lineage based rather than declaring-version based.

## Candidate relational identity

ObjectTemplate guarantees one unique effective member name across the shared property/component namespace and forbids inherited override/hiding.

For current runtime slots, two identities are useful:

```text
public/current lookup key
    (object_id, slot_name)

stable semantic slot key
    (slot_declaring_template_id, slot_name)
```

The candidate relational shape should therefore enforce both:

```text
PRIMARY KEY or UNIQUE
    (object_id, slot_declaring_template_id, slot_name)

UNIQUE
    (object_id, slot_name)
```

The exact choice of which becomes the declared PRIMARY KEY is a later physical-design choice. Both logical uniqueness properties matter.

## Ownership-edge FK candidate

Retain current ownership facts conceptually as:

```text
object_components
    child_object_id              PK
    parent_object_id             NOT NULL
    slot_declaring_template_id   NOT NULL
    slot_name                    NOT NULL
```

and add the strong relational dependency:

```text
FK (
    parent_object_id,
    slot_declaring_template_id,
    slot_name
)
REFERENCES object_component_slots (
    object_id,
    slot_declaring_template_id,
    slot_name
)
RESTRICT
```

This makes the database the final authority for:

```text
an ownership edge may exist only through a slot
that currently exists on that parent Object
under the same semantic slot identity
```

Including `slot_declaring_template_id` in the referenced key is deliberate. It makes semantic replacement a key-changing/removal operation that cannot silently reinterpret existing edges.

A direct `object_components.parent_object_id -> objects.id` FK may become redundant because parent existence is implied by the slot FK plus the slot's Object FK. Whether to retain or remove that duplicate constraint is OPEN for the final relational design.

## Slot ownership and Object DELETE

Slot rows are derived state owned by the Object, not external blockers.

Candidate lifetime shape:

```text
object_component_slots.object_id
    -> objects.id
    ON DELETE CASCADE
```

This allows Object DELETE to remove empty slot materialization automatically.

Because `object_components` references slot rows with RESTRICT semantics:

```text
Object with attached children
    -> cascading slot removal encounters referenced slot
    -> Object DELETE remains blocked

Object with only empty slots
    -> slot rows cascade away
    -> empty slot materialization does not block Object DELETE
```

This preserves the existing semantic rule that DELETE never implicitly detaches children.

Direct FKs from `slot_declaring_template_id` or `target_template_id` to ObjectTemplate lineages remain OPEN. They may duplicate model-plane lifetime blockers already guaranteed by the exact effective schema and stable lineage graph, while adding extra hot-path FK work and low-level delete blockers.

## Fundamental derived-state invariant

For every current Object `O`:

```text
MaterializedSlots(O)
    ==
EffectiveComponentSlots(
    O.template_id,
    O.template_version
)
```

For every row, at minimum:

```text
slot_declaring_template_id
slot_name
target_template_id
```

must equal the corresponding certified exact effective slot contract.

And every ownership edge must satisfy:

```text
edge semantic slot key
    -> exactly one current object_component_slots row
```

The Object binding and its materialized slot set must become atomically visible. No committed state may expose a new `objects.template_version` with the old slot materialization, or vice versa.

## CREATE revalidation

Earlier CREATE WIP says empty component slots are not materialized. That checkpoint is reopened.

Candidate final CREATE mutation:

```text
final exact PUBLISHED OTV admission/protection
+ INSERT Object
+ materialize all exact effective component slots for the new Object
```

The source rows already exist in immutable certified:

```text
object_template_effective_components
```

A preferred direction is one PostgreSQL business statement using the newly inserted Object identity plus a bounded `INSERT ... SELECT` from that exact effective-component range.

This does not perform semantic reconstruction inside the UoW; it copies already-certified immutable derived model state.

Candidate route statement count can therefore remain unchanged:

```text
STEP 1 binding/PUBLISHED lookup          1
STEP 3 final admission + Object + slots  1
CREATED lifecycle                        1
```

Additional CREATE cost is primarily:

```text
+ S slot row writes
+ one bounded internal exact-effective-component range read
```

where `S` is the Object effective slot count.

## GET Object revalidation

The earlier route-local candidate used:

```text
Q1 Object root
cache exact effective component schema
Q2 current ownership + child names
application merge

warm = 2 DB statements
cold = 3 DB statements
```

That path is reopened.

With current slot materialization, one statement can observe:

```text
objects
+ object_component_slots
+ object_components
+ child objects for canonical_name
```

and produce the complete Object representation including empty slots.

Candidate target:

```text
GET Object
    1 PostgreSQL statement
    0 component-schema cache lookup
    0 model-plane effective-schema read
    0 multi-statement coherent-read requirement
```

The query must still scale as:

```text
O(number of effective slots + number of direct children)
```

The exact SQL aggregation/LATERAL shape and physical indexes remain future plan-review items.

## GET one component slot revalidation

For:

```http
GET /objects/{parent}/components/{slot}
```

one statement can distinguish directly:

```text
parent absent
slot absent
slot present + empty
slot present + page of children
```

using:

```text
objects parent
LEFT JOIN object_component_slots requested current slot
LEFT/LATERAL current object_components page
JOIN child objects for canonical_name
```

No parent exact-template lookup, component-schema cache, or `object_template_effective_components` join is needed on the normal runtime read.

Statement count remains one, but the statement becomes pure current data-plane access.

## ATTACH revalidation

Earlier ATTACH preparation was:

```text
parent Object read
-> exact template pin
-> component-schema cache resolution
-> slot semantic identity + target_template_id
```

and the mutation UoW later locked/re-read the parent binding to prove that the prepared slot still belonged to the current schema.

Both assumptions are reopened.

### Candidate preparation

One parent+slot statement can return:

```text
parent existence
parent canonical_name
slot existence
slot_declaring_template_id
target_template_id
```

No parent exact template pin is needed merely to admit ATTACH.

Child bulk read and stable-ancestry compatibility cache remain independently useful.

### Candidate ATTACH x SCHEMA_CHANGE arbitration

The slot FK can replace the route-local need to stabilize the complete parent exact binding for slot safety.

Important races:

```text
SCHEMA_CHANGE removes slot first
    -> old slot row gone
    -> ATTACH edge INSERT cannot satisfy FK

ATTACH edge commits first
    -> slot row is referenced
    -> SCHEMA_CHANGE cannot remove that slot

semantic replacement
    -> declaring-template identity is part of FK key
    -> replacement cannot silently inherit old edges

target widening
    -> updates only non-key target_template_id
    -> child admitted under old narrower target remains valid after widening
```

Therefore a parent `template_version` change is no longer by itself a reason for ATTACH to fail. Only an actual incompatible current-slot transition needs to arbitrate with the edge write.

This potentially removes:

```text
parent FOR NO KEY UPDATE / exact-binding recheck
concurrent_object_change caused only by harmless parent-version evolution
component-schema cache dependency
component-schema cold fill
```

Global concurrency proof remains an architecture handoff; this is not yet normative.

### Candidate ATTACH statement cost

Starting from the previous reconciled cost:

```text
warm      7
full-cold 9
```

a conservative materialized-slot candidate becomes:

```text
PREPARATION
1 parent + current slot read
2 bulk child read
  ancestry cache

UoW
3 graph edge-add gate
4 protected ownerlessness + root-cycle admission
5 bulk edge INSERT
6 bulk ATTACH_TO lifecycle INSERT
COMMIT
```

Candidate:

```text
warm      6 PostgreSQL statements + COMMIT
full-cold 7 PostgreSQL statements + COMMIT
```

The only semantic-cache cold fill left on this path is stable child-lineage ancestry.

Further fusion of graph admission + edge INSERT is a separate optimization question and is not assumed here.

## DETACH revalidation

DETACH already needs no model-plane slot reconstruction because the current edge carries semantic identity.

The new slot FK changes the SCHEMA_CHANGE race:

```text
DETACH commits edge removal first
    -> a concurrent slot REMOVE/replacement may then proceed

SCHEMA_CHANGE slot REMOVE/replacement wins first
    -> it must arbitrate against the still-referenced slot row
```

This weakens the case for a parent Object lock used only as a generic SCHEMA_CHANGE rendezvous.

Candidate direction:

```text
remove route-local parent stabilization statement

one fresh set-based statement
    -> prove parent existence
    -> classify child existence
    -> DELETE exact requested edges
    -> RETURNING lifecycle material

one bulk DETACH_FROM INSERT
```

Candidate success cost:

```text
2 PostgreSQL statements + COMMIT
```

Whether DELETE + lifecycle can later be safely fused is a separate revalidation point.

## SCHEMA_CHANGE revalidation

This candidate changes the component side of Object SCHEMA_CHANGE materially.

Earlier WIPs treated effective slots as model-plane-only and used current outgoing ownership edges in both optimistic preparation and the whole-aggregate fingerprint so that ATTACH/DETACH changes could invalidate a prepared success.

With materialized current slots and edge->slot FK arbitration, that mechanism can be simplified.

### Component delta maintenance

The existing immutable MigrationPlan already knows the SOURCE -> TARGET component delta.

Candidate runtime maintenance:

```text
ADD slot
    -> INSERT current slot row

REMOVE slot
    -> DELETE current slot row
    -> FK failure if a current edge still references it

continuous slot target widening
    -> UPDATE target_template_id

semantic-identity replacement with same effective name
    -> key-changing UPDATE of slot_declaring_template_id
       plus target_template_id as required
    -> FK prevents key change while old semantic edges exist

position-only change
    -> no runtime slot DML because ordering is not materialized
```

Existing `object_components` edges remain unchanged on every successful normal SCHEMA_CHANGE.

### Ownership blockers move to the final relational boundary

For REMOVE/replacement, the final slot DELETE/key-changing UPDATE becomes the race authority.

This allows the component blocker rule to become:

```text
slot transition succeeds
    -> no blocking edge existed at the serialization point

FK blocks slot transition
    -> SCHEMA_CHANGE cannot commit
```

No diagnostic-only ownership query is required.

A concurrent DETACH may now allow the schema change to succeed if it removes the last blocker before final FK arbitration, rather than forcing the conservative false failure produced by an older preparatory ownership snapshot.

### Whole-Object fingerprint scope can shrink

Candidate revalidation removes outgoing ownership edges from the optimistic fingerprint.

The fingerprint remains useful for mutable intrinsic Object state required by property/schema migration:

```text
canonical_name
template_id
template_version
properties
```

but ATTACH/DETACH no longer need to invalidate a prepared migration merely because membership changed on preserved/widened slots.

REMOVE/replacement races are closed by the slot FK at final mutation.

This can reduce both optimistic and protected aggregate reads from:

```text
Object + all outgoing edges
```

to:

```text
Object intrinsic state only
```

Statement count need not decrease, but row volume, hashing work, lock coupling and retry frequency can.

### Final mutation cost

SCHEMA_CHANGE now pays slot-delta DML.

The delta is proportional to changed slots, not total slot count:

```text
row work ~= ADD + REMOVE + widened/replaced slots
```

A set-based final statement that applies disjoint slot deltas together with Object/lifecycle mutation may be feasible; alternatively architecture may use a small bounded number of additional bulk statements.

This WIP therefore does not freeze the new SCHEMA_CHANGE statement count yet.

Even a conservative `+1..+3` statement increase on SCHEMA_CHANGE is favorable under the supplied approximate workload ratio if ATTACH saves one statement on every warm invocation.

## Object DELETE revalidation

The current one-business-statement DELETE candidate can remain one statement.

Additional physical work becomes:

```text
DELETE Object
-> cascade owned empty/current slot rows
-> edge FK prevents cascade when attached children still exist
-> write DELETED lifecycle in the same business statement
```

No slot precheck is needed.

Object DELETE therefore pays row-delete volume proportional to current effective slot count but no new round trip.

## Workload-weighted mutation comparison

Using only the supplied approximate ratio:

```text
100 ATTACH
1 SCHEMA_CHANGE
```

and the conservative warm ATTACH improvement:

```text
7 -> 6 statements
```

we save approximately:

```text
100 PostgreSQL statements
```

per 101-operation mix before counting reads.

Even if SCHEMA_CHANGE required three additional PostgreSQL statements to maintain slot deltas:

```text
old mix   = 100*7 + 1*6 = 706
new upper = 100*6 + 1*9 = 609
```

which is still approximately 97 fewer business statements for that mutation mix.

This is not a benchmark and ignores row-volume/storage cost, but it demonstrates why SCHEMA_CHANGE statement count alone cannot reject the materialization candidate.

Frequent GET Object traffic would strengthen the case further because its candidate path changes from 2 warm / 3 cold statements to one statement.

## Storage/write-amplification cost

Let:

```text
O = current Object count
S = average effective component-slot count per Object
```

Then materialized slot row count is approximately:

```text
O * S
```

This is the principal cost of the candidate.

Additional index/storage cost is also expected because runtime needs both:

```text
(object_id, slot_name)
semantic composite identity used by ownership FK
```

Exact bytes and index choice must be measured against realistic Object/slot cardinalities before architecture freeze.

The candidate deliberately avoids `effective_ordinal` because that field would add write amplification without a current hot-path benefit.

## Cache consequences

The exact effective component-schema cache remains useful for model-plane consumers and other operations that need immutable exact schema semantics.

But under this candidate it is no longer required by:

```text
GET Object
GET one Object component slot
ATTACH slot resolution / target lookup
DETACH
```

This reduces runtime cold-path variability and removes the need to treat that cache facet as part of the normal Object data-plane read contract.

## Cross-operation consistency consequences

The materialization creates a useful runtime layering:

```text
objects
    current intrinsic Object state / exact binding

object_component_slots
    current effective component contract compiled onto this Object

object_components
    current membership facts constrained to those slots
```

This is intentionally different from making `object_component_slots` the model authority.

The consistency requirement is instead:

```text
ObjectTemplate exact effective schema
    semantic source

Object CREATE / SCHEMA_CHANGE
    materialization boundary

object_component_slots
    transactionally maintained runtime derivative

hot reads / ATTACH
    direct consumer
```

## WIP reopen / supersession map

This finding requires retroactive revalidation of at least:

```text
to-be-api-object-get.md
    -> REOPEN data path/cache/denormalization/cost/coherent-read realization

object-components-navigation-public-contract.md
    -> public contract retained; previously-open data path should consume slot materialization

to-be-api-object-create.md
    -> REOPEN statement claiming empty slots are not materialized
       and final mutation persistence dependencies

to-be-api-object-attach-batch.md
    -> REOPEN component-schema cache dependency
       parent binding stabilization
       concurrent_object_change race
       warm/cold cost

to-be-api-object-detach-batch.md
    -> REOPEN parent stabilization/LockPlan candidate and cost

object-components-physical-schema-discovery.md
    -> SUPERSEDED as complete runtime persistence candidate;
       enriched edge remains useful but is now only one part of the runtime design

object-schema-change-component-migration.md
    -> REOPEN ADD/REMOVE/replace statement that no empty slot row is materialized

object-schema-change-preparation-aggregate-read.md
object-schema-change-protected-fingerprint-read.md
object-aggregate-fingerprint-*.md
    -> REOPEN ownership-edge fingerprint scope

object-schema-change-q4-final-mutation.md
    -> REOPEN claim that final business mutation touches only Object + lifecycle

object-schema-change-warm-cost.md
    -> REOPEN statement count / row-work characterization

to-be-api-object-delete.md
    -> public/data-path direction retained;
       relational dependency and cascade row work must include owned slot rows
```

Other WIPs depending on any of these mechanisms must be revalidated transitively before being used again.

## Open architecture/discovery questions

Still OPEN:

```text
exact DDL and index choice for object_component_slots
whether direct object_components.parent_object_id FK becomes redundant
whether declaring/target template lineage copies receive direct FKs
exact CREATE fused statement shape
exact SCHEMA_CHANGE slot-delta statement decomposition
final ATTACH x SCHEMA_CHANGE PostgreSQL locking proof
final DETACH x SCHEMA_CHANGE PostgreSQL locking proof
constraint-specific failure mapping without diagnostic queries
realistic O and S storage/cardinality estimates
EXPLAIN evidence for GET Object, slot navigation and ATTACH lookup
migration/backfill ordering from current AS-IS
```

## Current candidate takeaway

The runtime persistence boundary is reopened around this stronger candidate:

```text
model-plane exact effective components
    -> certified immutable source

Object CREATE / SCHEMA_CHANGE
    -> compile current effective slot contract onto the Object

object_component_slots
    object_id
    slot_declaring_template_id
    slot_name
    target_template_id

object_components
    child ownership edge
    -> FK to current semantic slot row
```

Expected system-level effect:

```text
more storage
more bounded row writes on rare CREATE/SCHEMA_CHANGE/DELETE

in exchange for

fewer hot data-plane statements
less cache dependence
less schema reconstruction
stronger relational slot/edge arbitration
less cross-operation locking/retry coupling
```

This candidate is sufficiently strong to require immediate revalidation of the earlier Object route-local checkpoints, but it remains WIP and may still be modified or discarded as later findings emerge.
