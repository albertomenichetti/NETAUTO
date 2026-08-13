# Object — Domain & Business Model Ratificato v1

## Stato

**RATIFICATO come baseline Domain & Business corrente**

Questo documento descrive la semantica di dominio del modello `Object`.
La forma di tabelle, PK/FK/CHECK e indici è mantenuta nel documento separato `Object — Modello Relazionale Ratificato v1`.

---

## 1. Object identity

L'identità autorevole di un Object è esclusivamente:

```text
Object.id
```

`canonical_name` non partecipa all'identità e non è `UNIQUE`.

Due Object distinti possono avere lo stesso canonical name.

---

## 2. `canonical_name`

### Scopo

È un attributo umano/search-oriented per:

```text
visualizzazione
ricerca
lookup operativo
audit
```

Non sostituisce mai `id`.

### Create

```text
canonical_name omitted / None
    -> canonical_name = str(Object.id)

canonical_name provided and non-empty
    -> use provided value

canonical_name == ""
    -> invalid
```

La stringa vuota non viene interpretata come richiesta di fallback.

### Mutabilità

`canonical_name` è mutabile.

Una modifica del solo canonical name è una operation semanticamente distinta:

```text
RENAME
```

e produce un audit event dello stesso kind.

---

## 3. Runtime properties

Le proprietà runtime dell'Object sono dati semantici validati rispetto alla exact ObjectTemplateVersion pinnata.

La rappresentazione PostgreSQL è `JSONB`.

---

## 4. Exact ObjectTemplateVersion pin

Ogni Object è pinnato a una exact:

```text
(template_id, template_version)
```

Il pin identifica lo schema applicabile all'Object.

La semantica lifecycle e concurrency dell'admission verso una nuova exact OTV sarà ratificata nelle action:

```text
create Object
schema migration / repin
```

---

## 5. Component slots

Un Object può avere uno o più slot effettivi in funzione della propria exact ObjectTemplateVersion.

Uno slot è una collection semantica con cardinalità:

```text
0..N
```

Esempio:

```text
Router R1

slot["network_interfaces"] =
    {if1, if2, ..., ifN}

slot["supervisors"] =
    {supervisor1, supervisor2}
```

---

## 6. Significato di `slot_name`

`slot_name` identifica il ruolo/collection semantica, non necessariamente il tipo in modo univoco.

Esempio:

```text
slot "inside_interfaces"
    -> target NetworkInterface

slot "outside_interfaces"
    -> target NetworkInterface
```

Quindi:

```text
slot_name
    = ruolo semantico

target_template_id
    = tipo/lineage ammessa
```

---

## 7. Ownership esclusivo del child

Un Object può essere attached come child a:

```text
al massimo un owner/slot
```

alla volta.

Sono validi:

```text
R1 / network_interfaces -> if1
R1 / network_interfaces -> if2
R1 / network_interfaces -> if3
```

ma non:

```text
R1 / network_interfaces -> if1
R2 / network_interfaces -> if1
```

né:

```text
R1 / network_interfaces -> if1
R1 / backup_interfaces  -> if1
```

senza un precedente detach.

---

## 8. Cardinalità slot

Uno stesso `(parent Object, slot_name)` può contenere:

```text
0..N children
```

Non esiste una regola business "one child per slot".

---

## 9. Self-attachment

Vietato:

```text
A -> A
```

È un invariante di dominio e anche una regola protetta dal modello relazionale.

---

## 10. Effective slot validity

Ogni attachment deve soddisfare:

> `slot_name` appartiene agli effective component slots della exact ObjectTemplateVersion del parent Object.

La parola **effective** è fondamentale.

Lo slot può essere:

```text
definito localmente
```

oppure:

```text
ereditato tramite ObjectTemplate inheritance
```

Non basta quindi verificare le sole rows locali della exact OTV.

---

## 11. Child compatibility

Ogni effective slot dichiara:

```text
target_template_id
```

Il child attached deve essere semanticamente compatibile con quel target.

In prima approssimazione:

```text
child.template_id compatible with slot.target_template_id
```

La definizione esatta di "compatible" sarà ratificata con le action di attach.

---

## 12. Ownership graph aciclico

L'ownership graph degli Object deve essere aciclico.

Non sono ammessi:

```text
A -> B
B -> A
```

né:

```text
A -> B
B -> C
C -> A
```

Combinando:

```text
single-owner child
+
acyclicity
```

il grafo di ownership assume la forma di una foresta.

L'enforcement concorrente definitivo sarà analizzato con:

```text
attach
detach
subtree delete
```

---

## 13. Audit log

`object_changes` è un audit log storico:

```text
append-only
```

Le normali workflow applicative inseriscono audit event ma non modificano o cancellano quelli esistenti.

Un eventuale enforcement DB contro `UPDATE/DELETE` resta separato.

---

## 14. Audit kinds

Valori ratificati:

```text
CREATED
DELETED
RENAME
SCHEMA_CHANGE
DATA_CHANGE
```

### `CREATED`

L'Object è stato creato.

### `DELETED`

L'Object è stato cancellato.

### `RENAME`

È cambiato esclusivamente:

```text
canonical_name
```

### `SCHEMA_CHANGE`

È cambiata la exact ObjectTemplateVersion pinnata e può esserci una migrazione dei dati.

### `DATA_CHANGE`

Sono cambiati i runtime values senza cambio di schema e senza rename.

---

## 15. Operazioni semanticamente distinte

Non deve essere usato un generico update ambiguo per fondere senza distinzione:

```text
rename
data change
schema change
```

Mapping:

```text
rename
    -> RENAME

update properties
    -> DATA_CHANGE

migrate/repin schema
    -> SCHEMA_CHANGE
```

Se una workflow superiore esegue più mutazioni semanticamente distinte nella stessa transaction, è preferibile produrre audit event distinti e precisi.

---

## 16. Canonical Object snapshot

Shape logica uniforme:

```json
{
  "canonical_name": "router-rm-01",
  "template_id": "template-id",
  "template_version": 3,
  "properties": {
    "...": "..."
  }
}
```

Rappresenta lo stato semantico dell'Object.

Gli attachment/component ownership non sono inclusi, per ora, nello snapshot.

---

## 17. Semantica degli audit event

### CREATED

```text
before = absent
after  = initial full Object snapshot

object_changes.canonical_name
    = created name
```

### DELETED

```text
before = final full Object snapshot
after  = absent

object_changes.canonical_name
    = final/last known name
```

### RENAME

```text
before = full snapshot before rename
after  = full snapshot after rename
```

L'unica differenza semanticamente ammessa è:

```text
canonical_name
```

e la colonna `object_changes.canonical_name` contiene il nuovo nome.

### DATA_CHANGE

```text
before = full snapshot before
after  = full snapshot after
```

Devono rimanere invariati:

```text
canonical_name
template_id
template_version
```

e cambiano le runtime properties.

### SCHEMA_CHANGE

```text
before = full snapshot con old exact template pin
after  = full snapshot con new exact template pin
```

Gli snapshot includono anche i dati prima e dopo la migrazione.

Non è sufficiente registrare soltanto:

```text
old template -> new template
```

perché la migrazione può aggiungere required properties, applicare migration_default, rimuovere proprietà o trasformare dati.

---

## 18. Significato di `object_changes.canonical_name`

Matrice:

```text
CREATED
    -> created name

RENAME
    -> new name

DATA_CHANGE
    -> current name after change

SCHEMA_CHANGE
    -> current name after migration

DELETED
    -> final/last known name
```

La colonna serve per lookup e visualizzazione; la storia completa resta nei canonical snapshots.

---

## 19. Temporal semantics

`occurred_at` rappresenta l'istante assoluto dell'audit event.

La rappresentazione relazionale è `TIMESTAMPTZ`.

La responsabilità concreta di assegnazione fra application clock e database clock/default non è ancora ratificata.

---

## 20. Principio JSON semantico

Runtime properties e audit snapshots rappresentano contenuto semantico, non documenti testuali la cui serializzazione originale abbia valore di dominio.

La persistenza PostgreSQL usa quindi `JSONB`.

La stessa regola deve essere riesaminata coerentemente sugli altri campi JSON del sistema.

---

## 21. Questioni di dominio ancora aperte

Da ratificare analizzando le singole action Object:

```text
create Object admission protocol
rename concurrency
DATA_CHANGE concurrency
SCHEMA_CHANGE / migration protocol
attach/detach protocol
effective slot resolution
child target compatibility exact semantics
ownership acyclicity under concurrency
subtree deletion interaction
audit write atomicity rispetto alla mutation principale
```

Questi aspetti non vengono anticipati nella baseline.
