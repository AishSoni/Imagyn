#!/usr/bin/env python3
"""
Simple stdio-based MCP server for Imagyn
This uses the standard stdio transport which is more compatible with most MCP clients
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

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
                        "description": "Negative prompt to avoid certain elements",
                        "default": ""
                    },
                    "width": {
                        "type": "integer",
                        "description": "Image width in pixels",
                        "default": 1024
                    },
                    "height": {
                        "type": "integer",
                        "description": "Image height in pixels", 
                        "default": 1024
                    },
                    "seed": {
                        "type": "integer",
                        "description": "Seed for reproducible generation (optional)"
                    }
                },
                "required": ["prompt"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls"""
    try:
        if name == "get_server_status":
            return await get_server_status()
        elif name == "test_connection":
            return await test_connection()
        elif name == "generate_image":
            return await generate_image(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Error handling tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
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

async def generate_image(arguments: dict) -> list[types.TextContent]:
    """Generate image (placeholder implementation)"""
    prompt = arguments.get("prompt", "")
    negative_prompt = arguments.get("negative_prompt", "")
    width = arguments.get("width", 1024)
    height = arguments.get("height", 1024)
    seed = arguments.get("seed")
    
    if not server_config:
        return [types.TextContent(
            type="text",
            text="Error: Server configuration not loaded. Cannot generate images."
        )]
    
    # For now, return a placeholder response
    response = {
        "status": "placeholder",
        "message": "Image generation would be performed with these parameters:",
        "parameters": {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "seed": seed,
            "comfyui_url": server_config.get("comfyui_url")
        },
        "note": "This is a test response. Full image generation requires ComfyUI integration."
    }
    
    return [types.TextContent(
        type="text",
        text=json.dumps(response, indent=2)
    )]

async def main():
    """Main entry point"""
    global server_config, server_workflow
    
    # Load configuration
    import os
    config_path = os.getenv("IMAGYN_CONFIG", "config.json")
    logger.info(f"Loading config from: {config_path}")
    
    server_config = load_config(config_path)
    if server_config:
        workflow_file = server_config.get("workflow_file")
        if workflow_file:
            server_workflow = load_workflow(workflow_file)
    
    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
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
    asyncio.run(main())
