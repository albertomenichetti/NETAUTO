# M4 WIP — Object DETACH parent SHARE lock

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note supersedes the earlier route-local idea that Object DETACH required no explicit parent row lock.

## Superseded rule

The following earlier direction is no longer valid:

```text
DETACH -> no explicit parent lock
```

That direction was attractive because DETACH is schema-agnostic and does not need to interpret the parent's current ObjectTemplateVersion. However, it is insufficient once DETACH is composed with the already-frozen SCHEMA_CHANGE aggregate-fingerprint protocol.

## Why the parent lock is required

SCHEMA_CHANGE fingerprints the authoritative Object aggregate, including current ownership edges, and then protects the parent Object row before performing the final fresh aggregate reread and mutation.

Without a conflicting parent lock in DETACH, this interleaving would be possible:

```text
SCHEMA_CHANGE
    lock parent FOR NO KEY UPDATE
    fresh aggregate read sees edge E

DETACH
    delete E
    commit

SCHEMA_CHANGE
    update schema + lifecycle
    commit
```

That would permit SCHEMA_CHANGE to succeed even though the authoritative aggregate changed after its final fingerprint check.

The route-local SCHEMA_CHANGE contract explicitly requires serialization against ownership-edge mutation on the same parent, so DETACH must participate in that serialization domain.

## Frozen replacement rule

DETACH acquires a parent row lock inside its existing Q1 statement:

```text
SELECT parent.id, parent.canonical_name
FROM objects AS parent
WHERE parent.id = :parent_object_id
FOR SHARE
```

Conceptually this is part of the same Q1 statement that performs:

```text
parent existence
+ requested child existence
+ exact requested-edge DELETE
+ RETURNING lifecycle material
```

No extra PostgreSQL round trip is introduced.

## Why FOR SHARE

DETACH does not mutate the parent Object row itself. It only needs a lock mode that conflicts with SCHEMA_CHANGE's parent `FOR NO KEY UPDATE` lock.

`FOR SHARE` is sufficient for that purpose while still allowing multiple DETACH operations on the same parent to hold compatible parent locks concurrently; edge-row arbitration remains separate.

## Lifetime side effect

Holding the parent SHARE lock to commit also keeps parent lifetime stable while DETACH writes its lifecycle event rows.

This is a useful consequence, but the primary reason for the lock is serialization with SCHEMA_CHANGE aggregate certification.

## Cost

The frozen DETACH success-path statement count remains unchanged:

```text
Q1 parent FOR SHARE + admission + bulk DELETE ... RETURNING
Q2 bulk DETACH_FROM lifecycle INSERT

2 PostgreSQL business statements
```

There is no cache warm/cold distinction.

## Frozen takeaway

```text
DETACH parent lock is required
    -> parent FOR SHARE inside Q1
    -> serializes against SCHEMA_CHANGE parent FOR NO KEY UPDATE
    -> no extra statement
    -> supersedes the earlier no-parent-lock direction
```
