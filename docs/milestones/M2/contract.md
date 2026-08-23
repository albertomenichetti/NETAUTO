# M2 — Milestone Contract

**Status:** FINAL / FROZEN

**Authority:** NORMATIVE MILESTONE CONTRACT

**Freeze approval:** Explicitly approved after the PASS consistency closure recorded in `wip/contract-consistency-closure.md`.

## Authority and baseline

M2 starts from the delivered AS-IS in:

```text
docs/architecture/
```

Every delivered guarantee remains authoritative unless this contract explicitly changes it. Any M2 architecture or implementation decision must be traceable to this contract and may choose how to satisfy it, but may not alter its observable behavior, scope, boundaries, required outcomes or acceptance criteria.

This file owns M2 purpose, objectives, capability portfolio, scope, non-goals, explicit AS-IS deltas, required outcomes, acceptance criteria, contract quality gates and freeze/change-control rules. It does not own implementation decomposition or the detailed technical realization assigned to the M2 architecture set.

Discovery sources under `docs/milestones/M2/wip/` are non-normative inputs. This contract is self-contained and does not require those files to be read in order to understand the milestone obligations.

## Purpose

M2 extends the NETAUTO kernel with typed, versioned state for factual Relationships and establishes the first complete operable baseline for installing, validating, observing and using the core through its public interfaces.

M2 does not claim general production maturity beyond the explicit capabilities, guarantees and non-goals defined by this contract.

## Capability portfolio

### In scope

```text
Versioned Relationship property model
Core Health API
NETAUTO CLI
Runtime configuration and production deployment
```

### Cross-cutting foundation

```text
First durable Alembic kernel baseline
```

### Explicitly outside M2

```text
Logging operational review / introduction
```

Logging remains a candidate capability for a future milestone. The existing AS-IS log-level setting remains available, but M2 does not redesign the logging model.

## Objectives

### Objective 1 — Versioned Relationship state

Introduce versioned property schemas for RelationshipDefinitions and canonical typed property state for factual Relationships, using persisted exact schema and DataTypeVersion bindings.

### Objective 2 — Safe Relationship evolution

Provide explicit lifecycle, data-change and forward schema-change capabilities for Relationship schemas and factual Relationships, preserving information when compatible and failing atomically when it cannot be preserved.

### Objective 3 — Preserve the delivered Relationship model

Preserve the delivered stable Relationship topology, Resolution identity, factual uniqueness and deterministic runtime-closure semantics except for the explicit behavioral deltas authorized by this contract.

### Objective 4 — Establish the first durable kernel baseline

Establish one authoritative relational and Alembic baseline for the complete kernel, with exact application/schema compatibility validation and no dependency on disposable pre-baseline database histories.

### Objective 5 — Establish a defined operable runtime

Define a reproducible Linux installation and runtime baseline, including application configuration, PostgreSQL connectivity and pooling, explicit schema realization, runtime readiness observation and ordinary process operation.

### Objective 6 — Provide an official public-API client

Provide an official interactive and non-interactive CLI that operates exclusively through NETAUTO public HTTP interfaces and gives complete command coverage of the public M2 API without introducing an alternative business contract.

### Cross-cutting objective clause

All objectives must preserve every delivered AS-IS guarantee not explicitly changed by this contract and must be supported by observable, deterministic and traceable acceptance evidence.

## Scope

## 1. Versioned Relationship model

M2 introduces `RelationshipDefinitionVersion` as an exact versioned property-schema snapshot owned by a stable `RelationshipDefinition`.

Exact identity is:

```text
(relationship_definition_id, version)
```

The lifecycle is:

```text
DRAFT -> PUBLISHED -> DEPRECATED
```

A DRAFT owns an explicit generation `revision`. PUBLISHED and DEPRECATED versions are immutable snapshots.

Each exact version owns a complete ordered declaration set. Every declaration contains:

```text
name
position
exact DataTypeVersion pin
value_mode = SCALAR | LIST
```

All Relationship properties are optional. A present value is non-nullable. M2 defines no Relationship property create default or migration default.

The stable `RelationshipDefinition` gains:

```text
default_version: integer | null
```

The model-plane public surface includes:

```text
RelationshipDefinition.CREATE
RelationshipDefinition.RENAME
RelationshipDefinition.DELETE
RelationshipDefinition.GET / LIST

RelationshipDefinitionVersion.CREATE_NEXT
RelationshipDefinitionVersion.REVISE
RelationshipDefinitionVersion.PUBLISH
RelationshipDefinitionVersion.DEPRECATE
RelationshipDefinitionVersion.DELETE_DRAFT
RelationshipDefinitionVersion.GET / LIST

RelationshipDefinition.SET_DEFAULT
RelationshipDefinition.CLEAR_DEFAULT
```

`RelationshipDefinition.CREATE` atomically creates the stable Definition, its complete Resolution set and version `1` in `DRAFT` state with revision `1` and the complete initial property-schema candidate. The Definition initially has no default.

The following remain stable Definition-level state and are not copied or versioned inside a RelationshipDefinitionVersion:

```text
symmetry
RelationshipResolution identity and membership
Resolution endpoint ObjectTemplate lineages
Resolution navigation names
```

## 2. Typed factual Relationship state

Every factual Relationship owns:

```text
id
relationship_definition_id
relationship_definition_version
properties
complete deterministic runtime-resolution closure
```

The schema binding is exact, persisted, same-Definition and never floating. Existing facts never follow a changed default.

