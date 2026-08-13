# ObjectTemplateVersion Deprecate — Concurrency Contract DRAFT v2

## 1. Stato del documento

**DRAFT**

Questo documento ratifica provvisoriamente l'analisi e il protocollo concorrente dell'operazione:

```text
deprecate ObjectTemplateVersion
```

sulla base esclusiva del **modello relazionale ObjectTemplate v4 ratificato**.

Il documento non introduce alcun locking globale del model-plane o cross-plane.

---

# 2. Obiettivo dell'operazione

La `deprecate` modifica esclusivamente la exact:

```text
ObjectTemplateVersion(template_id, version)
```

portando lo stato da:

```text
PUBLISHED
```

a:

```text
DEPRECATED
```

Non modifica:

```text
parent_template_id
parent_version
properties
components
```

e non revisiona in alcun modo la struttura della versione.

---

# 3. Invariante locale

La transizione lifecycle ammessa è:

```text
PUBLISHED -> DEPRECATED
```

La `deprecate` è quindi valida soltanto se, al momento dell'update, la exact target ObjectTemplateVersion è ancora:

```text
status == PUBLISHED
```

Una sequenza:

```text
READ status=PUBLISHED
...
UPDATE status=DEPRECATED
```

non è sufficiente perché la decisione potrebbe diventare stale.

---

# 4. Conditional UPDATE / CAS

La precondizione e la transizione devono essere codificate nello stesso statement.

Forma ratificata:

```sql
UPDATE object_template_versions
SET status = 'DEPRECATED'
WHERE template_id = :template_id
  AND version = :version
  AND status = 'PUBLISHED';
```

Interpretazione:

```text
rowcount == 1
    -> deprecate riuscita

rowcount == 0
    -> exact version inesistente
       oppure lifecycle transition non valida
```

Se il contratto applicativo richiede di distinguere i due casi, può essere effettuata una lettura successiva per produrre l'errore di dominio appropriato.

---

# 5. Nessun locking esplicito preventivo

La `deprecate` non deve effettuare preventivamente:

```text
SELECT ... FOR UPDATE
SELECT ... FOR NO KEY UPDATE
```

Il conditional `UPDATE` è sufficiente a proteggere il suo invariante locale.

PostgreSQL acquisisce comunque i normali row lock richiesti dall'`UPDATE`.

La `deprecate` non deve conoscere preventivamente i workflow che consumano quella ObjectTemplateVersion.

---

# 6. Nessun uso esplicito dello structural gate

Lo structural gate della exact OTV:

```text
FOR NO KEY UPDATE
su object_template_versions(template_id, version)
```

serve alle operazioni che devono leggere o modificare in modo stabile la struttura DRAFT:

```text
parent_version
properties
components
```

La `deprecate` non legge e non modifica questi dati.

Il suo unico invariante è:

```text
status == PUBLISHED
```

protetto tramite CAS.

Per questo motivo non usa esplicitamente lo structural gate.

---

# 7. `deprecate` vs `deprecate`

Due richieste concorrenti possono tentare:

```text
PUBLISHED -> DEPRECATED
```

sulla stessa exact OTV.

Con il conditional `UPDATE`, una sola può modificare la row.

La seconda, quando viene rivalutata, non trova più:

```text
status == PUBLISHED
```

e ottiene:

```text
rowcount == 0
```

Non è richiesto alcun lock esplicito aggiuntivo.

---

# 8. `deprecate` vs `publish`

La `publish` opera su:

```text
DRAFT -> PUBLISHED
```

mentre la `deprecate` opera su:

```text
PUBLISHED -> DEPRECATED
```

La publish acquisisce lo structural gate sulla exact OTV.

Se il deprecate arriva quando la target è ancora `DRAFT`:

```text
status != PUBLISHED
```

e il CAS non è ammissibile.

Se invece il deprecate attende la publish e la publish committa:

```text
DRAFT -> PUBLISHED
```

il deprecate può successivamente effettuare:

```text
PUBLISHED -> DEPRECATED
```

Il risultato equivale all'ordine seriale:

```text
publish
deprecate
```

ed è valido.

