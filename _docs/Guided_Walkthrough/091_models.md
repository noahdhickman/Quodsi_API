# Task: Implement Core Simulation Model Management Features

**Objective:** Establish the foundational capabilities for managing simulation models within the Quodsi application. This involves implementing the `models` table and the necessary backend components to create, read, update, and delete model records.

**Source Documents:**
* Primarily refer to: `030_Model Database Schema.md` (the document you just provided) for detailed specifications of the **`models`** table.
* Recall existing patterns from `tenants`, `users`, and other previously implemented tables, especially the use of `BaseEntity`.

**General Guidelines:**
* **Adhere to Existing Architecture:** Implement new components following the established patterns:
    * SQLAlchemy Models (inheriting from `BaseEntity`)
    * Pydantic Schemas for API contracts and data transfer
    * Repositories (inheriting from `BaseRepository`) for data access logic, ensuring tenant isolation.
    * Services for business logic orchestration.
    * FastAPI Routers for API endpoints.
* **Database Migrations:** Use Alembic to generate and refine database migrations for the new `models` table.
* **Testing:** Write unit tests for new repository methods and service logic. Implement integration tests for new API endpoints related to models.
* **Code Clarity & Comments:** Ensure your code is well-organized, readable, and appropriately commented.
* **Design Thinking:** The database schema for `models` is rich. You'll need to design:
    * Pydantic schemas that appropriately represent model data for creation, reading, and updates (consider which fields are optional or have defaults).
    * Repository methods beyond basic CRUD if specific query patterns for models are anticipated (e.g., finding models by source, by user, or by template status).
    * Service layer logic to handle model creation (including setting defaults from the schema like `reps`, `forecast_days`, `time_type`, `version`), updates, and business rule enforcement.
    * Clear API contracts for interacting with models.

---

## Implementing the `models` Table and Core Functionality

The `models` table is central to Quodsi, storing definitions and metadata for all simulation models created on the platform.

### 1. Database Model (`app.db.models.simulation_model.py` - consider a new file, or `model.py` if not conflicting)

* **Create `Model` SQLAlchemy Model:**
    * Ensure it inherits from `app.db.models.base_entity.BaseEntity`.
    * Define all columns as specified in `030_Model Database Schema.md` for the `models` table. This includes:
        * Basic info: `name`, `description`.
        * Source info: `source`, `source_document_id`, `source_url`[cite: 761].
        * Default simulation parameters: `reps`[cite: 761], `forecast_days`[cite: 761], `random_seed`[cite: 762], `time_type`[cite: 762], `one_clock_unit`[cite: 762], `warmup_clock_period`[cite: 762], `run_clock_period`[cite: 762], `warmup_date_time`[cite: 763], `start_date_time`[cite: 763], `finish_date_time`[cite: 763].
        * Ownership/Association: `created_by_user_id`, `organization_id` (nullable), `team_id` (nullable)[cite: 763].
        * Flags: `is_public`, `is_template`[cite: 764].
        * Versioning: `version`[cite: 765].
        * Legacy: `blob_storage_url`[cite: 765].
    * **Relationships & Foreign Keys:**
        * The `tenant_id` FK is inherited.
        * Establish FK relationships for `created_by_user_id` to `users.id`[cite: 765].
        * Establish FK relationships for `organization_id` to `organizations.id` (nullable)[cite: 765].
        * Establish FK relationships for `team_id` to `teams.id` (nullable)[cite: 765].
        * Define SQLAlchemy `relationship()` attributes on `User`, `Organization`, and `Team` models if you anticipate needing to navigate from those entities to their associated models (e.g., `user.models`).
    * **Constraints & Indexes:**
        * Consider the check constraints like `ck_models_source`[cite: 761], `ck_models_time_type`[cite: 762], `ck_models_one_clock_unit`[cite: 762], and the various tenant consistency checks (e.g., `ck_models_tenant_org_consistency`). These will primarily be enforced in the Alembic migration.
        * BaseEntity provides standard indexes. Note the additional specific indexes for the `models` table listed in the schema document (e.g., `ix_models_tenant_name`, `ix_models_tenant_created_by_user`).
* Add your new model to `app.db.models.__init__.py`.

### 2. Pydantic Schemas (`app.schemas.simulation_model.py` - new file)

* **Design and Implement Schemas:**
    * `ModelCreate`: What data is absolutely required to create a model? What fields have defaults (e.g., `reps`, `forecast_days`, `version`) that might be set by the service if not provided by the user? Consider `name`, `source`, `created_by_user_id`, and `tenant_id` as essential. Other simulation parameters might be optional in the `Create` schema, with defaults applied at the service or DB level.
    * `ModelRead`: How should a model be represented when fetched via the API? Include all relevant fields, perhaps nesting `UserRead` for `created_by_user` if desired.
    * `ModelUpdate`: Which fields of a model can be updated? Typically `name`, `description`, simulation parameters, `is_public`, `is_template`. `source` or `source_document_id` changes might imply a more complex "re-import" logic.
    * `ModelSummary` (Optional): A lightweight schema for listing models.
* Think about validation for fields like `source` (enum-like), `time_type`, etc.
* Add new schemas to `app.schemas.__init__.py`.

### 3. Repository (`app.repositories.model_repository.py` - new file)

* **Create `ModelRepository`:**
    * It should inherit from `BaseRepository[Model]`.
    * Initialize with the `Model` model.
