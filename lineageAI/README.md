# EDC-MCP-LLM Integration

**Enterprise Data Catalog meets AI-powered Data Governance**

Sistema intelligente per l'esplorazione e l'analisi del lineage dati attraverso conversazioni naturali con Claude Desktop, integrando Informatica EDC con Large Language Models.

---

## 🎯 Cos'è

Un server MCP (Model Context Protocol) che espone le funzionalità di Informatica Enterprise Data Catalog attraverso Claude Desktop, arricchendole con analisi AI per:

- **Ricercare** asset nel catalogo tramite linguaggio naturale
- **Esplorare** lineage upstream/downstream con alberi di dipendenze
- **Analizzare** l'impatto di modifiche su tabelle e colonne
- **Generare** checklist operative per change management
- **Arricchire** automaticamente la documentazione tecnica

**Esempio:**
> "Cerca tutte le tabelle con GARANZIE nel nome e mostrami il lineage upstream della prima"

Claude Desktop usa i tools MCP per interrogare EDC e rispondere con analisi dettagliate.

---

## 🏗️ Architettura
```
Claude Desktop (UI)
    ↓ stdio (MCP protocol)
MCP Server (src/mcp/server.py)
    ↓
┌─────────────────┴──────────────────┐
│                                     │
EDC Client                       LLM Factory
(src/edc/)                       (src/llm/)
    ↓                                 ↓
Informatica EDC              TinyLlama │ Claude │ Gemma3
(API REST)                   (via Ollama)  (API)  (via Ollama)
```

### Componenti Principali

**EDC Integration** (`src/edc/`)
- `client.py` - Client HTTP per API EDC bulk/objects
- `lineage.py` - Costruzione alberi lineage (evoluzione TreeBuilder)
- `models.py` - Data models (TreeNode, ImpactAnalysis, etc.)
- `class_types.py` - Mappatura tipi asset EDC

**LLM Integration** (`src/llm/`)
- `base.py` - Interfaccia astratta per LLM
- `factory.py` - Factory pattern per istanziare provider
- `tinyllama.py` - Client Ollama (locale, veloce)
- `gemma3.py` - Client Gemma3 4B (bilanciato, default)
- `claude.py` - Client Anthropic API (potente, cloud)

**MCP Server** (`src/mcp/`)
- `server.py` - Espone 10+ tools per Claude Desktop

**Configuration** (`src/config/`)
- `settings.py` - Gestione centralizzata configurazione da `.env`

---

## 📋 Prerequisiti

### Software
- **Python 3.9+**
- **Claude Desktop** (per interfaccia MCP)
- **Ollama** (opzionale, per TinyLlama/Gemma3 locale)

### Accesso
- Credenziali EDC (username/password)
- Claude API key (opzionale, se usi provider Claude)
- VPN/rete aziendale (se EDC è interno)

---

## 🚀 Installazione

### 1. Clone e Setup
```bash
cd lineageAI

# Virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Dipendenze
pip install -r requirements.txt
```

### 2. Configurazione

**Crea `.env` dalla template:**
```bash
cp .env.example .env
```

**Modifica `.env` con i tuoi dati:**
```ini
# EDC Configuration
EDC_BASE_URL=https://edc.collaudo.servizi.allitude.it:9086/access
EDC_USERNAME=Administrator
EDC_PASSWORD=your_password_here

# LLM Provider (tinyllama, claude, gemma3)
DEFAULT_LLM_PROVIDER=gemma3

# TinyLlama/Gemma3 (via Ollama locale)
OLLAMA_BASE_URL=http://localhost:11434
TINYLLAMA_MODEL=tinyllama
GEMMA3_MODEL=gemma3:4b

# Claude (opzionale)
CLAUDE_API_KEY=sk-ant-api03-xxxxx
CLAUDE_MODEL=claude-sonnet-4-20250514
```

