# BFSI Document Intelligence Chatbot

An intelligent agentic RAG system for BFSI (Banking, Financial Services, and Insurance) document analysis with KPI extraction, document Q&A, and real-time data integration.

## Features

- **📊 KPI Extraction**: Automatically extract financial KPIs (Revenue, Profit, ROE, ROA, GNPA, NNPA, PCR, CRAR/CAR)
- **💬 Document Q&A**: Ask questions about uploaded documents with citations
- **🔧 External Tools**: Web search, stock prices, GDP data
- **🧠 Agentic Intelligence**: Smart routing between document RAG and external tools
- **⚡ Optimizations**: KV-caching and speculative decoding for improved performance

## Architecture

- **LangGraph**: Stateful agent orchestration for KPI and Chat flows
- **FAISS**: Vector store for document embeddings
- **Streamlit**: Modern web UI
- **LiteLLM**: LLM provider abstraction supporting OpenAI, Anthropic, Azure, and custom endpoints

## Quick Start

### Prerequisites

- Python 3.11+
- OpenShift/Kubernetes (for deployment)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/varunchach/Finance_doc_Analyzer_Agentic_demo.git
   cd Finance_doc_Analyzer_Agentic_demo
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file:
   ```bash
   # LLM Configuration (choose one)
   CUSTOM_LLM_ENDPOINT=https://your-litellm-endpoint.com/v1
   CUSTOM_LLM_MODEL=your-model-name
   CUSTOM_LLM_API_KEY=your-api-key
   
   # Embedding Model
   EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
   
   # Web Search
   TAVILY_API_KEY=your-tavily-key
   WEB_SEARCH_PROVIDER=tavily
   ```

5. **Run the application**
   ```bash
   streamlit run streamlit_app.py
   ```

## Deployment

### Docker Build

```bash
docker buildx build --platform linux/amd64 -t quay.io/your-org/bfsi-doc-intelligence:latest --push .
```

### OpenShift Deployment

1. **Create ConfigMap and Secret**
   ```bash
   oc apply -f configmap.yaml -n dsdemo1
   oc create secret generic bfsi-doc-intelligence-secrets \
     --from-literal=CUSTOM_LLM_ENDPOINT='your-endpoint' \
     --from-literal=CUSTOM_LLM_MODEL='your-model' \
     --from-literal=TAVILY_API_KEY='your-key' \
     -n dsdemo1
   ```

2. **Deploy application**
   ```bash
   oc apply -f deployment.yaml -n dsdemo1
   oc apply -f service.yaml -n dsdemo1
   oc apply -f route.yaml -n dsdemo1
   ```

## Usage

1. **Upload Document**: Upload a BFSI document (PDF, DOCX, TXT)
2. **Ingest**: Click "Ingest Document" to process and index
3. **Ask Questions**: Use the chat interface to query the document
4. **Generate KPI Report**: Click "Generate KPI Report" for automated analysis

## Tools

- **Web Search**: Real-time web search using Tavily
- **Finance Tool**: Stock prices and market data using yfinance
- **GDP Tool**: Economic indicators and GDP data

## Configuration

Key environment variables:
- `CUSTOM_LLM_ENDPOINT`: LiteLLM endpoint URL
- `CUSTOM_LLM_MODEL`: Model name
- `EMBEDDING_MODEL`: Embedding model (default: BAAI/bge-small-en-v1.5)
- `TAVILY_API_KEY`: Tavily API key for web search

## License

MIT
