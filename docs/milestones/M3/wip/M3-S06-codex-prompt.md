# Codex implementation prompt — M3-S06

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS under `docs/architecture/`, the FINAL/FROZEN M3 contract and architecture set, the FINAL/FROZEN `steps.md`, the ratified technology baseline, and the operational authorization in `status.md`.

If this prompt conflicts with an owning authority, stop the affected work and report the conflict. Do not reinterpret frozen semantics to fit current code or this execution aid.

---

# Assignment

Implement exactly:

```text
M3-S06 — Integrated read/cursor/coherence/non-drift/traceability closure
```

Work directly on branch:

```text
M3
```

The human-authorized implementation baseline is:

```text
28f2a1ad1f612cb19f8064e34ae9294c5a60499b
Authorize M3-S06 implementation
```

The prompt-publication commit is a later documentation-only descendant of that authorization commit. Work from the current `origin/M3`; do not reset to the authorization commit. Confirm the authorization commit remains in ancestry.

Current authorization is exactly:

```text
M3-S00    reviewer-owned COMPLETED
M3-S01    reviewer-owned COMPLETED
M3-S02    reviewer-owned COMPLETED
M3-S03    reviewer-owned COMPLETED
M3-S04    reviewer-owned COMPLETED
M3-S05    reviewer-owned COMPLETED
M3-S06    READY — AUTHORIZED
M3-S07    NOT AUTHORIZED / dependency blocked
```

S05 acceptance means the production trusted-read implementation now covers all 22 canonical GET routes. S06 is an **integration/evidence closure slice**, not a new resource-family implementation slice.

Primary stable evidence owned by S06:

```text
M3-VER-04 — Twenty-two-route public read compatibility
M3-VER-05 — Request/path-target failure preservation
M3-VER-06 — Read semantic authority and mutation preservation
M3-VER-09 — Complete twelve-route cursor binding
M3-VER-12 — Cursor keyset completeness
M3-VER-17 — No schema/migration/dependency drift
M3-VER-18 — Complete outcome traceability
M3-VER-19 — Single-request committed projection coherence
```

Mandatory affected-bundle re-execution:

```text
M3-VER-01 .. M3-VER-03
M3-VER-07 .. M3-VER-08
M3-VER-10 .. M3-VER-11
M3-VER-13 .. M3-VER-16
```

Do not start `M3-S07`. Do not create a pull request. Do not merge, rebase, force-push, rewrite published history, tag or release.

---

# 1. Mandatory repository pre-flight

Before editing software or evidence, re-read and obey at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

docs/architecture/README.md
docs/architecture/api.md
docs/architecture/cli.md
docs/architecture/persistence.md
docs/architecture/verification.md

docs/milestones/M3/contract.md
docs/milestones/M3/architecture/README.md
docs/milestones/M3/architecture/read-projections.md
docs/milestones/M3/architecture/api.md
docs/milestones/M3/architecture/cli.md
docs/milestones/M3/architecture/verification.md
docs/milestones/M3/steps.md
docs/milestones/M3/status.md

docs/milestones/M3/wip/M3-S06-codex-prompt.md
```

Inspect the accepted M3 evidence modules and their current collected test names, at minimum:

```text
tests/test_m3_s00_cli_location.py
tests/test_m3_s01_parent_tristate.py
tests/test_m3_s02_datatype_reads.py
tests/test_m3_s03_objecttemplate_reads.py
tests/test_m3_s04_object_reads.py
tests/test_m3_s05_relationship_reads.py
```

Inspect existing durable registry/non-drift/concurrency patterns rather than inventing a parallel testing style:

```text
tests/test_m1_traceability.py
tests/test_migrations.py
tests/test_schema_metadata.py
existing semantic-concurrency suites
existing cursor/API suites
existing CLI registry/protocol tests
tests/conftest.py
tests/support/
```

Inspect implementation only as needed to verify or correct frozen obligations. At minimum inspect:

```text
src/netauto/application/cursors.py
src/netauto/application/datatypes.py
src/netauto/application/objecttemplates.py
src/netauto/application/objects.py
src/netauto/application/relationshipdefinitions.py
src/netauto/application/relationships.py

