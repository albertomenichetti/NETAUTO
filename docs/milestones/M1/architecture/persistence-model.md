# M1 — PostgreSQL Persistence Model

**Status:** DRAFT — decisioni PERSIST-01..PERSIST-15 ratificate; freeze finale insieme alla restante architecture M1.

## 1. Scopo e autorità

Questo documento definisce il modello di persistenza PostgreSQL normativo per M1.

M1 supporta esclusivamente PostgreSQL. Non viene introdotta un'astrazione multi-backend e SQLite non è un backend supportato per il kernel M1.

Principio generale:

> il modello relazionale dichiara con PK, UNIQUE, FK, CHECK e NOT NULL gli stati strutturalmente impossibili che PostgreSQL può esprimere in modo trasparente; i predicate semantici cross-row, cross-aggregate, lifecycle e graph-wide restano responsabilità della Unit of Work e del concurrency contract.

Le semantic identity definite dai documenti di dominio restano authoritative. La forma fisica non introduce surrogate identity quando il dominio possiede già una exact tuple identity.

---

## 2. Authority table map — PERSIST-01

Tabelle authoritative M1:

### Model plane

```text
datatypes
datatype_versions
object_templates
object_template_versions
object_template_properties
object_template_components
relationship_definitions
relationship_resolutions
```

### Data plane

```text
objects
object_components
relationships
runtime_relationship_resolutions
```

### History

```text
object_lifecycle_events
```

Totale: **13 tabelle authoritative**.

Non esistono in M1:

- tabella `primitive_types`;
- effective-schema cache authoritative;
- runtime property EAV;
- ancestry closure table;
- reverse dependency authority table;
- generic member table property/slot;
- surrogate row identity per DTV/OTV/runtime relationship resolution.

Regola di delete fisica:

> `CASCADE` è ammesso solo root -> owned child state dello stesso aggregate; cross-aggregate/current-domain references usano normalmente `RESTRICT`; historical identity nel changelog non usa live FK.

---

## 3. Exact version identities e lineage defaults — PERSIST-02/PERSIST-03

### 3.1 DataTypeVersion

Identity fisica e semantica:

```text
PRIMARY KEY (datatype_id, version)
```

Nessun surrogate UUID per la version row.

`datatypes.default_version` è nullable e viene garantito strutturalmente tramite composite FK verso una version della stessa lineage.

### 3.2 ObjectTemplateVersion

Identity fisica e semantica:

```text
PRIMARY KEY (template_id, version)
```

Nessun surrogate UUID per la version row.

`object_templates.default_version` è nullable e usa composite FK verso una exact version della stessa lineage.

### 3.3 Parent lineage e exact parent pin

`object_templates.parent_template_id` è la sola authority della stable parent lineage.

Ogni non-root `object_template_versions` persiste anche:

```text
parent_template_id
parent_version
```

come exact parent dependency.

Per root lineage:

```text
object_templates.parent_template_id IS NULL
AND
OTV parent_template_id IS NULL
AND
OTV parent_version IS NULL
```

Per non-root lineage il pair OTV è non-null e deve identificare una exact parent OTV esistente.

L'uguaglianza:

```text
object_template_versions.parent_template_id
=
object_templates.parent_template_id
```

è un invariant UoW, non un trigger baseline.

### 3.4 Perché `parent_template_id` è intenzionalmente duplicato

Esempio:

```text
Router.parent = NetworkDevice
Router/v1 -> NetworkDevice/v2
Router/v2 -> NetworkDevice/v4
```

`parent_version=4` da solo non identifica la parent OTV perché `version` non è globalmente unique. L'exact identity è `(template_id, version)`.

Un surrogate `parent_otv_id` è rifiutato perché introdurrebbe una seconda technical identity per una entity che il dominio identifica già con la exact tuple.

Questa denormalizzazione non deve essere “normalizzata via” senza riaprire PERSIST-02.

---

## 4. ObjectTemplate declaration snapshots — PERSIST-04

Le local declarations sono separate:

```text
object_template_properties
object_template_components
```

Physical declaration snapshot key:

```text
(template_id, template_version, name)
```

