# M3 — Milestone Contract

**Status:** DRAFT / REVIEW — NOT FROZEN

**Authority:** PROPOSED MILESTONE CONTRACT — NO IMPLEMENTATION AUTHORITY

## Authority and baseline

M3 starts from the delivered AS-IS in:

```text
docs/architecture/
```

Every delivered guarantee remains authoritative unless this contract explicitly changes it. Any future M3 architecture or implementation decision must be traceable to this contract and may choose how to satisfy it, but may not alter its observable behavior, scope, boundaries, required outcomes or acceptance criteria.

This file owns the proposed M3 purpose, objectives, scope, non-goals, explicit AS-IS deltas, required outcomes and acceptance criteria. It does not own implementation decomposition or detailed technical realization; those belong to the future M3 architecture set and frozen `steps.md`.

Discovery material under `docs/milestones/M3/wip/` is non-normative input. This contract is self-contained and does not require those files to determine the intended M3 obligations.

Until this file is explicitly reviewed and marked `FINAL / FROZEN`, it creates no implementation authority.

## Purpose

M3 simplifies and corrects the public read/client correctness boundary of the delivered kernel without adding new business resources or routes.

The milestone has three purposes:

1. make official CLI create outcomes truthful when the server returns a canonical successful `201 Created` response with the required `Location`;
2. make public GET/read paths project persisted state without re-certifying semantic invariants already owned by mutation paths, while preserving strict request/cursor validation and existing public projections;
3. complete the public ObjectTemplate parent-filter contract with an explicit root-only carrier.

M3 also closes the cursor-identity defects discovered during the read audit and establishes one complete cursor-binding rule across every public paginated route.

## Capability portfolio

### In scope

```text
Official CLI post-create response correctness
Public business GET/read responsibility boundary
Public keyset cursor identity correctness
ObjectTemplate root-only parent filtering
Historical lifecycle read decoding boundary
```

### Explicitly outside M3

```text
new business resources
new public business routes
schema redesign
new Alembic migration
new runtime dependency
runtime lockfile change
general lock-plan redesign
broad mutation-lock minimization
unrelated CLI redesign
```

## Objectives

### Objective 1 — Truthful official CLI create outcomes

A canonical same-release successful create response must be reported as CLI success. Exact `Location` validation remains mandatory; genuine response-contract violations remain structured protocol failures.

### Objective 2 — Correct read responsibility

Public GET/read paths validate request carriers and cursor identity, locate requested targets, compose persisted facts and decode required carriers, but do not re-certify semantic invariants already owned and enforced by mutation paths.

### Objective 3 — Preserve public read behavior

The read simplification must preserve existing public DTOs, filters, ordering, pagination, path-target failure semantics and empty-collection distinctions except for the explicit cursor-identity corrections and ObjectTemplate root-filter carrier added by this contract.

### Objective 4 — Complete cursor query identity

Every public cursor must be bound to the semantic query that produced it, including route, path-scoped collection target, membership-changing filters and any presence bit required to distinguish semantically different queries.

### Objective 5 — Complete ObjectTemplate parent-filter tri-state

The ObjectTemplate lineage list must expose exactly one parent filter, `parent_template_id`, with three public states: omitted, exact UUID and explicit `null`.

### Cross-cutting objective clause

All objectives preserve every delivered AS-IS guarantee not explicitly changed by this contract and require deterministic, traceable acceptance evidence before delivery.

## Scope

## 1. Official CLI `201 Created` correctness

The official CLI continues to validate same-release successful responses against the static operation registry, including exact expected status, response DTO and required `Location`.

The eight registered operations that return `201 Created` remain the same public operation set:

```text
datatype create
datatype create-next
object-template create
object-template create-next
object create
relationship-definition create
relationship-definition create-next
relationship create
```

A valid server response consisting of the registered `201` status, canonical response body and exactly matching `Location` is a CLI success in both interactive and non-interactive execution.

