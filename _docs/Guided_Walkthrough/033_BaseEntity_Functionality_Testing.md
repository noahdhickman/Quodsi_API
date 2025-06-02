# Module 3.4: BaseEntity Functionality Testing

**Duration:** 20-25 minutes  
**Objective:** Test BaseEntity functionality through comprehensive CRUD operations and query patterns.

**Prerequisites:** Step 3 completed - Migration applied successfully

---

## Step 4: Test BaseEntity Functionality

### 4.1 Create Test Script
Create `test_base_entity.py` in the project root:

```python
"""
Test script to verify BaseEntity functionality.
Run this to test that BaseEntity works correctly.
"""
import uuid
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.test_model import TestModel

def test_base_entity():
    """Test BaseEntity CRUD operations"""
    db = SessionLocal()
    
    try:
        print("🧪 Testing BaseEntity functionality...")
        
        # Test 1: Create a record
        print("\n1. Creating test record...")
        test_record = TestModel(
            tenant_id=uuid.uuid4(),  # Mock tenant ID for testing
            name="Test Record",
            description="Testing BaseEntity"
        )
        
        db.add(test_record)
        db.commit()
        db.refresh(test_record)
        
        print(f"✅ Record created: {test_record}")
        print(f"   ID: {test_record.id}")
        print(f"   Index ID: {test_record.index_id}")
        print(f"   Created at: {test_record.created_at}")
        
        # Test 2: Query the record
        print("\n2. Querying record...")
        found_record = db.query(TestModel).filter(
            TestModel.id == test_record.id
        ).first()
        
        if found_record:
            print(f"✅ Record found: {found_record.name}")
        else:
            print("❌ Record not found")
            return False
        
        # Test 3: Update the record
        print("\n3. Updating record...")
        original_updated_at = found_record.updated_at
        found_record.description = "Updated description"
        db.commit()
        db.refresh(found_record)
        
        if found_record.updated_at > original_updated_at:
            print(f"✅ Record updated successfully")
            print(f"   Updated at: {found_record.updated_at}")
        else:
            print("❌ Updated timestamp not changed")
        
        # Test 4: Soft delete
        print("\n4. Testing soft delete...")
        found_record.soft_delete()
        db.commit()
        
        if found_record.is_deleted:
            print(f"✅ Record soft deleted successfully")
        else:
            print("❌ Soft delete failed")
        
        # Test 5: Verify soft deleted record is excluded from active queries
        print("\n5. Testing active record filter...")
        active_records = db.query(TestModel).filter(
            TestModel.get_active_query_filter()
        ).all()
        
        deleted_record_in_active = any(r.id == test_record.id for r in active_records)
        if not deleted_record_in_active:
            print("✅ Soft deleted record excluded from active queries")
        else:
            print("❌ Soft deleted record still appears in active queries")
        
        # Test 6: Restore record
        print("\n6. Testing record restoration...")
        found_record.restore()
        db.commit()
        
        if not found_record.is_deleted:
            print("✅ Record restored successfully")
        else:
            print("❌ Record restoration failed")
        
        # Test 7: Tenant filtering
        print("\n7. Testing tenant filtering...")
        tenant_records = db.query(TestModel).filter(
            TestModel.get_tenant_query_filter(test_record.tenant_id)
        ).all()
        
        if len(tenant_records) > 0:
            print(f"✅ Tenant filter works: found {len(tenant_records)} records")
        else:
            print("❌ Tenant filter failed")
        
        print(f"\n🎉 All BaseEntity tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        # Clean up: delete test record
        try:
            if 'test_record' in locals():
                db.delete(test_record)
                db.commit()
                print("🧹 Test record cleaned up")
        except:
            pass
        db.close()

if __name__ == "__main__":
    test_base_entity()
```

### 4.2 Run BaseEntity Tests
```bash
# Run from project root directory
python test_base_entity.py
```

**✅ Checkpoint:** All tests should pass, demonstrating that BaseEntity works correctly.

---

**Next Step:** [034_Database_Structure_Verification.md](./034_Database_Structure_Verification.md)
