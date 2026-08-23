# Semantic Concurrency Matrix — Current AS-IS

## Purpose and authority

This document is the authoritative semantic mutation matrix for the current kernel. It defines **what must remain true under concurrency before selecting PostgreSQL mechanisms**.

For every concrete pair of mutations, analysis proceeds in this order:

```text
scope
    -> when do the operations actually interact?

risk
    -> which invalid committed state or interleaving is threatened?

safety predicate
    -> which property must remain true?

allowed outcomes
    -> which serial, convergent or conservative outcomes are valid?
```

Row locks, advisory locks, PK/UNIQUE/FK details, isolation choices and retry realization belong to `concurrency.md`. Deterministic evidence belongs to `verification-concurrency-registry.md`.

The semantic matrix must never be reconstructed from the current lock layout: the guarantee is authoritative and the PostgreSQL mechanism realizes it.

## Canonical mutation census

The current kernel has 41 semantic mutation primitives.

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

### Object / ownership — 7

```text
OBJ.C     CREATE
OBJ.RN    RENAME
OBJ.DC    DATA_CHANGE
OBJ.SC    SCHEMA_CHANGE
OBJ.A     ATTACH
OBJ.DET   DETACH
OBJ.DEL   DELETE
```

### RelationshipDefinition — 10

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
RD.DL     DELETE
```

### Relationship — 4

```text
REL.C     CREATE
REL.DC    DATA_CHANGE
REL.SC    SCHEMA_CHANGE
REL.DEL   DELETE
```

Every future mutation must appear in this census and be compared against **every** existing mutation before its concurrency design is complete.

Read-only operations are not members of this mutation matrix; their snapshot/coherence contracts remain in the owning domain, API and persistence documents.

## Sparse representation

The authoritative matrix is sparse:

1. every concrete cell starts as `I — INDEPENDENT`;
2. a scoped rule below replaces or augments `I` when its concrete scope matches;
3. multiple predicates may apply to one concrete race;
4. the 41 mutations form 861 unordered cells including the diagonal;
5. the exact fifteen family blocks are `DT×DT`, `OT×OT`, `OBJ×OBJ`, `RD×RD`,
   `REL×REL`, `DT×OT`, `DT×OBJ`, `DT×RD`, `DT×REL`, `OT×OBJ`, `OT×RD`,
   `OT×REL`, `OBJ×RD`, `OBJ×REL` and `RD×REL`;
6. a rendered 41×41 table is a derived read model, not the source of truth.

### `I — INDEPENDENT`

`I` means that the concrete pair introduces no shared current semantic safety predicate.

It does **not** promise:

- zero physical row-lock contention;
- zero conservative FK/constraint interaction;
- guaranteed physical parallelism;
- absence of intentional implementation over-serialization.

Example:

```text
OBJ.RN(parent) × OBJ.A(parent, slot, child)
    semantic = I
