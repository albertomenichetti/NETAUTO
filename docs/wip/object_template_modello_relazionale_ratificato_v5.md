# ObjectTemplate — Modello Relazionale Ratificato

## 1. Stato del documento

**RATIFICATO**

Questo documento definisce il modello relazionale target di `ObjectTemplate` da usare come baseline per:

- implementazione dello schema PostgreSQL;
- repository e Unit of Work;
- invarianti di dominio;
- analisi delle operazioni concorrenti;
- successive ADR e migration.

Il modello qui descritto è autoritativo per l'analisi architetturale anche se non è ancora completamente implementato nel codice corrente.

---

# 2. Principio strutturale generale

Il modello è composto da quattro tabelle:

```text
object_templates
object_template_versions
object_template_properties
object_template_components
```

La separazione concettuale è:

```text
object_templates
    -> identità stabile della lineage

object_template_versions
    -> stato e struttura version-specific

object_template_properties
    -> properties della specifica version

object_template_components
    -> components della specifica version
```

Una parte importante del contratto di dominio riguarda l'ereditarietà:

```text
parent_template_id
    -> semanticamente immutabile lungo tutta la lineage

parent_version
    -> version-specific e modificabile tra versioni successive
```

Questa distinzione è fondamentale per comprendere perché entrambi i campi vengono memorizzati in `object_template_versions`.

---

# 3. Valutazioni che hanno portato al modello definitivo

## 3.1 Prima ipotesi: parent completamente version-specific

Il modello iniziale prevedeva:

```text
object_template_versions
    parent_template_id
    parent_version
```

Questa forma rappresentava naturalmente l'exact parent pin:

```text
(parent_template_id, parent_version)
```

ma lasciava aperta una questione di dominio:

> se entrambe le colonne sono version-specific, cosa impedisce a una nuova ObjectTemplateVersion di cambiare completamente parent lineage?

Esempio non ammesso dal contratto:

```text
Child/v1 -> ParentA/v2
Child/v2 -> ParentB/v3
```

Il dominio richiede invece che il parent logico rimanga stabile.

---

## 3.2 Seconda ipotesi: spostare parent identity sulla lineage

Per esprimere direttamente l'immutabilità del parent logico si è quindi valutato di spostare:

```text
parent_template_id
```

in:

```text
object_templates
```

lasciando:

```text
parent_version
```

in:

```text
object_template_versions
```

La semantica risultava molto naturale:

```text
object_templates.parent_template_id
    -> parent identity stabile

object_template_versions.parent_version
    -> exact parent version evolutiva
```

Questa soluzione però introduceva un problema relazionale.

La FK necessaria per proteggere l'exact parent pin è:

```text
(parent_template_id, parent_version)
    -> object_template_versions(template_id, version)
```

ma le due colonne sorgenti si sarebbero trovate in tabelle differenti.

PostgreSQL non può esprimere una foreign key composta usando colonne provenienti da due righe/tabelle sorgenti differenti.

---

## 3.3 Terza ipotesi: duplicare `parent_template_id`

Si è quindi valutato di mantenere:

```text
object_templates.parent_template_id
```

come valore autoritativo della lineage e duplicarlo anche in:

```text
object_template_versions.parent_template_id
```

come copia relazionale derivata, così da rendere possibile la FK composta:

```text
(parent_template_id, parent_version)
    -> object_template_versions(template_id, version)
```

Questa soluzione richiedeva però un ulteriore meccanismo per garantire:

```text
object_template_versions.parent_template_id
==
object_templates.parent_template_id
```

Si è valutata una FK composta verso:

```text
object_templates(id, parent_template_id)
```

ma la presenza di root template con parent `NULL` rendeva la combinazione con `MATCH FULL` scomoda e innaturale.

La soluzione avrebbe quindi richiesto una duplicazione intenzionale del dato più un ulteriore constraint trigger o meccanismo equivalente per mantenerlo coerente.

Il modello risultava formalmente corretto, ma più complesso del necessario:

