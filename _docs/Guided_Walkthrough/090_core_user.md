# Task: Implement User Session & Usage Statistics Core Features

**Objective:** Extend the Quodsi application's user core management capabilities by implementing database tables, schemas, repositories, services, and APIs for tracking user sessions and daily usage statistics.

**Source Documents:**
* Primarily refer to: `Quodsi SaaS App/database/schemas/010_User_Core_Management_Tables.md` for detailed specifications of the `user_sessions` and `user_usage_stats` tables.
* Recall existing patterns from `users` and `tenants` table implementations.

**General Guidelines:**
* **Adhere to Existing Architecture:** Implement new components following the established patterns:
    * SQLAlchemy Models (inheriting from `BaseEntity`)
    * Pydantic Schemas for API contracts and data transfer
    * Repositories (inheriting from `BaseRepository`) for data access logic, ensuring tenant isolation.
    * Services for business logic orchestration.
    * FastAPI Routers for API endpoints.
* **Database Migrations:** Use Alembic to generate and refine database migrations for the new tables.
* **Testing:** Write unit tests for new repository methods and service logic. Consider integration tests for any new API endpoints.
* **Code Clarity & Comments:** Ensure your code is well-organized, readable, and appropriately commented.
* **Design Thinking:** While the database schema is defined, you will need to design the Pydantic schemas, repository method signatures, service logic, and API contracts. Think about how these components will interact and what data is necessary at each layer.

---

## Module 1: `user_sessions` Table Implementation

The `user_sessions` table will track individual user sessions for analytics, auditing, and potentially for security features like identifying concurrent sessions.

### 1.1 Database Model (`app.db.models.user_session.py` - new file)

* **Create `UserSession` SQLAlchemy Model:**
    * Ensure it inherits from `app.db.models.base_entity.BaseEntity`.
    * Define all columns as specified in `010_User_Core_Management_Tables.md` for `user_sessions`[cite: 256]. Key fields to include: `user_id`[cite: 266], `ended_at`[cite: 269], `duration_minutes`[cite: 273], `session_type`[cite: 276], `client_type`[cite: 279], `client_info`[cite: 282], `ip_address`[cite: 284].
    * **Relationships & Foreign Keys:**
        * Establish the foreign key relationship from `UserSession.user_id` to `users.id`[cite: 267]. Include the SQLAlchemy `relationship()` on the `User` model if you foresee needing to access sessions from a user object (e.g., `user.sessions`).
    * **Constraints & Indexes:**
        * Ensure relevant check constraints from the spec are considered (e.g., `ck_user_sessions_client_type`, `ck_user_sessions_tenant_consistency`)[cite: 287]. SQLAlchemy models might not directly define all DB-level check constraints; these are often part of the Alembic migration script.
        * While `BaseEntity` provides some indexes, note any additional specific indexes mentioned for `user_sessions` [cite: 287] (e.g., `ix_user_sessions_tenant_user_created`). These will primarily be defined in the Alembic migration.
* Add your new model to `app.db.models.__init__.py`.

### 1.2 Pydantic Schemas (`app.schemas.user_session.py` - new file, or extend existing user schemas)

* **Design and Implement Schemas:**
    * `UserSessionCreate`: What data is required to start a new session? (e.g., `user_id`, `client_type`, `ip_address`).
    * `UserSessionRead`: What data should be returned when a session is queried? (e.g., include `id`, `user_id`, `created_at` (as session start), `ended_at`, `duration_minutes`, etc.).
    * `UserSessionUpdate` (Optional): Is there a need to update a session record directly via API, or will updates (like setting `ended_at`) be handled internally by services?
* Think about how these schemas will be used by services and API endpoints.
* Add new schemas to `app.schemas.__init__.py`.

### 1.3 Repository (`app.repositories.user_session_repository.py` - new file)

* **Create `UserSessionRepository`:**
    * It should inherit from `BaseRepository[UserSession]`.
    * Initialize with the `UserSession` model.
