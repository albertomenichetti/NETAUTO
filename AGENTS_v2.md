# NETAUTO — Coding Agent Operating Contract

This file defines repository-level operating rules for coding agents.

It is an **operational contract**, not a semantic architecture specification. It tells the agent how to establish context, which documentation to read, how to use each authority, when implementation is allowed, when work must stop, and what evidence must be returned for review.

It must not duplicate, reinterpret or silently override the normative project documentation.

## 1. Start from the repository README

Before any repository work, read the root `README.md`.

The root README is the mandatory **operational entry point** and must identify, directly or through explicit links:

```text
current delivered baseline
active cycle, if any
active branch
current phase
active slice or task
current operational status
active execution aid, when one exists
immediate next action
```

Use the README to determine **where the project currently is**. Then verify the detailed state against the active cycle's `status.md`, `steps.md` and other owning documents.

The README is a navigator and current-state entry point; it is **not** a semantic authority. It cannot override `docs/architecture/`, an active cycle contract, frozen architecture, frozen defect scope or the technology baseline.

If the README does not identify the current phase clearly, points to missing or incompatible cycle documents, or disagrees with the active branch/status, stop before modifying code and report the documentation/state gap.

Do not infer the current phase from branch name, commit recency, chat history, the last prompt or agent memory alone.

## 2. Establish the exact work context

Before modifying code, establish all of the following:

```text
current Git branch
active cycle type: milestone Mx or fix Fx-y
active cycle identifier
current phase
active slice identifier: Mx-Snn or Fx-y-Snn
active task / execution aid
publication expectation: local only, commit, push, or PR
```

Code-base changes are permitted only inside an active milestone or fix cycle as defined by `docs/general/linee_guida_progetto.md`.

The branch, cycle and slice must agree. If they do not, stop and report the mismatch rather than guessing the intended target.

Typical phases include:

```text
DESIGN
IMPLEMENTATION
REVIEW / REVIEW FIX
FINAL ACCEPTANCE or FINAL REGRESSION
AS-IS CONSOLIDATION
DELIVERED / CLOSED
NO ACTIVE CYCLE
```

Normal production implementation is allowed only when the active cycle and slice are ready for implementation or review-fix work.

- During `DESIGN`, do not implement the behavior being designed.
- During `FINAL ACCEPTANCE` / `FINAL REGRESSION`, do not introduce unrelated production changes; a discovered defect must be routed through the appropriate review-fix or reopen process.
- During `AS-IS CONSOLIDATION`, change only the documentation/artifacts explicitly owned by consolidation.
- When no active code cycle exists, do not modify the code-base.

An active prompt is an execution aid. It narrows the assigned work but never overrides the normative authorities.

## 3. Documentation authority map

Repository documentation is authoritative. Code, tests, Git history, chat, reports and memory are evidence or navigation aids; they do not create semantic authority by themselves.

Use the documentation sources as follows.

### `README.md`

Operational entry point for the current repository state. Use it to identify the active cycle, phase, slice and next action.

### `AGENTS.md`

Coding-agent operating rules. It governs how the agent works, not what the domain means.

### `docs/general/linee_guida_progetto.md`

Project governance authority:

- milestone and fix lifecycle;
- documentation roles;
- freeze/reopen/propagation rules;
- reviewer ownership;
- slice naming and completion discipline;
- final gates and cycle closure.

### `docs/architecture/`

Authoritative **current delivered AS-IS**.

Use `docs/architecture/README.md` as the current architecture entry point and authority map. Read every owning document on which the task depends.

Every assumption declared unchanged by an active cycle must be verifiable here.

### `docs/milestones/<Mx>/`

During an active milestone, this directory owns the milestone's normative TO-BE and execution record:

```text
contract.md
    -> scope, non-goals and acceptance criteria

architecture/README.md
    -> architecture-set status, authority map and open/reopen state

architecture/*.md
    -> owning TO-BE semantic and technical decisions

steps.md
    -> frozen implementation decomposition and traceability

status.md
    -> current operational state

acceptance.md, when present
    -> durable final-gate evidence

wip/
    -> temporary non-normative execution aids
```

A milestone may differ from `docs/architecture/` only where the difference is an explicit, contract-derived TO-BE decision. Unchanged behavior continues to derive from the current AS-IS.

