
# Project Reflection — Flock Energy Meter API

## 1. Approach

I implemented a read-only REST API wrapper using Python and FastAPI to expose selected meter-operations data from the legacy Urja Meter Ops portal.

I inspected the portal's browser network requests to identify upstream endpoints, query parameters, authentication behavior, and response formats. I verified the meter listing and search endpoint, the distribution transformer listing endpoint, and the meter energy readings endpoint before implementing the wrapper.

I organized the implementation into configuration, upstream HTTP communication, data models, and API routes to separate responsibilities and make future changes easier.

## 2. Design Decisions

### FastAPI

I chose FastAPI because it supports asynchronous endpoints, request validation, and automatic OpenAPI documentation. These features make it suitable for building a documented REST API.

### HTTPX

I used HTTPX for asynchronous upstream GET requests. The client reuses an HTTP session, applies a configurable timeout, and converts upstream HTTP and connection failures into application-level errors. It does not automatically follow redirects.

### Environment-based configuration

The upstream base URL, timeout, and session-cookie configuration are loaded from environment variables. Email and password settings are also defined in the configuration, but successful automated login has not been verified.

This avoids placing credentials directly in source code.

### Read-only access

The wrapper currently issues only GET requests to the upstream data endpoints. This reduces the risk of accidentally modifying operational meter data.

### Error handling

Upstream failures are converted into HTTP 502 responses, while invalid request parameters are handled by FastAPI validation. A meter that cannot be found through the verified search endpoint returns HTTP 404.

## 3. Testing

I created automated API tests using FastAPI's `TestClient` and a fake upstream client. The fake client allows the main API behavior to be tested without depending on the live portal or an active session cookie.

The mocked tests cover:

1. Health-check response.
2. Meter listing.
3. Meter search.
4. Search with no matches.
5. Transformer listing.
6. Meter consumption readings.
7. Invalid pagination.
8. Unknown meter consumption.
9. Retrieving meter details.
10. Handling an unknown meter identifier.

The latest full test run passed all 13 tests, including the three opt-in live integration tests. The mocked tests and live tests were also run separately, and all three live tests passed when a valid session cookie was configured.

The live integration tests verify selected operations against the real portal, but they do not establish that every upstream behavior will remain reliable.

## 4. Challenges and Lessons Learned

### Understanding the legacy portal

The upstream API behavior was not fully documented for this implementation. Inspecting browser network requests helped identify actual endpoint paths, query parameters, and response formats.

### Session-based authentication

The observed portal requests used a session cookie. I configured the wrapper to accept that cookie through an environment variable.

I also investigated the browser's login request, which uses a form-encoded POST request with email and password fields. An automated login attempt returned HTTP 403, so successful programmatic login and session renewal remain unverified. The current verified workflow uses a valid session cookie.

### Testing application dependencies

Initially, the tests unintentionally reached the live upstream portal because the application's lifespan initialized a real client. I corrected this by using FastAPI dependency overrides, allowing tests to inject a fake client.

This reinforced the importance of isolating external dependencies in automated tests.

### Preserving upstream data

The portal returned some numeric energy readings as strings. I kept the response structure unchanged instead of silently changing values or treating missing readings as zero.

### Python test execution

Running tests through `python -m pytest` provided consistent test execution using the selected Python environment.

## 5. Current Limitations

- Authentication currently depends on a valid session cookie.
- Automated login and session renewal have not been verified successfully.
- Only the verified meter, transformer, and consumption upstream endpoints are used.
- Meter details are retrieved through the verified search endpoint rather than a dedicated upstream detail endpoint.
- Each listing request retrieves one upstream page; automatic pagination is not implemented.
- Meter hierarchy, geographic data, and bulk export are not implemented because their upstream behavior has not been verified.
- The mocked tests use representative fake data and do not establish live integration reliability.
- Retry policies for general transient failures, caching, rate limiting, and production monitoring are not implemented.

## 6. Future Improvements

If I continued developing the project, I would:

1. Confirm and implement the portal's supported service-to-service authentication mechanism.
2. Add response models and consistent public API field naming.
3. Add tests for upstream HTTP errors, timeouts, malformed responses, and authentication failures.
4. Add automatic pagination where appropriate.
5. Investigate meter-detail and hierarchy endpoints using verified portal behavior.
6. Add structured logging, request correlation IDs, and operational monitoring without logging credentials.
7. Consider retries for appropriate transient failures and rate limiting for API clients.
8. Add continuous integration checks for automated tests, formatting, and linting.

## 7. Conclusion

This project demonstrates a read-only REST API wrapper with meter listing and search, meter-detail retrieval through search, transformer listing, and energy-consumption retrieval. It includes request validation, upstream error handling, automated API tests, and generated OpenAPI documentation.

The implementation prioritizes verified behavior and transparent documentation over assuming undocumented endpoints or authentication mechanisms. Successful automated login and session renewal remain outstanding limitations.
## 8. Answers to the Required Reflection Questions

### What assumptions did you make?

I assumed that the portal's observed GET endpoints and response formats were representative of the data available to the wrapper. I also assumed that a valid session cookie could be supplied through environment configuration. I treated the wrapper as read-only and avoided implementing unverified upstream operations.

### What mistake did you make while solving this?

One mistake was allowing the application's lifespan to initialize a real upstream client during tests, which caused some tests to depend on the live portal. I corrected this by overriding the FastAPI dependency and injecting a fake client. This taught me to isolate external services when testing API behavior.

### If reviewing your own submission, what would you criticise?

I would criticise the incomplete authentication lifecycle because automatic login and session renewal are not yet verified. The wrapper also has limited retry handling, no automatic pagination, and only a small set of verified upstream operations. Before production use, I would strengthen authentication, expand failure-case testing, and improve operational logging and monitoring.
