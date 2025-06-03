# Quodsi User Journey: Returning User Login & Engagement

This document outlines the typical journey for a returning Quodsi user, focusing on their login experience and subsequent interactions with the platform. This journey assumes the user has already completed the initial registration and first-time login.

## Assumptions:

* The user has an existing Quodsi account and is associated with a `tenant_id`.
* The user may have already created or interacted with models, analyses, or scenarios.
* The user's `users` table record exists, potentially with previous `last_login_at` and `login_count` data[cite: 1492, 1495].

## User Journey Steps:

**Step 1: User Navigates to Quodsi & Initiates Login**

* **Action:** The user opens their web browser and navigates to `www.quodsi.com` (or a bookmarked login page).
* **System Response:** The Quodsi homepage or login page is displayed.
* **User Interaction:** The user clicks the "Sign In" or "Login" button.

**Step 2: User Authenticates**

* **Action:** The user is presented with the login interface.
* **User Interaction:**
    * The user enters their registered email address and password.
    * Alternatively, if they registered using a federated identity provider (e.g., Microsoft Entra ID, Google), they select that option and authenticate through the provider's flow.
* **System Response:**
    * The system authenticates the user against its database or via the federated identity provider.
    * Upon successful authentication:
        * A new record is created in the `user_sessions` table. This record includes the `user_id`, `tenant_id`, `created_at` (as session start time), `client_info`, and `ip_address`[cite: 1524, 1520, 1537, 1540].
        * The user's record in the `users` table is updated:
            * `last_login_at` is set to the current timestamp[cite: 1492].
            * `login_count` is incremented[cite: 1495].
            * `last_session_start` is updated to the current session's start time[cite: 1501].
            * `last_active_at` is updated to the current timestamp[cite: 1504].

**Step 3: Landing on the Dashboard (Typically Model Manager View)**

* **Action:** After successful login, the user is redirected to their personalized Quodsi dashboard.
* **System Response:**
    * The dashboard, often defaulting to the "Model Manager" view, loads.
    * The system fetches and displays models accessible to the user based on:
        * Models where `models.created_by_user_id` matches the current user's ID[cite: 723].
        * Models shared with the user, their team, or organization via the `model_permissions` table[cite: 1189, 1192, 1195].
        * Public models (`models.is_public = true`) within the user's `tenant_id`[cite: 731].
    * The dashboard might remember and apply the user's last used filter or sort preferences for the model list (a common UX enhancement).

**Step 4: Typical Returning User Activities**

Once logged in, a returning user might engage in various activities:

* **A. Checking Status of Ongoing Work:**
    * Navigating to the ScenarioManager for a specific Analysis to check the `state` of previously run `scenarios` (e.g., looking for "RanSuccess," "RanWithErrors," or if "IsRunning" scenarios have completed)[cite: 16, 164, 262, 1395].
    * Reviewing progress indicators for any scenarios still in the "IsRunning" state[cite: 166, 167].
* **B. Continuing Existing Work:**
    * Selecting a model from the Model Manager, then an analysis, and then proceeding to the ScenarioManager to:
        * Modify parameters of existing scenarios (updating `scenario_item_profiles`)[cite: 20, 1434].
        * Create new scenarios within that analysis[cite: 136].
    * Opening a model to edit its core properties (e.g., `name`, `description`, simulation parameters in the `models` table).
    * Modifying properties of an existing `analysis`[cite: 1354, 1356, 1359, 1363].
* **C. Starting New Work:**
    * Clicking "Create New Model" from the Model Manager to define a new simulation model[cite: 667].
    * Navigating to an existing model and creating a new `analysis` within it[cite: 1341].
    * Opening an existing analysis and creating new `scenarios`[cite: 1369].
* **D. Managing Models, Analyses, or Scenarios:**
    * Using "Duplicate Scenario" functionality to iterate on existing setups[cite: 46, 53].
    * Using "Remove Scenario" (soft delete) for scenarios no longer actively needed[cite: 100, 109, 110].
    * Managing permissions for a model via the `model_permissions` table if they are an owner or have admin rights to the model[cite: 1176, 1200].
* **E. Collaborating:**
    * Accessing and potentially editing models or scenarios shared by other team members (based on `model_permissions`)[cite: 1176].
* **F. Account or Subscription Management (Less Frequent):**
    * Checking current `tenant_usage` (e.g., `current_models`, `scenarios_this_month`) against their `tenants` plan limits (`max_models`, `max_scenarios_per_month`)[cite: 534, 1103, 1106, 980, 1020, 1023].
    * If they are an admin/owner, navigating to settings to manage `tenant_settings` or aspects of their `organization_subscriptions` or `user_subscriptions`[cite: 529, 1047, 1753, 1716].

**Step 5: User Activity & Session Management**

* **System Response:**
    * As the user interacts with various features, their `users.last_active_at` timestamp is periodically updated to reflect their ongoing engagement[cite: 1504].
    * The current `user_sessions` record remains active.

**Step 6: User Logs Out or Session Ends**

* **A. Explicit Logout:**
    * **User Interaction:** The user clicks a "Logout" or "Sign Out" button.
    * **System Response:**
        * The current record in `user_sessions` is updated: `ended_at` is set to the current timestamp, and `duration_minutes` is calculated and stored[cite: 1527, 1531].
        * The user's `users.total_usage_minutes` might be updated by adding the calculated session duration[cite: 1498].
        * The user is redirected to the login page or homepage.
* **B. Session Timeout (Implicit Logout):**
    * **System Response:** If the user's session is inactive for a predefined period:
        * The backend identifies the inactive session.
        * The `user_sessions` record is updated similarly to an explicit logout (`ended_at`, `duration_minutes`)[cite: 1527, 1531].
        * `users.total_usage_minutes` can be updated[cite: 1498].
        * The next time the user tries to access the application, they will be required to log in again.

## Conclusion:

The journey for a returning user is focused on providing seamless re-entry into their workspace, easy access to their ongoing projects, and clear status updates. The system leverages stored preferences (potentially for filters/sorts) and session data to make the experience efficient and personalized.