# M4 WIP — RelationshipDefinition model-plane review owner

**Status:** ACTIVE REVIEW FRONTIER / SINGLE FAMILY OWNER / REST CONTRACT REVIEW IN PROGRESS / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose and ownership

This document is the single current M4 WIP owner for the `RelationshipDefinition` model-plane family review.

It owns the current review decisions for:

```text
public REST capabilities and wire contracts
stable RelationshipDefinition semantic contract
RelationshipDefinitionVersion public contract
version/property authoring semantics
model-plane lifecycle interactions
relationship_definition_space applicability semantics
later data-path / cache / persistence / concurrency handoff
```

Everything under `wip/` remains globally non-normative and does not authorize implementation.

The current review starts caller-first from the REST contract. SQL, cache, lock/FK/UNIQUE arbitration, final DDL, migration/backfill and measured physical evidence remain later review/architecture work unless a public-contract decision intrinsically requires a semantic choice.

## Precedence and source material

This file is the current family review owner from this point forward.

The following file remains the upstream semantic-intent input:

```text
new-relationship-definition.md
```

It established the redesign direction that this owner consumes, including:

```text
NO autonomous RelationshipResolution entity
NO resolution_id model-plane identity
stable directional semantic names owned by RelationshipDefinition
explicit stable symmetric intent
compact Definition source of truth
relationship_definition_space as derived effective exact-template semantic closure
```

Existing distributed files remain source material / operation-specific evidence:

```text
relationshipdefinition-create-discovery.md
relationshipdefinition-create-next-discovery.md
relationshipdefinition-delete-discovery.md
relationshipdefinition-delete-draft-discovery.md
relationshipdefinition-deprecate-discovery.md
relationshipdefinition-get-discovery.md
relationshipdefinition-get-version-discovery.md
relationshipdefinition-list-definitions-discovery.md
relationshipdefinition-list-versions-discovery.md
relationshipdefinition-publish-discovery.md
relationshipdefinition-rename-discovery.md
relationshipdefinition-revise-discovery.md
relationshipdefinition-set-default-discovery.md
relationshipdefinition-clear-default-discovery.md
```

Those files may contain assumptions that predate the current redesign. In particular they must not override this owner where they still assume:

```text
autonomous relationship_resolutions persistence
resolution_id as public/model identity
mutable semantic RelationshipDefinition names / RENAME
max(existing version) + 1 allocation
public caller-supplied property position
```

Cross-domain version allocation is owned by:

```text
version-allocation.md
```

Therefore new exact RelationshipDefinitionVersion allocation uses the shared monotonic/no-reuse allocator direction rather than `max(existing)+1`.

General M4 principles remain owned by:

```text
general-domain-principles.md
```

---

# 1. Current capability inventory

The AS-IS RelationshipDefinition family exposed four GET capabilities and ten mutations.

M4 has already decided that the old `RENAME` capability does not survive because semantic names are stable relationship meaning, not mutable display metadata.

Current candidate family surface therefore contains thirteen capabilities pending completion of the mutation review:

```text
READS
    GET    /api/v1/core/relationship-definitions
    GET    /api/v1/core/relationship-definitions/{relationship_definition_id}
    GET    /api/v1/core/relationship-definitions/{relationship_definition_id}/versions
    GET    /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}

MUTATIONS STILL TO REVIEW
    POST   /api/v1/core/relationship-definitions
    POST   /api/v1/core/relationship-definitions/{relationship_definition_id}/create-next
    POST   /api/v1/core/relationship-definitions/{relationship_definition_id}/set-default
    POST   /api/v1/core/relationship-definitions/{relationship_definition_id}/clear-default
    POST   /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}/revise
    POST   /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}/publish
    POST   /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}/deprecate
    DELETE /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}
    DELETE /api/v1/core/relationship-definitions/{relationship_definition_id}
```

Removed capability:

```text
POST /api/v1/core/relationship-definitions/{relationship_definition_id}/rename
    -> REMOVE from M4 TO-BE surface
```

