# M2 WIP — Relationship Properties and Versioned Relationship Schema

**Status:** API/SEMANTIC DISCOVERY CLOSED — PERSISTENCE DESIGN NOT STARTED

**Authority:** DISCOVERY CAPTURE — NON-NORMATIVE

This document captures the M2 discovery and API-semantic design decisions for introducing typed properties on factual `Relationship` resources and a versioned property schema on `RelationshipDefinition`.

It is an execution aid under `wip/`. It does not replace `contract.md`, the M2 architecture set, `steps.md`, the current delivered AS-IS, the persistence authority, the concurrency matrix, or the verification registries. The decisions below must later be assigned to the appropriate normative M2 architecture owners before implementation is authorized.

No physical table layout, migration DDL, lock layout, PostgreSQL realization, or verification scenario is ratified by this file. The persistence phase starts only after this semantic/API closure.

---

## 1. Closure result

Four explicit checks were completed before persistence design.

```text
semantic cross-check with AS-IS       -> PASS
functional cross-check with AS-IS     -> PASS
compatibility cross-check with AS-IS  -> PASS, with explicit M2 delta register
API contract consistency closure      -> PASS
```

The governing comparison is:

```text
MODEL PLANE

ObjectTemplate
    <-> RelationshipDefinition

ObjectTemplateVersion
    <-> RelationshipDefinitionVersion

RUNTIME / DATA PLANE

Object
    <-> Relationship
```

The design deliberately reuses the M1 solutions for equivalent problems. Differences remain only where the domains are genuinely different:

- `RelationshipDefinition` owns stable topology/navigation semantics rather than namespace, inheritance, components or abstractness;
- `RelationshipDefinitionVersion` contains only the complete property schema and has no inheritance/effective-schema layer;
- all M2 Relationship properties are optional;
- factual Relationship identity is a semantic fact with uniqueness rules that have no Object equivalent;
- Relationship lifecycle events are object-relative projections, not an intrinsic Relationship timeline.

---

## 2. Responsibility split

The M2 Relationship model separates stable topology, exact versioned property schema and factual runtime state.

```text
RelationshipDefinition
    -> stable relationship-type identity
    -> symmetry
    -> complete stable RelationshipResolution set
    -> endpoint ObjectTemplate lineage spaces
    -> mutable Resolution names
    -> default RelationshipDefinitionVersion policy

RelationshipDefinitionVersion
    -> exact versioned property-schema snapshot
    -> DRAFT/PUBLISHED/DEPRECATED lifecycle
    -> DRAFT generation revision
    -> complete property declarations
    -> exact DataTypeVersion pins

Relationship
    -> factual relationship identity
    -> stable RelationshipDefinition binding
    -> exact RelationshipDefinitionVersion pin
    -> canonical current properties
    -> complete deterministic RuntimeRelationshipResolution closure
```

Properties belong exclusively to the factual `Relationship`.

They do not belong to:

```text
RelationshipResolution
RuntimeRelationshipResolution
one individual object-relative view/perspective
```

All views of one factual Relationship observe the same property state.

---

## 3. Stable RelationshipDefinition contract

The M1 topology/navigation contract remains authoritative and stable.

A `RelationshipDefinition` continues to own:

```text
id
symmetric
complete resolutions[]
```

M2 adds:

```text
default_version: integer | null
```

The following remain stable Definition-level state and are not copied into each version:

```text
symmetry
Resolution identity and membership
Resolution from/to ObjectTemplate lineage
Resolution names
```

Changing symmetry, endpoint lineage, Resolution membership or Resolution cardinality still defines a different relationship type and requires a new Definition.

`RelationshipDefinition.RENAME` remains a mutation of the stable Definition aggregate:

- it changes Resolution names while preserving Resolution IDs and endpoint lineages;
- it recertifies the complete topology/navigation candidate against M1 equivalence and cross-Definition conflict rules;
- it does not create a new `RelationshipDefinitionVersion`;
- it does not change any version revision or lifecycle state;
- it does not change factual Relationship exact-version pins.

