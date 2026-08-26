# ObjectTemplate.DEPRECATE discovery — WIP / NON-NORMATIVE

## Scope

First-phase M4 discovery for `ObjectTemplate.DEPRECATE`. Non-normative. Lock redesign remains deferred to the global concurrency phase.

## AS-IS flow

Current successful path:

1. lock ObjectTemplate header (SHARE);
2. lock exact ObjectTemplateVersion (NO KEY UPDATE);
3. load lineage;
4. load exact version aggregate (header + local properties + local components);
5. require current status `PUBLISHED`;
6. require target is not the current default;
7. check whether any current PUBLISHED child ObjectTemplateVersion pins the target as exact parent;
8. update exact status to `DEPRECATED`;
9. reload the complete exact aggregate;
10. commit.

Because current `get_version()` loads header, properties and components with separate statements, the operation performs substantially more data access than its policy decision requires.

## Current truth vs immutable semantics

`DEPRECATE` is a current-policy operation. It needs:

- current exact-version existence;
- current exact-version status;
- current lineage default pointer;
- current existence of any active PUBLISHED exact child that pins this version.

The semantic payload of the exact version is not needed to decide admissibility.

Worker-local immutable ObjectTemplate cache is therefore not an admission authority for this operation.

## Active-child lookup

Current `has_active_child()` performs a `COUNT(*)` over ObjectTemplateVersions where:

- `parent_template_id = target template`;
- `parent_version = target version`;
- child status is `PUBLISHED`.

Only a boolean answer is needed. Candidate simplification: use `EXISTS` rather than counting all matching rows.

No reverse-dependency materialization is proposed specifically for this rare mutation. The dynamic lookup is expected to be sufficient if well indexed.

## Immutable materialization/cache behavior

`PUBLISHED -> DEPRECATED` changes lifecycle policy only. It does not change:

- exact parent pin;
- local declarations;
- materialized effective schema;
- runtime-oriented compiled ObjectTemplate representation.

Therefore:

- effective-schema materialization remains unchanged;
- immutable ObjectTemplate cache entries remain valid;
- no semantic cache invalidation is required.

A DEPRECATED exact version remains valid for historical exact consumers such as already-pinned Objects.

## Data-access findings

### Initial exact-version load

A complete exact version may still be needed to produce the public result, but it should be projected in one statement rather than via separate header/property/component reads.

### Post-update reload

The complete exact-version reload after changing status is redundant. The operation already holds the pre-update immutable semantic payload; the result can be reconstructed with the same payload and `status = DEPRECATED`.

Candidate first-phase data path, keeping current locking structure:

1. current locks;
2. lineage/default projection;
3. one exact-version projection;
4. one active-child `EXISTS`;
5. one status update;
6. construct result in memory;
7. commit.

Further compression via lock-returned status/default data is deferred to the concurrency redesign.

## Denormalization/cache decision

No new denormalization is justified by `ObjectTemplate.DEPRECATE` itself.

The existing M4 candidates remain:

- stable lineage ancestry closure for immutable lineage compatibility questions;
- materialized effective schema for immutable PUBLISHED/DEPRECATED exact versions;
- runtime-oriented worker cache for Object validation.

## Open items

- exact locking/rendezvous requirements against concurrent child publication, default changes and deletion;
- whether locking reads can return current status/default and remove ordinary reads;
- final SQL shape and indexes for active-child `EXISTS`.
