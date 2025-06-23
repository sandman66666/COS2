"""
Contact Enrichment Integration
============================
Integration layer that replaces the existing contact enrichment system
with the new enhanced enricher.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from utils.logging import structured_logger as logger
from intelligence.d_enrichment.enhanced_enrichment import EnhancedContactEnricher, EnhancedEnrichmentResult
from models.database import get_db_manager

class ContactEnrichmentService:
    """
    Service layer for contact enrichment that provides a clean interface
    and integrates with the database storage layer.
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.enricher = EnhancedContactEnricher(user_id)
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the enrichment service"""
        try:
            await self.enricher.initialize()
            self._initialized = True
            logger.info(f"Contact enrichment service initialized for user {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize enrichment service for user {self.user_id}: {e}")
            return False
    
    async def enrich_contact(self, contact: Dict) -> Dict:
        """
        Enrich a single contact and return in the format expected by the application
        
        Args:
            contact: Contact data with at least 'email' field
            
        Returns:
            Enriched contact data in application format
        """
        if not self._initialized:
            await self.initialize()
        
        email = contact.get('email', '').strip()
        if not email:
            return self._create_empty_enrichment(email, "No email provided")
        
        try:
            # Get user's emails for content analysis
            user_emails = await self._get_user_emails()
            
            # Perform enrichment
            result = await self.enricher.enrich_contact(contact, user_emails)
            
            # Convert to application format
            formatted_result = self._format_enrichment_result(result)
            
            # Store the result
            await self._store_enrichment_result(result)
            
            logger.info(f"Successfully enriched contact {email} with confidence {result.confidence_score:.1%}")
            return formatted_result
            
        except Exception as e:
            logger.error(f"Contact enrichment failed for {email}: {e}")
            return self._create_empty_enrichment(email, str(e))
    
    async def enrich_contacts_batch(self, contacts: List[Dict], max_concurrent: int = 3) -> Dict[str, Dict]:
        """
        Enrich multiple contacts concurrently with rate limiting
        
        Args:
            contacts: List of contact dictionaries
            max_concurrent: Maximum number of concurrent enrichments
            
        Returns:
            Dictionary mapping email to enrichment results
        """
        if not self._initialized:
            await self.initialize()
        
        results = {}
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def enrich_single(contact: Dict) -> None:
            async with semaphore:
                email = contact.get('email', '').strip()
                if email:
                    result = await self.enrich_contact(contact)
                    results[email] = result
                    # Small delay between requests
                    await asyncio.sleep(1)
        
        # Create tasks for all contacts
        tasks = [enrich_single(contact) for contact in contacts if contact.get('email')]
        
        # Execute with progress tracking
        if tasks:
            logger.info(f"Starting batch enrichment of {len(tasks)} contacts")
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Completed batch enrichment: {len(results)} contacts processed")
        
        return results
    
    async def get_enriched_contact(self, email: str) -> Optional[Dict]:
        """
        Get previously enriched contact data from storage
        
        Args:
            email: Contact email
            
        Returns:
            Enriched contact data or None if not found
        """
        try:
            db_manager = get_db_manager()
            stored_data = await db_manager.get_contact_enrichment(self.user_id, email)
            
            if stored_data:
                return self._format_stored_enrichment(stored_data)
            
        except Exception as e:
            logger.error(f"Failed to retrieve enriched contact {email}: {e}")
        
        return None
    
    async def _get_user_emails(self) -> List[Dict]:
        """Get user's emails for content analysis"""
        try:
            db_manager = get_db_manager()
            emails = db_manager.get_user_emails(self.user_id, limit=1000)  # Get recent emails
            
            # Convert to dict format
            email_dicts = []
            for email in emails:
                email_dicts.append({
                    'id': email.id,
                    'sender': email.sender,
                    'recipients': email.recipients or [],
                    'subject': email.subject,
                    'body_text': email.body_text,
                    'body_html': email.body_html,
                    'email_date': email.email_date.isoformat() if email.email_date else None
                })
            
            return email_dicts
            
        except Exception as e:
            logger.error(f"Failed to get user emails for analysis: {e}")
            return []
    
    def _format_enrichment_result(self, result: EnhancedEnrichmentResult) -> Dict:
        """
        Format enrichment result for application consumption
        """
        return {
            "email": result.email,
            "success": result.error is None,
            "method": "enhanced_multi_source_enrichment",
            "confidence": result.confidence_score,
            "data_sources": result.data_sources,
            "enrichment_timestamp": result.enrichment_timestamp.isoformat(),
            
            # Person data
            "person": {
                "name": result.person_data.get('name', ''),
                "title": result.person_data.get('title', ''),
                "phone": result.person_data.get('phone', ''),
                "mobile": result.person_data.get('mobile', ''),
                "seniority_level": result.person_data.get('seniority_level', ''),
                "expertise_areas": result.person_data.get('expertise_areas', []),
                "communication_style": result.person_data.get('communication_style', ''),
                "interests": result.person_data.get('interests', ''),
                "confidence_indicators": result.person_data.get('confidence_indicators', [])
            },
            
            # Company data
            "company": {
                "name": result.company_data.get('name', ''),
                "industry": result.company_data.get('industry', ''),
                "website": result.company_data.get('website', ''),
                "address": result.company_data.get('address', ''),
                "size_category": result.company_data.get('size_category', ''),
                "business_model": result.company_data.get('business_model', ''),
                "technology_maturity": result.company_data.get('technology_maturity', ''),
                "market_position": result.company_data.get('market_position', ''),
                "description": result.company_data.get('description', ''),
                "products": result.company_data.get('products', []),
                "culture": result.company_data.get('culture', '')
            },
            
            # Intelligence summary
            "intelligence_summary": {
                "total_data_sources": len(result.data_sources),
                "primary_source": result.data_sources[0] if result.data_sources else "none",
                "data_richness": self._calculate_data_richness(result),
                "reliability_score": self._calculate_reliability_score(result)
            },
            
            "error": result.error
        }
    
    def _create_empty_enrichment(self, email: str, error: str) -> Dict:
        """Create empty enrichment result for failed cases"""
        return {
            "email": email,
            "success": False,
            "method": "enhanced_multi_source_enrichment",
            "confidence": 0.0,
            "data_sources": [],
            "enrichment_timestamp": datetime.utcnow().isoformat(),
            
            "person": {
                "name": "",
                "title": "",
                "phone": "",
                "mobile": "",
                "seniority_level": "",
                "expertise_areas": [],
                "communication_style": "",
                "interests": "",
                "confidence_indicators": []
            },
            
            "company": {
                "name": "",
                "industry": "",
                "website": "",
                "address": "",
                "size_category": "",
                "business_model": "",
                "technology_maturity": "",
                "market_position": "",
                "description": "",
                "products": [],
                "culture": ""
            },
            
            "intelligence_summary": {
                "total_data_sources": 0,
                "primary_source": "none",
                "data_richness": 0.0,
                "reliability_score": 0.0
            },
            
            "error": error
        }
    
    def _calculate_data_richness(self, result: EnhancedEnrichmentResult) -> float:
        """Calculate how rich the extracted data is"""
        total_fields = 0
        filled_fields = 0
        
        # Count person fields
        person_fields = ['name', 'title', 'phone', 'seniority_level', 'expertise_areas', 'communication_style']
        for field in person_fields:
            total_fields += 1
            if result.person_data.get(field):
                filled_fields += 1
        
        # Count company fields
        company_fields = ['name', 'industry', 'size_category', 'business_model', 'description']
        for field in company_fields:
            total_fields += 1
            if result.company_data.get(field):
                filled_fields += 1
        
        return filled_fields / max(total_fields, 1)
    
    def _calculate_reliability_score(self, result: EnhancedEnrichmentResult) -> float:
        """Calculate how reliable the data sources are"""
        source_reliability = {
            'email_signatures': 0.9,  # Very reliable
            'email_content': 0.7,     # Good reliability
            'domain_intelligence': 0.6,  # Moderate reliability
            'web_scraping': 0.5,      # Variable reliability
            'claude_synthesis': 0.8   # Good processing reliability
        }
        
        if not result.data_sources:
            return 0.0
        
        total_reliability = sum(source_reliability.get(source, 0.3) for source in result.data_sources)
        return min(1.0, total_reliability / len(result.data_sources))
    
    def _format_stored_enrichment(self, stored_data: Dict) -> Dict:
        """Format previously stored enrichment data"""
        # This would format data that was previously stored in the database
        # For now, assume it's already in the correct format
        return stored_data
    
    async def _store_enrichment_result(self, result: EnhancedEnrichmentResult):
        """Store enrichment result in database"""
        try:
            db_manager = get_db_manager()
            
            # Format for storage
            storage_data = {
                'email': result.email,
                'confidence_score': result.confidence_score,
                'person_data': result.person_data,
                'company_data': result.company_data,
                'data_sources': result.data_sources,
                'enrichment_timestamp': result.enrichment_timestamp.isoformat(),
                'error': result.error
            }
            
            await db_manager.store_contact_enrichment(self.user_id, result.email, storage_data)
            
        except Exception as e:
            logger.error(f"Failed to store enrichment result for {result.email}: {e}")
    
    async def cleanup(self):
        """Clean up enrichment service resources"""
        if self.enricher:
            await self.enricher.cleanup()
        logger.info(f"Contact enrichment service cleaned up for user {self.user_id}")

    async def _generate_strategic_insights(self, contacts: List, emails: List, analysis_type: str = 'multidimensional') -> Dict:
        """
        Generate strategic insights from contacts and emails using Claude 4 Opus
        """
        try:
            if not self.enricher or not self.enricher.claude_client:
                return {"error": "Claude client not available"}
            
            # Prepare data for analysis
            contact_summary = []
            for contact in contacts[:20]:  # Analyze top 20 contacts
                metadata = json.loads(contact.get('metadata', '{}')) if contact.get('metadata') else {}
                contact_summary.append({
                    'email': contact.get('email'),
                    'name': contact.get('name'),
                    'trust_tier': contact.get('trust_tier'),
                    'frequency': contact.get('frequency'),
                    'domain': contact.get('domain'),
                    'enrichment_data': metadata.get('enrichment_data', {})
                })
            
            email_patterns = {}
            for email in emails[:100]:  # Analyze recent 100 emails
                try:
                    email_metadata = json.loads(email.get('metadata', '{}')) if email.get('metadata') else {}
                    sender = email_metadata.get('from', '')
                    if '@' in sender:
                        domain = sender.split('@')[1]
                        email_patterns[domain] = email_patterns.get(domain, 0) + 1
                except:
                    continue
            
            # Generate Claude 4 Opus analysis
            prompt = f"""
Analyze this professional network and communication patterns to generate strategic insights:

CONTACT ANALYSIS:
{json.dumps(contact_summary, indent=2)[:3000]}

EMAIL PATTERNS:
{json.dumps(email_patterns, indent=2)[:1000]}

ANALYSIS TYPE: {analysis_type}

Generate comprehensive strategic insights including:

{{
    "worldview": {{
        "core_philosophies": "Key business philosophies evident",
        "decision_making_patterns": "How decisions are approached",
        "value_systems": "What the user values professionally",
        "communication_style": "Professional communication patterns"
    }},
    "strategic_opportunities": [
        {{
            "opportunity": "Description of strategic opportunity",
            "priority": "high/medium/low",
            "reasoning": "Why this is important",
            "next_steps": "Recommended actions"
        }}
    ],
    "network_intelligence": {{
        "key_influencers": ["Most influential contacts"],
        "industry_coverage": ["Industries represented"],
        "geographic_reach": "Geographic distribution",
        "relationship_depth": "Quality of relationships"
    }},
    "growth_insights": {{
        "untapped_networks": "Potential new networks to explore",
        "strengthening_opportunities": "Relationships to deepen",
        "knowledge_gaps": "Areas needing more expertise",
        "market_positioning": "Current market position analysis"
    }},
    "predictive_analysis": {{
        "emerging_trends": ["Trends visible in network"],
        "future_opportunities": ["Upcoming opportunities"],
        "risk_factors": ["Potential risks to monitor"],
        "competitive_advantages": ["Current strengths to leverage"]
    }},
    "connections": [
        {{
            "type": "cross_domain_connection",
            "description": "How different areas connect",
            "strategic_value": "Why this connection matters"
        }}
    ]
}}

Provide deep, actionable insights that go beyond surface-level analysis.
"""

            working_model = await self.enricher._get_working_claude_model()
            response = await asyncio.to_thread(
                self.enricher.claude_client.messages.create,
                model=working_model,
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = self.enricher._parse_json_response(response.content[0].text)
            if result:
                logger.info(f"✅ Generated strategic insights using {working_model}")
                return result
            else:
                return {"error": "Failed to parse Claude response"}
                
        except Exception as e:
            logger.error(f"Strategic insights generation failed: {e}")
            return {"error": str(e)}


# Convenience functions for backward compatibility

async def enrich_contact(user_id: int, contact: Dict) -> Dict:
    """
    Enrich a single contact - main entry point for the application
    
    Args:
        user_id: User ID
        contact: Contact data with 'email' field
        
    Returns:
        Enriched contact data
    """
    service = ContactEnrichmentService(user_id)
    try:
        return await service.enrich_contact(contact)
    finally:
        await service.cleanup()

async def enrich_contacts_batch(user_id: int, contacts: List[Dict]) -> Dict[str, Dict]:
    """
    Enrich multiple contacts in batch
    
    Args:
        user_id: User ID
        contacts: List of contact dictionaries
        
    Returns:
        Dictionary mapping email to enrichment results
    """
    service = ContactEnrichmentService(user_id)
    try:
        return await service.enrich_contacts_batch(contacts)
    finally:
        await service.cleanup()

# Alias for backward compatibility with existing code
get_enhanced_contact_info = enrich_contact 