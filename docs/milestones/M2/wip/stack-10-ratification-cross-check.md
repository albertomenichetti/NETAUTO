# M2 STACK-10 Ratification Cross-Check

**Status:** PASS — STACK-10 RATIFIED AND PROPAGATED — FINAL ARCHITECTURE CLOSURE PENDING

**Authority:** REVIEW EVIDENCE — NON-NORMATIVE

## Review target

```text
docs/general/technology_baseline.md
    STACK-10 — official HTTP CLI and terminal interaction
```

The review compares the ratified technology decision with:

```text
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/health.md
docs/milestones/M2/architecture/cli.md
docs/milestones/M2/architecture/runtime-deployment.md
docs/milestones/M2/architecture/verification.md
docs/milestones/M2/wip/cli-stack-10-proposal.md
docs/general/technology_baseline.md STACK-01, STACK-03, STACK-05,
    STACK-07, STACK-08 and STACK-09
```

## Ratified decision

```text
HTTP client
    HTTPX AsyncClient
    httpx>=0.28,<1

terminal / REPL
    prompt_toolkit 3.x
    prompt-toolkit>=3.0,<4

process and parsing
    argparse
    shlex POSIX mode
    json
    pathlib
    asyncio
```

Explicitly not selected:

```text
Typer
Click
cmd2
Rich as semantic/output authority
stdlib readline as the cross-platform REPL foundation
dynamic OpenAPI command generation
CLI plugin framework
alternative HTTP client
```

## Closure summary

```text
native-asyncio alignment                       PASS
public HTTP-only client boundary               PASS
static 63-operation registry compatibility     PASS
Health /connect and /status compatibility      PASS
verified HTTPS / no-insecure policy            PASS
one-wheel and exact-lock packaging alignment   PASS
CLI-only import/runtime independence            PASS
PTY/HTTP/package verification hooks             PASS
STACK-09 serving/admin boundary                PASS
technology authority duplication               NONE
open technology decision                       0
contract reopening                              NOT REQUIRED
```

## Authority result

`docs/general/technology_baseline.md` is now the sole project-wide technology authority for HTTPX and `prompt_toolkit`. `cli.md` owns command/client behavior, `runtime-deployment.md` owns dependency and wheel realization, and `verification.md` owns evidence. The historical proposal remains review evidence only.

## Remaining gate

STACK-10 ratification closes the final project-wide technology decision required by M2. The architecture set now requires only:

```text
final M2-OUT -> M2-AC -> M2-VER -> implementation-path traceability
final contract / AS-IS / authority / terminology / hygiene sweep
resolution of any resulting finding
dedicated architecture freeze transition
```
