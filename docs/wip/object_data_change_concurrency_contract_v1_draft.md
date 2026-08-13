# Object DATA_CHANGE — Concurrency Contract DRAFT v1

## 1. Stato del documento

**DRAFT RATIFICATO come contratto corrente dell'action `DATA_CHANGE`**

Questo documento descrive congiuntamente:

```text
- semantica Domain/Application
- invarianti di data mutation
- garanzie relazionali PostgreSQL
- race concorrenti
- protocollo transazionale
- atomicità mutation + audit
```

Baseline di riferimento:

```text
Object — Modello Relazionale Ratificato v1
Object — Domain & Business Model Ratificato v1
Object Rename — Concurrency Contract DRAFT v1
```

Nessun locking globale del model-plane o cross-plane viene introdotto.

---

# 2. Obiettivo dell'operazione

`DATA_CHANGE` modifica esclusivamente:

```text
objects.properties_json
```

della exact Object row identificata da:

```text
objects.id
```

e produce atomicamente:

```text
object_changes
kind = DATA_CHANGE
```

Devono rimanere invariati:

```text
id
canonical_name
template_id
template_version
```

Quindi `DATA_CHANGE`:

```text
- non è un rename
- non è una schema migration
- non modifica ownership/component attachment
```

---

# 3. Semantica della mutation

La mutation viene applicata allo stato corrente dell'Object.

Forma concettuale:

```text
current properties
+
requested data changes
=
complete candidate properties
```

La candidate deve essere costruita soltanto dopo aver stabilizzato la exact Object row.

Questo evita che una richiesta basata su uno stato ormai stale sovrascriva modifiche concorrenti già committate.

---

# 4. Race fondamentale: DATA_CHANGE vs DATA_CHANGE

Scenario senza coordinamento:

```text
initial:
    properties = P0

T1                           T2

READ P0                      READ P0

candidate P1                 candidate P2

UPDATE P1
audit P0 -> P1
COMMIT

                              UPDATE P2
                              audit P0 -> P2
                              COMMIT
```

Problemi:

```text
lost mutation
+
stale / false audit transition
```

La seconda mutation dovrebbe invece partire dallo stato realmente corrente al momento della propria esecuzione serializzata.

---

# 5. Exact Object row come state gate

`DATA_CHANGE` deve acquisire:

```sql
SELECT ...
FROM objects
WHERE id = :object_id
FOR NO KEY UPDATE;
```

prima di qualsiasi decision read.

Solo dopo il lock vengono letti:

```text
canonical_name
template_id
template_version
properties_json
```

La exact:

```text
objects(id)
```

row funge quindi da:

```text
Object state gate
```

per la mutation.

---

# 6. Perché `FOR NO KEY UPDATE`

`DATA_CHANGE` modifica:

```text
properties_json
```

ma non modifica:

```text
objects.id
```

né altre key referenziate.

`FOR NO KEY UPDATE` è quindi il lock minimo appropriato per serializzare le mutation del live Object state senza introdurre un lock più forte del necessario.

Il lock protegge:

```text
current-state read
template-pin read
candidate construction
candidate validation
before/after audit
```

---

# 7. DATA_CHANGE vs DATA_CHANGE con state gate

Con il protocollo:

```text
T1                           T2

FOR NO KEY UPDATE

                             FOR NO KEY UPDATE
                             WAIT

read P0
apply delta A
candidate P1
audit P0 -> P1
COMMIT

                             acquire
                             read P1
                             apply delta B
                             candidate P2
                             audit P1 -> P2
                             COMMIT
```

Il risultato conserva entrambe le mutation se semanticamente compatibili.

L'audit descrive transizioni realmente avvenute.

---

# 8. Gate comune del live Object state

L'analisi di `DATA_CHANGE` conferma il pattern emerso con `RENAME`.

Le operation:

```text
RENAME
DATA_CHANGE
SCHEMA_CHANGE
```

condividono la caratteristica di:

```text
1. leggere current Object state
2. derivare una candidate
3. persistere un nuovo live state
4. registrare canonical before/after audit
```

