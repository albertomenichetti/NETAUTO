# M4 WIP — ObjectTemplate model-plane review owner

**Status:** ACTIVE REVIEW FRONTIER / SINGLE FAMILY OWNER / BASELINE RECONSTRUCTED / PUBLIC CONTRACT REVIEW PENDING / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose and ownership

This document is the single current M4 WIP owner for the `ObjectTemplate` model-plane family while its caller-first review is in progress.

The objective is to bring ObjectTemplate to the same discovery/revalidation maturity already reached by Object, factual Relationship and RelationshipDefinition. This owner will progressively contain:

```text
functional capability coverage
public REST contracts and wire carriers
stable lineage and exact-version semantics
inheritance and effective-schema responsibilities
logical persistence/materialization boundaries
cache facets and validation-loader contract
operation-level data paths and cost direction
cross-family lifetime/admission obligations
explicit concurrency / physical architecture handoffs
```

This bootstrap records the complete source corpus, the delivered AS-IS baseline, already-reviewed incoming constraints and the assumptions that require explicit revalidation. It does **not** close any ObjectTemplate public contract by itself.

The operation-specific ObjectTemplate discovery files remain in the working corpus as source material during the review. They are evidence and working hypotheses, not competing owners. They will be removed only after lossless absorption and a completed family consistency sweep.

Everything under `wip/` remains globally non-normative and does not authorize implementation.

---

# 1. Authority and precedence

Interpret this owner under:

```text
AGENTS.md
README.md
docs/general/linee_guida_progetto.md
docs/milestones/M4/status.md
docs/architecture/README.md
```

Until M4 freezes and promotes an explicit TO-BE architecture set, the delivered documents under `docs/architecture/` remain the normative AS-IS baseline.

Within M4 WIP, current precedence for this review is:

```text
general-domain-principles.md
    -> version meaning vs migrability
    -> operation-owned lifecycle payload
    -> no diagnostic-only backend work

version-allocation.md
    -> monotonic/no-reuse exact-version allocation
    -> logical last_versions(id, last_version)

reviewed downstream/cross-operation owners
    -> object.md
    -> object-revision.md
    -> object-components-persistence.md
    -> relationshipdefinition.md
    -> relationship.md

reviewed support
    -> object-template-ancestry-cache.md

this file
    -> current ObjectTemplate family review owner

objecttemplate-*-discovery.md
objecttemplate-validation-loader-handoff.md
    -> source material / handoff evidence to absorb or supersede

DataType WIP
    -> ACTIVE INPUT until its own family review
```

A source note that conflicts with a reviewed owner or cross-domain principle is not selected silently. The affected point must be explicitly revalidated here.

---

# 2. Review objective and phase boundary

The immediate objective is to close the **public contract** of every retained ObjectTemplate capability one operation at a time.

For each capability the review must explicitly ratify:

```text
HTTP method and route
path parameters
query parameters
strict request body
omission vs explicit null semantics
success status
success body and Location, where applicable
public response DTO and collection/page shape
ordering/cardinality/pagination semantics
finite public failure set and precedence
```

Only after a capability's caller-visible contract is closed should the review continue downward into:

```text
semantic preparation
current admission
logical persistence/materialization
cache use and cold fill
data path and cost
concurrency guarantees
relational-schema implications
```

The final family exit condition is:

```text
objecttemplate.md
    -> sole lossless ObjectTemplate family owner
    -> REVIEWED BASELINE at discovery/revalidation level

all retained capabilities
    -> caller-first contract closed
    -> logical technical path reviewed

cross-family sweep complete against
    -> Object
    -> ownership/component persistence
    -> RelationshipDefinition
    -> DataType boundary
    -> version allocation
    -> Lifecycle inputs

operation-specific source files
    -> removed only after verified absorption
```

This is not Contract freeze, Architecture freeze or implementation authorization.

---

# 3. Complete capability census

The delivered AS-IS surface contains exactly six reads and ten mutations.

## Reads — 6

```text
GET /api/v1/core/object-templates
GET /api/v1/core/object-templates/{template_id}
GET /api/v1/core/object-templates/{template_id}/versions
GET /api/v1/core/object-templates/{template_id}/versions/{version}
GET /api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema
GET /api/v1/core/object-templates/{template_id}/relationship-capabilities
```

## Mutations — 10

```text
POST   /api/v1/core/object-templates
POST   /api/v1/core/object-templates/{template_id}/create-next
POST   /api/v1/core/object-templates/{template_id}/versions/{version}/revise
POST   /api/v1/core/object-templates/{template_id}/versions/{version}/publish
POST   /api/v1/core/object-templates/{template_id}/set-default
POST   /api/v1/core/object-templates/{template_id}/clear-default
POST   /api/v1/core/object-templates/{template_id}/versions/{version}/deprecate
DELETE /api/v1/core/object-templates/{template_id}/versions/{version}
DELETE /api/v1/core/object-templates/{template_id}
POST   /api/v1/core/object-templates/{template_id}/set-description
```

This is the review starting census, not a blanket M4 retention decision. Every route, carrier, output and failure contract remains open until explicitly reviewed. A capability may be retained, reshaped, combined or removed only through an explicit caller/domain decision.

No additional ObjectTemplate capability is introduced by this baseline reconstruction.

---

# 4. Source corpus reconstructed

## Delivered AS-IS authorities

```text
docs/architecture/objecttemplate.md
    stable lineage, exact versions, inheritance, declarations,
    effective schema, lifecycle/default, dependency and delete semantics
docs/architecture/api.md
    current route inventory, wire DTOs, success/failure mapping
docs/architecture/persistence.md
    current tables, columns, keys, FKs, indexes and delete actions
docs/architecture/concurrency-matrix.md
    semantic mutation interactions and safety predicates
docs/architecture/concurrency.md
    current PostgreSQL lock/gate/UoW realization
docs/architecture/verification.md
    current finite route/schema/scenario verification obligations
```

