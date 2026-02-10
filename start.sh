#!/bin/bash

# Start API in background
python app.py &

# Wait for API to be ready
sleep 5

# Start Streamlit UI
streamlit run ui.py --server.port=$PORT --server.address=0.0.0.0