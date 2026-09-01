# M4 — New RelationshipDefinition intent

**Status:** INTENT DRAFT / ACTIVE REVIEW FRONTIER / WIP / NON-NORMATIVE

## Purpose

This document is the upstream intent owner for the current M4 revalidation of `RelationshipDefinition` semantics and relational representation.

It exists because the factual Relationship review exposed downstream anomalies whose root cause may be the current Definition/Resolution model rather than the factual Relationship implementation itself. The factual `relationship.md` review therefore remains frozen until this upstream model is coherent enough to revalidate its assumptions.

This file is deliberately an **intent draft**. It is not normative architecture and does not authorize implementation. It records the TO-BE direction and the checkpoints explicitly ratified during the M4 review so that the model can be stress-tested for missing cases before downstream work resumes.

Current scope:

```text
IN SCOPE
    stable RelationshipDefinition semantics
    symmetric/asymmetric domain meaning
    stable directional semantic names
    endpoint compatibility spaces
    what it means for a relationship meaning to be already expressed
    compact Definition source of truth
    effective materialized semantic closure over ObjectTemplate inheritance
    relational direction for Definition + closure
    model-plane vs data-plane responsibility split
    ability to expose oriented read projections without autonomous Resolution persistence

NOT YET CLOSED
    exact public RelationshipDefinition request/response DTOs
    exact physical column names/nullability/check constraints
    exact PK/FK/index realization
    CREATE/DELETE/version lifecycle concurrency protocol
    ObjectTemplate-growth maintenance protocol
    factual Relationship selector and persistence after removal of resolution_id
    factual Relationship runtime representation
```

---

# 1. Domain primitive — a RelationshipDefinition owns one relationship meaning

A `RelationshipDefinition` represents one relationship type between two declared ObjectTemplate compatibility-space roots.

For review notation, call them `A` and `B`.

ObjectTemplate inheritance is lineage-polymorphic. Define:

```text
Desc(T) = T + every current stable ObjectTemplate descendant of T
```

A directional semantic perspective:

```text
A --rel1--> B
```

means the complete effective set:

```text
Desc(A) x {rel1} x Desc(B)
```

A semantic name is directional unless symmetric semantics explicitly require the same name in the reciprocal orientation.

The two endpoint roots and the complete semantic naming contract are stable Definition-level state. They are not versioned property-schema state.

---

# 2. RATIFIED — semantic names are stable Definition semantics

Semantic names are not mutable display labels.

A name identifies the meaning of a specific directional perspective inside the Definition and is stable for the Definition lifetime.

Example asymmetric Definition:

```text
VirtualMachine --runs_on--> Hypervisor
Hypervisor     --hosts----> VirtualMachine
```

`runs_on` and `hosts` are distinct stable meanings.

Changing:

```text
hosts -> runs
```

or any other semantic-name replacement changes the relationship contract rather than renaming an existing contract.

Consequences to revalidate downstream:

```text
RelationshipDefinition.RENAME
    -> current AS-IS semantics no longer fit this model
    -> exact public route removal/replacement is a later API checkpoint

name mutation
    -> does not preserve the same stable Definition meaning
    -> a genuinely different semantic contract requires a different Definition
```

The earlier idea that names belong to autonomous `RelationshipResolution` entities is superseded by the relational direction ratified later in this document: names remain perspective-specific semantics, but their owner is the `RelationshipDefinition` itself.

---

# 3. RATIFIED — semantic cell and no-repetition invariant

At the effective exact-template level, one atomic directed relationship meaning is:

```text
semantic cell = (
    exact_from_template_id,
    stable_name,
    exact_to_template_id
)
```

The order of the endpoint templates is part of the semantic identity.

RATIFIED rule:

```text
the same semantic cell must not be expressed more than once in the model
```

Therefore:

```text
(T1, name, T2)
```

and:

```text
(T2, name, T1)
```

are distinct cells unless `T1 == T2`.

Different names also mean different semantic cells even when the endpoint pair is the same. NETAUTO does not attempt synonym inference:

```text
(Server, hosts, VM)
!=
(Server, runs, VM)
```

The global rule is based on meaning, not owner identity. Two different Definitions cannot make an already-owned cell distinct merely by having different UUIDs.

This invariant applies both:

```text
INTRA-DEFINITION
    -> one Definition must not express the same cell twice through its own semantics

INTER-DEFINITION
    -> a new/existing Definition must not re-express a cell already owned elsewhere
```

---

# 4. RATIFIED — `symmetric` is explicit stable client intent

Symmetry may be derivable after a complete Definition has been certified, but it cannot be safely inferred during authoring.

If a client supplies one name, the server cannot know whether:

```text
1. symmetric=true was intended
or
2. symmetric=false was intended but the reciprocal name was accidentally omitted
```

Therefore:

```text
symmetric
    -> required explicit client intent
    -> persisted on relationship_definitions
    -> stable for Definition lifetime
    -> never inferred from omission
```

Semantic meaning:

```text
symmetric = true
    reciprocal observation preserves the same semantic name

symmetric = false
    reciprocal observation requires a different semantic name
```

Definition CREATE must validate the complete semantic contract against this explicit intent.

---

# 5. RATIFIED — symmetric endpoint-space semantics

## 5.1 Same/overlapping lineage

Assume:

```text
A <: B
```

These three symmetric declarations describe different fact spaces:

```text
A --rel--> A
    -> both endpoints belong to Desc(A)

A --rel--> B
    -> both endpoints belong to Desc(B)
    -> at least one endpoint belongs to Desc(A)

B --rel--> B
    -> both endpoints belong to Desc(B)
```

The middle shape expresses an endpoint-presence applicability policy:

```text
at least one endpoint must belong to subtype-space A
```

That is not considered core RelationshipDefinition semantics.

RATIFIED rule:

```text
for symmetric Definitions, endpoint compatibility spaces are:
    IDENTICAL
    OR
    DISJOINT

never DISTINCT-BUT-OVERLAPPING
```

With the current single-inheritance model:

```text
A == B
    -> allowed

A ancestor-of B, A != B
    -> forbidden for symmetric Definition

B ancestor-of A, A != B
    -> forbidden for symmetric Definition
```

The rule is domain-driven, not a storage limitation.

## 5.2 Disjoint endpoint spaces

If:

```text
Desc(A) INTERSECT Desc(B) = EMPTY
```

then a symmetric Definition is a valid cross-domain relationship.

Example:

```text
Router --connected_to--> Switch
Switch --connected_to--> Router
```

The same stable name applies to both reciprocal orientations:

```text
Desc(A) x {rel} x Desc(B)
UNION
Desc(B) x {rel} x Desc(A)
```

Because the spaces are disjoint:

```text
(A', rel, B') != (B', rel, A')
```

so reciprocal materialization does not duplicate a semantic cell.

## 5.3 Same endpoint space

For:

```text
A --rel--> A
```

symmetric semantics require only one logical perspective. Its effective closure is:

```text
Desc(A) x {rel} x Desc(A)
```

There is no reason to generate a duplicate reciprocal declaration when source and destination compatibility spaces are the same.

---

# 6. RATIFIED — asymmetric semantics

An asymmetric Definition represents one fact whose endpoint roles are not semantic peers.

Therefore:

```text
symmetric = false
    -> exactly two reciprocal semantic perspectives
    -> exactly two distinct stable semantic names
```

For endpoint roots `A` and `B`:

```text
A --rel1--> B
B --rel2--> A
rel1 != rel2
```

Each name is strictly directional:

```text
E(rel1) = Desc(A) x {rel1} x Desc(B)
E(rel2) = Desc(B) x {rel2} x Desc(A)
```

There is no implicit reverse applicability of either name.

Example:

```text
VirtualMachine --runs_on--> Hypervisor
Hypervisor     --hosts----> VirtualMachine
```

Valid meanings:

```text
VirtualMachine runs_on Hypervisor
Hypervisor hosts VirtualMachine
```

Not expressed by the Definition:

```text
Hypervisor runs_on VirtualMachine
VirtualMachine hosts Hypervisor
```

A one-name asymmetric declaration is incomplete, not a separate supported shape.

## 6.1 Asymmetric endpoint spaces may overlap

Unlike symmetric semantics, asymmetric endpoint roles may be identical, disjoint, or ancestor/descendant-overlapping.

Example:

```text
Employee
└── Manager

Manager  --manages----> Employee
Employee --managed_by-> Manager
```

This is coherent because the two names represent distinct directional roles.

It naturally admits:

```text
Manager1 manages Manager2
Manager2 managed_by Manager1
```

because a Manager is also an Employee.

RATIFIED rule:

```text
symmetric = false
    -> endpoint spaces may be identical, disjoint, or distinct-but-overlapping
    -> overlap alone is not a rejection condition
```

A restriction such as:

```text
"a Manager may manage Employees but not Managers"
```

would be an applicability policy layered on top of relationship semantics, not something encoded by the core Definition topology.

The global semantic-cell uniqueness invariant remains authoritative: overlap is allowed, but an effective cell still cannot collide with an already-owned cell.

---

# 7. RATIFIED relational direction — no autonomous RelationshipResolution persistence

The review found no independent domain lifetime or identity for a directional perspective.

A perspective exists only as part of one immutable RelationshipDefinition semantic contract. Its endpoint roots and name cannot evolve independently from that Definition.

RATIFIED TO-BE direction:

```text
remove autonomous relationship_resolutions persistence
remove resolution_id as model-plane semantic identity
persist the complete compact relationship contract on relationship_definitions
materialize the effective inheritance-expanded cells in a derived closure table
```

This is a relational/model direction, not final DDL. Exact column names, nullability and CHECK constraints remain architecture work.

Logical Definition source-of-truth state is:

```text
RelationshipDefinition
    id
    symmetric
    endpoint A template root
    endpoint B template root
    semantic naming contract
    default_version
```

The naming contract is:

```text
symmetric=true
    -> exactly one stable semantic name
    -> same name used under reciprocal observation

symmetric=false
    -> exactly two distinct stable semantic names
    -> one name maps A -> B
    -> the reciprocal name maps B -> A
```

The persisted A/B slots are only a stable way to bind names to endpoint orientation. They do not create a privileged domain `source`, `target`, `forward` or `reverse` side.

A possible physical encoding might use fields conceptually equivalent to:

```text
relationship_definitions
    id
    symmetric
    endpoint_a_template_id
    endpoint_b_template_id
    name_a_to_b
    name_b_to_a       # asymmetric only, or otherwise represented compactly
    default_version
```

but this exact column layout is **not yet frozen**.

The existing version/property family remains conceptually separate:

```text
relationship_definition_versions
relationship_definition_properties
```

No checkpoint here changes their property-schema responsibilities.

---

# 8. Derived effective semantic closure

Working table name:

```text
relationship_definition_space
```

Conceptual rows:

```text
relationship_definition_space
    relationship_definition_id
    from_template_id
    name
    to_template_id
```

The table contains the complete exact-template semantic closure generated by the compact Definition through ObjectTemplate inheritance.

There is no `resolution_id` because there is no longer an autonomous Resolution owner. Every row is owned directly by one RelationshipDefinition.

## 8.1 Asymmetric example

Source Definition:

```text
VirtualMachine --runs_on--> Hypervisor
Hypervisor     --hosts----> VirtualMachine
```

Closure:

```text
for every VM' in Desc(VirtualMachine)
for every H'  in Desc(Hypervisor)

    (D, VM', runs_on, H')
    (D, H',  hosts,   VM')
```

## 8.2 Symmetric disjoint-space example

Source Definition:

```text
Router --connected_to--> Switch
```

with disjoint spaces materializes:

```text
for every R' in Desc(Router)
for every S' in Desc(Switch)

    (D, R', connected_to, S')
    (D, S', connected_to, R')
```

## 8.3 Symmetric same-space example

Source Definition:

```text
Person --friend_of--> Person
```

materializes exactly:

```text
Desc(Person) x {friend_of} x Desc(Person)
```

with no duplicate reciprocal generation.

---

# 9. RATIFIED semantic ownership; physical uniqueness still OPEN

With autonomous Resolution identity removed, the earlier single-owner rule becomes simpler:

```text
one semantic cell
    -> exactly one owning RelationshipDefinition globally
```

Semantic ownership key:

```text
(from_template_id, name, to_template_id)
```

A strong physical realization candidate is:

```text
UNIQUE (
    from_template_id,
    name,
    to_template_id
)
```

This would make the closure table the final relational arbitration authority for semantic repetition.

However the exact physical enforcement remains OPEN. M4 has not yet selected among:

```text
PRIMARY KEY
UNIQUE constraint/index
explicit candidate prevalidation + final UNIQUE arbitration
other equivalent PostgreSQL realization
```

