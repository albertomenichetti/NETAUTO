# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S06 — RelationshipDefinition model-plane and capability vertical slice
```

**Step status:** READY TO START

M1-S00 through M1-S05 have completed implementation review.

## M1-S05 accepted baseline

Accepted implementation:

```text
62857cc0c32b332a0e916ea83bdb2653f69596ab
+
622a46dde54c8f74cb8bc4ae6b7e70ebf140ee6f
    deterministic verification closure
```

The reviewed S05 capability includes:

- ATTACH/DETACH current ownership semantics with single-owner authority and acyclic graph enforcement;
- current `SlotSemanticKey` interpretation from the parent current exact effective schema, with no historical fallback or duplicated current-edge declaring lineage;
- `OWNERSHIP_GRAPH_WRITE_GATE` only for real edge-add candidates, with mandatory fresh post-gate child-ownership and graph reads;
- forward same-lineage Object `SCHEMA_CHANGE` with exact target admission, semantic-key property migration and outgoing attachment preservation;
- typed ATTACH_TO/DETACH_FROM lifecycle events committed atomically with the ownership transition;
- coherent Object components/owner projections and lifecycle response union extended through ownership events;
- strict S05 public routes and finite error mapping;
- no migration, final Object.DELETE, S06+ Relationship behavior, JSON Schema, ORM or new advisory gate.

The S05 architecture pre-flight had previously found and resolved the current-edge/DETACH documentation contradiction before coding. The frozen authority remains:

```text
object_components(child_object_id, parent_object_id, slot_name)
    -> current parent exact effective schema
    -> SlotSemanticKey(declaring_template_id, slot_name)
```

An unresolvable current edge is invariant corruption (`internal_error`), not a supported legacy edge. `SCHEMA_CHANGE` must prevent a committed repin that would make a retained edge uninterpretable or incompatible.

The verification decomposition was also aligned so semantic ownership `REF-02` / `REF-05` remain deferred to M1-S08 together with final `Object.DELETE`; S05 proves the current ownership PK/FK mechanics directly without introducing a private delete capability.

### Final S05 deterministic PostgreSQL coverage

The accepted suite includes the S05-realizable canonical scenarios and mechanism regressions:

```text
ROW-12 A/B  DATA_CHANGE × SCHEMA_CHANGE; SCHEMA_CHANGE × SCHEMA_CHANGE
ROW-13      ATTACH × SCHEMA_CHANGE(parent), both serial orders
ROW-14      DETACH × SCHEMA_CHANGE(parent), both serial orders
ARB-02      different ATTACH, same child + raw PK authority
ARB-03 A/B  identical ATTACH / identical DETACH convergence
ARB-04      ATTACH × DETACH exact fact
GATE-01     opposite edge-add / fresh committed graph visibility
GATE-02 A/B longer cycle; cycle candidate × concurrent path-removing DETACH
GATE-03 A/B fresh post-gate graph visibility; post-gate child-ownership reread
SNAP-04     ownership structural-event child display metadata
ATOMIC-04B  ownership edge/event all-or-nothing
PAR-03      intentional parent-owner serialization
PAR-04      intentional global ownership-gate serialization
```

Additional regression evidence proves exact no-op ATTACH, ownership-conflict ATTACH and DETACH do not acquire `OWNERSHIP_GRAPH_WRITE_GATE`.

### Final S05 quality gates

Reported on PostgreSQL 16.14:

```text
uv lock --check                         PASS
uv sync --locked                        PASS
uv build                                PASS
Ruff format/check                       PASS
Pyright strict                          PASS
non-PostgreSQL                          86 passed
PostgreSQL                              86 passed
```

No S05 completion blocker remains.

## Authoritative baseline

M1 implementation proceeds from the frozen/ratified authorities:

```text
docs/milestones/M1/contract.md
    FINAL / FROZEN

docs/milestones/M1/architecture/README.md
    FROZEN global architecture baseline

docs/milestones/M1/steps.md
    FINAL / FROZEN implementation decomposition

docs/general/technology_baseline.md
    STACK-01..STACK-09 ratified

AGENTS.md
    repository-level operating contract
```

Before each implementation step, the mandatory pre-flight defined by `AGENTS.md`, `docs/general/linee_guida_progetto.md` and the step itself must be executed against the current normative repository documents.

## Step registry

```text
M1-S00  COMPLETED        Clean-slate project bootstrap and quality/test runtime
M1-S01  COMPLETED        PostgreSQL schema, migration, UoW and deterministic-test foundation
M1-S02  COMPLETED        PrimitiveType and DataType vertical slice
M1-S03  COMPLETED        ObjectTemplate and active model graph vertical slice
M1-S04  COMPLETED        Object intrinsic state and intrinsic lifecycle vertical slice
M1-S05  COMPLETED        Ownership and Object schema-change vertical slice
M1-S06  READY TO START   RelationshipDefinition model-plane and capability vertical slice
M1-S07  NOT STARTED      Runtime Relationship and relationship lifecycle vertical slice
M1-S08  NOT STARTED      Cross-domain integrity, destructive-operation and API/read closure
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

None known for starting M1-S06.

PostgreSQL-dependent verification continues to require an externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

A newly discovered contradiction or missing decision in frozen architecture is not an implementation choice: the affected work stops and follows the explicit architecture reopen/revalidate/propagate/re-freeze process.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after implementation review and all applicable quality, API, persistence and deterministic PostgreSQL verification gates satisfy `steps.md`.
