# Dockerfile for BFSI Document Intelligence Application
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    curl \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt /app/

# Install Python dependencies
# Use --no-build-isolation for faster builds and install in one go
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . /app/

# Create vector_store, streamlit, and cache directories with proper permissions
# Copy Streamlit config to home directory to avoid permission issues
RUN mkdir -p /app/vector_store && \
    mkdir -p /home/appuser/.streamlit && \
    mkdir -p /home/appuser/.cache && \
    cp -r /app/.streamlit/* /home/appuser/.streamlit/ 2>/dev/null || true && \
    chown -R appuser:appuser /app/vector_store /home/appuser && \
    chmod -R 755 /home/appuser && \
    chmod -R 777 /home/appuser/.cache && \
    chmod -R 777 /app/vector_store

# Set Streamlit environment variables BEFORE switching user
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false \
    STREAMLIT_SERVER_FILE_WATCHER_TYPE=none \
    HOME=/home/appuser

# Switch to non-root user
USER appuser

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit with increased timeout for long operations
CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false", \
     "--server.fileWatcherType=none", \
     "--browser.gatherUsageStats=false"]

