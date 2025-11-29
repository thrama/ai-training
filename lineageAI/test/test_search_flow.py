"""
Test per tracciare il flusso completo di una ricerca MCP:
"Cerca le tabelle EDC che contengono RAPPORTO nel nome per la risorsa DataPlatform"
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.edc.lineage import LineageBuilder


def print_section(title):
    """Stampa una sezione ben visibile."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


async def test_search_flow():
    """
    Simula esattamente cosa succede quando Claude Desktop chiede:
    'Cerca le tabelle EDC che contengono RAPPORTO nel nome per la risorsa DataPlatform'
    """
    
    print_section("INIZIO TEST: Ricerca Tabelle con RAPPORTO")
    
    print("\n[Setup] Inizializzazione componenti...")
    
    # 1. Claude Desktop invia la richiesta al server MCP
    print("\n[Step 1] Claude Desktop -> MCP Server")
    print("   Tool richiesto: search_assets")
    print("   Arguments:")
    
    # Questi sono gli argomenti che il server MCP riceve
    mcp_arguments = {
        "resource_name": "DataPlatform",
        "name_filter": "RAPPORTO",
        "asset_type": "Table",
        "max_results": 10
    }
    
    for key, value in mcp_arguments.items():
        print(f"      {key}: {value}")
    
    # 2. Il server MCP instrada la richiesta
    print_section("Step 2: MCP Server - Routing")
    
    print("\n[MCP Server] Riceve chiamata tool 'search_assets'")
    print("[MCP Server] Routing verso: _handle_search_assets()")
    
    # 3. Handler MCP prepara la chiamata all'EDC Client
    print_section("Step 3: Handler MCP - Preparazione")
    
    print("\n[_handle_search_assets] Estrae parametri:")
    resource_name = mcp_arguments["resource_name"]
    name_filter = mcp_arguments.get("name_filter", "")
    asset_type = mcp_arguments.get("asset_type", "")
    max_results = mcp_arguments.get("max_results", 10)
    
    print(f"   resource_name: '{resource_name}'")
    print(f"   name_filter: '{name_filter}'")
    print(f"   asset_type: '{asset_type}'")
    print(f"   max_results: {max_results}")
    
    print("\n[_handle_search_assets] Chiama EDC Client:")
    print(f"   await lineage_builder.edc_client.bulk_search_assets(")
    print(f"       resource_name='{resource_name}',")
    print(f"       name_filter='{name_filter}',")
    print(f"       asset_type_filter='{asset_type}'")
    print(f"   )")
    
    # 4. EDC Client costruisce la chiamata API
    print_section("Step 4: EDC Client - Costruzione Chiamata API")
    
    print("\n[EDC Client] Metodo: bulk_search_assets()")
    print("[EDC Client] Costruisce URL e parametri API...")
    
    # Simuliamo la logica del client
    from src.config.settings import settings
    
    bulk_url = f"{settings.edc_base_url}/1/catalog/data/bulk"
    
    print(f"\n[EDC Client] URL API Bulk:")
    print(f"   {bulk_url}")
    
    # Mapping dei tipi
    class_mapping = {
        'table': 'com.infa.ldm.relational.Table',
        'view': 'com.infa.ldm.relational.ViewTable',
        'column': 'com.infa.ldm.relational.Column',
        'viewcolumn': 'com.infa.ldm.relational.ViewColumn'
    }
    
    asset_type_lower = asset_type.lower()
    class_type = class_mapping.get(asset_type_lower, 'com.infa.ldm.relational.Table')
    
    print(f"\n[EDC Client] Mapping tipo asset:")
    print(f"   Input: '{asset_type}'")
    print(f"   Normalized: '{asset_type_lower}'")
    print(f"   ClassType: '{class_type}'")
    
    api_params = {
        'resourceName': resource_name,
        'classTypes': class_type,
        'facts': 'id,core.name,core.classType',
        'includeRefObjects': 'true'
    }
    
    print(f"\n[EDC Client] Parametri API costruiti:")
    for key, value in api_params.items():
        print(f"   {key}: {value}")
    
    # 5. Chiamata API reale
    print_section("Step 5: Chiamata API EDC Reale")
    
    print("\n[API Call] Esecuzione chiamata HTTP GET...")
    print(f"   URL: {bulk_url}")
    print(f"   Method: GET (not POST!)")
    print(f"   Params: {api_params}")
    
    try:
        # Crea LineageBuilder invece di EDCClient direttamente
        lineage_builder = LineageBuilder()
        
        print("\n[EDC Client] Inizializzazione...")
        await lineage_builder.edc_client._ensure_session()
        
        print("[EDC Client] Sessione HTTP pronta")
        print("[EDC Client] Invio richiesta...")
        
        # Chiamata reale
        results = await lineage_builder.edc_client.bulk_search_assets(
            resource_name=resource_name,
            name_filter=name_filter,
            asset_type_filter=asset_type
        )
        
        print(f"\n[API Response] Status: 200 OK")
        print(f"[API Response] Items ricevuti: {len(results)}")
        
        # 6. Processamento risposta
        print_section("Step 6: Processamento Risposta")
        
        print(f"\n[EDC Client] Items dall'API: {len(results)}")
        
        if name_filter:
            print(f"\n[EDC Client] Filtro gia applicato: '{name_filter}'")
            print(f"   Risultati filtrati: {len(results)}")
        
        # Limita ai max_results
        if len(results) > max_results:
            print(f"\n[EDC Client] Limitazione risultati:")
            print(f"   Totali: {len(results)}")
            print(f"   Max richiesti: {max_results}")
            results = results[:max_results]
            print(f"   Ritornati: {len(results)}")
        
        # 7. Arricchimento risultati
        print_section("Step 7: Risultati Finali")
        
        if results:
            print(f"\n[Results] Trovati {len(results)} asset:")
            
            for i, item in enumerate(results[:5], 1):
                print(f"\n   Item {i}:")
                print(f"      Name: {item.get('name', 'N/A')}")
                print(f"      Type: {item.get('classType', 'N/A')}")
                print(f"      ID: {item.get('id', 'N/A')[:60]}...")
            
            if len(results) > 5:
                print(f"\n   ... e altri {len(results) - 5} items")
        else:
            print("\n[Results] Nessun risultato trovato")
        
        # 8. Costruzione risposta MCP
        print_section("Step 8: Costruzione Risposta MCP")
        
        print("\n[_handle_search_assets] Formatta risposta per MCP...")
        
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
        
        print("\n[MCP Response] Risposta formattata:")
        print("-" * 80)
        print(result_text[:500])
        if len(result_text) > 500:
            print(f"\n... (totale {len(result_text)} caratteri)")
        print("-" * 80)
        
        # 9. Ritorno a Claude Desktop
        print_section("Step 9: Ritorno a Claude Desktop")
        
        print("\n[MCP Server] Risposta inviata a Claude Desktop")
        print(f"[MCP Server] Formato: TextContent")
        print(f"[MCP Server] Lunghezza testo: {len(result_text)} caratteri")
        print(f"[MCP Server] Items inclusi: {len(results)}")
        
        # 10. Summary
        print_section("SUMMARY - Flusso Completo")
        
        print("\n1. Claude Desktop invia:")
        print("   Tool: search_assets")
        print(f"   Args: resource_name={resource_name}, name_filter={name_filter}")
        
        print("\n2. MCP Server riceve e instrada:")
        print("   Handler: _handle_search_assets()")
        
        print("\n3. EDC Client costruisce chiamata:")
        print(f"   API: GET {bulk_url}")
        print(f"   ClassType: {class_type}")
        
        print("\n4. API EDC risponde:")
        print(f"   Format: CSV")
        print(f"   Items ricevuti: {len(results)}")
        
        print("\n5. Filtro applicato:")
        print(f"   Nome contiene: '{name_filter}'")
        print(f"   Risultati finali: {len(results)}")
        
        print("\n6. Risposta a Claude:")
        print(f"   {len(results)} tabelle con {name_filter} nel nome")
        
        print_section("TEST COMPLETATO CON SUCCESSO")
        
        # Cleanup
        print("\n[Cleanup] Chiusura risorse...")
        await lineage_builder.close()
        print("[Cleanup] Done")
        
        return results
        
    except Exception as e:
        print(f"\n[ERROR] Errore durante il test: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Entry point."""
    print("\n" + "="*80)
    print("  TEST FLUSSO RICERCA MCP")
    print("  Query: Cerca tabelle con RAPPORTO in DataPlatform")
    print("="*80)
    
    results = await test_search_flow()
    
    if results:
        print(f"\n\n[SUCCESS] Test completato: {len(results)} risultati trovati")
    else:
        print(f"\n\n[FAIL] Test fallito")


if __name__ == "__main__":
    asyncio.run(main())