These describe delivered behavior, not the M4 TO-BE result.

## Operation-specific M4 source material

The current source set covers all sixteen delivered capabilities:

```text
objecttemplate-create-discovery.md
objecttemplate-create-next-discovery.md
objecttemplate-delete-draft-discovery.md
objecttemplate-delete-lineage-discovery.md
objecttemplate-deprecate-discovery.md
objecttemplate-get-effective-schema-discovery.md
objecttemplate-get-lineage-discovery.md
objecttemplate-get-version-discovery.md
objecttemplate-list-lineages-discovery.md
objecttemplate-list-versions-discovery.md
objecttemplate-publish-discovery.md
objecttemplate-relationship-capabilities-discovery.md
objecttemplate-revise-discovery.md
objecttemplate-set-default-discovery.md
objecttemplate-set-description-discovery.md
objecttemplate-clear-default-discovery.md
```

Cross-domain handoff input:

```text
objecttemplate-validation-loader-handoff.md
```

These notes were produced during an earlier bottom-up/data-access pass. Their findings remain useful evidence, but several assumptions have since been superseded by reviewed M4 owners and must be revalidated rather than copied.

## Reviewed incoming M4 owners/support

```text
general-domain-principles.md
version-allocation.md
object.md
object-revision.md
object-components-persistence.md
object-template-ancestry-cache.md
relationshipdefinition.md
relationship.md
```

## Deliberately unresolved upstream input

DataType remains `ACTIVE INPUT`. ObjectTemplate may close the exact consumer contract it requires from DataType dependencies, but it must not freeze DataType's final internal relational, cache or public design during this family review.

---

# 5. Reconstructed delivered semantic baseline — AS-IS reference only

This section is a neutral reconstruction of delivered ObjectTemplate semantics. It is not a TO-BE ratification.

## Stable lineage

Delivered stable lineage state is:

```text
id
namespace
name
abstract
parent_template_id
```

Delivered mutable/current lineage state is:

```text
description
default_version
```

The stable parent lineage is fixed for normal lineage lifetime; inheritance is single-parent and acyclic. `abstract=true` prevents direct Object creation but does not prevent use as an inheritance parent, component target or Relationship endpoint compatibility root.

## Exact ObjectTemplateVersion

Delivered exact identity is:

```text
(template_id, version)
```

An exact version contains:

```text
revision
status = DRAFT | PUBLISHED | DEPRECATED
exact parent pin for non-root versions:
    parent_template_id
    parent_version
local properties
local component declarations
```

DRAFT is mutable and uses `expected_revision`; PUBLISHED and DEPRECATED carry immutable semantic snapshots. Multiple DRAFTs may coexist.

The delivered allocation rule `max(existing)+1` and DRAFT-number reuse are recorded only as AS-IS and are superseded for M4 review by `version-allocation.md`.

## Local property declarations

Delivered local property state is:

```text
name
position
datatype_id
datatype_version
value_mode = SCALAR | LIST
required
migration_default
```

Every declaration pins one exact DataTypeVersion. Property cardinality belongs to the ObjectTemplate declaration rather than DataType.

Delivered rules distinguish optional and required SCALAR/LIST properties and validate required migration defaults against the exact pinned DataTypeVersion. `migration_default` is migration input for `Object.SCHEMA_CHANGE`, not an Object CREATE default.

Property semantic continuity is keyed by:

```text
(declaring_template_id, name)
```

The delivered architecture treats `position` as explicit declaration ordering state and historically permits only normal `SCALAR -> LIST` evolution. Both points require explicit M4 revalidation.

## Local component declarations

Delivered component declaration state is:

```text
name
position
target_template_id
```

The target is a stable ObjectTemplate lineage, not an exact version. Compatibility includes the target lineage and its descendants. Component and property names share one effective member namespace; a child cannot override or hide inherited members.

Slot semantic continuity is keyed by:

```text
(declaring_template_id, name)
```

Delivered normal evolution permits target widening toward an ancestor and treats narrowing/unrelated retargeting as requiring another controlled capability.

## Effective schema

Delivered semantic authority is:

```text
exact parent-version chain
+
local properties
+
local components
```

The public exact-version read exposes local declarations; effective schema is a separate projection that identifies each member's declaring lineage.

Delivered persistence computes effective schema through exact ancestry rather than owning a durable effective-schema table. Earlier M4 discovery proposes changing this boundary; that proposal is not ratified by this bootstrap.

## Lifecycle, defaults and dependencies

Delivered lifecycle is:

```text
DRAFT -> PUBLISHED -> DEPRECATED
```

A lineage default is null or an exact same-lineage PUBLISHED version. First publication may establish a missing default; later publications do not replace it automatically. The current default cannot be deprecated.

A PUBLISHED ObjectTemplateVersion participates in the active model graph. Its direct exact parent and local exact DataTypeVersion dependencies must remain PUBLISHED while that active edge exists.

Individual exact-version deletion is DRAFT-only. Whole-lineage deletion is blocked by current external references and removes owned exact versions/declarations only after admission.

## Read responsibility

Delivered public reads distinguish:

```text
stable lineage
exact local version
exact effective schema
relationship capabilities
```

The delivered public-read architecture targets one authoritative PostgreSQL business statement per capability and trusts admitted persisted facts rather than re-running mutation certification.

---

# 6. Already-reviewed incoming constraints

The following requirements are reviewed dependencies that this family must absorb or satisfy.

## Exact-version allocation

```text
new exact version
    -> allocate through shared last_versions(id, last_version)
    -> version increases with allocation order
    -> deleted exact version number is never reused
```

