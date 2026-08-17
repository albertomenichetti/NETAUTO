# M2 Relationship Architecture

**Status:** DRAFT — SEMANTIC DESIGN COMPLETE — CROSS-OWNER/TRACEABILITY/CONSISTENCY CLOSURE PASSED — READY FOR FREEZE REVIEW

**Authority:** NORMATIVE M2 ARCHITECTURE DRAFT

## Authority and scope

This document owns the M2 TO-BE domain architecture for:

```text
RelationshipDefinition
RelationshipResolution
RelationshipDefinitionVersion
Relationship property declarations
factual Relationship state
RuntimeRelationshipResolution closure semantics
Relationship lifecycle semantic meaning
model-plane/data-plane interaction
```

Its implementation authority, once this document and the complete M2 architecture set are frozen, is:

```text
docs/architecture/relationship.md
    delivered Relationship AS-IS
+
docs/milestones/M2/contract.md
    FINAL / FROZEN milestone obligations and explicit deltas
+
this document
    normative M2 Relationship delta
```

This document does not own:

```text
HTTP routes, wire DTOs, omission/null carriers or public error envelopes
    -> api.md

relational tables, foreign keys, JSONB codecs, indexes or Alembic DDL
    -> persistence.md

pairwise mutation interleavings and semantic concurrency matrix
    -> concurrency-matrix.md

PostgreSQL row locks, advisory gates, retries or deadlock realization
    -> concurrency.md

verification scenarios and acceptance evidence
    -> verification.md
```

Those owners must implement the semantics defined here without redefining them.

Discovery material under `../wip/` is non-normative and is superseded by this document for the areas owned here.

---

## 1. Governing model

M2 separates stable relationship topology, exact versioned property schema and current factual state.

```text
RelationshipDefinition
    -> stable relationship-type identity
    -> immutable symmetry
    -> complete stable RelationshipResolution set
    -> endpoint ObjectTemplate lineage spaces
    -> mutable Resolution navigation names
    -> nullable default-version policy

RelationshipDefinitionVersion
    -> exact versioned property-schema snapshot
    -> DRAFT / PUBLISHED / DEPRECATED lifecycle
    -> DRAFT generation revision
    -> complete ordered property declarations
    -> exact DataTypeVersion pins

Relationship
    -> factual association identity
    -> stable RelationshipDefinition binding
    -> exact RelationshipDefinitionVersion pin
    -> complete canonical current properties
    -> deterministic complete RuntimeRelationshipResolution closure
```

The governing correspondences are:

```text
MODEL PLANE

ObjectTemplate
    <-> RelationshipDefinition

ObjectTemplateVersion
    <-> RelationshipDefinitionVersion

DATA PLANE

Object
    <-> Relationship
```

Equivalent problems reuse the delivered ObjectTemplateVersion/Object solution unless the Relationship domain has a genuine difference.

Material differences are:

- RelationshipDefinition owns stable topology and navigation rather than inheritance, components, abstractness or qualified naming;
- RelationshipDefinitionVersion contains one complete local property schema and has no inheritance or effective-schema layer;
- all M2 Relationship properties are optional;
- factual Relationship uniqueness is a semantic association fact represented by a deterministic closure;
- Relationship lifecycle events are Object-relative projections rather than an intrinsic standalone Relationship timeline.

---

## 2. Preserved stable Relationship model

The delivered stable topology remains authoritative.

A complete RelationshipDefinition aggregate consists of:

```text
stable Definition header
+
complete RelationshipResolution set
```

Stable Definition state is:

```text
id
symmetric
```

M2 adds mutable policy state:

```text
default_version: integer | null
```

A RelationshipResolution retains stable:

```text
id
relationship_definition_id
from_template_id
to_template_id
```

and mutable non-key:

```text
name
```

The following remain Definition-level state and are never copied into or versioned by a RelationshipDefinitionVersion:

```text
symmetry
Resolution identity
Resolution membership
Resolution endpoint lineages
Resolution navigation names
```

Changing symmetry, endpoint lineage, Resolution membership or Resolution cardinality defines a different relationship type and requires a new RelationshipDefinition.

RelationshipResolution remains an owned child of the complete Definition aggregate and is not an autonomous public CRUD or lifecycle resource.

### 2.1 No privileged orientation

The model continues to define no privileged:

```text
source
target
forward
reverse
```

A non-symmetric Definition owns two reciprocal perspectives. Neither perspective is intrinsically primary.

### 2.2 Stable shape rules

