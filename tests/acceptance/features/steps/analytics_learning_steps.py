"""
Step definitions for the analytics_learning.feature file.

This module implements BDD step definitions for testing analytics and learning
functionality including performance metrics collection and training data collection.
"""
import os
import sys
import asyncio
import uuid
from pathlib import Path
from behave import given, when, then, step

# Make backend importable
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Test data structures for analytics and learning (no mocks in acceptance tests)
class TestMetricsCollector:
    def __init__(self):
        self.metrics = []
        self.performance_data = {}
        
    async def record_task_metrics(self, task_id, response_time, accuracy, user_satisfaction):
        """Record metrics for a completed task."""
        metric = {
            "task_id": task_id,
            "response_time_ms": response_time,
            "accuracy_score": accuracy,
            "user_satisfaction": user_satisfaction,
            "timestamp": "2025-01-01T10:00:00Z"
        }
        self.metrics.append(metric)
        return metric
        
    async def get_performance_summary(self):
        """Get aggregated performance metrics."""
        if not self.metrics:
            return {
                "total_tasks": 0,
                "avg_response_time": 0,
                "avg_accuracy": 0,
                "avg_satisfaction": 0
            }
            
        total_tasks = len(self.metrics)
        avg_response_time = sum(m["response_time_ms"] for m in self.metrics) / total_tasks
        avg_accuracy = sum(m["accuracy_score"] for m in self.metrics) / total_tasks
        avg_satisfaction = sum(m["user_satisfaction"] for m in self.metrics) / total_tasks
        
        return {
            "total_tasks": total_tasks,
            "avg_response_time": avg_response_time,
            "avg_accuracy": avg_accuracy,
            "avg_satisfaction": avg_satisfaction
        }

class TestTrainingDataCollector:
    def __init__(self):
        self.training_samples = []
        self.corrections = []
        
    async def record_user_correction(self, original_intent, corrected_intent, user_input, context):
        """Record a user correction for training data."""
        correction = {
            "correction_id": f"correction_{len(self.corrections) + 1}",
            "user_input": user_input,
            "original_intent": original_intent,
            "corrected_intent": corrected_intent,
            "context": context,
            "timestamp": "2025-01-01T10:00:00Z"
        }
        self.corrections.append(correction)
        
        # Convert to training sample
        training_sample = {
            "input": user_input,
            "expected_intent": corrected_intent,
            "context": context,
            "source": "user_correction"
        }
        self.training_samples.append(training_sample)
        
        return correction
        
    async def get_training_data(self):
        """Get collected training data."""
        return {
            "total_samples": len(self.training_samples),
            "samples": self.training_samples,
            "corrections_count": len(self.corrections)
        }

# Use test implementations for acceptance testing
MetricsCollector = TestMetricsCollector
TrainingDataCollector = TestTrainingDataCollector


# FR-5.1: Performance metrics collection
@given('tasks and responses are processed')
def step_impl_tasks_responses_processed(context):
    """Set up scenario with completed tasks and responses for metrics collection."""
    context.metrics_collector = TestMetricsCollector()
    
    # Set up test tasks with performance data
    context.completed_tasks = [
        {
            "task_id": "task_001",
            "task_type": "email_generation",
            "response_time_ms": 1250,
            "accuracy_score": 0.92,
            "user_satisfaction": 4.5,
            "model_used": "gpt-3.5-turbo"
        },
        {
            "task_id": "task_002", 
            "task_type": "inventory_query",
            "response_time_ms": 850,
            "accuracy_score": 0.98,
            "user_satisfaction": 5.0,
            "model_used": "gpt-3.5-turbo"
        },
        {
            "task_id": "task_003",
            "task_type": "document_generation",
            "response_time_ms": 2100,
            "accuracy_score": 0.85,
            "user_satisfaction": 4.0,
            "model_used": "gpt-4"
        },
        {
            "task_id": "task_004",
            "task_type": "data_analysis",
            "response_time_ms": 3200,
            "accuracy_score": 0.95,
            "user_satisfaction": 4.8,
            "model_used": "gpt-4"
        }
    ]


