# app/schemas/model_permission.py
"""
Pydantic schemas for model permission management.

These schemas define the API contracts for creating, reading, and managing
model permissions with proper validation and comprehensive access control.
"""
from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


class PermissionLevel(str, Enum):
    """Enumeration of permission levels"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class PermissionTargetType(str, Enum):
    """Enumeration of permission target types"""
    USER = "user"
    ORGANIZATION = "organization"
    TEAM = "team"


class ModelPermissionBase(BaseModel):
    """Base model permission schema with common fields"""
    
    permission_level: PermissionLevel = Field(..., description="Level of permission granted")
    is_active: bool = Field(default=True, description="Whether permission is currently active")
    notes: Optional[str] = Field(None, max_length=500, description="Notes about this permission")


class ModelPermissionCreate(ModelPermissionBase):
    """Schema for creating a new model permission"""
    
    model_id: UUID = Field(..., description="ID of the model to grant permission for")
    
    # Target (exactly one must be provided)
    user_id: Optional[UUID] = Field(None, description="Target user ID (for user permissions)")
    organization_id: Optional[UUID] = Field(None, description="Target organization ID (for org permissions)")
    team_id: Optional[UUID] = Field(None, description="Target team ID (for team permissions)")
    
    # Optional scheduling
    valid_from: Optional[datetime] = Field(None, description="When permission becomes valid")
    valid_until: Optional[datetime] = Field(None, description="When permission expires")
    
    @field_validator('permission_level')
    @classmethod
    def validate_permission_level(cls, v: str) -> str:
        """Validate permission level is allowed"""
        if v not in [level.value for level in PermissionLevel]:
            raise ValueError(f"Permission level must be one of: {', '.join([level.value for level in PermissionLevel])}")
        return v
    
    def model_post_init(self, __context: Any) -> None:
        """Validate that exactly one target is specified"""
        targets = [self.user_id, self.organization_id, self.team_id]
        non_none_targets = [t for t in targets if t is not None]
        
        if len(non_none_targets) != 1:
            raise ValueError("Exactly one of user_id, organization_id, or team_id must be specified")
        
        # Validate date ordering
        if self.valid_from and self.valid_until and self.valid_from >= self.valid_until:
            raise ValueError("valid_from must be before valid_until")

    model_config = {
        "json_schema_extra": {
            "example": {
                "model_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "permission_level": "read",
                "notes": "Grant read access for review"
            }
        }
    }


class ModelPermissionUpdate(BaseModel):
    """Schema for updating a model permission"""
    
    permission_level: Optional[PermissionLevel] = Field(None, description="New permission level")
    is_active: Optional[bool] = Field(None, description="Whether to activate/deactivate permission")
    notes: Optional[str] = Field(None, max_length=500, description="Updated notes")
    valid_from: Optional[datetime] = Field(None, description="Updated valid from date")
    valid_until: Optional[datetime] = Field(None, description="Updated valid until date")
    
    def model_post_init(self, __context: Any) -> None:
        """Validate date ordering if both dates are provided"""
        if self.valid_from and self.valid_until and self.valid_from >= self.valid_until:
            raise ValueError("valid_from must be before valid_until")


class ModelPermissionRead(ModelPermissionBase):
    """Schema for reading model permission information"""
    
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    
    # Permission details
    model_id: UUID
    user_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    
    # Scheduling
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    
    # Audit trail
    granted_by_user_id: UUID
    granted_at: datetime
    revoked_by_user_id: Optional[UUID] = None
    revoked_at: Optional[datetime] = None
    
    # Computed fields for convenience
    @computed_field
    @property
    def target_type(self) -> str:
        """Determine the type of permission target"""
        if self.user_id:
            return "user"
        elif self.organization_id:
            return "organization"
        elif self.team_id:
            return "team"
        return "unknown"
    
    @computed_field
    @property
    def target_id(self) -> Optional[UUID]:
        """Get the ID of the permission target"""
        return self.user_id or self.organization_id or self.team_id
    
    @computed_field
    @property
    def is_currently_valid(self) -> bool:
        """Check if permission is currently valid based on date range"""
        now = datetime.utcnow()
        
        if not self.is_active:
            return False
        
        if self.revoked_at:
            return False
            
        if self.valid_from and now < self.valid_from:
            return False
            
        if self.valid_until and now > self.valid_until:
            return False
            
        return True
    
    @computed_field
    @property
    def is_expired(self) -> bool:
        """Check if permission has expired"""
        if not self.valid_until:
            return False
        return datetime.utcnow() > self.valid_until
    
    @computed_field
    @property
    def is_revoked(self) -> bool:
        """Check if permission has been revoked"""
        return self.revoked_at is not None

    model_config = {"from_attributes": True}


class ModelPermissionSummary(BaseModel):
    """Lightweight permission schema for listings"""
    
    id: UUID
    model_id: UUID
    target_type: str
    target_id: UUID
    permission_level: PermissionLevel
    is_active: bool
    is_currently_valid: bool
    granted_at: datetime
    granted_by_user_id: UUID
    revoked_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ModelPermissionListResponse(BaseModel):
    """Paginated response for permission listings"""
    
    permissions: List[ModelPermissionSummary]
    total: int
    skip: int
    limit: int


class PermissionGrantRequest(BaseModel):
    """Schema for granting permissions to multiple targets"""
    
    model_id: UUID = Field(..., description="Model to grant permission for")
    permission_level: PermissionLevel = Field(..., description="Level of permission to grant")
    
    # Multiple targets can be specified
    user_ids: Optional[List[UUID]] = Field(None, description="List of user IDs to grant permission to")
    organization_ids: Optional[List[UUID]] = Field(None, description="List of organization IDs to grant permission to")
    team_ids: Optional[List[UUID]] = Field(None, description="List of team IDs to grant permission to")
    
    # Optional settings applied to all grants
    valid_from: Optional[datetime] = Field(None, description="When permissions become valid")
    valid_until: Optional[datetime] = Field(None, description="When permissions expire")
    notes: Optional[str] = Field(None, max_length=500, description="Notes for all permissions")
    
    def model_post_init(self, __context: Any) -> None:
        """Validate that at least one target is specified"""
        all_targets = (self.user_ids or []) + (self.organization_ids or []) + (self.team_ids or [])
        
        if not all_targets:
            raise ValueError("At least one target (user, organization, or team) must be specified")
        
        # Validate date ordering
        if self.valid_from and self.valid_until and self.valid_from >= self.valid_until:
            raise ValueError("valid_from must be before valid_until")


class PermissionRevokeRequest(BaseModel):
    """Schema for revoking permissions"""
    
    permission_ids: List[UUID] = Field(..., description="List of permission IDs to revoke")
    revocation_reason: Optional[str] = Field(None, max_length=500, description="Reason for revocation")


class ModelPermissionCheck(BaseModel):
    """Schema for checking user permissions on a model"""
    
    model_id: UUID
    user_id: UUID
    check_read: bool = Field(default=True, description="Check read permission")
    check_write: bool = Field(default=False, description="Check write permission")
    check_execute: bool = Field(default=False, description="Check execute permission")
    check_admin: bool = Field(default=False, description="Check admin permission")


class ModelPermissionResult(BaseModel):
    """Schema for permission check results"""
    
    model_id: UUID
    user_id: UUID
    
    # Permission results
    can_read: bool
    can_write: bool
    can_execute: bool
    can_admin: bool
    
    # Permission sources
    permission_sources: Dict[str, str] = Field(default_factory=dict, description="Source of each permission type")
    effective_permissions: List[ModelPermissionRead] = Field(default_factory=list, description="All effective permissions")
    
    # Access context
    has_any_permission: bool
    highest_permission_level: Optional[PermissionLevel] = None


class BulkPermissionResponse(BaseModel):
    """Schema for bulk permission operation responses"""
    
    successful_operations: List[UUID] = Field(default_factory=list, description="IDs of successful operations")
    failed_operations: List[Dict[str, Any]] = Field(default_factory=list, description="Details of failed operations")
    total_requested: int = Field(..., description="Total number of operations requested")
    total_successful: int = Field(..., description="Total number of successful operations")
    total_failed: int = Field(..., description="Total number of failed operations")