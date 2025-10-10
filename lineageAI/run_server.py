"""
Script per avviare il server MCP EDC-LLM SENZA BUFFERING.
Versione ULTRA-ROBUSTA per Windows che garantisce output immediato.
"""
import asyncio
import sys
import os
from pathlib import Path

# STEP 1: Forza unbuffered mode via environment PRIMA di tutto
os.environ['PYTHONUNBUFFERED'] = '1'

# STEP 2: Aggiungi al path PRIMA di importare src.*
sys.path.insert(0, str(Path(__file__).parent))

# STEP 3: Importa settings (che a sua volta modifica stdout/stderr)
from src.config.settings import settings, LLMProvider

# STEP 4: SOLO ORA applica riconfigurazioni aggiuntive
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

# STEP 5: Importa il resto
from src.mcp.server import EDCMCPServer


async def standalone_server():
    """Avvia server in modalità standalone per test."""
    
    print("="*70)
    print("[Standalone] MCP Server EDC-LLM - Modalità Test UNBUFFERED")
    print("="*70)
    print(f"Environment: {settings.environment.value}")
    print(f"EDC URL: {settings.edc_base_url}")
    print(f"LLM Provider: {settings.default_llm_provider.value}")
    print("="*70)
    
    try:
        print("\n[1/5] Creazione istanza EDCMCPServer...")
        server = EDCMCPServer()
        print("[OK] Server creato!")
        
        # Verifica disponibilità LLM
        print("\n[2/5] Verifica disponibilità provider LLM...")
        if settings.default_llm_provider == LLMProvider.CLAUDE:
            if not settings.is_claude_available():
                print("[Warning] Claude API key non configurata!")
                print("   Configura CLAUDE_API_KEY in .env")
            else:
                print("[OK] Claude disponibile")
        elif settings.default_llm_provider == LLMProvider.TINYLLAMA:
            if not settings.is_ollama_available():
                print("[Warning] Ollama non disponibile!")
                print("   Avvia Ollama con: ollama serve")
            else:
                print("[OK] TinyLlama/Ollama disponibile")
        
        print("\n[3/5] Server inizializzato con successo!")
        print("\n[4/5] Configurazione:")
        print("   - Modalità: STANDALONE TEST")
        print("   - Per Claude Desktop: python -m src.mcp.server")
        
        print("\n[5/5] Tools MCP disponibili:")
        tools = [
            "get_asset_details",
            "search_assets",
            "get_lineage_tree",
            "get_immediate_lineage",
            "analyze_change_impact",
            "generate_change_checklist",
            "enhance_asset_documentation",
            "switch_llm_provider",
            "get_llm_status",
            "get_system_statistics"
        ]
        for i, tool in enumerate(tools, 1):
            print(f"   {i:2}. {tool}")
        
        print("\n" + "="*70)
        print("[OK] SERVER PRONTO!")
        print("="*70)
        print("\n[Info] Per testare: python test_mcp_integration.py")
        print("\n[Ready] Server in attesa... (Premi Ctrl+C per terminare)")
        print()
        
        # Mantieni il server attivo con output periodico
        counter = 0
        while True:
            await asyncio.sleep(5)
            counter += 1
            if counter % 12 == 0:  # Ogni minuto
                print(f"[Heartbeat] Server attivo da {counter * 5} secondi...")
    
    except KeyboardInterrupt:
        print("\n\n[Shutdown] Shutdown richiesto dall'utente...")
    except Exception as e:
        print(f"\n[Error] Errore: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if 'server' in locals():
            print("\n[Cleanup] Chiusura risorse...")
            await server.cleanup()
            print("[OK] Cleanup completato")
        print("[Done] Server terminato\n")


def main():
    """Entry point."""
    print("\n" + "="*70)
    print("[START] AVVIO MCP SERVER - MODALITÀ TEST STANDALONE")
    print("="*70)
    print("[Info] Output unbuffered: ATTIVO")
    print("[Info] Dovresti vedere questo messaggio IMMEDIATAMENTE")
    print("="*70 + "\n")
    
    try:
        asyncio.run(standalone_server())
    except KeyboardInterrupt:
        print("\n[Exit] Terminato dall'utente")
    except Exception as e:
        print(f"\n[Fatal] Errore fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()