Definition semantic equivalence and cross-Definition Resolution conflict remain topology/navigation concerns. Property schemas, version numbers and property values do not distinguish otherwise equivalent relationship types.

A Definition with only DRAFT property-schema versions still exists as stable certified topology and participates in the Definition equivalence/conflict set, although it is not exposed as a currently usable runtime capability.

---

## 4. RelationshipDefinitionVersion model

### 4.1 Exact identity

The exact identity is composite:

```text
(relationship_definition_id, version)
```

Rules:

```text
version > 0
version is local to one RelationshipDefinition
no surrogate RelationshipDefinitionVersion UUID
```

### 4.2 Lifecycle

Lifecycle is identical to `ObjectTemplateVersion`:

```text
DRAFT -> PUBLISHED -> DEPRECATED
```

No reverse transition exists.

`PUBLISHED` and `DEPRECATED` are immutable snapshots.

A Definition may own multiple DRAFT versions concurrently. Each has an independent exact version and `revision`.

### 4.3 Version allocation

New version allocation uses:

```text
max(currently existing versions) + 1
```

Gaps are allowed. If the highest DRAFT is deleted, its version number may be reused. No irreversible audit sequence is introduced.

### 4.4 Initial version

`RelationshipDefinition.CREATE` atomically creates:

```text
RelationshipDefinition stable header
complete RelationshipResolution set
RelationshipDefinitionVersion v1
    status = DRAFT
    revision = 1
    complete initial property schema
```

An omitted initial `properties` field means an empty schema. An empty schema is still an exact versioned schema.

### 4.5 CREATE_NEXT

`CREATE_NEXT`:

- selects one exact source version in the same Definition;
- accepts a `PUBLISHED` or `DEPRECATED` source, never a DRAFT;
- the source need not be the numerically highest version;
- clones the complete property-schema snapshot exactly;
- creates a new DRAFT with `revision = 1`;
- does not opportunistically upgrade DataType dependencies;
- does not persist a `derived_from` domain relation.

A clone may therefore contain historical exact DataTypeVersion pins that are now DEPRECATED. The DRAFT remains well-formed but cannot be published until every active dependency requirement is satisfied.

### 4.6 DRAFT freshness

`revision` is the generation token of the complete DRAFT property-schema candidate.

The following require `expected_revision`:

```text
REVISE
PUBLISH
DELETE_DRAFT
```

A successful `REVISE` always increments `revision` exactly once, including when the canonical replacement is identical to the previous candidate.

`PUBLISH` checks `expected_revision` but does not increment it. `DELETE_DRAFT` removes the exact generation.

`DEPRECATE` has no `expected_revision`: it targets an immutable exact PUBLISHED snapshot, is atomic and irreversible, and leaves revision unchanged.

Lifecycle commands are not idempotent:

```text
PUBLISH on non-DRAFT        -> lifecycle_state_conflict
DEPRECATE on non-PUBLISHED  -> lifecycle_state_conflict
second DELETE_DRAFT         -> resource_not_found
```

### 4.7 REVISE

`REVISE` is complete replacement of the DRAFT property-schema candidate.

```text
properties required in request
properties=[] means empty schema
omission does not mean preserve current state
request-array order is not semantic
position is the ordering authority
```

The body cannot mutate stable Definition topology.

### 4.8 DRAFT validity and publication certification

Every persisted DRAFT must remain structurally and semantically well-formed after CREATE, CREATE_NEXT or REVISE.

A DRAFT may be well-formed but not currently publishable.

Publication requires:

- current state is DRAFT;
- matching `expected_revision`;
- complete property schema is valid;
- every exact DataTypeVersion dependency is still PUBLISHED through commit.

A new or rebound DataTypeVersion selection is a lifecycle-sensitive admission and requires PUBLISHED state. Preserving an already-owned historical exact pin in a cloned/current DRAFT does not manufacture a new binding, but publication still requires the final active dependency set to be PUBLISHED.

---

## 5. Default version policy

`RelationshipDefinition.default_version` is:

```text
NULL
or
an exact PUBLISHED RelationshipDefinitionVersion
of the same Definition
```

