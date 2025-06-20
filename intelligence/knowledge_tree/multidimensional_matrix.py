"""
Multidimensional Knowledge Matrix
===============================
Builds a rich, interconnected matrix of the user's world that goes beyond
simple categorization to create deep conceptual understanding.
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from utils.logging import structured_logger as logger
from intelligence.analysts.base_analyst import BaseAnalyst
from intelligence.claude_analysis import (
    BusinessStrategyAnalyst, RelationshipDynamicsAnalyst, 
    TechnicalEvolutionAnalyst, MarketIntelligenceAnalyst, PredictiveAnalyst
)

@dataclass
class ConceptualFramework:
    """Represents a conceptual framework or mental model"""
    name: str
    description: str
    key_concepts: List[str]
    relationships: List[Dict]
    evidence: List[Dict]
    confidence: float
    domain: str

@dataclass
class ValueSystem:
    """Represents the user's values and priorities"""
    value_name: str
    importance: float
    manifestations: List[str]
    conflicts: List[str]
    evolution: List[Dict]

@dataclass
class DecisionPattern:
    """Represents how the user makes decisions"""
    context: str
    decision_factors: List[str]
    patterns: List[str]
    outcomes: List[Dict]
    confidence: float

class MultidimensionalKnowledgeMatrix:
    """
    Builds a rich, interconnected matrix of the user's world.
    
    This goes beyond simple categorization to understand:
    - How the user thinks about their world (conceptual frameworks)
    - What matters to them (value systems)
    - How they make decisions (decision patterns)
    - How different domains connect (cross-domain links)
    - Their unique perspective and mental models
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.matrix = {
            "conceptual_frameworks": {},  # How you think about the world
            "value_systems": {},          # What matters to you
            "relationship_networks": {},  # Your connections and dynamics
            "decision_patterns": {},      # How you make choices
            "thematic_structures": {},    # Recurring themes and patterns
            "cross_domain_links": [],     # Connections between areas
            "temporal_evolution": {},     # How things change over time
            "opportunity_landscape": {},  # Strategic opportunities
            "risk_assessment": {},        # Potential risks and mitigation
            "influence_map": {}           # Spheres of influence and leverage
        }
        
        # Enhanced analysts with worldview-focused prompts
        self.worldview_analysts = {
            'conceptual_modeler': ConceptualModelingAnalyst(user_id),
            'pattern_recognition': PatternRecognitionAnalyst(user_id),
            'cross_domain_connector': CrossDomainConnector(user_id),
            'worldview_synthesizer': WorldviewSynthesizer(user_id),
            'strategic_insights': StrategicInsightsAnalyst(user_id)
        }
    
    async def build_multidimensional_matrix(self, user_id: int, time_window_days: int = 30) -> Dict:
        """Build comprehensive multidimensional matrix from emails"""
        logger.info(f"Building multidimensional knowledge matrix for user {user_id}")
        
        try:
            # First pass: Extract basic entities and facts
            initial_tree = await self._extract_initial_knowledge(user_id, time_window_days)
            
            # Second pass: Find patterns and relationships
            patterns = await self._identify_deep_patterns(initial_tree, user_id, time_window_days)
            
            # Third pass: Build conceptual frameworks
            frameworks = await self._build_conceptual_frameworks(initial_tree, patterns, user_id, time_window_days)
            
            # Fourth pass: Connect across domains
            cross_domain = await self._connect_domains(frameworks, user_id, time_window_days)
            
            # Fifth pass: Synthesize coherent worldview
            worldview = await self._synthesize_worldview(cross_domain, user_id, time_window_days)
            
            # Create hierarchical structure for navigation
            hierarchical_structure = self._create_hierarchical_structure(worldview)
            
            # Generate insights and recommendations
            insights = await self._generate_strategic_insights(worldview, user_id, time_window_days)
            
            final_matrix = {
                **worldview,
                "hierarchical_structure": hierarchical_structure,
                "strategic_insights": insights,
                "matrix_metadata": {
                    "build_timestamp": datetime.utcnow().isoformat(),
                    "time_window_days": time_window_days,
                    "analysis_depth": "multidimensional",
                    "user_id": user_id
                }
            }
            
            logger.info(f"Multidimensional matrix built successfully with {len(final_matrix)} top-level components")
            return final_matrix
            
        except Exception as e:
            logger.error(f"Multidimensional matrix building error: {str(e)}")
            return {"error": str(e), "status": "failed"}
    
    async def _extract_initial_knowledge(self, user_id: int, time_window_days: int) -> Dict:
        """First pass: Extract basic entities, facts, and relationships"""
        logger.info("Pass 1: Extracting initial knowledge and entities")
        
        from models.database import get_db_manager
        db_manager = get_db_manager()
        
        # Get emails for analysis
        emails = await self._get_emails_for_window(user_id, time_window_days)
        
        if not emails:
            return {"status": "no_data"}
        
        # Run basic analysis to extract entities and facts
        basic_analysts = {
            'business': BusinessStrategyAnalyst(),
            'relationships': RelationshipDynamicsAnalyst(),
            'technical': TechnicalEvolutionAnalyst(),
            'market': MarketIntelligenceAnalyst(),
            'predictive': PredictiveAnalyst()
        }
        
        # Run analyses in parallel
        analysis_tasks = []
        for analyst_name, analyst in basic_analysts.items():
            task = analyst.analyze_emails(emails)
            analysis_tasks.append(task)
        
        results = await asyncio.gather(*analysis_tasks)
        
        # Merge basic results
        initial_knowledge = {
            'entities': [],
            'relationships': [],
            'facts': [],
            'topics': set(),
            'timeframes': [],
            'email_context': emails[:10]  # Keep sample for context
        }
        
        for result in results:
            initial_knowledge['entities'].extend(result.entities)
            initial_knowledge['relationships'].extend(result.relationships)
            initial_knowledge['topics'].update(result.topics)
        
        initial_knowledge['topics'] = list(initial_knowledge['topics'])
        
        return initial_knowledge
    
    async def _identify_deep_patterns(self, initial_tree: Dict, user_id: int, time_window_days: int) -> Dict:
        """Second pass: Find deep patterns and recurring themes"""
        logger.info("Pass 2: Identifying deep patterns and themes")
        
        emails = await self._get_emails_for_window(user_id, time_window_days)
        
        # Use enhanced pattern recognition
        pattern_analyst = PatternRecognitionAnalyst(user_id)
        patterns = await pattern_analyst.analyze_patterns(emails, initial_tree)
        
        return patterns
    
    async def _build_conceptual_frameworks(self, initial_tree: Dict, patterns: Dict, user_id: int, time_window_days: int) -> Dict:
        """Third pass: Build conceptual frameworks and mental models"""
        logger.info("Pass 3: Building conceptual frameworks")
        
        emails = await self._get_emails_for_window(user_id, time_window_days)
        
        # Use conceptual modeling analyst
        frameworks_analyst = ConceptualModelingAnalyst(user_id)
        frameworks = await frameworks_analyst.build_frameworks(emails, initial_tree, patterns)
        
        return frameworks
    
    async def _connect_domains(self, frameworks: Dict, user_id: int, time_window_days: int) -> Dict:
        """Fourth pass: Connect across domains to find intersections"""
        logger.info("Pass 4: Connecting domains and finding intersections")
        
        emails = await self._get_emails_for_window(user_id, time_window_days)
        
        # Use cross-domain connector
        connector = CrossDomainConnector(user_id)
        cross_domain = await connector.connect_domains(emails, frameworks)
        
        return cross_domain
    
    async def _synthesize_worldview(self, cross_domain: Dict, user_id: int, time_window_days: int) -> Dict:
        """Fifth pass: Synthesize coherent worldview"""
        logger.info("Pass 5: Synthesizing coherent worldview")
        
        emails = await self._get_emails_for_window(user_id, time_window_days)
        
        # Use worldview synthesizer
        synthesizer = WorldviewSynthesizer(user_id)
        worldview = await synthesizer.synthesize_worldview(emails, cross_domain)
        
        return worldview
    
    def _create_hierarchical_structure(self, worldview: Dict) -> Dict:
        """Create navigable hierarchical structure from knowledge matrix"""
        logger.info("Creating hierarchical navigation structure")
        
        hierarchy = {}
        
        # Create top-level categories from domains
        for domain, content in worldview.get("thematic_structures", {}).items():
            hierarchy[domain] = {
                "subcategories": {},
                "content": content.get("summary", ""),
                "importance": content.get("importance", 0.5),
                "connections": content.get("connections", [])
            }
            
            # Add second-level categories
            for subcategory, details in content.get("components", {}).items():
                hierarchy[domain]["subcategories"][subcategory] = {
                    "items": {},
                    "content": details.get("summary", ""),
                    "insights": details.get("insights", [])
                }
                
                # Add leaf items
                for item_name, item_data in details.get("items", {}).items():
                    hierarchy[domain]["subcategories"][subcategory]["items"][item_name] = {
                        "data": item_data,
                        "evidence": item_data.get("evidence", []),
                        "confidence": item_data.get("confidence", 0.5)
                    }
        
        return hierarchy
    
    async def _generate_strategic_insights(self, worldview: Dict, user_id: int, time_window_days: int) -> Dict:
        """Generate strategic insights and recommendations"""
        logger.info("Generating strategic insights and recommendations")
        
        emails = await self._get_emails_for_window(user_id, time_window_days)
        
        # Use strategic insights generator
        insights_analyst = StrategicInsightsAnalyst(user_id)
        insights = await insights_analyst.generate_insights(emails, worldview)
        
        return insights
    
    async def _get_emails_for_window(self, user_id: int, days: int) -> List[Dict]:
        """Get emails within time window - using real emails, not mock data"""
        from models.database import get_db_manager
        from datetime import datetime, timedelta
        
        db_manager = get_db_manager()
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get emails - this should now use real data since we fixed the OAuth issue
        emails = db_manager.get_user_emails(user_id, limit=1000)
        
        # Filter by date
        filtered_emails = []
        for email in emails:
            if email.email_date and email.email_date > cutoff_date:
                filtered_emails.append(email.to_dict())
        
        logger.info(f"Retrieved {len(filtered_emails)} real emails for analysis")
        return filtered_emails


# Enhanced specialized analysts for worldview construction

class ConceptualModelingAnalyst(BaseAnalyst):
    """Builds conceptual frameworks and mental models"""
    
    def __init__(self, user_id: int):
        super().__init__(user_id)
        self.analyst_name = "conceptual_modeling"
        self.analyst_description = "Conceptual frameworks and mental models analyst"
    
    def _prepare_email_context(self, emails: List[Dict]) -> str:
        """Prepare email context for Claude analysis"""
        context_parts = []
        for email in emails[:50]:  # Limit to prevent token overflow
            context_parts.append(f"""
