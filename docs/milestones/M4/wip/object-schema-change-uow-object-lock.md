# M4 WIP — Object SCHEMA_CHANGE UoW Object lock

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note freezes Q2 of the short mutation unit of work for:

```http
POST /api/v1/core/objects/{object_id}/schema
```

## Context

Before Q2, the command has already:

```text
Q1
    locked the exact target ObjectTemplateVersion with FOR SHARE
    required current status == PUBLISHED
    retained that lock through commit
```

The target exact-version lock protects current target admission. Q2 protects the mutable Object aggregate against concurrent Object-side mutations while the prepared candidate is revalidated and committed.

## Q2 — Object concurrency rendezvous

Q2 acquires the target Object row with:

```sql
SELECT id
FROM objects
WHERE id = :object_id
FOR NO KEY UPDATE;
```

The exact selected column list is not semantically important. The frozen role of Q2 is lock acquisition, not state reconstruction.

## Lock role

The Object row is the concurrency rendezvous for mutations that can change the whole-aggregate fingerprint or otherwise conflict with schema change, including:

```text
SCHEMA_CHANGE
properties/DATA_CHANGE
RENAME
ATTACH
DETACH
DELETE (with a stronger conflicting lock)
```

`FOR NO KEY UPDATE` is held through the remaining fingerprint verification, write and commit.

## Do not reuse Q2-read state for fingerprinting

Q2 may have to wait behind a concurrent Object mutation.

Under PostgreSQL READ COMMITTED, the statement snapshot associated with the lock-acquisition statement is therefore not the snapshot that must be used to re-read nonlocked aggregate state such as outgoing `object_components` rows.

Frozen rule:

```text
Q2
    acquire Object @ FOR NO KEY UPDATE
    may wait

Q2 completes

Q3
    NEW PostgreSQL statement
    NEW READ COMMITTED statement snapshot
    read complete authoritative Object aggregate
    recompute fingerprint
```

No Object fields returned by Q2 are accepted as the authoritative protected fingerprint state.

In particular, the command must not combine Q2 lock acquisition and Q3 fingerprint reconstruction into one statement merely to save a round trip, because a wait during Q2 could otherwise leave nonlocked ownership rows observed through a stale pre-wait statement snapshot.

## Missing Object

If Q2 does not find the Object, the mutation cannot continue.

The exact public classification remains governed by the route's failure contract, but the command performs no write and rolls back the UoW.

## Frozen UoW prefix

The short successful UoW now begins:

```text
BEGIN

Q1
    exact TARGET OTV @ FOR SHARE
    require status == PUBLISHED

Q2
    Object @ FOR NO KEY UPDATE
    concurrency rendezvous only

Q3
    new statement / fresh READ COMMITTED snapshot
    read Object aggregate + current attached ownership edges
    recompute fingerprint
```

Q2 does not perform semantic migration work, cache fill, schema interpretation, property validation or lifecycle construction. All of that was completed before entering the UoW.
