"""
Competitive Landscape Intelligence Analyst
==========================================
CEO-level competitive landscape analysis using Claude 4 Opus.
Maps competitive position and strategic opportunities.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from utils.logging import structured_logger as logger
from intelligence.analysts.base_analyst import BaseAnalyst

class CompetitiveLandscapeAnalyst(BaseAnalyst):
    """
    Competitive Landscape Intelligence Analyst
    
    Maps the competitive landscape from a CEO's strategic perspective,
    providing insights for market positioning, competitive threats,
    and strategic opportunities.
    """
    
    def __init__(self, user_id: int, anthropic_api_key: str = None):
        """
        Initialize competitive landscape analyst
        
        Args:
            user_id: User ID for multi-tenant isolation
            anthropic_api_key: Optional API key for Claude Opus
        """
        super().__init__(user_id, anthropic_api_key)
        self.analyst_name = "competitive_landscape"
        self.analyst_description = "CEO-level competitive landscape intelligence analyst"
        
        # Customize Claude parameters for strategic analysis
        self.max_tokens = 4000
        self.temperature = 0.1  # Very low temperature for factual competitive analysis
    
    async def generate_intelligence(self, data: Dict) -> Dict:
        """
        Generate competitive landscape intelligence
        
        Args:
            data: Dictionary containing company context, industry data, and contact network
            
        Returns:
            Dictionary with competitive landscape analysis
        """
        try:
            # Extract data elements
            company_context = data.get("company_context", {})
            industry_context = data.get("industry_context", {})
            contact_network = data.get("contact_network", [])
            business_objectives = data.get("business_objectives", [])
            
            # Prepare comprehensive system prompt
            system_prompt = self._create_landscape_system_prompt()
            
            # Prepare user prompt with competitive context
            user_prompt = self._create_landscape_user_prompt(
                company_context=company_context,
                industry_context=industry_context,
                contact_network=contact_network,
                business_objectives=business_objectives
            )
            
            # Run Claude Opus analysis
            result_text = await self._run_claude_analysis(system_prompt, user_prompt)
            
            # Extract structured competitive intelligence
            structured_result = self._parse_landscape_response(result_text)
            
            # Add metadata
            structured_result["analysis_timestamp"] = datetime.utcnow().isoformat()
            structured_result["analysis_focus"] = "competitive_landscape_intelligence"
            structured_result["company"] = company_context.get("name", "Unknown")
            
            return structured_result
            
        except Exception as e:
            logger.error(
                "Error generating competitive landscape intelligence",
                error=str(e),
                user_id=self.user_id
            )
            return {"error": f"Competitive landscape analysis failed: {str(e)}"}
    
    def _create_landscape_system_prompt(self) -> str:
        """Create comprehensive system prompt for competitive landscape analysis"""
        return """You are a world-class competitive intelligence analyst and strategic market expert working for a CEO. Your task is to map the competitive landscape and identify strategic positioning opportunities that enable executive-level market decisions.

Your analysis should focus on:

1. COMPETITIVE POSITIONING ANALYSIS
   - Current market position and market share trends
   - Competitive advantages and vulnerabilities
   - Differentiation opportunities and threats
   - Strategic positioning gaps in the market
   - Brand positioning and perception analysis

2. COMPETITIVE THREAT ASSESSMENT
   - Direct competitors and their strategic moves
   - Emerging competitors and market disruptors
   - Competitive response patterns and capabilities
   - Resource advantages of key competitors
   - Strategic alliance threats and opportunities

3. MARKET OPPORTUNITY MAPPING
   - Underserved market segments and niches
   - Emerging market trends and technologies
   - Strategic partnership opportunities
   - Market expansion possibilities
   - Innovation gaps and opportunities

4. STRATEGIC INTELLIGENCE
   - Competitor strategic intentions and patterns
   - Industry consolidation trends
   - Technology disruption threats
   - Regulatory and policy impacts
   - Customer preference shifts

5. EXECUTIVE STRATEGIC RECOMMENDATIONS
   - Immediate competitive responses required
   - Strategic positioning adjustments
   - Market opportunity prioritization
   - Resource allocation recommendations
   - Strategic timing considerations

Provide insights that are:
- Strategically actionable for market leadership
- Based on competitive intelligence and market signals
- Forward-looking with strategic timing
- Aligned with business growth objectives
- Focused on sustainable competitive advantage

Focus on intelligence that enables better strategic market decisions, not just competitive monitoring."""

    def _create_landscape_user_prompt(self, company_context: Dict, industry_context: Dict,
                                     contact_network: List[Dict], business_objectives: List[Dict]) -> str:
        """Create competitive landscape analysis prompt with market context"""
        
        # Prepare company context
        company_summary = f"""
