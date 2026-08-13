# ADR 0001: Python and FastAPI

## Status

Accepted

## Context

NETAUTO is defined as a REST-API-first framework with a CLI that must use the
REST API rather than bypassing it.

## Decision

Use Python >= 3.13, FastAPI for the REST API, and Typer plus HTTPX for a CLI
that interacts with the API.

## Consequences

The API is the primary integration boundary, and the CLI remains separated
from application and domain services.
