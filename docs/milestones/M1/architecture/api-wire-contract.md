# M1 — API Wire Contract

**Status:** DRAFT — API-03 in progress. API-03.1 strict caller-intent rules, API-03.2 `expected_revision` placement, API-03.3 exact/implicit selector semantics e il `core.byte_size` public wire contract sono ratificati. Le restanti DTO/read/failure decisioni non sono ancora congelate.

## 1. Scopo

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

### 2.1 Naming e DTO strictness

- JSON object keys: `snake_case`;
- semantic command path segments: `kebab-case`;
- unknown command fields: rejected;
- generic scalar coercion: rejected.

Non sono genericamente equivalenti:

```text
"3"  vs 3
true vs 1
3    vs "3"
```

Una primitive può definire esplicitamente più carrier ammessi; tale union è parte del primitive wire contract, non una coercion del framework.

### 2.2 Omission vs intent esplicito

Normative rule:

> un default o una implicit resolution colma soltanto assenza di caller intent quando la specifica command assegna una semantica all'omissione. Un valore esplicito deve essere accettato oppure rifiutato; non viene mai corretto, sostituito o mascherato da un default.

```text
field omitted
    -> may trigger command-specific default/implicit semantics
       only when explicitly defined

explicit valid value
    -> use according to command contract

explicit invalid value
    -> failure
    -> no fallback/default replacement
```

JSON `null` è input esplicito, non omission. È valido soltanto quando `null` stesso è uno state/value semanticamente ammesso per quel field.

### 2.3 Object CREATE `canonical_name`

```text
canonical_name omitted
    -> canonical_name = str(Object.id)

canonical_name explicitly supplied
    -> valid non-empty string length 1..255

canonical_name = null / "" / invalid
    -> failure
```

Il fallback UUID colma esclusivamente assenza di intent.

### 2.4 Implicit version resolution

Quando una command supporta implicit exact-version binding, l'intent implicito viene espresso tramite omissione del relativo version field. Explicit `null` è invalido.

### 2.5 Validation boundary

Il transport valida shape/syntax indipendenti da persisted mutable state, inclusi JSON carrier, required/forbidden fields, unknown fields, UUID lexical shape, positive integer lexical shape, discriminator e cardinalità statiche.

Application/domain restano authority per existence, lifecycle, admission, effective schema, primitive semantic parsing/canonicalization, constraints, lineage compatibility, conflict predicate e ownership cycle.

### 2.6 Decisioni API-03.1

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

### 3.1 Scope

`expected_revision` è il generation precondition esclusivamente di:

```text
DataTypeVersion.REVISE
DataTypeVersion.PUBLISH
DataTypeVersion.DELETE_DRAFT
ObjectTemplateVersion.REVISE
ObjectTemplateVersion.PUBLISH
ObjectTemplateVersion.DELETE_DRAFT
```

Non è una generic resource revision.

### 3.2 Public representation

Tutte le sei route usano uniformemente:

```text
?expected_revision=<positive-decimal-integer>
```

Esempi:

```text
POST   /api/v1/core/datatypes/{datatype_id}/versions/{version}/revise?expected_revision=7
POST   /api/v1/core/datatypes/{datatype_id}/versions/{version}/publish?expected_revision=7
DELETE /api/v1/core/datatypes/{datatype_id}/versions/{version}?expected_revision=7

POST   /api/v1/core/object-templates/{template_id}/versions/{version}/revise?expected_revision=7
POST   /api/v1/core/object-templates/{template_id}/versions/{version}/publish?expected_revision=7
DELETE /api/v1/core/object-templates/{template_id}/versions/{version}?expected_revision=7
```

```text
path
    -> exact mutation target
query expected_revision
    -> DRAFT generation precondition
body, if any
    -> semantic candidate / command operands
```

REVISE body non contiene il token. PUBLISH e DELETE_DRAFT non introducono body artificiale.

M1 non usa `ETag`, `If-Match` o custom revision header per questa semantica.

Missing/empty/zero/negative/malformed `expected_revision` è transport-input failure; positive integer ben formato ma stale è application generation-conflict failure.

### 3.3 Decisioni API-03.2

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

### 4.1 General rule

M1 non introduce un generic `VersionSelector` object e non usa special string token come:

```text
"default"
"latest"
"highest"
```

Stable lineage identity ed exact version sono type-specific sibling fields:

```text
template_id / template_version
parent_template_id / parent_version
datatype_id / datatype_version
```

Un version field omesso significa implicit default selection **soltanto** quando la owning domain command possiede già quella modalità di binding.

### 4.2 Object CREATE

