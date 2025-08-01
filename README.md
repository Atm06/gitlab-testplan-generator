# GitLab UI Test Plan Generator

An AI-powered MCP server that generates comprehensive UI test plans from GitLab merge requests using local Ollama AI models. Your code never leaves your machine.

## 🏗️ Project Structure

```
gitlab-testplan-generator/
├── mcp-server/
│   ├── src/gitlab_mcp/           # Main package
│   │   ├── server.py            # MCP server with ui_test_plan_from_mr tool
│   │   ├── analyzer.py          # GitLab MR analysis with AI
│   │   ├── test_planner.py      # AI-powered test plan generation
│   │   ├── ai_service.py        # Local Ollama AI integration
│   │   └── models.py            # Pydantic data models
│   ├── examples/                # Usage examples
│   │   ├── demo_analysis.py     # Demo script
│   │   ├── example_usage.py     # Example usage patterns
│   │   └── test_ollama.py       # AI agent verification test
│   ├── docs/                    # Documentation
│   ├── main.py                  # Entry point
│   ├── requirements.txt         # Dependencies
│   └── .env                     # Environment configuration
└── venv/                        # Virtual environment
```

## 🔧 Features

### 🤖 **AI-Powered Analysis**
- Uses local Ollama AI models for intelligent code analysis
- Analyzes GitLab merge requests to identify affected UI areas
- Generates context-aware test scenarios based on code changes
- Privacy-first: All analysis happens locally on your machine

### 📋 **Comprehensive Test Plans**
- Generates UI-focused test scenarios with specific steps
- Risk assessment for each test scenario (high/medium/low)
- Expected results and acceptance criteria
- Handles both positive and edge-case testing scenarios

### 🔗 **Seamless Integration**
- Direct integration with Cursor IDE via MCP protocol
- Simple `@ui_test_plan_from_mr` command usage
- Works with GitLab.com and self-hosted GitLab instances
- No external API calls - everything runs locally

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8+
- [Ollama](https://ollama.ai) installed and running
- GitLab personal access token
- Cursor IDE

### 2. Installation

```bash
# Navigate to the project
cd gitlab-testplan-generator

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
cd mcp-server
pip install -r requirements.txt
```

### 3. Configuration

Set up your GitLab credentials in `mcp-server/.env`:

```env
GITLAB_URL=https://gitlab.cee.redhat.com  # Your GitLab instance
GITLAB_TOKEN=your-personal-access-token   # GitLab PAT with api, read_repository scopes
GITLAB_SSL_VERIFY=false                   # For internal GitLab instances
```

### 4. Install in Cursor

Add to your `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "gitlab-ui-test-plan-generator": {
      "command": "/path/to/gitlab-testplan-generator/venv/bin/python",
      "args": ["/path/to/gitlab-testplan-generator/mcp-server/main.py"],
      "env": {
        "GITLAB_URL": "https://gitlab.cee.redhat.com"
      }
    }
  }
}
```
```

### 5. Start Ollama

```bash
# Install and start Ollama
ollama serve

# Pull the AI model (in another terminal)
ollama pull qwen2.5-coder:1.5b
```

### 6. Verify AI Agent (Optional but Recommended)

```bash
# Navigate to examples directory
cd mcp-server/examples

# Run AI agent verification test
python test_ollama.py
```

This test verifies:
- ✅ Ollama server status and version
- ✅ Required AI model availability  
- ✅ AI generation capabilities

**Expected output:**
```
=== Ollama AI Agent Status Check ===
✅ Ollama server is running (version: 0.9.6)
✅ Required model 'qwen2.5-coder:1.5b' is available
✅ AI generation successful!
🎉 All tests passed! Your AI agent is running correctly on Ollama.
```

### Demo & Examples

```bash
# Verify AI agent is working correctly
python examples/test_ollama.py

# Run demo analysis (works offline without GitLab credentials)
python examples/demo_analysis.py

# Run with real GitLab connection
# (requires configured .env file)
python examples/demo_analysis.py
```

## 📋 Available MCP Tool

### `ui_test_plan_from_mr`

**The main tool for generating UI test plans from GitLab merge requests.**

**Usage in Cursor:**
```
@ui_test_plan_from_mr https://gitlab.cee.redhat.com/project/-/merge_requests/123
```

**What it does:**
1. 🔍 Analyzes the merge request and extracts code changes
2. 🤖 Uses local AI to understand the impact of changes
3. 🎯 Identifies affected UI areas and components
4. 📋 Generates comprehensive test scenarios with specific steps
5. ⚠️ Provides risk assessment for each scenario

## 💡 Usage Examples

### In Cursor:

```
@ui_test_plan_from_mr https://gitlab.cee.redhat.com/<project_name>/merge_requests/12345

@ui_test_plan_from_mr https://gitlab.cee.redhat.com/project/-/merge_requests/123/diffs
```

### Example Output:

The tool generates:
- **MR Title**: [JIRA-ID]: MR title description  
- **Affected Pages**: Affected pages and components
- **Test Scenarios**: 2-5 AI-generated scenarios
- **Risk Levels**: High/Medium/Low for each scenario
- **Detailed Steps**: Specific actions and expected results
- **AI Insights**: Summary of changes and user impact

## 🔧 Architecture

### Core Components

- **`CodeAnalyzer`**: Analyzes GitLab merge requests and calculates complexity/risk scores
- **`UITestPlanGenerator`**: Creates comprehensive test plans based on change analysis
- **`MCP Server`**: Exposes functionality through the Model Context Protocol
- **`Models`**: Pydantic data models for type safety and validation

### Component Analysis

The system automatically identifies components based on file patterns:

- **Authentication**: `/auth/`, `/login/`, `/user/` files
- **Database**: `.sql`, migration files, `/models/`, `/db/` files  
- **API**: `/api/`, `/endpoints/`, `/routes/` files
- **Frontend**: `.js`, `.ts`, `.vue`, `.html`, `.css` files
- **Backend**: `.py`, `.java`, `.cpp`, `.go` files
- **Configuration**: `/config/`, `.env`, `.yaml`, `.json` files
- **Security**: `/security/`, `/ssl/` files

### Risk Assessment

The server automatically assesses risk levels:

- **High Risk**: Security files, database migrations, configuration files, complex changes (>100 lines)
- **Medium Risk**: API files, service files, moderate complexity (50-100 lines)
- **Low Risk**: Documentation, simple changes (<50 lines)

## 📖 Documentation

- **[Setup Guide](SETUP_GUIDE.md)**: Detailed setup instructions
- **[Examples](../examples/)**: Working code examples and verification scripts

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test manually
4. Verify AI agent functionality: `python examples/test_ollama.py`
5. Test with real GitLab merge requests
6. Submit a pull request

### Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Verify setup
python examples/demo_analysis.py
```

## 📝 License

MIT License - see LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you've installed the package with `pip install -e .`
2. **GitLab Connection**: Verify your token has correct permissions and hasn't expired
3. **MCP Installation**: Ensure Cursor has MCP support enabled

### Debug Mode

```bash
# Run with debug logging
export PYTHONPATH=src
python -m gitlab_mcp.server --log-level debug
```

---

**Ready to start?** Check out the [Setup Guide](SETUP_GUIDE.md) for detailed instructions! 
