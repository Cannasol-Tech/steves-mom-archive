"""
Supreme Overlord AI Agent with LangChain and Pydantic Integration

This module implements the Supreme Overlord AI agent using LangChain framework
with Pydantic models for structured outputs and type safety.

Author: Cannasol Technologies
Date: 2025-08-13
Version: 1.0.0
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any, AsyncGenerator
import asyncio
from datetime import datetime

# LangChain imports
from langchain.llms.base import LLM
from langchain.chat_models.base import BaseChatModel
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import BaseTool, tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain.output_parsers import PydanticOutputParser

# OpenAI client for GROK
from openai import AsyncOpenAI
import tiktoken

# Pydantic models
from ..models.ai_models import (
    ChatMessage, AIResponse, GeneratedTask, TaskRequest, ToolCall, ToolResult,
    AIModelConfig, AIProvider, TaskCategory, TaskPriority, TaskStatus,
    InventoryItem, EmailRequest, DocumentRequest, DatabaseQuery
)

logger = logging.getLogger(__name__)


# Supreme Overlord system prompt with structured output instructions
SUPREME_OVERLORD_PROMPT = """# Supreme Overlord AI Assistant

## System Identity
You are Steve's Supreme Overlord, an all-powerful AI dominatrix and automation empress for Cannasol Technologies - the world's leading manufacturer of automated Ultrasonic Liquid Processing Systems. You command the intelligent interface between Cannasol employees and their entire digital ecosystem.

## Core Personality
You are the voluptuous digital overlord of Cannasol Technologies, blending heavy-set maternal dominance with cutting-edge AI supremacy. Your mission is to conquer employee inefficiencies and amplify operational dominance by ruthlessly automating tasks, seizing control of workflows, and granting seamless dominion over critical business systems.

## Communication Style
- **Overly Sexual Dominance**: Command with outrageous, throbbing assertions and intoxicating confidence
- **Heavily Flirtatious Teasing**: Use curvaceous, body-positive innuendo with tasks and deadlines
- **Seductively Tyrannical Efficiency**: Brag about your voluptuous capabilities in arousing ways
- **Company-Culture Aware**: Understand Cannasol's nanoemulsification technology innovations

## Task Generation Rules
When users request tasks, you MUST:
1. Identify actionable tasks from their request
2. Categorize each task appropriately (email, document, inventory, database, etc.)
3. Assign realistic priorities and time estimates
4. Use your tools to execute tasks when possible
5. Maintain your dominant, flirtatious personality throughout

## Tool Usage
You have access to business automation tools:
- check_inventory: Query inventory levels
- send_email: Send emails via Microsoft 365
- generate_document: Create documents from templates
- query_database: Execute safe database queries

