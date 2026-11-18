# 🛡️ MuLearn: Multi-Language Automated Mutation Testing Tool

MuLearn is an offline-first, lightweight mutation testing web application built for computer science education. It evaluates the strength of student unit test suites across **Python** and **C++** by injecting intentional logic and arithmetic faults (mutants) and tracking whether the student's tests catch them.

## Key Features
* **Multi-Language Support:** Automatically detects and executes test suites for Python (`.py`) and C++ (`.cpp` via `g++`).
* **Infinite Loop Guardrail:** Enforces a strict 2-second timeout limit on sandboxed executions to prevent system freezes.
* **Local SQLite Persistence:** Logs all mutation runs, execution durations, and final scores offline in `mulearn.db`.
* **Reactive Dashboard:** Built with ReactJS to provide instant file confirmation badges and live diagnostic summaries.

## How to Run Locally

### 1. Start the FastAPI Backend
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

### 2. Start the React Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173/` in your browser to run mutation analyses.
