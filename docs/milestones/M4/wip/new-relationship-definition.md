# M4 — New RelationshipDefinition intent

**Status:** INTENT DRAFT / ACTIVE REVIEW FRONTIER / WIP / NON-NORMATIVE

## Purpose

This document is the upstream intent owner for the current M4 revalidation of `RelationshipDefinition` / `RelationshipResolution` semantics and relational representation.

It exists because the factual Relationship review exposed downstream anomalies whose root cause may be the current Definition/Resolution model rather than the factual Relationship implementation itself. The factual `relationship.md` review is therefore frozen until this upstream model has been made coherent enough to revalidate its assumptions.

This file is deliberately an **intent draft**, not a normative architecture decision and not an implementation authorization. It records the candidate model we have derived so far so that it can be inspected for missing cases before any downstream contract, persistence, runtime-closure or concurrency work is resumed.

Current scope is intentionally narrow:

```text
IN SCOPE
    semantic meaning of RelationshipResolution
    stable vs mutable Resolution attributes
    what it means for a relationship meaning to be already expressed
    compact declared Resolution representation
    effective materialized Resolution semantic space
    relational candidate for that materialization
    model-plane vs data-plane responsibility split

NOT YET CLOSED
    final symmetric Definition persisted shape/cardinality
    final non-symmetric Definition persisted shape/cardinality
    final public RelationshipDefinition API
    exact CREATE/DELETE/REVISE lifecycle changes
    physical DDL/FK/index realization
    concurrency/locking protocol
    factual Relationship relational model
    runtime factual Relationship closure
```

---

# 1. Starting semantic objective

A `RelationshipResolution` expresses one directed semantic relationship over two ObjectTemplate compatibility spaces.

Conceptually, a declared Resolution is:

```text
A --rel1--> B
```

where:

```text
A
    declared from-template compatibility-space root

B
    declared to-template compatibility-space root

rel1
    semantic name of this specific Resolution/perspective
```

Because ObjectTemplate inheritance is lineage-polymorphic, the declaration applies not only to the exact roots `A` and `B`, but to every exact descendant pair admitted by those roots.

Let:

```text
Desc(T) = T + every current stable ObjectTemplate descendant of T
```

Then the effective semantic meaning of:

```text
A --rel1--> B
```

is the complete set:

```text
for every A' in Desc(A)
for every B' in Desc(B)

    A' --rel1--> B'
```

The model-plane therefore has a compact declaration and an effective semantic closure.

---

# 2. Candidate invariant — Resolution `name` is stable semantic state

The current redesign candidate treats `RelationshipResolution.name` as part of the stable semantic contract of that specific Resolution.

Candidate meaning:

```text
RelationshipResolution
    id                          stable identity
    relationship_definition_id stable membership
    from_template_id            stable declared compatibility-space root
    to_template_id              stable declared compatibility-space root
    name                         stable semantic name
```

`name` remains an attribute of the **specific Resolution**, not a name of the `RelationshipDefinition` root.

Example non-symmetric Definition:

```text
Resolution R1
    VM --runs_on--> Hypervisor

Resolution R2
    Hypervisor --hosts--> VM
```

`runs_on` and `hosts` are the stable semantic names of the two distinct perspectives.

Under this candidate, changing a Resolution name is not a display-metadata rename of the same semantic contract. A change such as:

```text
hosts -> runs
```

changes the expressed relationship meaning and therefore cannot be treated as an ordinary mutable `RelationshipDefinition.RENAME` operation preserving the same semantic Definition contract.

The exact lifecycle consequence is still OPEN, but the direction is:

```text
Resolution semantic name changes
    -> semantic contract changes
    -> do not silently mutate an already-admitted stable Resolution meaning
```

No schema-column relocation is implied: `name` remains owned by `relationship_resolutions`.

---

# 3. RATIFIED semantic invariant — already-expressed relationships cannot be redefined

