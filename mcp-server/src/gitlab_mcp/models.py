"""
Data models for the UI Test Plan Generator.

These models define the structure for analyzing code changes
and generating detailed, UI-focused test plans.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ChangeAnalysis(BaseModel):
    """Minimal analysis of code changes needed for test planning."""
    file_path: str
    change_type: str  # added, modified, deleted
    raw_diff: str


class TestStep(BaseModel):
    """A single, actionable step in a test case."""
    action: str
    expected_result: str


class UITestScenario(BaseModel):
    """A complete user scenario to be tested on the UI."""
    title: str = Field(description="A descriptive title for the test scenario, e.g., 'User successfully edits their profile'.")
    steps: List[TestStep] = Field(description="A sequence of steps to execute the test.")
    risk_level: str = Field(description="Estimated risk (low, medium, high) associated with this scenario failing.")


class UITestPlan(BaseModel):
    """The final UI test plan generated for a merge request."""
    merge_request_title: str
    affected_ui_pages: List[str] = Field(description="A list of UI pages or components likely affected by the changes.")
    overall_summary: str = Field(description="A high-level summary of the changes and the testing approach.")
    test_scenarios: List[UITestScenario] 