`properties` is the complete canonical current factual state. Only declarations from the exact pinned RelationshipDefinitionVersion may be present. Unknown properties and JSON null are invalid. Values are validated and canonicalized through the exact DataTypeVersion pins. Optional empty LIST state canonicalizes to property absence.

The public factual surface includes:

```text
Relationship.CREATE
Relationship.DATA_CHANGE
Relationship.SCHEMA_CHANGE
Relationship.DELETE
Relationship.GET
Object-relative Relationship collection
```

### CREATE

CREATE accepts an explicit exact RelationshipDefinitionVersion or deliberately resolves the stable Definition default. The selected version must remain PUBLISHED through commit. Omitted properties mean `{}`; explicit null is invalid.

Factual uniqueness remains defined only by stable RelationshipDefinition and endpoint assignment under the delivered symmetric/non-symmetric semantics. RelationshipDefinitionVersion and property values do not create parallel facts.

A new semantic fact returns `201 Created`. A semantic fact already current returns `409 relationship_fact_conflict`, performs no mutation and emits no lifecycle event.

### DATA_CHANGE

DATA_CHANGE accepts a non-empty set of per-property `SET` and `REMOVE` operations with at most one operation per property. It applies them to fresh current state under the already-pinned exact schema and replaces the complete canonical property snapshot only when semantic state changes.

A semantic no-op succeeds without a persisted update or lifecycle event.

### SCHEMA_CHANGE

SCHEMA_CHANGE selects one explicit exact forward target version of the same RelationshipDefinition. The target must remain PUBLISHED through commit. Migration is direct source-to-target; default, latest, highest and intermediate versions are not consulted.

Compatible values are preserved and canonicalized against the target exact DataTypeVersion. Allowed `SCALAR -> LIST` widening is applied when required. New optional properties remain absent. Source-only properties are removed. If current information cannot be preserved under the target, the entire operation fails with `schema_change_blocked` and leaves source state unchanged.

A valid forward schema change is always a real mutation because the exact pin changes, even when the resulting property map is equal.

### DELETE

DELETE targets one exact `relationship_id`. A current fact is removed with its complete runtime closure and returns `204 No Content`. An absent exact ID returns `404 resource_not_found` and emits no event. Exact-ID ABA safety is preserved.

## 3. Relationship reads and lifecycle

Stable RelationshipDefinition reads expose the complete stable aggregate and `default_version`; versions are not inlined.

Exact RelationshipDefinitionVersion reads expose the complete ordered property declaration set. Version collections expose exact summaries ordered by version and support the defined status filter and keyset cursor.

A Relationship capability is exposed only when the Resolution is topologically applicable and its Definition owns at least one PUBLISHED RelationshipDefinitionVersion. Capability membership does not require a non-null default; `default_version` is exposed separately.

Factual Relationship and Object-relative Relationship projections expose the exact RelationshipDefinitionVersion pin and canonical shared factual properties in addition to the delivered identities and semantic views.

Relationship lifecycle remains part of the single Object-relative lifecycle stream. M2 requires:

```text
RELATIONSHIP_CREATED
RELATIONSHIP_DATA_CHANGE
RELATIONSHIP_SCHEMA_CHANGE
RELATIONSHIP_DELETED
```

Each Relationship event contains historical Object-relative metadata, factual identities and a self-contained factual `before` and/or `after` snapshot containing exactly:

```text
relationship_definition_version
properties
```

A real transition emits exactly one event row per distinct Object-relative semantic view, not per raw runtime-resolution row. A DATA_CHANGE no-op emits no event. A valid SCHEMA_CHANGE emits events even when properties remain equal. The complete event set commits atomically with the factual transition. M2 introduces no separate Relationship timeline.

## 4. Core Health API

M2 introduces the operational endpoint:

```text
GET /health/core
```

The `/health` namespace is separate from `/api/v1/core`.

The response always contains:

```text
app_status
db_status
execution_time_ms
```

Each component status has a required `status = ok | error` and an optional safe controlled message.

HTTP semantics are:

```text
200
    every required component is ok

503
    at least one required component is error
    the complete structured body is still returned
```

The PostgreSQL readiness check executes an active query with a dedicated two-second timeout. Health never exposes raw exceptions, credentials, database URLs, usernames, hosts or other sensitive internals.

Health observes runtime readiness after successful startup. It does not repeat Alembic revision validation and performs no remediation.

## 5. Official NETAUTO CLI

M2 introduces one official CLI with two modes.

### Interactive mode

```text
netauto
```

starts a persistent REPL in:

```text
connection state = DISCONNECTED
output mode      = FORMATTED
```

Required local commands are:

```text
/connect <url>
/disconnect
/status
/output <JSON|FORMATTED>
/help [resource] [operation]
/history
/clear
/exit
```

The REPL provides session history, `Ctrl-R` reverse search and `Ctrl-D` exit on an empty prompt. One command failure does not terminate the REPL.

`/connect` validates an endpoint through `GET /health/core`; only HTTP 200 plus a valid Health response establishes CONNECTED. A failed new connection leaves the session DISCONNECTED and does not restore an old endpoint. `/status` is local while disconnected and revalidates through Health while connected. Business HTTP errors preserve CONNECTED state; transport failure moves the REPL to DISCONNECTED.

### Non-interactive mode

```text
netauto -n <endpoint> <operation...>
```

executes exactly one requested command, never prompts, emits one structured JSON result on stdout and exits zero on success or nonzero on failure. It performs no mandatory Health preflight.

