# app/api/routers/tenant.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.repositories.tenant_repository import TenantRepository
from app.schemas.tenant import TenantRead, TenantSummary
from app.api.response_helpers import create_success_response, create_error_response
from app.api.deps import get_current_user_mock, MockCurrentUser
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/tenants")


@router.get("/", response_model=dict)
async def list_tenants(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_db),
) -> dict:
    """
    List all tenants in the system.
    
    **Development/Testing Use**: Get tenant IDs for mock authentication headers.
    
    Example: Use X-Mock-Tenant-Id header with any tenant ID from this list.
    """
    try:
        from app.db.models.tenant import Tenant
        
        # Get all tenants (not filtered by current tenant for development purposes)
        tenants = db.query(Tenant).filter(
            Tenant.is_deleted == False
        ).order_by(Tenant.created_at.desc()).offset(skip).limit(limit).all()
        
        total = db.query(Tenant).filter(
            Tenant.is_deleted == False
        ).count()
        
        # Convert to summary format for easier consumption
        tenant_summaries = [
            TenantSummary.model_validate(tenant) for tenant in tenants
        ]
        
        return create_success_response(
            data={
                "tenants": [summary.model_dump() for summary in tenant_summaries],
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve tenants: {str(e)}", exc_info=True)
        return create_error_response(
            code="INTERNAL_ERROR",
            message="Failed to retrieve tenants"
        )


@router.get("/{tenant_id}", response_model=dict)
async def get_tenant(
    tenant_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get detailed information about a specific tenant.
    
    **Development/Testing Use**: Get full tenant details for testing purposes.
    """
    try:
        tenant_repo = TenantRepository()
        tenant = tenant_repo.get_by_id(db=db, id=tenant_id)
        
        if not tenant:
            return create_error_response(
                code="NOT_FOUND",
                message=f"Tenant {tenant_id} not found"
            )
        
        # Convert to full read schema
        tenant_data = TenantRead.model_validate(tenant)
        
        return create_success_response(
            data={"tenant": tenant_data.model_dump()}
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve tenant {tenant_id}: {str(e)}", exc_info=True)
        return create_error_response(
            code="INTERNAL_ERROR",
            message="Failed to retrieve tenant"
        )


@router.get("/me/info", response_model=dict)
async def get_current_tenant_info(
    request: Request,
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get information about the current user's tenant.
    
    **Use Case**: Get details about the tenant context for the current mock user.
    """
    try:
        tenant_repo = TenantRepository()
        tenant = tenant_repo.get_by_id(db=db, id=current_user.tenant_id)
        
        if not tenant:
            return create_error_response(
                code="NOT_FOUND",
                message=f"Current tenant {current_user.tenant_id} not found"
            )
        
        # Convert to full read schema
        tenant_data = TenantRead.model_validate(tenant)
        
        return create_success_response(
            data={
                "tenant": tenant_data.model_dump(),
                "current_user": {
                    "user_id": str(current_user.user_id),
                    "email": current_user.email,
                    "display_name": current_user.display_name
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve current tenant info: {str(e)}", exc_info=True)
        return create_error_response(
            code="INTERNAL_ERROR",
            message="Failed to retrieve current tenant information"
        )


@router.get("/summary/stats", response_model=dict)
async def get_tenant_summary_stats(
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get summary statistics about tenants in the system.
    
    **Development/Testing Use**: Overview of tenant data for development insights.
    """
    try:
        from app.db.models.tenant import Tenant
        from app.db.models.user import User
        from app.db.models.organization import Organization
        from sqlalchemy import func
        
        # Get tenant counts by status
        tenant_stats = db.query(
            Tenant.status,
            func.count(Tenant.id).label('count')
        ).filter(
            Tenant.is_deleted == False
        ).group_by(Tenant.status).all()
        
        # Get tenant counts by plan type
        plan_stats = db.query(
            Tenant.plan_type,
            func.count(Tenant.id).label('count')
        ).filter(
            Tenant.is_deleted == False
        ).group_by(Tenant.plan_type).all()
        
        # Get total users and organizations
        total_users = db.query(func.count(User.id)).filter(User.is_deleted == False).scalar()
        total_orgs = db.query(func.count(Organization.id)).filter(Organization.is_deleted == False).scalar()
        total_tenants = db.query(func.count(Tenant.id)).filter(Tenant.is_deleted == False).scalar()
        
        return create_success_response(
            data={
                "total_tenants": total_tenants,
                "total_users": total_users,
                "total_organizations": total_orgs,
                "tenants_by_status": {stat.status: stat.count for stat in tenant_stats},
                "tenants_by_plan": {stat.plan_type: stat.count for stat in plan_stats}
            },
            message="Tenant summary statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve tenant stats: {str(e)}", exc_info=True)
        return create_error_response(
            code="INTERNAL_ERROR",
            message="Failed to retrieve tenant statistics"
        )