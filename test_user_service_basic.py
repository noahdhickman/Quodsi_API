from app.services.user_service import UserService
from app.services.registration_service import RegistrationService
from app.schemas.user import UserRegistration, UserProfileUpdate
from app.db.session import SessionLocal
from uuid import uuid4

def test_user_service_basic():
    """Test basic UserService functionality"""
    
    db = SessionLocal()
    
    try:
        print("🧪 Testing UserService - Basic Functions...")
        
        # Setup: Create a test user and tenant
        registration_service = RegistrationService(db)
        user_service = UserService(db)
        
        registration_data = UserRegistration(
            email="testuser@userservice.com",
            display_name="Test User",
            identity_provider="local_dev_registration",
            identity_provider_id=f"test-user-service-{uuid4()}",
            company_name="User Service Test Company"
        )
        
        tenant, user = registration_service.register_user_and_tenant(registration_data)
        print(f"✅ Setup: Created user {user.email} in tenant {tenant.name}")
        
        # Test 1: Authentication
        print("\n--- Test 1: User Authentication ---")
        auth_result = user_service.authenticate_user(
            registration_data.identity_provider,
            registration_data.identity_provider_id
        )
        
        assert auth_result.success == True, "Authentication should succeed"
        assert auth_result.user is not None, "Should return user data"
        assert auth_result.tenant is not None, "Should return tenant data"
        print(f"✅ Authentication successful: {auth_result.message}")
        
        # Test 2: Get User Profile
        print("\n--- Test 2: User Profile ---")
        profile = user_service.get_user_profile(tenant.id, user.id)
        
        assert profile is not None, "Should return user profile"
        assert profile.email == user.email, "Should return correct user data"
        assert profile.login_count >= 1, "Should show login count from authentication"
        print(f"✅ Profile retrieved: {profile.display_name}")
        
        # Test 3: Update Profile
        print("\n--- Test 3: Profile Update ---")
        profile_update = UserProfileUpdate(
            display_name="Updated Test User",
            user_metadata='{"theme": "dark"}'
        )
        
        updated_profile = user_service.update_user_profile(
            tenant.id, user.id, profile_update
        )
        
        assert updated_profile.display_name == "Updated Test User", "Should update display name"
        print(f"✅ Profile updated: {updated_profile.display_name}")
        
        # Test 4: Session Tracking
        print("\n--- Test 4: Session Tracking ---")
        session_tracked = user_service.track_user_session(tenant.id, user.id, 30)
        
        assert session_tracked == True, "Should successfully track session"
        print("✅ Session tracking works")
        
        # Test 5: Activity Summary
        print("\n--- Test 5: Activity Summary ---")
        activity_summary = user_service.get_user_activity_summary(tenant.id, user.id)
        
        assert activity_summary is not None, "Should return activity summary"
        assert activity_summary.engagement_level in ["high", "medium", "low", "inactive"], "Should calculate engagement"
        print(f"✅ Activity summary: {activity_summary.engagement_level} engagement")
        
        # Clean up
        from app.repositories.user_repository import user_repo
        from app.repositories.tenant_repository import tenant_repo
        
        user_repo.soft_delete(db, tenant.id, user.id)
        tenant_repo.soft_delete(db, tenant.id, tenant.id)
        db.commit()
        print("✅ Cleaned up test data")
        
        print("\n🎉 UserService basic tests passed!")
        
    except Exception as e:
        print(f"❌ UserService test failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_user_service_basic()