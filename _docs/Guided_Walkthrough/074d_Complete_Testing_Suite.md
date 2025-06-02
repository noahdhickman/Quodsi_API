# Module 7.4d: Complete Testing Suite

## Purpose
Implement comprehensive integration tests for the complete API, including all endpoints, error handling, and documentation.

## Prerequisites
- Completed Module 7.4a (Centralized API Router Structure)
- Completed Module 7.4b (Global Middleware and Exception Handling)
- Completed Module 7.4c (Complete Main Application Setup)

---

## Part 4: Complete Testing Suite

### 4.1 API Integration Test

Create `test_api_integration.py`:

```python
# test_api_integration.py
"""
Integration tests for the complete API
"""
import requests
import json
from uuid import uuid4

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

def test_api_info():
    """Test API info endpoint"""
    response = requests.get(f"{API_URL}/")
    print(f"API Info: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 200

def test_health_checks():
    """Test all health check endpoints"""
    endpoints = [
        "/health/",
        "/health/detailed",
        "/health/liveness",
        "/health/readiness"
    ]
    
    for endpoint in endpoints:
        response = requests.get(f"{API_URL}{endpoint}")
        print(f"Health check {endpoint}: {response.status_code}")
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2, default=str))
        print()

def test_tenant_registration():
    """Test tenant registration"""
    registration_data = {
        "name": f"Test Company {uuid4().hex[:8]}",
        "domain": f"testco{uuid4().hex[:8]}",
        "admin_email": f"admin{uuid4().hex[:8]}@testco.com",
        "admin_password": "securepass123",
        "admin_display_name": "Test Admin"
    }
    
    response = requests.post(
        f"{API_URL}/auth/registration/tenant",
        json=registration_data
    )
    
    print(f"Tenant Registration: {response.status_code}")
    print(json.dumps(response.json(), indent=2, default=str))
    
    if response.status_code == 200:
        return response.json()["data"]
    return None

def test_user_profile_endpoints(tenant_data):
    """Test user profile endpoints with mock auth"""
    if not tenant_data:
        print("Skipping user profile tests - no tenant data")
        return
    
    headers = {
        "X-Mock-User-Id": str(tenant_data["admin_user_id"]),
        "X-Mock-Tenant-Id": str(tenant_data["tenant_id"]),
        "X-Mock-Email": tenant_data["admin_email"],
        "X-Mock-Display-Name": "Test Admin"
    }
    
    # Test get profile
    response = requests.get(f"{API_URL}/users/me", headers=headers)
    print(f"Get Profile: {response.status_code}")
    print(json.dumps(response.json(), indent=2, default=str))
    print()
    
    # Test update profile
    update_data = {
        "display_name": "Updated Admin Name",
        "role": "admin"
    }
    
    response = requests.put(
        f"{API_URL}/users/me",
        json=update_data,
        headers=headers
    )
    print(f"Update Profile: {response.status_code}")
    print(json.dumps(response.json(), indent=2, default=str))
    print()
    
    # Test list users
    response = requests.get(f"{API_URL}/users/", headers=headers)
    print(f"List Users: {response.status_code}")
    print(json.dumps(response.json(), indent=2, default=str))

def run_all_tests():
    """Run all integration tests"""
    print("=== API Integration Tests ===\n")
    
    # Test API info
    test_api_info()
    print()
    
    # Test health checks
    test_health_checks()
    print()
    
    # Test tenant registration
    tenant_data = test_tenant_registration()
    print()
    
    # Test user profile endpoints
    test_user_profile_endpoints(tenant_data)

if __name__ == "__main__":
    run_all_tests()
```

### 4.2 API Documentation Testing

Create `test_api_docs.py`:

```python
# test_api_docs.py
"""
Test API documentation endpoints
"""
import requests

BASE_URL = "http://localhost:8000"

def test_openapi_schema():
    """Test OpenAPI schema generation"""
    response = requests.get(f"{BASE_URL}/openapi.json")
    print(f"OpenAPI Schema: {response.status_code}")
    
    if response.status_code == 200:
        schema = response.json()
        print(f"API Title: {schema.get('info', {}).get('title')}")
        print(f"API Version: {schema.get('info', {}).get('version')}")
        print(f"Available Paths: {len(schema.get('paths', {}))}")
        
        # List all endpoints
        paths = schema.get('paths', {})
        print("\nAvailable Endpoints:")
        for path, methods in paths.items():
            for method in methods.keys():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    print(f"  {method.upper()} {path}")

def test_swagger_ui():
    """Test Swagger UI availability"""
    response = requests.get(f"{BASE_URL}/docs")
    print(f"Swagger UI: {response.status_code}")
    
def test_redoc():
    """Test ReDoc availability"""
    response = requests.get(f"{BASE_URL}/redoc")
    print(f"ReDoc: {response.status_code}")

if __name__ == "__main__":
    print("=== API Documentation Tests ===\n")
    test_openapi_schema()
    print()
    test_swagger_ui()
    test_redoc()
```

---

## Summary

This module provides comprehensive testing for the complete API:

### ✅ **Implemented Components:**

1. **Integration Tests**: Complete API endpoint testing
2. **Health Check Tests**: All health endpoints verification
3. **Registration Tests**: Tenant registration workflow testing
4. **User Profile Tests**: User management endpoint testing
5. **Documentation Tests**: API documentation availability testing

### 🧪 **Running Tests:**

Start the API server first:
```bash
uvicorn app.main:app --reload
```

Then run the tests in separate terminals:
```bash
python test_api_integration.py
python test_api_docs.py
```

### 📚 **Next Steps:**

Continue to Module 7.4e: Production Considerations to prepare the application for production deployment.
