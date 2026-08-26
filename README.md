# NETAUTO

NETAUTO is a REST-API-first dynamic infrastructure modeling kernel.

This README is the repository operational navigator. It identifies the current development-cycle and merge state, when one exists, and records delivered and merged cycles. It is **not** a semantic or architectural authority.

If this README, the checked-out branch or a cycle's authoritative documents disagree, stop and report the mismatch. Work resumes only after the repository state and documentation have been reconciled; conversational confirmation alone does not replace repository alignment.

## Current development cycle

**NO ACTIVE CYCLE**

There is currently no active milestone or fix cycle. Software changes are not permitted until a new cycle is explicitly opened and authorized according to [`docs/general/linee_guida_progetto.md`](docs/general/linee_guida_progetto.md).

When a software cycle is active:

- `Mx` points to `docs/milestones/Mx/`;
- `Fx-y` points to `docs/fixes/Fx-y/`.

A cycle's `status.md` owns its detailed phase, gates and blockers. Its `steps.md` owns the implementation decomposition. This README intentionally does not duplicate those details.

Explicitly authorized repository-governance or documentation maintenance outside a software cycle follows the limited rules in [`docs/general/linee_guida_progetto.md`](docs/general/linee_guida_progetto.md).

## Delivered cycles

| Cycle | Delivered result | Status | Historical record | Merged branch |
|---|---|---|---|---|
| `M1` | Kernel data-modeling baseline: `DataType`, `ObjectTemplate`, `Object`, `Relationship` | `DELIVERED / MERGED` | [`docs/milestones/M1/`](docs/milestones/M1/) | `core_review` |
| `M2` | Versioned Relationship schemas and factual state, durable migration baseline, centralized lock planning, Core Health, official CLI and installed Linux runtime | `DELIVERED / MERGED` | [`docs/milestones/M2/`](docs/milestones/M2/) | `master` |
| `M3` | Trusted one-statement public reads, complete cursor query identity, ObjectTemplate root filtering and exact CLI create-response validation | `DELIVERED / MERGED` | [`docs/milestones/M3/`](docs/milestones/M3/) | `master` |

M2 was merged into `master` by merge commit:

```text
748d02a2c54d432617f8f46b639379188f560bc4
Merge pull request #2 from albertomenichetti/M2
```

M3 was merged into `master` by merge commit:

```text
74e5a5a1404dc6c00a639e39d9de31f3674d064d
Merge pull request #6 from albertomenichetti/M3
```

The delivered M3 source head was:

```text
3111603e3b99276147ee54e869b70b0ea07d879d
```

The detailed delivery and merge states are recorded in the respective milestone `status.md` files. The complete delivered architecture is consolidated under [`docs/architecture/`](docs/architecture/).

## Documentation map

| Source | Responsibility |
|---|---|
| [`README.md`](README.md) | Operational entry point: active-cycle state, delivered/merged cycles, document repositories and branches. |
| [`AGENTS.md`](AGENTS.md) | Operating contract for coding agents; governs how agents work, not what the system means. |
| [`docs/general/linee_guida_progetto.md`](docs/general/linee_guida_progetto.md) | Governance for milestone and fix cycles, documentation roles, freeze/reopen, review, final gates and closure. |
| [`docs/architecture/README.md`](docs/architecture/README.md) | Entry point and authority map for the current delivered AS-IS. |
| [`docs/general/technology_baseline.md`](docs/general/technology_baseline.md) | Ratified project-wide implementation technologies and tooling. |
| `docs/milestones/<Mx>/` | Milestone TO-BE while active; permanent historical record after delivery. |
| `docs/fixes/<Fx-y>/` | Corrective scope/design while active; permanent historical record after delivery. |

Code, tests, schema, generated OpenAPI and Git history are implementation or evidence sources. They do not replace the applicable documentation authority.

## Repository layout

```text
src/netauto/
    implementation

src/netauto/migrations/
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
