"""
Enhanced Contact Enrichment System
=================================
Comprehensive enrichment that actually works by using multiple data sources
and fixing the web scraping issues.
"""

import asyncio
import aiohttp
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
import time
import random
from urllib.parse import urljoin, urlparse
import anthropic
import os
import ssl

from utils.logging import structured_logger as logger
from config.settings import ANTHROPIC_API_KEY

# Claude 4 Opus - now working with proper API key!
CLAUDE_MODEL = 'claude-opus-4-20250514'

@dataclass
class EnhancedEnrichmentResult:
    """Comprehensive enrichment result with extensive professional intelligence"""
    email: str
    confidence_score: float
    person_data: Dict[str, Any]
    company_data: Dict[str, Any]
    relationship_intelligence: Dict[str, Any]
    actionable_insights: Dict[str, Any]
    data_sources: List[str]
    enrichment_timestamp: datetime
    error: Optional[str] = None

class EnhancedContactEnricher:
    """
    Enhanced contact enricher that actually works
    Uses multiple data sources and robust web scraping
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        # Always get API key fresh from environment at runtime
        api_key = os.getenv('ANTHROPIC_API_KEY') or ANTHROPIC_API_KEY
        self.claude_client = anthropic.Anthropic(api_key=api_key) if api_key else None
        self.session = None
        self.browser = None
        self.working_claude_model = None  # Cache working model
        
        # Log the API key status for debugging
        if api_key:
            logger.info(f"Claude client initialized with API key: {api_key[:20]}...{api_key[-10:]}")
        else:
            logger.warning("No Claude API key found - Claude features will be disabled")
        
    async def initialize(self):
        """Initialize with robust web scraping capabilities"""
        import ssl
        
        # Create SSL context with more permissive settings for web scraping
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Enhanced HTTP session with better headers and settings
        connector = aiohttp.TCPConnector(
            limit=10, 
            limit_per_host=2,
            ttl_dns_cache=300,
            use_dns_cache=True,
            ssl=ssl_context,  # Add SSL context
            enable_cleanup_closed=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=10)
        
        # Rotate through multiple realistic user agents
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
        
        logger.info(f"Enhanced enricher initialized for user {self.user_id}")
    
    async def enrich_contact(self, contact: Dict, user_emails: List[Dict] = None) -> EnhancedEnrichmentResult:
        """
        Enrich contact using multiple data sources
        
        Args:
            contact: Contact data with email
            user_emails: User's emails for content analysis
            
        Returns:
            Enhanced enrichment result
        """
        email = contact.get('email', '').strip().lower()
        if not email:
            return EnhancedEnrichmentResult(
                email=email,
                confidence_score=0.0,
                person_data={},
                company_data={},
                relationship_intelligence={},
                actionable_insights={},
                data_sources=[],
                enrichment_timestamp=datetime.utcnow(),
                error="No email provided"
            )
        
        logger.info(f"Starting enhanced enrichment for {email}")
        
        # Initialize data containers
        person_data = {}
        company_data = {}
        data_sources = []
        
        try:
            # 1. EMAIL SIGNATURE ANALYSIS (Primary source - most reliable)
            signature_data = await self._analyze_email_signatures(email, user_emails or [])
            if signature_data['person'] or signature_data['company']:
                person_data.update(signature_data['person'])
                company_data.update(signature_data['company'])
                data_sources.append('email_signatures')
                logger.info(f"✅ Extracted data from email signatures for {email}")
            
            # 2. EMAIL CONTENT ANALYSIS (Secondary source)
            content_data = await self._analyze_email_content(email, user_emails or [])
            if content_data['person'] or content_data['company']:
                person_data.update(content_data['person'])
                company_data.update(content_data['company'])
                data_sources.append('email_content')
                logger.info(f"✅ Extracted data from email content for {email}")
            
            # 3. DOMAIN INTELLIGENCE (Tertiary source)
            domain = email.split('@')[1] if '@' in email else None
            if domain and not self._is_generic_domain(domain):
                domain_data = await self._analyze_domain_intelligence(domain)
                if domain_data:
                    company_data.update(domain_data)
                    data_sources.append('domain_intelligence')
                    logger.info(f"✅ Extracted domain intelligence for {domain}")
            
            # 4. ENHANCED WEB SCRAPING (Only if we have partial data to verify)
            if person_data.get('name') or company_data.get('name'):
                web_data = await self._enhanced_web_scraping(person_data, company_data, domain)
                if web_data['person'] or web_data['company']:
                    person_data.update(web_data['person'])
                    company_data.update(web_data['company'])
                    data_sources.append('web_scraping')
                    logger.info(f"✅ Enhanced with web scraping data for {email}")
            
            # 5. CLAUDE SYNTHESIS (Final processing)
            if person_data or company_data:
                synthesized_data = await self._claude_data_synthesis(
                    email, person_data, company_data, data_sources
                )
                person_data = synthesized_data['person']
                company_data = synthesized_data['company']
                data_sources.append('claude_synthesis')
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(person_data, company_data, data_sources)
            
            result = EnhancedEnrichmentResult(
                email=email,
                confidence_score=confidence_score,
                person_data=person_data,
                company_data=company_data,
                relationship_intelligence=synthesized_data.get('relationship_intelligence', {}),
                actionable_insights=synthesized_data.get('actionable_insights', {}),
                data_sources=data_sources,
                enrichment_timestamp=datetime.utcnow()
            )
            
            logger.info(f"✅ Enrichment completed for {email} - Confidence: {confidence_score:.1%}, Sources: {len(data_sources)}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Enrichment failed for {email}: {str(e)}")
            return EnhancedEnrichmentResult(
                email=email,
                confidence_score=0.0,
                person_data={},
                company_data={},
                relationship_intelligence={},
                actionable_insights={},
                data_sources=[],
                enrichment_timestamp=datetime.utcnow(),
                error=str(e)
            )
    
    async def _analyze_email_signatures(self, email: str, user_emails: List[Dict]) -> Dict:
        """
        Analyze email signatures for contact information
        This is often the most reliable source of structured data
        """
        person_data = {}
        company_data = {}
        
        # Find emails from/to this person
        relevant_emails = [
            e for e in user_emails 
            if email.lower() in (e.get('sender', '') + ' ' + ' '.join(e.get('recipients', []))).lower()
        ]
        
        if not relevant_emails:
            return {'person': person_data, 'company': company_data}
        
        # Extract signatures from email bodies
        signatures = []
        for em in relevant_emails[:10]:  # Check last 10 emails
            body = em.get('body_text', '') or em.get('body_html', '')
            if body:
                signature = self._extract_signature_from_email(body)
                if signature:
                    signatures.append(signature)
        
        if not signatures:
            return {'person': person_data, 'company': company_data}
        
        # Use Claude to analyze signatures
        if self.claude_client:
            try:
                signature_text = '\n---\n'.join(signatures[:5])  # Max 5 signatures
                
                prompt = f"""
