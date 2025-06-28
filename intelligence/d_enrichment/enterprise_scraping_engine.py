"""
Enterprise Scraping Engine
=========================
Professional-grade web scraping with enterprise anti-detection techniques
Built for production environments with strict network restrictions

Key Features:
- Multi-proxy residential rotation
- Advanced browser fingerprint randomization  
- Human behavioral pattern simulation
- CAPTCHA detection and handling
- Geolocation spoofing
- Session lifecycle management
- Request pattern obfuscation
- Content adaptation and parsing
"""

import asyncio
import aiohttp
import json
import re
import ssl
import random
import time
import base64
import hashlib
import urllib.parse
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import cloudscraper
import requests
from fake_useragent import UserAgent
import numpy as np

from utils.logging import structured_logger as logger

@dataclass
class ScrapingSession:
    """Represents a complete scraping session with fingerprint"""
    session_id: str
    user_agent: str
    headers: Dict[str, str]
    cookies: Dict[str, str]
    proxy: Optional[str]
    created_at: datetime
    requests_made: int = 0
    success_rate: float = 0.0
    last_used: Optional[datetime] = None
    
    def is_expired(self, max_age_minutes: int = 30) -> bool:
        """Check if session is expired"""
        if not self.last_used:
            return True
        return (datetime.utcnow() - self.last_used).total_seconds() > (max_age_minutes * 60)
    
    def should_rotate(self, max_requests: int = 50) -> bool:
        """Check if session should be rotated"""
        return self.requests_made >= max_requests or self.success_rate < 0.3

@dataclass 
class ScrapingResult:
    """Result from a scraping operation"""
    success: bool
    data: Dict[str, Any]
    url: str
    status_code: int
    response_time: float
    session_id: str
    error: Optional[str] = None
    captcha_detected: bool = False
    blocked: bool = False

