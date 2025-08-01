"""
Code Analysis Module

This module is responsible for parsing GitLab MR URLs, analyzing the
code changes, and inferring which UI pages are likely affected using
both heuristics and local AI analysis.
"""

import re
import os
from typing import List, Dict, Any
from urllib.parse import urlparse
import gitlab
from .models import ChangeAnalysis
from .ai_service import LocalAIService, get_ai_config


class CodeAnalyzer:
    """Analyzes code changes to inform UI test plan generation."""
    
    def __init__(self, mr_url: str):
        """
        Initializes the analyzer with a GitLab Merge Request URL.
        
        Args:
            mr_url: The full URL to the GitLab merge request.
        """
        parsed_url = urlparse(mr_url)
        gitlab_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        path_parts = parsed_url.path.strip('/').split('/-/')
        
        project_path = path_parts[0]
        mr_iid = int(path_parts[1].split('/')[-1])

        token = os.getenv("GITLAB_TOKEN")
        if not token:
            raise ValueError("GITLAB_TOKEN environment variable is required")

        ssl_verify = os.getenv('GITLAB_SSL_VERIFY', 'true').lower() != 'false'
        
        self.gl = gitlab.Gitlab(gitlab_url, private_token=token, ssl_verify=ssl_verify)
        self.project = self.gl.projects.get(project_path)
        self.mr = self.project.mergerequests.get(mr_iid)

    def get_change_analysis(self) -> List[ChangeAnalysis]:
        """
        Analyzes the changes in the MR and returns a structured list.
        """
        changes = self.mr.changes()['changes']
        analyses = []
        
        for change in changes:
            analysis = ChangeAnalysis(
                file_path=change['new_path'],
                change_type='deleted' if change['deleted_file'] else ('added' if change['new_file'] else 'modified'),
                raw_diff=change['diff']
            )
            analyses.append(analysis)
            
        return analyses


    
    async def ai_analyze_changes(self, changes: List[ChangeAnalysis]) -> Dict[str, Any]:
        """
        Use local AI to analyze code changes and understand their impact.
        This provides deeper insights than simple heuristics.
        """
        config = get_ai_config()
        
        async with LocalAIService(config) as ai_service:
            # Check if Ollama is running
            if not await ai_service.check_ollama_status():
                print("⚠️  Ollama not available. Falling back to heuristic analysis.")
                return self._fallback_analysis(changes)
            
            try:
                analysis = await ai_service.analyze_code_changes(changes, self.mr.title)
                print("✅ AI analysis completed")
                return analysis
            except Exception as e:
                print(f"⚠️  AI analysis failed: {e}. Using fallback analysis.")
                return self._fallback_analysis(changes)
    
    def _fallback_analysis(self, changes: List[ChangeAnalysis]) -> Dict[str, Any]:
        """Fallback analysis when AI is not available."""
        affected_files = [change.file_path for change in changes]
        
        return {
            "summary": f"Modified {len(changes)} files in merge request: {self.mr.title}",
            "affected_areas": self.infer_affected_ui_pages(changes),
            "user_impact": "Code changes detected. Manual verification recommended.",
            "risk_areas": ["UI functionality", "User workflows"]
        }
    
    async def ai_infer_affected_ui_pages(self, changes: List[ChangeAnalysis]) -> List[str]:
        """
        Use AI to intelligently infer affected UI pages based on code changes.
        Falls back to heuristic analysis if AI is not available.
        """
        try:
            analysis = await self.ai_analyze_changes(changes)
            ai_pages = analysis.get('affected_areas', [])
            
            return ai_pages if ai_pages else ["General UI"]
            
        except Exception as e:
            print(f"⚠️  AI page inference failed: {e}. Using fallback.")
            # Simple fallback based on file paths
            affected_pages = []
            for change in changes:
                if any(ext in change.file_path.lower() for ext in ['.tsx', '.jsx', '.vue', '.html', '.css', '.js', '.ts']):
                    page_name = change.file_path.split('/')[-1].replace('.', ' ').title()
                    affected_pages.append(page_name)
            
            return affected_pages[:5] if affected_pages else ["General UI"] 