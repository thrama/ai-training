#!/usr/bin/env python3
"""
Test della selezione intelligente dei classTypes basata su query naturali.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from dotenv import load_dotenv
from src.edc.client import EDCClient
from src.edc.class_types import ClassTypeSelector

load_dotenv()


async def test_inference_examples():
    """Test inferenza su query di esempio."""
    print("=" * 70)
    print("🧪 TEST INFERENZA INTELLIGENTE CLASSTYPES")
    print("=" * 70)
    
    # Query di test in linguaggio naturale
    test_queries = [
        ("Mostrami tutte le colonne di DataPlatform", "DataPlatform"),
        ("Quante tabelle ci sono in DWHEVO?", "DWHEVO"),
        ("Elenca le view del database ORAC51", "ORAC51"),
        ("Dammi tutte le colonne delle tabelle e delle viste", "DataPlatform"),
        ("Lista completa di tables and views in DWHEVO", "DWHEVO"),
        ("Cerca gli schemi disponibili", "DataPlatform"),
    ]
    
    async with EDCClient() as client:
        
        for i, (query, resource_name) in enumerate(test_queries, 1):
            print(f"\n{'=' * 70}")
            print(f"Test {i}: {query}")
            print(f"Resource: {resource_name}")
            print("-" * 70)
            
            # Test inferenza (senza chiamata API)
            inferred_types = ClassTypeSelector.infer_class_types(query)
            
            print(f"\n🤖 ClassTypes Inferiti:")
            for ct in inferred_types:
                desc = ClassTypeSelector.describe_class_type(ct)
                print(f"   • {desc}")
                print(f"     {ct}")
            
            # Test con chiamata API reale
            try:
                print(f"\n📥 Chiamata API con inferenza...")
                result = await client.get_resources_bulk(
                    resource_name=resource_name,
                    infer_from_query=query,
                    page_size=10  # Limita per test
                )
                
                items = result['items']
                
                print(f"✅ Trovati {len(items)} item")
                
                if items:
                    print(f"\n📋 Sample (primi 3):")
                    for j, item in enumerate(items[:3], 1):
                        ct_short = item['classType'].split('.')[-1]
                        print(f"   {j}. {item['name']} ({ct_short})")
                
            except Exception as e:
                print(f"⚠️  Errore API: {str(e)[:100]}")
            
            # Pausa tra test
            await asyncio.sleep(0.5)


async def test_natural_language_queries():
    """Test query naturali più complesse."""
    print("\n" + "=" * 70)
    print("🧪 TEST QUERY NATURALI AVANZATE")
    print("=" * 70)
    
    advanced_queries = [
        # Query in italiano
        "tutte le colonne",
        "solo tabelle",
        "tabelle e viste insieme",
        "colonne di vista",
        
        # Query in inglese
        "all columns",
        "tables only",
        "tables and views",
        "view columns",
        
        # Query miste
        "dammi le table",
        "show me columns",
        "lista views",
    ]
    
    print("\n🔍 Analisi Inferenza per Query Varie:\n")
    
    for query in advanced_queries:
        inferred = ClassTypeSelector.infer_class_types(query)
        
        print(f"Query: '{query}'")
        print(f"  → {len(inferred)} classType(s) inferiti")
        
        for ct in inferred:
            desc = ClassTypeSelector.describe_class_type(ct)
            print(f"    • {desc}")
        
        print()


async def test_comparison_explicit_vs_inferred():
    """Confronto tra specifica esplicita e inferenza."""
    print("\n" + "=" * 70)
    print("🧪 TEST CONFRONTO: ESPLICITO vs INFERENZA")
    print("=" * 70)
    
    resource_name = "DataPlatform"
    
    async with EDCClient() as client:
        
        # 1. Modo esplicito (vecchio)
        print("\n1️⃣  MODO ESPLICITO (classTypes specificati)")
        print("-" * 70)
        
        try:
            result_explicit = await client.get_resources_bulk(
                resource_name=resource_name,
                class_types=[
                    "com.infa.ldm.relational.Column",
                    "com.infa.ldm.relational.ViewColumn"
                ],
                page_size=10
            )
            
            print(f"✅ Trovati {len(result_explicit['items'])} item")
            print(f"   ClassTypes usati: Column, ViewColumn")
            
        except Exception as e:
            print(f"⚠️  Errore: {str(e)[:100]}")
        
        # 2. Modo con inferenza (nuovo)
        print("\n2️⃣  MODO INTELLIGENTE (inferenza da query)")
        print("-" * 70)
        
        try:
            result_inferred = await client.get_resources_bulk(
                resource_name=resource_name,
                infer_from_query="mostrami tutte le colonne",
                page_size=10
            )
            
            print(f"✅ Trovati {len(result_inferred['items'])} item")
            print(f"   Query: 'mostrami tutte le colonne'")
            
            if result_inferred.get('inferred_types'):
                print(f"   ClassTypes inferiti:")
                for ct in result_inferred['inferred_descriptions']:
                    print(f"     • {ct}")
        
        except Exception as e:
            print(f"⚠️  Errore: {str(e)[:100]}")
        
        # Confronto risultati
        print("\n📊 CONFRONTO:")
        print(f"   Esplicito: {len(result_explicit['items']) if 'result_explicit' in locals() else 0} item")
        print(f"   Inferito:  {len(result_inferred['items']) if 'result_inferred' in locals() else 0} item")


async def test_edge_cases():
    """Test casi limite e ambigui."""
    print("\n" + "=" * 70)
    print("🧪 TEST CASI LIMITE")
    print("=" * 70)
    
    edge_cases = [
        # Query ambigue
        ("dammi tutto", "Dovrebbe usare default (Column)"),
        ("", "Query vuota - default"),
        ("xyz123", "Query senza keyword - default"),
        
        # Query multiple keyword
        ("tabelle, viste e colonne", "Multiple keywords"),
        ("table or view", "Keyword OR"),
        
        # Query in altre lingue
        ("montrez-moi les tables", "Francese - non supportato, usa default"),
    ]
    
    print("\n🔍 Analisi Casi Limite:\n")
    
    for query, description in edge_cases:
        inferred = ClassTypeSelector.infer_class_types(query)
        
        print(f"Query: '{query}'")
        print(f"Descrizione: {description}")
        print(f"  → ClassTypes inferiti: {len(inferred)}")
        for ct in inferred:
            desc = ClassTypeSelector.describe_class_type(ct)
            print(f"    • {desc}")
        print()


async def demo_interactive():
    """Demo interattivo per testare inferenza."""
    print("\n" + "=" * 70)
    print("🎮 DEMO INTERATTIVO")
    print("=" * 70)
    print("\nProva l'inferenza con le tue query!")
    print("Esempi: 'mostra tabelle', 'tutte le colonne', 'view e table'")
    print("Scrivi 'quit' per uscire\n")
    
    async with EDCClient() as client:
        
        while True:
            try:
                query = input("Query → ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Ciao!")
                    break
                
                if not query:
                    continue
                
                # Mostra inferenza
                inferred = ClassTypeSelector.infer_class_types(query)
                
                print(f"\n🤖 Inferenza:")
                for ct in inferred:
                    desc = ClassTypeSelector.describe_class_type(ct)
                    print(f"   • {desc}")
                
                # Chiedi se fare chiamata API
                do_api = input("\nEseguire chiamata API? [y/N] ").strip().lower()
                
                if do_api == 'y':
                    resource = input("Resource name [DataPlatform]: ").strip() or "DataPlatform"
                    
                    print(f"\n📥 Chiamata API...")
                    result = await client.get_resources_bulk(
                        resource_name=resource,
                        infer_from_query=query,
                        page_size=5
                    )
                    
                    print(f"✅ Trovati {len(result['items'])} item")
                    
                    if result['items']:
                        print(f"\n📋 Sample:")
                        for i, item in enumerate(result['items'][:3], 1):
                            print(f"   {i}. {item['name']}")
                
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Ciao!")
                break
            except Exception as e:
                print(f"⚠️  Errore: {e}")


async def main():
    """Menu principale."""
    print("\n" + "=" * 70)
    print("🧪 TEST SUITE - INFERENZA INTELLIGENTE CLASSTYPES")
    print("=" * 70)
    print("\nScegli quale test eseguire:")
    print("1. Test inferenza su esempi predefiniti")
    print("2. Test query naturali avanzate")
    print("3. Confronto esplicito vs inferenza")
    print("4. Test casi limite")
    print("5. Demo interattivo")
    print("6. Esegui tutti i test")
    print("0. Esci")
    
    choice = input("\nScelta [0-6]: ").strip()
    
    if choice == "0":
        print("👋 Uscita...")
        return
    elif choice == "1":
        await test_inference_examples()
    elif choice == "2":
        await test_natural_language_queries()
    elif choice == "3":
        await test_comparison_explicit_vs_inferred()
    elif choice == "4":
        await test_edge_cases()
    elif choice == "5":
        await demo_interactive()
    elif choice == "6":
        print("\n🚀 Esecuzione di tutti i test...\n")
        await test_inference_examples()
        await test_natural_language_queries()
        await test_comparison_explicit_vs_inferred()
        await test_edge_cases()
        print("\n✅ Tutti i test completati!")
    else:
        print("❌ Scelta non valida")
        return
    
    print("\n" + "=" * 70)
    print("✅ Test completato!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())