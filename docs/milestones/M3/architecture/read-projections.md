# M3 — Public Read Projection Architecture

**Status:** DESIGN IN PROGRESS — ADP-01 CLOSED; ADP-02 PARTIAL (16 / 22); ADP-03 OPEN

**Authority:** M3 TO-BE ARCHITECTURE — PUBLIC READ PROJECTION OWNER

## Purpose and authority boundary

This document owns the M3 TO-BE architecture for the twenty-two canonical public business GET/read projections.

It derives from the frozen M3 contract and changes only the explicit M3 read-boundary delta. Delivered domain identities, mutation semantics, persistence schema, public DTOs, routing and failure behavior remain owned by the current AS-IS except where the frozen M3 contract explicitly changes them.

This document currently owns:

```text
ADP-01 — Read projection responsibility and reusable persistence boundary    CLOSED
ADP-02 — Complete 22-route one-statement projection matrix                  PARTIAL 16 / 22
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

M3 does not require a new package, class hierarchy or framework abstraction. `read projector` is an architectural role that may be realized by appropriately scoped persistence functions or methods.

## Application responsibility

The application read service owns semantics arising from the request rather than from persisted-state certification, including:

```text
request dependency rules
cursor route/filter/key compatibility
opening and closing the ordinary read UoW
404 versus successful-empty classification
Page/items/next-cursor composition
bounded application failure classification
```

Persistence may return explicit target-presence evidence. Persistence supplies the fact; application owns the public interpretation.

## Persistence projector responsibility

A read projector owns only the persisted facts required by the public projection:

```text
relational selection
joins / recursion / aggregation required by the projection
path-target existence evidence where required
member completion needed for required public fields
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

Therefore public reads must not re-run mutation-owned semantic certification such as:

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

Representational decoding remains required. A GET may and must perform the material checks needed to construct its typed result, for example:

```text
row/column extraction
UUID / integer / boolean / string conversion
closed-enum materialization
required persisted field presence
JSON object/array shape required by the response
historical snapshot materialization
```

A required field that cannot be materialized must not be silently dropped or repaired. The complete projection may fail through the existing bounded internal-failure boundary.

## Projection completion is not semantic certification

A projector may join persisted context solely to produce a required public field. That is projection, not semantic admission.

If one persisted public item requires exactly one contextual value, the projector must preserve the following representational rule:

```text
exactly one materializable contextual value
    -> project the item

zero materializable values
    -> required projection state cannot be constructed
    -> internal failure boundary

more than one materializable value where the DTO requires one
    -> ambiguous projection state
    -> internal failure boundary
```

The projector must never turn an unmaterializable persisted member into an apparently valid omission from the public collection.

## Reuse rule

Shared helpers are allowed when semantically neutral, such as:

```text
row -> typed carrier mapping
UUID / enum conversion
query-fragment construction
pure ordering/key helpers
pure response-shape assembly
```

Reuse is forbidden when it causes a GET to invoke mutation admission/transition validation, load dependencies solely to certify state, or add statements only because a mutation-oriented loader is broader than the public projection.

When a mutation loader is too broad, the GET uses a dedicated trusted read projector; the mutation loader remains strong.

## Unit of Work and snapshot rule

For the M3 canonical public GET census:

```text
one complete public projection
    -> one authoritative business SQL statement
    -> PostgreSQL statement snapshot
    -> ordinary read UoW
    -> no coherent_read() dependency
```

The preserved public guarantee is one self-consistent committed projection per request. Cross-request repeatable membership remains unpromised.

`coherent_read()` remains valid infrastructure outside this M3 census and is not globally deprecated.

## Path-target and empty collection rule

For path-scoped collections:

```text
target absent
    -> application 404 resource_not_found

target present + zero matching members
    -> successful empty page
```

The one-statement projector must carry enough target-presence evidence to preserve that distinction.

# ADP-02 — Projection-pattern vocabulary

ADP-02 uses named logical patterns to constrain correctness-critical query shape while leaving SQLAlchemy syntax, alias names and purely local decomposition to implementation.

## RP-01 — DIRECT PAGE

Use when one persisted relation directly represents the public collection.

```text
collection relation
    -> active filters
    -> keyset predicate
    -> canonical ORDER BY
    -> LIMIT limit + 1
```

No extra dependency read is added merely to certify persisted members.

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

Required result semantics:

```text
target absent             -> 404
target present, no child  -> 200 []
target present + child    -> normal page
```

