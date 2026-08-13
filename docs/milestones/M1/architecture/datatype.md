# M1 — DataType Architecture

**Status:** DRAFT

## 1. Scopo

Questo documento definisce la semantica architetturale del dominio `DataType` per la milestone M1.

Il documento è normativo per:

- responsabilità e boundary del concetto `DataType`;
- catalogo dei `PrimitiveType` built-in;
- canonicalizzazione dei valori;
- constraint supportati;
- lifecycle e versioning;
- draft concurrency semantics;
- explicit e implicit pinning;
- deletion semantics;
- read consistency;
- invarianti del dominio.

I meccanismi PostgreSQL concreti utilizzati per garantire le invarianti concorrenti — row lock, CAS, constraint, isolation level e relativi dettagli — saranno definiti nei documenti tecnici/concurrency della milestone e non sono fissati qui salvo dove il comportamento semantico richieda esplicitamente una determinata proprietà.

---

## 2. Responsabilità del DataType

### 2.1 Valore atomico

Un `DataType` rappresenta un dominio di valori atomici nominato e versionato.

Una `DataTypeVersion`:

- è basata su esattamente un `PrimitiveType` built-in;
- può restringere il dominio del primitive tramite constraint supportati;
- descrive il significato e l'insieme dei valori ammissibili per un singolo valore.

`DataType` non modella:

- object structure;
- nested properties;
- entity identity;
- relationships;
- component ownership.

La composizione strutturale di entità appartiene a `ObjectTemplate` e ai relativi meccanismi di component.

### 2.2 Value vs entity

La distinzione architetturale è:

```text
DataType
    -> value semantics

ObjectTemplateProperty
    -> associa uno o più valori a una property

Component
    -> associa Object con identità propria e ownership strutturale
```

Collection properties e structured value types non fanno parte del DataType atomico M1.

---

## 3. PrimitiveType

### 3.1 Autorità

`PrimitiveType` rappresenta una capability scalare built-in del kernel NETAUTO.

I primitive:

- sono definiti dall'applicazione;
- sono immutabili;
- non sono entità configurabili dall'utente;
- non sono persistiti come domain entities mutabili;
- fanno parte della versione del kernel NETAUTO.

Un nuovo concetto definito dall'utente deve normalmente essere modellato come `DataType` sopra un primitive esistente.

L'aggiunta di un nuovo primitive rappresenta una modifica di capability del kernel, non una normale operazione CRUD.

### 3.2 Catalogo M1

M1 supporta i seguenti primitive:

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

Runtime/plugin extensibility dei primitive è fuori M1.

---

## 4. Stable identity del DataType

La stable identity contiene concettualmente:

```text
DataType
--------
id
namespace
name
description
default_version
```

Semantica:

- `id` è immutabile;
- `namespace` è immutabile;
- `name` è immutabile;
- `(namespace, name)` costituisce il qualified human-readable identifier e deve essere univoco;
- `description` è metadata mutabile e non semantico;
- `default_version` è opzionale e determina l'implicit pinning.

M1 non introduce uno `status` separato sulla lineage `DataType`.

Rename, namespace move e aliasing sono fuori M1.

---

## 5. DataTypeVersion

Una `DataTypeVersion` rappresenta una snapshot versionata del dominio di valori.

Contiene concettualmente almeno:

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

### 5.1 Primitive stability nella lineage

Per M1 tutte le versioni della stessa `DataType` lineage devono utilizzare lo stesso `PrimitiveType`.

Il primitive viene scelto alla creazione della lineage e non cambia successivamente, incluso durante lo stato `DRAFT` della v1.

`base_type` rimane comunque informazione a livello di versione, così da non precludere una futura capability esplicita di representation migration.

Cross-primitive evolution è fuori M1.

### 5.2 Version number

`version` è un intero positivo univoco tra le versioni attualmente esistenti della stessa lineage.

La nuova versione viene allocata come:

```text
max(existing_versions) + 1
```

Regole:

- i gap intermedi non vengono riempiti;
- se viene cancellato il `DRAFT` con version number massimo, quel numero può essere riutilizzato da una successiva creazione;
- il version number non è un audit sequence permanente;
- le versioni entrate nel lifecycle stabile non vengono riutilizzate perché `PUBLISHED` e `DEPRECATED` non sono cancellabili individualmente.

### 5.3 Source di create-next

`create-next` riceve esplicitamente una source version.

La source:

- deve appartenere alla stessa lineage;
- deve essere `PUBLISHED` o `DEPRECATED`;
- non può essere `DRAFT` in M1.

La source viene utilizzata esclusivamente come snapshot iniziale per la nuova versione.

La nuova versione non mantiene alcuna relazione referenziale `derived_from` verso la source.

Eventuale provenance della creazione appartiene a un futuro audit/history model, non alle invarianti DataType.

Più `DRAFT` possono esistere contemporaneamente nella stessa lineage senza un limite hard-coded M1.

---

## 6. Lifecycle

Il lifecycle di una `DataTypeVersion` è strettamente monotono:

```text
DRAFT -> PUBLISHED -> DEPRECATED
```

Non esistono transizioni inverse.

### 6.1 DRAFT

Una versione `DRAFT`:

- non è ammissibile per nuovi consumer;
- può essere revisionata;
- può essere pubblicata;
- può essere cancellata individualmente;
- ha una `revision` mutabile usata come optimistic concurrency token.

Sono immutabili anche durante DRAFT:

- `datatype_id`;
- `version`;
- `base_type`.

I constraint costituiscono la mutable semantic snapshot del draft.

### 6.2 PUBLISHED

Una versione `PUBLISHED`:

- è una snapshot immutabile;
- può essere usata per nuovi explicit binding;
- può essere scelta come `default_version`;
- può diventare `DEPRECATED`;
- non può essere cancellata individualmente.

### 6.3 DEPRECATED

Una versione `DEPRECATED`:

- è una snapshot immutabile;
- rimane semanticamente valida per tutti i binding già materializzati;
- non è ammissibile per nuovi binding;
- può essere usata come source di `create-next`;
- non può essere cancellata individualmente.

La deprecazione non invalida retroattivamente consumer esistenti.

---

## 7. Draft optimistic concurrency

### 7.1 Revision token

Ogni `DataTypeVersion DRAFT` possiede una `revision` monotona della mutable snapshot.

La `revision`:

- nasce a `1`;
- aumenta a ogni revise del contenuto del draft;
- non rappresenta una snapshot storica recuperabile;
- non sostituisce il version number;
- è esclusivamente un generation/concurrency token.

### 7.2 Revise

Una revise deve dichiarare la `expected_revision`.

La mutation può avere successo soltanto se, al commit, la versione:

- esiste;
- è ancora `DRAFT`;
- possiede ancora la revisione attesa.

Una revise stale deve fallire e non può produrre last-write-wins silenzioso.

Una revise riuscita incrementa `revision`.

### 7.3 Publish

La publish deve dichiarare la `expected_revision` della snapshot che l'operatore intende pubblicare.

Se il draft è stato revisionato nel frattempo, la publish deve fallire.

La publish cambia lifecycle ma non modifica il contenuto editoriale; pertanto non incrementa la `revision`.

### 7.4 Delete DRAFT

La delete individuale di un `DRAFT` deve dichiarare la `expected_revision`.

Delete, revise e publish concorrenti sulla stessa revision devono essere mutuamente consistenti: al massimo una delle operazioni basate sulla stessa mutable snapshot può avere successo.

M1 non generalizza la `revision` a tutti gli aggregate. La stessa semantica verrà applicata a `ObjectTemplateVersion DRAFT`, che presenta lo stesso lifecycle editoriale mutabile.

---

## 8. Primitive canonicalization

NETAUTO distingue:

```text
validation
    -> il valore è ammissibile?

canonicalization
    -> qual è la rappresentazione autorevole dello stesso valore semantico?

normalization policy
    -> trasformazione business/domain-specific
```

