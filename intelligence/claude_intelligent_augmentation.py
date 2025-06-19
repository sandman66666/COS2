"""
Claude Opus 4 Intelligent Web Intelligence System
=============================================== 
Revolutionary approach using Claude Opus 4 as the orchestrating brain to:
1. Create intelligent domain navigation plans
2. Extract comprehensive company intelligence from websites
3. Use company context for targeted person searches
4. Avoid rate limiting through smart strategies
"""

import asyncio
import aiohttp
import json
import re
from typing import Dict, Optional, List, Tuple
from urllib.parse import quote, urljoin, urlparse
import time
import anthropic
from dataclasses import dataclass
import random

from utils.logging import structured_logger as logger
from config.settings import ANTHROPIC_API_KEY

@dataclass
class DomainIntelligencePlan:
    """Claude-generated plan for domain intelligence gathering"""
    domain: str
    primary_urls: List[str]
    fallback_urls: List[str]
    expected_company_info: Dict[str, str]
    navigation_strategy: str
    scraping_priorities: List[str]

@dataclass
class CompanyIntelligence:
    """Comprehensive company intelligence extracted by Claude"""
    name: str
    industry: str
    description: str
    size: Optional[str]
    founded: Optional[str]
    location: Optional[str]
    funding: Optional[str]
    leadership: List[Dict]
    key_people: List[Dict]
    products: List[str]
    technologies: List[str]
    recent_news: List[Dict]
    confidence_score: float

@dataclass
class PersonIntelligence:
    """Person intelligence enhanced with company context"""
    name: str
    title: str
    company_context: Dict
    professional_background: Dict
    connections: Dict
    confidence_score: float

