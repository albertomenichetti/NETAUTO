# M4 WIP — Object ATTACH error precedence

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the route-local error precedence for Object ATTACH batch.

The governing rule is deliberately simple:

```text
error precedence = execution/admission order
```

The route does not run a second diagnostic workflow, does not issue extra database statements only to improve error detail, and does not continue evaluating later gates after an earlier gate has failed.

## Frozen precedence

```text
1. wire/static request invalid
   -> 400 invalid_request

2. parent path target absent
   -> 404 resource_not_found

3. parent appears in child_object_ids
   -> 422 semantic_validation_failed / self_reference

4. slot unavailable in the prepared current parent schema
   -> 409 ownership_slot_unavailable

5. one or more child operands absent in the bulk child read
   -> 422 referenced_resource_not_found
   -> stop; do not continue into compatibility evaluation

6. one or more present child operands incompatible with the slot target lineage
   -> 422 semantic_validation_failed

7. Q2 detects parent binding changed since preparation
   -> 409 concurrent_object_change

8. Q3 graph admission
   has_owned_requested_child = true
       -> 409 ownership_conflict

   otherwise root_is_requested = true
       -> 409 ownership_cycle

9. Q4 residual integrity failure caused by a race
   -> translate from the known violated constraint class
   -> no diagnostic reread
```

## Batch implications

A batch may contain more than one latent problem. The route reports the first failing admission gate and stops.

Example:

```text
child-1 absent
child-2 incompatible
```

The bulk child read already proves that the batch cannot proceed, therefore the route returns `referenced_resource_not_found` and does not perform additional semantic work only to discover the incompatibility of `child-2`.

The same principle applies inside graph admission: `ownership_conflict` takes precedence over `ownership_cycle`, because the root-only cycle rule is meaningful only after all requested children have been certified ownerless.

## Diagnostic-work constraint

The route may expose only information already available from normal execution or from classification of the known violated relational constraint.

It MUST NOT issue an additional PostgreSQL statement solely to identify a more precise failing child, enrich `details`, or choose a more specific error after the decisive gate has already failed.

## Rationale

This keeps route behavior deterministic while avoiding a separate error-discovery algorithm that would:

- increase round trips;
- add failure-path work not needed for correctness;
- complicate concurrency semantics;
- risk exposing a diagnostic precedence different from the actual admission order.

The route therefore treats the first failed correctness gate as the public failure for that attempt.