# ObjectTemplateVersion Create-Next — Concurrency Contract DRAFT v1

## 1. Stato del documento

**DRAFT**

Questo documento ratifica provvisoriamente l'analisi e il protocollo concorrente dell'operazione:

```text
create-next ObjectTemplateVersion
```

sulla base del **modello relazionale ObjectTemplate v5 ratificato**.

Il documento non introduce alcun locking globale del model-plane o cross-plane.

---

# 2. Obiettivo dell'operazione

La `create-next ObjectTemplateVersion` crea una nuova exact version all'interno di una lineage esistente.

La nuova versione:

```text
- appartiene allo stesso template_id
- riceve un nuovo numero di versione
- nasce DRAFT
- clona esattamente lo snapshot persistito della source
```

La semantica ratificata è quindi:

```text
create-next
    =
exact clone della source
+
new DRAFT version
```

Non vengono applicate modifiche strutturali durante `create-next`.

Qualsiasi cambiamento successivo deve avvenire tramite:

```text
revise ObjectTemplateVersion
```

---

# 3. Source exact e non latest implicita

La create-next riceve una source exact:

```text
(template_id, source_version)
```

La source non deve essere necessariamente:

```text
MAX(version)
```

Sono quindi ammesse operazioni come:

```text
v1 PUBLISHED
v2 PUBLISHED
v3 DEPRECATED

create-next(source=v1)
    ->
v4 DRAFT clone esatto di v1
```

Version allocation e source selection sono due concetti distinti:

```text
new version number
    = MAX(existing versions) + 1

new version content
    = exact persisted source snapshot
```

---

# 4. Source lifecycle ammesso

La source deve essere:

```text
PUBLISHED
```

oppure:

```text
DEPRECATED
```

Non è ammessa una source:

```text
DRAFT
```

La ragione di dominio è che una DRAFT version è già modificabile tramite `revise`.

Consentire `create-next` da DRAFT introdurrebbe una semantica di branching di workspace che non appartiene al modello corrente.

---

# 5. Perché `DEPRECATED` è una source valida

Una lineage può trovarsi in uno stato in cui tutte le versioni esistenti sono `DEPRECATED`.

Deve comunque essere possibile evolvere la lineage.

Esempio:

```text
v1 DEPRECATED
    ->
create-next
    ->
v2 DRAFT
```

Inoltre la transizione:

```text
PUBLISHED -> DEPRECATED
```

non modifica la struttura della versione.

Quindi `PUBLISHED` e `DEPRECATED` sono entrambe source strutturalmente immutabili e valide per il clone.

---

# 6. Snapshot clonato

La nuova version deve copiare esattamente dalla source:

```text
parent_template_id
parent_version
```

tutte le rows locali di:

```text
object_template_properties
```

con:

```text
position
name
datatype_id
datatype_version
required
migration_default
```

e tutte le rows locali di:

```text
object_template_components
```

con:

```text
position
name
target_template_id
```

Non vengono materializzate o ri-risolte strutture ereditate dal parent.

La create-next clona le rows persistite locali della source.

---

# 7. Nessuna modifica in-line

Durante `create-next` non è ammesso modificare:

```text
parent_template_id
parent_version

properties

datatype bindings

required

migration_default

components
```

Il risultato immediato della create-next deve essere un clone strutturale esatto della source, salvo:

```text
version
status
```

che diventano:

```text
version = new_version
status  = DRAFT
```

Qualsiasi modifica deve avvenire successivamente tramite `revise`.

---

# 8. Esempio: cambio `required`

Se la source contiene:

```text
property X
required = FALSE
migration_default = NULL
```

la create-next deve produrre:

```text
new DRAFT
property X
required = FALSE
migration_default = NULL
```

Se la nuova versione deve invece avere:

```text
required = TRUE
```

la sequenza corretta è:

```text
create-next
    ->
exact clone DRAFT

revise
    ->
required FALSE -> TRUE
    +
migration_default valido
```

Analogamente:

```text
required TRUE -> FALSE
```

è una modifica di `revise`, non di `create-next`.

---

# 9. Problema concorrente principale: allocazione di `MAX(version)+1`

Supponiamo che esistano:

```text
v1
v2
v3
```

Due transazioni concorrenti:

```text
T1 create-next                 T2 create-next

MAX(version)=3                 MAX(version)=3

next=4                         next=4

INSERT v4                      INSERT v4
```

La PK:

```text
PRIMARY KEY(template_id, version)
```

impedirebbe la corruzione, ma una delle due operazioni semanticamente valide fallirebbe.

