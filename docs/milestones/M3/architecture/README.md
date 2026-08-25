# M3 — Architecture Set

**Architecture set status:** DESIGN COMPLETE — CONSISTENCY REVIEW PASSED — FREEZE APPROVAL PENDING — NOT FROZEN

**Authority:** M3 TO-BE ARCHITECTURE SET CONTROL

## Purpose and authority boundary

This directory defines the M3 TO-BE architecture required to realize the frozen milestone contract in [`../contract.md`](../contract.md).

The set starts from delivered AS-IS under `docs/architecture/` and changes only explicit M3 deltas. Preserved guarantees remain owned by their current AS-IS documents and must not be duplicated as competing M3 authority.

All planned M3 architecture design points are closed and the dedicated consistency review has passed. Implementation remains unauthorized until the project owner explicitly approves architecture freeze, this set becomes `FINAL / FROZEN`, `steps.md` is subsequently frozen and `status.md` explicitly authorizes a slice.

Consistency review evidence:

```text
docs/milestones/M3/wip/architecture-consistency-closure.md
status  PASS — READY FOR EXPLICIT HUMAN FREEZE DECISION
open findings  0
contract reopening  NOT REQUIRED
```

## Frozen contract inputs

```text
M3-OUT-01 .. M3-OUT-08
M3-AC-01  .. M3-AC-19
M3-CQG-01 .. M3-CQG-08
```

Primary areas:

```text
A. truthful CLI 201 / Location handling
B. public GET/read semantic-ownership correction
C. complete cursor query identity and keyset position
D. trusted historical lifecycle decoding
E. ObjectTemplate parent_template_id omitted / UUID / null carrier
F. single-request self-consistent committed read projection
```

No M3 architecture may broaden these outcomes into new routes/resources, schema/migrations, dependencies/lockfile changes, mutation-lock redesign or unrelated CLI behavior.

## Normative document map

| Document | Status | Ownership |
|---|---|---|
| [`read-projections.md`](read-projections.md) | ADP-01 / ADP-02 / ADP-03 CLOSED | GET/read responsibility, one-statement route matrix, read UoW/snapshot model, trusted lifecycle decoder boundary |
| [`api.md`](api.md) | ADP-04 / ADP-05 CLOSED | public cursor identity/keyset realization and ObjectTemplate HTTP parent tri-state |
| [`cli.md`](cli.md) | ADP-06 / ADP-07 CLOSED | nullable selector/query carrier and Location materialization grammar |
| [`verification.md`](verification.md) | ADP-08 CLOSED | deterministic architecture/acceptance evidence, stable M3-VER bundles and final evidence gates |

The four documents above are the complete planned M3 architecture owner set. Additional architecture documents may be added only through an explicitly reopened architecture design point and may not expand the frozen contract.

## Current AS-IS dependencies

Material current owners include:

```text
docs/architecture/README.md
docs/architecture/api.md
docs/architecture/cli.md
docs/architecture/datatype.md
docs/architecture/objecttemplate.md
docs/architecture/object.md
docs/architecture/relationship.md
docs/architecture/persistence.md
docs/architecture/concurrency.md
docs/architecture/verification.md
```

Every intentional M3 contradiction is a bounded TO-BE delta; every unaffected guarantee remains owned by delivered AS-IS.

## Area ownership and closure

### Public reads

Primary owner: `architecture/read-projections.md`; boundary owners: `api.md`, `verification.md`.

Closed by ADP-01 / ADP-02 / ADP-03:

```text
mutation certification vs read projection responsibility
one SQL business statement for all 22 canonical GET/read routes
ordinary read UoW / PostgreSQL statement snapshot
no target public GET dependence on coherent_read()
404 vs empty/null preservation
trusted projector boundary
complete route-specific projection-pattern matrix
historical lifecycle decoding-only boundary
no read-side lifecycle transition certification
write-side lifecycle validation remains intact
```

`coherent_read()` remains valid infrastructure outside the M3 canonical GET census and is not globally deprecated.

### Cursor correctness

Owner: `architecture/api.md`; verification owner: `architecture/verification.md`.

Closed by ADP-04:

```text
query identity = route + membership-affecting path targets + filters + semantic presence bits
position       = complete canonical ordering tuple
limit          = excluded from semantic identity
OBJ-GET-03 adds parent_object_id
OBJ-GET-06 adds object_id
lifecycle global/object scope remains distinct
ObjectTemplate omitted/root/exact-parent states remain distinct
codec v1 payload/invalid_cursor behavior preserved
```

### ObjectTemplate parent filter

HTTP owner: `architecture/api.md`; CLI owner: `architecture/cli.md`.

ADP-05 closes HTTP:

```text
HTTP omitted         -> parent_template_id=None, parent_filter_set=False
HTTP UUID            -> parent_template_id=UUID, parent_filter_set=True
HTTP lowercase null  -> parent_template_id=None, parent_filter_set=True
malformed/repeated   -> 400 invalid_request
parent_filter_set    -> internal only
```

ADP-06 closes CLI:

```text
CLI omitted          -> no query pair
CLI UUID/human       -> normal selector resolution -> UUID query pair
CLI explicit null    -> parsed None -> zero selector lookup -> lowercase null query pair
```

