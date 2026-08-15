# NETAUTO
NETAUTO is a REST-API-first dynamic infrastructure modeling kernel.

This README is a navigator and operational status projection, not a semantic authority. If this section disagrees with the current Git branch or an active cycle's authoritative `status.md`, stop immediately and ask for confirmation.


## Currently active developement phase
None started


## At Now delivered

This section is the repository-level current-state projection. It must be updated whenever the active baseline, cycle, branch, phase, slice, execution aid or immediate next action changes.

| Phase | Short Description | Status | Document Repository | Branch |
|---|---| --- |
| M1 | kernel data-modeling framework: DataType, ObejctTemplate, Object, Relationship | COMPLETED & MERGED | docs/milestones/M1 | core_review |

The detailed delivered <Mx/Fx> state remains authoritative in `docs/milestones/<Mx/Fx>/status.md`.


## How to start repository work

1. Read this README to determine the current baseline, cycle, phase, branch, slice, task and immediate next action.
2. Coding agents must then read [`AGENTS.md`](AGENTS.md) before modifying the repository.
3. Read [`docs/general/linee_guida_progetto.md`](docs/general/linee_guida_progetto.md) for milestone/fix governance, freeze, review and closure rules.
4. Enter the current delivered architecture through [`docs/architecture/README.md`](docs/architecture/README.md).
5. If a milestone or fix is active, follow the linked active-cycle contract/defect scope, frozen architecture where applicable, `steps.md`, `status.md` and current execution aid.
6. Read every ratified technology decision applicable to the task in [`docs/general/technology_baseline.md`](docs/general/technology_baseline.md).
7. If README, branch, active-cycle documents or task instructions disagree, do not infer intent from recency, code or chat history; stop and report the mismatch.

## Documentation map

| Source | Responsibility |
|---|---|
| [`README.md`](README.md) | Operational entry point: current baseline, active cycle, phase, branch, slice, task and next action. |
| [`AGENTS.md`](AGENTS.md) | Repository operating contract for coding agents. It governs how agents work, not what the system means. |
| [`docs/general/linee_guida_progetto.md`](docs/general/linee_guida_progetto.md) | General governance for milestone and fix cycles, documentation roles, freeze/reopen, reviewer ownership, final gates and closure. |
| [`docs/architecture/README.md`](docs/architecture/README.md) | Entry point and authority map for the current delivered AS-IS. |
| [`docs/architecture/`](docs/architecture/) | Current semantic, persistence, concurrency, API and verification architecture. |
| [`docs/general/technology_baseline.md`](docs/general/technology_baseline.md) | Project-wide implementation technologies and tooling; only ratified `STACK-*` decisions are authoritative while the document remains DRAFT. |
| `docs/milestones/<Mx>/` | Active milestone TO-BE and permanent historical milestone record after delivery. |
| `docs/fixes/<Fx-y>/` | Active corrective scope/design and permanent historical fix record after delivery. |
| active `steps.md` | Frozen implementation decomposition and traceability for the current cycle. |
| active `status.md` | Detailed current operational state; reviewer-owned completion and delivery status. |
| active `wip/` | Temporary, non-normative execution aids. |
| code, tests, schema, OpenAPI and Git history | Implementation and evidence sources; never autonomous semantic authority. |

A future milestone starts from `docs/architecture/` and may diverge from it only through an explicit contract-derived, frozen TO-BE decision. A fix corrects behavior already owed by the delivered baseline and cannot be used to introduce a new capability or intentional public-contract change.


## Repository layout

```text
src/netauto/
    kernel implementation

migrations/
    explicit Alembic schema history

tests/
    domain, application, real-PostgreSQL, concurrency,
    API, migration and property verification

docs/architecture/
    current delivered AS-IS

docs/general/
    project governance and technology baseline

docs/milestones/
    milestone TO-BE and historical records

docs/fixes/
    fix-cycle scope/design and historical records, when present
```


