# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S05 — Ownership and Object schema-change vertical slice
```

**Step status:** IN PROGRESS

M1-S00 through M1-S04 have completed implementation review.

M1-S04 accepted implementation baseline:

```text
d7fd864f31aa161962f1c9595c3fdf69228547d7
+
6a66ce267195166e61c8e98f52df3b344f2581f7
    review-fix delta
```

The reviewed S04 capability includes the complete intrinsic Object vertical slice: kernel-generated UUID identity, exact published OTV admission, definitive exact effective-schema interpretation on the caller-owned UoW, canonical runtime-property state, CREATE/RENAME/DATA_CHANGE, typed atomic intrinsic lifecycle persistence, Object GET/list, intrinsic lifecycle reads and deterministic real-PostgreSQL concurrency verification.

The S04 review-fix delta closed the public lifecycle DTO finding by replacing the broad lifecycle response DTO with a true discriminated intrinsic union, preserving the full nine-value lifecycle query-filter vocabulary while exposing only intrinsic event-family response variants. Final reported S04 gates passed with 84 non-PostgreSQL tests and 66 PostgreSQL tests on PostgreSQL 16.14, plus `uv lock`, `uv sync --locked`, build, Ruff and strict Pyright.

## M1-S05 pre-flight outcome

The initial S05 pre-flight found and stopped on a documentation contradiction around current ownership slot identity and `DETACH_FROM`. The affected architecture was explicitly reopened, revalidated, propagated and frozen again before coding.

The clarified frozen current ownership authority is now:

```text
object_components(
    child_object_id,
    parent_object_id,
    slot_name
)

current semantic interpretation
    -> parent Object current exact effective schema
    -> resolve slot_name
    -> SlotSemanticKey(declaring_template_id, slot_name)
```

Consequences:

- `slot_declaring_template_id` is intentionally not persisted in `object_components` and no schema migration is required;
- the runtime edge is a current fact, not a historical pin to the slot declaration that existed when ATTACH occurred;
- ATTACH performs current slot/compatibility admission;
- DETACH removes the exact current edge without repeating ATTACH-style child compatibility admission, but an existing edge must still resolve one current `SlotSemanticKey` in the stabilized parent current exact schema;
- an unresolvable persisted current edge is invariant corruption and maps to `internal_error`; no old-version, last-known-slot or lifecycle-history fallback becomes current-state authority;
- SCHEMA_CHANGE must fail before repinning if any outgoing edge would lose semantic-slot continuity or child compatibility in the target schema;
- ATTACH_TO / DETACH_FROM materialize the current resolved `SlotSemanticKey` as historical lifecycle metadata at transition time.

The ownership authority clarification was propagated through the owning domain, schema-change, lifecycle, persistence, PostgreSQL realization and API wire contracts and recorded in the final consistency/freeze authority. The global M1 architecture is again FROZEN.

Relevant architecture-alignment commits:

```text
01a5cdc4988b89672390c7f3085c52a9d934ab0c  object ownership authority
d0d7488deffdfdc7b8bb152497a500ce78220adc  API-03.6 DETACH semantics
196d1170d4910558ac725fce73583a316ff053d0  PERSIST-06 current edge authority
91a06c235b9a91a80656afa849aa07c9950ca408  REALIZE-10/15 ownership realization
0107bb5d059f18334cb03803ab11b91c2f4e9452  SCHEMA_CHANGE preservation consequence
b61a12b81701afe6727e3286a41d8742043b10ad  ownership lifecycle SlotSemanticKey
21bb8c62464960717144629857536267b9928a0a  consistency review / re-freeze record
5192c1d4fd40ce1c58b55ae33cfcb8681219845a  architecture index freeze restoration
```

A second pre-flight check found verification-decomposition drift: canonical ownership `REF-02` / `REF-05` require final `Object.DELETE`, while that semantic operation is deliberately delivered only in M1-S08. `steps.md` was realigned without changing domain semantics:

```text
9aa9dcc60fcb2f06f6a8b6a0346970e211f791e2
```

S05 therefore proves current ownership FK/PK `RESTRICT`/single-owner mechanics directly and implements all S05-realizable semantic concurrency scenarios. The semantic `REF-02` / `REF-05` variants are completed in S08 together with `Object.DELETE`; no fake/private delete operation is introduced in S05.

The mandatory S05 re-pre-flight against the corrected frozen documents is now clean. No architecture/documentation contradiction is currently known.

The non-normative Codex execution prompt for the current step is:

```text
docs/milestones/M1/wip/M1-S05-codex-prompt.md
```

Prompt creation commit:

```text
1d5ac060ef79e7604cc29c65aa03d6eded11687e
```

The prompt is an implementation aid only. `AGENTS.md`, the frozen M1 contract/architecture/steps and ratified STACK decisions remain authoritative.

With a single externally supplied `TEST_DATABASE_URL`, PostgreSQL-required suites remain serial with respect to pytest-xdist. Cross-worker PostgreSQL parallelism is permitted only when the external environment supplies isolated database targets per worker or equivalent isolation consistent with STACK-07/PGTEST.

## Authoritative baseline

M1 implementation proceeds from the following frozen/ratified authorities:

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
    repository-level operating contract for coding agents
```

Before each implementation step, the mandatory pre-flight defined by `AGENTS.md`, `docs/general/linee_guida_progetto.md` and the step itself must be executed against the current normative repository documents.

## Step registry

```text
M1-S00  COMPLETED        Clean-slate project bootstrap and quality/test runtime
M1-S01  COMPLETED        PostgreSQL schema, migration, UoW and deterministic-test foundation
M1-S02  COMPLETED        PrimitiveType and DataType vertical slice
M1-S03  COMPLETED        ObjectTemplate and active model graph vertical slice
M1-S04  COMPLETED        Object intrinsic state and intrinsic lifecycle vertical slice
M1-S05  IN PROGRESS      Ownership and Object schema-change vertical slice
M1-S06  NOT STARTED      RelationshipDefinition model-plane and capability vertical slice
M1-S07  NOT STARTED      Runtime Relationship and relationship lifecycle vertical slice
M1-S08  NOT STARTED      Cross-domain integrity, destructive-operation and API/read closure
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

None known for implementing M1-S05.

PostgreSQL-dependent verification requires an externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

A newly discovered contradiction or missing decision in frozen architecture is not an implementation blocker to work around: the affected work stops and follows the explicit architecture reopen/revalidate/propagate/re-freeze process.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after its implementation delta has been reviewed and its applicable quality gates, required PostgreSQL/API/concurrency verification and documentation coherence satisfy the exit criteria in `steps.md`.
