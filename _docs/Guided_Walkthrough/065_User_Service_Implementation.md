# Step 6.5: User Service Implementation

## Overview

The **UserService** demonstrates how services handle user-focused business operations beyond simple CRUD. This service manages user profiles, authentication coordination, and activity tracking while maintaining proper business logic separation.

Unlike the RegistrationService which coordinates multiple repositories, the UserService primarily works with the UserRepository but adds significant business logic for user management and authentication flows.

**What we'll implement:**
- UserService class for user-focused business operations
- Authentication coordination and session management
- User profile management with business rules
- Activity tracking and basic analytics
- Dependency injection for FastAPI integration

**Key Features:**
- ✅ **Authentication Coordination**: Handles login flows and session management
- ✅ **Profile Management**: User profile updates with validation
- ✅ **Activity Tracking**: Session tracking and engagement metrics
- ✅ **Business Rules**: User-specific validation and logic
- ✅ **Error Handling**: Comprehensive error recovery

---

## Step 1: Understanding User Service Responsibilities

### 1.1 Service vs Repository Division

```python
# Repository Layer - Data Access
class UserRepository:
    def get_by_identity_provider_id(self, db: Session, provider: str, provider_id: str) -> User:
        # Just finds user by identity provider
        return found_user
    
    def update_login_stats(self, db: Session, tenant_id: UUID, user_id: UUID) -> User:
        # Just updates login count and timestamp
        return updated_user

# Service Layer - Business Logic
class UserService:
    def authenticate_user(self, provider: str, provider_id: str) -> AuthenticationResult:
        # 1. Find user by identity provider
        # 2. Validate user status and tenant status
        # 3. Update login statistics
        # 4. Track authentication event
        # 5. Return comprehensive authentication result
```

### 1.2 User Service Responsibilities

**Authentication & Session Management**:
- Coordinate user authentication with identity providers
- Validate user and tenant status during login
- Track login statistics and authentication events
- Manage user session lifecycle

**Profile Management**:
- Handle user profile updates with business validation
- Manage user preferences and settings
- Handle profile metadata updates
- Coordinate profile changes with validation

---

## Step 2: Define User Service Schemas

### 2.1 Add Schemas to User Module

Add these schemas to your `app/schemas/user.py`:

```python
# Add these to your existing app/schemas/user.py file

class UserProfileUpdate(BaseModel):
    """Schema for updating user profile information."""
    display_name: Optional[str] = None
    user_metadata: Optional[str] = None  # JSON string for flexible metadata
    
    @field_validator('display_name')
    @classmethod
    def validate_display_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) < 2:
            raise ValueError("Display name must be at least 2 characters long")
        return v.strip() if v else None

class AuthenticationResult(BaseModel):
    """Result of user authentication process."""
    success: bool
    user: Optional[UserResponse] = None
    tenant: Optional[Dict[str, Any]] = None
    message: str
    requires_setup: bool = False

class UserActivitySummary(BaseModel):
    """Summary of user activity and engagement."""
    user_id: str
    total_logins: int
    total_usage_minutes: int
    last_login_at: Optional[datetime] = None
    days_since_registration: int
    is_recently_active: bool
    engagement_level: str  # "high", "medium", "low", "inactive"
```

---

## Step 3: Create Core User Service

### 3.1 Create User Service File

Create `app/services/user_service.py`:

