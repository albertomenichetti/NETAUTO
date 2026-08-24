# M3 — GET / Read Path Census

**Status:** COMPLETE — 22 / 22 CONSOLIDATED / NON-NORMATIVE

**Role:** repository-based discovery register for the 22 canonical public business GET/read routes.

This file is the compact census. The downstream closure/planning input is [`get-read-review-closure.md`](get-read-review-closure.md). Route-specific decision files remain supporting discovery evidence.

Nothing in this WIP area authorizes software implementation. Consolidated conclusions become normative only when promoted through the M3 contract, architecture and implementation-step freeze gates.

## 1. Census rules

The completed review used the following ownership model:

```text
mutation
    -> validates and preserves semantic invariants

database
    -> preserves structural invariants expressible as constraints / FK

GET / read
    -> validates request and cursor carriers
    -> trusts persisted semantic state
    -> locates, composes and projects persisted facts
    -> decodes carriers required for typed output
    -> does not re-certify mutation-owned semantic invariants
```

The completed review also established:

```text
22 / 22 target reads can be expressed as one SQL statement
22 / 22 therefore require no coherent_read() in the M3 target model
```

This is a route-census conclusion, not a blanket statement that `coherent_read()` has no valid use elsewhere.

## 2. Full route register

| ID | Public route | Revalidation target | `coherent_read()` target | Projection target | Disposition |
|---|---|---|---|---|---|
| `DT-GET-01` | `GET /datatypes` | remove default-target certification | remove | existing one-statement lineage page | simplify |
| `DT-GET-02` | `GET /datatypes/{id}` | remove default-target certification | remove | one lineage lookup + 404 | simplify |
| `DT-GET-03` | `GET /datatypes/{id}/versions` | none | none | one parent-rooted version page | compose |
| `DT-GET-04` | `GET /datatypes/{id}/versions/{version}` | none | none | existing exact lookup | keep |
| `OT-GET-01` | `GET /object-templates` | remove default-target certification | remove | existing lineage page | simplify |
| `OT-GET-02` | `GET /object-templates/{id}` | remove default-target certification | remove | one lineage lookup + 404 | simplify |
| `OT-GET-03` | `GET /object-templates/{id}/versions` | none | none | one parent-rooted version page | compose |
| `OT-GET-04` | `GET /object-templates/{id}/versions/{version}` | none beyond projection | remove | one exact header/property/component statement | compose |
| `OT-GET-05` | `GET /object-templates/{id}/versions/{version}/effective-schema` | remove persisted declaration/inheritance certification | remove | one recursive exact-chain statement | redesign read projection |
| `OT-GET-06` | `GET /object-templates/{id}/relationship-capabilities` | remove stable-graph/default-target certification | remove | one recursive stable-ancestry capability statement | redesign read projection |
| `OBJ-GET-01` | `GET /objects` | none | none | existing list statement | keep |
| `OBJ-GET-02` | `GET /objects/{id}` | remove runtime schema/DataType certification | none | one object lookup + 404 | simplify |
| `OBJ-GET-03` | `GET /objects/{parent}/components` | remove schema/slot certification | remove | one parent-rooted exact-chain component statement | redesign + cursor fix |
| `OBJ-GET-04` | `GET /objects/{child}/owner` | remove parent/schema/slot certification | remove | one child-rooted owner projection | redesign read projection |
| `OBJ-GET-05` | `GET /objects/{id}/lifecycle-events` | remove lifecycle semantic certification | remove | one target-object + event-page statement | compose + decoder cleanup |
| `OBJ-GET-06` | `GET /objects/{id}/relationships` | remove `_validated_many()` aggregate certification | remove | one target-object + runtime-view page | redesign + cursor fix |
| `RD-GET-01` | `GET /relationship-definitions` | remove definition/default certification | remove | existing aggregate-page statement | simplify |
| `RD-GET-02` | `GET /relationship-definitions/{id}` | remove definition/default certification | remove | one aggregate lookup + 404 | simplify |
| `RD-GET-03` | `GET /relationship-definitions/{id}/versions` | remove default certification | remove | one parent-rooted version page | compose |
| `RD-GET-04` | `GET /relationship-definitions/{id}/versions/{version}` | remove exact-version semantic certification | remove | one parent-rooted exact-version/property statement | compose |
| `REL-GET-01` | `GET /relationships/{id}` | remove factual aggregate/definition/schema certification | remove | dedicated one-statement factual/runtime-view projector | redesign read projection |
| `LC-GET-01` | `GET /lifecycle-events` | remove lifecycle semantic certification | remove | existing one-statement event page | decoder cleanup |

## 3. Family closure