Se la semantica desiderata è:

```text
due create-next concorrenti
    ->
v4
v5
```

l'allocation deve essere serializzata per lineage.

---

# 10. Stable lineage identity come allocation gate

La risorsa stabile della lineage è:

```text
object_templates.id
```

La create-next deve acquisire:

```sql
SELECT id
FROM object_templates
WHERE id = :template_id
FOR UPDATE;
```

prima di calcolare il prossimo numero di versione.

Solo dopo il lock:

```text
MAX(version)
```

può essere letto e trasformato in:

```text
new_version = MAX(version) + 1
```

---

# 11. Due create-next concorrenti

Con l'identity-row lock:

```text
T1                            T2

FOR UPDATE OT-X

                              FOR UPDATE OT-X
                              WAIT

MAX=3
INSERT v4
COMMIT

                              acquire
                              MAX=4
                              INSERT v5
                              COMMIT
```

Risultato:

```text
v4 DRAFT
v5 DRAFT
```

Lineage diverse restano indipendenti:

```text
create-next A
create-next B
```

non si bloccano tra loro.

---

# 12. Multiple DRAFT versions

Il modello corrente non stabilisce:

```text
at most one DRAFT per lineage
```

Quindi due create-next valide e serializzate possono produrre:

```text
v4 DRAFT
v5 DRAFT
```

anche dalla stessa source.

Esempio:

```text
create-next(source=v3)
create-next(source=v3)
```

può produrre:

```text
v4 DRAFT clone of v3
v5 DRAFT clone of v3
```

Se in futuro si volesse introdurre il vincolo:

```text
at most one DRAFT per lineage
```

sarebbe un nuovo invariante di dominio da ratificare separatamente.

---

# 13. Identity lock e delete concorrente

La create-next acquisisce:

```text
FOR UPDATE
```

sulla stable:

```text
object_templates.id
```

La delete della lineage deve eliminare quella stessa identity.

Quindi le due operazioni si coordinano naturalmente.

Possibili ordini:

```text
create-next vince
    -> nuova version viene inserita
    -> COMMIT
    -> delete può poi eliminare identity + versions via CASCADE
```

oppure:

```text
delete vince
    -> identity viene eliminata
    -> create-next non trova più la lineage
```

Non può risultare una ObjectTemplateVersion orfana.

---

# 14. Lettura della source

Dopo aver acquisito la stable lineage identity, la create-next legge la exact source:

```text
object_template_versions(
    template_id,
    source_version
)
```

e verifica:

```text
source exists
```

e:

```text
source.status IN (
    PUBLISHED,
    DEPRECATED
)
```

Non è necessario acquisire uno structural gate sulla source.

---

# 15. Perché non serve structural gate sulla source

Una source:

```text
PUBLISHED
```

non può più essere revisionata strutturalmente.

Può soltanto diventare:

```text
DEPRECATED
```

Una source:

```text
DEPRECATED
```

è terminale.

Quindi entrambe sono strutturalmente immutabili.

Il clone può leggere in sicurezza:

```text
parent pin
properties
components
```

senza `FOR NO KEY UPDATE` sulla source.

---

# 16. Create-next vs publish(source)

Se la source è inizialmente `DRAFT`:

```text
T1 create-next                 T2 publish source

READ source = DRAFT
REJECT

                               DRAFT -> PUBLISHED
                               COMMIT
```

Questo è corretto.

Se la publish committa prima della lettura della source:

```text
source = PUBLISHED
```

la create-next può procedere.

Non è richiesto un coordinamento aggiuntivo.

---

# 17. Create-next vs deprecate(source)

La source può essere sia:

```text
PUBLISHED
```

sia:

```text
DEPRECATED
```

Quindi la race:

```text
create-next
vs
PUBLISHED -> DEPRECATED
```

non invalida l'operazione.

Possibili osservazioni:

```text
create-next legge PUBLISHED
```

oppure:

```text
create-next legge DEPRECATED
```

sono entrambe valide.

Non è necessario:

```text
FOR SHARE
```

sulla source per stabilizzarne il lifecycle status.

---

# 18. Nessuna nuova admission dei parent binding

La source contiene già:

```text
(parent_template_id, parent_version)
```

La create-next copia esattamente entrambi.

Non sta scegliendo un nuovo exact parent.

Quindi non applica il normale admission protocol:

```text
FOR SHARE exact parent OTV
verify PUBLISHED
```

durante il clone.

Un parent può nel frattempo essere diventato:

```text
DEPRECATED
```

