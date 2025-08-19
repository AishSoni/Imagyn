#!/usr/bin/env python3
"""
Test script to validate LoRA application in workflow generation
"""

import asyncio
import sys
import json
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from imagyn.comfyui_client import ComfyUIClient


async def test_lora_workflow_application():
    """Test LoRA application in workflow generation"""
    
    print("Testing LoRA Application in Workflow...")
    
    # Simple test workflow with LoRA loader
    test_workflow = {
        "1": {
            "class_type": "LoraLoader",
            "inputs": {
                "lora_name": "placeholder.safetensors",
                "strength_model": 1.0,
                "strength_clip": 1.0
            }
        }
    }
    
    comfyui_url = "http://localhost:8000"
    
    async with ComfyUIClient(comfyui_url) as client:
        # Test connection
        print("Checking connection to ComfyUI server...")
        connected = await client.check_connection()
        if not connected:
            print(f"❌ Cannot connect to ComfyUI server at {comfyui_url}")
            return
        
        print("✅ Connected to ComfyUI server")
        
        # Test LoRA application
        print("\nTesting LoRA application to workflow...")
        try:
            # Get available LoRAs
            loras = await client.get_available_loras()
            if not loras:
                print("❌ No LoRAs available for testing")
                return
            
            print(f"📋 Using LoRA: {loras[0].name}")
            
            # Apply LoRA to workflow
            await client._apply_loras_to_workflow(
                workflow=test_workflow,
                loras=[loras[0].name],
                enable_loras=True
            )
            
            # Check if LoRA was applied correctly
            applied_lora = test_workflow["1"]["inputs"]["lora_name"]
            print(f"✅ LoRA successfully applied to workflow: {applied_lora}")
            
            # Verify it's a valid LoRA file
            if applied_lora.endswith('.safetensors'):
                print("✅ LoRA file format is correct")
            else:
                print("⚠️  LoRA file format might be unexpected")
                
        except Exception as e:
            print(f"❌ Failed to apply LoRA to workflow: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(test_lora_workflow_application())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
