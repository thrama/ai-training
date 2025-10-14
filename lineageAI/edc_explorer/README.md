# EDC Explorer - Terminal UI Interface

**Interfaccia moderna per esplorare Informatica EDC lineage con AI analytics**

Sviluppato per Lorenzo - Principal Data Architect @ NTT Data Italia

## 🎯 Caratteristiche

### Core Features
- **🔍 Asset Search**: Ricerca intelligente nel catalogo EDC
- **🌳 Lineage Explorer**: Visualizzazione interattiva degli alberi di lineage  
- **⚠️ Impact Analysis**: Analisi AI dell'impatto delle modifiche
- **📋 Operational Checklist**: Generazione automatica di checklist operative
- **🔄 Multi-LLM Support**: Switch tra TinyLlama e Claude
- **📊 System Monitoring**: Statistiche in tempo reale

### UI Features
- **🎨 Modern Terminal UI**: Interfaccia elegante con Textual
- **📱 Responsive Layout**: Adattamento automatico alle dimensioni del terminale
- **⌨️ Keyboard Navigation**: Controllo completo da tastiera
- **🎛️ Tabbed Interface**: Organizzazione intuitiva delle funzionalità
- **📝 Real-time Logs**: Monitoraggio delle attività in tempo reale

## 🚀 Installazione

### 1. Prerequisiti

```bash
# Python 3.9+
python --version

# Dipendenze di sistema (Ubuntu/Debian)
sudo apt update
sudo apt install python3-pip python3-venv

# Terminal moderno (raccomandato)
# Windows Terminal, iTerm2, o terminale con supporto colori
```

### 2. Setup Progetto

```bash
# Naviga nella directory del progetto
cd C:\Dev\ai-training\lineageAI

# Installa dipendenze TUI
pip install textual rich

# Verifica installazione Textual
python -c "import textual; print('✅ Textual installed')"
```

### 3. Preparazione File

```bash
# Copia i file TUI nella directory principale
# edc_explorer_tui.py      (applicazione principale)
# edc_explorer.css         (styling)
# edc_tui_launcher.py      (launcher con controlli)
# edc_mock_data.py         (dati mock per testing)

# Assicurati che .env sia configurato
# (usa i tuoi file esistenti)
```

## 🎮 Utilizzo

### Avvio Standard

```bash
# Metodo 1: Launcher con controlli preliminari (raccomandato)
python edc_tui_launcher.py

# Metodo 2: Avvio diretto
python edc_explorer_tui.py

# Metodo 3: Modalità mock (per testing offline)
EDC_MOCK_MODE=true python edc_explorer_tui.py
```

### Navigazione

| Azione | Tasto |
|--------|-------|
| Cambia tab | `Tab` / `Shift+Tab` |
| Naviga widget | `↑` `↓` `←` `→` |
| Attiva button | `Enter` / `Space` |
| Esci | `Ctrl+C` |
| Scroll | `Page Up` / `Page Down` |

## 📋 Guida alle Funzionalità

### 🔍 Asset Search Tab

1. **Seleziona Resource**: DataPlatform, ORAC51, DWHEVO
2. **Filtro Nome**: Parola chiave (es: "GARANZIE")
3. **Tipo Asset**: Table, View, Column, etc.
4. **Click Search**: Visualizza risultati nella tabella
5. **Seleziona Asset**: Vedi dettagli nella colonna destra

```
💡 Tip: Usa filtri progressivi per affinare la ricerca
```

### 🌳 Lineage Explorer Tab

1. **Asset ID**: Inserisci ID completo dell'asset
2. **Direction**: Upstream, Downstream, Both
3. **Depth**: Profondità massima (1-5)
4. **Build Tree**: Genera albero lineage
5. **AI Analysis**: Visualizza analisi automatica della complessità

```
Esempio Asset ID:
DataPlatform://ORAC51/DWHEVO/IFR_WK_GARANZIE_SOFFERENZE_DT_AP
```

### ⚠️ Impact Analysis Tab

1. **Asset to Modify**: ID dell'asset da modificare
2. **Change Type**: Tipo di modifica (Column Drop, etc.)
3. **Description**: Descrizione dettagliata
4. **Analyze Impact**: Genera analisi AI
5. **Generate Checklist**: Crea checklist operativa

```
📝 Change Types disponibili:
- Column Drop: Rimozione colonna
- Data Type Change: Modifica tipo dati
- Deprecation: Deprecazione asset
- Schema Change: Modifica schema
```

### ⚙️ System Tab

