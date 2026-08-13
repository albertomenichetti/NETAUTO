# Object — Modello Relazionale Ratificato v1

## Stato

**RATIFICATO come baseline relazionale corrente**

Questo documento descrive esclusivamente la forma relazionale del dominio `Object`.
Le regole Domain/Business sono mantenute nel documento separato `Object — Domain & Business Model Ratificato v1`.

---

## 1. Tabelle principali

La persistenza PostgreSQL del dominio Object è basata principalmente su:

```text
objects
object_components
object_changes
```

Principi:

```text
Object identity autorevole = objects.id
canonical_name = attributo descrittivo/search-oriented, non identitario
runtime properties = JSONB
ownership tra Object = object_components
audit history = object_changes
audit history sopravvive alla cancellazione della row live
```

---

## 2. `objects`

```text
objects
-------
id                  UUID NOT NULL
canonical_name      TEXT NOT NULL
template_id         NOT NULL
template_version    NOT NULL
properties_json     JSONB NOT NULL
```

Constraint:

```text
PRIMARY KEY(id)
```

```sql
FOREIGN KEY (template_id, template_version)
    REFERENCES object_template_versions(template_id, version)
    ON DELETE RESTRICT
```

```sql
CHECK (canonical_name <> '')
```

Indice:

```sql
CREATE INDEX ... ON objects(canonical_name);
```

`canonical_name` non è `UNIQUE`.

L'identità univoca dell'Object continua a essere esclusivamente:

```text
objects.id
```

### JSONB

`objects.properties_json` è ratificato come:

```text
JSONB NOT NULL
```

Regola architetturale candidata trasversale:

> I campi JSON che rappresentano dati strutturati semanticamente interrogabili o snapshot di stato devono essere persistiti come `JSONB`, salvo un requisito esplicito di preservazione della rappresentazione testuale originale.

Da riesaminare coerentemente almeno:

```text
objects.properties_json
object_changes.before_json
object_changes.after_json
datatype_versions.constraints_json
```

---

## 3. `object_components`

### Shape

```text
object_components
-----------------
parent_object_id
slot_name
child_object_id
```

È ratificato `slot_name`, non un generico `slot_id`, perché nel modello corrente non esiste una identity stabile separata dello slot.

### Cardinalità

Uno slot rappresenta una collection semantica:

```text
0..N
```

Esempio:

```text
Router R1

slot "network_interfaces"
    -> if1
    -> if2
    -> ...
    -> ifN

slot "supervisors"
    -> supervisor1
    -> supervisor2
```

### Chiavi

```text
PRIMARY KEY(child_object_id)
```

Questa PK impone che un Object possa essere child di al massimo un solo owner/slot alla volta.

Non deve esistere:

```text
UNIQUE(parent_object_id, slot_name)
```

perché uno stesso slot può contenere 0..N children.

### Foreign key

```sql
FOREIGN KEY (parent_object_id)
    REFERENCES objects(id)
    ON DELETE RESTRICT
```

```sql
FOREIGN KEY (child_object_id)
    REFERENCES objects(id)
    ON DELETE RESTRICT
```

### Check

```sql
CHECK (parent_object_id <> child_object_id)
```

```sql
CHECK (slot_name <> '')
```

### Indice

```sql
CREATE INDEX ...
ON object_components(parent_object_id, slot_name);
```

La query primaria servita è:

```text
tutti i children dello slot X del parent P
```

### Invarianti non ancora codificati da normali FK/CHECK

La baseline deve supportare:

```text
1. slot_name appartiene agli effective component slots
   della exact ObjectTemplateVersion del parent

2. child.template_id è compatibile con
   target_template_id dello slot effettivo

3. l'Object ownership graph è aciclico
```

Il meccanismo DB definitivo non è ancora ratificato.

Una FK diretta verso le sole rows locali di `object_template_components` non è sufficiente, perché uno slot effettivo può essere ereditato.

---

## 4. `object_changes`

### Ruolo

`object_changes` è un audit log storico e deve sopravvivere al delete della row live in `objects`.

### Shape

```text
object_changes
--------------
id                  PK
object_id           NOT NULL
canonical_name      TEXT NOT NULL
occurred_at         TIMESTAMPTZ NOT NULL
kind                TEXT NOT NULL
before_json         JSONB NULL
after_json          JSONB NULL
```

