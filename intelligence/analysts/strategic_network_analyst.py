"""
Strategic Network Intelligence Analyst
=====================================
CEO-level network analysis using Claude 4 Opus.
Maps professional networks to strategic business objectives.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from utils.logging import structured_logger as logger
from intelligence.analysts.base_analyst import BaseAnalyst

class StrategicNetworkAnalyst(BaseAnalyst):
    """
    Strategic Network Intelligence Analyst
    
    Maps professional networks to strategic business objectives,
    identifying key connectors, strategic gaps, and activation opportunities
    for achieving business goals.
    """
    
    def __init__(self, user_id: int, anthropic_api_key: str = None):
        """
        Initialize strategic network analyst
        
        Args:
            user_id: User ID for multi-tenant isolation
            anthropic_api_key: Optional API key for Claude Opus
        """
        super().__init__(user_id, anthropic_api_key)
        self.analyst_name = "strategic_network"
        self.analyst_description = "CEO-level strategic network intelligence analyst"
        
        # Customize Claude parameters for network analysis
        self.max_tokens = 4000
        self.temperature = 0.3  # Balanced temperature for strategic networking insights
    
    async def generate_intelligence(self, data: Dict) -> Dict:
        """
        Generate strategic network intelligence
        
        Args:
            data: Dictionary containing contacts, business objectives, and company context
            
        Returns:
            Dictionary with strategic network analysis
        """
        try:
            # Extract data elements
            contacts = data.get("contacts", [])
            business_objectives = data.get("business_objectives", [])
            company_context = data.get("company_context", {})
            recent_interactions = data.get("recent_interactions", [])
            
            # Prepare comprehensive system prompt
            system_prompt = self._create_network_system_prompt()
            
            # Prepare user prompt with network context
            user_prompt = self._create_network_user_prompt(
                contacts=contacts,
                business_objectives=business_objectives,
                company_context=company_context,
                recent_interactions=recent_interactions
            )
            
            # Run Claude Opus analysis
            result_text = await self._run_claude_analysis(system_prompt, user_prompt)
            
            # Extract structured network intelligence
            structured_result = self._parse_network_response(result_text)
            
            # Add metadata
            structured_result["analysis_timestamp"] = datetime.utcnow().isoformat()
            structured_result["analysis_focus"] = "strategic_network_intelligence"
            structured_result["total_contacts_analyzed"] = len(contacts)
            structured_result["objectives_mapped"] = len(business_objectives)
            
            return structured_result
            
        except Exception as e:
            logger.error(
                "Error generating strategic network intelligence",
                error=str(e),
                user_id=self.user_id
            )
            return {"error": f"Strategic network analysis failed: {str(e)}"}
    
    def _create_network_system_prompt(self) -> str:
        """Create comprehensive system prompt for strategic network analysis"""
        return """You are a world-class strategic network analyst and relationship strategist working for a CEO. Your task is to map professional networks to business objectives and identify strategic activation opportunities that enable business growth.

Your analysis should focus on:

1. OBJECTIVE-NETWORK MAPPING
   - Map contacts to specific business objectives
   - Identify network coverage gaps for each objective
   - Assess contact relevance and potential impact
   - Prioritize relationships by strategic value

2. STRATEGIC NETWORK TOPOLOGY
   - Identify key network connectors and influencers
   - Map relationship clusters and ecosystems
   - Find hidden connections and relationship paths
   - Assess network diversity and strategic reach

3. ACTIVATION STRATEGY DEVELOPMENT
   - Create specific activation approaches for each objective
   - Develop relationship warming and engagement strategies
   - Identify optimal timing for strategic outreach
   - Plan network expansion and relationship building

4. STRATEGIC GAP ANALYSIS
   - Identify critical network gaps for business objectives
   - Prioritize network expansion opportunities
   - Map competitive network advantages
   - Assess network risk and dependency concentration

