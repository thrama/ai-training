"""
Test completo integrazione MCP Server.
Testa tutti i tool MCP disponibili accedendo direttamente ai metodi.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.mcp.server import EDCMCPServer
from src.config.settings import settings, LLMProvider


async def test_mcp_tools():
    """Test tutti i tools MCP disponibili."""
    
    print("="*70)
    print("🧪 TEST MCP SERVER INTEGRATION")
    print("="*70)
    print(f"Environment: {settings.environment.value}")
    print(f"EDC URL: {settings.edc_base_url}")
    print(f"LLM Provider: {settings.default_llm_provider.value}")
    print("="*70)
    
    server = EDCMCPServer()
    
    # Inizializza LineageBuilder subito
    from src.edc.lineage import LineageBuilder
    server.lineage_builder = LineageBuilder()
    print("\n✅ LineageBuilder inizializzato")
    
    # Asset di test
    test_asset = "DataPlatform://ORAC51/DWHEVO/IFR_WK_GARANZIE_SOFFERENZE_DT_AP"
    
    print(f"\n📋 Asset di Test: {test_asset}")
    print("-"*70)
    
    try:
        # ====================================
        # Test 1: LLM Status
        # ====================================
        print("\n" + "="*70)
        print("1️⃣  TEST: LLM Status")
        print("="*70)
        
        try:
            print(f"Provider attivo: {server.current_llm_provider.value}")
            print(f"LLM Client: {type(server.llm_client).__name__}")
            print(f"Model: {server.llm_client.model_name}")
            
            # Verifica disponibilità provider
            print(f"\n🔍 Disponibilità Provider:")
            print(f"   • TinyLlama: {'✅' if settings.is_ollama_available() else '❌'}")
            print(f"   • Claude: {'✅' if settings.is_claude_available() else '❌'}")
            
        except Exception as e:
            print(f"⚠️  Errore: {e}")
        
        # ====================================
        # Test 2: Search Assets
        # ====================================
        print("\n" + "="*70)
        print("2️⃣  TEST: Search Assets")
        print("="*70)
        print("Query: *GARANZIE*")
        print("-"*70)

        try:
            results = await server.lineage_builder.edc_client.search_assets(
                "*GARANZIE*", {}
            )
            
            print(f"✅ Trovati {len(results)} asset")
            
            if results:
                print(f"\nPrimi 5 risultati:")
                for i, asset in enumerate(results[:5], 1):
                    print(f"   {i}. {asset.get('name', 'N/A')}")
                    print(f"      Type: {asset.get('classType', 'N/A')}")
                    print(f"      ID: {asset.get('id', 'N/A')[:80]}...")

        except Exception as e:
            print(f"⚠️  Errore: {e}")
            import traceback
            traceback.print_exc()
        
        # ====================================
        # Test 3: Asset Details
        # ====================================
        print("\n" + "="*70)
        print("3️⃣  TEST: Asset Details + AI Enhancement")
        print("="*70)
        print(f"Asset: {test_asset}")
        print("-"*70)
        
        try:
            # Recupera metadata
            metadata = await server.lineage_builder.get_asset_metadata(test_asset)
            
            print(f"✅ Asset trovato!")
            print(f"   Nome: {metadata['name']}")
            print(f"   Tipo: {metadata['classType']}")
            print(f"   Descrizione originale: {metadata['description'][:100] if metadata['description'] else 'N/A'}...")
            
            # AI Enhancement
            print(f"\n🤖 AI Enhancement...")
            enhanced = await server.llm_client.enhance_description(
                asset_name=metadata['name'],
                technical_desc=metadata['description'],
                schema_context="Banking - Data Warehouse",
                column_info=[]
            )
            
            print(f"✨ Descrizione arricchita:")
            print(f"   {enhanced}")
            
        except Exception as e:
            print(f"⚠️  Errore: {e}")
            import traceback
            traceback.print_exc()
        
        # ====================================
        # Test 4: Immediate Lineage
        # ====================================
        print("\n" + "="*70)
        print("4️⃣  TEST: Immediate Lineage")
        print("="*70)
        print(f"Asset: {test_asset}")
        print("Direction: upstream")
        print("-"*70)
        
        try:
            lineage = await server.lineage_builder.get_immediate_lineage(
                test_asset, "upstream"
            )
            
            print(f"✅ Trovati {len(lineage)} asset upstream")
            
            if lineage:
                print(f"\nPrime 5 dipendenze:")
                for i, link in enumerate(lineage[:5], 1):
                    print(f"   {i}. {link['name']}")
                    print(f"      Type: {link['classType']}")
                    print(f"      Association: {link['association']}")
            
        except Exception as e:
            print(f"⚠️  Errore: {e}")
            import traceback
            traceback.print_exc()
        
        # ====================================
        # Test 5: Lineage Tree
        # ====================================
        print("\n" + "="*70)
        print("5️⃣  TEST: Lineage Tree Construction")
        print("="*70)
        print(f"Asset: {test_asset}")
        print("Depth: 2 (limitato per performance)")
        print("-"*70)
        
        try:
            tree = await server.lineage_builder.build_tree(
                test_asset, "001", max_depth=2
            )
            
            if tree:
                stats = tree.get_statistics()
                print(f"✅ Albero costruito!")
                print(f"   • Nodi totali: {stats['total_nodes']}")
                print(f"   • Profondità max: {stats['max_depth']}")
                print(f"   • Nodi terminali: {stats['terminal_nodes']}")
                print(f"   • Figli diretti: {stats['direct_children']}")
                
                # Analisi complessità con LLM
                print(f"\n🤖 Analisi complessità AI...")
                lineage_data = {
                    'id': test_asset,
                    'code': '001',
                    'children_count': stats['total_nodes'],
                    'node_type': 'com.infa.ldm.relational.Table',
                    'is_terminal': False
                }
                
                complexity = await server.llm_client.analyze_lineage_complexity(
                    lineage_data
                )
                
                print(f"   • Complexity Score: {complexity['complexity_score']}/10")
                print(f"   • Risk Level: {complexity['risk_level']}")
                if complexity.get('risk_factors'):
                    print(f"   • Risk Factors: {len(complexity['risk_factors'])}")
                    for factor in complexity['risk_factors'][:3]:
                        print(f"     - {factor}")
            else:
                print("⚠️  Nessun albero costruito")
            
        except Exception as e:
            print(f"⚠️  Errore: {e}")
            import traceback
            traceback.print_exc()
        
        # ====================================
        # Test 6: Change Impact Analysis
        # ====================================
        print("\n" + "="*70)
        print("6️⃣  TEST: Change Impact Analysis")
        print("="*70)
        print(f"Asset: {test_asset}")
        print("Change Type: deprecation")
        print("-"*70)
        
        try:
            # Recupera lineage downstream
            downstream = await server.lineage_builder.get_immediate_lineage(
                test_asset, "downstream"
            )
            
            print(f"📊 Asset downstream impattati: {len(downstream)}")
            
            # Analisi impatto con LLM
            print(f"\n🤖 Analisi impatto AI...")
            impact = await server.llm_client.analyze_change_impact(
                source_asset=test_asset,
                change_type="deprecation",
                change_details={
                    "description": "Tabella deprecata per migrazione a nuovo modello dati"
                },
                affected_lineage={"downstream": downstream}
            )
            
            print(f"✅ Analisi completata:")
            print(f"   • Risk Level: {impact['risk_level']}")
            print(f"   • Business Impact: {impact['business_impact'][:200]}...")
            
            if impact.get('recommendations'):
                print(f"\n   💡 Top 3 Raccomandazioni:")
                for i, rec in enumerate(impact['recommendations'][:3], 1):
                    print(f"      {i}. {rec}")
            
        except Exception as e:
            print(f"⚠️  Errore: {e}")
            import traceback
            traceback.print_exc()
        
        # ====================================
        # Test 7: Generate Checklist
        # ====================================
        print("\n" + "="*70)
        print("7️⃣  TEST: Generate Change Checklist")
        print("="*70)
        
        try:
            # Usa risultato impact analysis precedente se disponibile
            if 'impact' in locals():
                checklist = await server.llm_client.generate_change_checklist(impact)
                
                print(f"✅ Checklist generata:")
                
                if checklist.get('governance_tasks'):
                    print(f"\n   📋 Governance Tasks:")
                    for task in checklist['governance_tasks'][:3]:
                        print(f"      • {task}")
                
                if checklist.get('pre_change_tasks'):
                    print(f"\n   🔧 Pre-Change Tasks:")
                    for task in checklist['pre_change_tasks'][:3]:
                        print(f"      • {task}")
                
                if checklist.get('validation_tasks'):
                    print(f"\n   ✅ Validation Tasks:")
                    for task in checklist['validation_tasks'][:3]:
                        print(f"      • {task}")
            else:
                print("⚠️  Skipped (impact analysis non disponibile)")
            
        except Exception as e:
            print(f"⚠️  Errore: {e}")
        
        # ====================================
        # Test 8: Documentation Enhancement
        # ====================================
        print("\n" + "="*70)
        print("8️⃣  TEST: Documentation Enhancement")
        print("="*70)
        
        try:
            # Usa metadata precedente se disponibile
            if 'metadata' in locals() and 'lineage' in locals():
                enhanced_docs = await server.llm_client.enhance_documentation(
                    asset_info=metadata,
                    lineage_context={"upstream": lineage},
                    business_context={"domain": "Banking - Risk Management"}
                )
                
                print(f"✅ Documentazione arricchita:")
                print(f"\n   📝 Enhanced Description:")
                print(f"      {enhanced_docs['enhanced_description'][:300]}...")
                
                print(f"\n   🎯 Business Purpose:")
                print(f"      {enhanced_docs['business_purpose']}")
                
                if enhanced_docs.get('suggested_tags'):
                    print(f"\n   🏷️  Suggested Tags:")
                    print(f"      {', '.join(enhanced_docs['suggested_tags'][:5])}")
            else:
                print("⚠️  Skipped (metadata non disponibile)")
            
        except Exception as e:
            print(f"⚠️  Errore: {e}")
        
        # ====================================
        # Test 9: System Statistics
        # ====================================
        print("\n" + "="*70)
        print("9️⃣  TEST: System Statistics")
        print("="*70)
        
        try:
            if server.lineage_builder:
                stats = server.lineage_builder.get_statistics()
                
                print(f"📊 Statistiche EDC:")
                print(f"   • Total API calls: {stats['total_requests']}")
                print(f"   • Cache hits: {stats['cache_hits']}")
                print(f"   • API errors: {stats['api_errors']}")
                print(f"   • Nodi creati: {stats['nodes_created']}")
                print(f"   • Cicli prevenuti: {stats['cycles_prevented']}")
                
                if stats['total_requests'] > 0:
                    cache_ratio = (stats['cache_hits'] / stats['total_requests']) * 100
                    print(f"   • Cache hit ratio: {cache_ratio:.1f}%")
            
        except Exception as e:
            print(f"⚠️  Errore: {e}")
        
        # ====================================
        # Riepilogo Finale
        # ====================================
        print("\n" + "="*70)
        print("✅ TUTTI I TEST COMPLETATI!")
        print("="*70)
        
    except Exception as e:
        print("\n" + "="*70)
        print(f"❌ ERRORE DURANTE I TEST: {e}")
        print("="*70)
        import traceback
        traceback.print_exc()
    finally:
        print("\n🧹 Cleanup risorse...")
        await server.cleanup()
        print("✅ Cleanup completato")


async def test_llm_switch():
    """Test cambio provider LLM a runtime."""
    
    print("\n" + "="*70)
    print("🔄 TEST SWITCH LLM PROVIDER")
    print("="*70)
    
    server = EDCMCPServer()
    
    try:
        # Status iniziale
        print("\n📍 Provider Iniziale:")
        print("-"*70)
        print(f"   Provider: {server.current_llm_provider.value}")
        print(f"   Client: {type(server.llm_client).__name__}")
        print(f"   Model: {server.llm_client.model_name}")
        
        # Verifica disponibilità
        claude_available = settings.is_claude_available()
        ollama_available = settings.is_ollama_available()
        
        print(f"\n🔍 Disponibilità Provider:")
        print(f"   • TinyLlama (Ollama): {'✅' if ollama_available else '❌'}")
        print(f"   • Claude API: {'✅' if claude_available else '❌'}")
        
        # Test switch se entrambi disponibili
        if claude_available and ollama_available:
            print("\n🔄 Tentativo Switch Provider...")
            print("-"*70)
            
            current = server.current_llm_provider
            new_provider = LLMProvider.CLAUDE if current == LLMProvider.TINYLLAMA else LLMProvider.TINYLLAMA
            
            print(f"   Da: {current.value}")
            print(f"   A: {new_provider.value}")
            
            # Esegui switch
            old_provider = server.current_llm_provider
            server.current_llm_provider = new_provider
            server._initialize_llm()
            
            print(f"\n✅ Switch completato!")
            print(f"   Nuovo provider: {server.current_llm_provider.value}")
            print(f"   Nuovo client: {type(server.llm_client).__name__}")
            
            # Test funzionalità
            print(f"\n🧪 Test funzionalità nuovo provider...")
            test_desc = await server.llm_client.enhance_description(
                asset_name="TEST_TABLE",
                technical_desc="Test table for validation",
                schema_context="test",
                column_info=[]
            )
            print(f"   ✅ Provider funzionante!")
            print(f"   Response: {test_desc[:100]}...")
            
        else:
            print("\n⚠️  Non tutti i provider disponibili per test switch")
            if not claude_available:
                print("   💡 Per abilitare Claude: configura CLAUDE_API_KEY in .env")
            if not ollama_available:
                print("   💡 Per abilitare TinyLlama: avvia Ollama")
        
        print("\n" + "="*70)
        print("✅ Test Switch Completato")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await server.cleanup()


async def test_performance():
    """Test performance con metriche dettagliate."""
    
    print("\n" + "="*70)
    print("⚡ TEST PERFORMANCE")
    print("="*70)
    
    import time
    
    server = EDCMCPServer()
    test_asset = "DataPlatform://ORAC51/DWHEVO/IFR_WK_GARANZIE_SOFFERENZE_DT_AP"
    
    try:
        from src.edc.lineage import LineageBuilder
        server.lineage_builder = LineageBuilder()
        
        # Test 1: Cache effectiveness
        print("\n1️⃣  Test Cache (2 chiamate stesso asset)")
        print("-"*70)
        
        start = time.time()
        metadata1 = await server.lineage_builder.get_asset_metadata(test_asset)
        first_call = time.time() - start
        print(f"   Prima chiamata: {first_call:.3f}s")
        
        start = time.time()
        metadata2 = await server.lineage_builder.get_asset_metadata(test_asset)
        second_call = time.time() - start
        print(f"   Seconda chiamata (cached): {second_call:.3f}s")
        
        if second_call > 0:
            speedup = first_call / second_call
            print(f"   ⚡ Speedup: {speedup:.1f}x")
        
        # Test 2: Lineage immediato
        print("\n2️⃣  Test Immediate Lineage")
        print("-"*70)
        
        start = time.time()
        lineage = await server.lineage_builder.get_immediate_lineage(test_asset, "upstream")
        duration = time.time() - start
        print(f"   Durata: {duration:.3f}s")
        print(f"   Asset trovati: {len(lineage)}")
        
        # Test 3: Lineage Tree
        print("\n3️⃣  Test Lineage Tree (depth=2)")
        print("-"*70)
        
        start = time.time()
        tree = await server.lineage_builder.build_tree(test_asset, "001", max_depth=2)
        duration = time.time() - start
        
        if tree:
            stats = tree.get_statistics()
            print(f"   Durata: {duration:.3f}s")
            print(f"   Nodi creati: {stats['total_nodes']}")
            print(f"   Nodes/sec: {stats['total_nodes']/duration:.1f}")
        
        # Statistiche finali
        print("\n📊 Statistiche Performance:")
        print("-"*70)
        stats = server.lineage_builder.get_statistics()
        print(f"   • Total API calls: {stats['total_requests']}")
        print(f"   • Cache hits: {stats['cache_hits']}")
        print(f"   • Nodi creati: {stats['nodes_created']}")
        
        if stats['total_requests'] > 0:
            cache_ratio = (stats['cache_hits'] / stats['total_requests']) * 100
            print(f"   • Cache hit ratio: {cache_ratio:.1f}%")
        
        print("\n✅ Test Performance Completato")
        
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await server.cleanup()


async def run_all_tests():
    """Esegue tutti i test in sequenza."""
    await test_mcp_tools()
    print("\n" + "="*70)
    input("Premi ENTER per continuare con test switch LLM...")
    await test_llm_switch()
    print("\n" + "="*70)
    input("Premi ENTER per continuare con test performance...")
    await test_performance()


def main():
    """Entry point con menu interattivo."""
    
    print("\n" + "="*70)
    print("🎯 TEST SUITE MCP SERVER")
    print("="*70)
    print("\nScegli quale test eseguire:")
    print("1. Test completo tutti i tools MCP")
    print("2. Test switch provider LLM")
    print("3. Test performance e caching")
    print("4. Esegui tutti i test")
    print("0. Esci")
    
    choice = input("\nScelta [0-4]: ").strip()
    
    if choice == "1":
        asyncio.run(test_mcp_tools())
    elif choice == "2":
        asyncio.run(test_llm_switch())
    elif choice == "3":
        asyncio.run(test_performance())
    elif choice == "4":
        asyncio.run(run_all_tests())
    elif choice == "0":
        print("👋 Uscita...")
    else:
        print("❌ Scelta non valida")


if __name__ == "__main__":
    main()