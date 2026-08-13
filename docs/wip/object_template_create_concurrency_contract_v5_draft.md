# ObjectTemplate Create — Concurrency Contract DRAFT v1

## 1. Stato del documento

**DRAFT**

Questo documento ratifica provvisoriamente l'analisi e il protocollo concorrente dell'operazione:

```text
create ObjectTemplate
```

sulla base del **modello relazionale ObjectTemplate v5 ratificato**.

Il documento non introduce alcun locking globale del model-plane o cross-plane.

---

# 2. Oggetto atomico della create

La `create ObjectTemplate` materializza atomicamente:

```text
ObjectTemplate identity
+
ObjectTemplateVersion v1 DRAFT
+
initial properties
+
initial components
```

In termini relazionali:

```text
object_templates

object_template_versions
    version = 1
    status = DRAFT

object_template_properties

object_template_components
```

L'intero aggregate deve essere persistito nella stessa transazione.

Non deve essere possibile osservare a commit avvenuto:

```text
identity senza v1
v1 senza struttura richiesta
properties/components parzialmente persistiti
```

---

# 3. Stato iniziale della nuova lineage

La prima versione deve nascere con:

```text
version = 1
status  = DRAFT
```

Non esiste alcuna allocation dinamica della versione.

La create non utilizza:

```text
MAX(version) + 1
```

e quindi non presenta la race di allocation propria della futura `create-next`.

La PK:

```text
PRIMARY KEY(template_id, version)
```

rimane l'autorità finale contro eventuali collisioni.

---

# 4. Collisioni dell'identità

L'identità stabile della lineage è protetta almeno da:

```text
PRIMARY KEY(object_templates.id)

UNIQUE(namespace, name)
```

Due create concorrenti possono tentare di usare:

```text
lo stesso id
```

oppure:

```text
lo stesso (namespace, name)
```

Non è richiesto alcun lock preventivo.

La soluzione minima è:

```text
INSERT concorrenti
    ->
PK / UNIQUE
    ->
una create vince
l'altra fallisce
```

La violation DB dovrebbe essere tradotta nell'errore di dominio appropriato.

---

# 5. Nessuno structural gate sulla nuova v1

Lo structural gate è la exact:

```text
object_template_versions(template_id, version)
```

acquisita `FOR NO KEY UPDATE` dalle operazioni che devono stabilizzare una DRAFT version già esistente.

Durante la create, la nuova:

```text
(template_id, 1)
```

non esiste ancora e non è visibile alle transazioni concorrenti prima del commit.

Non è quindi richiesto:

```text
FOR NO KEY UPDATE
```

sulla own v1.

Lo structural gate diventa rilevante soltanto dopo che la DRAFT version è stata creata e può essere oggetto di `revise` o `publish`.

---

# 6. Root lineage e child lineage

La candidate iniziale deve rispettare una delle due forme.

## Root lineage

```text
parent_template_id = NULL
parent_version     = NULL
```

## Child lineage

```text
parent_template_id != NULL
parent_version     != NULL
```

La FK composta con:

```text
MATCH FULL
```

costituisce la rete di sicurezza DB contro coppie parziali come:

```text
(NULL, 3)
('Parent', NULL)
```

L'application/domain layer deve comunque rigettare questi stati prima della persistenza.

---

# 7. Parent identity della lineage

Nella v1 viene scelto:

```text
parent_template_id
```

della nuova lineage.

Questo valore stabilisce il parent identity permanente della lineage.

Dopo la create:

```text
parent_template_id
```

è immutabile su UPDATE e tutte le versioni successive devono mantenere lo stesso valore.

La create è quindi l'unica operazione che sceglie liberamente il parent identity iniziale della lineage.

---

# 8. Exact parent pin

Se viene creata una child lineage:

```text
Child/v1 -> Parent/v5
```

la create introduce un nuovo binding verso la exact:

```text
ObjectTemplateVersion(Parent, 5)
```

La FK composta garantisce l'esistenza della exact parent version.

Non garantisce però:

```text
status == PUBLISHED
```

---

# 9. Admission rule del parent

Un nuovo parent binding può essere ammesso soltanto verso una exact ObjectTemplateVersion:

```text
PUBLISHED
```

La create è quindi un consumer lifecycle-sensitive della exact parent OTV.

Deve acquisire:

```sql
SELECT ...
FROM object_template_versions
WHERE template_id = :parent_template_id
  AND version = :parent_version
FOR SHARE;
```

e verificare:

```text
status == PUBLISHED
```

mantenendo il lock fino al commit.

---

# 10. Race con deprecate del parent

Senza stabilizzazione:

```text
T1 create Child               T2 deprecate Parent/v5

READ Parent/v5=PUBLISHED

                              PUBLISHED -> DEPRECATED
                              COMMIT

INSERT Child/v1 -> Parent/v5
COMMIT
```

Il nuovo binding sarebbe stato ammesso sulla base di un predicato stale.

Con `FOR SHARE`:

```text
create vince
    -> parent rimane PUBLISHED fino al commit
    -> il nuovo binding è ammesso correttamente
    -> deprecate può avvenire dopo

deprecate vince
    -> create vede DEPRECATED
    -> create fallisce
```

Questa è:

```text
admission-time consistency
```

Dopo il commit il parent può diventare `DEPRECATED` senza invalidare retroattivamente la child DRAFT.

Una futura `publish Child/v1` dovrà certificare nuovamente il parent.

---

# 11. Race con delete del parent

Il `FOR SHARE` sul parent protegge il predicato:

```text
status == PUBLISHED
```

La FK composta:

```text
(parent_template_id, parent_version)
    -> object_template_versions(template_id, version)
    ON DELETE RESTRICT
```

protegge invece:

```text
esistenza del parent binding
```

La race:

```text
create child vs delete parent
```

non può produrre un dangling reference.

Possibili esiti:

```text
create child vince
    -> exact parent viene referenziata
    -> delete parent fallisce

delete parent vince
    -> exact parent non esiste più
    -> create child non può persistere il binding
```

Non è richiesto un lock applicativo aggiuntivo per l'esistenza.

---

# 12. Candidate properties

La create riceve o costruisce il set completo delle properties iniziali.

Ogni property contiene almeno:

```text
position
name
datatype_id
datatype_version
required
migration_default
```

La candidate completa deve essere validata prima della persistenza.

Gli invarianti strutturali DB includono:

```text
PRIMARY KEY(template_id, template_version, name)

UNIQUE(template_id, template_version, position)

exact DataTypeVersion FK

required = TRUE
    -> migration_default SQL NOT NULL

migration_default
    -> non JSON null
```

---

# 13. Exact DataTypeVersion come dependency lifecycle-sensitive

Ogni property introduce un nuovo binding verso:

```text
(datatype_id, datatype_version)
```

La FK garantisce l'esistenza della exact DataTypeVersion.

Il contratto di dominio richiede inoltre che il binding venga creato soltanto mentre la DTV è:

```text
PUBLISHED
```

La create deve quindi:

```text
1. estrarre tutte le exact DTV dalle candidate properties
2. deduplicarle
3. ordinarle canonicamente
4. acquisire FOR SHARE
5. verificare status == PUBLISHED
6. mantenere i lock fino al commit
```

Chiave canonica:

```text
(datatype_id, datatype_version)
```

---

# 14. Race con deprecate di una DataTypeVersion

Senza stabilizzazione:

```text
T1 create OT                  T2 deprecate DTV-X/v3

READ DTV=PUBLISHED

                              UPDATE -> DEPRECATED
                              COMMIT

persist property pin
COMMIT
```

Con `FOR SHARE`:

```text
create vince
    -> DTV resta PUBLISHED fino al commit
    -> binding ammesso correttamente

deprecate vince
    -> create vede DEPRECATED
    -> create fallisce
```

La FK rimane l'autorità sull'esistenza.

---

# 15. `required` e `migration_default`

Per ogni candidate property vale:

```text
required == TRUE
    -> migration_default presente
```

Inoltre:

```text
migration_default presente
    -> deve validare contro la exact DTV pinnata
```

Il `migration_default` è metadata di migrazione.

Non è un default automatico per la normale `Object create`.

---

# 16. Validazione transazionale dei `migration_default`

Dopo aver acquisito le exact DTV `FOR SHARE`, la create dispone di:

```text
base_type
constraints
status
```

delle versioni effettivamente pinnate.

Ogni `migration_default` presente deve essere validato durante la stessa transazione:

```text
migration_default
    ->
validator della exact DataTypeVersion
    ->
valid / invalid
```