M1 supporta canonicalizzazione soltanto quando è una proprietà intrinseca e non ambigua del `PrimitiveType`.

I `DataType` non introducono automaticamente normalization o transformation policies.

I valori persistiti e restituiti dal canonical state utilizzano la forma canonica del primitive.

### 8.1 core.string

Canonicalization identity.

NETAUTO non applica automaticamente:

- lowercase/uppercase;
- trimming;
- Unicode normalization business-specific;
- altre trasformazioni testuali.

Un `mac_address` modellato come `core.string + pattern` rimane quindi una stringa: eventuale case normalization non viene introdotta implicitamente.

### 8.2 core.integer

Rappresenta un numero intero esatto.

I boolean non sono integer validi.

### 8.3 core.number

Rappresenta un numero decimale finito esatto.

La semantica del dominio non deve dipendere da floating-point binario.

Sono invalidi:

- `NaN`;
- `+Infinity`;
- `-Infinity`.

Rappresentazioni numericamente equivalenti rappresentano lo stesso valore canonico.

`core.integer` rimane distinto per i domini limitati agli interi.

Precision/scale policy, unità di misura generiche e arithmetic engine sono fuori M1.

### 8.4 core.boolean

Rappresentazione booleana canonica.

### 8.5 core.date

Rappresenta una data calendariale valida in forma ISO canonica.

### 8.6 core.datetime

`core.datetime` rappresenta esclusivamente un istante temporale assoluto.

Un input valido deve specificare esplicitamente:

- `Z`; oppure
- un UTC offset.

Naive/local datetime non sono validi.

Prima di entrare nel canonical state il valore viene convertito in UTC.

NETAUTO non preserva l'offset originale e tutte le read espongono la forma UTC canonica.

La conversione verso timezone locali è responsabilità dei consumer/UI.

Un eventuale future local/wall-clock datetime richiederà un primitive distinto.

### 8.7 core.ip

Rappresenta un singolo IPv4 o IPv6 address semanticamente valido.

Rappresentazioni equivalenti dello stesso indirizzo convergono alla forma canonica del primitive.

### 8.8 core.ip_prefix

Rappresenta una rete IPv4 o IPv6 valida.

La canonicalizzazione normalizza rappresentazioni equivalenti della stessa rete ma non corregge input semanticamente invalidi.

Ad esempio un valore con host bits impostati non viene automaticamente trasformato nella network corrispondente: viene rifiutato.

### 8.9 core.byte_size

`core.byte_size` rappresenta una quantità esatta non negativa di informazione.

L'unità canonica è il byte.

Sono semanticamente distinte le unità SI e IEC, ad esempio:

```text
1 GB  = 1,000,000,000 B
1 GiB = 1,073,741,824 B
```

Rappresentazioni equivalenti convergono allo stesso numero intero canonico di byte:

```text
1 GiB
1024 MiB
1073741824 B
    -> stesso canonical value
```

Sono ammesse rappresentazioni frazionarie soltanto quando la conversione produce esattamente un numero intero di byte.

La forma originaria e l'unità scelta nell'input non vengono preservate.

Un framework generale di unità di misura e un expression engine aritmetico sono fuori M1.

---

## 9. Constraint model

### 9.1 Principio

I constraint di una `DataTypeVersion` sono congiuntivi.

Un valore runtime è valido se e solo se soddisfa:

1. la semantica del `PrimitiveType`;
2. tutti i constraint dichiarati dalla exact `DataTypeVersion`.

M1 applica guardrail rigorosi ma non introduce un general-purpose satisfiability solver.

Devono essere rifiutati almeno:

- constraint non supportati dal primitive;
- malformed constraint values;
- constraint duplicati;
- contraddizioni dirette come `minimum > maximum` o `min_length > max_length`;
- enum member incompatibili con gli altri constraint.

