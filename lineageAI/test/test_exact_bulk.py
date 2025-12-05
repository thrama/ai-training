#!/usr/bin/env python3
"""
Test che replica esattamente la chiamata curl di esempio.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
import aiohttp
from dotenv import load_dotenv
from src.config.settings import settings

load_dotenv()


async def test_exact_curl():
    """Replica ESATTA del curl fornito."""
    print("=" * 70)
    print("🧪 TEST: Replica Esatta Curl Fornito")
    print("=" * 70)
    
    # URL e parametri ESATTI dal curl
    url = "https://edc.collaudo.servizi.allitude.it:9086/access/1/catalog/data/bulk"
    
    params = {
        'classTypes': 'com.infa.ldm.relational.Column,com.infa.ldm.relational.ViewColumn,com.infa.ldm.relational.Table,com.infa.ldm.relational.View',
        'facts': 'id,core.name,core.classType',
        'includeRefObjects': 'true',
        'resourceName': 'DataPlatform'
    }
    
    headers = {
        'Authorization': settings.edc_authorization_header,
        'Accept': 'application/json'
    }
    
    print(f"\n📍 URL: {url}")
    print(f"\n📋 Parametri:")
    for key, value in params.items():
        print(f"   {key}: {value[:80]}{'...' if len(value) > 80 else ''}")
    
    print(f"\n🔐 Authorization: {settings.edc_authorization_header[:30]}...")
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(ssl=False)
        
        async with aiohttp.ClientSession(
            headers=headers,
            timeout=timeout,
            connector=connector
        ) as session:
            
            print(f"\n📤 Invio richiesta POST...")
            
            async with session.post(
                url,
                params=params,
                data=''
            ) as response:
                
                print(f"\n📥 Response:")
                print(f"   Status: {response.status}")
                print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    items = data.get('items', [])
                    print(f"\n✅ SUCCESS!")
                    print(f"   Trovati {len(items)} item")
                    
                    if items:
                        print(f"\n📋 Primi 3 item:")
                        for i, item in enumerate(items[:3], 1):
                            name = item.get('name', 'N/A')
                            class_type = item.get('classType', 'N/A')
                            ct_short = class_type.split('.')[-1] if '.' in class_type else class_type
                            print(f"   {i}. {name} ({ct_short})")
                    
                    # Metadata
                    if 'metadata' in data or 'hasMore' in data:
                        print(f"\n📊 Metadata:")
                        print(f"   hasMore: {data.get('hasMore', 'N/A')}")
                        print(f"   offset: {data.get('offset', 'N/A')}")
                        print(f"   pageSize: {data.get('pageSize', 'N/A')}")
                    
                else:
                    error_text = await response.text()
                    print(f"\n❌ ERROR {response.status}")
                    print(f"\n📄 Response Body:")
                    print(error_text[:500])
                    
    except Exception as e:
        print(f"\n❌ Exception: {type(e).__name__}")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()


async def test_with_client():
    """Test usando il nostro EDCClient."""
    print("\n" + "=" * 70)
    print("🧪 TEST: Tramite EDCClient")
    print("=" * 70)
    
    from src.edc.client import EDCClient
    
    async with EDCClient() as client:
        
        print(f"\n📥 Chiamata get_resources_bulk...")
        
        try:
            result = await client.get_resources_bulk(
                resource_name="DataPlatform",
                class_types=[
                    "com.infa.ldm.relational.Column",
                    "com.infa.ldm.relational.ViewColumn",
                    "com.infa.ldm.relational.Table",
                    "com.infa.ldm.relational.View"
                ],
                facts=["id", "core.name", "core.classType"],
                include_ref_objects=True,
                page_size=100
            )
            
            items = result['items']
            print(f"\n✅ SUCCESS!")
            print(f"   Trovati {len(items)} item")
            
            if items:
                print(f"\n📋 Primi 3 item:")
                for i, item in enumerate(items[:3], 1):
                    print(f"   {i}. {item['name']} ({item['classType'].split('.')[-1]})")
            
            print(f"\n📊 Metadata:")
            print(f"   {result['metadata']}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Esegui entrambi i test."""
    
    print("\n🚀 TEST SUITE - API BULK EDC\n")
    
    # Test 1: Replica esatta curl
    await test_exact_curl()
    
    # Pausa
    print("\n" + "=" * 70)
    input("Premi ENTER per continuare con test EDCClient...")
    
    # Test 2: Tramite nostro client
    await test_with_client()
    
    print("\n" + "=" * 70)
    print("✅ Test completati!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())