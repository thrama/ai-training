#!/usr/bin/env python3
"""
Test della ricerca intelligente che sceglie automaticamente l'API migliore.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from dotenv import load_dotenv
from src.edc.client import EDCClient

load_dotenv()


async def test_smart_search():
    """Test ricerca intelligente con vari tipi di query."""
    
    print("=" * 70)
    print("🧠 TEST RICERCA INTELLIGENTE")
    print("=" * 70)
    
    # Query di test che dovrebbero usare API diverse
    test_queries = [
        # Dovrebbero usare BULK (elenco completo)
        {
            'query': "tutte le tabelle di DataPlatform",
            'resource': "DataPlatform",
            'expected_strategy': 'bulk_list',
            'description': "Elenco completo tabelle"
        },
        {
            'query': "mostrami le colonne di DWHEVO",
            'resource': "DWHEVO",
            'expected_strategy': 'bulk_list',
            'description': "Elenco completo colonne"
        },
        
        # Dovrebbero usare SEARCH (ricerca pattern)
        {
            'query': "tabelle con GARANZIE nel nome",
            'resource': "DataPlatform",  # ⭐ AGGIUNTO
            'expected_strategy': 'pattern_search',
            'description': "Ricerca per pattern nel nome"
        },
        {
            'query': "trova asset che contengono CUSTOMER",
            'resource': "DataPlatform",  # ⭐ AGGIUNTO
            'expected_strategy': 'pattern_search',
            'description': "Ricerca keyword CUSTOMER"
        },
        {
            'query': "cerca tabelle con IFR nel nome",
            'resource': "DWHEVO",  # ⭐ AGGIUNTO
            'expected_strategy': 'pattern_search',
            'description': "Ricerca tabelle IFR in DWHEVO"
        },
    ]
    
    async with EDCClient() as client:
        
        for i, test in enumerate(test_queries, 1):
            print(f"\n{'=' * 70}")
            print(f"Test {i}: {test['description']}")
            print(f"{'=' * 70}")
            print(f"Query: '{test['query']}'")
            print(f"Resource: {test['resource'] or 'Auto-detect'}")
            print(f"Expected Strategy: {test['expected_strategy']}")
            print("-" * 70)
            
            try:
                result = await client.smart_search(
                    query=test['query'],
                    resource_name=test['resource'],
                    max_results=10
                )
                
                strategy = result['metadata']['search_strategy']
                api_used = result['metadata']['api_used']
                items = result['items']
                
                print(f"\n📊 Risultato:")
                print(f"   Strategy: {strategy}")
                print(f"   API Used: {api_used}")
                print(f"   Items Found: {len(items)}")
                
                # Verifica strategia
                if strategy == test['expected_strategy']:
                    print(f"   ✅ Strategia corretta!")
                else:
                    print(f"   ⚠️  Strategia diversa da attesa")
                
                # Mostra primi risultati
                if items:
                    print(f"\n   📋 Primi 3 risultati:")
                    for j, item in enumerate(items[:3], 1):
                        name = item.get('name', 'N/A')
                        ct = item.get('classType', 'N/A').split('.')[-1]
                        print(f"      {j}. {name} ({ct})")
                else:
                    print(f"\n   ℹ️  Nessun risultato trovato")
                
            except Exception as e:
                print(f"\n   ❌ Errore: {e}")
                import traceback
                traceback.print_exc()
            
            # Pausa tra test
            await asyncio.sleep(0.5)


async def test_interactive():
    """Test interattivo per provare query personalizzate."""
    
    print("\n" + "=" * 70)
    print("🎮 TEST INTERATTIVO - RICERCA INTELLIGENTE")
    print("=" * 70)
    print("\nProva la ricerca intelligente con le tue query!")
    print("\nEsempi:")
    print("  - 'tutte le tabelle di DataPlatform'")
    print("  - 'trova tabelle con GARANZIE nel nome'")
    print("  - 'mostrami le colonne di DWHEVO'")
    print("  - 'cerca asset che contengono CUSTOMER'")
    print("\nScrivi 'quit' per uscire\n")
    
    async with EDCClient() as client:
        
        while True:
            try:
                query = input("Query → ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Ciao!")
                    break
                
                if not query:
                    continue
                
                print(f"\n🔍 Elaborazione query...")
                
                result = await client.smart_search(
                    query=query,
                    max_results=10
                )
                
                strategy = result['metadata']['search_strategy']
                api_used = result['metadata']['api_used']
                items = result['items']
                
                print(f"\n📊 Risultato:")
                print(f"   Strategy: {strategy}")
                print(f"   API: {api_used}")
                print(f"   Trovati: {len(items)} item")
                
                if items:
                    print(f"\n📋 Risultati:")
                    for i, item in enumerate(items[:5], 1):
                        name = item.get('name', 'N/A')
                        ct = item.get('classType', 'N/A').split('.')[-1]
                        print(f"   {i}. {name} ({ct})")
                    
                    if len(items) > 5:
                        print(f"   ... e altri {len(items) - 5} item")
                else:
                    print(f"\n   ℹ️  Nessun risultato trovato")
                
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Ciao!")
                break
            except Exception as e:
                print(f"❌ Errore: {e}")


async def test_comparison():
    """Confronta bulk vs search per stessa query."""
    
    print("\n" + "=" * 70)
    print("⚖️  TEST CONFRONTO: BULK vs SEARCH")
    print("=" * 70)
    
    async with EDCClient() as client:
        
        # Test 1: Con smart_search (automatico)
        print("\n1️⃣  Smart Search (automatico)")
        print("-" * 70)
        
        result_smart = await client.smart_search(
            query="tabelle con GARANZIE nel nome",
            max_results=10
        )
        
        print(f"Strategy: {result_smart['metadata']['search_strategy']}")
        print(f"API: {result_smart['metadata']['api_used']}")
        print(f"Trovati: {len(result_smart['items'])} item")
        
        # Test 2: Forzando search
        print("\n2️⃣  Search API (forzato)")
        print("-" * 70)
        
        items_search = await client.search_assets("*GARANZIE*", {})
        print(f"Trovati: {len(items_search)} item")
        
        # Test 3: Forzando bulk
        print("\n3️⃣  Bulk API (forzato - tutte le tabelle)")
        print("-" * 70)
        
        result_bulk = await client.get_resources_bulk(
            resource_name="DataPlatform",
            class_types=["com.infa.ldm.relational.Table"],
            page_size=100
        )
        print(f"Trovate: {len(result_bulk['items'])} tabelle totali")
        
        # Filtra manualmente per GARANZIE
        filtered = [
            item for item in result_bulk['items']
            if 'GARANZIE' in item.get('name', '').upper()
        ]
        print(f"Con GARANZIE nel nome: {len(filtered)} tabelle")
        
        # Confronto
        print("\n📊 CONFRONTO:")
        print(f"   Smart (auto):  {len(result_smart['items'])} item")
        print(f"   Search (API):  {len(items_search)} item")
        print(f"   Bulk filtered: {len(filtered)} item")


async def main():
    """Menu principale."""
    
    print("\n" + "=" * 70)
    print("🧠 TEST SUITE - RICERCA INTELLIGENTE")
    print("=" * 70)
    print("\nScegli quale test eseguire:")
    print("1. Test automatici con query predefinite")
    print("2. Test interattivo (prova le tue query)")
    print("3. Confronto bulk vs search")
    print("4. Esegui tutti i test")
    print("0. Esci")
    
    choice = input("\nScelta [0-4]: ").strip()
    
    if choice == "0":
        print("👋 Uscita...")
        return
    elif choice == "1":
        await test_smart_search()
    elif choice == "2":
        await test_interactive()
    elif choice == "3":
        await test_comparison()
    elif choice == "4":
        print("\n🚀 Esecuzione di tutti i test...\n")
        await test_smart_search()
        print("\n" + "=" * 70)
        input("Premi ENTER per test confronto...")
        await test_comparison()
        print("\n✅ Tutti i test completati!")
    else:
        print("❌ Scelta non valida")
        return
    
    print("\n" + "=" * 70)
    print("✅ Test completato!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())