```text
un parent_template_id autoritativo
+
una copia derivata
+
vincolo di sincronizzazione cross-table
+
FK exact parent
```

---

## 3.4 Decisione finale: exact parent pin nella version row

Si è quindi deciso di tornare a:

```text
object_template_versions
    parent_template_id
    parent_version
```

Questa forma rappresenta naturalmente il pin verso una exact parent version e consente una FK composta diretta.

La decisione NON modifica il contratto di dominio.

Il fatto che:

```text
parent_template_id
```

sia fisicamente memorizzato in `object_template_versions` non significa che sia semanticamente modificabile.

La regola definitiva è:

> tutte le versioni appartenenti alla stessa ObjectTemplate lineage devono avere lo stesso `parent_template_id`.

È consentito:

```text
Child/v1 -> ParentA/v2
Child/v2 -> ParentA/v3
Child/v3 -> ParentA/v5
```

Non è consentito:

```text
Child/v1 -> ParentA/v2
Child/v2 -> ParentB/v1
```

Quindi:

```text
parent_template_id
    -> stored per version
    -> domain-immutable across lineage

parent_version
    -> stored per version
    -> evolvable across lineage
```

Questa scelta mantiene il modello relazionale semplice senza rinunciare all'invariante di dominio.

---

# 4. `object_templates`

La tabella rappresenta l'identità stabile dell'ObjectTemplate lineage.

```text
object_templates
----------------
id              TEXT/UUID   PRIMARY KEY
namespace       TEXT        NOT NULL
name            TEXT        NOT NULL
description     TEXT        ...
abstract        BOOLEAN     NOT NULL

UNIQUE(namespace, name)
```

## 4.1 Semantica

Gli attributi presenti in questa tabella appartengono al contratto stabile della lineage.

In particolare:

```text
id
namespace
name
description
abstract
```

non sono version-specific.

L'ereditarietà non è materializzata qui perché il pin exact parent è rappresentato nella singola ObjectTemplateVersion.

---

# 5. `object_template_versions`

La tabella rappresenta la specifica versione della lineage.

```text
object_template_versions
------------------------
template_id          TEXT/UUID   NOT NULL
version              INTEGER     NOT NULL
parent_template_id   TEXT/UUID   NULL
parent_version       INTEGER     NULL
status               TEXT        NOT NULL

PRIMARY KEY(template_id, version)
```

## 5.1 Ownership della version

```sql
FOREIGN KEY (template_id)
    REFERENCES object_templates(id)
    ON DELETE CASCADE
```

Una ObjectTemplateVersion appartiene alla propria ObjectTemplate identity.

---

## 5.2 Exact parent pin

La coppia:

```text
(parent_template_id, parent_version)
```

identifica la exact parent ObjectTemplateVersion.

La FK è:

```sql
FOREIGN KEY (parent_template_id, parent_version)
    REFERENCES object_template_versions(template_id, version)
    MATCH FULL
    ON DELETE RESTRICT
```

`MATCH FULL` impone che siano validi soltanto:

```text
(NULL, NULL)
(non-NULL, non-NULL)
```

e rende invalide coppie parzialmente `NULL`.

Questo sostituisce il precedente `CHECK` del tipo:

```text
entrambi NULL
oppure
entrambi NOT NULL
```

con una semantica referenziale più completa.

---

# 6. Invariante forte sul parent identity

Anche se:

```text
parent_template_id
```

è fisicamente memorizzato in ogni riga di `object_template_versions`, esso è **semanticamente immutabile lungo tutta la lineage**.

Per un dato:

```text
template_id = X
```

deve valere contemporaneamente che:

1. tutte le versioni della lineage hanno lo stesso `parent_template_id`;
2. il `parent_template_id` di una versione già esistente non può mai essere modificato tramite `UPDATE`.

La semantica del confronto deve essere NULL-safe:

```text
IS NOT DISTINCT FROM
IS DISTINCT FROM
```

così da trattare correttamente anche le lineage root con:

```text
parent_template_id = NULL
```

