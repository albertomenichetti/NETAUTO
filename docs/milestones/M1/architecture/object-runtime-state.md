# M1 — Object Runtime State

**Status:** DRAFT

## 1. Identity e stable type assignment

L'identità autorevole è esclusivamente:

```text
Object.id
```

`Object.id`:

- è opaco;
- è immutabile;
- viene generato esclusivamente dal kernel NETAUTO;
- M1 usa UUIDv4;
- non può essere specificato dal caller.

La PK database è final authority sull'unicità degli Object correnti.

M1 non introduce infrastruttura aggiuntiva per garantire il non-riuso storico di un UUID internamente generato.

Identifier esterni (cloud resource id, serial, VMware UUID, legacy CMDB id, ecc.) sono semanticamente distinti da `Object.id`.

Ogni Object appartiene stabilmente a una `ObjectTemplate` lineage:

```text
template_id
```

`template_id` non fa parte dell'identity ma è immutable type assignment nelle normali operation M1.

Normale schema evolution modifica solo:

```text
template_version
```

Eventuale cross-lineage reclassification è RFE controllata.

## 2. canonical_name

`canonical_name` è human/search metadata:

- non è identity;
- non è unique;
- è mutabile;
- non viene normalizzato automaticamente;
- deve essere non vuoto;
- è bounded; il limite numerico definitivo è dettaglio persistence/API da finalizzare.

Create:

```text
canonical_name omitted / None
    -> canonical_name = str(Object.id)

canonical_name provided, valid and non-empty
    -> use exactly provided value

canonical_name == ""
    -> invalid
```

Il fallback a `str(Object.id)` esiste soltanto alla create.

`RENAME` richiede un nuovo valore esplicito e modifica esclusivamente `canonical_name`.

## 3. Exact ObjectTemplateVersion pin

Ogni Object persiste:

```text
(template_id, template_version)
```

entrambi concreti.

Non esistono persisted references con semantica:

```text
latest
default
follow-current
```

## 4. Definitive validation closure

Dato un exact ObjectTemplateVersion `T@V`, la definitive closure dell'Object è derivata esclusivamente tramite exact persisted edges:

```text
T@V
-> exact parent OTV
-> exact parent OTV
-> ...
-> root exact OTV
```

e, per le effective properties:

```text
property
-> exact DataTypeVersion
```

Mai durante closure resolution vengono consultati:

```text
ObjectTemplate.default_version
DataType.default_version
latest/highest published version
```

La create-time validation closure comprende:

- stable target ObjectTemplate metadata rilevante;
- selected exact OTV;
- exact OTV ancestry chain;
- effective property declarations;
- exact DTV snapshots delle properties.

I component slots fanno parte dell'effective template schema ma non della runtime-property validation della create, perché l'Object nasce detached.

Una PUBLISHED target OTV è il consistency anchor della create. Grazie all'active-model-graph invariant, la create non deve ricertificare o lifecycle-lockare transitivamente ogni ancestor OTV/DTV.

Integrity violations incontrate durante resolution — missing exact dependency, cycle, malformed effective schema — causano failure, ma CREATE non riesegue la publication certification.

## 5. Object CREATE target resolution

CREATE supporta due modalità.

### 5.1 Explicit exact pin

Input concettuale:

```text
template_id = T
template_version = V
```

`T@V` deve:

- esistere;
- appartenere a `T`;
- essere `PUBLISHED` fino al commit;
- appartenere a una lineage `abstract=false`.

Nessun fallback.

### 5.2 Implicit default pin

Input:

```text
template_id = T
template_version omitted
```

Resolution:

```text
T.default_version
```

Se `default_version` è `NULL`, CREATE fallisce anche se esistono altre PUBLISHED version.

La selected default exact OTV deve rimanere PUBLISHED fino al commit e viene materializzata nel persisted Object pin.

M1 non usa `highest/latest PUBLISHED` per Object create.

## 6. Runtime property canonical state

Object CREATE non persiste raw input: persiste la complete canonical validated candidate.

Per ogni value:

```text
raw input
-> SCALAR/LIST shape validation
-> PrimitiveType parse
-> primitive canonicalization
-> exact DTV constraint validation
-> canonical value
```

LIST:

- ordered;
- homogeneous rispetto alla exact DTV;
- duplicate values ammessi;
- ogni item validato/canonicalizzato indipendentemente.

Unknown property:

```text
-> reject
```

JSON `null`:

```text
-> invalid
```

## 7. Semantic cardinality e canonical absence

Cardinalità:

```text
SCALAR optional -> 0..1
SCALAR required -> 1
LIST optional   -> 0..N
LIST required   -> 1..N
```

`required` riguarda il numero semantico di valori, non la mera presenza della JSON key.

M1 canonicalizza cardinalità zero come **property key assente**.

Quindi per optional LIST:

```text
absent
[]
```

sono semanticamente equivalenti e convergono entrambi a key assente.

Una persisted LIST presente è quindi non-empty.

`migration_default` non viene mai usato durante Object CREATE.

