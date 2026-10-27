"""Launcher for Adham Agent Mobile Command Center Server."""
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.chdir(str(BASE_DIR))

import uvicorn
from server.app import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8080,
        reload=False,
        log_level="info",
        access_log=True
    )
