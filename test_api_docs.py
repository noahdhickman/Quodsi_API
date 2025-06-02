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