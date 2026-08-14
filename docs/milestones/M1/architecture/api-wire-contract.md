# M1 — API Wire Contract

**Status:** DRAFT — API-03 in progress. API-03.1 strict caller-intent rules, API-03.2 `expected_revision` placement, API-03.3 exact/implicit selectors, API-03.4 DataType command DTO, API-03.5 ObjectTemplate command DTO, API-03.6 Object command DTO, API-03.7 Relationship command DTO e il `core.byte_size` public wire contract sono ratificati. Restano primitive lexical forms, read/list e failure mapping.

## 1. Scopo e boundary

Questo documento definisce la public HTTP/JSON representation M1 quando il wire contract deve rendere esplicite semantiche già consolidate nel domain/application layer.

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

---

## 2. API-03.1 — strict wire shape e caller intent

### 2.1 Regole

- JSON object keys: `snake_case`;
- semantic command path segments: `kebab-case`;
- unknown command fields: rejected;
- generic scalar coercion: rejected.

Un default o una implicit resolution colma soltanto assenza di caller intent quando la specifica command assegna una semantica all'omissione. Un valore esplicito deve essere accettato oppure rifiutato; non viene mai corretto, sostituito o mascherato da un default.

JSON `null` è input esplicito, non omission. È valido soltanto quando `null` stesso è uno state/value semanticamente ammesso per quel field.

Object CREATE:

```text
canonical_name omitted
    -> canonical_name = str(Object.id)

canonical_name explicit valid string 1..255
    -> use exactly that value

canonical_name = null / "" / invalid
    -> failure
```

Quando una command supporta implicit exact-version binding, l'intent implicito viene espresso tramite omissione del relativo version field. Explicit `null` è invalido.

Il transport valida shape/syntax indipendenti da persisted mutable state; application/domain restano authority per existence, lifecycle, admission, effective schema, primitive semantic parsing/canonicalization, constraints, lineage compatibility, conflict predicate e ownership cycle.

### 2.2 Decisioni

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

`expected_revision` è il generation precondition esclusivamente di DTV/OTV `REVISE`, `PUBLISH` e `DELETE_DRAFT`.

Tutte le sei route usano:

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

REVISE body non contiene il token. PUBLISH e DELETE_DRAFT non introducono body artificiale. M1 non usa `ETag`, `If-Match` o custom revision header per questa semantica.

Missing/empty/zero/negative/malformed `expected_revision` è transport-input failure; positive integer ben formato ma stale è application generation-conflict failure.

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

M1 non introduce generic `VersionSelector` e non usa token `default`, `latest` o `highest`.

Stable lineage identity ed exact version sono type-specific sibling fields:

```text
template_id / template_version
parent_template_id / parent_version
datatype_id / datatype_version
```

Un version field omesso significa implicit default selection soltanto quando la owning domain command possiede già quella modalità di binding.

### Object CREATE

```text
template_version omitted -> resolve ObjectTemplate.default_version
template_version explicit -> exact OTV selection
template_version = null -> invalid
```

Default NULL => failure; nessun latest/highest fallback.

### ObjectTemplate CREATE parent

```text
parent_template_id omitted
    -> root; parent_version must be omitted

parent_template_id present + parent_version omitted
    -> resolve parent.default_version

both present
    -> exact parent pin

explicit null
    -> invalid
```

### ObjectTemplate REVISE parent

`parent_template_id` non appartiene al body.

```text
non-root parent_version explicit
    -> preserve/select exact parent pin

non-root parent_version omitted
    -> intentional rebind via current parent default

root parent_version
    -> forbidden
```

### Property DTV selector

```text
datatype_version omitted
    -> intentional new/rebound resolution via DataType.default_version

datatype_version explicit
    -> exact DTV pin
```

In complete OT REVISE, preservare historical DTV pin richiede reinviare `datatype_version`.

Exact-only selectors:

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

```json
{
  "namespace": "network.routing",
  "name": "asn",
  "description": "BGP autonomous system number",
  "base_type": "core.integer",
  "constraints": {
    "minimum": 1,
    "maximum": 4294967295
  }
}
```