Analyze these email signatures to extract contact information:

EMAIL SIGNATURES:
{signature_text}

Extract and format as JSON:
{{
    "person": {{
        "name": "Full Name",
        "title": "Job Title",
        "phone": "Phone Number",
        "mobile": "Mobile Number"
    }},
    "company": {{
        "name": "Company Name",
        "website": "Company Website",
        "address": "Company Address",
        "industry": "Industry/Sector"
    }}
}}

Only include fields where you have high confidence. Use empty string if uncertain.
"""

                working_model = CLAUDE_MODEL
                response = await asyncio.to_thread(
                    self.claude_client.messages.create,
                    model=working_model,
                    max_tokens=1000,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                result = self._parse_json_response(response.content[0].text)
                if result:
                    person_data = result.get('person', {})
                    company_data = result.get('company', {})
                    
            except Exception as e:
                logger.error(f"Claude signature analysis failed: {e}")
        
        return {'person': person_data, 'company': company_data}
    
    def _extract_signature_from_email(self, body: str) -> Optional[str]:
        """Extract email signature from email body"""
        # Common signature separators
        separators = [
            '--',
            '___',
            'Best regards',
            'Best,',
            'Regards,',
            'Sincerely,',
            'Thanks,',
            'Cheers,',
            '\n\n\n'
        ]
        
        # Split by separators and take the last part (likely signature)
        for separator in separators:
            if separator in body:
                parts = body.split(separator)
                if len(parts) > 1:
                    signature = parts[-1].strip()
                    # Signature should be short and contain contact info patterns
                    if 20 < len(signature) < 500 and self._looks_like_signature(signature):
                        return signature
        
        # Fallback: take last paragraph if it looks like a signature
        lines = body.strip().split('\n')
        if len(lines) > 3:
            last_paragraph = '\n'.join(lines[-5:]).strip()
            if self._looks_like_signature(last_paragraph):
                return last_paragraph
        
        return None
    
    def _looks_like_signature(self, text: str) -> bool:
        """Check if text looks like an email signature"""
        signature_indicators = [
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # Phone numbers
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\bwww\.[^\s]+\b',  # Website
            r'\bhttps?://[^\s]+\b',  # URL
            r'\b(CEO|CTO|VP|Director|Manager|President)\b',  # Titles
        ]
        
        matches = sum(1 for pattern in signature_indicators if re.search(pattern, text, re.IGNORECASE))
        return matches >= 2
    
    async def _analyze_email_content(self, email: str, user_emails: List[Dict]) -> Dict:
        """
        Analyze email content for contextual information about the person and company
        """
        person_data = {}
        company_data = {}
        
        # Find emails from/to this person
        relevant_emails = [
            e for e in user_emails 
            if email.lower() in (e.get('sender', '') + ' ' + ' '.join(e.get('recipients', []))).lower()
        ]
        
        if not relevant_emails:
            return {'person': person_data, 'company': company_data}
        
        # Combine email content
        combined_content = []
        for em in relevant_emails[:15]:  # Analyze up to 15 emails
            subject = em.get('subject', '')
            body = em.get('body_text', '') or em.get('body_html', '')
            if subject or body:
                combined_content.append(f"Subject: {subject}\nBody: {body[:500]}...")
        
        if not combined_content or not self.claude_client:
            return {'person': person_data, 'company': company_data}
        
        try:
            content_text = '\n---\n'.join(combined_content[:10])  # Max 10 emails
            
            prompt = f"""
