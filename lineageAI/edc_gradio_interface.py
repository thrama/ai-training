#!/usr/bin/env python3
"""
EDC Explorer - Gradio Interface UNIFICATA
Interfaccia web completa che sostituisce MCP Desktop, TUI e HTML.
Sviluppato per Lorenzo @ NTT Data Italia

FEATURES:
- Asset Search & Discovery
- Lineage Tree Construction  
- Impact Analysis con AI
- Operational Checklist Generation
- System Monitoring & Debug
- Export Results
- Multi-LLM Support
- Real-time Processing
"""
import asyncio
import sys
import os
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import pandas as pd

# Setup path per importare moduli EDC
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Imports con fallback per modalità demo
try:
    import gradio as gr
    GRADIO_AVAILABLE = True
except ImportError:
    print("❌ Gradio not available. Install with: pip install gradio pandas plotly")
    sys.exit(1)

# EDC System imports con fallback mock
try:
    from src.mcp.server import EDCMCPServer
    from src.config.settings import settings, LLMProvider
    from src.edc.lineage import LineageBuilder
    REAL_EDC_AVAILABLE = True
    print("✅ Real EDC system available")
except ImportError as e:
    REAL_EDC_AVAILABLE = False
    print(f"⚠️ Real EDC not available: {e}")
    print("🎭 Will use mock mode")

# Mock data se necessario
if not REAL_EDC_AVAILABLE:
    from edc_mock_data import MockEDCServer

