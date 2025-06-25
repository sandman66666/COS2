"""
Advanced Web Intelligence System
===============================
Multi-strategy web scraping with high success rates for company intelligence
"""

import asyncio
import aiohttp
import json
import re
import ssl
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import time

from utils.logging import structured_logger as logger

@dataclass
class CompanyIntelligence:
    """Comprehensive company intelligence data"""
    domain: str
    name: str = ""
    description: str = ""
    industry: str = ""
    size_estimate: str = ""
    technologies: List[str] = field(default_factory=list)
    social_links: Dict[str, str] = field(default_factory=dict)
    funding_info: str = ""
    founded_year: str = ""
    location: str = ""
    confidence_score: float = 0.0
    data_sources: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)

class AdvancedWebIntelligence:
    """
    Advanced web intelligence system with multiple strategies:
    1. Enhanced HTTP scraping with better headers
    2. Multiple search engines  
    3. Alternative data sources
    4. Intelligent fallbacks
    5. Optional browser automation (if available)
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.session = None
        self.search_engines = [
            "google.com",
            "bing.com", 
            "duckduckgo.com"
        ]
        self.cache = {}
        self.browser_available = False
        
    async def initialize(self):
        """Initialize all components"""
        # Initialize enhanced HTTP session
        await self._init_http_session()
        
        # Try to initialize browser (optional)
        await self._init_browser_if_available()
        
        logger.info(f"🚀 Advanced Web Intelligence initialized for user {self.user_id} (browser: {self.browser_available})")
    
    async def _init_http_session(self):
        """Initialize enhanced HTTP session"""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(
            limit=20,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True,
            ssl=ssl_context,
            enable_cleanup_closed=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=15, connect=5, sock_read=10)
        
        # Enhanced headers for better success rates
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
    
    async def _init_browser_if_available(self):
        """Try to initialize browser automation (optional)"""
        try:
            from playwright.async_api import async_playwright
            playwright = await async_playwright().start()
            
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            self.browser_available = True
            logger.info("🎭 Browser automation initialized")
            
        except Exception as e:
            logger.info(f"Browser automation not available: {e}")
            self.browser_available = False
            self.browser = None
            self.context = None
    
    async def get_company_intelligence(self, domain: str) -> CompanyIntelligence:
        """
        Get comprehensive company intelligence using multiple strategies
        """
        if domain in self.cache:
            cached = self.cache[domain]
            if (datetime.utcnow() - cached.last_updated).seconds < 3600:  # 1 hour cache
                return cached
        
        logger.info(f"🔍 Gathering intelligence for {domain}")
        
        intelligence = CompanyIntelligence(
            domain=domain,
            data_sources=[],
            last_updated=datetime.utcnow()
        )
        
        # Strategy 1: Enhanced direct website analysis
        website_data = await self._analyze_website_enhanced(domain)
        if website_data:
            self._merge_intelligence(intelligence, website_data, "enhanced_website")
        
        # Strategy 2: Multi-engine search
        search_data = await self._multi_engine_company_search(domain)
        if search_data:
            self._merge_intelligence(intelligence, search_data, "search_engines")
        
        # Strategy 3: Social platform discovery
        social_data = await self._discover_social_platforms(domain)
        if social_data:
            self._merge_intelligence(intelligence, social_data, "social_platforms")
        
        # Strategy 4: Alternative data sources
        alt_data = await self._get_alternative_data_sources(domain)
        if alt_data:
            self._merge_intelligence(intelligence, alt_data, "alternative_sources")
        
        # Strategy 5: Browser automation (if available)
        if self.browser_available:
            browser_data = await self._analyze_with_browser(domain)
            if browser_data:
                self._merge_intelligence(intelligence, browser_data, "browser_automation")
        
        # Calculate confidence score
        intelligence.confidence_score = self._calculate_confidence(intelligence)
        
        # Cache result
        self.cache[domain] = intelligence
        
        logger.info(f"✅ Intelligence gathered for {domain}: {intelligence.confidence_score:.2f} confidence, {len(intelligence.data_sources)} sources")
        
        return intelligence
    
    async def _analyze_website_enhanced(self, domain: str) -> Optional[Dict]:
        """Enhanced website analysis with better success rates"""
        urls_to_try = [
            f"https://{domain}",
            f"https://www.{domain}",
            f"https://{domain}/about",
            f"https://www.{domain}/about-us",
            f"https://www.{domain}/company",
            f"http://{domain}",  # Fallback to HTTP
            f"http://www.{domain}"
        ]
        
        for url in urls_to_try:
            try:
                # Random delay and user agent rotation
                await asyncio.sleep(random.uniform(0.5, 2))
                
                headers = {
                    'User-Agent': self._get_random_user_agent(),
                    'Referer': 'https://www.google.com/',
                }
                
                async with self.session.get(url, headers=headers, ssl=False) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Enhanced HTML parsing
                        data = self._extract_enhanced_info_from_html(html, domain)
                        if data:
                            logger.info(f"✅ Enhanced website analysis successful for {url}")
                            return data
                    
            except Exception as e:
                logger.debug(f"Enhanced website analysis failed for {url}: {e}")
                continue
        
        return None
    
    def _extract_enhanced_info_from_html(self, html: str, domain: str) -> Dict:
        """Enhanced information extraction from HTML"""
        data = {}
        
        # Extract title
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
            data['title'] = title
            
            # Try to extract company name from title
            if domain.split('.')[0].lower() in title.lower():
                data['company_name'] = title.split('-')[0].strip()
        
        # Enhanced meta description extraction
        desc_patterns = [
            r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*name=["\']twitter:description["\'][^>]*content=["\']([^"\']+)["\']'
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                data['description'] = match.group(1).strip()
                break
        
        # Look for structured data (JSON-LD)
        json_ld_matches = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
        for json_str in json_ld_matches:
            try:
                json_data = json.loads(json_str.strip())
                if isinstance(json_data, dict):
                    if json_data.get('@type') in ['Organization', 'Corporation', 'Company']:
                        if json_data.get('name'):
                            data['company_name'] = json_data['name']
                        if json_data.get('description'):
                            data['description'] = json_data['description']
                        if json_data.get('industry'):
                            data['industry'] = json_data['industry']
            except:
                continue
        
        # Enhanced social links extraction
        social_patterns = {
            'linkedin': r'https://[^"\']*linkedin\.com/company/[^"\']*',
            'twitter': r'https://[^"\']*twitter\.com/[^"\']*',
            'facebook': r'https://[^"\']*facebook\.com/[^"\']*'
        }
        
        for platform, pattern in social_patterns.items():
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                data[f'{platform}_url'] = matches[0]
        
        # Look for technology indicators
        tech_indicators = {
            'React': [r'react', r'_react', r'React\.'],
            'Angular': [r'angular', r'ng-'],
            'Vue.js': [r'vue\.js', r'vuejs'],
            'WordPress': [r'wp-content', r'wordpress'],
            'Shopify': [r'shopify', r'myshopify'],
            'Stripe': [r'stripe'],
            'Google Analytics': [r'google-analytics', r'gtag']
        }
        
        technologies = []
        for tech, patterns in tech_indicators.items():
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    technologies.append(tech)
                    break
        
        if technologies:
            data['technologies'] = technologies
        
        # Industry keyword detection
        industry_keywords = {
            'Technology': ['software', 'technology', 'tech', 'saas', 'platform'],
            'Healthcare': ['healthcare', 'medical', 'health', 'pharma'],
            'Finance': ['fintech', 'finance', 'banking', 'investment'],
            'E-commerce': ['ecommerce', 'e-commerce', 'retail', 'shop'],
            'Consulting': ['consulting', 'advisory', 'services'],
            'Education': ['education', 'learning', 'training'],
            'Startup': ['startup', 'venture', 'innovation']
        }
        
        html_lower = html.lower()
        for industry, keywords in industry_keywords.items():
            for keyword in keywords:
                if keyword in html_lower:
                    data['industry'] = industry
                    break
            if data.get('industry'):
                break
        
        return data
    
    async def _multi_engine_company_search(self, domain: str) -> Optional[Dict]:
        """Search multiple engines for company information"""
        company_name = self._domain_to_company_name(domain)
        
        search_queries = [
            f'"{domain}" company about',
            f'"{company_name}" company',
            f'{domain} startup'
        ]
        
        for query in search_queries:
            for engine in self.search_engines:
                try:
                    results = await self._search_engine_query(engine, query)
                    if results:
                        logger.info(f"✅ Found data via {engine} search")
                        return results
                    
                    # Rate limiting between searches
                    await asyncio.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    logger.debug(f"Search failed on {engine}: {e}")
                    continue
        
        return None
    
    async def _search_engine_query(self, engine: str, query: str) -> Optional[Dict]:
        """Query specific search engine with enhanced parsing"""
        try:
            encoded_query = query.replace(' ', '+').replace('"', '%22')
            
            if engine == "google.com":
                url = f"https://www.google.com/search?q={encoded_query}"
            elif engine == "bing.com":
                url = f"https://www.bing.com/search?q={encoded_query}"
            elif engine == "duckduckgo.com":
                url = f"https://duckduckgo.com/html/?q={encoded_query}"
            else:
                return None
            
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Referer': f'https://www.{engine}/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            async with self.session.get(url, headers=headers, ssl=False) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_search_results(html, engine)
                    
        except Exception as e:
            logger.debug(f"{engine} search error: {e}")
        
        return None
    
    def _parse_search_results(self, html: str, engine: str) -> Dict:
        """Enhanced search result parsing"""
        data = {}
        
        # Extract snippets based on engine
        if engine == "google.com":
            # Multiple pattern attempts for Google
            snippet_patterns = [
                r'<span[^>]*class="[^"]*st"[^>]*>(.*?)</span>',
                r'<div[^>]*data-sncf[^>]*>.*?<span[^>]*>(.*?)</span>',
                r'<div[^>]*class="[^"]*VwiC3b[^"]*"[^>]*>(.*?)</div>',
            ]
        elif engine == "bing.com":
            snippet_patterns = [
                r'<p class="b_para">(.*?)</p>',
                r'<div class="b_caption"[^>]*>(.*?)</div>',
            ]
        else:  # DuckDuckGo
            snippet_patterns = [
                r'<a class="result__snippet"[^>]*>(.*?)</a>',
                r'<div class="result__snippet"[^>]*>(.*?)</div>',
            ]
        
        for pattern in snippet_patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            if matches:
                # Clean up the snippet
                snippet = re.sub(r'<[^>]+>', '', matches[0])
                snippet = re.sub(r'\s+', ' ', snippet).strip()
                
                if len(snippet) > 20:
                    data['description'] = snippet[:400]  # Longer snippets
                    break
        
        # Look for industry indicators in search results
        industries = ['software', 'technology', 'fintech', 'healthcare', 'saas', 'startup', 'consulting']
        for industry in industries:
            if industry in html.lower():
                data['industry'] = industry.title()
                break
        
        return data
    
    async def _discover_social_platforms(self, domain: str) -> Optional[Dict]:
        """Discover social media platforms for the company"""
        company_name = self._domain_to_company_name(domain)
        
        social_links = {}
        
        # Strategy 1: Direct website analysis (extract social links from company website)
        try:
            website_social = await self._extract_social_from_website(domain)
            if website_social:
                social_links.update(website_social)
        except Exception as e:
            logger.debug(f"Website social extraction failed: {e}")
        
        # Strategy 2: LinkedIn company page search (if not found on website)
        if 'linkedin' not in social_links:
            try:
                linkedin_url = await self._find_linkedin_company_page(company_name, domain)
                if linkedin_url:
                    social_links['linkedin'] = linkedin_url
            except Exception as e:
                logger.debug(f"LinkedIn company discovery failed: {e}")
        
        # Strategy 3: Twitter/X profile search (if not found on website)
        if 'twitter' not in social_links:
            try:
                twitter_url = await self._find_twitter_profile(company_name, domain)
                if twitter_url:
                    social_links['twitter'] = twitter_url
            except Exception as e:
                logger.debug(f"Twitter discovery failed: {e}")
        
        # Strategy 4: Facebook page search (if not found on website)
        if 'facebook' not in social_links:
            try:
                facebook_url = await self._find_facebook_page(company_name, domain)
                if facebook_url:
                    social_links['facebook'] = facebook_url
            except Exception as e:
                logger.debug(f"Facebook discovery failed: {e}")
        
        if social_links:
            logger.info(f"✅ Found {len(social_links)} social profiles for {domain}: {list(social_links.keys())}")
            return {'social_links': social_links}
        
        return None
    
    async def _extract_social_from_website(self, domain: str) -> Optional[Dict]:
        """Extract social media links directly from the company website"""
        urls_to_try = [
            f"https://{domain}",
            f"https://www.{domain}",
            f"https://{domain}/about",
            f"https://www.{domain}/about-us",
            f"https://www.{domain}/contact"
        ]
        
        for url in urls_to_try:
            try:
                headers = {
                    'User-Agent': self._get_random_user_agent(),
                    'Referer': 'https://www.google.com/',
                }
                
                async with self.session.get(url, headers=headers, ssl=False) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        social_links = {}
                        
                        # Enhanced social media patterns
                        social_patterns = {
                            'linkedin': [
                                r'https://[^"\']*linkedin\.com/company/[^"\']*',
                                r'https://linkedin\.com/company/[^"\']*',
                                r'https://www\.linkedin\.com/company/[^"\']*'
                            ],
                            'twitter': [
                                r'https://[^"\']*twitter\.com/[^"\'/?]*',
                                r'https://[^"\']*x\.com/[^"\'/?]*',
                                r'twitter\.com/[^"\'/?]*',
                                r'x\.com/[^"\'/?]*'
                            ],
                            'facebook': [
                                r'https://[^"\']*facebook\.com/[^"\'/?]*',
                                r'https://www\.facebook\.com/[^"\'/?]*',
                                r'facebook\.com/[^"\'/?]*'
                            ],
                            'instagram': [
                                r'https://[^"\']*instagram\.com/[^"\'/?]*',
                                r'instagram\.com/[^"\'/?]*'
                            ],
                            'youtube': [
                                r'https://[^"\']*youtube\.com/[^"\'/?]*',
                                r'youtube\.com/[^"\'/?]*'
                            ]
                        }
                        
                        for platform, patterns in social_patterns.items():
                            for pattern in patterns:
                                matches = re.findall(pattern, html, re.IGNORECASE)
                                if matches:
                                    # Clean the URL
                                    social_url = matches[0]
                                    
                                    # Add https:// if missing
                                    if not social_url.startswith('http'):
                                        social_url = f"https://{social_url}"
                                    
                                    # Clean tracking parameters
                                    social_url = social_url.split('&')[0].split('?')[0]
                                    
                                    # Validate URL patterns
                                    if platform == 'linkedin' and '/company/' in social_url:
                                        social_links['linkedin'] = social_url
                                        break
                                    elif platform == 'twitter' and not any(exclude in social_url.lower() for exclude in ['/status/', '/search/', '/hashtag/']):
                                        social_links['twitter'] = social_url
                                        break
                                    elif platform == 'facebook' and not any(exclude in social_url.lower() for exclude in ['/posts/', '/photos/', '/videos/']):
                                        social_links['facebook'] = social_url
                                        break
                                    elif platform in ['instagram', 'youtube']:
                                        social_links[platform] = social_url
                                        break
                        
                        if social_links:
                            logger.info(f"✅ Extracted social links from {url}: {list(social_links.keys())}")
                            return social_links
                
                # Rate limiting between URLs
                await asyncio.sleep(random.uniform(0.5, 1))
                
            except Exception as e:
                logger.debug(f"Failed to extract social links from {url}: {e}")
                continue
        
        return None
    
    async def _find_linkedin_company_page(self, company_name: str, domain: str) -> Optional[str]:
        """Enhanced LinkedIn company page discovery with multiple strategies"""
        
        # Multiple search queries for better coverage
        search_queries = [
            f'"{company_name}" site:linkedin.com/company',
            f'"{domain}" site:linkedin.com/company',
            f'{company_name} company site:linkedin.com',
            f'"{company_name}" LinkedIn company page'
        ]
        
        for query in search_queries:
            try:
                encoded_query = query.replace(' ', '+').replace('"', '%22')
                
                headers = {
                    'User-Agent': self._get_random_user_agent(),
                    'Referer': 'https://www.google.com/',
                }
                
                async with self.session.get(
                    f"https://www.google.com/search?q={encoded_query}",
                    headers=headers,
                    ssl=False
                ) as response:
                    
                    if response.status == 200:
                        html = await response.text()
                        
                        # Enhanced LinkedIn URL patterns
                        linkedin_patterns = [
                            r'https://[^"\']*linkedin\.com/company/[^"\']*',
                            r'https://linkedin\.com/company/[^"\']*',
                            r'https://www\.linkedin\.com/company/[^"\']*'
                        ]
                        
                        for pattern in linkedin_patterns:
                            matches = re.findall(pattern, html, re.IGNORECASE)
                            if matches:
                                # Clean and validate LinkedIn URL
                                linkedin_url = matches[0].split('&')[0].split('?')[0]  # Remove tracking params
                                
                                # Verify it's a valid company page
                                if '/company/' in linkedin_url and not linkedin_url.endswith('/company/'):
                                    logger.info(f"✅ Found LinkedIn company page: {linkedin_url}")
                                    return linkedin_url
                
                # Rate limiting between queries
                await asyncio.sleep(random.uniform(1, 2))
                        
            except Exception as e:
                logger.debug(f"LinkedIn search failed for query '{query}': {e}")
                continue
        
        return None
    
    async def _find_twitter_profile(self, company_name: str, domain: str) -> Optional[str]:
        """Find company Twitter/X profile"""
        
        search_queries = [
            f'"{company_name}" site:twitter.com',
            f'"{domain}" site:twitter.com',  
            f'"{company_name}" site:x.com',
            f'{company_name} Twitter official'
        ]
        
        for query in search_queries:
            try:
                encoded_query = query.replace(' ', '+').replace('"', '%22')
                
                headers = {
                    'User-Agent': self._get_random_user_agent(),
                    'Referer': 'https://www.google.com/',
                }
                
                async with self.session.get(
                    f"https://www.google.com/search?q={encoded_query}",
                    headers=headers,
                    ssl=False
                ) as response:
                    
                    if response.status == 200:
                        html = await response.text()
                        
                        # Twitter/X URL patterns
                        twitter_patterns = [
                            r'https://[^"\']*twitter\.com/[^"\'/?]*',
                            r'https://[^"\']*x\.com/[^"\'/?]*'
                        ]
                        
                        for pattern in twitter_patterns:
                            matches = re.findall(pattern, html, re.IGNORECASE)
                            if matches:
                                twitter_url = matches[0].split('&')[0].split('?')[0]
                                
                                # Exclude generic Twitter pages
                                if not any(exclude in twitter_url.lower() for exclude in ['/status/', '/search/', '/hashtag/']):
                                    logger.info(f"✅ Found Twitter profile: {twitter_url}")
                                    return twitter_url
                
                await asyncio.sleep(random.uniform(1, 2))
                        
            except Exception as e:
                logger.debug(f"Twitter search failed for query '{query}': {e}")
                continue
        
        return None
    
    async def _find_facebook_page(self, company_name: str, domain: str) -> Optional[str]:
        """Find company Facebook page"""
        
        search_queries = [
            f'"{company_name}" site:facebook.com',
            f'"{domain}" site:facebook.com',
            f'{company_name} Facebook page official'
        ]
        
        for query in search_queries:
            try:
                encoded_query = query.replace(' ', '+').replace('"', '%22')
                
                headers = {
                    'User-Agent': self._get_random_user_agent(),
                    'Referer': 'https://www.google.com/',
                }
                
                async with self.session.get(
                    f"https://www.google.com/search?q={encoded_query}",
                    headers=headers,
                    ssl=False
                ) as response:
                    
                    if response.status == 200:
                        html = await response.text()
                        
                        # Facebook URL patterns
                        facebook_patterns = [
                            r'https://[^"\']*facebook\.com/[^"\'/?]*',
                            r'https://www\.facebook\.com/[^"\'/?]*'
                        ]
                        
                        for pattern in facebook_patterns:
                            matches = re.findall(pattern, html, re.IGNORECASE)
                            if matches:
                                facebook_url = matches[0].split('&')[0].split('?')[0]
                                
                                # Exclude generic Facebook pages
                                if not any(exclude in facebook_url.lower() for exclude in ['/posts/', '/photos/', '/videos/']):
                                    logger.info(f"✅ Found Facebook page: {facebook_url}")
                                    return facebook_url
                
                await asyncio.sleep(random.uniform(1, 2))
                        
            except Exception as e:
                logger.debug(f"Facebook search failed for query '{query}': {e}")
                continue
        
        return None
    
    async def _get_alternative_data_sources(self, domain: str) -> Optional[Dict]:
        """Get data from alternative sources"""
        company_name = self._domain_to_company_name(domain)
        
        # Search for funding/startup information
        queries = [
            f'"{company_name}" funding',
            f'"{company_name}" founded',
            f'"{domain}" company info'
        ]
        
        for query in queries:
            try:
                data = await self._search_for_company_metadata(query)
                if data:
                    return data
                    
                await asyncio.sleep(random.uniform(1, 2))
                
            except Exception as e:
                logger.debug(f"Alternative data search failed: {e}")
                continue
        
        return None
    
    async def _search_for_company_metadata(self, query: str) -> Optional[Dict]:
        """Search for company metadata"""
        try:
            encoded_query = query.replace(' ', '+').replace('"', '%22')
            
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Referer': 'https://www.google.com/',
            }
            
            async with self.session.get(
                f"https://www.google.com/search?q={encoded_query}",
                headers=headers,
                ssl=False
            ) as response:
                
                if response.status == 200:
                    html = await response.text()
                    
                    # Look for funding/founding information
                    funding_patterns = [
                        r'raised\s+\$([0-9.,]+[MBK]?)',
                        r'funding\s+of\s+\$([0-9.,]+[MBK]?)',
                        r'founded\s+in\s+(\d{4})',
                        r'established\s+(\d{4})'
                    ]
                    
                    data = {}
                    for pattern in funding_patterns:
                        match = re.search(pattern, html, re.IGNORECASE)
                        if match:
                            if 'raised' in pattern or 'funding' in pattern:
                                data['funding_info'] = f"${match.group(1)}"
                            elif 'founded' in pattern or 'established' in pattern:
                                data['founded_year'] = match.group(1)
                    
                    return data if data else None
                    
        except Exception as e:
            logger.debug(f"Metadata search failed: {e}")
        
        return None
    
    async def _analyze_with_browser(self, domain: str) -> Optional[Dict]:
        """Optional browser-based analysis if available"""
        if not self.browser_available:
            return None
        
        try:
            page = await self.context.new_page()
            await page.goto(f"https://{domain}", timeout=10000)
            await page.wait_for_timeout(2000)
            
            # Simple browser extraction
            data = await page.evaluate("""
                () => {
                    return {
                        title: document.title,
                        description: document.querySelector('meta[name="description"]')?.content || '',
                        has_react: !!window.React,
                        has_angular: !!window.angular,
                        has_vue: !!window.Vue
                    };
                }
            """)
            
            await page.close()
            
            if data.get('title') or data.get('description'):
                logger.info(f"✅ Browser analysis successful for {domain}")
                return data
                
        except Exception as e:
            logger.debug(f"Browser analysis failed for {domain}: {e}")
            if 'page' in locals():
                await page.close()
        
        return None
    
    def _merge_intelligence(self, intelligence: CompanyIntelligence, data: Dict, source: str):
        """Merge new data into intelligence object"""
        intelligence.data_sources.append(source)
        
        # Merge data with priority to existing values
        if not intelligence.name and data.get('company_name'):
            intelligence.name = data['company_name']
        elif not intelligence.name and data.get('title'):
            intelligence.name = data['title'].split('-')[0].strip()
        
        if not intelligence.description and data.get('description'):
            intelligence.description = data['description']
        
        if not intelligence.industry and data.get('industry'):
            intelligence.industry = data['industry']
        
        if data.get('technologies'):
            intelligence.technologies.extend(data['technologies'])
        
        # Merge social links
        for key, value in data.items():
            if key.endswith('_url') and value:
                platform = key.replace('_url', '')
                intelligence.social_links[platform] = value
        
        if data.get('social_links'):
            intelligence.social_links.update(data['social_links'])
        
        if data.get('funding_info'):
            intelligence.funding_info = data['funding_info']
        
        if data.get('founded_year'):
            intelligence.founded_year = data['founded_year']
    
    def _calculate_confidence(self, intelligence: CompanyIntelligence) -> float:
        """Calculate confidence score based on available data"""
        score = 0.0
        
        if intelligence.name: score += 0.25
        if intelligence.description: score += 0.35
        if intelligence.industry: score += 0.15
        if intelligence.social_links: score += 0.10
        if intelligence.technologies: score += 0.05
        if intelligence.funding_info: score += 0.05
        if intelligence.founded_year: score += 0.05
        
        # Bonus for multiple sources
        if len(intelligence.data_sources) > 1: score += 0.1
        if len(intelligence.data_sources) > 2: score += 0.1
        
        return min(score, 1.0)
    
    def _domain_to_company_name(self, domain: str) -> str:
        """Convert domain to likely company name"""
        name = domain.split('.')[0]
        name = re.sub(r'[^a-zA-Z0-9\s]', ' ', name)
        return ' '.join(word.capitalize() for word in name.split())
    
    def _get_random_user_agent(self) -> str:
        """Get random user agent for requests"""
        agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        return random.choice(agents)
    
    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
        
        if self.browser_available and self.context:
            await self.context.close()
        
        if self.browser_available and self.browser:
            await self.browser.close()
        
        logger.info("🧹 Advanced Web Intelligence cleaned up") 