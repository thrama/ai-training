"""
MCP Server principale per l'integrazione EDC-LLM.
Combina la potenza del lineage EDC con l'intelligenza dei LLM multipli.
"""
import asyncio
import time
import logging  # ← AGGIUNGI QUESTA RIGA
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict

from mcp.server import Server
from mcp.types import Tool, TextContent

from ..config.settings import settings, LLMProvider
from ..edc.lineage import LineageBuilder
from ..edc.models import (
    TreeNode, LineageDirection, ImpactAnalysisRequest, 
    ImpactAnalysisResult, EnhancementRequest, EnhancementResult
)
from ..llm.factory import LLMFactory, LLMConfig


class EDCMCPServer:
    """
    Server MCP che espone funzionalità EDC arricchite con LLM.
    Mantiene la compatibilità con la logica TreeBuilder esistente.
    """
    
    def __init__(self):
        """Inizializza il server MCP."""
        self.server = Server("edc-lineage-assistant")
        self.lineage_builder: Optional[LineageBuilder] = None
        self.llm_client = None
        self.current_llm_provider = settings.default_llm_provider
        
        # Inizializza LLM client
        self._initialize_llm()
        
        # Registra tools MCP
        self._register_tools()
    
    def _initialize_llm(self) -> None:
        """Inizializza il client LLM basato sulla configurazione."""
        if self.current_llm_provider == LLMProvider.TINYLLAMA:
            llm_config = LLMConfig(
                provider=LLMProvider.TINYLLAMA,
                model_name=settings.tinyllama_model,
                base_url=settings.ollama_base_url,
                max_tokens=settings.tinyllama_max_tokens,
                temperature=settings.tinyllama_temperature
            )
        elif self.current_llm_provider == LLMProvider.CLAUDE:
            if not settings.claude_api_key:
                raise ValueError("Claude API key non configurata")
            
            llm_config = LLMConfig(
                provider=LLMProvider.CLAUDE,
                model_name=settings.claude_model,
                api_key=settings.claude_api_key,
                max_tokens=settings.claude_max_tokens,
                temperature=settings.claude_temperature
            )
        else:
            raise ValueError(f"Provider LLM non supportato: {self.current_llm_provider}")
        
        self.llm_client = LLMFactory.create_llm_client(llm_config)
        print(f"[MCP] LLM inizializzato: {self.current_llm_provider.value}")
    
    def _register_tools(self) -> None:
        """Registra tutti i tools MCP."""
        
        # ====================================
        # ASSET INFORMATION TOOLS
        # ====================================
        
        @self.server.call_tool()
        async def get_asset_details(asset_id: str) -> List[TextContent]:
            """
            Recupera informazioni complete su un asset specifico con enhancement AI.
            
            Args:
                asset_id: Identificativo dell'asset EDC
            """
            try:
                if not self.lineage_builder:
                    self.lineage_builder = LineageBuilder()
                
                # Recupera metadati base
                metadata = await self.lineage_builder.get_asset_metadata(asset_id)
                
                # Enhancement con LLM se descrizione mancante/povera
                enhanced_description = metadata['description']
                if not metadata['description'] or len(metadata['description']) < 50:
                    enhanced_description = await self.llm_client.enhance_description(
                        asset_name=metadata['name'],
                        technical_desc=metadata['description'],
                        schema_context="",  # TODO: estrarre da metadata
                        column_info=[]     # TODO: estrarre colonne se tabella
                    )
                
                result = {
                    'asset_id': asset_id,
                    'name': metadata['name'],
                    'classType': metadata['classType'],
                    'original_description': metadata['description'],
                    'enhanced_description': enhanced_description,
                    'facts_count': len(metadata['facts']),
                    'llm_provider_used': self.current_llm_provider.value
                }
                
                return [TextContent(
                    type="text",
                    text=f"Asset Details for {asset_id}:\n\n" + 
                         f"Name: {result['name']}\n" +
                         f"Type: {result['classType']}\n" +
                         f"Enhanced Description: {result['enhanced_description']}\n" +
                         f"Facts: {result['facts_count']} items\n" +
                         f"Enhanced by: {result['llm_provider_used']}"
                )]
                
            except Exception as e:
                return [TextContent(type="text", text=f"Errore: {str(e)}")]
        
        @self.server.call_tool()
        async def search_assets(query: str, asset_type: str = "", max_results: int = 10) -> List[TextContent]:
            """
            Cerca asset nel catalogo EDC.
            
            Args:
                query: Termine di ricerca
                asset_type: Tipo di asset (opzionale)
                max_results: Numero massimo di risultati
            """
            try:
                if not self.lineage_builder:
                    self.lineage_builder = LineageBuilder()
                
                filters = {}
                if asset_type:
                    filters['classType'] = asset_type
                
                # Cerca via client EDC
                results = await self.lineage_builder.edc_client.search_assets(query, filters)
                
                # Limita risultati
                results = results[:max_results]
                
                if not results:
                    return [TextContent(type="text", text=f"Nessun asset trovato per: {query}")]
                
                result_text = f"Trovati {len(results)} asset per '{query}':\n\n"
                for i, asset in enumerate(results, 1):
                    result_text += f"{i}. {asset.get('name', 'N/A')} ({asset.get('classType', 'N/A')})\n"
                    result_text += f"   ID: {asset.get('id', 'N/A')}\n\n"
                
                return [TextContent(type="text", text=result_text)]
                
            except Exception as e:
                return [TextContent(type="text", text=f"Errore ricerca: {str(e)}")]
        
        # ====================================
        # LINEAGE ANALYSIS TOOLS
        # ====================================
        
        @self.server.call_tool()
        async def get_lineage_tree(asset_id: str, direction: str = "upstream", depth: int = 3) -> List[TextContent]:
            """
            Costruisce albero completo del lineage per un asset con analisi AI.
            
            Args:
                asset_id: Asset di partenza
                direction: "upstream", "downstream", "both"  
                depth: Profondità massima dell'albero
            """
            try:
                if not self.lineage_builder:
                    self.lineage_builder = LineageBuilder()
                
                start_time = time.time()
                
                if direction == "upstream":
                    # Usa il TreeBuilder originale per costruire l'albero
                    root_node = await self.lineage_builder.build_tree(
                        node_id=asset_id,
                        code="001",  # Codice iniziale
                        depth=0
                    )
                elif direction == "downstream":
                    # Per downstream, usa lineage immediato (semplificato)
                    immediate_lineage = await self.lineage_builder.get_immediate_lineage(
                        asset_id, "downstream"
                    )
                    
                    # Crea un pseudo-albero per downstream (semplificato)
                    root_node = TreeNode(asset_id, "001")
                    for i, link in enumerate(immediate_lineage, 1):
                        child_node = TreeNode(link['asset_id'], f"001{i:03d}")
                        root_node.children.append(child_node)
                else:
                    # Both - per ora solo upstream (downstream più complesso)
                    root_node = await self.lineage_builder.build_tree(
                        node_id=asset_id,
                        code="001",
                        depth=0
                    )
                
                build_time = time.time() - start_time
                
                if not root_node:
                    return [TextContent(type="text", text=f"Nessun lineage trovato per {asset_id}")]
                
                # Genera analisi del lineage con LLM
                lineage_data = self._tree_to_dict(root_node)
                complexity_analysis = await self.llm_client.analyze_lineage_complexity(lineage_data)
                
                # Formatta risultato
                stats = root_node.get_statistics()
                result_text = f"Lineage Tree per {asset_id} (direction: {direction}):\n\n"
                result_text += f"Statistiche:\n"
                result_text += f"- Nodi totali: {stats['total_nodes']}\n"
                result_text += f"- Profondità max: {stats['max_depth']}\n"
                result_text += f"- Field cross-references: {stats['field_cross_references']}\n"
                result_text += f"- Tempo costruzione: {build_time:.2f}s\n\n"
                
                result_text += f"Analisi Complessità (by {self.current_llm_provider.value}):\n"
                result_text += f"- Score complessità: {complexity_analysis.get('complexity_score', 'N/A')}/10\n"
                result_text += f"- Fattori di rischio: {len(complexity_analysis.get('risk_factors', []))}\n"
                result_text += f"- Dipendenze critiche: {len(complexity_analysis.get('critical_dependencies', []))}\n\n"
                
                if complexity_analysis.get('recommendations'):
                    result_text += "Raccomandazioni:\n"
                    for rec in complexity_analysis['recommendations']:
                        result_text += f"- {rec}\n"
                
                return [TextContent(type="text", text=result_text)]
                
            except Exception as e:
                return [TextContent(type="text", text=f"Errore costruzione lineage: {str(e)}")]
        
        @self.server.call_tool()
        async def get_immediate_lineage(asset_id: str, direction: str = "upstream") -> List[TextContent]:
            """
            Recupera il lineage immediato (1 livello) di un asset.
            
            Args:
                asset_id: ID dell'asset
                direction: "upstream", "downstream", "both"
            """
            try:
                if not self.lineage_builder:
                    self.lineage_builder = LineageBuilder()
                
                lineage = await self.lineage_builder.get_immediate_lineage(asset_id, direction)
                
                if not lineage:
                    return [TextContent(type="text", text=f"Nessun lineage immediato trovato per {asset_id}")]
                
                result_text = f"Lineage immediato per {asset_id} ({direction}):\n\n"
                
                upstream_count = len([l for l in lineage if l['direction'] == 'upstream'])
                downstream_count = len([l for l in lineage if l['direction'] == 'downstream'])
                
                result_text += f"Upstream: {upstream_count} asset\n"
                result_text += f"Downstream: {downstream_count} asset\n\n"
                
                for link in lineage:
                    direction_symbol = "⬅️" if link['direction'] == 'upstream' else "➡️"
                    result_text += f"{direction_symbol} {link['name']} ({link['classType']})\n"
                    result_text += f"   ID: {link['asset_id']}\n"
                    result_text += f"   Association: {link['association']}\n\n"
                
                return [TextContent(type="text", text=result_text)]
                
            except Exception as e:
                return [TextContent(type="text", text=f"Errore lineage immediato: {str(e)}")]
        
        # ====================================
        # IMPACT ANALYSIS TOOLS
        # ====================================
        
        @self.server.call_tool()
        async def analyze_change_impact(
            asset_id: str, 
            change_type: str, 
            change_description: str,
            max_depth: int = 5
        ) -> List[TextContent]:
            """
            Analizza l'impatto di una modifica su tutto il lineage downstream.
            
            Args:
                asset_id: Asset che subirà la modifica
                change_type: Tipo modifica (column_drop, data_type_change, deprecation, etc.)
                change_description: Descrizione dettagliata della modifica
                max_depth: Profondità massima analisi
            """
            try:
                if not self.lineage_builder:
                    self.lineage_builder = LineageBuilder()
                
                # Costruisce lineage downstream
                print(f"[MCP] Analizzando impatto per {asset_id}...")
                
                # Per ora usa lineage immediato (il downstream completo richiede logica più complessa)
                affected_lineage = await self.lineage_builder.get_immediate_lineage(
                    asset_id, "downstream"
                )
                
                # Prepara dettagli modifica
                change_details = {
                    "description": change_description,
                    "type": change_type,
                    "asset_id": asset_id
                }
                
                # Analizza con LLM
                impact_analysis = await self.llm_client.analyze_change_impact(
                    source_asset=asset_id,
                    change_type=change_type,
                    change_details=change_details,
                    affected_lineage={"downstream": affected_lineage}
                )
                
                # Formatta risultato
                result_text = f"Analisi Impatto per {asset_id}:\n\n"
                result_text += f"Modifica: {change_type}\n"
                result_text += f"Descrizione: {change_description}\n\n"
                
                result_text += f"Livello Rischio: {impact_analysis.get('risk_level', 'UNKNOWN')}\n"
                result_text += f"Asset Impattati: {len(affected_lineage)}\n\n"
                
                if impact_analysis.get('business_impact'):
                    result_text += f"Impatto Business:\n{impact_analysis['business_impact']}\n\n"
                
                if impact_analysis.get('technical_impact'):
                    result_text += f"Impatto Tecnico:\n{impact_analysis['technical_impact']}\n\n"
                
                if impact_analysis.get('recommendations'):
                    result_text += "Raccomandazioni:\n"
                    for i, rec in enumerate(impact_analysis['recommendations'], 1):
                        result_text += f"{i}. {rec}\n"
                    result_text += "\n"
                
                if impact_analysis.get('testing_strategy'):
                    result_text += "Strategia di Test:\n"
                    for i, test in enumerate(impact_analysis['testing_strategy'], 1):
                        result_text += f"{i}. {test}\n"
                
                result_text += f"\nAnalisi generata da: {self.current_llm_provider.value}"
                
                return [TextContent(type="text", text=result_text)]
                
            except Exception as e:
                return [TextContent(type="text", text=f"Errore analisi impatto: {str(e)}")]
        
        @self.server.call_tool()
        async def generate_change_checklist(
            asset_id: str,
            change_type: str,
            change_description: str
        ) -> List[TextContent]:
            """
            Genera checklist operativa per implementare una modifica.
            
            Args:
                asset_id: Asset che subirà la modifica
                change_type: Tipo di modifica
                change_description: Descrizione della modifica
            """
            try:
                # Prima esegui analisi impatto
                if not self.lineage_builder:
                    self.lineage_builder = LineageBuilder()
                
                affected_lineage = await self.lineage_builder.get_immediate_lineage(
                    asset_id, "downstream"
                )
                
                change_details = {
                    "description": change_description,
                    "type": change_type,
                    "asset_id": asset_id
                }
                
                impact_analysis = await self.llm_client.analyze_change_impact(
                    source_asset=asset_id,
                    change_type=change_type,
                    change_details=change_details,
                    affected_lineage={"downstream": affected_lineage}
                )
                
                # Genera checklist
                checklist = await self.llm_client.generate_change_checklist(impact_analysis)
                
                # Formatta risultato
                result_text = f"Checklist Operativa per {asset_id}:\n\n"
                result_text += f"Modifica: {change_type} - {change_description}\n\n"
                
                if checklist.get('governance_tasks'):
                    result_text += "📋 Governance e Approvazioni:\n"
                    for i, task in enumerate(checklist['governance_tasks'], 1):
                        result_text += f"   {i}. {task}\n"
                    result_text += "\n"
                
                if checklist.get('pre_change_tasks'):
                    result_text += "🔧 Preparazione Pre-Modifica:\n"
                    for i, task in enumerate(checklist['pre_change_tasks'], 1):
                        result_text += f"   {i}. {task}\n"
                    result_text += "\n"
                
                if checklist.get('execution_tasks'):
                    result_text += "⚡ Esecuzione Modifica:\n"
                    for i, task in enumerate(checklist['execution_tasks'], 1):
                        result_text += f"   {i}. {task}\n"
                    result_text += "\n"
                
                if checklist.get('validation_tasks'):
                    result_text += "✅ Validazione e Test:\n"
                    for i, task in enumerate(checklist['validation_tasks'], 1):
                        result_text += f"   {i}. {task}\n"
                    result_text += "\n"
                
                if checklist.get('rollback_procedures'):
                    result_text += "🔄 Procedure di Rollback:\n"
                    for i, proc in enumerate(checklist['rollback_procedures'], 1):
                        result_text += f"   {i}. {proc}\n"
                    result_text += "\n"
                
                if checklist.get('stakeholder_notifications'):
                    result_text += "📢 Comunicazioni Stakeholder:\n"
                    for i, notif in enumerate(checklist['stakeholder_notifications'], 1):
                        result_text += f"   {i}. {notif}\n"
                    result_text += "\n"
                
                if checklist.get('monitoring_tasks'):
                    result_text += "📊 Monitoraggio Post-Implementazione:\n"
                    for i, task in enumerate(checklist['monitoring_tasks'], 1):
                        result_text += f"   {i}. {task}\n"
                
                result_text += f"\nChecklist generata da: {self.current_llm_provider.value}"
                
                return [TextContent(type="text", text=result_text)]
                
            except Exception as e:
                return [TextContent(type="text", text=f"Errore generazione checklist: {str(e)}")]
        
        # ====================================
        # DOCUMENTATION ENHANCEMENT TOOLS
        # ====================================
        
        @self.server.call_tool()
        async def enhance_asset_documentation(
            asset_id: str,
            include_lineage_context: bool = True,
            business_domain: str = ""
        ) -> List[TextContent]:
            """
            Arricchisce la documentazione di un asset usando AI.
            
            Args:
                asset_id: Asset da documentare
                include_lineage_context: Se includere contesto lineage
                business_domain: Dominio business per contesto
            """
            try:
                if not self.lineage_builder:
                    self.lineage_builder = LineageBuilder()
                
                # Recupera metadati asset
                asset_metadata = await self.lineage_builder.get_asset_metadata(asset_id)
                
                # Recupera contesto lineage se richiesto
                lineage_context = {}
                if include_lineage_context:
                    upstream = await self.lineage_builder.get_immediate_lineage(
                        asset_id, "upstream"
                    )
                    lineage_context = {"upstream": upstream}
                
                # Prepara contesto business
                business_context = {}
                if business_domain:
                    business_context["domain"] = business_domain
                
                # Enhancement con LLM
                enhanced_docs = await self.llm_client.enhance_documentation(
                    asset_info=asset_metadata,
                    lineage_context=lineage_context,
                    business_context=business_context
                )
                
                # Formatta risultato
                result_text = f"Documentazione Arricchita per {asset_id}:\n\n"
                
                result_text += f"Asset: {asset_metadata['name']}\n"
                result_text += f"Tipo: {asset_metadata['classType']}\n\n"
                
                result_text += "📝 Descrizione Originale:\n"
                result_text += f"{asset_metadata['description'] or 'Nessuna descrizione disponibile'}\n\n"
                
                if enhanced_docs.get('enhanced_description'):
                    result_text += "✨ Descrizione Arricchita:\n"
                    result_text += f"{enhanced_docs['enhanced_description']}\n\n"
                
                if enhanced_docs.get('business_purpose'):
                    result_text += "🎯 Scopo Business:\n"
                    result_text += f"{enhanced_docs['business_purpose']}\n\n"
                
                if enhanced_docs.get('suggested_tags'):
                    result_text += "🏷️ Tag Suggeriti:\n"
                    result_text += f"{', '.join(enhanced_docs['suggested_tags'])}\n\n"
                
                if enhanced_docs.get('business_terms'):
                    result_text += "📚 Termini Business:\n"
                    for term in enhanced_docs['business_terms']:
                        result_text += f"- {term}\n"
                    result_text += "\n"
                
                if enhanced_docs.get('suggested_quality_rules'):
                    result_text += "🔍 Regole Qualità Suggerite:\n"
                    for rule in enhanced_docs['suggested_quality_rules']:
                        result_text += f"- {rule}\n"
                    result_text += "\n"
                
                if enhanced_docs.get('compliance_notes'):
                    result_text += "⚖️ Note Compliance:\n"
                    result_text += f"{enhanced_docs['compliance_notes']}\n\n"
                
                result_text += f"Enhancement generato da: {self.current_llm_provider.value}"
                
                return [TextContent(type="text", text=result_text)]
                
            except Exception as e:
                return [TextContent(type="text", text=f"Errore enhancement documentazione: {str(e)}")]
        
        # ====================================
        # LLM MANAGEMENT TOOLS
        # ====================================
        
        @self.server.call_tool()
        async def switch_llm_provider(provider: str) -> List[TextContent]:
            """
            Cambia provider LLM a runtime.
            
            Args:
                provider: "tinyllama" o "claude"
            """
            try:
                if provider.lower() == "tinyllama":
                    new_provider = LLMProvider.TINYLLAMA
                elif provider.lower() == "claude":
                    new_provider = LLMProvider.CLAUDE
                else:
                    return [TextContent(
                        type="text", 
                        text=f"Provider non supportato: {provider}. Usa 'tinyllama' o 'claude'"
                    )]
                
                if new_provider == self.current_llm_provider:
                    return [TextContent(
                        type="text",
                        text=f"Provider {provider} già attivo"
                    )]
                
                # Verifica disponibilità
                if new_provider == LLMProvider.CLAUDE and not settings.claude_api_key:
                    return [TextContent(
                        type="text",
                        text="Claude non disponibile: API key non configurata"
                    )]
                
                if new_provider == LLMProvider.TINYLLAMA and not settings.is_ollama_available():
                    return [TextContent(
                        type="text",
                        text="TinyLlama non disponibile: Ollama non in esecuzione"
                    )]
                
                # Switch provider
                old_provider = self.current_llm_provider.value
                self.current_llm_provider = new_provider
                self._initialize_llm()
                
                return [TextContent(
                    type="text",
                    text=f"Provider LLM cambiato da {old_provider} a {new_provider.value}"
                )]
                
            except Exception as e:
                return [TextContent(type="text", text=f"Errore cambio provider: {str(e)}")]
        
        @self.server.call_tool()
        async def get_llm_status() -> List[TextContent]:
            """Mostra lo stato corrente del sistema LLM."""
            try:
                status_text = "🤖 Stato Sistema LLM:\n\n"
                
                status_text += f"Provider Attivo: {self.current_llm_provider.value}\n\n"
                
                # Status TinyLlama
                ollama_available = settings.is_ollama_available()
                status_text += f"TinyLlama (Ollama): {'✅ Disponibile' if ollama_available else '❌ Non disponibile'}\n"
                if ollama_available:
                    status_text += f"  - URL: {settings.ollama_base_url}\n"
                    status_text += f"  - Modello: {settings.tinyllama_model}\n"
                
                # Status Claude
                claude_available = settings.is_claude_available()
                status_text += f"Claude API: {'✅ Disponibile' if claude_available else '❌ Non disponibile'}\n"
                if claude_available:
                    status_text += f"  - Modello: {settings.claude_model}\n"
                    status_text += f"  - Max tokens: {settings.claude_max_tokens}\n"
                
                # Statistiche se disponibili
                if self.lineage_builder:
                    stats = self.lineage_builder.get_statistics()
                    status_text += f"\n📊 Statistiche Sessione:\n"
                    status_text += f"  - API calls EDC: {stats['total_requests']}\n"
                    status_text += f"  - Nodi creati: {stats['nodes_created']}\n"
                    status_text += f"  - Cache hits: {stats['cache_hits']}\n"
                
                return [TextContent(type="text", text=status_text)]
                
            except Exception as e:
                return [TextContent(type="text", text=f"Errore stato LLM: {str(e)}")]
        
        # ====================================
        # UTILITY TOOLS
        # ====================================
        
        @self.server.call_tool()
        async def get_system_statistics() -> List[TextContent]:
            """Mostra statistiche complete del sistema."""
            try:
                stats_text = "📈 Statistiche Sistema EDC-MCP-LLM:\n\n"
                
                # Statistiche LLM
                stats_text += f"🤖 LLM Provider: {self.current_llm_provider.value}\n\n"
                
                # Statistiche EDC se disponibili
                if self.lineage_builder:
                    edc_stats = self.lineage_builder.get_statistics()
                    stats_text += "🏛️ Statistiche EDC:\n"
                    stats_text += f"  - Total API calls: {edc_stats['total_requests']}\n"
                    stats_text += f"  - Cache hits: {edc_stats['cache_hits']}\n"
                    stats_text += f"  - API errors: {edc_stats['api_errors']}\n"
                    stats_text += f"  - Nodi creati: {edc_stats['nodes_created']}\n"
                    stats_text += f"  - Cicli prevenuti: {edc_stats['cycles_prevented']}\n"
                    stats_text += f"  - Auto-referenze: {edc_stats['self_references']}\n"
                    stats_text += f"  - Field cross-references: {edc_stats['field_cross_references_found']}\n"
                    
                    if edc_stats['deduplication_sessions'] > 0:
                        stats_text += f"  - Sessioni deduplicazione: {edc_stats['deduplication_sessions']}\n"
                        stats_text += f"  - Link duplicati rimossi: {edc_stats['duplicate_children_removed']}\n"
                    
                    stats_text += "\n"
                
                # Configurazione sistema
                stats_text += "⚙️ Configurazione:\n"
                stats_text += f"  - Max tree depth: {settings.lineage_max_depth}\n"
                stats_text += f"  - Request timeout: {settings.request_timeout}s\n"
                stats_text += f"  - Max concurrent requests: {settings.max_concurrent_requests}\n"
                
                return [TextContent(type="text", text=stats_text)]
                
            except Exception as e:
                return [TextContent(type="text", text=f"Errore statistiche: {str(e)}")]
    
    def _tree_to_dict(self, node: TreeNode) -> dict:
        """Converte TreeNode in dizionario per LLM processing."""
        return {
            'id': node.id,
            'code': node.code,
            'description': node.description,
            'node_type': node.get_node_type(),
            'is_terminal': node.is_terminal_node(),
            'children_count': len(node.children),
            'children': [self._tree_to_dict(child) for child in node.children]
        }
    
    async def start_server(self, host: str = "localhost", port: int = 8000) -> None:
        """Avvia il server MCP."""
        print(f"[MCP] Starting EDC-MCP-LLM Server on {host}:{port}")
        print(f"[MCP] LLM Provider: {self.current_llm_provider.value}")
        print(f"[MCP] EDC URL: {settings.edc_base_url}")
        
        # Qui andrà la logica di avvio del server MCP
        # Per ora solo placeholder
        await asyncio.sleep(0.1)
    
    async def cleanup(self) -> None:
        """Cleanup delle risorse."""
        if self.lineage_builder:
            await self.lineage_builder.close()
        print("[MCP] Server cleanup completed")

