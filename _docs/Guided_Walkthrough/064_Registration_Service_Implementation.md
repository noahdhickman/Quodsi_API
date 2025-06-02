# Step 6.4: Registration Service Implementation

## Overview

The **RegistrationService** demonstrates how the Service Layer pattern coordinates multiple repository operations to implement complex business logic. This service handles the complete user and tenant registration process in a single, transactionally-safe operation.

This implementation shows how services orchestrate multiple repositories, manage transaction boundaries, handle business validation, and provide rollback capabilities when errors occur.

**What we'll implement:**
- RegistrationService class coordinating tenant and user creation
- Transaction management with commit/rollback logic
- Business validation and error handling
- Registration data validation and preprocessing
- Comprehensive testing with error scenarios

**Key Features:**
- ✅ **Multi-Repository Coordination**: Orchestrates TenantRepository and UserRepository
- ✅ **Transaction Management**: Proper commit/rollback boundaries
- ✅ **Business Logic**: Validates registration data and enforces rules
- ✅ **Error Handling**: Comprehensive error recovery and meaningful messages
- ✅ **Data Consistency**: Ensures both tenant and user are created or neither is created

---

## Step 1: Understanding Service Layer Responsibilities

### 1.1 Service vs Repository Responsibilities

```python
# Repository Layer - Data Access Only
class UserRepository:
    def create_user_for_tenant(self, db: Session, obj_in: UserCreate, tenant_id: UUID) -> User:
        # Just creates user, no business logic
        return self.create(db, obj_in=user_data, tenant_id=tenant_id)

class TenantRepository:
    def create(self, db: Session, obj_in: TenantCreate) -> Tenant:
        # Just creates tenant, no business logic
        return created_tenant

# Service Layer - Business Logic Coordination
class RegistrationService:
    def register_user_and_tenant(self, registration_data: UserRegistration):
        # 1. Validates business rules
        # 2. Coordinates multiple repositories
        # 3. Manages transactions
        # 4. Handles errors and rollback
        # 5. Returns complete result
```

### 1.2 Transaction Coordination Pattern

**Single Transaction for Multiple Operations**:
```python
# Service manages the transaction boundary
try:
    # Step 1: Create tenant (using tenant repository)
    tenant = tenant_repo.create(db, tenant_data)
    
    # Step 2: Create user for that tenant (using user repository)
    user = user_repo.create_user_for_tenant(db, user_data, tenant.id)
    
    # Step 3: Commit transaction (all or nothing)
    db.commit()
    
    return tenant, user
except Exception:
    # Step 4: Rollback on any error
    db.rollback()
    raise
```

---

## Step 2: Create Registration Service

### 2.1 Define Registration Schema

First, let's ensure we have the registration schema. Add this to your `app/schemas/user.py`:

```python
# Add this to your existing app/schemas/user.py file

class UserRegistration(BaseModel):
    """
    Schema for user registration that includes both user and tenant information.
    
    This schema is used when a user signs up and creates a new organization.
    """
    email: EmailStr
    display_name: str
    identity_provider: str = "local_dev_registration"
    identity_provider_id: Optional[str] = None
    
    # Tenant/Organization information
    company_name: str
    tenant_slug: Optional[str] = None  # Auto-generated if not provided
    
    @field_validator('company_name')
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError("Company name must be at least 2 characters long")
        return v.strip()
    
    @field_validator('tenant_slug', mode='before')
    @classmethod
    def validate_tenant_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Basic slug validation
        import re
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Tenant slug may only contain lowercase letters, numbers, and hyphens")
        return v
```

### 2.2 Create Registration Service

Create `app/services/registration_service.py`:

```python
from sqlalchemy.orm import Session
from typing import Tuple, Dict, Any
from uuid import UUID
from app.db.models.user import User
from app.db.models.tenant import Tenant
from app.repositories.tenant_repository import tenant_repo
from app.repositories.user_repository import user_repo
from app.schemas.user import UserRegistration
from app.schemas.tenant import TenantCreate
from app.schemas.user import UserCreate

class RegistrationService:
    """
    Service for handling user and tenant registration.
    
    Coordinates the creation of both tenant and initial admin user
    in a single transaction to ensure data consistency.
    
    Key Responsibilities:
    - Validate registration data
    - Create tenant organization
    - Create initial admin user
    - Manage transaction boundaries
    - Handle errors and rollbacks
    """
    
    def __init__(self, db: Session):
        """
        Initialize service with database session.
        
        Args:
            db: Database session for all operations
        """
        self.db = db
        self.tenant_repo = tenant_repo
        self.user_repo = user_repo
    
    def register_user_and_tenant(self, registration_data: UserRegistration) -> Tuple[Tenant, User]:
        """
        Register a new user and create their tenant organization.
        
        This is the main registration flow where a user creates both
        their account and their organization in a single operation.
        
        Args:
            registration_data: User registration information including company details
            
        Returns:
            Tuple of (created_tenant, created_user)
            
        Raises:
            ValueError: If validation fails or conflicts exist
            Exception: For database errors (triggers rollback)
            
        Example:
            registration = UserRegistration(
                email="admin@newcompany.com",
                display_name="Admin User",
                company_name="New Company Inc",
                identity_provider="entra_id",
                identity_provider_id="12345"
            )
            tenant, user = registration_service.register_user_and_tenant(registration)
        """
        try:
            # Step 1: Validate registration data
            self._validate_registration_data(registration_data)
            
            # Step 2: Create tenant first
            tenant = self._create_tenant_from_registration(registration_data)
            
            # Step 3: Create user for the tenant
            user = self._create_user_from_registration(registration_data, tenant.id)
            
            # Step 4: Commit the transaction
            self.db.commit()
            
            return tenant, user
            
        except Exception as e:
            # Step 5: Rollback on any error
            self.db.rollback()
            raise e
    
    def _validate_registration_data(self, registration_data: UserRegistration) -> None:
        """
        Validate registration data for business rules.
        
        Args:
            registration_data: Registration data to validate
            
        Raises:
            ValueError: If validation fails
        """
        # Check if user with this identity already exists
        existing_user = self.user_repo.get_by_identity_provider_id(
            self.db,
            registration_data.identity_provider,
            registration_data.identity_provider_id or registration_data.email
        )
        
        if existing_user:
            raise ValueError(
                f"User with identity provider {registration_data.identity_provider} "
                f"and ID {registration_data.identity_provider_id or registration_data.email} already exists"
            )
        
        # Check tenant slug availability if provided
        if registration_data.tenant_slug:
            if not self.tenant_repo.check_slug_availability(self.db, registration_data.tenant_slug):
                raise ValueError(f"Tenant slug '{registration_data.tenant_slug}' is already taken")
            
            if not self.tenant_repo.check_subdomain_availability(self.db, registration_data.tenant_slug):
                raise ValueError(f"Subdomain '{registration_data.tenant_slug}' is already taken")
    
    def _create_tenant_from_registration(self, registration_data: UserRegistration) -> Tenant:
        """
        Create tenant from registration data.
        
        Args:
            registration_data: Registration data containing tenant info
            
        Returns:
            Created tenant instance
        """
        tenant_create_data = TenantCreate(
            name=registration_data.company_name,
            slug=registration_data.tenant_slug,  # May be None - will be auto-generated
            subdomain=registration_data.tenant_slug,  # May be None - will be auto-generated
            plan_type="trial",
            status="trial"
        )
        
        return self.tenant_repo.create(self.db, obj_in=tenant_create_data)
    
    def _create_user_from_registration(self, registration_data: UserRegistration, tenant_id: UUID) -> User:
        """
        Create user from registration data for specific tenant.
        
        Args:
            registration_data: Registration data containing user info
            tenant_id: ID of the tenant to create user for
            
        Returns:
            Created user instance
        """
        user_create_data = UserCreate(
            email=registration_data.email,
            display_name=registration_data.display_name,
            identity_provider=registration_data.identity_provider,
            identity_provider_id=registration_data.identity_provider_id or registration_data.email
        )
        
        return self.user_repo.create_user_for_tenant(
            self.db,
            obj_in=user_create_data,
            tenant_id=tenant_id
        )
    
    def validate_registration_availability(self, registration_data: UserRegistration) -> Dict[str, Any]:
        """
        Validate registration data and return availability information.
        
        This method allows checking availability without actually creating
        the tenant and user, useful for form validation in the UI.
        
        Args:
            registration_data: Registration data to validate
            
        Returns:
            Dictionary with validation results and any issues found
            
        Example:
            result = registration_service.validate_registration_availability(registration_data)
            if result["is_valid"]:
                # Proceed with registration
            else:
                # Show validation errors: result["issues"]
        """
        issues = []
        warnings = []
        
        try:
            # Check identity provider uniqueness
            existing_user = self.user_repo.get_by_identity_provider_id(
                self.db,
                registration_data.identity_provider,
                registration_data.identity_provider_id or registration_data.email
            )
            
            if existing_user:
                issues.append("A user with this identity provider information already exists")
            
            # Check tenant slug availability if provided
            if registration_data.tenant_slug:
                if not self.tenant_repo.check_slug_availability(self.db, registration_data.tenant_slug):
                    issues.append(f"Tenant slug '{registration_data.tenant_slug}' is already taken")
                
                if not self.tenant_repo.check_subdomain_availability(self.db, registration_data.tenant_slug):
                    issues.append(f"Subdomain '{registration_data.tenant_slug}' is already taken")
            else:
                # Generate what the slug would be and check it
                generated_slug = self.tenant_repo.generate_unique_slug(self.db, registration_data.company_name)
                if generated_slug != registration_data.company_name.lower().replace(" ", "-"):
                    warnings.append(f"Company name will be converted to slug: '{generated_slug}'")
            
            return {
                "is_valid": len(issues) == 0,
                "issues": issues,
                "warnings": warnings,
                "suggested_slug": self.tenant_repo.generate_unique_slug(self.db, registration_data.company_name) if not registration_data.tenant_slug else None
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "warnings": [],
                "suggested_slug": None
            }
    
    def get_registration_suggestions(self, company_name: str) -> Dict[str, str]:
        """
        Get suggestions for tenant slug and subdomain based on company name.
        
        Useful for providing UI suggestions during registration.
        
        Args:
            company_name: Company name to generate suggestions from
            
        Returns:
            Dictionary with suggested slug and subdomain
        """
        try:
            suggested_slug = self.tenant_repo.generate_unique_slug(self.db, company_name)
            suggested_subdomain = self.tenant_repo.generate_unique_subdomain(self.db, company_name)
            
            return {
                "suggested_slug": suggested_slug,
                "suggested_subdomain": suggested_subdomain,
                "company_name": company_name
            }
        except Exception:
            # Fallback to basic suggestions
            import re
            basic_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', company_name.lower())
            basic_slug = re.sub(r'\s+', '-', basic_slug.strip())
            
            return {
                "suggested_slug": basic_slug,
                "suggested_subdomain": basic_slug.replace('-', ''),
                "company_name": company_name
            }


# Dependency injection helper for FastAPI
def get_registration_service(db: Session) -> RegistrationService:
    """
    Dependency injection helper for FastAPI endpoints.
    
    Usage in FastAPI:
        @router.post("/register")
        async def register(
            registration_data: UserRegistration,
            registration_service: RegistrationService = Depends(get_registration_service)
        ):
            tenant, user = registration_service.register_user_and_tenant(registration_data)
            return {"tenant": tenant, "user": user}
    """
    return RegistrationService(db)
```

