# Codex implementation prompt — M3-S03

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS under `docs/architecture/`, the FINAL/FROZEN M3 contract and architecture set, the FINAL/FROZEN `steps.md`, the ratified technology baseline, and the operational authorization in `status.md`.

If this prompt conflicts with any owning authority, stop the affected work and report the conflict. Do not reinterpret a frozen decision to fit current code or this execution aid.

---

# Assignment

Implement exactly:

```text
M3-S03 — ObjectTemplate trusted recursive and aggregate read projections
```

Work directly on branch:

```text
M3
```

The human-authorized implementation baseline is:

```text
0d6b6e628e14754337fca5c41b431cb26ff7f8aa
Authorize M3-S03 implementation
```

The prompt-publication commit is a later documentation-only descendant of that authorization commit. Work from the current `origin/M3`; do not reset the branch to the authorization commit. Confirm that the authorization commit remains in ancestry.

Current authorization is exactly:

```text
M3-S00    reviewer-owned COMPLETED
M3-S01    reviewer-owned COMPLETED
M3-S02    reviewer-owned COMPLETED
M3-S03    READY — AUTHORIZED
M3-S04    NOT AUTHORIZED / dependency blocked
M3-S05    NOT AUTHORIZED / dependency blocked
M3-S06    NOT AUTHORIZED / dependency blocked
M3-S07    NOT AUTHORIZED / dependency blocked
```

Deliver the complete bounded S03 ObjectTemplate read capability and permanent ObjectTemplate evidence targets contributing to:

```text
M3-VER-04
M3-VER-05
M3-VER-06
M3-VER-07 where an ObjectTemplate materially-undecodable carrier case is actually applicable
M3-VER-09
M3-VER-12
M3-VER-19
```

Re-execute as affected regression evidence:

```text
M3-VER-14
M3-VER-15
M3-VER-16
```

Important evidence ownership rule:

```text
M3-S03 owns no exclusive primary stable M3-VER bundle.
```

Therefore this slice must make its ObjectTemplate targets concrete and PASS, but it must **not** claim that the complete global `M3-VER-04/05/06/07/09/12/19` bundles are PASS. Their cross-family/global closure remains later, principally `M3-S06` as frozen by `steps.md`.

Do not start `M3-S04`. Do not create a pull request. Do not merge, rebase, force-push, rewrite published history, tag or release.

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

docs/milestones/M3/wip/M3-S03-codex-prompt.md
```

Historical M3 WIP discovery notes may be inspected only as non-normative implementation cross-checks. Relevant examples include:

```text
docs/milestones/M3/wip/get-read-census.md
docs/milestones/M3/wip/get-read-review-closure.md
docs/milestones/M3/wip/ot-get-04-decision.md
docs/milestones/M3/wip/ot-get-05-decision.md
docs/milestones/M3/wip/ot-get-06-decision.md
```

They never override the frozen contract, architecture or steps.

Confirm from the repository before changing behavior:

```text
checked-out branch                    M3
origin/M3 ancestry                    includes 0d6b6e628e14754337fca5c41b431cb26ff7f8aa
README active cycle                   M3
contract                              FINAL / FROZEN
architecture set                      FINAL / FROZEN
read-projections.md                   FINAL / FROZEN — ADP-01/02/03 CLOSED
api.md                                FINAL / FROZEN — ADP-04/05 CLOSED
verification.md                       FINAL / FROZEN — ADP-08 CLOSED
steps.md                              FINAL / FROZEN
M3-S00                                COMPLETED
M3-S01                                COMPLETED
M3-S02                                COMPLETED
M3-S03                                READY or IN PROGRESS
M3-S04                                NOT AUTHORIZED
relevant contract/architecture reopen none
project version                       0.2.0
```

Inspect the current realization before choosing local decomposition. At minimum inspect:

```text
src/netauto/domain/objecttemplates.py
src/netauto/application/objecttemplates.py
src/netauto/persistence/objecttemplates.py
src/netauto/entrypoints/api/objecttemplates.py

