# ObjectTemplateVersion Publish — Concurrency Contract DRAFT v2

## 1. Stato del documento

**DRAFT**

Questo documento ratifica provvisoriamente l'analisi e l'ipotetico protocollo concorrente dell'operazione:

```text
publish ObjectTemplateVersion
```

sulla base esclusiva del **modello relazionale ObjectTemplate v3 ratificato**.

Non vengono assunte come valide le conclusioni dei draft precedenti se non quando sono nuovamente derivate da questo modello.

Il documento non introduce alcun locking globale del model-plane o cross-plane.

---

# 2. Modello relazionale rilevante

## 2.1 `object_template_versions`

```text
object_template_versions
------------------------
template_id
version
parent_template_id
parent_version
status

PRIMARY KEY(template_id, version)
```

Foreign key:

```sql
FOREIGN KEY (template_id)
    REFERENCES object_templates(id)
    ON DELETE CASCADE
```

Exact parent pin:

```sql
FOREIGN KEY (parent_template_id, parent_version)
    REFERENCES object_template_versions(template_id, version)
    MATCH FULL
    ON DELETE RESTRICT
```

Il database deve inoltre garantire tramite constraint trigger o meccanismo equivalente che:

```text
per tutte le versioni con lo stesso template_id
parent_template_id rimanga identico
```

con confronto NULL-safe.

Quindi:

```text
parent_template_id
    -> fisicamente version-specific
    -> semanticamente immutabile lungo la lineage

parent_version
    -> fisicamente e semanticamente version-specific
```

---

## 2.2 `object_template_properties`

```text
object_template_properties
--------------------------
template_id
template_version
position
name
datatype_id
datatype_version
required
migration_default
```

La property pinna una exact DataTypeVersion:

```sql
FOREIGN KEY (datatype_id, datatype_version)
    REFERENCES datatype_versions(datatype_id, version)
    ON DELETE RESTRICT
```

---

## 2.3 `object_template_components`

```text
object_template_components
--------------------------
template_id
template_version
position
name
target_template_id
```

Il target è protetto da:

```sql
FOREIGN KEY (target_template_id)
    REFERENCES object_templates(id)
    ON DELETE RESTRICT
```

---

# 3. Obiettivo della publish

La publish modifica la exact:

```text
ObjectTemplateVersion(template_id, version)
```

con transizione:

```text
DRAFT -> PUBLISHED
```

La modifica fisica dello status riguarda una sola row, ma la decisione di pubblicare dipende da un insieme di dati distribuiti:

```text
target ObjectTemplateVersion
exact parent ObjectTemplateVersion
properties
exact DataTypeVersions
migration_default
components
component targets
```

La publish deve quindi essere considerata una operazione critica multi-row.

---

# 4. Invarianti richiesti al momento della publish

## 4.1 Target version `DRAFT`

La exact target version deve essere:

```text
status == DRAFT
```

---

## 4.2 Parent identity invariata lungo la lineage

L'immutabilità di:

```text
parent_template_id
```

non deve essere verificata dalla publish.

È un invariante del modello relazionale e del dominio:

```text
tutte le versioni della stessa template lineage
devono avere lo stesso parent_template_id
```

La publish può quindi assumere che il `parent_template_id` persistito nella exact target version sia coerente con la lineage.

---

## 4.3 Exact parent pin esistente

Se il parent è presente:

```text
(parent_template_id, parent_version)
```

deve identificare una exact ObjectTemplateVersion esistente.

Questo è garantito dalla FK composta:

```text
MATCH FULL
ON DELETE RESTRICT
```

La FK garantisce però soltanto l'esistenza, non lo status lifecycle.

---

## 4.4 Exact parent version `PUBLISHED`

Se il parent è presente deve valere:

```text
exact parent ObjectTemplateVersion.status == PUBLISHED
```

Questo è un predicato di dominio e non è garantito dalla FK.

---

