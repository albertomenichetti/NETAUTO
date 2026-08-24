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
phase                    DISCOVERY
contract                 NOT YET FROZEN
architecture set         NOT YET DEFINED / NOT FROZEN
implementation steps     NOT YET FROZEN
active implementation    NONE
software implementation  NOT AUTHORIZED
blockers                 none for discovery
```

The current work remains limited to repository-based discovery and preparation of the M3 scope. No implementation slice is active and no software behavior change is authorized yet.

Discovery material is non-normative and lives under:

```text
docs/milestones/M3/wip/
```

The current discovery summary is [`wip/discovery.md`](wip/discovery.md).

## Discovery workstream status

```text
Area A — CLI post-create correctness          CLOSED
Area B — public GET/read audit                CLOSED / 22 of 22 consolidated
Area C — parent_template_id = null carrier    OPEN
```

Area A closure is documented by:

- [`wip/cli-post-create-decision.md`](wip/cli-post-create-decision.md) — reviewed defect, census and target materializer semantics;
- [`wip/cli-post-create-closure.md`](wip/cli-post-create-closure.md) — consolidated downstream planning input.

Area B closure is documented by:

- [`wip/get-read-census.md`](wip/get-read-census.md) — complete 22-route register;
- [`wip/get-read-review-closure.md`](wip/get-read-review-closure.md) — consolidated downstream planning input;
- route-specific `*-get-*-decision.md` files — detailed discovery evidence where applicable.

These closures are discovery conclusions only. They do not themselves freeze public behavior, architecture or implementation steps.

## Consolidated Area A discovery conclusion

The CLI registry exposes eight `201 Created` operations with exact `Location` validation. Three create operations use nested response-path tokens and are deterministically affected by the current common materializer defect:

```text
{datatype.id}
{object_template.id}
{relationship_definition.id}
```

The target keeps the existing registry and exact `Location` contract, defines registered tokens as request-key / response-JSON-path metadata, removes Python format grammar from the common materializer and preserves `cli_protocol_error` for genuine same-release response violations.

A canonical committed `201` response with the correct `Location` must not become `cli_internal_error` because of local materialization behavior.

No Area A decision requires a schema, migration, dependency or lockfile change.

## Consolidated GET/read discovery conclusion

The completed 22-route audit found that every canonical public business GET/read path can materialize its required public projection in one SQL statement. The target read model therefore requires no `coherent_read()` usage across this canonical GET census.

The review also consolidated these cross-cutting inputs for the later M3 contract/architecture:

```text
GETs trust persisted semantic state
request/cursor validation remains strict
path-target 404 and empty-collection distinctions remain preserved
read-side semantic re-certification is removed
historical lifecycle carrier decoding is retained without semantic transition certification
OBJ-GET-03 cursor identity must include parent_object_id
OBJ-GET-06 cursor identity must include object_id
mutation-oriented semantic validators are not globally weakened for GET convenience
```

No consolidated GET/read decision currently requires a schema, migration, dependency or lockfile change.

## Discovery gates

Before M3 implementation may begin, the cycle must establish and freeze, in the project-governed order:

```text
complete remaining discovery
    -> milestone contract
    -> M3 architecture set
    -> consistency review / closure as required
    -> implementation steps
    -> explicit implementation authorization in this status
```

Until those gates are satisfied, the delivered AS-IS under `docs/architecture/` remains the only semantic authority for existing behavior.

## Current discovery scope

The M3 discovery boundary remains three areas:

1. CLI post-create correctness and audit of local post-success processing — **CLOSED at discovery level**.
2. Complete review of every public business GET/read path — **CLOSED at discovery level**.
3. Exact verification and, if required, correction of the public `parent_template_id = null` filtering contract across HTTP, cursor identity and CLI — **OPEN**.

This list is a discovery boundary, not a frozen milestone contract. Any addition, removal or reinterpretation remains subject to contract review before implementation.

The next discovery work is Area C. `steps.md` remains a pre-implementation placeholder and no `M3-Snn` slice is authorized.
