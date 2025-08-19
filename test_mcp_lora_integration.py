#!/usr/bin/env python3
"""
Test script to validate MCP server LoRA listing functionality
"""

import asyncio
import sys
import json
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from imagyn.imagyn_server import MCPServer
from imagyn.models import ImagynConfig


async def test_mcp_lora_listing():
    """Test MCP server LoRA listing functionality"""
    
    print("Testing MCP Server LoRA Listing...")
    
    # Create a test configuration
    test_config = {
        "comfyui_url": "http://localhost:8000",
        "workflow_file": "workflows/fluxkrea.json",
        "enable_loras": True,
        "output_folder": "output"
    }
    
    # Save temporary config
    config_path = "test_config.json"
    with open(config_path, 'w') as f:
        json.dump(test_config, f, indent=2)
    
    try:
        # Create MCP server instance
        server = MCPServer(config_path)
        
        # Test LoRA listing
        print("\nTesting list_available_loras tool...")
        result = await server._handle_list_loras({})
        
        if result and len(result) > 0:
            print("✅ LoRA listing successful!")
            print("Response:")
            print(result[0].text)
        else:
            print("❌ LoRA listing failed - no results returned")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test config
        if Path(config_path).exists():
            Path(config_path).unlink()


if __name__ == "__main__":
    try:
        asyncio.run(test_mcp_lora_listing())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
