# Object Create — Concurrency Contract DRAFT v1

## 1. Stato del documento

**DRAFT RATIFICATO come contratto corrente dell'action `create Object`**

Questo documento descrive congiuntamente:

```text
- semantica Domain/Application
- invarianti di admission
- garanzie relazionali PostgreSQL
- race concorrenti
- protocollo transazionale
- atomicità mutation + audit
```

Le responsabilità Domain/Application e DB sono mantenute in sezioni separate all'interno dello stesso documento per evitare divergenze tra due specifiche indipendenti.

Baseline di riferimento:

```text
Object — Modello Relazionale Ratificato v1
Object — Domain & Business Model Ratificato v1
ObjectTemplate — Modello Relazionale Ratificato v5
```

Nessun locking globale del model-plane o cross-plane viene introdotto.

---

# 2. Obiettivo dell'operazione

`create Object` crea atomicamente:

```text
objects row
+
object_changes CREATED
```

L'Object nasce:

```text
detached
```

e quindi la create non modifica:

```text
object_components
```

Un eventuale ownership attachment viene effettuato successivamente tramite l'action separata:

```text
attach Object
```

Un eventuale move è definito come:

```text
detach
+
attach
```

e non costituisce una action autonoma.

---

# 3. Candidate Object

La candidate finale contiene:

```text
id
canonical_name
template_id
template_version
properties_json
```

Il pin persistito verso ObjectTemplateVersion è sempre exact:

```text
(template_id, template_version)
```

anche quando il caller omette `template_version` nella request.

Non esiste quindi nel database un Object con semantica:

```text
"follow latest"
```

La modalità `latest PUBLISHED` esiste soltanto durante la risoluzione della create.

---

# 4. Object identity

`id` è l'identità autorevole dell'Object.

Collisioni concorrenti:

```text
T1 INSERT id = X
T2 INSERT id = X
```

sono risolte dalla:

```text
PRIMARY KEY(objects.id)
```

Non è necessario alcun lock preventivo.

Un eventuale pre-check applicativo può migliorare l'errore di dominio, ma la PK rimane l'autorità finale.

---

# 5. `canonical_name`

Semantica ratificata:

```text
canonical_name omitted / None
    -> canonical_name = str(Object.id)

canonical_name provided and non-empty
    -> use provided value

canonical_name == ""
    -> invalid
```

`canonical_name`:

```text
- non partecipa all'identità
- non è UNIQUE
- può essere uguale tra Object distinti
```

Non è richiesto alcun coordinamento concorrente durante la create.

La candidate audit deve usare il canonical name finale già risolto, incluso l'eventuale fallback a `str(id)`.

---

# 6. Due modalità di ObjectTemplateVersion resolution

La create può essere richiesta in due forme.

## 6.1 Exact pin esplicito

Input:

```text
template_id = T
template_version = V
```

Il caller richiede esattamente:

```text
ObjectTemplateVersion(T, V)
```

Non è ammesso alcun fallback verso versioni differenti.

## 6.2 Versione omessa

Input:

```text
template_id = T
template_version = omitted
```

Il dominio deve risolvere:

> la versione numericamente più alta tra tutte e sole le ObjectTemplateVersion `PUBLISHED` della lineage `T`.

Se non esiste alcuna versione `PUBLISHED`, la create deve fallire.

---

# 7. Exact pin esplicito — admission contract

Per una richiesta exact:

```text
(T, V)
```

la create deve acquisire:

```sql
SELECT ...
FROM object_template_versions
WHERE template_id = :template_id
  AND version = :template_version
FOR SHARE;
```

e verificare:

```text
row exists
status == PUBLISHED
```

Il lock viene mantenuto fino al commit.

Se la exact version richiesta è:

```text
missing
DRAFT
DEPRECATED
```

la create fallisce.

Non deve essere scelta silenziosamente un'altra versione.

---

# 8. Versione omessa — latest PUBLISHED resolution

Se `template_version` è omessa, la create deve selezionare la highest eligible version:

```sql
SELECT ...
FROM object_template_versions
WHERE template_id = :template_id
  AND status = 'PUBLISHED'
ORDER BY version DESC
LIMIT 1
FOR SHARE;
```

Semantica:

```text
nessuna PUBLISHED
    -> fail

una PUBLISHED
    -> select that version

più PUBLISHED
    -> select MAX(version) among PUBLISHED
```

Esempio:

```text
v1 PUBLISHED
v2 DEPRECATED
v3 PUBLISHED
v4 DRAFT
v5 DEPRECATED
```

risultato:

```text
selected = v3
```

---

# 9. Significato concorrente di "latest"

Non viene richiesto che la version selezionata sia ancora:

```text
highest PUBLISHED at COMMIT time
```

La semantica ratificata è:

> **highest PUBLISHED al momento della resolution/admission.**

La resolution della exact OTV costituisce il punto di linearizzazione della scelta.

Scenario:

```text
initial:
    v3 PUBLISHED
    v4 DRAFT

T1 create without version
T2 publish v4
```

Se T1 risolve prima:

```text
T1 selects v3
```

la create può validamente persistere:

```text
Object -> v3
```

anche se v4 diventa PUBLISHED prima del commit di T1.

L'ordine concorrente è semanticamente equivalente a:

```text
create admission
->
publish v4
```

Se invece v4 è già PUBLISHED quando avviene la resolution, la create deve scegliere v4.

Questo evita un lock di lineage aggiuntivo e mantiene il coordinamento locale.

---

# 10. Exact mode vs implicit latest mode

La distinzione è forte.

## Exact mode

```text
requested:
    T/v5

state:
    v5 DEPRECATED
    v4 PUBLISHED

result:
    FAIL
```

## Implicit latest mode

```text
requested:
    T + omitted version

state:
    v5 DEPRECATED
    v4 PUBLISHED

result:
    pin T/v4
```

La modalità implicit esprime una policy di resolution.

La modalità exact esprime una scelta vincolante del caller.

---

# 11. Race con deprecate della OTV selezionata

La OTV selezionata deve essere stabilizzata con:

```text
FOR SHARE
```

fino al commit.

Questo impedisce durante l'admission:

```text
PUBLISHED -> DEPRECATED
```

sulla row selezionata.

## Exact mode

Se il deprecate vince prima:

```text
exact requested OTV = DEPRECATED
-> create FAIL
```

## Implicit latest mode

La richiesta non è legata a una specifica version.

Se la candidate highest version perde eligibility prima dell'admission effettiva, la resolution deve produrre la highest version ancora `PUBLISHED`.

Concettualmente:

```text
resolve highest PUBLISHED
-> stabilize selected exact OTV FOR SHARE
-> use selected exact pin
```

Se nessuna PUBLISHED rimane:

```text
FAIL
```

---

# 12. Perché `FOR SHARE`

La create deve stabilizzare un predicato su una colonna non-key:

```text
status == PUBLISHED
```

Il deprecate modifica:

```text
status
```

senza modificare la key.

Per questo il lock appropriato è:

```text
FOR SHARE
```

e non semplicemente:

```text
FOR KEY SHARE
```

Il lock viene mantenuto fino al commit di:

```text
Object row
+
CREATED audit row
```

---

# 13. Persisted exact pin

Dopo la resolution, entrambe le modalità convergono sulla stessa rappresentazione:

```text
template_id = selected template_id
template_version = selected exact version
```

Entrambi i campi devono essere persistiti come valori concreti `NOT NULL`.

Non deve essere persistita alcuna informazione del tipo:

```text
latest
automatic
floating
```

La history dell'Object resta quindi deterministica.

---

# 14. DB authority sul pin

Lo schema relazionale garantisce:

```sql
FOREIGN KEY (template_id, template_version)
    REFERENCES object_template_versions(template_id, version)
    ON DELETE RESTRICT
```

La FK garantisce:

```text
- exact OTV exists
- persisted Object pin cannot become dangling
- referenced exact OTV cannot be deleted while Object exists
```

La FK NON garantisce:

```text
status == PUBLISHED
```

e NON può garantire:

```text
selected version == highest PUBLISHED
```

Questi sono predicati di admission Domain/Application protetti dal protocollo transazionale.

---

# 15. Race con delete ObjectTemplate / ObjectTemplateVersion

La OTV selezionata è stabilizzata durante l'admission.

Dopo l'INSERT Object, la FK `ON DELETE RESTRICT` protegge permanentemente il pin.

Possibili esiti:

```text
create wins
    -> Object persisted
    -> exact OTV becomes referenced
    -> later delete is RESTRICTED
```

oppure:

```text
delete wins before admission
    -> target OTV no longer exists
    -> create fails
```

Non può essere persistito un Object con dangling template pin.

Non serve un lock separato sulla `object_templates` identity.

---

# 16. Abstract ObjectTemplate

Se la semantica `abstract` è quella ratificata dal domain model ObjectTemplate, una lineage abstract non è direttamente istanziabile.

La create deve quindi richiedere:

```text
ObjectTemplate.abstract == FALSE
```

Questo è un predicato di dominio sulla template identity.

La modalità concreta di lettura deve essere coerente con la transazione, ma non viene introdotto un ulteriore lock dedicato fintanto che `abstract` appartiene al contratto stabile della lineage e non esiste una operation che lo muti concorrentemente.

