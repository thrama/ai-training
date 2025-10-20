# 🚀 Guida al Passaggio in Produzione

## Da Mock Mode a Produzione - Lorenzo @ NTT Data Italia

---

## 📋 Indice

1. [Architettura Sistema](#architettura)
2. [Prerequisiti](#prerequisiti)
3. [Setup Ambiente](#setup-ambiente)
4. [Avvio Server API](#avvio-server)
5. [Configurazione Interfaccia Web](#config-web)
6. [Test Funzionamento](#test)
7. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architettura Sistema {#architettura}

### Mock Mode (Attuale)
```
Browser (edc_explorer.html)
    ↓
Genera dati mock localmente
    ↓
Mostra risultati simulati
```

### Produzione
```
Browser (edc_explorer.html)
    ↓ HTTP POST
Server API Python (localhost:8080)
    ↓
Lineage Builder + EDC Client
    ↓ HTTP GET
Server EDC Informatica (edc.collaudo.servizi.allitude.it)
    ↓
Database Catalogo
```

---

## ✅ Prerequisiti {#prerequisiti}

### 1. Python e Dipendenze
```bash
# Verifica Python
python --version  # Deve essere 3.9+

# Installa dipendenze mancanti
pip install fastapi uvicorn python-multipart
```

### 2. File Configurazione
Verifica che `.env` sia configurato correttamente:

```bash
# .env
EDC_BASE_URL=https://edc.collaudo.servizi.allitude.it:9086/access
EDC_USERNAME=Administrator
EDC_PASSWORD=<tua_password>

# LLM Configuration (opzionale)
CLAUDE_API_KEY=<tua_key>  # Se usi Claude
OLLAMA_BASE_URL=http://192.168.1.17:11434  # Se usi TinyLlama
DEFAULT_LLM_PROVIDER=tinyllama
```

### 3. Test Connessione EDC
Prima di procedere, testa che la connessione EDC funzioni:

```bash
cd C:\Dev\ai-training\lineageAI
python -c "from src.config.settings import settings; print(f'EDC URL: {settings.edc_base_url}')"
```

---

## 🔧 Setup Ambiente {#setup-ambiente}

### 1. Salva i File

**File 1: `edc_api_server.py`**
```bash
# Salva nella directory principale del progetto
C:\Dev\ai-training\lineageAI\edc_api_server.py
```

**File 2: `edc_explorer.html` (aggiornato)**
```bash
# Sostituisci il file esistente in edc_explorer/
C:\Dev\ai-training\lineageAI\edc_explorer\edc_explorer.html
```

### 2. Verifica Struttura Directory
```
lineageAI/
├── .env                          ← Configurazione
├── edc_api_server.py            ← NUOVO: Server API
├── edc_explorer/
│   └── edc_explorer.html        ← AGGIORNATO: Interfaccia web
├── src/
│   ├── config/
│   │   └── settings.py
│   ├── edc/
│   │   ├── client.py
│   │   └── lineage.py
│   └── llm/
│       └── factory.py
└── venv/
```

---

## 🚀 Avvio Server API {#avvio-server}

### Opzione A: Avvio Manuale

```bash
# 1. Attiva virtual environment
cd C:\Dev\ai-training\lineageAI
venv\Scripts\activate

# 2. Avvia il server
python edc_api_server.py
```

**Output atteso:**
```
======================================================================
EDC API Server
======================================================================
EDC URL: https://edc.collaudo.servizi.allitude.it:9086/access
Default LLM: tinyllama
======================================================================

Starting server on http://localhost:8080
Documentation: http://localhost:8080/docs

Press Ctrl+C to stop
======================================================================

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
======================================================================
EDC API Server - Starting
======================================================================
Initializing LineageBuilder...
✓ LineageBuilder initialized
Initializing LLM (tinyllama)...
✓ LLM client initialized (tinyllama)
======================================================================
EDC API Server - Ready
EDC URL: https://edc.collaudo.servizi.allitude.it:9086/access
LLM Provider: tinyllama
======================================================================
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### Opzione B: Script di Avvio

Crea `start_server.bat`:
```batch
@echo off
cd /d C:\Dev\ai-training\lineageAI
call venv\Scripts\activate
python edc_api_server.py
pause
```

Poi fai doppio click su `start_server.bat`.

---

## 🌐 Configurazione Interfaccia Web {#config-web}

### 1. Apri `edc_explorer.html` con un editor

### 2. Trova questa riga (circa riga 650):
```javascript
const USE_REAL_API = true;  // ← CAMBIA QUESTO per switch mock/real
```

### 3. Modalità Disponibili

**Mock Mode** (testing senza server):
```javascript
const USE_REAL_API = false;  // Usa dati simulati
```

**Production Mode** (con server reale):
```javascript
const USE_REAL_API = true;   // Chiama il server Python
```

### 4. Verifica URL Server
```javascript
const API_BASE_URL = 'http://localhost:8080/api/mcp';
```
Se il server è su una porta diversa, cambia qui.

---

## ✅ Test Funzionamento {#test}

### Test 1: Health Check Server

Apri browser e vai a:
```
http://localhost:8080
```

**Risposta attesa:**
```json
{
  "service": "EDC Explorer API",
  "status": "running",
  "edc_url": "https://edc.collaudo.servizi.allitude.it:9086/access",
  "llm_provider": "tinyllama",
  "version": "1.0.0"
}
```

### Test 2: Documentazione API

Vai a:
```
http://localhost:8080/docs
```

Dovresti vedere Swagger UI con tutti gli endpoint disponibili.

### Test 3: Ricerca Asset

1. Apri `edc_explorer.html` nel browser
2. Vai nel **Tab System** - dovresti vedere log iniziali
3. Torna al **Tab Search**
4. Scrivi "GARANZIE" nel filtro
5. Clicca "CERCA ASSET"
6. Torna al **Tab System** - dovresti vedere:

```
[14:23:45.123] [INFO] INIZIO RICERCA ASSET
[14:23:45.124] [INFO] Mode: REAL API
[14:23:45.125] [INFO] Sending HTTP POST to http://localhost:8080/api/mcp/search_assets
🔵 API CALL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Method: search_assets
...
[14:23:45.550] [INFO] Response status: 200 OK
🟢 API RESPONSE (SUCCESS)
...
[14:23:45.600] [SUCCESS] RICERCA COMPLETATA
```

### Test 4: Controllo Console Server

Nel terminale dove hai avviato il server dovresti vedere:

```
[API] search_assets chiamato
  Resource: DataPlatform
  Filter: GARANZIE
  Type: None
  Results: 5 asset trovati
  Execution time: 234ms
INFO:     127.0.0.1:xxxxx - "POST /api/mcp/search_assets HTTP/1.1" 200 OK
```

---

## 🔍 Troubleshooting {#troubleshooting}

### Problema 1: Server non si avvia

**Errore:** `ModuleNotFoundError: No module named 'fastapi'`

**Soluzione:**
```bash
pip install fastapi uvicorn
```

---

### Problema 2: CORS Error nel browser

**Errore nel browser:** `Access to fetch blocked by CORS policy`

**Soluzione:** Verifica che il server abbia il middleware CORS abilitato (già presente nel codice).

Se il problema persiste, prova a:
1. Aprire `edc_explorer.html` usando `file:///` protocol
2. Oppure usa un server HTTP locale:
```bash
cd edc_explorer
python -m http.server 8081
# Poi apri http://localhost:8081/edc_explorer.html
```

---

### Problema 3: Timeout connessione EDC

**Errore:** `TimeoutError` o `Connection refused`

**Cause possibili:**
1. VPN non attiva
2. Firewall blocca la connessione
3. URL EDC errato nel `.env`

**Verifica:**
```bash
# Test connessione manuale
curl -k https://edc.collaudo.servizi.allitude.it:9086/access/1/catalog/data/resources
```

---

### Problema 4: Credenziali EDC errate

**Errore:** `401 Unauthorized`

**Soluzione:**
1. Verifica username/password nel `.env`
2. Rigenera il base64 dell'authorization:
```bash
echo -n "username:password" | base64
```
3. Aggiorna il file `.env`

---

### Problema 5: LLM non disponibile

**Errore:** `LLM not initialized`

**Per TinyLlama:**
```bash
# Verifica che Ollama sia in esecuzione
curl http://192.168.1.17:11434/api/tags
```

**Per Claude:**
```bash
# Verifica la API key nel .env
grep CLAUDE_API_KEY .env
```

---

## 🎯 Switch Veloce Mock ↔ Produzione

### In `edc_explorer.html`:

```javascript
// ═══════════════════════════════════════════
// MODALITÀ
// ═══════════════════════════════════════════

// 🎭 TESTING (Dati simulati, nessun server richiesto)
const USE_REAL_API = false;

// 🚀 PRODUZIONE (Server Python + EDC reale)
const USE_REAL_API = true;
```

**Cambia solo quella riga e ricarica la pagina!**

---

## 📊 Monitoring in Produzione

### Log Server
Il server logga tutto nel terminale:
- Ogni chiamata API
- Parametri ricevuti
- Risultati ottenuti
- Errori eventuali
- Tempo di esecuzione

### Log Browser
L'interfaccia web logga tutto nel **Tab System**:
- Chiamate HTTP
- Request/Response completi
- Errori di rete
- Parsing dati

---

## 🔐 Sicurezza (TODO per Deploy Esterno)

Se vuoi esporre il server oltre `localhost`:

1. **HTTPS**: Usa reverse proxy (nginx/Apache)
2. **Authentication**: Aggiungi JWT o Basic Auth
3. **CORS**: Limita origins specifici
4. **Rate Limiting**: Previeni abuse
5. **Environment**: Non committare `.env` su Git

---

## 📞 Supporto

- **Documentazione API**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/
- **Logs Server**: Terminale dove hai lanciato `python edc_api_server.py`
- **Logs Client**: Tab System nell'interfaccia web

---

## ✅ Checklist Finale

Prima di considerare il sistema "in produzione":

- [ ] Server API si avvia senza errori
- [ ] Health check ritorna 200 OK
- [ ] Ricerca asset funziona con dati reali
- [ ] Lineage tree si costruisce correttamente
- [ ] Analisi impatto genera risultati
- [ ] Checklist operativa viene creata
- [ ] Switch LLM funziona
- [ ] Log visibili in entrambi i lati (server + client)
- [ ] Nessun errore CORS nel browser
- [ ] Performance accettabile (< 2 secondi per ricerca)

---

**Sviluppato per Lorenzo - Principal Data Architect @ NTT Data Italia**

*Versione: 1.0.0 - Ottobre 2025*
