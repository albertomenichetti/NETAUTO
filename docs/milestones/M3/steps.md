# M3 — Implementation Steps

**Status:** DESIGN COMPLETE — REVIEW PENDING — NOT YET FROZEN — NO IMPLEMENTATION AUTHORITY

**Authority:** PRE-IMPLEMENTATION PLANNING AUTHORITY

## 1. Purpose and authority

This document decomposes the frozen M3 contract and architecture into an ordered implementation plan. Until the separate steps consistency review passes and the project owner explicitly approves the steps freeze, this file is planning authority only and does **not** authorize software changes.

Implementation authority is composed from:

```text
current delivered AS-IS
    -> docs/architecture/

M3 contract
    -> docs/milestones/M3/contract.md
    -> FINAL / FROZEN

M3 architecture
    -> docs/milestones/M3/architecture/
    -> FINAL / FROZEN

project-wide technologies
    -> docs/general/technology_baseline.md
    -> ratified project stack

this document, only after steps freeze
    -> implementation order, slice scope, evidence assignment
       and completion conditions
```

The M3 `wip/` directory is historical discovery/review evidence only. No slice may derive semantics from WIP material when a frozen contract or architecture owner exists.

The implementation traceability chain is:

```text
M3-OUT
    -> M3-AC
    -> M3-VER
    -> frozen architecture owner
    -> M3-Snn
    -> implementation mechanism
    -> executed evidence
```

Any contradiction between this plan and frozen contract/architecture requires the applicable formal reopen process. Implementation must never resolve such a contradiction by choosing a convenient code behavior.

## 2. Global implementation rules

### 2.1 Mandatory pre-flight

Before starting or resuming any slice, the implementer must verify:

```text
branch/cycle is M3
contract.md remains FINAL / FROZEN
architecture/README.md remains FINAL / FROZEN
all owning architecture documents remain FINAL / FROZEN
steps.md is FINAL / FROZEN before implementation starts
status.md authorizes the exact slice
all slice dependencies are reviewer-owned COMPLETED
no relevant contract/architecture authority is reopened
assigned M3-VER targets and regression obligations are known
required PostgreSQL infrastructure is available for mandatory PostgreSQL evidence
```

A failed pre-flight puts the slice in `STOP`.

### 2.2 Vertical completion and bounded scope

M3 is implemented through bounded capability/resource-family slices rather than one 22-route rewrite.

Every behavior-bearing slice must leave its bounded surface coherent across the layers it actually changes:

```text
HTTP / CLI lexical carrier where applicable
application request/query semantics
ordinary read UoW ownership
cursor identity where applicable
persistence read projection
public outcome classification
public DTO materialization
bounded failure mapping
deterministic verification
```

A helper, SQL query, DTO tweak or test scaffold alone does not complete a behavior-bearing slice.

`M3-S06` is the explicit cross-route integration/verification closure slice and `M3-S07` is the dedicated final-acceptance candidate gate.

### 2.3 Preserve delivered AS-IS outside frozen M3 deltas

Implementation must preserve all delivered guarantees not explicitly changed by M3.

It must not:

```text
add a business route or resource
change public DTO shapes or ordering outside frozen deltas
add offset pagination, total counts or new filter DSL
weaken mutation semantic validation
add hidden post-mutation CLI GET enrichment
change cursor payload format/version
add schema/index/constraint changes
add an Alembic revision
add a runtime dependency
change the runtime lockfile
introduce cross-request snapshot semantics
turn read decoding into repair or silent omission
```

### 2.4 Read/UoW/SQL discipline

For every canonical M3 GET target implemented by `M3-S02 .. M3-S05`:

```text
ordinary caller-owned read UoW
one complete public projection
exactly one authoritative business SQL statement
PostgreSQL statement snapshot
no coherent_read() dependency
no mutation semantic certification
representational decoding only as required for typed projection
no silent dropping of a required non-materializable persisted member
```

The logical projection shape for each route is exactly the frozen RP mapping in `architecture/read-projections.md`. Implementation-local SQLAlchemy syntax, aliases and helper names may vary but may not change those guarantees.

### 2.5 Cursor discipline

Every cursor-bearing route must construct one canonical semantic query identity and reuse it for decode and encode.

```text
identity = route + membership path target(s) + membership filters + required presence bits
position = complete canonical keyset tuple
limit    = excluded from identity
```

The delivered codec v1 structure is preserved. The two explicit M3 path-target repairs and the ObjectTemplate parent presence bit are implemented exactly as frozen by `architecture/api.md`.

### 2.6 Verification discipline

