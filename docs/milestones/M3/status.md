# M3 — Milestone Status

**Milestone status:** ACTIVE — IMPLEMENTATION — M3-S03 CANDIDATE READY FOR REVIEW

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
active implementation    M3-S03 — CANDIDATE READY FOR REVIEW
software implementation  AUTHORIZED — M3-S03 ONLY
blockers                 reviewer closure pending — S03-RF-01 / S03-RF-02
```

Contract, architecture and implementation decomposition remain frozen. `M3-S00 — Official CLI Location protocol correctness`, `M3-S01 — ObjectTemplate parent tri-state across HTTP, CLI and cursor identity`, and `M3-S02 — DataType trusted one-statement read projections` are reviewer-owned `COMPLETED`. Software implementation remains authorized only for bounded M3-S03 review corrections. No later slice may begin before M3-S03 is reviewer-owned `COMPLETED` and `status.md` explicitly authorizes the next exact slice.

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
M3-S02                    COMPLETED
```

The reviewed implementation realizes the frozen ADP-04 / ADP-05 / ADP-06 parent-filter tri-state without changing the existing application/persistence semantic owner or opaque cursor codec. Review confirmed the exact lowercase HTTP `null` carrier, preserved request-parameter presence bit, generic metadata-driven nullable direct-selector terminal rule, location-aware CLI QUERY `null` emission, unchanged BODY JSON-null behavior, PATH-None rejection, bounded human-selector discovery, and interactive/non-interactive carrier equivalence.

Permanent evidence covers HTTP omission / UUID / lowercase-null semantics and invalid lexical carriers, public-surface non-exposure of `parent_filter_set`, cursor incompatibility across omitted / root-only / exact-parent identities with successful root-only continuation, and the required CLI nullable-selector/planning invariants. No schema, migration, dependency, lockfile, DTO, route, persistence or cursor-codec change is part of M3-S01.

The completed M3-S01 execution aid has been removed from the active `wip/` working tree in accordance with project governance. Its history remains in Git.

## M3-S02 reviewer completion

