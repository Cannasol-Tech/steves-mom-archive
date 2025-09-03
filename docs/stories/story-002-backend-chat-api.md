# User Story 002: Backend Chat API

**As a developer**, I need a robust backend API **so that** the frontend can securely communicate with the AI model.

## Description
This story covers the creation of the FastAPI backend, including the chat endpoint, WebSocket for real-time updates, and integration with the AI provider.

## Acceptance Criteria
- A FastAPI application is created with CORS configured.
- A `/api/chat` endpoint accepts POST requests with a `ChatRequest` payload.
- The endpoint interacts with the `GROKProvider` to get a response from the AI model.
- The API returns a `ChatResponse` with the assistant's message.
- A `/ws` WebSocket endpoint is available for real-time communication.
- The backend can parse and broadcast animation directives found in the AI's response.
- A `/health` endpoint returns a 200 OK status.
