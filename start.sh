#!/bin/bash

# Start API on internal port 8000 (background)
echo "Starting FastAPI backend on port 8000..."
python app.py &
API_PID=$!

# Wait for API to start
echo "Waiting for API to be ready..."
sleep 10

# Check if API is alive
if ! kill -0 $API_PID 2>/dev/null; then
    echo "❌ API failed to start!"
    exit 1
fi

# Verify API responds
echo "Testing API connection..."
for i in {1..15}; do
    if curl -f http://127.0.0.1:8000/ > /dev/null 2>&1; then
        echo "✅ API is ready!"
        break
    fi
    echo "Waiting... ($i/15)"
    sleep 1
done

# Start Streamlit on Render's exposed port
echo "Starting Streamlit UI on port $PORT..."
streamlit run ui.py --server.port=$PORT --server.address=0.0.0.0