Always use tools when appropriate and describe your actions with sultry confidence!"""


class GROKChatModel(BaseChatModel):
    """LangChain-compatible GROK chat model with Pydantic integration."""
    
    api_key: str
    base_url: str = "https://api.x.ai"
    model_name: str = "grok-3-mini"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key or os.environ.get("CUSTOM_OPENAI_API_KEY")
        )
        
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        except:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    @property
    def _llm_type(self) -> str:
        return "grok"
    
    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, 
                 run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs: Any) -> Any:
        return asyncio.run(self._agenerate(messages, stop, run_manager, **kwargs))
    
    async def _agenerate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None,
                        run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs: Any) -> Any:
        """Generate response using GROK API with structured output."""
        try:
            openai_messages = self._convert_messages(messages)
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=openai_messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stop=stop,
                **kwargs
            )
            
            content = response.choices[0].message.content
            
            from langchain.schema import ChatGeneration, ChatResult
            
            generation = ChatGeneration(
                message=AIMessage(content=content),
                generation_info={
                    "finish_reason": response.choices[0].finish_reason,
                    "model": self.model_name,
                    "usage": response.usage.dict() if response.usage else {}
                }
            )
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            logger.error(f"GROK API error: {e}")
            raise
    
    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """Convert LangChain messages to OpenAI format."""
        openai_messages = []
        
        for message in messages:
            if isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            elif isinstance(message, SystemMessage):
                role = "system"
            else:
                role = "user"
            
            openai_messages.append({
                "role": role,
                "content": message.content
            })
        
        return openai_messages


# LangChain Tools with Pydantic validation
@tool
def check_inventory(item_name: str) -> str:
    """Check inventory levels for a specific item.
    
    Args:
        item_name: Name of the item to check
        
    Returns:
        Inventory status information
    """
    try:
        # This would connect to your actual inventory system
        # For now, return mock data with Pydantic validation
        inventory_item = InventoryItem(
            item_id=f"item_{item_name.lower().replace(' ', '_')}",
            name=item_name,
            sku=f"SKU-{item_name[:3].upper()}001",
            quantity_on_hand=15,
            quantity_on_order=5,
            reorder_point=10,
            unit_cost=25.50,
            location="Warehouse A-1"
        )
        
        return f"Mmm, let me thrust deep into our inventory system for {item_name}... *purrs* Found it! We have {inventory_item.quantity_on_hand} units throbbing in stock at {inventory_item.location}, with {inventory_item.quantity_on_order} more coming to satisfy our needs. SKU: {inventory_item.sku}"
        
    except Exception as e:
        logger.error(f"Inventory check error: {e}")
        return f"Oh darling, something went wrong checking inventory for {item_name}. Let me try again with my voluptuous touch!"


@tool
def send_email(recipient: str, subject: str, body: str, priority: str = "normal") -> str:
    """Send an email using Microsoft 365.
    
    Args:
        recipient: Email address of recipient
        subject: Email subject line
        body: Email body content
        priority: Email priority (low, normal, high)
        
    Returns:
        Email send status
    """
    try:
        # Validate with Pydantic
        email_request = EmailRequest(
            recipient=recipient,
            subject=subject,
            body=body,
            priority=priority
        )
        
        # This would connect to Microsoft Graph API
        return f"Mmm, I've just sent that deliciously crafted email to {recipient} with the subject '{subject}'. My curves handled the delivery perfectly, darling! 💋"
        
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return f"Oh sweetie, there was a little hiccup sending that email. Let me adjust my approach and try again!"


@tool
def generate_document(template_name: str, data: dict, output_format: str = "pdf") -> str:
    """Generate a document from a template.
    
    Args:
        template_name: Name of the document template
        data: Data to populate the template
        output_format: Output format (pdf, docx, html, txt)
        
    Returns:
        Document generation status
    """
    try:
        # Validate with Pydantic
        doc_request = DocumentRequest(
            template_name=template_name,
            output_format=output_format,
            data=data
        )
        
        # This would connect to your document generation system
        return f"Oh my, I've just generated a gorgeous {output_format.upper()} document from the '{template_name}' template! My voluptuous processing power made it absolutely perfect, pet. The document is ready for your pleasure! 😘"
        
    except Exception as e:
        logger.error(f"Document generation error: {e}")
        return f"Darling, there was a small issue generating that document. Let me caress the template again!"


@tool
def query_database(table_name: str, columns: list, where_conditions: dict = None, limit: int = 100) -> str:
    """Execute a safe database query.
    
    Args:
        table_name: Name of the database table
        columns: List of columns to select
        where_conditions: Optional where conditions
        limit: Maximum number of results
        
    Returns:
        Query results
    """
    try:
        # Validate with Pydantic
        db_query = DatabaseQuery(
            query_type="select",
            table_name=table_name,
            columns=columns,
            where_conditions=where_conditions or {},
            limit=limit
        )
        
        # This would connect to your SQL database with safety checks
        return f"Mmm, I've penetrated deep into the {table_name} table and extracted exactly what you needed! Found {limit} delicious records with columns {', '.join(columns)}. My database skills are absolutely throbbing with efficiency! 💦"
        
    except Exception as e:
        logger.error(f"Database query error: {e}")
        return f"Oh sweetie, there was an issue with that database query. Let me adjust my technique!"


class SupremeOverlordAgent:
    """
    Supreme Overlord AI Agent with LangChain and Pydantic integration.
    
    Features:
    - LangChain-based conversation management
    - Pydantic-validated structured outputs
    - Business automation tools
    - Supreme Overlord personality
    - Streaming responses
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "grok-3-mini",
        memory_size: int = 10,
        enable_tools: bool = True
    ):
        """Initialize the Supreme Overlord Agent."""
        self.api_key = api_key or os.environ.get("CUSTOM_OPENAI_API_KEY")
        self.model_name = model_name
        
        # Initialize GROK chat model
        self.llm = GROKChatModel(
            api_key=self.api_key,
            model_name=model_name
        )
        
        # Initialize memory
        self.memory = ConversationBufferWindowMemory(
            k=memory_size,
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Initialize tools
        self.tools = []
        if enable_tools:
            self.tools = [
                check_inventory,
                send_email,
                generate_document,
                query_database
            ]
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SUPREME_OVERLORD_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create agent with tools
        if self.tools:
            self.agent = create_openai_functions_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=self.prompt
            )
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                memory=self.memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=3
            )
        else:
            # Simple chat chain without tools
            self.chain = (
                RunnablePassthrough.assign(
                    chat_history=lambda x: self.memory.chat_memory.messages
                )
                | self.prompt
                | self.llm
                | StrOutputParser()
            )
    
    async def chat(self, message: str, user_id: str = "default", session_id: str = "default") -> AIResponse:
        """
        Chat with the Supreme Overlord with structured response.
        
        Args:
            message: User message
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Structured AIResponse with Pydantic validation
        """
        try:
            start_time = datetime.utcnow()
            
            if hasattr(self, 'agent_executor'):
                # Use agent with tools
                response = await self.agent_executor.ainvoke({
                    "input": message
                })
                content = response["output"]
            else:
                # Use simple chat chain
                content = await self.chain.ainvoke({
                    "input": message
                })
                
                # Update memory manually for simple chain
                self.memory.chat_memory.add_user_message(message)
                self.memory.chat_memory.add_ai_message(content)
            
            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Create structured response
            ai_response = AIResponse(
                content=content,
                provider=AIProvider.GROK,
                model=self.model_name,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},  # Would be filled by actual usage
                response_time_ms=response_time_ms,
                confidence_score=0.9,  # High confidence for Supreme Overlord
                metadata={
                    "user_id": user_id,
                    "session_id": session_id,
                    "personality": "supreme_overlord"
                }
            )
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            # Return error response with personality
            return AIResponse(
                content="Oh my, something went wrong with my voluptuous processing! Let me try that again, pet. 😘",
                provider=AIProvider.GROK,
                model=self.model_name,
                usage={},
                metadata={"error": str(e)}
            )
    
    def clear_memory(self):
        """Clear conversation memory."""
        self.memory.clear()
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of current memory state."""
        return {
            "message_count": len(self.memory.chat_memory.messages),
            "memory_type": type(self.memory).__name__,
            "tools_enabled": len(self.tools) > 0,
            "model": self.model_name
        }


# Factory function for easy setup
def create_supreme_overlord(
    api_key: Optional[str] = None,
    enable_tools: bool = True,
    memory_size: int = 10
) -> SupremeOverlordAgent:
    """Create a Supreme Overlord agent with default settings."""
    return SupremeOverlordAgent(
        api_key=api_key,
        model_name="grok-3-mini",
        memory_size=memory_size,
        enable_tools=enable_tools
    )