Rules mirror ObjectTemplate M1:

- first publication with `default_version = NULL` establishes that version automatically;
- later publications do not replace the default automatically;
- `SET_DEFAULT` accepts only an exact PUBLISHED same-Definition version;
- `CLEAR_DEFAULT` sets the pointer to NULL;
- changing the default affects future implicit Relationship CREATE only;
- existing factual Relationships retain their exact pins;
- the current default cannot be deprecated;
- no fallback to latest/highest exists.

A Definition may have PUBLISHED versions and no default. In that state explicit Relationship version selection remains possible while implicit selection fails.

---

## 6. Relationship property declarations

A declaration contains exactly:

```text
name
position
datatype_id
datatype_version
value_mode
```

The following concepts are deliberately absent from the M2 contract:

```text
required
migration_default
nullable
```

### 6.1 Optional-only and non-nullable

All Relationship properties are optional.

```text
property absent                 -> valid
property present with value     -> valid if typed/canonical
property present with JSON null -> invalid
```

No migration default exists because a new property never makes an existing factual Relationship invalid merely through absence.

### 6.2 Name and ordering

Property names use:

```text
[a-z][a-z0-9_]*
maximum length = 64
```

No automatic lowercase, trimming or replacement is applied.

`position`:

- is positive;
- is unique within the exact version;
- is presentation/order state;
- may change between versions;
- is not part of property semantic identity;
- is the only ordering authority.

### 6.3 Value modes

Supported value modes are:

```text
SCALAR
LIST
```

After first publication, normal evolution permits:

```text
SCALAR -> LIST
```

and forbids:

```text
LIST -> SCALAR
```

without a future explicit controlled migration capability.

### 6.4 Exact DataTypeVersion binding

Every persisted declaration contains an exact pin:

```text
(datatype_id, datatype_version)
```

Request semantics:

```text
datatype_version supplied
    -> select that exact version
    -> new/rebound target must be PUBLISHED

datatype_version omitted
    -> resolve DataType.default_version
    -> default must exist and be PUBLISHED
    -> materialize the selected exact version

datatype_version = null
    -> invalid request
```

A PUBLISHED RelationshipDefinitionVersion is an active model consumer. Its exact DataTypeVersion property dependencies must remain PUBLISHED. A PUBLISHED RDV blocks deprecation of those direct dependencies. DRAFT and DEPRECATED RDVs do not.

### 6.5 Historical semantic identity

Property continuity uses:

```text
RelationshipPropertySemanticKey
    = (relationship_definition_id, name)
```

Before first publication, a property remains editorial and its name, DataType lineage and value mode may be revised while the DRAFT remains valid.

After first publication:

- `name` is stable;
- `datatype_id` is stable;
- exact `datatype_version` may evolve;
- `position` may evolve;
- `SCALAR -> LIST` is allowed;
- `LIST -> SCALAR` is forbidden in normal M2 evolution.

Remove/re-add by the same Definition and name preserves the same historical semantic identity and cannot reset evolution constraints.

---

## 7. Factual Relationship state

A factual Relationship M2 has authoritative state:

```text
id
relationship_definition_id
relationship_definition_version
properties
complete runtime-resolution closure
```

The exact version pin is persisted and never floating.

### 7.1 Canonical properties

`properties` is the complete current factual property state.

Rules mirror Object runtime state:

- only names declared by the exact pinned RDV may be present;
- values use the existing canonical PrimitiveType/DataType representation;
- every value satisfies the exact DataTypeVersion pin;
- JSON null is invalid;
- unknown properties are invalid;
- optional LIST zero-cardinality canonicalizes to property absence;
- LIST ordering is semantic;
- JSON object key ordering is not semantic;
- `{}` is the zero-property representation.

### 7.2 Factual uniqueness

Factual uniqueness continues to depend only on:

```text
stable RelationshipDefinition
+ endpoint assignment under the M1 symmetric/non-symmetric semantics
```

It does not depend on:

```text
RelationshipDefinitionVersion
property schema
property values
```

Properties do not create parallel multi-edge instances of the same fact.

