# ADR 001: MVP Architecture Overview

**Status**: Proposed

**Context**:
Based on the Product Requirements Document (PRD), the Steve's Mom AI Chatbot MVP requires a full-stack application with a real-time chat interface, task management, and an admin dashboard. The system must be scalable, maintainable, and deployed on Azure with a high degree of automation.

**Decision**:
We will adopt a modern, decoupled architecture composed of three main pillars:

1.  **Frontend**: A single-page application (SPA) built with **React** and **TypeScript**. This provides a rich, interactive user experience. **Tailwind CSS** will be used for styling to ensure rapid and consistent UI development. State management will be handled via React's Context API for simplicity in the MVP.

2.  **Backend**: A **FastAPI** (Python) application will serve as the backend API. Its asynchronous nature is well-suited for I/O-bound operations like handling chat requests and database interactions. A **WebSocket** endpoint will be used for real-time communication with the frontend, enabling streaming responses from the AI. The backend will be deployed as an **Azure Function App** for serverless scalability and cost-efficiency.

3.  **Infrastructure**: All cloud resources will be managed using **Infrastructure as Code (IaC)** with **Azure Bicep**. This ensures repeatability and version control of our environment. The frontend will be hosted on **Azure Static Web Apps**, which provides seamless integration with GitHub for CI/CD, global distribution, and authentication. Data will be stored in **Azure SQL**, with **Azure Cache for Redis** used for session management or caching where needed. **Azure Key Vault** will securely store all secrets and credentials.

**Consequences**:
- **Positive**:
    - The decoupled nature allows frontend and backend teams to work independently.
    - The chosen technologies (React, FastAPI, Bicep) are popular, well-documented, and have strong community support.
    - The serverless backend and static web app hosting model are cost-effective and scale automatically.
    - The CI/CD pipeline ensures a high degree of automation and reliability.
- **Negative**:
    - The learning curve for team members unfamiliar with Bicep or FastAPI could introduce minor delays.
    - The complexity of managing a full-stack, multi-service application requires careful coordination.
