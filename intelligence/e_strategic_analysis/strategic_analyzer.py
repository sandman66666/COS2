"""
Strategic Analysis System - Phase 2
Orchestrates Claude 4 Opus agents working on clean, organized summaries with communication intelligence.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass

import anthropic
from .content_summarizer import ContentSummary, ContactSummary
from .communication_intelligence import CommunicationProfile
from .data_organizer import OrganizedContent

@dataclass
class StrategicInsight:
    agent_name: str
    title: str
    description: str
    strategic_value: str
    next_actions: List[str]
    confidence_score: float
    time_sensitivity: str
    business_impact: str

class StrategicAnalysisSystem:
    def __init__(self, api_key: str):
        self.claude_client = anthropic.Anthropic(api_key=api_key)

    async def analyze_strategic_intelligence(self, user_id: int, 
                                           topic_summaries: Dict[str, ContentSummary],
                                           contact_summaries: Dict[str, ContactSummary],
                                           communication_profiles: Dict[str, CommunicationProfile],
                                           organized_content: OrganizedContent) -> Dict[str, Any]:
        """
        Main orchestration: Run all agents in parallel on organized summaries
        """
        print("🧠 Starting Phase 2: Strategic Intelligence Analysis...")
        
        # Prepare analysis context
        context = self._prepare_analysis_context(
            topic_summaries, contact_summaries, communication_profiles, organized_content
        )
        
        # Run all agents in parallel (single pass each)
        print("🚀 Running strategic agents in parallel...")
        
        results = await asyncio.gather(
            self._business_development_analysis(context),
            self._competitive_intelligence_analysis(context),
            self._network_analysis(context),
            self._opportunity_matrix_analysis(context),
            return_exceptions=False  # Let failures propagate for retry
        )
        
        agent_insights = {
            "business_development": results[0],
            "competitive_intelligence": results[1], 
            "network_analysis": results[2],
            "opportunity_matrix": results[3]
        }
        
        print("✅ All strategic agents completed")
        
        # Synthesize results
        synthesis = await self._cross_domain_synthesis(agent_insights, context)
        
        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "agent_insights": agent_insights,
            "cross_domain_synthesis": synthesis,
            "total_insights": sum(len(insights) for insights in agent_insights.values())
        }

    def _prepare_analysis_context(self, topic_summaries, contact_summaries, 
                                communication_profiles, organized_content) -> Dict[str, Any]:
        """Prepare clean context for strategic agents"""
        
        # Group contacts by relationship status
        established_contacts = [s for s in contact_summaries.values() 
                              if s.relationship_status == "established"]
        attempted_contacts = [s for s in contact_summaries.values() 
                            if s.relationship_status == "attempted"]
        
        # Group topics by priority
        high_priority_topics = [s for s in topic_summaries.values() 
                              if s.priority_level == "high"]
        
        return {
            "established_contacts": established_contacts,
            "attempted_contacts": attempted_contacts,
            "high_priority_topics": high_priority_topics,
            "all_topic_summaries": list(topic_summaries.values()),
            "all_contact_summaries": list(contact_summaries.values()),
            "business_domains": organized_content.business_domains,
            "total_contacts": len(contact_summaries),
            "engagement_rate": self._calculate_engagement_rate(communication_profiles)
        }

    def _calculate_engagement_rate(self, communication_profiles) -> float:
        """Calculate overall engagement rate"""
        if not communication_profiles:
            return 0.0
        
        engaged_count = sum(1 for profile in communication_profiles.values() 
                          if profile.relationship_status.value in ["established", "ongoing"])
        return engaged_count / len(communication_profiles)

    async def _business_development_analysis(self, context: Dict[str, Any]) -> List[StrategicInsight]:
        """Business Development Agent Analysis"""
        
        prompt = f"""
        You are a Business Development strategist analyzing organized relationship and topic data.

        ESTABLISHED RELATIONSHIPS ({len(context['established_contacts'])}):
        {self._format_contacts_for_analysis(context['established_contacts'][:10])}

        ATTEMPTED CONTACTS ({len(context['attempted_contacts'])}):
        {self._format_contacts_for_analysis(context['attempted_contacts'][:10])}

        HIGH PRIORITY TOPICS ({len(context['high_priority_topics'])}):
        {self._format_topics_for_analysis(context['high_priority_topics'][:5])}

        Based on this organized intelligence, identify 3-5 strategic business development opportunities:

        1. Partnership opportunities with established contacts
        2. Re-engagement strategies for attempted contacts  
        3. Market expansion possibilities
        4. Revenue growth opportunities
        5. Strategic alliance potential

        For each opportunity, provide:
        - Title and description
        - Strategic value
        - Specific next actions
        - Confidence score (0-1)
        - Time sensitivity
        - Business impact

        Format as JSON array.
        """
        
        try:
            response = await self._call_claude_with_retry(prompt)
            insights_data = json.loads(response)
            
            insights = []
            for item in insights_data:
                insight = StrategicInsight(
                    agent_name="business_development",
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    strategic_value=item.get("strategic_value", ""),
                    next_actions=item.get("next_actions", []),
                    confidence_score=item.get("confidence_score", 0.5),
                    time_sensitivity=item.get("time_sensitivity", "medium"),
                    business_impact=item.get("business_impact", "")
                )
                insights.append(insight)
            
            return insights
            
        except Exception as e:
            print(f"❌ Business Development analysis failed: {e}")
            return []

    async def _competitive_intelligence_analysis(self, context: Dict[str, Any]) -> List[StrategicInsight]:
        """Competitive Intelligence Agent Analysis"""
        
        prompt = f"""
        You are a Competitive Intelligence analyst working with organized business data.

        BUSINESS DOMAINS: {', '.join(context['business_domains'].keys())}

        ESTABLISHED CONTACTS:
        {self._format_contacts_for_analysis(context['established_contacts'][:10])}

        HIGH PRIORITY TOPICS:
        {self._format_topics_for_analysis(context['high_priority_topics'][:5])}

        Analyze competitive positioning and market intelligence. Identify 3-5 strategic insights:

        1. Competitive advantages in your network
        2. Market positioning opportunities  
        3. Competitive threats or gaps
        4. Industry trend implications
        5. Strategic differentiation opportunities

        Focus on actionable competitive intelligence based on relationship and topic data.

        Format as JSON array with title, description, strategic_value, next_actions, confidence_score, time_sensitivity, business_impact.
        """
        
        try:
            response = await self._call_claude_with_retry(prompt)
            insights_data = json.loads(response)
            
            insights = []
            for item in insights_data:
                insight = StrategicInsight(
                    agent_name="competitive_intelligence",
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    strategic_value=item.get("strategic_value", ""),
                    next_actions=item.get("next_actions", []),
                    confidence_score=item.get("confidence_score", 0.5),
                    time_sensitivity=item.get("time_sensitivity", "medium"),
                    business_impact=item.get("business_impact", "")
                )
                insights.append(insight)
            
            return insights
            
        except Exception as e:
            print(f"❌ Competitive Intelligence analysis failed: {e}")
            return []

    async def _network_analysis(self, context: Dict[str, Any]) -> List[StrategicInsight]:
        """Network Analysis Agent"""
        
        prompt = f"""
        You are a Network Strategist analyzing relationship intelligence.

        RELATIONSHIP STATUS BREAKDOWN:
        - Established: {len(context['established_contacts'])} contacts
        - Attempted: {len(context['attempted_contacts'])} contacts  
        - Engagement Rate: {context['engagement_rate']:.1%}

        ESTABLISHED CONTACTS:
        {self._format_contacts_for_analysis(context['established_contacts'][:10])}

        ATTEMPTED CONTACTS (Re-engagement opportunities):
        {self._format_contacts_for_analysis(context['attempted_contacts'][:10])}

        Analyze network optimization opportunities. Identify 3-5 strategic insights:

        1. High-value relationship development opportunities
        2. Network expansion strategies
        3. Introduction pathway optimization
        4. Relationship maintenance priorities
        5. Influence network mapping

        Focus on maximizing network value and relationship ROI.

        Format as JSON array with title, description, strategic_value, next_actions, confidence_score, time_sensitivity, business_impact.
        """
        
        try:
            response = await self._call_claude_with_retry(prompt)
            insights_data = json.loads(response)
            
            insights = []
            for item in insights_data:
                insight = StrategicInsight(
                    agent_name="network_analysis",
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    strategic_value=item.get("strategic_value", ""),
                    next_actions=item.get("next_actions", []),
                    confidence_score=item.get("confidence_score", 0.5),
                    time_sensitivity=item.get("time_sensitivity", "medium"),
                    business_impact=item.get("business_impact", "")
                )
                insights.append(insight)
            
            return insights
            
        except Exception as e:
            print(f"❌ Network Analysis failed: {e}")
            return []

    async def _opportunity_matrix_analysis(self, context: Dict[str, Any]) -> List[StrategicInsight]:
        """Opportunity Matrix Agent"""
        
        prompt = f"""
        You are an Opportunity Strategist creating a strategic opportunity matrix.

        HIGH PRIORITY TOPICS:
        {self._format_topics_for_analysis(context['high_priority_topics'][:5])}

        ESTABLISHED RELATIONSHIPS:
        {self._format_contacts_for_analysis(context['established_contacts'][:10])}

        BUSINESS CONTEXT:
        - Total Contacts: {context['total_contacts']}
        - Engagement Rate: {context['engagement_rate']:.1%}
        - Business Domains: {', '.join(context['business_domains'].keys())}

        Create strategic opportunity matrix. Identify 3-5 high-impact opportunities:

        1. Cross-topic strategic opportunities
        2. Timing-sensitive market opportunities
        3. Resource optimization opportunities  
        4. Strategic initiative priorities
        5. Investment/partnership timing windows

        Prioritize by impact, feasibility, and timing.

        Format as JSON array with title, description, strategic_value, next_actions, confidence_score, time_sensitivity, business_impact.
        """
        
        try:
            response = await self._call_claude_with_retry(prompt)
            insights_data = json.loads(response)
            
            insights = []
            for item in insights_data:
                insight = StrategicInsight(
                    agent_name="opportunity_matrix",
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    strategic_value=item.get("strategic_value", ""),
                    next_actions=item.get("next_actions", []),
                    confidence_score=item.get("confidence_score", 0.5),
                    time_sensitivity=item.get("time_sensitivity", "medium"),
                    business_impact=item.get("business_impact", "")
                )
                insights.append(insight)
            
            return insights
            
        except Exception as e:
            print(f"❌ Opportunity Matrix analysis failed: {e}")
            return []

    async def _cross_domain_synthesis(self, agent_insights: Dict[str, List[StrategicInsight]], 
                                    context: Dict[str, Any]) -> List[StrategicInsight]:
        """Synthesize insights across all agent domains"""
        
        all_insights = []
        for insights in agent_insights.values():
            all_insights.extend(insights)
        
        if not all_insights:
            return []
        
        insights_summary = "\n".join([
            f"- {insight.agent_name}: {insight.title}"
            for insight in all_insights
        ])
        
        prompt = f"""
        Synthesize these strategic insights from multiple agents into 2-3 high-value cross-domain opportunities:

        AGENT INSIGHTS:
        {insights_summary}

        Identify synergies and create integrated strategic recommendations that:
        1. Combine insights from multiple agents
        2. Create multiplicative value opportunities
        3. Optimize timing and resource allocation
        4. Maximize strategic impact

        Format as JSON array with title, description, strategic_value, next_actions, confidence_score, time_sensitivity, business_impact.
        """
        
        try:
            response = await self._call_claude_with_retry(prompt)
            synthesis_data = json.loads(response)
            
            synthesis_insights = []
            for item in synthesis_data:
                insight = StrategicInsight(
                    agent_name="cross_domain_synthesis",
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    strategic_value=item.get("strategic_value", ""),
                    next_actions=item.get("next_actions", []),
                    confidence_score=item.get("confidence_score", 0.5),
                    time_sensitivity=item.get("time_sensitivity", "medium"),
                    business_impact=item.get("business_impact", "")
                )
                synthesis_insights.append(insight)
            
            return synthesis_insights
            
        except Exception as e:
            print(f"❌ Cross-domain synthesis failed: {e}")
            return []

    def _format_contacts_for_analysis(self, contacts: List[ContactSummary]) -> str:
        """Format contact summaries for agent analysis"""
        if not contacts:
            return "No contacts in this category"
        
        formatted = []
        for contact in contacts:
            formatted.append(
                f"• {contact.name or contact.email} ({contact.company or 'Unknown'}) - "
                f"{contact.role} - {contact.relationship_status} - "
                f"Topics: {', '.join(contact.topics_involved[:3])}"
            )
        
        return "\n".join(formatted)

    def _format_topics_for_analysis(self, topics: List[ContentSummary]) -> str:
        """Format topic summaries for agent analysis"""
        if not topics:
            return "No topics in this category"
        
        formatted = []
        for topic in topics:
            formatted.append(
                f"• {topic.topic_name} ({topic.priority_level}) - "
                f"{topic.business_context} - "
                f"Participants: {len(topic.participants)} - "
                f"Actions: {len(topic.action_items)}"
            )
        
        return "\n".join(formatted)

    async def _call_claude_with_retry(self, prompt: str) -> str:
        """Call Claude with infinite retry logic"""
        
        attempt = 0
        while True:
            try:
                attempt += 1
                
                response = self.claude_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    temperature=0.1,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                
                return response.content[0].text
                
            except Exception as e:
                if "overloaded" in str(e).lower() or "529" in str(e):
                    # Exponential backoff for server overload
                    wait_time = min(300, (2 ** attempt) + (attempt * 0.5))
                    print(f"⏳ Claude overloaded, retrying in {wait_time:.1f}s (attempt {attempt})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Claude API error: {e}")
                    if attempt < 5:  # Try 5 times for other errors
                        await asyncio.sleep(5)
                        continue
                    else:
                        raise 