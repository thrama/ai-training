"""
Client EDC per integrazione con API Informatica EDC.
Versione aggiornata per Allitude EDC con gestione robusta delle risposte API.
"""
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
import logging
import urllib3

from src.config.settings import settings

# Disabilita warning SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class EDCClient:
    """
    Client asincrono per API EDC.
    Gestisce chiamate API, caching, e parsing delle risposte per Allitude EDC.
    """
    
    def __init__(self):
        """Inizializza il client EDC usando settings centralizzato."""
        self.session: Optional[aiohttp.ClientSession] = None
        self._setup_from_settings()
        self._setup_logging()
        
        # Cache e statistiche
        self._cache = {}
        self._stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'api_errors': 0,
            'empty_responses': 0,
            'invalid_links': 0,
            'synonyms_filtered': 0
        }

    def _setup_from_settings(self) -> None:
        """Carica configurazione da settings centralizzato."""
        self.base_url = settings.edc_browse_url
        self.headers = settings.get_edc_headers()
        self.static_params = settings.get_edc_static_params()
        self.request_timeout = settings.edc_request_timeout
        self.max_retries = settings.edc_max_retries
        
        logging.info(f"EDC Client configurato: {settings.edc_base_url}")

    def _setup_logging(self) -> None:
        """Setup logging per il client EDC."""
        self.logger = logging.getLogger('edc_client')
        self.logger.setLevel(getattr(logging, settings.log_level))

    async def _ensure_session(self) -> None:
        """Assicura che la sessione HTTP sia inizializzata."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.request_timeout)
            connector = aiohttp.TCPConnector(
                ssl=False,  # Per self-signed certificates
                limit=20,
                limit_per_host=10
            )
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout,
                connector=connector
            )

    def _extract_name_from_item(self, item: dict, asset_id: str) -> str:
        """
        Estrae il nome dell'asset da vari possibili campi.
        Fallback: usa l'ultimo segmento dell'ID.
        """
        # Prova vari campi possibili
        name = (
            item.get('name') or
            item.get('core.name') or
            item.get('displayName') or
            item.get('label') or
            None
        )
        
        # Se non trovato, usa ultimo segmento dell'ID
        if not name and asset_id:
            if '/' in asset_id:
                name = asset_id.split('/')[-1]
            else:
                name = asset_id
        
        return name or 'Unknown'

    def _extract_classtype_from_item(self, item: dict) -> str:
        """
        Estrae il classType dell'asset da vari possibili campi.
        """
        class_type = (
            item.get('classType') or
            item.get('core.classType') or
            item.get('type') or
            'Unknown'
        )
        
        return class_type

    def _extract_description_from_facts(self, item: dict) -> str:
        """
        Estrae la descrizione dai facts dell'item API.
        Replica la logica del TreeBuilder con gestione robusta.
        """
        facts = item.get('facts', [])
        if not facts:
            return ""
        
        # Priorità delle descrizioni
        governed_axon_description = ""
        business_description = ""
        core_description = ""
        technical_description = ""
        
        for fact in facts:
            attribute_id = fact.get('attributeId', '')
            value = fact.get('value', '')
            
            if attribute_id == "com.infa.ldm.axon.governedAxonDescription":
                governed_axon_description = value
            elif attribute_id == "com.infa.ldm.ootb.enrichments.businessDescription":
                business_description = value
            elif attribute_id == "core.description":
                core_description = value
            elif attribute_id == "technicalDescription":
                technical_description = value
        
        # Ritorna la prima disponibile in ordine di priorità
        return (
            governed_axon_description or 
            business_description or 
            core_description or 
            technical_description
        )

    def _process_src_links(self, src_links: List[Dict]) -> List[Dict]:
        """
        Processa i src_links filtrando sinonimi e link invalidi.
        Mantiene la logica del TreeBuilder.
        """
        valid_links = []
        
        for link in src_links:
            link_id = link.get('id')
            association = link.get('association')
            
            if not link_id:
                self._stats['invalid_links'] += 1
                continue
            
            # Filtra sinonimi
            if association == "core.SynonymDataElementDataFlow":
                self._stats['synonyms_filtered'] += 1
                continue
            
            # Estrai nome dal link
            link_name = self._extract_name_from_item(link, link_id)
            
            # Aggiungi link valido
            valid_links.append({
                'id': link_id,
                'association': association,
                'name': link_name,
                'classType': link.get('classType', 'Unknown'),
                'href': link.get('href', '')
            })
        
        return valid_links

    async def get_asset_details(self, asset_id: str) -> Dict[str, Any]:
        """
        Recupera i dettagli completi di un asset.
        Versione robusta per Allitude EDC con gestione di risposte incomplete.
        
        Args:
            asset_id: ID dell'asset da recuperare
            
        Returns:
            Dict con metadati asset, src_links, descrizione, etc.
        """
        await self._ensure_session()
        
        # Controllo cache
        if asset_id in self._cache:
            self._stats['cache_hits'] += 1
            self.logger.info(f"Cache hit for asset: {asset_id}")
            return self._cache[asset_id]

        self._stats['total_requests'] += 1
        
        # Costruisci parametri query
        params = dict(self.static_params)
        params['q'] = f'id:{asset_id}'
        
        # Log per debug
        self.logger.info(f"Fetching asset: {asset_id}")
        self.logger.debug(f"Query params: {params}")
        
        try:
            async with self.session.get(
                self.base_url,
                params=params
            ) as response:
                
                # Log status
                self.logger.info(f"Response status: {response.status}")
                
                # Gestisci errori HTTP
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"API error {response.status}: {error_text[:200]}")
                
                response.raise_for_status()
                data = await response.json()
                
                # Log risposta per debug
                self.logger.debug(f"API Response keys: {list(data.keys())}")
                
                items = data.get('items', [])
                
                if not items:
                    # Nessun risultato - crea oggetto vuoto con fallback
                    self._stats['empty_responses'] += 1
                    self.logger.warning(f"Empty response for asset: {asset_id}")
                    
                    name_from_id = asset_id.split('/')[-1] if '/' in asset_id else asset_id
                    
                    result = {
                        'asset_id': asset_id,
                        'metadata': {},
                        'src_links': [],
                        'dst_links': [],
                        'description': '',
                        'name': name_from_id,
                        'classType': 'Unknown',
                        'facts': []
                    }
                else:
                    # Processa primo item
                    item = items[0]
                    
                    # Estrai campi con metodi robusti
                    name = self._extract_name_from_item(item, asset_id)
                    class_type = self._extract_classtype_from_item(item)
                    description = self._extract_description_from_facts(item)
                    
                    # Processa links (sia src che dst se disponibili)
                    src_links = self._process_src_links(item.get('srcLinks', []))
                    dst_links = self._process_src_links(item.get('dstLinks', []))
                    
                    result = {
                        'asset_id': asset_id,
                        'metadata': item,
                        'src_links': src_links,
                        'dst_links': dst_links,
                        'description': description,
                        'facts': item.get('facts', []),
                        'name': name,
                        'classType': class_type
                    }
                    
                    # Log info estratte
                    self.logger.info(
                        f"Asset found: {name} ({class_type}) - "
                        f"{len(src_links)} src, {len(dst_links)} dst"
                    )
                
                # Cache del risultato
                self._cache[asset_id] = result
                return result
                
        except aiohttp.ClientResponseError as e:
            self._stats['api_errors'] += 1
            self.logger.error(f"HTTP error fetching asset {asset_id}: {e.status} - {e.message}")
            raise
        except Exception as e:
            self._stats['api_errors'] += 1
            self.logger.error(f"Error fetching asset {asset_id}: {e}")
            raise

    async def search_assets(
        self, 
        query: str, 
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Cerca assets nel catalogo EDC.
        
        Args:
            query: Query di ricerca (es. "*", "*GARANZIE*", "name:CUSTOMER*")
            filters: Filtri aggiuntivi opzionali
            
        Returns:
            Lista di asset trovati
        """
        await self._ensure_session()
        
        params = dict(self.static_params)
        params['q'] = query
        
        if filters:
            params.update(filters)
        
        self.logger.info(f"Searching assets with query: {query}")
        
        try:
            async with self.session.get(
                self.base_url,
                params=params
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                items = data.get('items', [])
                
                # Arricchisci risultati con nomi estratti
                enriched_items = []
                for item in items:
                    asset_id = item.get('id', '')
                    
                    # Estrai nome
                    name = self._extract_name_from_item(item, asset_id)
                    class_type = self._extract_classtype_from_item(item)
                    
                    # Crea oggetto arricchito
                    enriched_item = {
                        **item,
                        'name': name,
                        'classType': class_type
                    }
                    enriched_items.append(enriched_item)
                
                self.logger.info(f"Found {len(enriched_items)} assets")
                return enriched_items
                
        except Exception as e:
            self.logger.error(f"Error searching assets with query '{query}': {e}")
            raise

    async def get_lineage_upstream(
        self, 
        asset_id: str, 
        depth: int = 1
    ) -> List[Dict]:
        """
        Recupera il lineage upstream di un asset.
        
        Args:
            asset_id: ID dell'asset
            depth: Profondità del lineage (per ora solo 1)
            
        Returns:
            Lista di asset upstream
        """
        asset_details = await self.get_asset_details(asset_id)
        return asset_details['src_links']

    async def get_lineage_downstream(
        self, 
        asset_id: str, 
        depth: int = 1
    ) -> List[Dict]:
        """
        Recupera il lineage downstream di un asset.
        
        Args:
            asset_id: ID dell'asset
            depth: Profondità del lineage (per ora solo 1)
            
        Returns:
            Lista di asset downstream
        """
        # Per downstream, potrebbe richiedere una chiamata separata
        # con includeDstLinks=true
        asset_details = await self.get_asset_details(asset_id)
        return asset_details['dst_links']

    def get_statistics(self) -> Dict[str, int]:
        """
        Restituisce le statistiche delle chiamate API.
        
        Returns:
            Dict con statistiche di utilizzo
        """
        return self._stats.copy()

    def clear_cache(self) -> None:
        """Svuota la cache degli asset."""
        self._cache.clear()
        self.logger.info("Cache cleared")

    async def close(self) -> None:
        """Chiude la sessione HTTP e rilascia risorse."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.info("EDC session closed")

    async def __aenter__(self):
        """Context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()