Non-symmetric:

```text
exactly two reciprocal Resolutions
reciprocal endpoint lineages
distinct navigation names
```

Symmetric:

```text
one semantic navigation name

same endpoint lineage
    -> one Resolution

different endpoint lineages
    -> two reciprocal Resolutions with the same name
```

Endpoint references remain stable ObjectTemplate lineages, never exact ObjectTemplateVersions.

### 2.3 Resolution names

Name grammar remains:

```text
[a-z][a-z0-9_]*
maximum length = 64
```

No automatic normalization is performed.

A rename:

- preserves Definition and Resolution identities;
- preserves symmetry, endpoint lineages and membership;
- replaces the complete navigation-name candidate atomically;
- re-certifies delivered Definition equivalence and cross-Definition conflict freedom;
- does not create or revise a RelationshipDefinitionVersion;
- does not modify any factual exact-version pin or property state.

Current reads observe current Resolution names. Historical lifecycle records preserve the names observed when their event set was created.

### 2.4 Definition equivalence and conflict freedom

Definition semantic equivalence remains based only on:

```text
symmetric
+
complete semantic Resolution set
```

Cross-Definition Resolution conflict remains based on:

```text
same navigation name
AND overlapping from-lineage spaces
AND overlapping to-lineage spaces
```

RelationshipDefinitionVersions, property declarations, version numbers, defaults and factual property values do not distinguish otherwise equivalent or conflicting stable relationship types.

A Definition with only DRAFT or DEPRECATED versions still belongs to the globally certified stable Definition set.

---

## 3. RelationshipDefinitionVersion identity and allocation

An exact RelationshipDefinitionVersion identity is:

```text
(relationship_definition_id, version)
```

Rules:

```text
version > 0
version is local to one RelationshipDefinition
no surrogate version UUID
```

Version allocation uses:

```text
max(currently existing versions) + 1
```

Gaps are allowed.

Deleting the highest DRAFT may make that version number available to a later allocation. Version number is an exact current resource identity, not an irreversible audit sequence.

A Definition may own multiple DRAFT versions concurrently.

No `derived_from`, source-version or provenance relation is part of the domain state. CREATE_NEXT uses an exact source command operand but does not persist that command history as version identity.

---

## 4. RelationshipDefinitionVersion lifecycle

Lifecycle is monotonic:

```text
DRAFT -> PUBLISHED -> DEPRECATED
```

No reverse transition exists.

### 4.1 DRAFT

A DRAFT:

- is an exact mutable property-schema candidate;
- owns a positive generation `revision`;
- must always remain structurally and semantically well-formed;
- may temporarily fail stronger publication-admission predicates;
- can be changed only through explicit complete-candidate operations.

The revision is the freshness token for the complete DRAFT generation.

The following commands consume `expected_revision`:

```text
REVISE
PUBLISH
DELETE_DRAFT
```

A stale generation cannot be silently overwritten or consumed.

### 4.2 PUBLISHED

A PUBLISHED version:

- is immutable;
- is eligible for new factual Relationship bindings;
- may be selected as Definition default;
- belongs to the active model graph;
- protects the PUBLISHED state of its direct exact DataTypeVersion dependencies.

### 4.3 DEPRECATED

A DEPRECATED version:

- is immutable;
- cannot receive new factual bindings;
- remains the authoritative exact schema for existing pinned facts;
- may be the source of CREATE_NEXT;
- may be the source of a forward factual SCHEMA_CHANGE;
- does not remain an active-model blocker of DataTypeVersion deprecation.

### 4.4 Command repeatability

Lifecycle commands are not idempotent state setters.

```text
PUBLISH on non-DRAFT
    -> lifecycle conflict

DEPRECATE on non-PUBLISHED
    -> lifecycle conflict

DELETE_DRAFT after exact version removal
    -> exact resource not found
```

PUBLISH and DEPRECATE do not increment revision.

---

## 5. Initial version and CREATE_NEXT

### 5.1 RelationshipDefinition CREATE

Creating a RelationshipDefinition atomically establishes:

```text
stable Definition header
complete certified Resolution set
RelationshipDefinitionVersion v1
    status = DRAFT
    revision = 1
    complete canonical initial property-schema candidate
default_version = null
```

An omitted initial property-schema candidate means an empty schema.

An empty schema is still a complete exact schema snapshot.

The new Definition is part of the stable certified topology set immediately, but it is not a currently usable runtime capability until at least one version is PUBLISHED.