Non esistono `property_id`, `slot_id` o generic member identity.

La historical semantic identity resta derivata:

```text
PropertySemanticKey = (declaring_template_id, name)
SlotSemanticKey     = (declaring_template_id, name)
```

La declaring lineage di una local declaration coincide con `template_id` della OTV owner.

### Property persistence

Ogni property persiste l'exact DTV pin:

```text
datatype_id
datatype_version
```

con composite FK `RESTRICT`.

`migration_default` è nullable canonical JSONB.

Constraint strutturale valido:

```text
required = false -> migration_default IS NULL
```

`position` è positivo e unique all'interno delle local properties della OTV.

### Component persistence

Ogni component persiste:

```text
target_template_id
```

come stable ObjectTemplate-lineage FK `RESTRICT`.

`position` è positivo e unique all'interno dei local components della OTV.

Property e slot condividono semanticamente un effective member namespace, ma il relativo cross-table/effective-closure invariant è UoW-enforced.

Owned declarations vengono eliminate con la owning OTV tramite `CASCADE`.

---

## 5. Object row — PERSIST-05

`objects` persiste almeno:

```text
id
canonical_name
template_id
template_version
properties
```

`id` è native PostgreSQL UUID e PK.

`(template_id, template_version)` è composite FK `RESTRICT` verso la current exact OTV.

`template_id` viene persistito direttamente perché è stable runtime type assignment e supporta ancestry/relationship/ownership compatibility senza ricostruzioni improprie.

`canonical_name`:

- `TEXT NOT NULL`;
- lunghezza semantica M1 `1..255`;
- non unique;
- nessuna identifier grammar.

`properties`:

```text
JSONB NOT NULL
```

con check che il top-level JSON sia un object; `{}` rappresenta zero properties.

Non esiste EAV runtime.

Il domain/UoW produce esclusivamente canonical JSON-compatible state. JSON key order non ha semantica; LIST order sì. Optional zero-cardinality = key assente. JSON `null` non è un domain value valido.

Non esiste `Object.state_revision` M1.

---

## 6. Ownership persistence — PERSIST-06

Tabella:

```text
object_components(
    child_object_id,
    parent_object_id,
    slot_name
)
```

Authority single-owner:

```text
PRIMARY KEY (child_object_id)
```

Entrambe le Object FK sono `RESTRICT`, mai `CASCADE`.

Constraint locale:

```text
parent_object_id <> child_object_id
```

Indice di navigazione/parent lookup:

```text
(parent_object_id, slot_name, child_object_id)
```

Non esiste `ownership_edge_id`.

Il runtime edge persiste `slot_name`, non una FK verso una exact slot declaration: l'edge è interpretato contro la **current exact effective schema closure del parent**. Un FK verso una exact declaration version-pin-nerebbe impropriamente l'edge.

`slot_declaring_template_id` non viene duplicato in `object_components`. La current `SlotSemanticKey = (declaring_template_id, slot_name)` è derivata dalla current exact effective closure del parent ed è l'unica semantic authority del current edge. Persistirla anche nella runtime row introdurrebbe una seconda authority da mantenere coerente senza aggiungere informazione necessaria al current ownership fact.

Conseguenza normativa: ogni current `object_components` row deve risolvere esattamente uno slot nella current exact schema del parent e il child deve restare lineage-compatible con quel current slot. `SCHEMA_CHANGE` è tenuto a preservare questa proprietà e non può lasciare legacy edge non rappresentati dal target schema. Una persisted ownership row non risolvibile contro il current parent schema è invariant corruption, non uno stato supportato da DETACH o da una historical fallback lookup.

Slot validity, child lineage compatibility e acyclicity sono UoW/concurrency invariants.

---

## 7. Relationship R2 persistence — PERSIST-07

### 7.1 Model plane

```text
relationship_definitions(
    id,
    symmetric
)
```

PK `id` UUID.

```text
relationship_resolutions(
    id,
    relationship_definition_id,
    from_template_id,
    to_template_id,
    name
)
```

PK `id` UUID.

Definition -> Resolution è owned child state e usa `CASCADE`.

