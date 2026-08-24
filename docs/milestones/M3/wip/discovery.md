# M3 — Preliminary Discovery Summary

**Status:** WIP / NON-NORMATIVE

**Role:** discovery aid only. This file records current findings, hypotheses and candidate principles. It does not define the M3 contract, architecture or implementation authority.

## 1. Purpose of the discovery

M3 is being explored as a focused kernel-simplification milestone with three bounded problem areas:

1. CLI post-create correctness.
2. Complete audit of all public business GET/read paths.
3. Verification and possible correction of the `parent_template_id = null` filter contract.

The milestone contract must not be frozen until these three areas have been closed enough that scope, observable deltas and acceptance criteria are unambiguous.

---

## 2. Area A — CLI post-create correctness

### Observed defect

A DataType `create` operation was observed to complete successfully on the remote HTTP API (`201 Created`, persisted resource, valid `Location`) while the CLI subsequently returned a local `cli_internal_error`.

The current evidence indicates the failure occurs after remote success while processing the command registry `Location` template. The DataType create spec uses a dotted placeholder form such as:

```text
/api/v1/core/datatypes/{datatype.id}
```

while the local lookup/materialization path does not resolve that template consistently.

### Discovery objective

Do not treat this only as a one-line DataType fix. Audit every command that performs local processing after a successful remote create response, especially every registry `location` template and the common code that resolves it.

### Candidate requirement to validate for the contract

A remotely successful and committed mutation must not be reported as a semantic failure solely because local CLI response decoration, rendering or `Location` materialization fails afterward.

The exact CLI behavior for an unexpected local post-success failure still needs to be designed and frozen; discovery must first identify the complete affected command set and common mechanism.

---

## 3. Area B — Complete GET/read-path audit

### Scope

The current public business API exposes 22 canonical GET/read routes. Discovery must review them one by one rather than extrapolating from the first findings.

For every GET, record at minimum:

```text
route / public projection
application query method
persistence calls and statement count
semantic checks performed on persisted state
use of coherent_read()
reason, if any, that multiple statements require one snapshot
whether one SQL statement can materialize the required projection cleanly
failure semantics
cursor/filter semantics where applicable
```

### Candidate architectural principle

The working principle to validate across the full census is:

```text
mutation
    -> validates and preserves semantic invariants

database
    -> preserves structural invariants expressible as constraints / FK

GET / read
    -> trusts persisted state
    -> locates, composes and projects it
    -> does not re-certify semantic invariants already owned by mutation paths
```

The criterion for read-side validation is semantic ownership, not cost. A cheap validation is still a validation and should not remain in a GET merely because it is inexpensive.

Operational protections such as generic timeouts are distinct from semantic integrity checks and must not be used to blur that ownership boundary.

### `coherent_read()` working rule

`coherent_read()` is not a target for blanket removal.

Its use must be explicitly justified by a real multi-statement projection that would otherwise be capable of assembling state from different committed snapshots.

Working rule:

```text
single statement sufficient
    -> ordinary statement snapshot should be sufficient

multiple statements semantically required to describe one projection
    -> coherent snapshot may be justified

multiple statements exist only because persistence is fragmented
    -> evaluate a single-statement materialization before retaining stronger read UoW semantics
```

### Known findings from the walkthrough

These are discovery findings, not frozen decisions.

#### DataType lineage list/get

Current reads re-check that a persisted `default_version` resolves to a PUBLISHED exact version. This appears to duplicate a semantic invariant already enforced by mutation workflows; the extra read is also the reason a coherent read snapshot is useful there.

Candidate simplification: trust the persisted default pointer semantics in normal reads and remove the second semantic certification query if the complete mutation audit confirms the invariant is fully owned on write.

#### ObjectTemplate lineage list/get

The same pattern exists: lineage reads re-check `default_version -> PUBLISHED` even though the database already guarantees exact-target existence through FK and mutation paths own lifecycle admissibility.

Candidate simplification is analogous to DataType, subject to full write-path verification.

