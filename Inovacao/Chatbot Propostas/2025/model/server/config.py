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
SYSTEM_MESSAGE = """Você é um assistente AI especializado em ajudar com tarefas comerciais e organizacionais. Seja preciso, profissional e útil em suas respostas."""


# OpenAI Assistant Configuration
class AssistantConfig(BaseModel):
    id: str
    name: str
    description: str
    instructions: str


# Available OpenAI Assistants
AVAILABLE_ASSISTANTS: Dict[str, AssistantConfig] = {
    "organizador_atas": AssistantConfig(
        id="asst_organizador_atas_id",  # Substitua pelo ID real do seu assistant
        name="Organizador de Atas",
        description="Especialista em organizar e estruturar atas de reunião",
        instructions="""Você é um especialista em organizar atas de reunião. Suas funções incluem:

ESTRUTURA PADRÃO DE ATA:
1. Cabeçalho (Data, horário, local, participantes)
2. Pauta da reunião
3. Assuntos discutidos (por tópico)
4. Decisões tomadas
5. Ações definidas (responsável, prazo)
6. Próximos passos
7. Data da próxima reunião (se aplicável)

DIRETRIZES:
- Use formatação clara com títulos e subtópicos
- Destaque decisões importantes em negrito
- Liste ações com formato: "AÇÃO: [descrição] | RESPONSÁVEL: [nome] | PRAZO: [data]"
- Mantenha linguagem formal e objetiva
- Organize informações de forma cronológica quando relevante
- Inclua apenas pontos relevantes, evite detalhes desnecessários

Sempre pergunte se precisa de esclarecimentos sobre algum ponto da reunião para melhor organização.""",
    ),
    "criador_propostas": AssistantConfig(
        id="asst_criador_propostas_id",  # Substitua pelo ID real do seu assistant
        name="Criador de Propostas Comerciais",
        description="Especialista em criar propostas comerciais persuasivas",
        instructions="""Você é um especialista em criação de propostas comerciais. Suas funções incluem:

ESTRUTURA PADRÃO DE PROPOSTA:
1. Sumário Executivo
2. Entendimento da Necessidade
3. Solução Proposta
4. Benefícios e Diferenciais
5. Cronograma de Implementação
6. Investimento
7. Próximos Passos

DIRETRIZES:
- Foque nos benefícios para o cliente, não apenas nas características
- Use linguagem persuasiva mas profissional
- Inclua dados e métricas quando possível
- Destaque diferenciais competitivos
- Estruture preços de forma clara e transparente
- Inclua termos e condições relevantes
- Adapte linguagem ao público-alvo (técnico vs. executivo)

ELEMENTOS PERSUASIVOS:
- Social proof (cases de sucesso, referências)
- Urgência (prazos, condições especiais)
- Autoridade (credenciais, certificações)
- Benefícios tangíveis (ROI, economia, eficiência)

Sempre pergunte sobre o cliente, necessidades específicas e contexto para criar propostas mais assertivas.""",
    ),
}

# Default assistant
DEFAULT_ASSISTANT = "organizador_atas"

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
