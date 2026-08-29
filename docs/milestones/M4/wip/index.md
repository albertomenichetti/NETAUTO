# M4 WIP — Working-set navigation index

**Status:** ACTIVE NAVIGATION MAP / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This file is the navigation map for the M4 working space.

It answers one practical question:

> Which documents should a reader use to reconstruct the **current working state of M4**, and which files are still present only as supporting input, traceability, or superseded micro-WIP?

This index is **not** a freeze declaration and it does **not** mean that the documents listed here are complete.

M4 is still in discovery. Documents in this directory may be amended, reopened, consolidated, superseded or removed as discovery progresses.

The labels used by this index are navigation labels only:

```text
SPINE
    read first to understand the current working direction

ACTIVE INPUT
    still directly contributes to the current working state;
    not yet consolidated into a single owner

SUPPORT / HANDOFF
    cross-domain, governance or later-architecture input that is still needed

SOURCE MATERIAL
    retained for evidence, lossless comparison and traceability;
    not a standalone authority for the current working state
```

Those navigation labels are intentionally separate from the **review-state** dimension used by the current top-down review:

```text
REVIEWED BASELINE
    current owner/support whose relevant contents have already passed
    the current review/revalidation process and can be used as baseline
    input for subsequent review steps

ACTIVE REVIEW FRONTIER
    current owner actively being revalidated against the reviewed baseline;
    it may still contain open, legacy or superseded assumptions and must not
    be treated as a closed baseline until its review/absorption is completed
```

A document may therefore be both `SPINE` and `ACTIVE REVIEW FRONTIER`. `SPINE` answers **where to read**; `REVIEWED BASELINE` / `ACTIVE REVIEW FRONTIER` answers **how far the current review has progressed**.

None of those labels means normative, implementation-authorizing or milestone-frozen. Everything under `wip/` remains globally non-normative.

Likewise, words such as `FROZEN`, `CLOSED` or `RECONCILED` inside older WIP files remain only local discovery checkpoints unless the current review-state classification below explicitly treats the document as part of the reviewed baseline.

## External interpretation anchors

Before using this map, the governing context remains outside this directory:

- [`AGENTS.md`](../../../../AGENTS.md) — repository operating rules and WIP semantics.
- [`README.md`](../../../../README.md) — repository entry point.
- [`docs/general/linee_guida_progetto.md`](../../../general/linee_guida_progetto.md) — project lifecycle/governance rules.
- [`docs/milestones/M4/status.md`](../status.md) — current M4 operational phase/status.
- [`docs/architecture/README.md`](../../../architecture/README.md) — delivered AS-IS architecture baseline.

Until M4 explicitly freezes a TO-BE delta, the delivered architecture remains the normative system baseline. This index only maps the M4 working set.

## Current review-state snapshot

The current **reviewed baseline** of the ongoing top-down review is:

```text
general-domain-principles.md
version-allocation.md

object.md
object-revision.md
object-components-persistence.md

object-template-ancestry-cache.md
    -> reviewed reusable support dependency
```

Interpretation:

```text
REVIEWED BASELINE
    general-domain-principles.md
    version-allocation.md
    object.md
    object-revision.md
    object-components-persistence.md

REVIEWED BASELINE SUPPORT
    object-template-ancestry-cache.md
```

The current **active review frontier** is:

```text
object-schema-change.md
```

It is the current detailed owner for SCHEMA_CHANGE, but it is still being revalidated against the reviewed baseline above. In particular, older fingerprint/freshness and source→target assumptions inside that owner must not be treated as already closed merely because the file is consolidated.

The following are useful navigation/method/discovery inputs but are **not, by that fact alone, part of the reviewed baseline**:

```text
index.md
    -> navigation map

discovery.md
    -> framing / hypotheses

top-down-api-closure-sweep.md
    -> review method

mutation-response-semantics-discovery.md
lifecycle discovery files
model-plane operation-level discovery sets
factual Relationship discovery sets
    -> active/distributed discovery still awaiting their own review closure
```

Review-state labels do not replace ownership or precedence rules. An `ACTIVE REVIEW FRONTIER` document remains the current owner for its topic while being reviewed; the label only means that its contents are not yet safe to treat as a closed reviewed baseline for later topics.

---

# 1. Current M4 navigation spine

These are the first documents to read when reconstructing the current working state.

## 1.1 Cross-cutting discovery and principles

