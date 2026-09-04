# M4 WIP — RelationshipDefinition model-plane review owner

**Status:** ACTIVE REVIEW FRONTIER / SINGLE FAMILY OWNER / REST CONTRACT REVIEW COMPLETE / TECHNICAL DISCOVERY CONSOLIDATION PENDING / M4 WIP / ALWAYS NON-NORMATIVE

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

The caller-first REST sweep is complete. The next step is **not** architecture closure: it is to revalidate and consolidate the technical discovery for this family — logical operation data paths, persistence/materialization candidates, cache boundaries, cost/over-fetch findings and explicit concurrency/architecture handoffs — until `RelationshipDefinition` reaches the same `REVIEWED BASELINE` discovery level already reached by Object and factual Relationship.

Final SQL, physical DDL, exact PK/FK/UNIQUE/index realization, lock/wait/retry/deadlock design, migration/backfill and other architecture-closing choices remain later work. They must not be silently frozen during this technical consolidation pass.

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

M4 has decided that the old `RENAME` capability does not survive because semantic names are stable relationship meaning, not mutable display metadata.

The current M4 REST candidate therefore contains thirteen reviewed capabilities:

```text
READS REVIEWED
    GET    /api/v1/core/relationship-definitions
    GET    /api/v1/core/relationship-definitions/{relationship_definition_id}
    GET    /api/v1/core/relationship-definitions/{relationship_definition_id}/versions
    GET    /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}

MUTATIONS REVIEWED
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

# 10. RD-CREATE-NEXT-01 — CREATE_NEXT RelationshipDefinitionVersion

**State:** REST CONTRACT REVIEWED / CURRENT M4 CANDIDATE

## Route and request

```http
POST /api/v1/core/relationship-definitions/{relationship_definition_id}/create-next
```

Query: none.

Body:

```text
RelationshipDefinitionCreateNext
    source_version: positive integer
```

`source_version` remains a command operand rather than a path target because the route operates on the stable RelationshipDefinition and asks the server to create a new exact version from one selected source.

## Source eligibility and clone semantics

The selected source exact RelationshipDefinitionVersion must exist in the same Definition and have lifecycle status:

```text
PUBLISHED | DEPRECATED
```

A DRAFT source is not eligible.

CREATE_NEXT clones the complete exact property declaration snapshot, including the preserved internal property order. It does not reinterpret the property schema through current defaults. When the immutable RDV cache has `snapshot READY`, CREATE_NEXT may use that exact cached declaration snapshot directly as the clone payload; on cache miss it performs a bounded cold load and may publish the snapshot facet. Cache presence does not prove current source existence or lifecycle eligibility: PostgreSQL remains authoritative for those current-state predicates.

The newly created version is:

```text
version
    -> allocated through the shared monotonic/no-reuse lineage allocator

revision = 1
status = DRAFT
properties = exact clone of source declaration snapshot
```

The source does not need to be numerically highest. Version-number magnitude is allocation identity/order only and does not encode migration direction or preferred source semantics.

## Clone, not re-certify

CREATE_NEXT does not re-run new-binding admission against exact DataType pins already present in an eligible immutable source merely because their current lifecycle state may have changed since source publication.

In particular:

```text
source property exact DataType pin
    -> cloned as historical exact semantic state
    -> current DataTypeVersion need not still be PUBLISHED merely to clone
```

The new result is DRAFT and may later be revised before PUBLISH. PUBLISH owns the later certification boundary for making that exact candidate newly consumable as a published model version.

If an exact dependency referenced by a persisted eligible source is physically missing, that is persisted-state corruption and therefore an internal failure rather than a caller operand error.

## Success contract

```text
201 Created
Location: /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{new_version}
body: none
```

The exact-version Location exposes the newly allocated version identity. No response-only GET reconstruction is required.

## Failure semantics

```text
400 invalid_request
    malformed relationship_definition_id
    source_version missing / null / malformed / non-positive
    query parameter supplied
    unknown/repeated body fields

404 resource_not_found
    path RelationshipDefinition absent

422 referenced_resource_not_found
    path Definition exists
    + selected source exact RelationshipDefinitionVersion absent

