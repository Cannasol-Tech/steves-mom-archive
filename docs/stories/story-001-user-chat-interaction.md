# User Story 001: User Chat Interaction

**As a user**, I want a clean and intuitive chat interface **so that** I can easily communicate with the chatbot.

## Description
This story focuses on the frontend components required for the chat page, including the message input, message list, and overall layout.

## Acceptance Criteria
- The chat interface is built with React, TypeScript, and Tailwind CSS.
- The `ChatPage` is the main view, containing the `ChatInput` and `MessageList` components.
- Users can type messages in an auto-sizing textarea.
- Pressing Enter sends a message, while Shift+Enter creates a new line.
- Messages from the user and the assistant are clearly distinguished.
- Timestamps are displayed for each message.
- The UI correctly displays streaming responses from the assistant.
- The application has a theme provider for managing styles.
