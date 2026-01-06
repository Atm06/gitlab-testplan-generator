# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GitLab UI Test Plan Generator is an MCP (Model Context Protocol) server that generates AI-powered UI test plans from GitLab merge request URLs using local Ollama AI models. The system operates entirely locally - no GitLab code ever leaves the machine.

**Key Architecture**: FastMCP server → GitLab API → Local AI (Ollama) → Structured test plans

## Development Commands

### Environment Setup
```bash
# Initial setup
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
cd mcp-server
pip install -r requirements.txt
```

### Running the MCP Server
```bash
# From project root, activate venv first
cd mcp-server
PYTHONPATH=src python main.py
```

### Testing
```bash
# Verify AI agent status (recommended before testing)
cd mcp-server/examples
python test_ollama.py

# Run demo analysis (tests without real GitLab connection)
python demo_analysis.py

# Test with real GitLab MR (requires .env configuration)
python example_usage.py
```

### Verification Commands
```bash
# Check Ollama is running
curl http://localhost:11434/api/version

# Test GitLab connection
python -c "
import os
from dotenv import load_dotenv
import gitlab
load_dotenv()
gl = gitlab.Gitlab(os.getenv('GITLAB_URL'), private_token=os.getenv('GITLAB_TOKEN'), ssl_verify=False)
print(f'✅ Connected as: {gl.user.username}')
"
```

## Project Structure

```
gitlab-testplan-generator/
├── mcp-server/
│   ├── src/gitlab_mcp/         # Core package
│   │   ├── server.py           # FastMCP server with ui_test_plan_from_mr tool
│   │   ├── analyzer.py         # GitLab MR analysis + AI integration
│   │   ├── test_planner.py     # AI-powered test scenario generation
│   │   ├── ai_service.py       # Local Ollama AI service wrapper
│   │   └── models.py           # Pydantic models (ChangeAnalysis, UITestPlan, etc.)
│   ├── examples/               # Usage examples and verification scripts
│   ├── docs/                   # Documentation
│   ├── main.py                 # Entry point (adds src to path)
│   ├── requirements.txt        # Python dependencies
│   └── .env                    # Environment configuration (not in git)
└── pyproject.toml              # Package metadata
```

## Core Architecture

### Data Flow
1. **Input**: GitLab MR URL via MCP tool call
2. **Extraction**: Parse URL → GitLab API → fetch MR changes
3. **Analysis**: Code changes → Local AI (Ollama) → impact analysis
4. **Generation**: AI generates test scenarios with steps/risk levels
5. **Output**: Structured UITestPlan with AI insights

### Key Components

**CodeAnalyzer** (`analyzer.py`):
- Parses GitLab MR URLs to extract project path and MR IID
- Uses python-gitlab library to fetch MR changes via GitLab API
- Implements AI-powered change analysis with fallback to heuristics
- Environment variables: `GITLAB_URL`, `GITLAB_TOKEN`, `GITLAB_SSL_VERIFY`

**UITestPlanGenerator** (`test_planner.py`):
- Generates UI test scenarios using LocalAIService
- Falls back to placeholder scenarios if AI unavailable
- Creates structured test plans with risk assessment

**LocalAIService** (`ai_service.py`):
- Async context manager for Ollama API integration
- Two main operations:
  - `analyze_code_changes()`: Understands impact and affected areas
  - `generate_ui_test_scenarios()`: Creates detailed test scenarios
- Implements JSON response cleaning (removes markdown code blocks)
- Graceful degradation when Ollama unavailable

**Pydantic Models** (`models.py`):
- `ChangeAnalysis`: File path, change type, raw diff
- `TestStep`: Action + expected result
- `UITestScenario`: Title, steps, risk level
- `UITestPlan`: Complete test plan structure

### MCP Server Pattern

The server uses FastMCP with a single tool:

```python
@mcp.tool()
async def ui_test_plan_from_mr(mr_url: str, ctx: Context) -> Dict[str, Any]
```

Tool workflow:
1. Clean URL (remove `@` prefix added by Cursor)
2. Initialize CodeAnalyzer with MR URL
3. Get code changes via GitLab API
4. Run AI analysis on changes
5. Infer affected UI pages using AI
6. Generate AI-powered test plan
7. Return structured result with AI insights

## Configuration

### Required Environment Variables

**`.env` file in `mcp-server/` directory:**
```env
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=glpat-xxxxxxxxxxxx
GITLAB_SSL_VERIFY=false  # For self-hosted instances
```

**Optional AI Configuration:**
```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:1.5b
AI_MAX_TOKENS=8192
AI_TEMPERATURE=0.3
```

### GitLab Token Requirements
- Scopes needed: `api`, `read_repository`
- Create at: User Settings → Access Tokens
- Never commit tokens to git

