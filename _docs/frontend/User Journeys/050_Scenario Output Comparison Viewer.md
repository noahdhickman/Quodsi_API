## Scenario Output Comparison Viewer: Vision & Features

### 1. Introduction and Purpose

The **Scenario Output Comparison Viewer** is a critical component of the Quodsi platform, designed to empower users to analyze and contrast the results from multiple simulation scenarios within a chosen Analysis. After running various scenarios with different parameters, users need a dedicated tool to easily compare key performance indicators (KPIs), throughput, resource utilization, time-series data, and other output metrics. This feature is essential for understanding the impact of changes, identifying optimal configurations, and making data-driven decisions.

### 2. Accessing the Comparison Viewer

The Scenario Output Comparison Viewer would typically be accessed from the **ScenarioManager** interface:

1.  **Navigate to an Analysis:** The user first selects a Model, then navigates to a specific Analysis, which displays a list of its associated scenarios. \[cite: 16, 18]
2.  **Select Scenarios:** Within the ScenarioManager's scenario list, the user selects two or more scenarios they wish to compare.
    * This selection would likely use checkboxes next to each scenario, a common feature in advanced table/datagrid interfaces. \[cite: 215]
    * Typically, only scenarios in a "RanSuccess" state \[cite: 1396] (or possibly "RanWithErrors" if partial results are to be compared) would be eligible for comparison, as they are expected to have generated output data.
3.  **Initiate Comparison:** Once multiple compatible scenarios are selected, a "Compare Outputs," "Analyze Results," or similar button in the ScenarioManager's toolbar or action panel becomes enabled. Clicking this button launches the Scenario Output Comparison Viewer.

### 3. Core Components & Layout of the Comparison Viewer

The Comparison Viewer would be a dedicated interface, possibly opening in a new maximized view, tab, or a large modal to provide ample space for data visualization.

* **A. Scenario Selection Pane:**
    * Displays the list of scenarios currently included in the comparison.
    * Allows the user to easily add or remove scenarios from the comparison set dynamically.
    * Shows key identifying information for each selected scenario (e.g., `scenarios.name`\[cite: 17], key overridden parameters from `scenario_item_profiles`).
* **B. Output Category & Metric Selection:**
    * **Output Category Selector:** A primary navigation element (e.g., tabs, sidebar, dropdown menu) allowing users to choose the general type of output they want to compare. Examples:
        * Entity Throughput (e.g., parts per hour, customers served)
        * Resource Utilization (e.g., machines, staff, beds)
        * Cycle Times / Lead Times
        * Work-In-Progress (WIP) Levels
        * Cost Analysis
        * Custom KPIs (if defined by the user or model)
        * Time Series Data
    * **Metric/Item Selector:** Once an output category is chosen, a secondary selector allows users to pick specific items or metrics within that category.
        * For "Resource Utilization": A multi-select list of available resources (from the parent model's `resources` table).
        * For "Time Series Data": A list of available time-dependent variables.
        * For "Entity Throughput": A list of entity types (from `entities` table).
    * **Statistic Selector (for aggregated values):** For metrics that are aggregated over the simulation run (like utilization or total throughput), users might select the statistic to compare (e.g., Average, Minimum, Maximum, Sum, 95th Percentile).
* **C. Comparison Display Area:**
    * The main section where the selected data for the chosen scenarios is visualized. The type of visualization will adapt to the data:
        * **Tabular Comparison:** For scalar KPIs, aggregated metrics, or end-of-run statistics. Scenarios would typically be columns, and metrics/items would be rows (or vice-versa). This allows for direct numerical comparison.
        * **Chart Comparison:**
            * **Time Series Charts:** For time-dependent data (e.g., WIP over time, queue length over time), overlaid line charts are ideal, with each scenario represented by a distinct color or line style.
            * **Bar Charts/Column Charts:** Useful for comparing discrete values across scenarios (e.g., total output of different entity types, average utilization of different resources).
            * **Distribution Plots (Histograms/Box Plots):** For comparing the distribution of certain metrics (e.g., entity cycle times) across scenarios.
        * **Statistical Summary Table:** Could display key statistical differences, confidence intervals (if replications `reps` > 1 \[cite: 17]), or even significance testing results between scenarios.
* **D. Controls & Customization:**
    * **Chart Controls:** Options to customize charts, such as:
        * Time range selection/zooming for time series.
        * Toggling visibility of specific scenarios or data series.
        * Data point markers, legends.
        * Option to view raw data.
    * **Export Options:** Ability to export the current comparison view (tables to CSV/Excel, charts to PNG/SVG/PDF). \[cite: 218]
    * **Layout/View Presets:** Option to save and load common comparison configurations.
    * **Link to Scenario Parameters:** Easy way to view the parameter differences (from `scenario_item_profiles` \[cite: 20]) between the compared scenarios to understand the drivers of output variation.

### 4. Data Handling and Source

* **Data Retrieval:** The Comparison Viewer will need to fetch detailed simulation output data. This data is expected to be stored in a structured format (e.g., JSON, CSV, Parquet) in a location specified by the `scenarios.blob_storage_path` field \[cite: 1428] for each scenario.
* **Data Processing:**
    * The viewer must be capable of parsing these output files.
    * If scenarios were run with multiple replications (`scenarios.reps` > 1 \[cite: 17, 1390]), the viewer should allow comparison of individual replications or, more commonly, display aggregated statistics (mean, median, confidence intervals) across replications for each scenario.
* **Data Schema:** While the exact schema of the output files in blob storage is not defined here, the system will need a standardized way to structure these results for the viewer to consume them effectively.

### 5. Example User Interaction Flow:

1.  User is in the ScenarioManager, viewing scenarios for "Analysis X."
2.  User checkboxes three scenarios: "Baseline," "New Robot Arm," and "Increased Staff." All are in "RanSuccess" state.
3.  The "Compare Outputs" button becomes active; the user clicks it.
4.  The Scenario Output Comparison Viewer opens, showing these three scenarios in the selection pane.
5.  By default, it might show a summary KPI dashboard or prompt for category selection.
6.  User selects the "Resource Utilization" category.
7.  User multi-selects "Assembly Robot 1" and "Packing Station Operator" from the item selector.
8.  User chooses "Average Utilization (%)" and "Total Idle Time (hours)" as metrics.
9.  The display area shows a table:

    | Metric                  | Baseline | New Robot Arm | Increased Staff |
    | ----------------------- | -------- | ------------- | --------------- |
    | Avg. Util. Assembly R1  | 75%      | 92%           | 78%             |
    | Idle Time Assembly R1   | 2.0 hrs  | 0.5 hrs       | 1.8 hrs         |
    | Avg. Util. Packer Op    | 95%      | 96%           | 65%             |
    | Idle Time Packer Op     | 0.2 hrs  | 0.15 hrs      | 3.5 hrs         |

10. User then selects the "Time Series Data" category and "Queue Length for Assembly Robot 1" as the metric.
11. An overlaid line chart appears, showing queue length over simulated time for the three selected scenarios.

### 6. Key Benefits

* **Insight Generation:** Directly compare the impact of different parameters or configurations.
* **Decision Support:** Helps in selecting the best-performing or most robust scenario.
* **Bottleneck Analysis:** Easily identify how changes affect constraints and flow.
* **Clear Communication:** Exportable visuals and data for reports and presentations.

This Scenario Output Comparison Viewer would significantly enhance the analytical power of Quodsi, transforming raw simulation output into actionable insights.