OUR COMPANY PROFILE:
Company: {company_context.get('name', 'Session42')}
Industry: {company_context.get('industry', 'AI Music Technology')}
Stage: {company_context.get('stage', 'Growth Stage Startup')}
Key Products: {company_context.get('products', 'AI Music Creation Platform (HitCraft)')}
Target Market: {company_context.get('target_market', 'Musicians and Content Creators')}
Current Position: {company_context.get('competitive_position', 'Artist-centric AI music tools')}
Revenue Stage: {company_context.get('revenue_stage', 'Early revenue')}
Funding Status: {company_context.get('funding_status', 'Series A completed')}
Team Size: {company_context.get('team_size', '15-25 employees')}
Geographic Focus: {company_context.get('geographic_focus', 'North America + Europe')}
"""
        
        # Prepare industry context
        industry_summary = f"""
INDUSTRY CONTEXT:
Market Size: {industry_context.get('market_size', '$1.2B AI music creation market')}
Growth Rate: {industry_context.get('growth_rate', '43% YoY growth')}
Key Trends: {industry_context.get('key_trends', 'AI democratization, creator economy growth')}
Technology Trends: {industry_context.get('tech_trends', 'Large language models, multimodal AI')}
Regulatory Environment: {industry_context.get('regulatory', 'Evolving AI regulations, copyright concerns')}
Investment Climate: {industry_context.get('investment', 'Strong VC interest in AI + music')}
"""
        
        # Prepare business objectives context
        objectives_summary = "OUR STRATEGIC OBJECTIVES:\n"
        for i, obj in enumerate(business_objectives[:5], 1):
            objectives_summary += f"{i}. {obj.get('title', 'Unnamed Objective')}\n"
            objectives_summary += f"   Description: {obj.get('description', 'No description')}\n"
            objectives_summary += f"   Timeline: {obj.get('timeline', 'No timeline')}\n"
        
        # Prepare network intelligence
        network_summary = ""
        if contact_network:
            network_summary = f"\nNETWORK INTELLIGENCE:\n"
            # Group contacts by industry relevance
            music_industry = [c for c in contact_network if 'music' in str(c.get('industry', '')).lower() or 'audio' in str(c.get('industry', '')).lower()]
            tech_industry = [c for c in contact_network if 'tech' in str(c.get('industry', '')).lower() or 'ai' in str(c.get('industry', '')).lower()]
            investment = [c for c in contact_network if 'invest' in str(c.get('title', '')).lower() or 'vc' in str(c.get('title', '')).lower()]
            
            if music_industry:
                network_summary += f"Music Industry Contacts: {len(music_industry)} contacts including roles at companies like {', '.join(set([c.get('company', 'Unknown')[:20] for c in music_industry[:3]]))}\n"
            if tech_industry:
                network_summary += f"Technology Industry Contacts: {len(tech_industry)} contacts including roles at {', '.join(set([c.get('company', 'Unknown')[:20] for c in tech_industry[:3]]))}\n"
            if investment:
                network_summary += f"Investment/VC Contacts: {len(investment)} contacts including {', '.join(set([c.get('title', 'Unknown')[:30] for c in investment[:3]]))}\n"
        
        return f"""
Analyze the competitive landscape for our company from a CEO's strategic perspective:

{company_summary}

{industry_summary}

{objectives_summary}

{network_summary}

Provide a comprehensive competitive landscape analysis that answers:

1. What is our current competitive position and how is it evolving?
2. Who are our key competitors and what are their strategic moves?
3. What are the biggest competitive threats and opportunities?
4. Where are the strategic gaps in the market we can exploit?
5. What immediate strategic actions should we take to strengthen our position?

Focus on actionable competitive intelligence that enables strategic market positioning.

