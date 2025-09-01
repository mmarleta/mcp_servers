from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .utils import (
    get_repo_root,
    load_yaml_file,
    load_compose,
    merge_compose_services,
    extract_env_from_service,
    read_text,
    iter_files_by_glob,
)


class Indexer:
    def __init__(self) -> None:
        self.repo_root: Path = get_repo_root()
        self.policy_path = self.repo_root / "mcp_servers/optimus_project_mcp/policy.yaml"
        self.policy: Dict = {}
        self.docs: Dict[str, str] = {}
        self.compose_merged: Dict = {}
        self.env_matrix: Dict[str, Dict] = {}

    # Public API
    def refresh(self) -> None:
        self._load_policy()
        self._load_docs()
        self._load_compose_and_envs()

    def get_policy(self) -> Dict:
        return self.policy

    def get_system_overview(self) -> Dict:
        return {
            "docs": self.docs,
            "compose_services": list((self.compose_merged.get("services") or {}).keys()),
        }

    def get_service_contract(self, service: str) -> Dict:
        svc = (self.policy.get("services") or {}).get(service)
        if not svc:
            raise KeyError(f"Unknown service: {service}")
        return svc

    def get_env_matrix(self) -> Dict[str, Dict]:
        return self.env_matrix

    # Internals
    def _load_policy(self) -> None:
        self.policy = load_yaml_file(str(self.policy_path.relative_to(self.repo_root)))

    def _load_docs(self) -> None:
        self.docs = {}
        for rel in self.policy.get("docs_files", []):
            try:
                self.docs[rel] = read_text(rel)
            except FileNotFoundError:
                self.docs[rel] = ""

    def _load_compose_and_envs(self) -> None:
        merged: Dict = {}
        compose_specs: List[str] = self.policy.get("compose_files", [])
        # Expand globs to actual file paths relative to repo root
        expanded: List[str] = []
        for spec in compose_specs:
            # If spec looks like a glob, expand; otherwise include as-is
            if any(ch in spec for ch in ["*", "?", "["]):
                for p in iter_files_by_glob(spec):
                    if p.is_file():
                        expanded.append(str(p.relative_to(self.repo_root)))
            else:
                expanded.append(spec)
        # Deduplicate and sort for deterministic merge order
        seen: set[str] = set()
        ordered_files: List[str] = []
        for rel in sorted(expanded):
            if rel in seen:
                continue
            seen.add(rel)
            ordered_files.append(rel)
        for i, rel in enumerate(ordered_files):
            file_data = load_compose(rel)
            if i == 0:
                merged = file_data or {}
            else:
                merged = merge_compose_services(merged or {}, file_data or {})
        self.compose_merged = merged or {}
        self._build_env_matrix()

    def _build_env_matrix(self) -> None:
        envs: Dict[str, Dict] = {}
        services: Dict = (self.compose_merged.get("services") or {})
        policy_services: Dict = self.policy.get("services", {})
        for name, svc in services.items():
            env_map = extract_env_from_service(svc or {})
            blocked_envs = set((policy_services.get(name, {}) or {}).get("blocked_env_vars", []))
            present_blocked = [k for k in sorted(env_map.keys()) if k in blocked_envs]
            envs[name] = {
                "env": env_map,
                "blocked_present": present_blocked,
                "ports": svc.get("ports", []),
                "depends_on": svc.get("depends_on"),
            }
        self.env_matrix = envs
