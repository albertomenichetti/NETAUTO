# Codex implementation prompt — M3-S02

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS under `docs/architecture/`, the FINAL/FROZEN M3 contract and architecture set, the FINAL/FROZEN `steps.md`, the ratified technology baseline, and the operational authorization in `status.md`.

If this prompt conflicts with any owning authority, stop the affected work and report the conflict. Do not reinterpret a frozen decision to fit current code or this execution aid.

---

# Assignment

Implement exactly:

```text
M3-S02 — DataType trusted one-statement read projections
```

Work directly on branch:

```text
M3
```

The human-authorized implementation baseline is:

```text
5fc50f12c77f7bdb8604d0f322ec657a3d6f6f07
Authorize M3-S02 implementation
```

The prompt-publication commit is a later documentation-only descendant of that authorization commit. Work from the current `origin/M3`; do not reset the branch to the authorization commit. Confirm that the authorization commit remains in ancestry.

Current authorization is exactly:

```text
M3-S00    reviewer-owned COMPLETED
M3-S01    reviewer-owned COMPLETED
M3-S02    READY — AUTHORIZED
M3-S03    NOT AUTHORIZED / dependency blocked
M3-S04    NOT AUTHORIZED / dependency blocked
M3-S05    NOT AUTHORIZED / dependency blocked
M3-S06    NOT AUTHORIZED / dependency blocked
M3-S07    NOT AUTHORIZED / dependency blocked
```

Deliver the complete bounded S02 DataType read capability and permanent DataType evidence targets contributing to:

```text
M3-VER-04
M3-VER-05
M3-VER-06
M3-VER-07 where a DataType carrier case is applicable
M3-VER-09
M3-VER-12
M3-VER-19
```

Important evidence ownership rule:

```text
M3-S02 owns no exclusive primary stable M3-VER bundle.
```

Therefore this slice must make its DataType targets concrete and PASS, but it must **not** claim that the complete global `M3-VER-04/05/06/07/09/12/19` bundles are PASS. Their cross-family/global closure is owned later, principally by M3-S06 as frozen by `steps.md`.

Do not start `M3-S03`. Do not create a pull request. Do not merge, rebase, force-push, rewrite published history, tag or release.

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

docs/milestones/M3/wip/M3-S02-codex-prompt.md
```

Read every applicable ratified `STACK-*` decision in `docs/general/technology_baseline.md`, especially the PostgreSQL, SQLAlchemy Core, explicit UoW, FastAPI/Pydantic and deterministic testing decisions.

Historical M3 WIP discovery files may be consulted only as non-normative evidence. They never override the frozen contract, architecture or steps owners.

Confirm from the repository before changing behavior:

```text
checked-out branch                    M3
origin/M3 ancestry                    includes 5fc50f12c77f7bdb8604d0f322ec657a3d6f6f07
README active cycle                   M3
contract                              FINAL / FROZEN
read-projection architecture          FINAL / FROZEN — ADP-01/02/03 CLOSED
API/cursor architecture               FINAL / FROZEN
verification architecture             FINAL / FROZEN — ADP-08 CLOSED
steps.md                              FINAL / FROZEN
M3-S00                                COMPLETED
M3-S01                                COMPLETED
M3-S02                                READY or IN PROGRESS
M3-S03                                NOT AUTHORIZED
open applicable reopen                none
project version                       0.2.0
```

Inspect the current implementation before selecting local decomposition. At minimum inspect:

```text
src/netauto/application/datatypes.py
src/netauto/persistence/datatypes.py
src/netauto/entrypoints/api/datatypes.py
src/netauto/application/cursors.py
src/netauto/persistence/uow.py
src/netauto/persistence/metadata.py
src/netauto/domain/datatypes.py
src/netauto/domain/primitives.py
src/netauto/transport/http/datatypes.py

existing DataType API/application/persistence tests
existing DataType mutation/concurrency/semantic tests
existing cursor tests
accepted M3-S00 and M3-S01 evidence tests
```

At minimum include the repository's current equivalents of:

```text
tests/test_datatype_api.py
tests/test_datatype_concurrency.py
tests/test_datatype_semantic_concurrency.py
tests/test_m2_s03_semantic_concurrency.py
tests/test_m3_s00_cli_location.py
tests/test_m3_s01_parent_tristate.py
```

Discover every other directly affected accepted test rather than assuming this list is exhaustive.

## Current AS-IS evidence to understand, not redesign around

The current code already demonstrates the exact implementation gap that S02 owns:

```text
DataTypeService.get_lineage()
    -> coherent_read()
    -> DataTypeStore.get_lineage()
    -> _validate_default_pointers()
    -> possible second DataTypeVersion query
    -> read-side default publication recertification

