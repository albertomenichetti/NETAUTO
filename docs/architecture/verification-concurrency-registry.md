# Canonical Concurrency Verification Registry — Current AS-IS

## Purpose and authority

This document is the authoritative current registry of deterministic real-PostgreSQL concurrency scenarios and reusable orchestration recipes.

It answers:

```text
which semantic race must remain verified?
which stable scenario ID names it?
which safety predicate(s) does it cover?
which orchestration recipe proves the required interleaving?
```

Scenario semantics are authoritative here. Concrete pytest targets are
implementation evidence and are machine-checked by the permanent traceability
registries; test names may be refactored without changing scenario identity,
provided the registry remains completely and correctly mapped.

The semantic predicate definitions and pairwise scope are owned by `concurrency-matrix.md`. PostgreSQL realization is owned by `concurrency.md`.

## Canonical scenario contract

A deterministic scenario specifies, as applicable:

```text
stable scenario ID
operations and concrete scope
safety predicate set
initial committed state
T1 / T2 / optional T3 phases
deterministic coordination points
required blocking or required progress
allowed committed outcomes
forbidden outcomes
final current-state assertions
lifecycle-event assertions
retry / convergence assertions
semantic authority and PostgreSQL mechanism exercised
```

Semantic outcome assertions are always normative. Mechanism assertions are also normative when the mechanism is part of the architecture, including:

- required row-lock rendezvous;
- PK/UNIQUE/FK arbitration;
- advisory-gate wait and post-wait fresh snapshot;
- intentional non-blocking;
- intentional over-serialization.

Normative concurrency evidence uses real PostgreSQL and independent connections/transactions. SQLite, mock repositories, in-process fake transactions and sleep-only scheduling cannot prove PostgreSQL locking, MVCC, constraint or advisory-gate guarantees.

## Scenario census

```text
ROW      30
ARB       8
REF      11
GATE      7
SNAP      5
ATOMIC    7
PAR       9
PLAN      6
        ----
total    83
```

The 83 IDs are stable. Variants `A/B/C` may share one ID only when they preserve the same authority, dominant mechanism and deterministic orchestration family.

## `ROW` — row-state serialization and freshness