Analyze these email exchanges to extract information about the person and their company:

EMAIL EXCHANGES:
{content_text}

Based on the content, context, and communication patterns, extract:

{{
    "person": {{
        "name": "Inferred full name if mentioned",
        "title": "Job title/role if evident",
        "expertise": "Areas of expertise/focus",
        "communication_style": "Professional communication style",
        "interests": "Professional interests mentioned"
    }},
    "company": {{
        "name": "Company name if mentioned",
        "industry": "Industry/sector if evident",
        "size": "Company size indicators",
        "products": "Products/services mentioned",
        "culture": "Company culture indicators"
    }}
}}

Only include fields where you have reasonable confidence based on the content.
"""

            working_model = CLAUDE_MODEL
            response = await asyncio.to_thread(
                self.claude_client.messages.create,
                model=working_model,
                max_tokens=1000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = self._parse_json_response(response.content[0].text)
            if result:
                person_data = result.get('person', {})
                company_data = result.get('company', {})
                
        except Exception as e:
            logger.error(f"Claude content analysis failed: {e}")
        
        return {'person': person_data, 'company': company_data}
    
    async def _analyze_domain_intelligence(self, domain: str) -> Dict:
        """
        Analyze domain for company intelligence with robust fallback strategies
        """
        if not domain or self._is_generic_domain(domain):
            return {}
        
        logger.info(f"  📈 Analyzing domain: {domain}")
        
        # Try multiple strategies for domain intelligence
        strategies = [
            self._fetch_domain_info,
            self._get_domain_via_whois_search,
            self._get_company_via_web_search
        ]
        
        for strategy in strategies:
            try:
                company_data = await strategy(domain)
                if company_data:
                    logger.info(f"  ✅ Successfully got domain data for {domain} via {strategy.__name__}")
                    return {
                        'name': company_data.get('company_name_from_site') or self._domain_to_company_name(domain),
                        'website': f"https://{domain}",
                        'description': company_data.get('description', ''),
                        'industry': company_data.get('industry', ''),
                        'title': company_data.get('website_title', ''),
                        'source': 'domain_analysis'
                    }
            except Exception as e:
                logger.debug(f"Strategy {strategy.__name__} failed for {domain}: {e}")
                continue
        
        # If all strategies fail, return basic company data
        logger.debug(f"All strategies failed for {domain}, returning basic data")
        return {
            'name': self._domain_to_company_name(domain),
            'website': f"https://{domain}",
            'source': 'domain_fallback'
        }
    
    async def _get_domain_via_whois_search(self, domain: str) -> Dict:
        """
        Get domain information via web search (fallback strategy)
        """
        try:
            search_query = f"{domain} company about"
            encoded_query = search_query.replace(' ', '+')
            
            await asyncio.sleep(random.uniform(1, 2))
            
            async with self.session.get(
                f"https://www.google.com/search?q={encoded_query}",
                headers={'Referer': 'https://www.google.com/'}, 
                ssl=False
            ) as response:
                
                if response.status == 200:
                    html = await response.text()
                    
                    # Extract company info from search results
                    return self._extract_company_from_search_results(html, domain)
                    
        except Exception as e:
            logger.debug(f"Web search strategy failed for {domain}: {e}")
            return {}
        
        return {}
    
    async def _get_company_via_web_search(self, domain: str) -> Dict:
        """
        Alternative web search strategy
        """
        try:
            company_name = self._domain_to_company_name(domain)
            search_query = f'"{company_name}" company'
            encoded_query = search_query.replace(' ', '+').replace('"', '%22')
            
            await asyncio.sleep(random.uniform(1, 2))
            
            async with self.session.get(
                f"https://www.google.com/search?q={encoded_query}",
                headers={'Referer': 'https://www.google.com/'}, 
                ssl=False
            ) as response:
                
                if response.status == 200:
                    html = await response.text()
                    return self._extract_company_from_search_results(html, domain)
                    
        except Exception as e:
            logger.debug(f"Alternative web search failed for {domain}: {e}")
            return {}
        
        return {}
    
    def _extract_company_from_search_results(self, html: str, domain: str) -> Dict:
        """
        Extract company information from Google search results
        """
        data = {}
        
        # Look for company descriptions in search snippets
        snippet_patterns = [
            rf'{re.escape(domain)}[^<]*?-\s*([^<\n.!?]{20,100})',
            rf'{re.escape(domain.split(".")[0])}[^<]*?(?:is|provides|offers|specializes in)\s*([^<\n.!?]{20,100})',
        ]
        
        for pattern in snippet_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                data['description'] = match.group(1).strip()
                break
        
        # Look for industry keywords
        industry_keywords = [
            'technology', 'software', 'finance', 'healthcare', 'education', 
            'startup', 'venture capital', 'consulting', 'marketing', 'e-commerce'
        ]
        
        for keyword in industry_keywords:
            if keyword in html.lower():
                data['industry'] = keyword.title()
                break
        
        return data
    
    async def _fetch_domain_info(self, domain: str) -> Dict:
        """
        Fetch basic information from company domain with robust scraping
        """
        if not self.session:
            await self.initialize()
        
        urls_to_try = [
            f"https://www.{domain}",
            f"https://{domain}",
            f"https://www.{domain}/about",
            f"https://{domain}/about"
        ]
        
        for url in urls_to_try:
            try:
                # Add random delay to avoid detection
                await asyncio.sleep(random.uniform(1, 3))
                
                # Rotate user agent
                headers = {
                    'User-Agent': random.choice([
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    ]),
                    'Referer': 'https://www.google.com/',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
                
                async with self.session.get(url, headers=headers, ssl=False) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._extract_info_from_html(html)
                    else:
                        logger.debug(f"HTTP {response.status} for {url}")
                        
            except asyncio.TimeoutError:
                logger.debug(f"Timeout fetching {url}")
                continue
            except aiohttp.ClientConnectorError as e:
                logger.debug(f"Connection error for {url}: {e}")
                continue
            except aiohttp.ClientSSLError as e:
                logger.debug(f"SSL error for {url}: {e}")
                continue
            except aiohttp.ClientResponseError as e:
                logger.debug(f"Response error for {url}: {e}")
                continue
            except Exception as e:
                # More informative logging for URL fetch failures
                error_type = type(e).__name__
                if hasattr(e, 'url') and str(e.url) != url:
                    logger.debug(f"Failed to fetch {url} (redirected to {e.url}): {error_type}: {e}")
                else:
                    logger.debug(f"Failed to fetch {url}: {error_type}: {e}")
                continue
        
        logger.debug(f"Unable to fetch any content for domain: {domain}")
        return {}
    
    def _extract_info_from_html(self, html: str) -> Dict:
        """Extract company information from HTML"""
        data = {}
        
        # Extract title
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        if title_match:
            data['website_title'] = title_match.group(1).strip()
        
        # Extract meta description
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if desc_match:
            data['description'] = desc_match.group(1).strip()
        
        # Look for company name patterns
        company_patterns = [
            r'<h1[^>]*>([^<]+(?:Company|Corp|Inc|Ltd|LLC)[^<]*)</h1>',
            r'<h2[^>]*>([^<]+(?:Company|Corp|Inc|Ltd|LLC)[^<]*)</h2>',
            r'(?:Company|About)\s*:\s*([^<\n]+)',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                data['company_name_from_site'] = match.group(1).strip()
                break
        
        return data
    
    async def _enhanced_web_scraping(self, person_data: Dict, company_data: Dict, domain: str) -> Dict:
        """
        Enhanced web scraping with better anti-detection when we have some data to verify
        """
        enhanced_person = {}
        enhanced_company = {}
        
        # Only do web scraping if we have a name to search for
        person_name = person_data.get('name')
        company_name = company_data.get('name')
        
        if not person_name and not company_name:
            return {'person': enhanced_person, 'company': enhanced_company}
        
        # Search for LinkedIn profile (more targeted than before)
        if person_name:
            linkedin_data = await self._search_linkedin_targeted(person_name, company_name)
            if linkedin_data:
                enhanced_person.update(linkedin_data)
        
        # Search for company information
        if company_name:
            company_web_data = await self._search_company_info(company_name, domain)
            if company_web_data:
                enhanced_company.update(company_web_data)
        
        return {'person': enhanced_person, 'company': enhanced_company}
    
    async def _search_linkedin_targeted(self, person_name: str, company_name: str = None) -> Dict:
        """Targeted LinkedIn search with better success rate"""
        try:
            search_query = f'"{person_name}"'
            if company_name:
                search_query += f' "{company_name}"'
            search_query += ' site:linkedin.com'
            
            encoded_query = search_query.replace(' ', '+').replace('"', '%22')
            
            # Use Google to find LinkedIn profiles
            await asyncio.sleep(random.uniform(2, 4))  # Random delay
            
            async with self.session.get(
                f"https://www.google.com/search?q={encoded_query}",
                headers={'Referer': 'https://www.google.com/'}
            ) as response:
                
                if response.status == 200:
                    html = await response.text()
                    
                    # Extract LinkedIn profile URLs
                    linkedin_urls = re.findall(r'https://[^"\']*linkedin\.com/in/[^"\']*', html)
                    
                    if linkedin_urls:
                        # Extract basic info from the search result snippet
                        return await self._extract_linkedin_snippet_info(html, person_name)
            
        except Exception as e:
            logger.debug(f"LinkedIn search failed: {e}")
        
        return {}
    
    async def _extract_linkedin_snippet_info(self, html: str, person_name: str) -> Dict:
        """Extract LinkedIn info from Google search snippets"""
        data = {}
        
        # Look for job title patterns in snippets
        title_patterns = [
            rf'{re.escape(person_name)}[^<]*?(?:is|works as|employed as)\s*([^<\n,]+)',
            rf'([^<\n,]+)\s*at\s*[^<\n]+{re.escape(person_name)}',
            rf'{re.escape(person_name)}[^<]*?([A-Z][^<\n,]*(?:Manager|Director|VP|CEO|CTO|Engineer|Developer|Analyst))'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                data['title'] = match.group(1).strip()
                break
        
        return data
    
    async def _search_company_info(self, company_name: str, domain: str) -> Dict:
        """Search for additional company information"""
        data = {}
        
        try:
            search_query = f'"{company_name}" company about'
            encoded_query = search_query.replace(' ', '+').replace('"', '%22')
            
            await asyncio.sleep(random.uniform(2, 4))
            
            async with self.session.get(
                f"https://www.google.com/search?q={encoded_query}",
                headers={'Referer': 'https://www.google.com/'}
            ) as response:
                
                if response.status == 200:
                    html = await response.text()
                    
                    # Extract company info from snippets
                    industry_patterns = [
                        rf'{re.escape(company_name)}[^<]*?(?:is|specializes in|focuses on)\s*([^<\n.]+)',
                        rf'([^<\n.]+)\s*company\s*{re.escape(company_name)}',
                    ]
                    
                    for pattern in industry_patterns:
                        match = re.search(pattern, html, re.IGNORECASE)
                        if match:
                            data['industry_context'] = match.group(1).strip()
                            break
        
        except Exception as e:
            logger.debug(f"Company search failed: {e}")
        
        return data
    
    async def _claude_data_synthesis(self, email: str, person_data: Dict, 
                                   company_data: Dict, data_sources: List[str]) -> Dict:
        """
        Use Claude to synthesize and enhance all collected data into comprehensive professional intelligence
        """
        if not self.claude_client:
            return {'person': person_data, 'company': company_data}
        
        try:
            prompt = f"""
