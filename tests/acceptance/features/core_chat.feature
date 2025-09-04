@skip @core @acceptance
Feature: Core Chat Interface
  As a Cannasol employee
  I want to chat with Steve's Mom and manage conversations
  So that I can get AI assistance efficiently

  @FR-1.1
  Scenario: FR-1.1 AI Model Integration baseline routing
    Given the system is configured with GROK as default provider
    When I send a general knowledge prompt
    Then the request is routed to GROK and a valid response is returned

  @FR-1.2
  Scenario: FR-1.2 Conversation management basics
    Given I have an active conversation
    When I send a follow-up message
    Then the assistant maintains context across the turn

  @FR-1.3
  Scenario: FR-1.3 NLP intent recognition for task generation
    Given a user message with an actionable request
    When the NLP layer processes the message
    Then an intent and entities are extracted for downstream task generation
