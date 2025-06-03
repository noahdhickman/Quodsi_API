# Quodsi Frontend: Models, Analysis & Scenario Management System

## Overview

This document outlines the hierarchical navigation system for the Quodsi frontend, following the Model → Analysis → Scenario workflow. The system assumes users have completed authentication via the Fake Authentication Approach and are viewing their personalized dashboard.

## Navigation Hierarchy

```
Dashboard → Model Manager → Analysis Manager → Scenario Manager
    ↓           ↓              ↓                ↓
Home Page   Models List    Analyses List    Scenarios List
```

Each level provides drill-down capability to the next level while maintaining breadcrumb navigation back to previous levels.

---

## 1. Model Manager

### Purpose
The Model Manager serves as the primary hub for users to view, manage, and navigate to all simulation models they have access to within their tenant.

### Layout & Design

#### Card-Based Layout
- **Layout**: Vertical stack of model cards
- **Card Width**: Full horizontal width (responsive design)
- **Spacing**: Consistent vertical spacing between cards
- **Component**: `ModelCard.tsx` (standalone, reusable component)

#### Model Card Component Structure

```typescript
// components/models/ModelCard.tsx
interface ModelCardProps {
  model: Model;
  onSelect: (modelId: string) => void;
  onEdit: (modelId: string) => void;
  onDelete: (modelId: string) => void;
  onDuplicate: (modelId: string) => void;
  onNavigateToAnalyses: (modelId: string) => void;
}
```

#### Card Content Layout

```
┌─────────────────────────────────────────────────────────────┐
│ [Source Icon] Model Name                          [Actions ⋮] │
│ Description text that can span multiple lines...              │
│                                                               │
│ Created: Date | Updated: Date | Source: LucidChart/Miro/etc  │
│                                                               │
│ [View Analyses] [Edit] [Duplicate] [Delete]                   │
└─────────────────────────────────────────────────────────────┘
```

#### Model Card Features

**Essential Information Display:**
- **Model Name**: Primary title with source indicator icon
- **Description**: Multi-line text with truncation/expand capability
- **Metadata**: Created date, last updated, source type
- **Status Indicators**: Visual indicators for model state
- **Analysis Count**: Number of associated analyses

**Action Buttons:**
- **View Analyses** (Primary): Navigate to Analysis Manager
- **Edit**: Modify model properties
- **Duplicate**: Create a copy of the model
- **Delete**: Soft delete with confirmation
- **Context Menu**: Additional actions (share, export, etc.)

**Source Integration:**
- **Source Icons**: Visual indicators for LucidChart, Miro, Standalone
- **Source Badge**: Color-coded badges showing model origin
- **Import Status**: If applicable, show sync status with external sources

### Data Integration

**API Endpoints Used:**
- `GET /api/models/` - Fetch user's accessible models
- `POST /api/models/` - Create new model
- `PUT /api/models/{id}` - Update model
- `DELETE /api/models/{id}` - Soft delete model
- `POST /api/models/{id}/duplicate` - Duplicate model

**Model Data Structure:**
```typescript
interface Model {
  id: string;
  name: string;
  description: string;
  source: 'lucidchart' | 'miro' | 'standalone';
  created_at: string;
  updated_at: string;
  created_by_user_id: string;
  tenant_id: string;
  is_public: boolean;
  analysis_count?: number; // Computed field
  status: 'active' | 'archived' | 'draft';
}
```

### User Interactions

**Primary Navigation:**
- Click "View Analyses" → Navigate to Analysis Manager for selected model
- Click model name → Same as "View Analyses"

**CRUD Operations:**
- **Create**: "New Model" button at top of page
- **Read**: Display model cards with all essential information
- **Update**: Edit button opens model properties form
- **Delete**: Confirmation dialog, then soft delete

**Filtering & Sorting:**
- **Filter by Source**: LucidChart, Miro, Standalone, All
- **Filter by Status**: Active, Archived, Draft
- **Sort Options**: Name (A-Z), Created Date, Updated Date
- **Search**: Real-time search by model name/description

---

## 2. Analysis Manager

### Purpose
Display and manage all analyses within a selected model, providing drill-down access to scenarios while maintaining model context.

### Navigation Context
- **Breadcrumb**: Dashboard > Models > [Model Name] > Analyses
- **Model Context Bar**: Show current model name and key details
- **Back Navigation**: Easy return to Model Manager

### Layout & Design

#### Analysis Card Component

```typescript
// components/analyses/AnalysisCard.tsx
interface AnalysisCardProps {
  analysis: Analysis;
  onSelect: (analysisId: string) => void;
  onEdit: (analysisId: string) => void;
  onDelete: (analysisId: string) => void;
  onDuplicate: (analysisId: string) => void;
  onNavigateToScenarios: (analysisId: string) => void;
}
```

