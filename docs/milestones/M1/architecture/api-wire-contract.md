# M1 — API Wire Contract

**Status:** DRAFT — API-03.1..10 e API-03.11A ratificati. Command DTO, exact/implicit selector, `expected_revision`, PrimitiveType public lexical forms, canonical read DTO, collection/list contract e failure-class/HTTP mapping baseline sono consolidati. Restano concrete error-code catalog e success HTTP mapping (API-03.11B).

## 1. Scopo e boundary

Questo documento è il registry normativo delle decisioni API-03 relative alla public HTTP/JSON representation M1.

Catena normativa:

```text
domain/application command semantics
-> accepted public wire input
-> transport shape validation
-> domain parse / validation / canonicalization
-> canonical domain value/state
-> canonical persistence / read output
```

La wire ergonomics non può restringere, ampliare o reinterpretare implicitamente il domain contract ratificato.

Prima di ogni nuovo API-03 point si applica il pre-flight definito in `docs/general/linee_guida_progetto.md` e in `architecture/README.md`.

Authority companion:

```text
api-read-contract.md
    -> API-03.9 canonical single/projection DTO

api-list-contract.md
    -> API-03.10 collection envelope, keyset pagination,
       ordering, list-item policy and filters

api-error-contract.md
    -> API-03.11 failure classes, HTTP/error-body mapping,
       concrete error-code catalog and success mapping
```

---

## 2. API-03.1 — strict wire shape e caller intent

Regole:

- JSON object keys `snake_case`;
- semantic command path segments `kebab-case`;
- unknown command fields rejected;
- generic scalar coercion rejected;
- omission e explicit caller intent distinti;
- defaults/implicit resolution colmano soltanto omission quando il command contract lo definisce;
- explicit invalid input fallisce e non viene sostituito da default;
- JSON `null` è valido soltanto quando `null` stesso è semantic state valido.

Object CREATE:

```text
canonical_name omitted
    -> canonical_name = str(Object.id)

canonical_name explicit valid string 1..255
    -> use exactly that value

canonical_name = null / "" / invalid
    -> failure
```

Implicit exact-version binding usa omissione del version field, mai explicit `null`.

```text
A3.1  JSON keys use snake_case; command route segments use kebab-case.
A3.2  Command DTOs reject unknown fields and generic scalar coercion.
A3.3  Omission and explicit caller intent are distinct.
A3.4  Defaults/implicit resolution apply only to omitted fields where explicitly defined.
A3.5  Explicit invalid input fails and is never repaired/replaced by a default.
A3.6  JSON null is valid only when null itself is a valid semantic field state.
A3.7  Object CREATE canonical_name omission uses UUID-string fallback; explicit invalid input fails.
A3.8  Implicit exact-version/default resolution is represented by omission, never null.
A3.9  Canonical responses follow canonical domain state, not caller lexical form.
A3.10 Transport handles syntax/shape; persisted-state semantic validation remains below it.
```

---

## 3. API-03.2 — `expected_revision`

`expected_revision` è il generation precondition esclusivamente di DTV/OTV `REVISE`, `PUBLISH`, `DELETE_DRAFT`.

Public representation uniforme:

```text
?expected_revision=<positive-decimal-integer>
```

```text
path
    -> exact mutation target
query expected_revision
    -> DRAFT generation precondition
body, if any
    -> semantic candidate / command operands
```

REVISE body non contiene il token. PUBLISH e DELETE_DRAFT non introducono body artificiali. M1 non usa `ETag`, `If-Match` o custom revision header per questa semantica.

Missing/empty/zero/negative/malformed token è transport-input failure; positive integer ben formato ma stale è application generation-conflict failure.

```text
A3.11 expected_revision is a required query parameter for DTV/OTV REVISE, PUBLISH and DELETE_DRAFT.
A3.12 It is not resource identity and never appears in the path.
A3.13 REVISE body contains only the complete desired mutable candidate.
A3.14 PUBLISH has no artificial body solely for expected_revision.
A3.15 DELETE_DRAFT has no body and uses the same query representation.
A3.16 No ETag/If-Match/custom revision-header contract in M1.
A3.17 Malformed/missing token is transport failure; stale well-formed token is application conflict.
```