The CLI must support registered `Location` identities that are obtained either from already-resolved request values or from fields nested in the canonical response body. In particular, the existing create response shapes for DataType, ObjectTemplate and RelationshipDefinition remain valid and require no public response flattening.

A server response with missing, repeated, non-materializable or mismatching `Location` remains a same-release protocol violation and is reported as `cli_protocol_error`.

A valid canonical successful response must not become `cli_internal_error` solely because of local post-success `Location` processing.

M3 does not weaken exact `Location` validation and does not add hidden post-mutation GET enrichment.

## 2. Public GET/read responsibility boundary

The delivered public business GET/read surface remains exactly twenty-two routes.

For supported persisted state, a public read owns:

```text
strict request carrier validation
strict cursor validation
path-target existence classification
lookup and composition of persisted facts needed by the public projection
carrier decoding required to construct the typed public response
```

A public read does not own semantic re-certification of invariants already established by mutation paths and persisted as current/history state.

Accordingly, a GET must not fail solely because it re-runs mutation-oriented semantic validation over persisted state, including re-certification of examples such as:

```text
default-version publication admissibility
persisted aggregate domain validation
inheritance admissibility/cycle/agreement rules already owned by mutation
runtime schema/DataType re-resolution used only to prove persisted values again
ownership slot semantic revalidation
factual Relationship Definition/schema/topology certification
lifecycle transition before/after semantic certification
```

This does not require a read to fabricate output from a materially undecodable carrier. Structural or representational state that cannot be decoded into the required typed public response remains an internal failure boundary.

Mutation-path semantic validation remains unchanged in responsibility and must not be weakened merely to simplify GETs.

## 3. Public read behavior preserved

Except for the explicit deltas in this contract, all twenty-two public GET/read routes preserve their delivered:

```text
HTTP route and method
success status
response DTO shape
field meaning
ordering
supported filters
keyset pagination model
limit semantics
strict unknown/repeated query handling
path-target 404 semantics
exact identity semantics
```

Parent/path-scoped collection reads continue to distinguish:

```text
missing path target
    -> 404 resource_not_found

existing path target with no matching children
    -> 200 with an empty page
```

M3 does not introduce offset pagination, total counts, generic sorting/query DSL or cross-request snapshot tokens.

## 4. Historical lifecycle read boundary

The global lifecycle route and Object-scoped lifecycle route retain the existing public discriminated event DTOs, ordering and filters.

Historical persisted carriers are decoded only as required to construct those typed public event projections. Read-time decoding may validate representational requirements such as object shape, required fields and primitive conversions necessary to materialize UUIDs, integers, event kinds and before/after snapshots.

GET-time decoding does not re-certify historical mutation semantics such as:

```text
whether a transition kind was semantically admissible
whether a before/after pair obeys mutation-specific changedness rules
whether a schema-change version increased
whether historical snapshot metadata semantically agrees with current/live state
whether mutation-owned state-family rules can be proved again
```

A materially undecodable historical carrier may still produce `500 internal_error`; a merely semantically non-recertified historical carrier must not fail only because GET replayed a mutation rule.

No current-state lookup is required merely to reinterpret historical event semantics.

## 5. Complete cursor identity contract

M3 keeps opaque keyset cursors and freezes the following public identity rule for every paginated route:

```text
cursor query identity
    = route identity
    + every path target that changes collection membership
    + every active query filter that changes collection membership
    + any presence bit required to distinguish semantically different filter states

cursor position
    = the complete canonical keyset-ordering tuple

limit
    = not part of semantic cursor identity
```

Changing `limit` between pages remains valid. Reusing a cursor with a different semantic query identity returns `400 invalid_cursor`.

The cursor-bearing public route census is exactly:

