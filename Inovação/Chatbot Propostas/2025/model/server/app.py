from flask import Flask, request
from flask_cors import CORS
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def create_app():
    """Application factory pattern for Flask app"""
    # Get absolute path to template folder
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_folder = os.path.join(current_dir, "client", "html")
    
    app = Flask(__name__, template_folder=template_folder)

    # Enable CORS for all routes
    CORS(app, origins=["*"])

    # Configure app
    app.config["SECRET_KEY"] = "your-secret-key-change-in-production"
    app.config["JSON_SORT_KEYS"] = False

    # Add request logging
    @app.before_request
    def log_request_info():
        logger.info(f"Request: {datetime.now()} - {request.method} {request.url}")

    @app.after_request
    def log_response_info(response):
        logger.info(f"Response: {response.status_code}")
        return response

    return app


app = create_app()
