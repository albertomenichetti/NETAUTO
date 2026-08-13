# M1 — ObjectTemplate Properties

**Status:** DRAFT

## 1. Local property declaration

Concettualmente:

```text
ObjectTemplateProperty
----------------------
name
position
datatype_id
datatype_version
value_mode
required
migration_default
```

La property appartiene a una exact ObjectTemplateVersion.

## 2. Exact DataTypeVersion pin

Ogni property persiste sempre un exact:

```text
(datatype_id, datatype_version)
```

Nuovi binding/rebinding possono essere:

- explicit: exact DTV specificata;
- implicit: `datatype_version` omessa e risolta tramite `DataType.default_version`.

L'implicit resolution materializza sempre l'exact pin.

Una nuova admission/rebinding richiede exact DTV `PUBLISHED` fino al commit.

`create-next` clona il binding storico della source senza opportunistic upgrade.

Un DRAFT può quindi contenere exact DTV ormai `DEPRECATED`; la publish finale richiede active dependencies `PUBLISHED`.

## 3. Value mode

M1 supporta:

```text
SCALAR
LIST
```

`SCALAR` contiene al massimo un valore.

`LIST` è una sequenza ordinata di zero o più valori omogenei.

Ogni item della LIST viene validato e canonicalizzato usando la stessa exact DataTypeVersion pinnata dalla property.

Fuori M1:

- SET semantics;
- unique-items;
- generic `min_count` / `max_count`;
- tuple;
- map;
- nested collections;
- heterogeneous collections.

## 4. Required

`required` ha un solo significato:

> la property deve avere almeno un valore.

Cardinalità:

```text
SCALAR + required=false -> 0..1
SCALAR + required=true  -> 1
LIST   + required=false -> 0..N
LIST   + required=true  -> 1..N
```

Una LIST required vuota è invalida.

L'assenza di una LIST optional e una LIST optional vuota sono semanticamente entrambe cardinalità zero.

Per canonical Object runtime state M1, cardinalità zero viene rappresentata con property key assente.

## 5. migration_default

`migration_default` è metadata esclusivamente per Object schema migration/repinning.

Non è un creation default.

Regole M1:

```text
required=false
    -> migration_default MUST be absent

required=true + SCALAR
    -> migration_default = exactly one concrete valid value

required=true + LIST
    -> migration_default = non-empty ordered list of valid values
```

Ogni valore deve essere valido e canonicalizzato secondo la exact DTV pinnata.

`SQL NULL` significa assenza.

JSON `null` non è un domain value valido.

Durante Object create il caller deve fornire esplicitamente tutti i valori required; il kernel non usa automaticamente `migration_default`.

Durante Object schema migration:

> `migration_default` fills absence; it never replaces existing information.

Se un source semantic value esiste ma non è valido nel target, lo schema change fallisce invece di sostituirlo automaticamente.

## 6. Effective property identity

Il `name` identifica semanticamente una property nell'effective schema.

I property names devono essere univoci nell'intero effective schema.

Una child template non può:

- override;
- shadow;
- remove

una property inherited.

L'autorità sulla definizione di una inherited property resta nella lineage che l'ha dichiarata.

M1 non introduce una stable `property_id`.

### 6.1 Historical/migration semantic key

Quando serve riconoscere la continuità della stessa property tra due exact effective schemas, la semantic key è:

```text
PropertySemanticKey
=
(declaring_template_id, name)
```

dove `declaring_template_id` è la ObjectTemplate lineage che localmente dichiara la property.

Il solo effective name non è sufficiente.

Quindi:

```text
Parent / serial_number
!=
Child / serial_number
```

anche se il nome coincide.

Una property removed e successivamente reintroduced con lo stesso nome dalla **stessa declaring lineage** conserva la stessa historical semantic identity.

Le historical evolution constraints continuano quindi attraverso il gap; remove/re-add non può essere usato per aggirare stabilità di `name`, `datatype_id`, `value_mode` direction o altre evolution rules.

## 7. Property appena introdotta nel DRAFT

Una declaration introdotta per la prima volta in una DRAFT e mai comparsa in una PUBLISHED snapshot rimane editoriale.

Prima della first publication possono essere corretti:

- `name`;
- `datatype_id`;
- `datatype_version`;
- `value_mode`;
- `required`;
- `migration_default`;
- `position`;

purché ogni revise committata produca una DRAFT well-formed.

La first publication storicizza la property identity.

## 8. Evolution di una property storicizzata

Dopo first publication sono stabili nelle normali operation:

```text
name
datatype_id
```

Sono evolutivi:

```text
datatype_version
required
migration_default
position
```

### 8.1 Value-mode evolution

M1 ammette una sola normale transition:

```text
SCALAR -> LIST
```

È una cardinality widening deterministica.

Durante Object migration:

```text
zero scalar values -> zero list values
scalar value V     -> [V]
```

La candidate finale viene comunque validata integralmente contro il target schema e la target exact DTV.

Non sono normali mutation M1:

```text
LIST -> SCALAR
cambio datatype_id verso un'altra DataType lineage
```

Se introdotte in futuro, richiederanno controlled property/data migration esplicite.

## 9. Remove e rename

Una local property storicizzata può essere rimossa in una versione successiva.

Durante Object migration verso uno schema che non contiene più tale semantic property, il relativo runtime value viene eliminato.

Non esistono preservation bucket, mapping o conversioni implicite.

Una inherited property non può essere rimossa dalla child.

Non esiste una normale rename operation per una property storicizzata.

Un cambio di naming ordinario richiede:

```text
version N
    -> remove old property

version N+1
    -> add new property name
```

Non esiste equivalenza automatica tra vecchia e nuova property.

Un eventuale rename con data preservation sarà un controlled property migration.

## 10. Position e ordering

`position` è presentation metadata locale:

- intero positivo;
- univoco tra le local properties della stessa OTV;
- gap ammessi;
- ordering crescente;
- nessuna rinumerazione automatica obbligatoria.

Non partecipa a identity, compatibility o migration semantics.

Effective property order:

```text
root local properties
+
next inheritance level local properties
+
...
+
leaf local properties
```

Ogni blocco locale è ordinato per `position`.

M1 non introduce interleaving/anchor globali tra inherited e local properties.

## 11. Naming

Property name:

```text
[a-z][a-z0-9_]*
```

max 64 caratteri.

Nessuna normalizzazione automatica.

Property e component slots condividono un unico effective member namespace; una property non può avere lo stesso nome di uno slot localmente o tramite inheritance.
