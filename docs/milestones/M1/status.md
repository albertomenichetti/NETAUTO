# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S09 — Full M1 acceptance, regression and delivery gate
```

**Step status:** IN PROGRESS

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
- immediate PostgreSQL FK `RESTRICT` as final cross-domain lifetime authority;
- atomic `DELETED` lifecycle event and historical retention with no implicit cleanup;
- bounded DataType/ObjectTemplate/Object FK race-loser translation;
- full cross-domain DT/OT/RD/Object blocker matrix;
- complete canonical `REF-01..06` closure including explicit REF-06 aggregate-CASCADE vs external-RESTRICT evidence;
- lifecycle filter/cursor/index closure;
- exact public inventory of 32 mutation routes, 20 read routes and 23 public error codes.

Final accepted S08 verification on PostgreSQL 16.14:

```text
full suite                              265 passed
non-PostgreSQL                          122 passed
real PostgreSQL                         143 passed
canonical REF selection                 16 passed
explicit REF-06 selection               3 passed
migration selection                     1 passed
schema metadata                         3 passed
persistence constraints / drift         2 passed
Ruff / Pyright strict / lock / sync / build  PASS
```

No production, migration, schema, gate, capability or normative architecture change was required by the S08 review fix.

## Frozen S07 physical correction carried forward

The accepted M1 head includes the explicitly re-frozen S07 correction:

```text
RelationshipResolution.name = mutable non-key metadata

0002_relationship_resolution_name_nonkey.py
    upgrade   -> drops uq_relationship_resolutions_semantic_child
    downgrade -> restores exactly that constraint
```

Committed `0001` remains unchanged.

## M1-S09 pre-flight outcome

The mandatory S09 pre-flight re-read the final milestone contract, global architecture freeze/index, final consistency review, canonical PGTEST matrix, API contracts, technology baseline and accepted repository seams.

Confirmed:

```text
M1 contract      FINAL / FROZEN
M1 architecture  FROZEN as a set, including ownership + PAR-02 corrections
M1 steps         FINAL / FROZEN
M1-S00..S08      COMPLETED
STACK-01..09     RATIFIED
```

No architecture contradiction is currently known.

S09 introduces no new kernel capability. It is the final acceptance/evidence/delivery closure.

### Required final acceptance closure

S09 must prove, not merely report:

```text
AC-01..AC-10            all explicitly traceable and PASS
T0..T6                  complete STACK-07 layer evidence
canonical PGTEST        51 / 51 IDs traceable and passing
non-I safety predicates 19 / 19 traceable
API surface             32 mutation / 20 read / 23 error codes
migrations              clean/base -> head + metadata drift closure
runtime/test DB          explicit separation retained
PostgreSQL-only          no alternative backend burden returned
```

The canonical PGTEST census is:

```text
17 ROW
7  ARB
6  REF
6  GATE
4  SNAP
4  ATOMIC
7  PAR
= 51 canonical IDs
```

S09 must add durable machine-checkable traceability from those IDs to real current tests rather than relying on a prose claim.

### Delivery/documentation closure

The root README is still the earlier clean-slate implementation-state document and must be updated with verified current commands for:

```text
CPython 3.14 / uv setup
explicit NETAUTO_DATABASE_URL migration
Uvicorn application factory run
TEST_DATABASE_URL test execution
Ruff / Pyright / build / focused verification
```

Application startup remains migration-free; PostgreSQL provisioning remains external.

S09 must also create a bounded M1 acceptance evidence record (`docs/milestones/M1/acceptance.md`) covering AC-01..10, T0..T6, PGTEST/predicate closure, API census, migration/static/reproducibility results and exact final verification counts.

The final documentation sweep may correct only demonstrably stale implementation-era wording. Individual architecture documents may retain older authoring labels such as `DRAFT`; global FREEZE-01 in `architecture/README.md` is the authority and those labels must not be misread as open design.

## S09 execution aid

The only current non-normative execution prompt is:

```text
docs/milestones/M1/wip/M1-S09-codex-prompt.md
```

Prompt creation commit:

```text
d29b7d2a9d6553ddde2d7269fdb9f20765bcc6c8
```

Codex must not mark M1-S09 COMPLETED or M1 DELIVERED. Final status transition is reviewer-owned after the acceptance candidate is reviewed.

## Authoritative baseline

```text
docs/milestones/M1/contract.md
    FINAL / FROZEN

docs/milestones/M1/architecture/README.md
    FROZEN including the 2026-08-15 corrections

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
M1-S09  IN PROGRESS      Full M1 acceptance, regression and delivery gate
```

## Current blockers

None known at S09 start.

PostgreSQL-dependent verification requires the externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

If the final gate discovers an implementation defect, fix it with the smallest deterministic regression-backed change. A genuine frozen architecture contradiction instead blocks the affected work and follows the explicit reopen/revalidate/propagate/re-freeze process.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

M1-S09 and M1 move to completed/delivered state only after the final GitHub delta and acceptance evidence have been reviewed.