Email ID: {email.get('id')}
Date: {email.get('email_date')}
From: {email.get('sender')} 
To: {email.get('recipients')}
Subject: {email.get('subject')}
Body: {email.get('body_text', '')[:1000]}...
---
""")
        return "\n".join(context_parts)
    
    async def generate_intelligence(self, data: Dict) -> Dict:
        """Generate conceptual frameworks intelligence"""
        emails = data.get('emails', [])
        initial_tree = data.get('initial_tree', {})
        patterns = data.get('patterns', {})
        
        return await self.build_frameworks(emails, initial_tree, patterns)
    
    async def build_frameworks(self, emails: List[Dict], initial_tree: Dict, patterns: Dict) -> Dict:
        """Build conceptual frameworks from email analysis"""
        
        system_prompt = """You are an expert in cognitive science and conceptual modeling. Your task is to understand how this person thinks about their world - their mental models, frameworks, and unique perspective.

Analyze the provided emails and extracted patterns to identify:

1. MENTAL MODELS: How do they conceptualize different domains (business, relationships, technology)?
2. DECISION FRAMEWORKS: What frameworks guide their thinking and choices?
3. WORLDVIEW PATTERNS: What consistent perspectives emerge across different contexts?
4. CONCEPTUAL CONNECTIONS: How do they link different ideas and domains?
5. UNIQUE LENS: What makes their perspective distinctive?