Each slice implements and executes all concrete evidence targets assigned to it and all directly affected delivered regressions.

Rules:

```text
real PostgreSQL for T2/T3/T5 claims
no SQLite substitute for PostgreSQL authority
no sleep-based correctness orchestration
no normative skip / xfail / generic flaky rerun
missing TEST_DATABASE_URL -> BLOCKED, never PASS
Ruff format/check green
Pyright strict green
all affected AS-IS regressions green
```

Primary bundle ownership below is unique. Earlier/later slices may implement supporting targets or re-execute a bundle without changing primary ownership.

### 2.7 Candidate and reviewer ownership

The implementer produces a candidate and reports verified facts.

The reviewer owns:

```text
REVIEW CHANGES REQUIRED
COMPLETED
final acceptance approval
DELIVERED
```

A review correction remains in the same slice unless the frozen decomposition itself is defective and requires steps reopening.

### 2.8 Documentation and evidence

Implementation may update operational status, concrete evidence records and permanent machine-checkable M3 test registries. It must not rewrite frozen contract/architecture to match code.

Commit-specific M3 evidence belongs under:

```text
docs/milestones/M3/evidence/
```

or the repository's equivalent candidate-evidence owner established during implementation. Such records are evidence, not competing semantic authority.

## 3. Slice dependency graph

M3 uses one intentionally linear implementation path:

```text
M3-S00
    -> M3-S01
    -> M3-S02
    -> M3-S03
    -> M3-S04
    -> M3-S05
    -> M3-S06
    -> M3-S07
```

Rationale:

```text
S00 fixes common CLI protocol behavior before later CLI carrier work touches shared files
S01 establishes the complete ObjectTemplate parent public tri-state before ObjectTemplate read rewrite
S02 establishes the simplest one-statement trusted-read patterns on DataType
S03 realizes the richer ObjectTemplate recursive/aggregate projections
S04 realizes Object projections, including both explicit M3 cursor path-target repairs
S05 completes RelationshipDefinition / Relationship / global lifecycle reads and the lifecycle decoder surface
S06 closes exact 22/12/8 censuses, cross-route evidence, one-statement/coherence and traceability
S07 re-executes final acceptance on one delivery candidate
```

Only the exact slice marked `READY` or `IN PROGRESS` by `status.md` may be implemented after steps freeze.

## 4. Primary evidence ownership

Each stable M3 evidence bundle has exactly one primary implementation slice:

| Evidence | Primary slice |
|---|---|
| `M3-VER-01` | `M3-S00` |
| `M3-VER-02` | `M3-S00` |
| `M3-VER-03` | `M3-S00` |
| `M3-VER-04` | `M3-S06` |
| `M3-VER-05` | `M3-S06` |
| `M3-VER-06` | `M3-S06` |
| `M3-VER-07` | `M3-S05` |
| `M3-VER-08` | `M3-S05` |
| `M3-VER-09` | `M3-S06` |
| `M3-VER-10` | `M3-S04` |
| `M3-VER-11` | `M3-S04` |
| `M3-VER-12` | `M3-S06` |
| `M3-VER-13` | `M3-S05` |
| `M3-VER-14` | `M3-S01` |
| `M3-VER-15` | `M3-S01` |
| `M3-VER-16` | `M3-S01` |
| `M3-VER-17` | `M3-S06` |
| `M3-VER-18` | `M3-S06` |
| `M3-VER-19` | `M3-S06` |

`M3-S02` and `M3-S03` are vertically complete resource-family slices whose concrete tests contribute to global bundles primarily closed by `M3-S06`; this is intentional and does not leave any `M3-VER-*` orphaned.

`M3-S07` owns no new stable bundle identity: it re-executes and accepts all `M3-VER-01 .. M3-VER-19` against one candidate commit.

## 5. Slice registry

| Slice | Title | Depends on | Primary evidence |
|---|---|---|---|
| `M3-S00` | Official CLI Location protocol correctness | none | `M3-VER-01..03` |
| `M3-S01` | ObjectTemplate parent tri-state across HTTP, CLI and cursor identity | `M3-S00` | `M3-VER-14..16` |
| `M3-S02` | DataType trusted one-statement read projections | `M3-S01` | supporting targets for global read/cursor/coherence bundles |
| `M3-S03` | ObjectTemplate trusted recursive and aggregate read projections | `M3-S02` | supporting targets for global read/cursor/coherence bundles |
| `M3-S04` | Object trusted projections and path-target cursor repairs | `M3-S03` | `M3-VER-10`, `M3-VER-11` |
| `M3-S05` | RelationshipDefinition, Relationship and lifecycle trusted reads | `M3-S04` | `M3-VER-07`, `M3-VER-08`, `M3-VER-13` |
| `M3-S06` | Integrated read/cursor/coherence/non-drift/traceability closure | `M3-S05` | `M3-VER-04..06`, `09`, `12`, `17..19` |
| `M3-S07` | Full M3 acceptance and delivery-candidate gate | `M3-S06` and all prior slices reviewer-owned `COMPLETED` | all `M3-VER-01..19` re-executed and accepted |

