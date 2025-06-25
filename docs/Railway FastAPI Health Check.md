# Railway FastAPI Health Check 301 Redirect Solutions

Railway deployment health checks are failing because **Railway does not follow redirects** and expects exactly HTTP 200 responses. Your FastAPI application is returning 301 redirects on `/api/v1/health/ready`, preventing successful deployment despite the app running correctly.

## Root Cause Analysis

**FastAPI's automatic trailing slash behavior** is the primary culprit. FastAPI automatically redirects requests when there's a trailing slash mismatch - if your route is defined as `/api/v1/health/ready` but Railway requests `/api/v1/health/ready/` (or vice versa), FastAPI returns a redirect response. Railway's health checker treats any non-200 response as a failure and **does not follow redirects**.

## Primary Solutions

### Solution 1: Disable FastAPI redirect behavior (Recommended)

For FastAPI 0.98.0 and later, use the `redirect_slashes=False` parameter:

```python
from fastapi import FastAPI
import os
import uvicorn

# Disable redirects globally
app = FastAPI(redirect_slashes=False)

@app.get("/api/v1/health/ready")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
```

### Solution 2: Define both route variants

Support both with and without trailing slashes:

```python
@app.get("/api/v1/health/ready")
@app.get("/api/v1/health/ready/")
async def health_check():
    return {"status": "healthy"}
```

### Solution 3: Use Railway-optimized configuration

Create a dedicated health router with redirects disabled:

```python
from fastapi import FastAPI, APIRouter

app = FastAPI()
health_router = APIRouter(redirect_slashes=False)

@health_router.get("/ready")
async def health_check():
    return {"status": "healthy"}

app.include_router(health_router, prefix="/api/v1/health")
```

## Server Configuration Fixes

### Switch to Hypercorn for better Railway compatibility

Railway's private networking can cause IPv4/IPv6 binding issues with Uvicorn. **Hypercorn provides better dual-stack support**:

```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "deploy": {
    "startCommand": "hypercorn main:app --bind \"[::]:$PORT\"",
    "healthcheckPath": "/api/v1/health/ready",
    "healthcheckTimeout": 300
  }
}
```

Install Hypercorn: `pip install hypercorn`

### Ensure proper host binding

Always bind to `0.0.0.0` (or `::` for IPv6) to make your service accessible to Railway's health checker:

```python
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # Critical: bind to 0.0.0.0, not localhost or 127.0.0.1
    uvicorn.run("main:app", host="0.0.0.0", port=port)
```

## Debugging and Verification

### Test redirect behavior locally

```bash
# Test both variants to identify redirect behavior
curl -v http://localhost:8000/api/v1/health/ready
curl -v http://localhost:8000/api/v1/health/ready/

# Check for redirects without following them
curl -I http://localhost:8000/api/v1/health/ready
```

### Add logging middleware for debugging

```python
import logging
from fastapi import Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response
```

### Test with FastAPI TestClient

```python
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health_check():
    # Test without redirect following
    response = client.get("/api/v1/health/ready", allow_redirects=False)
    assert response.status_code == 200  # Should not be 301 or 307
```

## Alternative Health Check Patterns

### Simplified health check path

Consider using a simpler path that's less prone to redirect issues:

```python
# In railway.json
{
  "deploy": {
    "healthcheckPath": "/health"
  }
}

# In your FastAPI app
@app.get("/health")
async def simple_health_check():
    return {"status": "OK"}
```

### Kubernetes-style endpoints

Implement separate liveness and readiness checks:

```python
@app.get("/healthz/live")
async def liveness_check():
    """Always returns healthy if app is running"""
    return {"status": "alive"}

@app.get("/healthz/ready") 
async def readiness_check():
    """Returns healthy only if app can serve requests"""
    # Add any dependency checks here
    return {"status": "ready"}
```

## Complete Working Example

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
import uvicorn

# Disable automatic redirects
app = FastAPI(redirect_slashes=False)

@app.get("/api/v1/health/ready")
async def health_check():
    return JSONResponse(
        content={"status": "healthy", "service": "api"},
        status_code=200
    )

# Optional: support both variants for maximum compatibility
@app.get("/api/v1/health/ready/")
async def health_check_with_slash():
    return JSONResponse(
        content={"status": "healthy", "service": "api"},
        status_code=200
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
```

Railway configuration (`railway.json`):

```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "deploy": {
    "healthcheckPath": "/api/v1/health/ready",
    "healthcheckTimeout": 180,
    "restartPolicyType": "ON_FAILURE"
  }
}
```

## Emergency Workaround

If issues persist, temporarily **disable health checks** to allow deployment:

```json
{
  "deploy": {
    "healthcheckPath": null
  }
}
```

Then diagnose the redirect issue in your deployed application and re-enable health checks once fixed.

## Key Takeaways

1. **Railway health checks never follow redirects** - they expect immediate 200 responses
2. **FastAPI's trailing slash behavior** is the most common cause of health check redirects
3. **Use `redirect_slashes=False`** as the primary solution for FastAPI 0.98.0+
4. **Always bind to `0.0.0.0:$PORT`** for Railway compatibility
5. **Consider Hypercorn over Uvicorn** for better Railway deployment stability
6. **Test both route variants** during development to catch redirect issues early

These solutions address the core issue while providing backup strategies and debugging techniques to ensure reliable Railway deployments with FastAPI health checks.