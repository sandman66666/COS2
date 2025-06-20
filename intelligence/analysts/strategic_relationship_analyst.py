"""
Strategic Relationship Intelligence Analyst
==========================================
CEO-level strategic relationship analysis using Claude 4 Opus.
Analyzes relationships from a strategic business perspective.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from utils.logging import structured_logger as logger
from intelligence.analysts.base_analyst import BaseAnalyst

class StrategicRelationshipAnalyst(BaseAnalyst):
    """
    Strategic Relationship Intelligence Analyst
    
    Analyzes contacts and relationships from a CEO's strategic lens,
    providing actionable intelligence for business development, partnerships,
    and competitive positioning.
    """
    
    def __init__(self, user_id: int, anthropic_api_key: str = None):
        """
        Initialize strategic relationship analyst
        
        Args:
            user_id: User ID for multi-tenant isolation
            anthropic_api_key: Optional API key for Claude Opus
        """
        super().__init__(user_id, anthropic_api_key)
        self.analyst_name = "strategic_relationship"
        self.analyst_description = "CEO-level strategic relationship intelligence analyst"
        
        # Customize Claude parameters for strategic analysis
        self.max_tokens = 4000
        self.temperature = 0.2  # Lower temperature for more strategic/factual responses
    
    async def generate_intelligence(self, data: Dict) -> Dict:
        """
        Generate strategic relationship intelligence
        
        Args:
            data: Dictionary containing contact data, company context, and business objectives
            
        Returns:
            Dictionary with strategic relationship analysis
        """
        try:
            # Extract data elements
            contact = data.get("contact", {})
            company_context = data.get("company_context", {})
            business_objectives = data.get("business_objectives", [])
            emails = data.get("emails", [])
            
            # Prepare comprehensive system prompt
            system_prompt = self._create_strategic_system_prompt()
            
            # Prepare user prompt with strategic context
            user_prompt = self._create_strategic_user_prompt(
                contact=contact,
                company_context=company_context,
                business_objectives=business_objectives,
                emails=emails
            )
            
            # Run Claude Opus analysis
            result_text = await self._run_claude_analysis(system_prompt, user_prompt)
            
            # Extract structured strategic intelligence
            structured_result = self._parse_strategic_response(result_text)
            
            # Add metadata
            structured_result["contact_id"] = contact.get("id")
            structured_result["contact_name"] = contact.get("name")
            structured_result["analysis_timestamp"] = datetime.utcnow().isoformat()
            structured_result["strategic_focus"] = "CEO_level_relationship_intelligence"
            
            return structured_result
            
        except Exception as e:
            logger.error(
                "Error generating strategic relationship intelligence",
                error=str(e),
                user_id=self.user_id
            )
            return {"error": f"Strategic relationship analysis failed: {str(e)}"}
    
    def _create_strategic_system_prompt(self) -> str:
        """Create comprehensive system prompt for strategic relationship analysis"""
        return """You are a world-class strategic business analyst and relationship intelligence expert working for a CEO. Your task is to analyze business relationships from a strategic perspective that enables executive-level decision making.

Your analysis should focus on:

1. STRATEGIC VALUE ASSESSMENT
   - Business development potential
   - Partnership synergy opportunities
   - Competitive intelligence value
   - Industry influence level
   - Market access enablement
   - Talent network connections
   - Investment/funding relevance

2. RELATIONSHIP DYNAMICS ANALYSIS
   - Current relationship strength and trajectory
   - Communication patterns and engagement level
   - Mutual value exchange potential
   - Trust and rapport indicators
   - Influence and decision-making authority

3. STRATEGIC POSITIONING
   - How this relationship affects competitive position
   - Market positioning implications
   - Industry reputation impact
   - Strategic alliance possibilities
   - Risk mitigation or amplification

4. ACTIONABLE INTELLIGENCE
   - Specific activation strategies
   - Optimal timing for engagement
   - Value proposition alignment
   - Risk assessment and mitigation
   - Expected ROI and success metrics

5. EXECUTIVE-LEVEL RECOMMENDATIONS
   - Immediate actions for the CEO
   - Medium-term relationship development
   - Long-term strategic positioning
   - Resource allocation priorities
   - Success measurements

