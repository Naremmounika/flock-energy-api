
# Upstream Protocol Documentation

## 1. Overview

The Flock Energy Meter API is a read-only HTTP wrapper around the Urja Meter Ops portal:

https://urja-ops.flockenergy.tech

The wrapper uses Python's HTTPX library to send asynchronous HTTP GET requests to the upstream portal. FastAPI exposes a separate, versioned REST API to clients.

Only read operations are implemented. No upstream create, update, or delete requests are issued.

## 2. Authentication

### Observed mechanism

The current implementation sends the following cookie when a session cookie is configured:

`Cookie: __Secure-better-auth.session_token=<session-cookie>`

The cookie value is loaded from the `PORTAL_SESSION_COOKIE` environment variable.

The client also sends these headers:

- `Accept: application/json`
- `Referer: https://urja-ops.flockenergy.tech/meters`

The cookie name was observed in browser traffic. This implementation does not establish that session cookies are the portal's officially supported integration mechanism.

### Login investigation

Browser network inspection identified the following login request:

- Method: `POST`
- Path: `/login`
- Content type: `application/x-www-form-urlencoded`
- Payload fields: `email`, `password`
- Observed session cookie name: `__Secure-better-auth.session_token`

An automated login attempt using the configured credentials returned HTTP 403. Therefore, automatic login has not been verified as working and should not be considered a supported capability of the current implementation.

### Limitations

- Session cookies may expire or be revoked.
- Automatic login and session renewal have not been verified successfully.
- Portal email and password settings are available in configuration, but the current session-cookie workflow is the verified authentication method.
- Authentication failures are reported as upstream errors.
- Credentials and cookies must not be included in source control or application logs.

A supported API authentication mechanism should be confirmed with the portal owner before production deployment.

## 3. Verified Upstream Endpoints

### 3.1 List and search meters

**Method:** `GET`

**Path:** `/portal/meters/search`

**Query parameters:**

| Parameter | Type | Observed usage |
|---|---|---|
| `q` | String | Search query; an empty string retrieves an unfiltered page |
| `page` | Integer | Page number, starting at 1 |

**Example request:**

`GET /portal/meters/search?q=J100040&page=1`

**Observed response structure:**

```json
{
  "data": [
    {
      "meterId": "J100040",
      "serialNo": "AL53485",
      "make": "Secure",
      "phaseType": "single",
      "installStatus": "Installed",
      "dtCode": "DT-001"
    }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 20
}
```

The observed search returned one matching record. The unfiltered first page returned 20 records with a reported total of 403.

### 3.2 List distribution transformers

**Method:** `GET`

**Path:** `/portal/dts`

**Query parameters:**

| Parameter | Type | Observed usage |
|---|---|---|
| `page` | Integer | Page number, starting at 1 |

**Example request:**

`GET /portal/dts?page=1`

**Observed response structure:**

```json
{
  "data": [
    {
      "code": "DT-001",
      "name": "Malviya Nagar DT 1",
      "feederCode": "F-001",
      "capacityKva": 100
    }
  ],
  "total": 40,
  "page": 1,
  "pageSize": 20
}
```

The first page returned 20 records, with a reported total of 40 transformers.

### 3.3 Retrieve meter energy readings

**Method:** `GET`

**Path:** `/portal/meters/{meter_id}/energy`

**Example request:**

`GET /portal/meters/J100040/energy`

**Observed response structure:**

```json
{
  "data": [
    {
      "timestamp": "23/06/2026 00:00",
      "kwh": "5219.83",
      "kvah": "5637.41",
      "voltR": "230"
    }
  ]
}
```

The portal returned energy readings containing a timestamp, kWh, kVAh, and red-phase voltage field. Numeric readings were represented as strings in the observed response.

The wrapper currently preserves this response structure rather than coercing the readings to numeric values.

### 3.4 Retrieve a meter through search

The wrapper retrieves a specific meter by querying the verified search endpoint:

**Method:** `GET`

**Path:** `/portal/meters/search`

**Example request:**

`GET /portal/meters/search?q=J100000&page=1`

The wrapper searches the returned `data` array for an exact `meterId` match. If no matching meter is found, the wrapper reports that the meter was not found.

A separate upstream meter-detail endpoint has not been verified.

## 4. Public API Mapping

| Public wrapper endpoint | Upstream endpoint |
|---|---|
| `GET /health` | Local health check; no upstream request |
| `GET /api/v1/meters` | `GET /portal/meters/search` |
| `GET /api/v1/meters/{meter_id}` | `GET /portal/meters/search?q={meter_id}&page=1` |
| `GET /api/v1/meters/{meter_id}/consumption` | `GET /portal/meters/{meter_id}/energy` |
| `GET /api/v1/transformers` | `GET /portal/dts` |

The wrapper exposes a versioned API prefix, `/api/v1`, to separate its public interface from the legacy portal's internal routes.

## 5. HTTP Client Behavior

The upstream client:

1. Constructs requests using the configured portal base URL.
2. Adds JSON acceptance and referer headers.
3. Adds the configured session cookie when present.
4. Sends asynchronous HTTP GET requests using HTTPX.
5. Applies the configured request timeout.
6. Does not automatically follow HTTP redirects.
7. Detects redirects and reports an upstream error when the response indicates that authentication or the upstream route may have changed.
8. Converts HTTP errors, connection failures, invalid JSON, and unexpected response structures into `PortalError` exceptions.

The FastAPI layer converts `PortalError` into an HTTP 502 response. Meter lookups that return no exact match are converted into HTTP 404 responses.

Pagination parameters are validated by FastAPI. The current implementation requests a single upstream page per API call; it does not automatically retrieve every page.

Although the client has been investigated for automatic login, the observed HTTP 403 response means that successful programmatic login and automatic session renewal are not currently verified.

## 6. Error Handling

| Condition | Wrapper behavior |
|---|---|
| Successful upstream JSON response | Return the upstream response body |
| Meter not found | Return HTTP 404 |
| Upstream HTTP error | Return HTTP 502 |
| Upstream connection failure | Return HTTP 502 |
| Invalid upstream JSON | Return HTTP 502 |
| Unexpected upstream response structure | Return HTTP 502 |
| Invalid page number | Return HTTP 422 |
| Search query exceeds 100 characters | Return HTTP 422 |
| Authentication failure | Report an upstream error |

The upstream HTTP status is included in the error detail when the portal returns an HTTP error. The wrapper does not intentionally expose authentication headers or cookie values in its error messages.

## 7. Endpoints and Capabilities Not Yet Verified

The following capabilities are not implemented or have not been verified sufficiently for reliable use:

- A dedicated upstream meter-detail endpoint; the wrapper uses the verified search endpoint instead.
- Full hierarchy or geographic data retrieval through the wrapper.
- Bulk export.
- Successful automated login using email and password.
- Automatic session renewal after expiry.
- Automatic pagination across all records.
- Write operations.

These capabilities should be investigated using authorized browser network traffic or documentation supplied by the portal owner. Endpoint names and authentication behavior should not be guessed.

## 8. Security Considerations

- Store session cookies in local environment configuration.
- Exclude `.env` from source control.
- Use authorized, read-only access.
- Do not log cookies, passwords, or authorization headers.
- Treat upstream error messages and response data as untrusted input.
- Confirm a supported integration authentication mechanism before production deployment.
- Rotate any session cookie that has been accidentally exposed.
