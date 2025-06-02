# Task: Implement Analysis Management Features

**Objective:** Enable users to group related simulation scenarios by implementing the `analyses` table. This table serves as a container for studies or experiments performed on a specific simulation model.

**Source Documents:**
* Primarily refer to: `061_Analysis Tables Database Schema.md` (the document you just provided) for detailed specifications of the **`analyses`** table.
* Recall existing patterns from `tenants`, `users`, `models`, and other previously implemented tables, especially the use of `BaseEntity`.

**Prerequisites:**
* The `models` table and its related components (model, schema, repository, service) must be implemented, as `analyses` are directly linked to a parent `model`.
* `users` and `tenants` tables must be available.

**General Guidelines:**
* **Adhere to Existing Architecture:** Implement new components following the established patterns:
    * SQLAlchemy Models (inheriting from `BaseEntity`)
    * Pydantic Schemas for API contracts and data transfer
    * Repositories (inheriting from `BaseRepository`) for data access logic, ensuring tenant isolation.
    * Services for business logic orchestration.
    * FastAPI Routers for API endpoints.
* **Database Migrations:** Use Alembic to generate and refine database migrations for the new `analyses` table.
* **Testing:** Write unit tests for new repository methods and service logic. Implement integration tests for new API endpoints related to analyses.
* **Code Clarity & Comments:** Ensure your code is well-organized, readable, and appropriately commented.
* **Design Thinking:** The database schema for `analyses` is provided. Your task is to design:
    * Pydantic schemas for creating, reading, and updating analyses.
    * Repository methods for querying analyses (e.g., by model, by user).
    * Service layer logic to handle the lifecycle of an analysis, including setting default values.
    * Clear API contracts for managing analyses.

---

## Implementing the `analyses` Table and Core Functionality

The `analyses` table allows users to organize sets of scenarios under a common study or experimental setup, linked to a parent simulation model.

### 1. Database Model (`app.db.models.analysis.py` - new file)

* **Create `Analysis` SQLAlchemy Model:**
    * Ensure it inherits from `app.db.models.base_entity.BaseEntity`.
    * Define all columns as specified in `061_Analysis Tables Database Schema.md` for the `analyses` table. This includes:
        * Core info: `name`, `description`.
        * Link to parent model: `model_id`.
        * Default parameters for child scenarios: `default_reps`, `default_time_period`.
        * Ownership: `created_by_user_id`.
    * **Relationships & Foreign Keys:**
        * The `tenant_id` FK is inherited.
        * Establish FK relationship for `model_id` to `models.id` (with `ON DELETE CASCADE`).
        * Establish FK relationship for `created_by_user_id` to `users.id`.
        * Define SQLAlchemy `relationship()` attributes:
            * On `Model` model: to navigate to its analyses (e.g., `model.analyses`).
            * On `User` model: to navigate to analyses created by a user (e.g., `user.analyses`).
            * You will later add a one-to-many relationship from `Analysis` to `Scenario` (e.g., `analysis.scenarios`) when the `scenarios` table is implemented.
    * **Constraints & Indexes:**
        * Note the check constraints: `ck_analyses_default_time_period`, `ck_analyses_tenant_consistency_model`, `ck_analyses_tenant_consistency_user`. These will primarily be enforced in the Alembic migration.
        * Note the unique constraint: `uq_analyses_tenant_model_name`.
        * BaseEntity provides standard indexes. Be aware of additional specific indexes like `ix_analyses_tenant_model` and `ix_analyses_tenant_created_by`.
* Add your new model to `app.db.models.__init__.py`.

### 2. Pydantic Schemas (`app.schemas.analysis.py` - new file)

* **Design and Implement Schemas:**
    * `AnalysisCreate`:
        * Required fields: `name`, `model_id`.
        * Optional fields: `description`, `default_reps`, `default_time_period`. The service layer can apply defaults if not provided.
    * `AnalysisRead`:
        * Should include all relevant fields from the `Analysis` model.
        * Consider whether to include a nested `ModelRead` schema for `model` details, and `UserRead` for `created_by_user`.
        * Eventually, it might include a list of `ScenarioRead` summaries.
    * `AnalysisUpdate`:
        * Fields that can be updated: `name`, `description`, `default_reps`, `default_time_period`.
    * `AnalysisSummary` (Optional): A lightweight schema for listing analyses, perhaps without deeply nested objects.
* Add new schemas to `app.schemas.__init__.py`.

### 3. Repository (`app.repositories.analysis_repository.py` - new file)

* **Create `AnalysisRepository`:**
    * It should inherit from `BaseRepository[Analysis]`.
    * Initialize with the `Analysis` model.