### Cursor MCP Configuration

Add to `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "gitlab-ui-test-plan-generator": {
      "command": "/path/to/.venv/bin/python",
      "args": ["/path/to/mcp-server/main.py"],
      "env": {
        "GITLAB_URL": "https://gitlab.example.com"
      }
    }
  }
}
```

## AI Integration Details

### Ollama Setup
```bash
# Start Ollama
ollama serve

# Pull required model
ollama pull qwen2.5-coder:1.5b
```

### AI Prompting Strategy

**Code Analysis Prompt** (in `analyzer.py`):
- System prompt defines role as "senior software engineer"
- Requests JSON response with: summary, affected_areas, user_impact, risk_areas
- Limits to first 10 files to avoid token limits
- Includes diffs under 2000 chars per file

**Test Scenario Generation** (in `test_planner.py`):
- System prompt defines role as "QA engineer"
- Requests 3-5 focused scenarios with 5+ steps each
- JSON array format with title, steps, risk_level
- Emphasizes user-facing tests (not unit/integration tests)

### Fallback Mechanisms

The system gracefully degrades when AI unavailable:
1. **AI Status Check**: `check_ollama_status()` before each operation
2. **Heuristic Fallback**: `_fallback_analysis()` for code analysis
3. **Placeholder Scenarios**: `_generate_placeholder_scenarios()` for test plans
4. **JSON Parsing Fallback**: Returns basic structure if AI response malformed

## Development Patterns

### Error Handling
- All AI operations wrapped in try/except with fallbacks
- User-friendly warnings: "⚠️ Ollama not available. Using fallback..."
- Exceptions propagated to MCP server with context via `ctx.error()`

### Async Context Management
```python
async with LocalAIService(config) as ai_service:
    # Auto-manages aiohttp session lifecycle
    result = await ai_service.analyze_code_changes(changes, mr_title)
```

### Path Management
`main.py` adds `src/` to Python path before importing:
```python
sys.path.insert(0, str(project_root / "src"))
from gitlab_mcp.server import main
```

### URL Parsing Pattern
GitLab MR URLs parsed to extract:
- Scheme + host → GitLab instance URL
- Project path (before `/-/`)
- MR IID (numeric ID from URL)

Example: `https://gitlab.com/group/project/-/merge_requests/123`
- Instance: `https://gitlab.com`
- Project: `group/project`
- IID: `123`

## Testing Strategy

### Manual Testing Workflow
1. Verify AI agent: `python examples/test_ollama.py`
2. Test offline: `python examples/demo_analysis.py`
3. Test with real MR: Use actual GitLab MR URL
4. Check in Cursor: `@ui_test_plan_from_mr <MR_URL>`

### Verification Points
- ✅ Ollama server running (port 11434)
- ✅ Required model available (`qwen2.5-coder:1.5b`)
- ✅ GitLab API accessible with token
- ✅ AI generation produces valid JSON
- ✅ Fallbacks work when AI unavailable

## Common Development Tasks

### Adding New AI Capabilities
1. Add method to `LocalAIService` in `ai_service.py`
2. Define system prompt and expected JSON structure
3. Implement `_clean_json_response()` parsing
4. Add fallback mechanism
5. Update models if needed in `models.py`

### Modifying Test Scenario Generation
- Edit system prompt in `ai_service.py` (line 144+)
- Adjust JSON structure in prompt and parsing logic
- Update `UITestScenario` model if schema changes
- Test with `examples/demo_analysis.py`

### Debugging AI Responses
- Check raw AI response before JSON parsing (logged on error)
- Verify `_clean_json_response()` removes markdown code blocks
- Test with different temperature values (0.1-0.7)
- Try different models if response quality issues

### Extending to Other GitLab Features
- Follow same pattern: analyzer → AI service → structured output
- Reuse `CodeAnalyzer` GitLab client setup
- Add new tools to `server.py` with `@mcp.tool()` decorator
- Maintain async/await pattern throughout

## Important Constraints

1. **Token Limits**: Diffs over 2000 chars excluded, max 10 files analyzed
2. **SSL Verification**: Often disabled for internal GitLab instances
3. **Model Selection**: `qwen2.5-coder:1.5b` balances speed/quality for code analysis
4. **No External API Calls**: Everything runs locally (privacy-first design)
5. **MCP Protocol**: Server must expose `server` object at module level

## Dependencies

Core dependencies:
- `mcp[cli]>=1.12.0` - MCP server framework
- `python-gitlab>=4.0.0` - GitLab API client
- `pydantic>=2.0.0` - Data validation
- `aiohttp>=3.9.0` - Async HTTP for Ollama
- `python-dotenv>=1.0.0` - Environment config

External dependencies:
- Ollama running on `localhost:11434`
- GitLab instance accessible via API
