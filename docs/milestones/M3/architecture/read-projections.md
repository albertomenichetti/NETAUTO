# M3 — Public Read Projection Architecture

**Status:** DESIGN IN PROGRESS — ADP-01 CLOSED; ADP-02 PARTIAL (20 / 22); ADP-03 OPEN

**Authority:** M3 TO-BE ARCHITECTURE — PUBLIC READ PROJECTION OWNER

## Purpose and authority boundary

This document owns the M3 TO-BE architecture for the twenty-two canonical public business GET/read projections.

It derives from the frozen M3 contract and changes only the explicit M3 read-boundary delta. Delivered domain identities, mutation semantics, persistence schema, public DTOs, routing and failure behavior remain owned by the current AS-IS except where the frozen M3 contract explicitly changes them.

Current design ownership:

```text
ADP-01 — Read projection responsibility and reusable persistence boundary    CLOSED
ADP-02 — Complete 22-route one-statement projection matrix                  PARTIAL 20 / 22
ADP-03 — Historical lifecycle trusted decoder                              OPEN
```

Implementation remains unauthorized while the M3 architecture set is not frozen.

## Frozen contract inputs

This owner realizes the read-side portions of:

```text
M3-OUT-03 — Read semantic-authority correction
M3-OUT-04 — Public read compatibility
M3-OUT-06 — Historical lifecycle trusted decoding
M3-OUT-08 — Regression and traceability closure

M3-AC-04 — Twenty-two-route read compatibility
M3-AC-05 — Request and path-target failure preservation
M3-AC-06 — No read-side mutation-semantic re-certification
M3-AC-07 — Materially undecodable carrier boundary
M3-AC-08 — Lifecycle historical decoding
M3-AC-18 — Complete outcome traceability
M3-AC-19 — Single-request committed read coherence
```

Cursor construction and public lexical carrier details remain owned by `api.md`; deterministic evidence remains owned by `verification.md`.

# ADP-01 — CLOSED — Read projection responsibility

## Read-path boundary

Every canonical public GET/read follows this responsibility chain:

```text
HTTP adapter
    -> lexical request-carrier parsing
    -> public DTO serialization

application read service
    -> request semantics
    -> cursor query-identity/key validation
    -> ordinary request read UoW ownership
    -> public outcome classification
       404 / 200 / Page / internal failure

persistence read projector
    -> complete persisted projection required by the request
    -> target-existence evidence where required
    -> relational / scalar / JSON carrier materialization
    -> canonical ordering and keyset predicate realization
    -> NO mutation semantic certification

typed application/public projection
```

`read projector` is an architectural role, not a required package/class hierarchy. Existing persistence modules may realize the role through appropriately scoped functions or methods.

## Application responsibility

The application read service owns request semantics rather than persisted-state certification:

```text
request dependency rules
cursor route/filter/key compatibility
opening/closing the ordinary read UoW
404 versus successful-empty/null classification
Page/items/next-cursor composition
bounded application failure classification
```

Persistence may return explicit target-presence evidence. Persistence supplies the fact; application owns the public interpretation.

## Persistence projector responsibility

A read projector owns only persisted facts needed by the public projection:

```text
relational selection
joins / recursion / aggregation required by the projection
path-target existence evidence where required
member completion needed for mandatory public fields
canonical route ordering / keyset predicates
row-to-carrier materialization
JSON/scalar decoding needed to construct typed output
```

The projector runs on the caller-owned connection and never opens, commits or nests a Unit of Work.

## Semantic certification versus representational decoding

A public GET must not answer:

```text
"Would this persisted state pass current mutation admission or transition validation?"
```

Public reads therefore must not re-run mutation-owned certification such as:

```text
default-version publication admissibility
aggregate/domain validation
inheritance acyclicity/agreement/admissibility
runtime schema/DataType resolution used only to prove persisted values
ownership slot/parent semantic validation
factual Relationship Definition/schema/topology validation
historical lifecycle transition validation
```

