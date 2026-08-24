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

The project owner explicitly approved the M3 contract after final review. Architecture design is the only active semantic/technical design activity. No implementation slice or software behavior change is authorized.

## Frozen contract gate

Normative contract:

- [`contract.md`](contract.md) — `FINAL / FROZEN`.

Freeze evidence:

```text
contract freeze commit   e48a81a2a7436a01644509579a02546fa777cc4a
reviewed content SHA     6f1ffd5f8e85c3bb90578db3ec2067f36df53e34
final review findings    5 / 5 CLOSED
open contract findings   0
human freeze approval    GRANTED
```

Any semantic change to frozen Scope, Non-goals, explicit deltas, outcomes or acceptance criteria requires formal contract reopening.

## Architecture set

Controller:

- [`architecture/README.md`](architecture/README.md) — `DESIGN IN PROGRESS — NOT FROZEN`.

Current TO-BE owners:

```text
architecture/read-projections.md
    DESIGN IN PROGRESS
    ADP-01 CLOSED
    ADP-02 PARTIAL — 16 / 22 routes defined
    ADP-03 OPEN

architecture/api.md
    NOT YET WRITTEN

architecture/cli.md
    NOT YET WRITTEN

architecture/verification.md
    NOT YET WRITTEN
```

## Architecture design-point status

```text
ADP-01  CLOSED   read projection responsibility / persistence boundary
ADP-02  PARTIAL  complete 22-route one-statement projection matrix — 16 / 22
ADP-03  OPEN     historical lifecycle trusted decoder
ADP-04  OPEN     cursor identity realization
ADP-05  OPEN     ObjectTemplate nullable HTTP query carrier
ADP-06  OPEN     CLI nullable selector/query carrier
ADP-07  OPEN     CLI Location materialization grammar
ADP-08  OPEN     verification architecture
```

ADP-02 route-family progress:

```text
DataType             4 / 4 CLOSED
ObjectTemplate       6 / 6 CLOSED
Object               6 / 6 CLOSED
RelationshipDef      0 / 4 OPEN
Relationship         0 / 1 OPEN
Global lifecycle     0 / 1 OPEN
------------------------------
total               16 / 22
```

Current projection vocabulary in [`architecture/read-projections.md`](architecture/read-projections.md):

```text
RP-01  DIRECT PAGE
RP-02  DIRECT EXACT
RP-03  PARENT-ROOTED PAGE
RP-04  EXACT AGGREGATE / INDEPENDENT CHILD SETS
RP-05  RECURSIVE EXACT-CHAIN PROJECTION
RP-06  RECURSIVE STABLE-ANCESTRY PAGE
RP-07  TARGET-ROOTED CONTEXT-COMPLETED PAGE
RP-08  TARGET-ROOTED OPTIONAL PROJECTION
```

Key closed Object-family rules include:

```text
components
    -> exact-chain context completes slot_declaring_template_id
    -> unmaterializable required context fails; it is not silently omitted

owner
    -> absent child = 404
    -> detached existing child = 200 null
    -> an existing ownership fact must materialize its declaring slot

relationships
    -> public semantic-view deduplication precedes public keyset/limit semantics
```

Mutation validators remain intact. `coherent_read()` remains infrastructure but is not a target dependency for the canonical M3 public GET census.

## Frozen contract outcomes to realize

```text
M3-OUT-01 .. M3-OUT-08
M3-AC-01  .. M3-AC-19
M3-CQG-01 .. M3-CQG-08
```

M3 remains bounded to:

1. CLI post-create correctness and `Location` response processing.
2. Public business GET/read responsibility, projection compatibility and cursor correctness.
3. Public `parent_template_id = null` root-only filter carrier across HTTP and official CLI.

The one-business-statement target for all 22 canonical GET/read routes is an architecture/verification obligation, not an additional public-contract delta.

## Discovery closure

All bounded discovery workstreams remain closed:

```text
Area A — CLI post-create correctness          CLOSED
Area B — public GET/read audit                CLOSED / 22 of 22
Area C — parent_template_id = null carrier    CLOSED
```

Discovery files under `wip/` remain non-normative evidence. The frozen contract owns the milestone outcome boundary.

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

Any architecture proposal requiring one of these enters STOP for contract review/reopen.

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

Continue **ADP-02** with the four RelationshipDefinition GET/read routes, then factual Relationship exact GET and global lifecycle page.

Software implementation remains **NOT AUTHORIZED**.