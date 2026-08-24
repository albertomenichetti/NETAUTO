# M3 — Public Read Projection Architecture

**Status:** DESIGN IN PROGRESS — ADP-01 CLOSED; ADP-02 CLOSED (22 / 22); ADP-03 OPEN

**Authority:** M3 TO-BE ARCHITECTURE — PUBLIC READ PROJECTION OWNER

## Purpose and authority boundary

This document owns the M3 TO-BE architecture for the twenty-two canonical public business GET/read projections.

It derives from the frozen M3 contract and changes only the explicit M3 read-boundary delta. Delivered domain identities, mutation semantics, persistence schema, public DTOs, routing and failure behavior remain owned by the current AS-IS except where the frozen M3 contract explicitly changes them.

Current design ownership:

```text
ADP-01 — Read projection responsibility and reusable persistence boundary    CLOSED
ADP-02 — Complete 22-route one-statement projection matrix                  CLOSED 22 / 22
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

# ADP-02 — CLOSED — Projection-pattern vocabulary

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

# ADP-02 — Complete route matrix — 22 / 22 CLOSED

| ID | Route | Pattern | Key architecture consequence |
|---|---|---|---|
| `DT-GET-01` | `GET /datatypes` | `RP-01` | direct lineage page; project `default_version` without target certification |
| `DT-GET-02` | `GET /datatypes/{id}` | `RP-02` | direct lineage exact read; no default-target lookup |
| `DT-GET-03` | `GET /datatypes/{id}/versions` | `RP-03` | lineage-rooted version page preserving `404` vs `200 []` |
| `DT-GET-04` | `GET /datatypes/{id}/versions/{version}` | `RP-02` | exact composite version row; no separate lineage read |
| `OT-GET-01` | `GET /object-templates` | `RP-01` | direct lineage page; internal parent tri-state supplied by application |
| `OT-GET-02` | `GET /object-templates/{id}` | `RP-02` | direct lineage exact read |
| `OT-GET-03` | `GET /object-templates/{id}/versions` | `RP-03` | lineage-rooted version page |
| `OT-GET-04` | `GET /object-templates/{id}/versions/{version}` | `RP-04` | exact header + independent properties/components |
| `OT-GET-05` | `GET /object-templates/{id}/versions/{version}/effective-schema` | `RP-05` | recursive exact-version chain |
| `OT-GET-06` | `GET /object-templates/{id}/relationship-capabilities` | `RP-06` | recursive stable-lineage ancestry page |
| `OBJ-GET-01` | `GET /objects` | `RP-01` | direct minimal ObjectSummary page |
| `OBJ-GET-02` | `GET /objects/{id}` | `RP-02` | direct intrinsic Object read; remove transitive schema/DataType certification |
| `OBJ-GET-03` | `GET /objects/{parent}/components` | `RP-07` + exact-chain context | complete `slot_declaring_template_id` from exact chain |
| `OBJ-GET-04` | `GET /objects/{child}/owner` | `RP-08` + exact-chain context | distinguish absent child / detached child / materialized owner |
| `OBJ-GET-05` | `GET /objects/{id}/lifecycle-events` | `RP-03` + ADP-03 decoder | target-rooted event page; decoder details deferred |
| `OBJ-GET-06` | `GET /objects/{id}/relationships` | `RP-07` | target-rooted deduplicated semantic Relationship-view page |
| `RD-GET-01` | `GET /relationship-definitions` | `RP-09` | page Definition root ids before expanding complete Resolution sets |
| `RD-GET-02` | `GET /relationship-definitions/{id}` | `RP-04` | exact aggregate header + complete Resolution set |
| `RD-GET-03` | `GET /relationship-definitions/{id}/versions` | `RP-03` | parent-rooted version page preserving parent 404 vs empty page |
| `RD-GET-04` | `GET /relationship-definitions/{id}/versions/{version}` | `RP-10` | distinguish parent absence, exact-version absence and empty property set |
| `REL-GET-01` | `GET /relationships/{id}` | `RP-04` | exact factual aggregate + deduplicated public `views[]` |
| `LC-GET-01` | `GET /lifecycle-events` | `RP-01` + ADP-03 decoder | existing direct event page retained; decoder cleanup deferred |

## DataType family

The four DataType GETs are direct/page patterns. `default_version` is projected without target publication certification. Version collections are parent-rooted so missing lineage remains distinct from an empty filtered page. Exact versions perform only representational decoding of persisted status/base type/constraints rather than constraint re-canonicalization.

## ObjectTemplate family

`OT-GET-01` receives the internal parent-filter tri-state from application; HTTP lexical omitted/UUID/lowercase-null handling remains ADP-05. Exact version aggregates keep properties and components independent and forbid a direct properties×components product.

Effective schema uses the persisted exact parent-version chain:

```text
(template_id, version)
    -> (parent_template_id, parent_version)
    -> ... exact root
