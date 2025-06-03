## ScenarioManager: Vision & Features

### 1. Overview and Purpose

The ScenarioManager is a sophisticated user interface within the Quodsi Standalone application, designed for managing, executing, and analyzing simulation scenarios. [cite: 14] It provides users with a comprehensive suite of tools to interact with scenarios derived from an Analysis, which itself is a container for multiple scenarios and holds default property values. [cite: 14, 15] The primary goal of the ScenarioManager is to offer an efficient and intuitive environment for users to conduct simulation studies.

### 2. Core Data Context

The ScenarioManager operates on `Scenario` entities. Key properties of a scenario include:

* **Id** (UUID): Unique identifier. [cite: 16]

* **Name**: Must be unique within its parent Analysis. [cite: 17]

* **Reps**: Default value of 1. [cite: 17]

* **ParentAnalysisId**: UUID of the parent Analysis. [cite: 18]

* **TimePeriod**: Enum (Hourly, Daily, Monthly). [cite: 18]

* **State**: Tracks the scenario's lifecycle (e.g., "NotReadyToRun," "ReadyToRun," "IsRunning," "RanSuccess," "RanWithErrors," "Cancelling"). [cite: 25, 77, 79, 80, 86, 135, 147, 176, 235, 243, 262]

Scenarios can also have child datasets like `Scenario Items Profile` to define changes to base item properties. [cite: 20]

### 3. Key UI Components & Layout

The ScenarioManager UI will be designed for clarity and ease of use, likely featuring:

* **Scenario Display Area:**

  * A primary view for listing scenarios, supporting either a **Basic Table/Datagrid** format [cite: 26] or an **Advanced Table/Datagrid** with more features. [cite: 23, 213]

  * The option to toggle between different display modes (e.g., table view vs. a more detailed property view per scenario) using a **Hybrid Scenario Display Toggle**. [cite: 284, 285]

* **Toolbar:**

  * A collection of icon-based buttons for global actions such as "Create New Scenario," filtering, sorting, and toggling display views. [cite: 186, 187]

  * All toolbar icons will have descriptive **Tooltips**. [cite: 186, 190]

* **Action Controls per Scenario:**

  * Contextual buttons/icons available for each scenario in the list, enabling actions like:

    * **Play/Run Scenario** [cite: 76]

    * **Cancel Scenario Run** [cite: 234]

    * **Duplicate Scenario** [cite: 46, 49]

    * **Remove Scenario** (soft delete) [cite: 100, 104]

    * **Animate Scenario** (new feature)

### 4. Core Features

#### 4.1. Scenario Display & Interaction

* **Basic Table/Datagrid Display:**

  * Scenarios displayed with each row representing a scenario and columns for key properties. [cite: 26]

  * Fixed essential columns. [cite: 27]

  * Responsive design with vertical/horizontal scrolling and sticky headers. [cite: 28, 29, 30, 33]

  * Handling for long text (e.g., truncation with tooltip). [cite: 31]

  * Keyboard navigation and accessibility support. [cite: 35]

  * Potential for alternating row colors and basic search. [cite: 37, 38]

* **Advanced Table/Datagrid Features:**

  * Column sorting. [cite: 23, 213]

  * Multi-property filtering and filter presets. [cite: 23, 214, 218]

  * Pagination or infinite scrolling for large datasets. [cite: 23, 215]

  * Column customization (visibility, adjustable widths, reordering). [cite: 23, 216, 217]

  * Multi-select functionality for bulk actions. [cite: 23, 216]

  * Data export capabilities (e.g., CSV, Excel). [cite: 23, 219]

  * Row grouping and aggregation. [cite: 23, 220]

* **Hybrid Scenario Display Toggle:**

  * Ability to switch between different scenario display modes (e.g., table vs. full property view). [cite: 284]

  * Smooth transitions, context preservation, and preference persistence. [cite: 286, 287]

#### 4.2. Scenario Lifecycle Management

* **Create New Scenario:**

  * A prominent "Create New Scenario" button/option. [cite: 133, 136]

  * A guided form or wizard for defining parameters (unique name, Reps, TimePeriod, etc.). [cite: 134, 138, 139, 140, 141]

  * Real-time validation and progress indication. [cite: 143, 144]

  * Summary before submission and success confirmation. [cite: 146, 148]

  * Newly created scenarios default to "NotReadyToRun" state. [cite: 135, 147]

  * Prevention of duplicate names within the same Analysis. [cite: 150]

* **Duplicate Existing Scenario:**

  * Easily accessible "Duplicate Scenario" option (via context menu, button, keyboard shortcut). [cite: 46, 49, 50, 51, 52]

  * Creates an exact copy with an automatically generated unique name (e.g., "Original Name - Copy"). [cite: 47, 53, 54]

  * The duplicated scenario is clearly marked and editable immediately. [cite: 55, 58]

  * Retains the same state as the original. [cite: 59]

* **Remove Scenario:**

  * Clear "Remove Scenario" option (via context menu, button, keyboard shortcut). [cite: 100, 101, 104, 105, 106, 107]

  * Implements a soft delete approach with a confirmation dialog. [cite: 101, 102, 108, 110]

  * Removed scenarios are hidden by default but viewable in a "Deleted Scenarios" section/filter. [cite: 111, 112]

  * Option to restore deleted scenarios. [cite: 102, 114]

  * Audit logging for removal/restoration. [cite: 116]

#### 4.3. Scenario Execution & Monitoring