Non serve ulteriore coordinamento specifico.

---

# 9. `deprecate` vs `revise`

La `revise` richiede:

```text
status == DRAFT
```

La `deprecate` richiede:

```text
status == PUBLISHED
```

I predicati sono mutuamente esclusivi.

Se la revise detiene lo structural gate, il conditional `UPDATE` del deprecate può eventualmente attendere.

Quando può essere valutato, deve comunque soddisfare:

```text
status == PUBLISHED
```

Se la versione è ancora `DRAFT`, nessuna row viene modificata.

Non è richiesto locking aggiuntivo.

---

# 10. Principio fondamentale: la responsabilità è sui consumer

La `deprecate` non deve proteggere i workflow che consumano la exact ObjectTemplateVersion.

Sono i workflow che basano una decisione su:

```text
ObjectTemplateVersion.status == PUBLISHED
```

a dover stabilizzare quel predicato fino al commit del nuovo binding.

Regola ratificata:

> Qualsiasi consumer che crea un nuovo binding la cui admission richiede una exact ObjectTemplateVersion `PUBLISHED` deve acquisire `FOR SHARE` sulla exact `(template_id, version)`, verificare `status == PUBLISHED`, persistere il binding e mantenere il lock fino al commit.

Schema generale:

```text
BEGIN

FOR SHARE exact ObjectTemplateVersion

verify status == PUBLISHED

persist new binding

COMMIT
```

Il normale `UPDATE` del deprecate deve attendere il `FOR SHARE`.

---

# 11. Consumer: publish di una child ObjectTemplateVersion

Scenario:

```text
Child/v3
    parent -> Parent/v5
```

La publish della child richiede:

```text
Parent/v5.status == PUBLISHED
```

Protocollo del consumer:

```text
FOR SHARE Parent/v5
verify PUBLISHED
publish Child/v3
COMMIT
```

Race:

```text
publish child vince
    -> Parent/v5 rimane PUBLISHED fino al commit
    -> deprecate Parent/v5 attende
    -> dopo il commit il parent può essere deprecato

deprecate parent vince
    -> Parent/v5 diventa DEPRECATED
    -> publish child vede DEPRECATED
    -> publish child fallisce
```

---

# 12. Consumer: revise di una child ObjectTemplateVersion

Scenario:

```text
Child/v3.parent_version
    4 -> 5
```

La revise crea un nuovo exact parent pin:

```text
Child/v3 -> Parent/v5
```

e richiede:

```text
Parent/v5.status == PUBLISHED
```

Protocollo:

```text
FOR SHARE Parent/v5
verify PUBLISHED
persist parent_version=5
COMMIT
```

Dopo il commit, `Parent/v5` può essere deprecata.

La child rimane `DRAFT`.

Una futura publish dovrà comunque riverificare il parent.

Questo distingue:

```text
revise
    -> admission-time consistency

publish
    -> certification-time consistency
```

---

# 13. Consumer futuro: create ObjectTemplate

Se la creazione di una nuova lineage produce una v1 con exact parent pin:

```text
Child/v1 -> Parent/v5
```

la create è un consumer della exact parent ObjectTemplateVersion.

Dovrà quindi seguire la stessa regola:

```text
FOR SHARE Parent/v5
verify PUBLISHED
persist child binding
COMMIT
```

I dettagli completi della `create` verranno ratificati nel relativo documento operativo.

---

# 14. Consumer futuro: Object

Se un workflow `Object create` o repinning può creare un nuovo binding verso una exact ObjectTemplateVersion soltanto se questa è `PUBLISHED`, anche quel workflow deve seguire:

```text
FOR SHARE exact OTV
verify PUBLISHED
persist Object binding
COMMIT
```

Il deprecator non deve conoscere il tipo concreto del consumer.

---

# 15. Binding esistenti

La transizione:

```text
PUBLISHED -> DEPRECATED
```

non invalida i binding già esistenti.

Possono continuare a esistere validamente:

```text
child OTV già pinnate
Object già pinnati
altri binding persistiti correttamente
```

Il significato di `DEPRECATED` è:

> la versione non è più ammissibile per nuovi binding che richiedono `PUBLISHED`.

