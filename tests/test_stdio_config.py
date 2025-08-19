#!/usr/bin/env python3
"""
Test script for stdio_mcp_server configuration
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.') / 'src'))

# Import the functions from stdio_mcp_server
import stdio_mcp_server
import asyncio

async def test():
    print("Testing stdio_mcp_server configuration...")
    
    config = stdio_mcp_server.load_config('config.json')
    if config:
        provider = config.get('provider', 'comfyui').lower()
        print(f'✅ Config loaded successfully')
        print(f'✅ Provider: {provider}')
        
        if provider == 'replicate':
            replicate_config = config.get('replicate', {})
            api_key_status = "configured" if replicate_config.get('api_key') else "missing"
            model_id = replicate_config.get('model_id', 'not set')
            print(f'✅ Replicate API key: {api_key_status}')
            print(f'✅ Model ID: {model_id}')
        elif provider == 'comfyui':
            comfyui_url = config.get('comfyui_url', 'not set')
            workflow_file = config.get('workflow_file', 'not set')
            print(f'✅ ComfyUI URL: {comfyui_url}')
            print(f'✅ Workflow file: {workflow_file}')
    else:
        print('❌ Failed to load config')

if __name__ == "__main__":
    asyncio.run(test())