## 4.5 Tutte le exact DataTypeVersion delle properties `PUBLISHED`

Per ogni property della target version:

```text
(datatype_id, datatype_version)
```

deve identificare una exact DataTypeVersion con:

```text
status == PUBLISHED
```

La FK ne garantisce l'esistenza, non lo status.

---

## 4.6 `migration_default` semanticamente valido

Il DB garantisce gli invarianti strutturali:

```text
required = TRUE
    -> migration_default SQL NOT NULL

migration_default
    -> non JSON null
```

La publish deve inoltre certificare che ogni `migration_default` presente sia valido rispetto alla exact DataTypeVersion pinnata dalla property.

Questa è una validazione applicativa/domain-level.

---

## 4.7 Component target esistenti

Per ogni component:

```text
target_template_id
```

deve identificare una `object_templates.id` esistente.

Questo requisito è già garantito dalla FK:

```text
ON DELETE RESTRICT
```

Non è richiesto alcun lifecycle status del component target.

---

# 5. Race fondamentale: publish vs modifica della stessa DRAFT version

Scenario senza coordinamento:

```text
T1 publish                     T2 modifica DRAFT

READ status = DRAFT

READ properties A,B

                               INSERT property C
                               COMMIT

validate A,B

UPDATE status = PUBLISHED
COMMIT
```

Risultato:

```text
version PUBLISHED
+
property C mai validata dalla publish
```

Questa race non può essere risolta lockando soltanto le rows di property già esistenti, perché una transazione concorrente potrebbe inserire nuove rows.

Il problema riguarda quindi la stabilità dell'intera struttura della exact version.

---

# 6. Structural gate della exact ObjectTemplateVersion

La risorsa naturale che rappresenta l'intera struttura della exact version è:

```text
object_template_versions(template_id, version)
```

L'ipotetico protocollo ratificato prevede che la publish acquisisca:

```sql
SELECT ...
FROM object_template_versions
WHERE template_id = :template_id
  AND version = :version
FOR NO KEY UPDATE;
```

prima di qualsiasi lettura decisionale della struttura.

Dopo l'acquisizione deve effettuare nuovamente:

```text
verify status == DRAFT
```

La exact ObjectTemplateVersion diventa così lo **structural gate** della propria struttura.

---

# 7. Condizione necessaria perché lo structural gate funzioni

Il row lock sulla OTV non blocca materialmente un `INSERT`, `UPDATE` o `DELETE` sulle rows di:

```text
object_template_properties
object_template_components
```

Perché lo structural gate sia realmente efficace deve quindi esistere un protocollo condiviso:

> qualsiasi operazione che modifichi `parent_version`, properties o components di una DRAFT ObjectTemplateVersion deve acquisire preventivamente il lock sulla exact `object_template_versions(template_id, version)`.

Questa regola non viene assunta da vecchi draft: viene nuovamente derivata dalla necessità di impedire modifiche strutturali concorrenti durante la publish.

Senza questo protocollo sarebbe necessario ricorrere a meccanismi più pesanti, ad esempio predicate/range locking o isolation più forte con gestione dei serialization failure.

Lo structural gate è preferito perché rimane puntuale sulla singola exact version.

---

# 8. Race sul lifecycle del parent

Scenario:

```text
T1 publish Child/v2           T2 deprecate Parent/v4

READ Parent/v4=PUBLISHED

                               UPDATE -> DEPRECATED
                               COMMIT

PUBLISH Child/v2
```

La FK non impedisce questa race, perché il parent continua a esistere anche da `DEPRECATED`.

La publish deve quindi comportarsi come consumer della exact parent ObjectTemplateVersion.

Protocollo:

```sql
SELECT ...
FROM object_template_versions
WHERE template_id = :parent_template_id
  AND version = :parent_version
FOR SHARE;
```

poi:

```text
verify parent.status == PUBLISHED
```

mantenendo il lock fino al commit.