* **Implement Key Methods:**
    * `start_session(db: Session, user_id: UUID, tenant_id: UUID, client_type: str, client_info: Optional[str], ip_address: Optional[str]) -> UserSession`: Creates and returns a new session record.
    * `end_session(db: Session, session_id: UUID, tenant_id: UUID) -> Optional[UserSession]`: Updates a session to mark it as ended, calculating and storing its duration.
    * `get_active_sessions_for_user(db: Session, user_id: UUID, tenant_id: UUID) -> List[UserSession]`: Retrieves sessions for a user that have not yet ended.
    * `get_session_history_for_user(db: Session, user_id: UUID, tenant_id: UUID, skip: int, limit: int) -> List[UserSession]`: Retrieves a paginated list of past sessions for a user.
* Ensure all repository methods correctly implement tenant isolation using `tenant_id`.
* Add to `app.repositories.__init__.py`.

### 1.4 Service Layer (`app.services.user_service.py` - extend existing)

* **Integrate Session Logic into `UserService`:**
    * `def record_session_start(self, user_id: UUID, tenant_id: UUID, client_type: str, client_info: Optional[str], ip_address: Optional[str]) -> UserSession:`
        * This method will use `UserSessionRepository.start_session()`.
        * It should also update the `last_session_start` and `last_active_at` fields on the `users` table (using `UserRepository`).
    * `def record_session_end(self, session_id: UUID, tenant_id: UUID) -> Optional[UserSession]:`
        * Calculates session duration (current time minus session start time).
        * Uses `UserSessionRepository.end_session()` to update the session record.
        * Consider updating `users.total_usage_minutes` based on the completed session's duration (using `UserRepository`).
* Think about transaction management: if multiple repository calls are made, ensure they are part of a single transaction.

### 1.5 API Endpoints (Consider if new or modifications to existing)

* **Discuss and Design:**
    * Are direct API endpoints needed to manage/view sessions (e.g., for an admin)?
    * Or will session tracking be primarily an internal mechanism triggered by other events (like login/logout, or regular activity heartbeats)?
    * For this task, explicit API endpoints for sessions might not be the primary focus unless specified. Session start/end could be tied into login/logout/token refresh logic within `UserService` or an authentication service.

### 1.6 Alembic Migration

* After defining the `UserSession` model:
    * Generate a new Alembic migration: `alembic revision -m "create_user_sessions_table"`
    * Inspect and edit the generated script:
        * Verify all columns, types, and nullability match the specs.
        * Manually add any specific indexes (e.g., `ix_user_sessions_tenant_user_created` [cite: 287]) and check constraints (e.g., `ck_user_sessions_client_type` [cite: 287]) defined in `010_User_Core_Management_Tables.md`.
    * Apply the migration: `alembic upgrade head`.

### 1.7 Testing

* Write unit tests for:
    * `UserSessionRepository` methods: `start_session`, `end_session`, `get_active_sessions_for_user`, etc.
    * `UserService` methods: `record_session_start`, `record_session_end`, ensuring updates to both `user_sessions` and `users` tables are handled correctly.

---

## Module 2: `user_usage_stats` Table Implementation

The `user_usage_stats` table will store aggregated daily usage statistics for users, facilitating reporting and analytics without querying raw event data constantly.

### 2.1 Database Model (`app.db.models.user_usage_stat.py` - new file)

* **Create `UserUsageStat` SQLAlchemy Model:**
    * Ensure it inherits from `app.db.models.base_entity.BaseEntity`.
    * Define columns as per `010_User_Core_Management_Tables.md` for `user_usage_stats`[cite: 288]. Key fields: `user_id`[cite: 298], `date`[cite: 301], `login_count` (daily)[cite: 305], `active_minutes`[cite: 309], `simulation_runs`[cite: 312], `documents_accessed`[cite: 315], `feature_usage` (JSON)[cite: 318].
    * **Relationships & Foreign Keys:**
        * Establish the foreign key relationship from `UserUsageStat.user_id` to `users.id`[cite: 299].
    * **Constraints & Indexes:**
        * The unique constraint `uq_user_usage_stats_tenant_user_date` [cite: 321] is critical. How will SQLAlchemy/Alembic handle this?
        * Consider the `ck_user_usage_stats_tenant_consistency` check constraint[cite: 321].
