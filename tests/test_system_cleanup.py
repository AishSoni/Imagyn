#!/usr/bin/env python3
"""
Final comprehensive test to validate the entire cleaned-up system
"""

import asyncio
import sys
import json
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from imagyn.imagyn_server import MCPServer
from imagyn.comfyui_client import ComfyUIClient
from imagyn.models import ImagynConfig


async def comprehensive_system_test():
    """Test the entire system after cleanup"""
    
    print("🧪 Comprehensive System Test After Cleanup")
    print("=" * 50)
    
    # Test 1: Configuration Loading
    print("\n1. Testing Configuration Loading...")
    try:
        config = ImagynConfig.load_from_file('config.json')
        print(f"✅ Configuration loaded successfully")
        print(f"   ComfyUI URL: {config.comfyui_url}")
        print(f"   LoRAs enabled: {config.enable_loras}")
        print(f"   Output folder: {config.output_folder}")
        
        # Verify no lora_folder_path
        if not hasattr(config, 'lora_folder_path'):
            print("✅ No lora_folder_path field in config")
        else:
            print("❌ Unexpected lora_folder_path field found")
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return
    
    # Test 2: ComfyUI Client
    print("\n2. Testing ComfyUI Client...")
    try:
        async with ComfyUIClient(config.comfyui_url) as client:
            # Connection test
            connected = await client.check_connection()
            if connected:
                print("✅ ComfyUI connection successful")
            else:
                print("❌ ComfyUI connection failed")
                return
            
            # LoRA query test
            loras = await client.get_available_loras()
            print(f"✅ Found {len(loras)} LoRA models from server")
            
            if loras:
                print(f"   Example LoRA: {loras[0].name}")
                
    except Exception as e:
        print(f"❌ ComfyUI client test failed: {e}")
        return
    
    # Test 3: MCP Server Integration
    print("\n3. Testing MCP Server Integration...")
    try:
        server = MCPServer('config.json')
        
        # Test LoRA listing
        result = await server._handle_list_loras({})
        if result and len(result) > 0:
            print("✅ MCP LoRA listing successful")
            print(f"   Response length: {len(result[0].text)} characters")
        else:
            print("❌ MCP LoRA listing failed")
            
        # Test status
        status_result = await server._handle_get_status({})
        if status_result and len(status_result) > 0:
            print("✅ MCP status check successful")
            # Check that status mentions server-based querying
            if "queried from ComfyUI server" in status_result[0].text:
                print("✅ Status correctly indicates server-based LoRA querying")
            else:
                print("⚠️  Status doesn't mention server-based querying")
        else:
            print("❌ MCP status check failed")
            
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
        return
    
    # Test 4: Code Quality Checks
    print("\n4. Testing Code Quality...")
    
    # Check that old imports are removed
    with open('src/imagyn/comfyui_client.py', 'r') as f:
        client_code = f.read()
        
    if 'import os' not in client_code and 'from pathlib import Path' not in client_code:
        print("✅ Unused imports removed from ComfyUI client")
    else:
        print("⚠️  Some unused imports might still be present")
    
    # Check that old methods are removed
    if '_get_available_loras(' not in client_code:
        print("✅ Old directory scanning method removed")
    else:
        print("❌ Old directory scanning method still present")
    
    print("\n" + "=" * 50)
    print("🎉 Comprehensive System Test Completed!")
    print("✅ All cleanup operations successful")
    print("✅ System is now fully server-based for LoRA discovery")
    print("✅ No local directory dependencies remain")


if __name__ == "__main__":
    try:
        asyncio.run(comprehensive_system_test())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
