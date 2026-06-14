# Intelligent Candidate Discovery Platform

This is the project foundation for the Intelligent Candidate Discovery & Ranking Platform. It features a clean architecture with a backend services/ML layer and a Next.js 15 Tailwind dashboard frontend.

## Structure Overview

- `data/`: Local CSV/JSONL dataset directory (used when DB credentials are not supplied).
- `backend/`: FastAPI application containing endpoint routes, core settings, service layer orchestrations, ML model skeletons, and utility CLI scripts.
- `frontend/`: Next.js 15 Tailwind-styled dashboard for recruiters.

## Local Development Setup

### Backend Setup
1. Change directory to `backend/`
2. Create a virtual environment: `python -m venv venv`
3. Activate virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/macOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run application:
   ```bash
   # Option 1: Module execution
   python -m app.run
   
   # Option 2: Direct Uvicorn reload execution
   uvicorn app.main:app --reload
   ```

### Frontend Setup
1. Change directory to `frontend/`
2. Install dependencies: `npm install`
3. Run development server: `npm run dev`

### Docker Compose Setup
Run both backend and frontend together:
```bash
docker-compose up --build
```