No ObjectTemplate operation may retain `max(existing)+1` as current M4 semantics. Numeric version order does not encode genealogy, semantic widening, compatibility, migrability, publication order or preference.

## Exact-version validity vs Object migration

`REVISE` and `PUBLISH` own ObjectTemplate candidate validity and active-model certification. They must not reject an otherwise valid exact version solely because a particular current Object may later fail `Object.SCHEMA_CHANGE` into it.

```text
valid exact ObjectTemplateVersion
    !=
all current Objects can migrate to it
```

The concrete migration operation owns preserve-or-fail admission for current runtime values and ownership state.

## Stable ancestry support

Reviewed support already defines:

```text
object_template_ancestry
    descendant_template_id
    ancestor_template_id
    depth
```

with reflexive `(T,T,0)` rows and worker-local READY semantics for complete source ancestor sets.

The ObjectTemplate family must close write/ownership maintenance on lineage CREATE/DELETE, coherence with stable parent state, relational lifetime behavior, cold-load/index support and interaction with `relationship_definition_space` maintenance.

Existing ancestry for an already-created lineage is immutable; creating a new descendant creates a new source set and does not change existing descendants' ancestor sets.

## Object direct-creation and validation consumer

Reviewed `Object.CREATE` requires:

```text
PostgreSQL
    -> current lineage/exact existence
    -> exact target PUBLISHED through binding commit

READY stable/immutable ObjectTemplate semantics
    -> stable abstract/direct-creation eligibility
    -> complete effective property schema
    -> exact DataTypeVersion semantic linkage
    -> compiled/runtime validation structures
```

The ObjectTemplate phase must provide a bounded reusable cold-load/materialization path. Runtime validation must not fall back to recursive parent-chain reconstruction or per-property/per-DataType N+1 loading. Cache presence never proves current lineage/exact existence, lifecycle status or default selection.

## Object schema migration consumer

Reviewed `Object.SCHEMA_CHANGE` requires exact SOURCE/TARGET ObjectTemplateVersion semantics and a reusable exact-pair migration plan. ObjectTemplate must provide immutable effective-property and effective-component information sufficient to preserve/validate values, identify semantic continuity by `(declaring_template_id, name)`, compute target component-slot delta and classify slot continuity/removal/replacement/target evolution.

Numeric target direction alone has no migration meaning.

## Current Object component-slot materialization

Reviewed Object persistence uses certified exact effective component semantics to maintain:

```text
object_component_slots
    object_id
    slot_declaring_template_id
    slot_name
    target_template_id
```

Object CREATE and SCHEMA_CHANGE require a bounded DB-internal source for the complete effective component set of an exact ObjectTemplateVersion. The ObjectTemplate family does not own factual ownership edges, but its certified effective slot semantics are their model source.

## RelationshipDefinition semantic-space maintenance

`relationship_definition_space` is derived from:

```text
compact RelationshipDefinition endpoint roots/names
+
current stable ObjectTemplate ancestry
```

ObjectTemplate stable-ancestry mutation must keep this derived closure coherent in the same committed state. In current normal semantics, lineage CREATE and admissible lineage DELETE are the material ancestry-change points; stable parent mutation is not an existing normal capability.

Compact endpoint-root references are real ObjectTemplate lifetime dependencies. Descendant rows generated only through derived expansion must not become autonomous blockers.

## Relationship capabilities downstream consumer

The delivered `relationship-capabilities` discovery depends on autonomous `RelationshipResolution`, `resolution_id` and mutable Resolution names. Those concepts no longer exist in the reviewed RelationshipDefinition model.

The ObjectTemplate family must redesign the capability contract/read projection against compact stable RelationshipDefinition semantics and `relationship_definition_space`. No old Resolution-based route field or pagination key survives by default.

## Cache lifecycle boundary

```text
DRAFT exact semantics
    -> mutable
    -> not immutable-cacheable

PUBLISHED / DEPRECATED exact semantics
    -> immutable payload
    -> may remain cache-valid across PUBLISHED -> DEPRECATED

PostgreSQL
    -> current existence
    -> current status/default
    -> final mutation admission
```

Publication of immutable cache state must occur only after authoritative commit. A post-commit local warm-up failure must not convert a durable successful publication into an API error when cold load remains available.

---

# 7. Strong M4 candidates from source material — not yet ratified here

## Immutable effective-schema materialization

Strong candidate:

```text
DRAFT
    -> effective schema derived transiently
    -> no long-lived immutable materialization

PUBLISHED / DEPRECATED
    -> own immutable effective-property and effective-component projections
    -> publication is certification/materialization boundary
```

The authoritative semantic state would remain stable lineage + exact parent pin + local declarations. Materialized effective rows would be derived owned state.

This candidate directly supports Object validation, Object schema migration and `object_component_slots` maintenance. Exact row shape, ordinals, ownership, indexes and publication DML remain open.

## Runtime-oriented immutable exact-version cache

Strong candidate facets include:

```text
stable lineage descriptor / abstract semantics
exact parent identity
complete effective properties
complete effective components
linked/compiled exact DataTypeVersion validators
```

The cache should be shaped for repeated Object data-plane consumption, not as a byte-for-byte public DTO or persistence mirror. Facets may be independently READY.

## Bounded validation loader

`objecttemplate-validation-loader-handoff.md` requires a capability conceptually equivalent to:

```text
ensure_object_template_validation_ready(template_id, version)
```

The family must close the authoritative cold source, bounded statement shape, facet readiness, DTV interaction, local fill coordination and no-extra-round-trip opportunistic warming rule.

## Set-based/bulk model-plane work

Source notes favor one authoritative business statement for public reads, set-based historical continuity lookup, bulk local declaration DML, DB-internal ancestry/effective projection construction and no per-member N+1 persistence or semantic loads.

