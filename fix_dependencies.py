#!/usr/bin/env python3
"""
Quick fix script for Imagyn MCP Server dependency issues
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_python_version():
    """Check current Python version"""
    version = sys.version_info
    print(f"Current Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 10:
        print("SUCCESS: Python version is compatible with MCP library")
        return True
    else:
        print("ERROR: Python version is too old for MCP library (requires 3.10+)")
        return False


def remove_old_venv():
    """Remove existing virtual environment"""
    venv_path = Path("imagyn_venv")
    if venv_path.exists():
        print("Removing old virtual environment...")
        try:
            shutil.rmtree(venv_path)
            print("SUCCESS: Old virtual environment removed")
            return True
        except Exception as e:
            print(f"ERROR: Failed to remove old virtual environment: {e}")
            return False
    else:
        print("INFO: No existing virtual environment found")
        return True


def create_fresh_venv():
    """Create a fresh virtual environment"""
    print("Creating fresh virtual environment...")
    try:
        result = subprocess.run([sys.executable, "-m", "venv", "imagyn_venv"], 
                              check=True, capture_output=True, text=True)
        print("SUCCESS: Fresh virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to create virtual environment: {e}")
        print(f"Error output: {e.stderr}")
        return False


def install_dependencies():
    """Install dependencies with specific Python version"""
    print("Installing dependencies...")
    
    # Determine the correct paths
    if os.name == 'nt':  # Windows
        pip_path = Path("imagyn_venv") / "Scripts" / "pip"
        python_path = Path("imagyn_venv") / "Scripts" / "python"
    else:  # Linux/Mac
        pip_path = Path("imagyn_venv") / "bin" / "pip"
        python_path = Path("imagyn_venv") / "bin" / "python"
    
    try:
        # Upgrade pip first
        print("  Upgrading pip...")
        subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # Install the project
        print("  Installing Imagyn MCP Server...")
        subprocess.run([str(pip_path), "install", "-e", "."], 
                      check=True, capture_output=True)
        
        print("SUCCESS: Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        return False


def verify_installation():
    """Verify the installation works"""
    print("Verifying installation...")
    
    if os.name == 'nt':  # Windows
        python_path = Path("imagyn_venv") / "Scripts" / "python"
    else:  # Linux/Mac
        python_path = Path("imagyn_venv") / "bin" / "python"
    
    try:
        # Test import
        result = subprocess.run([
            str(python_path), "-c", 
            "import mcp; print(f'MCP version: {mcp.__version__}')"
        ], check=True, capture_output=True, text=True)
        
        print(f"SUCCESS: Installation verified: {result.stdout.strip()}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Installation verification failed: {e}")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Main fix function"""
    print("Imagyn MCP Server Dependency Fix")
    print("=" * 40)
    
    # Check Python version first
    if not check_python_version():
        print("\nERROR: Python version is incompatible!")
        print("\nSolutions:")
        print("1. Install Python 3.10 or higher from https://python.org")
        print("2. Use pyenv, conda, or other version manager to switch to Python 3.10+")
        print("3. Create a virtual environment with Python 3.10+:")
        print("   python3.10 -m venv imagyn_venv  # If you have python3.10 installed")
        return False
    
    print("\n" + "-" * 40)
    
    # Fix steps
    steps = [
        (remove_old_venv, "Removing old virtual environment"),
        (create_fresh_venv, "Creating fresh virtual environment"),
        (install_dependencies, "Installing dependencies"),
        (verify_installation, "Verifying installation")
    ]
    
    for step_func, step_name in steps:
        print(f"\nRunning: {step_name}...")
        if not step_func():
            print(f"\nERROR: Fix failed at step: {step_name}")
            return False
    
    print("\n" + "=" * 40)
    print("SUCCESS: Dependency issues fixed!")
    print("=" * 40)
    print("\nYou can now run:")
    print("   python test_setup.py")
    print("   python src/imagyn/server.py")
    
    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
