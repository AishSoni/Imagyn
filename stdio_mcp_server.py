#!/usr/bin/env python3
"""
Simple stdio-based MCP server for Imagyn
This uses the standard stdio transport which is more compatible with most MCP clients
"""

import asyncio
import json
import logging
import sys
import platform
import os
import time
import httpx
import uuid
import websockets
import base64
from pathlib import Path
from typing import Any, Dict, Optional

# Fix for Windows asyncio issues - must be done before any asyncio operations
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Ensure we're using the virtual environment Python
script_dir = Path(__file__).parent
venv_path = script_dir / "imagyn_venv"
if venv_path.exists():
    # Add virtual environment site-packages to Python path
    site_packages = venv_path / "Lib" / "site-packages"
    if site_packages.exists():
        sys.path.insert(0, str(site_packages))

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Set up logging to stderr to avoid interfering with stdio
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("imagyn-mcp")

# Global variables for server state
server_config = None
server_storage = None
server_workflow = None

def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Load configuration from file"""
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            logger.error(f"Config file not found: {config_path}")
            return None
            
        with open(config_file, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded config from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return None

def load_workflow(workflow_path: str) -> Dict[str, Any]:
    """Load workflow template"""
    try:
        workflow_file = Path(workflow_path)
        if not workflow_file.exists():
            logger.error(f"Workflow file not found: {workflow_path}")
            return None
            
        with open(workflow_file, 'r') as f:
            workflow = json.load(f)
        logger.info(f"Loaded workflow from {workflow_path}")
        return workflow
    except Exception as e:
        logger.error(f"Failed to load workflow: {e}")
        return None

# Create the server
server = Server("imagyn-mcp")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="get_server_status",
            description="Get the current status of the Imagyn MCP server",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="test_connection", 
            description="Test the MCP connection",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="generate_image",
            description="Generate an image using ComfyUI with the specified prompt",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The text prompt for image generation"
                    },
                    "negative_prompt": {
                        "type": "string", 
                        "description": "Negative prompt to avoid certain elements"
                    },
                    "width": {
                        "type": "integer",
                        "description": "Image width in pixels",
                        "minimum": 64,
                        "maximum": 2048
                    },
                    "height": {
                        "type": "integer",
                        "description": "Image height in pixels",
                        "minimum": 64,
                        "maximum": 2048
                    },
                    "seed": {
                        "type": "integer",
                        "description": "Seed for reproducible generation (optional)",
                        "minimum": 0
                    }
                },
                "required": ["prompt"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls"""
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    try:
        if name == "get_server_status":
            return await get_server_status()
        elif name == "test_connection":
            return await test_connection()
        elif name == "generate_image":
            return await generate_image(arguments)
        else:
            error_msg = f"Unknown tool: {name}"
            logger.error(error_msg)
            return [types.TextContent(
                type="text",
                text=f"Error: {error_msg}"
            )]
    except Exception as e:
        error_msg = f"Error handling tool {name}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return [types.TextContent(
            type="text",
            text=f"Error: {error_msg}"
        )]

async def get_server_status() -> list[types.TextContent]:
    """Get server status"""
    global server_config, server_storage, server_workflow
    
    status = {
        "status": "running",
        "server_name": "Imagyn MCP Server (stdio)",
        "version": "0.1.0",
        "config_loaded": server_config is not None,
        "workflow_loaded": server_workflow is not None,
        "comfyui_url": server_config.get("comfyui_url", "Not configured") if server_config else "Not configured"
    }
    
    return [types.TextContent(
        type="text", 
        text=json.dumps(status, indent=2)
    )]

async def test_connection() -> list[types.TextContent]:
    """Test connection"""
    return [types.TextContent(
        type="text",
        text="MCP server is responding correctly. Connection test successful."
    )]

