# ObjectTemplate Delete — Concurrency Contract DRAFT v2

## 1. Stato del documento

**DRAFT**

Questo documento ratifica provvisoriamente l'analisi e il protocollo concorrente dell'operazione:

```text
delete ObjectTemplate
```

sulla base esclusiva del **modello relazionale ObjectTemplate v4 ratificato**.

Il documento non introduce alcun locking globale del model-plane o cross-plane.

Viene inoltre annotato un ulteriore vincolo di dominio emerso durante l'analisi:

```text
il parent graph degli ObjectTemplate deve essere aciclico
```

Tale vincolo è rilevante per la semantica complessiva di inheritance, delete e lock ordering, ma rimane separato dal protocollo concorrente specifico della `delete`.

---

# 2. Modello relazionale rilevante

## 2.1 `object_templates`

```text
object_templates
----------------
id
namespace
name
description
abstract
```

La row:

```text
object_templates.id
```

rappresenta l'identità stabile della lineage.

---

## 2.2 `object_template_versions`

```text
object_template_versions
------------------------
template_id
version
parent_template_id
parent_version
status
```

Ownership:

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

Il modello v4 non contiene:

```text
object_templates.parent_template_id
```

Il riferimento parent è quindi espresso esclusivamente tramite gli exact parent pin presenti nelle singole `object_template_versions`.

`parent_template_id` rimane comunque semanticamente stabile lungo la lineage attraverso gli invarianti di dominio e DB ratificati nel modello v4.

---

## 2.3 `object_template_properties`

Ownership:

```sql
FOREIGN KEY (template_id, template_version)
    REFERENCES object_template_versions(template_id, version)
    ON DELETE CASCADE
```

DataTypeVersion pin:

```sql
FOREIGN KEY (datatype_id, datatype_version)
    REFERENCES datatype_versions(datatype_id, version)
    ON DELETE RESTRICT
```

---

## 2.4 `object_template_components`

Ownership:

```sql
FOREIGN KEY (template_id, template_version)
    REFERENCES object_template_versions(template_id, version)
    ON DELETE CASCADE
```

External target reference:

```sql
FOREIGN KEY (target_template_id)
    REFERENCES object_templates(id)
    ON DELETE RESTRICT
```

---

# 3. Obiettivo della delete

L'operazione elimina una intera ObjectTemplate lineage:

```text
object_templates.id = :template_id
```

insieme a tutte le strutture da essa possedute.

La forma relazionale preferita è:

```sql
DELETE FROM object_templates
WHERE id = :template_id;
```

eseguita in una singola transazione.

Il database deve poi applicare automaticamente:

```text
ownership interno
    -> CASCADE

dependencies esterne
    -> RESTRICT
```

---

# 4. Ownership interna

La delete della `object_templates` identity deve eliminare automaticamente:

```text
object_template_versions
object_template_properties
object_template_components
```

attraverso la catena:

```text
object_templates
    |
    | ON DELETE CASCADE
    v
object_template_versions
    |
    +--------------------+
    |                    |
    v                    v
object_template_properties
object_template_components
```

Queste rows non rappresentano dependencies che devono impedire la cancellazione.

Sono parte dell'aggregate posseduto dalla lineage.

---

# 5. Dependencies esterne che devono impedire il delete

La delete può riuscire soltanto se nessuna dependency esterna protetta da FK `RESTRICT` impedisce la rimozione delle rows possedute.

Le principali dependencies identificate sono:

```text
exact parent pin da altre ObjectTemplateVersion
component target reference
Object pin verso exact ObjectTemplateVersion
```

---

# 6. Exact parent pin da altre ObjectTemplateVersion

Nel modello v4 il riferimento parent è:

```text
Child/vN
    ->
Parent/vM
```

tramite:

```text
object_template_versions
(parent_template_id, parent_version)
    ->
object_template_versions(template_id, version)
    ON DELETE RESTRICT
```

Se una qualsiasi child version referenzia una exact version della lineage da eliminare:

```text
Child/v3 -> Parent/v5
```

la cancellazione di `Parent` deve fallire perché la cascata dovrebbe eliminare `Parent/v5`, ancora referenziata.

Questo vale indipendentemente dallo status della child:

```text
DRAFT
PUBLISHED
DEPRECATED
```

