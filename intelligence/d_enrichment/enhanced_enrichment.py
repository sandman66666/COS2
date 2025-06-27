"""
Enhanced Contact Enrichment Service
================================
Comprehensive contact enrichment using multiple intelligence sources including
advanced web scraping, professional networks, and Claude AI synthesis.
"""

import asyncio
import json
import os
import random
import re
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import aiohttp
import anthropic

from utils.logging import structured_logger as logger
from config.settings import ANTHROPIC_API_KEY
from intelligence.d_enrichment.web_enrichment.enrichment_orchestrator import EnrichmentOrchestrator
from intelligence.d_enrichment.web_enrichment.linkedin_scraper import LinkedInScraper  
from intelligence.d_enrichment.web_enrichment.twitter_scraper import TwitterScraper

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
        Enrich contact using multiple data sources with robust fallbacks
        
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
        
        # Initialize synthesized_data early to avoid variable scope issues
        synthesized_data = {
            'person': {},
            'company': {},
            'relationship_intelligence': {},
            'actionable_insights': {}
        }
        
        try:
            # 1. EMAIL SIGNATURE ANALYSIS (Primary source - most reliable)
            try:
                signature_data = await self._analyze_email_signatures(email, user_emails or [])
                if signature_data['person'] or signature_data['company']:
                    person_data.update(signature_data['person'])
                    company_data.update(signature_data['company'])
                    data_sources.append('email_signatures')
                    logger.info(f"✅ Extracted data from email signatures for {email}")
            except Exception as e:
                logger.warning(f"Email signature analysis failed for {email}: {e}")
            
            # 2. EMAIL CONTENT ANALYSIS (Secondary source)
            try:
                content_data = await self._analyze_email_content(email, user_emails or [])
                if content_data['person'] or content_data['company']:
                    person_data.update(content_data['person'])
                    company_data.update(content_data['company'])
                    data_sources.append('email_content')
                    logger.info(f"✅ Extracted data from email content for {email}")
            except Exception as e:
                logger.warning(f"Email content analysis failed for {email}: {e}")
            
            # 3. DOMAIN INTELLIGENCE (Tertiary source)
            domain = email.split('@')[1] if '@' in email else None
            if domain and not self._is_generic_domain(domain):
                try:
                    domain_data = await self._analyze_domain_intelligence(domain)
                    if domain_data:
                        company_data.update(domain_data)
                        data_sources.append('domain_intelligence')
                        logger.info(f"✅ Extracted domain intelligence for {domain}")
                except Exception as e:
                    logger.warning(f"Domain intelligence failed for {domain}: {e}")
            
            # 4. WEB INTELLIGENCE (Enhanced - with fallbacks for memory issues)
            logger.info(f"🌐 Gathering comprehensive web intelligence for {email}")
            
            # Initialize web enrichment orchestrator with fallback handling
            try:
                web_orchestrator = EnrichmentOrchestrator(self.user_id)
                await asyncio.wait_for(web_orchestrator.initialize(), timeout=30)
                
                # Prepare contact data for web enrichment
                contact_for_enrichment = {
                    'email': email,
                    'name': person_data.get('name', ''),
                    'company': company_data.get('name', ''),
                    'domain': domain
                }
                
                # Get comprehensive web intelligence with timeout
                web_intelligence = await asyncio.wait_for(
                    web_orchestrator.enrich_contact(contact_for_enrichment),
                    timeout=60
                )
                
                if web_intelligence:
                    # Merge web intelligence into person and company data
                    if 'linkedin_data' in web_intelligence:
                        linkedin_data = web_intelligence['linkedin_data']
                        person_data.update({
                            'experience': linkedin_data.get('experience', []),
                            'education': linkedin_data.get('education', []),
                            'skills': linkedin_data.get('skills', []),
                            'about': linkedin_data.get('about', ''),
                            'current_position': linkedin_data.get('current_position', {}),
                            'connections': linkedin_data.get('connections', 0)
                        })
                        data_sources.append('linkedin_intelligence')
                    
                    if 'twitter_data' in web_intelligence:
                        twitter_data = web_intelligence['twitter_data']
                        person_data.update({
                            'twitter_bio': twitter_data.get('bio', ''),
                            'twitter_engagement': twitter_data.get('engagement_metrics', {}),
                            'recent_tweets': twitter_data.get('recent_tweets', []),
                            'thought_leadership_topics': twitter_data.get('topics', [])
                        })
                        data_sources.append('twitter_intelligence')
                    
                    logger.info(f"✅ Comprehensive web intelligence gathered for {email}: LinkedIn={bool(web_intelligence.get('linkedin_data'))}, Twitter={bool(web_intelligence.get('twitter_data'))}")
                
            except Exception as e:
                logger.warning(f"⚠️ Web intelligence gathering failed for {email} (likely missing Playwright browsers): {e}")
                logger.info(f"📋 Falling back to basic enrichment without advanced web scraping for {email}")
                
                # Fallback: Use basic domain intelligence without browser-based scraping
                try:
                    # Basic domain lookup without browser automation
                    basic_company_info = await self._get_basic_domain_info(domain)
                    if basic_company_info:
                        company_data.update(basic_company_info)
                        data_sources.append('basic_domain_lookup')
                        
                except Exception as fallback_error:
                    logger.warning(f"⚠️ Basic domain lookup also failed for {domain}: {fallback_error}")
            
            # 5. CLAUDE SYNTHESIS (Final processing) - Always runs with basic data
            if person_data or company_data:
                try:
                    claude_result = await self._claude_data_synthesis(
                        email, person_data, company_data, data_sources
                    )
                    if claude_result:
                        synthesized_data = claude_result
                    data_sources.append('claude_synthesis')
                except Exception as e:
                    logger.warning(f"Claude synthesis failed for {email}: {e}")
                    # Use basic data if Claude fails
                    synthesized_data.update({
                        'person': person_data,
                        'company': company_data
                    })
            else:
                # Use whatever basic data we have
                synthesized_data.update({
                    'person': person_data,
                    'company': company_data
                })
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(person_data, company_data, data_sources)
            
            result = EnhancedEnrichmentResult(
                email=email,
                confidence_score=confidence_score,
                person_data=synthesized_data.get('person', {}),
                company_data=synthesized_data.get('company', {}),
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
                person_data=synthesized_data.get('person', {}),
                company_data=synthesized_data.get('company', {}),
                relationship_intelligence=synthesized_data.get('relationship_intelligence', {}),
                actionable_insights=synthesized_data.get('actionable_insights', {}),
                data_sources=data_sources,
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

ENHANCED PERSON DATA (LinkedIn + Twitter Intelligence):
{json.dumps(person_data, indent=2)}

ENHANCED COMPANY DATA:
{json.dumps(company_data, indent=2)}

Extract MAXIMUM intelligence from LinkedIn experience, skills, about section, Twitter thought leadership, and other professional data to provide comprehensive business intelligence:

{{
    "person": {{
        "name": "Full professional name from LinkedIn/email",
        "current_title": "Current role/position from LinkedIn",
        "seniority_level": "junior/mid/senior/executive/founder (analyze from experience/title)",
        "career_stage": "early-career/growth/established/veteran/executive (from experience progression)",
        
        "professional_background": {{
            "previous_companies": "Extract from LinkedIn experience array",
            "career_progression": "Analyze career journey from experience data",
            "years_experience": "Calculate from LinkedIn experience timeline",
            "industry_expertise": "Derive from experience + skills",
            "functional_expertise": "Extract from titles + skills",
            "education_background": "From LinkedIn education array", 
            "certifications": "From LinkedIn skills/education",
            "skills_and_expertise": "Top skills from LinkedIn skills array"
        }},
        
        "current_focus": {{
            "investment_thesis": "If investor - analyze from about/headline/tweets",
            "portfolio_companies": "Extract from LinkedIn experience if investor",
            "key_initiatives": "From LinkedIn about section + recent experience",
            "speaking_topics": "Analyze from Twitter topics + LinkedIn headline",
            "content_themes": "From Twitter recent_tweets analysis",
            "thought_leadership_areas": "From Twitter thought_leadership_areas"
        }},
        
        "social_intelligence": {{
            "twitter_handle": "From Twitter data",
            "twitter_bio": "Professional bio from Twitter", 
            "follower_count": "Twitter followers (influence indicator)",
            "engagement_style": "Analyze from Twitter tweets + LinkedIn about",
            "content_frequency": "Analyze from Twitter activity",
            "professional_topics": "Merge Twitter topics + LinkedIn skills"
        }},
        
        "network_intelligence": {{
            "linkedin_connections": "From LinkedIn connections count",
            "network_value": "Assess from connections + experience level",
            "industry_influence": "Calculate from followers + experience + skills",
            "thought_leadership": "Based on Twitter engagement + LinkedIn headline",
            "conference_speaking": "Infer from skills + seniority",
            "media_presence": "Based on Twitter activity + professional background"
        }},
        
        "communication_insights": {{
            "communication_style": "Analyze from Twitter bio + LinkedIn about + tweets",
            "response_patterns": "Infer from social activity level",
            "preferred_topics": "Merge Twitter topics + LinkedIn skills",
            "social_presence": "active/minimal/thought-leader from Twitter data", 
            "outreach_timing": "Best approach based on communication style",
            "engagement_likelihood": "Based on social activity + role"
        }},
        
        "value_proposition": {{
            "what_they_offer": "Analyze from experience + skills + about section",
            "decision_authority": "Infer from title + seniority + company",
            "budget_authority": "Estimate from role + company stage",
            "network_value": "Based on connections + industry + experience",
            "expertise_value": "Top areas from skills + experience + tweets"
        }}
    }},
    
    "company": {{
        "name": "Official company name from LinkedIn/domain",
        "industry": "Primary industry from LinkedIn company + domain intelligence",
        "sub_industry": "Specific niche from LinkedIn experience",
        
        "company_profile": {{
            "business_model": "Infer from company data + person's role",
            "revenue_model": "Analyze from company intelligence",
            "target_market": "From domain intelligence + person's background",
            "company_stage": "From domain data + person's seniority",
            "employee_count": "From domain intelligence",
            "headquarters": "From LinkedIn location + domain data",
            "founded_year": "From domain intelligence if available"
        }},
        
        "financial_intelligence": {{
            "funding_status": "From domain intelligence",
            "funding_rounds": "Extract if available from domain data",
            "key_investors": "From domain intelligence",
            "estimated_valuation": "If available from domain data",
            "revenue_estimates": "Infer from company stage + employees",
            "growth_trajectory": "Analyze from company data + hiring"
        }},
        
        "market_position": {{
            "competitive_landscape": "From domain intelligence + industry analysis",
            "key_competitors": "From industry knowledge + domain data",
            "differentiation": "From company description + domain intelligence",
            "market_trends": "Industry context from domain intelligence",
            "growth_opportunities": "Based on company stage + market"
        }},
        
        "technology_profile": {{
            "tech_stack": "Infer from company type + domain intelligence",
            "digital_maturity": "Assess from company profile",
            "innovation_focus": "From company description + person's skills",
            "technology_partnerships": "From domain intelligence if available"
        }}
    }},
    
    "relationship_intelligence": {{
        "engagement_level": "high/medium/low based on email frequency + social activity",
        "relationship_stage": "cold/warm/active/partnership based on communication",
        "mutual_connections": "Potential overlap based on industry + location",
        "collaboration_opportunities": "Based on expertise + company needs",
        "referral_potential": "Based on network size + influence + relationship",
        "influence_score": "Calculate from followers + connections + experience"
    }},
    
    "actionable_insights": {{
        "best_approach": "Optimal engagement strategy based on communication style + role",
        "value_propositions": "What would most interest them based on focus areas",
        "timing_considerations": "When to reach out based on activity patterns",
        "conversation_starters": "Relevant topics from Twitter + LinkedIn interests",
        "meeting_likelihood": "Probability based on role + engagement style + social activity",
        "decision_timeline": "Speed based on role + company + industry"
    }}
}}

CRITICAL: Use ALL LinkedIn experience, education, skills, and about data. Use ALL Twitter bio, tweets, and engagement data. This is comprehensive business intelligence - extract every insight possible from the rich professional data collected."""

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
            
            # 4. COMPREHENSIVE WEB INTELLIGENCE (ENHANCED - Uses multiple professional sources)
            logger.info(f"🌐 Gathering comprehensive web intelligence for {email}")
            
            # Initialize web enrichment orchestrator with fallback handling
            try:
                web_orchestrator = EnrichmentOrchestrator(self.user_id)
                await asyncio.wait_for(web_orchestrator.initialize(), timeout=30)
                
                # Prepare contact data for web enrichment
                contact_for_enrichment = {
                    'email': email,
                    'name': person_data.get('name', ''),
                    'company': company_data.get('name', ''),
                    'domain': domain
                }
                
                # Get comprehensive web intelligence with timeout
                web_intelligence = await asyncio.wait_for(
                    web_orchestrator.enrich_contact(contact_for_enrichment),
                    timeout=60
                )
                
                if web_intelligence:
                    # Merge web intelligence into person and company data
                    if 'linkedin_data' in web_intelligence:
                        linkedin_data = web_intelligence['linkedin_data']
                        person_data.update({
                            'experience': linkedin_data.get('experience', []),
                            'education': linkedin_data.get('education', []),
                            'skills': linkedin_data.get('skills', []),
                            'about': linkedin_data.get('about', ''),
                            'current_position': linkedin_data.get('current_position', {}),
                            'connections': linkedin_data.get('connections', 0)
                        })
                        data_sources.append('linkedin_intelligence')
                    
                    if 'twitter_data' in web_intelligence:
                        twitter_data = web_intelligence['twitter_data']
                        person_data.update({
                            'twitter_bio': twitter_data.get('bio', ''),
                            'twitter_engagement': twitter_data.get('engagement_metrics', {}),
                            'recent_tweets': twitter_data.get('recent_tweets', []),
                            'thought_leadership_topics': twitter_data.get('topics', [])
                        })
                        data_sources.append('twitter_intelligence')
                    
                    logger.info(f"✅ Comprehensive web intelligence gathered for {email}: LinkedIn={bool(web_intelligence.get('linkedin_data'))}, Twitter={bool(web_intelligence.get('twitter_data'))}")
                
            except Exception as e:
                logger.warning(f"⚠️ Web intelligence gathering failed for {email} (likely missing Playwright browsers): {e}")
                logger.info(f"📋 Falling back to basic enrichment without advanced web scraping for {email}")
                
                # Fallback: Use basic domain intelligence without browser-based scraping
                try:
                    # Basic domain lookup without browser automation
                    basic_company_info = await self._get_basic_domain_info(domain)
                    if basic_company_info:
                        company_data.update(basic_company_info)
                        data_sources.append('basic_domain_lookup')
                        
                except Exception as fallback_error:
                    logger.warning(f"⚠️ Basic domain lookup also failed for {domain}: {fallback_error}")
            
            # 5. CLAUDE SYNTHESIS (Final processing)
            synthesized_data = {'person': person_data, 'company': company_data, 'relationship_intelligence': {}, 'actionable_insights': {}}
            
            if person_data or company_data:
                claude_result = await self._claude_data_synthesis(
                    email, person_data, company_data, data_sources
                )
                if claude_result:
                    synthesized_data = claude_result
                data_sources.append('claude_synthesis')
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(person_data, company_data, data_sources)
            
            result = EnhancedEnrichmentResult(
                email=email,
                confidence_score=confidence_score,
                person_data=synthesized_data['person'],
                company_data=synthesized_data['company'],
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
                person_data=cached_domain_data.copy(),  # At least return cached domain data
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

    async def _get_basic_domain_info(self, domain: str) -> Dict:
        """
        Get basic domain information without browser-based scraping
        Fallback method when Playwright browsers aren't available
        """
        try:
            # Basic domain intelligence using simple HTTP requests
            basic_info = {}
            
            # Simple domain name cleanup
            clean_domain = domain.lower().replace('www.', '')
            company_name = clean_domain.split('.')[0].replace('-', ' ').replace('_', ' ').title()
            
            basic_info.update({
                'name': company_name,
                'domain': clean_domain,
                'website': f"https://{clean_domain}",
                'enrichment_method': 'basic_fallback',
                'industry': 'Unknown',
                'description': f"Company associated with {clean_domain}"
            })
            
            # Try to get basic website title/description via simple HTTP request
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.get(f"https://{clean_domain}", headers={
                        'User-Agent': 'Mozilla/5.0 (compatible; contact-enrichment/1.0)'
                    }) as response:
                        if response.status == 200:
                            html = await response.text()
                            # Simple title extraction
                            import re
                            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
                            if title_match:
                                title = title_match.group(1).strip()
                                if title and title != company_name:
                                    basic_info['description'] = title
                                    
            except Exception as web_error:
                logger.debug(f"Basic web request failed for {domain}: {web_error}")
            
            return basic_info
            
        except Exception as e:
            logger.warning(f"Basic domain info extraction failed for {domain}: {e}")
            return {} 