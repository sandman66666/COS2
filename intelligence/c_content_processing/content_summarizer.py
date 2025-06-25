"""
Content Summarizer
Creates lightweight content summaries without expensive Claude API calls.
Prepares clean, structured summaries for strategic analysis phase.
"""

import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from collections import Counter

from intelligence.b_data_collection.data_organizer import ContentItem, TopicCluster, OrganizedContent

@dataclass
class ContentSummary:
    topic_name: str
    key_points: List[str]
    participants: List[str]
    timeline_summary: str
    business_context: str
    priority_level: str
    action_items: List[str]
    content_types: Dict[str, int]  # type -> count
    engagement_metrics: Dict[str, float]

@dataclass
class ContactSummary:
    email: str
    name: str
    company: str
    role: str
    relationship_status: str
    communication_summary: str
    topics_involved: List[str]
    last_interaction: str
    next_action: str

class ContentSummarizer:
    def __init__(self):
        self.action_keywords = [
            'need to', 'should', 'must', 'will', 'plan to', 'going to',
            'action item', 'todo', 'deadline', 'due', 'schedule', 'meeting'
        ]
        
        self.key_phrase_patterns = [
            r'the main (point|issue|challenge|opportunity) is',
            r'key (takeaway|insight|finding|result)',
            r'important to (note|remember|consider)',
            r'critical (factor|element|component)',
            r'(conclusion|summary|bottom line)',
            r'(decision|agreement|resolution) to',
        ]

    def create_summaries(self, organized_content: OrganizedContent) -> Tuple[Dict[str, ContentSummary], Dict[str, ContactSummary]]:
        """
        Create lightweight summaries of topics and contacts
        """
        print("📝 Creating content summaries...")
        
        # Create topic summaries
        topic_summaries = {}
        for topic_name, cluster in organized_content.topics.items():
            summary = self._create_topic_summary(topic_name, cluster, organized_content)
            topic_summaries[topic_name] = summary
        
        print(f"✅ Created {len(topic_summaries)} topic summaries")
        
        # Create contact summaries  
        contact_summaries = {}
        for email, profile in organized_content.communication_profiles.items():
            summary = self._create_contact_summary(email, profile, organized_content)
            contact_summaries[email] = summary
            
        print(f"✅ Created {len(contact_summaries)} contact summaries")
        
        return topic_summaries, contact_summaries

    def _create_topic_summary(self, topic_name: str, cluster: TopicCluster, 
                            organized_content: OrganizedContent) -> ContentSummary:
        """Create summary for a topic cluster"""
        
        # Get all content items for this topic
        content_items = [organized_content.content_index[item_id] 
                        for item_id in cluster.content_items 
                        if item_id in organized_content.content_index]
        
        # Extract key points from content
        key_points = self._extract_key_points(content_items)
        
        # Create timeline summary
        timeline_summary = self._create_timeline_summary(content_items)
        
        # Generate business context
        business_context = self._generate_business_context(cluster, content_items)
        
        # Determine priority level
        priority_level = self._determine_priority_level(cluster.priority_score)
        
        # Extract action items
        action_items = self._extract_action_items(content_items)
        
        # Count content types
        content_types = Counter(item.type for item in content_items)
        
        # Calculate engagement metrics
        engagement_metrics = self._calculate_engagement_metrics(content_items, organized_content)
        
        return ContentSummary(
            topic_name=topic_name,
            key_points=key_points,
            participants=list(cluster.participants),
            timeline_summary=timeline_summary,
            business_context=business_context,
            priority_level=priority_level,
            action_items=action_items,
            content_types=dict(content_types),
            engagement_metrics=engagement_metrics
        )

    def _create_contact_summary(self, email: str, profile, organized_content: OrganizedContent) -> ContactSummary:
        """Create summary for a contact"""
        
        # Get content items involving this contact
        contact_items = [item for item in organized_content.content_index.values() 
                        if email in item.participants]
        
        # Extract name and company from content
        name, company = self._extract_contact_info(email, contact_items)
        
        # Determine role
        role = self._determine_role(email, contact_items)
        
        # Create communication summary
        comm_summary = self._create_communication_summary(profile)
        
        # Get topics this contact is involved in
        topics_involved = list(set(topic for item in contact_items 
                                 for topic in (item.topics or [])))
        
        # Get last interaction summary
        last_interaction = self._get_last_interaction_summary(contact_items)
        
        # Determine next action
        next_action = self._determine_next_action(profile, contact_items)
        
        return ContactSummary(
            email=email,
            name=name,
            company=company,
            role=role,
            relationship_status=profile.relationship_status.value,
            communication_summary=comm_summary,
            topics_involved=topics_involved,
            last_interaction=last_interaction,
            next_action=next_action
        )

    def _extract_key_points(self, content_items: List[ContentItem]) -> List[str]:
        """Extract key points from content using pattern matching"""
        key_points = []
        
        for item in content_items:
            text = item.content + " " + item.subject
            
            # Look for key phrase patterns
            for pattern in self.key_phrase_patterns:
                matches = re.finditer(pattern, text.lower())
                for match in matches:
                    # Extract sentence containing the key phrase
                    sentence_start = text.rfind('.', 0, match.start()) + 1
                    sentence_end = text.find('.', match.end())
                    if sentence_end == -1:
                        sentence_end = len(text)
                    
                    sentence = text[sentence_start:sentence_end].strip()
                    if len(sentence) > 20 and len(sentence) < 200:
                        key_points.append(sentence)
            
            # Extract first and last sentences if they seem important
            sentences = text.split('.')
            for sentence in sentences[:2] + sentences[-2:]:
                sentence = sentence.strip()
                if (len(sentence) > 30 and 
                    any(keyword in sentence.lower() for keyword in ['important', 'key', 'main', 'critical'])):
                    key_points.append(sentence)
        
        # Remove duplicates and return top key points
        unique_points = list(set(key_points))
        return unique_points[:10]

    def _create_timeline_summary(self, content_items: List[ContentItem]) -> str:
        """Create timeline summary for content items"""
        if not content_items:
            return "No timeline data available"
        
        # Sort by timestamp
        sorted_items = sorted(content_items, key=lambda x: x.timestamp)
        
        start_date = sorted_items[0].timestamp.strftime("%Y-%m-%d")
        end_date = sorted_items[-1].timestamp.strftime("%Y-%m-%d")
        
        # Count content by type
        type_counts = Counter(item.type for item in content_items)
        
        summary = f"Activity from {start_date} to {end_date}. "
        summary += f"Total communications: {len(content_items)} "
        
        type_parts = []
        for content_type, count in type_counts.items():
            type_parts.append(f"{count} {content_type}s")
        
        summary += f"({', '.join(type_parts)})"
        
        return summary

    def _generate_business_context(self, cluster: TopicCluster, content_items: List[ContentItem]) -> str:
        """Generate business context for topic"""
        
        # Analyze business relevance scores
        avg_relevance = sum(item.business_relevance for item in content_items) / len(content_items)
        
        # Determine context based on business domain and relevance
        domain_contexts = {
            "ai_technology": "Technology development and AI innovation discussions",
            "music_industry": "Music industry partnerships and audio technology",
            "venture_capital": "Funding, investment, and venture capital activities", 
            "legal_compliance": "Legal matters, contracts, and compliance issues",
            "business_development": "Business partnerships and growth opportunities",
            "product_development": "Product features, development, and technical discussions",
            "marketing_sales": "Marketing initiatives and sales activities",
            "finance_operations": "Financial operations and business administration"
        }
        
        base_context = domain_contexts.get(cluster.business_domain, "General business discussions")
        
        if avg_relevance > 0.7:
            context = f"High-priority {base_context.lower()} with significant business impact"
        elif avg_relevance > 0.4:
            context = f"Moderate-priority {base_context.lower()} requiring attention"
        else:
            context = f"Low-priority {base_context.lower()} for awareness"
        
        return context

    def _determine_priority_level(self, priority_score: float) -> str:
        """Determine priority level from score"""
        if priority_score > 0.7:
            return "high"
        elif priority_score > 0.4:
            return "medium"
        else:
            return "low"

    def _extract_action_items(self, content_items: List[ContentItem]) -> List[str]:
        """Extract action items from content"""
        action_items = []
        
        for item in content_items:
            text = item.content.lower()
            
            # Look for action keywords
            for keyword in self.action_keywords:
                if keyword in text:
                    # Extract sentences containing action keywords
                    sentences = item.content.split('.')
                    for sentence in sentences:
                        if keyword in sentence.lower() and len(sentence.strip()) > 10:
                            action_items.append(sentence.strip())
        
        # Remove duplicates and return top action items
        unique_actions = list(set(action_items))
        return unique_actions[:5]

    def _calculate_engagement_metrics(self, content_items: List[ContentItem], 
                                    organized_content: OrganizedContent) -> Dict[str, float]:
        """Calculate engagement metrics for topic"""
        if not content_items:
            return {}
        
        # Get unique participants
        all_participants = set()
        for item in content_items:
            all_participants.update(item.participants)
        
        # Calculate average engagement score from communication profiles
        total_engagement = 0
        profile_count = 0
        
        for participant in all_participants:
            if participant in organized_content.communication_profiles:
                profile = organized_content.communication_profiles[participant]
                total_engagement += profile.engagement_score
                profile_count += 1
        
        avg_engagement = total_engagement / profile_count if profile_count > 0 else 0
        
        # Calculate other metrics
        avg_urgency = sum(item.urgency_score for item in content_items) / len(content_items)
        avg_relevance = sum(item.business_relevance for item in content_items) / len(content_items)
        participant_diversity = len(all_participants)
        
        return {
            "average_engagement": avg_engagement,
            "average_urgency": avg_urgency,
            "average_relevance": avg_relevance,
            "participant_diversity": participant_diversity,
            "content_volume": len(content_items)
        }

    def _extract_contact_info(self, email: str, content_items: List[ContentItem]) -> Tuple[str, str]:
        """Extract name and company from email content"""
        name = ""
        company = ""
        
        # Look for signatures and contact info in emails
        for item in content_items:
            if item.type == "email":
                content = item.content
                
                # Look for name patterns in signatures
                name_patterns = [
                    r'best regards,\s*([A-Za-z\s]+)',
                    r'sincerely,\s*([A-Za-z\s]+)',
                    r'thanks,\s*([A-Za-z\s]+)',
                    r'^([A-Za-z\s]+)\n',  # First line
                ]
                
                for pattern in name_patterns:
                    match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
                    if match and not name:
                        potential_name = match.group(1).strip()
                        if len(potential_name.split()) <= 3:  # Reasonable name length
                            name = potential_name
                            break
                
                # Extract company from email domain
                if not company and email:
                    domain = email.split('@')[-1].lower()
                    if domain not in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']:
                        # Remove common domain suffixes
                        company_name = domain.replace('.com', '').replace('.org', '').replace('.net', '')
                        company = company_name.title()
        
        return name or email.split('@')[0], company

    def _determine_role(self, email: str, content_items: List[ContentItem]) -> str:
        """Determine contact's role from content"""
        
        # Look for role indicators in email content
        role_patterns = {
            'ceo': ['ceo', 'chief executive', 'founder'],
            'cto': ['cto', 'chief technology', 'chief technical'],
            'cfo': ['cfo', 'chief financial'],
            'vp': ['vice president', 'vp of', 'vp,'],
            'director': ['director of', 'director,'],
            'manager': ['manager', 'mgr'],
            'engineer': ['engineer', 'developer', 'dev'],
            'investor': ['investor', 'venture', 'partner at'],
            'lawyer': ['attorney', 'lawyer', 'legal counsel']
        }
        
        for item in content_items:
            content_lower = item.content.lower()
            for role, keywords in role_patterns.items():
                if any(keyword in content_lower for keyword in keywords):
                    return role
        
        # Default based on email domain patterns
        domain = email.split('@')[-1].lower()
        if 'vc' in domain or 'ventures' in domain or 'capital' in domain:
            return 'investor'
        elif 'law' in domain or 'legal' in domain:
            return 'lawyer'
        
        return 'contact'

    def _create_communication_summary(self, profile) -> str:
        """Create communication summary from profile"""
        status_desc = {
            'established': 'Active relationship with regular communication',
            'ongoing': 'Currently engaged in active discussions',
            'attempted': 'Outreach attempted, limited response',
            'cold': 'Recent contact, awaiting response',
            'dormant': 'Previously active, now inactive'
        }
        
        base_summary = status_desc.get(profile.relationship_status.value, 'Unknown status')
        
        if profile.response_rate > 0:
            base_summary += f". Response rate: {profile.response_rate:.0%}"
        
        if profile.avg_response_time:
            days = profile.avg_response_time.days
            if days > 0:
                base_summary += f". Typical response time: {days} days"
            else:
                hours = profile.avg_response_time.seconds // 3600
                base_summary += f". Typical response time: {hours} hours"
        
        return base_summary

    def _get_last_interaction_summary(self, content_items: List[ContentItem]) -> str:
        """Get summary of last interaction"""
        if not content_items:
            return "No recent interactions"
        
        # Get most recent item
        latest_item = max(content_items, key=lambda x: x.timestamp)
        
        date_str = latest_item.timestamp.strftime("%Y-%m-%d")
        summary = f"Last {latest_item.type} on {date_str}"
        
        if latest_item.subject:
            summary += f": {latest_item.subject[:50]}..."
        
        return summary

    def _determine_next_action(self, profile, content_items: List[ContentItem]) -> str:
        """Determine recommended next action"""
        
        status = profile.relationship_status.value
        
        if status == 'attempted':
            return "Follow up with alternative approach or warm introduction"
        elif status == 'cold':
            return "Wait for response, consider gentle follow-up in 1 week"
        elif status == 'dormant':
            return "Re-engage with relevant update or opportunity"
        elif status == 'ongoing':
            return "Continue active communication and monitor for opportunities"
        elif status == 'established':
            return "Maintain relationship and explore collaboration opportunities"
        
        return "Review communication status and determine appropriate action" 