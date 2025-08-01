#!/usr/bin/env python3
"""
Demo script to test the GitLab MCP Server functionality.

This script demonstrates:
1. Connecting to GitLab
2. Analyzing a merge request
3. Generating a UI test plan

Usage:
    python examples/demo_analysis.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from gitlab_mcp.analyzer import CodeAnalyzer
from gitlab_mcp.test_planner import UITestPlanGenerator


async def main():
    """Main demo function."""
    print("=== GitLab MCP Server Demo ===\n")
    
    # Load environment variables
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ Loaded environment variables")
    else:
        print("⚠️  No .env file found. Make sure to configure your GitLab credentials.")
        return
    
    # Test MR URL (the one you provided)
    mr_url = "https://gitlab.cee.redhat.com/customer-platform/ecosystem-catalog-nextjs/-/merge_requests/252"
    
    try:
        print(f"🔍 Analyzing MR: {mr_url}")
        
        # Initialize analyzer
        analyzer = CodeAnalyzer(mr_url)
        
        # Analyze the merge request
        print("📊 Fetching merge request details...")
        changes = analyzer.get_change_analysis()
        
        # Use AI for analysis
        print("🤖 Running AI analysis...")
        analysis = await analyzer.ai_analyze_changes(changes)
        affected_pages = await analyzer.ai_infer_affected_ui_pages(changes)
        
        print(f"✅ Analysis complete!")
        print(f"  • Title: {analyzer.mr.title}")
        print(f"  • Files changed: {len(changes)}")
        print(f"  • Affected UI pages: {', '.join(affected_pages)}")
        print(f"  • AI Summary: {analysis.get('summary', 'N/A')}")
        
        # Generate AI-powered UI test plan
        print("\n🧪 Generating AI-powered UI test plan...")
        test_planner = UITestPlanGenerator()
        test_plan = await test_planner.generate_ai_plan(changes, affected_pages, analyzer.mr.title, analysis)
        
        print(f"✅ Test plan generated!")
        print(f"  • Total scenarios: {len(test_plan.test_scenarios)}")
        
        # Display the test plan
        print(f"\n{'='*60}")
        print(f"UI TEST PLAN")
        print(f"{'='*60}")
        print(f"MR: {test_plan.merge_request_title}")
        print(f"Affected Pages: {', '.join(test_plan.affected_ui_pages)}")
        print(f"Overall Summary: {test_plan.overall_summary}")
        print(f"\nTest Scenarios:")
        
        for i, scenario in enumerate(test_plan.test_scenarios, 1):
            print(f"\n{i}. {scenario.title}")
            print(f"   Risk Level: {scenario.risk_level}")
            print(f"   Steps:")
            for j, step in enumerate(scenario.steps, 1):
                print(f"     {j}. {step.action}")
                print(f"        Expected: {step.expected_result}")
        
        print(f"\n{'='*60}")
        print("✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure your .env file has valid GitLab credentials")
        print("2. Check that the GitLab URL is accessible")
        print("3. Verify the merge request exists and is accessible")


if __name__ == "__main__":
    asyncio.run(main())