* **Implement Key Methods (beyond basic CRUD from `BaseRepository`):**
    * `get_models_by_user(db: Session, tenant_id: UUID, user_id: UUID, skip: int, limit: int) -> List[Model]`.
    * `get_models_by_organization(db: Session, tenant_id: UUID, organization_id: UUID, skip: int, limit: int) -> List[Model]`.
    * `get_models_by_team(db: Session, tenant_id: UUID, team_id: UUID, skip: int, limit: int) -> List[Model]`.
    * `search_models_by_name(db: Session, tenant_id: UUID, name_query: str, skip: int, limit: int) -> List[Model]`.
    * `get_template_models(db: Session, tenant_id: Optional[UUID], skip: int, limit: int) -> List[Model]` (Note: `tenant_id` could be optional if templates can be global or system-wide).
* Ensure all repository methods correctly implement tenant isolation using `tenant_id`.
* Add to `app.repositories.__init__.py`.

### 4. Service Layer (`app.services.model_service.py` - new file)

* **Create `ModelService`:**
    * This service will orchestrate operations related to simulation models.
* **Implement Core Service Methods:**
    * `create_model(self, tenant_id: UUID, model_create_schema: ModelCreate, current_user_id: UUID) -> Model`:
        * Uses `ModelRepository` to persist the new model.
        * Applies default values for fields like `version`, `reps`, `forecast_days` if not provided in the schema, based on business rules or database defaults.
        * Ensures `created_by_user_id` is set.
        * Handles association with `organization_id` or `team_id` if provided, verifying tenant consistency.
    * `get_model_by_id(self, tenant_id: UUID, model_id: UUID) -> Optional[Model]`.
    * `update_model(self, tenant_id: UUID, model_id: UUID, model_update_schema: ModelUpdate, current_user_id: UUID) -> Optional[Model]`:
        * Implement authorization: Does the `current_user_id` have permission to update this model? (This might involve a future `ModelPermissionService`). For now, you might check if `current_user_id == model.created_by_user_id`.
        * Handle versioning if applicable (e.g., incrementing `version` on certain types of updates).
    * `delete_model(self, tenant_id: UUID, model_id: UUID, current_user_id: UUID) -> bool` (soft delete):
        * Permission check.
    * `list_models_for_tenant(self, tenant_id: UUID, skip: int, limit: int) -> List[Model]`.
    * `list_models_for_user(self, tenant_id: UUID, user_id: UUID, skip: int, limit: int) -> List[Model]`.
    * `create_model_from_template(self, tenant_id: UUID, template_model_id: UUID, new_model_name: str, current_user_id: UUID) -> Model`: Logic to copy a template model.
* Add to `app.services.__init__.py`.

### 5. API Endpoints (`app.api.routers.models.py` - new file)

* **Create a new FastAPI Router for Models:**
    * `POST /models/`: Create a new model within the authenticated user's tenant. Requires `ModelCreate` schema.
    * `GET /models/`: List models accessible to the current user within their tenant (consider pagination).
    * `GET /models/{model_id}`: Get details of a specific model.
    * `PUT /models/{model_id}`: Update a model. Requires `ModelUpdate` schema.
    * `DELETE /models/{model_id}`: Soft delete a model.
    * `POST /models/from-template/{template_model_id}`: Create a new model based on an existing template.
* These endpoints will use `ModelService` and depend on the current user's context (tenant and user ID).
* Consider query parameters for filtering list endpoints (e.g., by source, by template status).
* Integrate this new router into `app.api.api_router`.

### 6. Alembic Migration

* After defining the `Model` SQLAlchemy model:
    * Generate a new Alembic migration: `alembic revision -m "create_models_table"`
    * Inspect and meticulously edit the generated script:
        * Verify all columns, types, default values (e.g., `reps` DEFAULT 1[cite: 761], `version` DEFAULT 1 [cite: 765]), and nullability match the specifications from `030_Model Database Schema.md`.
        * Manually add all specified foreign keys (`fk_models_tenant`, `fk_models_created_by_user`[cite: 765], etc.).
        * Add all specified check constraints (`ck_models_source`[cite: 761], `ck_models_time_type`[cite: 762], tenant consistency checks).
        * Define all additional non-clustered indexes specified (e.g., `ix_models_tenant_name`, `ix_models_tenant_source`).
    * Apply the migration: `alembic upgrade head`.

### 7. Testing

* Write unit tests for:
    * `ModelRepository` methods (creating, fetching by various criteria).
    * `ModelService` methods (creation logic with defaults, updates, permission placeholders, deletion).
* Write integration tests for the new API endpoints for models. Test:
    * Model creation with minimal and full data.
    * Retrieval of single models and lists.
    * Updates to various fields.
    * Deletion.
    * Access control (basic checks, more thorough when permissions are formally implemented).

---

**Next Steps & Considerations:**
* This `models` table is a hub. The subsequent implementation of `entities`, `resources`, `activities`, etc., will all link back to it.
* Think about how `organization_id` and `team_id` on a model will interact with model permissions (to be implemented later from `050_Permissions and Security Database Schema.md`).
* The `source_document_id` and interaction with Lucidchart/Miro imply external API calls or parsing logic, which would be part of the `ModelService` but are beyond the scope of just setting up the table.

This task provides a significant piece of core functionality for Quodsi. Encourage the interns to be thorough, especially with the Alembic migration script, as it's the blueprint for the database structure.