## 6.1 Perché il solo vincolo cross-row non è sufficiente

Una formulazione del tipo:

```text
tutte le versioni con lo stesso template_id
devono avere lo stesso parent_template_id
```

non è sufficiente da sola.

Esempio:

```text
esiste soltanto:

Child/v1
parent_template_id = ParentA
```

Un update diretto:

```sql
UPDATE object_template_versions
SET parent_template_id = 'ParentB'
WHERE template_id = 'Child'
  AND version = 1;
```

potrebbe non trovare nessun'altra versione della stessa lineage con cui confrontare il nuovo valore.

Se il vincolo DB controllasse soltanto la coerenza con le *altre* versioni esistenti, il cambio:

```text
ParentA -> ParentB
```

potrebbe quindi sfuggire proprio quando la lineage contiene una sola versione.

Il contratto corretto deve perciò distinguere esplicitamente `UPDATE` e `INSERT`.

## 6.2 Regola DB su UPDATE

Per ogni riga già esistente di `object_template_versions`:

```text
parent_template_id
```

è immutabile.

Deve essere sempre vietato:

```text
NEW.parent_template_id
IS DISTINCT FROM
OLD.parent_template_id
```

Concettualmente:

```text
on UPDATE object_template_versions:

require:
    NEW.parent_template_id
    IS NOT DISTINCT FROM
    OLD.parent_template_id
```

Questa regola vale anche se la riga aggiornata è l'unica versione esistente della lineage.

Quindi:

```text
UPDATE parent_template_id
    -> sempre vietato
```

mentre:

```text
UPDATE parent_version
    -> ammesso se l'operazione di dominio lo consente
```

e se tutti gli altri invarianti risultano soddisfatti.

## 6.3 Regola DB su INSERT

La prima versione della lineage stabilisce il parent identity.

Concettualmente:

```text
Child/v1.parent_template_id
    -> definisce il parent logico della lineage Child
```

Per ogni nuova versione successiva con lo stesso `template_id` deve valere:

```text
NEW.parent_template_id
IS NOT DISTINCT FROM
existing_lineage_parent_template_id
```

Quindi sono ammessi:

```text
Child/v1 -> ParentA/v2
Child/v2 -> ParentA/v3
Child/v3 -> ParentA/v5
```

mentre deve essere rifiutato:

```text
Child/v1 -> ParentA/v2
Child/v2 -> ParentB/v1
```

Per una root lineage vale analogamente:

```text
Child/v1.parent_template_id = NULL
```

e tutte le versioni successive devono mantenere:

```text
parent_template_id = NULL
```

## 6.4 Ruolo del dominio

Le operazioni applicative devono rispettare esplicitamente lo stesso contratto:

```text
create ObjectTemplate
    -> sceglie parent_template_id nella v1
    -> quel valore stabilisce il parent identity della lineage

create-next version
    -> copia obbligatoriamente lo stesso parent_template_id
    -> può scegliere una nuova parent_version

revise version
    -> può cambiare parent_version
    -> NON può cambiare parent_template_id

publish/deprecate
    -> non modificano parent_template_id
```

Il fatto che `parent_template_id` sia presente in una tabella versionata non gli conferisce semantica versionabile.

## 6.5 Autorità finale DB

L'invariante non deve dipendere soltanto dal corretto comportamento dell'application/domain layer.

È ratificata l'intenzione di introdurre una protezione PostgreSQL tramite constraint trigger o meccanismo equivalente con **due responsabilità distinte**:

### A. Immutabilità su UPDATE

```text
OLD.parent_template_id
IS NOT DISTINCT FROM
NEW.parent_template_id
```

deve essere sempre vera.

### B. Coerenza di lineage su INSERT

Se esistono già versioni con lo stesso `template_id`:

```text
NEW.parent_template_id
IS NOT DISTINCT FROM
parent_template_id già stabilito dalla lineage
```

deve essere vera.

Pseudocodice concettuale:

```text
on UPDATE object_template_versions:
    reject if
        NEW.parent_template_id
        IS DISTINCT FROM
        OLD.parent_template_id

on INSERT object_template_versions:
    if another version with same template_id exists:
        reject if
            NEW.parent_template_id
            IS DISTINCT FROM
            existing.parent_template_id
```

Il database costituisce la rete di sicurezza finale; il dominio deve comunque impedire semanticamente gli stessi stati illegali.

## 6.6 Invariante risultante

La regola completa è quindi:

```text
parent_template_id
    -> scelto una sola volta quando nasce la lineage
    -> copiato identico in tutte le versioni successive
    -> mai modificabile su una versione già esistente

parent_version
    -> può evolvere tra versioni della stessa lineage
    -> può essere modificata sulle versioni DRAFT secondo il contratto di dominio
```

Questo evita sia:

```text
cambio di parent tra versioni
```

sia:

```text
riscrittura retroattiva del parent della prima/unica versione
```

---

# 6.7 Divieto di self-parent

L'aciclicità del parent graph è un vincolo di dominio.

Un caso minimo e sempre illegale è il self-parent:

```text
A -> A
```

Questo stato deve essere vietato anche direttamente dal modello relazionale.

È quindi ratificato il seguente `CHECK` sulla tabella `object_template_versions`:

```sql
CHECK (
    parent_template_id IS NULL
    OR parent_template_id <> template_id
)
```

Il vincolo significa:

```text
root lineage:
    parent_template_id = NULL
    -> ammesso

child lineage:
    parent_template_id != template_id
    -> obbligatorio
```

Questo `CHECK` non pretende, da solo, di dimostrare l'aciclicità generale del grafo per cicli di lunghezza maggiore di uno.

Protegge però in modo autoritativo il ciclo minimo:

```text
A -> A
```

L'aciclicità generale rimane un invariante di dominio da preservare attraverso i protocolli delle operazioni che introducono parent dependencies.

Nel normale workflow `create ObjectTemplate`, l'aciclicità generale è preservata per costruzione perché:

```text
1. la nuova lineage non esiste prima della create
2. il parent deve già esistere
3. l'exact parent version deve essere PUBLISHED
4. parent_template_id diventa immutabile dopo la nascita della lineage
5. self-parent è vietato dal CHECK
```

Di conseguenza una create normale aggiunge soltanto un arco:

```text
NEW -> EXISTING
```

e non può chiudere un ciclo attraverso un nodo `NEW` che prima della transazione non esisteva.

La scelta di introdurre anche un enforcement PostgreSQL generale contro cicli arbitrari di lunghezza > 1 resta separata e non viene anticipata in questa baseline.

# 7. `parent_version` è invece evolutiva

A differenza del parent identity:

```text
parent_version
```

appartiene realmente alla singola ObjectTemplateVersion.

Può quindi evolvere:

```text
Child/v1 -> ParentA/v2
Child/v2 -> ParentA/v3
Child/v3 -> ParentA/v5
```

Questo permette alla child lineage di seguire l'evoluzione del proprio parent senza cambiare parent logico.

La specifica parent version scelta deve comunque soddisfare gli invarianti lifecycle richiesti dalle operazioni di dominio.

In particolare, per i workflow già analizzati:

```text
create
revise
publish
```

l'exact parent version consumata deve essere `PUBLISHED` al momento dell'admission/certification previsto dal relativo concurrency contract.

La FK garantisce l'esistenza dell'exact parent version; lo status `PUBLISHED` rimane un predicato di dominio.

---

# 8. `object_template_properties`

La tabella contiene le properties della specifica ObjectTemplateVersion.

```text
object_template_properties
--------------------------
template_id         TEXT/UUID   NOT NULL
template_version    INTEGER     NOT NULL
position            INTEGER     NOT NULL
name                TEXT        NOT NULL
datatype_id         TEXT/UUID   NOT NULL
datatype_version    INTEGER     NOT NULL
required            BOOLEAN     NOT NULL
migration_default   JSONB       NULL

PRIMARY KEY(template_id, template_version, name)

UNIQUE(template_id, template_version, position)
```