The primary semantic objective is not merely to avoid structurally identical Definition rows. It is to avoid expressing a relationship meaning that is already expressed in the model.

At the effective exact-template level, one atomic directed semantic relationship is represented by:

```text
(
    exact_from_template_id,
    stable_resolution_name,
    exact_to_template_id
)
```

This tuple is the **semantic cell** of the effective Relationship model.

RATIFIED semantic rule:

```text
the same semantic cell must not be expressed more than once
```

Therefore two declared Resolutions are repetitive/conflicting whenever their effective expansions contain at least one identical semantic cell, regardless of whether they belong to:

```text
the same RelationshipDefinition
or
two different RelationshipDefinitions
```

This gives one general notion of repetition:

```text
same exact from-template
+
same stable Resolution name
+
same exact to-template

=> same relationship meaning is being expressed again
```

The rule deliberately depends on semantic meaning, not on:

```text
relationship_definition_id
resolution_id
```

Those identify owners of meaning; they do not make an already-expressed semantic cell different.

Equivalently, for every two distinct Resolution declarations `R1 != R2`, if `E(R)` denotes the complete effective semantic-cell expansion of `R`, then the model requires:

```text
E(R1) INTERSECT E(R2) = EMPTY
```

This invariant is global: it applies both intra-Definition and inter-Definition.

---

# 4. Declared source of truth

The compact declaration remains the authoritative source model.

Candidate declared shape, preserving the current basic table ownership:

```text
relationship_definitions
    id
    symmetric
    default_version

relationship_resolutions
    id
    relationship_definition_id
    from_template_id
    to_template_id
    name
```

At this checkpoint:

```text
relationship_definitions
    -> stable Definition root / grouping
    -> persisted explicit symmetric/asymmetric authoring intent

relationship_resolutions
    -> compact declared semantic perspectives
    -> declared endpoint compatibility-space roots
    -> stable semantic Resolution names
```

The existing version/property family remains conceptually separate and is not redesigned by this draft yet:

```text
relationship_definition_versions
relationship_definition_properties
```

No decision in this intent currently changes their version/property responsibilities.

---

# 5. Effective materialized semantic closure

The redesign introduces a candidate model-plane materialization of the complete exact-template semantic space generated by every declared Resolution.

Working name:

```text
relationship_resolution_space
```

Conceptual rows:

```text
relationship_resolution_space
    relationship_definition_id
    resolution_id
    from_template_id
    name
    to_template_id
```

Here:

```text
resolution_id
    owner declared Resolution

relationship_definition_id
    owner Definition identity / convenient coherence carrier

from_template_id
    exact effective ObjectTemplate member of the declared from-space

name
    stable semantic name inherited from the owning Resolution

to_template_id
    exact effective ObjectTemplate member of the declared to-space
```

For one declared directional semantic perspective:

```text
R1: A --rel1--> B
```

its materialized rows are exactly:

```text
Desc(A) x {rel1} x Desc(B)
```

Example:

```text
A
├── A1
└── A2

B
├── B1
└── B2
```

produces for `R1`:

```text
A   rel1 B
A   rel1 B1
A   rel1 B2
A1  rel1 B
A1  rel1 B1
A1  rel1 B2
A2  rel1 B
A2  rel1 B1
A2  rel1 B2
```

If the Definition also has the reciprocal distinct semantic perspective:

```text
R2: B --rel2--> A
```

then `R2` materializes independently as:

```text
Desc(B) x {rel2} x Desc(A)
```

for example:

```text
B   rel2 A
B   rel2 A1
B1  rel2 A
B1  rel2 A2
B2  rel2 A1
...
```

A semantic name does not automatically materialize in the reverse direction. The reverse orientation exists only when the Definition semantics require it, either under the same name for a symmetric relationship or under the distinct reciprocal name for an asymmetric relationship.

This table is derived effective knowledge, not the compact authoring source.

---

# 6. RATIFIED semantic ownership; physical uniqueness still candidate