You are a professional intelligence analyst. Synthesize this data into comprehensive professional intelligence:

EMAIL: {email}
DATA SOURCES: {', '.join(data_sources)}

RAW PERSON DATA:
{json.dumps(person_data, indent=2)}

RAW COMPANY DATA:
{json.dumps(company_data, indent=2)}

Extract MAXIMUM intelligence and provide a comprehensive professional profile:

{{
    "person": {{
        "name": "Full professional name",
        "current_title": "Current role/position",
        "seniority_level": "junior/mid/senior/executive/founder",
        "career_stage": "early-career/growth/established/veteran/executive",
        
        "professional_background": {{
            "previous_companies": ["Company 1", "Company 2"],
            "career_progression": "Brief career journey summary",
            "years_experience": "estimated total experience",
            "industry_expertise": ["primary industry", "secondary industry"],
            "functional_expertise": ["function 1", "function 2"],
            "education_background": "university/degree if found",
            "certifications": ["cert 1", "cert 2"] 
        }},
        
        "current_focus": {{
            "investment_thesis": "if investor - what they invest in",
            "portfolio_companies": ["company 1", "company 2"] if investor,
            "key_initiatives": ["current projects/focus areas"],
            "speaking_topics": ["areas of expertise they speak about"],
            "content_themes": ["topics they write/post about"]
        }},
        
        "network_intelligence": {{
            "board_positions": ["company board positions"],
            "advisor_roles": ["companies they advise"],
            "professional_associations": ["industry groups"],
            "conference_appearances": ["events they speak at"],
            "media_mentions": ["publications that quote them"]
        }},
        
        "communication_insights": {{
            "communication_style": "professional/casual/formal/technical",
            "response_patterns": "quick/deliberate/formal",
            "preferred_topics": ["business topics they engage with"],
            "social_presence": "active/minimal/thought-leader",
            "outreach_timing": "best times/approaches for contact"
        }},
        
        "value_proposition": {{
            "what_they_offer": "value they can provide",
            "decision_authority": "what they can decide on",
            "budget_authority": "estimated budget influence",
            "network_value": "valuable connections they have",
            "expertise_value": "knowledge they can share"
        }}
    }},
    
    "company": {{
        "name": "Official company name",
        "industry": "Primary industry sector",
        "sub_industry": "Specific niche/focus area",
        
        "company_profile": {{
            "business_model": "B2B/B2C/marketplace/SaaS/etc",
            "revenue_model": "subscription/transaction/licensing/etc",
            "target_market": "enterprise/SMB/consumer/etc",
            "company_stage": "seed/growth/mature/public/etc",
            "employee_count": "estimated size range",
            "headquarters": "primary location",
            "founded_year": "year established"
        }},
        
        "financial_intelligence": {{
            "funding_status": "bootstrapped/funded/public",
            "funding_rounds": ["Series A $XM", "Series B $XM"],
            "key_investors": ["investor 1", "investor 2"],
            "estimated_valuation": "if available",
            "revenue_estimates": "if available",
            "growth_trajectory": "growing/stable/declining"
        }},
        
        "market_position": {{
            "competitive_landscape": "leader/challenger/niche/startup",
            "key_competitors": ["competitor 1", "competitor 2"],
            "differentiation": "what makes them unique",
            "market_trends": "industry trends affecting them",
            "growth_opportunities": "expansion areas"
        }},
        
        "technology_profile": {{
            "tech_stack": ["primary technologies used"],
            "digital_maturity": "traditional/digital-native/tech-forward",
            "innovation_focus": ["AI/cloud/mobile/etc"],
            "technology_partnerships": ["key tech partners"],
            "digital_transformation": "stage of digital adoption"
        }},
        
        "business_intelligence": {{
            "key_products": ["main products/services"],
            "customer_base": "types of customers",
            "geographic_presence": "markets they serve",
            "partnership_strategy": "how they work with partners",
            "expansion_plans": "growth strategies",
            "acquisition_history": ["companies acquired"],
            "exit_strategy": "IPO/acquisition potential"
        }},
        
        "decision_making": {{
            "decision_makers": ["key executives by function"],
            "procurement_process": "how they buy",
            "budget_cycles": "when they make purchasing decisions",
            "vendor_preferences": "types of partners they work with",
            "evaluation_criteria": "what they value in partners"
        }}
    }},
    
    "relationship_intelligence": {{
        "engagement_level": "high/medium/low based on email frequency",
        "relationship_stage": "cold/warm/active/partnership",
        "mutual_connections": ["shared network if identified"],
        "collaboration_opportunities": ["potential areas to work together"],
        "referral_potential": "likelihood they'd make introductions",
        "influence_score": "how influential they are in their network"
    }},
    
    "actionable_insights": {{
        "best_approach": "how to most effectively engage them",
        "value_propositions": ["what would interest them most"],
        "timing_considerations": "when to reach out",
        "conversation_starters": ["relevant topics to discuss"],
        "meeting_likelihood": "probability they'd take a meeting",
        "decision_timeline": "how quickly they typically make decisions"
    }}
}}

