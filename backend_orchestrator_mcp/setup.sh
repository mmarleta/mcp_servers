#!/bin/bash

# 🚀 Backend Orchestrator MCP Server Setup Script
# ==============================================
# 
# Automated setup for Backend Orchestrator development tools
# Tech Lead: Optimus Project

set -e  # Exit on any error

echo "🚀 Setting up Backend Orchestrator MCP Server..."

# Configuration
MCP_DIR="/home/marcelo/projetos/oraljet/github/optimus_final/mcp_servers/backend_orchestrator_mcp"
BACKEND_ORCHESTRATOR_DIR="/home/marcelo/projetos/oraljet/github/optimus_final/backend-orchestrator"
CLAUDE_CONFIG_DIR="$HOME/.config/claude-desktop"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Verify dependencies
print_status "Checking system dependencies..."

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is required but not installed" 
    exit 1
fi

print_success "System dependencies verified"

# Step 2: Create virtual environment
print_status "Creating virtual environment..."

cd "$MCP_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Step 3: Activate virtual environment and install dependencies
print_status "Installing Python dependencies..."

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

print_success "Python dependencies installed"

# Step 4: Verify Backend Orchestrator directory exists
print_status "Verifying Backend Orchestrator directory..."

if [ ! -d "$BACKEND_ORCHESTRATOR_DIR" ]; then
    print_error "Backend Orchestrator directory not found: $BACKEND_ORCHESTRATOR_DIR"
    print_error "Please ensure the Optimus project is properly cloned"
    exit 1
fi

print_success "Backend Orchestrator directory verified"

# Step 5: Test MCP server
print_status "Testing MCP server startup..."

# Create test script
cat > test_mcp.py << 'EOF'
import sys
import os
sys.path.insert(0, '/home/marcelo/projetos/oraljet/github/optimus_final/backend-orchestrator')

try:
    from server import server, client
    print("✅ MCP server imports successful")
    
    # Test basic initialization
    if hasattr(server, 'list_tools'):
        print("✅ MCP server tools available")
    else:
        print("❌ MCP server tools not available")
        sys.exit(1)
        
    if hasattr(client, 'check_health'):
        print("✅ Backend Orchestrator client initialized")
    else:
        print("❌ Backend Orchestrator client not initialized")
        sys.exit(1)
        
    print("✅ MCP server test passed")
        
except Exception as e:
    print(f"❌ MCP server test failed: {e}")
    sys.exit(1)
EOF

python test_mcp.py
rm test_mcp.py

print_success "MCP server test passed"

# Step 6: Create Claude Desktop configuration
print_status "Configuring Claude Desktop integration..."

# Create claude-desktop config directory if it doesn't exist
mkdir -p "$CLAUDE_CONFIG_DIR"

# Check if config file exists
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"

if [ -f "$CLAUDE_CONFIG_FILE" ]; then
    print_warning "Claude Desktop config file already exists"
    print_warning "Please manually merge the configuration from:"
    print_warning "$MCP_DIR/claude_desktop_config.json"
else
    # Copy configuration
    cp claude_desktop_config.json "$CLAUDE_CONFIG_FILE"
    print_success "Claude Desktop configuration installed"
fi

# Step 7: Create environment file
print_status "Creating environment configuration..."

cat > .env << EOF
# Backend Orchestrator MCP Server Environment Configuration
# ========================================================

# Service URLs (update these based on your deployment)
BACKEND_ORCHESTRATOR_URL=http://localhost:8020
AI_ENGINE_URL=http://localhost:8010
REDIS_URL=redis://localhost:6379/0

# Development settings
LOG_LEVEL=INFO
PYTHONPATH=$BACKEND_ORCHESTRATOR_DIR:$MCP_DIR

# Optional: Authentication (if required)
# JWT_SECRET_KEY=your-secret-key
# API_KEY=your-api-key
EOF

print_success "Environment configuration created"

# Step 8: Create startup script
print_status "Creating startup script..."

cat > start_mcp_server.sh << 'EOF'
#!/bin/bash

# 🚀 Backend Orchestrator MCP Server Startup
# ==========================================

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment
source venv/bin/activate