| ID | Current semantic obligation |
|---|---|
| `ROW-01` | Same-lineage DataType/ObjectTemplate `CREATE_NEXT × CREATE_NEXT`: serially distinct version allocation under `VS`. |
| `ROW-02` | `CREATE_NEXT × DELETE_DRAFT(max)`: waiter re-evaluates the current version set/source after wake-up under `VS`. |
| `ROW-03` | Same exact DRAFT generation `REVISE × REVISE`: one winner, stale loser under `DG`. |
| `ROW-04` | Exact DRAFT terminal races: `REVISE × PUBLISH` and `PUBLISH × DELETE_DRAFT`; post-wait generation/lifecycle recheck under `DG + LS`. |
| `ROW-05` | Two PUBLISH operations in one lineage with NULL default: first serial publisher establishes the stable default under `DV`. |
| `ROW-06` | `SET_DEFAULT(v) × DEPRECATE(v)`: committed default never identifies a DEPRECATED version under `DV + LS`. |
| `ROW-07` | Explicit new exact binding × target DEPRECATE: admission holds target PUBLISHED through commit under `BA`. |
| `ROW-08` | Implicit binding × SET/CLEAR default: coherent default selection plus exact target admission under `BA + DV`. |
| `ROW-09` | ObjectTemplate consumer PUBLISH × dependency DEPRECATE: active-edge activation/deprecation rendezvous under `AM`. |
| `ROW-10` | Active blocker removal × dependency DEPRECATE: consumer deprecate/delete-lineage first may permit success; otherwise conservative failure under `AM`. |
| `ROW-11` | `OBJ.DATA_CHANGE × OBJ.DATA_CHANGE`: no lost JSONB update; waiter derives from fresh complete Object state under `OS`. |
| `ROW-12` | Object current-state/schema races: DATA_CHANGE × SCHEMA_CHANGE and SCHEMA_CHANGE × SCHEMA_CHANGE; fresh derivation under `OS`, plus target admission under `BA`. |
| `ROW-13` | ATTACH × parent SCHEMA_CHANGE: edge/schema outcomes are serially composable under `PO`. Both operation orders are required. |
| `ROW-14` | DETACH × parent SCHEMA_CHANGE: edge removal may unblock migration under `PO`. Both operation orders are required. |
| `ROW-15` | SET_DESCRIPTION × SET_DESCRIPTION: complete atomic last-write-wins values under `ML`. |
| `ROW-16` | REVISE × whole-lineage DELETE on the same aggregate: no partial child/aggregate state under `AL`. |
| `ROW-17` | RelationshipDefinition RENAME × DELETE on the same Definition: aggregate lifetime serialization under `AL`. |
| `ROW-18` | Same-Definition RD CREATE_NEXT × CREATE_NEXT allocates serially distinct versions from a fresh version set under `VS`. |
| `ROW-19` | RD CREATE_NEXT racing with relevant DRAFT deletion or source publication re-evaluates maximum/source eligibility after waiting under `VS`. |
| `ROW-20` | Same exact RDV generation REVISE/PUBLISH/DELETE_DRAFT has one valid generation consumer and exact stale/lifecycle/absence loser under `DG + LS`. |
| `ROW-21` | RD publication/default/set/clear/deprecate preserves a null-or-PUBLISHED same-Definition default under `DV + LS`. |
| `ROW-22` | Distinct ObjectTemplateVersion publications re-certify complete member history; no non-serial published history commits under `VH`. |
| `ROW-23` | Distinct RDV publications re-certify property history and first-default policy under `VH + DV`. |
| `ROW-24` | RD CREATE/REVISE exact or default DTV binding stabilizes one PUBLISHED target and materializes one coherent exact pin under `BA + DV`. |
| `ROW-25` | RDV PUBLISH and DTV DEPRECATE rendezvous; active-consumer removal permits success or conservative conflict under `AM`. |
| `ROW-26` | Relationship DATA_CHANGE × DATA_CHANGE uses fresh properties; no lost update and a waiter may become a no-op under `RS`. |
| `ROW-27` | Relationship DATA_CHANGE × SCHEMA_CHANGE produces serial factual history under the fresh pin/state under `RS`. |
| `ROW-28` | Relationship SCHEMA_CHANGE × SCHEMA_CHANGE re-evaluates source and exact target; only valid forward transitions commit under `RS + BA`. |
| `ROW-29` | Relationship DATA_CHANGE/SCHEMA_CHANGE × DELETE yields mutation-then-delete or delete-then-not-found with matching events under `RS`. |
| `ROW-30` | Explicit/implicit Relationship CREATE and SCHEMA_CHANGE arbitrate correctly with RDV publish/deprecate/default changes under `BA + DV`. |

## `ARB` — PK/UNIQUE arbitration and convergence

| ID | Current semantic obligation |
|---|---|
| `ARB-01` | Same qualified-name model CREATE × CREATE: one unique lineage wins and no orphan aggregate remains under `NU`. |
| `ARB-02` | Different-owner ATTACH candidates for the same child: ownership PK is final `SO` authority. Raw persistence arbitration remains covered so the graph gate cannot mask it. |
| `ARB-03` | Identical ATTACH and identical DETACH races: one real transition/event; the other converges as no-op under `OF`. |
| `ARB-04` | ATTACH × DETACH on the same exact fact: final state and event sequence must be serially explainable under `OF`. |
| `ARB-05` | Equivalent Relationship CREATE through reciprocal selectors, symmetric inverse assignment or inheritance overlap: exact-view arbitration; current-owner loser reports conflict and emits no event under `RF`. |
| `ARB-06` | Same-ID Relationship DELETE × DELETE: one 204, one 404 and one real deletion/event set under `RA`. |
| `ARB-07` | Relationship exact-ID ABA: late DELETE(X) cannot remove recreated Y; a collision loser restarts only if the observed winner disappears, while a current winner remains a conflict under `RF + RA`. |
| `ARB-08` | Non-equivalent candidate closures sharing any exact runtime-view key commit at most one complete fact; loser rolls back and reports current-owner conflict under `RF`. |