```text
GET /api/v1/core/datatypes
GET /api/v1/core/datatypes/{datatype_id}/versions
GET /api/v1/core/object-templates
GET /api/v1/core/object-templates/{template_id}/versions
GET /api/v1/core/object-templates/{template_id}/relationship-capabilities
GET /api/v1/core/objects
GET /api/v1/core/objects/{parent_object_id}/components
GET /api/v1/core/objects/{object_id}/relationships
GET /api/v1/core/objects/{object_id}/lifecycle-events
GET /api/v1/core/relationship-definitions
GET /api/v1/core/relationship-definitions/{relationship_definition_id}/versions
GET /api/v1/core/lifecycle-events
```

M3 intentionally corrects two delivered cursor identities:

```text
GET /objects/{parent_object_id}/components
    -> cursor identity includes parent_object_id

GET /objects/{object_id}/relationships
    -> cursor identity includes object_id
```

A cursor issued for one parent Object cannot continue the components page of another parent Object. A cursor issued for one Object cannot continue the Relationship page of another Object.

All other cursor-bearing routes preserve their current semantic identity, including path binding for version/capability collections and `involving_object_id` distinction between global and Object-scoped lifecycle queries.

## 6. ObjectTemplate parent-filter public tri-state

`GET /api/v1/core/object-templates` continues to expose one parent filter only:

```text
parent_template_id
```

Its complete public meaning becomes:

```text
parent_template_id omitted
    -> no parent predicate

parent_template_id=<UUID>
    -> only direct children whose stable parent is that ObjectTemplate

parent_template_id=null
    -> only root ObjectTemplates whose stable parent is null
```

The accepted root sentinel is the exact lowercase query carrier `null`. Empty string, uppercase/special sentinels and malformed UUID values remain invalid request carriers.

Repeated `parent_template_id` remains invalid under the delivered strict query contract.

The official CLI exposes the same tri-state:

```text
parameter omitted
    -> no parent query pair

parent_template_id=<UUID or accepted ObjectTemplate human selector>
    -> normal selector resolution and exact UUID query pair

parent_template_id=null
    -> explicit null query carrier
    -> no ObjectTemplate selector lookup for that value
```

`parent_filter_set` remains an internal representation only and is not added to the public HTTP or CLI contract.

Cursor identity must distinguish omission from explicit root-only filtering even though both may materialize as a nullable typed value internally.

## 7. Read projection and snapshot guarantee

Each public GET response must represent one self-consistent committed projection for that request. M3 does not promise repeatable membership across page requests and does not introduce a cross-request transaction/snapshot token.

The contract does not prescribe SQL statement count, CTE layout, joins, recursive-query shape, helper names or persistence method decomposition. The future M3 architecture must choose a realization that satisfies this public projection guarantee while honoring the read-responsibility boundary above.

## Cross-capability dependencies

The M3 dependency graph is:

```text
public read contract
    -> cursor identity contract
    -> HTTP adapters and official CLI must carry the same query identity

ObjectTemplate parent tri-state
    -> HTTP lexical carrier
    -> official CLI lexical carrier
    -> existing internal filter identity

same-release create contract
    -> static CLI registry
    -> CLI response/Location validation

mutation semantic authority
    -> persisted state
    -> public read projection trusts that semantic certification
```

No M3 capability requires a new persistence schema, migration, route or business resource.

## Non-goals

## Read-path non-goals

M3 does not introduce:

```text
new GET routes
new response fields
new search/filter capabilities except the root-only lexical state of existing parent_template_id
new ordering choices
offset pagination
page numbers
total_count
cross-request repeatable-read guarantees
public corruption diagnostics
read-time remediation/repair
removal or weakening of mutation semantic validation
```

## Cursor non-goals

M3 does not expose cursor internals as a stable client format and does not introduce:

```text
client-authored cursors
cursor introspection API
cursor persistence service
cross-route cursor reuse
cursor compatibility across future releases
limit as a semantic cursor-identity field
```

## CLI non-goals

M3 does not introduce:

```text
new CLI mode
new local command
hidden mutation enrichment GETs
direct application/persistence access
cross-release compatibility negotiation
general renderer redesign
new alternate root-filter syntax
```

## Persistence and platform non-goals

M3 does not require or introduce:

```text
database schema changes
new Alembic revision
new table/index/constraint solely for these changes
new runtime dependency
runtime lockfile change
new deployment capability
new concurrency locking policy for mutations
```

## AS-IS preservation and explicit M3 deltas

## Preserved guarantees

M3 preserves the delivered:

```text
63-operation business HTTP surface
GET /health/core operational surface
official HTTP-only CLI boundary
same-release CLI/server support model
strict request bodies and query validation
finite public error catalogue
bounded error details and no internal leakage
opaque keyset pagination
limit omitted -> 100 and existing accepted range
current public DTO shapes and ordering
exact version identities and persisted exact bindings
mutation semantic validation and atomicity
PostgreSQL schema and Alembic baseline
runtime/deployment model
```

## Intentional modifications of delivered contracts

### Public read corruption/validation boundary

The delivered AS-IS requires public reads to re-certify persisted semantic invariants and fail the representation when such certification fails. M3 narrows that boundary: GETs trust semantic state already admitted by mutation paths and perform only request validation, target lookup, fact composition and representational carrier decoding.

Materially undecodable persisted carriers remain an internal-failure boundary. M3 does not convert GETs into a repair or corruption-tolerance mechanism.

### Object components cursor identity

The Object-components cursor becomes bound to `parent_object_id` in addition to `slot_name` and its route/keyset position.

### Object Relationship cursor identity

The Object-relative Relationship cursor becomes bound to `object_id` in addition to `relationship_definition_id`, `name` and its route/keyset position.

### ObjectTemplate root-only filter

The existing `parent_template_id` filter gains one canonical lexical state: exact lowercase `null`, meaning stable root ObjectTemplates only. Omission continues to mean no parent filter.

### Official CLI create outcome correction

The official CLI must correctly materialize and validate existing registered nested `Location` identities so a valid canonical `201 Created` response is reported as success. This is a correction of delivered implementation behavior while preserving the existing same-release API/CLI response contract.

No other observable divergence from the delivered AS-IS is authorized without formal contract reopening.

## Required outcomes

## M3-OUT-01 — Truthful CLI create success

Every registered canonical `201 Created` response with the expected body and exact `Location` is reported as CLI success, including creates whose Location identity is nested in the response body.

## M3-OUT-02 — Exact CLI protocol failure preservation

Missing, repeated, non-materializable or mismatching `Location` remains `cli_protocol_error`; M3 does not weaken same-release response validation to obtain create success.

## M3-OUT-03 — Read semantic-authority correction

All twenty-two canonical public business GET/read routes stop re-certifying mutation-owned persisted semantic invariants while preserving strict request validation, target lookup and typed projection behavior.

## M3-OUT-04 — Public read compatibility

Public GET success DTOs, filters, ordering, pagination and failure semantics remain compatible except for the explicitly authorized cursor-binding corrections and ObjectTemplate root-only carrier.

## M3-OUT-05 — Complete cursor query identity

All twelve cursor-bearing public routes bind cursors to their complete semantic query identity and complete canonical keyset position. Cross-target and cross-filter cursor reuse is rejected while limit changes remain valid.

## M3-OUT-06 — Historical lifecycle trusted decoding

Lifecycle GETs materialize the existing typed historical DTOs through representational carrier decoding without replaying mutation semantic transition certification.

## M3-OUT-07 — ObjectTemplate root-only public filter

The HTTP API exposes `parent_template_id` as omitted / exact UUID / exact lowercase `null`; the official CLI exposes the same three semantics through omission / UUID-or-human-selector / explicit `null`. Root-only filtering is represented only by `parent_template_id=null`, and cursor identity preserves the distinction from omission.

## M3-OUT-08 — Regression and traceability closure