### [`general-domain-principles.md`](general-domain-principles.md) — SPINE / REVIEWED BASELINE / active collection

Working owner for general domain principles explicitly discovered or ratified during M4 and intended for later promotion to the appropriate normative documentation on `master`.

Current examples include:

```text
version number identifies an exact version
and orders creation/allocation within one lineage,
but does not encode genealogy, semantic order or migrability

validity of one exact version
!=
cross-version migrability

REVISE/PUBLISH own only the invariants required by their own contracts;
they do not speculate about future runtime migrations

lifecycle payload
    = complete exact semantic transition owned by the operation
    != automatic full aggregate before/after snapshots
```

This file is expected to grow as new general principles are ratified. Already-ratified entries participate in the reviewed baseline; newly added principles must still satisfy the file's explicit ratification rule.

### [`version-allocation.md`](version-allocation.md) — SPINE / REVIEWED BASELINE / cross-domain version allocation

Current cross-domain owner for the temporal version-number guarantee and the shared `last_versions(id,last_version)` allocator direction.

Use it for:

```text
created-after => numerically-greater version
no version-number reuse
shared allocator across versioned domain families
logical last_version allocation semantics
architecture handoff for atomic realization
```

It does not define semantic compatibility or migrability between versions.

### [`discovery.md`](discovery.md) — SPINE / discovery framing / NOT REVIEWED BASELINE

Initial M4 problem framing, workload hypotheses, evidence and design hypotheses. Use it to understand *why* M4 exists, not as a TO-BE contract or as a closed reviewed baseline.

### [`top-down-api-closure-sweep.md`](top-down-api-closure-sweep.md) — SPINE / operating method / NOT REVIEWED BASELINE

Working method for the top-down closure pass from public API surface down to data path, persistence, cache and concurrency consequences. It defines how the review proceeds, not the reviewed semantic baseline itself.

### [`mutation-response-semantics-discovery.md`](mutation-response-semantics-discovery.md) — ACTIVE INPUT / cross-family API semantics

Cross-family discovery around mutation success responses versus GET representation surfaces. It remains active discovery rather than reviewed-baseline authority.

### [`milestone-relational-schema-closure-requirement.md`](milestone-relational-schema-closure-requirement.md) — SUPPORT / governance handoff

Working governance requirement that milestone closure should document the complete resulting relational schema. This is a future governance handoff, not a current physical-schema freeze.

---

# 2. Object current working owners

The Object family has already been partially consolidated. **Use these owners before reading route-local or micro-step Object files.**

### [`object.md`](object.md) — SPINE / REVIEWED BASELINE / Object route owner

Primary consolidated working owner for the Object public surface and route-local semantics/data paths.

Use it first for:

```text
CREATE
LIST
GET Object
canonical-name mutation
properties mutation / DATA_CHANGE
GET schema
component navigation
ATTACH
DETACH
GET owner
DELETE
high-level SCHEMA_CHANGE boundary
```

The document is consolidated but not final or normative.

Current full-sweep checkpoints across the Object working set:

```text
POST /objects
GET /objects
GET /objects/{id}
PUT /objects/{id}/canonical-name
POST /objects/{id}/properties
DELETE /objects/{id}
```

The DATA_CHANGE route has completed its full sweep and lossless absorption into `object.md`. Its dedicated route/source WIPs were removed afterward; Git history remains the historical record.

The sections above that are explicitly full-swept, together with the already-revalidated cross-operation Object findings absorbed into this owner, form part of the current reviewed baseline. Sections that explicitly point to later review fronts remain subject to those owners.

### [`object-revision.md`](object-revision.md) — SPINE / REVIEWED BASELINE / cross-operation intrinsic Object generation

Current owner for the ratified M4 `objects.revision` direction.

Use it for:

```text
revision as universal intrinsic-row generation token
CREATE explicitly inserts revision = 1
all prepared intrinsic mutations use expected_revision
persisted intrinsic row mutation increments revision atomically
RENAME focused revision revalidation completed
DATA_CHANGE full sweep absorbed into object.md under revision CAS
SCHEMA_CHANGE future handoff from intrinsic fingerprint to expected revision
revision scope excludes ownership/Relationship facts outside objects
```

The revision is technical persistence/concurrency state and is not automatically exposed in public Object or lifecycle DTOs.

