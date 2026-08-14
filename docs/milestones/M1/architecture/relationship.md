# M1 — Relationship Architecture

**Status:** DRAFT — Relationship R2 semantics frozen; PostgreSQL persistence/concurrency realization and public command DTO contract complete; read/failure API details remain before final M1 architecture freeze.

## 1. Scopo

Questo documento è l'indice normativo dell'architettura `Relationship` per M1.

Documenti collegati:

- `relationship-definition.md` — aggregate `RelationshipDefinition`, symmetry, create/rename/delete e future versioning seam;
- `relationship-resolution.md` — model-plane resolved contract, semantic equivalence, conflict rules e capability reads;
- `relationship-runtime.md` — factual `Relationship`, runtime resolution closure, idempotency, delete e runtime reads;
- `relationship-concurrency.md` — transaction boundary, model/data-plane concurrency domains e high-risk races;
- `relationship-consistency-review.md` — consistency pass finale R2;
- `concurrency-postgresql-realization-relationship.md` — concrete PostgreSQL realization RC/RF/RA/ES + REALIZE-15;
- `persistence-model.md` / `persistence-uow-concurrency.md` — physical schema, FK/constraints, UoW/isolation/lock baseline;
- `concurrency-postgresql-test-matrix.md` — real-PG race coverage;
- `object-lifecycle-changelog.md` — lifecycle event-set semantics per Relationship;
- `object.md` — invariant cross-domain di lifecycle event-set atomicity;
- `api-wire-contract.md` — public command DTO/wire shape, API-03.7.

Le semantics e invarianti osservabili restano normative nei documenti di dominio; i meccanismi PostgreSQL non sono più “da definire” ma sono normativi nei persistence/realization contract sopra.

## 2. Modello concettuale

M1 separa quattro concetti:

```text
RelationshipDefinition
    -> stable identity e structural classification del relationship type

RelationshipResolution
    -> model-plane resolved semantic perspective

Relationship
    -> factual runtime association identity

RuntimeRelationshipResolution
    -> concrete object-relative resolved access path
       verso una factual Relationship
```

La `RelationshipDefinition` completa è un aggregate:

```text
RelationshipDefinition header
+
complete RelationshipResolution set
```

La factual `Relationship` completa è un aggregate:

```text
Relationship header
+
complete RuntimeRelationshipResolution closure
```

## 3. Principio resolved graph

La complessità di interpretazione viene pagata nel model-plane.

`RelationshipDefinition.CREATE/RENAME`:

- costruiscono/certificano il complete Resolution set;
- preservano symmetry shape;
- validano semantic equivalence;
- validano conflict fra Resolution;
- persistono un contratto già completamente risolto.

Il data-plane consuma quel contratto.

`Relationship.CREATE/DELETE` non reinterpretano forward/reverse/source/target semantics. Devono preservare soltanto:

- endpoint admission;
- factual uniqueness;
- complete runtime resolution closure;
- referential integrity;
- transactional/lifecycle atomicity.

## 4. Assenza intenzionale di source/target e forward/reverse

M1 non attribuisce un verso semanticamente privilegiato alla RelationshipDefinition.

Non esistono nel domain contract:

```text
source_template
target_template
forward_name
reverse_name
```

Una Relationship non-symmetric possiede due endpoint perspectives distinte.

Esempio:

```text
VM         -> Hypervisor / is_hosted_by
Hypervisor -> VM         / hosts
```

Nessuna delle due è semanticamente "forward".

## 5. Invarianti aggregate

