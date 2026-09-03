# RelationshipDefinition CLEAR_DEFAULT — M4 discovery

Status: **TECHNICAL DISCOVERY CLOSED EXCEPT CONCURRENCY/PHYSICAL REALIZATION / WIP / NON-NORMATIVE**

This note is operation-specific source/evidence subordinate to `relationshipdefinition.md` and to the current RelationshipDefinition technical consolidation ledger.

## Ratified M4 technical direction

`CLEAR_DEFAULT` changes only current mutable selection state on the RelationshipDefinition lineage.

The reviewed M4 REST success contract is:

```text
204 No Content
```

Therefore older AS-IS/discovery work that reloaded and returned the complete RelationshipDefinition aggregate after mutation is superseded.

## No semantic-preparation phase

`CLEAR_DEFAULT` has no exact-version operand and needs no worker-side semantic preparation.

It does not consume:

```text
RelationshipDefinitionVersion state
RDV properties
DataType / DataTypeVersion semantics
historical property continuity
relationship_definition_space
ObjectTemplate ancestry
immutable RDV cache
```

PostgreSQL is authoritative only for current RelationshipDefinition existence and current `default_version` state.

## Logical short-UoW path

Conceptually:

```text
CLEAR_DEFAULT(definition_id)

admission
    RelationshipDefinition exists

mutation
    RelationshipDefinition.default_version = NULL

commit
```

The operation is idempotent:

```text
default_version already NULL
    -> successful 204
```

A physical implementation may avoid a real row rewrite when the value is already NULL, but it must still distinguish:

```text
Definition absent
    -> 404 resource_not_found

Definition present + default already NULL
    -> 204 No Content
```

Exact statement shape remains architecture/physical work.

## Cache/materialization boundary

No cache fill, cache invalidation or new denormalization is justified.

The immutable exact-RDV cache excludes `default_version`; changing the pointer does not alter exact RDV semantics.

`relationship_definition_space` is independent from `default_version` and is untouched.

No post-write aggregate reload is required for the `204` response.

## Concurrency handoff

The material external consumer is factual `Relationship.CREATE` when the caller omits an explicit RelationshipDefinitionVersion and therefore resolves the owning Definition's current `default_version`.

Required current-state consequence:

```text
after CLEAR_DEFAULT is committed
    -> a new implicit version resolution cannot obtain the old default
    -> absent current default yields default_version_unavailable
```

The fate of a factual CREATE that had already resolved a legitimate exact default before CLEAR_DEFAULT commits belongs to the later cross-family concurrency closure; this operation-specific discovery does not invent the rendezvous mechanism.

## Technical closure checkpoint

```text
RD CLEAR_DEFAULT

semantic preparation
    -> NONE

authoritative state
    -> PostgreSQL only

reads/admission
    -> Definition existence only

writes
    -> default_version -> NULL only

cache/materialization
    -> NONE

post-write reload
    -> NONE

response
    -> 204
```