## 8. CREATE atomicity

La create costruisce prima una complete canonical candidate.

Poi current state e lifecycle event `CREATED` committano nella stessa Unit of Work.

Semantica:

```text
CREATED.before = absent
CREATED.after  = complete canonical Object snapshot
```

Lo snapshot deriva dalla stessa canonical candidate persistita nell'Object.

L'Object nasce detached.

## 9. Nessuna Object state_revision M1

M1 non introduce:

```text
Object.state_revision
```

Strong consistency viene garantita dai concurrency contract delle singole operation.

La scelta è sostenibile perché non esiste generic full-object update. Le mutation restano semanticamente strette.

Future optimistic revision/ETag è RFE.

## 10. RENAME

`RENAME` modifica esclusivamente:

```text
canonical_name
```

Non modifica o riscrive:

```text
template_id
template_version
properties
ownership
```

Una higher-level workflow può comporre più operation, ma le mutation restano semanticamente distinte.

`RENAME` e relativo lifecycle event committano atomicamente.

Per un event `RENAME`:

```text
before = complete canonical Object snapshot prima
after  = complete canonical Object snapshot dopo
```

L'unica differenza semanticamente ammessa è `canonical_name`.

## 11. DATA_CHANGE

M1 usa per-property mutation semantics, non un generic full-document replacement come primitive principale.

Command concettuale:

```text
SET property = value
REMOVE property
```

`SET`:

- richiede effective current property esistente;
- sostituisce l'intero valore della property;
- per LIST sostituisce l'intera list;
- non introduce item-level append/remove/index mutation;
- valida/canonicalizza rispetto alla current exact OTV closure.

`REMOVE`:

- richiede effective current property esistente;
- produce semantic cardinality zero;
- è valido solo se la final Object candidate resta valida;
- quindi una required property non può essere rimossa.

Per optional LIST:

```text
SET []
```

converge semanticamente a property assente.

Unknown SET/REMOVE causa failure.

Pipeline:

```text
read current Object
-> resolve current exact closure
-> apply all requested SET/REMOVE in memory
-> canonicalize affected values
-> validate complete final Object state
-> persist atomically
-> write DATA_CHANGE lifecycle event
```

Nessuna partial mutation.

Un request che dopo canonicalizzazione produce lo stesso semantic state è un no-op e non genera lifecycle event.

`DATA_CHANGE` deve essere fortemente consistente con concurrent `SCHEMA_CHANGE`: non può validare contro una old exact OTV e poi sovrascrivere state dopo un repin concorrente.

Per `DATA_CHANGE`:

```text
canonical_name unchanged
template_id unchanged
template_version unchanged
properties may change
```

## 12. Existing DEPRECATED schema state

Un Object già pinnato a una DEPRECATED OTV rimane semanticamente valido.

Mutation del data-plane che non creano un nuovo Object->OTV binding possono continuare a interpretare lo state tramite quella immutable historical exact closure.

La deprecazione non congela retroattivamente l'Object.

## 13. DELETE

M1 non supporta subtree delete.

DELETE:

- elimina esclusivamente l'Object richiesto;
- non esegue implicit detach;
- non elimina Relationship implicitamente;
- non effettua cleanup di altri domini.

Precondizione strutturale:

```text
outgoing ownership edges = 0
incoming ownership edge  = 0
```

L'Object deve quindi essere leaf **e detached**.

Eventuali Relationship/external references devono essere rimosse preventivamente tramite le relative operation.

DELETE e lifecycle `DELETED` sono atomici:

```text
DELETED.before = final canonical Object snapshot
DELETED.after  = absent
```

No `DETACH_FROM` impliciti vengono generati dalla delete perché l'Object deve essere già structurally isolated.

La future orchestration API può automatizzare una sequenza di operation atomiche M1, ma non modifica la primitive DELETE semantics.

## 14. DELETE concurrency

DELETE può committare solo se l'Object rimane isolato e non referenziato fino al commit.

Race semantica con nuove references:

```text
reference wins
    -> DELETE fails

DELETE wins
    -> reference creation fails
```

La persistence authority deve impedire implicit ownership cleanup. In particolare gli ownership reference verso parent/child devono avere semantica `RESTRICT`, non `CASCADE`.

Mutation dello stesso Object state e DELETE devono avere un ordine seriale.

## 15. Current-state read consistency

Primitive `GET Object` restituisce uno snapshot transazionalmente coerente di:

```text
id
canonical_name
template_id
template_version
canonical properties
```

Exact template pin e properties devono appartenere allo stesso committed state.

Ownership graph e lifecycle changelog sono read model distinti e non fanno parte obbligatoriamente della primitive Object snapshot.

Non è garantita repeatability tra richieste separate.

Un Object cancellato:

```text
GET current Object
    -> NotFound
```

Il kernel M1 non ricostruisce automaticamente current state dal lifecycle changelog.

Expanded/composite reads e historical `as-of` reconstruction sono RFE ad alta priorità M2.
