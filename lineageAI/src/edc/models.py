"""
Modelli dati per EDC Lineage.
Include TreeNode e altri dataclass per gestione lineage.
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class LineageDirection(str, Enum):
    """Direzione del lineage."""
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"
    BOTH = "both"


class TreeNode:
    """
    Nodo dell'albero di lineage.
    Compatibile con TreeBuilder originale.
    """
    
    def __init__(
        self,
        id: str,
        code: str,
        name: str = "",
        description: str = "",
        class_type: str = "",
        facts: List[Dict] = None
    ):
        """
        Inizializza un nodo.
        
        Args:
            id: ID univoco dell'asset
            code: Codice gerarchico (es. "001", "001001")
            name: Nome dell'asset
            description: Descrizione
            class_type: Tipo di asset
            facts: Facts EDC
        """
        self.id = id
        self.code = code
        self.name = name
        self.description = description
        self.class_type = class_type
        self.facts = facts or []
        self.children: List[TreeNode] = []
        self.metadata: Dict[str, Any] = {}
    
    def add_child(self, child: 'TreeNode') -> None:
        """Aggiunge un figlio al nodo."""
        if child not in self.children:
            self.children.append(child)
    
    def get_depth(self) -> int:
        """Calcola la profondità massima dell'albero."""
        if not self.children:
            return 1
        return 1 + max(child.get_depth() for child in self.children)
    
    def get_total_nodes(self) -> int:
        """Conta il numero totale di nodi."""
        return 1 + sum(child.get_total_nodes() for child in self.children)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Restituisce statistiche dell'albero.
        
        Returns:
            Dict con statistiche complete
        """
        return {
            'total_nodes': self.get_total_nodes(),
            'max_depth': self.get_depth(),
            'direct_children': len(self.children),
            'field_cross_references': self._count_field_xrefs(),
            'terminal_nodes': self._count_terminal_nodes()
        }
    
    def _count_field_xrefs(self) -> int:
        """Conta field cross-references nell'albero."""
        count = 0
        if 'field_xref' in self.metadata:
            count += 1
        for child in self.children:
            count += child._count_field_xrefs()
        return count
    
    def _count_terminal_nodes(self) -> int:
        """Conta nodi terminali (foglie)."""
        if not self.children:
            return 1
        return sum(child._count_terminal_nodes() for child in self.children)
    
    def is_terminal_node(self) -> bool:
        """Verifica se il nodo è terminale."""
        return len(self.children) == 0
    
    def get_node_type(self) -> str:
        """Restituisce il tipo del nodo."""
        return self.class_type or "Unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte il nodo in dizionario."""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'class_type': self.class_type,
            'children_count': len(self.children),
            'children': [child.to_dict() for child in self.children]
        }
    
    def __repr__(self) -> str:
        return f"TreeNode(id={self.id}, code={self.code}, children={len(self.children)})"


@dataclass
class ImpactAnalysisRequest:
    """Request per analisi di impatto."""
    source_asset: str
    change_type: str
    change_details: Dict[str, Any]
    max_depth: int = 5


@dataclass
class ImpactAnalysisResult:
    """Risultato analisi di impatto."""
    risk_level: str
    affected_assets: List[str]
    business_impact: str
    technical_impact: str
    recommendations: List[str]
    testing_strategy: List[str]


@dataclass
class EnhancementRequest:
    """Request per enhancement documentazione."""
    asset_id: str
    include_lineage: bool = True
    business_context: Optional[Dict[str, str]] = None


@dataclass
class EnhancementResult:
    """Risultato enhancement."""
    enhanced_description: str
    business_purpose: str
    suggested_tags: List[str]
    quality_rules: List[str]
    compliance_notes: str