---

# M3-S00 — Official CLI Location protocol correctness

## Objective

Correct common expected-Location materialization so every canonical registered `201 Created` response is truthfully reported as CLI success while exact same-release protocol validation remains strict.

## Dependencies

```text
none
```

## Frozen authorities

```text
docs/milestones/M3/contract.md
docs/milestones/M3/architecture/cli.md          ADP-07
docs/milestones/M3/architecture/verification.md M3-VER-01..03
docs/architecture/cli.md
```

## Bounded implementation scope

Expected production scope is limited to common CLI registry/protocol execution code, principally:

```text
src/netauto/cli/protocol.py
src/netauto/cli/registry.py
shared CLI execution/trace code only if required to preserve the frozen common pipeline
relevant CLI tests and M3 static registry evidence
```

Do not redesign rendering, enrichment, transport or command grammar.

## Deliverables

Implement the frozen tiny Location DSL:

```text
token grammar             {segment[.segment...]}
segment                   [a-z][a-z0-9_]*
lookup precedence         exact request key first, otherwise response JSON-object path
materializable scalar     str or int excluding bool
materialization           literal replacement only
Python format grammar     forbidden
runtime result            expected Location string or non-materializable
```

Preserve all eight existing `location_template` values and statically validate their closed syntax.

Protocol behavior must be:

```text
canonical status/body + exactly matching Location
    -> success

missing/repeated/mismatching Location
unresolvable/non-scalar expected token
    -> cli_protocol_error

valid nested-token success
    -> never cli_internal_error solely from Location processing
```

Exercise all eight registered creates, including the three nested response identities and five flat-token cases, in the shared interactive/non-interactive execution semantics. Add no hidden post-mutation GET.

## Primary evidence

```text
M3-VER-01
M3-VER-02
M3-VER-03
```

## Regression obligations

```text
63-operation registry census unchanged
8 registered 201 operations unchanged
same-release status/body validation unchanged
existing flat-token Location cases remain green
interactive and non-interactive execution remain behaviorally aligned
transport/trace behavior unchanged outside frozen delta
```

## Completion condition

Reviewer may mark `M3-S00` `COMPLETED` only when:

```text
all 8 canonical create responses succeed with exact Location
all Location violation classes map to cli_protocol_error
nested dotted tokens have no Python format semantics
static Location DSL checks are permanent
no hidden enrichment GET exists
M3-VER-01..03 PASS
all affected CLI regressions + Ruff/Pyright PASS
```

Primary outcome support:

```text
M3-OUT-01
M3-OUT-02
M3-OUT-08
```

---

# M3-S01 — ObjectTemplate parent tri-state across HTTP, CLI and cursor identity

## Objective

Deliver the complete public ObjectTemplate parent filter tri-state through the existing `parent_template_id` surface in HTTP and CLI, preserving the internal presence bit in cursor identity.

## Dependencies

```text
M3-S00 COMPLETED
```

## Frozen authorities

```text
docs/milestones/M3/architecture/api.md          ADP-04 / ADP-05
docs/milestones/M3/architecture/cli.md          ADP-06
docs/milestones/M3/architecture/verification.md M3-VER-14..16
```

## Bounded implementation scope

Expected production scope is limited to the existing ObjectTemplate list adapter/query identity and generic nullable CLI selector/planner path, principally:

```text
src/netauto/entrypoints/api/objecttemplates.py
src/netauto/application/objecttemplates.py
src/netauto/application/cursors.py only if required by existing cursor helper ownership
src/netauto/cli/registry.py
src/netauto/cli/parser.py
src/netauto/cli/selectors.py
src/netauto/cli/execution.py / existing request planner owner as applicable
relevant HTTP/CLI/cursor tests
```

Persistence already owns the internal tri-state; no schema or new persistence model is introduced.

## Deliverables

HTTP:

```text
parent_template_id omitted     -> None + parent_filter_set=False
parent_template_id=<UUID>      -> UUID + parent_filter_set=True
parent_template_id=null        -> None + parent_filter_set=True
other lexical sentinels        -> 400 invalid_request
repeated parameter             -> 400 invalid_request
```

CLI:

```text
omitted                        -> no selector target, no query pair
UUID                           -> exact UUID query pair
human ObjectTemplate selector  -> normal discovery -> UUID query pair
explicit null                  -> parsed None, zero selector lookup, literal query pair parent_template_id=null
```

Generic nullable direct-selector rule:

```text
selector-capable + nullable + None
    -> terminal value
    -> no selector target
```

Request planning must emit lexical `"null"` only for nullable QUERY `None`; do not introduce global `_wire_string(None)` behavior. BODY nullable null remains JSON null; PATH None remains invalid.

Cursor identity must preserve:

```text
omitted       -> parent_template_id=None, parent_filter_set=False
root-only     -> parent_template_id=None, parent_filter_set=True
exact parent  -> parent_template_id=str(UUID), parent_filter_set=True
```

No cursor codec/version change is allowed.

## Primary evidence

```text
M3-VER-14
M3-VER-15
M3-VER-16
```

## Supporting evidence/regression

This slice also establishes ObjectTemplate-list targets later consumed by:

```text
M3-VER-04
M3-VER-05
M3-VER-09
M3-VER-12
M3-VER-19
```

Preserve strict unknown-query handling, UUID parsing, selector ambiguity semantics, current persistence parent filtering and all non-null selector behavior.

## Completion condition

Reviewer may mark `M3-S01` `COMPLETED` only when:

```text
HTTP omitted / UUID / lowercase null semantics are exact
CLI omitted / UUID / human / null semantics are exact
explicit CLI null performs zero selector discovery
root-only and omitted cursors are mutually incompatible
root-only pagination continues successfully
parent_filter_set is not public
M3-VER-14..16 PASS
all affected HTTP/CLI/cursor regressions + Ruff/Pyright PASS
```

Primary outcome support:

```text
M3-OUT-05
M3-OUT-07
M3-OUT-08
```

---

# M3-S02 — DataType trusted one-statement read projections

## Objective

Convert the four canonical DataType GETs to the frozen trusted read responsibility and one-business-statement projection patterns while preserving public behavior and mutation semantic authority.

## Dependencies

```text
M3-S01 COMPLETED
```

## Frozen authorities

```text
docs/milestones/M3/architecture/read-projections.md
    DT-GET-01 -> RP-01
    DT-GET-02 -> RP-02
    DT-GET-03 -> RP-03
    DT-GET-04 -> RP-02

docs/milestones/M3/architecture/api.md
    DataType cursor identities unchanged
docs/milestones/M3/architecture/verification.md
```

## Bounded implementation scope

Principally:

```text
src/netauto/application/datatypes.py
src/netauto/persistence/datatypes.py
src/netauto/entrypoints/api/datatypes.py only where adapter wiring must change without public-contract change
DataType API/application/persistence/PostgreSQL tests
```

No ObjectTemplate/Object/Relationship read rewrite belongs in this slice.

## Deliverables

Implement all four DataType GETs with:

```text
ordinary read UoW
one authoritative business SQL statement per request
no coherent_read() dependency
no default-target publication recertification
no mutation-style constraint/domain recanonicalization
representational decoding sufficient for public DTOs
preserved filters/order/keyset/404-vs-empty semantics
```

`GET /datatypes/{id}/versions` must preserve stable parent absence separately from an existing parent with an empty filtered page.

The two DataType cursor identities and keysets remain exactly as frozen by ADP-04.

## Evidence assignment

This slice owns concrete DataType targets contributing to global bundles primarily closed by `M3-S06`:

```text
M3-VER-04
M3-VER-05
M3-VER-06
M3-VER-07 where a DataType projection carrier case is applicable
M3-VER-09
M3-VER-12
M3-VER-19
```

It has no exclusive primary stable bundle by design.

## Regression obligations

```text
DataType mutations retain semantic validation
public DTOs/filters/order unchanged
cursor limit-change continuation preserved
malformed/repeated request behavior preserved
all existing DataType API/application/persistence tests remain green unless frozen M3 read-boundary expectations explicitly replace them
```

## Completion condition

Reviewer may mark `M3-S02` `COMPLETED` only when:

```text
DT-GET-01..04 all use their frozen RP shapes
4 / 4 measured canonical DataType GETs issue one business SQL statement on PostgreSQL
no DataType GET depends on coherent_read() or mutation semantic recertification
public behavior and parent 404/empty distinction are preserved
affected mutation regressions remain green
assigned DataType evidence targets PASS
Ruff/Pyright PASS
```

Primary outcome support:

```text
M3-OUT-03
M3-OUT-04
M3-OUT-05
M3-OUT-08
```

---