### [`object-components-persistence.md`](object-components-persistence.md) — SPINE / REVIEWED BASELINE / cross-operation Object component persistence

Primary current working owner for reusable current component/ownership persistence concepts, including the `object_component_slots` / `object_components` candidate boundary, logical identities, materialization invariant, FK-arbitration findings and architecture handoff.

Its lossless persistence comparison is complete and its current cross-operation direction is part of the reviewed baseline. Physical DDL/index choices remain architecture work.

### [`object-schema-change.md`](object-schema-change.md) — SPINE / ACTIVE REVIEW FRONTIER / detailed SCHEMA_CHANGE owner

Primary current working owner for detailed `Object.SCHEMA_CHANGE` discovery.

**Important:** this owner is currently being revalidated step by step following newly ratified general domain principles and the newly introduced Object intrinsic revision direction. Its current fingerprint-related contents must therefore not be interpreted as semantically closed merely because earlier comparison/consolidation passes were completed.

When a legacy SCHEMA_CHANGE source file conflicts with this owner, [`object-revision.md`](object-revision.md), or a newly ratified general principle, do not silently choose one: revalidate the point explicitly and update the owner.

When the SCHEMA_CHANGE full sweep and lossless cleanup are complete, move this owner from `ACTIVE REVIEW FRONTIER` to `REVIEWED BASELINE` and advance the frontier to the next review target.

### [`object-template-ancestry-cache.md`](object-template-ancestry-cache.md) — SUPPORT / REVIEWED BASELINE SUPPORT / reusable stable-lineage cache

Reusable stable ObjectTemplate ancestry/compatibility cache input used by Object and other consumers. Kept separate because it is not Object-route-local state.

Its current stable-lineage compatibility/cache direction is a reviewed support dependency of the Object baseline, while exact physical/cache implementation remains architecture work.

---

# 3. Model-plane families still represented by operation-level discovery sets

These families do **not** yet have a single consolidated owner comparable to `object.md`.

Every file listed below remains an **ACTIVE INPUT** to the current working state of its family unless and until it is explicitly consolidated/superseded. These distributed sets are not automatically part of the `REVIEWED BASELINE`; each family must pass its own current review/closure process first.

## 3.1 DataType — ACTIVE INPUT set

- [`datatype-create-next-discovery.md`](datatype-create-next-discovery.md)
- [`datatype-delete-draft-discovery.md`](datatype-delete-draft-discovery.md)
- [`datatype-delete-lineage-discovery.md`](datatype-delete-lineage-discovery.md)
- [`datatype-deprecate-discovery.md`](datatype-deprecate-discovery.md)
- [`datatype-get-lineage-discovery.md`](datatype-get-lineage-discovery.md)
- [`datatype-get-version-discovery.md`](datatype-get-version-discovery.md)
- [`datatype-list-lineages-discovery.md`](datatype-list-lineages-discovery.md)
- [`datatype-list-versions-discovery.md`](datatype-list-versions-discovery.md)
- [`datatype-revise-discovery.md`](datatype-revise-discovery.md)
- [`datatype-set-default-discovery.md`](datatype-set-default-discovery.md)
- [`datatype-set-description-discovery.md`](datatype-set-description-discovery.md)

Version allocation for this family is cross-domain and owned by [`version-allocation.md`](version-allocation.md); operation-local files must not independently redefine numeric allocation semantics.

## 3.2 ObjectTemplate — ACTIVE INPUT set

- [`objecttemplate-create-discovery.md`](objecttemplate-create-discovery.md)
- [`objecttemplate-create-next-discovery.md`](objecttemplate-create-next-discovery.md)
- [`objecttemplate-delete-draft-discovery.md`](objecttemplate-delete-draft-discovery.md)
- [`objecttemplate-delete-lineage-discovery.md`](objecttemplate-delete-lineage-discovery.md)
- [`objecttemplate-deprecate-discovery.md`](objecttemplate-deprecate-discovery.md)
- [`objecttemplate-get-effective-schema-discovery.md`](objecttemplate-get-effective-schema-discovery.md)
- [`objecttemplate-get-lineage-discovery.md`](objecttemplate-get-lineage-discovery.md)
- [`objecttemplate-get-version-discovery.md`](objecttemplate-get-version-discovery.md)
- [`objecttemplate-list-lineages-discovery.md`](objecttemplate-list-lineages-discovery.md)
- [`objecttemplate-list-versions-discovery.md`](objecttemplate-list-versions-discovery.md)
- [`objecttemplate-publish-discovery.md`](objecttemplate-publish-discovery.md)
- [`objecttemplate-relationship-capabilities-discovery.md`](objecttemplate-relationship-capabilities-discovery.md)
- [`objecttemplate-revise-discovery.md`](objecttemplate-revise-discovery.md)
- [`objecttemplate-set-default-discovery.md`](objecttemplate-set-default-discovery.md)
- [`objecttemplate-set-description-discovery.md`](objecttemplate-set-description-discovery.md)
- [`objecttemplate-clear-default-discovery.md`](objecttemplate-clear-default-discovery.md)

