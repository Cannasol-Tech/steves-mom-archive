import React from 'react';
import { render, screen } from '@testing-library/react';

// Use MemoryRouter instead of BrowserRouter inside App during tests
jest.mock('react-router-dom', () => {
  const actual = jest.requireActual('react-router-dom');
  return {
    ...actual,
    BrowserRouter: actual.MemoryRouter,
  };
});

import App from './App';

// Prevent real WS connections during tests
class MockWebSocket {
  onopen: ((this: WebSocket, ev: Event) => any) | null = null;
  onclose: ((this: WebSocket, ev: CloseEvent) => any) | null = null;
  onmessage: ((this: WebSocket, ev: MessageEvent) => any) | null = null;
  onerror: ((this: WebSocket, ev: Event) => any) | null = null;
  readyState = 1;
  send() {}
  close() {
    this.readyState = 3;
  }
}

// @ts-ignore
global.WebSocket = MockWebSocket as any;

// Silence React Router v6 deprecation/future warnings for this suite only
let consoleWarnSpy: jest.SpyInstance;
beforeAll(() => {
  consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation((msg?: any, ...args: any[]) => {
    const text = String(msg || '');
    if (
      text.includes('Future Flag Warning') ||
      text.includes('is deprecated') ||
      text.includes('Future flags are deprecated') ||
      text.includes('Relative route resolution within Splat routes')
    ) {
      return;
    }
  });
});

afterAll(() => {
  consoleWarnSpy.mockRestore();
});

test("renders main header title text", async () => {
  render(<App />);
  const titleTexts = await screen.findAllByText(/Steve's Mom/i);
  expect(titleTexts.length).toBeGreaterThan(0);
});

test('renders chat page by default', async () => {
  render(<App />);
  const chatElement = await screen.findByText(/Chat with Steve's Mom AI/i);
  expect(chatElement).toBeInTheDocument();
});

test('renders navigation links', async () => {
  render(<App />);
  const chatLinks = await screen.findAllByRole('link', { name: /Chat/i });
  const adminLinks = await screen.findAllByRole('link', { name: /Admin/i });

  // Should have at least one of each link (desktop and mobile versions)
  expect(chatLinks.length).toBeGreaterThan(0);
  expect(adminLinks.length).toBeGreaterThan(0);
});

test('renders welcome message', async () => {
  render(<App />);
  const welcomeMessage = await screen.findByText(/Hello! I'm Steve's Mom AI assistant/i);
  expect(welcomeMessage).toBeInTheDocument();
});

test('renders chat input form', async () => {
  render(<App />);
  const chatInput = await screen.findByPlaceholderText(/Ask anything/i);
  const sendButton = await screen.findByRole('button', { name: /Send/i });

  expect(chatInput).toBeInTheDocument();
  expect(sendButton).toBeInTheDocument();
  expect(sendButton).toBeDisabled(); // Should be disabled when input is empty
});