A `LEFT JOIN`, lateral/target-rooted child subquery or equivalent form is valid only if child filters/keyset cannot erase the parent-only result.

## RP-04 — EXACT AGGREGATE / INDEPENDENT CHILD SETS

Use when an exact resource owns multiple independent zero-or-many child sets.

```text
exact target
    -> target/header existence branch
    -> independent child-set branch A
    -> independent child-set branch B
```

Required guarantees:

```text
exact target survives zero children
independent child sets never cartesian-multiply
ordering inside each child set remains canonical
all rows share one statement snapshot
```

Typed `UNION ALL`, independent SQL aggregation or another equivalent one-statement form is allowed only if those guarantees remain true.

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

`RP-05` and `RP-06` are intentionally different: exact-version ancestry must not be substituted for stable-lineage ancestry or vice versa.

## RP-07 — TARGET-ROOTED CONTEXT-COMPLETED PAGE

Use when the path target and the bounded primary member page are not alone sufficient to construct each public item; additional persisted context is required to complete mandatory public fields.

```text
path target
    -> target-presence evidence

bounded primary public-member candidate set
    -> filters
    -> keyset
    -> canonical ordering
    -> limit + 1

projection context
    -> joins / recursion required only to complete public fields

completed public page
```

Required guarantees:

```text
target absent                    -> 404
target present + no candidates   -> 200 []
completed candidates             -> normal page
required contextual field absent -> internal failure, never silent filtering
ambiguous required context        -> internal failure, never arbitrary choice
```

When raw persisted rows can duplicate one public semantic item, deduplication belongs to public-item derivation and therefore occurs **before** public keyset/limit semantics. A raw-row `LIMIT` followed by public deduplication is forbidden when it can change visible membership or cursor correctness.

## RP-08 — TARGET-ROOTED OPTIONAL PROJECTION

Use when the path target is required but the related public projection has cardinality `0..1` and absence of that relation has a public nullable meaning.

```text
required path target
    -> target absent: 404

optional related fact absent
    -> target exists: successful null projection

optional related fact present
    -> complete required contextual fields
    -> successful related projection
```

A related fact that exists but cannot be materialized must not be converted to public `null`; `null` means the optional relation is absent.

# ADP-02 — DataType family CLOSED

| ID | Route | Pattern | Key architecture consequence |
|---|---|---|---|
| `DT-GET-01` | `GET /datatypes` | `RP-01` | direct lineage page; project `default_version` without target certification |
| `DT-GET-02` | `GET /datatypes/{id}` | `RP-02` | direct lineage exact read; no default-target lookup |
| `DT-GET-03` | `GET /datatypes/{id}/versions` | `RP-03` | lineage-rooted version page preserving `404` vs `200 []` |
| `DT-GET-04` | `GET /datatypes/{id}/versions/{version}` | `RP-02` | exact composite version row; no separate lineage read |

## DT-GET-01 — lineage list

```text
source     datatypes
filters    namespace, name
keyset     (namespace, name)
order      (namespace, name) ASC
page       limit + 1
```

`default_version` is trusted persisted projection state; no publication lookup is part of the GET.

## DT-GET-02 — lineage exact

```text
datatypes WHERE id = :datatype_id
```

Zero rows -> lineage 404; one row -> direct projection. No default-target certification.

## DT-GET-03 — version page

```text
root       datatypes.id = :datatype_id
children   datatype_versions for that lineage
filter     status
keyset     version
order      version ASC
page       limit + 1
```

Child filters/keyset live inside the bounded child side so they cannot erase target-presence evidence.

## DT-GET-04 — exact version

```text
datatype_versions
WHERE datatype_id = :datatype_id
  AND version = :version
```

Persisted `status`, `base_type` and `constraints` are decoded representationally. The GET does not re-run constraint canonicalization/admission.

# ADP-02 — ObjectTemplate family CLOSED

| ID | Route | Pattern | Key architecture consequence |
|---|---|---|---|
| `OT-GET-01` | `GET /object-templates` | `RP-01` | direct lineage page; internal parent tri-state supplied by application |
| `OT-GET-02` | `GET /object-templates/{id}` | `RP-02` | direct lineage exact read |
| `OT-GET-03` | `GET /object-templates/{id}/versions` | `RP-03` | lineage-rooted version page |
| `OT-GET-04` | `GET /object-templates/{id}/versions/{version}` | `RP-04` | exact header + independent properties/components |
| `OT-GET-05` | `GET /object-templates/{id}/versions/{version}/effective-schema` | `RP-05` | recursive exact-version chain |
| `OT-GET-06` | `GET /object-templates/{id}/relationship-capabilities` | `RP-06` | recursive stable-lineage ancestry page |

