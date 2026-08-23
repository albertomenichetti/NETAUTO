# M2 Semantic Concurrency Matrix

**Status:** FINAL / FROZEN

**Authority:** NORMATIVE M2 ARCHITECTURE — FINAL / FROZEN

## Authority and scope

This document is the canonical M2 semantic mutation census and pairwise concurrency matrix.

It owns:

```text
complete mutation inventory
semantic interaction scope
safety-predicate definitions
allowed committed outcomes
intentional semantic independence
cross-domain predicate composition
handoff obligations to PostgreSQL realization and verification
```

Its implementation authority, once the complete M2 architecture set is frozen, is:

```text
docs/architecture/concurrency-matrix.md
    delivered semantic concurrency AS-IS
+
docs/milestones/M2/contract.md
    FINAL / FROZEN obligations and explicit deltas
+
relationship.md
    M2 Relationship semantics
+
api.md
    public success/failure outcomes
+
persistence.md
    physical authorities and transaction constraints
+
this document
    complete M2 semantic interaction matrix
```

This document defines **what must remain true** under every supported interleaving. It does not select row-lock modes, advisory-lock keys, retry limits or SQLAlchemy helpers. Those belong to `concurrency.md`. Deterministic independent-session PostgreSQL evidence belongs to `verification.md`.

The semantic matrix must never be reconstructed from the physical lock layout. A lock is valid only if it realizes a predicate defined here without silently changing the public contract.

---

## 1. Analysis method and completeness rule

Every concrete pair is analyzed in this order:

```text
scope
    -> when do the concrete operations interact?

risk
    -> which invalid committed state or impossible history is threatened?

safety predicate
    -> which property must remain true?

allowed outcomes
    -> which serial, conflicting, no-op or conservative outcomes are valid?
```

M2 has 41 mutation primitives.

```text
directed matrix cells      41 × 41 = 1681
unordered cells            41 × 42 / 2 = 861
family blocks evaluated    15
```

The authoritative representation is sparse:

1. every concrete cell begins as `I — INDEPENDENT`;
2. a scoped rule below replaces or augments `I` when its qualifier matches;
3. multiple predicates may apply to one race;
4. the predicate set is symmetric even when command roles differ;
5. all 861 unordered cells are classified by the sparse default plus the rules below.

Read-only operations are not mutation cells. Their snapshot/coherence obligations remain in `relationship.md`, `api.md` and `persistence.md`.

---

## 2. Canonical M2 mutation census

### DataType — 10

```text
DT.C      CREATE
DT.CN     CREATE_NEXT
DT.R      REVISE
DT.P      PUBLISH
DT.SD     SET_DEFAULT
DT.CD     CLEAR_DEFAULT
DT.D      DEPRECATE
DT.DD     DELETE_DRAFT
DT.DL     DELETE_LINEAGE
DT.DESC   SET_DESCRIPTION
```

### ObjectTemplate — 10

```text
OT.C      CREATE
OT.CN     CREATE_NEXT
OT.R      REVISE
OT.P      PUBLISH
OT.SD     SET_DEFAULT
OT.CD     CLEAR_DEFAULT
OT.D      DEPRECATE
OT.DD     DELETE_DRAFT
OT.DL     DELETE_LINEAGE
OT.DESC   SET_DESCRIPTION
```

### Object and ownership — 7

```text
OBJ.C     CREATE
OBJ.RN    RENAME
OBJ.DC    DATA_CHANGE
OBJ.SC    SCHEMA_CHANGE
OBJ.A     ATTACH
OBJ.DET   DETACH
OBJ.DEL   DELETE
```

### RelationshipDefinition and exact versions — 10

```text
RD.C      CREATE
RD.RN     RENAME
RD.CN     CREATE_NEXT
RD.R      REVISE
RD.P      PUBLISH
RD.SD     SET_DEFAULT
RD.CD     CLEAR_DEFAULT
RD.D      DEPRECATE
RD.DD     DELETE_DRAFT
RD.DL     DELETE_DEFINITION
```

`RD.*` uses the same aggregate-prefix convention as `DT.*` and `OT.*`: the stable Definition and its exact versions are one versioned aggregate family.

### Factual Relationship — 4

```text
REL.C     CREATE
REL.DC    DATA_CHANGE
REL.SC    SCHEMA_CHANGE
REL.DEL   DELETE
```

### M2 census delta

The delivered 32-mutation census is preserved and extended by nine primitives:

```text
RD.CN
RD.R
RD.P
RD.SD
RD.CD
RD.D
RD.DD
REL.DC
REL.SC
```

The delivered `RD.DEL` root operation is canonically named `RD.DL` here to align with the other versioned aggregate families. Its public behavior is unchanged except for the explicit M2 contract deltas already frozen.

Any future mutation must be added to this census and compared against all 41 existing primitives before its architecture can be considered complete.

---

## 3. `I — INDEPENDENT`

`I` means that the concrete pair introduces no shared **semantic** safety predicate beyond the invariants each operation already owns independently.

`I` does not promise:

```text
zero row-lock contention
zero FK or UNIQUE waiting
physical parallel execution
absence of conservative implementation serialization
absence of a shared advisory gate
```

Examples:

```text
OBJ.RN(parent) × OBJ.A(parent, slot, child)
    semantic = I
    current realization may serialize on the parent Object

independent model-root DELETE × independent model-root DELETE
    semantic = I
    M2 realization deliberately over-serializes through MODEL_ROOT_DELETE_GATE

REL.DC(fact A) × REL.DC(fact B)
    semantic = I
    provided A != B
```

Physical over-serialization of an `I` cell must be documented in `concurrency.md` and must not be reinterpreted as a new domain invariant.

---

