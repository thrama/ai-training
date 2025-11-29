# test_complete_integration.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from dotenv import load_dotenv
from src.edc.client import EDCClient
from src.llm.factory import LLMFactory, LLMConfig, LLMProvider

load_dotenv()

async def test_complete():
    """Test integrazione completa EDC + LLM con asset reale."""
    
    print("="*60)
    print("🚀 Test Integrazione Completa EDC + LLM")
    print("="*60)
    
    # Configura LLM
    llm_config = LLMConfig(
        provider=LLMProvider.TINYLLAMA,
        model_name="tinyllama",
        base_url="http://192.168.1.17:11434",
        max_tokens=2000,
        temperature=0.1
    )
    
    llm_client = LLMFactory.create_llm_client(llm_config)
    
    async with EDCClient() as edc_client:
        
        # Step 1: Cerca asset
        print("\n1️⃣  Ricerca asset GARANZIE in EDC...")
        print("-"*60)
        
        results = await edc_client.search_assets("*GARANZIE*", {})
        print(f"✅ Trovati {len(results)} asset\n")
        
        if not results:
            print("❌ Nessun asset trovato")
            return
        
        # Prendi il primo asset
        first_asset = results[0]
        asset_id = first_asset['id']
        asset_name = first_asset['name']
        
        print(f"📋 Asset selezionato: {asset_name}")
        print(f"   ID: {asset_id}")
        
        # Step 2: Recupera dettagli completi
        print(f"\n2️⃣  Recupero dettagli completi...")
        print("-"*60)
        
        details = await edc_client.get_asset_details(asset_id)
        
        print(f"✅ Dettagli recuperati:")
        print(f"   Nome: {details['name']}")
        print(f"   Tipo: {details['classType']}")
        print(f"   Descrizione: {details['description'][:100] if details['description'] else 'Nessuna'}...")
        print(f"   Upstream: {len(details['src_links'])} asset")
        print(f"   Downstream: {len(details['dst_links'])} asset")
        
        # Step 3: Enhancement con LLM
        print(f"\n3️⃣  Arricchimento descrizione con AI...")
        print("-"*60)
        
        enhanced = await llm_client.enhance_description(
            asset_name=details['name'],
            technical_desc=details['description'],
            schema_context="Banking - Garanzie",
            column_info=[]
        )
        
        print(f"📝 Descrizione originale:")
        print(f"   {details['description'][:150] if details['description'] else 'Nessuna'}...")
        print(f"\n✨ Descrizione arricchita AI:")
        print(f"   {enhanced}")
        
        # Step 4: Analisi Lineage se disponibile
        if details['src_links']:
            print(f"\n4️⃣  Analisi Lineage Upstream")
            print("-"*60)
            
            print(f"📥 Sorgenti dati ({len(details['src_links'])}):")
            for i, link in enumerate(details['src_links'][:5], 1):
                print(f"   {i}. {link['name']}")
                print(f"      Type: {link['classType']}")
                print(f"      Association: {link['association']}")
            
            # Analisi complessità
            lineage_data = {
                'id': asset_id,
                'code': '001',
                'children_count': len(details['src_links']),
                'node_type': details['classType'],
                'is_terminal': len(details['src_links']) == 0
            }
            
            complexity = await llm_client.analyze_lineage_complexity(lineage_data)
            
            print(f"\n📊 Analisi Complessità:")
            print(f"   Score: {complexity['complexity_score']}/10")
            print(f"   Risk Level: {complexity['risk_level']}")
            print(f"   Risk Factors:")
            for factor in complexity['risk_factors'][:3]:
                print(f"      - {factor}")
        
        # Step 5: Scenario di Change Impact
        if details['dst_links']:
            print(f"\n5️⃣  Analisi Impatto Modifica")
            print("-"*60)
            print(f"   Scenario: Deprecazione asset {asset_name}")
            
            affected_lineage = {
                'downstream': [
                    {
                        'asset_id': link['id'],
                        'name': link['name'],
                        'classType': link['classType']
                    }
                    for link in details['dst_links'][:10]
                ]
            }
            
            impact = await llm_client.analyze_change_impact(
                source_asset=asset_name,
                change_type="deprecation",
                change_details={
                    "description": f"Deprecazione asset {asset_name}",
                },
                affected_lineage=affected_lineage
            )
            
            print(f"\n   🎯 Risk Level: {impact['risk_level']}")
            print(f"   📊 Asset Impattati: {len(affected_lineage['downstream'])}")
            print(f"\n   💡 Top 3 Raccomandazioni:")
            for i, rec in enumerate(impact['recommendations'][:3], 1):
                print(f"      {i}. {rec}")
        
        # Statistiche finali
        print(f"\n6️⃣  Statistiche Sessione")
        print("-"*60)
        stats = edc_client.get_statistics()
        print(f"   EDC API calls: {stats['total_requests']}")
        print(f"   Cache hits: {stats['cache_hits']}")
        print(f"   Errors: {stats['api_errors']}")
        
    await llm_client.close()
    
    print("\n" + "="*60)
    print("✅ Test Integrazione Completato con Successo!")
    print("="*60)
    print("\n💡 Il sistema EDC + LLM è pienamente funzionante!")

if __name__ == "__main__":
    asyncio.run(test_complete())