Mutation paths retain all admission and transition validation. M3 does not weaken mutation validators merely to enable GET reuse.

Representational decoding remains required, including as needed:

```text
row/column extraction
UUID / integer / boolean / string conversion
closed-enum materialization
required persisted field presence
JSON object/array shape required by the response
historical snapshot materialization
```

A required field that cannot be materialized must not be silently dropped or repaired. The complete projection may fail through the bounded internal-failure boundary.

## Projection completion is not semantic certification

A projector may join persisted context solely to produce mandatory public fields. If one persisted public item requires exactly one contextual value:

```text
exactly one value
    -> project the item

zero values
    -> internal projection failure

more than one value where the DTO requires one
    -> ambiguous projection
    -> internal failure
```

The projector must never turn an unmaterializable persisted member into an apparently valid omission.

## Reuse rule

Semantically neutral helpers may be shared, for example:

```text
row -> typed carrier mapping
UUID / enum conversion
query-fragment construction
pure ordering/key helpers
pure response-shape assembly
```

Reuse is forbidden when it causes a GET to invoke mutation admission/transition validation, load dependencies solely to certify state, or add statements only because a mutation-oriented loader is broader than the public projection.

Where a mutation loader is too broad, the GET uses a trusted read projector; the mutation loader remains strong.

## Unit of Work and snapshot rule

For the M3 canonical public GET census:

```text
one complete public projection
    -> one authoritative business SQL statement
    -> PostgreSQL statement snapshot
    -> ordinary read UoW
    -> no coherent_read() dependency
```

The preserved guarantee is one self-consistent committed projection per request. Cross-request repeatable membership remains unpromised.

`coherent_read()` remains valid infrastructure outside this M3 census and is not globally deprecated.

## Path-target rule

For path-scoped collections:

```text
target absent
    -> application 404 resource_not_found

target present + zero matching members
    -> successful empty page
```

The one-statement projector carries enough target-presence evidence to preserve this distinction.

# ADP-02 — Projection-pattern vocabulary

ADP-02 freezes correctness-critical logical shapes while leaving SQLAlchemy syntax, aliases and purely local helper decomposition to implementation.

## RP-01 — DIRECT PAGE

Use when one persisted relation directly represents the public collection.

```text
collection relation
    -> active filters
    -> keyset predicate
    -> canonical ORDER BY
    -> LIMIT limit + 1
```

No dependency read is added merely to certify persisted members.

## RP-02 — DIRECT EXACT

Use when one exact persisted identity directly represents the public resource.

```text
exact persisted identity
    -> 0 rows: application classifies not found
    -> 1 row: typed projection
```

Representational decoding is allowed; mutation-owned semantic admission is not.

## RP-03 — PARENT-ROOTED PAGE

Use when a path-scoped zero-or-many collection must preserve target absence versus an empty collection.

```text
path target
    -> target-presence evidence
    -> bounded child page
       filters
       keyset
       canonical order
       LIMIT limit + 1
```

```text
target absent             -> 404
target present, no child  -> 200 []
target present + child    -> normal page
```

Child filters/keyset must not erase the parent-only result.

## RP-04 — EXACT AGGREGATE / INDEPENDENT CHILD SETS

Use when one exact resource owns one or more child sets that must be materialized completely without truncation or cross-multiplication.

```text
exact target
    -> target/header existence branch
    -> child-set branch A
    -> optional independent child-set branch B
    -> ...
```

Required guarantees:

```text
exact target survives zero children
independent child sets never cartesian-multiply
ordering inside each child set remains canonical
all rows share one statement snapshot
```

Typed `UNION ALL`, independent SQL aggregation or another equivalent one-statement form is valid when these guarantees hold.

## RP-05 — RECURSIVE EXACT-CHAIN PROJECTION

Use when a projection depends on one exact version and recursively pinned exact parent versions.

```text
requested exact leaf
    -> recurse through (parent_template_id, parent_version)
    -> exact ancestors
    -> declaration/context rows per exact node
    -> trusted deterministic projection
```

Required guarantees:

```text
follow exact pins, not stable-lineage ancestry
preserve requested leaf existence
preserve deterministic root-to-leaf ordering where required
preserve declaring_template_id where required
avoid independent-child cartesian multiplication
no inheritance/declaration semantic certification
```

## RP-06 — RECURSIVE STABLE-ANCESTRY PAGE

Use when collection membership depends on a stable lineage and its stable ancestors.

```text
requested stable lineage
    -> recurse through stable parent lineages
    -> bounded member query using ancestry ids
    -> filters / keyset / canonical order / limit + 1
```

Required guarantees:

```text
path-target existence survives an empty page
stable ancestry is projected, not semantically re-certified
membership predicates remain in the query
unrelated dependency certification is not added
```

`RP-05` and `RP-06` are intentionally distinct: exact-version ancestry must not be substituted for stable-lineage ancestry or vice versa.

## RP-07 — TARGET-ROOTED CONTEXT-COMPLETED PAGE

Use when the path target and primary member rows are insufficient to construct each public item and persisted context is required for mandatory fields.

```text
path target
    -> target-presence evidence

bounded primary public-member candidate set
    -> filters / keyset / canonical order / limit + 1

projection context
    -> joins / recursion required only to complete public fields

completed public page
```

Required guarantees:

```text
target absent                     -> 404
target present + no candidates    -> 200 []
completed candidates              -> normal page
required contextual field absent  -> internal failure, never silent filtering
ambiguous required context         -> internal failure, never arbitrary choice
```

When raw rows can duplicate one public semantic item, public-item derivation/deduplication occurs before public keyset/limit semantics.

## RP-08 — TARGET-ROOTED OPTIONAL PROJECTION

Use when the path target is required but the related public projection has cardinality `0..1`.

```text
required target absent
    -> 404

target present + optional relation absent
    -> successful null

target present + relation present
    -> complete related projection
```

A relation that exists but cannot be materialized must not be converted to `null`.

## RP-09 — ROOT-PAGED AGGREGATE

Use when the public collection is a page of aggregate roots and each selected root owns child rows required by the item projection.

```text
root relation
    -> root-level keyset / filters / canonical root order
    -> LIMIT limit + 1 ROOT IDENTITIES

selected root identities
    -> expand required child rows
    -> reconstruct each complete aggregate item
```

Required guarantees:

```text
public page cardinality is defined by root identities
LIMIT/keyset apply before child expansion
one selected root is never truncated by SQL row pagination
all required child rows for each selected root are projected
child expansion does not alter root ordering or cursor identity
```

Applying `LIMIT` to root×child joined rows is forbidden when it can truncate an aggregate or change public page cardinality.

## RP-10 — PARENT-ROOTED EXACT AGGREGATE

Use for a nested exact resource when the public contract distinguishes stable-parent absence from exact-child absence and the exact child owns zero-or-many child rows.

```text
required stable parent
    -> parent presence evidence
    -> optional exact child by exact identity
       -> exact-child presence evidence
       -> child-owned rows
```

Required public states:

```text
parent absent
    -> parent resource 404

parent present + exact child absent
    -> exact child resource 404

exact child present + zero child-owned rows
    -> successful exact aggregate with empty child set

exact child present + child-owned rows
    -> complete exact aggregate
```

Filters or joins for child-owned rows must not erase parent/exact-child presence evidence.

# ADP-02 — DataType family CLOSED

| ID | Route | Pattern | Key architecture consequence |
|---|---|---|---|
| `DT-GET-01` | `GET /datatypes` | `RP-01` | direct lineage page; project `default_version` without target certification |
| `DT-GET-02` | `GET /datatypes/{id}` | `RP-02` | direct lineage exact read; no default-target lookup |
| `DT-GET-03` | `GET /datatypes/{id}/versions` | `RP-03` | lineage-rooted version page preserving `404` vs `200 []` |
| `DT-GET-04` | `GET /datatypes/{id}/versions/{version}` | `RP-02` | exact composite version row; no separate lineage read |

