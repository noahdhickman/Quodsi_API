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
from app.core.logging_config import get_logger

logger = get_logger(__name__)

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
            identity_provider_id=registration_data.identity_provider_id or registration_data.email,
            tenant_id=tenant_id
        )
        
        return self.user_repo.create_user_for_tenant(
            self.db,
            obj_in=user_create_data
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
    
    def register_tenant_with_admin(
        self,
        tenant_name: str,
        domain: str,
        admin_email: str,
        admin_password: str,
        admin_display_name: str,
        request_id: str = "unknown"
    ) -> dict:
        """
        Register a new tenant with an admin user.
        
        This method creates both a tenant and its first admin user in a single transaction.
        
        Args:
            tenant_name: Name of the tenant organization
            domain: Domain/slug for the tenant
            admin_email: Email address for the admin user
            admin_password: Password for the admin user
            admin_display_name: Display name for the admin user
            request_id: Optional request ID for tracking
        
        Returns:
            Dictionary containing the created tenant and admin user information
        
        Raises:
            ValueError: If validation fails or conflicts exist
            Exception: For database errors (triggers rollback)
        """
        # START LOG - Log operation beginning with context
        logger.info(
            "Starting tenant registration with admin user",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "tenant_name": tenant_name,
                    "domain": domain,
                    "admin_email": admin_email,
                    "operation": "register_tenant_with_admin"
                }
            }
        )
        
        try:
            # Step 1: Create tenant
            logger.debug(
                "Creating tenant organization", 
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "step": "create_tenant",
                        "tenant_name": tenant_name,
                        "domain": domain
                    }
                }
            )
            
            from app.schemas.tenant import TenantCreate
            
            # Create tenant with TenantCreate object
            tenant_data = TenantCreate(
                name=tenant_name,
                slug=domain,
                subdomain=domain,
                plan_type="trial",
                status="trial"
            )
            
            # Create the tenant using the repository
            tenant = self.tenant_repo.create(self.db, obj_in=tenant_data)
            logger.debug(
                "Tenant created successfully", 
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "step": "create_tenant",
                        "tenant_id": str(tenant.id),
                        "tenant_name": tenant.name
                    }
                }
            )
            
            # Step 2: Create admin user
            logger.debug(
                "Creating admin user for tenant", 
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "step": "create_admin_user",
                        "tenant_id": str(tenant.id),
                        "admin_email": admin_email
                    }
                }
            )
            
            # Create admin user with local identity provider
            user_dict = {
                "email": admin_email,
                "display_name": admin_display_name,
                "identity_provider": "local",
                "identity_provider_id": admin_email,
                "status": "active"
            }
            admin_user = self.user_repo.create(self.db, obj_in=user_dict, tenant_id=tenant.id)
            logger.debug(
                "Admin user created successfully", 
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "step": "create_admin_user",
                        "user_id": str(admin_user.id),
                        "tenant_id": str(tenant.id)
                    }
                }
            )
            
            # Step 3: Commit transaction
            logger.debug(
                "Committing transaction", 
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "step": "commit_transaction"
                    }
                }
            )
            self.db.commit()
            
            # Prepare result
            result = {
                "tenant_id": tenant.id,
                "tenant_name": tenant.name,
                "domain": domain,
                "admin_user_id": admin_user.id,
                "admin_email": admin_email
            }
            
            # SUCCESS LOG - Log successful completion with results
            logger.info(
                "Tenant registration completed successfully", 
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "tenant_id": str(tenant.id),
                        "admin_user_id": str(admin_user.id),
                        "operation": "register_tenant_with_admin",
                        "status": "success"
                    }
                }
            )
            
            return result
            
        except Exception as e:
            # Rollback on any error
            try:
                self.db.rollback()
                logger.debug("Database rollback successful")
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {str(rollback_error)}")
            
            # ERROR LOG - Log failures with context
            logger.error(
                f"Tenant registration failed: {str(e)}",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "tenant_name": tenant_name,
                        "domain": domain,
                        "admin_email": admin_email,
                        "operation": "register_tenant_with_admin",
                        "status": "failed",
                        "error_type": type(e).__name__
                    }
                }
            )
            raise e


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