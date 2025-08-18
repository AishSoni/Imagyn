"""
Robust Imagyn MCP Server with better error handling
"""

import asyncio
import json
import logging
import sys
import traceback
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Context

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)  # Log to stderr to avoid interfering with stdio
    ]
)
logger = logging.getLogger(__name__)

try:
    # Add the src directory to the Python path
    src_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(src_dir))
    
    from imagyn.models import ImagynConfig
    from imagyn.comfyui_client import ComfyUIClient
    from imagyn.storage import ImageStorage
    
    logger.info("Successfully imported Imagyn modules")
except Exception as e:
    logger.error(f"Failed to import Imagyn modules: {e}")
    # Create a fallback server with limited functionality
    pass

class RobustImagynServer:
    """Robust Imagyn MCP Server with comprehensive error handling"""
    
    def __init__(self, config_path: str = "config.json"):
        self.mcp = FastMCP("Imagyn Image Generation Server")
        self.config = None
        self.storage = None
        self.workflow_template = None
        self.initialization_error = None
        
        try:
            self._initialize_components(config_path)
            logger.info("Server components initialized successfully")
        except Exception as e:
            self.initialization_error = str(e)
            logger.error(f"Server initialization failed: {e}")
            logger.error(traceback.format_exc())
        
        # Register tools (even if initialization failed, we provide error responses)
        self._register_tools()
    
    def _initialize_components(self, config_path: str):
        """Initialize server components with error handling"""
        try:
            self.config = ImagynConfig.load_from_file(config_path)
            self.storage = ImageStorage(self.config.output_folder)
            self.workflow_template = self._load_workflow_template()
        except Exception as e:
            raise Exception(f"Component initialization failed: {e}")
    
    def _load_workflow_template(self) -> Dict[str, Any]:
        """Load the ComfyUI workflow template"""
        try:
            workflow_path = Path(self.config.workflow_file)
            if not workflow_path.exists():
                raise FileNotFoundError(f"Workflow file not found: {self.config.workflow_file}")
            
            with open(workflow_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load workflow template: {e}")
    
    def _register_tools(self):
        """Register MCP tools with comprehensive error handling"""
        
        @self.mcp.tool()
        async def get_server_status(ctx: Context = None) -> dict:
            """Get server status and configuration information"""
            try:
                if ctx:
                    await ctx.info("Getting server status...")
                
                if self.initialization_error:
                    return {
                        "status": "error",
                        "error": self.initialization_error,
                        "server_name": "Imagyn MCP Server",
                        "version": "0.1.0"
                    }
                
                # Check ComfyUI connection if everything is initialized
                comfyui_status = "unknown"
                if self.config:
                    try:
                        async with ComfyUIClient(self.config.comfyui_url) as client:
                            if await client.check_connection():
                                comfyui_status = "connected"
                            else:
                                comfyui_status = "disconnected"
                    except Exception:
                        comfyui_status = "error"
                
                return {
                    "status": "running",
                    "server_name": "Imagyn MCP Server", 
                    "version": "0.1.0",
                    "comfyui_status": comfyui_status,
                    "config_loaded": self.config is not None,
                    "storage_initialized": self.storage is not None,
                    "workflow_loaded": self.workflow_template is not None
                }
                
            except Exception as e:
                logger.error(f"Error in get_server_status: {e}")
                return {"error": f"Failed to get server status: {str(e)}"}
        
        @self.mcp.tool()
        async def test_connection(ctx: Context = None) -> dict:
            """Test the MCP connection"""
            try:
                if ctx:
                    await ctx.info("Testing MCP connection...")
                
                return {
                    "status": "success",
                    "message": "MCP server is responding correctly",
                    "server_initialized": self.initialization_error is None
                }
            except Exception as e:
                logger.error(f"Error in test_connection: {e}")
                return {"error": f"Connection test failed: {str(e)}"}
        
        @self.mcp.tool()
        async def generate_image(
            prompt: str,
            negative_prompt: str = "",
            width: int = 1024,
            height: int = 1024,
            seed: Optional[int] = None,
            ctx: Context = None
        ) -> dict:
            """Generate an image from a text prompt using ComfyUI workflows"""
            try:
                if ctx:
                    await ctx.info(f"Starting image generation with prompt: {prompt[:100]}...")
                
                if self.initialization_error:
                    return {"error": f"Server not properly initialized: {self.initialization_error}"}
                
                if not self.config or not self.storage or not self.workflow_template:
                    return {"error": "Server components not properly loaded"}
                
                async with ComfyUIClient(self.config.comfyui_url) as client:
                    if not await client.check_connection():
                        return {"error": f"Cannot connect to ComfyUI server at {self.config.comfyui_url}"}
                    
                    # Generate image
                    if ctx:
                        await ctx.info("Generating image...")
                    
                    image_data, metadata = await client.generate_image(
                        workflow_template=self.workflow_template,
                        prompt=prompt,
                        negative_prompt=negative_prompt,
                        seed=seed,
                        loras=[],  # Simplified for now
                        width=width,
                        height=height
                    )
                    
                    # Store image
                    generated_image = await self.storage.store_image(
                        image_data=image_data,
                        metadata=metadata,
                        include_base64=True
                    )
                    
                    if ctx:
                        await ctx.info(f"Image generated successfully: {generated_image.image_id}")
                    
                    return {
                        "success": True,
                        "image_id": generated_image.image_id,
                        "prompt": prompt,
                        "seed": metadata.seed,
                        "generation_time": metadata.generation_time,
                        "dimensions": f"{width}x{height}",
                        "file_path": generated_image.file_path
                    }
                    
            except Exception as e:
                logger.error(f"Error in generate_image: {e}")
                logger.error(traceback.format_exc())
                if ctx:
                    await ctx.error(f"Error generating image: {str(e)}")
                return {"error": f"Failed to generate image: {str(e)}"}
    
    def run(self):
        """Run the server with comprehensive error handling"""
        try:
            logger.info("Starting Robust Imagyn MCP Server...")
            
            if self.initialization_error:
                logger.warning(f"Server starting with initialization error: {self.initialization_error}")
            else:
                logger.info("Server fully initialized and ready")
            
            # Run the server
            self.mcp.run()
            
        except Exception as e:
            logger.error(f"Server run failed: {e}")
            logger.error(traceback.format_exc())
            raise


def main():
    """Main entry point with error handling"""
    try:
        import os
        config_path = os.getenv("IMAGYN_CONFIG", "config.json")
        server = RobustImagynServer(config_path=config_path)
        server.run()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
