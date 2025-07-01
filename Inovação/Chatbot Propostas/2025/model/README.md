# 🤖 Modern ChatGPT Interface

Uma interface moderna e responsiva para interagir com OpenAI Assistants, especialmente projetada para **Organizador de Atas** e **Criador de Propostas Comerciais**.

## ✨ Características

- 🎯 **Dois Assistants Especializados**
  - **Organizador de Atas**: Estrutura atas profissionais
  - **Criador de Propostas**: Desenvolve propostas comerciais persuasivas
- 🔄 **Troca de Assistant**: Mude entre assistants mantendo o contexto
- 💬 **Chat em Tempo Real**: Interface responsiva com streaming
- 🎨 **Interface Moderna**: Design limpo e profissional
- � **Responsiva**: Funciona perfeitamente em mobile e desktop

## 🚀 Instalação Rápida

### 1. Clone e Configure
```bash
git clone <seu-repositorio>
cd "Chatbot Propostas/2025/model"
```

### 2. Instale Dependências
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copie o arquivo de exemplo
copy .env.example .env

# Edite o .env e adicione sua chave da OpenAI
OPENAI_API_KEY=sk-proj-...
```

### 4. Configure os Assistants
Edite o arquivo `server/config.py` e atualize os IDs dos seus assistants:

```python
AVAILABLE_ASSISTANTS: Dict[str, AssistantConfig] = {
    "organizador_atas": AssistantConfig(
        id="asst_SEU_ID_AQUI",  # ← Coloque o ID do seu assistant
        name="Organizador de Atas",
        description="Especialista em organizar e estruturar atas de reunião",
    ),
    "criador_propostas": AssistantConfig(
        id="asst_SEU_ID_AQUI",  # ← Coloque o ID do seu assistant
        name="Criador de Propostas Comerciais", 
        description="Especialista em criar propostas comerciais persuasivas",
    ),
}
```

### 5. Execute
```bash
python run.py
```

Acesse: **http://127.0.0.1:1338**

## ⚙️ Configuração

### Variáveis de Ambiente (.env)

| Variável | Descrição | Padrão |
|----------|-----------|---------|
| `OPENAI_API_KEY` | **Obrigatório** - Sua chave da OpenAI | - |
| `HOST` | Endereço do servidor | `127.0.0.1` |
| `PORT` | Porta do servidor | `1338` |
| `DEBUG` | Modo debug (`true`/`false`) | `false` |
| `TIMEOUT` | Timeout da API em segundos | `30` |

### Como Obter IDs dos Assistants

1. Acesse [OpenAI Platform](https://platform.openai.com/assistants)
2. Crie ou selecione um assistant
3. O ID aparece na URL: `asst_xxxxxxxxxxxxxxxxxxxxx`
4. Copie e cole em `server/config.py`

## 🎯 Como Usar

1. **Escolha o Assistant**: Use o dropdown para selecionar entre:
   - 📋 **Organizador de Atas**
   - 💼 **Criador de Propostas**

2. **Digite sua Mensagem**: Use a caixa de texto na parte inferior

3. **Envie**: Clique em "Enviar" ou pressione Enter

4. **Troque de Assistant**: O contexto é mantido ao trocar assistants

## 🏗️ Arquitetura

```
├── server/
│   ├── app.py          # Flask app factory
│   ├── backend.py      # OpenAI Assistants API
│   ├── website.py      # Routes e templates
│   └── config.py       # Configurações
├── client/
│   ├── html/           # Templates HTML
│   ├── css/            # Estilos modernos
│   └── js/             # JavaScript interativo
├── run.py              # Entry point
├── requirements.txt    # Dependências Python
└── .env               # Configurações (não commitado)
```

## � Desenvolvimento

### Logs
Os logs são salvos em `chatbot.log` e exibidos no console.

### Debug Mode
```bash
# No .env
DEBUG=true
```

### Health Check
```bash
curl http://127.0.0.1:1338/api/v1/health
```

## 📝 APIs Disponíveis

- `POST /api/v1/assistant/chat` - Chat com assistant
- `GET /api/v1/assistants` - Lista assistants disponíveis
- `GET /api/v1/models` - Lista modelos disponíveis
- `GET /api/v1/health` - Status da aplicação

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## � Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

---

**Desenvolvido com ❤️ para otimizar reuniões e propostas comerciais**