---

# 17. Effective schema resolution

Una volta fissata la exact OTV, la create deve risolvere:

```text
effective properties
```

comprendendo:

```text
local properties
+
inherited properties
```

attraverso gli exact parent pin ratificati nel modello ObjectTemplate.

La target OTV `PUBLISHED` è strutturalmente immutabile.

Le ancestor OTV pinnate nello schema storico sono exact e strutturalmente immutabili una volta pubblicate/deprecate.

Le exact DataTypeVersion usate dalle properties non sono revisionabili dopo publication.

Non serve quindi uno structural gate per la effective schema resolution.

---

# 18. Parent OTV e DTV incorporate nello schema

`create Object` crea un nuovo binding diretto verso:

```text
selected exact ObjectTemplateVersion
```

Non crea binding lifecycle-sensitive diretti verso:

```text
ancestor ObjectTemplateVersion
exact DataTypeVersion
```

già incorporate nello schema PUBLISHED.

Di conseguenza non viene richiesto che queste dependency siano ancora:

```text
PUBLISHED
```

al momento della Object create.

Possono essere:

```text
PUBLISHED
DEPRECATED
```

purché continuino a esistere e appartengano allo schema certificato della exact OTV selezionata.

---

# 19. Nessun `FOR SHARE` sulle DTV incorporate

Esempio:

```text
Router/v3 = PUBLISHED

effective property:
    ip_address -> DT-IP/v4

DT-IP/v4 = DEPRECATED
```

`Router/v3` rimane uno schema storico certificato valido.

La create può usare:

```text
DT-IP/v4
```

per validare il valore runtime.

Non viene effettuata una nuova admission diretta verso `DT-IP/v4`.

Quindi:

```text
no FOR SHARE DTV
no require DTV == PUBLISHED
```

durante `create Object`.

L'esistenza della DTV è protetta dalle FK dello schema ObjectTemplate.

---

# 20. Validazione di `properties_json`

La candidate runtime data deve essere validata contro le effective properties della exact OTV selezionata.

## Unknown properties

```text
input property not in effective schema
    -> reject
```

## Required properties

Ogni effective property:

```text
required == TRUE
```

deve essere esplicitamente presente nella Object create.

## Optional properties

Una effective property:

```text
required == FALSE
```

può essere omessa.

## Value validation

Ogni valore presente deve validare contro:

```text
exact DataTypeVersion
    base_type
    constraints
```

della property effettiva.

---

# 21. `migration_default` non è un create-time default

Durante Object create:

```text
migration_default
```

non viene applicato automaticamente.

Se una property è:

```text
required == TRUE
```

ma manca dalla request:

```text
create FAIL
```

anche se lo schema contiene un:

```text
migration_default
```

Il migration default è metadata destinato alle schema migration.

Non è necessaria una sua rivalidazione durante Object create, perché non viene consumato dall'operazione.

---

# 22. Object nasce detached

`create Object` non crea alcuna row in:

```text
object_components
```

Non esegue:

```text
slot resolution
child compatibility validation
ownership cycle detection
attach
```

Queste responsabilità appartengono all'action separata:

```text
attach Object
```

---

# 23. Audit `CREATED`

Ogni create riuscita deve produrre:

```text
object_changes.kind = CREATED
```

con:

```text
before_json = NULL
after_json  = canonical full Object snapshot
```

La snapshot deve essere costruita dalla candidate finale già risolta e validata.

Shape:

```json
{
  "canonical_name": "...",
  "template_id": "...",
  "template_version": 3,
  "properties": {
    "...": "..."
  }
}
```

Se `canonical_name` è stato omesso, lo snapshot contiene:

```text
str(Object.id)
```

non un valore nullo o mancante.

---

# 24. `object_changes.canonical_name`

Per un evento:

```text
CREATED
```

la colonna deve contenere:

```text
final canonical_name
```

dell'Object appena creato.

Questo coincide con:

```text
after_json.canonical_name
```

secondo la canonical snapshot semantics.

---

# 25. Atomicità mutation + audit

La create e il relativo audit sono una singola unità semantica.

Non deve essere possibile committare:

```text
Object senza CREATED event
```

né:

```text
CREATED event senza Object
```

Protocollo:

```text
BEGIN
...
INSERT objects
INSERT object_changes CREATED
COMMIT
```

Se l'audit insert fallisce:

```text
ROLLBACK
```

dell'intera Object create.

L'audit non è best-effort logging: appartiene al contratto persistente dell'action.

---

# 26. Race create vs create con stesso Object id

La race:

```text
T1 INSERT Object id=X
T2 INSERT Object id=X
```

