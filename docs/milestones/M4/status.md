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

ObjectTemplate is now the selected active review frontier:

```text
family owner
    docs/milestones/M4/wip/objecttemplate.md

current state
    baseline/source map reconstructed
    complete capability census recorded
    public contract review pending capability by capability
```

DataType remains `ACTIVE INPUT` and is intentionally left unchanged until its own family review. Lifecycle remains a separate open historical/audit family.

The ObjectTemplate pass will first close caller-visible contracts — API route, path/query parameters, strict body, omission/null semantics, success output and finite failures — and only then close logical data paths, effective-schema/materialization, cache, cost and concurrency/physical handoffs.

Architecture-wide relational, concurrency and verification closing has not started. All working notes under [`wip/`](wip/) remain non-normative.

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

Review the ObjectTemplate public surface one capability at a time and persist every agreed caller contract in `wip/objecttemplate.md` before descending into technical realization.

The first checkpoint is:

```text
GET /api/v1/core/object-templates
    -> method/route
    -> query parameters and cursor scope
    -> response/page DTO
    -> ordering and empty semantics
    -> finite failures and precedence
```

DataType remains `ACTIVE INPUT`; Lifecycle remains a separate historical/audit review; global architecture closing does not begin implicitly through this family selection.
