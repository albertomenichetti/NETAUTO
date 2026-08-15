# Codex implementation prompt — M1-S02

**Status:** NON-NORMATIVE IMPLEMENTATION PROMPT.

This file is an execution aid for Codex. It does not override `AGENTS.md`, the frozen M1 contract/architecture/steps, or the ratified technology baseline.

## Assignment

Implement exactly:

```text
M1-S02 — PrimitiveType and DataType vertical slice
```

from `docs/milestones/M1/steps.md`.

M1-S00 and M1-S01 are complete. Do not implement M1-S03 ObjectTemplate semantics or any later Object/ownership/Relationship capability.

## Mandatory pre-flight

Before changing files, read and obey:

```text
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md
docs/milestones/M1/contract.md
docs/milestones/M1/architecture/README.md
docs/milestones/M1/steps.md
docs/milestones/M1/status.md

docs/milestones/M1/architecture/datatype.md
docs/milestones/M1/architecture/persistence-model.md
docs/milestones/M1/architecture/persistence-uow-concurrency.md
docs/milestones/M1/architecture/concurrency-semantic-matrix.md
docs/milestones/M1/architecture/concurrency-postgresql-realization-matrix.md
docs/milestones/M1/architecture/concurrency-postgresql-test-matrix.md
docs/milestones/M1/architecture/api-contract.md
docs/milestones/M1/architecture/api-wire-contract.md
docs/milestones/M1/architecture/api-read-contract.md
docs/milestones/M1/architecture/api-list-contract.md
docs/milestones/M1/architecture/api-error-contract.md
```

Confirm from the repository itself that:

```text
M1 contract      = FINAL / FROZEN
M1 architecture  = globally FROZEN as a set
M1 steps         = FINAL / FROZEN
M1-S00           = COMPLETED
M1-S01           = COMPLETED
current step     = M1-S02
STACK-01..09     = RATIFIED
```

The S02 pre-flight API gap has been closed normatively in `api-error-contract.md`: DT.CREATE returns literal public fields `datatype` and `version`; OT.CREATE later uses `object_template` and `version`.

If normative authorities conflict, stop the affected work and report the contradiction instead of choosing one. Do not use historical implementation from Git history as a template.

## Objective

Deliver a complete usable M1 PrimitiveType + DataType vertical capability:

```text
plain-Python primitive/domain semantics
-> DataType application operations
-> explicit async PostgreSQL UoWs/locking
-> canonical persistence
-> public HTTP/JSON routes
-> read/list/cursor/error mapping
-> deterministic tests, including real PostgreSQL concurrency
```

A caller must be able to define, version, revise, publish, choose defaults, deprecate, read/list and delete allowed DataType state through `/api/v1/core` with one canonical primitive semantics path.

## Hard scope boundary

S02 MUST NOT implement:

```text
ObjectTemplate public/domain operations
ObjectTemplate effective-schema resolution
Object runtime operations or lifecycle events
ownership ATTACH/DETACH semantics
RelationshipDefinition or Relationship semantics
/api/v1/core/object-templates routes
/api/v1/core/objects routes
/api/v1/core/relationship-definitions routes
/api/v1/core/relationships routes
JSON Schema compiler/projection
ORM Session / AsyncSession
generic repository framework
generic command bus / service container
background jobs / 202 semantics
Docker/Testcontainers/DB provisioning
```

It is valid for DataType deprecation/delete safety to query the already-existing physical ObjectTemplate tables because active/reference authority exists physically from S01. That does not make ObjectTemplate a delivered S02 capability.

## 1. PrimitiveType domain authority

Implement one plain-Python, framework-independent primitive parser/canonicalizer/validator authority for the closed catalog:

```text
core.string
core.integer
core.number
core.boolean
core.date
core.datetime
core.ip
core.ip_prefix
core.byte_size
```

Domain code must not depend on FastAPI, Pydantic or SQLAlchemy.

Use standard-library semantics where frozen:

```text
re            -> pattern compile + re.fullmatch semantics
Decimal       -> exact-decimal / exact byte conversion authority
calendar/date -> Gregorian date validation
absolute datetime -> strict lexical parse, offset required, canonical UTC Z
ipaddress     -> IP/IP-prefix semantics; prefix host bits rejected
```