Required: `namespace`, `name`, `base_type`.

```text
description omitted -> initial null
description = null -> valid nullable state
constraints omitted -> creation default {}
constraints = {} -> explicit zero-constraint candidate
constraints = null -> invalid
```

Caller non fornisce `id`, `version`, `revision`, `status`, `default_version`.

Constraint key matrix:

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

```json
{
  "constraints": {
    "minimum": 1,
    "maximum": 65535
  }
}
```

`constraints` required; `{}` significa zero constraints. Omission non significa keep-current.

Forbidden nel body: lineage metadata, `description`, `base_type`, lifecycle/default state, version/revision, `expected_revision`.

Altre command:

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

### 6.1 CREATE

Canonical shape:

```json
{
  "namespace": "network",
  "name": "router",
  "description": "Network router",
  "abstract": false,
  "parent_template_id": "<uuid>",
  "parent_version": 3,
  "properties": [],
  "components": []
}
```

Required:

```text
namespace
name
abstract
```

`abstract` è structural lineage state immutabile e non possiede un public omitted->false default.

Creation omission semantics:

```text
description omitted
    -> null

properties omitted
    -> []

components omitted
    -> []

properties/components = null
    -> invalid
```

Parent selector segue API-03.3.

### 6.2 Property declaration

Canonical shape:

```json
{
  "name": "memory",
  "position": 20,
  "datatype_id": "<uuid>",
  "datatype_version": 4,
  "value_mode": "SCALAR",
  "required": true,
  "migration_default": "1 GiB"
}
```

Always required:

```text
name
position
datatype_id
value_mode
required
```

`datatype_version` può essere omessa soltanto per intentional implicit DTV default binding/rebinding.

`migration_default` è conditional:

```text
required=false
    -> migration_default MUST be absent

required=true + SCALAR
    -> migration_default REQUIRED, one concrete value

required=true + LIST
    -> migration_default REQUIRED, non-empty list
```

`migration_default:null` è invalido.

### 6.3 Component declaration

Canonical shape:

```json
{
  "name": "interfaces",
  "position": 10,
  "target_template_id": "<uuid>"
}
```

Esattamente questi tre field, tutti required. Nessun `target_template_version`, `required`, `min_count` o `max_count` M1.

### 6.4 Ordering authority

`position` è declaration state esplicito e non viene inferito dall'array index.

L'ordine di `properties[]` e `components[]` nella request non è semantic authority. Local ordering è determinato da `position`; una canonical response può quindi ordinare le declaration per `position`.

### 6.5 REVISE

Route:

```text
POST /api/v1/core/object-templates/{template_id}/versions/{version}/revise?expected_revision=N
```

Non-root candidate:

```json
{
  "parent_version": 5,
  "properties": [],
  "components": []
}
```

Root candidate:

```json
{
  "properties": [],
  "components": []
}
```

`properties` e `components` sono sempre required, anche quando `[]`, perché REVISE è complete local-candidate replacement. Omission non significa keep-current.

`parent_version` segue API-03.3: non-root omission intentionally rebinds via current parent default; root lo vieta.

Forbidden nel REVISE body:

```text
namespace
name
description
abstract
parent_template_id
template_id
version
revision
status
default_version
expected_revision
```

Nuove e historical declaration usano la stessa transport shape; historical evolution legality resta domain validation e non produce DTO separati.

### 6.6 Other ObjectTemplate commands

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

### 6.7 Decisioni API-03.5

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

### 7.1 CREATE

Canonical shape:

```json
{
  "template_id": "<uuid>",
  "template_version": 4,
  "canonical_name": "router-01",
  "properties": {
    "hostname": "router-01",
    "memory": "4 GiB"
  }
}
```

Required:

```text
template_id
```

Optional con omission semantics già ratificate:

```text
template_version omitted
    -> resolve ObjectTemplate.default_version

canonical_name omitted
    -> str(Object.id)

properties omitted
    -> creation default {}
```