### 5.2 CREATE_NEXT

CREATE_NEXT:

- selects one exact source version in the same Definition;
- accepts PUBLISHED or DEPRECATED source state;
- rejects DRAFT as source;
- does not require the source to be numerically highest;
- clones the complete declaration snapshot exactly;
- creates a new DRAFT at revision `1`;
- does not upgrade or re-resolve exact DataTypeVersion pins;
- does not change the stable Definition or its default.

A cloned declaration may retain an exact DataTypeVersion that became DEPRECATED after the source snapshot was created.

Such a clone is valid persisted historical candidate state, but publication remains blocked until the complete final dependency set is PUBLISHED.

---

## 6. DRAFT replacement and publication certification

### 6.1 REVISE

REVISE is complete replacement of one exact DRAFT property-schema candidate.

```text
complete declaration set required
empty set means exact empty schema
request order is not schema order
position is the sole ordering authority
```

REVISE cannot modify stable topology.

A successful REVISE increments revision exactly once, including when the resulting canonical candidate is equal to the previous candidate.

### 6.2 DRAFT well-formedness

Every persisted DRAFT must satisfy:

```text
exact Definition membership
unique valid property names
unique positive positions
valid SCALAR/LIST declarations
existing exact DataTypeVersion pins
valid historical evolution relative to prior published history
```

A DRAFT may be well-formed while not publishable because an already-owned exact dependency is now DEPRECATED.

### 6.3 Publication

Publication requires one fresh exact DRAFT generation whose complete candidate:

- is structurally and semantically valid;
- satisfies all historical property-evolution rules;
- has every direct exact DataTypeVersion dependency still PUBLISHED;
- remains admissible through commit.

PUBLISH turns the exact snapshot immutable.

If the stable Definition currently has no default, the first successful publication establishes the published version as default in the same semantic operation.

A later publication never replaces an existing default automatically.

---

## 7. Default-version policy

`RelationshipDefinition.default_version` is:

```text
null
or
an exact PUBLISHED RelationshipDefinitionVersion
owned by the same Definition
```

Rules:

```text
SET_DEFAULT
    -> exact same-Definition PUBLISHED version only

CLEAR_DEFAULT
    -> null

first PUBLISH while default is null
    -> establish that published version

later PUBLISH
    -> preserve current default

current default
    -> cannot be deprecated
```

Default changes govern only future implicit factual CREATE.

They do not update:

```text
existing Relationship exact pins
existing Relationship properties
runtime-resolution closures
lifecycle history
```

There is no fallback to latest, highest or another PUBLISHED version.

A Definition may have one or more PUBLISHED versions and `default_version = null`. Explicit exact CREATE remains available; implicit CREATE fails because no default was selected.

---

## 8. Relationship property declarations

One declaration belongs to one exact RelationshipDefinitionVersion and contains:

```text
name
position
datatype_id
datatype_version
value_mode
```

The following concepts do not exist for M2 Relationship properties:

```text
required
nullable
create default
migration default
```

### 8.1 Optional and non-nullable semantics

Every property is optional.

```text
property absent
    -> valid zero-cardinality state

property present with a concrete canonical value
    -> valid when the exact type contract accepts it

property present with JSON null
    -> invalid
```

No model-plane default invents factual data during CREATE or SCHEMA_CHANGE.

### 8.2 Name and position

Property name grammar is:

```text
[a-z][a-z0-9_]*
maximum length = 64
```

No automatic normalization is performed.

`position`:

- is positive;
- is unique within one exact version;
- is the only declaration-order authority;
- is presentation state rather than semantic identity;
- may change between versions;
- may contain gaps.

### 8.3 Value modes

Supported modes are:

```text
SCALAR
LIST
```

Property cardinality belongs to the declaration, not to DataTypeVersion.

Normal post-publication evolution permits:

```text
SCALAR -> LIST
```

and forbids:

```text
LIST -> SCALAR
```

A future explicit controlled migration capability would be required to support normal narrowing.

### 8.4 Exact DataTypeVersion binding

Every persisted declaration materializes:

```text
(datatype_id, datatype_version)
```

A command may select:

```text
an explicit exact DataTypeVersion
or
the current DataType default resolved once at admission
```

Every new or rebound exact selection must target a PUBLISHED DataTypeVersion and be stabilized through commit.

No floating DataType default, latest or highest reference is persisted.

Preserving an exact historical pin already owned by a cloned DRAFT is not a new binding, but the final RDV cannot be published unless that dependency is PUBLISHED.

