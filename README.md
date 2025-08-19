# Imagyn MCP Server

**Transform any tool-capable LLM into a powerful image generation platform**

Imagyn is a Model Context Protocol (MCP) server that seamlessly integrates image generation capabilities into any MCP-compatible chat interface. Give your AI conversations the same image generation and editing superpowers found in proprietary platforms like ChatGPT and Grok, but with full control over models, workflows, and infrastructure.

## ✨ Features

- 🎨 **Multi-Platform Support**: ComfyUI (local), Replicate, and Fal.ai integration
- 🔧 **Advanced Customization**: Full LoRA support for ComfyUI workflows
- 🗣️ **Conversational Interface**: Natural language image generation within chat
- 🔄 **Iterative Editing**: Refine and edit generated images through conversation
- 🎯 **Model Agnostic**: Works with any tool-capable LLM (Claude, GPT-4, local models)
- ⚡ **Plug & Play**: Drop into any MCP-compatible frontend

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- At least one of:
  - ComfyUI installation with Flux models
  - Replicate API key
  - Fal.ai API key

### Installation

**Option 1: Install from PyPI (when available)**
```bash
pip install imagyn-mcp-server
```

**Option 2: Install from source**
```bash
git clone https://github.com/AishSoni/Imagyn.git
cd Imagyn
pip install -e .
```

**Option 3: Development setup**
```bash
git clone https://github.com/AishSoni/Imagyn.git
cd Imagyn
python setup.py  # This will create a virtual environment and install dependencies

# Activate the virtual environment (Windows)
.\imagyn_venv\Scripts\activate

# Or on Linux/Mac
source imagyn_venv/bin/activate
```

### Configuration

Create a `config.json` file:

```json
{
  "providers": {
    "comfyui": {
      "enabled": true,
      "url": "http://localhost:8188",
      "workflows": {
        "text_to_image": "workflows/fluxkrea.json"
      },
      "loras_path": "/path/to/your/loras"
    },
    "replicate": {
      "enabled": true,
      "api_token": "your_replicate_token"
    },
    "fal": {
      "enabled": true,
      "api_key": "your_fal_api_key"
    }
  }
}
```

### Running the Server

For MCP protocol (recommended):
```bash
python stdio_mcp_server.py
```

Alternative FastAPI server:
```bash
python src/imagyn/fastmcp_server.py
```

## 🛠️ Supported Platforms

### ComfyUI
- **Text-to-Image**: Flux Krea Dev workflow support
- **LoRA Integration**: Dynamic LoRA loading and strength control
- **Custom Workflows**: Bring your own ComfyUI workflows
- **Local Control**: Full privacy and customization

### Replicate
- Access to latest models via cloud API
- No local hardware requirements
- Pay-per-use pricing

### Fal.ai
- Fast inference with optimized endpoints
- Competitive cloud pricing
- Real-time generation capabilities

## 💬 Usage Examples

Once connected to your MCP-compatible chat interface:

```
🧑 "Generate a cyberpunk detective in a neon-lit alley"

🤖 "I'll create that image for you using Flux..."
   [Image generated and displayed]
   Generated: img_001

🧑 "Make the lighting more dramatic and add rain"

🤖 "I'll enhance the image with more dramatic lighting and rain effects..."
   [Edited image displayed]  
   Generated: img_002 (edited from img_001)
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   LLM Client    │◄──►│ Imagyn MCP   │◄──►│   Image Gen     │
│  (Claude, etc.) │    │   Server     │    │   Providers     │
└─────────────────┘    └──────────────┘    └─────────────────┘
                              │                      │
                              ▼                      ▼
                       ┌──────────────┐    ┌─────────────────┐
                       │Image Storage │    │ ComfyUI/Cloud   │
                       │& Versioning  │    │    Services     │
                       └──────────────┘    └─────────────────┘
```

## 🔧 Configuration Options

### ComfyUI Provider
```json
{
  "comfyui": {
    "enabled": true,
    "url": "http://localhost:8188",
    "workflows": {
      "text_to_image": "workflows/fluxkrea.json"
    },
    "loras_path": "/path/to/loras",
    "default_loras": ["portrait_style", "cinematic_lighting"],
    "max_lora_strength": 1.0
  }
}
```

### Cloud Provider Settings
```json
{
  "replicate": {
    "enabled": true,
    "api_token": "your_token",
    "default_model": "black-forest-labs/flux-schnell"
  },
  "fal": {
    "enabled": true, 
    "api_key": "your_key",
    "default_model": "fal-ai/flux/schnell"
  }
}
```

## 📋 Available Tools

### `generate_image`
Generate images from text prompts
- **prompt** (string): Description of desired image
- **provider** (string, optional): Choose generation provider
- **loras** (array, optional): LoRA styles to apply (ComfyUI only)
- **lora_strengths** (array, optional): Strength values for LoRAs

### `edit_generated_image` 
Refine previously generated images
- **image_id** (string): ID of image to edit
- **prompt** (string): New prompt for editing
- **loras** (array, optional): LoRA adjustments

### `list_available_loras`
View available LoRA models (ComfyUI)

## 🗺️ Roadmap

- [ ] **Image-to-Image Workflows**: Direct img2img support with upload handling
- [ ] **Advanced Editing**: Inpainting, outpainting, and region-specific edits  
- [ ] **Workflow Templates**: Pre-built templates for common use cases
- [ ] **Batch Generation**: Generate multiple variations simultaneously
- [ ] **Style Presets**: Curated style combinations and presets
- [ ] **More Providers**: A1111, InvokeAI, and additional cloud services

## 🤝 Contributing

We welcome contributions! Please check the [Issues](https://github.com/AishSoni/Imagyn/issues) page for open tasks or submit new feature requests.

### Development Setup

```bash
git clone https://github.com/AishSoni/Imagyn.git
cd Imagyn
pip install -e ".[dev]"
```

## 📄 License

MIT License - see the repository for details.

## 🙋 Support

- 📖 [Documentation](https://github.com/AishSoni/Imagyn#readme)
- 🐛 [Issue Tracker](https://github.com/AishSoni/Imagyn/issues)