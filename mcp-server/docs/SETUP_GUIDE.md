# GitLab UI Test Plan Generator - Setup Guide

This guide will help you set up the GitLab UI Test Plan Generator to use AI-powered test plan generation directly in Cursor from GitLab merge request URLs.

## Prerequisites

- Python 3.8 or higher
- [Ollama](https://ollama.ai) installed and running
- Access to a GitLab repository (GitLab.com or self-hosted)
- Cursor IDE with MCP support
- GitLab personal access token

## Step 1: GitLab Configuration

### Create a Personal Access Token

1. Go to your GitLab instance (e.g., https://gitlab.cee.redhat.com)
2. Navigate to: **User Settings** → **Access Tokens**
3. Click **"Add new token"**
4. Fill in the details:
   - **Token name**: `cursor-ui-test-plan-generator`
   - **Expiration date**: Set to your preference (1 year recommended)
   - **Select scopes**:
     - ✅ `api` (Access the authenticated user's API)
     - ✅ `read_repository` (Read repository files and metadata)
5. Click **"Create personal access token"**
6. **Important**: Copy the token immediately - you won't see it again!

## Step 2: Install Ollama

### 2.1 Install Ollama

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# For Windows, download from https://ollama.ai
```

### 2.2 Start Ollama and Pull AI Model

```bash
# Start Ollama server (keep this running)
ollama serve

# In another terminal, pull the AI model
ollama pull qwen2.5-coder:1.5b
```

### 2.3 Verify AI Agent Setup (Optional)

To ensure your AI agent is running correctly on Ollama, you can run the verification script:

```bash
# Navigate to the examples directory
cd mcp-server/examples

# Run the AI agent verification test
python test_ollama.py
```

This test will check:
- ✅ Ollama server status and version
- ✅ Required AI model availability
- ✅ AI generation capabilities

If all tests pass, you'll see:
```
=== Ollama AI Agent Status Check ===

1. Checking if Ollama server is running...
✅ Ollama server is running (version: 0.9.6)

2. Checking if required model is available...
✅ Required model 'qwen2.5-coder:1.5b' is available

3. Testing AI generation...
✅ AI generation successful!

🎉 All tests passed! Your AI agent is running correctly on Ollama.
```

**Note**: Make sure you have the required dependencies installed. If you encounter a `ModuleNotFoundError`, install the missing packages in your virtual environment:

```bash
# Activate your virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install required dependencies
pip install aiohttp
```

## Step 3: Setup the MCP Server

### 3.1 Clone and Setup

```bash
# Navigate to your projects directory
cd ~/Projects  # or wherever you keep projects

# Clone this repository (or download the files)
git clone <repository-url>  # or create new directory
cd gitlab-test-plan-generator

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
cd mcp-server
pip install -r requirements.txt
```

### 3.2 Configure Environment

Create `mcp-server/.env` with your GitLab credentials:

```env
GITLAB_URL=https://gitlab.cee.redhat.com  # Your GitLab instance URL
GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx  # Your personal access token
GITLAB_SSL_VERIFY=false                   # For internal GitLab instances
```

## Step 4: Test the Installation

### 4.1 Test the MCP Server

```bash
# Activate virtual environment if not already active
cd gitlab-ui-test-plan-generator
source .venv/bin/activate

# Test that the server loads correctly
cd mcp-server
python -c "
import sys
sys.path.insert(0, 'src')
from gitlab_mcp.server import mcp
print('✅ MCP Server loads successfully')
"
```

### 4.2 Test with Demo Script (Optional)

```bash
# Run the demo script (requires valid .env configuration)
python examples/demo_analysis.py
```

## Step 5: Install in Cursor

Add the MCP server to your Cursor configuration file:

**Location:** `~/.cursor/mcp.json` (create if it doesn't exist)

```json
{
  "mcpServers": {
    "gitlab-ui-test-plan-generator": {
      "command": "/Users/your-username/Projects/gitlab-ui-test-plan-generator/.venv/bin/python",
      "args": [
        "/Users/your-username/Projects/gitlab-ui-test-plan-generator/mcp-server/main.py"
      ],
      "env": {
        "GITLAB_URL": "https://gitlab.cee.redhat.com"
      }
    }
  }
}
```

**Important:** Replace `/Users/your-username/Projects/gitlab-ui-test-plan-generator` with your actual path.

## Step 6: Using the Server in Cursor

### Restart Cursor

After adding the MCP configuration, restart Cursor to load the new server.

### Available Tool

**`ui_test_plan_from_mr`** - The main tool for generating UI test plans

### Usage Examples

Simply use the `@` syntax in Cursor with GitLab merge request URLs:

1. **Generate test plan from MR URL:**
   ```
   @ui_test_plan_from_mr https://gitlab.cee.redhat.com/customer-platform/ecosystem-catalog-nextjs/-/merge_requests/252
   ```

2. **Works with diffs URLs too:**
   ```
   @ui_test_plan_from_mr https://gitlab.cee.redhat.com/project/-/merge_requests/123/diffs
   ```

3. **Any GitLab MR URL format:**
   ```
   @ui_test_plan_from_mr https://your-gitlab.com/group/project/-/merge_requests/456
   ```

### What You'll Get

The tool will generate:
- ✅ **MR Analysis**: Title, affected files, change summary
- 🎯 **Affected UI Areas**: AI-identified components that need testing  
- 📋 **Test Scenarios**: 2-5 detailed scenarios with specific steps
- ⚠️ **Risk Assessment**: High/Medium/Low risk levels for each scenario
- 🤖 **AI Insights**: Summary of changes and user impact analysis

## Troubleshooting

### Common Issues

#### ❌ "GITLAB_TOKEN environment variable is required"
- **Solution**: Make sure your `.env` file is properly configured
- Check that `GITLAB_TOKEN` is set in your environment

#### ❌ "Project not found" or "403 Forbidden"
- **Solution**: Verify your token has access to the project
- Check that `GITLAB_PROJECT_ID` is the numeric ID, not the project name
- Ensure your token has the required scopes (`api`, `read_repository`, `read_user`)

#### ❌ "ModuleNotFoundError: No module named 'gitlab'"
- **Solution**: Make sure you've installed dependencies
- Run `pip install -r requirements.txt` in your virtual environment

#### ❌ MCP server not appearing in Cursor
- **Solution**: Check Cursor's MCP configuration at `~/.cursor/mcp.json`
- Verify the path to your virtual environment and main.py is correct
- Restart Cursor after configuration changes

#### ❌ "Ollama not available" warning
- **Solution**: Make sure Ollama is running with `ollama serve`
- Check if the model is installed: `ollama list`
- Pull the model if needed: `ollama pull qwen2.5-coder:1.5b`
- **Verify AI agent**: Run `python mcp-server/examples/test_ollama.py` to check AI agent status

### Debug Mode

For detailed debugging:

```bash
# Set debug environment
export MCP_DEBUG=1

# Test the MCP server directly
cd gitlab-ui-test-plan-generator/mcp-server
PYTHONPATH=src python main.py
```

### Verify Setup

Test your complete setup:

```bash
# 1. Check Ollama is running
curl http://localhost:11434/api/version

# 2. Test AI agent (optional but recommended)
cd mcp-server/examples
python test_ollama.py

# 3. Test GitLab connection
cd gitlab-ui-test-plan-generator/mcp-server
python -c "
import os
from dotenv import load_dotenv
import gitlab

load_dotenv()
gl = gitlab.Gitlab(os.getenv('GITLAB_URL'), private_token=os.getenv('GITLAB_TOKEN'), ssl_verify=False)
print(f'✅ GitLab connection successful: {gl.user.username}')
"

# 4. Test the demo
python examples/demo_analysis.py
```

## Security Notes

- **Never commit** your `.env` file to version control
- Use token expiration dates appropriate for your security policy
- Regularly rotate your GitLab personal access tokens
- Consider using GitLab group access tokens for team deployments

## Quick Test

After setup, try this in Cursor:

```
@ui_test_plan_from_mr https://gitlab.cee.redhat.com/customer-platform/ecosystem-catalog-nextjs/-/merge_requests/252
```

## Support

- Check the [README.md](README.md) for detailed documentation
- Review [examples/demo_analysis.py](../examples/demo_analysis.py) for usage examples
- Open an issue if you encounter problems

---

**Next Steps**: You're ready! Use `@ui_test_plan_from_mr` with any GitLab merge request URL in Cursor to generate AI-powered UI test plans! 