DataTypeService.list_lineages()
    -> coherent_read()
    -> DataTypeStore.list_lineages()
    -> _validate_default_pointers()
    -> possible second DataTypeVersion query
    -> read-side default publication recertification

DataTypeService.list_versions()
    -> ordinary UoW
    -> get_lineage(parent)
    -> list_versions(children)
    -> two business SELECTs

DataTypeService.get_version()
    -> ordinary UoW
    -> one exact composite DataTypeVersion SELECT
    -> already close to the frozen RP-02 target
```

Current persistence also already has useful neutral row materializers and direct queries. Reuse them only where that reuse does not reintroduce semantic certification or extra statements.

The current implementation is evidence, not authority. The frozen architecture below determines the target behavior.

Once pre-flight passes and implementation work actually begins, update `docs/milestones/M3/status.md`:

```text
M3-S02 — READY
    -> M3-S02 — IN PROGRESS
```

Do not mark M3-S02 `COMPLETED`.

If a mandatory pre-flight condition fails or implementation appears to require a frozen architecture contradiction, stop the affected work and report it rather than silently broadening the slice.

---

# 2. Hard scope boundary

## 2.1 In scope

Exactly these four canonical DataType GETs:

```text
DT-GET-01  GET /api/v1/core/datatypes
DT-GET-02  GET /api/v1/core/datatypes/{datatype_id}
DT-GET-03  GET /api/v1/core/datatypes/{datatype_id}/versions
DT-GET-04  GET /api/v1/core/datatypes/{datatype_id}/versions/{version}
```

And only the implementation/evidence necessary to give them the frozen trusted-read behavior:

```text
ordinary read UoW ownership
one authoritative business SQL statement per request
trusted persisted projection
representational decoding
404 / empty-page classification
existing filters/order/keysets/cursors
DataType-specific permanent M3 evidence
statement observation against real PostgreSQL
mutation-regression preservation
operational candidate status/evidence
```

Expected production scope is principally:

```text
src/netauto/application/datatypes.py
src/netauto/persistence/datatypes.py
src/netauto/entrypoints/api/datatypes.py only if minimal read wiring changes are required
relevant DataType tests
```

Application cursor helpers may be used as delivered. No cursor codec change is expected or authorized.

## 2.2 Explicitly out of scope

Do not implement any part of M3-S03 or later slices, including:

```text
ObjectTemplate trusted read rewrite
Object trusted read rewrite
Object components cursor path-target repair
Object Relationship cursor path-target repair
RelationshipDefinition trusted read rewrite
Relationship trusted read rewrite
lifecycle trusted decoder rollout
22-route integrated closure
full 12-route cursor closure
complete M3 traceability closure
final M3 acceptance/delivery
```

Do not introduce:

```text
new public route
new public DTO field or shape
new business resource
new API query parameter
new cursor route id
new cursor payload version
schema/table/index/constraint change
Alembic migration
runtime dependency
uv.lock semantic change
project-version change
new database technology
ORM migration
raw SQL bypass of the established SQLAlchemy Core architecture merely for convenience
new mutation semantics
weakened mutation validation
new public error code
new cross-release behavior
```

Do not change completed M3-S00 Location behavior or completed M3-S01 parent-tri-state behavior.

---

# 3. Frozen read-responsibility boundary — ADP-01

Every S02 GET must realize this responsibility chain:

```text
HTTP adapter
    -> lexical request parsing
    -> public DTO serialization

application read service
    -> request semantics
    -> cursor route/filter/key validation
    -> ordinary read UoW ownership
    -> 404 / Page classification

persistence read projector
    -> complete persisted projection required by this request
    -> target-presence evidence where needed
    -> canonical filter / keyset / order / limit
    -> representational materialization only
    -> no mutation-semantic certification