All persisted declarations, regardless of RDV lifecycle state, require their exact DataTypeVersion to remain physically available as historical dependency state. Persistence realizes this lifetime requirement.

---

## 9. Historical property identity and evolution

Relationship property continuity uses:

```text
RelationshipPropertySemanticKey
    = (relationship_definition_id, name)
```

### 9.1 Editorial state before first publication

A property that has never appeared in any PUBLISHED version remains editorial.

Within a well-formed DRAFT, normal revision may change:

```text
name
DataType lineage
exact DataTypeVersion
value mode
position
```

### 9.2 Stable history after first publication

After first publication of a semantic property:

- `name` is stable;
- `datatype_id` is stable;
- exact `datatype_version` may evolve;
- `position` may evolve;
- `SCALAR -> LIST` is allowed;
- `LIST -> SCALAR` is forbidden in M2 normal evolution.

A property may be absent from later versions.

If the same Definition later reintroduces the same name, it retains the same historical semantic identity. Remove/re-add cannot reset DataType-lineage or value-mode evolution constraints.

Properties with the same name in different RelationshipDefinitions are different semantic properties.

---

## 10. Active model dependency semantics

A PUBLISHED RelationshipDefinitionVersion is an active model-plane consumer.

Every direct exact DataTypeVersion dependency of a PUBLISHED RDV must remain PUBLISHED.

Therefore:

```text
PUBLISH RDV
    races consistently with
DTV DEPRECATE

PUBLISHED RDV property dependency
    blocks DTV DEPRECATE

DRAFT or DEPRECATED RDV dependency
    does not block DTV DEPRECATE
```

The active invariant applies to direct dependencies.

Recursive validity follows from each PUBLISHED dependency-owning model being independently certified.

Lifecycle changes do not rewrite existing declarations or factual Relationship state.

---

## 11. Factual Relationship state

A factual Relationship owns authoritative current state:

```text
id
relationship_definition_id
relationship_definition_version
properties
complete RuntimeRelationshipResolution closure
```

`id` remains a kernel-generated opaque immutable factual identity.

`relationship_definition_id` remains the stable relationship-type binding.

`relationship_definition_version` is the exact current property-schema pin.

No default/latest/highest selector is persisted.

All object-relative views of one fact observe the same exact pin and property state.

Properties never belong to an individual RelationshipResolution or RuntimeRelationshipResolution.

### 11.1 Valid exact source state

A current fact may be pinned only to an RDV that is:

```text
PUBLISHED
or
DEPRECATED
```

A factual pin to DRAFT is invariant corruption.

A later RDV deprecation does not invalidate the fact.

### 11.2 Canonical properties

`properties` is the complete current factual value state.

Rules:

- only names declared by the exact pinned RDV may be present;
- every present value is validated through the declaration's exact DataTypeVersion;
- canonical PrimitiveType representations are reused from the delivered kernel;
- JSON null is forbidden;
- unknown properties are forbidden;
- optional empty LIST canonicalizes to property absence;
- LIST ordering is semantic;
- JSON object key ordering is not semantic;
- `{}` represents zero valued properties.

Persisted state that violates the exact pinned schema is invariant corruption and is never treated as supported legacy state.

---

## 12. Preserved factual endpoint semantics and uniqueness

Public factual selection remains based on:

```text
resolution_id
from_object_id
to_object_id
```

The selected Resolution determines the requested semantic perspective.

Endpoint admission continues to depend only on stable `Object.template_id` lineage compatibility.

It does not depend on:

```text
Object exact ObjectTemplateVersion
Object properties
Object canonical name
Object ownership
ObjectTemplate default
ObjectTemplateVersion lifecycle
Relationship property values
RelationshipDefinitionVersion number
```

### 12.1 Non-symmetric fact

For reciprocal perspectives `R1` and `R2`:

```text
R1 / A -> B
```

is the same fact as:

```text
R2 / B -> A
```

and is distinct from the opposite role assignment unless the actual endpoint/self-loop semantics collapse it.

### 12.2 Symmetric fact

The endpoint pair is semantically unordered.

Any applicable perspective/assignment expressing the same unordered pair identifies the same fact.

### 12.3 Self-loop

`(A, A)` remains allowed whenever lineage admission permits it.

### 12.4 Factual uniqueness

Uniqueness depends only on:

```text
stable RelationshipDefinition
+
endpoint assignment under symmetric/non-symmetric semantics
```

It does not depend on:

```text
RDV pin
property schema
property values
default policy
```

Properties cannot create parallel multi-edge instances of one semantic fact.

Any exact resolved view required by a candidate closure already owned by a current fact prevents creation of a distinct candidate and identifies a factual conflict.

---

## 13. Deterministic complete runtime closure

Every fact materializes exactly the complete deterministic set of object-relative resolved views required by the stable Definition.

Exact runtime-view identity remains:

```text
(resolution_id, from_object_id, to_object_id)
```

There is no surrogate runtime-row identity.

Every runtime row must:

- belong to the same Relationship and stable Definition as the header;
- reference a Resolution owned by that Definition;
- use only the one factual endpoint pair;
- satisfy stable endpoint-lineage compatibility.

The aggregate must contain:

```text
all required exact views
no extra exact view
no duplicate exact view
```

Non-symmetric and symmetric closure derivation remains exactly as delivered, including:

```text
non-symmetric reciprocal closure
symmetric unordered-pair assignments
self-loop behavior
inheritance-overlap behavior
bounded closure size
```

RDV lifecycle, exact schema pin and properties never change closure membership.

A DATA_CHANGE or SCHEMA_CHANGE therefore never rewrites the closure.

---

## 14. Factual CREATE

CREATE describes only the birth of a new factual identity.

### 14.1 Exact schema selection

The command selects:

```text
an explicit exact same-Definition RDV
or
the stable Definition default resolved once
```

The selected target must remain PUBLISHED through commit.

If implicit selection finds no default, CREATE fails even when other PUBLISHED versions exist.

No latest/highest fallback exists.

### 14.2 Initial properties

The command supplies one complete initial property candidate.

Omission means:

```text
{}
```

The candidate is validated and canonicalized against the selected exact RDV and all exact DataTypeVersion pins.

### 14.3 Candidate validation and factual conflict

The complete requested candidate is validated before factual uniqueness is used to classify the operation.

An invalid endpoint, version or property candidate does not become successful or a mere duplicate solely because a similar fact already exists.

After candidate validity is established:

```text
fact unoccupied
    -> generate one new Relationship identity
    -> persist exact pin, canonical properties and complete closure
    -> produce one complete creation lifecycle event set

same semantic fact or required exact view already current
    -> factual conflict
    -> identify the current conflicting fact
    -> no current-state mutation
    -> no lifecycle event
```

M2 does not retain delivered CREATE convergence.

Equivalent concurrent candidates may commit at most one new fact. Final arbitration and fresh re-evaluation must produce the same conflict semantics for a loser while the winner remains current.

---

## 15. Factual DATA_CHANGE

DATA_CHANGE applies a semantic operation set to the fresh complete current factual property state.

Operations are:

```text
SET(property, value)
REMOVE(property)
```

Rules:

```text
non-empty operation set
at most one operation per property
operation order is non-semantic
```

DATA_CHANGE:

- uses the already-pinned exact RDV;
- does not resolve or change a default;
- does not change stable Definition binding;
- does not change the runtime closure;
- introduces no factual state revision or expected revision;
- derives one complete canonical candidate after current-state stabilization.

A fact pinned to a DEPRECATED RDV remains mutable under that immutable exact schema.

### 15.1 Semantic no-op

If the resulting canonical property state equals current state:

```text
operation succeeds
no persisted factual update
no lifecycle event
```

Examples include:

```text
SET to the same canonical value
REMOVE of an already-absent property
```

A real change replaces the complete property state atomically and produces the complete Object-relative DATA_CHANGE event set.

---

## 16. Factual SCHEMA_CHANGE

SCHEMA_CHANGE is an explicit forward migration within the same stable RelationshipDefinition.

```text
source
    current exact RDV pin
    PUBLISHED or DEPRECATED

target
    exact same-Definition RDV
    target.version > source.version
    PUBLISHED through commit
```

Migration is direct source-to-target.

The operation never traverses or consults:

```text
intermediate versions
Definition default
latest version
highest version
```

### 16.1 Property continuity

Continuity uses:

```text
(relationship_definition_id, property name)
```

For each target property:

```text
matching source semantic property with current value
    -> preserve the value
    -> apply SCALAR -> LIST widening when required
    -> validate and canonicalize against target exact DTV
    -> incompatibility blocks the entire migration

matching source semantic property without current value
    -> remain absent

new target property
    -> absent

source-only property
    -> removed from result
```

There is no:

```text
migration default
caller remediation payload
implicit coercion
extras/archive/preservation bucket
```