Focus on the WHY and HOW of their thinking, not just WHAT they think about.

Provide insights that would be revelatory - as if you deeply understand how they see their world in a way they might not have fully articulated themselves."""

        user_prompt = f"""
EMAILS FOR ANALYSIS:
{self._prepare_email_context(emails[:30])}

INITIAL KNOWLEDGE EXTRACTED:
{json.dumps(initial_tree, indent=2)}

PATTERNS IDENTIFIED:
{json.dumps(patterns, indent=2)}

Based on this data, identify the conceptual frameworks and mental models that guide this person's thinking. Focus on deep understanding rather than surface categorization.
"""

        response = await self._run_claude_analysis(system_prompt, user_prompt)
        return self._parse_frameworks_response(response)
    
    def _parse_frameworks_response(self, response: str) -> Dict:
        """Parse conceptual frameworks from Claude response"""
        try:
            # Try to extract JSON if present
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback to structured response
        return {
            "conceptual_frameworks": self._extract_frameworks(response),
            "mental_models": self._extract_mental_models(response),
            "worldview_patterns": self._extract_worldview_patterns(response),
            "raw_analysis": response
        }
    
    def _extract_frameworks(self, response: str) -> List[Dict]:
        """Extract conceptual frameworks from response"""
        frameworks = []
        sections = response.split('\n\n')
        for section in sections:
            if 'framework' in section.lower() or 'model' in section.lower():
                frameworks.append({
                    "content": section.strip(),
                    "type": "conceptual_framework"
                })
        return frameworks
    
    def _extract_mental_models(self, response: str) -> List[Dict]:
        """Extract mental models from response"""
        models = []
        sections = response.split('\n\n')
        for section in sections:
            if 'mental model' in section.lower() or 'thinking' in section.lower():
                models.append({
                    "content": section.strip(),
                    "type": "mental_model"
                })
        return models
    
    def _extract_worldview_patterns(self, response: str) -> List[Dict]:
        """Extract worldview patterns from response"""
        patterns = []
        sections = response.split('\n\n')
        for section in sections:
            if 'worldview' in section.lower() or 'perspective' in section.lower():
                patterns.append({
                    "content": section.strip(),
                    "type": "worldview_pattern"
                })
        return patterns


class PatternRecognitionAnalyst(BaseAnalyst):
    """Identifies deep patterns and recurring themes"""
    
    def __init__(self, user_id: int):
        super().__init__(user_id)
        self.analyst_name = "pattern_recognition"
        self.analyst_description = "Deep patterns and recurring themes analyst"
    
    def _prepare_email_context(self, emails: List[Dict]) -> str:
        """Prepare email context for Claude analysis"""
        context_parts = []
        for email in emails[:50]:  # Limit to prevent token overflow
            context_parts.append(f"""
