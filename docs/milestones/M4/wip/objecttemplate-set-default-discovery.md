# ObjectTemplate.SET_DEFAULT discovery — WIP / NON-NORMATIVE

## Scope

First-phase M4 discovery for `ObjectTemplate.SET_DEFAULT`. This note is non-normative. Lock redesign remains deferred to the global concurrency phase.

## AS-IS data path

Current implementation:

1. locks the ObjectTemplate header (`NO KEY UPDATE`);
2. locks the target exact ObjectTemplateVersion (`SHARE`);
3. loads the complete exact version aggregate;
4. requires the target status to be `PUBLISHED`;
5. updates `object_templates.default_version` and returns the lineage;
6. commits.

Because `ObjectTemplateStore.get_version()` loads header, local properties and local components through separate reads, the current admission path loads significantly more data than the operation requires.

## Required current truth

`SET_DEFAULT` needs only:

- the lineage to exist now;
- the requested exact version to exist now;
- the requested exact version to be currently `PUBLISHED`;
- the default pointer update.

Local declarations, effective schema and compiled/runtime semantic payload are irrelevant to this operation.

## Cache role

No semantic cache role is required. Cache presence cannot prove current existence or current `PUBLISHED` lifecycle admission.

## Candidate minimal data path

A candidate M4 persistence direction is a single conditional update such as conceptually:

```sql
UPDATE object_templates AS ot
SET default_version = :version
WHERE ot.id = :template_id
  AND EXISTS (
      SELECT 1
      FROM object_template_versions AS otv
      WHERE otv.template_id = ot.id
        AND otv.version = :version
        AND otv.status = 'PUBLISHED'
  )
RETURNING ot.*;
```

This expresses target existence, current `PUBLISHED` admission and pointer mutation in one business statement.

If the public error contract must distinguish lineage-not-found, exact-version-not-found and lifecycle conflict, the final statement shape may need to return a richer outcome instead of relying only on an empty `RETURNING` result.

## Concurrency caveat

The single-statement candidate is a data-access target, not yet a concurrency conclusion. The current explicit exact-version SHARE lock participates in the rendezvous with `DEPRECATE` and other lifecycle-sensitive operations. The second/global concurrency phase must prove whether PostgreSQL statement/row locking of the conditional update is sufficient to preserve the invariant that the current default cannot point to a non-PUBLISHED exact version.

If it is insufficient, the required stabilization should be incorporated with the smallest possible persistence protocol without reintroducing unnecessary aggregate reads.

## Frequency / optimization priority

`SET_DEFAULT` is expected to be a very rare model-plane mutation. Avoid over-engineering beyond eliminating clearly unnecessary semantic-payload loads and expressing the admission predicate cleanly.

## Current working finding

> Candidate target: one conditional `UPDATE ... RETURNING` that admits only a currently `PUBLISHED` exact target; semantic cache and denormalization have no direct role. Final locking semantics remain open until the global concurrency audit.