### `docs/fixes/<Fx-y>/`

During an active fix, this directory owns the corrective scope and execution record:

```text
defects.md
    -> frozen defect identities, reproduction evidence,
       violated authorities and correction design

architecture/README.md + architecture/*.md, when present
    -> frozen correction-design set for an architecture defect

steps.md
    -> frozen corrective implementation decomposition

status.md
    -> current operational state

wip/
    -> temporary non-normative execution aids
```

A fix corrects behavior already owed by the delivered baseline. It must not introduce a new capability, intentional public-contract change or new product semantics through the corrective path.

### `docs/general/technology_baseline.md`

Project-wide implementation technology authority. Only explicitly ratified `STACK-*` decisions are authoritative while the document remains DRAFT.

Technology choices implement semantic contracts; they cannot reinterpret them.

### Code, tests, schema, generated OpenAPI and Git history

These are implementation/evidence sources. Use them to inspect the current realization, reproduce defects and verify behavior.

They do not override the normative documentation. A conflict between implementation/evidence and authority is a finding to classify, not permission to choose the implementation behavior.

### Precedence and contradiction rule

A lower-level execution document cannot override an owning semantic authority:

```text
prompt / wip aid
    cannot override steps, contract, defects or frozen architecture

steps.md
    cannot override contract, defects or architecture

technology choice
    cannot reinterpret semantic architecture

current code/test behavior
    cannot silently redefine documentation
```

If normative sources conflict, do not select the newest, most convenient or last-read document. Stop the affected work and report an architecture/documentation defect.

## 4. Mandatory pre-flight before implementation

Before implementing or modifying behavior, perform a dependency-driven repository re-read. Do not rely on memory.

### Common checks

Confirm that:

- the README, branch, active cycle, phase and slice agree;
- the active task belongs to the current slice;
- the current delivered assumptions used by the task are verifiable in `docs/architecture/`;
- the owning domain/application/API/persistence/concurrency documents are identified;
- relevant invariants, failure semantics and acceptance/defect requirements are identified;
- required verification layers and concrete regression/concurrency obligations are identified;
- all needed `STACK-*` choices are ratified;
- no contradiction, stale-open marker or explicit reopen affects the task;
- no prompt instruction exceeds or contradicts its frozen scope.

### Milestone checks

For milestone implementation, confirm at minimum:

```text
contract.md
    FINAL / FROZEN

architecture/README.md
    architecture set FROZEN
    no relevant open design point

steps.md
    FINAL / FROZEN
    active slice defined

status.md
    active slice READY / IN PROGRESS / REVIEW CHANGES REQUIRED
    as appropriate to the assigned work
```

Read the current AS-IS plus every milestone architecture document that owns an explicit TO-BE change or dependency of the slice.

### Fix checks

For fix implementation, confirm at minimum:

```text
defects.md
    FROZEN
    defect IDs assigned to the slice
    deterministic reproduction evidence defined
    violated authority and expected correction identified

architecture/README.md
    FROZEN when the fix has correction architecture

steps.md
    FROZEN
    active slice defined

status.md
    active slice READY / IN PROGRESS / REVIEW CHANGES REQUIRED
    as appropriate to the assigned work
```

A reproducible defect must not reach implementation with only a vague symptom description.

### Concurrency pre-flight

When a task adds or changes a mutation or concurrency-sensitive guarantee, verify before coding that:

- the mutation is represented in `docs/architecture/concurrency-matrix.md` or in the active cycle's frozen TO-BE equivalent;
- its scoped interactions with existing mutations have been analyzed semantically;
- the required safety predicate and allowed outcomes are defined;
- the PostgreSQL/UoW realization is defined;
- deterministic real-PostgreSQL evidence is identified in `docs/architecture/verification-concurrency-registry.md` or in the active cycle's frozen extension.

Do not add an isolated lock, constraint or retry and call concurrency design complete without this chain.

If any mandatory pre-flight check fails, stop before implementing the affected behavior.

## 5. Implementation boundaries

Implementation realizes frozen decisions. It does not make new semantic decisions.

Do not resolve ambiguity by:

- inventing a domain rule;
- broadening or weakening a public contract;
- changing transaction boundaries, lock strength or retry semantics;
- introducing a new persistence representation;
- selecting an unratified dependency/framework;
- weakening a verification requirement;
- adding speculative abstractions for future capabilities;
- resurrecting removed historical code or compatibility layers as an implicit baseline.

