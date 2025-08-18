"""
Image storage and management for Imagyn MCP server
"""

import os
import json
import uuid
import base64
import aiofiles
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from .models import GeneratedImage, GenerationMetadata


class ImageStorage:
    """Manages storage and retrieval of generated images"""
    
    def __init__(self, output_folder: str = "output"):
        self.output_folder = Path(output_folder)
        self.metadata_file = self.output_folder / "metadata.json"
        self.images_folder = self.output_folder / "images"
        
        # Create directories if they don't exist
        self.output_folder.mkdir(exist_ok=True)
        self.images_folder.mkdir(exist_ok=True)
        
        # Load existing metadata
        self._metadata_cache: Dict[str, Dict] = {}
        self._load_metadata()
    
    def _load_metadata(self):
        """Load metadata from disk"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    self._metadata_cache = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self._metadata_cache = {}
    
    async def _save_metadata(self):
        """Save metadata to disk"""
        async with aiofiles.open(self.metadata_file, 'w') as f:
            await f.write(json.dumps(self._metadata_cache, indent=2))
    
    async def store_image(
        self,
        image_data: bytes,
        metadata: GenerationMetadata,
        include_base64: bool = True
    ) -> GeneratedImage:
        """Store an image with metadata"""
        
        # Generate unique image ID
        image_id = str(uuid.uuid4())
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{image_id[:8]}.png"
        file_path = self.images_folder / filename
        
        # Save image to disk
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(image_data)
        
        # Create base64 data if requested
        base64_data = None
        if include_base64:
            base64_data = base64.b64encode(image_data).decode('utf-8')
        
        # Create generated image object
        generated_image = GeneratedImage(
            image_id=image_id,
            file_path=str(file_path.absolute()),
            metadata=metadata,
            created_at=datetime.now().isoformat(),
            base64_data=base64_data
        )
        
        # Store metadata
        self._metadata_cache[image_id] = generated_image.to_dict()
        await self._save_metadata()
        
        return generated_image
    
    async def get_image(self, image_id: str, include_base64: bool = False) -> Optional[GeneratedImage]:
        """Retrieve an image by ID"""
        
        if image_id not in self._metadata_cache:
            return None
        
        image_data = self._metadata_cache[image_id]
        
        # Load base64 data if requested
        base64_data = image_data.get("base64_data")
        if include_base64 and not base64_data:
            try:
                async with aiofiles.open(image_data["file_path"], 'rb') as f:
                    image_bytes = await f.read()
                    base64_data = base64.b64encode(image_bytes).decode('utf-8')
            except FileNotFoundError:
                return None
        
        # Reconstruct metadata
        metadata_dict = image_data["metadata"]
        metadata = GenerationMetadata(
            prompt=metadata_dict["prompt"],
            negative_prompt=metadata_dict.get("negative_prompt", ""),
            loras_used=metadata_dict.get("loras_used", []),
            generation_time=metadata_dict.get("generation_time", 0.0),
            seed=metadata_dict.get("seed", 0),
            width=metadata_dict.get("width", 1024),
            height=metadata_dict.get("height", 1024),
            steps=metadata_dict.get("steps", 20),
            cfg=metadata_dict.get("cfg", 3.5),
            workflow_used=metadata_dict.get("workflow_used", "")
        )
        
        return GeneratedImage(
            image_id=image_id,
            file_path=image_data["file_path"],
            metadata=metadata,
            created_at=image_data["created_at"],
            base64_data=base64_data
        )
    
    async def get_recent_images(self, limit: int = 10) -> List[GeneratedImage]:
        """Get recent images sorted by creation time"""
        
        # Sort by creation time (most recent first)
        sorted_items = sorted(
            self._metadata_cache.items(),
            key=lambda x: x[1]["created_at"],
            reverse=True
        )
        
        images = []
        for image_id, _ in sorted_items[:limit]:
            image = await self.get_image(image_id)
            if image:
                images.append(image)
        
        return images
    
    async def delete_image(self, image_id: str) -> bool:
        """Delete an image and its metadata"""
        
        if image_id not in self._metadata_cache:
            return False
        
        image_data = self._metadata_cache[image_id]
        
        # Delete file
        try:
            file_path = Path(image_data["file_path"])
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass  # Continue even if file deletion fails
        
        # Remove from metadata
        del self._metadata_cache[image_id]
        await self._save_metadata()
        
        return True
    
    async def get_storage_stats(self) -> Dict[str, any]:
        """Get storage statistics"""
        
        total_images = len(self._metadata_cache)
        total_size = 0
        
        for image_data in self._metadata_cache.values():
            try:
                file_path = Path(image_data["file_path"])
                if file_path.exists():
                    total_size += file_path.stat().st_size
            except Exception:
                pass
        
        return {
            "total_images": total_images,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "output_folder": str(self.output_folder.absolute())
        }
