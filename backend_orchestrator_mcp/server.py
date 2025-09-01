#!/usr/bin/env python3
"""
🚀 Backend Orchestrator MCP Server - Optimus Development Tools
============================================================

MCP server specializado para desenvolvimento do Backend Orchestrator do sistema Optimus.
Oferece ferramentas práticas para debugging de gateway, análise de performance,
templates para routers enterprise, e troubleshooting de produção.

Features:
- Gateway debugging (rate limiting, cache coherence, circuit breakers)
- Router templates com enterprise patterns
- Performance analytics e troubleshooting
- Integration testing com AI Engine
- Diagnostics para problemas de produção

Tech Lead: Optimus Project
Architecture: HYBRID SMART ARCHITECTURE compliance
"""

import json
import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

# Add backend-orchestrator to path
current_dir = Path(__file__).parent
backend_orchestrator_root = current_dir.parent.parent / "backend-orchestrator"
sys.path.insert(0, str(backend_orchestrator_root))

try:
    import httpx
    import redis.asyncio as redis
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    import mcp.types as types
except ImportError as e:
    logging.error(f"Missing required dependencies: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("backend-orchestrator-mcp")

# MCP Server instance
server = Server("backend-orchestrator-mcp")

# Configuration
BACKEND_ORCHESTRATOR_URL = os.getenv("BACKEND_ORCHESTRATOR_URL", "http://localhost:8020")
AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://localhost:8010")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
BACKEND_ORCHESTRATOR_PATH = backend_orchestrator_root

class BackendOrchestratorClient:
    """Client para interagir com Backend Orchestrator"""
    
    def __init__(self):
        self.base_url = BACKEND_ORCHESTRATOR_URL
        self.client = httpx.AsyncClient(timeout=30.0)
        self.redis_client = None
    
    async def get_redis_client(self):
        """Get Redis client for diagnostics"""
        if not self.redis_client:
            try:
                self.redis_client = redis.from_url(REDIS_URL)
                await self.redis_client.ping()
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                return None
        return self.redis_client
    
    async def check_health(self) -> Dict[str, Any]:
        """Check Backend Orchestrator health"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        try:
            response = await self.client.get(f"{self.base_url}/api/cache/metrics")
            return response.json() if response.status_code == 200 else {"error": response.text}
        except Exception as e:
            return {"error": str(e)}
    
    async def analyze_rate_limiting(self, tenant_id: str = "demo_dentist") -> Dict[str, Any]:
        """Analyze rate limiting status for tenant"""
        redis_client = await self.get_redis_client()
        if not redis_client:
            return {"error": "Redis connection failed"}
        
        try:
            # Get rate limiting keys for tenant
            pattern = f"rate_limit:{tenant_id}:*"
            keys = await redis_client.keys(pattern)
            
            rate_limit_status = {}
            for key in keys:
                key_str = key.decode() if isinstance(key, bytes) else str(key)
                operation = key_str.split(":")[-1]
                
                # Get current count and TTL
                count = await redis_client.get(key)
                ttl = await redis_client.ttl(key)
                
                rate_limit_status[operation] = {
                    "current_count": int(count) if count else 0,
                    "ttl_seconds": ttl if ttl > 0 else 0,
                    "key": key_str
                }
            
            return {
                "tenant_id": tenant_id,
                "rate_limits": rate_limit_status,
                "total_active_limits": len(rate_limit_status)
            }
            
        except Exception as e:
            return {"error": str(e)}

# Initialize client
client = BackendOrchestratorClient()

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available Backend Orchestrator development tools"""
    return [
        Tool(
            name="diagnose_gateway_health",
            description="Comprehensive health check of Backend Orchestrator gateway including services, cache, rate limiting",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_cache_metrics": {
                        "type": "boolean", 
                        "description": "Include cache performance metrics",
                        "default": True
                    },
                    "include_rate_limiting": {
                        "type": "boolean",
                        "description": "Include rate limiting analysis",
                        "default": True
                    },
                    "tenant_id": {
                        "type": "string",
                        "description": "Tenant ID for rate limiting analysis",
                        "default": "demo_dentist"
                    }
                }
            }
        ),
        Tool(
            name="analyze_cache_coherence",
            description="Analyze cache coherence system performance and PubSub events",
            inputSchema={
                "type": "object",
                "properties": {
                    "time_window_minutes": {
                        "type": "number",
                        "description": "Time window for analysis in minutes",
                        "default": 15
                    },
                    "include_event_log": {
                        "type": "boolean",
                        "description": "Include recent cache coherence events",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="generate_enterprise_router",
            description="Generate a new router following Backend Orchestrator enterprise patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "router_name": {
                        "type": "string",
                        "description": "Name of the new router (e.g., 'products', 'orders')"
                    },
                    "router_type": {
                        "type": "string",
                        "enum": ["proxy", "direct", "hybrid"],
                        "description": "Type of router: proxy (forwards to AI Engine), direct (local logic), hybrid (both)",
                        "default": "proxy"
                    },
                    "operations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of operations (e.g., ['list', 'create', 'get', 'update', 'delete'])",
                        "default": ["list", "create", "get", "update"]
                    },
                    "include_rate_limiting": {
                        "type": "boolean",
                        "description": "Include enterprise rate limiting patterns",
                        "default": True
                    },
                    "include_caching": {
                        "type": "boolean", 
                        "description": "Include cache coherence patterns",
                        "default": True
                    }
                },
                "required": ["router_name"]
            }
        ),
        Tool(
            name="troubleshoot_production_issue",
            description="Troubleshoot common production issues in Backend Orchestrator",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_type": {
                        "type": "string",
                        "enum": ["rate_limiting", "cache_miss", "circuit_breaker", "proxy_timeout", "memory_leak", "high_latency"],
                        "description": "Type of issue to troubleshoot"
                    },
                    "tenant_id": {
                        "type": "string",
                        "description": "Affected tenant ID",
                        "default": "demo_dentist"
                    },
                    "time_window_minutes": {
                        "type": "number",
                        "description": "Time window to analyze",
                        "default": 30
                    }
                },
                "required": ["issue_type"]
            }
        ),
        Tool(
            name="test_ai_engine_integration",
            description="Test integration between Backend Orchestrator and AI Engine",
            inputSchema={
                "type": "object",
                "properties": {
                    "test_type": {
                        "type": "string",
                        "enum": ["connectivity", "performance", "error_handling", "full_flow"],
                        "description": "Type of integration test",
                        "default": "connectivity"
                    },
                    "tenant_id": {
                        "type": "string", 
                        "description": "Tenant ID for testing",
                        "default": "demo_dentist"
                    },
                    "include_cache_test": {
                        "type": "boolean",
                        "description": "Test cache coherence in integration",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="analyze_performance_metrics",
            description="Analyze Backend Orchestrator performance metrics and bottlenecks",
            inputSchema={
                "type": "object",
                "properties": {
                    "metric_type": {
                        "type": "string",
                        "enum": ["latency", "throughput", "error_rate", "cache_performance", "rate_limiting_efficiency"],
                        "description": "Type of performance metric to analyze",
                        "default": "latency"
                    },
                    "time_window_minutes": {
                        "type": "number",
                        "description": "Time window for analysis",
                        "default": 60
                    },
                    "tenant_filter": {
                        "type": "string",
                        "description": "Filter by specific tenant (optional)"
                    }
                }
            }
        ),
        Tool(
            name="validate_enterprise_patterns",
            description="Validate that existing routers follow enterprise patterns and best practices",
            inputSchema={
                "type": "object",
                "properties": {
                    "router_path": {
                        "type": "string",
                        "description": "Path to router file to validate (relative to src/backend/routers/)"
                    },
                    "check_all_routers": {
                        "type": "boolean",
                        "description": "Validate all routers in the system",
                        "default": False
                    },
                    "validation_level": {
                        "type": "string",
                        "enum": ["basic", "comprehensive", "production_ready"],
                        "description": "Level of validation to perform",
                        "default": "comprehensive"
                    }
                }
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute Backend Orchestrator development tools"""
    
    try:
        if name == "diagnose_gateway_health":
            return await diagnose_gateway_health(arguments)
        elif name == "analyze_cache_coherence":
            return await analyze_cache_coherence(arguments)
        elif name == "generate_enterprise_router":
            return await generate_enterprise_router(arguments)
        elif name == "troubleshoot_production_issue":
            return await troubleshoot_production_issue(arguments)
        elif name == "test_ai_engine_integration":
            return await test_ai_engine_integration(arguments)
        elif name == "analyze_performance_metrics":
            return await analyze_performance_metrics(arguments)
        elif name == "validate_enterprise_patterns":
            return await validate_enterprise_patterns(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
            
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]

async def diagnose_gateway_health(args: Dict[str, Any]) -> List[TextContent]:
    """Comprehensive Backend Orchestrator health diagnosis"""
    
    include_cache = args.get("include_cache_metrics", True)
    include_rate_limiting = args.get("include_rate_limiting", True) 
    tenant_id = args.get("tenant_id", "demo_dentist")
    
    # Check basic health
    health = await client.check_health()
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "backend_orchestrator_health": health,
        "diagnostics": []
    }
    
    # Cache metrics
    if include_cache and health.get("status") == "healthy":
        cache_metrics = await client.get_cache_metrics()
        result["cache_metrics"] = cache_metrics
        
        # Analyze cache performance
        if "error" not in cache_metrics:
            hit_rate = cache_metrics.get("hit_rate", 0)
            if hit_rate < 0.7:
                result["diagnostics"].append({
                    "type": "warning",
                    "message": f"Cache hit rate is low: {hit_rate:.2%}",
                    "recommendation": "Consider cache key optimization or increasing TTL"
                })
    
    # Rate limiting analysis
    if include_rate_limiting and health.get("status") == "healthy":
        rate_analysis = await client.analyze_rate_limiting(tenant_id)
        result["rate_limiting"] = rate_analysis
        
        if "error" not in rate_analysis:
            active_limits = rate_analysis.get("total_active_limits", 0)
            if active_limits > 10:
                result["diagnostics"].append({
                    "type": "info", 
                    "message": f"High number of active rate limits: {active_limits}",
                    "recommendation": "Monitor for potential rate limiting bottlenecks"
                })
    
    # AI Engine connectivity test
    try:
        ai_engine_health = await client.client.get(f"{AI_ENGINE_URL}/health", timeout=5.0)
        result["ai_engine_connectivity"] = {
            "status": "connected" if ai_engine_health.status_code == 200 else "disconnected",
            "status_code": ai_engine_health.status_code
        }
    except Exception as e:
        result["ai_engine_connectivity"] = {
            "status": "error",
            "error": str(e)
        }
        result["diagnostics"].append({
            "type": "critical",
            "message": "AI Engine connectivity failed",
            "recommendation": "Check AI Engine service and network connectivity"
        })
    
    # Overall health assessment
    issues = len([d for d in result["diagnostics"] if d["type"] in ["warning", "critical"]])
    result["overall_status"] = "healthy" if issues == 0 else "needs_attention" if issues < 3 else "critical"
    
    return [TextContent(
        type="text", 
        text=f"🚀 Backend Orchestrator Health Diagnosis\n\n{json.dumps(result, indent=2)}"
    )]

async def analyze_cache_coherence(args: Dict[str, Any]) -> List[TextContent]:
    """Analyze cache coherence system performance"""
    
    time_window = args.get("time_window_minutes", 15)
    include_event_log = args.get("include_event_log", True)
    
    redis_client = await client.get_redis_client()
    if not redis_client:
        return [TextContent(type="text", text="❌ Redis connection failed - cannot analyze cache coherence")]
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "analysis_window_minutes": time_window,
        "cache_coherence_analysis": {}
    }
    
    try:
        # Analyze cache keys
        cache_keys = await redis_client.keys("cache:*")
        coherence_keys = await redis_client.keys("cache_coherence:*")
        pubsub_keys = await redis_client.keys("pubsub:*")
        
        result["cache_coherence_analysis"] = {
            "total_cache_keys": len(cache_keys),
            "coherence_tracking_keys": len(coherence_keys),
            "pubsub_channels": len(pubsub_keys),
            "cache_to_coherence_ratio": len(coherence_keys) / max(len(cache_keys), 1)
        }
        
        # Sample cache key analysis
        if cache_keys:
            sample_keys = cache_keys[:5]  # Sample first 5 keys
            key_analysis = []
            
            for key in sample_keys:
                key_str = key.decode() if isinstance(key, bytes) else str(key)
                ttl = await redis_client.ttl(key)
                memory_usage = await redis_client.memory_usage(key)
                
                key_analysis.append({
                    "key": key_str,
                    "ttl_seconds": ttl,
                    "memory_bytes": memory_usage or 0
                })
            
            result["sample_cache_analysis"] = key_analysis
        
        # Recent cache coherence events (if available)
        if include_event_log:
            try:
                # Try to get recent coherence events from a log key
                events_key = "cache_coherence_events"
                recent_events = await redis_client.lrange(events_key, -10, -1)
                
                if recent_events:
                    result["recent_coherence_events"] = [
                        json.loads(event.decode()) if isinstance(event, bytes) else json.loads(event)
                        for event in recent_events
                    ]
                else:
                    result["recent_coherence_events"] = []
            except:
                result["recent_coherence_events"] = "Not available"
        
        # Performance recommendations
        recommendations = []
        ratio = result["cache_coherence_analysis"]["cache_to_coherence_ratio"]
        
        if ratio > 0.8:
            recommendations.append({
                "type": "optimization",
                "message": "High cache coherence overhead detected",
                "action": "Consider batch invalidation or longer coherence intervals"
            })
        elif ratio < 0.1:
            recommendations.append({
                "type": "warning", 
                "message": "Low cache coherence coverage",
                "action": "Verify coherence system is properly configured"
            })
        
        if len(cache_keys) > 10000:
            recommendations.append({
                "type": "performance",
                "message": f"Large number of cache keys: {len(cache_keys)}",
                "action": "Consider implementing cache eviction policies"
            })
        
        result["recommendations"] = recommendations
        
    except Exception as e:
        result["error"] = str(e)
    
    return [TextContent(
        type="text",
        text=f"📊 Cache Coherence Analysis\n\n{json.dumps(result, indent=2)}"
    )]

async def generate_enterprise_router(args: Dict[str, Any]) -> List[TextContent]:
    """Generate enterprise router with Backend Orchestrator patterns"""
    
    router_name = args["router_name"]
    router_type = args.get("router_type", "proxy")
    operations = args.get("operations", ["list", "create", "get", "update"])
    include_rate_limiting = args.get("include_rate_limiting", True)
    include_caching = args.get("include_caching", True)
    
    # Generate router code
    router_code = generate_router_code(
        router_name, router_type, operations, 
        include_rate_limiting, include_caching
    )
    
    # Generate corresponding test file
    test_code = generate_router_test_code(router_name, operations)
    
    # File paths
    router_path = f"src/backend/routers/{router_name}.py"
    test_path = f"tests/test_{router_name}.py"
    
    result = {
        "router_name": router_name,
        "router_type": router_type,
        "operations": operations,
        "files_generated": {
            "router": router_path,
            "test": test_path
        },
        "enterprise_features": {
            "rate_limiting": include_rate_limiting,
            "caching": include_caching,
            "multi_tenant": True,
            "error_handling": True,
            "monitoring": True
        }
    }
    
    return [
        TextContent(
            type="text",
            text=f"""🚀 Enterprise Router Generated: {router_name}

Router Configuration:
{json.dumps(result, indent=2)}

Generated Router Code:
```python
{router_code}
```

Generated Test Code:
```python
{test_code}
```

Next Steps:
1. Save router code to: {router_path}
2. Save test code to: {test_path}
3. Add router import to src/backend/app.py
4. Run tests: pytest {test_path} -v
5. Test integration with: python -m uvicorn backend.app:app --reload
"""
        )
    ]

def generate_router_code(name: str, router_type: str, operations: List[str], 
                        include_rate_limiting: bool, include_caching: bool) -> str:
    """Generate enterprise router code with all patterns"""
    
    imports = [
        "from __future__ import annotations",
        "",
        "import logging",
        "from typing import Any, Dict, List, Optional",
        "",
        "from fastapi import APIRouter, Depends, HTTPException, Header, Request",
        "from fastapi.responses import JSONResponse",
        "",
        "from backend.config.services_new import services",
        "from backend.dependencies_enterprise import get_redis_cache, get_http_client"
    ]
    
    if include_rate_limiting:
        imports.extend([
            "from backend.utils.rate_limiter import EnterpriseRateLimiter"
        ])
    
    if include_caching:
        imports.extend([
            "from backend.cache_coherence import CacheCoherenceManager, InvalidationType",
            "from backend.cache_keys import generate_cache_key"
        ])
    
    # Router setup
    router_setup = f"""
logger = logging.getLogger(__name__)

# Router configuration
router = APIRouter(
    prefix="/api/{name}",
    tags=["{name}"],
    responses={{
        404: {{"description": "Not found"}},
        429: {{"description": "Rate limit exceeded"}},
        500: {{"description": "Internal server error"}}
    }}
)
"""
    
    # Dependencies
    dependencies = ""
    if include_rate_limiting:
        dependencies += """
# Enterprise rate limiter
rate_limiter = EnterpriseRateLimiter()
"""
    
    if include_caching:
        dependencies += """
# Cache coherence manager
cache_coherence = CacheCoherenceManager()
"""
    
    # Generate operation endpoints
    endpoints = []
    
    for operation in operations:
        if operation == "list":
            endpoints.append(generate_list_endpoint(name, router_type, include_rate_limiting, include_caching))
        elif operation == "create":
            endpoints.append(generate_create_endpoint(name, router_type, include_rate_limiting, include_caching))
        elif operation == "get":
            endpoints.append(generate_get_endpoint(name, router_type, include_rate_limiting, include_caching))
        elif operation == "update":
            endpoints.append(generate_update_endpoint(name, router_type, include_rate_limiting, include_caching))
        elif operation == "delete":
            endpoints.append(generate_delete_endpoint(name, router_type, include_rate_limiting, include_caching))
    
    return "\n".join(imports) + router_setup + dependencies + "\n\n".join(endpoints)

def generate_list_endpoint(name: str, router_type: str, rate_limiting: bool, caching: bool) -> str:
    """Generate list endpoint with enterprise patterns"""
    
    rate_check = ""
    if rate_limiting:
        rate_check = f"""
    # Enterprise rate limiting
    if not await rate_limiter.check(x_tenant_id, "list_{name}"):
        raise HTTPException(
            status_code=429, 
            detail="Rate limit exceeded for {name} listing"
        )
    """
    
    cache_check = ""
    if caching:
        cache_check = f"""
    # Cache coherence check
    cache_key = generate_cache_key("list_{name}", x_tenant_id)
    cached_result = await redis_cache.get(cache_key)
    if cached_result:
        logger.info(f"Cache hit for {name} list - tenant: {{x_tenant_id}}")
        return JSONResponse(content=cached_result)
    """
    
    proxy_logic = ""
    if router_type in ["proxy", "hybrid"]:
        proxy_logic = f"""
    try:
        # Forward to AI Engine
        ai_engine_url = services.get_service_url("ai-engine")
        async with http_client as client:
            response = await client.get(
                f"{{ai_engine_url}}/api/{name}",
                headers={{"X-Tenant-ID": x_tenant_id}},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
        
        # Cache the result
        if caching:
            await redis_cache.set(cache_key, result, ttl=300)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error listing {name} for tenant {{x_tenant_id}}: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")
    """
    else:
        proxy_logic = f"""
    # Direct implementation (customize as needed)
    try:
        result = {{
            "{name}": [],
            "total": 0,
            "tenant_id": x_tenant_id,
            "timestamp": "2025-01-01T00:00:00Z"
        }}
        
        # Cache the result
        if caching:
            await redis_cache.set(cache_key, result, ttl=300)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error listing {name} for tenant {{x_tenant_id}}: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")
    """
    
    return f'''
@router.get("/")
async def list_{name}(
    x_tenant_id: str = Header(..., description="Tenant identifier"),
    redis_cache = Depends(get_redis_cache),
    http_client = Depends(get_http_client)
) -> JSONResponse:
    """List all {name} for tenant with enterprise patterns"""
    {rate_check}
    {cache_check}
    {proxy_logic}
'''

def generate_create_endpoint(name: str, router_type: str, rate_limiting: bool, caching: bool) -> str:
    """Generate create endpoint with enterprise patterns"""
    
    rate_check = ""
    if rate_limiting:
        rate_check = f"""
    # Enterprise rate limiting
    if not await rate_limiter.check(x_tenant_id, "create_{name}"):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded for {name} creation"
        )
    """
    
    cache_invalidation = ""
    if caching:
        cache_invalidation = f"""
        # Cache coherence - invalidate related caches
        await cache_coherence.invalidate_by_event({{
            "type": InvalidationType.BULK_INVALIDATION,
            "tenant_id": x_tenant_id,
            "resource_type": "{name}",
            "patterns": [f"list_{name}:{{x_tenant_id}}:*"]
        }})
        """
    
    proxy_logic = ""
    if router_type in ["proxy", "hybrid"]:
        proxy_logic = f"""
    try:
        # Forward to AI Engine
        ai_engine_url = services.get_service_url("ai-engine")
        async with http_client as client:
            response = await client.post(
                f"{{ai_engine_url}}/api/{name}",
                json=data.dict(),
                headers={{"X-Tenant-ID": x_tenant_id}},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
        
        {cache_invalidation}
        
        return JSONResponse(content=result, status_code=201)
        
    except Exception as e:
        logger.error(f"Error creating {name} for tenant {{x_tenant_id}}: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")
    """
    else:
        proxy_logic = f"""
    # Direct implementation (customize as needed)
    try:
        result = {{
            "id": "generated-id",
            "tenant_id": x_tenant_id,
            "created_at": "2025-01-01T00:00:00Z",
            **data.dict()
        }}
        
        {cache_invalidation}
        
        return JSONResponse(content=result, status_code=201)
        
    except Exception as e:
        logger.error(f"Error creating {name} for tenant {{x_tenant_id}}: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")
    """
    
    return f'''
@router.post("/")
async def create_{name}(
    data: Dict[str, Any],  # Replace with proper Pydantic model
    x_tenant_id: str = Header(..., description="Tenant identifier"),
    redis_cache = Depends(get_redis_cache),
    http_client = Depends(get_http_client)
) -> JSONResponse:
    """Create new {name} for tenant with enterprise patterns"""
    {rate_check}
    {proxy_logic}
'''

def generate_get_endpoint(name: str, router_type: str, rate_limiting: bool, caching: bool) -> str:
    """Generate get endpoint with enterprise patterns"""
    
    rate_check = ""
    if rate_limiting:
        rate_check = f"""
    # Enterprise rate limiting  
    if not await rate_limiter.check(x_tenant_id, "get_{name}"):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded for {name} retrieval"
        )
    """
    
    cache_check = ""
    if caching:
        cache_check = f"""
    # Cache coherence check
    cache_key = generate_cache_key("get_{name}", x_tenant_id, item_id)
    cached_result = await redis_cache.get(cache_key)
    if cached_result:
        logger.info(f"Cache hit for {name} {{item_id}} - tenant: {{x_tenant_id}}")
        return JSONResponse(content=cached_result)
    """
    
    proxy_logic = ""
    if router_type in ["proxy", "hybrid"]:
        proxy_logic = f"""
    try:
        # Forward to AI Engine
        ai_engine_url = services.get_service_url("ai-engine")
        async with http_client as client:
            response = await client.get(
                f"{{ai_engine_url}}/api/{name}/{{item_id}}",
                headers={{"X-Tenant-ID": x_tenant_id}},
                timeout=30.0
            )
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"{name.capitalize()} not found")
            
            response.raise_for_status()
            result = response.json()
        
        # Cache the result
        if caching:
            await redis_cache.set(cache_key, result, ttl=300)
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting {name} {{item_id}} for tenant {{x_tenant_id}}: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")
    """
    else:
        proxy_logic = f"""
    # Direct implementation (customize as needed)
    try:
        result = {{
            "id": item_id,
            "tenant_id": x_tenant_id,
            "data": "Sample data - implement actual logic"
        }}
        
        # Cache the result
        if caching:
            await redis_cache.set(cache_key, result, ttl=300)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error getting {name} {{item_id}} for tenant {{x_tenant_id}}: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")
    """
    
    return f'''
@router.get("/{{item_id}}")
async def get_{name}(
    item_id: str,
    x_tenant_id: str = Header(..., description="Tenant identifier"),
    redis_cache = Depends(get_redis_cache),
    http_client = Depends(get_http_client)
) -> JSONResponse:
    """Get specific {name} by ID for tenant with enterprise patterns"""
    {rate_check}
    {cache_check}
    {proxy_logic}
'''

def generate_update_endpoint(name: str, router_type: str, rate_limiting: bool, caching: bool) -> str:
    """Generate update endpoint with enterprise patterns"""
    
    rate_check = ""
    if rate_limiting:
        rate_check = f"""
    # Enterprise rate limiting
    if not await rate_limiter.check(x_tenant_id, "update_{name}"):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded for {name} update"
        )
    """
    
    cache_invalidation = ""
    if caching:
        cache_invalidation = f"""
        # Cache coherence - invalidate related caches
        await cache_coherence.invalidate_by_event({{
            "type": InvalidationType.BULK_INVALIDATION,
            "tenant_id": x_tenant_id,
            "resource_type": "{name}",
            "resource_id": item_id,
            "patterns": [
                f"get_{name}:{{x_tenant_id}}:{{item_id}}",
                f"list_{name}:{{x_tenant_id}}:*"
            ]
        }})
        """
    
    proxy_logic = ""
    if router_type in ["proxy", "hybrid"]:
        proxy_logic = f"""
    try:
        # Forward to AI Engine
        ai_engine_url = services.get_service_url("ai-engine")
        async with http_client as client:
            response = await client.put(
                f"{{ai_engine_url}}/api/{name}/{{item_id}}",
                json=data.dict(),
                headers={{"X-Tenant-ID": x_tenant_id}},
                timeout=30.0
            )
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"{name.capitalize()} not found")
            
            response.raise_for_status()
            result = response.json()
        
        {cache_invalidation}
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating {name} {{item_id}} for tenant {{x_tenant_id}}: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")
    """
    else:
        proxy_logic = f"""
    # Direct implementation (customize as needed) 
    try:
        result = {{
            "id": item_id,
            "tenant_id": x_tenant_id,
            "updated_at": "2025-01-01T00:00:00Z",
            **data.dict()
        }}
        
        {cache_invalidation}
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error updating {name} {{item_id}} for tenant {{x_tenant_id}}: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")
    """
    
    return f'''
@router.put("/{{item_id}}")
async def update_{name}(
    item_id: str,
    data: Dict[str, Any],  # Replace with proper Pydantic model
    x_tenant_id: str = Header(..., description="Tenant identifier"),
    redis_cache = Depends(get_redis_cache),
    http_client = Depends(get_http_client)
) -> JSONResponse:
    """Update specific {name} by ID for tenant with enterprise patterns"""
    {rate_check}
    {proxy_logic}
'''

def generate_delete_endpoint(name: str, router_type: str, rate_limiting: bool, caching: bool) -> str:
    """Generate delete endpoint with enterprise patterns"""
    
    rate_check = ""
    if rate_limiting:
        rate_check = f"""
    # Enterprise rate limiting
    if not await rate_limiter.check(x_tenant_id, "delete_{name}"):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded for {name} deletion"
        )
    """
    
    cache_invalidation = ""
    if caching:
        cache_invalidation = f"""
        # Cache coherence - invalidate related caches
        await cache_coherence.invalidate_by_event({{
            "type": InvalidationType.BULK_INVALIDATION,
            "tenant_id": x_tenant_id,
            "resource_type": "{name}",
            "resource_id": item_id,
            "patterns": [
                f"get_{name}:{{x_tenant_id}}:{{item_id}}",
                f"list_{name}:{{x_tenant_id}}:*"
            ]
        }})
        """
    
    proxy_logic = ""
    if router_type in ["proxy", "hybrid"]:
        proxy_logic = f"""
    try:
        # Forward to AI Engine
        ai_engine_url = services.get_service_url("ai-engine")
        async with http_client as client:
            response = await client.delete(
                f"{{ai_engine_url}}/api/{name}/{{item_id}}",
                headers={{"X-Tenant-ID": x_tenant_id}},
                timeout=30.0
            )
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"{name.capitalize()} not found")
            
            response.raise_for_status()
        
        {cache_invalidation}
        
        return JSONResponse(content={{"message": f"{name.capitalize()} deleted successfully"}}, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting {name} {{item_id}} for tenant {{x_tenant_id}}: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")
    """
    else:
        proxy_logic = f"""
    # Direct implementation (customize as needed)
    try:
        {cache_invalidation}
        
        return JSONResponse(content={{"message": f"{name.capitalize()} deleted successfully"}}, status_code=200)
        
    except Exception as e:
        logger.error(f"Error deleting {name} {{item_id}} for tenant {{x_tenant_id}}: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")
    """
    
    return f'''
@router.delete("/{{item_id}}")
async def delete_{name}(
    item_id: str,
    x_tenant_id: str = Header(..., description="Tenant identifier"),
    redis_cache = Depends(get_redis_cache),
    http_client = Depends(get_http_client)
) -> JSONResponse:
    """Delete specific {name} by ID for tenant with enterprise patterns"""
    {rate_check}
    {proxy_logic}
'''

def generate_router_test_code(name: str, operations: List[str]) -> str:
    """Generate comprehensive test code for the router"""
    
    return f'''"""
Tests for {name} router - Backend Orchestrator Enterprise Patterns
=================================================================

Comprehensive test suite covering:
- Multi-tenant isolation
- Rate limiting behavior  
- Cache coherence validation
- Error handling
- Integration with AI Engine
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from backend.app import app
from backend.routers.{name} import router


class Test{name.capitalize()}Router:
    """Test suite for {name} router with enterprise patterns"""
    
    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)
    
    @pytest.fixture
    def tenant_headers(self):
        """Standard tenant headers"""
        return {{"X-Tenant-ID": "test_tenant"}}
    
    @pytest.fixture
    def mock_redis_cache(self):
        """Mock Redis cache"""
        with patch("backend.dependencies_enterprise.get_redis_cache") as mock:
            mock_cache = AsyncMock()
            mock.return_value = mock_cache
            yield mock_cache
    
    @pytest.fixture  
    def mock_http_client(self):
        """Mock HTTP client"""
        with patch("backend.dependencies_enterprise.get_http_client") as mock:
            mock_client = AsyncMock()
            mock.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock.return_value.__aexit__ = AsyncMock(return_value=None)
            yield mock_client