Endpoint ObjectTemplate lineage FK usano `RESTRICT`.

È ammessa una defensive exact-child uniqueness:

```text
UNIQUE (
  relationship_definition_id,
  from_template_id,
  to_template_id,
  name
)
```

La complete Definition shape resta UoW-enforced.

### 7.2 Runtime factual aggregate

```text
relationships(
    id,
    relationship_definition_id
)
```

PK `id`; Definition FK `RESTRICT`.

```text
runtime_relationship_resolutions(
    relationship_id,
    relationship_definition_id,
    resolution_id,
    from_object_id,
    to_object_id
)
```

Authority exact resolved-view uniqueness/factual convergence:

```text
PRIMARY KEY (
    resolution_id,
    from_object_id,
    to_object_id
)
```

Non esiste surrogate runtime-row id.

Relationship -> runtime rows usa `CASCADE` perché sono child state dello stesso factual aggregate.

Resolution e Object references usano `RESTRICT`.

Indice aggregate load/delete:

```text
(relationship_id)
```

### 7.3 Denormalizzazione intenzionale `relationship_definition_id`

`runtime_relationship_resolutions.relationship_definition_id` duplica un dato derivabile sia dalla Relationship header sia dalla Resolution.

Authority:

```text
relationships.relationship_definition_id
relationship_resolutions.relationship_definition_id
```

devono concordare.

La duplicazione permette composite FK declarative:

```text
(relationship_id, relationship_definition_id)
    -> relationships(id, relationship_definition_id)

(resolution_id, relationship_definition_id)
    -> relationship_resolutions(id, relationship_definition_id)
```

così PostgreSQL impedisce che una runtime row mescoli Relationship e Resolution appartenenti a Definition diverse.

Per supportare tali FK servono technical UNIQUE:

```text
relationships(id, relationship_definition_id)
relationship_resolutions(id, relationship_definition_id)
```

anche se `id` è già PK. Questi UNIQUE sono **constraint-support structures**, non nuove business identity.

La normalized alternative senza il datum duplicato è stata rifiutata perché perderebbe la possibilità di esprimere declarativamente il same-Definition invariant senza trigger/domain SQL complesso.

Questa denormalizzazione non deve essere rimossa senza riaprire PERSIST-07.

Complete closure, factual endpoint-pair coherence e endpoint admission restano UoW invariants.

---

## 8. Lifecycle persistence — PERSIST-08/PERSIST-09

Una sola tabella:

```text
object_lifecycle_events
```

con colonne tipizzate almeno:

```text
id
occurred_at
kind

object_id
canonical_name

destination_object_id
destination_canonical_name

slot_declaring_template_id
slot_name

relationship_id
relationship_definition_id
relationship_name

before_state
after_state
```

`before_state` / `after_state` sono canonical JSONB per intrinsic snapshots. Structural metadata usa colonne tipizzate; non esiste generic event payload JSON.

Gli historical identity UUID nel changelog **non hanno live FK** verso current tables.

Event-family row shape usa CHECK dove ragionevole.

Append-only è kernel/application contract M1, non compliance-grade DB trigger immutability.

### Event identity

`id` è UUID row identity e deterministic ordering tie-breaker, ma non possiede domain semantics. Viene generato da PostgreSQL, non dall'application domain. L'application può usare `INSERT ... RETURNING id`.

Questo è intenzionalmente diverso dalle domain identity (`Object.id`, `Relationship.id`, Definition ids, ecc.), generate dal kernel/application.

### Timestamp authority

```text
occurred_at TIMESTAMPTZ NOT NULL
DEFAULT transaction_timestamp()
```

(`CURRENT_TIMESTAMP` è semanticamente equivalente in PostgreSQL).

Tutti gli event della stessa semantic UoW condividono quindi lo stesso transaction-start timestamp.

`occurred_at` **non** rappresenta commit order fisico e non è una global sequence. Ordering canonico:

```text
(occurred_at, id)
```

è deterministico, non una promessa di strict commit chronology.

---

## 9. PostgreSQL types — PERSIST-10/PERSIST-11

### Identity/versioning

