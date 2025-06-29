#!/usr/bin/env python3
"""
Modern ChatGPT Interface Application
Improved version with modern dependencies and better architecture
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.app import app
from server.website import Website
from server.backend import ChatbotBackend
from server.config import AppConfig, OpenAIConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("chatbot.log"), logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def load_config() -> Dict[str, Any]:
    """Load configuration from file and environment variables"""
    config_file = Path("config.json")

    if config_file.exists():
        import json

        try:
            with open(config_file, "r") as f:
                config = json.load(f)
            logger.info("Configuration loaded from config.json")
            return config
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Failed to load config.json: {e}")

    # Default configuration
    default_config = {
        "site_config": {"host": "127.0.0.1", "port": 1338, "debug": False},
        "openai_key": os.getenv("OPENAI_API_KEY", ""),
        "openai_api_base": os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
        "timeout": 30,
    }

    logger.info("Using default configuration")
    return default_config


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration"""
    if not config.get("openai_key"):
        logger.error(
            "OpenAI API key is required. Set OPENAI_API_KEY environment variable or add it to config.json"
        )
        return False

    return True


def setup_routes(app, config: Dict[str, Any]):
    """Setup all application routes"""
    # Website routes
    website = Website(app)
    for route, route_config in website.routes.items():
        app.add_url_rule(
            route,
            endpoint=f"website_{route.replace('/', '_').replace('<', '').replace('>', '')}",
            view_func=route_config["function"],
            methods=route_config["methods"],
        )

    # Backend API routes
    backend = ChatbotBackend(app, config)
    for route, route_config in backend.routes.items():
        app.add_url_rule(
            route,
            endpoint=f"api_{route.replace('/', '_').replace('<', '').replace('>', '')}",
            view_func=route_config["function"],
            methods=route_config["methods"],
        )

    logger.info("All routes configured successfully")


def main():
    """Main application entry point"""
    try:
        # Load and validate configuration
        config = load_config()

        if not validate_config(config):
            sys.exit(1)

        # Setup routes
        setup_routes(app, config)

        # Get server configuration
        site_config = config.get("site_config", {})
        host = site_config.get("host", "127.0.0.1")
        port = site_config.get("port", 1338)
        debug = site_config.get("debug", False)

        # Print startup information
        logger.info(f"Starting ChatGPT Interface Server")
        logger.info(f"Server: http://{host}:{port}")
        logger.info(f"Debug mode: {debug}")

        if config.get("openai_key"):
            logger.info("OpenAI API key configured")
        else:
            logger.warning(
                "OpenAI API key not configured - server will not work properly"
            )

        # Start the server
        app.run(host=host, port=port, debug=debug, threaded=True)

    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)
    finally:
        logger.info("Server stopped")


if __name__ == "__main__":
    main()