```text
DataType                  4 / 4  CLOSED
ObjectTemplate            6 / 6  CLOSED
Object                    6 / 6  CLOSED
RelationshipDefinition    4 / 4  CLOSED
Relationship              1 / 1  CLOSED
Global lifecycle          1 / 1  CLOSED
                         ------
                         22 / 22 CLOSED
```

## 4. Cross-route conclusions

### 4.1 No GET-side semantic re-certification

Examples removed by the target model include:

```text
default_version -> PUBLISHED checks
persisted aggregate domain validation
stable/exact inheritance re-certification
runtime schema/DataType re-resolution solely to prove persisted values again
ownership-slot semantic revalidation
factual Relationship closure/definition/schema certification
lifecycle transition correctness checks
```

A lookup or join that is required to build the response is projection. A lookup performed only to prove that already-persisted state is semantically valid is revalidation.

### 4.2 One statement per canonical business GET

The target statement may be structurally sophisticated — recursive CTE, parent-rooted outer join, typed union or dedicated read projector — but the completed review found no route that semantically requires a multi-statement public projection.

### 4.3 Preserve 404 vs empty collection

Parent-scoped collections must distinguish:

```text
missing path target -> 404
existing path target + zero matching rows -> 200 []
```

The single-statement formulation must preserve this distinction, normally by rooting the statement at the path target and outer-joining the filtered child/page projection.

### 4.4 Request/cursor validation remains strict

Read simplification does not relax request validation. Two path-binding defects require correction:

```text
OBJ-GET-03 cursor identity must include parent_object_id
OBJ-GET-06 cursor identity must include object_id
```

Lifecycle cursor identity is already correctly route/filter bound through `involving_object_id`.

### 4.5 Historical carrier decoding is not semantic validation

Lifecycle JSONB still needs enough decoding to construct typed output. The target decoder keeps carrier materialization/conversion but removes transition and cross-field semantic certification. The same boundary applies to HTTP DTO selection.

### 4.6 Mutation-oriented helpers remain intact

The GET review does not justify weakening validation helpers used by mutation workflows. When a GET needs a smaller trusted representation, prefer a read-specific projector rather than globally stripping validation from mutation-oriented aggregate/domain paths.

## 5. ObjectTemplate parent-filter finding

`OT-GET-01` closed the application/persistence portion of the separate nullable-parent investigation:

```text
parent filter absent                  -> no predicate
parent filter set + UUID              -> parent_template_id = UUID
parent filter set + None              -> parent_template_id IS NULL
cursor identity includes filter-set identity
```

The unresolved question is only the public HTTP/CLI carrier for the explicit root-only state. That remains a separate M3 discovery workstream and is not part of this GET/read closure.

## 6. Lifecycle shared conclusion

`OBJ-GET-05` and `LC-GET-01` share one target decoder policy:

```text
KEEP
    material decoding required to build LifecycleEvent values

REMOVE
    mutation-kind transition revalidation
    before/after semantic certification
    snapshot/outer-row coherence certification
    duplicated family/state semantic checks
```

The object-scoped route additionally folds path-object existence and event pagination into one statement. The global route already needs only the existing lifecycle page statement.

## 7. Detailed evidence index

The first seven decisions were consolidated directly in earlier versions of this census:

```text
DT-GET-01 .. DT-GET-04
OT-GET-01 .. OT-GET-03
```

Detailed satellite evidence for the remaining routes:

- [`ot-get-04-decision.md`](ot-get-04-decision.md)
- [`ot-get-05-decision.md`](ot-get-05-decision.md)
- [`ot-get-06-decision.md`](ot-get-06-decision.md)
- [`obj-get-01-decision.md`](obj-get-01-decision.md)
- [`obj-get-02-decision.md`](obj-get-02-decision.md)
- [`obj-get-03-decision.md`](obj-get-03-decision.md)
- [`obj-get-04-decision.md`](obj-get-04-decision.md)
- [`obj-get-05-decision.md`](obj-get-05-decision.md)
- [`obj-get-06-decision.md`](obj-get-06-decision.md)
- [`rd-get-01-decision.md`](rd-get-01-decision.md)
- [`rd-get-02-decision.md`](rd-get-02-decision.md)
- [`rd-get-03-decision.md`](rd-get-03-decision.md)
- [`rd-get-04-decision.md`](rd-get-04-decision.md)
- [`rel-get-01-decision.md`](rel-get-01-decision.md)
- [`lc-get-01-decision.md`](lc-get-01-decision.md)

The complete downstream planning summary is [`get-read-review-closure.md`](get-read-review-closure.md).

## 8. Discovery disposition

The GET/read workstream is **closed at discovery level**.

No further route-by-route GET investigation is required before drafting the M3 contract, unless one of the two remaining M3 discovery areas uncovers a direct conflict with a consolidated read decision.

Software implementation remains unauthorized until the normal M3 governance gates are completed.
