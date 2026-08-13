# ObjectTemplateVersion Revise — Concurrency Contract DRAFT v2

## 1. Stato del documento

**DRAFT**

Questo documento ratifica provvisoriamente l'analisi e il protocollo concorrente dell'operazione:

```text
revise ObjectTemplateVersion
```

sulla base esclusiva del **modello relazionale ObjectTemplate v4 ratificato**.

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

Exact parent pin:

```sql
FOREIGN KEY (parent_template_id, parent_version)
    REFERENCES object_template_versions(template_id, version)
    MATCH FULL
    ON DELETE RESTRICT
```

Invariante forte sul parent identity:

```text
UPDATE:
    parent_template_id è immutabile

INSERT:
    ogni nuova version della stessa lineage
    deve mantenere lo stesso parent_template_id
```

Quindi:

```text
parent_template_id
    -> fisicamente memorizzato per version row
    -> semanticamente lineage-stable
    -> immutabile su UPDATE

parent_version
    -> realmente version-specific
    -> modificabile sulle versioni DRAFT
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

Ogni property pinna una exact DataTypeVersion:

```text
(datatype_id, datatype_version)
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

Ogni component punta a una ObjectTemplate identity esistente.

---

# 3. Obiettivo della revise

La revise modifica una exact:

```text
ObjectTemplateVersion(template_id, version)
```

mantenendo:

```text
status == DRAFT
```

Può modificare esclusivamente dati version-specific.

In particolare:

```text
object_template_versions.parent_version

object_template_properties
    - set delle properties
    - position
    - name
    - datatype_id
    - datatype_version
    - required
    - migration_default

object_template_components
    - set dei components
    - position
    - name
    - target_template_id
```

Non può modificare:

```text
parent_template_id
```

e non può modificare il contratto stabile della lineage contenuto in `object_templates`.

---

# 4. Precondizione fondamentale

La revise è ammessa soltanto se la exact target ObjectTemplateVersion è:

```text
status == DRAFT
```

Una versione `PUBLISHED` o `DEPRECATED` non può essere revisionata.

---

# 5. Race fondamentale: revise vs revise

Senza coordinamento:

```text
T1 revise                    T2 revise

READ DRAFT / S0              READ DRAFT / S0

produce S1                   produce S2

WRITE S1
COMMIT

                             WRITE S2
                             COMMIT
```

La modifica `S1` può essere persa silenziosamente.

PK, FK e CHECK non impediscono questa race.

Serve quindi serializzare le mutation della struttura della **stessa exact version**.

---

# 6. Race fondamentale: revise vs publish

Senza coordinamento:

```text
T1 revise                    T2 publish

READ DRAFT

                             READ DRAFT
                             READ structure
                             validate

modify structure
COMMIT

                             status -> PUBLISHED
                             COMMIT
```

La publish potrebbe certificare una struttura diversa da quella effettivamente persistita.

La revise e la publish devono quindi coordinarsi sulla stessa exact ObjectTemplateVersion.

---

# 7. Structural gate della exact ObjectTemplateVersion

La revise deve acquisire:

```sql
SELECT ...
FROM object_template_versions
WHERE template_id = :template_id
  AND version = :version
FOR NO KEY UPDATE;
```

prima di qualsiasi lettura decisionale della struttura.

Dopo il lock deve effettuare:

```text
verify status == DRAFT
```

La exact:

```text
object_template_versions(template_id, version)
```

diventa lo **structural gate** della propria struttura DRAFT.

---

# 8. Protocollo condiviso dello structural gate

Il lock sulla row `object_template_versions` non blocca materialmente gli `INSERT`, `UPDATE` o `DELETE` sulle child rows:

```text
object_template_properties
object_template_components
```

Affinché lo structural gate stabilizzi realmente l'intera struttura, vale il protocollo:

> qualsiasi operazione che modifichi `parent_version`, properties o components di una DRAFT ObjectTemplateVersion deve acquisire preventivamente `FOR NO KEY UPDATE` sulla exact OTV.

Questo protocollo è necessario per impedire:

```text
lost update
revise/publish race
phantom structural changes
```

senza ricorrere a locking più globale o a isolation più pesante.

---

# 9. `parent_template_id` non è revisionabile

Il modello v4 stabilisce che:

```text
parent_template_id
```

è immutabile su ogni `UPDATE`.

La revise deve quindi rifiutare qualsiasi tentativo di cambio:

```text
ParentA -> ParentB
```

a livello di dominio.

Il DB costituisce comunque la rete di sicurezza finale.

Il fatto che `parent_template_id` sia fisicamente memorizzato nella version row non gli conferisce semantica versionabile.

---

# 10. `parent_version` è revisionabile

La revise può modificare:

```text
parent_version
```

mantenendo invariato:

```text
parent_template_id
```

Esempio ammesso:

```text
Child/v3

prima:
    ParentA/v2

dopo revise:
    ParentA/v5
```

La exact candidate parent diventa:

```text
(parent_template_id, candidate_parent_version)
```

La FK composta ne garantisce l'esistenza.

Non garantisce però:

```text
status == PUBLISHED
```

---

# 11. Parent exact version come dependency lifecycle-sensitive

La revise è un consumer della exact candidate parent ObjectTemplateVersion.

Deve acquisire:

```sql
SELECT ...
FROM object_template_versions
WHERE template_id = :parent_template_id
  AND version = :candidate_parent_version
FOR SHARE;
```

e verificare:

```text
status == PUBLISHED
```

mantenendo il lock fino al commit.

---

# 12. Race con deprecate del parent

Senza lock:

```text
T1 revise Child/v3            T2 deprecate ParentA/v5

READ ParentA/v5=PUBLISHED

                               UPDATE -> DEPRECATED
                               COMMIT

persist parent_version=5
COMMIT
```

Il nuovo binding sarebbe stato ammesso sulla base di un predicato ormai falso.

Con `FOR SHARE`:

```text
T1 FOR SHARE ParentA/v5

T2 deprecate
    -> WAIT

T1 verify PUBLISHED
   persist
   COMMIT

T2 può deprecare
```

Oppure:

```text
deprecate vince
-> revise vede DEPRECATED
-> revise fallisce
```

Dopo il commit della revise il parent può essere deprecato.

Poiché la child rimane `DRAFT`, una futura publish dovrà nuovamente certificare che il parent sia ancora `PUBLISHED`.

Quindi:

```text
revise
    -> admission-time consistency

publish
    -> certification-time consistency
```

---

# 13. Candidate structure

Dopo aver acquisito lo structural gate, la revise legge:

```text
current parent_version
current properties
current components
```

e costruisce:

```text
current structure
+
requested changes
=
candidate structure
```

La validazione deve riguardare la **candidate structure completa**, non soltanto i singoli delta.

---

# 14. Properties e exact DataTypeVersion

Dalla candidate structure devono essere estratte tutte le exact:

```text
(datatype_id, datatype_version)
```

referenziate dalle properties risultanti.

Per ogni nuovo binding verso una DataTypeVersion vale il contratto:

```text
exact DTV deve essere PUBLISHED
al momento dell'admission
```

La revise deve quindi:

```text
1. estrarre le exact DTV
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

# 15. Race con deprecate di una DataTypeVersion

Senza lock:

```text
T1 revise OT                  T2 deprecate DTV-X/v3

READ DTV=PUBLISHED

                              UPDATE -> DEPRECATED
                              COMMIT

persist property pin
COMMIT
```

Con `FOR SHARE`:

```text
revise vince
    -> DTV rimane PUBLISHED fino al commit
    -> deprecate attende

deprecate vince
    -> revise vede DEPRECATED
    -> revise fallisce
```

---

# 16. `required` e `migration_default`

Per ogni property della candidate structure vale:

```text
required == TRUE
    -> migration_default presente
```

Il DB protegge:

```text
required = TRUE
    -> migration_default SQL NOT NULL

migration_default
    -> non JSON null
```

La revise deve inoltre garantire la validità semantica del valore.

---

# 17. Validazione transazionale dei `migration_default`

Dopo aver acquisito `FOR SHARE` sulle exact DataTypeVersion, la revise dispone dei relativi:

```text
status
base_type
constraints
```

Ogni `migration_default` presente può quindi essere validato nella stessa transazione:

```text
migration_default
    -> exact DataTypeVersion validator
```

Regola:

```text
if required == TRUE:
    migration_default MUST be present

if migration_default is present:
    migration_default MUST validate
    against the exact DTV
```

La validazione avviene nell'application/domain layer mentre la transazione è ancora aperta.

---

# 18. Deduplicazione delle DataTypeVersion

Se la candidate structure contiene:

```text
property A -> DT-X/v3
property B -> DT-X/v3
property C -> DT-Y/v2
property D -> DT-X/v3
```

la revise acquisisce soltanto:

```text
DT-X/v3
DT-Y/v2
```

e usa le DTV caricate per validare tutte le relative properties e i relativi `migration_default`.

---

# 19. Components

Per ogni candidate component:

```text
target_template_id
```

deve identificare una ObjectTemplate identity esistente.

Questo è garantito dalla FK:

```text
object_template_components.target_template_id
    -> object_templates.id
    ON DELETE RESTRICT
