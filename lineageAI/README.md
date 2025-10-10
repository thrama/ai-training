# README - EDC-MCP-LLM Integration

## Cos'è questo progetto? (Spiegazione semplice)

Immagina di avere una grande biblioteca piena di libri (i tuoi dati aziendali). Ogni libro è collegato ad altri libri attraverso riferimenti e citazioni. Questo progetto è come avere un bibliotecario intelligente che:

1. **Sa dove sono tutti i libri** (Informatica EDC - il catalogo)
2. **Capisce come sono collegati tra loro** (Lineage - le relazioni)
3. **Può spiegarti tutto in modo semplice** (LLM - l'intelligenza artificiale)
4. **Risponde alle tue domande** (MCP - il sistema di comunicazione)

## I Tre Componenti Principali

```
┌─────────────────┐
│   TU CHIEDI     │
│  "Dove usano    │
│   questa        │
│   tabella?"     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   MCP SERVER    │ ◄─── Il "centralino" che smista le richieste
│  (server.py)    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌─────────┐
│   EDC   │ │   LLM   │
│ Catalogo│ │  AI     │
└─────────┘ └─────────┘
    │         │
    └────┬────┘
         ▼
    RISPOSTA COMPLETA
```

## Struttura dei File - Cosa Fa Ogni Cosa

### 📁 File di Configurazione (Quelli che devi modificare)

#### `.env` - Il File delle Credenziali
Contiene le password e le configurazioni segrete. È come il portachiavi:

```env
# Dove si trova il catalogo EDC
EDC_BASE_URL=https://edc.tuaazienda.it:9086/access

# Username e password per accedere
EDC_USERNAME=Administrator
EDC_PASSWORD=la_tua_password_segreta

# Chiave per usare Claude AI (opzionale)
CLAUDE_API_KEY=sk-ant-api03-xxxx...
```

**Cosa modificare:**
- `EDC_BASE_URL`: L'indirizzo del tuo server EDC
- `EDC_USERNAME`: Il tuo nome utente
- `EDC_PASSWORD`: La tua password
- `CLAUDE_API_KEY`: Se vuoi usare Claude invece di TinyLlama

#### `config.ini` - Le Impostazioni Avanzate
Contiene parametri tecnici. Normalmente non serve modificarlo.

### 📁 Codice Sorgente (`src/`)

#### `src/config/settings.py` - Il Centro di Controllo
Legge tutti i file di configurazione e li organizza. È come il cruscotto di un'auto che mostra tutte le spie.

**Cosa fa:**
- Legge il file `.env`
- Prepara le credenziali per EDC
- Configura quale AI usare (TinyLlama o Claude)
- Imposta limiti e timeout

#### `src/edc/` - La Parte che Parla con EDC

**`client.py`** - Il Messaggero
- Si connette al server EDC
- Chiede informazioni sugli asset (tabelle, colonne, etc.)
- Gestisce la cache per andare più veloce
- Conta quante chiamate fa (statistiche)

```python
# Esempio di cosa fa:
# 1. "Dammi info sulla tabella CLIENTI"
# 2. Controlla se ce l'ha già in memoria (cache)
# 3. Se no, chiama EDC
# 4. Salva la risposta per la prossima volta
```

**`lineage.py`** - Il Costruttore di Alberi
- Costruisce "l'albero genealogico" dei dati
- Parte da una tabella e trova tutte le tabelle "genitori"
- Si ferma ai livelli che gli dici tu (max_depth)
- Evita di girare in cerchio (prevenzione cicli)

```
Esempio di albero:
TABELLA_FINALE
    ├── TABELLA_INTERMEDIA_1
    │   ├── TABELLA_SORGENTE_A
    │   └── TABELLA_SORGENTE_B
    └── TABELLA_INTERMEDIA_2
        └── TABELLA_SORGENTE_C
```

**`models.py`** - Le Strutture Dati
Definisce come sono fatti gli oggetti (come i "mattoncini Lego" del progetto):
- `TreeNode`: Un nodo dell'albero
- `ImpactAnalysisRequest`: Una richiesta di analisi impatto
- Altri modelli dati

**`class_types.py`** - Il Traduttore di Tipi
Capisce cosa vuoi cercare quando parli in linguaggio naturale:

```python
# Tu dici: "mostrami le tabelle"
# Lui traduce in: "com.infa.ldm.relational.Table"

# Tu dici: "tutte le colonne"
# Lui traduce in: "com.infa.ldm.relational.Column"
```

#### `src/llm/` - La Parte dell'Intelligenza Artificiale

**`base.py`** - Il Contratto Base
Definisce cosa DEVE fare ogni AI, come un "contratto":
- Arricchire le descrizioni
- Analizzare la complessità
- Suggerire azioni da fare

**`tinyllama.py`** - L'AI Locale (Gratis)
- Si connette a Ollama sul tuo computer
- Veloce ma meno precisa
- Non servono API key
- Buona per sviluppo e test

**`claude.py`** - L'AI Cloud (A Pagamento)
- Si connette ai server di Anthropic
- Molto precisa e intelligente
- Serve API key
- Costa in base all'uso

**`factory.py`** - Il Selettore di AI
Decide quale AI usare in base alla configurazione. È come un interruttore:

```python
if config.provider == "tinyllama":
    return TinyLlamaClient()
elif config.provider == "claude":
    return ClaudeClient()
```

#### `src/mcp/server.py` - Il Cervello del Progetto

Questo è il file più importante! Coordina tutto.

**Cosa fa:**
1. **Registra i "tools"** (le funzioni disponibili)
2. **Riceve richieste** da Claude Desktop
3. **Chiama EDC** per i dati
4. **Chiama l'AI** per arricchire le risposte
5. **Ritorna il risultato**

**I Tools Disponibili** (le cose che puoi chiedere):

1. **`get_asset_details`** - "Dimmi tutto su questa tabella"
   ```
   Input: ID della tabella
   Output: Nome, tipo, descrizione arricchita, collegamenti
   ```

2. **`search_assets`** - "Cerca tabelle che contengono CLIENTE"
   ```
   Input: Parola da cercare, tipo di oggetto
   Output: Lista di asset trovati
   ```

3. **`get_lineage_tree`** - "Costruisci l'albero completo"
   ```
   Input: Tabella di partenza, profondità
   Output: Albero con tutte le dipendenze
   ```

4. **`get_immediate_lineage`** - "Da dove viene? Dove va?"
   ```
   Input: Tabella
   Output: Lista diretta upstream/downstream
   ```

5. **`analyze_change_impact`** - "Se cambio questo, cosa succede?"
   ```
   Input: Tabella, tipo di modifica
   Output: Rischio, impatti, raccomandazioni
   ```

6. **`generate_change_checklist`** - "Cosa devo fare step-by-step?"
   ```
   Input: Modifica da fare
   Output: Checklist operativa completa
   ```

7. **`enhance_asset_documentation`** - "Arricchisci la documentazione"
   ```
   Input: Asset
   Output: Descrizione migliorata, tag, regole qualità
   ```

8. **`switch_llm_provider`** - "Cambia AI"
   ```
   Input: tinyllama o claude
   Output: Conferma cambio
   ```

9. **`get_llm_status`** - "Che AI stai usando?"
   ```
   Output: Provider attivo, disponibilità
   ```

10. **`get_system_statistics`** - "Dammi le statistiche"
    ```
    Output: Chiamate fatte, cache, errori
    ```

### 📁 File di Test

Tutti i file `test_*.py` servono per verificare che tutto funzioni:

- **`test_llm_simple.py`** - Verifica che le AI rispondano
- **`test_mcp_integration.py`** - Testa tutti i tools MCP
- **`test_complete_integration.py`** - Test end-to-end completo
- **`test_edc_llm_integration.py`** - Test integrazione EDC+LLM
- **`test_search_flow.py`** - Traccia tutto il flusso di una ricerca

## Come Funziona - Flusso Completo

Ecco cosa succede quando chiedi qualcosa:

```
1. TU SCRIVI IN CLAUDE DESKTOP:
   "Cerca le tabelle che contengono GARANZIE"

2. CLAUDE DESKTOP:
   - Vede che hai chiesto una ricerca
   - Chiama il tool MCP "search_assets"
   - Parametri: resource_name="DataPlatform", name_filter="GARANZIE"

3. MCP SERVER (server.py):
   - Riceve la chiamata a "search_assets"
   - Smista a: _handle_search_assets()
   
4. EDC CLIENT (client.py):
   - Prepara chiamata API bulk EDC
   - URL: https://edc.../1/catalog/data/bulk
   - Parametri: resourceName=DataPlatform, etc.
   - Chiama l'API EDC

5. EDC (IL CATALOGO):
   - Cerca nel database
   - Trova tutte le tabelle
   - Ritorna CSV con i risultati

6. EDC CLIENT:
   - Legge il CSV
   - Filtra per "GARANZIE" nel nome
   - Arricchisce i dati

7. MCP SERVER:
   - Riceve i risultati
   - Opzionalmente chiama l'AI per arricchire
   - Formatta la risposta

8. CLAUDE DESKTOP:
   - Riceve la risposta formattata
   - Te la mostra in modo leggibile

9. TU LEGGI:
   "Trovate 5 tabelle con GARANZIE nel nome:
    1. IFR_WK_GARANZIE_DT
    2. GARANZIE_SOFFERENZE
    ..."
```

## Installazione - Passo Passo

### 1. Prerequisiti

```bash
# Hai bisogno di:
- Python 3.9 o superiore
- Accesso a un server Informatica EDC
- (Opzionale) Claude API key
- (Opzionale) Ollama per TinyLlama locale
```

### 2. Installazione Base

```bash
# Clona o scarica il progetto
cd lineageAI

# Crea ambiente virtuale
python -m venv venv

# Attiva ambiente
# Su Windows:
venv\Scripts\activate
# Su Linux/Mac:
source venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt
```

### 3. Configurazione

```bash
# Copia e modifica .env
cp .env.example .env
# Apri .env con un editor e inserisci le TUE credenziali

# Il file config.ini va bene così com'è (di solito)
```

### 4. Test di Verifica

```bash
# Test semplice LLM
python test_llm_simple.py

# Se funziona, prova il test completo
python test_mcp_integration.py
```

### 5. Configurazione Claude Desktop

Modifica il file di configurazione di Claude Desktop:

**Windows:**
`%APPDATA%\Claude\claude_desktop_config.json`

**Mac:**
`~/Library/Application Support/Claude/claude_desktop_config.json`

**Linux:**
`~/.config/Claude/claude_desktop_config.json`

Contenuto:
```json
{
  "mcpServers": {
    "edc-lineage": {
      "command": "C:\\path\\to\\your\\venv\\Scripts\\python.exe",
      "args": ["-m", "src.mcp.server"],
      "cwd": "C:\\path\\to\\lineageAI"
    }
  }
}
```

**IMPORTANTE:** Sostituisci i path con i TUOI path reali!

### 6. Avvio

```bash
# Riavvia Claude Desktop
# Dovresti vedere l'icona del martelletto
# Se clicchi vedrai il tool "edc-lineage"
```

## Esempi di Uso Pratico

### Esempio 1: Cercare una Tabella

**Tu chiedi a Claude:**
> Cerca tutte le tabelle che contengono CLIENTE nel nome nella risorsa DataPlatform

**Claude usa il tool:**
```
search_assets(
  resource_name="DataPlatform",
  name_filter="CLIENTE",
  asset_type="Table"
)
```

**Risposta:**
```
Trovate 12 tabelle:
1. TB_CLIENTI_ANAGRAFICI
2. DIM_CLIENTE
3. FACT_CLIENTI_VENDITE
...
```

### Esempio 2: Analisi Impatto

**Tu chiedi:**
> Se elimino la colonna EMAIL dalla tabella TB_CLIENTI, cosa succede?

**Claude usa:**
```
analyze_change_impact(
  asset_id="DataPlatform://ORAC51/SCHEMA/TB_CLIENTI",
  change_type="column_drop",
  change_description="Eliminazione colonna EMAIL"
)
```

**Risposta:**
```
LIVELLO RISCHIO: HIGH

Asset Impattati: 8 downstream

Impatto Business:
La colonna EMAIL è utilizzata in 3 report critici...

Raccomandazioni:
1. Verificare tutti i report che usano EMAIL
2. Creare colonna di migrazione temporanea
3. Aggiornare le query applicative
...
```

### Esempio 3: Documentazione

**Tu chiedi:**
> Arricchisci la documentazione della tabella VENDITE

**Claude usa:**
```
enhance_asset_documentation(
  asset_id="DataPlatform://ORAC51/SCHEMA/VENDITE",
  include_lineage_context=true,
  business_domain="Sales"
)
```

**Risposta:**
```
Descrizione Arricchita:
La tabella VENDITE contiene lo storico transazionale di tutte 
le vendite aziendali. Alimenta i report executive e i dashboard 
commerciali. È il cuore del sistema di reportistica...

Tag Suggeriti:
sales, transactional, daily-load, critical, gdpr

Regole Qualità:
1. Verificare che importo > 0
2. Data vendita <= oggi
...
```

## Troubleshooting - Problemi Comuni

### Il server non si avvia

**Sintomo:** Claude Desktop non vede il tool

**Soluzione:**
1. Verifica che i path nel `claude_desktop_config.json` siano corretti
2. Controlla il log: `%APPDATA%\Claude\logs\mcp-server-edc-lineage.log`
3. Prova ad avviare manualmente: `python -m src.mcp.server`

### Errore "EDC Connection Failed"

**Sintomo:** "Errore connessione EDC"

**Soluzione:**
1. Verifica che `EDC_BASE_URL` nel `.env` sia corretto
2. Verifica username e password
3. Testa con: `curl -I "https://tuo-edc-url/access"`
4. Controlla firewall/VPN

### LLM non funziona

**Sintomo:** "Error calling Claude/TinyLlama"

**Soluzione per Claude:**
1. Verifica `CLAUDE_API_KEY` nel `.env`
2. Controlla che la chiave sia valida
3. Verifica credito API residuo

**Soluzione per TinyLlama:**
1. Avvia Ollama: `ollama serve`
2. Verifica modello: `ollama list`
3. Scarica se manca: `ollama pull tinyllama`

### Ricerche lente

**Sintomo:** Le query impiegano molto tempo

**Soluzione:**
1. Riduci `max_results` nelle ricerche
2. Riduci `max_depth` negli alberi di lineage
3. Abilita cache (già attiva di default)
4. Aumenta `EDC_PAGE_SIZE` nel `.env`

### Errori SSL/Certificati

**Sintomo:** "SSL Certificate Verification Failed"

**Soluzione:**
1. Nel codice è già disabilitata la verifica SSL (`ssl=False`)
2. Se persiste, controlla proxy aziendali
3. Importa certificati custom se necessario

## Statistiche e Monitoring

### Vedere le Statistiche

**In Claude Desktop:**
> get_system_statistics

**Risposta:**
```
Statistiche Sistema:
LLM Provider: claude

EDC:
- Total API calls: 47
- Cache hits: 23 (48.9%)
- API errors: 0
- Nodi creati: 156

Configurazione:
- Max tree depth: 10
- Request timeout: 30s
```

### Log Files

I log sono scritti su `stderr` e vengono catturati da Claude Desktop:

**Windows:**
`%APPDATA%\Claude\logs\mcp-server-edc-lineage.log`

**Cosa cercare nei log:**
```
[MCP] >> handle_call_tool('search_assets') chiamato
[MCP] >> Arguments: {'resource_name': 'DataPlatform', ...}
[MCP] >> search_assets completed: 15 results
```

## Estensioni Possibili

### Aggiungere un Nuovo Tool

1. **Definisci il tool in `_register_tools()`:**
```python
Tool(
    name="il_mio_tool",
    description="Cosa fa",
    inputSchema={...}
)
```

2. **Crea l'handler:**
```python
async def _handle_il_mio_tool(self, param1: str) -> List[TextContent]:
    # La tua logica
    result = "La mia risposta"
    return [TextContent(type="text", text=result)]
```

3. **Aggiungi il routing in `handle_call_tool()`:**
```python
elif name == "il_mio_tool":
    return await self._handle_il_mio_tool(**arguments)
```

### Aggiungere un Nuovo Provider LLM

1. **Crea `src/llm/nuovo_provider.py`:**
```python
from .base import BaseLLMClient

class NuovoProviderClient(BaseLLMClient):
    async def enhance_description(self, ...):
        # Implementazione
```

2. **Aggiungi in `factory.py`:**
```python
elif config.provider == LLMProvider.NUOVO:
    return NuovoProviderClient(config)
```

3. **Aggiorna enum in `settings.py`:**
```python
class LLMProvider(str, Enum):
    TINYLLAMA = "tinyllama"
    CLAUDE = "claude"
    NUOVO = "nuovo"
```

## Architettura - Visione d'Insieme

```
Claude Desktop (UI)
    |
    | JSON-RPC via stdio
    v
MCP Server (server.py)
    |
    |-- Tool Handlers
    |   |-- _handle_search_assets()
    |   |-- _handle_get_asset_details()
    |   |-- _handle_analyze_change_impact()
    |   `-- ...
    |
    |-- Lineage Builder (lineage.py)
    |   |-- build_tree()
    |   |-- get_immediate_lineage()
    |   `-- get_asset_metadata()
    |
    |-- EDC Client (client.py)
    |   |-- bulk_search_assets()
    |   |-- get_asset_details()
    |   `-- search_assets()
    |
    `-- LLM Client (factory.py)
        |-- TinyLlamaClient (tinyllama.py)
        `-- ClaudeClient (claude.py)
            |-- enhance_description()
            |-- analyze_lineage_complexity()
            |-- analyze_change_impact()
            `-- generate_change_checklist()
```

## Performance e Limiti

### Limiti Configurabili

```env
# Nel file .env
EDC_MAX_TREE_DEPTH=100        # Profondità massima albero
EDC_MAX_TOTAL_NODES=10000     # Numero massimo nodi
EDC_REQUEST_TIMEOUT=30        # Timeout chiamate (secondi)
EDC_PAGE_SIZE=20              # Risultati per pagina
```

### Best Practices

1. **Per ricerche ampie:** Usa filtri stretti (name_filter, asset_type)
2. **Per lineage profondi:** Inizia con depth=2-3, poi aumenta se serve
3. **Per performance:** Abilita cache (già attivo di default)
4. **Per costi API:** Usa TinyLlama per sviluppo, Claude per produzione

## Sicurezza

### Credenziali

- **MAI** committare il file `.env` su Git
- Usa `.env.example` come template
- In produzione, usa secret manager (Azure KeyVault, AWS Secrets, etc.)

### Rete

- Il server MCP gira in locale
- Claude Desktop si connette via stdio (non rete)
- Solo EDC e LLM API sono chiamate esterne

### Dati Sensibili

- I dati EDC non vengono salvati permanentemente
- La cache è solo in memoria (RAM)
- I log non contengono dati sensibili (solo metadati)

## FAQ - Domande Frequenti

**Q: Posso usare questo in produzione?**
A: Sì, ma testa bene prima. È consigliato per analisi interattive, non per processi batch critici.

**Q: Quanto costa Claude API?**
A: Dipende dall'uso. Circa $3-15 per 1M token. TinyLlama è gratis ma locale.

**Q: Serve installare qualcosa sul server EDC?**
A: No, usa solo le API esistenti.

**Q: Funziona con EDC Cloud (IDMC)?**
A: In teoria sì, ma servono piccole modifiche agli endpoint API.

**Q: Posso aggiungere altri cataloghi (Collibra, Atlan)?**
A: Sì, basta creare un nuovo client che implementi le stesse interfacce di `EDCClient`.

**Q: I dati vengono inviati a Claude/OpenAI?**
A: Solo se usi Claude API. Con TinyLlama tutto è locale.

**Q: Quanto è veloce?**
A: Dipende. Ricerche semplici: 1-2 sec. Alberi profondi: 10-30 sec. Claude API: 2-5 sec.

## Supporto e Contributi

### Problemi

Se incontri problemi:
1. Controlla i log
2. Verifica la configurazione
3. Prova i test: `python test_mcp_integration.py`
4. Apri una issue su GitHub (se pubblico)

### Contribuire

Per aggiungere funzionalità:
1. Fork del progetto
2. Crea branch: `git checkout -b feature/nuova-funzione`
3. Implementa e testa
4. Pull request con descrizione dettagliata

## Crediti

- **Autore:** Lorenzo - Principal Data Architect @ NTT Data Italia
- **Specializzazione:** Data Governance, Informatica EDC
- **Esperienza:** 20+ anni enterprise data management

## Licenza

MIT License - Progetto formativo per esplorare l'integrazione di tecnologie moderne (MCP, LLM) con sistemi enterprise esistenti (EDC).

---

**Ultimo Aggiornamento:** Gennaio 2025

**Versione:** 0.1.0

**Python:** 3.9+

**Piattaforme:** Windows, Linux, macOS