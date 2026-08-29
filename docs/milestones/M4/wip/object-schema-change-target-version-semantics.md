# M4 WIP — Object SCHEMA_CHANGE target-version semantics

Status: SUPERSEDED SOURCE MATERIAL / M4 WIP / NON-NORMATIVE GLOBALLY

> **Superseded by current owner:** [`object-schema-change.md`](object-schema-change.md).
>
> The current reviewed direction no longer treats numeric version order as migration order. SCHEMA_CHANGE is an exact SOURCE -> TARGET migration; `target_version == current_version` is a `204` semantic no-op, while any distinct exact target is evaluated by SOURCE/TARGET migrability independently of whether its number is greater or smaller.
>
> The content below is retained only as historical discovery evidence and must not be used as current authority.

This note records the earlier target-version classification that was frozen before the cross-domain version semantics were revalidated.

```http
POST /api/v1/core/objects/{object_id}/schema
```

## Historical forward-only rule — SUPERSEDED

Given the Object aggregate snapshot used for preparation:

```text
current_version = S.template_version
target_version  = request.target_version
```

the earlier candidate required:

```text
target_version > current_version
```

Intermediate versions were not traversed; a request was planned directly SOURCE effective schema -> TARGET effective schema.

## Historical equal-target rule — SUPERSEDED

The earlier candidate classified:

```text
target_version == current_version
    -> semantic failure
    -> NOT 204 no-op
    -> no lifecycle event
    -> no mutation UoW
```

Current owner supersedes this with:

```text
target_version == current_version
    -> 204 semantic no-op
    -> no mutation
    -> no revision increment
    -> no SCHEMA_CHANGE lifecycle
```

## Historical lower-target rule — SUPERSEDED

The earlier candidate classified:

```text
target_version < current_version
    -> semantic failure
    -> downgrade unsupported
```

Current owner supersedes this because numeric order encodes creation/allocation order only, not migration direction. A numerically lower distinct target is an exact migration candidate whose admissibility depends on SOURCE/TARGET semantics and concrete Object state where required.

## Historical public failure mapping — SUPERSEDED

Both equal and lower target versions previously mapped to:

```text
HTTP 422
code = semantic_validation_failed
rule = must_be_greater_than_current_version
```

That diagnostic is no longer part of the current SCHEMA_CHANGE contract.

## Historical early classification — SUPERSEDED

Earlier:

```text
target_version <= observed current_version
    -> return 422 immediately

target_version > observed current_version
    -> continue preparation
```

This depended on the now-superseded assumption that Object schema migration could only increase version numbers.

Current classification is:

```text
target_version == observed current_version
    -> 204 semantic no-op

target_version != observed current_version
    -> identify exact SOURCE/TARGET pair
    -> evaluate migrability independently of numeric ordering
```

## Historical concurrency example — SOURCE EVIDENCE ONLY

The earlier candidate reasoned about concurrent migrations exclusively as increasing numeric versions and used an aggregate fingerprint retry mechanism. Both assumptions have since been superseded:

```text
numeric order
    -> not migration order

intrinsic Object fingerprint
    -> superseded by universal objects.revision generation semantics
```

The current retry/reprepare behavior is owned by `object-schema-change.md` together with [`object-revision.md`](object-revision.md) and remains under focused SCHEMA_CHANGE revalidation.
