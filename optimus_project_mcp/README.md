# Optimus Project MCP (Context + Guardrails)

A lightweight server exposing project-aware tools to keep AI assistants aligned with your Hybrid Smart Architecture.

Provides:
- get_system_overview
- get_service_contract(service)
- get_env_matrix
- code_search(query)
- open_file(path)
- plan_change(requirement)
- validate_diff(diff)
- refresh (reindex docs/compose)

It auto-reads your repo (SYSTEM_OVERVIEW.md + docker-compose.hybrid.yml + docker-compose.dev.yml) so you usually don't need to update this server unless architecture/policies change.

## Quick start

1) Install dependencies

```bash
pip install -r mcp_servers/optimus_project_mcp/requirements.txt
```

2) Run (HTTP tools mode)

```bash
python -m uvicorn mcp_servers.optimus_project_mcp.server:app --host 0.0.0.0 --port 8003 --reload
```

3) Endpoints

- GET /health
- POST /api/refresh
- GET /api/system_overview
- GET /api/service_contract/{service}
- GET /api/env_matrix
- GET /api/search?q=...&glob=**/*.py (optional)
- GET /api/open_file?path=relative/path
- POST /api/plan_change {"requirement": "..."}
- POST /api/validate_diff {"diff": "<unified diff>"}

## Auto indexer

The server automatically re-indexes when relevant files change (policy, compose, docs).

Environment variables:

- MCP_INDEXER_ENABLED: "true" (default) | "false"
- MCP_INDEXER_INTERVAL: polling interval in seconds (default: 1.0)

Examples:

```bash
# disable watcher
MCP_INDEXER_ENABLED=false python -m uvicorn mcp_servers.optimus_project_mcp.server:app --port 8003

# slower polling (2s)
MCP_INDEXER_INTERVAL=2.0 python -m uvicorn mcp_servers.optimus_project_mcp.server:app --port 8003
```

## MCP integration

- Claude CLI / Windsurf: You can create a small wrapper that treats these endpoints as tools, or use native MCP later. This server can be extended to speak MCP stdio if you prefer. For now, HTTP tools are easier and portable (also works with Cursor and Gemini CLI).

## Policies enforced (policy.yaml)

- DB access only in `memory-engine/`.
- No Alembic outside `memory-engine/`.
- Multi-tenant only: forbid `public` schema; enforce prefix `t_`.
- `ai-engine/` and `backend-orchestrator/` cannot use DB.
- `rules-engine/` cannot use DB (must call `memory-engine/`).
- LLM usage restricted to allowed services.
- Redis DB indexes per service.

## Notes

- Production uses docker-compose.hybrid.yml (per your setup). Dev stacks are hybrid + dev overlay.
- If you change architecture or add new services, update `policy.yaml`.