* **Play Button Functionality:**

  * Visible "Play" button for each scenario. [cite: 76]

  * Enabled for scenarios in "ReadyToRun" state; clicking initiates the run. [cite: 77, 78]

  * Disabled for "IsRunning" or other non-runnable states (e.g., "NotReadyToRun," "RanWithErrors"). [cite: 79, 80, 86]

  * Tooltip explains why it's disabled if applicable. [cite: 81]

  * Real-time state updates and visual feedback on action. [cite: 82, 83]

* **Cancel Button Functionality:**

  * Visible "Cancel" button for each scenario. [cite: 234]

  * Enabled for scenarios in "IsRunning" state; clicking initiates cancellation. [cite: 235, 236]

  * Disabled for scenarios not currently running, with an explanatory tooltip. [cite: 237, 239]

  * Real-time state updates (e.g., to "Cancelling") and visual feedback. [cite: 240, 241, 242]

  * Confirmation dialog to prevent accidental cancellations. [cite: 244]

* **Real-time Updates:**

  * Scenario states, associated UI elements (buttons, status indicators), and progress indicators update in real-time without page reloads. [cite: 163, 164, 165]

  * Progress indicator for "IsRunning" state shows percentage completion (e.g., completed reps vs. total reps). [cite: 165, 166]

  * Smooth UI transitions and notification of connection issues. [cite: 168, 170]

* **State Management:**

  * Robust tracking of scenario states. [cite: 25]

  * Persistence of filters and view preferences. [cite: 25]

#### 4.4. Scenario Animation (New Feature)

* **User Story:** As a user, I want to launch an animation for a completed scenario to visually understand its dynamics and behavior over time.

* **Initiation:**

  * An "Animate" or "View Animation" button/icon will be available for each scenario.

  * This button will be enabled primarily for scenarios in the "RanSuccess" state, indicating that the simulation completed and has necessary output data for animation. (The system will need to check if animation data is available, perhaps from `scenarios.blob_storage_path` or a similar field indicating results).

* **View Handling:**

  * Upon clicking the "Animate" button, the animation view will launch.

  * To maximize the viewing experience, this will ideally open in:

    * A new, maximized browser tab or window.

    * A dedicated full-screen modal overlay within the Quodsi application.

  * This ensures the animation has ample screen real estate, free from the clutter of the main ScenarioManager interface.

* **Animation Player Features:**

  * The animation view itself will be a player with controls such as:

    * Play/Pause

    * Scrub/Timeline bar

    * Speed control (0.5x, 1x, 2x, etc.)

    * Zoom in/out and Pan (if the animation represents a 2D space)

    * Step forward/backward (by event or time increment)

    * Information display (current simulation time, key statistics overlay)

* **Data Source:**

  * The animation will be driven by simulation output data specific to the selected scenario. This data will likely be fetched from a location specified in the `scenarios` table (e.g., `blob_storage_path` which would point to detailed results, including event logs or state changes necessary for animation).

* **Accessibility:** The animation view should consider accessibility, potentially offering textual descriptions of key events for users who cannot rely on visual information.

#### 4.5. User Experience Enhancements

* **Toolbar Tooltips:**

  * Descriptive tooltips for all toolbar icons for clarity. [cite: 186, 187, 190]

  * Support for touch devices (e.g., tap-and-hold). [cite: 188]

  * Quick appearance, legible, and non-intrusive. [cite: 189, 191, 192]

* **Error Messages and Troubleshooting:**

  * Scenarios in "RanWithErrors" state are visually distinct. [cite: 262]

  * Concise error summary with access to detailed error information (full message, stack trace, specific step/component). [cite: 263, 264, 265, 266]

  * Actionable next steps, ability to copy error details, and links to documentation for common/complex errors. [cite: 267, 268, 270, 271]

* **Filter Scenarios by State:**

  * Clear method to filter scenarios by one or multiple States (e.g., Initial, ReadyToRun, IsRunning, RanSuccess, RanWithErrors). [cite: 175, 176]

  * Real-time update of the filtered view and clear indication of active filters. [cite: 177, 178]

  * Option to clear filters and persistence of filter settings. [cite: 179, 180]

### 5. Technology Stack Considerations

The frontend for the ScenarioManager will leverage:

* **JavaScript Framework/Library:** React [cite: 22]

* **Language:** TypeScript (preferred for type safety, though JavaScript is an option) [cite: 22]

* **CSS Framework/Utility:** Options like Bootstrap or Tailwind CSS. [cite: 22]

* **State Management:** A robust solution like MobX, Redux, Recoil, or XState to handle complex UI states and real-time data. [cite: 22]

### 6. Notes and Future Considerations

* The system assumes initialization with a list of Scenarios belonging to a parent Analysis. [cite: 15, 16]

* Performance will be a key consideration, especially with real-time updates and potentially large numbers of scenarios. [cite: 36, 70, 95, 126, 158, 172, 204, 228] Virtualization techniques for tables/lists should be explored. [cite: 42]

* Accessibility (ARIA attributes, keyboard navigation, screen reader compatibility) needs to be integrated into all components and features. [cite: 35, 37, 90, 173, 181, 184, 196, 198, 230, 248, 277, 291]

* Robust error handling is critical for all user actions and backend communications. [cite: 41, 68, 93, 251, 262]

* An audit trail or history for significant actions (creation, duplication, deletion, execution) is important. [cite: 65, 116, 258]

* The design should be extensible to accommodate future parameters, features, or integration points. [cite: 160]

* Consistency in UI/UX patterns with the broader Quodsi application is essential. [cite: 43, 96, 159, 194, 255, 273]

This document provides a comprehensive vision for the ScenarioManager, blending established UI/UX patterns with the specific needs of simulation scenario management, including the new scenario animation feature.