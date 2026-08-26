# RelationshipDefinition DELETE_DRAFT discovery

Status: WIP / non-normative discovery for M4.

## Scope

Audit the current `RelationshipDefinition.DELETE_DRAFT` data path. Lock/concurrency redesign is intentionally deferred to the later global concurrency phase.

## Current behavior

After the current lock plan is acquired, the application loads the complete exact `RelationshipDefinitionVersion`, including all property declarations, then requires:

- `status == DRAFT`;
- `revision == expected_revision`.

It then deletes the exact version and commits.

## Finding: property payload is unnecessary

DELETE_DRAFT admission needs only:

```text
exact version exists
status
revision
```

The complete property declaration set does not participate in the decision and should not be loaded solely for this mutation.

Candidate M4 read path: use a lightweight exact-version header projection / locking read containing only identity, status and revision.

## Owned child cleanup

`relationship_definition_properties` is owned child state of the exact version and its FK to `relationship_definition_versions` uses `ON DELETE CASCADE`.

Therefore DELETE_DRAFT should delete the exact version root and rely on relational ownership for declaration cleanup. No explicit property deletion loop is needed.

## Cache behavior

DRAFT versions are mutable and are never admitted to the immutable runtime cache. DELETE_DRAFT therefore has no cache invalidation or warm-up responsibility.

## Deferred concurrency question

A later concurrency-design phase may evaluate whether the operation can safely become a conditional single-statement delete, conceptually:

```sql
DELETE FROM relationship_definition_versions
WHERE relationship_definition_id = :definition_id
  AND version = :version
  AND status = 'DRAFT'
  AND revision = :expected_revision
RETURNING ...;
```

That design must preserve the public distinction among:

- exact version not found;
- lifecycle state conflict;
- stale revision;
- successful deletion.

It must also be proven against the final M4 concurrency matrix. No locking change is proposed by this discovery note.

## Candidate conclusion

`RelationshipDefinition.DELETE_DRAFT` should not load property declarations. Status and revision are sufficient for admission, declaration rows are owned/cascading child state, and no cache or new denormalization is required. Conditional single-statement deletion remains deferred to the global concurrency phase.
