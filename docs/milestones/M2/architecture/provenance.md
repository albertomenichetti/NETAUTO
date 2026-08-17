# M2 WIP Extraction, Provenance and Retirement

**Status:** FINAL / FROZEN

**Authority:** NORMATIVE M2 ARCHITECTURE — FINAL / FROZEN

## 1. Purpose and authority rule

This document proves that every semantic, decision-bearing or technical item recorded under `../wip/` has one final disposition before the M2 architecture freeze.

After the architecture set is frozen, implementation planning and implementation **must not** use `../wip/` as a requirement or design authority.

The implementation authority remains:

```text
delivered AS-IS in docs/architecture/
+
FINAL / FROZEN docs/milestones/M2/contract.md
+
FINAL / FROZEN docs/milestones/M2/architecture/
+
ratified project-wide decisions in docs/general/technology_baseline.md
```

`../wip/` is retained only as historical discovery and review evidence. When WIP text conflicts with a later frozen decision, the later normative authority wins. A WIP statement absent from the authority composition above is not an implementation requirement.

## 2. Complete WIP disposition map

| WIP file | Classification | Final normative destination | Disposition |
|---|---|---|---|
| `relationship-properties.md` | semantic/API discovery | `relationship.md`, `api.md`, frozen `contract.md` | Core topology/version/property/factual/API decisions absorbed. The early lossless M1→M2 bridge is superseded by the first durable baseline. |
| `relationship-properties-persistence.md` | persistence discovery | `persistence.md`, `concurrency.md`, `verification.md` | Authorities, schema, lifetime, pipelines and reads absorbed. Uniform default-pointer validation is made explicit in `persistence.md`. |
| `relationship-properties-lifecycle.md` | lifecycle discovery | `persistence.md`, `api.md`, `verification.md` | Codec, fan-out, metadata, event-set and DTO decisions absorbed. Historical M1 backfill is superseded. |
| `relationship-properties-indexes.md` | index/access-path discovery | `persistence.md`, `verification.md` | Final index inventory, replacements, FK support and negative index contract absorbed. M1 backfill sequencing is superseded. |
| `relationship-properties-alembic-baseline.md` | durable-baseline decision | `persistence.md`, `runtime-deployment.md`, `verification.md` | One root/one head, fresh realization, exact guard, downgrade isolation and old-chain removal absorbed. |
| `health-api.md` | Health discovery | `health.md`, `api.md`, `runtime-deployment.md`, `verification.md` | Route, readiness, statuses, timeout and separation from schema compatibility absorbed; exact probe refined to `SELECT 1`. |
| `netauto-cli.md` | CLI discovery | `cli.md`, `api.md`, `health.md`, `runtime-deployment.md`, `verification.md` | Modes, state, grammar, selectors, output, errors, help and coverage absorbed. Cross-session history is deliberately rejected for M2. |
| `runtime-configuration-production-deployment.md` | runtime/deployment discovery | `runtime-deployment.md`, `health.md`, `verification.md` | Settings, pool, secret, wheel, startup, Linux and trust boundaries absorbed and refined to installed-release execution. |
| `cli-stack-10-proposal.md` | technology proposal | `docs/general/technology_baseline.md` `STACK-10`, plus `cli.md` and `runtime-deployment.md` consequences | Ratified; proposal retired as evidence. |
| `contract-consistency-closure.md` | contract review evidence | frozen `contract.md` | No implementation authority; records the completed contract gate. |
| `architecture-consistency-closure.md` | architecture review evidence | `architecture/README.md` and all owners | No implementation authority; records set-level closure. |
| `persistence-transaction-deadlock-cross-check.md` | review evidence with findings | `persistence.md`, `concurrency.md`, `verification.md` | Differential replacement, target-before-owner and root-delete gate absorbed. |
| `concurrency-matrix-cross-check.md` | review evidence with findings | `concurrency-matrix.md`, `verification.md` | `VH`, `RS`, RF/RA deltas and clone lifetime absorbed. |
| `concurrency-postgresql-cross-check.md` | review evidence with findings | `concurrency.md`, `verification.md` | Central LockPlan, gates, modes, order, retry budget and no-`40P01` policy absorbed. |
| `health-architecture-cross-check.md` | review evidence with findings | `health.md`, `runtime-deployment.md`, `verification.md` | Same pool, full two-second deadline, safe failure and no mutation-graph entry absorbed. |
| `cli-architecture-cross-check.md` | review evidence with findings | `cli.md`, `runtime-deployment.md`, `verification.md`, `STACK-10` | Static registry, neutral transport DTOs, nested selectors and bounded enrichment absorbed. |
| `runtime-deployment-architecture-cross-check.md` | review evidence with findings | `runtime-deployment.md`, `verification.md` | Embedded runtime lock, package migrations, exact head and direct installed executables absorbed. |
| `verification-architecture-cross-check.md` | review evidence with findings | `verification.md`, `architecture/README.md` | T0–T10, 32 bundles, 83 scenarios and freeze/evidence gate separation absorbed. |
| `stack-10-ratification-cross-check.md` | technology review evidence | `docs/general/technology_baseline.md` | No implementation authority; records successful ratification. |