---

## 4. API-03.3 — exact e implicit version selector

M1 non introduce generic `VersionSelector` e non usa token `default`, `latest`, `highest`.

Stable lineage identity ed exact version sono sibling fields type-specific:

```text
template_id / template_version
parent_template_id / parent_version
datatype_id / datatype_version
```

Omitted version significa implicit default soltanto quando la owning domain command definisce già implicit binding.

```text
Object CREATE template_version omitted
    -> ObjectTemplate.default_version

OT CREATE parent_template_id omitted
    -> root; parent_version forbidden

OT CREATE parent_template_id present + parent_version omitted
    -> parent.default_version

OT REVISE non-root parent_version omitted
    -> intentional rebind via current parent default

OT REVISE root parent_version
    -> forbidden

property datatype_version omitted
    -> intentional DataType.default_version binding/rebinding
```

Exact-only required selectors:

```text
DT.CREATE_NEXT.source_version
OT.CREATE_NEXT.source_version
DT.SET_DEFAULT.version
OT.SET_DEFAULT.version
Object.SCHEMA_CHANGE.target_version
```

```text
A3.18 Version selection uses type-specific flat fields, not a generic VersionSelector or default/latest token.
A3.19 Stable lineage identity and exact version are separate sibling fields.
A3.20 Omitted version means implicit default only where the owning domain command defines implicit binding.
A3.21 Object CREATE template_version omission resolves ObjectTemplate.default_version; null is invalid; no latest/highest fallback.
A3.22 OT CREATE: parent_template_id omitted = root; present + parent_version omitted = implicit parent default; both present = exact parent.
A3.23 OT REVISE never carries parent_template_id; non-root parent_version omission intentionally rebinds via current parent default; root forbids parent_version.
A3.24 Property datatype_version omission intentionally performs implicit DataType default binding/rebinding; preserving historical exact pin requires explicit version.
A3.25 DT/OT CREATE_NEXT source_version, SET_DEFAULT version and Object SCHEMA_CHANGE target_version are mandatory exact selectors.
A3.26 M1 exposes no generic default/latest/highest selector token.
```

---

## 5. API-03.4 — DataType command DTO

### CREATE

Required:

```text
namespace
name
base_type
```

Optional:

```text
description omitted -> initial null
description = null -> valid nullable state
constraints omitted -> creation default {}
constraints = {} -> explicit zero-constraint candidate
constraints = null -> invalid
```

Caller non fornisce `id`, `version`, `revision`, `status`, `default_version`.

Constraint matrix:

```text
core.string      -> min_length, max_length, pattern, enum
core.integer     -> minimum, maximum, enum
core.number      -> minimum, maximum, enum
core.boolean     -> enum
core.date        -> minimum, maximum, enum
core.datetime    -> minimum, maximum, enum
core.ip          -> ip_version, enum
core.ip_prefix   -> ip_version, enum
core.byte_size   -> minimum, maximum, enum
```

### REVISE

Body contiene esclusivamente required `constraints` complete candidate. `{}` significa zero constraints; omission non significa keep-current.

Forbidden: lineage metadata, `description`, `base_type`, lifecycle/default state, version/revision, `expected_revision`.

Other commands:

```text
CREATE_NEXT     { "source_version": N }
PUBLISH         no body + expected_revision query
SET_DEFAULT     { "version": N }
CLEAR_DEFAULT   no body
DEPRECATE       no body
DELETE_DRAFT    no body + expected_revision query
DELETE_LINEAGE  no body
SET_DESCRIPTION { "description": string|null }
```