### 2.3 Create Services Package Init

Create `app/services/__init__.py`:

```python
"""
Service layer for business logic coordination.

This package contains services that orchestrate multiple repository
operations, manage transaction boundaries, and implement complex
business logic.
"""

from .registration_service import RegistrationService, get_registration_service

__all__ = ["RegistrationService", "get_registration_service"]
```

---

## Step 3: Testing the Registration Service

### 3.1 Create Registration Service Test

Create `test_registration_service.py` in your project root:

```python
from app.services.registration_service import RegistrationService
from app.schemas.user import UserRegistration
from app.db.session import SessionLocal
from uuid import uuid4
import time

def test_registration_service():
    """Test RegistrationService functionality"""
    
    db = SessionLocal()
    
    try:
        print("🧪 Testing RegistrationService...")
        
        registration_service = RegistrationService(db)
        
        # Generate unique identifiers for this test run
        test_run_id = str(uuid4())[:8]
        unique_slug = f"test-company-{test_run_id}"
        
        # Test 1: Successful registration
        print("\n--- Test 1: Successful Registration ---")
        registration_data = UserRegistration(
            email=f"admin-{test_run_id}@testcompany.com",
            display_name="Test Admin",
            identity_provider="local_dev_registration",
            identity_provider_id=f"test-admin-{uuid4()}",
            company_name="Test Company LLC",
            tenant_slug=unique_slug
        )
        
        tenant, user = registration_service.register_user_and_tenant(registration_data)
        
        assert tenant is not None, "Tenant should be created"
        assert user is not None, "User should be created"
        assert user.tenant_id == tenant.id, "User should belong to created tenant"
        assert tenant.name == "Test Company LLC", "Tenant should have correct name"
        assert user.email == f"admin-{test_run_id}@testcompany.com", "User should have correct email"
        
        print(f"✅ Created tenant: {tenant.name} (slug: {tenant.slug})")
        print(f"✅ Created user: {user.email} for tenant")
        print(f"✅ User belongs to tenant: {user.tenant_id == tenant.id}")
        
        # Test 2: Validation - duplicate identity provider
        print("\n--- Test 2: Duplicate Identity Provider Validation ---")
        duplicate_registration = UserRegistration(
            email=f"another-{test_run_id}@testcompany.com",
            display_name="Another Admin",
            identity_provider="local_dev_registration",
            identity_provider_id=registration_data.identity_provider_id,  # Same as before
            company_name="Another Company",
            tenant_slug=f"another-company-{test_run_id}"
        )
        
        try:
            registration_service.register_user_and_tenant(duplicate_registration)
            assert False, "Should have failed with duplicate identity provider"
        except ValueError as e:
            print(f"✅ Correctly rejected duplicate identity: {e}")
        
        # Test 3: Validation - duplicate tenant slug
        print("\n--- Test 3: Duplicate Tenant Slug Validation ---")
        duplicate_slug_registration = UserRegistration(
            email=f"admin2-{test_run_id}@testcompany2.com",
            display_name="Test Admin 2",
            identity_provider="local_dev_registration",
            identity_provider_id=f"test-admin-2-{uuid4()}",
            company_name="Test Company 2",
            tenant_slug=unique_slug  # Same slug as first registration
        )
        
        try:
            registration_service.register_user_and_tenant(duplicate_slug_registration)
            assert False, "Should have failed with duplicate tenant slug"
        except ValueError as e:
            print(f"✅ Correctly rejected duplicate slug: {e}")
        
        # Test 4: Validation check without registration
        print("\n--- Test 4: Registration Availability Check ---")
        validation_result = registration_service.validate_registration_availability(
            duplicate_slug_registration
        )
        
        assert validation_result["is_valid"] == False, "Should be invalid"
        assert len(validation_result["issues"]) > 0, "Should have issues"
        print(f"✅ Validation check works: {len(validation_result['issues'])} issues found")
        print(f"   Issues: {validation_result['issues']}")
        
        # Test 5: Registration suggestions
        print("\n--- Test 5: Registration Suggestions ---")
        suggestions = registration_service.get_registration_suggestions("New Amazing Company!")
        
        assert "suggested_slug" in suggestions, "Should provide slug suggestion"
        assert "suggested_subdomain" in suggestions, "Should provide subdomain suggestion"
        print(f"✅ Suggestions work:")
        print(f"   Suggested slug: {suggestions['suggested_slug']}")
        print(f"   Suggested subdomain: {suggestions['suggested_subdomain']}")
        
        # Test 6: Auto-generation when no slug provided
        print("\n--- Test 6: Auto-Generation Without Slug ---")
        auto_gen_registration = UserRegistration(
            email=f"auto-{test_run_id}@autogencompany.com",
            display_name="Auto Gen User",
            identity_provider="local_dev_registration",
            identity_provider_id=f"auto-gen-{uuid4()}",
            company_name=f"Auto Generated Company {test_run_id}",
            # No tenant_slug provided - should be auto-generated
        )
        
        auto_tenant, auto_user = registration_service.register_user_and_tenant(auto_gen_registration)
        
        assert auto_tenant.slug is not None, "Should auto-generate slug"
        assert auto_tenant.subdomain is not None, "Should auto-generate subdomain"
        print(f"✅ Auto-generation works:")
        print(f"   Generated slug: {auto_tenant.slug}")
        print(f"   Generated subdomain: {auto_tenant.subdomain}")
        
        # Clean up
        print("\n--- Cleanup ---")
        from app.repositories.user_repository import user_repo
        from app.repositories.tenant_repository import tenant_repo
        
        # Clean up first registration
        user_repo.soft_delete(db, tenant.id, user.id)
        tenant_repo.soft_delete(db, tenant.id, tenant.id)
        
        # Clean up auto-generated registration
        user_repo.soft_delete(db, auto_tenant.id, auto_user.id)
        tenant_repo.soft_delete(db, auto_tenant.id, auto_tenant.id)
        
        db.commit()
        print("✅ Cleaned up test data")
        
        print("\n🎉 RegistrationService tests passed!")
        
    except Exception as e:
        print(f"❌ RegistrationService test failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_registration_service()
```

