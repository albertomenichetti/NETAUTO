# M4 WIP — Mutation response semantics discovery

Status: WIP / NON-NORMATIVE

## Scope

This note records an M4 API-design candidate that emerged while revisiting the public Object representation. It is intentionally broader than the Object family because the same question applies to mutation endpoints throughout the public API.

This is discovery only. It does not freeze the public contract and does not authorize implementation.

## Concrete problem

Today several mutations return the full public DTO of the mutated resource. For Object, for example, CREATE, RENAME, DATA_CHANGE and SCHEMA_CHANGE currently return `ObjectDto`.

That becomes increasingly awkward if `GET /objects/{id}` evolves into a richer representation containing both current properties and all direct component children. A rename that changes only `canonical_name` would then have to pay the cost of reconstructing the complete Object GET response solely because the mutation response reuses the same DTO.

Concrete example:

```text
POST /objects/server-1/rename
    changes only canonical_name

if mutation returns complete Object:
    reload Object
    + effective component slots
    + all direct object_components
    + child Object canonical names
    merely to build the response body
```

That couples mutation cost to read-projection richness.

## Strong candidate separation

Current brainstorming favors separating these two concrete questions:

```text
"Did the requested mutation succeed?"
    -> mutation response

"What does the resource look like now?"
    -> GET
```

For an existing resource mutation, the strong candidate is therefore:

```text
successful mutation
    -> 204 No Content
```

rather than returning the complete post-mutation public representation or an artificial `{ "status": "ok" }` body.

Examples:

```text
POST /objects/{id}/rename
    -> 204 No Content

POST /objects/{id}/data-change
    -> 204 No Content

POST /objects/{id}/schema-change
    -> 204 No Content

POST /objects/{parent}/attach
    -> 204 No Content

POST /objects/{parent}/detach
    -> 204 No Content

DELETE /objects/{id}
    -> 204 No Content
```

The same principle is a candidate for equivalent non-creating mutations in DataType, ObjectTemplate, RelationshipDefinition and factual Relationship families, subject to operation-by-operation review before any normative freeze.

## GET remains the representation surface

If a client needs the resulting resource after a successful mutation, it performs the corresponding GET.

Concrete flow:

```text
POST /objects/server-1/rename
    -> 204

GET /objects/server-1
    -> current complete public representation
```

This avoids making every mutation implicitly execute a complete read projection after its business work.

## CREATE is a distinct case

Creation differs because the client may not know the newly allocated resource identity before the request.

Strong candidate:

```text
POST collection
    -> 201 Created
    -> Location: canonical URI of the newly created resource
```

A response body is not automatically required merely to repeat the newly created representation.

Possible creation-specific minimal carriers remain OPEN where the server allocates an identity that is operationally useful to the caller, for example:

```text
Object CREATE
    -> Location identifies new Object id

create-next exact version
    -> newly allocated version number may need an explicit minimal carrier
```

Whether `Location` alone is sufficient for each create operation, or whether some operations need a minimal created-identity body, must be decided per operation.

## Why this matters for M4 optimization

This separation lets a mutation pay only for the data required to admit and execute that mutation.

Example:

```text
RENAME
    needs current Object + new name + lifecycle event
    does not need component expansion

DATA_CHANGE
    needs current Object + compiled exact schema + new properties
    does not need component expansion

ATTACH
    needs parent/child/current ownership/slot admission/cycle check
    does not need a complete parent Object response
```

The public GET may independently become richer without inflating all mutation paths.

## Architectural reading

The concrete API choice corresponds to separating command acknowledgement from resource representation. Mutation endpoints own command outcome semantics; GET endpoints own complete current public projections.

This is particularly valuable in NETAUTO because model/read projections can include materialized effective schema, direct component expansion and other data that are irrelevant to many individual mutations.

## Interaction with lifecycle events

This proposal changes HTTP response shape only. It does not remove or weaken lifecycle event generation.

A successful mutation still writes the lifecycle event required by the domain contract inside the same Unit of Work. Historical event payload design remains a separate concern.

## Open decisions

- exact operation matrix for `204 No Content` across every non-creating mutation family;
- whether idempotent no-op mutations return the same success status as a state-changing execution;
- CREATE response rules per resource family;
- whether `Location` alone is sufficient for Object/DataType/ObjectTemplate/RelationshipDefinition CREATE;
- minimal carrier, if any, for operations that allocate a new exact version number;
- whether factual Relationship CREATE uses `201 + Location` only or needs a minimal created identity carrier;
- compatibility/migration strategy for clients currently expecting mutation DTO bodies;
- whether any mutation has a concrete consumer need strong enough to justify returning data despite the default no-content rule.

## Candidate first-phase conclusion

Use `204 No Content` as the default successful response for mutations of existing resources, keep `GET` as the authority for the resulting public representation, and treat creation as a separate `201 Created + Location` design problem with minimal additional carriers only where concretely necessary.
