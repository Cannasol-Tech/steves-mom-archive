# User Story 004: Contextual Task Interaction & Analytics

**As a developer/agent**, I want to manage AI-generated tasks in a contextual side panel within the chat interface **so that** I can provide immediate feedback, and I want a separate page to view historical performance data **so that** I can track the AI's long-term progress.

## Description
This story refines the task management workflow. Task interaction (approve, reject, modify) will now occur in a stylish, slide-out side panel accessible directly from the chat view. This keeps the feedback loop tight and contextual.

The dedicated `TasksPage` will be repurposed into a historical analytics dashboard, displaying performance metrics with visibility scopes to protect proprietary information.

## Acceptance Criteria

### Agent Tasks Side Panel (Chat View)
- A button or arrow (e.g., labeled "Agent Tasks") is present in the chat interface to toggle a side panel.
- The side panel slides out from the right, revealing tasks generated in the current conversation.
- Tasks are private to the user who initiated the session.
- From the panel, a developer can approve, reject, or modify a task, providing direct feedback.

### Task Analytics Page (Formerly TasksPage)
- The main `TasksPage`, accessible from navigation, is now an analytics dashboard.
- It displays historical performance metrics, such as the percentage of tasks accepted, modified, and rejected.
- Data can be aggregated to show overall trends (e.g., "Database Tasks Accepted: 42") without exposing sensitive task content.
- The page may offer personalized views of an individual's historical interactions.
- The page is responsive and accessible.

## Developer Notes
- **Frontend Scaffolding Complete (as of 2025-08-29):**
  - `TaskPage` has been refactored to `TaskAnalyticsPage`.
  - `AgentTasksPanel` component has been created and integrated into `ChatPage`.
  - Routing and tests have been updated to reflect these changes.
  - Backend implementation is pending.