### DataType notes

`DT-GET-01` filters `namespace,name`, orders/keysets by `(namespace,name)` and applies `limit+1`. `DT-GET-02` directly projects `datatypes.id`. `DT-GET-03` roots the bounded status-filtered version page at the lineage so an empty page remains distinct from a missing lineage. `DT-GET-04` directly projects the exact `(datatype_id,version)` row and performs only representational decoding of persisted status/base_type/constraints.

No DataType GET re-runs constraint/default publication certification.

# ADP-02 — ObjectTemplate family CLOSED

| ID | Route | Pattern | Key architecture consequence |
|---|---|---|---|
| `OT-GET-01` | `GET /object-templates` | `RP-01` | direct lineage page; internal parent tri-state supplied by application |
| `OT-GET-02` | `GET /object-templates/{id}` | `RP-02` | direct lineage exact read |
| `OT-GET-03` | `GET /object-templates/{id}/versions` | `RP-03` | lineage-rooted version page |
| `OT-GET-04` | `GET /object-templates/{id}/versions/{version}` | `RP-04` | exact header + independent properties/components |
| `OT-GET-05` | `GET /object-templates/{id}/versions/{version}/effective-schema` | `RP-05` | recursive exact-version chain |
| `OT-GET-06` | `GET /object-templates/{id}/relationship-capabilities` | `RP-06` | recursive stable-lineage ancestry page |

### OT-GET-01..03

`OT-GET-01` uses `namespace,name,abstract,parent-filter-state`, keyset/order `(namespace,name)` and `limit+1`; `default_version` is projected without target certification. HTTP lexical omitted/UUID/lowercase-null handling remains ADP-05. `OT-GET-02` directly projects the lineage. `OT-GET-03` is a status-filtered lineage-rooted version page.

### OT-GET-04 — exact version aggregate

Public projection:

```text
ObjectTemplateVersion header
+ local properties[]
+ local components[]
```

Properties/components remain independent child sets. A direct properties×components join is forbidden. A typed multi-branch projection is preferred; equivalent independent aggregation is allowed.

### OT-GET-05 — effective schema

The projector follows persisted exact parent pins only:

```text
(template_id, version)
    -> (parent_template_id, parent_version)
    -> ... exact root
```

It emits declaration/context rows sufficient for trusted root-to-leaf effective-schema assembly with `declaring_template_id`, without mutation-oriented cycle/agreement/member-collision certification.

### OT-GET-06 — relationship capabilities

Capability membership follows stable ancestry, then `RelationshipResolution.from_template_id IN ancestry`, optional name filter, `resolution_id` keyset/order, `limit+1`, and the existing `EXISTS` predicate requiring at least one PUBLISHED RelationshipDefinitionVersion. That `EXISTS` is public membership logic, not certification. `default_version` is projected without target lookup.

# ADP-02 — Object family CLOSED

| ID | Route | Pattern | Key architecture consequence |
|---|---|---|---|
| `OBJ-GET-01` | `GET /objects` | `RP-01` | direct minimal ObjectSummary page |
| `OBJ-GET-02` | `GET /objects/{id}` | `RP-02` | direct intrinsic Object read; remove transitive schema/DataType certification |
| `OBJ-GET-03` | `GET /objects/{parent}/components` | `RP-07` + exact-chain context | complete `slot_declaring_template_id` from exact chain |
| `OBJ-GET-04` | `GET /objects/{child}/owner` | `RP-08` + exact-chain context | distinguish absent child / detached child / materialized owner |
| `OBJ-GET-05` | `GET /objects/{id}/lifecycle-events` | `RP-03` + ADP-03 decoder | target-rooted event page; decoder details deferred |
| `OBJ-GET-06` | `GET /objects/{id}/relationships` | `RP-07` | target-rooted deduplicated semantic Relationship-view page |

### OBJ-GET-01 — Object page

One statement over Object summary columns, filters `template_id`, dependent `template_version`, `canonical_name`, keyset/order `id`, `limit+1`. `template_version requires template_id` remains application request validation. Unknown filter targets yield an empty collection rather than a target lookup.

