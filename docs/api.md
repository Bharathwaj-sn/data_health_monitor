# API Reference

## Conventions

- The application API prefix is `/api/v1`.
- Lookup operations that need selection criteria use `POST` with a JSON body;
  `GET` operations do not accept request bodies.
- FastAPI's interactive schema and complete generated models are available at
  `/docs` while the backend is running.
- Requests receive an `X-Request-ID` response header. Include that value when
  correlating a client failure with structured application logs.
- Malformed request models return `422`. Domain errors are mapped by each route
  and described below. Unexpected errors return `500` with a generic detail.

## Health

| Method and path | Purpose | Response |
| --- | --- | --- |
| `GET /health` | Liveness probe; does not test Databricks connectivity. | `{"status":"healthy"}` |

## Databricks discovery

| Method and path | JSON body | Success response | Main failures |
| --- | --- | --- | --- |
| `GET /api/v1/databricks/whoami` | None | Authenticated Databricks identity. | `401` if the SDK cannot obtain an active user. |
| `GET /api/v1/databricks/catalogs` | None | `{"catalogs":[{"name":"..."}]}` | `503` when catalogs cannot be loaded. |
| `POST /api/v1/databricks/schemas:lookup` | `{"catalog_name":"..."}` | `{"schemas":[{"name":"..."}]}` | `404` for an inaccessible catalog. |
| `POST /api/v1/databricks/schema-objects:lookup` | `{"catalog_name":"...","schema_name":"..."}` | `{"tables":[...],"volumes":[...]}` | `404` for an inaccessible schema. |
| `POST /api/v1/databricks/tables:lookup` | `{"catalog_name":"...","schema_name":"...","table_name":"..."}` | Full table metadata, including columns. | `404` for an inaccessible table. |

The discovery routes read live Unity Catalog data. They do not populate the
local metadata snapshot; use metadata refresh for that.

## Metadata snapshot

| Method and path | JSON body | Success response | Main failures |
| --- | --- | --- | --- |
| `POST /api/v1/metadata/refresh` | `MetadataRefreshRequest` | Complete `MetadataSnapshot` with refresh details. | `500` when refresh cannot finish. |
| `GET /api/v1/metadata` | None | Persisted `MetadataSnapshot`. | `404` before the first refresh. |
| `GET /api/v1/metadata/summary` | None | Counts, refresh time, and last refresh scope. | `404` before the first refresh. |

`MetadataRefreshRequest` has the following valid shapes:

```json
{"scope_type":"catalog","catalog_name":"main"}
{"scope_type":"schema","catalog_name":"main","schema_name":"qa"}
{"scope_type":"table","catalog_name":"main","schema_name":"qa","table_name":"claims"}
```

A catalog refresh rebuilds that one catalog. A schema refresh replaces that
schema in the snapshot. A table refresh adds or replaces only that table.
`scope_type` determines which names must be present or omitted.

## Test cases

| Method and path | JSON body | Success response | Main failures |
| --- | --- | --- | --- |
| `POST /api/v1/test-cases` | `TestCaseCreate` | Created `TestCase`. | `409` for a duplicate; `500` otherwise. |
| `GET /api/v1/test-cases` | None | Array of `TestCase`. | `500` when the backing table cannot be read. |
| `GET /api/v1/test-cases/{test_case_id}` | None | One `TestCase`. | `404` when it is absent. |

`TestCaseCreate` requires these strings: `pipeline`, `component`,
`test_scenario`, `target_object`, `input_data`, `validation_check`, and
`expected_result`. The service assigns identifiers such as `TC000001`, marks
the record `ACTIVE`, and includes creation and update timestamps.

## Payor configuration