Given the stable-name direction and the ratified no-repetition invariant above, the semantic ownership key of the effective space is:

```text
(
    from_template_id,
    name,
    to_template_id
)
```

RATIFIED semantic meaning:

```text
one exact directed relationship meaning
    -> exactly one owning Resolution globally
```

A collision may be:

```text
INTRA-DEFINITION
    two Resolution expansions of the same Definition attempt to express
    the same semantic cell

INTER-DEFINITION
    a candidate Definition attempts to express a semantic cell already
    owned by another Definition
```

The same semantic authority therefore detects both malformed/redundant internal Definition shape and cross-Definition repetition.

A strong relational realization candidate is:

```text
UNIQUE (
    from_template_id,
    name,
    to_template_id
)
```

The exact physical choice between `PRIMARY KEY`, `UNIQUE`, explicit prevalidation plus final unique arbitration, or another DDL realization remains OPEN. The semantic single-owner invariant itself is ratified; only its exact physical enforcement is not yet closed.

---

# 7. Derived observation — symmetric overlap problem moves to the model plane

The materialized semantic-space representation exposes why some currently-admitted symmetric shapes may be intrinsically redundant.

Suppose:

```text
A
└── B
```

and a symmetric Definition is represented by reciprocal semantic perspectives with the same stable name:

```text
P1: A --rel--> B
P2: B --rel--> A
```

Then:

```text
P1 -> Desc(A) x {rel} x Desc(B)
P2 -> Desc(B) x {rel} x Desc(A)
```

Because:

```text
Desc(B) is a subset of Desc(A)
```

both expansions contain identical semantic cells in the overlap, for example:

```text
(B1, rel, B2)
```

when `B1` and `B2` are descendants of `B`.

Therefore the same exact relationship meaning is expressed twice **inside the Definition itself**.

This is a strong signal that the earlier runtime symptom (multiple equivalent runtime rows) is downstream of a model-plane semantic overlap.

This intent does **not yet freeze** the final symmetric persisted shape. The important observation is:

```text
a candidate Definition whose own effective perspective expansions collide
is semantically redundant before any factual Relationship exists
```

---

# 7A. RATIFIED domain invariant — symmetric overlapping endpoint spaces must coincide

The symmetric topology question is first a domain question, not a relational-model capability question.

Assume:

```text
A <: B
```

Then the following symmetric declarations express three different admissible fact spaces:

```text
A --rel--> A
    -> both endpoints belong to Desc(A)

A --rel--> B
    -> both endpoints belong to Desc(B)
       and at least one endpoint belongs to Desc(A)

B --rel--> B
    -> both endpoints belong to Desc(B)
```

The middle form is therefore not merely a broader/narrower ordinary relationship type. It encodes an applicability policy of the form:

```text
at least one endpoint must belong to subtype-space A
```

RATIFIED domain decision:

```text
a symmetric RelationshipDefinition is not the model-plane construct used to
encode such endpoint-presence policies
```

Therefore, whenever the two declared symmetric endpoint compatibility spaces overlap, they must be identical.

With the current single-inheritance ObjectTemplate model:

```text
A == B
    -> allowed

A ancestor-of B, A != B
    -> forbidden symmetric declaration

B ancestor-of A, A != B
    -> forbidden symmetric declaration
```

Equivalently:

```text
symmetric endpoint compatibility spaces
    -> IDENTICAL or DISJOINT
    -> never DISTINCT-BUT-OVERLAPPING
```

This rule is semantic/domain-driven. It is not justified by an inability to materialize the overlap: the model can represent the resulting fact space, but that fact space is considered an endpoint-applicability policy and therefore belongs outside the core RelationshipDefinition concept.

---

# 7B. RATIFIED domain invariant — disjoint endpoint spaces share Definition-level reciprocal topology, while semantic-name applicability remains directional

Let the two endpoint compatibility spaces be disjoint:

```text
Desc(A) INTERSECT Desc(B) = EMPTY
```