# OT-GET-06 is currently owned here:
src/netauto/application/relationshipdefinitions.py
src/netauto/persistence/relationships.py

src/netauto/application/cursors.py
src/netauto/persistence/uow.py
src/netauto/transport/http/objecttemplates.py

existing ObjectTemplate API/application/persistence tests
existing RelationshipCapability tests
existing ObjectTemplate mutation/concurrency tests
tests/test_m3_s01_parent_tristate.py
tests/test_m3_s02_datatype_reads.py
and every directly affected accepted regression discovered in the repository
```

The current code is evidence, not authority. Important AS-IS observations to verify rather than blindly assume include:

```text
OT-GET-01 list_lineages
    -> already has correct S01 parent tri-state and cursor identity
    -> currently uses coherent_read()
    -> currently recertifies default_version -> PUBLISHED

OT-GET-02 get_lineage
    -> currently uses coherent_read()
    -> currently recertifies default_version -> PUBLISHED

OT-GET-03 list_versions
    -> currently performs a separate stable-parent lookup before child page
    -> therefore currently requires more than one business statement

OT-GET-04 get_version
    -> current persistence get_version() performs header + properties + components reads
    -> currently needs coherent_read() for a coherent composite

OT-GET-05 get_effective_schema
    -> currently loads exact versions/declarations iteratively
    -> currently calls validation-aware exact-chain/domain resolution
    -> currently reads stable lineages while traversing exact pins

OT-GET-06 list_relationship_capabilities
    -> currently lives in RelationshipDefinitionService
    -> currently traverses stable ancestry in application with repeated reads
    -> currently recertifies ancestry/default-target semantics
    -> current capability SQL EXISTS(PUBLISHED RDV) is membership logic and must remain
```

Once pre-flight passes and implementation work actually begins, update `docs/milestones/M3/status.md`:

```text
M3-S03 READY -> M3-S03 IN PROGRESS
```

Do not mark the slice `COMPLETED`.

If repository authority or current ownership exposes a genuine contradiction not resolvable inside frozen S03, stop the affected work and report it. Do not silently redesign the architecture.

---

# 2. Hard scope boundary

## 2.1 In scope

Exactly six canonical ObjectTemplate public GET/read routes:

```text
OT-GET-01  GET /api/v1/core/object-templates
OT-GET-02  GET /api/v1/core/object-templates/{template_id}
OT-GET-03  GET /api/v1/core/object-templates/{template_id}/versions
OT-GET-04  GET /api/v1/core/object-templates/{template_id}/versions/{version}
OT-GET-05  GET /api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema
OT-GET-06  GET /api/v1/core/object-templates/{template_id}/relationship-capabilities
```

Expected production scope is principally:

```text
src/netauto/application/objecttemplates.py
src/netauto/persistence/objecttemplates.py
src/netauto/entrypoints/api/objecttemplates.py only if read wiring must change without public-contract change
```

Because the delivered implementation currently owns `OT-GET-06` in RelationshipDefinition service/persistence, bounded S03 changes are also allowed **only for this ObjectTemplate public route** in:

```text
src/netauto/application/relationshipdefinitions.py
src/netauto/persistence/relationships.py
```

Do not migrate or simplify unrelated RelationshipDefinition GETs; those remain owned by `M3-S05`.

Tests/evidence may add dedicated M3-S03 modules and minimally update legacy assertions whose old read-side certification expectation is explicitly replaced by frozen S03.

## 2.2 Explicitly out of scope

Do not implement any `M3-S04+` behavior, including:

```text
Object trusted read rewrites
components parent_object_id cursor repair
Object Relationship object_id cursor repair
RelationshipDefinition trusted-read family migration except the existing OT-GET-06 owner path
Relationship exact trusted read
lifecycle trusted decoder/read migration
integrated 22-route closure
final M3 acceptance/delivery
```

Do not introduce:

```text
new public route
new public DTO field
new query parameter
new cursor format/version
schema/table/index/constraint change
Alembic revision
runtime dependency
uv.lock semantic drift
project-version change
new business resource
new HTTP error code
new CLI grammar
transport/enrichment/render redesign
hidden post-read HTTP call
new database isolation promise
```

Preserve completed S00, S01 and S02 behavior.

---

# 3. Frozen trusted-read responsibility

All six S03 GETs must follow ADP-01:

```text
HTTP adapter
    -> lexical request parsing / strict query validation

