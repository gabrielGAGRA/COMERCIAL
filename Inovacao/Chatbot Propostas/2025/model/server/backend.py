from typing import Dict, List, Any, Optional, Generator
import json
import logging
from datetime import datetime
from flask import request, Response, stream_template, jsonify
import openai
from openai import OpenAI
import os
import time

from .config import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL,
    SYSTEM_MESSAGE,
    special_instructions,
    OpenAIConfig,
)

logger = logging.getLogger(__name__)


class ChatbotBackend:
    """Modern ChatGPT backend using OpenAI's official Python client"""

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
            "/api/v1/chat/completions": {
                "function": self._chat_completions,
                "methods": ["POST"],
            },
            "/api/v1/models": {"function": self._get_models, "methods": ["GET"]},
            "/api/v1/health": {"function": self._health_check, "methods": ["GET"]},
        }

    def _validate_request(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate incoming request data"""
        if not data:
            return False, "Request body is required"

        if "message" not in data or not data["message"].strip():
            return False, "Message is required and cannot be empty"

        model = data.get("model", DEFAULT_MODEL)
        if model not in AVAILABLE_MODELS:
            return (
                False,
                f"Model '{model}' is not available. Available models: {list(AVAILABLE_MODELS.keys())}",
            )

        return True, ""

    def _prepare_messages(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        instruction_type: str = "default",
    ) -> List[Dict[str, str]]:
        """Prepare messages for OpenAI API"""
        messages = [{"role": "system", "content": SYSTEM_MESSAGE}]

        # Add special instructions if specified
        if instruction_type in special_instructions:
            messages.extend(special_instructions[instruction_type])

        # Add conversation history if provided
        if conversation_history:
            # Validate and add conversation history
            for msg in conversation_history[-10:]:  # Limit to last 10 messages
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    if msg["role"] in ["user", "assistant"]:
                        messages.append(msg)

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    def _stream_chat_response(
        self, messages: List[Dict], model: str
    ) -> Generator[str, None, None]:
        """Generate streaming chat response"""
        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                max_tokens=AVAILABLE_MODELS[model].max_tokens,
                temperature=0.7,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    # Format as Server-Sent Events
                    yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"

            # Send completion signal
            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            yield f"data: {json.dumps({'error': f'API Error: {str(e)}', 'done': True})}\n\n"
        except Exception as e:
            logger.error(f"Unexpected error in stream_chat_response: {e}")
            yield f"data: {json.dumps({'error': f'Unexpected error: {str(e)}', 'done': True})}\n\n"

    def _chat_completions(self):
        """Handle chat completions endpoint"""
        try:
            data = request.get_json()

            # Validate request
            is_valid, error_message = self._validate_request(data)
            if not is_valid:
                return jsonify({"error": error_message}), 400

            message = data["message"]
            model = data.get("model", DEFAULT_MODEL)
            conversation_history = data.get("conversation_history", [])
            instruction_type = data.get("instruction_type", "default")
            stream = data.get("stream", True)

            logger.info(
                f"Processing chat request - Model: {model}, Message length: {len(message)}"
            )

            # Prepare messages
            messages = self._prepare_messages(
                message, conversation_history, instruction_type
            )

            if stream:
                # Return streaming response
                return Response(
                    self._stream_chat_response(messages, model),
                    mimetype="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type",
                    },
                )
            else:
                # Return single response
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=AVAILABLE_MODELS[model].max_tokens,
                        temperature=0.7,
                    )

                    return jsonify(
                        {
                            "message": response.choices[0].message.content,
                            "model": model,
                            "usage": {
                                "prompt_tokens": response.usage.prompt_tokens,
                                "completion_tokens": response.usage.completion_tokens,
                                "total_tokens": response.usage.total_tokens,
                            },
                        }
                    )

                except openai.APIError as e:
                    logger.error(f"OpenAI API error: {e}")
                    return jsonify({"error": f"API Error: {str(e)}"}), 500

        except Exception as e:
            logger.error(f"Error in chat_completions: {e}")
            return jsonify({"error": f"Internal server error: {str(e)}"}), 500

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

    def _health_check(self):
        """Health check endpoint"""
        try:
            # Test OpenAI connection
            models = self.client.models.list()
            api_status = "healthy"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            api_status = "unhealthy"

        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "openai_api_status": api_status,
                "available_models": list(AVAILABLE_MODELS.keys()),
            }
        )


# Backward compatibility alias
Backend_Api = ChatbotBackend
