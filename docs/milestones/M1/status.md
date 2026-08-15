# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S05 — Ownership and Object schema-change vertical slice
```

**Step status:** IN PROGRESS — REVIEW CHANGES REQUIRED

M1-S00 through M1-S04 have completed implementation review.

M1-S04 accepted implementation baseline:

```text
d7fd864f31aa161962f1c9595c3fdf69228547d7
+
6a66ce267195166e61c8e98f52df3b344f2581f7
    review-fix delta
```

The reviewed S04 capability includes the complete intrinsic Object vertical slice: kernel-generated UUID identity, exact published OTV admission, definitive exact effective-schema interpretation on the caller-owned UoW, canonical runtime-property state, CREATE/RENAME/DATA_CHANGE, typed atomic intrinsic lifecycle persistence, Object GET/list, intrinsic lifecycle reads and deterministic real-PostgreSQL concurrency verification.

## M1-S05 architecture pre-flight

The initial S05 pre-flight found a documentation contradiction around current ownership slot identity and `DETACH_FROM`. The architecture was explicitly reopened, propagated and frozen again before coding.

Frozen current ownership authority:

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

- `slot_declaring_template_id` is intentionally not persisted in `object_components`; no migration is required;
- the runtime edge is a current fact, not a historical declaration pin;
- ATTACH performs current slot/compatibility admission;
- DETACH removes the exact current edge without repeating ATTACH-style compatibility admission, but the edge must still resolve one current `SlotSemanticKey`;
- an unresolvable persisted current edge is invariant corruption -> `internal_error`; no old-version/lifecycle fallback is authority;
- SCHEMA_CHANGE must fail before repinning if an outgoing edge would lose semantic-slot continuity/compatibility;
- ATTACH_TO / DETACH_FROM materialize the current resolved `SlotSemanticKey` as historical event metadata.

Architecture alignment commits:

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

A second pre-flight check found verification-decomposition drift: ownership `REF-02` / `REF-05` require final `Object.DELETE`, deliberately delivered only in M1-S08. `steps.md` was realigned in:

```text
9aa9dcc60fcb2f06f6a8b6a0346970e211f791e2
```

S05 therefore proves current ownership FK/PK mechanics directly; semantic `REF-02` / `REF-05` are completed in S08 with Object.DELETE. No private/fake delete belongs in S05.

The mandatory S05 re-pre-flight against the corrected frozen documents was clean.

## S05 implementation review

Implementation under review:

```text
62857cc0c32b332a0e916ea83bdb2653f69596ab
```

The production delta is broadly architecture-compatible and establishes:

- ATTACH/DETACH current ownership semantics and projections;
- current SlotSemanticKey resolution with no historical fallback/current-edge duplication;
- PK single-owner authority plus transaction ownership graph gate and recursive cycle check;
- forward same-lineage SCHEMA_CHANGE with exact source/target closure and PropertySemanticKey migration;
- outgoing attachment preservation by SlotSemanticKey;
- intrinsic + ownership lifecycle event union and atomic structural events;
- coherent components/owner reads;
- S05 public routes/failure mapping;
- no migration, Object.DELETE, S06+ or normative architecture change.

Reported gates on PostgreSQL 16.14:

```text
uv lock / uv sync --locked / uv build   PASS
Ruff format/check                        PASS
Pyright strict                           PASS
non-PostgreSQL                           86 passed
PostgreSQL                               80 passed
```

The completion review found no current production semantic blocker, but the deterministic PostgreSQL verification closure is incomplete relative to the explicit S05 prompt/canonical PGTEST allocation.

Accepted existing coverage includes ROW-12A/B, target admission, GATE-01, GATE-03A via the GATE-01 fresh-graph interleaving, GATE-03B via the combined ARB-02/GATE-03B test, ARB-02 + raw PK authority, ARB-03A, ARB-04, SNAP-04, ATOMIC-04B, PAR-03 and PAR-04.

Remaining review findings:

```text
ROW-13 reverse order missing
    SCHEMA_CHANGE first -> ATTACH waits/reloads new schema/fails slot admission

ROW-14 reverse order missing
    SCHEMA_CHANGE first while edge current -> migration blocks/fails;
    waiting DETACH then removes edge

ARB-03B missing
    concurrent identical DETACH -> one real removal/event + one no-op success

GATE-02A canonical traceability missing
    longer committed path + cycle candidate through real graph-gate path

GATE-02B missing
    cycle-check ATTACH × concurrent DETACH removing blocking path
    -> safe success after visible removal or conservative cycle rejection only

explicit no-gate regression evidence incomplete
    exact no-op ATTACH / current-owner conflict ATTACH / DETACH must not
    enter OWNERSHIP_GRAPH_WRITE_GATE
```

These are verification-closure findings. Production behavior should not be changed unless the added deterministic tests expose a real defect.

The non-normative review-fix prompt is:

```text
docs/milestones/M1/wip/M1-S05-review-fixes-codex-prompt.md
```

Prompt commit:

```text
e2f06cbcd4b2134cfd264dc675a899179291fe1f
```

The original S05 implementation prompt remains non-normative execution material. `AGENTS.md`, the frozen M1 contract/architecture/steps and ratified STACK decisions remain authoritative.

With a single externally supplied `TEST_DATABASE_URL`, PostgreSQL-required suites remain serial with respect to pytest-xdist. Cross-worker PostgreSQL execution requires externally supplied isolated database targets consistent with STACK-07/PGTEST.

## Authoritative baseline

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

## Step registry

```text
M1-S00  COMPLETED        Clean-slate project bootstrap and quality/test runtime
M1-S01  COMPLETED        PostgreSQL schema, migration, UoW and deterministic-test foundation
M1-S02  COMPLETED        PrimitiveType and DataType vertical slice
M1-S03  COMPLETED        ObjectTemplate and active model graph vertical slice
M1-S04  COMPLETED        Object intrinsic state and intrinsic lifecycle vertical slice
M1-S05  IN PROGRESS      Ownership and Object schema-change vertical slice — review verification changes required
M1-S06  NOT STARTED      RelationshipDefinition model-plane and capability vertical slice
M1-S07  NOT STARTED      Runtime Relationship and relationship lifecycle vertical slice
M1-S08  NOT STARTED      Cross-domain integrity, destructive-operation and API/read closure
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

### S05 completion — deterministic verification closure

Close the targeted ROW-13/ROW-14 reverse orders, ARB-03B, GATE-02A/B and explicit no-gate path regression from the review-fix prompt. No architecture reopening is currently required.

PostgreSQL-dependent verification requires an externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after implementation review and all applicable quality, API, persistence and deterministic PostgreSQL verification gates satisfy `steps.md`.