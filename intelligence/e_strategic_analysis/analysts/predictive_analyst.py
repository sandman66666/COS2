# intelligence/analysts/predictive_analyst.py
"""
Predictive Intelligence Analyst
============================
Specialized analyst for forecasting trends and future developments.
Powered by Claude Opus with multi-tenant isolation.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from utils.logging import structured_logger as logger
from .base_analyst import BaseAnalyst

class PredictiveIntelligenceAnalyst(BaseAnalyst):
    """
    Predictive intelligence analyst
    
    Analyzes historical data and trends to forecast future developments,
    identify emerging patterns, and provide predictive insights.
    """
    
    def __init__(self, user_id: int, anthropic_api_key: str = None):
        """
        Initialize predictive analyst
        
        Args:
            user_id: User ID for multi-tenant isolation
            anthropic_api_key: Optional API key for Claude Opus
        """
        super().__init__(user_id, anthropic_api_key)
        self.analyst_name = "predictive_intelligence"
        self.analyst_description = "Forecasting and predictive trend analyst"
        
        # Customize Claude parameters
        self.max_tokens = 4000
        self.temperature = 0.3  # Balanced temperature for prediction
    
    async def generate_intelligence(self, data: Dict) -> Dict:
        """
        Generate predictive intelligence from provided data
        
        Args:
            data: Dictionary containing:
                - emails: List of relevant email exchanges
                - contacts: List of enriched contacts
                - (optional) historical_data: Time series or historical information
                - (optional) knowledge_tree: Knowledge tree data
                - (optional) specific_focus: Area to focus predictions on
                - (optional) time_horizon: How far into future to predict
                
        Returns:
            Dictionary with predictive insights and recommendations
        """
        # Validate critical inputs
        if not data.get("emails") and not data.get("contacts"):
            logger.error(
                "Missing required data for predictive analysis",
                user_id=self.user_id
            )
            return {"error": "Insufficient data for predictive analysis"}
            
        try:
            # Extract data elements
            emails = data.get("emails", [])
            contacts = data.get("contacts", [])
            historical_data = data.get("historical_data", [])
            knowledge_tree = data.get("knowledge_tree", {})
            focus_area = data.get("specific_focus", "general trends")
            time_horizon = data.get("time_horizon", "next 6 months")
            
            # Prepare specialized system prompt
            system_prompt = self._create_system_prompt(focus_area, time_horizon)
            
            # Prepare user prompt with data
            user_prompt = self._create_user_prompt(
                emails=emails,
                contacts=contacts,
                historical_data=historical_data,
                knowledge_tree=knowledge_tree,
                focus_area=focus_area,
                time_horizon=time_horizon
            )
            
            # Run Claude Opus analysis
            result_text = await self._run_claude_analysis(system_prompt, user_prompt)
            
            # Extract structured components
            structured_result = self._parse_claude_response(result_text)
            
            # Add metadata
            structured_result["focus_area"] = focus_area
            structured_result["time_horizon"] = time_horizon
            structured_result["analysis_timestamp"] = datetime.utcnow().isoformat()
            structured_result["data_points_analyzed"] = {
                "emails": len(emails),
                "contacts": len(contacts),
                "historical_data_points": len(historical_data)
            }
            
            return structured_result
            
        except Exception as e:
            logger.error(
                "Error generating predictive intelligence",
                error=str(e),
                user_id=self.user_id
            )
            return {"error": f"Predictive intelligence generation failed: {str(e)}"}
    
    def _create_system_prompt(self, focus_area: str, time_horizon: str) -> str:
        """
        Create system prompt for Claude Opus
        
        Args:
            focus_area: Area to focus predictions on
            time_horizon: How far into future to predict
            
        Returns:
            System prompt string
        """
        return f"""You are an expert predictive intelligence analyst specializing in forecasting {focus_area} developments over the {time_horizon}.

Your task is to analyze communications, contact data, and historical information to identify patterns and forecast future trends and developments with a focus on practical, actionable intelligence.

