from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, func
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta
from app.db.models.user import User
from app.db.models.tenant import Tenant
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate

class UserRepository(BaseRepository[User]):
    """
    Repository for user operations with tenant isolation.
    
    Inherits from BaseRepository to get standard CRUD operations
    and adds user-specific methods for authentication, activity tracking,
    and user management within tenant boundaries.
    
    Key Features:
    - Identity provider authentication
    - Email-based lookups within tenants
    - Activity and login statistics tracking
    - User search and filtering
    - Status management
    """
    
    def __init__(self):
        """Initialize with User model."""
        super().__init__(User)
    
    # === Authentication Methods ===
    
    def get_by_email(self, db: Session, tenant_id: UUID, email: str) -> Optional[User]:
        """
        Get user by email within a specific tenant.
        
        Email addresses are unique within each tenant but may be duplicated
        across different tenants, so tenant scoping is required.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            email: User email address
            
        Returns:
            User instance or None if not found
            
        Example:
            user = user_repo.get_by_email(db, tenant_id, "user@company.com")
        """
        return db.query(User).filter(
            and_(
                User.tenant_id == tenant_id,
                User.email == email,
                User.is_deleted == False
            )
        ).first()
    
    def get_by_identity_provider_id(self, db: Session, identity_provider: str, 
                                   identity_provider_id: str) -> Optional[User]:
        """
        Get user by identity provider information.
        
        This is used for authentication and doesn't require tenant_id
        since identity provider IDs are globally unique across the system.
        This method is typically called during the authentication process
        before we know which tenant the user belongs to.
        
        Args:
            db: Database session
            identity_provider: Provider name (e.g., "entra_id", "google", "local_dev_registration")
            identity_provider_id: Unique ID from the provider
            
        Returns:
            User instance or None if not found
            
        Example:
            user = user_repo.get_by_identity_provider_id(
                db, "entra_id", "12345-abcde-67890"
            )
        """
        return db.query(User).filter(
            and_(
                User.identity_provider == identity_provider,
                User.identity_provider_id == identity_provider_id,
                User.is_deleted == False
            )
        ).first()
    
    def check_email_availability(self, db: Session, tenant_id: UUID, email: str, 
                                exclude_user_id: Optional[UUID] = None) -> bool:
        """
        Check if an email address is available within a tenant.
        
        Used during user creation and email updates to prevent conflicts.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            email: Email address to check
            exclude_user_id: User ID to exclude from check (for updates)
            
        Returns:
            True if email is available, False if taken
        """
        query = db.query(User.id).filter(
            and_(
                User.tenant_id == tenant_id,
                User.email == email,
                User.is_deleted == False
            )
        )
        
        # Exclude specific user (useful for updates)
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        
        return query.first() is None
    
    # === User Creation and Management ===
    
    def create_user_for_tenant(self, db: Session, *, obj_in: UserCreate) -> User:
        """
        Create a new user with validation.
        
        Validates email uniqueness within the tenant and sets appropriate defaults.
        The tenant_id is included in the UserCreate schema.
        
        Args:
            db: Database session
            obj_in: User creation schema (includes tenant_id)
            
        Returns:
            Created user instance
            
        Raises:
            ValueError: If email is already taken within the tenant
            
        Example:
            user_data = UserCreate(
                email="user@company.com",
                display_name="John Doe",
                identity_provider="entra_id",
                identity_provider_id="12345",
                tenant_id=tenant_id
            )
            new_user = user_repo.create_user_for_tenant(db, obj_in=user_data)
        """
        # Check email availability
        if not self.check_email_availability(db, obj_in.tenant_id, obj_in.email):
            raise ValueError(f"Email '{obj_in.email}' is already taken in this organization")
        
        # Prepare user data
        user_data = {
            "email": obj_in.email,
            "display_name": obj_in.display_name,
            "identity_provider": obj_in.identity_provider,
            "identity_provider_id": obj_in.identity_provider_id,
            "status": getattr(obj_in, 'status', 'active'),
            "login_count": 0,
            "total_usage_minutes": 0
        }
        
        return self.create(db, obj_in=user_data, tenant_id=obj_in.tenant_id)
    
    # === Basic Activity Tracking ===
    
    def update_login_stats(self, db: Session, tenant_id: UUID, user_id: UUID) -> Optional[User]:
        """
        Update user login statistics when they authenticate.
        
        Increments login count and updates last login timestamp.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to update
            
        Returns:
            Updated user instance or None if not found
            
        Example:
            updated_user = user_repo.update_login_stats(db, tenant_id, user_id)
        """
        user = self.get_by_id(db, tenant_id, user_id)
        if user:
            user.login_count = (user.login_count or 0) + 1
            user.last_login_at = datetime.now(timezone.utc)
            user.updated_at = datetime.now(timezone.utc)
            db.add(user)
            db.flush()
            db.refresh(user)
        return user
    
    def update_activity_timestamp(self, db: Session, tenant_id: UUID, user_id: UUID) -> Optional[User]:
        """
        Update user's last activity timestamp.
        
        Called periodically during user sessions to track engagement.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to update
            
        Returns:
            Updated user instance or None if not found
        """
        user = self.get_by_id(db, tenant_id, user_id)
        if user:
            user.last_active_at = datetime.now(timezone.utc)
            user.updated_at = datetime.now(timezone.utc)
            db.add(user)
            db.flush()
            db.refresh(user)
        return user
    
    # === Basic User Queries ===
    
    def search_users(self, db: Session, tenant_id: UUID, *, search_term: str, 
                    skip: int = 0, limit: int = 100) -> List[User]:
        """
        Search users by email or display name within a tenant.
        
        Performs case-insensitive search across email and display_name fields.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            search_term: Term to search for
            skip: Pagination offset
            limit: Maximum results to return
            
        Returns:
            List of matching users
            
        Example:
            users = user_repo.search_users(db, tenant_id, search_term="john", limit=25)
        """
        return self.search(
            db=db,
            tenant_id=tenant_id,
            search_term=search_term,
            search_fields=["email", "display_name"],
            skip=skip,
            limit=limit
        )
    
    def get_users_by_status(self, db: Session, tenant_id: UUID, status: str, 
                           *, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get users filtered by status within a tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            status: User status to filter by (e.g., "active", "inactive", "suspended")
            skip: Pagination offset
            limit: Maximum results to return
            
        Returns:
            List of users with the specified status
        """
        return db.query(User).filter(
            and_(
                User.tenant_id == tenant_id,
                User.status == status,
                User.is_deleted == False
            )
        ).order_by(User.created_at.desc()).offset(skip).limit(limit).all()

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
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to update
            minutes: Minutes to add to total usage
            
        Returns:
            Updated user instance or None if not found
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
        """
        Get comprehensive statistics for a specific user.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to get statistics for
            
        Returns:
            Dictionary containing user statistics
        """
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
        
        # Calculate if user is recently active (within last 7 days)
        is_recently_active = False
        if user.last_active_at:
            last_active = user.last_active_at
            if last_active.tzinfo is None:
                last_active = last_active.replace(tzinfo=timezone.utc)
            days_since_last_active = (now - last_active).days
            is_recently_active = days_since_last_active <= 7
        
        return {
            "user_id": str(user.id),
            "login_count": user.login_count or 0,
            "total_usage_minutes": getattr(user, 'total_usage_minutes', 0) or 0,
            "days_since_registration": days_since_registration,
            "days_since_last_login": days_since_last_login,
            "is_recently_active": is_recently_active,
            "status": user.status,
            "identity_provider": user.identity_provider
        }
    
    def get_tenant_user_summary(self, db: Session, tenant_id: UUID) -> Dict[str, Any]:
        """
        Get summary statistics for all users in a tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            
        Returns:
            Dictionary containing tenant user summary statistics
        """
        active_count = self.count_users_by_status(db, tenant_id, "active")
        inactive_count = self.count_users_by_status(db, tenant_id, "inactive") 
        suspended_count = self.count_users_by_status(db, tenant_id, "suspended")
        
        return {
            "total_users": active_count + inactive_count + suspended_count,
            "active_users": active_count,
            "inactive_users": inactive_count,
            "suspended_users": suspended_count
        }


# Create singleton instance for dependency injection
user_repo = UserRepository()