```text
A3.27 DT.CREATE accepts namespace, name, base_type, optional description and optional constraints; IDs/version/revision/status/default are server state.
A3.28 DT.CREATE constraints omission means creation default {}; constraints=null is invalid.
A3.29 DT.REVISE is complete mutable-candidate replacement and requires constraints.
A3.30 DT.REVISE constraints={} explicitly means zero constraints; omission never means keep-current.
A3.31 DT.REVISE cannot carry lineage metadata, base_type, lifecycle/default state or expected_revision in its body.
A3.32 constraints is a JSON object whose allowed keys are determined by the fixed M1 primitive constraint matrix.
A3.33 Constraint values reuse the same PrimitiveType public-input and canonicalization contract used everywhere else.
A3.34 CREATE_NEXT and SET_DEFAULT use mandatory exact version bodies; PUBLISH/CLEAR_DEFAULT/DEPRECATE have no body.
A3.35 SET_DESCRIPTION body contains exactly description:string|null; null is valid because description itself is nullable state.
A3.36 DataType command DTOs never expose caller-controlled id, version, revision, status or default_version state.
```

---

## 6. API-03.5 — ObjectTemplate command DTO

### CREATE

Required:

```text
namespace
name
abstract
```

`abstract` non possiede omitted->false default.

```text
description omitted -> null
properties omitted  -> []
components omitted  -> []
properties/components = null -> invalid
```

Parent fields seguono API-03.3.

Property declaration always required:

```text
name
position
datatype_id
value_mode
required
```

`datatype_version` può essere omessa soltanto per intentional implicit DTV default binding/rebinding.

`migration_default`:

```text
required=false
    -> MUST be absent

required=true + SCALAR
    -> REQUIRED, one concrete value

required=true + LIST
    -> REQUIRED, non-empty list
```

`migration_default:null` invalido.

Component declaration contiene esattamente:

```text
name
position
target_template_id
```

`position` è explicit declaration state. Request array order non è semantic authority.

### REVISE

Complete local-candidate replacement:

```text
properties required, including []
components required, including []
```

Non-root `parent_version` segue API-03.3; root lo vieta.

Forbidden: stable lineage metadata, `abstract`, `parent_template_id`, lifecycle/default state, `expected_revision`.

New/historical declarations usano la stessa transport shape; historical evolution legality resta domain validation.

```text
A3.37 OT.CREATE requires namespace, name and explicit abstract; abstract has no omitted->false public default.
A3.38 OT.CREATE description omission means null; properties/components omission means creation default []; explicit null is invalid.
A3.39 OT CREATE parent fields follow API-03.3 flat selector semantics.
A3.40 Property declaration requires name, position, datatype_id, value_mode and required; datatype_version is optional only for intentional implicit DataType-default binding.
A3.41 migration_default is conditionally forbidden/required: optional property -> absent; required SCALAR -> one value; required LIST -> non-empty list; JSON null invalid.
A3.42 Component declaration contains exactly name, position, target_template_id; all required; no exact target version/cardinality fields.
A3.43 position is explicit declaration state and is never inferred from request-array ordering.
A3.44 Property/component request-array order is not semantic authority; position determines local ordering.
A3.45 OT.REVISE is complete local-candidate replacement; properties/components arrays are always required, including explicit [].
A3.46 OT.REVISE parent_version follows API-03.3: non-root omission intentionally rebinds via parent default; root forbids it.
A3.47 OT.REVISE cannot carry stable lineage metadata, abstract, parent_template_id, lifecycle/default state or expected_revision.
A3.48 The same declaration DTO shape is used for new and historical members; historical evolution legality remains domain validation, not transport DTO branching.
```

---

## 7. API-03.6 — Object command DTO

### CREATE

Required `template_id`.

```text
template_version omitted -> ObjectTemplate.default_version
canonical_name omitted   -> str(Object.id)
properties omitted       -> {}
```

`properties={}` significa zero runtime values forniti; non attiva `migration_default` e non soddisfa required properties mancanti.

Properties JSON object keyed by effective property name:

```text
SCALAR -> one PrimitiveType input value
LIST   -> JSON array
```