## OT-GET-01 — lineage list

```text
source     object_templates
filters    namespace, name, abstract, internal parent-filter state
keyset     (namespace, name)
order      (namespace, name) ASC
page       limit + 1
```

HTTP lexical realization of omitted / UUID / lowercase `null` is owned by `api.md` / ADP-05. `default_version` is projected without target certification.

## OT-GET-02 — lineage exact

Direct exact `object_templates.id` projection. Stable parent and nullable default are facts to project, not dependencies to certify.

## OT-GET-03 — version page

`RP-03` over `object_templates` + bounded `object_template_versions`; status/keyset predicates must preserve lineage existence across an empty child page.

## OT-GET-04 — exact version aggregate

Public projection:

```text
ObjectTemplateVersion header
+ local properties[]
+ local components[]
```

Properties and components are independent child sets and must never be joined into a `properties × components` product. A typed multi-branch projection is preferred; an equivalent independent aggregation is allowed.

## OT-GET-05 — effective schema

The exact inheritance chain is:

```text
(template_id, version)
    -> (parent_template_id, parent_version)
    -> ... exact root
```

The GET follows only persisted exact pins. It does not read stable lineage merely to re-certify agreement with the exact chain.

The projector emits enough exact-chain/declaration data to construct the trusted effective schema with deterministic root-to-leaf ordering and `declaring_template_id`, without calling mutation-oriented effective-schema validators.

## OT-GET-06 — relationship capabilities

Capability membership uses stable ancestry:

```text
requested stable ObjectTemplate
    -> stable ancestors
    -> RelationshipResolution where from_template_id is in ancestry
    -> optional name filter
    -> resolution_id keyset/order
    -> LIMIT limit + 1
    -> EXISTS at least one PUBLISHED RelationshipDefinitionVersion
```

The `EXISTS(PUBLISHED ...)` predicate remains because it defines public collection membership. `RelationshipDefinition.default_version` is projected without loading/certifying its target.

# ADP-02 — Object family CLOSED

| ID | Route | Pattern | Key architecture consequence |
|---|---|---|---|
| `OBJ-GET-01` | `GET /objects` | `RP-01` | direct minimal ObjectSummary page |
| `OBJ-GET-02` | `GET /objects/{id}` | `RP-02` | direct intrinsic Object read; remove transitive schema/DataType certification |
| `OBJ-GET-03` | `GET /objects/{parent}/components` | `RP-07` + exact-chain context | page ownership facts, complete `slot_declaring_template_id` from exact chain |
| `OBJ-GET-04` | `GET /objects/{child}/owner` | `RP-08` + exact-chain context | distinguish absent child / detached child / materialized owner |
| `OBJ-GET-05` | `GET /objects/{id}/lifecycle-events` | `RP-03` + ADP-03 decoder | target-rooted event page; decoder details deferred to ADP-03 |
| `OBJ-GET-06` | `GET /objects/{id}/relationships` | `RP-07` | target-rooted deduplicated semantic Relationship-view page |

## OBJ-GET-01 — Object list

The existing one-statement summary projection remains the architecture target:

```text
source     objects summary columns
filters    template_id, dependent template_version, canonical_name
keyset     id
order      id ASC
page       limit + 1
```

`template_version requires template_id` remains request validation in application. An unknown filter value naturally yields an empty collection; it is not a path target and does not require an existence lookup.

## OBJ-GET-02 — intrinsic Object exact read

Direct exact `objects.id` projection.

Representational decoding of the persisted `properties` carrier remains required, including top-level object shape and string keys needed to build `dict[str, JsonValue]`.

The GET must remove transitive runtime-schema/DataType loading and persisted-property semantic re-canonicalization. Those are mutation-owned invariants and are not needed to construct the public Object DTO.

## OBJ-GET-03 — component page

Pattern:

```text
RP-07 — TARGET-ROOTED CONTEXT-COMPLETED PAGE
```

Required persisted inputs:

```text
parent Object exact (template_id, template_version)
recursive exact ObjectTemplateVersion parent chain
bounded object_components page
component declarations on that exact chain matching persisted slot_name
```

Public item fields are:

```text
slot_declaring_template_id
slot_name
child_object_id
```

