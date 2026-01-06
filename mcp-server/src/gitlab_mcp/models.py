"""
Data models for the UI Test Plan Generator.

These models define the structure for analyzing code changes
and generating detailed, UI-focused test plans.
"""

from typing import Dict, List, Optional, Any
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


class ComponentOverview(BaseModel):
    """Component overview and description."""
    description: str = Field(description="Detailed description of what the component does")
    key_features: List[str] = Field(default_factory=list, description="Key features or capabilities of the component")


class DataFlow(BaseModel):
    """Data flow representation."""
    description: str = Field(description="Description of the data flow")
    flow_diagram: str = Field(description="ASCII art or text representation of data flow")
    api_endpoints: List[str] = Field(default_factory=list, description="API endpoints or GraphQL queries used")
    data_sources: List[str] = Field(default_factory=list, description="Data sources (APIs, databases, etc.)")


class ColumnMapping(BaseModel):
    """Mapping of UI column to backend data."""
    column_name: str
    data_source: str
    backend_field: str
    transformation: Optional[str] = Field(None, description="Any transformation applied to the data")


class FilterTest(BaseModel):
    """Filter test case definition."""
    filter_name: str
    filter_type: str  # e.g., "search", "dropdown", "checkbox"
    graphql_variable: Optional[str] = None
    test_case: str
    expected_behavior: str


class PaginationTest(BaseModel):
    """Pagination test case definition."""
    test_case: str
    expected_behavior: str


class TestCase(BaseModel):
    """A detailed test case with table format."""
    category: str  # e.g., "Data Loading & Display", "Filtering", "Pagination"
    test_cases: List[Dict[str, str]] = Field(description="List of test cases with keys like 'Test Case', 'Expected Behavior', 'How to Verify'")


class TestingMethod(BaseModel):
    """A method for testing UI against backend data."""
    method_name: str  # e.g., "Browser DevTools Network Tab", "Postman/GraphQL Testing", "Playwright E2E Tests"
    description: str
    steps: List[str] = Field(default_factory=list)
    code_example: Optional[str] = None


class TestChecklistItem(BaseModel):
    """A single item in the test checklist."""
    category: str
    test: str
    priority: str  # "High", "Medium", "Low" or emoji equivalents


class EnhancedUITestPlan(BaseModel):
    """Enhanced UI test plan with detailed structure."""
    merge_request_title: str
    affected_ui_pages: List[str]
    
    # Component details
    component_overview: Optional[ComponentOverview] = None
    data_flow: Optional[DataFlow] = None
    
    # Test details
    test_cases: List[TestCase] = Field(default_factory=list)
    column_mappings: List[ColumnMapping] = Field(default_factory=list)
    filter_tests: List[FilterTest] = Field(default_factory=list)
    pagination_tests: List[PaginationTest] = Field(default_factory=list)
    
    # Testing methods
    testing_methods: List[TestingMethod] = Field(default_factory=list)
    
    # Checklist
    test_checklist: List[TestChecklistItem] = Field(default_factory=list)
    
    # Traditional scenarios (for backward compatibility)
    test_scenarios: List[UITestScenario] = Field(default_factory=list)
    
    # Additional metadata
    overall_summary: Optional[str] = None
    ai_insights: Optional[Dict[str, Any]] = None


class UITestPlan(BaseModel):
    """The final UI test plan generated for a merge request."""
    merge_request_title: str
    affected_ui_pages: List[str] = Field(description="A list of UI pages or components likely affected by the changes.")
    overall_summary: str = Field(description="A high-level summary of the changes and the testing approach.")
    test_scenarios: List[UITestScenario] 