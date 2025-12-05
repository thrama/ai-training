# test_edc_llm_integration.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
import json
from dotenv import load_dotenv
from src.edc.client import EDCClient
from src.llm.factory import LLMFactory, LLMConfig, LLMProvider

load_dotenv()

async def test_integration():
    """Test integrazione EDC + LLM."""
    
    print("="*60)
    print("🔗 Test Integrazione EDC + LLM")
    print("="*60)
    
    # Asset reale Allitude
    asset_id = "DataPlatform://ORAC51/DWHEVO/IFR_WK_GARANZIE_SOFFERENZE_DT_AP"
    
    # Configura LLM
    llm_config = LLMConfig(
        provider=LLMProvider.TINYLLAMA,
        model_name="tinyllama",
        base_url="http://192.168.1.17:11434",
        max_tokens=2000,
        temperature=0.1
    )
    
    llm_client = LLMFactory.create_llm_client(llm_config)
    
    # Connetti a EDC
    async with EDCClient() as edc_client:
        
        print(f"\n1️⃣  Recupero asset da EDC...")
        print(f"   Asset ID: {asset_id}")
        
        try:
            asset_details = await edc_client.get_asset_details(asset_id)
            
            # 🔍 DEBUG: Stampa struttura completa
            print("\n" + "="*60)
            print("🔍 DEBUG: Struttura dati ricevuta")
            print("="*60)
            print(json.dumps(asset_details, indent=2, ensure_ascii=False)[:2000])
            print("="*60)
            
            # Prova ad accedere ai campi in modo sicuro
            name = asset_details.get('name', 'N/A')
            class_type = asset_details.get('classType', 'N/A')
            description = asset_details.get('description', '')
            
            print(f"\n✅ Asset trovato!")
            print(f"   Nome: {name}")
            print(f"   Tipo: {class_type}")
            print(f"   Descrizione: {description[:100] if description else 'Nessuna'}...")
            
            # Se ha una descrizione, prova l'enhancement
            if name != 'N/A':
                print("\n2️⃣  Arricchimento con LLM...")
                
                enhanced = await llm_client.enhance_description(
                    asset_name=name,
                    technical_desc=description,
                    schema_context="Banking - Mutui",
                    column_info=[]
                )
                
                print(f"✨ Descrizione arricchita:")
                print(f"{enhanced}")
            
        except KeyError as e:
            print(f"   ❌ Errore campo mancante: {e}")
            print("   💡 Vedi output DEBUG sopra per capire la struttura")
        except Exception as e:
            print(f"   ❌ Errore: {e}")
            import traceback
            traceback.print_exc()
    
    await llm_client.close()
    
    print("\n" + "="*60)
    print("✅ Test completato!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_integration())