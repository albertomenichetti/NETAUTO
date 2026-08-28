# M4 WIP — Object DELETE public contract

Status: FROZEN DISCOVERY INPUT / M4 WIP / ALWAYS NON-NORMATIVE

## Scope

This note records the current route-local public-contract candidate for Object DELETE during M4 discovery.

It is a local working checkpoint only. It is not architecture authority and remains subject to architecture-phase revalidation.

## Candidate route

```http
DELETE /api/v1/core/objects/{object_id}
```

No request body is accepted.

No query parameter is introduced for:

```text
force
cascade
recursive/subtree deletion
implicit detach
implicit Relationship deletion
```

Object DELETE removes only the explicitly selected Object.

## Candidate success

```http
204 No Content
```

DELETE is a mutation of an existing resource and does not return the deleted Object representation.

## Candidate failure semantics

### Missing path target

```text
Object does not exist
    -> 404 resource_not_found
```

A repeated DELETE after an already committed deletion therefore returns 404; Object DELETE is not a convergent already-absent 204 operation.

### Current lifetime blocker

```text
at least one current reference requires Object lifetime
    -> 409 delete_blocked
```

DELETE does not remove or rewrite blockers to become admissible.

Current blocker families include ownership and factual Relationship references, plus any other current cross-aggregate reference that the final relational architecture protects.

## Bounded public diagnostic contract

M4 DELETE does not promise exact blocker census information.

Candidate `delete_blocked` detail requires only bounded resource identity, for example:

```json
{
  "resource_type": "object",
  "id": "<uuid>"
}
```

The public contract does **not** require:

```text
complete blocker-type enumeration
exact blocker counts
blocker identities
unbounded blocker lists
```

An implementation may expose a bounded blocker classification only when that information is already available from required execution work, but the route must not require extra PostgreSQL work solely to enrich the diagnostic.

## No diagnostic-only PostgreSQL work

Candidate rule:

```text
no PostgreSQL statement is required solely to compute
blocker counts/types for a delete_blocked response
```

This intentionally supersedes the current AS-IS expectation that `delete_blocked` exposes exact blocker type/count information obtained through a dedicated blocker-count projection.

The later Object DELETE data-path discovery should therefore evaluate whether required deletion admission can rely directly on authoritative relational/FK arbitration rather than paying a mandatory pre-count round trip.

## Semantic guarantees retained

This candidate public-contract change does not weaken the underlying lifetime guarantee:

```text
Object DELETE must not commit while a current reference
requiring that Object lifetime remains committed.
```

The final M4 architecture must prove the concrete relational/concurrency realization before implementation.

## Frozen discovery takeaway

```text
DELETE /objects/{object_id}

no body
no force/cascade

success -> 204
missing target -> 404 resource_not_found
current lifetime blocker -> 409 delete_blocked

no public obligation for blocker counts/types
no diagnostic-only PostgreSQL query requirement
```
