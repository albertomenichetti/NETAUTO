# M3 — Public GET / Read Review Closure

**Status:** CONSOLIDATED DISCOVERY INPUT / NON-NORMATIVE

**Role:** closure record and downstream planning input for the M3 review of the 22 canonical public business GET/read routes.

This document does not authorize implementation and does not replace the future M3 contract, architecture set or implementation steps. It captures the conclusions that have been explicitly reviewed and consolidated during discovery so those later artifacts can consume one stable input rather than reconstructing decisions from the route-by-route walkthrough.

## 1. Closure statement

The public GET/read review is complete:

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

All 22 routes have an explicit discovery disposition.

The consolidated target conclusion is stronger than the preliminary discovery hypothesis:

```text
all 22 public business GET/read routes
    -> can materialize their complete public projection in one SQL statement
    -> therefore do not require coherent_read() in the M3 target model
```

This is a discovery conclusion to be promoted into the M3 contract and architecture only after the other M3 discovery workstreams are closed and the normal freeze gates are followed.

## 2. Consolidated read-ownership rule

The review converged on this ownership boundary:

```text
mutation paths
    -> validate semantic candidates
    -> preserve semantic invariants
    -> own admissibility and transition rules

database
    -> preserves structural invariants expressible by PK / FK / UNIQUE / CHECK

GET / read paths
    -> validate request carriers and cursor identity
    -> locate path targets
    -> compose persisted facts needed by the public projection
    -> decode persisted carriers into typed output
    -> do not re-certify semantic invariants already owned by mutation paths
```

The distinction is semantic, not performance-driven. A cheap semantic re-check is still outside GET ownership if it merely re-proves a persisted invariant.

## 3. Consolidated snapshot rule

`coherent_read()` remains a valid infrastructure capability, but the completed census found no canonical public business GET that still needs it after the target projection is expressed correctly.

Target rule:

```text
one SQL statement describes the complete public read projection
    -> use ordinary UnitOfWork / statement snapshot

multiple statements exist only because persistence is fragmented
    -> compose the read into one statement instead of retaining coherent_read()
```

No target decision requires weakening coherent snapshot semantics for workflows that genuinely need them outside this public GET census.

## 4. Route matrix

| ID | Public read | Consolidated target |
|---|---|---|
| `DT-GET-01` | `GET /datatypes` | remove default-pointer revalidation; existing one-statement lineage page |
| `DT-GET-02` | `GET /datatypes/{id}` | remove default-pointer revalidation; one lineage lookup + 404 |
| `DT-GET-03` | `GET /datatypes/{id}/versions` | one parent-rooted statement preserving parent 404 vs empty page |
| `DT-GET-04` | `GET /datatypes/{id}/versions/{version}` | keep existing one-statement exact read |
| `OT-GET-01` | `GET /object-templates` | remove default-pointer revalidation; preserve application/persistence parent tri-state |
| `OT-GET-02` | `GET /object-templates/{id}` | remove default-pointer revalidation; project persisted parent directly |
| `OT-GET-03` | `GET /object-templates/{id}/versions` | one lineage-rooted statement preserving 404 vs empty page |
| `OT-GET-04` | `GET /object-templates/{id}/versions/{version}` | one exact-target statement for header + local properties + local components |
| `OT-GET-05` | `GET /object-templates/{id}/versions/{version}/effective-schema` | one recursive exact-chain statement + trusted projection; no read-side declaration/inheritance certification |
| `OT-GET-06` | `GET /object-templates/{id}/relationship-capabilities` | one recursive stable-ancestry capability page; preserve capability-membership `EXISTS(PUBLISHED ...)` semantics |
| `OBJ-GET-01` | `GET /objects` | keep existing one-statement list projection |
| `OBJ-GET-02` | `GET /objects/{id}` | remove transitive runtime-schema/DataType semantic certification; one object lookup + 404 |
| `OBJ-GET-03` | `GET /objects/{parent}/components` | bind `parent_object_id` into cursor identity; one parent-rooted exact-chain component projection |
| `OBJ-GET-04` | `GET /objects/{child}/owner` | one child-rooted ownership + exact-slot projection; no persisted slot/parent re-certification |
| `OBJ-GET-05` | `GET /objects/{id}/lifecycle-events` | one target-object + lifecycle-page statement; trusted historical carrier decoding only |
| `OBJ-GET-06` | `GET /objects/{id}/relationships` | bind `object_id` into cursor identity; one target-object + runtime relationship-view page; remove `_validated_many()` |
| `RD-GET-01` | `GET /relationship-definitions` | remove definition/default semantic certification; keep one-statement aggregate page |
| `RD-GET-02` | `GET /relationship-definitions/{id}` | remove definition/default semantic certification; one aggregate lookup + 404 |
| `RD-GET-03` | `GET /relationship-definitions/{id}/versions` | one parent-rooted statement preserving 404 vs empty page; remove default-pointer certification |
| `RD-GET-04` | `GET /relationship-definitions/{id}/versions/{version}` | one parent-rooted exact-version + properties statement; preserve parent-vs-version 404 classification |
| `REL-GET-01` | `GET /relationships/{id}` | dedicated one-statement read projector from factual relationship + runtime resolutions + resolution names |
| `LC-GET-01` | `GET /lifecycle-events` | keep existing one-statement page; ordinary UoW; trusted historical carrier decoding only |

