# RelationshipDefinition CLEAR_DEFAULT — M4 discovery

Status: WIP / NON-NORMATIVE

## Scope

Audit of `RelationshipDefinition.CLEAR_DEFAULT` for M4 data-access, denormalization and cache implications. Concurrency realization is intentionally deferred to the global concurrency phase.

## Current behavior

The current application path:

1. acquires the RelationshipDefinition header lock;
2. sets `default_version = NULL`;
3. reloads the complete RelationshipDefinition aggregate;
4. commits and returns the complete aggregate.

The reload is required by the current public response shape, which returns the complete RelationshipDefinition including current Resolution names.

## M4 candidate

No exact RelationshipDefinitionVersion state is needed for CLEAR_DEFAULT. There is no target version, lifecycle validation, property-schema validation, or dependency resolution.

Prefer a single PostgreSQL mutation/projection statement that:

- targets the requested RelationshipDefinition;
- sets `default_version = NULL`;
- distinguishes missing Definition from success;
- returns the complete current RelationshipDefinition projection, including current Resolutions, in the same statement.

Conceptually:

```text
UPDATE relationship_definitions
SET default_version = NULL
WHERE id = :definition_id
        ↓
project updated Definition + current Resolution set
```

A data-modifying CTE or equivalent projection can realize the exact SQL shape later.

## Cache

Do not use or widen the stable RelationshipDefinition topology cache for this operation.

The candidate stable cache intentionally excludes mutable fields:

- `default_version`;
- `RelationshipResolution.name`.

The public response requires current Resolution names, so PostgreSQL remains the correct source for the returned aggregate.

## Denormalization

No new denormalization is justified by CLEAR_DEFAULT.

## Deferred concurrency question

The semantic rendezvous with factual `Relationship.CREATE` when the caller omits an explicit RelationshipDefinitionVersion remains open for the global concurrency phase:

```text
CLEAR_DEFAULT
      ↕
Relationship.CREATE using implicit current default
```

Do not redesign this locking interaction during the current operation-by-operation data-access audit.

## Candidate finding

`RelationshipDefinition.CLEAR_DEFAULT` can target one PostgreSQL `UPDATE + complete aggregate projection` statement. It needs no exact-version read, no cache interaction and no new denormalization. Concurrency with implicit-default factual Relationship creation remains deferred.
