# Codex implementation prompt — M3-S05

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS under `docs/architecture/`, the FINAL/FROZEN M3 contract and architecture set, the FINAL/FROZEN `steps.md`, the ratified technology baseline, and the operational authorization in `status.md`.

If this prompt conflicts with an owning authority, stop the affected work and report the conflict. Do not reinterpret frozen semantics to fit current code or this execution aid.

---

# Assignment

Implement exactly:

```text
M3-S05 — RelationshipDefinition, Relationship and lifecycle trusted reads
```

Work directly on branch:

```text
M3
```

The human-authorized implementation baseline is:

```text
dd5bde664922822c29b186b5e6a9d21396fb2746
Authorize M3-S05 implementation
```

The prompt-publication commit is a later documentation-only descendant of that authorization commit. Work from current `origin/M3`; do not reset the branch to the authorization commit. Confirm the authorization commit remains in ancestry.

Current authorization is exactly:

```text
M3-S00    reviewer-owned COMPLETED
M3-S01    reviewer-owned COMPLETED
M3-S02    reviewer-owned COMPLETED
M3-S03    reviewer-owned COMPLETED
M3-S04    reviewer-owned COMPLETED
M3-S05    READY — AUTHORIZED
M3-S06    NOT AUTHORIZED / dependency blocked
M3-S07    NOT AUTHORIZED / dependency blocked
```

Primary stable evidence owned by this slice:

```text
M3-VER-07 — Materially undecodable carrier boundary
M3-VER-08 — Trusted lifecycle historical decoding
M3-VER-13 — Lifecycle route-scope cursor distinction
```

S05 also completes concrete RelationshipDefinition / Relationship / lifecycle targets contributing to:

```text
M3-VER-04
M3-VER-05
M3-VER-06
M3-VER-09
M3-VER-12
M3-VER-19
```

Do **not** claim those global bundles PASS solely from S05. Their integrated cross-route closure remains `M3-S06`.

Do not start `M3-S06`. Do not create a pull request. Do not merge, rebase, force-push, rewrite published history, tag or release.

---

# 1. Mandatory repository pre-flight

Before editing software, re-read and obey at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

docs/architecture/README.md
docs/architecture/api.md
docs/architecture/verification.md

docs/milestones/M3/contract.md
docs/milestones/M3/architecture/README.md
docs/milestones/M3/architecture/read-projections.md
docs/milestones/M3/architecture/api.md
docs/milestones/M3/architecture/verification.md
docs/milestones/M3/steps.md
docs/milestones/M3/status.md

docs/milestones/M3/wip/M3-S05-codex-prompt.md
```

Historical M3 WIP route decisions may be used only as non-normative cross-check evidence. Frozen contract/architecture/steps own semantics.

Confirm before behavior changes:

```text
checked-out branch                    M3
origin/M3 ancestry                    includes dd5bde664922822c29b186b5e6a9d21396fb2746
README active cycle                   M3
contract                              FINAL / FROZEN
architecture set                      FINAL / FROZEN
read-projections ADP-01..03           CLOSED
api ADP-04 / ADP-05                   CLOSED
verification ADP-08                   CLOSED
steps.md                              FINAL / FROZEN
M3-S00..S04                           reviewer-owned COMPLETED
M3-S05                                READY or IN PROGRESS
M3-S06                                NOT AUTHORIZED
relevant reopen                       none
project version                       0.2.0
```

Inspect at minimum before choosing local decomposition:

```text
src/netauto/application/relationshipdefinitions.py
src/netauto/application/relationships.py
src/netauto/application/objects.py
src/netauto/application/cursors.py

src/netauto/persistence/relationships.py
src/netauto/persistence/lifecycle.py
src/netauto/persistence/metadata.py
src/netauto/persistence/uow.py

src/netauto/entrypoints/api/relationshipdefinitions.py
src/netauto/entrypoints/api/relationships.py
src/netauto/entrypoints/api/objects.py
src/netauto/transport/http/relationshipdefinitions.py
src/netauto/transport/http/relationships.py
src/netauto/transport/http/objects.py

existing RelationshipDefinition API/domain/concurrency tests
existing Relationship API/domain/concurrency tests
existing lifecycle tests
accepted M3-S02/S03/S04 evidence modules
all directly affected delivered regressions
```

Important current facts to repair rather than redesign:

```text
RD-GET-01 list definitions
    persistence already pages Definition root ids before Resolution expansion in one statement
    application still uses coherent_read(), _validate_persisted() and default-target recertification

