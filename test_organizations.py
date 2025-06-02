# test_organizations_fixed.py - Organization test with real tenant creation
"""
Fixed organization test that creates a real tenant first.
This solves the foreign key constraint issue.
"""

import requests
import json
from uuid import uuid4

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}

def print_response(response, action):
    """Pretty print API response"""
    print(f"\n--- {action} ---")
    print(f"Status: {response.status_code}")
    
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text}")
    print("-" * 40)

def create_test_tenant():
    """Create a test tenant first to solve the foreign key issue"""
    print("🏢 Creating Test Tenant First...")
    
    tenant_data = {
        "name": "Test Organization Tenant",
        "domain": "test-org-tenant.com",
        "admin_email": "admin@test-org-tenant.com",
        "admin_password": "TestPassword123!",
        "admin_display_name": "Test Admin"
    }
    
    response = requests.post(f"{BASE_URL}/auth/registration/tenant", headers=HEADERS, json=tenant_data)
    print_response(response, "Create Test Tenant")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success") and "data" in data:
            tenant_id = data["data"].get("tenant_id")
            print(f"✅ Created test tenant with ID: {tenant_id}")
            return tenant_id
        else:
            print("❌ Failed to create test tenant")
            return None
    else:
        print("❌ HTTP error creating test tenant")
        return None

def test_create_organization_with_real_tenant():
    """Test creating an organization with a real tenant"""
    # First create a test tenant
    tenant_id = create_test_tenant()
    if not tenant_id:
        print("❌ Cannot test organizations without a valid tenant")
        return None
    
    print(f"\n🏢 Testing Organization Creation with Real Tenant: {tenant_id}")
    
    org_data = {
        "name": "Real Test Corporation",
        "domain": "realtest.com",
        "billing_email": "billing@realtest.com",
        "billing_address": "123 Real Test Avenue",
        "stripe_customer_id": "cus_realtest123",
        "org_metadata": '{"industry": "testing", "size": "small"}'
    }
    
    response = requests.post(f"{BASE_URL}/organizations/", headers=HEADERS, json=org_data)
    print_response(response, "Create Organization with Real Tenant")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success") and "data" in data:
            org_id = data["data"].get("id")
            print(f"✅ Created organization with ID: {org_id}")
            return org_id, tenant_id
        else:
            print("❌ Failed to create organization")
            return None, tenant_id
    else:
        print("❌ HTTP error creating organization")
        return None, tenant_id

def test_all_with_real_tenant():
    """Test all organization functionality with a real tenant"""
    # Create organization with real tenant
    result = test_create_organization_with_real_tenant()
    if result is None:
        return
    
    org_id, tenant_id = result
    if not org_id:
        print("❌ Cannot continue without a created organization")
        return
    
    print(f"\n🎯 Testing with Organization ID: {org_id}")
    
    # Test list organizations
    print("\n📋 Testing Organization Listing")
    response = requests.get(f"{BASE_URL}/organizations/", headers=HEADERS)
    print_response(response, "List Organizations")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            orgs = data["data"].get("organizations", [])
            print(f"✅ Found {len(orgs)} organizations")
        else:
            print("❌ Failed to list organizations")
    
    # Test get by ID
    print(f"\n🔍 Testing Get Organization by ID: {org_id}")
    response = requests.get(f"{BASE_URL}/organizations/{org_id}", headers=HEADERS)
    print_response(response, f"Get Organization {org_id}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            org_name = data["data"].get("name")
            print(f"✅ Retrieved organization: {org_name}")
        else:
            print("❌ Failed to get organization")
    
    # Test update
    print(f"\n✏️  Testing Update Organization: {org_id}")
    update_data = {
        "name": "Updated Real Test Corporation",
        "billing_email": "newbilling@realtest.com"
    }
    
    response = requests.put(f"{BASE_URL}/organizations/{org_id}", headers=HEADERS, json=update_data)
    print_response(response, f"Update Organization {org_id}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            updated_name = data["data"].get("name")
            print(f"✅ Updated organization name to: {updated_name}")
        else:
            print("❌ Failed to update organization")
    
    # Test search
    print("\n🔍 Testing Organization Search")
    response = requests.get(f"{BASE_URL}/organizations/?search_term=Real", headers=HEADERS)
    print_response(response, "Search Organizations")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            orgs = data["data"].get("organizations", [])
            print(f"✅ Search returned {len(orgs)} results")
        else:
            print("❌ Failed to search organizations")
    
    # Test get by name
    print("\n📛 Testing Get Organization by Name")
    response = requests.get(f"{BASE_URL}/organizations/by-name/Updated Real Test Corporation", headers=HEADERS)
    print_response(response, "Get Organization by Name")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            org_name = data["data"].get("name")
            print(f"✅ Found organization by name: {org_name}")
        else:
            print("❌ Failed to get organization by name")
    
    # Test get by domain
    print("\n🌐 Testing Get Organizations by Domain")
    response = requests.get(f"{BASE_URL}/organizations/by-domain/realtest.com", headers=HEADERS)
    print_response(response, "Get Organizations by Domain")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            orgs = data["data"].get("organizations", [])
            domain = data["data"].get("domain")
            print(f"✅ Found {len(orgs)} organizations for domain: {domain}")
        else:
            print("❌ Failed to get organizations by domain")
    
    # Test statistics
    print("\n📊 Testing Organization Statistics")
    response = requests.get(f"{BASE_URL}/organizations/analytics/statistics", headers=HEADERS)
    print_response(response, "Organization Statistics")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            stats = data["data"]
            total = stats.get("total_organizations", 0)
            print(f"✅ Statistics retrieved - Total organizations: {total}")
        else:
            print("❌ Failed to get organization statistics")
    
    # Test validation (should fail)
    print("\n🚫 Testing Validation - Invalid Domain")
    invalid_org = {
        "name": "Invalid Domain Corp",
        "domain": "invalid_domain_no_dot"  # Should fail
    }
    
    response = requests.post(f"{BASE_URL}/organizations/", headers=HEADERS, json=invalid_org)
    print_response(response, "Create Organization with Invalid Domain")
    
    if response.status_code != 200:
        print("✅ Correctly rejected invalid domain")
    else:
        data = response.json()
        if not data.get("success"):
            print("✅ Correctly rejected invalid domain")
        else:
            print("❌ Invalid domain was accepted")
    
    # Clean up - delete the test organization
    print(f"\n🗑️  Cleaning Up - Delete Organization: {org_id}")
    response = requests.delete(f"{BASE_URL}/organizations/{org_id}", headers=HEADERS)
    print_response(response, f"Delete Organization {org_id}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print("✅ Organization deleted successfully")
        else:
            print("❌ Failed to delete organization")

def main():
    """Run the fixed organization tests"""
    print("🚀 Fixed Organization API Test")
    print("=" * 50)
    print("This test creates a real tenant first to solve the foreign key issue")
    print("Make sure your FastAPI server is running on http://localhost:8000")
    print()
    
    input("Press Enter to start testing...")
    
    try:
        test_all_with_real_tenant()
        
        print("\n" + "=" * 50)
        print("🎉 Fixed test completed!")
        print("✅ This test should work because it uses a real tenant ID")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server.")
        print("Make sure your FastAPI server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    main()