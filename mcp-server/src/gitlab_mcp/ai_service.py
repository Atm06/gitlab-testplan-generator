"""
Local AI Service for code analysis and test plan generation.

This module provides AI capabilities using locally hosted models via Ollama,
ensuring that no code data leaves your machine.
"""

import json
import os
import asyncio
from typing import List, Dict, Any, Optional
import aiohttp
from pydantic import BaseModel

from .models import ChangeAnalysis, UITestScenario, TestStep


class AIConfig(BaseModel):
    """Configuration for AI service."""
    ollama_host: str = "http://localhost:11434"
    model_name: str = "qwen2.5-coder:1.5b"
    max_tokens: int = 2048
    temperature: float = 0.3


class LocalAIService:
    """
    Local AI service using Ollama for code analysis and test plan generation.
    
    This service keeps all your GitLab code data private by processing everything
    locally using Ollama models.
    """
    
    def __init__(self, config: Optional[AIConfig] = None):
        self.config = config or AIConfig()
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _call_ollama(self, prompt: str, system_prompt: str = "") -> str:
        """
        Make a request to the local Ollama API.
        """
        if not self.session:
            raise RuntimeError("AIService must be used as an async context manager")
        
        payload = {
            "model": self.config.model_name,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        }
        
        try:
            async with self.session.post(
                f"{self.config.ollama_host}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error: {response.status} - {error_text}")
                
                result = await response.json()
                return result.get("response", "").strip()
        
        except aiohttp.ClientError as e:
            raise Exception(f"Failed to connect to Ollama: {e}. Make sure Ollama is running.")
    
    async def analyze_code_changes(self, changes: List[ChangeAnalysis], mr_title: str) -> Dict[str, Any]:
        """
        Analyze code changes using local AI to understand the impact and affected areas.
        """
        system_prompt = """You are a senior software engineer analyzing code changes for a GitLab merge request.
Your task is to understand the impact of the changes and identify which UI components or pages might be affected.

Focus on:
1. What functionality is being changed/added/removed
2. Which UI components or pages will be impacted
3. What user workflows might be affected
4. Potential edge cases or areas of concern

Respond with a JSON object containing:
{
    "summary": "Brief summary of changes",
    "affected_areas": ["list", "of", "affected", "ui", "areas"],
    "user_impact": "Description of how users will be affected",
    "risk_areas": ["potential", "risk", "areas"]
}"""
        
        # Prepare the changes summary for the AI
        changes_summary = f"Merge Request: {mr_title}\n\nCode Changes:\n"
        for change in changes[:10]:  # Limit to first 10 files to avoid token limits
            changes_summary += f"\nFile: {change.file_path}\n"
            changes_summary += f"Change Type: {change.change_type}\n"
            if len(change.raw_diff) < 2000:  # Include diff if not too long
                changes_summary += f"Diff:\n{change.raw_diff}\n"
            changes_summary += "---\n"
        
        prompt = f"Analyze these code changes:\n\n{changes_summary}"
        
        response = await self._call_ollama(prompt, system_prompt)
        
        try:
            # Try to parse JSON response
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback if AI doesn't return valid JSON
            return {
                "summary": response[:200] + "..." if len(response) > 200 else response,
                "affected_areas": [change.file_path for change in changes[:5]],
                "user_impact": "Manual testing required to verify functionality",
                "risk_areas": ["UI functionality", "User experience"]
            }
    
    async def generate_ui_test_scenarios(
        self, 
        changes: List[ChangeAnalysis], 
        affected_pages: List[str], 
        mr_title: str,
        analysis: Dict[str, Any]
    ) -> List[UITestScenario]:
        """
        Generate comprehensive UI test scenarios using local AI.
        """
        system_prompt = """You are a QA engineer creating detailed UI test scenarios for a web application.
Your task is to create comprehensive, actionable test scenarios that a manual tester can follow.

For each scenario, provide:
1. A clear, descriptive title
2. Step-by-step testing instructions
3. Expected results for each step
4. Risk level (low, medium, high)

Focus on:
- Core functionality that was changed
- User workflows that might be affected
- Edge cases and error conditions
- UI consistency and usability

Respond with a JSON array of test scenarios:
[
    {
        "title": "Test scenario title",
        "steps": [
            {
                "action": "What the tester should do",
                "expected_result": "What should happen"
            }
        ],
        "risk_level": "low|medium|high"
    }
]"""
        
        prompt = f"""Generate UI test scenarios for this merge request:

Title: {mr_title}
Summary: {analysis.get('summary', 'Code changes detected')}
Affected UI Areas: {', '.join(affected_pages)}
User Impact: {analysis.get('user_impact', 'Functionality changes')}
Risk Areas: {', '.join(analysis.get('risk_areas', []))}

Files Changed:
{chr(10).join([f"- {change.file_path} ({change.change_type})" for change in changes[:10]])}

Create 3-5 focused test scenarios that cover the main functionality and potential edge cases."""
        
        response = await self._call_ollama(prompt, system_prompt)
        
        try:
            scenarios_data = json.loads(response)
            scenarios = []
            
            for scenario_data in scenarios_data:
                steps = []
                for step_data in scenario_data.get('steps', []):
                    steps.append(TestStep(
                        action=step_data.get('action', ''),
                        expected_result=step_data.get('expected_result', '')
                    ))
                
                scenarios.append(UITestScenario(
                    title=scenario_data.get('title', 'Test Scenario'),
                    steps=steps,
                    risk_level=scenario_data.get('risk_level', 'medium')
                ))
            
            return scenarios
        
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback scenarios if AI response is malformed
            return self._generate_fallback_scenarios(affected_pages, analysis)
    
    def _generate_fallback_scenarios(self, affected_pages: List[str], analysis: Dict[str, Any]) -> List[UITestScenario]:
        """Generate basic fallback scenarios if AI parsing fails."""
        scenarios = []
        
        # Basic functionality test
        scenarios.append(UITestScenario(
            title="Verify core functionality on affected pages",
            steps=[
                TestStep(
                    action=f"Navigate to the affected area: {affected_pages[0] if affected_pages else 'main page'}",
                    expected_result="Page loads successfully without errors"
                ),
                TestStep(
                    action="Interact with the main functionality that was changed",
                    expected_result="Feature works as expected according to the requirements"
                ),
                TestStep(
                    action="Check for any UI inconsistencies or broken layouts",
                    expected_result="UI displays correctly and consistently"
                )
            ],
            risk_level="high"
        ))
        
        # Error handling test
        scenarios.append(UITestScenario(
            title="Test error handling and edge cases",
            steps=[
                TestStep(
                    action="Try to trigger error conditions in the changed functionality",
                    expected_result="Appropriate error messages are displayed to the user"
                ),
                TestStep(
                    action="Test with edge case inputs (empty, special characters, etc.)",
                    expected_result="System handles edge cases gracefully"
                )
            ],
            risk_level="medium"
        ))
        
        return scenarios
    
    async def check_ollama_status(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            if not self.session:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.config.ollama_host}/api/version") as response:
                        return response.status == 200
            else:
                async with self.session.get(f"{self.config.ollama_host}/api/version") as response:
                    return response.status == 200
        except:
            return False


def get_ai_config() -> AIConfig:
    """Get AI configuration from environment variables."""
    return AIConfig(
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        model_name=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:1.5b"),
        max_tokens=int(os.getenv("AI_MAX_TOKENS", "2048")),
        temperature=float(os.getenv("AI_TEMPERATURE", "0.3"))
    )