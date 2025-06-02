# Step 6: Repository and Service Patterns Overview

## Introduction

This module implements the **Repository Pattern** and **Service Layer Pattern** - two fundamental architectural patterns that create clean separation between data access, business logic, and API layers in our FastAPI application.

These patterns are essential for building maintainable, testable, and scalable multi-tenant SaaS applications like Quodsi.

## What Are These Patterns?

### Repository Pattern
The **Repository Pattern** encapsulates the logic needed to access data sources. It centralizes common data access functionality, providing better maintainability and decoupling the infrastructure or technology used to access databases from the domain model layer.

**Key Benefits:**
- **Data Access Abstraction**: Clean interface between business logic and data persistence
- **Multi-Tenant Safety**: Automatic tenant isolation for all database operations
- **Testability**: Easy to mock for unit testing
- **Consistency**: Standardized CRUD operations across all entities
- **Performance**: Optimized queries with strategic joins and eager loading

### Service Layer Pattern
The **Service Layer** defines an application's boundary and its set of available operations from the perspective of interfacing client layers. It encapsulates the application's business logic, controlling transactions and coordinating responses in the implementation of its operations.

**Key Benefits:**
- **Business Logic Coordination**: Orchestrates multiple repository operations
- **Transaction Management**: Handles commit/rollback boundaries
- **Error Handling**: Centralized error handling and recovery
- **Validation**: Business rule enforcement beyond schema validation
- **Cross-Entity Operations**: Coordinates operations across multiple entities

## Architecture Overview

```
┌─────────────────┐
│   FastAPI       │
│   Endpoints     │  ← API Layer (Controllers)
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Service       │
│   Layer         │  ← Business Logic Layer
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Repository    │
│   Layer         │  ← Data Access Layer
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   SQLAlchemy    │
│   Models        │  ← Domain Models
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Database      │
│   (SQL Server)  │  ← Data Storage
└─────────────────┘
```

## Multi-Tenant Architecture Considerations

### Tenant Isolation Strategy
Our implementation uses **tenant-scoped repositories** that automatically enforce data isolation:

1. **BaseRepository**: Generic repository with built-in tenant_id filtering
2. **TenantRepository**: Special case for tenant operations (global scope)
3. **UserRepository**: Tenant-scoped user operations with identity provider support

### Data Flow Example
```python
# API Endpoint
@router.get("/users/me")
async def get_current_user_profile(
    current_user: User = Depends(get_current_mock_user),
    user_service: UserService = Depends(get_user_service)
):
    # Service coordinates business logic
    profile = user_service.get_user_profile(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )
    return profile

# Service Layer
class UserService:
    def get_user_profile(self, tenant_id: UUID, user_id: UUID):
        # Coordinates multiple repository calls
        user = self.user_repo.get_by_id(tenant_id, user_id)
        tenant = self.tenant_repo.get_by_id(tenant_id)
        # Business logic and data transformation
        return UserWithTenant(user=user, tenant=tenant)

# Repository Layer
class UserRepository:
    def get_by_id(self, tenant_id: UUID, user_id: UUID):
        # Automatically enforces tenant isolation
        return db.query(User).filter(
            User.tenant_id == tenant_id,
            User.id == user_id,
            User.is_deleted == False
        ).first()
```

## What We'll Implement

### Repositories
1. **BaseRepository** (`061_Base_Repository_Implementation.md`)
   - Generic CRUD operations
   - Tenant-scoped filtering
   - Search and pagination
   - Soft delete support

2. **TenantRepository** (`062_Tenant_Repository_Implementation.md`)
   - Global tenant operations
   - Slug/subdomain uniqueness
   - Tenant lifecycle management

3. **UserRepository** (`063_User_Repository_Implementation.md`)
   - User-specific operations
   - Identity provider integration
   - Authentication support

### Services
4. **RegistrationService** (`064_Registration_Service_Implementation.md`)
   - User and tenant creation
   - Transaction coordination
   - Registration validation

5. **UserService** (`065_User_Service_Implementation.md`)
   - User profile management
   - Activity tracking
   - Statistics and analytics

### Infrastructure
6. **Service Dependencies** (`066_Service_Dependencies_and_DI.md`)
   - Dependency injection setup
   - FastAPI integration
   - Service lifecycle

7. **Testing** (`067_Repository_and_Service_Testing.md`)
   - Repository test patterns
   - Service testing with mocks
   - Integration testing