409 version_source_conflict
    selected source exists
    + source status is not PUBLISHED or DEPRECATED

500 internal_error
    persisted source/dependency invariant corruption
    persistence / infrastructure failure
```

CREATE_NEXT does not normally expose:

```text
dependency_not_admissible
default_version_unavailable
semantic_validation_failed
```

because it clones an already-certified immutable source snapshot rather than creating or rebinding property dependencies from caller declarations.

## CREATE_NEXT REST closure checkpoint

```text
POST /relationship-definitions/{id}/create-next
    -> body source_version
    -> source PUBLISHED | DEPRECATED
    -> exact property snapshot clone
    -> no DataType re-admission solely for clone
    -> shared no-reuse version allocation
    -> new DRAFT revision 1
    -> 201 + exact-version Location
    -> no response body
```

---

# 11. RD-REVISE-01 — REVISE RelationshipDefinitionVersion

**State:** REST CONTRACT REVIEWED / CURRENT M4 CANDIDATE

## Route and request

```http
POST /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}/revise
```

Query:

```text
expected_revision: positive integer required
```

Body:

```text
RelationshipDefinitionRevise
    properties: required array of RelationshipDefinitionPropertyInput
```

REVISE is a complete replacement command for one exact DRAFT property's declaration candidate. It is not a patch.

Therefore:

```text
properties omitted
    -> invalid_request

properties = null
    -> invalid_request

properties = []
    -> valid complete replacement with an empty property schema
```

The property input carrier is exactly the same authoring carrier established for CREATE:

```text
RelationshipDefinitionPropertyInput
    name: string
    datatype_id: UUID
    datatype_version: positive integer | omitted
    value_mode: SCALAR | LIST
```

`position` remains absent from public input. The order of `properties[]` defines the new preserved internal ordinal order.

## DataType selection semantics

For every submitted property declaration:

```text
datatype_version present
    -> select the explicit exact DataTypeVersion

datatype_version omitted
    -> resolve the current DataType.default_version
    -> materialize that exact pin in the revised DRAFT

datatype_version = null
    -> invalid_request
```

Omission never means "preserve the current exact pin" for an already-existing property. It is always an explicit default-based selection instruction, aligned with the common ObjectTemplate authoring semantics.

Current lifecycle admission applies only when REVISE creates or changes an exact DataType binding. An unchanged exact pin is historical/current candidate state and is not rejected merely because that exact DataTypeVersion is no longer PUBLISHED today.

## Historical property continuity

REVISE preserves complete committed-history semantics across all PUBLISHED/DEPRECATED RelationshipDefinitionVersion generations, independently of numeric publication/version order.

For a property name with committed history:

```text
historical DataType lineage (`datatype_id`)
    -> cannot change

exact datatype_version
    -> may change

value_mode
    -> may change SCALAR -> LIST
    -> may change LIST -> SCALAR
```

Exact RDV validity is intentionally distinct from factual cross-version migrability. A model-plane candidate is not globally invalid merely because some current factual Relationships could fail a later preserve-or-fail `Relationship.SCHEMA_CHANGE`; that concrete migration operation owns per-fact compatibility/admission.

These are candidate semantic-validation rules. A later data-path implementation may detect a single violating same-name DataType-lineage fact set-based rather than loading all historical versions, but must preserve the same complete-history meaning.

## Generation semantics

The target must currently be DRAFT and the caller must present the exact current `expected_revision`.

Every successful REVISE consumes exactly one DRAFT generation:

```text
status remains DRAFT
revision = previous revision + 1
```

This happens even when the canonical complete replacement is identical to the current candidate.

Therefore an identical replacement is not a no-op. This is intentionally aligned with ObjectTemplateVersion REVISE: `revision` represents the exact mutable DRAFT generation consumed by optimistic concurrency, not merely a count of semantic differences.

## Success contract

```text
204 No Content
body: none
```

The caller already selected the exact resource and supplied the complete replacement candidate. REVISE does not reconstruct the exact-version GET DTO solely for mutation response convenience.

## Failure semantics

```text
400 invalid_request
    malformed relationship_definition_id / version
    expected_revision missing / null / malformed / non-positive
    properties omitted / null
    malformed datatype_id / datatype_version / value_mode
    datatype_version = null
    unknown/repeated query or body fields

