# Codex prompt — M3 AS-IS consolidation

**Status:** NON-NORMATIVE POST-ACCEPTANCE EXECUTION AID.

This file is an execution aid for the reviewer-authorized M3 AS-IS consolidation gate. It is subordinate to `AGENTS.md`, `docs/general/linee_guida_progetto.md`, the delivered current AS-IS, the FINAL/FROZEN M3 contract and architecture set, the accepted M3 final gate, and the reviewer-owned consolidation specification in `docs/milestones/M3/as-is-consolidation.md`.

If this prompt conflicts with an owning authority, stop the affected path and report the conflict. Do not reinterpret accepted semantics to make documentation convenient.

---

# Assignment

Execute exactly:

```text
M3 post-acceptance AS-IS consolidation
```

Work directly on branch:

```text
M3
```

The consolidation gate specification was published at:

```text
60ae23a5e9453efe3c70c55222a0d8294f37be9c
docs(m3): define AS-IS consolidation gate
```

The human authorization baseline is:

```text
1f0795d7f35c425726c02eb2ca3efd4ef1251711
Authorize M3 AS-IS consolidation
```

Work from the current `origin/M3`; do not reset to either baseline. Confirm both commits remain in ancestry.

Current governance is exactly:

```text
M3-S00 .. M3-S07          reviewer-owned COMPLETED
M3 final acceptance       ACCEPTED
M3                        NOT DELIVERED
AS-IS consolidation       READY / AUTHORIZED
software implementation   NOT AUTHORIZED
consistency closure       NOT AUTHORIZED
final delivery            NOT AUTHORIZED
merge/tag/release/publish NOT AUTHORIZED
```

This is **not** a new implementation slice. Do not create an `M3-S08` or another software slice identifier.

Do not create a pull request. Do not merge, rebase, force-push, tag, release or publish artifacts.

---

# 1. Mandatory repository pre-flight

Before editing documentation, re-read and obey at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

all files under docs/architecture/

docs/milestones/M3/contract.md
docs/milestones/M3/architecture/README.md
docs/milestones/M3/architecture/read-projections.md
docs/milestones/M3/architecture/api.md
docs/milestones/M3/architecture/cli.md
docs/milestones/M3/architecture/verification.md
docs/milestones/M3/steps.md
docs/milestones/M3/status.md
docs/milestones/M3/acceptance.md
docs/milestones/M3/as-is-consolidation.md

docs/milestones/M3/evidence/M3-S06-candidate.md
docs/milestones/M3/evidence/M3-S07-candidate.md

