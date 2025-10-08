# EDC-MCP-LLM Integration

Progetto formativo per l'integrazione di **Informatica EDC** con **Model Context Protocol (MCP)** e **Large Language Models** multipli (TinyLlama e Claude).

## Obiettivi del Progetto

- Integrare API EDC per la costruzione di alberi di data lineage
- Utilizzare MCP per esporre funzionalità intelligenti
- Supportare provider LLM multipli (TinyLlama locale e Claude API)
- Mantenere compatibilità con logica TreeBuilder esistente
- Fornire analisi avanzate di impatto e enhancement documentazione

## Architettura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   EDC APIs      │    │   MCP Server    │    │   LLM Providers │
│                 │    │                 │    │                 │
│ • Asset Metadata│◄──►│ • Lineage Tools │◄──►│ • TinyLlama     │
│ • Lineage Data  │    │ • Impact Analysis│    │ • Claude API    │
│ • Field X-Ref   │    │ • Documentation │    │ • (Extensible)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Funzionalità Principali

### 1. Asset Information
- `get_asset_details()` - Recupera metadati completi con enhancement AI
- `search_assets()` - Ricerca intelligente nel catalogo
- `enhance_asset_documentation()` - Arricchimento documentazione

### 2. Lineage Analysis  
- `get_lineage_tree()` - Costruzione albero lineage completo
- `get_immediate_lineage()` - Lineage 1 livello (upstream/downstream)
- `analyze_lineage_complexity()` - Analisi complessità con AI

### 3. Impact Analysis
- `analyze_change_impact()` - Analisi impatti modifiche
- `generate_change_checklist()` - Checklist operativa
- Supporto per vari tipi di modifiche (column_drop, data_type_change, etc.)

### 4. LLM Management
- `switch_llm_provider()` - Cambio provider runtime
- `get_llm_status()` - Stato sistema LLM
- Supporto TinyLlama (locale) e Claude (API)

## Setup del Progetto

### 1. Prerequisiti

```bash
# Python 3.9+
python --version

# Ollama per TinyLlama (opzionale)
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull tinyllama

# Accesso a Informatica EDC
# Claude API key (opzionale)
```

### 2. Installazione

```bash
# Clone del progetto
git clone <repository-url>
cd edc-mcp-llm

# Ambiente virtuale
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Dipendenze
pip install -r requirements.txt
```

### 3. Configurazione

```bash
# Copia template configurazione
cp .env.example .env
cp config.ini.example config.ini

# Modifica .env con le tue credenziali
nano .env

# Modifica config.ini con parametri EDC
nano config.ini
```

### 4. Test Setup

```bash
# Test configurazione di base
python examples/basic_usage.py

# Test MCP server (quando implementato)
python -m src.mcp.server
```

## Configurazione Dettagliata

### File .env
```env
# EDC Configuration
EDC_BASE_URL=https://your-edc-instance.informatica.com/ldm
EDC_USERNAME=your_username
EDC_PASSWORD=your_password

# LLM Configuration
CLAUDE_API_KEY=your_claude_api_key
OLLAMA_BASE_URL=http://localhost:11434

# MCP Server
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000
```

### File config.ini
Contiene parametri specifici per:
- API EDC (associations, pageSize, etc.)
- TreeBuilder (deduplicazione, limiti, etc.)  
- Field cross-reference (opzionale)
- Logging

## Esempi di Utilizzo

### Analisi Asset Basica
```python
from src.edc.lineage import LineageBuilder
from src.llm.factory import LLMFactory, LLMConfig, LLMProvider

async def analyze_asset():
    # Configura LLM
    llm_config = LLMConfig(
        provider=LLMProvider.TINYLLAMA,
        model_name="tinyllama"
    )
    llm_client = LLMFactory.create_llm_client(llm_config)
    
    # Analizza asset
    async with LineageBuilder() as builder:
        metadata = await builder.get_asset_metadata("your-asset-id")
        
        # Enhancement con AI
        enhanced = await llm_client.enhance_description(
            asset_name=metadata['name'],
            technical_desc=metadata['description'],
            schema_context="banking",
            column_info=[]
        )
        
        print(f"Enhanced: {enhanced}")
```