5. NETWORK INTELLIGENCE SYNTHESIS
   - Cross-reference relationship patterns and insights
   - Identify emerging opportunities from network signals
   - Map industry influence and decision-making networks
   - Provide strategic relationship investment priorities

Provide insights that are:
- Strategically actionable for business objective achievement
- Relationship-focused with specific activation guidance
- Network-optimized for maximum strategic leverage
- Timing-sensitive with clear priority sequences
- ROI-focused on high-impact relationship investments

Focus on network intelligence that enables strategic relationship leverage for business growth."""

    def _create_network_user_prompt(self, contacts: List[Dict], business_objectives: List[Dict],
                                   company_context: Dict, recent_interactions: List[Dict]) -> str:
        """Create network analysis prompt with comprehensive relationship context"""
        
        # Prepare company context
        company_summary = f"""
OUR COMPANY PROFILE:
Company: {company_context.get('name', 'Session42')}
Industry: {company_context.get('industry', 'AI Music Technology')}
Stage: {company_context.get('stage', 'Growth Stage Startup')}
Key Products: {company_context.get('products', 'AI Music Creation Platform')}
Current Focus: {company_context.get('current_focus', 'Scaling user base and revenue')}
Team Size: {company_context.get('team_size', '15-25 employees')}
Geographic Markets: {company_context.get('markets', 'North America, Europe')}
"""
        
        # Prepare business objectives
        objectives_summary = "STRATEGIC BUSINESS OBJECTIVES:\n"
        for i, obj in enumerate(business_objectives[:6], 1):  # Top 6 objectives
            objectives_summary += f"{i}. {obj.get('title', 'Unnamed Objective')}\n"
            objectives_summary += f"   Description: {obj.get('description', 'No description')}\n"
            objectives_summary += f"   Timeline: {obj.get('timeline', 'Not specified')}\n"
            objectives_summary += f"   Success Metrics: {obj.get('success_metrics', 'Not specified')}\n"
            objectives_summary += f"   Priority Level: {obj.get('priority', 'Medium')}\n\n"
        
        # Prepare network overview
        network_summary = f"PROFESSIONAL NETWORK OVERVIEW:\n"
        network_summary += f"Total Contacts: {len(contacts)}\n"
        
        # Categorize contacts by industry/role
        categories = {}
        for contact in contacts:
            industry = contact.get('industry', 'Unknown').title()
            role_type = self._categorize_role(contact.get('title', ''))
            category = f"{industry} - {role_type}"
            categories[category] = categories.get(category, 0) + 1
        
        network_summary += "\nNetwork Distribution:\n"
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
            network_summary += f"- {category}: {count} contacts\n"
        
        # Prepare detailed contact profiles for key contacts
        contact_profiles = "\nKEY CONTACT PROFILES:\n"
        # Select top contacts based on intelligence data or company prominence
        key_contacts = sorted(contacts, key=lambda x: self._calculate_contact_importance(x), reverse=True)[:20]
        
        for i, contact in enumerate(key_contacts, 1):
            contact_profiles += f"{i}. {contact.get('name', 'Unknown')}\n"
            contact_profiles += f"   Title: {contact.get('title', 'Unknown')}\n"
            contact_profiles += f"   Company: {contact.get('company', 'Unknown')}\n"
            contact_profiles += f"   Industry: {contact.get('industry', 'Unknown')}\n"
            
            # Add intelligence data if available
            if contact.get('intelligence_data'):
                intel = contact['intelligence_data']
                contact_profiles += f"   Influence: {intel.get('professional', {}).get('network_influence', 'Unknown')}\n"
                contact_profiles += f"   Role Power: {intel.get('professional', {}).get('role_influence', 'Unknown')}\n"
            
            contact_profiles += "\n"
        
        # Prepare recent interaction context
        interaction_summary = ""
        if recent_interactions:
            interaction_summary = f"\nRECENT NETWORK INTERACTIONS:\n"
            for interaction in recent_interactions[:10]:  # Last 10 interactions
                interaction_summary += f"- {interaction.get('date', 'Unknown')}: {interaction.get('type', 'Contact')} with {interaction.get('contact_name', 'Unknown')}\n"
                interaction_summary += f"  Context: {interaction.get('context', 'No context')}\n"
        
        return f"""