Per queste mutation il candidato gate comune è:

```text
SELECT exact objects(id) FOR NO KEY UPDATE
```

Questo documento ratifica il gate per `DATA_CHANGE`.

La sua applicazione a `SCHEMA_CHANGE` verrà rivalutata e ratificata nella relativa action.

---

# 9. Schema corrente usato per la validazione

Dopo il lock viene letto il pin realmente corrente:

```text
(template_id, template_version)
```

La candidate `properties_json` deve essere validata contro l'effective schema della exact ObjectTemplateVersion attualmente pinnata.

Non è ammesso validare la candidate contro un template pin letto prima dell'acquisizione dell'Object state gate.

---

# 10. DATA_CHANGE vs SCHEMA_CHANGE

Senza gate comune è possibile:

```text
T1 DATA_CHANGE               T2 SCHEMA_CHANGE

reads template = v2
                              reads template = v2

validates candidate on v2    migrates to v3
                              COMMIT

writes state derived from v2
```

con rischio di persistere dati validati contro uno schema non più corrente.

Se entrambe le operation acquisiscono:

```text
FOR NO KEY UPDATE objects(id)
```

gli ordini validi diventano soltanto:

## DATA_CHANGE prima

```text
v2 / P0
-> DATA_CHANGE
v2 / P1
-> SCHEMA_CHANGE
v3 / migrated(P1)
```

## SCHEMA_CHANGE prima

```text
v2 / P0
-> SCHEMA_CHANGE
v3 / P3
-> DATA_CHANGE
validate against v3
-> v3 / P4
```

Entrambi sono semanticamente corretti.

---

# 11. DATA_CHANGE vs RENAME

Con lo stesso state gate, anche `DATA_CHANGE` e `RENAME` vengono serializzati sul live Object state.

Ordine possibile:

```text
A / P0
-> DATA_CHANGE
A / P1
-> RENAME
B / P1
```

oppure:

```text
A / P0
-> RENAME
B / P0
-> DATA_CHANGE
B / P1
```

In entrambi i casi gli audit snapshot restano concatenabili e coerenti.

---

# 12. Lifecycle della current ObjectTemplateVersion

`DATA_CHANGE` non crea un nuovo template binding.

L'Object può essere pinnato a una OTV:

```text
PUBLISHED
```

oppure successivamente:

```text
DEPRECATED
```

e deve comunque poter modificare i propri runtime data.

Quindi non viene richiesto:

```text
status == PUBLISHED
```

sulla current exact OTV.

Non serve:

```text
FOR SHARE exact OTV
```

per un lifecycle admission predicate.

La FK dell'Object continua a garantirne l'esistenza.

---

# 13. Parent OTV e DataTypeVersion

Lo schema exact pinnato è storico e strutturalmente immutabile.

Le ancestor OTV e le exact DataTypeVersion già incorporate nello schema possono essere:

```text
PUBLISHED
DEPRECATED
```

e continuano a rappresentare correttamente lo schema certificato.

`DATA_CHANGE` non crea una nuova admission diretta verso di esse.

Quindi non sono richiesti:

```text
FOR SHARE ancestor OTV
FOR SHARE DTV
require DTV == PUBLISHED
```

---

# 14. Effective schema resolution

Dopo aver stabilizzato l'Object:

```text
1. read current exact OTV pin
2. resolve effective properties
3. build candidate data
4. validate complete candidate
```

La effective schema resolution comprende:

```text
local properties
+
inherited properties
```

secondo il modello ObjectTemplate ratificato.

Non serve uno structural gate sulla OTV perché una PUBLISHED/DEPRECATED exact OTV è strutturalmente immutabile.

---

# 15. Complete candidate validation

La validazione deve riguardare la candidate completa, non soltanto i campi esplicitamente modificati.

Regole:

```text
no unknown properties

every required property present

optional properties may be absent

every present value valid
against the exact DataTypeVersion
of the effective property
```

Questo vale anche quando la mutation include la rimozione di una property.