```python
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone
from app.db.models.user import User
from app.repositories.user_repository import user_repo
from app.repositories.tenant_repository import tenant_repo
from app.schemas.user import (
    UserProfileUpdate, AuthenticationResult, UserResponse, 
    UserActivitySummary
)

class UserService:
    """
    Service for user-focused business operations.
    
    Handles user profile management, authentication coordination,
    and activity tracking while maintaining proper business logic
    separation from data access.
    
    Key Responsibilities:
    - Authentication coordination and validation
    - User profile management with business rules
    - Activity tracking and session management
    - User-specific business logic enforcement
    """
    
    def __init__(self, db: Session):
        """
        Initialize service with database session.
        
        Args:
            db: Database session for all operations
        """
        self.db = db
        self.user_repo = user_repo
        self.tenant_repo = tenant_repo
    
    # === Authentication & Session Management ===
    
    def authenticate_user(self, identity_provider: str, identity_provider_id: str) -> AuthenticationResult:
        """
        Authenticate user and return comprehensive authentication result.
        
        This method coordinates the complete authentication flow including
        user lookup, status validation, login tracking, and result preparation.
        
        Args:
            identity_provider: Provider name (e.g., "entra_id", "google")
            identity_provider_id: Unique ID from the provider
            
        Returns:
            AuthenticationResult with user data and authentication status
            
        Example:
            result = user_service.authenticate_user("entra_id", "12345")
            if result.success:
                user = result.user
                tenant = result.tenant
        """
        try:
            # Step 1: Find user by identity provider
            user = self.user_repo.get_by_identity_provider_id(
                self.db, identity_provider, identity_provider_id
            )
            
            if not user:
                return AuthenticationResult(
                    success=False,
                    message="User not found with provided identity information",
                    requires_setup=True
                )
            
            # Step 2: Validate user status
            if user.status != "active":
                return AuthenticationResult(
                    success=False,
                    message=f"User account is {user.status}. Please contact support.",
                    requires_setup=False
                )
            
            # Step 3: Validate tenant status
            tenant = self.tenant_repo.get_by_id(self.db, user.tenant_id)
            if not tenant or tenant.status not in ["active", "trial"]:
                return AuthenticationResult(
                    success=False,
                    message="Organization account is not active. Please contact support.",
                    requires_setup=False
                )
            
            # Step 4: Update login statistics
            self.user_repo.update_login_stats(self.db, user.tenant_id, user.id)
            
            # Step 5: Track activity
            self.user_repo.update_activity_timestamp(self.db, user.tenant_id, user.id)
            
            # Step 6: Commit authentication tracking
            self.db.commit()
            
            # Step 7: Prepare successful result
            user_response = UserResponse(
                id=user.id,
                email=user.email,
                display_name=user.display_name,
                status=user.status,
                login_count=user.login_count or 0,
                total_usage_minutes=getattr(user, 'total_usage_minutes', 0) or 0,
                last_login_at=user.last_login_at,
                last_active_at=getattr(user, 'last_active_at', None),
                created_at=user.created_at,
                updated_at=user.updated_at,
                tenant_id=user.tenant_id
            )
            
            return AuthenticationResult(
                success=True,
                user=user_response,
                tenant={
                    "id": str(tenant.id),
                    "name": tenant.name,
                    "slug": tenant.slug,
                    "subdomain": tenant.subdomain,
                    "status": tenant.status,
                    "plan_type": tenant.plan_type
                },
                message="Authentication successful",
                requires_setup=False
            )
            
        except Exception as e:
            # Rollback any changes on error
            self.db.rollback()
            return AuthenticationResult(
                success=False,
                message=f"Authentication failed: {str(e)}",
                requires_setup=False
            )
    
    def track_user_session(self, tenant_id: UUID, user_id: UUID, session_minutes: int) -> bool:
        """
        Track a user session and update engagement metrics.
        
        Args:
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to track
            session_minutes: Duration of the session in minutes
            
        Returns:
            True if tracking successful, False otherwise
        """
        try:
            # Update activity timestamp
            self.user_repo.update_activity_timestamp(self.db, tenant_id, user_id)
            
            # Add usage time
            self.user_repo.add_usage_time(self.db, tenant_id, user_id, session_minutes)
            
            # Commit changes
            self.db.commit()
            return True
            
        except Exception:
            self.db.rollback()
            return False
    
    # === Profile Management ===
    
    def get_user_profile(self, tenant_id: UUID, user_id: UUID) -> Optional[UserResponse]:
        """
        Get complete user profile with business logic applied.
        
        Args:
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to retrieve
            
        Returns:
            UserResponse with complete profile or None if not found
        """
        user = self.user_repo.get_by_id(self.db, tenant_id, user_id)
        if not user:
            return None
        
        return UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            status=user.status,
            login_count=user.login_count or 0,
            total_usage_minutes=getattr(user, 'total_usage_minutes', 0) or 0,
            last_login_at=user.last_login_at,
            last_active_at=getattr(user, 'last_active_at', None),
            created_at=user.created_at,
            updated_at=user.updated_at,
            tenant_id=user.tenant_id
        )
    
    def update_user_profile(self, tenant_id: UUID, user_id: UUID, 
                           profile_update: UserProfileUpdate) -> Optional[UserResponse]:
        """
        Update user profile with business validation.
        
        Args:
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to update
            profile_update: Profile update data
            
        Returns:
            Updated UserResponse or None if user not found
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Get current user
            user = self.user_repo.get_by_id(self.db, tenant_id, user_id)
            if not user:
                return None
            
            # Prepare update data
            update_data = {}
            
            if profile_update.display_name is not None:
                update_data["display_name"] = profile_update.display_name
            
            if profile_update.user_metadata is not None:
                # Validate JSON metadata if provided
                if profile_update.user_metadata:
                    try:
                        import json
                        json.loads(profile_update.user_metadata)  # Validate JSON
                    except json.JSONDecodeError:
                        raise ValueError("User metadata must be valid JSON")
                
                update_data["user_metadata"] = profile_update.user_metadata
            
            # Update user
            updated_user = self.user_repo.update(self.db, db_obj=user, obj_in=update_data)
            
            # Commit changes
            self.db.commit()
            
            # Return updated profile
            return self.get_user_profile(tenant_id, user_id)
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def deactivate_user(self, tenant_id: UUID, user_id: UUID, reason: str = "deactivated") -> bool:
        """
        Deactivate a user account with business logic.
        
        Args:
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to deactivate
            reason: Reason for deactivation
            
        Returns:
            True if deactivation successful, False if user not found
        """
        try:
            user = self.user_repo.get_by_id(self.db, tenant_id, user_id)
            if not user:
                return False
            
            # Update user status
            update_data = {
                "status": "inactive",
                "user_metadata": f'{{"deactivation_reason": "{reason}", "deactivated_at": "{datetime.now(timezone.utc).isoformat()}"}}'
            }
            
            self.user_repo.update(self.db, db_obj=user, obj_in=update_data)
            self.db.commit()
            
            return True
            
        except Exception:
            self.db.rollback()
            return False
    
    # === Basic Analytics ===
    
    def get_user_activity_summary(self, tenant_id: UUID, user_id: UUID) -> Optional[UserActivitySummary]:
        """
        Get basic user activity summary.
        
        Args:
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to analyze
            
        Returns:
            UserActivitySummary with engagement metrics or None if not found
        """
        stats = self.user_repo.get_user_statistics(self.db, tenant_id, user_id)
        if not stats:
            return None
        
        # Determine engagement level
        engagement_level = self._calculate_engagement_level(stats)
        
        return UserActivitySummary(
            user_id=str(user_id),
            total_logins=stats["login_count"],
            total_usage_minutes=stats["total_usage_minutes"],
            last_login_at=None,  # Would need to parse from stats if available
            days_since_registration=stats["days_since_registration"],
            is_recently_active=stats["is_recently_active"],
            engagement_level=engagement_level
        )
    
    def _calculate_engagement_level(self, user_stats: Dict[str, Any]) -> str:
        """
        Calculate user engagement level based on activity metrics.
        
        Args:
            user_stats: User statistics dictionary
            
        Returns:
            Engagement level: "high", "medium", "low", or "inactive"
        """
        login_count = user_stats.get("login_count", 0)
        total_usage = user_stats.get("total_usage_minutes", 0)
        days_since_registration = user_stats.get("days_since_registration", 0)
        is_recently_active = user_stats.get("is_recently_active", False)
        
        if not is_recently_active:
            return "inactive"
        
        # Calculate engagement score
        if days_since_registration > 0:
            avg_logins_per_day = login_count / days_since_registration
            avg_usage_per_day = total_usage / days_since_registration
        else:
            avg_logins_per_day = login_count
            avg_usage_per_day = total_usage
        
        if avg_logins_per_day >= 1 and avg_usage_per_day >= 30:
            return "high"
        elif avg_logins_per_day >= 0.3 and avg_usage_per_day >= 10:
            return "medium"
        else:
            return "low"


# Dependency injection helper for FastAPI
def get_user_service(db: Session) -> UserService:
    """
    Dependency injection helper for FastAPI endpoints.
    
    Usage in FastAPI:
        @router.get("/profile")
        async def get_profile(
            current_user: User = Depends(get_current_user),
            user_service: UserService = Depends(get_user_service)
        ):
            profile = user_service.get_user_profile(current_user.tenant_id, current_user.id)
            return profile
    """
    return UserService(db)
```

