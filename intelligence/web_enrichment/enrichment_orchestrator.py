# intelligence/web_enrichment/enrichment_orchestrator.py
"""
Contact Enrichment Orchestrator
=============================
Coordinates contact enrichment activities across multiple web sources.
Ensures proper multi-tenant isolation for user data.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from utils.logging import structured_logger as logger
from storage.storage_manager import get_storage_manager
from intelligence.web_enrichment.base_scraper import BaseScraper, EnrichmentResult
from intelligence.web_enrichment.linkedin_scraper import LinkedInScraper
from intelligence.web_enrichment.twitter_scraper import TwitterScraper

class EnrichmentOrchestrator:
    """
    Orchestrates the enrichment of contact data from multiple sources
    with multi-tenant isolation for user privacy
    """
    
    def __init__(self, user_id: int):
        """
        Initialize orchestrator for a specific user
        
        Args:
            user_id: User ID for multi-tenant isolation
        """
        self.user_id = user_id
        self.storage_manager = None
        self.scrapers = {}
        
    async def initialize(self) -> bool:
        """
        Initialize resources and connections
        
        Returns:
            True if initialization was successful
        """
        try:
            # Get storage manager
            self.storage_manager = await get_storage_manager()
            
            # Initialize scrapers
            self.scrapers = {
                'linkedin': LinkedInScraper(self.user_id),
                'twitter': TwitterScraper(self.user_id)
            }
            
            # Initialize each scraper
            for name, scraper in self.scrapers.items():
                await scraper.initialize()
                
            return True
            
        except Exception as e:
            logger.error("Failed to initialize enrichment orchestrator", 
                        user_id=self.user_id, error=str(e))
            return False
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        for name, scraper in self.scrapers.items():
            try:
                await scraper.cleanup()
            except Exception as e:
                logger.error(f"Error during {name} scraper cleanup", 
                            user_id=self.user_id, error=str(e))
    
    async def enrich_contact(self, contact: Dict, sources: List[str] = None) -> Dict[str, EnrichmentResult]:
        """
        Enrich a single contact from specified sources
        
        Args:
            contact: Contact dictionary with at least 'email' field
            sources: List of sources to use (defaults to all)
            
        Returns:
            Dictionary of enrichment results by source
        """
        if not contact.get('email'):
            logger.error("Cannot enrich contact without email", user_id=self.user_id)
            return {}
        
        # Use all sources if not specified
        if not sources:
            sources = list(self.scrapers.keys())
            
        results = {}
        
        # Run each scraper
        for source in sources:
            if source not in self.scrapers:
                logger.warning(f"Unknown enrichment source: {source}", user_id=self.user_id)
                continue
                
            scraper = self.scrapers[source]
            try:
                result = await scraper.enrich_contact(contact)
                results[source] = result
                
                # Short delay between sources
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error enriching contact from {source}", 
                           user_id=self.user_id, email=contact.get('email'), error=str(e))
                
        return results
    
    async def enrich_contacts(
        self, 
        contacts: List[Dict], 
        sources: List[str] = None,
        concurrency: int = 2
    ) -> Dict[str, Dict[str, EnrichmentResult]]:
        """
        Enrich multiple contacts with rate limiting
        
        Args:
            contacts: List of contact dictionaries
            sources: List of sources to use (defaults to all)
            concurrency: Maximum number of concurrent enrichment operations
            
        Returns:
            Dictionary of enrichment results by contact email and source
        """
        # Initialize if not already done
        if not self.scrapers:
            success = await self.initialize()
            if not success:
                return {}
                
        # Validate contacts
        valid_contacts = [c for c in contacts if c.get('email')]
        
        if not valid_contacts:
            logger.warning("No valid contacts for enrichment", user_id=self.user_id)
            return {}
        
        # Process in batches for rate limiting
        results = {}
        semaphore = asyncio.Semaphore(concurrency)
        
        async def process_contact(contact: Dict) -> None:
            """Process a single contact with semaphore"""
            async with semaphore:
                email = contact.get('email')
                try:
                    contact_results = await self.enrich_contact(contact, sources)
                    results[email] = contact_results
                    
                    # Store in database if we have successful results
                    await self._store_enrichment_results(contact, contact_results)
                    
                    # Small delay to be nice to APIs
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Failed to enrich contact", 
                               email=email, user_id=self.user_id, error=str(e))
        
        # Create tasks for all contacts
        tasks = [process_contact(contact) for contact in valid_contacts]
        
        # Run with progress tracking
        completed = 0
        total = len(tasks)
        
        for future in asyncio.as_completed(tasks):
            try:
                await future
                completed += 1
                
                # Log progress
                if completed % max(1, total // 10) == 0 or completed == total:
                    logger.info(f"Enrichment progress: {completed}/{total} contacts", 
                               user_id=self.user_id)
                    
            except Exception as e:
                logger.error("Error in contact enrichment task", 
                           user_id=self.user_id, error=str(e))
        
        return results
    
    async def _store_enrichment_results(
        self, 
        contact: Dict, 
        results: Dict[str, EnrichmentResult]
    ) -> None:
        """
        Store enrichment results in database
        
        Args:
            contact: Original contact data
            results: Enrichment results by source
        """
        if not results:
            return
            
        try:
            # Process only successful results
            data_to_store = {
                'enriched_at': datetime.utcnow().isoformat(),
                'email': contact.get('email')
            }
            
            # Merge data from each successful source
            for source, result in results.items():
                if result and result.successful:
                    data_to_store[source] = result.data
            
            # Only store if we have enrichment data
            if len(data_to_store) > 2:  # More than just timestamp and email
                # Calculate overall enrichment quality
                sources_count = sum(1 for _, r in results.items() if r and r.successful)
                enrichment_quality = min(1.0, sources_count / max(1, len(results)))
                
                data_to_store['enrichment_quality'] = enrichment_quality
                
                # Store in database
                await self.storage_manager.store_contact_enrichment(
                    self.user_id, 
                    contact.get('email'), 
                    data_to_store
                )
                
        except Exception as e:
            logger.error(f"Failed to store enrichment results", 
                       email=contact.get('email'), user_id=self.user_id, error=str(e))

# Convenience function for external calls
async def enrich_user_contacts(
    user_id: int, 
    contacts: List[Dict],
    sources: List[str] = None
) -> Dict:
    """
    Enrich contacts for a specific user
    
    Args:
        user_id: User ID for multi-tenant isolation
        contacts: List of contact dictionaries
        sources: List of sources to use
        
    Returns:
        Enrichment results
    """
    orchestrator = EnrichmentOrchestrator(user_id)
    try:
        await orchestrator.initialize()
        results = await orchestrator.enrich_contacts(contacts, sources)
        
        # Count success and failures
        success_count = sum(1 for email, res in results.items() 
                           for source, r in res.items() 
                           if r and r.successful)
        
        total_attempts = sum(1 for email, res in results.items() 
                            for source, _ in res.items())
        
        return {
            'status': 'completed',
            'success_rate': success_count / max(1, total_attempts) if total_attempts else 0,
            'contacts_processed': len(contacts),
            'successful_enrichments': success_count,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    finally:
        await orchestrator.cleanup()
