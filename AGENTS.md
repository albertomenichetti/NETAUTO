# NETAUTO — Coding Agent Operating Contract

This file defines repository-level operating rules for coding agents.

It is an **operational contract**, not a domain, architecture, technology or verification specification. It tells the agent how to locate the active work, use the owning documents, distinguish implementation freedom from missing design, stop safely, and hand a candidate to the reviewer.

It must not duplicate, reinterpret or silently override the normative documentation.

## 1. Start from the repository README

After reading this file, always read the root `README.md` before inspecting or modifying the repository.

The README is the operational navigator. It identifies the active cycle, its documentation root and its branch. It intentionally does not duplicate the detailed phase, current slice, blockers or task decomposition.

Resolve the detailed context as follows:

```text
README says active milestone Mx
    -> read docs/milestones/Mx/status.md
    -> read docs/milestones/Mx/steps.md
    -> then read contract.md, architecture/README.md
       and every owning document required by the assigned work

README says active fix Fx-y
    -> read docs/fixes/Fx-y/status.md
    -> read docs/fixes/Fx-y/steps.md
    -> then read defects.md, optional architecture/README.md
       and every owning document required by the assigned work

README says no active cycle
    -> do not modify software
```

The README is not a semantic authority. It cannot override the current AS-IS, an active contract or defect scope, frozen cycle architecture, or ratified technology decisions.

If the README, checked-out branch or active-cycle documents disagree, stop and report the mismatch. Do not infer intent from recency, chat history, a prompt or agent memory.

## 2. Establish the exact work context

Before modifying code, schema, migrations or normative documentation, establish:

```text
checked-out Git branch
active cycle type and identifier
current cycle phase
active slice, when implementation is in progress
assigned task or execution aid
expected publication action: local only, commit, push or PR
```

The active cycle's `status.md` owns the detailed operational state. The active `steps.md` owns slice decomposition and traceability. A prompt is only an execution aid: it narrows the assigned task but cannot create a cycle, change the phase or override frozen authorities.

### No active software cycle

When the README declares no active milestone or fix, software changes are forbidden.

A coding agent may perform repository-governance or documentation maintenance outside a software cycle only when a human explicitly authorizes both the scope and target branch. Such maintenance is limited to:

- repository navigation and governance documents;
- broken references, stale status wording and editorial drift;
- lossless clarification of the delivered AS-IS that does not change system meaning.

If the proposed documentation change would alter delivered semantics, public behavior, persistence guarantees, concurrency guarantees or the supported technology baseline, stop and require a milestone or fix cycle.

## 3. Documentation authority map

Repository documentation is authoritative. Code, tests, generated artifacts, Git history, chat, summaries, reports and memory are evidence or navigation aids; they do not create semantic authority by themselves.

| Source | How to use it |
|---|---|
| `README.md` | Identify the active cycle, its documentation root and branch. |
| `AGENTS.md` | Apply coding-agent operating rules. It governs how the agent works, not what the system means. |
| `docs/general/linee_guida_progetto.md` | Apply project governance: cycle lifecycle, document roles, discovery/WIP discipline, freeze/reopen/propagation, review ownership, final gates and closure. |
| `docs/architecture/README.md` | Enter the authoritative current delivered AS-IS and locate its owning documents. |
| `docs/architecture/*.md` | Verify every current assumption that the active cycle declares unchanged. |
| milestone `contract.md` | Read scope, non-goals and acceptance criteria. |
| milestone `architecture/README.md` | Verify architecture-set status and locate the owning TO-BE documents. |
| milestone `architecture/*.md` | Read explicit TO-BE decisions and their dependencies. |
| fix `defects.md` | Read frozen defect identities, reproduction evidence, violated authority and required correction. |
| fix `architecture/`, when present | Read the frozen correction-design set. |
| active `steps.md` | Read frozen slice scope, dependencies, verification and traceability. It cannot redefine contract, defects or architecture. |
| active `status.md` | Determine the detailed current phase, slice and blockers. |
| milestone `acceptance.md`, when present | Read durable final-acceptance evidence; it is evidence, not a replacement for architecture. |
| `docs/general/technology_baseline.md` | Read every ratified `STACK-*` decision applicable to the task. Technology realizes semantic contracts; it cannot reinterpret them. |
| active `wip/` material | Use only as temporary, always non-normative working material; local freeze/closure wording never makes it architecture authority. |
| `pyproject.toml`, lockfile and code | Inspect configured realization and collect evidence; do not treat them as independent design authority. |