* Add your new model to `app.db.models.__init__.py`.

### 2.2 Pydantic Schemas (`app.schemas.user_usage_stat.py` - new file, or extend)

* **Design and Implement Schemas:**
    * `UserUsageStatRead`: What data should be returned when querying daily stats?
    * `UserUsageStatCreate` (or `UserUsageStatUpdate`): How will these records be created or updated? Will it be through an API or an internal aggregation service? For an aggregation service, a Pydantic model might still be useful for internal data structure.
* Add new schemas to `app.schemas.__init__.py`.

### 2.3 Repository (`app.repositories.user_usage_stat_repository.py` - new file)

* **Create `UserUsageStatRepository`:**
    * Inherit from `BaseRepository[UserUsageStat]`.
    * Initialize with the `UserUsageStat` model.
* **Implement Key Methods:**
    * `upsert_daily_stats(db: Session, tenant_id: UUID, user_id: UUID, date: date, stats_to_add: dict) -> UserUsageStat`: This method should find an existing record for the user/date or create a new one, then increment the relevant counters (logins, active minutes, etc.). The `stats_to_add` dict might contain keys like `login_increment`, `active_minutes_increment`.
    * `get_stats_for_user_date_range(db: Session, user_id: UUID, tenant_id: UUID, start_date: date, end_date: date) -> List[UserUsageStat]`.
    * `get_aggregated_stats_for_tenant(db: Session, tenant_id: UUID, start_date: date, end_date: date) -> List[Dict[str, Any]]` (This might involve more complex aggregation queries).
* Add to `app.repositories.__init__.py`.

### 2.4 Service Layer (e.g., `app.services.user_analytics_service.py` - extend existing, or a new dedicated aggregation service)

* **Design Usage Aggregation Logic:**
    * How and when will `user_usage_stats` be populated?
        * Option 1: A method in `UserAnalyticsService` (or a new service) that is called periodically (e.g., by a scheduled task - outside the scope of this immediate task, but the service method is needed).
        * Option 2: Updates happen more frequently, perhaps triggered by events like session end or login.
    * `def aggregate_daily_user_stats(self, tenant_id: UUID, user_id: UUID, date: date, daily_login_count: int, daily_active_minutes: int, ...)`: This service method would use the `UserUsageStatRepository.upsert_daily_stats` method.
    * Methods in `UserAnalyticsService` that currently calculate stats on the fly from the `users` table (e.g., `get_user_activity_summary`) might be refactored to leverage the pre-aggregated `user_usage_stats` for better performance over longer time ranges.

### 2.5 API Endpoints (Likely new endpoints in an analytics/reporting router)

* **Design Endpoints for Accessing Stats:**
    * `GET /users/{user_id}/usage-stats?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`: Retrieves daily stats for a user over a period.
    * `GET /tenants/{tenant_id}/usage-report?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`: Retrieves aggregated usage for a tenant.
    * Consider who should have access to these endpoints (user for their own stats, admin for tenant-level reports). This involves permission checks.
* These endpoints will use the methods from your `UserAnalyticsService` (or the relevant service).

### 2.6 Alembic Migration

* After defining the `UserUsageStat` model:
    * Generate a new Alembic migration: `alembic revision -m "create_user_usage_stats_table"`
    * Inspect and edit:
        * Verify columns, types, nullability.
        * Ensure the unique constraint `uq_user_usage_stats_tenant_user_date` [cite: 321] is correctly defined.
        * Add other specific indexes and check constraints[cite: 321].
    * Apply: `alembic upgrade head`.

### 2.7 Testing

* Unit tests for:
    * `UserUsageStatRepository` methods, especially `upsert_daily_stats`.
    * Service logic for aggregating and retrieving usage statistics.
* Integration tests for any new API endpoints that expose this data.

---

**Final Steps for Both Modules:**
* **Code Review:** Participate in code reviews with your mentor/supervisor and fellow intern.
* **Testing:** Ensure all new functionalities are covered by tests and all tests pass.
* **Merge:** Follow the project's process for merging your changes.

Good luck! Remember to communicate with your fellow intern if you foresee any overlapping areas, especially in shared service files.