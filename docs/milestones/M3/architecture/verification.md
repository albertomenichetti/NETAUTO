# M3 — Verification Architecture

**Status:** FINAL / FROZEN — ADP-08 CLOSED

**Authority:** M3 TO-BE ARCHITECTURE — VERIFICATION OWNER

## Purpose and authority boundary

This document owns the M3 verification-design delta required to prove the frozen milestone contract and the complete M3 TO-BE architecture set.

It extends the delivered verification authority in `docs/architecture/verification.md` without redefining domain, persistence, API, CLI or runtime semantics. Those semantics remain owned by their respective AS-IS/M3 architecture documents.

ADP-08 freezes **what evidence must exist and pass**. It does not require not-yet-authorized M3 implementation code to have already produced that evidence before architecture freeze.

This owner is `FINAL / FROZEN`. Implementation remains unauthorized until `steps.md` is frozen and `status.md` explicitly authorizes implementation.

## Frozen inputs

Verification derives from:

```text
docs/milestones/M3/contract.md
    M3-OUT-01 .. M3-OUT-08
    M3-AC-01  .. M3-AC-19
    M3-CQG-01 .. M3-CQG-08

docs/milestones/M3/architecture/read-projections.md
    ADP-01 .. ADP-03

docs/milestones/M3/architecture/api.md
    ADP-04 .. ADP-05

docs/milestones/M3/architecture/cli.md
    ADP-06 .. ADP-07

docs/architecture/verification.md
    delivered T0 .. T10 layers, environment and evidence policy
```

# ADP-08 — CLOSED — Verification architecture

## 1. Three verification gates

M3 has three distinct gates.

### Architecture verification-design gate

Before the architecture set may freeze:

```text
every M3-OUT-* has an architecture or preserved AS-IS owner
every M3-AC-* maps to one stable M3-VER-* bundle
every M3-VER-* defines required assertions and verification layers
finite route/cursor/create censuses are exact and closed
negative/non-goal boundaries have deterministic evidence paths
no outcome, AC, architecture requirement or explicit delta is orphaned
```

This gate freezes the evidence design. It does not require M3 software implementation to exist yet.

### Implementation-slice verification gate

After `steps.md` becomes frozen, every implementation slice must:

```text
implement the M3-VER targets assigned to that slice
pass all directly affected deterministic evidence
preserve all affected delivered AS-IS regression evidence
leave no normative skip / xfail / automatic rerun / unexplained flaky target
```

A slice is not complete merely because the changed code path appears functional.

### Final acceptance gate

M3 delivery requires all normative evidence against one identified candidate commit and, where applicable, the artifact built from it:

```text
M3-VER-01 .. M3-VER-19     PASS
GET route census            22 / 22
cursor route census         12 / 12
CLI 201 Location census      8 / 8
required PostgreSQL evidence PASS
schema metadata drift        []
locked build/static gates    PASS
full repository suite        PASS
blocking M3 findings          0
open incompatible reopen      0
complete end-to-end traceability
```

A missing `TEST_DATABASE_URL` makes PostgreSQL-required evidence `BLOCKED`, never `PASS`.

## 2. Evidence states and durability

Stable evidence bundles use these states in candidate evidence records:

```text
DESIGNED
    assertions/layers/ownership frozen by architecture

IMPLEMENTED
    concrete evidence target(s) exist

PASS
    every mandatory target passed on the candidate

FAIL
    at least one mandatory target failed

BLOCKED
    required environment/prerequisite prevented execution
```

Only `PASS` satisfies final acceptance.

Concrete pytest node IDs, exact commands, commit hashes, database/version metadata, durations and test counts belong to implementation/final evidence records, not to this normative architecture.

`skip`, `xfail`, timeout, missing target or automatic rerun never substitutes for a normative PASS.

## 3. Preserved verification layers

M3 reuses the delivered T0–T10 stack.

Material M3 use is:

```text
T1  application/UoW orchestration and forbidden read-certification dependencies
T2  real PostgreSQL persistence, SQL-statement observation, corrupted-carrier fixtures
T3  deterministic PostgreSQL before/after snapshot interleaving evidence
T4  public HTTP behavior, GET/cursor/parent-filter/failure evidence
T5  schema/Alembic lifecycle and metadata-drift evidence
T6  targeted cursor/property algebra where stronger than examples
T8  CLI parser/selector/planner/protocol/interactive/non-interactive evidence
T10 static exact censuses, traceability, imports, forbidden dependencies and non-delta checks
```

Fakes may prove pure orchestration. They do not prove real PostgreSQL, public HTTP or installed-artifact claims.

## 4. Machine-checkable M3 registries

Implementation must provide one machine-checkable M3 traceability registry, conceptually in a dedicated test module or equivalent permanent test-only owner.

It contains exact sets/maps for:

```text
M3_OUTCOMES
    M3-OUT-01 .. M3-OUT-08

M3_ACCEPTANCE_CRITERIA
    M3-AC-01 .. M3-AC-19

M3_EVIDENCE_BUNDLES
    M3-VER-01 .. M3-VER-19

M3_OUTCOME_TO_ACCEPTANCE
M3_ACCEPTANCE_TO_EVIDENCE
M3_EVIDENCE_TO_ARCHITECTURE_OWNER
M3_EVIDENCE_TO_TARGETS

M3_GET_ROUTE_CENSUS
    exact 22 canonical public business GET/read routes

M3_CURSOR_ROUTE_CENSUS
    exact 12 cursor-bearing routes

M3_CLI_201_CENSUS
    exact 8 registered 201 + Location operations
```

Machine checks require exact equality, never a minimum count.

Every mapped concrete target must exist when its implementation slice is complete; no evidence bundle may be empty; no stable M3 identifier may be silently renamed or deleted.

## 5. Stable acceptance-evidence bundles

Every frozen acceptance criterion owns exactly one stable bundle:

```text
M3-AC-01 -> M3-VER-01
M3-AC-02 -> M3-VER-02
M3-AC-03 -> M3-VER-03
M3-AC-04 -> M3-VER-04
M3-AC-05 -> M3-VER-05
M3-AC-06 -> M3-VER-06
M3-AC-07 -> M3-VER-07
M3-AC-08 -> M3-VER-08
M3-AC-09 -> M3-VER-09
M3-AC-10 -> M3-VER-10
M3-AC-11 -> M3-VER-11
M3-AC-12 -> M3-VER-12
M3-AC-13 -> M3-VER-13
M3-AC-14 -> M3-VER-14
M3-AC-15 -> M3-VER-15
M3-AC-16 -> M3-VER-16
M3-AC-17 -> M3-VER-17
M3-AC-18 -> M3-VER-18
M3-AC-19 -> M3-VER-19
```

### M3-VER-01 — Eight-operation create success

Layers: `T8 + T10`.

Required evidence:

```text
all 8 registered 201 operations have one Location template
all 8 canonical response bodies materialize the expected Location
all 8 canonical exact Location responses produce CLI success
all 3 nested response-token templates exercised explicitly
all 5 flat-token templates retained
valid nested-token success never raises and never yields cli_internal_error
```

### M3-VER-02 — Exact Location protocol failures

Layers: `T8 + T10`.

Required evidence:

```text
missing actual Location       -> cli_protocol_error
repeated actual Location      -> cli_protocol_error
mismatching actual Location   -> cli_protocol_error
unresolvable expected token   -> cli_protocol_error
non-materializable token      -> cli_protocol_error
unsupported/malformed registry Location DSL rejected statically
request-key precedence tested independently of response fallback
no Python format/format_map interpretation of dotted tokens
```

### M3-VER-03 — Interactive/non-interactive create truthfulness

Layer: `T8`.

Required evidence:

```text
canonical nested-identity create succeeds non-interactively
canonical nested-identity create succeeds interactively
same parser/execution/protocol semantics in both modes
primary successful exchange remains in structured trace
no hidden post-mutation GET is performed
```

### M3-VER-04 — Twenty-two-route public read compatibility

Layers: `T2 + T4 + T10`.

Required evidence:

```text
exact 22-route census exercised
success DTO field meanings preserved
route-specific filters preserved
canonical ordering preserved
pagination model preserved
no public GET route added or removed
explicit M3 cursor/root-filter deltas are the only intended compatibility changes
```