```

The current realization may still serialize these operations on the same parent row. Such contention is a realization property and must not be reinterpreted as a new domain invariant.

## Safety-predicate catalog

### `NU` — qualified-name uniqueness

**Scope:** two mutations may introduce or reuse the same stable `(namespace, name)` in the same entity kind.

**Risk:** two current lineages own the same qualified name.

**Required property:** at most one current stable model entity owns that qualified name.

**Allowed outcomes:** one create/reuse wins; the conflicting candidate fails. No partial aggregate survives.

### `VS` — coherent version set

**Scope:** concurrent mutations use or change one lineage version set for allocation or source eligibility.

**Risk:** duplicate allocation, allocation from a stale maximum, or source validation against a version set that never existed.

**Required property:** allocation and source eligibility are derived from one serially coherent current version set.

**Allowed outcomes:** operations appear in a valid serial order; a waiter re-evaluates `max(existing)+1` and source eligibility after wake-up.

### `DG` — DRAFT generation freshness

**Scope:** mutations are based on the same exact DRAFT generation / `expected_revision`.

**Risk:** incompatible changes based on one generation both commit.

**Required property:** operations based on one exact generation cannot independently commit incompatible outcomes.

**Allowed outcomes:** one generation consumer wins; later incompatible operations observe stale generation or invalid lifecycle state.

### `LS` — lifecycle state

**Scope:** mutations act on the lifecycle of the same exact version.

**Risk:** illegal, duplicate or non-monotonic transitions.

**Required property:** committed transitions are explainable by a valid order of:

```text
DRAFT -> PUBLISHED -> DEPRECATED
```

**Allowed outcomes:** one valid real transition per state boundary; post-wait operations recheck current status and either proceed or fail/no-op according to the owning command contract.

### `DV` — default validity

**Scope:** mutations read or change lineage default policy or the lifecycle of the selected/current default.

**Risk:** default points to a non-PUBLISHED or wrong-lineage exact version, or first-publish/default policy reflects no serial order.

**Required property:** `default_version` is NULL or an exact same-lineage PUBLISHED version.

**Allowed outcomes:** first serial publisher may establish a missing default; set/clear/deprecate/publish outcomes follow one coherent default-policy order.

### `VH` — published version-history coherence

**Scope:** concurrent publication or revision activity can make two individually
valid exact-version candidates jointly violate historical declaration continuity.

**Risk:** published property/component history contains a renamed or rebound
semantic member, an unapproved cardinality narrowing, or incompatible histories
that were each certified against a stale prefix.

**Required property:** publication re-certifies the complete committed history of
the lineage/member set after every wait.

**Allowed outcomes:** one candidate publishes and the waiter re-certifies against
it; the waiter publishes only if the combined history remains valid, otherwise it
fails without partial state.

### `BA` — new binding admission

**Scope:** a mutation creates/rebinds a lifecycle-sensitive exact dependency or resolves an implicit default into a persisted exact pin.

**Risk:** a new committed binding points to an exact dependency that was not PUBLISHED through admission/commit.

**Required property:** the selected exact dependency remains PUBLISHED through the new binding/certification commit.

**Allowed outcomes:** binding wins and lifecycle change cannot invalidate it; lifecycle/delete wins and the new binding fails. Implicit selection and exact pin come from one coherent default/lifecycle state.

Cloning an already-persisted historical exact pin through `CREATE_NEXT` is not a new admission.

### `AM` — active model graph

**Scope:** concurrent operations activate/deactivate a direct PUBLISHED consumer edge or deprecate its exact dependency.

**Risk:** committed active edge:

```text
PUBLISHED consumer -> non-PUBLISHED dependency
```

**Required property:** every direct lifecycle-sensitive dependency of a PUBLISHED consumer remains PUBLISHED.

**Allowed outcomes:** consumer activation wins and dependency deprecation is blocked; dependency deprecation wins and consumer publication fails; blocker removal may permit deprecation or a conservative failure.

### `RL` — cross-aggregate reference lifetime

**Scope:** one mutation creates, keeps or removes a current cross-aggregate reference while another deletes its target.

**Risk:** dangling current reference or implicit semantic cascade.

**Required property:** reference and target lifetime resolve to a serially valid winner.

**Allowed outcomes:**

```text
reference wins
    -> target delete cannot commit

target delete wins
    -> new reference cannot commit

reference removal first
    -> target delete may become admissible
