# intelligence/behavioral_intelligence_system.py
"""
Automatic Behavioral Intelligence System

Analyzes communication patterns, personality traits, and informal influence networks
for ALL contacts the user communicates with. Uses same filtering as email ingestion.

AUTOMATIC DESIGN:
- No opt-in required - works for all communication partners
- Same filtering criteria as email processing
- Analyzes across all data sources (emails, Slack, future sources)
- Only processes people you actually communicate with
- Professional behavioral insights only
"""

import json
import asyncio
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import re
from collections import defaultdict

from utils.logging import structured_logger as logger

class CommunicationStyle(Enum):
    """Communication style categories"""
    ANALYTICAL = "analytical"          # Data-driven, detailed
    RELATIONSHIP_FOCUSED = "relationship"  # Emojis, personal touch
    RESULTS_ORIENTED = "results"       # Action words, decisive
    COLLABORATIVE = "collaborative"    # Questions, inclusive
    FORMAL = "formal"                  # Professional tone
    CASUAL = "casual"                  # Informal, friendly

class InfluenceLevel(Enum):
    """Informal influence levels"""
    HIGH = "high"           # Major influencer
    MEDIUM = "medium"       # Some influence
    LOW = "low"            # Limited influence
    UNKNOWN = "unknown"     # Not enough data

@dataclass
class BehavioralProfile:
    """Behavioral profile for a contact"""
    contact_email: str
    
    # Communication patterns
    avg_response_time_hours: float = 0.0
    preferred_communication_times: List[int] = field(default_factory=list)  # Hours 0-23
    weekend_activity: bool = False
    emoji_usage_frequency: float = 0.0
    
    # Communication style
    primary_style: CommunicationStyle = CommunicationStyle.UNKNOWN
    style_scores: Dict[str, float] = field(default_factory=dict)
    
    # Language patterns
    avg_message_length: float = 0.0
    question_frequency: float = 0.0  # Questions per message
    exclamation_frequency: float = 0.0
    technical_vocabulary_score: float = 0.0
    
    # Influence indicators
    influence_level: InfluenceLevel = InfluenceLevel.UNKNOWN
    influence_indicators: Dict[str, float] = field(default_factory=dict)
    
    # Relationship mapping
    frequent_collaborators: List[str] = field(default_factory=list)
    cc_frequency: float = 0.0  # How often they're CC'd
    mention_frequency: float = 0.0  # How often they're mentioned
    
    # Engagement patterns
    thread_participation_rate: float = 0.0
    initiative_taking_score: float = 0.0  # How often they start conversations
    
    # Professional insights (NOT personal)
    expertise_keywords: List[str] = field(default_factory=list)
    decision_making_style: str = "unknown"
    stress_indicators: Dict[str, float] = field(default_factory=dict)
    
    # Cross-platform patterns
    data_sources: Set[str] = field(default_factory=set)  # email, slack, etc.
    total_interactions: int = 0
    
    # Metadata
    data_points_analyzed: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    confidence_score: float = 0.0

