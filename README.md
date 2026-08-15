# NETAUTO
NETAUTO is a REST-API-first dynamic infrastructure modeling kernel.

This README is a navigator and operational status projection, not a semantic authority. If this section disagrees with the current Git branch or an active cycle's authoritative `status.md`, stop immediately and ask for confirmation.


## Currently in progress developement phase
None


## At Now delivered

This section is the repository-level current-state projection. It must be updated whenever the active baseline, cycle, branch, phase, slice, execution aid or immediate next action changes.

| Phase | Short Description | Status | Document Repository | Closed Developement Branch |
|---|---| --- | --- | --- |
| M1 | kernel data-modeling framework: DataType, ObejctTemplate, Object, Relationship | DELIVERED & MERGED | docs/milestones/M1 | core_review |

The detailed delivered <Mx/Fx> state remains authoritative in `docs/milestones/<Mx/Fx>/status.md`.


## Documentation map

| Source | Responsibility |
|---|---|
| [`README.md`](README.md) | Operational entry point: current baseline, active cycle, phase, branch. |
| [`AGENTS.md`](AGENTS.md) | Repository operating contract for coding agents. It governs how agents work, not what the system means. |
| [`docs/general/linee_guida_progetto.md`](docs/general/linee_guida_progetto.md) | General governance for milestone and fix cycles, documentation roles, freeze/reopen, reviewer ownership, final gates and closure. |
| [`docs/architecture/README.md`](docs/architecture/README.md) | Entry point and authority map for the current delivered AS-IS: current semantic, persistence, concurrency, API and verification architecture. |
| [`docs/general/technology_baseline.md`](docs/general/technology_baseline.md) | Project-wide implementation technologies and tooling; only ratified `STACK-*` decisions are authoritative while the document remains DRAFT. |


## Repository layout

```text
src/netauto/
    implementation

migrations/
    explicit Alembic schema history

tests/
    domain, application, real-PostgreSQL, concurrency,
    API, migration and property verification

docs/architecture/
    current delivered AS-IS

docs/general/
    project governance and technology baseline

docs/milestones/*
    milestone developement (either currently active or historical records)

docs/fixes/*
    fix-cycle developement (either currently active or historical records)
```