```

A delete that still observes the current blocker may fail conservatively.

### `AL` — aggregate/owned-child lifetime

**Scope:** one mutation acts on an aggregate or owned child while another deletes the same aggregate.

**Risk:** orphan child state, partial aggregate, mutation after delete, or resurrection.

**Required property:** aggregate lifetime and owned-child mutation follow one serial order.

**Allowed outcomes:** child/internal mutation completes before aggregate deletion, or aggregate delete wins and later mutation cannot commit against/resurrect the absent aggregate.

### `ML` — metadata last-write-wins

**Scope:** concurrent writes target the same metadata field whose contract is last-write-wins, currently `description`.

**Risk:** torn/merged metadata value or an invented optimistic-conflict contract.

**Required property:** each write is atomic and the final value is exactly one complete committed candidate.

**Allowed outcomes:** either committed candidate may be final; no merge or partial value.

### `OS` — complete Object state

**Scope:** intrinsic mutations on the same Object depend on or produce the complete current Object snapshot.

**Risk:** lost JSONB update, candidate derived from stale state, or lifecycle snapshots that never matched a committed Object generation.

**Required property:** committed Object state and lifecycle snapshots are explainable by a serial sequence of semantic Object transitions.

**Allowed outcomes:** waiter reloads/rederives from the current committed Object; complete state/event transition commits or rolls back atomically.

### `RS` — complete factual Relationship state

**Scope:** DATA_CHANGE, SCHEMA_CHANGE and DELETE act on the same factual
Relationship state.

**Risk:** lost property update, stale source pin, invalid forward migration,
mutation after deletion or lifecycle snapshots that do not describe committed
state.

**Required property:** exact pin, complete property map and transition events are
serially explainable from a fresh protected factual state.

**Allowed outcomes:** DATA_CHANGE may become a no-op after waiting; schema
migration rechecks its source and target; deletion wins or follows a complete
mutation, and a later mutation observes absence.

### `PO` — parent schema / ownership coherence

**Scope:** `ATTACH` or `DETACH` races with `SCHEMA_CHANGE` of the **parent** Object.

**Risk:** a committed outgoing edge is not valid against the parent's committed current exact schema.

**Required property:** every committed outgoing edge resolves to the same current `SlotSemanticKey` and compatible child under the parent's committed exact schema.

**Allowed outcomes:** ATTACH first makes schema change observe/preserve-or-reject the edge; schema change first makes ATTACH validate against the new schema; DETACH may remove a blocker before migration.

### `OF` — ownership fact

**Scope:** ATTACH/DETACH operations concern the same child/current ownership fact.

**Risk:** duplicate transition/event, removal of the wrong edge, implicit move, or fact sequence that has no serial explanation.

**Required property:** the child evolves serially between:

```text
detached
or
attached exactly to (parent, slot)
```

**Allowed outcomes:** identical ATTACH/DETACH converge with one real transition/event; DETACH never removes a different edge; ATTACH never performs an implicit move; ATTACH×DETACH has a serially explainable final fact/event sequence.

### `SO` — single owner

**Scope:** concurrent ATTACH candidates use the same child with different desired `(parent, slot)` facts.

**Risk:** one child has two current owners.

**Required property:** each child has at most one current owner/slot.

**Allowed outcomes:** at most one different desired ownership fact commits; the other candidate fails after final persistence arbitration/re-evaluation.

### `OC` — ownership acyclicity

**Scope:** concurrent edge additions can jointly create a cycle although each candidate is locally valid on its initial snapshot.

**Risk:** committed ownership graph is cyclic.

**Required property:** the committed ownership graph remains acyclic.

**Allowed outcomes:** only a cycle-free subset commits; waiter evaluates the protected graph from a fresh post-gate snapshot; concurrent edge removal may permit the candidate or conservative rejection.

### `RC` — certified RelationshipDefinition set

**Scope:** RelationshipDefinition CREATE/RENAME and concurrent removal of blocking Definitions modify the global certified interpretation set.

**Risk:** equivalent Definitions or cross-Definition Resolution conflicts coexist.

**Required property:** the committed Definition set is semantically non-duplicated and cross-definition conflict-free.

**Allowed outcomes:** at most one incompatible candidate commits; deletion may remove a blocker and make a later candidate admissible; conservative failure is permitted when the candidate observed the blocker.

### `RF` — factual Relationship uniqueness

**Scope:** concurrent `REL.C` requests represent the same fact through reciprocal selectors, symmetric inverse assignment or inheritance-overlap equivalent views.

**Risk:** duplicate factual Relationship identities, partial/multiple closure, or duplicate creation event sets.

**Required property:** exactly one current factual Relationship represents the semantic fact.

**Allowed outcomes:** one candidate creates the fact; every current-owner loser
reports `relationship_fact_conflict` after complete rollback/fresh
classification. If the owner disappeared, an approved bounded fresh-UoW restart
may rederive the candidate. The current fact has one complete runtime closure and
one creation event set.

### `RA` — Relationship exact-ID lifetime / ABA

**Scope:** create/delete/retry occurs around the same semantic fact and an exact factual identity.

**Risk:** stale `DELETE(X)` deletes a recreated equivalent fact `Y`, or same-ID delete emits multiple real deletion event sets.

**Required property:** `DELETE(X)` affects only exact factual identity `X`.

**Allowed outcomes:** concurrent same-ID deletes produce one `204`, one `404` and
one real delete/event set; after X is removed and equivalent Y is created, late
`DELETE(X)` returns not found and Y remains.

### `ES` — Relationship event metadata snapshot

**Scope:** a real factual Relationship transition races with mutable Definition/Object display metadata captured in the complete lifecycle event set.

**Risk:** one event set mixes half-old/half-new Definition names or incoherent endpoint display names.

**Required property:** the complete event set is derived from coherent committed metadata observations made by the Relationship mutation.

**Allowed outcomes:** all Definition names in the set are old or all are new according to one committed snapshot; Object display metadata comes from a coherent observation. Generic writer serialization is not required when snapshot coherence is preserved.

## Canonical sparse rules

Any concrete pair not matched below remains `I`.

### DataType × DataType

```text
DT.C × DT.C
    NU if same (namespace, name)

