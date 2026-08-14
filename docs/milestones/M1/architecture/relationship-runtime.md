# M1 — Runtime Relationship

**Status:** DRAFT

## 1. Responsabilità e shape

Concettualmente:

```text
Relationship
------------
id
relationship_definition_id
source_object_id
target_object_id
```

M1 non introduce Relationship properties.

Relationship è un factual runtime graph edge distinto dall'ownership graph.

## 2. Runtime identity

L'identity autorevole è:

```text
Relationship.id
```

`id`:

- è opaco;
- è immutabile;
- viene generato esclusivamente dal kernel;
- M1 usa UUIDv4;
- non può essere specificato dal caller.

La tuple endpoint non è identity, ma è subject a edge uniqueness.

## 3. Endpoint compatibility

Data definition `D`:

```text
source Object S compatible iff:
S.template_id == D.source_template_id
OR
S.template_id descendant-of D.source_template_id

target Object T compatible iff:
T.template_id == D.target_template_id
OR
T.template_id descendant-of D.target_template_id
```

Compatibility dipende esclusivamente da:

```text
Object.template_id
stable ObjectTemplate lineage ancestry
```

Non dipende da:

```text
Object.template_version
Object properties
Object canonical_name
OTV default/current status
```

Poiché `Object.template_id` e ObjectTemplate parent lineage sono stable nelle normali operation M1, una Relationship admitted non viene invalidata da normale Object `SCHEMA_CHANGE`.

## 4. Generic graph semantics

Relationship non è component ownership.

Non applica:

```text
single owner
acyclicity
forest semantics
subtree lifecycle
implicit detach
```

Il graph Relationship può contenere cicli.

## 5. Self-loop

M1 ammette:

```text
source_object_id == target_object_id
```

quando lo stesso Object è type-compatible con entrambi gli endpoint contract della definition.

Nessun generic `source != target` invariant viene imposto.

## 6. Directed definition semantics

Per una definition non symmetric:

```text
(D, A, B)
!=
(D, B, A)
```

quando entrambi gli edge risultano type-compatible.

Source e target sono semantic roles distinti.

La Relationship persistita conserva sempre l'orientamento canonico della definition:

```text
source_object_id satisfies source contract
target_object_id satisfies target contract
```

Il verso da cui il caller naviga o invoca l'operazione non modifica questa representation.

## 7. Symmetric definition semantics

Per una definition symmetric M1:

```text
source_template_id == target_template_id
AND
forward_name == reverse_name
```

source e target non rappresentano ruoli semanticamente distinti.

Quindi:

```text
(D,A,B) == (D,B,A)
```

La persistence usa una canonical endpoint ordering deterministica esclusivamente come representation detail.

L'ordering tecnica non possiede domain meaning.

Due create inverse:

```text
CREATE(D,A,B)
CREATE(D,B,A)
```

convergono sulla stessa current Relationship.

Self-loop symmetric resta ammesso.

## 8. Runtime uniqueness

Per definition directed:

```text
at most one current Relationship
per exact (D, source, target)
```

Per definition symmetric:

```text
at most one current Relationship
per canonical unordered pair {A,B}
```

M1 non supporta parallel/multi-edge instances indistinguibili.

Una futura capability di typed Relationship properties potrà rilassare questa uniqueness qualora più edge distinti fra gli stessi endpoint abbiano state proprio.

## 9. CREATE admission

Command concettuale:

```text
CREATE Relationship(
    relationship_definition_id = D,
    endpoint A,
    endpoint B
)
```

L'API può essere invocata da qualunque navigation direction, ma il domain deve risolvere una canonical runtime orientation coerente con la definition.

Per una nuova edge devono valere al commit:

```text
D exists
both Objects exist
endpoint roles are type-compatible
edge uniqueness is preserved
```

Non servono:

```text
exact OTV closure
property validation
ownership validation
cycle traversal
graph-wide lock
```

## 10. CREATE idempotency

Se la stessa factual edge è già current:

```text
CREATE
    -> successful idempotent no-op / converge on existing Relationship
```

Nessun nuovo Relationship UUID viene creato.

