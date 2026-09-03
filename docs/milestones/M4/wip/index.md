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

relationship.md
```

## REVIEWED BASELINE SUPPORT

```text
object-template-ancestry-cache.md
```

The route-level Object sweep is complete and consolidated in `object.md`, with cross-operation Object generation/component persistence responsibilities remaining in their dedicated reviewed owners.

The factual Relationship top-down sweep is also complete at the discovery/revalidation level and has been losslessly consolidated back into the single owner:

```text
relationship.md
```

The temporary `relationship-continuation.md` and `relationship-continuation-2.md` files have been merged back and removed. `relationship.md` now contains the ordered post-definition checkpoints through `C-REL-35`, including the global/Object-scoped reads, CREATE, DATA_CHANGE, SCHEMA_CHANGE and DELETE closures.

`REVIEWED BASELINE` here remains a WIP review state only. Factual Relationship still has architecture-closing decisions, most notably the final CREATE Definition-selection request shape and the global physical/cache/concurrency realization.

## ACTIVE REVIEW FRONTIER

The current top-down data-plane review frontier is now:

```text
Lifecycle
```

Current Lifecycle inputs:

```text
object-lifecycle-read-discovery.md
lifecycle-list-detail-api-discovery.md
lifecycle-summary-data-path-discovery.md
```

The top-down order is therefore now:

```text
Object         -> REVIEWED BASELINE
Relationship   -> REVIEWED BASELINE / ARCHITECTURE CLOSING PENDING
Lifecycle      -> ACTIVE REVIEW FRONTIER
```

Model-plane families remain active inputs in parallel and may still trigger targeted revalidation when a material upstream decision changes a reviewed data-plane assumption.

# 2. Current M4 spine

## Cross-cutting principles and method

### [`general-domain-principles.md`](general-domain-principles.md) — SPINE / REVIEWED BASELINE

Current owner for ratified general M4 principles, including:

```text
version number identifies exact version + allocation order only
validity of one exact version != cross-version migrability
REVISE/PUBLISH do not absorb future runtime-migration responsibility
lifecycle payload = complete operation-owned semantic transition
failure semantics/details derive from the efficient legal execution path
    -> no backend work solely for diagnostic enrichment
```

### [`version-allocation.md`](version-allocation.md) — SPINE / REVIEWED BASELINE

Current owner for shared monotonic/no-reuse version allocation and the logical `last_versions(id,last_version)` direction.

### [`discovery.md`](discovery.md) — SPINE / discovery framing / NOT REVIEWED BASELINE

Initial M4 motivation, workload hypotheses and design exploration.

### [`top-down-api-closure-sweep.md`](top-down-api-closure-sweep.md) — SPINE / operating method / NOT REVIEWED BASELINE

Method used to close routes from public contract through data path, cache, semantic concurrency, persistence implications, cost and architecture handoff.

### [`milestone-relational-schema-closure-requirement.md`](milestone-relational-schema-closure-requirement.md) — SUPPORT / HANDOFF

Governance input requiring milestone closure to document the resulting relational schema; not a current DDL freeze.

# 3. Object current owners

### [`object.md`](object.md) — SPINE / REVIEWED BASELINE / Object family owner

Primary family owner for Object public surfaces and route-local navigation.

Current full-sweep checkpoints include:

```text
POST /objects
GET /objects
GET /objects/{id}
PUT /objects/{id}/canonical-name
POST /objects/{id}/properties
GET /objects/{id}/schema
POST /objects/{id}/schema
GET /objects/{parent}/components/{slot}
POST /objects/{parent}/components/{slot}/attach
POST /objects/{parent}/components/{slot}/detach
GET /objects/{child}/owner
DELETE /objects/{id}
```

Use `object.md` for route contracts/data paths/cost/concurrency/handoffs. Cross-operation responsibilities remain intentionally separate:

```text
object-revision.md
    -> intrinsic Object generation / expected_revision protocol

object-components-persistence.md
    -> current component-slot / ownership persistence boundary

object-template-ancestry-cache.md
    -> reusable stable ObjectTemplate ancestry/compatibility cache support
```

The Object family closure is dependency-aware. Material future changes to certified effective-property/effective-component semantics or stable ancestry trigger only the targeted revalidations recorded by the Object owner.

# 4. Model-plane families — ACTIVE INPUT sets

These families remain non-normative active input unless/until consolidated and promoted by the milestone architecture process.

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

### [`new-relationship-definition.md`](new-relationship-definition.md) — INTENT DRAFT / ACTIVE INPUT / ARCHITECTURE HANDOFF

This remains the upstream intent owner for the RelationshipDefinition redesign that removed autonomous `RelationshipResolution` identity from the current candidate direction and established stable directional semantic names plus materialized exact-template semantic space.

Its stabilized semantics were sufficient to complete the downstream factual Relationship revalidation. Remaining model-plane API/physical/lifecycle details no longer freeze the factual owner by default; a future material change reopens only affected dependencies.

Existing distributed discovery remains active input/source for revalidation:

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

# 5. Factual Relationship — REVIEWED BASELINE / ARCHITECTURE CLOSING PENDING

### [`relationship.md`](relationship.md) — SPINE / REVIEWED BASELINE / single factual Relationship WIP owner

`relationship.md` is again the single factual Relationship WIP owner. The former temporary continuations have been losslessly absorbed and removed.

The post-definition full sweep covers exactly the M4 factual capabilities:

```text
CREATE
GET global detail by relationship_id
GET Object-scoped Relationship collection
DATA_CHANGE
SCHEMA_CHANGE
DELETE
```

Current reviewed data-plane direction includes:

```text
relationships
    -> factual root
    -> relationship_definition_id
    -> exact relationship_definition_version
    -> properties
    -> private revision generation token

