"""
LineageBuilder - Wrapper moderno per TreeBuilder con integrazione LLM.
Mantiene compatibilità con logica TreeBuilder esistente.
"""
import asyncio
from typing import Dict, List, Optional, Any
import logging

from .client import EDCClient
from .models import TreeNode, LineageDirection


class LineageBuilder:
    """
    Builder per alberi di lineage EDC.
    Evoluzione del TreeBuilder originale con supporto asincrono.
    """
    
    def __init__(self):
        """Inizializza il LineageBuilder."""
        self.edc_client = EDCClient()
        self.logger = logging.getLogger('lineage_builder')
        
        # Statistiche (compatibilità TreeBuilder)
        self._stats = {
            'nodes_created': 0,
            'total_requests': 0,
            'cache_hits': 0,
            'cycles_prevented': 0,
            'self_references': 0,
            'field_cross_references_found': 0,
            'api_errors': 0,
            'deduplication_sessions': 0,
            'duplicate_children_removed': 0
        }
        
        # Cache nodi visitati per prevenire cicli
        self._visited_nodes = set()
        
    async def build_tree(
        self,
        node_id: str,
        code: str,
        depth: int = 0,
        max_depth: int = 100
    ) -> Optional[TreeNode]:
        """
        Costruisce albero lineage completo (logica TreeBuilder).
        
        Args:
            node_id: ID dell'asset radice
            code: Codice progressivo (es. "001")
            depth: Profondità corrente
            max_depth: Profondità massima
            
        Returns:
            TreeNode radice dell'albero o None
        """
        # Prevenzione cicli
        if node_id in self._visited_nodes:
            self._stats['cycles_prevented'] += 1
            self.logger.warning(f"Ciclo rilevato per {node_id}")
            return None
        
        if depth >= max_depth:
            self.logger.warning(f"Max depth {max_depth} raggiunta")
            return None
        
        try:
            # Recupera dettagli asset
            asset_details = await self.edc_client.get_asset_details(node_id)
            
            # Crea nodo
            node = TreeNode(
                id=node_id,
                code=code,
                name=asset_details.get('name', ''),
                description=asset_details.get('description', ''),
                class_type=asset_details.get('classType', ''),
                facts=asset_details.get('facts', [])
            )
            
            self._stats['nodes_created'] += 1
            self._visited_nodes.add(node_id)
            
            # Processa src_links (upstream)
            src_links = asset_details.get('src_links', [])
            
            for i, link in enumerate(src_links, 1):
                child_id = link['id']
                child_code = f"{code}{i:03d}"
                
                # Ricorsione
                child_node = await self.build_tree(
                    child_id,
                    child_code,
                    depth + 1,
                    max_depth
                )
                
                if child_node:
                    node.add_child(child_node)
            
            self.logger.info(
                f"Nodo {node_id} creato - "
                f"depth={depth}, children={len(node.children)}"
            )
            
            return node
            
        except Exception as e:
            self._stats['api_errors'] += 1
            self.logger.error(f"Errore costruzione nodo {node_id}: {e}")
            return None
    
    async def get_asset_metadata(self, asset_id: str) -> Dict[str, Any]:
        """
        Recupera metadati di un asset.
        
        Args:
            asset_id: ID dell'asset
            
        Returns:
            Dict con metadati
        """
        details = await self.edc_client.get_asset_details(asset_id)
        
        return {
            'asset_id': asset_id,
            'name': details.get('name', ''),
            'classType': details.get('classType', ''),
            'description': details.get('description', ''),
            'facts': details.get('facts', []),
            'src_links': details.get('src_links', []),
            'dst_links': details.get('dst_links', [])
        }
    
    async def get_immediate_lineage(
        self,
        asset_id: str,
        direction: str = "upstream"
    ) -> List[Dict[str, Any]]:
        """
        Recupera lineage immediato (1 livello).
        
        Args:
            asset_id: ID dell'asset
            direction: "upstream", "downstream", "both"
            
        Returns:
            Lista di link immediati
        """
        details = await self.edc_client.get_asset_details(asset_id)
        
        results = []
        
        if direction in ["upstream", "both"]:
            for link in details.get('src_links', []):
                results.append({
                    'asset_id': link['id'],
                    'name': link['name'],
                    'classType': link['classType'],
                    'association': link['association'],
                    'direction': 'upstream'
                })
        
        if direction in ["downstream", "both"]:
            for link in details.get('dst_links', []):
                results.append({
                    'asset_id': link['id'],
                    'name': link['name'],
                    'classType': link['classType'],
                    'association': link['association'],
                    'direction': 'downstream'
                })
        
        return results
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Restituisce statistiche di costruzione.
        
        Returns:
            Dict con statistiche
        """
        # Combina statistiche builder + client
        client_stats = self.edc_client.get_statistics()
        
        combined_stats = {**self._stats}
        combined_stats['total_requests'] = client_stats['total_requests']
        combined_stats['cache_hits'] = client_stats['cache_hits']
        
        return combined_stats
    
    def clear_cache(self) -> None:
        """Pulisce cache e nodi visitati."""
        self._visited_nodes.clear()
        self.edc_client.clear_cache()
        self.logger.info("Cache cleared")
    
    async def close(self) -> None:
        """Chiude risorse."""
        await self.edc_client.close()
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.edc_client._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()