Do not implement a second validation language or compile to JSON Schema.

### Canonical primitive rules

Preserve the frozen behavior, including:

- string identity; no trim/lowercase/business normalization;
- integer is an exact JSON integer and Python bool is never accepted as integer;
- number public input is exact-decimal string only, no exponent/plus/NaN/Infinity; canonical exact-decimal string, negative zero -> `"0"`;
- boolean is actual boolean only;
- date is strict zero-padded `YYYY-MM-DD` in supported Gregorian range;
- datetime requires `Z` or explicit offset, rejects leap second, never rounds, converts to canonical UTC `Z`; digits after microsecond precision are accepted only when all excess digits are zero;
- IP is address only, no CIDR/zone identifier, canonical address string;
- IP prefix requires explicit CIDR/prefix length and rejects host bits rather than correcting them;
- byte size accepts non-negative integer bytes or the strict SI/IEC quantity-string contract and canonicalizes to exact non-negative integer bytes.

All constraint values, enum members, future Object values and future migration defaults must be able to reuse this same authority.

## 2. DataType constraint model

Implement exactly the M1 matrix:

```text
core.string      min_length, max_length, pattern, enum
core.integer     minimum, maximum, enum
core.number      minimum, maximum, enum
core.boolean     enum
core.date        minimum, maximum, enum
core.datetime    minimum, maximum, enum
core.ip          ip_version, enum
core.ip_prefix   ip_version, enum
core.byte_size   minimum, maximum, enum
```

Reject unsupported keys, malformed values and direct contradictions such as minimum > maximum / min_length > max_length.

`pattern` is a Python regex string: validity via `re.compile`, value matching via `re.fullmatch`.

`enum` is semantically an unordered finite set. Pipeline:

```text
raw member
-> primitive parse/validate
-> canonicalize
-> duplicate detection after canonicalization
-> validate against every other active constraint
-> canonical member
```

Persist/expose a deterministic canonical enum representation so semantically identical input order does not create distinct stored candidate state. Do not introduce a general satisfiability solver.

Constraint state is a canonical JSON-compatible object suitable for the existing JSONB column. `core.number` constraint values remain canonical decimal strings; byte-size values canonical integer bytes; datetime canonical UTC strings, etc.

## 3. DataType application/domain operations

Implement all S02 operations:

```text
CREATE
CREATE_NEXT
REVISE
PUBLISH
SET_DEFAULT
CLEAR_DEFAULT
DEPRECATE
DELETE_DRAFT
DELETE_LINEAGE
SET_DESCRIPTION
```

Preserve all DT-INV-001..020.

### CREATE

Atomically create:

```text
stable DataType lineage
+
v1 DRAFT
```

with application/kernel-generated DataType UUID, version 1, revision 1, DRAFT status, chosen immutable base_type and canonical constraints. `constraints` omission at HTTP create means `{}`. Initial default is null. `core` / `core.*` namespaces are reserved from the public/user admission path.

Translate qualified-name arbitration to the frozen semantic/public failure; never expose raw UNIQUE details.

### CREATE_NEXT

- path lineage is the stable target;
- `source_version` is an exact body operand;
- source must exist in same lineage and be PUBLISHED or DEPRECATED, never DRAFT;
- source need not be max version;
- acquire the stable lineage owner before deciding current version allocation;
- after lock wait, re-read current set/source eligibility;
- new version is `max(existing)+1`, DRAFT revision 1;
- clone source base_type + canonical constraints exactly;
- no `derived_from` persistence/semantic field.

### REVISE

- exact path target must exist;
- required positive `expected_revision` query token;
- exact DRAFT non-key owner `FOR NO KEY UPDATE`;
- re-check DRAFT status + current revision after owner acquisition;
- complete constraints replacement, not patch;
- successful revise increments revision by exactly one;
- base_type cannot change.

### PUBLISH

Use canonical ordering/ownership from the persistence contract:

```text
lineage header FOR NO KEY UPDATE
-> exact DRAFT FOR NO KEY UPDATE
-> fresh status/revision checks
-> publish
-> if default_version is null, set this first serially published version as default
```

Publish does not increment revision. Publishing another version must not replace an existing default.

### SET_DEFAULT / CLEAR_DEFAULT

SET_DEFAULT:

```text
lineage header FOR NO KEY UPDATE
-> target exact version FOR SHARE
-> recheck target PUBLISHED
-> set exact version
```

CLEAR_DEFAULT locks the lineage owner and sets null. No fallback/default-to-highest semantics exist.

### DEPRECATE

Use:

```text
lineage header FOR SHARE
-> exact target FOR NO KEY UPDATE
-> fresh lifecycle/default checks
-> direct active consumer lookup
```

Only PUBLISHED can transition to DEPRECATED. Current default blocks deprecation. A direct PUBLISHED ObjectTemplateVersion property consumer blocks deprecation even though ObjectTemplate commands are not implemented until S03; query the authoritative physical rows/indexes already present. DRAFT/DEPRECATED consumers do not block.

Do not introduce a reverse-dependency cache/table.

### DELETE_DRAFT

Canonical order:

```text
lineage header FOR NO KEY UPDATE
-> exact DRAFT FOR UPDATE
-> fresh status/revision checks
-> delete
```

Only DRAFT can be individually deleted and `expected_revision` is required.

### DELETE_LINEAGE

- path target missing -> normal URI-target not-found semantics;
- root lineage row `FOR UPDATE` is whole-aggregate owner;
- precheck external references for bounded semantic `delete_blocked` diagnostics;
- current cross-aggregate FKs remain final race authority;
- internal default pointer must not block whole-lineage delete: clear/neutralize the internal default pointer within the same UoW as needed before deleting the root/cascaded versions;
- operation is atomic and returns no body.

### SET_DESCRIPTION

Description is nullable non-semantic metadata with atomic last-write-wins behavior and no lineage revision token. Do not manufacture optimistic concurrency for it. Preserve the intentional concurrency topology from PAR-07.

## 4. Transport-neutral failure boundary

Application/domain code must remain HTTP-agnostic.

Implement only the small shared failure/result machinery needed now, but make it reusable by later slices. S02 must correctly produce/map the frozen codes it can exercise, including as applicable:

```text
invalid_request
invalid_cursor
resource_not_found
referenced_resource_not_found
semantic_validation_failed
stale_revision
lifecycle_state_conflict
version_source_conflict
default_version_unavailable
dependency_not_admissible
qualified_name_conflict
default_version_conflict
active_dependency_conflict
delete_blocked
internal_error
```

Do not invent generic `conflict` or expose SQL constraint/table names.

Known semantic validation failures should use `semantic_validation_failed` with bounded `violations` details rather than one public error code per primitive constraint.

## 5. DataType persistence/UoW

Use the S01 `AsyncEngine`, `UnitOfWorkFactory`, authoritative Core metadata and READ COMMITTED transaction semantics.

Do not use ORM Session/AsyncSession.

Persistence code owns SQL/query construction; application/domain code does not import SQLAlchemy objects.

One semantic mutation = one UoW. No repository/helper commits independently.

Preserve exact lock strengths and fresh post-lock reads from REALIZE-02..07 / REALIZE-15. Do not replace all locks with `FOR UPDATE`.

Translate expected PostgreSQL arbitration/FK conditions to known semantic failures only where the frozen operation contract assigns such convergence/conflict meaning. Unexpected integrity failures become internal invariant failures, not leaked SQL errors.

## 6. DataType read/query capability

Implement canonical reads:

```text
GET /api/v1/core/datatypes/{datatype_id}
GET /api/v1/core/datatypes/{datatype_id}/versions/{version}
```

Use exactly API-03.9 lineage and exact-version DTO shapes. Constraints in exact reads are canonical and `{}` for zero constraints.

Implement collections:

```text
GET /api/v1/core/datatypes
GET /api/v1/core/datatypes/{datatype_id}/versions
```

Contract:

```text
{ "items": [...], "next_cursor": string|null }
limit omitted=100, valid 1..500
opaque keyset cursor only
no offset/page/sort API
lineage order = (namespace, name) ASC
version order = version ASC
lineage exact filters = namespace, name
version exact filter = status
DTV list summary omits constraints
```

Each page is independently snapshot-consistent. Cursor is route/filter/order-specific, not a snapshot or domain identifier. Implement the smallest explicit versioned/validated cursor encoding; do not add a cursor secret/key setting or crypto framework unless a frozen requirement demands it.

## 7. Public FastAPI routes

Implement exactly the DataType inventory under `/api/v1/core`:

```text
POST   /datatypes
POST   /datatypes/{datatype_id}/create-next
POST   /datatypes/{datatype_id}/versions/{version}/revise
POST   /datatypes/{datatype_id}/versions/{version}/publish
POST   /datatypes/{datatype_id}/set-default
POST   /datatypes/{datatype_id}/clear-default
POST   /datatypes/{datatype_id}/versions/{version}/deprecate
DELETE /datatypes/{datatype_id}/versions/{version}
DELETE /datatypes/{datatype_id}
POST   /datatypes/{datatype_id}/set-description

GET    /datatypes
GET    /datatypes/{datatype_id}
GET    /datatypes/{datatype_id}/versions
GET    /datatypes/{datatype_id}/versions/{version}
```

No PATCH/PUT and no alternate qualified-name identity route.

### Strict request DTOs

Use Pydantic 2.x only at the HTTP boundary. Request models must be strict, forbid unknown fields, reject generic scalar coercion and preserve omission-vs-explicit-null semantics.

Transport may validate carrier/static lexical shape, but PrimitiveType/domain code remains semantic/canonicalization authority. Do not duplicate primitive business/constraint validation in Pydantic.

`expected_revision` is a required positive-integer query parameter only for REVISE, PUBLISH, DELETE_DRAFT. Missing/malformed is 400; well-formed stale is 409.

### Success response contract

Use exact frozen results:

```text
DT.CREATE
    201 + Location=/api/v1/core/datatypes/{id}
    body = {
      "datatype": <canonical DataType lineage DTO>,
      "version": <canonical exact v1 DTV DTO>
    }

DT.CREATE_NEXT
    201 + exact-version Location
    body = exact DTV DTO

REVISE / PUBLISH / DEPRECATE
    200 + exact DTV DTO

SET_DEFAULT / CLEAR_DEFAULT / SET_DESCRIPTION
    200 + DataType lineage DTO

DELETE_DRAFT / DELETE_LINEAGE
    204, no body

GET/list
    200 + canonical read/list body
```

`datatype` and `version` are literal public fields for DT.CREATE. This is command-specific composition, not a generic response envelope.

## 8. Composition

Wire the DataType application capability into the existing explicit process composition. FastAPI `Depends()` may expose already-composed HTTP/application capability where useful, but must not own the semantic UoW transaction boundary and must not become the kernel DI container.

Do not run migrations at startup. Keep import-time side effects absent.

## 9. Required tests — primitive/domain

Add exhaustive examples for frozen lexical/canonical edge cases and constraint combinations, including at least:

- integer vs bool rejection;
- decimal lexical grammar, equivalent canonical forms and negative zero;
- non-finite/exponent/leading-plus rejection;
- date invalid calendar values/bounds;
- datetime offset requirement, UTC conversion, >6 fractional digits zero-only rule, no leap second/no rounding;
- IPv4/IPv6 canonicalization;
- IP prefix host-bit rejection and no netmask aliases;
- byte size SI vs IEC, case sensitivity, optional single ASCII space, exact fractional conversion, exponent/plus/negative rejection;
- regex compile/fullmatch behavior;
- unsupported constraint keys;
- min/max contradictions;
- enum duplicate-after-canonicalization;
- enum member vs other-constraint validation;
- canonical constraint/enum idempotence.

Use targeted Hypothesis properties for meaningful pure properties such as canonicalization idempotence/round-trip and exact numeric/byte-size domains. Do not use property tests as a substitute for frozen examples.

