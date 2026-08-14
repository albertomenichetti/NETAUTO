# M1 — DataType Architecture

**Status:** DRAFT — domain semantics, persistence/concurrency and complete public API contract are ratified; only the separate JSON Schema compiler role remains before final M1 architecture freeze.

## 1. Scopo

Questo documento definisce la semantica architetturale del dominio `DataType` per M1.

È normativo per:

- responsabilità e boundary del `DataType`;
- catalogo dei `PrimitiveType`;
- canonicalizzazione;
- constraint;
- lifecycle/versioning;
- draft concurrency;
- explicit/implicit pinning;
- active model graph deprecation safety;
- deletion;
- read consistency;
- invarianti.

I meccanismi PostgreSQL concreti sono definiti in:

- `persistence-model.md` — PERSIST-01..15;
- `persistence-uow-concurrency.md` — PERSIST-16..20 + REALIZE-15 lock-strength refinement;
- `concurrency-semantic-matrix.md` e `concurrency-postgresql-realization-matrix.md` — safety predicate e realization;
- `concurrency-postgresql-test-matrix.md` — real-PG concurrency coverage.

La public API representation è definita in:

- `api-wire-contract.md` — API-03.4 DataType command DTO e API-03.8 PrimitiveType lexical forms;
- `api-read-contract.md` — API-03.9 lineage/exact-version canonical read DTO;
- `api-list-contract.md` — API-03.10 collection envelope, keyset cursor, ordering, summary item e filters;
- `api-error-contract.md` — API-03.11 failure classes/codes, bounded details and success HTTP mapping.

## 2. Responsabilità

Un `DataType` rappresenta un dominio nominato e versionato di **valori atomici scalari**.

Una `DataTypeVersion`:

- usa esattamente un PrimitiveType built-in;
- può restringerne il dominio tramite constraint;
- descrive la validità di un singolo valore.

`DataType` non modella object structure, entity identity, relationship, component ownership o collection cardinality.

`ObjectTemplateProperty` può associare uno o più valori dello stesso exact DataTypeVersion; la collection semantics appartiene alla property, non al DataType.

## 3. PrimitiveType

PrimitiveType è capability scalare built-in del kernel:

- application/code-defined;
- immutable;
- non user-defined mutable DB entity;
- runtime catalog closed/configuration-independent in M1.

Catalogo M1:

```text
core.string
core.integer
core.number
core.boolean
core.date
core.datetime
core.ip
core.ip_prefix
core.byte_size
```

Runtime/plugin-defined primitive è fuori M1.

## 4. Stable identity, naming e model identifier

Concettualmente:

```text
DataType
--------
id
namespace
name
description
default_version
```

- `id`, `namespace`, `name` immutabili;
- `(namespace, name)` univoco tra DataType;
- `description` metadata mutabile, non semantico;
- `default_version` semantic policy state;
- nessuno status sulla lineage;
- rename, namespace move e aliasing fuori M1;
- nessuna lineage-level optimistic revision.

`name`:

```text
[a-z][a-z0-9_]*
```

max 64 caratteri, nessuna normalizzazione automatica.

Namespace grammar condivisa con ObjectTemplate:

```text
namespace = segment("." segment)*
segment   = [a-z][a-z0-9_]*
```

max 64 caratteri per segmento, max 255 totali; `core` e `core.*` riservati al kernel.

Canonical model identifier derivato:

```text
datatype.<namespace>.<name>
```

Il `kind=datatype` è kernel-defined e non è parte del namespace.

## 5. DataTypeVersion

Concettualmente:

```text
DataTypeVersion
---------------
datatype_id
version
revision
status
base_type
constraints
```

### 5.1 Primitive stability

Tutte le versioni della stessa lineage usano lo stesso PrimitiveType in M1.

Il primitive viene scelto alla create e non cambia, nemmeno sulla v1 DRAFT.

`base_type` può restare fisicamente version-level per non precludere future explicit representation migration.

Cross-primitive evolution è fuori M1.

### 5.2 Version number

`version` è positivo e univoco tra le versioni attualmente esistenti.

Nuova allocation:

```text
max(existing_versions) + 1
```

Gap ammessi.

Se il DRAFT col numero massimo viene eliminato, quel numero può essere riutilizzato.

Nessun irreversible sequence counter.

### 5.3 create-next

`create-next` riceve una source exact della stessa lineage.

Source ammessa:

```text
PUBLISHED
DEPRECATED
```

mai DRAFT.

La source non deve essere la version massima.

La nuova version:

- usa `max(existing)+1`;
- nasce DRAFT revision 1;
- clona la source semantic snapshot;
- non mantiene `derived_from`.

Più DRAFT possono coesistere senza limite hard-coded.

## 6. Lifecycle

```text
DRAFT -> PUBLISHED -> DEPRECATED
```

monotono.

DRAFT:

- mutable constraints;
- revise/publish/delete;
- revision concurrency token.

Immutabili anche in DRAFT:

```text
datatype_id
version
base_type
```

PUBLISHED:

- immutable snapshot;
- ammessa per nuovi direct binding;
- può essere default;
- non cancellabile individualmente.

DEPRECATED:

- immutable legacy snapshot;
- valida per binding già materializzati;
- non ammessa per nuovi direct binding;
- source valida per create-next;
- non cancellabile individualmente.

La deprecazione non invalida retroattivamente binding storici.

## 7. Draft optimistic concurrency

Ogni DRAFT nasce `revision=1`.

`revision` è generation token, non audit/history.

`revise(expected_revision=N)` può riuscire solo se la target è ancora DRAFT revision N; al successo incrementa N -> N+1.

`publish` richiede `expected_revision`; se riesce non incrementa revision.

Delete DRAFT richiede `expected_revision`.

Delete/revise/publish concorrenti sulla stessa generation devono essere mutuamente consistenti.

La public HTTP representation di questo token è definita da `api-wire-contract.md` / API-03.2: REVISE, PUBLISH e DELETE_DRAFT usano uniformemente il required query parameter `expected_revision` con positive-integer lexical shape. Il token non è una generic HTTP resource revision.

## 8. Primitive canonicalization

NETAUTO distingue validation, canonicalization e business normalization.

Canonicalizzazione solo quando è proprietà intrinseca e non ambigua del PrimitiveType.

Il canonical state è ciò che persistence/read/API espongono.

- `core.string`: identity; niente lowercase/trim automatici.
- `core.integer`: exact integer; boolean non valido come integer.
- `core.number`: finite exact decimal semantic; no NaN/Infinity; rappresentazioni numeric-equivalent convergono.
- `core.boolean`: canonical boolean.
- `core.date`: valid calendar date, canonical ISO representation.
- `core.datetime`: absolute instant; input deve avere offset o Z; canonical UTC; offset originale non preservato; no arbitrary rounding.
- `core.ip`: canonical IPv4/IPv6 address.
- `core.ip_prefix`: canonical valid network; host bits invalidi vengono rifiutati, non corretti.
- `core.byte_size`: exact non-negative information quantity, canonical integer bytes; SI e IEC distinti; fractional input solo se converte a integer bytes esatti.

La public accepted lexical form di ciascun primitive è congelata in `api-wire-contract.md` API-03.8; `core.byte_size` usa inoltre il dedicated contract A3-BS-01..07. Tutti gli input position (`Object` values, constraint/enum e `migration_default`) riusano lo stesso PrimitiveType parser/canonicalizer.

General units/arithmetic framework è fuori M1.

## 9. Constraint model

I constraint sono congiuntivi.

Devono essere rifiutati:

- constraint non supportati;
- malformed values;
- duplicazioni;
- contradiction dirette come `minimum > maximum`;
- enum member incompatibili con gli altri constraint.

Nessun general satisfiability solver.

Matrice M1:

| Primitive | Constraint |
|---|---|
| `core.string` | `min_length`, `max_length`, `pattern`, `enum` |
| `core.integer` | `minimum`, `maximum`, `enum` |
| `core.number` | `minimum`, `maximum`, `enum` |
| `core.boolean` | `enum` |
| `core.date` | `minimum`, `maximum`, `enum` |
| `core.datetime` | `minimum`, `maximum`, `enum` |
| `core.ip` | `ip_version`, `enum` |
| `core.ip_prefix` | `ip_version`, `enum` |
| `core.byte_size` | `minimum`, `maximum`, `enum` |

`ip_version` ∈ `{4,6}`.

### 9.1 Pattern

`core.string.pattern` usa Python standard `re`.

Validity: `re.compile()`.

Matching semantics: full match, equivalente a `re.fullmatch()`.

NETAUTO semantics sono normative; JSON Schema è eventuale compile target e deve preservarle.

### 9.2 Enum

`enum` è disponibile per tutti i primitive M1.

È un unordered finite set di semantic values.

Pipeline:

```text
raw member
-> primitive parse/validation
-> primitive canonicalization
-> duplicate detection
-> validation against all other constraints
-> canonical member
```

Duplicate detection avviene dopo canonicalization.

Ogni member deve soddisfare gli altri constraint.

