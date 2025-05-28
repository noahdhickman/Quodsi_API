from app.repositories.user_repository import user_repo
from app.repositories.tenant_repository import tenant_repo
from app.schemas.user import UserCreate
from app.schemas.tenant import TenantCreate
from app.db.session import SessionLocal
from uuid import uuid4
import time

def test_user_repository_basic():
    """Test basic UserRepository functionality"""
    
    db = SessionLocal()
    
    try:
        print("🧪 Testing UserRepository - Basic Functions...")
        
        # Create a test tenant with unique name to avoid conflicts
        unique_suffix = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
        tenant_data = TenantCreate(
            name=f"Test Company {unique_suffix}",
            plan_type="trial",
            status="trial"
        )
        test_tenant = tenant_repo.create(db, obj_in=tenant_data)
        print(f"✅ Created test tenant: {test_tenant.name}")
        
        # Test email availability check
        test_email = f"test{unique_suffix}@example.com"
        available = user_repo.check_email_availability(db, test_tenant.id, test_email)
        assert available == True, "Email should be available"
        print("✅ Email availability check works")
        
        # Test user creation
        user_data = UserCreate(
            email=test_email,
            display_name="Test User",
            identity_provider="local_dev_registration",
            identity_provider_id=f"test-user-{unique_suffix}",
            tenant_id=test_tenant.id  # Include tenant_id as required by schema
        )
        
        new_user = user_repo.create_user_for_tenant(db, obj_in=user_data)
        print(f"✅ Created user: {new_user.email} in tenant {test_tenant.name}")
        
        # Test email no longer available
        available = user_repo.check_email_availability(db, test_tenant.id, test_email)
        assert available == False, "Email should no longer be available"
        print("✅ Email uniqueness enforcement works")
        
        # Test get by email
        found_user = user_repo.get_by_email(db, test_tenant.id, test_email)
        assert found_user is not None, "Should find user by email"
        assert found_user.id == new_user.id, "Should be the same user"
        print("✅ Get by email works")
        
        # Test get by identity provider
        found_user = user_repo.get_by_identity_provider_id(
            db, "local_dev_registration", f"test-user-{unique_suffix}"
        )
        assert found_user is not None, "Should find user by identity provider"
        assert found_user.id == new_user.id, "Should be the same user"
        print("✅ Identity provider lookup works")
        
        # Test login stats update
        original_count = new_user.login_count or 0
        updated_user = user_repo.update_login_stats(db, test_tenant.id, new_user.id)
        assert updated_user.login_count == original_count + 1, "Login count should increment"
        assert updated_user.last_login_at is not None, "Last login should be set"
        print("✅ Login stats update works")
        
        # Test user search
        search_results = user_repo.search_users(db, test_tenant.id, search_term="test", limit=10)
        assert len(search_results) >= 1, "Should find user in search"
        print("✅ User search works")
        
        # Clean up
        user_repo.soft_delete(db, test_tenant.id, new_user.id)
        tenant_repo.soft_delete(db, test_tenant.id, test_tenant.id)
        db.commit()
        print("✅ Cleaned up test data")
        
        print("\n🎉 UserRepository basic tests passed!")
        
    except Exception as e:
        print(f"❌ UserRepository test failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_user_repository_basic()