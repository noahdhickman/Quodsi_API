# test_user_schemas.py
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserRegistration, 
    UserInDB, LoginStats, UserWithTenant
)
from uuid import uuid4
from datetime import datetime
import json

def test_user_create_schema():
    """Test UserCreate schema validation"""
    print("\n🧪 Testing UserCreate schema...")
    
    # Valid data
    valid_data = {
        "email": "john.doe@acme.com",
        "display_name": "John Doe",
        "identity_provider": "entra_id",
        "identity_provider_id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "status": "active",
        "user_metadata": '{"department": "IT", "role": "admin"}'
    }
    
    try:
        user_create = UserCreate(**valid_data)
        print(f"✅ UserCreate valid: {user_create.email} ({user_create.status})")
        print(f"   Identity provider: {user_create.identity_provider}")
        print(f"   Metadata: {user_create.user_metadata}")
    except Exception as e:
        print(f"❌ UserCreate failed: {e}")
        return False
    
    # Test invalid email
    try:
        invalid_email_data = valid_data.copy()
        invalid_email_data["email"] = "not-an-email"
        UserCreate(**invalid_email_data)
        print("❌ Should have failed with invalid email")
        return False
    except Exception:
        print("✅ Correctly rejected invalid email")
    
    # Test missing required fields
    try:
        missing_field_data = valid_data.copy()
        del missing_field_data["display_name"]
        UserCreate(**missing_field_data)
        print("❌ Should have failed with missing display_name")
        return False
    except Exception:
        print("✅ Correctly rejected missing required field")
    
    return True

def test_user_update_schema():
    """Test UserUpdate schema validation"""
    print("\n🧪 Testing UserUpdate schema...")
    
    # Test partial update (all fields optional)
    update_data = {
        "display_name": "John D. Smith",
        "user_metadata": '{"timezone": "America/New_York", "theme": "dark"}'
    }
    
    try:
        user_update = UserUpdate(**update_data)
        print(f"✅ UserUpdate valid: {user_update.display_name}")
        print(f"   Metadata: {user_update.user_metadata}")
    except Exception as e:
        print(f"❌ UserUpdate failed: {e}")
        return False
    
    # Test empty update (should be valid)
    try:
        empty_update = UserUpdate()
        print("✅ Empty UserUpdate valid (all fields optional)")
    except Exception as e:
        print(f"❌ Empty UserUpdate failed: {e}")
        return False
    
    return True

def test_user_response_schema():
    """Test UserResponse schema validation"""
    print("\n🧪 Testing UserResponse schema...")
    
    response_data = {
        "id": str(uuid4()),
        "email": "jane.smith@acme.com",
        "display_name": "Jane Smith",
        "status": "active",
        "login_count": 5,
        "total_usage_minutes": 120,
        "last_login_at": datetime.utcnow(),
        "last_active_at": datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "tenant_id": str(uuid4())
    }
    
    try:
        user_response = UserResponse(**response_data)
        print(f"✅ UserResponse valid: {user_response.display_name}")
        print(f"   Login count: {user_response.login_count}")
        print(f"   Usage minutes: {user_response.total_usage_minutes}")
        print(f"   Last login: {user_response.last_login_at}")
    except Exception as e:
        print(f"❌ UserResponse failed: {e}")
        return False
    
    return True

def test_user_in_db_schema():
    """Test UserInDB schema validation"""
    print("\n🧪 Testing UserInDB schema...")
    
    db_data = {
        "id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "email": "db.user@acme.com",
        "display_name": "DB User",
        "identity_provider": "entra_id",
        "identity_provider_id": str(uuid4()),
        "status": "active",
        "login_count": 10,
        "total_usage_minutes": 300,
        "last_login_at": datetime.utcnow(),
        "last_active_at": datetime.utcnow(),
        "user_metadata": '{"preferences": {"notifications": true}}',
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_deleted": False
    }
    
    try:
        user_in_db = UserInDB(**db_data)
        print(f"✅ UserInDB valid: {user_in_db.email}")
        print(f"   Includes sensitive fields like identity_provider_id")
        print(f"   Has audit fields: created_at, updated_at, is_deleted")
    except Exception as e:
        print(f"❌ UserInDB failed: {e}")
        return False
    
    return True