Non significa:

> tutti i binding esistenti devono essere eliminati o diventano invalidi.

---

# 16. Caso importante: child DRAFT già pinnata

Scenario iniziale:

```text
Child/v3 = DRAFT
parent = Parent/v5

Parent/v5 = PUBLISHED
```

La child ha creato correttamente il pin mentre il parent era `PUBLISHED`.

Successivamente:

```text
Parent/v5 -> DEPRECATED
```

Questo deve essere consentito.

Lo stato:

```text
Child/v3 DRAFT
    -> Parent/v5 DEPRECATED
```

non è relazionalmente incoerente.

Quando verrà tentata:

```text
publish Child/v3
```

la publish dovrà verificare:

```text
Parent/v5.status == PUBLISHED
```

e fallirà.

Quindi il deprecate non deve essere impedito dalla presenza di child DRAFT già pinnate.

---

# 17. Admission-time consistency

La semantica complessiva dei consumer è di:

```text
admission-time consistency
```

Un nuovo binding viene ammesso tramite:

```text
FOR SHARE exact OTV
-> verify PUBLISHED
-> persist binding
-> COMMIT
```

Dopo il commit:

```text
PUBLISHED -> DEPRECATED
```

può avvenire senza invalidare retroattivamente il binding.

---

# 18. Parent identity invariant non coinvolto

Il modello v4 rende:

```text
parent_template_id
```

immutabile su UPDATE e coerente lungo tutta la lineage.

La `deprecate` modifica esclusivamente:

```text
status
```

e non interagisce con questo invariante.

Non è quindi necessario alcun controllo o lock aggiuntivo legato al parent identity.

---

# 19. Delete concorrente

La `deprecate` effettua:

```text
UPDATE exact OTV
```

mentre il delete della lineage deve eliminare la stessa row tramite cascade.

PostgreSQL coordina update/delete sulla stessa row.

Gli esiti sono serializzati e non esiste uno stato finale incoerente che richieda un lock applicativo preventivo.

---

# 20. Protocollo transazionale candidato

```text
BEGIN

1. eseguire conditional UPDATE:

   UPDATE object_template_versions
   SET status = DEPRECATED
   WHERE template_id = :template_id
     AND version = :version
     AND status = PUBLISHED

2. controllare rowcount

3. se rowcount == 0:
      distinguere eventualmente:
      - exact version inesistente
      - lifecycle transition non valida

4. se rowcount == 1:
      COMMIT
```

Non sono richieste letture strutturali di:

```text
parent_template_id
parent_version
properties
components
```

e non sono richiesti lock espliciti preventivi.

---

# 21. Separazione delle responsabilità

## Garantiti dal DB

```text
exact target identity
    -> PK

parent identity invariant
    -> constraint trigger / equivalent

referential integrity
    -> FK

row-level serialization dell'UPDATE
    -> PostgreSQL
```

## Garantiti dal deprecate protocol

```text
PUBLISHED -> DEPRECATED
solo se la row è ancora PUBLISHED
    -> conditional UPDATE / CAS
```

## Garantiti dai consumer

```text
new binding admitted only while exact OTV is PUBLISHED
    -> FOR SHARE + verify + commit
```

---

# 22. Verdetto DRAFT

> **Deprecate ObjectTemplateVersion è una operazione locale sulla singola OTV e non richiede locking esplicito preventivo.**
>
> La transizione viene protetta con conditional `UPDATE` / CAS:
>
> ```text
> PUBLISHED -> DEPRECATED
> ```
>
> La `deprecate` non utilizza lo structural gate perché non modifica `parent_version`, properties o components.
>
> I binding già esistenti rimangono validi dopo la deprecazione.
>
> **Qualsiasi workflow che crea un nuovo binding la cui admission richiede una exact ObjectTemplateVersion `PUBLISHED` deve invece acquisire `FOR SHARE` sulla exact OTV, verificarne lo status e mantenere il lock fino al commit.**
>
> Questo principio si applica a child parent pin, Object pin e qualsiasi altro consumer futuro.
>
> Nessun locking globale viene introdotto.
