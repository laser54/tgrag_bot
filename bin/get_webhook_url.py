#!/usr/bin/env python3
"""Get webhook URL from cloudflared log file."""

import os
import re
import time


def get_cloudflared_url_from_log(log_file="/app/data/cloudflared.log", start_time=None):
    """Extract tunnel URL from cloudflared log file."""
    try:
        if not os.path.exists(log_file):
            return None

        with open(log_file, encoding="utf-8") as f:
            lines = f.readlines()

        # Process lines in reverse order (most recent first)
        for _i, line in enumerate(reversed(lines)):
            line = line.strip()
            if not line:
                continue

            # If start_time is provided, check if log entry is newer than start_time
            if start_time is not None:
                try:
                    import json

                    log_entry = json.loads(line)
                    timestamp_str = log_entry.get("time", "")
                    if timestamp_str:
                        # Parse ISO timestamp (e.g., "2025-10-19T14:22:29Z")
                        from datetime import datetime

                        log_time = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )
                        if log_time.timestamp() < start_time:
                            continue  # Skip old log entries
                except (json.JSONDecodeError, ValueError, KeyError):
                    pass  # If can't parse timestamp, process anyway

            # Try to parse as JSON first
            try:
                import json

                log_entry = json.loads(line)
                message = log_entry.get("message", "")
                if "trycloudflare.com" in message:
                    url_pattern = re.compile(
                        r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com"
                    )
                    match = url_pattern.search(message)
                    if match:
                        return match.group(0)
            except json.JSONDecodeError:
                # If not JSON, try direct regex match
                url_pattern = re.compile(r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com")
                match = url_pattern.search(line)
                if match:
                    return match.group(0)

        return None
    except Exception as e:
        print(f"❌ Error reading cloudflared log: {e}")
        return None


def wait_for_cloudflared(max_attempts=60):
    """Wait for cloudflared to start and extract URL."""
    print("⏳ Waiting for cloudflared tunnel URL...")

    # Remove old cached file to force fresh detection
    cache_file = "/app/data/webhook_url.txt"
    if os.path.exists(cache_file):
        try:
            os.remove(cache_file)
        except Exception:
            pass  # Ignore errors when removing cache file

    # Record start time to only look for URLs after this point
    start_time = time.time()

    # Always try to extract fresh URL from log file
    for _attempt in range(max_attempts):
        tunnel_url = get_cloudflared_url_from_log(
            "/app/data/cloudflared.log", start_time
        )
        if tunnel_url:
            webhook_url = f"{tunnel_url}/webhook/telegram"
            os.environ["WEBHOOK_URL"] = webhook_url
            # Also write to file for persistence
            try:
                with open(cache_file, "w") as f:
                    f.write(webhook_url)
            except Exception:
                pass  # Ignore errors when caching URL
            print(f"✅ Webhook: {webhook_url}")
            return True

        # Keep quiet while waiting, avoid noisy progress logs
        time.sleep(1)

    print("❌ Failed to detect webhook URL from cloudflared logs")
    print("⚠️  Bot will run without webhook functionality")
    print("💡 Check cloudflared logs: docker compose logs cloudflared")
    return True  # Don't fail, just warn


if __name__ == "__main__":
    wait_for_cloudflared()
