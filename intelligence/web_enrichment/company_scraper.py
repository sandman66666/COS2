# intelligence/web_enrichment/company_scraper.py
"""
Company Intelligence Scraper
==========================
Enriches company data from public web sources.
Ensures proper multi-tenant isolation for user data.
"""

import re
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from utils.logging import structured_logger as logger
from intelligence.web_enrichment.base_scraper import BaseScraper, EnrichmentResult

class CompanyScraper(BaseScraper):
    """
    Company intelligence scraper for organizational data enrichment
    
    Extracts company information from publicly available sources
    to provide context on organizations where contacts work.
    """
    
    def __init__(self, user_id: int = None, rate_limit: float = 3.0):
        """
        Initialize company scraper
        
        Args:
            user_id: User ID for multi-tenant isolation
            rate_limit: Seconds between requests to avoid rate limiting
        """
        super().__init__(user_id, rate_limit)
        self.source = "company"
    
    async def enrich_contact(self, contact: Dict) -> EnrichmentResult:
        """
        Enrich contact with company data
        
        Args:
            contact: Contact information dictionary with at minimum:
                    - email: Email address
                    - company: (optional) Company name or None
                    
        Returns:
            EnrichmentResult with company data
        """
        if not contact.get("email"):
            return self._create_error_result(
                email=contact.get("email", "unknown"),
                source=self.source,
                error="Email is required for company enrichment"
            )
            
        try:
            # Initialize if needed
            if not self._initialized:
                success = await self.initialize()
                if not success:
                    return self._create_error_result(
                        email=contact["email"],
                        source=self.source,
                        error="Failed to initialize company scraper"
                    )
            
            # Extract email domain for company matching
            email = contact["email"]
            domain = email.split("@")[-1] if "@" in email else None
            
            # Try getting company name from contact data or LinkedIn enrichment
            company_name = (
                contact.get("company") or 
                contact.get("linkedin", {}).get("company") or 
                None
            )
            
            # Skip known generic domains
            if domain and self._is_generic_domain(domain):
                if not company_name:
                    return self._create_error_result(
                        email=email,
                        source=self.source,
                        error="Generic email domain with no company name provided"
                    )
            
            # If we have a domain but no company name, derive company from domain
            if domain and not company_name:
                company_name = self._domain_to_company_name(domain)
            
            if not company_name:
                return self._create_error_result(
                    email=email,
                    source=self.source,
                    error="Could not determine company name"
                )
            
            # Get company data
            company_data = await self._get_company_data(company_name, domain)
            
            if not company_data:
                return self._create_error_result(
                    email=email,
                    source=self.source,
                    error=f"No company data found for {company_name}"
                )
            
            # Format the data
            enriched_data = self._format_company_data(company_data)
            
            # Calculate confidence score based on data quality
            confidence = self._calculate_confidence(company_data, domain)
            
            return self._create_success_result(
                email=email,
                source=self.source,
                data=enriched_data,
                raw_data=company_data,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(
                "Company enrichment error",
                error=str(e),
                email=contact.get("email"),
                user_id=self.user_id
            )
            return self._create_error_result(
                email=contact["email"],
                source=self.source,
                error=f"Company enrichment failed: {str(e)}"
            )
    
    def _is_generic_domain(self, domain: str) -> bool:
        """
        Check if domain is a generic email provider
        
        Args:
            domain: Email domain
            
        Returns:
            True if generic provider
        """
        generic_domains = {
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
            "aol.com", "icloud.com", "mail.com", "protonmail.com",
            "zoho.com", "yandex.com", "gmx.com"
        }
        return domain.lower() in generic_domains
    
    def _domain_to_company_name(self, domain: str) -> str:
        """
        Convert domain to likely company name
        
        Args:
            domain: Email domain
            
        Returns:
            Company name derived from domain
        """
        # Strip TLD and common subdomains
        parts = domain.lower().split(".")
        
        # Remove TLD (.com, .org, etc)
        if len(parts) > 1:
            parts = parts[:-1]
            
        # Remove common subdomains
        if len(parts) > 1 and parts[0] in ["mail", "email", "corp", "www", "info"]:
            parts = parts[1:]
            
        # Join remaining parts and capitalize
        company_name = " ".join(parts).title()
        
        # Clean up
        company_name = re.sub(r'[-_]', ' ', company_name)
        
        return company_name
    
    async def _get_company_data(self, company_name: str, domain: str = None) -> Optional[Dict]:
        """
        Get company data from multiple sources
        
        Args:
            company_name: Company name
            domain: Company domain if known
            
        Returns:
            Company data or None if not found
        """
        # Try searching via structured search engines first
        company_data = await self._search_company_via_api(company_name, domain)
        
        # If that fails, fall back to web search
        if not company_data:
            company_data = await self._search_company_via_google(company_name, domain)
        
        return company_data
    
    async def _search_company_via_api(self, company_name: str, domain: str = None) -> Optional[Dict]:
        """
        Search for company using APIs
        
        Args:
            company_name: Company name
            domain: Company domain if known
            
        Returns:
            Company data dictionary if found
        """
        try:
            # Clearbit-like company API endpoint (placeholder)
            # In a real implementation, you would use a proper API service
            
            # Since we don't have actual API access, we'll simulate it
            # with a Google Knowledge Panel extraction instead
            
            search_query = f"{company_name} company"
            if domain:
                search_query += f" {domain}"
            
            encoded_query = search_query.replace(" ", "%20")
            
            # Use a page to search
            page = await self._new_page()
            
            try:
                # Search Google
                await page.goto(
                    f"https://www.google.com/search?q={encoded_query}",
                    wait_until="networkidle"
                )
                
                # Extract knowledge panel data
                company_data = await page.evaluate("""
                    () => {
                        // Helper to safely extract text
                        function safeText(selector) {
                            const el = document.querySelector(selector);
                            return el ? el.innerText.trim() : '';
                        }
                        
                        // Check if knowledge panel exists
                        const panel = document.querySelector('div[data-attrid], div.kp-header');
                        if (!panel) return null;
                        
                        // Extract company information
                        const name = safeText('h2[data-attrid="title"]') || safeText('div.kp-header h2');
                        
                        // Description
                        const description = safeText('[data-attrid="description"] > span, div[data-md]');
                        
                        // Type/industry/category
                        const type = safeText('[data-attrid*="category"] > span');
                        
                        // Founded data
                        const foundingDate = safeText('[data-attrid*="found"] > span');
                        
                        // Headquarters
                        const headquarters = safeText('[data-attrid*="locat"] > span');
                        
                        // Check for other common data attributes
                        const attributes = {};
                        document.querySelectorAll('[data-attrid]:not([data-attrid*="description"]):not([data-attrid="title"])').forEach(el => {
                            const key = el.getAttribute('data-attrid').split(':').pop();
                            const value = el.innerText.trim();
                            if (key && value) attributes[key] = value;
                        });
                        
                        // Website link
                        const websiteLink = document.querySelector('a[href^="https://"][data-attrid*="website"]');
                        const website = websiteLink ? websiteLink.href : '';
                        
                        return {
                            name,
                            description,
                            type,
                            founding_date: foundingDate,
                            headquarters,
                            website,
                            attributes,
                            source: 'google_knowledge_panel'
                        };
                    }
                """)
                
                return company_data
            
            finally:
                await page.close()
                
        except Exception as e:
            logger.error(
                f"Error in company API search", 
                error=str(e), 
                company=company_name,
                user_id=self.user_id
            )
            return None
    
    async def _search_company_via_google(self, company_name: str, domain: str = None) -> Optional[Dict]:
        """
        Search for company info via Google
        
        Args:
            company_name: Company name
            domain: Company domain if known
            
        Returns:
            Company data dictionary
        """
        try:
            # Build search query
            search_query = f"{company_name}"
            if domain:
                search_query += f" {domain}"
                
            search_query += " company about"
            
            # Encode query
            encoded_query = search_query.replace(" ", "+")
            
            # Get page
            page = await self._new_page()
            
            try:
                # Go to search results
                await page.goto(f"https://www.google.com/search?q={encoded_query}", wait_until="networkidle")
                
                # Extract snippet information
                company_data = await page.evaluate("""
                    () => {
                        const results = document.querySelectorAll('.g');
                        if (!results.length) return null;
                        
                        // Look for official site
                        let officialSite = null;
                        let description = '';
                        let headline = '';
                        
                        // Process search results
                        for (const result of results) {
                            const link = result.querySelector('a');
                            const url = link ? link.href : '';
                            const title = result.querySelector('h3') ? 
                                result.querySelector('h3').innerText : '';
                            
                            // Extract snippet text
                            const snippetEl = result.querySelector('div[style] > span');
                            const snippet = snippetEl ? snippetEl.innerText : '';
                            
                            // If this looks like an official site
                            if (url && title && (
                                title.toLowerCase().includes('official') ||
                                title.toLowerCase().includes('about us') ||
                                title.toLowerCase().includes('company')
                            )) {
                                officialSite = url;
                                description = snippet;
                                headline = title;
                                break;
                            }
                            
                            // Otherwise just use the first result
                            if (!officialSite && url) {
                                officialSite = url;
                                description = snippet;
                                headline = title;
                            }
                        }
                        
                        // Extract industry and size info if present
                        const industryMatch = description.match(/(?:industry|sector):\\s*([^\\.|,]+)/i);
                        const sizeMatch = description.match(/(?:employees|size|people):\\s*([^\\.|,]+)/i);
                        
                        return {
                            name: headline.replace(/- .+$/, '').trim(),
                            description,
                            website: officialSite,
                            industry: industryMatch ? industryMatch[1].trim() : '',
                            size: sizeMatch ? sizeMatch[1].trim() : '',
                            source: 'google_search'
                        };
                    }
                """)
                
                return company_data
                
            finally:
                await page.close()
                
        except Exception as e:
            logger.error(
                f"Error in company Google search", 
                error=str(e),
                company=company_name,
                user_id=self.user_id
            )
            return None
    
    def _calculate_confidence(self, data: Dict, domain: str = None) -> float:
        """
        Calculate confidence score for company data
        
        Args:
            data: Company data
            domain: Domain name if available
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence
        confidence = 0.5
        
        # If we have no data
        if not data:
            return 0.0
        
        # Name match with domain increases confidence
        if domain and data.get("website"):
            website = data["website"].lower()
            if domain.lower() in website:
                confidence += 0.3
                
        # Comprehensive data increases confidence
        if data.get("description") and len(data.get("description", "")) > 50:
            confidence += 0.1
            
        # More fields means higher confidence
        fields_count = sum(1 for k, v in data.items() if v and k != "source")
        confidence += min(0.2, fields_count * 0.02)
        
        # Cap at 1.0
        return min(1.0, confidence)
    
    def _format_company_data(self, data: Dict) -> Dict:
        """
        Format company data consistently
        
        Args:
            data: Raw company data
            
        Returns:
            Formatted company data
        """
        return {
            "name": data.get("name", ""),
            "description": data.get("description", ""),
            "website": data.get("website", ""),
            "industry": data.get("industry", data.get("type", "")),
            "founded": data.get("founding_date", ""),
            "headquarters": data.get("headquarters", ""),
            "size": data.get("size", ""),
            "data_source": data.get("source", "web")
        }