JSON null non è runtime property value. Optional LIST `[]` canonicalizza ad assenza; required LIST `[]` fallisce.

### RENAME

Body contiene esattamente `canonical_name:string`, valido `1..255`.

### DATA_CHANGE

Required non-empty `operations` array con discriminator:

```text
SET    -> exactly op, property, value
REMOVE -> exactly op, property; value forbidden
```

Una property compare al massimo una volta. Array order non è semantic authority. Empty operations è malformed; non-empty request può convergere a semantic no-op senza lifecycle event.

### SCHEMA_CHANGE

Body contiene esattamente mandatory `target_version`; nessun remediation/override/detach/cross-lineage field.

### ATTACH / DETACH

Body comune:

```text
slot_name
child_object_id
```

`parent_object_id` resta path target. Shared DTO non implica shared admission semantics: ATTACH valida current slot/compatibility, DETACH rimuove exact edge anche se slot non esiste più nello current schema.

### DELETE

No body, no cascade/force/recursive options.

```text
A3.49 Object CREATE requires template_id; template_version, canonical_name and properties are optional with their ratified omission semantics.
A3.50 Object CREATE properties omission means {}: zero supplied runtime values; it never activates migration_default or satisfies required properties.
A3.51 Object properties are a JSON object keyed by effective property name; SCALAR uses one primitive input value, LIST a JSON array; JSON null is never a runtime property value.
A3.52 Object RENAME body contains exactly canonical_name:string.
A3.53 DATA_CHANGE body contains a required non-empty operations array discriminated by SET | REMOVE.
A3.54 SET requires exactly op/property/value; REMOVE requires exactly op/property and forbids value.
A3.55 A property may occur at most once in one DATA_CHANGE request; operation-array order has no semantic meaning.
A3.56 Empty DATA_CHANGE operations is malformed; a non-empty request may converge to semantic no-op with no lifecycle event.
A3.57 SET [] remains valid for an optional LIST and canonicalizes to absence; SET null is invalid.
A3.58 SCHEMA_CHANGE body contains exactly mandatory target_version; no remediation, override, detach or cross-lineage fields exist.
A3.59 ATTACH and DETACH bodies contain exactly slot_name and child_object_id; parent_object_id remains the path command target.
A3.60 Shared ATTACH/DETACH DTO does not imply shared admission semantics: ATTACH validates current slot/compatibility, DETACH may remove an exact runtime edge even when the slot is absent from the current schema.
A3.61 Object DELETE has no body and exposes no cascade/force/recursive options.
A3.62 Object command DTOs never expose caller-controlled Object id, template_id mutation, state revision, ownership edge id or lifecycle data.
```

---

## 8. API-03.7 — RelationshipDefinition / Relationship command DTO

RelationshipDefinition CREATE è strict union discriminata da required `symmetric`.

Non-symmetric:

```text
symmetric=false
perspectives = exactly two unordered {template_id,name}
```

Names distinti.

Symmetric:

```text
symmetric=true
endpoint_template_ids = exactly two unordered lineage IDs; may be equal
name = one semantic name
```

Definition/Resolution IDs sono kernel-generated.

RelationshipDefinition RENAME non reinvia `symmetric`.

```text
non-symmetric
    -> complete unordered two-element resolutions {resolution_id,name}

symmetric
    -> exactly one name
```

Shape/current-symmetry mismatch è semantic command failure.

RelationshipDefinition DELETE no body/no cascade-force.

Relationship CREATE body contiene esattamente:

```text
resolution_id
from_object_id
to_object_id
```

Relationship ID e definition metadata non sono caller-supplied. Self-loop non è transport-rejected.

Relationship DELETE è exact relationship_id path based, no body, no semantic-tuple alternative.

