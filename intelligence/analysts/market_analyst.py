# intelligence/analysts/market_analyst.py
"""
Market Intelligence Analyst
========================
Specialized analyst for market trends and competitive landscape analysis.
Powered by Claude Opus with multi-tenant isolation.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from utils.logging import structured_logger as logger
from intelligence.analysts.base_analyst import BaseAnalyst

class MarketIntelligenceAnalyst(BaseAnalyst):
    """
    Market intelligence analyst
    
    Analyzes communications and enriched contact data to extract market insights,
    competitive landscape, industry trends, and market positioning recommendations.
    """
    
    def __init__(self, user_id: int, anthropic_api_key: str = None):
        """
        Initialize market analyst
        
        Args:
            user_id: User ID for multi-tenant isolation
            anthropic_api_key: Optional API key for Claude Opus
        """
        super().__init__(user_id, anthropic_api_key)
        self.analyst_name = "market_intelligence"
        self.analyst_description = "Market trends and competitive landscape analyst"
        
        # Customize Claude parameters
        self.max_tokens = 4000
        self.temperature = 0.2  # Balanced for market analysis
    
    async def generate_intelligence(self, data: Dict) -> Dict:
        """
        Generate market intelligence from provided data
        
        Args:
            data: Dictionary containing:
                - contacts: List of enriched contact data with company info
                - emails: List of relevant email exchanges
                - (optional) market_data: Industry or market specific data
                - (optional) knowledge_tree: Knowledge tree data
                - (optional) specific_focus: Market area to focus on
                - (optional) competitors: List of specific competitors to analyze
                
        Returns:
            Dictionary with market insights and recommendations
        """
        # Validate critical inputs
        if not data.get("contacts") and not data.get("emails"):
            logger.error(
                "Missing required data for market analysis",
                user_id=self.user_id
            )
            return {"error": "Insufficient data for market analysis"}
            
        try:
            # Extract data elements
            contacts = data.get("contacts", [])
            emails = data.get("emails", [])
            market_data = data.get("market_data", [])
            knowledge_tree = data.get("knowledge_tree", {})
            focus_area = data.get("specific_focus", "industry trends")
            competitors = data.get("competitors", [])
            
            # Prepare specialized system prompt
            system_prompt = self._create_system_prompt(focus_area, competitors)
            
            # Prepare user prompt with data
            user_prompt = self._create_user_prompt(
                contacts=contacts,
                emails=emails,
                market_data=market_data,
                knowledge_tree=knowledge_tree,
                focus_area=focus_area,
                competitors=competitors
            )
            
            # Run Claude Opus analysis
            result_text = await self._run_claude_analysis(system_prompt, user_prompt)
            
            # Extract structured components
            structured_result = self._parse_claude_response(result_text)
            
            # Add metadata
            structured_result["focus_area"] = focus_area
            structured_result["analysis_timestamp"] = datetime.utcnow().isoformat()
            structured_result["data_points_analyzed"] = {
                "contacts": len(contacts),
                "emails": len(emails),
                "market_data_points": len(market_data),
                "competitors": competitors
            }
            
            return structured_result
            
        except Exception as e:
            logger.error(
                "Error generating market intelligence",
                error=str(e),
                user_id=self.user_id
            )
            return {"error": f"Market intelligence generation failed: {str(e)}"}
    
    def _create_system_prompt(self, focus_area: str, competitors: List[str]) -> str:
        """
        Create system prompt for Claude Opus
        
        Args:
            focus_area: Market area to focus on
            competitors: List of specific competitors to analyze
            
        Returns:
            System prompt string
        """
        competitor_context = ""
        if competitors:
            competitor_list = ", ".join(competitors)
            competitor_context = f" with particular attention to these competitors: {competitor_list}"
            
        return f"""You are an expert market intelligence analyst specializing in {focus_area}{competitor_context}.

Your task is to analyze contact data, communications, and market information to extract valuable market insights, competitive intelligence, and strategic positioning recommendations.

Focus on:
1. Identifying key market trends and industry dynamics
2. Analyzing competitive landscape and positioning
3. Recognizing market opportunities and threats
4. Understanding customer segments and needs
5. Evaluating market entry or expansion strategies

