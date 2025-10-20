#!/usr/bin/env python3
"""
EDC API Server - Bridge tra Interfaccia Web e Backend Python
Espone le funzionalita MCP via REST API per l'interfaccia web.
Sviluppato per Lorenzo - Principal Data Architect @ NTT Data Italia
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import dei moduli reali
from src.edc.lineage import LineageBuilder
from src.llm.factory import LLMFactory, LLMConfig
from src.config.settings import settings, LLMProvider

# Modelli Pydantic per validazione request
class SearchAssetsRequest(BaseModel):
    resource_name: str
    name_filter: Optional[str] = None
    asset_type: Optional[str] = None
    max_results: int = 20

class BuildLineageRequest(BaseModel):
    asset_id: str
    direction: str = "both"
    depth: int = 3

class AnalyzeImpactRequest(BaseModel):
    asset_id: str
    change_type: str
    change_description: str

class GenerateChecklistRequest(BaseModel):
    asset_id: str
    change_description: str
    context: Optional[str] = None

class SwitchLLMRequest(BaseModel):
    provider: str


# Inizializza FastAPI
app = FastAPI(
    title="EDC Explorer API",
    description="API Server per EDC Lineage Explorer",
    version="1.0.0"
)

# Abilita CORS per permettere richieste dall'interfaccia web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specifica il dominio esatto
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stato globale
lineage_builder: Optional[LineageBuilder] = None
llm_client = None
current_llm_provider = settings.default_llm_provider


@app.on_event("startup")
async def startup_event():
    """Inizializza i componenti al startup."""
    global lineage_builder, llm_client
    
    print("=" * 70)
    print("EDC API Server - Starting")
    print("=" * 70)
    
    try:
        # Inizializza LineageBuilder
        print("Initializing LineageBuilder...")
        lineage_builder = LineageBuilder()
        print("✓ LineageBuilder initialized")
        
        # Inizializza LLM
        print(f"Initializing LLM ({current_llm_provider.value})...")
        
        if current_llm_provider == LLMProvider.TINYLLAMA:
            llm_config = LLMConfig(
                provider=LLMProvider.TINYLLAMA,
                model_name=settings.tinyllama_model,
                base_url=settings.ollama_base_url,
                max_tokens=settings.tinyllama_max_tokens,
                temperature=settings.tinyllama_temperature
            )
        elif current_llm_provider == LLMProvider.CLAUDE:
            if not settings.claude_api_key:
                raise ValueError("Claude API key not configured in .env")
            
            llm_config = LLMConfig(
                provider=LLMProvider.CLAUDE,
                model_name=settings.claude_model,
                api_key=settings.claude_api_key,
                max_tokens=settings.claude_max_tokens,
                temperature=settings.claude_temperature
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {current_llm_provider}")
        
        llm_client = LLMFactory.create_llm_client(llm_config)
        print(f"✓ LLM client initialized ({current_llm_provider.value})")
        
        print("=" * 70)
        print("EDC API Server - Ready")
        print(f"EDC URL: {settings.edc_base_url}")
        print(f"LLM Provider: {current_llm_provider.value}")
        print("=" * 70)
        
    except Exception as e:
        print(f"ERROR during startup: {e}")
        import traceback
        traceback.print_exc()
        raise


@app.get("/")
async def root():
    """Endpoint root per health check."""
    return {
        "service": "EDC Explorer API",
        "status": "running",
        "edc_url": settings.edc_base_url,
        "llm_provider": current_llm_provider.value,
        "version": "1.0.0"
    }


@app.post("/api/mcp/search_assets")
async def search_assets(request: SearchAssetsRequest):
    """
    Cerca asset nel catalogo EDC.
    
    Endpoint chiamato dall'interfaccia web quando clicchi "CERCA ASSET".
    """
    if not lineage_builder:
        raise HTTPException(status_code=500, detail="LineageBuilder not initialized")
    
    start_time = datetime.now()
    
    try:
        print(f"\n[API] search_assets chiamato")
        print(f"  Resource: {request.resource_name}")
        print(f"  Filter: {request.name_filter}")
        print(f"  Type: {request.asset_type}")
        
        # Chiama il metodo reale dell'EDC
        results = await lineage_builder.edc_client.bulk_search_assets(
            resource_name=request.resource_name,
            name_filter=request.name_filter or "",
            asset_type_filter=request.asset_type or ""
        )
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        print(f"  Results: {len(results)} asset trovati")
        print(f"  Execution time: {execution_time:.0f}ms")
        
        # Formatta i risultati per l'interfaccia web
        formatted_results = []
        for item in results[:request.max_results]:
            # Estrai informazioni dall'asset
            asset_id = item.get('id', 'N/A')
            name = item.get('core.name', item.get('name', 'N/A'))
            class_type = item.get('core.classType', item.get('classType', 'N/A'))
            
            # Estrai connection e schema dall'ID
            # Formato: DataPlatform://CONNECTION/SCHEMA/TABLE
            connection = "N/A"
            schema = "N/A"
            if '://' in asset_id:
                try:
                    parts = asset_id.split('://')[1].split('/')
                    connection = parts[0] if len(parts) > 0 else "N/A"
                    schema = parts[1] if len(parts) > 1 else "N/A"
                except:
                    pass
            
            # Tipo breve
            type_short = class_type.split('.')[-1] if '.' in class_type else class_type
            
            formatted_results.append({
                "id": asset_id,
                "name": name,
                "type": type_short,
                "classType": class_type,
                "connection": connection,
                "schema": schema
            })
        
        return {
            "success": True,
            "results": formatted_results,
            "results_count": len(formatted_results),
            "total_found": len(results),
            "resource": request.resource_name,
            "filter_applied": request.name_filter or "none",
            "execution_time_ms": int(execution_time)
        }
        
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mcp/build_lineage_tree")
async def build_lineage_tree(request: BuildLineageRequest):
    """Costruisce l'albero di lineage."""
    if not lineage_builder:
        raise HTTPException(status_code=500, detail="LineageBuilder not initialized")
    
    start_time = datetime.now()
    
    try:
        print(f"\n[API] build_lineage_tree chiamato")
        print(f"  Asset ID: {request.asset_id}")
        print(f"  Direction: {request.direction}")
        print(f"  Depth: {request.depth}")
        
        # Costruisci il tree
        tree = await lineage_builder.build_tree(
            root_asset_id=request.asset_id,
            max_depth=request.depth
        )
        
        # Formatta l'albero come testo
        tree_text = lineage_builder._format_tree_as_text(tree)
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        print(f"  Tree nodes: {len(tree)}")
        print(f"  Execution time: {execution_time:.0f}ms")
        
        # Opzionale: analisi AI della complessità
        analysis_text = ""
        if llm_client:
            try:
                print(f"  Running AI analysis...")
                prompt = f"Analyze this data lineage tree:\n\n{tree_text[:1000]}\n\nProvide a brief complexity analysis."
                analysis_text = await llm_client.generate(prompt, max_tokens=500)
                print(f"  AI analysis completed")
            except Exception as e:
                print(f"  AI analysis failed: {e}")
                analysis_text = f"AI analysis not available: {e}"
        
        return {
            "success": True,
            "tree_text": tree_text,
            "analysis_text": analysis_text,
            "node_count": len(tree),
            "max_depth_reached": request.depth,
            "has_cycles": False,  # TODO: implement cycle detection
            "execution_time_ms": int(execution_time)
        }
        
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mcp/analyze_impact")
async def analyze_impact(request: AnalyzeImpactRequest):
    """Analizza l'impatto di una modifica."""
    if not lineage_builder or not llm_client:
        raise HTTPException(status_code=500, detail="Services not initialized")
    
    start_time = datetime.now()
    
    try:
        print(f"\n[API] analyze_impact chiamato")
        print(f"  Asset ID: {request.asset_id}")
        print(f"  Change type: {request.change_type}")
        
        # Costruisci lineage per analisi
        tree = await lineage_builder.build_tree(
            root_asset_id=request.asset_id,
            max_depth=3
        )
        
        downstream_count = sum(1 for node in tree if node.parent_id == request.asset_id)
        
        # Genera analisi AI
        prompt = f"""
Analyze the impact of this change:

Asset: {request.asset_id}
Change Type: {request.change_type}
Description: {request.change_description}
Downstream Dependencies: {downstream_count}

Provide:
1. Risk level (LOW/MEDIUM/HIGH)
2. Estimated impacted assets
3. Business impact assessment
4. Timeline for implementation
5. Key recommendations
"""
        
        analysis = await llm_client.generate(prompt, max_tokens=1000)
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        print(f"  Analysis completed")
        print(f"  Execution time: {execution_time:.0f}ms")
        
        return {
            "success": True,
            "analysis_text": analysis,
            "impacted_assets": downstream_count,
            "downstream_tables": downstream_count,
            "risk_level": "MEDIUM",  # TODO: parse from AI response
            "execution_time_ms": int(execution_time)
        }
        
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mcp/generate_operational_checklist")
async def generate_checklist(request: GenerateChecklistRequest):
    """Genera checklist operativa."""
    if not llm_client:
        raise HTTPException(status_code=500, detail="LLM not initialized")
    
    start_time = datetime.now()
    
    try:
        print(f"\n[API] generate_checklist chiamato")
        print(f"  Asset ID: {request.asset_id}")
        
        prompt = f"""
Generate a detailed operational checklist for this change:

Asset: {request.asset_id}
Change: {request.change_description}
Context: {request.context or 'Standard change management'}

Include:
1. Pre-change tasks (preparation, backups, approvals)
2. Implementation tasks (execution steps)
3. Post-change tasks (verification, documentation)
4. Rollback plan
5. Stakeholder communication plan

Format as a numbered checklist with checkboxes.
"""
        
        checklist = await llm_client.generate(prompt, max_tokens=1500)
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        print(f"  Checklist generated")
        print(f"  Execution time: {execution_time:.0f}ms")
        
        return {
            "success": True,
            "checklist_text": checklist,
            "total_tasks": 30,  # TODO: count from generated text
            "estimated_time_hours": 6,
            "execution_time_ms": int(execution_time)
        }
        
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mcp/switch_llm_provider")
async def switch_llm(request: SwitchLLMRequest):
    """Cambia provider LLM."""
    global llm_client, current_llm_provider
    
    try:
        print(f"\n[API] switch_llm_provider chiamato")
        print(f"  New provider: {request.provider}")
        
        # Mappa stringa a enum
        if request.provider.lower() == "tinyllama":
            new_provider = LLMProvider.TINYLLAMA
        elif request.provider.lower() == "claude":
            new_provider = LLMProvider.CLAUDE
        else:
            raise ValueError(f"Unknown provider: {request.provider}")
        
        # Crea nuovo client
        llm_config = LLMConfig(provider=new_provider)
        llm_client = LLMFactory.create_client(llm_config)
        current_llm_provider = new_provider
        
        print(f"  LLM switched to: {new_provider.value}")
        
        return {
            "success": True,
            "provider": new_provider.value,
            "message": f"LLM provider switched to {new_provider.value}"
        }
        
    except Exception as e:
        print(f"  ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mcp/system_status")
async def system_status():
    """Ritorna lo stato del sistema."""
    return {
        "status": "running",
        "edc_connected": lineage_builder is not None,
        "edc_url": settings.edc_base_url,
        "llm_provider": current_llm_provider.value,
        "llm_available": llm_client is not None
    }


def main():
    """Avvia il server API."""
    print("\n" + "=" * 70)
    print("EDC API Server")
    print("=" * 70)
    print(f"EDC URL: {settings.edc_base_url}")
    print(f"Default LLM: {settings.default_llm_provider.value}")
    print("=" * 70)
    print("\nStarting server on http://localhost:8080")
    print("Documentation: http://localhost:8080/docs")
    print("\nPress Ctrl+C to stop")
    print("=" * 70 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )


if __name__ == "__main__":
    main()