404 resource_not_found
    RelationshipDefinition absent
    OR exact target RelationshipDefinitionVersion absent

422 referenced_resource_not_found
    newly selected DataType lineage absent
    OR newly selected explicit exact DataTypeVersion absent

422 semantic_validation_failed
    complete candidate violates an intrinsic RDV rule
    duplicate property names
    property naming rule violation
    historical DataType-lineage continuity violation

409 lifecycle_state_conflict
    exact target exists but is not DRAFT

409 stale_revision
    exact target is DRAFT
    + expected_revision != current revision

409 default_version_unavailable
    datatype_version omitted
    + selected DataType exists
    + no current default can be resolved

409 dependency_not_admissible
    new/changed exact DataType binding exists
    + is not currently admissible for new binding

500 internal_error
    persisted dependency/history invariant corruption
    persistence / infrastructure failure
```

REVISE has no normal `relationship_definition_conflict` outcome because property-schema editing does not alter the stable Definition topology/name semantic-cell ownership contract.

## REVISE REST closure checkpoint

```text
POST /relationship-definitions/{id}/versions/{version}/revise
    -> required expected_revision query token
    -> required complete properties[] replacement
    -> same flat DataType authoring carrier as CREATE
    -> omitted datatype_version always resolves current default
    -> array order defines internal ordinal
    -> target must be DRAFT
    -> successful call ALWAYS revision + 1
    -> identical canonical replacement is still a new generation
    -> 204, no body
```

---

# 12. RD-PUBLISH-01 — PUBLISH RelationshipDefinitionVersion

**State:** REST CONTRACT REVIEWED / CURRENT M4 CANDIDATE

## Route and request

```http
POST /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}/publish
```

Query:

```text
expected_revision: positive integer required
```

Body: none.

The target must be the exact current DRAFT generation selected by the path and `expected_revision`.

## Publication semantics

Successful publication performs:

```text
status
    DRAFT -> PUBLISHED

revision
    unchanged
```

PUBLISH consumes the current mutable DRAFT generation by making the exact snapshot immutable. It does not create a new generation and therefore does not increment `revision`.

PUBLISH re-certifies the complete candidate against all committed `PUBLISHED` / `DEPRECATED` property history because publication order is not constrained by numeric version order.

Every exact DataTypeVersion directly pinned by the DRAFT must still be currently `PUBLISHED` at the publication admission boundary.

## Default interaction

The current default rule is:

```text
Definition.default_version == null
    -> successful PUBLISH sets default_version = version

Definition.default_version != null
    -> successful PUBLISH leaves it unchanged
```

A later publication never silently replaces an existing default.

## Success contract

```text
204 No Content
body: none
```

No Location is required because PUBLISH mutates an already-addressable exact resource. No exact-version GET reconstruction is required solely for the mutation response.

## Failure semantics

```text
400 invalid_request
    malformed relationship_definition_id / version
    expected_revision missing / null / malformed / non-positive
    body present
    unknown/repeated query parameter

404 resource_not_found
    RelationshipDefinition absent
    OR exact target RelationshipDefinitionVersion absent

409 lifecycle_state_conflict
    exact target exists but is not DRAFT

409 stale_revision
    exact target is DRAFT
    + expected_revision != current revision

409 dependency_not_admissible
    an exact DataTypeVersion pinned by the DRAFT exists
    + is not currently PUBLISHED at publication time

422 semantic_validation_failed
    the otherwise well-formed DRAFT conflicts with committed
    PUBLISHED/DEPRECATED property-history continuity

500 internal_error
    persisted DRAFT is intrinsically malformed
    persisted exact DataType dependency is physically missing
    persisted invariant corruption / persistence / infrastructure failure
```

PUBLISH has no normal `referenced_resource_not_found`, `default_version_unavailable`, `default_version_conflict` or `relationship_definition_conflict` outcome.

## PUBLISH REST closure checkpoint

```text
POST /relationship-definitions/{id}/versions/{version}/publish
    -> required expected_revision
    -> body none
    -> DRAFT -> PUBLISHED
    -> revision unchanged
    -> re-certify committed property history
    -> every exact DataType pin currently PUBLISHED
    -> establish default only when still null
    -> 204, no body