Existing information is preserved or the operation fails with a property blocker. A migration default never overwrites an incompatible value because Relationship properties have no migration defaults.

### 16.2 Atomic state transition

Success atomically changes:

```text
relationship_definition_version
properties
```

and preserves:

```text
Relationship identity
stable Definition binding
endpoint pair
runtime closure
```

The schema change is always a real transition because the exact pin changes, even when the resulting property map is equal.

A failure leaves source pin, source properties and closure unchanged and emits no event.

---

## 17. Factual DELETE

DELETE targets one exact Relationship identity.

```text
current exact ID
    -> remove factual header and complete owned runtime closure
    -> produce one complete Object-relative deletion event set
    -> successful real transition

absent exact ID
    -> exact resource not found
    -> no mutation
    -> no event
```

DELETE does not identify a fact by endpoint tuple and never removes a later semantically equivalent Relationship with a different UUID.

Exact-ID ABA safety remains preserved.

DELETE does not cascade semantically to:

```text
endpoint Objects
stable Definition
RelationshipDefinitionVersion
RelationshipResolution
DataTypeVersion
historical lifecycle events
```

---

## 18. Model lifecycle versus existing facts

Model-plane lifecycle/default operations never reinterpret current facts.

```text
RDV PUBLISH
RDV DEPRECATE
SET_DEFAULT
CLEAR_DEFAULT
```

do not update:

```text
Relationship rows
exact factual pins
factual properties
runtime closures
historical events
```

After RDV deprecation:

```text
existing fact GET
    -> valid

existing fact DATA_CHANGE
    -> valid under pinned immutable schema

existing fact SCHEMA_CHANGE
    -> deprecated source allowed

new CREATE on deprecated RDV
    -> forbidden
```

Default changes affect only later implicit CREATE.

A Definition with no PUBLISHED version remains available to model-plane reads and stable conflict certification but exposes no currently usable runtime capability.

---

## 19. Capability semantics

M2 distinguishes two predicates.

### 19.1 Topological applicability

The delivered predicate remains:

```text
requested ObjectTemplate lineage
    == Resolution.from_template_id
or
requested lineage is a descendant of Resolution.from_template_id
```

The expected endpoint compatibility space remains `to_template_id`, lineage-polymorphic.

Topological applicability is independent of exact ObjectTemplateVersion state.

### 19.2 Current runtime usability

A topologically applicable Resolution is a currently usable Relationship capability only when its Definition owns at least one PUBLISHED RDV.

```text
only DRAFT versions
    -> not currently usable

only DEPRECATED versions
    -> not currently usable

at least one PUBLISHED version
    -> currently usable

PUBLISHED exists and default is null
    -> usable for explicit exact selection
    -> not usable for implicit selection
```

Capability usability does not select or inline an exact schema. Exact selection remains a CREATE concern.

---

## 20. Relationship lifecycle semantics

Relationship transitions remain projected into the unified Object lifecycle stream.

No standalone Relationship timeline is introduced.

A real transition emits exactly one event for every distinct Object-relative semantic view, not one event for every raw runtime row.

The complete event set is atomic with its factual mutation.

### 20.1 Historical metadata

Each event records the Object-relative semantic context observed for that transition:

```text
subject Object identity and historical canonical name
destination Object identity and historical canonical name
Relationship identity
stable Definition identity
historical Resolution navigation name
```

Names are historical values, not live references.

A transition concurrent with Object or Resolution rename observes one coherent committed metadata generation for its complete fan-out. Mixed old/new metadata inside one event set is invalid.

### 20.2 Historical factual state

The mutable factual snapshot is:

```text
RelationshipFactualState
    relationship_definition_version
    properties
```

It does not duplicate:

```text
Relationship identity
Definition identity
views
Resolution identities
Object names
schema declarations
DataType metadata
```

Those values are either event metadata or model-plane state.

Historical factual state is self-contained and remains meaningful after deletion of current Relationship, Definition, version, DataType or endpoint Objects.

### 20.3 Transition meanings

```text
RELATIONSHIP_CREATED
    before = null
    after  = initial factual state

RELATIONSHIP_DATA_CHANGE
    before = same exact version + previous properties
    after  = same exact version + changed properties

RELATIONSHIP_SCHEMA_CHANGE
    before = source exact version + source properties
    after  = forward target exact version + migrated properties

RELATIONSHIP_DELETED
    before = final factual state
    after  = null
```

A DATA_CHANGE no-op emits no event.