- native PostgreSQL `UUID` per tutte le current/historical UUID columns;
- DTV/OTV exact identity `(UUID, INTEGER)`;
- `version`, `revision`, `position` = `INTEGER` con positive CHECK;
- nessuna sequence/identity per version allocation: `max(existing)+1`, con possibile riuso del massimo DRAFT eliminato.

### Closed vocabularies

M1 usa `TEXT + CHECK`, non PostgreSQL ENUM, per:

```text
status: DRAFT | PUBLISHED | DEPRECATED
value_mode: SCALAR | LIST
base_type: closed PrimitiveType catalog
```

BOOLEAN nativo per `abstract`, `symmetric`, `required`.

Model/member identifiers usano `TEXT + CHECK` grammar, non `CITEXT` e non `VARCHAR` come authority semantica.

`description` è nullable `TEXT`.

DTV `constraints` è canonical `JSONB NOT NULL`, con `{}` per zero constraint e top-level object CHECK.

---

## 10. Primitive persistence codec — PERSIST-12

M1 richiede un'unica canonical PrimitiveType persistence mapping riusata in:

- DTV constraints/enum;
- property `migration_default`;
- Object properties;
- lifecycle intrinsic snapshots.

Concettualmente esiste un unico `PrimitivePersistenceCodec`; il nome implementativo non è normativo.

Mapping:

```text
core.string    -> JSON string
core.integer   -> JSON integer number
core.number    -> canonical exact-decimal JSON string
core.boolean   -> JSON boolean
core.date      -> ISO YYYY-MM-DD string
core.datetime  -> canonical UTC string ending Z
core.ip        -> canonical IP string
core.ip_prefix -> canonical CIDR string
core.byte_size -> JSON integer number, exact bytes
```

### `core.number`

Canonical exact decimal string:

- no `+`;
- no exponent;
- no superfluous leading/trailing zero;
- no decimal point quando integral;
- negative zero canonicalizzato a `"0"`.

La rappresentazione differente da `core.integer` è intenzionale per preservare exact-decimal semantics attraverso JSON client/toolchain che non garantiscono arbitrary precision numbers.

### `core.datetime`

Canonical UTC con suffisso `Z`, massima precisione microsecondo. Precisione più fine con cifre non-zero viene rifiutata; nessun rounding arbitrario. Trailing fractional zero vengono rimossi.

### `core.ip_prefix`

Host bits non-canonicali sono invalid input e vengono rifiutati, non corretti.

Constraint values riusano ricorsivamente lo stesso codec.

---

## 11. Naming persistence — PERSIST-13

Per DataType e ObjectTemplate si persiste soltanto:

```text
namespace
name
```

Il fully-qualified identifier derivato non viene persistito.

`UNIQUE(namespace, name)` è per-domain-table.

`name` CHECK:

```text
[a-z][a-z0-9_]{0,63}
```

Namespace:

- stessi segment grammar;
- max 64 per segmento;
- max 255 totale.

`core` / `core.*` reservation resta application/domain admission: il DB non distingue il caller kernel da caller esterni.

Uppercase input è invalido; non viene normalizzato case-insensitively.

`Object.canonical_name` è invece human/search metadata `TEXT`, non unique, `1..255`, senza model-identifier grammar.

---

## 12. Delete/FK matrix — PERSIST-14

### CASCADE: soltanto owned child state

```text
DataType              -> DataTypeVersion
ObjectTemplate        -> ObjectTemplateVersion
ObjectTemplateVersion -> local Property/Component
RelationshipDefinition-> RelationshipResolution
Relationship          -> RuntimeRelationshipResolution
```

### RESTRICT: current cross-aggregate/domain reference

Inclusi almeno:

```text
OTV exact parent -> parent OTV
Property -> DTV
Component -> target ObjectTemplate lineage
Object -> exact OTV
Ownership parent/child -> Object
Relationship -> RelationshipDefinition
Resolution endpoints -> ObjectTemplate lineage
RuntimeResolution -> Resolution
RuntimeResolution from/to -> Object
```

Nessun `ON DELETE SET NULL` per current domain references.

`CASCADE` è cleanup fisico **dopo** che la UoW ha ammesso semanticamente la root delete; non è il meccanismo di admission.