```

---

# 13. RD-DEFAULT-01 — SET_DEFAULT / CLEAR_DEFAULT

**State:** REST CONTRACT REVIEWED / CURRENT M4 CANDIDATE

The two default-management capabilities remain distinct rather than overloading an explicit nullable setter.

## SET_DEFAULT route and request

```http
POST /api/v1/core/relationship-definitions/{relationship_definition_id}/set-default
```

Query: none.

Body:

```text
RelationshipDefinitionSetDefault
    version: positive integer required
```

The selected exact version is a command operand, not a path target. It must exist in the same RelationshipDefinition and be currently `PUBLISHED`.

Success:

```text
204 No Content
body: none
```

SET_DEFAULT is idempotent on current value:

```text
version == current default_version
    -> 204
```

Failure semantics:

```text
400 invalid_request
    malformed relationship_definition_id
    version missing / null / malformed / non-positive
    query supplied
    unknown/repeated body field

404 resource_not_found
    path RelationshipDefinition absent

422 referenced_resource_not_found
    path Definition exists
    + selected exact RelationshipDefinitionVersion absent

409 dependency_not_admissible
    selected exact version exists
    + status != PUBLISHED

500 internal_error
    persisted invariant corruption / persistence / infrastructure failure
```

## CLEAR_DEFAULT route and request

```http
POST /api/v1/core/relationship-definitions/{relationship_definition_id}/clear-default
```

Query: none.
Body: none.

Successful CLEAR_DEFAULT establishes:

```text
default_version = null
```

Success:

```text
204 No Content
body: none
```

CLEAR_DEFAULT is idempotent when the default is already null.

Failure semantics:

```text
400 invalid_request
    malformed relationship_definition_id
    body or query supplied

404 resource_not_found
    RelationshipDefinition absent

500 internal_error
    persisted invariant corruption / persistence / infrastructure failure
```

CLEAR_DEFAULT has no exact-version operand and therefore no normal `409` or `422` outcome.

## Default-management closure checkpoint

```text
SET_DEFAULT
    -> distinct command
    -> body {version}
    -> exact PUBLISHED same-Definition target
    -> idempotent on current value
    -> 204, no body

CLEAR_DEFAULT
    -> distinct command
    -> no body
    -> stores null
    -> idempotent when already null
    -> 204, no body
```

---

# 14. RD-DEPRECATE-01 — DEPRECATE RelationshipDefinitionVersion

**State:** REST CONTRACT REVIEWED / CURRENT M4 CANDIDATE

## Route and request

```http
POST /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}/deprecate
```

Query: none.
Body: none.

Only an exact `PUBLISHED` RelationshipDefinitionVersion may be deprecated.

Successful transition:

```text
status
    PUBLISHED -> DEPRECATED

revision
    unchanged
```

The transition is irreversible and is not idempotent: calling DEPRECATE on an already DEPRECATED or DRAFT target is a lifecycle conflict.

## Default and factual-reference semantics

The current `default_version` cannot be deprecated.

Current factual Relationships pinned to the exact target version are **not** deprecation blockers. A DEPRECATED version remains a valid historical exact dependency for already-existing factual Relationships; deprecation only removes it from future lifecycle-sensitive admission.

The immutable semantic/property payload does not change during deprecation.

## Success contract

```text
204 No Content
body: none
```

## Failure semantics

```text
400 invalid_request
    malformed relationship_definition_id / version
    body or query supplied

404 resource_not_found
    RelationshipDefinition absent
    OR exact RelationshipDefinitionVersion absent

409 lifecycle_state_conflict
    exact target exists
    + status != PUBLISHED

409 default_version_conflict
    exact target is PUBLISHED
    + version == current default_version

500 internal_error
    persisted invariant corruption / persistence / infrastructure failure
