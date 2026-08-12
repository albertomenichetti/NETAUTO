# Data-Plane Concurrency Characterization (SQLite)

## Scope And Methodology

This document records observed data-plane concurrency behavior for the current
SQLite plus SQLAlchemy backend.

Scope:

- runtime Object workflows
- runtime ComponentMembership workflows
- runtime Relationship workflows

Out of scope:

- model-plane serialization
- PostgreSQL behavior
- concurrency hardening design

Methodology:

- real SQLite file databases
- separate Sessions and connections per contender
- foreign keys enabled
- deterministic thread synchronization using `threading.Barrier` and
  `threading.Event`
- no randomization
- no arbitrary timing sleeps
- no production code changes

## SQLite Caveat

These observations are authoritative for the current SQLite backend only.

Where a scenario is safe or fails safely because of SQLite transaction or lock
behavior rather than a structural constraint, that protection is backend
specific and must not be assumed to hold for PostgreSQL.

## Classification Definitions

- `SAFE_BY_CONSTRAINT`
  The invalid committed state is structurally impossible because of a physical
  relational constraint.
- `SAFE_BY_SEMANTICS`
  Existing domain semantics make the combined committed result valid.
- `FAILS_SAFELY`
  No invalid committed state is produced, but one contender fails because of
  current backend or persistence behavior.
- `UNSAFE`
  A committed outcome violates an invariant or cannot be explained by any valid
  serial execution of the two operations.

Protection sources:

- `PHYSICAL_CONSTRAINT`
- `APPLICATION_SEMANTICS`
- `SQLITE_WRITER_LOCKING`
- `NONE`

Portability:

- `PORTABLE`
- `SQLITE_SPECIFIC`

## Scenario Matrix

| Scenario | Invariant | Interleaving | Observed outcomes | Final state | Classification | Protection source | Portable? | C1 candidate? | PostgreSQL revisit? | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C0.1 same child, competing owners | one child has at most one direct owner | both pass owner check, `attach_a` writes first, stale `attach_b` writes second | `attach_a` succeeds; `attach_b` raises `ComponentMembershipAlreadyExists` | one membership row remains; child owned by `attach_a` parent | `SAFE_BY_CONSTRAINT` | `PHYSICAL_CONSTRAINT` | yes | no | no | protected by `object_components.child_object_id PRIMARY KEY` |
| C0.2 reciprocal attach `A->B` / `B->A` | ownership graph acyclic | both pass owner and cycle checks, `attach_a` writes first, stale `attach_b` writes second | both operations succeed | committed two-edge cycle `A->B` and `B->A` | `UNSAFE` | `NONE` | n/a | yes | no | single-edge self-check does not protect multi-node cycles |
| C0.3 concurrent Object updates | a successful update must not silently erase another successful update | both load the same object, `update_a` writes first, stale `update_b` writes second | both updates succeed | final object keeps only `b=new-b`; `a=new-a` is lost; both history entries record the same original `before` snapshot | `UNSAFE` | `NONE` | n/a | yes | no | demonstrated lost update |
| C0.4 Object update vs migration | committed migration must not be silently reverted by stale update | migration reads v1 object, update reads same v1 object, migration writes first, stale update writes second | migration succeeds; update succeeds | final object is back on template version 1 with updated properties; migration history exists but live row is reverted | `UNSAFE` | `NONE` | n/a | yes | no | demonstrated stale replacement reverting migration |
| C0.5 duplicate runtime Relationship create | no duplicate `(definition, source, target)` triple | both validate and see no duplicate, `create_a` writes first, stale `create_b` writes second | `create_a` succeeds; `create_b` raises `RelationshipAlreadyExists` | one relationship row remains | `SAFE_BY_CONSTRAINT` | `PHYSICAL_CONSTRAINT` | yes | no | no | protected by relationship triple `UNIQUE` |
| C0.6 subtree delete vs attach | delete result must correspond to a valid serial order | delete completes subtree discovery for `{R}`, attach validates, attach commits, stale delete resumes | delete succeeds; attach succeeds | `R` deleted; `C` survives detached; no membership row; delete history recorded only for `R` | `UNSAFE` | `NONE` | n/a | yes | no | not explainable by attach-then-delete or delete-then-attach |
| C0.7 Relationship create vs endpoint delete | no orphan relationship endpoints | delete completes incident relationship listing, create validates and commits, stale delete resumes | relationship create succeeds; delete raises raw `IntegrityError` | source object survives; relationship survives; no delete history row committed | `FAILS_SAFELY` | `PHYSICAL_CONSTRAINT` | yes | no | no | endpoint FK `RESTRICT` prevents orphaned relationship |

## Observed Exceptions And Outcomes

