"""
MCP Server principale per l'integrazione EDC-LLM.
Combina la potenza del lineage EDC con l'intelligenza dei LLM multipli.
VERSIONE DEBUG CON LOGGING DETTAGLIATO - SENZA EMOTICON
"""

import asyncio
import logging
import os
import sys
from typing import List, Optional

from mcp.types import GetPromptResult, Prompt, PromptArgument, PromptMessage, TextContent, Tool

from mcp.server import Server

from ..config.settings import LLMProvider, settings
from ..edc.lineage import LineageBuilder
from ..edc.models import TreeNode
from ..llm.factory import LLMConfig, LLMFactory


class EDCMCPServer:
    """
    Server MCP che espone funzionalità EDC arricchite con LLM.
    Mantiene la compatibilità con la logica TreeBuilder esistente.
    """

    def __init__(self):
        """Inizializza il server MCP."""
        try:
            print("[MCP] ===== INIZIO INIZIALIZZAZIONE =====", file=sys.stderr)
            print(f"[MCP] Python version: {sys.version}", file=sys.stderr)
            print(f"[MCP] Working directory: {os.getcwd()}", file=sys.stderr)

            self.server = Server("edc-lineage")
            print("[MCP] [OK] Server MCP creato", file=sys.stderr)

            self.lineage_builder: Optional[LineageBuilder] = None
            self.llm_client = None
            self.current_llm_provider = settings.default_llm_provider
            print(f"[MCP] [OK] Provider LLM: {self.current_llm_provider.value}", file=sys.stderr)

            # Inizializza LLM client
            print("[MCP] Inizializzazione LLM client...", file=sys.stderr)
            self._initialize_llm()
            print(f"[MCP] [OK] LLM client inizializzato: {type(self.llm_client).__name__}", file=sys.stderr)

            # Registra tools MCP
            print("[MCP] Registrazione tools e prompts...", file=sys.stderr)
            self._register_tools_and_prompts()
            print("[MCP] [OK] Tools e prompts registrati", file=sys.stderr)

            print("[MCP] ===== INIZIALIZZAZIONE COMPLETATA =====", file=sys.stderr)

        except Exception as e:
            print(f"[MCP] [ERROR] ERRORE FATALE in __init__: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            raise

    def _initialize_llm(self) -> None:
        """Inizializza il client LLM basato sulla configurazione."""
        try:
            print(f"[MCP] _initialize_llm: provider={self.current_llm_provider.value}", file=sys.stderr)

            if self.current_llm_provider == LLMProvider.TINYLLAMA:
                print("[MCP] Configurazione TinyLlama...", file=sys.stderr)
                llm_config = LLMConfig(
                    provider=LLMProvider.TINYLLAMA,
                    model_name=settings.tinyllama_model,
                    base_url=settings.tinyllama_base_url,
                    max_tokens=settings.tinyllama_max_tokens,
                    temperature=settings.tinyllama_temperature,
                )
                print(f"[MCP] Config: model={llm_config.model_name}, url={llm_config.base_url}", file=sys.stderr)

            elif self.current_llm_provider == LLMProvider.GEMMA3:
                print("[MCP] Configurazione Gemma3...", file=sys.stderr)
                llm_config = LLMConfig(
                    provider=LLMProvider.GEMMA3,
                    model_name=settings.gemma3_model,
                    base_url=settings.gemma3_base_url,
                    max_tokens=settings.gemma3_max_tokens,
                    temperature=settings.gemma3_temperature,
                )
                print(f"[MCP] Config: model={llm_config.model_name}, url={llm_config.base_url}", file=sys.stderr)

            elif self.current_llm_provider == LLMProvider.CLAUDE:
                print("[MCP] Configurazione Claude...", file=sys.stderr)

                if not settings.claude_api_key:
                    raise ValueError("Claude API key non configurata in .env")

                llm_config = LLMConfig(
                    provider=LLMProvider.CLAUDE,
                    model_name=settings.claude_model,
                    api_key=settings.claude_api_key,
                    max_tokens=settings.claude_max_tokens,
                    temperature=settings.claude_temperature,
                )
                print(f"[MCP] Config: model={llm_config.model_name}", file=sys.stderr)
            else:
                raise ValueError(f"Provider LLM non supportato: {self.current_llm_provider}")

            print("[MCP] Creazione client LLM tramite factory...", file=sys.stderr)
            self.llm_client = LLMFactory.create_llm_client(llm_config)
            print(f"[MCP] [OK] Client creato: {type(self.llm_client).__name__}", file=sys.stderr)

        except Exception as e:
            print(f"[MCP] [ERROR] ERRORE in _initialize_llm: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            raise

    def _register_tools_and_prompts(self) -> None:
        """Registra tutti i tools MCP."""

        try:
            print("[MCP] Inizio registrazione decoratori...", file=sys.stderr)

            # Lista dei tools disponibili
            @self.server.list_tools()
            async def handle_list_tools() -> list[Tool]:
                """List available tools."""
                print("[MCP] >> handle_list_tools() chiamato", file=sys.stderr)

                tools = [
                    Tool(
                        name="get_asset_details",
                        description="Recupera informazioni complete su un asset EDC specifico con enhancement AI",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "asset_id": {
                                    "type": "string",
                                    "description": "ID completo dell'asset EDC (es: DataPlatform://ORAC51/DWHEVO/TABLE_NAME)",
                                }
                            },
                            "required": ["asset_id"],
                        },
                    ),
                    Tool(
                        name="search_assets",
                        description="Cerca asset nel catalogo EDC usando API bulk per una risorsa specifica. Filtra i risultati per nome e tipo.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "resource_name": {
                                    "type": "string",
                                    "description": "Nome della risorsa EDC (es: DataPlatform, ORAC51, DWHEVO) - OBBLIGATORIO",
                                },
                                "name_filter": {
                                    "type": "string",
                                    "description": "Filtro sul nome dell'asset (case-insensitive, ricerca parziale)",
                                    "default": "",
                                },
                                "asset_type": {
                                    "type": "string",
                                    "description": "Tipo di asset da cercare (Table, View, Column, ViewTable, etc.)",
                                    "default": "",
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "Numero massimo di risultati da ritornare",
                                    "default": 10,
                                },
                            },
                            "required": ["resource_name"],
                        },
                    ),
                    Tool(
                        name="get_lineage_tree",
                        description="Costruisce albero completo del lineage con analisi AI",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "asset_id": {"type": "string", "description": "Asset di partenza"},
                                "direction": {
                                    "type": "string",
                                    "description": "Direzione: upstream, downstream, both",
                                    "default": "upstream",
                                },
                                "depth": {"type": "integer", "description": "ProfonditÃ  massima", "default": 3},
                            },
                            "required": ["asset_id"],
                        },
                    ),
                    Tool(
                        name="get_immediate_lineage",
                        description="Recupera lineage immediato (1 livello)",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "asset_id": {"type": "string", "description": "ID dell'asset"},
                                "direction": {
                                    "type": "string",
                                    "description": "upstream, downstream, both",
                                    "default": "upstream",
                                },
                            },
                            "required": ["asset_id"],
                        },
                    ),
                    Tool(
                        name="analyze_change_impact",
                        description="Analizza impatto di una modifica sul lineage",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "asset_id": {"type": "string", "description": "Asset che subirÃ  la modifica"},
                                "change_type": {
                                    "type": "string",
                                    "description": "Tipo modifica: column_drop, data_type_change, deprecation, etc.",
                                },
                                "change_description": {"type": "string", "description": "Descrizione dettagliata"},
                                "max_depth": {"type": "integer", "description": "ProfonditÃ  analisi", "default": 5},
                            },
                            "required": ["asset_id", "change_type", "change_description"],
                        },
                    ),
                    Tool(
                        name="generate_change_checklist",
                        description="Genera checklist operativa per una modifica",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "asset_id": {"type": "string"},
                                "change_type": {"type": "string"},
                                "change_description": {"type": "string"},
                            },
                            "required": ["asset_id", "change_type", "change_description"],
                        },
                    ),
                    Tool(
                        name="enhance_asset_documentation",
                        description="Arricchisce documentazione asset con AI",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "asset_id": {"type": "string"},
                                "include_lineage_context": {"type": "boolean", "default": True},
                                "business_domain": {"type": "string", "default": ""},
                            },
                            "required": ["asset_id"],
                        },
                    ),
                    Tool(
                        name="switch_llm_provider",
                        description="Cambia provider LLM a runtime",
                        inputSchema={
                            "type": "object",
                            "properties": {"provider": {"type": "string", "description": "tinyllama o claude"}},
                            "required": ["provider"],
                        },
                    ),
                    Tool(
                        name="get_llm_status",
                        description="Mostra stato corrente sistema LLM",
                        inputSchema={"type": "object", "properties": {}},
                    ),
                    Tool(
                        name="get_system_statistics",
                        description="Mostra statistiche complete del sistema",
                        inputSchema={"type": "object", "properties": {}},
                    ),
                ]

                print(f"[MCP] >> Ritorno {len(tools)} tools", file=sys.stderr)
                for i, tool in enumerate(tools, 1):
                    print(f"[MCP]    {i}. {tool.name}", file=sys.stderr)

                return tools

            print("[MCP] [OK] Decoratore list_tools registrato", file=sys.stderr)

            # ============================================
            # PROMPTS REGISTRATION
            # ============================================

            @self.server.list_prompts()
            async def handle_list_prompts() -> list[Prompt]:
                """List available prompts."""
                print("[MCP] >> handle_list_prompts() chiamato", file=sys.stderr)

                prompts = [
                    Prompt(
                        name="analyze_asset_comprehensive",
                        description="Analisi completa di un asset EDC con contesto business, tecnico e governance",
                        arguments=[
                            PromptArgument(
                                name="asset_id",
                                description="ID completo dell'asset EDC (es: DataPlatform://ORAC51/DWHEVO/TABLE)",
                                required=True,
                            ),
                            PromptArgument(
                                name="include_lineage",
                                description="Include analisi del lineage upstream/downstream",
                                required=False,
                            ),
                            PromptArgument(
                                name="business_domain",
                                description="Dominio business (es: GARANZIE, SOFFERENZE, CUSTOMER)",
                                required=False,
                            ),
                        ],
                    ),
                    Prompt(
                        name="impact_analysis_template",
                        description="Template guidato per analisi impatto di una modifica su asset EDC",
                        arguments=[
                            PromptArgument(name="asset_id", description="Asset da modificare", required=True),
                            PromptArgument(
                                name="change_type",
                                description="Tipo modifica: column_drop, data_type_change, deprecation, schema_change",
                                required=True,
                            ),
                            PromptArgument(
                                name="change_description",
                                description="Descrizione dettagliata della modifica proposta",
                                required=True,
                            ),
                        ],
                    ),
                    Prompt(
                        name="data_governance_review",
                        description="Revisione governance per un asset: qualita, compliance, ownership",
                        arguments=[
                            PromptArgument(name="asset_id", description="Asset da revisionare", required=True),
                            PromptArgument(
                                name="review_type",
                                description="Tipo review: quality, compliance, ownership, complete",
                                required=False,
                            ),
                        ],
                    ),
                    Prompt(
                        name="lineage_investigation",
                        description="Investigazione approfondita del lineage per troubleshooting o audit",
                        arguments=[
                            PromptArgument(name="asset_id", description="Asset punto di partenza", required=True),
                            PromptArgument(
                                name="investigation_goal",
                                description="Obiettivo: data_quality_issue, audit_trail, performance_bottleneck",
                                required=True,
                            ),
                            PromptArgument(
                                name="depth", description="Profondita analisi lineage (default: 3)", required=False
                            ),
                        ],
                    ),
                    Prompt(
                        name="migration_planning",
                        description="Pianificazione migrazione di un asset tra ambienti o sistemi",
                        arguments=[
                            PromptArgument(name="asset_id", description="Asset da migrare", required=True),
                            PromptArgument(
                                name="target_environment",
                                description="Ambiente target (es: dev, test, prod, cloud)",
                                required=True,
                            ),
                            PromptArgument(
                                name="migration_type",
                                description="Tipo: lift_and_shift, replatform, refactor",
                                required=False,
                            ),
                        ],
                    ),
                    Prompt(
                        name="documentation_enhancement",
                        description="Arricchimento guidato della documentazione di un asset",
                        arguments=[
                            PromptArgument(name="asset_id", description="Asset da documentare", required=True),
                            PromptArgument(
                                name="documentation_level",
                                description="Livello: basic, intermediate, comprehensive",
                                required=False,
                            ),
                        ],
                    ),
                ]

                print(f"[MCP] >> Ritorno {len(prompts)} prompts", file=sys.stderr)
                for i, prompt in enumerate(prompts, 1):
                    print(f"[MCP]    {i}. {prompt.name}", file=sys.stderr)

                return prompts

            print("[MCP] [OK] Decoratore list_prompts registrato", file=sys.stderr)

            # ============================================
            # GET PROMPT HANDLER
            # ============================================

            @self.server.get_prompt()
            async def handle_get_prompt(name: str, arguments: dict) -> GetPromptResult:
                """Get a specific prompt with arguments filled in."""
                print(f"[MCP] >> handle_get_prompt('{name}') chiamato", file=sys.stderr)
                print(f"[MCP] >> Arguments: {arguments}", file=sys.stderr)

                if name == "analyze_asset_comprehensive":
                    return await self._generate_analyze_asset_prompt(arguments)
                elif name == "impact_analysis_template":
                    return await self._generate_impact_analysis_prompt(arguments)
                elif name == "data_governance_review":
                    return await self._generate_governance_review_prompt(arguments)
                elif name == "lineage_investigation":
                    return await self._generate_lineage_investigation_prompt(arguments)
                elif name == "migration_planning":
                    return await self._generate_migration_planning_prompt(arguments)
                elif name == "documentation_enhancement":
                    return await self._generate_documentation_enhancement_prompt(arguments)
                else:
                    error_msg = f"Prompt sconosciuto: {name}"
                    print(f"[MCP] >> [ERROR] {error_msg}", file=sys.stderr)
                    return GetPromptResult(
                        description=f"Errore: {error_msg}",
                        messages=[PromptMessage(role="user", content=TextContent(type="text", text=error_msg))],
                    )

            print("[MCP] [OK] Decoratore get_prompt registrato", file=sys.stderr)

            # Handler per chiamate ai tools
            @self.server.call_tool()
            async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
                """Handle tool calls."""

                print(f"[MCP] >> handle_call_tool('{name}') chiamato", file=sys.stderr)
                print(f"[MCP] >> Arguments: {arguments}", file=sys.stderr)

                try:
                    # Inizializza LineageBuilder se necessario
                    if not self.lineage_builder and name not in [
                        "switch_llm_provider",
                        "get_llm_status",
                        "get_system_statistics",
                    ]:
                        print("[MCP] >> Inizializzazione LineageBuilder...", file=sys.stderr)
                        self.lineage_builder = LineageBuilder()
                        print("[MCP] >> [OK] LineageBuilder pronto", file=sys.stderr)

                    # Route to appropriate handler
                    if name == "get_asset_details":
                        return await self._handle_get_asset_details(**arguments)
                    elif name == "search_assets":
                        return await self._handle_search_assets(**arguments)
                    elif name == "get_lineage_tree":
                        return await self._handle_get_lineage_tree(**arguments)
                    elif name == "get_immediate_lineage":
                        return await self._handle_get_immediate_lineage(**arguments)
                    elif name == "analyze_change_impact":
                        return await self._handle_analyze_change_impact(**arguments)
                    elif name == "generate_change_checklist":
                        return await self._handle_generate_change_checklist(**arguments)
                    elif name == "enhance_asset_documentation":
                        return await self._handle_enhance_asset_documentation(**arguments)
                    elif name == "switch_llm_provider":
                        return await self._handle_switch_llm_provider(**arguments)
                    elif name == "get_llm_status":
                        return await self._handle_get_llm_status()
                    elif name == "get_system_statistics":
                        return await self._handle_get_system_statistics()
                    else:
                        error_msg = f"Tool sconosciuto: {name}"
                        print(f"[MCP] >> [ERROR] {error_msg}", file=sys.stderr)
                        return [TextContent(type="text", text=error_msg)]

                except Exception as e:
                    error_msg = f"Errore esecuzione tool '{name}': {str(e)}"
                    print(f"[MCP] >> [ERROR] {error_msg}", file=sys.stderr)
                    import traceback

                    traceback.print_exc(file=sys.stderr)
                    return [TextContent(type="text", text=error_msg)]

            print("[MCP] [OK] Decoratore call_tool registrato", file=sys.stderr)
            print("[MCP] [OK] Registrazione tools e prompts completata", file=sys.stderr)

        except Exception as e:
            print(f"[MCP] [ERROR] ERRORE in _register_tools: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            raise

    # ====================================
    # HANDLER METHODS
    # ====================================

    async def _handle_search_assets(
        self, resource_name: str, name_filter: str = "", asset_type: str = "", max_results: int = 10
    ) -> List[TextContent]:
        """Search assets using EDC bulk API."""
        print(
            f"[MCP] >> Executing search_assets: resource={resource_name}, name={name_filter}, type={asset_type}",
            file=sys.stderr,
        )

        try:
            # Usa API bulk
            results = await self.lineage_builder.edc_client.bulk_search_assets(
                resource_name=resource_name,
                name_filter=name_filter if name_filter else None,
                asset_type_filter=asset_type if asset_type else None,
            )

            # Limita risultati
            results = results[:max_results]

            if not results:
                msg = f"Nessun asset trovato nella risorsa '{resource_name}'"
                if name_filter:
                    msg += f" con '{name_filter}' nel nome"
                if asset_type:
                    msg += f" di tipo '{asset_type}'"
                return [TextContent(type="text", text=msg)]

            # Costruisci risposta
            result_text = f"Trovati {len(results)} asset nella risorsa '{resource_name}'"
            if name_filter:
                result_text += f" con '{name_filter}' nel nome"
            if asset_type:
                result_text += f" di tipo '{asset_type}'"
            result_text += ":\n\n"

            for i, asset in enumerate(results, 1):
                result_text += f"{i}. {asset.get('name', 'N/A')}\n"
                result_text += f"   Type: {asset.get('classType', 'N/A')}\n"
                result_text += f"   ID: {asset.get('id', 'N/A')}\n\n"

            print(f"[MCP] >> search_assets completed: {len(results)} results", file=sys.stderr)
            return [TextContent(type="text", text=result_text)]

        except Exception as e:
            error_msg = f"Errore ricerca bulk: {str(e)}"
            print(f"[MCP] >> [ERROR] {error_msg}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            return [TextContent(type="text", text=error_msg)]

    async def _handle_get_asset_details(self, asset_id: str) -> List[TextContent]:
        """Get asset details with AI enhancement."""
        print(f"[MCP] >> Executing get_asset_details for: {asset_id}", file=sys.stderr)

        try:
            metadata = await self.lineage_builder.get_asset_metadata(asset_id)

            enhanced_description = metadata["description"]
            if not metadata["description"] or len(metadata["description"]) < 50:
                print("[MCP] >> Enhancing description with LLM...", file=sys.stderr)
                enhanced_description = await self.llm_client.enhance_description(
                    asset_name=metadata["name"],
                    technical_desc=metadata["description"],
                    schema_context="",
                    column_info=[],
                )

            result_text = f"Asset Details for {asset_id}:\n\n"
            result_text += f"Name: {metadata['name']}\n"
            result_text += f"Type: {metadata['classType']}\n"
            result_text += f"Enhanced Description: {enhanced_description}\n"
            result_text += f"Facts: {len(metadata['facts'])} items\n"
            result_text += f"Upstream links: {len(metadata['src_links'])}\n"
            result_text += f"Downstream links: {len(metadata['dst_links'])}\n"
            result_text += f"\nEnhanced by: {self.current_llm_provider.value}\n"

            print("[MCP] >> get_asset_details completed successfully", file=sys.stderr)
            return [TextContent(type="text", text=result_text)]

        except Exception as e:
            error_msg = f"Errore recupero asset: {str(e)}"
            print(f"[MCP] >> [ERROR] {error_msg}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            return [TextContent(type="text", text=error_msg)]

    async def _handle_get_lineage_tree(
        self, asset_id: str, direction: str = "upstream", depth: int = 3
    ) -> List[TextContent]:
        """Build complete lineage tree with AI analysis."""
        print(f"[MCP] >> Executing get_lineage_tree: {asset_id}, direction={direction}, depth={depth}", file=sys.stderr)

        try:
            import time

            start_time = time.time()

            if direction == "upstream":
                root_node = await self.lineage_builder.build_tree(
                    node_id=asset_id, code="001", depth=0, max_depth=depth
                )
            elif direction == "downstream":
                immediate_lineage = await self.lineage_builder.get_immediate_lineage(asset_id, "downstream")
                root_node = TreeNode(asset_id, "001")
                for i, link in enumerate(immediate_lineage, 1):
                    child_node = TreeNode(link["asset_id"], f"001{i:03d}")
                    root_node.children.append(child_node)
            else:
                root_node = await self.lineage_builder.build_tree(
                    node_id=asset_id, code="001", depth=0, max_depth=depth
                )

            build_time = time.time() - start_time

            if not root_node:
                return [TextContent(type="text", text=f"Nessun lineage trovato per {asset_id}")]

            stats = root_node.get_statistics()
            result_text = f"Lineage Tree per {asset_id} (direction: {direction}):\n\n"
            result_text += "Statistiche:\n"
            result_text += f"- Nodi totali: {stats['total_nodes']}\n"
            result_text += f"- Profondita max: {stats['max_depth']}\n"
            result_text += f"- Tempo costruzione: {build_time:.2f}s\n\n"

            print(f"[MCP] >> get_lineage_tree completed: {stats['total_nodes']} nodes", file=sys.stderr)
            return [TextContent(type="text", text=result_text)]

        except Exception as e:
            error_msg = f"Errore costruzione lineage tree: {str(e)}"
            print(f"[MCP] >> [ERROR] {error_msg}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            return [TextContent(type="text", text=error_msg)]

    async def _handle_get_immediate_lineage(self, asset_id: str, direction: str = "upstream") -> List[TextContent]:
        """Get immediate (1-level) lineage."""
        print(f"[MCP] >> Executing get_immediate_lineage: {asset_id}, direction={direction}", file=sys.stderr)

        try:
            lineage = await self.lineage_builder.get_immediate_lineage(asset_id, direction)

            if not lineage:
                return [TextContent(type="text", text=f"Nessun lineage immediato trovato per {asset_id}")]

            result_text = f"Lineage immediato per {asset_id} ({direction}):\n\n"

            upstream_count = len([l for l in lineage if l["direction"] == "upstream"])
            downstream_count = len([l for l in lineage if l["direction"] == "downstream"])

            result_text += f"Upstream: {upstream_count} asset\n"
            result_text += f"Downstream: {downstream_count} asset\n\n"

            for link in lineage:
                direction_symbol = "<-" if link["direction"] == "upstream" else "->"
                result_text += f"{direction_symbol} {link['name']} ({link['classType']})\n"
                result_text += f"   ID: {link['asset_id']}\n"
                result_text += f"   Association: {link['association']}\n\n"

            print(f"[MCP] >> get_immediate_lineage completed: {len(lineage)} links", file=sys.stderr)
            return [TextContent(type="text", text=result_text)]

        except Exception as e:
            error_msg = f"Errore recupero lineage: {str(e)}"
            print(f"[MCP] >> [ERROR] {error_msg}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            return [TextContent(type="text", text=error_msg)]

    async def _handle_analyze_change_impact(
        self, asset_id: str, change_type: str, change_description: str, max_depth: int = 5
    ) -> List[TextContent]:
        """Analyze change impact on lineage."""
        print(f"[MCP] >> Executing analyze_change_impact: {asset_id}, type={change_type}", file=sys.stderr)

        try:
            affected_lineage = await self.lineage_builder.get_immediate_lineage(asset_id, "downstream")

            change_details = {"description": change_description, "type": change_type, "asset_id": asset_id}

            impact_analysis = await self.llm_client.analyze_change_impact(
                source_asset=asset_id,
                change_type=change_type,
                change_details=change_details,
                affected_lineage={"downstream": affected_lineage},
            )

            result_text = f"Analisi Impatto per {asset_id}:\n\n"
            result_text += f"Modifica: {change_type}\n"
            result_text += f"Descrizione: {change_description}\n\n"
            result_text += f"Livello Rischio: {impact_analysis.get('risk_level', 'UNKNOWN')}\n"
            result_text += f"Asset Impattati: {len(affected_lineage)}\n\n"

            if impact_analysis.get("business_impact"):
                result_text += f"Impatto Business:\n{impact_analysis['business_impact']}\n\n"

            if impact_analysis.get("recommendations"):
                result_text += "Raccomandazioni:\n"
                for i, rec in enumerate(impact_analysis["recommendations"][:5], 1):
                    result_text += f"{i}. {rec}\n"

            result_text += f"\nAnalisi generata da: {self.current_llm_provider.value}"

            print("[MCP] >> analyze_change_impact completed", file=sys.stderr)
            return [TextContent(type="text", text=result_text)]

        except Exception as e:
            error_msg = f"Errore analisi impatto: {str(e)}"
            print(f"[MCP] >> [ERROR] {error_msg}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            return [TextContent(type="text", text=error_msg)]

    async def _handle_generate_change_checklist(
        self, asset_id: str, change_type: str, change_description: str
    ) -> List[TextContent]:
        """Generate operational checklist for change."""
        print(f"[MCP] >> Executing generate_change_checklist: {asset_id}", file=sys.stderr)

        try:
            affected_lineage = await self.lineage_builder.get_immediate_lineage(asset_id, "downstream")

            change_details = {"description": change_description, "type": change_type, "asset_id": asset_id}

            impact_analysis = await self.llm_client.analyze_change_impact(
                source_asset=asset_id,
                change_type=change_type,
                change_details=change_details,
                affected_lineage={"downstream": affected_lineage},
            )

            checklist = await self.llm_client.generate_change_checklist(impact_analysis)

            result_text = f"Checklist Operativa per {asset_id}:\n\n"
            result_text += f"Modifica: {change_type} - {change_description}\n\n"

            if checklist.get("governance_tasks"):
                result_text += "Governance e Approvazioni:\n"
                for i, task in enumerate(checklist["governance_tasks"], 1):
                    result_text += f"   {i}. {task}\n"
                result_text += "\n"

            if checklist.get("pre_change_tasks"):
                result_text += "Preparazione Pre-Modifica:\n"
                for i, task in enumerate(checklist["pre_change_tasks"], 1):
                    result_text += f"   {i}. {task}\n"
                result_text += "\n"

            if checklist.get("validation_tasks"):
                result_text += "Validazione e Test:\n"
                for i, task in enumerate(checklist["validation_tasks"], 1):
                    result_text += f"   {i}. {task}\n"

            result_text += f"\nChecklist generata da: {self.current_llm_provider.value}"

            print("[MCP] >> generate_change_checklist completed", file=sys.stderr)
            return [TextContent(type="text", text=result_text)]

        except Exception as e:
            error_msg = f"Errore generazione checklist: {str(e)}"
            print(f"[MCP] >> [ERROR] {error_msg}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            return [TextContent(type="text", text=error_msg)]

    async def _handle_enhance_asset_documentation(
        self, asset_id: str, include_lineage_context: bool = True, business_domain: str = ""
    ) -> List[TextContent]:
        """Enhance asset documentation with AI."""
        print(f"[MCP] >> Executing enhance_asset_documentation: {asset_id}", file=sys.stderr)

        try:
            asset_metadata = await self.lineage_builder.get_asset_metadata(asset_id)

            lineage_context = {}
            if include_lineage_context:
                upstream = await self.lineage_builder.get_immediate_lineage(asset_id, "upstream")
                lineage_context = {"upstream": upstream}

            business_context = {}
            if business_domain:
                business_context["domain"] = business_domain

            enhanced_docs = await self.llm_client.enhance_documentation(
                asset_info=asset_metadata, lineage_context=lineage_context, business_context=business_context
            )

            result_text = f"Documentazione Arricchita per {asset_id}:\n\n"
            result_text += f"Asset: {asset_metadata['name']}\n"
            result_text += f"Tipo: {asset_metadata['classType']}\n\n"

            if enhanced_docs.get("enhanced_description"):
                result_text += "Descrizione Arricchita:\n"
                result_text += f"{enhanced_docs['enhanced_description']}\n\n"

            if enhanced_docs.get("business_purpose"):
                result_text += "Scopo Business:\n"
                result_text += f"{enhanced_docs['business_purpose']}\n\n"

            if enhanced_docs.get("suggested_tags"):
                result_text += "Tag Suggeriti:\n"
                result_text += f"{', '.join(enhanced_docs['suggested_tags'])}\n\n"

            result_text += f"Enhancement generato da: {self.current_llm_provider.value}"

            print("[MCP] >> enhance_asset_documentation completed", file=sys.stderr)
            return [TextContent(type="text", text=result_text)]

        except Exception as e:
            error_msg = f"Errore enhancement documentazione: {str(e)}"
            print(f"[MCP] >> [ERROR] {error_msg}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            return [TextContent(type="text", text=error_msg)]

    async def _handle_switch_llm_provider(self, provider: str) -> List[TextContent]:
        """Switch LLM provider at runtime."""
        print(f"[MCP] >> Executing switch_llm_provider: {provider}", file=sys.stderr)

        try:
            if provider.lower() == "tinyllama":
                new_provider = LLMProvider.TINYLLAMA
            elif provider.lower() == "claude":
                new_provider = LLMProvider.CLAUDE
            elif provider.lower() == "gemma3":
                new_provider = LLMProvider.GEMMA3
            else:
                return [
                    TextContent(
                        type="text", text=f"Provider non supportato: {provider}. Usa 'tinyllama', 'claude' o 'gemma3'"
                    )
                ]

            if new_provider == self.current_llm_provider:
                return [TextContent(type="text", text=f"Provider {provider} gia attivo")]

            old_provider = self.current_llm_provider.value
            self.current_llm_provider = new_provider
            self._initialize_llm()

            print(f"[MCP] >> Provider switched: {old_provider} -> {new_provider.value}", file=sys.stderr)
            return [TextContent(type="text", text=f"Provider LLM cambiato da {old_provider} a {new_provider.value}")]

        except Exception as e:
            error_msg = f"Errore switch provider: {str(e)}"
            print(f"[MCP] >> [ERROR] {error_msg}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            return [TextContent(type="text", text=error_msg)]

    async def _handle_get_llm_status(self) -> List[TextContent]:
        """Get current LLM system status."""
        print("[MCP] >> Executing get_llm_status", file=sys.stderr)

        try:
            status_text = "Stato Sistema LLM:\n\n"
            status_text += f"Provider Attivo: {self.current_llm_provider.value}\n\n"

            tinyllama_available = settings.is_tinyllama_available()
            status_text += f"TinyLlama (Raspberry): {'Disponibile' if tinyllama_available else 'Non disponibile'}\n"
            if tinyllama_available:
                status_text += f"  - URL: {settings.tinyllama_base_url}\n"
                status_text += f"  - Modello: {settings.tinyllama_model}\n"

            gemma3_available = settings.is_gemma3_available()
            status_text += f"\nGemma3 (Locale): {'Disponibile' if gemma3_available else 'Non disponibile'}\n"
            if gemma3_available:
                status_text += f"  - URL: {settings.gemma3_base_url}\n"
                status_text += f"  - Modello: {settings.gemma3_model}\n"

            claude_available = settings.is_claude_available()
            status_text += f"\nClaude API: {'Disponibile' if claude_available else 'Non disponibile'}\n"
            if claude_available:
                status_text += f"  - Modello: {settings.claude_model}\n"

            if self.lineage_builder:
                stats = self.lineage_builder.get_statistics()
                status_text += "\nStatistiche Sessione:\n"
                status_text += f"  - API calls EDC: {stats['total_requests']}\n"
                status_text += f"  - Nodi creati: {stats['nodes_created']}\n"
                status_text += f"  - Cache hits: {stats['cache_hits']}\n"

            print("[MCP] >> get_llm_status completed", file=sys.stderr)
            return [TextContent(type="text", text=status_text)]

        except Exception as e:
            error_msg = f"Errore recupero status: {str(e)}"
            print(f"[MCP] >> [ERROR] {error_msg}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            return [TextContent(type="text", text=error_msg)]

    async def _handle_get_system_statistics(self) -> List[TextContent]:
        """Get complete system statistics."""
        print("[MCP] >> Executing get_system_statistics", file=sys.stderr)

        try:
            stats_text = "Statistiche Sistema EDC-MCP-LLM:\n\n"
            stats_text += f"LLM Provider: {self.current_llm_provider.value}\n\n"

            if self.lineage_builder:
                edc_stats = self.lineage_builder.get_statistics()
                stats_text += "Statistiche EDC:\n"
                stats_text += f"  - Total API calls: {edc_stats['total_requests']}\n"
                stats_text += f"  - Cache hits: {edc_stats['cache_hits']}\n"
                stats_text += f"  - API errors: {edc_stats['api_errors']}\n"
                stats_text += f"  - Nodi creati: {edc_stats['nodes_created']}\n"
                stats_text += f"  - Cicli prevenuti: {edc_stats['cycles_prevented']}\n"

            stats_text += "\nConfigurazione:\n"
            stats_text += f"  - Max tree depth: {settings.lineage_max_depth}\n"
            stats_text += f"  - Request timeout: {settings.request_timeout}s\n"

            print("[MCP] >> get_system_statistics completed", file=sys.stderr)
            return [TextContent(type="text", text=stats_text)]

        except Exception as e:
            error_msg = f"Errore recupero statistiche: {str(e)}"
            print(f"[MCP] >> [ERROR] {error_msg}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            return [TextContent(type="text", text=error_msg)]

    # ====================================
    # PROMPT GENERATORS
    # ====================================

    async def _generate_analyze_asset_prompt(self, arguments: dict) -> GetPromptResult:
        """Genera prompt per analisi completa asset."""
        asset_id = arguments.get("asset_id")
        include_lineage = arguments.get("include_lineage", True)
        business_domain = arguments.get("business_domain", "")

        print(f"[MCP] >> Generazione prompt analyze_asset_comprehensive per {asset_id}", file=sys.stderr)

        prompt_text = """Analizza in modo completo questo asset del catalogo EDC - usa i tools MCP disponibili."""

        return GetPromptResult(
            description=f"Analisi completa dell'asset {asset_id}",
            messages=[PromptMessage(role="user", content=TextContent(type="text", text=prompt_text))],
        )

    async def _generate_impact_analysis_prompt(self, arguments: dict) -> GetPromptResult:
        """Genera prompt per analisi impatto."""
        asset_id = arguments.get("asset_id")
        change_type = arguments.get("change_type")
        change_description = arguments.get("change_description")

        print(f"[MCP] >> Generazione prompt impact_analysis per {asset_id}", file=sys.stderr)

        prompt_text = f"""Analizza impatto modifica su {asset_id} - usa analyze_change_impact tool."""

        return GetPromptResult(
            description=f"Analisi impatto modifica su {asset_id}",
            messages=[PromptMessage(role="user", content=TextContent(type="text", text=prompt_text))],
        )

    async def _generate_governance_review_prompt(self, arguments: dict) -> GetPromptResult:
        """Genera prompt per review governance."""
        asset_id = arguments.get("asset_id")
        review_type = arguments.get("review_type", "complete")

        print(f"[MCP] >> Generazione prompt governance_review per {asset_id}", file=sys.stderr)

        prompt_text = f"""Conduci review governance per {asset_id} - usa get_asset_details tool."""

        return GetPromptResult(
            description=f"Review governance per {asset_id}",
            messages=[PromptMessage(role="user", content=TextContent(type="text", text=prompt_text))],
        )

    async def _generate_lineage_investigation_prompt(self, arguments: dict) -> GetPromptResult:
        """Genera prompt per investigazione lineage."""
        asset_id = arguments.get("asset_id")
        investigation_goal = arguments.get("investigation_goal")
        depth = arguments.get("depth", 3)

        print(f"[MCP] >> Generazione prompt lineage_investigation per {asset_id}", file=sys.stderr)

        prompt_text = f"""Investiga lineage per {asset_id} - usa get_lineage_tree tool."""

        return GetPromptResult(
            description=f"Investigazione lineage per {asset_id}",
            messages=[PromptMessage(role="user", content=TextContent(type="text", text=prompt_text))],
        )

    async def _generate_migration_planning_prompt(self, arguments: dict) -> GetPromptResult:
        """Genera prompt per pianificazione migrazione."""
        asset_id = arguments.get("asset_id")
        target_environment = arguments.get("target_environment")
        migration_type = arguments.get("migration_type", "lift_and_shift")

        print(f"[MCP] >> Generazione prompt migration_planning per {asset_id}", file=sys.stderr)

        prompt_text = f"""Pianifica migrazione {asset_id} verso {target_environment}."""

        return GetPromptResult(
            description=f"Piano migrazione {asset_id}",
            messages=[PromptMessage(role="user", content=TextContent(type="text", text=prompt_text))],
        )

    async def _generate_documentation_enhancement_prompt(self, arguments: dict) -> GetPromptResult:
        """Genera prompt per arricchimento documentazione."""
        asset_id = arguments.get("asset_id")
        documentation_level = arguments.get("documentation_level", "comprehensive")

        print(f"[MCP] >> Generazione prompt documentation_enhancement per {asset_id}", file=sys.stderr)

        prompt_text = f"""Arricchisci documentazione per {asset_id} - usa enhance_asset_documentation tool."""

        return GetPromptResult(
            description=f"Documentazione per {asset_id}",
            messages=[PromptMessage(role="user", content=TextContent(type="text", text=prompt_text))],
        )

    async def cleanup(self) -> None:
        """Cleanup resources."""
        print("[MCP] Cleanup risorse...", file=sys.stderr)
        if self.lineage_builder:
            await self.lineage_builder.close()
        print("[MCP] Cleanup completato", file=sys.stderr)


async def main():
    """Entry point principale del server MCP."""

    # Setup logging to stderr
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", stream=sys.stderr
    )

    print("=" * 70, file=sys.stderr)
    print("[START] EDC-MCP-LLM Server - VERSIONE DEBUG", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print(f"Python: {sys.version}", file=sys.stderr)
    print(f"CWD: {os.getcwd()}", file=sys.stderr)
    print(f"Environment: {settings.environment.value}", file=sys.stderr)
    print(f"EDC URL: {settings.edc_base_url}", file=sys.stderr)
    print(f"LLM Provider: {settings.default_llm_provider.value}", file=sys.stderr)
    print("=" * 70, file=sys.stderr)

    try:
        print("[INIT] Creazione istanza EDCMCPServer...", file=sys.stderr)
        server = EDCMCPServer()
        print("[INIT] [OK] Server creato con successo", file=sys.stderr)

        # Verifica disponibilitÃ  LLM (non bloccante)
        print("[CHECK] Verifica disponibilita provider LLM...", file=sys.stderr)
        if settings.default_llm_provider == LLMProvider.CLAUDE:
            if not settings.is_claude_available():
                print("[WARNING] Claude API key non configurata!", file=sys.stderr)
        elif settings.default_llm_provider == LLMProvider.TINYLLAMA:
            if not settings.is_ollama_available():
                print("[WARNING] Ollama non disponibile!", file=sys.stderr)

        print("[STDIO] Avvio stdio_server...", file=sys.stderr)

        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            print("[STDIO] [OK] Streams connessi", file=sys.stderr)
            print("[RUN] Avvio server.run()...", file=sys.stderr)

            # Flush per assicurarsi che i log vengano scritti
            sys.stderr.flush()

            await server.server.run(read_stream, write_stream, server.server.create_initialization_options())

    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Shutdown richiesto...", file=sys.stderr)
    except Exception as e:
        print(f"\n[ERROR] ERRORE FATALE: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    finally:
        if "server" in locals():
            print("[CLEANUP] Cleanup risorse...", file=sys.stderr)
            await server.cleanup()
        print("[DONE] Server terminato", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