RD-GET-02 exact definition
    persistence already loads header + Resolution set in one statement
    application still uses coherent_read(), _validate_persisted() and default-target recertification

RD-GET-03 versions page
    application still performs Definition aggregate lookup + default recertification + version page
    -> must become one parent-rooted page statement

RD-GET-04 exact version
    current flow checks Definition separately and loads version header/properties separately
    -> must become one parent-rooted exact aggregate statement

REL-GET-01 exact Relationship
    current application uses coherent_read() + _validated() and reconstructs Definition/template/RDV/DataType semantic closure
    -> replace with trusted factual projection

LC-GET-01 global lifecycle
    persistence already performs one filtered event-page statement using the shared ADP-03 decoder
    application still wraps it in coherent_read()
    -> ordinary UoW, same query/filter/order/cursor semantics

S04 already changed the shared lifecycle decoder to ADP-03 semantics and completed Object-scoped lifecycle projection.
Do not regress or rewrite completed S04 Object routes.
```

When implementation actually begins, transition `M3-S05 READY -> IN PROGRESS` in `status.md`. Do not mark S05 `COMPLETED` as implementer.

---

# 2. Hard scope boundary

## In scope

Implement exactly these six canonical GET/read routes:

```text
RD-GET-01   GET /api/v1/core/relationship-definitions
RD-GET-02   GET /api/v1/core/relationship-definitions/{relationship_definition_id}
RD-GET-03   GET /api/v1/core/relationship-definitions/{relationship_definition_id}/versions
RD-GET-04   GET /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}
REL-GET-01  GET /api/v1/core/relationships/{relationship_id}
LC-GET-01   GET /api/v1/core/lifecycle-events
```

Expected production scope is principally:

```text
src/netauto/application/relationshipdefinitions.py
src/netauto/application/relationships.py
src/netauto/application/objects.py only for the existing global lifecycle read path
src/netauto/persistence/relationships.py
src/netauto/persistence/lifecycle.py only where shared ADP-03/global read ownership requires it
src/netauto/entrypoints/api/relationshipdefinitions.py only if read wiring changes without public-contract change
src/netauto/entrypoints/api/relationships.py only if read wiring changes without public-contract change
src/netauto/entrypoints/api/objects.py only if existing global lifecycle wiring requires it
relevant RelationshipDefinition/Relationship/lifecycle tests
operational M3-S05 status/evidence updates
```

## Explicitly out of scope

Do not implement M3-S06/S07 work, including:

```text
final integrated 22-route evidence registry closure
final 12-route cursor registry closure
T3 representative snapshot-interleaving closure
schema/Alembic/lockfile/platform non-drift final closure
machine-checkable M3 traceability closure
final delivery-candidate acceptance
```

Do not reopen or redesign completed Object/ObjectTemplate/DataType projections. Re-execution and narrowly necessary shared-lifecycle regressions are allowed.

Do not introduce:

```text
new business route/resource
public DTO field change
new public filter
cursor codec/version change
offset pagination or total counts
schema/table/index/constraint change
Alembic revision
runtime dependency
uv.lock semantic change
project-version change
hidden repair/remediation
weakened mutation validation
new retry/backoff behavior
new public error code
```

---

# 3. Universal S05 trusted-read rules

Each of the six S05 GETs must satisfy:

```text
one complete public projection
    -> exactly one authoritative business SQL statement
    -> one PostgreSQL statement snapshot
    -> ordinary caller-owned read UoW
    -> no coherent_read() dependency
    -> no mutation semantic certification
```

GETs trust persisted semantic state. They may decode carriers required to construct typed public state, but must not answer:

```text
"Would this persisted state pass current mutation admission/transition validation?"
```

Forbidden read-side recertification includes as applicable:

```text
RelationshipDefinition aggregate semantic validation
default_version -> PUBLISHED certification
RelationshipDefinitionVersion semantic/history certification
Relationship topology/template compatibility certification
Relationship property/DataType/schema canonicalization
live dependency loading solely to prove persisted factual state again
lifecycle transition changedness/version-increase replay
```

Mutation helpers and validators remain strong and available to mutation paths.

Representational failure remains bounded. If a mandatory carrier cannot be materialized into its public typed form, fail `500 internal_error`; do not repair, invent defaults, silently omit a required item or downgrade a materialization failure to an empty collection/null.

---

# 4. Exact route matrix

## RD-GET-01 — RP-09 ROOT-PAGED AGGREGATE

Route:

```text
GET /api/v1/core/relationship-definitions
```

Cursor identity remains:

```text
route = relationship_definitions
filters = {}
key = [str(id)]
ORDER BY id ASC
limit excluded from identity
```

Required projection:

```text
RelationshipDefinition root relation
    -> id keyset
    -> ORDER BY id
    -> LIMIT limit + 1 ROOT IDENTITIES

