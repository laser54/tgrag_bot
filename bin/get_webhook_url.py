#!/usr/bin/env python3
"""Get webhook URL from Pinggy SSH tunnel log file."""

import os
import re
import time

# Pinggy tunnel URLs look like:
#   https://abcdef-12-34-56-78.free.pinggy.link  (free tier)
#   https://abcdef-12-34-56-78.a.free.pinggy.link  (free tier, newer format)
#   https://abcdef.a.pinggy.online  (with token)
# IMPORTANT: Explicitly exclude dashboard.pinggy.io — Pinggy spams its log with
# "Upgrade at https://dashboard.pinggy.io" ads, and a broad regex will pick that
# up as the "tunnel URL", causing the bot to register a bogus webhook.
PINGGY_URL_PATTERN = re.compile(
    r"https://[a-zA-Z0-9][a-zA-Z0-9.-]*\."
    r"(?:pinggy\.link|pinggy\.online|pinggy-free\.link)\b"
)


def get_pinggy_url_from_log(log_file="/app/data/pinggy.log"):
    """Extract tunnel URL from Pinggy log file."""
    try:
        if not os.path.exists(log_file):
            return None

        with open(log_file, encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Find all URLs and return the last one (most recent)
        matches = PINGGY_URL_PATTERN.findall(content)
        if matches:
            return matches[-1]

        return None
    except Exception as e:
        print(f"❌ Error reading Pinggy log: {e}")
        return None


def wait_for_pinggy(max_attempts=60):
    """Wait for Pinggy tunnel to start and extract URL."""
    print("⏳ Waiting for Pinggy tunnel URL...")

    # Remove old cached file to force fresh detection
    cache_file = "/app/data/webhook_url.txt"
    if os.path.exists(cache_file):
        try:
            os.remove(cache_file)
        except Exception:
            pass

    for _attempt in range(max_attempts):
        tunnel_url = get_pinggy_url_from_log()
        if tunnel_url:
            webhook_url = f"{tunnel_url}/webhook/telegram"
            os.environ["WEBHOOK_URL"] = webhook_url
            # Also write to file for persistence
            try:
                with open(cache_file, "w") as f:
                    f.write(webhook_url)
            except Exception:
                pass
            print(f"✅ Webhook: {webhook_url}")
            return True

        time.sleep(1)

    print("❌ Failed to detect webhook URL from Pinggy logs")
    print("⚠️  Bot will run without webhook functionality")
    print("💡 Check Pinggy logs: docker compose logs pinggy")
    return True  # Don't fail, just warn


if __name__ == "__main__":
    wait_for_pinggy()
