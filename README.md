# mcp_servers

Custom [MCP](https://modelcontextprotocol.io) servers I built for my development workflow.

MCP (Model Context Protocol) lets you extend AI assistants like Claude with custom tools. Instead of the AI guessing about your codebase, you give it actual access to your architecture, contracts, and conventions.

## What's here

**backend_orchestrator_mcp** — Gives Claude deep context about a multi-service backend. System overview, service contracts, environment matrix, semantic code search, change planning, diff validation against project guardrails.

**optimus_project_mcp** — Project-specific tooling for a multi-tenant SaaS platform. 12 custom tools for navigating a complex codebase, auto-indexing, prompt templates.

**tray_mcp_server** — System tray integration for desktop.

## Usage

```bash
pip install -r backend_orchestrator_mcp/requirements.txt

# Add to Claude Code
claude mcp add my-server --scope user \
  --env PYTHONPATH=/path/to/project \
  -- python -m mcp_servers.backend_orchestrator_mcp.server
```

## Why bother

Generic AI assistants don't know your architecture decisions, service boundaries, or coding conventions. These servers fix that — Claude becomes a dev partner that actually understands the codebase instead of making educated guesses.

## More info

- [MCP docs](https://modelcontextprotocol.io)
- [Official server examples](https://github.com/modelcontextprotocol/servers)
