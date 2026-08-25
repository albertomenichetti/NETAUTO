# M3 — Milestone Status

**Milestone status:** ACTIVE — IMPLEMENTATION AUTHORIZATION — M3-S05 COMPLETED / M3-S06 PENDING

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
phase                    IMPLEMENTATION AUTHORIZATION
contract                 FINAL / FROZEN
architecture set         FINAL / FROZEN
architecture review      PASS
architecture approval    GRANTED
implementation steps     FINAL / FROZEN
steps review             PASS
steps approval           GRANTED
active implementation    NONE
software implementation  NOT AUTHORIZED
blockers                 none for M3-S06 authorization decision
```

`M3-S00`, `M3-S01`, `M3-S02`, `M3-S03`, `M3-S04`, and `M3-S05` are reviewer-owned `COMPLETED`. No later slice is authorized. Software implementation may resume only after this file explicitly authorizes the next exact slice.

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
```

The corrected candidate closes both reviewer findings. A persisted `required=true / migration_default=NULL` property is treated as a representable semantic surprise and projects normally through exact and effective-schema GETs, while new invalid mutations remain rejected. `RP-05` recursion keys its termination guard on exact `(template_id, version)` node identity; `RP-06` remains a separate stable-lineage ancestry projection. The original S03 execution aid and review-fix aid were removed from active `wip/`; Git retains their history.

## M3-S04 reviewer completion

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
```

The reviewed implementation realizes all six frozen Object read shapes with ordinary read UoWs and exactly one authoritative business SQL statement each. `OBJ-GET-02` projects intrinsic Object state without transitive ObjectTemplate/DataType recertification. `OBJ-GET-03` and `OBJ-GET-04` use exact template-version context only to materialize mandatory slot declaration identity. `OBJ-GET-05` uses the shared ADP-03 representational decoder and a target-rooted one-statement Object-scoped lifecycle page. `OBJ-GET-06` projects Object-relative Relationship views directly from persisted factual/runtime/Resolution state and performs public semantic `DISTINCT` before keyset/order/limit.

The two S04 cursor repairs are complete: `object_components` binds `parent_object_id`, and `object_relationships` binds `object_id`, without changing cursor codec v1. The completed S04 execution aid was removed from active `wip/`; Git retains its history.

## M3-S05 reviewer completion

Reviewer result:

```text
slice                     M3-S05 — RelationshipDefinition, Relationship and lifecycle trusted reads
review outcome            COMPLETED
candidate commit          8f37e1aa07589551ba0d35da2119a914df8b3014
primary evidence          M3-VER-07 / M3-VER-08 / M3-VER-13 — PASS
supporting S05 targets    M3-VER-04/05/06/09/12/19 — PASS where assigned
global M3-VER bundles     NOT YET CLOSED — integrated closure remains M3-S06
business SQL statements   RD-GET-01..04 / REL-GET-01 / LC-GET-01 = 1 / 1 / 1 / 1 / 1 / 1 on PostgreSQL 16.15
trusted-read boundary     PASS — representable persisted/history surprises readable; materially undecodable required historical carriers -> bounded 500
lifecycle cursor scope    PASS — global/Object scopes and Object A/B identities are mutually incompatible; same-scope changed-limit continuation preserved
mutation regressions      PASS — RelationshipDefinition/Relationship/lifecycle write validation remains active
accepted M3 regressions   M3-S00 .. M3-S04 PASS
candidate gates           PASS — 979 full-suite tests; 700 non-PostgreSQL tests; Ruff/Pyright/build/locked sync/lock/collection PASS
review findings           0
contract reopen           NOT REQUIRED
architecture reopen       NOT REQUIRED
steps reopen              NOT REQUIRED
M3-S06                    NOT AUTHORIZED
```

The reviewed implementation realizes the four frozen RelationshipDefinition read projections, exact factual Relationship projection, and global lifecycle projection with ordinary read UoWs and exactly one authoritative business SQL statement each. RelationshipDefinition list paging is root-first so Resolution child cardinality cannot truncate public roots; exact and nested version reads preserve parent/exact-child/empty distinctions. GET-side aggregate/default/history semantic recertification is removed while persisted typed fields and required property carriers remain materialized deterministically.

Exact Relationship GET now projects persisted factual state and deduplicated public `views[]` directly from `relationships`, runtime Resolution facts, and persisted Resolution names. It no longer calls the mutation-owned `_validated()` aggregate path. Persisted JSON-object facts that are representable by the public DTO remain readable; mutation topology/schema/property validation remains active on write paths.

Global lifecycle GET now uses an ordinary read UoW and the same ADP-03 trusted historical decoder already used by the Object-scoped route. `M3-VER-08` covers both intrinsic and Relationship historical semantic surprises; `M3-VER-07` covers materially undecodable required intrinsic and Relationship historical carriers with bounded `internal_error`; `M3-VER-13` closes global/Object-scoped and Object-A/Object-B cursor-scope incompatibility while preserving same-scope continuation and changed-limit compatibility.

With S05 accepted, the production implementation of the frozen trusted-read architecture now covers all **22 / 22 canonical GET routes**. This does not close the integrated cross-route M3 bundles: the exact 22-route/12-cursor censuses, cross-route coherence/non-drift and traceability closure remain owned by `M3-S06`.

No schema, migration, dependency, lockfile, project-version, public route, DTO, or cursor-codec change is part of M3-S05. The completed S05 execution aid has been removed from active `wip/`; Git retains its history.

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

The accepted S05 candidate introduced none of those changes.

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
explicit M3-S06 implementation authorization  PENDING
M3-S06 .. M3-S07 execution/review              BLOCKED BY DEPENDENCIES / NOT AUTHORIZED
final M3 acceptance                            PENDING
```

## Immediate next action

Make a separate explicit operational decision on whether to authorize `M3-S06 — Integrated read/cursor/coherence/non-drift/traceability closure` as the next implementation slice.

Software implementation is **NOT AUTHORIZED** until this status file is deliberately transitioned to authorize that exact slice.
