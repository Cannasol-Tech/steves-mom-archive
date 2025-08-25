import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '../../context/ThemeContext';
import ThemeToggle from '../ThemeToggle';

function setup() {
  return render(
    <ThemeProvider>
      <ThemeToggle />
    </ThemeProvider>
  );
}

describe('ThemeToggle', () => {
  const originalMatchMedia = window.matchMedia;

  afterEach(() => {
    // cleanup matchMedia mock
    window.matchMedia = originalMatchMedia;
    localStorage.clear();
    document.documentElement.classList.remove('light', 'dark');
  });

  test('honors localStorage theme on load', () => {
    localStorage.setItem('theme', 'dark');
    setup();
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  test('falls back to system preference when no localStorage', () => {
    // mock prefers-color-scheme: dark
    // @ts-ignore
    window.matchMedia = jest.fn().mockImplementation((query: string) => ({
      matches: query.includes('prefers-color-scheme: dark'),
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }));

    setup();
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  test('toggle switches theme and persists to localStorage', () => {
    localStorage.setItem('theme', 'light');
    setup();

    const btn = screen.getByRole('button', { name: /toggle theme/i });
    expect(document.documentElement.classList.contains('light')).toBe(true);

    fireEvent.click(btn);
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(localStorage.getItem('theme')).toBe('dark');

    fireEvent.click(btn);
    expect(document.documentElement.classList.contains('light')).toBe(true);
    expect(localStorage.getItem('theme')).toBe('light');
  });
});
