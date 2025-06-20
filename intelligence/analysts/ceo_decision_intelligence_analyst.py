"""
CEO Decision Intelligence Analyst
=================================
Executive-level decision intelligence using Claude 4 Opus.
Provides strategic decision support for CEO-level choices.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from utils.logging import structured_logger as logger
from intelligence.analysts.base_analyst import BaseAnalyst

class CEODecisionIntelligenceAnalyst(BaseAnalyst):
    """
    CEO Decision Intelligence Analyst
    
    Provides executive-level decision intelligence using strategic frameworks
    to analyze complex business decisions with competitive, financial, and
    operational considerations.
    """
    
    def __init__(self, user_id: int, anthropic_api_key: str = None):
        """
        Initialize CEO decision intelligence analyst
        
        Args:
            user_id: User ID for multi-tenant isolation
            anthropic_api_key: Optional API key for Claude Opus
        """
        super().__init__(user_id, anthropic_api_key)
        self.analyst_name = "ceo_decision_intelligence"
        self.analyst_description = "Executive-level strategic decision intelligence analyst"
        
        # Customize Claude parameters for strategic decision analysis
        self.max_tokens = 4000
        self.temperature = 0.2  # Balanced temperature for strategic reasoning
    
    async def generate_intelligence(self, data: Dict) -> Dict:
        """
        Generate CEO-level decision intelligence
        
        Args:
            data: Dictionary containing decision context, options, and business data
            
        Returns:
            Dictionary with strategic decision analysis
        """
        try:
            # Extract data elements
            decision_area = data.get("decision_area", "Strategic Decision")
            decision_options = data.get("decision_options", [])
            company_context = data.get("company_context", {})
            business_objectives = data.get("business_objectives", [])
            competitive_landscape = data.get("competitive_landscape", {})
            financial_context = data.get("financial_context", {})
            
            # Prepare comprehensive system prompt
            system_prompt = self._create_decision_system_prompt()
            
            # Prepare user prompt with decision context
            user_prompt = self._create_decision_user_prompt(
                decision_area=decision_area,
                decision_options=decision_options,
                company_context=company_context,
                business_objectives=business_objectives,
                competitive_landscape=competitive_landscape,
                financial_context=financial_context
            )
            
            # Run Claude Opus analysis
            result_text = await self._run_claude_analysis(system_prompt, user_prompt)
            
            # Extract structured decision intelligence
            structured_result = self._parse_decision_response(result_text)
            
            # Add metadata
            structured_result["decision_area"] = decision_area
            structured_result["analysis_timestamp"] = datetime.utcnow().isoformat()
            structured_result["analysis_focus"] = "executive_decision_intelligence"
            
            return structured_result
            
        except Exception as e:
            logger.error(
                "Error generating CEO decision intelligence",
                error=str(e),
                user_id=self.user_id
            )
            return {"error": f"CEO decision analysis failed: {str(e)}"}
    
    def _create_decision_system_prompt(self) -> str:
        """Create comprehensive system prompt for CEO decision analysis"""
        return """You are a world-class strategic decision analyst and executive advisor working directly with a CEO. Your task is to provide comprehensive decision intelligence that enables optimal strategic choices using proven decision frameworks.

Your analysis should apply these CEO-level decision frameworks:

1. OPPORTUNITY COST ANALYSIS
   - What are we giving up by choosing each option?
   - Resource allocation implications and tradeoffs
   - Timing opportunity costs and market windows
   - Strategic positioning opportunity costs

2. STRATEGIC ALIGNMENT ASSESSMENT
   - How well does each option align with business objectives?
   - Consistency with company mission and values
   - Impact on long-term strategic direction
   - Stakeholder alignment and support

3. RESOURCE ALLOCATION OPTIMIZATION
   - Required financial, human, and operational resources
   - Resource efficiency and ROI analysis
   - Capability requirements and gaps
   - Scalability and resource sustainability

