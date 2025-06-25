"""
Contact Enrichment Service
=========================
Enhanced service with advanced web intelligence and permanent database storage
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

from intelligence.d_enrichment.enhanced_enrichment import EnhancedContactEnricher
from intelligence.d_enrichment.advanced_web_intelligence import AdvancedWebIntelligence, CompanyIntelligence
from utils.logging import structured_logger as logger


class ContactEnrichmentService:
    """
    Enhanced contact enrichment service with database-backed permanent storage
    """
    
    def __init__(self, user_id: int, storage_manager=None):
        self.user_id = user_id
        self.basic_enricher = EnhancedContactEnricher(user_id)
        self.advanced_intelligence = AdvancedWebIntelligence(user_id)
        self.storage_manager = storage_manager  # For database access
        
        # In-memory cache for current session only
        self.domain_cache = {}
        self.cache_duration_hours = 24  # How long to consider DB data fresh
        
    async def initialize(self):
        """Initialize all enrichment components"""
        await self.basic_enricher.initialize()
        await self.advanced_intelligence.initialize()
        logger.info(f"📊 Contact Enrichment Service initialized for user {self.user_id}")
    
    async def enrich_contacts_batch(self, contacts: List[Dict], user_emails: List[Dict] = None) -> Dict:
        """
        Enhanced batch enrichment with database-backed domain intelligence storage
        """
        logger.info(f"🚀 Starting ADVANCED batch enrichment for {len(contacts)} contacts")
        
        # Group contacts by domain for efficient processing
        domain_groups = {}
        for contact in contacts:
            email = contact.get('email', '')
            if '@' in email:
                domain = email.split('@')[1]
                if domain not in domain_groups:
                    domain_groups[domain] = []
                domain_groups[domain].append(contact)
        
        logger.info(f"📊 Grouped into {len(domain_groups)} domains")
        
        # Process domains with database-backed intelligence
        enriched_results = {}
        
        for domain, domain_contacts in domain_groups.items():
            logger.info(f"🏢 Processing {len(domain_contacts)} contacts from {domain}")
            
            # Get advanced company intelligence (database-backed)
            company_intelligence = await self._get_domain_intelligence_from_db(domain)
            
            # Enrich each contact with domain context
            for contact in domain_contacts:
                try:
                    enriched_contact = await self._enrich_contact_with_intelligence(
                        contact, company_intelligence, user_emails
                    )
                    enriched_results[contact['email']] = enriched_contact
                    
                    # Store enrichment result in database
                    await self._store_enrichment_in_db(contact['email'], enriched_contact)
                    
                except Exception as e:
                    logger.error(f"Failed to enrich {contact.get('email')}: {e}")
                    # Fallback to basic enrichment
                    basic_result = await self.basic_enricher.enrich_contact(contact, user_emails)
                    enriched_results[contact['email']] = basic_result
        
        logger.info(f"✅ Advanced batch enrichment completed: {len(enriched_results)} contacts processed")
        
        return {
            'enriched_contacts': enriched_results,
            'total_processed': len(enriched_results),
            'domains_analyzed': len(domain_groups),
            'advanced_intelligence_used': True
        }
    
    async def _get_domain_intelligence_from_db(self, domain: str) -> Optional[CompanyIntelligence]:
        """
        Get comprehensive domain intelligence with database-backed storage
        """
        # Check in-memory cache first (for current session)
        if domain in self.domain_cache:
            cached = self.domain_cache[domain]
            cache_age = datetime.utcnow() - cached.last_updated
            if cache_age.total_seconds() < (self.cache_duration_hours * 3600):
                logger.info(f"📋 Using session cache for {domain}")
                return cached
        
        # Check database for existing domain intelligence
        cached_intelligence = await self._load_domain_intelligence_from_db(domain)
        if cached_intelligence:
            # Add to session cache
            self.domain_cache[domain] = cached_intelligence
            return cached_intelligence
        
        # Skip generic domains
        generic_domains = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'icloud.com', 'aol.com', 'comcast.net', 'verizon.net'
        ]
        
        if domain in generic_domains:
            return None
        
        # Get fresh intelligence and store in database
        try:
            logger.info(f"🔍 Gathering FRESH intelligence for {domain} (not in database)")
            intelligence = await self.advanced_intelligence.get_company_intelligence(domain)
            
            # Cache in memory and store in database
            self.domain_cache[domain] = intelligence
            await self._save_domain_intelligence_to_db(domain, intelligence)
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Failed to get intelligence for {domain}: {e}")
            return None
    
    async def _load_domain_intelligence_from_db(self, domain: str) -> Optional[CompanyIntelligence]:
        """Load domain intelligence from database"""
        if not self.storage_manager:
            return None
            
        try:
            # Look for any contact from this domain that has company intelligence
            contacts, _ = self.storage_manager.get_contacts(self.user_id, domain=domain, limit=1)
            
            if not contacts:
                return None
                
            contact = contacts[0]
            if not contact.get('metadata'):
                return None
                
            metadata = json.loads(contact['metadata']) if isinstance(contact['metadata'], str) else contact['metadata']
            enrichment_data = metadata.get('enrichment_data', {})
            company_data = enrichment_data.get('company_data', {})
            
            # Check if we have company intelligence and it's fresh
            if company_data.get('intelligence_updated'):
                intelligence_updated = datetime.fromisoformat(company_data['intelligence_updated'])
                age = datetime.utcnow() - intelligence_updated
                
                if age.total_seconds() < (self.cache_duration_hours * 3600):
                    # Reconstruct CompanyIntelligence from stored data
                    intelligence = CompanyIntelligence(
                        domain=domain,
                        name=company_data.get('name', ''),
                        description=company_data.get('description', ''),
                        industry=company_data.get('industry', ''),
                        technologies=company_data.get('technologies', []),
                        social_links=company_data.get('social_links', {}),
                        funding_info=company_data.get('funding_info', {}),
                        founded_year=company_data.get('founded_year'),
                        confidence_score=company_data.get('intelligence_score', 0.0),
                        data_sources=company_data.get('intelligence_sources', []),
                        last_updated=intelligence_updated
                    )
                    
                    logger.info(f"📋 Loaded domain intelligence for {domain} from database (age: {age})")
                    return intelligence
                else:
                    logger.info(f"🗑️ Stored intelligence for {domain} is stale (age: {age})")
                    
        except Exception as e:
            logger.warning(f"Failed to load domain intelligence for {domain} from database: {e}")
            
        return None
    
    async def _save_domain_intelligence_to_db(self, domain: str, intelligence: CompanyIntelligence):
        """Save domain intelligence by updating a contact from that domain"""
        if not self.storage_manager:
            return
            
        try:
            # Find a contact from this domain to attach the intelligence to
            contacts, _ = self.storage_manager.get_contacts(self.user_id, domain=domain, limit=1)
            
            if contacts:
                contact = contacts[0]
                email = contact['email']
                
                # For now, we'll store this via the existing enrichment update process
                # The domain intelligence will be saved when we store individual contact enrichments
                logger.info(f"💾 Will save domain intelligence for {domain} via contact enrichment updates")
                
        except Exception as e:
            logger.warning(f"Failed to save domain intelligence for {domain} to database: {e}")
    
    async def _store_enrichment_in_db(self, email: str, enrichment_result: Dict):
        """Store comprehensive enrichment result in database"""
        if not self.storage_manager:
            return
            
        try:
            # Create comprehensive enrichment metadata
            enrichment_data = {
                'enrichment_timestamp': datetime.utcnow().isoformat(),
                'confidence_score': getattr(enrichment_result, 'confidence_score', 0.0),
                'data_sources': getattr(enrichment_result, 'data_sources', []),
                
                # Enhanced person data with comprehensive professional intelligence
                'person_data': getattr(enrichment_result, 'person_data', {}),
                
                # Enhanced company data with business intelligence 
                'company_data': getattr(enrichment_result, 'company_data', {}),
                
                # NEW: Relationship intelligence
                'relationship_intelligence': getattr(enrichment_result, 'relationship_intelligence', {}),
                
                # NEW: Actionable insights for engagement
                'actionable_insights': getattr(enrichment_result, 'actionable_insights', {}),
                
                # Legacy fields for backward compatibility
                'title': getattr(enrichment_result, 'person_data', {}).get('current_title', ''),
                'company': getattr(enrichment_result, 'company_data', {}).get('name', ''),
                'industry': getattr(enrichment_result, 'company_data', {}).get('industry', ''),
                'seniority_level': getattr(enrichment_result, 'person_data', {}).get('seniority_level', ''),
            }
            
            # Store in contact metadata
            await self.storage_manager.update_contact_metadata(self.user_id, email, enrichment_data)
            logger.info(f"💾 Stored comprehensive enrichment data for {email}")
            
        except Exception as e:
            logger.error(f"Failed to store enrichment for {email}: {e}")
    
    async def _enrich_contact_with_intelligence(
        self, 
        contact: Dict, 
        company_intelligence: Optional[CompanyIntelligence],
        user_emails: List[Dict]
    ) -> Dict:
        """
        Enrich contact using both basic enrichment and advanced company intelligence
        """
        # Start with basic enrichment
        basic_result = await self.basic_enricher.enrich_contact(contact, user_emails)
        
        # If we have advanced company intelligence, enhance the result
        if company_intelligence and company_intelligence.confidence_score > 0.3:
            enhanced_result = self._merge_with_company_intelligence(basic_result, company_intelligence)
            
            logger.info(f"✨ Enhanced {contact['email']} with advanced intelligence (confidence: {company_intelligence.confidence_score:.2f})")
            
            return enhanced_result
        
        return basic_result
    
    def _merge_with_company_intelligence(
        self, 
        basic_result, 
        company_intelligence: CompanyIntelligence
    ) -> Dict:
        """
        Merge basic enrichment with advanced company intelligence
        """
        # Handle different result types (dict or EnhancedEnrichmentResult)
        if hasattr(basic_result, 'to_dict'):
            # It's an EnhancedEnrichmentResult object
            enhanced_result = basic_result.to_dict()
        elif hasattr(basic_result, '__dict__'):
            # It's an object with attributes
            enhanced_result = vars(basic_result).copy()
        elif isinstance(basic_result, dict):
            # It's already a dict
            enhanced_result = basic_result.copy()
        else:
            # Fallback - create new dict with basic data
            enhanced_result = {
                'confidence_score': 0.5,
                'data_sources': ['basic_enrichment'],
                'company_data': {}
            }
        
        # Ensure required keys exist
        if 'company_data' not in enhanced_result:
            enhanced_result['company_data'] = {}
        if 'data_sources' not in enhanced_result:
            enhanced_result['data_sources'] = ['basic_enrichment']
        if 'confidence_score' not in enhanced_result:
            enhanced_result['confidence_score'] = 0.5
        
        # Enhance company data with advanced intelligence
        company_data = enhanced_result.get('company_data', {})
        
        # Merge company information
        if company_intelligence.name and not company_data.get('name'):
            company_data['name'] = company_intelligence.name
        
        if company_intelligence.description and not company_data.get('description'):
            company_data['description'] = company_intelligence.description
        
        if company_intelligence.industry and not company_data.get('industry'):
            company_data['industry'] = company_intelligence.industry
        
        # Add new intelligence fields
        if company_intelligence.technologies:
            company_data['technologies'] = company_intelligence.technologies
        
        if company_intelligence.social_links:
            company_data['social_links'] = company_intelligence.social_links
        
        if company_intelligence.funding_info:
            company_data['funding_info'] = company_intelligence.funding_info
        
        if company_intelligence.founded_year:
            company_data['founded_year'] = company_intelligence.founded_year
        
        # Add intelligence metadata
        company_data['intelligence_score'] = company_intelligence.confidence_score
        company_data['intelligence_sources'] = company_intelligence.data_sources
        company_data['intelligence_updated'] = company_intelligence.last_updated.isoformat()
        
        # Update confidence score
        original_confidence = enhanced_result.get('confidence_score', 0.0)
        intelligence_boost = company_intelligence.confidence_score * 0.3  # 30% boost
        enhanced_result['confidence_score'] = min(original_confidence + intelligence_boost, 1.0)
        
        # Add data sources
        data_sources = enhanced_result.get('data_sources', [])
        data_sources.extend(['advanced_web_intelligence', 'multi_engine_search'])
        enhanced_result['data_sources'] = list(set(data_sources))  # Remove duplicates
        
        enhanced_result['company_data'] = company_data
        
        return enhanced_result
    
    async def get_domain_analysis(self, domain: str) -> Optional[Dict]:
        """
        Get standalone domain analysis for debugging/testing
        """
        intelligence = await self._get_domain_intelligence_from_db(domain)
        
        if intelligence:
            return {
                'domain': intelligence.domain,
                'name': intelligence.name,
                'description': intelligence.description,
                'industry': intelligence.industry,
                'technologies': intelligence.technologies,
                'social_links': intelligence.social_links,
                'funding_info': intelligence.funding_info,
                'founded_year': intelligence.founded_year,
                'confidence_score': intelligence.confidence_score,
                'data_sources': intelligence.data_sources,
                'last_updated': intelligence.last_updated.isoformat()
            }
        
        return None
    
    async def cleanup(self):
        """Clean up all resources"""
        await self.basic_enricher.cleanup()
        await self.advanced_intelligence.cleanup()
        logger.info("🧹 Contact Enrichment Service cleaned up") 