### M3-VER-05 — Request/path-target failure preservation

Layer: `T4`.

Required evidence:

```text
unknown query carrier -> delivered invalid_request
repeated query carrier -> delivered invalid_request
malformed request carrier -> delivered invalid_request
missing path target -> 404 resource_not_found
existing parent/path target + zero matching members -> successful empty page where defined
optional owner relation preserves target 404 versus successful null
```

### M3-VER-06 — Read semantic authority and mutation preservation

Layers: `T1 + T2 + T4 + T10`.

This bundle must prove both sides of the M3 responsibility boundary.

Read-side evidence:

```text
all 22 canonical GET targets have no mutation-semantic validator prerequisite
no read-only dependency load exists solely to recertify persisted semantics
representable persisted state that would fail removed mutation-style recertification remains readable
```

Runtime fixtures must cover representative removed certification families, including as applicable:

```text
default publication recertification
Object/property schema recertification
ownership slot semantic recertification
Relationship definition/schema/topology recertification
lifecycle transition recertification
```

Write-side evidence:

```text
mutation candidate/transition semantic validation remains active
M3 does not weaken a mutation validator merely to make reads succeed
existing affected mutation semantic-regression targets remain green
```

Static evidence across all 22 routes plus representative runtime family evidence is required; one isolated corruption fixture is not sufficient as the complete proof.

### M3-VER-07 — Materially undecodable carrier boundary

Layers: `T2 + T4`.

Required evidence uses persisted carriers that cannot be converted into mandatory public typed state, for example:

```text
missing required historical snapshot field
unparseable UUID in a required historical JSON field
wrong scalar/object carrier for required Relationship factual state
other required projection carrier that cannot be materialized
```

Result:

```text
bounded 500 internal_error
no repair
no fabricated default
no silent item omission
```

### M3-VER-08 — Trusted lifecycle historical decoding

Layers: `T2 + T4`.

Positive evidence must include structurally persisted and DTO-decodable historical events that violate transition certifications no longer owned by GET, including representative intrinsic and Relationship families.

Examples include:

```text
RENAME whose before/after pair would not pass current rename transition certification
DATA_CHANGE without current changedness certification
SCHEMA_CHANGE without version-increase recertification
Relationship DATA_CHANGE / SCHEMA_CHANGE analogous transition surprises
```

These remain readable when representationally decodable.

Negative materially-undecodable cases are owned by `M3-VER-07`.

Global and Object-scoped lifecycle filters/DTOs and `(occurred_at,id) DESC` ordering remain unchanged.

### M3-VER-09 — Complete twelve-route cursor binding

Layers: `T4 + T6 + T10`.

A machine-checkable route matrix supplies, for all 12 routes:

```text
codec route identity
membership-affecting path target(s)
membership-affecting filters
semantic presence bits
complete position key shape
canonical order
```

For every route:

```text
same semantic identity -> continuation accepted
same identity + changed limit only -> accepted
changed membership filter -> invalid_cursor
changed required path target -> invalid_cursor
incompatible route identity -> invalid_cursor
malformed/wrong-length/wrong-type key -> invalid_cursor
```

### M3-VER-10 — Components cross-parent cursor rejection

Layer: `T4`.

Explicit regression:

```text
cursor issued for parent A + slot filter X
reused on parent B + same slot filter X
    -> 400 invalid_cursor
```

A same-parent continuation remains valid.

### M3-VER-11 — Object Relationship cross-object cursor rejection

Layer: `T4`.

Explicit regression:

```text
cursor issued for Object A + same Relationship filters
reused for Object B
    -> 400 invalid_cursor
```

A same-Object continuation remains valid.

### M3-VER-12 — Cursor keyset completeness

Layers: `T2 + T4`.

Required evidence performs true multipage traversal over datasets that exercise complete ordering tuples and verifies no cursor-induced omission or duplication.

Material compound-key cases include:

```text
Object Relationships
    (relationship_id, destination_object_id, name)

lifecycle
    (occurred_at, id) DESC
```

All remaining route keys must also match the frozen ADP-04 matrix exactly.

Encode/decode unit tests alone do not prove this bundle.

### M3-VER-13 — Lifecycle route-scope cursor distinction

