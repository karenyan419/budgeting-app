#!/bin/bash
# Run both backend and frontend dev servers

trap 'kill 0' EXIT

echo "Starting backend on http://localhost:8000..."
cd backend && source venv/bin/activate && uvicorn main:app --reload &

echo "Starting frontend on http://localhost:5173..."
cd frontend && npm run dev &

wait