Prefer the smallest implementation that completely realizes the assigned contract. Vertical completeness is preferred over partial cross-layer scaffolding.

Local implementation decomposition remains free where it does not alter frozen semantics, guarantees, boundaries or verification authorities. Module/helper/fixture/test-file organization is not an architecture reopen by itself.

### Current layer and execution boundaries

Re-check the owning ratified `STACK-*` decisions, but preserve at least these current boundaries:

- pure domain logic is ordinary synchronous Python with no hidden I/O;
- I/O-bearing application/infrastructure operations are asynchronous;
- FastAPI and Pydantic belong to the HTTP/transport boundary;
- domain/application semantics do not depend on HTTP exceptions/status codes;
- SQLAlchemy Core and Psycopg belong to persistence; SQLAlchemy ORM/lazy-loading/ORM-owned UoW are not kernel authorities;
- one semantic Unit of Work owns one explicit PostgreSQL connection/transaction and its commit/rollback boundary;
- repositories do not independently commit;
- I/O remains explicit in the call graph;
- composition is explicit Python wiring; FastAPI `Depends()` is not the kernel composition container;
- process-local locks, mutable globals or caches never become cross-process correctness authorities;
- PostgreSQL remains the authoritative persistence and concurrency substrate.

## 6. Findings, regression and mandatory STOP

Classify every relevant finding as one of the following.

### Implementation defect

The applicable authorities define the expected behavior correctly and unambiguously, but the implementation does not comply.

Action:

```text
preserve the design
-> reproduce the defect when applicable
-> correct the implementation
-> add or strengthen permanent regression evidence
-> run the affected verification
```

Do not reopen architecture merely because the code contains a bug.

### Architecture defect / missing decision

The authorities are contradictory, incomplete, stale, wrong or insufficient to determine one behavior.

Action:

```text
STOP affected implementation
-> identify impacted authority and scope
-> report the contradiction/gap
-> re-read dependent authorities
-> wait for explicit design decision
-> propagate the correction across all affected normative documents
-> restore the required freeze
-> only then resume implementation
```

Never:

- choose one interpretation in code;
- weaken a test to obtain a green result;
- patch frozen documentation merely to describe the convenient implementation;
- use current code behavior as the new authority;
- continue unaffected-looking work that actually depends on the unresolved point.

A review-fix remains inside the same slice and must stay narrowly scoped to the reviewer findings unless a new architecture issue requires explicit reopen.

## 7. PostgreSQL, concurrency and migration rules

Persistence and concurrency guarantees attributed to PostgreSQL require a real PostgreSQL server.

### Provisioning boundary

The project/test suite does not provision PostgreSQL.

Do not introduce or silently use:

```text
SQLite fallback
fake PostgreSQL semantics
Docker-based test provisioning
Testcontainers
embedded/auto-started PostgreSQL
in-memory lock/MVCC simulations as correctness evidence
```

Configuration boundary:

```text
NETAUTO_DATABASE_URL
    -> runtime / explicit Alembic administration target

TEST_DATABASE_URL
    -> automated real-PostgreSQL verification target
```

Never commit either URL or database credentials.

If required PostgreSQL verification cannot run because `TEST_DATABASE_URL` is absent or unusable, report exactly which gates were not executed and why. Do not claim a fully verified candidate and do not substitute another backend.

### Deterministic concurrency

Use independent PostgreSQL connections/transactions and the current deterministic harness contract.

- Prefer real database blockers, PK/UNIQUE/FK arbitration and advisory gates.
- `sleep()` is not a correctness orchestration primitive.
- Timeouts are safety nets, not race-ordering mechanisms.
- Important non-blocking is proved through positive progress while the other transaction remains open.
- Generic automatic reruns are not accepted as flakiness treatment.
- Semantic retry/convergence is allowed only where the operation contract defines it.

Use:

```text
docs/architecture/concurrency-matrix.md
    -> semantic interaction and safety predicate

docs/architecture/concurrency.md
    -> current PostgreSQL/UoW realization

docs/architecture/verification-concurrency-registry.md
    -> stable scenario IDs, harness constraints and REC-* recipes
```

### Migration discipline

