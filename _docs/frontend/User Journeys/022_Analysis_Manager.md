### 2. User Journey: From Model List to Creating a New Analysis

This journey assumes the user has successfully logged into Quodsi and is on their dashboard.

**Step 1: Viewing the Model List (Model Manager)**

* **Action:** The user lands on the Quodsi dashboard, which prominently features the Model Manager view.
* **System Response:**
    * The Model Manager fetches and displays a list of models accessible to the user, respecting their `tenant_id` [cite: 318] and permissions derived from `models.created_by_user_id` [cite: 724] and the `model_permissions` table. [cite: 1176]
    * Each model is presented with key information (Name, Source, Last Updated, etc.) and available actions.
* **User Interaction:** The user scans the list, uses search/filter/sort options if necessary, and identifies the model they wish to work with.

**Step 2: Selecting a Model and Viewing its Analyses (Analysis Manager)**

* **Action:** The user clicks on a specific model's name or a "Manage Analyses" / "View Details" action associated with that model.
* **System Response:**
    * The UI transitions to an "Analysis Manager" view, scoped to the selected model.
    * This view displays a list of all analyses associated with the selected `model_id` [cite: 1352] by querying the `analyses` table. [cite: 1341]
    * Each analysis entry in the list shows:
        * `analyses.name` [cite: 1355]
        * `analyses.description` (briefly) [cite: 1358]
        * `analyses.default_reps` [cite: 1362]
        * `analyses.default_time_period` [cite: 1364]
        * Number of Scenarios (a count of related records in the `scenarios` table [cite: 1369]).
        * Status of the latest scenario run within that analysis (if applicable).
    * The Analysis Manager provides actions for each listed analysis:
        * **View/Manage Scenarios:** Navigates to the Scenario Manager for that analysis (as described in `ReactScenarios.TXT` [cite: 14]).
        * **Edit Analysis:** Allows modification of analysis properties.
        * **Duplicate Analysis:** Creates a copy of the analysis and its scenarios.
        * **Delete Analysis:** Soft deletes the analysis and its associated scenarios.
    * A prominent **"Create New Analysis"** button is visible within this view.

**Step 3: Creating a New Analysis for the Selected Model**

* **Action:** Within the Analysis Manager view for the chosen model, the user clicks the "Create New Analysis" button.
* **System Response:**
    * A modal dialog or a dedicated form page appears for creating a new analysis.
    * The `model_id` is implicitly set based on the current model context. [cite: 1352]
    * The `tenant_id` is inherited from the selected model. [cite: 1348]
    * The `created_by_user_id` is set to the currently logged-in user. [cite: 1366]
* **User Interaction (Form Fields):**
    * **Analysis Name (`analyses.name`):** User enters a unique name for this analysis within the context of the parent model. (Required) [cite: 1355]
    * **Description (`analyses.description`):** User provides an optional description for the analysis. [cite: 1358]
    * **Default Replications (`analyses.default_reps`):** User sets the default number of replications for scenarios under this analysis. Defaults to 1[cite: 1362], or could inherit from the parent model's default `reps` [cite: 694] if desired. (Required)
    * **Default Time Period (`analyses.default_time_period`):** User selects from predefined options (e.g., 'hourly', 'daily', 'monthly' [cite: 1364]). Could inherit from model's `time_type` [cite: 705] related settings. (Required)
* **Action:** User submits the form.
* **System Response (on successful submission):**
    * Input validation is performed.
    * A new record is created in the `analyses` table [cite: 1341] with the provided details, linked to the parent `model_id`[cite: 1352], `tenant_id`[cite: 1348], and `created_by_user_id`[cite: 1366].
    * The Analysis Manager list for the current model refreshes or dynamically updates to include the newly created analysis.
    * The user might be automatically navigated to the Scenario Manager view for this new, empty analysis, ready to create their first scenario.
    * A success notification is displayed.

### 3. Linking to Scenario Management

Once an analysis is created or selected from the Analysis Manager list, the user can click "View/Manage Scenarios." This action transitions them to the **Scenario Manager** interface for that specific analysis. 

* View a list of scenarios for the selected analysis. [cite: 26]
* Create new scenarios (inheriting defaults from the parent analysis). [cite: 133]
* Duplicate[cite: 46], remove (soft delete)[cite: 101], and run scenarios[cite: 76].
* View real-time updates on scenario states and progress. [cite: 163]
* Filter scenarios by state. [cite: 175]
* Access error messages for scenarios that ran with errors. [cite: 262]

This hierarchical approach (Dashboard -> Model Manager -> Analysis Manager -> Scenario Manager) provides a structured and intuitive way for users to navigate and manage their simulation studies within Quodsi.