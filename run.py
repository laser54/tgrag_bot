#!/usr/bin/env python3
"""Development server runner."""

import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "apps.bot.main:app", host="127.0.0.1", port=8080, reload=True, log_level="info"
    )
