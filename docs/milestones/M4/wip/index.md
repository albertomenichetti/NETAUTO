# M4 WIP — Working-set navigation index

**Status:** ACTIVE NAVIGATION MAP / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This file maps the current M4 working set and the progress of the ongoing top-down review.

Everything under `wip/` remains globally non-normative. `CLOSED`, `FROZEN`, `REVIEWED BASELINE` or similar wording in this directory is only an M4 discovery/review checkpoint and never authorizes implementation by itself.

Navigation role and review state are separate dimensions:

```text
SPINE
    first place to read for current working direction

ACTIVE INPUT
    distributed current discovery not yet consolidated/closed

SUPPORT / HANDOFF
    reusable cross-domain or later-architecture input

SOURCE MATERIAL
    evidence/traceability behind a current owner; not standalone authority

REVIEWED BASELINE
    relevant current owner/support has passed the present review/revalidation
    and may be reused as baseline input for later review steps

ACTIVE REVIEW FRONTIER
    topic currently being revalidated; legacy/open assumptions may still exist
```

`SPINE` answers **where to read**. `REVIEWED BASELINE` / `ACTIVE REVIEW FRONTIER` answers **how far review has progressed**.

## External interpretation anchors

Read these before interpreting M4 WIP:

- [`AGENTS.md`](../../../../AGENTS.md)
- [`README.md`](../../../../README.md)
- [`docs/general/linee_guida_progetto.md`](../../../general/linee_guida_progetto.md)
- [`docs/milestones/M4/status.md`](../status.md)
- [`docs/architecture/README.md`](../../../architecture/README.md)

Until M4 explicitly freezes/promotes a TO-BE delta, delivered architecture remains the normative AS-IS baseline.

# 1. Current review-state snapshot

## REVIEWED BASELINE

```text
general-domain-principles.md
version-allocation.md

object.md
object-revision.md
object-components-persistence.md
object-schema-change.md
```

## REVIEWED BASELINE SUPPORT

```text
object-template-ancestry-cache.md
```

Interpretation of `object.md` is section-sensitive: routes/sections explicitly marked full-sweep complete and already-revalidated cross-operation findings are baseline; later Object sections still marked checkpoint/open remain subject to their own review frontiers.

`object-schema-change.md` is now full-sweep complete and part of the reviewed baseline. It owns the detailed `POST /objects/{id}/schema` semantics, including exact-target migration, migration matrix, `objects.revision` retry alignment, slot-FK arbitration, failure mapping, lifecycle delta and cost/architecture handoff.

The dedicated SCHEMA_CHANGE/fingerprint micro-WIP family was removed after lossless consolidation; Git history is the historical record.

## ACTIVE REVIEW FRONTIER

The next Object route in the top-down sequence is:

```text
GET /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

Current owner/frontier:

```text
object.md
    -> section: GET one component slot
