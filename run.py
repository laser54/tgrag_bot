#!/usr/bin/env python3
"""Development server runner with cloudflared tunnel."""

import os
import subprocess
import sys
import time
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


def start_cloudflared_tunnel():
    """Start cloudflared tunnel and return the HTTPS URL."""
    print("🚀 Starting cloudflared tunnel on port 8080...")

    cloudflared_path = current_dir / "bin" / "cloudflared.exe"

    if not cloudflared_path.exists():
        print(f"❌ cloudflared not found at {cloudflared_path}")
        print("💡 Please ensure cloudflared.exe is in the bin/ directory")
        sys.exit(1)

    # Start cloudflared in background
    try:
        process = subprocess.Popen(
            [str(cloudflared_path), "tunnel", "--url", "http://localhost:8080"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
    except FileNotFoundError:
        print(f"❌ cloudflared not found at {cloudflared_path}")
        sys.exit(1)

    # Wait for tunnel URL
    import re

    url_pattern = re.compile(r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com")
    tunnel_url = None
    timeout = 30  # 30 seconds timeout

    start_time = time.time()
    while time.time() - start_time < timeout:
        if process.poll() is not None:
            # Process exited
            output, _ = process.communicate()
            print(f"❌ cloudflared exited unexpectedly: {output}")
            sys.exit(1)

        # Read output line by line
        line = process.stdout.readline()
        if line:
            print(f"[cloudflared] {line.strip()}")
            match = url_pattern.search(line)
            if match:
                tunnel_url = match.group(0)
                break

        time.sleep(0.1)

    if not tunnel_url:
        print("❌ Failed to get tunnel URL from cloudflared within 30 seconds")
        process.terminate()
        sys.exit(1)

    print(f"✅ Tunnel established: {tunnel_url}")

    # Set environment variable for webhook URL
    webhook_url = f"{tunnel_url}/webhook/telegram"
    os.environ["WEBHOOK_URL"] = webhook_url
    print(f"📡 Webhook URL: {webhook_url}")

    return process, tunnel_url


def cleanup_cloudflared(process):
    """Clean up cloudflared process."""
    if process and process.poll() is None:
        print("🧹 Shutting down cloudflared tunnel...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    # Check if we're running in Docker
    import os

    if os.getenv("DOCKER_CONTAINER"):
        # In Docker, just run FastAPI server (cloudflared runs in separate container)
        print("🐳 Running in Docker mode - using polling mode")
        import uvicorn

        uvicorn.run(
            "apps.bot.main:app",
            host="0.0.0.0",  # Listen on all interfaces in Docker
            port=8080,
            reload=False,
            log_level="info",
        )
    else:
        # Local development with cloudflared
        cloudflared_process = None

        try:
            # Start cloudflared tunnel
            cloudflared_process, tunnel_url = start_cloudflared_tunnel()

            # Give the tunnel a moment to fully establish
            time.sleep(2)

            # Start FastAPI server
            print("🌐 Starting FastAPI server...")
            import uvicorn

            uvicorn.run(
                "apps.bot.main:app",
                host="127.0.0.1",
                port=8080,
                reload=False,  # Disable reload to avoid conflicts with cloudflared
                log_level="info",
            )

        except KeyboardInterrupt:
            print("\n🛑 Received interrupt signal")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            if cloudflared_process:
                cleanup_cloudflared(cloudflared_process)
