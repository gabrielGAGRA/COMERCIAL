from typing import Dict, List
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ChatModel(BaseModel):
    id: str
    name: str
    context_window: int
    max_tokens: int


class AppConfig(BaseModel):
    debug: bool = Field(default=False)
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=1338)
    cors_origins: List[str] = Field(default=["*"])


class OpenAIConfig(BaseModel):
    api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    api_base: str = Field(default="https://api.openai.com/v1")
    timeout: int = Field(default=30)


# Available ChatGPT models
AVAILABLE_MODELS: Dict[str, ChatModel] = {
    "gpt-4o": ChatModel(
        id="gpt-4o", name="GPT-4o", context_window=128000, max_tokens=4096
    ),
    "gpt-4o-mini": ChatModel(
        id="gpt-4o-mini", name="GPT-4o Mini", context_window=128000, max_tokens=16384
    ),
    "o3-mini": ChatModel(
        id="o3-mini", name="O3 Mini", context_window=128000, max_tokens=65536
    ),
}

# Default model
DEFAULT_MODEL = "gpt-4o"

# System message for the chatbot
SYSTEM_MESSAGE = """You are a helpful AI assistant. You provide accurate, helpful, and detailed responses to user queries. You can:
- Answer questions on a wide variety of topics
- Help with problem-solving and analysis
- Assist with creative tasks
- Provide explanations and tutorials
- Help with coding and technical issues

Always be polite, professional, and aim to be as helpful as possible."""

# Rate limiting configuration
RATE_LIMIT_CONFIG = {"requests_per_minute": 60, "requests_per_hour": 1000}

special_instructions = {
    "default": [],
    "creative": [
        {
            "role": "system",
            "content": "Be more creative and imaginative in your responses.",
        }
    ],
    "technical": [
        {
            "role": "system",
            "content": "Focus on providing detailed technical explanations.",
        }
    ],
    "concise": [
        {"role": "system", "content": "Keep your responses concise and to the point."}
    ],
}