# M3-S03 — ObjectTemplate trusted recursive and aggregate read projections

## Objective

Convert the six canonical ObjectTemplate GETs to their frozen direct, aggregate and recursive trusted projection shapes, building on the already-delivered parent tri-state from `M3-S01`.

## Dependencies

```text
M3-S02 COMPLETED
```

## Frozen authorities

```text
docs/milestones/M3/architecture/read-projections.md
    OT-GET-01 -> RP-01
    OT-GET-02 -> RP-02
    OT-GET-03 -> RP-03
    OT-GET-04 -> RP-04
    OT-GET-05 -> RP-05
    OT-GET-06 -> RP-06
docs/milestones/M3/architecture/api.md
docs/milestones/M3/architecture/verification.md
```

## Bounded implementation scope

Principally:

```text
src/netauto/application/objecttemplates.py
src/netauto/persistence/objecttemplates.py
src/netauto/entrypoints/api/objecttemplates.py only where read wiring must change
ObjectTemplate API/application/persistence/PostgreSQL tests
```

No Object or Relationship family read rewrite belongs in this slice.

## Deliverables

Implement all six ObjectTemplate GETs under the trusted-read boundary.

Critical route-specific requirements:

```text
OT-GET-01
    one-statement direct page using S01 parent tri-state

OT-GET-02
    direct stable-lineage exact projection

OT-GET-03
    parent-rooted version page preserving 404 vs empty

OT-GET-04
    exact aggregate with independent property/component child sets
    no properties x components cartesian product

OT-GET-05
    recursive exact-version chain following persisted (template_id,version) pins
    root-to-leaf deterministic projection
    no inheritance semantic recertification

OT-GET-06
    recursive stable-lineage ancestry page
    existing PUBLISHED-RDV EXISTS remains membership semantics
    no default-version publication recertification
```

All six use one business SQL statement, ordinary read UoW and no GET `coherent_read()` dependency.

## Evidence assignment

Concrete ObjectTemplate targets contribute to global bundles primarily closed by `M3-S06`:

```text
M3-VER-04
M3-VER-05
M3-VER-06
M3-VER-07 where applicable
M3-VER-09
M3-VER-12
M3-VER-19
```

`M3-VER-14..16` are re-executed as affected regression evidence but remain primarily owned by `M3-S01`.

## Regression obligations

```text
ObjectTemplate mutations keep cycle/agreement/admissibility validation
exact-version identities unchanged
public effective-schema/capability DTOs unchanged
capability membership and ordering unchanged
parent-filter carrier/cursor semantics from S01 remain green
```

## Completion condition

Reviewer may mark `M3-S03` `COMPLETED` only when:

```text
OT-GET-01..06 all realize their frozen RP shapes
6 / 6 measured canonical ObjectTemplate GETs issue one business SQL statement on PostgreSQL
exact-chain and stable-ancestry recursion are not conflated
independent child sets cannot cross-multiply or truncate
no ObjectTemplate GET performs mutation semantic recertification
affected mutation and S01 regressions remain green
assigned evidence targets PASS
Ruff/Pyright PASS
```

Primary outcome support:

```text
M3-OUT-03
M3-OUT-04
M3-OUT-05
M3-OUT-07
M3-OUT-08
```

---

# M3-S04 — Object trusted projections and path-target cursor repairs

## Objective

Convert all six Object GET/read routes to frozen trusted projection shapes and deliver the two explicit M3 cursor path-target corrections on components and Object-relative Relationship collections.

## Dependencies

```text
M3-S03 COMPLETED
```

## Frozen authorities

```text
docs/milestones/M3/architecture/read-projections.md
    OBJ-GET-01 -> RP-01
    OBJ-GET-02 -> RP-02
    OBJ-GET-03 -> RP-07 + exact-chain context
    OBJ-GET-04 -> RP-08 + exact-chain context
    OBJ-GET-05 -> RP-03 + ADP-03 decoder
    OBJ-GET-06 -> RP-07
docs/milestones/M3/architecture/api.md
    components parent_object_id cursor repair
    object relationships object_id cursor repair
docs/milestones/M3/architecture/verification.md
```

## Bounded implementation scope

Principally:

```text
src/netauto/application/objects.py
src/netauto/persistence/objects.py
src/netauto/persistence/lifecycle.py as required for Object-scoped lifecycle projection/decoder
src/netauto/entrypoints/api/objects.py
shared cursor helper only where current ownership requires it
Object/lifecycle API/application/persistence/PostgreSQL tests
```

RelationshipDefinition/Relationship exact/global lifecycle read rewrites remain for `M3-S05`.