Se una validazione fallisce:

```text
ROLLBACK
```

dell'intera create.

---

# 17. Components

Ogni candidate component contiene:

```text
target_template_id
```

La FK:

```text
object_template_components.target_template_id
    -> object_templates.id
    ON DELETE RESTRICT
```

garantisce l'esistenza del target.

Non esiste un requisito lifecycle sul component target.

Non è quindi necessario un row lock esplicito sul target.

La race con un delete concorrente è affidata all'integrità referenziale PostgreSQL.

---

# 18. Vincolo di dominio: aciclicità del parent graph

Il parent graph degli ObjectTemplate deve essere aciclico.

Non sono ammessi:

```text
A -> A
```

né:

```text
A -> B
B -> A
```

né cicli più lunghi.

La proprietà riguarda:

```text
parent_template_id
```

ossia il parent identity stabile della lineage.

---

# 19. Self-parent

Il ciclo minimo:

```text
A -> A
```

deve essere vietato sia dal dominio sia dal DB.

Il modello relazionale v5 ratifica:

```sql
CHECK (
    parent_template_id IS NULL
    OR parent_template_id <> template_id
)
```

Quindi:

```text
root:
    parent_template_id = NULL
    -> ammesso

child:
    parent_template_id != template_id
    -> obbligatorio
```

---

# 20. Perché la normale create preserva l'aciclicità per costruzione

Una nuova lineage:

```text
NEW
```

non esiste nel grafo prima della create.

Se ha un parent, il parent deve essere una exact OTV:

```text
già esistente
+
PUBLISHED
```

Quindi la create aggiunge soltanto un arco:

```text
NEW -> EXISTING
```

Prima della create nessun nodo esistente può avere un parent path verso `NEW`, perché `NEW` non esiste.

Dopo la create, le lineage già esistenti non possono modificare:

```text
parent_template_id
```

per puntare retroattivamente a `NEW`, perché quel campo è immutabile.

Di conseguenza:

```text
fresh identity
+
existing parent
+
immutable parent identity
+
no self-parent
```

preserva l'aciclicità nel normale protocollo applicativo senza necessità di una traversal ricorsiva degli antenati durante la create.

---

# 21. Create concorrenti e ciclo reciproco

Scenario ipotetico:

```text
T1: create A -> B
T2: create B -> A
```

Non può essere ammesso dal protocollo normale.

Per scegliere `B` come parent, T1 deve trovare una exact:

```text
B/vN
```

già:

```text
PUBLISHED
```

e viceversa.

Ma una lineage appena creata nasce:

```text
v1 DRAFT
```

e non può quindi essere usata come parent durante una create concorrente prima di una futura publish.

Le due create non possono costruire reciprocamente il ciclo.

---

# 22. Limite dell'enforcement DB anti-ciclo

Il `CHECK`:

```text
parent_template_id != template_id
```

rende il database autoritativo contro il self-parent.

Non dimostra però da solo l'assenza di cicli arbitrari di lunghezza maggiore di uno in presenza di SQL fuori protocollo, bulk operation o futuri workflow non ancora analizzati.

Sono quindi distinti:

```text
normal domain/application protocol
    -> preserva aciclicità per costruzione

DB CHECK
    -> vieta autoritativamente self-parent

eventuale enforcement DB generale
    -> ancora da decidere
```

La normale `create` non richiede una recursive cycle query.

---

# 23. Atomicità della create

Qualsiasi errore deve annullare l'intera operazione.

Esempi:

```text
duplicate id

duplicate (namespace, name)

invalid parent pair

self-parent

parent missing

parent not PUBLISHED

DTV missing

DTV not PUBLISHED

invalid migration_default

duplicate property name

duplicate property position

invalid component target

qualsiasi FK/CHECK/UNIQUE violation
```

Esito richiesto:

```text
complete ObjectTemplate + v1 + structure
```

oppure:

```text
nothing
```

mai un aggregate parziale committato.

---

# 24. Protocollo transazionale candidato