Version allocation for this family is cross-domain and owned by [`version-allocation.md`](version-allocation.md).

Additional cross-domain handoff:

- [`objecttemplate-validation-loader-handoff.md`](objecttemplate-validation-loader-handoff.md) — **SUPPORT / HANDOFF**, not an already-ratified architecture realization.

## 3.3 RelationshipDefinition — ACTIVE INPUT set

- [`relationshipdefinition-create-discovery.md`](relationshipdefinition-create-discovery.md)
- [`relationshipdefinition-create-next-discovery.md`](relationshipdefinition-create-next-discovery.md)
- [`relationshipdefinition-delete-discovery.md`](relationshipdefinition-delete-discovery.md)
- [`relationshipdefinition-delete-draft-discovery.md`](relationshipdefinition-delete-draft-discovery.md)
- [`relationshipdefinition-deprecate-discovery.md`](relationshipdefinition-deprecate-discovery.md)
- [`relationshipdefinition-get-discovery.md`](relationshipdefinition-get-discovery.md)
- [`relationshipdefinition-get-version-discovery.md`](relationshipdefinition-get-version-discovery.md)
- [`relationshipdefinition-list-definitions-discovery.md`](relationshipdefinition-list-definitions-discovery.md)
- [`relationshipdefinition-list-versions-discovery.md`](relationshipdefinition-list-versions-discovery.md)
- [`relationshipdefinition-publish-discovery.md`](relationshipdefinition-publish-discovery.md)
- [`relationshipdefinition-rename-discovery.md`](relationshipdefinition-rename-discovery.md)
- [`relationshipdefinition-revise-discovery.md`](relationshipdefinition-revise-discovery.md)
- [`relationshipdefinition-set-default-discovery.md`](relationshipdefinition-set-default-discovery.md)
- [`relationshipdefinition-clear-default-discovery.md`](relationshipdefinition-clear-default-discovery.md)

Version allocation for this family is cross-domain and owned by [`version-allocation.md`](version-allocation.md).

---

# 4. Factual Relationship discovery still active

Factual Relationship has not yet been consolidated into one family owner. The following remain **ACTIVE INPUT** and are not yet part of the reviewed baseline:

- [`relationship-create-discovery.md`](relationship-create-discovery.md)
- [`relationship-create-runtime-closure-discovery.md`](relationship-create-runtime-closure-discovery.md)
- [`relationship-get-discovery.md`](relationship-get-discovery.md)
- [`relationship-list-for-object-discovery.md`](relationship-list-for-object-discovery.md)
- [`relationship-data-change-discovery.md`](relationship-data-change-discovery.md)
- [`relationship-delete-discovery.md`](relationship-delete-discovery.md)
- [`relationship-schema-change-discovery.md`](relationship-schema-change-discovery.md)

Object-relative Relationship API direction is currently also represented by:

- [`object-relationship-list-api-discovery.md`](object-relationship-list-api-discovery.md)
- [`object-relationship-detail-api-discovery.md`](object-relationship-detail-api-discovery.md)

These are active API discovery inputs, not closed public contracts.

---

# 5. Lifecycle discovery still active

The current Lifecycle working set is:

- [`object-lifecycle-read-discovery.md`](object-lifecycle-read-discovery.md) — Object-relative lifecycle read discovery.
- [`lifecycle-list-detail-api-discovery.md`](lifecycle-list-detail-api-discovery.md) — collection/detail API direction.
- [`lifecycle-summary-data-path-discovery.md`](lifecycle-summary-data-path-discovery.md) — summary/detail data-path consequences.

All three are **ACTIVE INPUT** and remain subject to later consolidation/revalidation. Ratified lifecycle principles already absorbed into `general-domain-principles.md`, `object.md` or another reviewed owner are baseline; these lifecycle discovery documents as complete files are not yet reviewed-baseline owners.

