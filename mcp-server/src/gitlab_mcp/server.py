#!/usr/bin/env python3
"""
GitLab UI Test Plan Generator MCP Server

This server generates detailed UI test plans from GitLab merge request URLs.
"""

import os
from typing import Dict, List, Any
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP, Context

from .analyzer import CodeAnalyzer
from .test_planner import UITestPlanGenerator
from .models import ChangeAnalysis, UITestPlan, EnhancedUITestPlan

# Load environment variables
load_dotenv()

# Initialize MCP server
mcp = FastMCP(
    name="GitLab UI Test Plan Generator",
)


@mcp.tool()
async def ui_test_plan_from_mr(mr_url: str, ctx: Context) -> Dict[str, Any]:
    """
    Generates a detailed UI test plan for a GitLab Merge Request URL using local AI.
    
    This tool uses a locally hosted AI model (via Ollama) to intelligently analyze
    code changes and generate comprehensive UI test scenarios. Your GitLab code
    never leaves your machine.
    
    Args:
        mr_url: The full GitLab merge request URL (e.g., https://gitlab.example.com/project/-/merge_requests/123)
    
    Returns:
        Dictionary containing the AI-generated UI test plan with affected pages and test scenarios
    """
    try:
        # Clean the URL - remove any extra @ symbols that Cursor might add
        cleaned_url = mr_url.strip()
        if cleaned_url.startswith('@'):
            cleaned_url = cleaned_url[1:]
        
        await ctx.info(f"🔍 Analyzing merge request: {cleaned_url}")
        
        # Initialize analyzer with the MR URL
        analyzer = CodeAnalyzer(cleaned_url)
        
        # Get code changes
        changes = analyzer.get_change_analysis()
        await ctx.info(f"📁 Found {len(changes)} changed files")
        
        # Use AI to analyze changes and infer affected UI pages
        await ctx.info("🤖 Running AI analysis of code changes...")
        analysis = await analyzer.ai_analyze_changes(changes)
        affected_pages = await analyzer.ai_infer_affected_ui_pages(changes)
        
        await ctx.info(f"🌐 Identified {len(affected_pages)} affected UI areas")
        
        # Generate enhanced AI-powered UI test plan
        generator = UITestPlanGenerator()
        await ctx.info("🧪 Generating enhanced AI-powered test plan...")
        enhanced_plan = await generator.generate_enhanced_plan(changes, affected_pages, analyzer.mr.title, analysis)
        
        await ctx.info(f"✅ Generated enhanced UI test plan for MR: {analyzer.mr.title}")
        
        # Format as markdown
        markdown_report = format_enhanced_test_plan(enhanced_plan)
        
        # Return both structured data and formatted markdown
        result = enhanced_plan.model_dump()
        result["markdown_report"] = markdown_report
        result["ai_insights"] = {
            "analysis_summary": analysis.get("summary", ""),
            "user_impact": analysis.get("user_impact", ""),
            "risk_areas": analysis.get("risk_areas", []),
            "ai_powered": True
        }
        
        return result
        
    except Exception as e:
        await ctx.error(f"Error generating UI test plan for {mr_url}: {str(e)}")
        raise


