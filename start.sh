#!/bin/bash

# Start API on internal port 8000
echo "Starting FastAPI backend..."
PORT=8000 python app.py &
API_PID=$!

# Wait for API
sleep 10

# Start Streamlit on Render's PORT
echo "Starting Streamlit UI..."
streamlit run ui.py --server.port=${PORT:-10000} --server.address=0.0.0.0