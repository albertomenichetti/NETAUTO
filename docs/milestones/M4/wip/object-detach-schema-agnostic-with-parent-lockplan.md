# M4 WIP — Object DETACH schema-agnostic admission with centralized parent LockPlan

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes one route-local M4 design point for Object DETACH after explicit re-validation against the delivered AS-IS architecture.

It supersedes only the earlier route-local DETACH parent-lock direction that proposed `FOR SHARE` inside the delete statement. It does not yet freeze the final DETACH Unit of Work, statement count, physical SQL shape, error precedence or cost.

The authoritative AS-IS baseline remains under `docs/architecture/`; this file is a non-normative discovery input for the future M4 architecture set.

## AS-IS authority re-validation

The delivered concurrency architecture already registers `OBJ.DET` in the centralized LockPlan with:

```text
Gate: none
Row plan: parent Object OBJ@NKU
Candidate-dependent target: parent and requested exact edge
Fresh boundary: current exact ownership fact
```

The semantic matrix also requires DETACH to preserve, among other interactions:

```text
PO  DETACH × parent SCHEMA_CHANGE
OF  ATTACH/DETACH and DETACH/DETACH on the same ownership fact
RL  DETACH × Object DELETE / reference-lifetime removal
```

Supported-path deadlocks are architecture/implementation defects; they are not a normal retry outcome.

## M4 ownership-edge materialization dependency

The current preferred M4 physical ownership fact is:

```text
object_components
    child_object_id
    parent_object_id
    slot_declaring_template_id
    slot_name
```

where:

```text
SlotSemanticKey = (slot_declaring_template_id, slot_name)
```

is materialized at ATTACH admission time.

This differs from the delivered AS-IS physical edge, which persists only `slot_name` and therefore forces later schema reinterpretation to recover the declaring lineage.

## Frozen semantic split

M4 DETACH is schema-agnostic for admission, but not concurrency-agnostic.

```text
schema interpretation
    -> not required to remove an already-admitted current ownership fact

concurrency stabilization
    -> still required through the centralized LockPlan
```

DETACH therefore keeps the existing centralized parent concurrency owner:

```text
parent Object OBJ@NKU
```

The lock is planned and acquired through the centralized LockPlan, not through route-local ad-hoc locking SQL.

## Removed DETACH work

Once the persisted edge carries the full SlotSemanticKey, DETACH does not need to perform:

```text
ObjectTemplate effective-schema reconstruction
component_schema lookup
ObjectTemplate ancestry loading
slot declaration re-resolution from slot_name
target_template_id lookup
child template-lineage compatibility validation
cycle validation
OWNERSHIP_GRAPH_WRITE_GATE acquisition
schema/cache preparation solely for DETACH admission
```

Those are admission/interpretation responsibilities of ATTACH and schema-migration logic, not safety requirements for removing an authoritative current edge.

## PO preservation — DETACH × parent SCHEMA_CHANGE

The PO guarantee remains protected by the shared parent concurrency owner, not by DETACH schema recertification.

### DETACH wins first

```text
DETACH
    LockPlan parent OBJ@NKU
    fresh ownership state
    remove edge E
    commit

SCHEMA_CHANGE
    later acquires parent OBJ@NKU
    fresh protected aggregate state excludes E
```

If SCHEMA_CHANGE prepared while E still existed, the M4 aggregate fingerprint protocol detects the changed ownership generation before commit.

### SCHEMA_CHANGE wins first

```text
SCHEMA_CHANGE
    parent OBJ@NKU
    validates/preserves current outgoing edges
    commits new exact schema

DETACH
    later acquires parent OBJ@NKU
    removes the still-current persisted edge
```

DETACH does not need to establish that the edge remains admissible under the newly committed schema because the operation removes that edge. Removing it cannot leave a newly invalid outgoing ownership fact behind.

Therefore PO does not depend on DETACH re-resolving the current effective slot.

## OF preservation — ownership fact sequencing

For operations involving the same parent, `parent OBJ@NKU` serializes the route before current-edge mutation.

The current ownership fact remains protected by the physical single-owner authority:

```text
PRIMARY KEY (child_object_id)
```

and DETACH must operate only on the exact requested current edge. Under the M4 richer edge this exact current fact is identified by at least:

```text
child_object_id
parent_object_id
slot_declaring_template_id
slot_name
```

A DETACH must never remove a different current edge or implicitly move a child.

The separate M4 batch/non-convergent public semantics remain a deliberate semantic delta from the delivered AS-IS and require future propagation into the semantic matrix and verification registry; they do not require current-schema recertification.

## RL preservation — reference lifetime

Parent lifetime is serialized through the planned parent Object lock.

Child lifetime does not require a DETACH-only child lock. The current ownership foreign key remains the physical lifetime authority while the edge exists; after a committed DETACH the removed reference may legitimately unblock child deletion.

No child lock is introduced solely to obtain fresher lifecycle display metadata. Historical names remain governed by the separate lifecycle metadata snapshot contract.

## Superseded route-local parent lock direction

This note supersedes the earlier WIP direction:

```text
DETACH parent FOR SHARE inside Q1
```

That direction correctly identified the need to rendezvous with SCHEMA_CHANGE but solved it outside the established architectural mechanism.

The corrected direction is:

```text
centralized LockPlan
    -> parent OBJ@NKU
```

This preserves the AS-IS concurrency-owner model, canonical planning discipline and supported-path deadlock guarantees.

## Explicitly not frozen here

This note does not freeze:

```text
final statement-by-statement DETACH UoW
whether preparation reads exist before BEGIN
exact current-edge reread SQL shape
exact bulk DELETE SQL shape
lifecycle INSERT shape
statement count / round-trip cost
failure precedence
physical index changes
final FK choice for slot_declaring_template_id
```

Those points must be re-derived from the centralized LockPlan architecture rather than from the previously drafted two-statement route-local UoW.

## Frozen takeaway

```text
M4 DETACH
    -> persisted SlotSemanticKey makes schema recertification unnecessary
    -> current object_components fact is the DETACH semantic source
    -> no schema/cache/ancestry/compatibility/cycle admission
    -> centralized LockPlan remains mandatory
    -> parent Object OBJ@NKU remains the concurrency owner
    -> no route-local FOR SHARE replacement
```

The next design step is to rebuild the DETACH Unit of Work from this corrected baseline and count the actual PostgreSQL work including centralized lock-plan acquisition.