## 5. Projection patterns to carry into architecture

### 5.1 Parent identity + filtered collection

Used by version lists and path-scoped collections that must distinguish:

```text
path target absent
    -> 404

path target present, no matching children
    -> 200 with empty collection
```

Preferred shape:

```text
parent/root relation
LEFT JOIN filtered/keyset child page
```

Child filters and cursor predicates belong in the join/subquery that materializes the child page, not in an outer predicate that would erase the parent-only row.

### 5.2 Exact aggregate with zero-or-many local declarations

Used by exact ObjectTemplateVersion and RelationshipDefinitionVersion projections.

The target statement must preserve the exact target even when its local declaration collection is empty. Avoid cartesian multiplication between independent child collections. Typed `UNION ALL`, independent aggregation or equivalent one-statement shapes are valid realizations.

### 5.3 Recursive exact inheritance projection

Where the public response depends on exact pinned inheritance, use recursive SQL following persisted exact parent pins. The query composes persisted facts; it does not re-certify cycles, parent agreement or declaration admissibility on read.

### 5.4 Recursive stable ancestry projection

Relationship capabilities depend on stable ObjectTemplate ancestry. The ancestry is part of the projection, but persisted graph semantic certification is not. Capability membership requiring at least one PUBLISHED RelationshipDefinitionVersion remains a query-membership rule, not a revalidation rule.

### 5.5 Dedicated read projectors

Do not globally weaken aggregate/domain loaders that mutation workflows use for semantic validation merely to simplify GETs.

Where a GET needs a materially smaller trusted projection, introduce a read-specific persistence projector. `REL-GET-01` is the clearest example: the public Relationship view can be projected directly from factual/runtime persisted state without invoking the mutation-oriented `_validated()` aggregate certification path.

## 6. Cursor and request conclusions

Request validation and persisted-state semantic validation are separate concerns. The review preserves strict request/cursor validation.

Two concrete cursor-identity defects were found:

```text
OBJ-GET-03
    current cursor identity omits parent_object_id
    target must include parent_object_id

OBJ-GET-06
    current cursor identity omits object_id
    target must include object_id
```

The lifecycle cursor already binds every filter carried by the shared query, including `involving_object_id`; therefore object-scoped and global lifecycle cursors remain distinct.

The `parent_template_id = null` public carrier question is explicitly not closed by this review. `OT-GET-01` confirmed only that application and persistence already support the intended tri-state and that cursor identity already carries `parent_filter_set`. HTTP/CLI wire expressibility remains the separate Area C discovery workstream.

## 7. Historical lifecycle decoding boundary

The lifecycle review established a reusable distinction:

```text
carrier decoding — KEEP
    JSON object materialization
    required field extraction
    UUID/string/integer conversion required to construct typed output
    EventKind materialization
    before/after snapshot materialization

semantic certification — REMOVE FROM GET
    transition correctness
    before/after change-kind rules
    version-increase rules
    snapshot identity/name agreement with outer columns
    duplicated event family/state-shape checks already owned by persistence constraints/mutations
    historical runtime-value admissibility rules not required merely to decode the carrier
```

