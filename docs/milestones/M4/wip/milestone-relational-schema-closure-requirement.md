# Milestone closure — complete relational schema documentation requirement

Status: GOVERNANCE HANDOFF / M4 WIP / NON-NORMATIVE GLOBALLY

## Purpose

This WIP records a documentation-governance requirement to be promoted into the project governance / milestone-closure rules.

From this point forward, the documentation closure of **every milestone** must produce or update a Markdown document that describes the **complete relational schema resulting from that milestone**.

The artifact is not a delta-only migration note. It must provide a reader with a complete, current picture of the relational persistence model after the milestone has been closed.

The final canonical path/name of this artifact is intentionally not frozen by this WIP; that must be decided when the governance documentation is updated.

## Mandatory scope

The milestone relational-schema artifact must cover, at minimum, every persisted relational structure that is part of the delivered system:

```text
all tables
all columns relevant to the relational contract
primary keys
foreign keys
unique constraints
check constraints
nullability where semantically relevant
defaults where semantically relevant
indexes
referential actions / lifetime behavior where relevant
materialized / derived / denormalized tables or columns
```

The document must describe the **complete resulting schema**, including structures unchanged by the milestone when they remain part of the delivered persistence model.

## Per-table documentation

For each table the document must make clear:

```text
purpose / semantic role
owned vs independent state where relevant
columns and their meaning
primary key
foreign keys
other integrity constraints
indexes
whether the table is authoritative or derived/materialized
```

Where useful, the table definition may be represented in a compact relational form, SQL-like form, Markdown table, or another unambiguous textual notation.

## Denormalization / materialization must be explicit

Every denormalized or materialized structure must be explicitly marked as such.

For each denormalized table, column or persisted derived projection, the documentation must explain:

```text
what authoritative normalized/model state it derives from
which consumer/workload it optimizes
why the duplication/materialization is preferred
when/how it is produced or refreshed
why it is safe from semantic staleness, or which consistency mechanism protects it
what additional write/storage cost is intentionally accepted
```

The document must not present denormalized state as if it were an independent semantic authority unless that is intentionally part of the architecture.

Examples of the type of explanation expected include:

```text
object_template_effective_properties
    -> denormalized/materialized exact effective schema
    -> produced at ObjectTemplate publication
    -> avoids runtime inheritance reconstruction
    -> immutable for the exact published/deprecated version

object_template_ancestry
    -> stable lineage closure
    -> avoids repeated recursive lineage traversal
    -> safe because parent_template_id is stable for lineage lifetime
```

These are examples only; the closure artifact must reflect the actual delivered schema of the milestone.

## Primary keys must be justified

For every primary key, the document must explain why that key shape represents the intended identity/invariant.

Examples of questions the explanation should answer:

```text
Why is this the row identity?
Why is the key single-column or composite?
Which business invariant is enforced by that choice?
Does the key also encode ownership or uniqueness semantics?
```

A PK must not be documented only as syntactic DDL such as `PRIMARY KEY (...)`; its architectural reason must be stated.

## Foreign keys must be justified

For every foreign key, the document must explain:

```text
which semantic reference it protects
which lifetime/reference-integrity guarantee it provides
why the referenced relation is the correct authority
which ON DELETE / ON UPDATE behavior is used, when relevant
why RESTRICT / CASCADE / other behavior is appropriate
```

If an apparently natural FK is intentionally absent, that absence should also be documented when it is architecturally significant.

## Indexes must be justified

For every non-PK index, the document must explain the workload/access path it exists to support.

The explanation should identify, where applicable:

```text
consumer operations/routes
filter or lookup prefix
ordering / pagination requirement
join path
uniqueness role, if any
why the indexed column order is intentional
why INCLUDE / partial / covering behavior is or is not required
```

Indexes must not be treated as unexplained implementation debris. Every retained index at milestone closure must have an explicit reason tied to the delivered workload or integrity model.

If an index exists only for a database-enforced FK/constraint implementation detail rather than a business access path, that reason should be stated explicitly.

## Completeness and synchronization requirement

The relational-schema artifact is part of milestone documentation closure and therefore must be synchronized with the actually delivered database schema.

A milestone must not be considered documentally closed if the schema artifact:

```text
omits delivered tables or indexes
still describes removed structures
misstates PK/FK/constraint behavior
fails to identify denormalized/materialized structures
fails to explain the rationale for PKs, FKs or indexes
```

The closure review should compare the document against the delivered migrations / DDL / persistence implementation and update it before the milestone is declared complete.

## Intended governance rule

The rule to promote into normative project governance is conceptually:

> Every milestone documentation closure must leave behind an updated Markdown description of the complete resulting relational schema. The document must cover tables, keys, constraints and indexes; explicitly identify and justify denormalized/materialized structures; and provide an architectural rationale for every PK, FK and retained index.

## M4 handoff

M4 itself must satisfy this requirement when its documentation closure is eventually performed.

Because M4 is explicitly revisiting persistence, denormalization/materialization and physical access paths, its final relational-schema artifact will be an important closure deliverable and should be verified against the final frozen M4 architecture and delivered migrations.
