# Codex implementation prompt — M3-S04

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS under `docs/architecture/`, the FINAL/FROZEN M3 contract and architecture set, the FINAL/FROZEN `steps.md`, the ratified technology baseline, and the operational authorization in `status.md`.

If this prompt conflicts with an owning authority, stop the affected work and report the conflict. Do not reinterpret frozen semantics to fit current code or this execution aid.

---

# Assignment

Implement exactly:

```text
M3-S04 — Object trusted projections and path-target cursor repairs
```

Work directly on branch:

```text
M3
```

The human-authorized implementation baseline is:

```text
af482bdd7f1bfad191b624e58e45b351bba4e09d
Authorize M3-S04 implementation
```

The prompt-publication commit is a later documentation-only descendant of that authorization commit. Work from the current `origin/M3`; do not reset the branch to the authorization commit. Confirm the authorization commit remains in ancestry.

Current authorization is exactly:

```text
M3-S00    reviewer-owned COMPLETED
M3-S01    reviewer-owned COMPLETED
M3-S02    reviewer-owned COMPLETED
M3-S03    reviewer-owned COMPLETED
M3-S04    READY — AUTHORIZED
M3-S05    NOT AUTHORIZED / dependency blocked
M3-S06    NOT AUTHORIZED / dependency blocked
M3-S07    NOT AUTHORIZED / dependency blocked
```

Primary stable evidence owned by this slice:

```text
M3-VER-10 — Components cross-parent cursor rejection
M3-VER-11 — Object Relationship cross-object cursor rejection
```

S04 also implements concrete Object-family targets contributing to the global bundles:

```text
M3-VER-04
M3-VER-05
M3-VER-06
M3-VER-07 where an Object/lifecycle carrier case applies
M3-VER-08
M3-VER-09
M3-VER-12
M3-VER-13
M3-VER-19
```

Do **not** claim those global bundles PASS solely from S04. Their primary/global closure remains in later frozen slices (`M3-S05` / `M3-S06` as assigned by `steps.md`).

Do not start `M3-S05`. Do not create a pull request. Do not merge, rebase, force-push, rewrite published history, tag or release.

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

docs/milestones/M3/wip/M3-S04-codex-prompt.md
```

Historical M3 WIP route decisions may be inspected only as non-normative cross-check evidence. They never override the frozen contract/architecture/steps. Relevant cross-checks include:

```text
docs/milestones/M3/wip/obj-get-01-decision.md
docs/milestones/M3/wip/obj-get-02-decision.md
docs/milestones/M3/wip/obj-get-03-decision.md
docs/milestones/M3/wip/obj-get-04-decision.md
docs/milestones/M3/wip/obj-get-05-decision.md
docs/milestones/M3/wip/obj-get-06-decision.md
```

Confirm before behavior changes:

```text
checked-out branch                    M3
origin/M3 ancestry                    includes af482bdd7f1bfad191b624e58e45b351bba4e09d
README active cycle                   M3
contract                              FINAL / FROZEN
architecture set                      FINAL / FROZEN
read-projections ADP-01..03           CLOSED
api ADP-04 / ADP-05                   CLOSED
verification ADP-08                   CLOSED
steps.md                              FINAL / FROZEN
M3-S00..S03                           reviewer-owned COMPLETED
M3-S04                                READY or IN PROGRESS
M3-S05                                NOT AUTHORIZED
relevant reopen                       none
project version                       0.2.0
```

Inspect at minimum before choosing local decomposition:

```text
src/netauto/application/objects.py
src/netauto/application/relationships.py
src/netauto/application/cursors.py

src/netauto/persistence/objects.py
src/netauto/persistence/objecttemplates.py
src/netauto/persistence/relationships.py
src/netauto/persistence/lifecycle.py
src/netauto/persistence/metadata.py
src/netauto/persistence/uow.py