The HTTP `_event()` projection must likewise choose the DTO from the already-decoded event kind rather than re-checking persisted `before`/`after` admissibility. An exhaustiveness/programmer guard is distinct from persisted-state certification and may remain if required by typing.

A `RuntimeError` barrier may remain for a materially undecodable historical carrier; it must no longer be the vehicle for semantic re-certification failures.

## 8. Public semantics that must be preserved

The GET simplification is not permission to relax the public read contract. Later contract/architecture/steps must preserve at least:

```text
request validation
unknown/duplicate query handling already defined by the public adapter
path-target 404 semantics
parent-target 404 vs existing-parent empty collection distinctions
exact composite identity semantics
status/name/template filters
keyset ordering and limit + 1 pagination
cursor route/filter identity
current DTO field shape and deterministic ordering
root-only parent tri-state inside application/persistence
lifecycle descending (occurred_at, id) keyset semantics
```

Supported persisted state should continue to produce the same successful public representation except for the explicitly identified cursor-identity fixes.

## 9. Expected implementation surface

The review currently requires no database schema, migration, dependency or lockfile change.

Expected software touchpoints, once implementation is authorized, are bounded to read application/persistence/adapter code and tests, principally:

```text
src/netauto/application/datatypes.py
src/netauto/application/objecttemplates.py
src/netauto/application/objects.py
src/netauto/application/relationshipdefinitions.py
src/netauto/application/relationships.py

src/netauto/persistence/datatypes.py
src/netauto/persistence/objecttemplates.py
src/netauto/persistence/objects.py
src/netauto/persistence/relationships.py
src/netauto/persistence/lifecycle.py

src/netauto/entrypoints/api/objects.py
```

This is a planning inventory, not implementation authority. Exact file changes remain subject to the frozen architecture/steps.

## 10. Candidate acceptance evidence for later freeze

The GET/read workstream should not be considered implemented merely because existing happy-path API tests pass. The eventual frozen plan should require evidence for the consolidated decisions, including:

```text
all 22 canonical public GET/read routes exercised
public success/404/filter/pagination behavior preserved
OBJ-GET-03 rejects a cursor issued for a different parent object
OBJ-GET-06 rejects a cursor issued for a different object
path-parent collection reads preserve 404 vs 200 []
exact-version projections correctly handle zero local declarations
recursive projections preserve expected effective/capability outputs
lifecycle global/object-scoped cursor identities remain distinct
historical lifecycle decoding accepts persisted carrier state without semantic re-certification
no public business GET invokes coherent_read() in the target implementation
statement evidence demonstrates one SQL statement per canonical public GET/read request path, excluding transport/framework metadata not part of the business read
mutation-path semantic validation remains intact
```

Statement-count evidence should be route-focused and deterministic; it should not rely on elapsed-time performance as a proxy for query shape.

## 11. Traceability

The compact 22-route register is [`get-read-census.md`](get-read-census.md).

Detailed decisions recorded after the original census stopped growing are retained as route-specific discovery evidence:

```text
ot-get-04-decision.md
ot-get-05-decision.md
ot-get-06-decision.md

obj-get-01-decision.md
obj-get-02-decision.md
obj-get-03-decision.md
obj-get-04-decision.md
obj-get-05-decision.md
obj-get-06-decision.md

rd-get-01-decision.md
rd-get-02-decision.md
rd-get-03-decision.md
rd-get-04-decision.md

rel-get-01-decision.md
lc-get-01-decision.md
```

`DT-GET-01..04` and `OT-GET-01..03` were consolidated directly in the census before route-specific satellite files became the working mechanism.

## 12. Downstream use

When the remaining M3 discovery areas are closed, this file is intended to feed:

```text
M3 contract
    -> observable behavior deltas and acceptance criteria

M3 architecture set
    -> read ownership rule
    -> one-statement projection patterns
    -> lifecycle carrier-decoding boundary
    -> cursor identity requirements

M3 implementation steps
    -> route grouping / sequencing
    -> code touchpoints
    -> statement-count and regression evidence
```

Until those artifacts are frozen and `status.md` authorizes implementation, this remains consolidated but non-normative discovery input.