DT.C × DT.DL
    NU if CREATE reuses the qualified name of the lineage being deleted

DT.CN × DT.CN
    VS if same lineage

DT.CN × DT.DD
    VS if same lineage and removing the DRAFT changes the relevant version set

{DT.R, DT.P, DT.DD} × {DT.R, DT.P, DT.DD}
    DG if same exact DRAFT generation

DT.P(vA) × DT.P(vB)
    DV if same lineage and missing-default/first-publish policy is material

DT.P × {DT.SD, DT.CD}
{DT.SD, DT.CD} × {DT.SD, DT.CD}
    DV if same lineage

{DT.SD, DT.CD} × DT.D
    DV when deprecation targets the selected/current default

DT.P × DT.D
    LS if same exact version
    plus DV when default state is material

DT.D × DT.D
    LS if same exact PUBLISHED version

same-lineage internal mutation × DT.DL
    AL when the internal mutation acts on the aggregate being removed

DT.DESC × DT.DESC
    ML if same lineage
```

All other DT×DT scopes are `I` unless another scoped rule above applies.

### ObjectTemplate × ObjectTemplate — same-lineage core

The DataType lineage/version rules apply symmetrically through ObjectTemplate/ObjectTemplateVersion identities:

```text
NU / VS / DG / LS / DV / AL / ML
```

### ObjectTemplate × ObjectTemplate — cross-lineage dependencies

```text
OT.C or OT.R
× parent lifecycle/default mutation
    BA when the candidate creates/rebinds a new exact parent OTV

OT.P(consumer) × OT.D(dependency)
    AM when the exact parent edge targets the dependency

OT.D(consumer) × OT.D(dependency)
    AM when consumer deprecation removes an active blocker

OT.DL(consumer lineage) × OT.D(dependency)
    AM when deletion removes active exact-parent consumers

OT.C or OT.R × OT.DL(target lineage)
    RL when the candidate adds/removes a parent/component reference

OT.DD(consumer DRAFT) × OT.DL(target lineage)
    RL when DRAFT removal removes a current blocker

OT.DL(consumer lineage) × OT.DL(target lineage)
    RL when the consumer contains an external reference to the target
```

`OT.CN` cloning an existing exact pin is not a new `BA` admission.

### DataType × ObjectTemplate

```text
OT.C or OT.R × DTV lifecycle/default mutation
    BA when a property creates/rebinds an exact DTV

OT.C or OT.R × DT.DL
    RL when the candidate adds/removes a property reference

OT.P × DT.D
    AM when publication would activate a property edge to the DTV

OT.D × DT.D
    AM when consumer deprecation removes an active blocker

OT.DD × DT.DL
    RL when DRAFT removal removes the current DTV-lineage blocker

OT.DL × DT.D
    AM when OT-lineage deletion removes active OTV consumers

OT.DL × DT.DL
    RL when the OT lineage contains property references to the DT lineage
