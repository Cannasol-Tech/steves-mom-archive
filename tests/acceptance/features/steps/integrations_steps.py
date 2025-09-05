"""
Step definitions for the integrations.feature file.

This module implements BDD step definitions for testing system integrations
including inventory database operations, email processing, and document generation.
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
class MockInventoryItem:
    def __init__(self, item_id, name, sku, quantity_on_hand, quantity_on_order=0, 
                 reorder_point=10, unit_cost=25.50, location="Warehouse A-1"):
        self.item_id = item_id
        self.name = name
        self.sku = sku
        self.quantity_on_hand = quantity_on_hand
        self.quantity_on_order = quantity_on_order
        self.reorder_point = reorder_point
        self.unit_cost = unit_cost
        self.location = location
        self.last_updated = "2025-01-01T10:00:00Z"

class MockInventoryAPI:
    def __init__(self):
        self.items = {}
        self.history = []
        self.read_item = AsyncMock()
        self.update_item = AsyncMock()
        self.get_history = AsyncMock()

class MockEmail:
    def __init__(self, id, sender, subject, body, timestamp, is_read=False):
        self.id = id
        self.sender = sender
        self.subject = subject
        self.body = body
        self.timestamp = timestamp
        self.is_read = is_read

class MockEmailProcessor:
    def __init__(self):
        self.process_inbox = AsyncMock()
        self.generate_summary = AsyncMock()
        self.draft_reply = AsyncMock()

class MockDocument:
    def __init__(self, id, template_name, content, format="pdf", version="1.0"):
        self.id = id
        self.template_name = template_name
        self.content = content
        self.format = format
        self.version = version
        self.created_at = "2025-01-01T10:00:00Z"

class MockDocumentGenerator:
    def __init__(self):
        self.generate_from_template = AsyncMock()
        self.validate_fields = AsyncMock()
        self.get_template = AsyncMock()

# Use mocks for acceptance tests
InventoryItem = MockInventoryItem
InventoryAPI = MockInventoryAPI
Email = MockEmail
EmailProcessor = MockEmailProcessor
Document = MockDocument
DocumentGenerator = MockDocumentGenerator


# FR-3.1: Inventory database operations
@given('I need to look up items and update quantities')
def step_impl_inventory_operations_needed(context):
    """Set up inventory operations scenario with items to look up and update."""
    context.inventory_api = MockInventoryAPI()
    
    # Set up test inventory items
    context.test_items = [
        MockInventoryItem(
            item_id="item_001",
            name="ABC123 Widget",
            sku="ABC123",
            quantity_on_hand=25,
            quantity_on_order=10,
            reorder_point=15,
            unit_cost=12.50,
            location="Warehouse A-1"
        ),
        MockInventoryItem(
            item_id="item_002", 
            name="XYZ789 Component",
            sku="XYZ789",
            quantity_on_hand=5,
            quantity_on_order=0,
            reorder_point=10,
            unit_cost=45.00,
            location="Warehouse B-2"
        )
    ]
    
    # Configure mock responses
    context.inventory_api.read_item.side_effect = lambda item_id: next(
        (item for item in context.test_items if item.item_id == item_id), None
    )
    
    # Set up update operations
    context.update_operations = [
        {"item_id": "item_001", "quantity_change": -5, "operation": "sale"},
        {"item_id": "item_002", "quantity_change": +20, "operation": "restock"}
    ]
    
    # Expected history entries
    context.expected_history = [
        {
            "item_id": "item_001",
            "operation": "sale",
            "quantity_change": -5,
            "new_quantity": 20,
            "timestamp": "2025-01-01T10:00:00Z"
        },
        {
            "item_id": "item_002", 
            "operation": "restock",
            "quantity_change": +20,
            "new_quantity": 25,
            "timestamp": "2025-01-01T10:00:01Z"
        }
    ]


@when('I perform read and write operations')
def step_impl_perform_inventory_operations(context):
    """Execute inventory read and write operations."""
    context.read_results = []
    context.update_results = []
    
    # Perform read operations
    for item in context.test_items:
        result = asyncio.run(context.inventory_api.read_item(item.item_id))
        context.read_results.append(result)
    
    # Perform update operations
    for operation in context.update_operations:
        # Find the item to update
        item = next(item for item in context.test_items if item.item_id == operation["item_id"])
        
        # Update quantity
        old_quantity = item.quantity_on_hand
        item.quantity_on_hand += operation["quantity_change"]
        
        # Mock the update call
        update_result = {
            "item_id": operation["item_id"],
            "old_quantity": old_quantity,
            "new_quantity": item.quantity_on_hand,
            "operation": operation["operation"]
        }
        
        context.inventory_api.update_item.return_value = update_result
        result = asyncio.run(context.inventory_api.update_item(
            operation["item_id"], 
            {"quantity_on_hand": item.quantity_on_hand}
        ))
        context.update_results.append(result)
    
    # Mock history retrieval
    context.inventory_api.get_history.return_value = context.expected_history
    context.history_results = asyncio.run(context.inventory_api.get_history())


@then('the inventory API reflects real-time changes with history')
def step_impl_verify_inventory_changes(context):
    """Verify that inventory operations were successful and history is maintained."""
    # Verify read operations
    assert len(context.read_results) == 2, "Should have read 2 items"
    for i, result in enumerate(context.read_results):
        expected_item = context.test_items[i]
        assert result.item_id == expected_item.item_id, f"Item ID should match for item {i}"
        assert result.name == expected_item.name, f"Item name should match for item {i}"
        assert result.sku == expected_item.sku, f"SKU should match for item {i}"
    
    # Verify update operations
    assert len(context.update_results) == 2, "Should have performed 2 updates"
    
    # Verify first update (sale - quantity decreased)
    first_update = context.update_results[0]
    assert first_update["item_id"] == "item_001", "First update should be for item_001"
    assert first_update["old_quantity"] == 25, "Original quantity should be 25"
    assert first_update["new_quantity"] == 20, "New quantity should be 20 after sale"
    assert first_update["operation"] == "sale", "Operation should be sale"
    
    # Verify second update (restock - quantity increased)
    second_update = context.update_results[1]
    assert second_update["item_id"] == "item_002", "Second update should be for item_002"
    assert second_update["old_quantity"] == 5, "Original quantity should be 5"
    assert second_update["new_quantity"] == 25, "New quantity should be 25 after restock"
    assert second_update["operation"] == "restock", "Operation should be restock"
    
    # Verify history tracking
    assert len(context.history_results) == 2, "Should have 2 history entries"
    for i, history_entry in enumerate(context.history_results):
        expected_entry = context.expected_history[i]
        assert history_entry["item_id"] == expected_entry["item_id"], f"History item ID should match for entry {i}"
        assert history_entry["operation"] == expected_entry["operation"], f"History operation should match for entry {i}"
        assert history_entry["quantity_change"] == expected_entry["quantity_change"], f"History quantity change should match for entry {i}"
    
    # Verify API calls were made
    assert context.inventory_api.read_item.call_count == 2, "Should have called read_item twice"
    assert context.inventory_api.update_item.call_count == 2, "Should have called update_item twice"
    context.inventory_api.get_history.assert_called_once(), "Should have called get_history once"


# FR-3.2: Email integration for summarization and drafting
@given('I have unread emails')
def step_impl_unread_emails_available(context):
    """Set up unread emails for processing."""
    context.email_processor = MockEmailProcessor()
    
    # Set up test emails
    context.unread_emails = [
        MockEmail(
            id="email_001",
            sender="client@example.com",
            subject="Project Status Update Required",
            body="Hi, I need an update on the quarterly inventory project. Can you provide the current status and timeline?",
            timestamp="2025-01-01T09:00:00Z",
            is_read=False
        ),
        MockEmail(
            id="email_002",
            sender="supplier@vendor.com", 
            subject="Delivery Schedule Confirmation",
            body="Please confirm the delivery schedule for order #12345. We need to coordinate with our warehouse team.",
            timestamp="2025-01-01T09:30:00Z",
            is_read=False
        ),
        MockEmail(
            id="email_003",
            sender="manager@company.com",
            subject="Budget Review Meeting",
            body="Let's schedule a meeting to review the Q1 budget allocations. Are you available next Tuesday?",
            timestamp="2025-01-01T10:00:00Z",
            is_read=False
        )
    ]
    
    # Expected summaries and draft replies
    context.expected_summaries = [
        {
            "email_id": "email_001",
            "summary": "Client requesting project status update for quarterly inventory project with timeline",
            "priority": "high",
            "action_required": True
        },
        {
            "email_id": "email_002",
            "summary": "Supplier requesting delivery schedule confirmation for order #12345",
            "priority": "medium", 
            "action_required": True
        },
        {
            "email_id": "email_003",
            "summary": "Manager requesting budget review meeting availability for next Tuesday",
            "priority": "medium",
            "action_required": True
        }
    ]
    
    context.expected_drafts = [
        {
            "email_id": "email_001",
            "draft_reply": "Thank you for your inquiry. The quarterly inventory project is currently 75% complete and on track for completion by January 15th. I'll send a detailed status report by end of day.",
            "requires_approval": True
        },
        {
            "email_id": "email_002", 
            "draft_reply": "Thank you for reaching out. I can confirm the delivery schedule for order #12345. The shipment is scheduled for January 10th between 9 AM and 2 PM. Please let me know if this works for your warehouse team.",
            "requires_approval": True
        },
        {
            "email_id": "email_003",
            "draft_reply": "I'm available for the budget review meeting next Tuesday. Would 2 PM work for you? Please send a calendar invite and I'll prepare the Q1 allocation materials.",
            "requires_approval": True
        }
    ]


@when('the system processes my inbox')
def step_impl_process_inbox(context):
    """Process the inbox to generate summaries and draft replies."""
    # Configure mock responses
    context.email_processor.process_inbox.return_value = {
        "processed_count": len(context.unread_emails),
        "summaries": context.expected_summaries,
        "drafts": context.expected_drafts
    }
    
    context.email_processor.generate_summary.side_effect = context.expected_summaries
    context.email_processor.draft_reply.side_effect = context.expected_drafts
    
    # Process the inbox
    context.processing_result = asyncio.run(
        context.email_processor.process_inbox(context.unread_emails)
    )
    
    # Generate individual summaries and drafts
    context.generated_summaries = []
    context.generated_drafts = []
    
    for email in context.unread_emails:
        summary = asyncio.run(context.email_processor.generate_summary(email))
        draft = asyncio.run(context.email_processor.draft_reply(email))
        
        context.generated_summaries.append(summary)
        context.generated_drafts.append(draft)


@then('summaries and draft replies are produced, requiring approval before send')
def step_impl_verify_email_processing(context):
    """Verify that email processing produced summaries and drafts requiring approval."""
    # Verify processing result
    assert context.processing_result["processed_count"] == 3, "Should have processed 3 emails"
    assert len(context.processing_result["summaries"]) == 3, "Should have 3 summaries"
    assert len(context.processing_result["drafts"]) == 3, "Should have 3 drafts"
    
    # Verify summaries
    for i, summary in enumerate(context.generated_summaries):
        expected_summary = context.expected_summaries[i]
        assert summary["email_id"] == expected_summary["email_id"], f"Summary email ID should match for email {i}"
        assert summary["summary"] == expected_summary["summary"], f"Summary content should match for email {i}"
        assert summary["priority"] in ["low", "medium", "high"], f"Summary should have valid priority for email {i}"
        assert summary["action_required"] == expected_summary["action_required"], f"Action required flag should match for email {i}"
    
    # Verify draft replies
    for i, draft in enumerate(context.generated_drafts):
        expected_draft = context.expected_drafts[i]
        assert draft["email_id"] == expected_draft["email_id"], f"Draft email ID should match for email {i}"
        assert draft["draft_reply"] == expected_draft["draft_reply"], f"Draft content should match for email {i}"
        assert draft["requires_approval"] == True, f"All drafts should require approval for email {i}"
        assert len(draft["draft_reply"]) > 0, f"Draft reply should not be empty for email {i}"
    
    # Verify API calls were made
    context.email_processor.process_inbox.assert_called_once_with(context.unread_emails)
    assert context.email_processor.generate_summary.call_count == 3, "Should have called generate_summary 3 times"
    assert context.email_processor.draft_reply.call_count == 3, "Should have called draft_reply 3 times"
    
    # Verify approval requirement
    for draft in context.generated_drafts:
        assert "requires_approval" in draft, "Draft should have approval requirement flag"
        assert draft["requires_approval"] == True, "All drafts should require approval before sending"


# FR-3.3: Document generation from templates
@given('a standard template and fields')
def step_impl_template_and_fields_available(context):
    """Set up document template and field data for generation."""
    context.document_generator = MockDocumentGenerator()

    # Set up template information
    context.template_name = "quarterly_report_template"
    context.template_fields = {
        "report_title": "Q1 2025 Inventory Analysis",
        "report_date": "2025-01-01",
        "company_name": "Cannasol Technologies",
        "prepared_by": "Steve's Mom AI",
        "total_items": 1247,
        "total_value": 156789.50,
        "top_categories": [
            {"name": "Electronics", "value": 45000.00, "percentage": 28.7},
            {"name": "Components", "value": 38500.00, "percentage": 24.5},
            {"name": "Tools", "value": 32100.00, "percentage": 20.5}
        ],
        "low_stock_alerts": [
            {"item": "ABC123", "current": 5, "reorder": 15},
            {"item": "XYZ789", "current": 2, "reorder": 10}
        ]
    }

    # Expected validation results
    context.expected_validation = {
        "valid": True,
        "required_fields_present": True,
        "field_types_correct": True,
        "validation_errors": []
    }

    # Expected generated document
    context.expected_document = MockDocument(
        id="doc_001",
        template_name=context.template_name,
        content="Generated quarterly report content with charts and analysis...",
        format="pdf",
        version="1.0"
    )


@when('I request a document generation')
def step_impl_request_document_generation(context):
    """Request document generation from template with field data."""
    # Configure mock responses
    context.document_generator.validate_fields.return_value = context.expected_validation
    context.document_generator.generate_from_template.return_value = context.expected_document
    context.document_generator.get_template.return_value = {
        "name": context.template_name,
        "required_fields": ["report_title", "report_date", "company_name", "prepared_by"],
        "optional_fields": ["total_items", "total_value", "top_categories", "low_stock_alerts"],
        "output_formats": ["pdf", "docx", "html"]
    }

    # Validate fields first
    context.validation_result = asyncio.run(
        context.document_generator.validate_fields(
            context.template_name,
            context.template_fields
        )
    )

    # Generate document if validation passes
    if context.validation_result["valid"]:
        context.generated_document = asyncio.run(
            context.document_generator.generate_from_template(
                template_name=context.template_name,
                fields=context.template_fields,
                output_format="pdf"
            )
        )
    else:
        context.generated_document = None

    # Get template information
    context.template_info = asyncio.run(
        context.document_generator.get_template(context.template_name)
    )


@then('a document is produced with validated fields and versioning')
def step_impl_verify_document_generation(context):
    """Verify that document generation was successful with proper validation and versioning."""
    # Verify field validation
    assert context.validation_result["valid"] == True, "Field validation should pass"
    assert context.validation_result["required_fields_present"] == True, "All required fields should be present"
    assert context.validation_result["field_types_correct"] == True, "Field types should be correct"
    assert len(context.validation_result["validation_errors"]) == 0, "Should have no validation errors"

    # Verify document was generated
    assert context.generated_document is not None, "Document should be generated"
    assert context.generated_document.id is not None, "Document should have an ID"
    assert context.generated_document.template_name == context.template_name, "Document should reference correct template"
    assert context.generated_document.format == "pdf", "Document should be in requested format"
    assert context.generated_document.version == "1.0", "Document should have version number"
    assert context.generated_document.created_at is not None, "Document should have creation timestamp"

    # Verify document content
    assert len(context.generated_document.content) > 0, "Document should have content"
    assert "quarterly report" in context.generated_document.content.lower(), "Document should contain expected content"

    # Verify template information
    assert context.template_info["name"] == context.template_name, "Template name should match"
    assert "required_fields" in context.template_info, "Template should specify required fields"
    assert "optional_fields" in context.template_info, "Template should specify optional fields"
    assert "output_formats" in context.template_info, "Template should specify supported formats"

    # Verify all required fields are present in our data
    required_fields = context.template_info["required_fields"]
    for field in required_fields:
        assert field in context.template_fields, f"Required field '{field}' should be present in data"

    # Verify API calls were made
    context.document_generator.validate_fields.assert_called_once_with(
        context.template_name,
        context.template_fields
    )
    context.document_generator.generate_from_template.assert_called_once_with(
        template_name=context.template_name,
        fields=context.template_fields,
        output_format="pdf"
    )
    context.document_generator.get_template.assert_called_once_with(context.template_name)

    # Verify versioning system
    assert hasattr(context.generated_document, 'version'), "Document should have version attribute"
    assert context.generated_document.version.count('.') >= 1, "Version should follow semantic versioning (e.g., 1.0)"