src/netauto/entrypoints/api/objects.py
src/netauto/entrypoints/api/relationships.py
src/netauto/transport/http/objects.py
src/netauto/transport/http/relationships.py

existing Object API/domain/concurrency tests
existing Relationship API/domain/concurrency tests
existing lifecycle tests
accepted M3-S01/S02/S03 evidence modules
all directly affected delivered regressions
```

The current implementation is evidence, not authority. Important current facts to preserve/repair rather than redesign include:

```text
OBJ-GET-01
    ObjectService.list_objects() already uses ordinary UoW + direct one-statement summary page

OBJ-GET-02
    ObjectService.get() loads one Object but then calls _validate_persisted_object()
    -> transitive ObjectTemplate/DataType semantic recertification must be removed from GET

OBJ-GET-03 components
    cursor filters currently contain only slot_name
    -> missing parent_object_id path identity
    current read uses coherent_read(), parent lookup, _schema_specs(), ownership page
    -> fragmented and over-certifying

OBJ-GET-04 owner
    current read uses coherent_read(), child lookup, ownership lookup, parent lookup, _schema_specs()
    -> fragmented and over-certifying

OBJ-GET-05 Object lifecycle
    ObjectService.list_events() currently checks involving Object separately then queries events
    -> object-scoped path therefore exceeds one business statement
    current lifecycle decoder replays mutation-like transition/property rules
    -> must become ADP-03 trusted historical decoder

OBJ-GET-06 Object Relationships
    cursor filters currently omit object_id
    current read uses coherent_read(), path Object lookup, page query, then _validated_many()
    -> missing path binding + broad Relationship/Definition/schema recertification
```

Once pre-flight passes and implementation work actually begins, update `docs/milestones/M3/status.md` from `M3-S04 — READY` to `M3-S04 — IN PROGRESS`. Do not mark it `COMPLETED`.

If a frozen authority is contradicted by the repository, stop the affected behavior and report the contradiction. Do not silently broaden scope.

---

# 2. Hard scope boundary

## In scope

Implement all six canonical Object GET/read routes:

```text
OBJ-GET-01  GET /api/v1/core/objects
OBJ-GET-02  GET /api/v1/core/objects/{object_id}
OBJ-GET-03  GET /api/v1/core/objects/{parent_object_id}/components
OBJ-GET-04  GET /api/v1/core/objects/{child_object_id}/owner
OBJ-GET-05  GET /api/v1/core/objects/{object_id}/lifecycle-events
OBJ-GET-06  GET /api/v1/core/objects/{object_id}/relationships
```

Expected production scope is principally:

```text
src/netauto/application/objects.py
src/netauto/application/relationships.py only for OBJ-GET-06
src/netauto/persistence/objects.py
src/netauto/persistence/relationships.py only for OBJ-GET-06 trusted page
src/netauto/persistence/lifecycle.py for OBJ-GET-05 projector/ADP-03 decoder
src/netauto/entrypoints/api/objects.py only if read wiring requires a non-public-contract change
src/netauto/entrypoints/api/relationships.py only if OBJ-GET-06 wiring requires it
shared cursor helper only if existing ownership genuinely requires it
relevant Object/Relationship/lifecycle tests
operational M3-S04 status/evidence updates
```

## Explicitly out of scope

Do not implement M3-S05 or later work, including:

```text
RelationshipDefinition GET trusted-read rewrite
exact Relationship GET trusted-read rewrite
final/global lifecycle GET one-statement rewrite
complete 22-route cross-family closure
complete 12-route cursor registry closure
single-request representative T3 coherence closure
schema/dependency non-drift final closure
final traceability registry closure
M3 delivery acceptance
```

A shared ADP-03 decoder correction needed by OBJ-GET-05 is allowed even though the decoder is reused by the global lifecycle route. Do not use that shared-helper necessity as permission to rewrite the global lifecycle route's UoW/query shape or claim S05 evidence early.

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
hidden read repair/remediation
weakened mutation validation
new retry/backoff behavior
new public error code
```

