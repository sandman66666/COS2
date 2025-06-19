# intelligence/analysts/base_analyst.py
"""
Base Intelligence Analyst
=====================
Abstract base class for all intelligence analysts powered by Claude Opus.
Ensures consistent interface and multi-tenant isolation.
"""

import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

import anthropic
from utils.logging import structured_logger as logger
from storage.storage_manager import get_storage_manager
from config import get_settings

class BaseAnalyst(ABC):
    """
    Base class for all intelligence analysts
    
    Provides common functionality for prompt construction,
    LLM interaction, and multi-tenant isolation.
    """
    
    def __init__(self, user_id: int, anthropic_api_key: str = None):
        """
        Initialize base analyst
        
        Args:
            user_id: User ID for multi-tenant isolation
            anthropic_api_key: Optional API key for Claude Opus
        """
        self.user_id = user_id
        self.settings = get_settings()
        self.api_key = anthropic_api_key or self.settings.ANTHROPIC_API_KEY
        self.model = "claude-3-opus-20240229"
        self.client = None
        self.storage_manager = None
        
        # Required to be set by subclasses
        self.analyst_name = "base_analyst"
        self.analyst_description = "Generic intelligence analyst"
        self.max_tokens = 4000
        self.temperature = 0.3
    
    async def initialize(self) -> bool:
        """
        Initialize resources and connections
        
        Returns:
            True if initialization successful
        """
        try:
            # Initialize Claude Opus client
            self.client = anthropic.Anthropic(api_key=self.api_key)
            
            # Get storage manager for result persistence
            self.storage_manager = await get_storage_manager()
            
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to initialize {self.analyst_name}",
                error=str(e),
                user_id=self.user_id
            )
            return False
    
    @abstractmethod
    async def generate_intelligence(self, data: Dict) -> Dict:
        """
        Generate intelligence analysis from provided data
        Must be implemented by subclasses
        
        Args:
            data: Dictionary with relevant data for analysis
            
        Returns:
            Dictionary with intelligence analysis results
        """
        pass
    
    async def analyze(self, input_data: Dict) -> Dict:
        """
        Public method to run analysis with standardized formatting
        
        Args:
            input_data: Dictionary of input data
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Initialize if needed
            if not self.client or not self.storage_manager:
                success = await self.initialize()
                if not success:
                    return self._create_error_response("Failed to initialize analyst")
            
            # Validate input data
            validation_error = self._validate_input(input_data)
            if validation_error:
                return self._create_error_response(validation_error)
            
            # Generate analysis
            start_time = datetime.utcnow()
            analysis_result = await self.generate_intelligence(input_data)
            end_time = datetime.utcnow()
            
            if not analysis_result:
                return self._create_error_response("No analysis results generated")
            
            # Format the result
            result = {
                "analyst_name": self.analyst_name,
                "analyst_description": self.analyst_description,
                "user_id": self.user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "execution_time_ms": int((end_time - start_time).total_seconds() * 1000),
                "results": analysis_result,
                "status": "success",
                "input_data_summary": self._summarize_input(input_data)
            }
            
            # Store the result
            await self._store_analysis_result(result)
            
            return result
            
        except Exception as e:
            logger.error(
                f"Error in {self.analyst_name}",
                error=str(e),
                user_id=self.user_id
            )
            return self._create_error_response(str(e))
    
    async def _run_claude_analysis(self, system_prompt: str, user_prompt: str) -> str:
        """
        Run Claude Opus analysis with system and user prompts
        
        Args:
            system_prompt: System prompt defining the analysis context
            user_prompt: User prompt with specific instructions and data
            
        Returns:
            Claude's response text
        """
        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            if not response or not response.content:
                logger.error(
                    f"Empty response from Claude Opus",
                    user_id=self.user_id,
                    analyst=self.analyst_name
                )
                return ""
                
            # Extract text content
            content = response.content[0].text
            return content
            
        except Exception as e:
            logger.error(
                f"Error running Claude Opus analysis",
                error=str(e),
                user_id=self.user_id,
                analyst=self.analyst_name
            )
            return ""
    
    async def _store_analysis_result(self, result: Dict) -> None:
        """
        Store analysis result in database
        
        Args:
            result: Analysis result dictionary
        """
        try:
            await self.storage_manager.store_intelligence_result(
                self.user_id,
                self.analyst_name,
                result
            )
        except Exception as e:
            logger.error(
                f"Failed to store analysis result",
                error=str(e),
                user_id=self.user_id,
                analyst=self.analyst_name
            )
    
    def _create_error_response(self, error_message: str) -> Dict:
        """
        Create standardized error response
        
        Args:
            error_message: Error description
            
        Returns:
            Error response dictionary
        """
        return {
            "analyst_name": self.analyst_name,
            "analyst_description": self.analyst_description,
            "user_id": self.user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": error_message
        }
    
    def _validate_input(self, input_data: Dict) -> Optional[str]:
        """
        Validate input data for analysis
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Error message if validation fails, None if valid
        """
        # Basic validation - subclasses should override with specific validation
        if not input_data:
            return "No input data provided"
        return None
    
    def _summarize_input(self, input_data: Dict) -> Dict:
        """
        Create summary of input data for recording
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Dictionary with input data summary
        """
        # Default implementation - subclasses should provide better summaries
        summary = {}
        
        for key, value in input_data.items():
            if isinstance(value, dict):
                summary[key] = "Dict with {} keys".format(len(value))
            elif isinstance(value, list):
                summary[key] = "List with {} items".format(len(value))
            elif isinstance(value, str) and len(value) > 100:
                summary[key] = "String of length {}".format(len(value))
            else:
                summary[key] = str(value)
                
        return summary
    
    def _format_json_for_prompt(self, data: Any) -> str:
        """
        Format data as pretty JSON for inclusion in prompt
        
        Args:
            data: Data to format
            
        Returns:
            Formatted JSON string
        """
        try:
            return json.dumps(data, indent=2)
        except Exception:
            return str(data)
