# User Auditing and Security Database Schema (Multi-Tenant with BaseEntity)

This document outlines the auditing and security database schema for Quodsi's user management system. These tables provide comprehensive event tracking, compliance, and security monitoring capabilities across all user management functions.

**Prerequisites**: This schema depends on the tables defined in:
- `000_User_Core_Management_Tables.md`
- `001_User_Organization_Management.md`
- `002_User_Team_Management.md`

**BaseEntity Standard Fields**:
Each table includes the following fields from `BaseEntity` (see `000_User_Core_Management_Tables.md` for details):
* `id`, `index_id`, `tenant_id`, `created_at`, `updated_at`, `is_deleted`

## Implementation Priority

These tables should be implemented **last** after all other user management tables:

1. **`audit_logs`** - Comprehensive event tracking for security and compliance

## Auditing and Security Tables

### `audit_logs`
Comprehensive event tracking for security, compliance, and operational monitoring.

| Column             | Type              | Constraints                               | Description                                          |
| :----------------- | :---------------- | :---------------------------------------- | :--------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Log entry identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NULL, FK to `tenants.id`* | *Tenant context of event, NULL for system (BaseEntity)*|
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Timestamp of the audit event (BaseEntity `created_at`)*|
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Usually same as created_at (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity, usually not used)* |
| `user_id`          | UNIQUEIDENTIFIER  | NULL, FK to `users.id`                    | Reference to user (null for system events)           |
| `event_type`       | VARCHAR(100)      | NOT NULL                                  | Event type (login, logout, simulation_run, etc.)     |
| `event_category`   | VARCHAR(50)       | NOT NULL, DEFAULT 'user_action'           | Event category (authentication, user_management, etc.) |
| `ip_address`       | VARCHAR(45)       | NULL                                      | User's IP address                                    |
| `user_agent`       | NVARCHAR(MAX)     | NULL                                      | User's browser/client info                           |
| `session_id`       | UNIQUEIDENTIFIER  | NULL, FK to `user_sessions.id`            | Reference to user session                            |
| `resource_type`    | VARCHAR(100)      | NULL                                      | Type of resource affected                            |
| `resource_id`      | VARCHAR(255)      | NULL                                      | Identifier of resource affected                      |
| `action`           | VARCHAR(50)       | NOT NULL                                  | Action performed (view, create, update, delete)      |
| `status`           | VARCHAR(50)       | NOT NULL                                  | Outcome (success, failure, partial)                 |
| `error_code`       | VARCHAR(50)       | NULL                                      | Error code if status is failure                      |
| `details`          | NVARCHAR(MAX)     | NULL                                      | Additional context information (JSON data)           |
| `before_state`     | NVARCHAR(MAX)     | NULL                                      | State before change (JSON data)                     |
| `after_state`      | NVARCHAR(MAX)     | NULL                                      | State after change (JSON data)                      |
| `related_entity_id`| UNIQUEIDENTIFIER  | NULL                                      | Optional reference to another entity                 |
| `client_type`      | VARCHAR(50)       | NULL                                      | Client application (lucidchart, standalone, api)    |
| `request_id`       | VARCHAR(100)      | NULL                                      | Request correlation ID                               |

**Indexes:**
* `ix_audit_logs_index_id` CLUSTERED on `index_id`
* `ix_audit_logs_id` UNIQUE NONCLUSTERED on `id`
* `ix_audit_logs_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_audit_logs_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_audit_logs_tenant_timestamp` NONCLUSTERED on (`tenant_id`, `created_at` DESC)
* `ix_audit_logs_tenant_user` NONCLUSTERED on (`tenant_id`, `user_id`) WHERE `user_id` IS NOT NULL
* `ix_audit_logs_event_type` NONCLUSTERED on (`tenant_id`, `event_type`, `created_at` DESC)
* `ix_audit_logs_event_category` NONCLUSTERED on (`tenant_id`, `event_category`, `created_at` DESC)
* `ix_audit_logs_resource` NONCLUSTERED on (`tenant_id`, `resource_type`, `resource_id`) WHERE `resource_type` IS NOT NULL
* `ix_audit_logs_status_timestamp` NONCLUSTERED on (`tenant_id`, `status`, `created_at` DESC)
* `ix_audit_logs_session` NONCLUSTERED on (`session_id`) WHERE `session_id` IS NOT NULL

**Constraints:**
* `fk_audit_logs_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_audit_logs_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
* `fk_audit_logs_session` FOREIGN KEY (`session_id`) REFERENCES `user_sessions`(`id`)
* `ck_audit_logs_event_category` CHECK (`event_category` IN ('authentication', 'user_management', 'organization_management', 'team_management', 'model_management', 'simulation', 'system', 'security'))
* `ck_audit_logs_action` CHECK (`action` IN ('view', 'create', 'update', 'delete', 'login', 'logout', 'invite', 'accept', 'reject', 'execute', 'download', 'export', 'import'))
* `ck_audit_logs_status` CHECK (`status` IN ('success', 'failure', 'partial', 'warning'))

## Event Types and Categories

### Authentication Events (`event_category` = 'authentication')
- `user_login` - User successful login
- `user_logout` - User logout
- `login_failed` - Failed login attempt
- `password_reset` - Password reset request
- `token_refresh` - JWT token refresh
- `session_timeout` - Session expired
- `account_locked` - Account locked due to failed attempts

### User Management Events (`event_category` = 'user_management')
- `user_created` - New user registration
- `user_updated` - User profile changes
- `user_deleted` - User account deletion
- `user_suspended` - User account suspension
- `user_reactivated` - User account reactivation
- `profile_viewed` - User profile accessed

### Security Events (`event_category` = 'security')
- `suspicious_activity` - Unusual user behavior detected
- `permission_denied` - Access denied to resource
- `data_breach_attempt` - Potential security breach
- `audit_log_tamper` - Attempt to modify audit logs
- `admin_action` - Administrative action performed

## Repository Pattern Examples

```python
# app/repositories/audit_repository.py
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.models.audit import AuditLog
from app.repositories.base_repository import BaseRepository