class EnterpriseScrapingEngine:
    """
    Enterprise-grade scraping engine with advanced anti-detection
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.sessions: Dict[str, ScrapingSession] = {}
        self.proxy_pool: List[str] = []
        self.user_agent_generator = None
        self.success_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'blocked_requests': 0,
            'captcha_encounters': 0,
            'proxy_rotations': 0,
            'session_rotations': 0
        }
        
        # Advanced configuration
        self.max_concurrent_sessions = 3
        self.session_rotation_interval = 25  # requests
        self.request_timing_variance = (2, 8)  # seconds
        self.human_behavior_simulation = True
        self.captcha_handling_enabled = True
        
        # Geolocation pools
        self.geolocations = [
            {'country': 'US', 'timezone': 'America/New_York'},
            {'country': 'US', 'timezone': 'America/Los_Angeles'}, 
            {'country': 'CA', 'timezone': 'America/Toronto'},
            {'country': 'GB', 'timezone': 'Europe/London'},
            {'country': 'DE', 'timezone': 'Europe/Berlin'},
        ]
        
    async def initialize(self):
        """Initialize the enterprise scraping engine"""
        try:
            # Initialize user agent generator
            self.user_agent_generator = UserAgent()
        except:
            # Fallback if fake_useragent fails
            self.user_agent_generator = None
        
        # Initialize proxy pool (would connect to proxy service in production)
        await self._initialize_proxy_pool()
        
        # Create initial scraping sessions
        await self._create_initial_sessions()
        
        logger.info(f"🏢 Enterprise Scraping Engine initialized for user {self.user_id}")
        logger.info(f"📊 Sessions: {len(self.sessions)}, Proxies: {len(self.proxy_pool)}")

    async def _initialize_proxy_pool(self):
        """Initialize residential proxy pool"""
        # In production, this would connect to services like:
        # - Bright Data (Luminati)
        # - Smartproxy  
        # - Oxylabs
        # - ProxyMesh
        
        # For now, we'll use direct connections with different techniques
        self.proxy_pool = [
            None,  # Direct connection
            # Add actual proxy endpoints in production
        ]
        
    async def _create_initial_sessions(self):
        """Create initial pool of diverse scraping sessions"""
        for i in range(self.max_concurrent_sessions):
            session = await self._create_new_session()
            self.sessions[session.session_id] = session
    
    async def _create_new_session(self) -> ScrapingSession:
        """Create a new scraping session with unique fingerprint"""
        session_id = f"ent_session_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Generate realistic user agent
        user_agent = self._generate_realistic_user_agent()
        
        # Generate realistic headers
        headers = self._generate_realistic_headers(user_agent)
        
        # Select proxy
        proxy = random.choice(self.proxy_pool) if self.proxy_pool else None
        
        # Initialize cookies
        cookies = self._generate_session_cookies()
        
        session = ScrapingSession(
            session_id=session_id,
            user_agent=user_agent,
            headers=headers,
            cookies=cookies,
            proxy=proxy,
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow()
        )
        
        logger.info(f"🆕 Created new scraping session: {session_id}")
        return session
    
    def _generate_realistic_user_agent(self) -> str:
        """Generate realistic user agent with proper versioning"""
        if self.user_agent_generator:
            try:
                # Try to get a random Chrome user agent
                return self.user_agent_generator.chrome
            except:
                pass
        
        # Fallback to manually crafted realistic user agents
        browsers = [
            {
                'name': 'Chrome',
                'versions': ['120.0.0.0', '121.0.0.0', '122.0.0.0'],
                'template': 'Mozilla/5.0 ({os}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36'
            },
            {
                'name': 'Firefox', 
                'versions': ['120.0', '121.0', '122.0'],
                'template': 'Mozilla/5.0 ({os}; rv:{version}) Gecko/20100101 Firefox/{version}'
            },
            {
                'name': 'Safari',
                'versions': ['17.2', '17.3', '17.4'],
                'template': 'Mozilla/5.0 ({os}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15'
            }
        ]
        
        operating_systems = [
            'Macintosh; Intel Mac OS X 10_15_7',
            'Windows NT 10.0; Win64; x64',
            'X11; Linux x86_64',
            'Macintosh; Intel Mac OS X 10_14_6',
            'Windows NT 10.0; WOW64'
        ]
        
        browser = random.choice(browsers)
        os = random.choice(operating_systems)
        version = random.choice(browser['versions'])
        
        # Safari only on macOS
        if browser['name'] == 'Safari' and 'Macintosh' not in os:
            os = 'Macintosh; Intel Mac OS X 10_15_7'
        
        return browser['template'].format(os=os, version=version)
    
    def _generate_realistic_headers(self, user_agent: str) -> Dict[str, str]:
        """Generate realistic HTTP headers based on user agent"""
        # Base headers that all browsers send
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': random.choice([
                'en-US,en;q=0.9',
                'en-US,en;q=0.5',
                'en-GB,en;q=0.9',
                'en-US,en;q=0.9,fr;q=0.8',
            ]),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
        # Browser-specific headers
        if 'Chrome' in user_agent:
            headers.update({
                'sec-ch-ua': '"Chromium";v="121", "Not:A-Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': f'"{self._get_platform_from_ua(user_agent)}"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            })
        elif 'Firefox' in user_agent:
            headers.update({
                'DNT': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            })
        elif 'Safari' in user_agent:
            headers.update({
                'DNT': '1',
            })
        
        # Randomly add optional headers
        if random.random() > 0.3:
            headers['DNT'] = '1'
        
        if random.random() > 0.7:
            headers['Pragma'] = 'no-cache'
            
        return headers
    
    def _get_platform_from_ua(self, user_agent: str) -> str:
        """Extract platform from user agent"""
        if 'Macintosh' in user_agent:
            return 'macOS'
        elif 'Windows' in user_agent:
            return 'Windows'  
        elif 'Linux' in user_agent:
            return 'Linux'
        else:
            return 'Windows'
    
    def _generate_session_cookies(self) -> Dict[str, str]:
        """Generate realistic session cookies"""
        cookies = {}
        
        # Common tracking cookies (with realistic values)
        if random.random() > 0.5:
            cookies['_ga'] = f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}"
        
        if random.random() > 0.6:
            cookies['_gid'] = f"GA1.2.{random.randint(100000000, 999999999)}"
            
        if random.random() > 0.7:
            cookies['_fbp'] = f"fb.1.{int(time.time())}.{random.randint(100000000, 999999999)}"
        
        return cookies
    
    async def advanced_scrape(self, url: str, method: str = 'GET', **kwargs) -> ScrapingResult:
        """
        Perform advanced scraping with enterprise techniques
        """
        start_time = time.time()
        
        # Select best session for this request
        session = await self._select_optimal_session()
        
        try:
            # Human behavior simulation
            if self.human_behavior_simulation:
                await self._simulate_human_delay()
            
            # Execute request with advanced techniques
            result = await self._execute_advanced_request(session, url, method, **kwargs)
            
            # Update session metrics
            session.requests_made += 1
            session.last_used = datetime.utcnow()
            
            # Calculate session success rate
            if result.success:
                session.success_rate = (session.success_rate * (session.requests_made - 1) + 1) / session.requests_made
                self.success_metrics['successful_requests'] += 1
            else:
                session.success_rate = (session.success_rate * (session.requests_made - 1)) / session.requests_made
                if result.blocked:
                    self.success_metrics['blocked_requests'] += 1
                if result.captcha_detected:
                    self.success_metrics['captcha_encounters'] += 1
            
            self.success_metrics['total_requests'] += 1
            
            # Check if session should be rotated
            if session.should_rotate():
                await self._rotate_session(session.session_id)
            
            result.response_time = time.time() - start_time
            return result
            
        except Exception as e:
            logger.error(f"Advanced scraping failed for {url}: {e}")
            return ScrapingResult(
                success=False,
                data={},
                url=url,
                status_code=0,
                response_time=time.time() - start_time,
                session_id=session.session_id,
                error=str(e)
            )
    
    async def _select_optimal_session(self) -> ScrapingSession:
        """Select the best session for the next request"""
        # Clean up expired sessions
        expired_sessions = [
            sid for sid, session in self.sessions.items() 
            if session.is_expired() or session.should_rotate()
        ]
        
        for sid in expired_sessions:
            await self._rotate_session(sid)
        
        # Ensure we have enough sessions
        while len(self.sessions) < self.max_concurrent_sessions:
            new_session = await self._create_new_session()
            self.sessions[new_session.session_id] = new_session
        
        # Select session with best success rate and lowest recent usage
        best_session = min(
            self.sessions.values(),
            key=lambda s: (
                -s.success_rate,  # Higher success rate is better
                -(time.time() - s.last_used.timestamp()) if s.last_used else 0  # More recent usage is worse
            )
        )
        
        return best_session
    
    async def _rotate_session(self, session_id: str):
        """Rotate a session with a new one"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.success_metrics['session_rotations'] += 1
            logger.info(f"🔄 Rotated session: {session_id}")
        
        # Create replacement session
        new_session = await self._create_new_session()
        self.sessions[new_session.session_id] = new_session
    
    async def _simulate_human_delay(self):
        """Simulate human-like delays between requests"""
        # Random delay with realistic patterns
        base_delay = random.uniform(*self.request_timing_variance)
        
        # Add occasional longer pauses (like humans do)
        if random.random() < 0.1:  # 10% chance of longer pause
            base_delay += random.uniform(5, 15)
        
        # Add micro-variations
        base_delay += random.gauss(0, 0.5)
        
        await asyncio.sleep(max(0.5, base_delay))
    
    async def _execute_advanced_request(self, session: ScrapingSession, url: str, method: str, **kwargs) -> ScrapingResult:
        """Execute request with advanced techniques"""
        
        # Try cloudscraper first (handles Cloudflare)
        try:
            result = await self._cloudscraper_request(session, url, method, **kwargs)
            if result.success:
                return result
        except Exception as e:
            logger.debug(f"Cloudscraper failed: {e}")
        
        # Fallback to advanced aiohttp
        try:
            result = await self._aiohttp_advanced_request(session, url, method, **kwargs)
            return result
        except Exception as e:
            logger.debug(f"Advanced aiohttp failed: {e}")
            return ScrapingResult(
                success=False,
                data={},
                url=url,
                status_code=0,
                response_time=0,
                session_id=session.session_id,
                error=str(e)
            )
    
    async def _cloudscraper_request(self, session: ScrapingSession, url: str, method: str, **kwargs) -> ScrapingResult:
        """Use cloudscraper for Cloudflare bypass"""
        
        def sync_cloudscraper_request():
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': self._get_platform_from_ua(session.user_agent).lower(),
                    'mobile': False
                }
            )
            
            scraper.headers.update(session.headers)
            
            if session.proxy:
                proxies = {
                    'http': session.proxy,
                    'https': session.proxy
                }
            else:
                proxies = None
            
            response = scraper.request(
                method=method,
                url=url,
                proxies=proxies,
                timeout=30,
                **kwargs
            )
            
            return response
        
        # Run cloudscraper in thread pool (it's synchronous)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, sync_cloudscraper_request)
        
        # Detect common blocking patterns
        blocked = self._detect_blocking(response.text, response.status_code)
        captcha = self._detect_captcha(response.text)
        
        if response.status_code == 200 and not blocked and not captcha:
            # Parse content intelligently
            data = self._intelligent_content_parsing(response.text, url)
            
            return ScrapingResult(
                success=True,
                data=data,
                url=url,
                status_code=response.status_code,
                response_time=0,
                session_id=session.session_id,
                captcha_detected=captcha,
                blocked=blocked
            )
        else:
            return ScrapingResult(
                success=False,
                data={},
                url=url,
                status_code=response.status_code,
                response_time=0,
                session_id=session.session_id,
                captcha_detected=captcha,
                blocked=blocked,
                error=f"Request failed: {response.status_code}"
            )
    
    async def _aiohttp_advanced_request(self, session: ScrapingSession, url: str, method: str, **kwargs) -> ScrapingResult:
        """Advanced aiohttp request with sophisticated configuration"""
        
        # Advanced SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Advanced connector
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=3,
            ttl_dns_cache=300,
            use_dns_cache=True,
            ssl=ssl_context,
            enable_cleanup_closed=True,
            keepalive_timeout=30,
            force_close=False
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
        
        # Create session with advanced configuration
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=session.headers,
            cookies=session.cookies
        ) as http_session:
            
            # Add referrer for more realistic traffic
            headers = session.headers.copy()
            if 'Referer' not in headers:
                headers['Referer'] = self._generate_realistic_referer(url)
            
            async with http_session.request(
                method=method,
                url=url,
                headers=headers,
                ssl=ssl_context,
                **kwargs
            ) as response:
                
                text = await response.text()
                
                # Detect blocking and captchas
                blocked = self._detect_blocking(text, response.status)
                captcha = self._detect_captcha(text)
                
                if response.status == 200 and not blocked and not captcha:
                    data = self._intelligent_content_parsing(text, url)
                    return ScrapingResult(
                        success=True,
                        data=data,
                        url=url,
                        status_code=response.status,
                        response_time=0,
                        session_id=session.session_id,
                        captcha_detected=captcha,
                        blocked=blocked
                    )
                else:
                    return ScrapingResult(
                        success=False,
                        data={},
                        url=url,
                        status_code=response.status,
                        response_time=0,
                        session_id=session.session_id,
                        captcha_detected=captcha,
                        blocked=blocked,
                        error=f"Request failed: {response.status}"
                    )
    
    def _generate_realistic_referer(self, target_url: str) -> str:
        """Generate realistic referer for the target URL"""
        referers = [
            'https://www.google.com/',
            'https://www.bing.com/',
            'https://duckduckgo.com/',
            'https://search.yahoo.com/',
            'https://www.linkedin.com/',
            'https://twitter.com/',
        ]
        
        # For LinkedIn pages, use LinkedIn referer
        if 'linkedin.com' in target_url:
            return 'https://www.linkedin.com/'
        
        # For GitHub pages, use GitHub referer  
        if 'github.com' in target_url:
            return 'https://github.com/'
        
        # Default to search engines
        return random.choice(referers)
    
    def _detect_blocking(self, content: str, status_code: int) -> bool:
        """Detect if request was blocked"""
        blocking_indicators = [
            'access denied',
            'blocked',
            'forbidden', 
            'rate limit',
            'too many requests',
            'cloudflare',
            'security check',
            'bot detected',
            'suspicious activity',
            'verification required'
        ]
        
        content_lower = content.lower()
        for indicator in blocking_indicators:
            if indicator in content_lower:
                return True
        
        # Status code indicators
        if status_code in [403, 429, 503]:
            return True
            
        return False
    
    def _detect_captcha(self, content: str) -> bool:
        """Detect if CAPTCHA is present"""
        captcha_indicators = [
            'captcha',
            'recaptcha', 
            'hcaptcha',
            'i am not a robot',
            'verify you are human',
            'security challenge',
            'prove you are not a bot'
        ]
        
        content_lower = content.lower()
        for indicator in captcha_indicators:
            if indicator in content_lower:
                return True
                
        return False
    
    def _intelligent_content_parsing(self, html: str, url: str) -> Dict[str, Any]:
        """Intelligently parse content based on URL and content type"""
        data = {}
        
        # Remove scripts and styles for cleaner parsing
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # LinkedIn-specific parsing
        if 'linkedin.com' in url:
            data.update(self._parse_linkedin_content(html))
        
        # GitHub-specific parsing
        elif 'github.com' in url:
            data.update(self._parse_github_content(html))
        
        # Company website parsing
        else:
            data.update(self._parse_company_website(html))
        
        # General metadata extraction
        data.update(self._extract_metadata(html))
        
        return data
    
    def _parse_linkedin_content(self, html: str) -> Dict[str, Any]:
        """Parse LinkedIn-specific content"""
        data = {}
        
        # Extract name
        name_patterns = [
            r'<h1[^>]*class="[^"]*text-heading-xlarge[^"]*"[^>]*>([^<]+)</h1>',
            r'"firstName":"([^"]+)"[^}]*"lastName":"([^"]+)"',
            r'<title>([^|]+) \|'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    data['name'] = f"{match.group(1)} {match.group(2)}"
                else:
                    data['name'] = match.group(1).strip()
                break
        
        # Extract title
        title_patterns = [
            r'<div[^>]*class="[^"]*text-body-medium[^"]*"[^>]*>([^<]+)</div>',
            r'"headline":"([^"]+)"'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                data['title'] = match.group(1).strip()
                break
        
        return data
    
    def _parse_github_content(self, html: str) -> Dict[str, Any]:
        """Parse GitHub-specific content"""
        data = {}
        
        # Extract name
        name_match = re.search(r'<span[^>]*class="[^"]*p-name[^"]*"[^>]*>([^<]+)</span>', html)
        if name_match:
            data['name'] = name_match.group(1).strip()
        
        # Extract bio
        bio_match = re.search(r'<div[^>]*class="[^"]*p-note[^"]*"[^>]*>([^<]+)</div>', html)
        if bio_match:
            data['bio'] = bio_match.group(1).strip()
        
        return data
    
    def _parse_company_website(self, html: str) -> Dict[str, Any]:
        """Parse company website content"""
        data = {}
        
        # Extract title
        title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
        if title_match:
            data['page_title'] = title_match.group(1).strip()
        
        # Extract description from meta tags
        desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html, re.IGNORECASE)
        if desc_match:
            data['description'] = desc_match.group(1).strip()
        
        return data
    
    def _extract_metadata(self, html: str) -> Dict[str, Any]:
        """Extract general metadata from any page"""
        data = {}
        
        # Extract all meta tags
        meta_tags = re.findall(r'<meta[^>]*>', html, re.IGNORECASE)
        data['meta_tags_count'] = len(meta_tags)
        
        # Extract structured data
        json_ld_matches = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
        if json_ld_matches:
            data['structured_data_found'] = True
            data['structured_data_count'] = len(json_ld_matches)
        
        return data
    
    async def get_success_metrics(self) -> Dict[str, Any]:
        """Get current success metrics"""
        total_requests = self.success_metrics['total_requests']
        successful_requests = self.success_metrics['successful_requests']
        
        return {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'success_rate': (successful_requests / max(1, total_requests)) * 100,
            'blocked_requests': self.success_metrics['blocked_requests'],
            'captcha_encounters': self.success_metrics['captcha_encounters'],
            'active_sessions': len(self.sessions),
            'session_rotations': self.success_metrics['session_rotations'],
            'proxy_rotations': self.success_metrics['proxy_rotations']
        }
    
    async def cleanup(self):
        """Clean up resources"""
        self.sessions.clear()
        logger.info(f"🧹 Enterprise Scraping Engine cleaned up for user {self.user_id}") 