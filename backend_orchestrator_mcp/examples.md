# 🔧 Backend Orchestrator MCP - Usage Examples

> **Practical examples for daily Backend Orchestrator development with the Optimus MCP server**

## 🚀 Getting Started

First, ensure the Optimus system is running:

```bash
# Start the core services
cd /path/to/optimus_final/ai-engine
docker-compose -f docker-compose.prod.yml up -d postgres redis

# Start Backend Orchestrator
cd ../backend-orchestrator  
uvicorn backend.app:app --host 0.0.0.0 --port 8020 --reload

# Start AI Engine
cd ../ai-engine
uvicorn ai_engine.app:app --host 0.0.0.0 --port 8010 --reload
```

## 📊 1. Daily Health Check

**Use Case**: Morning standup, system monitoring

```python
# Tool: diagnose_gateway_health
{
  "include_cache_metrics": true,
  "include_rate_limiting": true,
  "tenant_id": "demo_dentist"
}
```

**Expected Output**:
```json
{
  "timestamp": "2025-01-29T10:30:00Z",
  "backend_orchestrator_health": {"status": "healthy"},
  "cache_metrics": {"hit_rate": 0.85, "total_keys": 1247},
  "rate_limiting": {"total_active_limits": 5},
  "ai_engine_connectivity": {"status": "connected"},
  "overall_status": "healthy",
  "diagnostics": []
}
```

**Action Items**:
- ✅ System healthy - continue development
- ⚠️ If cache hit rate < 70% - investigate cache TTL settings
- 🔥 If AI Engine disconnected - check service and restart

---

## 🏗️ 2. Create New API Endpoint

**Use Case**: Adding new functionality (e.g., products management)

```python
# Tool: generate_enterprise_router
{
  "router_name": "products", 
  "router_type": "proxy",
  "operations": ["list", "create", "get", "update", "delete"],
  "include_rate_limiting": true,
  "include_caching": true
}
```

**Generated Files**:
1. **Router**: `src/backend/routers/products.py` 
2. **Tests**: `tests/test_products.py`

**Next Steps**:
```bash
# 1. Save generated code to files
# 2. Add to app.py
from backend.routers.products import router as products_router
app.include_router(products_router)

# 3. Run tests
pytest tests/test_products.py -v

# 4. Test manually
curl -X GET http://localhost:8020/api/products/ \
  -H "X-Tenant-ID: demo_dentist"
```

**Generated Code Features**:
- ✅ Enterprise rate limiting (per-tenant, per-operation)
- ✅ Redis cache coherence with automatic invalidation  
- ✅ Multi-tenant isolation with X-Tenant-ID headers
- ✅ Comprehensive error handling and logging
- ✅ AI Engine proxy integration
- ✅ Full test suite with mocks and edge cases

---

## 🚨 3. Troubleshoot Rate Limiting Issues

**Use Case**: Tenant hitting rate limits, degraded performance

```python
# Tool: troubleshoot_production_issue
{
  "issue_type": "rate_limiting",
  "tenant_id": "demo_dentist",
  "time_window_minutes": 30
}
```

**Diagnosis Output**:
```json
{
  "issue_type": "rate_limiting", 
  "tenant_id": "demo_dentist",
  "rate_limiting_analysis": {
    "chat": {"current_count": 150, "ttl_seconds": 45},
    "list_conversations": {"current_count": 89, "ttl_seconds": 22}
  },
  "diagnostics": [
    {
      "severity": "high",
      "message": "Excessive active rate limits: 18",
      "impact": "High memory usage and potential performance degradation"
    }
  ],
  "recommendations": [
    {
      "action": "Implement batch rate limit cleanup",
      "priority": "high", 
      "command": "redis-cli --scan --pattern 'rate_limit:*' | xargs redis-cli del"
    }
  ]
}
```

**Immediate Actions**:
```bash
# 1. Clear excessive rate limit keys
redis-cli --scan --pattern 'rate_limit:demo_dentist:*' | xargs redis-cli del

# 2. Check rate limiter configuration
cat src/backend/utils/rate_limiter.py | grep -A 10 "limits.*="

# 3. Monitor tenant activity
redis-cli monitor | grep "demo_dentist"
```

---

## ⚡ 4. Performance Analysis

**Use Case**: System feels slow, investigating bottlenecks

```python
# Tool: analyze_performance_metrics
{
  "metric_type": "latency",
  "time_window_minutes": 60,
  "tenant_filter": "demo_dentist"
}
```

**Performance Report**:
```json
{
  "metric_type": "latency",
  "analysis_results": {
    "latency_tests": [
      {"service": "backend_orchestrator", "latency_ms": 45, "status_code": 200},
      {"service": "ai_engine", "latency_ms": 230, "status_code": 200}
    ],
    "latency_summary": {
      "average_latency_ms": 137.5,
      "max_latency_ms": 230,
      "min_latency_ms": 45,
      "assessment": "good"
    }
  }
}
```