### Costruzione Lineage Tree
```python
async def build_lineage():
    async with LineageBuilder() as builder:
        # Costruisce albero completo (logica TreeBuilder)
        tree = await builder.build_tree(
            node_id="your-root-asset-id",
            code="001"
        )
        
        if tree:
            stats = tree.get_statistics()
            print(f"Nodi: {stats['total_nodes']}")
            print(f"Profondità: {stats['max_depth']}")
```

### Analisi di Impatto
```python
async def impact_analysis():
    llm_client = LLMFactory.create_llm_client(claude_config)
    
    async with LineageBuilder() as builder:
        # Analizza impatto modifica
        impact = await llm_client.analyze_change_impact(
            source_asset="asset-id",
            change_type="column_drop",
            change_details={"column": "customer_id"},
            affected_lineage=downstream_data
        )
        
        print(f"Risk: {impact['risk_level']}")
        print(f"Recommendations: {impact['recommendations']}")
```

## Compatibilità TreeBuilder

Il progetto mantiene piena compatibilità con la logica esistente:

- **Deduplicazione ID-only**: Preservata la logica di deduplicazione
- **Gestione auto-referenze**: Algoritmo intelligente mantenuto
- **Field cross-reference**: Supporto completo con alias legacy
- **Logging dettagliato**: Sistema di logging originale
- **Statistiche**: Tutte le metriche originali disponibili

## Struttura File

```
edc-mcp-llm/
├── src/
│   ├── edc/
│   │   ├── client.py          # Client asincrono EDC
│   │   ├── lineage.py         # LineageBuilder (da TreeBuilder)
│   │   └── models.py          # TreeNode + modelli aggiuntivi
│   ├── llm/
│   │   ├── base.py            # Classe base astratta
│   │   ├── tinyllama.py       # Client TinyLlama
│   │   ├── claude.py          # Client Claude
│   │   └── factory.py         # Factory pattern
│   ├── mcp/
│   │   └── server.py          # Server MCP principale
│   └── config/
│       └── settings.py        # Configurazioni centrali
├── examples/
│   ├── basic_usage.py         # Esempi di utilizzo
│   ├── compare_llms.py        # Confronto provider
│   └── lineage_analysis.py    # Analisi lineage avanzate
├── tests/
├── config.ini.example         # Template configurazione EDC
├── .env.example              # Template variabili ambiente
└── requirements.txt          # Dipendenze Python
```

## Roadmap

### Fase 1 - Foundation (Completata)
- [x] Integrazione TreeBuilder esistente
- [x] Client EDC asincrono
- [x] Astrazione LLM multi-provider
- [x] Struttura progetto modulare

### Fase 2 - MCP Integration (In Sviluppo)
- [ ] Server MCP completo
- [ ] Tool registration e testing
- [ ] Integrazione con client MCP
- [ ] Documentation tools avanzati

### Fase 3 - Advanced Features
- [ ] Caching intelligente
- [ ] Batch processing
- [ ] Visualizzazione lineage
- [ ] Export/import configurazioni

### Fase 4 - Production Ready
- [ ] Test suite completa
- [ ] Performance optimization
- [ ] Monitoring e metrics
- [ ] Deployment automation

## Troubleshooting

### Errori Comuni

**EDC Connection Issues**
```bash
# Verifica connettività
curl -I "https://your-edc-instance.com/ldm/api/v2"

# Verifica credenziali
echo "username:password" | base64
```

**Ollama/TinyLlama Issues**
```bash
# Verifica Ollama
ollama list
ollama pull tinyllama

# Test connessione
curl http://localhost:11434/api/tags
```

**Claude API Issues**
```bash
# Verifica API key
export CLAUDE_API_KEY="your-key"
# Test nel codice
```

### Performance Tuning

- **Cache**: Abilita caching per asset frequenti
- **Batch Size**: Ajusta pageSize in config.ini
- **Concurrent Requests**: Modifica max_concurrent_requests
- **Tree Depth**: Limita max_tree_depth per alberi grandi

## Contributing

1. Fork del repository
2. Crea feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing-feature`)
5. Apri Pull Request

## License

Progetto formativo - MIT License

## Contatti

Lorenzo - Principal Data Architect @ NTT Data Italia
- Specializzazione: Data Governance, Informatica EDC
- Esperienza: 20+ anni enterprise data management

---

**Nota**: Questo è un progetto formativo per esplorare l'integrazione di tecnologie moderne (MCP, LLM) con sistemi enterprise esistenti (EDC). La logica del TreeBuilder originale è preservata integralmente per garantire compatibilità.