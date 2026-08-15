# M1 — ObjectTemplate Lifecycle & Identity

**Status:** DRAFT

## 1. Stable identity

Concettualmente:

```text
ObjectTemplate
--------------
id
namespace
name
description
abstract
default_version
```

La lineage possiede inoltre zero o una parent lineage semanticamente stabile.

Regole:

- `id`, `namespace`, `name`, `abstract` sono immutabili;
- `(namespace, name)` è univoco tra ObjectTemplate;
- `description` è metadata mutabile e non semantico;
- atomic last-write-wins è accettabile per `description`;
- la parent lineage non cambia tramite normali mutation;
- `default_version` è semantic policy state mutabile;
- non esiste uno `status` separato sulla lineage;
- rename, namespace move e aliases sono fuori M1;
- non esiste lineage-level optimistic `revision`.

La collocazione fisica di `parent_template_id` nel modello relazionale non ne determina il livello semantico.

## 2. Naming e canonical model identifier

`ObjectTemplate.name`, property name e component-slot name:

```text
[a-z][a-z0-9_]*
```

Massimo 64 caratteri. Nessuna lowercase/trimming/replacement automatica: input non conforme viene rifiutato.

Namespace grammar condivisa con `DataType`:

```text
namespace = segment("." segment)*
segment   = [a-z][a-z0-9_]*
```

Regole:

- max 64 caratteri per segmento;
- max 255 caratteri totali;
- `core` e `core.*` riservati al kernel;
- nessuna normalizzazione automatica.

Il tipo della model entity non è parte del namespace.

Canonical fully-qualified model identifier:

```text
<kind>.<namespace>.<name>
```

Il `kind` è kernel-defined, stabile e non configurabile. In M1 almeno:

```text
datatype
objecttemplate
```

Esempi:

```text
datatype.network.routing.bgp_asn
objecttemplate.network.router
```

L'unicità `(namespace, name)` resta per domain entity type; M1 non introduce uniqueness cross-table globale.

## 3. Parent lineage

Una ObjectTemplate lineage può avere zero o una parent lineage.

La parent lineage viene stabilita alla create e rimane immutabile nelle normali operation.

```text
Router/v1 -> NetworkDevice/v2
Router/v2 -> NetworkDevice/v4
```

è ammesso.

```text
Router/v1 -> NetworkDevice/v2
Router/v2 -> VirtualMachine/v1
```

è vietato.

L'ancestry rappresenta `IS-A` a livello di lineage.

Un eventuale futuro cambio parent sarà una **controlled type reclassification A -> B**. Non verrà introdotto un generic operator update di `parent_template_id`.

## 4. Exact parent-version pin

Ogni non-root ObjectTemplateVersion materializza sempre:

```text
(parent_template_id, parent_version)
```

Non esistono floating `latest/default` references.

Una nuova selection può essere:

- explicit: exact version specificata;
- implicit: `parent_version` omessa e risolta tramite `parent.default_version`.

L'implicit resolution viene materializzata immediatamente come exact pin.

Una nuova admission/rebinding richiede che la exact parent version rimanga `PUBLISHED` fino al commit.

`create-next` non risolve nuovamente il parent default: copia esattamente il parent pin della source.

Una nuova DRAFT può quindi nascere con una exact parent version divenuta nel frattempo `DEPRECATED`: lo stato è well-formed ma non publishable finché il final parent pin non è PUBLISHED.

## 5. Acyclic inheritance

L'inheritance graph deve essere aciclico.

Le normali operation M1 preservano l'aciclicità per costruzione: il parent viene scelto alla nascita della lineage, deve già esistere e non può essere poi modificato tramite normale mutation.

Il resolver deve comunque rilevare defensively eventuali cicli e fallire esplicitamente.

M1 non introduce un limite hard-coded alla inheritance depth.

## 6. Version model

Concettualmente:

```text
ObjectTemplateVersion
---------------------
template_id
version
revision
status
parent_template_id
parent_version
local_properties
local_components
```

`version` è un intero positivo univoco tra le versions attualmente esistenti della lineage.

Nuova allocation:

```text
max(existing_versions) + 1
```

I gap sono ammessi.

Se viene eliminato il DRAFT col version number massimo, quel numero può essere riutilizzato.

Il version number non è un audit sequence permanente.

## 7. Lifecycle

Lifecycle monotono:

```text
DRAFT -> PUBLISHED -> DEPRECATED
```

Nessuna reverse transition.

Più DRAFT possono coesistere senza limite hard-coded.

### 7.1 DRAFT

Una DRAFT è una mutable semantic candidate.