**Cache Performance Analysis**:
```python
# Tool: analyze_performance_metrics
{
  "metric_type": "cache_performance",
  "time_window_minutes": 60
}
```

**Optimization Actions**:
- 🎯 Latency < 100ms: Excellent
- ⚠️ Latency 100-500ms: Good, monitor trends  
- 🔥 Latency > 500ms: Investigate AI Engine, database queries
- 📊 Cache hit rate < 60%: Increase TTL, optimize cache keys

---

## 🔌 5. Integration Testing

**Use Case**: After deployment, validating service connectivity

```python
# Tool: test_ai_engine_integration  
{
  "test_type": "full_flow",
  "tenant_id": "demo_dentist",
  "include_cache_test": true
}
```

**Test Results**:
```json
{
  "test_type": "full_flow",
  "tests_performed": [
    {"test": "ai_engine_health", "status": "pass", "response_time_ms": 89},
    {"test": "ai_engine_performance", "status": "pass", "successful_requests": 5},
    {"test": "cache_integration", "status": "pass", "data_integrity": true},
    {"test": "full_integration_flow", "status": "pass", "response_contains_reply": true}
  ],
  "overall_status": "all_pass",
  "pass_rate": "4/4 (100.0%)"
}
```

**Continuous Integration Usage**:
```bash
# Add to CI/CD pipeline
curl -X POST http://localhost:8020/mcp/test_ai_engine_integration \
  -H "Content-Type: application/json" \
  -d '{"test_type": "connectivity"}' \
  | jq '.overall_status' | grep -q "pass" || exit 1
```

---

## 📋 6. Code Quality Validation

**Use Case**: Pre-commit hook, code review automation

```python
# Tool: validate_enterprise_patterns
{
  "check_all_routers": true,
  "validation_level": "production_ready"
}
```

**Compliance Report**:
```json
{
  "overall_compliance": "excellent", 
  "average_compliance_score": 0.92,
  "files_validated": 12,
  "issues_found": [
    {
      "file": "src/backend/routers/old_router.py",
      "issue": "Missing EnterpriseRateLimiter",
      "priority": "high"
    }
  ],
  "recommendations": [
    {
      "issue": "Widespread issue: rate_limiting",
      "affected_files": 2,
      "recommendation": "Implement rate_limiting patterns across all routers"
    }
  ]
}
```

**Validation for Specific Router**:
```python
# Tool: validate_enterprise_patterns
{
  "router_path": "products.py",
  "validation_level": "comprehensive"  
}
```

---

## 💾 7. Cache Coherence Debugging

**Use Case**: Cache inconsistency issues, stale data

```python
# Tool: analyze_cache_coherence
{
  "time_window_minutes": 15,
  "include_event_log": true
}
```

**Cache Analysis**:
```json
{
  "cache_coherence_analysis": {
    "total_cache_keys": 1247,
    "coherence_tracking_keys": 156,
    "cache_to_coherence_ratio": 0.125
  },
  "sample_cache_analysis": [
    {"key": "cache:conversation:demo_dentist:12345", "ttl_seconds": 245, "memory_bytes": 1024},
    {"key": "cache:list_messages:demo_dentist:*", "ttl_seconds": 180, "memory_bytes": 2048}
  ],
  "recent_coherence_events": [
    {"type": "conversation_updated", "tenant_id": "demo_dentist", "timestamp": "2025-01-29T10:25:00Z"}
  ],
  "recommendations": [
    {"type": "performance", "message": "Large number of cache keys: 1247", "action": "Consider implementing cache eviction policies"}
  ]
}
```

**Cache Optimization Actions**:
```bash
# Clear old cache keys
redis-cli --scan --pattern 'cache:*' --count 1000 | while read key; do
  ttl=$(redis-cli ttl "$key")
  if [ "$ttl" -eq -1 ]; then
    redis-cli del "$key" 
  fi
done

# Monitor cache coherence events
redis-cli psubscribe "cache_coherence:*"
```

---

## 🎯 8. Incident Response Workflow

**Emergency Production Issue Response**:

### Step 1: Quick Health Check
```python
{"tool": "diagnose_gateway_health", "args": {"include_cache_metrics": true, "include_rate_limiting": true}}
```

### Step 2: Identify Issue Type
```python  
{"tool": "troubleshoot_production_issue", "args": {"issue_type": "high_latency", "time_window_minutes": 15}}
```

### Step 3: Performance Analysis
```python
{"tool": "analyze_performance_metrics", "args": {"metric_type": "latency", "time_window_minutes": 30}}
```

### Step 4: Integration Validation
```python
{"tool": "test_ai_engine_integration", "args": {"test_type": "connectivity"}}
```