tests/support/m3_evidence.py
tests/support/m3_s07_acceptance.py
tests/test_m3_traceability.py
tests/test_m3_s07_acceptance.py
```

Read the accepted implementation/registries only as cross-check evidence. They do not override documentary authority.

Pre-flight must confirm:

```text
branch                                M3
origin ancestry                       includes 60ae23a... and 1f0795d...
contract                              FINAL / FROZEN
M3 architecture                       FINAL / FROZEN
steps                                 FINAL / FROZEN
M3-S00..S07                           COMPLETED
final acceptance                      ACCEPTED
M3                                    NOT DELIVERED
AS-IS consolidation                   READY / AUTHORIZED
software implementation               NOT AUTHORIZED
consistency closure                   NOT AUTHORIZED
open incompatible reopen              none
current docs/architecture inventory   exactly 15 files
project version                       0.2.0
schema/migration/dependency baseline  unchanged
```

When work begins, `docs/milestones/M3/status.md` may move the consolidation gate from `READY` to `IN PROGRESS` while preserving:

```text
M3-S07 COMPLETED
software implementation NOT AUTHORIZED
M3 NOT DELIVERED
```

Do not alter the permanent S07 lifecycle/evidence semantics.

---

# 2. Hard repository scope

The consolidation candidate may change only:

```text
docs/architecture/*.md
docs/milestones/M3/status.md
```

The architecture corpus must remain **exactly 15 existing files**. Do not add, delete or rename an AS-IS owner.

Do not modify:

```text
src/netauto/
tests/
pyproject.toml
uv.lock
src/netauto/migrations/
README.md root
AGENTS.md
docs/general/
docs/milestones/M3/contract.md
docs/milestones/M3/architecture/
docs/milestones/M3/steps.md
docs/milestones/M3/acceptance.md
docs/milestones/M3/evidence/
docs/milestones/M3/as-is-consolidation.md
```

A need to modify any forbidden surface is a `STOP` condition and must be reported. Do not silently expand consolidation scope.

No software behavior, schema, dependency, lockfile, project-version or public-contract change is authorized.

---

# 3. Consolidation principle — state-heavy, history-light

The output must describe **what NETAUTO is now**, not how M3 changed M2.

Semantic sections must not say things like:

```text
M3 added ...
M3 changed ...
previously ...
newly ...
S04 fixed ...
M3-VER-19 proves ...
```

Use present-tense current-state language instead.

M1/M2/M3 may appear only in the concise provenance/navigation section of `docs/architecture/README.md` or links to historical records.

Do not copy into current owners:

```text
M3-OUT-*
M3-AC-*
M3-VER-*
M3-CQG-*
M3-Snn
review finding IDs
candidate/commit SHAs
pass counts, durations or candidate artifact hashes
```

The accepted M3 semantics must become native current AS-IS meaning, not a milestone overlay.

---

# 4. Exact target corpus

The corpus remains:

```text
docs/architecture/README.md
docs/architecture/datatype.md
docs/architecture/objecttemplate.md
docs/architecture/object.md
docs/architecture/relationship.md
docs/architecture/persistence.md
docs/architecture/concurrency-matrix.md
docs/architecture/concurrency.md
docs/architecture/api.md
docs/architecture/health.md
docs/architecture/cli.md
docs/architecture/runtime-deployment.md
docs/architecture/linux-operating-baseline.md
docs/architecture/verification.md
docs/architecture/verification-concurrency-registry.md
```

Audit all fifteen files even if some require no modification.

Expected materially impacted owners are principally:

```text
README.md
datatype.md
objecttemplate.md
object.md
relationship.md
persistence.md
api.md
cli.md
verification.md
```

Expected audit-only owners unless cross-reference/current-state wording requires a lossless edit:

```text
concurrency-matrix.md
concurrency.md
health.md
runtime-deployment.md
linux-operating-baseline.md
verification-concurrency-registry.md
```

Do not force edits merely to touch an expected file. Conversely, do not leave stale M2 read semantics merely because a file is not listed as expected-material.

---

# 5. Current read responsibility to consolidate

The current public business GET/read census is exactly 22 routes.

A public GET owns:

```text
strict request validation
strict cursor validation
path-target classification
persisted fact composition
representational decoding required for the typed public response
```

It does not re-run mutation-owned semantic certification solely because state is being read.

The current AS-IS must not retain or imply GET prerequisites such as:

```text
default-version publication re-certification
persisted aggregate mutation-domain validation
inheritance admissibility/cycle/agreement re-certification
schema/DataType re-resolution solely to prove persisted values again
ownership slot semantic revalidation
Relationship topology/schema/default re-certification
historical lifecycle transition changedness/admissibility/version-increase replay
```

Strong write/mutation validation remains current and must not be weakened in documentation.

Representable persisted semantic surprises are readable. Materially undecodable mandatory carriers fail through the bounded internal-failure boundary. Reads do not repair, invent defaults or silently drop mandatory projected state.

Audit at minimum:

```text
docs/architecture/README.md
docs/architecture/datatype.md
docs/architecture/objecttemplate.md
docs/architecture/object.md
docs/architecture/relationship.md
docs/architecture/persistence.md
docs/architecture/api.md
docs/architecture/verification.md
```

for stale wording equivalent to “persisted invariant corruption always fails because GET revalidates semantic invariants”.

---

# 6. One-statement / snapshot current architecture

For the canonical 22 public business GET/read routes:

```text
one complete public projection
    -> exactly one authoritative business SQL statement
    -> ordinary read Unit of Work
    -> one PostgreSQL statement snapshot
    -> no public-GET coherent_read() dependency
```

The coherent response rule is:

```text
writer commit before authoritative execute
    -> complete AFTER projection

writer commit after authoritative statement completes
    -> complete BEFORE projection
```

No mixed generation is allowed within the projected statement result.

There is no cross-request/page repeatable snapshot guarantee and no public snapshot token.

`coherent_read()` remains valid infrastructure outside the canonical 22 GET census. Do not describe it as globally removed or deprecated.

Persistence owns the realization; API owns public route/projection/failure behavior; verification owns durable proof obligations. Keep those ownership boundaries explicit.

---

# 7. Historical lifecycle read boundary

Consolidate the current global and Object-scoped lifecycle GET semantics:

```text
existing public discriminated event DTOs
existing filters
ORDER BY occurred_at DESC, id DESC
trusted representational decoder
no historical mutation-transition replay
```

Mandatory representational decoding includes required family/state fields, UUID/string/integer conversions and recursive JsonValue materialization.

Do not re-certify:

```text
transition admissibility
changedness
schema-version increase
historical agreement with current live state
```

A representable historical semantic surprise remains readable; a materially undecodable mandatory carrier fails boundedly.

Keep mutation-side lifecycle validation strong and distinct.

---

# 8. Complete current cursor matrix

The current identity rule is:

```text
query identity
    = route
    + every membership-affecting path target
    + every membership-affecting filter
    + required semantic presence bits

position
    = complete canonical ordering tuple

limit
    = not semantic identity
```

The exact cursor-bearing route census remains 12:

```text
GET /api/v1/core/datatypes
GET /api/v1/core/datatypes/{datatype_id}/versions
GET /api/v1/core/object-templates
GET /api/v1/core/object-templates/{template_id}/versions
GET /api/v1/core/object-templates/{template_id}/relationship-capabilities
GET /api/v1/core/objects
GET /api/v1/core/objects/{parent_object_id}/components
GET /api/v1/core/objects/{object_id}/relationships
GET /api/v1/core/objects/{object_id}/lifecycle-events
GET /api/v1/core/relationship-definitions
GET /api/v1/core/relationship-definitions/{relationship_definition_id}/versions
GET /api/v1/core/lifecycle-events
```

Mandatory identities/keysets to state exactly:

```text
object_components
    filters = parent_object_id, slot_name
    key     = child_object_id

object_relationships
    filters = object_id, relationship_definition_id, name
    key     = relationship_id, destination_object_id, name

lifecycle_events
    filters include involving_object_id
    global -> None
    Object scoped -> path Object UUID
    key = occurred_at, id DESC

object_templates
    filters include parent_template_id and internal parent_filter_set
    key = namespace, name
```

Cursor codec v1 stays opaque and unchanged. Changed limit remains valid; incompatible route/filter/path/presence/key remains `invalid_cursor`.

Do not describe the two path-target bindings as fixes or deltas; describe them as current identities.

---

# 9. ObjectTemplate parent tri-state

HTTP current meaning:

```text
parent_template_id omitted
    -> no parent predicate

parent_template_id=<UUID>
    -> direct stable children

parent_template_id=null
    -> stable roots only
```

Only exact lowercase `null` is accepted as the explicit root carrier. Empty, malformed, unsupported/uppercase sentinel and repeated values remain invalid requests.

Internal cursor/application state:

```text
omitted   -> parent_template_id=None, parent_filter_set=False
root-only -> parent_template_id=None, parent_filter_set=True
exact     -> parent_template_id=str(UUID), parent_filter_set=True
```

`parent_filter_set` is not public.

CLI current meaning:

```text
omitted       -> no query pair / no parent selector lookup
UUID          -> canonical UUID query pair
human selector -> bounded ObjectTemplate discovery -> UUID query pair
explicit null -> parsed None -> zero selector discovery -> lexical parent_template_id=null
```

Nullable QUERY None uses parameter metadata to emit lexical `null`; nullable BODY None remains JSON null; PATH None remains invalid. Do not broaden generic scalar serialization.

HTTP owns the lexical public query; CLI owns parsing/selector/planning; API/current cursor owner owns the semantic presence distinction.

---

# 10. CLI 201 Location current contract

The exact eight registered 201 operations remain current.

Location template grammar is the closed NETAUTO DSL:

```text
{segment}
{segment.segment...}
segment = [a-z][a-z0-9_]*
```

Token lookup:

```text
1. exact request_values key presence
2. otherwise dot-separated traversal in the validated response JSON object
```

Only:

```text
str
int excluding bool
```

may materialize a token.

Replacement is literal. Python `str.format`, `format_map`, array indexing, attributes, wildcards, conversions and format specs are not part of the grammar.

A registered create succeeds only after:

```text
expected status/body validated
actual Location count == 1
expected Location materializable
actual == expected exactly
```

Missing/repeated/mismatching/non-materializable Location state is `cli_protocol_error`. A canonical successful response must not become `cli_internal_error` solely because of Location materialization. No hidden post-mutation GET exists.

The three nested-response identities and five flat-token identities remain one common protocol mechanism; do not document command-specific hacks.

---

# 11. Preserved M2/current guarantees

M3 does not change, and consolidation must preserve without unnecessary rewrite:

```text
63 business HTTP operations + GET /health/core
15 PostgreSQL tables
one Alembic root/head/current 0001_m2_kernel
41 mutation primitives
15 concurrency family blocks / 861 unordered cells
83 canonical scenarios / 21 safety predicates
centralized mutation lock planner/gates/restart policy
Health contract
runtime/settings/deployment contract
Linux operating procedure
project version 0.2.0
runtime dependency and uv.lock baseline
no native auth/server-TLS/container/orchestrator/backup/observability product surface
```

If consolidation text appears to change any of these, stop and resolve the ownership conflict before proceeding.

---

# 12. README current architecture update

`docs/architecture/README.md` must remain the minimal semantic navigator.

Required changes include:

```text
add concise M3 provenance row
keep exact 15-owner file inventory
replace stale global read principle with current trusted-read/materialization boundary
state one-request projection coherence without implying read semantic re-certification
retain present-tense current system scope
```

The provenance row may summarize M3 historically in one concise navigation line. Semantic sections must not depend on that row.

Do not turn README into a milestone change log.

---

# 13. Verification current architecture

`docs/architecture/verification.md` must describe durable current guarantees rather than M3 bookkeeping.

Preserve T0–T10 and current project-wide verification policy.

Add/consolidate durable obligations equivalent to:

```text
public business GET census = 22 exact
cursor route census = 12 exact
registered CLI 201 Location census = 8 exact
canonical GET read-semantic-authority audit
representable surprise vs undecodable-carrier boundary
trusted historical lifecycle decoder evidence
complete cursor identity and true multipage keysets
ObjectTemplate HTTP/CLI tri-state
22/22 real-PostgreSQL one-business-statement evidence
deterministic BEFORE/AFTER statement-snapshot evidence
schema/migration/dependency/lock non-drift
```

Do not copy M3-VER IDs or candidate results into current architecture.

The authoritative concurrency registry remains 83 scenarios / 21 predicates; do not conflate it with the separate structured worker-outcome scenario count printed during pytest.

---

# 14. Cross-document consistency sweep before candidate publication

At minimum check mechanically or with bounded scripts:

```text
exact 15 architecture files
all Markdown links resolve
README owner map equals actual 15-file set
M1/M2/M3 leakage limited to README provenance/navigation
no M3-OUT/AC/VER/CQG/Snn/RF/candidate SHA in semantic owners
no TODO/TBD/FIXME/open semantic placeholder
no stale “new/introduced/changed/previously/M3 delta” semantic narration
GET census == 22
cursor census == 12
CLI 201 Location census == 8
business API still 63 + Health 1
schema tables == 15
Alembic unique head == 0001_m2_kernel
concurrency scenarios/predicates == 83/21
ObjectTemplate HTTP/CLI tri-state meanings agree
read responsibility agrees across model/persistence/API/verification
one-statement snapshot wording agrees across persistence/API/verification
lifecycle decoder wording agrees across Object/Relationship/API/persistence/verification
```

Do not merely grep and replace. Inspect false positives and semantic context.

---

# 15. Repository verification gate

With `TEST_DATABASE_URL` available, run at minimum:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q

uv run pytest -q tests/test_m3_traceability.py tests/test_m3_s07_acceptance.py
uv run pytest -q tests/test_m3_s00_cli_location.py tests/test_m3_s01_parent_tristate.py tests/test_m3_s02_datatype_reads.py tests/test_m3_s03_objecttemplate_reads.py tests/test_m3_s04_object_reads.py tests/test_m3_s05_relationship_reads.py tests/test_m3_s06_integration.py tests/test_m3_s07_acceptance.py tests/test_m3_traceability.py
uv run pytest -q tests/test_migrations.py tests/test_schema_metadata.py
uv run pytest -q -m "not postgresql"
uv run pytest -q
```

Also run/document the consolidation-specific Markdown inventory/link/wording/owner consistency checks you implement locally or through a bounded one-shot command. Do not add permanent test code; tests are outside consolidation scope.

Required outcome:

```text
skip / xfail / rerun             0 / 0 / 0
supported-path 40P01             0
unexpected 40001                 0
compare_metadata                 []
new unexplained warning          0
broken links                     0
unresolved semantic placeholder  0
production/test/schema delta     0
```

A previously reviewed third-party warning may be reported separately.

If a repository test fails because the accepted current architecture genuinely contradicts an existing permanent test, STOP and report it. Do not edit the test inside consolidation scope.

---

# 16. Candidate status and handoff

Once the complete 15-file corpus and verification gate pass, update only `docs/milestones/M3/status.md` to:

```text
AS-IS consolidation = CANDIDATE READY FOR REVIEW
M3-S07 = COMPLETED
software implementation = NOT AUTHORIZED
M3 = NOT DELIVERED
consistency closure = NOT AUTHORIZED
```

Commit the complete candidate as one documentation candidate commit. Do not create a separate acceptance decision; reviewer owns completion.

Candidate handoff must report:

```text
branch
candidate commit
parent/baseline
local/origin/remote synchronization
working tree
PR state
changed architecture files
unchanged audited architecture files
exact 15-file inventory
link audit
milestone/temporal wording audit
owner/conflict audit
22 GET / 12 cursor / 8 Location audit
15-table/Alembic non-drift
83-scenario/21-predicate non-drift
exact verification commands and results
collection/full/non-PG counts
skip/xfail/rerun/warning census
production/test/schema/dependency changes = none
```

Do **not** mark consolidation `COMPLETED`. Do **not** authorize or start consistency closure. Do **not** mark M3 delivered.

---

# Completion boundary

Your successful output is only:

```text
M3 AS-IS CONSOLIDATION — CANDIDATE READY FOR REVIEW
```

Reviewer then inspects the actual current-architecture delta. Only reviewer acceptance may transition:

```text
AS-IS consolidation -> COMPLETED
```

After that, consistency closure may be considered as a new separately authorized post-acceptance gate. Delivery remains later and separate.