Combinazioni formalmente valide ma semanticamente insolite rimangono responsabilità dell'operatore salvo i casi esplicitamente coperti dal kernel.

### 9.2 Matrice M1

| Primitive | Constraint M1 |
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

`ip_version` ammette esclusivamente i valori `4` e `6`.

### 9.3 Pattern

Il constraint `pattern`:

- è supportato da `core.string`;
- utilizza il dialetto standard Python `re`;
- deve essere sintatticamente compilabile;
- usa semantica di full match, equivalente a `re.fullmatch()`.

Il pattern descrive quindi l'intero valore, non una sottostringa.

La semantica normativa è quella NETAUTO/Python. Eventuali artefatti JSON Schema compilati devono preservare questa semantica e non costituiscono un commitment alla portabilità verso engine regex esterni.

### 9.4 Enum

`enum` è disponibile per tutti i primitive M1.

Un enum rappresenta un insieme finito e non ordinato di valori semantici ammessi.

Pipeline di definizione:

```text
raw enum member
    -> primitive parse/validation
    -> primitive canonicalization
    -> duplicate detection
    -> validation against all other constraints
    -> canonical enum member
```

Regole:

- l'enum non può essere vuoto;
- ogni membro deve essere valido per il primitive;
- ogni membro deve soddisfare tutti gli altri constraint della stessa DataTypeVersion;
- i duplicati vengono rilevati dopo canonicalizzazione;
- l'ordine non ha significato semantico.

Esempi di duplicate semantico:

```text
core.number:
    [1, 1.0, 1.00]

core.datetime:
    [2026-08-13T14:00:00Z,
     2026-08-13T16:00:00+02:00]

core.byte_size:
    [1 GiB, 1024 MiB]
```

### 9.5 Constraint esplicitamente non appartenenti a DataType

Non sono `DataType` constraint:

```text
required
nullable
default
unique
immutable
cardinality
```

Boundary:

- presence/cardinality/default semantics appartengono alla property declaration;
- uniqueness e altre global/dataset constraints appartengono a livelli superiori;
- `DataType` guarda esclusivamente alla validità del singolo valore.

---

## 10. Default version e pinning

### 10.1 Principio

Il version number, il lifecycle status e `default_version` rappresentano concetti indipendenti.

`PUBLISHED` significa:

> snapshot stabile e ammessa per nuovi explicit binding.

Non significa automaticamente:

> versione usata da tutti i nuovi consumer impliciti.

### 10.2 default_version

Ogni `DataType` può designare zero o una exact `DataTypeVersion PUBLISHED` come `default_version`.

Invariante:

```text
default_version IS NULL
OR
default_version references a PUBLISHED version
of the same DataType lineage
```

### 10.3 Explicit pinning

Un consumer che specifica una exact version può creare un nuovo binding soltanto se tale versione è `PUBLISHED` fino al commit dell'admission operation.

`DRAFT` e `DEPRECATED` non sono ammissibili per nuovi binding.

### 10.4 Implicit pinning

Un consumer che omette la versione risolve `DataType.default_version`.

La resolution:

- fallisce se `default_version` è `NULL`;
- deve vedere una target version `PUBLISHED`;
- materializza sempre un exact version pin nel consumer;
- non persiste mai un riferimento floating tipo `latest`.

Cambiare successivamente il default non modifica binding già materializzati.

### 10.5 Publish e promotion

`publish(version)` e `set_default(version)` sono operazioni semanticamente distinte.

Regole:

- la prima publish effettuata quando `default_version` è `NULL` assegna automaticamente quella versione come default;
- le publish successive non modificano il default esistente;
- una versione pubblicata non-default può quindi essere testata tramite explicit pinning prima della promotion;
- `set_default(version)` accetta esclusivamente una versione `PUBLISHED` della stessa lineage;
- `set_default` sulla versione già default può essere idempotente.

### 10.6 clear_default

`clear_default()` imposta:

```text
default_version = NULL
```

senza modificare il lifecycle delle versioni.

Effetto:

- implicit pinning disabilitato;
- explicit pinning verso altre versioni ancora `PUBLISHED` continua a essere possibile.

Una lineage può quindi avere tutte le versioni `DEPRECATED` e nessun default, rappresentando un DataType ritirato per nuovi utilizzi ma ancora valido per binding storici.

### 10.7 Deprecate del default

Una versione che costituisce il default non può essere deprecata finché il default non viene prima:

- spostato su un'altra versione `PUBLISHED`; oppure
- rimosso tramite `clear_default()`.

NETAUTO non effettua fallback automatico verso un'altra versione pubblicata.

---

## 11. Strong consistency delle mutation

Strong consistency è un requisito primario delle operazioni DataType.

Ogni mutation deve preservare tutte le invarianti interessate anche in presenza di concorrenza.

Non è sufficiente che ogni singola transazione produca localmente uno stato formalmente valido: nessun interleaving concorrente supportato può committare uno stato che violi le invarianti del kernel.

Esempi:

```text
set_default(v5)
vs
deprecate(v5)

-> non può mai produrre:
   default=v5 AND v5=DEPRECATED
```

```text
revise(DRAFT r7)
vs
publish(DRAFT r7)

-> al massimo una operazione basata su r7 può avere successo
```

```text
create-next
vs
create-next sulla stessa lineage

-> version allocation deve rimanere univoca
```

I meccanismi concreti saranno definiti nei concurrency contract.

---

## 12. Delete semantics

### 12.1 Delete di una singola versione

Solo una `DRAFT` può essere eliminata individualmente.

La delete richiede `expected_revision`.

Una `PUBLISHED` o `DEPRECATED` non può essere eliminata individualmente.

### 12.2 Delete dell'intera lineage

L'intera `DataType` lineage può essere eliminata atomicamente, indipendentemente dal fatto che alcune versioni siano state pubblicate in passato, se e solo se nessuna versione è attualmente referenziata da consumer esterni.

I riferimenti interni della lineage, incluso `default_version`, non devono impedire la cancellazione atomica dell'intera lineage.

La persistence layer authority deve impedire dangling references anche in presenza di race tra delete e creazione di nuovi consumer.

---

## 13. Read consistency

### 13.1 Ordinary read

Normali GET/list sono non-locking e restituiscono una snapshot transazionalmente consistente dello stato osservato dalla singola read operation.

Non viene garantita repeatable-read semantics tra richieste separate.

È quindi normale osservare:

```text
GET -> DRAFT revision=7
GET successiva -> DRAFT revision=8
```

### 13.2 Composite reads

Read che restituiscono insieme lineage metadata e version state non devono esporre combinazioni che non siano mai coesistite nella stessa database snapshot.

In particolare `default_version` e relativo stato devono essere osservati in modo internamente consistente.

### 13.3 Admission reads

Una read utilizzata per prendere una decisione di admission/mutation non è una semplice lookup informativa.

Il predicato rilevante deve rimanere valido fino al commit dell'intera Unit of Work.

Esempio implicit pinning:

```text
resolve default_version
verify target PUBLISHED
materialize exact consumer binding
COMMIT
```

Tale workflow deve essere fortemente consistente rispetto a `set_default`, `clear_default`, `deprecate`, delete e altre operazioni concorrenti rilevanti.

---

## 14. Metadata concurrency

`DataType.description` è metadata mutabile e non semanticamente rilevante.

M1 accetta last-write-wins per update concorrenti della description, purché l'update sia atomico.

Non viene introdotta una lineage-level `revision` per proteggere metadata descrittivi.

Distinzione:

```text
DRAFT semantic snapshot
    -> optimistic revision obbligatoria

default_version semantic policy
    -> strong consistency tramite specifico concurrency contract

description non-semantic metadata
    -> atomic last-write-wins ammesso
```

---

## 15. Invarianti M1

### DT-INV-001 — Atomic value responsibility

Un DataTypeVersion descrive un singolo dominio di valori atomici e non una struttura di entità.

