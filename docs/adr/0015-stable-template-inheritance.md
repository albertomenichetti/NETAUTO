# ADR 0015: Stable Template Inheritance Identity

## Status

Accepted

## Context

ObjectTemplate inheritance is single-parent and exact-version pinned, but that
alone does not prevent one ObjectTemplate identity from moving into a different
ancestry identity space after it has entered the published lifecycle.

The platform intentionally relies on stable ancestry identity for:

- component-slot type compatibility
- RelationshipDefinition applicability
- same-template Object migration safety

## Decision

1. ObjectTemplate inheritance remains single-parent and exact-version pinned.
2. Each individual ObjectTemplateVersion keeps an immutable exact parent pin
   once published.
3. Before an ObjectTemplate identity has any PUBLISHED or DEPRECATED version,
   its initial DRAFT may freely change parent.
4. Once the identity has any PUBLISHED or DEPRECATED version, the parent
   template identity is frozen:
   - if the published lineage parent is `P`, every later version must also use
     parent identity `P`
   - if the published lineage is root (`parent=None`), every later version must
     remain root
5. The exact parent version may advance in later child versions.
6. Parent exact version must be monotonically non-decreasing across child
   version numbers.
7. Every persisted non-null parent reference must resolve to an existing exact
   ObjectTemplateVersion.
8. DRAFT parent refs may point to an existing DRAFT, PUBLISHED, or DEPRECATED
   parent version.
9. Publication still requires the exact referenced parent version to be
   PUBLISHED.
10. Self-inheritance and inheritance cycles must not be persistible through
    supported application workflows.
11. Changing to a different parent identity represents a different semantic
    taxonomy and requires a new ObjectTemplate identity instead of a new
    version.
12. This invariant is intentionally relied upon by:
    - component-slot type compatibility
    - RelationshipDefinition applicability
    - same-template Object migration safety

## Consequences

- Every ObjectTemplate identity that has ever been published stays in the same
  ancestry identity space across future versions.
- Exact parent versions may move forward, but never backward.
- Historical DEPRECATED lineage remains authoritative for parent identity and
  monotonic parent-version evolution.
- Repository replacement now also prevents changing the exact parent pin of an
  already PUBLISHED or DEPRECATED ObjectTemplateVersion, because the exact
  published/deprecated schema snapshot is immutable in S4b.
- Supported create, revise, create-next, and publish workflows must validate:
  - exact parent existence
  - self-inheritance and inheritance cycles
  - stable parent identity after first publication
  - monotonic non-decreasing exact parent version
- Persistence now physically enforces:
  - non-null parent -> exact existing ObjectTemplateVersion
  - parent columns -> both NULL or both non-NULL
  - referenced exact parent version -> `RESTRICT` deletion
- Repository immutability enforcement now also guarantees:
  - PUBLISHED -> parent pin cannot be rewritten through replacement
  - DEPRECATED -> parent pin cannot be rewritten through replacement
- Stable parent identity, monotonic parent-version evolution, self-inheritance
  prevention, cycle prevention, and parent publication status remain semantic
  invariants enforced by supported workflows.
