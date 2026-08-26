# M3 Contract Final Review

**Status:** PASS — READY FOR EXPLICIT HUMAN FREEZE DECISION

**Authority:** REVIEW EVIDENCE — NON-NORMATIVE

This report records the final human-review preparation sweep for:

```text
docs/milestones/M3/contract.md
contract candidate commit  28c291b16378cd3849eba2d1d9828867b3941e92
contract content SHA        6f1ffd5f8e85c3bb90578db3ec2067f36df53e34
```

The contract remains `DRAFT / REVIEW — NOT FROZEN`. This report does not freeze the contract, authorize architecture implementation or create software implementation authority.

## 1. Final review summary

```text
Governance / authority boundary          PASS
Discovery capability coverage            PASS
AS-IS preservation / delta closure       PASS
CLI 201 / Location contract               PASS
22-route read-boundary closure            PASS
12-route cursor identity/keyset closure   PASS
Lifecycle historical-decoding boundary    PASS
HTTP / CLI parent-filter carrier          PASS
Single-request read coherence             PASS
Outcome / acceptance traceability         PASS
Contract / architecture boundary          PASS
Normative hygiene                         PASS
Open contract-level findings                 0
```

Recommendation:

```text
contract candidate is ready for explicit human FINAL / FROZEN approval
```

## 2. Authorities and inputs revalidated

### Governance

```text
AGENTS.md
README.md
docs/general/linee_guida_progetto.md
docs/milestones/M3/status.md
docs/milestones/M3/steps.md
```

### Delivered AS-IS materially affected

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

### Closed M3 discovery inputs

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

WIP inputs remain non-normative. The candidate contract is self-contained at contract level.

## 3. Final-review findings and closure

The final review found five wording/coverage issues in the first draft. All are closed in candidate commit `28c291b16378cd3849eba2d1d9828867b3941e92`.

### M3-CFR-F01 — Public read failure-preservation wording was too broad — CLOSED

Earlier `M3-OUT-04` stated that GET failure semantics remained compatible except for cursor/root-filter deltas. That contradicted the intentional M3 read-boundary delta: representable persisted state may cease to return a GET-time `500` that existed only because the read re-ran mutation semantic certification.

Closure:

```text
success DTO/filter/order/pagination compatibility remains explicit
request-validation and path-target failure compatibility remains explicit
other failure changes are allowed only where the registered read/cursor/root-filter deltas authorize them
```

No unregistered failure-semantic change is authorized.

### M3-CFR-F02 — Location response-source wording excluded top-level fields — CLOSED

The first draft described response-derived Location identity as coming from nested response fields. The eight-operation census also contains top-level response fields such as `id` and `version`.

Closure:

```text
Location identity may come from an already-resolved request value
or from a response-body JSON path
response path may be one segment or nested
```

The contract still does not prescribe the helper/materialization implementation.

### M3-CFR-F03 — Single-request read coherence lacked a dedicated acceptance criterion — CLOSED

The scope preserved one self-consistent committed projection per request, but the first draft did not assign that guarantee its own acceptance criterion.

Closure:

```text
M3-AC-19 — Single-request committed read coherence
```

The criterion preserves one coherent committed observation per request while retaining the existing non-guarantee of cross-request repeatable membership.

This is especially important because the future M3 architecture may change the realization of that guarantee; the public guarantee itself remains frozen.

### M3-CFR-F04 — Traceability wording risked duplicate ownership of preserved AS-IS — CLOSED

The first draft required every preserved affected AS-IS guarantee to receive normative architecture ownership inside M3. Repository governance instead requires unchanged guarantees to continue deriving from their current `docs/architecture/` owner.

Closure:

```text
explicit M3 delta
    -> frozen M3 architecture owner

preserved affected AS-IS guarantee
    -> remains traceable to current AS-IS owner

both
    -> deterministic verification evidence before delivery
```

`M3-OUT-08` and `M3-AC-18` now preserve that ownership discipline.

### M3-CFR-F05 — CLI side of parent-template null delta needed explicit delta registration — CLOSED

Scope and acceptance already required CLI `parent_template_id=null`, but the explicit AS-IS delta register described primarily the HTTP lexical change.

Closure now records that the official CLI:

```text
accepts parent_template_id=null for this nullable selector-capable query parameter
performs no ObjectTemplate selector lookup for explicit null
emits the canonical lowercase null HTTP query carrier
```

`parent_filter_set` remains internal only.

## 4. Capability and identifier closure

The final candidate contains:

```text
Objectives                  5
Required outcomes           M3-OUT-01 .. M3-OUT-08     = 8
Acceptance criteria         M3-AC-01  .. M3-AC-19      = 19
Contract quality gates      M3-CQG-01 .. M3-CQG-08     = 8
```

Coverage matrix:

| Capability area | Objectives | Outcomes | Acceptance criteria |
|---|---|---|---|
| CLI create correctness | 1 | OUT-01, OUT-02 | AC-01..03 |
| GET/read authority and compatibility | 2, 3 | OUT-03, OUT-04 | AC-04..07, AC-19 |
| Historical lifecycle decoding | 2, 3 | OUT-06 | AC-08 |
| Cursor identity/keyset | 4 | OUT-05 | AC-09..13 |
| ObjectTemplate root filter | 5 | OUT-07 | AC-14..16 |
| Non-delta / traceability | cross-cutting | OUT-08 | AC-17, AC-18 |

Checks:

```text
in-scope capability without objective          0
in-scope capability without outcome            0
required outcome without acceptance path       0
acceptance criterion without attributable area 0
duplicate OUT identifiers                      0
duplicate AC identifiers                       0
duplicate CQG identifiers                      0
```

## 5. AS-IS delta closure

The candidate preserves the delivered API/CLI/schema/runtime surface except for the five explicit M3 deltas:

```text
1. read semantic-certification boundary
    GET no longer fails solely to re-prove mutation-owned persisted semantics
    materially undecodable required carriers remain an internal-failure boundary

2. Object components cursor identity
    add parent_object_id

3. Object-relative Relationship cursor identity
    add object_id

4. ObjectTemplate parent filter
    HTTP parent_template_id=null -> root only
    CLI parent_template_id=null -> no selector lookup, send literal null
    omission remains no parent filter

5. CLI create Location correctness
    valid registered response-derived JSON paths, including nested identities, materialize correctly
    genuine Location protocol violations remain cli_protocol_error
```

The delivered single-request coherent-read guarantee is explicitly preserved as a self-consistent committed public projection and is covered by `M3-AC-19`.

Result:

```text
unregistered observable M3 delta found = 0
```

## 6. Cursor contract final check

The candidate freezes the complete twelve-route public cursor census and the general rule:

```text
query identity
    = route
    + every membership-affecting path target
    + every membership-affecting active query filter
    + required semantic presence bits

position
    = complete canonical ordering tuple

limit
    = excluded from semantic query identity
```

The final repository audit found exactly two current identity defects and zero keyset-key defects:

```text
GET /objects/{parent_object_id}/components
    missing parent_object_id

GET /objects/{object_id}/relationships
    missing object_id

additional cursor identity defect  0
keyset-position defect              0
```

The contract acceptance set covers cross-route, cross-target, cross-filter, lifecycle scope, ObjectTemplate presence-bit identity and changing-limit behavior.

## 7. Read-boundary and coherence final check

The candidate keeps these concepts distinct:

```text
request / cursor validation
    strict public boundary

persisted semantic certification
    mutation-owned
    GET does not re-run it merely as a condition of read success

representational carrier decoding
    GET-owned when required to construct typed output
    materially undecodable required state may fail safely

single-request coherence
    every response is one self-consistent committed projection

cross-request repeatable membership
    not promised
```

This explicitly changes the delivered broad corruption-certification rule while preserving the delivered coherent-projection guarantee.

No repair, silent omission or mutation-validation weakening is authorized.

## 8. Contract / architecture boundary final check

The contract deliberately does **not** freeze:

```text
one-statement SQL as public behavior
specific JOIN / CTE / UNION / recursive-query layouts
coherent_read removal mechanics
read projector helper or store method names
Location materializer helper structure
FastAPI/Pydantic helper naming
CLI parser/planner helper decomposition
statement-count instrumentation mechanism
implementation slicing
```

These remain architecture/verification/implementation decisions constrained by the contract.

The closed discovery conclusion that all 22 target reads can be realized in one business SQL statement remains a mandatory input to architecture design, not a public wire promise.

## 9. Normative hygiene

The candidate contains no known:

```text
TBD
TODO
unresolved candidate semantic
open contract design point
unclassified capability
competing owner requirement
silent AS-IS override
```

Canonical counts are now:

```text
public business GET/read routes     22
cursor-bearing public routes        12
registered 201 + Location commands   8
known cursor identity corrections    2
new public business routes           0
schema/migration/dependency delta     0
```

## 10. Final conclusion

The M3 contract candidate satisfies the final review gate:

```text
contract final review                 PASS
open contract findings                   0
candidate ready for human freeze      YES
architecture implementation authorized NO
software implementation authorized     NO
```

Next human-owned decision:

```text
APPROVE FREEZE
    -> contract.md becomes FINAL / FROZEN
    -> status.md advances to architecture design
    -> architecture set may be created as DESIGN IN PROGRESS / NOT FROZEN
    -> steps.md remains NOT FROZEN
    -> software implementation remains NOT AUTHORIZED

or

REQUEST CONTRACT CHANGES
    -> contract remains DRAFT / REVIEW
    -> findings are recorded and resolved before another freeze review
```