### 3.2 Run the Test

```bash
# Navigate to your project directory
cd C:\_source\Greenshoes\Summer2025Internship\Sprint2\Guided_Walkthrough\quodsi_api

# Activate virtual environment
.\venv\Scripts\activate

# Run the test
python test_registration_service.py
```

Expected output:
```
🧪 Testing RegistrationService...

--- Test 1: Successful Registration ---
✅ Created tenant: Test Company LLC (slug: test-company)
✅ Created user: admin@testcompany.com for tenant
✅ User belongs to tenant: True

--- Test 2: Duplicate Identity Provider Validation ---
✅ Correctly rejected duplicate identity: User with identity provider local_dev_registration and ID test-admin-... already exists

--- Test 3: Duplicate Tenant Slug Validation ---
✅ Correctly rejected duplicate slug: Tenant slug 'test-company' is already taken

--- Test 4: Registration Availability Check ---
✅ Validation check works: 1 issues found
   Issues: ["Tenant slug 'test-company' is already taken"]

--- Test 5: Registration Suggestions ---
✅ Suggestions work:
   Suggested slug: new-amazing-company
   Suggested subdomain: newamazingcompany

--- Test 6: Auto-Generation Without Slug ---
✅ Auto-generation works:
   Generated slug: auto-generated-company
   Generated subdomain: autogeneratedcompany

--- Cleanup ---
✅ Cleaned up test data

🎉 RegistrationService tests passed!
```

