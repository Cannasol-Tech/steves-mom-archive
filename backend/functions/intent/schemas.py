from enum import Enum
from pydantic import BaseModel, Field

class Intent(str, Enum):
    """Enumeration of possible user intents."""
    CREATE_TASK = "create_task"
    UPDATE_TASK = "update_task"
    DELETE_TASK = "delete_task"
    QUERY_KNOWLEDGE = "query_knowledge"
    SEND_EMAIL = "send_email"
    SCHEDULE_MEETING = "schedule_meeting"
    GENERAL_CONVERSATION = "general_conversation"
    UNKNOWN = "unknown"

class IntentDetectionResult(BaseModel):
    """Schema for the result of an intent detection operation."""
    intent: Intent = Field(..., description="The detected intent.")
    confidence: float = Field(..., ge=0, le=1, description="The confidence score of the detection.")
    entities: dict = Field(default_factory=dict, description="Any extracted entities from the user query.")
    needs_confirmation: bool = Field(False, description="Indicates if the detected intent requires user confirmation.")
