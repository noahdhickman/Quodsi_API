from app.repositories.tenant_repository import tenant_repo
from app.schemas.tenant import TenantCreate
from app.db.session import SessionLocal
from uuid import uuid4

def test_tenant_repository():
    """Test TenantRepository functionality"""
    
    db = SessionLocal()
    
    try:
        print("🧪 Testing TenantRepository...")
        
        # Test slug generation
        slug = tenant_repo.generate_unique_slug(db, "Acme Corporation")
        print(f"✅ Generated slug: '{slug}'")
        
        # Test subdomain generation
        subdomain = tenant_repo.generate_unique_subdomain(db, "Acme Corporation")
        print(f"✅ Generated subdomain: '{subdomain}'")
        
        # Test availability checks
        available = tenant_repo.check_slug_availability(db, "definitely-unique-slug-12345")
        print(f"✅ Slug availability check: {available}")
        
        available = tenant_repo.check_subdomain_availability(db, "definitelyunique12345")
        print(f"✅ Subdomain availability check: {available}")
        
        # Test tenant creation
        tenant_data = TenantCreate(
            name="Test Company",
            plan_type="trial",
            status="trial"
        )
        
        new_tenant = tenant_repo.create(db, obj_in=tenant_data)
        print(f"✅ Created tenant: {new_tenant.name} (slug: {new_tenant.slug})")
        
        # Test tenant lookup
        found_tenant = tenant_repo.get_by_slug(db, new_tenant.slug)
        assert found_tenant is not None, "Could not find tenant by slug"
        print(f"✅ Found tenant by slug: {found_tenant.name}")
        
        found_tenant = tenant_repo.get_by_subdomain(db, new_tenant.subdomain)
        assert found_tenant is not None, "Could not find tenant by subdomain"
        print(f"✅ Found tenant by subdomain: {found_tenant.name}")
        
        # Test tenant count
        count = tenant_repo.count_active_tenants(db)
        print(f"✅ Active tenant count: {count}")
        
        # Clean up
        tenant_repo.soft_delete(db, new_tenant.id, new_tenant.id)
        db.commit()
        print("✅ Cleaned up test tenant")
        
        print("\n🎉 TenantRepository tests passed!")
        
    except Exception as e:
        print(f"❌ TenantRepository test failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_tenant_repository()