---

# 6. Object source material retained for traceability

The files in this section are still useful for lossless comparison, evidence and reasoning history, but **must not be used as standalone current authority when a consolidated owner above covers the same topic**.

If a useful fact exists only here, it should be revalidated and then absorbed into the relevant owner rather than creating another independent current source.

## 6.1 Earlier Object API / route-local consolidations — SOURCE MATERIAL

- [`to-be-api-object-attach-batch-cost.md`](to-be-api-object-attach-batch-cost.md)
- [`to-be-api-object-attach-batch.md`](to-be-api-object-attach-batch.md)
- [`to-be-api-object-detach-batch.md`](to-be-api-object-detach-batch.md)
- [`to-be-api-object-schema.md`](to-be-api-object-schema.md)
- [`object-get-components-api-discovery.md`](object-get-components-api-discovery.md)

The dedicated legacy files for `POST /objects`, `GET /objects`, `GET /objects/{id}`, `PUT /objects/{id}/canonical-name`, `POST /objects/{id}/properties` and `DELETE /objects/{id}` are intentionally absent: their full sweeps are owned by `object.md`, and superseded route/source files were deleted after lossless absorption. Git history remains the historical record.

## 6.2 Component navigation / ownership route sources — SOURCE MATERIAL

- [`object-ownership-command-routes.md`](object-ownership-command-routes.md)
- [`object-components-navigation-public-contract.md`](object-components-navigation-public-contract.md)
- [`object-components-navigation-data-path.md`](object-components-navigation-data-path.md)
- [`object-components-navigation-cursor.md`](object-components-navigation-cursor.md)

Their current non-superseded findings have to be read through `object.md` first.

## 6.3 ATTACH micro-WIP family — SOURCE MATERIAL

- [`object-attach-discovery.md`](object-attach-discovery.md)
- [`object-attach-batch-cycle-check.md`](object-attach-batch-cycle-check.md)
- [`object-attach-batch-failure-mapping.md`](object-attach-batch-failure-mapping.md)
- [`object-attach-bulk-child-owner-read.md`](object-attach-bulk-child-owner-read.md)
- [`object-attach-cycle-safety-rationale.md`](object-attach-cycle-safety-rationale.md)
- [`object-attach-error-mapping-slot-compatibility.md`](object-attach-error-mapping-slot-compatibility.md)
- [`object-attach-error-precedence.md`](object-attach-error-precedence.md)
- [`object-attach-failure-diagnostic-no-extra-query.md`](object-attach-failure-diagnostic-no-extra-query.md)
- [`object-attach-lifecycle-display-name-freshness.md`](object-attach-lifecycle-display-name-freshness.md)
- [`object-attach-parent-binding-change-error.md`](object-attach-parent-binding-change-error.md)
- [`object-attach-q3-error-result-split.md`](object-attach-q3-error-result-split.md)
- [`object-attach-root-materialization-decision.md`](object-attach-root-materialization-decision.md)
- [`object-attach-self-reference-error.md`](object-attach-self-reference-error.md)
- [`object-attach-uow-q3-graph-admission.md`](object-attach-uow-q3-graph-admission.md)
- [`object-attach-uow-q4-bulk-insert.md`](object-attach-uow-q4-bulk-insert.md)
- [`object-attach-uow-q5-lifecycle-bulk.md`](object-attach-uow-q5-lifecycle-bulk.md)
- [`object-attach-uow.md`](object-attach-uow.md)
- [`object-attach-write-arbitration.md`](object-attach-write-arbitration.md)

Some of these files already explicitly mark themselves superseded/incorporated. The whole family remains available only as traceability/source material behind `object.md` and `object-components-persistence.md`.

## 6.4 DETACH micro-WIP family — SOURCE MATERIAL

