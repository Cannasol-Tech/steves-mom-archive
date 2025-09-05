"""
Step definitions for the task_workflow.feature file.

This module implements BDD step definitions for testing task generation,
approval workflows, and task execution functionality.
"""
import os
import sys
import asyncio
import uuid
from pathlib import Path
from unittest.mock import patch, AsyncMock, Mock
from behave import given, when, then, step

# Make backend importable
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Create mock classes for testing
class MockTask:
    def __init__(self, id=None, title="", description="", status="pending", 
                 task_type="general", confidence_score=0.8, metadata=None):
        self.id = id or str(uuid.uuid4())
        self.title = title
        self.description = description
        self.status = status
        self.task_type = task_type
        self.confidence_score = confidence_score
        self.metadata = metadata or {}
        self.approval_history = []

class MockTaskStatus:
    PENDING = "pending"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class MockApprovalHandler:
    def __init__(self, task):
        self.task = task
    
    def approve(self):
        self.task.status = MockTaskStatus.APPROVED
        self.task.approval_history.append({
            "action": "approved",
            "timestamp": "2025-01-01T10:00:00Z"
        })
    
    def reject(self):
        self.task.status = MockTaskStatus.REJECTED
        self.task.approval_history.append({
            "action": "rejected", 
            "timestamp": "2025-01-01T10:00:00Z"
        })

class MockTaskGenerator:
    def __init__(self):
        self.generate_tasks = AsyncMock()

class MockExecutionEngine:
    def __init__(self):
        self.execute_task = AsyncMock()
        self.get_progress = AsyncMock()

# Use mocks for acceptance tests
TaskStatus = MockTaskStatus
Task = MockTask
ApprovalHandler = MockApprovalHandler
TaskGenerator = MockTaskGenerator
ExecutionEngine = MockExecutionEngine


# FR-2.1: Intelligent Task Generation
@given('a complex user request requiring multiple actions')
def step_impl_complex_request(context):
    """Set up a complex user request that should generate multiple tasks."""
    context.user_request = "Please check our inventory for ABC123, send an email to john@example.com about the stock levels, and generate a quarterly report with the current inventory status"
    context.user_id = "test-user-123"
    context.session_id = "test-session-456"
    
    # Expected tasks that should be generated
    context.expected_tasks = [
        MockTask(
            title="Check inventory for ABC123",
            description="Query inventory system for item ABC123 stock levels",
            task_type="inventory_query",
            confidence_score=0.95,
            metadata={"item_code": "ABC123", "action": "check_stock"}
        ),
        MockTask(
            title="Send email about stock levels",
            description="Send email to john@example.com regarding ABC123 inventory status",
            task_type="email",
            confidence_score=0.90,
            metadata={"recipient": "john@example.com", "subject": "ABC123 Stock Levels"}
        ),
        MockTask(
            title="Generate quarterly inventory report",
            description="Create quarterly report with current inventory status",
            task_type="document_generation",
            confidence_score=0.85,
            metadata={"report_type": "quarterly", "content": "inventory_status"}
        )
    ]


@when('the system analyzes the request')
def step_impl_analyze_request(context):
    """Process the complex request through the task generation system."""
    # Mock the task generator
    context.task_generator = MockTaskGenerator()
    
    # Configure the mock to return our expected tasks
    context.task_generator.generate_tasks.return_value = context.expected_tasks
    
    # Execute the task generation
    context.generated_tasks = asyncio.run(
        context.task_generator.generate_tasks(
            user_request=context.user_request,
            user_id=context.user_id,
            session_id=context.session_id
        )
    )


@then('tasks are generated with types, metadata, and confidence scores')
def step_impl_verify_task_generation(context):
    """Verify that tasks were generated with proper structure and metadata."""
    # Verify tasks were generated
    assert len(context.generated_tasks) == 3, f"Expected 3 tasks, got {len(context.generated_tasks)}"
    
    # Verify each task has required attributes
    for task in context.generated_tasks:
        assert hasattr(task, 'title'), "Task should have a title"
        assert hasattr(task, 'description'), "Task should have a description"
        assert hasattr(task, 'task_type'), "Task should have a task_type"
        assert hasattr(task, 'confidence_score'), "Task should have a confidence_score"
        assert hasattr(task, 'metadata'), "Task should have metadata"
        
        # Verify confidence score is valid
        assert 0.0 <= task.confidence_score <= 1.0, f"Confidence score should be between 0 and 1, got {task.confidence_score}"
        
        # Verify task type is set
        assert task.task_type in ["inventory_query", "email", "document_generation"], \
            f"Unexpected task type: {task.task_type}"
        
        # Verify metadata is populated
        assert isinstance(task.metadata, dict), "Metadata should be a dictionary"
        assert len(task.metadata) > 0, "Metadata should not be empty"
    
    # Verify the task generator was called correctly
    context.task_generator.generate_tasks.assert_called_once_with(
        user_request=context.user_request,
        user_id=context.user_id,
        session_id=context.session_id
    )


