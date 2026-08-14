# M1 — Object SCHEMA_CHANGE

**Status:** DRAFT — semantics frozen; concurrency realization aligned to REALIZE-09/10/15.

## 1. Responsabilità

`SCHEMA_CHANGE` modifica la exact ObjectTemplateVersion usata da un Object e migra deterministicamente il runtime state verso il target schema.

Non è type reclassification.

Per ogni normale schema change M1:

```text
source.template_id
=
target.template_id
=
Object.template_id
```

`template_id` resta immutabile.

## 2. Forward-only exact target

M1 permette esclusivamente:

```text
target_version > current_version
```

Non è richiesto che il target sia la versione immediatamente successiva.

Una migration:

```text
@3 -> @8
```

viene calcolata direttamente source-to-target.

Le versioni intermedie non costituiscono una migration chain e non vengono attraversate artificialmente.

Schema downgrade/rollback è RFE.

Il target è una **exact version richiesta** e deve rimanere `PUBLISHED` fino al commit.

## 3. Source e target definitive closures

Ogni migration usa due closure distinte.

### SourceClosure

Deriva esclusivamente dalla exact OTV attualmente pinnata dall'Object.

La source:

- esiste per via del current Object exact pin;
- può essere PUBLISHED o DEPRECATED;
- è immutable;
- non costituisce una nuova admission.

### TargetClosure

Deriva esclusivamente dalla exact target OTV richiesta.

La target:

- appartiene alla stessa template lineage;
- ha version maggiore della source;
- deve rimanere PUBLISHED fino al commit;
- costituisce un nuovo direct Object->OTV binding.

Entrambe le closure percorrono esclusivamente:

```text
exact parent OTV pins
exact property DTV pins
```

Mai:

```text
ObjectTemplate.default_version
DataType.default_version
latest/current version
```

La target PUBLISHED OTV è consistency anchor; l'active-model-graph invariant evita lifecycle re-certification transitiva della target closure durante ogni Object migration.

## 4. Property semantic identity

Per schema migration la stessa effective name non è sufficiente a definire continuity.

Normative migration key:

```text
PropertySemanticKey
=
(declaring_template_id, name)
```

`declaring_template_id` identifica la ObjectTemplate lineage che localmente dichiara la property nella effective exact closure.

Esempio:

```text
Parent / serial_number
!=
Child / serial_number
```

anche se il runtime key name coincide.

M1 non introduce stable `property_id`.

Una property rimossa e successivamente reintrodotta con lo stesso nome dalla **stessa declaring lineage** conserva la stessa historical semantic identity e le relative evolution constraints.

Remove/re-add non può essere usato per aggirare la stabilità di `datatype_id`, name o le altre evolution rules.

## 5. Property migration algorithm

Per ogni effective target property:

1. calcola la target `PropertySemanticKey`;
2. cerca la stessa key nella source closure;
3. applica le seguenti regole.

### 5.1 Matching source property con semantic value presente

Sono ammesse esclusivamente le transformation M1 già ratificate:

```text
SCALAR -> SCALAR
    identity shape

LIST -> LIST
    identity shape

SCALAR -> LIST
    source V -> singleton [V]
```

Il resulting value viene sempre validato e canonicalizzato contro la **target exact DTV**.

Se è valido:

```text
carry forward
```

Se è invalido:

```text
SCHEMA_CHANGE FAIL
```

Questo vale sia per target optional sia required.

`migration_default` non sostituisce mai automaticamente un source value presente.

`LIST -> SCALAR` non è una normale evolution M1.

### 5.2 Matching source property senza semantic value

Target optional:

```text
remain absent
```

Target required:

```text
use target migration_default
```

### 5.3 Target property semanticamente nuova

Se nessuna matching source `PropertySemanticKey` esiste:

```text
target optional
    -> absent

target required
    -> target migration_default
```

### 5.4 Source-only property

Una source property senza matching target semantic key viene rimossa dal runtime state.

Nessun extras/archive/preservation bucket.

La before snapshot del lifecycle event conserva il previous state.

## 6. Stesso effective name, diversa semantic key

Scenario:

```text
source:
    Parent / serial_number

target:
    Child / serial_number
```

Le properties sono semanticamente diverse.

La source property viene trattata come rimossa.

La target property viene trattata come nuova:

```text
optional -> absent
required -> migration_default
```

La coincidenza del JSON/effective name non introduce carry-forward e non causa failure speciale.

## 7. migration_default semantic boundary

Normative rule:

> `migration_default` fills absence; it never replaces existing information.

È utilizzato soltanto quando:

```text
target required
AND
no source semantic value exists to preserve
```

Non viene usato quando un source value esiste ma è target-incompatible.

## 8. Nessuna remediation/transform M1