```

Primary source evidence for that frontier:

```text
object-get-components-api-discovery.md
object-components-navigation-public-contract.md
object-components-navigation-data-path.md
object-components-navigation-cursor.md
```

These source files do not override `object.md`; they are inputs for the focused full sweep of that route.

# 2. Current M4 spine

## Cross-cutting principles and method

### [`general-domain-principles.md`](general-domain-principles.md) — SPINE / REVIEWED BASELINE

Current owner for ratified general M4 principles, including:

```text
version number identifies exact version + allocation order only
validity of one exact version != cross-version migrability
REVISE/PUBLISH do not absorb future runtime-migration responsibility
lifecycle payload = complete operation-owned semantic transition
```

### [`version-allocation.md`](version-allocation.md) — SPINE / REVIEWED BASELINE

Current owner for shared monotonic/no-reuse version allocation and the logical `last_versions(id,last_version)` direction.

### [`discovery.md`](discovery.md) — SPINE / discovery framing / NOT REVIEWED BASELINE

Initial M4 motivation, workload hypotheses and design exploration.

### [`top-down-api-closure-sweep.md`](top-down-api-closure-sweep.md) — SPINE / operating method / NOT REVIEWED BASELINE

Method used to close routes from public contract through data path, cache, concurrency, persistence and architecture handoff.

### [`mutation-response-semantics-discovery.md`](mutation-response-semantics-discovery.md) — ACTIVE INPUT

Cross-family mutation-response vs GET-representation discovery.

### [`milestone-relational-schema-closure-requirement.md`](milestone-relational-schema-closure-requirement.md) — SUPPORT / HANDOFF

Governance input requiring milestone closure to document the resulting relational schema; not a current DDL freeze.

# 3. Object current owners

### [`object.md`](object.md) — SPINE / REVIEWED BASELINE / Object route owner

Primary owner for Object public surfaces and route-local semantics/data paths.

Current full-sweep checkpoints include:

```text
POST /objects
GET /objects
GET /objects/{id}
PUT /objects/{id}/canonical-name
POST /objects/{id}/properties
GET /objects/{id}/schema
POST /objects/{id}/schema
DELETE /objects/{id}
```

Detailed SCHEMA_CHANGE mechanics are owned by `object-schema-change.md`; current component persistence mechanics by `object-components-persistence.md`; intrinsic generation by `object-revision.md`.

### [`object-revision.md`](object-revision.md) — SPINE / REVIEWED BASELINE

Owner for the universal intrinsic `objects.revision` generation/CAS protocol:

```text
CREATE -> revision=1
prepared intrinsic mutation -> expected_revision
persisted intrinsic mutation -> revision+1 atomically
stale generation -> no mutation/lifecycle + bounded retry
revision scope excludes ownership/Relationship facts outside objects
```

### [`object-components-persistence.md`](object-components-persistence.md) — SPINE / REVIEWED BASELINE

Owner for current component/ownership persistence:

```text
object_component_slots
object_components
semantic slot identity
materialization invariant
edge -> current semantic-slot dependency
relational blocker arbitration
architecture physical-design handoff
```

### [`object-schema-change.md`](object-schema-change.md) — SPINE / REVIEWED BASELINE / full-swept SCHEMA_CHANGE owner

Use it for:

```text
exact-target SCHEMA_CHANGE semantics
SOURCE/TARGET exact effective-schema comparison
property/component migration matrix
immutable MigrationPlan and bounded semantic cache fills
single-generation Object preparation
expected_revision retry/reprepare
final TARGET PUBLISHED admission
current slot-delta maintenance/FK arbitration
failure taxonomy and precedence
operation-owned lifecycle binding + changed-property delta
no-op/warm/cold cost character
architecture handoff
```

### [`object-template-ancestry-cache.md`](object-template-ancestry-cache.md) — SUPPORT / REVIEWED BASELINE SUPPORT

Reusable stable ObjectTemplate lineage ancestry/compatibility cache. Exact physical/cache implementation remains architecture work.

# 4. Model-plane families — ACTIVE INPUT sets

These families do not yet have one consolidated reviewed owner comparable to the Object owners above. The following filename sets represent their current distributed working state.

## DataType

```text
datatype-create-next-discovery.md
datatype-delete-draft-discovery.md
datatype-delete-lineage-discovery.md
datatype-deprecate-discovery.md
datatype-get-lineage-discovery.md
datatype-get-version-discovery.md
datatype-list-lineages-discovery.md
datatype-list-versions-discovery.md
datatype-revise-discovery.md
datatype-set-default-discovery.md
datatype-set-description-discovery.md
```

Version allocation is cross-domain and owned by `version-allocation.md`.

## ObjectTemplate

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

Support/handoff:

```text
objecttemplate-validation-loader-handoff.md
```

## RelationshipDefinition

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

Version allocation is cross-domain and owned by `version-allocation.md`.

# 5. Factual Relationship — ACTIVE INPUT

Current distributed factual Relationship discovery:

```text
relationship-create-discovery.md
relationship-create-runtime-closure-discovery.md
relationship-get-discovery.md
relationship-list-for-object-discovery.md
relationship-data-change-discovery.md
relationship-delete-discovery.md
relationship-schema-change-discovery.md