Nessun lifecycle event duplicato viene prodotto.

Due concurrent identical CREATE possono entrambi essere osservabili come successo, ma una sola current Relationship viene materializzata.

Per symmetric definition, reverse-create è included nello stesso idempotency contract.

## 11. Navigation views

Una Relationship è navigabile da entrambi gli endpoint.

Per una directed edge persisted:

```text
source S -> target T
```

dal source:

```text
direction = OUTGOING
name = definition.forward_name
related_object_id = T
```

dal target:

```text
direction = INCOMING
name = definition.reverse_name
related_object_id = S
```

I directional names sono semantic labels, non chiavi sufficienti da sole a identificare il role.

Se lo stesso name è applicabile in più role, la navigation view conserva explicit `relationship_definition_id` e `direction`.

Per una symmetric edge:

```text
direction = SYMMETRIC
name = forward_name == reverse_name
related_object_id = other endpoint
```

Per un directed self-loop lo stesso Object ricopre entrambi i role. La view/lifecycle projection non deve perdere questa informazione: può usare `SELF` come presentation direction ma deve rendere disponibili entrambi i directional role/labels.

## 12. DELETE primitive

Kernel primitive:

```text
DELETE Relationship(relationship_id)
```

La delete è exact-ID based.

Casi:

```text
relationship exists
    -> remove exact edge + lifecycle event

relationship already absent
    -> successful idempotent no-op
```

Un retry tardivo di un vecchio `relationship_id` non può cancellare una nuova Relationship successivamente ricreata con la stessa semantic tuple.

M1 non definisce delete-by-tuple come kernel primitive.

## 13. DELETE effects

Runtime Relationship delete:

- rimuove soltanto l'exact edge indicata;
- non modifica Object;
- non modifica ownership;
- non elimina altre Relationship;
- non elimina RelationshipDefinition;
- non esegue cleanup implicito.

## 14. Object/definition delete interaction

Current Relationship reference blocca:

```text
Object.DELETE
RelationshipDefinition.DELETE
```

L'edge deve essere rimossa esplicitamente prima.

Nessuna cascade semantica viene usata.

## 15. Lifecycle events

Una reale edge creation produce:

```text
RELATIONSHIP_CREATED
```

Una reale edge removal produce:

```text
RELATIONSHIP_DELETED
```

Edge mutation ed event append sono una singola atomic UoW.

Idempotent no-op non produce eventi.

Persisted structural event orientation:

```text
object_id
    = canonical source endpoint

destination_object_id
    = canonical target endpoint
```

indipendentemente dalla navigation direction da cui il comando è stato richiesto.

L'event registra:

```text
relationship_id
relationship_definition_id

canonical_name
destination_canonical_name

relationship_forward_name
relationship_reverse_name
```

I directional labels devono appartenere allo stesso semantic definition snapshot della mutation.

I canonical names sono display metadata osservati in un coherent read snapshot della mutation; non introducono un concurrency dependency che serializzi genericamente Object.RENAME con ogni Relationship mutation.

`before_json` e `after_json` sono assenti.

## 16. Lifecycle read projection

Quando il lifecycle di Object X viene letto, lo stesso persisted Relationship event viene orientato rispetto a X.

Directed, X = source:

```text
direction = OUTGOING
name = relationship_forward_name
related_object = destination
```

Directed, X = target:

```text
direction = INCOMING
name = relationship_reverse_name
related_object = source
```

Symmetric:

```text
direction = SYMMETRIC
name = relationship_forward_name
```

Self-loop:

```text
direction = SELF
```

Per directed self-loop entrambi i role/labels devono restare rappresentabili.

Il verso con cui il caller ha invocato CREATE/DELETE non fa parte della semantic history.

## 17. Historical identifiers

Negli event Relationship:

```text
relationship_id
relationship_definition_id
object_id
destination_object_id
```

sono historical identifiers, non live foreign-key dependencies verso current state.

Gli event restano leggibili dopo delete di:

```text
Relationship
RelationshipDefinition
Object
```

Le informazioni denormalizzate rendono l'evento operativo anche se le entity correnti non sono più fetchabili.
