#!/usr/bin/env python3
"""
Main entry point for GitLab MCP Server

This file provides the main entry point for running the GitLab MCP server
with the new modular structure.
"""

import sys
from pathlib import Path

# Adjust path to find the 'src' directory from the new project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from gitlab_mcp.server import main

if __name__ == "__main__":
    main() 