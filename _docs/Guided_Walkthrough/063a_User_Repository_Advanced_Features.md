# Step 6.3a: User Repository Advanced Features

## Overview

This document continues from **063_User_Repository_Implementation.md** and adds advanced features to the UserRepository including comprehensive analytics, usage tracking, tenant-level summaries, and relationship management.

**Advanced Features:**
- Usage time tracking and analytics
- User statistics and engagement metrics
- Tenant-level user summaries
- Recently active user queries
- User-tenant relationship support
- Comprehensive testing suite

**Prerequisites:**
- Completed **063_User_Repository_Implementation.md**
- Basic UserRepository implemented and tested

---

## Step 1: Add Advanced Analytics Methods

### 1.1 Extend User Repository with Analytics

Add these methods to your existing `app/repositories/user_repository.py` file:

```python
# Add these methods to the existing UserRepository class

    def count_users_by_status(self, db: Session, tenant_id: UUID, status: str) -> int:
        """
        Count users by status within a tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            status: User status to count

        Returns:
            Number of users with the specified status
        """
        return (
            db.query(User)
            .filter(
                and_(
                    User.tenant_id == tenant_id,
                    User.status == status,
                    User.is_deleted == False,
                )
            )
            .count()
        )

    # === Advanced Activity Tracking ===
    
    def add_usage_time(self, db: Session, tenant_id: UUID, user_id: UUID, minutes: int) -> Optional[User]:
        """
        Add usage time to user's total usage statistics.
        
        Used for tracking user engagement and potentially for billing.
        """
        user = self.get_by_id(db, tenant_id, user_id)
        if user:
            user.total_usage_minutes = (user.total_usage_minutes or 0) + minutes
            user.updated_at = datetime.now(timezone.utc)
            db.add(user)
            db.flush()
            db.refresh(user)
        return user
    
    def get_user_statistics(self, db: Session, tenant_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Get comprehensive statistics for a specific user."""
        user = self.get_by_id(db, tenant_id, user_id)
        if not user:
            return {}
        
        now = datetime.now(timezone.utc)
        
        # Handle timezone-aware/naive datetime comparison
        created_at = user.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        days_since_registration = (now - created_at).days
        
        days_since_last_login = None
        if user.last_login_at:
            last_login = user.last_login_at
            if last_login.tzinfo is None:
                last_login = last_login.replace(tzinfo=timezone.utc)
            days_since_last_login = (now - last_login).days
        
        return {
            "user_id": str(user.id),
            "login_count": user.login_count or 0,
            "total_usage_minutes": getattr(user, 'total_usage_minutes', 0) or 0,
            "days_since_registration": days_since_registration,
            "days_since_last_login": days_since_last_login,
            "status": user.status,
            "identity_provider": user.identity_provider
        }
    
    def get_tenant_user_summary(self, db: Session, tenant_id: UUID) -> Dict[str, Any]:
        """Get summary statistics for all users in a tenant."""
        active_count = self.count_users_by_status(db, tenant_id, "active")
        inactive_count = self.count_users_by_status(db, tenant_id, "inactive") 
        suspended_count = self.count_users_by_status(db, tenant_id, "suspended")
        
        return {
            "total_users": active_count + inactive_count + suspended_count,
            "active_users": active_count,
            "inactive_users": inactive_count,
            "suspended_users": suspended_count
        }
```

---

## Step 2: Comprehensive Testing

### 2.1 Create Advanced Test Suite

Create `test_user_repository_advanced.py` in your project root:

```python
from app.repositories.user_repository import user_repo
from app.repositories.tenant_repository import tenant_repo
from app.schemas.user import UserCreate
from app.schemas.tenant import TenantCreate
from app.db.session import SessionLocal

def test_user_repository_advanced():
    """Test advanced UserRepository functionality"""
    
    db = SessionLocal()
    
    try:
        print("🧪 Testing UserRepository - Advanced Features...")
        
        # Create a test tenant
        tenant_data = TenantCreate(
            name="Advanced Test Company",
            plan_type="trial",
            status="trial"
        )
        test_tenant = tenant_repo.create(db, obj_in=tenant_data)
        print(f"✅ Created test tenant: {test_tenant.name}")
        
        # Create multiple test users
        users = []
        for i in range(3):
            user_data = UserCreate(
                email=f"user{i}@advanced-test.com",
                display_name=f"Advanced User {i}",
                identity_provider="local_dev_registration",
                identity_provider_id=f"advanced-user-{i}"
            )
            
            new_user = user_repo.create_user_for_tenant(
                db, obj_in=user_data, tenant_id=test_tenant.id
            )
            users.append(new_user)
            print(f"✅ Created user {i+1}: {new_user.email}")
        
        # Test usage time tracking
        user_repo.add_usage_time(db, test_tenant.id, users[0].id, 45)
        user_repo.add_usage_time(db, test_tenant.id, users[1].id, 30)
        print("✅ Added usage time to users")
        
        # Test activity tracking
        user_repo.update_activity_timestamp(db, test_tenant.id, users[0].id)
        user_repo.update_activity_timestamp(db, test_tenant.id, users[1].id)
        print("✅ Updated activity timestamps")
        
        # Test login stats for multiple users
        for user in users[:2]:  # First 2 users
            user_repo.update_login_stats(db, test_tenant.id, user.id)
        print("✅ Updated login stats")
        
        # Test user statistics
        stats = user_repo.get_user_statistics(db, test_tenant.id, users[0].id)
        assert "login_count" in stats, "Should include login count"
        assert stats["total_usage_minutes"] == 45, "Should show 45 minutes usage"
        print(f"✅ User statistics: {stats['login_count']} logins, {stats['total_usage_minutes']} minutes")
        
        # Test tenant user summary
        summary = user_repo.get_tenant_user_summary(db, test_tenant.id)
        assert summary["total_users"] == 3, "Should show 3 total users"
        assert summary["active_users"] == 3, "Should show 3 active users"
        print(f"✅ Tenant summary: {summary['total_users']} users, {summary['active_users']} active")
        
        # Test users by status counts
        active_count = user_repo.count_users_by_status(db, test_tenant.id, "active")
        assert active_count == 3, "Should count 3 active users"
        print(f"✅ Status counts: {active_count} active users")
        
        # Clean up
        for user in users:
            user_repo.soft_delete(db, test_tenant.id, user.id)
        tenant_repo.soft_delete(db, test_tenant.id, test_tenant.id)
        db.commit()
        print("✅ Cleaned up test data")
        
        print("\n🎉 UserRepository advanced tests passed!")
        
    except Exception as e:
        print(f"❌ UserRepository advanced test failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_user_repository_advanced()
```