Structure your analysis with these sections:
- Market Overview: Brief summary of key market insights
- Industry Trends: Analysis of significant market movements and directions
- Competitive Landscape: Assessment of key players, their strengths and weaknesses
- Market Opportunities: Identified areas for growth or advantage
- Strategic Recommendations: Actionable market strategy recommendations

Be analytical, evidence-based, and focused on actionable market intelligence.
Base all insights on the provided data and make reasonable market inferences where appropriate.
Format your response as a combination of concise market analysis paragraphs and bullet points for readability.

Maintain absolute confidentiality and privacy in your analysis.
Do not include any information that could be considered sensitive or proprietary.
"""
    
    def _create_user_prompt(
        self, 
        contacts: List[Dict],
        emails: List[Dict],
        market_data: List[Dict],
        knowledge_tree: Dict,
        focus_area: str,
        competitors: List[str]
    ) -> str:
        """
        Create user prompt with data for analysis
        
        Args:
            contacts: List of enriched contact data
            emails: List of relevant email exchanges
            market_data: Industry or market specific data
            knowledge_tree: Knowledge graph data
            focus_area: Area to focus analysis on
            competitors: List of specific competitors to analyze
            
        Returns:
            Formatted user prompt
        """
        # Limit data volume to fit context window
        max_contacts = min(50, len(contacts))
        max_emails = min(30, len(emails))
        max_market = min(20, len(market_data))
        
        # Select most important data
        selected_contacts = contacts[:max_contacts]
        selected_emails = emails[:max_emails]
        selected_market = market_data[:max_market]
        
        # Format competitor focus
        competitor_focus = ""
        if competitors:
            competitor_list = ", ".join(competitors)
            competitor_focus = f"\nPay special attention to these competitors: {competitor_list}"
        
        # Format prompt
        prompt = f"""Please analyze the following data and provide market intelligence insights focused on {focus_area}.{competitor_focus}

## CONTACTS DATA
Here are {len(selected_contacts)} contacts with company information for market analysis:

```json
{self._format_json_for_prompt(selected_contacts)}
```

## EMAIL COMMUNICATIONS
Here are {len(selected_emails)} relevant email exchanges that provide context on market dynamics:

```json
{self._format_json_for_prompt(selected_emails)}
```
"""

        # Add market data if available
        if selected_market:
            prompt += f"""
## MARKET DATA
Here is specific market information for analysis:

```json
{self._format_json_for_prompt(selected_market)}
```
"""

        # Add knowledge tree if available
        if knowledge_tree and knowledge_tree.get("nodes"):
            prompt += f"""
## KNOWLEDGE NETWORK
Here is a knowledge graph showing market relationships:

```json
{self._format_json_for_prompt(knowledge_tree)}
```
"""

        # Add specific instructions
        prompt += f"""
Based on this data, please provide:

1. A market intelligence analysis highlighting key industry trends and dynamics
2. Competitive landscape assessment{" with focus on the specified competitors" if competitors else ""}
3. Identification of market opportunities and potential threats
4. Strategic recommendations for market positioning and advantage

