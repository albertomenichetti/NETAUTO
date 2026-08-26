# M3 — Milestone Status

**Milestone status:** ACTIVE — IMPLEMENTATION — M3-S07 CANDIDATE READY FOR REVIEW

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
active implementation    M3-S07 — CANDIDATE READY FOR REVIEW
software implementation  AUTHORIZED — M3-S07 ONLY
blockers                 none
```

`M3-S00`, `M3-S01`, `M3-S02`, `M3-S03`, `M3-S04`, `M3-S05`, and `M3-S06` are reviewer-owned `COMPLETED`. The `M3-S07 — Full M3 acceptance and delivery-candidate gate` candidate is ready for reviewer inspection. No business behavior was planned or introduced in S07; the slice remained limited to the frozen final-candidate verification/evidence gate.

## Frozen governance gates

```text
contract                 docs/milestones/M3/contract.md
contract status          FINAL / FROZEN
contract freeze commit   e48a81a2a7436a01644509579a02546fa777cc4a
reviewed content SHA     6f1ffd5f8e85c3bb90578db3ec2067f36df53e34
open contract findings   0
human freeze approval    GRANTED

architecture set         docs/milestones/M3/architecture/
architecture status      FINAL / FROZEN
ADP-01 .. ADP-08         CLOSED — 8 / 8
open architecture finding 0
contract reopening       NOT REQUIRED

