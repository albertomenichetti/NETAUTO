# M3 — Discovery Closure

**Status:** DISCOVERY COMPLETE / CONSOLIDATED INPUT / NON-NORMATIVE

**Role:** final discovery closure and traceability input for M3 contract and architecture preparation. This document does not authorize implementation and does not itself freeze any M3 semantic or technical decision.

## 1. Closure statement

All three bounded M3 discovery workstreams are complete:

```text
Area A — CLI post-create correctness          CLOSED
Area B — public GET/read audit                CLOSED / 22 of 22
Area C — parent_template_id = null carrier    CLOSED
```

The discovery phase has produced a complete bounded change set, observable target outcomes, expected architecture impacts and candidate acceptance evidence.

No additional product area is required before contract drafting.

## 2. Area A — CLI post-create correctness

Authoritative discovery inputs:

- [`cli-post-create-decision.md`](cli-post-create-decision.md)
- [`cli-post-create-closure.md`](cli-post-create-closure.md)

Closed outcome:

```text
keep exact same-release 201 + Location validation
fix the common Location materializer, not individual commands
Location token = request key or response JSON path
remove Python format grammar from token materialization
valid committed 201 + correct Location must not become cli_internal_error
genuine Location mismatch remains cli_protocol_error
```

Current AS-IS owners impacted downstream:

```text
docs/architecture/cli.md
    -> static registry, same-release response validation, CLI process outcomes

docs/architecture/api.md
    -> exact create status / Location wire contract consumed by the CLI

docs/architecture/verification.md
    -> permanent evidence obligations if M3 promotes the new coverage
```

No DataType/ObjectTemplate/RelationshipDefinition domain owner changes are required for Area A.

## 3. Area B — public GET/read audit

Authoritative discovery inputs:

- [`get-read-census.md`](get-read-census.md)
- [`get-read-review-closure.md`](get-read-review-closure.md)
- route-specific `*-get-*-decision.md` files

Closed outcome:

```text
all 22 canonical public business GET/read routes reviewed
all 22 target one business SQL statement
no canonical public GET requires coherent_read() in the M3 target
GET/read paths trust persisted semantic state
request/cursor validation remains strict
path-target 404 / empty-collection semantics remain preserved
historical lifecycle reads retain carrier decoding but remove semantic transition re-certification
OBJ-GET-03 cursor identity adds parent_object_id
OBJ-GET-06 cursor identity adds object_id
```

Current AS-IS owners impacted downstream:

```text
docs/architecture/README.md
    -> current global "Coherent reads and safe corruption boundary" principle must be deliberately revised;
       M3 target separates coherent projection from persisted semantic re-certification

docs/architecture/api.md
    -> public read/filter/cursor/failure behavior and 22-route surface

docs/architecture/datatype.md
    -> DataType read ownership and default-pointer read semantics

docs/architecture/objecttemplate.md
    -> ObjectTemplate read/effective-schema/capability projection semantics

docs/architecture/object.md
    -> Object, ownership and lifecycle read projections

docs/architecture/relationship.md
    -> RelationshipDefinition/Relationship factual read projections and lifecycle history semantics

docs/architecture/persistence.md
    -> single-statement projection realization, persistence read responsibilities/codecs

docs/architecture/concurrency.md
    -> public-read UoW/snapshot realization; coherent_read infrastructure remains available where genuinely required

docs/architecture/verification.md
    -> statement-count, cursor-binding and semantic-read regression evidence
```

The Area B contract must describe observable read guarantees without turning a specific SQL formulation into public behavior. The architecture must own the one-statement projection patterns and read-validation responsibility boundary.

## 4. Area C — `parent_template_id = null`

Authoritative discovery inputs:

- [`parent-template-null-carrier-decision.md`](parent-template-null-carrier-decision.md)
- [`parent-template-null-carrier-closure.md`](parent-template-null-carrier-closure.md)

Closed outcome:

```text
one public filter only: parent_template_id
omitted -> no parent filter
UUID    -> direct children of that parent
null    -> root ObjectTemplates only
parent_filter_set remains internal and is not exposed publicly
HTTP accepts exact lowercase null or UUID
CLI nullable selector carrier uses null without selector lookup
cursor identity retains parent_filter_set to distinguish omission from root-only
application/persistence tri-state remains unchanged
```

Current AS-IS owners impacted downstream:

```text
docs/architecture/api.md
    -> public lexical query contract and ObjectTemplate list filter semantics

docs/architecture/cli.md
    -> nullable query parameter grammar, selector behavior and query serialization

docs/architecture/objecttemplate.md
    -> stable lineage parent semantics / root meaning where referenced

docs/architecture/persistence.md
    -> no semantic change required, but architecture should preserve the existing IS NULL projection boundary

docs/architecture/verification.md
    -> HTTP/CLI/cursor tri-state evidence
```

## 5. Contract candidate outcomes

The future M3 contract should freeze observable outcomes only.

Candidate contract boundary:

```text
A. CLI create correctness
    canonical successful create responses are reported as success
    exact Location validation remains mandatory
    protocol violations remain cli_protocol_error

B. Public GET/read behavior
    existing public DTO/filter/pagination/failure behavior is preserved except the identified cursor-binding corrections
    GETs no longer fail solely because they re-certify persisted semantic invariants
    historical lifecycle output remains typed and publicly compatible

C. ObjectTemplate root filter
    parent_template_id omitted / UUID / null is the complete public tri-state
    malformed/repeated carriers retain strict invalid-request behavior
    official CLI exposes the same tri-state
```

Implementation mechanisms such as helper names, CTE/UNION layouts and store method names do not belong in the contract.

## 6. Architecture candidate outcomes

The future M3 architecture set should define at least:

```text
read responsibility boundary
    mutation owns semantic certification
    DB owns structural constraints
    read owns request validation, lookup, composition and carrier decoding

single-statement public read realization
    parent-rooted outer-join collection projections
    exact aggregate multi-child projection without cartesian multiplication
    recursive exact inheritance projection
    recursive stable ancestry capability projection
    trusted read projectors where mutation aggregate loaders are too broad

lifecycle historical decoding boundary
    carrier decoding vs semantic transition certification

CLI Location token materialization grammar
    request key / response JSON path

nullable selector query carrier semantics
    explicit null is terminal for a nullable selector parameter
    null serialization is query-location aware

ObjectTemplate parent filter carrier
    omitted / UUID / null mapped to the existing internal tri-state
```

## 7. Schema / dependency / migration impact

Discovery found no requirement for:

```text
database schema change
Alembic migration
new runtime dependency
lockfile change
new business resource
new route
```

M3 is expected to be an application/persistence/HTTP/CLI correctness and simplification milestone over the existing durable model.

## 8. Cross-workstream consistency

No direct conflict was found between the three areas.

Area C uses the ObjectTemplate list path already reviewed in Area B and preserves its internal tri-state and target single-statement read shape.

Area A affects CLI response validation only and does not alter API create semantics.

Area B preserves mutation semantic validation, so the CLI create correction does not weaken server-side candidate certification.

## 9. Discovery completion checklist

```text
[x] Area A complete 201/Location census
[x] Area A common root cause and target grammar
[x] Area A acceptance boundary
[x] 22/22 GET/read census
[x] one-statement target for all 22 reads
[x] GET cursor bugs and lifecycle decoding boundary
[x] Area C actual HTTP/CLI reachability analysis
[x] canonical root-only public carrier selected
[x] HTTP/CLI/cursor Area C target boundary
[x] final deltas mapped to current AS-IS owners
[x] candidate contract outcomes identified
[x] candidate architecture outcomes identified
```

## 10. Next gate

Discovery is complete.

The next permitted governance activity is **M3 contract drafting and review**.

Software implementation remains unauthorized. Architecture and implementation steps must not be frozen or activated before the contract is final/frozen in the project-governed order.