La FK protegge l'integrità referenziale, non il lifecycle.

---

# 7. Differenza rispetto al precedente modello

Nel modello v4 non esiste più:

```text
object_templates.parent_template_id
```

Di conseguenza la delete di una lineage usata come parent non viene più bloccata da una FK:

```text
child object_templates
    -> parent object_templates
```

La protezione deriva esclusivamente dagli exact parent pin presenti in:

```text
object_template_versions
```

Questa è una differenza sostanziale rispetto alle precedenti analisi basate sul vecchio modello.

---

# 8. Component target reference

Un component può referenziare una ObjectTemplate identity:

```text
component.target_template_id = OT-X
```

La FK:

```text
object_template_components.target_template_id
    -> object_templates.id
    ON DELETE RESTRICT
```

impedisce la cancellazione di `OT-X` finché il component esiste.

Non può quindi risultare:

```text
component.target_template_id
    -> ObjectTemplate inesistente
```

---

# 9. Object pin verso exact ObjectTemplateVersion

Nel modello complessivo NETAUTO, un Object persistito deve pinnare una exact ObjectTemplateVersion.

La relazione attesa è concettualmente:

```text
Object
(template_id, template_version)
    ->
object_template_versions(template_id, version)
    ON DELETE RESTRICT
```

Di conseguenza una ObjectTemplate lineage non può essere cancellata finché almeno un Object utilizza una delle sue versioni.

La forma definitiva di questa FK verrà ratificata nel modello `Object`.

Per il protocollo della delete ObjectTemplate essa costituisce comunque una dependency esterna necessaria.

---

# 10. Le properties verso DataTypeVersion NON bloccano il delete

Le properties contengono:

```text
object_template_properties
    -> datatype_versions
    ON DELETE RESTRICT
```

Ma durante la delete dell'ObjectTemplate viene eliminata la row referencing:

```text
object_template_property
```

non la DataTypeVersion referenziata.

Questa FK impedisce:

```text
DELETE DataTypeVersion
```

mentre la property esiste.

Non impedisce:

```text
DELETE ObjectTemplate
```

con cascata delle proprie properties.

Quindi i DataTypeVersion pin non costituiscono dependencies esterne che bloccano questa operazione.

---

# 11. Race: nuovo exact parent pin vs delete

Scenario:

```text
T1 delete Parent              T2 create/revise Child

                              Child/v3 -> Parent/v5
```

La FK `RESTRICT` sull'exact parent pin è sufficiente a risolvere la race.

Possibili esiti:

```text
binding child vince
    -> Parent/v5 risulta referenziata
    -> delete Parent fallisce
```

oppure:

```text
delete Parent vince
    -> Parent/v5 viene eliminata
    -> il nuovo exact parent pin non può essere persistito
```

Non può esistere lo stato:

```text
Child/v3 -> Parent/v5
Parent/v5 inesistente
```

Non è richiesto un row lock applicativo aggiuntivo per proteggere l'esistenza.

---

# 12. Distinzione tra FK e consumer-side `FOR SHARE`

Le operazioni `create`, `revise` e `publish` possono acquisire `FOR SHARE` sulla exact parent ObjectTemplateVersion per stabilizzare:

```text
status == PUBLISHED
```

Quel lock protegge il **lifecycle predicate**.

La FK `RESTRICT` protegge invece:

```text
esistenza del riferimento
```

rispetto alla delete.

Le due responsabilità sono distinte:

```text
FOR SHARE
    -> parent rimane PUBLISHED durante admission/certification

FK RESTRICT
    -> parent non può sparire lasciando un dangling reference
```

---

# 13. Race: nuovo component target vs delete

Scenario:

```text
T1 delete OT-X               T2 persist component -> OT-X
```

La FK sul target decide correttamente la race.

Possibili esiti:

```text
component vince
    -> delete fallisce
```

oppure:

```text
delete vince
    -> il nuovo component non può essere persistito
```

Non può risultare un component dangling.

Non è necessario locking esplicito applicativo.

---

# 14. Race: nuovo Object pin vs delete

Scenario:

```text
T1 delete OT-X               T2 create/repin Object -> OT-X/v3
```

La FK dell'Object verso la exact OTV deve garantire:

```text
Object binding vince
    -> delete fallisce
```

oppure:

```text
delete vince
    -> nuovo Object binding fallisce
```

L'integrità referenziale rimane l'autorità finale.

---

# 15. Race: create-next della stessa lineage vs delete

Una nuova ObjectTemplateVersion è ownership interna:

```text
object_template_versions.template_id
    -> object_templates.id
    ON DELETE CASCADE
```

Scenario:

```text
T1 delete OT-X               T2 create-next OT-X/v5
```

Se il delete vince:

```text
OT-X viene eliminata
-> la nuova v5 non può sopravvivere come row orfana
```

Se create-next completa prima:

```text
OT-X/v5 viene persistita
```

questo non obbliga il delete a fallire.

L'ordine seriale:

```text
create-next v5
COMMIT

delete OT-X
-> CASCADE v5
COMMIT
```

è perfettamente valido.

Una nuova version della stessa lineage non è una dependency esterna.

---

# 16. Race: revise vs delete

La `revise` acquisisce:

```text
FOR NO KEY UPDATE
```

sulla exact OTV.

Il delete deve eliminare quella stessa row tramite cascade.

PostgreSQL coordina le due row mutation.

Possibili ordini seriali:

```text
revise
-> COMMIT
-> delete
```

oppure:

```text
delete
-> revise non può completare
```

Non è necessario un ulteriore lock esplicito lato delete.

---

# 17. Race: publish vs delete

La `publish` acquisisce lo structural gate sulla exact OTV e può effettuare:

```text
DRAFT -> PUBLISHED
```

Il delete deve eliminare la stessa row.

Il DB coordina le due operazioni.

È valido anche:

```text
publish succeeds
-> delete succeeds immediately after
```

se non esistono dependencies esterne.

Lo status `PUBLISHED` non significa che una versione sia intrinsecamente non cancellabile.

La cancellabilità è determinata dalle FK `RESTRICT`.

---

# 18. Race: deprecate vs delete

La `deprecate` effettua:

```text
UPDATE exact OTV
PUBLISHED -> DEPRECATED
```

mentre il delete deve eliminare la stessa row.

PostgreSQL coordina update e delete.

Non è necessario locking preventivo applicativo.

---

# 19. Nessun uso dello structural gate

La delete non deve leggere o certificare in modo stabile:

```text
parent_version
properties
components
```

Non deve costruire una candidate structure.

Non deve prendere una decisione basata sul contenuto strutturale delle singole versioni.

Deve solamente:

> eliminare l'intero aggregate se nessuna dependency esterna lo impedisce.

Per questo motivo non deve acquisire preventivamente:

```text
FOR NO KEY UPDATE
```

sulle singole OTV.

Il `DELETE`, le cascade e le FK acquisiscono i lock DB necessari.

---

# 20. Pre-check applicativi

L'application layer può effettuare pre-check per produrre errori di dominio più espressivi.

Esempi:

```text
ObjectTemplateReferencedAsParent
ObjectTemplateReferencedByComponent
ObjectTemplateInUseByObjects
```

Questi controlli sono utili per:

```text
domain semantics
error reporting
UX
```

ma non costituiscono l'autorità finale.

Race:

```text
T1 pre-check:
    nessun riferimento esterno

                              T2 INSERT component -> OT-X
                              COMMIT

T1 DELETE OT-X
```

Il pre-check è diventato stale.

La FK `RESTRICT` deve comunque impedire il delete.

Principio:

```text
pre-check applicativo
    -> errore semantico anticipato

FK RESTRICT
    -> autorità finale di consistenza
```

Una FK violation concorrente dovrebbe idealmente essere tradotta nello stesso errore di dominio previsto dal pre-check.

---

# 21. Forma preferita dell'operazione

La delete non dovrebbe enumerare e cancellare manualmente:

```text
properties
components
versions
template
```

La forma preferita è:

```sql
DELETE FROM object_templates
WHERE id = :template_id;
```

Il database distingue automaticamente:

```text
owned rows
    -> CASCADE

external dependencies
    -> RESTRICT
```

Questo riduce la superficie di race e concentra l'autorità referenziale nello schema relazionale.

---

# 22. Protocollo transazionale candidato

