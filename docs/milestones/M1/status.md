# M1 — Implementation Status

**Milestone status:** IMPLEMENTATION IN PROGRESS

## Current step

```text
M1-S08 — Cross-domain integrity, destructive-operation and API/read closure
```

**Step status:** IN PROGRESS

M1-S00 through M1-S07 have completed implementation review.

## M1-S07 accepted baseline

Accepted implementation:

```text
27150496d460a5eed0ca025b176ec52324e948a4
+
a625cf08572ad0a448cdc9e3e631c2d48878dea7
    verification-closure review fix
```

The accepted S07 capability includes complete factual Relationship semantics, deterministic runtime closure, exact-view PostgreSQL arbitration/convergence, exact-ID DELETE/ABA safety, factual/Object-relative reads, Relationship lifecycle events with one-statement metadata observation, and the final S07 REALIZE-15/API/atomic verification closure.

The S07 PAR-02 architecture correction remains part of the frozen physical baseline:

```text
RelationshipResolution.name = mutable non-key metadata

0002_resolution_name_nonkey
    upgrade   -> drops uq_relationship_resolutions_semantic_child
    downgrade -> restores exactly that constraint
```

No table/column/PK/FK/gate was added by that correction; committed `0001` remains unchanged.

Final accepted S07 verification on PostgreSQL 16.14:

```text
uv lock --check / sync / build          PASS
Ruff format/check                       PASS
Pyright strict                          PASS
non-PostgreSQL                          108 passed
PostgreSQL serial                       131 passed
S07 deterministic concurrency          19 passed
migration / schema / drift              3 passed
```

## M1-S08 pre-flight outcome

The mandatory S08 pre-flight re-read the frozen domain, persistence, concurrency/PGTEST and API authorities together with the accepted S07 implementation seams.

Confirmed:

```text
M1 contract      FINAL / FROZEN
M1 architecture  FROZEN as a set, including PAR-02 correction
M1 steps         FINAL / FROZEN
M1-S00..S07      COMPLETED
STACK-01..09     RATIFIED
```

No new architecture contradiction is known.

S08 is a closure step, not feature expansion. The only final public mutation capability newly delivered here is:

```text
OBJ.DELETE
DELETE /api/v1/core/objects/{object_id}
```

Frozen Object DELETE boundary:

```text
Object owner                  = objects(O) FOR UPDATE
incoming ownership            = 0
outgoing ownership            = 0
current factual Relationships = 0
no implicit detach/delete/cascade/remediation
real delete + DELETED event   = one atomic UoW
```

The semantic blocker detail types are already fixed by API-03.11:

```text
ownership
relationship
```

Relationship blocker counts are factual Relationship counts, not raw RuntimeRelationshipResolution-row counts.

Immediate PostgreSQL FK `RESTRICT` remains final race authority against ownership and Relationship references created concurrently after a semantic pre-check.

### Whole-lineage delete closure

Existing delete semantics remain authoritative:

```text
DataType DELETE_LINEAGE
    -> external ObjectTemplate property exact-DTV references

ObjectTemplate DELETE_LINEAGE
    -> child ObjectTemplate dependency
    -> external component target
    -> current Object exact OTV pin
    -> RelationshipResolution endpoint lineage

RelationshipDefinition DELETE
    -> current factual Relationship blockers
```

S08 must make every `delete_blocked` path, including bounded FK-race loser translation, conform to API-03.11 `details.blockers`; a known FK race must not fall back to bare `{resource_type,id}` details or leak persistence constraint names.

### Canonical PostgreSQL reference closure

S08 closes/audits the full canonical T-REF family:

```text
REF-01  model reference creation × target lineage delete
REF-02  ATTACH × OBJ.DELETE (parent and child)
REF-03  REL.CREATE × OBJ.DELETE(endpoint)
REF-04  REL.CREATE × RD.DELETE (accepted S07 regression retained)
REF-05  DETACH/REL.DELETE × OBJ.DELETE
REF-06  aggregate CASCADE × external RESTRICT
```

The S07-deferred semantic Object-delete scenarios are now executable; no fake/private delete is needed.

### Lifecycle/API closure

The global lifecycle route remains the historical authority. After Object deletion:

```text
GET /objects/{id}                    -> 404
GET /objects/{id}/lifecycle-events   -> 404 current path target absent
GET /lifecycle-events?object_id={id} -> historical events remain queryable
```

S08 also audits the frozen 32-mutation method/path census, all read/list routes, forbidden PUT/PATCH/autonomous-child surfaces, lifecycle filters/indices and the finite API-03.11 error catalog.

## S08 execution aid

The non-normative Codex prompt is:

```text
docs/milestones/M1/wip/M1-S08-codex-prompt.md
```

Prompt creation commit:

```text
5e4357eff6dce8ee6cee4632d25ed7377103e073
```

The prompt does not override the frozen architecture or ratified technology baseline.

## Authoritative baseline

```text
docs/milestones/M1/contract.md
    FINAL / FROZEN

docs/milestones/M1/architecture/README.md
    FROZEN after PAR-02 correction

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
M1-S08  IN PROGRESS      Cross-domain integrity, destructive-operation and API/read closure
M1-S09  NOT STARTED      Full M1 acceptance, regression and delivery gate
```

## Current blockers

None known for implementing M1-S08.

PostgreSQL-dependent verification requires the externally supplied dedicated real PostgreSQL target through `TEST_DATABASE_URL`.

A newly discovered contradiction or missing decision in frozen architecture is not an implementation choice: affected work stops and follows the explicit reopen/revalidate/propagate/re-freeze process.

## Operational rule

This file records operational progress only. It does not redefine milestone scope, architecture, technology choices or step semantics.

A step moves to `COMPLETED` only after implementation review and all applicable quality, API, persistence and deterministic PostgreSQL verification gates satisfy `steps.md`.
