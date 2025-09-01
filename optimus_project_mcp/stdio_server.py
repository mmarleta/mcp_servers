from __future__ import annotations

import os
import importlib
import time
import json
from typing import Dict, List, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

from mcp.server.fastmcp import FastMCP
import httpx

# Import modules (not symbols) to support hot reload
import mcp_servers.optimus_project_mcp.indexer as idx_mod
import mcp_servers.optimus_project_mcp.validator as val_mod
import mcp_servers.optimus_project_mcp.utils as util_mod
import mcp_servers.optimus_project_mcp.auto_indexer as ai_mod


mcp = FastMCP(name="Optimus Project MCP")

# In-memory singletons
indexer = idx_mod.Indexer()
indexer.refresh()
validator = val_mod.Validator(indexer.get_policy())
auto_indexer: Optional[ai_mod.AutoIndexer] = None


def _perform_refresh() -> None:
    """Reload policy/docs/compose and hot-reload code modules."""
    global indexer, validator
    # Hot-reload modules to pick up code changes without restart
    importlib.reload(util_mod)
    importlib.reload(idx_mod)
    importlib.reload(val_mod)
    # Recreate instances from reloaded modules
    indexer = idx_mod.Indexer()
    indexer.refresh()
    validator = val_mod.Validator(indexer.get_policy())


def _run_with_timeout(fn: Callable[[], Any], timeout_sec: float) -> Any:
    """Run a callable in a thread with a timeout. Raises TimeoutError on expiration."""
    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(fn)
        return fut.result(timeout=timeout_sec)


@mcp.tool()
def health() -> Dict[str, str]:
    """Health check."""
    return {"status": "ok"}


@mcp.tool()
def refresh() -> Dict[str, str]:
    """Reload policy/docs/compose and rebuild validator with timeout."""
    t0 = time.perf_counter()
    try:
        _run_with_timeout(_perform_refresh, 5.0)
        ok = True
        msg = "refreshed"
    except FuturesTimeout:
        ok = False
        msg = "refresh_timeout"
    dt_ms = int((time.perf_counter() - t0) * 1000)
    return {"status": msg, "duration_ms": str(dt_ms), "ok": str(ok).lower()}


@mcp.tool()
def system_overview() -> Dict:
    """Return docs filenames and compose service names."""
    return indexer.get_system_overview()


@mcp.tool()
def service_contract(service: str) -> Dict:
    """Return guardrail contract for a specific service name."""
    try:
        return indexer.get_service_contract(service)
    except KeyError:
        raise ValueError(f"Unknown service: {service}")


@mcp.tool()
def env_matrix() -> Dict[str, Dict]:
    """Return environment matrix for all compose services."""
    return indexer.get_env_matrix()


@mcp.tool()
def open_file(path: str) -> Dict[str, str]:
    """Open a repository-relative file and return its contents."""
    try:
        content = util_mod.read_text(path)
    except FileNotFoundError:
        raise ValueError(f"File not found: {path}")
    return {"path": path, "content": content}


@mcp.tool()
def search(q: str, glob: Optional[str] = None, limit: int = 100) -> Dict:
    """Search repository text with optional glob and result limit."""
    policy = indexer.get_policy()
    default_glob = (policy.get("search", {}) or {}).get("default_glob", "**/*")
    max_results = int((policy.get("search", {}) or {}).get("max_results", 100))
    results = util_mod.text_search(q, glob or default_glob, max_results=min(limit, max_results))
    return {"query": q, "results": results}


@mcp.tool()
def plan_change(requirement: str) -> Dict:
    """Provide high-level guidance according to architecture guardrails."""
    pol = indexer.get_policy()
    services = pol.get("services", {})
    guidance: List[str] = []

    low = requirement.lower()
    if any(k in low for k in ["database", "postgres", "schema", "migration", "alembic"]):
        guidance.append("All database read/write and migrations must be implemented in 'memory-engine/'. Other services must call its HTTP API.")
    if any(k in low for k in ["openai", "langchain", "llm", "embedding"]):
        guidance.append("LLM/LangChain usage is allowed in 'ai-engine/'. Avoid in 'backend-orchestrator/' and 'rules-engine/'.")
    if any(k in low for k in ["gateway", "entry", "handover", "webhook"]):
        guidance.append("Implement request routing/orchestration in 'backend-orchestrator/'. It must not handle DB nor LLM.")
    if any(k in low for k in ["rule", "business", "policy", "validation"]):
        guidance.append("Business rules live in 'rules-engine/'. It must call 'memory-engine/' for data, never DB directly.")

    guidance.append("Ensure multi-tenancy: never use 'public' schema; follow tenant-specific schemas (prefix 't_').")

    return {
        "requirement": requirement,
        "guidance": guidance,
        "service_contracts": services,
    }


