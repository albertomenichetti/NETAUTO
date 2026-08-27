# M4 WIP — Object SCHEMA_CHANGE target-version semantics

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the target-version classification frozen for:

```http
POST /api/v1/core/objects/{object_id}/schema
```

The route is a forward schema-migration command. It is not a generic setter for the Object's exact schema version.

## Forward-only rule

Given the Object aggregate snapshot used for preparation:

```text
current_version = S.template_version
target_version  = request.target_version
```

normal M4 schema migration requires:

```text
target_version > current_version
```

Intermediate versions are not traversed; a valid forward request may skip versions and is planned directly SOURCE effective schema -> TARGET effective schema.

Schema downgrade/rollback remains outside the normal M4 contract.

## Equal target is not a no-op

The route does not define idempotent convergence for an already-current exact version.

```text
target_version == current_version
    -> semantic failure
    -> NOT 204 no-op
    -> no lifecycle event
    -> no mutation UoW
```

The caller requested a schema migration but did not identify a forward target.

This intentionally differs from mutation commands whose domain contract explicitly defines convergence/no-op success.

## Lower target is invalid

```text
target_version < current_version
    -> semantic failure
    -> downgrade is not a normal migration
    -> no lifecycle event
    -> no mutation UoW
```

## Public failure mapping

Both equal and lower target versions map to the existing semantic-validation class:

```text
HTTP 422
code = semantic_validation_failed
```

Canonical bounded diagnostic shape:

```json
{
  "code": "semantic_validation_failed",
  "message": "The requested target version is not a valid forward schema migration target.",
  "details": {
    "violations": [
      {
        "path": "target_version",
        "rule": "must_be_greater_than_current_version"
      }
    ],
    "current_version": 5,
    "target_version": 5
  }
}
```

The stable public branching contract remains the top-level `code`; no dedicated new error code is introduced solely for non-forward target selection.

## Early classification

This classification is performed from the preparatory Object snapshot before expensive MigrationPlan application and before entering the mutation UoW.

```text
target_version <= observed current_version
    -> return 422 immediately

target_version > observed current_version
    -> continue preparation
```

For `target <= current`, the negative decision is stronger than the generally accepted conservative-failure rule: because normal Object schema migration itself is forward-only, another concurrent schema migration can only leave the current version unchanged or increase it. It cannot make a target already less-than-or-equal to the observed current version become a valid forward target.

## Concurrent forward migrations

A request initially observed as forward may become stale before commit.

Example:

```text
T1 preparation
    current = 4
    requested target = 6

T2 commits
    4 -> 5
```

T1's protected aggregate fingerprint no longer matches and its prepared success cannot commit. After bounded restart:

```text
current = 5
target = 6
    -> still forward
    -> prepare MigrationPlan(5,6)
```

If instead another transaction commits:

```text
4 -> 7
```

then on retry:

```text
current = 7
target = 6
    -> non-forward
    -> 422 semantic_validation_failed
```

The strong false-success protection therefore composes naturally with the forward-only target rule.

## Frozen decision

```text
target_version < current_version
    -> 422 semantic_validation_failed
    -> no downgrade
    -> no UoW
    -> no lifecycle

target_version == current_version
    -> 422 semantic_validation_failed
    -> NOT an idempotent no-op
    -> no UoW
    -> no lifecycle

target_version > current_version
    -> valid forward candidate
    -> continue target existence/lifecycle admission and migration preparation
```
