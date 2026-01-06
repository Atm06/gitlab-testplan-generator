"""
UI Test Plan Generation Module

This module takes code change analysis and generates a detailed,
UI-focused test plan with concrete scenarios and steps using local AI.
"""

import os
from typing import List, Dict, Any

from .models import (
    ChangeAnalysis, UITestPlan, UITestScenario, TestStep,
    EnhancedUITestPlan, ComponentOverview, DataFlow, ColumnMapping,
    FilterTest, PaginationTest, TestCase, TestingMethod, TestChecklistItem
)
from .ai_service import LocalAIService, get_ai_config


class UITestPlanGenerator:
    """Generates a UI-focused test plan from code changes."""

    async def generate_enhanced_plan(self, changes: List[ChangeAnalysis], affected_pages: List[str], mr_title: str, analysis: Dict[str, Any] = None) -> EnhancedUITestPlan:
        """
        Generates an enhanced, detailed UI test plan using local AI.
        
        This method uses local AI to create a comprehensive test plan with:
        - Component overview
        - Data flow diagrams
        - Column mappings
        - Filter and pagination tests
        - Testing methods
        - Test checklist
        """
        # Default analysis if not provided
        if analysis is None:
            analysis = {
                "summary": f"Changes detected in {len(changes)} files",
                "user_impact": "Functionality may be affected",
                "risk_areas": ["UI functionality"]
            }
        
        config = get_ai_config()
        
        enhanced_data = None
        scenarios = []
        
        try:
            async with LocalAIService(config) as ai_service:
                # Check if Ollama is running
                if not await ai_service.check_ollama_status():
                    print("⚠️  Ollama not available. Using fallback test plan.")
                    enhanced_data = self._generate_fallback_enhanced_data(affected_pages, analysis)
                    scenarios = self._generate_placeholder_scenarios(affected_pages, changes)
                else:
                    print("🤖 Generating enhanced AI-powered test plan...")
                    enhanced_data = await ai_service.generate_enhanced_test_plan(
                        changes, affected_pages, mr_title, analysis
                    )
                    print("✅ Generated enhanced test plan structure")
                    
                    # Also generate traditional scenarios for backward compatibility
                    print("🤖 Generating AI-powered test scenarios...")
                    scenarios = await ai_service.generate_ui_test_scenarios(
                        changes, affected_pages, mr_title, analysis
                    )
                    print(f"✅ Generated {len(scenarios)} AI test scenarios")
        
        except Exception as e:
            print(f"⚠️  AI test generation failed: {e}. Using fallback plan.")
            enhanced_data = self._generate_fallback_enhanced_data(affected_pages, analysis)
            scenarios = self._generate_placeholder_scenarios(affected_pages, changes)
        
        # Build the enhanced test plan
        component_overview = None
        if enhanced_data.get("component_overview"):
            co_data = enhanced_data["component_overview"]
            component_overview = ComponentOverview(
                description=co_data.get("description", ""),
                key_features=co_data.get("key_features", [])
            )
        
        data_flow = None
        if enhanced_data.get("data_flow"):
            df_data = enhanced_data["data_flow"]
            data_flow = DataFlow(
                description=df_data.get("description", ""),
                flow_diagram=df_data.get("flow_diagram", ""),
                api_endpoints=df_data.get("api_endpoints", []),
                data_sources=df_data.get("data_sources", [])
            )
        
        # Parse test cases
        test_cases = []
        for tc_data in enhanced_data.get("test_cases", []):
            test_cases.append(TestCase(
                category=tc_data.get("category", ""),
                test_cases=tc_data.get("test_cases", [])
            ))
        
        # Parse column mappings
        column_mappings = []
        for cm_data in enhanced_data.get("column_mappings", []):
            column_mappings.append(ColumnMapping(
                column_name=cm_data.get("column_name", ""),
                data_source=cm_data.get("data_source", ""),
                backend_field=cm_data.get("backend_field", ""),
                transformation=cm_data.get("transformation")
            ))
        
        # Parse filter tests
        filter_tests = []
        for ft_data in enhanced_data.get("filter_tests", []):
            filter_tests.append(FilterTest(
                filter_name=ft_data.get("filter_name", ""),
                filter_type=ft_data.get("filter_type", ""),
                graphql_variable=ft_data.get("graphql_variable"),
                test_case=ft_data.get("test_case", ""),
                expected_behavior=ft_data.get("expected_behavior", "")
            ))
        
        # Parse pagination tests
        pagination_tests = []
        for pt_data in enhanced_data.get("pagination_tests", []):
            pagination_tests.append(PaginationTest(
                test_case=pt_data.get("test_case", ""),
                expected_behavior=pt_data.get("expected_behavior", "")
            ))
        
        # Parse testing methods
        testing_methods = []
        for tm_data in enhanced_data.get("testing_methods", []):
            testing_methods.append(TestingMethod(
                method_name=tm_data.get("method_name", ""),
                description=tm_data.get("description", ""),
                steps=tm_data.get("steps", []),
                code_example=tm_data.get("code_example")
            ))
        
        # Parse test checklist
        test_checklist = []
        for tc_data in enhanced_data.get("test_checklist", []):
            test_checklist.append(TestChecklistItem(
                category=tc_data.get("category", ""),
                test=tc_data.get("test", ""),
                priority=tc_data.get("priority", "Medium")
            ))
        
        return EnhancedUITestPlan(
            merge_request_title=mr_title,
            affected_ui_pages=affected_pages,
            component_overview=component_overview,
            data_flow=data_flow,
            test_cases=test_cases,
            column_mappings=column_mappings,
            filter_tests=filter_tests,
            pagination_tests=pagination_tests,
            testing_methods=testing_methods,
            test_checklist=test_checklist,
            test_scenarios=scenarios,
            overall_summary=self._create_summary(changes, affected_pages),
            ai_insights=analysis
        )
    
    def _generate_fallback_enhanced_data(self, affected_pages: List[str], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback enhanced data structure."""
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

    async def generate_ai_plan(self, changes: List[ChangeAnalysis], affected_pages: List[str], mr_title: str, analysis: Dict[str, Any] = None) -> UITestPlan:
        """
        Generates the complete UI test plan using local AI.
        
        This method uses local AI to create intelligent, comprehensive test scenarios
        based on code changes and impact analysis.
        """
        summary = self._create_summary(changes, affected_pages)
        
        # Default analysis if not provided
        if analysis is None:
            analysis = {
                "summary": f"Changes detected in {len(changes)} files",
                "user_impact": "Functionality may be affected",
                "risk_areas": ["UI functionality"]
            }
        
        config = get_ai_config()
        
        try:
            async with LocalAIService(config) as ai_service:
                # Check if Ollama is running
                if not await ai_service.check_ollama_status():
                    print("⚠️  Ollama not available. Using fallback test scenarios.")
                    scenarios = self._generate_placeholder_scenarios(affected_pages, changes)
                else:
                    print("🤖 Generating AI-powered test scenarios...")
                    scenarios = await ai_service.generate_ui_test_scenarios(
                        changes, affected_pages, mr_title, analysis
                    )
                    print(f"✅ Generated {len(scenarios)} AI test scenarios")
        
        except Exception as e:
            print(f"⚠️  AI test generation failed: {e}. Using fallback scenarios.")
            scenarios = self._generate_placeholder_scenarios(affected_pages, changes)
        
        return UITestPlan(
            merge_request_title=mr_title,
            affected_ui_pages=affected_pages,
            overall_summary=summary,
            test_scenarios=scenarios,
        )



    def _create_summary(self, changes: List[ChangeAnalysis], affected_pages: List[str]) -> str:
        """Creates a high-level summary of the changes for the test plan."""
        num_files_changed = len(changes)
        
        summary = (
            f"This test plan covers changes to {num_files_changed} file(s), "
            f"primarily impacting the following UI areas: {', '.join(affected_pages)}. "
            "The focus is on end-to-end user scenarios to ensure the UI remains functional, "
            "intuitive, and visually correct."
        )
        return summary

    def _create_llm_prompt(self, changes: List[ChangeAnalysis], affected_pages: List[str], mr_title: str) -> str:
        """
        Creates a detailed prompt to be sent to an LLM to generate UI test scenarios.
        """
        changed_files_summary = "\n".join(f"- `{change.file_path}` ({change.change_type})" for change in changes)

        prompt = f"""
        As a senior QA engineer, your task is to create a detailed UI test plan for a merge request.

        **Merge Request Title:** "{mr_title}"

        **Summary of Changes:**
        The code changes affect {len(changes)} files, impacting these inferred UI pages/components: {', '.join(affected_pages)}.
        
        **Changed Files:**
        {changed_files_summary}

        **Your Task:**
        Based on the information above, create a list of detailed test scenarios. For each scenario:
        1.  Provide a clear, user-centric title.
        2.  List a sequence of simple, specific user actions (steps).
        3.  For each action, describe the expected result on the UI.
        4.  Estimate a risk level (low, medium, high) if the scenario fails.
        5.  Focus on user-facing tests. Do not include unit, integration, or API tests.
        6.  Include at least one positive "happy path" scenario and one negative or edge-case scenario.

        Provide the output as a JSON object that strictly follows this Pydantic model:

        """
        return prompt.strip()
    
    def _generate_placeholder_scenarios(self, affected_pages: List[str], changes: List[ChangeAnalysis]) -> List[UITestScenario]:
        """
        Generates example scenarios. In a real implementation, this would be
        the output from an LLM call.
        """
        scenarios = []
        
        # Happy Path Scenario
        if affected_pages:
            scenarios.append(UITestScenario(
                title=f"Happy Path: Verify core functionality on '{affected_pages[0]}' page",
                steps=[
                    TestStep(action=f"Navigate to the '{affected_pages[0]}' page.", expected_result="The page loads without errors and the main content is visible."),
                    TestStep(action="Interact with the primary element related to the change.", expected_result="The element behaves as expected according to the new functionality."),
                    TestStep(action="Perform a save or submit action.", expected_result="A success message appears and the UI reflects the updated state."),
                ],
                risk_level="high"
            ))

        # Negative/Edge Case Scenario
        scenarios.append(UITestScenario(
            title="Edge Case: Input validation and error handling",
            steps=[
                TestStep(action="Navigate to the relevant page and find the input form.", expected_result="The form is present with all fields."),
                TestStep(action="Enter invalid or empty data into the fields.", expected_result="Validation errors appear next to the respective fields."),
                TestStep(action="Attempt to submit the form with invalid data.", expected_result="Submission is blocked and a summary error message is displayed."),
            ],
            risk_level="medium"
        ))
        
        # A placeholder to show where the real LLM output would go
        scenarios.append(UITestScenario(
            title="[Generated by LLM] Scenario Placeholder",
            steps=[
                TestStep(action="This content would be generated by a call to an LLM using the generated prompt.", expected_result="The response would be parsed and structured into these models."),
            ],
            risk_level="medium"
        ))

        return scenarios 