### Step 5: Apply Recommendations
Follow specific commands from troubleshooting output.

---

## 🛠️ 9. Development Patterns

### New Feature Development Checklist

1. **Generate Router**:
   ```python
   {"tool": "generate_enterprise_router", "args": {"router_name": "new_feature", "router_type": "proxy"}}
   ```

2. **Validate Patterns**:
   ```python  
   {"tool": "validate_enterprise_patterns", "args": {"router_path": "new_feature.py", "validation_level": "production_ready"}}
   ```

3. **Test Integration**:
   ```python
   {"tool": "test_ai_engine_integration", "args": {"test_type": "full_flow"}}
   ```

4. **Performance Baseline**:
   ```python
   {"tool": "analyze_performance_metrics", "args": {"metric_type": "latency"}}
   ```

### Daily Monitoring Routine

**Morning (9 AM)**:
```python
{"tool": "diagnose_gateway_health", "args": {"include_cache_metrics": true}}
```

**Midday (1 PM)**:  
```python
{"tool": "analyze_performance_metrics", "args": {"metric_type": "cache_performance"}}
```

**Evening (6 PM)**:
```python
{"tool": "analyze_cache_coherence", "args": {"time_window_minutes": 60}}
```

---

## 📈 10. Advanced Scenarios

### High-Traffic Tenant Analysis
```python
{
  "tool": "troubleshoot_production_issue",
  "args": {
    "issue_type": "rate_limiting", 
    "tenant_id": "high_traffic_tenant",
    "time_window_minutes": 60
  }
}
```

### Multi-Tenant Performance Comparison
```bash
# Loop through tenants
for tenant in demo_dentist clinic_a clinic_b; do
  echo "=== $tenant ==="
  # Use MCP tool for each tenant
done
```

### Cache Efficiency Optimization
```python
{
  "tool": "analyze_cache_coherence",
  "args": {
    "time_window_minutes": 120,
    "include_event_log": true
  }
}
```

---

## 🔄 11. Continuous Integration Usage

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "🔍 Validating enterprise patterns..."
python mcp_client.py validate_enterprise_patterns '{"check_all_routers": true}' | grep -q "excellent" || {
  echo "❌ Enterprise patterns validation failed"
  exit 1
}

echo "✅ Pre-commit validation passed"
```

### Deployment Pipeline
```yaml
# .github/workflows/deploy.yml
- name: Validate Backend Orchestrator
  run: |
    python mcp_client.py test_ai_engine_integration '{"test_type": "connectivity"}'
    python mcp_client.py diagnose_gateway_health '{}'
```

---

## 🎓 12. Best Practices Summary

### When to Use Each Tool

| Time | Tool | Purpose |
|------|------|---------|
| **Daily** | `diagnose_gateway_health` | System health overview |
| **Development** | `generate_enterprise_router` | New feature creation |
| **Incidents** | `troubleshoot_production_issue` | Problem diagnosis |
| **Performance Issues** | `analyze_performance_metrics` | Bottleneck identification |
| **Deployments** | `test_ai_engine_integration` | Connectivity validation |
| **Code Reviews** | `validate_enterprise_patterns` | Quality assurance |
| **Cache Issues** | `analyze_cache_coherence` | Cache optimization |

### Tool Selection Matrix

| Issue | Primary Tool | Secondary Tool | 
|-------|--------------|----------------|
| **Slow responses** | `analyze_performance_metrics` | `analyze_cache_coherence` |
| **Rate limit errors** | `troubleshoot_production_issue` | `diagnose_gateway_health` |
| **New API needed** | `generate_enterprise_router` | `validate_enterprise_patterns` |
| **Cache misses** | `analyze_cache_coherence` | `analyze_performance_metrics` |
| **Service down** | `diagnose_gateway_health` | `test_ai_engine_integration` |

### Development Workflow

1. **Morning**: Health check + performance baseline
2. **Development**: Generate routers + validate patterns
3. **Testing**: Integration tests + performance analysis  
4. **Incidents**: Troubleshoot + diagnose + fix
5. **Evening**: Cache analysis + cleanup

---

## 💡 Pro Tips

### Efficient Debugging
- Always start with `diagnose_gateway_health` for overview
- Use `troubleshoot_production_issue` for specific problem types
- Combine multiple tools for comprehensive analysis

### Performance Optimization
- Monitor cache hit rates daily (aim for > 70%)
- Keep active rate limit keys under 1000
- Validate integration latency < 200ms

### Code Quality
- Generate all new routers with MCP to ensure consistency
- Validate enterprise patterns before every commit
- Use production-ready validation level for critical code

### Production Readiness  
- Test full integration flow before deployment
- Validate all enterprise patterns are implemented
- Monitor cache coherence for performance optimization

---

**🚀 Ready to build world-class Backend Orchestrator features with enterprise-grade patterns!**