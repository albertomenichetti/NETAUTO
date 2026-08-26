# M4 — Milestone Status

**Milestone status:** ACTIVE — BOOTSTRAP / DISCOVERY

**Authority:** OPERATIONAL CYCLE STATUS

## Cycle identity

```text
cycle          M4
cycle type     milestone
source branch  M4
target branch  master
```

## Current operational state

```text
phase                       BOOTSTRAP / DISCOVERY
contract                    NOT INITIALIZED / NOT FROZEN
architecture set            NOT INITIALIZED / NOT FROZEN
implementation steps        NOT INITIALIZED / NOT FROZEN
implementation              NOT AUTHORIZED
final acceptance            NOT APPLICABLE
active software cycle       M4
software implementation     FORBIDDEN
blockers                     design gates not yet established
```

M4 is open only for discovery and design bootstrap. The current delivered AS-IS under `docs/architecture/` remains the semantic authority until M4 defines and freezes an explicit TO-BE delta.

No software, schema, migration, dependency, persistence, concurrency or public-contract modification is authorized in the current phase.

## Current discovery focus

The initial exploration is evaluating whether NETAUTO can reduce the runtime cost of the existing REST operation surface by moving repeatable immutable-model work out of frequent data-plane operations and into rare model-plane mutation/certification paths.

Current investigation areas include, without yet making them architecture decisions:

- denormalized/materialized stable ObjectTemplate ancestry;
- denormalized/materialized exact ObjectTemplateVersion ancestry;
- durable effective-schema materialization or equivalent compiled model representations;
- worker-local caching restricted to information that does not require distributed cache-coherency protocols;
- operation-by-operation re-evaluation of SQL reads, traversal, lock planning and transaction duration;
- preservation of current semantic and concurrency guarantees while allowing existing M2/M3 realization mechanisms to be reconsidered where M4 explicitly redesigns them.

The working notes and hypotheses are non-normative and live under [`wip/`](wip/).

## Design gates

| Gate | State |
|---|---|
| Discovery / problem framing | IN PROGRESS |
| Contract | NOT INITIALIZED |
| Architecture set | NOT INITIALIZED |
| Implementation steps | NOT INITIALIZED |
| Implementation | NOT AUTHORIZED |
| Final acceptance | NOT APPLICABLE |

Implementation can start only after the project-governance sequence is satisfied:

```text
contract FINAL / FROZEN
    -> architecture set FROZEN
    -> steps FINAL / FROZEN
    -> status explicitly authorizes implementation
```

## Immediate next action

Continue bounded discovery of the current REST operations, starting from concrete hot-path cases and recording current cost, mutable/immutable dependencies, concurrency guarantees and candidate optimization directions before drafting the M4 contract.
