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

from .models import (
    ChangeAnalysis, UITestScenario, TestStep, EnhancedUITestPlan,
    ComponentOverview, DataFlow, ColumnMapping, FilterTest, PaginationTest,
    TestCase, TestingMethod, TestChecklistItem
)


class AIConfig(BaseModel):
    """Configuration for AI service."""
    ollama_host: str = "http://localhost:11434"
    model_name: str = "qwen2.5-coder:1.5b"
    max_tokens: int = 8192  # Increased from 8192 to allow for comprehensive responses
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
5. Be as detailed as possible. For each section, provide at least 3-5 sentences or bullet points. If possible, include examples.

Respond with a JSON object containing:
{
    "summary": "📝 Detailed summary of changes (at least 3 sentences)",
    "affected_areas": ["🧩 List all affected UI areas, be specific"],
    "user_impact": "👤 Describe in detail how users will be affected, including edge cases",
    "risk_areas": ["⚠️ List potential risk areas, explain why each is a risk"],
    "ai_insights": "🤖 Provide additional AI-driven insights, such as hidden risks, suggestions for extra testing, code quality observations, or architectural concerns. Be as thorough as possible.",
    "thinking_process": "🧠 Step-by-step reasoning or approach you used to analyze the changes. Explain your thought process, what patterns you noticed, and how you arrived at your conclusions."
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
            # Try to parse JSON response, handling markdown code blocks
            cleaned_response = self._clean_json_response(response)
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            # Fallback if AI doesn't return valid JSON
            print(f"⚠️  JSON parsing failed: {e}")
            print(f"Raw response: {response[:500]}...")
            return {
                "summary": response[:200] + "..." if len(response) > 200 else response,
                "affected_areas": [change.file_path for change in changes[:5]],
                "user_impact": "Manual testing required to verify functionality",
                "risk_areas": ["UI functionality", "User experience"],
                "ai_insights": "No additional insights generated. Please review the code manually for hidden risks or architectural concerns.",
                "thinking_process": "🧠 Unable to parse AI response. Manual analysis recommended."
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
Format your response for maximum readability:
- Use appropriate emojis for each section (e.g., 📝 for summary, 🧩 for affected areas, 👤 for user impact, ⚠️ for risks, 🤖 for AI insights).

- Make the report visually appealing and easy to scan.
For each scenario, provide:
1. A clear, descriptive title
2. At least 5 step-by-step testing instructions
3. Expected results for each step, with specific examples
4. Risk level (low, medium, high) and a short explanation of why it's a risk
5. AI insights: Provide additional AI-driven insights, such as hidden risks, suggestions for extra testing, code quality observations, or architectural concerns. Be as thorough as possible.

Focus on:
- Core functionality that was changed
- User workflows that might be affected
- Edge cases and error conditions
- UI consistency and usability

Respond with a JSON array of 5-7 test scenarios, each as detailed as possible:
[
    {
        "title": "Test scenario title",
        "steps": [
            {
                "action": "What the tester should do",
                "expected_result": "What should happen"
            }
        ],
        "risk_level": "low|medium|high",
        "ai_insights": "Provide additional AI-driven insights, such as hidden risks, suggestions for extra testing, code quality observations, or architectural concerns. Be as thorough as possible."
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
            # Clean and parse JSON response
            cleaned_response = self._clean_json_response(response)
            scenarios_data = json.loads(cleaned_response)
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

    async def generate_enhanced_test_plan(
        self,
        changes: List[ChangeAnalysis],
        affected_pages: List[str],
        mr_title: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate an enhanced, detailed test plan with component overview, data flow, 
        column mappings, filtering, pagination, and testing methods.
        """
        system_prompt = """You are a senior QA engineer creating a comprehensive, detailed UI test plan for a web application component.

Your task is to analyze the code changes and create a structured test plan that includes:

1. **Component Overview**: A clear description of what the component does, its purpose, and key features
2. **Key Data Flow**: Visual representation (ASCII art) showing how data flows from API/backend to UI components
3. **What to Test**: Organized test cases in table format covering:
   - Data Loading & Display
   - Table Columns Data Mapping (if applicable)
   - Filtering (if applicable)
   - Pagination (if applicable)
   - Error States
   - User Interactions
4. **How to Test UI Against Backend Data**: Multiple testing methods:
   - Browser DevTools Network Tab
   - Postman/GraphQL Testing (with example queries)
   - Playwright E2E Tests (with code examples)
5. **Test Checklist**: Organized by category with priorities (High/Medium/Low or emoji equivalents)

Analyze the code changes carefully to identify:
- API endpoints or GraphQL queries used
- Data structures and field mappings
- UI components and their data sources
- Filtering mechanisms
- Pagination logic
- Error handling

Respond with a comprehensive JSON object following this structure:
{
    "component_overview": {
        "description": "Detailed description of what the component does",
        "key_features": ["feature1", "feature2"]
    },
    "data_flow": {
        "description": "Description of data flow",
        "flow_diagram": "ASCII art representation showing data flow from API to UI",
        "api_endpoints": ["endpoint1", "endpoint2"],
        "data_sources": ["source1", "source2"]
    },
    "test_cases": [
        {
            "category": "Data Loading & Display",
            "test_cases": [
                {
                    "Test Case": "Initial load",
                    "Expected Behavior": "Shows skeleton loaders while loading",
                    "How to Verify": "Check for skeleton elements"
                }
            ]
        }
    ],
    "column_mappings": [
        {
            "column_name": "Tag",
            "data_source": "image.repositories[].tags[].name",
            "backend_field": "tags[].name",
            "transformation": "Filter by matching repository"
        }
    ],
    "filter_tests": [
        {
            "filter_name": "Tag Search",
            "filter_type": "search",
            "graphql_variable": "tags_elemMatch.name.iregex",
            "test_case": "Type 'latest' → verify only matching tags shown",
            "expected_behavior": "Filtered results contain 'latest'"
        }
    ],
    "pagination_tests": [
        {
            "test_case": "Page navigation",
            "expected_behavior": "Clicking page 2 updates page variable to 1 (0-indexed)"
        }
    ],
    "testing_methods": [
        {
            "method_name": "Browser DevTools Network Tab",
            "description": "How to use browser DevTools to verify UI matches backend",
            "steps": ["step1", "step2"],
            "code_example": "Optional code example if applicable"
        }
    ],
    "test_checklist": [
        {
            "category": "Data Display",
            "test": "Verify all columns populated correctly",
            "priority": "High"
        }
    ]
}

Be thorough and detailed. Extract as much information as possible from the code changes."""
        
        # Prepare detailed code context
        code_context = f"Merge Request: {mr_title}\n\n"
        code_context += f"Summary: {analysis.get('summary', 'Code changes detected')}\n"
        code_context += f"Affected UI Areas: {', '.join(affected_pages)}\n\n"
        code_context += "Code Changes:\n"
        
        for change in changes[:15]:  # Include more files for better context
            code_context += f"\n--- File: {change.file_path} ({change.change_type}) ---\n"
            # Include full diff for better analysis
            if len(change.raw_diff) < 5000:  # Include if not too long
                code_context += f"{change.raw_diff}\n"
            else:
                code_context += f"{change.raw_diff[:5000]}...\n[truncated]\n"
        
        prompt = f"""Analyze these code changes and generate a comprehensive test plan:

{code_context}

Generate a detailed test plan following the structure specified in the system prompt."""
        
        response = await self._call_ollama(prompt, system_prompt)
        
        try:
            cleaned_response = self._clean_json_response(response)
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            print(f"⚠️  Enhanced test plan JSON parsing failed: {e}")
            print(f"Raw response: {response[:500]}...")
            # Return a basic structure
            return self._generate_fallback_enhanced_plan(affected_pages, analysis)
    
    def _generate_fallback_enhanced_plan(self, affected_pages: List[str], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a basic enhanced plan structure if AI parsing fails."""
        return {
            "component_overview": {
                "description": f"Component affected by changes in {', '.join(affected_pages)}",
                "key_features": ["Core functionality", "User interactions"]
            },
            "data_flow": {
                "description": "Data flows from backend API to UI components",
                "flow_diagram": "API → Component → UI Display",
                "api_endpoints": [],
                "data_sources": ["Backend API"]
            },
            "test_cases": [
                {
                    "category": "Data Loading & Display",
                    "test_cases": [
                        {
                            "Test Case": "Initial load",
                            "Expected Behavior": "Page loads without errors",
                            "How to Verify": "Check for error messages or broken UI"
                        }
                    ]
                }
            ],
            "column_mappings": [],
            "filter_tests": [],
            "pagination_tests": [],
            "testing_methods": [
                {
                    "method_name": "Manual Testing",
                    "description": "Navigate to the affected pages and verify functionality",
                    "steps": [
                        f"Navigate to {affected_pages[0] if affected_pages else 'the affected page'}",
                        "Verify the page loads correctly",
                        "Test the main functionality"
                    ]
                }
            ],
            "test_checklist": [
                {
                    "category": "Core Functionality",
                    "test": "Verify page loads and displays correctly",
                    "priority": "High"
                }
            ]
        }

    def _clean_json_response(self, response: str) -> str:
        """
        Clean the AI response by removing markdown code block markers and other formatting.
        
        Args:
            response: Raw response from the AI model
            
        Returns:
            Cleaned JSON string ready for parsing
        """
        # Remove leading/trailing whitespace
        cleaned = response.strip()
        
        # Remove markdown code block markers
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]  # Remove ```json
        elif cleaned.startswith('```'):
            cleaned = cleaned[3:]   # Remove ```
            
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]  # Remove closing ```
            
        # Remove any remaining leading/trailing whitespace
        cleaned = cleaned.strip()
        
        return cleaned


def get_ai_config() -> AIConfig:
    """Get AI configuration from environment variables."""
    return AIConfig(
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        model_name=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:1.5b"),
        max_tokens=int(os.getenv("AI_MAX_TOKENS", "8192")),
        temperature=float(os.getenv("AI_TEMPERATURE", "0.3"))
    )