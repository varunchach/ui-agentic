#!/bin/bash
# Script to run Streamlit app with correct virtual environment

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Verify sentence-transformers is available
python -c "from sentence_transformers import SentenceTransformer; print('✅ sentence-transformers available')" || {
    echo "❌ sentence-transformers not found. Installing..."
    pip install sentence-transformers
}

# Run Streamlit
echo "🚀 Starting Streamlit app..."
streamlit run streamlit_app.py