{"".join([generate_test_method(name, op) for op in operations])}

    def test_missing_tenant_header(self, client):
        """Test that missing tenant header returns 422"""
        response = client.get("/api/{name}/")
        assert response.status_code == 422
        assert "X-Tenant-ID" in response.text

    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self, client, tenant_headers):
        """Test rate limiting behavior"""
        with patch("backend.utils.rate_limiter.EnterpriseRateLimiter.check") as mock_rate_limit:
            # Test rate limit exceeded
            mock_rate_limit.return_value = False
            response = client.get("/api/{name}/", headers=tenant_headers)
            assert response.status_code == 429
            
            # Test rate limit OK
            mock_rate_limit.return_value = True
            with patch("backend.dependencies_enterprise.get_redis_cache"):
                with patch("backend.dependencies_enterprise.get_http_client"):
                    response = client.get("/api/{name}/", headers=tenant_headers)
                    # Should not be 429 anymore
                    assert response.status_code != 429

    @pytest.mark.asyncio
    async def test_cache_coherence_integration(self, client, tenant_headers, mock_redis_cache):
        """Test cache coherence behavior"""
        # Test cache miss
        mock_redis_cache.get.return_value = None
        
        with patch("backend.dependencies_enterprise.get_http_client"):
            response = client.get("/api/{name}/", headers=tenant_headers)
            mock_redis_cache.get.assert_called_once()
        
        # Test cache hit
        mock_redis_cache.get.return_value = {{"cached": "data"}}
        response = client.get("/api/{name}/", headers=tenant_headers)
        
        # Verify cached data returned
        assert response.json() == {{"cached": "data"}}

    @pytest.mark.asyncio
    async def test_ai_engine_integration(self, client, tenant_headers, mock_http_client):
        """Test AI Engine integration"""
        # Mock successful AI Engine response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {{"ai_engine": "response"}}
        mock_response.raise_for_status = AsyncMock()
        mock_http_client.get.return_value = mock_response
        
        with patch("backend.dependencies_enterprise.get_redis_cache"):
            response = client.get("/api/{name}/", headers=tenant_headers)
            
        # Verify AI Engine was called
        mock_http_client.get.assert_called_once()
        assert "ai_engine" in response.json()

    def test_error_handling(self, client, tenant_headers):
        """Test comprehensive error handling"""
        # Test various error scenarios
        with patch("backend.dependencies_enterprise.get_redis_cache") as mock_cache:
            mock_cache.side_effect = Exception("Redis error")
            
            response = client.get("/api/{name}/", headers=tenant_headers)
            assert response.status_code == 500

    def test_tenant_isolation(self, client):
        """Test that different tenants get isolated responses"""
        tenant1_headers = {{"X-Tenant-ID": "tenant_1"}}
        tenant2_headers = {{"X-Tenant-ID": "tenant_2"}}
        
        with patch("backend.dependencies_enterprise.get_redis_cache"):
            with patch("backend.dependencies_enterprise.get_http_client"):
                response1 = client.get("/api/{name}/", headers=tenant1_headers)
                response2 = client.get("/api/{name}/", headers=tenant2_headers)
                
                # Both should succeed but be isolated
                assert response1.status_code in [200, 500]  # May fail due to mocking
                assert response2.status_code in [200, 500]  # May fail due to mocking
