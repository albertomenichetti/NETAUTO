# Codex implementation prompt — M2-S08

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

This file is an execution aid for Codex. It is subordinate to `AGENTS.md`, the delivered AS-IS, the FINAL/FROZEN M2 contract and architecture set, `steps.md`, the ratified technology baseline, and the reviewer-owned operational state in `status.md`.

## Assignment

Implement exactly:

```text
M2-S08 — Integrated regression, traceability and negative-surface closure
```

Work directly on branch:

```text
M2
```

The reviewer-owned authorization baseline is:

```text
1f8e82de73d953830a6b31045ec96dfe19116dd9
docs(m2): accept corrected S07 and reopen S08
```

That SHA is the required ancestry baseline, not the expected current HEAD: publication of this prompt necessarily creates a later commit. Start from the current clean `origin/M2` only when:

```text
origin/M2 contains 1f8e82de73d953830a6b31045ec96dfe19116dd9
this prompt exists at the current remote HEAD
status.md still marks M2-S08 READY or IN PROGRESS
M2-S09 remains BLOCKED
```

Current authorization is:

```text
M2-S00 ... M2-S07    reviewer-owned COMPLETED
M2-S08                READY
M2-S09                BLOCKED / not started
```

Deliver the complete vertically coherent S08 closure:

```text
one singular machine-checkable M2 traceability graph
M2-VER-31 concrete AS-IS regression closure
M2-VER-32 concrete complete outcome/authority traceability
exact 16 OUT / 32 AC / 32 VER / 83 scenario / 21 predicate censuses
exact 63 business HTTP / 63 remote CLI mapping equality
all 51 delivered concurrency IDs retained and concretely represented
finite preserved-AS-IS guarantee -> regression-target registry
finite M2 delta allowlist and no unregistered divergence
finite positive and negative surface inventories
contract-quality-gate and authority/provenance closure
no WIP implementation authority and no unresolved normative placeholder
final-acceptance evidence-record schema and validation harness
complete integrated regression and exact-remote candidate reruns
M2-S08 CANDIDATE READY FOR REVIEW handoff
```

Do not start `M2-S09`. Do not perform final M2 acceptance, create `acceptance.md`, mark the milestone delivered, merge, tag, publish a GitHub Release, upload an artifact, create a pull request, or add/use GitHub Actions.

The S08 result remains an implementation-slice candidate. `M2-S09` owns the final identified candidate commit, the exact final wheel, the complete direct 83-scenario and 32-bundle acceptance ledger, reviewer acceptance, AS-IS consolidation and milestone delivery.

Do not commit wheels, `dist/`, virtual environments, coverage output, generated certificates, database secrets, temporary evidence records or installed target directories.

---

# 1. Mandatory pre-flight

Before editing, re-read and obey at minimum:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md
    STACK-01 ... STACK-10

# delivered AS-IS
docs/architecture/README.md
docs/architecture/datatype.md
docs/architecture/objecttemplate.md
docs/architecture/object.md
docs/architecture/relationship.md
docs/architecture/persistence.md
docs/architecture/concurrency-matrix.md
docs/architecture/concurrency.md
docs/architecture/api.md
docs/architecture/verification.md
docs/architecture/verification-concurrency-registry.md

# frozen M2 authority
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/README.md
docs/milestones/M2/architecture/provenance.md
docs/milestones/M2/architecture/relationship.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/concurrency-matrix.md
docs/milestones/M2/architecture/concurrency.md
docs/milestones/M2/architecture/health.md
docs/milestones/M2/architecture/cli.md
docs/milestones/M2/architecture/runtime-deployment.md
docs/milestones/M2/architecture/verification.md
docs/milestones/M2/steps.md
docs/milestones/M2/status.md