```

DEPRECATE has no normal `active_dependency_conflict`, `dependency_not_admissible`, `referenced_resource_not_found` or `stale_revision` outcome.

## DEPRECATE REST closure checkpoint

```text
POST /relationship-definitions/{id}/versions/{version}/deprecate
    -> body/query none
    -> PUBLISHED only
    -> current default blocked
    -> factual historical pins do not block
    -> PUBLISHED -> DEPRECATED
    -> revision unchanged
    -> 204, no body
```

---

# 15. RD-DELETE-DRAFT-01 — DELETE exact DRAFT RelationshipDefinitionVersion

**State:** REST CONTRACT REVIEWED / CURRENT M4 CANDIDATE

## Route and request

```http
DELETE /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}
```

Query:

```text
expected_revision: positive integer required
```

Body: none.

The selected exact version must currently be:

```text
status = DRAFT
revision = expected_revision
```

The complete property declaration payload is not part of admission. Property rows are exact-version-owned child state and disappear with the exact DRAFT.

## Version allocation consequence

A successfully deleted exact DRAFT version number is never reusable. The shared lineage allocator remains monotonic/no-reuse independently of exact-version deletion.

## Success contract

```text
204 No Content
body: none
```

After success the exact resource no longer exists. A repeated DELETE against the same exact version therefore returns `404 resource_not_found` rather than a silent idempotent success.

## Failure semantics

```text
400 invalid_request
    malformed relationship_definition_id / version
    expected_revision missing / null / malformed / non-positive
    body present
    unknown/repeated query parameter

404 resource_not_found
    RelationshipDefinition absent
    OR exact RelationshipDefinitionVersion absent

409 lifecycle_state_conflict
    exact target exists
    + status != DRAFT

409 stale_revision
    exact target is DRAFT
    + expected_revision != current revision

500 internal_error
    persisted invariant corruption / persistence / infrastructure failure
```

DELETE_DRAFT has no normal `referenced_resource_not_found`, `default_version_conflict` or dependency-admission outcome.

## DELETE_DRAFT REST closure checkpoint

```text
DELETE /relationship-definitions/{id}/versions/{version}
    -> required expected_revision
    -> exact DRAFT generation only
    -> owned declaration cleanup
    -> deleted version number never reused
    -> first valid delete 204
    -> repeated delete 404
```

---

# 16. RD-DELETE-ROOT-01 — DELETE RelationshipDefinition

**State:** REST CONTRACT REVIEWED / CURRENT M4 CANDIDATE

## Route and request

```http
DELETE /api/v1/core/relationship-definitions/{relationship_definition_id}
```

Query: none.
Body: none.

## Aggregate ownership semantics

Successful root deletion removes the complete owned model aggregate:

```text
RelationshipDefinition
    -> all owned RelationshipDefinitionVersion rows
        -> all owned RelationshipDefinitionProperty rows
    -> all other Definition-owned / derived state
```

The future physical schema may realize owned cleanup through cascades or equivalent atomic ownership semantics. The REST contract does not require application-side child deletion loops.

The Definition topology / semantic-cell contract does not need to be re-certified before deletion: removing the Definition cannot create a new semantic-cell ownership collision.

## External blocker

A current factual Relationship that references any exact version of the Definition is an external lifetime blocker.

```text
at least one current factual Relationship references the Definition
    -> 409 delete_blocked

no current factual Relationship references the Definition
    -> root delete may proceed
```

The M4 public diagnostic deliberately removes the AS-IS total blocker count. `delete_blocked` needs only bounded information sufficient to identify the blocker family:

```json
{
  "code": "delete_blocked",
  "message": "The RelationshipDefinition is still referenced.",
  "details": {
    "blocker_type": "relationship"
  }
}
```

The contract does **not** require:

```text
COUNT of all blocking factual Relationships
list of blocking Relationship ids
full blocker enumeration
```

This allows the legal efficient path to stop after proving a real blocker rather than performing diagnostic-only total counting.

## Success contract

```text
204 No Content
body: none
```

After success the stable Definition resource no longer exists. A repeated root DELETE therefore returns `404 resource_not_found`.

## Failure semantics

```text
400 invalid_request
    malformed relationship_definition_id
    body or query supplied

404 resource_not_found
    RelationshipDefinition absent

