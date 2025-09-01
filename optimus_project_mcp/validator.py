from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from .utils import parse_unified_diff, service_for_path


DB_URL_HINTS = (
    "postgresql://",
    "postgresql+asyncpg://",
    "postgres://",
)

MIGRATION_IMPORTS = ("alembic",)
MIGRATION_DIR_HINTS = ("migrations", "alembic")
SQL_PUBLIC_HINTS = (
    "schema=\"public\"",
    "schema='public'",
    ".schema('public')",
    "CREATE SCHEMA public",
    "DROP SCHEMA public",
)

SERVICE_NAME_RE = re.compile(r"^\s{0,6}([A-Za-z0-9_-]+):\s*$")
ENV_ASSIGN_RE = re.compile(r"^\s*-\s*([A-Za-z_][A-Za-z0-9_]*)\s*=")
ENV_DICT_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:")
INLINE_ENV_LIST_RE = re.compile(r"^\s*environment\s*:\s*\[(.*)\]\s*$")
INLINE_ENV_DICT_RE = re.compile(r"^\s*environment\s*:\s*\{(.*)\}\s*$")


@dataclass
class Violation:
    type: str
    message: str
    file: Optional[str] = None
    evidence: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "message": self.message,
            "file": self.file,
            "evidence": self.evidence,
        }