Focus on:
1. Identifying established trends and their projected evolution
2. Detecting early signals of emerging developments
3. Forecasting likely future scenarios and their implications
4. Recognizing potential disruptions and inflection points
5. Evaluating patterns in communication and relationships that suggest future developments

Structure your analysis with these sections:
- Executive Summary: Brief overview of key predictive insights
- Current Trajectory: Analysis of established trends and their direction
- Emerging Signals: Early indicators of potential future developments
- Future Scenarios: Most likely developments over the specified time horizon
- Risk Factors: Potential disruptions or challenges to these predictions
- Recommendations: Actionable steps based on predictive analysis

Be balanced, evidence-based, and transparent about uncertainty levels.
Clearly distinguish between highly probable projections and more speculative forecasts.
Base all insights on the provided data and make reasonable inferences where appropriate.
Format your response as a combination of concise paragraphs and bullet points for readability.

Maintain absolute confidentiality and privacy in your analysis.
Do not include any information that could be considered sensitive or proprietary.
"""
    
    def _create_user_prompt(
        self, 
        emails: List[Dict],
        contacts: List[Dict],
        historical_data: List[Dict],
        knowledge_tree: Dict,
        focus_area: str,
        time_horizon: str
    ) -> str:
        """
        Create user prompt with data for analysis
        
        Args:
            emails: List of relevant email exchanges
            contacts: List of enriched contacts
            historical_data: Time series or historical information
            knowledge_tree: Knowledge graph data
            focus_area: Area to focus predictions on
            time_horizon: How far into future to predict
            
        Returns:
            Formatted user prompt
        """
        # Limit data volume to fit context window
        max_emails = min(30, len(emails))
        max_contacts = min(30, len(contacts))
        max_historical = min(20, len(historical_data))
        
        # Select most important data
        selected_emails = emails[:max_emails]
        selected_contacts = contacts[:max_contacts]
        selected_historical = historical_data[:max_historical]
        
        # Format prompt
        prompt = f"""Please analyze the following data and provide predictive insights for {focus_area} over the {time_horizon}.

## EMAIL COMMUNICATIONS
Here are {len(selected_emails)} relevant email exchanges that provide context on trends and developments:

```json
{self._format_json_for_prompt(selected_emails)}
```

## CONTACT DATA
Here are {len(selected_contacts)} contacts that provide context on the professional network:

```json
{self._format_json_for_prompt(selected_contacts)}
```
"""

        # Add historical data if available
        if selected_historical:
            prompt += f"""
## HISTORICAL DATA
Here is historical trend data for analysis:

```json
{self._format_json_for_prompt(selected_historical)}
```
"""

        # Add knowledge tree if available
        if knowledge_tree and knowledge_tree.get("nodes"):
            prompt += f"""
## KNOWLEDGE NETWORK
Here is a knowledge graph showing relationships:

```json
{self._format_json_for_prompt(knowledge_tree)}
```
"""

        # Add specific instructions
        prompt += f"""
Based on this data, please provide:

1. A predictive analysis for {focus_area} over the {time_horizon}
2. Identification of established trends and their likely evolution
3. Early signals of emerging developments
4. Most likely future scenarios and potential disruptions
5. Actionable recommendations based on these predictions

