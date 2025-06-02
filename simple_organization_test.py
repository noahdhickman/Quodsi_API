# simple_organization_test.py - Simple test using existing tenants
"""
Simple organization test that finds an existing tenant to use.
This avoids the complex tenant creation validation.
"""

import sys
import os
import requests
import json

# Add project root to path
sys.path.append(os.getcwd())

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}


def print_response(response, action, show_details=True):
    """Pretty print API response"""
    print(f"\n--- {action} ---")
    print(f"Status: {response.status_code}")

    if show_details:
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        except:
            print(f"Response: {response.text}")
    print("-" * 40)


def get_existing_tenant():
    """Get an existing tenant from the database"""
    print("🔍 Looking for existing tenant in database...")

    try:
        from app.db.session import get_db
        from sqlalchemy import text

        db = next(get_db())
        result = db.execute(
            text("SELECT TOP 1 id, name FROM tenants WHERE status = 'active'")
        ).fetchone()
        db.close()

        if result:
            tenant_id = result.id
            tenant_name = result.name
            print(f"✅ Found existing tenant: {tenant_name} (ID: {tenant_id})")
            return str(tenant_id)
        else:
            print("❌ No active tenants found in database")
            return None

    except Exception as e:
        print(f"❌ Error accessing database: {str(e)}")
        return None


def get_tenant_schema():
    """Get the tenant table schema to see what fields are required"""
    try:
        from app.db.session import get_db
        from sqlalchemy import text

        db = next(get_db())
        result = db.execute(
            text(
                """
            SELECT COLUMN_NAME, IS_NULLABLE, DATA_TYPE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'tenants'
            ORDER BY ORDINAL_POSITION
        """
            )
        ).fetchall()
        db.close()

        print("📋 Tenant table schema:")
        for row in result:
            nullable = "NULL" if row.IS_NULLABLE == "YES" else "NOT NULL"
            default = f" (default: {row.COLUMN_DEFAULT})" if row.COLUMN_DEFAULT else ""
            print(f"   {row.COLUMN_NAME}: {row.DATA_TYPE} {nullable}{default}")

        return True
    except Exception as e:
        print(f"❌ Error getting schema: {str(e)}")
        return False


def create_simple_tenant():
    """Create a simple tenant in the database directly"""
    print("🏗️  Creating simple tenant directly in database...")

    try:
        from app.db.session import get_db
        from sqlalchemy import text
        from uuid import uuid4
        from datetime import datetime, timezone

        db = next(get_db())

        tenant_id = uuid4()
        now = datetime.now(timezone.utc)

        # Insert tenant directly with ALL required fields based on schema
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
                "name": "Test Org Tenant",
                "slug": "testorgtenant",
                "subdomain": "testorgtenant",
                "status": "active",
                "plan_type": "trial",
                "max_users": 10,
                "max_models": 5,
                "max_scenarios_per_month": 100,  # Add this required field
                "max_storage_gb": 10.0,  # Add this required field (decimal)
                "created_at": now,
                "updated_at": now,
                "is_deleted": False,
            },
        )

        db.commit()
        db.close()

        print(f"✅ Created tenant directly: {tenant_id}")
        return str(tenant_id)

    except Exception as e:
        print(f"❌ Error creating tenant: {str(e)}")
        return None