Rare model-plane operations need bounded statement count, not artificial one-mega-statement compression.

## No separately materialized exact-version ancestry unless justified

Current evidence favors consuming the final effective schema rather than an explicit `object_template_version_ancestry` relation. A separate exact-version closure remains unjustified unless a real operation independently needs it after the full sweep.

---

# 8. Known stale or disputed assumptions requiring explicit revalidation

## Allocation and DRAFT-number reuse — superseded

```text
max(existing version) + 1
reuse deleted highest DRAFT number
```

are superseded by the shared monotonic/no-reuse allocator.

## Autonomous RelationshipResolution — superseded

Any blocker, relationship-capability DTO, filter, cursor or query plan based on:

```text
relationship_resolutions
resolution_id
mutable Resolution.name
```

must be replaced or removed.

## Public declaration `position` — open

Delivered ObjectTemplate authoring exposes explicit `position`; RelationshipDefinition M4 moved ordering to request-array order plus internal ordinal. ObjectTemplate must explicitly decide whether public property/component contracts retain position, use array order, or use another carrier. Uniformity is desirable only where semantics genuinely align.

## Historical `LIST -> SCALAR` prohibition — open

Delivered ObjectTemplate history permits only normal `SCALAR -> LIST`. M4 now separates exact-version validity from concrete Object migrability, and factual Object migration owns preserve-or-fail behavior. The ObjectTemplate rule must be revalidated deliberately rather than inherited or reversed by analogy.

## CREATE_NEXT clone strategy — open

The source note prefers DB-side cloning of immutable **local declarations**, partly because the runtime cache candidate is effective-schema oriented. RelationshipDefinition later preferred cache-snapshot cloning in application state. ObjectTemplate must compare local-declaration clone requirements, runtime-cache facet boundaries, source/current lifetime admission, referenced-target lifetime and bounded DML/payload cost. No strategy wins merely for cross-family uniformity.

## Effective-schema lifecycle and exact read routing — open

The strongest source direction materializes immutable effective schema only at PUBLISH and derives DRAFT effective schema from immutable parent plus local DRAFT declarations. Exact public GET and effective-schema GET contracts must be closed before the final read routing/materialization design is ratified.

## Mutation responses and response-only reloads — open

AS-IS mutations often return complete lineage/version state. M4's caller-first default favors `204` when no operation-owned result is needed and `201 + Location` for creation. Every ObjectTemplate operation must ratify its own response; no existing body survives automatically.

## Current lock plan — evidence, not TO-BE authority

Existing duplicate resolution passes, row locks, advisory gates and aggregate reloads may protect real safety predicates, but the current mechanism does not determine the M4 contract. The family review must first close semantics and required concurrent outcomes; global architecture later derives the smallest correct realization.

## DataType internal design — deliberately deferred

ObjectTemplate properties require exact DataTypeVersion identity, semantic validation and lifecycle admission. The family may state those consumer requirements, but relocation of `base_type`, DataType cache layout, DataType public DTOs and DataType operation contracts remain owned by the later DataType sweep.

---

# 9. Public-contract review discipline

For each operation, discussion and persistence proceed in this order:

```text
1. caller capability and route identity
2. path/query carrier grammar
3. strict request body and omission/null rules
4. success status, body and Location
5. response DTO cardinality/order/pagination
6. finite public error catalogue and precedence
7. explicit contract-closure checkpoint in this owner
```

During public-contract review:

```text
DO use
    caller need
    domain meaning
    consistency with already-reviewed analogous APIs
    bounded diagnostic principle

DO NOT use as authority
    current SQL convenience
    current table shape
    current lock plan
    source-file status labels
    desire for DTO reuse alone
```

Technical findings may be consulted to avoid an impossible or pathologically expensive contract, but they do not silently choose the contract.

After one public contract is closed, the owner records the decision immediately before moving to the next capability.

---

# 10. Working capability review sequence

```text
READS
1. LIST ObjectTemplate lineages
2. GET one ObjectTemplate lineage
3. LIST exact ObjectTemplateVersions
4. GET one exact ObjectTemplateVersion
5. GET exact effective schema
6. GET ObjectTemplate relationship capabilities

MUTATIONS
7. CREATE ObjectTemplate
8. CREATE_NEXT ObjectTemplateVersion
9. REVISE ObjectTemplateVersion
10. PUBLISH ObjectTemplateVersion
11. SET_DEFAULT
12. CLEAR_DEFAULT
13. DEPRECATE ObjectTemplateVersion
14. DELETE_DRAFT ObjectTemplateVersion
15. DELETE ObjectTemplate lineage
16. SET_DESCRIPTION
```

The order is operational, not semantic. It may be changed only explicitly during the review. No item is closed by appearing in this list.

The first public-contract checkpoint is:

```text
GET /api/v1/core/object-templates
```

---

# 11. Bootstrap result and current open boundary

Completed by this baseline reconstruction:

```text
ObjectTemplate selected as ACTIVE REVIEW FRONTIER
single family owner created
complete 6-read / 10-mutation census recorded
all operation-specific source material mapped and retained
AS-IS semantic baseline reconstructed
reviewed Object/ownership/RelationshipDefinition/version/cache inputs mapped
known stale assumptions made explicit
public-contract review protocol and sequence established
```

Not completed:

```text
no ObjectTemplate public contract ratified by this bootstrap
no source WIP absorbed or removed
no effective-schema/materialization strategy frozen
no cache implementation frozen
no DataType family decision frozen
no SQL/DDL/index/lock/retry/migration choice frozen
no Contract/Architecture/Steps gate advanced
no implementation authorized
```

The active next step is the operation-by-operation public-contract review beginning with the ObjectTemplate lineage collection.

---