## 8.1 Ownership

```sql
FOREIGN KEY (template_id, template_version)
    REFERENCES object_template_versions(template_id, version)
    ON DELETE CASCADE
```

La property appartiene alla specifica ObjectTemplateVersion.

---

## 8.2 DataTypeVersion pin

```sql
FOREIGN KEY (datatype_id, datatype_version)
    REFERENCES datatype_versions(datatype_id, version)
    ON DELETE RESTRICT
```

La property pinna una exact DataTypeVersion.

La FK garantisce l'esistenza della versione, non lo status lifecycle.

---

## 8.3 `migration_default`

`migration_default` è metadata di migrazione.

Non è un default utilizzabile durante il normale `Object create`.

Quando presente deve essere valido secondo la exact:

```text
(datatype_id, datatype_version)
```

pinnata dalla property.

La validazione è un invariante di dominio/applicativo.

---

## 8.4 Required property

È ratificato:

```text
required = TRUE
    => migration_default IS NOT NULL
```

Vincolo:

```sql
CHECK (
    required = FALSE
    OR migration_default IS NOT NULL
)
```

Questo non obbliga a eseguire una migrazione.

Garantisce però che una property obbligatoria disponga sempre del valore necessario a rendere possibile un futuro repinning/migration di Object che non possiedono ancora quella property.

---

## 8.5 SQL NULL e JSON null

SQL `NULL` significa:

```text
assenza di migration_default
```

JSON `null` non è un valore di dominio valido.

Vincolo:

```sql
CHECK (
    migration_default IS NULL
    OR migration_default <> 'null'::jsonb
)
```

Quindi per:

```text
required = TRUE
```

deve esistere un valore concreto:

```text
migration_default != SQL NULL
migration_default != JSON null
```

---

# 9. `object_template_components`

La tabella contiene i components della specifica ObjectTemplateVersion.

```text
object_template_components
--------------------------
template_id          TEXT/UUID   NOT NULL
template_version     INTEGER     NOT NULL
position             INTEGER     NOT NULL
name                 TEXT        NOT NULL
target_template_id   TEXT/UUID   NOT NULL

PRIMARY KEY(template_id, template_version, name)

UNIQUE(template_id, template_version, position)
```

## 9.1 Ownership

```sql
FOREIGN KEY (template_id, template_version)
    REFERENCES object_template_versions(template_id, version)
    ON DELETE CASCADE
```

---

## 9.2 Target ObjectTemplate

```sql
FOREIGN KEY (target_template_id)
    REFERENCES object_templates(id)
    ON DELETE RESTRICT
```

Il component punta alla ObjectTemplate identity, non a una specifica version.

Quindi:

```text
property
    -> exact DataTypeVersion pin

component
    -> ObjectTemplate identity reference
```

---

# 10. Modello complessivo ratificato

```text
object_templates
----------------
id                         PK
namespace
name
description
abstract

UNIQUE(namespace, name)


object_template_versions
------------------------
template_id
version
parent_template_id         NULL
parent_version             NULL
status

PK(template_id, version)

FK(template_id)
    -> object_templates.id
    ON DELETE CASCADE

FK(parent_template_id, parent_version)
    -> object_template_versions(template_id, version)
    MATCH FULL
    ON DELETE RESTRICT

CHECK (
    parent_template_id IS NULL
    OR parent_template_id <> template_id
)

CONSTRAINT TRIGGER / equivalent:

    UPDATE:
        parent_template_id is immutable
        NEW.parent_template_id
        IS NOT DISTINCT FROM
        OLD.parent_template_id

    INSERT:
        if the lineage already exists,
        NEW.parent_template_id must equal
        the lineage parent_template_id
        using NULL-safe comparison


object_template_properties
--------------------------
template_id
template_version
position
name
datatype_id
datatype_version
required
migration_default          JSONB NULL

PK(template_id, template_version, name)

UNIQUE(template_id, template_version, position)

FK(template_id, template_version)
    -> object_template_versions(template_id, version)
    ON DELETE CASCADE

FK(datatype_id, datatype_version)
    -> datatype_versions(datatype_id, version)
    ON DELETE RESTRICT

CHECK (
    required = FALSE
    OR migration_default IS NOT NULL
)

CHECK (
    migration_default IS NULL
    OR migration_default <> 'null'::jsonb
)


object_template_components
--------------------------
template_id
template_version
position
name
target_template_id

PK(template_id, template_version, name)

UNIQUE(template_id, template_version, position)

FK(template_id, template_version)
    -> object_template_versions(template_id, version)
    ON DELETE CASCADE

FK(target_template_id)
    -> object_templates.id
    ON DELETE RESTRICT
```