#### Card Content Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Analysis Name                                   [Actions ⋮]  │
│ Description text...                                          │
│                                                              │
│ Default Reps: 5 | Time Period: Daily | Scenarios: 12        │
│ Created: Date | Last Run: Date                               │
│                                                              │
│ [Manage Scenarios] [Edit] [Duplicate] [Delete]              │
└─────────────────────────────────────────────────────────────┘
```

#### Analysis-Specific Features

**Analysis Metadata:**
- **Default Parameters**: Default reps, time period settings
- **Scenario Count**: Number of scenarios in this analysis
- **Latest Activity**: Last scenario run date/time
- **Status Summary**: Overview of scenario states (running, completed, errors)

**Quick Actions:**
- **Manage Scenarios** (Primary): Navigate to Scenario Manager
- **Run All Scenarios**: Bulk execution option
- **Export Results**: Download analysis summary

### Data Integration

**API Endpoints:**
- `GET /api/models/{modelId}/analyses/` - Fetch analyses for model
- `POST /api/models/{modelId}/analyses/` - Create new analysis
- `PUT /api/analyses/{id}` - Update analysis
- `DELETE /api/analyses/{id}` - Soft delete analysis

**Analysis Data Structure:**
```typescript
interface Analysis {
  id: string;
  name: string;
  description: string;
  model_id: string;
  default_reps: number;
  default_time_period: 'hourly' | 'daily' | 'monthly';
  created_at: string;
  updated_at: string;
  scenario_count?: number;
  last_run_at?: string;
  scenarios_summary?: {
    total: number;
    running: number;
    completed: number;
    errors: number;
  };
}
```

---

## 3. Scenario Manager

### Purpose
The most critical interface in the application, providing comprehensive scenario management, execution, and results viewing capabilities.

### Navigation Context
- **Breadcrumb**: Dashboard > Models > [Model Name] > Analyses > [Analysis Name] > Scenarios
- **Analysis Context Bar**: Show current analysis name and parameters
- **Quick Navigation**: Jump back to any level in hierarchy

### Enhanced Card Layout

Given that Scenario Manager is the most heavily used interface, the cards require more sophisticated functionality:

#### Scenario Card Component

```typescript
// components/scenarios/ScenarioCard.tsx
interface ScenarioCardProps {
  scenario: Scenario;
  onRun: (scenarioId: string) => void;
  onCancel: (scenarioId: string) => void;
  onViewResults: (scenarioId: string) => void;
  onAnimate: (scenarioId: string, repNumber?: number) => void;
  onEdit: (scenarioId: string) => void;
  onDuplicate: (scenarioId: string) => void;
  onDelete: (scenarioId: string) => void;
}
```

#### Enhanced Card Layout

```
┌─────────────────────────────────────────────────────────────┐
│ [Status Indicator] Scenario Name               [Actions ⋮]   │
│ Description...                                               │
│                                                              │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │ Reps: 10        │ │ Time: Daily     │ │ Progress: 70%   │ │
│ │ Status: Running │ │ Duration: 2.5h  │ │ ETA: 45min      │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│                                                              │
│ [▶ Run] [⏹ Cancel] [📊 Results] [🎬 Animate] [Edit] [⋯ More] │
└─────────────────────────────────────────────────────────────┘
```

### Scenario States & Visual Indicators

**State Management:**
```typescript
type ScenarioState = 
  | 'NotReadyToRun'
  | 'ReadyToRun' 
  | 'IsRunning'
  | 'RanSuccess'
  | 'RanWithErrors'
  | 'Cancelling';
