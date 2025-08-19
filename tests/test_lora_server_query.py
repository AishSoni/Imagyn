#!/usr/bin/env python3
"""
Test script to validate LoRA querying from ComfyUI server
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from imagyn.comfyui_client import ComfyUIClient


async def test_lora_server_query():
    """Test querying LoRAs from ComfyUI server"""
    
    # Test with ComfyUI URL on port 8000
    comfyui_url = "http://localhost:8000"
    
    print(f"Testing LoRA query from ComfyUI server at: {comfyui_url}")
    
    async with ComfyUIClient(comfyui_url) as client:
        # Test connection
        print("Checking connection to ComfyUI server...")
        connected = await client.check_connection()
        if not connected:
            print(f"❌ Cannot connect to ComfyUI server at {comfyui_url}")
            print("Please ensure ComfyUI is running on the specified URL.")
            return
        
        print("✅ Connected to ComfyUI server")
        
        # Test LoRA querying
        print("\nQuerying available LoRAs from server...")
        try:
            loras = await client.get_available_loras()
            
            if loras:
                print(f"✅ Found {len(loras)} LoRA models:")
                for i, lora in enumerate(loras[:10], 1):  # Show first 10
                    print(f"  {i}. {lora.name} ({lora.file_path})")
                if len(loras) > 10:
                    print(f"  ... and {len(loras) - 10} more")
            else:
                print("ℹ️  No LoRA models found on the server")
                
        except Exception as e:
            print(f"❌ Failed to query LoRAs: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(test_lora_server_query())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