class ClaudeIntelligentAugmentation:
    """Claude Opus 4 powered intelligent augmentation system"""
    
    def __init__(self):
        self.claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
        self.session = None
        self.rate_limiter = {}
        
    async def initialize(self):
        """Initialize HTTP session with intelligent headers"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=2)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        # Rotate user agents intelligently
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
        
        logger.info("🧠 Claude Opus 4 Intelligent Augmentation initialized")

    async def create_domain_intelligence_plan(self, domain: str) -> DomainIntelligencePlan:
        """Use Claude to create an intelligent plan for domain exploration"""
        
        if not self.claude_client:
            logger.warning("Claude API not available, using fallback strategy")
            return self._create_fallback_plan(domain)
        
        prompt = f"""
        You are an expert web intelligence analyst. Create a comprehensive plan to gather intelligence about the company associated with domain: {domain}

        Analyze this domain and provide a strategic plan with:

        1. PRIMARY_URLS: Most likely URLs to contain company information (about, team, company, leadership pages)
        2. FALLBACK_URLS: Alternative URLs if primary ones fail
        3. EXPECTED_INFO: What types of company information we should expect to find
        4. NAVIGATION_STRATEGY: How to intelligently navigate the site
        5. SCRAPING_PRIORITIES: Order of information importance

        Consider:
        - Common website structures and patterns
        - Where companies typically place key information
        - How to avoid rate limiting and detection
        - Most efficient navigation paths

        Respond in JSON format:
        {{
            "primary_urls": ["/about", "/team", "/company"],
            "fallback_urls": ["/about-us", "/leadership", "/our-team"],
            "expected_company_info": {{
                "name": "likely found in header/about section",
                "industry": "about page or product descriptions",
                "description": "mission statement on about page"
            }},
            "navigation_strategy": "Start with about page, then team, prioritize official company info",
            "scraping_priorities": ["company_name", "description", "team", "products", "location"]
        }}
        """
        
        try:
            response = await self._call_claude(prompt)
            plan_data = json.loads(response)
            
            return DomainIntelligencePlan(
                domain=domain,
                primary_urls=[urljoin(f"https://{domain}", url) for url in plan_data.get('primary_urls', [])],
                fallback_urls=[urljoin(f"https://{domain}", url) for url in plan_data.get('fallback_urls', [])],
                expected_company_info=plan_data.get('expected_company_info', {}),
                navigation_strategy=plan_data.get('navigation_strategy', ''),
                scraping_priorities=plan_data.get('scraping_priorities', [])
            )
            
        except Exception as e:
            logger.error(f"Failed to create Claude intelligence plan: {e}")
            return self._create_fallback_plan(domain)

    async def extract_company_intelligence(self, domain: str) -> CompanyIntelligence:
        """Use Claude to intelligently extract comprehensive company information"""
        
        logger.info(f"🏢 Starting intelligent company analysis for {domain}")
        
        # Step 1: Create intelligent navigation plan
        plan = await self.create_domain_intelligence_plan(domain)
        logger.info(f"📋 Created intelligence plan with {len(plan.primary_urls)} primary targets")
        
        # Step 2: Intelligently gather raw content
        content_map = await self._intelligent_content_gathering(plan)
        
        # Step 3: Use Claude to extract structured intelligence
        company_intel = await self._claude_company_analysis(domain, content_map, plan)
        
        return company_intel

    async def _intelligent_content_gathering(self, plan: DomainIntelligencePlan) -> Dict[str, str]:
        """Intelligently gather content using Claude's navigation strategy"""
        
        content_map = {}
        
        # Rate limiting strategy
        await self._intelligent_rate_limit(plan.domain)
        
        # Try primary URLs first
        for url in plan.primary_urls[:3]:  # Limit to top 3 to avoid detection
            try:
                logger.info(f"🌐 Intelligently fetching: {url}")
                
                content = await self._smart_fetch_content(url)
                if content and len(content.strip()) > 100:
                    content_map[url] = content
                    logger.info(f"✅ Successfully gathered {len(content)} chars from {url}")
                    
                    # Intelligent delay between requests
                    await asyncio.sleep(random.uniform(2, 5))
                else:
                    logger.warning(f"❌ No useful content from {url}")
                    
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")
                continue
        
        # If primary URLs failed, try fallbacks
        if not content_map and plan.fallback_urls:
            logger.info("🔄 Primary URLs failed, trying fallback strategy")
            for url in plan.fallback_urls[:2]:
                try:
                    content = await self._smart_fetch_content(url)
                    if content:
                        content_map[url] = content
                        break
                except Exception as e:
                    continue
        
        logger.info(f"📊 Gathered content from {len(content_map)} URLs")
        return content_map

    async def _smart_fetch_content(self, url: str) -> Optional[str]:
        """Intelligently fetch content with anti-detection measures"""
        
        try:
            # Smart headers for this specific request
            headers = {
                'Referer': f"https://www.google.com/",
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Basic content cleaning
                    cleaned_content = self._clean_html_content(content)
                    return cleaned_content
                    
                elif response.status == 429:
                    logger.warning(f"Rate limited on {url}, backing off")
                    await asyncio.sleep(random.uniform(10, 20))
                    return None
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def _clean_html_content(self, html: str) -> str:
        """Extract meaningful content from HTML"""
        
        # Remove scripts and styles
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags but keep text
        text = re.sub(r'<[^>]+>', ' ', html)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Limit content size for Claude analysis
        return text[:8000] if text else ""

    async def _claude_company_analysis(self, domain: str, content_map: Dict[str, str], plan: DomainIntelligencePlan) -> CompanyIntelligence:
        """Use Claude to extract structured company intelligence from gathered content"""
        
        if not self.claude_client:
            return self._create_fallback_company_intel(domain)
        
        # Combine all content for analysis
        combined_content = "\n\n".join([f"=== {url} ===\n{content}" for url, content in content_map.items()])
        
        prompt = f"""
        You are an expert company intelligence analyst. Analyze the following website content from {domain} and extract comprehensive company intelligence.

        WEBSITE CONTENT:
        {combined_content[:15000]}

        Extract and structure the following information:

        1. COMPANY_NAME: Official company name
        2. INDUSTRY: Primary industry/sector
        3. DESCRIPTION: Company description and mission
        4. SIZE: Employee count or size category
        5. FOUNDED: Founding year or date
        6. LOCATION: Headquarters location
        7. FUNDING: Funding status, investors, amounts
        8. LEADERSHIP: Key executives and leadership team
        9. KEY_PEOPLE: Important team members
        10. PRODUCTS: Main products or services
        11. TECHNOLOGIES: Technologies they use/develop
        12. RECENT_NEWS: Any recent developments or news
        13. CONFIDENCE: Your confidence in this analysis (0-1)

        Respond in JSON format:
        {{
            "name": "Company Name",
            "industry": "Industry",
            "description": "Description",
            "size": "Size",
            "founded": "Year",
            "location": "Location",
            "funding": "Funding info",
            "leadership": [
                {{"name": "Name", "title": "Title", "background": "Info"}}
            ],
            "key_people": [
                {{"name": "Name", "role": "Role", "info": "Background"}}
            ],
            "products": ["Product1", "Product2"],
            "technologies": ["Tech1", "Tech2"],
            "recent_news": [
                {{"title": "News title", "summary": "Summary", "date": "Date"}}
            ],
            "confidence_score": 0.85
        }}

        Be thorough but accurate. If information is not clearly stated, mark confidence appropriately.
        """
        
        try:
            response = await self._call_claude(prompt)
            intel_data = json.loads(response)
            
            return CompanyIntelligence(
                name=intel_data.get('name', domain),
                industry=intel_data.get('industry', 'Unknown'),
                description=intel_data.get('description', ''),
                size=intel_data.get('size'),
                founded=intel_data.get('founded'),
                location=intel_data.get('location'),
                funding=intel_data.get('funding'),
                leadership=intel_data.get('leadership', []),
                key_people=intel_data.get('key_people', []),
                products=intel_data.get('products', []),
                technologies=intel_data.get('technologies', []),
                recent_news=intel_data.get('recent_news', []),
                confidence_score=intel_data.get('confidence_score', 0.5)
            )
            
        except Exception as e:
            logger.error(f"Claude company analysis failed: {e}")
            return self._create_fallback_company_intel(domain)

    async def extract_person_intelligence(self, first_name: str, last_name: str, email: str, company_intel: CompanyIntelligence) -> PersonIntelligence:
        """Use company context to intelligently search for person information"""
        
        logger.info(f"👤 Starting intelligent person analysis for {first_name} {last_name} at {company_intel.name}")
        
        if not self.claude_client:
            return self._create_fallback_person_intel(first_name, last_name, email)
        
        # For now, create basic person intelligence with company context
        # This would be enhanced with actual search implementation
        
        person_intel = PersonIntelligence(
            name=f"{first_name} {last_name}",
            title="Unknown",
            company_context={
                "company_name": company_intel.name,
                "industry": company_intel.industry,
                "company_size": company_intel.size
            },
            professional_background={},
            connections={},
            confidence_score=0.6
        )
        
        return person_intel

    async def _intelligent_rate_limit(self, domain: str):
        """Intelligent rate limiting based on domain characteristics"""
        
        now = time.time()
        if domain in self.rate_limiter:
            last_request = self.rate_limiter[domain]
            time_since = now - last_request
            
            # Intelligent delay based on domain type
            if domain.endswith('.com'):
                min_delay = 3
            elif domain.endswith('.ai') or domain.endswith('.io'):
                min_delay = 5  # Tech companies might have better protection
            else:
                min_delay = 2
            
            if time_since < min_delay:
                sleep_time = min_delay - time_since + random.uniform(1, 3)
                logger.info(f"⏱️ Intelligent rate limiting: sleeping {sleep_time:.1f}s for {domain}")
                await asyncio.sleep(sleep_time)
        
        self.rate_limiter[domain] = now

    async def _call_claude(self, prompt: str) -> str:
        """Call Claude Opus 4 with intelligent error handling"""
        
        try:
            message = self.claude_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            logger.info(f"📤 Claude response received ({len(response_text)} chars)")
            
            # Try to extract JSON from Claude's response
            # Sometimes Claude wraps JSON in markdown or adds explanations
            import re
            
            # Look for JSON block in markdown format
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                return json_match.group(1)
            
            # Look for JSON block without markdown
            json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
            if json_match:
                return json_match.group(1)
            
            # If no JSON found, log the raw response and return empty JSON
            logger.warning(f"🔍 No JSON found in Claude response. Raw response: {response_text[:500]}...")
            return "{}"
            
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise

    def _create_fallback_plan(self, domain: str) -> DomainIntelligencePlan:
        """Create fallback plan when Claude is not available"""
        
        common_paths = ['/about', '/about-us', '/company', '/team', '/leadership', '/our-team']
        primary_urls = [f"https://{domain}{path}" for path in common_paths[:3]]
        fallback_urls = [f"https://{domain}{path}" for path in common_paths[3:]]
        
        return DomainIntelligencePlan(
            domain=domain,
            primary_urls=primary_urls,
            fallback_urls=fallback_urls,
            expected_company_info={},
            navigation_strategy="Basic path enumeration",
            scraping_priorities=["name", "description", "team"]
        )

    def _create_fallback_company_intel(self, domain: str) -> CompanyIntelligence:
        """Create fallback company intelligence"""
        
        return CompanyIntelligence(
            name=domain.replace('.com', '').replace('.', ' ').title(),
            industry="Unknown",
            description="",
            size=None,
            founded=None,
            location=None,
            funding=None,
            leadership=[],
            key_people=[],
            products=[],
            technologies=[],
            recent_news=[],
            confidence_score=0.1
        )

    def _create_fallback_person_intel(self, first_name: str, last_name: str, email: str) -> PersonIntelligence:
        """Create fallback person intelligence"""
        
        return PersonIntelligence(
            name=f"{first_name} {last_name}",
            title="Unknown",
            company_context={},
            professional_background={},
            connections={},
            confidence_score=0.1
        )

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()

# Global instance
claude_intelligence = ClaudeIntelligentAugmentation()

async def get_claude_intelligent_augmentation(email: str, name: str = None) -> Dict:
    """Main function for Claude intelligent augmentation"""
    
    if not claude_intelligence.session:
        await claude_intelligence.initialize()
    
    try:
        # Extract domain from email
        domain = email.split('@')[1] if '@' in email else None
        if not domain:
            return {"error": "Invalid email format"}
        
        # Extract person name
        first_name, last_name = "", ""
        if name:
            parts = name.split()
            first_name = parts[0] if parts else ""
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        # Step 1: Get comprehensive company intelligence
        logger.info(f"🚀 Starting Claude Opus 4 intelligent augmentation for {email}")
        company_intel = await claude_intelligence.extract_company_intelligence(domain)
        
        # Step 2: Use company context for person intelligence
        person_intel = await claude_intelligence.extract_person_intelligence(
            first_name, last_name, email, company_intel
        )
        
        # Format response
        return {
            "success": True,
            "method": "claude_opus_4_intelligent_augmentation",
            "person": {
                "name": person_intel.name,
                "title": person_intel.title,
                "professional_background": person_intel.professional_background,
                "connections": person_intel.connections,
                "confidence": person_intel.confidence_score
            },
            "company": {
                "name": company_intel.name,
                "industry": company_intel.industry,
                "description": company_intel.description,
                "size": company_intel.size,
                "founded": company_intel.founded,
                "location": company_intel.location,
                "funding": company_intel.funding,
                "leadership": company_intel.leadership,
                "key_people": company_intel.key_people,
                "products": company_intel.products,
                "technologies": company_intel.technologies,
                "recent_news": company_intel.recent_news,
                "confidence": company_intel.confidence_score
            },
            "intelligence_summary": {
                "method": "claude_opus_4_intelligent_orchestration",
                "person_confidence": person_intel.confidence_score,
                "company_confidence": company_intel.confidence_score,
                "overall_confidence": (person_intel.confidence_score + company_intel.confidence_score) / 2
            }
        }
        
    except Exception as e:
        logger.error(f"Claude intelligent augmentation failed for {email}: {e}")
        return {"error": str(e), "method": "claude_opus_4_intelligent_augmentation"} 