### 3.2 Update Services Package Init

Update `app/services/__init__.py`:

```python
"""
Service layer for business logic coordination.

This package contains services that orchestrate multiple repository
operations, manage transaction boundaries, and implement complex
business logic.
"""

from .registration_service import RegistrationService, get_registration_service
from .user_service import UserService, get_user_service

__all__ = [
    "RegistrationService", "get_registration_service",
    "UserService", "get_user_service"
]
```

---

## Step 4: Basic Testing

### 4.1 Create Basic User Service Test

Create `test_user_service_basic.py` in your project root:

```python
from app.services.user_service import UserService
from app.services.registration_service import RegistrationService
from app.schemas.user import UserRegistration, UserProfileUpdate
from app.db.session import SessionLocal
from uuid import uuid4

def test_user_service_basic():
    """Test basic UserService functionality"""
    
    db = SessionLocal()
    
    try:
        print("🧪 Testing UserService - Basic Functions...")
        
        # Setup: Create a test user and tenant
        registration_service = RegistrationService(db)
        user_service = UserService(db)
        
        registration_data = UserRegistration(
            email="testuser@userservice.com",
            display_name="Test User",
            identity_provider="local_dev_registration",
            identity_provider_id=f"test-user-service-{uuid4()}",
            company_name="User Service Test Company"
        )
        
        tenant, user = registration_service.register_user_and_tenant(registration_data)
        print(f"✅ Setup: Created user {user.email} in tenant {tenant.name}")
        
        # Test 1: Authentication
        print("\n--- Test 1: User Authentication ---")
        auth_result = user_service.authenticate_user(
            registration_data.identity_provider,
            registration_data.identity_provider_id
        )
        
        assert auth_result.success == True, "Authentication should succeed"
        assert auth_result.user is not None, "Should return user data"
        assert auth_result.tenant is not None, "Should return tenant data"
        print(f"✅ Authentication successful: {auth_result.message}")
        
        # Test 2: Get User Profile
        print("\n--- Test 2: User Profile ---")
        profile = user_service.get_user_profile(tenant.id, user.id)
        
        assert profile is not None, "Should return user profile"
        assert profile.email == user.email, "Should return correct user data"
        assert profile.login_count >= 1, "Should show login count from authentication"
        print(f"✅ Profile retrieved: {profile.display_name}")
        
        # Test 3: Update Profile
        print("\n--- Test 3: Profile Update ---")
        profile_update = UserProfileUpdate(
            display_name="Updated Test User",
            user_metadata='{"theme": "dark"}'
        )
        
        updated_profile = user_service.update_user_profile(
            tenant.id, user.id, profile_update
        )
        
        assert updated_profile.display_name == "Updated Test User", "Should update display name"
        print(f"✅ Profile updated: {updated_profile.display_name}")
        
        # Test 4: Session Tracking
        print("\n--- Test 4: Session Tracking ---")
        session_tracked = user_service.track_user_session(tenant.id, user.id, 30)
        
        assert session_tracked == True, "Should successfully track session"
        print("✅ Session tracking works")
        
        # Test 5: Activity Summary
        print("\n--- Test 5: Activity Summary ---")
        activity_summary = user_service.get_user_activity_summary(tenant.id, user.id)
        
        assert activity_summary is not None, "Should return activity summary"
        assert activity_summary.engagement_level in ["high", "medium", "low", "inactive"], "Should calculate engagement"
        print(f"✅ Activity summary: {activity_summary.engagement_level} engagement")
        
        # Clean up
        from app.repositories.user_repository import user_repo
        from app.repositories.tenant_repository import tenant_repo
        
        user_repo.soft_delete(db, tenant.id, user.id)
        tenant_repo.soft_delete(db, tenant.id, tenant.id)
        db.commit()
        print("✅ Cleaned up test data")
        
        print("\n🎉 UserService basic tests passed!")
        
    except Exception as e:
        print(f"❌ UserService test failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_user_service_basic()
```

