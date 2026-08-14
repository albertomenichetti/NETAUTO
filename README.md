# NETAUTO

NETAUTO is a REST-API-first dynamic infrastructure modeling kernel.

The project is currently rebuilding its core implementation from a frozen M1 design baseline. The previous implementation was intentionally removed: current code must derive from the normative repository documentation rather than from historical package structure or behavior.

## Current milestone

M1 — **Kernel Consistency Baseline** — consolidates the four core concepts:

- `DataType`;
- `ObjectTemplate`;
- `Object`;
- `Relationship`.

M1 is correctness-first and PostgreSQL-only. Domain semantics, persistence, Unit of Work boundaries, concurrency guarantees, HTTP API contracts and verification requirements are designed as one coherent kernel baseline.

The M1 milestone contract is `FINAL / FROZEN`, and the M1 architecture is globally `FROZEN`.

## Documentation authority

Repository documentation is the source of truth for implementation.

Start here:

- [`AGENTS.md`](AGENTS.md) — operating rules for Codex/coding agents;
- [`docs/general/linee_guida_progetto.md`](docs/general/linee_guida_progetto.md) — project workflow, freeze and documentation-alignment rules;
- [`docs/general/technology_baseline.md`](docs/general/technology_baseline.md) — project-wide technology decisions;
- [`docs/milestones/M1/contract.md`](docs/milestones/M1/contract.md) — frozen M1 scope and acceptance criteria;
- [`docs/milestones/M1/architecture/README.md`](docs/milestones/M1/architecture/README.md) — frozen M1 architecture index and normative document map;
- `docs/milestones/M1/steps.md` — implementation decomposition once reviewed and frozen.

If documentation authorities conflict, the conflict is an architecture/documentation defect. It must be resolved in the documentation before the affected behavior is implemented.

## Implementation status

The repository is intentionally at a clean implementation baseline.

No removed historical code, dependency set, CLI, migration layout or package structure is implicitly authoritative. New implementation files are introduced only from the frozen M1 contracts and explicitly ratified technology decisions.

Implementation starts after the M1 step decomposition is reviewed and frozen.

## Historical implementation

Git history remains available for deliberate historical inspection, but previous code is not a compatibility target and must not be reconstructed merely because it existed before the M1 reset.