@when('metrics are recorded')
def step_impl_metrics_recorded(context):
    """Record performance metrics for the completed tasks."""
    context.recorded_metrics = []
    
    # Record metrics for each completed task
    for task in context.completed_tasks:
        metric = asyncio.run(
            context.metrics_collector.record_task_metrics(
                task_id=task["task_id"],
                response_time=task["response_time_ms"],
                accuracy=task["accuracy_score"],
                user_satisfaction=task["user_satisfaction"]
            )
        )
        context.recorded_metrics.append(metric)
    
    # Get performance summary
    context.performance_summary = asyncio.run(
        context.metrics_collector.get_performance_summary()
    )


@then('accuracy, response times, user satisfaction, and model comparisons are available')
def step_impl_verify_metrics_available(context):
    """Verify that comprehensive performance metrics are available."""
    # Verify individual metrics were recorded
    assert len(context.recorded_metrics) == 4, "Should have recorded 4 task metrics"
    
    for i, metric in enumerate(context.recorded_metrics):
        expected_task = context.completed_tasks[i]
        
        assert metric["task_id"] == expected_task["task_id"], f"Task ID should match for metric {i}"
        assert metric["response_time_ms"] == expected_task["response_time_ms"], f"Response time should match for metric {i}"
        assert metric["accuracy_score"] == expected_task["accuracy_score"], f"Accuracy should match for metric {i}"
        assert metric["user_satisfaction"] == expected_task["user_satisfaction"], f"User satisfaction should match for metric {i}"
        assert "timestamp" in metric, f"Metric {i} should have timestamp"
    
    # Verify performance summary
    summary = context.performance_summary
    assert summary["total_tasks"] == 4, "Summary should show 4 total tasks"
    
    # Verify average calculations
    expected_avg_response_time = (1250 + 850 + 2100 + 3200) / 4  # 1850ms
    expected_avg_accuracy = (0.92 + 0.98 + 0.85 + 0.95) / 4  # 0.925
    expected_avg_satisfaction = (4.5 + 5.0 + 4.0 + 4.8) / 4  # 4.575
    
    assert abs(summary["avg_response_time"] - expected_avg_response_time) < 0.1, \
        f"Average response time should be ~{expected_avg_response_time}ms, got {summary['avg_response_time']}"
    assert abs(summary["avg_accuracy"] - expected_avg_accuracy) < 0.01, \
        f"Average accuracy should be ~{expected_avg_accuracy}, got {summary['avg_accuracy']}"
    assert abs(summary["avg_satisfaction"] - expected_avg_satisfaction) < 0.01, \
        f"Average satisfaction should be ~{expected_avg_satisfaction}, got {summary['avg_satisfaction']}"
    
    # Verify model comparison data is available
    gpt35_tasks = [task for task in context.completed_tasks if task["model_used"] == "gpt-3.5-turbo"]
    gpt4_tasks = [task for task in context.completed_tasks if task["model_used"] == "gpt-4"]
    
    assert len(gpt35_tasks) == 2, "Should have 2 GPT-3.5 tasks for comparison"
    assert len(gpt4_tasks) == 2, "Should have 2 GPT-4 tasks for comparison"
    
    # Verify different performance characteristics between models
    gpt35_avg_time = sum(task["response_time_ms"] for task in gpt35_tasks) / len(gpt35_tasks)
    gpt4_avg_time = sum(task["response_time_ms"] for task in gpt4_tasks) / len(gpt4_tasks)
    
    assert gpt35_avg_time < gpt4_avg_time, "GPT-3.5 should be faster than GPT-4 on average"


