import uvicorn
import logging

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

if __name__ == "__main__":
    # Runs the FastAPI application locally on port 8000
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
