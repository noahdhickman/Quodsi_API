## Quodsi Dashboard & User Journey: Model Management to Analysis Creation

This document describes a vision for the Quodsi user dashboard, specifically the "Model Manager" view, and outlines the user journey from viewing their models to creating a new analysis within a selected model.

### 1. Quodsi Dashboard: Model Manager View Vision

Upon logging in, the user is typically directed to their main dashboard. A key component of this dashboard is the **Model Manager**.

**Purpose:**
The Model Manager serves as the central hub for users to access, organize, and manage all simulation models they have rights to.

**Layout & Key Elements:**

* **Main Display Area:**
    * A list or card-based grid displaying models accessible to the user.
    * Each model entry should be a clear, actionable item.
* **Navigation/Controls:**
    * **"Create New Model" Button:** Prominently displayed to allow users to initiate the model creation process.
    * **Search Bar:** To quickly find models by name or keywords.
    * **Filtering Options:** Dropdowns or facets to filter models by:
        * Owner (My Models, Shared with Me, Organization Models)
        * Source (`lucidchart`, `standalone`, `miro`) [cite: 316, 685]
        * Tags (if implemented)
        * Status (e.g., Draft, Completed, Archived - if such statuses are added)
    * **Sorting Options:** To sort models by:
        * Name (A-Z, Z-A)
        * Last Updated (Newest, Oldest)
        * Date Created (Newest, Oldest)
        * Owner

**Model Entry Display:**
Each model listed in the Model Manager should display concise, key information:

* **`name`**: The primary identifier. [cite: 679]
* **`description`**: A brief summary (potentially truncated with a tooltip for full view). [cite: 682]
* **`source`**: Icon/label indicating if it's from LucidChart, Standalone, or Miro. [cite: 316, 685]
* **`updated_at`**: Date of the last modification. [cite: 322]
* **Ownership/Sharing Status**: Indication if the model is owned by the user, shared directly, or accessed via team/organization permissions. (e.g., "Owned by You," "Shared by \[User/Team Name]").
* **Quick Actions (on hover or via a kebab menu):**
    * Open / View Details
    * Edit (if permissions allow)
    * Manage Analyses
    * Share / Manage Permissions
    * Duplicate Model
    * Delete Model (soft delete, respecting permissions)

**Model Accessibility & Data Sourcing:**
The list of models displayed will be populated based on:

1.  Models where `models.created_by_user_id` matches the current user's ID. [cite: 724]
2.  Models shared with the user, their team, or their organization via the `model_permissions` table. [cite: 1172, 1176] The `permission_level` ('read', 'write', 'execute', 'admin') will determine available actions. [cite: 1200]
3.  Public models (`models.is_public = true`) [cite: 734] within the user's `tenant_id` or potentially globally, depending on the definition of "public."

All queries will be scoped by the user's `tenant_id`. [cite: 318]

**CRUD Operations on Models:**

* **Create:** Clicking "Create New Model" would launch a wizard or form where the user defines the model's properties (name, description, source, simulation parameters like reps, time_type, etc.). This creates a new record in the `models` table. [cite: 667]
* **Read/View:** Clicking on a model's name or an "Open" action would navigate the user to a detailed model view or directly to its "Analysis Manager" view.
* **Update:** An "Edit" action (available based on permissions) would allow modification of the model's properties in the `models` table.
* **Delete:** A "Delete" action (available based on permissions) would set `models.is_deleted = true`. [cite: 322]

