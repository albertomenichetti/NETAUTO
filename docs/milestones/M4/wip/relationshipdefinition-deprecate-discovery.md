# RelationshipDefinition DEPRECATE — M4 discovery

Status: WIP / NON-NORMATIVE

## Scope

Audit of current `RelationshipDefinition.DEPRECATE` data access, cache behavior, and candidate M4 simplifications. Concurrency/locking realization remains deferred to the later global concurrency phase.

## Current semantic facts

- Only a `PUBLISHED` exact RelationshipDefinitionVersion can be deprecated.
- The current `default_version` cannot be deprecated.
- `PUBLISHED -> DEPRECATED` is irreversible.
- A `DEPRECATED` exact version remains a valid historical exact dependency for already-existing factual Relationships.
- Existing factual Relationships pinned to the target version are therefore not a deprecation blocker.
- `DEPRECATED` does not admit new lifecycle-sensitive direct bindings.

## Current data path

The current application flow acquires Definition/version locks, then loads:

1. the complete RelationshipDefinition aggregate, even though DEPRECATE only needs current `default_version` from it;
2. the complete exact RelationshipDefinitionVersion, including its properties;
3. after updating status to `DEPRECATED`, the exact version is loaded again only to build the response.

## Candidate M4 data path

Use one targeted projection that returns:

```text
Definition:
    exists
    default_version

Exact version:
    exists
    revision
    status
    complete properties
```

The property snapshot is still useful because the public mutation result is the complete exact version.

Then:

```text
project current state
    -> require exact version exists
    -> require status == PUBLISHED
    -> require default_version != target version

UPDATE exact status -> DEPRECATED
COMMIT
return the already-loaded exact snapshot with status changed in memory
```

No post-update exact-version reload is required if the status update succeeds.

## Factual references

Do not add a factual-reference blocker to DEPRECATE.

Current factual Relationships may remain pinned to a version after it becomes `DEPRECATED`; this is part of the lifecycle model. A helper such as `has_factual_reference()` therefore does not belong to the deprecation admission path.

## Cache behavior

Candidate immutable runtime cache:

```text
ImmutableRelationshipDefinitionVersionCache[(definition_id, version)]
    immutable property schema
    exact DataType pins
    compiled RuntimePropertySpec / validator structures
```

`PUBLISHED -> DEPRECATED` does not change the semantic payload, so the immutable cache entry remains valid and requires no invalidation.

Do not cache current lifecycle admission in this immutable cache. Cache presence must never prove that an exact version is still `PUBLISHED` or eligible for a new factual binding; PostgreSQL remains current-state authority.

## Concurrency deferred

The later global concurrency phase must rederive rendezvous for at least:

- DEPRECATE vs new `Relationship.CREATE` binding to the target exact version;
- DEPRECATE vs `SET_DEFAULT` / `CLEAR_DEFAULT`.

No lock redesign is proposed in this discovery note.

## Candidate conclusion

`RelationshipDefinition.DEPRECATE` should use a targeted current-default + exact-version projection, perform only the lifecycle/default checks it semantically needs, update status once, and return the in-memory exact snapshot with `DEPRECATED` status. Existing factual references do not block deprecation, and immutable runtime cache entries survive the lifecycle transition unchanged.
