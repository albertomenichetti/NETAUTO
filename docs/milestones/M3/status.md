# M3 — Milestone Status

**Milestone status:** ACTIVE — IMPLEMENTATION — M3-S05 CANDIDATE READY FOR REVIEW

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
active implementation    M3-S05 — CANDIDATE READY FOR REVIEW
software implementation  AUTHORIZED — M3-S05 ONLY
blockers                 none
```

`M3-S00`, `M3-S01`, `M3-S02`, `M3-S03`, and `M3-S04` are reviewer-owned `COMPLETED`. Software implementation is authorized only for `M3-S05 — RelationshipDefinition, Relationship and lifecycle trusted reads`. No later slice may begin before its predecessor is reviewer-owned `COMPLETED` and this file explicitly authorizes the next exact slice.

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

## M3-S00 reviewer completion

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
```

The reviewed implementation realizes the frozen ADP-07 Location DSL, exact single-Location validation, eight-operation create evidence, interactive/non-interactive truthfulness, and no hidden post-mutation GET. The completed S00 execution aid was removed from active `wip/`; Git retains its history.

## M3-S01 reviewer completion

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
```

The reviewed implementation realizes the frozen HTTP/CLI omitted / UUID / lowercase-`null` tri-state and internal cursor presence-bit distinction without changing persistence semantics or cursor codec v1. The completed S01 execution aid was removed from active `wip/`; Git retains its history.

## M3-S02 reviewer completion

```text
slice                     M3-S02 — DataType trusted one-statement read projections
review outcome            COMPLETED
candidate commit          dbd5f7aa5c8c1bfaffca892182e0cf47338f6936
assigned evidence         DataType targets for M3-VER-04/05/06/09/12/19 — PASS
M3-VER-07 DataType target NOT APPLICABLE — delivered schema closes mandatory carriers
exclusive primary bundle NONE — by frozen decomposition
global M3-VER bundles     NOT YET CLOSED
business SQL statements   DT-GET-01..04 = 1 / 1 / 1 / 1 on PostgreSQL 16.15
candidate gates           PASS
review findings           0
contract reopen           NOT REQUIRED
architecture reopen       NOT REQUIRED
steps reopen              NOT REQUIRED
```

The reviewed implementation realizes DataType `RP-01`, `RP-02`, and `RP-03` trusted reads, removes GET-side default publication recertification and `coherent_read()` dependence, preserves parent 404 versus empty-page behavior, and leaves mutation semantic validation active. The completed S02 execution aid was removed from active `wip/`; Git retains its history.

## M3-S03 reviewer completion

Reviewer result:

```text
slice                     M3-S03 — ObjectTemplate trusted recursive and aggregate read projections
review outcome            COMPLETED
initial candidate         2f287723703d33f2531328d8b85511603f881590
review findings record    1e955f2a9c42f2bd27167635b2774f1f0cd952f9
corrected candidate       24e80fb80d6d7b6adfb8a1f212094df33716a960
review findings           2 / 2 CLOSED — S03-RF-01 / S03-RF-02
assigned evidence         ObjectTemplate targets for M3-VER-04/05/06/09/12/19 — PASS
M3-VER-07 ObjectTemplate  NOT APPLICABLE — schema/DTO make nullable migration-default materializable
affected regression       M3-VER-14 .. M3-VER-16 — PASS
global M3-VER bundles     NOT YET CLOSED
business SQL statements   OT-GET-01..06 = 1 / 1 / 1 / 1 / 1 / 1 on PostgreSQL 16.15
candidate gates           PASS
contract reopen           NOT REQUIRED
architecture reopen       NOT REQUIRED
steps reopen              NOT REQUIRED
M3-S04                    COMPLETED
```

The corrected candidate closes both reviewer findings. A persisted `required=true / migration_default=NULL` property is treated as a representable semantic surprise and projects normally through exact and effective-schema GETs, while new invalid mutations remain rejected. `RP-05` recursion keys its termination guard on exact `(template_id, version)` node identity; `RP-06` remains a separate stable-lineage ancestry projection. The original S03 execution aid and review-fix aid were removed from active `wip/`; Git retains their history.

## M3-S04 reviewer completion

Reviewer result:

```text
slice                     M3-S04 — Object trusted projections and path-target cursor repairs
review outcome            COMPLETED
candidate commit          1a8245e35efc44306079fca9dd201cd397e54ead
primary evidence          M3-VER-10 / M3-VER-11 — PASS
supporting Object targets M3-VER-04/05/06/07/08/09/12/13/19 — PASS where assigned
business SQL statements   OBJ-GET-01..06 = 1 / 1 / 1 / 1 / 1 / 1 on PostgreSQL 16.15
context failure boundary  PASS — components/owner missing declaration -> bounded 500
Object lifecycle ADP-03   PASS — trusted semantic surprise + materially undecodable carrier
mutation regressions      PASS — Object/ownership/Relationship semantic validation
accepted M3 regressions   M3-S00 .. M3-S03 PASS
global M3-VER bundles     NOT YET CLOSED
candidate gates           PASS — full repository suite 973 passed
review findings           0
contract reopen           NOT REQUIRED
architecture reopen       NOT REQUIRED
steps reopen              NOT REQUIRED
M3-S05                    READY / AUTHORIZED
```

The reviewed implementation realizes all six frozen Object read shapes with ordinary read UoWs and exactly one authoritative business SQL statement each. `OBJ-GET-02` now projects intrinsic Object state without transitive ObjectTemplate/DataType recertification. `OBJ-GET-03` and `OBJ-GET-04` use the parent Object's exact template-version chain only to materialize the mandatory `slot_declaring_template_id`, preserving parent/child absence, empty/null states, and bounded internal failure when required declaration context is missing or ambiguous.

The two S04 cursor repairs are complete. `object_components` now binds `parent_object_id` in semantic cursor identity while retaining `child_object_id` as the position key; `object_relationships` now binds `object_id` while retaining the complete `(relationship_id, destination_object_id, name)` position key. Cross-parent and cross-Object reuse are rejected as `invalid_cursor`, and same-target continuation with changed limit remains valid.

`OBJ-GET-05` uses the shared ADP-03 representational decoder and a target-rooted one-statement Object-scoped lifecycle page. Historical semantic surprises that remain DTO-decodable are readable; materially undecodable required carriers fail through bounded `internal_error`. The shared decoder correction is allowed by the frozen S04 scope, while the global lifecycle route's query/UoW shape remains unchanged and its completion remains owned by M3-S05.

`OBJ-GET-06` projects Object-relative Relationship views directly from persisted factual/runtime/Resolution state, removes `_validated_many()` recertification, performs public semantic `DISTINCT` before keyset/order/limit, and preserves path-target 404 versus successful empty-page behavior. Exact Relationship GET behavior remains unchanged for M3-S05.

No schema, migration, dependency, lockfile, project-version, public route, DTO, or cursor-codec change is part of M3-S04. The completed S04 execution aid has been removed from active `wip/`; Git retains its history.

## M3-S05 implementation candidate

```text
authorized slice          M3-S05 — RelationshipDefinition, Relationship and lifecycle trusted reads
slice state               CANDIDATE READY FOR REVIEW
human authorization       GRANTED
predecessor               M3-S04 — COMPLETED
primary evidence          M3-VER-07 / M3-VER-08 / M3-VER-13 — PASS
supporting S05 targets    M3-VER-04/05/06/09/12/19 — PASS
global M3-VER bundles     NOT YET CLOSED
business SQL statements   RD-GET-01..04 / REL-GET-01 / LC-GET-01 = 1 / 1 / 1 / 1 / 1 / 1 on PostgreSQL 16.15
trusted-read boundary     PASS — representable history readable; materially undecodable required carriers -> bounded 500
cursor scope / continuity PASS — changed limit allowed; cross-target/filter misuse rejected
mutation regressions      PASS — semantic validation remains active on write paths
accepted M3 regressions   M3-S00 .. M3-S04 PASS
candidate gates           PASS — 979 collected; 700 non-PostgreSQL and 979 full-suite tests passed
review outcome            PENDING — reviewer-owned
later slices              NOT AUTHORIZED
```

The candidate realizes all six frozen S05 read shapes with ordinary read UoWs and exactly one authoritative business SQL statement each. RelationshipDefinition aggregate and version projections preserve parent/exact-child/empty distinctions, root-first paging, stored child ordering, historical scalar materialization, and default-pointer trust without read-side recertification. Exact Relationship GET projects persisted public views directly, deduplicates their public semantic identity, and preserves exact-target 404 versus a successful empty view set.

Global lifecycle reads now use the shared ADP-03 representational decoder through an ordinary one-statement read UoW. DTO-decodable historical semantic surprises remain readable, materially undecodable required carriers fail through bounded `internal_error`, and global/Object-scoped cursor identities remain mutually non-interchangeable. Mutation-side aggregate validation and deterministic concurrency evidence remain active.

No schema, migration, dependency, lockfile, project-version, public route, DTO, or cursor-codec change is part of M3-S05. Reviewer-owned `COMPLETED` remains a separate decision.

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

M3-S05 must preserve these non-deltas.

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
explicit M3-S05 implementation authorization  DONE — M3-S05 ONLY
M3-S05 execution/review                        CANDIDATE READY FOR REVIEW — REVIEW PENDING
M3-S06 .. M3-S07 execution/review              BLOCKED BY DEPENDENCIES / NOT AUTHORIZED
final M3 acceptance                            PENDING
```

## Immediate next action

Reviewer: inspect the M3-S05 candidate and its recorded evidence, then accept it or issue bounded review findings under the active slice.

Do not start M3-S06. The implementer produces a candidate and reports verified evidence; the reviewer alone may mark M3-S05 `COMPLETED` and authorize the next slice.