Historical changelog identities non hanno FK.

---

## 13. Baseline indices — PERSIST-15

Si creano soltanto indici giustificati da constraint, FK support, invariant lookup o API/read path già M1.

Model/dependency:

```text
object_template_properties(datatype_id, datatype_version)
object_template_versions(parent_template_id, parent_version)
object_templates(parent_template_id)
object_template_components(target_template_id)
relationship_resolutions(from_template_id)
relationship_resolutions(to_template_id)
```

Objects/ownership:

```text
objects(template_id, template_version)
objects(canonical_name, id)
object_components(parent_object_id, slot_name, child_object_id)
```

`objects(canonical_name, id)` è un read-path index normativo introdotto da API-03.10 per l'exact `canonical_name` filter della Object collection. `id` resta la canonical Object pagination/order key; l'indice non trasforma `canonical_name` in identity o uniqueness.

Relationship runtime:

```text
runtime_relationship_resolutions PK(resolution_id, from_object_id, to_object_id)
runtime_relationship_resolutions(from_object_id)
runtime_relationship_resolutions(to_object_id)
runtime_relationship_resolutions(relationship_id)
relationships(relationship_definition_id)
```

Più i technical UNIQUE `(id, relationship_definition_id)` richiesti dalle composite FK di PERSIST-07.

Lifecycle:

```text
(occurred_at, id)
(object_id, occurred_at, id)
(destination_object_id, occurred_at, id)
(relationship_id, occurred_at, id)
(relationship_definition_id, occurred_at, id)
(kind, occurred_at, id)
(relationship_name, occurred_at, id)
    WHERE relationship_name IS NOT NULL
```

API-03.10 rende quindi normativi anche:

- `(kind, occurred_at, id)` per il first-class lifecycle `kind` filter;
- il partial index `(relationship_name, occurred_at, id) WHERE relationship_name IS NOT NULL` per l'exact lifecycle `relationship_name` filter.

Il precedente marker "indice su kind soltanto se una API/query requirement M1 lo giustifica" è chiuso: API-03.10 costituisce quella requirement.

Non vengono introdotti baseline:

- GIN sulle runtime Object properties;
- GIN sugli historical snapshots;
- ancestry closure table/index;
- reverse-dependency materialization.

---

## 14. Registro delle denormalizzazioni intenzionali

Ogni denormalizzazione M1 deve documentare sempre:

1. datum duplicato;
2. authority;
3. ragione della duplicazione;
4. constraint/FK/query resi possibili;
5. consistency mechanism;
6. normalized alternative rifiutata e motivo;
7. nota esplicita che non va rimossa senza riaprire la relativa PERSIST decision.

M1 ne possiede almeno due:

### DENORM-01 — `object_template_versions.parent_template_id`

- authority: `object_templates.parent_template_id`;
- duplicazione: exact parent pair nella OTV;
- scopo: exact composite parent OTV FK e lettura diretta della dependency;
- consistency: structural FK/null-pair DB + lineage-equality UoW;
- alternativa rifiutata: surrogate `parent_otv_id` / perdita dell'exact domain tuple;
- decisione: PERSIST-02.

### DENORM-02 — `runtime_relationship_resolutions.relationship_definition_id`

- authority: Relationship header + Resolution devono concordare;
- scopo: composite FK che impediscono cross-Definition mixing;
- consistency: declarative composite FK;
- alternativa rifiutata: normalized runtime row con same-Definition invariant solo implicito/UoW;
- decisione: PERSIST-07.

I technical UNIQUE necessari alle composite FK sono support structures, non denormalizzazioni né identity aggiuntive.

---

## 15. Non-decisioni e confine del documento

Questo documento non definisce da solo:

- il lock concreto di ogni pairwise race;
- la complete semantic concurrency matrix;
- API/error mapping;
- steps implementativi.

La Unit of Work, isolation e concurrency realization già ratificate sono definite in `persistence-uow-concurrency.md`.

La technology-agnostic safety matrix è definita in `concurrency-semantic-matrix.md` e precede logicamente ogni realization PostgreSQL.