# 12. OT-GET-01 — LIST ObjectTemplate lineages

**State:** PUBLIC CONTRACT CLOSED / AUTHORITATIVE DATA PATH + CACHE BOUNDARY + PERSISTENCE/INDEX HANDOFF REVIEWED / TECHNICAL REVIEW IN PROGRESS / CURRENT M4 CANDIDATE

## Capability and responsibility

M4 retains a public collection capability for current `ObjectTemplate` lineages.

An `ObjectTemplate` is the stable lineage identity; exact `ObjectTemplateVersion` resources remain distinct subordinate resources. The collection answers:

```text
which current ObjectTemplate lineages exist
and match the caller's explicitly selected collection scope?
```

Membership is not implicitly restricted to:

```text
abstract == false
default_version present
at least one PUBLISHED exact version
direct Object.CREATE eligibility
```

Abstract, default-less or otherwise non-directly-instantiable lineages remain valid model-plane resources for inheritance, component targets and Relationship compatibility.

The collection does not own:

```text
exact-version listing or detail
local or effective schema
property/component declarations
relationship-capability projection
Object.CREATE admission
historical/deleted lineage discovery
mutation-semantic recertification
```

## Method and route

```http
GET /api/v1/core/object-templates
```

`GET` matches a side-effect-free current collection read. The existing `/object-templates` noun remains correct because `ObjectTemplate` already denotes the stable lineage; subordinate `/versions` routes distinguish exact snapshots.

M4 does not introduce, for this checkpoint:

```text
/object-template-lineages
/object-templates/lineages
a command-style collection search route
removal of the collection capability
```

## Path and query carrier inventory

Path parameters:

```text
none
```

The retained query-parameter inventory is exactly:

```text
namespace
name
abstract
parent_template_id
cursor
limit
```

Their caller-facing responsibilities are:

```text
namespace
    -> optional exact filter on the stable lineage namespace

name
    -> optional exact filter on the stable local lineage name

abstract
    -> optional exact filter on the stable abstract flag
    -> omission does not restrict collection membership

parent_template_id
    -> optional filter on the stable direct-parent relationship only
    -> it does not mean arbitrary ancestor or descendant search

cursor
    -> optional opaque continuation carrier for the same collection scope

limit
    -> optional requested page size
```

`parent_template_id` retains three semantic states:

```text
omitted
    -> no parent predicate

exact ObjectTemplate UUID
    -> only direct children of that stable parent

root selection
    -> only stable root lineages
```

M4 introduces no additional derived, recursive or search-oriented collection filter. In particular, the collection does not gain a current-version/admission filter such as:

```text
has_default
has_published_version
directly_instantiable
```

and does not gain ancestry/search carriers such as:

```text
ancestor_template_id
descendant_of
qualified-name prefix/contains
caller-defined generic sort/search DSL
```

A `qualified_name`-only filter does not replace the separate `namespace` and `name` carriers: the collection retains both stable dimensions independently.

## Strict request shape and lexical/omission/null semantics

### Request body and query multiplicity

The request body is forbidden.

```text
empty HTTP body
    -> valid

any non-empty body bytes, including
    {}
    null
    JSON or non-JSON payload
    whitespace-only payload
    -> 400 invalid_request
```

Unknown query parameters are rejected. Every retained query parameter has scalar cardinality and may occur at most once; repeated parameters are rejected even when every occurrence carries the same value.

```text
unknown query parameter
repeated query parameter
    -> 400 invalid_request
```

The adapter does not silently trim, lowercase, normalize or apply generic scalar coercion to repair caller input.

### `namespace`

```text
omitted
    -> no namespace predicate

supplied
    -> exact stable-namespace filter
    -> canonical namespace grammar:
       segment("." segment)*
       segment = [a-z][a-z0-9_]*
       maximum 64 characters per segment
       maximum 255 characters overall
```

Empty, explicit `null`, uppercase/non-canonical or otherwise malformed values are `400 invalid_request`. Matching is exact; the carrier does not express prefix, contains or case-insensitive search.

### `name`

```text
omitted
    -> no local-name predicate

supplied
    -> exact stable local-name filter
    -> [a-z][a-z0-9_]*
    -> maximum 64 characters
```

Empty, explicit `null`, uppercase/non-canonical or otherwise malformed values are `400 invalid_request`. Matching is exact and receives no trim or lowercase repair.

### `abstract`

```text
omitted
    -> no abstract predicate

abstract=true
    -> only abstract lineages

abstract=false
    -> only non-abstract lineages
```

Only exact lowercase lexical `true` and `false` are accepted. Empty, `null`, numeric, title-case, uppercase or other boolean-like spellings are `400 invalid_request`.

### `parent_template_id`

The semantic tri-state uses one carrier:

```text
omitted
    -> no parent predicate

parent_template_id=<UUID>
    -> only direct children of that stable parent lineage

parent_template_id=null
    -> only stable root lineages
```

The UUID form uses the shared public UUID carrier. Exact lowercase lexical `null` is the sole root sentinel. Empty, malformed UUID, `NULL`, `Null`, `none`, `root` or any other sentinel spelling is `400 invalid_request`.

Omission, exact-parent selection and root selection are distinct caller intents; no default or normalization collapses them.

### `limit`

```text
omitted
    -> 100

supplied
    -> positive decimal integer
    -> lexical grammar [1-9][0-9]*
    -> range 1..500
```

Empty, `null`, zero, sign-prefixed, leading-zero, decimal, exponent, boolean-like or out-of-range forms are `400 invalid_request`.

### `cursor`

```text
omitted
    -> first page

supplied
    -> opaque continuation token
```

`cursor` has no explicit-null semantics. Therefore `cursor=null` is a supplied token, not omission and not a first-page alias. Empty and other supplied values must satisfy the cursor codec; exact token structure, query binding and final `invalid_cursor` classification are owned by the pagination/cursor review block.