@mcp.tool()
def validate_diff(diff: str) -> Dict:
    """Validate a unified diff against architecture guardrails with timeout and duration."""
    t0 = time.perf_counter()
    try:
        result = _run_with_timeout(lambda: validator.validate_diff(diff), 8.0)
        result["duration_ms"] = int((time.perf_counter() - t0) * 1000)
        return result
    except FuturesTimeout:
        return {
            "ok": False,
            "duration_ms": int((time.perf_counter() - t0) * 1000),
            "violations": [
                {
                    "type": "timeout",
                    "message": "validate_diff exceeded 8s timeout",
                }
            ],
        }


def _maybe_start_auto_indexer() -> None:
    enabled = (os.getenv("MCP_INDEXER_ENABLED", "true").strip().lower() in ("1", "true", "yes", "on"))
    if not enabled:
        return
    interval = float(os.getenv("MCP_INDEXER_INTERVAL", "1.0"))
    global auto_indexer
    auto_indexer = ai_mod.AutoIndexer(indexer, on_refresh=_perform_refresh, interval_sec=interval)
    auto_indexer.start()


@mcp.tool()
def prompts_list() -> Dict:
    """List all stored prompt names."""
    prompts = util_mod.load_prompts()
    return {"prompts": sorted(prompts.keys()), "count": len(prompts)}


@mcp.tool()
def prompts_get(name: str) -> Dict:
    """Get a stored prompt template by name."""
    prompts = util_mod.load_prompts()
    if name not in prompts:
        raise ValueError(f"Unknown prompt: {name}")
    return {"name": name, "template": prompts[name]}


@mcp.tool()
def prompts_set(name: str, template: str) -> Dict:
    """Create or update a prompt template."""
    prompts = util_mod.load_prompts()
    prompts[name] = template
    util_mod.save_prompts(prompts)
    return {"status": "saved", "name": name, "length": len(template)}


@mcp.tool()
def prompts_delete(name: str) -> Dict:
    """Delete a stored prompt by name."""
    prompts = util_mod.load_prompts()
    if name not in prompts:
        raise ValueError(f"Unknown prompt: {name}")
    del prompts[name]
    util_mod.save_prompts(prompts)
    return {"status": "deleted", "name": name}


@mcp.tool()
def prompts_apply(name: str, variables_json: Optional[str] = None) -> Dict:
    """Render a stored prompt with variables (JSON string)."""
    prompts = util_mod.load_prompts()
    if name not in prompts:
        raise ValueError(f"Unknown prompt: {name}")
    variables: Dict[str, Any] = {}
    if variables_json:
        try:
            variables = json.loads(variables_json)
        except Exception:
            variables = {}
    rendered = util_mod.render_prompt(prompts[name], variables)
    return {"name": name, "rendered": rendered}


@mcp.tool()
def prompts_apply_kv(name: str, variables_kv: Optional[str] = None) -> Dict:
    """Render a stored prompt with simple key=value variables (e.g., "type=feat scope=mcp")."""
    prompts = util_mod.load_prompts()
    if name not in prompts:
        raise ValueError(f"Unknown prompt: {name}")
    variables = util_mod.parse_kv_pairs(variables_kv)
    rendered = util_mod.render_prompt(prompts[name], variables)
    return {"name": name, "rendered": rendered}


