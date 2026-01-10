"""Streamlit application entry point."""

import sys
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app.ui.main import main

if __name__ == "__main__":
    main()
