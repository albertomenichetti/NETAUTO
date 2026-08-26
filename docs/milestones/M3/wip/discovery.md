# M3 — Discovery Summary

**Status:** COMPLETE / CONSOLIDATED INPUT / NON-NORMATIVE

**Role:** discovery navigator and summary only. This file records the completed M3 discovery result. It does not define the M3 contract, freeze architecture or authorize implementation.

## 1. Workstream closure

All bounded M3 discovery areas are closed:

```text
Area A — CLI post-create correctness          CLOSED
Area B — public GET/read audit                CLOSED / 22 of 22 consolidated
Area C — parent_template_id = null carrier    CLOSED
```

Final cross-workstream closure and AS-IS traceability:

[`discovery-closure.md`](discovery-closure.md)

The next governance gate is M3 contract drafting and review. Software implementation remains unauthorized.

## 2. Area A — CLI post-create correctness

Detailed inputs:

- [`cli-post-create-decision.md`](cli-post-create-decision.md)
- [`cli-post-create-closure.md`](cli-post-create-closure.md)

Closed conclusions:

```text
8 registered operations use 201 Created + exact Location
3 nested-token creates are affected by the current materializer defect:
    datatype create                 {datatype.id}
    object-template create          {object_template.id}
    relationship-definition create  {relationship_definition.id}

Location token grammar:
    exact request-value key first
    otherwise dot-separated response JSON path

dot means JSON traversal only
no Python str.format / format_map grammar

canonical 201 + matching Location -> CLI success
genuine Location mismatch -> cli_protocol_error
valid committed success -> never cli_internal_error due to Location materialization
```

No schema, migration, dependency or lockfile change is required.

## 3. Area B — public GET/read audit

Detailed inputs:

- [`get-read-census.md`](get-read-census.md)
- [`get-read-review-closure.md`](get-read-review-closure.md)
- route-specific `*-get-*-decision.md` records

Complete census:

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

Closed conclusions:

```text
mutation owns semantic certification
database owns structural constraints
GET/read owns request validation, lookup, composition and carrier decoding
GET/read does not re-certify mutation-owned persisted semantic invariants

22 / 22 canonical public GET/read routes
    -> target one business SQL statement
    -> ordinary UnitOfWork / statement snapshot
    -> no coherent_read() required in the target census

preserve strict request/cursor validation
preserve path-target 404 vs existing-parent 200 [] distinctions
OBJ-GET-03 cursor identity adds parent_object_id
OBJ-GET-06 cursor identity adds object_id
lifecycle history keeps carrier decoding but removes semantic transition re-certification
mutation-path validators remain intact
```

No schema, migration, dependency or lockfile change is required.

## 4. Area C — `parent_template_id = null`

Detailed inputs:

- [`parent-template-null-carrier-decision.md`](parent-template-null-carrier-decision.md)
- [`parent-template-null-carrier-closure.md`](parent-template-null-carrier-closure.md)

The application, persistence and cursor layers already implement the intended tri-state. Discovery closed the missing public carrier.

Canonical public semantics:

```text
parent_template_id omitted
    -> no parent filter

parent_template_id=<UUID>
    -> direct children of that parent

parent_template_id=null
    -> root ObjectTemplates only
```

Only `parent_template_id` is public. `parent_filter_set` remains internal.

HTTP target:

```text
exact lowercase null -> typed None + parameter present
valid UUID            -> typed UUID + parameter present
omission              -> typed None + parameter absent
other lexical values  -> invalid_request / 400
```

CLI target:

```text
nullable selector parameter + non-null value
    -> normal ObjectTemplate selector resolution

nullable selector parameter + explicit null
    -> terminal None; no selector lookup
    -> query carrier parent_template_id=null
```

Explicit null query serialization is location-aware; `None` is not made a globally valid path/query scalar.

Existing application tri-state, persistence filtering and cursor codec remain unchanged.

No schema, migration, dependency or lockfile change is required.

## 5. AS-IS traceability

The final mapping to current authoritative owners is in [`discovery-closure.md`](discovery-closure.md).

Primary owners impacted by future M3 architecture work:

```text
docs/architecture/README.md
docs/architecture/api.md
docs/architecture/cli.md
docs/architecture/datatype.md
docs/architecture/objecttemplate.md
docs/architecture/object.md
docs/architecture/relationship.md
docs/architecture/persistence.md
docs/architecture/concurrency.md
docs/architecture/verification.md
```

The current AS-IS remains authoritative until the M3 contract, architecture, implementation and acceptance gates are completed.

## 6. Discovery completion checklist

```text
[x] complete 201/Location census and common root cause
[x] close CLI Location token grammar and target outcomes
[x] complete 22/22 GET/read census
[x] close one-statement target for every canonical public GET
[x] record read ownership, cursor defects and lifecycle decoding boundary
[x] verify HTTP/CLI reachability of ObjectTemplate parent tri-state
[x] select parent_template_id=null as canonical root-only carrier
[x] close HTTP/CLI/cursor Area C target boundary
[x] map all final deltas to current AS-IS owners
[x] identify contract candidate outcomes
[x] identify architecture candidate outcomes
```

## 7. Scope boundary

M3 discovery did not add general lock-plan redesign, broad mutation-lock minimization, new business capabilities, new model resources, unrelated schema redesign or unrelated CLI redesign.

## 8. Next action

Discovery is complete.

```text
M3 contract drafting and review
    -> architecture set
    -> required consistency review / closure
    -> implementation steps
    -> explicit implementation authorization
```

Until those gates advance, `steps.md` remains a pre-implementation placeholder and no software implementation is authorized.