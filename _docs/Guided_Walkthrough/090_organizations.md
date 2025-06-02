# Task: Implement User Organization Management Features

**Objective:** Enhance the Quodsi application by adding B2B organizational capabilities within tenants. This involves creating structures to represent customer organizations and managing user memberships and roles within them.

**Source Documents:**
* Primarily refer to: `Quodsi SaaS App/database/schemas/011_User_Organization_Management.md` for detailed specifications of the `organizations` and `organization_memberships` tables[cite: 1].
* Recall existing patterns from `users` and `tenants` table implementations and the `BaseEntity` structure.

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
* **Design Thinking:** The database schema provides the structure. Your role is to design the Pydantic schemas, repository method signatures, service layer interactions, API contracts, and any supporting logic to bring these tables to life. Consider the user stories: How will an admin create an organization? How will users be added? What information is needed at each step?

---

## Module 1: `organizations` Table Implementation

The `organizations` table will represent customer organizations or distinct business units *within* a tenant, often used for B2B subscriptions or departmental separation.

### 1.1 Database Model (`app.db.models.organization.py` - new file)

* **Create `Organization` SQLAlchemy Model:**
    * Ensure it inherits from `app.db.models.base_entity.BaseEntity`.
    * Define all columns as specified in `011_User_Organization_Management.md` for `organizations`[cite: 1]. Key fields include: `name`, `domain`, `billing_email`, `billing_address`, `stripe_customer_id`, `metadata`.
    * **Relationships & Foreign Keys:**
        * The crucial `tenant_id` FK is inherited from `BaseEntity` and links to `tenants.id`[cite: 1].
        * Consider the `OrganizationMembership` relationship (one-to-many: one organization to many memberships) that will be defined when `OrganizationMembership` model is created. You can add a `memberships` back-reference here if desired.
    * **Constraints & Indexes:**
        * Note the unique constraint `ix_organizations_tenant_name` (name unique within a tenant)[cite: 1].
        * The `ck_organizations_domain_format` check constraint should be considered[cite: 1].
* Add your new model to `app.db.models.__init__.py`.

### 1.2 Pydantic Schemas (`app.schemas.organization.py` - new file)

* **Design and Implement Schemas:**
    * `OrganizationCreate`: What data is needed to create an organization? (e.g., `name`, `tenant_id`, optional `domain`, `billing_email`).
    * `OrganizationRead`: What data should be returned when an organization is queried? (e.g., `id`, `name`, `domain`, `tenant_id`, `created_at`).
    * `OrganizationUpdate`: What fields of an organization can be updated?
* Add new schemas to `app.schemas.__init__.py`.

### 1.3 Repository (`app.repositories.organization_repository.py` - new file)

* **Create `OrganizationRepository`:**
    * It should inherit from `BaseRepository[Organization]`.
    * Initialize with the `Organization` model.
* **Implement Key Methods (examples from specs):**
    * `get_by_name(db: Session, tenant_id: UUID, name: str) -> Optional[Organization]`: Finds an organization by name within a specific tenant.
    * `get_by_domain(db: Session, tenant_id: UUID, domain: str) -> List[Organization]`: Finds organizations by domain within a tenant.
    * (The spec also includes `get_user_organizations` and `get_organization_members`, but these heavily involve `OrganizationMembership`, so they might be implemented or fleshed out more when the `OrganizationMembershipRepository` exists or as part of a combined service logic).
* Ensure all methods strictly enforce `tenant_id` scoping.
* Add to `app.repositories.__init__.py`.

### 1.4 Service Layer (`app.services.organization_service.py` - new file)

* **Create `OrganizationService`:**
    * This service will orchestrate operations related to organizations.
* **Implement Core Service Methods:**
    * `create_organization(self, tenant_id: UUID, org_create_schema: OrganizationCreate, current_user_id: UUID) -> Organization`:
        * Uses `OrganizationRepository` to persist the new organization.
        * Potentially, the user creating the organization could be automatically made the 'owner' or 'admin' of it via an `OrganizationMembership` record (this links to Module 2).
    * `get_organization_by_id(self, tenant_id: UUID, organization_id: UUID) -> Optional[Organization]`.
    * `update_organization(self, tenant_id: UUID, organization_id: UUID, org_update_schema: OrganizationUpdate) -> Optional[Organization]`.
    * `delete_organization(self, tenant_id: UUID, organization_id: UUID) -> bool` (soft delete).
    * `list_organizations_for_tenant(self, tenant_id: UUID, skip: int, limit: int) -> List[Organization]`.