e la nuova DRAFT deve comunque poter essere creata.

Una successiva `revise` potrà cambiare `parent_version` verso una exact parent PUBLISHED.

La futura `publish` dovrà nuovamente certificare che l'exact parent della candidate finale sia `PUBLISHED`.

---

# 19. Parent existence

La source OTV referenzia già l'exact parent tramite:

```text
FOREIGN KEY(parent_template_id, parent_version)
    -> object_template_versions(template_id, version)
    ON DELETE RESTRICT
```

Finché la source esiste, l'exact parent non può essere eliminato lasciando dangling reference.

La nuova OTV crea un secondo binding verso lo stesso exact parent.

La referential integrity DB rimane l'autorità finale sull'esistenza.

---

# 20. Nessuna nuova admission delle DataTypeVersion

Le source properties contengono già exact DTV pins:

```text
(datatype_id, datatype_version)
```

La create-next li copia esattamente.

Non sceglie nuove DataTypeVersion.

Quindi non richiede:

```text
FOR SHARE exact DTV
verify PUBLISHED
```

durante il clone.

Una DTV già correttamente bindata nella source può essere nel frattempo diventata:

```text
DEPRECATED
```

e questo non deve impedire la creazione della nuova DRAFT.

---

# 21. Perché i binding deprecated devono poter essere clonati

Scenario:

```text
source v3
property X -> DT/v7

DT/v7 -> DEPRECATED
```

La create-next deve poter produrre:

```text
v4 DRAFT
property X -> DT/v7
```

così che una successiva:

```text
revise v4
```

possa cambiare:

```text
DT/v7 -> DT/v8 PUBLISHED
```

Se `create-next` richiedesse che tutti i binding clonati fossero ancora PUBLISHED, potrebbe diventare impossibile evolvere una lineage storica che dipende da versioni ormai deprecated.

---

# 22. `migration_default`

Il `migration_default` viene copiato esattamente dalla source.

Se la source è `PUBLISHED` o `DEPRECATED`, il suo snapshot strutturale era già stato certificato.

La exact DTV referenziata non può essere revisionata strutturalmente dopo publication.

Quindi non è necessaria una nuova validazione semantica del `migration_default` durante create-next.

Una futura `revise` dovrà invece rivalidare la candidate se modifica:

```text
required
migration_default
datatype_id
datatype_version
```

La futura `publish` certificherà nuovamente la struttura finale.

---

# 23. Components

I components vengono clonati esattamente dalla source:

```text
position
name
target_template_id
```

Il target esiste grazie alla FK:

```text
object_template_components.target_template_id
    -> object_templates.id
    ON DELETE RESTRICT
```

La source component stessa protegge già il target dall'eliminazione mentre viene clonata.

La nuova component row aggiunge un ulteriore reference.

Non è necessario un row lock esplicito sul target.

---

# 24. Parent identity e modello v5

La nuova version deve copiare esattamente:

```text
source.parent_template_id
```

Non è un input modificabile di `create-next`.

Il modello v5 garantisce inoltre:

```text
INSERT di nuova version:
    parent_template_id deve essere identico
    a quello già stabilito dalla lineage
```

e:

```text
parent_template_id != template_id
```

quando il parent è presente.

Il DB rimane quindi l'autorità finale contro bug applicativi.

---

# 25. Parent version

Anche:

```text
parent_version
```

viene copiata esattamente dalla source.

Esempio:

```text
source:
Child/v3 -> ParentA/v5
```

produce:

```text
new:
Child/v4 DRAFT -> ParentA/v5
```

Se si vuole aggiornare il parent pin:

```text
ParentA/v5 -> ParentA/v7
```

l'operazione corretta è:

```text
revise Child/v4
```

non `create-next`.

---

# 26. Aciclicità

La create-next non modifica:

```text
parent_template_id
```

della lineage.

Quindi non modifica il parent graph a livello di identity.

Se prima valeva:

```text
Child -> ParentA
```

dopo create-next vale ancora:

```text
Child -> ParentA
```

Viene aggiunta soltanto una nuova version row.

La create-next non può quindi introdurre un nuovo ciclo di inheritance.

Non sono richiesti:

```text
recursive ancestor traversal
cycle query
graph lock
```

durante questa operazione.

---

# 27. Atomicità

L'intera operazione deve essere atomica.

Esiti ammessi:

```text
new OTV DRAFT
+
cloned properties
+
cloned components
```

oppure:

```text
nothing
```

Non deve essere possibile committare:

```text
new OTV senza tutte le cloned properties/components
```

o viceversa.

---

