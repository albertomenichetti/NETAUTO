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
Area A — CLI post-create correctness          OPEN
Area B — public GET/read audit                CLOSED / 22 of 22 consolidated
Area C — parent_template_id = null carrier    OPEN
```

The milestone contract must not be frozen until Areas A and C are also closed enough that scope, observable deltas and acceptance criteria are unambiguous.

---

## 2. Area A — CLI post-create correctness — OPEN

### Observed defect

A DataType `create` operation was observed to complete successfully on the remote HTTP API (`201 Created`, persisted resource, valid `Location`) while the CLI subsequently returned a local `cli_internal_error`.

The current evidence indicates the failure occurs after remote success while processing the command registry `Location` template. The DataType create spec uses a dotted placeholder form such as:

```text
/api/v1/core/datatypes/{datatype.id}
```

while the local lookup/materialization path does not resolve that template consistently.

### Discovery objective

Do not treat this only as a one-line DataType fix. Audit every command that performs local processing after a successful remote create response, especially every registry `location` template and the common code that resolves it.

### Candidate requirement to validate for the contract

A remotely successful and committed mutation must not be reported as a semantic failure solely because local CLI response decoration, rendering or `Location` materialization fails afterward.

The exact CLI behavior for an unexpected local post-success failure still needs to be designed and frozen; discovery must first identify the complete affected command set and common mechanism.

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

Area B requires no further route-by-route discovery unless Areas A or C uncover a direct conflict with these consolidated decisions.

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

Area B findings are now closed discovery input; they do not expand the milestone beyond read simplification, cursor correctness and the shared lifecycle decoder boundary discovered during that audit.

---

## 6. Discovery completion checklist

Before drafting/finalizing the M3 contract:

- [ ] reproduce and bound the CLI post-create defect across all relevant create actions;
- [x] complete the 22-GET census with read ownership, projection and coherent-read conclusions;
- [x] identify the concrete single-statement target for every canonical public business GET/read route;
- [x] record GET cursor/filter defects discovered by the audit;
- [x] record the lifecycle carrier-decoding vs semantic-certification boundary;
- [ ] verify actual HTTP behavior of `parent_template_id` omission / UUID / null-like inputs;
- [ ] determine whether root-only filtering already has normative wire semantics or requires an explicit M3 decision;
- [ ] map all final proposed deltas from Areas A/B/C to the authoritative AS-IS documents under `docs/architecture/`;
- [ ] convert only closed discovery conclusions into contract outcomes and acceptance criteria.

The next discovery work should address Areas A and C. Software implementation remains unauthorized.