selected roots
    -> expand complete Resolution sets
    -> reconstruct complete RelationshipDefinition items
```

Do not apply SQL `LIMIT` to raw root×Resolution rows where child cardinality can truncate roots or alter page cardinality.

Required states:

```text
zero roots -> successful empty page
selected root + zero resolutions -> complete root with resolutions=[]
selected root + many resolutions -> complete untruncated aggregate
```

Remove application `_validate_persisted()` and default-target publication certification. Persisted `default_version` is projected as a fact.

Permanent evidence must include at least one root whose Resolution child count is larger than the page limit and prove the selected root is complete rather than truncated.

## RD-GET-02 — RP-04 EXACT AGGREGATE

Route:

```text
GET /api/v1/core/relationship-definitions/{definition_id}
```

One statement must materialize:

```text
exact RelationshipDefinition header
complete Resolution set
```

Required states:

```text
root absent -> 404 resource_not_found
root present + zero resolutions -> successful aggregate with []
root present + resolutions -> complete deterministic aggregate
```

No `_validate_persisted()` and no default-version target lookup/certification.

A structurally committed but semantically surprising Definition/default pointer that is representable by the DTO must remain readable. Do not turn such a case into M3-VER-07 merely because mutation would reject it.

## RD-GET-03 — RP-03 PARENT-ROOTED VERSION PAGE

Route:

```text
GET /api/v1/core/relationship-definitions/{definition_id}/versions
```

Preserve cursor identity:

```text
route = relationship_definition_versions
filters = {
    definition_id: str(definition_id),
    status: None or status.value,
}
key = [version]
ORDER BY version ASC
```

Required states:

```text
Definition absent -> 404 resource_not_found
Definition exists + zero matching versions -> 200 empty page
Definition exists + members -> normal page
```

The **single** SQL statement carries parent-presence evidence independently from child membership. Status/keyset predicates must not erase the parent-only result.

Do not issue one Definition aggregate read plus a separate version page. Do not recertify the Definition default target.

## RD-GET-04 — RP-10 PARENT-ROOTED EXACT AGGREGATE

Route:

```text
GET /api/v1/core/relationship-definitions/{definition_id}/versions/{version}
```

Required public distinction:

```text
Definition parent absent
    -> 404 resource_not_found for parent

Definition parent present + exact version absent
    -> 404 resource_not_found for exact version

exact version present + zero properties
    -> success with properties=[]

exact version present + properties
    -> complete property set ordered by position ASC
```

One statement only. Parent and exact-child existence evidence must survive zero property rows.

Do not call `validate_relationship_definition_version()` or property-history/DataType semantic validators from the GET.

Use only representational decoding required for the version/property DTO fields.

## REL-GET-01 — RP-04 FACTUAL RELATIONSHIP EXACT AGGREGATE

Route:

```text
GET /api/v1/core/relationships/{relationship_id}
```

One statement rooted at `relationships` must materialize:

```text
relationship id
relationship_definition_id
relationship_definition_version
properties
views[]
    object_id
    destination_object_id
    name
```

Public `views[]` are derived from persisted runtime resolution facts plus persisted `relationship_resolutions.name`.

Projection semantics:

```text
Relationship root absent
    -> 404 resource_not_found

Relationship root present + zero materializable view rows
    -> success with views=[]

Relationship root present + view rows
    -> complete deduplicated views[]
```

`DISTINCT` or equivalent public semantic deduplication is projection logic. It must occur before final public ordering/materialization where duplicates can arise.

Persisted `properties` require only JSON object/string-key representational decoding for the DTO. Do not reconstruct/certify:

```text
RelationshipDefinition
ObjectTemplate ancestry
endpoint template compatibility
exact RelationshipDefinitionVersion semantic validity
DataType dependencies
Relationship property canonicality/topology
```

Do not call `_validated()` / `_validated_many()` or an equivalent mutation semantic aggregate certification path from this GET.

Permanent trusted-read evidence must include a structurally committed factual Relationship state that the old validating path would reject but whose public carriers are materializable; exact GET must return it.

Paired mutation tests must continue rejecting equivalent new invalid mutation state.

## LC-GET-01 — RP-01 + ADP-03 GLOBAL LIFECYCLE PAGE

Route:

```text
GET /api/v1/core/lifecycle-events
```

The delivered page query is already the target logical shape:

```text
object_lifecycle_events
    -> all existing public filters
    -> keyset (occurred_at,id)
    -> ORDER BY occurred_at DESC, id DESC
    -> LIMIT limit + 1
