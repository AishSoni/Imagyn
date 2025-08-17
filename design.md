# Imagyn MCP Server Design Document

## Project Overview

**Imagyn** is a Model Context Protocol (MCP) server that bridges LLMs with ComfyUI workflows, providing seamless text-to-image generation and iterative image editing capabilities. It democratizes advanced image generation by giving any tool-capable LLM the same integrated image generation experience found in proprietary platforms like ChatGPT and Grok.

## Goals & Objectives

### Primary Goals
- Enable any MCP-compatible LLM to generate and edit images through natural conversation
- Provide plug-and-play image generation capabilities without model multimodal requirements
- Support iterative image refinement workflows similar to proprietary platforms
- Maintain full user control over models, workflows, and generation parameters

### Success Metrics
- Seamless integration with multiple MCP frontends (Claude Desktop, custom clients)
- Sub-30 second generation times for standard workflows
- Support for 10+ concurrent generation requests
- Zero-configuration setup for end users

## Technical Architecture

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   LLM Client    │◄──►│   Imagyn MCP     │◄──►│   ComfyUI       │
│  (Claude, etc.) │    │     Server       │    │   Workflows     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Image Storage   │
                       │   & Metadata     │
                       └──────────────────┘
```

### Core Architecture
- **MCP Server**: Python-based server implementing MCP protocol specifications
- **ComfyUI Integration**: REST API client for workflow execution and queue management
- **Image Management**: Storage system for generated images with metadata tracking
- **Workflow Engine**: Template-based system for text-to-image and image-to-image workflows

## Feature Specifications

### Core Features

#### 1. Text-to-Image Generation
**Tool Name**: `generate_image`

**Parameters**:
```json
{
  "prompt": "string (required) - Text description for image generation",
  "loras": "array (optional) - List of LoRA names to apply",
  "style_preset": "string (optional) - Predefined style configuration"
}
```

**Returns**:
```json
{
  "image_id": "string - Unique identifier for generated image",
  "image_url": "string - URL for image display",
  "image_base64": "string - Base64 encoded image data",
  "metadata": {
    "prompt": "string",
    "loras_used": ["array"],
    "generation_time": "float",
    "seed": "integer"
  }
}
```

#### 2. Image Editing/Refinement
**Tool Name**: `edit_generated_image`

**Parameters**:
```json
{
  "image_id": "string (required) - ID from previous generation",
  "new_prompt": "string (required) - New/modified prompt",
  "loras": "array (optional) - LoRAs for the edit",
  "edit_strength": "float (optional) - Denoising strength (0.1-1.0)"
}
```

#### 3. LoRA Discovery
**Tool Name**: `list_available_loras`

**Returns**:
```json
{
  "loras": [
    {
      "name": "portrait_enhance",
      "description": "Professional portrait enhancement",
      "tags": ["portrait", "professional", "enhancement"]
    }
  ]
}
```

#### 4. Generation History
**Tool Name**: `get_generation_history`

**Parameters**:
```json
{
  "limit": "integer (optional) - Number of recent generations to return",
  "image_id": "string (optional) - Get specific image details"
}
```

### Workflow Support

#### Text-to-Image Workflow (Flux Krea Dev)
- **Base Model**: Flux Krea Dev
- **Fixed Parameters**: Steps (20), CFG (3.5), Sampler (euler), Scheduler (simple)
- **Dynamic Parameters**: Prompt, LoRA