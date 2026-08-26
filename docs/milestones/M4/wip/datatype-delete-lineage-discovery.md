# M4 — DataType DELETE_LINEAGE discovery

**Status:** WIP / NON-NORMATIVE

**Role:** bounded discovery note for `DataType.DELETE_LINEAGE`. This document records AS-IS evidence, findings and working preferences only. It does not define the M4 contract, TO-BE architecture, persistence schema, cache contract or concurrency realization.

The delivered AS-IS under `docs/architecture/` remains authoritative until M4 explicitly freezes a TO-BE delta.

## 1. AS-IS flow

Current `DELETE_LINEAGE`:

```text
BEGIN UoW

1. acquire MODEL_ROOT_DELETE_GATE
2. lock DataType header FOR UPDATE
3. count ObjectTemplate-property references
4. count RelationshipDefinition-property references
5. fail when external blockers exist
6. set default_version = NULL
7. delete DataType lineage
   -> owned DataTypeVersion rows cascade
   -> external reference FKs remain final race authority
8. COMMIT
```

The operation is expected to be rare.

## 2. Cacheability

Worker-local semantic cache has no admission role here.

The required facts are current mutable PostgreSQL truth:

```text
lineage currently exists
external references currently exist or not
```

Cached immutable DataType semantics cannot prove either fact.

## 3. Reverse-reference materialization finding

The current implementation derives blocker counts dynamically from ObjectTemplate-property and RelationshipDefinition-property references.

A reverse-reference materialization could theoretically make this lookup cheaper, but the current working preference is **not** to introduce such persistent derived state solely for `DataType.DELETE_LINEAGE`, because the operation is rare and the added maintenance complexity would be paid by other model-plane mutations.

This choice may be revisited if later M4 analysis finds a broader, cross-operation use for the same reverse dependency structure.

## 4. Blocker queries

Unlike `DEPRECATE`, `DELETE_LINEAGE` currently reports blocker counts, not just blocker existence. Therefore replacing all blocker scans with simple `EXISTS` queries would change diagnostic information unless the failure contract is redesigned.

No change is proposed here yet.

## 5. Why default_version is cleared before DELETE

The current relational schema contains both:

```text
datatype_versions.datatype_id
    -> datatypes.id
    ON DELETE CASCADE
```

and:

```text
datatypes.(id, default_version)
    -> datatype_versions.(datatype_id, version)
    ON DELETE RESTRICT
```

Therefore a lineage with a current default has an internal referential cycle:

```text
DataType lineage
    -> default exact version
    -> owning DataType lineage
```

Before deleting the lineage, the implementation sets `default_version = NULL` so that the owned version rows can be removed by cascade without the lineage's own default FK restricting that removal.

This is a relational realization concern, not an additional domain rule.

## 6. M4 schema-design note

Working finding:

> The preliminary `default_version = NULL` UPDATE is required by the current FK shape and should be reconsidered only as part of the complete M4 relational redesign, not as an isolated DELETE optimization.

This is especially relevant because M4 is already questioning the current physical placement of stable DataType facts such as `base_type`.

## 7. Explicitly open points

This note does not decide:

- final DataType relational schema;
- whether the default FK shape changes;
- final blocker-query form;
- final lock/gate realization;
- interaction with the global concurrency redesign;
- whether a future shared reverse-dependency structure becomes justified by other operations.