### 9.3 Non-DataType constraints

Non appartengono al DataType:

```text
required
nullable
default
unique
immutable
cardinality
```

Presence/default/cardinality appartengono alla property; dataset/global invariant a livelli superiori.

## 10. default_version e pinning

`version`, lifecycle status e `default_version` sono dimensioni indipendenti.

```text
default_version IS NULL
OR
default_version references a PUBLISHED version
of the same DataType lineage
```

Explicit binding: exact version deve rimanere PUBLISHED fino al commit.

Implicit binding: resolve `default_version`, verify PUBLISHED, materialize exact pin.

Nessun persisted floating `latest/default`.

First publish con default NULL -> auto-default.

Publish successive non cambiano default.

`set_default(version)` solo exact PUBLISHED same lineage.

`clear_default()` imposta NULL e disabilita implicit pinning.

Current default non può essere deprecated; nessun fallback automatico.

## 11. Active model graph e deprecate

M1 adotta il principio:

> la lifecycle consistency viene pagata quando cambia il model-plane, non a ogni consumo del data-plane.

Una `DataTypeVersion PUBLISHED` non può diventare DEPRECATED mentre esiste un direct model-plane consumer `PUBLISHED` che la pinna tramite lifecycle-sensitive exact dependency.

In M1 un esempio fondamentale è:

```text
ObjectTemplateVersion PUBLISHED
    property -> exact DataTypeVersion
```

Se tale edge esiste, `deprecate(DTV)` deve fallire.

Non bloccano:

- DRAFT model consumer;
- DEPRECATED model consumer;
- binding storico non più parte del model graph attivo.

La current default DTV è anch'essa non deprecabile finché default non viene spostato o rimosso.

È sufficiente controllare direct active consumers; la consistency transitiva dell'active graph segue dagli invarianti di ogni PUBLISHED consumer.

`publish consumer` e `deprecate DTV` devono essere fortemente consistenti e non possono entrambe committare producendo un edge:

```text
PUBLISHED consumer -> DEPRECATED DTV
```

Conseguenza importante: un `Object create` che consuma una PUBLISHED ObjectTemplateVersion non deve ricertificare a runtime il lifecycle dell'intera DTV dependency closure; il model-plane attivo è già consistente.

## 12. Strong consistency delle mutation

Ogni mutation deve preservare gli invarianti anche sotto concorrenza.

Esempi:

```text
set_default(v5)
vs
deprecate(v5)

-> mai default=v5 e v5=DEPRECATED
```

```text
revise(DRAFT r7)
vs
publish(DRAFT r7)

-> al massimo una operation basata su r7 può avere successo
```

```text
publish OTV consumer -> DTV
vs
deprecate DTV

-> non possono entrambe committare se produrrebbero active edge verso DEPRECATED
```

```text
create-next
vs
create-next stessa lineage

-> allocation univoca
```

I meccanismi concreti sono definiti nei concurrency/persistence contract M1 indicati nella sezione 1.

## 13. Delete semantics

Single version:

- solo DRAFT cancellabile individualmente;
- delete richiede `expected_revision`;
- PUBLISHED/DEPRECATED non cancellabili individualmente.

Entire lineage:

- hard delete atomica ammessa solo se nessun consumer esterno referenzia alcuna version;
- internal default pointer non blocca whole-lineage delete;
- persistence authority deve impedire dangling references anche sotto race.

## 14. Read consistency

Ordinary GET/list non-locking e snapshot-consistent per la singola operation.

Nessuna repeatability tra richieste separate.

Composite reads non devono esporre combinazioni di lineage/default/version che non siano mai coesistite nella stessa DB snapshot.

Admission/mutation reads devono preservare fino al commit i predicate rilevanti.

Esempio implicit pinning:

```text
resolve default_version
verify target PUBLISHED
materialize exact binding
COMMIT
```

Public read/list semantics:

- API-03.9 separa lineage read da exact-version read;
- API-03.10 usa keyset pagination, `(namespace,name) ASC` per lineage e `version ASC` per nested versions;
- lineage list riusa il bounded lineage DTO;
- version list usa summary senza `constraints`;
- exact filters M1: lineage `namespace`/`name`, version `status`.

Ogni pagina resta una read snapshot-consistent indipendente; il cursor non è un cross-request snapshot token.

## 15. Metadata concurrency

`description` è non-semantic metadata.

Atomic last-write-wins è accettabile.

Nessuna lineage-level revision.

Distinzione:

```text
DRAFT semantic snapshot
    -> optimistic revision

default_version / lifecycle policy
    -> strong concurrency contract

description
    -> atomic last-write-wins
```

