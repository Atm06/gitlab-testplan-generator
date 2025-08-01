#!/usr/bin/env python3
"""
Example usage script for the GitLab MCP Server

This script demonstrates how to interact with the GitLab MCP server
both as a standalone tool and through the MCP protocol.
"""

import asyncio
import os
from dotenv import load_dotenv

# Import our MCP server components
from gitlab_mcp.analyzer import CodeAnalyzer
from gitlab_mcp.test_planner import UITestPlanGenerator
from gitlab_mcp.models import ChangeAnalysis

async def example_direct_usage():
    """Example of using the server components directly (without MCP)."""
    print("=== Direct Usage Example ===")
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize the analyzer
        analyzer = CodeAnalyzer()
        
        # Get project info
        project = analyzer.project
        print(f"Project: {project.name}")
        print(f"Description: {project.description}")
        print()
        
        # List recent merge requests
        mrs = project.mergerequests.list(
            state='all',
            order_by='updated_at',
            sort='desc',
            per_page=5
        )
        
        print("Recent Merge Requests:")
        for mr in mrs:
            print(f"  #{mr.iid}: {mr.title} ({mr.state})")
        
        if mrs:
            # Analyze the first merge request
            mr = mrs[0]
            print(f"\nAnalyzing MR #{mr.iid}: {mr.title}")
            
            # Get changes
            changes = mr.changes()
            
            analyses = []
            for change in changes['changes']:
                file_path = change['new_path'] or change['old_path']
                diff = change.get('diff', '')
                
                # Count line changes
                lines = diff.split('\n')
                lines_added = len([l for l in lines if l.startswith('+')])
                lines_removed = len([l for l in lines if l.startswith('-')])
                
                # Determine change type
                if change['new_file']:
                    change_type = "added"
                elif change['deleted_file']:
                    change_type = "deleted"
                else:
                    change_type = "modified"
                
                # Analyze the change
                complexity = analyzer.calculate_complexity_score(diff)
                risk_level = analyzer.determine_risk_level(file_path, complexity, lines_added + lines_removed)
                affected_components = analyzer.identify_affected_components(file_path)
                potential_impacts = analyzer.identify_potential_impacts(file_path, diff)
                
                analysis = ChangeAnalysis(
                    file_path=file_path,
                    change_type=change_type,
                    lines_added=lines_added,
                    lines_removed=lines_removed,
                    complexity_score=complexity,
                    risk_level=risk_level,
                    affected_components=affected_components,
                    potential_impacts=potential_impacts
                )
                
                analyses.append(analysis)
                
                print(f"\n  File: {file_path}")
                print(f"    Type: {change_type}")
                print(f"    Lines: +{lines_added}/-{lines_removed}")
                print(f"    Complexity: {complexity}/10")
                print(f"    Risk: {risk_level}")
                print(f"    Components: {', '.join(affected_components)}")
                if potential_impacts:
                    print(f"    Impacts: {potential_impacts[0]}")
            
            # Generate test plan
            if analyses:
                print("\n=== Generated Test Plan ===")
                generator = UITestPlanGenerator()
                # Note: Using placeholder call since generate_test_plan was removed
                # In real usage, you would use generate_ai_plan method
                affected_pages = ["General UI"]
                test_plan = await generator.generate_ai_plan(analyses, affected_pages, mr.title)
                
                print("\nOverview:")
                print(test_plan.overview)
                
                print("\nCritical Test Cases:")
                for test in test_plan.critical_test_cases[:3]:  # Show first 3
                    print(f"  - {test}")
                
                print(f"\nEstimated Effort: {test_plan.estimated_effort}")
                
                print("\nCoverage Recommendations:")
                for component, target in list(test_plan.coverage_recommendations.items())[:3]:
                    print(f"  - {component}: {target}%")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your .env file is configured correctly with:")
        print("  - GITLAB_URL")
        print("  - GITLAB_TOKEN") 
        print("  - GITLAB_PROJECT_ID")


async def example_mcp_client():
    """Example of using the server through MCP protocol."""
    print("\n=== MCP Client Example ===")
    
    try:
        # This would be how you'd use it through MCP
        # (This is a conceptual example - in practice you'd use the MCP tools through Cursor)
        
        print("In Cursor, you would use these tools:")
        print("1. list_recent_merge_requests() - to see recent MRs")
        print("2. analyze_merge_request(mr_id) - to analyze changes")
        print("3. generate_test_plan(mr_id) - to get test recommendations")
        print("4. identify_impact_areas(mr_id) - to assess impact")
        
        print("\nExample conversation with Cursor:")
        print("You: 'Analyze merge request #123 and generate a test plan'")
        print("Cursor: 'I'll analyze MR #123 and create a comprehensive test plan for you.'")
        print("        [Uses analyze_merge_request(123) and generate_test_plan(123)]")
        print("        'Based on the analysis, here's your test plan...'")
        
    except Exception as e:
        print(f"Error: {e}")


def demonstrate_risk_assessment():
    """Demonstrate the risk assessment functionality."""
    print("\n=== Risk Assessment Demo ===")
    
    analyzer = CodeAnalyzer()
    
    # Test different file types and scenarios
    test_cases = [
        ("src/auth/login.py", "def authenticate(user, password):", 150),
        ("config/database.yaml", "host: production-db", 20),
        ("frontend/components/Button.js", "const Button = () => {", 30),
        ("docs/README.md", "# Documentation", 10),
        ("src/api/payments.py", "def process_payment(amount):", 80),
        ("migrations/001_add_users.sql", "CREATE TABLE users", 25),
    ]
    
    print("File Risk Assessment Examples:")
    for file_path, sample_code, lines_changed in test_cases:
        complexity = analyzer.calculate_complexity_score(sample_code)
        risk = analyzer.determine_risk_level(file_path, complexity, lines_changed)
        components = analyzer.identify_affected_components(file_path)
        
        print(f"\n  {file_path}")
        print(f"    Risk: {risk.upper()}")
        print(f"    Complexity: {complexity}/10")
        print(f"    Components: {', '.join(components)}")


async def main():
    """Run all examples."""
    print("GitLab MCP Server - Example Usage\n")
    
    # Check if environment is configured
    load_dotenv()
    if not all([os.getenv('GITLAB_TOKEN'), os.getenv('GITLAB_PROJECT_ID')]):
        print("⚠️  Environment not configured!")
        print("Please copy .env.example to .env and configure your GitLab credentials.")
        print("\nRunning offline demos instead...\n")
        
        demonstrate_risk_assessment()
        await example_mcp_client()
    else:
        print("✅ Environment configured, running full examples...\n")
        await example_direct_usage()
        await example_mcp_client()
    
    print("\n=== Example Complete ===")
    print("To use with Cursor:")
    print("1. Configure your .env file")
    print("2. Run: uv run mcp install gitlab_mcp_server.py")
    print("3. Start using the tools in Cursor!")


if __name__ == "__main__":
    asyncio.run(main()) 