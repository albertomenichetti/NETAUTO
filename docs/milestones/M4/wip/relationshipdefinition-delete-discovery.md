# RelationshipDefinition DELETE discovery

Status: WIP / NON-NORMATIVE

## Scope

First-phase M4 data-access / denormalization / cache audit for complete `RelationshipDefinition.DELETE`.

Locking and concurrency realization remain explicitly deferred to the later global concurrency phase.

## Current semantics

A RelationshipDefinition cannot be deleted while any current factual Relationship references one of its exact versions. Definition deletion removes the whole owned aggregate.

Owned state:

- RelationshipResolution rows belong to the Definition and are deleted with it.
- RelationshipDefinitionVersion rows belong to the Definition and are deleted with it.
- RelationshipDefinitionProperty rows belong to exact versions and are deleted with them.

External lifetime blocker:

- current factual Relationship rows reference exact RelationshipDefinitionVersion rows and therefore block Definition deletion.

## AS-IS observations

The application currently:

1. acquires the current Definition lock and model-root delete gate;
2. loads the complete RelationshipDefinition aggregate;
3. re-validates the persisted aggregate;
4. counts current factual Relationships for the Definition;
5. reports `delete_blocked` with the factual Relationship count when non-zero;
6. clears `default_version`;
7. deletes the Definition;
8. commits.

The complete aggregate load provides `symmetric`, `default_version` and the complete Resolution set even though those values do not participate in the deletion-admission decision after existence is established.

## M4 candidate data path

The minimum conceptual information required before DML is:

- current Definition existence;
- current factual Relationship blocker count.

The Definition topology does not need to be re-certified before deletion: removing a member from the certified Definition set cannot introduce a new semantic-equivalence or cross-Definition Resolution conflict.

A targeted projection can therefore replace the complete aggregate load.

## Blocker count

Do not mechanically replace the current `COUNT` with `EXISTS`.

The current public failure shape includes the actual blocker count, so `COUNT` is presently consumed information rather than pure existence probing.

The optimization target is instead to avoid `GET complete aggregate + COUNT` when one targeted projection can provide current existence and the blocker count.

## Ownership and cascades

No new reverse-dependency materialization is justified for this rare model-plane operation.

The relational ownership model already gives the right cleanup semantics:

```text
RelationshipDefinition
    -> RelationshipResolution          owned / cascade
    -> RelationshipDefinitionVersion   owned / cascade
         -> RelationshipDefinitionProperty owned / cascade
```

Current factual Relationship rows are intentionally non-owned lifetime references and therefore remain blockers.

## `default_version = NULL` before delete

The current two-step DML is not classified as accidental redundancy during this phase.

The relational schema contains a cyclic relationship:

```text
RelationshipDefinition.default_version
    -> RelationshipDefinitionVersion

RelationshipDefinitionVersion.relationship_definition_id
    -> RelationshipDefinition
```

The default-version FK is restrictive while Definition -> Version ownership cascades. Clearing the default before deleting the root breaks that cycle under the current schema.

Whether M4 changes the FK realization is a later schema/concurrency design question; this discovery does not assume that the two statements can simply be collapsed.

## Cache behavior after delete

Candidate worker-local caches may retain orphan entries after Definition deletion:

- stable RelationshipDefinition topology entries;
- immutable RelationshipDefinitionVersion runtime-schema entries.

No distributed invalidation protocol is proposed.

Cache presence must never prove current existence or current admission. A new factual Relationship binding still depends on current PostgreSQL state. Orphan cache entries are therefore semantically harmless and may age out locally.

## Candidate conclusion

`RelationshipDefinition.DELETE` should operate on current existence plus the factual Relationship blocker count, not on the complete Definition aggregate. Owned Resolution/version/property state remains cascade-managed; no reverse-dependency denormalization is added. The `default_version = NULL` step remains, for now, a consequence of the current cyclic FK design. Worker-local cache entries need no distributed invalidation after deletion.