## `REF` — FK `RESTRICT` reference lifetime

| ID | Current semantic obligation |
|---|---|
| `REF-01` | Model reference creation × target-lineage delete, including Object→exact OTV, ObjectTemplate property→exact DTV, component/Resolution→stable ObjectTemplate lineage. Both lifetime orders are exercised under `RL`. |
| `REF-02` | ATTACH × Object DELETE for parent and child lifetime: no dangling ownership reference under `RL`. |
| `REF-03` | Relationship CREATE × endpoint Object DELETE: runtime endpoint FK arbitration under `RL`. |
| `REF-04` | Relationship CREATE × RelationshipDefinition DELETE: factual Definition lifetime arbitration under `RL`. |
| `REF-05` | Reference removal × target delete: DETACH or Relationship DELETE may unblock Object DELETE; current blocker may cause conservative failure under `RL`. |
| `REF-06` | Aggregate internal CASCADE × external RESTRICT: root deletion cannot bypass an external reference; root, owned children and external reference survive the losing delete under `RL`. |
| `REF-07` | RD CREATE_NEXT cloned DTV references × DataType root delete, both winner orders, under `RL`. |
| `REF-08` | ObjectTemplate CREATE_NEXT cloned parent/component/DTV references × target root delete, both winner orders, under `RL`. |
| `REF-09` | Differential OT/RDV declaration replacement or reinsertion × target delete: no transient gap, dangling reference or deadlock under `RL`. |
| `REF-10` | Direct owner rebind × target root delete for OT parent, Object schema and Relationship schema, both orders and no deadlock under `RL`. |
| `REF-11` | Mutually referencing model-root deletes serialize through the model-root gate with no partial aggregate or deadlock under `RL`. |

`REF` coverage includes exact/composite and stable-lineage FK shapes.

## `GATE` — advisory predicate-set gates and fresh snapshots

| ID | Current semantic obligation |
|---|---|
| `GATE-01` | Opposite ownership edge additions `A→B × B→A`: at most one commits without a cycle under `OC`. |
| `GATE-02` | Non-trivial ownership graph: longer-cycle rejection and cycle-check race with a concurrent DETACH removing the blocking path under `OC`. |
| `GATE-03` | Ownership gate visibility: waiter observes the previous holder's committed graph and rereads child ownership in a subsequent READ COMMITTED statement under `OC`. |
| `GATE-04` | Concurrent RelationshipDefinition CREATE candidates, equivalent or conflicting: one globally admissible candidate under `RC`. |
| `GATE-05` | RelationshipDefinition CREATE × RENAME and RENAME × RENAME: certified-set candidate serialization under `RC`. |
| `GATE-06` | Definition gate visibility and blocker removal: waiter sees committed set after gate; DELETE takes no gate and may unblock or cause conservative failure under `RC`. |
| `GATE-07` | Model-root-delete-gate waiter owns no NETAUTO row lock, acquires after release and performs fresh blocker/aggregate reads. |

`GATE-03` and `GATE-06` must fail if gate acquisition and protected read are collapsed into one stale pre-wait statement snapshot.

## `SNAP` — coherent committed observation without generic serialization

| ID | Current semantic obligation |
|---|---|
| `SNAP-01` | Definition RENAME × real Relationship CREATE/DATA_CHANGE/SCHEMA_CHANGE/DELETE: complete event set uses one committed Definition-name observation under `ES`. |
| `SNAP-02` | Object RENAME × real Relationship CREATE/DATA_CHANGE/SCHEMA_CHANGE/DELETE: endpoint display metadata comes from one committed observation under `ES`. |
| `SNAP-03` | Independently renamed endpoints: only name combinations that coexisted in one statement snapshot; transaction timestamp does not redefine observation time under `ES`. |
| `SNAP-04` | Child rename concurrent with ATTACH/DETACH: no child lock solely for display metadata; structural event captures one committed child-name observation. |
| `SNAP-05` | Relationship DATA_CHANGE/SCHEMA_CHANGE racing with Object and Resolution renames produces one coherent all-row metadata observation while required rename progress remains possible under `ES`. |