### OBJ-GET-02 — intrinsic Object exact

Direct `objects.id` projection. Persisted `properties` must be representationally decodable as the required object carrier with string keys. Runtime-schema/DataType loading and property re-canonicalization are removed from GET.

### OBJ-GET-03 — component page

Inputs:

```text
parent Object exact template pin
recursive exact ObjectTemplateVersion chain
bounded object_components page
component declaration matching persisted slot_name on exact chain
```

The declaration lookup exists only to project mandatory `slot_declaring_template_id`. Zero or ambiguous contextual matches are internal projection failures, never silent member filtering. Primary page key/order remains `child_object_id`; optional `slot_name` remains a filter. Cursor identity adds `parent_object_id` under ADP-04.

### OBJ-GET-04 — owner

Required child Object is left-associated with the optional ownership fact. If ownership exists, the parent Object exact template pin and recursive exact chain provide the unique declaration needed for `slot_declaring_template_id`.

```text
child absent                  -> 404
child present, no ownership   -> 200 null
ownership materializable      -> OwnerProjection
ownership not materializable  -> internal failure, never null
```

### OBJ-GET-05 — lifecycle page

One target-rooted lifecycle page, ordered/keyed `(occurred_at,id) DESC`, preserving Object 404 versus empty event page. Historical decoding is ADP-03 work.

### OBJ-GET-06 — Object-relative Relationship page

The projector combines target Object, runtime resolution rows, factual Relationship state and Resolution names into complete public semantic views. It does not reload/validate Relationship, RelationshipDefinition, ObjectTemplate or DataType aggregates.

The public set is deduplicated before keyset/order/limit:

```text
derive complete semantic rows
    -> DISTINCT / equivalent semantic deduplication
    -> keyset (relationship_id, destination_object_id, name)
    -> ORDER BY same tuple ASC
    -> LIMIT limit + 1
```

Cursor identity adds `object_id` under ADP-04.

# ADP-02 — RelationshipDefinition family CLOSED

| ID | Route | Pattern | Key architecture consequence |
|---|---|---|---|
| `RD-GET-01` | `GET /relationship-definitions` | `RP-09` | page Definition root ids before expanding complete Resolution sets |
| `RD-GET-02` | `GET /relationship-definitions/{id}` | `RP-04` | exact aggregate header + complete Resolution set |
| `RD-GET-03` | `GET /relationship-definitions/{id}/versions` | `RP-03` | parent-rooted version page preserving parent 404 vs empty page |
| `RD-GET-04` | `GET /relationship-definitions/{id}/versions/{version}` | `RP-10` | distinguish parent absence, exact-version absence and empty property set |

## RD-GET-01 — root-paged Definition aggregates

Public page membership is defined by RelationshipDefinition roots, not joined Resolution rows.

Logical shape:

```text
relationship_definitions roots
    -> id keyset/order ASC
    -> LIMIT limit + 1 root ids

selected root ids
    -> join/expand relationship_resolutions
    -> reconstruct complete RelationshipDefinition aggregates
```

The aggregate expansion must never truncate one selected Definition because it owns multiple Resolution rows. The current page-root-first persistence architecture is retained. Read-side `validate_definition()`, default-target publication certification and `coherent_read()` are removed.

## RD-GET-02 — exact Definition aggregate

One exact RelationshipDefinition header plus its complete Resolution set is materialized in one statement under `RP-04`.

```text
Definition absent     -> 404
Definition present    -> complete aggregate projection
```

A persisted Resolution-set cardinality that mutation validation would reject is not re-certified by GET. Required fields must still be representationally materializable. `default_version` is projected without loading/certifying its target.

## RD-GET-03 — version page

One `RP-03` statement rooted at `relationship_definitions.id` with a bounded `relationship_definition_versions` child page:

```text
filter     status when supplied
keyset     version
order      version ASC
page       limit + 1
```