### DT-INV-002 — Built-in primitive authority

Ogni DataTypeVersion usa esattamente un PrimitiveType supportato dal kernel.

### DT-INV-003 — Stable lineage identity

`DataType.id`, `namespace` e `name` non cambiano durante la lifetime della lineage.

### DT-INV-004 — Qualified name uniqueness

Non possono esistere due DataType con la stessa coppia `(namespace, name)`.

### DT-INV-005 — Primitive stability

Tutte le DataTypeVersion appartenenti alla stessa lineage utilizzano lo stesso PrimitiveType in M1.

### DT-INV-006 — Positive unique version

Ogni versione esistente ha `version >= 1` ed è univoca nella lineage.

### DT-INV-007 — Lifecycle monotonicity

Le sole transizioni ammesse sono:

```text
DRAFT -> PUBLISHED -> DEPRECATED
```

### DT-INV-008 — Stable snapshot immutability

Una versione `PUBLISHED` o `DEPRECATED` è immutabile nel contenuto semantico.

### DT-INV-009 — Draft revision freshness

Una mutation dipendente dalla mutable snapshot del DRAFT può committare soltanto se la `expected_revision` coincide con quella corrente secondo il relativo concurrency contract.

### DT-INV-010 — Constraint validity

Ogni constraint è supportato dal primitive, formalmente valido e compatibile con le verifiche di coerenza M1.

### DT-INV-011 — Canonical value state

I valori che entrano nel canonical kernel state sono rappresentati nella forma canonica prevista dal PrimitiveType.

### DT-INV-012 — Canonical enum uniqueness

Gli elementi di un enum sono semanticamente unici dopo canonicalizzazione e soddisfano tutti gli altri constraint della DataTypeVersion.

### DT-INV-013 — Default target validity

`default_version` è `NULL` oppure punta a una exact `PUBLISHED` version della stessa lineage.

### DT-INV-014 — Binding admission

Un nuovo consumer può materializzare un exact binding soltanto verso una versione che rimane `PUBLISHED` fino al commit dell'operazione di admission.

### DT-INV-015 — No floating bindings

Ogni binding persistito materializza una exact DataTypeVersion; nessun consumer persistito segue dinamicamente il default.

### DT-INV-016 — Default deprecation safety

Una versione default non può diventare `DEPRECATED` finché `default_version` non è stato spostato o rimosso.

### DT-INV-017 — Draft-only individual deletion

Solo una DataTypeVersion `DRAFT`, con corretta stale-write protection, può essere eliminata individualmente.

### DT-INV-018 — Referential delete safety

L'intera lineage può essere cancellata soltanto quando nessun consumer esterno referenzia alcuna sua versione.

### DT-INV-019 — Strong concurrent consistency

Nessun interleaving concorrente supportato delle operazioni DataType può committare uno stato che violi una delle invarianti sopra definite.

---

## 16. Candidate future esplicitamente fuori M1

Le seguenti capability sono deliberate future candidates e non devono essere introdotte implicitamente durante M1:

- collection-valued properties;
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
- audit/provenance history della source di `create-next`.

---

## 17. Decisioni tecniche ancora da finalizzare

La semantica del presente documento non decide ancora:

- mapping PostgreSQL definitivo delle canonical value representations;
- representation di `core.number` exact decimal su API e persistence;
- wire syntax definitiva accettata da `core.byte_size`;
- dettagli testuali della canonical datetime representation;
- constraint SQL specifici;
- locking/CAS strategy per ogni operation;
- transaction isolation level per i singoli concurrency contract;
- shape REST definitiva di `expected_revision`;
- status code/API error code definitivi;
- endpoint REST definitivi per `set_default`, `clear_default` e delete della singola DRAFT version;
- representation JSON Schema e ruolo finale del compiler rispetto alle semantics native NETAUTO.

Tali decisioni devono essere definite prima del freeze dell'architecture M1 e prima della decomposizione in `steps.md`.