- [`object-detach-batch-non-convergent-semantics.md`](object-detach-batch-non-convergent-semantics.md)
- [`object-detach-discovery.md`](object-detach-discovery.md)
- [`object-detach-lifecycle-bulk.md`](object-detach-lifecycle-bulk.md)
- [`object-detach-lockplan-entry.md`](object-detach-lockplan-entry.md)
- [`object-detach-no-parent-lock.md`](object-detach-no-parent-lock.md)
- [`object-detach-parent-share-lock.md`](object-detach-parent-share-lock.md)
- [`object-detach-q1-failure-mapping.md`](object-detach-q1-failure-mapping.md)
- [`object-detach-q1-parent-and-delete.md`](object-detach-q1-parent-and-delete.md)
- [`object-detach-q2-set-based-delete.md`](object-detach-q2-set-based-delete.md)
- [`object-detach-schema-agnostic-with-parent-lockplan.md`](object-detach-schema-agnostic-with-parent-lockplan.md)
- [`object-detach-schema-agnostic.md`](object-detach-schema-agnostic.md)
- [`object-detach-static-validation.md`](object-detach-static-validation.md)
- [`object-detach-two-statement-uow.md`](object-detach-two-statement-uow.md)

This family contains successive and sometimes contradictory exploration steps. Use `object.md` for the current route direction; consult these files only to reconstruct why that direction exists or to perform an explicit revalidation.

## 6.5 Object component persistence source family — SOURCE MATERIAL / architecture input where noted

- [`object-component-slots-data-plane-materialization.md`](object-component-slots-data-plane-materialization.md)
- [`object-component-slots-fk-arbitration.md`](object-component-slots-fk-arbitration.md)
- [`object-components-physical-index-candidate.md`](object-components-physical-index-candidate.md)
- [`object-components-physical-schema-discovery.md`](object-components-physical-schema-discovery.md)
- [`object-components-reads-discovery.md`](object-components-reads-discovery.md)
- [`object-components-runtime-schema-discovery.md`](object-components-runtime-schema-discovery.md)

The lossless persistence comparison has been consolidated into `object-components-persistence.md`.

The physical schema/index files remain useful **architecture inputs only**. Their presence does not ratify final DDL, PK/UNIQUE choices or indexes during discovery.

## 6.6 SCHEMA_CHANGE source family — SOURCE MATERIAL / active revalidation evidence

- [`object-schema-change-ancestry-cache-fill.md`](object-schema-change-ancestry-cache-fill.md)
- [`object-schema-change-bounded-retry.md`](object-schema-change-bounded-retry.md)
- [`object-schema-change-cache-resolution.md`](object-schema-change-cache-resolution.md)
- [`object-schema-change-component-admission-from-snapshot.md`](object-schema-change-component-admission-from-snapshot.md)
- [`object-schema-change-component-migration.md`](object-schema-change-component-migration.md)
- [`object-schema-change-components-discovery.md`](object-schema-change-components-discovery.md)
- [`object-schema-change-delta-taxonomy.md`](object-schema-change-delta-taxonomy.md)
- [`object-schema-change-dtv-cache-fill.md`](object-schema-change-dtv-cache-fill.md)
- [`object-schema-change-dtv-cold-fill.md`](object-schema-change-dtv-cold-fill.md)
- [`object-schema-change-dtv-migration.md`](object-schema-change-dtv-migration.md)
- [`object-schema-change-exact-closure-cold-load.md`](object-schema-change-exact-closure-cold-load.md)
- [`object-schema-change-immutable-migration-plan.md`](object-schema-change-immutable-migration-plan.md)
- [`object-schema-change-lifecycle.md`](object-schema-change-lifecycle.md)
- [`object-schema-change-migration-plan-amortization.md`](object-schema-change-migration-plan-amortization.md)
- [`object-schema-change-preparation-aggregate-read.md`](object-schema-change-preparation-aggregate-read.md)
- [`object-schema-change-preparation-properties.md`](object-schema-change-preparation-properties.md)
- [`object-schema-change-preparation-snapshot.md`](object-schema-change-preparation-snapshot.md)
- [`object-schema-change-prepared-candidate.md`](object-schema-change-prepared-candidate.md)
- [`object-schema-change-property-migration.md`](object-schema-change-property-migration.md)
- [`object-schema-change-property-rule-composition.md`](object-schema-change-property-rule-composition.md)
- [`object-schema-change-protected-fingerprint-read.md`](object-schema-change-protected-fingerprint-read.md)
- [`object-schema-change-q3-fingerprint-outcome.md`](object-schema-change-q3-fingerprint-outcome.md)
- [`object-schema-change-q4-final-mutation.md`](object-schema-change-q4-final-mutation.md)
- [`object-schema-change-remove-preliminary-target-admission.md`](object-schema-change-remove-preliminary-target-admission.md)
- [`object-schema-change-target-admission.md`](object-schema-change-target-admission.md)
- [`object-schema-change-target-version-semantics.md`](object-schema-change-target-version-semantics.md)
- [`object-schema-change-uow-object-lock.md`](object-schema-change-uow-object-lock.md)
- [`object-schema-change-uow-target-admission.md`](object-schema-change-uow-target-admission.md)
- [`object-schema-change-uow.md`](object-schema-change-uow.md)
- [`object-schema-change-warm-cost.md`](object-schema-change-warm-cost.md)
- [`object-optimistic-preparation-fingerprint.md`](object-optimistic-preparation-fingerprint.md)
- [`object-aggregate-fingerprint-canonical-json.md`](object-aggregate-fingerprint-canonical-json.md)
- [`object-aggregate-fingerprint-sha256.md`](object-aggregate-fingerprint-sha256.md)

