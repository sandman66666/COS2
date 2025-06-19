# intelligence/web_enrichment/twitter_scraper.py
"""
Twitter/X Web Scraper
===================
Enriches contact data with Twitter profile information.
Uses a privacy-conscious approach for multi-tenant systems.
"""

import re
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from utils.logging import structured_logger as logger
from intelligence.web_enrichment.base_scraper import BaseScraper, EnrichmentResult

class TwitterScraper(BaseScraper):
    """
    Twitter/X web scraper for contact enrichment
    
    Extracts social media information about contacts while
    respecting website terms and user privacy.
    """
    
    def __init__(self, user_id: int = None, rate_limit: float = 2.5):
        """
        Initialize Twitter scraper
        
        Args:
            user_id: User ID for multi-tenant isolation
            rate_limit: Seconds between requests to avoid rate limiting
        """
        super().__init__(user_id, rate_limit)
        self.source = "twitter"
    
    async def enrich_contact(self, contact: Dict) -> EnrichmentResult:
        """
        Enrich contact with Twitter data
        
        Args:
            contact: Contact information dictionary with at minimum:
                    - email: Email address
                    - name: (optional) Full name
                    
        Returns:
            EnrichmentResult with Twitter profile data
        """
        if not contact.get("email"):
            return self._create_error_result(
                email=contact.get("email", "unknown"),
                source=self.source,
                error="Email is required for Twitter enrichment"
            )
            
        try:
            # Initialize if needed
            if not self._initialized:
                success = await self.initialize()
                if not success:
                    return self._create_error_result(
                        email=contact["email"],
                        source=self.source,
                        error="Failed to initialize Twitter scraper"
                    )
            
            # Extract data points from contact
            email = contact["email"]
            name = contact.get("name", "")
            
            # Try to find Twitter handle
            twitter_handle = await self._find_twitter_handle(email, name)
            
            if not twitter_handle:
                return self._create_error_result(
                    email=email,
                    source=self.source,
                    error="Could not find Twitter handle"
                )
            
            # Get profile data
            profile_data = await self._get_profile_data(twitter_handle)
            
            if not profile_data:
                return self._create_error_result(
                    email=email,
                    source=self.source,
                    error=f"No Twitter profile found for handle @{twitter_handle}"
                )
            
            # Format the data
            enriched_data = self._format_twitter_data(profile_data)
            
            # Calculate confidence based on name match
            confidence = self._calculate_confidence(name, profile_data.get("name", ""))
            
            return self._create_success_result(
                email=email,
                source=self.source,
                data=enriched_data,
                raw_data=profile_data,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(
                "Twitter enrichment error",
                error=str(e),
                email=contact.get("email"),
                user_id=self.user_id
            )
            return self._create_error_result(
                email=contact["email"],
                source=self.source,
                error=f"Twitter enrichment failed: {str(e)}"
            )
    
    async def _find_twitter_handle(self, email: str, name: str) -> Optional[str]:
        """
        Try to find Twitter handle from email or name
        
        Args:
            email: Contact's email address
            name: Contact's name
            
        Returns:
            Twitter handle if found, None otherwise
        """
        possible_handles = []
        
        # Try email-based handles
        if email and "@" in email:
            username = email.split("@")[0]
            possible_handles.append(username)
            
            # Common variations
            if "." in username:
                possible_handles.append(username.replace(".", ""))
                
            # Firstname.lastname format
            if "." in username:
                parts = username.split(".")
                if len(parts) == 2:
                    possible_handles.append(parts[0])  # Just first name
                    possible_handles.append(f"{parts[0]}_{parts[1]}")  # firstname_lastname
        
        # Try name-based handles
        if name:
            # Clean and normalize name
            name_clean = re.sub(r'[^\w\s]', '', name).lower()
            name_parts = name_clean.split()
            
            if len(name_parts) >= 2:
                # First initial + lastname
                possible_handles.append(f"{name_parts[0][0]}{name_parts[-1]}")
                
                # First name + last name
                possible_handles.append(f"{name_parts[0]}{name_parts[-1]}")
                
                # First name + underscore + last name
                possible_handles.append(f"{name_parts[0]}_{name_parts[-1]}")
        
        # Try each handle
        for handle in possible_handles:
            if await self._check_twitter_handle(handle):
                return handle
                
        # If no match found, try Google search
        return await self._search_twitter_via_google(name)
    
    async def _check_twitter_handle(self, handle: str) -> bool:
        """
        Check if a Twitter handle exists
        
        Args:
            handle: Twitter handle to check
            
        Returns:
            True if handle exists
        """
        try:
            # Clean handle
            handle = handle.strip().lower()
            if handle.startswith("@"):
                handle = handle[1:]
                
            # Try direct profile access
            url = f"https://twitter.com/{handle}"
            
            async with self.session.head(url, allow_redirects=True) as response:
                return response.status == 200
                
        except Exception as e:
            logger.debug(
                f"Error checking Twitter handle {handle}",
                error=str(e)
            )
            return False
    
    async def _search_twitter_via_google(self, name: str) -> Optional[str]:
        """
        Search for Twitter profile using Google
        
        Args:
            name: Person's name
            
        Returns:
            Twitter handle if found
        """
        if not name:
            return None
            
        try:
            page = await self._new_page()
            
            try:
                # Encode search query
                encoded_name = name.replace(" ", "+")
                search_url = f"https://www.google.com/search?q={encoded_name}+twitter+profile"
                
                await page.goto(search_url, wait_until="networkidle")
                
                # Extract Twitter URLs from search results
                twitter_handle = await page.evaluate("""
                    () => {
                        const twitterLinks = Array.from(document.querySelectorAll('a[href*="twitter.com/"]'));
                        
                        for (const link of twitterLinks) {
                            const href = link.href;
                            if (href.includes('/status/')) continue; // Skip tweet links
                            
                            const match = href.match(/twitter\\.com\\/(\\w+)/);
                            if (match && match[1] && match[1] !== 'search' && match[1].length > 1) {
                                return match[1];
                            }
                        }
                        
                        return null;
                    }
                """)
                
                return twitter_handle
            
            finally:
                await page.close()
                
        except Exception as e:
            logger.error(f"Twitter Google search error: {str(e)}")
            return None
    
    async def _get_profile_data(self, handle: str) -> Optional[Dict]:
        """
        Get Twitter profile data
        
        Args:
            handle: Twitter handle
            
        Returns:
            Profile data dictionary
        """
        try:
            # Clean handle
            handle = handle.strip().lower()
            if handle.startswith("@"):
                handle = handle[1:]
                
            profile_url = f"https://twitter.com/{handle}"
            
            page = await self._new_page()
            
            try:
                await page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_selector('main', timeout=10000)
                
                # Extract profile data
                profile_data = await page.evaluate("""
                    () => {
                        // Helper function for safe text extraction
                        function safeText(selector) {
                            const el = document.querySelector(selector);
                            return el ? el.innerText.trim() : '';
                        }
                        
                        // Extract basic profile info
                        const name = safeText('main div[data-testid="primaryColumn"] h2');
                        const handle = safeText('main div[data-testid="primaryColumn"] div[dir="ltr"] span');
                        const bio = safeText('main div[data-testid="primaryColumn"] div[data-testid="UserDescription"]');
                        const location = safeText('main div[data-testid="primaryColumn"] span[data-testid="UserLocation"]');
                        
                        // Get stats
                        const statsContainer = document.querySelector('main div[data-testid="primaryColumn"] div[role="navigation"]');
                        let followingCount = '';
                        let followersCount = '';
                        
                        if (statsContainer) {
                            const statElements = statsContainer.querySelectorAll('span');
                            if (statElements.length >= 2) {
                                followingCount = statElements[0].innerText;
                                followersCount = statElements[1].innerText;
                            }
                        }
                        
                        // Get profile image
                        const profileImg = document.querySelector('main div[data-testid="primaryColumn"] img[src*="profile_images"]');
                        const profileImageUrl = profileImg ? profileImg.src : '';
                        
                        // Check verification
                        const isVerified = Boolean(document.querySelector('main div[data-testid="primaryColumn"] svg[aria-label*="Verified"]'));
                        
                        // Extract joining date if present
                        const joinDate = safeText('main div[data-testid="primaryColumn"] span[data-testid="UserJoinDate"]');
                        
                        return {
                            name: name,
                            handle: handle,
                            bio: bio,
                            location: location,
                            followers: followersCount,
                            following: followingCount,
                            profile_image_url: profileImageUrl,
                            is_verified: isVerified,
                            join_date: joinDate,
                            profile_url: window.location.href
                        };
                    }
                """)
                
                return profile_data
                
            finally:
                await page.close()
                
        except Exception as e:
            logger.error(f"Error getting Twitter profile: {str(e)}")
            return None
    
    def _calculate_confidence(self, query_name: str, result_name: str) -> float:
        """
        Calculate confidence score of Twitter profile match
        
        Args:
            query_name: Name we searched for
            result_name: Name from Twitter profile
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not query_name or not result_name:
            return 0.5  # Default moderate confidence
        
        # Clean and normalize names
        query_clean = query_name.lower().strip()
        result_clean = result_name.lower().strip()
        
        # Exact match
        if query_clean == result_clean:
            return 0.95
        
        # Check if first and last name are present
        query_parts = query_clean.split()
        result_parts = result_clean.split()
        
        if len(query_parts) >= 2 and len(result_parts) >= 1:
            # Check if first name matches
            first_match = query_parts[0] == result_parts[0]
            
            # Check if last name is present
            last_match = query_parts[-1] in result_clean
            
            if first_match and last_match:
                return 0.9
            elif first_match:
                return 0.7
            elif last_match:
                return 0.6
        
        # Partial matching
        for part in query_parts:
            if len(part) > 2 and part in result_clean:
                return 0.6
        
        return 0.4  # Low confidence
    
    def _format_twitter_data(self, profile_data: Dict) -> Dict:
        """
        Format Twitter profile data consistently
        
        Args:
            profile_data: Raw profile data
            
        Returns:
            Formatted Twitter data
        """
        return {
            "name": profile_data.get("name", ""),
            "handle": profile_data.get("handle", "").replace("@", ""),
            "bio": profile_data.get("bio", ""),
            "location": profile_data.get("location", ""),
            "followers_count": profile_data.get("followers", ""),
            "following_count": profile_data.get("following", ""),
            "profile_image": profile_data.get("profile_image_url", ""),
            "verified": profile_data.get("is_verified", False),
            "join_date": profile_data.get("join_date", ""),
            "profile_url": profile_data.get("profile_url", "")
        }