Census:

```text
discovery / decision sources       8
project-wide technology proposal   1
review / closure evidence         10
                        --
total WIP documents               19
classified                        19 / 19
unclassified                       0
```

## 3. Explicit supersession register

The following earlier WIP positions are deliberately **not** propagated as final requirements:

```text
lossless in-place M1 -> M2 database migration
synthetic RDV v1 PUBLISHED/default/current-fact backfill
historical M1 Relationship event snapshot backfill
transitional nullable columns, dual decoders and progressive FK replacement
M1-aware or data-preserving downgrade
migration-time replacement-index sequencing for populated M1 data
persistent cross-session CLI history
source-project/checkout-based production launch through `uv run`
prompt_toolkit as an unratified candidate
Health query left unspecified
startup schema guard location left open
CLI process argument order and JSON trace shape left open
```

Their final replacements are, respectively:

```text
first durable empty-database root baseline
M2-native v1 DRAFT creation semantics
M2-only lifecycle shapes from fresh schema
single final DDL and index inventory
head -> base destructive isolated verification only
no legacy backfill phase
in-memory process history only
installed versioned release environment and direct executables
ratified STACK-10
exact `SELECT 1` probe
pre-serving same-engine exact-head guard
frozen `netauto -n <endpoint-root> <resource> <operation> ...` and trace schema
```

## 4. Technical extraction closure

The final owners contain the complete decision-bearing material required by subsequent phases:

```text
Relationship semantics and lifecycle          relationship.md
public routes, carriers and failures          api.md
relational schema, codec, indexes and DDL      persistence.md
pairwise semantic interleavings               concurrency-matrix.md
PostgreSQL locking, gates and retry            concurrency.md
Core readiness execution                      health.md
official HTTP client                          cli.md
settings, artifact, startup and operation      runtime-deployment.md
evidence and traceability                      verification.md
project-wide CLI technologies                  technology_baseline.md / STACK-10
```

The detailed audit record is `../wip/wip-extraction-closure.md`.

Result:

```text
WIP files classified                         PASS — 19 / 19
semantic decisions propagated                PASS
technical decisions propagated               PASS after persistence closure additions
superseded decisions explicitly retired      PASS
review findings owned normatively             PASS
implementation dependency on WIP              0
open extraction finding                       0
contract reopening                            NOT REQUIRED
```

## 5. Freeze and change control

This document is frozen together with the complete architecture set. Adding a new WIP document after freeze does not modify architecture authority. Any new semantic or technical requirement must formally reopen and amend the appropriate frozen contract or architecture owner before implementation can rely on it.
