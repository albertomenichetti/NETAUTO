# M4 WIP — RelationshipDefinition model-plane review owner

**Status:** REVIEWED BASELINE / SINGLE FAMILY OWNER / REST + TECHNICAL DISCOVERY CONSOLIDATED / ARCHITECTURE CLOSING PENDING / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose and ownership

This document is the single current M4 WIP owner for the `RelationshipDefinition` model-plane family.

It owns the current reviewed discovery decisions for:

```text
public REST capabilities and wire contracts
stable RelationshipDefinition semantic contract
RelationshipDefinitionVersion public contract
version/property authoring semantics
logical persistence and ownership boundaries
relationship_definition_space semantics and consumers
route-local logical data paths and cost direction
immutable/current cache authority
dependency lifetime and lifecycle interactions
explicit concurrency / physical architecture handoffs
```

Everything under `wip/` remains globally non-normative and does not authorize implementation.

The caller-first REST sweep, operation-level technical discovery and bidirectional consistency sweep are complete for the current reviewed baseline. This status is not architecture closure: final SQL, DDL, exact PK/FK/UNIQUE/index realization, lock/wait/retry/deadlock protocols, cache implementation, migration/backfill and verification design remain later work.

## Authority and retained dependencies

This file is the only active RelationshipDefinition family owner in the M4 working corpus.

The former semantic-intent draft, distributed operation-specific notes and temporary consolidation ledger have been losslessly absorbed here and removed. Git history remains the historical source for superseded intermediate reasoning; those deleted files are not required to interpret the current candidate.

Cross-domain concerns remain owned rather than duplicated by:

```text
general-domain-principles.md
    -> version meaning vs migrability
    -> operation-owned lifecycle scope
    -> bounded diagnostics / no diagnostic-only work

version-allocation.md
    -> shared monotonic/no-reuse exact-version allocation
    -> logical last_versions(id, last_version)

object-template-ancestry-cache.md
    -> stable ObjectTemplate ancestor/compatibility cache semantics

relationship.md
    -> factual Relationship contracts, runtime cells and exact-RDV consumers
```

The delivered AS-IS under `docs/architecture/` remains authoritative until M4 deliberately freezes and promotes a TO-BE architecture set.

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

This REST closure remains M4 WIP and non-normative. Together with the consolidated operation-level technical discovery, bidirectional consistency sweep and reviewed-baseline closure in the following sections, it establishes RelationshipDefinition as `REVIEWED BASELINE` at discovery level. It does not freeze physical SQL, cache realization, lock/FK/UNIQUE arbitration, retry behavior, DDL, migration/backfill or verification.

Any downstream finding that materially invalidates one of these caller-visible semantics must explicitly reopen the affected micro-contract under the normal M4 retroactive-revalidation rule.


---

# 18. Consolidated operation-level technical discovery

The operation-specific technical findings have been absorbed below as one family-owned baseline. They fix logical data paths, authority, cost and handoff boundaries without freezing final SQL or concurrency mechanisms.

## 1. `relationship_definition_space` classification — RATIFIED

`relationship_definition_space` is the complete current certified derived semantic closure for one RelationshipDefinition.

Logical source:

```text
compact RelationshipDefinition stable topology/names
+
current stable ObjectTemplate ancestry
```

Conceptual invariant:

```text
MaterializedSpace(D)
 ==
Expand(
    D.symmetric,
    D.endpoint_a_template_id,
    D.endpoint_b_template_id,
    D.name_a_to_b,
    D.name_b_to_a,
    current stable ObjectTemplate descendant sets
)
```

It is independent from:

```text
RelationshipDefinition.default_version
RDV lifecycle/status
RDV revision
RDV properties
```

The space exists from RelationshipDefinition CREATE even though v1 is DRAFT and `default_version = null`, because semantic-cell ownership belongs to the stable Definition rather than to a published exact version.

RelationshipDefinition-owned effects:

```text
CREATE Definition
    -> create complete space

CREATE_NEXT
REVISE
PUBLISH
SET_DEFAULT
CLEAR_DEFAULT
DEPRECATE
DELETE_DRAFT
    -> no space change

DELETE Definition
    -> remove owned space
```

Stable ObjectTemplate ancestry changes may require maintenance of the derived space, but that is an external maintenance dependency rather than a reason to move ObjectTemplate into the active RelationshipDefinition review.

Classification:

```text
derived/materialized trusted current model knowledge
NOT a second semantic authority
may be relational arbitration authority for exact semantic-cell ownership
```

Physical PK/UNIQUE/constraint realization remains architecture work.

### 1.1 Coherence invariant — RATIFIED

There must be no committed state in which stable ObjectTemplate ancestry has changed while `relationship_definition_space` remains stale.

```text
relationship_definition_space
    must always be coherent with
compact RelationshipDefinition state
+
current stable ObjectTemplate ancestry
```

A descendant lineage that appears only through derived expansion must not become an independent root-lineage lifetime blocker merely because it is present in the materialized space.

### 1.2 RelationshipDefinition consumers — RATIFIED

Within the RelationshipDefinition family, the space is **not** a general read model.

```text
CREATE Definition
    -> YES
       candidate-cell derivation
       semantic conflict arbitration
       complete space persistence

GET Definition detail
    -> NO full space scan
    -> use endpoint roots + stable ancestry descendant sets

LIST Definitions
GET/LIST versions
CREATE_NEXT
REVISE
PUBLISH
SET_DEFAULT
CLEAR_DEFAULT
DEPRECATE
DELETE_DRAFT
    -> NO space

DELETE Definition
    -> owned derived cleanup only
```

Primary roles:

```text
WRITE / ARBITRATION on CREATE
OWNED CLEANUP on DELETE
EXTERNAL coherence maintenance when stable ancestry changes
```

---

## 2. CREATE RelationshipDefinition — technical discovery CLOSED except concurrency/physical realization

### 2.1 Semantic preparation boundary — RATIFIED

CREATE uses the same broad separation already established for Object commands:

```text
STEP 1 — current dependency resolution
STEP 2 — semantic preparation outside mutation UoW
STEP 3 — short mutation UoW / final current admission / persistence
```

#### STEP 1 — exact dependency selection

For every property:

```text
explicit datatype_version
    -> select exact DTV

omitted datatype_version
    -> resolve current DataType.default_version
    -> materialize one exact DTV pin
```

Once an omitted default has resolved to an exact DTV, a later default change must **not** retarget the in-flight command.

Endpoint ObjectTemplate roots are also resolved as current existing lineages.

#### STEP 2 — complete DTV semantic preparation

For **all** selected exact DataTypeVersions:

```text
load semantic payload
compile required DataType semantics/validators
make validation semantics READY
```

Then build and validate the complete v1 DRAFT property candidate and compact RelationshipDefinition candidate.

This work stays outside the mutation UoW.

CREATE v1 has no prior committed RelationshipDefinition property history, therefore:

```text
NO published/deprecated history lookup for v1
```

#### STEP 3 — short mutation UoW

Final mutable/current admission includes at least:

```text
endpoint roots still current/existing
all newly selected exact DTV pins still admissible/PUBLISHED
```

The exact DTV semantic payload is **not** reloaded or recompiled inside the mutation UoW.

### 2.2 Endpoint-topology validation boundary — RATIFIED

CREATE does not load the full ObjectTemplate graph or descendant sets into the worker.

For symmetric topology validation the worker only needs the stable relation between endpoint roots A/B:

```text
A == B
A ancestor-of B
B ancestor-of A
neither ancestry direction
```

The existing stable ObjectTemplate ancestry cache may answer that bounded predicate. With single inheritance:

```text
symmetric + A == B
    -> identical spaces: valid

symmetric + one root is a strict ancestor of the other
    -> distinct-but-overlapping: invalid

symmetric + neither is ancestor of the other
    -> disjoint: valid
```

The stable A/B ancestry relation need not be re-proved in the final mutation UoW if both endpoints still exist; endpoint existence remains current PostgreSQL admission.

### 2.3 Candidate semantic closure generation — RATIFIED

Potentially large candidate semantic cells must remain DB-internal:

```text
DB -> worker -> DB candidate closure
    -> NO

PostgreSQL set-based derivation from
    compact candidate
    + object_template_ancestry
    -> YES
```

The worker owns the compact candidate and bounded failure information, not the Cartesian exact-template cell set.

### 2.4 Conflict path — RATIFIED

For an intrinsically valid candidate:

```text
CandidateSpace(D)
INTERSECT
current relationship_definition_space
```

is the conflict test.

If non-empty, the ordinary arbitration path needs at most one witness:

```text
existing relationship_definition_id
from_template_id
name
to_template_id
```

matching the reviewed REST error:

```text
409 relationship_definition_conflict
```

No conflict count, full conflicting Definition load, all-cell enumeration or equivalence-specific second path is required.

Candidate-internal duplication/malformed closure remains intrinsic semantic validation, not a current ownership conflict.

The mechanism that makes this correct under concurrent CREATE operations remains a concurrency/physical handoff.

### 2.5 Logical write set and cost invariant — RATIFIED

CREATE logically writes:

```text
relationship_definitions
last_versions
relationship_definition_versions
relationship_definition_properties
relationship_definition_space
```

The first exact version initializes the shared no-reuse allocator consistently with version 1.

Target DML cost invariant for P properties and N semantic cells:

```text
application persistence round trips
    -> bounded / constant in P and N

physical row writes
    -> O(P + N)
```

Required direction:

```text
bulk property persistence
set-based DB-internal space derivation/persistence
```

Forbidden hot shape:

```text
one statement per property
one statement per semantic cell
```

No requirement exists to compress the whole model-plane CREATE into one mega-statement; the requirement is bounded statement count and no N+1.

### 2.6 CREATE cache boundary — RATIFIED

CREATE may reuse/fill immutable exact-DTV semantic/compiled cache entries.

It does **not** publish a RelationshipDefinitionVersion immutable cache entry because the newly created v1 is DRAFT.

It does not create a worker cache for `relationship_definition_space`.

No dedicated stable RelationshipDefinition topology cache is justified by CREATE itself without a concrete consumer.

---

## 3. RelationshipDefinition GET family — technical checkpoints

### 3.1 LIST Definitions — RATIFIED

The compact Definition model removes the AS-IS Resolution row multiplication.

Target path:

```text
relationship_definitions D
JOIN endpoint ObjectTemplate root A
JOIN endpoint ObjectTemplate root B
keyset on D.id
LIMIT limit + 1
```

One DB row corresponds to one Definition. The worker performs only bounded perspective projection:

```text
asymmetric
    -> 2 perspectives

symmetric + A != B
    -> 2 reciprocal perspectives with same name

symmetric + A == B
    -> 1 perspective
```

No `relationship_definition_space`, ancestry, version, DataType or worker-cache read is needed.

Qualified endpoint names are resolved by the same bounded query; no endpoint N+1.

### 3.2 GET Definition detail — RATIFIED

The detail requires factored applicability, therefore the correct cost is:

```text
O(|Desc(A)| + |Desc(B)|)
```

not:

```text
O(|Desc(A)| * |Desc(B)|)
```