The status/keyset predicates remain on the child-page side so they cannot erase the parent-only result.

```text
parent absent                   -> RelationshipDefinition 404
parent present + zero versions  -> 200 []
parent present + versions       -> normal page
```

No default-pointer recertification is part of the GET.

## RD-GET-04 — nested exact version aggregate

One `RP-10` statement preserves three levels of public interpretation:

```text
RelationshipDefinition parent
    -> optional exact RelationshipDefinitionVersion(version)
       -> ordered property declarations
```

Result semantics:

```text
parent absent
    -> RelationshipDefinition 404

parent present + exact version absent
    -> RelationshipDefinitionVersion 404

exact version present + zero properties
    -> successful RDV with properties=[]

exact version present + properties
    -> successful complete RDV
```

Property ordering remains `position ASC`. The projector performs typed carrier decoding only and does not call persisted RDV semantic validators. Separate parent/header/property reads and `coherent_read()` are removed.

# ADP-02 — Remaining routes

The only uncovered canonical GET/read routes are:

```text
REL-GET-01  GET /relationships/{id}
LC-GET-01   GET /lifecycle-events
```

They must be closed before ADP-02 can become CLOSED.

# Cross-family ADP-02 invariants currently frozen

For all twenty covered routes:

```text
one complete business SQL statement
ordinary read UoW
one PostgreSQL statement snapshot
no public-GET coherent_read() dependency
no mutation semantic validator as a read prerequisite
no hidden remediation or silent filtering of required state
canonical public ordering and keyset semantics preserved
path-target absence versus empty-page/null semantics preserved
aggregate pages limit root/public items rather than arbitrary joined rows
nested exact resources preserve parent absence separately from exact-child absence
```

# Preserved AS-IS responsibilities

ADP-01 and the closed ADP-02 route families do not change:

```text
PostgreSQL as the only persistence backend
PK / UNIQUE / FK / CHECK / NOT NULL structural authority
mutation Unit-of-Work semantic admission and transition ownership
mutation lock-plan and concurrency guarantees
public DTO field meanings and route identities
public bounded failure envelope
opaque keyset pagination contract
exact persisted identities and bindings
schema / migration / dependency baseline
```

# Intentional AS-IS contradiction

The delivered global read principle treated persisted semantic invariant corruption as a reason to fail the complete representation after read-side certification.

M3 intentionally narrows that principle:

```text
mutation
    -> semantic certification

database
    -> structural invariant enforcement

public GET/read
    -> request/cursor validation
    -> persisted fact projection
    -> representational decoding
    -> no mutation-semantic re-certification
```

Representationally undecodable required state still fails safely. M3 introduces neither read-time repair nor silent corruption tolerance.

This contract-authorized contradiction must be propagated to the delivered AS-IS during final consolidation after implementation/acceptance.

# Downstream architecture constraints

The final two ADP-02 routes must:

```text
have one complete persistence projection boundary
use no mutation semantic validator as a read prerequisite
preserve public target/failure semantics
preserve canonical ordering/filtering/keyset semantics where applicable
observe one committed statement snapshot
require no public-GET coherent_read() dependency
```

ADP-03 must define lifecycle decoding exclusively as representational materialization, not transition certification.

`api.md` must preserve request/cursor/failure classification ownership without moving persistence semantic validation into the HTTP adapter.

`verification.md` must prove both sides of the boundary:

```text
public GETs do not re-certify mutation semantics
mutation semantic validation remains intact
```

# ADP status

```text
ADP-01  CLOSED
ADP-02  PARTIAL
    DataType             4 / 4 CLOSED
    ObjectTemplate       6 / 6 CLOSED
    Object               6 / 6 CLOSED
    RelationshipDef      4 / 4 CLOSED
    Relationship         0 / 1 OPEN
    Global lifecycle     0 / 1 OPEN
    ------------------------------
    total               20 / 22
ADP-03  OPEN
```

No implementation authority is created by these closures. The architecture set remains `DESIGN IN PROGRESS — NOT FROZEN`.
