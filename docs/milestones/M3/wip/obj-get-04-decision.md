# M3 discovery — OBJ-GET-04 decision

Status: CONSOLIDATED (discovery WIP, non-normative)

## Public read

`GET /api/v1/core/objects/{child_object_id}/owner`

Application owner: `ObjectService.get_owner()`.

## Current shape

The current read uses `coherent_read()` and composes multiple reads:

1. load the child Object to preserve path-target `404` semantics;
2. load its current ownership fact;
3. if an owner exists, load the parent Object;
4. resolve the parent's full effective schema through `_schema_specs()`;
5. resolve the ownership `slot_name` against that effective schema;
6. fail internally if the persisted parent or semantic slot cannot be re-certified.

The response only requires:

- `parent_object_id`;
- `slot_declaring_template_id`;
- `slot_name`.

## Consolidated findings

- Child existence is part of the public path-target contract and must remain: absent child -> `404`.
- Child present without an ownership fact must remain `200 null`.
- Parent existence re-check is persisted-state revalidation. The ownership parent reference is structurally protected by the persistence FK and must not be re-certified by the GET.
- Resolving the full effective schema through `_schema_specs()` is unnecessary for this projection and performs unrelated property/DataType loading and semantic certification.
- Re-checking that the persisted ownership slot still resolves to a semantic component slot is mutation-owned semantic revalidation and must be removed from the GET path.
- `coherent_read()` is justified by the current fragmented multi-statement shape, but is not required by the target single-statement projection.

## Target projection

Use one recursive statement rooted at the child Object:

1. select the target child row;
2. LEFT JOIN its optional current ownership fact;
3. when an owner exists, load the parent Object's exact `(template_id, template_version)`;
4. follow the exact ObjectTemplateVersion parent pins with a recursive CTE;
5. join only `object_template_components` by exact template/version and persisted `slot_name` to obtain `slot_declaring_template_id`;
6. project the owner response directly.

The child row itself is the existence marker, so no synthetic marker row is required.

Result interpretation:

- zero rows -> child absent -> `404`;
- one row with owner columns NULL -> child exists without owner -> `200 null`;
- one row with owner data -> build `OwnerProjection`.

The component-declaration join is projection, not semantic certification: it supplies `slot_declaring_template_id`, a response field. The GET trusts the mutation-owned invariant that persisted ownership facts reference a valid effective slot.

## Target transaction shape

- ordinary UoW;
- one recursive SQL statement;
- no `coherent_read()`;
- no `_schema_specs()` / effective-schema construction;
- no persisted parent existence re-check;
- no persisted slot semantic revalidation.

## Behavioral contract preserved

- absent child -> `404`;
- existing child without owner -> `200 null`;
- existing child with owner -> unchanged owner projection.
