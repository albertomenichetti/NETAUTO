# M1 — API Error Contract

**Status:** DRAFT — API-03.11A failure classes, HTTP mapping and canonical error body ratified. Concrete M1 error-code catalog remains API-03.11B work.

## 1. Scope and authority

This document is the normative API-03.11 authority for mapping transport-neutral application/domain failures to the public HTTP/JSON boundary.

The application/domain layer remains HTTP-agnostic:

```text
domain/application result or failure
-> stable transport-neutral failure class + code + details
-> HTTP adapter mapping
-> HTTP status + canonical error body
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

The HTTP status is derived from the failure class. A concrete stable `code` identifies the subtype inside that class.

---

## 3. INVALID_REQUEST — HTTP 400

`INVALID_REQUEST` is transport/wire/query/path invalidity that can be determined without interpreting mutable persisted domain state.

Examples include:

```text
malformed JSON
wrong JSON carrier
unknown field
missing required field
forbidden field
invalid UUID lexical form
invalid positive-integer lexical form
invalid discriminator
invalid static array cardinality
duplicate DATA_CHANGE operation for the same property
invalid cursor lexical/structural form
cursor reused with a different route/filter/order identity
```

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

This rule preserves the API-02 distinction between path command target and command operands.

---

## 5. SEMANTIC_VALIDATION — HTTP 422

`SEMANTIC_VALIDATION` means the request is syntactically/wire-valid and understood, but its requested semantic candidate/operands are not valid for the domain contract.

Typical examples:

```text
required Object property missing
unknown Object property
PrimitiveType/DTV constraint violation
invalid DataType constraint combination
Object CREATE against abstract lineage
Relationship endpoint lineage incompatibility
SCHEMA_CHANGE target from the wrong lineage
SCHEMA_CHANGE target_version <= current_version
ATTACH self-reference
referenced body operand does not exist
```

Rule of thumb:

> if success requires changing the semantic meaning or operands of the request, the failure is normally `SEMANTIC_VALIDATION`.

---

## 6. STATE_CONFLICT — HTTP 409

`STATE_CONFLICT` means the command itself is meaningful, but it cannot currently succeed because of mutable/current persisted state, lifecycle policy, dependency state, concurrency generation or conflicting facts.

Typical examples:

```text
well-formed but stale expected_revision
implicit binding requested while default_version is NULL
exact dependency exists but is no longer admissible/PUBLISHED
publish requested on a non-DRAFT version
deprecate blocked by current default or active consumer
delete blocked by current references
qualified-name uniqueness conflict
RelationshipDefinition semantic equivalence/conflict
ATTACH child already owned by another owner/slot
DETACH child currently owned by a different owner/slot
ownership cycle would be introduced
SCHEMA_CHANGE blocked by current runtime value incompatibility
SCHEMA_CHANGE blocked by current outgoing attachment state
```

Rule of thumb:

> if the same semantic intent could become valid after current state changes or remediation through existing domain operations, the failure is normally `STATE_CONFLICT`.

### 6.1 expected_revision

`expected_revision` remains an application generation token, not an HTTP conditional-header contract.

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

The response/status for these successful operations is defined by the success mapping portion of API-03.11, not by the failure taxonomy.

---

## 8. INTERNAL_FAILURE — HTTP 500

`INTERNAL_FAILURE` represents an unexpected server/integrity condition, including persisted state that contradicts M1 invariants and therefore should not be attributable to caller input.

Examples include:

```text
missing exact dependency that a current FK/invariant requires
malformed persisted effective schema
impossible persisted inheritance/runtime closure corruption
incoherent Relationship aggregate/runtime child set
unexpected persistence error not already translated into a known semantic race/conflict
```

The public error body MUST NOT expose SQL text, constraint names, stack traces or sensitive internal diagnostics.

Operational diagnostics remain server-side observability concerns.

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

The body does not duplicate the HTTP status.

M1 does not make request/correlation IDs part of core domain error semantics; infrastructure may expose correlation metadata separately without changing this contract.

---

## 10. Decision register — API-03.11A

```text
A3.121
Application/domain failures remain transport-neutral; HTTP mapping occurs only at the transport adapter.

A3.122
M1 public failure classes map as:
INVALID_REQUEST=400, NOT_FOUND=404, SEMANTIC_VALIDATION=422,
STATE_CONFLICT=409, INTERNAL_FAILURE=500.

A3.123
404 is reserved for missing request-URI/path target identity.
Missing resources referenced only as command operands map to semantic validation,
not target-resource not-found.

A3.124
400 covers transport/wire/query/path malformed input that does not require mutable persisted-state interpretation.

A3.125
422 covers syntactically valid but semantically invalid candidate/operand requests.

A3.126
409 covers meaningful commands blocked by current mutable state, lifecycle/dependency policy,
conflicting facts or stale application generation.

A3.127
Malformed expected_revision is 400; well-formed stale expected_revision is 409.
M1 does not use 412/ETag semantics for the application revision token.

A3.128
Domain-defined idempotent no-op/convergence is success and is never converted into a conflict merely because no persistence row changed.

A3.129
500 represents unexpected internal/invariant/integrity failure and never exposes SQL/stack/constraint internals publicly.

A3.130
Canonical error body is flat {code,message,details}; code is stable machine-readable snake_case,
message is human-readable only, details is always a JSON object.

A3.131
HTTP status derives from failure class; concrete code identifies the specific failure subtype.
```

---

## 11. API-03.11B remaining work

Still open:

```text
complete concrete M1 error-code catalog
code -> failure-class mapping
details schema per concrete code
success HTTP status/body mapping for create/command/delete/idempotent convergence
```