Email ID: {email.get('id')}
Date: {email.get('email_date')}
From: {email.get('sender')} 
To: {email.get('recipients')}
Subject: {email.get('subject')}
Body: {email.get('body_text', '')[:1000]}...
---
""")
        return "\n".join(context_parts)
    
    async def generate_intelligence(self, data: Dict) -> Dict:
        """Generate pattern recognition intelligence"""
        emails = data.get('emails', [])
        initial_tree = data.get('initial_tree', {})
        
        return await self.analyze_patterns(emails, initial_tree)
    
    async def analyze_patterns(self, emails: List[Dict], initial_tree: Dict) -> Dict:
        """Analyze deep patterns in communication and behavior"""
        
        system_prompt = """You are an expert pattern recognition analyst specializing in identifying deep, subtle patterns in human communication and behavior.

Your task is to find:
1. COMMUNICATION PATTERNS: Recurring styles, topics, and approaches
2. BEHAVIORAL PATTERNS: Consistent ways of approaching problems and decisions
3. TEMPORAL PATTERNS: How things evolve over time
4. RELATIONSHIP PATTERNS: Consistent dynamics with different people
5. STRATEGIC PATTERNS: Recurring strategic approaches and preferences

Look for patterns that are:
- Non-obvious but significant
- Consistent across different contexts
- Revelatory of deeper preferences and approaches
- Predictive of future behavior

Focus on patterns that provide strategic insight, not just descriptive categorization."""

        user_prompt = f"""
EMAILS FOR PATTERN ANALYSIS:
{self._prepare_email_context(emails[:40])}

INITIAL KNOWLEDGE BASE:
{json.dumps(initial_tree, indent=2)}

