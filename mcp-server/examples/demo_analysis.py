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
import threading
import time
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from gitlab_mcp.analyzer import CodeAnalyzer
from gitlab_mcp.test_planner import UITestPlanGenerator


def show_loader(message="Analyzing..."):
    """Show a spinner/loader while processing."""
    spinner = "|/-\\"
    for i in range(60):  # ~6 seconds, adjust as needed
        sys.stdout.write(f"\r{message} {spinner[i % len(spinner)]}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * (len(message) + 2) + "\r")  # Clear line


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
        
        # Start loader for AI analysis
        loader_thread = threading.Thread(target=show_loader, args=("🤖 AI is analyzing the code changes...",))
        loader_thread.start()
        
        # Use AI for analysis
        analysis = await analyzer.ai_analyze_changes(changes)
        affected_pages = await analyzer.ai_infer_affected_ui_pages(changes)
        
        loader_thread.join()
        print("✅ Analysis completed! Generating results now...\n")
        
        # Show AI thinking process if available
        if "thinking_process" in analysis:
            print("🧠 AI Thinking Process:\n", analysis.get("thinking_process"), "\n")
        
        print("✨ Here is your detailed AI-powered analysis:\n")
        print(f"📝 Summary: {analysis.get('summary', 'N/A')}")
        print(f"🧩 Affected Areas: {', '.join(analysis.get('affected_areas', []))}")
        print(f"👤 User Impact: {analysis.get('user_impact', 'N/A')}")
        print(f"⚠️ Risk Areas: {', '.join(analysis.get('risk_areas', []))}")
        print(f"🤖 AI Insights: {analysis.get('ai_insights', 'N/A')}")
        
        print(f"\n✅ Analysis complete!")
        print(f"  • Title: {analyzer.mr.title}")
        print(f"  • Files changed: {len(changes)}")
        print(f"  • Affected UI pages: {', '.join(affected_pages)}")
        
        # Start loader for test plan generation
        loader_thread = threading.Thread(target=show_loader, args=("🧪 AI is generating test scenarios...",))
        loader_thread.start()
        
        # Generate AI-powered UI test plan
        test_planner = UITestPlanGenerator()
        test_plan = await test_planner.generate_ai_plan(changes, affected_pages, analyzer.mr.title, analysis)
        
        loader_thread.join()
        print("✅ Test plan generation completed!\n")
        
        print(f"✅ Test plan generated!")
        print(f"  • Total scenarios: {len(test_plan.test_scenarios)}")
        
        # Display the test plan with improved formatting
        print(f"\n{'='*60}")
        print(f"🎯 UI TEST PLAN")
        print(f"{'='*60}")
        print(f"📋 MR: {test_plan.merge_request_title}")
        print(f"🧩 Affected Pages: {', '.join(test_plan.affected_ui_pages)}")
        print(f"📝 Overall Summary: {test_plan.overall_summary}")
        print(f"\n🧪 Test Scenarios:")
        
        for i, scenario in enumerate(test_plan.test_scenarios, 1):
            risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(scenario.risk_level.lower(), "⚪")
            print(f"\n{i}. {scenario.title}")
            print(f"   {risk_emoji} Risk Level: {scenario.risk_level}")
            print(f"   📋 Steps:")
            for j, step in enumerate(scenario.steps, 1):
                print(f"     {j}. {step.action}")
                print(f"        ✅ Expected: {step.expected_result}")
        
        print(f"\n{'='*60}")
        print("🎉 Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure your .env file has valid GitLab credentials")
        print("2. Check that the GitLab URL is accessible")
        print("3. Verify the merge request exists and is accessible")


if __name__ == "__main__":
    asyncio.run(main())