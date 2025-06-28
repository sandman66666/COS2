"""
Strategic Opportunity Scoring System
===================================
Scores and prioritizes opportunities based on multiple strategic factors.
Integrates with the two-phase knowledge tree system to enhance strategic analysis.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json

from utils.logging import structured_logger as logger
from intelligence.a_core.claude_analysis import get_claude_client

class OpportunityType(Enum):
    PARTNERSHIP = "partnership"
    INVESTMENT = "investment"
    SALES = "sales"
    HIRING = "hiring"
    ACQUISITION = "acquisition"
    STRATEGIC_ALLIANCE = "strategic_alliance"
    MARKET_ENTRY = "market_entry"
    PRODUCT_LAUNCH = "product_launch"
    NETWORK_EXPANSION = "network_expansion"

@dataclass
class OpportunitySignal:
    source: str  # "email", "news", "relationship_change", "market_event"
    strength: float  # 0-1
    description: str
    timestamp: datetime
    related_contacts: List[str]
    evidence: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OpportunityScore:
    opportunity_id: str
    type: OpportunityType
    title: str
    score: float  # 0-100
    factors: Dict[str, float]
    reasoning: str
    next_actions: List[str]
    optimal_timing: datetime
    success_probability: float
    resource_requirements: Dict[str, Any]
    related_contacts: List[str]
    signals: List[OpportunitySignal]
    created_at: datetime = field(default_factory=datetime.now)

class OpportunityScorer:
    """Score and prioritize strategic opportunities"""
    
    def __init__(self, claude_api_key: str):
        self.claude_api_key = claude_api_key
        
        # Scoring weights for different factors
        self.factor_weights = {
            'timing_alignment': 0.25,      # Market timing and internal readiness
            'relationship_strength': 0.20, # Quality of relationships involved
            'competitive_advantage': 0.20, # Strategic positioning advantages
            'resource_fit': 0.15,          # Alignment with current resources
            'success_probability': 0.20    # Likelihood of successful outcome
        }
    
    async def extract_opportunities_from_knowledge_tree(self, knowledge_tree: Dict) -> List[OpportunityScore]:
        """Extract and score opportunities from the knowledge tree"""
        opportunities = []
        
        # Extract opportunities from Phase 2 strategic analysis
        phase2_data = knowledge_tree.get('phase2_strategic_analysis', {})
        agent_insights = phase2_data.get('agent_insights', {})
        
        # Business Development opportunities
        bd_insights = agent_insights.get('business_development', [])
        for insight in bd_insights:
            if isinstance(insight, dict) and 'strategic_value' in insight:
                opportunity = await self._convert_insight_to_opportunity(insight, OpportunityType.PARTNERSHIP)
                if opportunity:
                    opportunities.append(opportunity)
        
        # Competitive Intelligence opportunities
        ci_insights = agent_insights.get('competitive_intelligence', [])
        for insight in ci_insights:
            if isinstance(insight, dict) and 'strategic_value' in insight:
                opportunity = await self._convert_insight_to_opportunity(insight, OpportunityType.MARKET_ENTRY)
                if opportunity:
                    opportunities.append(opportunity)
        
        # Network Analysis opportunities
        network_insights = agent_insights.get('network_analysis', [])
        for insight in network_insights:
            if isinstance(insight, dict) and 'strategic_value' in insight:
                opportunity = await self._convert_insight_to_opportunity(insight, OpportunityType.NETWORK_EXPANSION)
                if opportunity:
                    opportunities.append(opportunity)
        
        # Opportunity Matrix insights
        opp_insights = agent_insights.get('opportunity_matrix', [])
        for insight in opp_insights:
            if isinstance(insight, dict) and 'strategic_value' in insight:
                opportunity = await self._convert_insight_to_opportunity(insight, OpportunityType.STRATEGIC_ALLIANCE)
                if opportunity:
                    opportunities.append(opportunity)
        
        # Sort opportunities by score
        opportunities.sort(key=lambda x: x.score, reverse=True)
        
        return opportunities
    
    async def _convert_insight_to_opportunity(self, insight: Dict, opp_type: OpportunityType) -> Optional[OpportunityScore]:
        """Convert a strategic insight into a scored opportunity"""
        try:
            # Extract basic information
            title = insight.get('title', 'Strategic Opportunity')
            description = insight.get('description', '')
            strategic_value = insight.get('strategic_value', '')
            next_actions = insight.get('next_actions', [])
            
            # Create opportunity signals
            signals = [OpportunitySignal(
                source="strategic_analysis",
                strength=insight.get('confidence_score', 0.5),
                description=description,
                timestamp=datetime.now(),
                related_contacts=[],
                evidence={"strategic_value": strategic_value}
            )]
            
            # Calculate factor scores
            factors = {
                'timing_alignment': self._calculate_timing_score(insight),
                'relationship_strength': self._calculate_relationship_score(insight),
                'competitive_advantage': self._calculate_competitive_score(insight),
                'resource_fit': self._calculate_resource_score(insight),
                'success_probability': insight.get('confidence_score', 0.5)
            }
            
            # Calculate weighted total score
            total_score = sum(factors[key] * self.factor_weights[key] for key in factors)
            
            # Generate reasoning using Claude
            reasoning = await self._generate_opportunity_reasoning(insight, factors)
            
            return OpportunityScore(
                opportunity_id=f"opp_{hash(title)}_{datetime.now().timestamp()}",
                type=opp_type,
                title=title,
                score=total_score * 100,  # Convert to 0-100 scale
                factors=factors,
                reasoning=reasoning,
                next_actions=next_actions if isinstance(next_actions, list) else [str(next_actions)],
                optimal_timing=self._calculate_optimal_timing(insight),
                success_probability=factors['success_probability'],
                resource_requirements=self._estimate_resources(insight, opp_type),
                related_contacts=[],
                signals=signals
            )
            
        except Exception as e:
            logger.error(f"Error converting insight to opportunity: {e}")
            return None
    
    def _calculate_timing_score(self, insight: Dict) -> float:
        """Calculate timing alignment score"""
        time_sensitivity = insight.get('time_sensitivity', 'medium')
        timing_scores = {
            'high': 0.9,    # Urgent opportunities score higher
            'medium': 0.7,  # Standard timing
            'low': 0.5      # Long-term opportunities
        }
        return timing_scores.get(time_sensitivity, 0.7)
    
    def _calculate_relationship_score(self, insight: Dict) -> float:
        """Calculate relationship strength score"""
        # Look for relationship indicators in the insight
        agent_name = insight.get('agent_name', '')
        if agent_name == 'network_analysis':
            return 0.8  # Network insights typically involve relationships
        elif agent_name == 'business_development':
            return 0.7  # BD insights often involve partnerships
        else:
            return 0.5  # Default relationship strength
    
    def _calculate_competitive_score(self, insight: Dict) -> float:
        """Calculate competitive advantage score"""
        agent_name = insight.get('agent_name', '')
        if agent_name == 'competitive_intelligence':
            return 0.8  # Competitive insights likely have strategic advantage
        elif 'competitive' in insight.get('strategic_value', '').lower():
            return 0.7  # Strategic value mentions competitive aspects
        else:
            return 0.6  # Default competitive positioning
    
    def _calculate_resource_score(self, insight: Dict) -> float:
        """Calculate resource fit score"""
        business_impact = insight.get('business_impact', '')
        if 'high' in business_impact.lower():
            return 0.8  # High impact suggests good resource fit
        elif 'medium' in business_impact.lower():
            return 0.6  # Medium impact
        else:
            return 0.4  # Lower resource fit
    
    async def _generate_opportunity_reasoning(self, insight: Dict, factors: Dict) -> str:
        """Generate reasoning for opportunity scoring using Claude"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.claude_api_key)
            
            prompt = f"""
            Analyze this strategic opportunity and provide concise reasoning for its score:
            
            OPPORTUNITY DETAILS:
            Title: {insight.get('title', 'Strategic Opportunity')}
            Description: {insight.get('description', '')}
            Strategic Value: {insight.get('strategic_value', '')}
            Business Impact: {insight.get('business_impact', '')}
            
            SCORING FACTORS:
            - Timing Alignment: {factors['timing_alignment']:.2f}
            - Relationship Strength: {factors['relationship_strength']:.2f}
            - Competitive Advantage: {factors['competitive_advantage']:.2f}
            - Resource Fit: {factors['resource_fit']:.2f}
            - Success Probability: {factors['success_probability']:.2f}
            
            Provide a 2-3 sentence explanation of why this opportunity scored as it did, focusing on the key strengths and considerations.
            """
            
            response = await client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Error generating opportunity reasoning: {e}")
            return f"Strategic opportunity based on {insight.get('agent_name', 'analysis')} with {factors['success_probability']:.0%} success probability."
    
    def _calculate_optimal_timing(self, insight: Dict) -> datetime:
        """Calculate optimal timing for pursuing opportunity"""
        time_sensitivity = insight.get('time_sensitivity', 'medium')
        
        if time_sensitivity == 'high':
            return datetime.now() + timedelta(days=7)   # Within a week
        elif time_sensitivity == 'medium':
            return datetime.now() + timedelta(days=30)  # Within a month
        else:
            return datetime.now() + timedelta(days=90)  # Within a quarter
    
    def _estimate_resources(self, insight: Dict, opp_type: OpportunityType) -> Dict[str, Any]:
        """Estimate resource requirements for opportunity"""
        business_impact = insight.get('business_impact', 'medium')
        
        # Base resource estimates by opportunity type
        resource_estimates = {
            OpportunityType.PARTNERSHIP: {'time_weeks': 4, 'effort_level': 'medium'},
            OpportunityType.NETWORK_EXPANSION: {'time_weeks': 2, 'effort_level': 'low'},
            OpportunityType.STRATEGIC_ALLIANCE: {'time_weeks': 8, 'effort_level': 'high'},
            OpportunityType.MARKET_ENTRY: {'time_weeks': 12, 'effort_level': 'high'},
            OpportunityType.INVESTMENT: {'time_weeks': 16, 'effort_level': 'high'}
        }
        
        base_resources = resource_estimates.get(opp_type, {'time_weeks': 6, 'effort_level': 'medium'})
        
        # Adjust based on business impact
        if 'high' in business_impact.lower():
            base_resources['time_weeks'] = int(base_resources['time_weeks'] * 1.5)
            base_resources['effort_level'] = 'high'
        elif 'low' in business_impact.lower():
            base_resources['time_weeks'] = int(base_resources['time_weeks'] * 0.7)
            base_resources['effort_level'] = 'low'
        
        return base_resources
    
    def get_top_opportunities(self, opportunities: List[OpportunityScore], limit: int = 10) -> List[OpportunityScore]:
        """Get top N opportunities by score"""
        return sorted(opportunities, key=lambda x: x.score, reverse=True)[:limit]
    
    def filter_opportunities_by_type(self, opportunities: List[OpportunityScore], 
                                   opp_type: OpportunityType) -> List[OpportunityScore]:
        """Filter opportunities by type"""
        return [opp for opp in opportunities if opp.type == opp_type]
    
    def get_opportunity_summary(self, opportunities: List[OpportunityScore]) -> Dict[str, Any]:
        """Get summary statistics for opportunities"""
        if not opportunities:
            return {'total': 0, 'average_score': 0, 'by_type': {}}
        
        total = len(opportunities)
        average_score = sum(opp.score for opp in opportunities) / total
        
        # Group by type
        by_type = {}
        for opp in opportunities:
            type_name = opp.type.value
            if type_name not in by_type:
                by_type[type_name] = {'count': 0, 'avg_score': 0, 'total_score': 0}
            
            by_type[type_name]['count'] += 1
            by_type[type_name]['total_score'] += opp.score
        
        # Calculate averages
        for type_name in by_type:
            by_type[type_name]['avg_score'] = by_type[type_name]['total_score'] / by_type[type_name]['count']
            del by_type[type_name]['total_score']  # Remove intermediate calculation
        
        return {
            'total': total,
            'average_score': round(average_score, 2),
            'by_type': by_type,
            'top_score': max(opp.score for opp in opportunities),
            'generated_at': datetime.now().isoformat()
        } 