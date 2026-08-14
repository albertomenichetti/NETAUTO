# M1 — API Wire Contract

**Status:** DRAFT — API-03 in progress. API-03.1 general wire strictness/intent semantics e il `core.byte_size` request/canonical wire contract sono ratificati; le restanti DTO/wire decisioni non sono ancora congelate.

## 1. Scopo

Questo documento raccoglie le decisioni API-03 relative alla rappresentazione HTTP/JSON quando il public accepted input differisce dal canonical domain/persistence representation.

La catena normativa resta:

```text
domain/application command semantics
-> accepted public wire input
-> transport shape validation
-> domain parse / validation / canonicalization
-> canonical domain value/state
-> canonical persistence / read output
```

La wire ergonomics non può restringere o ampliare implicitamente il domain contract già ratificato.

Prima di aggiungere una nuova wire decision si applica il pre-flight definito in `docs/general/linee_guida_progetto.md` e in `architecture/README.md`: vengono riletti i domain/persistence/API contract da cui la representation dipende.

---

## 2. API-03.1 — general wire strictness and caller intent

### 2.1 Naming

JSON object keys usano `snake_case`.

I semantic command route segment restano `kebab-case` come definito da API-02.

### 2.2 Strict DTO shape

I command DTO M1 rifiutano unknown fields.

Il transport non esegue generic scalar coercion fra carrier semanticamente distinti. In particolare non sono automaticamente equivalenti:

```text
"3"  vs 3
true vs 1
3    vs "3"
```

Una primitive può definire esplicitamente più carrier accettati — come `core.byte_size` integer-or-quantity-string — ma quella union è parte del primitive wire contract e non una coercion generale del framework.

### 2.3 Omission vs explicit intent

Omission e input esplicito sono distinti.

Normative rule:

> un default o una implicit resolution può colmare soltanto **assenza di intent** quando la specifica command assegna una semantica all'omissione. Un valore esplicitamente fornito esprime caller intent e deve essere accettato oppure rifiutato; non viene mai corretto, sostituito o mascherato da un default.

Quindi:

```text
field omitted
    -> may trigger command-specific default/implicit semantics
       only when explicitly defined

explicit valid value
    -> use according to command contract

explicit invalid value
    -> validation/domain failure
    -> no fallback/default replacement
```

### 2.4 JSON null

JSON `null` è un input esplicito, non omission.

`null` è valido soltanto quando **null stesso** è un valore/state semanticamente ammesso per quel field. Non è un generic alias per:

```text
omitted
default
implicit resolution
clear
remove
```

Esempio valido:

```json
{"description": null}
```

perché `description` è nullable state.

Esempi invalidi:

```json
{"template_version": null}
{"parent": null}
{"migration_default": null}
```

quando il relativo contract richiede omission oppure un concrete value.

### 2.5 Object CREATE `canonical_name`

Il domain contract è esplicitamente:

```text
canonical_name omitted
    -> canonical_name = str(Object.id)

canonical_name explicitly supplied
    -> must be valid non-empty string length 1..255

canonical_name = null
    -> invalid explicit input

canonical_name = ""
    -> invalid explicit input
```

Il UUID-string fallback colma assenza di caller intent; non passa davanti a un intent esplicito invalido.

Un eventuale `None` tecnico usato internamente dal codice come sentinel di omission non deve diventare JSON-null semantics.

### 2.6 Implicit exact-version resolution

Quando una command supporta implicit default resolution di una exact version, l'intent implicito si esprime esclusivamente tramite **omissione del version field**.

```text
version omitted
    -> command-specific implicit default resolution

version = null
    -> invalid explicit input
```

Lo stesso principio si applica a ObjectTemplate parent-version selection e DataType/property exact-version binding quando il relativo command contract permette implicit resolution.

### 2.7 Canonical response independence

Accepted public input lexical forms e canonical response/persistence representation possono differire soltanto quando il domain codec definisce una canonicalizzazione deterministica.

Le response espongono sempre canonical domain state; non preservano automaticamente lexical choices del caller.

### 2.8 Validation boundary

Il transport è responsabile di shape/syntax che non dipendono da persisted mutable state, per esempio:

```text
JSON carrier type
required/forbidden request field
unknown field
UUID lexical shape
positive integer shape
closed discriminator vocabulary
statically known array cardinality
```

Application/domain restano authority per persisted-state e semantic validation, per esempio:

```text
entity/version existence
lifecycle state
published admission
effective-schema membership
PrimitiveType semantic parsing/canonicalization/constraints
lineage compatibility
conflict predicates
ownership cycles
```

Business validation non viene spostata nel router/Pydantic model.

---

## 3. API-03.1 ratified decisions

```text
A3.1
JSON object keys use snake_case; command route segments use kebab-case.

A3.2
Command DTOs reject unknown fields and generic scalar coercion.

A3.3
Omission and explicit caller intent are distinct.

A3.4
Defaults and implicit resolution may apply only to omitted fields when the
command contract explicitly defines omission semantics.

A3.5
An explicitly supplied invalid value fails; it is never repaired, replaced
or shadowed by a default.

A3.6
JSON null is valid only where null itself is an explicitly valid semantic
field state; null never generically means omitted/default/clear/remove.

A3.7
Object CREATE canonical_name omitted -> UUID-string fallback;
canonical_name explicit null/empty/invalid -> failure.

A3.8
Implicit exact-version/default resolution is represented by omission,
never by null.

A3.9
Canonical response representation follows canonical domain state,
independently from accepted non-canonical lexical input alternatives.

A3.10
Transport performs syntactic/structural validation; persisted-state and
semantic validation remain application/domain responsibility.
```

