from __future__ import annotations

import os
import importlib
import time
from typing import Dict, List, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

# Import modules (not symbols) to support hot reload
from . import indexer as idx_mod
from . import validator as val_mod
from . import utils as util_mod
from . import auto_indexer as ai_mod

app = FastAPI(title="Optimus Project MCP", version="0.1.0")


# In-memory singletons
indexer = idx_mod.Indexer()
indexer.refresh()
validator = val_mod.Validator(indexer.get_policy())
auto_indexer: Optional[ai_mod.AutoIndexer] = None


def _perform_refresh() -> None:
    """Hot-reload modules, rebuild index, and reload validator policy."""
    global indexer, validator
    importlib.reload(util_mod)
    importlib.reload(idx_mod)
    importlib.reload(val_mod)
    indexer = idx_mod.Indexer()
    indexer.refresh()
    validator = val_mod.Validator(indexer.get_policy())


def _run_with_timeout(fn: Callable[[], Any], timeout_sec: float) -> Any:
    """Run a callable in a thread with a timeout. Raises TimeoutError on expiration."""
    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(fn)
        return fut.result(timeout=timeout_sec)


class PlanRequest(BaseModel):
    requirement: str


class ValidateRequest(BaseModel):
    diff: str


class PromptSaveRequest(BaseModel):
    name: str
    template: str


class PromptApplyRequest(BaseModel):
    name: str
    variables: Optional[Dict[str, Any]] = None


class PromptApplyKVRequest(BaseModel):
    name: str
    variables_kv: Optional[str] = None


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/refresh")
async def refresh() -> Dict[str, str]:
    t0 = time.perf_counter()
    try:
        await app.state.loop.run_in_executor(None, lambda: _run_with_timeout(_perform_refresh, 5.0))
        ok = True
        msg = "refreshed"
    except FuturesTimeout:
        ok = False
        msg = "refresh_timeout"
    dt_ms = int((time.perf_counter() - t0) * 1000)
    return {"status": msg, "duration_ms": str(dt_ms), "ok": str(ok).lower()}


@app.get("/api/system_overview")
async def system_overview() -> Dict:
    return indexer.get_system_overview()


@app.get("/api/service_contract/{service}")
async def service_contract(service: str) -> Dict:
    try:
        return indexer.get_service_contract(service)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service}")


@app.get("/api/env_matrix")
async def env_matrix() -> Dict[str, Dict]:
    return indexer.get_env_matrix()


@app.get("/api/service_urls")
async def service_urls() -> Dict:
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

    def _env_internal_urls(env_map: Dict[str, Any]) -> List[str]:
        urls: List[str] = []
        for v in (env_map or {}).values():
            try:
                if isinstance(v, str) and (v.startswith("http://") or v.startswith("https://")):
                    urls.append(v)
            except Exception:
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