```

The persistence projector:

```text
runs on the caller-owned connection
opens no UoW
commits no UoW
nests no UoW
```

For each canonical DataType GET:

```text
one complete public projection
    -> exactly one authoritative business SQL statement
    -> one PostgreSQL statement snapshot
    -> ordinary read UoW
    -> no coherent_read() dependency
```

`coherent_read()` remains valid infrastructure elsewhere; S02 does not deprecate or remove it globally.

## 3.1 Read-side semantic certification is forbidden

A DataType GET must not ask:

```text
"Would this persisted state pass current mutation admission?"
```

In particular, S02 removes read-side dependency on:

```text
_validate_default_pointers()
default target PUBLISHED recertification
constraint canonicalization merely to prove persisted constraints
mutation-oriented validation of namespace/name/base-type semantics
other dependency loads used only to certify persisted state
```

Do **not** invoke these mutation-oriented helpers from the four S02 GETs merely because they already exist:

```text
canonicalize_constraints(...)
validate_qualified_name(...)
mutation candidate admission helpers
publication/default admissibility helpers
```

Closed-enum/typed carrier construction needed to represent public state is allowed and required. For example, converting a persisted status carrier into the delivered `VersionStatus` enum or a persisted base-type carrier into the delivered primitive enum is representational decoding, not mutation recertification.

## 3.2 Mutation authority must remain strong

Do not weaken writes to make read tests pass.

Existing mutations must continue to enforce, among other existing rules:

```text
qualified-name validation
constraint canonicalization/admission
DRAFT/revision checks
publish transition checks
set-default target existence and PUBLISHED admissibility
active-consumer deprecation constraints
delete/reference constraints
```

Permanent paired evidence must demonstrate at least one meaningful read/write boundary:

```text
representable persisted semantic surprise
    -> GET remains readable

corresponding invalid new mutation candidate/transition
    -> mutation remains rejected by the delivered structured boundary
```

---

# 4. Frozen DataType route matrix — ADP-02

Implement the exact frozen mapping:

| ID | Public route | Frozen pattern | Required consequence |
|---|---|---|---|
| `DT-GET-01` | `GET /datatypes` | `RP-01 DIRECT PAGE` | direct lineage page; project `default_version` without target certification |
| `DT-GET-02` | `GET /datatypes/{id}` | `RP-02 DIRECT EXACT` | direct lineage exact read; no default-target lookup |
| `DT-GET-03` | `GET /datatypes/{id}/versions` | `RP-03 PARENT-ROOTED PAGE` | one statement preserving parent 404 vs existing-parent empty page |
| `DT-GET-04` | `GET /datatypes/{id}/versions/{version}` | `RP-02 DIRECT EXACT` | exact composite version row; no separate lineage read |

Do not substitute a more elaborate pattern merely because it exists for another resource family.

---

# 5. DT-GET-01 — `/datatypes` — RP-01 DIRECT PAGE

Preserve public filters exactly:

```text
namespace
name
cursor
limit
```

Preserve semantic cursor filters exactly:

```text
{
    "namespace": namespace,
    "name": name,
}
```

Preserve complete public keyset/order:

```text
key        (namespace, name)
ORDER BY   namespace ASC, name ASC
```

Required persistence shape:

```text
datatypes
    -> namespace/name filters
    -> keyset predicate
    -> ORDER BY namespace, name
    -> LIMIT limit + 1
```

The selected lineage row directly owns public fields including `default_version`.

Critical S02 rule:

```text
default_version is projected as persisted.
No second DataTypeVersion query may verify that it exists or is PUBLISHED.
```

The application may compose `Page` and next cursor after the statement returns; cursor encoding is not a business SQL statement.

---

# 6. DT-GET-02 — `/datatypes/{id}` — RP-02 DIRECT EXACT

Required logical shape:

```text
datatypes WHERE id = :datatype_id
    -> 0 rows  -> application resource_not_found
    -> 1 row   -> DataType public projection
