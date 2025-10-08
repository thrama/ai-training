"""
Client Claude tramite Anthropic API.
"""
from typing import Dict, List, Any, Optional
import anthropic
import httpx
import ssl

from .base import BaseLLMClient


class ClaudeClient(BaseLLMClient):
    """Client per Claude via Anthropic API."""
    
    def __init__(self, config):
        super().__init__(config)
        
        # Configurazione httpx per gestire SSL correttamente
        # Usa il context SSL di sistema (che include certificati aziendali)
        ssl_context = ssl.create_default_context()
        # In alternativa, se ancora non funziona, commenta la riga sopra e usa:
        # ssl_context = ssl._create_unverified_context()  # Solo per sviluppo!
        
        # Crea client httpx con configurazione SSL custom
        http_client = httpx.Client(
            timeout=httpx.Timeout(60.0, connect=15.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            #verify=ssl_context  # ← Usa SSL context personalizzato
            verify=False
        )
        
        self.client = anthropic.Anthropic(
            api_key=config.api_key,
            http_client=http_client
        )
    
    async def _call_llm(
        self,
        prompt: str,
        system_message: Optional[str] = None
    ) -> str:
        """Chiama Claude API."""
        try:
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_message or "Sei un assistente esperto in data governance e lineage.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except anthropic.APIConnectionError as e:
            return f"Error calling Claude: Connection error - {e.__class__.__name__}: {str(e)}"
        except anthropic.RateLimitError as e:
            return f"Error calling Claude: Rate limit exceeded - {str(e)}"
        except anthropic.APIStatusError as e:
            return f"Error calling Claude: API error {e.status_code} - {str(e)}"
        except Exception as e:
            return f"Error calling Claude: {type(e).__name__} - {str(e)}"
    
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

Fornisci una descrizione business-friendly in italiano, chiara e concisa (max 4 frasi).
Includi lo scopo principale e il valore business dell'asset.
"""
        return await self._call_llm(prompt)
    
    async def analyze_lineage_complexity(
        self,
        lineage_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analizza complessità lineage."""
        prompt = f"""Analizza la complessità di questo lineage tree:

Nodi totali: {lineage_data.get('children_count', 0)}
Tipo: {lineage_data.get('node_type', 'unknown')}
È terminale: {lineage_data.get('is_terminal', False)}

Fornisci in formato JSON:
{{
    "complexity_score": <1-10>,
    "risk_level": "<LOW/MEDIUM/HIGH/CRITICAL>",
    "risk_factors": ["factor1", "factor2"],
    "critical_dependencies": ["dep1"],
    "recommendations": ["rec1", "rec2"]
}}
"""
        
        response = await self._call_llm(prompt)
        
        try:
            import json
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(response[json_start:json_end])
                return result
        except:
            pass
        
        return {
            'complexity_score': 5,
            'risk_level': 'MEDIUM',
            'risk_factors': ['Analisi dettagliata non disponibile'],
            'critical_dependencies': [],
            'recommendations': ['Rivedi manualmente il lineage']
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
        
        prompt = f"""Analizza l'impatto di questa modifica in ambito enterprise data governance:

Asset sorgente: {source_asset}
Tipo modifica: {change_type}
Descrizione: {change_details.get('description', '')}
Asset downstream impattati: {downstream_count}

Fornisci analisi dettagliata in italiano con:
1. Livello rischio (LOW/MEDIUM/HIGH/CRITICAL)
2. Impatto business (2-3 frasi)
3. Impatto tecnico (2-3 frasi)
4. 3-5 raccomandazioni operative
5. Strategia di testing (3-4 punti)
"""
        
        response = await self._call_llm(prompt)
        
        risk_level = "MEDIUM"
        if "CRITICAL" in response:
            risk_level = "CRITICAL"
        elif "HIGH" in response and "CRITICAL" not in response:
            risk_level = "HIGH"
        elif "LOW" in response and "MEDIUM" not in response:
            risk_level = "LOW"
        
        return {
            'risk_level': risk_level,
            'business_impact': response[:400],
            'technical_impact': f"Analisi completa: {downstream_count} asset downstream potrebbero essere impattati",
            'recommendations': [
                line.strip() for line in response.split('\n') 
                if line.strip().startswith(('•', '-', '*')) or 
                   any(str(i) in line[:3] for i in range(1, 10))
            ][:5],
            'testing_strategy': [
                "Validazione data quality pre/post change",
                "Test lineage integrity",
                "Smoke test applicazioni downstream",
                "Validazione business rules"
            ]
        }
    
    async def generate_change_checklist(
        self,
        impact_analysis: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Genera checklist completa."""
        return {
            'governance_tasks': [
                "Sottoponi change request formale",
                "Ottieni approvazione data owner e business owner",
                "Documenta risk assessment"
            ],
            'pre_change_tasks': [
                "Esegui backup completo dati",
                "Verifica ambienti test disponibili",
                "Prepara script di rollback"
            ],
            'execution_tasks': [
                "Implementa modifica in ambiente test",
                "Esegui smoke test immediati",
                "Valida risultati attesi"
            ],
            'validation_tasks': [
                "Test qualità dati completi",
                "Verifica integrità lineage",
                "Validazione business rules"
            ],
            'rollback_procedures': [
                "Procedura restore da backup",
                "Rollback configurazioni",
                "Notifica rollback completato"
            ],
            'stakeholder_notifications': [
                "Pre-change: notifica finestra manutenzione",
                "Durante change: status update",
                "Post-change: conferma successo"
            ],
            'monitoring_tasks': [
                "Monitora job downstream per 24-48h",
                "Verifica alert/anomalie",
                "Report post-implementazione"
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
        asset_type = asset_info.get('classType', '')
        current_desc = asset_info.get('description', '')
        
        upstream_count = len(lineage_context.get('upstream', []))
        domain = business_context.get('domain', '')
        
        prompt = f"""Arricchisci la documentazione per questo asset di data governance:

Nome: {asset_name}
Tipo: {asset_type}
Descrizione attuale: {current_desc or 'Non disponibile'}
Dominio business: {domain or 'Non specificato'}
Dipendenze upstream: {upstream_count}

Fornisci in italiano:
1. Descrizione arricchita business-friendly (3-4 frasi)
2. Scopo business principale
3. 5-7 tag pertinenti
4. 3-5 regole qualità suggerite
5. Note compliance/governance
"""
        
        response = await self._call_llm(prompt)
        
        return {
            'enhanced_description': response[:500],
            'business_purpose': f"Asset {asset_type} utilizzato nel dominio {domain or 'enterprise'}",
            'suggested_tags': ["data-governance", "enterprise", "managed", "production"],
            'business_terms': ["Data Asset", "Enterprise Resource"],
            'suggested_quality_rules': [
                "Completezza: verifica assenza valori nulli in campi chiave",
                "Consistenza: validazione formati standard",
                "Accuratezza: controllo range valori attesi",
                "Tempestività: verifica aggiornamento dati"
            ],
            'compliance_notes': "Verificare requisiti GDPR se contiene dati personali. Applicare retention policy aziendale."
        }