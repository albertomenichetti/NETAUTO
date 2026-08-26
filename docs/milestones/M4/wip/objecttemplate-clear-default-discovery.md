# ObjectTemplate.CLEAR_DEFAULT discovery — WIP / NON-NORMATIVE

## Scope

This note records first-phase M4 discovery for `ObjectTemplate.CLEAR_DEFAULT`. It is non-normative. Lock/concurrency redesign remains deferred to the global second phase.

## AS-IS data path

Current operation:

```text
BEGIN UoW

1. lock ObjectTemplate header NO KEY UPDATE
2. UPDATE object_templates
       SET default_version = NULL
   RETURNING lineage
3. COMMIT
```

No version aggregate, effective schema, DataType semantics, or cache state is needed.

## Candidate M4 data path

Pure data-access target:

```sql
UPDATE object_templates
SET default_version = NULL
WHERE id = :template_id
RETURNING *;
```

So the first-phase target is one SQL business statement plus commit.

## Cache / denormalization

No worker cache or denormalized semantic projection is useful for this operation. `default_version` is current mutable lineage state and PostgreSQL remains authoritative.

## Open concurrency question

The explicit ObjectTemplate header lock may still be required as rendezvous with operations that resolve a current default and persist an exact pin, especially `Object.CREATE` when `template_version` is omitted.

Example semantic race to re-derive in the second phase:

```text
CLEAR_DEFAULT                 Object.CREATE(default)
-------------                 ----------------------
clear default                 resolve current default
                              persist exact ObjectTemplateVersion pin
```

The final result must be equivalent to a supported serial ordering. Do not remove the header synchronization based on local data-access reasoning alone.

## Current first-phase conclusion

- target data path: one `UPDATE ... RETURNING` statement;
- no cache role;
- no denormalization role;
- whether explicit header locking is still required remains open until the global concurrency audit.
