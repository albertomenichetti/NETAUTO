# ObjectTemplate LIST versions — M4 discovery

Status: WIP / NON-NORMATIVE

## Current behavior

The public ObjectTemplate version-list read is already implemented as a one-statement PostgreSQL projection.

It outer-joins the lineage header to exact versions so that one statement can distinguish:

- missing ObjectTemplate lineage -> 404;
- existing lineage with no matching versions -> empty page.

The summary projection contains only:

- `template_id`;
- `version`;
- `revision`;
- `status`;
- `parent_template_id`;
- `parent_version`.

No local properties, local components, effective schema, DataType semantic payload, or stable ancestry are loaded.

## M4 finding

No denormalization or cache-assisted path is justified for this read.

The summary fields contain current lifecycle state (`status`, and mutable DRAFT `revision`) and therefore remain PostgreSQL current truth. The exact parent pin is part of the public summary contract and must also be returned.

The current one-statement lineage-existence discrimination should be preserved.

## Candidate direction

Keep the read as one minimal PostgreSQL statement that returns only summary fields and preserves the difference between missing parent lineage and an empty filtered result.

Do not load extra semantic payload solely to warm caches.

Do not use stable ancestry closure or immutable effective-schema materializations for this operation.

## Concurrency

No concurrency redesign is proposed in this discovery note. Any global read/mutation consistency concerns belong to the later M4 concurrency re-derivation phase.