## Directory Structure Setup

Before we begin implementation, let's set up the proper directory structure:

### 1. Create Repository Directory Structure

```bash
# Navigate to your project directory
cd C:\_source\Greenshoes\Summer2025Internship\Sprint2\Guided_Walkthrough\quodsi_api

# Create repositories directory (if it doesn't exist)
mkdir -p app/repositories

# Create services directory (if it doesn't exist)
mkdir -p app/services
```

### 2. Expected Final Structure

After completing this module, your project structure will look like:

```
quodsi_api/
├── app/
│   ├── api/
│   │   ├── deps.py              # Dependencies (auth, db session)
│   │   └── endpoints/           # API route handlers
│   ├── core/
│   │   └── config.py           # Application configuration
│   ├── db/
│   │   ├── models/             # SQLAlchemy models
│   │   │   ├── base_entity.py
│   │   │   ├── tenant.py
│   │   │   └── user.py
│   │   └── session.py          # Database session
│   ├── repositories/           # ← New: Data access layer
│   │   ├── __init__.py
│   │   ├── base.py            # Generic repository
│   │   ├── tenant_repository.py
│   │   └── user_repository.py
│   ├── schemas/               # Pydantic schemas
│   │   ├── tenant.py
│   │   └── user.py
│   ├── services/              # ← New: Business logic layer
│   │   ├── __init__.py
│   │   ├── registration_service.py
│   │   └── user_service.py
│   └── main.py               # FastAPI application
├── alembic/                  # Database migrations
├── tests/                    # ← New: Test infrastructure
│   ├── repositories/
│   └── services/
└── requirements.txt
```

## Key Principles to Remember

### 1. Separation of Concerns
- **Repositories**: Only handle data access and basic queries
- **Services**: Handle business logic, validation, and coordination
- **API Endpoints**: Handle HTTP concerns and delegation to services

### 2. Tenant Isolation
- All repository operations (except tenant lookups) are tenant-scoped
- Never allow cross-tenant data access
- Services coordinate multi-tenant operations safely

### 3. Transaction Management
- Services own transaction boundaries (commit/rollback)
- Repositories use flush() instead of commit()
- Complex operations are wrapped in try/catch with rollback

### 4. Error Handling
- Repositories raise specific exceptions
- Services handle and transform exceptions appropriately
- API layer catches service exceptions and returns proper HTTP responses

### 5. Testing Strategy
- Repositories are tested with real database operations
- Services are tested with mocked repositories
- Integration tests verify the full stack

## Prerequisites Check

Before proceeding, ensure you have completed:

- ✅ **Module 1-2**: Project setup and database configuration
- ✅ **Module 3**: Tenant model and schemas implemented
- ✅ **Module 4**: User model and schemas implemented
- ✅ **Step 5**: Schema validation testing completed

**Required Files:**
- `app/db/models/base_entity.py` - BaseEntity with tenant isolation
- `app/db/models/tenant.py` - Tenant SQLAlchemy model
- `app/db/models/user.py` - User SQLAlchemy model
- `app/schemas/tenant.py` - Tenant Pydantic schemas
- `app/schemas/user.py` - User Pydantic schemas
- `app/db/session.py` - Database session configuration

## Next Steps

Start with **061_Base_Repository_Implementation.md** to implement the foundational repository pattern that will be used by all other repositories.

Each subsequent step builds upon the previous ones, so follow them in order:

1. **Base Repository** → Generic CRUD foundation
2. **Tenant Repository** → Global tenant operations
3. **User Repository** → Tenant-scoped user operations
4. **Registration Service** → Business logic coordination
5. **User Service** → Advanced user operations
6. **Dependencies** → FastAPI integration
7. **Testing** → Verification and quality assurance

## Success Criteria

By the end of this module, you will have:

- ✅ **Clean Architecture**: Clear separation between data access and business logic
- ✅ **Multi-Tenant Safety**: Automatic tenant isolation in all operations
- ✅ **Testable Code**: Easily mockable repositories and services
- ✅ **Transaction Management**: Proper commit/rollback handling
- ✅ **Performance**: Optimized queries with proper indexing utilization
- ✅ **Consistency**: Standardized patterns across all data operations
- ✅ **Error Handling**: Centralized error management and recovery
- ✅ **Dependency Injection**: Clean service instantiation for FastAPI

This foundation will support all future features and ensure your application scales properly as you add more entities and business logic.