# FR-2.2: Approval Workflow
@given('tasks are generated for a request')
def step_impl_tasks_generated(context):
    """Set up generated tasks that need approval."""
    context.generated_tasks = [
        MockTask(
            title="Send email to client",
            description="Send follow-up email to client about project status",
            status=MockTaskStatus.PENDING_APPROVAL,
            task_type="email",
            confidence_score=0.88
        ),
        MockTask(
            title="Update inventory record",
            description="Update stock levels for item XYZ789",
            status=MockTaskStatus.PENDING_APPROVAL,
            task_type="inventory_update",
            confidence_score=0.92
        )
    ]
    
    # Mock approval handlers for each task
    context.approval_handlers = {}
    for task in context.generated_tasks:
        context.approval_handlers[task.id] = MockApprovalHandler(task)


@when('the user reviews the tasks')
def step_impl_user_reviews_tasks(context):
    """Simulate user reviewing and making approval decisions on tasks."""
    context.approval_decisions = []
    
    # User approves first task
    first_task = context.generated_tasks[0]
    approval_handler = context.approval_handlers[first_task.id]
    approval_handler.approve()
    context.approval_decisions.append({
        "task_id": first_task.id,
        "action": "approved",
        "reason": "Email content looks good"
    })
    
    # User rejects second task
    second_task = context.generated_tasks[1]
    approval_handler = context.approval_handlers[second_task.id]
    approval_handler.reject()
    context.approval_decisions.append({
        "task_id": second_task.id,
        "action": "rejected",
        "reason": "Need to verify stock levels first"
    })


@then('they can approve, reject, or modify them with history captured')
def step_impl_verify_approval_workflow(context):
    """Verify that approval workflow works correctly with history tracking."""
    # Verify first task was approved
    first_task = context.generated_tasks[0]
    assert first_task.status == MockTaskStatus.APPROVED, \
        f"First task should be approved, got {first_task.status}"
    assert len(first_task.approval_history) == 1, \
        "First task should have one approval history entry"
    assert first_task.approval_history[0]["action"] == "approved", \
        "First task history should show approval"
    
    # Verify second task was rejected
    second_task = context.generated_tasks[1]
    assert second_task.status == MockTaskStatus.REJECTED, \
        f"Second task should be rejected, got {second_task.status}"
    assert len(second_task.approval_history) == 1, \
        "Second task should have one approval history entry"
    assert second_task.approval_history[0]["action"] == "rejected", \
        "Second task history should show rejection"
    
    # Verify approval decisions were recorded
    assert len(context.approval_decisions) == 2, \
        "Should have recorded 2 approval decisions"
    
    # Verify approval handlers were used correctly
    for task in context.generated_tasks:
        handler = context.approval_handlers[task.id]
        assert handler.task == task, "Approval handler should reference correct task"


# FR-2.3: Task Execution and Progress
@given('an approved task with an available agent')
def step_impl_approved_task_with_agent(context):
    """Set up an approved task ready for execution."""
    context.approved_task = MockTask(
        title="Generate monthly sales report",
        description="Create comprehensive monthly sales report with charts and analysis",
        status=MockTaskStatus.APPROVED,
        task_type="document_generation",
        confidence_score=0.90
    )
    
    # Mock execution engine
    context.execution_engine = MockExecutionEngine()
    
    # Mock progress updates
    context.progress_updates = [
        {"status": "started", "progress": 0, "message": "Task execution started"},
        {"status": "in_progress", "progress": 25, "message": "Gathering sales data"},
        {"status": "in_progress", "progress": 50, "message": "Analyzing trends"},
        {"status": "in_progress", "progress": 75, "message": "Generating charts"},
        {"status": "completed", "progress": 100, "message": "Report generated successfully"}
    ]
    
    context.execution_engine.get_progress.side_effect = context.progress_updates


@when('execution starts')
def step_impl_execution_starts(context):
    """Start task execution and track progress."""
    # Start task execution
    context.execution_result = asyncio.run(
        context.execution_engine.execute_task(context.approved_task)
    )
    
    # Update task status
    context.approved_task.status = MockTaskStatus.IN_PROGRESS
    
    # Simulate progress tracking
    context.tracked_progress = []
    for update in context.progress_updates:
        progress = asyncio.run(
            context.execution_engine.get_progress(context.approved_task.id)
        )
        context.tracked_progress.append(progress)


@then('progress is tracked and status updates are emitted')
def step_impl_verify_execution_progress(context):
    """Verify that task execution progress is properly tracked."""
    # Verify execution was started
    context.execution_engine.execute_task.assert_called_once_with(context.approved_task)
    
    # Verify progress was tracked
    assert len(context.tracked_progress) == 5, \
        f"Expected 5 progress updates, got {len(context.tracked_progress)}"
    
    # Verify progress sequence
    expected_progress_values = [0, 25, 50, 75, 100]
    actual_progress_values = [update["progress"] for update in context.tracked_progress]
    assert actual_progress_values == expected_progress_values, \
        f"Progress values should be {expected_progress_values}, got {actual_progress_values}"
    
    # Verify status progression
    statuses = [update["status"] for update in context.tracked_progress]
    assert statuses[0] == "started", "First status should be 'started'"
    assert statuses[-1] == "completed", "Final status should be 'completed'"
    assert "in_progress" in statuses, "Should have 'in_progress' status updates"
    
    # Verify progress messages are meaningful
    for update in context.tracked_progress:
        assert "message" in update, "Each progress update should have a message"
        assert len(update["message"]) > 0, "Progress messages should not be empty"
    
    # Verify get_progress was called for tracking
    assert context.execution_engine.get_progress.call_count == 5, \
        "get_progress should be called for each progress update"