- **REL-INV-001 — Definition identity:** `RelationshipDefinition.id` è l'identity autorevole e stabile del relationship type.
- **REL-INV-002 — Stable symmetry:** `RelationshipDefinition.symmetric` è structural contract immutabile.
- **REL-INV-003 — Resolution identity:** ogni `RelationshipResolution.id` è kernel-generated, stabile e indipendente dal mutable `name`.
- **REL-INV-004 — Stable resolution endpoints:** `from_template_id` e `to_template_id` non cambiano tramite normali mutation.
- **REL-INV-005 — Resolution lineage references:** resolution endpoints referenziano stable ObjectTemplate lineage, mai exact OTV.
- **REL-INV-006 — Resolution name validity:** ogni `RelationshipResolution.name` rispetta la naming grammar M1.
- **REL-INV-007 — Non-symmetric shape:** `symmetric=false` implica esattamente due Resolution reciproche con semantic names distinti.
- **REL-INV-008 — Symmetric shape:** `symmetric=true` implica un solo semantic name; same-template -> una Resolution, different-template -> due Resolution reciproche con lo stesso name.
- **REL-INV-009 — Complete definition aggregate:** header e complete Resolution set committano/mutano come un aggregate indivisibile.
- **REL-INV-010 — Definition semantic uniqueness:** due Definition con la stessa `symmetric + complete semantic Resolution set` non possono coesistere.
- **REL-INV-011 — Cross-definition resolution conflict freedom:** Resolution di Definition distinte non possono esporre lo stesso name su from/to lineage spaces entrambi sovrapposti.
- **REL-INV-012 — Model-plane certification:** runtime mutation non riesegue semantic-equivalence/conflict analysis già certificata dalla Definition mutation.
- **REL-INV-013 — Factual Relationship identity:** `Relationship.id` è l'identity autorevole della factual runtime association.
- **REL-INV-014 — Stable definition binding:** una current Relationship appartiene stabilmente a una `relationship_definition_id`.
- **REL-INV-015 — Resolution membership coherence:** ogni runtime resolution row di Relationship X referenzia una model Resolution appartenente a `X.relationship_definition_id`.
- **REL-INV-016 — Factual endpoint-pair coherence:** tutte le runtime rows di una Relationship rappresentano la stessa factual coppia di Object, eventualmente self-pair.
- **REL-INV-017 — Complete runtime closure:** il runtime resolution set committed è esattamente la deterministic complete closure della factual pair sotto la Definition.
- **REL-INV-018 — Exact resolved-view uniqueness:** una exact `(resolution_id, from_object_id, to_object_id)` appartiene ad al massimo una current factual Relationship.
- **REL-INV-019 — Resolution-based CREATE:** runtime Relationship CREATE viene espresso tramite `resolution_id + from_object_id + to_object_id`.
- **REL-INV-020 — Lineage-polymorphic endpoint admission:** runtime view compatibility dipende esclusivamente da stable `Object.template_id` lineage compatibility.
- **REL-INV-021 — No exact OTV dependency:** Object `template_version`, properties, defaults e OTV lifecycle non determinano runtime Relationship validity.
- **REL-INV-022 — Symmetric interchangeability:** per `symmetric=true` l'assegnazione dei due Object ai due capi è semanticamente intercambiabile.
- **REL-INV-023 — Non-symmetric role preservation:** per `symmetric=false` l'endpoint assignment espresso dalla selected Resolution non è intercambiabile.
- **REL-INV-024 — Self-loop allowed:** la factual endpoint pair può essere `(A,A)` quando admission e Definition shape lo consentono.
- **REL-INV-025 — No ownership semantics:** Relationship non applica single-owner, acyclicity, subtree o implicit composition rules.
- **REL-INV-026 — Idempotent CREATE:** una CREATE che trova già la exact resolved view converge sulla stessa factual Relationship e non produce nuova mutation/event set.
- **REL-INV-027 — Exact-ID DELETE:** runtime delete è exact `relationship_id` based ed è idempotente sull'assenza.
- **REL-INV-028 — No partial child mutation:** model/runtime Resolution child state non possiede CRUD/lifecycle pubblico autonomo.
- **REL-INV-029 — Runtime referential integrity:** current Relationship/RuntimeResolution referenziano current Definition/Resolution/Object coerenti.
- **REL-INV-030 — Definition delete safety:** RelationshipDefinition delete richiede zero factual Relationship correnti.
- **REL-INV-031 — Object delete safety:** Object delete richiede zero current Relationship association.
- **REL-INV-032 — Lifecycle semantic-view set:** ogni factual Relationship transition produce un event per ogni distinct object-relative semantic view, non per ogni runtime resolution row.
- **REL-INV-033 — Lifecycle event-set atomicity:** factual state transition, complete runtime closure mutation e required lifecycle event set committano o rollbackano insieme.
- **REL-INV-034 — Historical lifecycle references:** identifier e names nel changelog sono historical data, non live referential dependencies.
- **REL-INV-035 — Strong concurrent consistency:** nessun supported interleaving può committare uno stato che viola le invarianti sopra.

