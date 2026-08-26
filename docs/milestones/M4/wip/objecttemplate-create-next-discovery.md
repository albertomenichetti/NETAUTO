# ObjectTemplate.CREATE_NEXT discovery — WIP / NON-NORMATIVE

## Scope

This note records first-phase M4 discovery for `ObjectTemplate.CREATE_NEXT`. It is non-normative. Lock redesign and global concurrency reasoning remain deferred to the second phase.

## Semantic baseline

`CREATE_NEXT(template_id, source_version)` accepts an exact source only when that source is `PUBLISHED` or `DEPRECATED`.

The source snapshot is semantically immutable. The operation creates a new DRAFT revision 1 in the same lineage by cloning:

- exact parent pin;
- local properties;
- local components.

The source need not be the highest existing version. Version allocation remains `max(existing)+1`, with deleted highest DRAFT version numbers potentially reusable.

## AS-IS flow

The current implementation, simplified, performs:

1. load the complete source exact version (`header + local properties + local components`);
2. load the source lineage;
3. verify source existence and eligibility;
4. derive dependency lock intents from the source snapshot;
5. acquire the current lock plan;
6. reload the complete source exact version;
7. re-check source eligibility and lock-plan stability;
8. compute `max(existing)+1`;
9. construct a DRAFT clone with the source parent pin and local declarations;
10. insert exact version;
11. insert cloned properties;
12. insert cloned components;
13. commit.

The repeated source load is currently part of lock-plan stabilization and is not treated as accidental duplication in first-phase discovery.

## Cache finding

The runtime-oriented immutable ObjectTemplate cache under consideration is expected to contain the effective/flattened schema and compiled structures optimized for Object validation.

`CREATE_NEXT` does not clone the effective schema. It clones the source's **local declarations**.

Therefore this operation does not, by itself, justify extending the hot-path ObjectTemplate cache with all local declarations merely to optimize a rare model-plane clone.

Working direction:

> Keep the runtime ObjectTemplate cache optimized for repeated Object/data-plane consumption. Do not expand it solely for `CREATE_NEXT` unless later operation audit shows strong cross-operation value.

## DB-side clone finding

Because the source is immutable, PostgreSQL already owns the exact local snapshot that must be copied.

Instead of transferring local declarations from PostgreSQL to Python and then writing identical rows back, investigate database-side cloning through `INSERT ... SELECT`.

Conceptual exact-version clone:

```sql
INSERT INTO object_template_versions (...)
SELECT
    template_id,
    :new_version,
    1,
    'DRAFT',
    parent_template_id,
    parent_version
FROM object_template_versions
WHERE template_id = :template_id
  AND version = :source_version;
```

Conceptual local-property clone:

```sql
INSERT INTO object_template_properties (...)
SELECT
    template_id,
    :new_version,
    name,
    position,
    datatype_id,
    datatype_version,
    value_mode,
    required,
    migration_default
FROM object_template_properties
WHERE template_id = :template_id
  AND template_version = :source_version;
```

The same direction applies to local components.

This can reduce clone DML/read traffic to a bounded number of statements independent of property/component cardinality.

## Version allocation

The operation still requires current mutable version-set truth to compute the new exact version number.

The current `max(existing)+1` rule and its interaction with concurrent `CREATE_NEXT` / `DELETE_DRAFT` remain part of the global version-set concurrency problem. No lock redesign is made here.

## Dependency lock planning

The current lock plan derives direct dependency intents from the source local snapshot:

- exact parent ObjectTemplate dependency;
- local property exact DataType pins;
- local component target lineages.

Even if DB-side clone removes the need to transfer the full source snapshot merely for copying, the current implementation still needs dependency knowledge before locking.

Whether this dependency-planning requirement can be simplified, batch-projected, derived from other materialization, or redesigned remains deferred to the second/global concurrency phase.

## Effective-schema materialization

The new version created by `CREATE_NEXT` is DRAFT.

Current preferred M4 direction is therefore:

- do **not** create long-lived effective-schema materialization for the new DRAFT;
- do **not** populate the immutable ObjectTemplate cache for the new DRAFT;
- retain source PUBLISHED/DEPRECATED materialization/cache unchanged;
- materialize the new version's effective schema later if/when that DRAFT is successfully PUBLISHED.

## Stable ancestry

`CREATE_NEXT` does not create a new lineage and therefore does not change stable ObjectTemplate ancestry materialization.

## First-phase preferred direction

The strongest current data-access direction for `CREATE_NEXT` is:

> Treat the operation as a database-side clone of an immutable local snapshot, ideally using bounded `INSERT ... SELECT` statements, while keeping current version-set/admission/locking semantics unchanged until the global concurrency redesign.

## Open items

- exact SQL/DML shape for DB-side cloning;
- preservation of FK authority and useful diagnostics during bulk/database-side clone;
- whether one statement can safely combine exact-version and declaration cloning without unnecessary complexity;
- whether current source eligibility can be checked in the clone statement or should remain a separate admission predicate;
- dependency lock-plan redesign;
- version-set concurrency and version-number allocation;
- whether later operation audit reveals a cross-operation need to cache local immutable declarations separately from runtime effective schema.