* Add to `app.services.__init__.py`.

### 1.5 API Endpoints (`app.api.routers.organizations.py` - new file)

* **Create a new FastAPI Router for Organizations:**
    * `POST /organizations/`: Create a new organization within the authenticated user's tenant.
    * `GET /organizations/`: List organizations for the current tenant.
    * `GET /organizations/{organization_id}`: Get details of a specific organization.
    * `PUT /organizations/{organization_id}`: Update an organization.
    * `DELETE /organizations/{organization_id}`: Soft delete an organization.
* These endpoints will use `OrganizationService` and depend on the current user's tenant context.
* Integrate this new router into `app.api.api_router`.

### 1.6 Alembic Migration

* After defining the `Organization` model:
    * Generate: `alembic revision -m "create_organizations_table"`
    * Edit: Ensure columns, types, indexes (e.g., `ix_organizations_tenant_name`, `ix_organizations_tenant_domain`)[cite: 1], and constraints (`fk_organizations_tenant`, `ck_organizations_domain_format`) [cite: 1] match the specifications.
    * Apply: `alembic upgrade head`.

### 1.7 Testing

* Unit tests for `OrganizationRepository` methods.
* Unit tests for `OrganizationService` methods.
* Integration tests for the new API endpoints.

---

## Module 2: `organization_memberships` Table Implementation

The `organization_memberships` table links users to the organizations created above, defining their role and status within that organization.

### 2.1 Database Model (`app.db.models.organization_membership.py` - new file, or extend `organization.py`)

* **Create `OrganizationMembership` SQLAlchemy Model:**
    * Inherit from `BaseEntity`.
    * Define columns as per specs[cite: 1]: `organization_id`, `user_id`, `role`, `invited_by_user_id`, `status`, `last_active_at`.
    * **Relationships & Foreign Keys:**
        * FK to `organizations.id` (`organization_id`)[cite: 1].
        * FK to `users.id` (`user_id`)[cite: 1].
        * FK to `users.id` (`invited_by_user_id`, nullable)[cite: 1].
        * Define `relationship()` attributes on `Organization` (e.g., `members`) and `User` (e.g., `organization_memberships`) to navigate these connections.
    * **Constraints & Indexes:**
        * Note the unique constraint `uq_organization_memberships_tenant_org_user` (a user can only have one active membership per organization within a tenant)[cite: 1].
        * Check constraints for `role` and `status` (`ck_organization_memberships_role`, `ck_organization_memberships_status`)[cite: 1].
        * The important `ck_orgmembers_tenant_consistency` constraint ensuring the user, organization, and membership all share the same `tenant_id`[cite: 1].
* Add model to `app.db.models.__init__.py`.

### 2.2 Pydantic Schemas (`app.schemas.organization_membership.py` - new file, or extend `organization.py`)

* **Design and Implement Schemas:**
    * `OrganizationMembershipCreate`: To add/invite a user to an organization (needs `organization_id`, `user_id`, `role`, `status`).
    * `OrganizationMembershipRead`: To display membership details (e.g., user info, organization info, role). This might involve nested schemas.
    * `OrganizationMembershipUpdate`: To change a user's role or status within an organization.
* Add new schemas to `app.schemas.__init__.py`.

### 2.3 Repository (`app.repositories.organization_membership_repository.py` - new file, or extend `organization_repository.py`)

* **Create `OrganizationMembershipRepository`:**
    * Inherit from `BaseRepository[OrganizationMembership]`.
