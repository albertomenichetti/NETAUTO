# RelationshipDefinition SET_DEFAULT — M4 discovery

Status: **TECHNICAL DISCOVERY CLOSED EXCEPT CONCURRENCY/PHYSICAL REALIZATION / WIP / NON-NORMATIVE**

This note is operation-specific source/evidence subordinate to `relationshipdefinition.md` and to the current RelationshipDefinition technical consolidation ledger.

## Ratified M4 technical direction

`SET_DEFAULT` changes only current mutable selection state on the RelationshipDefinition lineage.

The selected exact version must:

```text
exist in the same RelationshipDefinition
status == PUBLISHED
```

The reviewed M4 REST success contract is:

```text
204 No Content
```

Therefore older AS-IS/discovery work that reloaded and returned the complete RelationshipDefinition aggregate after mutation is superseded.

## No semantic-preparation phase

`SET_DEFAULT` does not require worker-side semantic preparation.

It does not consume:

```text
RDV property declarations
DataType / DataTypeVersion semantic payload
compiled RDV cache
relationship_definition_space
ObjectTemplate ancestry
historical property continuity
RDV revision
```

PostgreSQL remains the authority for the complete current admission predicate.

## Logical short-UoW path

Conceptually:

```text
SET_DEFAULT(definition_id, version)

current admission
    RelationshipDefinition exists
    exact RDV exists in same Definition
    exact RDV status == PUBLISHED

mutation
    RelationshipDefinition.default_version = version

commit
```

The operation is idempotent on current value:

```text
default_version == version
    -> successful 204
```

No response-only aggregate reconstruction or post-write reload is required.

## Cache/materialization boundary

No cache fill, cache invalidation or new denormalization is justified.

The immutable exact-RDV cache deliberately excludes lifecycle status and Definition default state, so it cannot prove SET_DEFAULT admission and does not need modification when the default pointer changes.

`relationship_definition_space` is independent from `default_version` and is untouched.

## Concurrency handoff

The material race is:

```text
SET_DEFAULT(D@V)
vs
DEPRECATE(D@V)
```

Required serializable outcome:

```text
SET_DEFAULT wins
    -> V becomes current default
    -> DEPRECATE cannot commit while V remains default

DEPRECATE wins
    -> V is no longer PUBLISHED
    -> SET_DEFAULT cannot commit V as default
```

Exact locking/rendezvous/statement realization remains architecture/concurrency work.

## Technical closure checkpoint

```text
RD SET_DEFAULT

semantic preparation
    -> NONE

authoritative state
    -> PostgreSQL only

reads/admission
    -> Definition existence
    -> exact target existence/status only

writes
    -> default_version only

cache
    -> NONE

post-write reload
    -> NONE

response
    -> 204
```