* **Implement Key Methods (beyond basic CRUD):**
    * `get_analyses_by_model_id(db: Session, tenant_id: UUID, model_id: UUID, skip: int, limit: int) -> List[Analysis]`.
    * `get_analyses_by_user_id(db: Session, tenant_id: UUID, user_id: UUID, skip: int, limit: int) -> List[Analysis]`.
    * `find_by_name_and_model_id(db: Session, tenant_id: UUID, model_id: UUID, name: str) -> Optional[Analysis]` (to support the unique constraint).
* Ensure all repository methods correctly implement tenant isolation using `tenant_id`.
* Add to `app.repositories.__init__.py`.

### 4. Service Layer (`app.services.analysis_service.py` - new file)

* **Create `AnalysisService`:**
    * This service will manage the business logic for analyses.
* **Implement Core Service Methods:**
    * `create_analysis(self, tenant_id: UUID, analysis_create_schema: AnalysisCreate, current_user_id: UUID) -> Analysis`:
        * Uses `AnalysisRepository` to persist the new analysis.
        * Sets `created_by_user_id` to `current_user_id`.
        * Applies default values for `default_reps` and `default_time_period` if not provided in the schema, based on schema defaults or DB defaults.
        * Verifies that the `model_id` provided belongs to the same `tenant_id`.
    * `get_analysis_by_id(self, tenant_id: UUID, analysis_id: UUID) -> Optional[Analysis]`.
    * `update_analysis(self, tenant_id: UUID, analysis_id: UUID, analysis_update_schema: AnalysisUpdate, current_user_id: UUID) -> Optional[Analysis]`:
        * Implement authorization: Does the `current_user_id` have permission to update this analysis (e.g., are they the creator)?
    * `delete_analysis(self, tenant_id: UUID, analysis_id: UUID, current_user_id: UUID) -> bool` (soft delete):
        * Permission check.
        * Note the `ON DELETE CASCADE` for `model_id` in the schema implies if a model is deleted, its analyses are also deleted. This service method handles direct deletion of an analysis.
    * `list_analyses_for_model(self, tenant_id: UUID, model_id: UUID, skip: int, limit: int) -> List[Analysis]`.
* Add to `app.services.__init__.py`.

### 5. API Endpoints (`app.api.routers.analyses.py` - new file)

* **Create a new FastAPI Router for Analyses:**
    * `POST /analyses/`: Create a new analysis. Requires `AnalysisCreate` schema. The `model_id` will be in the payload.
    * `GET /models/{model_id}/analyses/`: List all analyses for a specific model.
    * `GET /analyses/{analysis_id}`: Get details of a specific analysis.
    * `PUT /analyses/{analysis_id}`: Update an analysis. Requires `AnalysisUpdate` schema.
    * `DELETE /analyses/{analysis_id}`: Soft delete an analysis.
* These endpoints will use `AnalysisService` and depend on the current user's context (tenant and user ID for creation/permission checks).
* Integrate this new router into `app.api.api_router`.

### 6. Alembic Migration

* After defining the `Analysis` SQLAlchemy model:
    * Generate a new Alembic migration: `alembic revision -m "create_analyses_table"`
    * Inspect and meticulously edit the generated script:
        * Verify all columns, types, default values (e.g., `default_reps` DEFAULT 1), and nullability match the specifications from `061_Analysis Tables Database Schema.md`.
        * Manually add all specified foreign keys (`fk_analyses_tenant`, `fk_analyses_model`, `fk_analyses_created_by_user`). Ensure `ON DELETE CASCADE` is correctly set for `model_id`.
        * Add all specified check constraints (`ck_analyses_default_time_period`, tenant consistency checks).
        * Add the unique constraint `uq_analyses_tenant_model_name`.
        * Define all additional non-clustered indexes specified (e.g., `ix_analyses_tenant_model`, `ix_analyses_tenant_created_by`).
    * Apply the migration: `alembic upgrade head`.

### 7. Testing

* Write unit tests for:
    * `AnalysisRepository` methods.
    * `AnalysisService` methods (creation logic, updates, permission placeholders, deletion).
* Write integration tests for the new API endpoints for analyses. Test:
    * Analysis creation linked to a model.
    * Retrieval of analyses (for a model, and individually).
    * Updates to analysis properties.
    * Deletion.
    * Ensure tenant isolation: a user in tenant A cannot see/modify analyses in tenant B.

---

**Next Steps & Considerations:**
* The `analyses` table is a parent to the `scenarios` table (from `060_Scenario Tables Database Schema.md`). The `Scenario` model will have an FK to `analyses.id`.
* The default values for `default_reps` and `default_time_period` in the `analyses` table will be useful when creating new `scenarios` under this analysis.
* Permissions for who can create/edit/delete analyses will eventually be refined by a dedicated permissions system (e.g., based on `model_permissions` or roles).

This task lays the groundwork for organizing complex simulation experiments. It's crucial for the interns to understand the relationship between `models` and `analyses`.