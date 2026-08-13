# ObjectTemplate Property `required=true` — Semantica di Dominio Ratificata

## 1. Scopo

Questo documento ratifica il comportamento di dominio associato alle properties di una `ObjectTemplateVersion` con:

```text
required = TRUE
```

e introduce la semantica di:

```text
migration_default
```

L'obiettivo è garantire che una futura migrazione/repinning di un Object verso una `ObjectTemplateVersion` più recente sia sempre possibile quando la nuova versione richiede una property che l'Object precedente poteva legittimamente non possedere.

## 2. Invariante fondamentale

È ratificato:

```text
required = TRUE
    => migration_default presente
```

Una property obbligatoria non può quindi esistere nella definizione di una `ObjectTemplateVersion` senza un `migration_default` valido.

Questo non obbliga il sistema a migrare gli Object esistenti.

Garantisce invece che, se una migrazione/repinning viene richiesta, esista sempre un valore utilizzabile per soddisfare una property obbligatoria mancante.

## 3. Significato di `migration_default`

`migration_default` è metadata di migrazione.

Non è un normale default di creazione.

La sua semantica è:

> fornire un valore compatibile con la property quando un Object esistente viene migrato/repinnato verso una `ObjectTemplateVersion` che richiede quella property e l'Object non possiede già un valore utilizzabile.

Il nome ratificato è:

```text
migration_default
```

## 4. Regola per `Object create`

Durante il normale `Object create`, `migration_default` non deve essere utilizzato per completare automaticamente input mancanti.

Se una property è:

```text
required = TRUE
```

il chiamante deve fornire esplicitamente il relativo valore.

Quindi:

```text
Object create
+
required property assente nell'input
=
errore
```

anche se la property possiede un `migration_default`.

Esempio:

```text
property:
    name = "hostname"
    required = TRUE
    migration_default = "unknown"
```

Input:

```text
{}
```

Esito:

```text
create rifiutata
```

Non è ammesso trasformare implicitamente l'input in:

```text
{
    "hostname": "unknown"
}
```

`migration_default` non modifica quindi il contratto di creazione dell'Object.

## 5. Regola per migrazione/repinning

Durante un workflow di migrazione/repinning verso una nuova `ObjectTemplateVersion`:

1. viene determinato il nuovo set di properties richiesto dalla versione target;
2. per ogni property `required = TRUE`, il sistema verifica se l'Object dispone già di un valore compatibile;
3. se il valore esiste ed è utilizzabile, viene preservato secondo il contratto di migrazione;
4. se il valore manca, viene utilizzato il `migration_default` definito dalla property target.

Esempio:

```text
ObjectTemplate v1
-----------------
hostname   required = TRUE
location   required = FALSE
```

Un Object conforme a v1 può essere:

```text
hostname = "router-01"
location = assente
```

Una nuova versione può definire:

```text
ObjectTemplate v2
-----------------
hostname   required = TRUE
location   required = TRUE
           migration_default = "unknown"
```

Il repinning:

```text
v1 -> v2
```

può quindi produrre:

```text
hostname = "router-01"
location = "unknown"
```

La presenza del `migration_default` garantisce che la nuova obbligatorietà di `location` non renda strutturalmente impossibile la migrazione.

## 6. Validità del `migration_default`

Quando presente, `migration_default` deve essere un valore di dominio valido per la specifica `DataTypeVersion` pinnata dalla property:

```text
(datatype_id, datatype_version)
```

La validazione deve quindi essere eseguita secondo esattamente quella versione del DataType.

Non è sufficiente che:

- il DataType esista;
- una qualsiasi versione del DataType accetti il valore;
- il valore sia genericamente rappresentabile come JSON.

Deve valere:

```text
validate(
    migration_default,
    exact DataTypeVersion(datatype_id, datatype_version)
) == valid
```

La definizione o revisione di una `ObjectTemplateVersion` deve essere rifiutata se il `migration_default` non è valido per la `DataTypeVersion` pinnata.

## 7. `NULL` non è un valore di dominio

È ratificato che `NULL` non è un valore valido di dominio per una property.

Di conseguenza:

```text
SQL NULL
```

può significare soltanto:

```text
migration_default assente
```

e:

```text
JSON null
```

non può essere usato come `migration_default`.

Per una property required:

```text
required = TRUE
```

deve quindi esistere un valore concreto e valido:

```text
migration_default != SQL NULL
migration_default != JSON null
```

## 8. Invariante da applicare alla definizione delle properties

La definizione di una property deve rispettare almeno:

```text
se required = TRUE:
    migration_default deve essere presente
    migration_default non può essere null
    migration_default deve validare contro la exact DataTypeVersion
```

In pseudocodice:

```text
if property.required:
    require property.migration_default is present
    require property.migration_default is not null
    validate_against_exact_datatype_version(
        property.migration_default,
        property.datatype_id,
        property.datatype_version,
    )
```

La violazione di uno di questi requisiti deve impedire la persistenza della definizione.

## 9. Separazione tra admission e migration

La semantica ratificata mantiene distinti due workflow.

### Object create

```text
required property
    -> valore obbligatoriamente fornito dal caller

migration_default
    -> ignorato come fallback di creazione
```

### Object migration / repinning

```text
required property già valorizzata
    -> preservare/usare il valore secondo il contratto di migrazione

required property senza valore utilizzabile
    -> usare migration_default
```

Questa separazione è intenzionale.

`migration_default` garantisce la migrabilità, non riduce la severità del contratto di creazione.

## 10. Garanzia risultante

L'invariante:

```text
required = TRUE
    => migration_default valido e non-null
```

garantisce che l'introduzione o la trasformazione di una property in obbligatoria non renda, per la sola assenza di quella property sugli Object precedenti, impossibile un futuro repinning verso la nuova `ObjectTemplateVersion`.

La garanzia è:

```text
possibilità di migrazione
```

non:

```text
migrazione automatica obbligatoria
```

e non:

```text
default automatico durante Object create
```

Questa semantica costituisce la baseline di dominio ratificata da implementare per le properties `required = TRUE`.
