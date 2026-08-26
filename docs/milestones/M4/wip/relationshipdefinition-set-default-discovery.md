# RelationshipDefinition SET_DEFAULT — M4 discovery

Status: WIP / NON-NORMATIVE

## Scope

This note records the M4 discovery findings for `RelationshipDefinition.SET_DEFAULT` only. It is not a frozen contract or implementation authorization.

## Current semantic need

`SET_DEFAULT` changes only current mutable selection state on the RelationshipDefinition lineage. The selected exact version must exist in the same Definition and be currently `PUBLISHED`.

The public response is the complete current `RelationshipDefinition` DTO, including:

- `id`
- `symmetric`
- `default_version`
- complete current Resolution set with current mutable names and stable endpoint identities

Therefore this operation differs from ObjectTemplate SET_DEFAULT: the response cannot be reconstructed from a stable topology cache alone because Resolution `name` is mutable/current metadata.

## AS-IS data path

Current application behavior conceptually performs:

1. lock Definition header and target exact version;
2. load the complete target RelationshipDefinitionVersion;
3. require target status `PUBLISHED`;
4. update `relationship_definitions.default_version`;
5. reload the complete RelationshipDefinition aggregate, including all Resolutions, for the response.

The exact target property schema is over-read: SET_DEFAULT requires only target existence and current lifecycle status.

## M4 candidate data path

Target a single PostgreSQL mutation/projection statement which:

1. distinguishes Definition absence, exact-version absence, and exact target not currently `PUBLISHED`;
2. updates `default_version` only for an admissible exact target;
3. returns the complete current RelationshipDefinition projection, including current Resolution names.

A data-modifying CTE or equivalent one-statement projection is a candidate realization. Exact SQL shape remains implementation/design work, and concurrency correctness against DEPRECATE is deferred to the global M4 concurrency phase.

Conceptually:

```text
candidate exact version
        ↓
current exact existence/status check
        ↓
UPDATE default_version
        ↓
project current Definition + complete Resolutions
```

## Cache assessment

No cache is required or desirable for this operation.

A stable RelationshipDefinition topology cache may contain:

- Definition id
- symmetry
- Resolution id
- from_template_id
- to_template_id

but should not contain mutable Resolution names or `default_version`.

The public SET_DEFAULT response requires those current mutable fields, so PostgreSQL remains the correct source for the returned aggregate. Do not expand the stable cache only to avoid this rare model-plane read.

## Denormalization assessment

No new denormalization is justified by SET_DEFAULT.

## Deferred concurrency question

Whether the target one-statement mutation is sufficient as the complete concurrency rendezvous with concurrent DEPRECATE must be proven in the later global concurrency phase. Do not redesign locks during this discovery phase.

## Candidate decision

`RelationshipDefinition.SET_DEFAULT` should avoid loading the target property schema and should aim for a one-statement PostgreSQL validation + update + aggregate projection. Preserve current diagnostic distinctions and the complete public response. No cache fill, cache invalidation, or new denormalization is needed.