### Coverage and authority

Every public M2 business operation under `/api/v1/core` has a corresponding remote CLI operation. `/health/core` is covered through `/connect` and `/status`; no redundant business-style Health command is required.

The CLI operates exclusively through public HTTP interfaces. It does not invoke application services or persistence directly, does not invent domain identities and never guesses among ambiguous human selectors.

FORMATTED reads may perform additional read-only public HTTP lookups to produce a complete human-oriented representation. A required enrichment failure fails the complete command; no partial representation is presented as complete. Mutations do not perform hidden post-mutation GET enrichment.

JSON mode records every HTTP exchange actually performed by the command in execution order. Non-interactive stdout remains machine-readable JSON on both success and failure; stderr is reserved for process diagnostics outside the structured result.

## 6. Runtime configuration and production deployment

M2 defines a reproducible manual operating baseline for Linux.

Application/runtime configuration includes at least:

```text
database_url
log level
pool_size             default 10
max_overflow          default 20
pool_timeout          default 5 seconds and > 0
pool_recycle          default disabled
pool_pre_ping         default disabled
```

`database_url` is the single NETAUTO authority for the complete PostgreSQL connection specification, including credentials and database transport parameters.

Serving/deployment configuration remains separate and includes:

```text
bind host
bind port
Uvicorn worker count
```

Each worker is an independent process with its own application instance, event loop, SQLAlchemy engine and connection pool. Operational documentation must make the total connection-capacity multiplication explicit.

The canonical distributable artifact is one versioned Python wheel. Installation on a server does not require a Git checkout. The migration environment and complete Alembic graph required by the release ship in the wheel.

The supported operating procedure covers:

```text
install
configure
apply schema explicitly
start
stop
restart
verify readiness
```

Schema migrations never run automatically at application startup. Ordinary orderly shutdown releases runtime resources owned by the process.

## 7. First durable Alembic kernel baseline

M2 establishes the first durable Alembic baseline of the NETAUTO kernel.

One root revision with no predecessor creates directly the complete final relational schema, including the delivered AS-IS guarantees and all M2 extensions. The schema contains exactly fifteen authoritative tables:

```text
Model plane
    datatypes
    datatype_versions
    object_templates
    object_template_versions
    object_template_properties
    object_template_components
    relationship_definitions
    relationship_resolutions
    relationship_definition_versions
    relationship_definition_properties

Data plane
    objects
    object_components
    relationships
    runtime_relationship_resolutions

History
    object_lifecycle_events
```

The root revision creates the final columns, types, PK, UNIQUE, CHECK, FK, CASCADE/RESTRICT actions, explicit indexes, partial predicates, INCLUDE columns and M2 lifecycle vocabulary. SQLAlchemy metadata and the live schema must have zero drift.

The development revision history preceding this durable baseline is not an in-place upgrade source. Pre-baseline development databases are disposable and must be recreated. `alembic stamp` must not be used to relabel an old physical schema as the new baseline.

Supported schema transitions are:

```text
empty database -> head
head -> base
base -> head -> base -> head
```

`head -> base` is destructive for NETAUTO-owned data and structures but must preserve unrelated external structures.

## Cross-capability dependencies

M2 uses a directed dependency graph:

```text
unique Alembic head shipped by the release
    -> exact startup schema guard
    -> HTTP serving permitted

HTTP serving
    -> /api/v1/core
    -> /health/core

/api/v1/core
    -> CLI remote commands

/health/core
    -> interactive CLI /connect and /status
    -> deployment readiness verification

explicit Alembic realization
    -> startup guard
    -> readiness verification
```

Every server worker validates exact equality between the database revision and the unique Alembic head shipped by the running release before entering serving state. An uninitialized, unreachable, older, newer, unknown or indeterminate schema rejects startup. No HTTP endpoint enters serving and no migration is executed automatically.

Health observes runtime readiness only after startup. The interactive CLI uses Health to own its session connection state. Non-interactive commands invoke their requested operation without a mandatory Health preflight.

Deployment requires explicit schema realization, startup validation and readiness verification, but does not require the CLI. The server never depends on the CLI.

## Packaging and release boundary

M2 is distributed as one versioned NETAUTO Python wheel containing:

```text
server runtime
official CLI
complete Alembic environment and graph
required runtime package resources
release version metadata
```

These components share one release version but retain independent runtime responsibilities:

```text
server
    HTTP serving

CLI
    public HTTP client

Alembic
    explicit administrative schema realization
```

The CLI does not initialize the server or database. The server does not require the CLI. Installing the wheel does not apply migrations.

M2 guarantees compatibility between the official CLI and server distributed by the same NETAUTO release. Cross-release CLI/server compatibility is not guaranteed, and M2 defines no version-negotiation protocol or compatibility matrix.

The same wheel may be installed on a server or on an operator workstation used only for the CLI. A CLI-only workstation requires no PostgreSQL access or `database_url`.

## Trust, authentication and authorization boundary

M2 introduces no native authentication, client identity or authorization model.

M2 does not define:

```text
users or accounts
login or logout
API keys or bearer tokens
sessions
roles or permissions
resource-level authorization
401 / 403 application semantics
credential storage in the CLI
external identity-provider integration
```

NETAUTO HTTP surfaces are supported only within an administratively trusted access boundary and must not be exposed directly to untrusted networks. Operators are responsible for restricting reachability through external perimeter controls such as firewall, VPN, reverse proxy, gateway or network policy.