### 7.3 CREATE

Request state:

```text
resolution_id
from_object_id
to_object_id
relationship_definition_version optional
properties optional
```

Version selection mirrors Object CREATE:

```text
explicit version
    -> exact same-Definition RDV
    -> must remain PUBLISHED through commit

version omitted
    -> resolve RelationshipDefinition.default_version
    -> default must exist and remain PUBLISHED

version = null
    -> invalid request
```

Property input:

```text
properties omitted -> {}
properties={}       -> {}
properties=null     -> invalid request
```

CREATE describes the initial complete property state and never mutates an existing fact.

M2 deliberately removes M1 CREATE convergence:

```text
fact absent
    -> create one factual Relationship
    -> 201 Created

same semantic fact already current
    -> 409 relationship_fact_conflict
    -> no mutation
    -> no lifecycle event
```

Concurrent equivalent CREATE operations may produce only one winner; losing candidates receive the same conflict after final arbitration.

### 7.4 DATA_CHANGE

`Relationship.DATA_CHANGE` mirrors `Object.DATA_CHANGE`.

```text
operations is non-empty
SET(property, value)
REMOVE(property)
at most one operation per property
operation-array order is non-semantic
```

The mutation:

- locks/stabilizes the factual Relationship;
- reloads the current committed state;
- uses only the already-pinned exact RDV;
- does not consult default/latest;
- derives a complete candidate state;
- validates/canonicalizes it against the exact schema;
- has no `expected_revision` and introduces no runtime `state_revision`.

A semantic no-op is successful but persists no change and emits no lifecycle event. Examples include SET to the same canonical value and REMOVE of an already-absent property.

A factual Relationship pinned to a DEPRECATED RDV remains valid and may continue to execute DATA_CHANGE under that immutable schema.

### 7.5 SCHEMA_CHANGE

`Relationship.SCHEMA_CHANGE` mirrors `Object.SCHEMA_CHANGE`.

```text
source = current exact RDV pin
target = exact version in the same RelationshipDefinition
target_version > source_version
target must remain PUBLISHED through commit
source may be PUBLISHED or DEPRECATED
```

Migration is direct source-to-target. Intermediate versions, current defaults, latest and highest are not traversed or consulted.

Property migration:

- continuity uses `(relationship_definition_id, name)`;
- an existing source value for the same semantic property is preserved;
- allowed `SCALAR -> LIST` widening is applied when needed;
- the preserved value is validated/canonicalized against the target exact DataTypeVersion;
- incompatibility blocks the entire migration with `schema_change_blocked`;
- source absence remains target absence;
- newly introduced optional properties start absent;
- source-only properties and values are removed;
- no extras/archive/preservation bucket exists;
- no caller remediation payload exists.

Every valid forward schema change is a real mutation even when `properties` remains byte/semantically identical, because the exact RDV pin changes.

Relationship identity, stable Definition binding, endpoint pair and runtime closure remain unchanged.

### 7.6 DELETE

`Relationship.DELETE` is aligned with `Object.DELETE`, not with the M1 idempotent Relationship delete.

```text
current exact relationship_id exists
    -> delete fact + complete runtime closure atomically
    -> emit one complete deletion event set
    -> 204 No Content

relationship_id absent/already deleted
    -> 404 resource_not_found
    -> no event
```

Exact-ID ABA safety remains: a stale delete for identity X can never delete a later semantically equivalent identity Y.

---

## 8. Read projections

### 8.1 RelationshipDefinition

Stable Definition GET/list items expose:

```text
id
symmetric
default_version
resolutions[]
    resolution_id
    name
    from_template_id
    to_template_id
```

Versions are not inlined.

### 8.2 RelationshipDefinitionVersion

Exact version GET exposes:

```text
relationship_definition_id
version
revision
status
properties[]
    name
    position
    datatype_id
    datatype_version
    value_mode
```

`properties[]` is ordered by `position`.

Version list summaries expose:

```text
relationship_definition_id
version
revision
status
```

and omit declarations.

### 8.3 Factual Relationship

Relationship GET and mutation responses expose:

```text
id
relationship_definition_id
relationship_definition_version
properties
views[]
    object_id
    destination_object_id
    name
```

Properties appear once at factual level, never inside each view.

### 8.4 Object-relative Relationship projection

Each item exposes:

```text
relationship_id
relationship_definition_id
relationship_definition_version
object_id
destination_object_id
name
properties
```

Exact version and property state are denormalized from the factual Relationship into the read projection. They are not autonomous view state.

### 8.5 Relationship capabilities

Topological applicability remains derived from stable Resolution endpoint lineage and ancestry.

The public capability projection now represents a capability currently usable for a new factual Relationship. A Resolution is returned only when:

```text
1. it is topologically applicable to the requested ObjectTemplate lineage
2. its RelationshipDefinition owns at least one PUBLISHED RDV
```

Consequences:

```text
only DRAFT versions       -> capability omitted
only DEPRECATED versions  -> capability omitted
at least one PUBLISHED    -> capability returned
PUBLISHED exists + no default -> capability returned, explicit version required
```

Capability item:

```text
resolution_id
relationship_definition_id
name
from_template_id
to_template_id
default_version: integer | null
```

The item does not inline version lists or property schemas.

---

## 9. Lifecycle events

Relationship lifecycle remains projected into Object lifecycle timelines. No standalone Relationship timeline is introduced.

A real factual transition emits one event for every distinct object-relative semantic view, not one event per raw runtime row. The complete set is atomic with the factual mutation.

Common top-level object-relative context:

```text
id
occurred_at
kind
object_id
canonical_name
destination_object_id
destination_canonical_name
relationship_id
relationship_definition_id
relationship_name
```

Mutable factual state snapshot:

```text
relationship_definition_version
properties
```

No `views[]` is duplicated in event snapshots because each record already represents one object-relative semantic view.

### 9.1 RELATIONSHIP_CREATED

```text
before = null
after  = {relationship_definition_version, properties}
```

### 9.2 RELATIONSHIP_DATA_CHANGE

```text
before = {same version, previous properties}
after  = {same version, resulting properties}
```

A semantic no-op emits no event.

### 9.3 RELATIONSHIP_SCHEMA_CHANGE

```text
before = {source version, source properties}
after  = {target version, migrated properties}
```

A valid schema change always emits the complete event set, even when the property map is unchanged.

### 9.4 RELATIONSHIP_DELETED

```text
before = {relationship_definition_version, final properties}
after  = null
```

A failed second delete emits no event.

Relationship event metadata continues to capture coherent historical Resolution/Object display names. Definition rename concurrency must not produce a mixed old/new name set.

---

## 10. Public API inventory

All routes remain under `/api/v1/core`.

### 10.1 RelationshipDefinition and versions

| Method | Route | Request | Success |
|---|---|---|---|
| POST | `/relationship-definitions` | existing M1 topology body + optional `properties` | `201`, `Location` stable Definition, `{relationship_definition, version}` |
| GET | `/relationship-definitions` | `cursor`, `limit` | `200`, paginated stable aggregates |
| GET | `/relationship-definitions/{id}` | none | `200`, stable aggregate |
| POST | `/relationship-definitions/{id}/rename` | existing M1 rename body | `200`, stable aggregate |
| POST | `/relationship-definitions/{id}/create-next` | `{source_version}` | `201`, `Location` exact version, exact RDV |
| POST | `/relationship-definitions/{id}/set-default` | `{version}` | `200`, stable aggregate |
| POST | `/relationship-definitions/{id}/clear-default` | no body | `200`, stable aggregate |
| GET | `/relationship-definitions/{id}/versions` | `status?`, `cursor`, `limit` | `200`, version summaries |
| GET | `/relationship-definitions/{id}/versions/{version}` | none | `200`, exact RDV |
| POST | `/relationship-definitions/{id}/versions/{version}/revise?expected_revision=N` | complete `properties` | `200`, revised exact RDV |
| POST | `/relationship-definitions/{id}/versions/{version}/publish?expected_revision=N` | no body | `200`, PUBLISHED exact RDV |
| POST | `/relationship-definitions/{id}/versions/{version}/deprecate` | no body | `200`, DEPRECATED exact RDV |
| DELETE | `/relationship-definitions/{id}/versions/{version}?expected_revision=N` | no body | `204` |
| DELETE | `/relationship-definitions/{id}` | no body | `204` |