```text
BEGIN

1. costruire la candidate completa:
   - ObjectTemplate identity
   - v1
   - exact parent pin opzionale
   - properties
   - components

2. validare invarianti locali:
   - version == 1
   - status == DRAFT
   - root => parent pair NULL/NULL
   - child => parent pair completa
   - parent_template_id != template_id
   - required/default presence
   - property names/positions
   - component names/positions
   - altri invarianti strutturali di dominio

3. se il parent è presente:
   acquisire FOR SHARE
   sulla exact parent OTV

4. verificare:
   parent.status == PUBLISHED

5. estrarre tutte le distinct exact DTV
   dalle candidate properties

6. ordinarle canonicamente:
   (datatype_id, datatype_version)

7. acquisire FOR SHARE
   su tutte le exact DTV

8. verificare per tutte:
   status == PUBLISHED

9. validare ogni migration_default presente
   contro la relativa exact DTV

10. INSERT object_templates

11. INSERT object_template_versions:
    version = 1
    status  = DRAFT

12. INSERT object_template_properties

13. INSERT object_template_components

14. lasciare a PK / UNIQUE / FK / CHECK
    l'autorità finale contro race e stati illegali

15. COMMIT
```

Se qualsiasi step fallisce:

```text
ROLLBACK
```

---

# 25. Nota sull'ordine degli INSERT e dei lock

La sequenza sopra rappresenta una forma candidata del protocollo, non una ratifica definitiva dell'ordine globale tra categorie di lock.

In particolare può essere ragionevole, in implementazione, tentare prima alcuni INSERT dell'identità per fallire presto su collisioni.

Questa scelta non deve però compromettere:

```text
atomicità
admission-time consistency
referential integrity
```

L'ordine globale tra:

```text
ObjectTemplateVersion locks
DataTypeVersion locks
identity-row interactions
```

rimane deliberatamente aperto finché non sarà completato il lock graph delle operazioni ObjectTemplate.

---

# 26. Separazione delle responsabilità

## Garantiti dal DB

```text
ObjectTemplate id uniqueness
    -> PRIMARY KEY

(namespace, name) uniqueness
    -> UNIQUE

v1 exact identity
    -> PRIMARY KEY(template_id, version)

parent pair NULL/non-NULL consistency
    -> MATCH FULL

self-parent forbidden
    -> CHECK

exact parent existence
    -> composite FK

exact DTV existence
    -> FK

component target existence
    -> FK

property name uniqueness
    -> PK

property position uniqueness
    -> UNIQUE

required => migration_default present
    -> CHECK

migration_default != JSON null
    -> CHECK
```

## Garantiti dal create protocol

```text
v1 starts as DRAFT
    -> domain/application

parent PUBLISHED at admission
    -> FOR SHARE exact parent OTV

DTV PUBLISHED at admission
    -> FOR SHARE exact DTVs

migration_default semantically valid
    -> validation nella stessa transaction

aggregate completeness
    -> single transaction

normal-workflow parent graph acyclic
    -> fresh identity
       + existing PUBLISHED parent
       + immutable parent identity
       + self-parent prohibition
```

---

# 27. Verdetto DRAFT

> **Create ObjectTemplate è una operazione multi-row atomica, ma non richiede uno structural gate sulla propria nuova v1.**
>
> La create materializza in una sola transazione:
>
> ```text
> ObjectTemplate identity
> + v1 DRAFT
> + initial properties
> + initial components
> ```
>
> Le collisioni della identity sono affidate a PK e UNIQUE.
>
> La v1 nasce deterministicamente con:
>
> ```text
> version = 1
> status  = DRAFT
> ```
>
> Un eventuale exact parent deve essere acquisito `FOR SHARE` e risultare `PUBLISHED`.
>
> Tutte le distinct exact DataTypeVersion referenziate dalle properties devono essere acquisite `FOR SHARE` e risultare `PUBLISHED`.
>
> Ogni `migration_default` presente deve essere validato nella stessa transazione contro la relativa exact DTV.
>
> I component target sono protetti dalle FK e non richiedono lifecycle lock.
>
> Il self-parent è vietato dal dominio e dal `CHECK` DB:
>
> ```text
> parent_template_id IS NULL
> OR parent_template_id <> template_id
> ```
>
> Nel normale workflow la create preserva l'aciclicità del parent graph per costruzione e non richiede una recursive ancestor traversal.
>
> L'eventuale enforcement PostgreSQL generale contro cicli arbitrari di lunghezza maggiore di uno rimane deliberatamente non deciso.
>
> Nessun locking globale viene introdotto.