A valid SCHEMA_CHANGE always emits events.

The lifecycle public surface remains read-only.

---

## 21. Aggregate integrity and corruption boundary

A persisted factual Relationship is semantically valid only when all of the following hold:

```text
header
    stable Definition exists
    exact same-Definition RDV exists
    RDV status is PUBLISHED or DEPRECATED
    properties are canonical under that exact schema

property schema
    complete declaration set is valid
    exact DataTypeVersion dependencies exist
    no dependency is DRAFT
    PUBLISHED RDV dependencies remain PUBLISHED

runtime closure
    every row belongs to the fact and stable Definition
    every Resolution belongs to that Definition
    endpoint Objects exist and are lineage-compatible
    row set equals the deterministic complete closure

public semantic views
    equal the expected distinct Object-relative view set
```

Persisted violation is internal invariant corruption.

Reads and mutations do not:

```text
repair a closure
drop an unknown property
re-canonicalize and persist corrupted data
rebind to default/latest/highest
silently ignore a missing dependency
return a partial page or aggregate
```

Caller-invalid candidate state and persisted corruption remain distinct failure classes.

---

## 22. Delete and lifetime semantics

### 22.1 Definition aggregate deletion

A root RelationshipDefinition owns:

```text
complete Resolution set
all RelationshipDefinitionVersions
all version property declarations
```

After semantic admission, root deletion removes that complete owned model-plane aggregate atomically.

Current factual Relationships are external lifetime references and block root deletion.

Root deletion never implicitly deletes factual Relationships or endpoint Objects.

The internal default pointer is policy state owned by the same aggregate and is not an independent semantic blocker of an otherwise admissible root deletion.

Historical lifecycle records remain.

### 22.2 Individual version deletion

Only a DRAFT exact version may be deleted individually, and the command requires the fresh expected generation.

Deletion removes the exact DRAFT and its owned declarations.

PUBLISHED and DEPRECATED versions are never individually deleted by normal M2 lifecycle commands.

A factual or default reference into DRAFT would be invariant corruption and must not be silently cascaded.

### 22.3 DataTypeVersion lifetime

Every persisted declaration retains a historical exact dependency and therefore protects the physical lifetime of the referenced DataTypeVersion.

Deleting an RDV consumer removes its declarations and their outgoing references; it does not delete the DataTypeVersion.

Deprecating an RDV preserves its declarations and exact dependency history while removing its active-model lifecycle blocker.

### 22.4 Factual aggregate deletion

A factual Relationship owns only its complete RuntimeRelationshipResolution closure.

Deleting the factual root removes that closure and nothing else from current model/data state.

---

## 23. Model-plane and data-plane separation

Publishing or revising model state never silently transforms factual state.

```text
new RDV
    -> new exact schema option

existing Relationship
    -> remains pinned to current exact schema

explicit SCHEMA_CHANGE
    -> only path that changes factual RDV pin
```

Model evolution does not:

```text
rewrite existing properties
migrate all facts
repair incompatible current values
change endpoint assignment
rebuild runtime closure
invent defaults
```

Likewise, factual property values do not alter Definition equivalence, Resolution conflict or model publication semantics.

---

## 24. Semantic concurrency obligations

This document defines required semantic outcomes; concurrency owners define their realization.

The committed model/data set must preserve at least:

```text
DRAFT freshness
    no lost complete-candidate update

version allocation
    one exact version identity per Definition/version

default validity
    null or exact same-Definition PUBLISHED

publication/dependency graph
    no PUBLISHED RDV with non-PUBLISHED direct DTV dependency

new binding admission
    selected RDV remains PUBLISHED through commit

factual uniqueness
    equivalent CREATE candidates commit at most one fact

factual complete-state serialization
    DATA_CHANGE and SCHEMA_CHANGE derive from fresh current state

delete exactness
    one real same-ID deletion transition

lifecycle completeness
    no partial event set

rename snapshot coherence
    one committed metadata generation per event set
```

The complete mutation census and pairwise interleaving matrix are owned by `concurrency-matrix.md`.

PostgreSQL locks, gates, retries, constraint arbitration and deadlock prevention are owned by `concurrency.md`.

Neither owner may weaken the semantic outcomes above.

---

## 25. Explicit M2 deltas from delivered Relationship AS-IS

M2 preserves all delivered Relationship guarantees except these frozen deltas.

### 25.1 Definition creation

Delivered:

```text
stable Definition immediately runtime-usable
```

M2:

```text
stable Definition + v1 DRAFT revision 1
default null
not runtime-usable until a version is PUBLISHED
```

### 25.2 Capability visibility

Delivered:

```text
topological applicability only
```

M2:

```text
topological applicability
+
at least one PUBLISHED RDV
```

### 25.3 Factual CREATE

Delivered:

```text
duplicate semantic fact converges successfully
```

M2:

```text
duplicate semantic fact is a factual conflict
no mutation
```

### 25.4 Factual state

Delivered factual header had no versioned property state.

M2 adds:

```text
exact RDV pin
canonical properties
```

without changing fact identity or closure.

### 25.5 Factual DELETE

Delivered:

```text
absence is idempotent success
```

M2:

```text
absence is exact resource not found
```

### 25.6 Lifecycle

Delivered Relationship events carried Object-relative metadata only.

M2 adds:

```text
factual before/after state
RELATIONSHIP_DATA_CHANGE
RELATIONSHIP_SCHEMA_CHANGE
```

No other Relationship semantic divergence is authorized by this document.

---

## 26. Key invariants

- Definition, Resolution and factual Relationship identities remain kernel-generated, opaque and stable.
- Definition symmetry and Resolution endpoint lineages/membership remain stable.
- Resolution name is mutable non-key metadata.
- Definition equivalence and cross-Definition conflict ignore version/property state.
- RDV exact identity is `(relationship_definition_id, version)`.
- RDV lifecycle is monotonic; PUBLISHED and DEPRECATED are immutable.
- DRAFT mutation and consumption use generation freshness.
- Every persisted DRAFT is well-formed.
- Default is null or exact same-Definition PUBLISHED.
- Every declaration uses an exact DataTypeVersion pin.
- Every Relationship property is optional and non-nullable when present.
- Historical property identity survives remove/re-add by the same Definition and name.
- Normal post-publication value-mode evolution is only SCALAR to LIST.
- Every PUBLISHED RDV direct exact DTV dependency remains PUBLISHED.
- Every factual Relationship persists one exact RDV pin and complete canonical properties.
- A current factual pin is PUBLISHED or DEPRECATED, never DRAFT.
- Properties and RDV version do not participate in factual uniqueness.
- Every factual Relationship has exactly its delivered deterministic complete runtime closure.
- DATA_CHANGE preserves the exact pin and closure.
- SCHEMA_CHANGE is explicit, forward, same-Definition and preserve-or-fail.
- DELETE is exact-ID based, non-idempotent on absence and ABA-safe.
- Model lifecycle/default changes never rewrite current facts.
- A real factual transition and complete Object-relative event set are atomic.
- Historical Relationship state is self-contained and independent of live current rows.
- Persisted invariant corruption is never silently remediated.
- Supported concurrent interleavings preserve every invariant above.

---

## 27. Contract traceability

This document is the primary architecture owner for:

```text
M2-OUT-01
    Versioned Relationship property schema

M2-OUT-02
    Safe version lifecycle and default policy

M2-OUT-03
    Exact typed factual Relationship state

M2-OUT-04
    Explicit factual Relationship mutations

M2-OUT-05
    Preservation of factual identity and runtime closure
```

It provides the semantic authority required by acceptance criteria:

```text
M2-AC-01 ... M2-AC-19
M2-AC-31
```

Shared ownership boundaries:

```text
wire-level realization
    -> api.md

state/lifecycle physical realization
    -> persistence.md

interleaving completeness
    -> concurrency-matrix.md

PostgreSQL realization
    -> concurrency.md

deterministic evidence
    -> verification.md
```

Final traceability must link each cited criterion to those coordinated owners without duplicating semantic authority.

---

## 28. Design closure status

The Relationship semantic design owned by this document is complete.

```text
stable topology preservation            CLOSED
RDV identity/lifecycle/default policy    CLOSED
property declaration semantics           CLOSED
historical property evolution            CLOSED
active dependency semantics               CLOSED
factual exact state and uniqueness        CLOSED
CREATE / DATA_CHANGE / SCHEMA_CHANGE      CLOSED
DELETE and lifetime semantics             CLOSED
capability semantic predicate             CLOSED
lifecycle semantic meaning                CLOSED
corruption boundary                       CLOSED
semantic concurrency obligations          CLOSED
```

No open Relationship-domain decision remains inside this owner.

Cross-owner realization, traceability and consistency closure have passed.

This document remains `NOT FROZEN` only until the dedicated architecture-set freeze transition is explicitly approved and committed.
