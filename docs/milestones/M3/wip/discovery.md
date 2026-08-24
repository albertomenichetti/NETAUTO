# M3 — Preliminary Discovery Summary

**Status:** WIP / NON-NORMATIVE

**Role:** discovery aid only. This file records current findings and consolidated discovery inputs. It does not define the M3 contract, architecture or implementation authority.

## 1. Purpose and current workstream state

M3 is being explored as a focused kernel-simplification milestone with three bounded problem areas:

1. CLI post-create correctness.
2. Complete audit of all public business GET/read paths.
3. Verification and possible correction of the `parent_template_id = null` filter contract.

Current discovery state:

```text
Area A — CLI post-create correctness          CLOSED
Area B — public GET/read audit                CLOSED / 22 of 22 consolidated
Area C — parent_template_id = null carrier    OPEN
```

The milestone contract must not be frozen until Area C is also closed enough that scope, observable deltas and acceptance criteria are unambiguous.

---

## 2. Area A — CLI post-create correctness — CLOSED

Area A is closed at discovery level.

Detailed decision record:

[`cli-post-create-decision.md`](cli-post-create-decision.md)

Consolidated downstream planning input:

[`cli-post-create-closure.md`](cli-post-create-closure.md)

### Complete finding

The CLI registry contains eight operations with `201 Created` and an exact `Location` contract. Three use nested response-path tokens and are deterministically affected by the current materializer defect:

```text
datatype create                 {datatype.id}
object-template create          {object_template.id}
relationship-definition create  {relationship_definition.id}
```

Five use flat tokens and are not affected by this specific defect:

```text
datatype create-next
object-template create-next
object create
relationship-definition create-next
relationship create
```

The defect is common infrastructure behavior, not a DataType-only defect.

### Root cause and consolidated grammar

The current helper correctly traverses a dotted response path but then passes a mapping keyed by the literal dotted token to `str.format_map()`. Python formatting reinterprets the dot as attribute access and may raise `KeyError` after the valid remote `201` response has already been observed.

The consolidated `Location` token grammar is:

```text
{token}
    -> first resolve token as one exact request-value key
    -> otherwise resolve token as a dot-separated JSON-object path in the canonical response
```

Dots mean JSON-object traversal only. Registered `Location` metadata is not Python format syntax.

The target materializer must perform literal token replacement after resolution and must not use `str.format()` / `str.format_map()` or an equivalent formatter that gives dots another meaning.

### Public behavior to preserve

```text
canonical 201 body + matching Location
    -> CLI success

missing / duplicate / malformed / mismatching / non-materializable Location
    -> cli_protocol_error

canonical 201 body + correct Location
    -> never cli_internal_error because of local Location materialization
```

Exact `Location` validation remains part of the same-release CLI protocol contract and must not be weakened.

### Post-success boundary conclusion

The broader mutation post-success path was audited. Presentation-target construction occurs before the primary request, mutation commands are not subject to FORMATTED enrichment, and no current data-driven mutation-rendering defect was found. Area A therefore remains bounded to the shared `Location` materializer plus static/dynamic registry evidence for all eight `201` operations.

No general renderer redesign is included in M3.

### Candidate acceptance evidence

Later contract/steps should require:

```text
all 8 registered 201 operations covered
all 3 nested response-path templates exercised explicitly
all 5 flat templates retained
correct Location -> success
missing / duplicate / mismatching / unresolvable Location -> cli_protocol_error
valid nested-token success never raises / never yields cli_internal_error
interactive and non-interactive structured outcomes preserved
static registry evidence rejects unsupported Location token syntax
```

No Area A finding requires a schema, migration, dependency or lockfile change.

---

## 3. Area B — Complete GET/read-path audit — CLOSED

### Closure

The repository walkthrough has reviewed all 22 canonical public business GET/read routes:

```text
DataType                  4 / 4
ObjectTemplate            6 / 6
Object                    6 / 6
RelationshipDefinition    4 / 4
Relationship              1 / 1
Global lifecycle          1 / 1
                         ------
                         22 / 22
```

The compact route register is [`get-read-census.md`](get-read-census.md).

The consolidated downstream planning input is [`get-read-review-closure.md`](get-read-review-closure.md).

### Consolidated architectural input

The completed review confirms the following discovery rule:

```text
mutation
    -> validates and preserves semantic invariants

database
    -> preserves structural invariants expressible as constraints / FK

GET / read
    -> validates request/cursor carriers
    -> trusts persisted semantic state
    -> locates, composes and projects persisted facts
    -> performs only carrier decoding required for typed output
    -> does not re-certify semantic invariants already owned by mutation paths
```

The criterion is semantic ownership, not cost. A cheap validation is still outside GET ownership when it merely re-proves persisted state.

### Consolidated statement/snapshot conclusion

The route-by-route review found that every canonical public business GET can be materialized cleanly in one SQL statement.

Therefore the target conclusion is:

```text
22 / 22 public business GET/read routes
    -> one business SQL statement
    -> ordinary statement snapshot / ordinary UnitOfWork
    -> no coherent_read() required
```

This does not deprecate `coherent_read()` as infrastructure and does not apply to non-census workflows that genuinely require a multi-statement coherent snapshot.

### Projection patterns established by the review

Later architecture work should promote and formalize these patterns:

```text
path parent + filtered collection
    -> parent-rooted outer-join/page projection
    -> preserve 404 vs 200 []

exact aggregate + zero-or-many local declarations
    -> one statement without cartesian multiplication

exact inheritance-dependent projection
    -> recursive exact-chain SQL

stable ancestry-dependent capability projection
    -> recursive stable-ancestry SQL

mutation-oriented aggregate validator too broad for GET
    -> dedicated trusted read projector
```

### Persisted-state semantic checks to remove from GET paths

The review identified recurring revalidation patterns that belong to mutation/persistence ownership instead:

```text
default_version -> PUBLISHED certification
persisted aggregate domain validation
inheritance cycle/agreement/admissibility re-certification
runtime schema/DataType re-resolution used only to prove persisted values
ownership slot semantic revalidation
factual Relationship closure/Definition/schema certification
lifecycle before/after transition certification
```

Lookups or joins required to construct response fields remain legitimate projection work.

### Cursor findings

Request and cursor validation remain strict. Two concrete path-binding bugs were discovered:

```text
OBJ-GET-03
    GET /objects/{parent_object_id}/components
    cursor identity must include parent_object_id

OBJ-GET-06
    GET /objects/{object_id}/relationships
    cursor identity must include object_id
```

The lifecycle cursor is already correctly bound to all shared query filters, including `involving_object_id`, so global and object-scoped lifecycle cursors remain distinct.

### Lifecycle decoding conclusion

Lifecycle history requires a distinction between carrier decoding and semantic certification.

Keep only what is materially required to construct typed output from persisted JSONB:

```text
JSON object materialization
field extraction
UUID/string/integer conversion
EventKind materialization
before/after snapshot materialization
```

Remove from GET decoding/projection:

```text
transition correctness checks
before/after mutation-kind semantics
version-increase/change rules
snapshot-vs-outer-row semantic agreement checks
duplicated family/state certification
historical value-admissibility rules not needed merely to decode the carrier
```

A runtime error barrier may remain for a genuinely undecodable carrier, but must not represent semantic re-certification.

### Parent filter finding contributed by the GET review

`OT-GET-01` confirmed that the ObjectTemplate application/persistence layers already support the intended parent tri-state:

```text
filter omitted               -> no parent predicate
filter set + UUID            -> parent_template_id = UUID
filter set + None            -> parent_template_id IS NULL
```

Cursor identity already distinguishes omission from an explicit root-only filter through `parent_filter_set`.

This closes only the internal GET/read portion. The public HTTP/CLI carrier question remains Area C.

