import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import InputArea from '../InputArea';

function setup(initialValue = '') {
  const onChange = jest.fn();
  const onSubmit = jest.fn();
  const utils = render(
    <InputArea
      value={initialValue}
      onChange={onChange}
      onSubmit={onSubmit}
      disabled={false}
      loading={false}
    />
  );
  const textarea = screen.getByPlaceholderText(/Ask anything…/i) as HTMLTextAreaElement;
  const button = screen.getByRole('button', { name: /send/i });
  return { textarea, button, onChange, onSubmit, utils };
}

describe('InputArea', () => {
  test('disables send when value is empty', () => {
    const { button } = setup('');
    expect(button).toBeDisabled();
  });

  test('enables send when value has non-whitespace', async () => {
    const { textarea, onChange, utils } = setup('');
    await userEvent.type(textarea, 'Hello');
    expect(onChange).toHaveBeenCalled();
    // Re-render with controlled value to reflect enabled state
    utils.rerender(
      <InputArea value={'Hello'} onChange={onChange} onSubmit={jest.fn()} disabled={false} loading={false} />
    );
    expect(screen.getByRole('button', { name: /send/i })).toBeEnabled();
  });

  test('shows over-limit state and disables send', () => {
    const longText = 'a'.repeat(2001);
    const { textarea, onChange, utils } = setup('');
    fireEvent.change(textarea, { target: { value: longText } });
    expect(onChange).toHaveBeenCalled();
    // Re-render with controlled value to reflect over-limit UI using same root
    const onChange2 = jest.fn();
    const onSubmit2 = jest.fn();
    utils.rerender(
      <InputArea value={longText} onChange={onChange2} onSubmit={onSubmit2} disabled={false} loading={false} />
    );
    const ta = screen.getByPlaceholderText(/Ask anything…/i);
    expect(ta).toHaveAttribute('aria-invalid', 'true');
    const help = screen.getByText(/Too long by/i);
    expect(help).toBeInTheDocument();
    const send = screen.getByRole('button', { name: /send/i });
    expect(send).toBeDisabled();
  });

  test('autosizes textarea height on input (basic smoke)', () => {
    // Mock scrollHeight so autosize logic has a value
    Object.defineProperty(HTMLElement.prototype, 'scrollHeight', {
      configurable: true,
      get() {
        return 200; // px
      }
    });
    const { textarea } = setup('Hello');
    // After initial render, autosize effect should set height
    expect((textarea as HTMLTextAreaElement).style.height).not.toBe('');
  });

  test('clicking Send triggers onSubmit when under limit', async () => {
    const onChange = jest.fn();
    const onSubmit = jest.fn();
    const { rerender } = render(
      <InputArea value={''} onChange={onChange} onSubmit={onSubmit} disabled={false} loading={false} />
    );
    // Controlled update to a valid value so button is enabled
    rerender(<InputArea value={'Hi'} onChange={onChange} onSubmit={onSubmit} disabled={false} loading={false} />);
    const send = screen.getByRole('button', { name: /send/i });
    await userEvent.click(send);
    expect(onSubmit).toHaveBeenCalled();
  });

  test('provides keyboard hint via aria-describedby and sr-only content', () => {
    render(<InputArea value={''} onChange={jest.fn()} onSubmit={jest.fn()} disabled={false} loading={false} />);
    const textarea = screen.getByPlaceholderText(/Ask anything…/i);
    expect(textarea).toHaveAttribute('aria-describedby', 'chat-input-hint');
    const srHint = screen.getByText(/Press Command or Control and Enter to send/i);
    expect(srHint).toBeInTheDocument();
  });

  test('shows loading state: button aria-busy and disabled', () => {
    render(<InputArea value={'Hello'} onChange={jest.fn()} onSubmit={jest.fn()} disabled={false} loading={true} />);
    const send = screen.getByRole('button', { name: /send/i });
    expect(send).toHaveAttribute('aria-busy', 'true');
    expect(send).toBeDisabled();
    // Spinner or Sending… label visible
    expect(screen.getByText(/Sending…/i)).toBeInTheDocument();
  });
});