## 4. Safety-predicate catalog

M2 retains the 19 delivered predicates and introduces two justified predicates:

```text
VH    versioned schema-history coherence
RS    complete factual Relationship state
```

The complete M2 catalog contains 21 predicates.

### `NU` — qualified-name uniqueness

**Scope:** two mutations may introduce or reuse the same stable `(namespace, name)` in the same entity kind.

**Risk:** two current DataType or ObjectTemplate lineages own the same qualified name.

**Required property:** at most one current lineage owns the name.

**Allowed outcomes:** one candidate wins; the conflicting candidate fails. A delete may free the name for a later serial create. No orphan version/declaration aggregate survives.

---

### `VS` — coherent version set and source eligibility

**Scope:** concurrent mutations allocate from, delete from or change eligibility inside one stable aggregate version set.

**Risk:** duplicate allocation, stale `max(existing)+1`, or CREATE_NEXT source eligibility evaluated against no serially coherent state.

**Required property:** allocation and source eligibility are explainable by one serial order of the current version set.

**Allowed outcomes:** waiters re-evaluate the complete set and source after stabilization; version gaps/reuse follow the frozen version contract.

---

### `DG` — DRAFT generation freshness

**Scope:** operations consume the same exact DRAFT generation and `expected_revision`.

**Risk:** incompatible outcomes based on one generation both commit.

**Required property:** one generation cannot be revised, published or deleted twice as though no competing consumer existed.

**Allowed outcomes:** one consumer wins; later consumers observe `stale_revision`, lifecycle conflict or exact resource absence according to the command reached in the serial order.

---

### `LS` — lifecycle state

**Scope:** operations act on or depend on the lifecycle transition of the same exact version.

**Risk:** duplicate, illegal or non-monotonic transitions.

**Required property:** committed status history is explainable by:

```text
DRAFT -> PUBLISHED -> DEPRECATED
```

**Allowed outcomes:** one real transition per boundary; every waiter rechecks current status before deciding success or the defined non-success outcome.

---

### `DV` — default validity and policy order

**Scope:** operations read, establish, replace, clear or invalidate one stable aggregate default.

**Risk:** default points to a non-PUBLISHED or wrong-aggregate version, or first-publication policy reflects no serial order.

**Required property:**

```text
default_version = null
or
default_version identifies an exact same-aggregate PUBLISHED version
```

**Allowed outcomes:** first serial publication may establish a missing default; set/clear/deprecate and implicit binding observe one coherent default-policy order.

---

### `VH` — versioned schema-history coherence

**Scope:** distinct `OT.P` or distinct `RD.P` operations in the same aggregate can change the published historical member baseline used to certify property/component evolution.

**Risk:** both candidates validate against the same old history and commit a pair of PUBLISHED snapshots that cannot be admitted in any serial order, for example a later `SCALAR -> LIST` history followed by an independently certified `LIST -> SCALAR` publication.

**Required property:** each committed PUBLISHED schema snapshot is certified against one serially coherent current PUBLISHED/DEPRECATED semantic-member history.

**Allowed outcomes:** the first publisher commits; the waiter reloads historical continuity and either commits if still admissible or fails semantic certification. If default policy is material, `DV` applies in addition.

`VH` is not required for DataType constraints because the delivered DataType lineage has no equivalent cross-version member-history rule.

---

### `BA` — lifecycle-sensitive new binding admission

**Scope:** a mutation creates or rebinds a persisted exact dependency, or resolves a default into a new exact runtime/model pin.

**Risk:** a new binding commits to an exact target that was not PUBLISHED through admission and commit.

**Required property:** the selected exact dependency remains PUBLISHED through the new binding/certification commit.

**Allowed outcomes:** binding wins and the target lifecycle change cannot invalidate it before commit; lifecycle/delete wins and the binding fails. Implicit selection uses one coherent default and target lifecycle state.

Cloning already-owned exact pins through CREATE_NEXT is not `BA`; clone lifetime is covered by `RL`.

---

### `AM` — active model graph

**Scope:** operations activate or remove a direct PUBLISHED consumer edge while another operation deprecates the exact dependency.

**Risk:**

```text
PUBLISHED consumer -> non-PUBLISHED dependency
```

**Required property:** every direct exact lifecycle-sensitive dependency of a PUBLISHED consumer remains PUBLISHED.

**Allowed outcomes:** consumer publication wins and dependency deprecation is blocked; dependency deprecation wins and publication fails; active-consumer removal may permit dependency deprecation or may yield a conservative conflict.

---

### `RL` — cross-aggregate reference lifetime

**Scope:** one operation creates, removes or materially rebinds a current cross-aggregate reference while another deletes its target.

**Risk:** dangling current reference, implicit semantic cascade or reference resurrection against a deleted target.

**Required property:** target and reference lifetime follow a valid serial order.

**Allowed outcomes:**

```text
reference wins
    -> target delete cannot commit

target delete wins
    -> new/rebound reference cannot commit

reference removal wins
    -> target delete may become admissible

delete observes blocker before removal
    -> conservative delete_blocked is permitted
```

A mutation that leaves an already-existing stable root reference semantically unchanged is ordinarily `I` with the root delete, even when the physical realization still requires careful lock ordering.

---

### `AL` — aggregate and owned-child lifetime

**Scope:** an operation acts on a stable aggregate or owned exact child while another deletes the same root aggregate.

**Risk:** orphan child state, partial aggregate, mutation after deletion or resurrection.

**Required property:** internal mutation and root lifetime have one serial explanation.

**Allowed outcomes:** the internal mutation completes before root deletion, or root deletion wins and the later internal operation cannot commit against the absent aggregate.

---

### `ML` — metadata last-write-wins

