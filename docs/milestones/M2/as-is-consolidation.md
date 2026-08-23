# M2 — AS-IS consolidation gate

**Status:** FINAL — reviewer-owned post-implementation closure specification.

## Purpose and authority boundary

This document owns the **procedure, scope and acceptance conditions** for the
post-implementation consolidation of the accepted M2 result into the current
AS-IS under `docs/architecture/`.

It does not define product semantics and cannot override:

```text
docs/architecture/
    current delivered AS-IS at the start of consolidation

docs/milestones/M2/contract.md
    FINAL / FROZEN milestone contract

docs/milestones/M2/architecture/
    FINAL / FROZEN M2 TO-BE owners

docs/general/technology_baseline.md
    ratified project-wide technology decisions
```

The accepted implementation, schema, tests, generated surfaces and final M2-S09
evidence are cross-check evidence. They do not become independent semantic
authority.

If the current AS-IS, the frozen M2 owners and the accepted implementation do not
resolve to one coherent current-state meaning, the affected consolidation point
enters `STOP`. The consolidator must report the contradiction and must not choose
the newest document, the current code or the most convenient interpretation.

## Consolidation objective

The output is a self-contained, history-light and state-heavy current
architecture corpus.

A future milestone or fix must be able to answer:

```text
what NETAUTO is
which states are valid
which commands and reads exist
which persistence and concurrency guarantees hold
which runtime, Health, CLI and deployment boundaries are supported
which verification obligations preserve those guarantees
```

by reading `docs/architecture/` and the applicable technology baseline, without
reconstructing M1 or M2.

The consolidation is **not**:

```text
a change log
a before/after comparison
a copy of the M2 TO-BE documents
a summary of implementation commits
a final-acceptance report
a catalogue of test counts or candidate hashes
```

## Non-negotiable current-state rule

Semantic sections use present-tense current-state language.

Invalid consolidation style:

```text
M1 provided X and M2 added Y.
Previously the Definition was unversioned.
The new API now exposes ...
This behavior was introduced by M2-S03.
```

Required style:

```text
A RelationshipDefinition is a stable aggregate with ...
A RelationshipDefinitionVersion has ...
The API exposes ...
The persistence model contains ...
```

Cycle provenance may appear only in the concise provenance section of
`docs/architecture/README.md`. It must not leak into the semantic explanation of
any owning document.

## Gate lifecycle

```text
READY
    reviewer has authorized consolidation
    docs/architecture remains the pre-consolidation AS-IS

IN PROGRESS
    consolidator is deriving and writing the current-state corpus

CANDIDATE READY FOR REVIEW
    one complete consolidation candidate is pushed
    preliminary consistency and verification gates are green

REVIEW CHANGES REQUIRED
    reviewer has rejected the consolidation candidate
    corrections remain inside this gate

COMPLETED
    reviewer has accepted the current-state corpus
    the separate consistency-closure gate may start
```

The coding agent may publish only `CANDIDATE READY FOR REVIEW`. It may not mark
this gate `COMPLETED`, may not mark M2 `DELIVERED`, and may not merge.

## Source corpus to read in full

The consolidator must read, dependency-first:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

all files under docs/architecture/

docs/milestones/M2/contract.md
docs/milestones/M2/architecture/README.md
all normative files under docs/milestones/M2/architecture/
docs/milestones/M2/linux-operating-baseline.md
docs/milestones/M2/steps.md
docs/milestones/M2/status.md
docs/milestones/M2/acceptance.md

