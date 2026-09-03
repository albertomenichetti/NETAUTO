# RelationshipDefinition DEPRECATE — M4 discovery

Status: **TECHNICAL DISCOVERY CLOSED EXCEPT CONCURRENCY/PHYSICAL REALIZATION / WIP / NON-NORMATIVE**

This note is operation-specific source/evidence subordinate to `relationshipdefinition.md` and to the current RelationshipDefinition technical consolidation ledger.

## Ratified semantic boundary

Only an exact `PUBLISHED` RelationshipDefinitionVersion may be deprecated.

Successful transition:

```text
PUBLISHED -> DEPRECATED
revision unchanged
```

The current `RelationshipDefinition.default_version` cannot be deprecated.

Existing factual Relationships pinned to the target exact version are **not** blockers. A DEPRECATED RDV remains a valid historical exact dependency for already-existing factual Relationships; deprecation only removes it from new lifecycle-sensitive admission.

The reviewed M4 success contract is:

```text
204 No Content
```

Therefore older discovery that loaded the complete exact property snapshot merely to return the mutated RDV is superseded.

## No semantic-preparation phase

`DEPRECATE` requires no worker-side semantic preparation.

It does not consume:

```text
RDV properties
DataType / DataTypeVersion semantic payload
historical property continuity
relationship_definition_space
ObjectTemplate ancestry
compiled RDV cache
factual Relationship count/list
```

PostgreSQL remains current-state authority for the lifecycle/default admission predicate.

## Logical short-UoW path

Conceptually:

```text
DEPRECATE(definition_id, version)

current admission
    RelationshipDefinition exists
    exact RDV exists in the same Definition
    exact RDV.status == PUBLISHED
    RelationshipDefinition.default_version != version

mutation
    exact RDV.status = DEPRECATED
    revision unchanged

commit
```

No post-write reload is required for the `204` response.

## Factual-reference boundary

Do not add a factual-reference blocker or diagnostic query.

```text
existing factual Relationship pinned to target RDV
    -> does NOT block DEPRECATE
```

This is a lifecycle rule, not an optimization shortcut.

## Cache/materialization boundary

The immutable exact-RDV cache follows semantic immutability rather than current lifecycle status.

```text
PUBLISHED -> DEPRECATED
    -> immutable cache entry remains valid
    -> no cache invalidation or rewrite
```

DEPRECATE does not modify the exact property snapshot, exact DTV pins, value modes, ordinals or compiled runtime semantics.

Cache presence never proves that an RDV is currently PUBLISHED, so PostgreSQL remains the authority for new-binding admission.

`relationship_definition_space` is independent from RDV lifecycle and is untouched.

## Concurrency handoffs

Exact locking/rendezvous realization remains architecture work. Discovery requires the following serializable outcomes.

### DEPRECATE vs SET_DEFAULT(target)

```text
SET_DEFAULT wins
    -> target becomes current default
    -> DEPRECATE cannot commit while it remains default

DEPRECATE wins
    -> target is no longer PUBLISHED
    -> SET_DEFAULT cannot commit it as default
```

### DEPRECATE vs CLEAR_DEFAULT

```text
CLEAR_DEFAULT wins
    -> if target had been default, a later DEPRECATE may proceed

DEPRECATE observes target still current default
    -> default_version_conflict
```

### DEPRECATE vs new factual Relationship binding

```text
DEPRECATE wins before factual CREATE final admission
    -> new binding cannot commit against the now-DEPRECATED RDV

factual CREATE binding commits first
    -> DEPRECATE may still commit afterward
    -> the existing factual reference is not a blocker
```

## Technical closure checkpoint

```text
RD DEPRECATE

semantic preparation
    -> NONE

reads/admission
    -> Definition current default
    -> exact target existence/status

writes
    -> PUBLISHED -> DEPRECATED only

revision
    -> unchanged

factual-reference query
    -> NONE

cache
    -> unchanged

relationship_definition_space
    -> unchanged

post-write reload
    -> NONE

response
    -> 204
```
