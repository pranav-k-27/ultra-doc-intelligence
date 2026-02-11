#!/bin/bash

# Start API in background
echo "Starting FastAPI backend on port $PORT..."
python app.py &
API_PID=$!

# Wait for API to start
echo "Waiting for API to be ready..."
sleep 15

# Check if API is running
if ! kill -0 $API_PID 2>/dev/null; then
    echo "❌ API failed to start!"
    exit 1
fi

# Try to ping API
for i in {1..10}; do
    if curl -f http://localhost:$PORT/ > /dev/null 2>&1; then
        echo "✅ API is ready!"
        break
    fi
    echo "Waiting for API... ($i/10)"
    sleep 2
done

# Start Streamlit UI (also on same port - Render only exposes one port)
echo "Starting Streamlit UI..."
streamlit run ui.py --server.port=$PORT --server.address=0.0.0.0