implementation steps     docs/milestones/M3/steps.md
steps status             FINAL / FROZEN
slice registry           M3-S00 .. M3-S07
slice count              8
open decomposition finding 0
```

Any semantic change contradicting frozen contract, architecture, or steps requires the applicable formal reopen process rather than silent implementation drift.

## Frozen implementation registry

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

Frozen architecture closure remains:

```text
GET route matrix          22 / 22
cursor route matrix       12 / 12
CLI 201 Location matrix    8 / 8
M3-VER ownership          19 / 19
HTTP parent tri-state     CLOSED
CLI parent tri-state      CLOSED
open architecture finding 0
```

## Reviewer-owned completed slices

### M3-S00

```text
slice                     M3-S00 — Official CLI Location protocol correctness
review outcome            COMPLETED
candidate commit          7658c1d1f0e7e7c042bad94ea8258f4e91f48d09
primary evidence          M3-VER-01 .. M3-VER-03 — PASS
candidate gates           PASS
review findings           0
reopen required           NO
```

### M3-S01

```text
slice                     M3-S01 — ObjectTemplate parent tri-state across HTTP, CLI and cursor identity
review outcome            COMPLETED
candidate commit          9ce01224893926e3a28513db0cd85b02426da67e
primary evidence          M3-VER-14 .. M3-VER-16 — PASS
candidate gates           PASS
review findings           0
reopen required           NO
```

### M3-S02

```text
slice                     M3-S02 — DataType trusted one-statement read projections
review outcome            COMPLETED
candidate commit          dbd5f7aa5c8c1bfaffca892182e0cf47338f6936
assigned evidence         DataType targets for M3-VER-04/05/06/09/12/19 — PASS
M3-VER-07 DataType target NOT APPLICABLE — delivered schema closes mandatory carriers
business SQL statements   DT-GET-01..04 = 1 / 1 / 1 / 1 on PostgreSQL 16.15
candidate gates           PASS
review findings           0
reopen required           NO
```

### M3-S03

```text
slice                     M3-S03 — ObjectTemplate trusted recursive and aggregate read projections
review outcome            COMPLETED
initial candidate         2f287723703d33f2531328d8b85511603f881590
review findings record    1e955f2a9c42f2bd27167635b2774f1f0cd952f9
corrected candidate       24e80fb80d6d7b6adfb8a1f212094df33716a960
review findings           2 / 2 CLOSED — S03-RF-01 / S03-RF-02
assigned evidence         ObjectTemplate targets for M3-VER-04/05/06/09/12/19 — PASS
M3-VER-07 ObjectTemplate  NOT APPLICABLE — schema/DTO make nullable migration-default materializable
business SQL statements   OT-GET-01..06 = 1 / 1 / 1 / 1 / 1 / 1 on PostgreSQL 16.15
candidate gates           PASS
reopen required           NO
```

### M3-S04

```text
slice                     M3-S04 — Object trusted projections and path-target cursor repairs
review outcome            COMPLETED
candidate commit          1a8245e35efc44306079fca9dd201cd397e54ead
primary evidence          M3-VER-10 / M3-VER-11 — PASS
supporting Object targets M3-VER-04/05/06/07/08/09/12/13/19 — PASS where assigned
business SQL statements   OBJ-GET-01..06 = 1 / 1 / 1 / 1 / 1 / 1 on PostgreSQL 16.15
candidate gates           PASS — full repository suite 973 passed
review findings           0
reopen required           NO
```

### M3-S05

```text
slice                     M3-S05 — RelationshipDefinition, Relationship and lifecycle trusted reads
review outcome            COMPLETED
candidate commit          8f37e1aa07589551ba0d35da2119a914df8b3014
primary evidence          M3-VER-07 / M3-VER-08 / M3-VER-13 — PASS
supporting S05 targets    M3-VER-04/05/06/09/12/19 — PASS where assigned
business SQL statements   RD-GET-01..04 / REL-GET-01 / LC-GET-01 = 1 / 1 / 1 / 1 / 1 / 1 on PostgreSQL 16.15
trusted-read production   22 / 22 canonical GET routes implemented
candidate gates           PASS — 979 full-suite tests; 700 non-PostgreSQL tests; Ruff/Pyright/build/locked sync/lock/collection PASS
review findings           0
reopen required           NO
```

### M3-S06

```text
slice                     M3-S06 — Integrated read/cursor/coherence/non-drift/traceability closure
review outcome            COMPLETED
implementation candidate  c13bf884b8196e256fe4e7cefd73d083660fa54e
publication commit        0cba7219b2501952de761e4bb54fc2a76eb47e5c
candidate evidence        docs/milestones/M3/evidence/M3-S06-candidate.md
primary evidence          M3-VER-04 / 05 / 06 / 09 / 12 / 17 / 18 / 19 — PASS
re-executed evidence      M3-VER-01..03 / 07..08 / 10..11 / 13..16 — PASS
all evidence bundles      M3-VER-01 .. M3-VER-19 — PASS on the S06 candidate evidence run
GET census                22 / 22 exact
cursor census             12 / 12 exact
CLI 201 census             8 / 8 exact
business SQL statements   22 / 22 = exactly one on PostgreSQL 16.15
snapshot evidence         PASS — deterministic BEFORE and AFTER committed generations
traceability              PASS — 8 OUT / 19 AC / 19 VER, owner and non-empty collected-target closure
non-drift                 PASS — compare_metadata []; one migration root/head; dependency/lock/version unchanged
production corrections    NONE
candidate gates           PASS — 990 full-suite tests; 706 non-PostgreSQL tests; Ruff/Pyright/build/locked sync/lock/collection PASS
normative skip/xfail/rerun 0 / 0 / 0
review findings           0
reopen required           NO
M3-S07                    CANDIDATE READY / AWAITS REVIEW
```

The reviewed S06 implementation adds permanent integration evidence only and introduces no production correction. The traceability registry exactly closes the frozen 8-outcome, 19-acceptance-criterion and 19-evidence-bundle sets, maps every bundle to architecture owner(s) and non-empty collected pytest targets, and exactly represents the 22 business GET routes, 12 cursor-bearing routes and 8 registered CLI `201 + Location` operations.

Integrated public evidence covers all 22 canonical GET success targets and the required request/path-target failure classes. All twelve cursor routes perform true multipage continuation with changed limit and reject incompatible route/filter/path identities and malformed keys. The real PostgreSQL observer measures exactly one authoritative business statement for each of the 22 canonical GET routes.

`M3-VER-19` additionally has deterministic real-PostgreSQL BEFORE/AFTER evidence on a multi-fragment RelationshipDefinition projection. The AFTER cut pauses immediately before the production authoritative execute, commits the writer generation and then reads the complete AFTER generation. The BEFORE cut completes the production authoritative statement, commits the writer before application return, and retains the complete BEFORE generation. The harness changes no production SQL, isolation, locking or route selection and introduces no cross-request snapshot promise.

`M3-VER-17` confirms no schema, Alembic, runtime dependency, lockfile or project-version drift. Live `compare_metadata == []`; the shipped graph remains one root/head at `0001_m2_kernel`; the authorized `pyproject.toml`, `uv.lock` and migration blob baselines are unchanged.

All `M3-VER-01 .. M3-VER-19` have passing concrete evidence on the S06 candidate run. This closes S06 integration evidence but does not constitute final M3 acceptance or authorize delivery; final candidate acceptance remains the separate frozen `M3-S07` gate. The completed S06 execution aid has been removed from active `wip/`; Git retains its history.

## M3-S07 candidate publication

```text
authorized slice          M3-S07 — Full M3 acceptance and delivery-candidate gate
slice state               CANDIDATE READY FOR REVIEW
human authorization       GRANTED
predecessor               M3-S00 .. M3-S06 — reviewer-owned COMPLETED
planned business behavior NONE
stable evidence identities none new — re-execute M3-VER-01 .. M3-VER-19
tested candidate          1f018a771227087a5c629e644d77c06879585003
candidate evidence        docs/milestones/M3/evidence/M3-S07-candidate.md
GET census                22 exact
cursor census             12 exact
CLI 201 census             8 exact
required PostgreSQL       mandatory
implementer final gate    PASS
final reviewer decision   PENDING / reviewer-owned
M3 delivery approval      NOT YET GRANTED
```

`CANDIDATE READY FOR REVIEW` records that Codex executed the complete frozen final gate against the identified immutable candidate and published implementer evidence. It does not declare M3-S07 completed or M3 delivered/accepted. Reviewer-owned `COMPLETED` and final milestone delivery approval remain separate decisions.

## Scope impact

M3 requires no:

```text
database schema change
Alembic migration
new runtime dependency
runtime lockfile change
new business resource
new public route
project-version change
cursor-codec version change
```

S07 must re-prove these non-deltas on the final candidate rather than introduce them.

## Remaining gates

```text
contract FINAL / FROZEN                       DONE
architecture FINAL / FROZEN                   DONE
implementation steps FINAL / FROZEN           DONE
M3-S00 execution/review                        DONE — COMPLETED
M3-S01 execution/review                        DONE — COMPLETED
M3-S02 execution/review                        DONE — COMPLETED
M3-S03 execution/review                        DONE — COMPLETED
M3-S04 execution/review                        DONE — COMPLETED
M3-S05 execution/review                        DONE — COMPLETED
M3-S06 execution/review                        DONE — COMPLETED
explicit M3-S07 implementation authorization  DONE — M3-S07 ONLY
M3-S07 execution/review                        CANDIDATE READY — REVIEW PENDING
final M3 acceptance                            PENDING
```

## Immediate next action

Review the exact M3-S07 candidate, its durable evidence record and candidate-state acceptance summary. Record a reviewer-owned decision before any completion or milestone-delivery transition.

Do not mark `M3-S07` `COMPLETED`, do not mark M3 `ACCEPTED`/`DELIVERED`, and do not create a PR unless separately instructed. The reviewer alone may accept the final candidate and advance milestone governance.
