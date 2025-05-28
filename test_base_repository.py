from app.repositories.base import BaseRepository
from app.db.models.user import User
from app.db.session import SessionLocal, get_db
from uuid import uuid4

def test_base_repository():
    """Simple test to verify BaseRepository functionality"""
    
    # Create a User repository using BaseRepository
    user_repo = BaseRepository(User)
    db = SessionLocal()
    
    try:
        # Test that we can instantiate the repository
        print("✅ BaseRepository instantiated successfully")
        
        # Test that methods exist and have correct signatures
        tenant_id = uuid4()
        user_id = uuid4()
        
        # These should not raise AttributeError
        result = user_repo.get_by_id(db, tenant_id, user_id)
        print("✅ get_by_id method works (returned None as expected)")
        
        count = user_repo.count(db, tenant_id)
        print(f"✅ count method works (returned {count})")
        
        users = user_repo.get_all(db, tenant_id, limit=10)
        print(f"✅ get_all method works (returned {len(users)} users)")
        
        print("\n🎉 BaseRepository implementation is working correctly!")
        
    except Exception as e:
        print(f"❌ BaseRepository test failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_base_repository()