### Combining current AS-IS and active-cycle authority

For a milestone:

```text
current AS-IS
+
explicit frozen milestone delta
=
implementation authority for the active milestone
```

Anything declared unchanged continues to derive from `docs/architecture/`.

A fix also starts from the current AS-IS, but its authority is limited to the frozen defects and any frozen correction design. A fix cannot introduce a new capability, intentional public-contract change or new product semantics.

### Precedence and contradiction

Lower-level execution material cannot override an owning authority:

```text
prompt / wip aid
    cannot override steps, contract, defects or frozen architecture

steps.md
    cannot override contract, defects or architecture

technology choice
    cannot reinterpret semantic architecture

current code or test behavior
    cannot silently redefine documentation
```

If normative sources conflict, do not choose the newest or most convenient. Stop the affected work and report an architecture/documentation defect.

### Discovery and WIP operating discipline

The normative method is owned by `docs/general/linee_guida_progetto.md`. When the active milestone status authorizes discovery or design exploration, apply these operating rules before reasoning from a route-local or mechanism-level candidate:

```text
current semantic guarantee / invariant
!= current technical realization
!= candidate WIP delta
```

Required behavior:

- re-read the relevant current AS-IS owners before evaluating a dependent discovery point;
- preserve awareness of current guarantees and invariants without treating the current technical mechanism as automatically immutable;
- allow a milestone WIP to question or replace AS-IS signatures, data paths, persistence shapes, caches, query strategies, transaction/locking mechanisms or other realization choices when that is the purpose of discovery;
- do not reject a candidate merely because it diverges from the AS-IS mechanism;
- do not silently treat a semantic divergence as already adopted: record it as a candidate delta requiring later normative closure;
- treat every file under `wip/` as non-normative even when its local status says `FROZEN`, `CLOSED`, `RECONCILED` or `FROZEN DISCOVERY INPUT`;
- interpret such local freeze wording only as a working checkpoint that prevents circular rediscovery, never as architecture freeze or implementation authority;
- treat discovery as iterative convergence: every new finding must trigger an explicit check of whether upstream AS-IS assumptions or prior WIP candidates have become suboptimal, redundant, inconsistent or unnecessary;
- reopen, modify or supersede an upstream WIP whenever a downstream finding materially changes its assumptions, cost model, persistence boundary, concurrency rationale or cross-operation value; do not preserve a local closure merely for continuity;
- a local discovery freeze prevents circular rehash only while no new relevant evidence exists; new evidence is a mandatory reopen trigger, not an optional reason to revisit;
- before optimizing "given the current schema/data path", first challenge whether that schema, materialization boundary or division of work between model-plane and data-plane is itself still the best candidate, unless the current task explicitly fixes that boundary as an assumption;
- for a frequent data-plane path that derives or repeatedly resolves stable/slow-changing information, explicitly compare, when applicable: derive-on-read, worker-local cache, shared model-plane materialization, and per-instance/per-edge/per-aggregate data-plane materialization;
- do not reject mutable/per-instance denormalization merely because the value is derivable elsewhere; compare its maintenance cost against the frequency and cost of all operations that would consume it;
- use relative operation frequencies, cardinality/fan-out, warm/cold behavior, storage, write amplification, transaction/concurrency impact and cross-operation reuse as explicit inputs when they can change the preferred candidate;
- when a choice shifts work from a frequent operation to a rarer one, evaluate workload-weighted cost rather than route-local statement count alone; make material frequency assumptions visible instead of silently inventing a workload;
- if a new persistence/materialization candidate can eliminate an earlier query, cache lookup, traversal, lock or recheck, reopen the earlier candidate and recompute its path/cost instead of layering the new mechanism on top of stale work;
- when a candidate changes or bypasses an AS-IS mechanism, record the affected guarantee and the architecture handoff needed for later cross-cutting revalidation;
- do not force route-local discovery to close the entire global concurrency, transactionality or verification model unless that closure is necessary to answer the current discovery question;
- treat WIP SQL/statement counts, latency expectations and other cost profiles as candidate estimates, not normative budgets;
- before implementation, disregard WIP as independent authority and use only current AS-IS plus the explicitly frozen active-cycle architecture.

