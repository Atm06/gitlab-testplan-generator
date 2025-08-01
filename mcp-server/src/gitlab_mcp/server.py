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
from .models import ChangeAnalysis, UITestPlan

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
        await ctx.info(f"🔍 Analyzing merge request: {mr_url}")
        
        # Initialize analyzer with the MR URL
        analyzer = CodeAnalyzer(mr_url)
        
        # Get code changes
        changes = analyzer.get_change_analysis()
        await ctx.info(f"📁 Found {len(changes)} changed files")
        
        # Use AI to analyze changes and infer affected UI pages
        await ctx.info("🤖 Running AI analysis of code changes...")
        analysis = await analyzer.ai_analyze_changes(changes)
        affected_pages = await analyzer.ai_infer_affected_ui_pages(changes)
        
        await ctx.info(f"🌐 Identified {len(affected_pages)} affected UI areas")
        
        # Generate AI-powered UI test plan
        generator = UITestPlanGenerator()
        await ctx.info("🧪 Generating AI-powered test scenarios...")
        test_plan = await generator.generate_ai_plan(changes, affected_pages, analyzer.mr.title, analysis)
        
        await ctx.info(f"✅ Generated UI test plan with {len(test_plan.test_scenarios)} scenarios for MR: {analyzer.mr.title}")
        
        # Add AI analysis insights to the response
        result = test_plan.dict()
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


def main():
    """Main entry point for running the MCP server."""
    mcp.run()

# Expose the mcp object at module level for MCP CLI discovery
server = mcp


if __name__ == "__main__":
    main() 