application read service
    -> request semantics
    -> cursor route/filter/key validation
    -> ordinary read UoW
    -> 404 / Page / response classification

persistence read projector
    -> complete persisted projection in one authoritative SQL statement
    -> target-existence evidence where required
    -> canonical ordering/keyset
    -> representational decoding only

public DTO serialization
```

Every canonical S03 GET must satisfy:

```text
one complete public projection
    -> exactly one authoritative business SQL statement
    -> one PostgreSQL statement snapshot
    -> ordinary read UoW
    -> no coherent_read() dependency
```

`coherent_read()` remains valid infrastructure elsewhere. S03 must not globally remove/deprecate it.

Public GETs must not answer:

```text
"Would this persisted state pass current ObjectTemplate mutation validation?"
```

Therefore GET-only paths must not recertify persisted semantic invariants such as:

```text
default_version points to PUBLISHED
stable/exact inheritance agreement
inheritance acyclicity as mutation admission
local declaration validity
inherited member collision freedom
parent/default admissibility
component target semantic admissibility
```

Mutation paths retain those validators unchanged.

Representational decoding remains required. Do not fabricate defaults, silently omit required projection members or repair stored values.

---

# 4. Route matrix — exact frozen shapes

## OT-GET-01 — RP-01 DIRECT PAGE

Route:

```text
GET /api/v1/core/object-templates
```

Preserve the S01 public tri-state exactly:

```text
parent filter omitted
    parent_template_id=None
    parent_filter_set=False

parent_template_id=null
    parent_template_id=None
    parent_filter_set=True

parent_template_id=<UUID>
    parent_template_id=UUID
    parent_filter_set=True
```

Preserve filters and ordering:

```text
namespace
name
abstract
parent_template_id + parent_filter_set
keyset = (namespace, name)
ORDER BY namespace, name ASC
limit excluded from cursor semantic identity
```

Target:

```text
one direct SELECT over object_templates
no default-target lookup
no publication recertification
ordinary UoW
```

A persisted non-null `default_version` is projected as a fact; GET must not require it to resolve to a PUBLISHED target.

Re-run all S01 tri-state/cursor evidence after this change.

## OT-GET-02 — RP-02 DIRECT EXACT

Route:

```text
GET /api/v1/core/object-templates/{template_id}
```

Target:

```text
one exact object_templates read
0 rows -> existing 404 resource_not_found
1 row  -> ObjectTemplate projection
no default-target lookup/certification
ordinary UoW
```

No stable dependency load may be added solely to recertify persisted state.

## OT-GET-03 — RP-03 PARENT-ROOTED PAGE

Route:

```text
GET /api/v1/core/object-templates/{template_id}/versions
```

Preserve:

```text
status filter
cursor route = object_template_versions
cursor filters = template_id + status
keyset = (version)
ORDER BY version ASC
limit + 1 pagination
changed limit only remains compatible
```

Required public distinction:

```text
stable ObjectTemplate parent absent
    -> 404 resource_not_found

stable parent exists + zero versions matching status/keyset
    -> 200 {items: [], next_cursor: null}
```

The **single** SQL statement must carry parent-presence evidence while child membership filters/keyset stay in the child membership branch/ON condition so they cannot erase the parent-only result.

Do not issue one parent lookup plus one page lookup.

## OT-GET-04 — RP-04 EXACT AGGREGATE / INDEPENDENT CHILD SETS

Route:

```text
GET /api/v1/core/object-templates/{template_id}/versions/{version}
```

Projection owns:

```text
exact ObjectTemplateVersion header
complete local properties ordered by position
complete local components ordered by position
```

Required states:

```text
exact version absent
    -> 404 resource_not_found