```

and never substitutes stable lineage ancestry. Relationship capability membership instead uses stable lineage ancestry, then `RelationshipResolution.from_template_id IN ancestry`, optional name filtering, resolution-id keyset/order and the existing `EXISTS` predicate requiring at least one PUBLISHED RelationshipDefinitionVersion. That `EXISTS` remains collection-membership logic, not certification.

## Object family

`OBJ-GET-01` is a direct minimal summary page. `OBJ-GET-02` is a direct intrinsic Object read; persisted `properties` still require representational object/string-key decoding, but runtime schema/DataType recertification is removed.

`OBJ-GET-03` pages ownership facts and follows the parent Object's exact template-version chain only to obtain the unique `slot_declaring_template_id`. Missing or ambiguous contextual matches are internal projection failures and must not silently filter members.

`OBJ-GET-04` preserves:

```text
child absent                  -> 404
child present, no ownership   -> 200 null
ownership materializable      -> OwnerProjection
ownership not materializable  -> internal failure, never null
```

`OBJ-GET-05` is a target-rooted lifecycle page ordered/keyed `(occurred_at,id) DESC`; decoder semantics remain ADP-03.

`OBJ-GET-06` materializes complete public semantic Relationship views directly from persisted runtime/factual/Resolution state. Public semantic deduplication happens before keyset/order/limit:

```text
derive complete semantic rows
    -> DISTINCT / equivalent semantic deduplication
    -> keyset (relationship_id, destination_object_id, name)
    -> ORDER BY same tuple ASC
    -> LIMIT limit + 1
```

Cursor path-target corrections remain ADP-04.

## RelationshipDefinition family

`RD-GET-01` pages RelationshipDefinition root identities before Resolution expansion. Public page cardinality is defined by roots, not joined rows, so one selected aggregate can never be truncated by SQL row pagination.

`RD-GET-02` materializes one exact Definition aggregate and its complete Resolution set without `validate_definition()` or default-target recertification.

`RD-GET-03` is a parent-rooted status-filtered version page. Child filters/keyset must not erase parent presence.

`RD-GET-04` preserves separately:

```text
RelationshipDefinition parent absent
    -> parent 404

parent present + exact version absent
    -> exact-version 404

exact version present + zero properties
    -> success with properties=[]

exact version present + properties
    -> complete exact projection
```

Properties retain `position ASC`; persisted RDV semantic validators are not called by GET.

## REL-GET-01 — factual Relationship exact aggregate

Pattern:

```text
RP-04 — EXACT AGGREGATE / INDEPENDENT CHILD SETS
```

The one statement is rooted at the factual `relationships` row and materializes:

```text
relationship id
relationship_definition_id
relationship_definition_version
properties
views[]
    object_id
    destination_object_id
    name