class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, db: Session):
        super().__init__(db, AuditLog)
    
    def create_audit_log(self, tenant_id: Optional[UUID], user_id: Optional[UUID], 
                        event_type: str, action: str, status: str = 'success', 
                        **kwargs) -> AuditLog:
        """Create a new audit log entry"""
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            action=action,
            status=status,
            event_category=kwargs.get('event_category', 'user_action'),
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent'),
            session_id=kwargs.get('session_id'),
            resource_type=kwargs.get('resource_type'),
            resource_id=kwargs.get('resource_id'),
            error_code=kwargs.get('error_code'),
            details=kwargs.get('details'),
            before_state=kwargs.get('before_state'),
            after_state=kwargs.get('after_state'),
            related_entity_id=kwargs.get('related_entity_id'),
            client_type=kwargs.get('client_type'),
            request_id=kwargs.get('request_id')
        )
        self.db.add(audit_log)
        return audit_log
    
    def get_user_activity(self, tenant_id: UUID, user_id: UUID, 
                         days: int = 30, limit: int = 100) -> List[AuditLog]:
        """Get recent user activity"""
        since_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(AuditLog).filter(
            AuditLog.tenant_id == tenant_id,
            AuditLog.user_id == user_id,
            AuditLog.created_at >= since_date,
            AuditLog.is_deleted == False
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    def get_security_events(self, tenant_id: Optional[UUID] = None, 
                           hours: int = 24) -> List[AuditLog]:
        """Get recent security events"""
        since_date = datetime.utcnow() - timedelta(hours=hours)
        query = self.db.query(AuditLog).filter(
            AuditLog.created_at >= since_date,
            AuditLog.event_category == 'security',
            AuditLog.is_deleted == False
        )
        
        if tenant_id:
            query = query.filter(AuditLog.tenant_id == tenant_id)
        
        return query.order_by(AuditLog.created_at.desc()).all()
```

## Audit Service Layer

```python
# app/services/audit_service.py
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from app.repositories.audit_repository import AuditRepository
import json

class AuditService:
    def __init__(self, db: Session):
        self.audit_repo = AuditRepository(db)
        self.db = db
    
    def log_user_action(self, tenant_id: UUID, user_id: UUID, action: str, 
                       resource_type: str, resource_id: str, status: str = 'success',
                       request_context: Optional[Dict] = None, **kwargs):
        """Log a user action with automatic context capture"""
        details = {
            'timestamp': datetime.utcnow().isoformat(),
            'action_details': kwargs.get('action_details', {})
        }
        
        if request_context:
            details.update({
                'request_method': request_context.get('method'),
                'request_path': request_context.get('path'),
                'request_params': request_context.get('params')
            })
        
        return self.audit_repo.create_audit_log(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=f"{resource_type}_{action}",
            action=action,
            status=status,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details),
            **kwargs
        )
    
    def log_authentication_event(self, user_id: Optional[UUID], tenant_id: Optional[UUID],
                                event_type: str, status: str, ip_address: str,
                                user_agent: str, **kwargs):
        """Log authentication-related events"""
        return self.audit_repo.create_audit_log(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            event_category='authentication',
            action='login' if 'login' in event_type else 'authenticate',
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs
        )
    
    def log_security_event(self, tenant_id: Optional[UUID], user_id: Optional[UUID],
                          event_type: str, details: Dict, severity: str = 'warning'):
        """Log security-related events"""
        security_details = {
            'severity': severity,
            'detected_at': datetime.utcnow().isoformat(),
            **details
        }
        
        return self.audit_repo.create_audit_log(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            event_category='security',
            action='detect',
            status='warning' if severity in ['warning', 'low'] else 'failure',
            details=json.dumps(security_details)
        )
```

## Security Considerations

### Audit Log Protection
- **Immutable Design**: Audit logs should never be updated, only created
- **Access Control**: Strict permissions for audit log access
- **Integrity Verification**: Consider cryptographic signatures for critical logs
- **Backup Strategy**: Separate backup retention for audit logs

### Performance Optimization
- **Partitioning**: Consider table partitioning by date for large volumes
- **Indexing Strategy**: Optimize indexes for common query patterns
- **Async Logging**: Consider asynchronous audit log writing for performance
- **Archival Strategy**: Move old logs to cold storage for cost optimization

## Related Schema Files

This auditing schema references:
- **000_User_Core_Management_Tables.md**: `users` and `user_sessions` tables
- **001_User_Organization_Management.md**: Organization events
- **002_User_Team_Management.md**: Team management events
- **Multi-Tenant Management Tables.md**: `tenants` table

## Next Implementation Steps

1. **Create Alembic migration** for the audit_logs table
2. **Implement SQLAlchemy model** following the BaseEntity pattern
3. **Build audit repository and service** with proper tenant scoping
4. **Add audit decorators** for automatic event logging
5. **Implement retention policies** for compliance
6. **Create audit dashboard** for monitoring and reporting
7. **Set up alerting** for security events

This audit system provides comprehensive tracking and compliance capabilities for the entire Quodsi platform while maintaining performance and security standards.
