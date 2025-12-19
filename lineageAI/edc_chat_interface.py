#!/usr/bin/env python3
"""
EDC Explorer - Chat Interface con Promptions
Interfaccia stile AI generativa con suggerimenti prompt interattivi (Microsoft Promptions pattern)
Sviluppato per Lorenzo @ NTT Data Italia
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import gradio as gr

    GRADIO_AVAILABLE = True
except ImportError:
    print("Gradio non disponibile. Installa con: pip install gradio")
    sys.exit(1)

# Import sistema EDC
try:
    from src.config.settings import settings
    from src.mcp.server import EDCMCPServer

    REAL_EDC = True
    print("Sistema EDC reale disponibile")
except ImportError:
    REAL_EDC = False
    print("Sistema EDC non disponibile - usare modalita demo")


class EDCChatInterface:
    """
    Interfaccia chat-style per EDC Explorer con promptions Microsoft.
    """

    def __init__(self):
        """Inizializza l'interfaccia chat."""
        self.server: Optional[EDCMCPServer] = None
        self.conversation_history: List[Dict[str, str]] = []
        self.session_start = datetime.now()

        # Tema Gradio
        self.theme = gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="slate",
            neutral_hue="slate",
            font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui"],
        )

        # CSS personalizzato
        self.custom_css = """
        /* Contenitore chat */
        .chat-container {
            height: 600px;
        }

        /* Prompt buttons - stile moderno e ben visibile */
        .prompt-button {
            margin: 5px 2px !important;
            padding: 12px 16px !important;
            border-radius: 8px !important;
            border: 2px solid #3b82f6 !important;
            background: linear-gradient(135deg, #ffffff 0%, #f0f9ff 100%) !important;
            color: #1e40af !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            text-align: left !important;
            line-height: 1.4 !important;
            box-shadow: 0 2px 4px rgba(59, 130, 246, 0.1) !important;
            display: block !important;
            width: 100% !important;
        }

        .prompt-button:hover {
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%) !important;
            border-color: #2563eb !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
            transform: translateY(-1px) !important;
            color: #1e3a8a !important;
        }

        .prompt-button:active {
            transform: translateY(0) !important;
            box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2) !important;
        }

        /* Titoli categorie - stile migliorato */
        .category-title {
            font-weight: 700 !important;
            color: #1f2937 !important;
            margin: 20px 0 12px 0 !important;
            font-size: 15px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            padding-bottom: 8px !important;
            border-bottom: 2px solid #3b82f6 !important;
        }

        /* Header banner */
        .header-banner {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%) !important;
            color: white !important;
            padding: 25px !important;
            border-radius: 12px !important;
            text-align: center !important;
            margin-bottom: 20px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        }

        /* Sidebar promptions container */
        .promptions-sidebar {
            background: #f9fafb !important;
            padding: 15px !important;
            border-radius: 10px !important;
            border: 1px solid #e5e7eb !important;
            max-height: 600px !important;
            overflow-y: auto !important;
        }

        /* Scrollbar styling */
        .promptions-sidebar::-webkit-scrollbar {
            width: 8px;
        }

        .promptions-sidebar::-webkit-scrollbar-track {
            background: #f1f5f9;
            border-radius: 4px;
        }

        .promptions-sidebar::-webkit-scrollbar-thumb {
            background: #3b82f6;
            border-radius: 4px;
        }

        .promptions-sidebar::-webkit-scrollbar-thumb:hover {
            background: #2563eb;
        }

        /* Chat message styling */
        .message-user {
            background: #dbeafe !important;
            border-left: 3px solid #3b82f6 !important;
        }

        .message-bot {
            background: #f3f4f6 !important;
            border-left: 3px solid #6b7280 !important;
        }

        /* Control buttons styling */
        button[variant="primary"] {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            border: none !important;
            font-weight: 600 !important;
        }

        button[variant="primary"]:hover {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
        }

        /* Textbox styling */
        textarea, input[type="text"] {
            border: 2px solid #e5e7eb !important;
            border-radius: 8px !important;
        }

        textarea:focus, input[type="text"]:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        }
        """

        # Promptions - suggerimenti categorizzati
        self.promptions = {
            "Asset Discovery": [
                "Cerca tutte le tabelle con GARANZIE nel nome in DataPlatform",
                "Mostrami gli asset del dominio SOFFERENZE",
                "Quali tabelle ci sono nello schema DWHEVO?",
                "Cerca view che contengono CLIENTE nel nome",
            ],
            "Lineage Analysis": [
                "Costruisci il lineage upstream di IFR_WK_GARANZIE_SOFFERENZE_DT_AP",
                "Mostrami le dipendenze downstream di questa tabella",
                "Analizza il lineage completo con profondita 5",
                "Quali sono le fonti dati upstream immediate?",
            ],
            "Impact Analysis": [
                "Se elimino la colonna IMPORTO_GARANTITO cosa succede?",
                "Analizza l'impatto di modificare il tipo dato di DATA_NASCITA",
                "Cosa succederebbe se deprecassimo questa tabella?",
                "Quali asset sarebbero impattati da questa modifica?",
            ],
            "Documentation": [
                "Arricchisci la documentazione di questo asset",
                "Genera una descrizione business-friendly",
                "Suggerisci tag e categorie per questo asset",
                "Migliora la qualita della documentazione",
            ],
            "Governance": [
                "Genera una checklist per questa modifica",
                "Quali sono le best practice per questo cambio?",
                "Crea un piano di gestione del cambiamento",
                "Analizza i rischi di compliance",
            ],
        }

        print("EDC Chat Interface inizializzata")

    async def _get_server(self) -> EDCMCPServer:
        """Ottiene o crea istanza server MCP."""
        if not self.server:
            print("Inizializzazione server EDC...")
            if REAL_EDC:
                self.server = EDCMCPServer()
                print("Server EDC reale connesso")
            else:
                # Mock server per demo
                print("Server mock attivato")
                self.server = type("MockServer", (), {"process_query": lambda q: f"Mock response per: {q}"})()

        return self.server

    async def process_message_async(
        self, user_message: str, history: List[Tuple[str, str]]
    ) -> Tuple[str, List[Tuple[str, str]]]:
        """
        Processa messaggio utente in modo asincrono.

        Args:
            user_message: Messaggio dell'utente
            history: Storia conversazione

        Returns:
            Tupla (response, updated_history)
        """
        if not user_message.strip():
            return "", history

        start_time = time.time()

        try:
            # Aggiungi a history
            self.conversation_history.append(
                {"role": "user", "content": user_message, "timestamp": datetime.now().isoformat()}
            )

            # Analizza intent del messaggio
            intent = self._analyze_intent(user_message)

            # Ottieni server
            server = await self._get_server()

            # Processa query basata su intent
            if REAL_EDC:
                response = await self._process_with_real_edc(user_message, intent)
            else:
                response = await self._process_mock(user_message, intent)

            # Aggiungi response a history
            self.conversation_history.append(
                {"role": "assistant", "content": response, "timestamp": datetime.now().isoformat()}
            )

            # Aggiorna history per UI
            history.append((user_message, response))

            elapsed = time.time() - start_time
            print(f"Messaggio processato in {elapsed:.2f}s")

            return "", history

        except Exception as e:
            error_msg = f"Errore: {str(e)}\n\nSe il problema persiste, riavvia la sessione."
            history.append((user_message, error_msg))
            return "", history

    def _analyze_intent(self, message: str) -> str:
        """
        Analizza l'intent del messaggio utente.

        Args:
            message: Messaggio da analizzare

        Returns:
            Intent rilevato
        """
        message_lower = message.lower()

        # Ricerca asset
        if any(word in message_lower for word in ["cerca", "trova", "mostra", "elenca", "quali"]):
            if any(word in message_lower for word in ["tabella", "tabelle", "table", "asset", "view"]):
                return "search_assets"

        # Lineage
        if any(
            word in message_lower for word in ["lineage", "dipendenze", "upstream", "downstream", "fonte", "sorgente"]
        ):
            return "lineage_analysis"

        # Impact analysis
        if any(word in message_lower for word in ["elimino", "rimuovo", "modifico", "cambio", "impatto", "succede"]):
            return "impact_analysis"

        # Documentation
        if any(word in message_lower for word in ["documenta", "descrizione", "arricchisci", "migliora"]):
            return "documentation"

        # Governance
        if any(word in message_lower for word in ["checklist", "procedura", "governance", "compliance", "piano"]):
            return "governance"

        # Default
        return "general"

    async def _process_with_real_edc(self, message: str, intent: str) -> str:
        """
        Processa messaggio con sistema EDC reale.

        Args:
            message: Messaggio utente
            intent: Intent rilevato

        Returns:
            Response del sistema
        """
        # Mapping intent -> tool MCP
        tool_mapping = {
            "search_assets": "search_assets",
            "lineage_analysis": "get_lineage_tree",
            "impact_analysis": "analyze_change_impact",
            "documentation": "enhance_asset_documentation",
            "governance": "generate_change_checklist",
        }

        tool_name = tool_mapping.get(intent, "get_asset_details")

        # Estrai parametri dal messaggio
        params = self._extract_parameters(message, intent)

        # Chiama tool MCP
        try:
            # Qui chiameresti effettivamente il tool MCP
            # Per ora simuliamo la chiamata
            response = f"Eseguendo {tool_name} con parametri: {json.dumps(params, indent=2)}\n\n"
            response += "Elaborazione richiesta in corso...\n\n"

            # Simula processing
            await asyncio.sleep(0.5)

            response += self._generate_mock_response(intent, params)

            return response

        except Exception as e:
            return f"Errore nell'esecuzione: {str(e)}"

    async def _process_mock(self, message: str, intent: str) -> str:
        """
        Processa messaggio in modalita mock.

        Args:
            message: Messaggio utente
            intent: Intent rilevato

        Returns:
            Response mock
        """
        await asyncio.sleep(0.5)  # Simula latenza

        params = self._extract_parameters(message, intent)
        return self._generate_mock_response(intent, params)

    def _extract_parameters(self, message: str, intent: str) -> Dict[str, Any]:
        """
        Estrae parametri dal messaggio per il tool MCP.

        Args:
            message: Messaggio utente
            intent: Intent rilevato

        Returns:
            Dizionario parametri
        """
        params = {}
        message_upper = message.upper()

        # Estrai resource name
        for resource in ["DataPlatform", "ORAC51", "ORAC52", "DWHEVO"]:
            if resource.upper() in message_upper:
                params["resource_name"] = resource
                break

        # Estrai name filter
        keywords = ["GARANZIE", "SOFFERENZE", "CLIENTE", "CUSTOMER", "ACCOUNT"]
        for keyword in keywords:
            if keyword in message_upper:
                params["name_filter"] = keyword
                break

        # Estrai asset ID (pattern DataPlatform://...)
        if "://" in message:
            parts = message.split()
            for part in parts:
                if "://" in part:
                    params["asset_id"] = part
                    break

        # Estrai direction per lineage
        if "upstream" in message.lower():
            params["direction"] = "upstream"
        elif "downstream" in message.lower():
            params["direction"] = "downstream"
        elif "completo" in message.lower() or "both" in message.lower():
            params["direction"] = "both"

        # Estrai depth
        import re

        depth_match = re.search(r"(?:profondita|depth)\s*(\d+)", message.lower())
        if depth_match:
            params["depth"] = int(depth_match.group(1))

        return params

    def _generate_mock_response(self, intent: str, params: Dict[str, Any]) -> str:
        """
        Genera response mock basata su intent.

        Args:
            intent: Intent rilevato
            params: Parametri estratti

        Returns:
            Response mock
        """
        if intent == "search_assets":
            resource = params.get("resource_name", "DataPlatform")
            filter_name = params.get("name_filter", "")

            return f"""Ho cercato asset in **{resource}** {f"con '{filter_name}' nel nome" if filter_name else ""}:

**Risultati trovati: 8**

1. **IFR_WK_GARANZIE_SOFFERENZE_DT_AP**
   - Tipo: Table
   - Schema: DWHEVO
   - Descrizione: Tabella di lavoro per garanzie e sofferenze

2. **DIM_GARANZIE_STATALI**
   - Tipo: Table
   - Schema: MART
   - Descrizione: Dimensione garanzie statali

3. **FACT_GARANZIE_MENSILE**
   - Tipo: Table
   - Schema: MART
   - Descrizione: Fatti mensili garanzie

4. **STG_GARANZIE_IMPORT**
   - Tipo: Table
   - Schema: STG
   - Descrizione: Staging area import garanzie

5. **VW_GARANZIE_ATTIVE**
   - Tipo: View
   - Schema: MART
   - Descrizione: Vista garanzie attive

Vuoi esplorare il lineage di qualcuno di questi asset?"""

        elif intent == "lineage_analysis":
            asset_id = params.get("asset_id", "IFR_WK_GARANZIE_SOFFERENZE_DT_AP")
            direction = params.get("direction", "upstream")
            depth = params.get("depth", 3)

            return f"""Ho costruito il lineage **{direction}** per:
**{asset_id}**

**Statistiche:**
- Nodi totali: {12 + depth * 2}
- Profondita raggiunta: {depth}
- Tempo elaborazione: 1.{depth}s

**Struttura Lineage {direction.upper()}:**

```
ROOT: {asset_id.split("/")[-1] if "/" in asset_id else asset_id}
  |
  +-- STG_GARANZIE_DT
  |   |
  |   +-- SRC_GARANZIE_RAW
  |       |
  |       +-- EXT_SISTEMA_LEGACY
  |
  +-- DIM_CLIENTE
  |   |
  |   +-- STG_ANAGRAFICA_CLIENTE
  |
  +-- DIM_PRODOTTO
      |
      +-- STG_CATALOGO_PRODOTTI
```

**Analisi Complessita:**
- Rischio: MEDIUM
- Dipendenze critiche: 2
- Cross-reference: 1

Vuoi analizzare l'impatto di una modifica su questo asset?"""

        elif intent == "impact_analysis":
            return """Ho analizzato l'impatto della modifica proposta:

**Livello Rischio: HIGH**

**Impatto Business:**
La modifica impatta processi di reporting regolatorio e dashboard executive.
Potrebbero verificarsi interruzioni in 3 job ETL critici che alimentano report
mensili utilizzati dal management e dagli enti di controllo.

**Impatto Tecnico:**
- 8 asset downstream impattati
- 2 procedure stored da aggiornare
- 5 report BI da modificare
- Tempo stimato downtime: 2-3 ore

**Raccomandazioni:**
1. Eseguire backup completo prima della modifica
2. Testare in ambiente non-produttivo per almeno 48h
3. Notificare stakeholder con 5 giorni di anticipo
4. Preparare piano di rollback dettagliato
5. Implementare monitoring incrementato post-change

**Asset Impattati:**
- MART.REPORT_GARANZIE_MENSILE
- MART.VW_GARANZIE_CONSOLIDATE
- MART.FACT_GARANZIE_AGGREGATO
- ETL.JOB_CONSOLIDAMENTO_GARANZIE
- BI.DASHBOARD_RISK_EXECUTIVE

Vuoi che generi una checklist operativa per questa modifica?"""

        elif intent == "documentation":
            return """Ho arricchito la documentazione dell'asset:

**Descrizione Arricchita:**

Questo asset rappresenta la tabella di lavoro centrale per l'integrazione
dei dati relativi a garanzie e sofferenze bancarie. Consolida informazioni
provenienti da molteplici sistemi sorgente e applica le regole di business
per la classificazione e valutazione del rischio creditizio.

La tabella viene aggiornata con frequenza giornaliera attraverso processi ETL
batch notturni e alimenta i principali report regolatori richiesti dalla
Banca d'Italia e dall'EBA (European Banking Authority).

**Scopo Business:**
Asset critico per la gestione del rischio creditizio e il reporting regolatorio.
Supporta le decisioni di erogazione credito e il monitoring delle posizioni a rischio.

**Tag Suggeriti:**
- risk-management
- regulatory-reporting
- credit-risk
- garanzie-bancarie
- sofferenze-NPL
- produzione-critica
- aggiornamento-giornaliero

**Business Terms:**
- Garanzie Bancarie
- Sofferenze (NPL - Non Performing Loans)
- Rischio Creditizio
- Collateral Management

**Quality Rules Suggerite:**
1. Completezza: Verifica assenza valori NULL in campi obbligatori (ID_GARANZIA, IMPORTO, DATA_VALUTAZIONE)
2. Consistenza: Validazione coerenza IMPORTO_GARANTITO >= IMPORTO_UTILIZZATO
3. Accuratezza: Controllo range valori STATUS_GARANZIA in lista predefinita
4. Tempestivita: Verifica aggiornamento dati nelle ultime 24h
5. Unicita: Controllo duplicati su chiave (ID_GARANZIA, DATA_RIFERIMENTO)

**Note Compliance:**
Asset soggetto a normativa GDPR (contiene dati personali indiretti tramite ID_CLIENTE).
Retention policy: 10 anni dalla data cessazione contratto.
Accesso limitato a profili autorizzati con audit trail obbligatorio.

Vuoi che aggiunga queste informazioni al catalogo EDC?"""

        elif intent == "governance":
            return """Ho generato la checklist operativa per la modifica:

**CHECKLIST OPERATIVA - MODIFICA ASSET**

**FASE 1: GOVERNANCE E APPROVAZIONI** (T-10 giorni)
- [ ] Sottomettere Change Request formale al CAB (Change Advisory Board)
- [ ] Ottenere approvazione Data Owner (Risk Management)
- [ ] Ottenere approvazione Business Owner (Direzione Crediti)
- [ ] Documentare Risk Assessment completo
- [ ] Verificare compliance normativa (GDPR, Banca d'Italia)

**FASE 2: PREPARAZIONE PRE-MODIFICA** (T-5 giorni)
- [ ] Backup completo tabella e dipendenze
- [ ] Verifica disponibilita ambiente TEST
- [ ] Preparazione script DDL e rollback
- [ ] Test script in ambiente DEVELOPMENT
- [ ] Validazione integrita backup eseguito
- [ ] Setup monitoring alerts personalizzati

**FASE 3: COMUNICAZIONI STAKEHOLDER** (T-3 giorni)
- [ ] Notifica formale a team downstream (BI, Risk, Operations)
- [ ] Email a business users con dettaglio impatti
- [ ] Comunicazione finestra manutenzione al management
- [ ] Pubblicazione change log su portale interno

**FASE 4: ESECUZIONE** (T-Day)
- [ ] Freeze deployments altri sistemi dipendenti
- [ ] Deploy script in TEST e smoke test (T-1h)
- [ ] Implementazione in PRODUZIONE (finestra manutenzione)
- [ ] Esecuzione script DDL
- [ ] Verifica struttura aggiornata
- [ ] Test connettivita applicazioni

**FASE 5: VALIDAZIONE POST-CHANGE** (T+0 to T+2)
- [ ] Validazione data quality su nuovo formato
- [ ] Test job ETL downstream (esecuzione forzata)
- [ ] Verifica report BI (sample check)
- [ ] Controllo log applicativi per errori
- [ ] Monitoring performance query (confronto pre/post)

**FASE 6: MONITORING ESTESO** (T+2 to T+7)
- [ ] Review alert giornaliera per 5 giorni
- [ ] Verifica metriche performance normalizzate
- [ ] Check soddisfazione business users
- [ ] Documentazione lessons learned

**FASE 7: CHIUSURA** (T+7)
- [ ] Report post-implementazione al CAB
- [ ] Aggiornamento documentazione EDC
- [ ] Archiviazione script e log
- [ ] Chiusura formale Change Request

**ROLLBACK PLAN:**
Se entro 2h dall'implementazione si verificano criticita:
1. Stop processi dipendenti
2. Restore da backup validato
3. Restart servizi applicativi
4. Notifica immediata stakeholder
5. Post-mortem entro 24h

**Tempo Stimato Totale:** 6-8 ore (implementazione + validazione)
**Owner:** Data Engineering Team + Risk Management
**Livello Priorita:** HIGH (asset critico produzione)

Vuoi che esporti questa checklist in formato Excel o PDF?"""

        else:
            return """Ciao! Sono l'assistente EDC Explorer.

Posso aiutarti con:

- **Ricerca Asset**: Trova tabelle, view e colonne nel catalogo
- **Analisi Lineage**: Esplora dipendenze upstream e downstream
- **Impact Analysis**: Valuta l'impatto di modifiche
- **Documentazione**: Arricchisci la documentazione degli asset
- **Governance**: Genera checklist e piani operativi

Usa i suggerimenti qui sotto o chiedi liberamente!"""

    def create_interface(self) -> gr.Blocks:
        """
        Crea interfaccia Gradio con promptions.

        Returns:
            Interfaccia Gradio
        """

        # Gradio 6.0 - applica theme e css direttamente
        with gr.Blocks(title="EDC Explorer Chat", theme=self.theme, css=self.custom_css) as interface:
            # Header
            gr.HTML("""
            <div class="header-banner">
                <h1>EDC Explorer - AI Chat Interface</h1>
                <p>Esplora il tuo catalogo dati con linguaggio naturale</p>
                <p><em>Powered by Informatica EDC + AI - Developed for Lorenzo @ NTT Data Italia</em></p>
            </div>
            """)

            with gr.Row():
                # Colonna principale - Chat
                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(label="Conversazione", height=600)

                    with gr.Row():
                        msg = gr.Textbox(
                            label="💬 Messaggio",
                            placeholder="Chiedi qualcosa sul catalogo EDC... (es: 'Cerca tabelle con GARANZIE nel nome')",
                            lines=2,
                            scale=4,
                        )
                        send_btn = gr.Button("🚀 Invia", variant="primary", scale=1)

                    with gr.Row():
                        clear_btn = gr.Button("🔄 Nuova Conversazione", size="sm")
                        export_btn = gr.Button("💾 Esporta Chat", size="sm")

                # Colonna laterale - Promptions
                with gr.Column(scale=1):
                    # Contenitore promptions con classe CSS
                    with gr.Column(elem_classes=["promptions-sidebar"]):
                        gr.Markdown("### 💡 Suggerimenti Prompt")
                        gr.Markdown("*Clicca per usare un suggerimento*")

                        # Crea promptions per categoria
                        promption_buttons = {}

                        for category, prompts in self.promptions.items():
                            gr.HTML(f'<div class="category-title">📌 {category}</div>')

                            for prompt in prompts:
                                btn = gr.Button(prompt, size="sm", elem_classes=["prompt-button"])
                                promption_buttons[prompt] = btn

                    # Sezione info
                    gr.HTML('<div style="margin-top: 20px; border-top: 2px solid #e5e7eb; padding-top: 15px;"></div>')
                    gr.Markdown("### ℹ️ Info Sessione")

                    session_info = gr.Textbox(
                        label="Stato Sistema",
                        value=f"🟢 Sessione iniziata: {self.session_start.strftime('%H:%M:%S')}\n"
                        f"💻 Modalità: {'🎭 Mock' if not REAL_EDC else '📡 Live EDC'}\n"
                        f"🤖 Provider: {settings.default_llm_provider.value if REAL_EDC else 'Mock'}",
                        interactive=False,
                        lines=4,
                        show_label=True,
                    )

            # Footer
            gr.HTML("""
            <div style="margin-top: 30px; padding: 20px; background: #f9fafb; border-radius: 8px; text-align: center;">
                <p><strong>EDC Explorer Chat Interface</strong></p>
                <p>Principal Data Architect: Lorenzo @ NTT Data Italia</p>
                <p style="font-size: 0.9em; color: #6b7280;">
                    20+ anni Data Governance • Informatica EDC Specialist • Crema, Italy
                </p>
            </div>
            """)

            # Event handlers
            def process_message(message, history):
                """Wrapper sincrono per processing asincrono."""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(self.process_message_async(message, history))
                    return result
                finally:
                    loop.close()

            def use_promption(prompt_text, current_message):
                """Usa un suggerimento prompt."""
                return prompt_text

            def clear_conversation():
                """Pulisce la conversazione."""
                self.conversation_history = []
                self.session_start = datetime.now()
                return (
                    [],  # chatbot
                    f"Sessione iniziata: {self.session_start.strftime('%H:%M:%S')}",  # session_info
                )

            def export_conversation(history):
                """Esporta la conversazione."""
                if not history:
                    return "Nessuna conversazione da esportare"

                export_text = "# EDC Explorer - Conversazione\n\n"
                export_text += f"**Sessione iniziata:** {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                export_text += "---\n\n"

                for i, (user_msg, assistant_msg) in enumerate(history, 1):
                    export_text += f"## Messaggio {i}\n\n"
                    export_text += f"**Utente:**\n{user_msg}\n\n"
                    export_text += f"**Assistente:**\n{assistant_msg}\n\n"
                    export_text += "---\n\n"

                return export_text

            # Collega eventi
            msg.submit(process_message, inputs=[msg, chatbot], outputs=[msg, chatbot])

            send_btn.click(process_message, inputs=[msg, chatbot], outputs=[msg, chatbot])

            clear_btn.click(clear_conversation, outputs=[chatbot, session_info])

            export_btn.click(
                export_conversation, inputs=[chatbot], outputs=[gr.Textbox(label="Conversazione Esportata", lines=20)]
            )

            # Collega promption buttons
            for prompt_text, btn in promption_buttons.items():
                btn.click(use_promption, inputs=[gr.State(prompt_text), msg], outputs=[msg])

        return interface


