"""
Knowledge Tree Orchestrator - Two-Phase Architecture
====================================================
Phase 1: Claude Content Consolidation & Tree Structure Building (Comprehensive, Intelligent)
Phase 2: Strategic Intelligence Analysis (Expensive, High-Quality, Targeted)
Phase 3: Strategic Opportunity Scoring & Prioritization (Expensive, High-Quality, Targeted)

Implements the complete two-phase architecture as specified in flow.txt
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
from dataclasses import asdict
import anthropic

from intelligence.c_content_processing.claude_content_consolidator import ClaudeContentConsolidator, ContentItem, ContentType
from intelligence.e_strategic_analysis.strategic_analyzer import StrategicAnalysisSystem, StrategicInsight
from intelligence.e_strategic_analysis.opportunity_scorer import OpportunityScorer
from storage.storage_manager import StorageManager

class KnowledgeTreeOrchestrator:
    def __init__(self, claude_api_key: str):
        # Phase 1: Claude Content Consolidation (builds comprehensive tree structure)
        self.claude_consolidator = ClaudeContentConsolidator(claude_api_key)
        
        # Phase 2: Strategic Intelligence Analysis (works on organized tree)
        self.strategic_analyzer = StrategicAnalysisSystem(claude_api_key)
        
        # Phase 3: Strategic Opportunity Scoring (prioritizes opportunities)
        self.opportunity_scorer = OpportunityScorer(claude_api_key)
        
        self.storage_manager = StorageManager()

    async def build_complete_knowledge_tree(self, user_email: str, 
                                          force_rebuild: bool = False,
                                          force_phase1_rebuild: bool = False,
                                          force_phase2_rebuild: bool = False) -> Dict[str, Any]:
        """
        Complete Two-Phase Knowledge Tree Build Process
        ==============================================
        Phase 1: Claude Content Consolidation & Tree Structure Building
        Phase 2: Strategic Intelligence Analysis (5 Strategic Agents)
        """
        print("🚀 Starting Two-Phase Strategic Intelligence Build Process...")
        print("=" * 80)
        
        # Get user from database to get both email and numeric ID
        user = await self.storage_manager.get_user_by_email(user_email)
        if not user:
            raise ValueError(f"User {user_email} not found")
        
        user_id = user['id']  # Numeric ID for storage operations
        
        # Check if we have recent knowledge tree and don't force rebuild
        if not force_rebuild and not force_phase1_rebuild and not force_phase2_rebuild:
            existing_tree = await self._get_existing_tree(user_id)
            if existing_tree and self._is_tree_recent(existing_tree):
                print("✅ Using existing recent knowledge tree")
                return existing_tree

        # =============================================================================
        # PHASE 1: CLAUDE CONTENT CONSOLIDATION & TREE STRUCTURE BUILDING
        # =============================================================================
        print("\n" + "=" * 80)
        print("🧠 PHASE 1: CLAUDE CONTENT CONSOLIDATION & TREE STRUCTURE BUILDING")
        print("=" * 80)
        print("🎯 Focus: Comprehensive topic/branch structure for accurate classification")
        
        phase1_start = datetime.now()
        
        # 1.1. Multi-Source Content Aggregation
        print("\n📬 Step 1.1: Multi-Source Content Aggregation...")
        all_content_items = await self._aggregate_all_content_sources(user_id)
        print(f"📊 Retrieved {len(all_content_items)} items from all sources")
        
        if not all_content_items:
            return self._create_empty_tree_response(user_id, user_email)
        
        # 1.2. Claude Content Consolidation (Smart chunking or all-at-once)
        print(f"\n🧠 Step 1.2: Claude Content Consolidation...")
        print(f"🎯 Building comprehensive tree structure with {len(all_content_items)} content items")
        
        knowledge_tree = await self.claude_consolidator.process_all_content(
            content_items=all_content_items,
            user_email=user_email
        )
        
        print(f"✅ Built comprehensive knowledge tree:")
        print(f"   📁 Topics: {len(knowledge_tree.topics)}")
        print(f"   🤝 Relationships: {len(knowledge_tree.relationships)}")
        print(f"   🏢 Business Domains: {len(knowledge_tree.business_domains)}")
        print(f"   📅 Timeline Events: {len(knowledge_tree.timeline)}")
        
        phase1_duration = (datetime.now() - phase1_start).total_seconds()
        print(f"\n✅ PHASE 1 COMPLETED in {phase1_duration:.2f} seconds")
        
        # =============================================================================
        # PHASE 2: STRATEGIC INTELLIGENCE ANALYSIS (5 Strategic Agents)
        # =============================================================================
        print("\n" + "=" * 80)
        print("🧠 PHASE 2: STRATEGIC INTELLIGENCE ANALYSIS")
        print("=" * 80)
        print("🚀 Running 5 Strategic Agents with Claude 4 Opus on organized tree...")
        
        phase2_start = datetime.now()
        
        # Convert knowledge tree to format expected by strategic analyzer
        tree_context = self._convert_tree_to_strategic_context(knowledge_tree)
        
        # 2.1. Strategic Analysis with 5 Agents
        strategic_analysis = await self.strategic_analyzer.analyze_strategic_intelligence_from_tree(
            user_id=user_id,
            knowledge_tree=knowledge_tree,
            tree_context=tree_context
        )
        
        phase2_duration = (datetime.now() - phase2_start).total_seconds()
        print(f"\n✅ PHASE 2 COMPLETED in {phase2_duration:.2f} seconds")
        print(f"🎯 Generated {strategic_analysis['total_insights']} strategic insights")
        
        # =============================================================================
        # FINAL SYNTHESIS & STORAGE
        # =============================================================================
        print("\n" + "=" * 80)
        print("🔗 FINAL SYNTHESIS & STORAGE")
        print("=" * 80)
        
        # Combine Phase 1 and Phase 2 results into comprehensive knowledge tree
        comprehensive_tree = self._synthesize_three_phase_results(
            user_id=user_id,
            user_email=user_email,
            knowledge_tree=knowledge_tree,
            strategic_analysis=strategic_analysis,
            opportunities=[],  # Will be populated in Phase 3
            phase1_duration=phase1_duration,
            phase2_duration=phase2_duration,
            phase3_duration=0,  # Will be updated after Phase 3
            total_content_items=len(all_content_items)
        )
        
        # =============================================================================
        # PHASE 3: STRATEGIC OPPORTUNITY SCORING & PRIORITIZATION
        # =============================================================================
        print("\n" + "=" * 80)
        print("🎯 PHASE 3: STRATEGIC OPPORTUNITY SCORING & PRIORITIZATION")
        print("=" * 80)
        print("🔍 Extracting and scoring strategic opportunities...")
        
        phase3_start = datetime.now()
        
        # Extract and score opportunities from strategic analysis using comprehensive tree
        opportunities = await self.opportunity_scorer.extract_opportunities_from_knowledge_tree(comprehensive_tree)
        opportunity_summary = self.opportunity_scorer.get_opportunity_summary(opportunities)
        
        phase3_duration = (datetime.now() - phase3_start).total_seconds()
        print(f"\n✅ PHASE 3 COMPLETED in {phase3_duration:.2f} seconds")
        print(f"🎯 Identified {len(opportunities)} strategic opportunities")
        if opportunities:
            print(f"📊 Top opportunity score: {max(opp.score for opp in opportunities):.1f}/100")
            print(f"📈 Average opportunity score: {opportunity_summary['average_score']:.1f}/100")
        
        # Update comprehensive tree with Phase 3 results
        comprehensive_tree = self._synthesize_three_phase_results(
            user_id=user_id,
            user_email=user_email,
            knowledge_tree=knowledge_tree,
            strategic_analysis=strategic_analysis,
            opportunities=opportunities,
            phase1_duration=phase1_duration,
            phase2_duration=phase2_duration,
            phase3_duration=phase3_duration,
            total_content_items=len(all_content_items)
        )
        
        # Store the complete knowledge tree
        success = await self.storage_manager.store_knowledge_tree(
            user_id=user_id,
            tree_data=comprehensive_tree,
            analysis_type="three_phase_claude_consolidation_v1"
        )
        
        if not success:
            raise Exception("Failed to store knowledge tree")
        
        total_duration = phase1_duration + phase2_duration + phase3_duration
        print(f"\n🎉 THREE-PHASE KNOWLEDGE TREE BUILD COMPLETE!")
        print(f"⏱️  Phase 1 (Claude Consolidation): {phase1_duration:.2f}s")
        print(f"⏱️  Phase 2 (Strategic Analysis): {phase2_duration:.2f}s")
        print(f"⏱️  Phase 3 (Opportunity Scoring): {phase3_duration:.2f}s")
        print(f"⏱️  Total Processing Time: {total_duration:.2f}s")
        print(f"📊 Content Sources Processed: {len(knowledge_tree.content_sources)}")
        print(f"🏷️  Topics/Branches Identified: {len(knowledge_tree.topics)}")
        print(f"🤝 Relationships Mapped: {len(knowledge_tree.relationships)}")
        print(f"🎯 Strategic Insights: {strategic_analysis['total_insights']}")
        print(f"🚀 Strategic Opportunities: {len(opportunities)}")
        
        return {
            'success': True,
            'user_id': user_id,
            'user_email': user_email,
            'knowledge_tree': comprehensive_tree,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'processing_stats': {
                'total_content_processed': len(all_content_items),
                'content_sources': dict(knowledge_tree.content_sources),
                'topics_identified': len(knowledge_tree.topics),
                'relationships_mapped': len(knowledge_tree.relationships),
                'strategic_insights_generated': strategic_analysis['total_insights'],
                'opportunities_identified': len(opportunities),
                'phase1_duration_seconds': phase1_duration,
                'phase2_duration_seconds': phase2_duration,
                'phase3_duration_seconds': phase3_duration,
                'total_duration_seconds': total_duration,
                'architecture': 'three_phase_claude_consolidation_plus_opportunity_scoring'
            },
            'architecture_metadata': {
                'phase1_components': ['claude_content_consolidation', 'comprehensive_tree_building', 'topic_branch_structure'],
                'phase2_components': ['business_development_agent', 'competitive_intelligence_agent', 
                                    'network_analysis_agent', 'opportunity_matrix_agent', 'strategic_synthesizer'],
                'phase3_components': ['opportunity_extraction', 'strategic_scoring', 'priority_ranking'],
                'model_used': 'claude-3-opus-20240229',
                'processing_method': 'claude_consolidation_plus_strategic_analysis_plus_opportunity_scoring',
                'content_types_supported': ['email', 'document', 'slack', 'task', 'meeting', 'note'],
                'chunking_strategy': 'intelligent_batching_or_all_at_once'
            }
        }

    async def _aggregate_all_content_sources(self, user_id: int) -> List[ContentItem]:
        """
        Aggregate ALL available content sources into standardized ContentItem format
        """
        all_content_items = []
        
        # 1. Get Emails
        print("📧 Aggregating emails...")
        try:
            # Use the correct storage manager method
            emails = await self.storage_manager.get_emails_for_user(user_id, limit=2000, time_window_days=365)
            email_items = ClaudeContentConsolidator.from_emails(emails)
            all_content_items.extend(email_items)
            print(f"   ✅ Added {len(email_items)} emails")
        except Exception as e:
            print(f"   ⚠️ Error getting emails: {e}")
        
        # 2. Get Documents (if available)
        print("📄 Aggregating documents...")
        try:
            # This would be implemented when document storage is available
            # documents = self.storage_manager.get_documents(user_id)
            # doc_items = ClaudeContentConsolidator.from_documents(documents)
            # all_content_items.extend(doc_items)
            print(f"   ⚠️ Document integration not yet implemented")
        except Exception as e:
            print(f"   ⚠️ Error getting documents: {e}")
        
        # 3. Get Slack Messages (if available)
        print("💬 Aggregating Slack messages...")
        try:
            # This would be implemented when Slack integration is available
            # slack_messages = self.storage_manager.get_slack_messages(user_id)
            # slack_items = ClaudeContentConsolidator.from_slack_messages(slack_messages)
            # all_content_items.extend(slack_items)
            print(f"   ⚠️ Slack integration not yet implemented")
        except Exception as e:
            print(f"   ⚠️ Error getting Slack messages: {e}")
        
        # 4. Get Tasks/Meetings/Notes (if available)
        print("📝 Aggregating tasks, meetings, notes...")
        try:
            # This would be implemented when these integrations are available
            print(f"   ⚠️ Tasks/meetings/notes integration not yet implemented")
        except Exception as e:
            print(f"   ⚠️ Error getting additional content: {e}")
        
        print(f"📊 Total content items aggregated: {len(all_content_items)}")
        return all_content_items

    def _convert_tree_to_strategic_context(self, knowledge_tree) -> Dict[str, Any]:
        """
        Convert Claude knowledge tree to format expected by strategic analyzer
        """
        # Extract contact information from relationships
        contacts = []
        for email, relationship_data in knowledge_tree.relationships.items():
            contact_info = {
                'email': email,
                'name': relationship_data.get('name', email.split('@')[0]),
                'company': relationship_data.get('company', ''),
                'role': relationship_data.get('role', 'contact'),
                'relationship_status': relationship_data.get('relationship_status', 'unknown'),
                'communication_summary': relationship_data.get('communication_summary', ''),
                'topics_involved': relationship_data.get('topics_involved', []),
                'last_interaction': relationship_data.get('last_interaction', ''),
                'next_action': relationship_data.get('next_action', '')
            }
            contacts.append(contact_info)
        
        # Extract topic information
        topics = []
        for topic_name, topic_data in knowledge_tree.topics.items():
            topic_info = {
                'topic_name': topic_name,
                'key_points': topic_data.get('key_points', []),
                'participants': topic_data.get('participants', []),
                'timeline_summary': topic_data.get('timeline_summary', ''),
                'business_context': topic_data.get('business_context', ''),
                'priority_level': topic_data.get('business_relevance', 'medium'),
                'action_items': topic_data.get('action_items', [])
            }
            topics.append(topic_info)
        
        # Group contacts by relationship status
        established_contacts = [c for c in contacts if c['relationship_status'] in ['established', 'ongoing']]
        attempted_contacts = [c for c in contacts if c['relationship_status'] in ['attempted', 'cold']]
        
        # Group topics by priority
        high_priority_topics = [t for t in topics if t['priority_level'] == 'high']
        
        return {
            'established_contacts': established_contacts,
            'attempted_contacts': attempted_contacts,
            'high_priority_topics': high_priority_topics,
            'all_topics': topics,
            'all_contacts': contacts,
            'business_domains': knowledge_tree.business_domains,
            'total_contacts': len(contacts),
            'engagement_rate': len(established_contacts) / len(contacts) if contacts else 0
        }

    def _convert_strategic_insights_to_dict(self, strategic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert StrategicInsight objects to JSON-serializable dictionaries
        """
        serializable_analysis = {}
        
        for key, value in strategic_analysis.items():
            if key == "agent_insights":
                # Convert agent insights from StrategicInsight objects to dicts
                serializable_insights = {}
                for agent_name, insights in value.items():
                    if isinstance(insights, list):
                        serializable_insights[agent_name] = [
                            asdict(insight) if isinstance(insight, StrategicInsight) else insight 
                            for insight in insights
                        ]
                    else:
                        serializable_insights[agent_name] = insights
                serializable_analysis[key] = serializable_insights
            elif key == "cross_domain_synthesis":
                # Convert synthesis insights from StrategicInsight objects to dicts
                if isinstance(value, list):
                    serializable_analysis[key] = [
                        asdict(insight) if isinstance(insight, StrategicInsight) else insight 
                        for insight in value
                    ]
                else:
                    serializable_analysis[key] = value
            else:
                # Keep other values as-is
                serializable_analysis[key] = value
        
        return serializable_analysis

    def _synthesize_three_phase_results(self, user_id: int, user_email: str, 
                                      knowledge_tree, strategic_analysis: Dict,
                                      opportunities: List,
                                      phase1_duration: float, phase2_duration: float, phase3_duration: float,
                                      total_content_items: int) -> Dict[str, Any]:
        """
        Synthesize Phase 1 (Claude Consolidation), Phase 2 (Strategic Analysis), and Phase 3 (Opportunity Scoring) results
        """
        # Convert StrategicInsight objects to JSON-serializable dictionaries
        serializable_strategic_analysis = self._convert_strategic_insights_to_dict(strategic_analysis)
        
        # Convert opportunities to JSON-serializable format
        serializable_opportunities = [asdict(opp) for opp in opportunities]
        
        return {
            # Tree metadata
            "tree_type": "three_phase_claude_consolidation_v1",
            "user_id": user_id,
            "user_email": user_email,
            "build_timestamp": datetime.now().isoformat(),
            "architecture": "claude_consolidation_plus_strategic_analysis_plus_opportunity_scoring",
            
            # Phase 1 Results: Claude Content Consolidation & Tree Structure
            "phase1_claude_tree": {
                "topics": dict(knowledge_tree.topics),
                "relationships": dict(knowledge_tree.relationships),
                "business_domains": dict(knowledge_tree.business_domains),
                "timeline": knowledge_tree.timeline,
                "content_sources": dict(knowledge_tree.content_sources),
                "tree_metadata": dict(knowledge_tree.metadata)
            },
            
            # Phase 2 Results: Strategic Intelligence Analysis (now JSON serializable)
            "phase2_strategic_analysis": serializable_strategic_analysis,
            
            # Phase 3 Results: Strategic Opportunity Scoring
            "phase3_opportunity_analysis": {
                "opportunities": serializable_opportunities,
                "opportunity_summary": self.opportunity_scorer.get_opportunity_summary(opportunities),
                "top_opportunities": [asdict(opp) for opp in self.opportunity_scorer.get_top_opportunities(opportunities, 5)],
                "generated_at": datetime.now().isoformat()
            },
            
            # Performance metrics
            "processing_performance": {
                "phase1_duration_seconds": phase1_duration,
                "phase2_duration_seconds": phase2_duration,
                "phase3_duration_seconds": phase3_duration,
                "total_duration_seconds": phase1_duration + phase2_duration + phase3_duration,
                "content_processed": total_content_items,
                "content_sources_processed": len(knowledge_tree.content_sources),
                "topics_identified": len(knowledge_tree.topics),
                "relationships_mapped": len(knowledge_tree.relationships),
                "strategic_insights": serializable_strategic_analysis.get('total_insights', 0),
                "opportunities_identified": len(opportunities)
            },
            
            # Legacy compatibility for existing APIs
            "core_facts": dict(knowledge_tree.business_domains),
            "relationships": [{"source": topic, "target": ", ".join(subtopics)} 
                            for topic, subtopics in knowledge_tree.business_domains.items()],
            "timeline": knowledge_tree.timeline,
            "strategic_intelligence": serializable_strategic_analysis.get('agent_insights', {}),
            "cross_domain_synthesis": serializable_strategic_analysis.get('cross_domain_synthesis', []),
            "strategic_opportunities": serializable_opportunities,
            
            # New comprehensive structure
            "comprehensive_knowledge_tree": {
                "topics": dict(knowledge_tree.topics),
                "relationships": dict(knowledge_tree.relationships),
                "business_domains": dict(knowledge_tree.business_domains),
                "timeline": knowledge_tree.timeline,
                "strategic_insights": serializable_strategic_analysis.get('agent_insights', {}),
                "strategic_opportunities": serializable_opportunities,
                "content_sources": dict(knowledge_tree.content_sources)
            }
        }

    async def iterate_knowledge_tree(self, user_email: str) -> Dict[str, Any]:
        """
        Iterate/update existing knowledge tree with Claude consolidation
        """
        print("🔄 Starting Knowledge Tree Iteration with Claude Content Consolidation...")
        
        # With Claude consolidation, we can rebuild efficiently since it handles incrementals
        return await self.build_complete_knowledge_tree(user_email, force_rebuild=True)

    async def _get_existing_tree(self, user_id: int) -> Optional[Dict]:
        """Get existing knowledge tree from storage"""
        try:
            return await self.storage_manager.get_latest_knowledge_tree(user_id)
        except:
            return None

    def _is_tree_recent(self, tree: Dict, max_age_hours: int = 24) -> bool:
        """Check if tree is recent enough to skip rebuild"""
        try:
            created_at = tree.get('created_at')
            if not created_at:
                return False
            
            tree_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            age_hours = (datetime.now() - tree_time).total_seconds() / 3600
            
            return age_hours < max_age_hours
        except:
            return False

    def _create_empty_tree_response(self, user_id: int, user_email: str) -> Dict[str, Any]:
        """Create empty tree response when no content found"""
        return {
            'success': True,
            'user_id': user_id,
            'user_email': user_email,
            'knowledge_tree': {
                'user_email': user_email,
                'created_at': datetime.now().isoformat(),
                'version': "4.0_claude_content_consolidation",
                'analysis_depth': "claude_comprehensive_tree_building",
                'contact_count': 0,
                'content_count': 0,
                'entities': [],
                'topics': {},
                'business_domains': {},
                'insights': [],
                'relationships': {},
                'content_sources': {},
                'architecture': 'claude_consolidation_plus_strategic_analysis'
            },
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'message': 'No content found for analysis'
        }

    def get_knowledge_tree_status(self, user_email: str) -> Dict[str, Any]:
        """Get status of knowledge tree building process"""
        
        try:
            # Get user from database to get numeric ID
            user = asyncio.run(self.storage_manager.get_user_by_email(user_email))
            if not user:
                return {
                    "user_email": user_email,
                    "has_knowledge_tree": False,
                    "error": f"User {user_email} not found",
                    "processing_method": "claude_content_consolidation_plus_strategic_analysis"
                }
            
            user_id = user['id']
            tree = self.storage_manager.get_latest_knowledge_tree(user_id)
            has_tree = tree is not None
            
            status = {
                "user_id": user_id,
                "user_email": user_email,
                "has_knowledge_tree": has_tree,
                "last_updated": None,
                "statistics": {},
                "processing_method": "claude_content_consolidation_plus_strategic_analysis"
            }
            
            if has_tree:
                status["last_updated"] = tree.get("created_at")
                
                # Extract statistics from comprehensive tree structure
                phase1_data = tree.get("phase1_claude_tree", {})
                phase2_data = tree.get("phase2_strategic_analysis", {})
                
                status["statistics"] = {
                    "content_count": tree.get("processing_performance", {}).get("content_processed", 0),
                    "content_sources": len(phase1_data.get("content_sources", {})),
                    "topics_count": len(phase1_data.get("topics", {})),
                    "relationships_count": len(phase1_data.get("relationships", {})),
                    "business_domains": len(phase1_data.get("business_domains", {})),
                    "strategic_insights": phase2_data.get("total_insights", 0),
                    "content_source_breakdown": dict(phase1_data.get("content_sources", {})),
                    "processing_times": {
                        "phase1_seconds": tree.get("processing_performance", {}).get("phase1_duration_seconds", 0),
                        "phase2_seconds": tree.get("processing_performance", {}).get("phase2_duration_seconds", 0),
                        "total_seconds": tree.get("processing_performance", {}).get("total_duration_seconds", 0)
                    }
                }
                
            return status
            
        except Exception as e:
            return {
                "user_email": user_email,
                "has_knowledge_tree": False,
                "error": str(e),
                "processing_method": "claude_content_consolidation_plus_strategic_analysis"
            } 