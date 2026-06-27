import os
import uvicorn
import logging

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

if __name__ == "__main__":
    # Disable hot-reload in production — reload=True spawns a file-watcher
    # master process that restarts the worker mid-startup, killing the
    # background initialization thread before workspace_state.ready becomes True.
    is_dev = os.environ.get("ENV", "development").lower() == "development"
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=is_dev,
    )
