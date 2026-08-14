# M1 — API Error & Success Contract

**Status:** DRAFT — API-03.11A/B ratified. Failure classes, concrete public error codes, canonical error details and success HTTP status/body policy are consolidated.

## 1. Scope and authority

This document is the normative API-03.11 authority for mapping transport-neutral application/domain results and failures to the public HTTP/JSON boundary.

The application/domain layer remains HTTP-agnostic:

```text
domain/application result or failure
-> stable transport-neutral result / failure class + code + details
-> HTTP adapter mapping
-> HTTP status + canonical body/headers
```

Domain/application code MUST NOT expose HTTP-specific exception classes as its primary failure semantics.

---

## 2. Failure classes

M1 defines these public mapping classes:

```text
INVALID_REQUEST       -> HTTP 400
NOT_FOUND             -> HTTP 404
SEMANTIC_VALIDATION   -> HTTP 422
STATE_CONFLICT        -> HTTP 409
INTERNAL_FAILURE      -> HTTP 500
```

HTTP status derives from the failure class. A concrete stable `code` identifies the subtype inside that class.

---

## 3. INVALID_REQUEST — HTTP 400

`INVALID_REQUEST` is transport/wire/query/path invalidity that can be determined without interpreting mutable persisted domain state.

Examples include malformed JSON, wrong JSON carrier, unknown/missing/forbidden fields, invalid UUID or positive-integer lexical form, invalid discriminator/static array cardinality, duplicate DATA_CHANGE operation for the same property, and malformed/incompatible cursors.

A malformed `expected_revision` therefore maps to 400.

This failure may be produced entirely by the HTTP transport adapter before an application command is invoked.

---

## 4. NOT_FOUND — HTTP 404

`NOT_FOUND` is reserved for the resource identity selected by the request URI/path.

Examples:

```text
GET /objects/{object_id}
    -> object_id does not exist

POST /datatypes/{datatype_id}/versions/{version}/revise
    -> exact path-target DTV does not exist
```

A resource identifier supplied as a command operand/body reference is not the target URI identity and therefore does not become 404 merely because the referenced resource is absent.

Absent referenced operands belong to `SEMANTIC_VALIDATION` unless a more specific state-conflict rule applies.

---

## 5. SEMANTIC_VALIDATION — HTTP 422

`SEMANTIC_VALIDATION` means the request is syntactically/wire-valid and understood, but its requested semantic candidate/operands are not valid for the domain contract.

Typical examples include required/unknown Object properties, PrimitiveType/DTV constraint violations, invalid DataType constraint combinations, Object CREATE against an abstract lineage, Relationship endpoint lineage incompatibility, wrong-lineage/non-forward SCHEMA_CHANGE targets, ATTACH self-reference and absent referenced command operands.

Rule of thumb:

> if success requires changing the semantic meaning or operands of the request, the failure is normally `SEMANTIC_VALIDATION`.

---

## 6. STATE_CONFLICT — HTTP 409

`STATE_CONFLICT` means the command itself is meaningful, but it cannot currently succeed because of mutable/current persisted state, lifecycle policy, dependency state, concurrency generation or conflicting facts.

Typical examples include stale `expected_revision`, unavailable implicit default, lifecycle/dependency admission failure, default/active-consumer blockers, delete references, qualified-name conflict, RelationshipDefinition equivalence/conflict, ownership conflict/mismatch/cycle and SCHEMA_CHANGE blocked by current values/attachments.

Rule of thumb:

> if the same semantic intent could become valid after current state changes or remediation through existing domain operations, the failure is normally `STATE_CONFLICT`.

### 6.1 expected_revision

```text
malformed/missing expected_revision
    -> INVALID_REQUEST / 400

well-formed but stale expected_revision
    -> STATE_CONFLICT / 409
```

M1 does not reinterpret this as `412 Precondition Failed` and does not introduce ETag/If-Match semantics.

---

## 7. Idempotent convergence is success

A domain-defined idempotent no-op/convergence is not a failure and MUST NOT be mapped to 404/409 merely because no row changed.

Examples:

```text
ATTACH exact edge already current
DETACH exact edge already absent
Relationship CREATE finds existing exact factual view
Relationship DELETE exact id already absent
DATA_CHANGE non-empty request canonicalizes to unchanged semantic state
```

