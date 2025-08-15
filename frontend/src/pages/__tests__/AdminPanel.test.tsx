import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import AdminPage from '../AdminPage';

describe('AdminPage feature toggles', () => {
  test('renders feature toggle switches with correct initial states', () => {
    render(<AdminPage />);
    
    // Check that all feature toggles are present
    expect(screen.getByLabelText(/NL→SQL Queries/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email Integration/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Document Generation/i)).toBeInTheDocument();
    
    // Check initial states (should be enabled by default)
    expect(screen.getByLabelText(/NL→SQL Queries/i)).toBeChecked();
    expect(screen.getByLabelText(/Email Integration/i)).toBeChecked();
    expect(screen.getByLabelText(/Document Generation/i)).toBeChecked();
  });

  test('toggles feature states when clicked', () => {
    render(<AdminPage />);
    
    const nlsqlToggle = screen.getByLabelText(/NL→SQL Queries/i);
    const emailToggle = screen.getByLabelText(/Email Integration/i);
    
    // Toggle NL→SQL off
    fireEvent.click(nlsqlToggle);
    expect(nlsqlToggle).not.toBeChecked();
    
    // Toggle email off
    fireEvent.click(emailToggle);
    expect(emailToggle).not.toBeChecked();
    
    // Toggle NL→SQL back on
    fireEvent.click(nlsqlToggle);
    expect(nlsqlToggle).toBeChecked();
  });

  test('displays system status indicators', () => {
    render(<AdminPage />);
    
    // Check system status elements
    expect(screen.getByText(/API Status/i)).toBeInTheDocument();
    expect(screen.getByText(/Database/i)).toBeInTheDocument();
    expect(screen.getByText(/AI Model/i)).toBeInTheDocument();
    
    // Check status badges
    expect(screen.getByText(/Online/i)).toBeInTheDocument();
    expect(screen.getByText(/Connected/i)).toBeInTheDocument();
    expect(screen.getByText(/Pending/i)).toBeInTheDocument();
  });

  test('renders quick action buttons', () => {
    render(<AdminPage />);
    
    expect(screen.getByRole('button', { name: /View System Logs/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Export Analytics/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Manage Users/i })).toBeInTheDocument();
  });

  test('shows performance metrics placeholders', () => {
    render(<AdminPage />);
    
    expect(screen.getByText(/Requests\/Hour/i)).toBeInTheDocument();
    expect(screen.getByText(/Avg Response Time/i)).toBeInTheDocument();
    expect(screen.getByText(/Uptime/i)).toBeInTheDocument();
    expect(screen.getByText(/Active Users/i)).toBeInTheDocument();
  });
});
