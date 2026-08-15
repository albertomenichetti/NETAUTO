# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S09 — Full M1 acceptance, regression and delivery gate
```

**Step status:** READY TO START

M1-S00 through M1-S08 have completed implementation review.

## M1-S08 accepted baseline

Accepted implementation:

```text
678da20904bec7eb16a6baff45f26a80890dbcae
+
30fa3be16bef705c1e7df1d4c4e66679badf8c72
    REF-06 verification-closure review fix
```

The accepted S08 capability includes:

- final race-safe `Object.DELETE` using `objects(O) FOR UPDATE`;
- zero incoming/outgoing ownership and zero factual-Relationship delete admission;
- semantic blocker counts with factual Relationship de-duplication;
- immediate PostgreSQL FK `RESTRICT` as final Object/reference lifetime authority;
- atomic `DELETED` lifecycle event and historical event retention with no implicit cleanup;
- bounded DataType/ObjectTemplate/Object FK race-loser translations;
- full cross-domain DT/OT/RD/Object blocker matrix;
- complete canonical `REF-01..06` closure;
- lifecycle filter/cursor/index closure;
- exact public route inventory: 32 mutation routes and 20 read routes;
- exact finite API-03.11 public code/status catalog: 23 codes;
- no new migration, table, column, advisory gate, or S09 capability.

## S08 REF-06 completion

The final review-only patch is test-only and closes the remaining canonical mechanism evidence:

```text
REF-06A  DataType aggregate CASCADE
         × external ObjectTemplate property exact-DTV RESTRICT

REF-06B  ObjectTemplate aggregate CASCADE
         × external current Object -> exact OTV RESTRICT

REF-06C  RelationshipDefinition aggregate CASCADE
         × factual Relationship RESTRICT
```

Each variant proves:

```text
delete pre-check observes zero blockers
-> concurrent semantic reference commits
-> physical root DELETE is attempted
-> PostgreSQL RESTRICT is the loser authority
-> root aggregate survives
-> owned child state survives intact
-> external current reference survives
```

For REF-06C the isolated physical-delete UoW rolls back automatically on context exit when no commit occurs, so post-race survival assertions observe committed state, not an open aborted transaction.

## Final accepted S08 verification

Reported on PostgreSQL 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1):

```text
uv lock --check / sync / build          PASS
Ruff format/check                       PASS
Pyright strict                          PASS
full suite                              265 passed
non-PostgreSQL                          122 passed
real PostgreSQL                         143 passed
canonical REF selection                 16 passed
explicit REF-06 selection               3 passed
migration selection                     1 passed
schema metadata                         3 passed
persistence constraints / drift         2 passed
```

No production, migration, schema, gate, capability or normative-document change was required by the S08 review fix. No architecture contradiction remains known.

## Frozen physical correction carried from S07

The S07 PAR-02 correction remains part of the accepted M1 baseline:

```text
RelationshipResolution.name = mutable non-key metadata

0002_resolution_name_nonkey
    upgrade   -> drops uq_relationship_resolutions_semantic_child
    downgrade -> restores exactly that constraint
```

Committed `0001` remains unchanged.

## Authoritative baseline

```text
docs/milestones/M1/contract.md
    FINAL / FROZEN

docs/milestones/M1/architecture/README.md
    FROZEN including the PAR-02 correction

docs/milestones/M1/steps.md
    FINAL / FROZEN

docs/general/technology_baseline.md
    STACK-01..STACK-09 RATIFIED

AGENTS.md
    repository-level operating contract
```

## Step registry

```text
M1-S00  COMPLETED        Clean-slate project bootstrap and quality/test runtime
M1-S01  COMPLETED        PostgreSQL schema, migration, UoW and deterministic-test foundation
M1-S02  COMPLETED        PrimitiveType and DataType vertical slice
M1-S03  COMPLETED        ObjectTemplate and active model graph vertical slice
M1-S04  COMPLETED        Object intrinsic state and intrinsic lifecycle vertical slice
M1-S05  COMPLETED        Ownership and Object schema-change vertical slice
M1-S06  COMPLETED        RelationshipDefinition model-plane and capability vertical slice
M1-S07  COMPLETED        Runtime Relationship and relationship lifecycle vertical slice
M1-S08  COMPLETED        Cross-domain integrity, destructive-operation and API/read closure
M1-S09  READY TO START   Full M1 acceptance, regression and delivery gate
```

## Current blockers

None known for starting M1-S09.

PostgreSQL-dependent verification requires the externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

A newly discovered contradiction or missing decision in frozen architecture is not an implementation choice: affected work stops and follows the explicit reopen/revalidate/propagate/re-freeze process.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after implementation review and all applicable quality, API, persistence and deterministic PostgreSQL verification gates satisfy `steps.md`.