@mcp.tool()
def service_urls() -> Dict:
    """List base URLs and related info for each compose service.

    For each service, derive:
      - ports: the raw compose port mappings
      - base_urls: http://localhost:<host_port> for each published port
      - internal_urls: any env var values that look like http(s) URLs
      - common_paths: generic paths commonly used by services (health/docs)
    """
    matrix = indexer.get_env_matrix() or {}

    def _extract_host_ports(ports: List) -> List[str]:
        host_ports: List[str] = []
        for p in ports or []:
            # Compose supports strings like "3000:80", "127.0.0.1:8020:8020", "8050:8050/tcp"
            # and dicts like {published: 3000, target: 80}
            if isinstance(p, str):
                s = p.split("/")[0]  # drop protocol suffix if any
                parts = s.split(":")
                if len(parts) == 1:
                    # Only one value (container-only). Treat it as host for best-effort.
                    host = parts[0]
                elif len(parts) == 2:
                    # host:container
                    host = parts[0]
                else:
                    # ip:host:container (or similar). Host port is the penultimate part.
                    host = parts[-2]
                if host and host.isdigit():
                    host_ports.append(host)
            elif isinstance(p, dict):
                pub = p.get("published") or p.get("host_port") or p.get("published_port")
                if pub is not None:
                    host_ports.append(str(pub))
        # Deduplicate and sort for stable output
        return sorted({h for h in host_ports if h})

    def _env_internal_urls(env_map: Dict[str, Any]) -> List[str]:
        urls: List[str] = []
        for v in (env_map or {}).values():
            try:
                if isinstance(v, str) and (v.startswith("http://") or v.startswith("https://")):
                    urls.append(v)
            except Exception:
                # be defensive against odd values
                continue
        return sorted(set(urls))

    services_out: Dict[str, Dict[str, Any]] = {}
    for name, info in matrix.items():
        ports = info.get("ports") or []
        host_ports = _extract_host_ports(ports)
        base_urls = [f"http://localhost:{hp}" for hp in host_ports]
        env_map = info.get("env") or {}
        internal_urls = _env_internal_urls(env_map)
        common_paths = ["/health", "/docs", "/openapi.json"]

        services_out[name] = {
            "ports": ports,
            "base_urls": base_urls,
            "internal_urls": internal_urls,
            "common_paths": common_paths,
        }

    return {"services": services_out}