## Deliverables

Implement the six Object routes with one-statement trusted projections.

Critical requirements:

```text
OBJ-GET-02
    intrinsic Object projection without transitive schema/DataType recertification

OBJ-GET-03 components
    target-rooted page
    exact template-chain context only to materialize slot_declaring_template_id
    exactly one declaration required per public fact
    zero/multiple declaration context -> internal failure, never silent drop
    cursor identity includes parent_object_id

OBJ-GET-04 owner
    child absent -> 404
    child present detached -> 200 null
    ownership fact present but required slot context not materializable -> internal failure

OBJ-GET-05 lifecycle
    target-rooted page
    trusted historical representational decoder
    no transition semantic replay

OBJ-GET-06 relationships
    target-rooted contextual page
    DISTINCT public semantic rows before keyset/order/limit
    cursor identity includes object_id
    complete key = (relationship_id,destination_object_id,name)
```

## Primary evidence

```text
M3-VER-10
M3-VER-11
```

## Supporting evidence

Concrete Object targets contribute to:

```text
M3-VER-04
M3-VER-05
M3-VER-06
M3-VER-07
M3-VER-08
M3-VER-09
M3-VER-12
M3-VER-13
M3-VER-19
```

## Regression obligations

```text
Object mutation schema/property validation remains active
ownership mutation validation remains active
Relationship mutation topology/schema validation remains active
public Object DTOs/order/filter semantics unchanged
owner 404/null distinction preserved
all existing Object and lifecycle regressions affected by the read boundary remain green
```

## Completion condition

Reviewer may mark `M3-S04` `COMPLETED` only when:

```text
OBJ-GET-01..06 realize frozen RP shapes
6 / 6 measured canonical Object GETs issue one business SQL statement on PostgreSQL
components cross-parent cursor reuse -> invalid_cursor
Object Relationship cross-object cursor reuse -> invalid_cursor
same-target continuations remain valid
contextual projection failures cannot silently omit/fabricate public state
Object-scoped lifecycle decoder follows ADP-03
M3-VER-10 and M3-VER-11 PASS
assigned supporting targets and affected regressions PASS
Ruff/Pyright PASS
```

Primary outcome support:

```text
M3-OUT-03
M3-OUT-04
M3-OUT-05
M3-OUT-06
M3-OUT-08
```

---

# M3-S05 — RelationshipDefinition, Relationship and lifecycle trusted reads

## Objective

Complete the twenty-two-route trusted-read implementation by converting the four RelationshipDefinition GETs, exact Relationship GET and global lifecycle GET, and close the trusted lifecycle decoder behavior across intrinsic and Relationship historical families.

## Dependencies

```text
M3-S04 COMPLETED
```

## Frozen authorities

```text
docs/milestones/M3/architecture/read-projections.md
    RD-GET-01 -> RP-09
    RD-GET-02 -> RP-04
    RD-GET-03 -> RP-03
    RD-GET-04 -> RP-10
    REL-GET-01 -> RP-04
    LC-GET-01 -> RP-01 + ADP-03 decoder
docs/milestones/M3/architecture/api.md
    RD and lifecycle cursor identities
docs/milestones/M3/architecture/verification.md
```

## Bounded implementation scope

Principally:

```text
src/netauto/application/relationshipdefinitions.py
src/netauto/application/relationships.py
src/netauto/persistence/relationships.py
src/netauto/persistence/lifecycle.py
src/netauto/entrypoints/api/relationshipdefinitions.py
src/netauto/entrypoints/api/relationships.py
existing global lifecycle API owner
RelationshipDefinition/Relationship/lifecycle tests
```

No new Relationship schema, route or mutation capability is introduced.

## Deliverables

RelationshipDefinition:

```text
list
    page root Definition ids before Resolution expansion
    complete aggregate items; joined child cardinality must not truncate roots

exact definition
    exact header + complete Resolution set
    zero resolutions remains materializable

versions
    parent-rooted page preserving stable parent 404 vs empty filtered page

exact version
    preserve parent absence separately from exact version absence
    exact version with zero properties remains valid
```

Relationship exact GET:

```text
factual Relationship root + complete deduplicated public views[]
no Definition/template/RDV/DataType mutation-semantic recertification
```

Lifecycle:

```text
global route remains direct page with (occurred_at,id) DESC
Object-scoped route from S04 and global route share trusted ADP-03 decoder
representational decoding keeps UUID/int/string/JSON requirements needed by DTOs
semantically surprising but representable historical transitions remain readable
materially undecodable required carrier -> bounded internal_error
no live lookup solely to reinterpret historical semantics
```

