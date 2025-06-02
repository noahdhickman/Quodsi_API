# debug_organization.py - Debug organization creation issues
"""
Debug script to test organization creation at each layer
Run this to find exactly where the issue is happening
"""

import sys
import os
from uuid import uuid4

# Add project root to path
sys.path.append(os.getcwd())


def test_database_connection():
    """Test if we can connect to the database"""
    print("🔌 Testing database connection...")
    try:
        from app.db.session import get_db

        db = next(get_db())
        print("✅ Database connection successful")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False


def test_organization_model():
    """Test if we can create an Organization model instance"""
    print("\n📦 Testing Organization model...")
    try:
        from app.db.models.organization import Organization
        from datetime import datetime, timezone

        org = Organization(
            name="Test Model Org",
            domain="test.com",
            tenant_id=uuid4(),
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        print("✅ Organization model creation successful")
        print(f"   Name: {org.name}")
        print(f"   Domain: {org.domain}")
        return True
    except Exception as e:
        print(f"❌ Organization model creation failed: {str(e)}")
        return False


def test_repository_import():
    """Test if we can import the repository"""
    print("\n📚 Testing repository import...")
    try:
        from app.repositories import organization_repo

        print("✅ Repository import successful")
        print(f"   Repository type: {type(organization_repo)}")
        return True
    except Exception as e:
        print(f"❌ Repository import failed: {str(e)}")
        return False


def test_service_import():
    """Test if we can import and create the service"""
    print("\n⚙️  Testing service import...")
    try:
        from app.services.organization_service import OrganizationService
        from app.db.session import get_db

        db = next(get_db())
        service = OrganizationService(db)
        print("✅ Service creation successful")
        print(f"   Service type: {type(service)}")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Service creation failed: {str(e)}")
        return False


def test_schema_validation():
    """Test if the Pydantic schemas work"""
    print("\n📋 Testing schema validation...")
    try:
        from app.schemas.organization import OrganizationCreate

        org_data = OrganizationCreate(
            name="Test Schema Org", domain="schema.com", billing_email="test@schema.com"
        )
        print("✅ Schema validation successful")
        print(f"   Name: {org_data.name}")
        print(f"   Domain: {org_data.domain}")
        return True
    except Exception as e:
        print(f"❌ Schema validation failed: {str(e)}")
        return False


def test_database_table():
    """Test if the organizations table exists"""
    print("\n🗄️  Testing database table...")
    try:
        from app.db.session import get_db
        from sqlalchemy import text

        db = next(get_db())
        result = db.execute(text("SELECT COUNT(*) FROM organizations")).fetchone()
        print("✅ Organizations table accessible")
        print(f"   Current row count: {result[0]}")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Organizations table test failed: {str(e)}")
        return False


def test_full_creation():
    """Test creating an organization through the service layer"""
    print("\n🏗️  Testing full organization creation...")
    try:
        from app.services.organization_service import OrganizationService
        from app.schemas.organization import OrganizationCreate
        from app.db.session import get_db

        db = next(get_db())
        service = OrganizationService(db)

        org_data = OrganizationCreate(
            name="Debug Test Corp",
            domain="debug.com",
            billing_email="billing@debug.com",
        )

        tenant_id = uuid4()
        print(f"   Using tenant_id: {tenant_id}")

        # This is where the actual error likely occurs
        new_org = service.create_organization(
            tenant_id=tenant_id, organization_data=org_data
        )

        print("✅ Full organization creation successful")
        print(f"   Created org ID: {new_org.id}")
        print(f"   Created org name: {new_org.name}")

        # Clean up - delete the test org
        service.delete_organization(tenant_id, new_org.id)

        db.close()
        return True
    except Exception as e:
        print(f"❌ Full organization creation failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        import traceback

        print(f"   Full traceback:\n{traceback.format_exc()}")
        return False


def main():
    """Run all debug tests"""
    print("🐛 Organization Debug Test Suite")
    print("=" * 50)

    tests = [
        test_database_connection,
        test_organization_model,
        test_repository_import,
        test_service_import,
        test_schema_validation,
        test_database_table,
        test_full_creation,  # This will likely show us the exact error
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {str(e)}")
            results.append(False)
        print()

    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"📊 Debug Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Everything working! The API issue might be elsewhere.")
    else:
        print("🔍 Found issues! Check the failed tests above.")


if __name__ == "__main__":
    main()
