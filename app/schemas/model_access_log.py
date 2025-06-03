# app/schemas/model_access_log.py
"""
Pydantic schemas for model access logging.

These schemas define the API contracts for creating, reading, and analyzing
model access logs for comprehensive audit trail and security monitoring.
"""
from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


class AccessType(str, Enum):
    """Enumeration of access types"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    PERMISSION_CHANGE = "permission_change"
    SHARE = "share"
    DOWNLOAD = "download"
    COPY = "copy"
    TEMPLATE_CREATE = "template_create"


class AccessResult(str, Enum):
    """Enumeration of access results"""
    SUCCESS = "success"
    DENIED = "denied"
    ERROR = "error"
    PARTIAL = "partial"


class ModelAccessLogBase(BaseModel):
    """Base access log schema with common fields"""
    
    access_type: AccessType = Field(..., description="Type of access attempted")
    access_result: AccessResult = Field(..., description="Result of the access attempt")
    permission_source: Optional[str] = Field(None, max_length=50, description="Source of permission used")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional access details (JSON)")


class ModelAccessLogCreate(ModelAccessLogBase):
    """Schema for creating a new access log entry"""
    
    model_id: UUID = Field(..., description="ID of the model accessed")
    user_id: UUID = Field(..., description="ID of the user performing access")
    
    # Session context
    session_id: Optional[str] = Field(None, max_length=255, description="User session identifier")
    ip_address: Optional[str] = Field(None, max_length=45, description="Client IP address")
    user_agent: Optional[str] = Field(None, max_length=500, description="Client user agent string")
    
    # Request context
    endpoint: Optional[str] = Field(None, max_length=100, description="API endpoint accessed")
    request_method: Optional[str] = Field(None, max_length=10, description="HTTP method used")
    
    @field_validator('access_type')
    @classmethod
    def validate_access_type(cls, v: str) -> str:
        """Validate access type is allowed"""
        if v not in [access_type.value for access_type in AccessType]:
            raise ValueError(f"Access type must be one of: {', '.join([access_type.value for access_type in AccessType])}")
        return v
    
    @field_validator('access_result')
    @classmethod
    def validate_access_result(cls, v: str) -> str:
        """Validate access result is allowed"""
        if v not in [result.value for result in AccessResult]:
            raise ValueError(f"Access result must be one of: {', '.join([result.value for result in AccessResult])}")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "model_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "access_type": "read",
                "access_result": "success",
                "permission_source": "direct",
                "session_id": "sess_123456789",
                "ip_address": "192.168.1.100",
                "endpoint": "/api/models/550e8400-e29b-41d4-a716-446655440000"
            }
        }
    }


class ModelAccessLogRead(ModelAccessLogBase):
    """Schema for reading access log information"""
    
    id: UUID
    tenant_id: UUID
    created_at: datetime
    
    # Access details
    model_id: UUID
    user_id: UUID
    
    # Session context
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Request context
    endpoint: Optional[str] = None
    request_method: Optional[str] = None
    
    # Computed fields for convenience
    @computed_field
    @property
    def was_successful(self) -> bool:
        """Check if access was successful"""
        return self.access_result == AccessResult.SUCCESS
    
    @computed_field
    @property
    def was_denied(self) -> bool:
        """Check if access was denied"""
        return self.access_result == AccessResult.DENIED
    
    @computed_field
    @property
    def is_security_relevant(self) -> bool:
        """Check if this log entry is security-relevant"""
        return (
            self.access_result == AccessResult.DENIED or
            self.access_type in [AccessType.PERMISSION_CHANGE, AccessType.DELETE] or
            self.permission_source is None
        )

    model_config = {"from_attributes": True}


class ModelAccessLogSummary(BaseModel):
    """Lightweight access log schema for listings"""
    
    id: UUID
    model_id: UUID
    user_id: UUID
    access_type: AccessType
    access_result: AccessResult
    permission_source: Optional[str] = None
    created_at: datetime
    ip_address: Optional[str] = None

    model_config = {"from_attributes": True}


class ModelAccessLogListResponse(BaseModel):
    """Paginated response for access log listings"""
    
    access_logs: List[ModelAccessLogSummary]
    total: int
    skip: int
    limit: int


class AccessLogQuery(BaseModel):
    """Schema for querying access logs with filters"""
    
    # Basic filters
    model_id: Optional[UUID] = Field(None, description="Filter by model ID")
    user_id: Optional[UUID] = Field(None, description="Filter by user ID")
    access_type: Optional[AccessType] = Field(None, description="Filter by access type")
    access_result: Optional[AccessResult] = Field(None, description="Filter by access result")
    
    # Date range filters
    start_date: Optional[datetime] = Field(None, description="Filter logs after this date")
    end_date: Optional[datetime] = Field(None, description="Filter logs before this date")
    
    # Context filters
    ip_address: Optional[str] = Field(None, description="Filter by IP address")
    session_id: Optional[str] = Field(None, description="Filter by session ID")
    permission_source: Optional[str] = Field(None, description="Filter by permission source")
    
    # Security-focused filters
    denied_only: bool = Field(default=False, description="Show only denied access attempts")
    security_relevant_only: bool = Field(default=False, description="Show only security-relevant events")
    
    # Pagination
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of records to return")
    
    def model_post_init(self, __context: Any) -> None:
        """Validate date range"""
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")


class AccessLogAnalytics(BaseModel):
    """Schema for access log analytics and statistics"""
    
    # Time period
    period_start: datetime
    period_end: datetime
    
    # Overall statistics
    total_accesses: int
    successful_accesses: int
    denied_accesses: int
    error_accesses: int
    
    # User statistics
    unique_users: int
    most_active_users: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Model statistics
    unique_models: int
    most_accessed_models: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Access type breakdown
    access_type_counts: Dict[str, int] = Field(default_factory=dict)
    
    # Security metrics
    failed_access_attempts: int
    suspicious_activity_count: int
    unique_ip_addresses: int
    
    # Computed metrics
    @computed_field
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_accesses == 0:
            return 0.0
        return (self.successful_accesses / self.total_accesses) * 100
    
    @computed_field
    @property
    def denial_rate(self) -> float:
        """Calculate denial rate percentage"""
        if self.total_accesses == 0:
            return 0.0
        return (self.denied_accesses / self.total_accesses) * 100


class UserAccessSummary(BaseModel):
    """Schema for user-specific access summary"""
    
    user_id: UUID
    model_id: UUID
    
    # Access counts
    total_accesses: int
    successful_accesses: int
    denied_accesses: int
    
    # Access types
    read_accesses: int
    write_accesses: int
    execute_accesses: int
    other_accesses: int
    
    # Timeline
    first_access: Optional[datetime] = None
    last_access: Optional[datetime] = None
    last_successful_access: Optional[datetime] = None
    
    # Permission context
    current_permission_level: Optional[str] = None
    primary_permission_source: Optional[str] = None


class ModelAccessSummary(BaseModel):
    """Schema for model-specific access summary"""
    
    model_id: UUID
    
    # Access statistics
    total_accesses: int
    unique_users: int
    successful_accesses: int
    denied_accesses: int
    
    # Popular operations
    most_common_access_type: Optional[str] = None
    access_type_distribution: Dict[str, int] = Field(default_factory=dict)
    
    # Timeline
    first_access: Optional[datetime] = None
    last_access: Optional[datetime] = None
    
    # Top users by access count
    top_users: List[Dict[str, Any]] = Field(default_factory=list)


class SecurityAlert(BaseModel):
    """Schema for security alerts based on access patterns"""
    
    alert_type: str = Field(..., description="Type of security alert")
    severity: str = Field(..., description="Alert severity level")
    description: str = Field(..., description="Human-readable alert description")
    
    # Related entities
    user_id: Optional[UUID] = None
    model_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    
    # Alert details
    trigger_event: ModelAccessLogRead
    related_events: List[ModelAccessLogSummary] = Field(default_factory=list)
    event_count: int = Field(default=1, description="Number of related events")
    
    # Metadata
    first_occurrence: datetime
    last_occurrence: datetime
    created_at: datetime


class BulkAccessLogResponse(BaseModel):
    """Schema for bulk access log operation responses"""
    
    created_logs: List[UUID] = Field(default_factory=list, description="IDs of successfully created logs")
    failed_logs: List[Dict[str, Any]] = Field(default_factory=list, description="Details of failed log entries")
    total_requested: int = Field(..., description="Total number of log entries requested")
    total_created: int = Field(..., description="Total number of successfully created entries")
    total_failed: int = Field(..., description="Total number of failed entries")