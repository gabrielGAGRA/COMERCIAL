from typing import Dict, List, Any, Optional, Generator
import json
import logging
from datetime import datetime
from flask import request, Response, jsonify
import openai
from openai import OpenAI
import os
import time

from .config import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL,
    OpenAIConfig,
    AVAILABLE_ASSISTANTS,
    DEFAULT_ASSISTANT,
    AssistantConfig,
)

logger = logging.getLogger(__name__)


class ChatbotBackend:
    """Modern ChatGPT backend using OpenAI Assistants API"""

    def __init__(self, app, config: Dict[str, Any]) -> None:
        self.app = app
        self.config = OpenAIConfig(
            api_key=config.get("openai_key", ""),
            api_base=config.get("openai_api_base", "https://api.openai.com/v1"),
            timeout=config.get("timeout", 30),
        )

        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base,
            timeout=self.config.timeout,
        )

        self.routes = {
            "/api/v1/assistant/chat": {
                "function": self._assistant_chat,
                "methods": ["POST"],
            },
            "/api/v1/models": {"function": self._get_models, "methods": ["GET"]},
            "/api/v1/assistants": {
                "function": self._get_assistants,
                "methods": ["GET"],
            },
            "/api/v1/health": {"function": self._health_check, "methods": ["GET"]},
        }

    def _validate_assistant_request(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate incoming assistant request data"""
        if not data:
            return False, "Request body is required"

        if "message" not in data or not data["message"].strip():
            return False, "Message is required and cannot be empty"

        assistant_key = data.get("assistant", DEFAULT_ASSISTANT)
        if assistant_key not in AVAILABLE_ASSISTANTS:
            return (
                False,
                f'Assistant "{assistant_key}" not available. Available assistants: {list(AVAILABLE_ASSISTANTS.keys())}',
            )

        return True, ""

    def _get_models(self):
        """Return available models"""
        models_info = []
        for model_id, model_info in AVAILABLE_MODELS.items():
            models_info.append(
                {
                    "id": model_info.id,
                    "name": model_info.name,
                    "context_window": model_info.context_window,
                    "max_tokens": model_info.max_tokens,
                }
            )

        return jsonify({"models": models_info, "default_model": DEFAULT_MODEL})

    def _get_assistants(self):
        """Return available assistants"""
        assistants_info = []
        for assistant_id, assistant_info in AVAILABLE_ASSISTANTS.items():
            assistants_info.append(
                {
                    "id": assistant_id,
                    "name": assistant_info.name,
                    "description": assistant_info.description,
                    "openai_id": assistant_info.id,
                }
            )

        return jsonify(
            {"assistants": assistants_info, "default_assistant": DEFAULT_ASSISTANT}
        )

    def _assistant_chat(self):
        """Handle assistant chat using OpenAI Assistants API"""
        try:
            data = request.get_json()

            # Validate request
            is_valid, error_message = self._validate_assistant_request(data)
            if not is_valid:
                return jsonify({"error": error_message}), 400

            message = data["message"]
            assistant_key = data.get("assistant", DEFAULT_ASSISTANT)
            conversation_history = data.get("conversation_history", [])
            thread_id = data.get("thread_id", None)

            assistant_config = AVAILABLE_ASSISTANTS[assistant_key]

            logger.info(
                f"Processing assistant chat - Assistant: {assistant_config.name}, Message length: {len(message)}"
            )

            try:
                # Create or use existing thread
                if not thread_id:
                    thread = self.client.beta.threads.create()
                    thread_id = thread.id
                    logger.info(f"Created new thread: {thread_id}")

                    # Add conversation history to thread if provided
                    if conversation_history:
                        logger.info(
                            f"Adding {len(conversation_history)} messages to thread history"
                        )
                        for msg in conversation_history[-10:]:  # Last 10 messages
                            if (
                                isinstance(msg, dict)
                                and "role" in msg
                                and "content" in msg
                                and msg["role"] in ["user", "assistant"]
                            ):
                                self.client.beta.threads.messages.create(
                                    thread_id=thread_id,
                                    role=msg["role"],
                                    content=msg["content"],
                                )
                else:
                    logger.info(f"Using existing thread: {thread_id}")

                # Add current user message to thread
                self.client.beta.threads.messages.create(
                    thread_id=thread_id, role="user", content=message
                )

                # Create and run assistant (without additional instructions)
                run = self.client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=assistant_config.id,
                )

                logger.info(f"Started assistant run: {run.id}")

                # Stream response
                return Response(
                    self._stream_assistant_response(thread_id, run.id),
                    mimetype="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type",
                    },
                )

            except openai.APIError as e:
                logger.error(f"OpenAI Assistant API error: {e}")
                return jsonify({"error": f"Assistant API Error: {str(e)}"}), 500

        except Exception as e:
            logger.error(f"Error in assistant_chat: {e}")
            return jsonify({"error": f"Internal server error: {str(e)}"}), 500

    def _stream_assistant_response(
        self, thread_id: str, run_id: str
    ) -> Generator[str, None, None]:
        """Stream assistant response"""
        try:
            max_polling_time = 300  # 5 minutes max
            polling_start = time.time()

            # Poll for run completion
            while True:
                # Check timeout
                if time.time() - polling_start > max_polling_time:
                    logger.error(f"Assistant run {run_id} timed out")
                    yield f"data: {json.dumps({'error': 'Assistant response timed out', 'done': True})}\n\n"
                    break

                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id, run_id=run_id
                )

                logger.debug(f"Run status: {run.status}")

                if run.status == "completed":
                    # Get the latest assistant message
                    messages = self.client.beta.threads.messages.list(
                        thread_id=thread_id, order="desc", limit=1
                    )

                    if messages.data and messages.data[0].role == "assistant":
                        message = messages.data[0]
                        if message.content and message.content[0].type == "text":
                            content = message.content[0].text.value

                            # Stream the content in chunks for better UX
                            words = content.split(" ")
                            for i, word in enumerate(words):
                                if i > 0:
                                    word = " " + word
                                yield f"data: {json.dumps({'content': word, 'done': False, 'thread_id': thread_id})}\n\n"
                                time.sleep(0.03)  # Small delay for streaming effect

                    # Send completion signal
                    yield f"data: {json.dumps({'content': '', 'done': True, 'thread_id': thread_id})}\n\n"
                    logger.info(f"Assistant run {run_id} completed successfully")
                    break

                elif run.status == "failed":
                    error_msg = f"Assistant run failed: {run.last_error.message if run.last_error else 'Unknown error'}"
                    logger.error(error_msg)
                    yield f"data: {json.dumps({'error': error_msg, 'done': True})}\n\n"
                    break

                elif run.status in ["cancelled", "expired"]:
                    error_msg = f"Assistant run {run.status}"
                    logger.warning(error_msg)
                    yield f"data: {json.dumps({'error': error_msg, 'done': True})}\n\n"
                    break

                elif run.status == "requires_action":
                    # Handle function calls if needed in the future
                    logger.warning(
                        "Assistant requires action - function calls not implemented"
                    )
                    yield f"data: {json.dumps({'error': 'Assistant requires action (not supported)', 'done': True})}\n\n"
                    break

                else:
                    # Still running (queued, in_progress), wait a bit
                    time.sleep(1)

        except Exception as e:
            logger.error(f"Error streaming assistant response: {e}")
            yield f"data: {json.dumps({'error': f'Streaming error: {str(e)}', 'done': True})}\n\n"

    def _health_check(self):
        """Health check endpoint"""
        try:
            # Test OpenAI connection by listing assistants
            assistants = self.client.beta.assistants.list(limit=1)
            api_status = "healthy"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            api_status = "unhealthy"

        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "openai_api_status": api_status,
                "available_assistants": list(AVAILABLE_ASSISTANTS.keys()),
                "default_assistant": DEFAULT_ASSISTANT,
            }
        )


# Backward compatibility alias
Backend_Api = ChatbotBackend
