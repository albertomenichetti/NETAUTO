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
    VM --is_hosted_by--> Hypervisor

Resolution R2
    Hypervisor --hosts--> VM
```

`is_hosted_by` and `hosts` are the stable semantic names of the two distinct perspectives.

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
    -> stable Definition root / grouping and symmetric classification

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

For one declared Resolution:

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

If the Definition also declares the reciprocal distinct semantic perspective:

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

and a symmetric Definition is represented by reciprocal Resolutions with the same stable name:

```text
R1: A --rel--> B
R2: B --rel--> A
```

Then:

```text
R1 -> Desc(A) x {rel} x Desc(B)
R2 -> Desc(B) x {rel} x Desc(A)
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

# 7B. RATIFIED domain invariant — disjoint endpoint spaces have the same applicability topology regardless of symmetry

Let the two endpoint compatibility spaces be disjoint:

```text
Desc(A) INTERSECT Desc(B) = EMPTY
```

A RelationshipDefinition between those spaces is a genuine cross-domain relationship: every admitted fact necessarily connects one member of `Desc(A)` with one member of `Desc(B)`.

RATIFIED domain decision:

```text
for disjoint endpoint spaces, symmetric and asymmetric Definitions have the
same endpoint-applicability topology
```

Both cases require the same two reciprocal directed effective spaces:

```text
Desc(A) -> Desc(B)
Desc(B) -> Desc(A)
```

The difference is semantic naming, not endpoint applicability:

```text
SYMMETRIC
    A --rel--> B
    B --rel--> A
    same stable semantic name in both directions

ASYMMETRIC
    A --rel1--> B
    B --rel2--> A
    distinct stable semantic names for the two perspectives
```

Because the endpoint spaces are disjoint, the two reciprocal expansions cannot collide merely by reversing direction. For a symmetric Definition they occupy different ordered semantic cells even though the name is the same:

```text
(A', rel, B') != (B', rel, A')
```

This means symmetry must not introduce a special applicability algorithm for the disjoint-lineage case. The model-plane effective closure treats symmetric and asymmetric cross-domain relationships uniformly; symmetry only determines whether the reciprocal perspectives carry the same or different semantic names.

This checkpoint deliberately does **not** decide the persisted representation. In particular, it does not yet decide whether reciprocal effective perspectives require two stored `relationship_resolutions`, can be derived from one compact declaration, or whether `relationship_definitions.symmetric` remains the best primitive field. Those are the next representation questions to revalidate from the domain semantics above.

---

# 8. Model-plane cost is intentionally traded for data-plane simplicity

The materialized space can be large.

For one Resolution:

```text
R: A --name--> B
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
    expand declared Resolution spaces
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

Without the effective materialization, factual Relationship admission must still interpret whether the concrete Object endpoint templates belong to the two declared Resolution spaces, typically via ancestry membership predicates.

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

Normal factual admission therefore consumes a model-plane-certified answer instead of reconstructing inheritance semantics.

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
new RelationshipDefinition / Resolution declaration
    -> materialize the new declared spaces
    -> reject if required semantic cells are already owned

RelationshipDefinition deletion
    -> remove its derived semantic cells

new ObjectTemplate descendant
    -> may add effective semantic cells to every Resolution whose declared
       from/to roots admit that new lineage member

ObjectTemplate lineage deletion/change
    -> must keep derived space exactly synchronized with the stable lineage model
```

The exact supported ObjectTemplate topology-mutation lifecycle is not decided here; this section records only the dependency.

Important boundary:

```text
relationship_resolutions
    -> source declaration / true external lineage ownership

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
    symmetric
    default_version

        1
        |
        | owns
        v

relationship_resolutions
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

The declared relational picture above remains a **candidate inherited from the current shape**. The ratified disjoint-space semantics explicitly reopen whether two reciprocal perspective rows and the `symmetric` boolean are the minimal TO-BE representation.

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
symmetric disjoint endpoint spaces requiring a distinct applicability model from
    asymmetric cross-domain relationships
```

No such supersession is effective yet except for the ratified intent checkpoints explicitly marked above. These remain targeted downstream revalidation inputs until the intent is promoted.

---

# 14. OPEN questions before downstream review can resume

The current intent is intentionally incomplete. At least the following points must be reviewed explicitly:

```text
1. Symmetric Definition shape
    - RATIFIED: endpoint spaces are identical or disjoint, never distinct-but-overlapping
    - RATIFIED: disjoint symmetric/asymmetric cases share the same reciprocal applicability topology
    - OPEN: minimal persisted representation for same-space symmetric semantics
    - OPEN: minimal persisted representation for reciprocal disjoint-space perspectives
    - OPEN: whether `symmetric` remains a primitive field or can be derived from perspective semantics

2. Non-symmetric Definition shape
    - whether exactly two reciprocal semantic perspectives remains the right domain model
    - whether same-lineage overlap is meaningful when perspective names differ
    - minimal persisted representation once perspective semantics are stabilized

3. Resolution identity
    - continued role of resolution_id once semantic cells are materialized
    - whether callers still select by resolution_id in the final TO-BE API

4. Stable-name lifecycle
    - immutable from Definition CREATE vs editable only in a pre-admission phase
    - exact fate of RelationshipDefinition.RENAME

5. Materialized-space physical realization
    - exact PK/UNIQUE shape implementing the ratified single-owner semantic invariant
    - whether relationship_definition_id is physically denormalized
    - FK/cascade/rebuild strategy
    - indexes for model conflict, capability and factual admission

6. ObjectTemplate model-growth maintenance
    - efficient incremental expansion on new descendants
    - transactional conflict arbitration when a new descendant creates a
      semantic-cell collision between already-existing declared Resolutions

7. RelationshipDefinition version/property interaction
    - confirm that Resolution topology/name remains definition-stable and outside
      the RDV lifecycle

8. Factual Relationship redesign
    - only after this upstream model is stable, revalidate factual endpoint
      identity, runtime rows, uniqueness, GETs and concurrency
```

---

# 15. Current working thesis

The current draft can be summarized as:

```text
RelationshipResolution declaration
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

semantic ownership invariant [RATIFIED]
    = one semantic cell has one Resolution owner globally

symmetric endpoint-space domain invariant [RATIFIED]
    = endpoint compatibility spaces are identical or disjoint
    = distinct-but-overlapping spaces are not core relationship semantics
      because they encode an endpoint-presence applicability policy

disjoint-space topology invariant [RATIFIED]
    = symmetric and asymmetric Definitions use the same reciprocal endpoint
      applicability topology
    = symmetry changes reciprocal semantic naming, not endpoint admissibility

model plane
    = pays expansion + conflict certification

data plane
    = consumes exact pre-resolved applicability
```

This thesis is the basis for the next review pass. It must be challenged with concrete symmetric/non-symmetric/inheritance examples before any downstream factual Relationship work is resumed.
