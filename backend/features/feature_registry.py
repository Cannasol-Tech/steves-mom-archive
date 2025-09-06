"""
Feature Implementation Registry

This module tracks which features are implemented vs planned,
allowing tests to automatically skip unimplemented scenarios.
"""
from enum import Enum
from typing import Dict, Set, Optional
from dataclasses import dataclass
from pathlib import Path
import json


class ImplementationStatus(Enum):
    """Feature implementation status."""

    NOT_IMPLEMENTED = "not_implemented"
    PARTIAL = "partial"
    IMPLEMENTED = "implemented"
    DEPRECATED = "deprecated"


@dataclass
class FeatureInfo:
    """Information about a feature's implementation status."""

    feature_id: str
    name: str
    status: ImplementationStatus
    description: str
    dependencies: Set[str]
    implementation_notes: Optional[str] = None
    skip_reason: Optional[str] = None


class FeatureRegistry:
    """Registry for tracking feature implementation status."""

    def __init__(self):
        self.features: Dict[str, FeatureInfo] = {}
        self._load_default_features()

    def _load_default_features(self):
        """Load the default feature registry."""
        # Core Chat Interface Features
        self.register_feature(
            FeatureInfo(
                feature_id="FR-1.1",
                name="AI Model Integration",
                status=ImplementationStatus.IMPLEMENTED,
                description="Basic AI model routing with GROK provider",
                dependencies=set(),
                implementation_notes="Model router and GROK provider implemented",
            )
        )

        self.register_feature(
            FeatureInfo(
                feature_id="FR-1.2",
                name="Conversation Management",
                status=ImplementationStatus.IMPLEMENTED,
                description="Context retention across conversation turns",
                dependencies={"FR-1.1"},
                implementation_notes="Conversation manager with persistent storage implemented",
            )
        )

        self.register_feature(
            FeatureInfo(
                feature_id="FR-1.3",
                name="NLP Intent Recognition",
                status=ImplementationStatus.NOT_IMPLEMENTED,
                description="Extract intents and entities for task generation",
                dependencies={"FR-1.1"},
                skip_reason="NLP intent recognition system not implemented",
            )
        )

        # Task Generation and Workflow Features
        self.register_feature(
            FeatureInfo(
                feature_id="FR-2.1",
                name="Intelligent Task Generation",
                status=ImplementationStatus.NOT_IMPLEMENTED,
                description="Generate tasks from natural language requests",
                dependencies={"FR-1.3"},
                skip_reason="Task generation engine not implemented",
            )
        )

        self.register_feature(
            FeatureInfo(
                feature_id="FR-2.2",
                name="Approval Workflow",
                status=ImplementationStatus.IMPLEMENTED,
                description="Task approval, rejection, and modification with history",
                dependencies=set(),
                implementation_notes="Basic approval workflow implemented in API",
            )
        )

        self.register_feature(
            FeatureInfo(
                feature_id="FR-2.3",
                name="Task Execution and Progress",
                status=ImplementationStatus.NOT_IMPLEMENTED,
                description="Execute tasks and track progress with status updates",
                dependencies={"FR-2.1", "FR-2.2"},
                skip_reason="Task execution engine not implemented",
            )
        )

        # System Integrations Features
        self.register_feature(
            FeatureInfo(
                feature_id="FR-3.1",
                name="Inventory Database Operations",
                status=ImplementationStatus.PARTIAL,
                description="Real-time inventory queries and updates",
                dependencies=set(),
                implementation_notes="Mock implementation exists, real database integration needed",
                skip_reason="Real inventory database not connected",
            )
        )

        self.register_feature(
            FeatureInfo(
                feature_id="FR-3.2",
                name="Email Integration",
                status=ImplementationStatus.NOT_IMPLEMENTED,
                description="Email summarization and draft generation",
                dependencies=set(),
                skip_reason="Email integration not implemented",
            )
        )

        self.register_feature(
            FeatureInfo(
                feature_id="FR-3.3",
                name="Document Generation",
                status=ImplementationStatus.NOT_IMPLEMENTED,
                description="Generate documents from templates",
                dependencies=set(),
                skip_reason="Document generation system not implemented",
            )
        )

        # Security and Access Control Features
        self.register_feature(
            FeatureInfo(
                feature_id="FR-4.1",
                name="Azure AD Authentication",
                status=ImplementationStatus.NOT_IMPLEMENTED,
                description="Azure AD SSO authentication",
                dependencies=set(),
                skip_reason="Azure AD integration not implemented",
            )
        )

        self.register_feature(
            FeatureInfo(
                feature_id="FR-4.2",
                name="Role-based Authorization",
                status=ImplementationStatus.NOT_IMPLEMENTED,
                description="RBAC system with permissions",
                dependencies={"FR-4.1"},
                skip_reason="RBAC system not implemented",
            )
        )

        self.register_feature(
            FeatureInfo(
                feature_id="FR-4.3",
                name="Audit and Compliance Logging",
                status=ImplementationStatus.NOT_IMPLEMENTED,
                description="Audit logs with export capabilities",
                dependencies={"FR-4.1"},
                skip_reason="Audit logging system not implemented",
            )
        )

        # Analytics and Learning Features
        self.register_feature(
            FeatureInfo(
                feature_id="FR-5.1",
                name="Performance Metrics",
                status=ImplementationStatus.PARTIAL,
                description="System performance and usage metrics",
                dependencies=set(),
                implementation_notes="Basic task analytics implemented",
                skip_reason="Comprehensive metrics collection not implemented",
            )
        )

        self.register_feature(
            FeatureInfo(
                feature_id="FR-5.2",
                name="Training Data Collection",
                status=ImplementationStatus.NOT_IMPLEMENTED,
                description="Collect data for model improvement",
                dependencies={"FR-5.1"},
                skip_reason="Training data collection not implemented",
            )
        )

    def register_feature(self, feature: FeatureInfo):
        """Register a feature in the registry."""
        self.features[feature.feature_id] = feature

    def get_feature(self, feature_id: str) -> Optional[FeatureInfo]:
        """Get feature information by ID."""
        return self.features.get(feature_id)

    def is_implemented(self, feature_id: str) -> bool:
        """Check if a feature is fully implemented."""
        feature = self.get_feature(feature_id)
        return feature is not None and feature.status == ImplementationStatus.IMPLEMENTED

    def should_skip(self, feature_id: str) -> bool:
        """Check if a feature should be skipped in tests."""
        feature = self.get_feature(feature_id)
        if not feature:
            return True  # Skip unknown features

        return feature.status in [
            ImplementationStatus.NOT_IMPLEMENTED,
            ImplementationStatus.DEPRECATED,
        ]

    def get_skip_reason(self, feature_id: str) -> str:
        """Get the reason why a feature should be skipped."""
        feature = self.get_feature(feature_id)
        if not feature:
            return f"Feature {feature_id} not found in registry"

        if feature.skip_reason:
            return feature.skip_reason

        if feature.status == ImplementationStatus.NOT_IMPLEMENTED:
            return f"Feature {feature_id} not implemented yet"
        elif feature.status == ImplementationStatus.DEPRECATED:
            return f"Feature {feature_id} is deprecated"
        else:
            return f"Feature {feature_id} status: {feature.status.value}"

    def get_implemented_features(self) -> Set[str]:
        """Get all implemented feature IDs."""
        return {
            fid
            for fid, feature in self.features.items()
            if feature.status == ImplementationStatus.IMPLEMENTED
        }

    def get_unimplemented_features(self) -> Set[str]:
        """Get all unimplemented feature IDs."""
        return {
            fid
            for fid, feature in self.features.items()
            if feature.status == ImplementationStatus.NOT_IMPLEMENTED
        }

    def export_to_json(self, file_path: Path):
        """Export feature registry to JSON file."""
        data = {
            fid: {
                "name": feature.name,
                "status": feature.status.value,
                "description": feature.description,
                "dependencies": list(feature.dependencies),
                "implementation_notes": feature.implementation_notes,
                "skip_reason": feature.skip_reason,
            }
            for fid, feature in self.features.items()
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_status_summary(self) -> Dict[str, int]:
        """Get a summary of feature statuses."""
        summary = {}
        for status in ImplementationStatus:
            summary[status.value] = sum(
                1 for feature in self.features.values() if feature.status == status
            )
        return summary


# Global feature registry instance
feature_registry = FeatureRegistry()


def is_feature_implemented(feature_id: str) -> bool:
    """Check if a feature is implemented."""
    return feature_registry.is_implemented(feature_id)


def should_skip_feature(feature_id: str) -> bool:
    """Check if a feature should be skipped in tests."""
    return feature_registry.should_skip(feature_id)


def get_skip_reason(feature_id: str) -> str:
    """Get the reason why a feature should be skipped."""
    return feature_registry.get_skip_reason(feature_id)
