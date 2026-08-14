# NETAUTO — Agent Operating Contract

This file gives coding agents repository-level operating rules. It is **not** an architecture specification and must not duplicate or reinterpret the normative documentation.

## 1. Source of truth

For NETAUTO work, repository documentation is authoritative. Chat history, summaries, prior code, Git history and agent memory are navigation aids only.

Read authority in this order, as applicable:

1. `docs/general/linee_guida_progetto.md` — project workflow, freeze, traceability and documentation-alignment rules.
2. `docs/milestones/<milestone>/contract.md` — milestone scope, non-goals and acceptance criteria.
3. `docs/milestones/<milestone>/architecture/README.md` — architecture status/index and map to the owning normative documents.
4. The specific normative architecture documents identified by that index.
5. `docs/general/technology_baseline.md` — project-wide implementation technology choices; only explicitly ratified STACK decisions are authoritative while the document remains DRAFT.
6. Frozen `steps.md` / current `status.md`, when present, for implementation decomposition and current execution state.

If two normative documents conflict, **do not choose one** and do not infer intent from recency. Treat the conflict as an architecture/documentation defect and stop the affected implementation until the authorities are realigned.

## 2. Mandatory pre-flight before implementation

Before implementing or modifying behavior, re-read the normative documents on which that change depends. Scope the re-read to the actual dependencies, but do not rely on memory alone.

For M1, at minimum establish:

- `docs/milestones/M1/contract.md` is `FINAL / FROZEN`;
- `docs/milestones/M1/architecture/README.md` is `FROZEN`;
- the owning domain contract is identified;
- the relevant persistence / UoW / concurrency realization is identified;
- the required PostgreSQL verification scenario(s) are identified where concurrency is involved;
- the API/wire/read/list/error contract is identified for public behavior;
- the required technology choices are explicitly ratified in `technology_baseline.md`;
- no known contradiction or reopened design point affects the work.

If an implementation step depends on a milestone `steps.md`, do not invent that decomposition when the required step document is absent or not frozen.

## 3. Clean-slate implementation rule

The current implementation is intentionally being rebuilt from the frozen documentation.

Do **not** reconstruct the old codebase from Git history, resurrect removed packages/configuration, or copy historical patterns merely because they existed before the reset. Historical code may be inspected only deliberately for a narrowly identified implementation idea, and every reused idea must first be validated against the current normative architecture and technology baseline.

New code must derive from the current contracts, not from the previous implementation shape.

## 4. Design vs implementation

Implementation realizes frozen decisions; it does not make new semantic decisions.

Do not resolve ambiguity by:

- adding a convenient domain rule;
- weakening or broadening a public contract;
- changing transaction boundaries or lock semantics;
- introducing a new persistence representation;
- selecting an unratified framework/library;
- creating speculative abstraction for a future capability.

When a genuine missing decision is encountered, report the gap and stop the affected behavior. Architecture must be explicitly reopened and propagated before implementation continues.

Prefer the smallest implementation that fully realizes the frozen contract. NETAUTO deliberately avoids speculative generalization and framework-shaped domain design.

## 5. Layer boundaries

Preserve the boundaries ratified in the technology baseline and milestone architecture.

In particular:

- domain code is plain Python and performs no hidden I/O;
- application I/O is asynchronous where required by the ratified execution model;
- FastAPI/Pydantic remain transport-boundary technologies, not domain authorities;
- SQLAlchemy/Psycopg remain persistence-boundary technologies and do not leak into domain/application semantics;
- PostgreSQL is the authoritative persistence/concurrency substrate;
- a semantic Unit of Work owns its explicit connection/transaction and transaction boundary;
- FastAPI `Depends()` is not the kernel composition container;
- process-local state, locks or caches must never become cross-process correctness authorities.

Do not duplicate these rules here with new semantics: consult the owning STACK/architecture documents for details.

## 6. PostgreSQL and concurrency correctness

Never substitute SQLite, fake PostgreSQL behavior, mocked locks or in-memory concurrency simulation as evidence of persistence/concurrency correctness.

For frozen M1 concurrency behavior, preserve the deterministic PGTEST contract, including independent PostgreSQL sessions, real blockers/constraints/gates, fresh-snapshot rules, and the prohibition on `sleep()` as a correctness orchestration primitive.

If a concurrency regression is found, prefer a deterministic failing regression scenario before/with the fix whenever reasonably possible.

## 7. Testing and quality gates

Testing is part of kernel correctness, not optional scaffolding.

For every change, run the smallest applicable verification set that proves the affected contracts, and expand it when the change crosses boundaries. Use the ratified tools/configuration from `technology_baseline.md`.

Expected categories include, as applicable:

- pure domain/unit tests;
- application/orchestration tests;
- real-PostgreSQL persistence tests via externally supplied `TEST_DATABASE_URL`;
- deterministic PostgreSQL concurrency tests;
- API contract/integration tests;
- migration/schema tests;
- targeted Hypothesis properties;
- Ruff formatting/linting;
- Pyright strict type checking.

Do not hide flakes with generic retries. Do not silently skip required PostgreSQL verification by falling back to another backend.

## 8. Documentation discipline

`docs/` is the current documentation authority.

Temporary/WIP material, when present under a `wip/` location, is non-normative until promoted into the appropriate authoritative document.

When implementation reveals a true contradiction or missing architecture decision, do not patch documentation merely to match code. Reopen the design explicitly, ratify the change, propagate it to all affected normative documents, restore the freeze, then implement.

Implementation-only decomposition or operational status may be updated in the milestone files intended for those purposes, but frozen semantic contracts must not drift as a side effect of coding.

## 9. Repository hygiene

Keep the repository intentionally small and explicit:

- add dependencies only when required by a ratified decision or current implementation need;
- avoid duplicate tools/frameworks with overlapping authority;
- do not add generated caches, local environments, secrets or test database credentials to Git;
- keep configuration centralized where the technology baseline requires it;
- do not create compatibility layers for removed historical code.

## 10. Completion rule

A change is complete only when the repository is coherent across every affected level:

```text
contract / invariant
-> architecture mechanism
-> implementation
-> persistence / API realization where applicable
-> deterministic verification
```

Before finishing, report any contract that could not be verified, any required test that could not run, and any architecture/documentation issue discovered. Never present an implementation as complete while knowingly leaving a semantic contradiction unresolved.
