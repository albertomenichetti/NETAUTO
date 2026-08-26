# RelationshipDefinition CREATE_NEXT — M4 Discovery

Status: WIP / NON-NORMATIVE

## Scope

First-phase M4 audit of `RelationshipDefinition.CREATE_NEXT`. This note records data-path, denormalization and cache findings only. Locking/concurrency redesign is explicitly deferred to the later global concurrency phase.

## Current semantic contract

`CREATE_NEXT` accepts an exact `PUBLISHED` or `DEPRECATED` RelationshipDefinitionVersion source and creates `max(existing)+1` as a new `DRAFT`, revision 1, cloning the complete property declaration snapshot.

The source property snapshot is immutable because only `PUBLISHED` / `DEPRECATED` versions are eligible.

## AS-IS observations

Current application flow:

1. loads the complete RelationshipDefinition aggregate mainly to prove the Definition exists;
2. loads the complete source exact version and property set;
3. checks source lifecycle eligibility;
4. derives/acquires the current dependency lock plan from exact DataType pins plus Definition/source rows;
5. reloads the complete source and rechecks lifecycle/plan stability;
6. selects the next lineage-local version number;
7. creates a DRAFT aggregate in memory;
8. persists one version row plus one INSERT per property.

The complete Definition aggregate is not semantically needed for cloning. Its topology, names, symmetry and default are not consumed by the operation beyond Definition existence.

The double source load is currently part of lock-plan stabilization and is not classified as removable before the global concurrency redesign.

## Candidate M4 data path

### Remove aggregate-sized Definition existence read

Do not load the complete Definition + Resolution aggregate merely to check existence. Use a minimal existence/header path, potentially absorbed by the eventual locking/admission statement once concurrency is redesigned.

### Prefer DB-side clone

The immutable source rows are already authoritative in PostgreSQL. Prefer cloning the property snapshot with DB-side set-based DML:

```text
INSERT new RelationshipDefinitionVersion DRAFT
+
INSERT relationship_definition_properties ... SELECT ...
    FROM source exact version
```

This makes clone DML constant with respect to property count:

```text
1 INSERT version
1 INSERT ... SELECT properties
```

rather than `1 + P` INSERT statements.

### Cache is not the clone mechanism

A future immutable RelationshipDefinitionVersion runtime cache will naturally contain the same complete property schema used by `CREATE_NEXT`, unlike ObjectTemplate where runtime effective schema differs from local declarations. Nevertheless, `CREATE_NEXT` is a rare model-plane operation and PostgreSQL can clone the authoritative immutable rows directly without transferring declarations DB -> application -> DB.

Therefore the runtime cache may be useful to data-plane Relationship operations but is not the primary CREATE_NEXT clone source.

## Cache/materialization implications

The newly created version is `DRAFT` and therefore:

- is not immutable-cacheable;
- does not trigger immutable version-cache fill;
- requires no new Relationship-specific denormalization.

## Deferred concurrency question

The current pre/post-lock reload of the immutable source is deferred to the global concurrency phase. M4 should later determine the minimum current-state stabilization needed for source existence/lifecycle and exact DataType dependency races without assuming the current duplicate aggregate load remains necessary.

## Candidate conclusion

`RelationshipDefinition.CREATE_NEXT` should eliminate the complete Definition aggregate read used only for existence and should clone the immutable property snapshot DB-side with `INSERT ... SELECT`. Do not use the worker runtime cache as the clone mechanism. Keep lock-plan-related source reloading explicitly open until the global concurrency audit.