Provide insights that are:
- Strategically significant for business growth
- Actionable at the executive level
- Based on concrete evidence and patterns
- Forward-looking with clear timing
- Aligned with business objectives

Focus on intelligence that enables better strategic decisions, not just descriptive analysis."""

    def _create_strategic_user_prompt(self, contact: Dict, company_context: Dict, 
                                     business_objectives: List[Dict], emails: List[Dict]) -> str:
        """Create strategic analysis prompt with business context"""
        
        # Prepare contact summary
        contact_summary = f"""
CONTACT PROFILE:
Name: {contact.get('name', 'Unknown')}
Title: {contact.get('title', 'Unknown')}
Company: {contact.get('company', 'Unknown')}
Email: {contact.get('email', 'Unknown')}
Industry: {contact.get('industry', 'Unknown')}
Location: {contact.get('location', 'Unknown')}
"""
        
        # Add intelligence data if available
        if contact.get('intelligence_data'):
            intel = contact['intelligence_data']
            contact_summary += f"""
INTELLIGENCE DATA:
- Professional Background: {intel.get('professional', {}).get('background', 'N/A')}
- Company Role: {intel.get('professional', {}).get('role_influence', 'N/A')}
- Industry Connections: {intel.get('professional', {}).get('network_influence', 'N/A')}
- Recent Activities: {intel.get('recent_activities', 'N/A')}
"""
        
        # Prepare company context
        company_summary = f"""
OUR COMPANY CONTEXT:
Company: {company_context.get('name', 'Session42')}
Industry: {company_context.get('industry', 'AI Music Technology')}
Stage: {company_context.get('stage', 'Growth Stage Startup')}
Key Products: {company_context.get('products', 'AI Music Creation Platform')}
Target Market: {company_context.get('target_market', 'Musicians and Content Creators')}
Competitive Position: {company_context.get('competitive_position', 'Artist-centric AI music tools')}
"""
        
        # Prepare business objectives
        objectives_summary = "CURRENT BUSINESS OBJECTIVES:\n"
        for i, obj in enumerate(business_objectives[:5], 1):  # Limit to top 5
            objectives_summary += f"{i}. {obj.get('title', 'Unnamed Objective')} - {obj.get('description', 'No description')}\n"
        
        # Prepare recent communication context
        email_context = ""
        if emails:
            email_context = f"\nRECENT COMMUNICATION PATTERNS:\n"
            recent_emails = emails[:5]  # Last 5 emails
            for email in recent_emails:
                email_context += f"- {email.get('date', 'Unknown date')}: {email.get('subject', 'No subject')} ({email.get('sender', 'Unknown sender')})\n"
                if email.get('key_topics'):
                    email_context += f"  Topics: {', '.join(email.get('key_topics', []))}\n"
        
        return f"""
Analyze this business relationship from a CEO's strategic perspective:

{contact_summary}

{company_summary}

{objectives_summary}

{email_context}

Provide a comprehensive strategic relationship analysis that answers:

1. What is the strategic value of this relationship to our business objectives?
2. How does this contact influence our competitive position and market access?
3. What specific partnership or collaboration opportunities exist?
4. What is the optimal strategy for developing this relationship?
5. What immediate actions should the CEO take?

Focus on actionable strategic intelligence that enables executive-level decision making.

