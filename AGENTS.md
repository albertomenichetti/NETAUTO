# NETAUTO

NETAUTO is a REST-API-first dynamic infrastructure modeling framework.

## Goals

The framework will eventually provide:

- asset management
- CMDB
- network source of truth
- automatic discovery and onboarding
- network service definitions

The backend must not contain domain-specific concepts such as
Device, Router, Interface, Site, VLAN, etc.

Those concepts must be dynamically defined through the API.

## Core concepts

- DataType
- ObjectTemplate
- Object
- RelationshipType
- Relationship
- Observation

## Architecture

CLI -> REST API -> Application Layer -> Domain Core -> Persistence

The CLI MUST use the REST API.
The CLI MUST NOT import application/domain services directly.

## Technology

- Python >= 3.13
- uv
- FastAPI
- Pydantic v2
- JSON Schema Draft 2020-12
- python-jsonschema
- SQLAlchemy 2
- SQLite initially
- PostgreSQL later
- Typer
- HTTPX
- pytest
- Ruff
- Pyright

## Domain rules

The domain core MUST NOT depend on:

- FastAPI
- Typer
- SQLAlchemy

Pydantic is used for static API models.

Dynamic user-defined types are represented as DataTypes and compiled
to JSON Schema. Do not dynamically generate Pydantic models for them.

Validation is strict. No implicit value coercion.

## ObjectTemplate inheritance

- single inheritance
- parent versions are pinned
- published versions are immutable
- no inheritance cycles
- inherited properties cannot be removed
- inherited property datatype cannot change
- abstract templates cannot be instantiated
- an instance of a child template is also semantically an instance
  of all ancestor templates

## Versioning

Both DataType and ObjectTemplate are versioned.

Lifecycle:

draft -> published -> deprecated

Published versions are immutable.

References from published schemas always point to exact versions.