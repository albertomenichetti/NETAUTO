# M2 WIP — First Durable Alembic Kernel Baseline

**Status:** ALEMBIC BASELINE DESIGN CLOSED

**Authority:** DISCOVERY CAPTURE — NON-NORMATIVE

This document is the Alembic/schema-realization addendum to:

```text
docs/milestones/M2/wip/relationship-properties.md
docs/milestones/M2/wip/relationship-properties-persistence.md
docs/milestones/M2/wip/relationship-properties-lifecycle.md
docs/milestones/M2/wip/relationship-properties-indexes.md
```

It supersedes the previously assumed requirement for a data-preserving `M1 -> M2` Alembic migration.

The supersession is valid because the delivered M1 software is not deployed against any durable production or user database, and every current development database is disposable and recreatable.

M1 remains the authoritative delivered software and architecture AS-IS used for semantic and functional cross-checks. It is not a supported database-migration source.

---

## 1. Governing decision

M2 establishes the **first durable Alembic baseline** of the NETAUTO kernel.

Alembic is re-initialized to create directly the complete relational schema consisting of:

```text
current delivered AS-IS guarantees
+
all frozen M2 schema extensions
```

The revision history is not required to preserve the intermediate development evolution represented by:

```text
0001_m1_schema
0002_relationship_resolution_name_nonkey
```

The implementation will replace that history with one initial revision conceptually shaped as:

```text
migrations/versions/0001_initial_kernel_schema.py

revision = "0001_initial_kernel_schema"
down_revision = None
```

The exact filename and revision identifier may follow the repository naming convention at implementation time, but the semantic contract is one root revision with no predecessor.

---

## 2. No in-place upgrade source

The new baseline supports:

```text
empty PostgreSQL database
    -> alembic upgrade head
    -> complete M2 kernel schema
```

It does not support:

```text
0001_m1_schema database -> M2 in place
0002_relationship_resolution_name_nonkey database -> M2 in place
manually drifted M1 schema -> M2 in place
partially migrated database -> M2 in place
```

Every pre-baseline development database must be handled through:

```text
drop/recreate database
alembic upgrade head
```

Do not use `alembic stamp` to relabel an old physical schema as the new baseline. `stamp` changes revision metadata without realizing the required DDL and would conceal schema drift.

---

## 3. Direct M2 creation semantics

The fresh baseline creates no legacy rows and performs no synthetic semantic backfill.

In particular, it does **not** manufacture:

```text
legacy RelationshipDefinition -> v1 PUBLISHED
legacy RelationshipDefinition.default_version -> 1
legacy Relationship -> exact RDV v1 + properties {}
legacy lifecycle Relationship snapshots
```

New resources follow the M2 command contract directly:

```text
RelationshipDefinition.CREATE
    -> stable Definition header
    -> complete Resolution set
    -> RDV v1 DRAFT revision 1
    -> default_version = NULL
```

The distinction is important:

```text
M1-compatible data bridge
    -> unnecessary because no durable M1 data exists

M2 runtime semantics
    -> authoritative for every newly created database
```

---

## 4. Complete authoritative schema

The initial revision creates exactly fifteen NETAUTO authoritative tables.

### Model plane — 10

```text
datatypes
datatype_versions
object_templates
object_template_versions
object_template_properties
object_template_components
relationship_definitions
relationship_resolutions
relationship_definition_versions
relationship_definition_properties
```

### Data plane — 4

```text
objects
object_components
relationships
runtime_relationship_resolutions
```

### History — 1

```text
object_lifecycle_events
```

The revision creates directly the final approved:

```text
columns
types
PRIMARY KEY constraints
technical and semantic UNIQUE constraints
CHECK constraints
foreign keys
CASCADE / RESTRICT actions
server defaults
explicit indexes
partial predicates
INCLUDE columns
```

No later revision exists merely to remove a constraint or repair a baseline decision already known before the first durable release.

---

## 5. DDL authority and drift rule

The final SQLAlchemy metadata and the initial Alembic revision must describe the same schema exactly.

The implementation workflow is:

```text
1. freeze final SQLAlchemy metadata
2. realize one initial Alembic revision from that authority
3. inspect and adjust generated DDL deliberately
4. verify live PostgreSQL schema against metadata
5. require compare_metadata differences == []
```

