"""
Configurazioni centrali del progetto EDC-MCP-LLM
"""
import os
import sys
import base64
from typing import Optional, List
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, computed_field
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class LLMProvider(str, Enum):
    """Provider LLM supportati."""
    TINYLLAMA = "tinyllama"
    CLAUDE = "claude"
    GEMMA3 = "gemma3"

class Settings(BaseSettings):
    """Configurazioni principali dell'applicazione"""
    
    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=True)
    
    # ========================================
    # EDC Configuration - UNICA FONTE
    # ========================================
    edc_base_url: str = Field(..., description="URL base di EDC")
    edc_username: str = Field(..., description="Username EDC")
    edc_password: str = Field(..., description="Password EDC")
    edc_api_version: str = Field(default="2", description="Versione API EDC")
    
    # Parametri API EDC
    edc_associations: str = Field(
        default="core.DataSetDataFlow,core.DirectionalDataFlow",
        description="Associations da includere (solo quelle valide)"
    )
    edc_include_dst_links: bool = Field(
        default=True,
        description="Include destination links"
    )
    edc_include_ref_objects: bool = Field(
        default=True,
        description="Include reference objects"
    )
    edc_include_src_links: bool = Field(default=True)
    edc_page_size: int = Field(default=20)
    edc_offset: int = Field(default=0)
    
    # Performance EDC
    edc_request_timeout: int = Field(default=30)
    edc_max_retries: int = Field(default=3)
    edc_max_tree_depth: int = Field(default=100)
    edc_max_total_nodes: int = Field(default=10000)
    edc_enable_child_deduplication: bool = Field(default=True)
    
    # ========================================
    # LLM Configuration
    # ========================================
    default_llm_provider: LLMProvider = Field(default=LLMProvider.CLAUDE)
    
    # Claude
    claude_api_key: Optional[str] = Field(default=None)
    claude_model: str = Field(default="claude-sonnet-4-20250514")
    claude_max_tokens: int = Field(default=4000)
    claude_temperature: float = Field(default=0.1)
    
    # TinyLlama (Raspberry Pi)
    tinyllama_base_url: str = Field(default="http://192.168.1.17:11434")
    tinyllama_model: str = Field(default="tinyllama")
    tinyllama_max_tokens: int = Field(default=2000)
    tinyllama_temperature: float = Field(default=0.1)
    
    # Gemma3 (PC Locale)
    gemma3_base_url: str = Field(default="http://localhost:11434")
    gemma3_model: str = Field(default="gemma3:4b")
    gemma3_max_tokens: int = Field(default=4000)
    gemma3_temperature: float = Field(default=0.1)
    
    # ========================================
    # MCP Server
    # ========================================
    mcp_server_host: str = Field(default="localhost")
    mcp_server_port: int = Field(default=8000)
    
    # Performance
    max_concurrent_requests: int = Field(default=10)
    request_timeout: int = Field(default=30)
    lineage_max_depth: int = Field(default=10)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    
    class Config:
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        case_sensitive = False
        extra = "ignore"
    
    # ========================================
    # Computed Properties
    # ========================================
    
    @computed_field
    @property
    def edc_authorization_header(self) -> str:
        """Genera header Authorization per EDC"""
        credentials = f"{self.edc_username}:{self.edc_password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    @computed_field
    @property
    def edc_browse_url(self) -> str:
        """
        URL completo per API catalog/data/objects (formato Allitude)
        Esempio: https://edc.collaudo.servizi.allitude.it:9086/access/2/catalog/data/objects
        """
        return f"{self.edc_base_url}/{self.edc_api_version}/catalog/data/objects"
    
    @computed_field
    @property
    def edc_associations_list(self) -> List[str]:
        """Lista associations"""
        return [a.strip() for a in self.edc_associations.split(',') if a.strip()]
    
    def get_edc_headers(self) -> dict:
        """Headers per chiamate EDC"""
        return {
            "Authorization": self.edc_authorization_header,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Connection": "keep-alive",
            "User-Agent": "EDC-MCP-LLM Integration"
        }
    
    def get_edc_static_params(self) -> list:
        """Parametri statici per API EDC (compatibilita TreeBuilder)"""
        params = []
        for assoc in self.edc_associations_list:
            params.append(('associations', assoc))
        
        params.extend([
            ('includeDstLinks', str(self.edc_include_dst_links).lower()),
            ('includeRefObjects', str(self.edc_include_ref_objects).lower()),
            ('includeSrcLinks', str(self.edc_include_src_links).lower()),
            ('offset', str(self.edc_offset)),
            ('pageSize', str(self.edc_page_size))
        ])
        
        return params
    
    def is_claude_available(self) -> bool:
        """Verifica se Claude e configurato"""
        return self.claude_api_key is not None and len(self.claude_api_key) > 10
    
    def is_tinyllama_available(self) -> bool:
        """Verifica se TinyLlama (Raspberry) e disponibile"""
        try:
            import requests
            response = requests.get(f"{self.tinyllama_base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def is_gemma3_available(self) -> bool:
        """Verifica se Gemma3 (locale) e disponibile"""
        try:
            import requests
            response = requests.get(f"{self.gemma3_base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def is_ollama_available(self) -> bool:
        """Verifica se almeno un Ollama e disponibile (compatibilita)"""
        return self.is_tinyllama_available() or self.is_gemma3_available()

# Singleton settings instance
try:
    settings = Settings()
    
    # Debug: stampa se ha caricato correttamente
    if "example.com" in settings.edc_base_url:
        print(f"[WARNING] Settings using fallback config!")
        print(f"   .env file not found or not loaded")
        print(f"   Looking for: {Path(__file__).parent.parent.parent / '.env'}")
    else:
        print(f"[OK] Settings loaded successfully from .env")
        print(f"   EDC URL: {settings.edc_base_url}")
        
except Exception as e:
    print(f"[WARNING] Could not load settings from .env: {e}")
    print("   Using default settings...")
    settings = Settings(
        edc_base_url="https://example.com/ldm",
        edc_username="user",
        edc_password="pass"
    )