One authoritative PostgreSQL read obtains:

```text
compact Definition
endpoint-root references
complete current descendants of each distinct endpoint root
```

using `object_template_ancestry` by `ancestor_template_id` plus descendant ObjectTemplate references.

If A == B the descendant set is obtained once and reused.

The GET must not read `relationship_definition_space` and refactor an N×M cell set back into two arrays.

The existing worker ancestry cache is not authoritative for complete **descendant enumeration** because new descendants can appear over time; PostgreSQL remains the current source for this read.

### 3.3 LIST exact versions — RATIFIED

Keep one root-preserving authoritative PostgreSQL statement that distinguishes:

```text
Definition absent -> 404
Definition present + no matching versions -> empty page
```

Projection is only:

```text
version
revision
status
```

with optional status predicate, keyset by version and `limit + 1`.

No properties, DataType, topology, space, ancestry or cache involvement.

### 3.4 GET exact RDV — RATIFIED

Public exact-version GET stays PostgreSQL-authoritative rather than bifurcating into cache-hit/cache-miss DTO paths.

One statement projects:

```text
Definition existence sentinel
exact RDV header
ordered properties
DataType lineage namespace/name for qualified_name
```

Property payload:

```text
name
internal ordinal
value_mode
datatype_id
datatype_version
DataType namespace/name
```

The public DTO omits ordinal but preserves its order.

No DataTypeVersion semantic payload or validator compilation is required for this read.

The immutable RDV cache is runtime-oriented and is not a required public GET source.

---

## 4. CREATE_NEXT RelationshipDefinitionVersion — technical discovery CLOSED except concurrency/physical realization

### 4.1 Immutable source and preferred cache path — RATIFIED

Eligible source state:

```text
PUBLISHED | DEPRECATED
```

therefore the complete source declaration snapshot is immutable.

Preferred direction is to exploit the immutable RDV cache and build the next DRAFT in application/domain state outside the mutation UoW rather than using DB-side `INSERT ... SELECT` as the primary clone mechanism.

Conceptual cache facets:

```text
ImmutableRelationshipDefinitionVersionCache[(definition_id, version)]

snapshot READY
    ordered properties
        name
        ordinal
        datatype_id
        datatype_version
        value_mode

compiled READY
    RuntimePropertySpec / validators / DTV semantic linkage
```

CREATE_NEXT requires only `snapshot READY`.

On cache miss:

```text
bounded cold load of exact immutable snapshot
-> publish snapshot facet
```

No DTV semantic load/compile is required merely to clone.

### 4.2 Prepared next candidate — RATIFIED

Outside the mutation UoW the application may build:

```text
PreparedRelationshipDefinitionVersion
    status = DRAFT
    revision = 1
    properties = exact ordered source snapshot clone
    version = not allocated yet
```

The new version number remains unassigned until the shared `last_versions` allocator is advanced in the mutation UoW.

### 4.3 Final UoW — RATIFIED at logical level

Short mutation UoW must establish at least:

```text
Definition still exists
source exact version still exists
source.status still in {PUBLISHED, DEPRECATED}
allocate next version through last_versions
bulk insert new RDV + cloned properties
```

No source-property reread, DTV reread, DTV compilation or historical continuity validation is required inside the UoW.

A concurrent:

```text
PUBLISHED -> DEPRECATED
```

of the source is semantically harmless because both source states are eligible.

Source/root disappearance remains a concurrency realization concern.

The new DRAFT is not published into immutable RDV cache.

---

## 5. REVISE RelationshipDefinitionVersion — technical discovery CLOSED except concurrency/physical realization

### 5.1 Preparation boundary — RATIFIED

REVISE starts from the current exact DRAFT snapshot so the application knows:

```text
status
revision
complete ordered current properties
```

This supports early target-state/revision checks, classification of unchanged vs new/changed exact bindings, and declaration-delta computation.

Outside the mutation UoW:

```text
complete request properties[]
    -> resolve every exact DTV pin
       explicit version or current DataType.default_version
    -> once resolved, default changes do not retarget the candidate
    -> load + compile ALL selected exact DTV semantics
    -> build/validate complete replacement candidate
```

Lifecycle admission differs by binding class:

```text
unchanged exact DTV pin
    -> semantic load/compile YES
    -> current PUBLISHED requirement NO

new property / changed exact DTV pin
    -> semantic load/compile YES
    -> current PUBLISHED admission YES
```

Omitted `datatype_version` is always a fresh default-selection instruction, not shorthand for preserving the current exact pin.

### 5.2 Historical continuity — LATER REVALIDATION RATIFIED

The former RelationshipDefinition wording that forbade committed-history `LIST -> SCALAR` is superseded by the current M4 revalidation; the current owner carries the corrected rule.

Current rule:

```text
same historical property name
    -> DataType lineage (`datatype_id`) remains stable

exact datatype_version
    -> may change

value_mode
    -> may change SCALAR -> LIST
    -> may change LIST -> SCALAR
```

Why `LIST -> SCALAR` is no longer a model-plane publication/revision prohibition:

```text
validity of an exact RDV
    !=
ability of every current factual Relationship to migrate to it
```

A factual `Relationship.SCHEMA_CHANGE` pays concrete preserve-or-fail migration admission for the selected source/target and can reject a multi-item LIST when targeting SCALAR. The model-plane exact target need not be globally banned merely because some facts cannot migrate to it.

DataType lineage continuity remains because same-name factual property continuity currently treats cross-DataType-lineage change as a different/unsupported semantic property transition.

### 5.3 Historical conflict probe — RATIFIED

Do not materialize full committed history in the worker.

The only remaining committed-history violation is:

```text
historical.name == candidate.name
AND historical.datatype_id != candidate.datatype_id
```

Detection should be set-based, candidate-name scoped, and may stop at one violating fact.

No history-summary materialization is justified for this rare model-plane operation.

An early fail-fast probe may run before expensive semantic preparation, but commit legality must still reflect all PUBLISHED/DEPRECATED history at the final admission boundary. A concurrent PUBLISH of another RDV may add committed history while the candidate is being prepared.

The exact concurrency mechanism remains architecture work.

### 5.4 Persistence delta — RATIFIED

The application already owns both:

```text
current DRAFT snapshot
prepared complete candidate
```

so persistence must not reread properties merely to compute the delta.

Classify by property name:

```text
unchanged
removed
added
changed
```

where `changed` includes changes to exact pin, value mode or ordinal.

Short-UoW DML direction:

```text
<= 1 bulk DELETE for removed + changed
<= 1 bulk INSERT for added + changed
1 RDV revision UPDATE
```

Delete-before-insert naturally supports ordinal swaps and uniqueness-sensitive replacement.

Identical complete replacement:

```text
property delta empty
DELETE 0
INSERT 0
revision still +1
```

because every successful REVISE consumes exactly one DRAFT generation.

No full delete/reinsert is preferred when most rows are unchanged; differential DML preserves bounded statement count while reducing row/index/FK churn.

No post-mutation reload is required for the 204 response.

### 5.5 Final admission ordering — RATIFIED at logical level

Logical short-UoW ordering:

```text
1. target-generation gate
       exact RDV still exists
       status == DRAFT
       revision == expected_revision

2. final dependency admission
       every new/changed exact DTV binding still admissible/PUBLISHED

3. final historical admission
       candidate remains compatible with all committed
       PUBLISHED/DEPRECATED same-name history
       under the current datatype-lineage-only continuity rule

4. persist declaration delta

5. consume exactly one revision generation
       result revision = expected_revision + 1
```

Whether revision CAS is physically performed at the initial gate or after equivalent protection is architecture work; the invariant is that a successful REVISE starts from exactly `expected_revision` and commits exactly the prepared complete candidate as `expected_revision + 1`.

The concurrency realization must also ensure that a newly committed incompatible publication cannot invalidate the historical admission between check and commit.

---

## 6. PUBLISH RelationshipDefinitionVersion — technical discovery CLOSED except concurrency/physical realization

### 6.1 Semantic preparation outside mutation UoW — RATIFIED

PUBLISH starts from one authoritative exact current DRAFT generation:

```text
Definition exists
exact target exists
status = DRAFT
revision = R
complete ordered properties
```

For **all** exact DTV pins in that DRAFT, outside the mutation UoW:

```text
load immutable exact DataTypeVersion semantic payload
compile validators/runtime semantic structures
prepare complete immutable RDV runtime representation
```

Conceptual prepared value:

```text
PreparedPublishedRDV
    relationship_definition_id
    version
    source_revision = R
    ordered property snapshot
    compiled RuntimePropertySpec / validators / exact-DTV linkage
```

An early set-based historical continuity probe may fail fast. Under the current revalidated history rule it needs only detect same-name historical declarations with a different `datatype_id`.

No complete RelationshipDefinition topology, `relationship_definition_space`, ObjectTemplate ancestry or full committed-history materialization is required.

Compilation can occur before final stabilization because exact DTV semantics are immutable. A concurrent REVISE is rejected by the final generation gate if target revision no longer equals prepared revision R.

### 6.2 Short final publication UoW — RATIFIED at logical level

Logical final admission:

```text
1. exact target still exists
2. status still DRAFT
3. revision == expected_revision == prepared source revision R
4. every pinned exact DTV is still PUBLISHED
5. committed-history datatype-lineage continuity is still valid
6. DRAFT -> PUBLISHED
7. revision unchanged
8. if Definition.default_version is still NULL
       -> set this version as default
   else
       -> leave current default unchanged
9. commit
```

No DTV semantic reload/recompile belongs inside the mutation UoW.

No `relationship_definition_space` maintenance occurs because RDV publication does not change stable Definition topology/name semantic ownership.

Exact locking/rendezvous mechanics remain architecture/concurrency work.

### 6.3 Immutable RDV cache publication — RATIFIED

The prepared immutable RDV becomes consumable in worker-local cache **only after successful PUBLISH commit**.

Conceptual facets:

```text
ImmutableRelationshipDefinitionVersionCache[(definition_id, version)]

snapshot READY
    ordered properties
        name
        ordinal
        datatype_id
        datatype_version
        value_mode

compiled READY
    RuntimePropertySpec / validators / exact-DTV semantic linkage
```

PUBLISH normally makes both facets READY from already prepared in-memory state. No post-commit DB reload or recompilation is required.

The cache excludes mutable/current state:

```text
RDV.status
RelationshipDefinition.default_version
```

Cache presence never proves current existence or current lifecycle admission.

### 6.4 Cache lifecycle across DEPRECATE/DELETE — RATIFIED

The immutable RDV cache follows semantic immutability rather than lifecycle state:

```text
DRAFT
    -> not immutable-cacheable

PUBLISHED
    -> immutable-cacheable

PUBLISHED -> DEPRECATED
    -> entry remains semantically valid
    -> no invalidation
```

DEPRECATE changes only current admission state and does not change the exact property snapshot or compiled semantics.

The same immutable entry can therefore serve existing factual Relationships pinned to a DEPRECATED version and CREATE_NEXT sources in either PUBLISHED or DEPRECATED state.

