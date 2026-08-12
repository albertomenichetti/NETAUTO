# NETAUTO

NETAUTO is a REST-API-first dynamic infrastructure modeling framework.

Development is currently focused on the schema and object engine that will
support dynamic infrastructure modeling through the API.

## Development Database

PostgreSQL is the default runtime backend.

- `DATABASE_URL` overrides the runtime database URL
- when `DATABASE_URL` is absent, the runtime default is
  `postgresql+psycopg://localhost/netauto`
- PostgreSQL runtime/schema setup is Alembic-managed; migrate the configured
  database before starting the application
- authoritative integration and full-suite validation require
  `TEST_DATABASE_URL`
- PostgreSQL integration tests run in ordinary `uv run pytest`; the old
  `--run-postgresql` opt-in is gone
- SQLite remains explicit transitional compatibility only until M2.5.12 and
  can still be selected via `DATABASE_URL=sqlite:///...`

Example URLs:

```bash
DATABASE_URL=postgresql+psycopg://localhost/netauto
TEST_DATABASE_URL=postgresql+psycopg://localhost/netauto_test
```

## CLI

The CLI is an HTTP client for the REST API.

Examples:

```bash
NETAUTO_API_URL=http://127.0.0.1:8000 uv run netauto datatype list
uv run netauto --api-url http://127.0.0.1:8000 --output json datatype list
uv run netauto datatype create \
  --namespace network \
  --name vlan_id \
  --description "VLAN identifier" \
  --base-type core.integer \
  --constraint minimum=1 \
  --constraint maximum=4094
uv run netauto datatype version publish <DATATYPE_ID> 1
uv run netauto datatype create --file models/datatypes/vlan_id.json
```