### 2.2 Run Advanced Tests

```bash
# Navigate to your project directory
cd C:\_source\Greenshoes\Summer2025Internship\Sprint2\Guided_Walkthrough\quodsi_api

# Activate virtual environment
.\venv\Scripts\activate

# Run the advanced test
python test_user_repository_advanced.py
```

---

## Step 3: Usage Patterns and Examples

### 3.1 Analytics Dashboard Usage

```python
# Example: Building a tenant analytics dashboard
def get_tenant_dashboard_data(db: Session, tenant_id: UUID):
    """Get comprehensive data for tenant dashboard"""
    
    # Get overall tenant user summary
    user_summary = user_repo.get_tenant_user_summary(db, tenant_id)
    
    # Get recently active users
    recent_users = user_repo.get_users_by_status(db, tenant_id, "active", limit=10)
    
    return {
        "user_summary": user_summary,
        "recent_users": [{
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "last_login": user.last_login_at
        } for user in recent_users]
    }
```

### 3.2 User Profile with Statistics

```python
# Example: Complete user profile with analytics
def get_user_profile_with_stats(db: Session, tenant_id: UUID, user_id: UUID):
    """Get user profile with comprehensive statistics"""
    
    # Get user data
    user = user_repo.get_by_id(db, tenant_id, user_id)
    if not user:
        return None
    
    # Get detailed statistics
    stats = user_repo.get_user_statistics(db, tenant_id, user_id)
    
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "status": user.status,
            "created_at": user.created_at
        },
        "statistics": stats
    }
```

---

## Step 4: Performance Considerations

### 4.1 Query Optimization Tips

**Batch Operations**:
```python
# Instead of updating users one by one:
for user_id in user_ids:
    user_repo.update_activity_timestamp(db, tenant_id, user_id)

# Consider bulk updates for better performance:
db.query(User).filter(
    User.tenant_id == tenant_id,
    User.id.in_(user_ids)
).update({
    User.last_active_at: datetime.now(timezone.utc),
    User.updated_at: datetime.now(timezone.utc)
})
db.commit()
```

**Limit Large Queries**:
```python
# Always use reasonable limits for analytics queries
users = user_repo.get_users_by_status(
    db, tenant_id, "active", limit=1000  # Prevent excessive memory usage
)
```

---

## Common Issues and Solutions

### Issue 1: Timezone-aware/naive DateTime Comparison Error
**Problem**: `TypeError: can't subtract offset-naive and offset-aware datetimes` when calculating date differences
**Solution**: Ensure datetime objects have consistent timezone information before comparison:
```python
# Handle timezone-aware/naive datetime comparison
created_at = user.created_at
if created_at.tzinfo is None:
    created_at = created_at.replace(tzinfo=timezone.utc)
days_since_registration = (now - created_at).days
```

### Issue 2: Missing total_usage_minutes Field
**Problem**: Some queries fail because User model doesn't have total_usage_minutes
**Solution**: Add the field to your User model or handle gracefully with getattr() checks

### Issue 3: Performance Issues with Large Tenants
**Problem**: Analytics queries are slow for tenants with many users
**Solution**: Use pagination, implement caching, or run analytics as background tasks

### Issue 4: Memory Usage with Statistics
**Problem**: Large result sets consume too much memory
**Solution**: Use streaming queries, pagination, and reasonable limits

---

## Verification Checklist

After completing this step, verify:

- [ ] Advanced analytics methods added to UserRepository
- [ ] Usage time tracking works correctly
- [ ] User statistics calculation works
- [ ] Tenant-level user summaries work
- [ ] Advanced test suite runs successfully
- [ ] Performance considerations understood
- [ ] Proper error handling for optional features

## Next Steps

With the complete UserRepository implemented, you now have:

1. **Complete User Data Access** - All CRUD operations plus user-specific methods
2. **Authentication Integration** - Identity provider support for multiple auth systems
3. **Activity Tracking** - Login statistics and user engagement metrics
4. **Advanced Analytics** - Comprehensive user and tenant statistics
5. **Performance Optimization** - Efficient queries with proper indexing

In **064_Registration_Service_Implementation.md**, we'll create the RegistrationService that coordinates user and tenant creation in a single transaction, demonstrating how services orchestrate multiple repository operations while maintaining data consistency.

## Key Takeaways

1. **Advanced analytics** provide valuable insights for dashboards and decision-making
2. **Usage tracking** enables engagement analysis and potential billing features
3. **Performance considerations** are crucial for analytics queries with large datasets
4. **Error handling** should gracefully handle optional features and missing fields
5. **Tenant-level summaries** provide organizational insights for admin dashboards
6. **Batch operations** improve performance for bulk updates
7. **Testing** should cover both success and edge cases for complex analytics