The revision must be self-contained. It must not import mutable application metadata or domain code at migration execution time.

Explicit names are required for:

```text
PK where project convention requires it
UNIQUE constraints
CHECK constraints
foreign keys
indexes
```

Stable names remain part of constraint-race diagnostics, migration verification and persistence traceability.

---

## 6. DDL creation order

The revision creates dependency roots before their consumers and adds intentional cyclic default pointers only after both sides exist.

Conceptual order:

```text
1. independent historical authority
       object_lifecycle_events

2. stable lineage/root tables
       datatypes
       object_templates
       relationship_definitions

3. exact version tables
       datatype_versions
       object_template_versions
       relationship_definition_versions

4. cyclic default-version foreign keys
       datatypes -> datatype_versions
       object_templates -> object_template_versions
       relationship_definitions -> relationship_definition_versions

5. model declarations and topology children
       object_template_properties
       object_template_components
       relationship_resolutions
       relationship_definition_properties

6. factual current-state roots
       objects
       relationships

7. current-state owned children
       object_components
       runtime_relationship_resolutions

8. explicit indexes not owned by PK/UNIQUE constraints
```

Equivalent dependency-safe ordering is acceptable, but all three default-version cycles must follow the same intentional pattern.

---

## 7. RelationshipDefinition default-version cycle

The fresh schema contains:

```text
relationship_definition_versions.relationship_definition_id
    -> relationship_definitions.id
    ON DELETE CASCADE
```

and:

```text
relationship_definitions(id, default_version)
    -> relationship_definition_versions(
           relationship_definition_id,
           version
       )
    ON DELETE RESTRICT
```

The first FK expresses owned-version lifetime. The second expresses one optional exact default pointer.

The second FK is added only after both tables exist, using the same pattern already established for DataType and ObjectTemplate default-version cycles.

Application root-delete realization may clear the internal default pointer before deleting the root when required by PostgreSQL execution ordering. That is internal aggregate cleanup, not a semantic blocker and not a public mutation.

---

## 8. Lifecycle schema is created directly in M2 form

The initial revision creates `object_lifecycle_events` with the complete M2 vocabulary:

```text
CREATED
RENAME
DATA_CHANGE
SCHEMA_CHANGE
ATTACH_TO
DETACH_FROM
RELATIONSHIP_CREATED
RELATIONSHIP_DATA_CHANGE
RELATIONSHIP_SCHEMA_CHANGE
RELATIONSHIP_DELETED
DELETED
```

Its family/state checks are created directly with the final M2 nullability rules.

There is no lifecycle backfill phase and no temporary support for Relationship events with both snapshots null.

The sole accepted Relationship lifecycle shapes are the M2 shapes defined in the lifecycle WIP.

---

## 9. Index realization

The initial revision creates directly the final index inventory from:

```text
docs/milestones/M2/wip/relationship-properties-indexes.md
```

This includes:

```text
new RDV and declaration indexes
Resolution aggregate/name indexes
exact-RDV Relationship consumer index
replacement Object-relative runtime indexes
cross-domain version/status and semantic-history hardening indexes
partial lifecycle indexes
```

It intentionally omits:

```text
GIN indexes on runtime properties
GIN/expression indexes on lifecycle snapshots
standalone default_version indexes
duplicate partial PUBLISHED indexes
a second factual-identity index
event-set grouping indexes
```

Because the database is created empty, no create-before-drop replacement sequence is needed inside the initial revision: only the final index definitions are emitted.

---

## 10. Operational cutover policy

No rolling compatibility contract is required between old and new application/schema generations.

Unsupported combinations are:

```text
M1 application + fresh M2 schema
M2 application + old M1 development schema
```

The only supported setup sequence is:

```text
1. stop/discard any old development runtime
2. recreate the database
3. apply the new initial revision to head
4. start the M2 application
```

This is not a production migration window and introduces no dual-write, dual-read, expand/contract or online-backfill protocol.

---

## 11. Alembic revision gate

The application should fail startup explicitly when the connected database is not at the exact revision expected by the running software.

Conceptual invariant:

```text
database Alembic revision == application expected revision
```

Failure cases include:

```text
uninitialized database
old discarded M1 revision
newer unsupported revision
missing alembic_version table
multiple unexpected heads
```

