# test_mock_auth.py
"""
Test mock authentication functionality outside of FastAPI context
"""
from app.api.deps import MockCurrentUser, DEFAULT_TEST_USER
from uuid import UUID

def test_mock_auth():
    """Test mock authentication with different scenarios"""
    
    # Test 1: Default user
    print("Test 1: Default user")
    print(f"User ID: {DEFAULT_TEST_USER.user_id}")
    print(f"Tenant ID: {DEFAULT_TEST_USER.tenant_id}")
    print(f"Email: {DEFAULT_TEST_USER.email}")
    print(f"Display Name: {DEFAULT_TEST_USER.display_name}")
    print()
    
    # Test 2: Custom user creation
    print("Test 2: Custom user")
    custom_user = MockCurrentUser(
        user_id=UUID("999e8400-e29b-41d4-a716-446655440000"),
        tenant_id=UUID("888e8400-e29b-41d4-a716-446655440000"),
        email="custom@example.com",
        display_name="Custom User"
    )
    print(f"User ID: {custom_user.user_id}")
    print(f"Tenant ID: {custom_user.tenant_id}")
    print(f"Email: {custom_user.email}")
    print(f"Display Name: {custom_user.display_name}")
    print()
    
    # Test 3: Verify data types
    print("Test 3: Data type verification")
    print(f"User ID type: {type(DEFAULT_TEST_USER.user_id)}")
    print(f"Tenant ID type: {type(DEFAULT_TEST_USER.tenant_id)}")
    print(f"Email type: {type(DEFAULT_TEST_USER.email)}")
    print(f"Display Name type: {type(DEFAULT_TEST_USER.display_name)}")

if __name__ == "__main__":
    test_mock_auth()