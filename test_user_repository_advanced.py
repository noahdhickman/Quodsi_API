from app.repositories.user_repository import user_repo
from app.repositories.tenant_repository import tenant_repo
from app.schemas.user import UserCreate
from app.schemas.tenant import TenantCreate
from app.db.session import SessionLocal

def test_user_repository_advanced():
    """Test advanced UserRepository functionality"""
    
    db = SessionLocal()
    
    try:
        print("🧪 Testing UserRepository - Advanced Features...")
        
        # Create a test tenant
        tenant_data = TenantCreate(
            name="Advanced Test Company",
            plan_type="trial",
            status="trial"
        )
        test_tenant = tenant_repo.create(db, obj_in=tenant_data)
        print(f"✅ Created test tenant: {test_tenant.name}")
        
        # Create multiple test users
        users = []
        for i in range(3):
            user_data = UserCreate(
                email=f"user{i}@advanced-test.com",
                display_name=f"Advanced User {i}",
                identity_provider="local_dev_registration",
                identity_provider_id=f"advanced-user-{i}",
                tenant_id=test_tenant.id
            )
            
            new_user = user_repo.create_user_for_tenant(
                db, obj_in=user_data
            )
            users.append(new_user)
            print(f"✅ Created user {i+1}: {new_user.email}")
        
        # Test usage time tracking
        user_repo.add_usage_time(db, test_tenant.id, users[0].id, 45)
        user_repo.add_usage_time(db, test_tenant.id, users[1].id, 30)
        print("✅ Added usage time to users")
        
        # Test activity tracking
        user_repo.update_activity_timestamp(db, test_tenant.id, users[0].id)
        user_repo.update_activity_timestamp(db, test_tenant.id, users[1].id)
        print("✅ Updated activity timestamps")
        
        # Test login stats for multiple users
        for user in users[:2]:  # First 2 users
            user_repo.update_login_stats(db, test_tenant.id, user.id)
        print("✅ Updated login stats")
        
        # Test user statistics
        stats = user_repo.get_user_statistics(db, test_tenant.id, users[0].id)
        assert "login_count" in stats, "Should include login count"
        assert stats["total_usage_minutes"] == 45, "Should show 45 minutes usage"
        print(f"✅ User statistics: {stats['login_count']} logins, {stats['total_usage_minutes']} minutes")
        
        # Test tenant user summary
        summary = user_repo.get_tenant_user_summary(db, test_tenant.id)
        assert summary["total_users"] == 3, "Should show 3 total users"
        assert summary["active_users"] == 3, "Should show 3 active users"
        print(f"✅ Tenant summary: {summary['total_users']} users, {summary['active_users']} active")
        
        # Test users by status counts
        active_count = user_repo.count_users_by_status(db, test_tenant.id, "active")
        assert active_count == 3, "Should count 3 active users"
        print(f"✅ Status counts: {active_count} active users")
        
        # Clean up
        for user in users:
            user_repo.soft_delete(db, test_tenant.id, user.id)
        tenant_repo.soft_delete(db, test_tenant.id, test_tenant.id)
        db.commit()
        print("✅ Cleaned up test data")
        
        print("\n🎉 UserRepository advanced tests passed!")
        
    except Exception as e:
        print(f"❌ UserRepository advanced test failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_user_repository_advanced()