# M1 — ObjectTemplate Components

**Status:** DRAFT

## 1. Responsabilità

Una `ObjectTemplateComponent` dichiara un **named ownership slot** della specifica ObjectTemplateVersion.

Non è:

- un embedded object;
- una property;
- una generic Relationship.

Uno slot contiene semanticamente:

```text
0..N child Objects
```

Ogni child è un vero `Object` con propria identity, canonical name, exact ObjectTemplateVersion pin, runtime properties e possibili Relationships.

M1 non introduce required slots, min/max component cardinality o one-child-per-slot.

## 2. Target lineage

Ogni slot punta a:

```text
target_template_id
```

cioè a una ObjectTemplate lineage, non a una exact version.

Per definire lo slot è sufficiente che la target lineage esista.

Non è richiesto:

- `default_version` non-NULL;
- una exact target version;
- una current PUBLISHED target version.

La target lineage può essere `abstract`.

## 3. Polymorphic compatibility

Un child è compatibile con lo slot se:

```text
child.template_id == target_template_id
OR
child.template_id is descendant of target_template_id
```

La compatibility è lineage-polymorphic e non dipende dalla exact ObjectTemplateVersion del child.

Distinzione:

```text
exact ObjectTemplateVersion
    -> schema interno del singolo Object

lineage ancestry
    -> type compatibility dello slot
```

L'abstractness impedisce l'instantiation diretta di una lineage, non il suo uso come compatibility contract.

## 4. Slot identity e inheritance

Il `name` identifica semanticamente il ruolo dello slot nell'effective schema.

Dopo first publication il nome è immutabile nelle normali operation.

Uno slot introdotto soltanto nel DRAFT e mai pubblicato resta editoriale fino alla first publication.

Una child template non può:

- override;
- hide;
- remove

uno slot inherited.

## 5. Target evolution

Per uno slot storicizzato, la normale schema evolution M1 può cambiare `target_template_id` soltanto tramite **widening** verso un ancestor della target corrente.

Esempio ammesso:

```text
PhysicalNetworkInterface
    ->
NetworkInterface
```

Non sono normali mutation M1:

```text
NetworkInterface
    ->
PhysicalNetworkInterface
```

(narrowing)

oppure:

```text
NetworkInterface
    ->
StorageVolume
```

(lineage non correlata).

Un futuro narrowing potrà esistere soltanto come controlled component-slot migration con verifica/remediation degli attachment esistenti.

## 6. Slot removal

Uno slot locale può essere rimosso in una nuova ObjectTemplateVersion.

La publication della nuova version è **sempre consentita** indipendentemente dagli Object runtime esistenti.

Se un Object possiede attachment su uno slot rimosso o incompatibile, il suo futuro `SCHEMA_CHANGE` verso la nuova OTV deve fallire finché gli attachment non vengono rimediati esplicitamente.

Non esistono detach impliciti durante schema migration.

## 7. Position

`position` è presentation metadata locale:

- intero positivo;
- univoco tra local component slots della stessa OTV;
- gap ammessi;
- nessuna rinumerazione automatica obbligatoria.

Non partecipa alla compatibility.

Property ordering e component ordering restano domini separati.

## 8. Naming e shared member namespace

Component-slot name:

```text
[a-z][a-z0-9_]*
```

max 64 caratteri.

Nessuna normalizzazione automatica.

Properties e component slots condividono un unico effective member namespace:

```text
effective_property_names
INTERSECT
effective_component_names
=
empty
```

La regola vale localmente e attraverso inheritance.

## 9. Runtime ownership consequences

A runtime:

- uno stesso owner/slot può contenere `0..N` child;
- un child può appartenere al massimo a un owner/slot alla volta;
- self-attachment è vietato;
- l'ownership graph degli Object deve essere aciclico;
- la compatibilità di ogni attachment usa l'effective slot schema dell'owner e la lineage del child.

I concurrency contract di `attach`, `detach` e `SCHEMA_CHANGE` definiranno i meccanismi di enforcement.
