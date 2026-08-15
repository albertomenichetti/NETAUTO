# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S07 — Runtime Relationship and relationship lifecycle vertical slice
```

**Step status:** READY TO START

M1-S00 through M1-S06 have completed implementation review.

## M1-S06 accepted baseline

Accepted implementation:

```text
1c21ac046505e383b707b3f7e328b82921257673
+
e4fd891a9ef606ea43eaf4aa38029d33619ddbf8
    API error-detail review fix
```

The reviewed S06 capability includes:

- complete `RelationshipDefinition` + authoritative `RelationshipResolution` aggregate semantics;
- deterministic symmetric/non-symmetric Resolution-set derivation with kernel-generated stable identities;
- semantic equivalence and cross-Definition conflict certification over ObjectTemplate lineage-overlap spaces;
- `RELATIONSHIP_DEFINITION_CONFLICT_GATE` for CREATE/RENAME only, with mandatory separate fresh post-gate certified-set read;
- coherent one-statement certified Definition+Resolution set decoding;
- Definition RENAME `FOR NO KEY UPDATE`, DELETE `FOR UPDATE`, and DELETE without conflict gate;
- stable ObjectTemplate lineage FK `RESTRICT` lifetime semantics without exact-OTV admission or generic lifecycle locking;
- atomic complete Resolution-name RENAME;
- RelationshipDefinition CREATE/RENAME/DELETE/GET/list public API;
- ObjectTemplate `relationship-capabilities` projection/list with inherited applicability, exact name filtering and `resolution_id ASC` keyset pagination;
- no standalone RelationshipResolution API, runtime Relationship capability, Relationship lifecycle event variant, migration or new advisory gate.

The final review-fix aligned API-03.11 error details by:

- returning bounded factual Relationship blocker type/count information for `RD.DELETE -> delete_blocked`;
- preserving the failed ObjectTemplate endpoint UUID through the bounded FK-race persistence error so `referenced_resource_not_found.details.id` remains the semantic missing lineage selector.

### Final S06 deterministic PostgreSQL coverage

The accepted suite includes:

```text
ROW-17      RD.RENAME × RD.DELETE, both serial orders
REF-01      RD.CREATE × ObjectTemplate whole-lineage DELETE, both directions
GATE-04 A/B equivalent and non-equivalent conflicting concurrent CREATE
GATE-05 A/B CREATE × RENAME; RENAME(D1) × RENAME(D2)
GATE-06 A/B fresh post-gate visibility; blocker DELETE concurrent with candidate
ATOMIC-04C  complete Resolution-name mutation rollback/atomicity
```

Additional REALIZE-12 mechanism coverage proves same-Definition rename ownership before the gate, intentional global gate over-serialization, transaction-level gate lifetime/release on rollback, coherent protected certified-set reads and absence of fan-out Definition row locking.

### Final S06 quality gates

Reported on PostgreSQL 16.14:

```text
uv lock --check                         PASS
uv sync --locked                        PASS
uv build                                PASS
Ruff format/check                       PASS
Pyright strict                          PASS
non-PostgreSQL                          101 passed
PostgreSQL                              106 passed
```

No S06 completion blocker remains.

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
M1-S06  COMPLETED        RelationshipDefinition model-plane and capability vertical slice
M1-S07  READY TO START   Runtime Relationship and relationship lifecycle vertical slice
M1-S08  NOT STARTED      Cross-domain integrity, destructive-operation and API/read closure
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

None known for starting M1-S07.

PostgreSQL-dependent verification continues to require an externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

A newly discovered contradiction or missing decision in frozen architecture is not an implementation choice: the affected work stops and follows the explicit architecture reopen/revalidate/propagate/re-freeze process.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after implementation review and all applicable quality, API, persistence and deterministic PostgreSQL verification gates satisfy `steps.md`.
