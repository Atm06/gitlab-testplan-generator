"""
GitLab MCP Server

A Model Context Protocol server for GitLab integration that provides
intelligent code change analysis and automated test plan generation.
"""

__version__ = "1.0.0"
__author__ = "Ashutosh Mallick"
__email__ = "amallick@redhat.com"

from .server import mcp
from .analyzer import CodeAnalyzer
from .test_planner import UITestPlanGenerator
from .models import ChangeAnalysis, UITestPlan

__all__ = [
    "mcp",
    "CodeAnalyzer", 
    "UITestPlanGenerator",
    "ChangeAnalysis",
    "UITestPlan"
] 