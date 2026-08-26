# M4 WIP — ObjectTemplate DELETE_LINEAGE discovery

Status: WIP / NON-NORMATIVE

## Scope

Operation-by-operation M4 discovery for `ObjectTemplate.DELETE_LINEAGE`. This note records current findings only; locking/concurrency redesign is deferred to the global concurrency phase.

## Current data path

The current operation acquires the model-root delete gate and an ObjectTemplate header lock, derives current external blockers, then deletes the lineage. Persistence first clears `default_version` and then deletes the lineage so that the circular reference between lineage default and owned exact versions is broken before cascade deletion.

Current blocker classes are derived dynamically:

- child ObjectTemplate lineages whose `parent_template_id` is the target lineage;
- external ObjectTemplate component declarations whose `target_template_id` is the target lineage;
- Objects whose `template_id` is the target lineage;
- RelationshipResolution endpoints whose `from_template_id` or `to_template_id` is the target lineage.

The current implementation obtains those counts with four separate `COUNT(*)` statements.

## M4 findings

### Do not add reverse-reference denormalization for this operation

`DELETE_LINEAGE` is a rare model-plane mutation. Its external blockers should continue to be derived from current PostgreSQL truth rather than introducing dedicated reverse-reference materializations only to optimize deletion.

The four current counts could eventually be projected by one statement containing four scalar subqueries if reducing round trips is useful, while retaining the current diagnostic counts. This is secondary and does not justify new persisted semantic state.

### Stable ancestry materialization is owned derived state

If M4 introduces a stable lineage closure such as:

```text
object_template_ancestry
    descendant_template_id
    ancestor_template_id
    depth
```

its rows are derived from the stable lineage graph and must be owned by that graph. They must disappear automatically when the corresponding lineage is deleted, preferably through FK/cascade ownership rather than application-level cleanup.

The closure must never become an independent delete blocker.

A deletion that is otherwise admissible cannot leave surviving descendants whose ancestry still contains the deleted lineage: any descendant path necessarily contains a direct child, and the existing child-lineage blocker already makes such a deletion inadmissible.

### Immutable effective-schema materializations are owned by exact versions

If M4 introduces immutable materialized effective schema rows for PUBLISHED/DEPRECATED exact versions, those rows are derived state owned by their exact ObjectTemplateVersion.

Deleting the lineage should therefore delete, by ownership/cascade:

```text
ObjectTemplate lineage
    -> exact versions
        -> local declarations
        -> immutable effective properties/components
```

No member-by-member cleanup should be required in application code.

### Worker-local immutable cache requires no distributed invalidation

A worker may retain stale immutable ObjectTemplate cache entries after a lineage has been deleted. This is acceptable under the M4 cache model because cache presence never proves current existence or admissibility.

Any later public operation that requires the current existence of that lineage/version must still consult PostgreSQL current truth.

## Candidate first-phase conclusion

`ObjectTemplate.DELETE_LINEAGE` does not justify new reverse-reference denormalization. Stable ancestry and immutable effective-schema materializations must be pure owned/derived state removed automatically with the aggregate. Existing blocker derivation may optionally be collapsed into one diagnostic set-based statement, but locking and concurrent-reference safety remain deferred to the global concurrency phase.

A design test for M4 denormalization is therefore: adding derived materializations must not make lineage deletion semantically more complex. If it does, ownership has likely been modeled incorrectly.