Be thorough and intelligent. Extract every possible insight. Make educated inferences where data suggests patterns. This intelligence will drive important business decisions.
"""

            working_model = CLAUDE_MODEL
            response = await asyncio.to_thread(
                self.claude_client.messages.create,
                model=working_model,
                max_tokens=4000,  # Increased for richer output
                temperature=0.3,   # Slightly higher for more creative synthesis
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = self._parse_json_response(response.content[0].text)
            if result:
                return {
                    'person': result.get('person', person_data),
                    'company': result.get('company', company_data),
                    'relationship_intelligence': result.get('relationship_intelligence', {}),
                    'actionable_insights': result.get('actionable_insights', {})
                }
                
        except Exception as e:
            logger.error(f"Claude synthesis failed: {e}")
        
        return {'person': person_data, 'company': company_data}
    
    def _parse_json_response(self, response_text: str) -> Optional[Dict]:
        """Parse JSON response from Claude, handling markdown formatting"""
        try:
            # Remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            return json.loads(text)
        except:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            return None
    
    def _is_generic_domain(self, domain: str) -> bool:
        """Check if domain is a generic email provider"""
        generic_domains = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'aol.com', 'icloud.com', 'mail.com', 'protonmail.com',
            'zoho.com', 'yandex.com', 'gmx.com', 'live.com',
            'msn.com', 'comcast.net', 'sbcglobal.net'
        }
        return domain.lower() in generic_domains
    
    def _domain_to_company_name(self, domain: str) -> str:
        """Convert domain to likely company name"""
        # Remove TLD and common prefixes
        parts = domain.lower().split('.')
        if len(parts) > 1:
            main_part = parts[0]
        else:
            main_part = domain
        
        # Remove common prefixes
        prefixes_to_remove = ['www', 'mail', 'email', 'smtp', 'pop', 'imap']
        if main_part in prefixes_to_remove and len(parts) > 1:
            main_part = parts[1]
        
        # Clean up and capitalize
        company_name = re.sub(r'[-_]', ' ', main_part).title()
        
        return company_name
    
    def _calculate_confidence_score(self, person_data: Dict, company_data: Dict, 
                                  data_sources: List[str]) -> float:
        """Calculate overall confidence score based on data quality and sources"""
        score = 0.0
        
        # Base score from data sources
        source_weights = {
            'email_signatures': 0.4,  # Most reliable
            'email_content': 0.3,
            'domain_intelligence': 0.2,
            'web_scraping': 0.3,
            'claude_synthesis': 0.1
        }
        
        for source in data_sources:
            score += source_weights.get(source, 0.1)
        
        # Bonus for data completeness
        person_fields = sum(1 for v in person_data.values() if v and str(v).strip())
        company_fields = sum(1 for v in company_data.values() if v and str(v).strip())
        
        completeness_bonus = min(0.3, (person_fields + company_fields) * 0.05)
        score += completeness_bonus
        
        # Bonus for having name
        if person_data.get('name') and len(person_data['name'].strip()) > 1:
            score += 0.2
        
        return min(1.0, score)
    
    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()

    async def enrich_contacts_by_domain_batch(self, contacts: List[Dict], user_emails: List[Dict] = None) -> Dict[str, EnhancedEnrichmentResult]:
        """
        Efficiently enrich contacts by grouping them by domain and doing domain intelligence once per domain
        
        Args:
            contacts: List of contact dictionaries
            user_emails: User's emails for content analysis
            
        Returns:
            Dictionary mapping email to enrichment results
        """
        if not contacts:
            return {}
        
        logger.info(f"🚀 Starting domain-based batch enrichment for {len(contacts)} contacts")
        
        # Group contacts by domain
        domain_groups = {}
        generic_contacts = []
        
        for contact in contacts:
            email = contact.get('email', '').strip().lower()
            if not email or '@' not in email:
                continue
                
            domain = email.split('@')[1]
            
            if self._is_generic_domain(domain):
                generic_contacts.append(contact)
            else:
                if domain not in domain_groups:
                    domain_groups[domain] = []
                domain_groups[domain].append(contact)
        
        logger.info(f"📊 Grouped into {len(domain_groups)} company domains + {len(generic_contacts)} generic contacts")
        
        # Process domain intelligence once per domain
        domain_intelligence_cache = {}
        
        logger.info(f"🏢 Processing company intelligence for {len(domain_groups)} domains...")
        for domain in domain_groups.keys():
            logger.info(f"  📈 Analyzing domain: {domain}")
            domain_data = await self._analyze_domain_intelligence(domain)
            domain_intelligence_cache[domain] = domain_data
        
        # Now process contacts efficiently using cached domain data
        results = {}
        
        # Process company contacts (use cached domain intelligence)
        for domain, domain_contacts in domain_groups.items():
            cached_domain_data = domain_intelligence_cache.get(domain, {})
            logger.info(f"🔄 Processing {len(domain_contacts)} contacts from {domain} using cached domain intelligence")
            
            for contact in domain_contacts:
                result = await self._enrich_contact_with_cached_domain(contact, cached_domain_data, user_emails or [])
                results[contact.get('email', '').strip().lower()] = result
        
        # Process generic contacts individually (no domain intelligence to cache)
        if generic_contacts:
            logger.info(f"👤 Processing {len(generic_contacts)} contacts from generic domains individually")
            for contact in generic_contacts:
                result = await self.enrich_contact(contact, user_emails)
                results[contact.get('email', '').strip().lower()] = result
        
        success_count = sum(1 for r in results.values() if r.confidence_score > 0)
        logger.info(f"✅ Domain-based batch enrichment completed: {success_count}/{len(results)} successful")
        
        return results
    
    async def _enrich_contact_with_cached_domain(self, contact: Dict, cached_domain_data: Dict, user_emails: List[Dict]) -> EnhancedEnrichmentResult:
        """
        Enrich contact using pre-computed domain intelligence (much faster)
        
        Args:
            contact: Contact data with email
            cached_domain_data: Pre-computed domain intelligence
            user_emails: User's emails for content analysis
            
        Returns:
            Enhanced enrichment result
        """
        email = contact.get('email', '').strip().lower()
        if not email:
            return EnhancedEnrichmentResult(
                email=email,
                confidence_score=0.0,
                person_data={},
                company_data={},
                relationship_intelligence={},
                actionable_insights={},
                data_sources=[],
                enrichment_timestamp=datetime.utcnow(),
                error="No email provided"
            )
        
        logger.info(f"⚡ Fast enrichment for {email} using cached domain data")
        
        # Initialize data containers
        person_data = {}
        company_data = cached_domain_data.copy()  # Start with cached domain data
        data_sources = []
        
        if cached_domain_data:
            data_sources.append('domain_intelligence_cached')
        
        try:
            # 1. EMAIL SIGNATURE ANALYSIS (Individual analysis)
            signature_data = await self._analyze_email_signatures(email, user_emails or [])
            if signature_data['person'] or signature_data['company']:
                person_data.update(signature_data['person'])
                # Merge company data carefully (don't overwrite cached domain data)
                for key, value in signature_data['company'].items():
                    if value and (key not in company_data or not company_data[key]):
                        company_data[key] = value
                data_sources.append('email_signatures')
                logger.info(f"✅ Extracted data from email signatures for {email}")
            
            # 2. EMAIL CONTENT ANALYSIS (Individual analysis)
            content_data = await self._analyze_email_content(email, user_emails or [])
            if content_data['person'] or content_data['company']:
                person_data.update(content_data['person'])
                # Merge company data carefully
                for key, value in content_data['company'].items():
                    if value and (key not in company_data or not company_data[key]):
                        company_data[key] = value
                data_sources.append('email_content')
                logger.info(f"✅ Extracted data from email content for {email}")
            
            # 3. SKIP DOMAIN INTELLIGENCE (already cached)
            # This is the efficiency gain - we don't redo domain analysis!
            
            # 4. ENHANCED WEB SCRAPING (Only if we have partial data to verify)
            if person_data.get('name') or company_data.get('name'):
                domain = email.split('@')[1] if '@' in email else None
                web_data = await self._enhanced_web_scraping(person_data, company_data, domain)
                if web_data['person'] or web_data['company']:
                    person_data.update(web_data['person'])
                    # Merge company data carefully
                    for key, value in web_data['company'].items():
                        if value and (key not in company_data or not company_data[key]):
                            company_data[key] = value
                    data_sources.append('web_scraping')
                    logger.info(f"✅ Enhanced with web scraping data for {email}")
            
            # 5. CLAUDE SYNTHESIS (Final processing)
            if person_data or company_data:
                synthesized_data = await self._claude_data_synthesis(
                    email, person_data, company_data, data_sources
                )
                person_data = synthesized_data['person']
                company_data = synthesized_data['company']
                data_sources.append('claude_synthesis')
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(person_data, company_data, data_sources)
            
            result = EnhancedEnrichmentResult(
                email=email,
                confidence_score=confidence_score,
                person_data=person_data,
                company_data=company_data,
                relationship_intelligence=synthesized_data.get('relationship_intelligence', {}),
                actionable_insights=synthesized_data.get('actionable_insights', {}),
                data_sources=data_sources,
                enrichment_timestamp=datetime.utcnow()
            )
            
            logger.info(f"⚡ Fast enrichment completed for {email} - Confidence: {confidence_score:.1%}, Sources: {len(data_sources)}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Fast enrichment failed for {email}: {str(e)}")
            return EnhancedEnrichmentResult(
                email=email,
                confidence_score=0.0,
                person_data={},
                company_data=cached_domain_data.copy(),  # At least return cached domain data
                relationship_intelligence={},
                actionable_insights={},
                data_sources=data_sources,
                enrichment_timestamp=datetime.utcnow(),
                error=str(e)
            )

    async def test_connectivity(self, test_url: str = "https://httpbin.org/get") -> Dict:
        """
        Test HTTP connectivity and SSL configuration
        
        Args:
            test_url: URL to test connectivity against
            
        Returns:
            Dictionary with test results
        """
        if not self.session:
            await self.initialize()
        
        result = {
            'test_url': test_url,
            'success': False,
            'error': None,
            'status_code': None,
            'response_time': None
        }
        
        try:
            import time
            start_time = time.time()
            
            async with self.session.get(test_url, ssl=False) as response:
                result['status_code'] = response.status
                result['response_time'] = time.time() - start_time
                
                if response.status == 200:
                    result['success'] = True
                    text = await response.text()
                    result['response_length'] = len(text)
                else:
                    result['error'] = f"HTTP {response.status}"
                    
        except Exception as e:
            result['error'] = f"{type(e).__name__}: {str(e)}"
            
        return result 