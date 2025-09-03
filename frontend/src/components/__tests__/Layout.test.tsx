import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import Layout from '../Layout';
import { ThemeProvider } from '../../context/ThemeContext';

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

function renderWithRoute(pathname: string, ui: React.ReactNode) {
  return render(
    <MemoryRouter initialEntries={[pathname]}>
      <ThemeProvider>
        {ui}
      </ThemeProvider>
    </MemoryRouter>
  );
}

describe('Layout', () => {
  test('highlights Chat link as active on / and /chat', () => {
    const { rerender } = renderWithRoute('/', <Layout><div>home</div></Layout>);

    const chatLink1 = screen.getAllByRole('link', { name: /chat/i })[0];
    expect(chatLink1.className).toMatch(/bg-primary-100|dark:bg-primary-800\/50/);

    rerender(
      <MemoryRouter initialEntries={["/chat"]}>
        <ThemeProvider>
          <Layout><div>chat</div></Layout>
        </ThemeProvider>
      </MemoryRouter>
    );
    const chatLink2 = screen.getAllByRole('link', { name: /chat/i })[0];
    expect(chatLink2.className).toMatch(/bg-primary-100|dark:bg-primary-800\/50/);
  });

  test('highlights Tasks link as active on /tasks', () => {
    renderWithRoute('/tasks', <Layout><div>tasks</div></Layout>);
    const tasksLink = screen.getAllByRole('link', { name: /tasks/i })[0];
    expect(tasksLink.className).toMatch(/bg-primary-100|dark:bg-primary-800\/50/);
  });

  test('mobile menu toggles via button (aria-expanded) and reveals drawer links', () => {
    renderWithRoute('/', <Layout><div>home</div></Layout>);

    const menuButton = screen.getByRole('button', { name: /open main menu/i });
    expect(menuButton).toHaveAttribute('aria-expanded', 'false');

    fireEvent.click(menuButton);
    expect(menuButton).toHaveAttribute('aria-expanded', 'true');

    // Drawer-only list exists when open; find a Tasks link whose closest aside has the mobile-only class
    const tasksLinks = screen.getAllByRole('link', { name: /tasks/i });
    const hasMobileAside = tasksLinks.some(l => l.closest('aside')?.className.includes('md:hidden'));
    expect(hasMobileAside).toBe(true);

    // Close again
    fireEvent.click(menuButton);
    expect(menuButton).toHaveAttribute('aria-expanded', 'false');
  });
});