```

Do not load the default version merely to certify `default_version`.

No `coherent_read()`.
No second business statement.
No default publication recertification.

A persisted lineage whose `default_version` points to an existing non-PUBLISHED version is a useful positive trusted-read fixture if the delivered schema permits it: the GET should return the persisted pointer rather than failing read-side certification.

Do not alter production schema or disable constraints to manufacture that fixture.

---

# 7. DT-GET-03 — `/datatypes/{id}/versions` — RP-03 PARENT-ROOTED PAGE

This is the principal one-statement shape change in S02.

Public request behavior remains:

```text
path target datatype_id
query status?
query cursor?
query limit?
```

Cursor identity remains exactly:

```text
route = "datatype_versions"
filters = {
    "datatype_id": str(datatype_id),
    "status": None or status.value,
}
key = [version]
ORDER BY version ASC
```

The one authoritative statement must preserve both facts:

```text
stable DataType parent exists?
matching version rows after filters/keyset?
```

Required public outcomes:

```text
parent absent
    -> 404 resource_not_found

parent present + no versions matching status/keyset
    -> 200 page with items=[]

parent present + matching versions
    -> normal ordered page + next_cursor
```

The status/keyset predicates must not erase the parent-existence evidence.

A valid implementation may use one SQLAlchemy Core statement with an outer-join/CTE/lateral/typed-union/other equivalent shape, provided all frozen RP-03 guarantees hold.

Do not prescribe a second existence SELECT.
Do not perform a hidden parent GET in application.
Do not treat empty filtered children as parent absence.

Use `LIMIT limit + 1` semantics over real child page membership, not over an artificial sentinel in a way that corrupts pagination.

If a one-row parent-presence sentinel is used inside the result shape, it must be impossible for that sentinel to alter public item count, keyset order or next-cursor computation.

---

# 8. DT-GET-04 — `/datatypes/{id}/versions/{version}` — RP-02 DIRECT EXACT

Required logical shape:

```text
datatype_versions
WHERE datatype_id = :datatype_id
  AND version = :version

0 rows -> resource_not_found for datatype_version
1 row  -> exact DataTypeVersion projection
```

No separate stable-lineage existence read is allowed.

The current AS-IS path is already structurally close to this shape. Prefer a minimal correction or preservation rather than unnecessary abstraction churn.

Persisted exact-version fields must be representationally decoded for the delivered DTO:

```text
datatype_id
version
revision
status
base_type
constraints
```

Do not run `canonicalize_constraints()` on the persisted constraints during GET.

---

# 9. Representational decoding and materially undecodable carriers

Trusted read does **not** mean untyped pass-through.

The projector/application must still materialize required public typed state.

Allowed/required representational decoding includes:

```text
UUID carrier -> UUID
status string -> delivered closed VersionStatus
base_type string -> delivered closed primitive type
version/revision -> integer
constraints -> JSON object shape required by the public DTO
```

A persisted carrier that is representable but semantically surprising under current mutation rules remains readable.

A persisted carrier that cannot be materialized into a mandatory public field must produce the existing bounded internal-failure behavior:

```text
500 internal_error
no fabricated default
no silent item omission
no automatic repair
```

For the DataType-specific target contributing to `M3-VER-07`, use a corruption that can be represented by the delivered schema without altering schema/constraints. A likely candidate is a JSON/JSONB `constraints` carrier with a non-object JSON shape, if the current schema permits it. Verify the schema before selecting the fixture.

Do not drop database constraints, alter metadata, disable validation globally or introduce a test-only production bypass simply to create a corruption case.

If no DataType carrier case is actually possible under the delivered schema without violating the frozen fixture policy, record that fact precisely; do not fabricate a `M3-VER-07` PASS claim. The S02 steps explicitly qualify this contribution as applicable only where a DataType projection carrier case is applicable.

---

# 10. Trusted-read semantic-surprise evidence

Permanent real-PostgreSQL evidence should prove the DataType portion of the read-authority correction.

At minimum cover a representative persisted state that the old GET path would reject only because of mutation-style recertification but that remains public-DTO representable.

Preferred fixture where schema permits:

```text
DataType lineage default_version -> existing DRAFT DataTypeVersion
```

Expected read behavior:

```text
GET /datatypes/{id}
    -> 200
    -> default_version projected exactly as persisted

GET /datatypes filtered to that lineage
    -> 200
    -> lineage projected; no recertification failure
```

Paired mutation behavior must remain:

```text
POST /datatypes/{id}/set-default {version: <DRAFT>}
    -> existing dependency_not_admissible / delivered state-conflict behavior
