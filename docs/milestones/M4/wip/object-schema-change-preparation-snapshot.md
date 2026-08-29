# M4 WIP — Object SCHEMA_CHANGE preparation snapshot

Status: SUPERSEDED SOURCE MATERIAL / M4 WIP / NON-NORMATIVE GLOBALLY

This note is retained only as historical source material for the earlier aggregate-snapshot / fingerprint SCHEMA_CHANGE design.

Current authority is [`object-schema-change.md`](object-schema-change.md), together with [`object-revision.md`](object-revision.md) and [`object-components-persistence.md`](object-components-persistence.md).

The earlier preparation direction in this file is superseded on all of these points:

```text
separate lightweight binding read
    + second aggregate preparation read

current attached ownership edges
    as normal preparation input

current attached ownership edges
    as intrinsic optimistic-fingerprint input

canonical aggregate JSON + SHA fingerprint
    as stale-generation authority
```

Current revalidated preparation is:

```text
one coherent intrinsic Object generation read per attempt
    template_id
    template_version
    properties
    revision = R

MigrationPlan
    -> immutable SOURCE/TARGET semantic classification

current ownership membership
    -> not read for normal semantic preparation

REMOVE / semantic replacement blockers
    -> arbitrated at the final edge -> current-slot relational boundary

component target narrowing / unrelated relation
    -> categorically rejected from immutable plan classification
    -> no child compatibility read

intrinsic stale-success protection
    -> expected_revision = R
```

`object_components` membership therefore remains outside the intrinsic revision/preparation boundary. It is consulted only by relational enforcement where the operation actually depends on current structural facts.

Git history retains the complete earlier aggregate-snapshot rationale.