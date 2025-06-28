"""
Black Belt Intelligence Adapter
===============================
Integration adapter to enhance existing enrichment with black belt techniques
while maintaining backward compatibility.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from intelligence.d_enrichment.black_belt_web_intelligence import (
    BlackBeltWebIntelligence, 
    AdvancedPersonIntelligence
)
from intelligence.d_enrichment.advanced_web_intelligence import CompanyIntelligence
from utils.logging import structured_logger as logger

class BlackBeltEnrichmentAdapter:
    """
    Adapter to enhance existing enrichment with black belt intelligence
    """
    
    def __init__(self, user_id: int, claude_api_key: str = None):
        self.user_id = user_id
        self.claude_api_key = claude_api_key
        self.black_belt_engine = None
        self.success_metrics = {
            'black_belt_enabled': False,
            'advanced_profiles_found': 0,
            'ai_analysis_completed': 0,
            'career_trajectories_analyzed': 0,
            'behavioral_patterns_detected': 0
        }

    async def initialize(self):
        """Initialize the BLACK BELT primary enrichment system"""
        try:
            self.black_belt_engine = BlackBeltWebIntelligence(self.user_id, self.claude_api_key)
            await self.black_belt_engine.initialize()
            self.success_metrics['black_belt_enabled'] = True
            logger.info(f"🥷 BLACK BELT Primary System initialized for user {self.user_id}")
        except Exception as e:
            logger.error(f"BLACK BELT Primary System initialization failed: {e}")
            self.black_belt_engine = None

    async def enhance_contact_enrichment(
        self, 
        email: str, 
        basic_enrichment_result: Any,
        context_emails: List[Dict] = None
    ) -> Dict:
        """
        BLACK BELT PRIMARY: Create comprehensive enrichment from minimal context
        No longer "enhancing" basic enrichment - this IS the enrichment
        """
        if not self.black_belt_engine:
            # Return minimal structured result if black belt is not available
            return self._create_black_belt_minimal_result(email, basic_enrichment_result)
        
        logger.info(f"🥷 BLACK BELT PRIMARY enrichment for {email}")
        
        try:
            # Get comprehensive intelligence (this is now the main pipeline)
            advanced_intelligence = await self.black_belt_engine.get_comprehensive_person_intelligence(
                email, context_emails
            )
            
            # Create comprehensive result from Black Belt intelligence
            enhanced_result = self._create_black_belt_enrichment_result(
                basic_enrichment_result,  # This is now just minimal context
                advanced_intelligence
            )
            
            # Update success metrics
            self._update_success_metrics(advanced_intelligence)
            
            logger.info(f"🥷 BLACK BELT PRIMARY SUCCESS for {email} with confidence {enhanced_result.get('confidence_score', 0):.2f}")
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"🥷 BLACK BELT PRIMARY enrichment failed for {email}: {e}")
            # Return minimal structured result on failure
            return self._create_black_belt_minimal_result(email, basic_enrichment_result)

    def _create_black_belt_minimal_result(self, email: str, context_data: Any) -> Dict:
        """
        Create minimal Black Belt structured result when main enrichment fails
        """
        # Handle context data (could be dict or minimal contact info)
        if isinstance(context_data, dict):
            context = context_data
        else:
            context = {'email': email}
        
        return {
            'email': email,
            'confidence_score': 0.3,
            'data_sources': ['black_belt_minimal'],
            
            # Basic data from context
            'person_data': {
                'name': context.get('name', ''),
                'current_title': '',
                'current_company': '',
                'career_history': [],
                'career_progression': '',
                'years_experience': 0,
                'seniority_level': 'unknown',
                'core_expertise': [],
                'technical_skills': [],
                'industry_experience': [],
                'professional_background': {},
                'current_focus': {},
                'value_proposition': {
                    'engagement_likelihood': 0.4,
                    'best_approach': 'Professional networking with research',
                    'communication_style': 'unknown',
                    'decision_authority': 'Unknown - research needed',
                    'network_value': 'Unknown - requires analysis'
                }
            },
            
            'company_data': {
                'name': '',
                'description': '',
                'industry': '',
                'domain': context.get('domain', ''),
                'technologies': [],
                'social_links': {},
                'funding_info': {},
                'founded_year': None
            },
            
            # Black Belt intelligence modules (empty but structured)
            'social_intelligence': {
                'linkedin_profile': '',
                'github_profile': '',
                'twitter_profile': '',
                'personal_website': '',
                'speaking_engagements': [],
                'publications': []
            },
            'behavioral_intelligence': {
                'content_sharing_patterns': {},
                'network_analysis': {},
                'communication_style': '',
                'engagement_patterns': {
                    'likelihood': 0.4,
                    'best_approach': 'Research-based professional outreach',
                    'optimal_timing': 'Requires further analysis'
                }
            },
            'real_time_intelligence': {
                'recent_activities': [],
                'job_change_indicators': [],
                'industry_involvement': {},
                'last_intelligence_update': datetime.utcnow().isoformat()
            },
            'ai_insights': {
                'personality_profile': {},
                'engagement_strategy': {
                    'likelihood_score': 0.4,
                    'recommended_approach': 'Professional networking with research',
                    'conversation_starters': ['Would value connecting to learn about your work'],
                    'timing_considerations': 'Research optimal timing'
                }
            },
            'relationship_intelligence': {
                'relationship_stage': 'prospect',
                'engagement_level': 'unknown',
                'professional_overlap': [],
                'mutual_connections': [],
                'influence_network': 0
            },
            'actionable_insights': {
                'best_approach': 'Research-driven professional networking',
                'value_propositions': ['Professional networking opportunity', 'Industry insights exchange'],
                'conversation_starters': ['Would love to connect and learn about your professional journey'],
                'meeting_likelihood': 'Medium - requires proper research and approach',
                'timing_considerations': 'Research optimal timing and recent activities',
                'engagement_channels': ['Email - Well-researched professional outreach', 'LinkedIn - Professional networking']
            },
            
            'enrichment_timestamp': datetime.utcnow().isoformat(),
            'enrichment_version': 'black_belt_minimal_v1.0',
            'processing_stats': {
                'profiles_discovered': 0,
                'ai_analysis_performed': False,
                'career_analysis_completed': False,
                'real_time_data_found': False
            }
        }

    def _create_black_belt_enrichment_result(
        self, 
        context_data: Any, 
        advanced_intelligence: AdvancedPersonIntelligence
    ) -> Dict:
        """
        Create comprehensive Black Belt enrichment result from advanced intelligence
        This is now the PRIMARY enrichment method, not an enhancement
        """
        # Convert basic result to dict format
        if hasattr(context_data, 'to_dict'):
            base_data = context_data.to_dict()
        elif hasattr(context_data, '__dict__'):
            base_data = vars(context_data).copy()
        elif isinstance(context_data, dict):
            base_data = context_data.copy()
        else:
            base_data = {}
        
        # Enhanced person data with black belt intelligence
        enhanced_person_data = {
            # Basic data (preserved from existing)
            'name': advanced_intelligence.full_name or base_data.get('person_data', {}).get('name', '') or base_data.get('name', ''),
            'current_title': advanced_intelligence.current_title or base_data.get('person_data', {}).get('current_title', ''),
            'current_company': advanced_intelligence.current_company or base_data.get('company_data', {}).get('name', ''),
            
            # Advanced professional intelligence (BLACK BELT CORE)
            'career_history': advanced_intelligence.career_history,
            'career_progression': advanced_intelligence.career_progression,
            'years_experience': advanced_intelligence.years_experience,
            'seniority_level': advanced_intelligence.seniority_level,
            
            # Expertise and skills (BLACK BELT CORE)
            'core_expertise': advanced_intelligence.core_expertise,
            'technical_skills': advanced_intelligence.technical_skills,
            'industry_experience': advanced_intelligence.industry_experience,
            
            # Professional background analysis (BLACK BELT INTELLIGENCE)
            'professional_background': {
                'years_experience': advanced_intelligence.years_experience,
                'career_progression': advanced_intelligence.career_progression,
                'industry_expertise': advanced_intelligence.industry_experience,
                'technical_competencies': advanced_intelligence.technical_skills
            },
            
            # Current focus and value proposition (BLACK BELT INSIGHTS)
            'current_focus': {
                'primary_expertise': advanced_intelligence.core_expertise[:3] if advanced_intelligence.core_expertise else [],
                'career_stage': advanced_intelligence.seniority_level,
                'industry_involvement': advanced_intelligence.industry_involvement
            },
            
            'value_proposition': {
                'engagement_likelihood': advanced_intelligence.engagement_likelihood,
                'best_approach': advanced_intelligence.best_approach_strategy,
                'communication_style': advanced_intelligence.communication_style,
                'decision_authority': self._determine_decision_authority(advanced_intelligence.seniority_level),
                'network_value': self._assess_network_value(advanced_intelligence)
            }
        }
        
        # Enhanced company data
        enhanced_company_data = base_data.get('company_data', {}).copy()
        if advanced_intelligence.current_company:
            enhanced_company_data['name'] = advanced_intelligence.current_company
        
        # Social and professional presence (BLACK BELT SOCIAL INTELLIGENCE)
        social_intelligence = {
            'linkedin_profile': advanced_intelligence.linkedin_profile,
            'github_profile': advanced_intelligence.github_profile,
            'twitter_profile': advanced_intelligence.twitter_profile,
            'personal_website': advanced_intelligence.personal_website,
            'speaking_engagements': advanced_intelligence.speaking_engagements,
            'publications': advanced_intelligence.publications
        }
        
        # Behavioral intelligence (BLACK BELT BEHAVIORAL ANALYSIS)
        behavioral_intelligence = {
            'content_sharing_patterns': advanced_intelligence.content_sharing_patterns,
            'network_analysis': advanced_intelligence.network_analysis,
            'communication_style': advanced_intelligence.communication_style,
            'engagement_patterns': {
                'likelihood': advanced_intelligence.engagement_likelihood,
                'best_approach': advanced_intelligence.best_approach_strategy,
                'optimal_timing': self._determine_optimal_timing(advanced_intelligence)
            }
        }
        
        # Real-time intelligence (BLACK BELT REAL-TIME MONITORING)
        real_time_intelligence = {
            'recent_activities': advanced_intelligence.recent_activities,
            'job_change_indicators': advanced_intelligence.job_change_indicators,
            'industry_involvement': advanced_intelligence.industry_involvement,
            'last_intelligence_update': advanced_intelligence.last_updated.isoformat()
        }
        
        # AI-powered insights (BLACK BELT AI ANALYSIS)
        ai_insights = {
            'personality_profile': advanced_intelligence.personality_profile,
            'engagement_strategy': {
                'likelihood_score': advanced_intelligence.engagement_likelihood,
                'recommended_approach': advanced_intelligence.best_approach_strategy,
                'conversation_starters': self._generate_conversation_starters(advanced_intelligence),
                'timing_considerations': self._get_timing_considerations(advanced_intelligence)
            }
        }
        
        # Relationship intelligence (BLACK BELT RELATIONSHIP MAPPING)
        relationship_intelligence = {
            'relationship_stage': self._determine_relationship_stage(advanced_intelligence),
            'engagement_level': self._calculate_engagement_level(advanced_intelligence),
            'professional_overlap': self._analyze_professional_overlap(advanced_intelligence),
            'mutual_connections': advanced_intelligence.network_analysis.get('mutual_connections', []),
            'influence_network': advanced_intelligence.network_analysis.get('influence_score', 0)
        }
        
        # Actionable insights (BLACK BELT STRATEGIC RECOMMENDATIONS)
        actionable_insights = {
            'best_approach': advanced_intelligence.best_approach_strategy,
            'value_propositions': self._generate_value_propositions(advanced_intelligence),
            'conversation_starters': self._generate_conversation_starters(advanced_intelligence),
            'meeting_likelihood': self._calculate_meeting_likelihood(advanced_intelligence),
            'timing_considerations': self._get_timing_considerations(advanced_intelligence),
            'engagement_channels': self._recommend_engagement_channels(advanced_intelligence)
        }
        
        # Calculate enhanced confidence score (Black Belt typically has higher confidence)
        black_belt_confidence = advanced_intelligence.confidence_score
        
        # Combine data sources
        combined_sources = list(set(
            base_data.get('data_sources', []) + 
            advanced_intelligence.data_sources
        ))
        
        # Return comprehensive BLACK BELT enrichment result
        return {
            'email': advanced_intelligence.email,
            'confidence_score': black_belt_confidence,
            'data_sources': combined_sources,
            
            # BLACK BELT enhanced core data
            'person_data': enhanced_person_data,
            'company_data': enhanced_company_data,
            
            # BLACK BELT Advanced intelligence modules
            'social_intelligence': social_intelligence,
            'behavioral_intelligence': behavioral_intelligence,
            'real_time_intelligence': real_time_intelligence,
            'ai_insights': ai_insights,
            'relationship_intelligence': relationship_intelligence,
            'actionable_insights': actionable_insights,
            
            # Metadata
            'enrichment_timestamp': datetime.utcnow().isoformat(),
            'enrichment_version': 'black_belt_primary_v1.0',
            'processing_stats': {
                'profiles_discovered': len([p for p in [
                    advanced_intelligence.linkedin_profile,
                    advanced_intelligence.github_profile,
                    advanced_intelligence.twitter_profile
                ] if p]),
                'ai_analysis_performed': bool(advanced_intelligence.personality_profile),
                'career_analysis_completed': bool(advanced_intelligence.career_history),
                'real_time_data_found': bool(advanced_intelligence.recent_activities)
            }
        }

    def _update_success_metrics(self, intelligence: AdvancedPersonIntelligence):
        """Update success metrics based on intelligence gathering"""
        if intelligence.linkedin_profile or intelligence.github_profile or intelligence.twitter_profile:
            self.success_metrics['advanced_profiles_found'] += 1
        
        if intelligence.personality_profile:
            self.success_metrics['ai_analysis_completed'] += 1
        
        if intelligence.career_history:
            self.success_metrics['career_trajectories_analyzed'] += 1
        
        if intelligence.communication_style or intelligence.engagement_likelihood > 0:
            self.success_metrics['behavioral_patterns_detected'] += 1

    def _determine_decision_authority(self, seniority_level: str) -> str:
        """Determine decision-making authority based on seniority"""
        authority_map = {
            'executive': 'High - Strategic decision maker',
            'senior': 'Medium-High - Departmental influence',
            'mid_level': 'Medium - Project-level decisions',
            'junior': 'Low - Individual contributor',
            'unknown': 'Unknown - Requires further analysis'
        }
        return authority_map.get(seniority_level, 'Unknown')

    def _assess_network_value(self, intelligence: AdvancedPersonIntelligence) -> str:
        """Assess the networking value of the contact"""
        score = 0
        
        # Social presence indicates networking activity
        if intelligence.linkedin_profile:
            score += 30
        if intelligence.twitter_profile:
            score += 20
        if intelligence.github_profile:
            score += 10
        
        # Seniority indicates influence
        seniority_scores = {
            'executive': 40,
            'senior': 30,
            'mid_level': 20,
            'junior': 10
        }
        score += seniority_scores.get(intelligence.seniority_level, 0)
        
        # Industry experience indicates expertise
        if intelligence.industry_experience:
            score += len(intelligence.industry_experience) * 5
        
        if score >= 80:
            return 'Very High - Key industry influencer'
        elif score >= 60:
            return 'High - Strong networking potential'
        elif score >= 40:
            return 'Medium - Good professional contact'
        elif score >= 20:
            return 'Low-Medium - Limited networking value'
        else:
            return 'Low - Minimal networking indicators'

    def _determine_optimal_timing(self, intelligence: AdvancedPersonIntelligence) -> str:
        """Determine optimal timing for engagement"""
        if intelligence.recent_activities:
            return 'Immediate - Recent activity detected'
        elif intelligence.job_change_indicators:
            return 'Soon - Potential transition period'
        elif intelligence.seniority_level == 'executive':
            return 'Planned - Schedule in advance'
        else:
            return 'Flexible - No specific timing constraints'

    def _generate_conversation_starters(self, intelligence: AdvancedPersonIntelligence) -> List[str]:
        """Generate contextual conversation starters"""
        starters = []
        
        if intelligence.technical_skills:
            starters.append(f"Interested in your work with {intelligence.technical_skills[0]}")
        
        if intelligence.current_company:
            starters.append(f"Following {intelligence.current_company}'s recent developments")
        
        if intelligence.industry_experience:
            starters.append(f"Would value your insights on {intelligence.industry_experience[0]} trends")
        
        if intelligence.speaking_engagements:
            starters.append("Saw your recent speaking engagement - compelling insights")
        
        if not starters:
            starters.append("Would love to connect and learn about your professional journey")
        
        return starters[:3]  # Top 3 starters

    def _get_timing_considerations(self, intelligence: AdvancedPersonIntelligence) -> str:
        """Get timing considerations for engagement"""
        if intelligence.recent_activities:
            return "High engagement window - recent activity suggests availability"
        elif intelligence.seniority_level == 'executive':
            return "Plan ahead - senior executives prefer scheduled interactions"
        elif intelligence.job_change_indicators:
            return "Transitional period - may be open to new opportunities"
        else:
            return "Standard timing - no special considerations identified"

    def _determine_relationship_stage(self, intelligence: AdvancedPersonIntelligence) -> str:
        """Determine the current relationship stage"""
        # This would be enhanced with email history analysis
        return "prospect"  # Default for new contacts

    def _calculate_engagement_level(self, intelligence: AdvancedPersonIntelligence) -> str:
        """Calculate expected engagement level"""
        if intelligence.engagement_likelihood >= 0.8:
            return "very_high"
        elif intelligence.engagement_likelihood >= 0.6:
            return "high"
        elif intelligence.engagement_likelihood >= 0.4:
            return "medium"
        elif intelligence.engagement_likelihood >= 0.2:
            return "low"
        else:
            return "very_low"

    def _analyze_professional_overlap(self, intelligence: AdvancedPersonIntelligence) -> List[str]:
        """Analyze areas of professional overlap"""
        overlaps = []
        
        # This would be enhanced with user's profile analysis
        if intelligence.technical_skills:
            overlaps.extend(intelligence.technical_skills[:2])
        
        if intelligence.industry_experience:
            overlaps.extend(intelligence.industry_experience[:2])
        
        return overlaps

    def _generate_value_propositions(self, intelligence: AdvancedPersonIntelligence) -> List[str]:
        """Generate value propositions for engagement"""
        propositions = []
        
        if intelligence.seniority_level == 'executive':
            propositions.append("Strategic insights for business growth")
            propositions.append("Executive-level market intelligence")
        
        if intelligence.technical_skills:
            propositions.append("Technical expertise and innovation opportunities")
        
        if intelligence.career_progression == 'rapid':
            propositions.append("Professional development and growth opportunities")
        
        propositions.append("Valuable industry connections and networking")
        
        return propositions[:3]

    def _calculate_meeting_likelihood(self, intelligence: AdvancedPersonIntelligence) -> str:
        """Calculate likelihood of securing a meeting"""
        score = intelligence.engagement_likelihood
        
        if score >= 0.8:
            return "Very High (80%+) - Strong indicators for positive response"
        elif score >= 0.6:
            return "High (60-80%) - Good chance with proper approach"
        elif score >= 0.4:
            return "Medium (40-60%) - Requires strategic positioning"
        elif score >= 0.2:
            return "Low (20-40%) - Challenging but possible"
        else:
            return "Very Low (<20%) - Consider alternative approaches"

    def _recommend_engagement_channels(self, intelligence: AdvancedPersonIntelligence) -> List[str]:
        """Recommend optimal engagement channels"""
        channels = []
        
        if intelligence.linkedin_profile:
            channels.append("LinkedIn - Professional networking")
        
        if intelligence.twitter_profile:
            channels.append("Twitter - Thought leadership engagement")
        
        if intelligence.speaking_engagements:
            channels.append("Industry events - In-person networking")
        
        if intelligence.technical_skills and intelligence.github_profile:
            channels.append("GitHub - Technical collaboration")
        
        channels.append("Email - Direct professional outreach")
        
        return channels[:3]

    async def cleanup(self):
        """Clean up resources"""
        if self.black_belt_engine:
            await self.black_belt_engine.cleanup()
        
        logger.info(f"🥷 BLACK BELT Primary System metrics: {self.success_metrics}")

    def get_success_metrics(self) -> Dict:
        """Get success metrics for the BLACK BELT primary enrichment system"""
        return self.success_metrics.copy() 