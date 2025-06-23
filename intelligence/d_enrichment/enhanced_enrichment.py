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

from utils.logging import structured_logger as logger
from config.settings import ANTHROPIC_API_KEY

# Claude 4 Opus - now working with proper API key!
CLAUDE_MODEL = 'claude-opus-4-20250514'

@dataclass
class EnhancedEnrichmentResult:
    """Comprehensive enrichment result with multiple data sources"""
    email: str
    confidence_score: float
    person_data: Dict[str, Any]
    company_data: Dict[str, Any]
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
        # Enhanced HTTP session with better headers and settings
        connector = aiohttp.TCPConnector(
            limit=10, 
            limit_per_host=2,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
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
        Analyze email domain to extract company information
        """
        if self._is_generic_domain(domain):
            return {}
        
        company_data = {}
        
        # 1. Basic domain analysis
        company_name = self._domain_to_company_name(domain)
        company_data['name'] = company_name
        
        # 2. Try to fetch company website
        website_data = await self._fetch_domain_info(domain)
        if website_data:
            company_data.update(website_data)
        
        # 3. Use Claude for domain intelligence
        if self.claude_client and company_data.get('name'):
            try:
                prompt = f"""
Analyze this company domain and provide business intelligence:

Domain: {domain}
Inferred Company Name: {company_name}
Website Data: {json.dumps(website_data) if website_data else 'None'}

Based on the domain and any context, provide:

{{
    "company": {{
        "name": "Refined company name",
        "industry": "Likely industry",
        "size": "Estimated company size",
        "business_type": "B2B/B2C/etc",
        "technology_focus": "Tech stack or focus area",
        "market_position": "Market position if known"
    }}
}}

Use your knowledge to make educated inferences about this company.
"""

                working_model = CLAUDE_MODEL
                response = await asyncio.to_thread(
                    self.claude_client.messages.create,
                    model=working_model,
                    max_tokens=800,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                result = self._parse_json_response(response.content[0].text)
                if result and result.get('company'):
                    company_data.update(result['company'])
                    
            except Exception as e:
                logger.error(f"Claude domain analysis failed: {e}")
        
        return company_data
    
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
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    ]),
                    'Referer': 'https://www.google.com/',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
                
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._extract_info_from_html(html)
                        
            except Exception as e:
                # More informative logging for URL fetch failures
                if hasattr(e, 'url') and str(e.url) != url:
                    logger.debug(f"Failed to fetch {url} (redirected to {e.url}): {e}")
                else:
                    logger.debug(f"Failed to fetch {url}: {e}")
                continue
        
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
        Use Claude to synthesize and enhance all collected data
        """
        if not self.claude_client:
            return {'person': person_data, 'company': company_data}
        
        try:
            prompt = f"""
Synthesize and enhance this contact information:

EMAIL: {email}
DATA SOURCES: {', '.join(data_sources)}

PERSON DATA:
{json.dumps(person_data, indent=2)}

COMPANY DATA:
{json.dumps(company_data, indent=2)}

Please synthesize this information into a coherent, enhanced profile:

{{
    "person": {{
        "name": "Best available full name",
        "title": "Most accurate job title",
        "seniority_level": "junior/mid/senior/executive",
        "expertise_areas": ["area1", "area2"],
        "communication_style": "professional/casual/formal",
        "confidence_indicators": ["what makes us confident about this data"]
    }},
    "company": {{
        "name": "Official company name",
        "industry": "Primary industry",
        "size_category": "startup/small/medium/large/enterprise",
        "business_model": "B2B/B2C/marketplace/etc",
        "technology_maturity": "traditional/digital-native/tech-forward",
        "market_position": "leader/challenger/niche/startup"
    }}
}}

Resolve any conflicts in the data and provide the most accurate synthesis.
"""

            working_model = CLAUDE_MODEL
            response = await asyncio.to_thread(
                self.claude_client.messages.create,
                model=working_model,
                max_tokens=1200,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = self._parse_json_response(response.content[0].text)
            if result:
                return {
                    'person': result.get('person', person_data),
                    'company': result.get('company', company_data)
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
                data_sources=data_sources,
                enrichment_timestamp=datetime.utcnow(),
                error=str(e)
            ) 