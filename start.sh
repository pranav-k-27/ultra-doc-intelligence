#!/bin/bash

# Start API in background with output
echo "Starting FastAPI backend..."
python app.py > api.log 2>&1 &
API_PID=$!

# Wait and check if API is alive
sleep 10

# Check if API process is still running
if ! kill -0 $API_PID 2>/dev/null; then
    echo "ERROR: API failed to start!"
    cat api.log
    exit 1
fi

# Wait for API to respond
echo "Waiting for API to be ready..."
for i in {1..30}; do
    if curl -f http://localhost:8000/ > /dev/null 2>&1; then
        echo "API is ready!"
        break
    fi
    echo "Attempt $i/30: API not ready yet..."
    sleep 2
done

# Start Streamlit
echo "Starting Streamlit UI..."
streamlit run ui.py --server.port=$PORT --server.address=0.0.0.0