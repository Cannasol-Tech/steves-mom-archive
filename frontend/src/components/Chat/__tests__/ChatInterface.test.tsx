import React from 'react';
import { render, screen } from '@testing-library/react';
import ChatInterface from '../ChatInterface';
import type { Message } from '../MessageList';

const mockProps = {
  messages: [] as Message[],
  isLoading: false,
  inputValue: '',
  model: 'grok-3-mini',
  onModelChange: jest.fn(),
  onChangeInput: jest.fn(),
  onSubmit: jest.fn(),
  onKeyDown: jest.fn(),
  onApproveTask: jest.fn(),
  onRejectTask: jest.fn(),
};

describe('ChatInterface', () => {
  it('renders the chat header with the correct title', () => {
    render(<ChatInterface {...mockProps} />);
    expect(screen.getByText(/Chat with Steve's Mom AI/i)).toBeInTheDocument();
  });

  it('renders the MessageList component', () => {
    render(<ChatInterface {...mockProps} />);
    // A simple way to check for MessageList is to look for its container or a unique element within it.
    // Assuming MessageList has a role or test-id would be better, but for now, we check for a known child.
    expect(screen.getByText(/Assistant is idle/i)).toBeInTheDocument(); // More specific check for the message list's status
  });

  it('renders the InputArea component', () => {
    render(<ChatInterface {...mockProps} />);
    expect(screen.getByPlaceholderText(/Ask anything…/i)).toBeInTheDocument();
  });

  it('displays a toast message when provided', () => {
    render(<ChatInterface {...mockProps} toastMessage="This is a test toast" />);
    expect(screen.getByText(/This is a test toast/i)).toBeInTheDocument();
  });

  it('shows a loading state in the input area when isLoading is true', () => {
    render(<ChatInterface {...mockProps} isLoading={true} inputValue="A message" />);
    expect(screen.getByText(/Sending…/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeDisabled();
  });
});