Such controls do not become NETAUTO identity or authorization authorities. M2 does not interpret forwarded identity headers or guarantee integration with external authentication gateways. The official CLI uses no native credential contract in M2.

## TLS and network-security boundary

M2 does not own server-side TLS termination or certificate lifecycle.

The canonical server transport is HTTP within an administratively trusted deployment boundary. Traffic crossing an untrusted network segment must be protected by externally managed TLS termination. Direct unencrypted exposure across such a segment is unsupported.

The official CLI supports `http://` and `https://` endpoints. For HTTPS it performs standard certificate and hostname verification using the administered runtime/system trust store. M2 provides no insecure verification-bypass mode.

NETAUTO does not own certificate issuance, private-key management, rotation, reload, mTLS, pinning or TOFU. Reverse-proxy product selection and configuration remain operator responsibilities and are not M2 compatibility authorities.

PostgreSQL transport security is expressed through the canonical `database_url`, without a second NETAUTO TLS-configuration authority. NETAUTO does not override the driver transport policy and does not expose database connection details through Health or logs.

## Non-goals

## Relationship model non-goals

M2 does not introduce:

```text
versioned Relationship topology or Resolution membership
required Relationship properties
nullable present Relationship values
Relationship property create defaults or migration defaults
normal LIST -> SCALAR narrowing
caller remediation during SCHEMA_CHANGE
automatic factual schema migration
floating binding to default/latest/highest
property- or version-based multi-edge factual identity
runtime property EAV
property-value search API
effective or inherited Relationship schema
standalone property-declaration CRUD
standalone RelationshipResolution CRUD
```

## Lifecycle non-goals

M2 does not introduce:

```text
a separate Relationship timeline
public event-set or transition aggregate
event_set_id or transition_id
a compliance-grade immutable ledger
event sourcing or replay as current-state authority
temporal current-state reconstruction
retention or archive policy
snapshot property search
live history foreign keys
retroactive historical metadata renaming
```

## API and protocol non-goals

M2 does not introduce:

```text
a new business API version
generic query or sorting DSL
offset/page-number pagination
automatic total counts
bulk or batch mutation protocol
generic PATCH semantics
WebSocket, SSE or CDC subscription
generic idempotency-key framework
general ETag / If-Match protocol
cross-request database snapshot tokens
dynamic semantic extension through OpenAPI
```

## Security and network non-goals

M2 does not introduce:

```text
native authentication or authorization
rate limiting or anti-abuse policy
native server certificate management
certificate rotation or reload
mTLS or client certificates
certificate pinning or TOFU
CLI insecure TLS bypass
reverse-proxy or firewall automation
VPN or load-balancer configuration
a separate Health listener
```

## Deployment and platform non-goals

M2 does not provide:

```text
Docker or Kubernetes assets
systemd unit or custom process manager
start-at-boot or automatic restart
service discovery, clustering or high availability
multi-region operation
rolling, blue/green, canary or zero-downtime upgrade
application/schema rollback procedure
artifact registry or transfer automation
CI/CD deployment pipeline
automatic installation or upgrade
```

## Data-protection non-goals

M2 does not provide:

```text
backup or restore automation
point-in-time recovery procedure
PostgreSQL replica management
data-retention policy
disaster-recovery orchestration
business-continuity SLA
```

## Observability non-goals

Beyond the defined Core Health API, M2 does not introduce:

```text
logging redesign or structured logging contract
correlation/request identifiers
distributed tracing
metrics endpoint or Prometheus integration
dashboards or alerting
central log shipping or rotation
compliance audit logs
```

## CLI non-goals

M2 does not introduce:

```text
direct application-service or database access
implicit/default server connection
automatic instance discovery
named persistent connection profiles
mandatory persistence of endpoint or output mode
credential storage
dynamic OpenAPI command generation
CLI plugin framework
custom nested value DSL
domain identities invented for convenience
hidden post-mutation GET
a cross-release compatibility protocol
a granular exit-code taxonomy
a full-screen TUI, macro language or offline mode
```

Persistent history across CLI process restarts is a NICE TO HAVE and not an M2 acceptance requirement.

## Health non-goals

M2 does not introduce:

```text
generic GET /health aggregation
dynamic health registry or plugin health framework
health dependency graph
warning/degraded/unknown state model
metrics or extended diagnostics payload
schema-revision validation inside Health
automatic remediation
readiness checks for future unincluded capabilities
PostgreSQL internal diagnostics
```

## Alembic non-goals

M2 does not support:

```text
M1-to-M2 in-place data migration
preservation or stamping of pre-baseline development databases
dual-schema read/write compatibility
online backfill or expand/contract rollout
automatic migration at startup
conditional downgrade to M1
data-preserving head-to-base downgrade
multiple Alembic heads
```

## Performance and availability non-goals

M2 defines no quantitative throughput, latency, maximum-dataset, horizontal-scaling, benchmark, availability or zero-lock DDL SLA.

This does not relax the required kernel quality baseline: justified indexes, bounded pagination, deliberate query paths, avoidance of preventable N+1 behavior and deterministic concurrency outcomes remain mandatory.

## AS-IS preservation and explicit M2 deltas

## Preserved guarantees

M2 preserves the delivered:

```text
stable RelationshipDefinition topology and symmetry
RelationshipResolution identity, membership and endpoint lineages
mutable Resolution name as non-key metadata
Definition equivalence and cross-Definition Resolution conflict semantics
Relationship factual identity
symmetric/non-symmetric factual uniqueness
self-loop support
exact runtime-view identity
complete deterministic runtime-resolution closure
Object stable-lineage endpoint admission
Object and RelationshipDefinition delete blockers
Object-relative semantic-view deduplication
/api/v1/core business namespace
strict request bodies
failure-class boundary
bounded error details and no SQL/internal leakage
opaque keyset pagination
single-request coherent reads
```

RelationshipDefinitionVersion and property values do not participate in stable topology identity or factual uniqueness.

## Additive M2 surfaces

M2 adds:

```text
RelationshipDefinitionVersion lifecycle and reads
RelationshipDefinition default policy
versioned Relationship property declarations
Relationship.DATA_CHANGE
Relationship.SCHEMA_CHANGE
RELATIONSHIP_DATA_CHANGE lifecycle kind
RELATIONSHIP_SCHEMA_CHANGE lifecycle kind
GET /health/core
official interactive and non-interactive CLI
versioned wheel operating baseline
explicit startup revision guard
first durable Alembic root baseline
```

## Intentional modifications of delivered contracts

### RelationshipDefinition.CREATE

Delivered behavior created the stable Definition aggregate as immediately runtime-usable. M2 creates the stable aggregate plus version `1` as `DRAFT revision 1`, returns both Definition and version and exposes no runtime capability until at least one version is PUBLISHED.

### Relationship capability visibility

Delivered capability visibility depended only on topological applicability. M2 additionally requires at least one PUBLISHED RelationshipDefinitionVersion and exposes `default_version` separately.

### Relationship.CREATE request and response

M2 adds an optional exact `relationship_definition_version` selector and optional complete initial `properties`. Omission of the version resolves the Definition default; omission of properties means `{}`. The resulting projection exposes the exact pin and canonical properties.

### Duplicate Relationship.CREATE

Delivered duplicate CREATE converged successfully on the current fact. M2 returns `409 relationship_fact_conflict`, exposes the current conflicting Relationship identity in bounded details and performs no mutation.

### Relationship.DELETE on absence

Delivered Relationship DELETE returned success when the exact ID was already absent. M2 aligns with Object DELETE: an absent exact target returns `404 resource_not_found` and emits no event.

### Relationship projections

Relationship GET and Object-relative Relationship items add `relationship_definition_version` and canonical factual `properties`.

### Relationship lifecycle

RELATIONSHIP_CREATED and RELATIONSHIP_DELETED add factual before/after state, and M2 adds DATA_CHANGE and SCHEMA_CHANGE Relationship event kinds.

### Stable RelationshipDefinition projection

Stable Definition projections add `default_version`; exact versions remain separate resources.

### Startup behavior

Delivered startup did not require exact Alembic revision equality. M2 rejects serving unless the actual database revision exactly equals the unique head shipped by the release.

### Alembic development history

The disposable development revisions preceding M2 are replaced by one first durable root revision. Old development databases are recreated and are not supported as in-place upgrade sources.

No other observable divergence from the delivered AS-IS is authorized without formal contract reopening.

## Required outcomes

## M2-OUT-01 — Versioned Relationship property schema

Every RelationshipDefinition can own exact versioned property-schema snapshots with an explicit lifecycle, generation revision and complete ordered declaration set, including exact DataTypeVersion pins and SCALAR/LIST modes. Properties are optional, non-nullable when present and have no Relationship migration defaults.

## M2-OUT-02 — Safe version lifecycle and default policy

RelationshipDefinitionVersion lifecycle operations and RelationshipDefinition default-version policy behave consistently with the delivered versioned model patterns, including DRAFT freshness, immutable published snapshots, admissible dependencies, explicit default control and no latest/highest fallback.

## M2-OUT-03 — Exact typed factual Relationship state

Every factual Relationship persists and exposes one exact RelationshipDefinitionVersion binding and one complete canonical property state validated against exact schema and DataTypeVersion pins.

## M2-OUT-04 — Explicit factual Relationship mutations

The public Relationship surface provides explicit creation, data mutation, forward schema migration and exact-identity deletion semantics, including duplicate-fact conflict, no-op DATA_CHANGE behavior, preserve-or-fail SCHEMA_CHANGE and missing-target DELETE failure.

## M2-OUT-05 — Preservation of factual identity and runtime closure

Relationship property state and schema version do not alter stable topology, factual uniqueness, endpoint-lineage admission or deterministic runtime-resolution closure semantics.

## M2-OUT-06 — Complete coherent read projections

Every public Relationship and RelationshipDefinition read exposes the new state through snapshot-consistent projections without floating resolution, silent remediation or partial aggregate/page output.

## M2-OUT-07 — Complete Relationship lifecycle observability

Every real factual Relationship transition produces a complete, self-contained and Object-relative lifecycle event set committed atomically with the transition.

## M2-OUT-08 — Deterministic transactional and concurrency safety

All new and modified model-plane and factual mutations preserve their complete semantic predicates under supported concurrent interleavings, with no lost update, invalid active binding, partial aggregate or partial event set.

## M2-OUT-09 — First durable relational kernel baseline

M2 provides one authoritative relational schema and one root Alembic revision that directly realize the complete fifteen-table kernel baseline, final constraints and final index inventory with zero metadata drift.

## M2-OUT-10 — Exact startup schema compatibility

Every server worker validates exact equality between the database revision and the unique Alembic head distributed by the running release before entering serving state.

