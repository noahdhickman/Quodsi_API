# test_response_helpers.py
"""
Test API response helper functions
"""
from app.api.response_helpers import create_success_response, create_error_response, create_validation_error_response
from uuid import UUID
import json

def test_response_helpers():
    """Test response helper functions"""
    
    # Test 1: Success response
    print("Test 1: Success response")
    test_data = {"message": "Hello World", "count": 42}
    tenant_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    
    success_response = create_success_response(test_data, tenant_id)
    print("Success response structure:")
    print(json.dumps(success_response, indent=2, default=str))
    print()
    
    # Test 2: Error response
    print("Test 2: Error response")
    error_response = create_error_response(
        code="VALIDATION_ERROR",
        message="Email is required",
        field="email",
        tenant_id=tenant_id
    )
    print("Error response structure:")
    print(json.dumps(error_response, indent=2, default=str))
    print()
    
    # Test 3: Validation error response
    print("Test 3: Validation error response")
    validation_errors = [
        {"msg": "field required", "loc": ["email"]},
        {"msg": "ensure this value has at least 8 characters", "loc": ["password"]}
    ]
    
    validation_response = create_validation_error_response(validation_errors, tenant_id)
    print("Validation error response structure:")
    print(json.dumps(validation_response, indent=2, default=str))

if __name__ == "__main__":
    test_response_helpers()