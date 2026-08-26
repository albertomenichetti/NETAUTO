# M3 — Public Read Projection Architecture

**Status:** FINAL / FROZEN — ADP-01 / ADP-02 / ADP-03 CLOSED

**Authority:** M3 TO-BE ARCHITECTURE — PUBLIC READ PROJECTION OWNER

## Purpose and authority boundary

This document owns the M3 TO-BE architecture for the twenty-two canonical public business GET/read projections and the trusted historical lifecycle decoding boundary used by the lifecycle read surfaces.

It derives from the frozen M3 contract and changes only the explicit M3 read-boundary delta. Delivered domain identities, mutation semantics, persistence schema, public DTOs, routing and failure behavior remain owned by the current AS-IS except where the frozen M3 contract explicitly changes them.

Current design ownership:

```text
ADP-01 — Read projection responsibility and reusable persistence boundary    CLOSED
ADP-02 — Complete 22-route one-statement projection matrix                  CLOSED 22 / 22
ADP-03 — Historical lifecycle trusted decoder                              CLOSED
```

This owner is `FINAL / FROZEN`. Implementation remains unauthorized until `steps.md` is frozen and `status.md` explicitly authorizes a slice.

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
| `OBJ-GET-05` | `GET /objects/{id}/lifecycle-events` | `RP-03` + ADP-03 decoder | target-rooted event page + trusted historical decoding |
| `OBJ-GET-06` | `GET /objects/{id}/relationships` | `RP-07` | target-rooted deduplicated semantic Relationship-view page |
| `RD-GET-01` | `GET /relationship-definitions` | `RP-09` | page Definition root ids before expanding complete Resolution sets |
| `RD-GET-02` | `GET /relationship-definitions/{id}` | `RP-04` | exact aggregate header + complete Resolution set |
| `RD-GET-03` | `GET /relationship-definitions/{id}/versions` | `RP-03` | parent-rooted version page preserving parent 404 vs empty page |
| `RD-GET-04` | `GET /relationship-definitions/{id}/versions/{version}` | `RP-10` | distinguish parent absence, exact-version absence and empty property set |
| `REL-GET-01` | `GET /relationships/{id}` | `RP-04` | exact factual aggregate + deduplicated public `views[]` |
| `LC-GET-01` | `GET /lifecycle-events` | `RP-01` + ADP-03 decoder | direct event page + trusted historical decoding |

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

`OBJ-GET-05` is a target-rooted lifecycle page ordered/keyed `(occurred_at,id) DESC` and uses the ADP-03 trusted historical decoder.

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

The existing single event-page query remains the target:

```text
object_lifecycle_events
    -> public filters
    -> keyset (occurred_at, id)
    -> ORDER BY occurred_at DESC, id DESC
    -> LIMIT limit + 1
```

All current public filters remain collection-membership inputs. There is no URI/path target and therefore no parent/existence marker requirement. Historical carrier materialization is defined by ADP-03 below.

## ADP-02 closure invariants

All twenty-two canonical public business GET/read routes satisfy:

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

ADP-02 is **CLOSED**. No further route-shape decision is required unless a later architecture point discovers a contradiction with the frozen contract; such a contradiction must trigger governance reopening rather than silent reinterpretation.

# ADP-03 — CLOSED — Historical lifecycle trusted decoder

## Scope

ADP-03 owns the historical carrier decoder shared by:

```text
OBJ-GET-05  GET /objects/{id}/lifecycle-events
LC-GET-01   GET /lifecycle-events
```

It does not change lifecycle write semantics, event kinds, DTO fields, database schema, event persistence format, ordering/filtering or cursor behavior.

The decoder boundary is deliberately narrow:

```text
historical read decoder
    asks: "can these persisted carriers be materialized into the required typed historical response?"

historical read decoder
    does NOT ask: "would this historical state/transition pass current mutation validation?"
```

## Database structural authority

The delivered lifecycle table already owns structural constraints for:

```text
allowed EventKind values
family-specific nullable/non-null columns
before_state / after_state presence shape per EventKind
before_state / after_state top-level JSON object shape when present
outer canonical-name length
outer slot_name / relationship_name identifier carrier shape
```

Public reads do not duplicate those database constraints as a second semantic certification layer.

If a required carrier nevertheless cannot be materialized at runtime, the read fails through the bounded internal-failure boundary. This is representational failure, not mutation-semantic recertification.

## Event-kind materialization

The persisted `kind` carrier is converted to `EventKind` because the typed discriminant is required to select the historical event family.

```text
persisted kind string
    -> EventKind
    -> typed intrinsic / ownership / Relationship historical projection
```