class BehavioralIntelligenceSystem:
    """
    Automatic behavioral intelligence for all communication partners
    
    SIMPLE PRINCIPLE: If you communicate with them, we learn their patterns
    
    KEY FEATURES:
    1. Automatic behavioral analysis for all contacts
    2. Cross-platform pattern recognition (email + Slack + future sources)
    3. Professional communication intelligence
    4. Response time and availability optimization
    5. Influence network mapping
    
    FILTERING: Uses same criteria as email ingestion - only people you communicate with
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        
        # Behavioral profiles cache
        self.behavioral_profiles: Dict[str, BehavioralProfile] = {}
        
        # Pattern detection configurations
        self.style_keywords = {
            CommunicationStyle.ANALYTICAL: [
                'data', 'analysis', 'metrics', 'statistics', 'numbers',
                'chart', 'graph', 'percentage', 'trend', 'evidence', 'report'
            ],
            CommunicationStyle.RELATIONSHIP_FOCUSED: [
                'team', 'together', 'collaborate', 'support', 'help',
                'thank', 'appreciate', 'great job', 'awesome', 'amazing', 'wonderful'
            ],
            CommunicationStyle.RESULTS_ORIENTED: [
                'deliver', 'execute', 'achieve', 'complete', 'finish',
                'deadline', 'target', 'goal', 'action', 'implement', 'done'
            ],
            CommunicationStyle.COLLABORATIVE: [
                'what do you think', 'thoughts', 'feedback', 'input',
                'suggestions', 'ideas', 'discuss', 'brainstorm', 'opinion'
            ],
            CommunicationStyle.FORMAL: [
                'please', 'kindly', 'sincerely', 'regards', 'formal',
                'professional', 'appropriate', 'protocol', 'procedure'
            ],
            CommunicationStyle.CASUAL: [
                'hey', 'hi there', 'cool', 'awesome', 'lol', 'haha',
                'totally', 'definitely', 'super', 'pretty much'
            ]
        }
    
    async def analyze_message_for_behavioral_insights(self, message_data: Dict, data_source: str = "email") -> Optional[Dict]:
        """
        Analyze any message (email, Slack, etc.) for behavioral insights
        
        Args:
            message_data: Message data from any source
            data_source: Source type (email, slack, etc.)
            
        Returns:
            Behavioral insights or None if no meaningful patterns
        """
        
        # Extract sender/contact email
        contact_email = self._extract_contact_email(message_data, data_source)
        if not contact_email:
            return None
        
        # Skip automated messages
        if self._is_automated_message(message_data):
            return None
        
        # Extract behavioral signals (without storing the message)
        behavioral_signals = await self._extract_behavioral_signals(message_data, data_source)
        
        # Update behavioral profile
        profile = await self._update_behavioral_profile(contact_email, behavioral_signals, data_source)
        
        # Generate insights if we have enough data
        insights = await self._generate_behavioral_insights(profile, behavioral_signals)
        
        return insights if insights else None
    
    def _extract_contact_email(self, message_data: Dict, data_source: str) -> Optional[str]:
        """Extract contact email from message data regardless of source"""
        
        if data_source == "email":
            # Email: sender field
            sender = message_data.get('sender', '') or message_data.get('from', '')
            if '@' in sender:
                # Extract email from "Name <email>" format
                import re
                email_match = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', sender)
                return email_match.group(1).lower() if email_match else None
        
        elif data_source == "slack":
            # Slack: user field, need to map to email
            user_id = message_data.get('user', '')
            user_email = message_data.get('user_email', '')  # From enriched data
            return user_email.lower() if user_email and '@' in user_email else None
        
        # Future sources can be added here
        return None
    
    def _is_automated_message(self, message_data: Dict) -> bool:
        """Check if message is automated (skip behavioral analysis)"""
        
        content = message_data.get('text', '') or message_data.get('body_text', '') or message_data.get('subject', '')
        content_lower = content.lower()
        
        # Skip obvious automated patterns
        automated_indicators = [
            'automated', 'no-reply', 'noreply', 'unsubscribe', 'do not reply',
            'automated response', 'out of office', 'vacation reply',
            'delivery notification', 'read receipt', 'calendar invitation'
        ]
        
        if any(indicator in content_lower for indicator in automated_indicators):
            return True
        
        # Skip very short messages (likely not meaningful for behavioral analysis)
        if len(content.strip()) < 10:
            return True
        
        return False
    
    async def _extract_behavioral_signals(self, message_data: Dict, data_source: str) -> Dict:
        """Extract behavioral signals from any message type"""
        
        content = message_data.get('text', '') or message_data.get('body_text', '') or ''
        timestamp = message_data.get('ts') or message_data.get('created_at', '') or message_data.get('date', '')
        
        signals = {
            'data_source': data_source,
            
            # Message characteristics
            'message_length': len(content),
            'word_count': len(content.split()) if content else 0,
            'has_emoji': bool(re.search(r'[😀-🿿]|:[a-z_]+:', content)),
            'emoji_count': len(re.findall(r'[😀-🿿]|:[a-z_]+:', content)),
            'has_question': '?' in content,
            'question_count': content.count('?'),
            'has_exclamation': '!' in content,
            'exclamation_count': content.count('!'),
            
            # Technical/business vocabulary
            'technical_terms': self._count_technical_terms(content),
            'business_terms': self._count_business_terms(content),
            
            # Communication style indicators
            'style_scores': self._calculate_style_scores(content),
            
            # Timing patterns
            'timestamp': timestamp,
            'hour_of_day': self._extract_hour_from_timestamp(timestamp),
            'is_weekend': self._is_weekend(timestamp),
            
            # Interaction patterns (source-specific)
            'has_mentions': '@' in content,
            'mention_count': content.count('@'),
            'is_thread_reply': bool(message_data.get('thread_ts') or message_data.get('in_reply_to')),
            'is_dm': self._is_direct_message(message_data, data_source),
            
            # Influence indicators
            'cc_recipients': self._count_cc_recipients(message_data, data_source),
            'starts_thread': not bool(message_data.get('thread_ts') or message_data.get('in_reply_to')),
            'message_importance': self._assess_message_importance(content)
        }
        
        return signals
    
    def _is_direct_message(self, message_data: Dict, data_source: str) -> bool:
        """Check if message is a direct message"""
        if data_source == "slack":
            return message_data.get('channel_type') == 'im'
        elif data_source == "email":
            # Email is direct if only one recipient and no CC
            recipients = message_data.get('recipients', []) or message_data.get('to', [])
            cc = message_data.get('cc', [])
            return len(recipients) == 1 and len(cc) == 0
        return False
    
    def _count_cc_recipients(self, message_data: Dict, data_source: str) -> int:
        """Count CC recipients"""
        if data_source == "email":
            cc = message_data.get('cc', [])
            return len(cc) if isinstance(cc, list) else 0
        return 0  # Slack doesn't have CC
    
    def _count_technical_terms(self, content: str) -> int:
        """Count technical vocabulary usage"""
        technical_terms = [
            'api', 'database', 'server', 'cloud', 'integration', 'algorithm',
            'architecture', 'framework', 'deployment', 'scalability',
            'performance', 'security', 'analytics', 'automation', 'infrastructure',
            'docker', 'kubernetes', 'microservices', 'devops', 'cicd'
        ]
        return sum(1 for term in technical_terms if term in content.lower())
    
    def _count_business_terms(self, content: str) -> int:
        """Count business vocabulary usage"""
        business_terms = [
            'revenue', 'profit', 'roi', 'kpi', 'strategy', 'roadmap',
            'customer', 'client', 'market', 'competitive', 'budget',
            'investment', 'partnership', 'acquisition', 'stakeholder',
            'pipeline', 'forecast', 'metrics', 'conversion', 'growth'
        ]
        return sum(1 for term in business_terms if term in content.lower())
    
    def _calculate_style_scores(self, content: str) -> Dict[str, float]:
        """Calculate communication style scores"""
        style_scores = {}
        content_lower = content.lower()
        
        for style, keywords in self.style_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            style_scores[style.value] = score / len(keywords) if keywords else 0.0
        
        return style_scores
    
    def _extract_hour_from_timestamp(self, timestamp: str) -> int:
        """Extract hour of day from timestamp"""
        try:
            if timestamp:
                if '.' in timestamp and timestamp.replace('.', '').isdigit():  # Unix timestamp
                    dt = datetime.fromtimestamp(float(timestamp))
                else:  # ISO format
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.hour
        except:
            pass
        return 12  # Default to midday
    
    def _is_weekend(self, timestamp: str) -> bool:
        """Check if timestamp is on weekend"""
        try:
            if timestamp:
                if '.' in timestamp and timestamp.replace('.', '').isdigit():
                    dt = datetime.fromtimestamp(float(timestamp))
                else:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.weekday() >= 5  # Saturday = 5, Sunday = 6
        except:
            pass
        return False
    
    def _assess_message_importance(self, content: str) -> float:
        """Assess message importance based on content"""
        importance_indicators = [
            'urgent', 'asap', 'critical', 'important', 'deadline',
            'decision', 'approval', 'sign off', 'launch', 'meeting',
            'please review', 'need your input', 'time sensitive'
        ]
        
        score = sum(1 for indicator in importance_indicators 
                   if indicator in content.lower())
        
        return min(1.0, score / 3.0)  # Normalize to 0-1
    
    async def _update_behavioral_profile(self, contact_email: str, signals: Dict, data_source: str) -> BehavioralProfile:
        """Update behavioral profile with new signals from any data source"""
        
        if contact_email not in self.behavioral_profiles:
            self.behavioral_profiles[contact_email] = BehavioralProfile(
                contact_email=contact_email
            )
        
        profile = self.behavioral_profiles[contact_email]
        
        # Track data sources
        profile.data_sources.add(data_source)
        profile.total_interactions += 1
        
        # Update communication patterns (running averages)
        profile.data_points_analyzed += 1
        n = profile.data_points_analyzed
        
        # Update message length average
        profile.avg_message_length = (
            (profile.avg_message_length * (n-1) + signals['message_length']) / n
        )
        
        # Update emoji usage
        emoji_usage = 1.0 if signals['has_emoji'] else 0.0
        profile.emoji_usage_frequency = (
            (profile.emoji_usage_frequency * (n-1) + emoji_usage) / n
        )
        
        # Update question frequency
        question_freq = signals['question_count'] / max(1, signals['word_count'])
        profile.question_frequency = (
            (profile.question_frequency * (n-1) + question_freq) / n
        )
        
        # Update timing patterns
        hour = signals['hour_of_day']
        if hour not in profile.preferred_communication_times:
            profile.preferred_communication_times.append(hour)
        
        if signals['is_weekend']:
            profile.weekend_activity = True
        
        # Update style scores
        for style, score in signals['style_scores'].items():
            if style not in profile.style_scores:
                profile.style_scores[style] = 0.0
            profile.style_scores[style] = (
                (profile.style_scores[style] * (n-1) + score) / n
            )
        
        # Determine primary style
        if profile.style_scores:
            profile.primary_style = CommunicationStyle(
                max(profile.style_scores, key=profile.style_scores.get)
            )
        
        # Update influence indicators
        if signals['starts_thread']:
            profile.influence_indicators['thread_starter'] = (
                profile.influence_indicators.get('thread_starter', 0) + 0.1
            )
        
        if signals['cc_recipients'] > 0:
            profile.influence_indicators['cc_frequency'] = (
                profile.influence_indicators.get('cc_frequency', 0) + 0.1
            )
        
        if signals['message_importance'] > 0.5:
            profile.influence_indicators['importance_sender'] = (
                profile.influence_indicators.get('importance_sender', 0) + 0.1
            )
        
        # Cross-platform influence boost (more data sources = higher confidence)
        if len(profile.data_sources) > 1:
            profile.influence_indicators['multi_platform'] = (
                profile.influence_indicators.get('multi_platform', 0) + 0.2
            )
        
        # Calculate overall influence level
        total_influence = sum(profile.influence_indicators.values())
        if total_influence > 2.5:
            profile.influence_level = InfluenceLevel.HIGH
        elif total_influence > 1.2:
            profile.influence_level = InfluenceLevel.MEDIUM
        elif total_influence > 0.4:
            profile.influence_level = InfluenceLevel.LOW
        
        # Update confidence score (cross-platform data increases confidence)
        platform_bonus = len(profile.data_sources) * 0.2  # Bonus for multiple data sources
        profile.confidence_score = min(1.0, (profile.data_points_analyzed / 30.0) + platform_bonus)
        
        profile.last_updated = datetime.utcnow()
        
        return profile
    
    async def _generate_behavioral_insights(self, profile: BehavioralProfile, signals: Dict) -> Optional[Dict]:
        """Generate actionable behavioral insights"""
        
        if profile.confidence_score < 0.2:  # Need minimum data
            return None
        
        insights = {
            'contact_email': profile.contact_email,
            'behavioral_summary': {
                'communication_style': profile.primary_style.value,
                'influence_level': profile.influence_level.value,
                'confidence': profile.confidence_score,
                'data_sources': list(profile.data_sources),
                'total_interactions': profile.total_interactions
            }
        }
        
        # Communication timing insights
        if profile.preferred_communication_times:
            peak_hours = self._find_peak_communication_hours(profile.preferred_communication_times)
            insights['timing_intelligence'] = {
                'best_contact_hours': peak_hours,
                'weekend_responsive': profile.weekend_activity,
                'avg_response_time': f"{profile.avg_response_time_hours:.1f} hours" if profile.avg_response_time_hours > 0 else "unknown"
            }
        
        # Communication style insights
        if profile.style_scores:
            insights['communication_intelligence'] = {
                'primary_style': profile.primary_style.value,
                'style_breakdown': profile.style_scores,
                'emoji_user': profile.emoji_usage_frequency > 0.3,
                'question_asker': profile.question_frequency > 0.1,
                'message_style': 'detailed' if profile.avg_message_length > 100 else 'concise',
                'cross_platform_consistent': len(profile.data_sources) > 1
            }
        
        # Influence insights
        if profile.influence_level != InfluenceLevel.UNKNOWN:
            insights['influence_intelligence'] = {
                'influence_level': profile.influence_level.value,
                'influence_indicators': profile.influence_indicators,
                'strategic_importance': self._assess_strategic_importance(profile),
                'multi_platform_presence': len(profile.data_sources) > 1
            }
        
        # Professional insights
        insights['professional_intelligence'] = {
            'technical_communicator': signals['technical_terms'] > 2,
            'business_focused': signals['business_terms'] > 1,
            'collaborative_style': profile.question_frequency > 0.15,
            'decision_maker': profile.influence_indicators.get('importance_sender', 0) > 0.5,
            'platform_activity': list(profile.data_sources)
        }
        
        return insights
    
    def _find_peak_communication_hours(self, hours: List[int]) -> List[int]:
        """Find peak communication hours"""
        hour_counts = defaultdict(int)
        for hour in hours:
            hour_counts[hour] += 1
        
        # Return top 3 most common hours
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:3]]
    
    def _assess_strategic_importance(self, profile: BehavioralProfile) -> str:
        """Assess strategic importance of contact"""
        
        influence_score = sum(profile.influence_indicators.values())
        
        # Multi-platform contacts get importance boost
        platform_boost = len(profile.data_sources) * 0.5
        total_score = influence_score + platform_boost
        
        if total_score > 3.0 and profile.primary_style in [
            CommunicationStyle.ANALYTICAL, CommunicationStyle.RESULTS_ORIENTED
        ]:
            return "high_strategic_value"
        elif total_score > 1.5:
            return "medium_strategic_value"
        else:
            return "standard_contact"
    
    async def get_behavioral_profile(self, contact_email: str) -> Optional[BehavioralProfile]:
        """Get behavioral profile for a contact"""
        return self.behavioral_profiles.get(contact_email.lower())
    
    async def get_cross_platform_insights(self) -> Dict:
        """Get insights about cross-platform communication patterns"""
        
        cross_platform_contacts = [
            profile for profile in self.behavioral_profiles.values()
            if len(profile.data_sources) > 1 and profile.confidence_score > 0.3
        ]
        
        insights = {
            'total_contacts': len(self.behavioral_profiles),
            'cross_platform_contacts': len(cross_platform_contacts),
            'platform_breakdown': {},
            'style_consistency': {},
            'influence_correlation': {}
        }
        
        # Platform breakdown
        all_platforms = set()
        for profile in self.behavioral_profiles.values():
            all_platforms.update(profile.data_sources)
        
        for platform in all_platforms:
            insights['platform_breakdown'][platform] = sum(
                1 for p in self.behavioral_profiles.values() 
                if platform in p.data_sources
            )
        
        return insights
    
    async def generate_communication_strategy(self, contact_email: str) -> Optional[Dict]:
        """Generate personalized communication strategy for a contact"""
        
        profile = await self.get_behavioral_profile(contact_email)
        if not profile or profile.confidence_score < 0.3:
            return None
        
        strategy = {
            'contact_email': contact_email,
            'data_quality': {
                'confidence_score': profile.confidence_score,
                'data_sources': list(profile.data_sources),
                'interactions_analyzed': profile.total_interactions
            },
            'communication_approach': {},
            'timing_recommendations': {},
            'platform_preferences': {},
            'relationship_insights': {}
        }
        
        # Communication approach based on style
        if profile.primary_style == CommunicationStyle.ANALYTICAL:
            strategy['communication_approach'] = {
                'style': 'data_driven',
                'recommendations': [
                    'Include specific metrics and data points',
                    'Provide detailed analysis and evidence',
                    'Use charts or graphs when possible',
                    'Be precise and factual'
                ]
            }
        elif profile.primary_style == CommunicationStyle.RELATIONSHIP_FOCUSED:
            strategy['communication_approach'] = {
                'style': 'relationship_building',
                'recommendations': [
                    'Use warm, personal tone',
                    'Acknowledge their contributions',
                    'Include team impact and collaboration aspects',
                    f"{'Use emojis appropriately' if profile.emoji_usage_frequency > 0.3 else 'Keep tone professional'}"
                ]
            }
        elif profile.primary_style == CommunicationStyle.RESULTS_ORIENTED:
            strategy['communication_approach'] = {
                'style': 'action_focused',
                'recommendations': [
                    'Lead with outcomes and results',
                    'Be direct and concise',
                    'Include clear action items',
                    'Emphasize deadlines and deliverables'
                ]
            }
        elif profile.primary_style == CommunicationStyle.COLLABORATIVE:
            strategy['communication_approach'] = {
                'style': 'collaborative',
                'recommendations': [
                    'Ask for their input and feedback',
                    'Frame as joint problem-solving',
                    'Use inclusive language',
                    'Provide multiple options for consideration'
                ]
            }
        
        # Timing recommendations
        if profile.preferred_communication_times:
            peak_hours = self._find_peak_communication_hours(profile.preferred_communication_times)
            strategy['timing_recommendations'] = {
                'best_hours': peak_hours,
                'weekend_ok': profile.weekend_activity,
                'message_length_preference': 'detailed' if profile.avg_message_length > 100 else 'concise'
            }
        
        # Platform preferences
        strategy['platform_preferences'] = {
            'active_platforms': list(profile.data_sources),
            'multi_platform_user': len(profile.data_sources) > 1,
            'primary_platform': max(profile.data_sources) if profile.data_sources else 'email'
        }
        
        # Relationship insights
        strategy['relationship_insights'] = {
            'influence_level': profile.influence_level.value,
            'strategic_importance': self._assess_strategic_importance(profile),
            'collaboration_style': 'question_oriented' if profile.question_frequency > 0.15 else 'statement_oriented',
            'communication_frequency': 'high' if profile.total_interactions > 20 else 'medium' if profile.total_interactions > 5 else 'low'
        }
        
        return strategy 