`properties` omitted e `properties={}` significano zero runtime property values forniti dal caller. Non attivano `migration_default` e non soddisfano property required mancanti.

Explicit `null` per `template_version`, `canonical_name` o `properties` è invalido.

`properties` è un JSON object keyed by effective property name:

```text
SCALAR -> one PrimitiveType input value
LIST   -> JSON array of PrimitiveType input values
```

JSON `null` non è runtime property value. Optional LIST `[]` è ammesso e canonicalizza a property key assente; required LIST `[]` fallisce.

### 7.2 RENAME

```json
{
  "canonical_name": "router-02"
}
```

Esattamente un required string field, valido `1..255`; `null`/empty/invalid falliscono.

### 7.3 DATA_CHANGE

Canonical shape:

```json
{
  "operations": [
    {
      "op": "SET",
      "property": "hostname",
      "value": "router-02"
    },
    {
      "op": "REMOVE",
      "property": "description"
    }
  ]
}
```

Discriminator vocabulary:

```text
SET
REMOVE
```

`SET` richiede esattamente `op`, `property`, `value`.

`REMOVE` richiede esattamente `op`, `property` e vieta `value`.

`operations` è required e non-empty. Una stessa property può apparire al massimo una volta nella request; l'ordine dell'array non ha significato semantico. La command rappresenta un set atomico di per-property change, non uno script sequenziale.

Un payload non-empty può comunque convergere allo stesso semantic state corrente e produrre valid semantic no-op senza lifecycle event.

Per optional LIST:

```text
SET []
    -> valid
    -> canonical absence
```

`SET null` è invalido.

### 7.4 SCHEMA_CHANGE

```json
{
  "target_version": 8
}
```

Esattamente questo mandatory exact selector. Non esistono body field per `template_id`, remediation, target property override, transformation, detach o migration script.

### 7.5 ATTACH / DETACH

Entrambe le route usano la stessa strict body shape:

```json
{
  "slot_name": "interfaces",
  "child_object_id": "<uuid>"
}
```

`parent_object_id` resta il target nel path.

La shared wire shape non crea shared admission semantics:

```text
ATTACH
    -> current slot must exist
    -> child compatibility validated

DETACH
    -> removes only the exact runtime edge
    -> does not require current slot existence
    -> does not revalidate compatibility
```

La `SlotSemanticKey`/declaring lineage non è caller input e viene risolta dal kernel.

### 7.6 DELETE

Object DELETE non ha body e non espone `cascade`, `force`, `recursive`, implicit detach o subtree options.

### 7.7 Decisioni API-03.6

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

### 8.1 RelationshipDefinition CREATE

CREATE usa una strict union discriminata dal required boolean `symmetric`.

Non-symmetric:

```json
{
  "symmetric": false,
  "perspectives": [
    {
      "template_id": "<uuid-a>",
      "name": "is_hosted_by"
    },
    {
      "template_id": "<uuid-b>",
      "name": "hosts"
    }
  ]
}
```

`perspectives` contiene esattamente due elementi `{template_id,name}`. L'ordine non ha significato semantico e i due names devono essere distinti, anche con endpoint template uguali.

Symmetric:

```json
{
  "symmetric": true,
  "endpoint_template_ids": [
    "<uuid-a>",
    "<uuid-b>"
  ],
  "name": "connects_to"
}
```

`endpoint_template_ids` contiene esattamente due template lineage IDs, semanticamente unordered; gli ID possono essere uguali. Il caller fornisce un solo semantic name. Il kernel genera una Resolution per same-template oppure due reciprocal Resolution con lo stesso name per different-template.

Il caller non fornisce `RelationshipDefinition.id` né `RelationshipResolution.id` durante CREATE.

### 8.2 RelationshipDefinition RENAME

La route è:

```text
POST /api/v1/core/relationship-definitions/{relationship_definition_id}/rename
```

`symmetric` non viene reinviato nel body perché è stable aggregate state già identificato dal path.

