# intelligence/web_enrichment/linkedin_scraper.py
"""
LinkedIn Web Scraper
==================
Enriches contact data with LinkedIn profile information.
Uses a privacy-conscious approach for multi-tenant systems.
"""

import re
import asyncio
import time
from typing import Dict, List, Optional, Any

from playwright.async_api import Page
from utils.logging import structured_logger as logger
from intelligence.d_enrichment.web_enrichment.base_scraper import BaseScraper, EnrichmentResult

class LinkedInScraper(BaseScraper):
    """
    LinkedIn web scraper for contact enrichment
    
    Extracts professional information about contacts from LinkedIn 
    while respecting website terms and user privacy.
    """
    
    def __init__(self, user_id: int = None, rate_limit: float = 3.0):
        """
        Initialize LinkedIn scraper
        
        Args:
            user_id: User ID for multi-tenant isolation
            rate_limit: Seconds between requests to avoid rate limiting
        """
        super().__init__(user_id, rate_limit)
        self.source = "linkedin"
    
    async def enrich_contact(self, contact: Dict) -> EnrichmentResult:
        """
        Enrich contact with LinkedIn data
        
        Args:
            contact: Contact information dictionary with at minimum:
                    - email: Email address
                    - name: (optional) Full name
                    - company: (optional) Company name
                    
        Returns:
            EnrichmentResult with LinkedIn profile data
        """
        if not contact.get("email"):
            return self._create_error_result(
                email=contact.get("email", "unknown"),
                source=self.source,
                error="Email is required for LinkedIn enrichment"
            )
            
        try:
            # Initialize if needed
            if not self._initialized:
                success = await self.initialize()
                if not success:
                    return self._create_error_result(
                        email=contact["email"],
                        source=self.source,
                        error="Failed to initialize LinkedIn scraper"
                    )
            
            # Build search query from available information
            name = contact.get("name", "")
            company = contact.get("company", "")
            domain = contact.get("domain", "")
            
            if not name:
                # Try to extract name from email if not provided
                email_parts = contact["email"].split("@")[0].split(".")
                if len(email_parts) >= 2:
                    name = " ".join([p.capitalize() for p in email_parts])
            
            if not company and domain and domain != "gmail.com":
                # Use domain as company name if available
                company = domain.split(".")[0].capitalize()
            
            # If we still don't have enough info, return error
            if not name:
                return self._create_error_result(
                    email=contact["email"],
                    source=self.source,
                    error="Insufficient information to search LinkedIn"
                )
                
            # Search for LinkedIn profile
            profile_data = await self._search_linkedin(name, company)
            
            if not profile_data:
                return self._create_error_result(
                    email=contact["email"], 
                    source=self.source,
                    error="No LinkedIn profile found"
                )
            
            # If we have a profile URL, get more details
            if profile_data.get("profile_url"):
                detailed_data = await self._extract_profile_details(profile_data["profile_url"])
                profile_data.update(detailed_data)
            
            # Calculate confidence score based on name match
            confidence = self._calculate_confidence_score(name, profile_data.get("name", ""))
            
            # Format the enriched data
            enriched_data = self._format_linkedin_data(profile_data)
            
            return self._create_success_result(
                email=contact["email"],
                source=self.source,
                data=enriched_data,
                raw_data=profile_data,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(
                "LinkedIn enrichment error",
                error=str(e),
                email=contact.get("email"),
                user_id=self.user_id
            )
            return self._create_error_result(
                email=contact["email"],
                source=self.source,
                error=f"LinkedIn enrichment failed: {str(e)}"
            )
    
    async def _search_linkedin(self, name: str, company: str = "") -> Optional[Dict]:
        """
        Search LinkedIn for a person
        
        Args:
            name: Person's name
            company: Optional company name for better targeting
            
        Returns:
            Dictionary with basic profile data or None if not found
        """
        try:
            # Create search query
            search_query = f"{name}"
            if company:
                search_query += f" {company}"
                
            # URL encode the query
            encoded_query = search_query.replace(" ", "%20")
                
            # Get new browser page with rate limiting
            page = await self._new_page()
            
            try:
                # Navigate to LinkedIn search
                search_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded_query}"
                await page.goto(search_url, wait_until="networkidle")
                
                # Check if we're on login page (LinkedIn blocks unauthenticated searches)
                is_login_page = await page.evaluate("""
                    () => {
                        return Boolean(document.querySelector('form[data-id="sign-in-form"]'));
                    }
                """)
                
                if is_login_page:
                    logger.warning(
                        "LinkedIn requires authentication for search", 
                        user_id=self.user_id
                    )
                    
                    # Fallback to Google search for LinkedIn profile
                    await page.goto(
                        f"https://www.google.com/search?q={encoded_query}+linkedin", 
                        wait_until="networkidle"
                    )
                    
                    # Extract LinkedIn profile from Google search results
                    profile_data = await page.evaluate("""
                        () => {
                            const linkedInResults = Array.from(document.querySelectorAll('a[href*="linkedin.com/in/"]'));
                            if (linkedInResults.length === 0) return null;
                            
                            const firstResult = linkedInResults[0];
                            const url = firstResult.href;
                            const title = firstResult.querySelector('h3') 
                                ? firstResult.querySelector('h3').innerText 
                                : '';
                            const snippet = firstResult.parentElement.querySelector('div[style] div[style]') 
                                ? firstResult.parentElement.querySelector('div[style] div[style]').innerText
                                : '';
                                
                            return {
                                name: title.replace(' | LinkedIn', '').replace(' - LinkedIn', ''),
                                snippet: snippet,
                                profile_url: url
                            };
                        }
                    """)
                    
                    # Extract company and title from snippet
                    if profile_data and profile_data.get("snippet"):
                        snippet = profile_data.get("snippet", "")
                        
                        # Try to extract company and title from snippet
                        profile_data["position"] = ""
                        profile_data["company"] = ""
                        
                        position_match = re.search(r'(?:is|as|at)\s+([^\.]+?)(?:at|in|\.|\-)', snippet)
                        if position_match:
                            profile_data["position"] = position_match.group(1).strip()
                            
                        company_match = re.search(r'(?:at|@)\s+([^\.]+?)(?:in|\.|\-)', snippet)
                        if company_match:
                            profile_data["company"] = company_match.group(1).strip()
                    
                    return profile_data
                else:
                    # Extract data from LinkedIn search results
                    profile_data = await page.evaluate("""
                        () => {
                            const results = document.querySelectorAll('.reusable-search__result-container');
                            if (results.length === 0) return null;
                            
                            const firstResult = results[0];
                            const nameElement = firstResult.querySelector('.entity-result__title-text a');
                            const subtitleElement = firstResult.querySelector('.entity-result__primary-subtitle');
                            const locationElement = firstResult.querySelector('.entity-result__secondary-subtitle');
                            
                            if (!nameElement) return null;
                            
                            const profileUrl = nameElement.href;
                            const name = nameElement.innerText.trim();
                            const position = subtitleElement ? subtitleElement.innerText.trim() : '';
                            const location = locationElement ? locationElement.innerText.trim() : '';
                            
                            return {
                                name,
                                position,
                                location,
                                profile_url: profileUrl
                            };
                        }
                    """)
                    
                    return profile_data
            
            finally:
                # Always close the page to avoid memory leaks
                await page.close()
        
        except Exception as e:
            logger.error(
                "LinkedIn search error",
                error=str(e),
                name=name,
                company=company,
                user_id=self.user_id
            )
            return None
    
    async def _extract_profile_details(self, profile_url: str) -> Dict:
        """
        Extract more details from LinkedIn profile page
        
        Args:
            profile_url: URL to LinkedIn profile
            
        Returns:
            Dictionary with detailed profile data
        """
        try:
            # Get new page
            page = await self._new_page()
            
            try:
                # Navigate to profile
                await page.goto(profile_url, wait_until="networkidle")
                
                # Check if we hit a login wall
                is_login_wall = await page.evaluate("""
                    () => {
                        return Boolean(document.querySelector('.login__form'));
                    }
                """)
                
                if is_login_wall:
                    # We can only get limited info from preview
                    profile_preview = await page.evaluate("""
                        () => {
                            const name = document.querySelector('h1')?.innerText || '';
                            const headline = document.querySelector('h2')?.innerText || '';
                            
                            return {
                                full_name: name,
                                headline: headline,
                                limited_access: true
                            };
                        }
                    """)
                    
                    return profile_preview
                else:
                    # Extract more detailed information
                    detailed_data = await page.evaluate("""
                        () => {
                            // Helper to safely extract text
                            function safeText(selector) {
                                const element = document.querySelector(selector);
                                return element ? element.innerText.trim() : '';
                            }
                            
                            // Extract experience items
                            const experienceItems = Array.from(
                                document.querySelectorAll('.experience-section li')
                            ).map(item => {
                                const title = item.querySelector('.pv-entity__summary-info h3')?.innerText || '';
                                const company = item.querySelector('.pv-entity__secondary-title')?.innerText || '';
                                const dateRange = item.querySelector('.pv-entity__date-range span:not(:first-child)')?.innerText || '';
                                return { title, company, dateRange };
                            });
                            
                            // Extract education items
                            const educationItems = Array.from(
                                document.querySelectorAll('.education-section li')
                            ).map(item => {
                                const school = item.querySelector('h3')?.innerText || '';
                                const degree = item.querySelector('.pv-entity__secondary-title')?.innerText || '';
                                const years = item.querySelector('.pv-entity__dates span:not(:first-child)')?.innerText || '';
                                return { school, degree, years };
                            });
                            
                            // Extract skills
                            const skills = Array.from(
                                document.querySelectorAll('.pv-skill-categories-section li .pv-skill-category-entity__name-text')
                            ).map(skill => skill.innerText.trim());
                            
                            return {
                                about: safeText('.pv-about-section .pv-about__summary-text'),
                                experience: experienceItems.slice(0, 3), // Limit to recent 3
                                education: educationItems,
                                skills: skills.slice(0, 10), // Limit to top 10
                                connections: safeText('.pv-top-card--list .pv-top-card--list-bullet:first-child'),
                                activity_status: safeText('.pv-recent-activity-section-v2__headline h3')
                            };
                        }
                    """)
                    
                    return detailed_data
                    
            finally:
                # Always close the page
                await page.close()
                
        except Exception as e:
            logger.error(
                "LinkedIn profile details error", 
                error=str(e),
                profile_url=profile_url,
                user_id=self.user_id
            )
            return {}
    
    def _calculate_confidence_score(self, query_name: str, result_name: str) -> float:
        """
        Calculate confidence score based on name match
        
        Args:
            query_name: The name we searched for
            result_name: The name we found
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not query_name or not result_name:
            return 0.5  # Default moderate confidence
        
        # Normalize names
        query_name = query_name.lower().strip()
        result_name = result_name.lower().strip()
        
        # Exact match
        if query_name == result_name:
            return 1.0
            
        # Check if all query name parts are in result name
        query_parts = set(query_name.split())
        result_parts = set(result_name.split())
        
        # If all parts are contained, high confidence
        if query_parts.issubset(result_parts):
            return 0.9
            
        # Calculate how many parts match
        matching_parts = query_parts.intersection(result_parts)
        match_ratio = len(matching_parts) / max(len(query_parts), 1)
        
        # Scale from 0.3 to 0.8 based on match ratio
        confidence = 0.3 + (match_ratio * 0.5)
        
        return confidence
        
    def _format_linkedin_data(self, raw_data: Dict) -> Dict:
        """
        Format LinkedIn data into a consistent structure
        
        Args:
            raw_data: Raw LinkedIn data
            
        Returns:
            Consistently formatted LinkedIn profile data
        """
        return {
            "name": raw_data.get("name", ""),
            "position": raw_data.get("position", ""),
            "company": raw_data.get("company", ""),
            "location": raw_data.get("location", ""),
            "profile_url": raw_data.get("profile_url", ""),
            "headline": raw_data.get("headline", ""),
            "about": raw_data.get("about", ""),
            "experience": raw_data.get("experience", []),
            "education": raw_data.get("education", []),
            "skills": raw_data.get("skills", []),
            "connections": raw_data.get("connections", ""),
            "limited_data": raw_data.get("limited_access", False)
        }