`SNAP-04` protects a lifecycle metadata realization clarification and does not introduce a twentieth safety predicate.

## `ATOMIC` — all-or-nothing semantic transitions

| ID | Current semantic obligation |
|---|---|
| `ATOMIC-01` | Multi-row ObjectTemplate candidate failure cannot expose mixed header/property/component generation; supports `DG`. |
| `ATOMIC-02` | Later runtime Relationship closure collision rolls back candidate header, earlier closure rows and events under `RF`. |
| `ATOMIC-03` | Forced Relationship DELETE rollback leaves header and complete closure current and commits no deletion events under `RA`. |
| `ATOMIC-04` | State/event or aggregate-child atomicity variants: intrinsic Object transition (`OS`), ownership edge transition (`OF`) and complete Definition rename (`RC`). |
| `ATOMIC-05` | RDV differential declaration failure rolls back revision and complete child generation under `DG`. |
| `ATOMIC-06` | Forced Relationship DATA_CHANGE event failure leaves exact pin/properties/closure unchanged and writes no event under `RS`. |
| `ATOMIC-07` | Forced Relationship SCHEMA_CHANGE event failure rolls back exact pin/properties and writes no event under `RS`. |

Atomic scenarios cover distinct aggregate shapes rather than every mutation separately.

## `PAR` — intended blocking and non-blocking regression probes

| ID | Current semantic obligation |
|---|---|
| `PAR-01` | Relationship CREATE progresses while an Object RENAME remains open; FK identity protection must coexist with non-key Object mutation. Supports `ES`/lock-strength realization. |
| `PAR-02` | Relationship CREATE progresses while Definition RENAME remains open; mutable Resolution name must not become a key-changing FK structure. Supports `ES`. |
| `PAR-03` | Parent Object RENAME × ATTACH intentionally serialize on the shared parent non-key owner. |
| `PAR-04` | Unrelated real ATTACH operations intentionally serialize on the global ownership graph gate; protects `OC` realization. |
| `PAR-05` | Unrelated Relationship CREATE operations have no global Relationship serialization. |
| `PAR-06` | Distinct exact-version DEPRECATE operations in one lineage make progress concurrently at lineage-lock level. |
| `PAR-07` | Header topology: description × set-default intentionally contends; description × exact DRAFT revise makes independent progress. |
| `PAR-08` | Definition RENAME remains compatible with RDV revise/default/deprecate and factual Relationship CREATE where progress is required. |
| `PAR-09` | Distinct exact RDV deprecations and distinct DRAFT revisions make progress under compatible stable-header locks. |

A refactor that preserves functional outcomes but breaks an intended blocking/non-blocking contract is not architecture-compatible.

## `PLAN` — centralized lock planner and failure boundaries

| ID | Current semantic obligation |
|---|---|
| `PLAN-01` | SQL compilation proves exact KS/S/NKU/U mapping, one-table `OF`, explicit ordering and absence of NOWAIT/SKIP LOCKED. |
| `PLAN-02` | Intent coalescence, class ordering, ObjectTemplate ancestor ordering, header/version ordering and UUID tie-breaks are deterministic. |
| `PLAN-03` | A changed dependency set raises `LockPlanStale`, rolls back the whole attempt and starts a fresh UoW; no post-DML lock append. |
| `PLAN-04` | The finite SQLSTATE plus constraint-name registry classifies known races only after rollback; unknown names become internal failure. |
| `PLAN-05` | Exactly four total attempts; no retry after semantic failure, `40P01` or `40001`; exact-view owner-current/disappeared paths remain distinct. |
| `PLAN-06` | At most one gate, gate before rows, no normal upgrade, no explicit row lock after DML and no supported row-to-gate edge. |

## Safety-predicate coverage

