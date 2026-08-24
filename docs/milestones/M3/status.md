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

The current work is limited to repository-based discovery and preparation of the M3 scope. No implementation slice is active and no software behavior change is authorized yet.

Discovery material is non-normative and lives under:

```text
docs/milestones/M3/wip/
```

The current discovery summary is [`wip/discovery.md`](wip/discovery.md).

## Discovery gates

Before M3 implementation may begin, the cycle must establish and freeze, in the project-governed order:

```text
complete discovery
    -> milestone contract
    -> M3 architecture set
    -> consistency review / closure as required
    -> implementation steps
    -> explicit implementation authorization in this status
```

Until those gates are satisfied, the delivered AS-IS under `docs/architecture/` remains the only semantic authority for existing behavior.

## Current discovery scope

The preliminary M3 discovery is organized around three bounded areas:

1. CLI post-create correctness and audit of local post-success processing.
2. Complete review of every public business GET/read path, with special attention to read-side semantic revalidation, `coherent_read()` justification and single-statement projection opportunities.
3. Exact verification and, if required, correction of the public `parent_template_id = null` filtering contract across HTTP, cursor identity and CLI.

This list is a discovery boundary, not a frozen milestone contract. Any addition, removal or reinterpretation remains subject to contract review before implementation.
