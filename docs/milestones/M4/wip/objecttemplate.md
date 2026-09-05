# M4 WIP â€” ObjectTemplate model-plane review owner

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

## Reads â€” 6

```text
GET /api/v1/core/object-templates
GET /api/v1/core/object-templates/{template_id}
GET /api/v1/core/object-templates/{template_id}/versions
GET /api/v1/core/object-templates/{template_id}/versions/{version}
GET /api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema
GET /api/v1/core/object-templates/{template_id}/relationship-capabilities
```

## Mutations â€” 10

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

# 5. Reconstructed delivered semantic baseline â€” AS-IS reference only

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

# 7. Strong M4 candidates from source material â€” not yet ratified here

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

## Allocation and DRAFT-number reuse â€” superseded

```text
max(existing version) + 1
reuse deleted highest DRAFT number
```

are superseded by the shared monotonic/no-reuse allocator.

## Autonomous RelationshipResolution â€” superseded

Any blocker, relationship-capability DTO, filter, cursor or query plan based on:

```text
relationship_resolutions
resolution_id
mutable Resolution.name
```

must be replaced or removed.

## Public declaration `position` â€” open

Delivered ObjectTemplate authoring exposes explicit `position`; RelationshipDefinition M4 moved ordering to request-array order plus internal ordinal. ObjectTemplate must explicitly decide whether public property/component contracts retain position, use array order, or use another carrier. Uniformity is desirable only where semantics genuinely align.

## Historical `LIST -> SCALAR` prohibition â€” open

Delivered ObjectTemplate history permits only normal `SCALAR -> LIST`. M4 now separates exact-version validity from concrete Object migrability, and factual Object migration owns preserve-or-fail behavior. The ObjectTemplate rule must be revalidated deliberately rather than inherited or reversed by analogy.

## CREATE_NEXT clone strategy â€” open

The source note prefers DB-side cloning of immutable **local declarations**, partly because the runtime cache candidate is effective-schema oriented. RelationshipDefinition later preferred cache-snapshot cloning in application state. ObjectTemplate must compare local-declaration clone requirements, runtime-cache facet boundaries, source/current lifetime admission, referenced-target lifetime and bounded DML/payload cost. No strategy wins merely for cross-family uniformity.

## Effective-schema lifecycle and exact read routing â€” open

The strongest source direction materializes immutable effective schema only at PUBLISH and derives DRAFT effective schema from immutable parent plus local DRAFT declarations. Exact public GET and effective-schema GET contracts must be closed before the final read routing/materialization design is ratified.

## Mutation responses and response-only reloads â€” open

AS-IS mutations often return complete lineage/version state. M4's caller-first default favors `204` when no operation-owned result is needed and `201 + Location` for creation. Every ObjectTemplate operation must ratify its own response; no existing body survives automatically.

## Current lock plan â€” evidence, not TO-BE authority

Existing duplicate resolution passes, row locks, advisory gates and aggregate reloads may protect real safety predicates, but the current mechanism does not determine the M4 contract. The family review must first close semantics and required concurrent outcomes; global architecture later derives the smallest correct realization.

## DataType internal design â€” deliberately deferred

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

# 12. OT-GET-01 â€” LIST ObjectTemplate lineages

