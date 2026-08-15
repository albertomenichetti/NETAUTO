# Codex review-fix prompt — M1-S05

**Status:** NON-NORMATIVE REVIEW-FIX PROMPT.

This execution aid does not override `AGENTS.md`, the frozen M1 contract/architecture/steps, or the ratified technology baseline.

## Assignment

Close only the remaining M1-S05 completion-review verification findings on top of implementation commit:

```text
62857cc0c32b332a0e916ea83bdb2653f69596ab
```

Do not start M1-S06. Do not implement final Object.DELETE. Do not add migrations or change normative architecture.

The reviewer found no production semantic blocker in the S05 kernel/API delta. Preserve the existing implementation unless one of the required deterministic tests exposes a real defect.

## Mandatory pre-flight

Re-read at minimum:

```text
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md
docs/milestones/M1/steps.md
docs/milestones/M1/status.md
docs/milestones/M1/architecture/README.md
docs/milestones/M1/architecture/object-ownership.md
docs/milestones/M1/architecture/object-schema-change.md
docs/milestones/M1/architecture/concurrency-postgresql-realization-object-ownership.md
docs/milestones/M1/architecture/concurrency-postgresql-test-matrix.md
```

The ownership current-edge authority clarification remains frozen: no `slot_declaring_template_id` current-edge column and no historical fallback.

## Accepted review findings / do not duplicate

The existing implementation/review already accepts:

- ROW-12A/B current-state serialization and target admission;
- GATE-01 opposite-edge acyclicity;
- GATE-03A fresh post-gate graph visibility as exercised by the existing GATE-01 interleaving (the waiter can reject the reverse edge only by observing the previous holder's committed edge in the later graph statement);
- GATE-03B post-gate child ownership reread as exercised by the combined ARB-02/GATE-03B test;
- ARB-02 distinct-owner same-child semantics plus direct raw PK authority test;
- ARB-03A identical ATTACH convergence;
- ARB-04 ATTACH × DETACH;
- SNAP-04 child display-metadata observation;
- ATOMIC-04B ownership edge/event rollback (one real edge-add shape is sufficient by the frozen prompt);
- PAR-03 and PAR-04;
- REF-02/REF-05 semantic variants remain deferred to S08 with Object.DELETE under the corrected frozen `steps.md`.

Do not add duplicate tests for accepted cases solely to increase counts.

## Finding 1 — close ROW-13 both serial orders

The current named test proves only:

```text
ATTACH first
-> SCHEMA_CHANGE waiter sees the committed edge
-> target removing the slot is schema_change_blocked
```

Add the reverse deterministic order:

```text
SCHEMA_CHANGE(parent) first while target removes/unavailable slot
-> ATTACH waits on the same parent Object FOR NO KEY UPDATE owner
-> schema change commits if there is no edge yet
-> ATTACH wakes, reloads parent current state, validates against the new exact schema
-> ATTACH fails ownership_slot_unavailable (or the exact frozen semantic failure appropriate to the constructed target)
-> no edge/event commits
```

Use independent semantic UoWs and deterministic blocker evidence (`pg_blocking_pids()` through the canonical harness where blocking is expected). No sleeps.

The test must prove the waiter re-derives from the committed current parent schema, not a pre-wait schema snapshot.

## Finding 2 — close ROW-14 both serial orders

The current named test proves only:

```text
DETACH first
-> removal commits
-> SCHEMA_CHANGE waiter sees removal and succeeds
```

Add the reverse deterministic order:

```text
SCHEMA_CHANGE(parent) first while blocking edge is still current
-> DETACH waits on the same parent Object owner
-> SCHEMA_CHANGE observes the edge and fails schema_change_blocked
-> after the failed transaction releases the parent owner, DETACH proceeds and removes the exact edge
-> parent remains on source version
-> exactly one DETACH_FROM event for the real removal
```

Prove parent-owner blocking with the real PostgreSQL mechanism. DETACH must not acquire the ownership graph gate.

## Finding 3 — ARB-03B identical DETACH

Add the canonical concurrent identical DETACH variant:

```text
initial current edge P/S -> C
T1 DETACH(P,S,C)
T2 DETACH(P,S,C)
```

Required outcome:

- both commands succeed (`204` at HTTP, semantic success at service level);
- exactly one transaction performs the real row removal;
- exactly one `DETACH_FROM` lifecycle event commits;
- the waiter wakes/re-reads and converges as detached no-op;
- final child owner is null/detached;
- no mismatch/conflict is manufactured solely because the other DETACH won.

Use the parent Object owner and deterministic blocking proof; no sleeps.

## Finding 4 — canonical GATE-02A/B coverage

### GATE-02A — longer-cycle candidate

Promote the existing functional longer-cycle behavior into an explicitly traceable real-PostgreSQL canonical scenario (a dedicated T3 test is preferred so scenario identity is not hidden inside a broad API test):

```text
A -> B
B -> C
candidate C -> A
-> ownership_cycle
-> committed graph unchanged/acyclic
```

The candidate must go through the real ATTACH graph-gate/cycle-query path.

### GATE-02B — cycle check × concurrent DETACH path removal

Add the missing concurrent path-removal variant using independent UoWs and deterministic orchestration.

Construct a committed path that makes a candidate ATTACH cyclic, then race:

```text
ATTACH candidate whose cycle predicate depends on that path
×
DETACH removing an edge on the blocking path
```

Allowed serial outcomes are exactly those frozen by PGTEST:

1. ATTACH observes the blocking path before the removal is committed -> conservative `ownership_cycle`; DETACH may then commit.
2. DETACH commits first and the later protected cycle read sees the removal -> ATTACH may succeed if all other admission predicates remain valid.

Forbidden:

- a committed ownership cycle;
- stale-snapshot behavior that commits an edge against a graph state that should have made it invalid;
- DETACH taking the ownership graph gate.

The test should make the ordering deterministic and assert the resulting current graph/event state, not merely command return codes.

## Finding 5 — explicit gate-path regression evidence

The S05 implementation prompt required mechanism evidence that some paths do **not** enter the global graph gate. Current code has the correct early returns, but completion coverage should protect that realization from refactor regressions.

Add a small targeted regression (one parametrized test is fine) proving that `acquire_advisory_gate(OWNERSHIP_GRAPH_WRITE_GATE)` is not reached for:

- exact idempotent ATTACH;
- ATTACH rejected because child already has a different current owner/slot;
- DETACH (real removal and/or detached no-op).

A narrow test-only monkeypatch/interceptor around the real gate seam is acceptable. Do not add production hooks.

Also ensure existing rollback evidence plus the reusable S01 gate foundation remains sufficient to demonstrate transaction-level gate lifetime. Do not duplicate generic advisory-lock foundation tests unless the current suite cannot actually prove the required property.

## Preserve all existing S05 behavior

Do not regress:

- current edge stores only child/parent/slot_name;
- current `SlotSemanticKey` derives from current parent exact effective schema;
- unresolvable current edge -> internal_error;
- no historical slot reconstruction;
- parent Object `FOR NO KEY UPDATE` owner;
- graph gate only for real ATTACH edge-add candidates;
- post-gate child ownership and graph reads are separate fresh statements;
- target OTV `FOR SHARE` held through SCHEMA_CHANGE commit;
- property migration by `(declaring_template_id,name)`;
- no implicit detach/remediation;
- structural lifecycle event shape/atomicity;
- coherent components/owner reads;
- no Object.DELETE/S06+ behavior.

## Verification gates

Run and report:

```text
uv lock (canonical repository lock check)
uv sync --locked
uv build
Ruff format/check
Pyright strict
full non-PostgreSQL suite
full real-PostgreSQL suite on TEST_DATABASE_URL
PostgreSQL server version
```

Specifically report the resulting canonical S05 T3 coverage, including the newly closed:

```text
ROW-13 reverse order
ROW-14 reverse order
ARB-03B
GATE-02A
GATE-02B
```

and the gate-skip regression.

No generic retries, no sleep-based orchestration, no production pause/debug hooks. `status.md` remains reviewer-controlled.