---

## 8. INTERNAL_FAILURE — HTTP 500

`INTERNAL_FAILURE` represents an unexpected server/integrity condition, including persisted state that contradicts M1 invariants and therefore should not be attributable to caller input.

Examples include missing exact dependencies that current invariants require, malformed persisted effective schema, impossible inheritance/runtime closure corruption, incoherent Relationship aggregate/runtime child state and unexpected persistence errors not already translated into a known semantic race/conflict.

The public error body MUST NOT expose SQL text, constraint names, stack traces or sensitive internal diagnostics.

---

## 9. Canonical public error body

All mapped public errors use the flat shape:

```json
{
  "code": "stale_revision",
  "message": "The draft revision does not match the expected revision.",
  "details": {
    "expected_revision": 7,
    "current_revision": 8
  }
}
```

Fields:

```text
code
    required stable machine-readable snake_case code

message
    required human-readable diagnostic
    clients MUST NOT branch on message text

details
    required JSON object
    {} when no structured detail is exposed
    code-specific machine-readable context
```

The body does not duplicate the HTTP status. Request/correlation IDs are infrastructure metadata, not core domain error semantics.

---

## 10. Concrete M1 error-code catalog — API-03.11B

M1 exposes a finite public code catalog. A known M1 failure MUST map to one of these codes; generic `conflict` / `state_conflict` escape-hatch codes are not part of the public contract.

| HTTP | Failure class | `code` | Semantic use |
|---:|---|---|---|
| 400 | INVALID_REQUEST | `invalid_request` | malformed transport/path/query/body shape not covered by a more specific 400 code |
| 400 | INVALID_REQUEST | `invalid_cursor` | malformed cursor or cursor incompatible with route/filter/order identity |
| 404 | NOT_FOUND | `resource_not_found` | request-URI/path target identity is absent |
| 422 | SEMANTIC_VALIDATION | `referenced_resource_not_found` | a referenced command operand/resource is absent |
| 422 | SEMANTIC_VALIDATION | `semantic_validation_failed` | semantic candidate/operand validation failed |
| 409 | STATE_CONFLICT | `stale_revision` | well-formed expected/current DRAFT generation mismatch |
| 409 | STATE_CONFLICT | `lifecycle_state_conflict` | operation is incompatible with the target current lifecycle state |
| 409 | STATE_CONFLICT | `version_source_conflict` | `create-next` source exists but is not currently an eligible source |
| 409 | STATE_CONFLICT | `default_version_unavailable` | an implicit version binding was requested but no current default exists |
| 409 | STATE_CONFLICT | `dependency_not_admissible` | an exact dependency exists but is not currently admissible/PUBLISHED for the requested new binding/certification |
| 409 | STATE_CONFLICT | `qualified_name_conflict` | immutable `(namespace,name)` identity is already occupied |
| 409 | STATE_CONFLICT | `default_version_conflict` | requested lifecycle/default mutation is blocked by the current default pointer |
| 409 | STATE_CONFLICT | `active_dependency_conflict` | lifecycle mutation is blocked by a direct active/PUBLISHED consumer |
| 409 | STATE_CONFLICT | `delete_blocked` | current references/structural facts prevent the requested delete |
| 409 | STATE_CONFLICT | `ownership_slot_unavailable` | requested ATTACH slot is unavailable in the parent's current effective schema |
| 409 | STATE_CONFLICT | `ownership_conflict` | child is already owned by a different owner/slot |
| 409 | STATE_CONFLICT | `ownership_mismatch` | DETACH identifies an edge different from the child's current owner/slot |
| 409 | STATE_CONFLICT | `ownership_cycle` | requested ATTACH would introduce an ownership cycle |
| 409 | STATE_CONFLICT | `schema_change_blocked` | current Object value/attachment state prevents the requested schema migration |
| 409 | STATE_CONFLICT | `relationship_definition_equivalent` | an equivalent RelationshipDefinition already exists |
| 409 | STATE_CONFLICT | `relationship_definition_conflict` | cross-Definition Resolution conflict prevents CREATE/RENAME |
| 409 | STATE_CONFLICT | `relationship_fact_conflict` | runtime closure would collide with a distinct current factual Relationship |
| 500 | INTERNAL_FAILURE | `internal_error` | unexpected invariant/integrity/server failure |

