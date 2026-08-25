# M3 — Milestone Status

**Milestone status:** ACTIVE — IMPLEMENTATION — M3-S02 CANDIDATE READY FOR REVIEW

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
phase                    IMPLEMENTATION
contract                 FINAL / FROZEN
architecture set         FINAL / FROZEN
architecture review      PASS
architecture approval    GRANTED
implementation steps     FINAL / FROZEN
steps review             PASS
steps approval           GRANTED
active implementation    M3-S02 — CANDIDATE READY FOR REVIEW
software implementation  AUTHORIZED — M3-S02 ONLY
blockers                 none
```

Contract, architecture and implementation decomposition remain frozen. `M3-S00 — Official CLI Location protocol correctness` and `M3-S01 — ObjectTemplate parent tri-state across HTTP, CLI and cursor identity` are reviewer-owned `COMPLETED`. Software implementation is authorized only for `M3-S02 — DataType trusted one-statement read projections`. No later slice may begin before its predecessor is reviewer-owned `COMPLETED` and `status.md` explicitly authorizes the next exact slice.

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

## Frozen architecture gate

Consistency review:

```text
report                    docs/milestones/M3/wip/architecture-consistency-closure.md
status                    PASS
findings                  2 / 2 CLOSED
open architecture finding 0
contract reopening        NOT REQUIRED
```

Freeze approval:

```text
record                    docs/milestones/M3/wip/architecture-freeze.md
human freeze approval     GRANTED
architecture set status   FINAL / FROZEN
```

Publication commits:

```text
read-projections owner    706dd4838a66bac16db10e6d6a983f2e39d61430
api owner                 8e25a197381b05445e0a9bc0ea395bdf976317e0
cli owner                 bcd99ab8b3d237fc178b418855309b964bac6069
verification owner        4ddcf24ed53d8265b7f0d64e0bcc2fbd6e23b35c
architecture controller   dd5593045c9a6bee5ebbf52931879bdb09441a9f
freeze approval record    8996fa1875152996dddab4d0609ed978cf50561b
```

## Frozen implementation steps gate

Decomposition owner:

```text
document                  docs/milestones/M3/steps.md
status                    FINAL / FROZEN
slice registry            M3-S00 .. M3-S07
slice count               8
```

Consistency review:

```text
report                    docs/milestones/M3/wip/steps-consistency-closure.md
status                    PASS
blocking findings         0
open findings             0
contract reopening        NOT REQUIRED
architecture reopening    NOT REQUIRED
```

Freeze approval:

```text
record                    docs/milestones/M3/wip/steps-freeze.md
human freeze approval     GRANTED
reviewed content SHA      cd8e1b904c57487f18a82cfe262135bd2b90664c
steps publication commit  dc5e5166be100e4072417b2fd516851ec0994af1
freeze approval record    45de5e4cac5be3c2e74e47cbe986b1991f9c3a9d
```

Frozen linear registry:

```text
M3-S00  Official CLI Location protocol correctness
M3-S01  ObjectTemplate parent tri-state across HTTP, CLI and cursor identity
M3-S02  DataType trusted one-statement read projections
M3-S03  ObjectTemplate trusted recursive and aggregate read projections
M3-S04  Object trusted projections and path-target cursor repairs
M3-S05  RelationshipDefinition, Relationship and lifecycle trusted reads
M3-S06  Integrated read/cursor/coherence/non-drift/traceability closure
M3-S07  Full M3 acceptance and delivery-candidate gate
```

Dependency graph:

```text
M3-S00 -> M3-S01 -> M3-S02 -> M3-S03 -> M3-S04 -> M3-S05 -> M3-S06 -> M3-S07
```

Review closure proves:

```text
GET route assignment       22 / 22 exact
cursor route path          12 / 12 exact
CLI 201 path                8 / 8 exact
M3-VER primary ownership   19 / 19 exact
open decomposition finding  0
```

## M3-S00 reviewer completion

Reviewer result:

```text
slice                     M3-S00 — Official CLI Location protocol correctness
review outcome            COMPLETED
candidate commit          7658c1d1f0e7e7c042bad94ea8258f4e91f48d09
primary evidence          M3-VER-01 .. M3-VER-03 — PASS
candidate gates           PASS
review findings           0
contract reopen           NOT REQUIRED
architecture reopen       NOT REQUIRED
steps reopen              NOT REQUIRED
M3-S01                    COMPLETED
```

The reviewed implementation conforms to the frozen ADP-07 Location DSL and preserves the delivered CLI boundary outside the authorized delta. Review confirmed the common literal materializer, exact request-key presence precedence, nested JSON-object traversal, `str` / non-boolean `int` scalar rule, exact single-Location validation, permanent eight-operation evidence, interactive/non-interactive truthfulness and absence of a hidden post-mutation GET.

The pre-existing formatter-only change in `docs/milestones/M3/wip/obj-get-06-decision.md` was explicitly authorized during M3-S00 and reviewed as non-semantic WIP layout only. It creates no M3-S00 behavior, contract or architecture delta.

The completed M3-S00 execution aid has been removed from the active `wip/` working tree in accordance with project governance. Its history remains in Git.

## M3-S01 reviewer completion

Reviewer result:

```text
slice                     M3-S01 — ObjectTemplate parent tri-state across HTTP, CLI and cursor identity
review outcome            COMPLETED
candidate commit          9ce01224893926e3a28513db0cd85b02426da67e
primary evidence          M3-VER-14 .. M3-VER-16 — PASS
candidate gates           PASS
review findings           0
contract reopen           NOT REQUIRED
architecture reopen       NOT REQUIRED
steps reopen              NOT REQUIRED
M3-S02                    READY / AUTHORIZED
```

The reviewed implementation realizes the frozen ADP-04 / ADP-05 / ADP-06 parent-filter tri-state without changing the existing application/persistence semantic owner or opaque cursor codec. Review confirmed the exact lowercase HTTP `null` carrier, preserved request-parameter presence bit, generic metadata-driven nullable direct-selector terminal rule, location-aware CLI QUERY `null` emission, unchanged BODY JSON-null behavior, PATH-None rejection, bounded human-selector discovery, and interactive/non-interactive carrier equivalence.

Permanent evidence covers HTTP omission / UUID / lowercase-null semantics and invalid lexical carriers, public-surface non-exposure of `parent_filter_set`, cursor incompatibility across omitted / root-only / exact-parent identities with successful root-only continuation, and the required CLI nullable-selector/planning invariants. No schema, migration, dependency, lockfile, DTO, route, persistence or cursor-codec change is part of M3-S01.

The completed M3-S01 execution aid has been removed from the active `wip/` working tree in accordance with project governance. Its history remains in Git.

## M3-S02 implementation authorization

```text
authorized slice          M3-S02 — DataType trusted one-statement read projections
slice state               CANDIDATE READY FOR REVIEW
human authorization       GRANTED
predecessor               M3-S01 — COMPLETED
assigned evidence         DataType targets for M3-VER-04/05/06/07/09/12/19
exclusive primary bundle  NONE — by frozen decomposition
candidate evidence        DataType targets for M3-VER-04/05/06/09/12/19 — PASS
M3-VER-07 target          NOT APPLICABLE — delivered DataType schema closes mandatory carriers
global M3-VER bundles     NOT YET CLOSED
candidate gates           PASS
later slices              NOT AUTHORIZED
```

The mandatory repository pre-flight, assigned DataType evidence and complete candidate gate passed inside the exact frozen `M3-S02` scope. All four canonical DataType GETs were measured at exactly one business SQL statement on real PostgreSQL, no DataType GET depends on `coherent_read()` or read-side mutation certification, and the paired mutation boundary remains active. The candidate is ready for reviewer inspection; reviewer-owned completion and global M3-VER bundle closure remain separate.

## Frozen architecture closure

```text
ADP-01 .. ADP-08          CLOSED — 8 / 8
GET route matrix          CLOSED — 22 / 22
cursor route matrix       CLOSED — 12 / 12
HTTP parent tri-state     CLOSED
CLI parent tri-state      CLOSED
CLI create Location       CLOSED — 8 / 8
verification bundles      DESIGNED — 19 / 19
architecture review       PASS
open architecture finding 0
```

Material frozen architecture outcomes include:

```text
public GETs trust mutation-owned semantic certification
all 22 canonical GETs target one business SQL statement / statement snapshot
historical lifecycle reads decode representational carriers without transition recertification
components cursor binds parent_object_id
Object Relationship cursor binds object_id
ObjectTemplate HTTP and CLI expose omitted / UUID / lowercase null tri-state
CLI Location templates use the frozen tiny registry DSL
19 stable M3-VER bundles own final acceptance evidence
```

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

Any implementation proposal that contradicts frozen contract, architecture or steps must stop for the applicable reopen process rather than silently altering semantics.

## Remaining gates

```text
contract FINAL / FROZEN                       DONE
architecture design                           DONE — 8 / 8
architecture consistency review               DONE — PASS
architecture set FINAL / FROZEN               DONE
implementation steps design                   DONE — M3-S00..S07
implementation steps consistency review       DONE — PASS
implementation steps FINAL / FROZEN           DONE
M3-S00 execution/review                        DONE — COMPLETED
M3-S01 execution/review                        DONE — COMPLETED
explicit M3-S02 implementation authorization  DONE — M3-S02 ONLY
M3-S02 execution/review                        CANDIDATE READY FOR REVIEW
M3-S03 .. M3-S07 execution/review              BLOCKED BY DEPENDENCIES / NOT AUTHORIZED
final M3 acceptance                            PENDING
```

## Immediate next action

Review the `M3-S02 — DataType trusted one-statement read projections` candidate and its concrete DataType evidence targets.

The implementer produces a candidate and reports verified evidence. The reviewer alone may mark `M3-S02` `COMPLETED` and authorize the transition to `M3-S03`.