Changing one or both stable semantic names changes the RelationshipDefinition contract and requires a different Definition identity rather than an identity-preserving rename.

---

# 2. Shared public reference carriers

## 2.1 ObjectTemplate reference

RelationshipDefinition read projections expose both stable ObjectTemplate identity and a readable stable qualified name.

Current public reference carrier:

```text
ObjectTemplateReference
    id: UUID
    qualified_name: string
```

where:

```text
qualified_name = namespace + "." + name
```

`id` remains the authoritative stable identity. `qualified_name` is a readable derived presentation of the stable ObjectTemplate `(namespace, name)` identity.

## 2.2 DataType exact reference

RelationshipDefinitionVersion property projections expose one exact DataTypeVersion pin through:

```text
DataTypeVersionReference
    id: UUID
    qualified_name: string
    version: positive integer
```

where `id` is the stable DataType lineage identity, `qualified_name` is the derived stable `namespace.name`, and `version` selects the exact DataTypeVersion.

The property declaration does not inline DataType constraints or PrimitiveType semantics merely to make the RDV DTO self-contained. Those remain owned by the referenced DataTypeVersion.

---

# 3. RelationshipDefinition compact public semantics

The public Definition contract has no `resolution_id`.

A directional public semantic perspective is:

```text
RelationshipDefinitionPerspective
    name: string
    from_template: ObjectTemplateReference
    to_template: ObjectTemplateReference
```

Current perspective cardinality:

```text
symmetric = false
    -> exactly 2 perspectives
    -> reciprocal endpoint orientation
    -> distinct stable semantic names

symmetric = true, endpoint roots distinct/disjoint
    -> exactly 2 perspectives
    -> reciprocal endpoint orientation
    -> same stable semantic name

symmetric = true, same endpoint root
    -> exactly 1 perspective
    -> no duplicated reciprocal public perspective
```

The A/B compact persistence orientation is not exposed as privileged source/target domain meaning. Public perspectives express the semantic orientations directly.

---

# 4. RD-GET-01 — LIST RelationshipDefinitions

**State:** REST CONTRACT REVIEWED / CURRENT M4 CANDIDATE

## Route

```http
GET /api/v1/core/relationship-definitions
```

Body: none.

Query surface:

```text
cursor
    optional opaque cursor

limit
    optional positive integer
    default = 100
    range = 1..500
```

No additional RelationshipDefinition filters are currently part of this collection contract.

In particular M4 does not add speculative filters for:

```text
symmetric
endpoint template
semantic name
default_version
version status
```

A future caller/search requirement may reopen that boundary explicitly.

## Pagination semantics

The collection remains keyset-paginated by internal Definition identity semantics. Cursor representation is opaque and has no public ordering meaning beyond continuation of the same collection scope.

## Response

```text
200 OK

RelationshipDefinitionPage
    items[]: RelationshipDefinitionSummary
    next_cursor: string | null
```

Current summary shape:

```text
RelationshipDefinitionSummary
    id: UUID
    symmetric: bool
    default_version: positive integer | null
    perspectives[]: RelationshipDefinitionPerspective
```

The LIST intentionally does **not** return the complete inheritance-expanded applicability closure. It returns only the compact authored/current Definition contract.

## Failure semantics

Current generic read boundary:

```text
400 invalid_request
    malformed cursor/limit
    unknown or repeated query parameter
    request body present

500 internal_error
    persisted invariant corruption / persistence / infrastructure failure
```

The root collection has no path-selected RelationshipDefinition identity and therefore has no normal `404` outcome.

---

# 5. RD-GET-02 — GET one RelationshipDefinition

**State:** REST CONTRACT REVIEWED / CURRENT M4 CANDIDATE

## Route

```http
GET /api/v1/core/relationship-definitions/{relationship_definition_id}
```

Path:

```text
relationship_definition_id: UUID required
```

Query: none.

Body: none.

## Response

```text
200 OK
RelationshipDefinitionDetail
```