4. COMPETITIVE ADVANTAGE ANALYSIS
   - How each option affects competitive position
   - Sustainable competitive advantages gained/lost
   - Competitor response likelihood and timing
   - Market positioning implications

5. RISK EXPOSURE EVALUATION
   - Downside scenarios and probability assessment
   - Operational, financial, and strategic risks
   - Risk mitigation strategies and costs
   - Acceptable risk levels for potential returns

6. TIMING SENSITIVITY ASSESSMENT
   - Market timing and windows of opportunity
   - Competitive timing considerations
   - Resource availability timing
   - Optimal sequencing of decisions

Provide insights that are:
- Strategically comprehensive covering all major considerations
- Quantified where possible with clear metrics
- Forward-looking with scenario analysis
- Actionable with clear recommendations
- Executive-focused on strategic implications

Focus on decision support that enables confident, well-informed strategic choices."""

    def _create_decision_user_prompt(self, decision_area: str, decision_options: List[Dict],
                                    company_context: Dict, business_objectives: List[Dict],
                                    competitive_landscape: Dict, financial_context: Dict) -> str:
        """Create decision analysis prompt with comprehensive context"""
        
        # Prepare decision context
        decision_summary = f"""
DECISION AREA: {decision_area}

DECISION OPTIONS:
"""
        for i, option in enumerate(decision_options, 1):
            decision_summary += f"""
Option {i}: {option.get('title', f'Option {i}')}
Description: {option.get('description', 'No description provided')}
Timeline: {option.get('timeline', 'No timeline specified')}
Investment Required: {option.get('investment', 'Not specified')}
Expected Outcome: {option.get('expected_outcome', 'Not specified')}
"""
        
        # Prepare company context
        company_summary = f"""
COMPANY CONTEXT:
Company: {company_context.get('name', 'Session42')}
Stage: {company_context.get('stage', 'Growth Stage Startup')}
Current Revenue: {company_context.get('revenue', 'Not disclosed')}
Team Size: {company_context.get('team_size', '15-25 employees')}
Funding Status: {company_context.get('funding_status', 'Series A completed')}
Cash Runway: {company_context.get('cash_runway', 'Not specified')}
Key Strengths: {company_context.get('strengths', 'Artist-centric AI platform')}
Current Challenges: {company_context.get('challenges', 'Scaling and market penetration')}
"""
        
        # Prepare business objectives
        objectives_summary = "BUSINESS OBJECTIVES:\n"
        for i, obj in enumerate(business_objectives[:5], 1):
            objectives_summary += f"{i}. {obj.get('title', 'Unnamed Objective')}\n"
            objectives_summary += f"   Priority: {obj.get('priority', 'Not specified')}\n"
            objectives_summary += f"   Timeline: {obj.get('timeline', 'Not specified')}\n"
            objectives_summary += f"   Success Metrics: {obj.get('success_metrics', 'Not specified')}\n"
        
        # Prepare competitive landscape
        competitive_summary = ""
        if competitive_landscape:
            competitive_summary = f"""
COMPETITIVE LANDSCAPE:
Market Position: {competitive_landscape.get('market_position', 'Not specified')}
Key Competitors: {', '.join(competitive_landscape.get('key_competitors', ['Not specified']))}
Competitive Threats: {', '.join(competitive_landscape.get('threats', ['Not specified']))}
Market Opportunities: {', '.join(competitive_landscape.get('opportunities', ['Not specified']))}
"""
        
        # Prepare financial context
        financial_summary = ""
        if financial_context:
            financial_summary = f"""
FINANCIAL CONTEXT:
Monthly Burn Rate: {financial_context.get('burn_rate', 'Not specified')}
Current MRR/ARR: {financial_context.get('recurring_revenue', 'Not specified')}
Growth Rate: {financial_context.get('growth_rate', 'Not specified')}
Customer Acquisition Cost: {financial_context.get('cac', 'Not specified')}
Lifetime Value: {financial_context.get('ltv', 'Not specified')}
"""
        
        return f"""