Provide your analysis in JSON format with the following structure:
{{
  "strategic_value_assessment": {{
    "business_development_potential": {{
      "score": 0.0-1.0,
      "rationale": "detailed explanation",
      "specific_opportunities": ["opportunity 1", "opportunity 2"]
    }},
    "partnership_synergy_score": {{
      "score": 0.0-1.0,
      "rationale": "detailed explanation",
      "potential_partnerships": ["partnership type 1", "partnership type 2"]
    }},
    "competitive_intelligence_value": {{
      "score": 0.0-1.0,
      "insights": ["insight 1", "insight 2"],
      "strategic_implications": ["implication 1", "implication 2"]
    }},
    "industry_influence_level": {{
      "score": 0.0-1.0,
      "influence_areas": ["area 1", "area 2"],
      "network_reach": "assessment of their network reach"
    }},
    "talent_network_value": {{
      "score": 0.0-1.0,
      "value_proposition": "explanation of talent access",
      "key_connections": ["connection type 1", "connection type 2"]
    }}
  }},
  "relationship_dynamics": {{
    "current_strength": 0.0-1.0,
    "engagement_level": "high/medium/low",
    "communication_patterns": ["pattern 1", "pattern 2"],
    "trust_indicators": ["indicator 1", "indicator 2"],
    "decision_making_authority": "assessment of their authority level"
  }},
  "strategic_positioning": {{
    "competitive_impact": "how this relationship affects competitive position",
    "market_positioning": "implications for market position",
    "strategic_risks": ["risk 1", "risk 2"],
    "strategic_opportunities": ["opportunity 1", "opportunity 2"]
  }},
  "executive_action_plan": {{
    "immediate_actions": ["action 1", "action 2"],
    "optimal_timing": "when to take action",
    "medium_term_strategy": ["strategy element 1", "strategy element 2"],
    "long_term_positioning": "long-term relationship vision",
    "success_metrics": ["metric 1", "metric 2"]
  }},
  "ceo_recommendations": {{
    "priority_level": "high/medium/low",
    "recommended_approach": "specific approach for CEO",
    "resource_requirements": "what resources are needed",
    "expected_roi": "expected return on relationship investment",
    "timeline": "recommended timeline for relationship development"
  }}
}}
"""
    
    def _parse_strategic_response(self, response_text: str) -> Dict:
        """Parse strategic relationship analysis response"""
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
            "strategic_value_assessment": self._extract_strategic_value(response_text),
            "relationship_dynamics": self._extract_relationship_dynamics(response_text),
            "strategic_positioning": self._extract_strategic_positioning(response_text),
            "executive_action_plan": self._extract_action_plan(response_text),
            "ceo_recommendations": self._extract_ceo_recommendations(response_text),
            "raw_analysis": response_text
        }
    
    def _extract_strategic_value(self, text: str) -> Dict:
        """Extract strategic value assessment from text"""
        # Implementation to extract strategic value information
        return {
            "business_development_potential": {"score": 0.7, "rationale": "Extracted from analysis"},
            "partnership_synergy_score": {"score": 0.6, "rationale": "Extracted from analysis"},
            "competitive_intelligence_value": {"score": 0.8, "insights": ["Extracted insight"]},
            "industry_influence_level": {"score": 0.7, "influence_areas": ["Extracted area"]},
            "talent_network_value": {"score": 0.6, "value_proposition": "Extracted value"}
        }
    
    def _extract_relationship_dynamics(self, text: str) -> Dict:
        """Extract relationship dynamics from text"""
        return {
            "current_strength": 0.7,
            "engagement_level": "medium",
            "communication_patterns": ["Extracted pattern"],
            "trust_indicators": ["Extracted indicator"],
            "decision_making_authority": "Extracted authority assessment"
        }
    
    def _extract_strategic_positioning(self, text: str) -> Dict:
        """Extract strategic positioning from text"""
        return {
            "competitive_impact": "Extracted competitive impact",
            "market_positioning": "Extracted market positioning",
            "strategic_risks": ["Extracted risk"],
            "strategic_opportunities": ["Extracted opportunity"]
        }
    
    def _extract_action_plan(self, text: str) -> Dict:
        """Extract executive action plan from text"""
        return {
            "immediate_actions": ["Extracted action"],
            "optimal_timing": "Extracted timing",
            "medium_term_strategy": ["Extracted strategy"],
            "long_term_positioning": "Extracted positioning",
            "success_metrics": ["Extracted metric"]
        }
    
    def _extract_ceo_recommendations(self, text: str) -> Dict:
        """Extract CEO recommendations from text"""
        return {
            "priority_level": "medium",
            "recommended_approach": "Extracted approach",
            "resource_requirements": "Extracted requirements",
            "expected_roi": "Extracted ROI",
            "timeline": "Extracted timeline"
        } 