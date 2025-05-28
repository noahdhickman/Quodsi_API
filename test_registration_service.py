from app.services.registration_service import RegistrationService
from app.schemas.user import UserRegistration
from app.db.session import SessionLocal
from uuid import uuid4
import time

def test_registration_service():
    """Test RegistrationService functionality"""
    
    db = SessionLocal()
    
    try:
        print("🧪 Testing RegistrationService...")
        
        registration_service = RegistrationService(db)
        
        # Generate unique identifiers for this test run
        test_run_id = str(uuid4())[:8]
        unique_slug = f"test-company-{test_run_id}"
        
        # Test 1: Successful registration
        print("\n--- Test 1: Successful Registration ---")
        registration_data = UserRegistration(
            email=f"admin-{test_run_id}@testcompany.com",
            display_name="Test Admin",
            identity_provider="local_dev_registration",
            identity_provider_id=f"test-admin-{uuid4()}",
            company_name="Test Company LLC",
            tenant_slug=unique_slug
        )
        
        tenant, user = registration_service.register_user_and_tenant(registration_data)
        
        assert tenant is not None, "Tenant should be created"
        assert user is not None, "User should be created"
        assert user.tenant_id == tenant.id, "User should belong to created tenant"
        assert tenant.name == "Test Company LLC", "Tenant should have correct name"
        assert user.email == f"admin-{test_run_id}@testcompany.com", "User should have correct email"
        
        print(f"✅ Created tenant: {tenant.name} (slug: {tenant.slug})")
        print(f"✅ Created user: {user.email} for tenant")
        print(f"✅ User belongs to tenant: {user.tenant_id == tenant.id}")
        
        # Test 2: Validation - duplicate identity provider
        print("\n--- Test 2: Duplicate Identity Provider Validation ---")
        duplicate_registration = UserRegistration(
            email=f"another-{test_run_id}@testcompany.com",
            display_name="Another Admin",
            identity_provider="local_dev_registration",
            identity_provider_id=registration_data.identity_provider_id,  # Same as before
            company_name="Another Company",
            tenant_slug=f"another-company-{test_run_id}"
        )
        
        try:
            registration_service.register_user_and_tenant(duplicate_registration)
            assert False, "Should have failed with duplicate identity provider"
        except ValueError as e:
            print(f"✅ Correctly rejected duplicate identity: {e}")
        
        # Test 3: Validation - duplicate tenant slug
        print("\n--- Test 3: Duplicate Tenant Slug Validation ---")
        duplicate_slug_registration = UserRegistration(
            email=f"admin2-{test_run_id}@testcompany2.com",
            display_name="Test Admin 2",
            identity_provider="local_dev_registration",
            identity_provider_id=f"test-admin-2-{uuid4()}",
            company_name="Test Company 2",
            tenant_slug=unique_slug  # Same slug as first registration
        )
        
        try:
            registration_service.register_user_and_tenant(duplicate_slug_registration)
            assert False, "Should have failed with duplicate tenant slug"
        except ValueError as e:
            print(f"✅ Correctly rejected duplicate slug: {e}")
        
        # Test 4: Validation check without registration
        print("\n--- Test 4: Registration Availability Check ---")
        validation_result = registration_service.validate_registration_availability(
            duplicate_slug_registration
        )
        
        assert validation_result["is_valid"] == False, "Should be invalid"
        assert len(validation_result["issues"]) > 0, "Should have issues"
        print(f"✅ Validation check works: {len(validation_result['issues'])} issues found")
        print(f"   Issues: {validation_result['issues']}")
        
        # Test 5: Registration suggestions
        print("\n--- Test 5: Registration Suggestions ---")
        suggestions = registration_service.get_registration_suggestions("New Amazing Company!")
        
        assert "suggested_slug" in suggestions, "Should provide slug suggestion"
        assert "suggested_subdomain" in suggestions, "Should provide subdomain suggestion"
        print(f"✅ Suggestions work:")
        print(f"   Suggested slug: {suggestions['suggested_slug']}")
        print(f"   Suggested subdomain: {suggestions['suggested_subdomain']}")
        
        # Test 6: Auto-generation when no slug provided
        print("\n--- Test 6: Auto-Generation Without Slug ---")
        auto_gen_registration = UserRegistration(
            email=f"auto-{test_run_id}@autogencompany.com",
            display_name="Auto Gen User",
            identity_provider="local_dev_registration",
            identity_provider_id=f"auto-gen-{uuid4()}",
            company_name=f"Auto Generated Company {test_run_id}",
            # No tenant_slug provided - should be auto-generated
        )
        
        auto_tenant, auto_user = registration_service.register_user_and_tenant(auto_gen_registration)
        
        assert auto_tenant.slug is not None, "Should auto-generate slug"
        assert auto_tenant.subdomain is not None, "Should auto-generate subdomain"
        print(f"✅ Auto-generation works:")
        print(f"   Generated slug: {auto_tenant.slug}")
        print(f"   Generated subdomain: {auto_tenant.subdomain}")
        
        # Clean up
        print("\n--- Cleanup ---")
        from app.repositories.user_repository import user_repo
        from app.repositories.tenant_repository import tenant_repo
        
        # Clean up first registration
        user_repo.soft_delete(db, tenant.id, user.id)
        tenant_repo.soft_delete(db, tenant.id, tenant.id)
        
        # Clean up auto-generated registration
        user_repo.soft_delete(db, auto_tenant.id, auto_user.id)
        tenant_repo.soft_delete(db, auto_tenant.id, auto_tenant.id)
        
        db.commit()
        print("✅ Cleaned up test data")
        
        print("\n🎉 RegistrationService tests passed!")
        
    except Exception as e:
        print(f"❌ RegistrationService test failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_registration_service()