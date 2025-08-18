#!/usr/bin/env python3
"""
Setup script for Imagyn MCP Server
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description=""):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"SUCCESS: {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"SUCCESS: Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"ERROR: Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("   Imagyn requires Python 3.10 or higher (due to MCP library requirements)")
        return False


def setup_virtual_environment():
    """Create and setup virtual environment"""
    venv_path = Path("imagyn_venv")
    
    if venv_path.exists():
        print("INFO: Virtual environment already exists")
        return True
    
    print("Creating virtual environment...")
    if not run_command("python -m venv imagyn_venv", "Creating virtual environment"):
        return False
    
    return True


def install_dependencies():
    """Install project dependencies"""
    print("Installing dependencies...")
    
    # Determine the correct pip path
    if os.name == 'nt':  # Windows
        pip_path = "imagyn_venv\\Scripts\\pip"
        python_path = "imagyn_venv\\Scripts\\python"
    else:  # Linux/Mac
        pip_path = "imagyn_venv/bin/pip"
        python_path = "imagyn_venv/bin/python"
    
    # Upgrade pip first
    if not run_command(f"{python_path} -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install project in development mode
    if not run_command(f"{pip_path} install -e .", "Installing Imagyn MCP Server"):
        return False
    
    return True


def create_output_directories():
    """Create necessary output directories"""
    print("Creating output directories...")
    
    directories = [
        "output",
        "output/images",
        "models",
        "models/loras"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   Created: {directory}")
    
    print("SUCCESS: Output directories created")
    return True


def validate_config():
    """Validate configuration file"""
    print("Validating configuration...")
    
    config_path = Path("config.json")
    if not config_path.exists():
        print("INFO: config.json not found, using default configuration")
        return True
    
    try:
        import json
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        required_keys = [
            "comfyui_url", "workflow_file", "enable_loras", 
            "lora_folder_path", "output_folder"
        ]
        
        for key in required_keys:
            if key not in config:
                print(f"WARNING: Missing configuration key: {key}")
                return False
        
        print("SUCCESS: Configuration is valid")
        return True
    
    except Exception as e:
        print(f"ERROR: Configuration validation failed: {e}")
        return False


def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "=" * 50)
    print("Imagyn MCP Server setup completed!")
    print("=" * 50)
    print("\nNext Steps:")
    print("1. Start ComfyUI server:")
    print("   cd /path/to/ComfyUI")
    print("   python main.py")
    print()
    print("2. (Optional) Configure Imagyn:")
    print("   Edit config.json to match your setup")
    print()
    print("3. Test the installation:")
    print("   python test_setup.py")
    print()
    print("4. Start the MCP server:")
    if os.name == 'nt':  # Windows
        print("   imagyn_venv\\Scripts\\python src\\imagyn\\server.py")
    else:  # Linux/Mac
        print("   imagyn_venv/bin/python src/imagyn/server.py")
    print()
    print("5. Configure your MCP client:")
    print("   See claude_desktop_config.json for Claude Desktop")
    print()
    print("Documentation: README.md")
    print("Issues: https://github.com/AishSoni/Imagyn/issues")


def main():
    """Main setup function"""
    print("Imagyn MCP Server Setup")
    print("=" * 30)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    # Setup steps
    steps = [
        (setup_virtual_environment, "Setting up virtual environment"),
        (install_dependencies, "Installing dependencies"),
        (create_output_directories, "Creating directories"),
        (validate_config, "Validating configuration")
    ]
    
    failed_steps = []
    for step_func, step_name in steps:
        print(f"\n{'-' * 30}")
        if not step_func():
            failed_steps.append(step_name)
    
    print(f"\n{'-' * 30}")
    
    if failed_steps:
        print(f"ERROR: Setup failed. The following steps had errors:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\nPlease fix the errors and run setup again.")
        sys.exit(1)
    else:
        print_next_steps()


if __name__ == "__main__":
    main()