è risolta dalla PK.

Una sola transaction può riuscire.

Non è richiesto:

```text
SELECT-before-INSERT
row lock preventivo
identity gate
```

---

# 27. Lock non richiesti

`create Object` non richiede:

```text
FOR UPDATE sulla nuova Object
```

perché la row non esiste ancora.

Non richiede:

```text
Object ownership lock
```

perché nasce detached.

Non richiede:

```text
FOR SHARE sulle ancestor OTV
```

perché fanno parte dello schema storico immutabile della selected OTV.

Non richiede:

```text
FOR SHARE sulle DTV incorporate
```

perché non sono nuove admission dirette.

Non richiede:

```text
object_templates identity FOR UPDATE
```

perché non effettua version allocation o mutation della lineage.

---

# 28. Protocollo transazionale candidato

```text
BEGIN

1. generate/validate Object id

2. resolve canonical_name:
   omitted / None
       -> str(id)
   empty string
       -> reject

3. resolve exact target ObjectTemplateVersion

   IF template_version is explicitly supplied:

       SELECT exact OTV FOR SHARE

       require:
           exists
           status == PUBLISHED

   ELSE:

       SELECT highest PUBLISHED OTV
       for requested template_id
       ORDER BY version DESC
       LIMIT 1
       FOR SHARE

       require:
           at least one PUBLISHED version exists

       selected exact version =
           highest PUBLISHED at admission/resolution

4. exact target pin is now fixed

5. require:
   target ObjectTemplate is instantiable
   (`abstract == FALSE`, if applicable)

6. resolve effective schema
   of selected exact OTV

7. validate properties_json:
   - no unknown properties
   - all required explicitly present
   - optional may be absent
   - each provided value validates against exact DTV
   - migration_default is NOT used

8. build final Object candidate

9. build canonical CREATED after snapshot
   from final candidate

10. INSERT objects

11. INSERT object_changes:
    kind           = CREATED
    object_id      = new Object id
    canonical_name = final canonical_name
    before_json    = NULL
    after_json     = canonical snapshot

12. COMMIT
```

Qualsiasi failure produce:

```text
ROLLBACK
```

dell'intera operation.

---

# 29. Separazione delle responsabilità

## Domain/Application

Garantisce:

```text
canonical_name fallback

exact vs implicit-latest semantics

exact requested OTV must be PUBLISHED

implicit resolution must find at least one PUBLISHED OTV

implicit selected version =
    highest PUBLISHED at admission

abstract template not instantiable

effective schema resolution

runtime property validation

required properties explicitly present

migration_default not used as create-time default

canonical CREATED snapshot

mutation + audit semantics
```

## PostgreSQL / relational model

Garantisce:

```text
Object id uniqueness
    -> PRIMARY KEY

canonical_name non-empty
    -> CHECK

persisted exact OTV exists
    -> composite FK

exact OTV cannot be deleted while Object exists
    -> ON DELETE RESTRICT

properties_json representation
    -> JSONB

audit kind/nullability structural consistency
    -> object_changes CHECK constraints

transaction atomicity
    -> single PostgreSQL transaction
```

## Concurrency protocol

Garantisce:

```text
selected exact OTV remains PUBLISHED
through admission + commit
    -> FOR SHARE

exact latest resolution has a defined
linearization point
    -> highest PUBLISHED at resolution/admission

no dangling target
    -> row locking + FK authority
```

---

# 30. Verdetto DRAFT

> **Create Object è una operation multi-row atomica composta da `Object + CREATED audit`.**
>
> La request può specificare una exact ObjectTemplateVersion oppure omettere la versione.
>
> In exact mode, la exact requested version deve esistere ed essere `PUBLISHED`; nessun fallback è ammesso.
>
> In implicit mode, deve esistere almeno una version `PUBLISHED` e viene selezionata la version numericamente più alta tra quelle `PUBLISHED` al momento della resolution/admission.
>
> La selected exact OTV viene acquisita `FOR SHARE` e mantenuta stabile fino al commit.
>
> La semantica `latest` non viene persistita: ogni Object viene sempre salvato con un exact `(template_id, template_version)`.
>
> Parent OTV e DTV già incorporate nello schema PUBLISHED selezionato non richiedono nuova admission lifecycle e possono essere `DEPRECATED`.
>
> Le runtime properties vengono validate contro l'effective schema della selected exact OTV.
>
> Le required properties devono essere esplicitamente fornite; `migration_default` non è un create-time default.
>
> L'Object nasce detached.
>
> L'INSERT della row `objects` e del relativo `CREATED object_change` devono avvenire nella stessa transazione.
>
> Nessun locking globale viene introdotto.