```text
A3.63 RelationshipDefinition CREATE is a strict union discriminated by the required symmetric boolean.
A3.64 Non-symmetric CREATE contains exactly symmetric=false and a two-element perspectives array of {template_id,name}; perspective order is not semantic and names must be distinct.
A3.65 Symmetric CREATE contains exactly symmetric=true, a two-element endpoint_template_ids array and one semantic name; endpoint order is not semantic and the IDs may be equal.
A3.66 Definition/Resolution identities are kernel-generated during CREATE; callers never supply them.
A3.67 RelationshipDefinition RENAME does not resend symmetric.
A3.68 Non-symmetric RENAME body contains a complete two-element resolutions array of {resolution_id,name}; order is irrelevant and duplicate resolution IDs are invalid.
A3.69 Symmetric RENAME body contains exactly one name field, independent of whether the aggregate physically owns one or two Resolutions.
A3.70 RENAME request shape and current Definition symmetry must agree; mismatch is a semantic command failure.
A3.71 RelationshipDefinition DELETE has no body and no cascade/force option.
A3.72 Relationship CREATE body contains exactly resolution_id, from_object_id and to_object_id; all required.
A3.73 Relationship CREATE never accepts caller-supplied relationship_id, relationship_definition_id, names or endpoint template metadata.
A3.74 from_object_id == to_object_id is not rejected structurally; self-loop admission remains domain semantics.
A3.75 Relationship DELETE is exact relationship_id based, has no body, and exposes no semantic-tuple delete alternative.
A3.76 Array ordering never creates orientation for semantic unordered Definition sets; source/target or forward/reverse fields remain absent.
```

---

## 9. API-03.8 — PrimitiveType public lexical forms

Ogni PrimitiveType possiede un unico public input carrier/lexical contract riusato per Object property, DTV constraints/enum e OTV `migration_default`.

| Primitive | Accepted public input | Canonical output |
|---|---|---|
| `core.string` | JSON string | identical JSON string |
| `core.integer` | JSON integer | JSON integer |
| `core.number` | exact-decimal JSON string | canonical exact-decimal string |
| `core.boolean` | JSON boolean | JSON boolean |
| `core.date` | zero-padded `YYYY-MM-DD` | `YYYY-MM-DD` |
| `core.datetime` | strict offset/Z datetime string | canonical UTC `Z` string |
| `core.ip` | IPv4/IPv6 address string | canonical IP string |
| `core.ip_prefix` | explicit CIDR address/prefix-length | canonical CIDR string |
| `core.byte_size` | exact integer bytes OR strict SI/IEC quantity string | exact integer bytes |

`core.number` grammar:

```text
-?(0|[1-9][0-9]*)(\.[0-9]+)?
```

No plus/exponent/NaN/Infinity. Numeric-equivalent strings canonicalizzano secondo PERSIST-12; negative zero -> `"0"`.

`core.date`: Gregorian `0001-01-01..9999-12-31`.

`core.datetime`:

```text
YYYY-MM-DDTHH:MM:SS[.fraction](Z|±HH:MM)
```

Offset obbligatorio, no leap-second `:60`, no rounding. Digits beyond sixth accepted only when all zero; canonical output UTC `Z` with trailing fractional zeros removed.

`core.ip`: no CIDR/zone identifier. `core.ip_prefix`: explicit CIDR, no netmask aliases, host bits rejected rather than corrected.

```text
A3.77 Every PrimitiveType has one public input carrier/lexical contract reused for Object values, DataType constraints/enums and migration_default.
A3.78 core.string accepts only JSON string and performs identity canonicalization; no trimming, case folding or Unicode/business normalization.
A3.79 core.integer accepts only a JSON integer; booleans, strings, floating-number and exponent forms are not integer inputs.
A3.80 core.number accepts only an exact-decimal JSON string using -?(0|[1-9][0-9]*)(\.[0-9]+)?; no plus sign or exponent notation; canonical output follows PERSIST-12 exact-decimal rules.
A3.81 core.boolean accepts only JSON true/false.
A3.82 core.date accepts exactly zero-padded YYYY-MM-DD Gregorian dates in range 0001-01-01..9999-12-31.
A3.83 core.datetime accepts YYYY-MM-DDTHH:MM:SS[.fraction](Z|±HH:MM), requires an absolute offset, rejects leap-second :60 and never rounds fractional precision.
A3.84 Datetime digits beyond microseconds are accepted only when all digits beyond the sixth are zero; canonical output is UTC Z with trailing fractional zeros removed.
A3.85 core.ip accepts valid IPv4/IPv6 textual addresses, no zone identifier or CIDR; output is canonical address text.
A3.86 core.ip_prefix requires explicit address/prefix-length CIDR syntax; host bits are rejected, never normalized away; netmask aliases are not accepted.
A3.87 core.byte_size remains governed by A3-BS-01..07.
A3.88 Transport may validate carrier and lexical shape, but PrimitiveType/domain code remains authority for semantic parsing, canonicalization and constraints.
```