Use this mandatory thinking loop during discovery:

```text
current question
    -> identify upstream assumptions and candidate dependencies
    -> challenge current realization/materialization boundaries
    -> compare materially different alternatives
    -> select a local checkpoint
    -> propagate known consequences
    -> continue downstream
    -> on new evidence, walk dependencies backward and revalidate
```

For a hot data-plane candidate, do not declare route-local closure until the persistence/materialization challenge has been performed or explicitly recorded as not applicable.

No WIP decision is promoted by default because it was committed, repeatedly reused, human-approved during discovery or deeply analyzed. Promotion occurs only through deliberate architecture-phase adoption and propagation as defined by project governance.

## 4. Mandatory pre-flight before implementation

Before implementing or modifying behavior, perform a dependency-driven repository re-read. Do not rely on memory.

Confirm that:

- README, branch and active-cycle documents identify the same cycle;
- `status.md` explicitly permits the assigned phase and task;
- the task belongs to the active slice when a slice is required;
- every unchanged starting assumption is verifiable in `docs/architecture/`;
- the owning semantic, application, persistence, public-boundary and verification documents are identified;
- relevant invariants, failure semantics and acceptance or defect requirements are known;
- every applicable `STACK-*` decision is ratified;
- no contradiction, stale-open marker or explicit reopen affects the work;
- required verification obligations are known before coding begins.

### Milestone implementation

Verify at minimum:

```text
contract.md
    FINAL / FROZEN

architecture/README.md
    architecture set FROZEN
    no relevant open or reopened point

steps.md
    FINAL / FROZEN
    assigned slice defined

status.md
    explicitly authorizes the assigned implementation or review-fix work
```

Read the current AS-IS plus every milestone document that owns an explicit TO-BE change or a dependency of the slice.

### Fix implementation

Verify at minimum:

```text
defects.md
    FROZEN
    defect IDs assigned to the slice
    reproduction evidence defined
    violated authority identified
    expected correction defined

architecture/README.md
    FROZEN when correction architecture exists

steps.md
    FROZEN
    assigned slice defined

status.md
    explicitly authorizes the assigned implementation or review-fix work
```

A reproducible defect must not reach implementation with only a vague symptom description.

### Change-specific authority checks

Use the owning documents rather than a summary in this file:

- domain/application behavior -> owning current and active-cycle architecture;
- public behavior -> owning API contracts;
- persistence/schema behavior -> owning persistence and migration contracts;
- technology/dependency/composition/toolchain -> applicable ratified `STACK-*` decisions;
- concurrency-sensitive work -> current semantic matrix, PostgreSQL realization and canonical verification registry, plus active-cycle extensions;
- required verification -> current verification architecture, active steps and assigned task.

Do not add an isolated mechanism and call the design complete when the owning semantic or verification chain is absent.

If any mandatory pre-flight check fails, stop before implementing the affected behavior.

## 5. Implementation mandate and freedom

Implementation realizes frozen decisions. It does not make new semantic, architectural or project-wide technology decisions.

Do not resolve ambiguity by:

- inventing a domain rule;
- broadening or weakening a public contract;
- changing a transaction, concurrency or persistence guarantee;
- introducing a new authoritative representation;
- selecting or substituting an unratified technology;
- weakening a verification obligation;
- adding speculative abstractions for future capabilities;
- resurrecting removed historical code or compatibility layers as an implicit baseline.

Prefer the smallest implementation that completely realizes the assigned slice. Vertical completeness is preferred over partial cross-layer scaffolding.

Local implementation decomposition remains free where the owning documents intentionally leave it open. Module structure, helper naming, fixture organization and similar local choices do not require architecture reopening unless they alter semantics, guarantees, boundaries, project-wide technology or verification authority.

Before choosing a framework, library, pattern, layer boundary, persistence technique, concurrency mechanism or testing approach, locate the owning decision. If no applicable decision exists:

```text
purely local decomposition choice
    -> implementer may choose the smallest adequate option

semantic / guarantee / public boundary / project-wide technology choice
    -> STOP and request explicit resolution
```

Historical code may be inspected deliberately as evidence or for a narrowly identified implementation idea. It must not be restored merely because it existed before.

## 6. Findings, regression and mandatory STOP

Classify every relevant finding.

### Implementation defect

The authorities define the expected behavior correctly and unambiguously, but the implementation does not comply.

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

```text
STOP affected implementation
-> identify impacted authority and scope
-> report the contradiction or gap
-> re-read dependent authorities
-> obtain an explicit design decision
-> propagate the correction across every affected normative document
-> restore the required freeze
-> only then resume implementation
```

Never choose one interpretation in code, weaken a test to obtain a green result, rewrite frozen documentation to fit a convenient implementation, or use current code behavior as the new authority.

A review-fix remains inside the same slice and stays limited to reviewer findings unless a new architecture issue requires explicit reopen.

## 7. Verification and change discipline

Testing and verification are part of the implementation candidate.

Determine the required evidence from the owning verification architecture, active contract or defects, active steps, assigned task and project configuration.

Run the smallest focused verification that proves the affected contract, then expand to every cross-boundary and cycle-required gate.

Rules:

- do not replace a required verification layer with a cheaper surrogate;
- do not disable or deselect a required failing test merely to finish the task;
- do not weaken an established regression to match the implementation;
- do not hide failures or flakes with generic retries;
- do not introduce broad suppressions for convenience;
- keep any unavoidable suppression local and justified;
- follow the owning deterministic-concurrency contract rather than improvising a different proof;
- use the ratified toolchain and repository configuration rather than creating a parallel quality policy.

If required infrastructure or configuration is unavailable, report exactly which verification could not run and why. Do not claim a fully verified candidate and do not silently substitute another backend, tool or test strategy.

Schema, migration and dependency changes are permitted only when explicitly inside the active frozen scope. Follow the owning persistence, migration and technology decisions; do not rewrite delivered schema history or add speculative dependencies.

## 8. Documentation, Git and reviewer ownership

### Documentation boundaries

- `docs/architecture/` is the delivered AS-IS. Change its meaning only through an authorized cycle; outside a cycle, only explicit human-authorized lossless clarification is permitted.
- Delivered milestone and fix directories are historical records. Do not rewrite them as current authority.
- Do not change an active frozen contract, `defects.md` or architecture merely to fit implementation.
- Update active `steps.md`, `status.md`, `acceptance.md` or execution aids only when the task explicitly assigns that responsibility.
- Treat `wip/` as always non-normative working space; local freeze/closure labels are never architecture or implementation authority.

### Reviewer-owned states

The coding agent produces a candidate. The reviewer accepts or rejects it.

The coding agent must not independently assign:

```text
slice COMPLETED
cycle DELIVERED
review outcome ACCEPTED
review outcome REVIEW CHANGES REQUIRED
```

### Git rules

- Work on the active cycle branch identified by README and cycle status.
- Never merge a cycle branch into `master`; merge is human-owned.
- Outside a software cycle, commit directly to `master` only when a human explicitly authorizes a bounded governance/documentation-maintenance task.
- Never force-push or rewrite published history unless explicitly authorized for a narrowly defined recovery operation.
- Create a PR only when explicitly requested.
- Commit and push only according to the task's publication instructions.
- Do not include unrelated changes in the candidate.
- Do not commit secrets, credentials, database URLs, local environments, generated caches or transient diagnostics.
- Before reporting a committed/pushed handoff, verify the working tree and local/remote branch state.

## 9. Candidate handoff

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
schema / migration changes
dependency / lock changes

verification commands actually executed
exact results
runtime/database versions when relevant

verification not executed and reason
known limitations or residual risks
architecture/documentation findings
explicitly deferred or out-of-scope behavior
```

Use language such as:

```text
candidate implemented and ready for reviewer inspection
```

Do not state that a slice is `COMPLETED` or a cycle is `DELIVERED` unless reporting a reviewer-owned state already authoritatively recorded before the agent's work.

Never claim a test, migration, clean working tree, push or remote synchronization that was not actually verified.