from .schemas import Intent, IntentDetectionResult

class IntentDetector:
    """Detects user intent from a given text query."""

    def __init__(self):
        # In the future, this could load rules from a config file or database
        self.rules = {
            Intent.CREATE_TASK: ["create a task", "new task", "add a to-do"],
            Intent.SEND_EMAIL: ["send an email", "email to", "write an email"],
            Intent.SCHEDULE_MEETING: ["schedule a meeting", "setup a meeting", "meeting with"],
        }

    async def detect_intent(self, query: str) -> IntentDetectionResult:
        """Detects the intent of a user's query based on a set of rules."""
        query = query.lower()
        
        for intent, keywords in self.rules.items():
            for keyword in keywords:
                if keyword in query:
                    return IntentDetectionResult(
                        intent=intent,
                        confidence=0.9,  # High confidence for direct keyword match
                        entities={},
                        needs_confirmation=True
                    )
        
        return IntentDetectionResult(
            intent=Intent.GENERAL_CONVERSATION,
            confidence=0.5,
            entities={}
        )
