# User Story 006: Backend Task API

**As a developer**, I need backend endpoints for task management **so that** the frontend can interact with task data.

## Description
This story covers the API endpoints required to support the task management feature.

## Acceptance Criteria
- The FastAPI application includes a new router for task-related endpoints.
- CRUD (Create, Read, Update, Delete) operations for tasks are exposed via `/api/tasks`.
- Endpoints are protected and can only be accessed by authenticated users.
- The API interacts with a database (e.g., Azure SQL) to persist task data.
- The database schema is managed using Alembic migrations.