```

All other DT×OT scopes are `I`.

### ObjectTemplate × Object / ownership

```text
OBJ.C × target OTV lifecycle/default mutation
    BA when the mutation affects explicit/default target admission

OBJ.C × OT.DL
    RL when CREATE introduces Object -> exact OTV reference

OBJ.SC × target OTV PUBLISH/DEPRECATE
    BA when the mutation concerns the exact schema-change target

OBJ.DEL × OT.DL
    RL when Object deletion removes a current exact OTV reference
```

Intentional:

```text
OBJ.SC × OT.DL = I
```

because `Object.template_id` is unchanged and the lineage reference exists before and after schema change.

`OBJ.RN`, `OBJ.DC`, `OBJ.A` and `OBJ.DET` consume already-bound historical schema and do not create new OTV lifecycle admission.

### Object / ownership internal

```text
{OBJ.RN, OBJ.DC, OBJ.SC, OBJ.DEL}
× same set
    OS when same Object and both are real intrinsic/current-state transitions

OBJ.SC(parent) × OBJ.A(parent, slot, child)
    PO

OBJ.SC(parent) × OBJ.DET(parent, slot, child)
    PO

OBJ.A(parent, slot, child) × identical OBJ.A
    OF

OBJ.A(P1,S1,C) × OBJ.A(P2,S2,C)
    SO when desired ownership differs

OBJ.A(edge1) × OBJ.A(edge2)
    OC when the combined committed graph could form a cycle

OBJ.A × OBJ.DET
    OF when the same child/current fact is involved

OBJ.DET × OBJ.DET
    OF when the same child/current fact is involved

OBJ.A × OBJ.DEL
    RL when ATTACH creates a current reference to the Object being deleted

OBJ.DET × OBJ.DEL
    RL when DETACH removes a current ownership blocker
```

Intentional `I` examples:

```text
OBJ.RN(parent) × OBJ.A(parent, slot, child)
OBJ.DC(parent) × OBJ.A(parent, slot, child)
OBJ.SC(child)  × OBJ.A(parent, slot, child)
```

The PostgreSQL realization may intentionally over-serialize some of these.

### RelationshipDefinition internal

```text
RD.C × RD.C
    RC when candidates are equivalent or cross-conflicting

RD.C × RD.RN
    RC when create and renamed candidates may conflict/equivalate

RD.RN × RD.RN
    RC for same Definition candidate transition or conflicting different Definitions

RD.C or RD.RN × RD.DL(other)
    RC when the deleted Definition is a blocker of the candidate set

RD.RN × RD.DL
    AL when same Definition

RD.DL × RD.DL
    AL when same Definition

RD.CN × RD.CN
    VS when same Definition

RD.CN × RD.DD or source RD.P
    VS when version-set/source eligibility overlaps

RD.R / RD.P / RD.DD on the same exact DRAFT
    DG + LS

RD.P / RD.SD / RD.CD / RD.D on one Definition
    DV when publication/default/deprecation policy overlaps

RD.P × RD.P on distinct versions with shared property history
    VH (+ DV when first-default policy participates)

RD.C / RD.R × DTV lifecycle/default mutation
    BA when an exact property dependency is admitted

RD.P × DTV.D
    AM + VH for active dependency and history recertification

RD.CN / RD.R × DataType root delete
    RL for cloned or rebound exact property references

same-Definition internal mutation × RD.DL
    AL
```

Definition DELETE removes a member of the certified set and cannot itself introduce a new conflict.

### ObjectTemplate × RelationshipDefinition

```text
RD.C × OT.DL
    RL when the candidate introduces a Resolution endpoint reference

RD.DL × OT.DL
    RL when deletion removes the endpoint reference
```

`RD.RN × OT.DL = I` because endpoint references do not change. Exact OTV lifecycle/default operations are independent from RelationshipResolution, which references stable template lineages.

### RelationshipDefinition × Relationship runtime

```text
RD.RN × real REL.C
    ES when same Definition

RD.RN × real REL.DEL
    ES when same Definition

RD.DL × REL.C
    RL when CREATE uses the Definition being deleted