**Scope:** concurrent writes target one metadata field whose contract is atomic last-write-wins, currently `description`.

**Risk:** torn/merged metadata or invented optimistic-conflict behavior.

**Required property:** final state equals one complete committed candidate.

**Allowed outcomes:** either write may be final; no merge or partial value.

---

### `OS` — complete Object state

**Scope:** intrinsic Object operations depend on or mutate the same Object snapshot.

**Risk:** lost JSONB update, stale schema migration, wrong delete snapshot or lifecycle state that never matched committed Object state.

**Required property:** current Object state and intrinsic lifecycle events are explainable by one serial sequence of complete transitions.

**Allowed outcomes:** waiter reloads and rederives from current committed state; each real state/event transition commits completely or not at all.

---

### `RS` — complete factual Relationship state

**Scope:** `REL.DC`, `REL.SC` and `REL.DEL` operate on the same factual Relationship identity.

**Risk:** lost property update, migration from stale pin/state, deletion snapshot inconsistent with current state, or lifecycle events that cannot be placed in one serial factual history.

**Required property:** exact pin, complete canonical properties, closure preservation/removal and lifecycle snapshots are explainable by one serial sequence of factual Relationship transitions.

**Allowed outcomes:**

```text
DATA_CHANGE × DATA_CHANGE
    -> waiter derives from fresh properties
    -> either another real change or a semantic no-op

DATA_CHANGE × SCHEMA_CHANGE
    -> second operation applies under the fresh schema/state
    -> or fails by its normal validation/conflict contract

SCHEMA_CHANGE × SCHEMA_CHANGE
    -> second target is re-evaluated against the fresh source pin
    -> proceeds only if still a valid forward target

mutation × DELETE
    -> mutation first then delete captures resulting final state
    -> or delete first and mutation observes resource_not_found
```

`RS` does not make different Relationship identities interact.

---

### `PO` — parent schema and ownership coherence

**Scope:** parent Object `SCHEMA_CHANGE` races with `ATTACH` or `DETACH`.

**Risk:** a committed outgoing edge is invalid under the parent's committed exact schema.

**Required property:** every current edge resolves to one current `SlotSemanticKey` and compatible child under the parent schema.

**Allowed outcomes:** ATTACH first is observed by schema migration; schema change first governs later ATTACH; DETACH may remove a blocker before migration.

---

### `OF` — ownership fact

**Scope:** ATTACH/DETACH operations concern the same child's current ownership fact.

**Risk:** duplicate transition/event, removal of another edge, implicit move or non-serial fact history.

**Required property:** one child evolves serially between detached and exactly one `(parent, slot)` fact.

**Allowed outcomes:** identical operations converge with one real transition; DETACH never removes a different edge; ATTACH never performs implicit move.

---

### `SO` — single owner

**Scope:** different ATTACH candidates target the same child with distinct desired ownership facts.

**Risk:** one child has multiple current owners.

**Required property:** at most one ownership fact exists per child.

**Allowed outcomes:** one candidate commits; the other fails after final arbitration and fresh evaluation.

---

### `OC` — ownership acyclicity

**Scope:** concurrent ownership edge additions can jointly create a cycle while each appears locally valid.

**Risk:** committed ownership graph contains a directed cycle.

**Required property:** the committed graph remains acyclic.

**Allowed outcomes:** only a cycle-free subset commits; waiter evaluates a fresh protected graph; concurrent removal may permit success or conservative rejection.

---

### `RC` — certified RelationshipDefinition set

**Scope:** `RD.C`, `RD.RN` and deletion of blocking Definitions alter the globally certified stable topology/navigation set.

**Risk:** equivalent Definitions or cross-Definition Resolution conflicts coexist.

**Required property:** the committed stable Definition set is semantically non-duplicated and conflict-free.

**Allowed outcomes:** at most one incompatible candidate commits; deleting a blocker may permit a later candidate; a candidate that observed the blocker may fail conservatively.

Versions, defaults and properties do not participate in `RC`.

---

### `RF` — factual Relationship and exact-view uniqueness

**Scope:** concurrent `REL.C` candidates have intersecting deterministic closures, including equivalent facts expressed through reciprocal/symmetric/inheritance-overlap selectors or distinct invalid candidates that contend for an exact runtime view.

**Risk:** duplicate factual identities, one exact view owned by multiple facts, partial closure or duplicate creation event sets.

**Required property:**

```text
one exact runtime view belongs to at most one current fact
and
every committed fact owns its complete deterministic closure
```

**Allowed outcomes:** if no current owner exists, one candidate creates the fact and every conflicting loser rolls back completely. If an exact view is already owned before both candidates, both candidates fail against that current owner. After fresh re-evaluation, a loser returns `relationship_fact_conflict` while the winner/current owner remains; if that owner disappeared, a fresh candidate may create a new factual identity.

M2 deliberately does not treat the loser as successful convergence.

---

### `RA` — Relationship exact-ID lifetime and ABA

**Scope:** create/delete/retry occurs around one semantic fact and an exact factual identity, or same-ID DELETE operations race.

**Risk:** stale `DELETE(X)` removes a later equivalent fact `Y`, or multiple real deletion event sets are emitted for X.

**Required property:** DELETE affects only the exact requested UUID and every exact identity has at most one real deletion transition.

**Allowed outcomes:** one same-ID DELETE returns `204` and emits the event set; a waiter returns `404`. After X is removed, a late DELETE(X) never removes recreated Y.

---

### `ES` — Relationship event metadata snapshot

**Scope:** a real Relationship transition races with mutable Object canonical names or RelationshipResolution navigation names captured in its event fan-out.

**Risk:** one event set combines metadata from incompatible committed observations.

