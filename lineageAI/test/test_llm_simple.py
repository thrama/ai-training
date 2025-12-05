# test_llm_simple.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
import os
import argparse
from dotenv import load_dotenv
from src.llm.factory import LLMFactory, LLMConfig, LLMProvider

# Carica variabili da .env
load_dotenv()

async def test_tinyllama():
    """Test TinyLlama."""
    print("\n" + "="*60)
    print("🤖 Testing TinyLlama")
    print("="*60)
    
    tinyllama_config = LLMConfig(
        provider=LLMProvider.TINYLLAMA,
        model_name="tinyllama",
        base_url="http://192.168.1.17:11434",
        max_tokens=2000,
        temperature=0.1
    )
    
    try:
        client = LLMFactory.create_llm_client(tinyllama_config)
        print(f"✅ Client created: {type(client).__name__}")
        
        print("⏳ Testing connection to Ollama...")
        result = await client.enhance_description(
            asset_name="CUSTOMER_TABLE",
            technical_desc="Table containing customer information",
            schema_context="banking",
            column_info=[]
        )
        
        if "Error" in result:
            print(f"❌ Connection failed: {result}")
            return False
        else:
            print(f"✅ Connection OK!")
            print(f"\n📝 Response:")
            print("-" * 60)
            print(result)
            print("-" * 60)
            await client.close()
            return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_claude():
    """Test Claude."""
    print("\n" + "="*60)
    print("🧠 Testing Claude")
    print("="*60)
    
    claude_key = os.getenv('CLAUDE_API_KEY')
    
    if not claude_key or not claude_key.startswith('sk-ant-'):
        print("❌ CLAUDE_API_KEY not found or invalid in .env file")
        return False
    
    print(f"✅ Found API key: {claude_key[:20]}...")
    
    claude_config = LLMConfig(
        provider=LLMProvider.CLAUDE,
        model_name="claude-3-5-sonnet-20241022",
        api_key=claude_key,
        max_tokens=1000,
        temperature=0.1
    )
    
    try:
        client = LLMFactory.create_llm_client(claude_config)
        print(f"✅ Client created: {type(client).__name__}")
        
        print("⏳ Testing Claude API call...")
        result = await client.enhance_description(
            asset_name="CUSTOMER_TABLE",
            technical_desc="Table containing customer information",
            schema_context="banking",
            column_info=[]
        )
        
        if "Error" in result:
            print(f"❌ API call failed: {result}")
            return False
        else:
            print(f"✅ API call OK!")
            print(f"\n📝 Response:")
            print("-" * 60)
            print(result)
            print("-" * 60)
            return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Main test function."""
    
    parser = argparse.ArgumentParser(
        description='Test LLM providers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi d'uso:
  python test_llm_simple.py                    # Menu interattivo
  python test_llm_simple.py --tinyllama        # Solo TinyLlama
  python test_llm_simple.py --claude           # Solo Claude
  python test_llm_simple.py --both             # Entrambi
        """
    )
    
    parser.add_argument('--tinyllama', action='store_true', 
                       help='Test solo TinyLlama')
    parser.add_argument('--claude', action='store_true', 
                       help='Test solo Claude')
    parser.add_argument('--both', action='store_true', 
                       help='Test entrambi i provider')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🧪 LLM Provider Test Suite")
    print("="*60)
    
    results = {}
    
    # Se nessun argomento, mostra menu interattivo
    if not (args.tinyllama or args.claude or args.both):
        print("\nScegli quale provider testare:")
        print("1. TinyLlama (Ollama)")
        print("2. Claude (Anthropic API)")
        print("3. Entrambi")
        print("0. Esci")
        
        choice = input("\nScelta [1-3, 0 per uscire]: ").strip()
        
        if choice == "0":
            print("👋 Uscita...")
            return
        elif choice == "1":
            args.tinyllama = True
        elif choice == "2":
            args.claude = True
        elif choice == "3":
            args.both = True
        else:
            print("❌ Scelta non valida!")
            return
    
    # Esegui i test
    if args.both or args.tinyllama:
        results['tinyllama'] = await test_tinyllama()
    
    if args.both or args.claude:
        results['claude'] = await test_claude()
    
    # Summary
    if results:
        print("\n" + "="*60)
        print("📊 Test Summary")
        print("="*60)
        for provider, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{provider.upper():15} {status}")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(main())