Layer: `T4`.

Required evidence:

```text
global lifecycle cursor on Object-scoped route -> invalid_cursor
Object-scoped A cursor on Object-scoped B -> invalid_cursor
existing lifecycle filter changes -> invalid_cursor
same scope/filter identity -> continuation accepted
```

### M3-VER-14 — ObjectTemplate HTTP parent tri-state

Layer: `T4`.

Required evidence:

```text
parent_template_id omitted -> no parent predicate
valid UUID -> direct children only
exact lowercase null -> roots only
empty -> 400 invalid_request
uppercase/special sentinel -> 400 invalid_request
malformed UUID -> 400 invalid_request
repeated parent_template_id -> 400 invalid_request
parent_filter_set never appears as public query/DTO surface
```

### M3-VER-15 — ObjectTemplate CLI parent tri-state

Layer: `T8`.

Required evidence:

```text
omitted -> no selector lookup, no query pair
UUID -> exact UUID query pair
human ObjectTemplate selector -> normal bounded discovery -> resolved UUID query pair
explicit null -> parsed None -> zero selector-discovery GET -> literal parent_template_id=null query pair
explicit null on non-nullable parameter -> cli_invalid_parameter
nullable BODY null remains JSON null
PATH None remains invalid/impossible
no global _wire_string(None) behavior
interactive/non-interactive carrier equivalence
```

### M3-VER-16 — Parent-filter cursor identity

Layer: `T4`.

Required evidence:

```text
omitted cursor rejected under root-only
root-only cursor rejected under omitted
root-only cursor continues root-only page successfully
exact parent A cursor rejected under exact parent B
exact-parent/root-only identities remain mutually incompatible
```

The internal `parent_filter_set` distinction is verified indirectly through behavior and may be inspected in lower-layer unit evidence without becoming public API.

### M3-VER-17 — No schema/migration/dependency drift

Layers: `T5 + T10`.

Required evidence:

```text
no new Alembic revision
same delivered one-root/head migration graph
live PostgreSQL schema remains the delivered authoritative schema
compare_metadata == []
no new runtime dependency
uv lock --check PASS
runtime lockfile unchanged by M3 unless contract is formally reopened
no M3 table/index/constraint introduced
```

### M3-VER-18 — Complete outcome traceability

Layer: `T10`.

Required machine-checkable closure:

```text
8 / 8 M3 outcomes registered
19 / 19 acceptance criteria registered
19 / 19 evidence bundles registered
every OUT -> one or more ACs
every AC -> exactly one VER bundle
every VER -> architecture owner(s)
every VER -> non-empty concrete target set once implemented
22 / 22 GET routes represented
12 / 12 cursor routes represented
8 / 8 CLI 201 operations represented
no stale TODO/TBD/open semantic owner
no incompatible formal reopen
```

`M3-CQG-01 .. M3-CQG-08` must also be statically checked as represented by the frozen contract/architecture/governance state; they are quality-gate checks rather than additional VER bundle identities.

### M3-VER-19 — Single-request committed projection coherence

Layers: `T2 + T3 + T10`.

#### 22/22 one-business-statement evidence

Each canonical public GET/read invocation is measured independently against real PostgreSQL and must issue exactly one authoritative business SQL statement for its complete projection.

The measurement window begins immediately before the target business read path and ends when the business projection has been obtained.

The following do not count when performed outside the measured target invocation:

```text
fixture/setup SQL
database cleanup
connection/dialect warmup
driver transaction-control not expressed as an application business statement
```

Any application/business SELECT or equivalent statement issued during the target read counts. Helper statements are not exempt merely because they are internal.

Static evidence also proves no target public GET depends on `coherent_read()`.

#### Deterministic snapshot evidence

At least one representative multi-fragment projection family must have real-PostgreSQL deterministic interleaving evidence showing:

```text
reader paused before authoritative execute
writer commits
reader executes
    -> complete AFTER projection

reader authoritative statement completes
writer commits before application returns projection
    -> complete BEFORE projection
```

The harness may observe/pause named phases but must not alter SQL, isolation, production locks, candidate data or production path selection.

This representative concurrency scenario supplements — and does not replace — the 22/22 statement-count proof.