exact version present + zero properties/components
    -> successful exact DTO with empty sets

exact version present + properties/components
    -> complete independent child sets
```

One statement only.

Do **not** implement direct header × properties × components row multiplication. Independent child sets must not cartesian-multiply, duplicate, truncate or alter ordering.

A typed `UNION ALL`, independent SQL aggregation or an equivalent one-statement form is allowed. Exact SQLAlchemy decomposition is local implementation detail.

Permanent evidence must include an aggregate with multiple properties and multiple components and prove output cardinalities/order remain exact rather than multiplicative.

## OT-GET-05 — RP-05 RECURSIVE EXACT-CHAIN PROJECTION

Route:

```text
GET /api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema
```

This route follows **persisted exact version pins**, not stable-lineage ancestry:

```text
requested (template_id, version)
    -> (parent_template_id, parent_version)
    -> parent exact pair
    -> ...
```

The stable `object_templates.parent_template_id` chain is not the source of truth for this exact-version projection.

Target persistence shape:

```text
one recursive SQL statement
root requested exact leaf
follow exact parent pair recursively
gather exact-chain local properties/components
preserve declaring_template_id
produce deterministic root-to-leaf projection
avoid property/component cartesian multiplication
preserve exact-leaf existence marker
```

Required public states:

```text
requested exact version absent
    -> 404

requested exact version exists + no effective members
    -> success with empty properties/components

requested exact version exists + inherited/local members
    -> complete EffectiveSchema
```

The GET path must not call validation-aware helpers merely because mutation workflows use them. In particular, do not depend on GET-time calls to:

```text
validate_local_declarations(...)
resolve_effective_schema(...) when it performs semantic certification
stable-lineage/exact-parent agreement checks
inherited-member collision validation
mutation-style inheritance admission validation
```

Do not weaken/delete those helpers if mutation paths still need them. Introduce/read through a trusted projector instead.

Permanent positive evidence must prove **exact-pin semantics** independently from stable ancestry. Prefer a representable persisted fixture where the exact version pin differs from the stable-lineage parent while all FK-required exact targets exist; the effective-schema GET must follow the exact persisted pair rather than recertifying stable agreement.

Also include at least one representable persisted declaration/inheritance surprise that the old validating resolver would reject but whose carriers are sufficient to build the public lists; the trusted GET must project persisted facts without mutation recertification. Do not fabricate a fixture that violates database structural constraints required for committed state.

Do not use a deliberately cyclic fixture as the only semantic-surprise proof; recursion safety/termination must not be conflated with mutation-cycle certification.

## OT-GET-06 — RP-06 RECURSIVE STABLE-ANCESTRY PAGE

Route:

```text
GET /api/v1/core/object-templates/{template_id}/relationship-capabilities
```

This route intentionally uses **stable lineage ancestry**, unlike OT-GET-05.

Canonical cursor identity remains:

```text
route = relationship_capabilities
filters = {
    template_id: str(template_id),
    name: name,
}
key = [resolution_id]
ORDER BY resolution_id ASC
```

Target single statement:

```text
recursive CTE rooted at requested stable ObjectTemplate lineage
    -> stable parent ids

capability member page
    -> RelationshipResolution.from_template_id IN stable ancestry
    -> optional name filter
    -> resolution_id keyset
    -> ORDER BY resolution_id
    -> LIMIT limit + 1
    -> preserve existing EXISTS(at least one PUBLISHED RelationshipDefinitionVersion)
```

The existing PUBLISHED-RDV `EXISTS` is collection-membership logic, **not** default-target certification; preserve it.

Remove GET-side recertification of:

```text
stable ancestry cycle validity
stable parent semantic validity
RelationshipDefinition default_version -> PUBLISHED
```

Path target distinction must remain:

```text
requested ObjectTemplate absent
    -> 404