### 3. Test Connessione
```bash
# Verifica settings
python -c "from src.config.settings import settings; print(f'EDC: {settings.edc_base_url}')"

# Test EDC client
python -c "import asyncio; from src.edc.client import EDCClient; asyncio.run(EDCClient().get_asset_details('DataPlatform://ORAC51/DWHEVO/test'))"
```

### 4. Configurazione Claude Desktop

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`
```json
{
  "mcpServers": {
    "edc-lineage": {
      "command": "C:\\Dev\\ai-training\\lineageAI\\venv\\Scripts\\python.exe",
      "args": ["-m", "src.mcp.server"],
      "cwd": "C:\\Dev\\ai-training\\lineageAI"
    }
  }
}
```

**⚠️ Importante:** Sostituisci i path con quelli corretti del tuo sistema!

### 5. Avvio

1. Riavvia Claude Desktop
2. Verifica icona 🔨 in basso (tools disponibili)
3. Clicca per vedere "edc-lineage" tra i server MCP attivi

---

## 🛠️ Tools MCP Disponibili

Il sistema espone 10 tools per Claude Desktop:

### 1. **search_assets**
Cerca asset nel catalogo EDC.
```
Parametri:
- resource_name: string (obbligatorio, es: "DataPlatform")
- name_filter: string (opzionale, es: "GARANZIE")
- asset_type: string (opzionale, es: "Table", "View")
- max_results: integer (default: 10)
```

### 2. **get_asset_details**
Recupera dettagli completi di un asset con enhancement AI.
```
Parametri:
- asset_id: string (es: "DataPlatform://ORAC51/DWHEVO/TABLE_NAME")
```

### 3. **get_lineage_tree**
Costruisce albero lineage completo con analisi AI.
```
Parametri:
- asset_id: string
- direction: "upstream" | "downstream" | "both" (default: "upstream")
- depth: integer (default: 3, max: 10)
```

### 4. **get_immediate_lineage**
Recupera lineage immediato (1 livello).
```
Parametri:
- asset_id: string
- direction: "upstream" | "downstream" | "both"
```

### 5. **analyze_change_impact**
Analizza impatto di una modifica con AI.
```
Parametri:
- asset_id: string
- change_type: string (es: "column_drop", "data_type_change")
- change_description: string
- max_depth: integer (default: 5)
```

### 6. **generate_change_checklist**
Genera checklist operativa per implementare una modifica.
```
Parametri:
- asset_id: string
- change_type: string
- change_description: string
```

### 7. **enhance_asset_documentation**
Arricchisce documentazione asset con AI.
```
Parametri:
- asset_id: string
- include_lineage_context: boolean (default: true)
- business_domain: string (opzionale)
```

### 8. **switch_llm_provider**
Cambia provider LLM a runtime.
```
Parametri:
- provider: "tinyllama" | "claude" | "gemma3"
```

### 9. **get_llm_status**
Mostra stato corrente sistema LLM.

### 10. **get_system_statistics**
Statistiche complete: API calls, cache hits, errori, etc.

---

## 💡 Esempi d'Uso

### Ricerca Asset

**Tu chiedi a Claude:**
> Cerca le tabelle che contengono GARANZIE nel nome in DataPlatform

**Claude usa:**
```
search_assets(
  resource_name="DataPlatform",
  name_filter="GARANZIE",
  asset_type="Table"
)
```

**Risposta:**
```
Trovati 12 asset:
1. IFR_WK_GARANZIE_SOFFERENZE_DT_AP
2. DIM_GARANZIE_STATALI
3. FACT_GARANZIE_MENSILE
...
```

---

### Lineage Upstream

**Tu chiedi:**
> Costruisci il lineage upstream di IFR_WK_GARANZIE_SOFFERENZE_DT_AP con profondità 2

**Claude usa:**
```
get_lineage_tree(
  asset_id="DataPlatform://ORAC51/DWHEVO/IFR_WK_GARANZIE_SOFFERENZE_DT_AP",
  direction="upstream",
  depth=2
)
```

**Risposta:**
```
Albero Lineage:

[001] IFR_WK_GARANZIE_SOFFERENZE_DT_AP (Table)
  [001001] STG_GARANZIE_DT (Table)
    [001001001] SRC_GARANZIE_RAW (Table)
  [001002] DIM_CLIENTE (Table)
    [001002001] STG_ANAGRAFICA (Table)

Statistiche:
- Nodi totali: 5
- Profondità: 3
- Tempo: 1.2s
```

---

### Analisi Impatto

**Tu chiedi:**
> Se elimino la colonna IMPORTO_GARANTITO da IFR_WK_GARANZIE_SOFFERENZE_DT_AP, cosa succede?

**Claude usa:**
```
analyze_change_impact(
  asset_id="DataPlatform://ORAC51/DWHEVO/IFR_WK_GARANZIE_SOFFERENZE_DT_AP",
  change_type="column_drop",
  change_description="Eliminazione colonna IMPORTO_GARANTITO"
)
```

**Risposta (generata da Gemma3):**
```
LIVELLO RISCHIO: HIGH

Asset Downstream Impattati: 8

Impatto Business:
La colonna IMPORTO_GARANTITO è utilizzata in report regolatori
e dashboard executive. L'eliminazione causerebbe failure di 3 job
critici di reporting mensile.

Raccomandazioni:
1. Verificare tutte le query SQL che referenziano la colonna
2. Aggiornare viste materializzate
3. Comunicare a team BI e Compliance
4. Preparare periodo di transizione con colonna deprecata
5. Implementare validazione su nuova struttura

Strategia Testing:
- Unit test su procedure stored
- Integration test job ETL
- Smoke test report executive
- Validazione dati pre/post migrazione
```

---

### Checklist Operativa

**Tu chiedi:**
> Genera una checklist per aggiungere la colonna DATA_SCADENZA

**Claude usa:**
```
generate_change_checklist(
  asset_id="DataPlatform://ORAC51/DWHEVO/IFR_WK_GARANZIE_SOFFERENZE_DT_AP",
  change_type="schema_change",
  change_description="Aggiunta nuova colonna DATA_SCADENZA"
)
```

**Risposta:**
```
CHECKLIST OPERATIVA

GOVERNANCE E APPROVAZIONI:
  [ ] 1. Sottometti change request formale
  [ ] 2. Ottieni approvazione data owner
  [ ] 3. Documenta risk assessment

PREPARAZIONE PRE-MODIFICA:
  [ ] 1. Backup completo tabella e dipendenze
  [ ] 2. Verifica ambiente test disponibile
  [ ] 3. Prepara script DDL e rollback

ESECUZIONE:
  [ ] 1. Deploy in DEV e test unitari
  [ ] 2. Deploy in TEST e integration test
  [ ] 3. Deploy in PROD con finestra manutenzione

VALIDAZIONE:
  [ ] 1. Verifica schema aggiornato
  [ ] 2. Test job ETL downstream
  [ ] 3. Controllo data quality

MONITORING POST-IMPLEMENTAZIONE:
  [ ] 1. Monitora job per 48h
  [ ] 2. Verifica assenza alert
  [ ] 3. Report post-implementazione
