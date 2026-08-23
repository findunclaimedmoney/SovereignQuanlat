#!/bin/bash
echo "========================================"
echo " Sovereign Quant Super Agent Dashboard"
echo "========================================"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed."
    exit 1
fi

echo "Installing / updating dependencies..."
python3 -m pip install -r requirements.txt --quiet

echo ""
echo "Starting dashboard..."
echo "Open your browser to: http://localhost:8501"
echo "Press Ctrl+C to stop."
echo ""

python3 -m streamlit run app.py --server.headless true
