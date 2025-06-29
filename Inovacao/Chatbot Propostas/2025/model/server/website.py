from flask import render_template, send_file, redirect, jsonify, request
from typing import Dict, Any
import logging
import os
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class Website:
    """Improved website handler with better error handling and logging"""

    def __init__(self, app) -> None:
        self.app = app
        self.routes = {
            "/": {"function": self._home, "methods": ["GET"]},
            "/chat": {"function": self._new_chat, "methods": ["GET"]},
            "/chat/": {"function": self._new_chat, "methods": ["GET"]},
            "/chat/<conversation_id>": {
                "function": self._chat_with_id,
                "methods": ["GET"],
            },
            "/assets/<folder>/<file>": {
                "function": self._serve_assets,
                "methods": ["GET"],
            },
            "/api/info": {"function": self._app_info, "methods": ["GET"]},
        }

    def _home(self):
        """Redirect home to chat"""
        return redirect("/chat")

    def _new_chat(self):
        """Create a new chat session"""
        try:
            chat_id = self._generate_chat_id()
            logger.info(f"Creating new chat session: {chat_id}")
            return render_template("index.html", chat_id=chat_id)
        except Exception as e:
            logger.error(f"Error creating new chat: {e}")
            return render_template("error.html", error="Failed to create new chat"), 500

    def _chat_with_id(self, conversation_id: str):
        """Load existing chat session"""
        try:
            # Validate conversation ID format
            if not self._is_valid_chat_id(conversation_id):
                logger.warning(f"Invalid chat ID format: {conversation_id}")
                return redirect("/chat")

            logger.info(f"Loading chat session: {conversation_id}")
            return render_template("index.html", chat_id=conversation_id)
        except Exception as e:
            logger.error(f"Error loading chat {conversation_id}: {e}")
            return render_template("error.html", error="Failed to load chat"), 500

    def _serve_assets(self, folder: str, file: str):
        """Serve static assets with proper error handling"""
        try:
            asset_path = f"./../client/{folder}/{file}"

            # Security check - prevent directory traversal
            if ".." in folder or ".." in file:
                logger.warning(f"Directory traversal attempt: {folder}/{file}")
                return "Access denied", 403

            # Check if file exists
            if not os.path.exists(asset_path):
                logger.warning(f"Asset not found: {asset_path}")
                return "File not found", 404

            # Determine MIME type based on file extension
            mime_type = self._get_mime_type(file)

            return send_file(asset_path, as_attachment=False, mimetype=mime_type)

        except Exception as e:
            logger.error(f"Error serving asset {folder}/{file}: {e}")
            return "Internal server error", 500

    def _app_info(self):
        """Provide application information"""
        return jsonify(
            {
                "name": "ChatGPT Interface",
                "version": "2.0.0",
                "description": "Modern ChatGPT interface with improved backend",
                "timestamp": datetime.now().isoformat(),
                "features": [
                    "Modern OpenAI API integration",
                    "Streaming responses",
                    "Multiple model support",
                    "Conversation history",
                    "Responsive design",
                ],
            }
        )

    def _generate_chat_id(self) -> str:
        """Generate a unique chat ID"""
        return str(uuid.uuid4())

    def _is_valid_chat_id(self, chat_id: str) -> bool:
        """Validate chat ID format"""
        try:
            uuid.UUID(chat_id)
            return True
        except ValueError:
            # Also accept the old format for backward compatibility
            return "-" in chat_id and len(chat_id.split("-")) >= 4

    def _get_mime_type(self, filename: str) -> str:
        """Determine MIME type based on file extension"""
        extension = filename.lower().split(".")[-1]
        mime_types = {
            "css": "text/css",
            "js": "application/javascript",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "svg": "image/svg+xml",
            "ico": "image/x-icon",
            "woff": "font/woff",
            "woff2": "font/woff2",
            "ttf": "font/ttf",
            "eot": "application/vnd.ms-fontobject",
        }
        return mime_types.get(extension, "application/octet-stream")
