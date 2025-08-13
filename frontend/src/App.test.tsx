import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders main header title', () => {
  render(<App />);
  const titleElement = screen.getByRole('heading', { level: 1, name: /Steve's Mom AI/i });
  expect(titleElement).toBeInTheDocument();
});

test('renders chat page by default', () => {
  render(<App />);
  const chatElement = screen.getByText(/Chat with Steve's Mom AI/i);
  expect(chatElement).toBeInTheDocument();
});

test('renders navigation links', () => {
  render(<App />);
  const chatLinks = screen.getAllByRole('link', { name: /Chat/i });
  const inventoryLinks = screen.getAllByRole('link', { name: /Inventory/i });
  const adminLinks = screen.getAllByRole('link', { name: /Admin/i });

  // Should have at least one of each link (desktop and mobile versions)
  expect(chatLinks.length).toBeGreaterThan(0);
  expect(inventoryLinks.length).toBeGreaterThan(0);
  expect(adminLinks.length).toBeGreaterThan(0);
});

test('renders welcome message', () => {
  render(<App />);
  const welcomeMessage = screen.getByText(/Hello! I'm Steve's Mom AI assistant/i);
  expect(welcomeMessage).toBeInTheDocument();
});

test('renders chat input form', () => {
  render(<App />);
  const chatInput = screen.getByPlaceholderText(/Type your message here/i);
  const sendButton = screen.getByRole('button', { name: /Send/i });

  expect(chatInput).toBeInTheDocument();
  expect(sendButton).toBeInTheDocument();
  expect(sendButton).toBeDisabled(); // Should be disabled when input is empty
});
