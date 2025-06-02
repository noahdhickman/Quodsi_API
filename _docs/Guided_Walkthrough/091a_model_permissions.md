# Task: Implement Model Permissions and Access Logging System

**Objective:** To establish a robust access control system for simulation models and to create a comprehensive audit trail for all model-related access and operations. This involves implementing the `model_permissions` and `model_access_logs` tables and their supporting backend logic.

**Source Documents:**
* Primarily refer to: `050_Model_Permissions_Database Schema.md` for detailed specifications.
* Refer to previously implemented `BaseEntity`, `models`, `users`, `organizations`, and `teams` structures as these are prerequisites.

**General Guidelines:**
* **Adhere to Existing Architecture:** Implement new components following established patterns (SQLAlchemy Models, Pydantic Schemas, Repositories, Services, FastAPI Routers).
* **Database Migrations:** Use Alembic for all database schema changes. Pay close attention to constraints and indexes.
* **Testing:** Rigorous testing is paramount for security features. Cover various permission scenarios and ensure access logs are accurately created.
* **Code Clarity & Security Focus:** Write clear, maintainable code. Security implications should be at the forefront of design decisions.
* **Design Thinking:** The database schema is provided. Your task is to design:
    * Pydantic schemas for granting, revoking, updating, and listing model permissions.
    * Pydantic schemas for representing model access log entries if they are to be exposed via an API (likely admin-only).
    * Repository methods for managing permission records and creating access log entries.
    * A comprehensive `ModelPermissionService` (or similar) to check permissions based on user, team, and organization grants. This service will also manage the lifecycle of permissions.
    * Service logic for automatically creating `model_access_logs` when models are accessed or modified through other services (e.g., `ModelService`).
    * API endpoints for managing model permissions.

---

## Module 1: `model_permissions` Table Implementation

This table will store explicit access rights to models for users, teams, or entire organizations, defining *who* can do *what* with a specific model.

### 1.1 Database Model (`app.db.models.model_permission.py` - new file)

* **Create `ModelPermission` SQLAlchemy Model:**
    * Ensure it inherits from `app.db.models.base_entity.BaseEntity`.
    * Define all columns as per `050_Model_Permissions_Database Schema.md`. Key fields include:
        * `model_id` [cite: 1]
        * Grantee fields: `user_id` (nullable)[cite: 1], `organization_id` (nullable)[cite: 1], `team_id` (nullable) [cite: 1]
        * `permission_level` (e.g., 'read', 'write', 'execute', 'admin') [cite: 1]
        * Lifecycle/audit fields: `granted_by_user_id`[cite: 1], `expires_at`[cite: 1], `is_active`[cite: 1], `revoked_at`[cite: 1], `revoked_by_user_id`[cite: 1], `grant_reason`[cite: 1], `revoke_reason`[cite: 1].
    * **Relationships & Foreign Keys:**
        * Inherited `tenant_id`.
        * FK to `models.id` for `model_id` (ensure `ON DELETE CASCADE` as per schema)[cite: 1].
        * FKs to `users.id`, `organizations.id`, `teams.id` for grantee fields.
        * FKs to `users.id` for `granted_by_user_id` and `revoked_by_user_id`.
        * Define SQLAlchemy `relationship()` attributes on `Model`, `User`, `Organization`, `Team` for easy navigation of permissions if needed.
    * **Constraints & Indexes:**
        * Pay close attention to `ck_model_permissions_single_target` to ensure a permission is granted to only one type of entity (user, org, or team)[cite: 1].
        * Implement `ck_model_permissions_level`[cite: 1].
        * Ensure all tenant consistency check constraints are considered for the Alembic script[cite: 1].
        * Note specified indexes like `ix_model_permissions_tenant_model`, `ix_model_permissions_tenant_user`, etc. [cite: 1]
* Add your new model to `app.db.models.__init__.py`.

### 1.2 Pydantic Schemas (`app.schemas.model_permission.py` - new file)

* **Design and Implement Schemas:**
    * `ModelPermissionGrant` (or `ModelPermissionCreate`): For granting new permissions. Needs `model_id`, one of (`user_id`, `organization_id`, `team_id`), `permission_level`. `granted_by_user_id` would come from the authenticated user.
    * `ModelPermissionRead`: To display existing permissions. Should clearly show the model, the grantee (user/org/team), level, and status. May involve nested schemas for grantee details.
    * `ModelPermissionUpdate`: For changing `permission_level`, `expires_at`, or `is_active` status.
    * `ModelPermissionRevoke`: For revoking a permission (might just be an update to `is_active=False`, `revoked_at`, `revoked_by_user_id`).
