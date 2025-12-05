"""
Test per ispezionare la risposta raw dell'API bulk EDC.
Scopriamo cosa sta davvero ritornando il server.
"""
import asyncio
import aiohttp
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import settings


async def inspect_api_response():
    """Ispeziona la risposta raw dell'API bulk."""
    
    print("="*80)
    print("ISPEZIONE RISPOSTA API BULK EDC")
    print("="*80)
    
    # URL e parametri
    bulk_url = f"{settings.edc_base_url}/1/catalog/data/bulk"
    
    params = {
        'resourceName': 'DataPlatform',
        'classTypes': 'com.infa.ldm.relational.Table',
        'facts': 'id,core.name,core.classType',
        'includeRefObjects': 'true'
    }
    
    print(f"\n[Request]")
    print(f"URL: {bulk_url}")
    print(f"Method: POST")
    print(f"\nParameters:")
    for k, v in params.items():
        print(f"  {k}: {v}")
    
    # Headers
    headers = {
        'Authorization': settings.edc_authorization_header,
        'Accept': 'application/json',
        'Connection': 'keep-alive'
    }
    
    print(f"\nHeaders:")
    for k, v in headers.items():
        if k == 'Authorization':
            print(f"  {k}: {v[:20]}...")
        else:
            print(f"  {k}: {v}")
    
    # Chiamata
    timeout = aiohttp.ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(ssl=False)
    
    async with aiohttp.ClientSession(
        headers=headers,
        timeout=timeout,
        connector=connector
    ) as session:
        
        print(f"\n[Sending Request]...")
        print(f"Method: GET (not POST!)")
        
        # ⭐ CRITICAL: Usa GET come fa Postman!
        async with session.get(bulk_url, params=params) as response:
            
            print(f"\n[Response]")
            print(f"Status: {response.status}")
            print(f"Reason: {response.reason}")
            
            print(f"\n[Response Headers]:")
            for k, v in response.headers.items():
                print(f"  {k}: {v}")
            
            content_type = response.headers.get('Content-Type', 'N/A')
            content_encoding = response.headers.get('Content-Encoding', 'N/A')
            content_length = response.headers.get('Content-Length', 'N/A')
            
            print(f"\n[Content Info]")
            print(f"Content-Type: {content_type}")
            print(f"Content-Encoding: {content_encoding}")
            print(f"Content-Length: {content_length}")
            
            # Leggi i bytes raw
            print(f"\n[Reading Raw Bytes]...")
            raw_bytes = await response.read()
            
            print(f"Bytes ricevuti: {len(raw_bytes)}")
            print(f"Primi 100 bytes (hex): {raw_bytes[:100].hex()}")
            print(f"Primi 100 bytes (repr): {repr(raw_bytes[:100])}")
            
            # Prova a decodificare come testo
            print(f"\n[Tentativo Decodifica UTF-8]...")
            try:
                text = raw_bytes.decode('utf-8')
                print(f"SUCCESS - Lunghezza testo: {len(text)} caratteri")
                print(f"\nPrimi 1000 caratteri:")
                print("-"*80)
                print(text[:1000])
                print("-"*80)
                
                # Verifica se è CSV
                print(f"\n[Analisi Formato]...")
                first_line = text.split('\n')[0] if '\n' in text else text[:100]
                print(f"Prima riga: {first_line}")
                
                if ',' in first_line or '\t' in first_line:
                    print("✅ Sembra CSV (contiene virgole o tab)")
                    
                    # Prova parsing CSV
                    print(f"\n[Tentativo Parsing CSV]...")
                    import csv
                    from io import StringIO
                    
                    csv_reader = csv.DictReader(StringIO(text))
                    items = list(csv_reader)
                    
                    print(f"SUCCESS - CSV valido!")
                    print(f"Righe parsate: {len(items)}")
                    
                    if items:
                        print(f"\nColonne CSV:")
                        for i, col in enumerate(items[0].keys(), 1):
                            print(f"  {i}. {col}")
                        
                        print(f"\nPrima riga di dati:")
                        import json
                        print(json.dumps(items[0], indent=2, ensure_ascii=False))
                    
                    return {'format': 'csv', 'items': items}
                
                # Prova parsing JSON
                print(f"\n[Tentativo Parsing JSON]...")
                import json
                try:
                    data = json.loads(text)
                    print(f"SUCCESS - JSON valido!")
                    print(f"Chiavi root: {list(data.keys())}")
                    
                    if 'items' in data:
                        items = data['items']
                        print(f"Items trovati: {len(items)}")
                        
                        if items:
                            print(f"\nPrimo item:")
                            print(json.dumps(items[0], indent=2, ensure_ascii=False)[:500])
                    
                    return {'format': 'json', 'data': data}
                    
                except json.JSONDecodeError as je:
                    print(f"FAIL - JSON non valido: {je}")
                    print(f"\nTesto che ha causato errore:")
                    print(text[:1000])
                    
            except UnicodeDecodeError as e:
                print(f"FAIL - Non è UTF-8: {e}")
                
                # Prova gzip decompress
                print(f"\n[Tentativo Decompressione GZIP]...")
                import gzip
                try:
                    decompressed = gzip.decompress(raw_bytes)
                    print(f"SUCCESS - Decompresso: {len(decompressed)} bytes")
                    
                    text = decompressed.decode('utf-8')
                    print(f"\nPrimi 500 caratteri dopo decompressione:")
                    print("-"*80)
                    print(text[:500])
                    print("-"*80)
                    
                    # Prova parsing JSON
                    import json
                    data = json.loads(text)
                    print(f"\nJSON valido dopo decompressione!")
                    print(f"Chiavi: {list(data.keys())}")
                    
                    return data
                    
                except Exception as ge:
                    print(f"FAIL - Non è GZIP: {ge}")
            
            # Se arriviamo qui, niente ha funzionato
            print(f"\n[Diagnostic Summary]")
            print(f"❌ Non è JSON diretto")
            print(f"❌ Non è UTF-8 decodificabile")
            print(f"❌ Non è GZIP compresso")
            
            print(f"\n[Magic Bytes Analysis]")
            magic = raw_bytes[:4]
            print(f"Primi 4 bytes: {magic.hex()}")
            
            if magic[:2] == b'\x1f\x8b':
                print("  → Sembra GZIP (1f 8b)")
            elif magic[:2] == b'PK':
                print("  → Sembra ZIP (50 4b)")
            elif magic == b'\x00\x00\x00\x00':
                print("  → Tutti zero - risposta vuota?")
            else:
                print(f"  → Formato sconosciuto")
            
            return None


async def main():
    """Entry point."""
    try:
        result = await inspect_api_response()
        
        print("\n" + "="*80)
        if result:
            print("✅ SUCCESSO - API ritorna dati validi")
        else:
            print("❌ FALLITO - API non ritorna JSON valido")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())