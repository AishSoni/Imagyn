# Imagyn MCP Server

An open-source Model Context Protocol (MCP) server that bridges LLMs with ComfyUI workflows for seamless text-to-image generation and iterative image editing.

## 🚀 Features

- **Text-to-Image Generation**: Generate high-quality images from text prompts using ComfyUI workflows
- **Image Editing**: Refine and modify generated images with new prompts
- **LoRA Support**: Apply custom LoRA models for specialized styles and effects
- **Generation History**: Track and retrieve previous generations
- **Inline Image Display**: Generated images are shown directly in the chat interface
- **ComfyUI Integration**: Full compatibility with ComfyUI API and workflows
- **Storage Management**: Automatic image storage with metadata tracking

## 📋 Requirements

- Python 3.10+
- ComfyUI server running locally or remotely
- MCP-compatible client (Claude Desktop, custom implementations)

## 🛠️ Installation

1. **Clone the repository:**
```bash
git clone https://github.com/AishSoni/Imagyn.git
cd Imagyn
```

2. **Create and activate virtual environment:**
```bash
python -m venv imagyn_venv
# Windows
imagyn_venv\Scripts\activate
# Linux/Mac
source imagyn_venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -e .
```

## ⚙️ Configuration

Create or modify `config.json` in the project root:

```json
{
  "comfyui_url": "http://localhost:8188",
  "workflow_file": "workflows/txt2img_flux.json",
  "enable_loras": true,
  "lora_folder_path": "models/loras",
  "output_folder": "output",
  "max_concurrent_generations": 3,
  "default_generation_timeout": 300
}
```

### Configuration Options

- **comfyui_url**: URL of your ComfyUI server
- **workflow_file**: Path to the ComfyUI workflow JSON file
- **enable_loras**: Enable/disable LoRA model support
- **lora_folder_path**: Directory containing LoRA model files
- **output_folder**: Directory for storing generated images
- **max_concurrent_generations**: Maximum simultaneous generations
- **default_generation_timeout**: Timeout in seconds for generation

## 📁 Workflow Setup

Imagyn uses ComfyUI-compatible workflow JSON files. You can:

1. **Use provided workflows:**
   - `workflows/txt2img_flux.json` - Basic text-to-image with Flux
   - `workflows/txt2img_flux_lora.json` - Text-to-image with LoRA support

2. **Create custom workflows:**
   - Export workflow from ComfyUI interface
   - Save as JSON in the `workflows/` folder
   - Update `workflow_file` in config.json

### Workflow Requirements

Your workflow should include:
- Text input nodes for positive/negative prompts
- Configurable seed, width, height parameters
- SaveImage node for output
- LoRA loader nodes (if using LoRAs)

## 🎨 LoRA Models

If LoRAs are enabled:

1. Place `.safetensors` LoRA files in the configured `lora_folder_path`
2. LoRAs will be automatically discovered and listed
3. Apply LoRAs by name in generation requests

## 🚀 Usage

### Starting the Server

```bash
python src/imagyn/server.py
```

### MCP Tools Available

#### 1. `generate_image`
Generate images from text prompts.

**Parameters:**
- `prompt` (required): Text description for image generation
- `negative_prompt` (optional): Elements to avoid in the image
- `loras` (optional): List of LoRA names to apply
- `width` (optional): Image width in pixels (default: 1024)
- `height` (optional): Image height in pixels (default: 1024)
- `seed` (optional): Random seed for reproducible results

#### 2. `edit_generated_image`
Edit or refine previously generated images.

**Parameters:**
- `image_id` (required): ID of the image to edit
- `new_prompt` (required): New prompt for the edit
- `negative_prompt` (optional): Negative prompt for the edit
- `loras` (optional): LoRAs to apply
- `edit_strength` (optional): Denoising strength (0.1-1.0)

#### 3. `list_available_loras`
List all available LoRA models.

#### 4. `get_generation_history`
Get recent generation history or specific image details.

**Parameters:**
- `limit` (optional): Number of recent generations (default: 10)
- `image_id` (optional): Get details for specific image

#### 5. `get_server_status`
Get server status and configuration information.

### Example Conversations

**Generate an image:**
```
User: Generate an image of a sunset over mountains
Assistant: [Uses generate_image tool and displays the generated image inline]
```

**Edit an image:**
```
User: Make the sky more dramatic in image abc12345
Assistant: [Uses edit_generated_image tool with the specified ID]
```

**List LoRAs:**
```
User: What LoRA models are available?
Assistant: [Uses list_available_loras tool]
```

## 🔧 Troubleshooting

### Common Issues

1. **ComfyUI Connection Failed**
   - Ensure ComfyUI server is running
   - Check the `comfyui_url` in config.json
   - Verify network connectivity

2. **Workflow File Not Found**
   - Check that the workflow file exists at the specified path
   - Ensure the JSON format is valid

3. **LoRA Models Not Found**
   - Verify the `lora_folder_path` exists
   - Ensure LoRA files are in `.safetensors` format
   - Check that `enable_loras` is set to `true`

4. **Generation Timeout**
   - Increase `default_generation_timeout` in config
   - Check ComfyUI server performance
   - Verify workflow complexity

### Logs and Debugging

The server provides detailed logging. Check the console output for:
- Connection status
- Generation progress
- Error messages
- Configuration validation

## 📂 Project Structure

```
Imagyn/
├── config.json              # Server configuration
├── workflows/               # ComfyUI workflow files
│   ├── txt2img_flux.json
│   └── txt2img_flux_lora.json
├── src/imagyn/             # Source code
│   ├── __init__.py
│   ├── server.py           # Main entry point
│   ├── mcp.py             # MCP server implementation
│   ├── models.py          # Data models
│   ├── comfyui_client.py  # ComfyUI API client
│   └── storage.py         # Image storage management
├── output/                 # Generated images
├── models/loras/          # LoRA model files
└── pyproject.toml         # Project configuration
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- ComfyUI for the powerful workflow system
- MCP community for the protocol specifications
- Contributors and users of the Imagyn project - Open-Source Image Generation MCP Server

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
