#!/usr/bin/env python3
"""
Debug script to test MCP tool registration
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from imagyn.imagyn_server import MCPServer


async def test_tool_registration():
    """Test that tools are properly registered"""
    print("🔧 Testing MCP tool registration...")
    
    try:
        # Initialize server
        server = MCPServer("config.json")
        print("✅ MCP Server initialized")
        
        # Get the internal MCP server
        mcp_server = server.server
        
        # Check if tools are registered
        print(f"📊 Server object: {type(mcp_server)}")
        print(f"📊 Server name: {mcp_server.name}")
        
        # Try to manually call list_tools
        tools = await mcp_server.list_tools()
        print(f"✅ Found {len(tools)} tools:")
        
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
        
        return len(tools) > 0
        
    except Exception as e:
        print(f"❌ Tool registration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_tool_registration())
    if success:
        print("\n🎉 Tools are properly registered!")
    else:
        print("\n❌ Tool registration failed!")
    sys.exit(0 if success else 1)