If implementation discovers a supported M1 failure that cannot be represented by this catalog, it is an architecture finding and MUST be resolved in documentation rather than hidden behind a generic conflict code.

---

## 11. `details` contract

`details` is always a JSON object. It provides bounded, code-specific diagnostics and MUST NOT expose raw persistence structure.

### 11.1 `semantic_validation_failed`

May aggregate multiple semantic violations:

```json
{
  "violations": [
    {
      "path": "properties.hostname",
      "rule": "required"
    },
    {
      "path": "properties.memory",
      "rule": "constraint_violation"
    }
  ]
}
```

Each violation has required `path` and stable diagnostic `rule`; optional bounded context may be added where the owning validation contract needs it. The top-level public branching contract remains `code`, not one exception/code per property or constraint rule.

### 11.2 `stale_revision`

```json
{
  "expected_revision": 7,
  "current_revision": 8
}
```

### 11.3 not-found codes

`resource_not_found` / `referenced_resource_not_found` expose the semantic resource type and the known selector fields, for example:

```json
{
  "resource_type": "object_template_version",
  "id": "<uuid>",
  "version": 4
}
```

### 11.4 `delete_blocked`

Expose bounded blocker type/count information, not an unbounded list of every blocker identity:

```json
{
  "resource_type": "object",
  "id": "<uuid>",
  "blockers": [
    {"type": "ownership", "count": 1},
    {"type": "relationship", "count": 3}
  ]
}
```

### 11.5 `schema_change_blocked`

Expose one sufficient semantic blocker diagnostic rather than scanning/serializing every blocker:

```json
{
  "object_id": "<uuid>",
  "target_version": 8,
  "blocker_type": "attachment",
  "member_name": "interfaces",
  "child_object_id": "<uuid>"
}
```

Other conflict codes expose only bounded semantic identifiers/current-state facts needed to understand the conflict. SQL constraint names, table/column details and stack traces are forbidden public details.

---

## 12. Success HTTP mapping — API-03.11B

### 12.1 Reads

All successful GET single/projection/list operations return:

```text
HTTP 200
+ canonical API-03.9 / API-03.10 response body
```

The ratified Object owner zero-cardinality case remains:

```text
existing detached Object
-> HTTP 200
-> JSON null
```

### 12.2 Newly created resources

A newly created public resource returns `201 Created` and a `Location` header identifying its canonical resource URI.

```text
DT.CREATE
    -> 201
    -> command-specific DataType lineage + created v1 DTV result
    -> Location = stable DataType lineage URI

OT.CREATE
    -> 201
    -> command-specific ObjectTemplate lineage + created v1 OTV result
    -> Location = stable ObjectTemplate lineage URI

DT/OT.CREATE_NEXT
    -> 201
    -> created exact-version DTO
    -> Location = created exact-version URI

Object.CREATE
    -> 201
    -> canonical Object DTO
    -> Location = Object URI

RelationshipDefinition.CREATE
    -> 201
    -> complete Definition aggregate DTO
    -> Location = Definition URI

Relationship.CREATE, new factual relationship
    -> 201
    -> factual Relationship DTO
    -> Location = Relationship URI
```

DT/OT CREATE are intentionally command-specific results because one atomic operation creates a stable lineage and its v1 DRAFT. This is not a generic response envelope.

### 12.3 Normal semantic mutation commands

A successful state-changing command normally returns `200 OK` with the resulting canonical semantic resource/projection:

```text
DT REVISE / PUBLISH / DEPRECATE
    -> exact DTV DTO

DT SET_DEFAULT / CLEAR_DEFAULT / SET_DESCRIPTION
    -> DataType lineage DTO

OT REVISE / PUBLISH / DEPRECATE
    -> exact local OTV DTO

OT SET_DEFAULT / CLEAR_DEFAULT / SET_DESCRIPTION
    -> ObjectTemplate lineage DTO

Object RENAME / DATA_CHANGE / SCHEMA_CHANGE
    -> Object DTO

RelationshipDefinition RENAME
    -> complete Definition aggregate DTO

ATTACH
    -> resulting component projection item
```

The public API does not return SQL row counts or generic `{success:true}` / `{changed:false}` bodies.

A valid semantic no-op such as DATA_CHANGE canonicalizing to unchanged state returns the same success status/body shape as the corresponding real mutation.

