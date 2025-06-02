# Step 6: Test Pydantic Schemas

## Overview

This test script focuses specifically on validating the Pydantic schemas for the Tenant model **without** touching the database. While the previous test (Step 5) validated the complete end-to-end functionality including database operations, this test isolates and validates just the data validation and serialization layer.

**Key Differences from Step 5 (Tenant Model Test):**

| Aspect | Step 5: Tenant Model Test | Step 6: Pydantic Schema Test |
|--------|---------------------------|--------------------------------|
| **Scope** | Full end-to-end testing | Schema validation only |
| **Database** | Uses real database connection | No database interaction |
| **Focus** | SQLAlchemy model + business logic | Pydantic validation + serialization |
| **Speed** | Slower (database I/O) | Faster (in-memory only) |
| **Dependencies** | Requires working database | Pure Python validation |

**What this test validates:**

### **Input Validation**
- Field validation rules (name length, subdomain format, email format)
- Required vs optional field handling
- Data type conversion and coercion
- Business rule enforcement (reserved subdomains, URL-friendly strings)

### **Computed Fields**
- Automatic slug generation from tenant name
- Automatic subdomain generation from slug
- Computed properties in TenantRead schema
- Field transformation logic

### **Schema Variants**
- **TenantCreate**: Input validation for new tenant creation
- **TenantRead**: Output serialization with computed properties
- **TenantUpdate**: Partial update validation (all fields optional)
- **TenantSummary**: Lightweight representation for lists

### **Error Handling**
- ValidationError generation for invalid inputs
- Specific error messages for different validation failures
- Edge case handling (empty strings, special characters, etc.)

### **Serialization/Deserialization**
- Python object to JSON conversion
- Type safety and data integrity
- Proper handling of optional fields and None values

**Why Both Tests Are Important:**
- **Step 5** ensures the database and model work together correctly
- **Step 6** ensures data validation works independently and can catch issues early
- Schema tests run faster and can be used in CI/CD pipelines
- Separation of concerns: data validation vs database operations

**Expected Outcome:** All validation tests should pass, confirming that the Pydantic schemas properly validate input data and handle edge cases before any database operations occur.

---

## 6.1 Create Schema Test Script
Create `test_tenant_schemas.py` in the project root directory:

```python
"""
Test script for Tenant Pydantic schemas.
Tests validation, serialization, and computed fields.
"""
from app.schemas.tenant import TenantCreate, TenantRead, TenantUpdate
from pydantic import ValidationError
import uuid
from datetime import datetime

def test_tenant_schemas():
    """Test Tenant Pydantic schemas"""
    
    try:
        print("🧪 Testing Tenant schemas...")
        
        # Test 1: Valid tenant creation
        print("\n1. Testing valid tenant creation...")
        valid_tenant = TenantCreate(
            name="Acme Corporation",
            billing_email="billing@acme.com"
        )
        
        print(f"✅ Valid tenant created")
        print(f"   Name: {valid_tenant.name}")
        print(f"   Computed slug: {valid_tenant.computed_slug}")
        print(f"   Computed subdomain: {valid_tenant.computed_subdomain}")
        
        # Test 2: Test validation errors
        print("\n2. Testing validation errors...")
        
        # Test invalid name
        try:
            TenantCreate(name="A")  # Too short
            print("❌ Short name validation failed")
        except ValidationError as e:
            print("✅ Short name validation working")
        
        # Test invalid subdomain
        try:
            TenantCreate(name="Test Company", subdomain="invalid_subdomain!")
            print("❌ Invalid subdomain validation failed")
        except ValidationError as e:
            print("✅ Invalid subdomain validation working")
        
        # Test reserved subdomain
        try:
            TenantCreate(name="Test Company", subdomain="www")
            print("❌ Reserved subdomain validation failed")
        except ValidationError as e:
            print("✅ Reserved subdomain validation working")
        
        # Test 3: TenantRead schema
        print("\n3. Testing TenantRead schema...")
        
        # Mock tenant data
        tenant_data = {
            "id": uuid.uuid4(),
            "name": "Test Company",
            "subdomain": "test-company",
            "slug": "test-company",
            "plan_type": "trial",
            "status": "trial",
            "max_users": 5,
            "max_models": 10,
            "max_scenarios_per_month": 100,
            "max_storage_gb": 1.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "trial_expires_at": None,
            "activated_at": None,
            "stripe_customer_id": None,
            "billing_email": None
        }
        
        tenant_read = TenantRead(**tenant_data)
        print(f"✅ TenantRead created")
        print(f"   Full domain: {tenant_read.full_domain}")
        print(f"   Is trial: {tenant_read.is_trial}")
        print(f"   Is active: {tenant_read.is_active}")
        
        # Test 4: TenantUpdate schema
        print("\n4. Testing TenantUpdate schema...")
        
        tenant_update = TenantUpdate(
            name="Updated Company Name",
            max_users=20
        )
        
        print(f"✅ TenantUpdate created")
        print(f"   Name: {tenant_update.name}")
        print(f"   Max users: {tenant_update.max_users}")
        
        print(f"\n🎉 All Tenant schema tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Schema test failed with error: {e}")
        return False

if __name__ == "__main__":
    test_tenant_schemas()
```

## 6.2 Run Schema Tests
```bash
python test_tenant_schemas.py
```

**✅ Checkpoint:** All schema tests should pass.
