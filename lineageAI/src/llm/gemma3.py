"""
Client Gemma3 4B tramite Ollama.
Google Gemma3 4B - Modello open-source ottimizzato per data governance.
"""
import aiohttp
import json
from typing import Dict, List, Any, Optional

from .base import BaseLLMClient


class Gemma3Client(BaseLLMClient):
    """Client per Gemma3 4B via Ollama."""
    
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
        """Chiama Ollama API per Gemma3."""
        await self._ensure_session()
        
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
                "top_k": 40,
                "top_p": 0.9
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
            return f"Error calling Gemma3: {str(e)}"
    
    async def enhance_description(
        self,
        asset_name: str,
        technical_desc: str,
        schema_context: str,
        column_info: List[Dict[str, Any]]
    ) -> str:
        """Arricchisce descrizione asset con Gemma3."""
        prompt = f"""Sei un esperto di data governance. Arricchisci questa descrizione tecnica con contesto business.

Asset: {asset_name}
Descrizione tecnica: {technical_desc or 'Nessuna descrizione disponibile'}
Contesto schema: {schema_context or 'Non specificato'}

Fornisci una descrizione business-friendly in italiano, chiara e professionale (4-5 frasi).
Includi:
1. Scopo principale dell'asset
2. Valore business
3. Utenti tipici
4. Frequenza di aggiornamento se rilevante

Formato: Solo il testo della descrizione, senza intestazioni o punti elenco.
"""
        
        system_msg = "Sei un Data Architect esperto in data governance enterprise. Rispondi sempre in italiano con linguaggio professionale ma comprensibile."
        
        response = await self._call_llm(prompt, system_msg)
        return response.strip()
    
    async def analyze_lineage_complexity(
        self,
        lineage_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analizza complessita lineage con Gemma3."""
        nodes_count = lineage_data.get('children_count', 0)
        node_type = lineage_data.get('node_type', 'unknown')
        is_terminal = lineage_data.get('is_terminal', False)
        
        prompt = f"""Analizza la complessita di questo lineage tree:

Nodi totali: {nodes_count}
Tipo asset: {node_type}
E un nodo terminale: {is_terminal}

Fornisci analisi strutturata:

COMPLEXITY_SCORE: <numero 1-10>
RISK_LEVEL: <LOW/MEDIUM/HIGH/CRITICAL>

RISK_FACTORS:
- <fattore 1>
- <fattore 2>
- <fattore 3>

CRITICAL_DEPENDENCIES:
- <dipendenza critica 1>
- <dipendenza critica 2>

RECOMMENDATIONS:
- <raccomandazione 1>
- <raccomandazione 2>
- <raccomandazione 3>
- <raccomandazione 4>
- <raccomandazione 5>
"""
        
        response = await self._call_llm(prompt)
        
        # Parsing avanzato della risposta
        try:
            lines = response.strip().split('\n')
            complexity_score = 5
            risk_level = "MEDIUM"
            risk_factors = []
            critical_deps = []
            recommendations = []
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                if 'COMPLEXITY_SCORE:' in line:
                    try:
                        score_str = line.split(':')[-1].strip()
                        complexity_score = int(''.join(c for c in score_str if c.isdigit())[:1] or '5')
                    except:
                        pass
                
                elif 'RISK_LEVEL:' in line:
                    level = line.split(':')[-1].strip().upper()
                    if any(lvl in level for lvl in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']):
                        for lvl in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                            if lvl in level:
                                risk_level = lvl
                                break
                
                elif 'RISK_FACTORS:' in line:
                    current_section = 'risks'
                elif 'CRITICAL_DEPENDENCIES:' in line:
                    current_section = 'deps'
                elif 'RECOMMENDATIONS:' in line:
                    current_section = 'recs'
                
                elif line.startswith('-') or line.startswith('•'):
                    item = line[1:].strip()
                    if item:
                        if current_section == 'risks':
                            risk_factors.append(item)
                        elif current_section == 'deps':
                            critical_deps.append(item)
                        elif current_section == 'recs':
                            recommendations.append(item)
            
            # Fallback values
            if not risk_factors:
                risk_factors = [f"Lineage con {nodes_count} nodi richiede attenzione"]
            if not recommendations:
                recommendations = [
                    "Documenta le dipendenze critiche",
                    "Monitora le modifiche a monte",
                    "Testa impatti downstream prima di modifiche"
                ]
            
            return {
                'complexity_score': complexity_score,
                'risk_level': risk_level,
                'risk_factors': risk_factors[:5],
                'critical_dependencies': critical_deps[:3],
                'recommendations': recommendations[:7]
            }
            
        except Exception as e:
            # Fallback in caso di errore parsing
            if nodes_count < 5:
                return {
                    'complexity_score': 2,
                    'risk_level': 'LOW',
                    'risk_factors': ['Lineage semplice con poche dipendenze'],
                    'critical_dependencies': [],
                    'recommendations': ['Mantieni documentazione aggiornata']
                }
            elif nodes_count < 20:
                return {
                    'complexity_score': 5,
                    'risk_level': 'MEDIUM',
                    'risk_factors': [f'Lineage moderato con {nodes_count} nodi'],
                    'critical_dependencies': [],
                    'recommendations': [
                        'Monitora modifiche upstream',
                        'Documenta dipendenze chiave'
                    ]
                }
            else:
                return {
                    'complexity_score': 8,
                    'risk_level': 'HIGH',
                    'risk_factors': [f'Lineage complesso con {nodes_count} nodi'],
                    'critical_dependencies': [],
                    'recommendations': [
                        'Audit completo delle dipendenze',
                        'Piano di gestione modifiche robusto',
                        'Testing estensivo per ogni modifica'
                    ]
                }
    
    async def analyze_change_impact(
        self,
        source_asset: str,
        change_type: str,
        change_details: Dict[str, Any],
        affected_lineage: Dict[str, List[Dict]]
    ) -> Dict[str, Any]:
        """Analizza impatto modifiche con Gemma3."""
        downstream_count = len(affected_lineage.get('downstream', []))
        
        prompt = f"""Analizza l'impatto di questa modifica in un ambiente enterprise data governance:

Asset sorgente: {source_asset}
Tipo modifica: {change_type}
Descrizione: {change_details.get('description', '')}
Asset downstream impattati: {downstream_count}

Fornisci analisi dettagliata in italiano:

RISK_LEVEL: <LOW/MEDIUM/HIGH/CRITICAL>

BUSINESS_IMPACT:
<2-3 frasi sull'impatto business>

TECHNICAL_IMPACT:
<2-3 frasi sull'impatto tecnico>

RECOMMENDATIONS:
- <raccomandazione operativa 1>
- <raccomandazione operativa 2>
- <raccomandazione operativa 3>
- <raccomandazione operativa 4>
- <raccomandazione operativa 5>

TESTING_STRATEGY:
- <strategia test 1>
- <strategia test 2>
- <strategia test 3>
- <strategia test 4>
"""
        
        response = await self._call_llm(prompt)
        
        # Parsing della risposta
        risk_level = "MEDIUM"
        business_impact = ""
        technical_impact = ""
        recommendations = []
        testing_strategy = []
        
        lines = response.strip().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if 'RISK_LEVEL:' in line:
                level = line.split(':')[-1].strip().upper()
                for lvl in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                    if lvl in level:
                        risk_level = lvl
                        break
            
            elif 'BUSINESS_IMPACT:' in line:
                current_section = 'business'
            elif 'TECHNICAL_IMPACT:' in line:
                current_section = 'technical'
            elif 'RECOMMENDATIONS:' in line:
                current_section = 'recs'
            elif 'TESTING_STRATEGY:' in line:
                current_section = 'testing'
            
            elif line.startswith('-') or line.startswith('•'):
                item = line[1:].strip()
                if item:
                    if current_section == 'recs':
                        recommendations.append(item)
                    elif current_section == 'testing':
                        testing_strategy.append(item)
            
            elif line and current_section in ['business', 'technical']:
                if current_section == 'business':
                    business_impact += line + " "
                elif current_section == 'technical':
                    technical_impact += line + " "
        
        # Fallback values
        if not business_impact:
            business_impact = f"La modifica di tipo {change_type} potrebbe impattare {downstream_count} asset downstream."
        
        if not technical_impact:
            technical_impact = f"Impatto tecnico da valutare su {downstream_count} componenti dipendenti."
        
        if not recommendations:
            recommendations = [
                "Esegui backup completo prima della modifica",
                "Testa in ambiente non-produttivo",
                "Notifica i team downstream",
                "Prepara piano di rollback",
                "Monitora per 48h post-implementazione"
            ]
        
        if not testing_strategy:
            testing_strategy = [
                "Test unitari sui dati modificati",
                "Validazione integrity constraints",
                "Test integration con sistemi downstream",
                "Smoke test applicazioni consumer"
            ]
        
        return {
            'risk_level': risk_level,
            'business_impact': business_impact.strip(),
            'technical_impact': technical_impact.strip(),
            'recommendations': recommendations[:5],
            'testing_strategy': testing_strategy[:4]
        }
    
    async def generate_change_checklist(
        self,
        impact_analysis: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Genera checklist operativa con Gemma3."""
        risk_level = impact_analysis.get('risk_level', 'MEDIUM')
        
        prompt = f"""Genera una checklist operativa dettagliata per implementare questa modifica.

Livello di rischio: {risk_level}

Fornisci checklist strutturata per ciascuna fase:

GOVERNANCE_TASKS:
- <task governance 1>
- <task governance 2>
- <task governance 3>

PRE_CHANGE_TASKS:
- <task preparazione 1>
- <task preparazione 2>
- <task preparazione 3>

EXECUTION_TASKS:
- <task esecuzione 1>
- <task esecuzione 2>
- <task esecuzione 3>

VALIDATION_TASKS:
- <task validazione 1>
- <task validazione 2>
- <task validazione 3>

ROLLBACK_PROCEDURES:
- <procedura rollback 1>
- <procedura rollback 2>

STAKEHOLDER_NOTIFICATIONS:
- <notifica stakeholder 1>
- <notifica stakeholder 2>

MONITORING_TASKS:
- <task monitoring 1>
- <task monitoring 2>
- <task monitoring 3>
"""
        
        response = await self._call_llm(prompt)
        
        # Parsing checklist
        checklist = {
            'governance_tasks': [],
            'pre_change_tasks': [],
            'execution_tasks': [],
            'validation_tasks': [],
            'rollback_procedures': [],
            'stakeholder_notifications': [],
            'monitoring_tasks': []
        }
        
        current_section = None
        section_map = {
            'GOVERNANCE_TASKS:': 'governance_tasks',
            'PRE_CHANGE_TASKS:': 'pre_change_tasks',
            'EXECUTION_TASKS:': 'execution_tasks',
            'VALIDATION_TASKS:': 'validation_tasks',
            'ROLLBACK_PROCEDURES:': 'rollback_procedures',
            'STAKEHOLDER_NOTIFICATIONS:': 'stakeholder_notifications',
            'MONITORING_TASKS:': 'monitoring_tasks'
        }
        
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check se e una nuova sezione
            for key, section_name in section_map.items():
                if key in line:
                    current_section = section_name
                    break
            
            # Aggiungi item alla sezione corrente
            if (line.startswith('-') or line.startswith('•')) and current_section:
                item = line[1:].strip()
                if item and len(checklist[current_section]) < 5:
                    checklist[current_section].append(item)
        
        # Fallback per sezioni vuote
        if not checklist['governance_tasks']:
            checklist['governance_tasks'] = [
                "Sottometti change request formale",
                "Ottieni approvazione data owner",
                "Documenta risk assessment"
            ]
        
        if not checklist['pre_change_tasks']:
            checklist['pre_change_tasks'] = [
                "Backup completo dati",
                "Verifica ambiente test disponibile",
                "Prepara script rollback"
            ]
        
        if not checklist['execution_tasks']:
            checklist['execution_tasks'] = [
                "Implementa in test",
                "Verifica risultati",
                "Deploy in produzione"
            ]
        
        if not checklist['validation_tasks']:
            checklist['validation_tasks'] = [
                "Test qualita dati",
                "Verifica lineage",
                "Validazione business rules"
            ]
        
        if not checklist['rollback_procedures']:
            checklist['rollback_procedures'] = [
                "Restore da backup",
                "Verifica ripristino"
            ]
        
        if not checklist['stakeholder_notifications']:
            checklist['stakeholder_notifications'] = [
                "Pre-change: notifica finestra manutenzione",
                "Post-change: conferma successo"
            ]
        
        if not checklist['monitoring_tasks']:
            checklist['monitoring_tasks'] = [
                "Monitora job downstream 24-48h",
                "Verifica alert/anomalie",
                "Report post-implementazione"
            ]
        
        return checklist
    
    async def enhance_documentation(
        self,
        asset_info: Dict[str, Any],
        lineage_context: Dict[str, List[Dict]],
        business_context: Dict[str, str]
    ) -> Dict[str, Any]:
        """Arricchisce documentazione con Gemma3."""
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

ENHANCED_DESCRIPTION:
<4-5 frasi descrizione business-friendly>

BUSINESS_PURPOSE:
<scopo principale business>

SUGGESTED_TAGS:
- <tag 1>
- <tag 2>
- <tag 3>
- <tag 4>
- <tag 5>

QUALITY_RULES:
- <regola qualita 1>
- <regola qualita 2>
- <regola qualita 3>
- <regola qualita 4>
- <regola qualita 5>

COMPLIANCE_NOTES:
<note compliance e governance>
"""
        
        response = await self._call_llm(prompt)
        
        # Parsing response
        enhanced_desc = ""
        business_purpose = ""
        tags = []
        quality_rules = []
        compliance_notes = ""
        
        lines = response.strip().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if 'ENHANCED_DESCRIPTION:' in line:
                current_section = 'desc'
            elif 'BUSINESS_PURPOSE:' in line:
                current_section = 'purpose'
            elif 'SUGGESTED_TAGS:' in line:
                current_section = 'tags'
            elif 'QUALITY_RULES:' in line:
                current_section = 'rules'
            elif 'COMPLIANCE_NOTES:' in line:
                current_section = 'compliance'
            
            elif line.startswith('-') or line.startswith('•'):
                item = line[1:].strip()
                if item:
                    if current_section == 'tags':
                        tags.append(item)
                    elif current_section == 'rules':
                        quality_rules.append(item)
            
            elif line and current_section in ['desc', 'purpose', 'compliance']:
                if current_section == 'desc':
                    enhanced_desc += line + " "
                elif current_section == 'purpose':
                    business_purpose += line + " "
                elif current_section == 'compliance':
                    compliance_notes += line + " "
        
        # Fallback values
        if not enhanced_desc:
            enhanced_desc = f"Asset {asset_type} utilizzato nel dominio {domain or 'enterprise'}. " \
                          f"Contiene dati critici per le operazioni business. " \
                          f"Dipende da {upstream_count} sorgenti upstream."
        
        if not business_purpose:
            business_purpose = f"Asset operativo per gestione dati {domain or 'enterprise'}"
        
        if not tags:
            tags = ["data-governance", "enterprise", "managed", "production", asset_type.lower()]
        
        if not quality_rules:
            quality_rules = [
                "Completezza: verifica assenza valori nulli in campi chiave",
                "Consistenza: validazione formati standard",
                "Accuratezza: controllo range valori attesi",
                "Tempestivita: verifica aggiornamento dati",
                "Unicita: controllo duplicati"
            ]
        
        if not compliance_notes:
            compliance_notes = "Verificare requisiti GDPR se contiene dati personali. " \
                             "Applicare retention policy aziendale. " \
                             "Documentare data lineage per audit."
        
        return {
            'enhanced_description': enhanced_desc.strip(),
            'business_purpose': business_purpose.strip(),
            'suggested_tags': tags[:7],
            'business_terms': ["Data Asset", "Enterprise Resource", "Managed Data"],
            'suggested_quality_rules': quality_rules[:5],
            'compliance_notes': compliance_notes.strip()
        }
    
    async def close(self):
        """Chiude la sessione."""
        if self.session and not self.session.closed:
            await self.session.close()