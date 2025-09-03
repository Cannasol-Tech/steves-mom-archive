import React from 'react';
import { render, screen } from '@testing-library/react';
import AgentTasksPanel from '../AgentTasksPanel';
import { TaskStatus } from '../../types/tasks';

const mockTasks = [
  {
    id: '1',
    taskId: 'task-1',
    content: 'First test task',
    role: 'assistant' as const,
    timestamp: new Date(),
    taskStatus: TaskStatus.PENDING_APPROVAL,
  },
];

describe('AgentTasksPanel', () => {
  test('does not render when closed', () => {
    render(<AgentTasksPanel isOpen={false} onClose={() => {}} tasks={[]} onApprove={() => {}} onReject={() => {}} />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  test('renders when open', () => {
    render(<AgentTasksPanel isOpen={true} onClose={() => {}} tasks={[]} onApprove={() => {}} onReject={() => {}} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
        expect(screen.getByText('Agent Tasks')).toBeInTheDocument();
  });

  test('renders tasks when open', () => {
    render(<AgentTasksPanel isOpen={true} onClose={() => {}} tasks={mockTasks} onApprove={() => {}} onReject={() => {}} />);
    expect(screen.getByText('First test task')).toBeInTheDocument();
    expect(screen.getByText('Approve')).toBeInTheDocument();
    expect(screen.getByText('Reject')).toBeInTheDocument();
  });
});