Complete Definition deletion does not require correctness-driven distributed cache invalidation because cache presence is never existence authority and UUID/exact-version identities are not reused. Local eviction may be opportunistic.

Facet consumers remain distinct:

```text
snapshot READY
    -> sufficient for CREATE_NEXT

compiled READY
    -> required by factual runtime consumers
```

### 6.5 No new relational RDV materialization — RATIFIED

`relationship_definition_properties` already stores the complete exact schema snapshot. PUBLISH does not justify another persisted copy merely to accelerate runtime compilation. Optimization is worker-local immutable cache reuse.

### 6.6 Default interaction and DML/cost closure — RATIFIED

`default_version` is not a semantic-preparation input and does not require a pre-read.

PUBLISH owns one conditional current-state transition at its final publication boundary:

```text
if Definition.default_version is still NULL
    -> set default_version = this published version

otherwise
    -> leave the current non-null default unchanged
```

Logical mutation direction:

```text
1. final generation/dependency/history admission
2. UPDATE exact RDV DRAFT -> PUBLISHED, revision unchanged
3. conditional UPDATE Definition
       SET default_version = :version
       WHERE id = :definition_id
         AND default_version IS NULL
4. COMMIT
```

The conditional default update may affect one or zero rows. Zero rows does not invalidate publication; it means a default already exists. The `204 No Content` response does not require learning or re-projecting which case occurred.

Concurrent publications against an initially NULL default must preserve a NULL-only claim invariant: at most one publication establishes the first default, while another publication may still succeed without replacing it. Exact serialization remains architecture work.

PUBLISH should own this narrow first-default transition directly rather than routing through the public `SET_DEFAULT` helper if that helper introduces command-specific reads/admission/reloads not required by publication.

Cost shape:

```text
READ / PREPARATION
    O(P) exact property snapshot
    bounded/bulk exact-DTV semantic preparation
    set-based history probe

MUTATION DML
    1 RDV status UPDATE
    <= 1 conditional Definition default UPDATE

property writes
    0
relationship_definition_space writes
    0
post-mutation reads
    0
```

Mutation statement count is constant in property count.

---

## 7. SET_DEFAULT — technical discovery CLOSED except concurrency/physical realization

`SET_DEFAULT` changes only current mutable selection state on the RelationshipDefinition lineage.

Admission:

```text
RelationshipDefinition exists
selected exact RDV exists in the same Definition
selected exact RDV status == PUBLISHED
```

No semantic-preparation phase is required. The operation does not consume RDV properties, DTV semantics, compiled caches, topology, ancestry, history or revision.

Logical short-UoW path:

```text
current admission
    Definition exists
    exact target exists/status == PUBLISHED

mutation
    default_version = selected version

commit
```

The command is idempotent when the selected version is already the current default. The `204 No Content` response requires no aggregate reconstruction or post-write reload.

No cache fill/invalidation or `relationship_definition_space` maintenance occurs.

Concurrency handoff:

```text
SET_DEFAULT(D@V) vs DEPRECATE(D@V)

SET_DEFAULT wins
    -> V becomes current default
    -> DEPRECATE cannot commit while V remains default

DEPRECATE wins
    -> V no longer PUBLISHED
    -> SET_DEFAULT cannot commit V as default
```

Exact rendezvous realization remains architecture work.

---

## 8. CLEAR_DEFAULT — technical discovery CLOSED except concurrency/physical realization

`CLEAR_DEFAULT` changes only the current mutable default pointer and has no exact-version operand.

Admission:

```text
RelationshipDefinition exists
```

Mutation:

```text
default_version -> NULL
```

The command is idempotent when the default is already NULL. A physical implementation may avoid a real row rewrite in that case, but must still distinguish an absent Definition (404) from a present Definition whose default is already NULL (204).

No semantic preparation, exact-version read, property/DTV/history/topology/space read, cache interaction, new denormalization or post-write reload is required.

External concurrency handoff:

```text
after CLEAR_DEFAULT commits
    -> a new factual Relationship.CREATE implicit-version resolution
       cannot obtain the old default
```

The fate of a factual CREATE that had already resolved an exact default before CLEAR_DEFAULT commits belongs to later cross-family concurrency closure.

---

## 9. DEPRECATE — technical discovery CLOSED except concurrency/physical realization

`DEPRECATE` changes only lifecycle admission state of one exact immutable RDV.

Admission:

```text
RelationshipDefinition exists
exact RDV exists
RDV.status == PUBLISHED
Definition.default_version != target version
```

Mutation:

```text
RDV.status -> DEPRECATED
RDV.revision unchanged
```

No semantic preparation, RDV property read, DTV semantic load, historical-continuity probe, factual Relationship scan/count, topology/space read or post-write reload is required.

Existing factual Relationships pinned to the target exact version are intentionally **not** deprecation blockers. The exact immutable snapshot remains a valid historical dependency for those facts.

The immutable exact-RDV cache remains valid unchanged across `PUBLISHED -> DEPRECATED`; lifecycle status is not stored in the immutable cache.

Concurrency handoffs include at least:

```text
DEPRECATE vs SET_DEFAULT(target)
DEPRECATE vs factual Relationship.CREATE binding to target
DEPRECATE vs CLEAR_DEFAULT when target is current default
```

Exact rendezvous realization remains architecture work.

---

## 10. DELETE_DRAFT — technical discovery CLOSED except concurrency/physical realization

Admission needs only the exact mutable generation header:

```text
RelationshipDefinition exists
exact RDV exists
status == DRAFT
revision == expected_revision
```

The complete property declaration payload is not read for admission.

Mutation/ownership:

```text
DELETE exact DRAFT RDV root
    -> relationship_definition_properties owned cleanup

relationship_definition_space
    -> UNCHANGED

last_versions
    -> UNCHANGED by exact-version deletion
    -> allocated version number is never reusable
```

DRAFT versions are never published in the immutable RDV cache, so DELETE_DRAFT has no cache invalidation responsibility.

Successful deletion returns `204`; a repeated delete observes exact resource absence and returns the reviewed 404 outcome.

Concurrency handoff:

```text
DELETE_DRAFT vs REVISE
DELETE_DRAFT vs PUBLISH
DELETE_DRAFT vs DELETE_DRAFT
```

Only one operation may consume a given DRAFT generation identified by `expected_revision`. Exact conditional-delete/lock realization remains architecture work.

---

## 11. DELETE RelationshipDefinition root — technical discovery CLOSED except concurrency/physical realization

The stable root owns:

```text
RelationshipDefinitionVersion rows
    -> RelationshipDefinitionProperty rows
relationship_definition_space rows
```

There is no autonomous RelationshipResolution persistence in the M4 model.

A current factual Relationship referencing any exact version of the Definition is the only reviewed external blocker type for this operation.

### 11.1 Blocker authority — RATIFIED

The M4 error details require only:

```text
409 delete_blocked
    blocker_type = relationship
```

Therefore no blocker COUNT is required. A bounded `EXISTS` may be used as fail-fast optimization, but correctness must ultimately be owned by relational/FK lifetime arbitration or an equivalent current-state mechanism valid through the delete commit boundary.

This is necessary because a standalone preflight `EXISTS=false` cannot by itself exclude a new concurrent factual pin.

### 11.2 New-pinning rendezvous — RATIFIED handoff

Root DELETE requires an independent complete lifetime/admission rendezvous with both:

```text
Relationship.CREATE explicit exact-version selection
Relationship.CREATE implicit/default selection
```

Pre-clearing `default_version` is not sufficient to provide this guarantee and is not the primary semantic safety predicate.

### 11.3 `default_version` pre-clear classification — RATIFIED

The AS-IS pre-clear is classified as:

```text
semantic root-delete requirement
    -> NO

possible defense-in-depth
    -> YES

known AS-IS physical reason
    -> break the current cyclic FK:
       Definition.default_version -> RDV
       RDV -> Definition
```

Architecture decides whether final FK design still requires the explicit pre-clear or whether direct root-owned cascade/equivalent cleanup removes the need.

### 11.4 Logical DML and cost — RATIFIED

Conceptually:

```text
stabilize root lifetime
optional physical default pre-clear if final FK design requires it
DELETE RelationshipDefinition root
    -> owned cleanup of versions
    -> owned cleanup of version properties
    -> owned cleanup of relationship_definition_space
```

Application persistence round trips are bounded/constant in owned-row counts. Physical cleanup work is naturally:

```text
O(versions + properties + relationship_definition_space rows)
```

No application loop or full topology/property/schema reload is required.

No correctness-driven distributed cache invalidation is required; orphan immutable local cache entries are harmless because cache presence never proves current existence/admission and identities are not reused.

### 11.5 `last_versions` handoff — RATIFIED boundary

Complete-lineage allocator-row lifetime is owned by the cross-domain `version-allocation.md` architecture handoff. RelationshipDefinition DELETE does not independently choose retain-vs-delete behavior for the shared allocator row.

The final architecture must preserve the cross-domain allocation invariants and must not accidentally reintroduce version-number reuse semantics.

---

# 19. Bidirectional consistency sweep

The following checkpoints reconcile the operation-level baseline with the factual Relationship, DataType, ObjectTemplate ancestry and shared version-allocation boundaries.

### CS-01 — historical `value_mode` owner correction — RESOLVED

The family owner previously retained the stale monotonic rule:

```text
once LIST
    -> later SCALAR forbidden
```

That wording conflicted with the later M4 revalidation ratified during this sweep and with factual `Relationship.SCHEMA_CHANGE` preserve-or-fail semantics.

The owner has now been corrected at the source. Current family rule:

```text
same-name committed history
    -> datatype_id lineage remains stable

exact datatype_version
    -> may change

value_mode
    -> SCALAR -> LIST allowed
    -> LIST -> SCALAR allowed
```

`historical LIST -> SCALAR violation` is no longer a normal REVISE semantic error. Exact RDV validity remains distinct from factual cross-version migrability.

### CS-02 — CREATE_NEXT immutable cache authority wording — RESOLVED

The family owner previously said that CREATE_NEXT did not treat worker cache state as the authoritative clone source. That wording was too broad and could be read as forbidding the ratified immutable snapshot cache-hit path.

The owner now distinguishes payload authority from current-state authority:

```text
ImmutableRelationshipDefinitionVersionCache snapshot READY
    -> may provide the exact immutable declaration snapshot directly
    -> sufficient clone payload for CREATE_NEXT

PostgreSQL
    -> remains authority for current Definition existence
    -> source exact-version existence
    -> source lifecycle eligibility PUBLISHED | DEPRECATED
```

The compiled facet is not required for CREATE_NEXT; `snapshot READY` is sufficient. On cache miss, CREATE_NEXT performs a bounded cold load of the immutable snapshot and may publish that facet.

### CS-03 — `relationship_definition_space` responsibility matrix — RESOLVED

The owner now records the complete responsibility boundary for the derived exact-template semantic closure:

```text
RelationshipDefinition.CREATE
    -> derive/arbitrate/persist complete space

Relationship.CREATE
    -> consume one exact semantic cell for oriented admission
       and unique owning-Definition resolution

RelationshipDefinition.GET detail
    -> use compact roots + current descendant sets
    -> no space scan/refactoring

RelationshipDefinition version/default/lifecycle operations
    -> no space read or write

RelationshipDefinition.DELETE root
    -> owned space cleanup

ObjectTemplate stable-ancestry mutation
    -> coherent set-based maintenance of affected space
```

