# Part 2: Service and Repository Logging

**Duration:** 15-20 minutes  
**Objective:** Learn how to add comprehensive logging to business logic and data access layers using consistent patterns.

**Prerequisites:** Part 1 completed - Basic logging infrastructure working

---

## Overview

Instead of showing complete file rewrites, this guide teaches you the **patterns** for adding logging to your existing services and repositories. You'll learn where to place logs, what information to include, and how to maintain consistency across your application.

---

## Step 1: Core Logging Patterns

### 1.1 Basic Setup Pattern
**For every service/repository file, add these imports:**

```python
from app.core.logging_config import get_logger

logger = get_logger(__name__)
```

**Why:** This creates a logger instance specific to each file, making it easy to identify where logs originate.

### 1.2 The Four Types of Logs

| Log Level | When to Use | Example |
|-----------|------------|---------|
| **DEBUG** | Detailed step tracking, variable values | `"Processing user ID: 12345"` |
| **INFO** | Successful operations, milestones | `"User created successfully"` |
| **WARNING** | Business rule violations, recoverable issues | `"Email already exists, skipping"` |
| **ERROR** | Exceptions, failures | `"Database connection failed"` |

---

## Step 2: Service Layer Logging Patterns

### 2.1 Operation Boundary Logging
**Pattern:** Log at the start and end of major operations

```python
def register_user_and_tenant(self, db: Session, *, reg_in: UserRegistrationRequest, request_id: str = "unknown"):
    # START LOG - Log operation beginning with context
    logger.info(
        "Starting user and tenant registration",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "email": reg_in.email,
                "company_name": reg_in.company_name,
                "operation": "register_user_and_tenant"
            }
        }
    )
    
    try:
        # ... your existing business logic ...
        
        # SUCCESS LOG - Log successful completion with results
        logger.info(
            "User registration completed successfully", 
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(new_user.id),
                    "tenant_id": str(new_tenant.id),
                    "operation": "register_user_and_tenant",
                    "status": "success"
                }
            }
        )
        
        return new_user, new_tenant
        
    except Exception as e:
        # ERROR LOG - Log failures with context
        logger.error(
            f"User registration failed: {str(e)}",
            exc_info=True,  # This includes the stack trace
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "email": reg_in.email,
                    "operation": "register_user_and_tenant",
                    "status": "failed"
                }
            }
        )
        raise
```

**Apply this pattern to:** Any service method that represents a complete business operation.

### 2.2 Step Tracking Pattern
**Pattern:** Log major steps within complex operations

```python
def complex_business_operation(self, ...):
    logger.info("Starting complex operation", extra={"extra_fields": {...}})
    
    # Step 1
    logger.debug("Creating tenant organization", extra={"extra_fields": {"step": "create_tenant"}})
    new_tenant = tenant_repo.create(...)
    logger.debug("Tenant created", extra={"extra_fields": {"tenant_id": str(new_tenant.id)}})
    
    # Step 2  
    logger.debug("Creating user account", extra={"extra_fields": {"step": "create_user"}})
    new_user = user_repo.create(...)
    logger.debug("User created", extra={"extra_fields": {"user_id": str(new_user.id)}})
```

**Apply this pattern to:** Multi-step service operations where you need to track progress.

---

## Step 3: Repository Layer Logging Patterns

### 3.1 Data Access Logging Pattern
**Pattern:** Log database operations with relevant context

```python
def create(self, db: Session, *, obj_in: TenantCreate) -> Tenant:
    # Log the operation start with input details
    logger.debug(
        "Creating new tenant",
        extra={
            "extra_fields": {
                "tenant_name": obj_in.name,
                "slug": slug,
                "subdomain": subdomain
            }
        }
    )
    
    try:
        # ... your existing create logic ...
        
        # Log successful creation with generated details
        logger.info(
            "Tenant created successfully",
            extra={
                "extra_fields": {
                    "tenant_id": str(db_obj.id),
                    "tenant_name": db_obj.name,
                    "slug": db_obj.slug
                }
            }
        )
        
        return db_obj
        
    except IntegrityError as e:
        db.rollback()
        logger.error(
            f"Database integrity error creating tenant: {str(e)}",
            exc_info=True,
            extra={"extra_fields": {"tenant_name": obj_in.name}}
        )
        raise ValueError("Tenant with this information already exists")
```

**Apply this pattern to:** Any repository method that creates, updates, or deletes data.

### 3.2 Business Rule Validation Pattern
**Pattern:** Log when business rules prevent operations

