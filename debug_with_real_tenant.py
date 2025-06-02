# debug_with_real_tenant.py - Debug organization creation with a real tenant
"""
Debug script to test organization creation with the tenant we just created successfully.
This will show us the exact error happening in organization creation.
"""

import sys
import os
from uuid import uuid4

# Add project root to path
sys.path.append(os.getcwd())


def create_test_tenant():
    """Create a test tenant (we know this works now)"""
    try:
        from app.db.session import get_db
        from sqlalchemy import text
        from uuid import uuid4
        from datetime import datetime, timezone

        db = next(get_db())

        tenant_id = uuid4()
        now = datetime.now(timezone.utc)

        # Insert tenant with all required fields
        db.execute(
            text(
                """
            INSERT INTO tenants (
                id, name, slug, subdomain, status, plan_type, 
                max_users, max_models, max_scenarios_per_month, max_storage_gb,
                created_at, updated_at, is_deleted
            )
            VALUES (
                :id, :name, :slug, :subdomain, :status, :plan_type, 
                :max_users, :max_models, :max_scenarios_per_month, :max_storage_gb,
                :created_at, :updated_at, :is_deleted
            )
        """
            ),
            {
                "id": tenant_id,
                "name": "Debug Test Tenant",
                "slug": "debugtest",
                "subdomain": "debugtest",
                "status": "active",
                "plan_type": "trial",
                "max_users": 10,
                "max_models": 5,
                "max_scenarios_per_month": 100,
                "max_storage_gb": 10.0,
                "created_at": now,
                "updated_at": now,
                "is_deleted": False,
            },
        )

        db.commit()
        db.close()

        print(f"✅ Created debug tenant: {tenant_id}")
        return tenant_id

    except Exception as e:
        print(f"❌ Error creating tenant: {str(e)}")
        return None


def test_organization_creation_detailed(tenant_id):
    """Test organization creation with detailed error reporting"""
    print(f"\n🔍 Testing organization creation with tenant: {tenant_id}")

    try:
        from app.services.organization_service import OrganizationService
        from app.schemas.organization import OrganizationCreate
        from app.db.session import get_db

        # Create service
        db = next(get_db())
        service = OrganizationService(db)

        # Create organization data
        org_data = OrganizationCreate(
            name="Debug Test Organization",
            domain="debug.com",
            billing_email="billing@debug.com",
            billing_address="123 Debug Street",
            org_metadata='{"debug": "test"}',
        )

        print(f"📋 Organization data created:")
        print(f"   Name: {org_data.name}")
        print(f"   Domain: {org_data.domain}")
        print(f"   Billing Email: {org_data.billing_email}")

        # Step-by-step debugging
        print(f"\n🔍 Step 1: Checking name uniqueness...")
        name_exists = service.organization_repo.name_exists(
            db, tenant_id, org_data.name
        )
        print(f"   Name exists: {name_exists}")

        print(f"\n🔍 Step 2: Validating domain format...")
        try:
            service._validate_domain_format(org_data.domain)
            print(f"   Domain validation: ✅ Passed")
        except Exception as e:
            print(f"   Domain validation: ❌ Failed - {str(e)}")
            return False

        print(f"\n🔍 Step 3: Validating JSON metadata...")
        try:
            service._validate_json_metadata(org_data.org_metadata)
            print(f"   JSON validation: ✅ Passed")
        except Exception as e:
            print(f"   JSON validation: ❌ Failed - {str(e)}")
            return False

        print(f"\n🔍 Step 4: Preparing creation data...")
        create_data = org_data.model_dump(exclude_unset=True)
        print(f"   Create data keys: {list(create_data.keys())}")

        print(f"\n🔍 Step 5: Attempting repository creation...")
        try:
            db_organization = service.organization_repo.create(
                db=db, obj_in=create_data, tenant_id=tenant_id
            )
            print(f"   Repository creation: ✅ Success")
            print(f"   Created org ID: {db_organization.id}")

            # Commit the transaction
            db.commit()

            print(f"\n✅ Organization created successfully!")
            print(f"   ID: {db_organization.id}")
            print(f"   Name: {db_organization.name}")
            print(f"   Domain: {db_organization.domain}")
            print(f"   Tenant ID: {db_organization.tenant_id}")

            return db_organization.id

        except Exception as e:
            db.rollback()
            print(f"   Repository creation: ❌ Failed")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {str(e)}")

            # Print full traceback for debugging
            import traceback

            print(f"\n🐛 Full error traceback:")
            print(traceback.format_exc())

            return False

    except Exception as e:
        print(f"❌ Error in test setup: {str(e)}")
        import traceback

        print(traceback.format_exc())
        return False


def cleanup_tenant(tenant_id):
    """Clean up the test tenant"""
    try:
        from app.db.session import get_db
        from sqlalchemy import text

        db = next(get_db())

        # Delete any organizations first
        db.execute(
            text("DELETE FROM organizations WHERE tenant_id = :tenant_id"),
            {"tenant_id": tenant_id},
        )

        # Delete the tenant
        db.execute(text("DELETE FROM tenants WHERE id = :id"), {"id": tenant_id})

        db.commit()
        db.close()

        print(f"🧹 Cleaned up tenant: {tenant_id}")

    except Exception as e:
        print(f"⚠️  Error cleaning up: {str(e)}")


def main():
    """Run detailed debug test"""
    print("🐛 Detailed Organization Creation Debug")
    print("=" * 50)

    # Create test tenant
    tenant_id = create_test_tenant()
    if not tenant_id:
        print("❌ Cannot proceed without tenant")
        return

    try:
        # Test organization creation with detailed logging
        result = test_organization_creation_detailed(tenant_id)

        if result:
            print(f"\n🎉 SUCCESS! Organization creation is working!")
            print(f"The issue was likely in the API layer, not the business logic.")
        else:
            print(f"\n❌ Organization creation failed.")
            print(f"Check the error details above to see what's wrong.")

    finally:
        # Always clean up
        cleanup_tenant(tenant_id)


if __name__ == "__main__":
    main()