M3 does not promise repeatable membership across separate requests/pages.

## 6. SQL-statement observation rule

The M3 one-statement claim is an architecture realization obligation, not a public wire field. It therefore requires direct deterministic SQL observation.

A test that only sees `200`, correct DTO shape or absence of `coherent_read()` does not prove the claim.

The collector/hook may be implementation-local but must observe the actual statements emitted on the real PostgreSQL connection used by the target invocation and must not change transaction semantics.

Each of the exact 22 route identities must have an explicit statement-count disposition in the evidence registry.

## 7. Read/write semantic-boundary rule

Verification must never prove read simplification by deleting or bypassing write validation.

Required paired evidence is:

```text
representable persisted semantic surprise
    -> public GET succeeds

corresponding semantically invalid new mutation candidate/transition
    -> existing mutation validation still rejects/classifies it
```

The exact paired fixtures may differ by family, but evidence must cover the material validator families removed from reads.

## 8. Cursor verification rule

The cursor matrix is one closed finite registry, not twelve unrelated hand-maintained tests.

Generated/shared coverage is encouraged for the common invariants, but explicit M3 regression targets remain mandatory for:

```text
components parent A/B
Object Relationships Object A/B
lifecycle global/Object scope
ObjectTemplate omitted/root/exact-parent states
```

Limit changes must be positively exercised because exclusion of `limit` from semantic identity is a required behavior, not merely an absent field assertion.

## 9. CLI verification rule

The eight `201 Created` operations form one exact registry-derived matrix.

Static evidence verifies:

```text
exact eight-operation census
exact one Location template per 201 operation
Location token DSL well-formedness
no unsupported Python-format token semantics
```

Runtime controlled-transport evidence verifies canonical successes and protocol failures. At least one affected nested create must be exercised through both interactive and non-interactive execution boundaries.

For `parent_template_id=null`, the execution ledger must prove zero selector lookup attributable to that parameter and the primary request trace must contain the literal lowercase query value.

## 10. Schema/dependency non-delta rule

M3 adds no schema, migration or runtime dependency capability.

Verification therefore treats any unexplained change in these surfaces as a blocking contract contradiction, not as an incidental implementation choice.

The final candidate evidence must identify the baseline and prove the non-delta through migration inventory, metadata comparison, dependency/lock checks and repository traceability.

## 11. Canonical project gates

M3 preserves the delivered project gates conceptually:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
required focused M3 evidence selections
required real-PostgreSQL M3 evidence selections
full repository pytest suite
```

The final evidence record stores the exact commands, environment and results.

No normative target may be silently skipped because `TEST_DATABASE_URL` is absent.

## 12. Final acceptance invariants

M3 final acceptance passes only when:

```text
M3-VER-01 .. M3-VER-19       PASS
normative skip / xfail / rerun 0 / 0 / 0
GET route evidence             22 / 22
cursor route evidence          12 / 12
CLI create Location evidence    8 / 8
schema compare_metadata         []
new Alembic revisions            0
new runtime dependencies         0
runtime lockfile M3 drift        0
required PostgreSQL evidence   PASS
build / Ruff / Pyright         PASS
full repository suite          PASS
blocking M3 findings             0
open incompatible reopen         0
contract -> architecture -> steps -> implementation -> evidence traceability COMPLETE
```

A reviewed third-party warning may be censused under the delivered verification policy; an unexplained new project warning remains a finding.

## 13. Architecture-freeze publication

ADP-08 is **CLOSED** because all M3 evidence obligations are designed and traceable.

The dedicated architecture consistency review passed with zero open findings and no contract reopen requirement. The project owner explicitly approved architecture freeze after that PASS.

The architecture set is therefore `FINAL / FROZEN`. This publication changes authority/status only; executed `M3-VER-*` evidence remains pending by governance and is required during implementation slices and final acceptance.

Architecture freeze does not authorize software implementation. `steps.md` remains the next independent frozen gate.

# ADP status

```text
ADP-08  CLOSED
M3 architecture design points  8 / 8 CLOSED
```

This owner is `FINAL / FROZEN`. Software implementation remains **NOT AUTHORIZED** until frozen `steps.md` and explicit `status.md` authorization.