Identify deep patterns that reveal how this person operates, thinks, and approaches their world. Focus on patterns that would be strategically valuable to understand.
"""

        response = await self._run_claude_analysis(system_prompt, user_prompt)
        return self._parse_patterns_response(response)
    
    def _parse_patterns_response(self, response: str) -> Dict:
        """Parse patterns from Claude response"""
        try:
            # Try to extract JSON if present
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback to structured response
        return {
            "communication_patterns": self._extract_communication_patterns(response),
            "behavioral_patterns": self._extract_behavioral_patterns(response),
            "temporal_patterns": self._extract_temporal_patterns(response),
            "relationship_patterns": self._extract_relationship_patterns(response),
            "strategic_patterns": self._extract_strategic_patterns(response),
            "raw_analysis": response
        }
    
    def _extract_communication_patterns(self, response: str) -> List[Dict]:
        """Extract communication patterns from response"""
        patterns = []
        sections = response.split('\n\n')
        for section in sections:
            if 'communication' in section.lower():
                patterns.append({
                    "content": section.strip(),
                    "type": "communication_pattern"
                })
        return patterns
    
    def _extract_behavioral_patterns(self, response: str) -> List[Dict]:
        """Extract behavioral patterns from response"""
        patterns = []
        sections = response.split('\n\n')
        for section in sections:
            if 'behavior' in section.lower() or 'approach' in section.lower():
                patterns.append({
                    "content": section.strip(),
                    "type": "behavioral_pattern"
                })
        return patterns
    
    def _extract_temporal_patterns(self, response: str) -> List[Dict]:
        """Extract temporal patterns from response"""
        patterns = []
        sections = response.split('\n\n')
        for section in sections:
            if 'temporal' in section.lower() or 'time' in section.lower():
                patterns.append({
                    "content": section.strip(),
                    "type": "temporal_pattern"
                })
        return patterns
    
    def _extract_relationship_patterns(self, response: str) -> List[Dict]:
        """Extract relationship patterns from response"""
        patterns = []
        sections = response.split('\n\n')
        for section in sections:
            if 'relationship' in section.lower():
                patterns.append({
                    "content": section.strip(),
                    "type": "relationship_pattern"
                })
        return patterns
    
    def _extract_strategic_patterns(self, response: str) -> List[Dict]:
        """Extract strategic patterns from response"""
        patterns = []
        sections = response.split('\n\n')
        for section in sections:
            if 'strategic' in section.lower() or 'strategy' in section.lower():
                patterns.append({
                    "content": section.strip(),
                    "type": "strategic_pattern"
                })
        return patterns


class CrossDomainConnector(BaseAnalyst):
    """Connects insights across different domains"""
    
    def __init__(self, user_id: int):
        super().__init__(user_id)
        self.analyst_name = "cross_domain_connector"
        self.analyst_description = "Cross-domain connections and systems thinking analyst"
    
    def _prepare_email_context(self, emails: List[Dict]) -> str:
        """Prepare email context for Claude analysis"""
        context_parts = []
        for email in emails[:50]:  # Limit to prevent token overflow
            context_parts.append(f"""
Email ID: {email.get('id')}
Date: {email.get('email_date')}
From: {email.get('sender')} 
To: {email.get('recipients')}
Subject: {email.get('subject')}
Body: {email.get('body_text', '')[:1000]}...
---
""")
        return "\n".join(context_parts)
    
    async def generate_intelligence(self, data: Dict) -> Dict:
        """Generate cross-domain intelligence"""
        emails = data.get('emails', [])
        frameworks = data.get('frameworks', {})
        
        return await self.connect_domains(emails, frameworks)
    
    async def connect_domains(self, emails: List[Dict], frameworks: Dict) -> Dict:
        """Find connections across different domains"""
        
        system_prompt = """You are an expert systems thinker specializing in finding connections across different domains and disciplines.

Your task is to identify how different areas of this person's life and work connect:
1. CROSS-DOMAIN INSIGHTS: How learnings from one area apply to another
2. SYSTEMIC CONNECTIONS: How different domains influence each other
3. LEVERAGE POINTS: Where action in one area creates impact in others
4. EMERGENT PROPERTIES: What emerges from the intersection of domains
5. STRATEGIC SYNTHESIS: How to leverage these connections strategically