## M2-OUT-11 — Core runtime readiness endpoint

M2 exposes one stable Core readiness endpoint that reports bounded application and PostgreSQL runtime readiness with safe diagnostics and a dedicated database timeout.

## M2-OUT-12 — Official complete HTTP CLI

M2 provides one official interactive and non-interactive client for the public HTTP surface of the same NETAUTO release, with complete business-operation coverage and Health-backed interactive connection state.

## M2-OUT-13 — One coherent versioned distribution

M2 is delivered as one versioned Python wheel containing server runtime, official CLI and complete Alembic graph for that release while retaining independent runtime responsibilities.

## M2-OUT-14 — Reproducible Linux operating baseline

M2 defines and verifies a reproducible manual Linux installation, configuration, schema realization, ordinary process operation and readiness-verification procedure.

## M2-OUT-15 — Explicit trust and transport boundary

M2 documents and enforces the limits of its supported access and transport model, including no native auth, trusted-boundary HTTP, external TLS for untrusted segments, verified CLI HTTPS and database transport through `database_url`.

## M2-OUT-16 — Regression, verification and traceability closure

Every M2 outcome and every preserved AS-IS guarantee has complete, deterministic and traceable verification evidence before delivery.

## Acceptance criteria

## M2-AC-01 — Initial Definition version

Creating a RelationshipDefinition creates exactly one stable Definition aggregate and exactly one version `1` in `DRAFT` state with revision `1` and the complete canonical initial property-schema candidate. The Definition initially has no default, the response contains both resources and no runtime capability is exposed before a version is PUBLISHED.

## M2-AC-02 — DRAFT generation lifecycle

CREATE_NEXT, REVISE, PUBLISH and DELETE_DRAFT operate on one exact generation and reject stale or ineligible state without partial modification. CREATE_NEXT clones one eligible exact PUBLISHED/DEPRECATED snapshot into a new DRAFT revision `1`; REVISE performs complete replacement and increments revision once; stale revision returns `stale_revision`; lifecycle-ineligible commands return the defined conflict; a second DELETE_DRAFT returns not found.

## M2-AC-03 — Publication, default and deprecation

Only a complete admissible DRAFT becomes PUBLISHED. First publication establishes the default only when no default exists; later publication does not replace it. The default is null or an exact same-Definition PUBLISHED version. SET_DEFAULT, CLEAR_DEFAULT and DEPRECATE enforce their lifecycle rules; the current default cannot be deprecated; DEPRECATE is irreversible and does not change revision; no latest/highest fallback occurs.

## M2-AC-04 — Property declaration semantics

Every persisted declaration has one exact DataTypeVersion binding and obeys optional, non-nullable and SCALAR/LIST semantics. Explicit or default-based DataTypeVersion selection materializes an exact PUBLISHED pin; explicit null is invalid; absent optional state is valid; present null is invalid; empty optional LIST state canonicalizes to absence. After first publication, name and DataType lineage remain stable, SCALAR-to-LIST is allowed, LIST-to-SCALAR is rejected and remove/re-add does not reset semantic history.

## M2-AC-05 — Model-plane reads and capabilities

Definition GET/list exposes the complete Resolution aggregate and default without inlining versions. Exact version GET returns complete declarations ordered by position. Version list is ordered by version, filters status and maintains cursor identity. A capability exists only with at least one PUBLISHED version, may expose a null default and appears once per Resolution.

## M2-AC-06 — New factual Relationship creation

A valid unoccupied CREATE creates exactly one fact with one exact PUBLISHED RelationshipDefinitionVersion pin, one complete canonical property state and one complete deterministic closure. It returns `201 Created`, exact Location and a projection containing identity, Definition, exact version, properties and distinct views. Explicit and default-based version selection work without latest/highest lookup.

## M2-AC-07 — Duplicate factual creation

A CREATE for an already-current semantic fact returns `409 relationship_fact_conflict`, identifies the current conflicting Relationship in bounded details and produces no state or lifecycle mutation. The loser of equivalent concurrent CREATE follows the same rule after fresh re-evaluation.

## M2-AC-08 — Relationship DATA_CHANGE

DATA_CHANGE applies a non-empty unique-property SET/REMOVE set to freshly loaded complete state and replaces the complete canonical property map only on a real semantic change. Exact version and closure remain unchanged. A real change returns the updated state and emits the complete DATA_CHANGE event set; SET to the same canonical value or REMOVE of an absent property succeeds with no persisted update or event.

## M2-AC-09 — Relationship SCHEMA_CHANGE

SCHEMA_CHANGE moves a fact directly to an explicit forward PUBLISHED version of the same Definition. Compatible continuous values are preserved and canonicalized, SCALAR-to-LIST widening is applied, new optional properties remain absent and source-only properties are removed. An incompatible current value returns `schema_change_blocked` and leaves source state intact. On success version and properties change atomically, closure remains unchanged and an event is emitted even when property maps are equal.

## M2-AC-10 — Relationship DELETE

Deleting a current exact Relationship removes the fact and complete closure atomically, emits one complete deletion event set and returns `204`. Deleting an absent exact ID returns `404 resource_not_found` and emits no second event. A stale delete for an old UUID cannot delete a later equivalent fact with another UUID.

## M2-AC-11 — Relationship read coherence and corruption boundary