The detail contains the same compact Definition contract as the LIST summary plus the complete current effective applicability expressed in factored form per perspective.

```text
RelationshipDefinitionDetail
    id: UUID
    symmetric: bool
    default_version: positive integer | null
    perspectives[]: RelationshipDefinitionPerspectiveDetail
```

```text
RelationshipDefinitionPerspectiveDetail
    name: string

    from_template: ObjectTemplateReference
    to_template: ObjectTemplateReference

    applicability
        from_templates[]: ObjectTemplateReference
        to_templates[]: ObjectTemplateReference
```

Applicability meaning:

```text
from_templates
    = declared from-template root
      + every current stable ObjectTemplate subtype/descendant
        in that perspective's effective from-space

to_templates
    = declared to-template root
      + every current stable ObjectTemplate subtype/descendant
        in that perspective's effective to-space

for that semantic name:
    every from_templates element
    x
    every to_templates element
    = complete effective exact-template semantic cells
```

This is a **lossless factored REST projection** of the applicability closure. The REST contract does not mechanically expose one element per physical `relationship_definition_space` row and therefore does not force an `N x M` JSON fan-out when two independent effective endpoint sets can represent the same information.

`relationship_definition_space` remains a model-plane derived-state/relational concept; the public field is semantic `applicability` rather than a physical table projection.

## Failure semantics

```text
400 invalid_request
    malformed path UUID
    query/body not allowed

404 resource_not_found
    RelationshipDefinition path target does not exist

500 internal_error
    persisted invariant corruption / persistence / infrastructure failure
```

No normal `409` or `422` outcome belongs to this read.

---

# 6. RD-GET-03 — LIST RelationshipDefinitionVersions

**State:** REST CONTRACT REVIEWED / CURRENT M4 CANDIDATE

## Route

```http
GET /api/v1/core/relationship-definitions/{relationship_definition_id}/versions
```

Path:

```text
relationship_definition_id: UUID required
```

Body: none.

Query surface:

```text
status
    optional exact lifecycle enum
    DRAFT | PUBLISHED | DEPRECATED

cursor
    optional opaque cursor

limit
    optional positive integer
    default = 100
    range = 1..500
```

`status` is retained because lifecycle state is a native dimension of the version collection rather than a generic search predicate.

Cursor scope is bound at least to:

```text
collection kind
relationship_definition_id
status omitted/value
```

`limit` is not part of semantic cursor scope.

## Response

```text
200 OK

RelationshipDefinitionVersionPage
    items[]: RelationshipDefinitionVersionSummary
    next_cursor: string | null
```

Current summary item deliberately does not repeat the parent Definition id because the entire collection is already scoped by the path:

```text
RelationshipDefinitionVersionSummary
    version: positive integer
    revision: positive integer
    status: DRAFT | PUBLISHED | DEPRECATED
```

No property declaration payload is returned by the version collection.

## Existence semantics

```text
RelationshipDefinition absent
    -> 404 resource_not_found

RelationshipDefinition exists
+ no exact versions match the current collection/filter
    -> 200 OK
    -> items = []
    -> next_cursor = null
```

## Failure semantics

```text
400 invalid_request
    malformed relationship_definition_id
    invalid status
    invalid/incompatible cursor
    invalid limit
    unknown/repeated query parameter
    body present

404 resource_not_found
    parent RelationshipDefinition path target absent

500 internal_error
    persisted invariant corruption / persistence / infrastructure failure
```

No normal `409` or `422` outcome belongs to this read.

---

# 7. RD-GET-04 — GET exact RelationshipDefinitionVersion

**State:** REST CONTRACT REVIEWED / CURRENT M4 CANDIDATE

## Route

```http
GET /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}
```

Path:

```text
relationship_definition_id: UUID required
version: positive integer required
```

Query: none.

Body: none.

## Response

```text
200 OK
RelationshipDefinitionVersionDetail
```

Current detail shape:

```text
RelationshipDefinitionVersionDetail
    version: positive integer
    revision: positive integer
    status: DRAFT | PUBLISHED | DEPRECATED
    properties[]: RelationshipDefinitionProperty
```

The parent `relationship_definition_id` is not repeated in the response because it is already unambiguously selected by the resource URI. This is intentionally consistent with the LIST-version item shape.

Property carrier:

```text
RelationshipDefinitionProperty
    name: string
    value_mode: SCALAR | LIST
    datatype: DataTypeVersionReference
```

Expanded:

```text
RelationshipDefinitionProperty
    name
    value_mode
    datatype
        id
        qualified_name
        version
```

The public property DTO does **not** expose `position`.

## Property ordering / internal position

M4 retains an internal ordering field/ordinal for RelationshipDefinitionVersion property declarations, but classifies it as ordering/presentation metadata rather than property semantic identity.

Current direction:

```text
public CREATE/REVISE property input
    -> caller expresses order through the properties[] array order
    -> no explicit public position field

internal model/persistence
    -> derive/store position/ordinal from array order
    -> preserve it across the exact version

CREATE_NEXT
    -> clones the source property's preserved internal order

public GET exact version
    -> properties[] returned in preserved internal order
    -> no explicit position field
```

`position` therefore is not:

```text
property identity
validation semantics
DataType compatibility semantics
migration semantics
factual Relationship property-map semantics
```

The stable historical property identity remains name-based according to the RelationshipDefinitionVersion contract unless a later focused review explicitly reopens that rule.

## Failure semantics

```text
400 invalid_request
    malformed relationship_definition_id
    malformed/non-positive version
    query/body not allowed

404 resource_not_found
    RelationshipDefinition absent
    OR exact RelationshipDefinitionVersion absent

500 internal_error
    persisted invariant corruption / persistence / infrastructure failure
```

The implementation may retain distinct resource detail internally/publicly for the missing Definition vs missing exact version case, but both are path-target `404 resource_not_found` outcomes.

No normal `409` or `422` outcome belongs to this read.

---

# 8. GET-family closure checkpoint

The four RelationshipDefinition GET capabilities are now reviewed at the REST-contract level:

```text
GET /relationship-definitions
    -> compact paginated Definition summaries

GET /relationship-definitions/{id}
    -> compact Definition detail
    -> + complete factored current applicability closure

GET /relationship-definitions/{id}/versions
    -> paginated lifecycle/version summaries
    -> optional status filter

GET /relationship-definitions/{id}/versions/{version}
    -> exact version detail
    -> complete ordered property declaration projection
```

Important M4 deltas from AS-IS:

```text
NO resolution_id in Definition REST representations
semantic perspectives replace autonomous Resolution DTOs
ObjectTemplate references expose id + qualified_name
Definition detail exposes factored applicability closure
LIST Definition does not expose that expanded closure
version LIST/detail do not repeat relationship_definition_id
property DataType pin uses nested id + qualified_name + version
property position is not public input/output
property array order is preserved through internal ordinal state
```

The GET-family REST contract is considered closed for the current review unless downstream model-plane analysis discovers a material semantic dependency that requires targeted revalidation.

---

# 9. RD-CREATE-01 — CREATE RelationshipDefinition

**State:** REST CONTRACT REVIEWED / CURRENT M4 CANDIDATE

## Route

```http
POST /api/v1/core/relationship-definitions
```

Query: none.

The command creates one new stable RelationshipDefinition together with its initial exact RelationshipDefinitionVersion:

```text
version = 1
status = DRAFT
revision = 1
default_version = null
```

The Definition and its exact v1 are one atomic operation-owned creation result even though the success response does not re-project both resources.

## Success contract

```text
201 Created
Location: /api/v1/core/relationship-definitions/{new_relationship_definition_id}
body: none
```

`Location` communicates the only server-allocated identity the caller needs to continue with the stable Definition resource. The initial exact version number/status/revision are deterministic command semantics, not additional generated result values requiring a response body.

CREATE therefore does not reconstruct the richer Definition GET detail or exact-version GET projection after mutation solely for response convenience.

