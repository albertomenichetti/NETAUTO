# M2 Official CLI Architecture Cross-Check

**Status:** PASS — CLI DESIGN COMPLETE — RUNTIME OWNER REVIEW / TECHNOLOGY CONSOLIDATION / IMPLEMENTATION EVIDENCE PENDING

**Authority:** REVIEW EVIDENCE — NON-NORMATIVE

## Review target

```text
docs/milestones/M2/architecture/cli.md
```

The review compares the CLI design with:

```text
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/health.md
docs/milestones/M2/architecture/verification.md

docs/milestones/M2/wip/netauto-cli.md

docs/architecture/api.md
docs/architecture/verification.md
docs/general/technology_baseline.md

current public route inventory, transport DTO placement,
package/dependency configuration and HTTP composition on branch M2
```

## Closure summary

```text
interactive mode and initial state              PASS
non-interactive exact invocation                PASS
local command inventory                         PASS — 8/8
business HTTP operation coverage                PASS — 63/63
unique CLI command keys                         PASS — 63/63
Health consumption boundary                     PASS
static command/help/dispatch authority          PASS
endpoint-root and TLS policy                    PASS
HTTP lifecycle, timeout and retry policy        PASS
human selector policy                           PASS
nested selector resolution                      PASS
omission versus explicit null                   PASS
structured inline/file JSON input               PASS
FORMATTED output and enrichment boundary        PASS
JSON trace schema                               PASS
remote/local/selector/transport/protocol errors PASS
connection-state transitions                    PASS
same-release compatibility                      PASS
application/persistence isolation               PASS
M2-VER-25 ... M2-VER-28 hooks                  PASS
negative CLI surface                            PASS
open CLI-specific architecture point            0
contract reopening                              NOT REQUIRED
runtime owner review                            PENDING
technology baseline consolidation               PENDING — STACK-10 proposal captured
implementation evidence                         PENDING by governance
```

## Material findings

### 1. One static registry must own the complete client surface

A hand-written parser, separate help text and separate HTTP dispatcher would create three authorities that can drift.

The accepted design uses one immutable `CommandSpec` registry for:

```text
parser
help
selector traversal
HTTP method/path/body/query construction
expected success status
response validation
FORMATTED renderer selection
coverage verification
```

The registry contains exactly 63 unique `(resource, operation)` keys and exactly the 63 business `(method, path-template)` operations owned by `api.md`.

No alias or hidden dispatcher path counts as API coverage.

### 2. Health remains a local session dependency, not a 64th remote business command

The exact boundary is:

```text
/connect
/status while CONNECTED
    -> GET /health/core

remote business registry
    -> exactly 63 /api/v1/core operations

netauto -n business command
    -> no mandatory Health preflight
```

This preserves the frozen capability dependency map and avoids treating an operational readiness probe as a business resource.

### 3. Shared wire validation requires a neutral transport package

The server and same-release CLI must validate the same request/response DTOs, but the CLI must not import FastAPI route functions or application services.

The accepted boundary is:

```text
src/netauto/transport/http/
    -> transport-only Pydantic DTOs
    -> canonical business error model
    -> Health model

server adapters
    -> import neutral DTOs
    -> own Request/Response/routing and application mapping

CLI
    -> import neutral DTOs
    -> own HTTP client validation
```

The neutral package contains no FastAPI request object, application service, SQLAlchemy, Psycopg or persistence import. Sharing a DTO does not share semantic execution authority.

### 4. Human selectors must extend into nested request values

Top-level readable selectors alone would leave the majority of create/revise commands dependent on raw UUIDs.

The accepted registry declares selector-bearing fields recursively, including:

```text
DataType selectors in property declarations
ObjectTemplate selectors in parent, component, endpoint and perspective values
Object selectors in ownership and Relationship endpoint values
```

Every human selector is resolved through an existing public GET/list route and rewritten to the exact UUID carrier expected by the API.

RelationshipDefinition, factual Relationship and Resolution identities remain UUID-only because the domain exposes no unambiguous human identity for them.

### 5. Selector resolution must not cache across commands

Object canonical names are mutable and non-unique. Cross-command caching could silently address a stale identity.

The accepted algorithm uses:

```text
per-command first-occurrence ordering
sequential public GET resolution
per-command duplicate lookup memoization
no cross-command selector cache
```

Zero, one and more-than-one matches are distinct outcomes; ambiguity is never guessed.

### 6. FORMATTED enrichment must be bounded

The discovery requirement for complete human-oriented reads could otherwise introduce unbounded list N+1 behavior.

The accepted policy is:

```text
single-resource reads
    -> explicitly registered bounded enrichment
    -> complete-or-fail

list/page reads
    -> primary page only
    -> no per-item enrichment

mutations
    -> direct operation result only
    -> no hidden post-mutation GET

JSON mode
    -> no FORMATTED-only enrichment
```