A value that cannot be converted to the closed `EventKind` type is materially undecodable and fails internally. The decoder does not separately re-prove the database CHECK constraint.

## Historical JsonValue decoder

Historical JSON values are decoded according to the public `JsonValue` carrier type, not current runtime Object/Relationship property admission rules.

Accepted recursive carrier grammar:

```text
None
str
bool
int, excluding bool
list[JsonValue]          including []
dict[str, JsonValue]     including {}
```

Therefore historical decoding must not impose runtime-property restrictions such as:

```text
property-name identifier grammar
non-null runtime property values
non-empty list requirement
homogeneous list primitive types
current DataType/schema canonicalization
```

A historical property map is representationally valid when it can be decoded as:

```text
dict[str, JsonValue]
```

Nested lists/objects and JSON null are accepted when they are valid `JsonValue` carriers, even if the current mutation model would reject the same value as current runtime Object/Relationship state.

Non-`JsonValue` Python carriers, non-string JSON object keys or otherwise unmaterializable required JSON fail internally.

## Historical Object snapshot decoding

An intrinsic historical Object snapshot requires these fields to construct the public `ObjectDto` carrier:

```text
id
canonical_name
template_id
template_version
properties
```

Required decoding:

```text
snapshot carrier       -> object/dict
id                     -> string parseable as UUID
template_id            -> string parseable as UUID
canonical_name         -> str
template_version       -> int, excluding bool
properties             -> dict[str, JsonValue]
```

The read decoder does **not** re-certify:

```text
canonical_name length 1..255
template_version > 0
property-name identifier grammar
runtime property admissibility/canonicality
current ObjectTemplate/DataType closure
```

Missing required fields make the snapshot materially undecodable and fail internally.

Extra historical JSON fields that are not required by the public snapshot are ignored. Exact internal JSON key-set equality is not a public read invariant and must not be used as certification.

The current plain `Object` value carrier may be reused because it is a data container; no current-state Object semantic validator is invoked by historical decoding.

## Historical Relationship factual-state decoding

A historical Relationship factual state requires:

```text
relationship_definition_version
properties
```

Required decoding:

```text
state carrier                     -> object/dict
relationship_definition_version   -> int, excluding bool
properties                        -> dict[str, JsonValue]
```

The decoder does **not** require `relationship_definition_version > 0` as a read-side semantic certification rule and does not load the current RelationshipDefinitionVersion or DataType dependencies.

Missing required fields fail internally. Extra historical JSON fields not required by the public factual-state DTO are ignored.

## Outer event-field decoding

Database-native typed columns needed by a selected event family are projected mechanically:

```text
UUID columns       -> UUID carrier
datetime column    -> datetime carrier
text columns       -> str carrier
nullable family columns -> consumed according to the selected EventKind family
```

The decoder may fail if a field required to construct the selected typed projection is materially absent or of an unusable runtime carrier type. It does not maintain a duplicate whole-row family-shape certification matrix merely to re-prove database constraints.

In particular, the read path removes duplicated checks whose only purpose is to prove that ownership rows have no before/after state or that Relationship rows have no slot columns. The database remains structural authority for those shapes.

## Intrinsic transition certification removed

After mechanical snapshot decoding, the historical GET must not compare outer event fields and snapshots to prove mutation semantics.

Remove read-side checks such as:

```text
before.id == outer object_id
after.id == outer object_id
after.canonical_name == outer canonical_name
```

and event-specific transition certification:

```text
RENAME
    template_id unchanged
    template_version unchanged
    properties unchanged

DATA_CHANGE
    canonical_name unchanged
    template_id unchanged
    template_version unchanged
    properties changed

SCHEMA_CHANGE
    canonical_name unchanged
    template_id unchanged
    template_version increased

DELETED
    before.canonical_name == outer canonical_name
```

These are mutation/write-owned transition invariants, not historical response-decoding requirements.

## Relationship transition certification removed

After factual-state decoding, the historical GET must not re-prove Relationship mutation semantics.

Remove read-side checks such as:

```text
RELATIONSHIP_DATA_CHANGE
    before.relationship_definition_version == after.relationship_definition_version
    before.properties != after.properties

RELATIONSHIP_SCHEMA_CHANGE
    after.relationship_definition_version > before.relationship_definition_version
```

No current Relationship, RelationshipDefinition, exact RelationshipDefinitionVersion, ObjectTemplate lineage or DataType lookup is performed merely to reinterpret historical event state.

## Before/after state-shape ownership

The database already owns the `before_state` / `after_state` presence matrix for all event kinds.

