# NETAUTO — Coding Agent Operating Contract

This file defines repository-level operating rules for coding agents.

It is an **operational contract**, not a domain, architecture, technology or verification specification. It tells the agent:

- how to determine the current project phase and assigned work;
- which authoritative documents to read and how to combine them;
- which pre-flight checks are required before implementation;
- which choices remain local implementation freedom;
- when work must stop for an explicit design decision;
- what may be changed and what must remain reviewer-owned;
- which evidence must be returned at handoff.

It must not duplicate, reinterpret or silently override the owning normative documentation.

## 1. Start from the repository README

Before any repository work, read the root `README.md`.

The README is the mandatory **operational entry point**. It must identify, directly or through explicit links:

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

Use the README to determine **where the project currently is**. Then verify that state against the current Git branch and the active cycle documents.

The README is a navigator, not a semantic authority. It cannot override `docs/architecture/`, an active milestone contract, a frozen defect scope, frozen cycle architecture or the ratified technology baseline.

Do not infer the current phase from branch name, commit recency, chat history, the latest prompt or agent memory alone.

If the README does not identify the current phase clearly, points to missing or incompatible cycle documents, or disagrees with the branch or authoritative cycle status, stop before modifying the repository and report the state/documentation gap.

## 2. Establish the exact work context

Before modifying code or normative documentation, establish all of the following:

```text
current Git branch
active cycle type: milestone Mx or fix Fx-y
active cycle identifier
current phase
active slice identifier: Mx-Snn or Fx-y-Snn
active task / execution aid
publication expectation: local only, commit, push, or PR
```

Code-base changes are permitted only inside an active milestone or fix cycle, as defined by `docs/general/linee_guida_progetto.md`.

The README, branch, cycle, phase, slice, status and active task must agree. If they do not, stop and report the mismatch rather than guessing the intended target.

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

Apply the phase boundary strictly:

- during `DESIGN`, do not implement the behavior being designed;
- during `IMPLEMENTATION`, work only on the active frozen slice;
- during `REVIEW / REVIEW FIX`, address only the current reviewer findings unless an explicit reopen occurs;
- during `FINAL ACCEPTANCE / FINAL REGRESSION`, do not introduce unrelated production changes;
- during `AS-IS CONSOLIDATION`, modify only the documentation or artifacts explicitly owned by consolidation;
- when no active code cycle exists, do not modify the code-base.

An active prompt is an execution aid. It narrows the assigned task but never creates authority, changes the phase or overrides frozen documents.

## 3. Documentation authority map

Repository documentation is authoritative. Code, tests, generated artifacts, Git history, chat, summaries, reports and memory are evidence or navigation aids; they do not create semantic authority by themselves.

Use each source according to its owning role.

| Source | How to use it |
|---|---|
| `README.md` | Determine the current baseline, cycle, phase, slice, active task and next action. Cross-check it against the active cycle documents and Git state. |
| `AGENTS.md` | Apply coding-agent operating rules. It governs how the agent works, not what the system means. |
| `docs/general/linee_guida_progetto.md` | Apply project governance: milestone/fix lifecycle, documentation roles, freeze/reopen/propagation, reviewer ownership, final gates and closure. |
| `docs/architecture/README.md` | Enter the authoritative current delivered AS-IS and locate its owning architecture documents. |
| `docs/architecture/*.md` | Verify every current assumption that the active cycle declares unchanged. |
| `docs/milestones/<Mx>/contract.md` | Read milestone scope, non-goals and acceptance criteria. |
| `docs/milestones/<Mx>/architecture/README.md` | Verify the milestone architecture-set status and locate the owning TO-BE documents. |
| `docs/milestones/<Mx>/architecture/*.md` | Read only the explicit milestone TO-BE decisions and their dependencies. |
| `docs/fixes/<Fx-y>/defects.md` | Read the frozen defect scope, reproduction evidence, violated authority and expected correction. |
| `docs/fixes/<Fx-y>/architecture/`, when present | Read the frozen correction-design set for an architecture defect. |
| active `steps.md` | Read the frozen slice decomposition, scope and traceability. It cannot redefine contract, defects or architecture. |
| active `status.md` | Verify the current operational state and reviewer-controlled progress. |
| `docs/general/technology_baseline.md` | Read every ratified `STACK-*` decision applicable to the task. Technology realizes semantic contracts; it cannot reinterpret them. |
| active `wip/` material | Use only as a temporary execution aid. It is non-normative until promoted. |
| root README commands and `pyproject.toml` | Use the current operational commands and configured project toolchain. |
| code, tests, schema, OpenAPI and Git history | Inspect implementation, reproduce defects and collect evidence. Never use them to override normative documentation. |

### Combining AS-IS and active-cycle authority

A milestone starts from `docs/architecture/` and may diverge from it only where the milestone contract and frozen architecture define an explicit TO-BE change.

```text
current AS-IS
+
explicit frozen milestone delta
=
implementation authority for the active milestone
```

Anything declared unchanged continues to derive from `docs/architecture/`.

A fix also starts from the current AS-IS, but its authority is limited to the frozen defects and any frozen correction design. A fix must not be used to introduce new capability, intentional public-contract change or new product semantics.

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

If normative sources conflict, do not choose the newest, most convenient or last-read document. Stop the affected work and report an architecture/documentation defect.

## 4. Mandatory pre-flight before implementation

Before implementing or modifying behavior, perform a dependency-driven repository re-read. Do not rely on memory.

### Common checks

Confirm that:

- the README, branch, active cycle, phase, slice and task agree;
- the task belongs to the current slice and does not exceed its frozen scope;
- every starting assumption declared unchanged is verifiable in `docs/architecture/`;
- the owning semantic, application, persistence, public-boundary and verification documents affected by the task are identified;
- relevant invariants, failure semantics and acceptance or defect requirements are identified;
- every applicable `STACK-*` decision is ratified;
- no contradiction, stale-open marker or explicit reopen affects the task;
- the required verification obligations are known before coding begins.

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

Read the current AS-IS plus every milestone document that owns an explicit TO-BE change or a dependency of the slice.

### Fix checks

For fix implementation, confirm at minimum:

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
    active slice defined

status.md
    active slice READY / IN PROGRESS / REVIEW CHANGES REQUIRED
    as appropriate to the assigned work
```

A reproducible defect must not reach implementation with only a vague symptom description.

### Change-specific authority checks

Use the owning documents rather than a summary in this file:

- for domain or application behavior, read the owning current and active-cycle architecture;
- for public behavior, read the owning API contracts;
- for persistence or schema behavior, read the owning persistence and migration contracts;
- for a technology, dependency, composition or toolchain choice, read the applicable ratified `STACK-*` decisions;
- for concurrency-sensitive work, read `docs/architecture/concurrency-matrix.md`, `docs/architecture/concurrency.md` and `docs/architecture/verification-concurrency-registry.md`, plus any frozen active-cycle extensions;
- for required test layers and closure evidence, read the owning verification documents, active `steps.md`, task prompt and root README commands.

Do not add an isolated mechanism and call the design complete when the owning semantic or verification chain is absent.

If any mandatory pre-flight check fails, stop before implementing the affected behavior.

## 5. Implementation mandate and freedom

Implementation realizes frozen decisions. It does not make new semantic, architectural or project-wide technology decisions.

Do not resolve ambiguity by:

- inventing a domain rule;
- broadening or weakening a public contract;
- changing a semantic transaction, concurrency or persistence guarantee;
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

The applicable authorities define the expected behavior correctly and unambiguously, but the implementation does not comply.

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
-> identify the impacted authority and scope
-> report the contradiction or gap
-> re-read dependent authorities
-> obtain an explicit design decision
-> propagate the correction across every affected normative document
-> restore the required freeze
-> only then resume implementation
```

Never:

- choose one interpretation in code;
- weaken a test to obtain a green result;
- rewrite frozen documentation to describe the convenient implementation;
- use current code behavior as the new authority;
- continue work that depends on the unresolved point.

A review-fix remains inside the same slice and stays limited to reviewer findings unless a new architecture issue requires explicit reopen.

## 7. Verification and change discipline

Testing and verification are part of the implementation candidate.

Determine the required evidence from:

```text
owning verification architecture
active contract / defects / steps
active task or review-fix prompt
root README operational commands
project configuration
```

Run the smallest focused verification that proves the affected contract, then expand to every cross-boundary and cycle-required gate.

Rules:

- do not replace a required verification layer with a cheaper surrogate;
- do not disable or deselect a required failing test merely to finish the task;
- do not weaken an established regression to match the implementation;
- do not hide failures or flakes with generic retries;
- do not introduce broad suppressions for convenience;
- keep any unavoidable suppression local and justified;
- follow the owning deterministic-concurrency contract rather than improvising a different proof;
- follow the current project commands and configured toolchain rather than creating a parallel quality policy.

If required infrastructure or configuration is unavailable, report exactly which verification could not run and why. Do not claim a fully verified candidate and do not silently substitute another backend, tool or test strategy.

### Schema, migration and dependency changes

Make these changes only when they are explicitly inside the active frozen scope.

- Identify and follow the owning persistence, migration and technology decisions before editing them.
- Do not rewrite delivered schema history unless an explicit authority permits that operation.
- Do not add a dependency for a speculative future need.
- Keep project metadata, lock state and verification coherent according to the ratified technology baseline and root README workflow.

## 8. Documentation, Git and reviewer ownership

### Documentation modification boundaries

- `docs/architecture/` is the delivered AS-IS. Change it only during an explicitly authorized reopen or AS-IS consolidation task.
- Delivered milestone and fix directories are historical records. Do not rewrite them as current authority.
- Do not change an active frozen contract, `defects.md` or architecture merely to fit implementation.
- Update active `steps.md`, `status.md`, `acceptance.md` or execution aids only when the task explicitly assigns that responsibility.
- Treat `wip/` as non-normative working space.

### Reviewer-owned states

The coding agent produces a candidate. The reviewer accepts or rejects it.

The coding agent must not independently assign:

```text
slice COMPLETED
cycle DELIVERED
review outcome ACCEPTED
review outcome REVIEW CHANGES REQUIRED
```

Do not change reviewer-owned status merely because implementation and local tests appear successful.

### Git and repository rules

- Work only on the active cycle branch.
- Never merge the cycle branch into `master`; merge is human-owned.
- Never force-push or rewrite published history unless explicitly authorized for a narrowly defined recovery operation.
- Create a PR only when explicitly requested.
- Commit and push only according to the task's publication instructions.
- Do not include unrelated changes in the candidate.
- Do not commit secrets, credentials, database URLs, local environments, generated caches or transient diagnostics.
- When a committed/pushed handoff is requested, verify the working tree and local/remote branch state before reporting them.

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

Do not state that a slice is `COMPLETED` or a cycle is `DELIVERED` unless reporting a reviewer-owned state that was already authoritatively recorded before the agent's work.

Never claim a test, migration, clean working tree, push or remote synchronization that was not actually verified.
