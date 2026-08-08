# NETAUTO

NETAUTO is a REST-API-first dynamic infrastructure modeling framework.

Development is currently focused on the schema and object engine that will
support dynamic infrastructure modeling through the API.

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