Complete lifecycle cursor scope distinction between global and Object-scoped identities.

## Primary evidence

```text
M3-VER-07
M3-VER-08
M3-VER-13
```

## Supporting evidence

This slice completes concrete targets contributing to:

```text
M3-VER-04
M3-VER-05
M3-VER-06
M3-VER-09
M3-VER-12
M3-VER-19
```

## Regression obligations

```text
RelationshipDefinition and Relationship mutations retain semantic validation
factual Relationship identities/properties/versions unchanged
lifecycle filters/DTO discrimination/order unchanged
no default publication or relationship topology recertification remains on GET
all affected RD/Relationship/lifecycle regressions remain green
```

## Completion condition

Reviewer may mark `M3-S05` `COMPLETED` only when:

```text
RD-GET-01..04, REL-GET-01 and LC-GET-01 realize frozen RP shapes
6 / 6 measured canonical routes issue one business SQL statement on PostgreSQL
all 22 / 22 M3 GET routes are now implemented under the trusted-read architecture
representable semantically non-recertified lifecycle history is readable
materially undecodable mandatory history fails boundedly
lifecycle cross-scope cursor reuse is rejected
M3-VER-07, M3-VER-08 and M3-VER-13 PASS
assigned supporting targets and mutation regressions PASS
Ruff/Pyright PASS
```

Primary outcome support:

```text
M3-OUT-03
M3-OUT-04
M3-OUT-05
M3-OUT-06
M3-OUT-08
```

---

# M3-S06 — Integrated read/cursor/coherence/non-drift/traceability closure

## Objective

Close the global M3 obligations that cannot be proven by one resource-family slice alone: exact public read compatibility/failures, complete 12-route cursor identity/keysets, read-vs-mutation semantic authority, 22/22 one-statement/coherence evidence, platform non-drift and machine-checkable traceability.

This is an integration/evidence closure slice. It may correct implementation defects found by its required evidence, but it must not introduce new semantics or reopen frozen architecture implicitly.

## Dependencies

```text
M3-S05 COMPLETED
```

## Frozen authorities

```text
docs/milestones/M3/contract.md
docs/milestones/M3/architecture/read-projections.md
docs/milestones/M3/architecture/api.md
docs/milestones/M3/architecture/cli.md
docs/milestones/M3/architecture/verification.md
docs/architecture/verification.md
```

## Bounded implementation scope

Principally test/evidence and only implementation corrections needed to satisfy frozen architecture:

```text
permanent M3 machine-checkable traceability/census registry
cross-route HTTP/cursor tests
PostgreSQL SQL-statement measurement harness
T3 deterministic snapshot-interleaving harness/test hooks that do not change production semantics
mutation semantic-regression evidence
schema/Alembic/lockfile non-drift checks
candidate evidence records
production modules only for defects exposed by these frozen obligations
```

## Deliverables

Machine-checkable exact registries:

```text
M3_OUTCOMES                     8 exact
M3_ACCEPTANCE_CRITERIA         19 exact
M3_EVIDENCE_BUNDLES            19 exact
M3_OUTCOME_TO_ACCEPTANCE
M3_ACCEPTANCE_TO_EVIDENCE
M3_EVIDENCE_TO_ARCHITECTURE_OWNER
M3_EVIDENCE_TO_TARGETS
M3_GET_ROUTE_CENSUS            22 exact
M3_CURSOR_ROUTE_CENSUS         12 exact
M3_CLI_201_CENSUS               8 exact
```

Global public-read evidence:

```text
22 / 22 success compatibility
strict malformed/unknown/repeated request handling
path-target 404 vs successful empty/null distinctions
all 22 read targets free of mutation-semantic validator prerequisites
representative persisted-state fixtures across removed recertification families
write-side mutation semantic regressions remain active
```

Global cursor evidence:

```text
12 / 12 canonical route/filter/path/presence identity matrix
same identity accepted
changed limit accepted
changed membership filter rejected
changed required path target rejected
malformed/wrong key rejected
true multipage traversal without cursor-induced omission/duplication
compound Object Relationship and lifecycle keysets exercised
```

One-statement/coherence evidence:

```text
22 / 22 canonical GET invocations measured on real PostgreSQL
exactly one authoritative business SQL statement each
no coherent_read() dependency across the census
representative deterministic T3 before/after writer interleaving proves whole projection is one statement snapshot
no cross-request snapshot promise is introduced
```

Non-drift:

```text
no new Alembic revision
same delivered migration root/head
live schema compare_metadata == []
no M3 table/index/constraint delta
no runtime dependency delta
uv lock --check PASS
runtime lockfile unchanged
```

