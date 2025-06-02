# Task: Implement Scenario Management and Execution Features

**Objective:** Enable users to define, manage, and track individual simulation runs (scenarios) with specific parameter configurations. This involves implementing the `scenarios` table for overall scenario management and the `scenario_item_profiles` table for parameter overrides.

**Source Documents:**
* Primarily refer to: `062_Scenario Tables Database Schema.md` (the document you just provided) for detailed specifications of the `scenarios` and `scenario_item_profiles` tables.
* Recall existing patterns from `tenants`, `users`, `models`, `analyses`, and other previously implemented tables, especially the use of `BaseEntity`.

**Prerequisites:**
* The `analyses` table and its related components (model, schema, repository, service) must be implemented, as `scenarios` are children of an `analysis`.
* `models` and `users` tables must be available.

**General Guidelines:**
* **Adhere to Existing Architecture:** Implement new components following the established patterns:
    * SQLAlchemy Models (inheriting from `BaseEntity`)
    * Pydantic Schemas for API contracts and data transfer
    * Repositories (inheriting from `BaseRepository`) for data access logic, ensuring tenant isolation.
    * Services for business logic orchestration.
    * FastAPI Routers for API endpoints.
* **Database Migrations:** Use Alembic to generate and refine database migrations for the new tables.
* **Testing:** Write unit tests for new repository methods and service logic. Implement integration tests for new API endpoints.
* **Code Clarity & Comments:** Ensure your code is well-organized, readable, and appropriately commented.
* **Design Thinking:** While the database schemas are defined, you'll design:
    * Pydantic schemas for creating and managing scenarios and their parameter overrides.
    * Repository methods for querying scenarios and their profiles.
    * Service layer logic for scenario lifecycle (creation, state changes, execution tracking), and managing parameter overrides.
    * Clear API contracts for these operations.

---

## Module 1: `scenarios` Table Implementation

The `scenarios` table captures individual simulation runs, their configurations, execution state, and links to results.

### 1.1 Database Model (`app.db.models.scenario.py` - new file)

* **Create `Scenario` SQLAlchemy Model:**
    * Ensure it inherits from `app.db.models.base_entity.BaseEntity`.
    * Define all columns as specified in `062_Scenario Tables Database Schema.md` for `scenarios`. This includes:
        * Core info: `name`, `description`.
        * Link to parent analysis: `analysis_id`.
        * Configuration: `reps`, `time_period`.
        * Execution tracking: `state`, `current_rep`, `total_reps`, `progress_percentage`, `started_at`, `completed_at`, `execution_time_ms`.
        * Error handling: `error_message`, `error_details`, `error_stack_trace`.
        * Results link: `blob_storage_path`.
        * Ownership: `created_by_user_id`.
    * **Relationships & Foreign Keys:**
        * The `tenant_id` FK is inherited.
        * FK for `analysis_id` to `analyses.id` (with `ON DELETE CASCADE`).
        * FK for `created_by_user_id` to `users.id`.
        * Define SQLAlchemy `relationship()`:
            * On `Analysis` model: to navigate to its scenarios (e.g., `analysis.scenarios`).
            * On `User` model: to navigate to scenarios created by a user (e.g., `user.scenarios`).
            * You will later add a one-to-many relationship from `Scenario` to `ScenarioItemProfile` (e.g., `scenario.item_profiles`).
    * **Constraints & Indexes:**
        * Note check constraints: `ck_scenarios_time_period`, `ck_scenarios_state`, and tenant consistency checks.
        * Note unique constraint: `uq_scenarios_tenant_analysis_name`.
        * Be aware of specific indexes like `ix_scenarios_tenant_analysis`, `ix_scenarios_tenant_state`.
* Add your new model to `app.db.models.__init__.py`.

### 1.2 Pydantic Schemas (`app.schemas.scenario.py` - new file)

* **Design and Implement Schemas:**
    * `ScenarioCreate`:
        * Required: `name`, `analysis_id`.
        * Optional: `description`, `reps`, `time_period`. The service can inherit defaults from the parent `Analysis` if not provided.
    * `ScenarioRead`:
        * All relevant fields from the `Scenario` model.
        * Consider nesting `AnalysisRead` and `UserRead`.
        * Will eventually include `ScenarioItemProfileRead` list.
    * `ScenarioUpdate`:
        * Fields like `name`, `description`, `reps`, `time_period`. Updating `state` should likely be handled by specific service methods (e.g., `run_scenario`, `cancel_scenario`).
    * `ScenarioStateUpdate` (Internal/Service use or specific endpoint): For updating execution progress fields.
    * `ScenarioSummary` (Optional): Lightweight for lists.
* Add new schemas to `app.schemas.__init__.py`.

### 1.3 Repository (`app.repositories.scenario_repository.py` - new file)

* **Create `ScenarioRepository`:**
    * Inherit from `BaseRepository[Scenario]`.
    * Initialize with `Scenario` model.