```

---

## 🎛️ Provider LLM

### Gemma3 4B (Default) - Bilanciato
```ini
DEFAULT_LLM_PROVIDER=gemma3
OLLAMA_BASE_URL=http://localhost:11434
GEMMA3_MODEL=gemma3:4b
```

**Pro:**
- Ottimo rapporto qualità/velocità
- Locale (privacy)
- Gratis
- Analisi tecniche molto buone

**Contro:**
- Richiede Ollama installato
- RAM: ~8GB

**Setup:**
```bash
ollama pull gemma3:4b
ollama serve
```

---

### TinyLlama - Veloce
```ini
DEFAULT_LLM_PROVIDER=tinyllama
TINYLLAMA_MODEL=tinyllama
```

**Pro:**
- Molto veloce
- Leggero (RAM: ~2GB)
- Locale e gratis

**Contro:**
- Meno preciso di Gemma3/Claude
- Analisi più semplici

**Uso:** Sviluppo, test rapidi, high-volume processing

---

### Claude Sonnet 4 - Potente
```ini
DEFAULT_LLM_PROVIDER=claude
CLAUDE_API_KEY=sk-ant-api03-xxxxx
CLAUDE_MODEL=claude-sonnet-4-20250514
```

**Pro:**
- Analisi molto dettagliate
- Eccellente per change impact
- Migliore comprensione contesto

**Contro:**
- Richiede API key
- Costo per token (~$3-15 per 1M token)
- Richiede connessione internet

**Uso:** Analisi critiche, produzione, demo executive

---

### Switch Runtime

Puoi cambiare provider durante la conversazione:

> Passa a Claude per questa analisi
```
switch_llm_provider(provider="claude")
```

---

## 🧪 Testing Interattivo

### Jupyter Notebook
```bash
# Installa kernel
pip install ipykernel
python -m ipykernel install --user --name=lineageai --display-name="LineageAI"

# Avvia Jupyter
jupyter notebook notebooks/edc_testing_notebook.ipynb
```

Il notebook include:
- Setup automatico imports
- Funzioni helper per test
- Esempi pre-compilati
- Visualizzazione alberi lineage
- Switch LLM interattivo

---

## 📊 Statistiche e Monitoring

### In Claude Desktop

> Mostrami le statistiche del sistema
```
get_system_statistics()
```

**Output:**
```
Statistiche Sistema EDC-MCP-LLM:

LLM Provider: gemma3

EDC:
- Total API calls: 47
- Cache hits: 23 (48.9%)
- API errors: 0
- Nodi creati: 156

Configurazione:
- Max tree depth: 10
- Request timeout: 30s
```

### Log MCP Server

**Windows:**
```
%APPDATA%\Claude\logs\mcp-server-edc-lineage.log
```

**Contenuto esempio:**
```
[MCP] >> handle_call_tool('search_assets') chiamato
[MCP] >> Arguments: {'resource_name': 'DataPlatform', ...}
[MCP] >> search_assets completed: 15 results
```

---

## 🔧 Troubleshooting

### Server MCP non visibile in Claude Desktop

**Sintomi:** Icona 🔨 non appare o server non in lista

**Soluzioni:**
1. Verifica path nel `claude_desktop_config.json` (usa path assoluti)
2. Controlla log: `%APPDATA%\Claude\logs\mcp-server-edc-lineage.log`
3. Test manuale: `python -m src.mcp.server`
4. Riavvia Claude Desktop completamente

---

### EDC Connection Failed

**Sintomi:** Errori "Connection refused" o "Timeout"

**Soluzioni:**
1. Verifica VPN attiva
2. Test connessione: `curl -I https://edc.collaudo.servizi.allitude.it:9086/access`
3. Controlla firewall/proxy
4. Verifica credenziali in `.env`

---

### LLM Provider Error

**Per Ollama (TinyLlama/Gemma3):**
```bash
# Verifica Ollama running
curl http://localhost:11434/api/tags

# Avvia se necessario
ollama serve

# Verifica modello installato
ollama list

# Installa se mancante
ollama pull gemma3:4b
```