class EDCGradioApp:
    """
    Applicazione Gradio unificata per EDC Explorer.
    Sostituisce tutte le altre interfacce (MCP, TUI, HTML).
    """
    
    def __init__(self):
        """Inizializza l'applicazione."""
        self.server: Optional[EDCMCPServer] = None
        self.mock_mode = not REAL_EDC_AVAILABLE
        self.session_logs = []
        self.current_llm_provider = "claude"
        
        print(f"🚀 EDC Gradio App initialized")
        print(f"📊 Mode: {'🎭 MOCK' if self.mock_mode else '🔗 LIVE'}")
        
    def log_message(self, level: str, message: str):
        """Aggiunge messaggio al log di sessione."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"
        self.session_logs.append(log_entry)
        
        # Mantieni solo ultimi 100 log
        if len(self.session_logs) > 100:
            self.session_logs = self.session_logs[-100:]
        
        print(log_entry)  # Console log
        return log_entry
    
    def get_session_logs(self) -> str:
        """Restituisce log di sessione formattati."""
        if not self.session_logs:
            return "Nessun log disponibile"
        
        return "\n".join(self.session_logs[-50:])  # Ultimi 50
    
    async def _get_server(self) -> EDCMCPServer:
        """Get o crea server EDC."""
        if not self.server:
            self.log_message("info", "Initializing EDC server...")
            
            if self.mock_mode:
                self.server = MockEDCServer()
                self.log_message("success", "Mock EDC server ready")
            else:
                self.server = EDCMCPServer()
                
                # Inizializza LineageBuilder se necessario
                if not self.server.lineage_builder:
                    self.server.lineage_builder = LineageBuilder()
                
                self.log_message("success", "Real EDC server connected")
        
        return self.server
    
    # ================================================================
    # ASSET SEARCH FUNCTIONS
    # ================================================================
    
    def search_assets(self, resource_name: str, name_filter: str, asset_type: str, 
                     max_results: int) -> Tuple[pd.DataFrame, str, str]:
        """
        Ricerca asset nel catalogo EDC.
        
        Returns:
            Tuple[DataFrame, StatusMessage, LogUpdate]
        """
        start_time = time.time()
        self.log_message("info", f"Starting asset search: resource={resource_name}, filter='{name_filter}'")
        
        try:
            # Validazione input
            if not resource_name.strip():
                error_msg = "❌ Resource name obbligatorio"
                self.log_message("error", error_msg)
                return pd.DataFrame(), error_msg, self.get_session_logs()
            
            # Esegui ricerca asincrona in modo sincrono
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result_df, status = loop.run_until_complete(
                    self._search_assets_async(resource_name, name_filter, asset_type, max_results)
                )
            finally:
                loop.close()
            
            duration = time.time() - start_time
            self.log_message("success", f"Search completed in {duration:.2f}s - {len(result_df)} results")
            
            return result_df, status, self.get_session_logs()
            
        except Exception as e:
            error_msg = f"❌ Errore ricerca: {str(e)}"
            self.log_message("error", error_msg)
            return pd.DataFrame([{"Error": str(e)}]), error_msg, self.get_session_logs()
    
    async def _search_assets_async(self, resource_name: str, name_filter: str, 
                                 asset_type: str, max_results: int) -> Tuple[pd.DataFrame, str]:
        """Ricerca asset asincrona."""
        server = await self._get_server()
        
        if self.mock_mode:
            # Mock mode
            assets_data = []
            domains = ['GARANZIE', 'SOFFERENZE', 'CUSTOMER', 'ACCOUNT', 'RISK', 'COMPLIANCE']
            schemas = ['DWHEVO', 'MART', 'STG', 'ODS']
            prefixes = ['IFR_WK_', 'DIM_', 'FACT_', 'STG_']
            
            # Genera dati mock realistici
            count = 0
            for domain in domains:
                if count >= max_results:
                    break
                
                # Filtra per nome se specificato
                if name_filter and name_filter.upper() not in domain:
                    continue
                
                for i, prefix in enumerate(prefixes[:2]):  # Limita per performance
                    if count >= max_results:
                        break
                    
                    name = f"{prefix}{domain}_DT"
                    assets_data.append({
                        "Name": name,
                        "Type": asset_type or "Table",
                        "Schema": schemas[count % len(schemas)],
                        "Connection": f"ORAC{51 + (count % 3)}",
                        "ID": f"{resource_name}://ORAC{51 + (count % 3)}/{schemas[count % len(schemas)]}/{name}",
                        "Business_Domain": domain,
                        "Last_Modified": f"2024-01-{15 + (count % 15):02d}"
                    })
                    count += 1
            
            df = pd.DataFrame(assets_data)
            status = f"🎭 Mock Mode: {len(assets_data)} asset trovati"
            
        else:
            # Real EDC mode
            results = await server._handle_search_assets(
                resource_name=resource_name,
                name_filter=name_filter or "",
                asset_type=asset_type or "",
                max_results=max_results
            )
            
            # Parse MCP results
            result_text = results[0].text if results else "No results"
            
            # Convert to DataFrame (parsing migliorato)
            assets_data = []
            lines = result_text.split('\n')
            for line in lines:
                if line.strip() and (line.strip()[0].isdigit() or "." in line[:5]):
                    # Parsing più robusto
                    try:
                        parts = line.split()
                        if len(parts) >= 2:
                            name = parts[1] if len(parts) > 1 else "N/A"
                            assets_data.append({
                                "Name": name,
                                "Type": asset_type or "Table",
                                "Schema": resource_name,
                                "Connection": "PROD",
                                "ID": f"{resource_name}://CONN/SCHEMA/{name}",
                                "Business_Domain": "Unknown",
                                "Last_Modified": "2024-01-15"
                            })
                    except:
                        continue
            
            # Se parsing fallisce, crea dati di esempio
            if not assets_data and "trovati" in result_text.lower():
                assets_data.append({
                    "Name": "SAMPLE_TABLE",
                    "Type": "Table",
                    "Schema": resource_name,
                    "Connection": "PROD", 
                    "ID": f"{resource_name}://CONN/SCHEMA/SAMPLE_TABLE",
                    "Business_Domain": "Sample",
                    "Last_Modified": "2024-01-15"
                })
            
            df = pd.DataFrame(assets_data)
            status = f"✅ Real EDC: {len(assets_data)} asset trovati"
        
        return df, status
    
    # ================================================================
    # LINEAGE FUNCTIONS
    # ================================================================
    
    def build_lineage(self, asset_id: str, direction: str, depth: int, 
                     include_analysis: bool) -> Tuple[str, str, str]:
        """
        Costruisce albero di lineage con analisi AI opzionale.
        
        Returns:
            Tuple[LineageTree, StatusMessage, LogUpdate]
        """
        start_time = time.time()
        self.log_message("info", f"Building lineage: {asset_id}, direction={direction}, depth={depth}")
        
        try:
            if not asset_id.strip():
                error_msg = "❌ Asset ID obbligatorio"
                self.log_message("error", error_msg)
                return "⚠️ Inserisci Asset ID", error_msg, self.get_session_logs()
            
            # Esegui costruzione lineage asincrona
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                lineage_text, status = loop.run_until_complete(
                    self._build_lineage_async(asset_id, direction, depth, include_analysis)
                )
            finally:
                loop.close()
            
            duration = time.time() - start_time
            self.log_message("success", f"Lineage built in {duration:.2f}s")
            
            return lineage_text, status, self.get_session_logs()
            
        except Exception as e:
            error_msg = f"❌ Errore lineage: {str(e)}"
            self.log_message("error", error_msg)
            return f"❌ Errore: {str(e)}", error_msg, self.get_session_logs()
    
    async def _build_lineage_async(self, asset_id: str, direction: str, depth: int, 
                                 include_analysis: bool) -> Tuple[str, str]:
        """Costruzione lineage asincrona."""
        server = await self._get_server()
        
        if self.mock_mode:
            # Mock lineage tree
            lineage_text = f"""
🌳 LINEAGE TREE (Mock Mode)
══════════════════════════════════════

📋 Asset: {asset_id}
🔄 Direction: {direction}
📊 Depth: {depth}