This keeps human output useful while preserving predictable HTTP work and transparent command intent.

### 7. JSON output is a CLI execution trace, not a second server envelope

The accepted top-level result records:

```text
original parsed command intent
all attempted HTTP exchanges in order
primary operation result
one structured error
```

Selector lookups and any mode-specific enrichment are visible exactly when they occur. A local parse failure has an empty exchange list; a transport-failed request remains an attempted exchange with no response.

The trace does not reinterpret server payloads or introduce a business result model independent of the public API.

### 8. Explicit trace output and operational logging remain separate

The discovery requires the explicit JSON debug/trace mode to show the exchanges actually observed by the client.

The accepted security boundary therefore combines:

```text
no field-level masking of explicit operator-selected trace payloads
+
no CLI-native credentials or auth headers
+
URL userinfo forbidden
+
no cookie persistence
+
no history persistence
```

Business payloads may be sensitive and the operator owns stdout redirection permissions. This does not weaken the project logging rule: CLI operational logs do not emit unrestricted trace payloads.

### 9. Session history is deliberately memory-only

Persistent history was a discovery NICE TO HAVE, not an acceptance requirement. Persisting command lines would also create an unmanaged local store for structured payload values.

The accepted M2 contract is:

```text
current-process in-memory history
Ctrl-R over that history
/history chronological view
no history file
```

This is simpler, safer and fully satisfies `M2-AC-25`.

### 10. HTTP transport must be transparent and non-retrying

The accepted transport uses one scoped asynchronous client with:

```text
verified HTTPS
no insecure mode
redirects not followed
no cookie persistence
finite transport timeouts
one attempt per planned request
```

Automatic retry of a mutation or selector request could add hidden exchanges and duplicate operator intent. Server-side semantic retry remains server authority.

### 11. Connection state follows communication, not business success

For ordinary remote commands:

```text
valid HTTP response, including business error
    -> communication succeeded
    -> CONNECTED preserved

protocol-invalid HTTP response
    -> endpoint was reached
    -> CONNECTED preserved

transport failure
    -> communication unavailable
    -> DISCONNECTED
```

`/connect` and `/status` intentionally apply the stricter Health-ready rule and disconnect on any non-ready or invalid Health outcome.

### 12. Technology selection is justified but still needs project-wide consolidation

The architecture selects:

```text
HTTPX AsyncClient
prompt_toolkit PromptSession.prompt_async()
stdlib argparse/shlex/json/pathlib
```

This is aligned with the ratified native-asyncio and testing baseline and avoids a second command framework.

Because technology choices are project-wide authority, the exact decision is captured separately in:

```text
docs/milestones/M2/wip/cli-stack-10-proposal.md
```

It must be explicitly consolidated as `STACK-10` in `docs/general/technology_baseline.md` before the architecture set freezes. Dependency metadata and `uv.lock` change only during authorized implementation.

## Exact operation coverage audit

```text
datatype                 14
object-template          16
object                   13
relationship-definition  14
relationship              5
lifecycle-event           1
                         ---
total                    63
```

The operation names map one-to-one to:

```text
41 mutation HTTP routes
22 read HTTP routes
```

The review found:

```text
missing business operation    0
extra business operation      0
duplicate command key         0
dynamic/hidden operation      0
business-style Health command 0
```

## Cross-owner result

### Contract

```text
M2-OUT-12 covered
M2-AC-25 ... M2-AC-28 concretely realizable
M2-OUT-13 and M2-OUT-15 handoff preserved
no Scope, Non-goal or delta change
```

### API

```text
exact route inventory              aligned
request field names                aligned
omission/null semantics            aligned
success status/response validators aligned
business error preservation        aligned
no new lookup route                aligned
```

### Health

```text
/connect exact GET /health/core     aligned
/status exact GET /health/core      aligned
ready 200 + exact DTO required      aligned
no non-interactive preflight        aligned
```

### Verification

```text
M2-VER-25 state/terminal hooks      complete
M2-VER-26 Health/state hooks        complete
M2-VER-27 process/stream hooks      complete
M2-VER-28 exact coverage/boundary   complete
```

### Runtime handoff

`runtime-deployment.md` must confirm:

```text
one console entrypoint in the wheel
runtime inclusion of HTTPX and prompt_toolkit
same version metadata
CLI-only installation without database_url
installed invocation outside Git checkout
```

It may refine package-resource mechanics but may not change command, transport, selector, output or state semantics.

## Final result

```text
CLI architecture design        COMPLETE
contract compatibility         PASS
API compatibility              PASS
Health compatibility           PASS
verification-design coverage   PASS
AS-IS compatibility            PASS — additive client only
CLI-specific open point        0
runtime owner review           PENDING
STACK-10 consolidation         PENDING before architecture freeze
implementation evidence        PENDING
contract reopening             NOT REQUIRED
```