## Success status, response-body presence and Location

Every successful collection read returns:

```http
200 OK
Content-Type: application/json
```

The response body is always present and represents the requested page through one typed JSON page carrier.

An empty result is a normal represented page:

```text
zero matching items
    -> 200 OK
    -> page body present
    -> zero-item collection representation
    -> no error
```

The route does not use cardinality-dependent success shapes. In particular, an empty page does not produce `204 No Content` and a non-empty page does not use `206 Partial Content`; cursor pagination is not an HTTP byte-range protocol.

The response carries no `Location` header because the operation creates no resource and the requested collection URI is already known to the caller.

M4 therefore introduces no successful response variant based on:

```text
201 Created
202 Accepted
204 No Content
206 Partial Content
redirect
Content-Range
total-count header
Location
```

## Page envelope and collection-item DTO

The public page carrier is:

```text
ObjectTemplatePage
    items: ObjectTemplateSummary[]
    next_cursor: string | null
```

The collection item is the complete current stable-lineage header projection:

```text
ObjectTemplateSummary
    id: UUID
    namespace: string
    name: string
    description: string | null
    abstract: bool
    parent_template_id: UUID | null
    default_version: positive integer | null
```

Presence rules are fixed:

```text
items
    -> always present
    -> [] for a zero-item page

next_cursor
    -> always present
    -> string when another page is available
    -> null when no continuation is available

description
parent_template_id
default_version
    -> always present
    -> JSON null represents the corresponding genuine absent state
```

The nullable values mean:

```text
description = null
    -> no current description

parent_template_id = null
    -> stable root lineage

default_version = null
    -> no exact version currently selected as the lineage default
```

`default_version` remains a same-lineage exact-version selection policy. Its presence does not mean latest/highest version, direct Object creation eligibility or any independently re-certified lifecycle condition.

The collection deliberately does not add:

```text
qualified_name duplicated beside namespace + name
expanded parent reference
version status, count or list
effective schema
relationship capabilities
count or total_count
has_more
links / self / previous_cursor
```

`ObjectTemplateSummary` names the public role of the collection item. It does not require a distinct implementation class if the later lineage-detail review proves the exact same projection appropriate there.

## Collection membership, cardinality, filter composition and canonical ordering

Membership is the set of current `ObjectTemplate` lineage rows that satisfy every supplied membership filter. One current lineage may occur at most once.

All supplied filters compose conjunctively:

```text
membership =
    current ObjectTemplate lineage
    AND namespace predicate, when supplied
    AND name predicate, when supplied
    AND abstract predicate, when supplied
    AND direct-parent/root predicate, when supplied
```

No filter has precedence over another, cancels another filter or introduces implicit OR semantics.

Cardinality is:

```text
unfiltered or partially filtered collection
    -> 0..N distinct current lineages

one returned page
    -> 0..limit distinct items

name only
    -> 0..N lineages across different namespaces

namespace + name
    -> 0..1 lineage
       because (namespace, name) is unique
```

A syntactically valid filter combination with no matching lineage returns the normal represented empty page.

A well-formed `parent_template_id` UUID that does not identify a current lineage also returns an empty page:

```text
200 OK
items = []
next_cursor = null
```

The parent query value is a membership filter, not an implicit path-selected or referenced resource. Its absence therefore does not produce `404 resource_not_found` or `422 referenced_resource_not_found`, and the collection does not require a separate parent-existence read solely for diagnosis.

The canonical ordering is fixed:

```text
(namespace ASC, name ASC)
```

This pair is the complete ordering tuple because the qualified lineage identity `(namespace, name)` is unique. No additional `id` tie-breaker is required.

The collection does not use caller-selected sorting, UUID order, creation order, inheritance depth or hierarchical/preorder traversal. Mutable fields such as `description` and `default_version` do not participate in ordering.

## Keyset pagination, cursor position and semantic query binding

The collection uses opaque keyset pagination only.

```text
supported
    -> opaque continuation cursor

not supported
    -> offset
    -> page number
    -> caller-selected ordering
    -> public multi-page snapshot token
```

The cursor position is the complete canonical ordering tuple of the last item actually returned:

```text
(last_returned.namespace, last_returned.name)
```

Continuation uses the same ascending tuple order:

```text
(namespace, name) > cursor position
ORDER BY namespace ASC, name ASC
```

The cursor is never derived from an internal look-ahead row that is not returned to the caller.

Observable page behavior is:

```text
returned items
    -> 0..limit

another item exists after the returned page
within the page's authoritative statement snapshot
    -> next_cursor is an opaque string

no further item exists
    -> next_cursor = null

empty page
    -> next_cursor = null
```

A bounded look-ahead such as `limit + 1` is an allowed efficient realization, not a public protocol requirement.

### Cursor position is not a resource reference

The keyset position does not require the lineage that originally occupied that position to continue existing or matching the collection.

```text
page 1 ends at (namespace=N, name=X)
lineage N.X is then deleted
    -> cursor remains usable
    -> continuation still applies tuple > (N, X)
```

The route does not re-read or validate the previous last item merely to use the cursor. Deletion of that item therefore does not produce `404` or invalidate an otherwise compatible cursor.

### Semantic query identity

A cursor is valid only for the same semantic collection scope that produced it.

The cursor identity includes:

```text
route/capability
    -> GET /api/v1/core/object-templates

namespace
    -> omitted or exact canonical value

name
    -> omitted or exact canonical value

abstract
    -> omitted, true or false

parent selection
    -> omitted
    -> root-only
    -> exact parent UUID
```

The parent presence state is mandatory because:

```text
parent_template_id omitted
    !=
parent_template_id=null
```

