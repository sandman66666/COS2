"""
Unified Intelligence Orchestrator
================================
Combines core knowledge tree analysts with CEO strategic analysts
into one comprehensive intelligence pipeline.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from utils.logging import structured_logger as logger

# Core analysts
from intelligence.a_core.claude_analysis import (
    BusinessStrategyAnalyst, RelationshipDynamicsAnalyst, 
    TechnicalEvolutionAnalyst, MarketIntelligenceAnalyst, PredictiveAnalyst
)

# CEO strategic analysts
from intelligence.e_strategic_analysis.analysts.strategic_relationship_analyst import StrategicRelationshipAnalyst
from intelligence.e_strategic_analysis.analysts.competitive_landscape_analyst import CompetitiveLandscapeAnalyst
from intelligence.e_strategic_analysis.analysts.ceo_decision_intelligence_analyst import CEODecisionIntelligenceAnalyst
from intelligence.e_strategic_analysis.analysts.strategic_network_analyst import StrategicNetworkAnalyst

from storage.storage_manager_sync import get_storage_manager_sync
from storage.enhanced_graph_client import EnhancedGraphClient
from storage.enhanced_vector_client import EnhancedVectorClient

class UnifiedIntelligenceOrchestrator:
    """
    Unified Intelligence Orchestrator
    
    Combines all analyst capabilities into a single, comprehensive
    intelligence pipeline that generates multi-layered strategic insights.
    """
    
    def __init__(self, user_id: int, anthropic_api_key: str):
        """
        Initialize unified intelligence orchestrator
        
        Args:
            user_id: User ID for multi-tenant isolation
            anthropic_api_key: Claude API key
        """
        self.user_id = user_id
        self.anthropic_api_key = anthropic_api_key
        
        # Initialize core analysts (knowledge tree builders)
        self.core_analysts = {
            'business_strategy': BusinessStrategyAnalyst(),
            'relationship_dynamics': RelationshipDynamicsAnalyst(),
            'technical_evolution': TechnicalEvolutionAnalyst(),
            'market_intelligence': MarketIntelligenceAnalyst(),
            'predictive': PredictiveAnalyst()
        }
        
        # Initialize CEO strategic analysts
        self.strategic_analysts = {
            'strategic_relationship': StrategicRelationshipAnalyst(user_id, anthropic_api_key),
            'competitive_landscape': CompetitiveLandscapeAnalyst(user_id, anthropic_api_key),
            'ceo_decision_intelligence': CEODecisionIntelligenceAnalyst(user_id, anthropic_api_key),
            'strategic_network': StrategicNetworkAnalyst(user_id, anthropic_api_key)
        }
        
        # Initialize enhanced storage clients
        self.storage_manager = get_storage_manager_sync()
        self.enhanced_graph_client = EnhancedGraphClient()
        self.enhanced_vector_client = EnhancedVectorClient()
        
        logger.info(
            "Unified Intelligence Orchestrator initialized with enhanced clients",
            user_id=user_id,
            core_analysts=list(self.core_analysts.keys()),
            strategic_analysts=list(self.strategic_analysts.keys())
        )
    
    async def generate_comprehensive_intelligence(self, 
                                                content_window_days: int = 90,
                                                force_rebuild: bool = False) -> Dict:
        """
        Generate comprehensive intelligence combining all analyst capabilities
        
        Args:
            content_window_days: Days of content to analyze
            force_rebuild: Force rebuild of all analysis
            
        Returns:
            Unified intelligence report with all analyst insights
        """
        try:
            logger.info(
                "Starting comprehensive intelligence generation with enhanced storage",
                user_id=self.user_id,
                content_window_days=content_window_days
            )
            
            # Initialize enhanced clients
            await self._init_enhanced_clients()
            
            # Phase 1: Get organized content for analysis
            content_data = await self._get_organized_content(content_window_days)
            
            # Phase 2: Run core knowledge tree analysis
            core_intelligence = await self._run_core_analysis(content_data)
            
            # Phase 3: Run strategic analysis using core intelligence context
            strategic_intelligence = await self._run_strategic_analysis(content_data, core_intelligence)
            
            # Phase 4: Synthesize unified intelligence report
            unified_report = await self._synthesize_unified_intelligence(
                core_intelligence, strategic_intelligence, content_data
            )
            
            # Phase 5: Enhanced storage integration
            await self._store_with_enhanced_clients(unified_report)
            
            logger.info(
                "Comprehensive intelligence generation completed with enhanced storage",
                user_id=self.user_id,
                report_sections=list(unified_report.keys())
            )
            
            return unified_report
            
        except Exception as e:
            logger.error(
                "Error generating comprehensive intelligence",
                error=str(e),
                user_id=self.user_id
            )
            return {"error": f"Intelligence generation failed: {str(e)}"}
    
    async def _init_enhanced_clients(self) -> None:
        """Initialize enhanced Neo4j and ChromaDB clients"""
        try:
            # Connect to enhanced graph client
            await self.enhanced_graph_client.connect()
            
            # Connect to enhanced vector client
            await self.enhanced_vector_client.connect()
            
            logger.info("Enhanced clients initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize enhanced clients: {str(e)}")
            raise
    
    async def _store_with_enhanced_clients(self, unified_report: Dict) -> Dict:
        """Store unified intelligence using enhanced clients"""
        try:
            storage_results = {}
            
            # 1. Store traditional knowledge tree
            traditional_storage = self.storage_manager.store_knowledge_tree(
                self.user_id, 
                unified_report, 
                "unified_intelligence_v1"
            )
            storage_results['traditional_storage'] = traditional_storage
            
            # 2. Build strategic relationship graph in Neo4j
            try:
                graph_results = await self.enhanced_graph_client.build_strategic_relationship_graph(
                    self.user_id, 
                    unified_report
                )
                storage_results['graph_storage'] = graph_results
                logger.info("Strategic relationship graph built successfully")
            except Exception as e:
                logger.error(f"Graph storage failed: {str(e)}")
                storage_results['graph_storage'] = {'error': str(e)}
            
            # 3. Index comprehensive intelligence in ChromaDB
            try:
                vector_results = await self.enhanced_vector_client.index_unified_intelligence(
                    self.user_id, 
                    unified_report
                )
                storage_results['vector_storage'] = vector_results
                logger.info("Unified intelligence indexed successfully")
            except Exception as e:
                logger.error(f"Vector storage failed: {str(e)}")
                storage_results['vector_storage'] = {'error': str(e)}
            
            return storage_results
            
        except Exception as e:
            logger.error(f"Enhanced storage integration failed: {str(e)}")
            return {'error': str(e)}
    
    async def search_strategic_intelligence(
        self, 
        query: str, 
        content_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict:
        """
        Search across all strategic intelligence using enhanced vector search
        
        Args:
            query: Search query
            content_types: Optional filter for content types
            limit: Maximum results
            
        Returns:
            Comprehensive search results across all intelligence
        """
        try:
            # Ensure vector client is connected
            if not self.enhanced_vector_client.client:
                await self.enhanced_vector_client.connect()
            
            # Perform cross-intelligence search
            search_results = await self.enhanced_vector_client.semantic_search_across_intelligence(
                self.user_id, 
                query, 
                content_types, 
                limit
            )
            
            return search_results
            
        except Exception as e:
            logger.error(f"Strategic intelligence search failed: {str(e)}")
            return {'error': str(e), 'query': query}
    
    async def get_strategic_network_analysis(self) -> Dict:
        """Get comprehensive strategic network analysis from graph database"""
        try:
            # Ensure graph client is connected
            if not self.enhanced_graph_client.driver:
                await self.enhanced_graph_client.connect()
            
            # Get strategic network analysis
            network_analysis = await self.enhanced_graph_client.get_strategic_network_analysis(
                self.user_id
            )
            
            return network_analysis
            
        except Exception as e:
            logger.error(f"Strategic network analysis failed: {str(e)}")
            return {'error': str(e)}
    
    async def find_strategic_paths_to_objective(self, objective_id: str, max_depth: int = 3) -> Dict:
        """Find strategic paths to achieve a specific business objective"""
        try:
            # Ensure graph client is connected
            if not self.enhanced_graph_client.driver:
                await self.enhanced_graph_client.connect()
            
            # Find strategic paths
            strategic_paths = await self.enhanced_graph_client.find_strategic_paths(
                self.user_id, 
                objective_id, 
                max_depth
            )
            
            return strategic_paths
            
        except Exception as e:
            logger.error(f"Strategic path finding failed: {str(e)}")
            return {'error': str(e), 'objective_id': objective_id}
    
    async def get_competitive_landscape_graph(self) -> Dict:
        """Get competitive landscape as interactive graph"""
        try:
            # Ensure graph client is connected
            if not self.enhanced_graph_client.driver:
                await self.enhanced_graph_client.connect()
            
            # Get competitive landscape
            competitive_landscape = await self.enhanced_graph_client.get_competitive_landscape_graph(
                self.user_id
            )
            
            return competitive_landscape
            
        except Exception as e:
            logger.error(f"Competitive landscape analysis failed: {str(e)}")
            return {'error': str(e)}
    
    async def cleanup(self) -> None:
        """Clean up enhanced client connections"""
        try:
            if self.enhanced_graph_client:
                await self.enhanced_graph_client.disconnect()
            
            if self.enhanced_vector_client:
                await self.enhanced_vector_client.disconnect()
                
            logger.info("Enhanced clients cleaned up successfully")
        except Exception as e:
            logger.error(f"Enhanced client cleanup failed: {str(e)}")
    
    async def _get_organized_content(self, days: int) -> Dict:
        """Get and organize content for analysis"""
        try:
            # Get emails for time window
            emails = self.storage_manager.get_emails_for_user(self.user_id, limit=2000)
            
            # Filter by time window if specified
            if days:
                from datetime import datetime, timedelta
                cutoff = datetime.utcnow() - timedelta(days=days)
                emails = [e for e in emails if e.get('email_date') and 
                         datetime.fromisoformat(e['email_date'].replace('Z', '+00:00')) > cutoff]
            
            # Get contacts
            contacts, _ = self.storage_manager.get_contacts(self.user_id, limit=500)
            
            # Get existing knowledge tree if available
            existing_tree = self.storage_manager.get_latest_knowledge_tree(self.user_id)
            
            return {
                'emails': emails,
                'contacts': contacts,
                'existing_knowledge_tree': existing_tree,
                'content_window_days': days,
                'total_emails': len(emails),
                'total_contacts': len(contacts)
            }
            
        except Exception as e:
            logger.error(f"Error getting organized content: {str(e)}")
            return {}
    
    async def _run_core_analysis(self, content_data: Dict) -> Dict:
        """Run core knowledge tree analysis"""
        try:
            logger.info("Running core analyst pipeline")
            
            emails = content_data.get('emails', [])
            if not emails:
                logger.warning("No emails found for core analysis")
                return {}
            
            # Run all core analysts in parallel
            analysis_tasks = []
            for analyst_name, analyst in self.core_analysts.items():
                task = asyncio.create_task(
                    self._run_single_core_analyst(analyst, emails, analyst_name)
                )
                analysis_tasks.append((analyst_name, task))
            
            # Collect results
            core_results = {}
            for analyst_name, task in analysis_tasks:
                try:
                    result = await task
                    core_results[analyst_name] = result
                    logger.info(f"Core analyst completed: {analyst_name}")
                except Exception as e:
                    logger.error(f"Core analyst failed: {analyst_name}, error: {str(e)}")
                    core_results[analyst_name] = {"error": str(e)}
            
            # Build knowledge tree from core results
            knowledge_tree = await self._build_knowledge_tree_from_core(core_results, emails)
            
            return {
                'core_analyst_results': core_results,
                'knowledge_tree': knowledge_tree,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in core analysis: {str(e)}")
            return {}
    
    async def _run_single_core_analyst(self, analyst, emails: List[Dict], analyst_name: str) -> Dict:
        """Run a single core analyst"""
        try:
            # Convert emails to format expected by core analysts
            email_batch = []
            for email in emails[:100]:  # Limit for performance
                email_text = f"Subject: {email.get('subject', '')}\n{email.get('body_text', '')}"
                email_batch.append({
                    'id': email.get('id', ''),
                    'text': email_text,
                    'sender': email.get('sender', ''),
                    'date': email.get('email_date', '')
                })
            
            # Run analyst
            return await analyst.analyze_batch_async(email_batch)
            
        except Exception as e:
            logger.error(f"Error running core analyst {analyst_name}: {str(e)}")
            return {"error": str(e)}
    
    async def _run_strategic_analysis(self, content_data: Dict, core_intelligence: Dict) -> Dict:
        """Run strategic analysis using core intelligence as context"""
        try:
            logger.info("Running strategic analyst pipeline")
            
            contacts = content_data.get('contacts', [])
            knowledge_tree = core_intelligence.get('knowledge_tree', {})
            
            # Prepare strategic context
            strategic_context = await self._prepare_strategic_context(
                content_data, core_intelligence
            )
            
            # Run strategic analysts with enhanced context
            strategic_results = {}
            
            # 1. Strategic Network Analysis (foundation for others)
            network_data = {
                "contacts": contacts,
                "business_objectives": strategic_context.get('business_objectives', []),
                "company_context": strategic_context.get('company_context', {}),
                "recent_interactions": content_data.get('emails', [])[-50:],  # Recent 50 emails
                "knowledge_tree_context": knowledge_tree
            }
            strategic_results['network'] = await self.strategic_analysts['strategic_network'].generate_intelligence(network_data)
            
            # 2. Competitive Landscape Analysis
            landscape_data = {
                "company_context": strategic_context.get('company_context', {}),
                "industry_context": strategic_context.get('industry_context', {}),
                "contact_network": contacts,
                "business_objectives": strategic_context.get('business_objectives', []),
                "market_intelligence_insights": core_intelligence.get('core_analyst_results', {}).get('market_intelligence', {})
            }
            strategic_results['landscape'] = await self.strategic_analysts['competitive_landscape'].generate_intelligence(landscape_data)
            
            # 3. Strategic Relationship Analysis for key contacts
            key_contacts = self._identify_key_contacts(contacts, strategic_results.get('network', {}))
            strategic_results['key_relationships'] = {}
            
            for contact in key_contacts[:5]:  # Top 5 strategic contacts
                relationship_data = {
                    "contact": contact,
                    "company_context": strategic_context.get('company_context', {}),
                    "business_objectives": strategic_context.get('business_objectives', []),
                    "emails": await self._get_contact_emails(contact.get('id', ''), content_data.get('emails', []))
                }
                strategic_results['key_relationships'][contact.get('id', '')] = await self.strategic_analysts['strategic_relationship'].generate_intelligence(relationship_data)
            
            # 4. Decision Intelligence for business objectives
            business_objectives = strategic_context.get('business_objectives', [])
            strategic_results['decision_intelligence'] = {}
            
            for objective in business_objectives[:3]:  # Top 3 objectives
                decision_options = await self._generate_decision_options_from_intelligence(
                    objective, core_intelligence, strategic_results
                )
                
                decision_data = {
                    "decision_area": objective.get('title', 'Strategic Decision'),
                    "decision_options": decision_options,
                    "company_context": strategic_context.get('company_context', {}),
                    "business_objectives": [objective],
                    "competitive_landscape": strategic_results.get('landscape', {}),
                    "financial_context": strategic_context.get('financial_context', {})
                }
                strategic_results['decision_intelligence'][objective.get('id', '')] = await self.strategic_analysts['ceo_decision_intelligence'].generate_intelligence(decision_data)
            
            return strategic_results
            
        except Exception as e:
            logger.error(f"Error in strategic analysis: {str(e)}")
            return {}
    
    async def _prepare_strategic_context(self, content_data: Dict, core_intelligence: Dict) -> Dict:
        """Prepare strategic context from content and core intelligence"""
        try:
            # Extract business context from core intelligence
            business_insights = core_intelligence.get('core_analyst_results', {}).get('business_strategy', {})
            
            # Default company context (can be enhanced with real data)
            company_context = {
                "name": "User Company",
                "industry": business_insights.get('industry_focus', 'Technology'),
                "stage": business_insights.get('business_stage', 'Growth Stage'),
                "competitive_position": business_insights.get('competitive_approach', 'Differentiated'),
                "team_size": len(content_data.get('contacts', [])),
                "strategic_focus": business_insights.get('strategic_priorities', [])
            }
            
            # Extract business objectives from core intelligence
            business_objectives = []
            if business_insights.get('strategic_priorities'):
                for i, priority in enumerate(business_insights['strategic_priorities'][:5]):
                    business_objectives.append({
                        "id": f"objective_{i+1}",
                        "title": priority,
                        "description": f"Strategic priority: {priority}",
                        "priority": "high" if i < 2 else "medium"
                    })
            
            # Industry context from market intelligence
            market_insights = core_intelligence.get('core_analyst_results', {}).get('market_intelligence', {})
            industry_context = {
                "market_trends": market_insights.get('market_trends', []),
                "competitive_dynamics": market_insights.get('competitive_landscape', {}),
                "industry_evolution": market_insights.get('future_predictions', [])
            }
            
            # Financial context (placeholder - can be enhanced)
            financial_context = {
                "stage": "growth",
                "funding_status": "funded",
                "financial_priorities": ["growth", "efficiency"]
            }
            
            return {
                "company_context": company_context,
                "business_objectives": business_objectives,
                "industry_context": industry_context,
                "financial_context": financial_context
            }
            
        except Exception as e:
            logger.error(f"Error preparing strategic context: {str(e)}")
            return {}
    
    async def _synthesize_unified_intelligence(self, core_intelligence: Dict, 
                                             strategic_intelligence: Dict, 
                                             content_data: Dict) -> Dict:
        """Synthesize unified intelligence report"""
        try:
            # Create unified intelligence structure
            unified_report = {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "user_id": self.user_id,
                "content_scope": {
                    "emails_analyzed": content_data.get('total_emails', 0),
                    "contacts_analyzed": content_data.get('total_contacts', 0),
                    "time_window_days": content_data.get('content_window_days', 90)
                },
                
                # Core Intelligence (Foundation)
                "foundation_intelligence": {
                    "knowledge_tree": core_intelligence.get('knowledge_tree', {}),
                    "core_analyst_insights": core_intelligence.get('core_analyst_results', {}),
                    "strategic_dna": self._extract_strategic_dna(core_intelligence),
                    "relationship_philosophy": self._extract_relationship_philosophy(core_intelligence),
                    "decision_frameworks": self._extract_decision_frameworks(core_intelligence)
                },
                
                # Strategic Intelligence (Executive Layer)
                "executive_intelligence": {
                    "competitive_position": strategic_intelligence.get('landscape', {}),
                    "strategic_network": strategic_intelligence.get('network', {}),
                    "key_relationships": strategic_intelligence.get('key_relationships', {}),
                    "decision_support": strategic_intelligence.get('decision_intelligence', {}),
                    "strategic_opportunities": self._extract_strategic_opportunities(strategic_intelligence),
                    "executive_priorities": self._extract_executive_priorities(strategic_intelligence)
                },
                
                # Unified Insights (Cross-System Synthesis)
                "unified_insights": {
                    "strategic_synthesis": self._create_strategic_synthesis(core_intelligence, strategic_intelligence),
                    "actionable_intelligence": self._extract_actionable_intelligence(core_intelligence, strategic_intelligence),
                    "competitive_intelligence": self._synthesize_competitive_intelligence(core_intelligence, strategic_intelligence),
                    "relationship_activation": self._create_relationship_activation_plan(core_intelligence, strategic_intelligence),
                    "decision_priorities": self._prioritize_strategic_decisions(core_intelligence, strategic_intelligence)
                },
                
                # Executive Summary
                "executive_summary": self._create_executive_summary(core_intelligence, strategic_intelligence)
            }
            
            return unified_report
            
        except Exception as e:
            logger.error(f"Error synthesizing unified intelligence: {str(e)}")
            return {}
    
    def _extract_strategic_dna(self, core_intelligence: Dict) -> Dict:
        """Extract strategic DNA from core business analysis"""
        business_strategy = core_intelligence.get('core_analyst_results', {}).get('business_strategy', {})
        return {
            "strategic_worldview": business_strategy.get('strategic_worldview', {}),
            "decision_architecture": business_strategy.get('decision_frameworks', {}),
            "competitive_philosophy": business_strategy.get('competitive_approach', {}),
            "value_creation_models": business_strategy.get('value_creation', {})
        }
    
    def _extract_relationship_philosophy(self, core_intelligence: Dict) -> Dict:
        """Extract relationship philosophy from core relationship analysis"""
        relationship_dynamics = core_intelligence.get('core_analyst_results', {}).get('relationship_dynamics', {})
        return {
            "relationship_approach": relationship_dynamics.get('relationship_style', {}),
            "influence_patterns": relationship_dynamics.get('influence_methods', {}),
            "trust_building": relationship_dynamics.get('trust_building', {}),
            "network_philosophy": relationship_dynamics.get('network_approach', {})
        }
    
    # Additional helper methods for synthesis...
    def _identify_key_contacts(self, contacts: List[Dict], network_analysis: Dict) -> List[Dict]:
        """Identify key strategic contacts"""
        # Simple implementation - can be enhanced with network analysis insights
        return sorted(contacts, key=lambda x: x.get('trust_tier_numeric', 0), reverse=True)[:10]
    
    async def _get_contact_emails(self, contact_id: str, all_emails: List[Dict]) -> List[Dict]:
        """Get emails for specific contact"""
        return [email for email in all_emails if contact_id in email.get('sender', '')][:20]
    
    async def _store_unified_intelligence(self, unified_report: Dict) -> bool:
        """Store unified intelligence report"""
        try:
            return self.storage_manager.store_knowledge_tree(
                self.user_id, 
                unified_report, 
                "unified_intelligence_v1"
            )
        except Exception as e:
            logger.error(f"Error storing unified intelligence: {str(e)}")
            return False
    
    # Placeholder methods for synthesis (to be implemented)
    def _build_knowledge_tree_from_core(self, core_results: Dict, emails: List[Dict]) -> Dict:
        """Build knowledge tree from core analyst results"""
        return {"knowledge_tree": "synthesized_from_core_results"}
    
    def _generate_decision_options_from_intelligence(self, objective: Dict, core_intelligence: Dict, strategic_results: Dict) -> List[Dict]:
        """Generate decision options from intelligence"""
        return [{"option": "strategic_option_1"}, {"option": "strategic_option_2"}]
    
    def _extract_strategic_opportunities(self, strategic_intelligence: Dict) -> List[Dict]:
        """Extract strategic opportunities"""
        return []
    
    def _extract_executive_priorities(self, strategic_intelligence: Dict) -> List[Dict]:
        """Extract executive priorities"""
        return []
    
    def _create_strategic_synthesis(self, core_intelligence: Dict, strategic_intelligence: Dict) -> Dict:
        """Create strategic synthesis"""
        return {}
    
    def _extract_actionable_intelligence(self, core_intelligence: Dict, strategic_intelligence: Dict) -> List[Dict]:
        """Extract actionable intelligence"""
        return []
    
    def _synthesize_competitive_intelligence(self, core_intelligence: Dict, strategic_intelligence: Dict) -> Dict:
        """Synthesize competitive intelligence"""
        return {}
    
    def _create_relationship_activation_plan(self, core_intelligence: Dict, strategic_intelligence: Dict) -> Dict:
        """Create relationship activation plan"""
        return {}
    
    def _prioritize_strategic_decisions(self, core_intelligence: Dict, strategic_intelligence: Dict) -> List[Dict]:
        """Prioritize strategic decisions"""
        return []
    
    def _create_executive_summary(self, core_intelligence: Dict, strategic_intelligence: Dict) -> Dict:
        """Create executive summary"""
        return {
            "key_insights": [],
            "strategic_priorities": [],
            "immediate_actions": [],
            "competitive_position": {},
            "recommendation": "unified_intelligence_generated"
        } 