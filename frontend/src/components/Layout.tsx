import React, { useState, ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);

  const isActive = (path: string) => {
    return location.pathname === path || (path === '/chat' && location.pathname === '/');
  };

  return (
    <div className="min-h-screen spatial-bg flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 h-16 flex items-center px-4 sm:px-6 lg:px-8">
        <div className="flex-1 flex items-center justify-between max-w-7xl w-full mx-auto">
          <Link to="/" className="flex items-center space-x-3">
            <img
              src="/cannasol-logo.png"
              alt="Cannasol Technologies"
              className="h-6 w-6 sm:h-8 sm:w-8 object-contain"
              onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
            />
            <span className="text-lg font-semibold text-gray-900">Steve's Mom</span>
          </Link>
          <div className="hidden md:block">
            <div className="flex items-center space-x-3">
              <span className="text-sm text-gray-500">Signed in as</span>
              <div className="w-8 h-8 bg-secondary-300 rounded-full" />
            </div>
          </div>
          <div className="md:hidden">
            <button
              type="button"
              className="inline-flex items-center justify-center rounded-md p-2 text-gray-600 hover:bg-gray-100 hover:text-gray-900 focus:outline-none"
              aria-controls="mobile-menu"
              aria-expanded={isOpen}
              onClick={() => setIsOpen(!isOpen)}
            >
              <span className="sr-only">Open main menu</span>
              <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* Body: Sidebar + Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <aside className="hidden md:flex md:flex-col md:w-60 border-r border-gray-200 bg-white">
          <nav className="flex-1 p-4 space-y-1">
            <Link
              to="/"
              className={`block px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                isActive('/') || isActive('/chat')
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              Chat
            </Link>
            <Link
              to="/admin"
              className={`block px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                isActive('/admin')
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              Admin
            </Link>
          </nav>
        </aside>

        {/* Mobile nav (drawer-like simple list) */}
        {isOpen && (
          <aside className="md:hidden w-full border-b border-gray-200 bg-white">
            <nav className="p-2 space-y-1">
              <Link
                to="/"
                onClick={() => setIsOpen(false)}
                className={`block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 ${
                  isActive('/') || isActive('/chat')
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                Chat
              </Link>
              <Link
                to="/admin"
                onClick={() => setIsOpen(false)}
                className={`block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 ${
                  isActive('/admin')
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                Admin
              </Link>
            </nav>
          </aside>
        )}

        {/* Main content */}
        <main className="flex-1 overflow-auto px-4 sm:px-6 lg:px-8 py-6 flex items-center justify-center">
          <div className="w-full max-w-4xl">
            {children}
          </div>
        </main>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-200">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-4 text-sm text-gray-500">
          &copy; {new Date().getFullYear()} Steve's Mom AI Chatbot. Built with &hearts; for efficient business operations.
        </div>
      </footer>
    </div>
  );
};

export default Layout;
