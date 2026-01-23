# TrueTrack Frontend Audit Report

## Executive Summary
The "standalone with reverse proxy" architecture is currently non-functional due to a critical routing misconfiguration in the backend `api/main.py` file. The implemented "reverse proxy" within FastAPI effectively blocks all access to the API, causing the application to fail.

## Findings

### 1. Critical Routing Misconfiguration (High Severity)
- **Issue**: The fallback catch-all route (`/{path:path}`) intended to proxy requests to the Next.js frontend is defined **before** the API router is included.
- **Impact**: In FastAPI, routes are matched in order of definition. The catch-all route matches *every* request, including API calls.
- **Root Cause**: In `api/main.py`, the `proxy_frontend` function is defined and registered (lines 304-343) before `app.include_router(api)` is called (line 345).
- **Compounding Factor**: The `proxy_frontend` handler explicitly raises `HTTPException(404)` if the path starts with `api/`. Since it catches everything, all API requests receive a 404 error and never reach the actual API endpoints.

### 2. "Dumb" Proxy Limitations (Medium Severity)
- **Issue**: The current proxy implementation using `httpx` reads the entire response body into memory before returning it.
- **Impact**: This breaks streaming responses (e.g., real-time updates, large file downloads) and increases memory usage / latency.
- **Recommendation**: Switch to a streaming proxy implementation using `StreamingResponse`.

### 3. Missing Frontend Build Verification (Low Severity)
- **Issue**: The `app.py` startup script checks for `server.js` but doesn't explicitly verify if the frontend build is fresh or valid.
- **Impact**: If the user forgets to build the frontend, the app will crash at startup with a `RuntimeError`.

## Proposed Architecture Logic

The core idea of "Python backend serving as a reverse proxy to a local Next.js standalone server" is sound for a localized "standalone" distribution. However, the implementation needs to respect the routing priority:

1.  **Static Files**: `/_next/static` (already correctly handled).
2.  **API Routes**: `/api/*` (must take precedence).
3.  **Frontend Pages**: `/*` (fallback for everything else).

## Recommendations

1.  **Reorder Routes**: Move `app.include_router(api)` to the top of the route definitions, before the catch-all proxy.
2.  **Remove Explicit Block**: Remove the `if path.startswith("api/")` check in the proxy, as the Router will naturally handle API requests first.
3.  **Implement Streaming**: Refactor `proxy_frontend` to stream responses from the Next.js server.
