"""
Contact Enrichment Service
=========================
Enhanced service with advanced web intelligence and permanent database storage
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import gc
import psutil
from collections import defaultdict
import logging

from intelligence.d_enrichment.enhanced_enrichment import EnhancedContactEnricher
from intelligence.d_enrichment.advanced_web_intelligence import AdvancedWebIntelligence, CompanyIntelligence
from utils.logging import structured_logger as logger

logger = logging.getLogger(__name__)

class ContactEnrichmentService:
    """
    Enhanced contact enrichment service with database-backed permanent storage
    """
    
    def __init__(self, user_id: int, storage_manager=None):
        self.user_id = user_id
        self.basic_enricher = EnhancedContactEnricher(user_id, storage_manager)
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
    
    def _get_memory_usage(self):
        """Get current memory usage percentage"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            # Heroku limit is 512MB
            memory_percent = (memory_mb / 512) * 100
            return memory_percent
        except:
            return 0

    def _get_dynamic_batch_size(self, memory_percent: float) -> int:
        """Get dynamic batch size based on memory usage"""
        if memory_percent > 75:
            return 5  # Very small batches when memory is high
        elif memory_percent > 50:
            return 10  # Medium batches
        elif memory_percent > 25:
            return 15  # Larger batches
        else:
            return 20  # Maximum batch size when memory is low
    
    def _cleanup_memory(self):
        """Aggressive memory cleanup"""
        gc.collect()

    async def enrich_contacts_batch(self, contacts: List[Dict], user_emails: List[Dict] = None) -> Dict:
        """
        Enrich multiple contacts with memory-aware batch processing
        """
        try:
            total_contacts = len(contacts)
            logger.info(f"🚀 Starting ADVANCED batch enrichment for {total_contacts} contacts")
            
            # Initial memory check
            initial_memory = self._get_memory_usage()
            logger.info(f"📊 Initial memory usage: {initial_memory:.1f}%")
            
            # Group contacts by domain for efficient processing
            domain_groups = defaultdict(list)
            for contact in contacts:
                domain = contact.get('email', '').split('@')[1] if '@' in contact.get('email', '') else 'unknown'
                domain_groups[domain].append(contact)
            
            # Process in memory-aware batches
            batch_size = self._get_dynamic_batch_size(initial_memory)
            total_batches = (total_contacts + batch_size - 1) // batch_size
            
            enriched_contacts = []
            failed_contacts = []
            successful_count = 0
            
            batch_num = 0
            processed_contacts = 0
            
            for domain, domain_contacts in domain_groups.items():
                # Check memory before processing each domain
                current_memory = self._get_memory_usage()
                
                # Skip processing if memory is too high
                if current_memory > 90:
                    logger.warning(f"🚨 Memory usage critical ({current_memory:.1f}%), stopping enrichment")
                    break
                
                # Process domain contacts in batches
                for i in range(0, len(domain_contacts), batch_size):
                    batch_num += 1
                    batch_contacts = domain_contacts[i:i + batch_size]
                    current_memory = self._get_memory_usage()
                    
                    logger.info(f"🔄 Processing batch {batch_num}/{total_batches}: {len(batch_contacts)} contacts (Memory: {current_memory:.1f}%)")
                    logger.info(f"📊 Batch {batch_num} grouped into 1 domains")
                    
                    # Adjust batch size dynamically based on current memory
                    if current_memory > 80:
                        batch_size = 5  # Reduce batch size if memory is high
                        logger.warning(f"⚠️ Reducing batch size to {batch_size} due to high memory usage")
                    
                    logger.info(f"🏢 Processing {len(batch_contacts)} contacts from {domain}")
                    
                    # Process domain intelligence once per domain
                    domain_intelligence = None
                    if domain != 'unknown' and not self._is_generic_domain(domain):
                        domain_intelligence = await self._get_domain_intelligence_from_db(domain)
                    
                    # Process each contact in the batch
                    for contact in batch_contacts:
                        try:
                            # Check memory before each contact
                            contact_memory = self._get_memory_usage()
                            if contact_memory > 85:
                                logger.warning(f"⚠️ Skipping contact due to high memory usage: {contact_memory:.1f}%")
                                failed_contacts.append({
                                    'contact': contact,
                                    'error': f'Memory limit exceeded: {contact_memory:.1f}%'
                                })
                                continue
                            
                            # Enrich the contact
                            enriched = await self._enrich_contact_with_intelligence(
                                contact, domain_intelligence, user_emails
                            )
                            
                            if enriched:
                                enriched_contacts.append(enriched)
                                successful_count += 1
                            else:
                                failed_contacts.append({
                                    'contact': contact,
                                    'error': 'Enrichment returned empty result'
                                })
                            
                            processed_contacts += 1
                            
                        except Exception as e:
                            logger.error(f"Failed to enrich contact {contact.get('email', 'unknown')}: {e}")
                            failed_contacts.append({
                                'contact': contact,
                                'error': str(e)
                            })
                    
                    # Memory cleanup after each batch
                    self._cleanup_memory()
                    
                    # Check if we should continue
                    if self._get_memory_usage() > 85:
                        logger.warning("🚨 Memory usage too high, stopping batch processing")
                        break
            
            # Final memory cleanup
            self._cleanup_memory()
            final_memory = self._get_memory_usage()
            
            # Calculate success rate
            success_rate = (successful_count / total_contacts) * 100 if total_contacts > 0 else 0
            
            result = {
                'enriched_contacts': enriched_contacts,
                'failed_contacts': failed_contacts,
                'total_processed': processed_contacts,
                'successful_count': successful_count,
                'failed_count': len(failed_contacts),
                'success_rate': success_rate,
                'memory_usage': {
                    'initial': initial_memory,
                    'final': final_memory,
                    'peak': max(initial_memory, final_memory)
                },
                'processing_stats': {
                    'total_batches': batch_num,
                    'final_batch_size': batch_size,
                    'domains_processed': len(domain_groups)
                }
            }
            
            logger.info(f"✅ Batch enrichment completed: {successful_count}/{total_contacts} success ({success_rate:.1f}%)")
            logger.info(f"📊 Memory usage: {initial_memory:.1f}% → {final_memory:.1f}%")
            
            return result
            
        except Exception as e:
            logger.error(f"Batch enrichment failed: {e}")
            return {
                'enriched_contacts': [],
                'failed_contacts': [],
                'total_processed': 0,
                'successful_count': 0,
                'failed_count': len(contacts),
                'success_rate': 0,
                'error': str(e)
            }

    def _is_generic_domain(self, domain: str) -> bool:
        """Check if domain is a generic email provider"""
        generic_domains = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 
            'aol.com', 'icloud.com', 'protonmail.com', 'mail.com'
        }
        return domain.lower() in generic_domains
    
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
            
            # Store in contact metadata (this is a synchronous call, not async)
            success = self.storage_manager.postgres.update_contact_metadata(self.user_id, email, {'enrichment_data': enrichment_data})
            if success:
                logger.info(f"💾 Stored comprehensive enrichment data for {email}")
            else:
                logger.warning(f"⚠️ Failed to store enrichment data for {email}")
            
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