def test_user_registration_schema():
    """Test UserRegistration schema validation"""
    print("\n🧪 Testing UserRegistration schema...")
    
    registration_data = {
        "email": "admin@newcompany.com",
        "display_name": "New Admin",
        "identity_provider": "entra_id",
        "identity_provider_id": str(uuid4()),
        "company_name": "New Company Inc",
        "tenant_slug": "new-company"
    }
    
    try:
        registration = UserRegistration(**registration_data)
        print(f"✅ UserRegistration valid: {registration.company_name}")
        print(f"   Admin user: {registration.email}")
        print(f"   Tenant slug: {registration.tenant_slug}")
    except Exception as e:
        print(f"❌ UserRegistration failed: {e}")
        return False
    
    # Test without optional tenant_slug
    try:
        no_slug_data = registration_data.copy()
        del no_slug_data["tenant_slug"]
        registration_no_slug = UserRegistration(**no_slug_data)
        print("✅ UserRegistration valid without tenant_slug (auto-generated)")
    except Exception as e:
        print(f"❌ UserRegistration without slug failed: {e}")
        return False
    
    return True

def test_login_stats_schema():
    """Test LoginStats schema validation"""
    print("\n🧪 Testing LoginStats schema...")
    
    stats_data = {
        "user_id": str(uuid4()),
        "login_count": 25,
        "total_usage_minutes": 1500,
        "last_login_at": datetime.utcnow(),
        "last_session_start": datetime.utcnow(),
        "last_active_at": datetime.utcnow()
    }
    
    try:
        login_stats = LoginStats(**stats_data)
        print(f"✅ LoginStats valid: {login_stats.login_count} logins")
        print(f"   Usage: {login_stats.total_usage_minutes} minutes")
    except Exception as e:
        print(f"❌ LoginStats failed: {e}")
        return False
    
    return True

def test_user_with_tenant_schema():
    """Test UserWithTenant schema validation"""
    print("\n🧪 Testing UserWithTenant schema...")
    
    user_with_tenant_data = {
        "id": str(uuid4()),
        "email": "user@company.com",
        "display_name": "User With Tenant",
        "status": "active",
        "login_count": 5,
        "total_usage_minutes": 120,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "tenant_id": str(uuid4()),
        "tenant": {
            "id": str(uuid4()),
            "name": "Company Name",
            "subdomain": "company",
            "status": "active"
        }
    }
    
    try:
        user_with_tenant = UserWithTenant(**user_with_tenant_data)
        print(f"✅ UserWithTenant valid: {user_with_tenant.email}")
        print(f"   Tenant info: {user_with_tenant.tenant}")
    except Exception as e:
        print(f"❌ UserWithTenant failed: {e}")
        return False
    
    return True

def test_schema_serialization():
    """Test schema serialization to JSON"""
    print("\n🧪 Testing schema JSON serialization...")
    
    user_data = {
        "id": str(uuid4()),
        "email": "serialize@test.com",
        "display_name": "Serialize Test",
        "status": "active",
        "login_count": 1,
        "total_usage_minutes": 30,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "tenant_id": str(uuid4())
    }
    
    try:
        user_response = UserResponse(**user_data)
        json_str = user_response.model_dump_json()
        json_dict = json.loads(json_str)
        
        print("✅ Schema serializes to JSON correctly")
        print(f"   JSON keys: {list(json_dict.keys())}")
        print(f"   Email in JSON: {json_dict['email']}")
        
        # Test deserialization
        user_from_json = UserResponse.model_validate(json_dict)
        print("✅ Schema deserializes from JSON correctly")
        
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return False
    
    return True

def test_user_schemas():
    """Run all User Pydantic schema tests"""
    print("🧪 Testing User Pydantic Schemas")
    print("=" * 50)
    
    tests = [
        test_user_create_schema,
        test_user_update_schema,
        test_user_response_schema,
        test_user_in_db_schema,
        test_user_registration_schema,
        test_login_stats_schema,
        test_user_with_tenant_schema,
        test_schema_serialization
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All User schema tests passed!")
        return True
    else:
        print(f"❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = test_user_schemas()
    if not success:
        exit(1)