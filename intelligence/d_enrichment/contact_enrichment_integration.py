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
        NOW USES DOMAIN-BASED BATCH PROCESSING FOR MAXIMUM EFFICIENCY
        
        Args:
            contacts: List of contact dictionaries
            max_concurrent: Maximum number of concurrent enrichments (not used in domain-based approach)
            
        Returns:
            Dictionary mapping email to enrichment results
        """
        if not self._initialized:
            await self.initialize()
        
        if not contacts:
            return {}
        
        logger.info(f"🚀 Starting DOMAIN-BASED batch enrichment for {len(contacts)} contacts")
        
        # Get user emails for context analysis
        user_emails = []
        try:
            if hasattr(self.storage_manager, 'get_emails'):
                emails_data, _ = self.storage_manager.get_emails(self.user_id, limit=500)
                user_emails = emails_data
                logger.info(f"📧 Retrieved {len(user_emails)} user emails for context analysis")
        except Exception as e:
            logger.warning(f"Could not retrieve user emails: {e}")
        
        # Use the new EFFICIENT domain-based enrichment
        enrichment_results = await self.enricher.enrich_contacts_by_domain_batch(contacts, user_emails)
        
        # Convert results to the expected format
        results = {}
        for email, enrichment_result in enrichment_results.items():
            if enrichment_result.error:
                results[email] = {
                    'success': False,
                    'error': enrichment_result.error,
                    'confidence_score': 0.0,
                    'data_sources': []
                }
            else:
                results[email] = {
                    'success': True,
                    'confidence_score': enrichment_result.confidence_score,
                    'person_data': enrichment_result.person_data,
                    'company_data': enrichment_result.company_data,
                    'data_sources': enrichment_result.data_sources,
                    'enrichment_timestamp': enrichment_result.enrichment_timestamp.isoformat()
                }
        
        # Calculate and log efficiency stats
        successful = sum(1 for result in results.values() if result.get('success', False))
        failed = len(results) - successful
        success_rate = successful / len(results) if results else 0
        
        # Count unique domains to show efficiency gain
        domains = set()
        for contact in contacts:
            email = contact.get('email', '')
            if '@' in email:
                domains.add(email.split('@')[1])
        
        logger.info(f"✅ DOMAIN-BASED enrichment completed:")
        logger.info(f"   📊 {successful} successful, {failed} failed ({success_rate:.1%} success rate)")
        logger.info(f"   🏢 {len(domains)} unique domains processed")
        logger.info(f"   ⚡ Efficiency gain: {len(contacts)/len(domains):.1f}x faster than individual processing")
        
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
            
            # Person data - include ALL enriched data
            "person": result.person_data,
            
            # Company data - include ALL enriched data  
            "company": result.company_data,
            
            # Relationship intelligence - pass through from enricher
            "relationship_intelligence": result.relationship_intelligence,
            
            # Actionable insights - pass through from enricher
            "actionable_insights": result.actionable_insights,
            
            # Intelligence summary - use rich data if available, fallback to basic metrics
            "intelligence_summary": result.actionable_insights if result.actionable_insights else {
                "total_data_sources": len(result.data_sources),
                "primary_source": result.data_sources[0] if result.data_sources else "none",
                "data_richness": self._calculate_data_richness(result),
                "reliability_score": self._calculate_reliability_score(result),
                "note": "Limited public data available for comprehensive intelligence analysis"
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
            
            # Person data - empty
            "person": {},
            
            # Company data - empty
            "company": {},
            
            # Relationship intelligence - empty
            "relationship_intelligence": {},
            
            # Actionable insights - empty
            "actionable_insights": {},
            
            # Intelligence summary - basic metrics only
            "intelligence_summary": {
                "total_data_sources": 0,
                "primary_source": "none",
                "data_richness": 0.0,
                "reliability_score": 0.0,
                "note": f"Enrichment failed: {error}"
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