**Per Claude API:**
1. Verifica API key valida
2. Controlla credito residuo su console.anthropic.com
3. Test manuale:
```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $CLAUDE_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

---

### Ricerche Lente

**Sintomi:** Timeout o response time > 10s

**Ottimizzazioni:**
1. Riduci `max_results` nelle ricerche
2. Riduci `depth` nei lineage tree
3. La cache è già attiva di default
4. Aumenta `EDC_REQUEST_TIMEOUT` nel `.env` se necessario

---

### SSL Certificate Errors

**Sintomi:** `SSL: CERTIFICATE_VERIFY_FAILED`

**Soluzione:** Già disabilitata la verifica SSL nel codice per certificati self-signed:
```python
connector = aiohttp.TCPConnector(ssl=False)
```

Se persiste, verifica proxy aziendali o certificati custom.

---

## 📁 Struttura File
```
lineageAI/
├── .env                          # Configurazione (NON commitare!)
├── .env.example                  # Template configurazione
├── requirements.txt              # Dipendenze Python
├── run_server.py                 # Avvio MCP server (standalone test)
├── README.md                     # Questa documentazione
│
├── notebooks/
│   └── edc_testing_notebook.ipynb  # Test interattivi Jupyter
│
├── src/
│   ├── config/
│   │   └── settings.py           # Gestione configurazione centralizzata
│   │
│   ├── edc/                      # Integrazione EDC
│   │   ├── client.py             # Client HTTP per API EDC
│   │   ├── lineage.py            # Builder alberi lineage
│   │   ├── models.py             # Data models
│   │   └── class_types.py        # Mappatura tipi asset
│   │
│   ├── llm/                      # Integrazione LLM
│   │   ├── base.py               # Interfaccia astratta
│   │   ├── factory.py            # Factory pattern
│   │   ├── tinyllama.py          # Client Ollama
│   │   ├── gemma3.py             # Client Gemma3
│   │   └── claude.py             # Client Anthropic
│   │
│   └── mcp/                      # MCP Server
│       └── server.py             # Server principale con 10 tools
│
└── venv/                         # Virtual environment (gitignore)
```

---

## 🔐 Sicurezza

### Credenziali
- **MAI** commitare `.env` su Git
- Usa `.env.example` come template
- In produzione: secret manager (Azure KeyVault, AWS Secrets)

### Rete
- Server MCP gira solo locale (stdio)
- Solo EDC e LLM API sono chiamate esterne
- Nessuna porta TCP aperta

### Dati
- Cache solo in memoria (no persistenza)
- Log non contengono dati sensibili
- Lineage tree non persistiti

---

## 🎯 Best Practices

### Performance
1. **Ricerche ampie:** Usa filtri stretti (name_filter + asset_type)
2. **Lineage profondi:** Inizia con depth=2, poi aumenta se serve
3. **Cache:** Già attivo - riusa gli stessi asset per sfruttarlo
4. **Batch:** Per analisi massive, considera scripting diretto

### Costi LLM
1. **Sviluppo:** TinyLlama (gratis)
2. **Normale:** Gemma3 (gratis, ottimo)
3. **Critiche/Demo:** Claude (pagamento)

### Data Governance
1. Documenta le modifiche nel catalogo EDC
2. Usa checklist generate per compliance
3. Archivia analisi impatto per audit trail
4. Sfrutta enhancement AI per migliorare metadati

---

## 📚 Riferimenti

### Documentazione Prodotti
- [Informatica EDC](https://docs.informatica.com/data-catalog.html)
- [Anthropic Claude](https://docs.anthropic.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Ollama](https://ollama.ai/)

### API EDC
- Base URL: `https://edc.servizi.allitude.it:9086/access`
- Versione API: 2
- Endpoints principali:
  - `/1/catalog/data/bulk` - Ricerca bulk
  - `/2/catalog/data/objects` - Dettagli asset

---

## 👤 Autore

**Lorenzo** - Principal Data Architect @ NTT Data Italia

- 20+ anni esperienza enterprise data management
- Specializzazione: Data Governance, Informatica EDC
- Progetti: Axon, IDMC, PowerCenter, Data Quality

---

## 📄 Licenza

MIT License - Progetto formativo per esplorare integrazione tecnologie moderne (MCP, LLM) con sistemi enterprise esistenti (EDC).

---

**Ultimo Aggiornamento:** Novembre 2024  
**Versione:** 1.0.0  
**Python:** 3.9+  
**Piattaforme:** Windows, Linux, macOS