Non-symmetric rename:

```json
{
  "resolutions": [
    {
      "resolution_id": "<uuid-r1>",
      "name": "hosted_by"
    },
    {
      "resolution_id": "<uuid-r2>",
      "name": "hosts"
    }
  ]
}
```

`resolutions` contiene esattamente due elementi, copre il complete current Resolution set, è unordered e vieta duplicate `resolution_id`.

Symmetric rename:

```json
{
  "name": "connected_to"
}
```

Un solo semantic name, indipendentemente dal fatto che il complete aggregate possieda fisicamente una oppure due Resolution rows.

Le due request shape sono strutturalmente disgiunte. Il transport può validarne la shape senza leggere persisted state; l'application/domain verifica che la shape scelta sia coerente con la current Definition symmetry e che, per non-symmetric, gli ID appartengano al complete child set della Definition. Shape/symmetry mismatch è semantic command failure.

### 8.3 RelationshipDefinition DELETE

```text
DELETE /api/v1/core/relationship-definitions/{relationship_definition_id}
```

Nessun body e nessuna option `force`, `cascade` o implicit factual-relationship cleanup.

### 8.4 Runtime Relationship CREATE

```json
{
  "resolution_id": "<uuid>",
  "from_object_id": "<uuid>",
  "to_object_id": "<uuid>"
}
```

Esattamente questi tre required field. Non sono caller input:

```text
relationship_id
relationship_definition_id
name
symmetric
from_template_id
to_template_id
```

`relationship_definition_id` deriva dalla selected Resolution. `Relationship.id` è kernel-generated quando nasce un nuovo factual relationship.

`from_object_id == to_object_id` non viene rifiutato strutturalmente: self-loop admission resta domain semantics.

La selected Resolution preserva la perspective assignment per non-symmetric Definition; symmetric Resolution/assignment equivalenti possono convergere sullo stesso factual Relationship secondo il runtime idempotency contract.

### 8.5 Runtime Relationship DELETE

```text
DELETE /api/v1/core/relationships/{relationship_id}
```

Nessun body. DELETE resta exact-ID based e non esiste semantic-tuple delete alternative; questo preserva anche la ratificata ABA safety.

### 8.6 Ordering e generated identity

Gli array che rappresentano semantic set unordered non acquisiscono orientation dall'ordine JSON:

```text
non-symmetric perspectives[]
symmetric endpoint_template_ids[]
non-symmetric rename resolutions[]
```

M1 continua a non introdurre `source`/`target` o `forward`/`reverse` field.

### 8.7 Decisioni API-03.7

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

## 9. `core.byte_size` public wire contract

Ovunque il public API accetti semantic `core.byte_size` — Object property, DataType constraint/enum, ObjectTemplate `migration_default` — sono ammessi:

```text
non-negative JSON integer exact bytes
OR
strict SI/IEC quantity string
```

Canonical suffix vocabulary case-sensitive:

```text
SI:  B, kB, MB, GB, TB, PB, EB
IEC: KiB, MiB, GiB, TiB, PiB, EiB
```

Sono ammesse forma adiacente o con un solo ASCII space. Alias/case folding non ammessi. Quantità in exact decimal ordinary notation: non-negative, no exponent, no leading `+`.

```text
parse exact decimal quantity
-> multiply by exact unit multiplier
-> require integer result >= 0 bytes
-> canonical integer byte count
```

Esempi:

```text
1 MB     -> 1,000,000
1 MiB    -> 1,048,576
1.5 KiB  -> 1,536
0.1 kB   -> 100
0.1 KiB  -> invalid (102.4 bytes)
```

Canonical API read/response e persistence state sono sempre non-negative JSON integer exact bytes. Caller lexical unit non preservata.

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

## 10. API-03 remaining work

Still open and to be revalidated/ratified point-by-point:

```text
remaining primitive public-input lexical forms
canonical read DTO conventions
pagination/filter/list envelopes
success/failure HTTP mapping
```