Already-admitted factual GET/DATA_CHANGE/SCHEMA_CHANGE/DELETE operations do not re-certify model-plane topology through the space.

The owner also records that a newly created subtype must update ancestry and every induced semantic cell in one coherent commit boundary. Under current single inheritance, subtype creation cannot introduce a genuinely new collision between two already-certified Definitions: any such overlap would imply an already-existing overlapping root-level cell. Concurrent ObjectTemplate.CREATE and RelationshipDefinition.CREATE still require an architecture-level rendezvous so either serial order produces complete closure.

Compact endpoint-root references remain real ObjectTemplate lifetime dependencies. Descendant appearances that exist only through derived expansion must not become autonomous deletion blockers.

The legacy ObjectTemplate relationship-capabilities discovery remains deferred to the ObjectTemplate family sweep because it still assumes autonomous RelationshipResolution identity and mutable names. RelationshipDefinition records only the downstream-consumer handoff and does not freeze that route's final read model here.

### CS-04 — PUBLISH commit and immutable-cache visibility — RESOLVED

The owner now records PostgreSQL commit as the sole authoritative publication boundary.

```text
outside short UoW
    prepare complete immutable exact-RDV snapshot + compiled semantics

inside short UoW
    final generation/lifecycle/dependency/history admission
    DRAFT -> PUBLISHED
    conditional first-default claim
    COMMIT

post-commit only
    publish prepared immutable cache entry
```

A cache entry must never become visible before commit. A rolled-back PUBLISH therefore leaves no apparent immutable published snapshot.

Post-commit cache publication is an optimization rather than a second domain transaction:

```text
DB commit succeeds + cache publication fails
    -> PUBLISH remains successful
    -> 204
    -> later cache miss reconstructs from PostgreSQL
```

The failure may be logged/observed operationally but must not be returned as `500`, because the lifecycle mutation is already durable and a caller retry would address a now non-DRAFT target.

Worker-local caches need no synchronous distributed propagation. Other workers may cold-load the exact immutable state. Facet readiness remains explicit: `snapshot READY` is sufficient for CREATE_NEXT, while factual runtime consumers require `compiled READY`; neither is inferred from the other.

PUBLISHED -> DEPRECATED leaves the immutable entry valid. Root deletion needs no correctness-driven invalidation, and cache state never owns current `status`, `default_version`, resource existence or admission.


### CS-05 — RDV declaration → exact DataTypeVersion dependency matrix — RESOLVED

The owner now separates three concerns:

```text
exact dependency lifetime
    -> every persisted RelationshipDefinition declaration

active-model lifecycle dependency
    -> declarations owned by PUBLISHED RDVs only

new-binding PUBLISHED admission
    -> CREATE selected pins
    -> REVISE added/rebound pins
    -> all pins when publishing an RDV
```

Lifecycle matrix:

```text
DRAFT declaration
    -> lifetime blocker YES
    -> DTV deprecation blocker NO

PUBLISHED declaration
    -> lifetime blocker YES
    -> DTV deprecation blocker YES

DEPRECATED declaration
    -> lifetime blocker YES
    -> DTV deprecation blocker NO
```

The owner also records that REVISE declaration DML classification and exact-dependency classification are independent. A value-mode or ordinal change may cause a physical row replacement while retaining the same exact DTV pin; that unchanged pin requires lifetime preservation but no current PUBLISHED re-admission.

CREATE_NEXT continues to require neither DTV reload/compilation nor current PUBLISHED admission. Architecture must prove the cloned pins' lifetime through source RDV/declaration stabilization and exact declaration FKs, or add only the minimum equivalent exact-target protection.

The cross-family `RDV.PUBLISH × DTV.DEPRECATE` rendezvous must produce only the two serial outcomes: publication first creates an active blocker, while deprecation first makes publication fail `dependency_not_admissible`.

### CS-06 — implicit default resolution freezes one exact RDV selection — RESOLVED

The RelationshipDefinition owner and factual Relationship owner now agree that `default_version` is used only to select one exact RDV when the caller omits an explicit version.

```text
resolve D.default_version = V
    -> materialize exact target D@V
    -> keep D@V fixed for the in-flight command
```

Later `SET_DEFAULT`, `CLEAR_DEFAULT`, or first-default establishment changes only future implicit resolutions. Final factual CREATE admission protects exact `D@V` existence/same-Definition ownership and `PUBLISHED` status through commit, but does not require `D.default_version == V`.

The owner records the corresponding race outcomes:

```text
CLEAR before resolution
    -> default_version_unavailable

CLEAR after exact resolution
    -> no retarget/invalidation from pointer change alone

SET_DEFAULT before resolution
    -> new pointer may be selected

SET_DEFAULT after resolution
    -> already selected exact target remains fixed

first PUBLISH before resolution
    -> newly established default may be selected

resolution observes NULL first
    -> no mandatory chase of a concurrently appearing default
```

A later loss of exact `PUBLISHED` status still blocks the final new binding. This rule is independent of the still-open factual CREATE choice between explicit Definition selection and unique owner derivation from the requested semantic cell.

### CS-07 — committed property-history linearization — RESOLVED

The owner now distinguishes same-target publication arbitration from Definition-level committed-history arbitration.

```text
PUBLISH same exact DRAFT
    -> target generation/lifecycle gate

PUBLISH different exact DRAFTs of the same Definition
    -> committed-history linearization
    -> incompatible candidates cannot both commit
```

