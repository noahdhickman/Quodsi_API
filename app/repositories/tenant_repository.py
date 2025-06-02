from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List, Dict, Any
from uuid import UUID
from app.db.models.tenant import Tenant
from app.schemas.tenant import TenantCreate
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class TenantRepository:
    def get_by_id(self, db: Session, id: UUID) -> Optional[Tenant]:
        logger.debug("Getting tenant by ID", extra={"extra_fields": {"tenant_id": str(id)}})
        return db.query(Tenant).filter(
            and_(Tenant.id == id, Tenant.is_deleted == False)
        ).first()

    def get_by_slug(self, db: Session, slug: str) -> Optional[Tenant]:
        logger.debug("Getting tenant by slug", extra={"extra_fields": {"slug": slug}})
        return db.query(Tenant).filter(
            and_(Tenant.slug == slug, Tenant.is_deleted == False)
        ).first()

    def get_by_subdomain(self, db: Session, subdomain: str) -> Optional[Tenant]:
        logger.debug("Getting tenant by subdomain", extra={"extra_fields": {"subdomain": subdomain}})
        return db.query(Tenant).filter(
            and_(Tenant.subdomain == subdomain, Tenant.is_deleted == False)
        ).first()

    def check_slug_availability(self, db: Session, slug: str, exclude_id: Optional[UUID] = None) -> bool:
        logger.debug("Checking slug availability", extra={"extra_fields": {"slug": slug, "exclude_id": str(exclude_id) if exclude_id else None}})
        query = db.query(Tenant.id).filter(
            and_(Tenant.slug == slug, Tenant.is_deleted == False)
        )
        if exclude_id:
            query = query.filter(Tenant.id != exclude_id)
        return query.first() is None

    def check_subdomain_availability(self, db: Session, subdomain: str, exclude_id: Optional[UUID] = None) -> bool:
        logger.debug("Checking subdomain availability", extra={"extra_fields": {"subdomain": subdomain, "exclude_id": str(exclude_id) if exclude_id else None}})
        query = db.query(Tenant.id).filter(
            and_(Tenant.subdomain == subdomain, Tenant.is_deleted == False)
        )
        if exclude_id:
            query = query.filter(Tenant.id != exclude_id)
        return query.first() is None

    def generate_unique_slug(self, db: Session, name: str, exclude_id: Optional[UUID] = None) -> str:
        import re
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
        slug = re.sub(r'\s+', '-', slug.strip())
        slug = re.sub(r'-+', '-', slug).strip('-')
        if len(slug) < 3:
            slug = f"tenant-{slug}"
        original_slug = slug
        counter = 1
        while not self.check_slug_availability(db, slug, exclude_id):
            counter += 1
            slug = f"{original_slug}-{counter}"
        logger.debug("Generated unique slug", extra={"extra_fields": {"generated_slug": slug}})
        return slug

    def generate_unique_subdomain(self, db: Session, name: str, exclude_id: Optional[UUID] = None) -> str:
        import re
        subdomain = re.sub(r'[^a-zA-Z0-9]', '', name.lower())
        if len(subdomain) < 3:
            subdomain = f"tenant{subdomain}"
        if len(subdomain) > 20:
            subdomain = subdomain[:20]
        original_subdomain = subdomain
        counter = 1
        while not self.check_subdomain_availability(db, subdomain, exclude_id):
            counter += 1
            base_length = min(len(original_subdomain), 15)
            subdomain = f"{original_subdomain[:base_length]}{counter}"
        logger.debug("Generated unique subdomain", extra={"extra_fields": {"generated_subdomain": subdomain}})
        return subdomain

    def create(self, db: Session, *, obj_in: TenantCreate) -> Tenant:
        logger.debug("Creating new tenant", extra={"extra_fields": {"name": obj_in.name}})
        try:
            slug = obj_in.slug or self.generate_unique_slug(db, obj_in.name)
            if obj_in.slug and not self.check_slug_availability(db, slug):
                raise ValueError(f"Slug '{slug}' is already taken")
            subdomain = obj_in.subdomain or self.generate_unique_subdomain(db, obj_in.name)
            if obj_in.subdomain and not self.check_subdomain_availability(db, subdomain):
                raise ValueError(f"Subdomain '{subdomain}' is already taken")
            from datetime import datetime, timezone, timedelta
            db_obj = Tenant(
                name=obj_in.name,
                slug=slug,
                subdomain=subdomain,
                plan_type=obj_in.plan_type,
                status=obj_in.status,
                tenant_id=None,
                max_users=getattr(obj_in, 'max_users', None) or 5,
                max_models=getattr(obj_in, 'max_models', None) or 10,
                max_scenarios_per_month=getattr(obj_in, 'max_scenarios_per_month', None) or 100,
                max_storage_gb=getattr(obj_in, 'max_storage_gb', None) or 1.0,
                billing_email=getattr(obj_in, 'billing_email', None)
            )
            if obj_in.plan_type == "trial":
                db_obj.trial_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
                logger.debug("Set trial expiration", extra={"extra_fields": {"trial_expires_at": db_obj.trial_expires_at.isoformat()}})
            db.add(db_obj)
            db.flush()
            db.refresh(db_obj)
            logger.info("Tenant created", extra={"extra_fields": {"tenant_id": str(db_obj.id), "slug": slug, "subdomain": subdomain}})
            return db_obj
        except Exception as e:
            logger.error(f"Failed to create tenant: {str(e)}", exc_info=True, extra={"extra_fields": {"tenant_name": obj_in.name}})
            raise

    def update(self, db: Session, *, db_obj: Tenant, obj_in: Dict[str, Any]) -> Tenant:
        from datetime import datetime, timezone
        logger.debug("Updating tenant", extra={"extra_fields": {"tenant_id": str(db_obj.id)}})
        if "slug" in obj_in and obj_in["slug"] != db_obj.slug:
            if not self.check_slug_availability(db, obj_in["slug"], exclude_id=db_obj.id):
                raise ValueError(f"Slug '{obj_in['slug']}' is already taken")
        if "subdomain" in obj_in and obj_in["subdomain"] != db_obj.subdomain:
            if not self.check_subdomain_availability(db, obj_in["subdomain"], exclude_id=db_obj.id):
                raise ValueError(f"Subdomain '{obj_in['subdomain']}' is already taken")
        protected_fields = {"id", "index_id", "created_at", "tenant_id"}
        for field, value in obj_in.items():
            if field not in protected_fields and hasattr(db_obj, field):
                setattr(db_obj, field, value)
        if "status" in obj_in and obj_in["status"] == "active" and db_obj.status != "active":
            db_obj.activated_at = datetime.now(timezone.utc)
        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        logger.info("Tenant updated", extra={"extra_fields": {"tenant_id": str(db_obj.id)}})
        return db_obj

    def soft_delete(self, db: Session, tenant_id: UUID, id: UUID) -> bool:
        from datetime import datetime, timezone
        logger.debug("Soft deleting tenant", extra={"extra_fields": {"tenant_id": str(id)}})
        db_obj = self.get_by_id(db, id)
        if db_obj:
            db_obj.is_deleted = True
            db_obj.status = "deleted"
            db_obj.updated_at = datetime.now(timezone.utc)
            db.add(db_obj)
            db.flush()
            logger.info("Tenant soft-deleted", extra={"extra_fields": {"tenant_id": str(id)}})
            return True
        return False

# Singleton instance for dependency injection
tenant_repo = TenantRepository()
