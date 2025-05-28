# test_user_tenant_relationship.py
from app.db.session import SessionLocal
from app.db.models import Tenant, User
from uuid import uuid4
from datetime import datetime

def test_user_tenant_relationship():
    """Test User-Tenant relationship and verify database schema works correctly"""
    db = SessionLocal()
    try:
        print("🧪 Testing User-Tenant relationship...")
        
        # Create a test tenant
        test_tenant = Tenant(
            name="Test Company",
            subdomain="test-company",
            slug="test-company",
            plan_type="trial",
            status="trial"
        )
        db.add(test_tenant)
        db.flush()  # Get the ID without committing
        print(f"✅ Created test tenant: {test_tenant.name} (ID: {test_tenant.id})")
        
        # Create a test user
        test_user = User(
            tenant_id=test_tenant.id,
            identity_provider="entra_id",
            identity_provider_id=str(uuid4()),
            email="test@testcompany.com",
            display_name="Test User",
            status="active",
            user_metadata='{"department": "IT", "role": "admin"}'
        )
        db.add(test_user)
        db.commit()
        print(f"✅ Created test user: {test_user.email} (ID: {test_user.id})")
        
        # Test the relationship - user to tenant
        print(f"✅ User's tenant: {test_user.tenant.name}")
        assert test_user.tenant.id == test_tenant.id, "User-tenant relationship failed"
        
        # Test the relationship - tenant to users
        tenant_user_emails = [user.email for user in test_tenant.users]
        print(f"✅ Tenant's users: {tenant_user_emails}")
        assert test_user.email in tenant_user_emails, "Tenant-users relationship failed"
        
        # Test login stats update
        original_login_count = test_user.login_count
        test_user.update_login_stats()
        db.commit()
        
        print(f"✅ Login count: {original_login_count} → {test_user.login_count}")
        print(f"✅ Last login: {test_user.last_login_at}")
        print(f"✅ Last active: {test_user.last_active_at}")
        
        # Test activity update
        test_user.update_activity()
        db.commit()
        print(f"✅ Activity updated: {test_user.last_active_at}")
        
        # Test user metadata
        print(f"✅ User metadata: {test_user.user_metadata}")
        
        # Test BaseEntity fields
        print(f"✅ BaseEntity fields:")
        print(f"   - ID: {test_user.id}")
        print(f"   - Index ID: {test_user.index_id}")
        print(f"   - Tenant ID: {test_user.tenant_id}")
        print(f"   - Created: {test_user.created_at}")
        print(f"   - Updated: {test_user.updated_at}")
        print(f"   - Deleted: {test_user.is_deleted}")
        
        # Clean up
        db.delete(test_user)
        db.delete(test_tenant)
        db.commit()
        print("🧹 Cleaned up test data")
        
        print("\n🎉 All User-Tenant relationship tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_user_tenant_relationship()
    if not success:
        exit(1)