The semantic invariant is ratified; only the DDL mechanism is not.

---

# 10. RATIFIED direction — oriented GET projection is derived, not persisted

Removing `relationship_resolutions` does not require losing an oriented RelationshipDefinition representation.

The public API already treats read DTOs as semantic projections rather than persistence-row mirrors. The TO-BE domain can therefore derive oriented perspectives directly from the compact Definition.

Candidate logical read projection:

```text
RelationshipDefinition
    id
    symmetric
    default_version
    perspectives[]
        name
        from_template_id
        to_template_id
```

Exact public field naming remains OPEN; in particular this checkpoint does not yet decide whether the final API keeps a legacy `resolutions` label or adopts `perspectives`.

`resolution_id` is not present in the TO-BE projection because there is no autonomous Resolution identity.

Domain construction rules are simple and deterministic:

```text
SYMMETRIC + same endpoint space
    -> one oriented item
       A --rel--> A

SYMMETRIC + disjoint endpoint spaces
    -> two reciprocal oriented items
       A --rel--> B
       B --rel--> A

ASYMMETRIC
    -> two reciprocal oriented items
       A --rel1--> B
       B --rel2--> A
```

The oriented projection is therefore a presentation/navigation view over stable Definition semantics, not evidence that the perspectives need separate persistence identities.

Exact array ordering is also not yet a semantic contract; a deterministic operational order can be chosen later if required.

---

# 11. Model-plane cost is intentionally traded for data-plane simplicity

For one directional perspective:

```text
A --name--> B
```

the materialized row count is conceptually:

```text
|Desc(A)| * |Desc(B)|
```

A symmetric disjoint-space Definition adds the reciprocal set under the same name. An asymmetric Definition adds the reciprocal set under the second name.

This can produce a large closure, but the cost is deliberately model-plane work over stable semantic knowledge.

Intended split:

```text
MODEL PLANE
    interpret ObjectTemplate inheritance
    expand stable Definition semantics
    certify no semantic-cell repetition
    materialize exact effective cells
    maintain closure when model topology changes

DATA PLANE
    consume already-resolved exact semantic applicability
    avoid ancestry traversal and Definition reinterpretation on normal factual admission
```

This materialization is therefore not merely a cache. It is candidate **certified effective model knowledge**.

---

# 12. Data-plane and capability benefits

Once concrete Object endpoint template IDs are known, factual Relationship admission should be able to consume an exact closure answer instead of reinterpreting inheritance.

The exact factual CREATE selector is deliberately reopened because `resolution_id` disappears.

Possible later selector inputs include some combination of:

```text
relationship_definition_id
semantic name
actual from/to Object identities/templates
```

but the exact public/data-plane contract is OUT OF SCOPE until this upstream model stabilizes.

The same closure can also support:

```text
RelationshipDefinition CREATE/conflict admission
    -> candidate cell acquisition against current occupied space

ObjectTemplate relationship-capability lookup
    -> exact rows where from_template_id = selected template

factual Relationship CREATE admission
    -> exact Definition/name/from-template/to-template applicability

future model analysis/search
    -> concrete representation of all currently expressible directed meanings
```

This avoids independently reimplementing inheritance predicates in several consumers.

---

# 13. Maintenance triggers and derived-state boundary

The compact Definition is source of truth. `relationship_definition_space` is derived effective knowledge.

At minimum, revalidation must cover:

```text
new RelationshipDefinition
    -> derive every required semantic cell
    -> reject if any cell is already owned
    -> persist compact Definition + complete closure atomically

RelationshipDefinition deletion
    -> remove its derived cells

new ObjectTemplate descendant
    -> may introduce new cells for every Definition whose endpoint roots admit it
    -> may reveal a semantic collision between already-existing Definitions

ObjectTemplate lineage deletion/change
    -> derived space must remain synchronized with the stable lineage model
```

The new-descendant case is particularly important and remains OPEN at the execution/concurrency layer: ObjectTemplate model growth may need to reject a topology change if expanding existing Definitions would create a semantic-cell collision.

Derived rows must not accidentally acquire stronger lifetime semantics than the compact declaration. Materializing a descendant template in a cell does not mean the RelationshipDefinition explicitly owns that descendant lineage in the same sense as its declared endpoint roots.

