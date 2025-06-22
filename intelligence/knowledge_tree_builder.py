# intelligence/knowledge_tree_builder.py
import json
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import re
import anthropic
import os
import random

from utils.logging import structured_logger as logger
from config.settings import ANTHROPIC_API_KEY

# Claude 4 Opus - same as advanced system
CLAUDE_MODEL = 'claude-opus-4-20250514'

# Infinite retry configuration for consistent quality
BASE_DELAY = 2  # seconds
MAX_DELAY = 60  # seconds (cap the exponential backoff)
DELAY_JITTER = 0.5  # random variance to spread requests

class FactualKnowledgeTreeBuilder:
    """
    Builds knowledge tree skeleton based on high-certainty factual extraction
    Phase 1: Extract core facts and relationships
    Phase 2: Propose tree structure for user validation  
    Phase 3: Augment with additional sources
    """
    
    def __init__(self):
        # Use environment variable for API key instead of config import
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            # Fallback to config if env var not set
            api_key = ANTHROPIC_API_KEY
        
        self.claude_client = anthropic.Anthropic(api_key=api_key)
        
    async def _make_claude_request(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.3, agent_name: str = "Factual Extractor") -> str:
        """Make Claude API request with infinite retries until successful - ensures consistent quality"""
        if not self.claude_client:
            raise Exception("Claude client not available - cannot provide premium analysis")
            
        attempt = 0
        while True:
            attempt += 1
            try:
                # Add progressive delay with jitter
                if attempt > 1:
                    delay = min(BASE_DELAY * (1.5 ** (attempt - 2)), MAX_DELAY)
                    jitter = random.uniform(-DELAY_JITTER, DELAY_JITTER)
                    total_delay = max(0.1, delay + jitter)
                    
                    logger.info(f"⏳ {agent_name}: Claude servers busy, retrying in {total_delay:.1f}s (attempt {attempt})")
                    await asyncio.sleep(total_delay)
                
                # Small delay between all requests to be respectful
                await asyncio.sleep(random.uniform(0.2, 0.8))
                
                logger.info(f"🤖 {agent_name}: Sending request to Claude 4 Opus (attempt {attempt})")
                
                response = await asyncio.to_thread(
                    self.claude_client.messages.create,
                    model=CLAUDE_MODEL,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                
                logger.info(f"✅ {agent_name}: Claude 4 Opus responded successfully (attempt {attempt})")
                return response.content[0].text
                
            except Exception as e:
                error_str = str(e)
                
                # Check error types
                if "529" in error_str or "overloaded" in error_str.lower():
                    logger.warning(f"⚠️ {agent_name}: Claude servers overloaded (attempt {attempt}) - will retry until successful")
                    continue  # Keep retrying overload errors
                    
                elif "401" in error_str or "authentication" in error_str.lower():
                    logger.error(f"❌ {agent_name}: Authentication failed - check API key")
                    raise Exception(f"API authentication failed: {error_str}")
                    
                elif "rate_limit" in error_str.lower() or "429" in error_str:
                    logger.warning(f"⚠️ {agent_name}: Rate limited (attempt {attempt}) - will retry until successful")
                    continue  # Keep retrying rate limits
                    
                else:
                    logger.warning(f"⚠️ {agent_name}: Unexpected error (attempt {attempt}): {error_str} - retrying")
                    continue  # Keep retrying other errors too
                    
        # This should never be reached due to infinite loop

    async def extract_core_facts(self, emails: List[Dict]) -> Dict:
        """Extract high-certainty facts from email communications"""
        
        # Prepare email content for analysis
        email_sample = []
        for email in emails[:50]:  # Sample for initial fact extraction
            content = email.get('content', '')[:500]  # Limit content length
            metadata = email.get('metadata', {})
            sender = metadata.get('sender', 'Unknown')
            subject = metadata.get('subject', 'No Subject')
            
            email_sample.append({
                'sender': sender,
                'subject': subject,
                'content_snippet': content
            })
        
        # Extract organizational relationships with high confidence
        org_structure = await self._extract_organizational_structure(email_sample)
        
        # Extract business entities and products
        business_entities = await self._extract_business_entities(email_sample)
        
        # Extract communication patterns (factual, not interpretive)
        communication_patterns = await self._extract_communication_patterns(emails)
        
        return {
            'organizational_structure': org_structure,
            'business_entities': business_entities,
            'communication_patterns': communication_patterns,
            'extraction_metadata': {
                'emails_analyzed': len(emails),
                'sample_size': len(email_sample),
                'extraction_timestamp': datetime.now().isoformat(),
                'confidence_threshold': 'high'
            }
        }
    
    async def _extract_organizational_structure(self, email_sample: List[Dict]) -> Dict:
        """Extract organizational roles and relationships with high certainty - guaranteed success with infinite retries"""
        
        prompt = f"""
You are a factual data extractor. Analyze these email communications to identify ONLY high-certainty organizational relationships.

Email Sample:
{json.dumps(email_sample[:20], indent=2)}

Extract ONLY the following factual information:
1. ORGANIZATIONAL ROLES: Who holds what specific titles or roles? (Only if explicitly mentioned)
2. COMPANY STRUCTURE: What companies/entities are mentioned as being related?
3. REPORTING RELATIONSHIPS: Who reports to whom? (Only if clearly stated)

Rules:
- ONLY extract information that is explicitly stated or has very high confidence
- Do NOT infer or assume relationships
- Do NOT provide strategic analysis
- Use confidence levels: HIGH (explicitly stated), MEDIUM (strongly implied), LOW (possible)
- If uncertain, mark as "needs_clarification"

Return ONLY valid JSON format:
{{
    "roles": [
        {{
            "email": "person@domain.com",
            "role": "specific title",
            "confidence": "HIGH/MEDIUM/LOW",
            "evidence": "direct quote or clear indication"
        }}
    ],
    "companies": [
        {{
            "name": "company name",
            "relationship": "parent/subsidiary/product/etc",
            "confidence": "HIGH/MEDIUM/LOW",
            "evidence": "supporting evidence"
        }}
    ],
    "relationships": [
        {{
            "person_a": "email@domain.com",
            "person_b": "email@domain.com", 
            "relationship_type": "reports_to/collaborates_with/etc",
            "confidence": "HIGH/MEDIUM/LOW",
            "evidence": "supporting evidence"
        }}
    ],
    "needs_clarification": ["questions to ask user for validation"]
}}
"""
        
        logger.info(f"🤖 Organizational Structure Extractor: Analyzing with infinite retries")
        
        # Get response with infinite retries
        response_text = await self._make_claude_request(prompt, max_tokens=4000, temperature=0.3, agent_name="Organizational Structure Extractor")
        
        # Parse JSON with retry on failure
        while True:
            try:
                result = json.loads(response_text)
                logger.info(f"✅ Organizational Structure: Extracted {len(result.get('roles', []))} roles and {len(result.get('companies', []))} companies")
                return result
            except json.JSONDecodeError:
                logger.warning(f"⚠️ Organizational Structure Extractor: JSON parsing failed, re-requesting")
                retry_prompt = prompt + "\n\nIMPORTANT: Respond with valid JSON only, no markdown or explanations."
                response_text = await self._make_claude_request(retry_prompt, agent_name="Organizational Structure Extractor (JSON retry)")
    
    async def _extract_business_entities(self, email_sample: List[Dict]) -> Dict:
        """Extract business entities, products, and P&Ls with high certainty - guaranteed success with infinite retries"""
        
        prompt = f"""
You are a factual business entity extractor. Analyze these communications to identify business entities and products.

Email Sample:
{json.dumps(email_sample[:20], indent=2)}

Extract ONLY factual information about:
1. PRODUCTS/SERVICES: What specific products or services are mentioned?
2. BUSINESS UNITS: What P&Ls, divisions, or business units are referenced?
3. PARTNERSHIPS: What external companies are mentioned as partners/clients?
4. TECHNOLOGIES: What specific technologies or platforms are discussed?

Rules:
- ONLY extract entities that are explicitly mentioned
- Do NOT infer business relationships
- Use confidence levels based on clarity of mention
- Focus on factual identification, not analysis

Return ONLY valid JSON format:
{{
    "products": [
        {{
            "name": "product name",
            "type": "software/service/platform/etc",
            "confidence": "HIGH/MEDIUM/LOW",
            "evidence": "where mentioned"
        }}
    ],
    "business_units": [
        {{
            "name": "unit name",
            "type": "P&L/division/department",
            "confidence": "HIGH/MEDIUM/LOW",
            "evidence": "supporting context"
        }}
    ],
    "external_entities": [
        {{
            "name": "company/organization name",
            "relationship_type": "client/partner/vendor/competitor",
            "confidence": "HIGH/MEDIUM/LOW",
            "evidence": "context of mention"
        }}
    ],
    "technologies": [
        {{
            "name": "technology name",
            "category": "AI/software/platform/etc",
            "confidence": "HIGH/MEDIUM/LOW",
            "context": "how it's used or mentioned"
        }}
    ]
}}
"""
        
        logger.info(f"🤖 Business Entity Extractor: Analyzing with infinite retries")
        
        # Get response with infinite retries
        response_text = await self._make_claude_request(prompt, max_tokens=4000, temperature=0.3, agent_name="Business Entity Extractor")
        
        # Parse JSON with retry on failure
        while True:
            try:
                result = json.loads(response_text)
                logger.info(f"✅ Business Entities: Extracted {len(result.get('products', []))} products and {len(result.get('external_entities', []))} external entities")
                return result
            except json.JSONDecodeError:
                logger.warning(f"⚠️ Business Entity Extractor: JSON parsing failed, re-requesting")
                retry_prompt = prompt + "\n\nIMPORTANT: Respond with valid JSON only, no markdown or explanations."
                response_text = await self._make_claude_request(retry_prompt, agent_name="Business Entity Extractor (JSON retry)")
    
    async def _extract_communication_patterns(self, emails: List[Dict]) -> Dict:
        """Extract factual communication patterns without interpretation"""
        
        # Count communication frequency by sender
        sender_counts = {}
        domain_counts = {}
        
        for email in emails:
            metadata = email.get('metadata', {})
            sender = metadata.get('sender', 'Unknown')
            
            # Count by sender
            sender_counts[sender] = sender_counts.get(sender, 0) + 1
            
            # Count by domain
            if '@' in sender:
                domain = sender.split('@')[1]
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        # Sort by frequency
        top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "communication_frequency": {
                "top_senders": [{"email": sender, "count": count} for sender, count in top_senders],
                "top_domains": [{"domain": domain, "count": count} for domain, count in top_domains],
                "total_emails": len(emails)
            },
            "analysis_period": {
                "start_date": min([email.get('created_at', '') for email in emails]) if emails else None,
                "end_date": max([email.get('created_at', '') for email in emails]) if emails else None
            }
        }
    
    async def propose_knowledge_tree_structure(self, core_facts: Dict) -> Dict:
        """Propose a knowledge tree structure for user validation - guaranteed success with infinite retries"""
        
        prompt = f"""
Based on these extracted facts, propose a knowledge tree structure for validation.

Core Facts:
{json.dumps(core_facts, indent=2)}

Create a tree structure that:
1. Organizes information hierarchically
2. Separates high-confidence facts from areas needing clarification
3. Identifies gaps where additional data sources would help
4. Suggests specific questions for user validation

Return ONLY valid JSON format:
{{
    "proposed_tree": {{
        "session42_organization": {{
            "leadership": {{
                "high_confidence": ["facts we're sure about"],
                "needs_validation": ["questions for user"]
            }},
            "business_units": {{
                "high_confidence": ["confirmed P&Ls"],
                "needs_validation": ["possible business units to confirm"]
            }},
            "products": {{
                "high_confidence": ["confirmed products"],
                "needs_validation": ["possible products to confirm"]
            }}
        }},
        "external_relationships": {{
            "partners": {{
                "high_confidence": ["confirmed partners"],
                "needs_validation": ["possible partners"]
            }},
            "competitors": {{
                "high_confidence": ["confirmed competitors"],
                "needs_validation": ["possible competitors"]
            }}
        }}
    }},
    "validation_questions": [
        "Specific questions to ask user to confirm/correct the tree"
    ],
    "data_gaps": [
        "Areas where additional data sources (Slack, docs, etc.) would be valuable"
    ],
    "next_steps": [
        "Recommended next actions for tree refinement"
    ]
}}
"""
        
        logger.info(f"🤖 Tree Structure Proposer: Analyzing with infinite retries")
        
        # Get response with infinite retries
        response_text = await self._make_claude_request(prompt, max_tokens=4000, temperature=0.3, agent_name="Tree Structure Proposer")
        
        # Parse JSON with retry on failure
        while True:
            try:
                result = json.loads(response_text)
                logger.info(f"✅ Tree Structure: Proposed structure with {len(result.get('validation_questions', []))} validation questions")
                return result
            except json.JSONDecodeError:
                logger.warning(f"⚠️ Tree Structure Proposer: JSON parsing failed, re-requesting")
                retry_prompt = prompt + "\n\nIMPORTANT: Respond with valid JSON only, no markdown or explanations."
                response_text = await self._make_claude_request(retry_prompt, agent_name="Tree Structure Proposer (JSON retry)")
    
    async def build_factual_knowledge_tree(self, user_id: int, emails: List[Dict]) -> Dict:
        """Main method to build factual knowledge tree"""
        
        logger.info(f"🌳 Building factual knowledge tree for user {user_id}")
        logger.info(f"📧 Analyzing {len(emails)} emails for factual extraction")
        
        # Step 1: Extract core facts
        core_facts = await self.extract_core_facts(emails)
        
        # Step 2: Propose tree structure
        tree_proposal = await self.propose_knowledge_tree_structure(core_facts)
        
        # Step 3: Combine into knowledge tree
        knowledge_tree = {
            "tree_type": "factual_extraction_v1",
            "build_timestamp": datetime.now().isoformat(),
            "data_sources": ["email"],
            "core_facts": core_facts,
            "proposed_structure": tree_proposal,
            "status": "awaiting_user_validation",
            "confidence_levels": {
                "HIGH": "Explicitly stated or very clear evidence",
                "MEDIUM": "Strongly implied or contextually clear", 
                "LOW": "Possible but uncertain, needs validation"
            }
        }
        
        logger.info("✅ Factual knowledge tree built successfully")
        return knowledge_tree 