`slot_declaring_template_id` is projection context. Looking it up does **not** authorize effective-schema or slot-admissibility certification.

The primary page is ownership facts ordered/keyed by `child_object_id`. `slot_name` remains an optional filter. The path target must survive an empty page.

For each paged ownership fact:

```text
exactly one matching declaration on the exact chain
    -> materialize ComponentProjection

zero matching declarations
    -> required public field cannot be materialized
    -> internal failure

more than one matching declaration
    -> ambiguous required public field
    -> internal failure
```

The query must not use an inner-join shape that silently removes an ownership fact when declaration context is missing.

Cursor query identity includes `parent_object_id`; the cursor owner and exact format are frozen in `api.md` / ADP-04.

## OBJ-GET-04 — owner projection

Pattern:

```text
RP-08 — TARGET-ROOTED OPTIONAL PROJECTION
```

Logical source:

```text
required child Object
    LEFT JOIN optional object_components ownership fact

if ownership exists
    -> parent Object exact (template_id, template_version)
    -> recursive exact ObjectTemplateVersion chain
    -> matching component declaration
    -> slot_declaring_template_id
```

Public outcomes are fixed:

```text
child absent
    -> 404

child present + no ownership fact
    -> 200 null

child present + one materializable ownership fact
    -> 200 OwnerProjection
```

A persisted ownership fact that cannot produce exactly one `slot_declaring_template_id` is an internal projection failure and must not be converted into `200 null`.

The GET does not re-check parent existence semantically, rebuild the full effective schema, or re-certify slot compatibility.

## OBJ-GET-05 — Object lifecycle page

Pattern:

```text
RP-03 — PARENT-ROOTED PAGE
```

The one statement combines:

```text
required path Object existence
filtered lifecycle event page
(occurred_at, id) DESC keyset/order
limit + 1
```

It must preserve:

```text
Object absent                -> 404
Object present + zero events -> 200 []
Object present + events      -> normal page
```

Historical row decoding is representational work but its exact boundary remains ADP-03. Once the projection is one statement, this GET uses an ordinary UoW and no `coherent_read()`.

## OBJ-GET-06 — Object-relative Relationship page

Pattern:

```text
RP-07 — TARGET-ROOTED CONTEXT-COMPLETED PAGE
```

The one statement combines:

```text
required Object target
runtime_relationship_resolutions
relationships
relationship_resolutions names
```

and materializes complete public `ObjectRelationshipView` rows:

```text
relationship_id
relationship_definition_id
relationship_definition_version
properties
object_id
destination_object_id
name
```

No `_validated_many()`-style reload of Relationship, RelationshipDefinition, ObjectTemplate or DataType aggregates belongs to the read path.

The public collection is a **deduplicated semantic-view set**, not raw runtime rows. Therefore the architecture order is:

```text
derive complete public semantic rows
    -> DISTINCT / equivalent semantic deduplication
    -> apply public keyset
       (relationship_id, destination_object_id, name)
    -> ORDER BY same tuple ASC
    -> LIMIT limit + 1
```

Applying the page limit to raw runtime rows and deduplicating afterward is forbidden when it can shorten pages, omit semantic views or corrupt cursor continuation.

Path-target framing must preserve:

```text
Object absent                  -> 404
Object present + zero views    -> 200 []
Object present + public views  -> normal page
```

Cursor query identity includes `object_id`; its exact construction is owned by `api.md` / ADP-04.

# Cross-family ADP-02 invariants currently frozen

For all sixteen covered routes:

```text
one complete business SQL statement
ordinary read UoW
one PostgreSQL statement snapshot
no public-GET coherent_read() dependency
no mutation semantic validator as a read prerequisite
no hidden remediation or silent filtering of required state
canonical public ordering and keyset semantics preserved
path-target absence versus empty-page/null semantics preserved
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

Remaining ADP-02 work must ensure every uncovered route:

```text
has one complete persistence projection boundary
uses no mutation semantic validator as a read prerequisite
preserves target-absence versus empty-collection behavior where applicable
preserves canonical ordering/filtering/keyset semantics
observes one committed statement snapshot
requires no public-GET coherent_read() dependency
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
    RelationshipDef      0 / 4 OPEN
    Relationship         0 / 1 OPEN
    Global lifecycle     0 / 1 OPEN
    ------------------------------
    total               16 / 22
ADP-03  OPEN
```

No implementation authority is created by these closures. The architecture set remains `DESIGN IN PROGRESS — NOT FROZEN`.