```

**Visual Indicators:**
- **NotReadyToRun**: Gray indicator, disabled run button
- **ReadyToRun**: Green indicator, enabled run button
- **IsRunning**: Blue indicator with progress animation
- **RanSuccess**: Green checkmark, results available
- **RanWithErrors**: Yellow warning, partial results
- **Cancelling**: Orange indicator with cancel animation

### Core Scenario Actions

#### 1. Run Scenario
- **Button State**: Enabled only for "ReadyToRun" scenarios
- **Action**: Execute simulation with defined parameters
- **Feedback**: Real-time progress updates, state transitions
- **Error Handling**: Display errors with actionable guidance

#### 2. Cancel Scenario
- **Button State**: Enabled only for "IsRunning" scenarios
- **Confirmation**: Prevent accidental cancellations
- **Action**: Graceful termination of running simulation
- **State Update**: Transition to "Cancelling" then final state

#### 3. View Results
- **Availability**: Enabled for "RanSuccess" and "RanWithErrors"
- **Action**: Navigate to results dashboard/viewer
- **Data Source**: Fetch from `blob_storage_path`
- **Visualization**: Charts, tables, KPI summaries

#### 4. Animate Scenario (Key Feature)
- **Availability**: Enabled for scenarios with completed simulation data
- **Rep Selection**: Choose specific replication to animate
- **Target**: Open new browser tab with 2D animation player
- **Player Features**:
  - Play/Pause controls
  - Timeline scrubbing
  - Speed adjustment (0.5x, 1x, 2x, 4x)
  - Zoom and pan capabilities
  - Event highlighting
  - Statistics overlay

```typescript
// Animation launch function
const handleAnimateScenario = (scenarioId: string, repNumber: number = 1) => {
  const animationUrl = `/animation/${scenarioId}/rep/${repNumber}`;
  window.open(animationUrl, '_blank', 'width=1200,height=800');
};
```

### Advanced Scenario Manager Features

#### Bulk Operations
- **Multi-Select**: Checkbox selection for multiple scenarios
- **Bulk Actions**: Run selected, delete selected, export selected
- **Progress Monitoring**: Track multiple running scenarios

#### Filtering & Sorting
- **Filter by State**: Show only scenarios in specific states
- **Filter by Results**: Show only successful/failed scenarios
- **Sort Options**: Name, creation date, last run, duration
- **Search**: Real-time search across scenario names and descriptions

#### Real-Time Updates
- **WebSocket Integration**: Live updates for scenario states
- **Progress Indicators**: Real-time progress bars for running scenarios
- **Notifications**: Browser notifications for completion events
- **Auto-Refresh**: Periodic updates for state synchronization

### Data Integration

**API Endpoints:**
- `GET /api/analyses/{analysisId}/scenarios/` - Fetch scenarios
- `POST /api/analyses/{analysisId}/scenarios/` - Create scenario
- `PUT /api/scenarios/{id}` - Update scenario
- `DELETE /api/scenarios/{id}` - Soft delete
- `POST /api/scenarios/{id}/run` - Execute scenario
- `POST /api/scenarios/{id}/cancel` - Cancel execution
- `GET /api/scenarios/{id}/results` - Fetch results
- `GET /api/scenarios/{id}/animation-data/{rep}` - Animation data

**Scenario Data Structure:**
```typescript
interface Scenario {
  id: string;
  name: string;
  description: string;
  analysis_id: string;
  reps: number;
  time_period: 'hourly' | 'daily' | 'monthly';
  state: ScenarioState;
  progress_percentage?: number;
  estimated_completion?: string;
  started_at?: string;
  completed_at?: string;
  duration_minutes?: number;
  blob_storage_path?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}
```

---

## 4. Cross-Cutting Concerns

### Responsive Design
- **Mobile-First**: Cards stack properly on mobile devices
- **Tablet Layout**: Optimized spacing and touch targets
- **Desktop**: Full-width cards with hover effects

### Performance Optimization
- **Lazy Loading**: Load cards as user scrolls
- **Virtual Scrolling**: Handle large lists efficiently
- **Caching**: Cache frequently accessed data
- **Optimistic Updates**: Immediate UI feedback for user actions

### Error Handling
- **Network Errors**: Graceful handling of API failures
- **Validation Errors**: Clear form validation messages
- **State Errors**: Recovery from inconsistent states
- **User Guidance**: Actionable error messages with next steps

### Accessibility
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Readers**: Proper ARIA labels and descriptions
- **Color Contrast**: WCAG-compliant color schemes
- **Focus Management**: Clear focus indicators

### State Management
- **Global State**: User context, selected items, filters
- **Local State**: Card interactions, form data, UI state
- **Persistence**: Remember user preferences and view states
- **Synchronization**: Keep data consistent across components

---

## 5. Implementation Roadmap

### Phase 1: Foundation
1. Set up routing structure (React Router)
2. Create base card components with mock data
3. Implement navigation hierarchy
4. Add basic CRUD operations

### Phase 2: Core Functionality
1. Integrate with existing API endpoints
2. Add real-time scenario state updates
3. Implement run/cancel scenario functionality
4. Create results viewing capability

### Phase 3: Advanced Features
1. Build 2D animation player in new tab
2. Add bulk operations and filtering
3. Implement WebSocket for live updates
4. Add comprehensive error handling

### Phase 4: Polish & Optimization
1. Performance optimization and caching
2. Mobile responsiveness refinement
3. Accessibility improvements
4. User experience enhancements

This detailed design provides a robust foundation for the hierarchical navigation system while maintaining flexibility for future iterations and improvements.