## Quodsi Standalone Application Layout (Azure DevOps Inspired)

This layout aims to replicate a familiar and efficient user experience, similar to Azure DevOps, for navigating Models, Analyses, and Scenarios within the Quodsi Standalone application. It prioritizes quick selection of a Model and Analysis, followed by focused work within the Scenario Manager.

### 1. Global Header

Spans the full width at the top, persistent across all views.

* **Far Left: Quodsi Logo & Application Name**
    * Clickable Quodsi logo (navigates to main Model Manager dashboard).
    * Text: "Quodsi" or "Quodsi Standalone."
* **Center (Optional): Global Search Bar**
    * Input field for searching Models, Analyses, Scenarios.
* **Far Right: Tenant, Notifications, User Profile & Actions**
    * **(Optional) Current Tenant Display:** `Tenant: [Tenant Name]` (from `tenants.name`).
    * **Notifications Icon:** (Bell icon) For system alerts, simulation completions, sharing notifications.
    * **Help Icon:** (Question mark icon) Links to documentation/support.
    * **User Profile Dropdown:**
        * Displays user's `display_name` or avatar. [cite: 2584, 2602]
        * Menu items:
            * **My Profile:** Manages details from `GET /v1/users/me`. [cite: 2601]
            * **Subscription:** Manages data from `GET /v1/subscription` and related billing/invoice endpoints. [cite: 2784]
            * **Cloud Connections:** Manages connections using `GET /v1/cloud-connections`. [cite: 2909]
            * **User Settings/Preferences:** (e.g., Animation preferences `GET /v1/users/me/animation-preferences`). [cite: 2857, 2903]
            * **Tenant Management (Admin only):** Access to tenant settings, user management (`GET /v1/tenant/users` [cite: 2643]), audit logs (`GET /v1/tenant/audit-logs` [cite: 2653]) based on `tenant_user_roles.role`. [cite: 299, 488, 502, 2286]
            * **Logout:** Calls `POST /v1/auth/logout`. [cite: 2586]

### 2. Left Vertical Navigation Pane

Collapsible pane on the left, context-sensitive based on the selected Model.

* **A. Project/Model Selector (Top of Nav or First Section):**
    * **Current Model Display:** Shows `models.name` of the active Model. [cite: 899]
    * **Model Switcher:** Dropdown/button to list and select from accessible Models (via `GET /v1/models` [cite: 2658]).
        * Each model entry shows `models.name` [cite: 899] and an icon for `models.source` (LucidChart, Standalone, Miro [cite: 905, 2200, 2261, 2311]).
    * **"+ New Model" Button/Link:** Initiates model creation (UI for `POST /v1/models` [cite: 2664]).

* **B. Model-Specific Navigation (Updates after Model selection):**
    * Lists views/services for the current Model.
    * **Overview:** (Optional) Summary page for the selected Model.
    * **Analyses:**
        * Primary navigation item.
        * **Behavior (Option 1 - Preferred):** Clicking "Analyses" loads the **Analysis Manager** (listing `analyses` for the current `model_id` via `GET /v1/models/{model_id}/analyses` [cite: 2679]) into the Main Content Area. Users select an Analysis from this main list to proceed.
        * **(Alternative) Behavior (Option 2 - Nested Nav):** "Analyses" expands *in the left nav* to list individual `analyses.name`. [cite: 1381, 2340] Clicking an analysis name loads its ScenarioManager directly into the main content.
    * **Permissions:** Manages `model_permissions` for the selected Model (`GET /v1/models/{model_id}/permissions` [cite: 2761]).
    * **Model Settings:** Edits selected Model properties (`PUT /v1/models/{model_id}` [cite: 2665]).
    * **(Future) Components:** Access to edit `entities`[cite: 2667], `activities`[cite: 2669], `resources` [cite: 2670] for standalone models.

* **C. Global/Application Sections (Bottom of Nav):**
    * **Dashboard/Home:** Returns to the main Model Manager view.
    * **Help**
    * **Settings** (Global User Preferences)

