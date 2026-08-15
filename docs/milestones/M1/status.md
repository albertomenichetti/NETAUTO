# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S06 — RelationshipDefinition model-plane and capability vertical slice
```

**Step status:** IN PROGRESS

M1-S00 through M1-S05 have completed implementation review.

## M1-S05 accepted baseline

Accepted implementation:

```text
62857cc0c32b332a0e916ea83bdb2653f69596ab
+
622a46dde54c8f74cb8bc4ae6b7e70ebf140ee6f
    deterministic verification closure
```

The reviewed S05 capability includes ATTACH/DETACH ownership, current SlotSemanticKey interpretation, acyclic single-owner graph enforcement, forward same-lineage Object SCHEMA_CHANGE, structural ownership lifecycle events, coherent components/owner projections and complete S05 deterministic PostgreSQL coverage. Final reported gates passed with 86 non-PostgreSQL and 86 PostgreSQL tests on PostgreSQL 16.14, plus lock/sync/build, Ruff and strict Pyright.

The frozen ownership authority remains:

```text
object_components(child_object_id, parent_object_id, slot_name)
    -> current parent exact effective schema
    -> SlotSemanticKey(declaring_template_id, slot_name)
```

Semantic ownership REF-02 / REF-05 remain assigned to M1-S08 together with final Object.DELETE.

## M1-S06 pre-flight outcome

The mandatory S06 pre-flight re-read the current repository authorities for RelationshipDefinition/RelationshipResolution, ObjectTemplate lineage references/capabilities, persistence/UoW, REALIZE-12/15, canonical PGTEST and API-03.

Confirmed:

```text
M1 contract      FINAL / FROZEN
M1 architecture  FROZEN as a set
M1 steps         FINAL / FROZEN
M1-S00..S05      COMPLETED
STACK-01..09     RATIFIED
```

No architecture/documentation contradiction is currently known for S06.

Frozen S06 implementation boundaries include:

- complete RelationshipDefinition + RelationshipResolution aggregate;
- deterministic symmetric/non-symmetric Resolution-set derivation;
- semantic equivalence and cross-Definition conflict freedom over lineage-overlap spaces;
- `RELATIONSHIP_DEFINITION_CONFLICT_GATE` for CREATE/RENAME only;
- gate acquisition and authoritative certified-set read as separate statements with a fresh READ COMMITTED snapshot;
- Definition RENAME owner `FOR NO KEY UPDATE`, DELETE owner `FOR UPDATE`;
- endpoint ObjectTemplate lineage references as stable FK `RESTRICT` references, with no exact-OTV admission or generic lifecycle lock;
- coherent Definition aggregate reads and ObjectTemplate relationship-capability projection;
- no standalone RelationshipResolution API;
- no S07 factual Relationship behavior or Relationship lifecycle event variants;
- no migration or new advisory gate.

Because RD.DELETE intentionally does not take the conflict gate, the implementation prompt requires the post-gate certified-set read to observe complete Definition+Resolution aggregates from one coherent committed snapshot rather than mixing header/child generations across multiple READ COMMITTED statement snapshots.

Canonical deterministic PostgreSQL coverage owned by S06 includes:

```text
ROW-17
REF-01  RD.CREATE -> ObjectTemplate stable-lineage reference
GATE-04 A/B
GATE-05 A/B
GATE-06 A/B
ATOMIC-04C
```

plus the required REALIZE-12 mechanism regressions for global gate over-serialization, fresh post-wait visibility, no-gate DELETE, same-Definition rename ownership, gate lifetime/rollback and no fan-out row locking.

The non-normative Codex implementation prompt is:

```text
docs/milestones/M1/wip/M1-S06-codex-prompt.md
```

Prompt creation commit:

```text
cb568fef6c3e9ee6238542adc7844e76782e576e
```

The prompt is an execution aid only; `AGENTS.md`, the frozen M1 contract/architecture/steps and ratified STACK decisions remain authoritative.

## Authoritative baseline

M1 implementation proceeds from the frozen/ratified authorities:

```text
docs/milestones/M1/contract.md
    FINAL / FROZEN

docs/milestones/M1/architecture/README.md
    FROZEN global architecture baseline

docs/milestones/M1/steps.md
    FINAL / FROZEN implementation decomposition

docs/general/technology_baseline.md
    STACK-01..STACK-09 ratified

AGENTS.md
    repository-level operating contract
```

Before each implementation step, the mandatory pre-flight defined by `AGENTS.md`, `docs/general/linee_guida_progetto.md` and the step itself must be executed against the current normative repository documents.

## Step registry

```text
M1-S00  COMPLETED        Clean-slate project bootstrap and quality/test runtime
M1-S01  COMPLETED        PostgreSQL schema, migration, UoW and deterministic-test foundation
M1-S02  COMPLETED        PrimitiveType and DataType vertical slice
M1-S03  COMPLETED        ObjectTemplate and active model graph vertical slice
M1-S04  COMPLETED        Object intrinsic state and intrinsic lifecycle vertical slice
M1-S05  COMPLETED        Ownership and Object schema-change vertical slice
M1-S06  IN PROGRESS      RelationshipDefinition model-plane and capability vertical slice
M1-S07  NOT STARTED      Runtime Relationship and relationship lifecycle vertical slice
M1-S08  NOT STARTED      Cross-domain integrity, destructive-operation and API/read closure
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

None known for implementing M1-S06.

PostgreSQL-dependent verification requires an externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

A newly discovered contradiction or missing decision in frozen architecture is not an implementation choice: the affected work stops and follows the explicit architecture reopen/revalidate/propagate/re-freeze process.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after implementation review and all applicable quality, API, persistence and deterministic PostgreSQL verification gates satisfy `steps.md`.
