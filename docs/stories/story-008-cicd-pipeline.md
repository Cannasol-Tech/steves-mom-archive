# User Story 008: CI/CD Pipeline

**As a developer**, I want our code to be automatically tested and deployed **so that** I can focus on writing features.

## Description
This story involves setting up GitHub Actions workflows to automate the build, test, and deployment process for both the frontend and backend applications.

## Acceptance Criteria
- A workflow is triggered on every push to the `main` and `develop` branches.
- The workflow runs linting and unit tests for both frontend and backend.
- On a push to `main`, the workflow deploys the frontend to the Azure Static Web App.
- On a push to `main`, the workflow deploys the backend functions to the Azure Function App.
- The pipeline uses secrets stored in GitHub for Azure credentials.
