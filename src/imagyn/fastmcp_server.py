"""
Imagyn FastMCP Server - Modern MCP server implementation using FastMCP
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Context

from .models import ImagynConfig
from .comfyui_client import ComfyUIClient
from .storage import ImageStorage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImagynFastMCPServer:
    """Imagyn MCP Server using FastMCP"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = ImagynConfig.load_from_file(config_path)
        self.storage = ImageStorage(self.config.output_folder)
        self.workflow_template = self._load_workflow_template()
        
        # Create FastMCP server
        self.mcp = FastMCP("Imagyn Image Generation Server")
        
        # Register tools
        self._register_tools()
    
    def _load_workflow_template(self) -> Dict[str, Any]:
        """Load the ComfyUI workflow template"""
        workflow_path = Path(self.config.workflow_file)
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {self.config.workflow_file}")
        
        with open(workflow_path, 'r') as f:
            return json.load(f)
    
    def _register_tools(self):
        """Register MCP tools"""
        
        @self.mcp.tool()
        async def generate_image(
            prompt: str,
            negative_prompt: str = "",
            loras: List[str] = None,
            width: int = 1024,
            height: int = 1024,
            seed: Optional[int] = None,
            ctx: Context = None
        ) -> dict:
            """Generate an image from a text prompt using ComfyUI workflows
            
            Args:
                prompt: Text description for image generation
                negative_prompt: Negative prompt to avoid certain elements
                loras: List of LoRA names to apply (if enabled)
                width: Image width in pixels
                height: Image height in pixels
                seed: Random seed for generation (optional)
            """
            if loras is None:
                loras = []
                
            await ctx.info(f"Starting image generation with prompt: {prompt[:100]}...")
            
            # Check if LoRAs are enabled
            if loras and not self.config.enable_loras:
                await ctx.warning("LoRAs are disabled in server configuration. Request will proceed without LoRAs.")
                loras = []
            
            async with ComfyUIClient(self.config.comfyui_url) as client:
                # Check connection
                if not await client.check_connection():
                    await ctx.error(f"Cannot connect to ComfyUI server at {self.config.comfyui_url}")
                    return {"error": f"Cannot connect to ComfyUI server at {self.config.comfyui_url}"}
                
                try:
                    # Generate image
                    await ctx.info("Generating image...")
                    image_data, metadata = await client.generate_image(
                        workflow_template=self.workflow_template,
                        prompt=prompt,
                        negative_prompt=negative_prompt,
                        seed=seed,
                        loras=loras if self.config.enable_loras else [],
                        width=width,
                        height=height
                    )
                    
                    # Store image
                    generated_image = await self.storage.store_image(
                        image_data=image_data,
                        metadata=metadata,
                        include_base64=True
                    )
                    
                    await ctx.info(f"Image generated successfully: {generated_image.image_id}")
                    
                    return {
                        "success": True,
                        "image_id": generated_image.image_id,
                        "prompt": prompt,
                        "seed": metadata.seed,
                        "generation_time": metadata.generation_time,
                        "dimensions": f"{width}x{height}",
                        "file_path": generated_image.file_path,
                        "base64_data": generated_image.base64_data
                    }
                    
                except Exception as e:
                    logger.error(f"Error generating image: {e}")
                    await ctx.error(f"Error generating image: {str(e)}")
                    return {"error": f"Failed to generate image: {str(e)}"}
        
        @self.mcp.tool()
        async def edit_generated_image(
            image_id: str,
            new_prompt: str,
            negative_prompt: str = "",
            loras: List[str] = None,
            edit_strength: float = 0.7,
            ctx: Context = None
        ) -> dict:
            """Edit or refine a previously generated image
            
            Args:
                image_id: ID of the image to edit
                new_prompt: New or modified prompt for the edit
                negative_prompt: Negative prompt for the edit
                loras: LoRAs to apply for the edit
                edit_strength: Denoising strength for edit (0.1-1.0)
            """
            if loras is None:
                loras = []
                
            await ctx.info(f"Starting image edit for image {image_id}")
            
            try:
                # Get original image
                original_image = await self.storage.get_image(image_id)
                if not original_image:
                    return {"error": f"Image with ID {image_id} not found"}
                
                # Load original image data
                original_path = Path(original_image.file_path)
                if not original_path.exists():
                    return {"error": f"Original image file not found: {original_image.file_path}"}
                
                async with ComfyUIClient(self.config.comfyui_url) as client:
                    if not await client.check_connection():
                        return {"error": f"Cannot connect to ComfyUI server at {self.config.comfyui_url}"}
                    
                    # Edit image
                    await ctx.info("Processing image edit...")
                    image_data, metadata = await client.edit_image(
                        workflow_template=self.workflow_template,
                        original_image_path=str(original_path),
                        prompt=new_prompt,
                        negative_prompt=negative_prompt,
                        denoising_strength=edit_strength,
                        loras=loras if self.config.enable_loras else []
                    )
                    
                    # Store edited image
                    edited_image = await self.storage.store_image(
                        image_data=image_data,
                        metadata=metadata,
                        include_base64=True,
                        parent_id=image_id
                    )
                    
                    await ctx.info(f"Image edited successfully: {edited_image.image_id}")
                    
                    return {
                        "success": True,
                        "new_image_id": edited_image.image_id,
                        "original_image_id": image_id,
                        "new_prompt": new_prompt,
                        "edit_strength": edit_strength,
                        "generation_time": metadata.generation_time,
                        "file_path": edited_image.file_path,
                        "base64_data": edited_image.base64_data
                    }
                    
            except Exception as e:
                logger.error(f"Error editing image: {e}")
                await ctx.error(f"Error editing image: {str(e)}")
                return {"error": f"Failed to edit image: {str(e)}"}
        
        @self.mcp.tool()
        async def list_available_loras(ctx: Context = None) -> dict:
            """List available LoRA models for image generation"""
            
            await ctx.info("Listing available LoRA models...")
            
            try:
                if not self.config.enable_loras:
                    return {
                        "loras_enabled": False,
                        "message": "LoRAs are disabled in server configuration",
                        "available_loras": []
                    }
                
                lora_path = Path(self.config.lora_folder_path)
                if not lora_path.exists():
                    return {
                        "loras_enabled": True,
                        "error": f"LoRA folder not found: {self.config.lora_folder_path}",
                        "available_loras": []
                    }
                
                # Find .safetensors files
                lora_files = list(lora_path.glob("*.safetensors"))
                lora_names = [f.stem for f in lora_files]
                
                await ctx.info(f"Found {len(lora_names)} LoRA models")
                
                return {
                    "loras_enabled": True,
                    "lora_folder": str(lora_path),
                    "total_count": len(lora_names),
                    "available_loras": lora_names
                }
                
            except Exception as e:
                logger.error(f"Error listing LoRAs: {e}")
                await ctx.error(f"Error listing LoRAs: {str(e)}")
                return {"error": f"Failed to list LoRAs: {str(e)}"}
        
        @self.mcp.tool()
        async def get_generation_history(
            limit: int = 10,
            image_id: Optional[str] = None,
            ctx: Context = None
        ) -> dict:
            """Get recent image generation history
            
            Args:
                limit: Number of recent generations to return (1-50)
                image_id: Get details for a specific image ID
            """
            
            await ctx.info(f"Retrieving generation history (limit: {limit})")
            
            try:
                if image_id:
                    # Get specific image
                    image = await self.storage.get_image(image_id)
                    if not image:
                        return {"error": f"Image with ID {image_id} not found"}
                    
                    return {
                        "request_type": "specific_image",
                        "image_id": image_id,
                        "image": {
                            "id": image.image_id,
                            "prompt": image.metadata.prompt,
                            "negative_prompt": image.metadata.negative_prompt,
                            "seed": image.metadata.seed,
                            "generation_time": image.metadata.generation_time,
                            "created_at": image.created_at.isoformat(),
                            "file_path": image.file_path,
                            "width": image.metadata.width,
                            "height": image.metadata.height,
                            "loras": image.metadata.loras,
                            "parent_id": image.parent_id
                        }
                    }
                else:
                    # Get recent history
                    limit = max(1, min(50, limit))  # Clamp between 1-50
                    images = await self.storage.get_recent_images(limit)
                    
                    history_items = []
                    for image in images:
                        history_items.append({
                            "id": image.image_id,
                            "prompt": image.metadata.prompt[:100] + "..." if len(image.metadata.prompt) > 100 else image.metadata.prompt,
                            "seed": image.metadata.seed,
                            "generation_time": image.metadata.generation_time,
                            "created_at": image.created_at.isoformat(),
                            "dimensions": f"{image.metadata.width}x{image.metadata.height}",
                            "parent_id": image.parent_id
                        })
                    
                    await ctx.info(f"Retrieved {len(history_items)} recent generations")
                    
                    return {
                        "request_type": "recent_history",
                        "limit": limit,
                        "total_returned": len(history_items),
                        "history": history_items
                    }
                    
            except Exception as e:
                logger.error(f"Error getting history: {e}")
                await ctx.error(f"Error getting history: {str(e)}")
                return {"error": f"Failed to get generation history: {str(e)}"}
        
        @self.mcp.tool()
        async def get_server_status(ctx: Context = None) -> dict:
            """Get server status and configuration information"""
            
            await ctx.info("Getting server status...")
            
            try:
                # Check ComfyUI connection
                comfyui_status = "unknown"
                try:
                    async with ComfyUIClient(self.config.comfyui_url) as client:
                        if await client.check_connection():
                            comfyui_status = "connected"
                        else:
                            comfyui_status = "disconnected"
                except Exception:
                    comfyui_status = "error"
                
                # Get storage statistics
                storage_stats = await self.storage.get_storage_stats()
                
                await ctx.info("Server status retrieved successfully")
                
                return {
                    "server_name": "Imagyn MCP Server",
                    "version": "0.1.0",
                    "status": "running",
                    "comfyui": {
                        "url": self.config.comfyui_url,
                        "status": comfyui_status
                    },
                    "configuration": {
                        "workflow_file": self.config.workflow_file,
                        "loras_enabled": self.config.enable_loras,
                        "lora_folder": self.config.lora_folder_path,
                        "output_folder": self.config.output_folder,
                        "max_concurrent_generations": self.config.max_concurrent_generations,
                        "default_timeout": self.config.default_generation_timeout
                    },
                    "storage": storage_stats
                }
                
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                await ctx.error(f"Error getting status: {str(e)}")
                return {"error": f"Failed to get server status: {str(e)}"}
    
    def run(self):
        """Run the FastMCP server"""
        logger.info("Starting Imagyn FastMCP Server...")
        
        # Validate configuration
        try:
            workflow_path = Path(self.config.workflow_file)
            if not workflow_path.exists():
                logger.error(f"Workflow file not found: {self.config.workflow_file}")
                return
            
            if self.config.enable_loras:
                lora_path = Path(self.config.lora_folder_path)
                if not lora_path.exists():
                    logger.warning(f"LoRA folder not found: {self.config.lora_folder_path}")
        
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return
        
        logger.info(f"ComfyUI URL: {self.config.comfyui_url}")
        logger.info(f"Workflow: {self.config.workflow_file}")
        logger.info(f"LoRAs enabled: {self.config.enable_loras}")
        logger.info(f"Output folder: {self.config.output_folder}")
        
        # Run the server using stdio transport (default)
        self.mcp.run()