async def main():
    """Entry point principale del server MCP."""
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("="*60)
    print("🚀 EDC-MCP-LLM Server")
    print("="*60)
    print(f"Environment: {settings.environment.value}")
    print(f"EDC URL: {settings.edc_base_url}")
    print(f"LLM Provider: {settings.default_llm_provider.value}")
    print("="*60)
    
    try:
        # Crea server
        server = EDCMCPServer()
        
        # Verifica disponibilità LLM
        if settings.default_llm_provider == LLMProvider.CLAUDE:
            if not settings.is_claude_available():
                print("⚠️  WARNING: Claude API key non configurata!")
                print("   Configura CLAUDE_API_KEY in .env")
        elif settings.default_llm_provider == LLMProvider.TINYLLAMA:
            if not settings.is_ollama_available():
                print("⚠️  WARNING: Ollama non disponibile!")
                print("   Avvia Ollama con: ollama serve")
        
        print("\n✅ Server inizializzato con successo!")
        print(f"\n📋 Tools MCP disponibili:")
        print("   • get_asset_details - Dettagli asset con AI enhancement")
        print("   • search_assets - Ricerca nel catalogo EDC")
        print("   • get_lineage_tree - Costruzione albero lineage completo")
        print("   • get_immediate_lineage - Lineage 1 livello")
        print("   • analyze_change_impact - Analisi impatto modifiche")
        print("   • generate_change_checklist - Genera checklist operativa")
        print("   • enhance_asset_documentation - Arricchimento documentazione")
        print("   • switch_llm_provider - Cambia provider LLM")
        print("   • get_llm_status - Stato sistema LLM")
        print("   • get_system_statistics - Statistiche complete")
        
        print(f"\n🔌 Server in ascolto su stdio (MCP protocol)")
        print("   Usa questo server da Claude Desktop o client MCP compatibili")
        print("\n💡 Per testare, usa: python test_mcp_integration.py")
        print("\nPremi Ctrl+C per terminare...\n")
        
        # Avvia il server MCP su stdio
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await server.server.run(
                read_stream,
                write_stream,
                server.server.create_initialization_options()
            )
    
    except KeyboardInterrupt:
        print("\n\n🛑 Shutdown richiesto...")
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if 'server' in locals():
            await server.cleanup()
        print("✅ Server terminato")


if __name__ == "__main__":
    # Esegui il server
    asyncio.run(main())