A RelationshipDefinition between those spaces is a genuine cross-domain relationship: every admitted fact necessarily connects one member of `Desc(A)` with one member of `Desc(B)`.

RATIFIED domain decision:

```text
for disjoint endpoint spaces, symmetric and asymmetric Definitions share the
same reciprocal endpoint-space pairing at Definition level
```

At the Definition level both describe a fact connecting the two spaces:

```text
Desc(A) <-> Desc(B)
```

This does **not** mean that every semantic name is applicable in both directions.

For a symmetric Definition, reciprocal observation preserves the same name, so that one semantic name covers both orientations:

```text
SYMMETRIC
    A --rel--> B
    B --rel--> A

effective cells for rel:
    Desc(A) x {rel} x Desc(B)
    UNION
    Desc(B) x {rel} x Desc(A)
```

For an asymmetric Definition, each semantic name is directional and covers exactly one reciprocal orientation:

```text
ASYMMETRIC
    A --rel1--> B
    B --rel2--> A
    rel1 != rel2

rel1 effective cells:
    Desc(A) x {rel1} x Desc(B)

rel2 effective cells:
    Desc(B) x {rel2} x Desc(A)
```

Therefore an asymmetric Definition does **not** imply:

```text
B --rel1--> A
or
A --rel2--> B
```

For example:

```text
VirtualMachine --runs_on--> Hypervisor
Hypervisor     --hosts----> VirtualMachine
```

admits `runs_on` only in the `VirtualMachine -> Hypervisor` orientation and `hosts` only in the reciprocal `Hypervisor -> VirtualMachine` orientation.

Because the endpoint spaces are disjoint, a symmetric Definition can materialize the same name in both reciprocal orientations without creating a duplicate semantic cell:

```text
(A', rel, B') != (B', rel, A')
```

The persisted representation is still OPEN. In particular, this checkpoint does not decide whether the reciprocal semantic perspectives require two stored `relationship_resolutions` or can be derived from a more compact declaration.

---

# 7C. RATIFIED authoring invariant — symmetry is explicit client intent and persisted stable Definition state

Once a complete Definition exists, symmetric/asymmetric semantics may be recognizable from the complete reciprocal perspective naming. That derivability does not remove the need for explicit client intent at Definition authoring time.

If a client supplies only one semantic name, the server cannot safely infer whether:

```text
1. the client intends a symmetric relationship
or
2. the client intends an asymmetric relationship but omitted the reciprocal name
```

RATIFIED domain/API-authoring decision:

```text
symmetric is required explicit client intent
```

The server therefore does not infer symmetry from request shape or omitted reciprocal naming.

The intent is persisted on the stable Definition root:

```text
relationship_definitions.symmetric
```

and is stable for the Definition lifetime.

Its semantic role is:

```text
symmetric = true
    reciprocal observation preserves the same semantic name

symmetric = false
    reciprocal observation requires a distinct semantic name
```

Definition CREATE must validate the complete perspective semantics against the explicitly supplied intent. `symmetric` may therefore be redundant with an already-complete certified Definition state, but that redundancy is intentional:

```text
client intent
    -> explicit
    -> never inferred from omission

persisted Definition state
    -> records that intent directly

perspective semantics
    -> must be coherent with the persisted intent
```

This checkpoint does not yet close the exact public request DTO or the minimal persisted Resolution-row cardinality.

---

# 7D. RATIFIED domain invariant — asymmetric Definitions require exactly two distinct reciprocal semantic names

An asymmetric RelationshipDefinition represents one relationship fact whose two endpoint roles are not semantically peers.

RATIFIED domain decision:

```text
symmetric = false
    -> exactly two reciprocal semantic perspectives
    -> exactly two distinct stable semantic names
```

For declared endpoint roots `A` and `B`, the complete asymmetric semantics are:

```text
P1
    A --rel1--> B

P2
    B --rel2--> A

rel1 != rel2
```

The reciprocal topology is part of the same Definition:

```text
P2.from = P1.to
P2.to   = P1.from
```