Focus specifically on {focus_area} and organize your response according to the structure in your instructions.
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
            "market_overview": "",
            "industry_trends": [],
            "competitive_landscape": {},
            "market_opportunities": [],
            "strategic_recommendations": []
        }
        
        if not response_text:
            return result
            
        # Extract market overview
        if "Market Overview" in response_text:
            parts = response_text.split("Market Overview", 1)
            if len(parts) > 1:
                overview_section = parts[1].split("\n#", 1)[0].split("Industry Trends", 1)[0].strip()
                result["market_overview"] = overview_section
        
        # Extract industry trends
        if "Industry Trends" in response_text:
            parts = response_text.split("Industry Trends", 1)
            if len(parts) > 1:
                trends_text = parts[1].split("\n#", 1)[0].split("Competitive Landscape", 1)[0]
                # Extract bullet points
                trends = []
                for line in trends_text.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        trends.append(line.strip()[2:])
                if trends:
                    result["industry_trends"] = trends
                else:
                    result["industry_trends"] = [trends_text.strip()]
        
        # Extract competitive landscape
        # For this one, we'll try to structure it as a dictionary of competitors
        if "Competitive Landscape" in response_text:
            parts = response_text.split("Competitive Landscape", 1)
            if len(parts) > 1:
                landscape_text = parts[1].split("\n#", 1)[0].split("Market Opportunities", 1)[0]
                
                # Try to extract competitor-specific insights
                competitive_landscape = {}
                
                # Look for competitor names in bold or as subsections
                competitors = []
                for line in landscape_text.split("\n"):
                    # Check for markdown bold or subsection headers
                    if line.strip().startswith("**") and line.strip().endswith("**"):
                        competitor = line.strip().strip("**").strip(":")
                        competitors.append(competitor)
                    elif line.strip().startswith("### "):
                        competitor = line.strip()[4:].strip(":")
                        competitors.append(competitor)
                
                # If we found structured competitors, extract their data
                if competitors:
                    current_competitor = None
                    competitor_text = ""
                    
                    for line in landscape_text.split("\n"):
                        # Check for new competitor section
                        is_new_section = False
                        for competitor in competitors:
                            if line.strip().startswith(f"**{competitor}") or line.strip().startswith(f"### {competitor}"):
                                # Save previous competitor text if any
                                if current_competitor and competitor_text:
                                    competitive_landscape[current_competitor] = competitor_text.strip()
                                
                                # Start new competitor section
                                current_competitor = competitor
                                competitor_text = ""
                                is_new_section = True
                                break
                        
                        # If not a new section and we have a current competitor, add line to text
                        if not is_new_section and current_competitor:
                            competitor_text += line + "\n"
                    
                    # Save last competitor
                    if current_competitor and competitor_text:
                        competitive_landscape[current_competitor] = competitor_text.strip()
                
                # If we couldn't extract structured competitors, use whole text
                if not competitive_landscape:
                    result["competitive_landscape"] = {"overview": landscape_text.strip()}
                else:
                    result["competitive_landscape"] = competitive_landscape
        
        # Extract market opportunities
        if "Market Opportunities" in response_text:
            parts = response_text.split("Market Opportunities", 1)
            if len(parts) > 1:
                opps_text = parts[1].split("\n#", 1)[0].split("Strategic Recommendations", 1)[0]
                # Extract bullet points
                opps = []
                for line in opps_text.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        opps.append(line.strip()[2:])
                if opps:
                    result["market_opportunities"] = opps
                else:
                    result["market_opportunities"] = [opps_text.strip()]
        
        # Extract strategic recommendations
        if "Strategic Recommendations" in response_text:
            parts = response_text.split("Strategic Recommendations", 1)
            if len(parts) > 1:
                recs_text = parts[1].strip()
                # Extract bullet points
                recs = []
                for line in recs_text.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        recs.append(line.strip()[2:])
                if recs:
                    result["strategic_recommendations"] = recs
                else:
                    result["strategic_recommendations"] = [recs_text.strip()]
        
        # Add full text as fallback
        result["full_analysis"] = response_text
        
        return result
    
    def _validate_input(self, input_data: Dict) -> Optional[str]:
        """
        Validate input data for market analysis
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Error message if validation fails, None if valid
        """
        if not input_data:
            return "No input data provided"
            
        if not input_data.get("contacts") and not input_data.get("emails"):
            return "Missing required data: need either contacts or emails"
            
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
        
        if "contacts" in input_data:
            contacts = input_data["contacts"]
            summary["contacts_count"] = len(contacts)
            
            # Count contacts by company for market coverage
            companies = {}
            for contact in contacts:
                company = contact.get("company", "Unknown")
                companies[company] = companies.get(company, 0) + 1
                
            summary["company_distribution"] = dict(sorted(
                companies.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5])  # Top 5 companies
            
        if "emails" in input_data:
            emails = input_data["emails"]
            summary["emails_count"] = len(emails)
            
        if "market_data" in input_data:
            market_data = input_data["market_data"]
            summary["market_data_points"] = len(market_data)
            
        if "specific_focus" in input_data:
            summary["focus_area"] = input_data["specific_focus"]
            
        if "competitors" in input_data:
            summary["competitors"] = input_data["competitors"]
            
        return summary
