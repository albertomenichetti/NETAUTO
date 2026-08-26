# ObjectTemplate.DELETE_DRAFT discovery — WIP / NON-NORMATIVE

## Scope

First-phase M4 discovery for `ObjectTemplate.DELETE_DRAFT`. Lock redesign remains deferred to the global concurrency phase.

## AS-IS flow

Current application flow:

1. lock ObjectTemplate header with `NO KEY UPDATE`;
2. lock exact ObjectTemplateVersion with `UPDATE`;
3. load the complete exact version aggregate;
4. require `DRAFT` lifecycle and matching `expected_revision`;
5. delete the exact version;
6. commit.

The complete exact-version load currently includes header, local properties and local components.

## Data-access finding

Admission for `DELETE_DRAFT` needs only current exact-version facts:

```text
exists
status
revision
```

It does not need:

```text
parent exact pin
local properties
local components
effective schema
```

Therefore the complete aggregate load is oversized for this operation.

Candidate first-phase data path, keeping the current locking structure as baseline:

```text
lock header
locking exact read -> existence + status + revision
DELETE exact version
COMMIT
```

The locking read should ideally return the lifecycle/freshness fields required by admission, avoiding a subsequent aggregate read.

## Cache / materialization

DRAFT exact ObjectTemplate semantics are not worker-cacheable.

Under the current M4 direction, DRAFT effective schema is derived transiently/on demand and is not persisted as the immutable effective-schema materialization. Therefore deleting a DRAFT requires no effective-materialization cleanup and no immutable-cache invalidation.

## Deferred concurrency question

`DELETE_DRAFT` interacts with lineage version-set allocation, especially `CREATE_NEXT`, because deleting the highest DRAFT can permit reuse of that version number under the current `max(existing)+1` rule.

The current header/version locking contract remains the baseline until the second-phase global concurrency audit.

## Working finding

> `ObjectTemplate.DELETE_DRAFT` should be header-oriented rather than aggregate-oriented: admission needs only current existence/status/revision, with no role for semantic cache or effective-schema materialization.
