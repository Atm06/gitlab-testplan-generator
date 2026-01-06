#!/usr/bin/env python3
"""
Analyze a specific GitLab MR and generate UI test plan
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv
from gitlab_mcp.analyzer import CodeAnalyzer
from gitlab_mcp.test_planner import UITestPlanGenerator

async def analyze_mr(mr_url: str):
    """Analyze a merge request and generate test plan."""
    load_dotenv()

    print(f"🔍 Analyzing merge request: {mr_url}\n")

    try:
        # Initialize analyzer with the MR URL
        analyzer = CodeAnalyzer(mr_url)

        print(f"📋 MR #{analyzer.mr.iid}: {analyzer.mr.title}")
        print(f"👤 Author: {analyzer.mr.author['name']}")
        print(f"📊 Status: {analyzer.mr.state}")
        print()

        # Get code changes
        print("📁 Analyzing changed files...")
        changes = analyzer.get_change_analysis()
        print(f"   Found {len(changes)} changed files\n")

        for change in changes[:10]:  # Show first 10
            print(f"   • {change.file_path} ({change.change_type})")

        if len(changes) > 10:
            print(f"   ... and {len(changes) - 10} more files")

        print()

        # Use AI to analyze changes
        print("🤖 Running AI analysis of code changes...")
        analysis = await analyzer.ai_analyze_changes(changes)

        print(f"\n📝 AI Analysis Summary:")
        print(f"   {analysis.get('summary', 'N/A')}")
        print(f"\n🎯 User Impact:")
        print(f"   {analysis.get('user_impact', 'N/A')}")
        print(f"\n⚠️  Risk Areas:")
        for risk in analysis.get('risk_areas', [])[:3]:
            print(f"   • {risk}")
        print()

        # Infer affected UI pages
        print("🌐 Identifying affected UI areas...")
        affected_pages = await analyzer.ai_infer_affected_ui_pages(changes)
        print(f"   Identified {len(affected_pages)} affected UI areas:")
        for page in affected_pages:
            print(f"   • {page}")
        print()

        # Generate AI-powered UI test plan
        generator = UITestPlanGenerator()
        print("🧪 Generating AI-powered test scenarios...\n")
        test_plan = await generator.generate_ai_plan(changes, affected_pages, analyzer.mr.title, analysis)

        # Display test plan
        print("=" * 80)
        print("UI TEST PLAN")
        print("=" * 80)
        print(f"\nMR: {analyzer.mr.title}")
        print(f"URL: {mr_url}")
        print(f"\nOVERVIEW:\n{test_plan.overall_summary}\n")

        print(f"\n📋 TEST SCENARIOS ({len(test_plan.test_scenarios)}):")
        print("-" * 80)

        for i, scenario in enumerate(test_plan.test_scenarios, 1):
            print(f"\n{i}. {scenario.title}")
            print(f"   Risk Level: {scenario.risk_level.upper()}")
            print(f"   Steps:")
            for j, step in enumerate(scenario.steps, 1):
                print(f"      {j}. Action: {step.action}")
                print(f"         Expected: {step.expected_result}")

        print("\n" + "=" * 80)
        print(f"Total Scenarios: {len(test_plan.test_scenarios)}")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_mr.py <gitlab_mr_url>")
        print("Example: python analyze_mr.py https://gitlab.cee.redhat.com/customer-platform/ecosystem-catalog-nextjs/-/merge_requests/344")
        sys.exit(1)

    mr_url = sys.argv[1]
    sys.exit(asyncio.run(analyze_mr(mr_url)))