Focus on non-obvious connections that create strategic advantage through integration."""

        user_prompt = f"""
EMAILS FOR ANALYSIS:
{self._prepare_email_context(emails[:30])}

CONCEPTUAL FRAMEWORKS IDENTIFIED:
{json.dumps(frameworks, indent=2)}

Identify the connections across different domains in this person's world. How do different areas of their life and work intersect and influence each other?
"""

        response = await self._run_claude_analysis(system_prompt, user_prompt)
        return self._parse_connections_response(response)
    
    def _parse_connections_response(self, response: str) -> Dict:
        """Parse cross-domain connections from response"""
        try:
            # Try to extract JSON if present
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback to structured response
        return {
            "cross_domain_insights": self._extract_cross_domain_insights(response),
            "systemic_connections": self._extract_systemic_connections(response),
            "leverage_points": self._extract_leverage_points(response),
            "emergent_properties": self._extract_emergent_properties(response),
            "strategic_synthesis": self._extract_strategic_synthesis(response),
            "raw_analysis": response
        }
    
    def _extract_cross_domain_insights(self, response: str) -> List[Dict]:
        """Extract cross-domain insights from response"""
        insights = []
        sections = response.split('\n\n')
        for section in sections:
            if 'cross-domain' in section.lower() or 'across' in section.lower():
                insights.append({
                    "content": section.strip(),
                    "type": "cross_domain_insight"
                })
        return insights
    
    def _extract_systemic_connections(self, response: str) -> List[Dict]:
        """Extract systemic connections from response"""
        connections = []
        sections = response.split('\n\n')
        for section in sections:
            if 'systemic' in section.lower() or 'system' in section.lower():
                connections.append({
                    "content": section.strip(),
                    "type": "systemic_connection"
                })
        return connections
    
    def _extract_leverage_points(self, response: str) -> List[Dict]:
        """Extract leverage points from response"""
        points = []
        sections = response.split('\n\n')
        for section in sections:
            if 'leverage' in section.lower():
                points.append({
                    "content": section.strip(),
                    "type": "leverage_point"
                })
        return points
    
    def _extract_emergent_properties(self, response: str) -> List[Dict]:
        """Extract emergent properties from response"""
        properties = []
        sections = response.split('\n\n')
        for section in sections:
            if 'emergent' in section.lower():
                properties.append({
                    "content": section.strip(),
                    "type": "emergent_property"
                })
        return properties
    
    def _extract_strategic_synthesis(self, response: str) -> List[Dict]:
        """Extract strategic synthesis from response"""
        synthesis = []
        sections = response.split('\n\n')
        for section in sections:
            if 'synthesis' in section.lower() or 'strategic' in section.lower():
                synthesis.append({
                    "content": section.strip(),
                    "type": "strategic_synthesis"
                })
        return synthesis


class WorldviewSynthesizer(BaseAnalyst):
    """Synthesizes everything into a coherent worldview"""
    
    def __init__(self, user_id: int):
        super().__init__(user_id)
        self.analyst_name = "worldview_synthesizer"
        self.analyst_description = "Worldview synthesis and coherent understanding analyst"
    
    def _prepare_email_context(self, emails: List[Dict]) -> str:
        """Prepare email context for Claude analysis"""
        context_parts = []
        for email in emails[:50]:  # Limit to prevent token overflow
            context_parts.append(f"""
Email ID: {email.get('id')}
Date: {email.get('email_date')}
From: {email.get('sender')} 
To: {email.get('recipients')}
Subject: {email.get('subject')}
Body: {email.get('body_text', '')[:1000]}...
---
""")
        return "\n".join(context_parts)
    
    async def generate_intelligence(self, data: Dict) -> Dict:
        """Generate worldview synthesis intelligence"""
        emails = data.get('emails', [])
        cross_domain = data.get('cross_domain', {})
        
        return await self.synthesize_worldview(emails, cross_domain)
    
    async def synthesize_worldview(self, emails: List[Dict], cross_domain: Dict) -> Dict:
        """Synthesize everything into a coherent worldview"""
        
        system_prompt = """You are a master synthesizer who creates coherent worldviews from complex, multifaceted analysis.