```text
NU  -> ARB-01
VS  -> ROW-01, ROW-02, ROW-18, ROW-19
DG  -> ROW-03, ROW-04, ROW-20, ATOMIC-01, ATOMIC-05
LS  -> ROW-04, ROW-06, ROW-20, ROW-21
DV  -> ROW-05, ROW-06, ROW-08, ROW-21, ROW-23, ROW-24, ROW-30
VH  -> ROW-22, ROW-23
BA  -> ROW-07, ROW-08, ROW-12, ROW-24, ROW-28, ROW-30
AM  -> ROW-09, ROW-10, ROW-25
RL  -> REF-01..REF-11
AL  -> ROW-16, ROW-17
ML  -> ROW-15
OS  -> ROW-11, ROW-12, ATOMIC-04
RS  -> ROW-26, ROW-27, ROW-28, ROW-29, ATOMIC-06, ATOMIC-07
PO  -> ROW-13, ROW-14
OF  -> ARB-03, ARB-04, ATOMIC-04
SO  -> ARB-02
OC  -> GATE-01, GATE-02, GATE-03, PAR-04
RC  -> GATE-04, GATE-05, GATE-06, ATOMIC-04
RF  -> ARB-05, ARB-07, ARB-08, ATOMIC-02
RA  -> ARB-06, ARB-07, ATOMIC-03
ES  -> SNAP-01, SNAP-02, SNAP-03, SNAP-04, SNAP-05, PAR-01, PAR-02, PAR-08
```

All 21 current safety predicates must remain mapped to at least one canonical
scenario.

## Deterministic harness contract

Canonical roles:

```text
CTL
    orchestration controller; not a semantic transaction

OBS
    fresh observer/introspection connection

B
    optional real-PostgreSQL blocker/control transaction

T1 / T2 / optional T3
    independent semantic worker transactions
```

Workers use explicit `READ COMMITTED`, independent sessions and identifiable backend metadata. Deterministic ordering is established by real lock/gate/constraint boundaries, explicit barriers or a narrowly bounded test-only persistence interceptor when no canonical PostgreSQL construction is reasonable.

Required harness properties:

- positive blocking is proved primarily through `pg_blocking_pids()` with known blocker PID;
- `pg_stat_activity` and `pg_locks` provide diagnostics, not a fragile reconstructed blocker authority;
- no assumption that a row wait must appear as a specific tuple-lock row;
- intentional non-blocking is proved by positive progress while the other transaction remains open;
- gate wait is followed by a **new** protected-read statement;
- timeouts are hang/failure safety nets, never scheduling primitives;
- no sleep-only orchestration;
- independently committing workers require isolated test databases and explicit cleanup after session termination;
- normative scenarios are not automatically rerun to hide flakiness;
- only operation-defined semantic retry/convergence is allowed;
- stress/randomized tests are supplementary and discoveries must be reduced to a deterministic stable scenario.

Canonical test-phase vocabulary:

```text
UOW_STARTED
DISCOVERY_COMPLETE
LOCK_PLAN_BUILT
OWNER_STABILIZED
DEPENDENCIES_STABILIZED
GATE_WAITING
GATE_ACQUIRED
ROW_LOCK_WAITING
ROW_LOCKS_ACQUIRED
PROTECTED_STATE_REREAD
LOCK_PLAN_STALE
CANDIDATE_WRITTEN
CLOSURE_WRITTEN
METADATA_SNAPSHOT_CAPTURED
EVENT_SET_WRITTEN
CONSTRAINT_ARBITRATED
BEFORE_COMMIT
COMMITTED
ROLLED_BACK
UOW_RESTARTED
```

A test-only interceptor may observe/pause a named persistence phase, but must not change candidate data, issue semantic SQL, alter isolation, commit/rollback, swallow/translate errors differently, select another production path or use sleep to force scheduling.

## Reusable deterministic recipes

### `REC-LOCK` — owner/row-lock waiter

T1 stabilizes the semantic owner and remains open; T2 blocks on that owner; after release T2 must reread/revalidate and produce the correct serial outcome.

### `REC-UNIQUE` — PK/UNIQUE arbitration

One uncommitted candidate occupies the PK/UNIQUE authority; the competing candidate receives the real arbitration outcome. Aggregate candidates roll back completely before semantic convergence/retry.

### `REC-FK` — referential lifetime

Submodes:

```text
REFERENCE_FIRST
DELETE_FIRST
REMOVAL_UNBLOCKS_DELETE
```