#### ObjectTemplate exact version GET

The current store materializes one `ObjectTemplateVersion` through separate reads for:

```text
version header
local properties
local components
```

Here `coherent_read()` has a concrete justification with the current persistence shape: without one snapshot, a concurrent DRAFT revision/delete could produce a mixed projection that never existed as one committed state.

Candidate improvement: evaluate a single SQL statement that materializes header + properties + components without cartesian multiplication, for example through independent aggregation/subquery strategies. If achieved cleanly, the stronger multi-statement read transaction may become unnecessary for this GET.

#### ObjectTemplate effective schema

The effective-schema read legitimately composes an exact inheritance chain, but the current traversal also performs semantic re-validation of persisted declarations and inheritance consistency.

Working direction: separate projection/composition from semantic certification. Persisted state should be considered already certified by mutation paths. Discovery must identify which checks are truly required to compute the projection and which merely re-prove invariants such as:

```text
local declaration validity
parent pair validity
acyclic inheritance
stable-lineage / exact-parent agreement
exact parent existence / admissibility
```

Existence required to load a referenced row is a lookup concern; semantic re-certification of invariants is not automatically a read concern.

### Important non-conclusion

M3 discovery has **not** concluded that every `coherent_read()` should disappear or that every multi-query read must become one SQL statement. Each of the 22 GETs must be classified explicitly.

---

## 4. Area C — `parent_template_id = null`

### Current intended shape visible in the implementation

The ObjectTemplate list path carries both:

```text
parent_template_id: UUID | None
parent_filter_set: bool
```

and persistence supports three semantic states:

```text
parent filter absent
    -> do not filter by parent

parent filter present with UUID
    -> parent_template_id = UUID

parent filter present with None
    -> parent_template_id IS NULL
    -> root ObjectTemplates only
```

Cursor identity also records `parent_filter_set`, which shows that omission and an explicit root filter are intended to be distinct query states.

### Suspected public-contract gap

The HTTP route currently exposes `parent_template_id` as `UUID | None` in a query string. A query string does not naturally carry JSON `null`; common lexical forms such as empty string or `null` are not valid UUIDs under the current parser.

Therefore the application/persistence tri-state may include a state that cannot currently be expressed through the public HTTP carrier.

### Required discovery

Verify this with exact public HTTP evidence, including at least:

```text
parameter omitted
valid UUID
empty value
literal "null"
any currently documented/CLI-generated nullable form
unknown/duplicate parameter handling
cursor continuation for each reachable filter state
```

Then determine whether the current architecture already specifies a canonical public representation for "root only". If it does not, this is an architecture/public-contract decision for M3 rather than a local parser fix.

Any correction must be propagated coherently through:

```text
HTTP contract
FastAPI carrier/parsing
application filter identity
cursor encoding/validation
CLI parameter model and examples
API/CLI regression evidence
```

---

## 5. Preliminary scope boundary

At this stage M3 discovery includes only the three areas above.

Explicitly not yet included:

```text
general lock-plan redesign
broad mutation-lock minimization
new business capabilities
new model resources
schema redesign unrelated to the three discovery areas
unrelated CLI redesign
```

Additional findings discovered while auditing the 22 GETs may be proposed, but they must be reviewed before being added to the M3 contract.

---

## 6. Discovery completion checklist

Before drafting/finalizing the M3 contract:

- reproduce and bound the CLI post-create defect across all relevant create actions;
- complete the 22-GET census with statement counts, semantic read checks and coherent-read rationale;
- identify every concrete single-statement projection candidate and every GET where coherent snapshot semantics remain justified;
- verify the actual HTTP behavior of `parent_template_id` omission / UUID / null-like inputs;
- determine whether root-only filtering already has normative wire semantics or requires an explicit M3 decision;
- map every proposed delta to the current authoritative AS-IS documents under `docs/architecture/`;
- convert only closed discovery conclusions into contract outcomes and acceptance criteria.