---

## Step 4: Understanding Service Layer Benefits

### 4.1 Transaction Management

**Before (without service layer)**:
```python
# Error-prone: Manual transaction management in multiple places
def register_user_endpoint(registration_data):
    db = get_db()
    try:
        tenant = tenant_repo.create(db, tenant_data)
        db.commit()  # First commit
        
        user = user_repo.create_user_for_tenant(db, user_data, tenant.id)
        db.commit()  # Second commit
        
        # Problem: If user creation fails, tenant still exists!
    except Exception:
        db.rollback()  # May not rollback tenant creation
```

**After (with service layer)**:
```python
# Clean: Service manages single transaction boundary
def register_user_endpoint(registration_data):
    db = get_db()
    registration_service = RegistrationService(db)
    
    # Single transaction - both created or neither created
    tenant, user = registration_service.register_user_and_tenant(registration_data)
```

### 4.2 Business Logic Centralization

**Repository Layer** - Simple data operations:
```python
class TenantRepository:
    def create(self, db: Session, obj_in: TenantCreate) -> Tenant:
        # Just creates tenant - no validation
        return created_tenant
```

**Service Layer** - Complex business logic:
```python
class RegistrationService:
    def register_user_and_tenant(self, registration_data: UserRegistration):
        # 1. Validates business rules
        # 2. Checks for conflicts
        # 3. Coordinates multiple repositories
        # 4. Manages transactions
        # 5. Provides meaningful error messages
```

### 4.3 Error Handling and Recovery

**Comprehensive Error Scenarios**:
```python
try:
    # Business validation
    self._validate_registration_data(registration_data)
    
    # Data operations
    tenant = self._create_tenant_from_registration(registration_data)
    user = self._create_user_from_registration(registration_data, tenant.id)
    
    # Transaction commit
    self.db.commit()
    
except ValueError as e:
    # Business logic errors - don't rollback (no DB changes yet)
    raise e
except Exception as e:
    # Database errors - rollback everything
    self.db.rollback()
    raise e
```

---

## Step 5: Service Usage Patterns

### 5.1 FastAPI Integration