Each name remains strictly directional:

```text
E(rel1) = Desc(A) x {rel1} x Desc(B)
E(rel2) = Desc(B) x {rel2} x Desc(A)
```

There is no automatic reverse applicability of either individual name.

Example:

```text
VirtualMachine --runs_on--> Hypervisor
Hypervisor     --hosts----> VirtualMachine
```

means:

```text
VirtualMachine runs_on Hypervisor     -> valid semantic direction
Hypervisor hosts VirtualMachine       -> valid reciprocal semantic direction

Hypervisor runs_on VirtualMachine     -> not expressed by this Definition
VirtualMachine hosts Hypervisor       -> not expressed by this Definition
```

A one-name asymmetric declaration is therefore incomplete rather than a distinct supported relationship shape. Without the second reciprocal name there is no complete asymmetric semantic contract and no reliable distinction from symmetric authoring intent.

This checkpoint is a domain semantic/cardinality decision only. It does **not** yet decide whether the two reciprocal semantic perspectives must be persisted as two autonomous `relationship_resolutions` rows or can be represented by a different compact TO-BE relational structure.

---

# 8. Model-plane cost is intentionally traded for data-plane simplicity

The materialized space can be large.

For one directional semantic perspective:

```text
A --name--> B
```

row count is conceptually:

```text
|Desc(A)| * |Desc(B)|
```

This expansion is accepted as a serious but potentially desirable design trade-off because it is model-plane work over stable semantic knowledge.

The intended separation is:

```text
MODEL PLANE
    interpret stable ObjectTemplate inheritance
    expand declared semantic perspective spaces
    detect semantic repetition/conflict
    materialize exact effective semantic cells
    maintain the materialization when the stable model grows/changes

DATA PLANE
    consume already-resolved effective semantic knowledge
    avoid ancestry traversal/reinterpretation for normal factual admission
```

The materialization is therefore not proposed merely as a query cache. It is candidate **certified effective model knowledge**.

---

# 9. Data-plane admission benefit

Without the effective materialization, factual Relationship admission must still interpret whether the concrete Object endpoint templates belong to the directional semantic perspective selected by the caller, typically via ancestry membership predicates.

With the materialized space, after obtaining the two concrete Object `template_id` values, applicability can conceptually reduce to an exact lookup:

```text
resolution_id = requested Resolution
from_template_id = actual from Object template
to_template_id = actual to Object template
```

Equivalent conceptual predicate:

```text
EXISTS relationship_resolution_space row
WHERE
    resolution_id = :resolution_id
    AND from_template_id = :actual_from_template_id
    AND to_template_id = :actual_to_template_id
```

Normal factual admission therefore consumes a model-plane-certified directional answer instead of reconstructing inheritance semantics.

The exact factual Relationship model remains intentionally OUT OF SCOPE until this upstream model is stabilized.

---

# 10. Additional consumers of the same materialization

The same effective space could potentially serve several model/data-plane consumers without duplicating semantic interpretation.

Candidate consumers:

```text
RelationshipDefinition CREATE/conflict admission
    -> candidate semantic-cell acquisition vs current occupied space

Relationship capability lookup for an exact ObjectTemplate
    -> direct rows where from_template_id = selected exact template

factual Relationship CREATE admission
    -> exact Resolution + concrete endpoint-template lookup

future model analysis/search
    -> concrete representation of which directed relationship meanings
       are currently expressible for exact ObjectTemplate pairs
```

This consolidation is considered an architectural benefit: multiple operations consume the same certified effective model instead of independently reimplementing lineage predicates.

---

# 11. Maintenance triggers and derived-state boundary

The effective space changes when its source stable model changes.

At minimum, revalidation must account for:

```text
new RelationshipDefinition / semantic perspective declaration
    -> materialize the new declared spaces
    -> reject if required semantic cells are already owned

RelationshipDefinition deletion
    -> remove its derived semantic cells

new ObjectTemplate descendant
    -> may add effective semantic cells to every perspective whose declared
       from/to roots admit that new lineage member

ObjectTemplate lineage deletion/change
    -> must keep derived space exactly synchronized with the stable lineage model
```

