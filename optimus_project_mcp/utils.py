from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Any
import shlex

import yaml

# Paths


def get_repo_root() -> Path:
    # repo_root/mcp_servers/optimus_project_mcp/utils.py -> repo_root
    return Path(__file__).resolve().parents[2]


def safe_join_repo(rel_path: str) -> Path:
    root = get_repo_root()
    p = (root / rel_path).resolve()
    if not str(p).startswith(str(root.resolve())):
        raise ValueError("Path escapes repository root")
    return p


# IO helpers


def read_text(rel_path: str, max_bytes: int = 2_000_000) -> str:
    p = safe_join_repo(rel_path)
    if not p.exists():
        raise FileNotFoundError(rel_path)
    data = p.read_bytes()
    if len(data) > max_bytes:
        return data[:max_bytes].decode(errors="ignore") + "\n... [truncated]"
    return data.decode(errors="ignore")


def load_yaml_file(rel_path: str) -> Dict:
    p = safe_join_repo(rel_path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_yaml_file(rel_path: str, data: Dict) -> None:
    p = safe_join_repo(rel_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data or {}, f, sort_keys=True, allow_unicode=True)


# Search


def iter_files_by_glob(glob_pattern: str) -> Iterable[Path]:
    root = get_repo_root()
    # support comma-separated patterns
    patterns = [g.strip() for g in glob_pattern.split(",") if g.strip()]
    if not patterns:
        patterns = ["**/*"]
    for pat in patterns:
        yield from root.glob(pat)


def text_search(query: str, glob_pattern: str, max_results: int = 100) -> List[Dict]:
    query_lower = query.lower()
    results: List[Dict] = []
    seen: set[str] = set()
    for path in iter_files_by_glob(glob_pattern):
        if len(results) >= max_results:
            break
        if path.is_dir():
            continue
        # skip binary-ish files
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".pdf", ".gif", ".heic", ".webp"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if query_lower in text.lower():
            rel = str(path.relative_to(get_repo_root()))
            if rel in seen:
                continue
            # capture first occurrence snippet
            idx = text.lower().find(query_lower)
            start = max(0, idx - 160)
            end = min(len(text), idx + 160)
            snippet = text[start:end]
            results.append({
                "path": rel,
                "snippet": snippet,
            })
            seen.add(rel)
    return results


# Compose helpers


def load_compose(rel_path: str) -> Dict:
    return load_yaml_file(rel_path)


def merge_compose_services(base: Dict, overlay: Dict) -> Dict:
    """Shallow merge of services: overlay wins."""
    merged = {k: v for k, v in base.items()}
    if not overlay:
        return merged
    for name, svc in (overlay.get("services") or {}).items():
        b_services = merged.setdefault("services", {})
        b = b_services.get(name, {})
        # shallow dict merge
        new = {**b, **svc}
        b_services[name] = new
    return merged


def extract_env_from_service(svc: Dict) -> Dict[str, Optional[str]]:
    env_map: Dict[str, Optional[str]] = {}
    env = svc.get("environment")
    if isinstance(env, list):
        # e.g., ["FOO=bar", "BAZ"]
        for item in env:
            if isinstance(item, str):
                if "=" in item:
                    k, v = item.split("=", 1)
                    env_map[k] = v
                else:
                    env_map[item] = None
    elif isinstance(env, dict):
        env_map.update({str(k): (None if v is None else str(v)) for k, v in env.items()})
    return env_map


def read_file_if_exists(path: Path, max_bytes: int = 1_000_000) -> Optional[str]:
    if path.exists() and path.is_file():
        try:
            data = path.read_bytes()
            return data[:max_bytes].decode(errors="ignore")
        except Exception:
            return None
    return None


# Diff parsing

HUNK_FILE_RE = re.compile(r"^\+\+\+\s+b/(.+)$")
HUNK_FILE_OLD_RE = re.compile(r"^---\s+a/(.+)$")


def parse_unified_diff(diff_text: str) -> List[Dict]:
    """Parse a unified diff into a list of file change dicts with added lines only."""
    changes: List[Dict] = []
    current: Optional[Dict] = None
    for line in diff_text.splitlines():
        if line.startswith("diff "):
            if current:
                changes.append(current)
            current = None
        elif line.startswith("--- "):
            # old file
            m = HUNK_FILE_OLD_RE.match(line)
            if m:
                # keep old if needed
                pass
        elif line.startswith("+++ "):
            m = HUNK_FILE_RE.match(line)
            if m:
                if current:
                    changes.append(current)
                current = {"file": m.group(1), "added": [], "removed": []}
        elif line.startswith("+") and not line.startswith("+++"):
            if current is not None:
                current["added"].append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            if current is not None:
                current["removed"].append(line[1:])
    if current:
        changes.append(current)
    return changes


# Mapping service <-> directory
SERVICE_DIR_MAP = {
    "ai-engine": "ai-engine",
    "backend-orchestrator": "backend-orchestrator",
    "memory-engine": "memory-engine",
    "rules-engine": "rules_engine",  # repo dir uses underscore
}


def service_for_path(rel_path: str) -> Optional[str]:
    # Normalize path
    rel_path = rel_path.lstrip("./")
    for svc, d in SERVICE_DIR_MAP.items():
        if rel_path.startswith(f"{d}/"):
            return svc
    return None


# Prompts utilities


PROMPTS_REL_PATH = "mcp_servers/optimus_project_mcp/prompts.yaml"


def load_prompts() -> Dict[str, str]:
    """Load prompts from repo prompts.yaml. Accepts either top-level map or {'prompts': {...}}."""
    data = load_yaml_file(PROMPTS_REL_PATH)
    raw = data.get("prompts") if isinstance(data, dict) else None
    if isinstance(raw, dict):
        src = raw
    elif isinstance(data, dict):
        src = data
    else:
        src = {}
    prompts: Dict[str, str] = {}
    for k, v in (src or {}).items():
        try:
            key = str(k)
            val = "" if v is None else str(v)
        except Exception:
            continue
        prompts[key] = val
    return prompts


def save_prompts(prompts: Dict[str, str]) -> None:
    save_yaml_file(PROMPTS_REL_PATH, {"prompts": dict(sorted(prompts.items()))})


def render_prompt(template: str, variables: Optional[Dict[str, Any]] = None) -> str:
    variables = variables or {}
    try:
        return template.format(**variables)
    except Exception:
        return template


def parse_kv_pairs(kv: Optional[str]) -> Dict[str, str]:
    """Parse a shell-like 'k=v k2="v 2"' string into a dict. Ignores tokens without '='."""
    if not kv:
        return {}
    out: Dict[str, str] = {}
    try:
        tokens = shlex.split(kv)
    except Exception:
        tokens = kv.split()
    for tok in tokens:
        if "=" not in tok:
            continue
        k, v = tok.split("=", 1)
        if k:
            out[k] = v
    return out
