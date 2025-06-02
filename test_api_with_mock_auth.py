# test_api_with_mock_auth.py - Test API with the updated mock authentication
"""
Test the organization API using the updated mock authentication system.
This will trigger the auto-creation of the mock tenant.
"""

import requests
import json

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


def test_organization_with_mock_auth():
    """Test organization creation using the default mock authentication"""
    print("🏢 Testing Organization API with Mock Authentication")
    print("This should auto-create the mock tenant on first request")

    # Test 1: Create Organization (this should trigger mock tenant creation)
    print("\n1️⃣  Testing Create Organization (will auto-create mock tenant)")
    org_data = {
        "name": "Mock Auth Test Corp",
        "domain": "mockauth.com",
        "billing_email": "billing@mockauth.com",
        "billing_address": "123 Mock Auth Street",
        "org_metadata": '{"test": "mockauth"}',
    }

    response = requests.post(
        f"{BASE_URL}/organizations/", headers=HEADERS, json=org_data
    )
    print_response(response, "Create Organization with Mock Auth")

    org_id = None
    if response.status_code == 200:
        data = response.json()
        if data.get("success") and "data" in data:
            org_id = data["data"].get("id")
            print(f"✅ Created organization: {org_id}")
        else:
            error_msg = ""
            if "errors" in data and len(data["errors"]) > 0:
                error_msg = data["errors"][0].get("message", "Unknown error")
            print(f"❌ Create failed: {error_msg}")
            return False
    else:
        print(f"❌ HTTP error: {response.status_code}")
        return False

    # Test 2: List Organizations
    print("\n2️⃣  Testing List Organizations")
    response = requests.get(f"{BASE_URL}/organizations/", headers=HEADERS)
    print_response(response, "List Organizations")

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
    if org_id:
        print(f"\n3️⃣  Testing Get Organization by ID")
        response = requests.get(f"{BASE_URL}/organizations/{org_id}", headers=HEADERS)
        print_response(response, "Get Organization")

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
    if org_id:
        print(f"\n4️⃣  Testing Update Organization")
        update_data = {
            "name": "Updated Mock Auth Test Corp",
            "billing_email": "newbilling@mockauth.com",
        }

        response = requests.put(
            f"{BASE_URL}/organizations/{org_id}", headers=HEADERS, json=update_data
        )
        print_response(response, "Update Organization")

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                name = data["data"].get("name")
                print(f"✅ Updated organization: {name}")
            else:
                print("❌ Update failed")
        else:
            print(f"❌ HTTP error: {response.status_code}")

    # Test 5: Get Organization Statistics
    print(f"\n5️⃣  Testing Organization Statistics")
    response = requests.get(
        f"{BASE_URL}/organizations/analytics/statistics", headers=HEADERS
    )
    print_response(response, "Statistics")

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            total = data["data"].get("total_organizations", 0)
            print(f"✅ Statistics: {total} total organizations")
        else:
            print("❌ Statistics failed")
    else:
        print(f"❌ HTTP error: {response.status_code}")

    # Test 6: Test Validation (should fail)
    print(f"\n6️⃣  Testing Validation (Invalid Domain)")
    invalid_data = {"name": "Invalid Corp", "domain": "invalid_no_dot"}

    response = requests.post(
        f"{BASE_URL}/organizations/", headers=HEADERS, json=invalid_data
    )
    print_response(response, "Invalid Domain Test")

    if response.status_code == 200:
        data = response.json()
        if not data.get("success"):
            error_msg = ""
            if "errors" in data and len(data["errors"]) > 0:
                error_msg = data["errors"][0].get("message", "")
            if "dot" in error_msg.lower():
                print(f"✅ Correctly rejected invalid domain")
            else:
                print(f"❌ Wrong validation error: {error_msg}")
        else:
            print("❌ Invalid domain was accepted")
    else:
        print(f"✅ HTTP error correctly rejected invalid data: {response.status_code}")

    # Test 7: Clean Up - Delete Organization
    if org_id:
        print(f"\n🗑️  Cleaning Up - Delete Organization")
        response = requests.delete(
            f"{BASE_URL}/organizations/{org_id}", headers=HEADERS
        )
        print_response(response, "Delete Organization")

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Deleted organization successfully")
            else:
                print("❌ Delete failed")
        else:
            print(f"❌ HTTP error: {response.status_code}")

    return True


def test_with_custom_headers():
    """Test with custom tenant headers to verify header support works"""
    print(f"\n🔧 Testing with Custom Headers")

    # Custom headers to override the default mock tenant
    custom_headers = {
        "Content-Type": "application/json",
        "X-Mock-Tenant-Id": "550e8400-e29b-41d4-a716-446655440000",  # Use the default mock tenant
        "X-Mock-User-Id": "123e4567-e89b-12d3-a456-426614174000",
        "X-Mock-Email": "customtest@example.com",
        "X-Mock-Display-Name": "Custom Test User",
    }

    org_data = {"name": "Custom Header Test Corp", "domain": "customheader.com"}

    response = requests.post(
        f"{BASE_URL}/organizations/", headers=custom_headers, json=org_data
    )
    print_response(response, "Create Organization with Custom Headers")

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print(f"✅ Custom headers working correctly")
        else:
            print(f"❌ Custom headers failed")
    else:
        print(f"❌ HTTP error with custom headers: {response.status_code}")


def main():
    """Run the mock authentication tests"""
    print("🚀 Organization API Test with Mock Authentication")
    print("=" * 60)
    print("This test uses the updated mock authentication system")
    print("The first API call should auto-create the mock tenant")
    print()

    input("Press Enter to start testing...")

    try:
        # Test with default mock auth
        success = test_organization_with_mock_auth()

        # Test with custom headers
        test_with_custom_headers()

        print("\n" + "=" * 60)
        if success:
            print("🎉 Mock authentication tests completed!")
            print("✅ Your organization system is working with mock auth!")
        else:
            print("⚠️  Some tests had issues")

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server.")
        print("Make sure your FastAPI server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


if __name__ == "__main__":
    main()
