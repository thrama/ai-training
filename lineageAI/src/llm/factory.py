"""
Factory per la creazione di client LLM.
Integra il sistema di astrazione LLM multi-provider.
"""
from dataclasses import dataclass
from typing import Optional

from .base import BaseLLMClient
from .tinyllama import TinyLlamaClient
from .claude import ClaudeClient

# IMPORTA da settings invece di ridefinirlo
from ..config.settings import LLMProvider  # ← CAMBIA QUESTA RIGA


@dataclass
class LLMConfig:
    provider: LLMProvider
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.1


class LLMFactory:
    """Factory per creare istanze LLM basate sulla configurazione."""
    
    @staticmethod
    def create_llm_client(config: LLMConfig) -> BaseLLMClient:
        """
        Crea client LLM basato sulla configurazione.
        
        Args:
            config: Configurazione LLM
            
        Returns:
            BaseLLMClient: Client LLM configurato
            
        Raises:
            ValueError: Se il provider non è supportato
        """
        if config.provider == LLMProvider.TINYLLAMA:
            return TinyLlamaClient(config)
        elif config.provider == LLMProvider.CLAUDE:
            return ClaudeClient(config)
        else:
            raise ValueError(f"Provider LLM non supportato: {config.provider}")
    
    @staticmethod
    def get_available_providers() -> list[str]:
        """Restituisce la lista dei provider disponibili."""
        return [provider.value for provider in LLMProvider]
    
    @staticmethod
    def validate_config(config: LLMConfig) -> bool:
        """
        Valida una configurazione LLM.
        
        Args:
            config: Configurazione da validare
            
        Returns:
            bool: True se valida, False altrimenti
        """
        if config.provider == LLMProvider.CLAUDE:
            return config.api_key is not None
        elif config.provider == LLMProvider.TINYLLAMA:
            return config.base_url is not None
        
        return False