Relationship GET and Object-relative Relationship pages observe one coherent committed aggregate. A concurrent mutation is seen entirely before or after, never as mixed pin/properties/header/closure state. Persisted invariant corruption returns `500 internal_error`; no remediation, default fallback or partial page is allowed.

## M2-AC-12 — Exact lifecycle event shapes

Every Relationship lifecycle row decodes through the sole M2 discriminated contract. CREATED has null before and factual after; DATA_CHANGE has same-version, different-property before/after; SCHEMA_CHANGE has forward-version before/after; DELETED has factual before and null after. Each factual snapshot contains exactly version and properties.

## M2-AC-13 — Semantic-view fan-out

A real Relationship transition emits exactly one lifecycle event per distinct Object-relative semantic view independently of raw runtime-row count. Non-symmetric facts, symmetric distinct endpoints, symmetric self-loop and inheritance overlap are covered without duplicate public events.

## M2-AC-14 — Event-set atomicity and historical independence

Factual mutation, closure transition and complete event set commit or roll back together for CREATE, DATA_CHANGE, SCHEMA_CHANGE and DELETE. Event-writer failure leaves no partial transition. Historical events remain decodable after deletion of current Relationship, Definition/version or endpoint Objects and require no current-state lookup.

## M2-AC-15 — DRAFT lost-update prevention

Concurrent commands on one DRAFT generation cannot silently overwrite one another. One command consumes or changes the current generation; the other receives stale or another explicitly defined non-success outcome, with no lost update or hybrid candidate.

## M2-AC-16 — Model admission stability

Publication, default selection, deprecation and exact dependency/binding admission remain valid through commit. No default may point to a non-PUBLISHED version, no PUBLISHED consumer may commit with an inadmissible dependency, the current default cannot be deprecated and no new fact may bind to a version that lost PUBLISHED status in the race.

## M2-AC-17 — Concurrent factual CREATE

Equivalent concurrent CREATE candidates commit at most one fact, one complete closure and one complete creation event set. If the winner remains current, the loser returns `relationship_fact_conflict`. No loser header, closure row or event remains.

## M2-AC-18 — Concurrent factual mutations and deletion

DATA_CHANGE, SCHEMA_CHANGE and DELETE serialize against fresh current factual state for DATA_CHANGE/DATA_CHANGE, DATA_CHANGE/SCHEMA_CHANGE, SCHEMA_CHANGE/SCHEMA_CHANGE, mutation/DELETE and DELETE/DELETE. Two same-ID deletes produce one real transition/event set and one `404` waiter.

## M2-AC-19 — Coherent historical metadata under rename races

A Relationship event set concurrent with Object or Resolution rename contains one complete committed metadata observation: all-old or all-new. Mixed generations or inconsistent metadata across rows of one event set are forbidden.

## M2-AC-20 — Fresh durable schema realization

Applying the unique M2 root revision to an empty PostgreSQL database produces exactly the fifteen-table authoritative schema, one head, expected types and constraints, final lifecycle vocabulary, final indexes including partial predicates and INCLUDE columns, no forbidden JSONB indexes and zero metadata drift.

## M2-AC-21 — Baseline downgrade and repeatability

`head -> base` removes all and only NETAUTO-owned relational structures while preserving an unrelated external sentinel. `base -> head -> base -> head` reproduces the same final schema without residual drift. No populated-M1 upgrade is supported or tested.

## M2-AC-22 — Exact startup revision gate

Every worker serves only when actual database revision exactly equals the unique shipped head. Unreachable database, missing revision table, base/uninitialized database, old, newer, unknown, multiple or indeterminate heads reject startup. No business or Health endpoint serves and no migration executes automatically.

## M2-AC-23 — Core readiness contract

`GET /health/core` returns the complete bounded body on healthy and unhealthy outcomes. Application and DB ok yield `200`; DB error or dedicated two-second timeout yields `503` with complete body. `execution_time_ms` is always an integer. Messages are safe and contain no raw exception, credential, URL or internal detail. Health performs no Alembic check or remediation.

## M2-AC-24 — One versioned distribution

One versioned wheel contains server runtime, official CLI and complete Alembic graph, installs without Git checkout, supports server start, CLI invocation, explicit migration and discovery of the unique shipped head. None of these actions implicitly executes another.

## M2-AC-25 — Interactive CLI state machine

Starting `netauto` opens a persistent REPL in DISCONNECTED/FORMATTED state and supports the complete required local command inventory, session history, Ctrl-R, Ctrl-D exit and continued REPL lifetime after command error.

## M2-AC-26 — Interactive connection behavior

`/connect` establishes CONNECTED only after a valid Health 200; failure leaves DISCONNECTED and does not restore an old endpoint. `/status` performs no request while disconnected and revalidates Health while connected. Business HTTP errors preserve CONNECTED; transport failure clears it.

## M2-AC-27 — Non-interactive CLI contract

`netauto -n` performs one command without prompting, emits structured JSON on stdout and exits zero/nonzero for success/failure. It performs no mandatory Health preflight. Stderr is reserved for process diagnostics outside the structured result. The trace includes all and only exchanges actually performed.

## M2-AC-28 — CLI coverage and authority boundary

Every public M2 business HTTP operation maps to a remote CLI command, and Health is covered through `/connect` and `/status`. The CLI uses only public HTTP, never application services or PostgreSQL, invents no domain identity and rejects ambiguous selectors. Same-release CLI/server compatibility is verified; cross-release compatibility is not promised.

## M2-AC-29 — Linux operating procedure