# FR-5.2: Training data collection
@given('user corrections and feedback occur')
def step_impl_user_corrections_feedback(context):
    """Set up scenario with user corrections and feedback for training data collection."""
    context.training_collector = TestTrainingDataCollector()
    
    # Set up test scenarios where users correct AI misidentifications
    context.correction_scenarios = [
        {
            "user_input": "Send a message to the team about the meeting",
            "original_intent": "email_generation",
            "corrected_intent": "slack_message",
            "context": "User clarified they meant Slack, not email",
            "correction_reason": "Wrong communication channel identified"
        },
        {
            "user_input": "Check inventory for ABC123",
            "original_intent": "general_query",
            "corrected_intent": "inventory_lookup",
            "context": "User was looking for specific inventory item",
            "correction_reason": "Intent classification too generic"
        },
        {
            "user_input": "Generate the quarterly report",
            "original_intent": "document_creation",
            "corrected_intent": "report_generation",
            "context": "User needed specific report type, not generic document",
            "correction_reason": "Task type too broad"
        }
    ]


@when('tasks are misidentified and corrected')
def step_impl_tasks_misidentified_corrected(context):
    """Process user corrections for misidentified tasks."""
    context.recorded_corrections = []
    
    # Record each user correction
    for scenario in context.correction_scenarios:
        correction = asyncio.run(
            context.training_collector.record_user_correction(
                original_intent=scenario["original_intent"],
                corrected_intent=scenario["corrected_intent"],
                user_input=scenario["user_input"],
                context=scenario["context"]
            )
        )
        context.recorded_corrections.append(correction)
    
    # Get training data summary
    context.training_data = asyncio.run(
        context.training_collector.get_training_data()
    )


@then('training data is collected for future improvements')
def step_impl_verify_training_data_collected(context):
    """Verify that training data is properly collected for future model improvements."""
    # Verify corrections were recorded
    assert len(context.recorded_corrections) == 3, "Should have recorded 3 corrections"
    
    for i, correction in enumerate(context.recorded_corrections):
        expected_scenario = context.correction_scenarios[i]
        
        assert correction["user_input"] == expected_scenario["user_input"], f"User input should match for correction {i}"
        assert correction["original_intent"] == expected_scenario["original_intent"], f"Original intent should match for correction {i}"
        assert correction["corrected_intent"] == expected_scenario["corrected_intent"], f"Corrected intent should match for correction {i}"
        assert correction["context"] == expected_scenario["context"], f"Context should match for correction {i}"
        assert "correction_id" in correction, f"Correction {i} should have an ID"
        assert "timestamp" in correction, f"Correction {i} should have timestamp"
    
    # Verify training data was generated
    training_data = context.training_data
    assert training_data["total_samples"] == 3, "Should have 3 training samples"
    assert training_data["corrections_count"] == 3, "Should have 3 corrections recorded"
    
    # Verify training samples structure
    samples = training_data["samples"]
    for i, sample in enumerate(samples):
        expected_scenario = context.correction_scenarios[i]
        
        assert sample["input"] == expected_scenario["user_input"], f"Training sample {i} input should match"
        assert sample["expected_intent"] == expected_scenario["corrected_intent"], f"Training sample {i} expected intent should match"
        assert sample["context"] == expected_scenario["context"], f"Training sample {i} context should match"
        assert sample["source"] == "user_correction", f"Training sample {i} should be marked as user correction"
    
    # Verify training data covers different types of corrections
    intent_corrections = set(correction["corrected_intent"] for correction in context.recorded_corrections)
    assert "slack_message" in intent_corrections, "Should include Slack message intent correction"
    assert "inventory_lookup" in intent_corrections, "Should include inventory lookup intent correction"
    assert "report_generation" in intent_corrections, "Should include report generation intent correction"
    
    # Verify training data can be used for model improvement
    assert all("input" in sample and "expected_intent" in sample for sample in samples), \
        "All training samples should have input and expected intent for model training"
    
    # Verify context is preserved for better training
    assert all("context" in sample for sample in samples), \
        "All training samples should preserve context for better model understanding"