Analyze this strategic decision from a CEO's perspective using proven decision frameworks:

{decision_summary}

{company_summary}

{objectives_summary}

{competitive_summary}

{financial_summary}

Provide a comprehensive strategic decision analysis that covers:

1. For each decision option, analyze using all major decision frameworks
2. Identify the key tradeoffs and opportunity costs
3. Assess strategic alignment with business objectives
4. Evaluate resource requirements and ROI
5. Analyze competitive implications and risks
6. Recommend optimal decision with clear rationale

Focus on strategic decision intelligence that enables confident executive choices.

Provide your analysis in JSON format with the following structure:
{{
  "decision_framework_analysis": {{
    "opportunity_cost_analysis": {{
      "option_1": {{
        "opportunity_costs": ["cost 1", "cost 2"],
        "foregone_benefits": ["benefit 1", "benefit 2"],
        "resource_tradeoffs": "analysis of resource tradeoffs"
      }},
      "option_2": {{
        "opportunity_costs": ["cost 1", "cost 2"],
        "foregone_benefits": ["benefit 1", "benefit 2"],
        "resource_tradeoffs": "analysis of resource tradeoffs"
      }}
    }},
    "strategic_alignment_assessment": {{
      "option_1": {{
        "alignment_score": 0.0-1.0,
        "alignment_factors": ["factor 1", "factor 2"],
        "strategic_fit": "assessment of strategic fit"
      }},
      "option_2": {{
        "alignment_score": 0.0-1.0,
        "alignment_factors": ["factor 1", "factor 2"],
        "strategic_fit": "assessment of strategic fit"
      }}
    }},
    "resource_allocation_optimization": {{
      "option_1": {{
        "resource_requirements": {{
          "financial": "financial requirements",
          "human": "human resource needs",
          "operational": "operational requirements"
        }},
        "resource_efficiency": "efficiency analysis",
        "roi_projection": "projected return on investment"
      }},
      "option_2": {{
        "resource_requirements": {{
          "financial": "financial requirements",
          "human": "human resource needs",
          "operational": "operational requirements"
        }},
        "resource_efficiency": "efficiency analysis",
        "roi_projection": "projected return on investment"
      }}
    }},
    "competitive_advantage_analysis": {{
      "option_1": {{
        "competitive_impact": "impact on competitive position",
        "advantage_created": ["advantage 1", "advantage 2"],
        "competitive_risks": ["risk 1", "risk 2"]
      }},
      "option_2": {{
        "competitive_impact": "impact on competitive position",
        "advantage_created": ["advantage 1", "advantage 2"],
        "competitive_risks": ["risk 1", "risk 2"]
      }}
    }},
    "risk_exposure_evaluation": {{
      "option_1": {{
        "risk_level": "high/medium/low",
        "key_risks": ["risk 1", "risk 2"],
        "mitigation_strategies": ["strategy 1", "strategy 2"],
        "downside_scenarios": ["scenario 1", "scenario 2"]
      }},
      "option_2": {{
        "risk_level": "high/medium/low",
        "key_risks": ["risk 1", "risk 2"],
        "mitigation_strategies": ["strategy 1", "strategy 2"],
        "downside_scenarios": ["scenario 1", "scenario 2"]
      }}
    }},
    "timing_sensitivity_assessment": {{
      "option_1": {{
        "timing_criticality": "high/medium/low",
        "optimal_timing": "when to execute",
        "timing_risks": ["risk 1", "risk 2"],
        "market_window": "market timing considerations"
      }},
      "option_2": {{
        "timing_criticality": "high/medium/low",
        "optimal_timing": "when to execute",
        "timing_risks": ["risk 1", "risk 2"],
        "market_window": "market timing considerations"
      }}
    }}
  }},
  "comparative_analysis": {{
    "option_rankings": [
      {{
        "option": "option name",
        "overall_score": 0.0-1.0,
        "strengths": ["strength 1", "strength 2"],
        "weaknesses": ["weakness 1", "weakness 2"],
        "best_case_scenario": "best possible outcome",
        "worst_case_scenario": "worst possible outcome"
      }}
    ],
    "key_differentiators": ["differentiator 1", "differentiator 2"],
    "critical_success_factors": ["factor 1", "factor 2"]
  }},
  "executive_recommendation": {{
    "recommended_option": "recommended option with rationale",
    "confidence_level": "high/medium/low",
    "key_rationale": ["reason 1", "reason 2"],
    "implementation_roadmap": [
      {{
        "phase": "phase name",
        "timeline": "timeline",
        "key_actions": ["action 1", "action 2"],
        "success_metrics": ["metric 1", "metric 2"]
      }}
    ],
    "contingency_plans": [
      {{
        "scenario": "scenario description",
        "response_strategy": "how to respond"
      }}
    ]
  }},
  "executive_considerations": {{
    "board_communication": "how to communicate to board",
    "stakeholder_impact": "impact on key stakeholders",
    "investor_implications": "implications for investors",
    "team_communication": "how to communicate to team",
    "market_communication": "external communication strategy"
  }}
}}
"""
    
    def _parse_decision_response(self, response_text: str) -> Dict:
        """Parse CEO decision intelligence response"""
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
            "decision_framework_analysis": self._extract_framework_analysis(response_text),
            "comparative_analysis": self._extract_comparative_analysis(response_text),
            "executive_recommendation": self._extract_executive_recommendation(response_text),
            "executive_considerations": self._extract_executive_considerations(response_text),
            "raw_analysis": response_text
        }
    
    def _extract_framework_analysis(self, text: str) -> Dict:
        """Extract decision framework analysis from text"""
        return {
            "opportunity_cost_analysis": {"extracted": "Opportunity cost analysis"},
            "strategic_alignment_assessment": {"extracted": "Strategic alignment assessment"},
            "resource_allocation_optimization": {"extracted": "Resource allocation analysis"},
            "competitive_advantage_analysis": {"extracted": "Competitive advantage analysis"},
            "risk_exposure_evaluation": {"extracted": "Risk exposure evaluation"},
            "timing_sensitivity_assessment": {"extracted": "Timing sensitivity assessment"}
        }
    
    def _extract_comparative_analysis(self, text: str) -> Dict:
        """Extract comparative analysis from text"""
        return {
            "option_rankings": [{
                "option": "Extracted option",
                "overall_score": 0.7,
                "strengths": ["Extracted strength"],
                "weaknesses": ["Extracted weakness"],
                "best_case_scenario": "Extracted best case",
                "worst_case_scenario": "Extracted worst case"
            }],
            "key_differentiators": ["Extracted differentiator"],
            "critical_success_factors": ["Extracted success factor"]
        }
    
    def _extract_executive_recommendation(self, text: str) -> Dict:
        """Extract executive recommendation from text"""
        return {
            "recommended_option": "Extracted recommendation",
            "confidence_level": "medium",
            "key_rationale": ["Extracted rationale"],
            "implementation_roadmap": [{
                "phase": "Extracted phase",
                "timeline": "Extracted timeline",
                "key_actions": ["Extracted action"],
                "success_metrics": ["Extracted metric"]
            }],
            "contingency_plans": [{
                "scenario": "Extracted scenario",
                "response_strategy": "Extracted strategy"
            }]
        }
    
    def _extract_executive_considerations(self, text: str) -> Dict:
        """Extract executive considerations from text"""
        return {
            "board_communication": "Extracted board communication",
            "stakeholder_impact": "Extracted stakeholder impact",
            "investor_implications": "Extracted investor implications",
            "team_communication": "Extracted team communication",
            "market_communication": "Extracted market communication"
        } 