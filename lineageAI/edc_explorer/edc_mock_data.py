#!/usr/bin/env python3
"""
Mock data e funzioni per testing dell'interfaccia EDC Explorer.
Utile quando EDC non è disponibile o per sviluppo offline.
"""
from typing import List, Dict, Any
import random
import json


class MockEDCServer:
    """
    Mock del server EDC per testing offline.
    Simula le risposte dei vari tool MCP.
    """
    
    def __init__(self):
        self.mock_assets = self._generate_mock_assets()
        self.connection_status = "Connected (Mock Mode)"
        self.current_llm_provider = "claude"
    
    def _generate_mock_assets(self) -> List[Dict[str, Any]]:
        """Genera asset mock realistici per il dominio banking."""
        
        schemas = ["DWHEVO", "ORAC51", "DataPlatform"]
        table_prefixes = ["IFR_WK_", "DIM_", "FACT_", "STG_", "TMP_"]
        business_domains = [
            "GARANZIE", "SOFFERENZE", "CUSTOMER", "ACCOUNT", "TRANSACTION",
            "RISK", "COMPLIANCE", "PORTFOLIO", "CREDIT", "DEPOSITS"
        ]
        table_suffixes = ["_DT", "_AP", "_HIST", "_CURRENT", "_SUMMARY"]
        
        assets = []
        
        for i in range(50):
            schema = random.choice(schemas)
            prefix = random.choice(table_prefixes)
            domain = random.choice(business_domains)
            suffix = random.choice(table_suffixes)
            
            asset_name = f"{prefix}{domain}{suffix}"
            asset_id = f"DataPlatform://{schema}/{asset_name}"
            
            # Tipo di asset
            asset_types = ["Table", "View", "Column"]
            asset_type = random.choice(asset_types)
            
            asset = {
                "id": asset_id,
                "name": asset_name,
                "classType": f"com.infa.ldm.relational.{asset_type}",
                "description": self._generate_description(domain, asset_type),
                "schema": schema,
                "business_domain": domain
            }
            
            assets.append(asset)
        
        return assets
    
    def _generate_description(self, domain: str, asset_type: str) -> str:
        """Genera descrizioni realistiche per gli asset."""
        
        descriptions = {
            "GARANZIE": "Tabella contenente informazioni sulle garanzie bancarie e collaterali",
            "SOFFERENZE": "Dati relativi ai crediti in sofferenza e non performing loans",
            "CUSTOMER": "Anagrafica clienti con informazioni demografiche e contrattuali",
            "ACCOUNT": "Conti correnti e prodotti bancari attivi",
            "TRANSACTION": "Movimenti e transazioni sui conti clienti",
            "RISK": "Metriche e indicatori di rischio creditizio",
            "COMPLIANCE": "Dati per compliance normativa e reporting regolamentare",
            "PORTFOLIO": "Composizione e performance del portafoglio crediti",
            "CREDIT": "Informazioni sui finanziamenti e linee di credito",
            "DEPOSITS": "Depositi e giacenze sui conti clienti"
        }
        
        base_desc = descriptions.get(domain, f"Tabella relativa al dominio {domain}")
        
        if asset_type == "View":
            return f"Vista aggregata: {base_desc}"
        elif asset_type == "Column":
            return f"Colonna di {base_desc.lower()}"
        else:
            return base_desc
    
    async def mock_search_assets(
        self, 
        resource_name: str,
        name_filter: str = "",
        asset_type: str = "",
        max_results: int = 10
    ) -> str:
        """Mock della ricerca asset."""
        
        # Filtra per risorsa
        filtered_assets = [
            asset for asset in self.mock_assets 
            if resource_name.upper() in asset["schema"].upper()
        ]
        
        # Filtra per nome
        if name_filter:
            filtered_assets = [
                asset for asset in filtered_assets
                if name_filter.upper() in asset["name"].upper()
            ]
        
        # Filtra per tipo
        if asset_type:
            filtered_assets = [
                asset for asset in filtered_assets
                if asset_type.lower() in asset["classType"].lower()
            ]
        
        # Limita risultati
        filtered_assets = filtered_assets[:max_results]
        
        # Costruisci risposta formattata
        result_text = f"🔍 Mock Search Results\n\n"
        result_text += f"Trovati {len(filtered_assets)} asset nella risorsa '{resource_name}'"
        
        if name_filter:
            result_text += f" con '{name_filter}' nel nome"
        if asset_type:
            result_text += f" di tipo '{asset_type}'"
        
        result_text += ":\n\n"
        
        for i, asset in enumerate(filtered_assets, 1):
            result_text += f"{i}. {asset['name']}\n"
            result_text += f"   Type: {asset['classType']}\n"
            result_text += f"   ID: {asset['id']}\n"
            result_text += f"   Description: {asset['description']}\n\n"
        
        if not filtered_assets:
            result_text += "Nessun asset trovato con i criteri specificati.\n"
            result_text += "💡 Suggerimento: prova con filtri più generici\n"
        
        result_text += f"\n📍 Modalità: MOCK DATA\n"
        result_text += f"🔄 Provider LLM: {self.current_llm_provider}\n"
        
        return result_text
    
    async def mock_get_asset_details(self, asset_id: str) -> str:
        """Mock dei dettagli asset."""
        
        # Trova asset o crea uno mock
        asset = next(
            (a for a in self.mock_assets if a["id"] == asset_id),
            None
        )
        
        if not asset:
            # Crea asset mock dal ID
            name = asset_id.split("/")[-1] if "/" in asset_id else asset_id
            asset = {
                "id": asset_id,
                "name": name,
                "classType": "com.infa.ldm.relational.Table",
                "description": f"Asset mock generato per {name}",
                "schema": "MockSchema"
            }
        
        # Genera enhancement AI mock
        ai_enhancement = self._generate_ai_enhancement(asset["name"])
        
        result_text = f"📋 Asset Details (Mock)\n\n"
        result_text += f"Asset ID: {asset['id']}\n"
        result_text += f"Name: {asset['name']}\n"
        result_text += f"Type: {asset['classType']}\n"
        result_text += f"Schema: {asset.get('schema', 'Unknown')}\n\n"
        
        result_text += f"📝 Original Description:\n{asset['description']}\n\n"
        result_text += f"✨ AI Enhanced Description:\n{ai_enhancement}\n\n"
        
        # Mock lineage info
        upstream_count = random.randint(0, 5)
        downstream_count = random.randint(0, 8)
        
        result_text += f"🔗 Lineage Information:\n"
        result_text += f"   Upstream links: {upstream_count}\n"
        result_text += f"   Downstream links: {downstream_count}\n\n"
        
        result_text += f"📊 Mock Facts: {random.randint(5, 15)} items\n"
        result_text += f"🤖 Enhanced by: {self.current_llm_provider} (Mock)\n"
        
        return result_text
    
    def _generate_ai_enhancement(self, asset_name: str) -> str:
        """Genera enhancement AI mock."""
        
        business_contexts = [
            "nel contesto di gestione del rischio creditizio",
            "per l'analisi della qualità del portafoglio",
            "nelle attività di compliance e reporting regolamentare", 
            "per la segmentazione e profilazione clienti",
            "nell'ambito del monitoraggio delle performance finanziarie"
        ]
        
        enhancements = [
            f"Asset strategico utilizzato {random.choice(business_contexts)}. "
            f"Contiene informazioni aggregate e storicizzate essenziali per il "
            f"processo decisionale e la reportistica direzionale. "
            f"L'asset supporta analisi predittive e KPI di business critici.",
            
            f"Tabella operativa fondamentale {random.choice(business_contexts)}. "
            f"Alimenta dashboard executive e processi di data governance. "
            f"Richiede particolare attenzione per data quality e lineage tracking.",
            
            f"Risorsa dati chiave {random.choice(business_contexts)}. "
            f"Integra multiple sorgenti per fornire una vista unificata del business. "
            f"Elemento centrale nell'architettura data warehouse aziendale."
        ]
        
        return random.choice(enhancements)
    
    async def mock_lineage_tree(
        self, 
        asset_id: str, 
        direction: str = "upstream",
        depth: int = 3
    ) -> str:
        """Mock della costruzione lineage tree."""
        
        result_text = f"🌳 Lineage Tree (Mock) for {asset_id}\n\n"
        result_text += f"Direction: {direction}\n"
        result_text += f"Max Depth: {depth}\n\n"
        
        # Statistiche mock
        total_nodes = random.randint(5, 25)
        max_depth_found = min(depth, random.randint(2, depth))
        build_time = round(random.uniform(0.5, 3.0), 2)
        
        result_text += f"📊 Lineage Statistics:\n"
        result_text += f"   - Total nodes: {total_nodes}\n"
        result_text += f"   - Max depth found: {max_depth_found}\n"
        result_text += f"   - Build time: {build_time}s\n"
        result_text += f"   - Terminal nodes: {random.randint(3, 8)}\n\n"
        
        # AI Complexity Analysis mock
        complexity_score = random.randint(4, 9)
        risk_levels = ["LOW", "MEDIUM", "HIGH"]
        risk_level = random.choice(risk_levels)
        
        result_text += f"🤖 AI Complexity Analysis:\n"
        result_text += f"   - Complexity Score: {complexity_score}/10\n"
        result_text += f"   - Risk Level: {risk_level}\n"
        result_text += f"   - Critical Dependencies: {random.randint(1, 4)}\n\n"
        
        # Mock lineage nodes
        result_text += f"🔗 Key Lineage Nodes:\n"
        for i in range(min(5, total_nodes)):
            level = random.randint(1, max_depth_found)
            node_name = f"MOCK_NODE_{i+1:02d}"
            result_text += f"   Level {level}: {node_name}\n"
        
        result_text += f"\n📍 Mock Mode - Real lineage requires EDC connection\n"
        
        return result_text
    
    async def mock_impact_analysis(
        self,
        asset_id: str,
        change_type: str,
        change_description: str
    ) -> str:
        """Mock dell'analisi di impatto."""
        
        risk_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        risk_weights = [0.3, 0.4, 0.2, 0.1]  # Probabilità per ogni livello
        risk_level = random.choices(risk_levels, weights=risk_weights)[0]
        
        result_text = f"⚠️ Impact Analysis (Mock)\n\n"
        result_text += f"Asset: {asset_id}\n"
        result_text += f"Change Type: {change_type}\n"
        result_text += f"Description: {change_description}\n\n"
        
        result_text += f"📊 Risk Assessment:\n"
        result_text += f"   Risk Level: {risk_level}\n"
        
        affected_assets = random.randint(2, 15)
        result_text += f"   Affected Assets: {affected_assets}\n"
        result_text += f"   Business Units Impacted: {random.randint(1, 4)}\n\n"
        
        # Business Impact mock
        business_impacts = [
            "Potenziale interruzione nei processi di reporting regolamentare. "
            "Impatto stimato sui KPI di risk management e compliance.",
            
            "Possibili ritardi nell'aggiornamento delle dashboard executive. "
            "Richiede coordinamento con i team di business intelligence.",
            
            "Modifica critica che potrebbe influenzare le metriche di qualità crediti. "
            "Necessaria validazione con i data owner del risk management."
        ]
        
        result_text += f"💼 Business Impact:\n{random.choice(business_impacts)}\n\n"
        
        # Technical Impact mock
        result_text += f"⚙️ Technical Impact:\n"
        result_text += f"Modifica di tipo '{change_type}' su asset centrale del data warehouse. "
        result_text += f"Potrebbero essere necessari aggiornamenti a {affected_assets} asset downstream "
        result_text += f"e revisione di {random.randint(3, 10)} processi ETL collegati.\n\n"
        
        # Recommendations mock
        recommendations = [
            "Eseguire backup completo prima dell'implementazione",
            "Coordinare con i team downstream per validazione impatti",
            "Implementare in ambiente test con dataset rappresentativo",
            "Pianificare rollback procedure in caso di problemi",
            "Monitorare job ETL per 48h post-implementazione",
            "Aggiornare documentazione tecnica e business"
        ]
        
        selected_recs = random.sample(recommendations, random.randint(3, 5))
        
        result_text += f"💡 Recommendations:\n"
        for i, rec in enumerate(selected_recs, 1):
            result_text += f"   {i}. {rec}\n"
        
        result_text += f"\n🤖 Analysis generated by: {self.current_llm_provider} (Mock)\n"
        result_text += f"📍 Mock Mode - Real analysis requires EDC connection\n"
        
        return result_text
    
    async def mock_generate_checklist(
        self,
        asset_id: str,
        change_type: str,
        change_description: str
    ) -> str:
        """Mock della generazione checklist."""
        
        result_text = f"📋 Operational Checklist (Mock)\n\n"
        result_text += f"Asset: {asset_id}\n"
        result_text += f"Change: {change_type} - {change_description}\n\n"
        
        # Governance Tasks
        result_text += f"🏛️ Governance & Approvals:\n"
        governance_tasks = [
            "Submit formal change request to Data Governance Committee",
            "Obtain approval from Business Data Owner",
            "Get technical sign-off from Architecture Review Board",
            "Document risk assessment in change management system"
        ]
        
        for i, task in enumerate(governance_tasks, 1):
            result_text += f"   {i}. {task}\n"
        
        result_text += f"\n🔧 Pre-Change Preparation:\n"
        pre_change_tasks = [
            "Create full backup of affected datasets",
            "Prepare rollback scripts and procedures",
            "Set up monitoring alerts for post-change validation",
            "Coordinate maintenance window with business users",
            "Verify test environment reflects production setup"
        ]
        
        for i, task in enumerate(pre_change_tasks, 1):
            result_text += f"   {i}. {task}\n"
        
        result_text += f"\n✅ Validation & Testing:\n"
        validation_tasks = [
            "Execute end-to-end data quality tests",
            "Validate business rules and calculations",
            "Check data lineage integrity post-change",
            "Perform user acceptance testing with business stakeholders",
            "Verify reporting and dashboard functionality"
        ]
        
        for i, task in enumerate(validation_tasks, 1):
            result_text += f"   {i}. {task}\n"
        
        result_text += f"\n📱 Stakeholder Communication:\n"
        communication_tasks = [
            "Notify downstream system owners 48h in advance",
            "Send change window details to business users",
            "Prepare status updates for management dashboard",
            "Document lessons learned and update procedures"
        ]
        
        for i, task in enumerate(communication_tasks, 1):
            result_text += f"   {i}. {task}\n"
        
        result_text += f"\n🤖 Checklist generated by: {self.current_llm_provider} (Mock)\n"
        result_text += f"📍 Mock Mode - Customize based on actual organizational procedures\n"
        
        return result_text
    
    async def mock_system_statistics(self) -> str:
        """Mock delle statistiche di sistema."""
        
        result_text = f"📊 System Statistics (Mock)\n\n"
        
        result_text += f"🔗 Connection Status:\n"
        result_text += f"   EDC Server: {self.connection_status}\n"
        result_text += f"   LLM Provider: {self.current_llm_provider}\n"
        result_text += f"   Mock Assets Available: {len(self.mock_assets)}\n\n"
        
        result_text += f"📈 Session Statistics:\n"
        result_text += f"   Mock API calls: {random.randint(5, 25)}\n"
        result_text += f"   Cache hits: {random.randint(10, 50)}\n"
        result_text += f"   Mock nodes created: {random.randint(20, 100)}\n"
        result_text += f"   Simulated cycles prevented: {random.randint(0, 5)}\n\n"
        
        result_text += f"⚙️ Configuration:\n"
        result_text += f"   Max tree depth: 10 (mock)\n"
        result_text += f"   Request timeout: 30s\n"
        result_text += f"   Mock mode: ACTIVE\n\n"
        
        result_text += f"💾 Mock Data:\n"
        result_text += f"   Business domains: GARANZIE, SOFFERENZE, CUSTOMER, etc.\n"
        result_text += f"   Schema types: DWHEVO, ORAC51, DataPlatform\n"
        result_text += f"   Asset types: Tables, Views, Columns\n\n"
        
        result_text += f"⚠️ Note: This is mock data for development/testing\n"
        result_text += f"Real EDC connection required for production use\n"
        
        return result_text


# Funzioni di utilità per la modalità mock
def get_mock_server() -> MockEDCServer:
    """Restituisce un'istanza del server mock."""
    return MockEDCServer()

def is_mock_mode_enabled() -> bool:
    """Verifica se la modalità mock è abilitata."""
    import os
    return os.environ.get('EDC_MOCK_MODE', 'false').lower() == 'true'

def enable_mock_mode():
    """Abilita la modalità mock."""
    import os
    os.environ['EDC_MOCK_MODE'] = 'true'

if __name__ == "__main__":
    # Test del mock server
    async def test_mock():
        mock_server = get_mock_server()
        
        print("🧪 Testing Mock EDC Server")
        print("=" * 50)
        
        # Test search
        search_result = await mock_server.mock_search_assets(
            "DataPlatform", "GARANZIE", "", 5
        )
        print(search_result)
        
        print("\n" + "=" * 50)
        
        # Test asset details
        asset_id = "DataPlatform://DWHEVO/IFR_WK_GARANZIE_DT"
        details_result = await mock_server.mock_get_asset_details(asset_id)
        print(details_result)
    
    import asyncio
    asyncio.run(test_mock())