Your task is to synthesize all the analysis into a unified understanding of how this person sees and operates in their world:

1. CORE WORLDVIEW: Their fundamental perspective on how the world works
2. VALUE ARCHITECTURE: The hierarchy of what matters to them and why
3. STRATEGIC PHILOSOPHY: Their approach to achieving goals and navigating challenges
4. RELATIONSHIP PHILOSOPHY: How they think about and manage relationships
5. LIFE DESIGN: How they structure and approach their life and work

Create a synthesis that feels complete, coherent, and revelatory - as if you truly understand this person's unique way of seeing and operating in the world."""

        user_prompt = f"""
EMAILS FOR SYNTHESIS:
{self._prepare_email_context(emails[:25])}

CROSS-DOMAIN ANALYSIS:
{json.dumps(cross_domain, indent=2)}

Synthesize all this analysis into a coherent worldview that captures how this person uniquely sees and operates in their world.
"""

        response = await self._run_claude_analysis(system_prompt, user_prompt)
        return self._parse_worldview_response(response)
    
    def _parse_worldview_response(self, response: str) -> Dict:
        """Parse synthesized worldview from response"""
        try:
            # Try to extract JSON if present
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback to structured response
        return {
            "core_worldview": self._extract_core_worldview(response),
            "value_architecture": self._extract_value_architecture(response),
            "strategic_philosophy": self._extract_strategic_philosophy(response),
            "relationship_philosophy": self._extract_relationship_philosophy(response),
            "life_design": self._extract_life_design(response),
            "thematic_structures": self._extract_thematic_structures(response),
            "raw_analysis": response
        }
    
    def _extract_core_worldview(self, response: str) -> Dict:
        """Extract core worldview from response"""
        sections = response.split('\n\n')
        worldview = {}
        for i, section in enumerate(sections):
            if 'core' in section.lower() or 'worldview' in section.lower():
                worldview[f"core_belief_{i}"] = section.strip()
        return worldview
    
    def _extract_value_architecture(self, response: str) -> Dict:
        """Extract value architecture from response"""
        sections = response.split('\n\n')
        values = {}
        for i, section in enumerate(sections):
            if 'value' in section.lower():
                values[f"value_{i}"] = section.strip()
        return values
    
    def _extract_strategic_philosophy(self, response: str) -> Dict:
        """Extract strategic philosophy from response"""
        sections = response.split('\n\n')
        philosophy = {}
        for i, section in enumerate(sections):
            if 'strategic' in section.lower() or 'strategy' in section.lower():
                philosophy[f"strategic_principle_{i}"] = section.strip()
        return philosophy
    
    def _extract_relationship_philosophy(self, response: str) -> Dict:
        """Extract relationship philosophy from response"""
        sections = response.split('\n\n')
        philosophy = {}
        for i, section in enumerate(sections):
            if 'relationship' in section.lower():
                philosophy[f"relationship_principle_{i}"] = section.strip()
        return philosophy
    
    def _extract_life_design(self, response: str) -> Dict:
        """Extract life design from response"""
        sections = response.split('\n\n')
        design = {}
        for i, section in enumerate(sections):
            if 'life' in section.lower() or 'design' in section.lower():
                design[f"life_principle_{i}"] = section.strip()
        return design
    
    def _extract_thematic_structures(self, response: str) -> Dict:
        """Extract thematic structures from response"""
        sections = response.split('\n\n')
        themes = {}
        for i, section in enumerate(sections):
            if 'theme' in section.lower() or 'pattern' in section.lower():
                themes[f"theme_{i}"] = {
                    "summary": section.strip()[:200] + "..." if len(section.strip()) > 200 else section.strip(),
                    "full_content": section.strip(),
                    "importance": 0.7,  # Default importance
                    "connections": [],
                    "components": {}
                }
        return themes