## 16. Invarianti M1

- **DT-INV-001:** DataTypeVersion descrive un singolo dominio atomico.
- **DT-INV-002:** ogni DTV usa esattamente un PrimitiveType kernel-supported.
- **DT-INV-003:** stable `id`, namespace e name.
- **DT-INV-004:** `(namespace,name)` univoco.
- **DT-INV-005:** PrimitiveType stabile nella lineage.
- **DT-INV-006:** positive unique current version.
- **DT-INV-007:** lifecycle monotono.
- **DT-INV-008:** PUBLISHED/DEPRECATED immutable.
- **DT-INV-009:** DRAFT mutation freshness tramite expected_revision.
- **DT-INV-010:** constraint validity.
- **DT-INV-011:** canonical value state.
- **DT-INV-012:** canonical enum uniqueness.
- **DT-INV-013:** default NULL oppure exact PUBLISHED same lineage.
- **DT-INV-014:** nuovi direct binding solo verso PUBLISHED fino al commit.
- **DT-INV-015:** no floating persisted binding.
- **DT-INV-016:** current default non deprecabile.
- **DT-INV-017:** PUBLISHED DTV non deprecabile con direct active/PUBLISHED model consumer.
- **DT-INV-018:** single-version delete solo DRAFT.
- **DT-INV-019:** whole-lineage delete solo senza external references.
- **DT-INV-020:** strong concurrent consistency di tutte le invarianti.

## 17. Candidate future / RFE

Fuori M1:

- structured/composite value types;
- cross-primitive DataType representation migration;
- runtime/plugin-defined PrimitiveType;
- general-purpose unit/quantity framework;
- arithmetic expression engine;
- local/wall-clock datetime primitive;
- `exclusive_minimum` / `exclusive_maximum`;
- `multiple_of`;
- IP network-membership constraint;
- IP prefix-length constraints;
- DataType rename/move/aliasing;
- generic constraint satisfiability solver;
- audit/provenance della source di create-next;
- advanced collection semantics a livello property oltre M1 `LIST` (SET, cardinalità arbitrarie, nested/heterogeneous collections).

## 18. Technical-contract status

Le seguenti decisioni **non sono più aperte** e sono normative nei persistence/concurrency/API document:

```text
PostgreSQL canonical persistence mapping
exact-decimal persistence representation
byte_size persistence as integer bytes
canonical datetime persistence details
SQL structural constraint strategy
locking / CAS / owner strength / lock ordering
active-model reverse lookup + required indices
READ COMMITTED mutation isolation baseline
whole-UoW retry/convergence boundaries
expected_revision public HTTP placement for REVISE/PUBLISH/DELETE_DRAFT
DataType CREATE/REVISE/command DTO shape (API-03.4)
PrimitiveType accepted public lexical forms + canonical public output (API-03.8 / A3-BS)
DataType lineage/exact-version read DTO shape (API-03.9)
DataType collection/list/pagination/filter contract (API-03.10)
public error-code/status/success mapping (API-03.11)
```

In particolare:

- `core.number` persiste e viene esposto canonicalmente come exact-decimal JSON string; API-03.8 accetta soltanto exact-decimal JSON string senza exponent/leading plus;
- `core.byte_size` persiste e viene esposto canonicalmente come integer bytes; il public input accetta integer bytes oppure strict SI/IEC quantity string secondo A3-BS-01..07;
- `core.datetime` persiste/esce canonical UTC `Z` con precisione massima microsecondo; API-03.8 congela la strict absolute-offset lexical form e il no-rounding contract;
- `core.ip`/`core.ip_prefix`, date, boolean, integer e string public lexical forms sono congelate da API-03.8;
- active DTV reverse lookup usa le authoritative property/OTV rows e gli indici di `persistence-model.md`;
- concurrency segue REALIZE-01..15 e i test PGTEST;
- `expected_revision` usa il required positive-integer query parameter definito da API-03.2, senza ETag/If-Match semantics;
- API-03.4 definisce CREATE come lineage + v1 DRAFT con `constraints` omission -> `{}`, REVISE come complete constraints candidate required e gli altri command DTO DataType;
- API-03.9/03.10 chiudono canonical read, summary list, exact filters e keyset pagination del dominio;
- API-03.11 chiude failure classes, concrete error codes/details e success response policy senza introdurre HTTP semantics nel domain layer.

Resta da definire/finalizzare prima del coding freeze soltanto:

- ruolo/esatta surface del JSON Schema compiler, se mantenuto in M1.
