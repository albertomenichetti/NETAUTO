# M1 — API Wire Contract

**Status:** DRAFT — API-03 in progress. API-03.1 strict caller-intent rules, API-03.2 `expected_revision` placement, API-03.3 exact/implicit selector semantics, API-03.4 DataType command DTO e il `core.byte_size` public wire contract sono ratificati. Le restanti DTO/read/failure decisioni non sono ancora congelate.

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

### 3.1 Scope e representation

`expected_revision` è il generation precondition esclusivamente di DTV/OTV `REVISE`, `PUBLISH` e `DELETE_DRAFT`.

Tutte le sei route usano uniformemente:

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

REVISE body non contiene il token. PUBLISH e DELETE_DRAFT non introducono body artificiale.

M1 non usa `ETag`, `If-Match` o custom revision header per questa semantica.

Missing/empty/zero/negative/malformed `expected_revision` è transport-input failure; positive integer ben formato ma stale è application generation-conflict failure.

### 3.2 Decisioni API-03.2

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

M1 non introduce un generic `VersionSelector` object e non usa special string token come `default`, `latest` o `highest`.

Stable lineage identity ed exact version sono type-specific sibling fields:

```text
template_id / template_version
parent_template_id / parent_version
datatype_id / datatype_version
```

Un version field omesso significa implicit default selection soltanto quando la owning domain command possiede già quella modalità di binding.

### 4.2 Object CREATE

```text
template_version omitted
    -> resolve ObjectTemplate.default_version

template_version explicit
    -> exact OTV selection

template_version = null
    -> invalid
```

Se il default è NULL, CREATE fallisce. Nessun fallback a latest/highest PUBLISHED.

### 4.3 ObjectTemplate CREATE parent selector

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

### 4.4 ObjectTemplate REVISE parent selector

`parent_template_id` non appartiene al REVISE body.

Per non-root lineage:

```text
parent_version explicit
    -> preserve/select exact parent pin

parent_version omitted
    -> intentional rebind via current parent default
```

Per root lineage, `parent_version` è forbidden.

### 4.5 ObjectTemplate property DTV selector

```text
datatype_version omitted
    -> intentional new/rebound resolution via DataType.default_version

datatype_version explicit
    -> exact DTV pin
```

In un complete OT REVISE, preservare un historical DTV pin richiede reinviare `datatype_version` esplicitamente.

### 4.6 Exact-only selectors

Sempre exact e required:

```text
DT.CREATE_NEXT.source_version
OT.CREATE_NEXT.source_version
DT.SET_DEFAULT.version
OT.SET_DEFAULT.version
Object.SCHEMA_CHANGE.target_version
```

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

## 5. API-03.4 — DataType command DTO

### 5.1 CREATE

```http
POST /api/v1/core/datatypes
```

Canonical request shape:

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

Required:

```text
namespace
name
base_type
```

Optional:

```text
description
constraints
```

Creation omission semantics:

```text
description omitted
    -> initial description = null

description = null
    -> valid explicit nullable state

constraints omitted
    -> creation default {}

constraints = {}
    -> explicit zero-constraint candidate

constraints = null
    -> invalid
```

Caller non può fornire `id`, `version`, `revision`, `status` o `default_version`.

CREATE produce atomicamente stable lineage + v1 DRAFT revision 1.

### 5.2 Constraint object shape

`constraints` è sempre un JSON object. Le key ammesse dipendono dal fixed M1 PrimitiveType constraint matrix:

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

Unknown/unsupported constraint key è invalid input.

Constraint values riusano lo stesso PrimitiveType public-input + canonicalization contract usato negli altri input position.

### 5.3 REVISE

```http
POST /api/v1/core/datatypes/{datatype_id}/versions/{version}/revise?expected_revision=N
```

Body canonicale:

```json
{
  "constraints": {
    "minimum": 1,
    "maximum": 65535
  }
}
```

`constraints` è required perché REVISE è complete mutable-candidate replacement.

```text
constraints = {}
    -> deliberate zero-constraint candidate

constraints omitted
    -> invalid; never means keep-current
```

REVISE body non può contenere:

```text
namespace
name
description
base_type
version
revision
status
default_version
expected_revision
```

### 5.4 Other DataType commands

```text
CREATE_NEXT
    body = { "source_version": <positive exact version> }

PUBLISH
    no body; required expected_revision query

SET_DEFAULT
    body = { "version": <positive exact PUBLISHED version> }

CLEAR_DEFAULT
    no body

DEPRECATE
    no body

DELETE_DRAFT
    no body; required expected_revision query

DELETE_LINEAGE
    no body

SET_DESCRIPTION
    body = { "description": <string|null> }
```

`description:null` è valido perché `description` è nullable state, non perché null significhi generic clear/default.

### 5.5 Candidate canonicalization

La request non viene persistita verbatim:

```text
wire constraint input
-> primitive parse
-> primitive canonicalization
-> constraint structural/contradiction validation
-> enum canonicalization + duplicate detection
-> canonical constraints object
-> persistence
```

### 5.6 Decisioni API-03.4

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

## 6. `core.byte_size` public wire contract

### 6.1 Accepted input

Ovunque il public API accetti un semantic `core.byte_size` value — Object property, DataType constraint/enum, ObjectTemplate `migration_default` — sono ammessi:

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

Sono ammesse forma adiacente o con un solo ASCII space. Alias/case folding non sono ammessi.

La quantità usa exact decimal ordinary notation: non-negative, no exponent, no leading `+`.

### 6.2 Exact conversion

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

### 6.3 Canonical output/persistence

Il canonical API read/response e persistence state sono sempre un non-negative JSON integer contenente exact bytes. La lexical unit del caller non viene preservata.

### 6.4 Decisioni byte-size

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

## 7. API-03 remaining work

Still open and to be revalidated/ratified point-by-point:

```text
ObjectTemplate complete local candidate CREATE/REVISE DTOs beyond selector semantics
Object CREATE/DATA_CHANGE/SCHEMA_CHANGE/ownership DTOs beyond selector/canonical_name semantics
RelationshipDefinition discriminated CREATE/RENAME DTOs
Relationship CREATE DTO
remaining primitive public-input lexical forms
canonical read DTO conventions
pagination/filter/list envelopes
success/failure HTTP mapping
```