although both may use a nullable internal value. The public contract requires an equivalent semantic presence discriminator but does not expose or freeze an implementation field name such as `parent_filter_set`.

Binding is semantic rather than based on raw query-string layout:

```text
query-parameter order
    -> irrelevant

accepted lexical representation of the same UUID
    -> same UUID identity

filter presence and canonical value
    -> relevant
```

The cursor identity excludes:

```text
limit
cursor token itself
description
default_version
other response-only fields that affect neither membership nor ordering
```

Therefore a caller may continue the same collection with a different valid `limit`.

### Incompatible cursor

A supplied cursor is `400 invalid_cursor` when it is malformed or cannot represent the same collection query, including:

```text
malformed token/envelope
unsupported cursor version
wrong route/capability
namespace mismatch
name mismatch
abstract mismatch
parent omitted/root/exact-UUID mismatch
incomplete position tuple
position with wrong cardinality or carrier types
```

The exact token encoding remains an implementation detail. This block fixes semantic compatibility, not the physical cursor envelope.

### Per-page snapshot and cross-page behavior

Each request observes one coherent authoritative statement snapshot for its own page. Separate page requests do not share a repeatable collection snapshot.

Without intervening membership changes, keyset traversal returns matching lineages once and in canonical order without cursor-induced omission or duplication.

With current-state mutations between requests:

```text
new lineage inserted after the cursor position
    -> may appear on a later page

new lineage inserted before or at the cursor position
    -> is not recovered by that continuation

lineage deleted before the next request
    -> does not appear

previous last lineage deleted
    -> compatible cursor remains usable
```

The cursor is a continuation token, not a domain identity, database offset, transaction snapshot, CDC token or frozen-catalog handle.

## Finite public failure catalogue and precedence

The finite public failure set is exactly:

```text
400 invalid_request
400 invalid_cursor
500 internal_error
```

The root collection has no path-selected resource and performs no mutation, dependency admission or semantic candidate validation. Therefore it has no normal:

```text
404 resource_not_found
409 state conflict
422 semantic_validation_failed
422 referenced_resource_not_found
```

A well-formed absent parent filter and any other valid filter combination with no matches remain successful empty pages.

Failure precedence is:

```text
1. static request validation
2. cursor validation against the canonical request scope
3. authoritative current collection read
4. bounded internal failure boundary
```

### 1. Static request validation

Malformed request carriers are rejected before cursor decoding or PostgreSQL business work:

```text
non-empty request body
unknown or repeated query parameter
malformed namespace
malformed name
invalid abstract carrier
parent_template_id neither UUID nor lowercase null
malformed or out-of-range limit
    -> 400 invalid_request
    -> zero PostgreSQL business statements
```

When a request contains both a static carrier error and a malformed or incompatible cursor, `invalid_request` takes precedence because the semantic request scope must first be valid and canonicalized.

### 2. Cursor validation

After static request validation, a malformed or scope-incompatible cursor returns:

```text
400 invalid_cursor
zero PostgreSQL business statements
```

This includes malformed token/envelope, unsupported version, wrong route, filter or parent-presence mismatch, and a position with incorrect cardinality or carrier types.

A compatible cursor whose former last item was deleted, no longer matches or lies beyond the current end is not invalid and does not trigger an existence read. It proceeds to the authoritative collection read and may yield an empty page.

### 3. Authoritative current collection read

A valid request and compatible cursor execute the current collection read. Zero matching rows, an absent well-formed parent UUID and a deleted prior cursor-position lineage are normal successful states represented by `200 OK`.

The read does not issue diagnostic follow-up work merely to distinguish empty-subcases or re-certify represented lineage/default semantics.

### 4. Internal failure boundary

Unexpected persistence/infrastructure failure or inability to decode a mandatory persisted carrier into the complete typed page projection returns:

```text
500 internal_error
```

The error response does not expose SQL, table/column names, constraints, driver details, stack traces or cursor internals.

A representable persisted semantic surprise remains readable. The GET does not replay mutation-owned lifecycle/default/inheritance certification merely because it projects current persisted state.

The canonical error envelope remains:

```json
{
  "code": "invalid_cursor",
  "message": "...",
  "details": {}
}
```

`code` is the stable branching carrier, `message` is not, and `details` remains a bounded JSON object. This route introduces no new mandatory error-detail payload.

## Public-contract closure checkpoint

The caller-visible contract of `GET /api/v1/core/object-templates` is closed for the current M4 review candidate:

```text
capability
    -> current ObjectTemplate lineage collection

request
    -> no path parameters
    -> exact filters: namespace, name, abstract, parent_template_id
    -> opaque cursor + limit
    -> no body

success
    -> 200 OK
    -> ObjectTemplatePage
    -> ordered ObjectTemplateSummary items
    -> represented empty page
    -> no Location

membership/order
    -> conjunctive filters
    -> parent omitted/root/exact direct-parent semantics
    -> (namespace ASC, name ASC)

pagination
    -> opaque keyset on (namespace, name)
    -> limit excluded from cursor identity
    -> one statement snapshot per page

failures
    -> invalid_request
    -> invalid_cursor
    -> internal_error
```

This is a WIP review closure only. It does not freeze the milestone contract or architecture and does not authorize implementation.

## Logical authoritative data path and cache authority boundary

After static request and cursor validation, every valid request executes exactly one authoritative PostgreSQL business statement over the current ObjectTemplate lineage relation.

The statement owns, in one bounded page operation:

```text
source
    -> current ObjectTemplate lineage rows

membership
    -> every supplied exact filter composed with AND

continuation
    -> (namespace, name) > cursor position, when supplied

ordering
    -> namespace ASC, name ASC

projection
    -> id
    -> namespace
    -> name
    -> description
    -> abstract
    -> parent_template_id
    -> default_version

page acquisition
    -> bounded work sufficient to return 0..limit items
       and determine whether a continuation exists
```