* **Implement Key Methods:**
    * `get_scenarios_by_analysis_id(db: Session, tenant_id: UUID, analysis_id: UUID, skip: int, limit: int) -> List[Scenario]`.
    * `get_scenarios_by_state(db: Session, tenant_id: UUID, state: str, skip: int, limit: int) -> List[Scenario]`.
    * `update_scenario_status(db: Session, tenant_id: UUID, scenario_id: UUID, new_state: str, progress_details: Optional[dict] = None) -> Optional[Scenario]`: Helper to update execution-related fields.
* Add to `app.repositories.__init__.py`.

### 1.4 Service Layer (`app.services.scenario_service.py` - new file)

* **Create `ScenarioService`:**
* **Implement Core Service Methods:**
    * `create_scenario(self, tenant_id: UUID, scenario_create_schema: ScenarioCreate, current_user_id: UUID) -> Scenario`:
        * Fetches parent `Analysis` to get defaults for `reps`, `time_period` if not in `scenario_create_schema`.
        * Sets `created_by_user_id`, `state` (e.g., 'not_ready_to_run').
    * `get_scenario_details(self, tenant_id: UUID, scenario_id: UUID) -> Optional[Scenario]`.
    * `update_scenario_metadata(self, tenant_id: UUID, scenario_id: UUID, scenario_update_schema: ScenarioUpdate, current_user_id: UUID) -> Optional[Scenario]` (for name, description etc.).
    * `delete_scenario(self, tenant_id: UUID, scenario_id: UUID, current_user_id: UUID) -> bool`.
    * `list_scenarios_for_analysis(self, tenant_id: UUID, analysis_id: UUID, skip: int, limit: int) -> List[Scenario]`.
    * **Execution Lifecycle Methods (Crucial for later integration with a simulation engine):**
        * `prepare_scenario_for_run(self, tenant_id: UUID, scenario_id: UUID) -> bool`: Sets state to 'ready_to_run'.
        * `start_scenario_run(self, tenant_id: UUID, scenario_id: UUID) -> bool`: Sets state to 'is_running', `started_at`.
        * `update_scenario_progress(self, tenant_id: UUID, scenario_id: UUID, current_rep: int, total_reps: int, progress_percentage: float) -> bool`.
        * `complete_scenario_run(self, tenant_id: UUID, scenario_id: UUID, execution_time_ms: int, blob_storage_path: str) -> bool`: Sets state to 'ran_success', `completed_at`.
        * `fail_scenario_run(self, tenant_id: UUID, scenario_id: UUID, error_message: str, error_details: Optional[str], error_stack_trace: Optional[str]) -> bool`: Sets state to 'ran_with_errors'.
* Add to `app.services.__init__.py`.

### 1.5 API Endpoints (`app.api.routers.scenarios.py` - new file)

* **Create a new FastAPI Router for Scenarios:**
    * `POST /scenarios/`: Create a new scenario (under an analysis specified in payload).
    * `GET /analyses/{analysis_id}/scenarios/`: List scenarios for a specific analysis.
    * `GET /scenarios/{scenario_id}`: Get scenario details.
    * `PUT /scenarios/{scenario_id}`: Update scenario metadata.
    * `DELETE /scenarios/{scenario_id}`: Soft delete a scenario.
    * **Endpoints for Execution Control (may need protection/specific roles):**
        * `POST /scenarios/{scenario_id}/run`: Triggers scenario execution (changes state via service).
        * `POST /scenarios/{scenario_id}/cancel`: Attempts to cancel a running scenario.
        * `GET /scenarios/{scenario_id}/status`: Get current execution status/progress.
* Integrate this new router into `app.api.api_router`.

### 1.6 Alembic Migration for `scenarios`

* After defining `Scenario` model:
    * Generate: `alembic revision -m "create_scenarios_table"`
    * Edit: Verify columns, types, defaults (e.g., `state` DEFAULT 'not_ready_to_run'), FKs (`ON DELETE CASCADE` for `analysis_id`), check constraints (`ck_scenarios_state`), unique constraints (`uq_scenarios_tenant_analysis_name`), and indexes.
    * Apply: `alembic upgrade head`.

### 1.7 Testing for `scenarios`

* Unit tests for `ScenarioRepository` and `ScenarioService` methods (especially lifecycle and state transitions).
* Integration tests for API endpoints.

---

## Module 2: `scenario_item_profiles` Table Implementation

This table allows users to override specific parameters of model components (activities, resources, etc.) for a particular scenario, enabling "what-if" analysis.

### 2.1 Database Model (`app.db.models.scenario_item_profile.py` - new file, or extend `scenario.py`)