---

## 10. `core.byte_size` public wire contract

Accepted input:

```text
non-negative JSON integer exact bytes
OR
strict SI/IEC quantity string
```

Suffix case-sensitive:

```text
SI:  B, kB, MB, GB, TB, PB, EB
IEC: KiB, MiB, GiB, TiB, PiB, EiB
```

Adjacent o one-ASCII-space separator. No aliases/case folding. Quantity exact decimal ordinary notation, non-negative, no exponent/leading plus.

Exact conversion deve produrre integer bytes; nessuna floating-point approximation è authority.

Canonical API output/persistence = non-negative JSON integer exact bytes; caller unit non preservata.

```text
A3-BS-01 integer exact bytes OR strict SI/IEC quantity string accepted.
A3-BS-02 SI/IEC suffixes are case-sensitive and distinct.
A3-BS-03 adjacent or one-ASCII-space forms accepted; no aliases/case folding.
A3-BS-04 exact decimal ordinary notation; no exponent/leading plus.
A3-BS-05 fractional input only when exact conversion yields integer bytes.
A3-BS-06 canonical API output and persistence are always exact integer bytes.
A3-BS-07 one primitive parser/canonicalizer reused across all byte_size input positions.
```

---

## 11. API-03.9 — canonical read DTO

La canonical read authority è:

```text
api-read-contract.md
```

Principi registrati qui:

```text
single-resource/projection response
    -> no generic data envelope

nullable / zero-one state
    -> explicit null only when semantically genuine

empty collection/map
    -> [] / {}

DataType
    -> separate lineage and exact-version DTO

ObjectTemplate
    -> separate lineage, exact local snapshot and effective-schema DTO

Object GET
    -> intrinsic current state only

ownership
    -> semantic SlotSemanticKey projection, not persistence-row resource

Object.owner
    -> existing detached Object => HTTP 200 + null

RelationshipDefinition GET
    -> complete aggregate

Relationship GET
    -> deduplicated factual semantic views

Object relationships
    -> ObjectRelationshipView semantic projection

lifecycle
    -> discriminated event-family union
```

Effective-schema members expose `declaring_template_id`. Lifecycle intrinsic `before/after` reuse canonical Object snapshot; `CREATED.before` and `DELETED.after` use genuine `null` historical-state absence.

```text
A3.89 Single-resource/projection responses have no generic data envelope.
A3.90 Canonical read DTOs expose explicit null only for genuine nullable/zero-one state; empty collections/maps use []/{} and are not null.
A3.91 DataType lineage and exact-version reads remain separate DTOs; lineage does not inline its version collection.
A3.92 ObjectTemplate lineage, exact-version local snapshot and effective-schema projection are three separate DTOs.
A3.93 Effective-schema members include declaring_template_id and are returned in canonical effective ordering; request-array ordering remains unrelated.
A3.94 Relationship capability items expose resolution_id, relationship_definition_id, name, from_template_id and to_template_id.
A3.95 Object GET exposes only intrinsic current state: id/canonical_name/template exact pin/canonical properties.
A3.96 Ownership reads are semantic projections and expose SlotSemanticKey data; they never expose object_components as a CRUD/resource representation.
A3.97 GET Object.owner returns JSON null for an existing detached Object; Object-not-found remains a distinct failure.
A3.98 RelationshipDefinition GET always returns the complete Definition + Resolution aggregate.
A3.99 Relationship GET returns a factual aggregate with deduplicated semantic views, never raw RuntimeRelationshipResolution rows.
A3.100 Object-relative Relationship read returns self-contained ObjectRelationshipView items and performs semantic deduplication.
A3.101 Lifecycle read DTO is a discriminated union by event kind/family, not one wide nullable persistence-shaped record.
A3.102 Intrinsic lifecycle before/after reuse canonical Object snapshot shape; null means historical state absence for CREATED/DELETED.
A3.103 Collection route envelopes, list-item summary/full policy, pagination and filters are defined separately by API-03.10 in api-list-contract.md.
```

