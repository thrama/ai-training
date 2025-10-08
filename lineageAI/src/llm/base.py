"""
Classe base astratta per i client LLM.
Definisce l'interfaccia comune per tutti i provider LLM.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BaseLLMClient(ABC):
    """
    Classe base astratta per client LLM.
    Tutti i provider (TinyLlama, Claude, etc.) devono implementare questi metodi.
    """
    
    def __init__(self, config):
        """
        Inizializza il client LLM.
        
        Args:
            config: Configurazione LLM (LLMConfig)
        """
        self.config = config
        self.model_name = config.model_name
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature
    
    @abstractmethod
    async def enhance_description(
        self,
        asset_name: str,
        technical_desc: str,
        schema_context: str,
        column_info: List[Dict[str, Any]]
    ) -> str:
        """
        Arricchisce la descrizione di un asset con contesto business.
        
        Args:
            asset_name: Nome dell'asset
            technical_desc: Descrizione tecnica esistente
            schema_context: Contesto dello schema/dominio
            column_info: Informazioni sulle colonne (se tabella)
            
        Returns:
            str: Descrizione arricchita
        """
        pass
    
    @abstractmethod
    async def analyze_lineage_complexity(
        self,
        lineage_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analizza la complessità di un albero di lineage.
        
        Args:
            lineage_data: Dati del lineage tree
            
        Returns:
            Dict con:
                - complexity_score: int (1-10)
                - risk_factors: List[str]
                - critical_dependencies: List[str]
                - recommendations: List[str]
        """
        pass
    
    @abstractmethod
    async def analyze_change_impact(
        self,
        source_asset: str,
        change_type: str,
        change_details: Dict[str, Any],
        affected_lineage: Dict[str, List[Dict]]
    ) -> Dict[str, Any]:
        """
        Analizza l'impatto di una modifica sul lineage.
        
        Args:
            source_asset: Asset che subisce la modifica
            change_type: Tipo di modifica (column_drop, data_type_change, etc.)
            change_details: Dettagli della modifica
            affected_lineage: Lineage impattato (upstream/downstream)
            
        Returns:
            Dict con:
                - risk_level: str (LOW, MEDIUM, HIGH, CRITICAL)
                - business_impact: str
                - technical_impact: str
                - recommendations: List[str]
                - testing_strategy: List[str]
        """
        pass
    
    @abstractmethod
    async def generate_change_checklist(
        self,
        impact_analysis: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Genera una checklist operativa per implementare una modifica.
        
        Args:
            impact_analysis: Risultato dell'analisi di impatto
            
        Returns:
            Dict con:
                - governance_tasks: List[str]
                - pre_change_tasks: List[str]
                - execution_tasks: List[str]
                - validation_tasks: List[str]
                - rollback_procedures: List[str]
                - stakeholder_notifications: List[str]
                - monitoring_tasks: List[str]
        """
        pass
    
    @abstractmethod
    async def enhance_documentation(
        self,
        asset_info: Dict[str, Any],
        lineage_context: Dict[str, List[Dict]],
        business_context: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Arricchisce la documentazione di un asset.
        
        Args:
            asset_info: Informazioni sull'asset
            lineage_context: Contesto dal lineage
            business_context: Contesto business
            
        Returns:
            Dict con:
                - enhanced_description: str
                - business_purpose: str
                - suggested_tags: List[str]
                - business_terms: List[str]
                - suggested_quality_rules: List[str]
                - compliance_notes: str
        """
        pass
    
    async def _call_llm(
        self,
        prompt: str,
        system_message: Optional[str] = None
    ) -> str:
        """
        Metodo helper per chiamate LLM.
        Può essere sovrascritto dai client specifici.
        
        Args:
            prompt: Prompt per l'LLM
            system_message: Messaggio di sistema opzionale
            
        Returns:
            str: Risposta dell'LLM
        """
        raise NotImplementedError("Subclass must implement _call_llm")
    
    def _build_prompt(
        self,
        template: str,
        **kwargs
    ) -> str:
        """
        Helper per costruire prompt con template.
        
        Args:
            template: Template del prompt
            **kwargs: Variabili da sostituire nel template
            
        Returns:
            str: Prompt formattato
        """
        return template.format(**kwargs)