Esiti:

```text
publish child vince
    -> parent rimane PUBLISHED fino al commit
    -> il deprecate concorrente attende

deprecate parent vince
    -> publish vede DEPRECATED
    -> publish fallisce
```

---

# 9. Race sul lifecycle delle DataTypeVersion

Scenario:

```text
T1 publish OT                 T2 deprecate DTV-X/v3

READ DTV=PUBLISHED

                              UPDATE -> DEPRECATED
                              COMMIT

PUBLISH OT
```

Anche qui la FK garantisce soltanto l'esistenza.

Per tutte le distinct exact DataTypeVersion referenziate dalle properties la publish deve:

```text
1. estrarre (datatype_id, datatype_version)
2. deduplicare
3. ordinare secondo chiave canonica
4. acquisire FOR SHARE
5. verificare status == PUBLISHED
6. mantenere i lock fino al commit
```

Chiave canonica:

```text
(datatype_id, datatype_version)
```

---

# 10. Validazione dei `migration_default`

Dopo aver acquisito `FOR SHARE` sulle exact DataTypeVersion, la publish dispone dei relativi:

```text
status
base_type
constraints
```

Una DataTypeVersion `PUBLISHED` non è revisionabile nei suoi constraints.

La publish può quindi validare durante la stessa transazione:

```text
migration_default
    -> exact DataTypeVersion validator
```

Regola:

```text
required == TRUE
    -> migration_default presente

migration_default presente
    -> migration_default valido contro la exact DTV
```

Se una validazione fallisce, la publish deve fallire senza modificare lo status della target version.

---

# 11. Components

L'esistenza dei component target è già garantita da:

```text
object_template_components.target_template_id
    -> object_templates.id
    ON DELETE RESTRICT
```

Non è necessario acquisire row lock espliciti sui target per il solo requisito di esistenza.

La stabilità dell'insieme dei components durante la publish deriva invece dallo structural gate della target OTV e dal protocollo condiviso delle mutation DRAFT.

---

# 12. Publish concorrente della stessa exact version

Con lo structural gate:

```text
T1 publish                    T2 publish

FOR NO KEY UPDATE

                              FOR NO KEY UPDATE
                              -> WAIT

verify DRAFT
validate
UPDATE -> PUBLISHED
COMMIT

                              lock acquired
                              status == PUBLISHED
                              REJECT
```

Non è necessario un CAS separato sulla transizione finale perché il row lock e il re-check dello status serializzano la decisione.

---

# 13. Delete concorrente

Il delete dell'ObjectTemplate deve eliminare la exact OTV tramite cascade.

Se la publish possiede un row lock sulla OTV, il delete deve coordinarsi con quel lock.

Gli esiti sono serializzabili:

```text
publish completa
-> delete procede successivamente
```

oppure:

```text
delete elimina prima la lineage
-> publish non trova più la target version
```

Non è necessario un lock aggiuntivo specifico lato publish per questa race.

---

# 14. Ipotesi di protocollo transazionale

La sequenza candidata è:

```text
BEGIN

1. acquisire FOR NO KEY UPDATE
   sulla exact target ObjectTemplateVersion

2. re-read della target row

3. verificare:
   target.status == DRAFT

4. dalla row stabilizzata ricavare:
   parent_template_id
   parent_version

5. leggere persisted properties e components
   della target version

6. se il parent è presente:
   acquisire FOR SHARE
   sulla exact parent ObjectTemplateVersion

7. verificare:
   parent.status == PUBLISHED

8. estrarre dalle properties
   tutte le distinct exact DataTypeVersion

9. ordinarle secondo:
   (datatype_id, datatype_version)

10. acquisire FOR SHARE
    sulle exact DataTypeVersion

11. verificare per tutte:
    status == PUBLISHED

12. validare ogni migration_default presente
    contro la relativa exact DataTypeVersion

13. considerare l'esistenza dei component target
    garantita dalle FK

14. aggiornare target:
    DRAFT -> PUBLISHED

15. COMMIT
```

