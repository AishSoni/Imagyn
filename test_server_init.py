#!/usr/bin/env python3
"""
Simple test to verify the MCP server can start without errors
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from imagyn.models import ImagynConfig
from imagyn.imagyn_server import MCPServer


async def test_server_initialization():
    """Test that the server can be initialized without errors"""
    print("🚀 Testing MCP Server initialization...")
    
    try:
        # Load config
        config = ImagynConfig.load_from_file("config.json")
        print(f"✅ Config loaded: {config.comfyui_url}")
        
        # Initialize server
        server = MCPServer("config.json")
        print("✅ MCP Server initialized successfully")
        
        # Test workflow loading
        workflow = server.workflow_template
        print(f"✅ Workflow loaded with {len(workflow)} nodes")
        
        print("\n🎉 Server initialization test passed!")
        print("The server is ready to be used with ChatMCP or other MCP clients.")
        
        return True
        
    except Exception as e:
        print(f"❌ Server initialization failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_server_initialization())
    sys.exit(0 if success else 1)