@mcp.tool()
def discover_endpoints(
    timeout_sec: float = 2.0,
    services_csv: Optional[str] = None,
    page: int = 1,
    page_size: Optional[int] = None,
    base_urls_limit: Optional[int] = None,
    max_endpoints_per_service: Optional[int] = None,
    include_endpoints: bool = True,
    only_policy_services: bool = False,
) -> Dict:
    """Discover HTTP endpoints for services by fetching /openapi.json.

    Parameters:
      - timeout_sec: request timeout per base URL.
      - services_csv: optional comma-separated list of service names to include.
      - page, page_size: optional pagination over the selected service list.
      - base_urls_limit: limit how many base URLs per service are scanned and returned.
      - max_endpoints_per_service: truncate endpoint lists per service to this max.
      - include_endpoints: if False, omit heavy endpoint arrays; return counts/flags only.
      - only_policy_services: if True, restrict to services defined in policy.services

    Returns per service:
      - base_urls: candidate base URLs (possibly truncated)
      - openapi: map of base_url -> { ok, status, error?, endpoints? or endpoints_count, truncated? }
      - missing_openapi: true if none of the base URLs returned a valid spec

    Also returns:
      - violations: list of missing_openapi violations (policy services with exposed ports)
      - pagination: metadata when page_size is provided

    Note: New tools require restarting the MCP server process to appear in clients.
    """
    matrix = indexer.get_env_matrix() or {}
    policy = indexer.get_policy() or {}
    policy_services = set((policy.get("services") or {}).keys())

    def _extract_host_ports(ports: List) -> List[str]:
        host_ports: List[str] = []
        for p in ports or []:
            if isinstance(p, str):
                s = p.split("/")[0]
                parts = s.split(":")
                if len(parts) == 1:
                    host = parts[0]
                elif len(parts) == 2:
                    host = parts[0]
                else:
                    host = parts[-2]
                if host and host.isdigit():
                    host_ports.append(host)
            elif isinstance(p, dict):
                pub = p.get("published") or p.get("host_port") or p.get("published_port")
                if pub is not None:
                    host_ports.append(str(pub))
        return sorted({h for h in host_ports if h})

    def _extract_endpoints_from_spec(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        paths = spec.get("paths") or {}
        methods_set = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}
        endpoints: List[Dict[str, Any]] = []
        for route, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            for m, detail in methods.items():
                if m.lower() not in methods_set:
                    continue
                summary = None
                try:
                    summary = detail.get("summary") or (detail.get("description") or "").split("\n")[0]
                except Exception:
                    summary = None
                op_id = None
                try:
                    op_id = detail.get("operationId")
                except Exception:
                    op_id = None
                endpoints.append({
                    "method": m.upper(),
                    "path": route,
                    "summary": summary,
                    "operationId": op_id,
                })
        return endpoints

    # Determine service selection
    all_service_names = list(matrix.keys())
    policy_services = set((policy.get("services") or {}).keys())
    if only_policy_services:
        all_service_names = [n for n in all_service_names if n in policy_services]

    selected_set: Optional[set[str]] = None
    if services_csv and services_csv.strip():
        selected_set = {s.strip() for s in services_csv.split(",") if s.strip()}
    service_names = [n for n in sorted(all_service_names) if (selected_set is None or n in selected_set)]

    total_services = len(service_names)
    # Apply pagination
    if page_size is not None:
        try:
            page_i = max(1, int(page))
            size_i = max(1, int(page_size))
        except Exception:
            page_i, size_i = 1, int(page_size or 1)
        start = (page_i - 1) * size_i
        end = start + size_i
        page_names = service_names[start:end]
        pagination_meta = {
            "page": page_i,
            "page_size": size_i,
            "total_services": total_services,
            "has_more": end < total_services,
        }
    else:
        page_names = service_names
        pagination_meta = None

    services_out: Dict[str, Dict[str, Any]] = {}
    violations: List[Dict[str, str]] = []

    for name in page_names:
        info = matrix.get(name) or {}
        ports = info.get("ports") or []
        host_ports = _extract_host_ports(ports)
        base_urls_full = [f"http://localhost:{hp}" for hp in host_ports]
        base_urls = base_urls_full[: int(base_urls_limit)] if (base_urls_limit and base_urls_limit > 0) else base_urls_full

        openapi_results: Dict[str, Dict[str, Any]] = {}
        any_ok = False

        for base in base_urls:
            url = base.rstrip("/") + "/openapi.json"
            try:
                with httpx.Client(follow_redirects=True, timeout=timeout_sec) as client:
                    resp = client.get(url)
                status = resp.status_code
                if status == 200:
                    # Best-effort JSON parse
                    spec: Dict[str, Any] = {}
                    try:
                        spec = resp.json()
                    except Exception as e:
                        openapi_results[base] = {
                            "ok": False,
                            "status": status,
                            "error": f"invalid_json: {e}",
                        }
                        continue
                    endpoints = _extract_endpoints_from_spec(spec or {})
                    if max_endpoints_per_service and max_endpoints_per_service > 0 and len(endpoints) > max_endpoints_per_service:
                        truncated_list = endpoints[: int(max_endpoints_per_service)]
                        if include_endpoints:
                            openapi_results[base] = {
                                "ok": True,
                                "status": status,
                                "endpoints": truncated_list,
                                "endpoints_count": len(endpoints),
                                "truncated": True,
                            }
                        else:
                            openapi_results[base] = {
                                "ok": True,
                                "status": status,
                                "endpoints_count": len(endpoints),
                                "truncated": True,
                            }
                    else:
                        if include_endpoints:
                            openapi_results[base] = {
                                "ok": True,
                                "status": status,
                                "endpoints": endpoints,
                                "endpoints_count": len(endpoints),
                            }
                        else:
                            openapi_results[base] = {
                                "ok": True,
                                "status": status,
                                "endpoints_count": len(endpoints),
                            }
                    any_ok = True
                else:
                    openapi_results[base] = {
                        "ok": False,
                        "status": status,
                    }
            except Exception as e:
                openapi_results[base] = {
                    "ok": False,
                    "status": "exception",
                    "error": str(e),
                }

        # Only consider it a violation if:
        #  - the service is one of the project application services (per policy.services)
        #  - and it exposes at least one published port (HTTP-exposed)
        #  - and none of the base URLs provided a valid OpenAPI spec
        missing = (len(base_urls) > 0) and (not any_ok)
        if missing and (name in policy_services):
            violations.append({
                "type": "missing_openapi",
                "service": name,
                "message": f"Service '{name}' has no reachable /openapi.json on any exposed port.",
            })

        services_out[name] = {
            "base_urls": base_urls,
            "openapi": openapi_results,
            "missing_openapi": missing,
        }

    result: Dict[str, Any] = {"services": services_out, "violations": violations}
    if pagination_meta is not None:
        result["pagination"] = pagination_meta
    return result

def main() -> None:
    _maybe_start_auto_indexer()
    mcp.run()


if __name__ == "__main__":
    main()
