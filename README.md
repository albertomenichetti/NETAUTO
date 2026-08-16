# NETAUTO

NETAUTO is a REST-API-first dynamic infrastructure modeling kernel.

This README is the repository operational navigator. It identifies the active development cycle, when one exists, and directs readers to the documents that own its detailed state. It is **not** a semantic or architectural authority.

If this README, the checked-out branch or an active cycle's authoritative documents disagree, stop and report the mismatch. Work resumes only after the repository state and documentation have been reconciled; a conversational confirmation alone does not replace that alignment.

## Current development cycle

| Active cycle | Type | Status | Documentation | Branch |
|---|---|---|---|---|
| `M2` | Milestone | DESIGN | [`docs/milestones/M2`](docs/milestones/M2) | M2 |

When a cycle is active:

- `Mx` points to `docs/milestones/Mx/`;
- `Fx-y` points to `docs/fixes/Fx-y/`.

The cycle's `status.md` owns its detailed phase, current slice and blockers. Its `steps.md` owns the implementation decomposition. This README intentionally does not duplicate those details.

With no active cycle, software changes are not permitted. Explicitly authorized repository-governance or documentation maintenance follows the limited rules in [`docs/general/linee_guida_progetto.md`](docs/general/linee_guida_progetto.md).

## Delivered cycles

| Cycle | Delivered result | Status | Historical record | Merged branch |
|---|---|---|---|---|
| `M1` | Kernel data-modeling baseline: `DataType`, `ObjectTemplate`, `Object`, `Relationship` | `DELIVERED / MERGED` | [`docs/milestones/M1/`](docs/milestones/M1/) | `core_review` |

The detailed M1 delivery state is recorded in [`docs/milestones/M1/status.md`](docs/milestones/M1/status.md). The current delivered architecture is consolidated separately under [`docs/architecture/`](docs/architecture/).

## Documentation map

| Source | Responsibility |
|---|---|
| [`README.md`](README.md) | Operational entry point: active cycle, document repository and branch. |
| [`AGENTS.md`](AGENTS.md) | Operating contract for coding agents; governs how agents work, not what the system means. |
| [`docs/general/linee_guida_progetto.md`](docs/general/linee_guida_progetto.md) | Governance for milestone and fix cycles, documentation roles, freeze/reopen, review, final gates and closure. |
| [`docs/architecture/README.md`](docs/architecture/README.md) | Entry point and authority map for the current delivered AS-IS. |
| [`docs/general/technology_baseline.md`](docs/general/technology_baseline.md) | Ratified project-wide implementation technologies and tooling. |
| `docs/milestones/<Mx>/` | Active milestone TO-BE while open; permanent historical record after delivery. |
| `docs/fixes/<Fx-y>/` | Active corrective scope/design while open; permanent historical record after delivery. |

Code, tests, schema, generated OpenAPI and Git history are implementation or evidence sources. They do not replace the applicable documentation authority.

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
    active or historical milestone records

docs/fixes/*
    active or historical fix-cycle records
```