@app.get("/api/open_file")
async def open_file(path: str = Query(..., description="Repository-relative path")) -> Dict[str, str]:
    try:
        content = util_mod.read_text(path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    return {"path": path, "content": content}


@app.get("/api/search")
async def code_search(q: str = Query(...), glob: Optional[str] = Query(None), limit: int = Query(100)) -> Dict:
    policy = indexer.get_policy()
    default_glob = (policy.get("search", {}) or {}).get("default_glob", "**/*")
    max_results = int((policy.get("search", {}) or {}).get("max_results", 100))
    results = util_mod.text_search(q, glob or default_glob, max_results=min(limit, max_results))
    return {"query": q, "results": results}


@app.post("/api/plan_change")
async def plan_change(req: PlanRequest) -> Dict:
    # Very lightweight planner using policy contracts
    pol = indexer.get_policy()
    services = pol.get("services", {})
    guidance: List[str] = []

    # High-level hints
    if any(k in req.requirement.lower() for k in ["database", "postgres", "schema", "migration", "alembic"]):
        guidance.append("All database read/write and migrations must be implemented in 'memory-engine/'. Other services must call its HTTP API.")
    if any(k in req.requirement.lower() for k in ["openai", "langchain", "llm", "embedding"]):
        guidance.append("LLM/LangChain usage is allowed in 'ai-engine/'. Avoid in 'backend-orchestrator/' and 'rules-engine/'.")
    if any(k in req.requirement.lower() for k in ["gateway", "entry", "handover", "webhook"]):
        guidance.append("Implement request routing/orchestration in 'backend-orchestrator/'. It must not handle DB nor LLM.")
    if any(k in req.requirement.lower() for k in ["rule", "business", "policy", "validation"]):
        guidance.append("Business rules live in 'rules-engine/'. It must call 'memory-engine/' for data, never DB directly.")

    guidance.append("Ensure multi-tenancy: never use 'public' schema; follow tenant-specific schemas (prefix 't_').")

    return {
        "requirement": req.requirement,
        "guidance": guidance,
        "service_contracts": services,
    }


# Prompts endpoints


@app.get("/api/prompts")
async def prompts_list() -> Dict:
    prompts = util_mod.load_prompts()
    return {"prompts": sorted(prompts.keys()), "count": len(prompts)}


@app.get("/api/prompts/{name}")
async def prompts_get(name: str) -> Dict:
    prompts = util_mod.load_prompts()
    if name not in prompts:
        raise HTTPException(status_code=404, detail=f"Unknown prompt: {name}")
    return {"name": name, "template": prompts[name]}


@app.post("/api/prompts")
async def prompts_set(body: PromptSaveRequest) -> Dict:
    prompts = util_mod.load_prompts()
    prompts[body.name] = body.template
    util_mod.save_prompts(prompts)
    return {"status": "saved", "name": body.name, "length": len(body.template)}


@app.delete("/api/prompts/{name}")
async def prompts_delete(name: str) -> Dict:
    prompts = util_mod.load_prompts()
    if name not in prompts:
        raise HTTPException(status_code=404, detail=f"Unknown prompt: {name}")
    del prompts[name]
    util_mod.save_prompts(prompts)
    return {"status": "deleted", "name": name}


@app.post("/api/prompts/apply")
async def prompts_apply(body: PromptApplyRequest) -> Dict:
    prompts = util_mod.load_prompts()
    if body.name not in prompts:
        raise HTTPException(status_code=404, detail=f"Unknown prompt: {body.name}")
    rendered = util_mod.render_prompt(prompts[body.name], body.variables or {})
    return {"name": body.name, "rendered": rendered}


@app.post("/api/prompts/apply_kv")
async def prompts_apply_kv(body: PromptApplyKVRequest) -> Dict:
    prompts = util_mod.load_prompts()
    if body.name not in prompts:
        raise HTTPException(status_code=404, detail=f"Unknown prompt: {body.name}")
    variables = util_mod.parse_kv_pairs(body.variables_kv)
    rendered = util_mod.render_prompt(prompts[body.name], variables)
    return {"name": body.name, "rendered": rendered}


@app.post("/api/validate_diff")
async def validate_diff(req: ValidateRequest) -> Dict:
    t0 = time.perf_counter()
    try:
        result = await app.state.loop.run_in_executor(None, lambda: _run_with_timeout(lambda: validator.validate_diff(req.diff), 8.0))
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


@app.on_event("startup")
async def _startup() -> None:
    """Start background auto-indexer to keep context fresh."""
    # Save loop to use with run_in_executor
    app.state.loop = getattr(app.state, 'loop', None) or __import__('asyncio').get_running_loop()
    enabled = (os.getenv("MCP_INDEXER_ENABLED", "true").strip().lower() in ("1", "true", "yes", "on"))
    if not enabled:
        return
    interval = float(os.getenv("MCP_INDEXER_INTERVAL", "1.0"))
    global auto_indexer
    auto_indexer = ai_mod.AutoIndexer(indexer, on_refresh=_perform_refresh, interval_sec=interval)
    auto_indexer.start()


@app.on_event("shutdown")
async def _shutdown() -> None:
    global auto_indexer
    if auto_indexer:
        auto_indexer.stop()