the accepted schema, migration graph, public API/CLI registries,
settings model, package metadata and permanent verification registries
```

Historical M2 WIP material is not semantic authority and is not a source to copy
into the current AS-IS.

## Target corpus and ownership map

The expected current architecture corpus is:

| Area | Current owner / projection | Consolidation action |
|---|---|---|
| Set entry point and authority map | `docs/architecture/README.md` | Rewrite the map and current scope; add concise consolidated-cycle provenance only. |
| DataType | `docs/architecture/datatype.md` | Audit against the accepted state; modify only where a current cross-reference or shared invariant is no longer exact. |
| ObjectTemplate | `docs/architecture/objecttemplate.md` | Audit against the accepted state; modify only where a current cross-reference or shared invariant is no longer exact. |
| Object | `docs/architecture/object.md` | Audit against the accepted state; modify only where a current cross-reference or shared invariant is no longer exact. |
| Relationship model and factual semantics | `docs/architecture/relationship.md` | Rewrite as the complete current owner, including versioned Definition semantics and factual Relationship state. |
| Persistence and migration authority | `docs/architecture/persistence.md` | Rewrite as the exact current fifteen-table model and current one-root Alembic baseline. |
| Semantic concurrency matrix | `docs/architecture/concurrency-matrix.md` | Replace the old census with the exact current mutation matrix and safety predicates. |
| PostgreSQL/UoW concurrency realization | `docs/architecture/concurrency.md` | Rewrite around the current centralized lock planner, gates, ordering and restart policy. |
| Public HTTP API | `docs/architecture/api.md` | Rewrite around the exact current business and Health surfaces, DTOs, failures, reads and pagination. |
| Core Health | `docs/architecture/health.md` | Add a current semantic and runtime Health owner. |
| Official CLI | `docs/architecture/cli.md` | Add the current non-interactive and REPL client contract. |
| Runtime and deployment | `docs/architecture/runtime-deployment.md` | Add the current settings, packaging, startup guard, trust and deployment owner. |
| Linux operating projection | `docs/architecture/linux-operating-baseline.md` | Add a current operator-facing procedure derived from the accepted runtime contract. It is a projection; `runtime-deployment.md` remains the semantic owner. |
| Verification policy | `docs/architecture/verification.md` | Rewrite the durable current T0–T10 policy and evidence obligations. |
| Canonical concurrency verification | `docs/architecture/verification-concurrency-registry.md` | Rewrite the exact current stable scenario/predicate registry and recipes. |

`docs/milestones/M2/architecture/provenance.md` remains historical M2 material. It
must not be copied into `docs/architecture/` as a current semantic owner.

No additional AS-IS file may be introduced unless the current owner map cannot
remain coherent without it. Such a need is a reviewer finding, not an automatic
permission to split ownership.

## Durable identifiers and historical identifiers

The current AS-IS preserves identifiers that are needed to evolve the system
safely across future cycles, including:

```text
semantic invariant identifiers where already authoritative
canonical mutation names
canonical concurrency scenario IDs
safety-predicate codes
public error codes
route, setting, schema-object and migration identifiers
```

The following remain in the historical M2 record and must not become current
architecture identifiers:

```text
M2-OUT-*
M2-AC-*
M2-VER-*
M2-Snn
candidate SHA values
commit SHA values
exact pass counts and command durations
review-fix identifiers
```

A milestone-specific identifier may appear in `docs/architecture/` only when a
frozen owner explicitly declares it durable beyond the milestone. Mere use in a
traceability test is not sufficient.

## Semantic coverage requirements

### Relationship

The current Relationship owner must describe one coherent model containing at
least:

```text
stable RelationshipDefinition identity and topology
Resolution membership and identity
versioned RelationshipDefinitionVersion lifecycle
complete version declaration state and revision semantics
default-version behavior and capability derivation
property declarations, ordering, exact DataTypeVersion pinning and history
factual Relationship stable identity
exact persisted RelationshipDefinitionVersion pin
canonical current property state
complete deterministic endpoint closure
CREATE, DATA_CHANGE, SCHEMA_CHANGE and DELETE
no-op versus real-change semantics
atomic lifecycle-event sets
read projections and corruption boundaries
delete blockers and reference lifetime
absence of autonomous Resolution CRUD
```

The document must not explain which subset came from M1 or M2.

### Persistence and Alembic

The current persistence owner must describe the physical system that exists now:

```text
exact fifteen-table inventory
current PK / UNIQUE / FK / CHECK / index authority
current CASCADE / RESTRICT boundaries
canonical JSONB and scalar representations
Relationship current property and exact-pin storage
Relationship lifecycle/event representation
one NETAUTO UoW per semantic mutation
one shipped Alembic base/head/current authority: 0001_m2_kernel
zero application, CLI or startup auto-migration
exact startup revision equality before serving
```

It must not describe a thirteen-table predecessor, a migration from an M1 head,
or “new M2 tables”. Historical migration evolution belongs only to cycle history.

### Semantic concurrency

The current semantic matrix and realization must agree on:

```text
41 mutation primitives
15 family blocks
861 unordered interaction cells
complete current classification
21 safety predicates, including VH and RS
one complete pre-DML lock plan per supported mutation
advisory-gate-first acquisition
canonical row-class and intra-class ordering
no normal row-lock upgrades
model-root delete serialization
existing-owner target-before-owner ordering
child-FK target-before-DML ordering
differential declaration replacement
CREATE_NEXT lifetime holds
bounded whole-UoW restart for approved causes only
no automatic retry of SQLSTATE 40P01
supported wait-for graph acyclic by construction
```

The semantic matrix owns what must remain true. The PostgreSQL document owns how
that property is realized. Neither may redefine the other.

### Public API

The current API owner must expose one exact, self-contained surface:

```text
/api/v1/core business namespace
63 business operations
GET /health/core as the sole operational HTTP route
strict operation-specific request DTOs
omission distinct from explicit null/input
exact selectors and lineage/version identities
current RelationshipDefinitionVersion and Relationship property projections
finite public failure catalogue with bounded safe details
keyset pagination and route-specific ordering
exact success status, body and Location behavior
absence of generic PUT/PATCH/action DSL and other forbidden surfaces
```

The route inventory must be written as a current inventory, never as “52 old + 11
new”.

### Health

The Health owner must describe:

```text
GET /health/core
same worker engine/pool used by business work
exact bounded SELECT 1 probe
fixed full-probe deadline
safe 200/503 response contract
startup revision guard as a separate pre-serving concern
no migration, repair, auth, schema-detail or secret leakage
process remains HTTP-capable when PostgreSQL later becomes unavailable
```

### CLI

The CLI owner must describe the current official client:

```text
one static registry covering all 63 business operations
8 local commands
non-interactive and asynchronous REPL contracts
HTTP-only execution boundary
selector resolution and exact persisted identity behavior
one persistent client per REPL session
fresh command-local ledger/memo state
FORMATTED and JSON modes
bounded HTTP trace and failure rendering
GET-only presentation enrichment with identity validation
verified HTTPS and no insecure bypass
no credential or endpoint persistence
process-local command history only
Ctrl-C / Ctrl-D / Ctrl-R behavior
stdout, stderr and exit-status contract
```

It must not expose internal domain or persistence mechanisms as client
responsibility.

### Runtime, distribution and Linux operation

The runtime owner and operator projection must describe:

```text
complete NETAUTO Settings inventory and validation boundaries
explicit secret-directory composition
one engine/pool per worker and orderly disposal
one wheel containing server, CLI, migration graph and runtime metadata
one embedded exact runtime lock derived from uv.lock
installed package-resource Alembic discovery and unique head
pre-serving exact revision guard
no installation/startup/CLI automatic migration
manual Linux install, explicit migration, start, readiness, stop and restart
trusted-boundary HTTP with external TLS termination responsibility
no bundled daemon, process manager, container, firewall or backup product
```

The operator guide must be actionable for the current release and must remove
phrases such as “M2”, “first baseline”, “candidate” and “to be implemented”.
Candidate hashes and final-gate counts remain in `acceptance.md`, not in the
current operating guide.

### Verification

The current verification owners must preserve durable obligations rather than
milestone evidence bookkeeping:

```text
T0 through T10
real-PostgreSQL requirement for persistence/concurrency claims
installed-wheel T9 isolation
static/negative-surface T10 boundaries
exact current route/schema/CLI/settings inventories
83 canonical concurrency scenarios
21 safety predicates
deterministic orchestration recipes
zero normative SKIP/XFAIL/RERUN acceptance
schema drift = []
reproducible build and locked-environment gates
```

M2 acceptance bundles and candidate command ledgers remain historical evidence
and are not copied into the AS-IS.

## Current-state writing rules

Every owning document must:

- state its purpose and authority boundary;
- use present tense;
- define canonical entities, states, invariants, commands and failures directly;
- contain exact finite inventories where the surface is closed;
- distinguish semantic state from persistence and wire representation;
- reference another current owner rather than duplicating its decision;
- contain no unresolved `TODO`, `TBD`, `FIXME`, open point or design placeholder;
- contain no requirement to consult M1/M2 documents to understand current
  behavior;
- avoid implementation-module tours unless a concrete entrypoint or package
  boundary is itself architectural;
- avoid candidate hashes, test durations, review findings and delivery evidence.

The words `M1` and `M2` are allowed only in the concise provenance table and in
links that identify historical cycle records. They are not allowed in semantic
sections.

The following forms require explicit review and are normally invalid outside a
provenance/update-discipline paragraph:

```text
previously
new / newly
added / introduced
changed from
preserved from
legacy
before / after M2
during M2
M2 delta
target / TO-BE
candidate
to be implemented
```

A blind global replacement is forbidden. The consolidator must rewrite the
meaning as current state.

## Cross-document consistency rules

The consolidation candidate must have one owner for every decision.

At minimum, verify:

```text
README map == actual current AS-IS file inventory
API operation inventory == current public registry/OpenAPI evidence
CLI remote inventory == business API inventory
Health route appears once and is not counted as a business command
persistence table/key/index inventory == accepted metadata/migration evidence
concurrency mutation census == semantic matrix == lock-plan registry
scenario IDs and predicates == canonical verification registry
settings inventory == current Settings model
startup expected revision == unique shipped Alembic head
operator procedure == runtime/deployment owner
non-goals == implemented negative surface
all internal links resolve inside the current AS-IS or technology baseline
```

Cross-cutting consequences may be repeated only as references or concise
constraints. Repetition must not create a second normative definition.

## Allowed repository delta

The consolidation candidate may modify only:

```text
docs/architecture/*.md
docs/milestones/M2/status.md
```

The new current files explicitly allowed are:

```text
docs/architecture/health.md
docs/architecture/cli.md
docs/architecture/runtime-deployment.md
docs/architecture/linux-operating-baseline.md
```

Do not modify:

```text
src/netauto/
tests/
pyproject.toml
uv.lock
src/netauto/release/runtime.pylock.toml
schema or migrations
README.md root
AGENTS.md
docs/general/
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/
docs/milestones/M2/steps.md
docs/milestones/M2/acceptance.md
docs/milestones/M2/evidence/
```

A need to modify code, schema, tests, frozen M2 authority or project-wide
technology is a `STOP`, not consolidation scope.

## Preliminary consistency and verification gate

Before publishing a candidate, execute at least:

```text
internal Markdown link/reference audit
exact target-file inventory audit
temporal/delta wording audit with explicit provenance allowlist
milestone-ID leakage audit
normative placeholder audit
API / CLI / Health inventory cross-check
schema / migration / metadata cross-check
settings / runtime / operator-guide cross-check
concurrency matrix / lock plan / scenario / predicate cross-check
```

Then execute the repository gates on the consolidation tree:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q

traceability and documentation-policy tests
schema / migration / settings / API / CLI / Health focused tests
PostgreSQL / concurrency suite
non-PostgreSQL suite
full repository suite
```

Required outcome:

```text
skip / xfail / rerun             0 / 0 / 0
supported-path 40P01             0
unexpected 40001                 0
negative-control SQLSTATE        exact expected census
compare_metadata                 []
new unexplained warnings         0
artifact identity                unchanged
```

The compact accepted evidence JSON may be excluded from formatter-only handling
when required to preserve its stable byte representation. Ruff lint still checks
the repository according to project configuration.

## Candidate publication

If any semantic contradiction or gate failure occurs:

```text
AS-IS consolidation    IN PROGRESS
consistency closure    BLOCKED
M2                     NOT DELIVERED
```

Do not weaken the current AS-IS, frozen M2 owners or tests to obtain a green
result.

When all consolidation and preliminary gates pass:

1. update `docs/milestones/M2/status.md` to:

   ```text
   AS-IS consolidation    CANDIDATE READY FOR REVIEW
   consistency closure    BLOCKED
   M2                     NOT DELIVERED
   ```

2. commit with a bounded split such as:

   ```text
   docs(architecture): consolidate current AS-IS
   docs(m2): publish AS-IS consolidation candidate
   ```

3. push only to `M2`;
4. verify `HEAD == origin/M2 == remote M2`, ahead/behind `0/0`, clean worktree;
5. rerun the relevant documentation, traceability, PostgreSQL/non-PostgreSQL and
   full-suite gates on the exact remote HEAD.

No PR, workflow, tag, Release, artifact publication, delivery declaration or
merge is part of this gate.

## Candidate handoff

Report only verified facts:

```text
starting and final SHA
changed / added AS-IS files
source-to-target ownership map
areas audited but intentionally unchanged
current-state wording audit
milestone-ID and temporal-language audit
exact finite inventories
link/reference audit
focused and full verification
artifact invariance
open contradictions or findings
remote synchronization and worktree state
```

The only implementer handoff is:

```text
AS-IS consolidation    CANDIDATE READY FOR REVIEW
consistency closure    BLOCKED
M2                     NOT DELIVERED
```

After reviewer acceptance, a separate consistency-closure gate performs an
independent whole-corpus sweep. Only after both gates are reviewer-owned
`COMPLETED` may M2 become `DELIVERED`.