---

## 4. API-03 pre-flight finding — `core.byte_size`

La re-validation di `datatype.md` conferma la domain semantics M1:

```text
core.byte_size
    exact non-negative information quantity
    SI and IEC units are semantically distinct
    fractional input is valid only when exact conversion
    produces an integer number of bytes
```

La re-validation di `persistence-model.md` / PERSIST-12 conferma invece il canonical persisted state:

```text
core.byte_size
    -> JSON integer number
    -> exact bytes
```

Non esiste quindi alcuna contraddizione nel consentire una forma di input più ergonomica: **accepted input syntax e canonical persisted/read representation sono boundary distinti**.

---

## 5. Ratified `core.byte_size` public wire input

Ovunque il public API accetti un semantic value di un exact DTV con `base_type = core.byte_size` — inclusi Object property input, DataType constraint/enum values e ObjectTemplate `migration_default` — M1 accetta due JSON carrier espliciti.

### 5.1 Exact bytes integer

```json
1024
```

Semantica:

```text
JSON non-negative integer
-> exact byte count
```

Boolean non è un integer byte-size input.

### 5.2 Quantity string with explicit SI/IEC unit

Esempi validi:

```json
"1 KiB"
"1MiB"
"1.5 MB"
"0.1 kB"
```

Canonical suffix vocabulary M1, case-sensitive:

```text
SI
    B
    kB
    MB
    GB
    TB
    PB
    EB

IEC
    KiB
    MiB
    GiB
    TiB
    PiB
    EiB
```

Sono accettate esclusivamente due separator shape fra quantità e unità:

```text
adjacent
    "1MiB"

one ASCII space
    "1 MiB"
```

Non vengono accettati alias alternativi o case folding, per esempio:

```text
KB
mb
M
megabyte
mega
```

La parte numerica usa exact decimal lexical semantics:

```text
non-negative
ordinary decimal notation
no exponent notation
no leading plus sign
```

Quindi, per esempio:

```text
"1.5 MiB"  valid if exact conversion is integral bytes
"1e3 B"    invalid
"-1 MiB"   invalid
```

### 5.3 Exact conversion rule

Parsing/canonicalization concettuale:

```text
parse exact decimal quantity
-> multiply by exact unit multiplier
-> require mathematical result to be an integer >= 0
-> canonical byte count integer
```

Esempi:

```text
1 MB
    -> 1,000,000 bytes

1 MiB
    -> 1,048,576 bytes

1.5 KiB
    -> 1,536 bytes

0.1 kB
    -> 100 bytes

0.1 KiB
    -> invalid because 102.4 bytes is not an integer byte count
```

Nessun floating-point arithmetic approssimato può diventare authority della conversione.

---

## 6. Canonical `core.byte_size` output and persistence

Indipendentemente dalla accepted input representation, il canonical API read/response value e la persistence representation sono sempre:

```text
non-negative JSON integer
containing exact bytes
```

Quindi input equivalenti:

```json
1024
```

```json
"1 KiB"
```

convergono entrambi a canonical response/state:

```json
1024
```

La lexical unit scelta dal caller non viene preservata come domain state o display metadata.

---

## 7. `core.byte_size` wire/domain validation boundary

Il transport DTO dichiara esplicitamente la union di carrier ammessi per `core.byte_size`; non si tratta di generic scalar coercion.

Il transport può rifiutare malformed JSON/type/lexical shape. Il PrimitiveType/domain codec resta authority per:

- exact quantity parsing;
- SI/IEC multiplier semantics;
- exact-integral-byte requirement;
- constraint validation;
- canonicalization a integer bytes.

La stessa primitive parsing/canonicalization semantics deve essere riusata in tutti i public input position che accettano `core.byte_size`; non devono esistere parser divergenti per Object values, enum, constraint o migration defaults.

---

## 8. Ratified byte-size wire decisions

```text
A3-BS-01
core.byte_size accepts either a non-negative JSON integer meaning exact bytes
or a JSON string quantity using the canonical SI/IEC unit vocabulary.

A3-BS-02
SI and IEC suffixes are case-sensitive and distinct:
B/kB/MB/GB/TB/PB/EB and KiB/MiB/GiB/TiB/PiB/EiB.

A3-BS-03
Both adjacent and one-ASCII-space quantity/unit forms are accepted;
alternative aliases/case folding are not.

A3-BS-04
String quantities use non-negative exact decimal ordinary notation;
exponent notation and leading plus are not accepted.

A3-BS-05
Fractional quantity input is accepted only when exact conversion yields
an integer number of bytes.

A3-BS-06
Canonical API output and PostgreSQL persistence are always a JSON integer
containing exact bytes; caller lexical units are not preserved.

A3-BS-07
One PrimitiveType parsing/canonicalization contract is reused across Object
values, constraints/enums and migration_default input.
```

---

## 9. API-03 remaining work

Still open and to be revalidated/ratified point-by-point:

```text
expected_revision HTTP placement
DataType CREATE/REVISE DTOs
ObjectTemplate complete local candidate CREATE/REVISE DTOs
Object CREATE/DATA_CHANGE/SCHEMA_CHANGE/ownership DTOs beyond canonical_name omission
RelationshipDefinition discriminated CREATE/RENAME DTOs
Relationship CREATE DTO
remaining primitive public-input lexical forms
canonical read DTO conventions
pagination/filter/list envelopes
success/failure HTTP mapping
```
