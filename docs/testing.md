# Testing Guide

## Commands

Run the backend suite from the repository root after installing
`requirements.txt` into the active virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Run the Angular unit tests and production build from `frontend/`:

```powershell
npm test -- --watch=false
npm run build
```

The frontend build is an important contract check because it type-checks and
bundles the standalone application.

## Backend test map

| Area | Test modules |
| --- | --- |
| API routing, contracts, schema validation | `test_api.py`, `test_v1_api_contract.py`, `test_v1_schemas.py`, `test_qa_context_routes.py` |
| Metadata persistence and refresh behavior | `test_metadata_repository.py` |
| Databricks and SQL execution behavior | `test_databricks_sql_service.py` |
| Test cases and payor configuration | `test_test_case_service.py`, `test_payor_config_service.py` |
| QA context | `test_qa_context_service.py` |
| Genie models, context, service, coordinator | `test_genie_models.py`, `test_genie_context_service.py`, `test_genie_service.py`, `test_genie_space_coordinator.py` |
| Saved SQL and batch execution | `test_validation_sql_service.py`, `test_batch_execution_models.py`, `test_batch_execution_service.py` |
| Cross-cutting HTTP behavior | `test_observability.py`, `test_exception_handlers.py` |
| Client compatibility | `test_frontend_contract_fixtures.py`, `test_streamlit_api_client.py` |

The tests use fakes, dependency overrides, and fixtures rather than requiring a
live Databricks workspace. They are the preferred safety net for service and
contract changes.

## Fixtures

`frontend/tests/fixtures/` contains API-contract, Databricks, error, Genie,
metadata, payor-config, QA-context, test-case, validation-SQL, and batch
execution examples. The Python fixture-contract test checks that those values
remain compatible with API response models used by the client layer.

## Testing by change type

| Change | First focused check |
| --- | --- |
| Route, response shape, or dependency wiring | Relevant `test_api.py`, `test_v1_api_contract.py`, or route-specific test |
| Pydantic model or validation rule | `test_v1_schemas.py` and the model/service-specific test |
| Metadata repository behavior | `test_metadata_repository.py` |
| Genie context or coordinator behavior | `test_genie_context_service.py` or `test_genie_space_coordinator.py` |
| SQL timeout, persistence, or batch behavior | Corresponding Databricks SQL, validation SQL, or batch test |
| Angular component/API changes | `npm test -- --watch=false` and `npm run build` |

Run the complete pytest suite before integrating changes that cross more than
one layer, particularly changes to model serialization, dependency providers,
or workflow orchestration.