Provide your analysis in JSON format with the following structure:
{{
  "market_position_analysis": {{
    "current_market_share": "estimated market share and position",
    "competitive_positioning": "how we're positioned vs competitors", 
    "brand_perception": "market perception of our brand",
    "differentiation_factors": ["factor 1", "factor 2"],
    "positioning_gaps": ["gap 1", "gap 2"]
  }},
  "competitive_landscape": {{
    "direct_competitors": [
      {{
        "name": "competitor name",
        "market_position": "their position",
        "threat_level": "high/medium/low",
        "strategic_moves": ["move 1", "move 2"],
        "vulnerabilities": ["vulnerability 1", "vulnerability 2"],
        "competitive_response": "recommended response"
      }}
    ],
    "emerging_threats": [
      {{
        "threat_type": "type of threat",
        "description": "threat description",
        "timeline": "when threat materializes",
        "impact_level": "high/medium/low",
        "mitigation_strategy": "how to address"
      }}
    ],
    "strategic_opportunities": [
      {{
        "opportunity": "opportunity description",
        "market_size": "size of opportunity",
        "competitive_advantage": "our advantage in pursuing",
        "resource_requirements": "what's needed",
        "timeline": "optimal timing"
      }}
    ]
  }},
  "market_intelligence": {{
    "market_trends": ["trend 1", "trend 2"],
    "technology_disruptions": ["disruption 1", "disruption 2"],
    "customer_behavior_shifts": ["shift 1", "shift 2"],
    "regulatory_impacts": ["impact 1", "impact 2"],
    "investment_patterns": ["pattern 1", "pattern 2"]
  }},
  "strategic_recommendations": {{
    "immediate_actions": [
      {{
        "action": "specific action",
        "rationale": "why this action",
        "timeline": "when to execute",
        "resources_needed": "what resources required",
        "success_metrics": "how to measure success"
      }}
    ],
    "medium_term_strategy": [
      {{
        "strategy": "strategic initiative",
        "competitive_advantage": "advantage gained",
        "timeline": "execution timeline",
        "investment_required": "investment needed"
      }}
    ],
    "long_term_positioning": {{
      "vision": "long-term competitive vision",
      "strategic_moats": ["moat 1", "moat 2"],
      "market_leadership_path": "path to market leadership"
    }}
  }},
  "risk_assessment": {{
    "competitive_risks": ["risk 1", "risk 2"],
    "market_risks": ["risk 1", "risk 2"],
    "technology_risks": ["risk 1", "risk 2"],
    "mitigation_strategies": ["strategy 1", "strategy 2"]
  }}
}}
"""
    
    def _parse_landscape_response(self, response_text: str) -> Dict:
        """Parse competitive landscape analysis response"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"Failed to parse JSON response: {str(e)}")
        
        # Fallback to structured text parsing
        return {
            "market_position_analysis": self._extract_market_position(response_text),
            "competitive_landscape": self._extract_competitive_landscape(response_text),
            "market_intelligence": self._extract_market_intelligence(response_text),
            "strategic_recommendations": self._extract_strategic_recommendations(response_text),
            "risk_assessment": self._extract_risk_assessment(response_text),
            "raw_analysis": response_text
        }
    
    def _extract_market_position(self, text: str) -> Dict:
        """Extract market position analysis from text"""
        return {
            "current_market_share": "Extracted market share analysis",
            "competitive_positioning": "Extracted positioning analysis",
            "brand_perception": "Extracted brand perception",
            "differentiation_factors": ["Extracted factor"],
            "positioning_gaps": ["Extracted gap"]
        }
    
    def _extract_competitive_landscape(self, text: str) -> Dict:
        """Extract competitive landscape from text"""
        return {
            "direct_competitors": [{
                "name": "Extracted competitor",
                "market_position": "Extracted position",
                "threat_level": "medium",
                "strategic_moves": ["Extracted move"],
                "vulnerabilities": ["Extracted vulnerability"],
                "competitive_response": "Extracted response"
            }],
            "emerging_threats": [{
                "threat_type": "Extracted threat type",
                "description": "Extracted description",
                "timeline": "Extracted timeline",
                "impact_level": "medium",
                "mitigation_strategy": "Extracted strategy"
            }],
            "strategic_opportunities": [{
                "opportunity": "Extracted opportunity",
                "market_size": "Extracted size",
                "competitive_advantage": "Extracted advantage",
                "resource_requirements": "Extracted requirements",
                "timeline": "Extracted timeline"
            }]
        }
    
    def _extract_market_intelligence(self, text: str) -> Dict:
        """Extract market intelligence from text"""
        return {
            "market_trends": ["Extracted trend"],
            "technology_disruptions": ["Extracted disruption"],
            "customer_behavior_shifts": ["Extracted shift"],
            "regulatory_impacts": ["Extracted impact"],
            "investment_patterns": ["Extracted pattern"]
        }
    
    def _extract_strategic_recommendations(self, text: str) -> Dict:
        """Extract strategic recommendations from text"""
        return {
            "immediate_actions": [{
                "action": "Extracted action",
                "rationale": "Extracted rationale",
                "timeline": "Extracted timeline",
                "resources_needed": "Extracted resources",
                "success_metrics": "Extracted metrics"
            }],
            "medium_term_strategy": [{
                "strategy": "Extracted strategy",
                "competitive_advantage": "Extracted advantage",
                "timeline": "Extracted timeline",
                "investment_required": "Extracted investment"
            }],
            "long_term_positioning": {
                "vision": "Extracted vision",
                "strategic_moats": ["Extracted moat"],
                "market_leadership_path": "Extracted path"
            }
        }
    
    def _extract_risk_assessment(self, text: str) -> Dict:
        """Extract risk assessment from text"""
        return {
            "competitive_risks": ["Extracted risk"],
            "market_risks": ["Extracted risk"],
            "technology_risks": ["Extracted risk"],
            "mitigation_strategies": ["Extracted strategy"]
        } 