def format_enhanced_test_plan(plan: EnhancedUITestPlan) -> str:
    """
    Formats an enhanced test plan into a detailed markdown report.
    """
    lines = []
    
    # Title
    lines.append(f"# Test Plan: {plan.merge_request_title}\n")
    
    # Component Overview
    if plan.component_overview:
        lines.append("## 📋 Component Overview")
        lines.append(plan.component_overview.description or "")
        if plan.component_overview.key_features:
            lines.append("\n**Key Features:**")
            for feature in plan.component_overview.key_features:
                lines.append(f"- {feature}")
        lines.append("")
    
    # Data Flow
    if plan.data_flow:
        lines.append("## 🔄 Key Data Flow")
        if plan.data_flow.description:
            lines.append(plan.data_flow.description)
        if plan.data_flow.flow_diagram:
            lines.append("\n```")
            lines.append(plan.data_flow.flow_diagram)
            lines.append("```")
        if plan.data_flow.api_endpoints:
            lines.append("\n**API Endpoints:**")
            for endpoint in plan.data_flow.api_endpoints:
                lines.append(f"- {endpoint}")
        if plan.data_flow.data_sources:
            lines.append("\n**Data Sources:**")
            for source in plan.data_flow.data_sources:
                lines.append(f"- {source}")
        lines.append("")
    
    # What to Test
    if plan.test_cases:
        lines.append("## 🧪 What to Test")
        for test_case in plan.test_cases:
            lines.append(f"\n### {test_case.category}")
            if test_case.test_cases and len(test_case.test_cases) > 0:
                # Create table header
                headers = list(test_case.test_cases[0].keys())
                lines.append("| " + " | ".join(headers) + " |")
                lines.append("|" + "|".join(["---"] * len(headers)) + "|")
                
                # Add rows
                for tc in test_case.test_cases:
                    row = "| " + " | ".join(str(tc.get(h, "")) for h in headers) + " |"
                    lines.append(row)
            lines.append("")
    
    # Table Columns Data Mapping
    if plan.column_mappings:
        lines.append("## 📊 Table Columns Data Mapping")
        lines.append("| Column | Data Source | Backend Field | Transformation |")
        lines.append("|--------|-------------|---------------|----------------|")
        for cm in plan.column_mappings:
            transformation = cm.transformation or ""
            lines.append(f"| {cm.column_name} | {cm.data_source} | {cm.backend_field} | {transformation} |")
        lines.append("")
    
    # Filtering
    if plan.filter_tests:
        lines.append("## 🔍 Filtering")
        lines.append("| Filter | GraphQL Variable | Test Case | Expected Behavior |")
        lines.append("|--------|------------------|-----------|-------------------|")
        for ft in plan.filter_tests:
            graphql_var = ft.graphql_variable or ""
            lines.append(f"| {ft.filter_name} | {graphql_var} | {ft.test_case} | {ft.expected_behavior} |")
        lines.append("")
    
    # Pagination
    if plan.pagination_tests:
        lines.append("## 📄 Pagination")
        lines.append("| Test Case | Expected Behavior |")
        lines.append("|-----------|-------------------|")
        for pt in plan.pagination_tests:
            lines.append(f"| {pt.test_case} | {pt.expected_behavior} |")
        lines.append("")
    
    # How to Test UI Against Backend Data
    if plan.testing_methods:
        lines.append("## 🔍 How to Test UI Against Backend Data")
        for method in plan.testing_methods:
            lines.append(f"\n### Method: {method.method_name}")
            lines.append(method.description or "")
            if method.steps:
                lines.append("\n**Steps:**")
                for i, step in enumerate(method.steps, 1):
                    lines.append(f"{i}. {step}")
            if method.code_example:
                lines.append("\n**Code Example:**")
                lines.append("```")
                lines.append(method.code_example)
                lines.append("```")
            lines.append("")
    
    # Test Checklist
    if plan.test_checklist:
        lines.append("## 📊 Test Checklist")
        lines.append("| Category | Test | Priority |")
        lines.append("|----------|------|----------|")
        for item in plan.test_checklist:
            # Convert priority to emoji if needed
            priority = item.priority or "Medium"
            priority_lower = priority.lower()
            if priority_lower == "high":
                priority = "🔴 High"
            elif priority_lower == "medium":
                priority = "🟡 Medium"
            elif priority_lower == "low":
                priority = "🟢 Low"
            lines.append(f"| {item.category} | {item.test} | {priority} |")
        lines.append("")
    
    # Traditional Test Scenarios (for backward compatibility)
    if plan.test_scenarios:
        lines.append("## 🎯 Test Scenarios")
        for scenario in plan.test_scenarios:
            lines.append(f"\n### {scenario.title} (Risk: {scenario.risk_level})")
            for i, step in enumerate(scenario.steps, 1):
                lines.append(f"{i}. **Action:** {step.action}")
                lines.append(f"   **Expected:** {step.expected_result}")
            lines.append("")
    
    # AI Insights
    if plan.ai_insights:
        lines.append("## 🤖 AI Analysis Insights")
        if plan.ai_insights.get("summary"):
            lines.append(f"**Summary:** {plan.ai_insights.get('summary')}")
        if plan.ai_insights.get("user_impact"):
            lines.append(f"**User Impact:** {plan.ai_insights.get('user_impact')}")
        if plan.ai_insights.get("risk_areas"):
            lines.append(f"**Risk Areas:** {', '.join(plan.ai_insights.get('risk_areas', []))}")
        lines.append("")
    
    return "\n".join(lines)


def main():
    """Main entry point for running the MCP server."""
    mcp.run()

# Expose the mcp object at module level for MCP CLI discovery
server = mcp


if __name__ == "__main__":
    main() 