Se qualsiasi controllo fallisce:

```text
ROLLBACK
```

e la target version rimane `DRAFT`.

---

# 15. Ordine dei lock intra-categoria

Quando devono essere acquisiti più lock della stessa categoria:

```text
- deduplicare
- ordinare con chiave canonica
- acquisire in ordine lessicografico
```

Per le DataTypeVersion:

```text
(datatype_id, version)
```

Per eventuali set di ObjectTemplateVersion:

```text
(template_id, version)
```

Questa regola è già ratificabile localmente.

---

# 16. Lock ordering globale: ancora aperto

Non viene ancora ratificato un ordine globale tra categorie quali:

```text
ObjectTemplateVersion target
ObjectTemplateVersion parent
DataTypeVersion
```

La publish presenta una dipendenza naturale di scoperta:

```text
lock target OTV
    ->
leggere exact parent pin e structure
    ->
scoprire parent OTV e DTV
```

Inoltre esiste un potenziale problema di deadlock tra OTV differenti:

```text
T1 locks A
then wants B

T2 locks B
then wants A
```

La valutazione dell'ordine globale deve quindi essere rinviata fino a quando saranno stati chiariti:

```text
- eventuale invariante di aciclicità del parent graph
- protocollo delle altre operazioni ObjectTemplate
- grafo complessivo delle dipendenze di locking
```

Il presente draft ratifica quindi il protocollo locale della publish, ma non un ordine globale definitivo tra categorie.

---

# 17. Separazione delle responsabilità

La publish non deve proteggere invarianti già garantiti dal modello relazionale.

## Garantiti dal DB

```text
target OTV appartiene a un ObjectTemplate esistente
    -> FK

parent_template_id stabile lungo la lineage
    -> constraint trigger / equivalent

exact parent pin esistente
    -> composite FK MATCH FULL RESTRICT

exact DataTypeVersion esistente
    -> FK RESTRICT

component target esistente
    -> FK RESTRICT

required => migration_default presente
    -> CHECK

migration_default != JSON null
    -> CHECK
```

## Garantiti dal protocollo di publish

```text
target ancora DRAFT
    -> structural gate + re-check

structure stabile durante la validazione
    -> structural gate protocol

exact parent ancora PUBLISHED
    -> FOR SHARE

exact DataTypeVersion ancora PUBLISHED
    -> FOR SHARE

migration_default semanticamente valido
    -> domain validation nella stessa transaction
```

---

# 18. Verdetto DRAFT

> **Publish ObjectTemplateVersion è un'operazione critica multi-row.**
>
> La exact target ObjectTemplateVersion deve essere stabilizzata tramite `FOR NO KEY UPDATE` e funge da structural gate della specifica DRAFT version.
>
> Affinché questo gate sia efficace, qualsiasi mutation di `parent_version`, properties o components della stessa DRAFT version deve coordinarsi preventivamente sulla stessa exact OTV.
>
> Se è presente un parent, la exact parent ObjectTemplateVersion deve essere acquisita `FOR SHARE` e risultare `PUBLISHED`.
>
> Tutte le distinct exact DataTypeVersion referenziate dalle properties devono essere acquisite `FOR SHARE` e risultare `PUBLISHED`.
>
> Ogni `migration_default` presente deve essere validato durante la stessa transazione contro la relativa exact DataTypeVersion.
>
> L'esistenza dei component target è garantita dalle FK.
>
> Solo dopo la verifica e stabilizzazione di tutti questi invarianti può avvenire:
>
> ```text
> DRAFT -> PUBLISHED
> ```
>
> Nessun locking globale viene introdotto.
>
> **L'ordine globale tra categorie di lock rimane deliberatamente aperto** fino al completamento dell'analisi delle altre operazioni ObjectTemplate e del parent graph.