docs/milestones/M2/wip/M2-S08-codex-prompt.md
```

Historical records may be inspected only as evidence/navigation and never as semantic authority, including:

```text
docs/milestones/M1/acceptance.md
docs/milestones/M1/status.md
docs/milestones/M2/wip/*.md
Git history and prior candidate reports
```

Inspect the accepted implementation and current verification infrastructure before choosing a decomposition. At minimum inspect:

```text
pyproject.toml
uv.lock
.python-version
.gitignore
alembic.ini

src/netauto/failures.py
src/netauto/persistence/metadata.py
src/netauto/persistence/locking.py
src/netauto/runtime/schema_guard.py
src/netauto/entrypoints/http.py
src/netauto/entrypoints/api/errors.py
src/netauto/transport/http/errors.py
src/netauto/cli/registry.py
src/netauto/cli/
src/netauto/migrations/
src/netauto/release/runtime.pylock.toml

tests/conftest.py
tests/test_m1_traceability.py
tests/test_m2_s00_traceability.py
tests/test_m2_traceability.py
tests/test_object_scope.py
tests/test_schema_metadata.py
tests/test_migrations.py
tests/test_persistence_constraints.py
tests/test_runtime_schema_guard.py
tests/test_http_composition.py
tests/test_health*.py
all tests/test_m2_s05_*.py
all tests/test_m2_s06_*.py
all tests/test_m2_s07_*.py
tests/support/
```

Confirm from the repository and environment:

```text
checked-out branch                    M2
origin/M2 ancestry                    contains 1f8e82de...
working tree                          clean
contract                              FINAL / FROZEN
architecture set                      FINAL / FROZEN
steps                                 FINAL / FROZEN
technology STACK-01 ... STACK-10      RATIFIED
M2-S07                                reviewer-owned COMPLETED
M2-S08                                READY or IN PROGRESS
M2-S09                                BLOCKED
relevant authority reopen             none
TEST_DATABASE_URL                     present, valid, externally supplied real PostgreSQL
```

Do not provision PostgreSQL, invent credentials, silently use localhost, use SQLite, Docker, Testcontainers or an embedded database. If `TEST_DATABASE_URL` is missing or invalid, bounded non-PostgreSQL work may continue but S08 cannot become candidate-ready.

If the delivered AS-IS and frozen M2 authority are contradictory or fail to determine an observable result, stop the affected point and report the architecture finding. Do not select behavior from current code, weaken a test, or edit frozen authority to fit a convenient implementation.

---

# 2. Hard scope boundary

## 2.1 In scope

```text
extension of the singular tests/test_m2_traceability.py authority
M2-VER-31 and M2-VER-32 concrete target ownership
exact primary-bundle owner registry for M2-VER-01 ... M2-VER-32
outcome -> architecture owner -> AC -> VER -> target graph
contract quality-gate traceability
preserved AS-IS guarantee -> regression-target mapping
M1 delivered 51-scenario retention and M2 83-scenario representation
21-predicate and recipe closure
M2 delta allowlist and exact unchanged-surface assertions
public HTTP / CLI / error-catalog equality and negative API surface
schema / constraint / index / Alembic positive and negative inventories
auth/TLS/credential/insecure-surface absence
CLI direct-kernel import absence
automatic migration/stamp/repair absence
WIP authority and normative-placeholder closure
evidence-record schema under docs/milestones/M2/evidence/
test-only evidence-record validator/harness
focused and integrated verification
status/evidence publication for the S08 candidate
```

A bounded implementation correction is allowed only when a deterministic S08 regression proves an implementation defect whose required behavior is already unambiguous in the delivered AS-IS plus frozen M2 delta. Keep such a patch minimal and register its regression target.

## 2.2 Out of scope

Do not introduce, change or claim:

```text
new business, Health, CLI or deployment capability
new route, command, status, error code, DTO field or selector
new table, constraint, index, migration revision or Alembic head
new dependency, lock resolution, setting or process entrypoint
new authentication, authorization, TLS or credential contract
new compatibility/version-negotiation behavior
new installer, migration wrapper, process manager or orchestration asset
M2-S09 final candidate execution or final decision
acceptance.md, delivered AS-IS consolidation or master merge
coverage percentage as a correctness gate
```

No production-code, schema, migration, dependency or runtime change is expected. If satisfying S08 appears to require an observable change outside the frozen delta allowlist, stop and report rather than broadening scope.

Preserve exactly:

```text
version                          0.2.0
authoritative tables             15
Alembic bases / heads            1 / 1
head                             0001_m2_kernel
compare_metadata                 []
public business HTTP operations  63
operational Health operations    1
total public HTTP operations     64
CLI remote / local operations    63 / 8
public error codes               23
registry examples                65
canonical scenarios              83
safety predicates                21
runtime package graph            29 total / 27 Linux-applicable
```

---

# 3. Use one singular traceability authority

Extend the existing singular machine-checkable registry in:

```text
tests/test_m2_traceability.py
```

Do not create a competing M2 traceability module. Supporting constants/helpers may live in a bounded test-only support module when needed, but `tests/test_m2_traceability.py` remains the aggregation and authority check.

Preserve and complete the existing registries:

```text
M2_OUTCOMES
M2_ACCEPTANCE_CRITERIA
M2_EVIDENCE_BUNDLES
M2_CONCURRENCY_SCENARIOS
M2_OUTCOME_TO_ACCEPTANCE
M2_ACCEPTANCE_TO_EVIDENCE
M2_EVIDENCE_TO_TARGETS
M2_SCENARIO_TO_TARGETS
M2_SCENARIO_TO_RECIPES
M2_PREDICATE_TO_SCENARIOS
```

At S08 completion their exact censuses are:

```text
M2-OUT                         16 / 16
M2-AC                          32 / 32
M2-VER                         32 / 32
canonical scenarios            83 / 83
safety predicates              21 / 21
```

Add a finite primary ownership map, conceptually:

```text
M2_PRIMARY_BUNDLE_OWNER = {
    "M2-VER-01": "M2-S01",
    ...
    "M2-VER-32": "M2-S08",
}
```

Exact ownership is:

```text
S01    M2-VER-01..07, 10, 20, 21
S02    M2-VER-08, 09, 11..14
S03    M2-VER-15..19
S04    M2-VER-22, 23
S05    M2-VER-27
S06    M2-VER-25, 26, 28
S07    M2-VER-24, 29, 30
S08    M2-VER-31, 32
```

Machine-check:

```text
exact 32-key census
one and only one primary slice per bundle
all owner slices are M2-S01 ... M2-S08
all previous primary/support/review-fix registries remain intact
M2-VER-31 and M2-VER-32 are no longer DESIGNED/empty
all 32 M2_EVIDENCE_TO_TARGETS entries are IMPLEMENTED and non-empty
all target node IDs exist and collect
no duplicate target inside one declared role
```

Update every stale S05/S06/S07 traceability assertion that currently expects `M2-VER-31` or `M2-VER-32` to remain `DESIGNED`. Replace it with explicit S08 ownership checks; do not delete the previous-slice preservation assertions.

---

# 4. Complete outcome and architecture-owner traceability

Add an exact finite normative owner registry using repository paths, not free-form labels. It must distinguish:

```text
delivered AS-IS semantic owners
the M2 contract
the frozen M2 architecture owners
ratified technology baseline
steps/status operational documents
non-authoritative WIP/history
```

Add exact maps equivalent to:

```text
M2_OUTCOME_TO_ARCHITECTURE_OWNERS
M2_ARCHITECTURE_OWNER_TO_OUTCOMES
```

Use the frozen outcome coverage in `architecture/verification.md`:

```text
OUT-01  relationship + api + persistence
OUT-02  relationship + concurrency-matrix + concurrency
OUT-03  relationship + persistence + api
OUT-04  relationship + api + concurrency owners
OUT-05  relationship + persistence
OUT-06  api + persistence
OUT-07  relationship + api + persistence
OUT-08  concurrency-matrix + concurrency + persistence
OUT-09  persistence
OUT-10  runtime-deployment + persistence
OUT-11  health + api
OUT-12  cli + api
OUT-13  runtime-deployment + cli
OUT-14  runtime-deployment
OUT-15  runtime-deployment + cli
OUT-16  verification + all owning architecture documents
```

Machine-check the complete chain:

```text
M2 outcome
    -> at least one valid frozen architecture owner
    -> one or more M2 acceptance criteria
    -> exact same-number M2 evidence bundles
    -> one or more concrete collected targets
```

Also prove:

```text
no owner path is outside the frozen authority composition
no semantic owner is a WIP file, status.md, prompt, source file or test file
inverse owner/outcome mapping is exact
all owner documents exist and are FINAL/FROZEN where required
no outcome, acceptance criterion, bundle or target is orphaned
```

Do not invent stable semantic identifiers for unnumbered prose. Use the frozen OUT/AC/VER identifiers plus finite preserved-guarantee and negative-surface registries defined below.

---

# 5. Contract portfolio and quality-gate closure

Add exact test-only registries for:

```text
M2_CAPABILITY_PORTFOLIO
M2_CAPABILITY_TRACE
M2_CONTRACT_QUALITY_GATES
M2_CONTRACT_QUALITY_GATE_TO_TARGETS
```

The capability portfolio must equal the frozen contract:

```text
in scope
    Versioned Relationship property model
    Core Health API
    NETAUTO CLI
    Runtime configuration and production deployment

cross-cutting foundation
    First durable Alembic kernel baseline

explicitly outside M2
    Logging operational review / introduction
```

For every in-scope/foundation capability, explicitly map the relevant:

```text
objective(s)
outcome(s)
acceptance criterion/criteria
evidence bundle(s)
architecture owner(s)
```

Overlap is expected. Do not infer coverage from substring coincidence.

The contract-quality-gate registry is exactly:

```text
M2-CQG-01 ... M2-CQG-10
```

Permanent T10 targets must prove:

```text
CQG-01  portfolio classification exact and closed
CQG-02  no unresolved normative placeholder/open point
CQG-03  preserved guarantee and delta allowlist closure
CQG-04  capability -> objective -> OUT -> AC -> VER coverage
CQG-05  dependency graph directed/acyclic with one authority per responsibility
CQG-06  Scope / Non-goal / trust-boundary consistency
CQG-07  cross-cutting atomicity/canonicalization/coherence guarantees covered
CQG-08  deferred choices remain implementation-only and do not change outcomes
CQG-09  canonical vocabulary and stable identifiers
CQG-10  freeze/change-control and formal-reopen rules remain present
```

These tests validate the frozen documents. They must not edit or reinterpret them.

---

# 6. `M2-VER-31` — AS-IS regression closure

Create a permanent exact registry, conceptually:

```text
M2_AS_IS_GUARANTEE_TO_TARGETS: dict[str, frozenset[str]]
```

Use one canonical key per delivered guarantee and require exactly the 18 preserved guarantees in the M2 contract:

```text
stable RelationshipDefinition topology and symmetry
RelationshipResolution identity, membership and endpoint lineages
mutable Resolution name as non-key metadata
Definition equivalence and cross-Definition Resolution conflict semantics
Relationship factual identity
symmetric/non-symmetric factual uniqueness
self-loop support
exact runtime-view identity
complete deterministic runtime-resolution closure
Object stable-lineage endpoint admission
Object and RelationshipDefinition delete blockers
Object-relative semantic-view deduplication
/api/v1/core business namespace
strict request bodies
failure-class boundary
bounded error details and no SQL/internal leakage
opaque keyset pagination
single-request coherent reads
```

For each guarantee:

```text
one or more concrete deterministic targets
all target IDs exist and collect
no file-level or full-suite pseudo-target
runtime/PostgreSQL claims use appropriate real evidence
no guarantee is mapped only to documentation prose
```

Prefer existing accepted M1/M2 tests. Add a new regression only when the existing suite does not concretely prove the guarantee.

## 6.1 Delivered concurrency preservation

Machine-check:

```text
exact delivered scenario IDs       51 / 51
all delivered IDs remain keys in the 83-ID M2 registry
all delivered target sets remain non-empty
all original delivered targets remain represented
all delivered recipes remain represented
all 19 delivered predicates remain present and non-empty
new predicates are exactly VH and RS
no delivered stable scenario ID is renamed or removed
```

The only delivered scenario obligation deltas are the frozen seven:

```text
ARB-05
ARB-06
ARB-07
SNAP-01
SNAP-02
ATOMIC-02
ATOMIC-03
```

Register their exact authorized modifications. No other delivered scenario obligation changes.

The direct all-51-delivered-target union is a mandatory S08 gate. It must use real PostgreSQL and report selected/unique/pass counts. The dedicated direct all-83 acceptance ledger remains S09-owned, although the ordinary S08 full suite and PostgreSQL gate may naturally execute all implemented scenario tests.

## 6.2 Exact M2 delta allowlist

Add one explicit finite delta authority, conceptually:

```text
M2_DELTA_ALLOWLIST
M2_PUBLIC_WIRE_DELTA_ALLOWLIST
M2_DELIVERED_SCENARIO_DELTA_ALLOWLIST
M2_SCHEMA_RUNTIME_DELTA_ALLOWLIST
```

The high-level allowlist is exactly:

```text
RelationshipDefinition CREATE includes v1 DRAFT
capability requires one PUBLISHED RDV
Relationship CREATE request/projection adds exact pin and properties
duplicate Relationship CREATE becomes relationship_fact_conflict
missing Relationship DELETE becomes resource_not_found
Relationship lifecycle adds before/after state and new change kinds
startup requires exact shipped Alembic revision
one fresh durable root baseline replaces disposable development history
new Health, CLI, release and Linux-runtime surfaces
```

The public-wire delta must equal `architecture/api.md` section “Explicit AS-IS wire deltas”, including the exact route/DTO/status changes and no others.

Machine-check at least:

```text
M1 business operations             52
M2 business operations             63
business additions                 exact 11-route S01/S02 delta
removed delivered business routes  0
operational addition               exact GET /health/core
M1 and M2 public code catalog       exact same 23 codes
new public error codes              0
```

Schema/runtime closure must prove the frozen positive and negative inventories rather than compare only counts. Use the delivered 13-table AS-IS plus M2 persistence authority to establish the exact authorized transition to the final 15-table schema, modified exact pins/state/history, one root/head, and the negative index/table contract.

Any difference outside the registered allowlist is a failing regression or an architecture STOP condition.

## 6.3 `M2-VER-31` target ownership

Add explicit primary targets, conceptually:

```text
S08_PRIMARY_BUNDLE_TARGETS["M2-VER-31"]
```

It must include the dedicated AS-IS guarantee/delta closure targets and every concrete target required by `M2_AS_IS_GUARANTEE_TO_TARGETS`. A complete repository command is mandatory execution evidence but does not replace concrete node ownership in the registry.

---

# 7. Positive and negative surface closure

Create one finite machine-checkable negative-surface authority, conceptually:

```text
M2_NEGATIVE_SURFACE_CONTRACT
M2_NEGATIVE_SURFACE_TO_TARGETS
```

Do not use one broad grep assertion as substitute for finite ownership. Every explicit M2 contract non-goal and every negative surface named by `architecture/verification.md` must appear exactly once in the registry and map to at least one concrete assertion target.

A bounded stdlib parser may extract the explicit fenced entries under the frozen contract Non-goal sections and compare them with the registry. Use an explicit false-positive/format allowlist; do not make Markdown wording a new semantic authority.

Required categories include at minimum:

```text
relationship model non-goals
lifecycle/history non-goals
API/protocol non-goals
security/network non-goals
deployment/platform non-goals
data-protection non-goals
observability non-goals
CLI non-goals
Health non-goals
Alembic non-goals
performance/availability non-goals
```

## 7.1 Public HTTP and error surface

Prove exact positive inventory:

```text
41 mutations
22 reads
63 /api/v1/core business operations
1 GET /health/core
64 total public HTTP operations
23 public business error codes
```

Prove exact absence of:

```text
generic PUT/PATCH
action DSL
bulk/batch transaction endpoint
generic GET /health
standalone RelationshipResolution CRUD
standalone property-declaration CRUD
runtime Relationship-resolution CRUD
property-value search
event-set/transition resource
schema migration endpoint
auth/login/logout/token/account/role routes
401/403 native contract
JSON Schema projection or dynamic semantic extension
```

The exact generated OpenAPI operation set must equal the frozen registry. Minimum-count assertions are forbidden.

## 7.2 CLI coverage and authority boundary

Expose and machine-check exact test-only sets equivalent to:

```text
PUBLIC_HTTP_OPERATIONS
CLI_REMOTE_OPERATION_COVERAGE
HEALTH_LOCAL_COMMAND_COVERAGE
```

Require:

```text
63 business operations == 63 remote CLI mappings
one mapping per business operation
no duplicate route/method or command identity
GET /health/core covered by /connect and /status
no redundant remote Health command
8 exact local commands
65 exact registry examples
```

Statically inspect the complete production CLI import closure. Reject direct or transitive CLI dependency on:

```text
netauto.application
netauto.persistence
SQLAlchemy
Psycopg
Alembic execution
server composition
```

except the neutral transport DTO/value modules explicitly permitted by the CLI architecture.

Also prove absence of URL userinfo, credential/header injection options, persistent credential/profile/cookie/history surfaces, insecure TLS bypass, hidden retry and hidden post-mutation GET.

## 7.3 Schema, constraint, index and Alembic surfaces

Machine-check exact positive inventories from metadata, migration and live PostgreSQL:

```text
15 tables
exact columns/types/nullability/defaults
named PK/UNIQUE/CHECK/FK and delete actions
exact explicit indexes, sort order, predicates and INCLUDE columns
one installed/root revision
one base
one head 0001_m2_kernel
compare_metadata == []
```

Machine-check the complete negative contract, including absence of:

```text
runtime Relationship property EAV
property-value rows
effective-schema cache
compiled generic schema
reverse-dependency materialization
surrogate RDV/declaration/runtime-resolution IDs
separate Relationship timeline
event-set grouping identity
GIN on Object/Relationship properties
GIN/expression lifecycle snapshot indexes
standalone default_version indexes
duplicate PUBLISHED-only indexes
second factual-identity index
event-set grouping index
multiple Alembic heads
executable disposable M1 revisions
startup migration/stamp/repair
```

Do not weaken an exact existing schema assertion to a subset/count assertion.

## 7.4 Auth, TLS, runtime and deployment surfaces

Preserve/reuse installed evidence proving:

```text
no native auth/authorization/credential storage
no OpenAPI securitySchemes or 401/403 responses
trusted-boundary HTTP only
external TLS for untrusted segments
verified CLI HTTPS certificate and hostname
no insecure/skip-verify option
no native server certificate/key lifecycle settings
database transport solely through database_url
no secret/internal detail in Health/logging/CLI/artifact/config
no Docker/Kubernetes/systemd/process-manager/CI deployment product
```

## 7.5 Automatic migration absence

Use AST/import/call-graph checks plus existing runtime/T9 evidence to prove:

```text
application factory does not upgrade/stamp/repair
ASGI lifespan does not upgrade/stamp/repair
CLI import/invocation does not upgrade/stamp/repair
wheel installation does not upgrade/stamp/repair
only explicit Alembic administration owns schema realization
```

A raw string search alone is insufficient where aliases or imported callables could hide a call path.

## 7.6 WIP authority absence

The following must be true:

```text
production code has no dependency on docs/milestones/M2/wip
tests do not read an execution prompt as semantic authority
final/frozen implementation requirements resolve to AS-IS + contract + architecture + technology baseline
WIP references in normative documents are only explicit provenance, retirement, freeze-record or non-authority statements
all 19 historical WIP documents retain one final disposition in provenance.md
unclassified WIP documents = 0
```

Do not assert that the string `wip` is globally absent: frozen contract/architecture/provenance documents deliberately record historical provenance. Build a finite allowlist of permitted reference contexts and reject normative dependency language or unclassified files.

## 7.7 Normative placeholder absence

Scan only the authoritative corpus with a bounded parser and explicit contextual exceptions. Prove no unresolved semantic:

```text
TBD
TODO
FIXME
OPEN QUESTION
unresolved candidate
open design/contract point
PARTIALLY REOPENED authority
```

Do not misclassify domain lifecycle `DRAFT`, quoted negative examples, historical supersession lists, or sentences explicitly stating that no open point remains.

---

# 8. `M2-VER-32` — complete outcome traceability

Add explicit primary target ownership:

```text
S08_PRIMARY_BUNDLE_TARGETS["M2-VER-32"]
```

The bundle must concretely prove:

```text
16/16 outcomes
32/32 acceptance criteria
32/32 evidence bundles
83/83 scenario IDs
21/21 safety predicates
one primary owner for every bundle
OUT -> owner -> AC -> VER -> target chain
all 18 preserved AS-IS guarantees -> regression targets
all public business operations -> CLI mappings
all explicit negative surfaces/non-goals -> assertion targets
all 10 contract quality gates -> targets
no orphan or unauthorized architecture requirement
no unresolved normative placeholder
no WIP implementation authority
```

`M2-VER-32` is T10. Do not make its success depend on importing and starting PostgreSQL merely to discover identifiers; runtime targets it references remain separately executed through their owned layers.

At the end of S08:

```text
M2_EVIDENCE_TO_TARGETS["M2-VER-31"] = IMPLEMENTED / non-empty
M2_EVIDENCE_TO_TARGETS["M2-VER-32"] = IMPLEMENTED / non-empty
all 32 bundles                         IMPLEMENTED / non-empty
```

Candidate execution records may report all concrete S08 targets as passed. `PASS` in the final durable all-32 candidate ledger remains S09-owned.

---

# 9. Final-acceptance evidence record schema — prepare, do not populate

Create:

```text
docs/milestones/M2/evidence/README.md
```

This document is non-normative evidence-format guidance beneath frozen verification architecture. It must explain that S09 creates the candidate-specific record; S08 defines and validates the finite schema only.

Provide one test-only validator/harness using stdlib dataclasses, typed structures or an equivalent bounded mechanism. Do not add a dependency and do not introduce JSON Schema as a public or semantic NETAUTO language.

The future record schema must require at least:

```text
schema/version of the evidence record
candidate commit SHA and branch
release version
wheel filename, byte size, member count and SHA-256
runtime-lock path, size, package census and SHA-256
Python / uv / Hatchling / PostgreSQL / Linux versions
locked-environment and build confirmation
exact command ledger with argv, exit status, duration and test census
M2-VER-01 ... M2-VER-32 status ledger
83-scenario status ledger
21-predicate coverage ledger
schema/Alembic/compare_metadata result
OpenAPI/business/Health/CLI operation census
installed-wheel/T9 result
skip/xfail/rerun/warning/SQLSTATE census
open findings
review decision field reserved for reviewer ownership
```

Evidence states are the frozen vocabulary:

```text
DESIGNED
IMPLEMENTED
PASS
FAIL
BLOCKED
```

Validation requirements:

```text
exact identifier sets; no missing or extra keys
40-hex candidate SHA
64-hex artifact hashes
non-negative durations/counts
no credential/database URL/secret fields or values
no acceptance decision may be pre-populated by the implementer
stable serialization suitable for Git review
```

Do not create an actual candidate evidence record in S08. Do not claim final acceptance and do not add `docs/milestones/M2/acceptance.md`.

---

# 10. Suggested implementation decomposition

A bounded decomposition is preferred:

```text
tests/test_m2_traceability.py
    singular aggregate graph, owner maps, VER-31/32 ownership

tests/test_m2_s08_regression.py
    AS-IS guarantees, delta allowlist and delivered-scenario retention

tests/test_m2_s08_negative_surface.py
    API/CLI/schema/Alembic/auth/TLS/migration/WIP/placeholder closure

tests/test_m2_s08_evidence.py
    evidence-record schema and contract-quality-gate validation

tests/support/m2_evidence.py
    optional test-only parser/record validator helpers

docs/milestones/M2/evidence/README.md
    future S09 record format and authority boundary
```

Equivalent coherent decomposition is allowed. Avoid one opaque test containing every assertion and avoid a proliferation of competing registries.

Tests must use repository paths relative to the repository root, stable sorted collections and bounded diagnostics. Static inspections must parse Python/Markdown structures where material instead of relying on fragile substring coincidence.

---

# 11. Required focused verification

Run the smallest affected evidence first. Record exact selected, unique, parametrized and passed counts plus durations.

## 11.1 Singular graph and owner closure

Execute exact targets proving:

```text
16/32/32 identifier censuses
primary-bundle owner map
OUT -> owner -> AC -> VER -> target
83 scenario / 21 predicate / recipe closure
all 32 bundles IMPLEMENTED and non-empty
contract-quality-gate registry
```

## 11.2 M2-VER-31

Execute the complete deduplicated target union for:

```text
all 18 preserved guarantees
delta allowlist
51 delivered scenario retention
route/error/schema delta closure
pagination/coherence/non-leakage regressions
no unrelated public/persistence divergence
```

Then execute the exact direct union of all 51 delivered concurrency scenario targets with real PostgreSQL.

## 11.3 M2-VER-32

Execute the complete deduplicated T10 target union for:

```text
complete traceability graph
negative-surface contract
contract quality gates
authority/provenance/WIP closure
normative-placeholder closure
evidence-record schema validation
```

## 11.4 Positive/negative inventories

Run exact focused groups for:

```text
OpenAPI / route / error catalog
CLI registry and import boundary
metadata / live schema / constraints / indexes
Alembic root/base/head and no automatic migration
auth/TLS/trust/secret surfaces
WIP and normative-document policy
```

## 11.5 Previous-slice preservation

Re-execute at minimum:

```text
tests/test_m1_traceability.py
tests/test_m2_s00_traceability.py
tests/test_m2_traceability.py
all S05 tests
all S06 tests
all S07/T9 tests
Settings/runtime/schema-guard/Health groups
migration/schema metadata groups
```

Do not weaken or deselect a previously accepted target to make S08 pass.

---

# 12. Quality and integrated gates

Run before publication:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

Then run and report:

```text
focused S08 target union
M2-VER-31 complete union
M2-VER-32 complete union
all T10/static closure targets
all 51 delivered scenario targets
complete delivered regression suite
complete M2 functional/API/CLI/runtime/T9 suite
complete PostgreSQL/concurrency suite
complete non-PostgreSQL suite
complete repository suite
```

Use the externally supplied real PostgreSQL target. Run interfering PostgreSQL suites serially unless the existing harness provides isolated databases.

Require:

```text
skip / xfail / rerun             0 / 0 / 0
supported-path 40P01             0
unexpected 40001                 0
negative controls                exact finite expected census only
warning changes                  none unexplained
schema drift                     []
```

No generic flaky retry. A timeout is failure/hang protection, not scheduling evidence.

S08 does not replace S09's direct all-83 scenario and all-32 bundle final candidate ledger. Do not label the S08 execution as final milestone acceptance.

---

# 13. Candidate publication

Only after every mandatory S08 gate passes, update `docs/milestones/M2/status.md` to:

```text
M2-S08    CANDIDATE READY FOR REVIEW
M2-S09    BLOCKED
```

Never set S08 to `COMPLETED`; that is reviewer-owned.

Record in `status.md`:

```text
starting ancestry and implementation/evidence commits
closed S08 obligations
exact 16/32/32/83/21/63 censuses
VER-31 and VER-32 selected/unique/pass counts
51-delivered-scenario direct gate
focused/T10/schema/API/CLI/T9 results
PostgreSQL, non-PostgreSQL and full-suite counts/durations
skip/xfail/rerun/warning and SQLSTATE censuses
CPython/PostgreSQL/uv/Hatchling versions
version/wheel/runtime-lock facts reused from the candidate build
unchanged production/schema/API/CLI/dependency boundaries
S09 blocked and no final acceptance claimed
```

Do not create a candidate-specific file under `docs/milestones/M2/evidence/`; S09 owns that record.

Recommended commit separation:

```text
implementation/tests/evidence-schema correction
candidate evidence/status publication
```

Inspect status and diff before each commit. Stage only confirmed S08 paths. Never stage `dist/`, wheels, venvs, generated certificates, secrets, coverage files or temporary records.

---

# 14. Push and exact-remote rerun

Push only to `origin/M2`. Then verify:

```text
HEAD == origin/M2 == remote M2
working tree clean
ahead / behind 0 / 0
no PR
no GitHub Action or workflow run
no tag or GitHub Release
no artifact publication
```

On the exact remote HEAD rerun at least:

```text
M2-VER-31 complete union
M2-VER-32 complete union
all S08/T10 targets
M1/S00/M2 traceability
all 51 delivered scenario targets
route/error/API/CLI equality targets
schema/migration positive and negative targets
complete S07/T9 targets
PostgreSQL/concurrency suite
non-PostgreSQL suite
complete repository suite
```

If any post-push gate fails, append a corrective commit, return S08 to `IN PROGRESS`, keep S09 blocked and do not hand off a candidate.

---

# 15. Completion report

Report verified facts only:

```text
branch and starting ancestry
implementation and evidence/status commits
HEAD/origin/remote equality
ahead/behind and clean worktree
files changed
VER-31 and VER-32 closure
16/32/32/83/21/63 exact censuses
18 preserved guarantees mapped
negative-surface and delta-allowlist closure
51 delivered scenario result
focused/T10/schema/API/CLI/T9/full results
skip/xfail/rerun/warning and SQLSTATE census
evidence-schema files created
unchanged production/schema/API/CLI/dependency boundaries
absence of PR/Actions/tag/Release/artifact publication
M2-S09 blocked
```

The only successful implementer state is:

```text
M2-S08    CANDIDATE READY FOR REVIEW
M2-S09    BLOCKED
```

`M2-S08 COMPLETED`, final candidate acceptance, AS-IS consolidation, `M2 DELIVERED` and merge remain reviewer/human-owned.