Nullable direct-selector handling is metadata-driven. Nullable QUERY None emits lexical `null`; nullable BODY None remains JSON null; PATH None remains invalid. The generic scalar serializer is not broadened to accept None.

### CLI post-create

Owner: `architecture/cli.md`; verification owner: `architecture/verification.md`.

Closed by ADP-07:

```text
Location template = tiny NETAUTO registry DSL, not Python format syntax
request exact-key presence has precedence over response fallback
response fallback = dot-separated JSON-object traversal
materializable token = str or int excluding bool
literal {token} replacement only
unresolvable/non-scalar expected token -> cli_protocol_error
actual Location count must equal one and match exactly
all eight registered 201 operations covered
no hidden post-mutation GET
```

### Verification

Owner: `architecture/verification.md`.

Closed by ADP-08:

```text
three gates: architecture design / implementation slice / final acceptance
19 stable bundles M3-VER-01 .. M3-VER-19
one bundle per M3-AC-01 .. M3-AC-19
machine-checkable OUT / AC / VER / owner / target traceability
22 / 22 real-PostgreSQL one-business-statement disposition
paired read-simplification + mutation-validation preservation evidence
trusted lifecycle positive/negative decoding evidence
12 / 12 cursor matrix plus explicit M3 regressions
HTTP + CLI ObjectTemplate parent tri-state evidence
8 / 8 CLI 201 Location matrix
schema/migration/dependency/lockfile non-delta evidence
single-request committed snapshot evidence
```

A missing required PostgreSQL environment yields `BLOCKED`, never `PASS`.

## Design-point status

```text
ADP-01  CLOSED   read projection responsibility / persistence boundary
ADP-02  CLOSED   one-statement projection matrix — 22 / 22 routes
ADP-03  CLOSED   historical lifecycle trusted decoder
ADP-04  CLOSED   cursor identity realization — 12 / 12 routes
ADP-05  CLOSED   ObjectTemplate nullable HTTP query carrier
ADP-06  CLOSED   CLI nullable selector/query carrier
ADP-07  CLOSED   CLI Location materialization grammar — 8 / 8 creates
ADP-08  CLOSED   verification architecture — 19 / 19 AC bundles
```

Current progress:

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
next governance work       EXPLICIT ARCHITECTURE FREEZE DECISION
```

## Closed architecture summary

```text
ADP-01  responsibility boundary
ADP-02  22-route one-statement projection matrix
ADP-03  trusted historical lifecycle decoder
ADP-04  12-route cursor identity realization
ADP-05  HTTP parent_template_id omitted/UUID/null carrier
ADP-06  CLI nullable selector/query carrier
ADP-07  CLI Location materialization DSL
ADP-08  deterministic verification architecture
```

No implementation authority is created by design-point closure or consistency PASS.

## Architecture design rules

```text
public contract outcome
    != architecture realization
    != local implementation decomposition

request validation
    != persisted semantic certification
    != representational decoding

cursor query identity
    != keyset position
    != page limit

public lexical carrier
    != internal semantic presence bit

CLI parsed explicit null
    != omitted parameter
    != arbitrary None scalar

Location registry token
    != Python formatting expression

verification design DESIGNED
    != implementation evidence PASS

current AS-IS ownership
    != M3 TO-BE delta ownership
```

## Consistency / freeze gate

Consistency review result:

```text
all planned owner documents present                         PASS
ADP-01 .. ADP-08 all CLOSED                                PASS
all M3 outcomes/ACs/CQGs have architecture/AS-IS paths     PASS
22 / 22 GET projection dispositions consistent             PASS
12 / 12 cursor identity/keyset dispositions consistent     PASS
HTTP and CLI parent-filter carriers consistent              PASS
CLI Location grammar covers all 8 registered 201 ops       PASS
19 / 19 ACs map to stable verification bundles             PASS
cross-document responsibility boundaries consistent        PASS
normative TODO/TBD/open semantic statement                  0
open architecture finding                                   0
contract contradiction                                      0
required formal reopen                                      0
```

Architecture freeze still requires explicit project-owner approval.

Until that approval and publication transition:

```text
ARCHITECTURE SET = DESIGN COMPLETE — CONSISTENCY REVIEW PASSED — NOT FROZEN
IMPLEMENTATION   = NOT AUTHORIZED
```

## Immediate next action

Request the explicit project-owner architecture freeze decision.

If approved, the dedicated freeze publication transition must:

```text
mark read-projections.md FINAL / FROZEN
mark api.md FINAL / FROZEN
mark cli.md FINAL / FROZEN
mark verification.md FINAL / FROZEN
mark architecture/README.md ARCHITECTURE SET = FINAL / FROZEN
update status.md to implementation planning
update steps.md prerequisite state to architecture FINAL / FROZEN
leave steps.md NOT YET FROZEN
leave software implementation NOT AUTHORIZED
```

If architecture changes are requested instead, the affected ADP(s) must be explicitly reopened; the frozen contract must not be silently reinterpreted.

## Reopen discipline

If a requested architecture change discovers that the frozen contract is contradictory or insufficient to determine an observable outcome, stop the affected freeze path and request formal contract reopening. Architecture must not repair a contract-level gap by silently changing semantics.