# Legacy Streamlit Client

## Role

`frontend/streamlit_app.py` is the retained proof-of-concept operator client.
Unlike the current Angular dashboard, it implements the full health-check
workflow over the FastAPI API. It uses `requests` directly with a fixed local
API base URL of `http://127.0.0.1:8000`.

Run it after FastAPI is available:

```powershell
.\.venv\Scripts\python.exe -m streamlit run frontend\streamlit_app.py
```

## Implemented tabs

| Tab | Behavior |
| --- | --- |
| Metadata | Select catalog/schema/table scope, refresh the metadata snapshot, and display its summary. |
| Health Check Definitions | Create test cases, list saved definitions, and select one for generation. |
| Create Health Check | Select catalog, schema, table, payor, and file type; preview QA and Genie context; generate/refine/save SQL. |
| Run Health Checks | Execute one saved SQL item or choose an ordered batch and display result rows and batch outcomes. |

The client keeps selections, generated SQL, the Genie conversation, saved state,
and batch order in Streamlit session state. Reloading the Streamlit session
clears this client-side context; persisted test cases and SQL remain in
Databricks tables.

## Timeout behavior

The Streamlit client allows 20 minutes and 30 seconds for initial Genie SQL
generation and conversation refinement, and 30 minutes and 30 seconds for
batch execution. These HTTP timeouts are independent of the backend's SQL and
batch execution timeouts.

## Verified route mismatch

The batch helper currently posts to `/api/qa/validation-sql/batch-execute`, but
the FastAPI route is `/api/v1/qa/validation-sql/batch-execute`. As written, the
Streamlit batch action will target a nonexistent path and should be corrected
before relying on it. The single-query, save, list, metadata, test-case,
payor, and Genie helper paths use the `/api/v1` prefix.

This client is retained for workflow coverage and reference. New browser-facing
work should target the Angular SPA unless the product direction explicitly
keeps Streamlit as a supported operational interface.