### 4.2 Run Basic Test

```bash
# Navigate to your project directory
cd C:\_source\Greenshoes\Summer2025Internship\Sprint2\Guided_Walkthrough\quodsi_api

# Activate virtual environment
.\venv\Scripts\activate

# Run the test
python test_user_service_basic.py
```

---

## Step 5: Understanding Core Service Features

### 5.1 Authentication Coordination

**Complete Authentication Flow**:
```python
def authenticate_user(self, identity_provider: str, identity_provider_id: str):
    # 1. Find user by identity provider (repository)
    # 2. Validate user status (business logic)
    # 3. Validate tenant status (business logic)
    # 4. Update login statistics (repository + business logic)
    # 5. Track activity (repository)
    # 6. Commit transaction (service responsibility)
    # 7. Prepare comprehensive result (business logic)
```

### 5.2 Profile Management with Validation

**Business Logic in Profile Updates**:
```python
def update_user_profile(self, tenant_id: UUID, user_id: UUID, profile_update: UserProfileUpdate):
    # 1. Validate JSON metadata format
    # 2. Apply business rules to display name
    # 3. Update user via repository
    # 4. Commit changes
    # 5. Return updated profile
```

### 5.3 Session and Activity Tracking

**Coordinated Activity Tracking**:
```python
def track_user_session(self, tenant_id: UUID, user_id: UUID, session_minutes: int):
    # 1. Update activity timestamp
    # 2. Add usage time
    # 3. Commit both updates in single transaction
```