---

## 12. API-03.10 — collection/list contract

La collection authority è:

```text
api-list-contract.md
```

Registry summary:

```text
envelope
    -> {items:[...], next_cursor:string|null}
    -> no data/page/total_count/has_more wrapper fields

pagination
    -> opaque keyset cursor only
    -> no offset/page-number
    -> limit omitted => 100; valid 1..500

cursor
    -> route/order/filter specific
    -> not domain identity / DB offset / snapshot / CDC token
    -> changing filters invalidates cursor; limit may change

consistency
    -> each page independently snapshot-consistent
    -> no cross-request repeatable membership promise

sorting
    -> one fixed canonical order per route
    -> no generic sort/order surface

list item policy
    -> DTV summary omits constraints
    -> OTV summary omits declarations
    -> Object summary omits properties
    -> bounded lineage/Definition aggregates may reuse full DTO
    -> nested semantic projections reuse API-03.9 item shape
    -> lifecycle uses full event DTO

filters
    -> explicit route-specific exact filters only
    -> no generic query DSL / fuzzy search
```

Canonical route ordering:

```text
DataType/ObjectTemplate lineage -> (namespace,name) ASC
nested versions                 -> version ASC
Objects                         -> id ASC
RelationshipDefinitions         -> id ASC
relationship capabilities       -> resolution_id ASC
Object components               -> child_object_id ASC
ObjectRelationshipView          -> (relationship_id,destination_object_id,name) ASC
lifecycle                       -> (occurred_at,id) DESC
```

Object list exact filters:

```text
template_id
template_version only with template_id
canonical_name
```

Object-specific lifecycle route means events involving the Object:

```text
object_id = X OR destination_object_id = X
```

Lifecycle first-class filters:

```text
kind
object_id
destination_object_id
relationship_id
relationship_definition_id
relationship_name
occurred_from
occurred_to
```

API-03.10 creates normative PERSIST-15 read-path indices:

```text
objects(canonical_name,id)
object_lifecycle_events(kind,occurred_at,id)
object_lifecycle_events(relationship_name,occurred_at,id)
    WHERE relationship_name IS NOT NULL
```