* **Create `ScenarioItemProfile` SQLAlchemy Model:**
    * Inherit from `BaseEntity`.
    * Define columns: `scenario_id`, `target_object_id`, `target_object_type`, `property_name`, `property_value`, `original_value`, `description`, `change_reason`.
    * **Relationships & Foreign Keys:**
        * FK for `scenario_id` to `scenarios.id` (`ON DELETE CASCADE`).
        * `target_object_id` is a generic ID; `target_object_type` discriminates (e.g., 'activity', 'resource'). No direct FK here, but application logic must ensure validity.
        * Define `relationship()` on `Scenario` model: `item_profiles = relationship("ScenarioItemProfile", ...)`
    * **Constraints & Indexes:**
        * Note `ck_scenario_item_profiles_target_type` check constraint.
        * Note `uq_scenprofiles_tenant_scenario_target_prop` unique constraint.
* Add model to `app.db.models.__init__.py`.

### 2.2 Pydantic Schemas (`app.schemas.scenario_item_profile.py` - new file, or extend `scenario.py`)

* **Design and Implement Schemas:**
    * `ScenarioItemProfileCreate`: `scenario_id` (often path param), `target_object_id`, `target_object_type`, `property_name`, `property_value`, optional `description`, `change_reason`.
    * `ScenarioItemProfileRead`: All fields.
    * `ScenarioItemProfileUpdate`: Probably just `property_value` and `description`/`change_reason`.
* Add new schemas to `app.schemas.__init__.py`.

### 2.3 Repository (`app.repositories.scenario_item_profile_repository.py` - new file)

* **Create `ScenarioItemProfileRepository`:**
    * Inherit `BaseRepository[ScenarioItemProfile]`.
* **Implement Key Methods:**
    * `get_profiles_for_scenario(db: Session, tenant_id: UUID, scenario_id: UUID) -> List[ScenarioItemProfile]`.
    * `get_profile_for_target_property(db: Session, tenant_id: UUID, scenario_id: UUID, target_object_id: UUID, property_name: str) -> Optional[ScenarioItemProfile]`.
    * `delete_profiles_for_scenario(db: Session, tenant_id: UUID, scenario_id: UUID) -> int`: Returns number of profiles deleted.
* Add to `app.repositories.__init__.py`.

### 2.4 Service Layer (`app.services.scenario_service.py` - extend existing)

* **Extend `ScenarioService` with Item Profile Logic:**
    * `add_item_profile_to_scenario(self, tenant_id: UUID, scenario_id: UUID, profile_create_schema: ScenarioItemProfileCreate, current_user_id: UUID) -> ScenarioItemProfile`:
        * Validates `target_object_type` and potentially `target_object_id` against the parent scenario's model.
        * May fetch and store `original_value` from the base model component.
    * `update_item_profile(self, tenant_id: UUID, profile_id: UUID, profile_update_schema: ScenarioItemProfileUpdate, current_user_id: UUID) -> Optional[ScenarioItemProfile]`.
    * `remove_item_profile(self, tenant_id: UUID, profile_id: UUID, current_user_id: UUID) -> bool`.
    * `get_item_profiles_for_scenario(self, tenant_id: UUID, scenario_id: UUID) -> List[ScenarioItemProfileRead]`.
    * `apply_scenario_profiles_to_model_data(self, tenant_id: UUID, scenario_id: UUID) -> dict`: This is a complex method that would fetch a base model's configuration and then overlay the `scenario_item_profiles` to produce the specific configuration for *this* scenario run. This resulting configuration would then be passed to the simulation engine.

### 2.5 API Endpoints (`app.api.routers.scenarios.py` - extend existing router, or a new sub-router)

* **Add/Modify Endpoints for Scenario Item Profiles:**
    * `POST /scenarios/{scenario_id}/profiles/`: Add a parameter override to a scenario.
    * `GET /scenarios/{scenario_id}/profiles/`: List all overrides for a scenario.
    * `GET /scenarios/{scenario_id}/profiles/{profile_id}`: Get a specific override.
    * `PUT /scenarios/{scenario_id}/profiles/{profile_id}`: Update an override.
    * `DELETE /scenarios/{scenario_id}/profiles/{profile_id}`: Remove an override.

### 2.6 Alembic Migration for `scenario_item_profiles`

* After defining `ScenarioItemProfile` model:
    * Generate: `alembic revision -m "create_scenario_item_profiles_table"`
    * Edit: Verify columns, types, FKs (`ON DELETE CASCADE` for `scenario_id`), check constraints (`ck_scenario_item_profiles_target_type`), unique constraints (`uq_scenprofiles_tenant_scenario_target_prop`), and indexes.
    * Apply: `alembic upgrade head`.

### 2.7 Testing for `scenario_item_profiles`

* Unit tests for repository and service methods related to managing item profiles.
* Integration tests for the API endpoints. Test adding, listing, updating, deleting overrides.

---

**Final Steps for Both Modules:**
* **Code Review:** Critical for these interconnected components.
* **Testing:** Ensure comprehensive test coverage.
* **Merge:** Integrate into the main codebase.

This module is core to the "what-if" analysis capabilities of Quodsi. The `scenario_item_profiles` table, in particular, enables the flexibility needed for experimentation. The interaction between scenarios and the actual simulation engine (which is external to this schema) will be a key integration point for the `ScenarioService`.