```

Also consider a DTO-representable constraints object that violates current constraint canonicalization semantics. An exact GET may return the persisted JSON object as factual state, while a new revise/create candidate with the analogous invalid constraints must still be rejected.

Do not alter public response shapes to expose that this state is surprising.

---

# 11. Cursor and pagination evidence for the two DataType cursor routes

S02 contributes DataType targets to the global cursor bundles; it does not close the twelve-route matrix globally.

## `datatypes`

Preserve exactly:

```text
route id   datatypes
filters    namespace, name
key        [namespace, name]
order      namespace ASC, name ASC
```

Permanent DataType evidence must include real multipage traversal and prove:

```text
same semantic identity continuation -> accepted
same identity + changed limit only   -> accepted
changed namespace/name filter        -> invalid_cursor
malformed/wrong-shape key            -> invalid_cursor where directly exercised
no omission/duplication over multipage traversal
```

## `datatype_versions`

Preserve exactly:

```text
route id   datatype_versions
filters    datatype_id, status
key        [version]
order      version ASC
```

Permanent DataType evidence must include:

```text
same parent/status continuation      -> accepted
same identity + changed limit only   -> accepted
changed status                       -> invalid_cursor
cursor from parent A reused on B     -> invalid_cursor
true multipage traversal             -> no omission/duplication
```

Do not include `limit` in cursor semantic identity.
Do not change codec v1 or route ids.

---

# 12. Request/path-target public compatibility

Preserve delivered request behavior for the four routes.

At minimum permanent/regression evidence must retain:

```text
unknown query                       -> 400 invalid_request
repeated query                      -> 400 invalid_request
malformed UUID/path integer/status  -> 400 invalid_request
missing exact lineage               -> 404 resource_not_found
missing exact version               -> 404 resource_not_found
missing parent on versions list     -> 404 resource_not_found
existing parent + zero filtered versions -> 200 []
```

No new error code is authorized.

Public DTO fields, route inventory, filter names, ordering and pagination shape remain unchanged.

---

# 13. Exactly-one-business-statement evidence — mandatory real PostgreSQL

This is a mandatory S02 candidate gate.

Measure each canonical DataType GET independently against the actual PostgreSQL connection used by production code:

```text
DT-GET-01  GET /datatypes
DT-GET-02  GET /datatypes/{id}
DT-GET-03  GET /datatypes/{id}/versions
DT-GET-04  GET /datatypes/{id}/versions/{version}
```

Required result:

```text
4 / 4 routes
exactly 1 authoritative business SQL statement each
```

The measurement window begins immediately before the target business read path and ends after the complete business projection has been obtained.

Do not count fixture/setup/cleanup SQL outside the target window.

Driver transaction control that is not expressed as an application business SQL statement is not a business statement.

But every application/business SELECT or equivalent SQL statement inside the target read invocation counts. A helper query is not exempt because it is internal.

The evidence collector may use SQLAlchemy event hooks or an equivalent deterministic test-only observer, but it must:

```text
observe the real production connection
not alter the SQL
not alter isolation
not alter locks
not alter code-path selection
not replace PostgreSQL with a fake
```

Do not satisfy the gate merely by AST inspection, response status or counting store method calls.

Static evidence must additionally prove that the four DataType GET application paths do not depend on `coherent_read()`.

## PostgreSQL requirement

S02 has mandatory T2 evidence. Therefore:

```text
TEST_DATABASE_URL missing
    -> S02 candidate gate BLOCKED
    -> do not mark CANDIDATE READY FOR REVIEW