Exact FK/ON DELETE/rebuild behavior for closure endpoint IDs remains architecture work.

---

# 14. RelationshipDefinitionVersion/property boundary

The redesign currently changes only stable Definition topology/naming and its effective closure.

The existing versioned property-schema family remains conceptually:

```text
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

Current intended boundary:

```text
Definition stable state
    -> symmetric intent
    -> endpoint roots
    -> stable semantic names

DefinitionVersion state
    -> property schema only
```

A later checkpoint must confirm this separation explicitly against CREATE_NEXT/REVISE/PUBLISH semantics, but no current evidence requires endpoint topology or semantic names to be versioned.

---

# 15. Downstream assumptions that must be revalidated

If this intent is promoted, the following AS-IS/current-review assumptions cannot survive unchanged:

```text
relationship_resolutions as autonomous persistence
resolution_id as stable model-plane perspective identity
RelationshipDefinition.RENAME mutating semantic names
runtime Relationship CREATE selecting an autonomous Resolution UUID
runtime closure compensating for ambiguous/redundant Definition overlap
same-Definition overlap being delegated to factual runtime closure
symmetric distinct-but-overlapping endpoint roots being valid core semantics
asymmetric relationship names being applicable in both orientations
asymmetric Definitions being allowed to omit the reciprocal name
cross-Definition conflict being represented only as an abstract overlap predicate
```

The factual Relationship WIP remains frozen until these dependencies are revalidated against the stabilized upstream Definition model.

---

# 16. OPEN questions

The current intent is deliberately incomplete. Remaining explicit review points include:

```text
1. Exact compact relational encoding
    - final column names for endpoint slots and names
    - symmetric representation of the single name
    - CHECK/nullability constraints
    - endpoint-root FK behavior

2. Physical relationship_definition_space realization
    - PK/UNIQUE choice
    - indexes for conflict/capability/factual admission
    - FK/cascade/rebuild semantics
    - storage/fan-out evidence gate

3. ObjectTemplate model-growth maintenance
    - efficient incremental expansion
    - atomic collision certification on new descendants
    - concurrency with Definition CREATE/DELETE

4. Stable-name lifecycle/API
    - exact removal/replacement of RelationshipDefinition.RENAME
    - migration/backfill from AS-IS Resolution rows

5. RelationshipDefinition public GET/list
    - exact `perspectives`/legacy naming
    - exact list vs detail projection richness
    - deterministic operational ordering if required

6. Factual Relationship redesign
    - replacement for resolution_id CREATE selector
    - factual endpoint identity/uniqueness
    - need, if any, for derived runtime rows after Definition closure exists
    - GET and Object-scoped collection realization
    - concurrency and lifecycle payloads

7. Version/property interaction
    - confirm stable topology/name remains outside RDV lifecycle
```

---

# 17. Current working thesis

```text
RelationshipDefinition
    = complete compact stable relationship contract

    stable Definition UUID
    + explicit stable symmetric intent
    + two declared endpoint compatibility-space roots
    + one stable semantic name if symmetric
      OR two distinct stable reciprocal names if asymmetric

NO autonomous RelationshipResolution entity
NO resolution_id model identity

        ↓ model-plane expansion through ObjectTemplate inheritance

relationship_definition_space
    = complete exact effective semantic closure

    relationship_definition_id
    exact from-template
    stable semantic name
    exact to-template

semantic cell [RATIFIED]
    = (exact from-template, stable name, exact to-template)
    = ordered/directional semantic identity

semantic ownership [RATIFIED]
    = one semantic cell belongs to exactly one RelationshipDefinition globally

symmetric [RATIFIED]
    = explicit persisted client intent
    = reciprocal observation preserves one stable name
    = endpoint spaces identical or disjoint
    = never distinct-but-overlapping

asymmetric [RATIFIED]
    = exactly two distinct reciprocal stable names
    = each name applies only in its own direction
    = endpoint spaces may be identical, disjoint, or inheritance-overlapping

oriented GET
    = domain/API projection derived from Definition semantics
    = does not require autonomous perspective persistence

model plane
    = pays expansion + conflict certification

data plane
    = consumes exact pre-resolved directional applicability
```

This thesis is the basis for the next review pass and must continue to be challenged with concrete domain and lineage examples before downstream factual Relationship work resumes.
