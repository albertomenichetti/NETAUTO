# M4 — Relationship.CREATE runtime closure and conflict discovery

**Status:** WIP / NON-NORMATIVE

## Scope

This note records the second half of the M4 discovery audit for factual `Relationship.CREATE`, after current model admission, endpoint admission, runtime-closure derivation, and property canonicalization have already produced one complete factual candidate.

Concurrency/restart realization is intentionally deferred to the later global concurrency phase.

## Current persisted realization already materializes conflict ownership

`runtime_relationship_resolutions` is not just an implementation child table. It is the persisted complete deterministic runtime closure of a factual Relationship, and its exact row identity is:

```text
(resolution_id, from_object_id, to_object_id)
```

The table primary key is exactly that tuple. Therefore it already acts as both:

```text
materialized runtime closure
+
authoritative exact-view ownership index
```

M4 should not introduce a second Relationship-specific conflict/materialization table for the same semantic space.

## Current duplicate pre-check information

After deriving the complete runtime closure, the current CREATE path performs:

```text
exact_relationship_id(
    selected_resolution_id,
    input_from_object_id,
    input_to_object_id,
)
```

and later:

```text
current_candidate_relationship_ids(complete_closure)
```

The selected exact view is necessarily one member of the complete derived closure. Therefore the first query is an informational subset of the second closure-wide ownership lookup.

Candidate M4 direction:

```text
one set-based closure-owner projection
```

is sufficient as the pre-check information source if a pre-check remains part of the final concurrency design.

Whether pre-checking should remain at all, or whether the runtime-resolution PK should be the first arbitration point followed by post-rollback classification, is explicitly deferred to the global concurrency phase.

## Conflict-owner classification must not re-certify the existing fact

The current path may route an observed conflicting Relationship through full `_validated()` semantic recertification. That can reload/revalidate:

- factual Relationship aggregate;
- RelationshipDefinition aggregate;
- endpoint Object template identities;
- the complete ObjectTemplate parent graph;
- exact RelationshipDefinitionVersion schema;
- exact DataType dependencies;
- canonical property semantics.

The CREATE conflict contract only needs a current conflicting owner identity/liveness classification. It does not need to re-certify the complete semantic validity of an already admitted persisted fact.

Candidate principle:

```text
conflict classification
    needs protected current owner identity
    does not need full semantic recertification
```

The exact locking/liveness proof remains deferred.

## Runtime closure DML

Current persistence inserts:

```text
1 Relationship root INSERT
N runtime_relationship_resolutions INSERTs
```

where current closure cardinality is bounded but can contain multiple rows.

Candidate M4 DML:

```text
1 Relationship root INSERT
1 bulk INSERT complete runtime closure
```

The full closure remains atomic. A primary-key collision on any exact view must fail the whole statement/UoW. `ON CONFLICT DO NOTHING` is not acceptable because it could materialize only a subset of the required closure.

## Lifecycle events

`LifecycleStore.insert_relationship_events()` already performs one bulk event INSERT and should remain so.

The current CREATE path performs a post-insert `relationship_views()` read to capture coherent historical metadata:

- current Resolution names;
- current endpoint Object canonical names;
- the exact complete runtime closure.

There is a possible M4 optimization: include endpoint canonical names and current Resolution names in the already-required admission projections and derive lifecycle views in memory from the candidate closure.

However this interacts directly with the concurrency rule that event metadata observed during concurrent Object/Definition renames must be coherent and must not mix half-old/half-new naming state.

Therefore:

```text
eliminate lifecycle metadata reread
    -> OPEN / concurrency-dependent
```

## Candidate data path for this half

```text
complete derived closure
        ↓
optional one set-based current-owner lookup
        ↓
no full semantic validation of observed existing owners
        ↓
1 INSERT factual root
1 bulk INSERT complete runtime closure
        ↓
PK exact-view arbitration
        ↓
coherent lifecycle metadata capture
        ↓
1 bulk INSERT lifecycle event set
```

## Discovery conclusions

- `runtime_relationship_resolutions` is already the correct closure materialization and exact-view ownership index.
- No new Relationship-specific conflict denormalization is justified.
- The selected-view pre-check is informationally redundant once the complete closure is known; one closure-wide ownership lookup is sufficient if a pre-check remains.
- Existing conflicting facts should not be fully semantically recertified merely to return their owner ID.
- Runtime closure persistence should become one bulk INSERT, preserving all-or-nothing semantics.
- Collision restart/arbitration mechanics remain deferred to the global concurrency phase.
- Elimination of the lifecycle-metadata reread remains OPEN pending the rename/coherence concurrency proof.