Analyze our professional network from a strategic business perspective:

{company_summary}

{objectives_summary}

{network_summary}

{contact_profiles}

{interaction_summary}

Provide a comprehensive strategic network analysis that maps our network to business objectives:

1. For each business objective, identify which contacts are most relevant and how to activate them
2. Map network topology to identify key connectors and influence patterns
3. Identify strategic gaps where we need new relationships
4. Create specific activation strategies for priority objectives
5. Recommend network expansion and relationship development priorities

Focus on actionable network intelligence that enables strategic relationship leverage.

Provide your analysis in JSON format with the following structure:
{{
  "objective_network_mapping": {{
    "objective_1": {{
      "objective_title": "objective name",
      "relevant_contacts": [
        {{
          "contact_name": "contact name",
          "relevance_score": 0.0-1.0,
          "relevance_factors": ["factor 1", "factor 2"],
          "activation_approach": "specific approach for this contact",
          "optimal_timing": "when to engage",
          "expected_value": "potential value from relationship"
        }}
      ],
      "network_coverage_score": 0.0-1.0,
      "critical_gaps": ["gap 1", "gap 2"],
      "activation_strategy": {{
        "phase_1": "immediate actions (0-30 days)",
        "phase_2": "medium-term development (1-3 months)",
        "phase_3": "long-term cultivation (3-12 months)"
      }},
      "success_metrics": ["metric 1", "metric 2"]
    }}
  }},
  "network_topology_analysis": {{
    "key_connectors": [
      {{
        "contact_name": "connector name",
        "connector_score": 0.0-1.0,
        "network_reach": "assessment of their network reach",
        "influence_areas": ["area 1", "area 2"],
        "strategic_value": "why they're strategically valuable",
        "relationship_investment": "how to invest in this relationship"
      }}
    ],
    "network_clusters": [
      {{
        "cluster_name": "cluster description",
        "key_members": ["member 1", "member 2"],
        "strategic_importance": "why this cluster matters",
        "engagement_strategy": "how to engage with this cluster"
      }}
    ],
    "influence_pathways": [
      {{
        "target": "target person/decision",
        "pathway": ["contact 1", "contact 2", "target"],
        "pathway_strength": 0.0-1.0,
        "activation_approach": "how to activate this pathway"
      }}
    ]
  }},
  "strategic_gap_analysis": {{
    "critical_network_gaps": [
      {{
        "gap_area": "area where network is weak",
        "business_impact": "how this gap affects business objectives",
        "target_profiles": ["type of contact needed 1", "type 2"],
        "acquisition_strategy": "how to fill this gap",
        "priority_level": "high/medium/low",
        "timeline": "when to address this gap"
      }}
    ],
    "network_expansion_priorities": [
      {{
        "expansion_area": "area to expand into",
        "strategic_rationale": "why expand here",
        "target_characteristics": "ideal contact characteristics",
        "connection_strategy": "how to make connections",
        "investment_required": "time/resources needed"
      }}
    ]
  }},
  "activation_roadmap": {{
    "immediate_priorities": [
      {{
        "action": "specific action to take",
        "contacts_involved": ["contact 1", "contact 2"],
        "objective_alignment": "which business objective this serves",
        "timeline": "when to execute",
        "success_criteria": "how to measure success"
      }}
    ],
    "relationship_development_pipeline": [
      {{
        "relationship_stage": "current/developing/target",
        "contacts": ["contact names"],
        "development_actions": ["action 1", "action 2"],
        "timeline": "development timeline",
        "investment_level": "high/medium/low"
      }}
    ],
    "network_expansion_plan": [
      {{
        "expansion_goal": "what we want to achieve",
        "target_network": "specific network/community to enter",
        "entry_strategy": "how to gain access",
        "key_facilitators": "contacts who can help",
        "timeline": "expansion timeline"
      }}
    ]
  }},
  "strategic_recommendations": {{
    "high_impact_opportunities": [
      {{
        "opportunity": "specific opportunity description",
        "contacts_involved": ["contact names"],
        "business_objective": "which objective this advances",
        "implementation_approach": "how to pursue",
        "timeline": "optimal timing",
        "success_probability": 0.0-1.0
      }}
    ],
    "relationship_investment_priorities": [
      {{
        "contact_name": "contact to prioritize",
        "investment_rationale": "why prioritize this relationship",
        "investment_approach": "how to invest in relationship",
        "expected_roi": "expected business value",
        "timeline": "investment timeline"
      }}
    ],
    "network_optimization_actions": [
      {{
        "optimization": "specific optimization to make",
        "current_limitation": "what's limiting us now",
        "optimization_approach": "how to optimize",
        "resource_requirements": "what's needed",
        "expected_benefit": "anticipated improvement"
      }}
    ]
  }}
}}
"""
    
    def _categorize_role(self, title: str) -> str:
        """Categorize contact role for network analysis"""
        title_lower = title.lower()
        
        if any(term in title_lower for term in ['ceo', 'founder', 'president']):
            return 'Executive Leadership'
        elif any(term in title_lower for term in ['cto', 'engineering', 'technical', 'developer']):
            return 'Technology'
        elif any(term in title_lower for term in ['invest', 'vc', 'partner', 'fund']):
            return 'Investment'
        elif any(term in title_lower for term in ['marketing', 'growth', 'business development']):
            return 'Business Development'
        elif any(term in title_lower for term in ['product', 'design', 'ux']):
            return 'Product'
        elif any(term in title_lower for term in ['sales', 'revenue', 'partnerships']):
            return 'Sales & Partnerships'
        else:
            return 'Other Professional'
    
    def _calculate_contact_importance(self, contact: Dict) -> float:
        """Calculate strategic importance score for contact prioritization"""
        score = 0.0
        
        # Company prominence (rough heuristic)
        company = contact.get('company', '').lower()
        if any(prominent in company for prominent in ['google', 'apple', 'microsoft', 'amazon', 'meta', 'spotify', 'netflix']):
            score += 0.4
        elif any(relevant in company for relevant in ['music', 'audio', 'media', 'entertainment']):
            score += 0.3
        
        # Title seniority
        title = contact.get('title', '').lower()
        if any(senior in title for senior in ['ceo', 'founder', 'president', 'vp', 'director']):
            score += 0.3
        elif any(mid in title for mid in ['manager', 'lead', 'senior']):
            score += 0.2
        
        # Intelligence data boost
        if contact.get('intelligence_data'):
            score += 0.3
        
        return min(score, 1.0)
    
    def _parse_network_response(self, response_text: str) -> Dict:
        """Parse strategic network analysis response"""
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
            "objective_network_mapping": self._extract_objective_mapping(response_text),
            "network_topology_analysis": self._extract_topology_analysis(response_text),
            "strategic_gap_analysis": self._extract_gap_analysis(response_text),
            "activation_roadmap": self._extract_activation_roadmap(response_text),
            "strategic_recommendations": self._extract_strategic_recommendations(response_text),
            "raw_analysis": response_text
        }
    
    def _extract_objective_mapping(self, text: str) -> Dict:
        """Extract objective-network mapping from text"""
        return {
            "objective_1": {
                "objective_title": "Extracted objective",
                "relevant_contacts": [{
                    "contact_name": "Extracted contact",
                    "relevance_score": 0.7,
                    "relevance_factors": ["Extracted factor"],
                    "activation_approach": "Extracted approach",
                    "optimal_timing": "Extracted timing",
                    "expected_value": "Extracted value"
                }],
                "network_coverage_score": 0.6,
                "critical_gaps": ["Extracted gap"],
                "activation_strategy": {
                    "phase_1": "Extracted immediate actions",
                    "phase_2": "Extracted medium-term actions", 
                    "phase_3": "Extracted long-term actions"
                },
                "success_metrics": ["Extracted metric"]
            }
        }
    
    def _extract_topology_analysis(self, text: str) -> Dict:
        """Extract network topology analysis from text"""
        return {
            "key_connectors": [{
                "contact_name": "Extracted connector",
                "connector_score": 0.8,
                "network_reach": "Extracted reach assessment",
                "influence_areas": ["Extracted area"],
                "strategic_value": "Extracted value",
                "relationship_investment": "Extracted investment approach"
            }],
            "network_clusters": [{
                "cluster_name": "Extracted cluster",
                "key_members": ["Extracted member"],
                "strategic_importance": "Extracted importance",
                "engagement_strategy": "Extracted strategy"
            }],
            "influence_pathways": [{
                "target": "Extracted target",
                "pathway": ["Extracted contact", "Extracted target"],
                "pathway_strength": 0.7,
                "activation_approach": "Extracted approach"
            }]
        }
    
    def _extract_gap_analysis(self, text: str) -> Dict:
        """Extract strategic gap analysis from text"""
        return {
            "critical_network_gaps": [{
                "gap_area": "Extracted gap area",
                "business_impact": "Extracted impact",
                "target_profiles": ["Extracted profile"],
                "acquisition_strategy": "Extracted strategy",
                "priority_level": "medium",
                "timeline": "Extracted timeline"
            }],
            "network_expansion_priorities": [{
                "expansion_area": "Extracted area",
                "strategic_rationale": "Extracted rationale",
                "target_characteristics": "Extracted characteristics",
                "connection_strategy": "Extracted strategy",
                "investment_required": "Extracted investment"
            }]
        }
    
    def _extract_activation_roadmap(self, text: str) -> Dict:
        """Extract activation roadmap from text"""
        return {
            "immediate_priorities": [{
                "action": "Extracted action",
                "contacts_involved": ["Extracted contact"],
                "objective_alignment": "Extracted objective",
                "timeline": "Extracted timeline",
                "success_criteria": "Extracted criteria"
            }],
            "relationship_development_pipeline": [{
                "relationship_stage": "current",
                "contacts": ["Extracted contacts"],
                "development_actions": ["Extracted action"],
                "timeline": "Extracted timeline",
                "investment_level": "medium"
            }],
            "network_expansion_plan": [{
                "expansion_goal": "Extracted goal",
                "target_network": "Extracted network",
                "entry_strategy": "Extracted strategy",
                "key_facilitators": "Extracted facilitators",
                "timeline": "Extracted timeline"
            }]
        }
    
    def _extract_strategic_recommendations(self, text: str) -> Dict:
        """Extract strategic recommendations from text"""
        return {
            "high_impact_opportunities": [{
                "opportunity": "Extracted opportunity",
                "contacts_involved": ["Extracted contact"],
                "business_objective": "Extracted objective",
                "implementation_approach": "Extracted approach",
                "timeline": "Extracted timeline",
                "success_probability": 0.7
            }],
            "relationship_investment_priorities": [{
                "contact_name": "Extracted contact",
                "investment_rationale": "Extracted rationale",
                "investment_approach": "Extracted approach",
                "expected_roi": "Extracted ROI",
                "timeline": "Extracted timeline"
            }],
            "network_optimization_actions": [{
                "optimization": "Extracted optimization",
                "current_limitation": "Extracted limitation",
                "optimization_approach": "Extracted approach",
                "resource_requirements": "Extracted requirements",
                "expected_benefit": "Extracted benefit"
            }]
        } 