**Required property:** the complete event set uses one coherent committed metadata observation.

**Allowed outcomes:** the set is wholly consistent with one statement snapshot. For one rename transaction it is all-old or all-new. With multiple independent renames, only combinations that coexisted in the authoritative snapshot are valid.

`ES` applies only to real transitions:

```text
successful new REL.C
real REL.DC
every successful REL.SC
real REL.DEL
```

A duplicate CREATE conflict or DATA_CHANGE no-op creates no event set and does not activate `ES`.

---

## 5. Common versioned-aggregate rules

Let:

```text
X ∈ {DT, OT, RD}
```

where `X.DL` deletes the stable root and its owned versions.

### 5.1 Version allocation and source state

```text
X.CN × X.CN
    VS when same stable aggregate

X.CN × X.DD
    VS when same aggregate and DRAFT deletion changes the relevant maximum

X.CN × X.P
    VS when PUBLISH changes the selected exact source from ineligible DRAFT
       to eligible PUBLISHED

X.CN × X.DL
    AL when the root being removed owns the source/version set
```

A source deprecation does not invalidate CREATE_NEXT because PUBLISHED and DEPRECATED are both eligible; absent another predicate, `X.CN × X.D = I`.

### 5.2 Exact DRAFT generation

```text
{X.R, X.P, X.DD} × {X.R, X.P, X.DD}
    DG when the same exact DRAFT generation is consumed
```

Where one or both operations cross a lifecycle boundary, `LS` also applies.

Examples:

```text
X.R × X.P
    DG + LS on same exact generation

X.P × X.DD
    DG + LS on same exact generation

X.DD × X.DD
    DG on the same exact generation:
    one delete succeeds, the later exact target is absent
```

The public result remains operation-specific; the predicate set does not invent idempotence.

### 5.3 Lifecycle and default policy

```text
X.P × X.D
    LS when same exact version
    + DV when that version is or may become default

X.D × X.D
    LS when same exact PUBLISHED version

X.P(vA) × X.P(vB)
    DV when same aggregate and missing-default first-publication policy is material

X.P × {X.SD, X.CD}
{X.SD, X.CD} × {X.SD, X.CD}
    DV when same aggregate

{X.SD, X.CD} × X.D
    DV when deprecation targets the selected/current default
```

For `OT` and `RD`, distinct same-aggregate publication may additionally activate `VH`.

### 5.4 Aggregate lifetime

```text
{X.CN, X.R, X.P, X.SD, X.CD, X.D, X.DD} × X.DL
    AL when same stable aggregate

X.DL × X.DL
    AL when same exact stable aggregate
```

Metadata operations join the same rule in their family-specific sections.

---

## 6. DataType internal rules

```text
DT.C × DT.C
    NU when same qualified name

DT.C × DT.DL
    NU when CREATE reuses the qualified name being removed

DT.DESC × DT.DESC
    ML when same lineage

DT.DESC × DT.DL
    AL when same lineage
```

Distinct DataType root deletes with no cross-reference are semantically `I`, although the M2 PostgreSQL realization may serialize all model-root deletes.

All other DT×DT cells follow the common versioned rules or remain `I`.

---

## 7. ObjectTemplate internal and cross-lineage rules

### 7.1 Stable qualified name and metadata

```text
OT.C × OT.C
    NU when same qualified name

OT.C × OT.DL
    NU when CREATE reuses the qualified name being removed

OT.DESC × OT.DESC
    ML when same lineage

OT.DESC × OT.DL
    AL when same lineage
```

### 7.2 Published member history

```text
OT.P(vA) × OT.P(vB)
    VH when vA != vB, same lineage and published property/component
       history may affect either candidate
    + DV when default establishment is material
```

The waiter re-certifies historical property and component evolution after the first publication.

### 7.3 Exact parent binding and stable component references

```text
OT.C or OT.R
× parent exact-version lifecycle/default mutation
    BA when the candidate creates/rebinds an exact parent OTV
    + DV when omitted parent_version resolves through parent default

OT.C or OT.R
× OT.DL(target lineage)
    RL when the candidate adds, removes or rebinds a parent/component
       reference to that target lineage

OT.CN
× OT.DL(target lineage)
    RL when the clone materializes parent/component references to the target

OT.DD(consumer DRAFT)
× OT.DL(target lineage)
    RL when deleting the DRAFT removes a current target reference

OT.DL(consumer lineage)
× OT.DL(target lineage)
    RL when the consumer aggregate owns a parent/component reference
       into the target
```

A REVISE that preserves the same exact parent pin is not a new `BA` admission. A source clone is not `BA`; it remains a new physical lifetime reference under `RL`.

### 7.4 Active exact-parent graph

```text
OT.P(consumer) × OT.D(dependency)
    AM when the consumer exact parent pin targets the dependency

OT.D(consumer) × OT.D(dependency)
    AM when consumer deprecation removes an active blocker

OT.DL(consumer lineage) × OT.D(dependency)
    AM when root deletion removes active exact-parent consumers
```

All other OT×OT scopes remain `I` unless a common rule applies.

---

## 8. Object and ownership internal rules

```text
{OBJ.RN, OBJ.DC, OBJ.SC, OBJ.DEL}
×
{OBJ.RN, OBJ.DC, OBJ.SC, OBJ.DEL}
    OS when same Object and the operations depend on or produce
       complete intrinsic state
```

```text
OBJ.SC(parent) × OBJ.A(parent, slot, child)
    PO

OBJ.SC(parent) × OBJ.DET(parent, slot, child)
    PO
```

