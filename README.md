
# Flock Energy Meter API

A read-only REST API wrapper for the Urja Meter Ops portal. The service exposes meter information, distribution transformers, and energy-consumption readings through FastAPI.

## Features

- List and search meters with pagination.
- Retrieve details for a specific meter.
- List distribution transformers.
- Retrieve energy-consumption readings for a meter.
- Validate request parameters and return clear upstream errors.
- Generate an OpenAPI specification and interactive Swagger documentation.
- Run mocked API tests without depending on the live portal.
- Run optional integration tests against the real portal.

## Technology Stack

- Python 3.11+
- FastAPI
- HTTPX
- Pydantic Settings
- Pytest

## Project Structure

```text
flock-energy-api/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── client.py
│   ├── models.py
│   └── main.py
├── tests/
│   ├── test_api.py
│   ├── test_health.py
│   └── test_live_portal.py
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── PROTOCOL.md
├── REFLECTION.md
└── openapi.json
```

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/Scripts/activate
```

If the virtual environment already exists, activate it with the second command.

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Configure environment variables

Create a local `.env` file using `.env.example` as a reference:

```dotenv
PORTAL_BASE_URL=https://urja-ops.flockenergy.tech
PORTAL_EMAIL=
PORTAL_PASSWORD=
PORTAL_SESSION_COOKIE=
REQUEST_TIMEOUT=30
API_PORT=8000
```

The current implementation uses `PORTAL_SESSION_COOKIE` for upstream authentication. Obtain a valid session through an authorized login and store the cookie value locally. Do not commit `.env` or share session credentials.

Although email and password settings are available, automatic login and session renewal have not yet been verified successfully. Session cookies may expire.

### 4. Start the API

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Available local URLs:

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json
- Health check: http://127.0.0.1:8000/health

## API Endpoints

### Health check

`GET /health`

Checks whether the wrapper service is running.

Example response:

```json
{
  "status": "ok",
  "service": "flock-energy-api"
}
```

### List and search meters

`GET /api/v1/meters?page=1&q=J100040`

Returns a page of meters, optionally filtered by a search query.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | Integer | `1` | Page number; must be at least 1 |
| `q` | String | Empty | Optional search query; maximum 100 characters |

Example:

```bash
curl "http://127.0.0.1:8000/api/v1/meters?page=1&q=J100040"
```

### Retrieve a meter

`GET /api/v1/meters/{meter_id}`

Returns the matching meter record. Returns `404` if the meter is not found.

Example:

```bash
curl "http://127.0.0.1:8000/api/v1/meters/J100000"
```

### List distribution transformers

`GET /api/v1/transformers?page=1`

Returns a page of distribution transformers.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | Integer | `1` | Page number; must be at least 1 |

Example:

```bash
curl "http://127.0.0.1:8000/api/v1/transformers?page=1"
```

### Retrieve energy consumption

`GET /api/v1/meters/{meter_id}/consumption`

Returns energy readings for the specified meter.

Example:

```bash
curl "http://127.0.0.1:8000/api/v1/meters/J100000/consumption"
```

The upstream response can include `timestamp`, `kwh`, `kvah`, and `voltR`. Numeric readings may be represented as strings.

## Error Handling

| HTTP status | Meaning |
|---|---|
| `200` | Request succeeded |
| `404` | Requested meter was not found |
| `422` | Request validation failed |
| `502` | Upstream portal request failed |

The health endpoint confirms that the wrapper is running; it does not guarantee that the upstream portal is reachable.

## Running Tests

Run the regular automated test suite:

```bash
python -m pytest -q
```

Run the live integration tests separately:

```bash
RUN_LIVE_TESTS=1 python -m pytest -q tests/test_live_portal.py
```

The live tests require a valid session cookie in the local `.env` file and access to the upstream portal. They are opt-in so ordinary tests do not depend on external availability.

## Generating the OpenAPI Specification

After changing API routes or schemas, regenerate the checked-in specification:

```bash
python -c "import json; from app.main import app; open('openapi.json', 'w', encoding='utf-8').write(json.dumps(app.openapi(), indent=2) + '\n')"
```

## Known Limitations

- Upstream authentication currently relies on a session cookie.
- Automatic login and re-authentication after session expiry have not been verified successfully.
- Upstream data structures and availability depend on the legacy portal.
- The API is read-only and does not create or modify portal records.
## Assumptions

- The legacy Urja Meter Ops portal is the source of truth for meter, transformer, and energy-consumption data.
- The wrapper is intended for read-only access and does not create, update, or delete portal records.
- Portal responses and authentication behavior may change because the upstream system is outside this project's control.

## Design Decisions and Trade-offs

- **FastAPI:** Provides request validation, typed endpoints, and automatic OpenAPI documentation.
- **HTTPX:** Provides an asynchronous HTTP client for communicating with the upstream portal.
- **Session-cookie authentication:** Uses an existing authenticated portal session because automated login and session renewal have not been verified successfully.
- **Read-only scope:** Keeps the implementation focused on retrieving and exposing portal data rather than modifying legacy records.
- **Trade-off:** The session-cookie approach is straightforward but requires a valid cookie and does not yet provide verified automatic renewal.

## Intentional Omissions

- Create, update, and delete operations.
- Verified automatic login and session renewal.
- Caching and a local database or search index.
- A separate frontend or user interface.

## Future Improvements

- Implement and test reliable authentication renewal.
- Add stronger retry handling and more detailed upstream error reporting.
- Introduce caching if appropriate for the portal's data and freshness requirements.
- Expand tests for upstream failures, expired sessions, and unusual response formats.
- Add deployment guidance and operational monitoring.

## Additional Documentation

- [Portal investigation and protocol notes](PROTOCOL.md)
- [OpenAPI specification](openapi.json)
- [Assessment reflection](REFLECTION.md)