## Primary evidence

```text
M3-VER-04
M3-VER-05
M3-VER-06
M3-VER-09
M3-VER-12
M3-VER-17
M3-VER-18
M3-VER-19
```

## Required re-execution

Re-run prior primary bundles affected by integration:

```text
M3-VER-01..03
M3-VER-07..08
M3-VER-10..11
M3-VER-13..16
```

This does not change their primary ownership.

## Completion condition

Reviewer may mark `M3-S06` `COMPLETED` only when:

```text
all 19 M3-VER bundles have non-empty concrete target sets
M3-VER-04,05,06,09,12,17,18,19 PASS
22 / 22 GET census exact
12 / 12 cursor census exact
8 / 8 CLI 201 census exact
22 / 22 PostgreSQL one-business-statement measurements PASS
required T3 coherence evidence PASS
mutation semantic regressions PASS
schema/dependency/lock non-drift PASS
no normative skip/xfail/rerun workaround
all prior primary bundles still PASS when re-executed as affected
Ruff/Pyright and affected repository suites PASS
```

Primary outcome support:

```text
M3-OUT-03
M3-OUT-04
M3-OUT-05
M3-OUT-08
```

---

# M3-S07 — Full M3 acceptance and delivery-candidate gate

## Objective

Produce and review one M3 delivery candidate with complete end-to-end evidence. This slice adds no planned business behavior; it validates the integrated result and records acceptance facts.

## Dependencies

```text
M3-S00 .. M3-S06 reviewer-owned COMPLETED
```

## Frozen authorities

```text
docs/milestones/M3/contract.md
docs/milestones/M3/architecture/
this steps.md after freeze
docs/architecture/verification.md
project build/static/release authorities
```

## Deliverables

Identify one candidate commit and execute the complete final gate:

```text
M3-VER-01 .. M3-VER-19             PASS
GET route census                    22 / 22
cursor route census                 12 / 12
CLI 201 Location census              8 / 8
required PostgreSQL evidence         PASS
schema metadata drift                []
no Alembic/schema/dependency drift   PASS
Ruff format/check                    PASS
Pyright strict                       PASS
locked dependency/build checks       PASS
full repository test suite           PASS
normative skip/xfail/rerun            0
blocking M3 findings                  0
open incompatible reopen              0
end-to-end traceability              COMPLETE
```

Record PostgreSQL/server/runtime versions and exact commands/counts in candidate evidence. A missing PostgreSQL environment blocks acceptance; it does not downgrade the requirement.

Perform final change review against the frozen contract/architecture/steps and confirm no accidental public/schema/dependency scope escaped the milestone.

## Evidence ownership

No new stable `M3-VER-*` identity is created. All nineteen bundles are re-executed and reviewer-accepted on the same delivery candidate.

## Completion condition

`M3-S07` may be marked `COMPLETED` only when the reviewer accepts the candidate and every final gate above is PASS with zero blocking findings.

Only after that may milestone governance advance to final M3 delivery approval/consolidation. No implementation success claim is inferred from planning or from earlier slice completion alone.

Primary outcome support:

```text
M3-OUT-01 .. M3-OUT-08
```

---

## 6. Steps-design review gate

This decomposition is **not yet frozen**.

Before a steps freeze may be proposed, a separate steps consistency review must verify at minimum:

```text
slice registry is complete and ordered
slice dependency graph is acyclic and implementation-safe
scope boundaries are bounded and non-overlapping except explicit shared infrastructure
all frozen ADP responsibilities are realized by one or more slices
all 22 GET routes are assigned exactly once to behavior implementation slices
all 12 cursor routes have an implementation/evidence path
all 8 CLI 201 Location operations have an implementation/evidence path
all 19 M3-VER bundles have exactly one primary implementation owner
all M3-OUT / M3-AC / M3-VER obligations are traceable through slices
no slice invents semantics beyond frozen contract/architecture
no required schema/migration/dependency/lockfile delta is introduced
final integration and final acceptance paths are sufficient
no open TODO/TBD/ambiguous implementation authority remains
```

Findings must be closed before steps freeze approval is requested.

## 7. Implementation gate

Implementation remains in STOP until all of the following are true:

```text
steps consistency review       PASS
steps.md                        FINAL / FROZEN
project-owner steps approval    GRANTED
status.md                       explicitly authorizes an M3-Snn slice
```

Until then:

```text
active implementation    NONE
software implementation  NOT AUTHORIZED
```

## Immediate next action

Run the separate M3 steps consistency review against this complete decomposition. Correct any finding before requesting explicit project-owner approval to freeze `steps.md`.