Preserve accepted S00-S03 behavior and evidence.

---

# 3. Universal S04 trusted-read rules

Every canonical Object GET must satisfy:

```text
one complete public projection
    -> exactly one authoritative business SQL statement
    -> PostgreSQL statement snapshot
    -> ordinary caller-owned read UoW
    -> no coherent_read() dependency
    -> no mutation semantic certification
```

Representational decoding remains mandatory for fields needed by the public DTO. A required contextual value that cannot be materialized must produce bounded internal failure; do not silently omit/fabricate it.

Do not answer on a GET:

```text
"Would this persisted state pass current mutation admission/transition validation?"
```

Forbidden read-side recertification includes as applicable:

```text
runtime Object schema/DataType validation
Object property canonicalization against current schema
ObjectTemplate publication/admissibility checks
ownership slot semantic admissibility checks
ownership target-lineage compatibility recertification
Relationship aggregate/Definition/schema/topology validation
Relationship property canonicalization
lifecycle transition replay/change-detection/version-increase certification
```

Mutation paths keep all existing validators unchanged.

---

# 4. Exact route matrix

## OBJ-GET-01 — RP-01 DIRECT PAGE

Route:

```text
GET /api/v1/core/objects
```

Preserve canonical filters:

```text
template_id
template_version
canonical_name
```

Preserve request dependency:

```text
template_version requires template_id
```

Cursor identity remains:

```text
route = objects
filters = {
    template_id: None or str(UUID),
    template_version: None or int,
    canonical_name: None or str,
}
key = [str(id)]
ORDER BY id ASC
```

Target is the delivered direct `ObjectSummary` page:

```text
objects
    -> filters
    -> id keyset
    -> ORDER BY id
    -> LIMIT limit + 1
```

Do not broaden this route merely because other Object routes require richer projectors.

Permanent evidence should still measure it at one business statement and preserve filter/request/cursor behavior.

## OBJ-GET-02 — RP-02 DIRECT EXACT

Route:

```text
GET /api/v1/core/objects/{object_id}
```

The public projection is intrinsic Object state only:

```text
id
canonical_name
template_id
template_version
properties
```

Target:

```text
one exact objects row
0 rows -> 404 resource_not_found
1 row  -> Object DTO
```

Persisted `properties` must decode as the response's required JSON object/string-key carrier. Do not load ObjectTemplate, effective schema, DataTypes or constraints merely to re-certify the persisted Object.

Remove GET-time dependence on `_validate_persisted_object()` / `_schema_specs()` / runtime property canonicalization.

Positive trusted-read evidence must include a representable persisted Object property surprise that would fail current mutation/schema recertification but is still a valid public JSON-object carrier and therefore GET-readable.

Paired mutation evidence must prove Object create/data-change/schema-change validation remains strong.

## OBJ-GET-03 — RP-07 + EXACT-CHAIN CONTEXT

Route:

```text
GET /api/v1/core/objects/{parent_object_id}/components
```

Cursor identity correction is mandatory:

```text
route = object_components
filters = {
    parent_object_id: str(parent_object_id),
    slot_name: slot_name,
}
key = [str(child_object_id)]
ORDER BY child_object_id ASC
```

`parent_object_id` is semantic query identity, not keyset position.

Required public states:

```text
parent Object absent
    -> 404 resource_not_found

parent exists + zero matching ownership facts
    -> 200 empty page

parent exists + facts + unique required declaration context
    -> complete ComponentProjection page
```

Each public item requires:

```text
slot_declaring_template_id
slot_name
child_object_id
```

Projection context comes from the parent Object's exact pinned template-version chain:

```text
parent Object (template_id, template_version)
    -> exact ObjectTemplateVersion
    -> persisted exact parent pins recursively
    -> component declarations by (exact template, exact version, slot_name)
```

