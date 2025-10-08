"""
Client TinyLlama tramite Ollama.
"""
import aiohttp
import json
from typing import Dict, List, Any, Optional

from .base import BaseLLMClient


class TinyLlamaClient(BaseLLMClient):
    """Client per TinyLlama via Ollama."""
    
    def __init__(self, config):
        super().__init__(config)
        self.base_url = config.base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _ensure_session(self):
        """Assicura che la sessione HTTP sia inizializzata."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def _call_llm(
        self,
        prompt: str,
        system_message: Optional[str] = None
    ) -> str:
        """Chiama Ollama API."""
        await self._ensure_session()
        
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        
        if system_message:
            payload["system"] = system_message
        
        try:
            async with self.session.post(url, json=payload) as response:
                response.raise_for_status()
                result = await response.json()
                return result.get('response', '')
        except Exception as e:
            return f"Error calling TinyLlama: {str(e)}"
    
    async def enhance_description(
        self,
        asset_name: str,
        technical_desc: str,
        schema_context: str,
        column_info: List[Dict[str, Any]]
    ) -> str:
        """Arricchisce descrizione asset."""
        prompt = f"""Arricchisci la seguente descrizione tecnica con contesto business.

Asset: {asset_name}
Descrizione tecnica: {technical_desc or 'Nessuna descrizione disponibile'}
Contesto schema: {schema_context or 'Non specificato'}

Fornisci una descrizione business-friendly in italiano, breve e chiara (max 3 frasi).
"""
        return await self._call_llm(prompt)
    
    async def analyze_lineage_complexity(
        self,
        lineage_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analizza complessità lineage."""
        nodes_count = lineage_data.get('children_count', 0)
        
        # Analisi semplificata per TinyLlama
        if nodes_count < 5:
            complexity_score = 2
            risk = "LOW"
        elif nodes_count < 20:
            complexity_score = 5
            risk = "MEDIUM"
        else:
            complexity_score = 8
            risk = "HIGH"
        
        return {
            'complexity_score': complexity_score,
            'risk_level': risk,
            'risk_factors': [f"Numero di nodi: {nodes_count}"],
            'critical_dependencies': [],
            'recommendations': [
                "Monitora le modifiche a monte",
                "Documenta le dipendenze critiche"
            ]
        }
    
    async def analyze_change_impact(
        self,
        source_asset: str,
        change_type: str,
        change_details: Dict[str, Any],
        affected_lineage: Dict[str, List[Dict]]
    ) -> Dict[str, Any]:
        """Analizza impatto modifiche."""
        downstream_count = len(affected_lineage.get('downstream', []))
        
        prompt = f"""Analizza l'impatto di questa modifica:

Asset: {source_asset}
Tipo modifica: {change_type}
Dettagli: {change_details.get('description', '')}
Asset impattati: {downstream_count}

Fornisci:
1. Livello di rischio (LOW/MEDIUM/HIGH/CRITICAL)
2. Impatto business (1 frase)
3. Impatto tecnico (1 frase)
4. 2 raccomandazioni principali
"""
        
        response = await self._call_llm(prompt)
        
        # Parsing semplificato della risposta
        risk_level = "MEDIUM"
        if "CRITICAL" in response.upper():
            risk_level = "CRITICAL"
        elif "HIGH" in response.upper():
            risk_level = "HIGH"
        elif "LOW" in response.upper():
            risk_level = "LOW"
        
        return {
            'risk_level': risk_level,
            'business_impact': response[:200],
            'technical_impact': f"Potenziale impatto su {downstream_count} asset downstream",
            'recommendations': [
                "Effettua backup prima della modifica",
                "Testa in ambiente non-produttivo"
            ],
            'testing_strategy': [
                "Test unitari sui dati",
                "Validazione lineage"
            ]
        }
    
    async def generate_change_checklist(
        self,
        impact_analysis: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Genera checklist operativa."""
        return {
            'governance_tasks': [
                "Richiedi approvazione change request",
                "Notifica data owner"
            ],
            'pre_change_tasks': [
                "Backup dati esistenti",
                "Documenta stato corrente"
            ],
            'execution_tasks': [
                "Implementa modifica in test",
                "Verifica risultati"
            ],
            'validation_tasks': [
                "Test qualità dati",
                "Verifica lineage downstream"
            ],
            'rollback_procedures': [
                "Restore da backup se necessario"
            ],
            'stakeholder_notifications': [
                "Notifica team downstream"
            ],
            'monitoring_tasks': [
                "Monitora job downstream per 24h"
            ]
        }
    
    async def enhance_documentation(
        self,
        asset_info: Dict[str, Any],
        lineage_context: Dict[str, List[Dict]],
        business_context: Dict[str, str]
    ) -> Dict[str, Any]:
        """Arricchisce documentazione."""
        asset_name = asset_info.get('name', '')
        
        prompt = f"""Arricchisci la documentazione per: {asset_name}

Fornisci:
1. Descrizione business (2-3 frasi)
2. Scopo principale
3. 3-5 tag pertinenti
"""
        
        response = await self._call_llm(prompt)
        
        return {
            'enhanced_description': response[:300],
            'business_purpose': f"Asset utilizzato per {asset_name}",
            'suggested_tags': ["data", "enterprise", "managed"],
            'business_terms': [],
            'suggested_quality_rules': [
                "Verifica completezza dati",
                "Controllo valori nulli"
            ],
            'compliance_notes': "Da verificare requisiti specifici"
        }
    
    async def close(self):
        """Chiude la sessione."""
        if self.session and not self.session.closed:
            await self.session.close()