* **Implement Key Methods (examples from specs [cite: 1]):**
    * `add_member(db: Session, tenant_id: UUID, organization_id: UUID, user_id: UUID, role: str, invited_by_user_id: Optional[UUID]=None, status: str = 'active') -> OrganizationMembership`.
    * `get_membership(db: Session, tenant_id: UUID, organization_id: UUID, user_id: UUID) -> Optional[OrganizationMembership]`.
    * `update_member_role_or_status(db: Session, membership_id: UUID, tenant_id: UUID, new_role: Optional[str], new_status: Optional[str]) -> Optional[OrganizationMembership]`.
    * `remove_member(db: Session, membership_id: UUID, tenant_id: UUID) -> bool` (soft delete).
    * `get_members_of_organization(db: Session, tenant_id: UUID, organization_id: UUID, skip: int, limit: int) -> List[OrganizationMembership]`.
    * `get_organizations_for_user(db: Session, tenant_id: UUID, user_id: UUID, skip: int, limit: int) -> List[OrganizationMembership]`.
* Add to `app.repositories.__init__.py`.

### 2.4 Service Layer (`app.services.organization_service.py` - extend existing)

* **Extend `OrganizationService` with Membership Logic:**
    * `invite_user_to_organization(self, tenant_id: UUID, organization_id: UUID, invitee_user_id: UUID, role: str, inviter_user_id: UUID) -> OrganizationMembership`:
        * Uses `OrganizationMembershipRepository`.
        * May involve sending notifications (out of scope for DB/API layer for now).
        * Handles logic from spec `invite_user_to_organization` example, including `find_or_create_user_by_email` (this implies `UserService` might be needed or a similar utility). For simplicity, assume `invitee_user_id` is known.
    * `accept_invitation(self, tenant_id: UUID, membership_id: UUID) -> OrganizationMembership`: Changes membership status from 'invited' to 'active'.
    * `remove_user_from_organization(self, tenant_id: UUID, organization_id: UUID, user_id: UUID) -> bool`.
    * `update_user_role_in_organization(self, tenant_id: UUID, organization_id: UUID, user_id: UUID, new_role: str) -> Optional[OrganizationMembership]`.
    * `list_organization_members(self, tenant_id: UUID, organization_id: UUID) -> List[OrganizationMembershipRead]`.
    * `list_user_organizations(self, tenant_id: UUID, user_id: UUID) -> List[OrganizationRead]`.
    * The example `create_organization_with_owner` logic [cite: 1] from the spec should be implemented here: when an organization is created, the creator (current user) is automatically added as an 'owner' to `organization_memberships`.

### 2.5 API Endpoints (`app.api.routers.organizations.py` - extend existing)

* **Add/Modify Endpoints in the Organizations Router:**
    * `POST /organizations/{organization_id}/members`: Invite/add a user to an organization.
    * `GET /organizations/{organization_id}/members`: List members of an organization.
    * `PUT /organizations/{organization_id}/members/{user_id}`: Update a user's role/status in an organization.
    * `DELETE /organizations/{organization_id}/members/{user_id}`: Remove a user from an organization.
    * `GET /users/{user_id}/organizations`: List organizations a specific user belongs to (consider if this belongs in a user-centric router or here).
* Ensure appropriate permission checks (e.g., only an admin/owner of an organization can add/remove members). This is where RBAC from `tenant_user_roles` or specific logic in `OrganizationService` will be important.

### 2.6 Alembic Migration

* After defining the `OrganizationMembership` model:
    * Generate: `alembic revision -m "create_organization_memberships_table"`
    * Edit: Ensure columns, FKs, unique constraints (like `uq_organization_memberships_tenant_org_user`)[cite: 1], check constraints (`ck_organization_memberships_role`, `ck_organization_memberships_status`, `ck_orgmembers_tenant_consistency`)[cite: 1], and indexes match the specs.
    * Apply: `alembic upgrade head`.

### 2.7 Testing

* Unit tests for `OrganizationMembershipRepository` methods.
* Unit tests for `OrganizationService` methods related to membership management and role logic.
* Integration tests for the new API endpoints for managing organization members. Test scenarios like inviting a user, accepting an invitation, changing roles, removing members.

---

**Final Steps for Both Modules:**
* **Code Review:** Essential for learning and quality.
* **Testing:** Verify all logic paths and API responses.
* **Merge:** Integrate into the main codebase.

This plan provides a structured way for your interns to tackle these B2B features, building upon their existing knowledge and the provided detailed database schemas. Remember to encourage them to discuss how `organizations` and `organization_memberships` will be used by other upcoming features (like Teams or Model Permissions) to inform their Pydantic schema and service method designs.