M1 non permette di passare allo SCHEMA_CHANGE:

- target property replacement values;
- explicit target SET/REMOVE overrides;
- expression language;
- migration scripts;
- arbitrary coercions;
- truncate/clamp/first-element heuristics.

Un source value presente ma target-incompatible blocca la migration.

Controlled schema migration con explicit remediation/transformation è RFE.

## 9. Target component validation

A differenza di Object CREATE, SCHEMA_CHANGE deve considerare gli outgoing component attachments esistenti.

Per ogni runtime edge:

```text
ParentObject / slot_name -> ChildObject
```

si ricava dalla **source exact closure**:

```text
SlotSemanticKey
=
(declaring_template_id, name)
```

Nella target closure deve esistere lo stesso semantic slot.

Il solo `slot_name` coincidente non basta.

Se lo stesso slot esiste, il child deve essere ancora type-compatible con:

```text
target_slot.target_template_id
```

Se:

- semantic slot non esiste più;
- child non è target-compatible;

allora:

```text
SCHEMA_CHANGE FAIL
```

Nessun implicit detach/rebind.

Uno slot removed e successivamente reintroduced con lo stesso name dalla stessa declaring lineage conserva historical identity/evolution continuity.

## 10. Incoming ownership e Relationships

Incoming ownership dell'Object migrato non richiede revalidation perché child compatibility dipende da:

```text
Object.template_id
```

che rimane immutabile.

Le Relationships non richiedono revalidation per lo stesso motivo: Relationship endpoint compatibility è lineage-based e il normale SCHEMA_CHANGE non cambia `template_id`.

## 11. Atomicity

Conceptual Unit of Work:

```text
Object row FOR NO KEY UPDATE
-> reload complete current Object state
-> resolve SourceClosure(current exact OTV)

-> admit/stabilize exact target OTV FOR SHARE
-> resolve TargetClosure

-> migrate properties
-> validate outgoing attachments while parent Object owner is held
-> validate complete target canonical state

-> persist template_version + properties
-> persist lifecycle SCHEMA_CHANGE event
-> COMMIT
```

Il target `FOR SHARE` è `S-BINDING-ADMISSION`; l'Object non-key owner realizza `S-OBJECT-STATE` e, quando l'Object è parent, `S-PARENT-OWNERSHIP` per il current outgoing edge set.

Failure in qualsiasi punto:

```text
ROLLBACK ALL
```

Committed states del tipo:

```text
new template_version + old properties
old template_version + migrated properties
```

sono vietati.

## 12. DATA_CHANGE concurrency

`DATA_CHANGE` e `SCHEMA_CHANGE` sullo stesso Object hanno un ordine seriale tramite la stessa Object row `FOR NO KEY UPDATE` owner.

Dopo ogni eventuale wait la mutation ricarica il current complete Object state e deriva/rivalida la candidate da quello state.

È vietato:

```text
SCHEMA_CHANGE reads P1
DATA_CHANGE commits P2
SCHEMA_CHANGE migrates stale P1 and overwrites P2
```

Il concrete contract è REALIZE-09 in `concurrency-postgresql-realization-object-ownership.md` e nel canonical realization index.

## 13. Ownership concurrency — high risk, realization ratificata

Invariante al commit:

```text
for every outgoing attachment of parent P:

slot semantic key exists
in P current exact effective schema

AND

child.template_id is compatible
with current slot target
```

Race critica:

```text
T1 SCHEMA_CHANGE P
T2 ATTACH/DETACH on P
```

Semantica richiesta:

```text
ATTACH wins
    -> SCHEMA_CHANGE observes resulting edge
       and fails if target cannot preserve it

SCHEMA_CHANGE wins
    -> ATTACH validates against new current schema
       and fails if no longer admissible

DETACH wins
    -> SCHEMA_CHANGE observes the removal and may become admissible
```

PostgreSQL realization M1:

```text
SCHEMA_CHANGE(parent)
ATTACH(parent)
DETACH(parent)
    -> same parent Object row FOR NO KEY UPDATE owner
```

Per ATTACH, dopo parent stabilization e local validation, ogni real edge-add entra inoltre nel `OWNERSHIP_GRAPH_WRITE_GATE` per `S-OWN-CYCLE`; SCHEMA_CHANGE/DETACH non prendono quel global gate.

Dettaglio normativo: `concurrency-postgresql-realization-object-ownership.md` REALIZE-10/11/15.

## 14. Lifecycle event

Una schema migration riuscita produce un singolo:

```text
SCHEMA_CHANGE
```

con:

```text
before = complete canonical source Object snapshot
after  = complete canonical target Object snapshot
```

Non vengono prodotti DATA_CHANGE separati per il carry/default deterministico interno alla migration.