async def generate_image(arguments: dict) -> list[types.TextContent | types.ImageContent]:
    """Generate image using ComfyUI"""
    import time
    import httpx
    import uuid
    import websockets
    import base64
    from pathlib import Path
    
    prompt = arguments.get("prompt", "")
    negative_prompt = arguments.get("negative_prompt", "")
    width = arguments.get("width", 1024)
    height = arguments.get("height", 1024)
    seed = arguments.get("seed", None)
    
    if not prompt.strip():
        return [types.TextContent(
            type="text",
            text="Error: Prompt cannot be empty."
        )]
    
    if not server_config:
        return [types.TextContent(
            type="text",
            text="Error: Server configuration not loaded. Cannot generate images."
        )]
    
    if not server_workflow:
        return [types.TextContent(
            type="text",
            text="Error: Workflow template not loaded. Cannot generate images."
        )]
    
    try:
        base_url = server_config.get("comfyui_url", "http://localhost:8188").rstrip('/')
        client_id = str(uuid.uuid4())
        
        # Test connection
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(f"{base_url}/system_stats")
                if response.status_code != 200:
                    return [types.TextContent(
                        type="text",
                        text=f"Error: Cannot connect to ComfyUI at {base_url}"
                    )]
            except Exception as e:
                return [types.TextContent(
                    type="text", 
                    text=f"Error: Cannot connect to ComfyUI at {base_url}: {str(e)}"
                )]
            
            # Prepare workflow
            workflow = json.loads(json.dumps(server_workflow))
            
            # Set the prompt (node 45 is CLIP Text Encode)
            if "45" in workflow:  # Positive prompt node
                workflow["45"]["inputs"]["text"] = prompt
            
            # Set negative prompt (this workflow uses ConditioningZeroOut instead of negative prompt)
            # We'll keep the existing structure for now
                
            # Set seed (node 31 is KSampler)
            if seed is None:
                seed = int(time.time()) % (2**32)
            if "31" in workflow:  # KSampler node
                workflow["31"]["inputs"]["seed"] = seed
                
            # Set dimensions (node 27 is EmptySD3LatentImage)
            if "27" in workflow:  # Empty latent image node
                workflow["27"]["inputs"]["width"] = width
                workflow["27"]["inputs"]["height"] = height
            
            logger.info(f"Generating image: {prompt[:100]}...")
            start_time = time.time()
            
            # Queue the workflow
            prompt_request = {
                "client_id": client_id,
                "prompt": workflow
            }
            
            response = await client.post(f"{base_url}/prompt", json=prompt_request)
            response.raise_for_status()
            result = response.json()
            prompt_id = result["prompt_id"]
            
            # Wait for completion via WebSocket
            ws_url = base_url.replace('http', 'ws') + f"/ws?clientId={client_id}"
            
            async with websockets.connect(ws_url) as websocket:
                timeout = 300  # 5 minutes
                start_ws_time = time.time()
                
                while time.time() - start_ws_time < timeout:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(message)
                        
                        if data["type"] == "executing":
                            executing_data = data["data"]
                            if executing_data["node"] is None and executing_data["prompt_id"] == prompt_id:
                                # Execution completed
                                break
                    except asyncio.TimeoutError:
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        return [types.TextContent(
                            type="text",
                            text="Error: WebSocket connection closed during generation"
                        )]
            
            # Get history and download image
            response = await client.get(f"{base_url}/history/{prompt_id}")
            response.raise_for_status()
            history = response.json()
            
            prompt_history = history.get(prompt_id, {})
            outputs = prompt_history.get("outputs", {})
            
            # Find the SaveImage node output
            save_image_outputs = None
            for node_id, node_output in outputs.items():
                if "images" in node_output:
                    save_image_outputs = node_output["images"]
                    break
            
            if not save_image_outputs:
                return [types.TextContent(
                    type="text",
                    text="Error: No image output found in workflow execution"
                )]
            
            # Download the first image
            image_info = save_image_outputs[0]
            params = {
                "filename": image_info["filename"],
                "type": image_info.get("type", "output")
            }
            if image_info.get("subfolder"):
                params["subfolder"] = image_info["subfolder"]
            
            response = await client.get(f"{base_url}/view", params=params)
            response.raise_for_status()
            image_data = response.content
            
            generation_time = time.time() - start_time
            
            # Store image locally
            output_dir = Path(server_config.get("output_folder", "output"))
            output_dir.mkdir(exist_ok=True)
            
            # Create unique filename
            image_id = f"img_{int(time.time())}_{seed}"
            image_path = output_dir / f"{image_id}.png"
            
            with open(image_path, "wb") as f:
                f.write(image_data)
            
            # Convert to base64 for MCP response
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            logger.info(f"Image generated successfully: {image_id} in {generation_time:.2f}s")
            
            return [
                types.TextContent(
                    type="text",
                    text=f"✅ **Image Generated Successfully!**\n\n"
                         f"**Image ID:** {image_id}\n"
                         f"**Prompt:** {prompt}\n" 
                         f"**Dimensions:** {width}×{height}\n"
                         f"**Seed:** {seed}\n"
                         f"**Generation Time:** {generation_time:.2f}s\n"
                         f"**Saved to:** {image_path}\n\n"
                         f"The image has been generated and is displayed below:"
                ),
                types.ImageContent(
                    type="image",
                    data=base64_data,
                    mimeType="image/png"
                )
            ]
            
    except Exception as e:
        logger.error(f"Image generation failed: {e}", exc_info=True)
        return [types.TextContent(
            type="text",
            text=f"❌ **Image generation failed:** {str(e)}"
        )]

async def main():
    """Main entry point"""
    global server_config, server_workflow
    
    # Ensure we're in the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Load configuration
    config_path = os.getenv("IMAGYN_CONFIG", "config.json")
    logger.info(f"Loading config from: {config_path}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    server_config = load_config(config_path)
    if server_config:
        workflow_file = server_config.get("workflow_file")
        if workflow_file:
            server_workflow = load_workflow(workflow_file)
    
    logger.info("Starting MCP server...")
    
    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("MCP server streams established")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="imagyn-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error running server: {e}", exc_info=True)
        sys.exit(1)
