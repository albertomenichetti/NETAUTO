# Architecture

## Project goals

NETAUTO is a REST-API-first dynamic infrastructure modeling framework.

Its planned outcomes are:

- asset management
- CMDB
- network source of truth
- automatic discovery and onboarding
- network service definitions

The backend must not encode domain-specific concepts such as device or VLAN
types. Those concepts are defined dynamically through the API.

## Layered architecture

The repository follows this direction:

CLI -> REST API -> Application Layer -> Domain Core -> Persistence

## Dependency direction

Dependencies must point inward toward the domain core.

- The CLI must use the REST API.
- The CLI must not import application or domain services directly.
- The domain core must not depend on FastAPI, Typer, or SQLAlchemy.

## Static models vs dynamic schemas

Pydantic is used for static API models.

Dynamic user-defined types are represented as DataTypes and compiled to
JSON Schema. They are not expressed as dynamically generated Pydantic models.

Built-in primitive types are part of the domain core itself. They are not
user-created DataTypes and do not carry versioning, lifecycle, or persistence
metadata.

Validation is strict and must not rely on implicit value coercion.

## CLI and API rule

The CLI is a client of the REST API. It is not an alternate execution path
into application or domain services.