* Add new schemas to `app.schemas.__init__.py`.

### 1.3 Repository (`app.repositories.model_permission_repository.py` - new file)

* **Create `ModelPermissionRepository`:**
    * Inherit from `BaseRepository[ModelPermission]`.
* **Implement Key Methods:**
    * `get_permissions_for_model(db: Session, tenant_id: UUID, model_id: UUID) -> List[ModelPermission]`.
    * `get_user_permissions_for_model(db: Session, tenant_id: UUID, model_id: UUID, user_id: UUID) -> List[ModelPermission]` (direct user grants).
    * `get_team_permissions_for_model(db: Session, tenant_id: UUID, model_id: UUID, team_ids: List[UUID]) -> List[ModelPermission]` (permissions for teams a user belongs to).
    * `get_organization_permissions_for_model(db: Session, tenant_id: UUID, model_id: UUID, organization_ids: List[UUID]) -> List[ModelPermission]` (permissions for orgs a user belongs to).
    * `find_existing_permission(...)`: To check if a specific grant already exists before creating a duplicate.
* Add to `app.repositories.__init__.py`.

### 1.4 Service Layer (`app.services.model_permission_service.py` - new file)

* **Create `ModelPermissionService`:**
* **Implement Core Service Methods:**
    * `grant_permission(self, tenant_id: UUID, grant_schema: ModelPermissionGrant, granting_user_id: UUID) -> ModelPermission`.
        * Ensures `granting_user_id` has authority to grant permissions on the model (e.g., is owner or admin of the model).
    * `revoke_permission(self, tenant_id: UUID, permission_id: UUID, revoking_user_id: UUID, reason: Optional[str]) -> bool`.
    * `update_permission(self, tenant_id: UUID, permission_id: UUID, update_schema: ModelPermissionUpdate, current_user_id: UUID) -> Optional[ModelPermission]`.
    * `list_permissions_for_model(self, tenant_id: UUID, model_id: UUID) -> List[ModelPermissionRead]`.
    * **`check_user_access(self, tenant_id: UUID, model_id: UUID, user_id: UUID, required_level: str) -> bool`:** This is a **critical** method.
        * It needs to determine if the `user_id` has at least the `required_level` of permission for the `model_id`.
        * This check must consider:
            1. Direct permissions granted to the `user_id`.
            2. Permissions granted to any `team_id` the user is a member of.
            3. Permissions granted to any `organization_id` the user is a member of.
        * It should respect the hierarchy of permissions (e.g., 'admin' implies 'write', 'write' implies 'read').
        * It should consider `is_active` and `expires_at` fields.
* This service will be injected into other services (like `ModelService`, `ScenarioService`) to protect their methods.
* Add to `app.services.__init__.py`.

### 1.5 API Endpoints (`app.api.routers.model_permissions.py` - new file)