## 10. Required tests — application/API/PostgreSQL

Cover every DataType command success and every relevant failure family.

Real PostgreSQL verification is mandatory through the external `TEST_DATABASE_URL`. With one DB URL, run PostgreSQL tests serially with respect to xdist.

Verify at least:

- persistence round-trip of canonical constraints;
- atomic CREATE lineage+v1;
- version allocation/gap/max-DRAFT reuse semantics;
- revision freshness and lifecycle immutability;
- first-publish auto-default and subsequent-publish stability;
- set/clear default;
- deprecate default blocker;
- deprecate direct PUBLISHED raw physical OTV consumer blocker, without implementing OT commands;
- DRAFT/DEPRECATED physical consumers do not block deprecate;
- individual DRAFT delete;
- whole-lineage deletion + external FK blocker + internal default non-blocking;
- description LWW behavior;
- strict API body/query shapes, omission/null semantics, Location headers/statuses;
- read/list DTOs, filters, order, keyset continuation, cursor/filter mismatch -> `invalid_cursor`;
- public errors contain only bounded semantic details and no SQL internals.

## 11. Deterministic PGTEST coverage in S02

Use the S01 harness and stable scenario IDs. Do not rename canonical IDs.

Implement the DataType-realizable coverage required by the frozen S02 step, including:

```text
ROW-01  CREATE_NEXT × CREATE_NEXT same lineage
ROW-02  CREATE_NEXT × DELETE_DRAFT(max)
ROW-03  REVISE × REVISE same DRAFT generation
ROW-04  exact DRAFT terminal races (DataType variants applicable)
ROW-05  PUBLISH(vA) × PUBLISH(vB), default null
ROW-06  SET_DEFAULT(v) × DEPRECATE(v)
ROW-15  SET_DESCRIPTION × SET_DESCRIPTION
ROW-16  REVISE × DELETE_LINEAGE same aggregate
ARB-01  CREATE × CREATE same qualified name
PAR-06  DEPRECATE(v1) × DEPRECATE(v2), same lineage
PAR-07  description/header topology (SET_DESCRIPTION×SET_DEFAULT and SET_DESCRIPTION×REVISE)
```

For `ROW-07` / `ROW-08`, implement the reusable DataType exact/implicit binding-admission primitive required by the frozen architecture where it naturally belongs, including exact `FOR SHARE` and implicit lineage `FOR SHARE` -> default -> exact `FOR SHARE` fresh validation. Exercise the canonical scenario in S02 only if it can be proven through the real capability without manufacturing a fake semantic consumer. Otherwise report the DataType-side mechanism as implemented and leave the full cross-domain committed-reference scenario explicitly for S03. Never claim PGTEST coverage using a mock/fake consumer.

`ROW-09` / `ROW-10` active-consumer races require the actual ObjectTemplate semantic operations and belong to S03; do not simulate them here.

All concurrency tests:

- real PostgreSQL;
- independent connections/transactions;
- deterministic blocker/barrier orchestration;
- `pg_blocking_pids()` for positive blocker proof where required;
- no sleep correctness orchestration;
- timeouts only as safety nets;
- assert allowed outcome sets/forbidden states rather than arbitrary winner scheduling.

## 12. Quality gates

Run and report at least:

```text
uv lock
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -m "not postgresql"
uv run pytest -m postgresql
```

If you use narrower commands during development, the final report must still include the full S02 applicable gates.

Do not mark S02 `COMPLETED`; completion is a review decision after the pushed delta and verification evidence are inspected.

## Completion report

At the end provide:

- commit SHA and confirmation pushed to `origin/core_review`;
- concise files/layers added/changed;
- PrimitiveType implementation structure and canonicalization authority;
- DataType operation/persistence/API structure;
- exact PGTEST IDs implemented and any explicitly deferred cross-domain variants with rationale;
- all verification commands/results and PostgreSQL version;
- any Ruff/Pyright suppression, retry, test hook or unusual workaround (preferably none);
- any architecture/documentation contradiction found;
- confirmation no S03+ capability or JSON Schema was implemented;
- confirmation `status.md` was not marked completed by Codex.