class Validator:
    def __init__(self, policy: Dict) -> None:
        self.policy = policy or {}
        self.services = self.policy.get("services", {})
        self.blocked_db_imports = set((self.policy.get("validator", {}) or {}).get("blocked_db_imports", []))
        self.blocked_llm_gateway = set((self.policy.get("validator", {}) or {}).get("blocked_llm_imports_gateway", []))
        self.compose_blocked_env = (self.policy.get("validator", {}) or {}).get("compose_blocked_env_for_services", {})
        self.migrations_allowed = set(self.policy.get("migrations_allowed_services", []))
        self.multi_forbidden = list((self.policy.get("multi_tenant", {}) or {}).get("forbidden_patterns", []))
        self._multi_forbidden_low = [p.lower() for p in self.multi_forbidden]
        vcfg = (self.policy.get("validator", {}) or {})
        self.sensitive_env_keys = set(vcfg.get("sensitive_env_keys_for_fallback", []))
        self.sqlalchemy_reserved = set(vcfg.get("reserved_sqlalchemy_identifiers", []))
        # Mock/placeholder data guardrails
        self.mock_forbidden_terms = [
            t.lower() for t in (vcfg.get("mock_data_forbidden_terms", [
                "use_mock", "mock", "fake", "placeholder", "stub", "dummy", "sample_data",
            ]) or [])
        ]
        self.mock_allowed_path_substrings = list(vcfg.get("mock_data_allowed_path_substrings", [
            "/tests/", "/test/", "/__tests__/", "/fixtures/", "/examples/", "/scripts/", "/migrations/",
        ]) or [])
        self.forbid_literal_return_in_except = bool(vcfg.get("forbid_literal_return_in_except", True))
        # Redis cache guardrails config
        rcfg = (vcfg.get("redis_cache", {}) or {})
        self.redis_ttl_required_outside_db = bool(rcfg.get("ttl_required_outside_db", True))
        self.redis_client_imports = list(rcfg.get("redis_client_imports", []))
        self.redis_invalidation_calls = list(rcfg.get("invalidation_calls", []))
        self.redis_db_write_hints = list(rcfg.get("db_write_hints", []))
        self.redis_disallowed_persistent_cmds_outside_db = list(rcfg.get("disallowed_persistent_cmds_outside_db", []))
        self.redis_key_prefix_per_service = (rcfg.get("key_prefix_per_service", {}) or {})

    def validate_diff(self, diff_text: str) -> Dict:
        changes = parse_unified_diff(diff_text or "")
        violations: List[Violation] = []
        for ch in changes:
            fpath = ch.get("file") or ""
            added = ch.get("added") or []
            svc = service_for_path(fpath)

            # Compose-specific checks: either explicitly listed in policy, a docker-compose*.yml/.yaml file, or compose.yml/yaml
            if (
                fpath in (self.policy.get("compose_files") or [])
                or ("docker-compose" in fpath and (fpath.endswith(".yml") or fpath.endswith(".yaml")))
                or os.path.basename(fpath) in ("compose.yml", "compose.yaml")
            ):
                violations.extend(self._check_compose_added_lines(fpath, added))
                continue

            # code checks
            violations.extend(self._check_blocked_imports(fpath, svc, added))
            violations.extend(self._check_blocked_db_urls(fpath, svc, added))
            violations.extend(self._check_migrations(fpath, svc, added))
            violations.extend(self._check_multi_tenant_sql(fpath, added))
            violations.extend(self._check_sqlalchemy_reserved(fpath, added))
            violations.extend(self._check_hardcoded_env_fallbacks(fpath, added))
            violations.extend(self._check_mock_data_usage(fpath, added))
            violations.extend(self._check_literal_return_in_except_or_catch(fpath, added))
            violations.extend(self._check_redis_usage(fpath, svc, added))

        return {
            "ok": len(violations) == 0,
            "violations": [v.to_dict() for v in violations],
        }

    # --- Checks ---
    def _check_blocked_imports(self, fpath: str, svc: Optional[str], added: List[str]) -> List[Violation]:
        out: List[Violation] = []
        if not svc:
            return out
        svc_rules = self.services.get(svc, {})
        blocked = set(svc_rules.get("blocked_imports", [])) | self.blocked_db_imports
        # gateway: add llm blocks
        if svc == "backend-orchestrator":
            blocked |= self.blocked_llm_gateway
        imp_from_re = re.compile(r"^from\s+([A-Za-z0-9_\.]+)\s+import\s+.+$")
        for line in added:
            line_stripped = line.strip()
            if line_stripped.startswith("import "):
                imports = line_stripped[len("import "):]
                for part in imports.split(","):
                    name = part.strip().split(" as ")[0].strip()
                    for mod in blocked:
                        if name == mod or name.startswith(mod + "."):
                            out.append(Violation(
                                type="blocked_import",
                                message=f"Import '{mod}' is not allowed in service '{svc}'.",
                                file=fpath,
                                evidence=line_stripped,
                            ))
                            break
            elif line_stripped.startswith("from "):
                m = imp_from_re.match(line_stripped)
                if m:
                    pkg = m.group(1)
                    for mod in blocked:
                        if pkg == mod or pkg.startswith(mod + "."):
                            out.append(Violation(
                                type="blocked_import",
                                message=f"Import '{mod}' is not allowed in service '{svc}'.",
                                file=fpath,
                                evidence=line_stripped,
                            ))
                            break
        return out
    def _check_sqlalchemy_reserved(self, fpath: str, added: List[str]) -> List[Violation]:
        """Detect problematic usage of SQLAlchemy reserved identifiers such as 'metadata'.

        Flags cases like:
          - metadata = ... (attribute overshadowing Base.metadata)
          - Column('metadata', ...)
          - Column(name="metadata", ...)
          - keyword 'metadata=' in SQLAlchemy constructs
        """
        out: List[Violation] = []
        if not fpath.endswith((".py", ".pyi")):
            return out
        reserved = {s.lower() for s in (self.sqlalchemy_reserved or [])}
        if not reserved:
            return out
        # Simple regexes to catch common anti-patterns
        col_name_literal_re = re.compile(r"Column\s*\(\s*(['\"])({names})\1\s*[,)\n]".format(names="|".join(map(re.escape, reserved))), re.IGNORECASE)
        kw_assign_re = re.compile(r"\b({names})\s*=".format(names="|".join(map(re.escape, reserved))), re.IGNORECASE)
        for line in added:
            low = line.lower()
            # attribute assignment like: metadata = ...
            if kw_assign_re.search(line):
                out.append(Violation(
                    type="sqlalchemy_reserved_identifier",
                    message="Use of reserved identifier (e.g., 'metadata') detected; rename to 'meta' or another name.",
                    file=fpath,
                    evidence=line.strip(),
                ))
                continue
            # Column('metadata', ...)
            if col_name_literal_re.search(line):
                out.append(Violation(
                    type="sqlalchemy_reserved_identifier",
                    message="Column named with reserved identifier (e.g., 'metadata'); use a different column/attr name like 'meta'.",
                    file=fpath,
                    evidence=line.strip(),
                ))
                continue
        return out

    def _check_hardcoded_env_fallbacks(self, fpath: str, added: List[str]) -> List[Violation]:
        """Detect hardcoded defaults in os.getenv()/os.environ.get() calls.

        Examples flagged:
          os.getenv("OPENAI_API_KEY", "abc")
          os.environ.get("DATABASE_URL", "postgres://...")

        If key is in sensitive_env_keys, any explicit default triggers a violation.
        Otherwise, string-literal defaults trigger a warning-level violation.
        """
        out: List[Violation] = []
        if not fpath.endswith((".py", ".pyi")):
            return out
        getv_re = re.compile(r"os\.getenv\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*,\s*([^\)]+)\)")
        envget_re = re.compile(r"os\.environ\.get\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*,\s*([^\)]+)\)")
        str_lit_re = re.compile(r"^\s*['\"].*['\"]\s*$")
        for line in added:
            m1 = getv_re.search(line)
            m2 = envget_re.search(line)
            if not m1 and not m2:
                continue
            m = m1 or m2
            key = (m.group(1) or "").strip()
            default_expr = (m.group(2) or "").strip()
            key_low = key.upper()
            is_sensitive = key_low in {k.upper() for k in self.sensitive_env_keys}
            is_string_literal = bool(str_lit_re.match(default_expr))
            if is_sensitive or is_string_literal:
                out.append(Violation(
                    type="hardcoded_env_fallback",
                    message=f"Avoid default value in getenv/environ.get for '{key}'. Require config and fail fast instead of hardcoding.",
                    file=fpath,
                    evidence=line.strip(),
                ))
        return out


    def _check_blocked_db_urls(self, fpath: str, svc: Optional[str], added: List[str]) -> List[Violation]:
        out: List[Violation] = []
        if not svc:
            return out
        svc_rules = self.services.get(svc, {})
        if svc_rules.get("allowed_db_access", False):
            return out
        for line in added:
            low = line.lower()
            if "database_url" in low or any(h in low for h in DB_URL_HINTS):
                out.append(Violation(
                    type="blocked_db_access",
                    message=f"Direct database URL/config detected in '{svc}', which is not allowed.",
                    file=fpath,
                    evidence=line.strip(),
                ))
        return out

    def _check_migrations(self, fpath: str, svc: Optional[str], added: List[str]) -> List[Violation]:
        out: List[Violation] = []
        if svc and svc in self.migrations_allowed:
            return out
        # directory hints
        if any(h in fpath for h in MIGRATION_DIR_HINTS):
            out.append(Violation(
                type="blocked_migration",
                message=f"Migrations are only allowed in services {sorted(self.migrations_allowed)}.",
                file=fpath,
                evidence=fpath,
            ))
            return out
        # import hints
        for line in added:
            if any(mi in line for mi in MIGRATION_IMPORTS):
                out.append(Violation(
                    type="blocked_migration",
                    message=f"Alembic/migration usage is restricted to {sorted(self.migrations_allowed)}.",
                    file=fpath,
                    evidence=line.strip(),
                ))
        return out

    def _check_multi_tenant_sql(self, fpath: str, added: List[str]) -> List[Violation]:
        out: List[Violation] = []
        for line in added:
            low = line.lower()
            for pat in self._multi_forbidden_low + [p.lower() for p in SQL_PUBLIC_HINTS]:
                if pat in low:
                    out.append(Violation(
                        type="multi_tenant_violation",
                        message="Forbidden reference to public schema or non-tenant-safe SQL detected.",
                        file=fpath,
                        evidence=line.strip(),
                    ))
                    break
        return out

    def _is_path_allowed_for_mock(self, fpath: str) -> bool:
        f_low = fpath.replace("\\", "/").lower()
        for sub in self.mock_allowed_path_substrings:
            if sub.lower() in f_low:
                return True
        # allow common test filename patterns
        base = os.path.basename(f_low)
        if base.startswith("test_") or base.endswith("_test.py") or ".spec." in base or ".test." in base:
            return True
        return False

    def _check_mock_data_usage(self, fpath: str, added: List[str]) -> List[Violation]:
        out: List[Violation] = []
        # Only check common runtime source files
        if not fpath.endswith((".py", ".js", ".ts", ".tsx")):
            return out
        if self._is_path_allowed_for_mock(fpath):
            return out
        # Build a regex for forbidden terms
        if not self.mock_forbidden_terms:
            return out
        terms = [re.escape(t) for t in self.mock_forbidden_terms]
        pat = re.compile(r"\b(" + "|".join(terms) + r")\b", re.IGNORECASE)
        for line in added:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            # Skip legitimate unittest.mock imports even in runtime files
            if "unittest.mock" in s.replace(" ", "") or s.startswith("from unittest import mock"):
                continue
            if pat.search(s):
                out.append(Violation(
                    type="mock_data_usage",
                    message="Detected mock/fake/placeholder data usage in runtime code. Do NOT use mock data; fail clearly or trigger handover.",
                    file=fpath,
                    evidence=s,
                ))
        return out

    def _check_literal_return_in_except_or_catch(self, fpath: str, added: List[str]) -> List[Violation]:
        out: List[Violation] = []
        if not self.forbid_literal_return_in_except:
            return out
        is_py = fpath.endswith((".py",))
        is_js = fpath.endswith((".js", ".ts", ".tsx"))
        if not (is_py or is_js):
            return out
        # scan a small window after an except/catch to catch literal returns
        lit_py = re.compile(r"^\s*return\s+(\{.*\}|\[.*\]|[\'\"].*[\'\"]|None|True|False|\d+)[\s#]*$")
        lit_js = re.compile(r"^\s*return\s+(\{.*\}|\[.*\]|[\'\"].*[\'\"]|null|true|false|\d+)[\s/]*.*$")
        for i, line in enumerate(added):
            ls = line.strip()
            if (is_py and (ls.startswith("except ") or ls == "except:")) or (is_js and ("catch(" in ls or ls.startswith("catch "))):
                # look ahead up to 6 lines
                for j in range(i + 1, min(i + 7, len(added))):
                    nxt = added[j].rstrip("\n")
                    if is_py and lit_py.match(nxt):
                        out.append(Violation(
                            type="silent_failure_literal_return",
                            message="Do not return literal values in except blocks. Raise a clear domain error or mark system offline/trigger handover.",
                            file=fpath,
                            evidence=nxt.strip(),
                        ))
                        break
                    if is_js and lit_js.match(nxt):
                        out.append(Violation(
                            type="silent_failure_literal_return",
                            message="Do not return literal values in catch blocks. Surface a clear user-facing outage and avoid mock data.",
                            file=fpath,
                            evidence=nxt.strip(),
                        ))
                        break
        return out

    def _check_redis_usage(self, fpath: str, svc: Optional[str], added: List[str]) -> List[Violation]:
        """Heuristics for Redis cache usage guardrails (diff-based, Python-oriented).

        - Enforce TTL on set operations outside DB-owning services.
        - Enforce namespaced literal keys per service.
        - Disallow persistent structures usage outside DB-owning services.
        - In DB-owning services, require cache invalidation calls near DB writes.
        """
        out: List[Violation] = []
        if not svc:
            return out
        is_py = fpath.endswith((".py", ".pyi"))
        if not is_py:
            return out
        svc_rules = self.services.get(svc, {}) or {}

        # Detect redis import hints to gate var-based heuristics and avoid false positives
        has_redis_import_hint = False
        clients = set(self.redis_client_imports or [])
        clients.update(["redis", "redis.asyncio", "aioredis"])
        for line in added:
            ls = line.strip()
            if any(ls.startswith(f"import {c}") or ls.startswith(f"from {c} ") for c in clients):
                has_redis_import_hint = True
                break

        # Collect likely client variables (very light heuristics)
        client_vars: set[str] = set()
        # Assignments like: client = redis.Redis(...), client = Redis(...), client = aioredis.from_url(...)
        assign_patterns = [
            re.compile(r"^\s*(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:[A-Za-z_][A-Za-z0-9_]*\.)?Redis\s*\("),
            re.compile(r"^\s*(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*aioredis\.(?:from_url|Redis)\s*\("),
            re.compile(r"^\s*(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*redis\.asyncio\.(?:from_url|Redis)\s*\("),
            re.compile(r"^\s*(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:[A-Za-z_][A-Za-z0-9_]*)\.pipeline\s*\("),
        ]
        call_var_re = re.compile(r"\b(?P<var>[A-Za-z_][A-Za-z0-9_]*)\.(?P<method>[A-Za-z_][A-Za-z0-9_]*)\s*\(")
        for line in added:
            for pat in assign_patterns:
                m = pat.match(line)
                if m:
                    client_vars.add(m.group("var"))
            # Also collect variables that are calling typical redis methods in this diff (when we have an import hint)
            if has_redis_import_hint:
                m2 = call_var_re.search(line.replace(" ", ""))
                if m2 and m2.group("method") in {"set","setex","psetex","hset","zadd","xadd","lpush","rpush","sadd","expire","pexpire","delete","unlink","publish"}:
                    client_vars.add(m2.group("var"))

        # TTL required for non-DB services
        if self.redis_ttl_required_outside_db and not svc_rules.get("allowed_db_access", False):
            # Check module-style and var-style calls
            for i, line in enumerate(added):
                s = line.strip()
                compact = s.replace(" ", "")
                # Module style: redis.set(...)
                if "redis." in compact and ".set(" in compact and "setex(" not in compact and "ex=" not in compact and "px=" not in compact:
                    # Accept TTL if immediate follow-up applies expire/pexpire/expireat
                    ttl_granted = False
                    for j in range(i + 1, min(i + 5, len(added))):
                        seg = added[j].replace(" ", "")
                        if ("redis.expire(" in seg or "redis.pexpire(" in seg or
                            "redis.expireat(" in seg or "redis.pexpireat(" in seg):
                            ttl_granted = True
                            break
                    if not ttl_granted:
                        out.append(Violation(
                            type="redis_ttl_required",
                            message=f"Service '{svc}' must set TTL when writing to Redis (use ex=/px=, setex, or expire immediately after set).",
                            file=fpath,
                            evidence=s,
                        ))
                    continue
                # Var style: <var>.set(...)
                m = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\.set\s*\(", s)
                if m:
                    var = m.group(1)
                    if has_redis_import_hint or var in client_vars:
                        if "setex(" in compact or "ex=" in compact or "px=" in compact:
                            continue
                        # Accept TTL if next few lines on same var call expire/pexpire
                        ttl_granted = False
                        for j in range(i + 1, min(i + 5, len(added))):
                            seg = added[j].replace(" ", "")
                            if (f"{var}.expire(" in seg or f"{var}.pexpire(" in seg or
                                f"{var}.expireat(" in seg or f"{var}.pexpireat(" in seg):
                                ttl_granted = True
                                break
                        if not ttl_granted:
                            out.append(Violation(
                                type="redis_ttl_required",
                                message=f"Service '{svc}' must set TTL when writing to Redis (use ex=/px=, setex, or expire immediately after set).",
                                file=fpath,
                                evidence=s,
                            ))

        # Namespaced literal keys (module and var styles)
        key_prefix = (self.redis_key_prefix_per_service.get(svc) or f"{svc}:")
        # Module style literal key
        mod_key_lit_re = re.compile(r"\bredis\.[A-Za-z_][A-Za-z0-9_]*\s*\(\s*[fFrRbBuU]*(['\"])([^'\"]+)\1")
        for line in added:
            m = mod_key_lit_re.search(line)
            if m:
                lit = m.group(2)
                if not lit.startswith(key_prefix):
                    out.append(Violation(
                        type="redis_key_not_namespaced",
                        message=f"Redis key should be namespaced with '{key_prefix}*' for service '{svc}'.",
                        file=fpath,
                        evidence=line.strip(),
                    ))
        # Var style literal key: for any detected client var
        if client_vars or has_redis_import_hint:
            for var in (client_vars or {"redis"}):
                vpat = re.compile(r"\b" + re.escape(var) + r"\.[A-Za-z_][A-Za-z0-9_]*\s*\(\s*[fFrRbBuU]*(['\"])([^'\"]+)\1")
                for line in added:
                    m = vpat.search(line)
                    if m:
                        lit = m.group(2)
                        if not lit.startswith(key_prefix):
                            out.append(Violation(
                                type="redis_key_not_namespaced",
                                message=f"Redis key should be namespaced with '{key_prefix}*' for service '{svc}'.",
                                file=fpath,
                                evidence=line.strip(),
                            ))

        # Disallow persistent structures outside DB-owning services
        if not svc_rules.get("allowed_db_access", False):
            cmds = set(self.redis_disallowed_persistent_cmds_outside_db or [])
            for line in added:
                compact = line.replace(" ", "")
                for cmd in cmds:
                    if f"redis.{cmd}(" in compact:
                        out.append(Violation(
                            type="redis_persistent_cmd_not_allowed",
                            message=f"Command '{cmd}' suggests persisting domain state in Redis. Use DB as SoT and cache with TTL only (service '{svc}').",
                            file=fpath,
                            evidence=line.strip(),
                        ))
                    # var style
                    m = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\." + re.escape(cmd) + r"\s*\(", line)
                    if m and (has_redis_import_hint or m.group(1) in client_vars):
                        out.append(Violation(
                            type="redis_persistent_cmd_not_allowed",
                            message=f"Command '{cmd}' suggests persisting domain state in Redis. Use DB as SoT and cache with TTL only (service '{svc}').",
                            file=fpath,
                            evidence=line.strip(),
                        ))

        # In DB-owning services, require cache invalidation near DB writes
        if svc_rules.get("allowed_db_access", False):
            hints = self.redis_db_write_hints or []
            inv_calls = list(self.redis_invalidation_calls or [])
            inv_extras = ["delete_many", "delete_pattern", "del_pattern", "invalidate", "clear"]
            inv_calls = sorted(set(inv_calls + inv_extras))
            mod_inv_patterns = [f"redis.{c}(" for c in inv_calls if c != "cache_invalidate"]
            for i, line in enumerate(added):
                if any(h in line for h in hints):
                    found_inv = False
                    # forward window
                    for j in range(i, min(i + 14, len(added))):
                        seg = added[j]
                        if any(p in seg for p in mod_inv_patterns) or ("cache_invalidate(" in seg):
                            found_inv = True
                            break
                        # var-based invalidations
                        vm = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s*\(", seg)
                        if vm and (has_redis_import_hint or vm.group(1) in client_vars) and vm.group(2) in inv_calls:
                            found_inv = True
                            break
                    if not found_inv:
                        out.append(Violation(
                            type="missing_cache_invalidation_after_db_write",
                            message=f"DB write detected in '{svc}' but no cache invalidation nearby; ensure redis.delete/expire or publish or cache_invalidate after commit.",
                            file=fpath,
                            evidence=line.strip(),
                        ))
                    # avoid spamming: only one violation per commit line
        return out

    def _check_compose_added_lines(self, fpath: str, added: List[str]) -> List[Violation]:
        out: List[Violation] = []
        current_service: Optional[str] = None
        service_indent: int = 0
        in_services: bool = False
        services_indent: int = 0
        in_env: bool = False
        env_indent: int = 0

        # Hints to detect DB URLs in values
        db_hints = tuple(DB_URL_HINTS)

        # Sets to improve parsing fidelity
        TOP_LEVEL_IGNORES = {"services", "version", "volumes", "networks", "configs", "secrets"}
        SERVICE_FIELD_IGNORES = {
            "image",
            "build",
            "command",
            "entrypoint",
            "environment",
            "env_file",
            "ports",
            "volumes",
            "depends_on",
            "restart",
            "healthcheck",
            "deploy",
            "labels",
            "container_name",
            "networks",
            "logging",
            "extra_hosts",
            "user",
            "working_dir",
            "secrets",
            "configs",
            "expose",
            "stop_grace_period",
            "stop_signal",
            "ulimits",
            "cap_add",
            "cap_drop",
            "privileged",
        }

        def indent_of(s: str) -> int:
            return len(s) - len(s.lstrip(" "))

        def extract_db_from_redis_url(url: str) -> Optional[int]:
            u = (url or "").strip().strip('"').strip("'")
            m = re.search(r"redis(?:s)?://[^\s]*?/(\d+)", u)
            if m:
                try:
                    return int(m.group(1))
                except Exception:
                    return None
            m2 = re.search(r"(?:\?|&)db=(\d+)", u)
            if m2:
                try:
                    return int(m2.group(1))
                except Exception:
                    return None
            return None

        for raw in added:
            line = raw.rstrip("\n")

            # Enter services block
            if re.match(r"^\s*services:\s*$", line):
                in_services = True
                services_indent = indent_of(line)
                current_service = None
                in_env = False
                continue

            if in_services:
                ind = indent_of(line)
                # Leave services block on dedent to same or less indent
                if line.strip() and not line.strip().startswith("#") and ind <= services_indent:
                    in_services = False
                    current_service = None
                    in_env = False
                    # continue to process other top-level sections
                # Detect any YAML key line
                m_key = re.match(r"^\s*([A-Za-z0-9_-]+):\s*$", line)
                if m_key:
                    key = m_key.group(1)
                    # Skip top-level meta sections and extension fields
                    if key in TOP_LEVEL_IGNORES or key.startswith("x-"):
                        current_service = None
                        in_env = False
                        continue
                    # Inside services block
                    if ind > services_indent:
                        if current_service is None:
                            # First service detected
                            current_service = key
                            service_indent = ind
                            in_env = False
                            continue
                        # New service header at same indent as previous service
                        if ind == service_indent:
                            current_service = key
                            in_env = False
                            continue
                        # Field under current service
                        if ind > service_indent:
                            if key in SERVICE_FIELD_IGNORES:
                                # Flag env_file usage as a warning: it can hide DB URLs in external files
                                if key == "env_file":
                                    svc_rules = self.services.get(current_service, {}) or {}
                                    if not svc_rules.get("allowed_db_access", False):
                                        out.append(Violation(
                                            type="compose_env_file_added",
                                            message=f"'env_file' added under service '{current_service}'. External env files may conceal DB URLs; this service cannot own DB configs.",
                                            file=fpath,
                                            evidence=line.strip(),
                                        ))
                                in_env = (key == "environment")
                            else:
                                # Unknown field: still considered under current service
                                in_env = False
                            continue

            if not current_service:
                continue

            # Compute blocked env set for the current service
            blocked_service_vars = set((self.services.get(current_service, {}) or {}).get("blocked_env_vars", []))
            blocked_compose_vars = set(self.compose_blocked_env.get(current_service, []))
            blocked_all = blocked_service_vars | blocked_compose_vars
            svc_rules = self.services.get(current_service, {}) or {}

            # Inline environment syntax on a single line (list or dict)
            # environment: ["KEY=VALUE", "FOO=bar"]
            m_inline_list = INLINE_ENV_LIST_RE.match(line)
            if m_inline_list:
                inner = m_inline_list.group(1)
                items = [tok.strip() for tok in inner.split(",") if tok.strip()]
                blocked_service_vars = set((self.services.get(current_service, {}) or {}).get("blocked_env_vars", []))
                blocked_compose_vars = set(self.compose_blocked_env.get(current_service, []))
                blocked_all = blocked_service_vars | blocked_compose_vars
                svc_rules = self.services.get(current_service, {}) or {}
                for it in items:
                    t = it.strip().strip('"').strip("'")
                    if "=" in t:
                        k, v = t.split("=", 1)
                    else:
                        k, v = t, ""
                    if k in blocked_all:
                        out.append(Violation(
                            type="compose_blocked_env",
                            message=f"Environment variable '{k}' is not allowed for service '{current_service}'.",
                            file=fpath,
                            evidence=line.strip(),
                        ))
                    if not svc_rules.get("allowed_db_access", False) and any(h in v.lower() for h in db_hints):
                        out.append(Violation(
                            type="compose_blocked_db_access",
                            message=f"Database URL detected in environment for service '{current_service}', which is not allowed.",
                            file=fpath,
                            evidence=line.strip(),
                        ))
                    # Enforce Redis DB mapping from policy
                    expected_db = (svc_rules.get("redis_db") if svc_rules is not None else None)
                    if expected_db is not None:
                        try:
                            expected_db_int = int(str(expected_db))
                        except Exception:
                            expected_db_int = None
                        key_up = (k or "").strip().upper()
                        if key_up.endswith("REDIS_DB") and expected_db_int is not None:
                            try:
                                actual = int(str(v).strip())
                            except Exception:
                                actual = None
                            if actual is not None and actual != expected_db_int:
                                out.append(Violation(
                                    type="compose_redis_db_mismatch",
                                    message=f"Service '{current_service}' must use REDIS_DB={expected_db_int} per policy.",
                                    file=fpath,
                                    evidence=line.strip(),
                                ))
                        if key_up.endswith("REDIS_URL") and expected_db_int is not None:
                            actual = extract_db_from_redis_url(v)
                            if actual is not None and actual != expected_db_int:
                                out.append(Violation(
                                    type="compose_redis_url_db_mismatch",
                                    message=f"Service '{current_service}' REDIS_URL must reference DB {expected_db_int} per policy.",
                                    file=fpath,
                                    evidence=line.strip(),
                                ))
                continue

            # environment: { KEY: value, FOO: bar }
            m_inline_dict = INLINE_ENV_DICT_RE.match(line)
            if m_inline_dict:
                inner = m_inline_dict.group(1)
                pairs = [tok.strip() for tok in inner.split(",") if tok.strip()]
                blocked_service_vars = set((self.services.get(current_service, {}) or {}).get("blocked_env_vars", []))
                blocked_compose_vars = set(self.compose_blocked_env.get(current_service, []))
                blocked_all = blocked_service_vars | blocked_compose_vars
                svc_rules = self.services.get(current_service, {}) or {}
                for pr in pairs:
                    if ":" not in pr:
                        continue
                    k, v = pr.split(":", 1)
                    k = k.strip().strip('"').strip("'")
                    v = v.strip().strip('"').strip("'")
                    if k in blocked_all:
                        out.append(Violation(
                            type="compose_blocked_env",
                            message=f"Environment variable '{k}' is not allowed for service '{current_service}'.",
                            file=fpath,
                            evidence=line.strip(),
                        ))
                    if not svc_rules.get("allowed_db_access", False) and any(h in v.lower() for h in db_hints):
                        out.append(Violation(
                            type="compose_blocked_db_access",
                            message=f"Database URL detected in environment for service '{current_service}', which is not allowed.",
                            file=fpath,
                            evidence=line.strip(),
                        ))
                    # Enforce Redis DB mapping from policy
                    expected_db = (svc_rules.get("redis_db") if svc_rules is not None else None)
                    if expected_db is not None:
                        try:
                            expected_db_int = int(str(expected_db))
                        except Exception:
                            expected_db_int = None
                        key_up = (k or "").strip().upper()
                        if key_up.endswith("REDIS_DB") and expected_db_int is not None:
                            try:
                                actual = int(str(v).strip())
                            except Exception:
                                actual = None
                            if actual is not None and actual != expected_db_int:
                                out.append(Violation(
                                    type="compose_redis_db_mismatch",
                                    message=f"Service '{current_service}' must use REDIS_DB={expected_db_int} per policy.",
                                    file=fpath,
                                    evidence=line.strip(),
                                ))
                        if key_up.endswith("REDIS_URL") and expected_db_int is not None:
                            actual = extract_db_from_redis_url(v)
                            if actual is not None and actual != expected_db_int:
                                out.append(Violation(
                                    type="compose_redis_url_db_mismatch",
                                    message=f"Service '{current_service}' REDIS_URL must reference DB {expected_db_int} per policy.",
                                    file=fpath,
                                    evidence=line.strip(),
                                ))
                continue

            # Start/stop of environment block
            if re.match(r"^\s*environment\s*:\s*$", line):
                in_env = True
                env_indent = indent_of(line)
                continue
            if in_env and line.strip() and indent_of(line) <= env_indent:
                in_env = False

            if not in_env:
                continue

            # list style: - KEY=VALUE
            m_list = ENV_ASSIGN_RE.match(line)
            if m_list:
                key = m_list.group(1)
                value = line.split("=", 1)[1].strip() if "=" in line else ""
                if key in blocked_all:
                    out.append(Violation(
                        type="compose_blocked_env",
                        message=f"Environment variable '{key}' is not allowed for service '{current_service}'.",
                        file=fpath,
                        evidence=line.strip(),
                    ))
                if not svc_rules.get("allowed_db_access", False) and any(h in value.lower() for h in db_hints):
                    out.append(Violation(
                        type="compose_blocked_db_access",
                        message=f"Database URL detected in environment for service '{current_service}', which is not allowed.",
                        file=fpath,
                        evidence=line.strip(),
                    ))
                # Enforce Redis DB mapping from policy
                expected_db = (svc_rules.get("redis_db") if svc_rules is not None else None)
                if expected_db is not None:
                    try:
                        expected_db_int = int(str(expected_db))
                    except Exception:
                        expected_db_int = None
                    key_up = (key or "").strip().upper()
                    if key_up.endswith("REDIS_DB") and expected_db_int is not None:
                        try:
                            actual = int(value.strip('"').strip("'"))
                        except Exception:
                            actual = None
                        if actual is not None and actual != expected_db_int:
                            out.append(Violation(
                                type="compose_redis_db_mismatch",
                                message=f"Service '{current_service}' must use REDIS_DB={expected_db_int} per policy.",
                                file=fpath,
                                evidence=line.strip(),
                            ))
                    if key_up.endswith("REDIS_URL") and expected_db_int is not None:
                        actual = extract_db_from_redis_url(value)
                        if actual is not None and actual != expected_db_int:
                            out.append(Violation(
                                type="compose_redis_url_db_mismatch",
                                message=f"Service '{current_service}' REDIS_URL must reference DB {expected_db_int} per policy.",
                                file=fpath,
                                evidence=line.strip(),
                            ))
                continue

            # dict style inside environment: KEY: value
            m_dict = ENV_DICT_RE.match(line)
            if m_dict:
                key = m_dict.group(1)
                value = line.split(":", 1)[1].strip() if ":" in line else ""
                if key in blocked_all:
                    out.append(Violation(
                        type="compose_blocked_env",
                        message=f"Environment variable '{key}' is not allowed for service '{current_service}'.",
                        file=fpath,
                        evidence=line.strip(),
                    ))
                if not svc_rules.get("allowed_db_access", False) and any(h in value.lower() for h in db_hints):
                    out.append(Violation(
                        type="compose_blocked_db_access",
                        message=f"Database URL detected in environment for service '{current_service}', which is not allowed.",
                        file=fpath,
                        evidence=line.strip(),
                    ))
                # Enforce Redis DB mapping from policy
                expected_db = (svc_rules.get("redis_db") if svc_rules is not None else None)
                if expected_db is not None:
                    try:
                        expected_db_int = int(str(expected_db))
                    except Exception:
                        expected_db_int = None
                    key_up = (key or "").strip().upper()
                    if key_up.endswith("REDIS_DB") and expected_db_int is not None:
                        try:
                            actual = int(value.strip('"').strip("'"))
                        except Exception:
                            actual = None
                        if actual is not None and actual != expected_db_int:
                            out.append(Violation(
                                type="compose_redis_db_mismatch",
                                message=f"Service '{current_service}' must use REDIS_DB={expected_db_int} per policy.",
                                file=fpath,
                                evidence=line.strip(),
                            ))
                    if key_up.endswith("REDIS_URL") and expected_db_int is not None:
                        actual = extract_db_from_redis_url(value)
                        if actual is not None and actual != expected_db_int:
                            out.append(Violation(
                                type="compose_redis_url_db_mismatch",
                                message=f"Service '{current_service}' REDIS_URL must reference DB {expected_db_int} per policy.",
                                file=fpath,
                                evidence=line.strip(),
                            ))
        return out
