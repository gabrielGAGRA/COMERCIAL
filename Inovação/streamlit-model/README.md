# 🤖 ChatGPT Interface - Streamlit Version

Uma interface Streamlit moderna para interagir com OpenAI Assistants especializados.

## ✨ Características

- 🎯 **Dois Assistants Especializados**
  - 📋 **Organizador de Atas**: Estrutura atas profissionais
  - 💼 **Criador de Propostas**: Desenvolve propostas comerciais
- 🔄 **Troca de Assistant**: Mude entre assistants facilmente
- 💬 **Interface Responsiva**: Design moderno do Streamlit
- 🚀 **Deploy Fácil**: Pronto para Streamlit Cloud

## 🚀 Deploy no Streamlit Cloud

### 1. Preparação
```bash
git clone <seu-repositorio>
cd streamlit-chatgpt-interface
```

### 2. Configure os Secrets
No Streamlit Cloud, adicione em **Settings > Secrets**:
```toml
OPENAI_API_KEY = "sk-proj-sua-chave-aqui"
```

### 3. Deploy
- Conecte seu repositório ao Streamlit Cloud
- A aplicação será automaticamente deployada
- Acesse via URL fornecida pelo Streamlit

## 🔧 Desenvolvimento Local

### 1. Instale Dependências
```bash
pip install -r requirements.txt
```

### 2. Configure Secrets Localmente
Crie `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "sua-chave-aqui"
```

### 3. Execute
```bash
streamlit run streamlit_app.py
```

## ⚙️ Configuração dos Assistants

Atualize os IDs dos assistants no código:

```python
AVAILABLE_ASSISTANTS = {
    "organizador_atas": {
        "id": "asst_SEU_ID_AQUI",  # ← Seu ID do assistant
        "name": "Organizador de Atas",
        # ...
    },
    # ...
}
```

### Como Obter IDs dos Assistants:
1. Acesse [OpenAI Platform](https://platform.openai.com/assistants)
2. Crie ou selecione um assistant
3. O ID aparece como: `asst_xxxxxxxxxxxxxxxxxxxxx`

## 🎯 Funcionalidades

### Chat Interface
- Conversa natural com assistants especializados
- Histórico de mensagens mantido na sessão
- Troca de assistant preserva contexto quando possível

### Sidebar Controls
- Seleção de assistant
- Nova conversa
- Limpar histórico
- Informações da sessão

### Assistants Disponíveis

**📋 Organizador de Atas**
- Especialista em estruturar reuniões
- Organiza pontos discutidos
- Cria atas profissionais

**💼 Criador de Propostas**
- Desenvolve propostas comerciais
- Linguagem persuasiva
- Estrutura profissional

## 🔐 Segurança

- Chaves API armazenadas em Streamlit Secrets
- Não exposição de credenciais no código
- Validação de entrada do usuário

## 📱 Responsividade

- Interface adaptável a diferentes telas
- Sidebar colapsável em mobile
- Chat otimizado para todos os dispositivos

## 🚨 Troubleshooting

**Erro de API Key:**
- Verifique se a chave está configurada corretamente
- Confirme que a chave tem créditos na OpenAI
- Teste a chave manualmente na interface

**Assistant não responde:**
- Verifique os IDs dos assistants
- Confirme que os assistants existem na sua conta OpenAI
- Tente criar uma nova conversa

**Deploy falha:**
- Verifique o arquivo `requirements.txt`
- Confirme que todos os secrets estão configurados
- Verifique os logs do Streamlit Cloud

## 📄 Estrutura do Projeto

```
streamlit-chatgpt-interface/
├── streamlit_app.py          # Aplicação principal
├── requirements.txt          # Dependências Python
├── .streamlit/
│   ├── config.toml          # Configuração do Streamlit
│   └── secrets.toml         # Secrets locais (não commitado)
└── README.md                # Este arquivo
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

MIT License - veja LICENSE para detalhes.

---

**Desenvolvido com ❤️ usando Streamlit e OpenAI Assistants**