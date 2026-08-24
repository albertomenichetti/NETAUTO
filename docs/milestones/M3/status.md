# M3 — Milestone Status

**Milestone status:** ACTIVE — ARCHITECTURE DESIGN

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
phase                    ARCHITECTURE DESIGN
contract                 FINAL / FROZEN
architecture set         DESIGN IN PROGRESS — NOT FROZEN
implementation steps     NOT YET FROZEN
active implementation    NONE
software implementation  NOT AUTHORIZED
blockers                 none for architecture design
```

The project owner explicitly approved the M3 contract after final review. The contract is now frozen and architecture design is the only active semantic/technical design activity.

No implementation slice or software behavior change is authorized yet.

## Frozen contract gate

Normative contract:

- [`contract.md`](contract.md) — `FINAL / FROZEN`.

Freeze publication:

```text
contract freeze commit   e48a81a2a7436a01644509579a02546fa777cc4a
reviewed content SHA     6f1ffd5f8e85c3bb90578db3ec2067f36df53e34
final review findings    5 / 5 CLOSED
open contract findings   0
human freeze approval    GRANTED
```

Final review evidence:

- [`wip/contract-final-review.md`](wip/contract-final-review.md) — `PASS — READY FOR EXPLICIT HUMAN FREEZE DECISION`; the subsequent human decision was approval.

Any semantic change to frozen contract Scope, Non-goals, explicit deltas, outcomes or acceptance criteria now requires formal contract reopening.

## Architecture set

Architecture control document:

- [`architecture/README.md`](architecture/README.md) — `DESIGN IN PROGRESS — NOT FROZEN`.

Planned TO-BE owners:

```text
architecture/read-projections.md
    public read responsibility
    22-route one-statement projection architecture
    read UoW/snapshot realization
    trusted lifecycle/read projectors

architecture/api.md
    public cursor identity/keyset realization
    ObjectTemplate parent_template_id HTTP tri-state

architecture/cli.md
    Location value-path materialization
    nullable selector/query carrier semantics

architecture/verification.md
    deterministic M3 architecture and acceptance evidence
```

These owning documents are not yet written and therefore create no frozen design authority yet.

## Open architecture design points

The architecture set currently tracks:

```text
ADP-01  read projection responsibility / persistence boundary
ADP-02  complete 22-route one-statement projection matrix
ADP-03  historical lifecycle trusted decoder
ADP-04  cursor identity realization
ADP-05  ObjectTemplate nullable HTTP query carrier
ADP-06  CLI nullable selector/query carrier
ADP-07  CLI Location materialization grammar
ADP-08  verification architecture
```

All are OPEN. Architecture cannot freeze until all are closed and cross-document consistency passes.

## Frozen contract outcomes to realize

```text
M3-OUT-01 .. M3-OUT-08
M3-AC-01  .. M3-AC-19
M3-CQG-01 .. M3-CQG-08
```

The architecture must remain bounded to:

1. CLI post-create correctness and `Location` response processing.
2. Public business GET/read responsibility, projection compatibility and cursor correctness.
3. Public `parent_template_id = null` root-only filter carrier across HTTP and official CLI.

The one-business-statement target for all 22 canonical GET/read routes is an architecture/verification obligation, not an additional public-contract delta.

## Discovery closure

All bounded discovery workstreams remain closed:

```text
Area A — CLI post-create correctness          CLOSED
Area B — public GET/read audit                CLOSED / 22 of 22 consolidated
Area C — parent_template_id = null carrier    CLOSED
```

Primary discovery navigation/evidence:

- [`wip/discovery.md`](wip/discovery.md)
- [`wip/discovery-closure.md`](wip/discovery-closure.md)
- [`wip/cli-post-create-closure.md`](wip/cli-post-create-closure.md)
- [`wip/get-read-review-closure.md`](wip/get-read-review-closure.md)
- [`wip/cursor-identity-audit.md`](wip/cursor-identity-audit.md)
- [`wip/parent-template-null-carrier-closure.md`](wip/parent-template-null-carrier-closure.md)

These files are non-normative inputs. The frozen contract now owns the milestone outcome boundary.

## Scope impact

The frozen M3 contract requires no:

```text
database schema change
Alembic migration
new runtime dependency
runtime lockfile change
new business resource
new public route
```

Any architecture proposal that requires one of these would contradict the current frozen contract and must stop for explicit contract review/reopen.

## Remaining gates

Before implementation may begin:

```text
contract FINAL / FROZEN                       DONE
    -> architecture design                    ACTIVE
    -> architecture consistency closure       PENDING
    -> architecture set FINAL / FROZEN        PENDING
    -> implementation steps FINAL / FROZEN    PENDING
    -> explicit implementation authorization  PENDING
```

`steps.md` remains a pre-implementation placeholder. No `M3-Snn` slice is defined or active.

## Immediate next action

Begin architecture design from [`architecture/README.md`](architecture/README.md), closing its open design points dependency-first.

Software implementation remains **NOT AUTHORIZED**.