The exact supported ObjectTemplate topology-mutation lifecycle is not decided here; this section records only the dependency.

Important boundary:

```text
relationship_resolutions
    -> current candidate source declaration / true external lineage ownership

relationship_resolution_space
    -> derived effective closure
```

The derived table must **not accidentally create stronger model-lifetime semantics than the declaration itself**. In particular, materializing a descendant template as an effective cell must not automatically mean that the RelationshipDefinition now owns that descendant lineage in the same sense as its explicitly declared endpoint roots.

Therefore the exact FK / ON DELETE behavior from `relationship_resolution_space.from_template_id` and `.to_template_id` to `object_templates` is explicitly OPEN and must be designed as derived-state maintenance, not inferred mechanically from the declared Resolution FK policy.

---

# 12. Candidate relational picture

Current intent draft:

```text
relationship_definitions
    id PK
    symmetric                                        # RATIFIED stable explicit intent
    default_version

        1
        |
        | owns
        v

relationship_resolutions                            # representation still candidate
    id PK
    relationship_definition_id FK -> relationship_definitions.id
    from_template_id FK -> object_templates.id     # declared root
    to_template_id   FK -> object_templates.id     # declared root
    name                                             # STABLE semantic attribute

        1
        |
        | expands to
        v

relationship_resolution_space
    relationship_definition_id
    resolution_id
    from_template_id                                # exact effective member
    name                                            # stable copied semantic name
    to_template_id                                  # exact effective member

    ratified semantic ownership:
        one owner per (from_template_id, name, to_template_id)

    candidate physical enforcement:
        UNIQUE(from_template_id, name, to_template_id)

relationship_definition_versions
    relationship_definition_id
    version
    revision
    status

relationship_definition_properties
    relationship_definition_id
    relationship_definition_version
    name
    position
    datatype_id
    datatype_version
    value_mode
```

The version/property side is shown only for completeness; it is not yet modified by this redesign intent.

The declared relational picture above remains a **candidate inherited from the current Resolution shape**, except that persistence of stable explicit `relationship_definitions.symmetric` intent is ratified. The domain now requires:

```text
symmetric=true
    -> one semantic name preserved under reciprocal observation

symmetric=false
    -> exactly two distinct reciprocal semantic names
    -> each name owns only its declared direction
```

The remaining representation question is whether those semantic perspectives require one/two stored `relationship_resolutions` rows or should be represented more compactly.

---

# 13. What this candidate would supersede if eventually ratified

If this intent is later ratified and promoted, it would require targeted revalidation of assumptions currently based on:

```text
RelationshipResolution.name as mutable metadata
RelationshipDefinition.RENAME preserving the same semantic Definition
abstract overlap predicates as the only cross-Definition conflict representation
same-Definition Resolution overlap being automatically tolerated and delegated
    to factual runtime closure
runtime Relationship CREATE performing lineage-based Resolution applicability
factual runtime closure being used to compensate for ambiguous/redundant
    Definition semantic coverage
symmetric distinct-but-overlapping endpoint roots being valid model semantics
symmetric disjoint endpoint spaces requiring a distinct endpoint-pairing model from
    asymmetric cross-domain relationships
symmetry being inferred from incomplete perspective/request shape rather than
    supplied as explicit authoring intent
asymmetric Definitions allowing a missing reciprocal semantic name
an asymmetric semantic name being treated as applicable in both endpoint orientations
```

No such supersession is effective yet except for the ratified intent checkpoints explicitly marked above. These remain targeted downstream revalidation inputs until the intent is promoted.

---

# 14. OPEN questions before downstream review can resume

The current intent is intentionally incomplete. At least the following points must be reviewed explicitly:

```text
1. Symmetric Definition persisted shape
    - RATIFIED: endpoint spaces are identical or disjoint, never distinct-but-overlapping
    - RATIFIED: disjoint symmetric/asymmetric cases share the same reciprocal endpoint-space pairing at Definition level
    - RATIFIED: one symmetric name applies in both reciprocal orientations
    - RATIFIED: symmetric is explicit client intent, persisted and stable for Definition lifetime
    - OPEN: minimal persisted representation for same-space symmetric semantics
    - OPEN: minimal persisted representation for reciprocal disjoint-space symmetric semantics

2. Non-symmetric Definition persisted shape
    - RATIFIED: exactly two reciprocal semantic perspectives
    - RATIFIED: exactly two distinct stable semantic names
    - RATIFIED: each name is directional and applies only in its own orientation
    - OPEN: whether same-lineage endpoint overlap is meaningful/allowed for asymmetric Definitions
    - OPEN: minimal persisted representation of the two reciprocal semantics

3. Resolution identity
    - continued role of resolution_id once semantic cells are materialized
    - whether callers still select by resolution_id in the final TO-BE API

4. Stable-name lifecycle
    - immutable from Definition CREATE vs editable only in a pre-admission phase
    - exact fate of RelationshipDefinition.RENAME

5. Materialized-space physical realization
    - exact PK/UNIQUE shape implementing the ratified single-owner semantic invariant
    - whether relationship_definition_id is physically denormalized
    - how ownership is represented if the compact Resolution table changes
    - FK/cascade/rebuild strategy
    - indexes for model conflict, capability and factual admission

6. ObjectTemplate model-growth maintenance
    - efficient incremental expansion on new descendants
    - transactional conflict arbitration when a new descendant creates a
      semantic-cell collision between already-existing declared perspectives

7. RelationshipDefinition version/property interaction
    - confirm that perspective topology/name remains definition-stable and outside
      the RDV lifecycle

8. Factual Relationship redesign
    - only after this upstream model is stable, revalidate factual endpoint
      identity, runtime rows, uniqueness, GETs and concurrency
```

---

# 15. Current working thesis

The current draft can be summarized as:

```text
directional semantic perspective
    = compact stable semantic rule

    declared from-template root
    + stable name
    + declared to-template root

        ↓ model-plane expansion through stable ObjectTemplate inheritance

relationship_resolution_space
    = complete exact effective semantic closure

    exact from-template
    + stable name
    + exact to-template

semantic cell [RATIFIED]
    = (exact from-template, stable name, exact to-template)
    = ordered/directional semantic identity

semantic ownership invariant [RATIFIED]
    = one semantic cell has one Resolution/perspective owner globally

symmetric endpoint-space domain invariant [RATIFIED]
    = endpoint compatibility spaces are identical or disjoint
    = distinct-but-overlapping spaces are not core relationship semantics
      because they encode an endpoint-presence applicability policy

disjoint-space Definition topology [RATIFIED]
    = symmetric and asymmetric Definitions share the same reciprocal endpoint-space pairing
    = this equivalence is Definition-level only, not per semantic name

symmetric semantics [RATIFIED]
    = one stable semantic name
    = reciprocal observation preserves that name
    = the same name applies in both required reciprocal orientations

asymmetric semantics [RATIFIED]
    = exactly two reciprocal semantic perspectives
    = exactly two distinct stable semantic names
    = each name applies only in its declared orientation
    = e.g. VirtualMachine --runs_on--> Hypervisor / Hypervisor --hosts--> VirtualMachine

symmetric authoring intent [RATIFIED]
    = explicit required client intent
    = persisted stable Definition state
    = never inferred from an omitted reciprocal name/request field
    = complete perspective semantics must validate against that intent

model plane
    = pays expansion + conflict certification

data plane
    = consumes exact pre-resolved directional applicability
```

This thesis is the basis for the next review pass. It must be challenged with concrete symmetric/non-symmetric/inheritance examples before any downstream factual Relationship work is resumed.
