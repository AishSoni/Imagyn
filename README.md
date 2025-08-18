# Imagyn - Open-Source Image Generation MCP Server

**Imagyn** is a Model Context Protocol (MCP) server that bridges LLMs with ComfyUI workflows, providing seamless text-to-image generation and iterative image editing capabilities.

## Features

- 🎨 **Text-to-Image Generation**: Generate images from natural language descriptions
- ✏️ **Image Editing**: Iteratively refine and edit generated images
- 🔧 **LoRA Support**: Discover and apply LoRA models for style customization
- 📚 **Generation History**: Track and revisit previous generations
- 🔌 **MCP Compatible**: Works with any MCP-compatible LLM client
- 🎯 **ComfyUI Integration**: Leverages powerful ComfyUI workflows

## Quick Start

### Prerequisites

- Python 3.8+
- ComfyUI instance running locally or remotely
- MCP-compatible client (Claude Desktop, etc.)

### Installation

```bash
pip install imagyn-mcp-server
```

### Configuration

Create a configuration file `config.json`:

```json
{
  "comfyui": {
    "host": "127.0.0.1",
    "port": 8188
  },
  "storage": {
    "images_dir": "./generated_images",
    "max_history": 100
  },
  "workflows": {
    "text_to_image": "workflows/flux_text_to_image.json",
    "image_to_image": "workflows/flux_image_to_image.json"
  }
}
```

### Running the Server

```bash
imagyn-server --config config.json
```

### MCP Client Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "imagyn": {
      "command": "imagyn-server",
      "args": ["--config", "config.json"]
    }
  }
}
```

## Available Tools

### `generate_image`
Generate images from text descriptions.

**Parameters:**
- `prompt` (required): Text description for image generation
- `loras` (optional): List of LoRA names to apply
- `style_preset` (optional): Predefined style configuration

### `edit_generated_image`
Edit and refine previously generated images.

**Parameters:**
- `image_id` (required): ID from previous generation
- `new_prompt` (required): New/modified prompt
- `loras` (optional): LoRAs for the edit
- `edit_strength` (optional): Denoising strength (0.1-1.0)

### `list_available_loras`
Discover available LoRA models for style customization.

### `get_generation_history`
Retrieve generation history and metadata.

**Parameters:**
- `limit` (optional): Number of recent generations to return
- `image_id` (optional): Get specific image details

## Development

### Setup Development Environment

```bash
git clone https://github.com/AishSoni/Imagyn.git
cd Imagyn
pip install -e ".[dev]"
pre-commit install
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src tests
isort src tests
```

## Architecture

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

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](https://github.com/AishSoni/Imagyn#readme)
- 🐛 [Issues](https://github.com/AishSoni/Imagyn/issues)
- 💬 [Discussions](https://github.com/AishSoni/Imagyn/discussions)
