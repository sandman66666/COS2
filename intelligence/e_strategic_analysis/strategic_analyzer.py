"""
Strategic Analysis System - Phase 2
Orchestrates Claude 4 Opus agents working on clean, organized summaries with communication intelligence.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass
import re

import anthropic
from intelligence.c_content_processing.content_summarizer import ContentSummary, ContactSummary
from intelligence.b_data_collection.communication_intelligence import CommunicationProfile
from intelligence.b_data_collection.data_organizer import OrganizedContent

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

    async def analyze_strategic_intelligence_from_tree(self, user_id: int, 
                                                     knowledge_tree,
                                                     tree_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Strategic Analysis working directly with Claude knowledge tree
        """
        print("🧠 Starting Phase 2: Strategic Intelligence Analysis from Claude Tree...")
        
        # Run all agents in parallel using tree context
        print("🚀 Running strategic agents in parallel on Claude tree...")
        
        results = await asyncio.gather(
            self._business_development_analysis(tree_context),
            self._competitive_intelligence_analysis(tree_context),
            self._network_analysis(tree_context),
            self._opportunity_matrix_analysis(tree_context),
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
        synthesis = await self._cross_domain_synthesis(agent_insights, tree_context)
        
        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "agent_insights": agent_insights,
            "cross_domain_synthesis": synthesis,
            "total_insights": sum(len(insights) for insights in agent_insights.values()),
            "tree_metadata": {
                "topics_analyzed": len(tree_context.get('all_topics', [])),
                "contacts_analyzed": len(tree_context.get('all_contacts', [])),
                "business_domains": list(tree_context.get('business_domains', {}).keys()),
                "engagement_rate": tree_context.get('engagement_rate', 0)
            }
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

    def _extract_json_from_response(self, response: str) -> List[Dict]:
        """Extract JSON from Claude response, handling markdown formatting"""
        
        # Try direct JSON parsing first
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code blocks
        json_patterns = [
            r'```json\s*(\[.*?\])\s*```',
            r'```\s*(\[.*?\])\s*```',
            r'(\[.*?\])',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue
        
        # If no JSON array found, create a single insight from the text
        print(f"⚠️ Could not parse JSON, creating fallback insight from text")
        return [{
            "title": "Strategic Analysis",
            "description": response[:500] + "..." if len(response) > 500 else response,
            "strategic_value": "Requires further analysis",
            "next_actions": ["Review and refine analysis"],
            "confidence_score": 0.3,
            "time_sensitivity": "medium",
            "business_impact": "To be determined"
        }]

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

        IMPORTANT: Return ONLY a JSON array in this exact format:
        [
          {{
            "title": "Opportunity Title",
            "description": "Detailed description",
            "strategic_value": "Clear value proposition",
            "next_actions": ["Action 1", "Action 2"],
            "confidence_score": 0.8,
            "time_sensitivity": "high",
            "business_impact": "Impact description"
          }}
        ]
        """
        
        try:
            response = await self._call_claude_with_retry(prompt)
            insights_data = self._extract_json_from_response(response)
            
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
            
            print(f"✅ Business Development: {len(insights)} insights generated")
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

        IMPORTANT: Return ONLY a JSON array in this exact format:
        [
          {{
            "title": "Insight Title",
            "description": "Detailed analysis",
            "strategic_value": "Competitive advantage",
            "next_actions": ["Action 1", "Action 2"],
            "confidence_score": 0.7,
            "time_sensitivity": "medium",
            "business_impact": "Market positioning impact"
          }}
        ]
        """
        
        try:
            response = await self._call_claude_with_retry(prompt)
            insights_data = self._extract_json_from_response(response)
            
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
            
            print(f"✅ Competitive Intelligence: {len(insights)} insights generated")
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

        IMPORTANT: Return ONLY a JSON array in this exact format:
        [
          {{
            "title": "Network Strategy",
            "description": "Network optimization approach",
            "strategic_value": "Relationship value",
            "next_actions": ["Action 1", "Action 2"],
            "confidence_score": 0.8,
            "time_sensitivity": "high",
            "business_impact": "Network growth impact"
          }}
        ]
        """
        
        try:
            response = await self._call_claude_with_retry(prompt)
            insights_data = self._extract_json_from_response(response)
            
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
            
            print(f"✅ Network Analysis: {len(insights)} insights generated")
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

        IMPORTANT: Return ONLY a JSON array in this exact format:
        [
          {{
            "title": "Opportunity Title",
            "description": "Strategic opportunity description",
            "strategic_value": "Value proposition",
            "next_actions": ["Action 1", "Action 2"],
            "confidence_score": 0.9,
            "time_sensitivity": "high",
            "business_impact": "Expected business impact"
          }}
        ]
        """
        
        try:
            response = await self._call_claude_with_retry(prompt)
            insights_data = self._extract_json_from_response(response)
            
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
            
            print(f"✅ Opportunity Matrix: {len(insights)} insights generated")
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
            print("⚠️ No insights to synthesize")
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

        IMPORTANT: Return ONLY a JSON array in this exact format:
        [
          {{
            "title": "Cross-Domain Opportunity",
            "description": "Integrated strategic recommendation",
            "strategic_value": "Synergistic value creation",
            "next_actions": ["Action 1", "Action 2"],
            "confidence_score": 0.8,
            "time_sensitivity": "high",
            "business_impact": "Multiplicative impact across domains"
          }}
        ]
        """
        
        try:
            response = await self._call_claude_with_retry(prompt)
            synthesis_data = self._extract_json_from_response(response)
            
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
            
            print(f"✅ Cross-Domain Synthesis: {len(synthesis_insights)} insights generated")
            return synthesis_insights
            
        except Exception as e:
            print(f"❌ Cross-domain synthesis failed: {e}")
            return []

    def _format_contacts_for_analysis(self, contacts: List) -> str:
        """Format contact summaries for agent analysis"""
        if not contacts:
            return "No contacts in this category"
        
        formatted = []
        for contact in contacts:
            # Handle both dict and object formats
            if isinstance(contact, dict):
                email = contact.get('email', 'unknown@unknown.com')
                name = contact.get('name', email.split('@')[0])
                company = contact.get('company', 'Unknown')
                role = contact.get('role', 'contact')
                relationship_status = contact.get('relationship_status', 'unknown')
                topics_involved = contact.get('topics_involved', [])
            else:
                # Original object format
                email = contact.email
                name = contact.name
                company = contact.company
                role = contact.role
                relationship_status = contact.relationship_status
                topics_involved = contact.topics_involved
            
            formatted.append(
                f"• {name or email} ({company or 'Unknown'}) - "
                f"{role} - {relationship_status} - "
                f"Topics: {', '.join(topics_involved[:3])}"
            )
        
        return "\n".join(formatted)

    def _format_topics_for_analysis(self, topics: List) -> str:
        """Format topic summaries for agent analysis"""
        if not topics:
            return "No topics in this category"
        
        formatted = []
        for topic in topics:
            # Handle both dict and object formats
            if isinstance(topic, dict):
                topic_name = topic.get('topic_name', 'Unknown Topic')
                priority_level = topic.get('priority_level', 'medium')
                business_context = topic.get('business_context', 'No context')
                participants = topic.get('participants', [])
                action_items = topic.get('action_items', [])
            else:
                # Original object format
                topic_name = topic.topic_name
                priority_level = topic.priority_level
                business_context = topic.business_context
                participants = topic.participants
                action_items = topic.action_items
            
            formatted.append(
                f"• {topic_name} ({priority_level}) - "
                f"{business_context} - "
                f"Participants: {len(participants)} - "
                f"Actions: {len(action_items)}"
            )
        
        return "\n".join(formatted)

    async def _call_claude_with_retry(self, prompt: str) -> str:
        """Call Claude with infinite retry logic"""
        
        attempt = 0
        while True:
            try:
                attempt += 1
                print(f"🔍 Claude API call attempt {attempt}")
                
                response = await asyncio.to_thread(
                    self.claude_client.messages.create,
                    model="claude-3-5-sonnet-20241022",  # Use correct Claude model name
                    max_tokens=4000,
                    temperature=0.1,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                
                response_text = response.content[0].text
                print(f"✅ Claude response received: {len(response_text)} chars")
                print(f"🔍 Response preview: {response_text[:200]}...")
                
                return response_text
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Claude API error (attempt {attempt}): {error_msg}")
                
                if "overloaded" in error_msg.lower() or "529" in error_msg:
                    # Exponential backoff for server overload
                    wait_time = min(300, (2 ** attempt) + (attempt * 0.5))
                    print(f"⏳ Claude overloaded, retrying in {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    continue
                elif "model" in error_msg.lower() and "not found" in error_msg.lower():
                    print(f"❌ Model error: {error_msg}")
                    print("🔧 Trying fallback model...")
                    # Try different model names
                    fallback_models = [
                        "claude-3-5-sonnet-20241022",
                        "claude-3-sonnet-20240229", 
                        "claude-3-haiku-20240307"
                    ]
                    for model in fallback_models:
                        try:
                            response = await asyncio.to_thread(
                                self.claude_client.messages.create,
                                model=model,
                                max_tokens=4000,
                                temperature=0.1,
                                messages=[{
                                    "role": "user",
                                    "content": prompt
                                }]
                            )
                            response_text = response.content[0].text
                            print(f"✅ Fallback model {model} worked!")
                            return response_text
                        except:
                            continue
                    # If all models fail, raise the original error
                    raise
                else:
                    if attempt < 5:  # Try 5 times for other errors
                        await asyncio.sleep(5)
                        continue
                    else:
                        print(f"❌ Max retries reached. Last error: {error_msg}")
                        raise 