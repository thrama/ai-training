#!/usr/bin/env python3
"""
Verifica costruzione URL per API bulk.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from src.config.settings import settings

load_dotenv()

print("=" * 70)
print("🔍 VERIFICA COSTRUZIONE URL")
print("=" * 70)

print(f"\n📍 Settings EDC:")
print(f"   edc_base_url: {settings.edc_base_url}")
print(f"   edc_api_version: {settings.edc_api_version}")

print(f"\n📍 URL Standard (objects):")
print(f"   edc_browse_url: {settings.edc_browse_url}")

print(f"\n📍 URL Bulk (corretto):")
base = settings.edc_base_url.rstrip('/')
bulk_url = f"{base}/1/catalog/data/bulk"
print(f"   bulk_url: {bulk_url}")

print(f"\n✅ URL Atteso:")
print(f"   https://edc.collaudo.servizi.allitude.it:9086/access/1/catalog/data/bulk")

print(f"\n❓ Match: {bulk_url == 'https://edc.collaudo.servizi.allitude.it:9086/access/1/catalog/data/bulk'}")

# Test parametri
print(f"\n📋 Parametri Test:")
params = {
    'resourceName': 'DataPlatform',
    'classTypes': 'com.infa.ldm.relational.Column',
    'facts': 'id,core.name,core.classType',
    'includeRefObjects': 'true',
    'offset': '0',
    'pageSize': '10'
}

for key, value in params.items():
    print(f"   {key} = {value}")

# Simula query string
from urllib.parse import urlencode
query_string = urlencode(params)
full_url = f"{bulk_url}?{query_string}"

print(f"\n🌐 URL Completo (simulato):")
print(f"   {full_url}")

print(f"\n📏 Lunghezza URL: {len(full_url)} caratteri")