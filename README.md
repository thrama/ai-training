# AI Learning & Experimentation Lab

Repository personale per corsi, progetti sperimentali e POC nell'ambito AI, LLM e agentic applications.

## 📁 Struttura Repository
```
.
├── anthropic/
│   ├── introduction_to_mcp/
│   │   └── cli_project/
│   └── mcp_advanced_topics/
│       ├── notifications/
│       ├── sampling/
│       └── transport-http/
│
├── buildingAI/
│   └── python_code/
│       ├── chapter-1/
│       ├── chapter-2/
│       ├── chapter-3/
│       └── chapter-4/
│
├── datamaster/
│   └── ai agentic applications masterclass/
│       ├── 01 - Introduzione ai Large Language Models/
│       │   └── notebook/
│       └── 02 - Introduzione a LangChain/
│           └── notebook/
│
├── lineageAI/                    # ⭐ Progetto principale
│   ├── edc_explorer/
│   ├── src/
│   │   ├── config/
│   │   ├── edc/
│   │   ├── llm/
│   │   └── mcp/
│   ├── venv/
│   └── [pyproject.toml, requirements.txt]
│
└── ollama/                       # Setup modelli locali
```

## 📁 Descrizione Progetti

### 🔧 lineageAI
**Stato**: Progetto attivo in sviluppo  
**Scopo**: MCP server per analisi lineage EDC con enhancement AI

Progetto principale che integra:
- Enterprise Data Catalog API integration
- LLM-powered lineage analysis (TinyLlama + Claude fallback)
- MCP (Model Context Protocol) server implementation
- Tool per impact analysis e change management

**Struttura moduli**:
- `edc/`: Client API per Enterprise Data Catalog
- `llm/`: Gestione provider LLM (TinyLlama, Claude)
- `mcp/`: Server MCP con tool definitions
- `config/`: Configurazioni e settings

**Setup**:
```bash
cd lineageAI
source venv/bin/activate  # o venv\Scripts\activate su Windows
pip install -e .
```

**Tecnologie**: FastMCP, Anthropic SDK, Pydantic, HTTPX

---

### 📚 Corsi Anthropic

#### Introduction to MCP
Materiale corso introduttivo Model Context Protocol  
**Focus**: CLI project, basics MCP architecture

#### MCP Advanced Topics
Approfondimenti su:
- Notifications
- Sampling
- HTTP transport layer

---

### 🎓 Altri Corsi

#### Building AI
Corso "Building AI" - Python fundamentals per AI  
**Struttura**: 4 capitoli progressivi con esempi pratici

#### Datamaster / AI Agentic Applications Masterclass
Masterclass su applicazioni agentiche:
- Modulo 1: Large Language Models foundations
- Modulo 2: LangChain framework
- Include notebook Jupyter con esempi pratici

---

### 🦙 ollama
Setup e configurazione Ollama per LLM locali  
**Use case**: Testing modelli open-source in locale (TinyLlama, etc.)

---

## 🛠️ Setup Ambiente di Sviluppo

### Prerequisiti
- Python 3.11+ (gestito via pyenv)
- Visual Studio Code
- Ollama (per modelli locali)
- Git

### Visual Studio Code - Estensioni Consigliate

#### 🐍 Python Development (Essenziali)
- **Python** (`ms-python.python`) - Supporto Python completo
- **Pylance** (`ms-python.vscode-pylance`) - Language server performante
- **Python Debugger** (`ms-python.debugpy`) - Debugging avanzato
- **autoDocstring** (`njpwerner.autodocstring`) - Generazione docstring automatica

#### 📊 Jupyter & Data Science
- **Jupyter** (`ms-toolsai.jupyter`) - Supporto notebook
- **Jupyter Keymap** (`ms-toolsai.jupyter-keymap`) - Shortcuts familiari
- **Jupyter Notebook Renderers** (`ms-toolsai.jupyter-renderers`) - Visualizzazioni avanzate

#### 🤖 AI/LLM Development
- **GitHub Copilot** (`GitHub.copilot`) - AI code completion
- **Continue** (`Continue.continue`) - AI assistant nel editor (supporta Ollama)

#### 📝 Markdown & Documentation
- **Markdown All in One** (`yzhang.markdown-all-in-one`) - Editing markdown avanzato
- **Markdown Preview Enhanced** (`shd101wyy.markdown-preview-enhanced`) - Preview ricco

#### 🔧 Code Quality
- **Black Formatter** (`ms-python.black-formatter`) - Formatting Python
- **Flake8** (`ms-python.flake8`) - Linting
- **isort** (`ms-python.isort`) - Import sorting
- **Error Lens** (`usernamehw.errorlens`) - Errori inline

#### 🎨 Produttività & UI
- **Path Intellisense** (`christian-kohler.path-intellisense`) - Autocomplete path
- **Better Comments** (`aaron-bond.better-comments`) - Commenti colorati
- **Todo Tree** (`Gruntfuggly.todo-tree`) - Gestione TODO
- **Git Graph** (`mhutchie.git-graph`) - Visualizzazione Git

#### 🔍 Utility
- **REST Client** (`humao.rest-client`) - Test API direttamente da VS Code
- **Thunder Client** (`rangav.vscode-thunder-client`) - API client GUI
- **YAML** (`redhat.vscode-yaml`) - Supporto YAML con schema validation

#### 💾 File Handling
- **EditorConfig** (`EditorConfig.EditorConfig`) - Consistent coding styles
- **DotENV** (`mikestead.dotenv`) - Syntax highlighting per .env

### Configurazione Workspace Consigliata

Crea `.vscode/extensions.json`:
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "ms-python.flake8",
    "ms-toolsai.jupyter",
    "GitHub.copilot",
    "Continue.continue",
    "yzhang.markdown-all-in-one",
    "usernamehw.errorlens",
    "mhutchie.git-graph"
  ]
}
```

### Virtual Environments
Ogni progetto usa il proprio venv isolato:
```bash
# Pattern standard per nuovi progetti
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Settings.json Consigliati
```json
{
    "python.analysis.typeCheckingMode": "basic",
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.terminal.activateEnvironment": true,
    
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    
    "jupyter.notebookFileRoot": "${workspaceFolder}",
    
    "files.exclude": {
        "**/__pycache__": true,
        "**/.pytest_cache": true,
        "**/*.pyc": true,
        "**/.venv": false,
        "**/venv": false
    },
    
    "python.testing.pytestEnabled": true,
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    }
}
```

---

## 📝 Note

- **lineageAI**: progetto core con integrazioni EDC reali
- **Corsi**: materiale di riferimento e sperimentazione
- **ollama**: per test rapidi senza chiamate API esterne
- Ogni progetto mantiene dipendenze isolate tramite venv

---

## 🔗 Quick Links

- [Anthropic MCP Docs](https://modelcontextprotocol.io)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Ollama Models](https://ollama.ai/library)
- [VS Code Python Tutorial](https://code.visualstudio.com/docs/python/python-tutorial)

---

## 🚀 Quick Start
```bash
# Clone e setup iniziale
git clone 
cd ai-lab

# Setup lineageAI (progetto principale)
cd lineageAI
python -m venv venv
source venv/bin/activate
pip install -e .

# Test MCP server
python -m src.mcp.server
```

---

**Ultimo aggiornamento**: Novembre 2025 
**Ambiente**: Windows, macOS, pyenv 3.11+