```

Non è richiesto alcun lifecycle status del target.

Non serve quindi un row lock esplicito sul component target.

La stabilità dell'insieme dei components è garantita dallo structural gate della own OTV e dal protocollo condiviso delle mutation DRAFT.

---

# 20. Delete concorrente

La revise possiede:

```text
FOR NO KEY UPDATE
```

sulla exact OTV.

Un delete della lineage deve eliminare quella stessa row tramite cascade e deve quindi coordinarsi con il row lock.

Gli esiti risultano serializzati:

```text
revise completa
-> delete procede successivamente
```

oppure:

```text
delete elimina prima la lineage
-> revise non può completare
```

Non è richiesto alcun lock aggiuntivo sulla `object_templates` identity.

---

# 21. Deprecate della target version

La revise richiede:

```text
status == DRAFT
```

La deprecate richiede:

```text
status == PUBLISHED
```

I predicati sono mutuamente esclusivi.

Lo structural gate più il re-check di:

```text
status == DRAFT
```

è sufficiente.

---

# 22. Protocollo transazionale candidato

```text
BEGIN

1. acquisire FOR NO KEY UPDATE
   sulla exact target OTV

2. re-read della target row

3. verificare:
   target.status == DRAFT

4. verificare:
   parent_template_id non modificabile

5. leggere:
   current parent_version
   current properties
   current components

6. applicare la requested revision

7. costruire la candidate structure completa

8. validare gli invarianti locali:
   - parent_template_id invariato
   - required/migration_default presence
   - names / positions
   - altri invarianti strutturali

9. se la candidate ha parent:
   acquisire FOR SHARE
   sulla exact candidate parent OTV

10. verificare:
    parent.status == PUBLISHED

11. estrarre tutte le distinct exact DTV
    dalle candidate properties

12. ordinarle canonicamente:
    (datatype_id, datatype_version)

13. acquisire FOR SHARE
    su tutte le exact DTV

14. verificare per tutte:
    status == PUBLISHED

15. validare ogni migration_default presente
    contro la relativa exact DTV

16. considerare l'esistenza dei component target
    garantita dalle FK

17. persistere atomicamente la candidate structure:
    - parent_version
    - properties
    - components

18. mantenere:
    status == DRAFT

19. COMMIT
```

Se qualsiasi controllo fallisce:

```text
ROLLBACK
```

e la target version rimane invariata.

---

# 23. Separazione delle responsabilità

## Garantiti dal DB

```text
parent_template_id immutable on UPDATE
    -> constraint trigger / equivalent

same parent_template_id on later version INSERT
    -> constraint trigger / equivalent

exact parent existence
    -> composite FK MATCH FULL RESTRICT

exact DTV existence
    -> FK RESTRICT

component target existence
    -> FK RESTRICT

required => migration_default present
    -> CHECK

migration_default != JSON null
    -> CHECK
```

## Garantiti dal protocollo di revise

```text
target ancora DRAFT
    -> structural gate + re-check

no lost update
    -> structural gate

no revise/publish race
    -> structural gate

candidate parent ancora PUBLISHED
    -> FOR SHARE parent OTV

candidate DTV ancora PUBLISHED
    -> FOR SHARE exact DTVs

migration_default semanticamente valido
    -> validation nella stessa transaction
```

---

# 24. Lock ordering intra-categoria

Quando la revise deve acquisire più lock della stessa categoria:

```text
- deduplicare
- ordinare secondo chiave canonica
- acquisire in ordine lessicografico
```

Chiavi canoniche:

```text
ObjectTemplateVersion:
    (template_id, version)

DataTypeVersion:
    (datatype_id, version)
```

Questa regola è ratificabile localmente.

---

# 25. Lock ordering globale ancora aperto

La sequenza naturale di scoperta della revise è:

```text
own OTV
    ->
candidate parent OTV
    ->
exact DataTypeVersions
```

Questa sequenza non viene ancora elevata a regola globale per tutte le operazioni.

L'ordine globale tra categorie di lock verrà ratificato soltanto dopo aver completato l'analisi delle altre operazioni ObjectTemplate e del grafo delle dipendenze.

---

# 26. Verdetto DRAFT

> **Revise ObjectTemplateVersion è una operazione critica multi-row.**
>
> La exact target ObjectTemplateVersion deve essere acquisita `FOR NO KEY UPDATE` prima di qualsiasi lettura decisionale e costituisce lo structural gate della specifica versione DRAFT.
>
> `parent_template_id` è semanticamente e fisicamente immutabile su UPDATE; la revise può modificare soltanto `parent_version`.
>
> La exact candidate parent ObjectTemplateVersion, se presente, deve essere acquisita `FOR SHARE` e risultare `PUBLISHED`.
>
> Tutte le distinct exact DataTypeVersion della candidate structure devono essere acquisite `FOR SHARE` e risultare `PUBLISHED`.
>
> Ogni `migration_default` presente deve essere validato nella stessa transazione contro la relativa exact DataTypeVersion.
>
> I component target sono protetti dalle FK.
>
> La candidate structure viene persistita atomicamente e la target version rimane `DRAFT`.
>
> Nessun locking globale viene introdotto.
>
> L'ordine globale tra categorie di lock rimane deliberatamente aperto.