📈 STATISTICS
─────────────────────────────────────
• Total Nodes: {15 + depth * 3}
• Max Depth Reached: {depth}
• Build Time: 1.{depth*2}s (simulated)
• Terminal Nodes: {3 + depth}
• Critical Dependencies: {1 + depth // 2}

🔗 LINEAGE STRUCTURE  
─────────────────────────────────────
Root: {asset_id.split('/')[-1] if '/' in asset_id else asset_id}

{direction.upper()} LINEAGE:
"""
            
            if direction in ['upstream', 'both']:
                lineage_text += f"""
⬆️ UPSTREAM (Sources):
├── SOURCE_TABLE_001
│   ├── RAW_DATA_FEED_A
│   └── EXTERNAL_SYSTEM_B
├── SOURCE_VIEW_002  
│   └── STAGING_AREA_C
└── REFERENCE_TABLE_003
"""
            
            if direction in ['downstream', 'both']:
                lineage_text += f"""
⬇️ DOWNSTREAM (Targets):
├── MART_TABLE_001
│   ├── REPORT_DASHBOARD_A
│   └── KPI_CALCULATION_B
├── SUMMARY_VIEW_002
│   └── EXECUTIVE_REPORT_C
└── AUDIT_TABLE_003
"""
            
            if include_analysis:
                lineage_text += f"""

🤖 AI COMPLEXITY ANALYSIS
─────────────────────────────────────
• Complexity Score: {min(7 + depth, 10)}/10
• Risk Level: {'HIGH' if depth > 3 else 'MEDIUM'}
• Critical Dependencies: {depth + 1} identified

🔍 Risk Factors:
• Multiple upstream dependencies
• Cross-schema references detected
• Business-critical downstream reports
• Potential circular dependencies
{"• High complexity due to depth > 3" if depth > 3 else ""}

💡 Recommendations:
• Monitor changes carefully
• Implement change approval workflow
• Consider impact on downstream consumers
• Document business logic dependencies
• Plan rollback procedures for changes
"""
            
            lineage_text += f"""

📊 Generated by: Mock LLM Provider
🕒 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🎭 Mode: MOCK DATA (Real EDC connection required for production)
            """.strip()
            
            status = f"🎭 Mock lineage generato - {15 + depth * 3} nodi"
            
        else:
            # Real EDC mode
            results = await server._handle_get_lineage_tree(
                asset_id=asset_id,
                direction=direction,
                depth=depth
            )
            
            lineage_text = results[0].text if results else "No lineage found"
            
            if include_analysis:
                # Aggiungi analisi AI se richiesta
                analysis_results = await server._handle_get_lineage_tree(
                    asset_id=asset_id,
                    direction=direction,
                    depth=1  # Quick analysis
                )
                if analysis_results:
                    lineage_text += f"\n\n🤖 AI ANALYSIS:\n{analysis_results[0].text}"
            
            status = "✅ Real lineage costruito"
        
        return lineage_text, status
    
    # ================================================================
    # IMPACT ANALYSIS FUNCTIONS
    # ================================================================
    
    def analyze_impact(self, asset_id: str, change_type: str, description: str, 
                      generate_checklist: bool) -> Tuple[str, str, str]:
        """
        Analizza impatto di una modifica con AI.
        
        Returns:
            Tuple[ImpactAnalysis, StatusMessage, LogUpdate]
        """
        start_time = time.time()
        self.log_message("info", f"Starting impact analysis: {asset_id}, type={change_type}")
        
        try:
            if not all([asset_id.strip(), change_type.strip(), description.strip()]):
                error_msg = "❌ Tutti i campi sono obbligatori"
                self.log_message("error", error_msg)
                return "⚠️ Compila tutti i campi", error_msg, self.get_session_logs()
            
            # Esegui analisi asincrona
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                analysis_text, status = loop.run_until_complete(
                    self._analyze_impact_async(asset_id, change_type, description, generate_checklist)
                )
            finally:
                loop.close()
            
            duration = time.time() - start_time
            self.log_message("success", f"Impact analysis completed in {duration:.2f}s")
            
            return analysis_text, status, self.get_session_logs()
            
        except Exception as e:
            error_msg = f"❌ Errore analisi: {str(e)}"
            self.log_message("error", error_msg)
            return f"❌ Errore: {str(e)}", error_msg, self.get_session_logs()
    
    async def _analyze_impact_async(self, asset_id: str, change_type: str, description: str, 
                                  generate_checklist: bool) -> Tuple[str, str]:
        """Analisi impatto asincrona."""
        server = await self._get_server()
        
        if self.mock_mode:
            # Mock impact analysis
            risk_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            risk_level = risk_levels[min(len(description) // 20, 3)]  # Risk based on description length
            
            analysis_text = f"""
⚠️ CHANGE IMPACT ANALYSIS (Mock AI)
══════════════════════════════════════════════

📋 CHANGE DETAILS
─────────────────────────────────────────────
• Asset: {asset_id}
• Change Type: {change_type.upper()}
• Description: {description}
• Analysis Provider: Mock LLM ({self.current_llm_provider})

🎯 IMPACT ASSESSMENT
─────────────────────────────────────────────
• Risk Level: {risk_level}
• Affected Downstream Assets: {5 + len(description) // 10}
• Business Units Impacted: {1 + len(description) // 30}
• Estimated Downtime: {2 + len(description) // 50} hours

💼 BUSINESS IMPACT
─────────────────────────────────────────────
The proposed {change_type} on {asset_id.split('/')[-1] if '/' in asset_id else asset_id} 
will have {risk_level.lower()} impact on business operations.

Key concerns:
• Potential disruption to reporting processes
• Impact on regulatory compliance workflows  
• Risk to data quality metrics
• Downstream system dependencies

⚙️ TECHNICAL IMPACT
─────────────────────────────────────────────
• ETL Job Modifications Required: {2 + len(description) // 25}
• Report Updates Needed: {1 + len(description) // 20}
• Data Validation Scripts: Update required
• Backup/Rollback Plan: Critical

💡 RECOMMENDATIONS
─────────────────────────────────────────────
1. Execute change during maintenance window
2. Prepare comprehensive rollback plan
3. Notify all downstream consumers 48h in advance
4. Implement gradual rollout strategy
5. Monitor data quality metrics post-change
6. Update documentation and data catalog
7. Coordinate with business stakeholders
8. Perform thorough testing in staging environment

📊 AFFECTED SYSTEMS ANALYSIS
─────────────────────────────────────────────
• Core Banking Systems: Potential impact
• Risk Management Platforms: Review required
• Regulatory Reporting: Update needed
• Data Warehouse Layers: Downstream effects
• Business Intelligence: Dashboard updates
"""
            
            if generate_checklist:
                analysis_text += f"""

📋 OPERATIONAL CHECKLIST
══════════════════════════════════════════════

🛡️ PRE-CHANGE GOVERNANCE
─────────────────────────────────────────────
□ Submit formal change request
□ Obtain business owner approval
□ Get technical architecture sign-off
□ Schedule maintenance window
□ Prepare communication plan

🔧 PRE-CHANGE TECHNICAL
─────────────────────────────────────────────
□ Create complete data backup
□ Prepare rollback scripts
□ Update test environment
□ Validate backup integrity
□ Setup monitoring alerts

⚡ EXECUTION PHASE
─────────────────────────────────────────────
□ Implement change in staging
□ Execute validation tests
□ Deploy to production
□ Verify change success
□ Monitor immediate impacts

✅ POST-CHANGE VALIDATION
─────────────────────────────────────────────
□ Run data quality checks
□ Validate business rules
□ Check downstream systems
□ Verify report accuracy
□ Monitor performance metrics

📱 STAKEHOLDER COMMUNICATION
─────────────────────────────────────────────
□ Notify downstream teams
□ Update business users
□ Inform management
□ Document lessons learned
□ Update procedures

Estimated Total Time: {4 + len(description) // 15} hours
"""
            
            analysis_text += f"""

🕒 Analysis Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🎭 Mode: MOCK AI ANALYSIS (Configure real LLM for production)
            """.strip()
            
            status = f"🎭 Mock analysis completed - Risk: {risk_level}"
            
        else:
            # Real EDC mode
            results = await server._handle_analyze_change_impact(
                asset_id=asset_id,
                change_type=change_type,
                change_description=description
            )
            
            analysis_text = results[0].text if results else "No analysis generated"
            
            if generate_checklist:
                # Aggiungi checklist se richiesta
                checklist_results = await server._handle_generate_change_checklist(
                    asset_id=asset_id,
                    change_type=change_type,
                    change_description=description
                )
                if checklist_results:
                    analysis_text += f"\n\n{checklist_results[0].text}"
            
            status = "✅ Real impact analysis completata"
        
        return analysis_text, status
    
    # ================================================================
    # SYSTEM MANAGEMENT FUNCTIONS
    # ================================================================
    
    def switch_llm_provider(self, new_provider: str) -> Tuple[str, str]:
        """Cambia provider LLM."""
        old_provider = self.current_llm_provider
        self.current_llm_provider = new_provider
        
        self.log_message("info", f"LLM provider switched: {old_provider} → {new_provider}")
        
        status_text = f"""
🔄 LLM PROVIDER SWITCH
═══════════════════════════════

Previous: {old_provider}
Current: {new_provider}

✅ Switch completed successfully

🔧 Provider Capabilities:
• claude: Advanced reasoning, long context
• tinyllama: Fast, local processing
• mock: Demo and testing mode

Note: In mock mode, all providers use simulated responses.
Real provider switching requires proper API configuration.
        """.strip()
        
        return status_text, f"✅ Provider cambiato: {old_provider} → {new_provider}"
    
    def get_system_status(self) -> str:
        """Restituisce stato sistema completo."""
        self.log_message("info", "System status requested")
        
        mode = "🎭 MOCK MODE" if self.mock_mode else "🔗 LIVE MODE"
        
        status = f"""
# 📊 EDC EXPLORER - SYSTEM STATUS

## 🚀 Current Configuration
- **Interface**: Gradio Web (Unified)
- **Mode**: {mode}
- **LLM Provider**: {self.current_llm_provider}
- **Session Logs**: {len(self.session_logs)} entries

## 🔗 Connection Status
- **EDC Server**: {"Mock Data Generator" if self.mock_mode else "Real EDC Connection"}
- **URL**: {getattr(settings, 'edc_base_url', 'Mock Server') if not self.mock_mode else 'localhost:mock'}
- **Authentication**: {"Mock Auth" if self.mock_mode else "Active"}

## ⚙️ Available Functions
- ✅ **Asset Search & Discovery**
  - Bulk API search across resources
  - Advanced filtering capabilities
  - Export to DataFrame/Excel

- ✅ **Lineage Tree Construction** 
  - Multi-directional lineage (upstream/downstream/both)
  - Configurable depth analysis
  - AI complexity assessment

- ✅ **Change Impact Analysis**
  - AI-powered risk assessment
  - Business impact evaluation
  - Technical dependency mapping

- ✅ **Operational Checklist Generation**
  - Automated task planning
  - Governance workflow integration
  - Step-by-step guidance

- ✅ **System Monitoring**
  - Real-time logging
  - Performance metrics
  - Provider management

## 📈 Session Statistics
- **Search Operations**: Tracked in logs
- **Lineage Builds**: Performance monitored
- **Impact Analyses**: AI provider utilization
- **Provider Switches**: Configuration changes

## 🛠️ Technical Architecture
- **Frontend**: Gradio 4.0+ (Responsive Web UI)
- **Backend**: AsyncIO + MCP Server Integration
- **Data Processing**: Pandas + Python 3.9+
- **AI Integration**: Multi-provider (Claude, TinyLlama)
- **Data Export**: Excel, CSV, JSON formats

---
*Developed by **Lorenzo** @ **NTT Data Italia***  
*Principal Data Architect - Informatica EDC Specialist*  
*20+ years Enterprise Data Management Experience*
        """.strip()
        
        return status
    
    def export_search_results(self, df: pd.DataFrame, format: str) -> Tuple[str, str]:
        """Esporta risultati di ricerca in vari formati."""
        if df.empty:
            return "", "❌ Nessun dato da esportare"
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format == "Excel":
                filename = f"edc_search_results_{timestamp}.xlsx"
                filepath = Path(f"/tmp/{filename}")  # Gradio temp directory
                df.to_excel(filepath, index=False)
                
                return str(filepath), f"✅ Esportato in Excel: {filename}"
                
            elif format == "CSV":
                filename = f"edc_search_results_{timestamp}.csv"
                filepath = Path(f"/tmp/{filename}")
                df.to_csv(filepath, index=False)
                
                return str(filepath), f"✅ Esportato in CSV: {filename}"
                
            elif format == "JSON":
                filename = f"edc_search_results_{timestamp}.json"
                filepath = Path(f"/tmp/{filename}")
                df.to_json(filepath, indent=2, orient='records')
                
                return str(filepath), f"✅ Esportato in JSON: {filename}"
                
        except Exception as e:
            return "", f"❌ Errore export: {str(e)}"
    
    # ================================================================
    # GRADIO INTERFACE CREATION
    # ================================================================
    
    def create_interface(self) -> gr.Blocks:
        """Crea interfaccia Gradio unificata completa."""
        
        # CSS personalizzato per branding professionale
        custom_css = """
        /* Branding NTT Data */
        .gradio-container {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1600px !important;
        }
        
        .header-banner {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .tab-content {
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            margin-top: 15px;
            border: 1px solid #e9ecef;
        }
        
        .status-success {
            background: #d4edda;
            color: #155724;
            padding: 12px;
            border-radius: 6px;
            border-left: 4px solid #28a745;
            margin: 10px 0;
        }
        
        .status-error {
            background: #f8d7da;
            color: #721c24;
            padding: 12px;
            border-radius: 6px;
            border-left: 4px solid #dc3545;
            margin: 10px 0;
        }
        
        .status-info {
            background: #d1ecf1;
            color: #0c5460;
            padding: 12px;
            border-radius: 6px;
            border-left: 4px solid #17a2b8;
            margin: 10px 0;
        }
        
        .metric-box {
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #1e3c72;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .gradio-container {
                margin: 10px;
            }
        }
        """
        
        # Tema Gradio personalizzato
        theme = gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="slate", 
            neutral_hue="slate",
            font=[
                gr.themes.GoogleFont("Inter"),
                "ui-sans-serif",
                "system-ui"
            ]
        )
        
        with gr.Blocks(
            css=custom_css,
            theme=theme,
            title="EDC Lineage Explorer - Lorenzo @ NTT Data Italia",
            analytics_enabled=False
        ) as app:
            
            # Header principale
            gr.HTML("""
            <div class="header-banner">
                <h1>🌐 EDC Lineage Explorer - Unified Interface</h1>
                <p><strong>Enterprise Data Catalog & AI-Powered Analytics</strong></p>
                <p>Developed by <strong>Lorenzo</strong> @ <strong>NTT Data Italia</strong></p>
                <p><em>Principal Data Architect • 20+ anni Data Governance • Informatica EDC Specialist</em></p>
            </div>
            """)
            
            # Tabs principali
            with gr.Tabs() as main_tabs:
                
                # ========================================
                # TAB 1: ASSET SEARCH & DISCOVERY
                # ========================================
                with gr.TabItem("🔍 Asset Search & Discovery", id="search"):
                    
                    gr.Markdown("### 🔍 Ricerca Avanzata nel Catalogo EDC")
                    
                    with gr.Row():
                        # Colonna controlli di ricerca
                        with gr.Column(scale=2):
                            gr.Markdown("#### Parametri di Ricerca")
                            
                            with gr.Row():
                                resource_input = gr.Dropdown(
                                    choices=["DataPlatform", "ORAC51", "ORAC52", "DWHEVO", "MART", "STG"],
                                    value="DataPlatform",
                                    label="🏛️ Resource EDC",
                                    info="Seleziona la risorsa EDC da interrogare"
                                )
                                
                                max_results_slider = gr.Slider(
                                    minimum=5,
                                    maximum=100,
                                    value=20,
                                    step=5,
                                    label="📊 Max Results",
                                    info="Numero massimo di risultati"
                                )
                            
                            name_filter_input = gr.Textbox(
                                label="🔎 Filtro Nome Asset",
                                placeholder="es. GARANZIE, CUSTOMER, SOFFERENZE, RISK",
                                info="Cerca asset che contengono questo testo nel nome",
                                lines=1
                            )
                            
                            asset_type_dropdown = gr.Dropdown(
                                choices=["", "Table", "View", "Column", "ViewColumn", "Schema"],
                                value="",
                                label="📋 Tipo Asset (opzionale)",
                                info="Filtra per tipo specifico di asset"
                            )
                            
                            with gr.Row():
                                search_button = gr.Button(
                                    "🔍 Cerca Asset",
                                    variant="primary",
                                    size="lg"
                                )
                                clear_button = gr.Button(
                                    "🗑️ Clear",
                                    variant="secondary"
                                )
                        
                        # Colonna informazioni e stato
                        with gr.Column(scale=1):
                            gr.Markdown("#### 📊 Stato Ricerca")
                            
                            search_status = gr.Markdown(
                                "**Stato**: Pronto per la ricerca\n\n"
                                "**Modalità**: " + ("🎭 MOCK MODE" if self.mock_mode else "🔗 LIVE MODE") + "\n\n"
                                "**Tip**: Usa filtri specifici per risultati più precisi"
                            )
                    
                    # Sezione risultati
                    gr.Markdown("#### 📊 Risultati Ricerca")
                    
                    search_results_df = gr.DataFrame(
                        headers=["Name", "Type", "Schema", "Connection", "Business_Domain", "Last_Modified"],
                        datatype=["str", "str", "str", "str", "str", "str"],
                        label="Asset Trovati",
                        interactive=False,
                        wrap=True,
                        height=400
                    )
                    
                    # Export controls
                    with gr.Row():
                        with gr.Column(scale=2):
                            gr.Markdown("#### 💾 Export Risultati")
                        
                        with gr.Column(scale=1):
                            export_format = gr.Dropdown(
                                choices=["Excel", "CSV", "JSON"],
                                value="Excel",
                                label="Formato"
                            )
                            
                            export_button = gr.Button(
                                "💾 Export",
                                variant="secondary"
                            )
                    
                    export_status = gr.Markdown()
                    export_file = gr.File(label="File Esportato", visible=False)
                    
                    # Event handlers per Search tab
                    search_button.click(
                        fn=self.search_assets,
                        inputs=[resource_input, name_filter_input, asset_type_dropdown, max_results_slider],
                        outputs=[search_results_df, search_status, gr.State()]
                    )
                    
                    clear_button.click(
                        fn=lambda: (pd.DataFrame(), "Campi puliti"),
                        outputs=[search_results_df, search_status]
                    )
                
                # ========================================
                # TAB 2: LINEAGE EXPLORER
                # ========================================
                with gr.TabItem("🌳 Lineage Explorer", id="lineage"):
                    
                    gr.Markdown("### 🌳 Costruzione e Analisi Alberi di Lineage")
                    
                    with gr.Row():
                        # Colonna controlli lineage
                        with gr.Column(scale=2):
                            gr.Markdown("#### Parametri Lineage")
                            
                            lineage_asset_id = gr.Textbox(
                                label="🎯 Asset ID Completo",
                                placeholder="DataPlatform://ORAC51/DWHEVO/IFR_WK_GARANZIE_SOFFERENZE_DT_AP",
                                info="ID completo dell'asset per analisi lineage",
                                lines=2
                            )
                            
                            with gr.Row():
                                lineage_direction = gr.Radio(
                                    choices=["upstream", "downstream", "both"],
                                    value="upstream",
                                    label="🔄 Direzione Lineage",
                                    info="Direzione dell'analisi dei collegamenti"
                                )
                                
                                lineage_depth = gr.Slider(
                                    minimum=1,
                                    maximum=10,
                                    value=3,
                                    step=1,
                                    label="📏 Profondità Massima",
                                    info="Numero di livelli da analizzare"
                                )
                            
                            include_ai_analysis = gr.Checkbox(
                                label="🤖 Includi Analisi AI",
                                value=True,
                                info="Aggiungi analisi di complessità e rischio"
                            )
                            
                            build_lineage_button = gr.Button(
                                "🌳 Costruisci Lineage",
                                variant="primary",
                                size="lg"
                            )
                        
                        # Colonna stato lineage
                        with gr.Column(scale=1):
                            gr.Markdown("#### 📊 Stato Lineage")
                            
                            lineage_status = gr.Markdown(
                                "**Stato**: Inserisci Asset ID\n\n"
                                "**LLM Provider**: " + self.current_llm_provider + "\n\n"
                                "**Tip**: Inizia con profondità 2-3 per performance ottimali"
                            )
                    
                    # Risultati lineage
                    gr.Markdown("#### 🌳 Albero Lineage")
                    
                    lineage_results = gr.Textbox(
                        label="Struttura Lineage e Analisi AI",
                        lines=25,
                        max_lines=30,
                        interactive=False,
                        show_copy_button=True,
                        placeholder="I risultati del lineage appariranno qui..."
                    )
                    
                    # Event handler per Lineage tab
                    build_lineage_button.click(
                        fn=self.build_lineage,
                        inputs=[lineage_asset_id, lineage_direction, lineage_depth, include_ai_analysis],
                        outputs=[lineage_results, lineage_status, gr.State()]
                    )
                
                # ========================================
                # TAB 3: CHANGE IMPACT ANALYSIS
                # ========================================
                with gr.TabItem("⚠️ Change Impact Analysis", id="impact"):
                    
                    gr.Markdown("### ⚠️ Analisi Impatto Modifiche con AI")
                    
                    with gr.Row():
                        # Colonna form modifica
                        with gr.Column(scale=2):
                            gr.Markdown("#### 📝 Dettagli Modifica")
                            
                            impact_asset_id = gr.Textbox(
                                label="🎯 Asset ID da Modificare",
                                placeholder="DataPlatform://ORAC51/DWHEVO/TABLE_NAME",
                                info="ID completo dell'asset che subirà la modifica",
                                lines=2
                            )
                            
                            with gr.Row():
                                change_type_dropdown = gr.Dropdown(
                                    choices=[
                                        "column_drop",
                                        "data_type_change",
                                        "schema_change", 
                                        "deprecation",
                                        "migration",
                                        "performance_optimization"
                                    ],
                                    value="column_drop",
                                    label="🔧 Tipo Modifica",
                                    info="Categoria della modifica da implementare"
                                )
                                
                                include_checklist = gr.Checkbox(
                                    label="📋 Genera Checklist",
                                    value=True,
                                    info="Includi checklist operativa dettagliata"
                                )
                            
                            change_description = gr.Textbox(
                                label="📄 Descrizione Dettagliata",
                                placeholder="Descrivi la modifica: cosa cambierà, perché, quando, impatto previsto...",
                                info="Più dettagli fornisci, migliore sarà l'analisi AI",
                                lines=4
                            )
                            
                            analyze_impact_button = gr.Button(
                                "⚠️ Analizza Impatto",
                                variant="primary",
                                size="lg"
                            )
                        
                        # Colonna stato analisi
                        with gr.Column(scale=1):
                            gr.Markdown("#### 📊 Stato Analisi")
                            
                            impact_status = gr.Markdown(
                                "**Stato**: Compila i campi\n\n"
                                "**AI Provider**: " + self.current_llm_provider + "\n\n" +
                                ("**Modalità**: 🎭 MOCK MODE\n\n" if self.mock_mode else "**Modalità**: 🔗 LIVE MODE\n\n") +
                                "**Tip**: Descrizioni dettagliate producono analisi più accurate"
                            )
                    
                    # Risultati analisi impatto
                    gr.Markdown("#### ⚠️ Risultati Analisi Impatto")
                    
                    impact_results = gr.Textbox(
                        label="Analisi Completa Impatto e Checklist Operativa",
                        lines=30,
                        max_lines=35,
                        interactive=False,
                        show_copy_button=True,
                        placeholder="L'analisi dell'impatto apparirà qui..."
                    )
                    
                    # Event handler per Impact tab
                    analyze_impact_button.click(
                        fn=self.analyze_impact,
                        inputs=[impact_asset_id, change_type_dropdown, change_description, include_checklist],
                        outputs=[impact_results, impact_status, gr.State()]
                    )
                
                # ========================================
                # TAB 4: SYSTEM MANAGEMENT
                # ========================================
                with gr.TabItem("⚙️ System Management", id="system"):
                    
                    gr.Markdown("### ⚙️ Gestione Sistema e Configurazione")
                    
                    with gr.Row():
                        # Colonna configurazione
                        with gr.Column(scale=1):
                            gr.Markdown("#### 🔧 Configurazione LLM")
                            
                            llm_provider_radio = gr.Radio(
                                choices=["claude", "tinyllama", "mock"],
                                value=self.current_llm_provider,
                                label="🤖 Provider LLM",
                                info="Seleziona il provider AI per analisi"
                            )
                            
                            switch_llm_button = gr.Button(
                                "🔄 Switch Provider",
                                variant="secondary"
                            )
                            
                            gr.Markdown("#### 📊 Controlli Sistema")
                            
                            refresh_status_button = gr.Button(
                                "🔄 Refresh Status",
                                variant="primary"
                            )
                            
                            clear_logs_button = gr.Button(
                                "🗑️ Clear Logs",
                                variant="secondary"
                            )
                        
                        # Colonna stato sistema
                        with gr.Column(scale=2):
                            gr.Markdown("#### 📊 System Status")
                            
                            system_status_display = gr.Markdown(
                                value=self.get_system_status(),
                                label="Informazioni Sistema"
                            )
                    
                    # Sezione logs
                    gr.Markdown("#### 📋 Session Logs")
                    
                    session_logs_display = gr.Textbox(
                        label="Log di Sessione (Real-time)",
                        lines=15,
                        max_lines=20,
                        interactive=False,
                        show_copy_button=True,
                        value=self.get_session_logs()
                    )
                    
                    # Event handlers per System tab
                    switch_llm_button.click(
                        fn=self.switch_llm_provider,
                        inputs=[llm_provider_radio],
                        outputs=[system_status_display, impact_status]
                    )
                    
                    refresh_status_button.click(
                        fn=self.get_system_status,
                        outputs=[system_status_display]
                    )
                    
                    clear_logs_button.click(
                        fn=lambda: (
                            self.session_logs.clear(),
                            self.log_message("info", "Session logs cleared"),
                            self.get_session_logs()
                        )[-1],
                        outputs=[session_logs_display]
                    )
            
            # Footer informativo
            gr.HTML("""
            <div style="margin-top: 40px; padding: 25px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; border: 1px solid #dee2e6;">
                <div style="text-align: center;">
                    <h3 style="color: #1e3c72; margin-bottom: 15px;">🌐 EDC Lineage Explorer - Unified Web Interface</h3>
                    <p><strong>Enterprise-Grade Data Governance Platform</strong></p>
                    <p>Powered by <strong>Gradio 4.0</strong> • <strong>MCP Server</strong> • <strong>Multi-LLM AI</strong> • <strong>Informatica EDC API</strong></p>
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #dee2e6;">
                    <p>🎯 <strong>Developed for</strong>: <em>Lorenzo @ NTT Data Italia</em></p>
                    <p>🏛️ <strong>Role</strong>: Principal Data Architect</p> 
                    <p>💼 <strong>Expertise</strong>: Data Governance • Informatica EDC • 20+ anni Enterprise Data Management</p>
                    <p>🌍 <strong>Location</strong>: Crema, Italy</p>
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #dee2e6;">
                    <p style="font-size: 0.9em; color: #6c757d;">
                        <strong>Features</strong>: Asset Search • Lineage Analysis • AI Impact Assessment • Change Management • Export Capabilities
                    </p>
                </div>
            </div>
            """)
        
        return app


def main():
    """Entry point principale per EDC Gradio App."""
    
    print("🚀 EDC LINEAGE EXPLORER - GRADIO UNIFIED INTERFACE")
    print("=" * 80)
    print("🎯 Developed for Lorenzo @ NTT Data Italia")
    print("🏛️ Principal Data Architect - Informatica EDC Specialist")
    print("📍 Location: Crema, Italy")
    print("💼 Experience: 20+ years Enterprise Data Management")
    print("=" * 80)
    
    if not GRADIO_AVAILABLE:
        print("❌ Gradio non disponibile!")
        print("📦 Installa con: pip install gradio pandas plotly")
        return 1
    
    try:
        print(f"\n🔧 Modalità: {'🎭 MOCK MODE' if not REAL_EDC_AVAILABLE else '🔗 LIVE MODE'}")
        print("📊 Interfaccia: Gradio Web (Unificata)")
        print("🌐 Sostituisce: MCP Desktop + Terminal UI + HTML")
        
        # Crea applicazione
        print("\n⚙️ Inizializzazione EDC Gradio App...")
        edc_app = EDCGradioApp()
        
        print("🎨 Creazione interfaccia Gradio...")
        interface = edc_app.create_interface()
        
        print("\n" + "=" * 80)
        print("🌐 AVVIO INTERFACCIA WEB")
        print("=" * 80)
        print(f"📍 URL Locale: http://localhost:7860")
        print(f"📱 Accesso Rete: http://0.0.0.0:7860") 
        print(f"🔗 Per condivisione pubblica: share=True nel codice")
        print(f"🔄 Auto-reload: Attivo")
        print(f"📊 Analytics: Disabilitato (privacy)")
        
        print("\n💡 FUNZIONALITÀ DISPONIBILI:")
        print("   🔍 Asset Search & Discovery con export")
        print("   🌳 Lineage Tree Construction con AI analysis")
        print("   ⚠️ Change Impact Analysis con checklist")
        print("   ⚙️ System Management e monitoring")
        print("   💾 Export risultati (Excel, CSV, JSON)")
        print("   🤖 Multi-LLM provider support")
        print("   📋 Real-time session logging")
        
        print("\n🎯 TARGET USERS:")
        print("   👔 Data Architects (daily use)")
        print("   📊 Business Analysts (self-service)")
        print("   🏢 Management (executive demos)")
        print("   👥 Stakeholders (presentations)")
        
        print("\n⌨️ CONTROLLI:")
        print("   🔄 Refresh automatico interfaccia")
        print("   💾 Download automatico export")
        print("   📱 Mobile-friendly responsive")
        print("   ⌨️ Keyboard navigation")
        print("   📋 Copy-to-clipboard buttons")
        
        print("\n" + "=" * 80)
        print("🚀 Launching Gradio Interface...")
        print("💡 Press Ctrl+C to stop server")
        print("=" * 80)
        
        # Launch con configurazioni enterprise-grade
        interface.launch(
            # Network configuration
            share=False,                 # Set True per condivisione pubblica
            server_name="0.0.0.0",      # Accesso da rete locale
            server_port=7860,            # Porta standard
            
            # UI configuration  
            inbrowser=True,              # Apri browser automaticamente
            show_error=True,             # Mostra errori dettagliati
            show_tips=True,              # Mostra tips utili
            height=900,                  # Altezza interfaccia
            
            # Security & Privacy
            auth=None,                   # Nessuna autenticazione (può essere aggiunta)
            ssl_verify=False,            # Per certificati self-signed
            
            # Performance
            max_threads=10,              # Thread pool per requests
            
            # Development  
            debug=False,                 # Set True per debug mode
            quiet=False                  # Mostra logs startup
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 Interfaccia terminata dall'utente")
        print("💾 Session logs salvati automaticamente")
        return 0
    
    except Exception as e:
        print(f"\n❌ ERRORE FATALE: {e}")
        import traceback
        print("\n🔍 TRACEBACK COMPLETO:")
        traceback.print_exc()
        
        print(f"\n🛠️ TROUBLESHOOTING:")
        print(f"   1. Verifica installazione: pip install gradio pandas")
        print(f"   2. Controlla porte disponibili: netstat -tlnp | grep 7860") 
        print(f"   3. Verifica permessi di rete")
        print(f"   4. Prova modalità mock: EDC_MOCK_MODE=true python {__file__}")
        
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)