"""
MCPServer - Implements the MCP protocol and exposes image generation tools
"""

import asyncio
import json
import random
import logging
from typing import Any, Dict, List, Optional, Sequence
from pathlib import Path

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio

from .models import ImagynConfig
from .comfyui_client import ComfyUIClient
from .storage import ImageStorage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPServer:
    """Main MCP Server for Imagyn image generation"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = ImagynConfig.load_from_file(config_path)
        self.server = Server("imagyn-mcp-server")
        self.storage = ImageStorage(self.config.output_folder)
        self.workflow_template = self._load_workflow_template()
        
        # Setup MCP tools
        self._setup_tools()
    
    def _load_workflow_template(self) -> Dict[str, Any]:
        """Load the ComfyUI workflow template"""
        workflow_path = Path(self.config.workflow_file)
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {self.config.workflow_file}")
        
        with open(workflow_path, 'r') as f:
            return json.load(f)
    
    def _setup_tools(self):
        """Setup MCP tools"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools"""
            return [
                types.Tool(
                    name="generate_image",
                    description="Generate an image from a text prompt using ComfyUI workflows",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "Text description for image generation"
                            },
                            "negative_prompt": {
                                "type": "string",
                                "description": "Negative prompt to avoid certain elements",
                                "default": ""
                            },
                            "loras": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of LoRA names to apply (if enabled)",
                                "default": []
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
                                "description": "Random seed for generation (optional)"
                            }
                        },
                        "required": ["prompt"]
                    }
                ),
                types.Tool(
                    name="edit_generated_image",
                    description="Edit or refine a previously generated image",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "image_id": {
                                "type": "string",
                                "description": "ID of the image to edit"
                            },
                            "new_prompt": {
                                "type": "string",
                                "description": "New or modified prompt for the edit"
                            },
                            "negative_prompt": {
                                "type": "string",
                                "description": "Negative prompt for the edit",
                                "default": ""
                            },
                            "loras": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "LoRAs to apply for the edit",
                                "default": []
                            },
                            "edit_strength": {
                                "type": "number",
                                "description": "Denoising strength for edit (0.1-1.0)",
                                "minimum": 0.1,
                                "maximum": 1.0,
                                "default": 0.7
                            }
                        },
                        "required": ["image_id", "new_prompt"]
                    }
                ),
                types.Tool(
                    name="list_available_loras",
                    description="List available LoRA models for image generation",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                types.Tool(
                    name="get_generation_history",
                    description="Get recent image generation history",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Number of recent generations to return",
                                "minimum": 1,
                                "maximum": 50,
                                "default": 10
                            },
                            "image_id": {
                                "type": "string",
                                "description": "Get details for a specific image ID"
                            }
                        },
                        "additionalProperties": False
                    }
                ),
                types.Tool(
                    name="get_server_status",
                    description="Get server status and configuration information",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Handle tool calls"""
            
            try:
                if name == "generate_image":
                    return await self._handle_generate_image(arguments)
                elif name == "edit_generated_image":
                    return await self._handle_edit_image(arguments)
                elif name == "list_available_loras":
                    return await self._handle_list_loras(arguments)
                elif name == "get_generation_history":
                    return await self._handle_get_history(arguments)
                elif name == "get_server_status":
                    return await self._handle_get_status(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error handling tool call {name}: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]
    
    async def _handle_generate_image(self, arguments: dict) -> list[types.TextContent | types.ImageContent]:
        """Handle image generation requests"""
        
        prompt = arguments["prompt"]
        negative_prompt = arguments.get("negative_prompt", "")
        loras = arguments.get("loras", [])
        width = arguments.get("width", 1024)
        height = arguments.get("height", 1024)
        seed = arguments.get("seed")
        
        # Check if LoRAs are enabled
        if loras and not self.config.enable_loras:
            return [types.TextContent(
                type="text",
                text="LoRAs are disabled in server configuration. Request will proceed without LoRAs."
            )]
        
        async with ComfyUIClient(
            self.config.comfyui_url,
            http_timeout=self.config.http_timeout,
            websocket_timeout=self.config.websocket_timeout
        ) as client:
            # Check connection
            if not await client.check_connection():
                return [types.TextContent(
                    type="text",
                    text=f"Error: Cannot connect to ComfyUI server at {self.config.comfyui_url}"
                )]
            
            try:
                # Generate image
                logger.info(f"Generating image with prompt: {prompt[:100]}...")
                image_data, metadata = await client.generate_image(
                    workflow_template=self.workflow_template,
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    seed=seed,
                    loras=loras if self.config.enable_loras else [],
                    width=width,
                    height=height,
                    enable_loras=self.config.enable_loras
                )
                
                # Store image
                generated_image = await self.storage.store_image(
                    image_data=image_data,
                    metadata=metadata,
                    include_base64=True
                )
                
                logger.info(f"Image generated successfully: {generated_image.image_id}")
                
                # Return both text and image content
                return [
                    types.TextContent(
                        type="text",
                        text=f"Image generated successfully!\n\n"
                             f"**Image ID:** {generated_image.image_id}\n"
                             f"**Prompt:** {prompt}\n"
                             f"**Seed:** {metadata.seed}\n"
                             f"**Generation Time:** {metadata.generation_time:.2f}s\n"
                             f"**Dimensions:** {width}x{height}\n"
                             f"**LoRAs Used:** {', '.join(metadata.loras_used) if metadata.loras_used else 'None'}"
                    ),
                    types.ImageContent(
                        type="image",
                        data=generated_image.base64_data,
                        mimeType="image/png"
                    )
                ]
                
            except Exception as e:
                logger.error(f"Image generation failed: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Image generation failed: {str(e)}"
                )]
    
    async def _handle_edit_image(self, arguments: dict) -> list[types.TextContent | types.ImageContent]:
        """Handle image editing requests"""
        
        image_id = arguments["image_id"]
        new_prompt = arguments["new_prompt"]
        negative_prompt = arguments.get("negative_prompt", "")
        loras = arguments.get("loras", [])
        edit_strength = arguments.get("edit_strength", 0.7)
        
        # Get original image
        original_image = await self.storage.get_image(image_id)
        if not original_image:
            return [types.TextContent(
                type="text",
                text=f"Error: Image with ID {image_id} not found"
            )]
        
        # For now, treat image editing as a new generation with the same parameters
        # In a full implementation, this would use img2img workflows
        async with ComfyUIClient(
            self.config.comfyui_url,
            http_timeout=self.config.http_timeout,
            websocket_timeout=self.config.websocket_timeout
        ) as client:
            if not await client.check_connection():
                return [types.TextContent(
                    type="text",
                    text=f"Error: Cannot connect to ComfyUI server at {self.config.comfyui_url}"
                )]
            
            try:
                # Generate new image based on edit
                logger.info(f"Editing image {image_id} with new prompt: {new_prompt[:100]}...")
                image_data, metadata = await client.generate_image(
                    workflow_template=self.workflow_template,
                    prompt=new_prompt,
                    negative_prompt=negative_prompt,
                    seed=None,  # Use random seed for variation
                    loras=loras if self.config.enable_loras else [],
                    width=original_image.metadata.width,
                    height=original_image.metadata.height,
                    enable_loras=self.config.enable_loras
                )
                
                # Store the edited image
                generated_image = await self.storage.store_image(
                    image_data=image_data,
                    metadata=metadata,
                    include_base64=True
                )
                
                logger.info(f"Image edited successfully: {generated_image.image_id}")
                
                return [
                    types.TextContent(
                        type="text",
                        text=f"Image edited successfully!\n\n"
                             f"**New Image ID:** {generated_image.image_id}\n"
                             f"**Original Image ID:** {image_id}\n"
                             f"**New Prompt:** {new_prompt}\n"
                             f"**Seed:** {metadata.seed}\n"
                             f"**Generation Time:** {metadata.generation_time:.2f}s"
                    ),
                    types.ImageContent(
                        type="image",
                        data=generated_image.base64_data,
                        mimeType="image/png"
                    )
                ]
                
            except Exception as e:
                logger.error(f"Image editing failed: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Image editing failed: {str(e)}"
                )]
    
    async def _handle_list_loras(self, arguments: dict) -> list[types.TextContent]:
        """Handle LoRA listing requests"""
        
        if not self.config.enable_loras:
            return [types.TextContent(
                type="text",
                text="LoRAs are disabled in server configuration."
            )]
        
        async with ComfyUIClient(
            self.config.comfyui_url,
            http_timeout=self.config.http_timeout,
            websocket_timeout=self.config.websocket_timeout
        ) as client:
            try:
                # Check connection first
                if not await client.check_connection():
                    return [types.TextContent(
                        type="text",
                        text=f"Error: Cannot connect to ComfyUI server at {self.config.comfyui_url}"
                    )]
                
                loras = await client.get_available_loras()
                
                if not loras:
                    return [types.TextContent(
                        type="text",
                        text="No LoRA models found on the ComfyUI server."
                    )]
                
                lora_list = []
                for lora in loras:
                    lora_list.append(f"- **{lora.name}**: {lora.description}")
                
                return [types.TextContent(
                    type="text",
                    text=f"Available LoRA Models ({len(loras)} found from ComfyUI server):\n\n" + "\n".join(lora_list)
                )]
                
            except Exception as e:
                logger.error(f"Failed to list LoRAs from ComfyUI server: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Failed to list LoRAs from ComfyUI server: {str(e)}"
                )]
    
    async def _handle_get_history(self, arguments: dict) -> list[types.TextContent]:
        """Handle generation history requests"""
        
        image_id = arguments.get("image_id")
        limit = arguments.get("limit", 10)
        
        try:
            if image_id:
                # Get specific image details
                image = await self.storage.get_image(image_id)
                if not image:
                    return [types.TextContent(
                        type="text",
                        text=f"Image with ID {image_id} not found"
                    )]
                
                return [types.TextContent(
                    type="text",
                    text=f"**Image Details**\n\n"
                         f"**ID:** {image.image_id}\n"
                         f"**Created:** {image.created_at}\n"
                         f"**Prompt:** {image.metadata.prompt}\n"
                         f"**Negative Prompt:** {image.metadata.negative_prompt or 'None'}\n"
                         f"**Seed:** {image.metadata.seed}\n"
                         f"**Dimensions:** {image.metadata.width}x{image.metadata.height}\n"
                         f"**Steps:** {image.metadata.steps}\n"
                         f"**CFG:** {image.metadata.cfg}\n"
                         f"**Generation Time:** {image.metadata.generation_time:.2f}s\n"
                         f"**LoRAs Used:** {', '.join(image.metadata.loras_used) if image.metadata.loras_used else 'None'}\n"
                         f"**File Path:** {image.file_path}"
                )]
            else:
                # Get recent images
                recent_images = await self.storage.get_recent_images(limit)
                
                if not recent_images:
                    return [types.TextContent(
                        type="text",
                        text="No images found in generation history"
                    )]
                
                history_text = f"**Recent Generations** (Last {len(recent_images)} images):\n\n"
                for i, image in enumerate(recent_images, 1):
                    history_text += (
                        f"{i}. **{image.image_id[:8]}...** - {image.created_at}\n"
                        f"   Prompt: {image.metadata.prompt[:80]}{'...' if len(image.metadata.prompt) > 80 else ''}\n"
                        f"   Seed: {image.metadata.seed}, Time: {image.metadata.generation_time:.2f}s\n\n"
                    )
                
                return [types.TextContent(type="text", text=history_text)]
                
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return [types.TextContent(
                type="text",
                text=f"Failed to get generation history: {str(e)}"
            )]
    
    async def _handle_get_status(self, arguments: dict) -> list[types.TextContent]:
        """Handle server status requests"""
        
        try:
            # Check ComfyUI connection
            async with ComfyUIClient(
                self.config.comfyui_url,
                http_timeout=self.config.http_timeout,
                websocket_timeout=self.config.websocket_timeout
            ) as client:
                comfyui_status = await client.check_connection()
            
            # Get storage stats
            storage_stats = await self.storage.get_storage_stats()
            
            status_text = f"""**Imagyn MCP Server Status**

**ComfyUI Connection:** {'✅ Connected' if comfyui_status else '❌ Disconnected'}
**ComfyUI URL:** {self.config.comfyui_url}
**Workflow File:** {self.config.workflow_file}
**LoRAs Enabled:** {'✅ Yes (queried from ComfyUI server)' if self.config.enable_loras else '❌ No'}
**Output Folder:** {self.config.output_folder}
**Max Concurrent Generations:** {self.config.max_concurrent_generations}

**Timeout Configuration:**
- HTTP Timeout: {self.config.http_timeout}s
- WebSocket Timeout: {self.config.websocket_timeout}s  
- Generation Timeout: {self.config.default_generation_timeout}s

**Storage Statistics:**
- Total Images: {storage_stats['total_images']}
- Total Size: {storage_stats['total_size_mb']} MB
- Storage Location: {storage_stats['output_folder']}
"""
            
            return [types.TextContent(type="text", text=status_text)]
            
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return [types.TextContent(
                type="text",
                text=f"Failed to get server status: {str(e)}"
            )]
    
    async def start(self):
        """Start the MCP server"""
        logger.info("Starting Imagyn MCP Server...")
        
        # Validate configuration
        try:
            workflow_path = Path(self.config.workflow_file)
            if not workflow_path.exists():
                logger.error(f"Workflow file not found: {self.config.workflow_file}")
                return
        
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return
        
        logger.info(f"ComfyUI URL: {self.config.comfyui_url}")
        logger.info(f"Workflow: {self.config.workflow_file}")
        logger.info(f"LoRAs enabled: {self.config.enable_loras} (queried from ComfyUI server)")
        logger.info(f"Output folder: {self.config.output_folder}")
        
        # Run the MCP server
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="imagyn-mcp-server",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options={},
                        experimental_capabilities={},
                    ),
                ),
            )