runtime_relationship_cells
    -> owned exact Object-level semantic cells
    -> (relationship_id, from_object_id, name, to_object_id)

semantic-cell uniqueness
    -> (from_object_id, name, to_object_id)
    -> at most one current factual Relationship owner

semantic name
    -> stable runtime semantic state
    -> no autonomous RelationshipResolution / resolution_id
```

Key reviewed route-level conclusions include:

```text
global GET
    -> complete lossless perspectives[]
    -> one authoritative PostgreSQL statement
    -> no model-plane recertification

Object-scoped GET
    -> 1:1 runtime-cell projection
    -> exact name filter restored
    -> keyset (name, to_object_id)
    -> semantic-cell B-tree reused for navigation

DATA_CHANGE
    -> immutable exact-RDV semantic cache
    -> relationships.revision freshness
    -> no new model-plane admission

SCHEMA_CHANGE
    -> exact SOURCE/TARGET pair
    -> numeric version direction has no migration meaning
    -> exact-pair MigrationPlan
    -> lossless conditional LIST -> SCALAR
    -> revision freshness + final TARGET PUBLISHED admission

DELETE
    -> explicit root-only DELETE
    -> owned runtime cells removed by FK ON DELETE CASCADE
    -> no closure recertification
    -> no DELETE revision protocol
    -> one-business-statement target + atomic lifecycle
```

Factual-domain delta discovered during the DELETE pass:

```text
from_object_id != to_object_id

self-reference
    -> 422 semantic_validation_failed
    -> rule = self_reference
```

This supersedes earlier factual self-loop candidates. Consumers of admitted persisted state do not recertify this invariant.

Remaining architecture-closing items include at least:

```text
C-REL-26
    final CREATE request choice:
        Candidate A -> explicit relationship_definition_id
        Candidate B -> derive owning Definition from admitted semantic cell

C-REL-22
    revalidate optional relationship_fact_conflict owner detail
    against the final efficient arbitration path

final relational DDL
    relationships.revision
    runtime_relationship_cells PK/UNIQUE/FKs/CASCADE
    physical indexes

final cache realization
    immutable exact RDV semantics
    migration plans

final concurrency realization
    lock/wait/FK/UNIQUE arbitration
    retry/rendezvous/deadlock proof

final lifecycle physical carriers
    coherent Object canonical-name observations
    batch persistence/decoding

EXPLAIN/BUFFERS/storage/JSONB/WAL/latency/contention evidence
```

These are architecture/physical decisions and do not reopen route-local factual discovery merely to choose a mechanism. A material new semantic dependency remains a valid targeted reopen trigger.

Global Relationship discovery/query remains deferred to M5 Search API. Object-scoped single-Relationship detail remains unnecessary absent a new caller requirement. Endpoint reassignment/repointing remains DELETE + CREATE with a new factual identity.

# 6. Lifecycle — ACTIVE REVIEW FRONTIER

Current Lifecycle discovery:

```text
object-lifecycle-read-discovery.md
lifecycle-list-detail-api-discovery.md
lifecycle-summary-data-path-discovery.md
```

Reviewed Object and factual Relationship mutation owners now provide the operation-owned lifecycle inputs that this pass must consume rather than redefine.

Object baseline inputs include:

```text
RENAME
    -> exact canonical_name transition

DATA_CHANGE
    -> exact binding context + changed-property delta

SCHEMA_CHANGE
    -> exact binding transition + actual changed-property delta

ATTACH / DETACH
    -> exact ownership-edge semantic identity
    -> required coherent historical Object display metadata
    -> one event per real edge transition

Object CREATE / DELETE
    -> broader creation/deletion snapshot where operation responsibility justifies it
```

Factual Relationship baseline inputs include:

```text
RELATIONSHIP_CREATED
    before_state = null
    after_state  = { relationship_definition_version, properties }

RELATIONSHIP_DATA_CHANGE
    before/after exact factual snapshots
    same exact version

RELATIONSHIP_SCHEMA_CHANGE
    before/after exact factual snapshots
    before.version != after.version
    no numeric direction meaning

RELATIONSHIP_DELETED
    before_state = { relationship_definition_version, properties }
    after_state  = null

Relationship event fan-out
    -> one event row per persisted runtime semantic cell
    -> coherent historical Object canonical-name observations
    -> revision excluded from historical factual state
```

The Lifecycle pass owns final collection/detail DTOs, discriminated event-detail carriers, persistence decoding/read paths, summary-vs-detail payload boundaries and its own physical/read optimization handoff.

# 7. Source-material cleanup notes

Former route-specific Object WIP families and focused component/SCHEMA_CHANGE source files were removed after their lossless absorption into reviewed Object owners. Git history remains historical evidence.

The factual Relationship temporary continuation files were likewise removed after the ordered checkpoints through `C-REL-35` were consolidated into `relationship.md`.

Source material is evidence only. If it conflicts with a reviewed owner/general principle, revalidate explicitly rather than treating the source as authority.

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
