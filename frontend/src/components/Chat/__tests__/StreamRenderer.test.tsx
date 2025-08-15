import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import StreamRenderer, { StreamRendererProps } from '../StreamRenderer';

const setup = (props?: Partial<StreamRendererProps>) => {
  const defaults: StreamRendererProps = {
    content: '',
    isStreaming: false,
    onRetry: jest.fn(),
    onCancel: jest.fn(),
  };
  const all = { ...defaults, ...props } as StreamRendererProps;
  const utils = render(<StreamRenderer {...all} />);
  return { ...utils, props: all };
};

describe('StreamRenderer', () => {
  test('renders initial content and updates progressively', () => {
    const { rerender } = setup({ content: 'Hello' });
    expect(screen.getByTestId('stream-content')).toHaveTextContent('Hello');

    rerender(
      <StreamRenderer content={'Hello, wor'} isStreaming={true} onRetry={() => {}} onCancel={() => {}} />
    );
    expect(screen.getByTestId('stream-content')).toHaveTextContent('Hello, wor');

    rerender(
      <StreamRenderer content={'Hello, world!'} isStreaming={false} onRetry={() => {}} onCancel={() => {}} />
    );
    expect(screen.getByTestId('stream-content')).toHaveTextContent('Hello, world!');
  });

  test('shows streaming hint and enables Cancel when isStreaming is true', () => {
    setup({ content: 'Partial', isStreaming: true });
    expect(screen.getByText(/Streaming…/)).toBeInTheDocument();

    const cancelBtn = screen.getByRole('button', { name: /Cancel/i });
    expect(cancelBtn).toBeEnabled();
  });

  test('disables Cancel when not streaming', () => {
    setup({ content: 'Done', isStreaming: false });
    const cancelBtn = screen.getByRole('button', { name: /Cancel/i });
    expect(cancelBtn).toBeDisabled();
  });

  test('Retry and Cancel callbacks are invoked', () => {
    const onRetry = jest.fn();
    const onCancel = jest.fn();
    setup({ content: 'Hi', isStreaming: true, onRetry, onCancel });

    fireEvent.click(screen.getByRole('button', { name: /Retry/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: /Cancel/i }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