- C0.1 loser exception: `ComponentMembershipAlreadyExists`
- C0.2 exceptions: none
- C0.3 exceptions: none
- C0.4 exceptions: none
- C0.5 loser exception: `RelationshipAlreadyExists`
- C0.6 exceptions: none
- C0.7 delete exception: raw SQLAlchemy `IntegrityError` wrapping SQLite FK failure

## Safe Enough Now

- C0.1 same-child competing owners
- C0.5 duplicate runtime Relationship create
- C0.7 Relationship create vs endpoint delete

These do not require C1 work on the current SQLite backend because the relevant
invariant is already protected physically.

## C1 Candidates

Only demonstrated `UNSAFE` SQLite races belong here.

- C0.2 reciprocal attach / ownership cycle race
  Mechanism family: graph-edge coordination or targeted serialization
- C0.3 concurrent Object updates
  Mechanism family: optimistic conditional write
- C0.4 Object update vs migration
  Mechanism family: optimistic conditional write or targeted serialization
- C0.6 subtree delete vs attach
  Mechanism family: delete/attach coordination

## Remediation Status

- C0.2 reciprocal attach / ownership cycle race
  remediated by M2.C1b ownership-graph coordination
- C0.3 concurrent Object updates
  remediated by M2.C1a optimistic conditional Object replace
- C0.4 Object update vs migration
  remediated by M2.C1a optimistic conditional Object replace
- C0.6 subtree delete vs attach
  remediated by M2.C1b ownership-graph coordination
- C0.1 same-child competing owners
  physical PK remains the structural guarantee; C1b now also serializes
  supported attach decisions before the owner check
- C0.5 duplicate runtime Relationship create
  unchanged; remains protected by physical constraint
- C0.7 Relationship create vs endpoint delete
  unchanged historically; remains fail-safe via physical FK protection

## Post-C1 Status Notes

- C0.1 same-child competing owners
  Supported concurrent attach workflows now serialize through
  `OWNERSHIP_GRAPH_GUARD`, so the stale double-owner-check interleaving is no
  longer reachable through supported application paths. The physical
  `PRIMARY KEY(child_object_id)` remains the structural defense-in-depth
  guarantee.
- C0.2 reciprocal attach / ownership cycle race
  Supported concurrent attach workflows now serialize through
  `OWNERSHIP_GRAPH_GUARD`. The second attach revalidates after guard
  acquisition and observes the committed first edge, so the stale reciprocal
  cycle interleaving is no longer reachable through supported workflows.
- C0.6 subtree delete vs attach
  Supported `delete_object` and `attach_component` workflows now serialize
  through `OWNERSHIP_GRAPH_GUARD`. Subtree discovery is performed while the
  guard is held, so stale discovery cannot survive a concurrent supported
  attach or detach.
- C0.7 Relationship create vs endpoint delete
  Historical C0 classification remains `FAILS_SAFELY` with portable endpoint
  FK protection. On SQLite after C1b, `delete_object` acquires the ownership
  writer reservation before incident-relationship discovery, so SQLite may
  physically serialize runtime Relationship creation earlier than PostgreSQL
  eventually will. PostgreSQL runtime Relationship safety must still rely on
  relational FK behavior because runtime Relationship creation does not acquire
  `OWNERSHIP_GRAPH_GUARD`.

## PostgreSQL Revisit

None of the characterized mandatory scenarios were safe only because of SQLite
writer locking. The unsafe cases committed on SQLite, and the safe cases were
protected by physical constraints.

PostgreSQL still requires a fresh concurrency review because backend behavior
will differ, but this slice did not produce a SQLite-specific fail-safe case in
the mandatory matrix.

Additional future characterization items:

- `delete_object` vs concurrent Object property update
- `delete_object` vs concurrent Object migration

## Invariants Physically Protected By S3 Constraints

- one child has at most one direct owner
  Source: `object_components.child_object_id PRIMARY KEY`
- no direct self ownership
  Source: `CHECK(parent_object_id <> child_object_id)`
- no duplicate runtime relationship triple
  Source: `UNIQUE(relationship_definition_id, source_object_id, target_object_id)`
- no orphan runtime relationship endpoints
  Source: relationship endpoint FKs with `RESTRICT`
- no nonexistent runtime ObjectTemplateVersion pin
  Source: object exact template-version FK

## Items That Do Not Require C1

- same-child competing owners, because the direct-owner invariant is already
  structurally enforced
- duplicate runtime Relationship create, because duplicate triples are already
  structurally enforced
- Relationship create vs endpoint delete, because endpoint FK `RESTRICT`
  prevents orphan relationships and the stale delete rolls back

## Unresolved Or Untested Cases

- optional C0.8 attach vs detach same child was not implemented
- no broader pairwise matrix beyond the required scenarios
- PostgreSQL concurrency behavior remains uncharacterized