RD.DL × REL.DEL
    RL when Relationship deletion removes the current blocker

RD.P / RD.D / RD.SD / RD.CD × REL.C or REL.SC
    BA + DV when exact/default factual admission overlaps
```

A failed duplicate `REL.C` creates no lifecycle event set and therefore does not
activate `ES`.

### Relationship runtime internal

```text
REL.C × REL.C
    RF when both requests represent the same absent fact

REL.C × REL.DEL
    RA when DELETE targets the current factual identity of the same fact

REL.DC × REL.DC
    RS when same relationship_id

REL.DC × REL.SC
    RS when same relationship_id

REL.SC × REL.SC
    RS + BA when same relationship_id and target admission overlaps

REL.DC or REL.SC × REL.DEL
    RS + RA when same relationship_id

REL.DEL × REL.DEL
    RA when same relationship_id
```

Different factual Relationships are normally independent; the Relationship graph has no ownership-style global acyclicity predicate.

### Object × Relationship runtime

```text
OBJ.RN(object) × real REL.C/REL.DC/REL.SC/REL.DEL
    ES when the Object participates in the transition

OBJ.DEL(object) × REL.C
    RL when CREATE introduces a current endpoint reference

OBJ.DEL(object) × REL.DEL
    RL when Relationship removal removes the current blocker

OBJ.DEL(object) × REL.DC/REL.SC
    RL when the factual state mutation retains the endpoint reference
```

Intentional `I`:

```text
OBJ.DC  × REL.C/REL.DEL
OBJ.SC  × REL.C/REL.DEL
OBJ.A   × REL.C/REL.DEL
OBJ.DET × REL.C/REL.DEL
```

Relationship admission depends on stable `Object.template_id`, not current properties, exact template version or ownership state.

### Completely independent cross-domain blocks

All concrete cells in these blocks are `I`:

```text
DataType × Object
Object × RelationshipDefinition
```

This independence is evaluated, not omitted. Architectural reasons include:

- Object runtime consumes DataType contracts through already-certified exact ObjectTemplate model state;
- RelationshipDefinition property schemas bind exact DataTypeVersions and are
  classified by `BA`, `AM`, `VH` and `RL` where their predicates overlap;
- runtime Relationship endpoint admission uses stable ObjectTemplate lineage assignment;
- RelationshipResolution already owns endpoint-lineage references;
- Object/ownership runtime state does not participate in RelationshipDefinition conflict certification.

## Multi-predicate cells

A concrete race may activate multiple predicates. The authoritative result is a **set** of predicates, not an arbitrarily selected primary predicate.

For example, a same-lineage lifecycle interaction that also participates in a cross-lineage active dependency may require both a local lifecycle/default predicate and `AM`.

## Predicate vs mechanism

A predicate never implies one specific technical mechanism.

Examples:

```text
ES
    -> coherent observation
    -> not generic exclusive serialization

RL
    -> valid lifetime ordering
    -> currently realized primarily by semantic admission + FK RESTRICT

RF
    -> factual convergence
    -> currently realized through exact-view uniqueness + fresh-UoW restart
```

`concurrency.md` must document any intentional serialization applied to an `I` cell as realization over-serialization rather than redefining the domain.

## Realization and verification traceability

Every non-trivial scoped rule must map to:

```text
operation A / operation B
scope qualifier
semantic predicate set
concurrency owner / authority
PostgreSQL mechanism
isolation assumption
retry or convergence rule
canonical real-PostgreSQL scenario
```

Required chain:

```text
Invariant
    -> semantic matrix rule
    -> safety predicate
    -> PostgreSQL realization
    -> deterministic verification scenario
```

If a non-trivial rule cannot be mapped to a concrete, testable authority/mechanism, concurrency design is not closed.

## Evolution rule

Before implementing any future mutation primitive:

1. add it to the canonical census;
2. compare it with every existing mutation;
3. reuse an existing predicate or introduce a justified new one;
4. update PostgreSQL realization in `concurrency.md`;
5. add/update deterministic scenarios in `verification-concurrency-registry.md`.

A feature must not bypass semantic analysis by adding an isolated lock or constraint first.
