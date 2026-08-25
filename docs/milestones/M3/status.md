# M3 — Milestone Status

**Milestone status:** ACTIVE — ARCHITECTURE FREEZE APPROVAL PENDING

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
phase                    ARCHITECTURE DESIGN COMPLETE
consistency review       PASS
next gate                EXPLICIT ARCHITECTURE FREEZE DECISION
contract                 FINAL / FROZEN
architecture set         DESIGN COMPLETE — CONSISTENCY PASS — NOT FROZEN
implementation steps     NOT YET FROZEN
active implementation    NONE
software implementation  NOT AUTHORIZED
blockers                 none for architecture freeze decision
```

All eight planned architecture design points are closed and the dedicated consistency review passed with zero open findings. This does not create implementation authority. The architecture set requires explicit project-owner freeze approval before it may become `FINAL / FROZEN`; `steps.md` remains a later independent gate.

Consistency review:

```text
report                   docs/milestones/M3/wip/architecture-consistency-closure.md
status                   PASS
findings                 2 / 2 CLOSED
open architecture finding 0
contract reopening       NOT REQUIRED
```

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

- [`architecture/README.md`](architecture/README.md) — `DESIGN COMPLETE — CONSISTENCY REVIEW PASSED — FREEZE APPROVAL PENDING — NOT FROZEN`.

Current TO-BE owners:

```text
architecture/read-projections.md
    ADP-01 CLOSED
    ADP-02 CLOSED — 22 / 22 routes
    ADP-03 CLOSED

architecture/api.md
    ADP-04 CLOSED — 12 / 12 cursor routes
    ADP-05 CLOSED

architecture/cli.md
    ADP-06 CLOSED
    ADP-07 CLOSED — 8 / 8 create Location templates

architecture/verification.md
    ADP-08 CLOSED
    M3-VER-01 .. M3-VER-19 DESIGNED
```

## Architecture design-point status

```text
ADP-01  CLOSED   read projection responsibility / persistence boundary
ADP-02  CLOSED   complete 22-route one-statement projection matrix — 22 / 22
ADP-03  CLOSED   historical lifecycle trusted decoder
ADP-04  CLOSED   cursor identity realization — 12 / 12
ADP-05  CLOSED   ObjectTemplate nullable HTTP query carrier
ADP-06  CLOSED   CLI nullable selector/query carrier
ADP-07  CLOSED   CLI Location materialization grammar — 8 / 8 creates
ADP-08  CLOSED   verification architecture — 19 / 19 AC bundles designed
```

Progress:

```text
closed design points       8 / 8
open design points         0 / 8
GET route coverage        22 / 22 CLOSED
cursor route coverage     12 / 12 CLOSED
HTTP parent tri-state     CLOSED
CLI parent tri-state      CLOSED
CLI create Location        8 / 8 CLOSED
verification bundles      19 / 19 DESIGNED
consistency review         PASS
open architecture findings 0
```

## Architecture closure to date

### Public read boundary

All 22 canonical public business GET/read targets have one complete one-statement logical projection under an ordinary read UoW / PostgreSQL statement snapshot and no target dependence on `coherent_read()`.

Historical lifecycle reads have a decoding-only boundary: typed historical carrier materialization remains; mutation-transition semantic recertification and live-state reinterpretation are removed from the read target while write validation remains strong.

### Cursor boundary

Cursor architecture preserves the delivered opaque codec v1 and complete canonical keyset tuples. The only M3 cursor identity corrections are:

```text
GET /objects/{parent_object_id}/components
    -> include parent_object_id

GET /objects/{object_id}/relationships
    -> include object_id
```

ObjectTemplate omitted/root-only/exact-parent states remain distinct through internal `parent_filter_set`. Global/Object-scoped lifecycle remain distinct through `involving_object_id`. `limit` remains excluded from semantic cursor identity.

### ObjectTemplate parent-filter carrier

HTTP:

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

Malformed/unsupported/repeated query carriers remain `400 invalid_request`; `parent_filter_set` is not public.

CLI:

```text
omitted
    -> no selector target
    -> no query pair

UUID or accepted ObjectTemplate human selector
    -> normal selector resolution
    -> exact UUID query pair

explicit null
    -> parsed None
    -> terminal nullable selector value
    -> zero selector-discovery GETs
    -> parent_template_id=null query pair
```

Only the ObjectTemplate list `parent_template_id` registry parameter becomes nullable. Nullable QUERY None emits lexical `null`; nullable BODY None remains JSON null; PATH None remains invalid. `_wire_string(None)` is not introduced globally.

### CLI Location grammar

The eight existing `201 Created` Location templates remain unchanged.

```text
token grammar
    {segment(.segment)*}

lookup precedence
    exact request_values key presence
    else response JSON-object path

materializable scalar
    str
    int excluding bool

materialization
    literal {token} replacement only
    no str.format / format_map semantics

failure
    missing/repeated/mismatching actual Location
    or non-materializable expected Location
        -> cli_protocol_error
```

The three nested response identities and five flat-token cases share one common materializer. No hidden post-mutation GET is introduced, and a canonical matching 201 cannot become `cli_internal_error` because of local Location formatting.

### Verification architecture

ADP-08 freezes three distinct verification gates and 19 stable evidence bundles:

```text
M3-AC-01 -> M3-VER-01
...
M3-AC-19 -> M3-VER-19
```

Permanent evidence design includes:

```text
22 / 22 GET compatibility + real-PG one-business-statement measurement
paired read non-recertification + write-validator preservation evidence
historical lifecycle trusted-decoder positive/negative evidence
12 / 12 cursor identity/keyset matrix
HTTP/CLI parent tri-state evidence
8 / 8 CLI Location success/failure matrix
single-request committed snapshot evidence
schema/migration/dependency/lockfile non-delta evidence
machine-checkable OUT/AC/VER/owner/target traceability
```

PostgreSQL-required bundles are `BLOCKED`, not `PASS`, when the required environment is unavailable.

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

Discovery material under `wip/` remains non-normative input; the frozen contract and M3 architecture documents own the TO-BE boundary.

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

Any requested architecture change that would require one of these or another observable contract change must stop for contract review/reopen rather than being absorbed silently.

## Remaining gates

```text
contract FINAL / FROZEN                       DONE
architecture design                           DONE — 8 / 8 ADPs CLOSED
architecture consistency review               DONE — PASS
explicit architecture freeze approval         NEXT
architecture set FINAL / FROZEN               PENDING
implementation steps FINAL / FROZEN            PENDING
explicit implementation authorization          PENDING
```

`steps.md` remains a pre-implementation placeholder. No `M3-Snn` slice is defined or active.

## Immediate next action

Obtain the explicit project-owner architecture freeze decision.

If approved, the freeze publication transition must mark the four architecture owners and controller `FINAL / FROZEN`, advance `status.md` to implementation planning and leave `steps.md` not yet frozen. Software implementation remains **NOT AUTHORIZED** until the later steps freeze and explicit implementation authorization.

If changes are requested, the affected ADP(s) must be explicitly reopened before semantic edits. A contract-level contradiction requires formal contract reopening.