# 28. Protocollo transazionale candidato

```text
BEGIN

1. acquisire FOR UPDATE
   sulla stable ObjectTemplate identity:

   SELECT id
   FROM object_templates
   WHERE id = :template_id
   FOR UPDATE

2. se identity missing:
       fail

3. leggere exact source OTV:
   (template_id, source_version)

4. verificare:
   source exists

5. verificare:
   source.status IN (
       PUBLISHED,
       DEPRECATED
   )

6. leggere:
   MAX(version)
   per la lineage

7. calcolare:
   new_version = MAX(version) + 1

8. leggere lo snapshot persistito locale della source:
   - parent_template_id
   - parent_version
   - properties
   - components

9. costruire la nuova OTV:
   template_id = same lineage
   version     = new_version
   status      = DRAFT
   parent pin  = exact clone della source

10. INSERT new OTV

11. INSERT cloned properties

12. INSERT cloned components

13. lasciare a:
    - PK
    - FK
    - CHECK
    - lineage parent invariant
    l'autorità finale

14. COMMIT
```

Se qualsiasi step fallisce:

```text
ROLLBACK
```

---

# 29. Lock non richiesti

La create-next non richiede:

```text
FOR NO KEY UPDATE sulla nuova OTV
```

perché la target non esiste ancora.

Non richiede:

```text
FOR NO KEY UPDATE sulla source
```

perché la source è strutturalmente immutabile.

Non richiede:

```text
FOR SHARE sul parent
```

perché non sta creando una nuova parent choice.

Non richiede:

```text
FOR SHARE sulle DTV
```

perché non sta creando nuove DTV choices.

Non richiede:

```text
component target locks
```

perché le FK proteggono l'esistenza.

Non richiede:

```text
cycle traversal
```

perché `parent_template_id` non cambia.

---

# 30. Separazione delle responsabilità

## Garantiti dal DB

```text
lineage existence
    -> FK OTV.template_id -> object_templates.id

version uniqueness
    -> PK(template_id, version)

parent identity consistency
    -> lineage trigger / equivalent

self-parent prohibition
    -> CHECK

exact parent existence
    -> composite FK RESTRICT

exact DTV existence
    -> FK RESTRICT

component target existence
    -> FK RESTRICT

property uniqueness
    -> PK / UNIQUE
```

## Garantiti dal create-next protocol

```text
source exact and valid
    -> source exists

source lifecycle eligible
    -> PUBLISHED or DEPRECATED

new version allocation
    -> identity-row FOR UPDATE
       then MAX(version)+1

new status
    -> DRAFT

exact source cloning
    -> application/domain protocol

atomic aggregate creation
    -> single transaction
```

---

# 31. Relazione con `revise`

La separazione delle responsabilità è esplicita.

## `create-next`

```text
clone exact historical snapshot
+
allocate new version
+
create new DRAFT
```

Non modifica la struttura.

## `revise`

```text
modify existing DRAFT candidate
```

Può cambiare, secondo i contratti ratificati:

```text
parent_version
properties
DTV pins
required
migration_default
components
```

e applica i relativi admission e validation protocol.

Quindi:

```text
create-next
    -> historical fork

revise
    -> structural evolution
```

---

# 32. Verdetto DRAFT

> **Create-next ObjectTemplateVersion è una operazione di exact historical snapshot cloning combinata con una per-lineage version allocation.**
>
> La source è exact e può essere `PUBLISHED` o `DEPRECATED`, mai `DRAFT`.
>
> La nuova versione è:
>
> ```text
> MAX(version) + 1
> status = DRAFT
> ```
>
> L'allocation viene serializzata localmente tramite `FOR UPDATE` sulla stable `object_templates` identity.
>
> `parent_template_id`, `parent_version`, properties, exact DataTypeVersion pins, `required`, `migration_default` e components vengono clonati esattamente dalla source.
>
> **Nessun cambiamento strutturale è ammesso durante `create-next`.**
>
> Ogni cambiamento successivo, incluso:
>
> ```text
> required FALSE -> TRUE
> required TRUE  -> FALSE
> ```
>
> deve avvenire tramite `revise`.
>
> I parent/DTV binding clonati non devono essere nuovamente `PUBLISHED`: possono essere `DEPRECATED`, perché sono carried-forward historical bindings già validi nella source.
>
> Non servono structural gate sulla source, `FOR SHARE` su parent o DTV, component target locks o cycle traversal.
>
> L'aciclicità non viene modificata perché `parent_template_id` resta invariato.
>
> Nessun locking globale viene introdotto.