## 6. Public command DTO contract

API-03.7 in `api-wire-contract.md` è ora normativo per il transport M1.

In sintesi:

```text
RelationshipDefinition.CREATE
    symmetric=false
        -> exactly two unordered named perspectives {template_id,name}

    symmetric=true
        -> unordered two-element endpoint_template_ids
        -> one semantic name

RelationshipDefinition.RENAME
    non-symmetric
        -> complete unordered two-element {resolution_id,name} set

    symmetric
        -> one semantic name

RelationshipDefinition.DELETE
    -> no body / no cascade-force semantics

Relationship.CREATE
    -> exactly resolution_id + from_object_id + to_object_id

Relationship.DELETE
    -> exact relationship_id path identity / no body
```

Definition/Resolution/Relationship identities create-time restano kernel-generated. Nessun array ordering introduce source/target o forward/reverse orientation. Self-loop non viene rifiutato strutturalmente dal transport.

Questa sezione non sostituisce le domain validation in `relationship-definition.md` / `relationship-runtime.md`: aggregate shape, lineage admission, conflict/equivalence, factual convergence e symmetry semantics restano application/domain authority.

## 7. Modelling guideline

Una Relationship capability dovrebbe essere dichiarata sul template-space più generale per cui la semantics è corretta per tutti i discendenti:

```text
highest semantically correct,
lowest necessary
```

Non creare specialization duplicate soltanto per restringere artificialmente lo spazio di compatibility.

## 8. Future typed Relationship properties

M1 non introduce:

```text
RelationshipDefinitionVersion
Relationship properties
```

Il modello R2 fornisce un seam esplicito:

```text
RelationshipDefinition
    -> stable topology/navigation contract

future RelationshipDefinitionVersion
    -> exact typed property schema

Relationship
    -> factual association
    -> future exact definition-version pin
    -> future canonical properties

RuntimeRelationshipResolution
    -> stable resolved access paths
```

Future property/schema evolution non modifica `symmetric`, Resolution set, endpoint lineage o resolved graph topology.

## 9. Candidate future / RFE

- `RelationshipDefinitionVersion`;
- typed Relationship properties;
- exact RDV pin sulla factual Relationship;
- Relationship property schema migration;
- parallel/multi-edge factual instances se future properties giustificano state distinti;
- richer graph/composite reads;
- historical relationship reconstruction;
- controlled future mutation di structural relationship type soltanto tramite workflow espliciti, non generic update.

## 10. Technical-contract status

Le seguenti decisioni non sono più aperte:

```text
PostgreSQL physical schema e authoritative tables
PK/FK/UNIQUE/CHECK layout; no constraint-trigger baseline
model-plane Definition conflict serialization = transaction advisory gate
runtime exact-view authority = PK(resolution_id, from_object_id, to_object_id)
unique-collision behavior = whole-UoW rollback + fresh semantic convergence UoW
READ COMMITTED mutation isolation
ObjectTemplate ancestry authority = stable parent lineage; recursive lookup, no closure authority
lifecycle physical representation e one-statement Relationship metadata observation
runtime from_object_id / relationship / Definition lookup indices
RD.RENAME non-key owner = FOR NO KEY UPDATE; RD.DELETE = FOR UPDATE
Relationship DELETE exact-id owner = FOR UPDATE
RelationshipDefinition/Relationship public command DTO shapes = API-03.7
```

Restano aperti prima del coding freeze soltanto aspetti di transport/read/application non ancora chiusi:

- canonical read DTO shapes;
- public error/status taxonomy.