Il tipo concreto di `object_changes.id` rimane quello standard adottato dal progetto; questo documento ne ratifica il ruolo di PK ma non introduce un nuovo tipo.

### Nessuna FK verso `objects`

È intenzionale che:

```text
object_changes.object_id
```

non abbia FK verso:

```text
objects.id
```

Perché:

```text
CASCADE  -> distruggerebbe l'audit
RESTRICT -> impedirebbe il delete dell'Object
SET NULL -> perderebbe l'identificatore storico
```

`object_id` rimane quindi un identificatore storico `NOT NULL`.

### `canonical_name`

```sql
CHECK (canonical_name <> '')
```

```sql
CREATE INDEX ... ON object_changes(canonical_name);
```

È una denormalizzazione intenzionale per ricerca, visualizzazione e audit lookup.

### `occurred_at`

Tipo ratificato:

```text
TIMESTAMPTZ NOT NULL
```

La scelta fra application clock e DB default resta separata.

### `kind`

Valori ratificati:

```text
CREATED
DELETED
RENAME
SCHEMA_CHANGE
DATA_CHANGE
```

Forma:

```text
TEXT NOT NULL
```

con:

```sql
CHECK (
    kind IN (
        'CREATED',
        'DELETED',
        'RENAME',
        'SCHEMA_CHANGE',
        'DATA_CHANGE'
    )
)
```

È preferito `TEXT + CHECK` a un native PostgreSQL ENUM.

### `before_json` / `after_json`

Entrambi sono `JSONB` e rappresentano canonical Object snapshots con shape uniforme.

Nullability:

```text
CREATED
    before_json = NULL
    after_json  = NOT NULL

DELETED
    before_json = NOT NULL
    after_json  = NULL

RENAME
    before_json = NOT NULL
    after_json  = NOT NULL

SCHEMA_CHANGE
    before_json = NOT NULL
    after_json  = NOT NULL

DATA_CHANGE
    before_json = NOT NULL
    after_json  = NOT NULL
```

Constraint:

```sql
CHECK (
    (
        kind = 'CREATED'
        AND before_json IS NULL
        AND after_json IS NOT NULL
    )
    OR
    (
        kind = 'DELETED'
        AND before_json IS NOT NULL
        AND after_json IS NULL
    )
    OR
    (
        kind IN ('RENAME', 'SCHEMA_CHANGE', 'DATA_CHANGE')
        AND before_json IS NOT NULL
        AND after_json IS NOT NULL
    )
)
```

### Indici audit

```sql
CREATE INDEX ...
ON object_changes(object_id, occurred_at);
```

```sql
CREATE INDEX ...
ON object_changes(canonical_name);
```

Un eventuale indice `(kind, occurred_at)` non viene introdotto senza un caso d'uso concreto.

---

## 5. Canonical Object snapshot

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

I riferimenti autorevoli dello schema sono:

```text
template_id
template_version
```

Gli attachment `object_components` non fanno parte, per ora, del canonical Object snapshot.

---

## 6. Baseline complessiva

```text
objects
-------
id                  UUID PK
canonical_name      TEXT NOT NULL
template_id
template_version
properties_json     JSONB NOT NULL

CHECK canonical_name <> ''
FK exact ObjectTemplateVersion ON DELETE RESTRICT
INDEX canonical_name
```

```text
object_components
-----------------
parent_object_id
slot_name
child_object_id     PK

FK parent -> objects.id RESTRICT
FK child  -> objects.id RESTRICT
CHECK parent != child
CHECK slot_name <> ''
INDEX(parent_object_id, slot_name)
```

```text
object_changes
--------------
id                  PK
object_id           NOT NULL
canonical_name      TEXT NOT NULL
occurred_at         TIMESTAMPTZ NOT NULL
kind                TEXT NOT NULL
before_json         JSONB NULL
after_json          JSONB NULL

NO FK object_id -> objects
CHECK canonical_name <> ''
CHECK kind codificato
CHECK before/after coerenti con kind
INDEX(object_id, occurred_at)
INDEX(canonical_name)
```

---

## 7. Questioni relazionali deliberatamente aperte

```text
effective slot validation
child/slot target compatibility
ownership graph acyclicity
eventuale DB-level append-only enforcement di object_changes
```

Devono essere risolte analizzando le action Object e il relativo protocollo concorrente, senza introdurre prematuramente meccanismi globali.
