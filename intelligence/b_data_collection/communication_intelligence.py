"""
Communication Intelligence Analyzer
Analyzes email threads, response patterns, and relationship status to provide accurate
relationship assessment for strategic analysis.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class RelationshipStatus(Enum):
    ESTABLISHED = "established"  # Bidirectional communication with positive responses
    ATTEMPTED = "attempted"      # Outbound only, no response or negative response
    COLD = "cold"               # Initial outreach, status unknown
    ONGOING = "ongoing"         # Active back-and-forth communication
    DORMANT = "dormant"         # Previously active, now inactive

class CommunicationDirection(Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"

@dataclass
class EmailAnalysis:
    sender: str
    recipient: str
    timestamp: datetime
    subject: str
    content: str
    is_reply: bool
    thread_id: str
    response_time: Optional[timedelta] = None
    sentiment: str = "neutral"
    length: int = 0

@dataclass
class CommunicationProfile:
    email: str
    relationship_status: RelationshipStatus
    communication_direction: CommunicationDirection
    total_emails: int
    outbound_count: int
    inbound_count: int
    response_rate: float
    avg_response_time: Optional[timedelta]
    last_contact: datetime
    last_response: Optional[datetime]
    engagement_score: float
    response_quality: str  # "detailed", "brief", "auto_reply", "none"
    sentiment_trend: str   # "positive", "negative", "neutral", "declining"

class CommunicationIntelligenceAnalyzer:
    def __init__(self):
        self.auto_reply_patterns = [
            r"thank you for your email",
            r"i'm currently out of office",
            r"auto.*reply",
            r"this is an automated",
            r"noreply",
            r"do not reply"
        ]
        
        self.positive_patterns = [
            r"thank you", r"thanks", r"appreciate",
            r"looking forward", r"great", r"excellent",
            r"yes", r"absolutely", r"definitely",
            r"happy to", r"pleased to"
        ]
        
        self.negative_patterns = [
            r"unfortunately", r"cannot", r"unable",
            r"not interested", r"no thank you",
            r"decline", r"pass", r"busy"
        ]

    def analyze_email_thread(self, emails: List[Dict]) -> Dict[str, CommunicationProfile]:
        """
        Analyze email communications to determine actual relationship status
        """
        # Group emails by contact
        contact_emails = self._group_emails_by_contact(emails)
        
        profiles = {}
        for contact_email, email_list in contact_emails.items():
            profile = self._analyze_contact_communication(contact_email, email_list)
            profiles[contact_email] = profile
            
        return profiles

    def _group_emails_by_contact(self, emails: List[Dict]) -> Dict[str, List[EmailAnalysis]]:
        """Group emails by contact email address"""
        contact_groups = {}
        
        for email_data in emails:
            # Extract sender/recipient info
            sender = email_data.get('sender', '').lower()
            recipients = email_data.get('recipients', [])
            
            # Determine which contact this email involves
            contact_email = None
            if sender != email_data.get('user_email', '').lower():
                contact_email = sender
            else:
                # This is an outbound email, get the primary recipient
                for recipient in recipients:
                    if recipient.lower() != email_data.get('user_email', '').lower():
                        contact_email = recipient.lower()
                        break
            
            if contact_email:
                if contact_email not in contact_groups:
                    contact_groups[contact_email] = []
                
                email_analysis = EmailAnalysis(
                    sender=sender,
                    recipient=recipients[0] if recipients else '',
                    timestamp=datetime.fromisoformat(email_data.get('created_at', '')),
                    subject=email_data.get('subject', ''),
                    content=email_data.get('content', ''),
                    is_reply=self._is_reply(email_data.get('subject', '')),
                    thread_id=email_data.get('thread_id', ''),
                    length=len(email_data.get('content', ''))
                )
                
                contact_groups[contact_email].append(email_analysis)
        
        # Sort each contact's emails by timestamp
        for contact_email in contact_groups:
            contact_groups[contact_email].sort(key=lambda x: x.timestamp)
            
        return contact_groups

    def _analyze_contact_communication(self, contact_email: str, emails: List[EmailAnalysis]) -> CommunicationProfile:
        """Analyze communication pattern with a specific contact"""
        user_email = emails[0].sender.lower() if emails else ""
        
        # Count inbound vs outbound
        outbound_count = sum(1 for email in emails if email.sender.lower() == user_email)
        inbound_count = len(emails) - outbound_count
        
        # Analyze response patterns
        response_times = []
        last_outbound_time = None
        has_responses = False
        
        for email in emails:
            if email.sender.lower() == user_email:
                # This is an outbound email
                last_outbound_time = email.timestamp
            else:
                # This is an inbound email (response)
                has_responses = True
                if last_outbound_time:
                    response_time = email.timestamp - last_outbound_time
                    response_times.append(response_time)
                    last_outbound_time = None
        
        # Calculate metrics
        response_rate = inbound_count / outbound_count if outbound_count > 0 else 0
        avg_response_time = sum(response_times, timedelta()) / len(response_times) if response_times else None
        
        # Determine relationship status
        relationship_status = self._determine_relationship_status(
            outbound_count, inbound_count, response_rate, emails
        )
        
        # Determine communication direction
        if outbound_count > 0 and inbound_count > 0:
            direction = CommunicationDirection.BIDIRECTIONAL
        elif outbound_count > 0:
            direction = CommunicationDirection.OUTBOUND
        else:
            direction = CommunicationDirection.INBOUND
        
        # Calculate engagement score
        engagement_score = self._calculate_engagement_score(
            response_rate, inbound_count, emails
        )
        
        # Analyze response quality and sentiment
        response_quality = self._analyze_response_quality(emails, user_email)
        sentiment_trend = self._analyze_sentiment_trend(emails)
        
        # Get timing info
        last_contact = max(email.timestamp for email in emails) if emails else datetime.now()
        last_response = max(
            (email.timestamp for email in emails if email.sender.lower() != user_email),
            default=None
        )
        
        return CommunicationProfile(
            email=contact_email,
            relationship_status=relationship_status,
            communication_direction=direction,
            total_emails=len(emails),
            outbound_count=outbound_count,
            inbound_count=inbound_count,
            response_rate=response_rate,
            avg_response_time=avg_response_time,
            last_contact=last_contact,
            last_response=last_response,
            engagement_score=engagement_score,
            response_quality=response_quality,
            sentiment_trend=sentiment_trend
        )

    def _determine_relationship_status(self, outbound_count: int, inbound_count: int, 
                                     response_rate: float, emails: List[EmailAnalysis]) -> RelationshipStatus:
        """Determine the actual relationship status based on communication patterns"""
        
        if outbound_count == 0 and inbound_count > 0:
            return RelationshipStatus.ESTABLISHED  # They initiated contact
        
        if inbound_count == 0 and outbound_count > 0:
            # Check if emails are very recent (might be cold outreach)
            latest_email = max(emails, key=lambda x: x.timestamp)
            if (datetime.now() - latest_email.timestamp).days < 7:
                return RelationshipStatus.COLD
            else:
                return RelationshipStatus.ATTEMPTED  # No response to outbound emails
        
        if response_rate >= 0.5 and inbound_count >= 2:
            # Check if recent activity
            latest_email = max(emails, key=lambda x: x.timestamp)
            if (datetime.now() - latest_email.timestamp).days < 30:
                return RelationshipStatus.ONGOING
            else:
                return RelationshipStatus.ESTABLISHED
        
        if response_rate > 0 and response_rate < 0.5:
            # Some responses but low rate
            latest_response = None
            for email in reversed(emails):
                if email.sender.lower() != emails[0].sender.lower():
                    latest_response = email.timestamp
                    break
            
            if latest_response and (datetime.now() - latest_response).days > 60:
                return RelationshipStatus.DORMANT
            else:
                return RelationshipStatus.ATTEMPTED
        
        return RelationshipStatus.ATTEMPTED

    def _calculate_engagement_score(self, response_rate: float, inbound_count: int, 
                                  emails: List[EmailAnalysis]) -> float:
        """Calculate engagement score (0-1) based on communication quality"""
        base_score = response_rate * 0.4
        
        # Bonus for multiple responses
        response_bonus = min(inbound_count * 0.1, 0.3)
        
        # Bonus for detailed responses
        detail_bonus = 0
        user_email = emails[0].sender.lower() if emails else ""
        for email in emails:
            if email.sender.lower() != user_email and email.length > 100:
                detail_bonus += 0.05
        detail_bonus = min(detail_bonus, 0.3)
        
        return min(base_score + response_bonus + detail_bonus, 1.0)

    def _analyze_response_quality(self, emails: List[EmailAnalysis], user_email: str) -> str:
        """Analyze the quality of responses received"""
        response_emails = [email for email in emails if email.sender.lower() != user_email.lower()]
        
        if not response_emails:
            return "none"
        
        # Check for auto-replies
        for email in response_emails:
            if self._is_auto_reply(email.content):
                return "auto_reply"
        
        # Analyze length and content
        avg_length = sum(email.length for email in response_emails) / len(response_emails)
        
        if avg_length > 200:
            return "detailed"
        elif avg_length > 50:
            return "brief"
        else:
            return "minimal"

    def _analyze_sentiment_trend(self, emails: List[EmailAnalysis]) -> str:
        """Analyze sentiment trend across communications"""
        sentiments = []
        
        for email in emails:
            sentiment_score = self._calculate_sentiment_score(email.content)
            sentiments.append(sentiment_score)
        
        if not sentiments:
            return "neutral"
        
        # Simple trend analysis
        recent_sentiment = sum(sentiments[-3:]) / min(len(sentiments), 3)
        overall_sentiment = sum(sentiments) / len(sentiments)
        
        if recent_sentiment > 0.3:
            return "positive"
        elif recent_sentiment < -0.3:
            return "negative"
        elif recent_sentiment < overall_sentiment - 0.2:
            return "declining"
        else:
            return "neutral"

    def _calculate_sentiment_score(self, content: str) -> float:
        """Calculate sentiment score for email content"""
        content_lower = content.lower()
        
        positive_count = sum(1 for pattern in self.positive_patterns 
                           if re.search(pattern, content_lower))
        negative_count = sum(1 for pattern in self.negative_patterns 
                           if re.search(pattern, content_lower))
        
        if positive_count + negative_count == 0:
            return 0
        
        return (positive_count - negative_count) / (positive_count + negative_count)

    def _is_reply(self, subject: str) -> bool:
        """Check if email is a reply based on subject"""
        return subject.lower().startswith(('re:', 'fwd:', 'fw:'))

    def _is_auto_reply(self, content: str) -> bool:
        """Check if email is an auto-reply"""
        content_lower = content.lower()
        return any(re.search(pattern, content_lower) for pattern in self.auto_reply_patterns)

    def generate_relationship_summary(self, profile: CommunicationProfile) -> str:
        """Generate human-readable relationship summary"""
        status_descriptions = {
            RelationshipStatus.ESTABLISHED: "Established relationship with confirmed engagement",
            RelationshipStatus.ATTEMPTED: "Attempted contact with limited or no response",
            RelationshipStatus.COLD: "Recent outreach, response pending",
            RelationshipStatus.ONGOING: "Active ongoing communication",
            RelationshipStatus.DORMANT: "Previously active relationship, now inactive"
        }
        
        summary = f"{status_descriptions[profile.relationship_status]}. "
        summary += f"Total emails: {profile.total_emails} "
        summary += f"(Outbound: {profile.outbound_count}, Inbound: {profile.inbound_count}). "
        summary += f"Response rate: {profile.response_rate:.1%}. "
        summary += f"Engagement score: {profile.engagement_score:.2f}. "
        summary += f"Response quality: {profile.response_quality}."
        
        return summary 