---

# 11. Ownership e dependencies

Il principio generale resta:

```text
ownership interno
    -> ON DELETE CASCADE

riferimenti esterni
    -> ON DELETE RESTRICT
```

Ownership interna:

```text
object_templates
    -> object_template_versions
    -> properties
    -> components
```

Dependencies esterne:

```text
exact parent pins
component targets
DataTypeVersion pins
Object pins verso ObjectTemplateVersion
```

---

# 12. Conseguenze sulle operazioni

La decisione finale sul parent rende le operazioni più semplici.

Quando una operazione acquisisce il row lock sulla exact:

```text
object_template_versions(template_id, version)
```

stabilizza sulla stessa row:

```text
status
parent_template_id
parent_version
```

Questo è particolarmente utile per:

```text
publish
revise
```

che possono quindi:

```text
lock own OTV
-> leggere exact parent pin
-> acquisire FOR SHARE sul parent
-> validarne PUBLISHED
```

senza attraversare `object_templates` per ricostruire il pin.

---

# 13. Regola definitiva sul parent

La semantica deve essere considerata esplicitamente parte del contratto di dominio:

```text
parent_template_id
    -> fisicamente memorizzato per version row
    -> semanticamente lineage-stable
    -> scelto dalla prima versione
    -> identico su tutte le versioni successive
    -> immutabile su ogni UPDATE

parent_version
    -> fisicamente version-specific
    -> semanticamente version-specific
    -> modificabile nelle successive versioni DRAFT
```

In altre parole:

> il parent logico non cambia mai; evolve soltanto la versione del parent a cui una specifica ObjectTemplateVersion è pinnata.

Questa regola deve essere rispettata sia dall'application/domain layer sia dal database tramite un vincolo cross-row dedicato.

---

# 14. Decisione architetturale finale

Il ritorno di:

```text
parent_template_id
parent_version
```

nella tabella `object_template_versions` non rappresenta un ritorno alla semantica originale non vincolata.

È una decisione di modellazione relazionale volta a:

- rappresentare naturalmente l'exact parent pin;
- utilizzare una FK composta standard;
- evitare duplicazione cross-table di `parent_template_id`;
- evitare meccanismi di sincronizzazione fra valore autoritativo e copia derivata;
- mantenere semplice il locking delle operazioni su una exact ObjectTemplateVersion.

L'immutabilità del parent identity rimane un requisito forte e viene resa esplicita tramite:

```text
domain invariant
+
database constraint trigger / equivalent
```

Il modello consente quindi contemporaneamente:

```text
parent identity stabile
+
parent version evolutiva
+
exact parent referential integrity
+
schema relazionale semplice
```

Questo costituisce il modello relazionale `ObjectTemplate` ratificato.


---

## Addendum v5 — self-parent e aciclicità

Rispetto alla v4, questa versione ratifica inoltre:

```text
parent_template_id != template_id
```

quando il parent è presente, tramite `CHECK` DB.

Il parent graph degli ObjectTemplate è considerato **aciclico per vincolo di dominio**.

Il `CHECK` anti-self-parent è autoritativo per i cicli di lunghezza 1; l'enforcement DB generale dell'aciclicità per cicli più lunghi resta deliberatamente non deciso.
