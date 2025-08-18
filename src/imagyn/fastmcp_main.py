"""
Imagyn FastMCP Server - Main entry point using modern FastMCP
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from imagyn.fastmcp_server import ImagynFastMCPServer


def main():
    """Main entry point for the Imagyn FastMCP server"""
    
    # Get config path from environment or use default
    config_path = os.getenv("IMAGYN_CONFIG", "config.json")
    
    try:
        server = ImagynFastMCPServer(config_path=config_path)
        server.run()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure config.json exists in the project root directory.")
        sys.exit(1)
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