**State:** PUBLIC CONTRACT CLOSED / AUTHORITATIVE DATA PATH + CACHE BOUNDARY + PERSISTENCE/INDEX HANDOFF REVIE]€¼Q!9%0IY%\%8AI=IML€¼UII9P4Ğ9%Q((ŒŒ…Á…‰¥±¥Ñä…¹É•ÍÁ½¹Í¥‰¥±¥Ñä()4ĞÉ•Ñ…¥¹Ì„ÁÕ‰±¥Œ½±±•Ñ¥½¸…Á…‰¥±¥Ñä™½ÈÕÉÉ•¹Ğ=‰©•ÑQ•µÁ±…Ñ•€±¥¹•…•Ì¸()¸=‰©•ÑQ•µÁ±…Ñ•€¥ÌÑ¡”ÍÑ…‰±”±¥¹•…”¥‘•¹Ñ¥Ñäì•á…Ğ=‰©•ÑQ•µÁ±…Ñ•Y•ÉÍ¥½¹€É•Í½ÕÉ•ÌÉ•µ…¥¸‘¥ÍÑ¥¹ĞÍÕ‰½É‘¥¹…Ñ”É•Í½ÕÉ•Ì¸Q¡”½±±•Ñ¥½¸…¹Íİ•ÉÌè()Ñ•áĞ)İ¡¥ ÕÉÉ•¹Ğ=‰©•ÑQ•µÁ±…Ñ”±¥¹•…•Ì•á¥ÍĞ)…¹µ…Ñ Ñ¡”…±±•ÈÌ•áÁ±¥¥Ñ±äÍ•±•Ñ•½±±•Ñ¥½¸Í½Á”ü)€()5•µ‰•ÉÍ¡¥À¥Ì¹½Ğ¥µÁ±¥¥Ñ±äÉ•ÍÑÉ¥Ñ•Ñ¼è()Ñ•áĞ)…‰ÍÑÉ…Ğ€ôô™…±Í”)‘•™…Õ±Ñ}Ù•ÉÍ¥½¸ÁÉ•Í•¹Ğ)…Ğ±•…ÍĞ½¹”AU	1%M!•á…ĞÙ•ÉÍ¥½¸)‘¥É•Ğ=‰©•Ğ¹IQ•±¥¥‰¥±¥Ñä)€()‰ÍÑÉ…Ğ°‘•™…Õ±Ğµ±•ÍÌ½È½Ñ¡•Éİ¥Í”¹½¸µ‘¥É•Ñ±äµ¥¹ÍÑ…¹Ñ¥…‰±”±¥¹•…•ÌÉ•µ…¥¸Ù…±¥µ½‘•°µÁ±…¹”É•Í½ÕÉ•Ì™½È¥¹¡•É¥Ñ…¹”°½µÁ½¹•¹ĞÑ…É•ÑÌ…¹I•±…Ñ¥½¹Í¡¥À½µÁ…Ñ¥‰¥±¥Ñä¸()Q¡”½±±•Ñ¥½¸‘½•Ì¹½Ğ½İ¸è()Ñ•áĞ)•á…ĞµÙ•ÉÍ¥½¸±¥ÍÑ¥¹œ½È‘•Ñ…¥°)±½…°½È•™™•Ñ¥Ù”Í¡•µ„)ÁÉ½Á•ÉÑä½½µÁ½¹•¹Ğ‘•±…É…Ñ¥½¹Ì)É•±…Ñ¥½¹Í¡¥Àµ…Á…‰¥±¥ÑäÁÉ½©•Ñ¥½¸)=‰©•Ğ¹IQ…‘µ¥ÍÍ¥½¸)¡¥ÍÑ½É¥…°½‘•±•Ñ•±¥¹•…”‘¥Í½Ù•Éä)µÕÑ…Ñ¥½¸µÍ•µ…¹Ñ¥ŒÉ••ÉÑ¥™¥…Ñ¥½¸)€((ŒŒ5•Ñ¡½…¹É½ÕÑ”()¡ÑÑÀ)P€½…Á¤½ØÄ½½É”½½‰©•ĞµÑ•µÁ±…Ñ•Ì)€()Q€µ…Ñ¡•Ì„Í¥‘”µ•™™•Ğµ™É•”ÕÉÉ•¹Ğ½±±•Ñ¥½¸É•…¸Q¡”•á¥ÍÑ¥¹œ€½½‰©•ĞµÑ•µÁ±…Ñ•Í€¹½Õ¸É•µ…¥¹Ì½ÉÉ•Ğ‰•…ÕÍ”=‰©•ÑQ•µÁ±…Ñ•€…±É•…‘ä‘•¹½Ñ•ÌÑ¡”ÍÑ…‰±”±¥¹•…”ìÍÕ‰½É‘¥¹…Ñ”€½Ù•ÉÍ¥½¹Í€É½ÕÑ•Ì‘¥ÍÑ¥¹Õ¥Í •á…ĞÍ¹…ÁÍ¡½ÑÌ¸()4Ğ‘½•Ì¹½Ğ¥¹ÑÉ½‘Õ”°™½ÈÑ¡¥Ì¡•­Á½¥¹Ğè()Ñ•áĞ(½½‰©•ĞµÑ•µÁ±…Ñ”µ±¥¹•…•Ì(½½‰©•ĞµÑ•µÁ±…Ñ•Ì½±¥¹•…•Ì)„½µµ…¹µÍÑå±”½±±•Ñ¥½¸Í•…É É½ÕÑ”)É•µ½Ù…°½˜Ñ¡”½±±•Ñ¥½¸…Á…‰¥±¥Ñä)€((ŒŒA…Ñ …¹ÅÕ•Éä…ÉÉ¥•È¥¹Ù•¹Ñ½Éä()A…Ñ Á…É…µ•Ñ•ÉÌè()Ñ•áĞ)¹½¹”)€()Q¡”É•Ñ…¥¹•ÅÕ•ÉäµÁ…É…µ•Ñ•È¥¹Ù•¹Ñ½Éä¥Ì•á…Ñ±äè()Ñ•áĞ)¹…µ•ÍÁ…”)¹…µ”)…‰ÍÑÉ…Ğ)Á…É•¹Ñ}Ñ•µÁ±…Ñ•}¥)ÕÉÍ½È)±¥µ¥Ğ)€()Q¡•¥È…±±•Èµ™…¥¹œÉ•ÍÁ½¹Í¥‰¥±¥Ñ¥•Ì…É”è()Ñ•áĞ)¹…µ•ÍÁ…”(€€€€´ø½ÁÑ¥½¹…°•á…Ğ™¥±Ñ•È½¸Ñ¡”ÍÑ…‰±”±¥¹•…”¹…µ•ÍÁ…”()¹…µ”(€€€€´ø½ÁÑ¥½¹…°•á…Ğ™¥±Ñ•È½¸Ñ¡”ÍÑ…‰±”±½…°±¥¹•…”¹…µ”()…‰ÍÑÉ…Ğ(€€€€´ø½ÁÑ¥½¹…°•á…Ğ™¥±Ñ•È½¸Ñ¡”ÍÑ…‰±”…‰ÍÑÉ…Ğ™±…œ(€€€€´ø½µ¥ÍÍ¥½¸‘½•Ì¹½ĞÉ•ÍÑÉ¥Ğ½±±•Ñ¥½¸µ•µ‰•ÉÍ¡¥À()Á…É•¹Ñ}Ñ•µÁ±…Ñ•}¥(€€€€´ø½ÁÑ¥½¹…°™¥±Ñ•È½¸Ñ¡”ÍÑ…‰±”‘¥É•ĞµÁ…É•¹ĞÉ•±…Ñ¥½¹Í¡¥À½¹±ä(€€€€´ø¥Ğ‘½•Ì¹½Ğµ•…¸…É‰¥ÑÉ…Éä…¹•ÍÑ½È½È‘•Í•¹‘…¹ĞÍ•…É ()ÕÉÍ½È(€€€€´ø½ÁÑ¥½¹…°½Á…ÅÕ”½¹Ñ¥¹Õ…Ñ¥½¸…ÉÉ¥•È™½ÈÑ¡”Í…µ”½±±•Ñ¥½¸Í½Á”()±¥µ¥Ğ(€€€€´ø½ÁÑ¥½¹…°É•ÅÕ•ÍÑ•Á…”Í¥é”)€()Á…É•¹Ñ}Ñ•µÁ±…Ñ•}¥‘€É•Ñ…¥¹ÌÑ¡É•”Í•µ…¹Ñ¥ŒÍÑ…Ñ•Ìè()Ñ•áĞ)½µ¥ÑÑ•(€€€€´ø¹¼Á…É•¹ĞÁÉ•‘¥…Ñ”()•á…Ğ=‰©•ÑQ•µÁ±…Ñ”UU%(€€€€´ø½¹±ä‘¥É•Ğ¡¥±‘É•¸½˜Ñ¡…ĞÍÑ…‰±”Á…É•¹Ğ()É½½ĞÍ•±•Ñ¥½¸(€€€€´ø½¹±äÍÑ…‰±”É½½Ğ±¥¹•…•Ì)€()4Ğ¥¹ÑÉ½‘Õ•Ì¹¼…‘‘¥Ñ¥½¹…°‘•É¥Ù•°É•ÕÉÍ¥Ù”½ÈÍ•…É µ½É¥•¹Ñ•½±±•Ñ¥½¸™¥±Ñ•È¸%¸Á…ÉÑ¥Õ±…È°Ñ¡”½±±•Ñ¥½¸‘½•Ì¹½Ğ…¥¸„ÕÉÉ•¹ĞµÙ•ÉÍ¥½¸½…‘µ¥ÍÍ¥½¸™¥±Ñ•ÈÍÕ …Ìè()Ñ•áĞ)¡…Í}‘•™…Õ±Ğ)¡…Í}ÁÕ‰±¥Í¡•‘}Ù•ÉÍ¥½¸)‘¥É•Ñ±å}¥¹ÍÑ…¹Ñ¥…‰±”)€()…¹‘½•Ì¹½Ğ…¥¸…¹•ÍÑÉä½Í•…É …ÉÉ¥•ÉÌÍÕ …Ìè()Ñ•áĞ)…¹•ÍÑ½É}Ñ•µÁ±…Ñ•}¥)‘•Í•¹‘…¹Ñ}½˜)ÅÕ…±¥™¥•µ¹…µ”ÁÉ•™¥à½½¹Ñ…¥¹Ì)…±±•Èµ‘•™¥¹••¹•É¥ŒÍ½ÉĞ½Í•…É M0)€()ÅÕ…±¥™¥•‘}¹…µ•€µ½¹±ä™¥±Ñ•È‘½•Ì¹½ĞÉ•Á±…”Ñ¡”Í•Á…É…Ñ”¹…µ•ÍÁ…•€…¹¹…µ•€…ÉÉ¥•ÉÌèÑ¡”½±±•Ñ¥½¸É•Ñ…¥¹Ì‰½Ñ ÍÑ…‰±”‘¥µ•¹Í¥½¹Ì¥¹‘•Á•¹‘•¹Ñ±ä¸((ŒŒMÑÉ¥ĞÉ•ÅÕ•ÍĞÍ¡…Á”…¹±•á¥…°½½µ¥ÍÍ¥½¸½¹Õ±°Í•µ…¹Ñ¥Ì((ŒŒŒI•ÅÕ•ÍĞ‰½‘ä…¹ÅÕ•ÉäµÕ±Ñ¥Á±¥¥Ñä()Q¡”É•ÅÕ•ÍĞ‰½‘ä¥Ì™½É‰¥‘‘•¸¸()Ñ•áĞ)•µÁÑä!QQ@‰½‘ä(€€€€´øÙ…±¥()…¹ä¹½¸µ•µÁÑä‰½‘ä‰åÑ•Ì°¥¹±Õ‘¥¹œ(€€€íô(€€€¹Õ±°(€€€)M=8½È¹½¸µ)M=8Á…å±½…(€€€İ¡¥Ñ•ÍÁ…”µ½¹±äÁ…å±½…(€€€€´ø€ĞÀÀ¥¹Ù…±¥‘}É•ÅÕ•ÍĞ)€()U¹­¹½İ¸ÅÕ•ÉäÁ…É…µ•Ñ•ÉÌ…É”É•©•Ñ•¸Ù•ÉäÉ•Ñ…¥¹•ÅÕ•ÉäÁ…É…µ•Ñ•È¡…ÌÍ…±…È…É‘¥¹…±¥Ñä…¹µ…ä½ÕÈ…Ğµ½ÍĞ½¹”ìÉ•Á•…Ñ•Á…É…µ•Ñ•ÉÌ…É”É•©•Ñ••Ù•¸İ¡•¸•Ù•Éä½ÕÉÉ•¹”…ÉÉ¥•ÌÑ¡”Í…µ”Ù…±Õ”¸()Ñ•áĞ)Õ¹­¹½İ¸ÅÕ•ÉäÁ…É…µ•Ñ•È)É•Á•…Ñ•ÅÕ•ÉäÁ…É…µ•Ñ•È(€€€€´ø€ĞÀÀ¥¹Ù…±¥‘}É•ÅÕ•ÍĞ)€()Q¡”…‘…ÁÑ•È‘½•Ì¹½ĞÍ¥±•¹Ñ±äÑÉ¥´°±½İ•É…Í”°¹½Éµ…±¥é”½È…ÁÁ±ä•¹•É¥ŒÍ…±…È½•É¥½¸Ñ¼É•Á…¥È…±±•È¥¹ÁÕĞ¸((ŒŒŒ¹…µ•ÍÁ…•€()Ñ•áĞ)½µ¥ÑÑ•(€€€€´ø¹¼¹…µ•ÍÁ…”ÁÉ•‘¥…Ñ”()ÍÕÁÁ±¥•(€€€€´ø•á…ĞÍÑ…‰±”µ¹…µ•ÍÁ…”™¥±Ñ•È(€€€€´ø…¹½¹¥…°¹…µ•ÍÁ…”É…µµ…Èè(€€€€€€Í•µ•¹Ğ ˆ¸ˆÍ•µ•¹Ğ¤¨(€€€€€€Í•µ•¹Ğ€ôm„µéum„µèÀ´å}t¨(€€€€€€µ…á¥µÕ´€ØĞ¡…É…Ñ•ÉÌÁ•ÈÍ•µ•¹Ğ(€€€€€€µ…á¥µÕ´€ÈÔÔ¡…É…Ñ•ÉÌ½Ù•É…±°)€()µÁÑä°•áÁ±¥¥Ğ¹Õ±±€°ÕÁÁ•É…Í”½¹½¸µ…¹½¹¥…°½È½Ñ¡•Éİ¥Í”µ…±™½Éµ•Ù…±Õ•Ì…É”€ĞÀÀ¥¹Ù…±¥‘}É•ÅÕ•ÍÑ€¸5…Ñ¡¥¹œ¥Ì•á…ĞìÑ¡”…ÉÉ¥•È‘½•Ì¹½Ğ•áÁÉ•ÍÌÁÉ•™¥à°½¹Ñ…¥¹Ì½È…Í”µ¥¹Í•¹Í¥Ñ¥Ù”Í•…É ¸((ŒŒŒ¹…µ•€()Ñ•áĞ)½µ¥ÑÑ•(€€€€´ø¹¼±½…°µ¹…µ”ÁÉ•‘¥…Ñ”()ÍÕÁÁ±¥•(€€€€´ø•á…ĞÍÑ…‰±”±½…°µ¹…µ”™¥±Ñ•È(€€€€´øm„µéum„µèÀ´å}t¨(€€€€´øµ…á¥µÕ´€ØĞ¡…É…Ñ•ÉÌ)€()µÁÑä°•áÁ±¥¥Ğ¹Õ±±€°ÕÁÁ•É…Í”½¹½¸µ…¹½¹¥…°½È½Ñ¡•Éİ¥Í”µ…±™½Éµ•Ù…±Õ•Ì…É”€ĞÀÀ¥¹Ù…±¥‘}É•ÅÕ•ÍÑ€¸5…Ñ¡¥¹œ¥Ì•á…Ğ…¹É••¥Ù•Ì¹¼ÑÉ¥´½È±½İ•É…Í”É•Á…¥È¸((ŒŒŒ…‰ÍÑÉ…Ñ€()Ñ•áĞ)½µ¥ÑÑ•(€€€€´ø¹¼…‰ÍÑÉ…ĞÁÉ•‘¥…Ñ”()…‰ÍÑÉ…ĞõÑÉÕ”(€€€€´ø½¹±ä…‰ÍÑÉ…Ğ±¥¹•…•Ì()…‰ÍÑÉ…Ğõ™…±Í”(€€€€´ø½¹±ä¹½¸µ…‰ÍÑÉ…Ğ±¥¹•…•Ì)€()=¹±ä•á…Ğ±½İ•É…Í”±•á¥…°ÑÉÕ•€…¹™…±Í•€…É”…•ÁÑ•¸µÁÑä°¹Õ±±€°¹Õµ•É¥Œ°Ñ¥Ñ±”µ…Í”°ÕÁÁ•É…Í”½È½Ñ¡•È‰½½±•…¸µ±¥­”ÍÁ•±±¥¹Ì…É”€ĞÀÀ¥¹Ù…±¥‘}É•ÅÕ•ÍÑ€¸((ŒŒŒÁ…É•¹Ñ}Ñ•µÁ±…Ñ•}¥‘€()Q¡”Í•µ…¹Ñ¥ŒÑÉ¤µÍÑ…Ñ”ÕÍ•Ì½¹”…ÉÉ¥•Èè()Ñ•áĞ)½µ¥ÑÑ•(€€€€´ø¹¼Á…É•¹ĞÁÉ•‘¥…Ñ”()Á…É•¹Ñ}Ñ•µÁ±…Ñ•}¥ôñUU%ø(€€€€´ø½¹±ä‘¥É•Ğ¡¥±‘É•¸½˜Ñ¡…ĞÍÑ…‰±”Á…É•¹Ğ±¥¹•…”()Á…É•¹Ñ}Ñ•µÁ±…Ñ•}¥õ¹Õ±°(€€€€´ø½¹±äÍÑ…‰±”É½½Ğ±¥¹•…•Ì)€()Q¡”UU%™½É´ÕÍ•ÌÑ¡”Í¡…É•ÁÕ‰±¥ŒUU%…ÉÉ¥•È¸á…Ğ±½İ•É…Í”±•á¥…°¹Õ±±€¥ÌÑ¡”Í½±”É½½ĞÍ•¹Ñ¥¹•°¸µÁÑä°µ…±™½Éµ•UU%°9U11€°9Õ±±€°¹½¹•€°É½½Ñ€½È…¹ä½Ñ¡•ÈÍ•¹Ñ¥¹•°ÍÁ•±±¥¹œ¥Ì€ĞÀÀ¥¹Ù…±¥‘}É•ÅÕ•ÍÑ€¸()=µ¥ÍÍ¥½¸°•á…ĞµÁ…É•¹ĞÍ•±•Ñ¥½¸…¹É½½ĞÍ•±•Ñ¥½¸…É”‘¥ÍÑ¥¹Ğ…±±•È¥¹Ñ•¹ÑÌì¹¼‘•™…Õ±Ğ½È¹½Éµ…±¥é…Ñ¥½¸½±±…ÁÍ•ÌÑ¡•´¸((ŒŒŒ±¥µ¥Ñ€()Ñ•áĞ)½µ¥ÑÑ•(€€€€´ø€ÄÀÀ()ÍÕÁÁ±¥•(€€€€´øÁ½Í¥Ñ¥Ù”‘•¥µ…°¥¹Ñ••È(€€€€´ø±•á¥…°É…µµ…ÈlÄ´åulÀ´åt¨(€€€€´øÉ…¹”€Ä¸¸ÔÀÀ)€()µÁÑä°¹Õ±±€°é•É¼°Í¥¸µÁÉ•™¥á•°±•…‘¥¹œµé•É¼°‘•¥µ…°°•áÁ½¹•¹Ğ°‰½½±•…¸µ±¥­”½È½ÕĞµ½˜µÉ…¹”™½ÉµÌ…É”€ĞÀÀ¥¹Ù…±¥‘}É•ÅÕ•ÍÑ€¸((ŒŒŒÕÉÍ½É€()Ñ•áĞ)½µ¥ÑÑ•(€€€€´ø™¥ÉÍĞÁ…”()ÍÕÁÁ±¥•(€€€€´ø½Á…ÅÕ”½¹Ñ¥¹Õ…Ñ¥½¸Ñ½­•¸)€()ÕÉÍ½É€¡…Ì¹¼•áÁ±¥¥Ğµ¹Õ±°Í•µ…¹Ñ¥Ì¸Q¡•É•™½É”ÕÉÍ½Èõ¹Õ±±€¥Ì„ÍÕÁÁ±¥•Ñ½­•¸°¹½Ğ½µ¥ÍÍ¥½¸…¹¹½Ğ„™¥ÉÍĞµÁ…”…±¥…Ì¸µÁÑä…¹½Ñ¡•ÈÍÕÁÁ±¥•Ù…±Õ•ÌµÕÍĞÍ…Ñ¥Í™äÑ¡”ÕÉÍ½È½‘•Œì•á…ĞÑ½­•¸ÍÑÉÕÑÕÉ”°ÅÕ•Éä‰¥¹‘¥¹œ…¹™¥¹…°¥¹Ù…±¥‘}ÕÉÍ½É€±…ÍÍ¥™¥…Ñ¥½¸…É”½İ¹•‰äÑ¡”Á…¥¹…Ñ¥½¸½ÕÉÍ½ÈÉ•Ù¥•Ü‰±½¬¸((ŒŒMÕ•ÍÌÍÑ…ÑÕÌ°É•ÍÁ½¹Í”µ‰½‘äÁÉ•Í•¹”…¹1½…Ñ¥½¸()Ù•ÉäÍÕ•ÍÍ™Õ°½±±•Ñ¥½¸É•…É•ÑÕÉ¹Ìè()¡ÑÑÀ(ÈÀÀ=,)½¹Ñ•¹ĞµQåÁ”è…ÁÁ±¥…Ñ¥½¸½©Í½¸)€()Q¡”É•ÍÁ½¹Í”‰½‘ä¥Ì…±İ…åÌÁÉ•Í•¹Ğ…¹É•ÁÉ•Í•¹ÑÌÑ¡”É•ÅÕ•ÍÑ•Á…”Ñ¡É½Õ ½¹”ÑåÁ•)M=8Á…”…ÉÉ¥•È¸()¸•µÁÑäÉ•ÍÕ±Ğ¥Ì„¹½Éµ…°É•ÁÉ•Í•¹Ñ•Á…”è()Ñ•áĞ)é•É¼µ…Ñ¡¥¹œ¥Ñ•µÌ(€€€€´ø€ÈÀÀ=,(€€€€´øÁ…”‰½‘äÁÉ•Í•¹Ğ(€€€€´øé•É¼µ¥Ñ•´½±±•Ñ¥½¸É•ÁÉ•Í•¹Ñ…Ñ¥½¸(€€€€´ø¹¼•ÉÉ½È)€()Q¡”É½ÕÑ”‘½•Ì¹½ĞÕÍ”…É‘¥¹…±¥Ñäµ‘•Á•¹‘•¹ĞÍÕ•ÍÌÍ¡…Á•Ì¸%¸Á…ÉÑ¥Õ±…È°…¸•µÁÑäÁ…”‘½•Ì¹½ĞÁÉ½‘Õ”€ÈÀĞ9¼½¹Ñ•¹Ñ€…¹„¹½¸µ•µÁÑäÁ…”‘½•Ì¹½ĞÕÍ”€ÈÀØA…ÉÑ¥…°½¹Ñ•¹Ñ€ìÕÉÍ½ÈÁ…¥¹…Ñ¥½¸¥Ì¹½Ğ…¸!QQ@‰åÑ”µÉ…¹”ÁÉ½Ñ½½°¸()Q¡”É•ÍÁ½¹Í”…ÉÉ¥•Ì¹¼1½…Ñ¥½¹€¡•…‘•È‰•…ÕÍ”Ñ¡”½Á•É…Ñ¥½¸É•…Ñ•Ì¹¼É•Í½ÕÉ”…¹Ñ¡”É•ÅÕ•ÍÑ•½±±•Ñ¥½¸UI$¥Ì…±É•…‘ä­¹½İ¸Ñ¼Ñ¡”…±±•È¸()4ĞÑ¡•É•™½É”¥¹ÑÉ½‘Õ•Ì¹¼ÍÕ•ÍÍ™Õ°É•ÍÁ½¹Í”Ù…É¥…¹Ğ‰…Í•½¸è()Ñ•áĞ(ÈÀÄÉ•…Ñ•(ÈÀÈ•ÁÑ•(ÈÀĞ9¼½¹Ñ•¹Ğ(ÈÀØA…ÉÑ¥…°½¹Ñ•¹Ğ)É•‘¥É•Ğ)½¹Ñ•¹ĞµI…¹”)Ñ½Ñ…°µ½Õ¹Ğ¡•…‘•È)1½…Ñ¥½¸)€((ŒŒA…”•¹Ù•±½Á”…¹½±±•Ñ¥½¸µ¥Ñ•´Q<()Q¡”ÁÕ‰±¥ŒÁ…”…ÉÉ¥•È¥Ìè()Ñ•áĞ)=‰©•ÑQ•µÁ±…Ñ•A…”(€€€¥Ñ•µÌè=‰©•ÑQ•µÁ±…Ñ•MÕµµ…Éåmt(€€€¹•áÑ}ÕÉÍ½ÈèÍÑÉ¥¹œğ¹Õ±°)€()Q¡”½±±•Ñ¥½¸¥Ñ•´¥ÌÑ¡”½µÁ±•Ñ”ÕÉÉ•¹ĞÍÑ…‰±”µ±¥¹•…”¡•…‘•ÈÁÉ½©•Ñ¥½¸è()Ñ•áĞ)=‰©•ÑQ•µÁ±…Ñ•MÕµµ…Éä(€€€¥èUU%(€€€¹…µ•ÍÁ…”èÍÑÉ¥¹œ(€€€¹…µ”èÍÑÉ¥¹œ(€€€‘•ÍÉ¥ÁÑ¥½¸èÍÑÉ¥¹œğ¹Õ±°(€€€…‰ÍÑÉ…Ğè‰½½°(€€€Á…É•¹Ñ}Ñ•µÁ±…Ñ•}¥èUU%ğ¹Õ±°(€€€‘•™…Õ±Ñ}Ù•ÉÍ¥½¸èÁ½Í¥Ñ¥Ù”¥¹Ñ••Èğ¹Õ±°)€()AÉ•Í•¹”ÉÕ±•Ì…É”™¥á•è()Ñ•áĞ)¥Ñ•µÌ(€€€€´ø…±İ…åÌÁÉ•Í•¹Ğ(€€€€´ømt™½È„é•É¼µ¥Ñ•´Á…”()¹•áÑ}ÕÉÍ½È(€€€€´ø…±İ…åÌÁÉ•Í•¹Ğ(€€€€´øÍÑÉ¥¹œİ¡•¸…¹½Ñ¡•ÈÁ…”¥Ì…Ù…¥±…‰±”(€€€€´ø¹Õ±°İ¡•¸¹¼½¹Ñ¥¹Õ…Ñ¥½¸¥Ì…Ù…¥±…‰±”()‘•ÍÉ¥ÁÑ¥½¸)Á…É•¹Ñ}Ñ•µÁ±…Ñ•}¥)‘•™…Õ±Ñ}Ù•ÉÍ¥½¸(€€€€´ø…±İ…åÌÁÉ•Í•¹Ğ(€€€€´ø)M=8¹Õ±°É•ÁÉ•Í•¹ÑÌÑ¡”½ÉÉ•ÍÁ½¹‘¥¹œ•¹Õ¥¹”…‰Í•¹ĞÍÑ…Ñ”)€()Q¡”¹Õ±±…‰±”Ù…±Õ•Ìµ•…¸è()Ñ•áĞ)‘•ÍÉ¥ÁÑ¥½¸€ô¹Õ±°(€€€€´ø¹¼ÕÉÉ•¹Ğ‘•ÍÉ¥ÁÑ¥½¸()Á…É•¹Ñ}Ñ•µÁ±…Ñ•}¥€ô¹Õ±°(€€€€´øÍÑ…‰±”É½½Ğ±¥¹•…”()‘•™…Õ±Ñ}Ù•ÉÍ¥½¸€ô¹Õ±°(€€€€´ø¹¼•á…ĞÙ•ÉÍ¥½¸ÕÉÉ•¹Ñ±äÍ•±•Ñ•…ÌÑ¡”±¥¹•…”‘•™…Õ±Ğ)€()‘•™…Õ±Ñ}Ù•ÉÍ¥½¹€É•µ…¥¹Ì„Í…µ”µ±¥¹•…”•á…ĞµÙ•ÉÍ¥½¸Í•±•Ñ¥½¸Á½±¥ä¸%ÑÌÁÉ•Í•¹”‘½•Ì¹½Ğµ•…¸±…Ñ•ÍĞ½¡¥¡•ÍĞÙ•ÉÍ¥½¸°‘¥É•Ğ=‰©•ĞÉ•…Ñ¥½¸•±¥¥‰¥±¥Ñä½È…¹ä¥¹‘•Á•¹‘•¹Ñ±äÉ”µ•ÉÑ¥™¥•±¥™•å±”½¹‘¥Ñ¥½¸¸()Q¡”½±±•Ñ¥½¸‘•±¥‰•É…Ñ•±ä‘½•Ì¹½Ğ…‘è()Ñ•áĞ)ÅÕ…±¥™¥•‘}¹…µ”‘ÕÁ±¥…Ñ•‰•Í¥‘”¹…µ•ÍÁ…”€¬¹…µ”)•áÁ…¹‘•Á…É•¹ĞÉ•™•É•¹”)Ù•ÉÍ¥½¸ÍÑ…ÑÕÌ°½Õ¹Ğ½È±¥ÍĞ)•™™•Ñ¥Ù”Í¡•µ„)É•±…Ñ¥½¹Í¡¥À…Á…‰¥±¥Ñ¥•Ì)½Õ¹Ğ½ÈÑ½Ñ…±}½Õ¹Ğ)¡…Í}µ½É”)±¥¹­Ì€¼Í•±˜€¼ÁÉ•Ù¥½ÕÍ}ÕÉÍ½È)€()=‰©•ÑQ•µÁ±…Ñ•MÕµµ…Éå€¹…µ•ÌÑ¡”ÁÕ‰±¥ŒÉ½±”½˜Ñ¡”½±±•Ñ¥½¸¥Ñ•´¸%Ğ‘½•Ì¹½ĞÉ•ÅÕ¥É”„‘¥ÍÑ¥¹Ğ¥µÁ±•µ•¹Ñ…Ñ¥½¸±…ÍÌ¥˜Ñ¡”±…Ñ•È±¥¹•…”µ‘•Ñ…¥°É•Ù¥•ÜÁÉ½Ù•ÌÑ¡”•á…ĞÍ…µ”ÁÉ½©•Ñ¥½¸…ÁÁÉ½ÁÉ¥…Ñ”Ñ¡•É”¸((ŒŒ½±±•Ñ¥½¸µ•µ‰•ÉÍ¡¥À°…É‘¥¹…±¥Ñä°™¥±Ñ•È½µÁ½Í¥Ñ¥½¸…¹…¹½¹¥…°½É‘•É¥¹œ()5•µ‰•ÉÍ¡¥À¥ÌÑ¡”Í•Ğ½˜ÕÉÉ•¹Ğ=‰©•ÑQ•µÁ±…Ñ•€±¥¹•…”É½İÌÑ¡…ĞÍ…Ñ¥Í™ä•Ù•ÉäÍÕÁÁ±¥•µ•µ‰•ÉÍ¡¥À™¥±Ñ•È¸=¹”ÕÉÉ•¹Ğ±¥¹•…”µ…ä½ÕÈ…Ğµ½ÍĞ½¹”¸()±°ÍÕÁÁ±¥•™¥±Ñ•ÉÌ½µÁ½Í”½¹©Õ¹Ñ¥Ù•±äè()Ñ•áĞ)µ•µ‰•ÉÍ¡¥À€ô(€€€ÕÉÉ•¹Ğ=‰©•ÑQ•µÁ±…Ñ”±¥¹•…”(€€€9¹…µ•ÍÁ…”ÁÉ•‘¥…Ñ”°İ¡•¸ÍÕÁÁ±¥•(€€€9¹…µ”ÁÉ•‘¥…Ñ”°İ¡•¸ÍÕÁÁ±¥•(€€€9…‰ÍÑÉ…ĞÁÉ•‘¥…Ñ”°İ¡•¸ÍÕÁÁ±¥•(€€€9‘¥É•ĞµÁ…É•¹Ğ½É½½ĞÁÉ•‘¥…Ñ”°İ¡•¸ÍÕÁÁ±¥•)€()9¼™¥±Ñ•È¡…ÌÁÉ••‘•¹”½Ù•È…¹½Ñ¡•È°…¹•±Ì…¹½Ñ¡•È™¥±Ñ•È½È¥¹ÑÉ½‘Õ•Ì¥µÁ±¥¥Ğ=HÍ•µ…¹Ñ¥Ì¸()…É‘¥¹…±¥Ñä¥Ìè()Ñ•áĞ)Õ¹™¥±Ñ•É•½ÈÁ…ÉÑ¥…±±ä™¥±Ñ•É•½±±•Ñ¥½¸(€€€€´ø€À¸¹8‘¥ÍÑ¥¹ĞÕÉÉ•¹Ğ±¥¹•…•Ì()½¹”É•ÑÕÉ¹•Á…”(€€€€´ø€À¸¹±¥µ¥Ğ‘¥ÍÑ¥¹Ğ¥Ñ•µÌ()¹…µ”½¹±ä(€€€€´ø€À¸¹8±¥¹•…•Ì…É½ÍÌ‘¥™™•É•¹Ğ¹…µ•ÍÁ…•Ì()¹…µ•ÍÁ…”€¬¹…µ”(€€€€´ø€À¸¸Ä±¥¹•…”(€€€€€€‰•…ÕÍ”€¡¹…µ•ÍÁ…”°¹…µ”¤¥ÌÕ¹¥ÅÕ”)€()Íå¹Ñ…Ñ¥…±±äÙ…±¥™¥±Ñ•È½µ‰¥¹…Ñ¥½¸İ¥Ñ ¹¼µ…Ñ¡¥¹œ±¥¹•…”É•ÑÕÉ¹ÌÑ¡”¹½Éµ…°É•ÁÉ•Í•¹Ñ••µÁÑäÁ…”¸()İ•±°µ™½Éµ•Á…É•¹Ñ}Ñ•µÁ±…Ñ•}¥‘€UU%Ñ¡…Ğ‘½•Ì¹½Ğ¥‘•¹Ñ¥™ä„ÕÉÉ•¹Ğ±¥¹•…”…±Í¼É•ÑÕÉ¹Ì…¸•µÁÑäÁ…”è()Ñ•áĞ(ÈÀÀ=,)¥Ñ•µÌ€ômt)¹•áÑ}ÕÉÍ½È€ô¹Õ±°)€()Q¡”Á…É•¹ĞÅÕ•ÉäÙ…±Õ”¥Ì„µ•µ‰•ÉÍ¡¥À™¥±Ñ•È°¹½Ğ…¸¥µÁ±¥¥ĞÁ…Ñ µÍ•±•Ñ•½ÈÉ•™•É•¹•É•Í½ÕÉ”¸%ÑÌ…‰Í•¹”Ñ¡•É•™½É”‘½•Ì¹½ĞÁÉ½‘Õ”€ĞÀĞÉ•Í½ÕÉ•}¹½Ñ}™½Õ¹‘€½È€ĞÈÈÉ•™•É•¹•‘}É•Í½ÕÉ•}¹½Ñ}™½Õ¹‘€°…¹Ñ¡”½±±•Ñ¥½¸‘½•Ì¹½ĞÉ•ÅÕ¥É”„Í•Á…É…Ñ”Á…É•¹Ğµ•á¥ÍÑ•¹”É•…Í½±•±ä™½È‘¥…¹½Í¥Ì¸()Q¡”…¹½¹¥…°½É‘•É¥¹œ¥Ì™¥á•è()Ñ•áĞ(¡¹…µ•ÍÁ…”M°¹…µ”M¤)€()Q¡¥ÌÁ…¥È¥ÌÑ¡”½µÁ±•Ñ”½É‘•É¥¹œÑÕÁ±”‰•…ÕÍ”Ñ¡”ÅÕ…±¥™¥•±¥¹•…”¥‘•¹Ñ¥Ñä€¡¹…µ•ÍÁ…”°¹…µ”¥€¥ÌÕ¹¥ÅÕ”¸9¼…‘‘¥Ñ¥½¹…°¥‘€Ñ¥”µ‰É•…­•È¥ÌÉ•ÅÕ¥É•¸()Q¡”½±±•Ñ¥½¸‘½•Ì¹½ĞÕÍ”…±±•ÈµÍ•±•Ñ•Í½ÉÑ¥¹œ°UU%½É‘•È°É•…Ñ¥½¸½É‘•È°¥¹¡•É¥Ñ…¹”‘•ÁÑ ½È¡¥•É…É¡¥…°½ÁÉ•½É‘•ÈÑÉ…Ù•ÉÍ…°¸5ÕÑ…‰±”™¥•±‘ÌÍÕ …Ì‘•ÍÉ¥ÁÑ¥½¹€…¹‘•™…Õ±Ñ}Ù•ÉÍ¥½¹€‘¼¹½ĞÁ…ÉÑ¥¥Á…Ñ”¥¸½É‘•É¥¹œ¸((ŒŒ-•åÍ•ĞÁ…¥¹…Ñ¥½¸°ÕÉÍ½ÈÁ½Í¥Ñ¥½¸…¹Í•µ…¹Ñ¥ŒÅÕ•Éä‰¥¹‘¥¹œ()Q¡”½±±•Ñ¥½¸ÕÍ•Ì½Á…ÅÕ”­•åÍ•ĞÁ…¥¹…Ñ¥½¸½¹±ä¸()Ñ•áĞ)ÍÕÁÁ½ÉÑ•(€€€€´ø½Á…ÅÕ”½¹Ñ¥¹Õ…Ñ¥½¸ÕÉÍ½È()¹½ĞÍÕÁÁ½ÉÑ•(€€€€´ø½™™Í•Ğ(€€€€´øÁ…”¹Õµ‰•È(€€€€´ø…±±•ÈµÍ•±•Ñ•½É‘•É¥¹œ(€€€€´øÁÕ‰±¥ŒµÕ±Ñ¤µÁ…”Í¹…ÁÍ¡½ĞÑ½­•¸)€()Q¡”ÕÉÍ½ÈÁ½Í¥Ñ¥½¸¥ÌÑ¡”½µÁ±•Ñ”…¹½¹¥…°½É‘•É¥¹œÑÕÁ±”½˜Ñ¡”±…ÍĞ¥Ñ•´…ÑÕ…±±äÉ•ÑÕÉ¹•è()Ñ•áĞ(¡±…ÍÑ}É•ÑÕÉ¹•¹¹…µ•ÍÁ…”°±…ÍÑ}É•ÑÕÉ¹•¹¹…µ”¤)€()½¹Ñ¥¹Õ…Ñ¥½¸ÕÍ•ÌÑ¡”Í…µ”…Í•¹‘¥¹œÑÕÁ±”½É‘•Èè()Ñ•áĞ(¡¹…µ•ÍÁ…”°¹…µ”¤€øÕÉÍ½ÈÁ½Í¥Ñ¥½¸)=IH	d¹…µ•ÍÁ…”M°¹…µ”M)€()Q¡”ÕÉÍ½È¥Ì¹•Ù•È‘•É¥Ù•™É½´…¸¥¹Ñ•É¹…°±½½¬µ…¡•…É½ÜÑ¡…Ğ¥Ì¹½ĞÉ•ÑÕÉ¹•Ñ¼Ñ¡”…±±•È¸()=‰Í•ÉÙ…‰±”Á…”‰•¡…Ù¥½È¥Ìè()Ñ•áĞ)É•ÑÕÉ¹•¥Ñ•µÌ(€€€€´ø€À¸¹±¥µ¥Ğ()…¹½Ñ¡•È¥Ñ•´•á¥ÍÑÌ…™Ñ•ÈÑ¡”É•ÑÕÉ¹•Á…”)İ¥Ñ¡¥¸Ñ¡”Á…”Ì…ÕÑ¡½É¥Ñ…Ñ¥Ù”ÍÑ…Ñ•µ•¹ĞÍ¹…ÁÍ¡½Ğ(€€€€´ø¹•áÑ}ÕÉÍ½È¥Ì…¸½Á…ÅÕ”ÍÑÉ¥¹œ()¹¼™ÕÉÑ¡•È¥Ñ•´•á¥ÍÑÌ(€€€€´ø¹•áÑ}ÕÉÍ½È€ô¹Õ±°()•µÁÑäÁ…”(€€€€´ø¹•áÑ}ÕÉÍ½È€ô¹Õ±°)€()‰½Õ¹‘•±½½¬µ…¡•…ÍÕ …Ì±¥µ¥Ğ€¬€Å€¥Ì…¸…±±½İ••™™¥¥•¹ĞÉ•…±¥é…Ñ¥½¸°¹½Ğ„ÁÕ‰±¥ŒÁÉ½Ñ½½°É•ÅÕ¥É•µ•¹Ğ¸((ŒŒŒÕÉÍ½ÈÁ½Í¥Ñ¥½¸¥Ì¹½Ğ„É•Í½ÕÉ”É•™•É•¹”()Q¡”­•åÍ•ĞÁ½Í¥Ñ¥½¸‘½•Ì¹½ĞÉ•ÅÕ¥É”Ñ¡”±¥¹•…”Ñ¡…Ğ½É¥¥¹…±±ä½ÕÁ¥•Ñ¡…ĞÁ½Í¥Ñ¥½¸Ñ¼½¹Ñ¥¹Õ”•á¥ÍÑ¥¹œ½Èµ…Ñ¡¥¹œÑ¡”½±±•Ñ¥½¸¸()Ñ•áĞ)Á…”€Ä•¹‘Ì…Ğ€¡¹…µ•ÍÁ…”õ8°¹…µ”õ`¤)±¥¹•…”8¹`¥ÌÑ¡•¸‘•±•Ñ•(€€€€´øÕÉÍ½ÈÉ•µ…¥¹ÌÕÍ…‰±”(€€€€´ø½¹Ñ¥¹Õ…Ñ¥½¸ÍÑ¥±°…ÁÁ±¥•ÌÑÕÁ±”€ø€¡8°`¤)€()Q¡”É½ÕÑ”‘½•Ì¹½ĞÉ”µÉ•…½ÈÙ…±¥‘…Ñ”Ñ¡”ÁÉ•Ù¥½ÕÌ±…ÍĞ¥Ñ•´µ•É•±äÑ¼ÕÍ”Ñ¡”ÕÉÍ½È¸•±•Ñ¥½¸½˜Ñ¡…Ğ¥Ñ•´Ñ¡•É•™½É”‘½•Ì¹½ĞÁÉ½‘Õ”€ĞÀÑ€½È¥¹Ù…±¥‘…Ñ”…¸½Ñ¡•Éİ¥Í”½µÁ…Ñ¥‰±”ÕÉÍ½È¸((ŒŒŒM•µ…¹Ñ¥ŒÅÕ•Éä¥‘•¹Ñ¥Ñä()ÕÉÍ½È¥ÌÙ…±¥½¹±ä™½ÈÑ¡”Í…µ”Í•µ…¹Ñ¥Œ½±±•Ñ¥½¸Í½Á”Ñ¡…ĞÁÉ½‘Õ•¥Ğ¸()Q¡”ÕÉÍ½È¥‘•¹Ñ¥Ñä¥¹±Õ‘•Ìè()Ñ•áĞ)É½ÕÑ”½…Á…‰¥±¥Ñä(€€€€´øP€½…Á¤½ØÄ½½É”½½‰©•ĞµÑ•µÁ±…Ñ•Ì()¹…µ•ÍÁ…”(€€€€´ø½µ¥ÑÑ•½È•á…Ğ…¹½¹¥…°Ù…±Õ”()¹…µ”(€€€€´ø½µ¥ÑÑ•½È•á…Ğ…¹½¹¥…°Ù…±Õ”()…‰ÍÑÉ…Ğ(€€€€´ø½µ¥ÑÑ•°ÑÉÕ”½È™…±Í”()Á…É•¹ĞÍ•±•Ñ¥½¸(€€€€´ø½µ¥ÑÑ•(€€€€´øÉ½½Ğµ½¹±ä(€€€€´ø•á…ĞÁ…É•¹ĞUU%)€()Q¡”Á…É•¹ĞÁÉ•Í•¹”ÍÑ…Ñ”¥Ìµ…¹‘…Ñ½Éä‰•…ÕÍ”è()Ñ•áĞ)Á…É•¹Ñ}Ñ•µÁ±…Ñ•}¥½µ¥ÑÑ•(€€€€„ô)Á…É•¹Ñ}Ñ•µÁ±…Ñ•}¥õ¹Õ±°)€()…±Ñ¡½Õ ‰½Ñ µ…äÕÍ”„¹Õ±±…‰±”¥¹Ñ•É¹…°Ù…±Õ”¸Q¡”ÁÕ‰±¥Œ½¹ÑÉ…ĞÉ•ÅÕ¥É•Ì…¸•ÅÕ¥Ù…±•¹ĞÍ•µ…¹Ñ¥ŒÁÉ•Í•¹”‘¥ÍÉ¥µ¥¹…Ñ½È‰ÕĞ‘½•Ì¹½Ğ•áÁ½Í”½È™É••é”…¸¥µÁ±•µ•¹Ñ…Ñ¥½¸™¥•±¹…µ”ÍÕ …ÌÁ…É•¹Ñ}™¥±Ñ•É}Í•Ñ€¸()	¥¹‘¥¹œ¥ÌÍ•µ…¹Ñ¥ŒÉ…Ñ¡•ÈÑ¡…¸‰…Í•½¸É…ÜÅÕ•ÉäµÍÑÉ¥¹œ±…å½ÕĞè()Ñ•áĞ)ÅÕ•ÉäµÁ…É…µ•Ñ•È½É‘•È(€€€€´ø¥ÉÉ•±•Ù…¹Ğ()…•ÁÑ•±•á¥…°É•ÁÉ•Í•¹Ñ…Ñ¥½¸½˜Ñ¡”Í…µ”UU%(€€€€´øÍ…µ”UU%¥‘•¹Ñ¥Ñä()™¥±Ñ•ÈÁÉ•Í•¹”…¹…¹½¹¥…°Ù…±Õ”(€€€€´øÉ•±•Ù…¹Ğ)€()Q¡”ÕÉÍ½È¥‘•¹Ñ¥Ñä•á±Õ‘•Ìè()Ñ•áĞ)±¥µ¥Ğ)ÕÉÍ½ÈÑ½­•¸¥ÑÍ•±˜)‘•ÍÉ¥ÁÑ¥½¸)‘•™…Õ±Ñ}Ù•ÉÍ¥½¸)½Ñ¡•ÈÉ•ÍÁ½¹Í”µ½¹±ä™¥•±‘ÌÑ¡…Ğ…™™•Ğ¹•¥Ñ¡•Èµ•µ‰•ÉÍ¡¥À¹½È½É‘•É¥¹œ)€()Q¡•É•™½É”„…±±•Èµ…ä½¹Ñ¥¹Õ”Ñ¡”Í…µ”½±±•Ñ¥½¸İ¥Ñ „‘¥™™•É•¹ĞÙ…±¥±¥µ¥Ñ€¸((ŒŒŒ%¹½µÁ…Ñ¥‰±”ÕÉÍ½È()ÍÕÁÁ±¥•ÕÉÍ½È¥Ì€ĞÀÀ¥¹Ù…±¥‘}ÕÉÍ½É€İ¡•¸¥Ğ¥Ìµ…±™½Éµ•½È…¹¹½ĞÉ•ÁÉ•Í•¹ĞÑ¡”Í…µ”½±±•Ñ¥½¸ÅÕ•Éä°¥¹±Õ‘¥¹œè()Ñ•áĞ)µ…±™½Éµ•Ñ½­•¸½•¹Ù•±½Á”)Õ¹ÍÕÁÁ½ÉÑ•ÕÉÍ½ÈÙ•ÉÍ¥½¸)İÉ½¹œÉ½ÕÑ”½…Á…‰¥±¥Ñä)¹…µ•ÍÁ…”µ¥Íµ…Ñ )¹…µ”µ¥Íµ…Ñ )…‰ÍÑÉ…Ğµ¥Íµ…Ñ )Á…É•¹Ğ½µ¥ÑÑ•½É½½Ğ½•á…ĞµUU%µ¥Íµ…Ñ )¥¹½µÁ±•Ñ”Á½Í¥Ñ¥½¸ÑÕÁ±”)Á½Í¥Ñ¥½¸İ¥Ñ İÉ½¹œ…É‘¥¹…±¥Ñä½È…ÉÉ¥•ÈÑåÁ•Ì)€()Q¡”•á…ĞÑ½­•¸•¹½‘¥¹œÉ•µ…¥¹Ì…¸¥µÁ±•µ•¹Ñ…Ñ¥½¸‘•Ñ…¥°¸Q¡¥Ì‰±½¬™¥á•ÌÍ•µ…¹Ñ¥Œ½µÁ…Ñ¥‰¥±¥Ñä°¹½ĞÑ¡”Á¡åÍ¥…°ÕÉÍ½È•¹Ù•±½Á”¸((ŒŒŒA•ÈµÁ…”Í¹…ÁÍ¡½Ğ…¹É½ÍÌµÁ…”‰•¡…Ù¥½È()… É•ÅÕ•ÍĞ½‰Í•ÉÙ•Ì½¹”½¡•É•¹Ğ…ÕÑ¡½É¥Ñ…Ñ¥Ù”ÍÑ…Ñ•µ•¹ĞÍ¹…ÁÍ¡½Ğ™½È¥ÑÌ½İ¸Á…”¸M•Á…É…Ñ”Á…”É•ÅÕ•ÍÑÌ‘¼¹½ĞÍ¡…É”„É•Á•…Ñ…‰±”½±±•Ñ¥½¸Í¹…ÁÍ¡½Ğ¸()]¥Ñ¡½ÕĞ¥¹Ñ•ÉÙ•¹¥¹œµ•µ‰•ÉÍ¡¥À¡…¹•Ì°­•åÍ•ĞÑÉ…Ù•ÉÍ…°É•ÑÕÉ¹Ìµ…Ñ¡¥¹œ±¥¹•…•Ì½¹”…¹¥¸…¹½¹¥…°½É‘•Èİ¥Ñ¡½ÕĞÕÉÍ½Èµ¥¹‘Õ•½µ¥ÍÍ¥½¸½È‘ÕÁ±¥…Ñ¥½¸¸()]¥Ñ ÕÉÉ•¹ĞµÍÑ…Ñ”µÕÑ…Ñ¥½¹Ì‰•Ñİ••¸É•ÅÕ•ÍÑÌè()Ñ•áĞ)¹•Ü±¥¹•…”¥¹Í•ÉÑ•…™Ñ•ÈÑ¡”ÕÉÍ½ÈÁ½Í¥Ñ¥½¸(€€€€´øµ…ä…ÁÁ•…È½¸„±…Ñ•ÈÁ…”()¹•Ü±¥¹•…”¥¹Í•ÉÑ•‰•™½É”½È…ĞÑ¡”ÕÉÍ½ÈÁ½Í¥Ñ¥½¸(€€€€´ø¥Ì¹½ĞÉ•½Ù•É•‰äÑ¡…Ğ½¹Ñ¥¹Õ…Ñ¥½¸()±¥¹•…”‘•±•Ñ•‰•™½É”Ñ¡”¹•áĞÉ•ÅÕ•ÍĞ(€€€€´ø‘½•Ì¹½Ğ…ÁÁ•…È()ÁÉ•Ù¥½ÕÌ±…ÍĞ±¥¹•…”‘•±•Ñ•(€€€€´ø½µÁ…Ñ¥‰±”ÕÉÍ½ÈÉ•µ…¥¹ÌÕÍ…‰±”)€()Q¡”ÕÉÍ½È¥Ì„½¹Ñ¥¹Õ…Ñ¥½¸Ñ½­•¸°¹½Ğ„‘½µ…¥¸¥‘•¹Ñ¥Ñä°‘…Ñ…‰…Í”½™™Í•Ğ°ÑÉ…¹Í…Ñ¥½¸Í¹…ÁÍ¡½Ğ°Ñ½­•¸½È™É½é•¸µ…Ñ…±½œ¡…¹‘±”¸((ŒŒ¥¹¥Ñ”ÁÕ‰±¥Œ™…¥±ÕÉ”…Ñ…±½Õ”…¹ÁÉ••‘•¹”()Q¡”™¥¹¥Ñ”ÁÕ‰±¥Œ™…¥±ÕÉ”Í•Ğ¥Ì•á…Ñ±äè()Ñ•áĞ(ĞÀÀ¥¹Ù…±¥‘}É•ÅÕ•ÍĞ(ĞÀÀ¥¹Ù…±¥‘}ÕÉÍ½È(ÔÀÀ¥¹Ñ•É¹…±}•ÉÉ½È)€()Q¡”É½½Ğ½±±•Ñ¥½¸¡…Ì¹¼Á…Ñ µÍ•±•Ñ•É•Í½ÕÉ”…¹Á•É™½ÉµÌ¹¼µÕÑ…Ñ¥½¸°‘•Á•¹‘•¹ä…‘µ¥ÍÍ¥½¸½ÈÍ•µ…¹Ñ¥Œ…¹‘¥‘…Ñ”Ù…±¥‘…Ñ¥½¸¸Q¡•É•™½É”¥Ğ¡…Ì¹¼¹½Éµ…°è()Ñ•áĞ(ĞÀĞÉ•Í½ÕÉ•}¹½Ñ}™½Õ¹(ĞÀäÍÑ…Ñ”½¹™±¥Ğ(ĞÈÈÍ•µ…¹Ñ¥}Ù…±¥‘…Ñ¥½¹}™…¥±•(ĞÈÈÉ•™•É•¹•‘}É•Í½ÕÉ•}¹½Ñ}™½Õ¹)€()İ•±°µ™½Éµ•…‰Í•¹ĞÁ…É•¹Ğ™¥±Ñ•È…¹…¹ä½Ñ¡•ÈÙ…±¥™¥±Ñ•È½µ‰¥¹…Ñ¥½¸İ¥Ñ ¹¼µ…Ñ¡•ÌÉ•µ…¥¸ÍÕ•ÍÍ™Õ°•µÁÑäÁ…•Ì¸()…¥±ÕÉ”ÁÉ••‘•¹”¥Ìè()Ñ•áĞ(Ä¸ÍÑ…Ñ¥ŒÉ•ÅÕ•ÍĞÙ…±¥‘…Ñ¥½¸(È¸ÕÉÍ½ÈÙ…±¥‘…Ñ¥½¸……¥¹ÍĞÑ¡”…¹½¹¥…°É•ÅÕ•ÍĞÍ½Á”(Ì¸…ÕÑ¡½É¥Ñ…Ñ¥Ù”ÕÉÉ•¹Ğ½±±•Ñ¥½¸É•…(Ğ¸‰½Õ¹‘•¥¹Ñ•É¹…°™…¥±ÕÉ”‰½Õ¹‘…Éä)€((ŒŒŒ€Ä¸MÑ…Ñ¥ŒÉ•ÅÕ•ÍĞÙ…±¥‘…Ñ¥½¸()5…±™½Éµ•É•ÅÕ•ÍĞ…ÉÉ¥•ÉÌ…É”É•©•Ñ•‰•™½É”ÕÉÍ½È‘•½‘¥¹œ½ÈA½ÍÑÉ•ME0‰ÕÍ¥¹•ÍÌİ½É¬è()Ñ•áĞ)¹½¸µ•µÁÑäÉ•ÅÕ•ÍĞ‰½‘ä)Õ¹­¹½İ¸½ÈÉ•Á•…Ñ•ÅÕ•ÉäÁ…É…µ•Ñ•È)µ…±™½Éµ•¹…µ•ÍÁ…”)µ…±™½Éµ•¹…µ”)¥¹Ù…±¥…‰ÍÑÉ…Ğ…ÉÉ¥•È)Á…É•¹Ñ}Ñ•µÁ±…Ñ•}¥¹•¥Ñ¡•ÈUU%¹½È±½İ•É…Í”¹Õ±°)µ…±™½Éµ•½È½ÕĞµ½˜µÉ…¹”±¥µ¥Ğ(€€€€´ø€ĞÀÀ¥¹Ù…±¥‘}É•ÅÕ•ÍĞ(€€€€´øé•É¼A½ÍÑÉ•ME0‰ÕÍ¥¹•ÍÌÍÑ…Ñ•µ•¹ÑÌ)€()]¡•¸„É•ÅÕ•ÍĞ½¹Ñ…¥¹Ì‰½Ñ „ÍÑ…Ñ¥Œ…ÉÉ¥•È•ÉÉ½È…¹„µ…±™½Éµ•½È¥¹½µÁ…Ñ¥‰±”ÕÉÍ½È°¥¹Ù…±¥‘}É•ÅÕ•ÍÑ€Ñ…­•ÌÁÉ••‘•¹”‰•…ÕÍ”Ñ¡”Í•µ…¹Ñ¥ŒÉ•ÅÕ•ÍĞÍ½Á”µÕÍĞ™¥ÉÍĞ‰”Ù…±¥…¹…¹½¹¥…±¥é•¸((ŒŒŒ€È¸ÕÉÍ½ÈÙ…±¥‘…Ñ¥½¸()™Ñ•ÈÍÑ…Ñ¥ŒÉ•ÅÕ•ÍĞÙ…±¥‘…Ñ¥½¸°„µ…±™½Éµ•½ÈÍ½Á”µ¥¹½µÁ…Ñ¥‰±”ÕÉÍ½ÈÉ•ÑÕÉ¹Ìè()Ñ•áĞ(ĞÀÀ¥¹Ù…±¥‘}ÕÉÍ½È)é•É¼A½ÍÑÉ•ME0‰ÕÍ¥¹•ÍÌÍÑ…Ñ•µ•¹ÑÌ)€()Q¡¥Ì¥¹±Õ‘•Ìµ…±™½Éµ•Ñ½­•¸½•¹Ù•±½Á”°Õ¹ÍÕÁÁ½ÉÑ•Ù•ÉÍ¥½¸°İÉ½¹œÉ½ÕÑ”°™¥±Ñ•È½ÈÁ…É•¹ĞµÁÉ•Í•¹”µ¥Íµ…Ñ °…¹„Á½Í¥Ñ¥½¸İ¥Ñ ¥¹½ÉÉ•Ğ…É‘¥¹…±¥Ñä½È…ÉÉ¥•ÈÑåÁ•Ì¸()½µÁ…Ñ¥‰±”ÕÉÍ½Èİ¡½Í”™½Éµ•È±…ÍĞ¥Ñ•´İ…Ì‘•±•Ñ•°¹¼±½¹•Èµ…Ñ¡•Ì½È±¥•Ì‰•å½¹Ñ¡”ÕÉÉ•¹Ğ•¹¥Ì¹½Ğ¥¹Ù…±¥…¹‘½•Ì¹½ĞÑÉ¥•È…¸•á¥ÍÑ•¹”É•…¸%ĞÁÉ½••‘ÌÑ¼Ñ¡”…ÕÑ¡½É¥Ñ…Ñ¥Ù”½±±•Ñ¥½¸É•……¹µ…äå¥•±…¸•µÁÑäÁ…”¸((ŒŒŒ€Ì¸ÕÑ¡½É¥Ñ…Ñ¥Ù”ÕÉÉ•¹Ğ½±±•Ñ¥½¸É•…()Ù…±¥É•ÅÕ•ÍĞ…¹½µÁ…Ñ¥‰±”ÕÉÍ½È•á•ÕÑ”Ñ¡”ÕÉÉ•¹Ğ½±±•Ñ¥½¸É•…¸i•É¼µ…Ñ¡¥¹œÉ½İÌ°…¸…‰Í•¹Ğİ•±°µ™½Éµ•Á…É•¹ĞUU%…¹„‘•±•Ñ•ÁÉ¥½ÈÕÉÍ½ÈµÁ½Í¥Ñ¥½¸±¥¹•…”…É”¹½Éµ…°ÍÕ•ÍÍ™Õ°ÍÑ…Ñ•ÌÉ•ÁÉ•Í•¹Ñ•‰ä€ÈÀÀ=-€¸()Q¡”É•…‘½•Ì¹½Ğ¥ÍÍÕ”‘¥…¹½ÍÑ¥Œ™½±±½ÜµÕÀİ½É¬µ•É•±äÑ¼‘¥ÍÑ¥¹Õ¥Í •µÁÑäµÍÕ‰…Í•Ì½ÈÉ”µ•ÉÑ¥™äÉ•ÁÉ•Í•¹Ñ•±¥¹•…”½‘•™…Õ±ĞÍ•µ…¹Ñ¥Ì¸((ŒŒŒ€Ğ¸%¹Ñ•É¹…°™…¥±ÕÉ”‰½Õ¹‘…Éä()U¹•áÁ•Ñ•Á•ÉÍ¥ÍÑ•¹”½¥¹™É…ÍÑÉÕÑÕÉ”™…¥±ÕÉ”½È¥¹…‰¥±¥ÑäÑ¼‘•½‘”„µ…¹‘…Ñ½ÉäÁ•ÉÍ¥ÍÑ•…ÉÉ¥•È¥¹Ñ¼Ñ¡”½µÁ±•Ñ”ÑåÁ•Á…”ÁÉ½©•Ñ¥½¸É•ÑÕÉ¹Ìè()Ñ•áĞ(ÔÀÀ¥¹Ñ•É¹…±}•ÉÉ½È)€()Q¡”•ÉÉ½ÈÉ•ÍÁ½¹Í”‘½•Ì¹½Ğ•áÁ½Í”ME0°Ñ…‰±”½½±Õµ¸¹…µ•Ì°½¹ÍÑÉ…¥¹ÑÌ°‘É¥Ù•È‘•Ñ…¥±Ì°ÍÑ…¬ÑÉ…•Ì½ÈÕÉÍ½È¥¹Ñ•É¹…±Ì¸()É•ÁÉ•Í•¹Ñ…‰±”Á•ÉÍ¥ÍÑ•Í•µ…¹Ñ¥ŒÍÕÉÁÉ¥Í”É•µ…¥¹ÌÉ•…‘…‰±”¸Q¡”P‘½•Ì¹½ĞÉ•Á±…äµÕÑ…Ñ¥½¸µ½İ¹•±¥™•å±”½‘•™…Õ±Ğ½¥¹¡•É¥Ñ…¹”•ÉÑ¥™¥…Ñ¥½¸µ•É•±ä‰•…ÕÍ”¥ĞÁÉ½©•ÑÌÕÉÉ•¹ĞÁ•ÉÍ¥ÍÑ•ÍÑ…Ñ”¸()Q¡”…¹½¹¥…°•ÉÉ½È•¹Ù•±½Á”É•µ…¥¹Ìè()©Í½¸)ì(€€‰½‘”ˆè€‰¥¹Ù…±¥‘}ÕÉÍ½Èˆ°(€€‰µ•ÍÍ…”ˆè€ˆ¸¸¸ˆ°(€€‰‘•Ñ…¥±Ìˆèíô)ô)€()½‘•€¥ÌÑ¡”ÍÑ…‰±”‰É…¹¡¥¹œ…ÉÉ¥•È°µ•ÍÍ…•€¥Ì¹½Ğ°…¹‘•Ñ…¥±Í€É•µ…¥¹Ì„‰½Õ¹‘•)M=8½‰©•Ğ¸Q¡¥ÌÉ½ÕÑ”¥¹ÑÉ½‘Õ•Ì¹¼¹•Üµ…¹‘…Ñ½Éä•ÉÉ½Èµ‘•Ñ…¥°Á…å±½…¸((ŒŒAÕ‰±¥Œµ½¹ÑÉ…Ğ±½ÍÕÉ”¡•­Á½¥¹Ğ()Q¡”…±±•ÈµÙ¥Í¥‰±”½¹ÑÉ…Ğ½˜P€½…Á¤½ØÄ½½É”½½‰©•ĞµÑ•µÁ±…Ñ•Í€¥Ì±½Í•™½ÈÑ¡”ÕÉÉ•¹Ğ4ĞÉ•Ù¥•Ü…¹‘¥‘…Ñ”è()Ñ•áĞ)…Á…‰¥±¥Ñä(€€€€´øÕÉÉ•¹Ğ=‰©•ÑQ•µÁ±…Ñ”±¥¹•…”½±±•Ñ¥½¸()É•ÅÕ•ÍĞ(€€€€´ø¹¼Á…Ñ Á…É…µ•Ñ•ÉÌ(€€€€´ø•á…Ğ™¥±Ñ•ÉÌè¹…µ•ÍÁ…”°¹…µ”°…‰ÍÑÉ…Ğ°Á…É•¹Ñ}Ñ•µÁ±…Ñ•}¥(€€€€´ø½Á…ÅÕ”ÕÉÍ½È€¬±¥µ¥Ğ(€€€€´ø¹¼‰½‘ä()ÍÕ•ÍÌ(€€€€´ø€ÈÀÀ=,(€€€€´ø=‰©•ÑQ•µÁ±…Ñ•A…”(€€€€´ø½É‘•É•=‰©•ÑQ•µÁ±…Ñ•MÕµµ…Éä¥Ñ•µÌ(€€€€´øÉ•ÁÉ•Í•¹Ñ••µÁÑäÁ…”(€€€€´ø¹¼1½…Ñ¥½¸()µ•µ‰•ÉÍ¡¥À½½É‘•È(€€€€´ø½¹©Õ¹Ñ¥Ù”™¥±Ñ•ÉÌ(€€€€´øÁ…É•¹Ğ½µ¥ÑÑ•½É½½Ğ½•á…Ğ‘¥É•ĞµÁ…É•¹ĞÍ•µ…¹Ñ¥Ì(€€€€´ø€¡¹…µ•ÍÁ…”M°¹…µ”M¤()Á…¥¹…Ñ¥½¸(€€€€´ø½Á…ÅÕ”­•åÍ•Ğ½¸€¡¹…µ•ÍÁ…”°¹…µ”¤(€€€€´ø±¥µ¥Ğ•á±Õ‘•™É½´ÕÉÍ½È¥‘•¹Ñ¥Ñä(€€€€´ø½¹”ÍÑ…Ñ•µ•¹ĞÍ¹…ÁÍ¡½ĞÁ•ÈÁ…”()™…¥±ÕÉ•Ì(€€€€´ø¥¹Ù…±¥‘}É•ÅÕ•ÍĞ(€€€€´ø¥¹Ù…±¥‘}ÕÉÍ½È(€€€€´ø¥¹Ñ•É¹…±}•ÉÉ½È)€()Q¡¥Ì¥Ì„]%@É•Ù¥•Ü±½ÍÕÉ”½¹±ä¸%Ğ‘½•Ì¹½Ğ™É••é”Ñ¡”µ¥±•ÍÑ½¹”½¹ÑÉ…Ğ½È…É¡¥Ñ•ÑÕÉ”…¹‘½•Ì¹½Ğ…ÕÑ¡½É¥é”¥µÁ±•µ•¹Ñ…Ñ¥½¸¸((ŒŒ1½¥…°…ÕÑ¡½É¥Ñ…Ñ¥Ù”‘…Ñ„Á…Ñ …¹…¡”…ÕÑ¡½É¥Ñä‰½Õ¹‘…Éä()™Ñ•ÈÍÑ…Ñ¥ŒÉ•ÅÕ•ÍĞ…¹ÕÉÍ½ÈÙ…±¥‘…Ñ¥½¸°•Ù•ÉäÙ…±¥É•ÅÕ•ÍĞ•á•ÕÑ•Ì•á…Ñ±ä½¹”…ÕÑ¡½É¥Ñ…Ñ¥Ù”A½ÍÑÉ•ME0‰ÕÍ¥¹•ÍÌÍÑ…Ñ•µ•¹Ğ½Ù•ÈÑ¡”ÕÉÉ•¹Ğ=‰©•ÑQ•µÁ±…Ñ”±¥¹•…”É•±…Ñ¥½¸¸()Q¡”ÍÑ…Ñ•µ•¹Ğ½İ¹Ì°¥¸½¹”‰½Õ¹‘•Á…”½Á•É…Ñ¥½¸è()Ñ•áĞ)Í½ÕÉ”(€€€€´øÕÉÉ•¹Ğ=‰©•ÑQ•µÁ±…Ñ”±¥¹•…”É½İÌ()µ•µ‰•ÉÍ¡¥À(€€€€´ø•Ù•ÉäÍÕÁÁ±¥••á…Ğ™¥±Ñ•È½µÁ½Í•İ¥Ñ 9()½¹Ñ¥¹Õ…Ñ¥½¸(€€€€´ø€¡¹…µ•ÍÁ…”°¹…µ”¤€øÕÉÍ½ÈÁ½Í¥Ñ¥½¸°İ¡•¸ÍÕÁÁ±¥•()½É‘•É¥¹œ(€€€€´ø¹…µ•ÍÁ…”M°¹…µ”M()ÁÉ½©•Ñ¥½¸(€€€€´ø¥(€€€€´ø¹…µ•ÍÁ…”(€€€€´ø¹…µ”(€€€€´ø‘•ÍÉ¥ÁÑ¥½¸(€€€€´ø…‰ÍÑÉ…Ğ(€€€€´øÁ…É•¹Ñ}Ñ•µÁ±…Ñ•}¥(€€€€´ø‘•™…Õ±Ñ}Ù•ÉÍ¥½¸()Á…”…ÅÕ¥Í¥Ñ¥½¸(€€€€´ø‰½Õ¹‘•İ½É¬ÍÕ™™¥¥•¹ĞÑ¼É•ÑÕÉ¸€À¸¹±¥µ¥Ğ¥Ñ•µÌ(€€€€€€…¹‘•Ñ•Éµ¥¹”İ¡•Ñ¡•È„½¹Ñ¥¹Õ…Ñ¥½¸•á¥ÍÑÌ)€()‰½Õ¹‘•±½½¬µ…¡•…ÍÕ …Ì±¥µ¥Ğ€¬€Å€¥Ì…¸…±±½İ•É•…±¥é…Ñ¥½¸°‰ÕĞÑ¡”ÁÕ‰±¥Œ…¹±½¥…°É•ÅÕ¥É•µ•¹Ğ¥Ì½¹”…ÕÑ¡½É¥Ñ…Ñ¥Ù”‰ÕÍ¥¹•ÍÌÍÑ…Ñ•µ•¹Ğİ¥Ñ İ½É¬ÁÉ½Á½ÉÑ¥½¹…°Ñ¼½¹”Á…”¸()Q¡”Á…”Q<…¹¹•áÑ}ÕÉÍ½É€…É”½¹ÍÑÉÕÑ••¹Ñ¥É•±ä™É½´Ñ¡…ĞÍÑ…Ñ•µ•¹ĞÉ•ÍÕ±Ğ¸Q¡”É½ÕÑ”¥ÍÍÕ•Ì¹¼Í•½¹ÍÑ…Ñ•µ•¹Ğ™½ÈÑ½Ñ…°½Õ¹Ğ°Á…É•¹Ğµ™¥±Ñ•È•á¥ÍÑ•¹”°ÕÉÍ½ÈµÁ½Í¥Ñ¥½¸•á¥ÍÑ•¹”°‘•™…Õ±ĞµÑ…É•ĞÙ…±¥‘…Ñ¥½¸°É•ÍÁ½¹Í”•¹É¥¡µ•¹Ğ½È‘¥…¹½ÍÑ¥Œ±…ÍÍ¥™¥…Ñ¥½¸¸()Q¡”…ÕÑ¡½É¥Ñ…Ñ¥Ù”Á…Ñ ‘½•Ì¹½ĞÉ•ÅÕ¥É”è()Ñ•áĞ)=‰©•ÑQ•µÁ±…Ñ•Y•ÉÍ¥½¸©½¥¹Ì)ÁÉ½Á•ÉÑä½½µÁ½¹•¹Ğ‘•±…É…Ñ¥½¸©½¥¹Ì)½‰©•Ñ}Ñ•µÁ±…Ñ•}…¹•ÍÑÉäÑÉ…Ù•ÉÍ…°)É•ÕÉÍ¥Ù”•á…ĞµÁ…É•¹ĞÑÉ…Ù•ÉÍ…°)•™™•Ñ¥Ù”µÍ¡•µ„±½…‘¥¹œ)I•±…Ñ¥½¹Í¡¥Á•™¥¹¥Ñ¥½¸½ÈÉ•±…Ñ¥½¹Í¡¥Á}‘•™¥¹¥Ñ¥½¹}ÍÁ…”É•…‘Ì)µÕÑ…Ñ¥½¸µÍ•µ…¹Ñ¥ŒÉ••ÉÑ¥™¥…Ñ¥½¸)µ½‘•°µÁ±…¹”…¡”É•…‘Ì)8¬Ä™½±±½ÜµÕÀÅÕ•É¥•Ì)€()A½ÍÑÉ•ME0É•µ…¥¹Ì…ÕÑ¡½É¥Ñ…Ñ¥Ù”™½Èè()Ñ•áĞ)ÕÉÉ•¹Ğ±¥¹•…”•á¥ÍÑ•¹”)½µÁ±•Ñ”½±±•Ñ¥½¸µ•µ‰•ÉÍ¡¥À)ÕÉÉ•¹Ğ‘•ÍÉ¥ÁÑ¥½¸)ÕÉÉ•¹Ğ‘•™…Õ±Ñ}Ù•ÉÍ¥½¸)™¥±Ñ•È•Ù…±Õ…Ñ¥½¸)…¹½¹¥…°½É‘•É•Á…”)€()9¼İ½É­•Èµ±½…°…¡”µ…äÍ•ÉÙ”°½µÁ±•Ñ”½È½Ù•ÉÉÕ±”Ñ¡”ÁÕ‰±¥ŒÉ•ÍÁ½¹Í”¸((ŒŒŒ=ÁÁ½ÉÑÕ¹¥ÍÑ¥ŒÍÑ…‰±”µ‘•ÍÉ¥ÁÑ½È™¥±°()Q¡”…±É•…‘äµÉ•ÑÕÉ¹•É½İÌµ…ä½ÁÁ½ÉÑÕ¹¥ÍÑ¥…±±äÁ½ÁÕ±…Ñ”„İ½É­•Èµ±½…°ÍÑ…‰±”‘•ÍÉ¥ÁÑ½È™…•Ğè()Ñ•áĞ)MÑ…‰±•=‰©•ÑQ•µÁ±…Ñ••ÍÉ¥ÁÑ½È(€€€¥(€€€¹…µ•ÍÁ…”(€€€¹…µ”(€€€…‰ÍÑÉ…Ğ(€€€Á…É•¹Ñ}Ñ•µÁ±…Ñ•}¥)€()Q¡¥Ì™¥±°¥Ì½ÁÑ¥½¹…°…¹Á½±¥äµ…Ñ•¸%Ğµ…äÕÍ”½¹±ä½±Õµ¹Ì…±É•…‘äÉ•ÑÕÉ¹•‰äÑ¡”…ÕÑ¡½É¥Ñ…Ñ¥Ù”ÍÑ…Ñ•µ•¹Ğ…¹µÕÍĞ…‘¹¼A½ÍÑÉ•ME0É½Õ¹ÑÉ¥À½È…¡”±½½­ÕÀÉ•ÅÕ¥É•‰äÑ¡”É•ÍÁ½¹Í”¸()Ñ•áĞ)…¡”½±)…¡”Á…ÉÑ¥…°)™¥±°Í­¥ÁÁ•‰äÁ½±¥ä)•¹ÑÉäÉ•©•Ñ•‰ä…Á…¥Ñä½•Ù¥Ñ¥½¸Á½±¥ä(€€€€´ø¥‘•¹Ñ¥…°ÁÕ‰±¥ŒÉ•ÍÁ½¹Í”(€€€€´ø½±±•Ñ¥½¸ÍÕ•ÍÌÕ¹…™™•Ñ•)€()‘•ÍÉ¥ÁÑ¥½¹€…¹‘•™…Õ±Ñ}Ù•ÉÍ¥½¹€…É”ÕÉÉ•¹ĞµÕÑ…‰±”ÍÑ…Ñ”…¹…É”¹½ĞÁ…ÉĞ½˜Ñ¡¥ÌÍÑ…‰±”‘•ÍÉ¥ÁÑ½È™…•Ğ¸()‘•ÍÉ¥ÁÑ½È™¥±°‘½•Ì¹½Ğµ…­”…¹ä½˜Ñ¡”™½±±½İ¥¹œIdè()Ñ•áĞ)½µÁ±•Ñ”=‰©•ÑQ•µÁ±…Ñ”…¹•ÍÑÉäÍ½ÕÉ”Í•Ğ)•á…Ğ=‰©•ÑQ•µÁ±…Ñ•Y•ÉÍ¥½¸Í•µ…¹Ñ¥Ì)•™™•Ñ¥Ù”ÁÉ½Á•ÉÑ¥•Ì)•™™•Ñ¥Ù”½µÁ½¹•¹ÑÌ)±¥¹­•…Ñ…QåÁ•Y•ÉÍ¥½¸Í•µ…¹Ñ¥Ì)½µÁ¥±•Ù…±¥‘…Ñ½ÉÌ)€()Q¡”½±±•Ñ¥½¸Ñ¡•É•™½É”Á•É™½ÉµÌ¹¼ÍÁ•Õ±…Ñ¥Ù”…¹•ÍÑÉä½•™™•Ñ¥Ù”µÍ¡•µ„±½…µ•É•±äÑ¼İ…É´…¹½Ñ¡•È½¹ÍÕµ•È¸((ŒŒŒ…¹‘¥‘…Ñ”½ÍĞÁÉ½™¥±”()Ñ•áĞ)ÍÑ…Ñ¥Œ¥¹Ù…±¥É•ÅÕ•ÍĞ(€€€€´ø€ÀA½ÍÑÉ•ME0‰ÕÍ¥¹•ÍÌÍÑ…Ñ•µ•¹ÑÌ()¥¹Ù…±¥½È¥¹½µÁ…Ñ¥‰±”ÕÉÍ½È(€€€€´ø€ÀA½ÍÑÉ•ME0‰ÕÍ¥¹•ÍÌÍÑ…Ñ•µ•¹ÑÌ()Ù…±¥•µÁÑä½È¹½¸µ•µÁÑäÁ…”(€€€€´ø•á…Ñ±ä€ÄA½ÍÑÉ•ME0‰ÕÍ¥¹•ÍÌÍÑ…Ñ•µ•¹Ğ()É•ÅÕ¥É•…¡”É•…‘Ì(€€€€´ø€À()…‘‘¥Ñ¥½¹…°İ½É¬™½È…¡”™¥±°(€€€€´ø€À()µ½‘•°½•™™•Ñ¥Ù”µÍ¡•µ„İ½É¬(€€€€´ø€À)€((ŒŒA•ÉÍ¥ÍÑ•¹”½ÅÕ•Éä…ÉÉ¥•È…¹Á¡åÍ¥…°µ¥¹‘•à¡…¹‘½™˜()Q¡”Á•ÉÍ¥ÍÑ•¹”±…å•ÈÍ¡½Õ±‰Õ¥±½¹”‘å¹…µ¥ŒM1Q€½Ù•È½‰©•Ñ}Ñ•µÁ±…Ñ•Í€°…‘‘¥¹œ½¹±äÑ¡”ÁÉ•‘¥…Ñ•ÌÑ¡…Ğ…É”Í•µ…¹Ñ¥…±±äÁÉ•Í•¹Ğ¥¸Ñ¡”Ù…±¥‘…Ñ•É•ÅÕ•ÍĞè()ÍÅ°)M1P(€€€¥°(€€€¹…µ•ÍÁ…”°(€€€¹…µ”°(€€€‘•ÍÉ¥ÁÑ¥½¸°(€€€…‰ÍÑÉ…Ğ°(€€€Á…É•¹Ñ}Ñ•µÁ±…Ñ•}¥°(€€€‘•™…Õ±Ñ}Ù•ÉÍ¥½¸)I=4½‰©•Ñ}Ñ•µÁ±…Ñ•Ì)]!I(€€€€´´ÍÕÁÁ±¥••á…Ğµ•µ‰•ÉÍ¡¥ÀÁÉ•‘¥…Ñ•Ì½¹±ä(€€€€´´Á±ÕÌÑÕÁ±”­•åÍ•Ğ½¹Ñ¥¹Õ…Ñ¥½¸İ¡•¸„ÕÉÍ½È¥ÌÍÕÁÁ±¥•)=IH	d(€€€¹…µ•ÍÁ…”M°(€€€¹…µ”M)1%5%P€é±¥µ¥Ñ}Á±ÕÍ}½¹”ì)€()Q¡”Á…É•¹ĞÑÉ¤µÍÑ…Ñ”µÕÍĞ½µÁ¥±”‘¥É•Ñ±ä¥¹Ñ¼Ñ¡”½ÉÉ•ÍÁ½¹‘¥¹œME0Í¡…Á”è()Ñ•áĞ)Á…É•¹Ğ½µ¥ÑÑ•(€€€€´ø¹¼Á…É•¹ĞÁÉ•‘¥…Ñ”()É½½Ğµ½¹±ä(€€€€´øÁ…É•¹Ñ}Ñ•µÁ±…Ñ•}¥%L9U10()•á…ĞÁ…É•¹Ğ(€€€€´øÁ…É•¹Ñ}Ñ•µÁ±…Ñ•}¥€ô€éÁ…É•¹Ñ}Ñ•µÁ±…Ñ•}¥)€()Q¡”ÅÕ•Éä‰Õ¥±‘•ÈµÕÍĞ¹½Ğ•¹½‘”½ÁÑ¥½¹…°™¥±Ñ•ÉÌÑ¡É½Õ •¹•É¥Œ¹Õ±°µÍ¡½ÉĞµ¥ÉÕ¥Ğ•áÁÉ•ÍÍ¥½¹ÌÍÕ …Ì€ éÙ…±Õ”%L9U10=H½±Õµ¸€ô€éÙ…±Õ”¥€¸%ĞÍ¡½Õ±•áÁ½Í”Ñ¡”…ÑÕ…°…Ñ¥Ù”ÁÉ•‘¥…Ñ”Í•ĞÑ¼A½ÍÑÉ•ME0…¹ÕÍ”Ñ¡”ÑÕÁ±”ÁÉ•‘¥…Ñ”è()Ñ•áĞ(¡¹…µ•ÍÁ…”°¹…µ”¤€ø€ é…™Ñ•É}¹…µ•ÍÁ…”°€é…™Ñ•É}¹…µ”¤)€()™½È½¹Ñ¥¹Õ…Ñ¥½¸¸1%5%P±¥µ¥Ğ€¬€Å€¥ÌÑ¡”É•½µµ•¹‘•‰½Õ¹‘•É•…±¥é…Ñ¥½¸™½È‘•É¥Ù¥¹œ¹•áÑ}ÕÉÍ½É€¥¸Ñ¡”Í…µ”ÍÑ…Ñ•µ•¹Ğ¸9¼=U9Q€°Q°©½¥¸½È™½±±½ÜµÕÀÍÑ…Ñ•µ•¹Ğ‰•±½¹ÌÑ¼Ñ¡¥ÌÉ½ÕÑ”¸((ŒŒŒÕÉÉ•¹Ğ¥¹‘•à¡…¹‘½™˜()I•Ñ…¥¸Ñ¡”½¹ÍÑÉ…¥¹Ğµ½İ¹•Õ¹¥ÅÕ”µÑÉ•”è()Ñ•áĞ)U9%EU€¡¹…µ•ÍÁ…”°¹…µ”¤)€()%ĞÉ•µ…¥¹ÌÑ¡”ÁÉ¥µ…Éä…•ÍÌÁ…Ñ ™½ÈÕ¹™¥±Ñ•É•…¹¹…µ•ÍÁ…”µ™¥±Ñ•É•ÑÉ…Ù•ÉÍ…°°•á…ĞÅÕ…±¥™¥•µ¹…µ”±½½­ÕÀ°…¹½¹¥…°½É‘•É¥¹œ…¹•¹•É¥Œ­•åÍ•Ğ½¹Ñ¥¹Õ…Ñ¥½¸¸()‘Ñ¡•Í”•áÁ±¥¥ĞµÑÉ•”…•ÍÌÁ…Ñ¡Ìè()Ñ•áĞ)¥á}½‰©•Ñ}Ñ•µÁ±…Ñ•Í}¹…µ•}¹…µ•ÍÁ…”(€€€€¡¹…µ”°¹…µ•ÍÁ…”¤()¥á}½‰©•Ñ}Ñ•µÁ±…Ñ•Í}…‰ÍÑÉ…Ñ}¹…µ•ÍÁ…•}¹…µ”(€€€€¡…‰ÍÑÉ…Ğ°¹…µ•ÍÁ…”°¹…µ”¤()¥á}½‰©•Ñ}Ñ•µÁ±…Ñ•Í}Á…É•¹Ñ}¹…µ•ÍÁ…•}¹…µ”(€€€€¡Á…É•¹Ñ}Ñ•µÁ±…Ñ•}¥°¹…µ•ÍÁ…”°¹…µ”¤)€()Q¡•¥ÈÉ•ÍÁ½¹Í¥‰¥±¥Ñ¥•Ì…É”É•ÍÁ•Ñ¥Ù•±äè()Ñ•áĞ(¡¹…µ”°¹…µ•ÍÁ…”¤(€€€€´ø¹…µ”µ½¹±ä™¥±Ñ•É¥¹œİ¥Ñ …¹½¹¥…°ÑÉ…Ù•ÉÍ…°¥¹Í¥‘”„½¹ÍÑ…¹Ğ¹…µ”((¡…‰ÍÑÉ…Ğ°¹…µ•ÍÁ…”°¹…µ”¤(€€€€´ø…‰ÍÑÉ…Ğµ™¥±Ñ•É•…¹½¹¥…°ÑÉ…Ù•ÉÍ…°((¡Á…É•¹Ñ}Ñ•µÁ±…Ñ•}¥°¹…µ•ÍÁ…”°¹…µ”¤(€€€€´ø•á…ĞµÁ…É•¹Ğ…¹É½½Ğµ½¹±ä…¹½¹¥…°ÑÉ…Ù•ÉÍ…°(€€€€´øÉ•Ù•ÉÍ”µÁ…É•¹Ğ…•ÍÌ¹••‘•‰ä±¥¹•…”±¥™•Ñ¥µ”½‘•±•Ñ”¡•­Ì)€()Q¡”½µÁ½Í¥Ñ”Á…É•¹Ğ¥¹‘•àÉ•Á±…•ÌÑ¡”•á¥ÍÑ¥¹œÁ…É•¹Ğµ½¹±ä¥¹‘•àè()Ñ•áĞ)¥á}½‰©•Ñ}Ñ•µÁ±…Ñ•Í}Á…É•¹Ğ(€€€€¡Á…É•¹Ñ}Ñ•µÁ±…Ñ•}¥¤)€()‰•…ÕÍ”¥ÑÌ±•…‘¥¹œ½±Õµ¸ÁÉ•Í•ÉÙ•ÌÑ¡”É•Ù•ÉÍ”µÁ…É•¹Ğ±½½­ÕÀİ¡¥±”Ñ¡”ÍÕ™™¥àÍÕÁÁ½ÉÑÌÑ¡”½±±•Ñ¥½¸Ì…¹½¹¥…°½É‘•È…¹­•åÍ•ĞÁ…¥¹…Ñ¥½¸¸()¼¹½Ğ…‘%91U€½±Õµ¹Ì¸‘•ÍÉ¥ÁÑ¥½¹€…¹‘•™…Õ±Ñ}Ù•ÉÍ¥½¹€…É”µÕÑ…‰±”…¹Ñ¡”½µÁ±•Ñ”ÁÕ‰±¥ŒÉ½ÜÍÑ¥±°É•ÅÕ¥É•Ì¡•…À…•ÍÌì½Áå¥¹œÑ¡•´¥¹Ñ¼½±±•Ñ¥½¸¥¹‘•á•Ìİ½Õ±¥¹É•…Í”µÕÑ…Ñ¥½¸µ…¥¹Ñ•¹…¹”İ¥Ñ¡½ÕĞ•ÍÑ…‰±¥Í¡¥¹œ„½µÁ•±±¥¹œ½Ù•É¥¹œµÉ•…‰•¹•™¥Ğ¸()¼¹½ĞÉ•…Ñ”…‘‘¥Ñ¥½¹…°¥¹‘•á•Ì½¸è()Ñ•áĞ)‘•ÍÉ¥ÁÑ¥½¸)‘•™…Õ±Ñ}Ù•ÉÍ¥½¸)¥‰•å½¹Ñ¡”ÁÉ¥µ…Éä­•ä)ÅÕ…±¥™¥•‘}¹…µ”…Ì„‘•É¥Ù•‘ÕÁ±¥…Ñ”)€()…¹‘¼¹½ĞÁÉ½±¥™•É…Ñ”¥¹‘•á•Ì™½È•Ù•Éä™¥±Ñ•È½µ‰¥¹…Ñ¥½¸¸Q¡”™½ÕÈ…•ÍÌ™…µ¥±¥•Ì…‰½Ù”½Ù•ÈÑ¡”ÁÉ¥µ…Éä½±±•Ñ¥½¸Í¡…Á•ÌìÉ•µ…¥¹¥¹œ½¹©Õ¹Ñ¥Ù”™¥±Ñ•ÉÌµ…ä‰”…ÁÁ±¥•…ÌÉ•Í¥‘Õ…°ÁÉ•‘¥…Ñ•Ì½Ù•ÈÑ¡”‰•ÍĞ…Ù…¥±…‰±”ÍÑ…‰±”µ­•ä…•ÍÌÁ…Ñ ¸((ŒŒŒÉ¡¥Ñ•ÑÕÉ”Ù•É¥™¥…Ñ¥½¸¡…¹‘½™˜()É¡¥Ñ•ÑÕÉ”±½Í¥¹œµÕÍĞÙ…±¥‘…Ñ”É•ÁÉ•Í•¹Ñ…Ñ¥Ù”…É‘¥¹…±¥Ñ¥•Ì™½Èè()Ñ•áĞ)Õ¹™¥±Ñ•É•)¹…µ•ÍÁ…”µ™¥±Ñ•É•)¹…µ”µ½¹±ä)…‰ÍÑÉ…Ğµ™¥±Ñ•É•)•á…ĞµÁ…É•¹Ğ)É½½Ğµ½¹±ä)€()İ¥Ñ …¹İ¥Ñ¡½ÕĞ„ÕÉÍ½È°ÕÍ¥¹œÁ±…¹¹•È…¹ÉÕ¹Ñ¥µ”•Ù¥‘•¹”¸%ĞµÕÍĞÁÉ•Í•ÉÙ”è()Ñ•áĞ)½¹”…ÕÑ¡½É¥Ñ…Ñ¥Ù”‰ÕÍ¥¹•ÍÌÍÑ…Ñ•µ•¹Ğ)‰½Õ¹‘•±¥µ¥Ğ¬Ä…ÅÕ¥Í¥Ñ¥½¸)…¹½¹¥…°­•åÍ•Ğ½É‘•È)¹¼Á…Ñ¡½±½¥…°•áÁ±¥¥ĞÍ½ÉĞ½µ…Ñ•É¥…±¥é…Ñ¥½¸)¹¼Õ¹©ÕÍÑ¥™¥•™Õ±°ÁÉ½©•Ñ¥½¸Í…¸)¹¼‘ÕÁ±¥…Ñ”½É•‘Õ¹‘…¹Ğ¥¹‘•à)€()Q¡”•á…ĞA½ÍÑÉ•ME0Á±…¸¥Ì¹½ĞÁ…ÉĞ½˜Ñ¡”ÁÕ‰±¥Œ½¹ÑÉ…Ğ¸±…Ñ•Èµ•…ÍÕÉ•…É¡¥Ñ•ÑÕÉ”…‘©ÕÍÑµ•¹Ğµ…äµ•É”½ÈÉ•Á±…”…¸¥¹‘•à½¹±ä¥˜¥ĞÁÉ•Í•ÉÙ•Ì•ÅÕ¥Ù…±•¹Ğ…•ÍÌ™½ÈÑ¡”½İ¹•ÅÕ•Éä™…µ¥±¥•Ì…¹É•½É‘ÌÑ¡”•Ù¥‘•¹”•áÁ±¥¥Ñ±ä¸((ŒŒI•µ…¥¹¥¹œÑ•¡¹¥…°É•Ù¥•Ü‰½Õ¹‘…Éä()MÑ¥±°Ñ¼É•Ù¥•Ü™½ÈÑ¡¥Ì½Á•É…Ñ¥½¸è()Ñ•áĞ)É•…Í¹…ÁÍ¡½Ğ½½¹ÕÉÉ•¹äÉ•…±¥é…Ñ¥½¸)µ•…ÍÕÉ•µ•¹Ğµ½É¥•¹Ñ•½ÍĞÙ…±¥‘…Ñ¥½¸…¹™¥¹…°½Á•É…Ñ¥½¸±½ÍÕÉ”)€()Q¡”¹•áĞµ¥É¼µÁ½¥¹Ğ¥ÌÑ¡”É•…Í¹…ÁÍ¡½Ğ½½¹ÕÉÉ•¹äÉ•…±¥é…Ñ¥½¸¸(