No ordering may produce a dangling current reference.

### `REC-GATE` — logical predicate-set waiter

Holder owns the transaction advisory gate; waiter blocks, then acquires it and performs a **subsequent** protected-state read from a fresh READ COMMITTED snapshot.

### `REC-CUT` — committed observation cut

Defines whether authoritative observation occurs before or after a metadata/state commit without introducing generic writer serialization. It also supports conservative blocker-removal outcomes.

### `REC-ROLLBACK` — rollback after physical work

Physical writes occur before a later failure/rollback; no partial current state or lifecycle event set may remain committed.

### `REC-PROGRESS` — intentional non-blocking

T2 reaches a deterministic progress point while T1 remains open, proving that a prohibited generic blocking mechanism is absent.

### `REC-ABA` — fresh-UoW restart / exact identity

Protects exact-ID delete ABA and collision-loser restart from fresh committed state, including winner disappearance before convergence.

### `REC-PLAN` — finite lock-plan construction

Proves pure/static `LockPlan` construction, intent coalescence, canonical ordering and exact SQL compilation without executing a semantic mutation.

### `REC-CLASSIFY` — post-rollback failure classification

Induces or constructs a failure in the finite SQLSTATE plus constraint-name registry, leaves the failed transaction and verifies semantic classification. Unknown names remain internal failures.

### `REC-RESTART` — bounded fresh-UoW restart

Forces an approved restart cause and proves complete rollback, a new connection/UoW, bounded attempt count and fresh derivation. Semantic failures, `40P01` and `40001` are not restart causes.

## Canonical scenario-to-recipe mapping

```text
ROW-01..ROW-09   REC-LOCK
ROW-10           REC-CUT
ROW-11..ROW-30   REC-LOCK

ARB-01           REC-UNIQUE
ARB-02           REC-UNIQUE
ARB-03           REC-LOCK
ARB-04           REC-LOCK
ARB-05           REC-UNIQUE + REC-ABA
ARB-06           REC-LOCK
ARB-07           REC-ABA
                 variant B also REC-UNIQUE + REC-RESTART
ARB-08           REC-UNIQUE + REC-ROLLBACK

REF-01..REF-10   REC-FK
REF-11           REC-GATE + REC-FK

GATE-01          REC-GATE
GATE-02          REC-GATE
                 removal variant also REC-CUT
GATE-03..GATE-05 REC-GATE
GATE-06          REC-GATE
                 blocker-delete variant also REC-CUT
GATE-07          REC-GATE

SNAP-01..SNAP-05 REC-CUT

ATOMIC-01        REC-ROLLBACK
ATOMIC-02        REC-UNIQUE + REC-ROLLBACK
ATOMIC-03        REC-ROLLBACK
ATOMIC-04..07     REC-ROLLBACK

PAR-01           REC-PROGRESS
PAR-02           REC-PROGRESS
PAR-03           REC-LOCK
PAR-04           REC-GATE
PAR-05           REC-PROGRESS
PAR-06           REC-PROGRESS
PAR-07           REC-LOCK + REC-PROGRESS
PAR-08..PAR-09   REC-PROGRESS

PLAN-01..PLAN-02 REC-PLAN
PLAN-03          REC-RESTART
PLAN-04          REC-CLASSIFY
PLAN-05          REC-RESTART
PLAN-06          REC-PLAN
```

The registry uses exactly eleven orchestration recipe families.

Each scenario has exactly one primary recipe and optional secondary recipes. A variant requiring a different authority or primary recipe receives a new stable scenario ID rather than being hidden beneath an existing ID.

## Evolution rule

A future mutation or new concurrency guarantee must:

1. update the mutation/predicate analysis in `concurrency-matrix.md`;
2. append or update stable scenario IDs without renumbering existing IDs;
3. update the 21-predicate coverage mapping, introducing a new predicate only when justified;
4. define a primary recipe and any secondary recipe;
5. provide deterministic real-PostgreSQL evidence;
6. keep concrete test-target traceability machine-checkable.

No feature may claim concurrency closure solely from stress testing, a new lock, or a passing functional test.
