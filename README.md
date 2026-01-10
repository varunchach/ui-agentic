# Agentic BFSI Document Intelligence Chatbot

A production-grade, agentic document intelligence chatbot specifically designed for BFSI (Banking, Financial Services, and Insurance) documents. The application provides two distinct agentic flows: KPI Report Generation and Document Chat with agentic RAG capabilities.

## Features

- **Document Ingestion**: Supports PDFs, text files, and tables with section-aware chunking
- **KPI Report Generation**: Automated extraction of BFSI KPIs (Revenue, Net Profit, ROE, ROA, GNPA, NNPA, PCR, CRAR/CAR) with structured report generation
- **Document Chat**: Grounded Q&A with strict citation requirements and conversation memory
- **Agentic RAG**: Intelligent routing between document RAG and external tools (web search, finance, GDP)
- **Vector Storage**: FAISS-based vector database with BGE embeddings
- **Re-ranking**: BGE Large re-ranker for improved retrieval quality
- **LLM Optimizations**: KV-caching and speculative decoding support
- **Streamlit UI**: Modern, intuitive interface for document upload and interaction

## Quick Start

### Step 1: Setup Environment

```bash
# Navigate to project directory
cd /Users/varunraste/Downloads/UI_Agentic

# Activate virtual environment
source venv/bin/activate

# Install dependencies (if not already installed)
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your API keys
```

**Required Configuration:**
```bash
# LiteLLM Configuration (or use OpenAI/Anthropic)
CUSTOM_LLM_ENDPOINT=https://your-litellm-endpoint.com/v1
CUSTOM_LLM_API_KEY=your_api_key_here
CUSTOM_LLM_MODEL=your-model-name
CUSTOM_LLM_TEMPERATURE=0.0
```

**Optional Tools Configuration:**
```bash
# Web Search (Tavily recommended for RAG)
WEB_SEARCH_PROVIDER=tavily
TAVILY_API_KEY=your_tavily_api_key_here

# OR use DuckDuckGo (free, no key needed)
# WEB_SEARCH_PROVIDER=duckduckgo

# Economic Data (optional)
# FRED_API_KEY=your_fred_api_key_here
```

### Step 3: Run Application

```bash
# Using helper script
./run_app.sh

# OR directly
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

### Step 4: Upload and Process Document

1. Upload a BFSI document (PDF, TXT, or DOCX) in the sidebar
2. Click **"📥 Ingest Document"** and wait for processing
3. Choose your workflow:
   - **📊 Generate KPI Report**: Extract and analyze financial KPIs
   - **💬 Chat with Document**: Ask questions with agentic RAG capabilities

## Configuration

### LLM Providers

The application supports multiple LLM providers:

#### LiteLLM (Recommended)
```bash
CUSTOM_LLM_ENDPOINT=https://your-endpoint.com/v1
CUSTOM_LLM_API_KEY=your_key
CUSTOM_LLM_MODEL=your-model-name
CUSTOM_LLM_TEMPERATURE=0.0
```

#### OpenAI
```bash
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4
```

#### Anthropic
```bash
ANTHROPIC_API_KEY=your_key
ANTHROPIC_MODEL=claude-3-opus-20240229
```

### Embedding Model

Default: `BAAI/bge-small-en-v1.5` (fast, 384 dimensions)

To change:
```bash
EMBEDDING_MODEL=your-model-name
EMBEDDING_DIMENSION=384
```

### Tools Configuration

#### Web Search
- **Tavily** (Recommended): Optimized for RAG, requires API key from https://tavily.com/
- **DuckDuckGo**: Free, no API key required
- **SerpAPI**: Optional, requires key from https://serpapi.com/

```bash
WEB_SEARCH_PROVIDER=tavily
TAVILY_API_KEY=your_key
```

#### Finance Tool
- Uses `yfinance` library (free, no API key)
- Supports US stocks (AAPL, MSFT) and Indian stocks (HDFCBANK.NS, RELIANCE.NS)

#### GDP Tool
- **World Bank API**: Default, free, no API key
- **FRED API**: Optional, more detailed data, requires key from https://fred.stlouisfed.org/

```bash
FRED_API_KEY=your_key  # Optional
```

### LLM Optimizations

KV-caching and speculative decoding are **enabled by default** for optimal performance:

```bash
# All enabled by default - no configuration needed
LLM_OPTIMIZATION_ENABLED=true  # Default: true
KV_CACHE_ENABLED=true          # Default: true
SPECULATIVE_DECODING_ENABLED=true  # Default: true
SPECULATIVE_MODEL=your-draft-model  # Optional: specify draft model for speculative decoding
```

**Performance Benefits:**
- **KV-Caching**: 20-40% faster for multi-turn conversations
- **Speculative Decoding**: 2-3x faster token generation (requires draft model)
- **Response Time Display**: UI shows execution time for each query

## Architecture

```
app/
├── config/          # Configuration management
│   ├── settings.py # Main configuration
│   ├── kpi_schema.py # KPI definitions
│   └── utils.py    # Config utilities
├── agents/         # Agent implementations
│   ├── orchestrator.py # Main orchestrator
│   ├── router_agent.py # Agentic RAG router
│   ├── kpi/        # KPI report flow agents
│   └── chat/       # Chat flow agents
├── ingestion/      # Document processing pipeline
│   ├── document_loader.py
│   ├── chunker.py
│   ├── embedder.py
│   ├── vector_store.py
│   └── pipeline.py
├── tools/          # External tools
│   ├── web_search.py
│   ├── finance_tool.py
│   ├── gdp_tool.py
│   └── tool_registry.py
├── ui/             # Streamlit UI components
│   ├── main.py
│   ├── chat_view.py
│   └── kpi_report_view.py
└── utils/          # Shared utilities
    ├── reranker.py
    ├── memory.py
    ├── export.py
    └── llm_optimizations.py