```

Do not use SQLite, Docker/Testcontainers invented by the implementation, fake engines or fabricated credentials as a substitute for required project PostgreSQL evidence.

Report the exact PostgreSQL server version used.

S02 does **not** need to claim the global M3-VER-19 deterministic multi-fragment T3 scenario complete. That cross-family representative snapshot evidence belongs to the later global closure. S02's mandatory contribution is the four-route real-PostgreSQL statement-count proof plus its static no-`coherent_read()` proof and functional behavior.

---

# 14. Implementation discipline

Prefer the smallest coherent persistence/application delta that realizes the frozen RP shapes.

A suitable implementation may introduce DataType-specific read-projector methods/results under the existing persistence module where one statement must return both target presence and page rows.

Good properties:

```text
one common row-to-typed-carrier mapper where semantically neutral
explicit parent-presence result for RP-03
caller-owned connection
no hidden UoW
no mutation helper reuse that recertifies state
minimal API adapter churn
unchanged cursor codec
unchanged write methods
```

Avoid:

```text
one generic mega-projector across unrelated resource families
raw SQL string construction when SQLAlchemy Core expresses the shape
operation-specific application hacks that hide extra SELECTs
adding caching to mask statement counts
loading all rows then paginating in Python
changing persistence mutation loaders to weaken write validation
catch-all exception suppression
silently filtering malformed persisted rows
```

If an implementation helper becomes useful for later resource slices, keep its current abstraction grounded in the DataType need. Do not pre-implement S03+ behavior.

---

# 15. Permanent S02 evidence

A dedicated module such as:

```text
tests/test_m3_s02_datatype_reads.py
```

is acceptable and recommended, but exact test-file layout is implementation-local.

Permanent evidence should make the following DataType facts machine-checkable.

## DataType target contribution to M3-VER-04

```text
4 / 4 canonical DataType GET route behavior preserved
public DTO meanings unchanged
filters/order/pagination unchanged
no DataType GET route added/removed
```

## DataType target contribution to M3-VER-05

```text
unknown/repeated/malformed request carriers preserved
parent missing vs existing parent + empty filtered version page preserved
exact resource 404 preserved
```

## DataType target contribution to M3-VER-06

```text
no default publication recertification on GET
representable semantic surprise remains readable
paired mutation validation remains active
no read-only dependency load solely for certification
```

## DataType target contribution to M3-VER-07, if applicable

```text
materially undecodable persisted DataType carrier
    -> bounded 500 internal_error
    -> no repair / fabrication / omission
```

## DataType target contribution to M3-VER-09

```text
2 DataType cursor identities remain exact
filter/path changes incompatible
changed limit alone compatible
```

## DataType target contribution to M3-VER-12

```text
true multipage traversal for datatypes and datatype_versions
no omission
no duplication
correct canonical keysets
```

## DataType target contribution to M3-VER-19

```text
4 / 4 measured DataType GETs
exactly one business SQL statement each on real PostgreSQL
no coherent_read dependency
```

Do not label any of these global bundles fully PASS unless the frozen later owner has actually completed every required family. S02 status/evidence wording must say **DataType targets PASS** or equivalent.

---

# 16. Regression obligations

Re-run all directly affected DataType delivered evidence, including current equivalents of:

```text
tests/test_datatype_api.py
tests/test_datatype_concurrency.py
tests/test_datatype_semantic_concurrency.py
tests/test_m2_s03_semantic_concurrency.py
```

Preserve mutation semantic coverage. A read simplification is invalid if mutation tests become weaker or are edited to accept previously invalid writes.

Re-run completed M3 evidence affected by shared infrastructure, at minimum:

```text
tests/test_m3_s00_cli_location.py
tests/test_m3_s01_parent_tristate.py
```

Discover and execute other application/persistence/cursor/HTTP tests actually affected by the diff.

Non-drift requirements are exact:

```text
project version                 0.2.0 unchanged
runtime dependencies           unchanged
uv.lock                        unchanged
schema                         unchanged
migrations                     unchanged
public DataType routes         unchanged
public DataType DTOs           unchanged
cursor codec version           v1 unchanged
M3-S00 behavior/evidence       preserved
M3-S01 behavior/evidence       preserved
```

---

# 17. Candidate verification gate

Use the repository's locked toolchain and real configured PostgreSQL.

Run focused evidence first, then regressions, static gates and complete suite.

At minimum execute and report exact results for:

```text
uv lock --check
uv sync --locked

uv run pytest -q <M3-S02 focused DataType targets>
uv run pytest -q <directly affected DataType API/application/persistence/mutation regressions>
uv run pytest -q tests/test_m3_s00_cli_location.py tests/test_m3_s01_parent_tristate.py

uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
uv run pytest -q -m "not postgresql"
uv run pytest -q
uv build
```

The exact focused selector is implementation-local; report it verbatim.

Mandatory S02 conditions:

```text
DataType S02 normative skips       0
DataType S02 xfails                0
DataType S02 automatic reruns      0
new unexplained warnings           0
4/4 DataType statement counts      exactly one business SQL statement
required PostgreSQL evidence       PASS
Ruff format                        PASS
Ruff lint                          PASS
Pyright strict                     PASS
all affected DataType regressions  PASS
full repository suite              PASS
build                              PASS
```

A previously reviewed third-party warning may remain censused exactly as delivered; do not hide or suppress a new warning merely to finish the gate.

Do not weaken, skip, xfail, deselect or retry a normative target to obtain a green result.

If full suite or any mandatory gate fails, classify and report the failure accurately. Do not mark the slice candidate-ready until mandatory failures are resolved or an applicable human/governance decision explicitly changes the condition.

---

# 18. Non-drift inspection before publication

Before candidate publication inspect the diff against:

```text
human authorization commit  5fc50f12c77f7bdb8604d0f322ec657a3d6f6f07
prompt-publication head      current origin/M3 before coding
```

Prove that the implementation does not change:

```text
pyproject.toml version/dependency meaning
uv.lock
src/netauto/migrations/
schema metadata
public route inventory
public DataType DTO shapes
cursor codec structure/version
completed M3-S00/S01 semantics
```

If schema, migration, dependency, lockfile, public-route or DTO change appears necessary, STOP. That is outside M3-S02 and requires the applicable frozen-authority process.

---

# 19. Status, evidence, commit and push

When coding begins:

```text
M3-S02 READY -> M3-S02 IN PROGRESS
```

During implementation:

```text
contract/architecture/steps remain frozen
WIP prompt remains non-normative
implementation defect -> fix code + permanent regression evidence
architecture contradiction -> STOP and report
```

Only when every mandatory S02 target and candidate gate passes may the implementer publish operational status as:

```text
M3-S02 — CANDIDATE READY FOR REVIEW
```

Use truthful evidence wording such as:

```text
DataType targets for M3-VER-04/05/06/09/12/19 — PASS
DataType M3-VER-07 target — PASS / NOT APPLICABLE with frozen-justified reason
Global M3-VER bundles — NOT YET CLOSED
candidate gates — PASS
```

Do **not** publish:

```text
M3-S02 COMPLETED
M3-S03 READY
M3-S03 AUTHORIZED
M3 DELIVERED
M3 ACCEPTED
M3-VER-04..19 globally PASS solely from S02
```

Reviewer/human ownership remains separate.

Commit the complete candidate and push it directly to branch `M3`. Do not create a PR.

Before handoff verify rather than assume:

```text
working tree clean
checked-out branch M3
local HEAD commit
origin/M3 commit
remote M3 commit
local HEAD == origin/M3 == remote M3
```

If the candidate gate is blocked or failing, keep the slice `IN PROGRESS` with accurate blocker status and do not publish a misleading candidate-ready commit.

Keep this execution aid under `wip/` while the slice remains active. It is removed only after reviewer acceptance/governance closure; Git history retains it.

---

# 20. Required final handoff

Return one concise but complete handoff containing:

```text
cycle / slice
branch
authorization baseline
prompt-publication baseline
candidate commit SHA
push/synchronization state
working-tree state
PR state
slice operational state
M3-S03 authorization state
```

List changed files and explain each production delta.

State explicitly whether there were changes to:

```text
schema
migrations
dependencies
uv.lock
project version
public routes
public DTOs
cursor codec
```

Report the DataType route matrix result:

```text
DT-GET-01 -> RP-01
DT-GET-02 -> RP-02
DT-GET-03 -> RP-03
DT-GET-04 -> RP-02
```

Report one-statement evidence exactly:

```text
4/4 canonical DataType GETs
statement count per route
PostgreSQL server version
measurement mechanism/target file
```

Report trusted-read evidence:

```text
removed read-side certification dependencies
representable semantic-surprise fixture and result
paired mutation rejection and result
materially-undecodable DataType carrier target result or justified N/A
```

Report cursor evidence:

```text
datatypes multipage / changed-limit / filter mismatch
datatype_versions multipage / changed-limit / status/parent mismatch
```

Report exact verification commands/results, including:

```text
focused S02 tests
DataType regressions
M3-S00/S01 regressions
Ruff format/lint
Pyright
collection count
non-PostgreSQL suite
full repository suite
build
skip/xfail/rerun counts
warnings
Python version
PostgreSQL version
uv / pytest / Ruff / Pyright versions when available
```

List anything not executed and why.

List residual risks/findings. If none, say none.

Use final wording equivalent to:

```text
M3-S02 candidate implemented and ready for reviewer inspection.
```

Do not say `COMPLETED`. Do not start M3-S03.