| Method and path | JSON body | Success response | Main failures |
| --- | --- | --- | --- |
| `GET /api/v1/payor-config/payors` | None | `{"payors":["..."]}` | `500` when retrieval fails. |
| `POST /api/v1/payor-config/file-types:lookup` | `{"payor":"..."}` | `{"file_types":["..."]}` | `500` when retrieval fails. |
| `POST /api/v1/payor-config:lookup` | `{"payor":"...","file_type":"..."}` | One `PayorConfig`. | `404` missing, `409` duplicate. |
| `POST /api/v1/payor-config:search` | `{"payor":"..."}` | Array of `PayorConfig`. | `500` when retrieval fails. |

`PayorConfig` mirrors the ingestion configuration table. The most important
fields for QA context are `payor`, `file_type`, `sql_pool_table`, table names,
key and standardization-column lists, filters, file details, and threshold
settings. It also preserves the wire aliases `12_month_rolling` and
`12_month_rolling_key`.

## QA context and Genie

The three context-generation routes accept the same body:

```json
{
  "test_case_id":"TC000001",
  "catalog":"main",
  "schema":"qa",
  "selections":[
    {"table_name":"claims","payor":"ExamplePayor","file_type":"Claims"}
  ]
}
```

Each selection must be unique by the tuple `table_name`, `payor`, and
`file_type`. On the server, the `schema` JSON property is represented as
`schema_name` in Python.

| Method and path | Purpose | Success response | Main failures |
| --- | --- | --- | --- |
| `POST /api/v1/qa/context` | Resolve test case, payor configuration, and refreshed table metadata. | `QAContext` | `404` absent test case/config; `409` no snapshot/table or duplicate config; `422` table mismatch/missing expected table. |
| `POST /api/v1/qa/genie-context` | Transform QA context into Genie serialized-space version 2. | `GenieSerializedSpace` | Same context failures; `409` when Genie context cannot be formed. |
| `POST /api/v1/qa/genie-space` | Update/create the managed Genie space and ask it to generate SQL. | `GenieSQLGeneration` | Context failures; `409` invalid Genie configuration; `502` Genie failure. |
| `POST /api/v1/qa/genie/conversations/{conversation_id}/messages` | Continue the managed Genie conversation. | `GenieSQLGeneration` | `409` no managed space; `502` Genie failure. |
| `GET /api/v1/genie-space/status` | Return the currently managed space's ID, configured title, and status. | `{"space_id":"...","title":"...","status":"ready"}` | Startup must have completed. |

`GenieSQLGeneration` returns `space_id`, `conversation_id`, `message_id`, and
`sql`. Genie serialized spaces must use `version: 2` and cannot contain
duplicate data-source identifiers or duplicate column names in one table.

## Validation SQL and execution

| Method and path | JSON body | Success response | Main failures |
| --- | --- | --- | --- |
| `POST /api/v1/qa/validation-sql` | `ValidationSQLCreate` | Saved `ValidationSQL`. | `502` persistence/SQL error; `503` other failure. |
| `POST /api/v1/qa/validation-sql:search` | `{}` or `{"test_case_id":"TC000001"}` | Array of saved `ValidationSQL`. | `502` retrieval error. |
| `POST /api/v1/qa/validation-sql/{validation_sql_id}:execute` | `{}` | `TestCaseResult`. | `404` if unknown; `502` execution error. |
| `POST /api/v1/qa/validation-sql/batch-execute` | `{"validation_sql_ids":["id-1","id-2"]}` | `BatchExecutionResult`. | `404` if any requested ID is absent; `502` retrieval error. |

`ValidationSQLCreate` requires the test-case ID, fully qualified target table,
payor, file type, generated SQL, and Genie space/conversation/message IDs. A
saved record gains a UUID-like `validation_sql_id`, `created_at`, and `SAVED`
status.

`TestCaseResult` contains execution status, statement ID, returned column names
and rows, row count, and execution timestamp. Batch IDs must be nonempty and
unique. Its aggregate status is `SUCCEEDED`, `COMPLETED_WITH_FAILURES`, or
`FAILED`; each item is `SUCCEEDED`, `FAILED`, or `SKIPPED` with an execution
order and optional error.