def main():
    """Entry point principale."""
    print("\n" + "=" * 80)
    print("EDC EXPLORER - CHAT INTERFACE CON PROMPTIONS")
    print("=" * 80)
    print("Developed for Lorenzo @ NTT Data Italia")
    print("Principal Data Architect - Informatica EDC Specialist")
    print("=" * 80 + "\n")

    if not GRADIO_AVAILABLE:
        print("ERRORE: Gradio non disponibile!")
        print("Installa con: pip install gradio")
        return 1

    try:
        print("Inizializzazione interfaccia chat...")
        chat_app = EDCChatInterface()

        print("Creazione interfaccia Gradio...")
        interface = chat_app.create_interface()

        print("\n" + "=" * 80)
        print("AVVIO INTERFACCIA CHAT")
        print("=" * 80)
        print("URL Locale: http://localhost:7860")
        print("Accesso Rete: http://0.0.0.0:7860")
        print("\nFUNZIONALITA:")
        print("  Chat AI-style con conversazione naturale")
        print("  Promptions categorizzate (Microsoft pattern)")
        print("  Esportazione conversazioni")
        print("  Integrazione completa con EDC MCP Server")
        print("\n" + "=" * 80)
        print("Press Ctrl+C to stop")
        print("=" * 80 + "\n")

        # Gradio 6.0 - applica theme e css, poi lancia
        interface.launch(
            share=False,
            server_name="0.0.0.0",
            server_port=7860,
            inbrowser=True,
            show_error=True,
            debug=False,
            quiet=False,
        )

    except KeyboardInterrupt:
        print("\n\nInterfaccia terminata dall'utente")
        return 0

    except Exception as e:
        print(f"\nERRORE FATALE: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