```text
OBJ.A(parent, slot, child) × identical OBJ.A
    OF

OBJ.A(P1,S1,C) × OBJ.A(P2,S2,C)
    SO when desired ownership facts differ

OBJ.A(edge1) × OBJ.A(edge2)
    OC when both committed edges could form a cycle

OBJ.A × OBJ.DET
    OF when the same child/current ownership fact is involved

OBJ.DET × OBJ.DET
    OF when the same child/current ownership fact is involved
```

```text
OBJ.A × OBJ.DEL
    RL when ATTACH creates a reference to the Object being deleted

OBJ.DET × OBJ.DEL
    RL when DETACH removes the current ownership blocker
```

Intentional semantic independence remains:

```text
OBJ.RN(parent) × OBJ.A(parent, slot, child)
OBJ.DC(parent) × OBJ.A(parent, slot, child)
OBJ.SC(child)  × OBJ.A(parent, slot, child)
```

The physical realization may intentionally serialize some of these on the parent Object.

---

## 9. RelationshipDefinition internal rules

The common versioned-aggregate rules apply to `RD.CN/R/P/SD/CD/D/DD/DL`.

### 9.1 Certified stable Definition set

```text
RD.C × RD.C
    RC when candidates are equivalent or cross-conflicting

RD.C × RD.RN
    RC when create and renamed candidates may conflict/equivalate

RD.RN × RD.RN
    RC for same-Definition rename serialization or conflicting
       different-Definition candidates

RD.C or RD.RN × RD.DL(other)
    RC when the deleted Definition is a blocker of the candidate set
```

```text
RD.RN × RD.DL
    AL when same Definition

RD.DL × RD.DL
    AL when same Definition
```

Deleting a Definition cannot itself introduce a new stable-set conflict.

### 9.2 Published property history

```text
RD.P(vA) × RD.P(vB)
    VH when vA != vB, same Definition and published property history
       may affect either candidate
    + DV when default establishment is material
```

### 9.3 Stable topology versus version state

Absent root deletion or another listed predicate, the following are intentionally `I`:

```text
RD.RN × {RD.CN, RD.R, RD.P, RD.SD, RD.CD, RD.D, RD.DD}
```

Rename changes Resolution metadata and global certification only; it does not mutate version schema/default state. The PostgreSQL realization must preserve this semantic independence where required by the progress contract.

Different Definition root deletes are semantically `I` unless another cross-reference or `RC` scope applies. The model-root delete gate is conservative physical serialization, not a new `RC` rule.

---

## 10. Factual Relationship internal rules

### 10.1 Concurrent creation

```text
REL.C × REL.C
    RF when deterministic candidate closures intersect
```

This includes:

```text
reciprocal selectors of one non-symmetric fact
symmetric inverse endpoint assignment
inheritance-overlap equivalent views
distinct candidate closures sharing an exact runtime-view key
```

The M2 loser returns `relationship_fact_conflict`; it does not converge successfully.

### 10.2 Complete factual state

```text
{REL.DC, REL.SC, REL.DEL}
×
{REL.DC, REL.SC, REL.DEL}
    RS when same relationship_id
```

Additional exact-delete rule:

```text
REL.DEL × REL.DEL
    RS + RA when same relationship_id
```

### 10.3 Create/delete and ABA

```text
REL.C × REL.DEL
    RF + RA when DELETE targets the current identity of the same
       semantic fact or a fresh CREATE/retry crosses its removal
```

Valid serial outcomes include:

```text
CREATE observes current X
    -> relationship_fact_conflict
    -> DELETE may later remove X

DELETE removes X first
    -> later fresh CREATE may create Y

late DELETE(X) after Y exists
    -> resource_not_found for X
    -> Y remains
```

### 10.4 Intentional independence

```text
REL.C × REL.DC
REL.C × REL.SC
```

are semantically `I` when a current fact already exists: CREATE conflicts by factual identity independently of current pin/properties, while the mutation owns the current fact state.

Operations on different `relationship_id` values are `I` unless CREATE closures intersect under `RF`.

There is no global Relationship graph predicate.

---

## 11. DataType × ObjectTemplate

```text
OT.C or OT.R
× DTV lifecycle/default mutation
    BA when a property creates/rebinds an exact DTV
    + DV when datatype_version omission resolves the DataType default
```

The lifecycle/default mutation set includes the concrete operation that can change target admission:

```text
DT.P
DT.D
DT.SD
DT.CD
```

```text
OT.C or OT.R × DT.DL
    RL when the final candidate adds/removes/rebinds a property reference

OT.CN × DT.DL
    RL when cloned declarations materialize exact DTV references

OT.DD × DT.DL
    RL when DRAFT removal removes a current DTV lifetime blocker

OT.DL × DT.DL
    RL when the ObjectTemplate aggregate owns DTV references
```

```text
OT.P × DT.D
    AM when publication activates an exact property edge

OT.D × DT.D
    AM when consumer deprecation removes an active blocker

OT.DL × DT.D
    AM when consumer root deletion removes active blockers
```

A candidate preserving an already-owned exact pin is not new `BA`. DTV deprecation may proceed against a DRAFT consumer that merely preserves the historical pin; publication later rechecks `AM`.

All other DT×OT cells are `I`.

---

## 12. DataType × RelationshipDefinition

RelationshipDefinitionVersion properties use the same exact DTV lifecycle and lifetime model as ObjectTemplate properties.

```text
RD.C or RD.R
× DTV lifecycle/default mutation
    BA when a property creates/rebinds an exact DTV
    + DV when datatype_version omission resolves the DataType default
```

```text
RD.C or RD.R × DT.DL
    RL when the final candidate adds/removes/rebinds a DTV reference

RD.CN × DT.DL
    RL when cloned declarations materialize exact DTV references

RD.DD × DT.DL
    RL when DRAFT removal removes a current DTV lifetime blocker

RD.DL × DT.DL
    RL when Definition-owned declarations reference the DataType lineage
```

