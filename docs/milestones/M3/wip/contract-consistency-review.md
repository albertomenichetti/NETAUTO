# M3 Contract Consistency Review

**Status:** PASS — READY FOR HUMAN FREEZE REVIEW

**Authority:** REVIEW EVIDENCE — NON-NORMATIVE

This report records the pre-freeze consistency review performed on:

```text
docs/milestones/M3/contract.md
```

The contract remains `DRAFT / REVIEW — NOT FROZEN`. This report does not freeze the contract, authorize architecture implementation or create software implementation authority.

## 1. Review summary

```text
Discovery capability coverage          PASS
AS-IS preservation/delta closure       PASS
Cursor census/rule closure             PASS
HTTP/CLI carrier consistency           PASS
Read-boundary consistency              PASS
Outcome/acceptance traceability        PASS
Contract/architecture boundary         PASS
Normative hygiene                      PASS
Open contract-level findings              0
```

No blocking contract-level finding remains for human freeze review.

## 2. Inputs reviewed

### Repository governance

```text
AGENTS.md
README.md
docs/general/linee_guida_progetto.md
docs/milestones/M3/status.md
docs/milestones/M3/steps.md
```

### Delivered AS-IS owners materially affected by M3

```text
docs/architecture/README.md
docs/architecture/api.md
docs/architecture/cli.md
docs/architecture/datatype.md
docs/architecture/objecttemplate.md
docs/architecture/object.md
docs/architecture/relationship.md
docs/architecture/persistence.md
docs/architecture/concurrency.md
docs/architecture/verification.md
```

### Consolidated M3 discovery inputs

```text
docs/milestones/M3/wip/discovery.md
docs/milestones/M3/wip/discovery-closure.md

docs/milestones/M3/wip/cli-post-create-decision.md
docs/milestones/M3/wip/cli-post-create-closure.md

docs/milestones/M3/wip/get-read-census.md
docs/milestones/M3/wip/get-read-review-closure.md
docs/milestones/M3/wip/cursor-identity-audit.md
route-specific *-get-*-decision.md records

docs/milestones/M3/wip/parent-template-null-carrier-decision.md
docs/milestones/M3/wip/parent-template-null-carrier-closure.md
```

WIP files remain non-normative. Their closed contract-level decisions have been distilled into `contract.md`; realization details remain assigned to the future M3 architecture set.

## 3. Capability portfolio closure

Every completed discovery area is classified.

| Capability area | Classification |
|---|---|
| CLI post-create response correctness | IN SCOPE |
| Public GET/read responsibility boundary | IN SCOPE |
| Public cursor identity correctness | IN SCOPE |
| Historical lifecycle trusted decoding | IN SCOPE / READ-BOUNDARY SPECIALIZATION |
| ObjectTemplate root-only parent filtering | IN SCOPE |
| One-statement public GET realization | ARCHITECTURE HANDOFF, NOT PUBLIC CONTRACT |
| General lock-plan redesign | OUT OF SCOPE |
| Broad mutation-lock minimization | OUT OF SCOPE |
| New schema/migration/dependency | OUT OF SCOPE |
| New business route/resource | OUT OF SCOPE |
| General CLI redesign | OUT OF SCOPE |

Result:

```text
unclassified discovery capability = 0
```

## 4. Capability coverage matrix

| Capability area | Objectives | Required outcomes | Acceptance criteria |
|---|---|---|---|
| CLI create correctness | 1 | M3-OUT-01, 02 | M3-AC-01..03 |
| GET/read authority and compatibility | 2, 3 | M3-OUT-03, 04 | M3-AC-04..07 |
| Historical lifecycle decoding | 2, 3 | M3-OUT-06 | M3-AC-08 |
| Cursor identity | 4 | M3-OUT-05 | M3-AC-09..13 |
| ObjectTemplate root filter | 5 | M3-OUT-07 | M3-AC-14..16 |
| Regression / non-delta / traceability | cross-cutting | M3-OUT-08 | M3-AC-17, 18 |

Checks:

```text
in-scope capability without objective          0
in-scope capability without outcome            0
required outcome without acceptance path       0
acceptance criterion without attributable area 0
```

## 5. AS-IS preservation and delta closure

The contract preserves the delivered:

```text
63 business HTTP operations
GET /health/core
official HTTP-only CLI boundary
same-release CLI/server support model
strict request/query/body validation
finite public error catalogue
bounded details / no internal leakage
opaque keyset pagination and existing limit semantics
public DTO shapes and ordering
exact version identities and exact persisted pins
mutation semantic validation and atomicity
PostgreSQL schema and durable Alembic baseline
runtime/deployment boundary
```

The contract registers every M3 observable delta identified by discovery:

```text
1. public read semantic-certification boundary
    -> GET no longer re-certifies mutation-owned persisted semantics
    -> representationally undecodable carrier remains internal-failure boundary

2. Object components cursor identity
    -> add parent_object_id

3. Object-relative Relationship cursor identity
    -> add object_id

4. ObjectTemplate parent filter
    -> exact lowercase parent_template_id=null means root only
    -> omission remains no parent filter

5. official CLI create outcome correction
    -> valid nested-identity 201 + exact Location is success
    -> genuine Location mismatch remains cli_protocol_error
```

Result:

```text
unregistered observable M3 delta found = 0
```

## 6. Read-boundary consistency

The contract keeps three responsibilities distinct:

```text
request/cursor validation
    -> strict and unchanged

persisted semantic certification
    -> mutation responsibility
    -> removed from GET when it merely re-proves admitted state

representational carrier decoding
    -> GET responsibility when needed to construct typed output
    -> materially undecodable required state may fail safely
```

This resolves the deliberate conflict with the delivered AS-IS principle that required read-side semantic corruption certification. The change is explicit rather than silently inferred from code.

The contract does not require reads to repair, normalize or partially suppress required persisted data, and it does not weaken mutation validation.

Historical lifecycle uses the same boundary: carrier decoding remains; mutation-transition re-certification does not.

Result:

```text
read/mutation responsibility contradiction = 0
corruption-tolerance obligation introduced  = 0
mutation validation weakening authorized     = 0
```

## 7. Cursor census and identity closure

The contract includes the complete audited cursor-bearing public census:

```text
12 / 12 routes
```

The general rule is closed as:

```text
query identity
    = route
    + membership-affecting path target(s)
    + membership-affecting query filters
    + required semantic presence bits

position
    = complete canonical ordering tuple

limit
    = excluded from semantic query identity
```

The final discovery audit found exactly two incomplete current identities and no incomplete keyset ordering tuple:

```text
GET /objects/{parent_object_id}/components
    -> missing parent_object_id

GET /objects/{object_id}/relationships
    -> missing object_id

additional identity defects = 0
keyset-key defects           = 0
```

The contract adds explicit cross-path acceptance criteria for both defects and preserves lifecycle route-scope distinction through the existing involving-object identity.

Result:

```text
cursor-bearing route omitted from contract census = 0
known cursor defect omitted from delta register    = 0
```

## 8. ObjectTemplate carrier consistency

The contract keeps exactly one public filter:

```text
parent_template_id
```

HTTP semantics are unambiguous:

```text
omitted        -> no parent filter
UUID           -> direct children of that parent
lowercase null -> roots only
```

CLI semantics are the same at intent level while retaining its existing selector convenience:

```text
omitted                 -> no query pair
UUID / human selector   -> resolve/send UUID
explicit null           -> send parent_template_id=null with no selector lookup
```

The contract does not imply that HTTP accepts human ObjectTemplate selectors and does not expose `parent_filter_set` publicly.

Result:

```text
HTTP/CLI semantic mismatch      = 0
second public root filter added = 0
internal presence bit exposed   = 0
```

## 9. Contract versus architecture boundary

The contract intentionally freezes observable behavior and correctness guarantees, but does not prescribe the discovery implementation targets below:

```text
one SQL statement per public GET
specific parent-rooted LEFT JOIN layout
typed UNION ALL layout
recursive CTE shape
trusted projector helper/store method names
coherent_read removal mechanics
Location helper naming / literal replacement implementation
FastAPI/Pydantic helper naming
CLI request-planner helper decomposition
```

These remain mandatory architecture/implementation work where required to satisfy the frozen contract, but are not themselves public contract semantics.

The one-statement target remains a central M3 architecture/verification input and is not lost by omission from the public contract.

Result:

```text
implementation detail improperly frozen as public behavior = 0
closed discovery realization requirement lost entirely     = 0
```

## 10. Outcome and acceptance identifier hygiene

The draft contains unique contiguous identifier sets:

```text
M3-OUT-01 ... M3-OUT-08
M3-AC-01  ... M3-AC-18
M3-CQG-01 ... M3-CQG-08
```

The future architecture set must add the next traceability layer:

```text
M3-OUT / M3-AC
    -> architecture owner/decision
    -> steps slice
    -> implementation mechanism
    -> deterministic verification evidence
```

The contract requires that closure through `M3-OUT-08` and `M3-AC-18`.

## 11. Contradiction sweep

| Topic | Potential contradiction | Closure |
|---|---|---|
| Read corruption boundary | Delivered AS-IS re-certifies persisted semantics | Explicit M3 delta narrows GET responsibility while retaining undecodable-carrier failure |
| Coherent read guarantee | Discovery targets no `coherent_read()` on 22 GETs | Contract preserves self-consistent single-request projection and leaves realization to architecture |
| One-statement target | Strong discovery realization conclusion | Deliberately architecture/verification handoff, not public contract behavior |
| Cursor path target | Route discriminator alone might appear sufficient | Contract explicitly includes membership-affecting path targets in query identity |
| Cursor limit | Changing page size could be interpreted as mismatch | Contract explicitly excludes `limit` from semantic query identity |
| Lifecycle global/object route | Shared internal route token could collide | Contract requires path-scope incompatibility; discovery confirms involving-object identity already supports it |
| Parent null | Typed `None` also represents omission internally | Contract requires semantic presence distinction while keeping presence bit internal |
| Parent selector | CLI supports human selector but HTTP does not | Contract distinguishes HTTP UUID/null from CLI UUID-or-human-selector/null |
| Location defect | Could be “fixed” by relaxing validation | Contract explicitly preserves exact Location validation and protocol failure |
| Schema/dependency impact | Read/projector changes might invite schema/index work | Contract explicitly requires no schema/Alembic/dependency/lockfile delta |

Result:

```text
unresolved contract contradiction = 0
```

## 12. Normative hygiene

The draft contains:

```text
Purpose
Capability portfolio
5 Objectives
Scope
Cross-capability dependency map
Non-goals
AS-IS preservation and explicit deltas
8 Required outcomes
18 Acceptance criteria
8 Contract quality gates
Final acceptance gate
Freeze/change-control rules
```

Checks:

```text
TBD occurrences                   0
TODO occurrences                  0
unresolved candidate/open point   0
duplicate OUT identifiers         0
duplicate AC identifiers          0
duplicate CQG identifiers         0
```

## 13. Architecture handoff

After contract freeze, the M3 architecture set must own at least:

```text
read semantic-responsibility boundary realization
one-statement target for all 22 canonical public business GETs
route-specific projection patterns from the discovery closure
historical lifecycle carrier decoder boundary
complete 12-route cursor identity realization
OBJ-GET-03 parent path binding
OBJ-GET-06 object path binding
ObjectTemplate parent null HTTP carrier
nullable selector null CLI semantics and query serialization
CLI Location request-key / response-JSON-path materialization grammar
verification obligations for statement evidence, cursor cross-target rejection and preserved mutation validation
```

None of those architecture decisions may broaden or reinterpret the proposed contract without a contract reopen.

## 14. Final finding

The M3 draft satisfies the pre-freeze consistency conditions at review-evidence level:

```text
Discovery capability coverage          PASS
AS-IS preservation/delta closure       PASS
Cursor census/rule closure             PASS
HTTP/CLI carrier consistency           PASS
Read-boundary consistency              PASS
Outcome/acceptance traceability        PASS
Contract/architecture boundary         PASS
Normative hygiene                      PASS
Open contract-level findings              0
```

Recommendation:

```text
submit docs/milestones/M3/contract.md for explicit human freeze review

on human approval:
    contract.md -> FINAL / FROZEN
    status.md -> architecture design phase
    architecture/README.md -> DESIGN IN PROGRESS — NOT FROZEN
    steps.md remains NOT YET FROZEN / NO IMPLEMENTATION AUTHORITY
    software implementation remains NOT AUTHORIZED
```