The application does not start in a degraded mode and does not discover schema incompatibility lazily on the first request.

The exact runtime location and error surface of this gate remain an implementation/architecture realization item, but the requirement belongs to the M2 baseline.

---

## 12. Downgrade contract

The only downgrade is:

```text
head -> base
```

It is intentionally destructive for NETAUTO-owned data and schema.

It must:

```text
remove all and only NETAUTO-owned constraints, indexes and tables
respect dependency order
remove cyclic default FKs before dropping their tables where required
leave unrelated external schemas/tables untouched
remove the NETAUTO Alembic revision marker through normal Alembic behavior
```

It does not attempt to convert M2 into M1 and makes no data-preservation promise.

There is therefore no:

```text
conditional M1 representability predicate
reverse lifecycle snapshot backfill
RDV collapse
property-value loss acceptance
partial downgrade
```

---

## 13. Failure and repeatability

The initial upgrade is executed transactionally under PostgreSQL/Alembic.

Required outcome:

```text
success
    -> complete final schema at head

failure
    -> no committed partial NETAUTO schema
    -> revision remains at base
```

The migration should not use `IF EXISTS` or `IF NOT EXISTS` to conceal drift in the normal path.

After a rolled-back failure, a corrected `alembic upgrade head` must be able to run from the unchanged base state.

---

## 14. Verification contract

The migration verification suite must cover at least:

### 14.1 Fresh upgrade

```text
base -> head
```

Verify:

```text
exactly fifteen NETAUTO authoritative tables
expected columns and types
expected PK/UNIQUE/CHECK/FK constraints
expected CASCADE/RESTRICT actions
expected explicit indexes and partial predicates
expected INCLUDE columns
negative index contract
single Alembic head
metadata drift == []
```

### 14.2 Downgrade isolation

```text
head -> base
```

Verify:

```text
all NETAUTO structures removed
unrelated external sentinel table preserved
```

### 14.3 Repeatability

```text
base -> head -> base -> head
```

Verify the same final schema and no residual drift.

### 14.4 Revision gate

Verify startup behavior for:

```text
expected head
base/uninitialized database
old discarded revision marker
unexpected newer/different revision
```

### 14.5 Constraint and index contract

Extend static metadata and live introspection tests to cover:

```text
fifteen-table authority
new composite exact identities
new default FK cycle
lifecycle M2 kind/state shape
new and replaced indexes
partial index predicates
negative JSONB index assertions
```

No populated-M1 upgrade, data backfill or lossless downgrade test is required.

---

## 15. Repository transition during implementation

The implementation of this decision must:

```text
remove the current development revision files:
    0001_m1_schema_initial_m1_schema.py
    0002_relationship_resolution_name_nonkey.py

create one new root initial revision
update migration and metadata tests
update expected-table counts from 13 to 15
update status/architecture references that still describe M1 as the Alembic source
```

The old revision files remain useful historical Git commits, but they do not remain executable heads in the first durable baseline.

Development databases carrying those revisions must be recreated rather than stamped or upgraded.

---

## 16. Superseded migration work

The following previously identified work is explicitly cancelled:

```text
M1 data preflight
semantic validation of legacy closures
RDV v1 PUBLISHED backfill
legacy default_version backfill
Relationship exact-version/properties backfill
lifecycle snapshot backfill
transitional nullable columns
transitional CHECK removal/re-addition
progressive FK replacement
legacy count reconciliation
M1/M2 rolling compatibility
large-data backfill batching
conditional M2 -> M1 downgrade
legacy dual snapshot decoder
```

This cancellation reduces accidental complexity without changing any frozen domain, API, persistence or lifecycle requirement.

---

## 17. Closed and remaining work

Closed by this addendum:

```text
Alembic source/target posture
first durable root revision decision
no in-place M1 upgrade
fresh fifteen-table realization
DDL dependency/cycle strategy
direct M2 lifecycle schema
index realization posture
development database recreation policy
destructive isolated head -> base downgrade
revision-gate requirement
migration verification scope
```

Still open outside this addendum:

```text
persistence consistency closure
semantic concurrency census and pairwise matrix
PostgreSQL row-lock/advisory-gate/retry realization
verification scenario registry
normative architecture propagation
M2 contract freeze
implementation sequencing
```
