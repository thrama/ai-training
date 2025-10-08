# search_dwhevo.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from src.edc.client import EDCClient

async def search():
    print("🔍 Ricerca asset in DWHEVO\n")
    
    async with EDCClient() as client:
        # Cerca nello schema
        results = await client.search_assets("core.resourceName:DWHEVO", {})
        
        print(f"Trovati {len(results)} asset\n")
        
        for i, asset in enumerate(results[:10], 1):
            print(f"{i}. {asset.get('name', 'N/A')}")
            print(f"   ID: {asset.get('id', 'N/A')}")
            print(f"   Type: {asset.get('classType', 'N/A')}")
            
            # Mostra se ha lineage
            src = len(asset.get('srcLinks', []))
            dst = len(asset.get('dstLinks', []))
            if src or dst:
                print(f"   📊 Lineage: {src} upstream, {dst} downstream")
            print()

asyncio.run(search())