src/netauto/persistence/datatypes.py
src/netauto/persistence/objecttemplates.py
src/netauto/persistence/objects.py
src/netauto/persistence/relationships.py
src/netauto/persistence/lifecycle.py
src/netauto/persistence/uow.py
src/netauto/persistence/metadata.py

src/netauto/entrypoints/api/*.py
src/netauto/cli/registry.py
src/netauto/cli/protocol.py
src/netauto/cli/execution.py

pyproject.toml
uv.lock
src/netauto/migrations/versions/
```

Pre-flight must confirm:

```text
checked-out branch                    M3
origin/M3 ancestry                    includes 28f2a1ad1f612cb19f8064e34ae9294c5a60499b
contract                              FINAL / FROZEN
architecture set                      FINAL / FROZEN
steps.md                              FINAL / FROZEN
M3-S00..S05                           reviewer-owned COMPLETED
M3-S06                                READY or IN PROGRESS
M3-S07                                NOT AUTHORIZED
open incompatible reopen              none
project version                       0.2.0
migration revision                    one root/head = 0001_m2_kernel
runtime dependency set                unchanged
uv.lock                               unchanged from authorized baseline
required PostgreSQL                   available via TEST_DATABASE_URL
```

Authorized non-drift baseline facts at prompt publication are:

```text
pyproject.toml blob SHA               d20bbb94739a74ebfb0bd27291b6e4f130d24c5f
uv.lock blob SHA                      0aa980926fda5f42ee3a7d3cedc64f9fcf8c2d23
migration file                        src/netauto/migrations/versions/0001_m2_durable_kernel.py
migration blob SHA                    27fc85e0b4411332fce87c406b6216b35db6eb20
migration revision                    0001_m2_kernel
```

These SHAs are evidence baselines, not permission to reset files. If the branch has legitimately advanced through the prompt commit, work from the current head.

When S06 work actually begins, `status.md` may move from `READY` to `IN PROGRESS`. Do not mark S06 `COMPLETED`.

---

# 2. Hard scope boundary

## In scope

S06 principally adds or completes permanent integration/evidence assets:

```text
machine-checkable M3 traceability/census registry
cross-route HTTP compatibility/failure evidence
complete 12-route cursor identity/keyset evidence
22-route PostgreSQL statement-count census
real-PostgreSQL deterministic T3 single-statement snapshot evidence
read-vs-mutation semantic-authority integration evidence
schema/Alembic/dependency/lockfile non-drift evidence
candidate evidence record/status update
```

Production modules may change **only** if S06 evidence exposes an implementation defect against already-frozen contract/architecture. Any such correction must preserve the existing public semantics and remain narrowly tied to a failing S06 obligation.

## Explicitly out of scope

Do not:

```text
add or reinterpret public business semantics
add a public route/resource/filter/DTO field
change cursor codec/version
change M3 Location DSL or parent-tri-state semantics
change schema/table/index/constraint
add an Alembic revision
add/change runtime dependencies
change uv.lock semantically
change project version
introduce cross-request snapshot guarantees
redesign mutation locking/retries
perform unrelated refactors
start S07 final acceptance/delivery work
mark M3 DELIVERED/ACCEPTED
```

If integrated evidence reveals a contradiction in frozen authority rather than an implementation defect, stop that path and report the required reopen. Do not resolve an architecture contradiction by changing tests or code opportunistically.

---

# 3. Machine-checkable M3 traceability registry — mandatory

Create one permanent machine-checkable M3 owner, using a dedicated module such as:

```text
tests/test_m3_traceability.py
```

or a small `tests/support/m3_*.py` registry plus a test owner. Reuse the durable style established by `tests/test_m1_traceability.py` where useful.

The registry must contain exact sets/maps for:

```text
M3_OUTCOMES
    exact M3-OUT-01 .. M3-OUT-08

M3_ACCEPTANCE_CRITERIA
    exact M3-AC-01 .. M3-AC-19

M3_EVIDENCE_BUNDLES
    exact M3-VER-01 .. M3-VER-19

M3_OUTCOME_TO_ACCEPTANCE
M3_ACCEPTANCE_TO_EVIDENCE
M3_EVIDENCE_TO_ARCHITECTURE_OWNER
M3_EVIDENCE_TO_TARGETS

M3_GET_ROUTE_CENSUS
    exact 22 canonical business GET/read routes

M3_CURSOR_ROUTE_CENSUS
    exact 12 cursor-bearing routes

M3_CLI_201_CENSUS
    exact 8 registered 201 + Location operations
```

Rules:

```text
exact equality, never >= counts
no missing/stale/renamed stable M3 id
all 8 outcomes have one or more ACs
all 19 ACs map to exactly one M3-VER bundle
M3-AC-N -> M3-VER-N for N=01..19, exactly as frozen
all 19 M3-VER bundles have architecture owner(s)
all 19 M3-VER bundles have non-empty concrete target sets
all concrete pytest targets exist and are collected
22 GET entries exactly equal the frozen route census
12 cursor entries exactly equal the ADP-04 matrix
8 CLI create entries exactly equal the ADP-07 matrix
```

Derive `M3_OUTCOME_TO_ACCEPTANCE` and `M3_EVIDENCE_TO_ARCHITECTURE_OWNER` from the FINAL/FROZEN contract/architecture. Do not guess from slice ownership. The registry is evidence of the frozen traceability chain, not a new semantic authority.

Concrete target references should use stable module/function identities (or an equivalent machine-checkable collected-node representation). It is acceptable for one test to support multiple bundles where the test deliberately proves multiple frozen assertions; every bundle must still be non-empty and truthful.

Also statically prove `M3-CQG-01 .. M3-CQG-08` are present and represented by the frozen contract/architecture/governance state. They are quality-gate checks, not extra M3-VER identities.

Normative M3 files must have no unresolved semantic `TODO`, `TBD`, `candidate` ownership ambiguity, open incompatible reopen, or stale active execution aid contradicting the current governance state. Historical WIP may remain historical and must not be misclassified as normative authority.

---

# 4. Exact 22-route GET census — M3-VER-04 / 05 / 06 / 19

The frozen 22-route census is exactly:

```text
DT-GET-01  GET /api/v1/core/datatypes
DT-GET-02  GET /api/v1/core/datatypes/{datatype_id}
DT-GET-03  GET /api/v1/core/datatypes/{datatype_id}/versions
DT-GET-04  GET /api/v1/core/datatypes/{datatype_id}/versions/{version}

OT-GET-01  GET /api/v1/core/object-templates
OT-GET-02  GET /api/v1/core/object-templates/{template_id}
OT-GET-03  GET /api/v1/core/object-templates/{template_id}/versions
OT-GET-04  GET /api/v1/core/object-templates/{template_id}/versions/{version}
OT-GET-05  GET /api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema
OT-GET-06  GET /api/v1/core/object-templates/{template_id}/relationship-capabilities

OBJ-GET-01 GET /api/v1/core/objects
OBJ-GET-02 GET /api/v1/core/objects/{object_id}
OBJ-GET-03 GET /api/v1/core/objects/{parent_object_id}/components
OBJ-GET-04 GET /api/v1/core/objects/{child_object_id}/owner
OBJ-GET-05 GET /api/v1/core/objects/{object_id}/lifecycle-events
OBJ-GET-06 GET /api/v1/core/objects/{object_id}/relationships

RD-GET-01  GET /api/v1/core/relationship-definitions
RD-GET-02  GET /api/v1/core/relationship-definitions/{relationship_definition_id}
RD-GET-03  GET /api/v1/core/relationship-definitions/{relationship_definition_id}/versions
RD-GET-04  GET /api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}

REL-GET-01 GET /api/v1/core/relationships/{relationship_id}
LC-GET-01  GET /api/v1/core/lifecycle-events
```

Permanent integrated evidence must prove **all 22 success paths** against the public HTTP boundary and exact census equality against the actual registered application routes.

For M3-VER-04, prove across the census:

```text
success DTO field meanings preserved
route-specific filters preserved
canonical ordering preserved
keyset pagination model preserved
limit semantics preserved
no business GET added/removed
only intended M3 public deltas exist
```

Do not satisfy this solely by mapping old test node IDs. Add a finite integrated route matrix that can prove the exact 22 public targets exist and have canonical successful invocations. Existing S02-S05 evidence may be reused as concrete supporting targets.

For M3-VER-05, integrated evidence must cover the frozen failure categories with public HTTP requests:

```text
unknown query -> 400 invalid_request
repeated query -> 400 invalid_request
malformed carrier -> 400 invalid_request
missing path target -> 404 resource_not_found
existing path target + zero matching members -> successful empty page where defined
owner target absent -> 404
owner target present + no owner -> 200 null
nested exact parent absent vs exact child absent where the public distinction exists
```

Use a matrix/category approach rather than one arbitrary route and claim global closure.

For M3-VER-06, prove both sides globally:

```text
READ:
    every one of the 22 GET application targets has no mutation-semantic validator prerequisite
    no read-only dependency load exists solely to re-certify persisted semantics
    representative persisted semantic surprises remain readable across the material removed-certification families

WRITE:
    mutation candidate/transition validation remains active
    affected deterministic mutation/concurrency regressions remain green
```

Representative runtime families must include, at minimum, the already-delivered evidence for:

```text
default publication recertification
Object/property schema recertification
ownership slot/context boundary
Relationship definition/schema/topology recertification
lifecycle transition recertification
```

Do not weaken or delete a mutation validator to make M3-VER-06 pass.

---

# 5. Exact 12-route cursor registry — M3-VER-09 / 12

The frozen ADP-04 matrix is exactly:

| # | Public route | Codec route | Semantic filters | Position key |
|---:|---|---|---|---|
| 1 | `/datatypes` | `datatypes` | `namespace`, `name` | `(namespace, name)` |
| 2 | `/datatypes/{datatype_id}/versions` | `datatype_versions` | `datatype_id`, `status` | `(version)` |
| 3 | `/object-templates` | `object_templates` | `namespace`, `name`, `abstract`, `parent_template_id`, `parent_filter_set` | `(namespace, name)` |
| 4 | `/object-templates/{template_id}/versions` | `object_template_versions` | `template_id`, `status` | `(version)` |
| 5 | `/object-templates/{template_id}/relationship-capabilities` | `relationship_capabilities` | `template_id`, `name` | `(resolution_id)` |
| 6 | `/objects` | `objects` | `template_id`, `template_version`, `canonical_name` | `(id)` |
| 7 | `/objects/{parent_object_id}/components` | `object_components` | `parent_object_id`, `slot_name` | `(child_object_id)` |
| 8 | `/objects/{object_id}/relationships` | `object_relationships` | `object_id`, `relationship_definition_id`, `name` | `(relationship_id, destination_object_id, name)` |
| 9 | `/objects/{object_id}/lifecycle-events` | `lifecycle_events` | all lifecycle filters + `involving_object_id=<path object>` | `(occurred_at, id)` DESC |
| 10 | `/relationship-definitions` | `relationship_definitions` | `{}` | `(id)` |
| 11 | `/relationship-definitions/{definition_id}/versions` | `relationship_definition_versions` | `definition_id`, `status` | `(version)` |
| 12 | `/lifecycle-events` | `lifecycle_events` | all global lifecycle filters + `involving_object_id=None` | `(occurred_at, id)` DESC |

The machine registry must encode these exact identities and canonical ordering/key shapes.

Public HTTP evidence must prove for **every applicable route**:

```text
same semantic identity -> continuation accepted
same identity + changed limit only -> accepted
changed membership filter -> invalid_cursor when the route has such a filter
changed required path target -> invalid_cursor when the route has such a target
incompatible route/scope identity -> invalid_cursor
malformed/wrong-length/wrong-type key -> invalid_cursor
```

M3-VER-12 requires true multipage traversal, not only cursor codec unit tests. Exercise real pages and verify no omission/duplication attributable to cursor continuation.

At minimum the compound material cases must be exercised directly:

```text
Object Relationships
    key = (relationship_id, destination_object_id, name)

lifecycle global and Object-scoped
    key = (occurred_at, id) DESC
```

Prefer generated/shared coverage driven by the machine cursor registry, while retaining explicit regressions for:

```text
Object components parent A/B
Object Relationships Object A/B
lifecycle global/Object scope and Object A/B
ObjectTemplate omitted/root/exact-parent identities
```

Do not add `limit` to semantic identity. Do not move path targets into keyset position.

---

# 6. Exact 8-operation CLI 201 census — traceability/re-execution

The frozen ADP-07 matrix is exactly:

```text
datatype create
datatype create-next
object-template create
object-template create-next
object create
relationship-definition create
relationship-definition create-next
relationship create
```

Frozen Location templates remain exactly those registered today, including the three nested response identities:

```text
/api/v1/core/datatypes/{datatype.id}
/api/v1/core/object-templates/{object_template.id}
/api/v1/core/relationship-definitions/{relationship_definition.id}
```

and the five flat-token cases already frozen by ADP-07.

The traceability registry must equal the live CLI registry-derived `201` operation set and validate exactly one Location template per operation. Re-execute M3-VER-01..03, including interactive/non-interactive nested create truthfulness and protocol-failure classes. Do not modify Location templates or add a hidden enrichment GET.

---

# 7. M3-VER-19 — 22/22 one-business-statement census

Build one integrated real-PostgreSQL statement-observation harness that measures all exact 22 canonical GET invocations independently.

Use the actual runtime `AsyncEngine.sync_engine` / production connection path, e.g. SQLAlchemy `before_cursor_execute`, following accepted S02-S05 practice.

For each route invocation:

```text
business SQL statement count == 1
```

Measurement rules:

```text
clear the observer immediately before each target GET
setup/fixture/cleanup/warmup SQL remains outside the measurement window
transaction-control emitted below the application business layer is not counted as a business projection statement
ANY application SELECT/equivalent inside the target invocation counts
helper SELECTs are not exempt
record route id -> observed count explicitly for all 22
```

The test must use canonical successful targets, not 404 short-circuits as a substitute for the read projection.

Also provide static evidence across the exact 22 application GET targets that none depends on `coherent_read()`.

Do not claim 22/22 from the sum of earlier family reports alone: S06 must execute the integrated 22-route census on one S06 candidate.

Missing `TEST_DATABASE_URL` makes M3-VER-19 `BLOCKED`, never PASS.

---

# 8. M3-VER-19 — deterministic T3 single-request snapshot evidence

Add at least one real-PostgreSQL deterministic concurrency scenario for a **representative multi-fragment projection family**.

Good representative choices include an aggregate whose public response combines one root with multiple persisted fragments, for example an ObjectTemplate exact aggregate, RelationshipDefinition aggregate, or factual Relationship projection. Choose the family that yields the clearest deterministic before/after generations without changing production semantics.

The evidence must prove both interleavings:

```text
A — AFTER projection
    reader reaches a test-observed pause immediately BEFORE its one authoritative execute
    independent writer transaction commits a complete generation change
    reader execute proceeds
    response == complete AFTER generation

B — BEFORE projection
    reader authoritative statement executes/completes
    reader is paused by a test-only observation point before application returns the projection
    independent writer transaction commits a complete generation change
    reader resumes
    response == complete BEFORE generation
```

The observed response must never mix incompatible before/after fragments.

Harness rules:

```text
real PostgreSQL only
independent reader/writer sessions
deterministic barriers/events; no sleep-based correctness
no change to production SQL text
no change to production transaction isolation
no production lock added by the harness
no alternate production path selected
no mutation of reader candidate/request by the hook
no commit/rollback performed by the observation hook itself
bounded timeout only as a hang guard
```

SQLAlchemy connection events or an equivalent test-only phase observer are acceptable if they satisfy those rules. A writer may use an independent PostgreSQL transaction or an existing production mutation path; the test must make the before/after committed generations explicit and deterministic.

This T3 scenario supplements the 22/22 statement census; it does not replace it.

Explicitly preserve the non-goal:

```text
M3 does NOT promise repeatable membership or one shared snapshot across separate page requests.
```

---

# 9. M3-VER-17 — schema/migration/dependency/lock non-drift

Permanent evidence must prove:

```text
no new Alembic revision
one migration root/head only
revision == 0001_m2_kernel
down_revision == None
live PostgreSQL schema matches delivered metadata
compare_metadata == []
no M3 table/index/constraint delta
project version remains 0.2.0
runtime dependency list unchanged
uv lock --check PASS
uv.lock unchanged from authorized M3 baseline
```

Reuse the delivered T5 migration/schema authority in `tests/test_migrations.py` / `tests/test_schema_metadata.py`; do not create a weaker parallel schema assertion.

At minimum statically assert the S06 candidate still has:

```text
only the delivered migration revision file 0001_m2_durable_kernel.py (plus package __init__.py)
revision id 0001_m2_kernel
pyproject version 0.2.0
no runtime dependency delta
```

Run the existing real-PostgreSQL migration/drift evidence, including `compare_metadata == []`.

Any unexplained schema/migration/runtime dependency/lockfile change is a blocking contract contradiction, not something S06 should normalize.

---

# 10. M3-VER-18 — complete outcome traceability

The machine registry and static tests must prove:

```text
8 / 8 outcomes
19 / 19 ACs
19 / 19 VER bundles
all OUT -> non-empty AC set
all AC -> exactly one VER
all VER -> non-empty architecture owner set
all VER -> non-empty concrete target set
22 / 22 GET routes
12 / 12 cursor routes
8 / 8 CLI 201 operations
M3-CQG-01 .. M3-CQG-08 represented
no stale normative TODO/TBD/open semantic owner
no incompatible formal reopen
```

Architecture owner mappings must reference the frozen M3 owner set and preserved AS-IS owner where applicable, for example:

```text
docs/milestones/M3/architecture/read-projections.md
docs/milestones/M3/architecture/api.md
docs/milestones/M3/architecture/cli.md
docs/milestones/M3/architecture/verification.md
docs/architecture/verification.md where delivered verification authority remains material
```

Do not use `steps.md` slice ownership as a substitute for architecture ownership.

Concrete target existence must be machine checked. A string naming a test that no longer exists is not traceability closure.

---

# 11. Required prior-bundle re-execution

S06 must re-execute and record the prior primary evidence affected by integration:

```text
M3-VER-01..03     S00 CLI Location/protocol
M3-VER-07..08     trusted/undecodable lifecycle boundary
M3-VER-10..11     Object path-target cursor repairs
M3-VER-13         lifecycle scope cursor distinction
M3-VER-14..16     ObjectTemplate HTTP/CLI parent tri-state and cursor identity
```

This does not change primary ownership.

If all S06 primary bundles and all required prior re-executions pass, the S06 candidate may truthfully report that `M3-VER-01..19` have passing concrete evidence on the S06 candidate. That is **not** final M3 acceptance: S07 must still re-execute and accept all evidence against one final delivery candidate.

---

# 12. Candidate evidence record

S06 is the first integrated evidence-closure slice. Create a durable candidate evidence record under the established milestone evidence location, preferably:

```text
docs/milestones/M3/evidence/M3-S06-candidate.md
```

If the repository already establishes another exact evidence-record convention during pre-flight, follow it instead.

The evidence record is non-semantic and must identify facts for the candidate commit, including:

```text
candidate SHA / authorization baseline / prompt baseline
branch and sync state
PostgreSQL server version
Python / uv / pytest / Ruff / Pyright versions
exact 22-route statement-count disposition
T3 scenario and before/after result
22-route GET census result
12-route cursor census result
8-operation CLI census result
M3-VER-01..19 disposition and concrete target commands
schema compare_metadata result
migration root/head result
runtime dependency/uv.lock non-drift result
normative skip/xfail/rerun census
supported-path 40P01 / unexpected 40001 census where affected concurrency suites report it
warnings
full repository suite/build/static gate results
open risks/findings
```

Do not put new semantic rules in the evidence record.

---

# 13. Candidate verification gate

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

Run focused permanent S06 evidence for:

```text
M3 traceability exact registries
M3-VER-04 / 05 / 06 integrated read evidence
M3-VER-09 / 12 complete cursor evidence
M3-VER-17 non-drift
M3-VER-18 traceability
M3-VER-19 22/22 statement census + T3 snapshot
```

Re-run prior primary evidence:

```text
M3-S00 evidence
M3-S01 evidence
M3-S05 M3-VER-07/08/13 evidence
M3-S04 M3-VER-10/11 evidence
all other prior M3 primary targets required by the frozen re-execution list
```

Run all directly affected mutation semantic-regression suites and deterministic concurrency suites needed to prove M3-VER-06.

Run the existing PostgreSQL migration/schema drift evidence for M3-VER-17.

Run:

```text
uv run pytest -q -m "not postgresql"
```

Then run the complete repository suite with the required PostgreSQL environment.

Normative candidate conditions:

```text
skip / xfail / automatic rerun = 0 / 0 / 0
new unexplained project warning = 0
required PostgreSQL evidence = PASS
M3-VER-04,05,06,09,12,17,18,19 = PASS
required prior primary bundles = PASS on the candidate
22 GET census = exact
12 cursor census = exact
8 CLI 201 census = exact
22/22 statement counts = exactly 1
T3 before/after snapshot evidence = PASS
compare_metadata = []
new Alembic revision = 0
runtime dependency delta = 0
uv.lock M3 drift = 0
Ruff/Pyright/build/full suite = PASS
```

A previously reviewed third-party deprecation warning may be reported separately under delivered verification policy. Do not hide or normalize a new warning.

A missing `TEST_DATABASE_URL` or any unavailable required PostgreSQL evidence makes S06 `BLOCKED`, never candidate-ready.

---

# 14. Candidate status/publication discipline

Only after every mandatory S06 gate passes may the implementer publish:

```text
M3-S06 — CANDIDATE READY FOR REVIEW
```

The candidate status may truthfully state:

```text
M3-VER-04/05/06/09/12/17/18/19 — PASS
required prior primary bundles — PASS on this candidate
all 19 M3-VER bundles have non-empty concrete target sets
all 19 M3-VER bundles have passing S06-candidate evidence if actually re-executed
22 / 22 GET census PASS
12 / 12 cursor census PASS
8 / 8 CLI 201 census PASS
22 / 22 statement count PASS
T3 snapshot evidence PASS
schema/dependency/lock non-drift PASS
candidate gates PASS
```

The implementer must **not** publish:

```text
M3-S06 COMPLETED
M3-S07 READY/AUTHORIZED
M3 FINAL ACCEPTANCE PASS
M3 DELIVERED
```

Reviewer owns S06 completion. S07 authorization is a later explicit human/governance decision.

Commit and push the complete candidate directly to branch `M3` under the current operating model. Do not create a PR.

After push verify:

```text
working tree clean
local HEAD == origin/M3 == remote M3
candidate commit identified
no unexpected changed files
no forbidden schema/migration/dependency/lock/version/route/DTO/cursor-codec drift
M3-S07 remains NOT AUTHORIZED
```

Keep this execution aid in `docs/milestones/M3/wip/` while S06 remains active. Reviewer removes it only after accepted completion.

---

# 15. Required final handoff from Codex

Report at minimum:

```text
cycle / slice
branch
authorization baseline
prompt baseline
candidate commit
push/sync state
working tree
PR state
S06 operational state
S07 authorization state

changed files
production corrections, if any, each tied to a failing frozen S06 obligation

traceability registry:
    outcomes 8/8
    ACs 19/19
    VERs 19/19
    all VER target sets non-empty
    CQGs 8/8 represented

GET census 22/22
cursor census 12/12
CLI 201 census 8/8

M3-VER-04 result
M3-VER-05 result
M3-VER-06 result
M3-VER-09 result
M3-VER-12 result
M3-VER-17 result
M3-VER-18 result
M3-VER-19 result

required prior bundle re-execution results
22-route statement count table
T3 representative family + BEFORE/AFTER interleaving evidence
schema compare_metadata result
migration graph result
dependency/lockfile non-drift result
mutation regression result

exact commands and test counts
PostgreSQL/Python/uv/pytest/Ruff/Pyright versions
skip/xfail/rerun census
40P01/40001 census where applicable
warnings
open findings/blockers/risks
```

If all mandatory gates pass, use wording equivalent to:

```text
M3-S06 candidate implemented and ready for reviewer inspection.
```

Do not state that S06 is reviewer-completed, that S07 is authorized, or that M3 has passed final acceptance.