```

## Agentic Flows (LangGraph)

The application uses **LangGraph** for state machine-based agent orchestration, providing better observability, error handling, and workflow management.

### KPI Report Generation (LangGraph Workflow)

```
START → retrieval → financial_analysis → report_generation → END
```

**Graph Nodes:**
1. **retrieval**: Retrieves relevant chunks for KPI extraction
2. **financial_analysis**: Extracts structured KPIs from chunks
3. **report_generation**: Generates comprehensive markdown report
4. **error_handler**: Handles errors at any stage

**Extracted KPIs:**
- Financial Metrics: Revenue, Net Profit, ROE, ROA
- Asset Quality: GNPA, NNPA, PCR
- Capital Adequacy: CRAR/CAR
- Growth Metrics: QoQ/YoY growth rates

### Document Chat with Agentic RAG (LangGraph Workflow)

```
START → router → [rag | tool | both] → combine_results → END

RAG Path: router → query_understanding → retrieval_rerank → qa → combine
Tool Path: router → tool_execution → combine
Both Path: router → query_understanding → retrieval_rerank → qa → tool_execution → combine
```

**Graph Nodes:**
1. **router**: Intelligently routes to RAG, tools, or both
2. **query_understanding**: Refines query for better retrieval
3. **retrieval_rerank**: Retrieves and re-ranks relevant chunks
4. **qa**: Generates grounded answer with citations
5. **tool_execution**: Executes external tools (web search, finance, GDP)
6. **combine_results**: Merges RAG and tool outputs
7. **error_handler**: Handles errors gracefully

**Router Intelligence:**
- Uses RAG when query is about the uploaded document
- Uses tools for real-time data (stock prices, web search, GDP)
- Combines both when query needs document context + real-time data

**Example Queries:**
- **RAG**: "What is the revenue in the document?"
- **Tools**: "What is the current price of AAPL?"
- **Both**: "Compare document revenue with current market trends"

## Usage Examples

### KPI Report Flow

1. Upload a BFSI document (e.g., quarterly report)
2. Click **"📊 Generate KPI Report"**
3. Wait for processing (1-2 minutes)
4. View structured report with:
   - Executive Summary
   - Key Financial Highlights
   - Risk & Asset Quality
   - Capital Adequacy
   - Trends & Red Flags
5. Download as Markdown or PDF

### Chat Flow

1. Click **"💬 Chat with Document"**
2. Ask questions:
   - **Document queries**: "What is the GNPA ratio?"
   - **Real-time data**: "What is the current price of HDFCBANK.NS?"
   - **Web search**: "Search for latest RBI regulations"
   - **Combined**: "Compare document CRAR with industry average"
3. View answers with citations and tool usage indicators
4. Continue conversation (memory is maintained)

## Technology Stack

- **Framework**: LangChain + LangGraph (for agent orchestration)
- **UI**: Streamlit
- **Embeddings**: BGE (BAAI/bge-small-en-v1.5)
- **Vector DB**: FAISS
- **Re-ranker**: BGE Large (FlagEmbedding)
- **Document Processing**: Docling, PyPDF, python-docx
- **Tools**: Tavily, DuckDuckGo, yfinance, World Bank API, FRED API
- **Agent Orchestration**: LangGraph (state machine workflows)

## Development

### Project Structure

- `streamlit_app.py`: Main entry point
- `app/config/`: Configuration and KPI schema definitions
- `app/ingestion/`: Document loading, chunking, embedding, and vector storage
- `app/agents/`: Agent implementations
  - `app/agents/graphs/`: LangGraph workflows (KPI and Chat graphs)
  - `app/agents/kpi/`: KPI extraction agents
  - `app/agents/chat/`: Chat flow agents
  - `app/agents/orchestrator.py`: Main orchestrator using LangGraph
- `app/tools/`: External tool integrations
- `app/ui/`: Streamlit UI components
- `app/utils/`: Shared utilities (re-ranker, memory, export, optimizations)

### Adding New KPIs

Edit `app/config/kpi_schema.py` to add new KPI definitions and extraction patterns.

### Adding New Tools

1. Create tool class in `app/tools/`
2. Register in `app/tools/tool_registry.py`
3. Update router agent to recognize tool usage scenarios

## Troubleshooting

### Slow Performance?
- First run downloads models (one-time, 5-10 minutes)
- Use faster embedding model: `BAAI/bge-small-en-v1.5` (default)
- KPI report generation takes 1-2 minutes (2 LLM calls)
- Enable KV-caching for faster chat responses

### Import Errors?
- Make sure venv is activated: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### Model Download Issues?
- Check internet connection
- Optional: Add `HUGGINGFACE_API_TOKEN` to `.env` for better rate limits

### Tool Not Working?
- Verify API keys in `.env` file
- Check tool provider status
- Use DuckDuckGo (free) if Tavily key is missing

## Expected Timings

- **First Run (Model Downloads)**: 5-10 minutes
- **Document Ingestion**: 1-3 minutes
- **KPI Report Generation**: 1-2 minutes
- **Chat Response**: 10-30 seconds per query

## What Gets Saved?

**During Session (in memory):**
- ✅ Document vector store
- ✅ Agent orchestrator
- ✅ KPI reports
- ✅ Chat history
- ✅ Extracted KPI data

**On Disk:**
- ✅ Vector store index (in `vector_store/` folder)
- ✅ Document chunks and embeddings

**Note:** Context persists during the Streamlit session. If you refresh the page, you'll need to re-upload the document.

## License

[Specify your license]

## Contributing

[Contributing guidelines]