```python
# Example FastAPI endpoint using the service
from fastapi import APIRouter, Depends, HTTPException
from app.services.registration_service import get_registration_service
from app.schemas.user import UserRegistration

router = APIRouter()

@router.post("/register")
async def register_user_and_tenant(
    registration_data: UserRegistration,
    registration_service: RegistrationService = Depends(get_registration_service)
):
    """Register a new user and create their tenant organization."""
    try:
        tenant, user = registration_service.register_user_and_tenant(registration_data)
        
        return {
            "message": "Registration successful",
            "tenant": {
                "id": str(tenant.id),
                "name": tenant.name,
                "slug": tenant.slug,
                "subdomain": tenant.subdomain
            },
            "user": {
                "id": str(user.id),
                "email": user.email,
                "display_name": user.display_name
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/register/validate")
async def validate_registration(
    registration_data: UserRegistration,
    registration_service: RegistrationService = Depends(get_registration_service)
):
    """Validate registration data without creating accounts."""
    result = registration_service.validate_registration_availability(registration_data)
    return result
```

### 5.2 Form Validation Usage

```python
# Example: Frontend form validation
def check_registration_form(form_data):
    """Check form data before submission"""
    registration_data = UserRegistration(**form_data)
    
    # Check availability without registering
    result = registration_service.validate_registration_availability(registration_data)
    
    if result["is_valid"]:
        return {"status": "valid", "can_proceed": True}
    else:
        return {
            "status": "invalid", 
            "errors": result["issues"],
            "suggestions": result.get("suggested_slug")
        }
```

---

## Common Issues and Solutions

### Issue 1: Unique Constraint Violation During Testing
**Problem**: Test fails with `Violation of UNIQUE KEY constraint 'uq_tenants_slug'` when using hardcoded test data
**Solution**: Generate unique test identifiers for each test run to prevent conflicts:
```python
# Generate unique identifiers for each test run
test_run_id = str(uuid4())[:8]
unique_slug = f"test-company-{test_run_id}"

# Use unique values in test data
registration_data = UserRegistration(
    email=f"admin-{test_run_id}@testcompany.com",
    tenant_slug=unique_slug,
    # ... other fields
)
```

### Issue 2: Transaction Rollback Not Working
**Problem**: Changes persist even when exceptions occur
**Solution**: Ensure proper exception handling and rollback in service methods

### Issue 3: Validation Errors After Database Changes
**Problem**: Business validation happens after database operations
**Solution**: Always validate before making database changes

### Issue 4: Partial Registration States
**Problem**: Tenant created but user creation fails
**Solution**: Use single transaction boundary in service layer

### Issue 5: Identity Provider ID Conflicts
**Problem**: Same identity provider ID used across different registrations  
**Solution**: Validate identity provider uniqueness in service layer

---

## Verification Checklist

After completing this step, verify:

- [ ] `app/services/registration_service.py` exists with complete implementation
- [ ] RegistrationService coordinates TenantRepository and UserRepository
- [ ] Transaction management with proper commit/rollback
- [ ] Business validation prevents conflicts and invalid data
- [ ] Registration availability checking works
- [ ] Auto-generation of slugs and subdomains works
- [ ] Comprehensive error handling with meaningful messages
- [ ] Test script runs successfully with all scenarios
- [ ] Service is exported in `__init__.py`
- [ ] Dependency injection helper function works

## Next Steps

With the RegistrationService implemented, you now have:

1. **Service Layer Foundation** - Pattern for coordinating multiple repositories
2. **Transaction Management** - Proper commit/rollback boundaries
3. **Business Logic Coordination** - Complex validation and data processing
4. **Error Handling** - Comprehensive error recovery and meaningful messages
5. **Registration Complete** - Full user and tenant creation process

In **065_User_Service_Implementation.md**, we'll create the UserService that handles user profile management, authentication coordination, and user-specific business operations.

## Key Takeaways

1. **Services coordinate repositories** - Multiple data operations in single transactions
2. **Transaction boundaries** are owned by services, not repositories
3. **Business validation** happens before database operations
4. **Error handling** must distinguish between validation and database errors
5. **Complex operations** benefit from step-by-step breakdown with validation
6. **Dependency injection** makes services easy to test and use in FastAPI
7. **Registration is complex** - requires coordination of multiple entities and validation
8. **Rollback safety** ensures data consistency when operations fail