Every explicit M3 delta and every preserved affected AS-IS guarantee has deterministic verification and normative architecture ownership before delivery.

## Acceptance criteria

## M3-AC-01 — Eight-operation create success coverage

All eight registered `201 Created` operations are exercised against their expected canonical success response and exact Location. The three nested-response identity cases — DataType create, ObjectTemplate create and RelationshipDefinition create — succeed without local exception or `cli_internal_error`. The five flat-token cases remain successful.

## M3-AC-02 — Exact Location protocol failures

For registered `201` operations, missing Location, repeated Location, mismatching Location and an expected Location that cannot be materialized from canonical request/response carriers produce structured `cli_protocol_error`. No such case is silently accepted.

## M3-AC-03 — Interactive and non-interactive create truthfulness

A canonical successful nested-identity create is reported as success in both interactive and non-interactive CLI execution. The observed primary exchange remains in the structured trace and no hidden post-mutation GET is added.

## M3-AC-04 — Twenty-two-route read compatibility

Every canonical public business GET/read route is exercised and preserves its delivered successful DTO shape, field meaning, ordering and supported filter behavior except for the explicit M3 deltas. No route is removed or added.

## M3-AC-05 — Request and path-target failure preservation

Unknown/repeated/malformed request carriers remain rejected under the delivered failure contract. Missing path targets retain `404 resource_not_found`. Existing path targets with no matching collection members retain `200` with an empty page where currently defined.

## M3-AC-06 — No read-side mutation-semantic re-certification

A public GET does not fail solely because a mutation-oriented semantic validator would reject persisted semantic state that the read can otherwise represent. Mutation-path admission and transition validation remain active and unchanged in responsibility.

## M3-AC-07 — Materially undecodable carrier boundary

A persisted carrier that cannot be structurally or representationally decoded into the required typed response may return `500 internal_error`; M3 does not fabricate, repair or partially omit required response state.

## M3-AC-08 — Lifecycle historical decoding

Global and Object-scoped lifecycle reads retain their current public discriminated event shapes, filters and `(occurred_at, id)` descending pagination. Historical carriers are not rejected solely for failing mutation transition rules that are unnecessary to decode the event DTO.

## M3-AC-09 — Complete twelve-route cursor binding

Every one of the twelve cursor-bearing routes rejects a cursor when any semantic membership filter or required path target differs from the issuing query. A cursor with unchanged semantic identity continues successfully even when `limit` changes.

## M3-AC-10 — Object components cross-parent cursor rejection

A cursor issued by `GET /objects/{parentA}/components` is rejected with `400 invalid_cursor` when supplied to `GET /objects/{parentB}/components`, even when all query parameters such as `slot_name` are otherwise equal.

## M3-AC-11 — Object Relationship cross-object cursor rejection

A cursor issued by `GET /objects/{objectA}/relationships` is rejected with `400 invalid_cursor` when supplied to `GET /objects/{objectB}/relationships`, even when `relationship_definition_id` and `name` are otherwise equal.

## M3-AC-12 — Cursor keyset completeness

Every emitted cursor carries a position sufficient to continue the complete canonical ordering of its issuing collection. Pagination produces no omission or duplication attributable to an incomplete keyset position.

## M3-AC-13 — Lifecycle route-scope cursor distinction

A cursor issued by the global lifecycle route is incompatible with the Object-scoped lifecycle route, and cursors from different Object-scoped lifecycle path targets are mutually incompatible. Existing lifecycle filters remain part of cursor identity.

## M3-AC-14 — ObjectTemplate parent-filter HTTP tri-state

`GET /object-templates` with omitted `parent_template_id` does not filter the parent dimension; with a valid UUID it returns only direct children of that parent; with exact lowercase `parent_template_id=null` it returns only stable root ObjectTemplates.

Empty value, malformed UUID, unsupported sentinel and repeated `parent_template_id` return the delivered `invalid_request / 400` class.

