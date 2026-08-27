# M4 WIP — Object.RENAME same-name semantics

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the caller-visible and persistence semantics for same-name Object rename requests under the M4 TO-BE candidate.

## Public operation

```http
PUT /api/v1/core/objects/{object_id}/canonical-name
```

Request:

```json
{
  "canonical_name": "server-2"
}
```

Success:

```text
204 No Content
```

## Frozen decision

The mutation does **not** first compare the requested `canonical_name` with the currently persisted value.

The write targets the Object by identity only:

```text
UPDATE objects
SET canonical_name = requested_name
WHERE id = object_id
```

Therefore:

```text
Object absent
    -> UPDATE affects 0 rows
    -> path resource not found

Object exists, current name differs
    -> UPDATE affects the Object
    -> success 204

Object exists, current name already equals requested name
    -> UPDATE still targets/affects the Object
    -> success 204
```

The HTTP outcome for an existing Object is intentionally independent of whether the requested value was already present.

## Superseded candidate

An earlier M4 candidate treated same-name rename as a semantic no-op and proposed skipping UPDATE/lifecycle work.

That candidate is superseded by this decision.

The motivation is to avoid an additional read/lock/check whose only purpose would be to classify an otherwise harmless same-value assignment. The mutation itself is the existence test and concurrency rendezvous.

## Lifecycle consequence

RENAME remains an auditable mutation operation. If the mutation completes for an existing Object, the normal RENAME lifecycle write is performed atomically with it.

Therefore a same-name request may produce a RENAME event whose intrinsic `before_state` and `after_state` differ only conceptually by the requested assignment and can be value-equal for `canonical_name`.

This is intentional for RENAME and does not change the separately frozen DATA_CHANGE rule that semantic no-op property mutations emit no fake lifecycle transition.

## Design consequence

There is no need for a dedicated preliminary `SELECT ... FOR NO KEY UPDATE` merely to distinguish same-name from changed-name requests.

The remaining route-local design question is how to obtain the exact before/after intrinsic snapshots and write the lifecycle event atomically while keeping the mutation path as compact as possible.