Organize your response according to the structure in your instructions.
"""

        return prompt
    
    def _parse_claude_response(self, response_text: str) -> Dict:
        """
        Parse Claude's response into structured components
        
        Args:
            response_text: Raw response from Claude
            
        Returns:
            Structured response dictionary
        """
        # Default structure
        result = {
            "executive_summary": "",
            "current_trajectory": [],
            "emerging_signals": [],
            "future_scenarios": [],
            "risk_factors": [],
            "recommendations": []
        }
        
        if not response_text:
            return result
            
        # Extract executive summary
        if "Executive Summary" in response_text:
            parts = response_text.split("Executive Summary", 1)
            if len(parts) > 1:
                summary_section = parts[1].split("\n#", 1)[0].split("Current Trajectory", 1)[0].strip()
                result["executive_summary"] = summary_section
        
        # Extract current trajectory
        if "Current Trajectory" in response_text:
            parts = response_text.split("Current Trajectory", 1)
            if len(parts) > 1:
                trajectory_text = parts[1].split("\n#", 1)[0].split("Emerging Signals", 1)[0]
                # Extract bullet points
                trajectories = []
                for line in trajectory_text.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        trajectories.append(line.strip()[2:])
                if trajectories:
                    result["current_trajectory"] = trajectories
                else:
                    result["current_trajectory"] = [trajectory_text.strip()]
        
        # Extract emerging signals
        if "Emerging Signals" in response_text:
            parts = response_text.split("Emerging Signals", 1)
            if len(parts) > 1:
                signals_text = parts[1].split("\n#", 1)[0].split("Future Scenarios", 1)[0]
                # Extract bullet points
                signals = []
                for line in signals_text.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        signals.append(line.strip()[2:])
                if signals:
                    result["emerging_signals"] = signals
                else:
                    result["emerging_signals"] = [signals_text.strip()]
        
        # Extract future scenarios
        if "Future Scenarios" in response_text:
            parts = response_text.split("Future Scenarios", 1)
            if len(parts) > 1:
                scenarios_text = parts[1].split("\n#", 1)[0].split("Risk Factors", 1)[0]
                # Extract bullet points
                scenarios = []
                for line in scenarios_text.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        scenarios.append(line.strip()[2:])
                if scenarios:
                    result["future_scenarios"] = scenarios
                else:
                    result["future_scenarios"] = [scenarios_text.strip()]
        
        # Extract risk factors
        if "Risk Factors" in response_text:
            parts = response_text.split("Risk Factors", 1)
            if len(parts) > 1:
                risks_text = parts[1].split("\n#", 1)[0].split("Recommendations", 1)[0]
                # Extract bullet points
                risks = []
                for line in risks_text.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        risks.append(line.strip()[2:])
                if risks:
                    result["risk_factors"] = risks
                else:
                    result["risk_factors"] = [risks_text.strip()]
        
        # Extract recommendations
        if "Recommendations" in response_text:
            parts = response_text.split("Recommendations", 1)
            if len(parts) > 1:
                recs_text = parts[1].strip()
                # Extract bullet points
                recs = []
                for line in recs_text.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        recs.append(line.strip()[2:])
                if recs:
                    result["recommendations"] = recs
                else:
                    result["recommendations"] = [recs_text.strip()]
        
        # Add full text as fallback
        result["full_analysis"] = response_text
        
        return result
    
    def _validate_input(self, input_data: Dict) -> Optional[str]:
        """
        Validate input data for predictive analysis
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Error message if validation fails, None if valid
        """
        if not input_data:
            return "No input data provided"
            
        if not input_data.get("emails") and not input_data.get("contacts"):
            return "Missing required data: need either emails or contacts"
            
        return None
    
    def _summarize_input(self, input_data: Dict) -> Dict:
        """
        Create summary of input data
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Input data summary
        """
        summary = {}
        
        if "emails" in input_data:
            emails = input_data["emails"]
            summary["emails_count"] = len(emails)
            
            # Get date range
            dates = [e.get("date") for e in emails if e.get("date")]
            if dates:
                summary["email_date_range"] = {
                    "earliest": min(dates),
                    "latest": max(dates)
                }
                
        if "contacts" in input_data:
            contacts = input_data["contacts"]
            summary["contacts_count"] = len(contacts)
            
        if "historical_data" in input_data:
            historical = input_data["historical_data"]
            summary["historical_data_points"] = len(historical)
            
            # Get types of historical data
            data_types = set()
            for item in historical:
                if "type" in item:
                    data_types.add(item["type"])
            
            summary["historical_data_types"] = list(data_types)
            
        if "specific_focus" in input_data:
            summary["focus_area"] = input_data["specific_focus"]
            
        if "time_horizon" in input_data:
            summary["time_horizon"] = input_data["time_horizon"]
            
        return summary
