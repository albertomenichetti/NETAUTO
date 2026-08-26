# M4 — DataType DEPRECATE discovery

**Status:** WIP / NON-NORMATIVE

**Role:** bounded discovery note for `DataType.DEPRECATE`. This note records current data-access findings and working direction only. It does not define the M4 contract, TO-BE architecture, persistence schema, cache contract or concurrency redesign.

## 1. AS-IS data-access shape

`DataType.DEPRECATE(datatype_id, version)` currently needs current PostgreSQL state for:

- exact version lifecycle status;
- current lineage `default_version`;
- existence of active PUBLISHED model consumers that reference the exact DataTypeVersion.

The active-consumer predicate is currently derived dynamically from two consumer families:

```text
PUBLISHED ObjectTemplateVersion property -> exact DataTypeVersion
PUBLISHED RelationshipDefinitionVersion property -> exact DataTypeVersion
```

The current persistence implementation checks those families separately.

## 2. Cache classification

The worker-local immutable semantic cache is not useful for the admission decision of `DEPRECATE`.

The relevant facts are current/mutable:

```text
exact status
current default pointer
current active-consumer set
```

Therefore PostgreSQL remains the authority for this operation.

## 3. Reverse-dependency materialization finding

A possible persistence optimization is to materialize the reverse active-model dependency relation so that the blocker predicate can be queried directly instead of derived from consumer declarations and lifecycle state.

This is technically plausible but is **not the preferred working direction at this stage**.

Reason: `DataType.DEPRECATE` is expected to be a rare model-plane mutation. Introducing and maintaining additional current mutable reverse-dependency state would increase write-path and persistence complexity for a limited runtime benefit.

Working preference:

> continue deriving active consumers dynamically unless the wider M4 audit shows that the same reverse-dependency materialization has substantial cross-operation value beyond rare deprecation paths.

The finding is retained because later ObjectTemplate/RelationshipDefinition analysis may change the cost-benefit assessment.

## 4. Query-shape observation

The semantic question is whether at least one active blocker exists, not how many blockers exist.

Therefore a likely local data-access improvement, independent of any denormalization decision, is:

```text
COUNT(*)
    -> EXISTS
```

or an equivalent bounded existence projection.

Whether the two consumer families should remain separate statements or be expressed in one business statement is left open for the later query-shape review.

## 5. Concurrency explicitly deferred

Current row-lock choices and their interaction with PUBLISH, SET/CLEAR DEFAULT, consumer publication/deprecation and lineage deletion are not redesigned in this note.

M4 will reconsider locking only in a later global concurrency phase against the complete semantic concurrency matrix.