- Application startup never applies migrations implicitly.
- Alembic migration is an explicit administrative action.
- Do not rewrite a migration already included in a delivered AS-IS baseline.
- Add a new revision when an authorized schema change must evolve delivered history.
- A migration inside an undelivered active cycle follows that cycle's frozen migration/architecture authority.
- Verify clean base-to-head migration, metadata/schema alignment and relevant downgrade/upgrade composition where required.

## 8. Verification, quality and dependency discipline

Testing is part of kernel correctness.

Use the canonical commands documented in the root README and the configuration in `pyproject.toml`. Do not invent a parallel toolchain or hidden quality policy.

The current baseline normally includes, as applicable:

```text
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest ...
```

Run the smallest focused verification that proves the affected contract, then expand to all cross-boundary and cycle-required gates.

Verification categories may include:

- pure domain tests;
- application/orchestration tests;
- real-PostgreSQL persistence tests;
- deterministic PostgreSQL concurrency scenarios;
- API contract/integration tests;
- migration/schema/drift tests;
- targeted Hypothesis properties;
- complete cycle regression/acceptance selections.

Rules:

- do not disable or deselect a required failing test merely to complete the task;
- do not hide failures with generic retries;
- do not add broad Ruff/Pyright/test suppressions for convenience;
- suppressions, when unavoidable, must be local and justified;
- strict type checking includes tests and harness code;
- PostgreSQL tests run serially when only one test database is available;
- xdist/parallel real-PG execution requires externally managed isolated database targets per worker.

### Dependencies

Add or change a dependency only for a current justified need consistent with ratified technology decisions.

A dependency change must update `pyproject.toml` and `uv.lock` coherently and pass the applicable verification. Do not introduce overlapping tools/frameworks with duplicate authority or placeholder dependencies for future possibilities.

## 9. Documentation, Git and reviewer ownership

### Documentation modification boundaries

- `docs/architecture/` is the current delivered AS-IS. Do not update it opportunistically during normal implementation; change it only in an explicitly authorized reopen or AS-IS consolidation task.
- Delivered `docs/milestones/<old>/` and `docs/fixes/<old>/` directories are historical records. Do not rewrite them as current authority.
- Active frozen contract, `defects.md` and architecture documents must not be changed merely to fit implementation.
- Update active `steps.md` or `status.md` only when the assigned task explicitly grants that responsibility.
- `wip/` material is non-normative and must not be treated as authority.
- Do not edit, replace or delete the active execution aid unless the task explicitly requires it.

### Reviewer-owned states

The coding agent produces an implementation candidate; the reviewer accepts or rejects it.

The coding agent must not independently assign:

```text
slice COMPLETED
cycle DELIVERED
review outcome ACCEPTED
review outcome REVIEW CHANGES REQUIRED
```

Do not change reviewer-owned status merely because implementation and local tests appear successful.

### Git rules

- Work only on the active cycle branch.
- Never merge to `master`; cycle merge is human-owned.
- Never force-push or rewrite published history unless explicitly authorized for a narrowly defined recovery operation.
- Create a PR only when explicitly requested.
- Commit and push only according to the task's publication instructions.
- Do not include unrelated changes in the candidate.
- Do not commit generated caches, virtual environments, secrets, database URLs or local diagnostic artifacts.
- When a committed/pushed handoff is requested, leave the working tree clean and verify the local/remote branch state.

Historical code may be inspected deliberately for evidence or a narrowly identified implementation idea. It must not be restored merely because it existed before.

## 10. Candidate handoff

The agent's output is a **candidate for reviewer inspection**, not self-approved completion.

At handoff, report only verified facts and include, as applicable:

```text
cycle and slice
branch
commit SHA
push / remote synchronization status
working-tree status

implemented scope
changed files or change categories
migration changes
dependency/lockfile changes

verification commands actually executed
exact results
Python and PostgreSQL versions where relevant

tests/gates not executed and reason
known limitations or residual risks
architecture/documentation findings
explicitly deferred or out-of-scope behavior
```

Use language such as:

```text
candidate implemented and ready for reviewer inspection
```

Do not state that a slice is `COMPLETED` or a cycle is `DELIVERED` unless reporting a reviewer-owned state that was already authoritatively recorded before the agent's work.

Never claim a test, migration, clean working tree, push or remote synchronization that was not actually verified.