```text
A3.104 Every paginated collection uses {items:[...], next_cursor:string|null}. No generic data wrapper, total_count, page count or has_more field.
A3.105 Pagination uses opaque keyset cursors only. M1 exposes no offset/page-number pagination.
A3.106 limit is optional with default 100 and allowed range 1..500.
A3.107 A cursor is route/query-filter/order specific and is not a domain identity, DB offset, snapshot token or change-feed token. Its internal encoding is not public contract.
A3.108 Each page is independently snapshot-consistent. Pagination across requests does not promise repeatable dataset membership under concurrent mutation.
A3.109 M1 collection ordering is fixed per route; no generic sort/order query surface is exposed.
A3.110 Default canonical orders are: DataType/ObjectTemplate lineages -> namespace,name ASC; nested versions -> version ASC; Objects -> id ASC; RelationshipDefinitions -> id ASC; capabilities -> resolution_id ASC; components -> child_object_id ASC; ObjectRelationshipView -> relationship_id,destination_object_id,name ASC; lifecycle -> occurred_at,id DESC.
A3.111 Collection routes use summary DTOs when the exact resource can carry unbounded/large state: DTV list omits constraints; OTV list omits declarations; Object list omits properties. Small/bounded lineage and Definition aggregates may reuse full read DTOs.
A3.112 Nested capability/components/ObjectRelationshipView collections use their complete API-03.9 projection item shape.
A3.113 Lifecycle collection items are complete API-03.9 event DTOs because M1 does not introduce a separate lifecycle-event detail route.
A3.114 /api/v1/core/objects/{object_id}/lifecycle-events means events involving the Object: object_id == X OR destination_object_id == X.
A3.115 M1 filters are explicit route-specific exact filters; no generic query DSL or fuzzy-search semantics are implied.
A3.116 Object list supports template_id, dependent template_version and exact canonical_name filters. template_version without template_id is invalid.
A3.117 Lifecycle lists support kind, object/destination Object IDs, relationship/definition IDs, exact relationship_name and occurred_from/to.
A3.118 Cursor continuation is bound to the active filter set. Changing filters while reusing a cursor is invalid; limit may change.
A3.119 API-03.10 establishes new M1 read-path index requirements: objects(canonical_name,id), lifecycle(kind,occurred_at,id), and partial lifecycle(relationship_name,occurred_at,id) WHERE relationship_name IS NOT NULL.
A3.120 These index additions are normative PERSIST-15 requirements and must be kept aligned with the persistence model.
```

---

## 13. API-03.11A — failure classes and public error shape

The canonical error authority is:

```text
api-error-contract.md
```

Registry summary:

```text
INVALID_REQUEST       -> 400
NOT_FOUND             -> 404
SEMANTIC_VALIDATION   -> 422
STATE_CONFLICT        -> 409
INTERNAL_FAILURE      -> 500
```

Important boundaries:

```text
404
    -> missing request-URI/path target identity only

missing referenced command operand
    -> normally 422 semantic validation

malformed expected_revision
    -> 400

well-formed stale expected_revision
    -> 409

idempotent no-op / factual convergence
    -> success, never conflict merely because no row changed
```

Canonical public error body:

```json
{
  "code": "stale_revision",
  "message": "The draft revision does not match the expected revision.",
  "details": {}
}
```

`code` is stable machine-readable snake_case; clients do not branch on `message`; `details` is always a JSON object. HTTP status derives from failure class; concrete code identifies the subtype. Internal failures never expose SQL/stack/constraint internals.

```text
A3.121 Application/domain failures remain transport-neutral; HTTP mapping occurs only at the transport adapter.
A3.122 M1 public failure classes map as INVALID_REQUEST=400, NOT_FOUND=404, SEMANTIC_VALIDATION=422, STATE_CONFLICT=409, INTERNAL_FAILURE=500.
A3.123 404 is reserved for missing request-URI/path target identity; missing command operands are semantic validation unless a more specific state rule applies.
A3.124 400 covers transport/wire/query/path malformed input that does not require mutable persisted-state interpretation.
A3.125 422 covers syntactically valid but semantically invalid candidate/operand requests.
A3.126 409 covers meaningful commands blocked by current mutable state, lifecycle/dependency policy, conflicting facts or stale application generation.
A3.127 Malformed expected_revision is 400; well-formed stale expected_revision is 409; no 412/ETag reinterpretation.
A3.128 Domain-defined idempotent no-op/convergence is success and is never converted into conflict merely because no persistence row changed.
A3.129 500 represents unexpected internal/invariant/integrity failure and never exposes SQL/stack/constraint internals publicly.
A3.130 Canonical error body is flat {code,message,details}; code is stable machine-readable snake_case, message is human-readable only, details is always a JSON object.
A3.131 HTTP status derives from failure class; concrete code identifies the specific failure subtype.
```

---

## 14. API-03 remaining work

Still open and to be revalidated/ratified point-by-point:

```text
API-03.11B complete concrete M1 error-code catalog + details schemas
API-03.11B success HTTP status/body mapping
```
