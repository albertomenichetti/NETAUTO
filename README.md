# NETAUTO

NETAUTO is a REST-API-first dynamic infrastructure modeling kernel.

This README is the repository operational navigator. It identifies the current development-cycle and merge state, when one exists, and directs readers to the documents that own its detailed status. It is **not** a semantic or architectural authority.

If this README, the checked-out branch or a cycle's authoritative documents disagree, stop and report the mismatch. Work resumes only after the repository state and documentation have been reconciled; a conversational confirmation alone does not replace that alignment.

## Current development cycle

| Cycle | Type | Status | Documentation | Branch |
|---|---|---|---|---|
| `M2` | Milestone | `DELIVERED — MERGE PENDING` | [`docs/milestones/M2`](docs/milestones/M2) | `M2` |

M2 is formally delivered and remains listed here until the human-owned merge is executed. It is no longer an active software implementation cycle: further software changes require a new milestone or fix, or an explicit formal reopen. After merge, this README must be updated to `MERGED` and, when no subsequent cycle exists, to `NO ACTIVE CYCLE`.

When a software cycle is active:

- `Mx` points to `docs/milestones/Mx/`;
- `Fx-y` points to `docs/fixes/Fx-y/`.

A cycle's `status.md` owns its detailed phase, gates and blockers. Its `steps.md` owns the implementation decomposition. This README intentionally does not duplicate those details.

With no active software cycle, software changes are not permitted. Explicitly authorized repository-governance or documentation maintenance follows the limited rules in [`docs/general/linee_guida_progetto.md`](docs/general/linee_guida_progetto.md).

## Delivered cycles

| Cycle | Delivered result | Status | Historical record | Merged branch |
|---|---|---|---|---|
| `M1` | Kernel data-modeling baseline: `DataType`, `ObjectTemplate`, `Object`, `Relationship` | `DELIVERED / MERGED` | [`docs/milestones/M1/`](docs/milestones/M1/) | `core_review` |
| `M2` | Versioned Relationship schemas and factual state, durable migration baseline, centralized lock planning, Core Health, official CLI and installed Linux runtime | `DELIVERED / NOT MERGED` | [`docs/milestones/M2/`](docs/milestones/M2/) | — |

The detailed delivery states are recorded in [`docs/milestones/M1/status.md`](docs/milestones/M1/status.md) and [`docs/milestones/M2/status.md`](docs/milestones/M2/status.md). The complete delivered architecture is consolidated separately under [`docs/architecture/`](docs/architecture/).

## Documentation map

| Source | Responsibility |
|---|---|
| [`README.md`](README.md) | Operational entry point: current cycle, delivery/merge state, document repository and branch. |
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
