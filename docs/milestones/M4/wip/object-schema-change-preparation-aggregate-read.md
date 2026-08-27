# M4 WIP — Object SCHEMA_CHANGE preparation aggregate read

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note freezes the optimistic preparation read performed after the required immutable `MigrationPlan` has been obtained or compiled for:

```http
POST /api/v1/core/objects/{object_id}/schema
```

## Context

The command first performs a lightweight Object binding lookup and derives:

```text
(template_id, source_version, target_version)
```

It then resolves:

```text
MigrationPlanCache[(template_id, source_version, target_version)]
```

including bounded cache fill where necessary.

Only after that immutable model-plane work is READY does the command read the complete current Object aggregate required for optimistic migration preparation and fingerprinting.

## Runtime state read

The preparation read must observe in one PostgreSQL statement:

```text
Object intrinsic state
    id
    canonical_name
    template_id
    template_version
    properties

current attached ownership edges where this Object is parent
    child_object_id
    slot_declaring_template_id
    slot_name
```

These ownership rows are factual runtime edges currently present in `object_components`.

They are not the effective component slots defined by the ObjectTemplate schema. Effective component-slot knowledge belongs to the immutable source/target closures and therefore to the `MigrationPlan`.

## Preferred simple statement shape

Conceptually:

```sql
SELECT
    o.id,
    o.canonical_name,
    o.template_id,
    o.template_version,
    o.properties,
    oc.child_object_id,
    oc.slot_declaring_template_id,
    oc.slot_name
FROM objects o
LEFT JOIN object_components oc
    ON oc.parent_object_id = o.id
WHERE o.id = :object_id;
```

The exact SQL syntax is not yet normative. The frozen requirement is one coherent `READ COMMITTED` statement snapshot containing the complete Object intrinsic state plus all current attached ownership edges.

No joins to child Object rows are required.

Explicitly excluded:

```text
child canonical_name
child properties
child exact schema binding
ObjectTemplate metadata/effective schema
Relationship state
lifecycle history
incoming owner edge
```

## Empty ownership

An Object with no attached children is represented as:

```text
Object intrinsic state present
ownership = []
```

A `LEFT JOIN`-style realization must distinguish this from Object absence.

## Deterministic fingerprint ordering

PostgreSQL is not required to emit ownership rows in canonical fingerprint order.

The application sorts the factual edges before canonical JSON encoding using the already-frozen tuple:

```text
(slot_declaring_template_id, slot_name, child_object_id)
```

This keeps canonical fingerprint ordering an application concern and avoids requiring a route-specific database sort or index solely for hashing.

## Binding stability check before fingerprinting

The complete aggregate read must still match the Object binding that selected the immutable migration plan.

Given an initial plan identity:

```text
(template_id = T, source_version = S, target_version = V)
```

the second Object read must satisfy:

```text
current.template_id == T
current.template_version == S
```

If either value differs, the prepared model-plane decision is stale.

Frozen behavior:

```text
binding differs
    -> fail the current caller request
    -> do not calculate/use a fingerprint for the stale plan
    -> do not automatically compile/re-plan from the newly observed version
```

Even when the newly observed version remains lower than the requested target version, this request does not transparently restart planning from that new source version.

The caller may retry. A fresh request then naturally discovers the new current source version and resolves the appropriate `MigrationPlan[(T, new_source, target)]`.

This intentionally favors a conservative false failure over hidden extra retry/re-planning behavior.

It also preserves the previously frozen rule that automatic retry is reserved for the protected fingerprint-mismatch path, rather than introducing an additional automatic restart trigger during optimistic preparation.

## Fingerprint creation

Only after the second read confirms the same source binding does the application construct the canonical Object aggregate snapshot `S` and calculate:

```text
F(S) = SHA-256(canonical_json_utf8(S))
```

The resulting raw 32-byte digest becomes the expected Object aggregate fingerprint carried by the prepared schema-change candidate.

## Frozen decision

```text
MigrationPlan READY
    -> one coherent Object + current attached ownership read
    -> require same template_id/source_version used by MigrationPlan

binding mismatch
    -> fail request
    -> no automatic re-plan

binding match
    -> sort ownership deterministically in application
    -> construct canonical aggregate S
    -> SHA-256(S)
    -> continue optimistic migration preparation
```

Physical index/plan verification remains part of the architecture-wide M4 relational review.