```

There is no path-target marker requirement.

Use an ordinary UoW. Remove the remaining `coherent_read()` dependency. Do not add helper reads.

Preserve all existing filters and canonical cursor identity, including:

```text
route = lifecycle_events
filters = {
    kind,
    object_id,
    destination_object_id,
    relationship_id,
    relationship_definition_id,
    relationship_name,
    occurred_from,
    occurred_to,
    involving_object_id=None,
}
key = [canonical occurred_at, str(id)]
ORDER BY occurred_at DESC, id DESC
```

The global route and the S04 Object-scoped route share the same ADP-03 trusted decoder already introduced in S04. Do not fork the decoder into divergent semantics.

---

# 5. ADP-03 / M3-VER-07 and M3-VER-08 — primary S05 ownership

S05 owns the stable primary acceptance for both the negative materialization boundary and positive trusted-history behavior.

## M3-VER-07 — materially undecodable carrier boundary

Do not confuse semantic surprise with materialization failure.

A fixture belongs to M3-VER-07 only when a persisted required carrier cannot be converted into mandatory public typed state, for example:

```text
historical Object snapshot missing a required field
historical Object snapshot UUID carrier not parseable as UUID
historical Relationship factual state with wrong scalar/object type
historical Relationship factual state missing a required field
```

Expected result:

```text
500 internal_error
no repair
no fabricated default
no silent event/item omission
```

Use deterministic PostgreSQL fixtures that remain safe for the delivered structural schema. The lifecycle table already requires top-level JSON objects where present, so corrupt nested field values/omissions may be used without schema changes.

Primary S05 evidence should cover both public historical families materially enough to close the bundle, including at least:

```text
one intrinsic Object historical mandatory-carrier failure
one Relationship factual-state mandatory-carrier failure
```

Re-execute the accepted S04 Object-scoped negative boundary as regression evidence.

Representable values such as semantic identifier surprises, zero/non-positive historical versions when the DTO carrier is simply int, nested JSON null/objects/lists, or extra unused JSON fields are **not** M3-VER-07 failures when ADP-03 can materialize them.

## M3-VER-08 — trusted lifecycle historical decoding

Positive evidence must include structurally persisted and DTO-decodable historical state that fails mutation-style transition certification but remains readable.

Close representative cases across both intrinsic and Relationship families. At minimum exercise:

```text
intrinsic family
    RENAME or DATA_CHANGE or SCHEMA_CHANGE semantic surprise

Relationship family
    RELATIONSHIP_DATA_CHANGE and/or RELATIONSHIP_SCHEMA_CHANGE semantic surprise
```

Material examples may include:

```text
DATA_CHANGE whose before/after properties are unchanged
SCHEMA_CHANGE whose after version does not increase
Relationship DATA_CHANGE with unchanged properties or surprising version relation
Relationship SCHEMA_CHANGE without version increase
```

The exact fixture must remain structurally committable under database constraints and DTO-decodable.

Prove the relevant **global** lifecycle GET returns the event. Re-execute the S04 Object-scoped trusted decoder evidence so shared behavior cannot diverge.

Mutation/write-side transition generation and validation must remain unchanged and green.

---

# 6. M3-VER-13 — lifecycle route-scope cursor distinction

Primary S05 evidence must prove the frozen lifecycle identity split while keeping codec v1 unchanged.

Required public evidence:

```text
global lifecycle cursor reused on Object-scoped route
    -> 400 invalid_cursor

Object-scoped A cursor reused on Object-scoped B
    -> 400 invalid_cursor

changed lifecycle membership filter
    -> 400 invalid_cursor

same global scope/filter identity
    -> continuation accepted

same Object scope/filter identity
    -> continuation accepted

changed limit only
    -> continuation accepted