* **Create a new FastAPI Router for Model Permissions (likely under a model's path):**
    * `POST /models/{model_id}/permissions/`: Grant a new permission for the model.
    * `GET /models/{model_id}/permissions/`: List all permissions for the model.
    * `PUT /models/{model_id}/permissions/{permission_id}`: Update an existing permission.
    * `DELETE /models/{model_id}/permissions/{permission_id}`: Revoke (soft delete or deactivate) a permission.
* These endpoints will use `ModelPermissionService` and require robust authorization checks on the caller.
* Integrate this new router into `app.api.api_router`.

### 1.6 Alembic Migration for `model_permissions`

* After defining the `ModelPermission` model:
    * Generate: `alembic revision -m "create_model_permissions_table"`
    * Edit: Meticulously ensure all columns, types, FKs (with `ON DELETE CASCADE` for `model_id`), check constraints (especially `ck_model_permissions_single_target` and `ck_model_permissions_level`), and all specified indexes are correctly defined[cite: 1].
    * Apply: `alembic upgrade head`.

### 1.7 Testing for `model_permissions`

* Unit tests for `ModelPermissionRepository`.
* Extensive unit tests for `ModelPermissionService`, especially the `check_user_access` method covering various scenarios (direct grant, team grant, org grant, expired grant, inactive grant, permission hierarchy).
* Integration tests for API endpoints, focusing on granting, revoking, and listing permissions, and ensuring unauthorized users cannot manage permissions.

---

## Module 2: `model_access_logs` Table Implementation

This table will serve as an audit trail, recording who accessed or performed operations on models, when, and what the outcome was.

### 2.1 Database Model (`app.db.models.model_access_log.py` - new file)

* **Create `ModelAccessLog` SQLAlchemy Model:**
    * Inherit from `BaseEntity`.
    * Define columns as per `050_Model_Permissions_Database Schema.md`: `model_id`, `user_id`, `access_type`, `access_result`, `permission_source` (nullable), `permission_id` (nullable, FK to `model_permissions.id`), `session_id` (nullable), `ip_address` (nullable), `user_agent` (nullable), `details` (nullable JSON)[cite: 1].
        * Note: `created_at` from `BaseEntity` serves as `accessed_at`.
    * **Relationships & Foreign Keys:**
        * Inherited `tenant_id`.
        * FKs to `models.id`, `users.id`, and `model_permissions.id`.
    * **Constraints & Indexes:**
        * Note check constraints `ck_model_access_logs_access_type` and `ck_model_access_logs_access_result`[cite: 1].
        * Note tenant consistency checks[cite: 1].
        * Be aware of specified indexes like `ix_model_access_logs_tenant_model_user`[cite: 1].
* Add model to `app.db.models.__init__.py`.

### 2.2 Pydantic Schemas (`app.schemas.model_access_log.py` - new file)

* **Design and Implement Schemas:**
    * `ModelAccessLogCreate` (Internal use for services): `model_id`, `user_id`, `access_type`, `access_result`, and other contextual fields.
    * `ModelAccessLogRead`: For displaying log entries (likely for an admin interface).
* Add new schemas to `app.schemas.__init__.py`.

### 2.3 Repository (`app.repositories.model_access_log_repository.py` - new file)

* **Create `ModelAccessLogRepository`:**
    * Inherit `BaseRepository[ModelAccessLog]`.
* **Implement Key Methods:**
    * `create_log_entry(db: Session, log_data: ModelAccessLogCreate) -> ModelAccessLog` (Note: `log_data` would be a Pydantic schema or dict).
    * `get_logs_for_model(db: Session, tenant_id: UUID, model_id: UUID, skip: int, limit: int) -> List[ModelAccessLog]`.
    * `get_logs_for_user(db: Session, tenant_id: UUID, user_id: UUID, skip: int, limit: int) -> List[ModelAccessLog]`.
* Add to `app.repositories.__init__.py`.

### 2.4 Service Layer (Extend existing services like `ModelService`, or use a dedicated `AuditService`)

* **Integrate Access Logging:**
    * Instead of a standalone `ModelAccessLogService` for *creating* logs, the logging action should ideally be embedded within other services.
    * For example, in `ModelService`:
        * When `get_model_by_id` is called, after permission checks, it should create a `ModelAccessLog` entry (e.g., `access_type='view'`, `access_result='granted'`).
        * When `update_model` is successful, log `access_type='edit'`, `access_result='success'`. If permission is denied by `ModelPermissionService`, log `access_result='denied'`.
    * A generic `AuditService` (as hinted in `013_User_Auditing_Security.md`) could provide helper methods to create these logs, which other services call.
* **Retrieval Service (Optional, for admin UI):**
    * A method in `ModelPermissionService` or an `AuditService` like `list_model_access_logs(self, tenant_id: UUID, model_id: Optional[UUID], user_id: Optional[UUID], skip: int, limit: int) -> List[ModelAccessLogRead]` might be useful.

### 2.5 API Endpoints (Likely Admin-focused, if any direct query endpoints are needed)

* **Consider API for Log Retrieval:**
    * `GET /admin/logs/model-access?model_id=...&user_id=...`: An admin endpoint to view access logs. This requires strong authorization.
* For this task, focus on the *creation* of logs within other services rather than exposing logs via new query APIs, unless specifically prioritized.

### 2.6 Alembic Migration for `model_access_logs`

* After defining `ModelAccessLog` model:
    * Generate: `alembic revision -m "create_model_access_logs_table"`
    * Edit: Verify columns, types, FKs, check constraints, and indexes as per the schema document[cite: 1].
    * Apply: `alembic upgrade head`.

### 2.7 Testing for `model_access_logs`

* Unit tests to ensure that service methods (e.g., in `ModelService`) correctly create `ModelAccessLog` entries upon successful operations or permission denials.
* Test repository methods for creating and querying logs.
* If API endpoints are created for viewing logs, test them.

---

**Final Steps for Both Modules:**
* **Security Review:** Given the nature of these tables, a careful review of the permission checking logic and access log creation is crucial.
* **Code Review & Testing:** Ensure all new functionalities are robustly tested.
* **Merge:** Integrate into the main codebase.

This module is foundational for securing your application's core assets (simulation models). The `ModelPermissionService.check_user_access` method will be central and complex, so allocate sufficient time for its design and testing.