Version list contract:

```text
order version ASC
optional status = DRAFT | PUBLISHED | DEPRECATED
standard opaque keyset cursor
limit default 100
limit range 1..500
no offset/page/total_count/generic sort
```

### 10.2 Factual Relationship

| Method | Route | Request | Success |
|---|---|---|---|
| POST | `/relationships` | selector/endpoints + optional exact version + optional properties | `201`, `Location`, factual Relationship |
| GET | `/relationships/{relationship_id}` | none | `200`, factual Relationship |
| POST | `/relationships/{relationship_id}/data-change` | non-empty SET/REMOVE operations | `200`, factual Relationship |
| POST | `/relationships/{relationship_id}/schema-change` | `{target_version}` | `200`, factual Relationship |
| DELETE | `/relationships/{relationship_id}` | no body | `204`; absent target is `404` |

Updated existing projections:

```text
GET /objects/{object_id}/relationships
GET /object-templates/{template_id}/relationship-capabilities
```

Existing lifecycle read routes remain unchanged; their discriminated union gains the new Relationship event kinds and factual before/after snapshots.

### 10.3 No standalone child resources

M2 does not introduce:

```text
/relationship-definition-versions top-level resource
standalone RelationshipResolution CRUD
standalone RelationshipDefinition property CRUD
standalone Relationship lifecycle timeline
```

---

## 11. Wire-shape closure

### 11.1 RelationshipDefinition CREATE

The current symmetric/non-symmetric discriminated topology body is retained. Both variants gain top-level optional `properties`.

```text
properties omitted -> []
properties=[]       -> empty v1 schema
properties=null     -> invalid_request
```

Caller cannot supply generated/stored lifecycle state:

```text
Definition ID
Resolution IDs
version
revision
status
default_version
```

Response:

```json
{
  "relationship_definition": {
    "id": "<uuid>",
    "symmetric": false,
    "default_version": null,
    "resolutions": []
  },
  "version": {
    "relationship_definition_id": "<uuid>",
    "version": 1,
    "revision": 1,
    "status": "DRAFT",
    "properties": []
  }
}
```

### 11.2 Property request

```text
name required
position positive integer
datatype_id UUID
datatype_version optional positive integer, explicit null forbidden
value_mode SCALAR | LIST
unknown fields forbidden
```

### 11.3 Relationship CREATE

```text
resolution_id required
from_object_id required
to_object_id required
relationship_definition_version optional positive integer, null forbidden
properties optional JSON object, null forbidden
unknown fields forbidden
```

`relationship_definition_id` is not accepted because `resolution_id` already determines the stable Definition.

### 11.4 DATA_CHANGE

```text
operations required and non-empty
SET requires property + value
REMOVE requires property and forbids value
one operation per property
wire duplicate -> invalid_request
JSON null SET value -> semantic validation failure
```

### 11.5 SCHEMA_CHANGE

```text
target_version required positive integer
no expected_revision
no target Definition ID
no remediation/properties payload
```

---

## 12. Error and success closure

The existing failure classes remain unchanged:

```text
INVALID_REQUEST       -> 400
NOT_FOUND             -> 404
SEMANTIC_VALIDATION   -> 422
STATE_CONFLICT        -> 409
INTERNAL_FAILURE      -> 500
```

No new public error code is required for this capability.

Reused codes include:

```text
invalid_request
resource_not_found
referenced_resource_not_found
semantic_validation_failed
stale_revision
lifecycle_state_conflict
version_source_conflict
default_version_unavailable
dependency_not_admissible
default_version_conflict
active_dependency_conflict
delete_blocked
schema_change_blocked
relationship_definition_equivalent
relationship_definition_conflict
relationship_fact_conflict
internal_error
```

Boundary rules:

```text
missing path target exact resource
    -> 404 resource_not_found

missing body/command operand
    -> 422 referenced_resource_not_found

invalid static body/query/null/duplicate operation
    -> 400 invalid_request

invalid typed candidate/value/evolution/forward target
    -> 422 semantic_validation_failed

mutable lifecycle/default/dependency/current-fact blocker
    -> 409 specific state-conflict code
```

`relationship_fact_conflict` is broadened to cover any requested fact already occupied by a current factual Relationship, including the exact same semantic fact and a distinct candidate closure collision. Bounded details expose the conflicting `relationship_id`.

`schema_change_blocked` is reused for current Relationship property values incompatible with the target schema, with bounded details:

```text
relationship_id
target_version
blocker_type = property
member_name
```

Success mapping:

```text
GET/read                         -> 200 + canonical body
new stable/exact/runtime resource -> 201 + Location + canonical body
normal semantic mutation        -> 200 + resulting canonical resource
successful delete               -> 204, no body
```

---

## 13. Semantic AS-IS cross-check matrix

| Equivalent responsibility | M1 authority | M2 Relationship decision | Result |
|---|---|---|---|
| stable model + initial DRAFT | ObjectTemplate CREATE | Definition + Resolution set + RDV v1 DRAFT revision 1 | aligned |
| exact version identity | `(template_id, version)` | `(relationship_definition_id, version)` | aligned |
| DRAFT freshness | expected revision on revise/publish/delete | identical | aligned |
| lifecycle/default policy | OTV lifecycle and lineage default | identical | aligned |
| complete schema replacement | OTV REVISE declarations | RDV REVISE properties | aligned |
| exact DTV property pin | ObjectTemplate property | RDV property | aligned |
| active dependency graph | PUBLISHED OTV blocks DTV deprecation | PUBLISHED RDV blocks DTV deprecation | aligned |
| runtime exact schema pin | Object template version | Relationship Definition version | aligned |
| runtime CREATE defaults | Object explicit/implicit exact version | Relationship explicit/implicit exact version | aligned |
| runtime canonical properties | Object properties | Relationship properties | aligned |
| runtime data mutation | Object SET/REMOVE, no runtime revision | Relationship SET/REMOVE, no runtime revision | aligned |
| runtime schema migration | Object forward same-lineage exact target | Relationship forward same-Definition exact target | aligned |
| runtime DELETE | Object absent target is 404 | Relationship absent target is 404 | aligned |
| collection contract | version lists and standard cursor | RDV list identical | aligned |
| public errors | stable finite code catalog | reused, no generic escape hatch | aligned |

Relationship event snapshots are intentionally not full Relationship DTOs. Object events are intrinsic-resource events, while Relationship events are object-relative structural projections. The top-level event already carries fact/view identity, so `before/after` contains only mutable factual schema/property state. This is semantic alignment, not mechanical DTO duplication.

---

## 14. Functional AS-IS cross-check

The following equal problems use equal solutions:

```text
mutable complete DRAFT candidate
    -> revision + expected_revision

implicit lifecycle-sensitive dependency selection
    -> resolve current default + persist exact pin

active published model dependency
    -> dependency must remain PUBLISHED

historical property continuity
    -> stable semantic key + remove/re-add continuity

runtime partial intent over complete JSON state
    -> semantic SET/REMOVE + lock + fresh reload

runtime schema evolution
    -> explicit forward exact-target migration

incompatible current data
    -> atomic schema_change_blocked

optional property absence
    -> no invented value/default

root aggregate deletion
    -> external references block; owned child state removed only after admission

real runtime transition
    -> state + complete lifecycle event set commit atomically
```

No M2 shortcut introduces a second solution for an already-solved M1 problem.

---

## 15. Compatibility closure with delivered M1 state

### 15.1 Preserved invariants

M2 does not reinterpret or weaken:

- stable Definition/Resolution identities;
- immutable symmetry and endpoint lineage topology;
- no privileged source/target orientation;
- Definition equivalence and cross-Definition Resolution conflict freedom;
- lineage-polymorphic endpoint admission;
- factual uniqueness under symmetric/non-symmetric semantics;
- deterministic complete runtime-resolution closure;
- exact resolved-view uniqueness;
- fact-level properties rather than view-level state;
- Object/Definition delete reference safety;
- lifecycle event fan-out by distinct semantic view;
- coherent historical name snapshots.

### 15.2 Mandatory lossless migration bridge

The future persistence design must preserve all currently delivered M1 data and behavior through this semantic bridge:

```text
for every existing M1 RelationshipDefinition
    -> create synthetic RDV version 1
       revision = 1
       status = PUBLISHED
       properties = []
    -> set default_version = 1

for every existing current M1 Relationship
    -> relationship_definition_version = 1
    -> properties = {}

for every historical M1 Relationship lifecycle event
    RELATIONSHIP_CREATED
        -> after = {relationship_definition_version: 1, properties: {}}
        -> before = null

    RELATIONSHIP_DELETED
        -> before = {relationship_definition_version: 1, properties: {}}
        -> after = null
```

Historical event backfill must not require a current live Definition FK. M1 lifecycle history is deliberately historical and may reference a Definition already deleted before M2.

This bridge preserves:

- current Relationship GET meaning;
- current factual uniqueness and closure;
- existing implicit Relationship CREATE requests, because migrated defaults are v1;
- existing relationship-capability membership, because every migrated Definition has a PUBLISHED v1;
- existing zero-property semantics;
- historical lifecycle interpretation.

### 15.3 Intentional M2 API/behavior deltas

These are explicit contract changes, not hidden compatibility assumptions:

1. `RelationshipDefinition.CREATE` response changes from the direct Definition DTO to `{relationship_definition, version}`.
2. `Relationship.CREATE` no longer converges on an existing fact; it returns `409 relationship_fact_conflict`.
3. `Relationship.DELETE` is no longer idempotent on absence; an absent exact ID returns `404 resource_not_found`.
4. A newly created M2 Definition has only a DRAFT v1 and is not usable for new Relationships until a version is PUBLISHED.
5. Relationship/Definition/read DTOs gain exact-version/default/property fields.
6. Relationship capability items gain `default_version` and are filtered when no PUBLISHED RDV exists.
7. Relationship lifecycle events gain factual snapshots and two new kinds: `RELATIONSHIP_DATA_CHANGE` and `RELATIONSHIP_SCHEMA_CHANGE`.

These deltas require explicit release notes, API tests and concurrency updates. They do not prevent a lossless migration of existing state.

---

## 16. API consistency closure checklist

```text
[PASS] every new path target has one canonical identity
[PASS] body operands are not misclassified as path targets
[PASS] semantically equal commands reuse status/body/Location contracts
[PASS] all DRAFT generation consumers use expected_revision uniformly
[PASS] no runtime state_revision is introduced only for Relationship
[PASS] omission and explicit null have distinct frozen meanings
[PASS] all persisted version-sensitive references are exact
[PASS] list routes reuse standard pagination/filter/order rules
[PASS] property ordering has one authority: position
[PASS] no property/Resolution child CRUD surface is introduced
[PASS] no generic conflict code is introduced
[PASS] CREATE, mutation and delete success mappings are closed
[PASS] factual DTO, object-relative DTO and capability DTO responsibilities do not overlap ambiguously
[PASS] lifecycle kinds and before/after nullability are closed
[PASS] M1 data has a lossless semantic migration bridge
[PASS] intentional breaking changes are enumerated explicitly
```

No unresolved API-semantic decision blocks persistence design.

---

## 17. Next design phase

The next phase is persistence design. It must determine, without changing the semantics above:

- authoritative relational representation of RDV and declarations;
- exact version/default foreign keys and ownership/delete actions;
- factual Relationship exact pin and canonical property storage;
- lifecycle snapshot storage and M1 backfill;
- migration ordering and integrity gates;
- indices and constraint-enforcement boundaries;
- interaction with existing runtime-resolution denormalization;
- resulting authoritative table count.

After persistence design, the capability still requires explicit concurrency-matrix, PostgreSQL realization and verification-registry closure before implementation.
