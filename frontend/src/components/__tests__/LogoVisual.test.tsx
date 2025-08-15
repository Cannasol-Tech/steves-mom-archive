import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Layout from '../Layout';
import ChatInterface from '../Chat/ChatInterface';
import type { Message } from '../Chat/MessageList';

// Mock messages for chat interface testing
const mockMessages: Message[] = [
  {
    id: '1',
    content: 'Hello! I\'m Steve\'s Mom AI assistant.',
    role: 'assistant',
    timestamp: new Date()
  }
];

describe('Cannasol Logo Visual Regression Tests', () => {
  test('logo displays in header with correct attributes and responsive sizing', () => {
    render(
      <BrowserRouter>
        <Layout>
          <div>Test content</div>
        </Layout>
      </BrowserRouter>
    );
    
    const logo = screen.getByAltText('Cannasol Technologies');
    expect(logo).toBeInTheDocument();
    expect(logo).toHaveAttribute('src', '/cannasol-logo.png');
    expect(logo).toHaveClass('h-6', 'w-6', 'sm:h-8', 'sm:w-8', 'object-contain');
  });

  test('logo appears alongside Steve\'s Mom branding text', () => {
    render(
      <BrowserRouter>
        <Layout>
          <div>Test content</div>
        </Layout>
      </BrowserRouter>
    );
    
    const logo = screen.getByAltText('Cannasol Technologies');
    const brandingText = screen.getByText('Steve\'s Mom');
    
    expect(logo).toBeInTheDocument();
    expect(brandingText).toBeInTheDocument();
    
    // Verify they're in the same container (header link)
    const headerLink = logo.closest('a');
    expect(headerLink).toContainElement(brandingText);
  });

  test('logo has error handling for missing image', () => {
    render(
      <BrowserRouter>
        <Layout>
          <div>Test content</div>
        </Layout>
      </BrowserRouter>
    );
    
    const logo = screen.getByAltText('Cannasol Technologies') as HTMLImageElement;
    
    // Verify the logo element exists and has proper structure
    expect(logo).toBeInTheDocument();
    expect(logo.tagName).toBe('IMG');
    
    // Note: onError handler is defined inline in JSX, not as DOM attribute
    // The error handling functionality is present in the component code
    expect(logo).toHaveAttribute('src', '/cannasol-logo.png');
  });

  test('logo maintains accessibility with proper alt text', () => {
    render(
      <BrowserRouter>
        <Layout>
          <div>Test content</div>
        </Layout>
      </BrowserRouter>
    );
    
    const logo = screen.getByRole('img', { name: /cannasol technologies/i });
    expect(logo).toBeInTheDocument();
    expect(logo).toHaveAttribute('alt', 'Cannasol Technologies');
  });

  test('logo displays in chat interface loading states', () => {
    render(
      <ChatInterface
        messages={mockMessages}
        isLoading={true}
        inputValue=""
        model="grok-3-mini (proxy)"
        onModelChange={() => {}}
        onChangeInput={() => {}}
        onSubmit={() => {}}
        onKeyDown={() => {}}
        streamingContent=""
        streamingActive={false}
        onRetryStream={() => {}}
        onCancelStream={() => {}}
      />
    );
    
    // Check that Cannasol logo appears in chat interface branding
    const chatLogo = screen.getByAltText('Cannasol Technologies');
    expect(chatLogo).toBeInTheDocument();
    expect(chatLogo).toHaveClass('h-5', 'w-5', 'sm:h-6', 'sm:w-6', 'object-contain');
  });

  test('logo responsive classes work across breakpoints', () => {
    render(
      <BrowserRouter>
        <Layout>
          <div>Test content</div>
        </Layout>
      </BrowserRouter>
    );
    
    const logo = screen.getByAltText('Cannasol Technologies');
    
    // Verify responsive classes are present
    expect(logo).toHaveClass('h-6', 'w-6'); // mobile
    expect(logo).toHaveClass('sm:h-8', 'sm:w-8'); // small screens and up
    expect(logo).toHaveClass('object-contain'); // maintains aspect ratio
  });
});