Deve essere sempre **well-formed**, ma può essere temporaneamente non publishable.

Possiede `revision`, generation token dell'intera candidate snapshot:

```text
parent_version
local properties
local components
```

Nuova DRAFT: `revision=1`.

### 7.2 PUBLISHED

Una PUBLISHED:

- è strutturalmente immutabile;
- appartiene all'active model graph;
- è ammessa per nuovi direct binding;
- può essere `default_version`;
- non è cancellabile individualmente.

### 7.3 DEPRECATED

Una DEPRECATED:

- è strutturalmente immutabile;
- rappresenta una snapshot legacy;
- resta valida per state/binding già ammessi;
- non riceve nuovi direct binding;
- può essere source di `create-next`;
- non è cancellabile individualmente.

## 8. create-next

`create-next(source=exact_version)` richiede source `PUBLISHED` o `DEPRECATED`, mai DRAFT.

La source non deve essere `MAX(version)`.

La nuova version:

- usa `max(existing)+1`;
- nasce DRAFT revision 1;
- clona exact parent pin e local persisted declarations della source;
- non esegue opportunistic dependency upgrade;
- non mantiene una domain relation `derived_from`.

Provenance/audit della source è future capability.

## 9. Draft optimistic concurrency

`revise`, `publish` e delete DRAFT richiedono `expected_revision`.

Una revise può committare solo se target ancora DRAFT e `revision == expected_revision`.

Una revise riuscita incrementa revision esattamente una volta, indipendentemente dal numero di row SQL modificate.

Publish non incrementa revision perché non cambia la structural candidate.

Delete/revise/publish concorrenti basati sulla stessa candidate generation devono essere mutuamente consistenti.

La public HTTP representation di questo token è definita da `api-wire-contract.md` / API-03.2: REVISE, PUBLISH e DELETE_DRAFT usano uniformemente il required query parameter `expected_revision` con positive-integer lexical shape. Il token non è una generic HTTP resource revision e M1 non usa ETag/If-Match per questa semantica.

## 10. default_version

`ObjectTemplate.default_version` replica intenzionalmente il contratto `DataType`.

Invariante:

```text
default_version IS NULL
OR
default_version references a PUBLISHED version
of the same ObjectTemplate lineage
```

Regole:

- explicit pin: exact target deve restare PUBLISHED fino al commit;
- implicit pin: resolve lineage default e materialize exact pin;
- first publish con default NULL -> auto-default;
- publish successive non cambiano il default;
- `set_default` accetta solo exact PUBLISHED version della stessa lineage;
- `clear_default` disabilita implicit pinning;
- existing bindings non cambiano quando cambia il default;
- current default non può essere deprecated;
- nessun fallback automatico.

## 11. Deprecate ObjectTemplateVersion

Una PUBLISHED OTV può diventare DEPRECATED solo se:

1. non è current `default_version`;
2. non esistono direct model-plane consumer `PUBLISHED` che la referenziano tramite lifecycle-sensitive exact-version dependency.

In M1 una child OTV PUBLISHED che la pinna come exact parent è un blocker.

Non bloccano:

- Object runtime esistenti;
- DRAFT model consumers;
- DEPRECATED model consumers;
- lineage-level references, inclusi component slots.

È sufficiente un direct reverse lookup; non serve graph traversal transitiva.

`publish consumer` e `deprecate dependency` devono essere fortemente consistenti: non possono entrambe committare producendo un edge `PUBLISHED -> DEPRECATED`.

## 12. Delete semantics

### 12.1 Single version

Solo DRAFT è cancellabile individualmente, con `expected_revision`.

PUBLISHED e DEPRECATED non sono cancellabili individualmente.

### 12.2 Entire lineage

Whole-lineage hard delete è ammessa solo se nessun consumer esterno referenzia la lineage o una sua exact version.

Internal versions, local declarations e internal default pointer vengono rimossi insieme.

External references bloccano la delete e non vengono modificate implicitamente.

Anche reference provenienti da DRAFT persistiti sono dependency reali.

Esempi di external dependency:

- Object -> exact OTV;
- child ObjectTemplate -> exact parent OTV;
- component slot di altra OTV -> target lineage;
- altri model consumer M1/futuri.

Nessun semantic cascade verso altri domini.

## 13. Read consistency

Ordinary GET/list restituiscono uno snapshot transazionalmente coerente della singola operation.

Non è garantita repeatability tra richieste separate.

Read usate per admission/mutation devono preservare fino al commit i predicate rilevanti, per esempio:

```text
implicit default resolution
parent exact admission
set_default
publish
deprecate
delete
```