Do **not** use stable lineage ancestry as a substitute for the exact chain.

The read must not build the complete effective schema or load DataTypes/properties solely because mutation helpers do.

However, `slot_declaring_template_id` is a mandatory public field. Therefore context completion is not semantic certification:

```text
exactly one matching declaration context
    -> project item

zero matching declarations for a persisted ownership fact
more than one matching declaration where one declaring template is required
    -> bounded 500 internal_error
    -> never silently omit the ownership fact
    -> never invent a declaring template
```

The statement must preserve parent existence independently from child/page membership and apply keyset/limit to public ownership facts, not context-expanded rows.

M3-VER-10 primary evidence:

```text
cursor issued for parent A + slot filter X
reused for parent B + same slot filter X
    -> 400 invalid_cursor

same-parent continuation
    -> success

changed limit only
    -> success
```

Also prove true multipage traversal without omission/duplication.

## OBJ-GET-04 — RP-08 + EXACT-CHAIN CONTEXT

Route:

```text
GET /api/v1/core/objects/{child_object_id}/owner
```

Required states:

```text
child Object absent
    -> 404 resource_not_found

child exists + no ownership fact
    -> 200 null

ownership fact exists + required context materializable
    -> OwnerProjection

ownership fact exists + required context not materializable/ambiguous
    -> bounded 500 internal_error
    -> never convert to null
```

Public owner projection is:

```text
parent_object_id
slot_declaring_template_id
slot_name
```

When ownership exists, use the parent Object's exact pinned template-version chain solely to locate the persisted component declaration needed for `slot_declaring_template_id`.

Do not:

```text
load/revalidate full effective schema
load DataTypes/properties
re-certify target lineage compatibility
re-certify ownership mutation admissibility
perform a separate parent-existence lookup merely to certify the FK
```

One statement only; ordinary UoW.

Permanent evidence must distinguish 404, null, materialized owner, and non-materializable context failure.

## OBJ-GET-05 — RP-03 + ADP-03 TRUSTED HISTORICAL DECODER

Route:

```text
GET /api/v1/core/objects/{object_id}/lifecycle-events
```

Cursor identity remains the delivered lifecycle identity:

```text
route = lifecycle_events
filters include all public lifecycle filters plus:
    involving_object_id = str(path object_id)
key = [canonical occurred_at, str(id)]
ORDER BY occurred_at DESC, id DESC
```

Required path/page states:

```text
path Object absent
    -> 404 resource_not_found

path Object exists + zero matching events
    -> 200 empty page

path Object exists + events
    -> normal page
```

The target is one parent-rooted statement that combines Object existence and the filtered event page. Do not issue a separate `ObjectStore.get()` plus event SELECT.

### ADP-03 decoder — exact read responsibility

The historical decoder asks only:

```text
can persisted carriers be materialized into the required typed historical response?
```

It must not ask whether the historical state/transition would pass today's mutation rules.

Historical `JsonValue` grammar is recursive:

```text
None
str
bool
int excluding bool
list[JsonValue] including []
dict[str, JsonValue] including {}
```

Do not impose runtime-property restrictions such as:

```text
property identifier grammar
non-null runtime property value
non-empty list
homogeneous list primitive type
current DataType/schema canonicality
```

Historical Object snapshot required fields:

```text
id                 string parseable as UUID
canonical_name     str
template_id        string parseable as UUID
template_version   int excluding bool
properties         dict[str, JsonValue]
```

Do not recertify canonical-name length or positive template version. Extra unneeded historical fields are ignored; exact JSON key-set equality is not required.

Historical Relationship factual state required fields:

```text
relationship_definition_version  int excluding bool
properties                       dict[str, JsonValue]
```

Do not require version > 0 as a read semantic rule. Extra unneeded fields are ignored.

For event families, keep only presence/type/discriminant checks necessary to construct the public event DTO. Remove transition replay such as:

```text
RENAME before/after semantic equality rules
DATA_CHANGE changedness/version recertification
SCHEMA_CHANGE version-increase recertification
Relationship DATA_CHANGE changedness/version recertification
Relationship SCHEMA_CHANGE version-increase recertification
```

Materially undecodable required carriers remain bounded `500 internal_error`; no repair/fabrication/silent omission.

Because the decoder is shared with global lifecycle, implement it as the common ADP-03 decoder. Do **not** rewrite the global lifecycle route's read/UoW shape in S04; S05 owns global lifecycle GET completion and primary M3-VER-08/13 closure.

S04 supporting evidence must include at least one Object-scoped representable historical semantic surprise that now reads successfully and at least one materially undecodable required snapshot carrier producing bounded 500 if an applicable safe PostgreSQL fixture exists.

## OBJ-GET-06 — RP-07 TARGET-ROOTED RELATIONSHIP VIEW PAGE

Route:

```text
GET /api/v1/core/objects/{object_id}/relationships
```

Cursor identity correction is mandatory:

```text
route = object_relationships
filters = {
    object_id: str(object_id),
    relationship_definition_id: None or str(UUID),
    name: name,
}
key = [str(relationship_id), str(destination_object_id), name]
ORDER BY (relationship_id, destination_object_id, name) ASC
```

Required public states:

```text
path Object absent
    -> 404 resource_not_found

path Object exists + zero semantic views
    -> 200 empty page

path Object exists + semantic views
    -> complete ObjectRelationshipView page
```

Public item fields are projected from persisted factual/runtime/Resolution state. The GET must not call `_validated_many()` or reconstruct RelationshipDefinition/ObjectTemplate/DataType semantic closure simply to certify page rows.

Remove page-vs-reconstructed-aggregate semantic comparison.

Public semantic derivation is:

```text
derive complete ObjectRelationshipView rows
    -> DISTINCT / equivalent semantic deduplication
    -> keyset (relationship_id, destination_object_id, name)
    -> ORDER BY same tuple
    -> LIMIT limit + 1 PUBLIC ITEMS
```

Deduplication must occur before keyset/order/limit. Do not apply SQL limit to a raw duplicate-producing rowset when doing so can change public item cardinality.

`properties` still require representational decoding as a JSON object/string-key map because they are public fields; no Relationship schema/property canonicalization is allowed.

M3-VER-11 primary evidence:

```text
cursor issued for Object A + same Relationship filters
reused for Object B
    -> 400 invalid_cursor

same-Object continuation
    -> success

changed limit only
    -> success
```

Permanent evidence must exercise the full compound key and prove multipage no omission/duplication.

---

# 5. Cursor rules — primary S04 ownership

M3 keeps cursor codec v1 unchanged:

```text
v
route
filters
key
```

S04 must change only canonical semantic identities for the two frozen path-target repairs:

```text
object_components
    add parent_object_id

object_relationships
    add object_id
```

Do not add path targets to position keys. Do not add `limit` to semantic identity.

For both repaired routes permanent evidence must prove:

```text
same path/filter identity -> continuation accepted
same identity + changed limit -> accepted
changed path target -> invalid_cursor
changed query membership filter -> invalid_cursor
wrong route -> invalid_cursor where directly exercised
malformed/wrong-length/wrong-type key -> invalid_cursor
```

`M3-VER-10` and `M3-VER-11` must be fully PASS on the candidate. Supporting cursor targets contribute to global M3-VER-09/12 but do not close them globally.

---

# 6. Read/write semantic-authority pairing

S04 must prove both sides.

Representative read-side surprises should cover material Object-family validators removed from GET, such as:

```text
intrinsic Object properties representable as JSON object but not valid under current schema/DataType rules
persisted ownership fact whose required declaring-slot context can still be projected without running broad semantic admission
Object Relationship factual page representable without Definition/schema/topology recertification
historical lifecycle before/after values that are DTO-decodable but violate current transition certification
```