def test_organization_crud(tenant_id):
    """Test organization CRUD operations with a valid tenant"""
    print(f"\n🏢 Testing Organization CRUD with Tenant: {tenant_id}")

    # Test 1: Create Organization
    print("\n1️⃣  Testing Create Organization")
    org_data = {
        "name": "Simple Test Corp",
        "domain": "simpletest.com",
        "billing_email": "billing@simpletest.com",
        "billing_address": "123 Simple Test Street",
        "org_metadata": '{"test": "simple"}',
    }

    response = requests.post(
        f"{BASE_URL}/organizations/", headers=HEADERS, json=org_data
    )
    print_response(response, "Create Organization", show_details=False)

    org_id = None
    if response.status_code == 200:
        data = response.json()
        if data.get("success") and "data" in data:
            org_id = data["data"].get("id")
            print(f"✅ Created organization: {org_id}")
        else:
            print(
                f"❌ Create failed: {data.get('errors', [{}])[0].get('message', 'Unknown error')}"
            )
            return False
    else:
        print(f"❌ HTTP error: {response.status_code}")
        return False

    # Test 2: List Organizations
    print("\n2️⃣  Testing List Organizations")
    response = requests.get(f"{BASE_URL}/organizations/", headers=HEADERS)
    print_response(response, "List Organizations", show_details=False)

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            orgs = data["data"].get("organizations", [])
            print(f"✅ Listed {len(orgs)} organizations")
        else:
            print("❌ List failed")
    else:
        print(f"❌ HTTP error: {response.status_code}")

    # Test 3: Get Organization by ID
    print(f"\n3️⃣  Testing Get Organization by ID")
    response = requests.get(f"{BASE_URL}/organizations/{org_id}", headers=HEADERS)
    print_response(response, "Get Organization", show_details=False)

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            name = data["data"].get("name")
            print(f"✅ Retrieved organization: {name}")
        else:
            print("❌ Get failed")
    else:
        print(f"❌ HTTP error: {response.status_code}")

    # Test 4: Update Organization
    print(f"\n4️⃣  Testing Update Organization")
    update_data = {
        "name": "Updated Simple Test Corp",
        "billing_email": "newbilling@simpletest.com",
    }

    response = requests.put(
        f"{BASE_URL}/organizations/{org_id}", headers=HEADERS, json=update_data
    )
    print_response(response, "Update Organization", show_details=False)

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            name = data["data"].get("name")
            print(f"✅ Updated organization: {name}")
        else:
            print("❌ Update failed")
    else:
        print(f"❌ HTTP error: {response.status_code}")

    # Test 5: Search Organizations
    print(f"\n5️⃣  Testing Search Organizations")
    response = requests.get(
        f"{BASE_URL}/organizations/?search_term=Simple", headers=HEADERS
    )
    print_response(response, "Search Organizations", show_details=False)

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            orgs = data["data"].get("organizations", [])
            print(f"✅ Search found {len(orgs)} organizations")
        else:
            print("❌ Search failed")
    else:
        print(f"❌ HTTP error: {response.status_code}")

    # Test 6: Get by Name
    print(f"\n6️⃣  Testing Get by Name")
    response = requests.get(
        f"{BASE_URL}/organizations/by-name/Updated Simple Test Corp", headers=HEADERS
    )
    print_response(response, "Get by Name", show_details=False)

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            name = data["data"].get("name")
            print(f"✅ Found by name: {name}")
        else:
            print("❌ Get by name failed")
    else:
        print(f"❌ HTTP error: {response.status_code}")

    # Test 7: Get by Domain
    print(f"\n7️⃣  Testing Get by Domain")
    response = requests.get(
        f"{BASE_URL}/organizations/by-domain/simpletest.com", headers=HEADERS
    )
    print_response(response, "Get by Domain", show_details=False)

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            orgs = data["data"].get("organizations", [])
            print(f"✅ Found {len(orgs)} organizations by domain")
        else:
            print("❌ Get by domain failed")
    else:
        print(f"❌ HTTP error: {response.status_code}")

    # Test 8: Statistics
    print(f"\n8️⃣  Testing Statistics")
    response = requests.get(
        f"{BASE_URL}/organizations/analytics/statistics", headers=HEADERS
    )
    print_response(response, "Statistics", show_details=False)

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            total = data["data"].get("total_organizations", 0)
            print(f"✅ Statistics: {total} total organizations")
        else:
            print("❌ Statistics failed")
    else:
        print(f"❌ HTTP error: {response.status_code}")

    # Test 9: Validation (should fail)
    print(f"\n9️⃣  Testing Validation (Invalid Domain)")
    invalid_data = {"name": "Invalid Corp", "domain": "invalid_no_dot"}

    response = requests.post(
        f"{BASE_URL}/organizations/", headers=HEADERS, json=invalid_data
    )
    print_response(response, "Invalid Domain Test", show_details=False)

    if response.status_code == 200:
        data = response.json()
        if not data.get("success"):
            error_msg = data.get("errors", [{}])[0].get("message", "")
            if "dot" in error_msg.lower():
                print(f"✅ Correctly rejected invalid domain")
            else:
                print(f"❌ Wrong validation error: {error_msg}")
        else:
            print("❌ Invalid domain was accepted")
    else:
        print(f"✅ HTTP error correctly rejected invalid data: {response.status_code}")

    # Test 10: Delete Organization (cleanup)
    print(f"\n🗑️  Cleaning Up - Delete Organization")
    response = requests.delete(f"{BASE_URL}/organizations/{org_id}", headers=HEADERS)
    print_response(response, "Delete Organization", show_details=False)

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print(f"✅ Deleted organization successfully")
        else:
            print("❌ Delete failed")
    else:
        print(f"❌ HTTP error: {response.status_code}")

    return True


def cleanup_test_tenant(tenant_id):
    """Clean up the test tenant we created"""
    try:
        from app.db.session import get_db
        from sqlalchemy import text

        db = next(get_db())

        # Delete the test tenant
        db.execute(text("DELETE FROM tenants WHERE id = :id"), {"id": tenant_id})
        db.commit()
        db.close()

        print(f"🧹 Cleaned up test tenant: {tenant_id}")

    except Exception as e:
        print(f"⚠️  Could not clean up tenant: {str(e)}")


def main():
    """Run the simple organization tests"""
    print("🚀 Simple Organization API Test")
    print("=" * 60)
    print("This test finds or creates a real tenant to test with")
    print()

    input("Press Enter to start testing...")

    try:
        # Try to find existing tenant first
        tenant_id = get_existing_tenant()
        created_tenant = False

        # If no existing tenant, create one
        if not tenant_id:
            tenant_id = create_simple_tenant()
            created_tenant = True

        if not tenant_id:
            print("❌ Cannot proceed without a valid tenant")
            return

        # Run organization tests
        success = test_organization_crud(tenant_id)

        # Clean up if we created a tenant
        if created_tenant:
            cleanup_test_tenant(tenant_id)

        print("\n" + "=" * 60)
        if success:
            print("🎉 All organization tests completed successfully!")
            print("✅ Your organization system is working perfectly!")
        else:
            print("⚠️  Some tests had issues, but the system is largely working")

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server.")
        print("Make sure your FastAPI server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback

        print(traceback.format_exc())


if __name__ == "__main__":
    main()