# Start MCP server
echo "🚀 Starting Backend Orchestrator MCP Server..."
echo "📡 Backend Orchestrator URL: $BACKEND_ORCHESTRATOR_URL"  
echo "🤖 AI Engine URL: $AI_ENGINE_URL"
echo "📊 Redis URL: $REDIS_URL"
echo ""

python server.py
EOF

chmod +x start_mcp_server.sh

print_success "Startup script created"

# Step 9: Create development helper scripts
print_status "Creating development helper scripts..."

# Health check script
cat > health_check.py << 'EOF'
#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.insert(0, '/home/marcelo/projetos/oraljet/github/optimus_final/backend-orchestrator')

from server import BackendOrchestratorClient

async def main():
    client = BackendOrchestratorClient()
    
    print("🏥 Backend Orchestrator Health Check")
    print("=" * 40)
    
    # Basic health check
    health = await client.check_health()
    print(f"Backend Orchestrator: {health.get('status', 'unknown').upper()}")
    
    # Cache metrics
    cache_metrics = await client.get_cache_metrics()
    if "error" not in cache_metrics:
        hit_rate = cache_metrics.get("hit_rate", 0)
        print(f"Cache Hit Rate: {hit_rate:.1%}")
    else:
        print("Cache Metrics: Not available")
    
    # Rate limiting check
    rate_analysis = await client.analyze_rate_limiting("demo_dentist")
    if "error" not in rate_analysis:
        active_limits = rate_analysis.get("total_active_limits", 0)
        print(f"Active Rate Limits: {active_limits}")
    else:
        print("Rate Limiting: Not available")
        
    print("\n✅ Health check completed")

if __name__ == "__main__":
    asyncio.run(main())
EOF

chmod +x health_check.py

# Quick test script  
cat > quick_test.py << 'EOF'
#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.insert(0, '/home/marcelo/projetos/oraljet/github/optimus_final/backend-orchestrator')

from server import diagnose_gateway_health

async def main():
    print("🧪 Quick MCP Server Test")
    print("=" * 30)
    
    # Test gateway health diagnosis
    result = await diagnose_gateway_health({
        "include_cache_metrics": True,
        "include_rate_limiting": True,
        "tenant_id": "demo_dentist"
    })
    
    print("Gateway Health Diagnosis:")
    for content in result:
        print(content.text[:500] + "..." if len(content.text) > 500 else content.text)
    
    print("\n✅ Quick test completed")

if __name__ == "__main__":
    asyncio.run(main())
EOF

chmod +x quick_test.py

print_success "Development helper scripts created"

# Step 10: Final verification
print_status "Performing final verification..."

# Check file permissions
chmod +x server.py
chmod +x setup.sh

# Verify all files are created
REQUIRED_FILES=(
    "server.py"
    "requirements.txt" 
    "README.md"
    "claude_desktop_config.json"
    ".env"
    "start_mcp_server.sh"
    "health_check.py"
    "quick_test.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "✓ $file"
    else
        print_error "✗ $file missing"
        exit 1
    fi
done

print_success "All required files verified"

# Deactivate virtual environment
deactivate

# Final instructions
echo ""
echo "🎉 Backend Orchestrator MCP Server Setup Complete!"
echo ""
echo "📋 Next Steps:"
echo "  1. Start the Optimus system (Backend Orchestrator + AI Engine + Redis)"
echo "  2. Test MCP server: ./quick_test.py"
echo "  3. Start MCP server: ./start_mcp_server.sh" 
echo "  4. Restart Claude Desktop to load the new MCP server"
echo ""
echo "🔧 Available Commands:"
echo "  ./start_mcp_server.sh    - Start MCP server"
echo "  ./health_check.py        - Check system health"
echo "  ./quick_test.py          - Test MCP functionality" 
echo ""
echo "📖 Documentation: README.md"
echo "⚙️  Configuration: .env"
echo "🖥️  Claude Config: $CLAUDE_CONFIG_FILE"
echo ""
echo "✅ Ready for production-grade Backend Orchestrator development!"