---

## Common Issues and Solutions

### Issue 1: Authentication State Management
**Problem**: Authentication updates not persisting
**Solution**: Ensure commit() is called after all authentication tracking

### Issue 2: Profile Update Validation
**Problem**: Invalid JSON metadata not caught
**Solution**: Validate JSON in service layer before repository update

### Issue 3: Session Tracking Failures
**Problem**: Partial session updates when errors occur
**Solution**: Use try/catch with rollback in service methods

---

## Verification Checklist

After completing this step, verify:

- [ ] `app/services/user_service.py` exists with core implementation
- [ ] Authentication coordination works with proper validation
- [ ] Profile management includes business validation
- [ ] Session tracking updates multiple fields in single transaction
- [ ] Activity summary calculation works
- [ ] Basic test script runs successfully
- [ ] Service is exported in `__init__.py`
- [ ] Dependency injection helper function works

## Next Steps

Continue with **065a_User_Service_Analytics_and_Testing.md** for:
- Advanced user analytics and insights
- Tenant-level user management features
- Comprehensive testing with complex scenarios
- Performance considerations for analytics
- Usage patterns and FastAPI integration examples

## Key Takeaways

1. **Services coordinate business logic** beyond simple data access
2. **Authentication flows** require multiple validation steps and tracking
3. **Profile management** needs business rules and validation
4. **Session tracking** benefits from transactional coordination
5. **Activity summaries** provide valuable user engagement insights
6. **Error handling** must include proper rollback for data consistency
7. **Dependency injection** makes services easy to test and use in FastAPI