Esempi:

```text
remove optional property
    -> allowed

remove required property
    -> reject
```

---

# 16. `migration_default` non viene usato

`migration_default` appartiene esclusivamente alle schema migration.

Durante `DATA_CHANGE`:

```text
required property missing
```

produce:

```text
FAIL
```

Non viene applicato automaticamente alcun migration default.

---

# 17. No-op semantico

Dopo applicazione della mutation e normalizzazione della candidate:

```text
candidate properties == current properties
```

produce:

```text
no-op idempotente
```

con:

```text
nessun UPDATE
nessun DATA_CHANGE audit
```

La decisione deve avvenire dopo l'acquisizione dell'Object state gate.

La comparazione è semantica rispetto al contenuto JSONB persistito, non rispetto alla rappresentazione testuale originale.

---

# 18. Canonical before snapshot

Dopo il lock viene costruito il canonical current snapshot:

```json
{
  "canonical_name": "...",
  "template_id": "...",
  "template_version": 3,
  "properties": {
    "...": "old"
  }
}
```

Questo rappresenta lo stato effettivamente corrente prima della mutation.

---

# 19. Canonical after snapshot

L'after snapshot mantiene invariati:

```text
canonical_name
template_id
template_version
```

e sostituisce:

```text
properties
```

con la complete candidate validata.

---

# 20. Domain invariant di `DATA_CHANGE`

Un evento:

```text
kind = DATA_CHANGE
```

significa:

```text
before.canonical_name == after.canonical_name

before.template_id == after.template_id

before.template_version == after.template_version

before.properties != after.properties
```

Questa è una garanzia Domain/Application.

Non viene introdotto un CHECK DB che confronti semanticamente i canonical JSON snapshots.

---

# 21. `object_changes.canonical_name`

Per:

```text
DATA_CHANGE
```

la colonna:

```text
object_changes.canonical_name
```

deve contenere il canonical name corrente dell'Object.

Poiché DATA_CHANGE non rinomina:

```text
before.canonical_name
=
after.canonical_name
=
object_changes.canonical_name
```

---

# 22. DATA_CHANGE vs delete

Il live Object state gate fornisce la serializzazione naturale con una delete che stabilizzi la stessa row.

Se DATA_CHANGE vince:

```text
P0 -> P1
DATA_CHANGE audit
COMMIT

DELETE
```

la delete deve osservare:

```text
P1
```

come final current state.

Se delete vince:

```text
Object removed
-> DATA_CHANGE cannot proceed
```

Il protocollo della delete sarà ratificato separatamente.

---

# 23. DATA_CHANGE vs attach/detach

`DATA_CHANGE` non modifica:

```text
template_id
template_version
ownership
slot compatibility
ownership graph
```

Il canonical Object snapshot non contiene gli attachment.

Non esiste attualmente una business rule in cui la compatibilità di attachment dipenda dai runtime property values.

Quindi `DATA_CHANGE` non richiede:

```text
ownership graph lock
slot lock
parent/child attachment lock
```

e può restare indipendente da `attach/detach` quando i rispettivi protocolli lo consentono.

---

# 24. Perché non usare un CAS ottimistico

Una possibile alternativa sarebbe un conditional update basato sul vecchio stato.

Esempio concettuale:

```text
UPDATE ...
WHERE properties_json = old_properties
```

Ma l'operation deve comunque:

```text
read current template pin
resolve effective schema
construct complete candidate
validate candidate
construct canonical before snapshot
construct canonical after snapshot
```

Inoltre non esiste attualmente:

```text
object revision counter
```

da usare come token ottimistico.

Il row lock è quindi il meccanismo locale più semplice e coerente con la semantica dell'action.

---

# 25. Mutation + audit atomicity

La mutation e il relativo audit formano una singola unità semantica.

Non deve essere possibile committare:

```text
properties_json modificato
senza DATA_CHANGE audit
```

né:

```text
DATA_CHANGE audit
senza live mutation
```

Protocollo:

```text
BEGIN

lock Object
build candidate
validate candidate
UPDATE properties_json
INSERT object_changes DATA_CHANGE

COMMIT
```

Se l'audit insert fallisce:

```text
ROLLBACK
```

dell'intera mutation.

---

# 26. Protocollo transazionale candidato

```text
BEGIN

1. SELECT exact Object
   FOR NO KEY UPDATE

2. if Object missing:
       fail

3. read current:
   canonical_name
   template_id
   template_version
   properties_json

4. resolve effective schema
   of current exact OTV

5. apply requested data mutation
   to current properties

6. build complete candidate properties

7. validate complete candidate:
   - no unknown properties
   - all required present
   - optional may be absent
   - all values validate against exact DTV
   - migration_default is NOT used

8. if candidate == current:
       no-op
       no UPDATE
       no audit
       COMMIT / return unchanged

9. build canonical before snapshot

10. UPDATE objects
    SET properties_json = :candidate_jsonb
    WHERE id = :object_id

11. build canonical after snapshot

12. INSERT object_changes:
    kind           = DATA_CHANGE
    object_id      = Object id
    canonical_name = current canonical name
    before_json    = before snapshot
    after_json     = after snapshot

13. COMMIT
```

Qualsiasi failure produce:

```text
ROLLBACK
```

---

# 27. Lock non richiesti

`DATA_CHANGE` non richiede:

```text
FOR SHARE ObjectTemplateVersion
```

Non richiede:

```text
FOR SHARE DataTypeVersion
```

Non richiede:

```text
ObjectTemplate identity lock
```

Non richiede:

```text
ownership graph lock
```

Non richiede:

```text
parent/child attachment lock
```

L'unico lock applicativo esplicito richiesto è:

```text
FOR NO KEY UPDATE
sulla exact Object row
```

---

# 28. Separazione delle responsabilità

## Domain/Application

Garantisce:

```text
DATA_CHANGE changes only properties

candidate derives from current locked state

effective schema resolution

complete candidate validation

required properties remain present

migration_default not used

semantic no-op detection

canonical before/after snapshot semantics

DATA_CHANGE audit semantics
```

## PostgreSQL / relational model

Garantisce:

```text
Object identity
    -> PRIMARY KEY

current exact template pin existence
    -> composite FK

current exact template pin cannot dangle
    -> ON DELETE RESTRICT

runtime properties representation
    -> JSONB

Object row serialization
    -> row locking

audit structural consistency
    -> object_changes CHECK constraints

atomicity
    -> single PostgreSQL transaction
```

## Concurrency protocol

Garantisce:

```text
current-state read non-stale

DATA_CHANGE vs DATA_CHANGE serialization

DATA_CHANGE vs RENAME serialization

DATA_CHANGE vs SCHEMA_CHANGE serialization
when SCHEMA_CHANGE adopts the same state gate

candidate validated against the actually current template pin

coherent before/after audit
```

---

# 29. Verdetto DRAFT

> **DATA_CHANGE è una mutation locale del live Object state.**
>
> Prima di qualsiasi decision read deve acquisire:
>
> ```text
> FOR NO KEY UPDATE
> ```
>
> sulla exact `objects(id)` row.
>
> La candidate viene derivata dallo stato corrente bloccato e validata integralmente contro l'effective schema della exact ObjectTemplateVersion realmente pinnata in quel momento.
>
> Il lock protegge:
>
> ```text
> no lost mutation
> current template-pin correctness
> candidate validation correctness
> coherent before/after audit
> serialization with RENAME
> serialization with SCHEMA_CHANGE
> ```
>
> `DATA_CHANGE` non crea nuovi lifecycle binding e quindi non richiede `FOR SHARE` su ObjectTemplateVersion o DataTypeVersion.
>
> `migration_default` non viene usato.
>
> Una candidate semanticamente identica allo stato corrente è un no-op senza audit event.
>
> `UPDATE objects.properties_json` e `INSERT object_changes(DATA_CHANGE)` devono essere committati atomicamente nella stessa transazione.
>
> Nessun locking globale viene introdotto.