Every successful publication must be compatible with all `PUBLISHED | DEPRECATED` same-name declarations linearized before its commit, under the current datatype-lineage-only continuity rule.

REVISE remains provisional with respect to future history growth: it validates against history at its own commit boundary, but a later publication may make that DRAFT no longer publishable. PUBLISH does not scan or protect unrelated DRAFT candidates and always re-certifies its selected candidate.

`PUBLISHED -> DEPRECATED` does not remove history membership, while DELETE_DRAFT has no history effect. The implementation direction remains set-based early/final probes without worker-side full-history loading or a new history-summary materialization. Exact Definition-local concurrency realization remains architecture work.

---

# 20. Consolidated logical model and semantic persistence boundary

The stable compact source of truth is conceptually:

```text
relationship_definitions
    id
    symmetric
    endpoint_a_template_id
    endpoint_b_template_id
    name_a_to_b
    name_b_to_a
    default_version
```

A/B preserves the caller-authored orientation. It is not a privileged source/target ordering and is not canonicalized by UUID or another synthetic key.

Both naming slots are populated:

```text
symmetric = true
    -> name_a_to_b == name_b_to_a

symmetric = false
    -> name_a_to_b != name_b_to_a
```

Exact version and declaration state remain conceptually:

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
    internal ordinal
    datatype_id
    datatype_version
    value_mode
```

The physical ordinal column name remains architecture work. Public array order defines it and exact-version reads preserve it without exposing it.

One exact-template directed semantic cell is:

```text
(from_template_id, name, to_template_id)
```

The ordered templates and stable name are all part of semantic identity. One current semantic cell has one owning RelationshipDefinition globally; duplicate generation inside one Definition and repetition across Definitions are both invalid.

`relationship_definition_space` is the complete Definition-owned derived closure over compact Definition state and current stable ObjectTemplate ancestry. It is relational semantic-cell ownership/arbitration knowledge, not a second domain authority and not an autonomous RelationshipResolution entity.

Same-template cells are valid model-plane applicability:

```text
(T, name, T)
```

They mean that two Objects in the same compatibility space may participate. They do not authorize factual self-reference. The factual owner separately requires:

```text
from_object_id != to_object_id
```

Final DDL must therefore not translate the factual Object-identity rule into a model-plane `from_template_id != to_template_id` restriction.

Symmetry/name equality and allowed endpoint-space topology are domain semantics. Final architecture must retain genuinely relational integrity and arbitration, but must not add semantic database `CHECK` predicates merely to duplicate domain validation without an independent relational reason.

No additional current authority is introduced for:

```text
autonomous RelationshipResolution persistence
resolution_id model identity
another relational copy of exact RDV semantics
persisted committed-history summary
worker cache for relationship_definition_space
mutable RelationshipDefinition topology/default cache
```

The shared `last_versions(id, last_version)` allocator remains owned by `version-allocation.md`; exact-version deletion never rewinds it.

---

# 21. Architecture handoff, reviewed-baseline result and reopen triggers

The reviewed baseline deliberately leaves these mechanisms open while fixing the guarantees they must preserve:

```text
final SQL column names/types/nullability
PK/FK/UNIQUE/index realization
semantic-cell arbitration carrier
owned cleanup and ON DELETE behavior
default-version same-Definition FK/cycle realization
last_versions row lifetime on root deletion
exact lock/gate/wait/retry/deadlock protocol
transaction isolation and final-admission statement shapes
migration/backfill from autonomous RelationshipResolution state
cache process topology, capacity, eviction and observability
cold-loader statement grouping
verification/concurrency scenario registry
```

Required concurrency families include at least:

```text
RD.CREATE vs RD.CREATE semantic-cell ownership
RD.CREATE vs ObjectTemplate ancestry growth
same-DRAFT REVISE/PUBLISH/DELETE_DRAFT generation races
different-RDV PUBLISH committed-history linearization
RDV.PUBLISH vs DTV.DEPRECATE
SET_DEFAULT vs DEPRECATE(target)
CLEAR/SET/default resolution vs factual Relationship.CREATE
RDV.DEPRECATE vs new factual binding
root DELETE vs explicit and implicit new factual pinning
same-lineage exact-version allocation
```

The current sweep has checked this owner bidirectionally against:

```text
general-domain-principles.md
version-allocation.md
object-template-ancestry-cache.md
relationship.md
the former semantic-intent draft
the former operation-specific RelationshipDefinition notes
the temporary technical-consolidation ledger
```

Current result:

```text
one active RelationshipDefinition family owner
no autonomous RelationshipResolution candidate
no unresolved REST/semantic/data-path/cache contradiction
no temporary RelationshipDefinition source or consolidation file required
all unresolved items classified as architecture/concurrency/physical handoffs
```

`RelationshipDefinition` therefore reaches M4 `REVIEWED BASELINE` at discovery level. This means the owner may be reused as reviewed input by later family and architecture work. It does not mean:

```text
M4 contract frozen
M4 architecture frozen
implementation authorized
```

Targeted revalidation is required if later work changes a material dependency, including:

```text
ObjectTemplate inheritance no longer single
stable Definition topology or names become mutable/versioned
factual Relationship CREATE selector/admission materially changes
DataType exact-dependency lifecycle rules change
a new hot consumer requires another model-plane projection/materialization
measured semantic-space fan-out invalidates the current storage trade-off
versioned lineage UUID allocation stops sharing the current practical namespace
a physical design cannot realize a reviewed invariant without changing semantics
```

Implementation remains forbidden until the normal M4 Contract -> Architecture -> Steps -> Status authorization sequence is satisfied.