- **Connection Status**: Stato connessione EDC
- **LLM Provider**: Switch tra TinyLlama e Claude
- **System Statistics**: Metriche di performance
- **System Logs**: Log in tempo reale

## 🔧 Configurazione

### Variabili Ambiente

```bash
# Modalità mock per testing
export EDC_MOCK_MODE=true

# Terminale ottimizzato
export TERM=xterm-256color
export COLORTERM=truecolor
```

### Dimensioni Terminale Raccomandate

- **Minimo**: 80x24
- **Raccomandato**: 120x40
- **Ottimale**: 140x50+

### Personalizzazione CSS

Il file `edc_explorer.css` può essere modificato per personalizzare:
- Colori del tema
- Spaziatura e layout
- Stili dei widget
- Indicatori di stato

```css
/* Esempio: Tema scuro personalizzato */
App {
    background: #1e1e1e;
}

.section-title {
    background: #0078d4;
    color: #ffffff;
}
```

## 🧪 Modalità Mock (Testing)

Per sviluppo e testing senza connessione EDC:

```bash
# Abilita mock mode
export EDC_MOCK_MODE=true
python edc_explorer_tui.py

# Oppure direttamente
python edc_mock_data.py  # Test standalone
```

### Dati Mock Disponibili
- **50+ Asset**: Tabelle, viste, colonne
- **Domini Business**: GARANZIE, SOFFERENZE, CUSTOMER, etc.
- **Schemi**: DWHEVO, ORAC51, DataPlatform
- **Lineage Simulato**: Alberi con 5-25 nodi
- **AI Analysis**: Risposte simulate di TinyLlama/Claude

## 🔍 Troubleshooting

### Problemi Comuni

#### ❌ "ModuleNotFoundError: No module named 'textual'"
```bash
pip install textual rich
# oppure
pip install -r requirements.txt
```

#### ❌ Terminale non supporta colori
```bash
# Verifica supporto colori
echo $TERM
echo $COLORTERM

# Imposta variabili
export TERM=xterm-256color
export COLORTERM=truecolor
```

#### ❌ Layout non ottimale
```bash
# Verifica dimensioni terminale
python -c "import shutil; print(shutil.get_terminal_size())"

# Ridimensiona terminale a 120x40 o maggiore
```

#### ❌ Connessione EDC fallisce
```bash
# Usa modalità mock per testing
export EDC_MOCK_MODE=true

# Verifica configurazione .env
cat .env | grep EDC_BASE_URL
```

#### ❌ LLM provider non disponibile
```bash
# Verifica Claude API
echo $CLAUDE_API_KEY

# Verifica Ollama
curl http://192.168.1.17:11434/api/tags

# Fallback a mock mode
export EDC_MOCK_MODE=true
```

### Log Debugging

```bash
# Abilita logging dettagliato
export LOG_LEVEL=DEBUG

# Redirect logs su file
python edc_explorer_tui.py 2>debug.log

# Monitor logs in tempo reale
tail -f debug.log
```

## 🎨 Screenshots (ASCII Mock)

```
┌─ EDC Lineage Explorer ──────────────────────────────────────────────────────┐
│                                                                              │
│ Asset Search │ Lineage │ Impact Analysis │ System                           │
│──────────────┴─────────┴─────────────────┴────────────────────────────────│
│                                                                              │
│ 🔍 Asset Search & Discovery                                                 │
│                                                                              │
│ [DataPlatform ▼] [Filter: GARANZIE    ] [All Types ▼] [Search]            │
│                                                                              │
│ ┌─ Search Results ──────────────────┐ ┌─ Asset Details ───────────────────┐ │
│ │ Name                   Type    ID  │ │                                   │ │
│ │ IFR_WK_GARANZIE_DT    Table   001 │ │ Asset: IFR_WK_GARANZIE_DT        │ │
│ │ IFR_WK_GARANZIE_AP    Table   002 │ │ Type: Table                       │ │
│ │ DIM_GARANZIE_CURRENT  Table   003 │ │                                   │ │
│ │ FACT_GARANZIE_SUMMARY View    004 │ │ Enhanced Description:             │ │
│ │ ▲                            ▼    │ │ Asset strategico utilizzato nel   │ │
│ └───────────────────────────────────┘ │ contesto di gestione del rischio  │ │
│                                       │ creditizio. Contiene informazioni │ │
│                                       │ aggregate essenziali per il       │ │
│                                       │ processo decisionale...           │ │
│                                       └───────────────────────────────────┘ │
│                                                                              │
└─[H] Help [Q] Quit [Tab] Navigate ─────────────────────────── 14:30:25 ─────┘
```