requested ObjectTemplate exists + no matching capabilities
    -> 200 empty page
```

The statement therefore needs target-presence evidence independent from capability rows. Any marker/branch must be removed before application pagination so it never consumes public `limit` or appears in DTOs.

Permanent evidence must prove stable-ancestry semantics: a child template must receive capabilities declared for itself and its stable ancestors according to the frozen membership rule.

Permanent trusted-read evidence should also prove that a representable RelationshipDefinition `default_version` surprise no longer causes this ObjectTemplate capability GET to fail, while the existing `EXISTS(PUBLISHED RDV)` membership predicate still controls eligibility.

Do not migrate RelationshipDefinition GET/read semantics generally in this slice.

---

# 5. Exact-chain vs stable-ancestry separation

This distinction is correctness-critical and must have explicit evidence:

```text
OT-GET-05 effective schema
    -> exact (template_id, version) parent pins

OT-GET-06 relationship capabilities
    -> stable object_templates.parent_template_id ancestry
```

Do not share a helper that silently substitutes one ancestry model for the other.

At minimum, permanent evidence must make it impossible for a future refactor to replace one with the other unnoticed.

---

# 6. Cursor and request behavior

Preserve all existing strict public request behavior:

```text
unknown query -> 400 invalid_request
repeated query -> 400 invalid_request
malformed UUID/path integer/status/bool -> 400 invalid_request
```

Preserve all three ObjectTemplate cursor routes exactly:

```text
object_templates
object_template_versions
relationship_capabilities
```

For each affected cursor route, evidence must include where applicable:

```text
same semantic identity -> continuation accepted
same identity + changed limit -> accepted
changed membership filter -> invalid_cursor
changed path target -> invalid_cursor
malformed/wrong-length/wrong-type key -> invalid_cursor
```

For `object_templates`, re-run the S01 omitted/root/exact-parent incompatibility matrix.

Do not change cursor codec v1.

---

# 7. Read semantic authority / write semantic authority pairing

S03 must prove both sides of the boundary.

Read-side representative persisted surprises should demonstrate that GET no longer performs mutation-owned certification, including material ObjectTemplate cases such as:

```text
lineage default_version points to a non-PUBLISHED but structurally existing version
exact-version parent pin differs from stable lineage parent while exact FK target exists
representable inherited declaration collision or equivalent old-resolver semantic rejection
RelationshipCapability row carries a default_version that would fail old default-target recertification while membership EXISTS(PUBLISHED RDV) remains true
```

Use only fixtures that can exist as committed state under the delivered schema, unless a specific M3-VER-07 materially-undecodable test intentionally exercises a corruption boundary with a documented safe fixture mechanism.

Write-side evidence must prove existing mutation validation remains active, including relevant representatives for:

```text
default target admissibility
inheritance cycle/agreement/admissibility
local declaration/collision validation
component target semantics
```

Do not remove or weaken a mutation validator to make GET tests pass.

---

# 8. M3-VER-07 applicability

Do not invent a materially-undecodable ObjectTemplate carrier merely to claim coverage.

Assess the delivered schema and public typed carriers.

If an ObjectTemplate persisted carrier can be committed in a form that is structurally present but cannot be converted into a mandatory public typed field, add a deterministic PostgreSQL + HTTP target proving:

```text
bounded 500 internal_error
no repair
no fabricated default
no silent item omission
```

If the delivered schema/check/FK/type constraints make every mandatory ObjectTemplate carrier materializable and no legitimate S03 case exists, record the ObjectTemplate `M3-VER-07` target as **NOT APPLICABLE** with permanent static/schema evidence, analogous in rigor to the accepted DataType S02 disposition.

Do not claim global M3-VER-07 PASS from S03.

---

# 9. One-business-statement evidence — mandatory

This slice requires real PostgreSQL.

Measure each of the exact six canonical ObjectTemplate GETs independently on the production runtime connection/engine:

```text
OT-GET-01
OT-GET-02
OT-GET-03
OT-GET-04
OT-GET-05
OT-GET-06
```

For each invocation:

```text
business SQL statement count == 1
```

Use a deterministic SQLAlchemy statement observation boundary such as `before_cursor_execute` on the actual runtime `AsyncEngine.sync_engine`, following the accepted S02 evidence model.

The measurement window must start immediately before the target GET and be cleared per route. Fixture/setup/cleanup/warmup SQL must remain outside the measured target invocation.

The one target statement must be the authoritative projection. A helper SELECT is not exempt because it is internal.

Also add static evidence that none of the six GET application paths invokes `coherent_read()` or mutation-only certification helpers.

Missing `TEST_DATABASE_URL` makes required S03 PostgreSQL evidence **BLOCKED**, never PASS. Do not substitute SQLite, Docker/Testcontainers, invented credentials or fake statement counting for the normative PostgreSQL claim.

---

# 10. Permanent S03 evidence

A dedicated module such as:

```text
tests/test_m3_s03_objecttemplate_reads.py
```

is acceptable but not mandatory. Test organization may follow repository conventions.

The permanent S03 evidence set must cover at least:

```text
1. OT-GET-01 trusted direct page + S01 parent tri-state regressions
2. OT-GET-02 trusted exact lineage + 404
3. OT-GET-03 parent 404 vs filtered-empty + status/keyset/cursor
4. OT-GET-04 exact aggregate with independent nontrivial properties/components
5. OT-GET-05 exact-pin recursive effective schema + 404/empty/nonempty
6. OT-GET-05 no validating-domain resolver dependency
7. OT-GET-06 stable-ancestry capability membership + target 404/empty
8. OT-GET-06 PUBLISHED-RDV EXISTS preserved while default-pointer recertification removed
9. exact-chain vs stable-ancestry distinction
10. cursor continuation/filter/path/key behavior for all affected ObjectTemplate cursor routes
11. representative read-surprise succeeds + paired mutation rejection remains active
12. M3-VER-07 applicable negative target or rigorous NOT APPLICABLE evidence
13. six-route PostgreSQL statement-count census = 1/1/1/1/1/1
14. static no-coherent_read/no mutation-certification dependencies on S03 GET paths
```

Do not claim global bundle completion.

If a machine-checkable incremental M3 traceability registry already exists, extend it truthfully with only concrete S03 targets now implemented. Do not fabricate later-family targets or PASS states.

---

# 11. Regression obligations

At minimum discover and re-run the current equivalents of:

```text
tests/test_objecttemplate_api.py
ObjectTemplate application/persistence tests
ObjectTemplate semantic/concurrency mutation tests
RelationshipCapability / RelationshipDefinition tests affected only by OT-GET-06 ownership
tests/test_m3_s01_parent_tristate.py
tests/test_m3_s02_datatype_reads.py
cross-family default-pointer corruption regression
```

Also re-run completed S00/S01 evidence families if the actual diff touches shared API/CLI/cursor surfaces.

Exact non-drift requirements:

```text
public ObjectTemplate route inventory      unchanged
public DTO fields/shapes                   unchanged
S01 parent tri-state                       unchanged
cursor codec version                       v1 unchanged
ObjectTemplate mutation semantics          unchanged
RelationshipDefinition GET family          unchanged except OT-GET-06 current-owner implementation path
schema/migrations                          unchanged
runtime dependencies                       unchanged
uv.lock                                    unchanged
project version                            0.2.0 unchanged
```

The accepted S02 DataType read boundary must remain green.

---

# 12. Candidate verification gate

Use the locked repository toolchain.

At minimum execute and report exact results for:

```text
uv lock --check
uv sync --locked