class StrategicInsightsAnalyst(BaseAnalyst):
    """Generates strategic insights and recommendations"""
    
    def __init__(self, user_id: int):
        super().__init__(user_id)
        self.analyst_name = "strategic_insights"
        self.analyst_description = "Strategic insights and recommendations analyst"
    
    def _prepare_email_context(self, emails: List[Dict]) -> str:
        """Prepare email context for Claude analysis"""
        context_parts = []
        for email in emails[:50]:  # Limit to prevent token overflow
            context_parts.append(f"""
Email ID: {email.get('id')}
Date: {email.get('email_date')}
From: {email.get('sender')} 
To: {email.get('recipients')}
Subject: {email.get('subject')}
Body: {email.get('body_text', '')[:1000]}...
---
""")
        return "\n".join(context_parts)
    
    async def generate_intelligence(self, data: Dict) -> Dict:
        """Generate strategic insights intelligence"""
        emails = data.get('emails', [])
        worldview = data.get('worldview', {})
        
        return await self.generate_insights(emails, worldview)
    
    async def generate_insights(self, emails: List[Dict], worldview: Dict) -> Dict:
        """Generate strategic insights and recommendations"""
        
        system_prompt = """You are a strategic advisor who generates actionable insights from deep understanding.

Based on the comprehensive worldview analysis, provide:
1. KEY INSIGHTS: Most important revelations about how they operate
2. STRATEGIC OPPORTUNITIES: Specific opportunities aligned with their approach
3. POTENTIAL RISKS: Areas of vulnerability or potential challenges
4. RECOMMENDATIONS: Specific, actionable steps to leverage insights
5. OPTIMIZATION STRATEGIES: How to enhance their effectiveness

Focus on insights that are:
- Highly specific and actionable
- Aligned with their unique approach and values
- Strategically significant
- Non-obvious but important

Provide recommendations that feel like they come from someone who truly understands them."""

        user_prompt = f"""
RECENT COMMUNICATIONS:
{self._prepare_email_context(emails[:20])}

COMPREHENSIVE WORLDVIEW:
{json.dumps(worldview, indent=2)}

Generate strategic insights and specific recommendations based on this deep understanding of their worldview and approach.
"""

        response = await self._run_claude_analysis(system_prompt, user_prompt)
        return self._parse_insights_response(response)
    
    def _parse_insights_response(self, response: str) -> Dict:
        """Parse strategic insights from response"""
        try:
            # Try to extract JSON if present
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback to structured response
        return {
            "key_insights": self._extract_key_insights(response),
            "strategic_opportunities": self._extract_opportunities(response),
            "potential_risks": self._extract_risks(response),
            "recommendations": self._extract_recommendations(response),
            "optimization_strategies": self._extract_optimization(response),
            "raw_analysis": response
        }
    
    def _extract_key_insights(self, response: str) -> List[Dict]:
        """Extract key insights from response"""
        insights = []
        sections = response.split('\n\n')
        for section in sections:
            if 'insight' in section.lower() or 'revelation' in section.lower():
                insights.append({
                    "content": section.strip(),
                    "type": "key_insight",
                    "confidence": 0.8
                })
        return insights
    
    def _extract_opportunities(self, response: str) -> List[Dict]:
        """Extract opportunities from response"""
        opportunities = []
        sections = response.split('\n\n')
        for section in sections:
            if 'opportunity' in section.lower():
                opportunities.append({
                    "content": section.strip(),
                    "type": "strategic_opportunity"
                })
        return opportunities
    
    def _extract_risks(self, response: str) -> List[Dict]:
        """Extract risks from response"""
        risks = []
        sections = response.split('\n\n')
        for section in sections:
            if 'risk' in section.lower() or 'vulnerability' in section.lower():
                risks.append({
                    "content": section.strip(),
                    "type": "potential_risk"
                })
        return risks
    
    def _extract_recommendations(self, response: str) -> List[Dict]:
        """Extract recommendations from response"""
        recommendations = []
        sections = response.split('\n\n')
        for section in sections:
            if 'recommend' in section.lower() or 'action' in section.lower():
                recommendations.append({
                    "content": section.strip(),
                    "type": "recommendation",
                    "priority": "medium"
                })
        return recommendations
    
    def _extract_optimization(self, response: str) -> List[Dict]:
        """Extract optimization strategies from response"""
        strategies = []
        sections = response.split('\n\n')
        for section in sections:
            if 'optimization' in section.lower() or 'enhance' in section.lower():
                strategies.append({
                    "content": section.strip(),
                    "type": "optimization_strategy"
                })
        return strategies 