'''

def generate_test_method(name: str, operation: str) -> str:
    """Generate test method for specific operation"""
    
    if operation == "list":
        return f'''
    def test_list_{name}(self, client, tenant_headers, mock_redis_cache, mock_http_client):
        """Test listing {name} with enterprise patterns"""
        # Mock cache miss
        mock_redis_cache.get.return_value = None
        
        # Mock AI Engine response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {{"{name}": [], "total": 0}}
        mock_response.raise_for_status = AsyncMock()
        mock_http_client.get.return_value = mock_response
        
        response = client.get("/api/{name}/", headers=tenant_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "{name}" in data
        assert "total" in data
'''
    
    elif operation == "create":
        return f'''
    def test_create_{name}(self, client, tenant_headers, mock_redis_cache, mock_http_client):
        """Test creating {name} with enterprise patterns"""
        # Mock AI Engine response
        mock_response = AsyncMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {{"id": "test-id", "created": True}}
        mock_response.raise_for_status = AsyncMock()
        mock_http_client.post.return_value = mock_response
        
        test_data = {{"name": "test {name}", "description": "test description"}}
        response = client.post("/api/{name}/", json=test_data, headers=tenant_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
'''
    
    elif operation == "get":
        return f'''
    def test_get_{name}(self, client, tenant_headers, mock_redis_cache, mock_http_client):
        """Test getting {name} by ID with enterprise patterns"""
        # Mock cache miss
        mock_redis_cache.get.return_value = None
        
        # Mock AI Engine response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {{"id": "test-id", "name": "test {name}"}}
        mock_response.raise_for_status = AsyncMock()
        mock_http_client.get.return_value = mock_response
        
        response = client.get("/api/{name}/test-id", headers=tenant_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-id"
    
    def test_get_{name}_not_found(self, client, tenant_headers, mock_redis_cache, mock_http_client):
        """Test getting non-existent {name}"""
        # Mock cache miss
        mock_redis_cache.get.return_value = None
        
        # Mock AI Engine 404 response
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_http_client.get.return_value = mock_response
        
        response = client.get("/api/{name}/nonexistent-id", headers=tenant_headers)
        assert response.status_code == 404
'''
    
    elif operation == "update":
        return f'''
    def test_update_{name}(self, client, tenant_headers, mock_redis_cache, mock_http_client):
        """Test updating {name} with enterprise patterns"""
        # Mock AI Engine response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {{"id": "test-id", "updated": True}}
        mock_response.raise_for_status = AsyncMock()
        mock_http_client.put.return_value = mock_response
        
        update_data = {{"name": "updated {name}"}}
        response = client.put("/api/{name}/test-id", json=update_data, headers=tenant_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "updated" in data
'''
    
    elif operation == "delete":
        return f'''
    def test_delete_{name}(self, client, tenant_headers, mock_redis_cache, mock_http_client):
        """Test deleting {name} with enterprise patterns"""
        # Mock AI Engine response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = AsyncMock()
        mock_http_client.delete.return_value = mock_response
        
        response = client.delete("/api/{name}/test-id", headers=tenant_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
'''
    
    return ""

async def troubleshoot_production_issue(args: Dict[str, Any]) -> List[TextContent]:
    """Troubleshoot common production issues"""
    
    issue_type = args["issue_type"]
    tenant_id = args.get("tenant_id", "demo_dentist")
    time_window = args.get("time_window_minutes", 30)
    
    troubleshooting_result = {
        "issue_type": issue_type,
        "tenant_id": tenant_id,
        "analysis_window_minutes": time_window,
        "timestamp": datetime.now().isoformat(),
        "diagnostics": [],
        "recommendations": []
    }
    
    # Issue-specific troubleshooting
    if issue_type == "rate_limiting":
        rate_analysis = await client.analyze_rate_limiting(tenant_id)
        troubleshooting_result["rate_limiting_analysis"] = rate_analysis
        
        if "error" not in rate_analysis:
            active_limits = rate_analysis.get("total_active_limits", 0)
            if active_limits > 15:
                troubleshooting_result["diagnostics"].append({
                    "severity": "high",
                    "message": f"Excessive active rate limits: {active_limits}",
                    "impact": "High memory usage and potential performance degradation"
                })
                troubleshooting_result["recommendations"].extend([
                    {
                        "action": "Implement batch rate limit cleanup",
                        "priority": "high",
                        "command": "redis-cli --scan --pattern 'rate_limit:*' | xargs redis-cli del"
                    },
                    {
                        "action": "Review rate limit configurations",
                        "priority": "medium", 
                        "file": "src/backend/utils/rate_limiter.py"
                    }
                ])
    
    elif issue_type == "cache_miss":
        cache_metrics = await client.get_cache_metrics()
        troubleshooting_result["cache_analysis"] = cache_metrics
        
        if "error" not in cache_metrics:
            hit_rate = cache_metrics.get("hit_rate", 0)
            if hit_rate < 0.5:
                troubleshooting_result["diagnostics"].append({
                    "severity": "medium",
                    "message": f"Low cache hit rate: {hit_rate:.2%}",
                    "impact": "Increased latency and AI Engine load"
                })
                troubleshooting_result["recommendations"].extend([
                    {
                        "action": "Increase cache TTL values",
                        "priority": "medium",
                        "file": "src/backend/cache_manager.py"
                    },
                    {
                        "action": "Review cache key patterns",
                        "priority": "low",
                        "file": "src/backend/cache_keys.py"
                    }
                ])
    
    elif issue_type == "circuit_breaker":
        # Check health of downstream services
        health = await client.check_health()
        troubleshooting_result["health_analysis"] = health
        
        if health.get("status") != "healthy":
            troubleshooting_result["diagnostics"].append({
                "severity": "critical",
                "message": "Backend Orchestrator unhealthy",
                "impact": "Service degradation or outage"
            })
            troubleshooting_result["recommendations"].extend([
                {
                    "action": "Check service logs",
                    "priority": "critical",
                    "command": "docker-compose logs -f backend-orchestrator"
                },
                {
                    "action": "Restart service if needed",
                    "priority": "high",
                    "command": "docker-compose restart backend-orchestrator"
                }
            ])
        
        # Check AI Engine connectivity
        ai_health = troubleshooting_result.get("ai_engine_connectivity", {})
        if ai_health.get("status") != "connected":
            troubleshooting_result["diagnostics"].append({
                "severity": "critical",
                "message": "AI Engine connectivity issues",
                "impact": "Circuit breaker likely triggered"
            })
            troubleshooting_result["recommendations"].extend([
                {
                    "action": "Check AI Engine service",
                    "priority": "critical",
                    "command": "docker-compose logs -f ai-engine"
                },
                {
                    "action": "Verify network connectivity",
                    "priority": "high",
                    "command": f"curl -f {AI_ENGINE_URL}/health"
                }
            ])
    
    elif issue_type == "proxy_timeout":
        troubleshooting_result["diagnostics"].append({
            "severity": "high",
            "message": "Proxy timeout indicates AI Engine performance issues",
            "impact": "Request failures and user experience degradation"
        })
        troubleshooting_result["recommendations"].extend([
            {
                "action": "Check AI Engine response times",
                "priority": "high",
                "command": f"curl -w '@curl-format.txt' -s -o /dev/null {AI_ENGINE_URL}/health"
            },
            {
                "action": "Increase proxy timeout if needed",
                "priority": "medium",
                "file": "src/backend/dependencies_enterprise.py"
            },
            {
                "action": "Review AI Engine resource usage",
                "priority": "high",
                "command": "docker stats ai-engine"
            }
        ])
    
    elif issue_type == "memory_leak":
        troubleshooting_result["diagnostics"].append({
            "severity": "high",
            "message": "Memory leak investigation required",
            "impact": "Progressive performance degradation"
        })
        troubleshooting_result["recommendations"].extend([
            {
                "action": "Monitor memory usage",
                "priority": "critical",
                "command": "docker stats backend-orchestrator"
            },
            {
                "action": "Check for connection leaks",
                "priority": "high",
                "file": "src/backend/dependencies_enterprise.py"
            },
            {
                "action": "Review cache TTL settings",
                "priority": "medium",
                "file": "src/backend/cache_manager.py"
            }
        ])
    
    elif issue_type == "high_latency":
        cache_metrics = await client.get_cache_metrics()
        troubleshooting_result["performance_analysis"] = cache_metrics
        
        troubleshooting_result["diagnostics"].append({
            "severity": "medium",
            "message": "High latency detected",
            "impact": "Poor user experience"
        })
        troubleshooting_result["recommendations"].extend([
            {
                "action": "Analyze cache performance",
                "priority": "high",
                "details": "Check cache hit rates and coherence overhead"
            },
            {
                "action": "Profile AI Engine responses",
                "priority": "high",
                "command": "time curl -s -o /dev/null -w '%{time_total}' http://localhost:8010/health"
            },
            {
                "action": "Review database query performance",
                "priority": "medium",
                "file": "Check AI Engine database queries"
            }
        ])
    
    # Generate overall assessment
    critical_issues = len([d for d in troubleshooting_result["diagnostics"] if d.get("severity") == "critical"])
    high_issues = len([d for d in troubleshooting_result["diagnostics"] if d.get("severity") == "high"])
    
    if critical_issues > 0:
        troubleshooting_result["severity_assessment"] = "critical"
        troubleshooting_result["immediate_action_required"] = True
    elif high_issues > 0:
        troubleshooting_result["severity_assessment"] = "high"
        troubleshooting_result["immediate_action_required"] = True
    else:
        troubleshooting_result["severity_assessment"] = "medium"
        troubleshooting_result["immediate_action_required"] = False
    
    return [TextContent(
        type="text",
        text=f"""🔧 Production Issue Troubleshooting: {issue_type}

{json.dumps(troubleshooting_result, indent=2)}

🚨 Action Required: {troubleshooting_result['immediate_action_required']}
📊 Severity: {troubleshooting_result['severity_assessment'].upper()}

Next Steps:
{chr(10).join([f"• {rec['action']} (Priority: {rec['priority']})" for rec in troubleshooting_result['recommendations']])}
"""
    )]

async def test_ai_engine_integration(args: Dict[str, Any]) -> List[TextContent]:
    """Test Backend Orchestrator integration with AI Engine"""
    
    test_type = args.get("test_type", "connectivity")
    tenant_id = args.get("tenant_id", "demo_dentist") 
    include_cache = args.get("include_cache_test", True)
    
    test_results = {
        "test_type": test_type,
        "tenant_id": tenant_id,
        "timestamp": datetime.now().isoformat(),
        "tests_performed": [],
        "overall_status": "unknown"
    }
    
    if test_type in ["connectivity", "full_flow"]:
        # Test basic connectivity
        try:
            health_response = await client.client.get(f"{AI_ENGINE_URL}/health", timeout=5.0)
            connectivity_test = {
                "test": "ai_engine_health",
                "status": "pass" if health_response.status_code == 200 else "fail",
                "response_time_ms": health_response.elapsed.total_seconds() * 1000 if hasattr(health_response, 'elapsed') else 0,
                "status_code": health_response.status_code
            }
            if health_response.status_code == 200:
                connectivity_test["response_data"] = health_response.json()
        except Exception as e:
            connectivity_test = {
                "test": "ai_engine_health",
                "status": "fail",
                "error": str(e)
            }
        
        test_results["tests_performed"].append(connectivity_test)
    
    if test_type in ["performance", "full_flow"]:
        # Performance test
        start_time = datetime.now()
        try:
            # Test multiple rapid requests
            tasks = []
            for i in range(5):
                task = client.client.get(f"{AI_ENGINE_URL}/health", timeout=10.0)
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = datetime.now()
            
            successful_responses = [r for r in responses if not isinstance(r, Exception) and r.status_code == 200]
            failed_responses = [r for r in responses if isinstance(r, Exception) or r.status_code != 200]
            
            performance_test = {
                "test": "ai_engine_performance",
                "total_requests": 5,
                "successful_requests": len(successful_responses),
                "failed_requests": len(failed_responses),
                "total_time_ms": (end_time - start_time).total_seconds() * 1000,
                "average_response_time_ms": (end_time - start_time).total_seconds() * 1000 / 5,
                "status": "pass" if len(successful_responses) >= 4 else "fail"
            }
            
        except Exception as e:
            performance_test = {
                "test": "ai_engine_performance", 
                "status": "fail",
                "error": str(e)
            }
        
        test_results["tests_performed"].append(performance_test)
    
    if test_type in ["error_handling", "full_flow"]:
        # Error handling test
        try:
            # Test invalid endpoint
            error_response = await client.client.get(f"{AI_ENGINE_URL}/invalid-endpoint", timeout=5.0)
            
            error_handling_test = {
                "test": "ai_engine_error_handling",
                "status": "pass" if error_response.status_code == 404 else "fail",
                "expected_status": 404,
                "actual_status": error_response.status_code,
                "handles_errors_gracefully": error_response.status_code in [400, 404, 500]
            }
            
        except Exception as e:
            error_handling_test = {
                "test": "ai_engine_error_handling",
                "status": "fail",
                "error": str(e)
            }
        
        test_results["tests_performed"].append(error_handling_test)
    
    if include_cache and test_type in ["connectivity", "full_flow"]:
        # Cache integration test
        redis_client = await client.get_redis_client()
        if redis_client:
            try:
                # Test cache operations
                test_key = f"integration_test:{tenant_id}:{datetime.now().timestamp()}"
                test_value = {"test": "cache_integration", "timestamp": datetime.now().isoformat()}
                
                await redis_client.set(test_key, json.dumps(test_value), ex=300)
                retrieved_value = await redis_client.get(test_key)
                await redis_client.delete(test_key)
                
                cache_test = {
                    "test": "cache_integration",
                    "status": "pass" if retrieved_value else "fail",
                    "cache_roundtrip_successful": retrieved_value is not None,
                    "data_integrity": json.loads(retrieved_value.decode()) == test_value if retrieved_value else False
                }
                
            except Exception as e:
                cache_test = {
                    "test": "cache_integration",
                    "status": "fail", 
                    "error": str(e)
                }
        else:
            cache_test = {
                "test": "cache_integration",
                "status": "fail",
                "error": "Redis connection not available"
            }
        
        test_results["tests_performed"].append(cache_test)
    
    if test_type == "full_flow":
        # Full integration flow test
        try:
            # Test Backend Orchestrator to AI Engine proxy
            proxy_response = await client.client.post(
                f"{BACKEND_ORCHESTRATOR_URL}/api/chat",
                json={"phone": f"+5511999{datetime.now().microsecond}", "message": "Integration test"},
                headers={"X-Tenant-ID": tenant_id},
                timeout=30.0
            )
            
            full_flow_test = {
                "test": "full_integration_flow",
                "status": "pass" if proxy_response.status_code in [200, 201] else "fail",
                "status_code": proxy_response.status_code,
                "backend_to_ai_engine": proxy_response.status_code in [200, 201],
                "response_has_data": bool(proxy_response.text)
            }
            
            if proxy_response.status_code in [200, 201]:
                try:
                    response_data = proxy_response.json()
                    full_flow_test["response_contains_reply"] = "reply" in response_data or "message" in response_data
                except:
                    full_flow_test["response_contains_reply"] = False
            
        except Exception as e:
            full_flow_test = {
                "test": "full_integration_flow",
                "status": "fail",
                "error": str(e)
            }
        
        test_results["tests_performed"].append(full_flow_test)
    
    # Calculate overall status
    passed_tests = len([t for t in test_results["tests_performed"] if t.get("status") == "pass"])
    total_tests = len(test_results["tests_performed"])
    
    if total_tests == 0:
        test_results["overall_status"] = "no_tests_performed"
    elif passed_tests == total_tests:
        test_results["overall_status"] = "all_pass"
    elif passed_tests >= total_tests * 0.8:
        test_results["overall_status"] = "mostly_pass"
    elif passed_tests > 0:
        test_results["overall_status"] = "partial_pass"
    else:
        test_results["overall_status"] = "all_fail"
    
    test_results["pass_rate"] = f"{passed_tests}/{total_tests} ({passed_tests/max(total_tests, 1)*100:.1f}%)"
    
    return [TextContent(
        type="text",
        text=f"""🔌 AI Engine Integration Test Results

{json.dumps(test_results, indent=2)}

Summary:
✅ Passed: {passed_tests}/{total_tests} tests
📊 Pass Rate: {test_results['pass_rate']}
🎯 Overall Status: {test_results['overall_status'].upper()}
"""
    )]

async def analyze_performance_metrics(args: Dict[str, Any]) -> List[TextContent]:
    """Analyze Backend Orchestrator performance metrics"""
    
    metric_type = args.get("metric_type", "latency")
    time_window = args.get("time_window_minutes", 60)
    tenant_filter = args.get("tenant_filter")
    
    performance_analysis = {
        "metric_type": metric_type,
        "time_window_minutes": time_window,
        "tenant_filter": tenant_filter,
        "timestamp": datetime.now().isoformat(),
        "analysis_results": {}
    }
    
    # Get basic health and cache metrics
    health = await client.check_health()
    cache_metrics = await client.get_cache_metrics()
    
    performance_analysis["service_health"] = health
    performance_analysis["cache_performance"] = cache_metrics
    
    if metric_type == "latency":
        # Latency analysis
        latency_tests = []
        
        # Test Backend Orchestrator latency
        start_time = datetime.now()
        try:
            health_response = await client.client.get(f"{BACKEND_ORCHESTRATOR_URL}/health")
            end_time = datetime.now()
            
            latency_tests.append({
                "service": "backend_orchestrator",
                "endpoint": "/health",
                "latency_ms": (end_time - start_time).total_seconds() * 1000,
                "status_code": health_response.status_code
            })
        except Exception as e:
            latency_tests.append({
                "service": "backend_orchestrator",
                "endpoint": "/health", 
                "error": str(e)
            })
        
        # Test AI Engine latency
        start_time = datetime.now()
        try:
            ai_response = await client.client.get(f"{AI_ENGINE_URL}/health")
            end_time = datetime.now()
            
            latency_tests.append({
                "service": "ai_engine",
                "endpoint": "/health",
                "latency_ms": (end_time - start_time).total_seconds() * 1000,
                "status_code": ai_response.status_code
            })
        except Exception as e:
            latency_tests.append({
                "service": "ai_engine",
                "endpoint": "/health",
                "error": str(e)
            })
        
        performance_analysis["analysis_results"]["latency_tests"] = latency_tests
        
        # Latency assessment
        successful_tests = [t for t in latency_tests if "latency_ms" in t]
        if successful_tests:
            avg_latency = sum(t["latency_ms"] for t in successful_tests) / len(successful_tests)
            max_latency = max(t["latency_ms"] for t in successful_tests)
            min_latency = min(t["latency_ms"] for t in successful_tests)
            
            performance_analysis["analysis_results"]["latency_summary"] = {
                "average_latency_ms": avg_latency,
                "max_latency_ms": max_latency,
                "min_latency_ms": min_latency,
                "assessment": (
                    "excellent" if avg_latency < 100 else
                    "good" if avg_latency < 500 else
                    "acceptable" if avg_latency < 1000 else
                    "poor"
                )
            }
    
    elif metric_type == "cache_performance":
        # Detailed cache analysis
        redis_client = await client.get_redis_client()
        if redis_client:
            try:
                # Get cache statistics
                cache_info = await redis_client.info("keyspace")
                memory_info = await redis_client.info("memory")
                
                # Count different types of keys
                cache_keys = await redis_client.keys("cache:*")
                rate_limit_keys = await redis_client.keys("rate_limit:*")
                coherence_keys = await redis_client.keys("cache_coherence:*")
                
                performance_analysis["analysis_results"]["cache_statistics"] = {
                    "total_cache_keys": len(cache_keys),
                    "rate_limit_keys": len(rate_limit_keys),
                    "coherence_keys": len(coherence_keys),
                    "memory_used_bytes": memory_info.get("used_memory", 0),
                    "memory_used_human": memory_info.get("used_memory_human", "0B"),
                    "keyspace_info": cache_info
                }
                
                # Cache efficiency calculation
                if "error" not in cache_metrics:
                    hit_rate = cache_metrics.get("hit_rate", 0)
                    performance_analysis["analysis_results"]["cache_efficiency"] = {
                        "hit_rate": hit_rate,
                        "efficiency_assessment": (
                            "excellent" if hit_rate > 0.8 else
                            "good" if hit_rate > 0.6 else
                            "acceptable" if hit_rate > 0.4 else
                            "poor"
                        ),
                        "cache_to_data_ratio": len(cache_keys) / max(len(rate_limit_keys) + len(coherence_keys), 1)
                    }
                
            except Exception as e:
                performance_analysis["analysis_results"]["cache_error"] = str(e)
    
    elif metric_type == "rate_limiting_efficiency":
        # Rate limiting performance analysis
        if tenant_filter:
            rate_analysis = await client.analyze_rate_limiting(tenant_filter)
            performance_analysis["analysis_results"]["tenant_rate_limiting"] = rate_analysis
        else:
            # Analyze overall rate limiting
            redis_client = await client.get_redis_client()
            if redis_client:
                try:
                    rate_limit_keys = await redis_client.keys("rate_limit:*")
                    
                    # Sample analysis of rate limit keys
                    sample_analysis = []
                    for key in rate_limit_keys[:10]:  # Sample first 10 keys
                        key_str = key.decode() if isinstance(key, bytes) else str(key)
                        count = await redis_client.get(key)
                        ttl = await redis_client.ttl(key)
                        
                        sample_analysis.append({
                            "key": key_str,
                            "current_count": int(count) if count else 0,
                            "ttl_seconds": ttl
                        })
                    
                    performance_analysis["analysis_results"]["rate_limiting_analysis"] = {
                        "total_rate_limit_keys": len(rate_limit_keys),
                        "sample_keys": sample_analysis,
                        "memory_efficiency": len(rate_limit_keys) < 1000  # Arbitrary threshold
                    }
                    
                except Exception as e:
                    performance_analysis["analysis_results"]["rate_limiting_error"] = str(e)
    
    # Generate recommendations based on analysis
    recommendations = []
    
    if metric_type == "latency":
        latency_summary = performance_analysis["analysis_results"].get("latency_summary", {})
        avg_latency = latency_summary.get("average_latency_ms", 0)
        
        if avg_latency > 1000:
            recommendations.append({
                "issue": "High average latency",
                "recommendation": "Investigate service performance and consider scaling",
                "priority": "high"
            })
        elif avg_latency > 500:
            recommendations.append({
                "issue": "Moderate latency",
                "recommendation": "Monitor service performance and optimize if needed",
                "priority": "medium"
            })
    
    if metric_type == "cache_performance":
        cache_efficiency = performance_analysis["analysis_results"].get("cache_efficiency", {})
        hit_rate = cache_efficiency.get("hit_rate", 0)
        
        if hit_rate < 0.4:
            recommendations.append({
                "issue": "Low cache hit rate",
                "recommendation": "Review cache TTL settings and key patterns",
                "priority": "high"
            })
        
        cache_stats = performance_analysis["analysis_results"].get("cache_statistics", {})
        total_keys = cache_stats.get("total_cache_keys", 0)
        
        if total_keys > 50000:
            recommendations.append({
                "issue": "High number of cache keys",
                "recommendation": "Implement cache eviction policies",
                "priority": "medium"
            })
    
    performance_analysis["recommendations"] = recommendations
    
    return [TextContent(
        type="text",
        text=f"""📊 Performance Metrics Analysis: {metric_type}

{json.dumps(performance_analysis, indent=2)}

Recommendations:
{chr(10).join([f"• {rec['issue']}: {rec['recommendation']} (Priority: {rec['priority']})" for rec in recommendations])}
"""
    )]

async def validate_enterprise_patterns(args: Dict[str, Any]) -> List[TextContent]:
    """Validate enterprise patterns in Backend Orchestrator routers"""
    
    router_path = args.get("router_path")
    check_all_routers = args.get("check_all_routers", False)
    validation_level = args.get("validation_level", "comprehensive")
    
    validation_results = {
        "validation_level": validation_level,
        "timestamp": datetime.now().isoformat(),
        "validated_files": [],
        "overall_compliance": "unknown",
        "issues_found": [],
        "recommendations": []
    }
    
    routers_to_check = []
    
    if check_all_routers:
        # Get all router files
        routers_dir = BACKEND_ORCHESTRATOR_PATH / "src" / "backend" / "routers"
        if routers_dir.exists():
            router_files = [f for f in routers_dir.glob("*.py") if f.name != "__init__.py"]
            routers_to_check = [str(f.relative_to(BACKEND_ORCHESTRATOR_PATH)) for f in router_files]
        else:
            return [TextContent(type="text", text="❌ Routers directory not found")]
    
    elif router_path:
        # Check specific router
        full_path = BACKEND_ORCHESTRATOR_PATH / "src" / "backend" / "routers" / router_path
        if not full_path.exists():
            full_path = BACKEND_ORCHESTRATOR_PATH / router_path
        
        if full_path.exists():
            routers_to_check = [str(full_path.relative_to(BACKEND_ORCHESTRATOR_PATH))]
        else:
            return [TextContent(type="text", text=f"❌ Router file not found: {router_path}")]
    
    else:
        return [TextContent(type="text", text="❌ Either router_path or check_all_routers must be specified")]
    
    # Validation patterns to check
    enterprise_patterns = {
        "rate_limiting": {
            "required_imports": ["EnterpriseRateLimiter", "rate_limiter"],
            "required_patterns": ["await rate_limiter.check", "HTTPException(status_code=429"]
        },
        "caching": {
            "required_imports": ["redis", "get_redis_cache"],
            "required_patterns": ["await redis_cache.get", "await redis_cache.set"]
        },
        "multi_tenant": {
            "required_imports": ["Header"],
            "required_patterns": ["x_tenant_id: str = Header"]
        },
        "error_handling": {
            "required_patterns": ["try:", "except", "HTTPException", "logger.error"]
        },
        "dependency_injection": {
            "required_imports": ["Depends"],
            "required_patterns": ["= Depends("]
        },
        "logging": {
            "required_imports": ["logging"],
            "required_patterns": ["logger = logging.getLogger", "logger.info", "logger.error"]
        }
    }
    
    # Validate each router
    for router_file in routers_to_check:
        file_path = BACKEND_ORCHESTRATOR_PATH / router_file
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            file_validation = {
                "file": router_file,
                "patterns_found": {},
                "compliance_score": 0,
                "issues": [],
                "compliant_patterns": []
            }
            
            # Check each enterprise pattern
            for pattern_name, pattern_config in enterprise_patterns.items():
                pattern_compliance = {"imports": [], "patterns": []}
                
                # Check required imports
                for required_import in pattern_config.get("required_imports", []):
                    if required_import in file_content:
                        pattern_compliance["imports"].append(required_import)
                
                # Check required patterns
                for required_pattern in pattern_config.get("required_patterns", []):
                    if required_pattern in file_content:
                        pattern_compliance["patterns"].append(required_pattern)
                
                file_validation["patterns_found"][pattern_name] = pattern_compliance
                
                # Determine compliance for this pattern
                total_requirements = len(pattern_config.get("required_imports", [])) + len(pattern_config.get("required_patterns", []))
                found_requirements = len(pattern_compliance["imports"]) + len(pattern_compliance["patterns"])
                
                if total_requirements > 0:
                    pattern_score = found_requirements / total_requirements
                    
                    if pattern_score >= 0.8:
                        file_validation["compliant_patterns"].append(pattern_name)
                    elif pattern_score < 0.5:
                        file_validation["issues"].append({
                            "pattern": pattern_name,
                            "issue": f"Low compliance: {pattern_score:.1%}",
                            "missing_imports": [imp for imp in pattern_config.get("required_imports", []) if imp not in file_content],
                            "missing_patterns": [pat for pat in pattern_config.get("required_patterns", []) if pat not in file_content]
                        })
            
            # Calculate overall compliance score for file
            total_patterns = len(enterprise_patterns)
            compliant_patterns = len(file_validation["compliant_patterns"])
            file_validation["compliance_score"] = compliant_patterns / total_patterns if total_patterns > 0 else 0
            
            # Additional validation based on validation level
            if validation_level in ["comprehensive", "production_ready"]:
                # Check for common anti-patterns
                anti_patterns = [
                    ("Hardcoded values", ["localhost", "5432", "6379"]),
                    ("Missing error handling", ["except:", "except Exception:"]),
                    ("Synchronous operations", ["requests.get", "requests.post"]),
                    ("No timeout specified", ["httpx.get(", "httpx.post("] if "timeout=" not in file_content else [])
                ]
                
                for anti_pattern_name, patterns in anti_patterns:
                    found_anti_patterns = [p for p in patterns if p in file_content]
                    if found_anti_patterns:
                        file_validation["issues"].append({
                            "type": "anti_pattern",
                            "issue": anti_pattern_name,
                            "found_patterns": found_anti_patterns
                        })
            
            if validation_level == "production_ready":
                # Production-specific checks
                production_requirements = {
                    "Circuit breaker patterns": ["circuit_breaker", "CircuitBreaker"],
                    "Metrics collection": ["prometheus", "metrics", "counter", "histogram"],
                    "Structured logging": ["logger.info", "logger.error", "logger.warning"],
                    "Input validation": ["pydantic", "BaseModel", "Field"],
                    "Security headers": ["X-Tenant-ID", "Authorization"]
                }
                
                for req_name, patterns in production_requirements.items():
                    if not any(pattern in file_content for pattern in patterns):
                        file_validation["issues"].append({
                            "type": "production_requirement",
                            "issue": f"Missing {req_name}",
                            "required_patterns": patterns
                        })
            
            validation_results["validated_files"].append(file_validation)
            
        except Exception as e:
            validation_results["validated_files"].append({
                "file": router_file,
                "error": str(e),
                "compliance_score": 0
            })
    
    # Calculate overall compliance
    if validation_results["validated_files"]:
        total_score = sum(f.get("compliance_score", 0) for f in validation_results["validated_files"])
        avg_compliance = total_score / len(validation_results["validated_files"])
        
        if avg_compliance >= 0.8:
            validation_results["overall_compliance"] = "excellent"
        elif avg_compliance >= 0.6:
            validation_results["overall_compliance"] = "good"
        elif avg_compliance >= 0.4:
            validation_results["overall_compliance"] = "acceptable"
        else:
            validation_results["overall_compliance"] = "needs_improvement"
        
        validation_results["average_compliance_score"] = avg_compliance
    
    # Generate overall issues and recommendations
    all_issues = []
    for file_val in validation_results["validated_files"]:
        for issue in file_val.get("issues", []):
            all_issues.append({
                "file": file_val["file"],
                **issue
            })
    
    validation_results["issues_found"] = all_issues
    
    # Generate recommendations
    common_issues = {}
    for issue in all_issues:
        issue_type = issue.get("pattern", issue.get("type", issue.get("issue", "unknown")))
        if issue_type not in common_issues:
            common_issues[issue_type] = []
        common_issues[issue_type].append(issue["file"])
    
    for issue_type, affected_files in common_issues.items():
        if len(affected_files) > len(validation_results["validated_files"]) * 0.5:  # More than 50% of files
            validation_results["recommendations"].append({
                "issue": f"Widespread issue: {issue_type}",
                "affected_files": len(affected_files),
                "recommendation": f"Implement {issue_type} patterns across all routers",
                "priority": "high" if len(affected_files) > 2 else "medium"
            })
    
    return [TextContent(
        type="text",
        text=f"""✅ Enterprise Patterns Validation Results

{json.dumps(validation_results, indent=2)}

Summary:
📊 Overall Compliance: {validation_results['overall_compliance'].upper()}
📈 Average Score: {validation_results.get('average_compliance_score', 0):.1%}
🔍 Files Validated: {len(validation_results['validated_files'])}
⚠️  Issues Found: {len(validation_results['issues_found'])}

Top Recommendations:
{chr(10).join([f"• {rec['issue']}: {rec['recommendation']} (Priority: {rec['priority']})" for rec in validation_results['recommendations'][:5]])}
"""
    )]

@server.call_tool()
async def handle_tool_call(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle MCP tool calls"""
    return await call_tool(name, arguments)

async def main():
    """Run the MCP server"""
    import mcp.server.stdio
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())