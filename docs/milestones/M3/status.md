# M3 — Milestone Status

**Milestone status:** ACTIVE — CONTRACT REVIEW

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
phase                    CONTRACT — HUMAN FREEZE REVIEW
contract                 DRAFT / REVIEW — NOT FROZEN
architecture set         NOT YET DEFINED / NOT FROZEN
implementation steps     NOT YET FROZEN
active implementation    NONE
software implementation  NOT AUTHORIZED
blockers                 explicit human contract freeze decision
```

All bounded discovery work is complete. A self-contained M3 milestone contract has been drafted and has passed the non-normative pre-freeze consistency review. The next permitted governance action is explicit human contract review/freeze or review changes.

No architecture set, implementation slice or software behavior change is authorized yet.

## Contract review state

Proposed normative contract:

- [`contract.md`](contract.md) — `DRAFT / REVIEW — NOT FROZEN`.

Pre-freeze review evidence:

- [`wip/contract-consistency-review.md`](wip/contract-consistency-review.md) — `PASS — READY FOR HUMAN FREEZE REVIEW`, zero open contract-level findings.

The review report does not freeze the contract. Human approval is required before the contract may become `FINAL / FROZEN` and architecture design may begin.

## Discovery closure

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

These discovery records remain evidence/input only. The proposed `contract.md` is self-contained and is the artifact under freeze review.

## Proposed contract outcomes

The draft freezes, if approved, the following bounded outcome set.

### Area A — CLI create correctness

```text
all 8 registered 201 Created operations retain exact Location validation
valid canonical 201 + correct Location -> CLI success
nested response identities are supported without response flattening
genuine Location mismatch -> cli_protocol_error
valid success must not become cli_internal_error due to Location processing
```

### Area B — public reads and cursors

```text
22 / 22 canonical public business GET/read routes remain the public read surface
GETs stop re-certifying mutation-owned persisted semantic invariants
strict request/cursor validation and typed carrier decoding remain
path-target 404 vs existing-target empty collection distinctions remain
historical lifecycle decoding retains representation checks without transition re-certification

cursor-bearing public routes audited      12 / 12
complete current identities               10 / 12
known incomplete identities                2 / 12
new cursor defects found                    0
keyset-key defects                          0

cursor query identity
    = route
    + every membership-affecting path target
    + every membership-affecting query filter
    + required semantic presence bits
cursor position = complete canonical ordering tuple
limit is not part of semantic query identity

OBJ-GET-03 cursor identity adds parent_object_id
OBJ-GET-06 cursor identity adds object_id
```

The discovery one-statement target for all 22 GETs remains a mandatory architecture/verification handoff and is intentionally not frozen as public contract behavior.

### Area C — ObjectTemplate root filter

```text
HTTP parent_template_id omitted -> no parent filter
HTTP parent_template_id=<UUID>  -> direct children of that parent
HTTP parent_template_id=null    -> root ObjectTemplates only

CLI omission                    -> no parent query pair
CLI UUID / human selector       -> exact UUID query pair
CLI explicit null               -> parent_template_id=null without selector lookup

parent_filter_set remains internal only
```

## Scope impact

The proposed M3 contract requires no:

```text
database schema change
Alembic migration
new runtime dependency
lockfile change
new business resource
new public route
```

M3 remains bounded to application/persistence/HTTP/CLI correctness and simplification over the delivered durable model.

## AS-IS traceability

The final discovery mapping from M3 outcomes to current architecture owners is in [`wip/discovery-closure.md`](wip/discovery-closure.md).

The proposed contract explicitly registers the delivered read-corruption/semantic-certification boundary as an intentional M3 delta rather than treating implementation behavior as authority.

The current delivered AS-IS under `docs/architecture/` remains authoritative until the M3 contract is frozen and subsequent architecture/implementation gates are completed.

## Remaining gates

Before M3 implementation may begin, the cycle must proceed in the project-governed order:

```text
contract HUMAN REVIEW
    -> contract FINAL / FROZEN
    -> M3 architecture set DESIGN / consistency closure / FINAL / FROZEN
    -> implementation steps FINAL / FROZEN
    -> explicit implementation authorization in this status
```

`steps.md` remains a pre-implementation placeholder. No `M3-Snn` slice is currently defined or active.

## Current bounded scope

M3 remains exactly:

1. CLI post-create correctness and local `Location` response processing.
2. Public business GET/read responsibility, projection compatibility and cursor correctness.
3. Public `parent_template_id = null` root-only filter carrier across HTTP and official CLI.

No general lock-plan redesign, broad mutation-lock minimization, new model capability, unrelated schema redesign or unrelated CLI redesign is included.

## Immediate next action

Human review of [`contract.md`](contract.md).

Permitted outcomes:

```text
approve freeze
    -> contract.md FINAL / FROZEN
    -> begin M3 architecture design

request changes
    -> keep contract DRAFT / REVIEW
    -> apply/close contract findings
    -> repeat consistency review as required
```

Software implementation remains NOT AUTHORIZED.