object-relationship-list-api-discovery.md
object-relationship-detail-api-discovery.md
```

These remain active inputs, not reviewed public-contract owners.

# 6. Lifecycle — ACTIVE INPUT with reviewed mutation payload inputs

Current lifecycle discovery:

```text
object-lifecycle-read-discovery.md
lifecycle-list-detail-api-discovery.md
lifecycle-summary-data-path-discovery.md
```

The files remain ACTIVE INPUT as complete documents, but mutation-owned payload semantics already ratified by reviewed Object owners are baseline inputs, including:

```text
RENAME
    -> exact canonical_name transition

DATA_CHANGE
    -> exact binding context + changed-property delta

SCHEMA_CHANGE
    -> exact binding transition + actual changed-property delta
```

The lifecycle API pass still owns final collection/detail DTOs, discriminated detail carrier, persistence decoding and read-side physical realization.

# 7. Object source material retained behind current owners

Source material is evidence only. If it conflicts with a reviewed owner/general principle, revalidate explicitly rather than treating the source as authority.

## Component navigation / ownership route sources

```text
object-get-components-api-discovery.md
object-ownership-command-routes.md
object-components-navigation-public-contract.md
object-components-navigation-data-path.md
object-components-navigation-cursor.md
```

The first four relevant navigation files are also current evidence for the active GET-component-slot frontier.

## ATTACH source family

All existing files matching:

```text
object-attach-*.md
to-be-api-object-attach-*.md
```

are SOURCE MATERIAL behind `object.md` / `object-components-persistence.md` unless explicitly re-promoted during ATTACH full sweep.

## DETACH source family

All existing files matching:

```text
object-detach-*.md
to-be-api-object-detach-*.md
```

are SOURCE MATERIAL behind the current owners unless explicitly re-promoted.

## Component-persistence source / architecture inputs

```text
object-component-slots-data-plane-materialization.md
object-component-slots-fk-arbitration.md
object-components-reads-discovery.md
object-components-runtime-schema-discovery.md
```

Physical-only candidates remain architecture inputs rather than reviewed DDL:

```text
object-components-physical-index-candidate.md
object-components-physical-schema-discovery.md
```

## SCHEMA_CHANGE source family cleanup

The dedicated files matching the former detailed SCHEMA_CHANGE/fingerprint source set were removed after the full sweep and lossless consolidation into:

```text
object-schema-change.md
object-revision.md
object-components-persistence.md
lifecycle discovery consumers
```

This includes former `object-schema-change-*` micro-WIPs and the former Object aggregate/optimistic fingerprint WIPs used only by that superseded realization. Git history is the historical source.

# 8. Maintenance rules

When a new WIP is created:

```text
1. classify navigation role
2. if it participates in current review, classify review state
3. do not imply completion merely by indexing it
```

When a review target closes:

```text
1. complete the route/owner full sweep
2. perform lossless consolidation/comparison
3. remove or demote superseded source material only when safe
4. promote the current owner/support to REVIEWED BASELINE
5. advance ACTIVE REVIEW FRONTIER
6. update this index
```

If a reviewed assumption is materially reopened:

```text
mark the affected topic/owner as ACTIVE REVIEW FRONTIER
state the reopened boundary
retain unaffected reviewed findings where ownership permits
```

If SOURCE MATERIAL conflicts with a SPINE owner or ratified general principle:

```text
DO NOT silently choose one
DO NOT infer a resolution
revalidate the specific point explicitly
record the result in the correct owner
```

# 9. Current-state precedence

Use this order to reconstruct M4 today:

```text
repository governance + M4 status
    -> interpretation boundary

general-domain-principles.md
    -> ratified cross-domain principles

version-allocation.md
    -> shared numeric allocation semantics

cross-operation reviewed owner when relevant
    -> e.g. object-revision.md / object-components-persistence.md

current family/topic owner
    -> reviewed baseline or active review frontier

ACTIVE INPUT set where no owner is consolidated

SUPPORT / HANDOFF

SOURCE MATERIAL
    -> evidence/explicit revalidation only
```

Review-state classification never changes topic ownership; it states whether the owner is safe to reuse as a closed baseline for subsequent review work.

## Completeness convention

Explicit filename lists and filename-pattern groups in this index both count as represented working sets. A WIP file outside those represented sets should not be assumed to contribute to current M4 state merely because it exists in the directory. If it becomes relevant again, add/reclassify it explicitly.
