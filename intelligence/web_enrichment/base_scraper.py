# intelligence/web_enrichment/base_scraper.py
"""
Base Web Scraper
===============
Base class for all web scraping workers that enrich contact data.
Ensures proper multi-tenant isolation for user data.
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import time
from abc import ABC, abstractmethod

from playwright.async_api import async_playwright, Page, Browser
from utils.logging import structured_logger as logger

@dataclass
class EnrichmentResult:
    """Result of web enrichment for a contact"""
    email: str
    user_id: int
    source: str  # The source of enrichment (e.g., "linkedin", "twitter")
    data: Dict[str, Any] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    enrichment_timestamp: datetime = None
    error: Optional[str] = None
    successful: bool = False


class BaseScraper(ABC):
    """
    Base class for web scrapers with consistent interface
    Implements multi-tenant isolation to ensure data privacy
    """
    
    def __init__(self, user_id: int = None, rate_limit: float = 2.0):
        """
        Initialize base scraper
        
        Args:
            user_id: ID of user for multi-tenant isolation
            rate_limit: Minimum seconds between requests to avoid rate limiting
        """
        self.user_id = user_id
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.browser = None
        self.context = None
        self.session = None
        self._initialized = False
        
    async def initialize(self) -> bool:
        """
        Initialize browser and session
        
        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True
            
        try:
            # Create HTTP session for API requests
            self.session = aiohttp.ClientSession(
                headers=self._get_default_headers()
            )
            
            # Initialize playwright browser
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,  # Use headless browser
            )
            
            # Create context with custom settings
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent=self._get_user_agent(),
                ignore_https_errors=True
            )
            
            self._initialized = True
            logger.info(f"{self.__class__.__name__} initialized", user_id=self.user_id)
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to initialize {self.__class__.__name__}", 
                user_id=self.user_id,
                error=str(e)
            )
            await self.cleanup()
            return False
    
    async def cleanup(self) -> None:
        """Clean up resources when done"""
        try:
            if self.browser:
                await self.browser.close()
                self.browser = None
                
            if self.context:
                await self.context.close()
                self.context = None
                
            if self.session:
                await self.session.close()
                self.session = None
                
            self._initialized = False
            
        except Exception as e:
            logger.error(
                f"Error during {self.__class__.__name__} cleanup", 
                error=str(e),
                user_id=self.user_id
            )
    
    @abstractmethod
    async def enrich_contact(self, contact: Dict) -> EnrichmentResult:
        """
        Enrich a contact with web data
        Must be implemented by subclasses
        
        Args:
            contact: Contact data dictionary with at least 'email' field
            
        Returns:
            Enrichment result with data from web source
        """
        pass
    
    async def _new_page(self) -> Page:
        """
        Create a new browser page with rate limiting
        
        Returns:
            New playwright page
        """
        if not self._initialized:
            await self.initialize()
            
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            await asyncio.sleep(self.rate_limit - time_since_last)
            
        # Update last request time
        self.last_request_time = time.time()
        
        # Create new page
        return await self.context.new_page()
    
    def _get_default_headers(self) -> Dict[str, str]:
        """
        Get default headers for requests
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            "User-Agent": self._get_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "TE": "trailers"
        }
    
    def _get_user_agent(self) -> str:
        """
        Get user agent string
        
        Returns:
            User agent string
        """
        return (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        )
    
    async def _take_screenshot(self, page: Page, name: str = "error") -> Optional[str]:
        """
        Take screenshot for debugging
        
        Args:
            page: Playwright page
            name: Screenshot name prefix
            
        Returns:
            Path to screenshot file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"debug_{name}_{timestamp}.png"
            await page.screenshot(path=filename)
            return filename
        except Exception as e:
            logger.error("Failed to take screenshot", error=str(e))
            return None
    
    def _create_success_result(
        self,
        email: str,
        source: str,
        data: Dict[str, Any],
        raw_data: Dict[str, Any] = None,
        confidence: float = 1.0
    ) -> EnrichmentResult:
        """
        Create successful enrichment result
        
        Args:
            email: Contact email
            source: Source of the data
            data: Processed data
            raw_data: Raw data from source
            confidence: Confidence score (0.0-1.0)
            
        Returns:
            EnrichmentResult with successful status
        """
        return EnrichmentResult(
            email=email,
            user_id=self.user_id,
            source=source,
            data=data,
            raw_data=raw_data or {},
            confidence_score=confidence,
            enrichment_timestamp=datetime.utcnow(),
            successful=True
        )
    
    def _create_error_result(
        self,
        email: str,
        source: str,
        error: str
    ) -> EnrichmentResult:
        """
        Create error enrichment result
        
        Args:
            email: Contact email
            source: Source of the data
            error: Error message
            
        Returns:
            EnrichmentResult with error status
        """
        return EnrichmentResult(
            email=email,
            user_id=self.user_id,
            source=source,
            error=error,
            enrichment_timestamp=datetime.utcnow(),
            successful=False
        )