409 delete_blocked
    at least one current factual Relationship references an exact version
    details.blocker_type = "relationship"

500 internal_error
    persisted invariant corruption / persistence / infrastructure failure
```

## Root DELETE REST closure checkpoint

```text
DELETE /relationship-definitions/{id}
    -> no body/query
    -> delete complete owned aggregate
    -> factual current Relationship is the external blocker
    -> delete_blocked exposes blocker type only, no count/list
    -> no topology re-certification
    -> first valid delete 204
    -> repeated delete 404
```

---

# 17. RelationshipDefinition REST-family closure checkpoint

The complete current M4 RelationshipDefinition REST family is now reviewed caller-first:

```text
4 GET capabilities
9 retained mutations
1 removed mutation: RENAME
```

Key cross-operation rules now closed at REST-contract level include:

```text
NO autonomous RelationshipResolution public identity
NO resolution_id
stable semantic names; no RENAME
explicit symmetric intent
compact authored topology + factored applicability reads
shared monotonic/no-reuse exact-version allocation
DRAFT revision generation semantics
REVISE always consumes one revision, even for identical replacement
PUBLISH / DEPRECATE do not increment revision
CREATE_NEXT clones eligible immutable source without re-admitting historical pins
PUBLISH is the certification boundary for current exact DataType admissibility
first publication establishes default only when still null
SET_DEFAULT / CLEAR_DEFAULT remain distinct and are idempotent on current value
DEPRECATE cannot target the current default
DEPRECATED exact versions remain valid historical factual dependencies
DELETE_DRAFT never recycles an allocated version number
root DELETE is blocked by current factual Relationships
root delete_blocked diagnostic exposes blocker type, not total count
mutation success responses avoid response-only GET reconstruction
```

This REST closure remains M4 WIP and non-normative. It does not mean the RelationshipDefinition family has reached the consolidated discovery baseline of Object/factual Relationship, and it does not freeze physical SQL, cache realization, lock/FK/UNIQUE arbitration, retry behavior, DDL or migration/backfill.

Any downstream finding that materially invalidates one of these caller-visible semantics must explicitly reopen the affected micro-contract under the normal M4 retroactive-revalidation rule.

---

# 18. Current next review frontier

No RelationshipDefinition REST capability remains unreviewed in the current retained family surface.

The next family frontier is **consolidated technical discovery / revalidation**, with the explicit goal of bringing `RelationshipDefinition` to the same M4 `REVIEWED BASELINE` discovery level already reached by Object and factual Relationship. This is not architecture closure.

```text
RelationshipDefinition technical discovery consolidation
    -> rebase every distributed relationshipdefinition-*-discovery finding
       on the reviewed REST contracts and post-Resolution semantic model

    -> consolidate route-local logical data paths
       reads / writes / admission predicates / response-only work
       and remove stale autonomous-Resolution assumptions

    -> consolidate the discovery-level logical persistence model
       compact RelationshipDefinition source of truth
       RelationshipDefinitionVersion/property ownership
       shared no-reuse version allocation
       relationship_definition_space derived semantic closure

    -> revalidate the relationship_definition_space materialization boundary
       against actual GET / CREATE / factual-Relationship consumers
       without freezing final DDL

    -> consolidate cache boundaries
       immutable exact-RDV runtime semantics
       stable/current Definition semantics where justified
       PostgreSQL authority for mutable lifecycle/default state

    -> re-run operation-level cost / over-fetch / materialization challenges
       using the now-final REST response and error contracts
       including GP-05 bounded diagnostics

    -> carry final PK/FK/UNIQUE/index choices,
       lock/wait/retry/deadlock realization and other concurrency arbitration
       forward as explicit architecture handoffs rather than solving them here

    -> run a consistency sweep against reviewed Object and factual Relationship
       and promote RelationshipDefinition to REVIEWED BASELINE only when
       no material semantic/data-path/cache contradiction remains
```

Only after this family reaches that reviewed discovery baseline should M4 proceed to the broader architecture-closing work shared with Object and factual Relationship.

Implementation remains forbidden until the normal M4 Contract -> Architecture -> Steps freeze sequence authorizes it.
