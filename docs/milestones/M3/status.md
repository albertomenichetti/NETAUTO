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

The frozen contract is authoritative. Architecture design is the only active semantic/technical design activity; no implementation slice or software behavior change is authorized.

## Frozen contract gate

```text
contract                 docs/milestones/M3/contract.md
contract status          FINAL / FROZEN
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
    ADP-02 CLOSED — 22 / 22 routes
    ADP-03 CLOSED

architecture/api.md
    DESIGN IN PROGRESS
    ADP-04 CLOSED — 12 / 12 cursor routes
    ADP-05 CLOSED

architecture/cli.md
    NOT YET WRITTEN

architecture/verification.md
    NOT YET WRITTEN
```

## Architecture design-point status

```text
ADP-01  CLOSED   read projection responsibility / persistence boundary
ADP-02  CLOSED   complete 22-route one-statement projection matrix — 22 / 22
ADP-03  CLOSED   historical lifecycle trusted decoder
ADP-04  CLOSED   cursor identity realization — 12 / 12
ADP-05  CLOSED   ObjectTemplate nullable HTTP query carrier
ADP-06  OPEN     CLI nullable selector/query carrier
ADP-07  OPEN     CLI Location materialization grammar
ADP-08  OPEN     verification architecture
```

Progress:

```text
closed design points  5 / 8
open design points    3 / 8
```

## Architecture closure to date

```text
GET projection matrix                     CLOSED — 22 / 22
historical lifecycle decoder              CLOSED
cursor identity matrix                    CLOSED — 12 / 12
ObjectTemplate HTTP parent tri-state      CLOSED
```

All 22 canonical public business GET/read targets have one complete one-statement logical projection under an ordinary read UoW / PostgreSQL statement snapshot and no target dependence on `coherent_read()`.

Historical lifecycle reads have a decoding-only boundary: typed historical carrier materialization remains; mutation-transition semantic recertification and live-state reinterpretation are removed from the read target while write validation remains strong.

Cursor architecture preserves the delivered opaque codec v1 and complete canonical keyset tuples. The only cursor identity corrections are `parent_object_id` for Object components and `object_id` for Object-relative Relationships. ObjectTemplate omitted/root-only/exact-parent states remain distinct through internal `parent_filter_set`.

ADP-05 freezes the HTTP ObjectTemplate parent filter as:

```text
omitted
    -> parent_template_id=None
    -> parent_filter_set=False

valid UUID
    -> parent_template_id=UUID
    -> parent_filter_set=True

exact lowercase null
    -> parent_template_id=None
    -> parent_filter_set=True
```

Only exact lowercase `null` receives M3 sentinel treatment; all other non-UUID values remain request-validation failures. Repeated query parameters remain `400 invalid_request`. `parent_filter_set` is not public.

## Frozen contract outcomes to realize

```text
M3-OUT-01 .. M3-OUT-08
M3-AC-01  .. M3-AC-19
M3-CQG-01 .. M3-CQG-08
```

Architecture remains bounded to:

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

Discovery material under `wip/` remains non-normative input; the frozen contract and current M3 architecture documents own the TO-BE boundary.

## Scope impact

M3 requires no:

```text
database schema change
Alembic migration
new runtime dependency
runtime lockfile change
new business resource
new public route
```

Any architecture proposal requiring one of these contradicts the frozen contract and must stop for contract review/reopen.

## Remaining gates

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

Close **ADP-06 — CLI nullable selector/query carrier** in a new [`architecture/cli.md`](architecture/cli.md).

The design must freeze metadata-driven handling for the ObjectTemplate list parameter so that:

```text
parameter omitted
    -> no parent_template_id query pair

UUID or accepted ObjectTemplate human selector
    -> normal selector resolution
    -> exact UUID query pair

explicit null
    -> nullable terminal carrier
    -> no selector lookup
    -> lexical query value "null"
```

It must not globally redefine arbitrary `None` as a valid query/path scalar: nullable QUERY None serializes `null`, nullable BODY None retains JSON null semantics, and PATH None remains invalid/impossible.

Software implementation remains **NOT AUTHORIZED**.