### 12.4 Relationship CREATE convergence

Relationship CREATE is the collection CREATE whose domain contract explicitly distinguishes creation from convergence:

```text
new factual Relationship
    -> 201 + Location + factual Relationship DTO

existing semantic fact / exact-view convergence
    -> 200 + same factual Relationship DTO
```

Convergence is success and emits no duplicate lifecycle event.

### 12.5 DETACH and DELETE

```text
DETACH real removal
DETACH already-detached idempotent no-op
    -> 204 No Content

successful DELETE primitive
    -> 204 No Content
```

Relationship DELETE additionally preserves its exact-ID idempotent/ABA contract:

```text
Relationship exact id already absent
    -> 204 No Content
```

Other delete operations that target an absent URI identity are not made idempotent by this rule; they follow `resource_not_found` unless their owning domain contract explicitly defines absence as successful convergence.

### 12.6 No asynchronous kernel success

M1 kernel primitives are synchronous transaction-bound operations. API-03 does not expose `202 Accepted`/background-operation semantics.

---

## 13. Decision register — API-03.11A

```text
A3.121 Application/domain failures remain transport-neutral; HTTP mapping occurs only at the transport adapter.
A3.122 M1 public failure classes map as INVALID_REQUEST=400, NOT_FOUND=404, SEMANTIC_VALIDATION=422, STATE_CONFLICT=409, INTERNAL_FAILURE=500.
A3.123 404 is reserved for missing request-URI/path target identity; missing command operands are semantic validation.
A3.124 400 covers transport/wire/query/path malformed input not requiring mutable persisted-state interpretation.
A3.125 422 covers syntactically valid but semantically invalid candidate/operand requests.
A3.126 409 covers meaningful commands blocked by current state/lifecycle/dependency/conflicting facts/stale generation.
A3.127 Malformed expected_revision is 400; well-formed stale expected_revision is 409; no 412/ETag semantics.
A3.128 Domain-defined idempotent no-op/convergence is success and is never converted into conflict merely because no row changed.
A3.129 500 represents unexpected internal/invariant/integrity failure and never exposes SQL/stack/constraint internals publicly.
A3.130 Canonical error body is flat {code,message,details}; code is stable, message human-readable only, details always an object.
A3.131 HTTP status derives from failure class; concrete code identifies the failure subtype.
```

---

## 14. Decision register — API-03.11B

```text
A3.132
M1 exposes the finite concrete error-code catalog defined by API-03.11B;
no generic conflict/state-conflict escape hatch is allowed for known M1 failures.

A3.133
semantic_validation_failed is the deliberate aggregate code for candidate
validation rules; details.violations carries path/rule context without
creating one top-level code per constraint/property rule.

A3.134
resource_not_found is used only for missing URI/path target identity;
referenced_resource_not_found is used for missing command operands.

A3.135
Known lifecycle/default/dependency/ownership/schema-change/Relationship
conflicts use their dedicated 409 codes rather than persistence/SQL errors.

A3.136
internal_error is the only public 500 code in M1 and exposes no internal
persistence/stack information.

A3.137
GET success is 200 with canonical read/list projection.

A3.138
A newly created public resource returns 201 and a Location header.
DT/OT CREATE return a command-specific lineage + v1 result.

A3.139
DT/OT CREATE_NEXT returns 201 with the created exact-version DTO.

A3.140
Relationship CREATE returns 201 when a new factual Relationship is created
and 200 when semantic idempotency converges on an existing one; both return
the same factual Relationship DTO.

A3.141
Successful semantic mutation commands normally return 200 with the resulting
canonical semantic resource/projection, never SQL row counts or generic
success/changed flags.

A3.142
ATTACH returns 200 with the resulting component projection whether newly
attached or exact-idempotent.

A3.143
DETACH returns 204 both after real removal and for the already-detached
idempotent no-op.

A3.144
Successful DELETE returns 204 with no body.
Relationship DELETE additionally returns 204 when its exact ID is already absent,
as required by its explicit idempotent/ABA contract.

A3.145
No 202/async success status exists for M1 kernel primitives.
```

---

## 15. API-03 status

API-03.1..11B are ratified. No HTTP command/read/list/error/success mapping remains open inside API-03.