```

The public `views[]` set is derived from persisted runtime resolution facts plus `relationship_resolutions.name`. Public-view `DISTINCT` / equivalent deduplication is projection semantics and does not re-certify why duplicate raw rows might exist.

Result semantics:

```text
Relationship root absent
    -> 404

Relationship root present + zero materializable views
    -> success with views=[]

Relationship root present + views
    -> complete factual projection
```

The root row must survive zero joined view rows. Persisted `properties` are decoded only as the JSON object carrier required by the response; no schema/property canonicalization is re-run.

The GET does not reconstruct or validate RelationshipDefinition, ObjectTemplate ancestry, endpoint templates, exact RelationshipDefinitionVersion or DataType dependencies. Mutation-oriented aggregate loaders remain strong for mutation flows; this GET uses a trusted projection boundary.

## LC-GET-01 — global lifecycle page

Pattern:

```text
RP-01 — DIRECT PAGE
+ ADP-03 trusted historical decoder
```

The existing single event-page query remains the target:

```text
object_lifecycle_events
    -> public filters
    -> keyset (occurred_at, id)
    -> ORDER BY occurred_at DESC, id DESC
    -> LIMIT limit + 1
```

All current public filters remain collection-membership inputs. There is no URI/path target and therefore no parent/existence marker requirement.

The query itself requires no recomposition in M3. Historical carrier decoding required to materialize typed lifecycle DTOs remains, but transition/state semantic certification is owned by ADP-03 and is not part of ADP-02.

# ADP-02 closure invariants

All twenty-two canonical public business GET/read routes now satisfy:

```text
one complete business SQL statement
ordinary read UoW
one PostgreSQL statement snapshot
no public-GET coherent_read() dependency
no mutation semantic validator as a read prerequisite
no hidden remediation or silent filtering of required state
canonical public ordering/filter/keyset semantics preserved
path-target absence versus empty-page/null semantics preserved
aggregate pages limit root/public items rather than arbitrary joined rows
nested exact resources preserve parent absence separately from exact-child absence
public semantic deduplication occurs before keyset/limit when membership requires it
```

Route-family closure:

```text
DataType             4 / 4 CLOSED
ObjectTemplate       6 / 6 CLOSED
Object               6 / 6 CLOSED
RelationshipDef      4 / 4 CLOSED
Relationship         1 / 1 CLOSED
Global lifecycle     1 / 1 CLOSED
------------------------------
total               22 / 22 CLOSED
```

ADP-02 is therefore **CLOSED**. No further route-shape decision is required unless a later architecture point discovers a contradiction with the frozen contract; such a contradiction must trigger governance reopening rather than silent reinterpretation.

# Preserved AS-IS responsibilities

ADP-01 and ADP-02 do not change:

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

ADP-03 must define lifecycle decoding exclusively as representational materialization, not transition certification, for both `OBJ-GET-05` and `LC-GET-01`.

`api.md` must preserve request/cursor/failure classification ownership without moving persistence semantic validation into the HTTP adapter. ADP-04 must realize the complete 12-route cursor identity rules, including `parent_object_id`, `object_id` and ObjectTemplate parent-filter presence semantics.

`verification.md` must prove:

```text
all 22 canonical GETs execute one business projection statement
public GETs do not re-certify mutation semantics
mutation semantic validation remains intact
single-request committed coherence is preserved
route-specific 404 / empty / null distinctions remain exact
```

# ADP status

```text
ADP-01  CLOSED
ADP-02  CLOSED
    DataType             4 / 4 CLOSED
    ObjectTemplate       6 / 6 CLOSED
    Object               6 / 6 CLOSED
    RelationshipDef      4 / 4 CLOSED
    Relationship         1 / 1 CLOSED
    Global lifecycle     1 / 1 CLOSED
    ------------------------------
    total               22 / 22 CLOSED
ADP-03  OPEN
```

No implementation authority is created by these closures. The architecture set remains `DESIGN IN PROGRESS — NOT FROZEN`.