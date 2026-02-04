# 🔌 MCP Servers Collection

> Custom Model Context Protocol (MCP) servers for AI-assisted development workflows.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)
[![Claude](https://img.shields.io/badge/Claude-Code-orange.svg)](https://claude.ai)

## What is MCP?

[Model Context Protocol](https://modelcontextprotocol.io) is an open standard for connecting AI assistants to external tools and data sources. These servers extend Claude Code (and other MCP-compatible clients) with custom capabilities.

## Included Servers

### 🏗️ Backend Orchestrator MCP

Provides Claude Code with deep understanding of a multi-service backend architecture:

- **System Overview** — Full architecture documentation
- **Service Contracts** — API contracts between microservices
- **Environment Matrix** — Environment variables across services
- **Code Search** — Semantic search across the codebase
- **Change Planning** — Architecture-aware guidance for modifications
- **Diff Validation** — Validate changes against project guardrails

### 🎯 Optimus Project MCP

Project-specific tooling for a multi-tenant SaaS platform:

- **12 custom tools** for navigating a complex codebase
- **Auto-indexing** with configurable polling
- **Prompt templates** for common development tasks

### 🖥️ Tray MCP Server

System tray integration for desktop environments.

## Quick Start

```bash
# Install dependencies
pip install -r backend_orchestrator_mcp/requirements.txt

# Add to Claude Code
claude mcp add my-server --scope user \
  --env PYTHONPATH=/path/to/project \
  -- python -m mcp_servers.backend_orchestrator_mcp.server
```

## Configuration

Each server supports environment-based configuration:

```bash
MCP_INDEXER_ENABLED=true    # Enable auto-indexing
MCP_INDEXER_INTERVAL=1.0    # Polling interval (seconds)
PYTHONPATH=/path/to/project # Project root for imports
```

## Architecture

```
mcp_servers/
├── backend_orchestrator_mcp/
│   ├── server.py           # HTTP server (SSE transport)
│   ├── stdio_server.py     # Stdio server (for Claude Code)
│   └── requirements.txt
├── optimus_project_mcp/
│   ├── server.py
│   ├── stdio_server.py
│   └── tools/              # Custom tool implementations
└── tray_mcp_server/
    └── ...
```

## Why Custom MCP Servers?

Standard AI assistants lack context about your specific:
- Architecture decisions
- Service boundaries
- Coding conventions
- Environment setup

Custom MCP servers bridge this gap, turning Claude into a context-aware development partner that understands *your* codebase.

## Use Cases

- 🔍 **Codebase Navigation** — "Show me how auth flows between services"
- 📋 **Change Planning** — "What files need to change for feature X?"
- ✅ **Validation** — "Does this PR follow our architecture guidelines?"
- 📚 **Documentation** — "Generate docs for this service contract"

## Tech Stack

- **Python 3.10+**
- **MCP SDK** — Protocol implementation
- **FastAPI** — HTTP transport option
- **Pydantic** — Data validation

## Resources

- [MCP Documentation](https://modelcontextprotocol.io)
- [Claude Code](https://claude.ai/code)
- [MCP Server Examples](https://github.com/modelcontextprotocol/servers)

## License

MIT

---

Built by [Marcelo Marleta](https://github.com/mmarleta)