* **Visuals & Interaction:**
    * **Collapsible:** Button to shrink nav to icons, expanding on hover/click.
    * **Icons & Text:** For navigation items.
    * **Active State Indication:** Highlighting for the current Model and active section/analysis.

### 3. Main Content Area

Dynamically displays content based on Left Nav selections.

* **Initial/Dashboard View (No specific Model/Analysis selected):**
    * Displays the **Model Manager**: A list/grid of accessible models (data from `GET /v1/models` [cite: 2658]), with search, filter (by `source`[cite: 2659], `is_public`[cite: 2659], `is_template` [cite: 2659]), and sort capabilities.
    * Each model entry shows key info: `name`[cite: 2659], `description`[cite: 2659], `source`[cite: 2659], `updated_at`[cite: 2660], `analysis_count`[cite: 2660], `permission_level`[cite: 2660].

* **Model Selected > "Analyses" clicked (using preferred Behavior Option 1):**
    * Displays the **Analysis Manager**: A list/grid of `analyses` for the selected `model_id` (data from `GET /v1/models/{model_id}/analyses` [cite: 2679]).
    * Each analysis entry shows: `name`[cite: 2680], `description`[cite: 2680], `default_reps`[cite: 2680], `scenario_count`[cite: 2680], `last_run_at`[cite: 2680].
    * Includes a "+ New Analysis" button (UI for `POST /v1/models/{model_id}/analyses` [cite: 2682]).

* **Analysis Selected (from Analysis Manager or Left Nav nested list):**
    * Displays the **Scenario Manager**: This is the primary "deep work" area.
        * A clear header indicates: `Model: [models.name] / Analysis: [analyses.name]`
        * Lists scenarios for the active analysis (data from `GET /v1/analyses/{analysis_id}/scenarios` [cite: 2685]).
        * Each scenario entry shows: `name`[cite: 2686], `reps`[cite: 2686], `state`[cite: 2686], `progress_percentage`[cite: 2686], `parameter_overrides_count`[cite: 2686].
        * Toolbar for "Create New Scenario" (`POST /v1/analyses/{analysis_id}/scenarios` [cite: 2690]), filtering by `state`[cite: 2685], etc.
        * Row-level actions for scenarios: Run (`POST /v1/scenarios/{scenario_id}/execute` [cite: 2699]), Cancel (`POST /v1/scenarios/{scenario_id}/cancel` [cite: 2700]), Duplicate (`POST /v1/scenarios/{scenario_id}/duplicate` [cite: 2694]), Remove (soft delete `DELETE /v1/scenarios/{scenario_id}` [cite: 2693]), View Results (`GET /v1/scenarios/{scenario_id}/results` [cite: 2721]), Animate (`GET /v1/scenarios/{scenario_id}/results/animation` [cite: 2816, 2862]).

### How This Meets the "Quick Selection, Deep Work" Need:

1.  **Quick Model Selection:** The Model Selector in the Left Nav allows swift changing of the overarching Model context.
2.  **Quick Analysis Selection:** Once a Model is selected, its Analyses can be chosen either from a list in the main content area (Analysis Manager) or potentially a nested list in the Left Nav, leading quickly to the desired set of Scenarios.
3.  **Deep Work in ScenarioManager:** The Main Content Area is then fully dedicated to the feature-rich ScenarioManager, allowing users to focus on managing and interacting with scenarios. The Left Nav can be collapsed to maximize this workspace.
4.  **Context Awareness:** The Left Nav always indicates the active Model. The ScenarioManager (and Analysis Manager) will have clear headers/breadcrumbs indicating the current Model and Analysis context.
5.  **Efficient Navigation:** Users can easily switch between Analyses of the same Model or change Models entirely using the Left Nav, without excessive "backing out" through multiple full-page views if the Left Nav offers nested Analysis selection or if the main views load quickly.

This structure, inspired by Azure DevOps, provides a robust and familiar framework for Quodsi Standalone, catering to the specified user workflow.