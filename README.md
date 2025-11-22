# Finance Tracker

## Project Structure

- `backend/`: FastAPI backend application
- `frontend/`: React frontend application

## Getting Started

### Backend

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Run the server:
   ```bash
   cd backend
   ../venv/bin/uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`.
   API Documentation: `http://localhost:8000/docs`

### Frontend

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Run the development server:
   ```bash
   npm start
   ```
   The application will be available at `http://localhost:3000`.

## Features Implemented

- **Authentication**: Register, Login, Token Refresh (JWT)
- **Accounts**: Create, Read, Update, Delete Accounts
