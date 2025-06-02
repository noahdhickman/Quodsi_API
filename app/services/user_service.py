from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone
from app.db.models.user import User
from app.repositories.user_repository import user_repo
from app.repositories.tenant_repository import tenant_repo
from app.schemas.user import (
    UserProfileUpdate,
    AuthenticationResult,
    UserResponse,
    UserActivitySummary,
)

# Add this import with your other imports at the top
from app.repositories.user_session_repository import UserSessionRepository
from app.db.models.user_session import UserSession


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
        self.session_repo = UserSessionRepository()

    # === Authentication & Session Management ===

    def record_session_start(
        self,
        user_id: UUID,
        tenant_id: UUID,
        client_type: str,
        session_type: str = "web",
        client_info: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> UserSession:

        logger.info(
            "Starting new user session",
            extra={
                "extra_fields": {
                    "user_id": str(user_id),
                    "tenant_id": str(tenant_id),
                    "client_type": client_type,
                    "session_type": session_type,
                    "operation": "record_session_start",
                }
            },
        )

        try:
            # Start the new session
            new_session = self.session_repo.start_session(
                db=self.db,
                user_id=user_id,
                tenant_id=tenant_id,
                client_type=client_type,
                session_type=session_type,
                client_info=client_info,
                ip_address=ip_address,
            )

            # Update user's session tracking fields
            now = datetime.utcnow()
            user_updates = {"last_session_start": now, "last_active_at": now}

            # Update user record
            user = self.user_repo.get_by_id(self.db, tenant_id, user_id)
            if user:
                for key, value in user_updates.items():
                    if hasattr(user, key):
                        setattr(user, key, value)

            self.db.commit()

            logger.info(
                "User session started successfully",
                extra={
                    "extra_fields": {
                        "user_id": str(user_id),
                        "session_id": str(new_session.id),
                        "operation": "record_session_start",
                        "status": "success",
                    }
                },
            )

            return new_session

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Failed to start user session: {str(e)}",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "user_id": str(user_id),
                        "tenant_id": str(tenant_id),
                        "operation": "record_session_start",
                        "status": "failed",
                        "error_type": type(e).__name__,
                    }
                },
            )
            raise e

    def record_session_end(
        self, session_id: UUID, tenant_id: UUID, user_id: Optional[UUID] = None
    ) -> Optional[UserSession]:
        """
        End a user session and update user's total usage.

        Args:
            session_id: ID of the session to end
            tenant_id: Tenant ID for isolation
            user_id: Optional user ID (for additional validation)

        Returns:
            The ended UserSession object, or None if not found
        """
        logger.info(
            "Ending user session",
            extra={
                "extra_fields": {
                    "session_id": str(session_id),
                    "tenant_id": str(tenant_id),
                    "user_id": str(user_id) if user_id else None,
                    "operation": "record_session_end",
                }
            },
        )

        try:
            # End the session
            ended_session = self.session_repo.end_session(
                db=self.db, session_id=session_id, tenant_id=tenant_id
            )

            if ended_session and ended_session.duration_minutes:
                # Update user's total usage minutes
                user = self.user_repo.get_by_id(
                    self.db, tenant_id, ended_session.user_id
                )

                if user:
                    current_total = getattr(user, "total_usage_minutes", 0) or 0
                    new_total = current_total + ended_session.duration_minutes

                    if hasattr(user, "total_usage_minutes"):
                        user.total_usage_minutes = new_total

                    logger.info(
                        "Updated user total usage minutes",
                        extra={
                            "extra_fields": {
                                "user_id": str(ended_session.user_id),
                                "session_duration": ended_session.duration_minutes,
                                "new_total_usage": new_total,
                                "operation": "record_session_end",
                            }
                        },
                    )

            self.db.commit()

            logger.info(
                "User session ended successfully",
                extra={
                    "extra_fields": {
                        "session_id": str(session_id),
                        "duration_minutes": (
                            ended_session.duration_minutes if ended_session else None
                        ),
                        "operation": "record_session_end",
                        "status": "success",
                    }
                },
            )

            return ended_session

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Failed to end user session: {str(e)}",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "session_id": str(session_id),
                        "tenant_id": str(tenant_id),
                        "operation": "record_session_end",
                        "status": "failed",
                        "error_type": type(e).__name__,
                    }
                },
            )
            raise e

    def get_user_active_sessions(
        self, user_id: UUID, tenant_id: UUID
    ) -> List[UserSession]:
        """
        Get all active sessions for a user.

        Args:
            user_id: ID of the user
            tenant_id: Tenant ID for isolation

        Returns:
            List of active UserSession objects
        """
        return self.session_repo.get_active_sessions_for_user(
            self.db, user_id, tenant_id
        )

    def get_user_session_history(
        self, user_id: UUID, tenant_id: UUID, skip: int = 0, limit: int = 50
    ) -> tuple[List[UserSession], int]:
        """
        Get paginated session history for a user.

        Args:
            user_id: ID of the user
            tenant_id: Tenant ID for isolation
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            Tuple of (sessions_list, total_count)
        """
        sessions = self.session_repo.get_session_history_for_user(
            self.db, user_id, tenant_id, skip, limit
        )

        total_count = self.session_repo.count_sessions_for_user(
            self.db, user_id, tenant_id
        )

        return sessions, total_count

    def end_all_user_sessions(
        self, user_id: UUID, tenant_id: UUID
    ) -> List[UserSession]:
        """
        End all active sessions for a user (logout from all devices).

        Args:
            user_id: ID of the user
            tenant_id: Tenant ID for isolation

        Returns:
            List of ended UserSession objects
        """
        logger.info(
            "Ending all user sessions",
            extra={
                "extra_fields": {
                    "user_id": str(user_id),
                    "tenant_id": str(tenant_id),
                    "operation": "end_all_user_sessions",
                }
            },
        )

        try:
            ended_sessions = self.session_repo.end_all_active_sessions_for_user(
                self.db, user_id, tenant_id
            )

            # Update user's total usage minutes with all ended sessions
            if ended_sessions:
                user = self.user_repo.get_by_id(self.db, tenant_id, user_id)
                if user:
                    total_additional_minutes = sum(
                        session.duration_minutes or 0 for session in ended_sessions
                    )
                    current_total = getattr(user, "total_usage_minutes", 0) or 0
                    new_total = current_total + total_additional_minutes

                    if hasattr(user, "total_usage_minutes"):
                        user.total_usage_minutes = new_total

                    logger.info(
                        "Updated user total usage after ending all sessions",
                        extra={
                            "extra_fields": {
                                "user_id": str(user_id),
                                "sessions_ended": len(ended_sessions),
                                "additional_minutes": total_additional_minutes,
                                "new_total_usage": new_total,
                                "operation": "end_all_user_sessions",
                            }
                        },
                    )

            self.db.commit()

            logger.info(
                "All user sessions ended successfully",
                extra={
                    "extra_fields": {
                        "user_id": str(user_id),
                        "sessions_ended": len(ended_sessions),
                        "operation": "end_all_user_sessions",
                        "status": "success",
                    }
                },
            )

            return ended_sessions

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Failed to end all user sessions: {str(e)}",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "user_id": str(user_id),
                        "tenant_id": str(tenant_id),
                        "operation": "end_all_user_sessions",
                        "status": "failed",
                        "error_type": type(e).__name__,
                    }
                },
            )
            raise e

    def get_session_by_id(
        self, session_id: UUID, tenant_id: UUID
    ) -> Optional[UserSession]:
        """
        Get a specific session by ID.

        Args:
            session_id: ID of the session
            tenant_id: Tenant ID for isolation

        Returns:
            UserSession object or None if not found
        """
        return self.session_repo.get_session_by_id(self.db, session_id, tenant_id)

    def authenticate_user(
        self, identity_provider: str, identity_provider_id: str
    ) -> AuthenticationResult:
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
                    requires_setup=True,
                )

            # Step 2: Validate user status
            if user.status != "active":
                return AuthenticationResult(
                    success=False,
                    message=f"User account is {user.status}. Please contact support.",
                    requires_setup=False,
                )

            # Step 3: Validate tenant status
            tenant = self.tenant_repo.get_by_id(self.db, user.tenant_id)
            if not tenant or tenant.status not in ["active", "trial"]:
                return AuthenticationResult(
                    success=False,
                    message="Organization account is not active. Please contact support.",
                    requires_setup=False,
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
                total_usage_minutes=getattr(user, "total_usage_minutes", 0) or 0,
                last_login_at=user.last_login_at,
                last_active_at=getattr(user, "last_active_at", None),
                created_at=user.created_at,
                updated_at=user.updated_at,
                tenant_id=user.tenant_id,
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
                    "plan_type": tenant.plan_type,
                },
                message="Authentication successful",
                requires_setup=False,
            )

        except Exception as e:
            # Rollback any changes on error
            self.db.rollback()
            return AuthenticationResult(
                success=False,
                message=f"Authentication failed: {str(e)}",
                requires_setup=False,
            )

    def track_user_session(
        self, tenant_id: UUID, user_id: UUID, session_minutes: int
    ) -> bool:
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

    def get_user_profile(
        self, tenant_id: UUID, user_id: UUID
    ) -> Optional[UserResponse]:
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
            total_usage_minutes=getattr(user, "total_usage_minutes", 0) or 0,
            last_login_at=user.last_login_at,
            last_active_at=getattr(user, "last_active_at", None),
            created_at=user.created_at,
            updated_at=user.updated_at,
            tenant_id=user.tenant_id,
        )

    def update_user_profile(
        self, tenant_id: UUID, user_id: UUID, profile_update: UserProfileUpdate
    ) -> Optional[UserResponse]:
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
            updated_user = self.user_repo.update(
                self.db, db_obj=user, obj_in=update_data
            )

            # Commit changes
            self.db.commit()

            # Return updated profile
            return self.get_user_profile(tenant_id, user_id)

        except Exception as e:
            self.db.rollback()
            raise e

    def deactivate_user(
        self, tenant_id: UUID, user_id: UUID, reason: str = "deactivated"
    ) -> bool:
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
                "user_metadata": f'{{"deactivation_reason": "{reason}", "deactivated_at": "{datetime.now(timezone.utc).isoformat()}"}}',
            }

            self.user_repo.update(self.db, db_obj=user, obj_in=update_data)
            self.db.commit()

            return True

        except Exception:
            self.db.rollback()
            return False

    # === Basic Analytics ===

    def get_user_activity_summary(
        self, tenant_id: UUID, user_id: UUID
    ) -> Optional[UserActivitySummary]:
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

        # Calculate if user is recently active (activity within last 7 days)
        is_recently_active = False
        if stats.get("days_since_last_login") is not None:
            is_recently_active = stats["days_since_last_login"] <= 7

        # Determine engagement level
        engagement_level = self._calculate_engagement_level(stats)

        return UserActivitySummary(
            user_id=str(user_id),
            total_logins=stats["login_count"],
            total_usage_minutes=stats["total_usage_minutes"],
            last_login_at=None,  # Would need to parse from stats if available
            days_since_registration=stats["days_since_registration"],
            is_recently_active=is_recently_active,
            engagement_level=engagement_level,
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

    def get_user_by_id_in_tenant(self, user_id: str, tenant_id: UUID) -> Optional[User]:
        """Get user by ID within a specific tenant"""
        print(f"Inside get_user_by_id_in_tenant method")
        print(f"  user_id type: {type(user_id)}, value: {user_id}")
        print(f"  tenant_id type: {type(tenant_id)}, value: {tenant_id}")

        try:
            # Try converting string UUID to UUID object if needed
            if isinstance(user_id, str):
                print(f"  Converting user_id string to UUID")
                try:
                    user_id_uuid = UUID(user_id)
                    print(f"  Converted user_id: {user_id_uuid}")
                except ValueError as e:
                    print(f"  ERROR converting user_id to UUID: {str(e)}")
                    return None
            else:
                user_id_uuid = user_id

            # Instead of direct query, use the user_repo which is designed
            # to work with SQL Server's UNIQUEIDENTIFIER fields
            print(f"  Using user_repo to find user")
            # Most user repos have a get_by_tenant method or similar
            try:
                # Try to use a repository method if available
                if hasattr(self.user_repo, "get_by_tenant"):
                    user = self.user_repo.get_by_tenant(
                        self.db, tenant_id, user_id_uuid
                    )
                    print(f"  Found user with get_by_tenant: {user}")
                else:
                    # Fallback to direct query with proper SQL Server handling
                    user = (
                        self.db.query(User)
                        .filter(User.id == user_id_uuid, User.tenant_id == tenant_id)
                        .first()
                    )
                    print(f"  Found user with direct query: {user}")

                return user
            except Exception as repo_error:
                print(f"  Error in repository: {str(repo_error)}")
                # Try one more approach - filter manually
                all_tenant_users = (
                    self.db.query(User).filter(User.tenant_id == tenant_id).all()
                )
                print(f"  Got {len(all_tenant_users)} users in tenant")

                # Find the user with matching ID (string comparison)
                for u in all_tenant_users:
                    if str(u.id).lower() == str(user_id).lower():
                        print(f"  Found user by string comparison: {u}")
                        return u

                return None

        except Exception as e:
            print(f"  ERROR in get_user_by_id_in_tenant: {type(e).__name__}: {str(e)}")
            import traceback

            print(traceback.format_exc())
            raise e

    def search_users_in_tenant(
        self,
        tenant_id: UUID,
        search_term: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[User], int]:
        """
        Search users within a tenant with filtering and pagination.

        Returns tuple of (users, total_count)
        """
        query = self.db.query(User).filter(User.tenant_id == tenant_id)

        # Add is_deleted filter if it exists
        if hasattr(User, "is_deleted"):
            query = query.filter(User.is_deleted == False)

        # Apply search term filter
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                (User.email.ilike(search_pattern))
                | (User.display_name.ilike(search_pattern))
            )

        # Apply role filter
        if role:
            query = query.filter(User.role == role)

        # Apply active status filter
        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination
        users = query.order_by(User.created_at).offset(offset).limit(limit).all()

        return users, total_count

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash - implement proper password hashing"""
        # Placeholder - implement with bcrypt or similar
        return password == password_hash  # TEMPORARY - NOT SECURE

    def _hash_password(self, password: str) -> str:
        """Hash password - implement proper password hashing"""
        # Placeholder - implement with bcrypt or similar
        return password  # TEMPORARY - NOT SECURE

    # === Tenant-Level User Management ===

    def get_tenant_user_overview(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Get overview of all users in a tenant for admin purposes.

        Args:
            tenant_id: Tenant UUID for isolation

        Returns:
            Dictionary with tenant user overview
        """
        try:
            # Get tenant user summary
            summary = self.user_repo.get_tenant_user_summary(self.db, tenant_id)

            # Get recent users
            recent_users = self.user_repo.get_users_by_status(
                self.db, tenant_id, "active", limit=10
            )

            # Calculate engagement distribution
            all_users = self.user_repo.get_all(self.db, tenant_id, limit=1000)
            engagement_distribution = self._calculate_engagement_distribution(
                tenant_id, all_users
            )

            return {
                "summary": summary,
                "recent_users": [
                    {
                        "id": str(user.id),
                        "email": user.email,
                        "display_name": user.display_name,
                        "status": user.status,
                        "last_login_at": user.last_login_at,
                        "created_at": user.created_at,
                    }
                    for user in recent_users
                ],
                "engagement_distribution": engagement_distribution,
            }

        except Exception:
            return {"summary": {}, "recent_users": [], "engagement_distribution": {}}

    def _calculate_engagement_distribution(
        self, tenant_id: UUID, users: List[User]
    ) -> Dict[str, int]:
        """
        Calculate engagement level distribution for tenant users.

        Args:
            tenant_id: Tenant UUID for isolation
            users: List of users to analyze

        Returns:
            Dictionary with engagement level counts
        """
        distribution = {"high": 0, "medium": 0, "low": 0, "inactive": 0}

        for user in users:
            stats = self.user_repo.get_user_statistics(self.db, tenant_id, user.id)
            if stats:
                engagement_level = self._calculate_engagement_level(stats)
                distribution[engagement_level] += 1

        return distribution

    def get_tenant_user_analytics(
        self, tenant_id: UUID, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive tenant user analytics for specified period.

        Args:
            tenant_id: Tenant UUID for isolation
            days: Number of days to analyze

        Returns:
            Dictionary with tenant analytics
        """
        try:
            from datetime import timedelta

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            # Get all users
            all_users = self.user_repo.get_all(self.db, tenant_id, limit=1000)

            # Calculate metrics
            total_users = len(all_users)
            active_users = len([u for u in all_users if u.status == "active"])

            # Calculate activity metrics
            total_logins = sum(u.login_count or 0 for u in all_users)
            total_usage = sum(
                getattr(u, "total_usage_minutes", 0) or 0 for u in all_users
            )

            # Calculate averages
            avg_logins_per_user = total_logins / max(total_users, 1)
            avg_usage_per_user = total_usage / max(total_users, 1)

            return {
                "period_days": days,
                "total_users": total_users,
                "active_users": active_users,
                "total_logins": total_logins,
                "total_usage_minutes": total_usage,
                "avg_logins_per_user": round(avg_logins_per_user, 2),
                "avg_usage_per_user": round(avg_usage_per_user, 2),
                "analysis_date": datetime.now(timezone.utc).isoformat(),
            }

        except Exception:
            return {
                "period_days": days,
                "total_users": 0,
                "active_users": 0,
                "total_logins": 0,
                "total_usage_minutes": 0,
                "avg_logins_per_user": 0,
                "avg_usage_per_user": 0,
                "analysis_date": datetime.now(timezone.utc).isoformat(),
            }

    def get_user_insights(
        self, tenant_id: UUID, user_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive user insights and recommendations.

        Args:
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to analyze

        Returns:
            Dictionary with detailed user insights or None if not found
        """
        activity_summary = self.get_user_activity_summary(tenant_id, user_id)
        if not activity_summary:
            return None

        # Generate usage patterns
        usage_patterns = self._analyze_usage_patterns(tenant_id, user_id)

        # Generate recommendations
        recommendations = self._generate_user_recommendations(
            activity_summary, usage_patterns
        )

        return {
            "user_id": str(user_id),
            "activity_summary": {
                "total_logins": activity_summary.total_logins,
                "total_usage_minutes": activity_summary.total_usage_minutes,
                "days_since_registration": activity_summary.days_since_registration,
                "engagement_level": activity_summary.engagement_level,
                "is_recently_active": activity_summary.is_recently_active,
            },
            "usage_patterns": usage_patterns,
            "recommendations": recommendations,
        }

    def _analyze_usage_patterns(self, tenant_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """
        Analyze user usage patterns.

        Args:
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to analyze

        Returns:
            Dictionary with usage pattern insights
        """
        stats = self.user_repo.get_user_statistics(self.db, tenant_id, user_id)

        return {
            "avg_session_length": stats.get("total_usage_minutes", 0)
            / max(stats.get("login_count", 1), 1),
            "login_frequency": "weekly" if stats.get("login_count", 0) > 0 else "never",
            "most_active_time": "business_hours",  # Would be calculated from actual session data
            "usage_trend": "stable",  # Would be calculated from historical data
        }

    def _generate_user_recommendations(
        self, activity_summary: UserActivitySummary, usage_patterns: Dict[str, Any]
    ) -> List[str]:
        """
        Generate personalized recommendations for the user.

        Args:
            activity_summary: User activity summary
            usage_patterns: User usage patterns

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if activity_summary.engagement_level == "low":
            recommendations.append(
                "Try exploring more features to get the most value from the platform"
            )
            recommendations.append(
                "Consider setting up regular usage sessions to build engagement"
            )

        if activity_summary.engagement_level == "inactive":
            recommendations.append(
                "Welcome back! Check out what's new since your last visit"
            )
            recommendations.append(
                "Complete your profile setup to personalize your experience"
            )

        if activity_summary.total_logins < 5:
            recommendations.append(
                "Complete the getting started guide to learn key features"
            )

        if usage_patterns["avg_session_length"] < 10:
            recommendations.append(
                "Take time to explore features more deeply in each session"
            )

        return recommendations

    def change_user_password(
        self, user_id: UUID, current_password: str, new_password: str
    ) -> bool:
        """
        Change a user's password after verifying the current password.

        Returns True if successful, False if current password is incorrect.
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Verify current password (you'll need to implement password hashing)
        # For now, this is a placeholder - you should use proper password hashing
        if not self._verify_password(current_password, user.password_hash):
            return False

        # Hash new password and update
        user.password_hash = self._hash_password(new_password)
        user.updated_at = datetime.utcnow()

        self.db.commit()
        return True


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