The installed release can be configured, schema-realized, started, stopped, restarted and readiness-verified on Linux using the documented manual procedure. It covers wheel installation, database URL, pool settings, log level, bind, workers, explicit Alembic, orderly shutdown and Health. Application, serving and secret responsibilities are distinguished, and no Git checkout is required.

## M2-AC-30 — Trust and transport boundary

Documentation and runtime behavior are consistent with no native auth or CLI credential persistence, HTTP only within a trusted boundary, external TLS for untrusted segments, verified CLI HTTPS without insecure bypass and database transport expressed through `database_url`. Deployment examples do not present unprotected universal exposure as a safe default.

## M2-AC-31 — AS-IS regression closure

Every delivered AS-IS guarantee not listed in the explicit delta register remains satisfied, including stable topology, Resolution identity, factual uniqueness, runtime closure, Object lineage admission, failure classes, keyset pagination, bounded errors and no internal leakage.

## M2-AC-32 — Complete outcome traceability

Every M2 Required outcome is owned by at least one normative architecture document and linked to one or more deterministic acceptance criteria and verification scenarios. No outcome, criterion, architecture requirement or preserved guarantee is orphaned or unauthorized.

## Contract quality gates

## M2-CQG-01 — Portfolio closure

Every candidate capability identified for M2 is classified as in scope, cross-cutting foundation, non-goal or future candidate. No unclassified candidate remains.

## M2-CQG-02 — Contract completeness

Every normative section is complete. The contract contains no TBD, TODO, unresolved candidate or open contract point.

## M2-CQG-03 — AS-IS preservation and delta closure

Every delivered AS-IS guarantee is preserved or explicitly changed by the M2 delta register. Any unregistered observable difference is a regression or requires formal reopening.

## M2-CQG-04 — Capability coverage matrix

Every in-scope capability appears in Purpose, at least one Objective, at least one Required outcome and at least one Acceptance criterion. No capability, outcome or criterion is orphaned.

## M2-CQG-05 — Cross-capability dependency closure

The dependency graph is directed, acyclic and assigns one authority to each shared responsibility. Health does not own schema compatibility, CLI is not required by the server, and startup does not run migrations.

## M2-CQG-06 — Boundary and Non-goal consistency

Every Scope statement is compatible with every Non-goal, trust boundary and transport boundary. “Operable” and “production deployment” do not imply excluded security, orchestration, recovery or availability features.

## M2-CQG-07 — Cross-cutting kernel guarantees

Every affected capability preserves exact-version binding, canonical state, atomic complete-aggregate mutation, atomic event sets, coherent reads, bounded diagnostics, no internal leakage, no implicit remediation, deterministic concurrency, single persistence authority, schema compatibility and self-contained history.

## M2-CQG-08 — Architecture-decision handoff

Every intentionally deferred item is classified as architecture or implementation work and may determine how, but not whether or with what observable result, this contract is satisfied.

## M2-CQG-09 — Normative vocabulary and traceability hygiene

The contract uses canonical Relationship terminology and stable `M2-OUT-*`, `M2-AC-*` and `M2-CQG-*` identifiers consistently. Readiness and schema compatibility, event row and event set, exact version and default policy remain distinct concepts.

## M2-CQG-10 — Freeze and change control

After FINAL / FROZEN, any semantic change to Scope, Non-goals, explicit deltas, outcomes or acceptance criteria requires formal contract reopening. Pure editorial correction and traceability enrichment that do not change semantics do not require reopening.

## Final acceptance gate

M2 delivery requires a final acceptance gate distinct from ordinary implementation-slice completion.

The final gate must jointly verify:

```text
all M2-AC criteria
AS-IS regression closure
complete architecture traceability
schema/metadata drift closure
deterministic concurrency evidence
packaging and runtime evidence
absence of blocking findings
```

`steps.md` will decide whether this is realized as a dedicated final slice or as an external gate after all implementation slices. Completion of implementation slices alone does not imply milestone acceptance.

## Architecture handoff

Contract freeze authorizes, but does not complete, M2 architecture design. The architecture set must still close at least:

```text
normative domain and API ownership
complete persistence metadata and codec ownership
complete mutation census and pairwise semantic concurrency matrix
PostgreSQL lock, advisory-gate, retry and deadlock realization
Health and startup-guard realization
CLI grammar, state machine, transport and output realization
runtime configuration and deployment realization
verification and traceability registries
```

These decisions may not alter this contract without formal reopening.

## Open contract points

None.

## Freeze status

The following closure conditions have been satisfied:

```text
Capability coverage                 PASS
AS-IS preservation/delta closure    PASS
Cross-WIP consistency               PASS
Dependency/boundary consistency     PASS
Outcome/acceptance traceability     PASS
Normative hygiene                   PASS
Open contract points                0
Explicit freeze approval            GRANTED
```

This contract is `FINAL / FROZEN`. Architecture design is authorized. Implementation planning remains not started, and implementation remains unauthorized until the complete M2 architecture set is frozen.

## Change-control rule

A formal contract reopening must identify the changed point, explain the cause, repeat the relevant AS-IS and cross-capability checks, update affected outcomes and acceptance criteria, reassess architecture already produced and update milestone status.

The following require reopening:

```text
new capability
new or changed breaking behavior
removal or weakening of an acceptance criterion
changed public response or command semantics
new security model
weakened atomicity, consistency or concurrency guarantee
```

Purely editorial corrections, typo fixes and traceability links that do not change normative meaning do not require reopening.