```text
RD.P × DT.D
    AM when publication activates a direct DTV edge

RD.D × DT.D
    AM when RDV deprecation removes an active blocker

RD.DL × DT.D
    AM when Definition root deletion removes active RDV consumers
```

`RD.CN` clone is not `BA`; its dependencies may already be DEPRECATED and publication remains separately blocked.

All other DT×RD cells are `I`.

---

## 13. DataType × Object and DataType × Relationship

Every concrete cell in these two blocks is `I`.

```text
DataType × Object
DataType × factual Relationship
```

Reasons:

- Object runtime consumes DTV semantics through an already-certified exact ObjectTemplateVersion;
- factual Relationship runtime consumes DTV semantics through an already-certified exact RelationshipDefinitionVersion;
- existing historical exact bindings remain valid after dependency deprecation;
- DATA_CHANGE and SCHEMA_CHANGE do not recursively create new DTV bindings.

This evaluated independence does not weaken corruption checks: a missing or DRAFT exact DTV behind persisted certified state remains `internal_error`.

---

## 14. ObjectTemplate × Object and ownership

```text
OBJ.C × target OTV lifecycle/default mutation
    BA when explicit/default target admission is affected
    + DV when template_version omission resolves the ObjectTemplate default

OBJ.C × OT.DL
    RL when CREATE introduces Object -> exact OTV lifetime
```

```text
OBJ.SC × target OTV PUBLISH/DEPRECATE
    BA when the operation concerns the explicit schema-change target
```

`OBJ.SC` source deprecation is `I`: the current source may be PUBLISHED or DEPRECATED.

```text
OBJ.DEL × OT.DL
    RL when Object deletion removes the current exact OTV/root blocker
```

Intentional semantic independence remains:

```text
OBJ.SC × OT.DL = I
```

because the stable ObjectTemplate lineage reference exists before and after and root deletion is already blocked by the current Object. The target-before-owner physical lock order remains mandatory in `concurrency.md` to avoid a wait-cycle; it does not create a new semantic result.

`OBJ.RN`, `OBJ.DC`, `OBJ.A` and `OBJ.DET` consume already-bound schema state and do not create OTV lifecycle admission.

---

## 15. ObjectTemplate × RelationshipDefinition

```text
RD.C × OT.DL
    RL when Definition creation introduces Resolution endpoint references

RD.DL × OT.DL
    RL when Definition deletion removes endpoint references
```

Intentional `I`:

```text
RD.RN × OT.DL
RD.CN/R/P/SD/CD/D/DD × any OTV lifecycle/default operation
```

Resolution endpoint lineages are stable ObjectTemplate references and do not depend on exact OTV lifecycle/default state.

Concurrent deletion of an unrelated lineage cannot change overlap semantics among surviving referenced lineages. Existing child/Resolution FKs preserve ancestry/root lifetime.

---

## 16. ObjectTemplate × factual Relationship

Every concrete cell in this block is `I`.

Relationship endpoint admission depends on:

```text
Object.template_id stable lineage
+
RelationshipResolution stable endpoint lineages
```

It does not depend on:

```text
Object exact OTV pin
Object properties
OTV default
OTV lifecycle
```

ObjectTemplate root lifetime is already protected by Objects and Resolution endpoint references. Factual Relationship mutation neither creates nor removes those model-plane references.

---

## 17. Object × RelationshipDefinition

Every concrete cell in this block is `I`.

Object intrinsic/ownership state does not participate in stable RelationshipDefinition certification, RDV lifecycle, property history or default policy.

Physical sharing of ObjectTemplate ancestry reads does not create a semantic mutation predicate.

---

## 18. Object × factual Relationship

### 18.1 Historical metadata

```text
OBJ.RN(object)
× real {REL.C, REL.DC, REL.SC, REL.DEL}
    ES when the Object participates in the transition
```

A DATA_CHANGE no-op and duplicate CREATE conflict emit no event and do not activate `ES`.

### 18.2 Endpoint lifetime

```text
OBJ.DEL(object) × REL.C
    RL when CREATE introduces the Object as an endpoint

OBJ.DEL(object) × REL.DEL
    RL when Relationship deletion removes the current endpoint blocker
```

Intentional `I`:

```text
OBJ.DEL × {REL.DC, REL.SC}
OBJ.DC  × any REL mutation
OBJ.SC  × any REL mutation
OBJ.A   × any REL mutation
OBJ.DET × any REL mutation
```

DATA_CHANGE/SCHEMA_CHANGE preserve the existing endpoint reference; Object deletion is already blocked while the fact remains. Relationship validity does not depend on Object exact schema, properties or ownership.

---

## 19. RelationshipDefinition × factual Relationship

### 19.1 Historical Resolution names

```text
RD.RN
× real {REL.C, REL.DC, REL.SC, REL.DEL}
    ES when the transition belongs to the renamed Definition
```

Duplicate CREATE conflict and DATA_CHANGE no-op do not activate `ES`.

### 19.2 New exact factual binding

Explicit Relationship CREATE:

```text
REL.C(explicit target)
× {RD.P(target), RD.D(target)}
    BA when target lifecycle admission is affected
```

Implicit Relationship CREATE:

```text
REL.C(omitted version)
× {RD.P, RD.SD, RD.CD, RD.D}
    BA + DV when the operation can change the resolved default
       or selected target PUBLISHED state
```

Relationship schema change:

```text
REL.SC × {RD.P(target), RD.D(target)}
    BA when the exact forward target lifecycle is affected
```

Source-version deprecation is `I` for `REL.SC`: a source may be PUBLISHED or DEPRECATED.