```python
def create_user_for_tenant(self, db: Session, *, obj_in: UserCreateInternal, tenant_id: UUID) -> User:
    # Check business rules first
    existing_user = db.query(User).filter(...).first()
    
    if existing_user:
        # Log business rule violation
        logger.warning(
            "User creation failed - email already exists in tenant",
            extra={
                "extra_fields": {
                    "email": obj_in.email,
                    "tenant_id": str(tenant_id),
                    "existing_user_id": str(existing_user.id)
                }
            }
        )
        raise ValueError(f"User with email '{obj_in.email}' already exists in this tenant")
```

**Apply this pattern to:** Any validation that prevents an operation from proceeding.

---

## Step 4: Practical Implementation Guide

### 4.1 What to Log in Your Services
1. **Method Entry:** Operation name, input parameters, request ID
2. **Major Steps:** What step is being performed, relevant IDs
3. **Success:** Final result, generated IDs, status
4. **Errors:** Exception details, input context, operation name

### 4.2 What to Log in Your Repositories  
1. **Data Operations:** What's being created/updated/deleted, key fields
2. **Business Rule Checks:** Why an operation was prevented
3. **Database Errors:** Full context of what was being attempted
4. **Success Results:** Generated IDs, final state

### 4.3 Essential Context Fields
Always include these in your `extra_fields`:

```python
{
    "request_id": request_id,        # For tracing requests
    "operation": "method_name",      # What operation is happening
    "user_id": str(user_id),         # Who is performing the action
    "tenant_id": str(tenant_id),     # Which tenant context  
    "entity_id": str(entity.id),     # The main entity being worked on
    "status": "success|failed"       # Operation outcome
}
```

---

## Step 5: Implementation Exercise

### 5.1 Update Your User Service
1. **Add the basic setup** (imports and logger) to your `app/services/user_service.py`
2. **Find your main registration method** and apply the **Operation Boundary Logging** pattern
3. **Add step tracking** for major steps like "create tenant" and "create user"
4. **Test** by making a registration request and checking the logs

### 5.2 Update Your Tenant Repository
1. **Add the basic setup** to your `app/repositories/tenant_repository.py`
2. **Find your create method** and apply the **Data Access Logging** pattern
3. **Add business rule validation logging** for duplicate tenant checks
4. **Test** by creating tenants and checking the logs

### 5.3 Update Your User Repository
1. **Add the basic setup** to your `app/repositories/user_repository.py`
2. **Apply the Data Access Logging pattern** to your user creation method
3. **Add business rule validation logging** for duplicate user checks
4. **Test** by creating users and checking the logs

---

## Step 6: Testing Your Logging

### 6.1 Test Successful Operations
```bash
# Make a successful registration request
curl -X POST http://localhost:8000/api/v1/auth/registration/tenant \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "domain": "testco",
    "admin_email": "admin@testco.com",
    "admin_password": "password123",
    "admin_display_name": "Test Admin"
  }'
```

**Expected Logs:**
- Service: "Starting user and tenant registration"
- Repository: "Creating new tenant"
- Repository: "Tenant created successfully"
- Repository: "Creating user for tenant"
- Repository: "User created successfully"
- Service: "User registration completed successfully"

### 6.2 Test Error Scenarios
```bash
# Try to create duplicate tenant
curl -X POST http://localhost:8000/api/v1/auth/registration/tenant \
  -H "Content-Type: application/json" \
  -d '{...same data as above...}'
```

**Expected Logs:**
- Warning: "Tenant creation failed - slug or subdomain already exists"
- Error: "Database integrity error creating tenant"

---

## Verification Checklist

- [ ] ✅ Added logging imports to service and repository files
- [ ] ✅ Applied Operation Boundary Logging to service methods
- [ ] ✅ Applied Data Access Logging to repository methods  
- [ ] ✅ Added business rule validation logging
- [ ] ✅ All logs include relevant context in `extra_fields`
- [ ] ✅ Error logs include `exc_info=True` for stack traces
- [ ] ✅ Request IDs are passed through service layers
- [ ] ✅ Tested both success and error scenarios
- [ ] ✅ Can trace complete request flow through logs

---

## Key Logging Principles

### 1. Consistency
Use the same patterns across all services and repositories for predictable log structure.

### 2. Context is King  
Always include enough context to understand what happened without looking at other logs.

### 3. Actionable Information
Log information that helps with debugging, monitoring, and business insights.

### 4. Performance Awareness
Use DEBUG for verbose information, INFO for important milestones, avoid logging sensitive data.

---

## What's Next

You now understand how to add structured logging to any service or repository. The next step is to connect this logging to your API endpoints and see the complete request flow.

**Next:** [Part 3: API Endpoint Logging](./080_Logging_Integration_Part3_API.md)