```

Also exercise global↔Object scope incompatibility in both directions where straightforward. No new route id is needed; distinction remains `involving_object_id=None` vs `str(object_id)`.

Preserve complete lifecycle position key `(occurred_at,id) DESC` and true multipage no-omission/no-duplication behavior.

---

# 7. RelationshipDefinition cursor / aggregate obligations

Preserve delivered cursor codec v1.

RelationshipDefinition list:

```text
route = relationship_definitions
filters = {}
key = [str(id)]
```

RelationshipDefinition versions:

```text
route = relationship_definition_versions
filters = {definition_id, status}
key = [version]
```

Permanent evidence should include:

```text
same identity continuation
changed limit accepted
changed status/definition target rejected for version cursor
malformed/wrong-type key rejected
true multipage traversal without omission/duplication
RD root aggregate pagination unaffected by Resolution child cardinality
```

These are concrete S05 targets for global M3-VER-09/12, which remain primarily closed in S06.

---

# 8. Read/write semantic authority pairing

S05 must prove the read/write boundary, not just statement counts.

Read-side representative surprises should include material cases such as:

```text
RelationshipDefinition default_version points to a structurally existing non-PUBLISHED version
representable Definition aggregate state rejected by mutation/domain validation
representable RelationshipDefinitionVersion/property dependency state rejected by mutation admission
factual Relationship state whose old _validated() semantic closure would fail but DTO carriers are materializable
lifecycle intrinsic and Relationship transition surprises
```

Use structurally committable persisted states.

Write-side evidence must prove existing mutation validation remains active for representatives including:

```text
RelationshipDefinition create/revise/publish/set-default admission
RelationshipDefinitionVersion property/dependency semantic validation
Relationship create/topology/property validation
Relationship data-change/schema-change validation
lifecycle writers preserve canonical event transition shapes
```

Do not weaken a mutation validator merely to make reads succeed.

---

# 9. One-business-statement evidence — mandatory PostgreSQL

Measure independently on the actual production runtime engine:

```text
RD-GET-01
RD-GET-02
RD-GET-03
RD-GET-04
REL-GET-01
LC-GET-01
```

For each target invocation:

```text
business SQL statement count == 1
```

Use deterministic SQLAlchemy observation such as `before_cursor_execute` on the runtime `AsyncEngine.sync_engine`, following accepted S02/S03/S04 practice.

The measurement window starts immediately before each target GET and is cleared per route. Setup/cleanup/warmup SQL is outside the measured invocation. A helper SELECT is still a business statement.

Add static evidence that these six GET application paths do not depend on:

```text
coherent_read
RelationshipDefinition _validate_persisted / default-pointer recertification
RelationshipDefinitionVersion mutation validators
Relationship _validated / _validated_many
schema/DataType/topology certification helpers
transition-certifying lifecycle logic
```

Missing `TEST_DATABASE_URL` makes mandatory S05 PostgreSQL evidence `BLOCKED`, never PASS. Do not substitute SQLite, Docker/Testcontainers, invented credentials or fake statement counters.

Once S05 is implemented, production route implementation should be 22/22 trusted one-statement by family, but the integrated 22-route acceptance/census remains S06-owned. Report that distinction explicitly.

---

# 10. Permanent S05 evidence

A dedicated module such as:

```text
tests/test_m3_s05_relationship_reads.py
```

is acceptable but not mandatory.

Permanent evidence must cover at minimum:

```text
1. RD-GET-01 root-page pagination before Resolution expansion
2. RD-GET-01 selected aggregate completeness with child count > page limit
3. RD-GET-02 exact 404 / zero resolutions / complete resolutions
4. RD trusted default/aggregate semantic surprise + paired mutation rejection
5. RD-GET-03 parent 404 vs filtered empty vs nonempty page
6. RD version cursor continuation/filter/target/key validation
7. RD-GET-04 parent absent vs exact version absent vs zero properties vs populated properties
8. RD-GET-04 trusted semantic surprise + mutation validation preservation
9. REL-GET-01 root 404 / zero views / deduplicated complete views
10. REL-GET-01 trusted factual semantic surprise + paired mutation rejection
11. LC-GET-01 filter/order/keyset/multipage behavior
12. M3-VER-07 intrinsic materially-undecodable historical carrier -> bounded 500
13. M3-VER-07 Relationship factual-state materially-undecodable carrier -> bounded 500
14. M3-VER-08 intrinsic trusted semantic surprise readable
15. M3-VER-08 Relationship trusted semantic surprise readable
16. M3-VER-13 global/Object scope cursor incompatibility + same-scope continuation
17. changed-limit continuation and malformed lifecycle cursor evidence
18. exact 6/6 one-business-statement PostgreSQL census
19. static no-coherent-read / no-read-certification evidence
20. affected RelationshipDefinition mutation regressions
21. affected Relationship mutation/lifecycle-writer regressions
22. accepted M3-S02/S03/S04 regressions
```

Do not close M3-VER-07/08/13 using static assertions alone; they require real public/runtime evidence at the frozen layers.

---

# 11. Regression / non-drift obligations

Preserve:

```text
public route inventory
public RelationshipDefinition / Relationship / Lifecycle DTO shapes
strict request validation and existing error catalogue
RelationshipDefinition list/version ordering and filters
Relationship factual identities/properties/version fields
lifecycle filters and DTO discrimination
lifecycle ordering (occurred_at,id) DESC
all canonical cursor keys/identities
S04 Object-scoped lifecycle semantics
S04 object_components / object_relationships cursor repairs
Object/ObjectTemplate/DataType accepted M3 behavior
all mutation semantic validation
schema/migration/dependency/lock/project-version non-delta
cursor codec v1
```

Changes to legacy tests are allowed only when frozen S05 read-boundary expectations explicitly replace pre-M3 read-side recertification. Narrow such changes to the six S05 GET surfaces. Do not silently alter unrelated mutation expectations.

---

# 12. Candidate verification gate

Run and record at minimum:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

Run mandatory focused PostgreSQL evidence for:

```text
RD-GET-01..04
REL-GET-01
LC-GET-01
M3-VER-07
M3-VER-08
M3-VER-13
six-route statement census
RD aggregate/root pagination
Relationship trusted factual projection
lifecycle keyset/scope behavior
```

Run all directly affected RelationshipDefinition/Relationship/lifecycle regressions and accepted M3-S02/S03/S04 evidence.

Run:

```text
uv run pytest -q -m "not postgresql"
```

Then run the complete repository suite with the required PostgreSQL environment.

Normative:

```text
skip / xfail / automatic rerun = 0 / 0 / 0
```

Report already-censused third-party warnings separately. Any new project warning/failure is a finding.

If any mandatory gate is unexecuted or fails, keep S05 IN PROGRESS / blocked. Do not claim candidate-ready.

---

# 13. Candidate status / publication discipline

Only when all mandatory S05 evidence and candidate gates pass may the implementer publish:

```text
M3-S05 — CANDIDATE READY FOR REVIEW
```

The implementer must not mark:

```text
M3-S05 COMPLETED
M3-S06 READY/AUTHORIZED
M3 accepted/delivered
M3-VER-04/05/06/09/12/19 globally PASS
```

The primary bundles **M3-VER-07, M3-VER-08 and M3-VER-13** may and must be reported PASS if their complete frozen S05 evidence passes.

Commit and push the complete candidate directly to branch `M3` according to the current project operating model. Do not create a PR.

After push verify:

```text
working tree clean
local HEAD == origin/M3 == remote M3
candidate commit identified
no unexpected changed files
no schema/migration/dependency/lock/version/route/DTO/cursor-codec drift
M3-S06 remains NOT AUTHORIZED
```

Keep this execution aid in `docs/milestones/M3/wip/` while S05 is active. Reviewer removes it only after accepted completion.

---

# 14. Required final handoff from Codex

Report at minimum:

```text
cycle/slice
branch
authorization baseline
prompt baseline
candidate commit
push/sync state
working-tree state
PR state
operational slice state
M3-S06 authorization state

changed files
route-by-route realization RD-GET-01..04 / REL-GET-01 / LC-GET-01
M3-VER-07 result and exact negative fixtures
M3-VER-08 result and intrinsic/Relationship positive fixtures
M3-VER-13 result and cursor scope matrix
six-route PostgreSQL statement-count table
RD root-aggregate pagination evidence
RD parent/exact-child failure distinctions
Relationship exact trusted projection evidence
lifecycle global filters/keyset evidence
mutation-regression evidence
accepted S02/S03/S04 regressions
full verification commands/results
Python/PostgreSQL/uv/pytest/Ruff/Pyright versions
skip/xfail/rerun census
warnings
schema/migration/dependency/lock/version/route/DTO/cursor-codec non-drift
open findings or blockers
```

If all mandatory gates pass, use wording equivalent to:

```text
M3-S05 candidate implemented and ready for reviewer inspection.
```

Do not state that M3-S05 is completed or that M3-S06 is authorized.