# focused S03 PostgreSQL + static evidence
uv run pytest -q <M3-S03 focused targets>

# directly affected ObjectTemplate/RelationshipCapability regressions
uv run pytest -q <affected regression targets>

# completed S01/S02 evidence regressions
uv run pytest -q tests/test_m3_s01_parent_tristate.py
uv run pytest -q tests/test_m3_s02_datatype_reads.py

uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
uv run pytest -q -m "not postgresql"
uv run pytest -q
uv build
```

If current repository test markers/names require a semantically equivalent command selection, report the exact commands actually used.

Requirements:

```text
S03 mandatory target skip        0
S03 mandatory target xfail       0
S03 mandatory target rerun       0
new unexplained project warning  0
Ruff                             PASS
Pyright strict                   PASS
6/6 ObjectTemplate statements    exactly 1 each on real PostgreSQL
all affected regressions         PASS
full repository suite            PASS
build                            PASS
```

Do not weaken, skip, xfail, deselect or automatic-rerun a failing normative target to finish the slice.

A previously censused third-party warning may be reported truthfully; any new unexplained warning is a finding.

---

# 13. Diff/non-drift inspection

Before publication inspect the complete candidate diff from:

```text
prompt-publication HEAD
    -> candidate HEAD
```

Prove no forbidden delta in at least:

```text
pyproject.toml dependency/version meaning
uv.lock
src/netauto/migrations/
public API route inventory
public DTO contracts
cursor codec/version
unrelated Object / Relationship / lifecycle family implementation
```

If an unexpected schema, migration, dependency, lockfile, public-contract or later-slice change appears necessary, STOP. It is outside M3-S03 and requires the applicable architecture/contract process.

---

# 14. Status, commit and publication discipline

When implementation starts:

```text
M3-S03 READY -> M3-S03 IN PROGRESS
```

During work keep:

```text
contract/architecture/steps frozen
M3-S04..S07 NOT AUTHORIZED
M3-S03 execution aid non-normative
```

When and only when every mandatory S03 target and candidate gate passes, the implementer may update operational status to:

```text
M3-S03 — CANDIDATE READY FOR REVIEW
```

The candidate status must truthfully record:

```text
ObjectTemplate concrete targets for global M3-VER bundles — PASS
M3-VER-07 ObjectTemplate target — PASS or rigorously NOT APPLICABLE
M3-VER-14..16 affected regressions — PASS
global M3-VER bundles — NOT YET CLOSED
6/6 one-business-statement evidence — PASS
candidate gates — PASS
M3-S04 — NOT AUTHORIZED
```

Do **not** set:

```text
M3-S03 COMPLETED
M3-S04 READY
M3 DELIVERED
ACCEPTED
```

Those are reviewer/human-owned transitions.

Commit and push the complete candidate to branch `M3`. Do not create a PR.

Before final handoff verify:

```text
working tree clean
local branch M3
local HEAD commit
origin/M3 commit
remote M3 commit
local HEAD == origin/M3 == remote M3
```

Keep `docs/milestones/M3/wip/M3-S03-codex-prompt.md` in the active WIP tree while S03 is active. Reviewer removes it after acceptance according to governance.

---

# 15. Final handoff format

Report at least:

```text
cycle/slice
branch
authorization baseline
prompt baseline
candidate commit
push/synchronization state
working-tree state
PR state
status
M3-S04 authorization state

changed files
production scope
read-projector decomposition per OT-GET-01..06

six-route SQL statement census
PostgreSQL version
statement-observation mechanism

trusted-read surprise evidence
paired mutation-preservation evidence
exact-chain vs stable-ancestry evidence
RP-04 independent-child evidence
parent/path 404-vs-empty evidence
cursor evidence
M3-VER-07 disposition
S01/S02 regression results

exact verification commands/results
collection count
non-PostgreSQL count
full-suite count
Ruff/Pyright/build/lock results
skip/xfail/rerun counts
warnings
tool versions

schema/migration/dependency/lockfile/version/route/DTO/cursor-codec non-drift facts
unexecuted verification and reason, if any
residual risks/findings
```

Use the handoff wording:

```text
M3-S03 candidate implemented and ready for reviewer inspection.
```

Do not say `COMPLETED`. Do not begin M3-S04.