Reviewer result:

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
M3-S03                    REVIEW CHANGES REQUIRED / AUTHORIZED
```

The reviewed implementation realizes the frozen DataType `RP-01`, `RP-02` and `RP-03` trusted-read patterns while preserving public routes, DTOs, filters, ordering, cursor identities and mutation semantic authority. Review confirmed that all four canonical DataType GETs use ordinary read UoWs, perform no `coherent_read()` dependency or default-target publication recertification, and issue exactly one authoritative business SQL statement per request on real PostgreSQL.

The parent-rooted version page carries parent-presence evidence through one LEFT JOIN whose membership filters and keyset predicate remain in the join condition, preserving missing-parent `404` separately from an existing parent with an empty filtered page. DataType lineage/exact reads now expose representable persisted facts even when those facts would fail mutation-time certification; paired mutation evidence confirms `set-default` and constraint revision validation remain active.

The legacy cross-family default-pointer corruption regression was narrowed only for the completed DataType read boundary: DataType reads now remain readable as required by M3-S02, while ObjectTemplate and RelationshipDefinition retain their pre-S03/pre-S05 internal-failure expectations. No later-family read behavior was silently migrated.

The completed M3-S02 execution aid has been removed from the active `wip/` working tree in accordance with project governance. Its history remains in Git.

## M3-S03 reviewer result

Reviewer result:

```text
slice                     M3-S03 — ObjectTemplate trusted recursive and aggregate read projections
review outcome            REVIEW CHANGES REQUIRED
reviewed candidate        2f287723703d33f2531328d8b85511603f881590
review findings           2 — S03-RF-01 / S03-RF-02
candidate SQL census      OT-GET-01..06 = 1 / 1 / 1 / 1 / 1 / 1 on PostgreSQL 16.15
candidate global bundles  NOT YET CLOSED
contract reopen           NOT REQUIRED
architecture reopen       NOT REQUIRED
steps reopen              NOT REQUIRED
M3-S04                    NOT AUTHORIZED
```

### S03-RF-01 — required migration-default absence is semantic surprise, not undecodable carrier

The candidate introduces `_projected_property()` and returns `500 internal_error` whenever a persisted property has `required=True` and `migration_default=None`. That condition is mutation-owned semantic admission, not a representational materialization requirement. The delivered schema permits the row structurally, and the public `PropertyDto` represents `migration_default` as nullable and excludes it when `None`.

Therefore a committed `required=True / migration_default=None` row is a representable persisted semantic surprise and must remain readable under the M3 trusted-read boundary. It cannot serve as the ObjectTemplate `M3-VER-07` materially-undecodable fixture.

Required correction:

```text
remove the GET-side required/migration_default semantic check
project migration_default=None normally through exact/effective GETs
add positive trusted-read evidence for the representable surprise
retain mutation-side rejection for newly submitted required properties without a default
reassess ObjectTemplate M3-VER-07 applicability
if no genuinely non-materializable mandatory public carrier exists, record NOT APPLICABLE with schema/DTO evidence
```

### S03-RF-02 — exact-chain recursion is incorrectly bounded by stable template identity

`ObjectTemplateStore.project_effective_schema()` tracks `visited` as `template_id` only and suppresses a recursive parent whenever that stable template id has already appeared. That imports stable-lineage cycle semantics into `RP-05` and can truncate a finite persisted exact-pin chain containing the same stable template at different exact versions, for example:

```text
A:2 -> B:1 -> A:1 -> root
```

The frozen `RP-05` source of truth is the persisted exact `(template_id, version)` parent pair, and GET must not recertify stable-lineage acyclicity. Recursion safety must therefore not discard a distinct exact pair merely because its stable template id repeated.

Required correction:

```text
follow every distinct persisted exact (template_id, version) pair
if a recursion guard is required for termination, key it by the exact pair or an equivalent exact-node identity
never reject/truncate solely because the same stable template id reappears at another version
add permanent evidence with a finite repeated-stable-lineage / distinct-exact-version chain
preserve one-statement execution and deterministic root-to-leaf projection
keep RP-06 stable ancestry separate and unchanged in meaning
```

Both findings are implementation defects inside the already-frozen S03 design. No contract, architecture or steps reopen is required. The existing S03 execution aid remains active in `wip/`; do not remove it until reviewer acceptance.

## M3-S03 corrected implementation candidate

```text
authorized slice          M3-S03 — ObjectTemplate trusted recursive and aggregate read projections
slice state               CANDIDATE READY FOR REVIEW
reviewed candidate        2f287723703d33f2531328d8b85511603f881590
review findings record    1e955f2a9c42f2bd27167635b2774f1f0cd952f9
S03-RF-01 correction      IMPLEMENTED — PENDING REVIEWER CLOSURE
S03-RF-02 correction      IMPLEMENTED — PENDING REVIEWER CLOSURE
candidate evidence        ObjectTemplate targets for M3-VER-04/05/06/09/12/19 — PASS
M3-VER-07 target          NOT APPLICABLE — schema and DTO make the nullable carrier materializable
affected regression       M3-VER-14 .. M3-VER-16 — PASS
global M3-VER bundles     NOT YET CLOSED
business SQL statements   OT-GET-01..06 = 1 / 1 / 1 / 1 / 1 / 1 on PostgreSQL 16.15
candidate gates           PASS
later slices              NOT AUTHORIZED
```

`S03-RF-01` is corrected by projecting a committed `required=true / migration_default=NULL` property through both exact and effective-schema reads without fabricating a default. Permanent paired evidence confirms missing and explicit-null defaults remain rejected for new mutation requests. ObjectTemplate has no applicable `M3-VER-07` target for this carrier: the delivered column is nullable, `PropertyDto.migration_default` is nullable and omitted when `None`, and the remaining mandatory carriers are structurally typed/constrained by the delivered schema.

`S03-RF-02` is corrected by keying recursive safety on exact `(template_id, version)` node identity. Permanent PostgreSQL evidence follows the finite exact chain `A:2 -> B:1 -> A:1`, retains both distinct A versions in deterministic root-to-leaf order, and measures one authoritative business SQL statement. `OT-GET-06` remains the separate stable-ancestry projection.

Both corrections and the complete original S03 candidate gate pass. The findings are not reviewer-closed by this candidate; reviewer inspection and reviewer-owned completion remain pending.

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
M3-S02 execution/review                        DONE — COMPLETED
explicit M3-S03 implementation authorization  DONE — M3-S03 ONLY
M3-S03 execution/review                        CORRECTED CANDIDATE READY FOR REVIEW — reviewer closure pending
M3-S04 .. M3-S07 execution/review              BLOCKED BY DEPENDENCIES / NOT AUTHORIZED
final M3 acceptance                            PENDING
```

## Immediate next action

Review the corrected `M3-S03` candidate and its permanent `S03-RF-01` / `S03-RF-02` evidence.

Do not start M3-S04. Reviewer-owned `COMPLETED` remains pending until both findings are closed and the corrected evidence is accepted.
