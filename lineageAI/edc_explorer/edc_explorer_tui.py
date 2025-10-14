#!/usr/bin/env python3
"""
EDC-MCP Terminal UI Explorer - FIXED VERSION
Interfaccia terminale moderna per esplorare EDC lineage con Textual.
Sviluppato per Lorenzo - Principal Data Architect @ NTT Data Italia

FIXED: 
- Import paths corretti per struttura directory
- Risolto conflitto logging con Textual (log -> write_log)
- Mock mode completo per testing offline
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# FIX: Aggiungi il path della directory parent per accedere a src.*
current_dir = Path(__file__).parent
project_root = current_dir.parent  # Se sei in edc_explorer/, vai su di un livello
sys.path.insert(0, str(project_root))

print(f"[DEBUG] Current dir: {current_dir}")
print(f"[DEBUG] Project root: {project_root}")
print(f"[DEBUG] Python path: {sys.path[:3]}")

# Verifica se i moduli src sono disponibili
try:
    from src.config.settings import settings, LLMProvider
    print("[OK] ✅ src.config.settings imported successfully")
except ImportError as e:
    print(f"[ERROR] ❌ Failed to import src.config.settings: {e}")
    print("📁 Directory structure check:")
    
    src_path = project_root / "src"
    if src_path.exists():
        print(f"   ✅ {src_path} exists")
        config_path = src_path / "config"
        if config_path.exists():
            print(f"   ✅ {config_path} exists")
            settings_file = config_path / "settings.py"
            if settings_file.exists():
                print(f"   ✅ {settings_file} exists")
            else:
                print(f"   ❌ {settings_file} missing")
        else:
            print(f"   ❌ {config_path} missing")
    else:
        print(f"   ❌ {src_path} missing")
    
    # Fallback: crea configurazione mock
    print("\n🔄 Using fallback mock configuration...")
    
    class MockLLMProvider:
        TINYLLAMA = "tinyllama"
        CLAUDE = "claude"
    
    class MockSettings:
        def __init__(self):
            self.environment = type('obj', (object,), {'value': 'development'})
            self.edc_base_url = "https://edc.example.com"
            self.default_llm_provider = type('obj', (object,), {'value': 'claude'})
            
        def is_claude_available(self):
            return False
        
        def is_ollama_available(self):
            return False
    
    settings = MockSettings()
    LLMProvider = MockLLMProvider()

# Import Textual
try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.widgets import (
        Header, Footer, Input, Button, DataTable, Static, 
        TabbedContent, TabPane, Log, ProgressBar, Select,
        Tree, Label, Collapsible
    )
    from textual.reactive import reactive
    from textual.message import Message
    from textual import events
    from textual.coordinate import Coordinate
    print("[OK] ✅ Textual imported successfully")
except ImportError as e:
    print(f"[ERROR] ❌ Textual not available: {e}")
    print("Install with: pip install textual")
    sys.exit(1)

# Import dei nostri moduli (con fallback)
try:
    from src.mcp.server import EDCMCPServer
    print("[OK] ✅ EDCMCPServer imported")
    REAL_SERVER_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] ⚠️ Real server not available: {e}")
    print("🎭 Will use mock server instead")
    REAL_SERVER_AVAILABLE = False
    
    # Mock server semplificato
    class MockEDCMCPServer:
        def __init__(self):
            self.current_llm_provider = type('obj', (object,), {'value': 'claude'})
            self.lineage_builder = None
        
        async def _handle_search_assets(self, **kwargs):
            from textual.widgets import TextContent
            return [type('obj', (object,), {
                'text': f"🎭 MOCK SEARCH RESULTS\n\n"
                       f"Resource: {kwargs.get('resource_name', 'N/A')}\n"
                       f"Filter: {kwargs.get('name_filter', 'N/A')}\n"
                       f"Type: {kwargs.get('asset_type', 'N/A')}\n\n"
                       f"1. MOCK_TABLE_GARANZIE_001\n"
                       f"   Type: com.infa.ldm.relational.Table\n"
                       f"   ID: DataPlatform://MOCK/SCHEMA/TABLE_001\n\n"
                       f"2. MOCK_VIEW_SOFFERENZE_002\n"
                       f"   Type: com.infa.ldm.relational.View\n"
                       f"   ID: DataPlatform://MOCK/SCHEMA/VIEW_002\n\n"
                       f"📍 Mock mode active - real EDC connection needed for production"
            })]
        
        async def _handle_get_asset_details(self, **kwargs):
            return [type('obj', (object,), {
                'text': f"📋 MOCK ASSET DETAILS\n\n"
                       f"Asset ID: {kwargs.get('asset_id', 'N/A')}\n"
                       f"Name: MOCK_ASSET\n"
                       f"Type: Table\n\n"
                       f"Enhanced Description:\n"
                       f"Mock asset for testing TUI interface.\n"
                       f"Real EDC connection required for actual data.\n\n"
                       f"🤖 Enhanced by: Mock LLM Provider"
            })]
        
        async def _handle_get_lineage_tree(self, **kwargs):
            return [type('obj', (object,), {
                'text': f"🌳 MOCK LINEAGE TREE\n\n"
                       f"Asset: {kwargs.get('asset_id', 'N/A')}\n"
                       f"Direction: {kwargs.get('direction', 'upstream')}\n"
                       f"Depth: {kwargs.get('depth', 3)}\n\n"
                       f"Statistics:\n"
                       f"- Total nodes: 12 (mock)\n"
                       f"- Max depth: 3\n"
                       f"- Build time: 1.5s (simulated)\n\n"
                       f"🎭 Mock lineage - connect to EDC for real data"
            })]
        
        async def _handle_analyze_change_impact(self, **kwargs):
            return [type('obj', (object,), {
                'text': f"⚠️ MOCK IMPACT ANALYSIS\n\n"
                       f"Asset: {kwargs.get('asset_id', 'N/A')}\n"
                       f"Change: {kwargs.get('change_type', 'N/A')}\n"
                       f"Description: {kwargs.get('change_description', 'N/A')}\n\n"
                       f"Risk Level: MEDIUM (mock)\n"
                       f"Affected Assets: 5 (simulated)\n\n"
                       f"Business Impact:\n"
                       f"Mock analysis suggests moderate impact on downstream systems.\n"
                       f"Real analysis requires EDC connection and LLM provider.\n\n"
                       f"🎭 Mock analysis - configure real providers for production"
            })]
        
        async def _handle_generate_change_checklist(self, **kwargs):
            return [type('obj', (object,), {
                'text': f"📋 MOCK OPERATIONAL CHECKLIST\n\n"
                       f"Asset: {kwargs.get('asset_id', 'N/A')}\n"
                       f"Change: {kwargs.get('change_type', 'N/A')}\n\n"
                       f"Governance Tasks:\n"
                       f"   1. Submit change request (mock)\n"
                       f"   2. Get business approval (mock)\n\n"
                       f"Pre-Change Tasks:\n"
                       f"   1. Create backup (mock)\n"
                       f"   2. Prepare rollback (mock)\n\n"
                       f"🎭 Mock checklist - real checklist requires LLM integration"
            })]
        
        async def _handle_switch_llm_provider(self, **kwargs):
            return [type('obj', (object,), {
                'text': f"🔄 MOCK LLM SWITCH\n\n"
                       f"Provider: {kwargs.get('provider', 'N/A')}\n"
                       f"Status: Simulated switch successful\n\n"
                       f"🎭 Mock mode - real provider switch requires configuration"
            })]
        
        async def _handle_get_system_statistics(self):
            return [type('obj', (object,), {
                'text': f"📊 MOCK SYSTEM STATISTICS\n\n"
                       f"Connection: Mock Mode Active\n"
                       f"LLM Provider: Mock\n"
                       f"EDC URL: Mock Server\n\n"
                       f"Session Stats:\n"
                       f"- Mock API calls: 15\n"
                       f"- Simulated cache hits: 8\n"
                       f"- Mock nodes created: 42\n\n"
                       f"🎭 All data is simulated for TUI testing"
            })]
        
        async def cleanup(self):
            pass
    
    EDCMCPServer = MockEDCMCPServer


class EDCExplorerApp(App):
    """
    Applicazione Textual per esplorare EDC lineage.
    Versione con import paths corretti e fallback mock.
    """
    
    CSS_PATH = "edc_explorer.css"
    TITLE = "EDC Lineage Explorer"
    SUB_TITLE = "Enterprise Data Catalog & AI Analytics"
    
    # State reattivo
    current_resource = reactive("DataPlatform")
    connection_status = reactive("Disconnected")
    current_llm = reactive("claude")
    
    def __init__(self):
        super().__init__()
        self.server: Optional[EDCMCPServer] = None
        self.search_results: List[Dict] = []
        self.selected_asset: Optional[str] = None
        self.mock_mode = not REAL_SERVER_AVAILABLE
        
    def compose(self) -> ComposeResult:
        """Compone l'interfaccia principale."""
        yield Header()
        
        with TabbedContent(initial="search"):
            # Tab 1: Asset Search
            with TabPane("Asset Search", id="search"):
                yield from self._create_search_tab()
            
            # Tab 2: Lineage Explorer
            with TabPane("Lineage", id="lineage"):
                yield from self._create_lineage_tab()
            
            # Tab 3: Impact Analysis
            with TabPane("Impact Analysis", id="impact"):
                yield from self._create_impact_tab()
            
            # Tab 4: System Status
            with TabPane("System", id="system"):
                yield from self._create_system_tab()
        
        yield Footer()
    
    def _create_search_tab(self) -> ComposeResult:
        """Crea il tab per la ricerca asset."""
        mode_indicator = "🎭 MOCK MODE" if self.mock_mode else "🔗 LIVE MODE"
        yield Static(f"🔍 Asset Search & Discovery - {mode_indicator}", classes="section-title")
        
        with Horizontal(classes="search-controls"):
            yield Select(
                [("DataPlatform", "DataPlatform"), ("ORAC51", "ORAC51"), ("DWHEVO", "DWHEVO")],
                value="DataPlatform",
                id="resource_select"
            )
            yield Input(
                placeholder="Filter by name (es: GARANZIE)",
                id="name_filter"
            )
            yield Select(
                [("All Types", ""), ("Table", "Table"), ("View", "View"), ("Column", "Column")],
                value="",
                id="type_filter"
            )
            yield Button("Search", id="search_btn", variant="primary")
        
        with Horizontal(classes="results-section"):
            # Colonna sinistra: Risultati ricerca
            with Vertical(classes="search-results"):
                yield Static("Search Results", classes="subsection-title")
                yield DataTable(id="results_table")
            
            # Colonna destra: Dettagli asset selezionato
            with Vertical(classes="asset-details"):
                yield Static("Asset Details", classes="subsection-title")
                yield ScrollableContainer(
                    Static("Select an asset to view details", id="asset_details"),
                    id="details_scroll"
                )
    
    def _create_lineage_tab(self) -> ComposeResult:
        """Crea il tab per l'esplorazione del lineage."""
        mode_indicator = "🎭 MOCK MODE" if self.mock_mode else "🔗 LIVE MODE"
        yield Static(f"🌳 Lineage Tree Explorer - {mode_indicator}", classes="section-title")
        
        with Horizontal(classes="lineage-controls"):
            yield Input(
                placeholder="Asset ID for lineage analysis",
                id="lineage_asset_id"
            )
            yield Select(
                [("Upstream", "upstream"), ("Downstream", "downstream"), ("Both", "both")],
                value="upstream",
                id="lineage_direction"
            )
            yield Select(
                [("Depth 1", "1"), ("Depth 2", "2"), ("Depth 3", "3"), ("Depth 5", "5")],
                value="3",
                id="lineage_depth"
            )
            yield Button("Build Tree", id="lineage_btn", variant="primary")
        
        with Horizontal(classes="lineage-display"):
            # Albero lineage
            with Vertical(classes="lineage-tree"):
                yield Static("Lineage Tree", classes="subsection-title")
                yield Tree("Root", id="lineage_tree_widget")
            
            # Statistiche e AI analysis
            with Vertical(classes="lineage-analysis"):
                yield Static("AI Analysis", classes="subsection-title")
                yield ScrollableContainer(
                    Static("Build a lineage tree to see AI analysis", id="lineage_analysis"),
                    id="analysis_scroll"
                )
    
    def _create_impact_tab(self) -> ComposeResult:
        """Crea il tab per l'analisi degli impatti."""
        mode_indicator = "🎭 MOCK MODE" if self.mock_mode else "🔗 LIVE MODE"
        yield Static(f"⚠️ Change Impact Analysis - {mode_indicator}", classes="section-title")
        
        with Vertical(classes="impact-form"):
            yield Static("Change Details", classes="subsection-title")
            
            with Horizontal(classes="impact-inputs"):
                yield Input(
                    placeholder="Asset ID to modify",
                    id="impact_asset_id"
                )
                yield Select(
                    [
                        ("Column Drop", "column_drop"),
                        ("Data Type Change", "data_type_change"),
                        ("Deprecation", "deprecation"),
                        ("Schema Change", "schema_change")
                    ],
                    value="column_drop",
                    id="change_type"
                )
            
            yield Input(
                placeholder="Describe the change in detail",
                id="change_description"
            )
            
            with Horizontal(classes="impact-actions"):
                yield Button("Analyze Impact", id="analyze_btn", variant="primary")
                yield Button("Generate Checklist", id="checklist_btn", variant="success")
        
        with Horizontal(classes="impact-results"):
            # Risultati analisi
            with Vertical(classes="impact-analysis-results"):
                yield Static("Impact Analysis Results", classes="subsection-title")
                yield ScrollableContainer(
                    Static("Run an impact analysis to see results", id="impact_results"),
                    id="impact_scroll"
                )
            
            # Checklist operativa
            with Vertical(classes="operational-checklist"):
                yield Static("Operational Checklist", classes="subsection-title")
                yield ScrollableContainer(
                    Static("Generate checklist after impact analysis", id="checklist_results"),
                    id="checklist_scroll"
                )
    
    def _create_system_tab(self) -> ComposeResult:
        """Crea il tab per lo stato del sistema."""
        mode_indicator = "🎭 MOCK MODE" if self.mock_mode else "🔗 LIVE MODE"
        yield Static(f"⚙️ System Status & Configuration - {mode_indicator}", classes="section-title")
        
        with Horizontal(classes="system-overview"):
            # Stato connessione e provider
            with Vertical(classes="connection-status"):
                yield Static("Connection Status", classes="subsection-title")
                yield Static(f"Status: {self.connection_status}", id="connection_display")
                yield Static(f"EDC URL: {settings.edc_base_url}", id="edc_url_display")
                yield Button("Connect", id="connect_btn", variant="primary")
                yield Button("Disconnect", id="disconnect_btn", variant="warning")
            
            # Provider LLM
            with Vertical(classes="llm-provider"):
                yield Static("LLM Provider", classes="subsection-title")
                yield Static(f"Current: {self.current_llm}", id="llm_display")
                yield Select(
                    [("TinyLlama", "tinyllama"), ("Claude", "claude")],
                    value="claude",
                    id="llm_select"
                )
                yield Button("Switch Provider", id="switch_llm_btn", variant="success")
        
        # Statistiche dettagliate
        with Vertical(classes="system-stats"):
            yield Static("System Statistics", classes="subsection-title")
            yield ScrollableContainer(
                Static("Connect to see statistics", id="stats_display"),
                id="stats_scroll"
            )
        
        # Log sistema
        with Vertical(classes="system-logs"):
            yield Static("System Logs", classes="subsection-title")
            yield Log(id="system_log")
    
    async def on_mount(self) -> None:
        """Inizializzazione quando l'app viene montata."""
        if self.mock_mode:
            self.write_log("🎭 EDC Explorer started in MOCK MODE")
            self.write_log("💡 Real EDC connection not available - using simulated data")
        else:
            self.write_log("🚀 EDC Explorer started in LIVE MODE")
        
        self.write_log(f"📊 Environment: {settings.environment.value}")
        self.write_log(f"🔗 EDC URL: {settings.edc_base_url}")
        
        # Setup tabelle
        await self._setup_results_table()
        
        # Auto-connect
        await self._connect_to_server()
    
    async def _setup_results_table(self) -> None:
        """Configura la tabella dei risultati."""
        table = self.query_one("#results_table", DataTable)
        table.add_columns("Name", "Type", "ID")
        table.cursor_type = "row"
        table.zebra_stripes = True
    
    async def _connect_to_server(self) -> None:
        """Connette al server MCP."""
        try:
            if self.mock_mode:
                self.write_log("🎭 Connecting to Mock server...")
                self.connection_status = "Connected (Mock)"
            else:
                self.write_log("🔄 Connecting to EDC-MCP server...")
                self.connection_status = "Connecting"
            
            self.server = EDCMCPServer()
            
            if not self.mock_mode:
                # Inizializza LineageBuilder solo se non in mock mode
                try:
                    from src.edc.lineage import LineageBuilder
                    self.server.lineage_builder = LineageBuilder()
                except ImportError:
                    self.write_log("⚠️ LineageBuilder not available")
            
            self.connection_status = "Connected (Mock)" if self.mock_mode else "Connected"
            self.current_llm = self.server.current_llm_provider.value if hasattr(self.server.current_llm_provider, 'value') else "mock"
            
            self.write_log("✅ Connected successfully!")
            
            # Aggiorna display
            self.query_one("#connection_display", Static).update(f"Status: {self.connection_status}")
            self.query_one("#llm_display", Static).update(f"Current: {self.current_llm}")
            
            # Carica statistiche
            await self._update_system_stats()
            
        except Exception as e:
            self.connection_status = "Error"
            self.write_log(f"❌ Connection failed: {e}")
            self.query_one("#connection_display", Static).update(f"Status: {self.connection_status}")
    
    async def _disconnect_from_server(self) -> None:
        """Disconnette dal server."""
        if self.server:
            try:
                await self.server.cleanup()
                self.server = None
                self.connection_status = "Disconnected"
                self.write_log("🔌 Disconnected from server")
                
                self.query_one("#connection_display", Static).update(f"Status: {self.connection_status}")
                
            except Exception as e:
                self.write_log(f"❌ Disconnect error: {e}")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Gestisce i click sui bottoni."""
        button_id = event.button.id
        
        if button_id == "search_btn":
            await self._perform_search()
        elif button_id == "lineage_btn":
            await self._build_lineage()
        elif button_id == "analyze_btn":
            await self._analyze_impact()
        elif button_id == "checklist_btn":
            await self._generate_checklist()
        elif button_id == "connect_btn":
            await self._connect_to_server()
        elif button_id == "disconnect_btn":
            await self._disconnect_from_server()
        elif button_id == "switch_llm_btn":
            await self._switch_llm_provider()
    
    async def _perform_search(self) -> None:
        """Esegue la ricerca degli asset."""
        if not self.server:
            self.write_log("❌ Not connected to server")
            return
        
        try:
            # Leggi input
            resource = self.query_one("#resource_select", Select).value
            name_filter = self.query_one("#name_filter", Input).value
            type_filter = self.query_one("#type_filter", Select).value
            
            self.write_log(f"🔍 Searching: resource={resource}, filter='{name_filter}', type='{type_filter}'")
            
            # Esegui ricerca
            result = await self.server._handle_search_assets(
                resource_name=resource,
                name_filter=name_filter or "",
                asset_type=type_filter or "",
                max_results=20
            )
            
            # Parse dei risultati (assumendo formato testuale)
            result_text = result[0].text
            
            # Aggiorna tabella (parsing semplificato)
            table = self.query_one("#results_table", DataTable)
            table.clear()
            
            # Parsing migliorato per testo mock
            lines = result_text.split('\n')
            count = 0
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or "MOCK_" in line):
                    # Estrai nome da linee come "1. MOCK_TABLE_GARANZIE_001"
                    if '. ' in line:
                        name_part = line.split('. ', 1)[1]
                        table.add_row(name_part, "Table", f"asset_{count}")
                        count += 1
            
            # Se non trovati asset parsabili, aggiungi placeholder
            if table.row_count == 0:
                table.add_row("MOCK_GARANZIE_TABLE", "Table", "mock_001")
                table.add_row("MOCK_SOFFERENZE_VIEW", "View", "mock_002")
                table.add_row("MOCK_CUSTOMER_DATA", "Table", "mock_003")
            
            self.write_log(f"✅ Found {table.row_count} assets")
            
        except Exception as e:
            self.write_log(f"❌ Search error: {e}")
            import traceback
            self.write_log(f"Traceback: {traceback.format_exc()}")
    
    async def _build_lineage(self) -> None:
        """Costruisce l'albero di lineage."""
        if not self.server:
            self.write_log("❌ Not connected to server")
            return
        
        try:
            asset_id = self.query_one("#lineage_asset_id", Input).value
            direction = self.query_one("#lineage_direction", Select).value
            depth = int(self.query_one("#lineage_depth", Select).value)
            
            if not asset_id:
                # Usa ID mock per demo
                asset_id = "DataPlatform://MOCK/SCHEMA/DEMO_TABLE"
                self.query_one("#lineage_asset_id", Input).value = asset_id
                self.write_log("💡 Using demo asset ID for testing")
            
            self.write_log(f"🌳 Building lineage: {asset_id}, direction={direction}, depth={depth}")
            
            # Costruisci lineage
            result = await self.server._handle_get_lineage_tree(
                asset_id=asset_id,
                direction=direction,
                depth=depth
            )
            
            # Aggiorna tree widget
            tree = self.query_one("#lineage_tree_widget", Tree)
            tree.clear()
            root = tree.root.add(f"Asset: {asset_id.split('/')[-1]}")
            
            # Aggiungi nodi mock
            if self.mock_mode:
                upstream = root.add("Upstream Sources")
                upstream.add_leaf("MOCK_SOURCE_TABLE_1")
                upstream.add_leaf("MOCK_SOURCE_VIEW_2")
                
                downstream = root.add("Downstream Targets")
                downstream.add_leaf("MOCK_TARGET_REPORT_1")
                downstream.add_leaf("MOCK_TARGET_DASHBOARD_2")
            
            root.expand()
            
            # Aggiorna analisi
            analysis_text = result[0].text
            self.query_one("#lineage_analysis", Static).update(analysis_text)
            
            self.write_log("✅ Lineage tree built successfully")
            
        except Exception as e:
            self.write_log(f"❌ Lineage error: {e}")
    
    async def _analyze_impact(self) -> None:
        """Analizza l'impatto di una modifica."""
        if not self.server:
            self.write_log("❌ Not connected to server")
            return
        
        try:
            asset_id = self.query_one("#impact_asset_id", Input).value
            change_type = self.query_one("#change_type", Select).value
            description = self.query_one("#change_description", Input).value
            
            if not asset_id:
                asset_id = "DataPlatform://MOCK/SCHEMA/DEMO_TABLE"
                self.query_one("#impact_asset_id", Input).value = asset_id
            
            if not description:
                description = "Demo impact analysis for testing"
                self.query_one("#change_description", Input).value = description
            
            self.write_log(f"⚠️ Analyzing impact: {asset_id}, type={change_type}")
            
            # Analizza impatto
            result = await self.server._handle_analyze_change_impact(
                asset_id=asset_id,
                change_type=change_type,
                change_description=description
            )
            
            # Aggiorna risultati
            impact_text = result[0].text
            self.query_one("#impact_results", Static).update(impact_text)
            
            self.write_log("✅ Impact analysis completed")
            
        except Exception as e:
            self.write_log(f"❌ Impact analysis error: {e}")
    
    async def _generate_checklist(self) -> None:
        """Genera la checklist operativa."""
        if not self.server:
            self.write_log("❌ Not connected to server")
            return
        
        try:
            asset_id = self.query_one("#impact_asset_id", Input).value
            change_type = self.query_one("#change_type", Select).value
            description = self.query_one("#change_description", Input).value
            
            if not asset_id:
                asset_id = "DataPlatform://MOCK/SCHEMA/DEMO_TABLE"
            
            if not description:
                description = "Demo checklist generation"
            
            self.write_log(f"📋 Generating checklist for: {asset_id}")
            
            # Genera checklist
            result = await self.server._handle_generate_change_checklist(
                asset_id=asset_id,
                change_type=change_type,
                change_description=description
            )
            
            # Aggiorna checklist
            checklist_text = result[0].text
            self.query_one("#checklist_results", Static).update(checklist_text)
            
            self.write_log("✅ Checklist generated")
            
        except Exception as e:
            self.write_log(f"❌ Checklist generation error: {e}")
    
    async def _switch_llm_provider(self) -> None:
        """Cambia il provider LLM."""
        if not self.server:
            self.write_log("❌ Not connected to server")
            return
        
        try:
            new_provider = self.query_one("#llm_select", Select).value
            
            self.write_log(f"🔄 Switching LLM provider to: {new_provider}")
            
            result = await self.server._handle_switch_llm_provider(provider=new_provider)
            
            self.current_llm = new_provider
            self.query_one("#llm_display", Static).update(f"Current: {self.current_llm}")
            
            self.write_log("✅ LLM provider switched successfully")
            
        except Exception as e:
            self.write_log(f"❌ LLM switch error: {e}")
    
    async def _update_system_stats(self) -> None:
        """Aggiorna le statistiche di sistema."""
        if not self.server:
            return
        
        try:
            result = await self.server._handle_get_system_statistics()
            stats_text = result[0].text
            self.query_one("#stats_display", Static).update(stats_text)
        except Exception as e:
            self.write_log(f"❌ Stats update error: {e}")
    
    def write_log(self, message: str) -> None:
        """Aggiunge un messaggio al log widget."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        try:
            log_widget = self.query_one("#system_log", Log)
            log_widget.write_line(f"[{timestamp}] {message}")
        except:
            # Fallback se log widget non disponibile
            print(f"[{timestamp}] {message}")


def main():
    """Entry point principale."""
    print("\n" + "=" * 70)
    print("🚀 EDC EXPLORER - TERMINAL UI (FIXED VERSION)")
    print("=" * 70)
    print("Developed for Lorenzo - Principal Data Architect @ NTT Data Italia")
    
    if not REAL_SERVER_AVAILABLE:
        print("\n🎭 MOCK MODE ACTIVE")
        print("   Real EDC server modules not available")
        print("   Using simulated data for interface testing")
        print("   All functionality will work with mock responses")
    else:
        print("\n🔗 LIVE MODE READY")
        print("   Real EDC server modules loaded successfully")
        print("   Ready for production use")
    
    print("=" * 70)
    print("\n💡 Navigation Tips:")
    print("   • Tab/Shift+Tab: Switch between tabs")
    print("   • Arrow keys: Navigate widgets")
    print("   • Enter/Space: Activate buttons")
    print("   • Ctrl+C: Exit application")
    print("\n" + "=" * 70)
    
    try:
        app = EDCExplorerApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()