Use only structurally committable persisted states unless a specific M3-VER-07 negative carrier fixture intentionally uses a documented safe corruption mechanism.

Paired write-side evidence must keep existing validation active for representatives including:

```text
Object create/data-change/schema-change property validation
ownership slot/target/cycle validation
Relationship mutation topology/schema/property validation
lifecycle writes producing canonical event shapes
```

Do not weaken write validators to make read tests pass.

---

# 7. One-business-statement evidence — mandatory PostgreSQL

Measure independently on the production runtime engine:

```text
OBJ-GET-01  GET /objects
OBJ-GET-02  GET /objects/{id}
OBJ-GET-03  GET /objects/{parent}/components
OBJ-GET-04  GET /objects/{child}/owner
OBJ-GET-05  GET /objects/{id}/lifecycle-events
OBJ-GET-06  GET /objects/{id}/relationships
```

For each target invocation:

```text
business SQL statement count == 1
```

Use direct deterministic SQL observation on the real PostgreSQL runtime connection, e.g. SQLAlchemy `before_cursor_execute` on the actual runtime `AsyncEngine.sync_engine`, following accepted S02/S03 evidence practice.

The measurement window begins immediately before each target GET and is cleared per route. Setup/cleanup/warmup SQL stays outside the measured invocation.

A helper SELECT is still a business statement. There is no exemption for internal helper calls.

Also add static evidence that the six GET application paths do not depend on:

```text
coherent_read
Object runtime semantic recertification helpers
full effective-schema/DataType loaders where projection-only context suffices
Relationship _validated_many or equivalent mutation aggregate certification
transition-certifying lifecycle decoder logic
```

Missing `TEST_DATABASE_URL` makes mandatory S04 PostgreSQL evidence `BLOCKED`, never PASS. Do not substitute SQLite, Docker/Testcontainers, invented credentials or fake statement counters.

---

# 8. Permanent S04 evidence

A dedicated module such as:

```text
tests/test_m3_s04_object_reads.py
```

is acceptable but not mandatory.

Permanent evidence must cover at minimum:

```text
1. OBJ-GET-01 public filters/order/pagination + one statement
2. OBJ-GET-02 trusted intrinsic read + 404 + representable semantic surprise
3. OBJ-GET-03 parent 404 vs empty vs nonempty contextual page
4. OBJ-GET-03 unique declaring-template context and context-failure internal boundary
5. M3-VER-10 parent A cursor rejected on parent B; same-parent continuation valid
6. OBJ-GET-04 child 404 vs detached null vs materialized owner vs context failure
7. OBJ-GET-05 path 404 vs empty/nonempty page
8. OBJ-GET-05 trusted ADP-03 historical semantic-surprise decoding
9. applicable OBJ lifecycle materially-undecodable carrier -> bounded 500
10. OBJ-GET-06 path 404 vs empty/nonempty deduplicated page
11. OBJ-GET-06 compound-key multipage traversal without omission/duplication
12. M3-VER-11 Object A cursor rejected on Object B; same-Object continuation valid
13. changed-limit cursor continuation on all affected cursor routes
14. malformed/wrong-type cursor-key rejection
15. exact 6/6 one-business-statement PostgreSQL census
16. static no-coherent-read / no-read-certification evidence
17. affected Object mutation validation regressions
18. affected Relationship mutation validation regressions
19. accepted M3-S01/S02/S03 regressions
```

Do not rely only on encode/decode cursor unit tests for M3-VER-10/11 or keyset completeness; use public HTTP multipage behavior.

---

# 9. Regression / non-drift obligations

Preserve:

```text
public Object route inventory
public Object/Component/Owner/Lifecycle/ObjectRelationship DTO shapes
strict request validation and existing error catalogue
Object list filter dependency template_version -> template_id
all canonical orderings/keysets
lifecycle filter semantics
lifecycle route-scope involving_object_id identity
Object/Relationship mutation semantics
accepted M3-S00 Location behavior
accepted M3-S01 parent tri-state behavior
accepted M3-S02 DataType trusted reads
accepted M3-S03 ObjectTemplate trusted reads
schema/migration/dependency/lock/project-version non-delta
cursor codec v1
```

Changes to legacy tests are allowed only when a frozen S04 read-boundary expectation explicitly replaces a pre-M3 read-side recertification expectation. Narrow such changes to Object/Object-scoped lifecycle/Object-relative Relationship reads; do not silently migrate RelationshipDefinition/exact Relationship/global lifecycle GET expectations owned by S05.

---

# 10. Candidate verification gate

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

Run mandatory real-PostgreSQL focused S04 evidence including:

```text
M3-VER-10
M3-VER-11
six-route statement census
trusted Object read evidence
components/owner contextual projection evidence
Object-scoped lifecycle ADP-03 evidence
Object Relationship dedup/keyset evidence
```

Run all directly affected Object, ownership, lifecycle and Relationship regressions, plus accepted M3-S01/S02/S03 evidence.

Run:

```text
uv run pytest -q -m "not postgresql"
```

Then run the complete repository suite with the required PostgreSQL environment for the candidate gate.

Normative:

```text
skip / xfail / automatic rerun = 0 / 0 / 0
```

A reviewed already-censused third-party warning may be reported separately. Any new project warning/failure is a finding.

Do not claim PASS for an unexecuted mandatory gate.

---

# 11. Candidate status / publication discipline

When coding actually begins, S04 may move from `READY` to `IN PROGRESS`.

Only when:

```text
OBJ-GET-01..06 all realize frozen RP shapes
6 / 6 Object GETs measure exactly one business SQL statement on PostgreSQL
M3-VER-10 PASS
M3-VER-11 PASS
same-target cursor continuations PASS
context-completion failure boundaries PASS
Object-scoped ADP-03 decoder evidence PASS
mutation regressions PASS
affected prior M3 regressions PASS
static/build/full candidate gates PASS
```

may the implementer publish operational state:

```text
M3-S04 — CANDIDATE READY FOR REVIEW
```

The implementer must not mark:

```text
M3-S04 COMPLETED
M3-S05 READY/AUTHORIZED
M3 accepted/delivered
all global M3-VER bundles PASS
```

Those are reviewer/later-slice decisions.

Commit and push the complete candidate directly to branch `M3` according to the current project operating model. Do not create a PR.

After push verify:

```text
working tree clean
local HEAD == origin/M3 == remote M3
candidate commit identified
no unexpected changed files
no forbidden schema/migration/dependency/lock/version/route/DTO drift
M3-S05 remains NOT AUTHORIZED
```

Keep this execution aid in `docs/milestones/M3/wip/` while S04 is active. Reviewer removes it only after accepted completion.

If a mandatory gate fails, keep S04 in `IN PROGRESS` / review-blocked state and report the exact blocker. Do not publish a candidate-ready state merely because focused tests pass.

---

# 12. Required final handoff from Codex

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
M3-S05 authorization state

changed files
route-by-route realization OBJ-GET-01..06
cursor filters before/after for object_components and object_relationships
M3-VER-10 result
M3-VER-11 result
six-route PostgreSQL statement-count table
trusted-read surprise evidence
context-completion failure evidence
ADP-03 Object-scoped lifecycle evidence
keyset/multipage evidence
mutation-regression evidence
full verification commands/results
Python/PostgreSQL/uv/pytest/Ruff/Pyright versions
skip/xfail/rerun census
warnings
schema/migration/dependency/lock/version/route/DTO/cursor-codec non-drift
open findings or blockers
```

If all mandatory gates pass, use wording equivalent to:

```text
M3-S04 candidate implemented and ready for reviewer inspection.
```

Do not state that M3-S04 is completed or that M3-S05 is authorized.
