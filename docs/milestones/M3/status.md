# M3 — Milestone Status

**Milestone status:** ACTIVE — DISCOVERY

**Authority:** OPERATIONAL CYCLE STATUS

## Cycle identity

```text
cycle          M3
cycle type     milestone
source branch  M3
baseline       delivered AS-IS in docs/architecture/
```

M3 starts from the delivered and merged M2 baseline. The root `README.md` identifies `M3` as the active milestone and this branch as the cycle branch.

## Current phase

```text
phase                    DISCOVERY — COMPLETE
contract                 NOT YET FROZEN
architecture set         NOT YET DEFINED / NOT FROZEN
implementation steps     NOT YET FROZEN
active implementation    NONE
software implementation  NOT AUTHORIZED
blockers                 none for contract preparation
```

All bounded discovery work is complete. The next permitted governance activity is M3 contract drafting and review. No implementation slice is active and no software behavior change is authorized yet.

Discovery material is non-normative and lives under:

```text
docs/milestones/M3/wip/
```

Discovery closure is documented by:

- [`wip/discovery.md`](wip/discovery.md) — discovery navigator;
- [`wip/discovery-closure.md`](wip/discovery-closure.md) — final cross-workstream closure and AS-IS owner mapping.

## Discovery workstream status

```text
Area A — CLI post-create correctness          CLOSED
Area B — public GET/read audit                CLOSED / 22 of 22 consolidated
Area C — parent_template_id = null carrier    CLOSED
```

Area A closure:

- [`wip/cli-post-create-decision.md`](wip/cli-post-create-decision.md)
- [`wip/cli-post-create-closure.md`](wip/cli-post-create-closure.md)

Area B closure:

- [`wip/get-read-census.md`](wip/get-read-census.md)
- [`wip/get-read-review-closure.md`](wip/get-read-review-closure.md)
- [`wip/cursor-identity-audit.md`](wip/cursor-identity-audit.md) — final 12-route cursor identity/keyset cross-check
- route-specific `*-get-*-decision.md` files

Area C closure:

- [`wip/parent-template-null-carrier-decision.md`](wip/parent-template-null-carrier-decision.md)
- [`wip/parent-template-null-carrier-closure.md`](wip/parent-template-null-carrier-closure.md)

These are discovery conclusions only. They do not themselves freeze public behavior, architecture or implementation steps.

## Consolidated discovery outcomes

### Area A — CLI create correctness

The CLI registry has eight `201 Created` operations with exact `Location` validation. Three create operations use nested response-path tokens and are deterministically affected by the common materializer defect.

Target direction:

```text
Location token = exact request key or response JSON path
no Python format grammar
exact Location validation preserved
valid committed 201 + correct Location -> CLI success
genuine protocol mismatch -> cli_protocol_error
```

### Area B — public reads

The 22-route audit found that every canonical public business GET/read path can materialize its required projection in one SQL statement.

A final cursor cross-check audited all 12 paginated public routes and found no additional defect beyond the two already identified during the route walkthrough:

```text
cursor-bearing public routes audited      12 / 12
complete current identities               10 / 12
known incomplete identities                2 / 12
new cursor defects found                    0
keyset-key defects                          0
```

Target direction:

```text
GETs trust persisted semantic state
request/cursor validation remains strict
path-target 404 and empty-collection distinctions remain preserved
read-side semantic re-certification is removed
historical lifecycle carrier decoding remains without semantic transition certification

cursor query identity
    = route
    + every membership-affecting path target
    + every membership-affecting query filter
    + required semantic presence bits
cursor position = complete canonical ordering tuple
limit is not part of semantic query identity

OBJ-GET-03 cursor identity adds parent_object_id
OBJ-GET-06 cursor identity adds object_id
no canonical public GET requires coherent_read() in the target census
mutation-oriented validators remain intact for mutation paths
```

### Area C — ObjectTemplate root filter

The canonical public tri-state is:

```text
parent_template_id omitted -> no parent filter
parent_template_id=<UUID>  -> direct children of that parent
parent_template_id=null    -> root ObjectTemplates only
```

`parent_filter_set` remains internal only. HTTP and CLI must support the same tri-state while preserving the existing application/persistence/cursor semantics.

## Discovery scope impact

No consolidated M3 discovery decision requires:

```text
database schema change
Alembic migration
new runtime dependency
lockfile change
new business resource
new public route
```

The expected M3 change remains bounded to application/persistence/HTTP/CLI correctness and simplification over the existing durable model.

## AS-IS traceability

The final mapping from M3 discovery outcomes to current architecture owners is in [`wip/discovery-closure.md`](wip/discovery-closure.md).

The current delivered AS-IS under `docs/architecture/` remains the only semantic authority until M3 completes its contract, architecture, implementation and acceptance gates.

## Remaining gates

Before M3 implementation may begin, the cycle must proceed in the project-governed order:

```text
DISCOVERY COMPLETE
    -> milestone contract FINAL / FROZEN
    -> M3 architecture set FINAL / FROZEN
    -> required consistency review / closure
    -> implementation steps FINAL / FROZEN
    -> explicit implementation authorization in this status
```

`steps.md` remains a pre-implementation placeholder. No `M3-Snn` slice is currently defined or active.

## Current discovery boundary

The completed discovery boundary remains exactly:

1. CLI post-create correctness and local post-success processing.
2. Complete review of every public business GET/read path.
3. Public `parent_template_id = null` root-only filter carrier across HTTP, cursor identity and CLI.

No general lock-plan redesign, broad mutation-lock minimization, new model capability, unrelated schema redesign or unrelated CLI redesign was added.

## Immediate next action

Prepare and review the **M3 milestone contract** from the consolidated discovery inputs.

Software implementation remains NOT AUTHORIZED.