Exact:

```json
{
  "template_id": "<uuid>",
  "template_version": 7
}
```

Implicit:

```json
{
  "template_id": "<uuid>"
}
```

Semantica:

```text
template_version omitted
    -> resolve ObjectTemplate.default_version

template_version explicit
    -> exact OTV selection

template_version = null
    -> invalid
```

Se il default è NULL, CREATE fallisce. Non esiste fallback a latest/highest PUBLISHED.

### 4.3 ObjectTemplate CREATE parent selector

Root:

```json
{
  "namespace": "network",
  "name": "device"
}
```

Exact parent:

```json
{
  "namespace": "network",
  "name": "router",
  "parent_template_id": "<uuid>",
  "parent_version": 4
}
```

Implicit parent version:

```json
{
  "namespace": "network",
  "name": "router",
  "parent_template_id": "<uuid>"
}
```

Rules:

```text
parent_template_id omitted
    -> root
    -> parent_version must be omitted

parent_template_id present + parent_version omitted
    -> resolve parent.default_version

both present
    -> exact parent pin

explicit null
    -> invalid
```

### 4.4 ObjectTemplate REVISE parent selector

`parent_template_id` è stable lineage state e non appartiene al REVISE body.

Per non-root lineage:

```text
parent_version explicit
    -> preserve/select that exact parent pin

parent_version omitted
    -> intentional rebind via current parent default
```

Poiché REVISE è complete candidate replacement, omission non significa “leave unchanged”. Se si vuole preservare l'historical exact parent pin, `parent_version` va reinviata esplicitamente.

Per root lineage, `parent_version` è forbidden.

### 4.5 ObjectTemplate property DTV selector

Exact property binding:

```json
{
  "name": "memory",
  "datatype_id": "<uuid>",
  "datatype_version": 3,
  "value_mode": "SCALAR",
  "required": true,
  "position": 10,
  "migration_default": "1 GiB"
}
```

Implicit DTV default binding:

```json
{
  "name": "memory",
  "datatype_id": "<uuid>",
  "value_mode": "SCALAR",
  "required": true,
  "position": 10,
  "migration_default": "1 GiB"
}
```

```text
datatype_version omitted
    -> intentional new/rebound resolution via DataType.default_version

datatype_version explicit
    -> exact DTV pin
```

In un complete OT REVISE, preservare un historical DTV pin richiede quindi reinviare `datatype_version` esplicitamente. Omission non significa “keep current”.

### 4.6 Exact-only selectors

Queste operation richiedono sempre una exact version esplicita:

```text
DT.CREATE_NEXT.source_version
OT.CREATE_NEXT.source_version
DT.SET_DEFAULT.version
OT.SET_DEFAULT.version
Object.SCHEMA_CHANGE.target_version
```

Omission/null è invalida e non risolve alcun default.

### 4.7 Decisioni API-03.3

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

## 5. `core.byte_size` public wire contract

### 5.1 Accepted input

Ovunque il public API accetti un semantic `core.byte_size` value — Object property, DataType constraint/enum, ObjectTemplate `migration_default` — sono ammessi due carrier.

Exact bytes:

```json
1024
```

oppure quantity string con unità SI/IEC esplicita:

```json
"1 KiB"
"1MiB"
"1.5 MB"
"0.1 kB"
```

Canonical suffix vocabulary case-sensitive:

```text
SI:  B, kB, MB, GB, TB, PB, EB
IEC: KiB, MiB, GiB, TiB, PiB, EiB
```

Sono ammesse forma adiacente o con un solo ASCII space. Alias/case folding non sono ammessi.

La quantità usa exact decimal ordinary notation: non-negative, no exponent, no leading `+`.

### 5.2 Exact conversion

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

Nessuna floating-point approximation è authority.

### 5.3 Canonical output/persistence

Il canonical API read/response e persistence state sono sempre un non-negative JSON integer contenente exact bytes. La lexical unit del caller non viene preservata.

### 5.4 Decisioni byte-size

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

## 6. API-03 remaining work

Still open and to be revalidated/ratified point-by-point:

```text
DataType CREATE/REVISE command DTOs
ObjectTemplate complete local candidate CREATE/REVISE DTOs beyond selector semantics
Object CREATE/DATA_CHANGE/SCHEMA_CHANGE/ownership DTOs beyond selector/canonical_name semantics
RelationshipDefinition discriminated CREATE/RENAME DTOs
Relationship CREATE DTO
remaining primitive public-input lexical forms
canonical read DTO conventions
pagination/filter/list envelopes
success/failure HTTP mapping
```