A bounded look-ahead such as `limit + 1` is an allowed realization, but the public and logical requirement is one authoritative business statement with work proportional to one page.

The page DTO and `next_cursor` are constructed entirely from that statement result. The route issues no second statement for total count, parent-filter existence, cursor-position existence, default-target validation, response enrichment or diagnostic classification.

The authoritative path does not require:

```text
ObjectTemplateVersion joins
property/component declaration joins
object_template_ancestry traversal
recursive exact-parent traversal
effective-schema loading
RelationshipDefinition or relationship_definition_space reads
mutation-semantic recertification
model-plane cache reads
N+1 follow-up queries
```

PostgreSQL remains authoritative for:

```text
current lineage existence
complete collection membership
current description
current default_version
filter evaluation
canonical ordered page
```

No worker-local cache may serve, complete or overrule the public response.

### Opportunistic stable-descriptor fill

The already-returned rows may opportunistically populate a worker-local stable descriptor facet:

```text
StableObjectTemplateDescriptor
    id
    namespace
    name
    abstract
    parent_template_id
```

This fill is optional and policy-gated. It may use only columns already returned by the authoritative statement and must add no PostgreSQL round trip or cache lookup required by the response.

```text
cache cold
cache partial
fill skipped by policy
entry rejected by capacity/eviction policy
    -> identical public response
    -> collection success unaffected
```

`description` and `default_version` are current mutable state and are not part of this stable descriptor facet.

A descriptor fill does not make any of the following READY:

```text
complete ObjectTemplate ancestry source set
exact ObjectTemplateVersion semantics
effective properties
effective components
linked DataTypeVersion semantics
compiled validators
```

The collection therefore performs no speculative ancestry/effective-schema load merely to warm another consumer.

### Candidate cost profile

```text
static invalid request
    -> 0 PostgreSQL business statements

invalid or incompatible cursor
    -> 0 PostgreSQL business statements

valid empty or non-empty page
    -> exactly 1 PostgreSQL business statement

required cache reads
    -> 0

additional DB work for cache fill
    -> 0

model/effective-schema work
    -> 0
```

## Persistence/query carrier and physical-index handoff

The persistence layer should build one dynamic `SELECT` over `object_templates`, adding only the predicates that are semantically present in the validated request:

```sql
SELECT
    id,
    namespace,
    name,
    description,
    abstract,
    parent_template_id,
    default_version
FROM object_templates
WHERE
    -- supplied exact membership predicates only
    -- plus tuple keyset continuation when a cursor is supplied
ORDER BY
    namespace ASC,
    name ASC
LIMIT :limit_plus_one;
```

The parent tri-state must compile directly into the corresponding SQL shape:

```text
parent omitted
    -> no parent predicate

root-only
    -> parent_template_id IS NULL

exact parent
    -> parent_template_id = :parent_template_id
```

The query builder must not encode optional filters through generic null-short-circuit expressions such as `(:value IS NULL OR column = :value)`. It should expose the actual active predicate set to PostgreSQL and use the tuple predicate:

```text
(namespace, name) > (:after_namespace, :after_name)
```

for continuation. `LIMIT limit + 1` is the recommended bounded realization for deriving `next_cursor` in the same statement. No `COUNT`, CTE, join or follow-up statement belongs to this route.

### Current index handoff

Retain the constraint-owned unique B-tree:

```text
UNIQUE (namespace, name)
```

It remains the primary access path for unfiltered and namespace-filtered traversal, exact qualified-name lookup, canonical ordering and generic keyset continuation.

Add these explicit B-tree access paths:

```text
ix_object_templates_name_namespace
    (name, namespace)

ix_object_templates_abstract_namespace_name
    (abstract, namespace, name)

ix_object_templates_parent_namespace_name
    (parent_template_id, namespace, name)
```

Their responsibilities are respectively:

```text
(name, namespace)
    -> name-only filtering with canonical traversal inside a constant name

(abstract, namespace, name)
    -> abstract-filtered canonical traversal

(parent_template_id, namespace, name)
    -> exact-parent and root-only canonical traversal
    -> reverse-parent access needed by lineage lifetime/delete checks
```

The composite parent index replaces the existing parent-only index:

```text
ix_object_templates_parent
    (parent_template_id)
```

because its leading column preserves the reverse-parent lookup while the suffix supports the collection's canonical order and keyset pagination.

Do not add `INCLUDE` columns. `description` and `default_version` are mutable and the complete public row still requires heap access; copying them into collection indexes would increase mutation maintenance without establishing a compelling covering-read benefit.

Do not create additional indexes on:

```text
description
default_version
id beyond the primary key
qualified_name as a derived duplicate
```

and do not proliferate indexes for every filter combination. The four access families above cover the primary collection shapes; remaining conjunctive filters may be applied as residual predicates over the best available stable-key access path.

### Architecture verification handoff

Architecture closing must validate representative cardinalities for:

```text
unfiltered
namespace-filtered
name-only
abstract-filtered
exact-parent
root-only
```

with and without a cursor, using planner and runtime evidence. It must preserve:

```text
one authoritative business statement
bounded limit+1 acquisition
canonical keyset order
no pathological explicit sort/materialization
no unjustified full projection scan
no duplicate/redundant index
```

The exact PostgreSQL plan is not part of the public contract. A later measured architecture adjustment may merge or replace an index only if it preserves equivalent access for the owned query families and records the evidence explicitly.

## Remaining technical review boundary

Still to review for this operation:

```text
read snapshot/concurrency realization
measurement-oriented cost validation and final operation closure
```

The next micro-point is the read snapshot/concurrency realization.
