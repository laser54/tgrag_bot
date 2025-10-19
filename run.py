#!/usr/bin/env python3
"""Development server runner."""

import subprocess
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


def run_docker_compose():
    """Run docker compose up."""
    print("🐳 Starting services with Docker Compose...")
    try:
        subprocess.run(
            ["docker", "compose", "up", "--build"],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker Compose failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Docker not found. Please install Docker and Docker Compose.")
        sys.exit(1)


if __name__ == "__main__":
    # Always run with Docker Compose
    run_docker_compose()