## Topology authoring body

The current public topology authoring shape is flat and command-oriented:

```text
RelationshipDefinitionCreate
    symmetric: bool
    from_template_id: UUID
    to_template_id: UUID
    name: string
    reciprocal_name: string | conditionally omitted
    properties[]
```

There is deliberately no nested `perspective` object and no complete reciprocal `perspectives[]` authoring array.

The caller declares one oriented semantic statement directly:

```text
from_template_id --name--> to_template_id
```

and, only for asymmetric semantics, supplies the reciprocal semantic name.

### Symmetric form

```text
symmetric = true
name required
reciprocal_name forbidden
```

The reciprocal orientation necessarily uses the same semantic name.

Example:

```json
{
  "symmetric": true,
  "from_template_id": "<Router>",
  "to_template_id": "<Switch>",
  "name": "connected_to",
  "properties": []
}
```

### Asymmetric form

```text
symmetric = false
name required
reciprocal_name required
reciprocal_name != name
```

Example:

```json
{
  "symmetric": false,
  "from_template_id": "<VirtualMachine>",
  "to_template_id": "<Hypervisor>",
  "name": "runs_on",
  "reciprocal_name": "hosts",
  "properties": []
}
```

This expresses the complete semantic pair:

```text
VirtualMachine --runs_on--> Hypervisor
Hypervisor     --hosts----> VirtualMachine
```

without requiring the caller to duplicate reciprocal endpoint ids in a second object.

## Internal A/B mapping

The public `from/to` fields express the caller's authored orientation. The compact internal A/B representation may preserve that orientation without exposing storage-oriented A/B terminology in the REST contract:

```text
A = from_template_id
B = to_template_id
name_a_to_b = name

symmetric = true
    -> name_b_to_a = name

symmetric = false
    -> name_b_to_a = reciprocal_name
```

A/B remains stable authoring/persistence orientation, not privileged domain source/target meaning. The server does not canonicalize/reorder the caller-declared orientation merely to obtain a synthetic storage order.

The upstream topology rules remain authoritative and are classified through CREATE semantic validation rather than alternative DTO shapes. In particular:

```text
symmetric Definitions
    -> endpoint spaces must be identical or disjoint
    -> distinct-but-overlapping endpoint spaces are invalid

asymmetric Definitions
    -> endpoint spaces may be identical, disjoint or overlapping
```

## Property authoring body

The initial v1 DRAFT property schema uses a flat command carrier aligned with the common ObjectTemplate property-authoring pattern where the two domains share semantics:

```text
RelationshipDefinitionPropertyInput
    name: string
    datatype_id: UUID
    datatype_version: positive integer | omitted
    value_mode: SCALAR | LIST
```

`position` is not a public field. The caller expresses presentation/order intent through the order of `properties[]`; CREATE derives and stores the internal ordinal from that array order.

DataType selection semantics:

```text
datatype_id
    -> required stable DataType lineage selector

datatype_version present
    -> select that exact DataTypeVersion

datatype_version omitted
    -> resolve the current DataType.default_version
    -> materialize the resulting exact pin in the new RDV declaration

datatype_version = null
    -> invalid request
```

New RelationshipDefinitionVersion property bindings admit only an exact DataTypeVersion that is currently valid for new model binding according to the owning DataType lifecycle contract; the exact selected pin is persisted regardless of whether it was explicit or resolved through the current default.

Initial property-list omission semantics:

```text
properties omitted
    -> exactly empty initial property schema

properties = []
    -> exactly empty initial property schema

properties = null
    -> invalid request
```

Property names remain unique within the exact version; property historical semantic identity remains name-based. `value_mode` remains explicit caller intent and is not inferred.

### Cross-family ObjectTemplate alignment

The RelationshipDefinition property command intentionally shares the common flat authoring subset with ObjectTemplate:

```text
name
datatype_id
datatype_version?    # omission resolves current DataType default
value_mode
```