## 🚀 Funzionalità Avanzate

### Scripting e Automazione

```python
# Script personalizzato per batch operations
from edc_explorer_tui import EDCExplorerApp
from edc_mock_data import get_mock_server

async def batch_analysis():
    """Analizza multiple asset in batch."""
    mock_server = get_mock_server()
    
    assets_to_analyze = [
        "DataPlatform://ORAC51/DWHEVO/IFR_WK_GARANZIE_DT",
        "DataPlatform://ORAC51/DWHEVO/IFR_WK_SOFFERENZE_AP",
        "DataPlatform://ORAC51/DWHEVO/DIM_CUSTOMER_CURRENT"
    ]
    
    for asset_id in assets_to_analyze:
        impact = await mock_server.mock_impact_analysis(
            asset_id, "deprecation", "Batch analysis test"
        )
        print(f"Asset: {asset_id}")
        print(f"Impact: {impact[:100]}...")
        print("-" * 50)

# Esecuzione
import asyncio
asyncio.run(batch_analysis())
```

### Integrazione con Jupyter

```python
# notebook_integration.py
import asyncio
from IPython.display import display, HTML
from edc_mock_data import get_mock_server

class EDCNotebookHelper:
    def __init__(self):
        self.mock_server = get_mock_server()
    
    async def search_and_display(self, resource, filter_name=""):
        """Ricerca e visualizza risultati in notebook."""
        result = await self.mock_server.mock_search_assets(
            resource, filter_name, max_results=10
        )
        
        # Converti in HTML per visualizzazione
        html_result = result.replace('\n', '<br>')
        display(HTML(f"<pre>{html_result}</pre>"))
        
        return result

# Uso in Jupyter
# helper = EDCNotebookHelper()
# await helper.search_and_display("DataPlatform", "GARANZIE")
```

### Export Risultati

```python
# export_utils.py
import json
import csv
from datetime import datetime

def export_search_results(results, format="json"):
    """Esporta risultati ricerca in vari formati."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format == "json":
        filename = f"edc_search_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
    
    elif format == "csv":
        filename = f"edc_search_{timestamp}.csv"
        with open(filename, 'w', newline='') as f:
            if results:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
    
    print(f"Results exported to: {filename}")
    return filename
```

## 🔄 Roadmap & Extensioni

### Prossime Funzionalità
- **📊 Data Profiling**: Statistiche sui dataset
- **🔔 Alert System**: Notifiche per modifiche critiche
- **📈 Trend Analysis**: Analisi trend di utilizzo
- **🔒 Security Scanning**: Controlli di sicurezza
- **📱 Mobile Layout**: Supporto terminali piccoli

### Plugin System
```python
# plugin_interface.py
class EDCPlugin:
    def __init__(self, app):
        self.app = app
    
    async def on_search_complete(self, results):
        """Hook dopo ricerca completata."""
        pass
    
    async def on_asset_selected(self, asset_id):
        """Hook quando asset viene selezionato."""
        pass
    
    def add_custom_tab(self):
        """Aggiunge tab personalizzato."""
        pass

# Esempio plugin
class DataQualityPlugin(EDCPlugin):
    async def on_asset_selected(self, asset_id):
        # Analisi qualità dati automatica
        quality_score = await self.analyze_quality(asset_id)
        self.app.display_quality_score(quality_score)
```

## 📞 Supporto

### Contatti
- **Sviluppatore**: Lorenzo - Principal Data Architect @ NTT Data Italia
- **Specializzazione**: Data Governance, Informatica EDC
- **Location**: Crema, Italy

### Resources
- **Documentazione Textual**: https://textual.textualize.io/
- **Informatica EDC API**: Documentazione ufficiale
- **GitHub Issues**: Per bug report e feature request

### Community
- **Data Architecture Community**: Condivisione best practice
- **Informatica User Groups**: Forum tecnici specializzati
- **Python Data Community**: Supporto sviluppo

---

**🎯 Nota**: Questa è un'interfaccia moderna per data architect che lavorano quotidianamente con Informatica EDC. L'obiettivo è rendere l'esplorazione del lineage più efficiente e intuitiva, integrando l'intelligenza artificiale per analisi avanzate.

**🚀 Prossimi Steps**: 
1. Test con i tuoi dati EDC reali
2. Personalizzazione CSS secondo le tue preferenze  
3. Configurazione provider LLM ottimali
4. Eventuale sviluppo di plugin specifici per NTT Data

**💡 Feedback**: Ogni suggerimento per migliorare l'interfaccia è benvenuto!