## M3-AC-15 — ObjectTemplate parent-filter CLI tri-state

The official CLI supports omission, UUID/human ObjectTemplate selector and explicit `parent_template_id=null`. Explicit null causes no ObjectTemplate selector lookup and emits the canonical HTTP query carrier `parent_template_id=null`.

## M3-AC-16 — Parent-filter cursor identity

ObjectTemplate lineage cursors distinguish unfiltered parent dimension, root-only filtering and each exact parent UUID. A cursor issued for one state is rejected when reused for another, while a root-only cursor continues root-only pagination successfully.

## M3-AC-17 — No persistence/schema/dependency drift

M3 requires no database schema or Alembic revision change, no new runtime dependency and no runtime lockfile change. Final evidence confirms the delivered schema baseline and dependency set remain unchanged unless this contract is formally reopened.

## M3-AC-18 — Complete outcome traceability

Every `M3-OUT-*` outcome is owned by at least one frozen M3 architecture document and linked to deterministic acceptance/verification evidence. No acceptance criterion, architecture requirement or explicit AS-IS delta is orphaned.

## Contract quality gates

## M3-CQG-01 — Scope closure

Every completed discovery workstream is represented in Purpose, Objectives, Scope, Required outcomes and Acceptance criteria. No additional discovery capability is silently promoted into M3.

## M3-CQG-02 — Contract completeness

The frozen contract contains no TBD, TODO, unresolved candidate or open semantic point.

## M3-CQG-03 — AS-IS preservation and delta closure

Every affected delivered AS-IS guarantee is either preserved or explicitly changed in the M3 delta register. Any other observable divergence is a regression or requires formal contract reopening.

## M3-CQG-04 — Cursor rule closure

The cursor contract covers all twelve cursor-bearing public routes, distinguishes semantic query identity from keyset position and explicitly excludes `limit` from query identity.

## M3-CQG-05 — Read-boundary closure

The contract distinguishes request validation, semantic re-certification and representational carrier decoding without requiring GETs to repair undecodable state or weakening mutation validation.

## M3-CQG-06 — Public carrier consistency

HTTP and official CLI define the same ObjectTemplate parent-filter tri-state and do not expose the internal `parent_filter_set` representation.

## M3-CQG-07 — Contract/architecture boundary

The contract freezes observable outcomes and required guarantees without prescribing helper names, store APIs, SQL CTE/UNION shapes, statement count or local code decomposition. Those choices belong to the architecture/implementation layers subject to this contract.

## M3-CQG-08 — Freeze and change control

After `FINAL / FROZEN`, any semantic change to Scope, Non-goals, explicit deltas, outcomes or acceptance criteria requires formal contract reopening. Pure editorial correction and traceability enrichment that do not change meaning do not require reopening.

## Final acceptance gate

M3 delivery requires a final acceptance gate distinct from ordinary implementation-slice completion.

The final gate must jointly verify:

```text
all M3-OUT-* outcomes
all M3-AC-* acceptance criteria
all preserved affected AS-IS guarantees
complete cursor-bearing route census
HTTP / CLI public carrier consistency
read/mutation semantic-authority boundary
historical lifecycle decoding boundary
schema / migration / dependency non-delta
required build / static-analysis / repository verification
complete contract -> architecture -> steps -> implementation -> evidence traceability
no incompatible open finding or stale reopen
```

The exact executable verification matrix is owned by the future frozen M3 architecture/steps and the current verification authority. Performance timing is not a substitute for deterministic correctness evidence.

## Freeze and change control

This draft is not frozen.

Before it may become `FINAL / FROZEN`:

```text
human review of this proposed contract
contract consistency sweep against delivered AS-IS and completed M3 discovery
closure of every contract finding
explicit freeze approval
status.md updated to record the frozen contract gate
```

After freeze, architecture may determine how to realize these obligations but may not add, remove or reinterpret their observable semantics without a formal contract reopen.
