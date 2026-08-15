# Codex review-fix prompt — M1-S04

**Status:** NON-NORMATIVE REVIEW-FIX PROMPT.

This file is an execution aid for Codex. It does not override `AGENTS.md`, the frozen M1 contract/architecture/steps, or the ratified technology baseline.

## Assignment

Continue the current implementation step:

```text
M1-S04 — Object intrinsic state and intrinsic lifecycle vertical slice
```

The implementation commit under review is:

```text
d7fd864f31aa161962f1c9595c3fdf69228547d7
```

Do not start M1-S05. Preserve the S04 implementation except for the targeted public lifecycle DTO correction below.

## Mandatory pre-flight

Re-read and obey at minimum:

```text
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md
docs/milestones/M1/steps.md
docs/milestones/M1/status.md

docs/milestones/M1/architecture/object-lifecycle-changelog.md
docs/milestones/M1/architecture/api-read-contract.md
docs/milestones/M1/architecture/api-list-contract.md
docs/milestones/M1/architecture/api-wire-contract.md
docs/milestones/M1/architecture/api-error-contract.md
```

No architecture contradiction was found. This is a transport/public-schema implementation finding only.

## Review finding — lifecycle response DTO is wider than the frozen intrinsic family

Current S04 transport defines one intrinsic lifecycle DTO whose field is effectively:

```text
kind: EventKind
before: Object | null
after: Object | null
```

but persistence `EventKind` contains all nine M1 kinds:

```text
CREATED
RENAME
DATA_CHANGE
SCHEMA_CHANGE
ATTACH_TO
DETACH_FROM
RELATIONSHIP_CREATED
RELATIONSHIP_DELETED
DELETED
```

This makes the public/OpenAPI response schema claim that ownership and Relationship event kinds may use the intrinsic `{before,after}` response shape. That contradicts API-03.9, where lifecycle reads are a discriminated event-family union and structural/Relationship events have different fields.

S04 is authorized to expose only the already-frozen **intrinsic read family**:

```text
CREATED
RENAME
DATA_CHANGE
SCHEMA_CHANGE
DELETED
```

S04 produces only CREATED/RENAME/DATA_CHANGE, but its read representation may recognize SCHEMA_CHANGE/DELETED because they share the frozen intrinsic snapshot family and will be produced later.

### Required correction

Keep these concerns separate:

```text
persistence/internal EventKind
    -> all 9 frozen M1 kinds

public lifecycle `kind` query filter
    -> all frozen route-filter kinds are still accepted according to API-03.10
    -> structural/Relationship filters simply yield no S04 rows

public S04 response item
    -> intrinsic family only
    -> must not advertise ATTACH_TO / DETACH_FROM / RELATIONSHIP_* with intrinsic fields
```

Implement a real discriminated intrinsic response representation. Prefer explicit Pydantic variants whose `kind` fields are `Literal[...]`, for example conceptually:

```text
CREATED
    kind = CREATED
    before = null
    after = Object DTO

RENAME | DATA_CHANGE | SCHEMA_CHANGE
    before = Object DTO
    after = Object DTO

DELETED
    before = Object DTO
    after = null
```

The exact class names are implementation detail. The important contract is that the response schema is discriminated by `kind`, structural/Relationship kinds are not valid intrinsic response variants, and kind-specific before/after nullability is represented rather than one unconstrained nullable pair.

Do not invent S05/S07 ownership or Relationship DTO classes merely to complete the future full union. Those variants are delivered in their owning slices.

Do not move or duplicate persistence `EventKind` simply to satisfy the HTTP type. A transport-only intrinsic kind/union is appropriate.

## Preserve existing accepted S04 behavior

Do not regress:

- Object CREATE/RENAME/DATA_CHANGE semantics;
- PrimitiveType canonicalization reuse;
- exact/default OTV admission and caller-owned-UoW lock lifetime;
- existing Object behavior on DEPRECATED OTV;
- Object `FOR NO KEY UPDATE` owner strength;
- no-op DATA_CHANGE with no event;
- DB-generated lifecycle event id/time;
- runtime/persisted corruption -> `internal_error`;
- Object list/keyset behavior;
- lifecycle filters/cursor ordering;
- Object-specific lifecycle route 404 for absent current Object;
- ROW-11, REF-01, target-admission/default race and ATOMIC-04A deterministic evidence;
- hard S05+ scope boundary.

## Required tests

Add/adjust focused transport/API tests proving:

1. S04 runtime CREATED/RENAME/DATA_CHANGE responses still serialize exactly as API-03.9 requires.
2. CREATED exposes `before:null` and concrete `after`.
3. RENAME/DATA_CHANGE expose concrete before and after snapshots.
4. The generated OpenAPI/public response schema does not advertise `ATTACH_TO`, `DETACH_FROM`, `RELATIONSHIP_CREATED`, or `RELATIONSHIP_DELETED` as valid values of an intrinsic response variant.
5. The global lifecycle **query** filter may still accept a future structural kind and return an empty page on an S04-only dataset; do not accidentally narrow the query contract while narrowing the response family.
6. Existing S04 tests remain green.

No new PostgreSQL concurrency scenario is required solely for this DTO correction, but the complete existing PostgreSQL suite must be rerun because the public integration surface is being changed.

## Required verification

Run and report exact results for:

```text
uv lock
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -m "not postgresql"
uv run pytest -m postgresql
```

Use the externally supplied real `TEST_DATABASE_URL`; do not provision or substitute another database. Report PostgreSQL version.

## Completion report

Return:

- commit SHA pushed to `origin/core_review`;
- concise description of the DTO/OpenAPI correction;
- focused test evidence for discriminated intrinsic lifecycle responses and structural-kind query filtering;
- complete gate counts/results;
- confirmation that no S05+ behavior or normative docs were changed;
- leave `docs/milestones/M1/status.md` reviewer-controlled and do not mark S04 complete.