```text
BEGIN

1. eventuali pre-check applicativi
   per error reporting

2. DELETE FROM object_templates
   WHERE id = :template_id

3. PostgreSQL applica:

   ownership:
       object_template_versions
       object_template_properties
       object_template_components
           -> CASCADE

   external dependencies:
       exact parent pins
       component target references
       Object exact-version pins
           -> RESTRICT

4. se una FK RESTRICT fallisce:
       tradurre idealmente la violation
       nell'errore di dominio appropriato
       ROLLBACK

5. altrimenti:
       COMMIT
```

---

# 23. Vincolo di dominio: aciclicità del parent graph

Durante l'analisi è stato ratificato anche il seguente vincolo di dominio:

> **Il grafo di ereditarietà degli ObjectTemplate deve essere aciclico.**

Non deve quindi essere possibile costruire dipendenze come:

```text
A -> B
B -> A
```

né cicli più lunghi:

```text
A -> B
B -> C
C -> A
```

La regola si riferisce all'identità logica del parent:

```text
parent_template_id
```

che è stabile lungo la lineage.

L'evoluzione di:

```text
parent_version
```

non deve modificare questa proprietà del grafo.

---

# 24. Perché l'aciclicità è importante

L'aciclicità è necessaria per mantenere una semantica sana e deterministica di:

```text
inheritance
dependency traversal
delete behavior
lock ordering
cycle detection
```

Un ciclo produrrebbe lineage che sono simultaneamente antenate e discendenti l'una dell'altra.

Inoltre le FK `RESTRICT` sugli exact parent pin renderebbero le lineage ciclicamente dipendenti difficili o impossibili da eliminare singolarmente.

La presenza di cicli complicherebbe anche l'analisi del lock ordering delle operazioni che attraversano parent dependencies.

---

# 25. Aciclicità separata dal protocollo della delete

L'aciclicità è un **invariante di dominio**, non un meccanismo necessario per rendere concorrente-safe la singola operazione `delete`.

Anche senza assumere aciclicità, le FK continuano a impedire dangling references.

Quindi:

```text
delete consistency
    -> CASCADE + RESTRICT

parent graph validity
    -> acyclicity domain invariant
```

sono due responsabilità distinte.

Il meccanismo concreto con cui l'aciclicità verrà verificata e resa autoritativa:

```text
application validation
constraint trigger
recursive query
altro meccanismo PostgreSQL
```

rimane da definire nell'analisi specifica delle operazioni che creano o modificano parent dependencies.

Non viene scelto prematuramente in questo documento.

---

# 26. Separazione delle responsabilità

## Garantiti dal DB

```text
ownership cleanup
    -> ON DELETE CASCADE

exact parent dependency
    -> FK RESTRICT

component target dependency
    -> FK RESTRICT

Object exact-version dependency
    -> FK RESTRICT nel modello Object

race tra reference creation e delete
    -> referential integrity PostgreSQL

row mutation coordination
    -> PostgreSQL
```

## Garantiti dall'application layer

```text
pre-check opzionali
    -> error reporting più preciso

mapping FK violation
    -> domain error appropriato
```

## Invariante di dominio separato

```text
parent graph acyclic
```

---

# 27. Verdetto DRAFT

> **Delete ObjectTemplate è SAFE senza locking esplicito applicativo.**
>
> La forma preferita è un singolo `DELETE` sulla `object_templates` identity eseguito in una transazione.
>
> Le strutture possedute vengono eliminate tramite `ON DELETE CASCADE`.
>
> Le dependencies esterne impediscono il delete tramite FK `ON DELETE RESTRICT`.
>
> Nel modello v4 le principali dependencies esterne sono:
>
> ```text
> exact parent pins da altre ObjectTemplateVersion
> component target references
> Object pins verso exact ObjectTemplateVersion
> ```
>
> Le properties verso DataTypeVersion non impediscono il delete, perché durante questa operazione vengono eliminate le rows referencing.
>
> Eventuali pre-check applicativi servono soltanto a produrre errori di dominio migliori; le FK rimangono l'autorità finale anche nelle race.
>
> La delete non richiede structural gate né altri row lock preventivi.
>
> Separatamente, viene ratificato come vincolo di dominio che **il parent graph degli ObjectTemplate deve essere aciclico**. Il meccanismo concreto di enforcement verrà definito analizzando le operazioni che introducono o modificano parent dependencies.
>
> Nessun locking globale viene introdotto.