ObjectTemplate adds only domain-owned fields that do not apply to RelationshipDefinition:

```text
required
migration_default
```

This is deliberate semantic uniformity rather than forced DTO identity.

The current delivered ObjectTemplate wire still exposes explicit `position`. M4 has now classified RelationshipDefinition `position` as internal ordering metadata and removed it from public input/output. That difference is recorded as a targeted ObjectTemplate REST revalidation point when the ObjectTemplate family receives its own caller-first contract sweep; it does not reopen the RelationshipDefinition decision and does not silently change ObjectTemplate here.

## Failure semantics

CREATE has no normal `404` outcome because the route targets the collection rather than an existing RelationshipDefinition path resource.

```text
400 invalid_request
    malformed/invalid JSON or command shape
    symmetric not a strict boolean
    malformed UUID / datatype_version / value_mode
    reciprocal_name missing when symmetric=false
    reciprocal_name present when symmetric=true
    properties = null
    datatype_version = null
    unknown fields / other statically invalid wire input

422 referenced_resource_not_found
    from_template_id lineage absent
    to_template_id lineage absent
    datatype_id lineage absent
    explicitly selected exact datatype_version absent

422 semantic_validation_failed
    candidate violates an intrinsic RelationshipDefinition/RDV rule
    examples include:
        symmetric endpoint spaces are distinct-but-overlapping
        asymmetric name == reciprocal_name
        duplicate property names
        semantic/property naming grammar violation

409 default_version_unavailable
    datatype_version omitted
    + DataType lineage exists
    + no current default can be selected

409 dependency_not_admissible
    selected exact DataTypeVersion exists
    + is not currently admissible for a new model binding

409 relationship_definition_conflict
    candidate is intrinsically valid
    + at least one candidate semantic cell is already owned by current model state

500 internal_error
    persisted invariant corruption / persistence / infrastructure failure
```

The old public distinction:

```text
relationship_definition_equivalent
relationship_definition_conflict
```

is removed from the current M4 candidate. A complete semantic-equivalence collision is simply the maximal case of semantic-cell ownership conflict and therefore uses the single code:

```text
relationship_definition_conflict
```

## `relationship_definition_conflict` bounded witness

The conflict details expose at most one sufficient semantic-cell witness:

```text
details
    relationship_definition_id
    semantic_cell
        from_template_id
        name
        to_template_id
```

Example shape:

```json
{
  "code": "relationship_definition_conflict",
  "message": "The requested RelationshipDefinition conflicts with existing relationship semantics.",
  "details": {
    "relationship_definition_id": "<existing-definition-id>",
    "semantic_cell": {
      "from_template_id": "<template-id>",
      "name": "hosts",
      "to_template_id": "<template-id>"
    }
  }
}
```

If multiple cells or Definitions conflict, the public contract does not promise which valid witness is returned. The operation does not enumerate all conflicts and does not perform additional backend work solely to enrich the diagnostic. The witness must derive from the ordinary efficient certification/arbitration path.

## CREATE REST closure checkpoint

The CREATE REST contract is reviewed for the current M4 candidate:

```text
POST /relationship-definitions
    -> flat semantic topology body
    -> optional initial properties[]
    -> DataType default-or-exact selection
    -> array-order -> internal ordinal
    -> atomic stable Definition + v1 DRAFT revision 1
    -> 201 + stable Definition Location
    -> no response body
    -> one model semantic-cell conflict code
```

Downstream data-path/physical/concurrency work may choose how to realize these semantics but must not silently reintroduce autonomous Resolution identity, public `position`, Definition-equivalent error branching or response-only aggregate reconstruction.

---

# 10. Current next review frontier

Current next family micro-point:

```text
RelationshipDefinition CREATE_NEXT
    -> exact route/body
    -> source-version eligibility
    -> shared monotonic/no-reuse target version allocation
    -> success acknowledgement / Location
    -> finite public failure vocabulary
```

Then continue with REVISE, PUBLISH, default management, DEPRECATE and deletion separately.