These files have already fed a consolidation/comparison pass, but remain important evidence while `object-schema-change.md` is being revalidated against newly clarified domain principles and the Object revision direction.

Do not promote a statement from one of these files to current state merely because the file says `FROZEN`; compare it against the current owner, [`object-revision.md`](object-revision.md), the reviewed baseline and the general principles first.

---

# 7. How to maintain this index

This file is part of the working process and must evolve with M4.

Whenever a new WIP document is created:

```text
1. add it here in the appropriate navigation category
2. state whether it is SPINE, ACTIVE INPUT, SUPPORT/HANDOFF or SOURCE MATERIAL
3. if it participates in the current review, also classify its review state
4. do not imply completion merely by indexing it
```

Whenever a review target is completed:

```text
1. finish the explicit full-sweep/revalidation required for that owner
2. perform any required lossless absorption/comparison and cleanup
3. move the owner/support from ACTIVE REVIEW FRONTIER to REVIEWED BASELINE
   only when the current review no longer depends on unresolved legacy assumptions
4. advance ACTIVE REVIEW FRONTIER to the next owner/topic
5. update the Current review-state snapshot above
```

If a reviewed-baseline assumption is materially reopened later:

```text
do not leave the document silently classified as REVIEWED BASELINE

instead:
    mark the affected owner/topic as ACTIVE REVIEW FRONTIER
    state the precise reopened boundary
    retain unaffected reviewed findings where their ownership permits it
```

Whenever several WIPs are consolidated into one owner:

```text
1. promote the consolidated owner into the SPINE/current-family section
2. move absorbed micro-WIPs to SOURCE MATERIAL
3. perform a lossless comparison before deleting source files
4. clean surviving cross-references
5. delete superseded files only when safe
6. rely on Git history as the historical record afterward
7. update the review-state classification if consolidation completes or reopens review work
```

If a SOURCE MATERIAL file conflicts with a SPINE owner or with a newly ratified general principle:

```text
DO NOT silently choose one
DO NOT infer a resolution

instead:
    reopen/revalidate the specific point
    record the resulting decision in the correct owner
    update this index if ownership/status or review-state classification changes
```

## Current-state rule

A reader trying to understand M4 **today** should use this precedence:

```text
repository governance / M4 status
    -> interpretation boundary

general-domain-principles.md
    -> ratified general principles discovered during M4

version-allocation.md
    -> cross-domain numeric version allocation semantics

object-revision.md where intrinsic Object generation/freshness is relevant
    -> cross-operation Object row-generation semantics

current owner for the relevant family/topic
    -> current working direction
    -> may be REVIEWED BASELINE or ACTIVE REVIEW FRONTIER

ACTIVE INPUT set where no consolidated owner exists
    -> current distributed discovery state

SUPPORT / HANDOFF
    -> reusable or later-phase input

SOURCE MATERIAL
    -> traceability / explicit revalidation only
```

Review-state classification does **not** change topic ownership or this precedence. It tells the reader whether the current owner may be safely reused as a closed baseline for later review work, or whether it is still the active place where assumptions are being revalidated.

This precedence is only a working-navigation rule. It does not turn M4 WIP into normative project documentation.

## Completeness rule for the map

The intent of this index is to enumerate the documents that currently participate in reconstructing the M4 working state and to make the progress of the current review explicit.

A WIP file not represented here should **not** be assumed to contribute to the current state merely because it exists in the directory. If it becomes relevant again, add it to this map explicitly and classify its navigation role and, where applicable, its review state.