The trusted read pipeline therefore uses the already-decoded `EventKind` to materialize the corresponding typed historical variant without duplicating a second semantic rule such as:

```text
CREATED must be before=None, after=present
DELETED must be before=present, after=None
changed event must have before+after
Relationship-created/deleted/changed equivalents
```

If implementation retains coarse internal dataclasses with optional `before`/`after`, kind-directed typing casts or equivalent programmer-facing narrowing may be used. A dedicated more-precise internal discriminated variant is also allowed. The architecture freezes the responsibility boundary, not a class hierarchy.

## HTTP DTO adapter

The HTTP adapter selects the public discriminated DTO mechanically from the already-decoded historical event family/kind.

It must not repeat persisted-state certification through branches of the form:

```text
kind == X AND before/after is not None
```

for the purpose of proving database event shape again.

Typing narrowing, casts or equivalent exhaustive mapping are allowed when needed by the type checker. The adapter remains responsible for DTO construction and serialization only.

## Write-path separation

Lifecycle mutation/write validation remains strong.

The current implementation may share decoder functions between persisted reads and rows returned immediately after writes. M3 does not allow a mutation invariant to become weaker merely because the public historical read decoder is decoding-only.

Therefore:

```text
mechanical carrier decoding
    -> may be shared

mutation transition / event-set correctness
    -> remains on mutation/write boundary
    -> must not depend on public GET semantic recertification
```

If an existing mutation path currently relies on semantic checks embedded in the shared read decoder, those checks must remain or be relocated to the mutation/write path before the read decoder is simplified.

This separation applies to intrinsic, ownership and Relationship lifecycle writes. It does not authorize weakening write-side validation or event atomicity.

## ADP-03 KEEP / REMOVE matrix

```text
KEEP — representational decoding
    EventKind materialization
    required historical field presence needed for DTO construction
    UUID parsing for UUIDs serialized inside JSON snapshots
    exact primitive carrier typing needed by DTO fields
    recursive JsonValue decoding
    dict[str, JsonValue] materialization
    typed historical event-family projection
    bounded internal failure for materially undecodable required state

REMOVE — read-side semantic certification
    historical property-name identifier grammar
    runtime-property non-null / non-empty-list / homogeneous-list rules
    canonical-name bounds inside JSON snapshots
    positive-version checks inside JSON snapshots/factual states
    exact internal JSON key-set equality
    outer-row vs snapshot identity/name agreement
    intrinsic RENAME/DATA_CHANGE/SCHEMA_CHANGE transition semantics
    Relationship DATA_CHANGE/SCHEMA_CHANGE transition semantics
    duplicated database family/state-shape certification
    HTTP before/after presence recertification
    live/current-state lookups used only to reinterpret history
```

## ADP-03 failure boundary

The distinction frozen by ADP-03 is:

```text
persisted state semantically surprising under current mutation rules
    + still materially decodable as the frozen public historical carrier
    -> RETURN the historical representation

persisted state missing/malformed such that a required public carrier cannot be built
    -> bounded internal failure
```

The read never fabricates missing required fields, silently drops an event, repairs historical state or substitutes current live state.

ADP-03 is **CLOSED**.

# Preserved AS-IS responsibilities

ADP-01, ADP-02 and ADP-03 do not change:

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
lifecycle mutation/event atomicity
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

For lifecycle history this means semantically surprising but representationally decodable historical carriers remain readable. Representationally undecodable required state still fails safely. M3 introduces neither read-time repair nor silent corruption tolerance.

This contract-authorized contradiction must be propagated to the delivered AS-IS during final consolidation after implementation/acceptance.

# Downstream architecture constraints

`api.md` must preserve request/cursor/failure classification ownership without moving persistence semantic validation into the HTTP adapter. ADP-04 must realize the complete 12-route cursor identity rules, including `parent_object_id`, `object_id` and ObjectTemplate parent-filter presence semantics.

`verification.md` must prove:

```text
all 22 canonical GETs execute one business projection statement
public GETs do not re-certify mutation semantics
historical lifecycle GETs retain representational decoding but no transition certification
materially undecodable historical carriers fail through the bounded internal boundary
semantically surprising but decodable historical carriers remain readable
mutation semantic and lifecycle-write validation remains intact
single-request committed coherence is preserved
route-specific 404 / empty / null distinctions remain exact
```

# ADP status

```text
ADP-01  CLOSED
ADP-02  CLOSED — 22 / 22
ADP-03  CLOSED
```

This owner is `FINAL / FROZEN`. No implementation authority is created by architecture freeze; implementation remains gated by frozen `steps.md` and explicit `status.md` authorization.