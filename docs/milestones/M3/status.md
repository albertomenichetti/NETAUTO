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

The project owner explicitly approved the M3 contract after final review. The contract is frozen and architecture design is the only active semantic/technical design activity.

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

- [`wip/contract-final-review.md`](wip/contract-final-review.md) — final review PASS; the subsequent human decision was approval.

Any semantic change to frozen contract Scope, Non-goals, explicit deltas, outcomes or acceptance criteria requires formal contract reopening.

## Architecture set

Architecture control document:

- [`architecture/README.md`](architecture/README.md) — `DESIGN IN PROGRESS — NOT FROZEN`.

Current TO-BE owners:

```text
architecture/read-projections.md
    DESIGN IN PROGRESS
    ADP-01 CLOSED
    ADP-02 / ADP-03 OPEN

architecture/api.md
    NOT YET WRITTEN

architecture/cli.md
    NOT YET WRITTEN

architecture/verification.md
    NOT YET WRITTEN
```

The architecture set remains non-frozen and creates no software implementation authority.

## Architecture design-point status

```text
ADP-01  CLOSED   read projection responsibility / persistence boundary
ADP-02  OPEN     complete 22-route one-statement projection matrix
ADP-03  OPEN     historical lifecycle trusted decoder
ADP-04  OPEN     cursor identity realization
ADP-05  OPEN     ObjectTemplate nullable HTTP query carrier
ADP-06  OPEN     CLI nullable selector/query carrier
ADP-07  OPEN     CLI Location materialization grammar
ADP-08  OPEN     verification architecture
```

Progress:

```text
closed  1 / 8
open    7 / 8
```

ADP-01 is owned normatively by [`architecture/read-projections.md`](architecture/read-projections.md). It freezes the application/persistence responsibility boundary for public reads:

```text
application read service
    -> request semantics / cursor validation
    -> read UoW ownership
    -> public 404 / 200 / Page classification

persistence read projector
    -> complete persisted projection on caller-owned connection
    -> target-presence evidence where required
    -> representational carrier decoding
    -> no mutation semantic certification
```

Mutation validators remain intact. `coherent_read()` remains available infrastructure but is not a target dependency for the 22 canonical M3 public GETs.

## Frozen contract outcomes to realize

```text
M3-OUT-01 .. M3-OUT-08
M3-AC-01  .. M3-AC-19
M3-CQG-01 .. M3-CQG-08
```

The architecture remains bounded to:

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

These files are non-normative inputs. The frozen contract owns the milestone outcome boundary.

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

Any architecture proposal that requires one of these contradicts the current frozen contract and must stop for explicit contract review/reopen.

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

Close **ADP-02 — Complete 22-route one-statement projection matrix** under the responsibility boundary frozen by ADP-01.

Software implementation remains **NOT AUTHORIZED**.
