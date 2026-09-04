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

M4 has completed the current discovery/revalidation baseline for:

```text
Object
factual Relationship
RelationshipDefinition model plane
```

The remaining model-plane families still classified as active input are:

```text
DataType
ObjectTemplate
```

Their relative review order has not yet been selected and must be chosen explicitly. Lifecycle remains a separate open historical/audit family. Architecture-wide physical, relational, concurrency and verification closing has not started.

The current reviewed directions continue to investigate shifting repeatable immutable-model work away from frequent data-plane operations and into rare model-plane mutation/certification paths, while preserving current semantic and concurrency guarantees. All working notes under [`wip/`](wip/) remain non-normative.
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

Explicitly select the next model-plane family review between DataType and ObjectTemplate, then perform its caller-first, operation-level and cross-family consistency sweep. The other family remains `ACTIVE INPUT` until selected. Lifecycle remains a separate historical/audit review, and global architecture closing does not begin implicitly through this selection.
