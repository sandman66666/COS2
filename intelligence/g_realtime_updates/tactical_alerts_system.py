"""
Tactical Alerts System
=====================
Real-time monitoring for urgent emails and automatic action item surfacing.
Powered by Claude Opus for intelligent urgency detection.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

from utils.logging import structured_logger as logger
from intelligence.a_core.claude_analysis import claude_client
from storage.storage_manager import get_storage_manager

class AlertType(Enum):
    URGENT_RESPONSE = "urgent_response"
    DEADLINE_APPROACHING = "deadline_approaching" 
    RELATIONSHIP_RISK = "relationship_risk"
    OPPORTUNITY_WINDOW = "opportunity_window"
    ACTION_REQUIRED = "action_required"
    ESCALATION_NEEDED = "escalation_needed"

class UrgencyLevel(Enum):
    CRITICAL = "critical"  # Within 24 hours
    HIGH = "high"         # Within 3 days
    MEDIUM = "medium"     # Within 1 week
    LOW = "low"          # Within 2 weeks

@dataclass
class TacticalAlert:
    """Urgent action item or alert"""
    alert_id: str
    user_id: int
    alert_type: AlertType
    urgency: UrgencyLevel
    title: str
    description: str
    source_email_id: Optional[str]
    contact_email: Optional[str]
    deadline: Optional[datetime]
    recommended_actions: List[Dict]
    context: Dict
    created_at: datetime
    acknowledged: bool = False
    dismissed: bool = False

class TacticalAlertsSystem:
    """
    Real-time tactical alerts system that monitors emails and surfaces urgent items
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.storage_manager = None
        self.active_alerts: List[TacticalAlert] = []
        self.processed_emails: Set[str] = set()
        
    async def initialize(self):
        """Initialize the alerts system"""
        self.storage_manager = await get_storage_manager()
        await self._load_active_alerts()
        
    async def process_new_email(self, email_data: Dict) -> List[TacticalAlert]:
        """
        Process a new email for urgent alerts
        
        Args:
            email_data: Email data dictionary
            
        Returns:
            List of tactical alerts generated
        """
        email_id = email_data.get('email_id')
        if email_id in self.processed_emails:
            return []
            
        try:
            # Analyze email for urgency indicators
            urgency_analysis = await self._analyze_email_urgency(email_data)
            
            alerts = []
            if urgency_analysis.get('is_urgent'):
                # Generate tactical alerts
                new_alerts = await self._generate_alerts_from_email(email_data, urgency_analysis)
                alerts.extend(new_alerts)
                
                # Store and track alerts
                for alert in new_alerts:
                    await self._store_alert(alert)
                    self.active_alerts.append(alert)
                    
            self.processed_emails.add(email_id)
            return alerts
            
        except Exception as e:
            logger.error(f"Error processing email for alerts: {str(e)}", user_id=self.user_id)
            return []
    
    async def _analyze_email_urgency(self, email_data: Dict) -> Dict:
        """
        Use Claude to analyze email for urgency indicators
        
        Args:
            email_data: Email data dictionary
            
        Returns:
            Urgency analysis results
        """
        email_content = f"""
Subject: {email_data.get('subject', '')}
From: {email_data.get('sender_email', '')}
Date: {email_data.get('date', '')}
Content: {email_data.get('body_text', '')[:2000]}
"""
        
        prompt = f"""Analyze this email for urgent action items and tactical alerts:

{email_content}

Identify:
1. Is this email urgent? (true/false)
2. Urgency level: critical, high, medium, low
3. Type of urgency: response_needed, deadline_approaching, escalation, opportunity, relationship_risk
4. Specific action items (be concrete)
5. Deadlines or time sensitivity
6. Context and background needed
7. Recommended immediate actions (3-5 specific steps)
8. Who should be involved
9. Risks of delay or inaction

Urgent indicators to look for:
- Words like "urgent", "ASAP", "immediate", "critical", "emergency"
- Deadlines mentioned (today, tomorrow, end of week)
- Request for immediate response or action
- Escalation from previous emails
- Time-sensitive opportunities
- Relationship issues requiring attention
- Financial or business-critical matters

Format response as JSON:
{{
  "is_urgent": boolean,
  "urgency_level": "critical|high|medium|low",
  "alert_types": ["response_needed", "deadline_approaching", etc.],
  "action_items": [
    {{
      "action": "specific action",
      "deadline": "timeframe",
      "priority": "high|medium|low"
    }}
  ],
  "deadlines": [
    {{
      "description": "what's due",
      "date": "when",
      "criticality": "high|medium|low"
    }}
  ],
  "context": "situational context",
  "recommended_actions": ["action 1", "action 2"],
  "involved_parties": ["who should act"],
  "delay_risks": ["risk of not acting"],
  "opportunity_window": "time window if applicable"
}}
"""
        
        try:
            response = await asyncio.to_thread(
                claude_client.messages.create,
                model="claude-opus-4-20250514",
                max_tokens=2000,
                temperature=0.1,  # Low temperature for factual analysis
                messages=[{"role": "user", "content": prompt}]
            )
            
            analysis = json.loads(response.content[0].text)
            return analysis
            
        except Exception as e:
            logger.error(f"Error in urgency analysis: {str(e)}")
            return {"is_urgent": False}
    
    async def _generate_alerts_from_email(self, email_data: Dict, urgency_analysis: Dict) -> List[TacticalAlert]:
        """Generate tactical alerts from email and urgency analysis"""
        alerts = []
        
        # Map urgency level
        urgency_map = {
            "critical": UrgencyLevel.CRITICAL,
            "high": UrgencyLevel.HIGH,
            "medium": UrgencyLevel.MEDIUM,
            "low": UrgencyLevel.LOW
        }
        urgency = urgency_map.get(urgency_analysis.get('urgency_level', 'medium'), UrgencyLevel.MEDIUM)
        
        # Generate alerts for each type
        for alert_type_str in urgency_analysis.get('alert_types', []):
            alert_type = self._map_alert_type(alert_type_str)
            
            if alert_type:
                alert = TacticalAlert(
                    alert_id=f"alert_{datetime.utcnow().timestamp()}_{len(alerts)}",
                    user_id=self.user_id,
                    alert_type=alert_type,
                    urgency=urgency,
                    title=self._generate_alert_title(alert_type, email_data, urgency_analysis),
                    description=self._generate_alert_description(alert_type, urgency_analysis),
                    source_email_id=email_data.get('email_id'),
                    contact_email=email_data.get('sender_email'),
                    deadline=self._extract_deadline(urgency_analysis),
                    recommended_actions=urgency_analysis.get('action_items', []),
                    context={
                        'email_subject': email_data.get('subject'),
                        'urgency_analysis': urgency_analysis,
                        'email_snippet': email_data.get('body_text', '')[:200]
                    },
                    created_at=datetime.utcnow()
                )
                alerts.append(alert)
        
        return alerts
    
    def _map_alert_type(self, type_str: str) -> Optional[AlertType]:
        """Map string to AlertType enum"""
        mapping = {
            'response_needed': AlertType.URGENT_RESPONSE,
            'deadline_approaching': AlertType.DEADLINE_APPROACHING,
            'relationship_risk': AlertType.RELATIONSHIP_RISK,
            'opportunity': AlertType.OPPORTUNITY_WINDOW,
            'action_required': AlertType.ACTION_REQUIRED,
            'escalation': AlertType.ESCALATION_NEEDED
        }
        return mapping.get(type_str)
    
    def _generate_alert_title(self, alert_type: AlertType, email_data: Dict, analysis: Dict) -> str:
        """Generate contextual alert title"""
        sender = email_data.get('sender_email', 'Unknown')
        subject = email_data.get('subject', 'No Subject')
        
        if alert_type == AlertType.URGENT_RESPONSE:
            return f"Urgent Response Needed: {sender}"
        elif alert_type == AlertType.DEADLINE_APPROACHING:
            return f"Deadline Alert: {subject[:50]}"
        elif alert_type == AlertType.OPPORTUNITY_WINDOW:
            return f"Time-Sensitive Opportunity: {sender}"
        elif alert_type == AlertType.RELATIONSHIP_RISK:
            return f"Relationship Attention Needed: {sender}"
        elif alert_type == AlertType.ESCALATION_NEEDED:
            return f"Escalation Required: {subject[:50]}"
        else:
            return f"Action Required: {subject[:50]}"
    
    def _generate_alert_description(self, alert_type: AlertType, analysis: Dict) -> str:
        """Generate contextual alert description"""
        context = analysis.get('context', '')
        action_items = analysis.get('action_items', [])
        
        description = context
        if action_items:
            description += f"\n\nImmediate actions: {', '.join([a.get('action', '') for a in action_items[:3]])}"
            
        return description[:500]  # Limit length
    
    def _extract_deadline(self, analysis: Dict) -> Optional[datetime]:
        """Extract deadline from analysis"""
        deadlines = analysis.get('deadlines', [])
        if deadlines:
            # Parse first deadline - in production would use better date parsing
            deadline_str = deadlines[0].get('date', '')
            if 'today' in deadline_str.lower():
                return datetime.utcnow() + timedelta(hours=24)
            elif 'tomorrow' in deadline_str.lower():
                return datetime.utcnow() + timedelta(days=1)
            elif 'week' in deadline_str.lower():
                return datetime.utcnow() + timedelta(weeks=1)
        return None
    
    async def get_active_alerts(self, urgency_filter: Optional[UrgencyLevel] = None) -> List[TacticalAlert]:
        """
        Get active alerts, optionally filtered by urgency
        
        Args:
            urgency_filter: Optional urgency level filter
            
        Returns:
            List of active alerts
        """
        alerts = [a for a in self.active_alerts if not a.dismissed and not a.acknowledged]
        
        if urgency_filter:
            alerts = [a for a in alerts if a.urgency == urgency_filter]
            
        # Sort by urgency and creation time
        urgency_order = {
            UrgencyLevel.CRITICAL: 0,
            UrgencyLevel.HIGH: 1,
            UrgencyLevel.MEDIUM: 2,
            UrgencyLevel.LOW: 3
        }
        
        alerts.sort(key=lambda a: (urgency_order[a.urgency], a.created_at), reverse=True)
        return alerts
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark alert as acknowledged"""
        for alert in self.active_alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                await self._update_alert(alert)
                return True
        return False
    
    async def dismiss_alert(self, alert_id: str) -> bool:
        """Dismiss an alert"""
        for alert in self.active_alerts:
            if alert.alert_id == alert_id:
                alert.dismissed = True
                await self._update_alert(alert)
                return True
        return False
    
    async def get_alert_summary(self) -> Dict:
        """Get summary of current alerts"""
        active = await self.get_active_alerts()
        
        return {
            'total_active': len(active),
            'critical': len([a for a in active if a.urgency == UrgencyLevel.CRITICAL]),
            'high': len([a for a in active if a.urgency == UrgencyLevel.HIGH]),
            'medium': len([a for a in active if a.urgency == UrgencyLevel.MEDIUM]),
            'low': len([a for a in active if a.urgency == UrgencyLevel.LOW]),
            'by_type': {
                alert_type.value: len([a for a in active if a.alert_type == alert_type])
                for alert_type in AlertType
            },
            'most_urgent': active[0] if active else None
        }
    
    async def _store_alert(self, alert: TacticalAlert):
        """Store alert in database"""
        # Implementation would store in database
        pass
        
    async def _update_alert(self, alert: TacticalAlert):
        """Update alert in database"""
        # Implementation would update database
        pass
        
    async def _load_active_alerts(self):
        """Load active alerts from database"""
        # Implementation would load from database
        pass

# Global alert systems by user
_alert_systems: Dict[int, TacticalAlertsSystem] = {}

async def get_tactical_alerts_system(user_id: int) -> TacticalAlertsSystem:
    """Get or create tactical alerts system for user"""
    if user_id not in _alert_systems:
        system = TacticalAlertsSystem(user_id)
        await system.initialize()
        _alert_systems[user_id] = system
    return _alert_systems[user_id] 