### 19.3 Definition/root lifetime

```text
RD.DL × REL.C
    RL when CREATE introduces the current factual reference

RD.DL × REL.DEL
    RL when factual deletion removes the current blocker
```

Intentional `I`:

```text
RD.DL × {REL.DC, REL.SC}
```

The existing fact already references the same stable Definition before and after these operations, so root deletion is already blocked. `REL.SC` still uses target-before-owner physical ordering.

```text
RD.P/RD.D/RD.SD/RD.CD × REL.DC
    I
```

Existing facts remain valid under their persisted exact pin; model lifecycle/default changes never rewrite factual state.

```text
RD.DD × any current REL mutation
    I
```

A valid current fact can never reference a DRAFT version.

---

## 20. Model-root delete interactions

The semantic matrix distinguishes actual reference/lifetime predicates from the conservative physical root-delete gate.

### 20.1 Same aggregate

```text
root internal mutation × same root DELETE
    AL
```

### 20.2 Cross-root references

```text
OT.DL(consumer) × DT.DL(target)
    RL when property references exist

RD.DL(consumer) × DT.DL(target)
    RL when property references exist

RD.DL(consumer) × OT.DL(target)
    RL when Resolution endpoint references exist

OT.DL(consumer A) × OT.DL(target B)
    RL when parent/component references exist
```

Mutual references activate the same `RL` predicate in both directions; no serial order may leave a dangling reference.

### 20.3 Semantically independent root deletes

These remain `I` when no same-root, reference, qualified-name or certified-set scope exists:

```text
DT.DL(A) × DT.DL(B)
RD.DL(A) × RD.DL(B)
unrelated DT.DL × unrelated OT.DL
unrelated DT.DL × unrelated RD.DL
unrelated OT.DL × unrelated RD.DL
```

`MODEL_ROOT_DELETE_GATE` is intentional persistence over-serialization used to make the physical FK/cascade wait graph acyclic. It does not change these semantic classifications.

---

## 21. Multi-predicate cells and composition

A concrete race may activate more than one predicate.

Examples:

```text
RD.P(v2) × RD.P(v3), default null
    VH + DV

REL.C implicit × RD.D(current default)
    BA + DV

REL.C × REL.DEL on same semantic fact
    RF + RA

REL.DEL × REL.DEL same ID
    RS + RA

OT.P consumer × DT.D target
    AM
    plus local LS/DV if the same operation also changes the consumer's
    own lifecycle/default state through another scoped relation
```

The authoritative result is the complete predicate set.

Pairwise predicates also compose across multi-party races. For example, a real Relationship transition racing with two independent Object renames must satisfy `ES` against both rename operations through one coherent metadata statement snapshot.

No multi-party outcome may violate a predicate merely because every isolated pair appears valid.

---

## 22. Realization-critical semantic independence

The following cells are semantically `I` or have a narrower predicate, but the physical realization must still honor the persistence deadlock/progress design.

### 22.1 Existing-owner rebind

```text
OBJ.SC × OT.DL
REL.SC × RD.DL
```

Stable root reference is unchanged, so the semantic root-delete cell is `I`. Nevertheless the target exact version must be acquired before the mutable Object/Relationship owner to prevent child-owner/target-delete inversion.

### 22.2 Preserved declaration reference

```text
OT.R or RD.R preserving one exact DTV pin
× DTV deprecation
    I for BA/AM
```

The DRAFT may retain a historical pin while the DTV becomes DEPRECATED. Differential physical replacement and target lifetime holds must avoid manufacturing a deadlock or transient reference gap.

### 22.3 Definition rename and Relationship create

```text
RD.RN × real REL.C
    ES
```

`ES` requires coherent observation, not generic exclusive serialization. The realization must preserve the delivered progress contract: Relationship CREATE may progress while rename remains open when FK identity protection and metadata observation permit it.

### 22.4 Object rename and Relationship create

```text
OBJ.RN × real REL.C
    ES
```

Object non-key rename must remain compatible with endpoint lifetime protection.

### 22.5 Independent root deletes

```text
semantic = I
physical = intentionally serialized by MODEL_ROOT_DELETE_GATE
```

The gate is an implementation deadlock-prevention measure and cannot leak as a new public conflict code.

---

## 23. PostgreSQL realization handoff

`concurrency.md` must map every non-trivial rule to:

```text
operation pair and scope
predicate set
concurrency owner
complete pre-DML lock plan
advisory gate, if any
row mode and canonical order
fresh post-wait re-read
constraint arbitration
whole-UoW restart or public failure
deterministic PostgreSQL scenario
```

The following persistence requirements are mandatory consequences of the matrix and may not be weakened:

```text
one mutation = one UoW
READ COMMITTED mutation baseline
complete lock plan before DML
at most one advisory gate, acquired before rows
no normal row-lock upgrade
canonical row-class/intra-class ordering
new/rebound FK target before existing owner
inserted/reinserted FK target before child DML
differential declaration replacement
CREATE_NEXT cloned-reference lifetime holds
deterministic closure and event-row ordering
fresh whole-UoW restart for stale optimistic plans
PK/UNIQUE/FK as final arbitration
no supported semantic outcome depends on deadlock victim selection
```

A SQLSTATE `40P01` in a supported deterministic scenario is not a business conflict. It is an architecture/realization defect.

---

## 24. Verification obligations

The delivered deterministic scenario registry remains the baseline and must be extended, not replaced.

At minimum the M2 verification owner must add or broaden scenarios for:

```text
RD version allocation and source eligibility                  VS
RD DRAFT revise/publish/delete generation races               DG + LS
RD distinct-version concurrent publication history            VH
RD default/publication/deprecation races                       DV + LS
RD property binding and DTV lifecycle/default races            BA + DV
RD publication/dependency deprecation                          AM
RD clone/revise/delete lifetime versus DTV root delete         RL
RD root/internal lifetime                                      AL
REL concurrent CREATE with conflict, not convergence           RF
REL DATA_CHANGE/DATA_CHANGE                                    RS
REL DATA_CHANGE/SCHEMA_CHANGE                                  RS
REL SCHEMA_CHANGE/SCHEMA_CHANGE                                RS
REL mutation/DELETE and DELETE/DELETE                          RS + RA
REL explicit/implicit CREATE versus RDV lifecycle/default      BA + DV
REL SCHEMA_CHANGE versus target deprecation/publication        BA
REL CREATE/DELETE versus Definition and endpoint deletes       RL
REL CREATE/DATA_CHANGE/SCHEMA_CHANGE/DELETE rename snapshots   ES
OT/RD distinct publication historical re-certification         VH
CREATE_NEXT cloned-reference versus target delete              RL
mutually referencing model-root deletes                        RL + no 40P01
realization-critical I-cell progress contracts                 no regression
```

Normative concurrency evidence uses real PostgreSQL and independent connections. Sleep-only scheduling, fake repositories and in-process transaction mocks cannot prove these obligations.

---

## 25. Family-block completeness audit

| Block | Classification source | Status |
|---|---|---|
| DT × DT | common version rules + §6 | COMPLETE |
| DT × OT | §11 | COMPLETE |
| DT × OBJ | §13 | COMPLETE — all `I` |
| DT × RD | §12 | COMPLETE |
| DT × REL | §13 | COMPLETE — all `I` |
| OT × OT | common version rules + §7 | COMPLETE |
| OT × OBJ | §14 | COMPLETE |
| OT × RD | §15 | COMPLETE |
| OT × REL | §16 | COMPLETE — all `I` |
| OBJ × OBJ | §8 | COMPLETE |
| OBJ × RD | §17 | COMPLETE — all `I` |
| OBJ × REL | §18 | COMPLETE |
| RD × RD | common version rules + §9 | COMPLETE |
| RD × REL | §19 | COMPLETE |
| REL × REL | §10 | COMPLETE |

```text
mutation census complete        41 / 41
family blocks complete          15 / 15
unordered cells classified      861 / 861
safety predicates               21
new predicates                  VH, RS
unclassified mutation           0
open semantic matrix point      0
```

---

## 26. AS-IS preservation and M2 deltas

The matrix preserves all delivered predicate meanings except the explicit M2 contract deltas.

### Preserved

```text
version allocation and DRAFT freshness
lifecycle/default validity
exact binding admission
active-model consistency
FK lifetime and aggregate lifetime
Object/ownership state predicates
certified stable RelationshipDefinition set
factual uniqueness authority in exact runtime views
exact-ID ABA protection
coherent metadata observation
```

### Intentional M2 changes

```text
RF loser
    delivered -> successful convergence
    M2        -> relationship_fact_conflict

RA same-ID delete waiter
    delivered -> idempotent success
    M2        -> resource_not_found

Relationship current-state races
    delivered -> CREATE/DELETE only
    M2        -> RS covers DATA_CHANGE/SCHEMA_CHANGE/DELETE

Relationship real metadata transitions
    delivered -> CREATE/DELETE
    M2        -> CREATE/DATA_CHANGE/SCHEMA_CHANGE/DELETE
```

### Cross-domain hardening without public semantic change

```text
VH makes already-required schema history concurrency explicit
CREATE_NEXT cloned-reference lifetime is explicitly classified under RL
model-root delete over-serialization remains a physical realization detail
```

No additional public behavior change is authorized.

---

## 27. Contract traceability

Primary ownership:

```text
M2-OUT-02
    safe version lifecycle and default policy

M2-OUT-04
    explicit factual Relationship mutations

M2-OUT-08
    deterministic transactional and concurrency safety
```

Direct acceptance-criterion authority:

```text
M2-AC-15
    DRAFT lost-update prevention

M2-AC-16
    model admission stability

M2-AC-17
    concurrent factual CREATE

M2-AC-18
    concurrent factual mutations and deletion

M2-AC-19
    coherent historical metadata
```

The matrix also supplies concurrency obligations for:

```text
M2-AC-01 ... M2-AC-10
M2-AC-13 ... M2-AC-14
M2-AC-31
```

Shared owners:

```text
domain semantics       -> relationship.md
wire outcomes          -> api.md
physical authorities   -> persistence.md
PostgreSQL mechanism   -> concurrency.md
deterministic evidence -> verification.md
```

---

## 28. Design closure status

```text
canonical mutation census                         CLOSED
all 41 mutations compared                         CLOSED
all 15 family blocks classified                   CLOSED
all 861 unordered cells classified                CLOSED
delivered 19-predicate catalog preserved          CLOSED
VH schema-history predicate                       CLOSED
RS factual Relationship-state predicate           CLOSED
M2 RF conflict outcome                            CLOSED
M2 RA not-found delete outcome                    CLOSED
cross-domain exact binding and dependency scopes  CLOSED
root/reference lifetime scopes                    CLOSED
intentional semantic independence                 CLOSED
persistence hardening handoff                      CLOSED
```

No semantic concurrency decision remains open in this owner.

PostgreSQL realization, progress/deadlock design and deterministic evidence registration have passed architecture review. Executed no-`40P01` evidence remains a mandatory implementation/final-delivery gate, not an architecture-freeze prerequisite.

This document is `FINAL / FROZEN`. Any semantic or technical change requires formal architecture reopening and a renewed cross-document consistency review.
