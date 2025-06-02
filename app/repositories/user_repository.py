from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, func
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta
from app.db.models.user import User
from app.db.models.tenant import Tenant
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    def get_by_email(self, db: Session, tenant_id: UUID, email: str) -> Optional[User]:
        logger.debug(
            "Looking up user by email",
            extra={"extra_fields": {
                "tenant_id": str(tenant_id),
                "email": email,
                "operation": "get_by_email"
            }}
        )
        return db.query(User).filter(
            and_(
                User.tenant_id == tenant_id,
                User.email == email,
                User.is_deleted == False
            )
        ).first()

    def get_by_identity_provider_id(self, db: Session, identity_provider: str, identity_provider_id: str) -> Optional[User]:
        logger.debug(
            "Looking up user by identity provider",
            extra={"extra_fields": {
                "identity_provider": identity_provider,
                "identity_provider_id": identity_provider_id,
                "operation": "get_by_identity_provider_id"
            }}
        )
        return db.query(User).filter(
            and_(
                User.identity_provider == identity_provider,
                User.identity_provider_id == identity_provider_id,
                User.is_deleted == False
            )
        ).first()

    def check_email_availability(self, db: Session, tenant_id: UUID, email: str, exclude_user_id: Optional[UUID] = None) -> bool:
        logger.debug(
            "Checking email availability",
            extra={"extra_fields": {
                "tenant_id": str(tenant_id),
                "email": email,
                "exclude_user_id": str(exclude_user_id) if exclude_user_id else None
            }}
        )
        query = db.query(User.id).filter(
            and_(
                User.tenant_id == tenant_id,
                User.email == email,
                User.is_deleted == False
            )
        )
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        return query.first() is None

    def create_user_for_tenant(self, db: Session, *, obj_in: UserCreate) -> User:
        logger.debug(
            "Creating new user for tenant",
            extra={"extra_fields": {
                "tenant_id": str(obj_in.tenant_id),
                "email": obj_in.email,
                "identity_provider": obj_in.identity_provider,
                "operation": "create_user_for_tenant"
            }}
        )
        try:
            logger.debug("Checking email availability")
            if not self.check_email_availability(db, obj_in.tenant_id, obj_in.email):
                logger.warning(
                    "User creation failed - email already exists in tenant",
                    extra={"extra_fields": {
                        "email": obj_in.email,
                        "tenant_id": str(obj_in.tenant_id),
                        "validation_error": "email_already_exists"
                    }}
                )
                raise ValueError(f"Email '{obj_in.email}' is already taken in this organization")

            logger.debug("Preparing user data for creation")
            user_data = {
                "email": obj_in.email,
                "display_name": obj_in.display_name,
                "identity_provider": obj_in.identity_provider,
                "identity_provider_id": obj_in.identity_provider_id,
                "status": getattr(obj_in, 'status', 'active'),
                "login_count": 0,
                "total_usage_minutes": 0
            }

            logger.debug("Creating user in database")
            user = self.create(db, obj_in=user_data, tenant_id=obj_in.tenant_id)

            logger.info(
                "User created successfully",
                extra={"extra_fields": {
                    "user_id": str(user.id),
                    "tenant_id": str(obj_in.tenant_id),
                    "email": user.email,
                    "identity_provider": user.identity_provider,
                    "status": user.status
                }}
            )
            return user

        except ValueError:
            raise
        except Exception as e:
            logger.error(
                f"Database error creating user: {str(e)}",
                exc_info=True,
                extra={"extra_fields": {
                    "tenant_id": str(obj_in.tenant_id),
                    "email": obj_in.email,
                    "error_type": type(e).__name__
                }}
            )
            raise

    def update_login_stats(self, db: Session, tenant_id: UUID, user_id: UUID) -> Optional[User]:
        logger.debug("Updating login stats", extra={"extra_fields": {
            "tenant_id": str(tenant_id),
            "user_id": str(user_id)
        }})
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
        logger.debug("Updating activity timestamp", extra={"extra_fields": {
            "tenant_id": str(tenant_id),
            "user_id": str(user_id)
        }})
        user = self.get_by_id(db, tenant_id, user_id)
        if user:
            user.last_active_at = datetime.now(timezone.utc)
            user.updated_at = datetime.now(timezone.utc)
            db.add(user)
            db.flush()
            db.refresh(user)
        return user

    def search_users(self, db: Session, tenant_id: UUID, *, search_term: str, skip: int = 0, limit: int = 100) -> List[User]:
        logger.debug("Searching users", extra={"extra_fields": {
            "tenant_id": str(tenant_id),
            "search_term": search_term,
            "skip": skip,
            "limit": limit
        }})
        return self.search(
            db=db,
            tenant_id=tenant_id,
            search_term=search_term,
            search_fields=["email", "display_name"],
            skip=skip,
            limit=limit
        )

    def get_users_by_status(self, db: Session, tenant_id: UUID, status: str, *, skip: int = 0, limit: int = 100) -> List[User]:
        logger.debug("Getting users by status", extra={"extra_fields": {
            "tenant_id": str(tenant_id),
            "status": status,
            "skip": skip,
            "limit": limit
        }})
        return db.query(User).filter(
            and_(
                User.tenant_id == tenant_id,
                User.status == status,
                User.is_deleted == False
            )
        ).order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    def count_users_by_status(self, db: Session, tenant_id: UUID, status: str) -> int:
        logger.debug("Counting users by status", extra={"extra_fields": {
            "tenant_id": str(tenant_id),
            "status": status
        }})
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

    def add_usage_time(self, db: Session, tenant_id: UUID, user_id: UUID, minutes: int) -> Optional[User]:
        logger.debug("Adding usage time", extra={"extra_fields": {
            "tenant_id": str(tenant_id),
            "user_id": str(user_id),
            "minutes": minutes
        }})
        user = self.get_by_id(db, tenant_id, user_id)
        if user:
            user.total_usage_minutes = (user.total_usage_minutes or 0) + minutes
            user.updated_at = datetime.now(timezone.utc)
            db.add(user)
            db.flush()
            db.refresh(user)
        return user

    def get_user_statistics(self, db: Session, tenant_id: UUID, user_id: UUID) -> Dict[str, Any]:
        logger.debug("Getting user statistics", extra={"extra_fields": {
            "tenant_id": str(tenant_id),
            "user_id": str(user_id)
        }})
        user = self.get_by_id(db, tenant_id, user_id)
        if not user:
            return {}

        now = datetime.now(timezone.utc)
        created_at = user.created_at.replace(tzinfo=timezone.utc) if user.created_at.tzinfo is None else user.created_at
        days_since_registration = (now - created_at).days

        days_since_last_login = None
        if user.last_login_at:
            last_login = user.last_login_at.replace(tzinfo=timezone.utc) if user.last_login_at.tzinfo is None else user.last_login_at
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
        logger.debug("Getting tenant user summary", extra={"extra_fields": {
            "tenant_id": str(tenant_id)
        }})
        active_count = self.count_users_by_status(db, tenant_id, "active")
        inactive_count = self.count_users_by_status(db, tenant_id, "inactive") 
        suspended_count = self.count_users_by_status(db, tenant_id, "suspended")

        return {
            "total_users": active_count + inactive_count + suspended_count,
            "active_users": active_count,
            "inactive_users": inactive_count,
            "suspended_users": suspended_count
        }

user_repo = UserRepository()