### Expected implementation boundary from the GET review

No consolidated GET decision currently requires a database schema, migration, dependency or lockfile change.

Expected later implementation work is confined to read application/persistence/adapter code and regression/statement evidence, subject to frozen architecture and steps.

### Candidate acceptance evidence

The later contract/steps should include evidence that:

```text
all 22 canonical public GET/read routes preserve public success/failure/filter/pagination semantics
OBJ-GET-03 and OBJ-GET-06 cursors are path-bound
parent-scoped collections preserve missing-parent 404 vs existing-parent 200 []
recursive projections preserve expected effective/capability outputs
historical lifecycle output is decoded without semantic re-certification
no public business GET invokes coherent_read() in the target implementation
one business SQL statement materializes each canonical GET/read request
mutation-path semantic validation remains intact
```

Area B requires no further route-by-route discovery unless Area C uncovers a direct conflict with these consolidated decisions.

---

## 4. Area C — `parent_template_id = null` — OPEN

### Current intended shape visible in the implementation

The ObjectTemplate list path carries both:

```text
parent_template_id: UUID | None
parent_filter_set: bool
```

and persistence supports three semantic states:

```text
parent filter absent
    -> do not filter by parent

parent filter present with UUID
    -> parent_template_id = UUID

parent filter present with None
    -> parent_template_id IS NULL
    -> root ObjectTemplates only
```

Cursor identity also records `parent_filter_set`, so omission and an explicit root-only filter are intended to be distinct query identities.

### Suspected public-contract gap

The HTTP route currently exposes `parent_template_id` as `UUID | None` in a query string. A query string does not naturally carry JSON `null`; common lexical forms such as empty string or `null` are not valid UUIDs under the current parser.

Therefore the application/persistence tri-state may include a state that cannot currently be expressed through the public HTTP carrier.

### Required discovery

Verify this with exact public HTTP evidence, including at least:

```text
parameter omitted
valid UUID
empty value
literal "null"
any currently documented/CLI-generated nullable form
unknown/duplicate parameter handling
cursor continuation for each reachable filter state
```

Then determine whether the current architecture already specifies a canonical public representation for "root only". If it does not, this is an architecture/public-contract decision for M3 rather than a local parser fix.

Any correction must be propagated coherently through:

```text
HTTP contract
FastAPI carrier/parsing
application filter identity
cursor encoding/validation
CLI parameter model and examples
API/CLI regression evidence
```

---

## 5. Preliminary scope boundary

M3 discovery remains bounded to the three areas above.

Explicitly not included:

```text
general lock-plan redesign
broad mutation-lock minimization
new business capabilities
new model resources
schema redesign unrelated to the three discovery areas
unrelated CLI redesign
```

Areas A and B are now closed discovery inputs. They do not expand the milestone beyond their consolidated boundaries.

---

## 6. Discovery completion checklist

Before drafting/finalizing the M3 contract:

- [x] reproduce and bound the CLI post-create defect across all relevant create actions;
- [x] define the shared `Location` token grammar and public post-create outcome semantics;
- [x] identify Area A downstream acceptance evidence and scope boundary;
- [x] complete the 22-GET census with read ownership, projection and coherent-read conclusions;
- [x] identify the concrete single-statement target for every canonical public business GET/read route;
- [x] record GET cursor/filter defects discovered by the audit;
- [x] record the lifecycle carrier-decoding vs semantic-certification boundary;
- [ ] verify actual HTTP behavior of `parent_template_id` omission / UUID / null-like inputs;
- [ ] determine whether root-only filtering already has normative wire semantics or requires an explicit M3 decision;
- [ ] map all final proposed deltas from Areas A/B/C to the authoritative AS-IS documents under `docs/architecture/`;
- [ ] convert only closed discovery conclusions into contract outcomes and acceptance criteria.

The next discovery work is Area C. Software implementation remains unauthorized.
