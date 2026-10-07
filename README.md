# CyberSec AI Tutor

A local-first, privacy-preserving AI tutor for cybersecurity education. Built with Streamlit, Ollama, LangChain, LangGraph, and ChromaDB.

## Features

- **Local-First**: All LLM inference runs locally via Ollama - no data leaves your machine
- **RAG Pipeline**: Retrieval-Augmented Generation with ChromaDB vector store
- **Intent Classification**: Rule-based query routing for efficient retrieval
- **Conditional Retrieval**: LangGraph workflow skips vector search for simple queries
- **Incremental Ingestion**: Smart document updates with stale chunk cleanup
- **Conversation Memory**: Sliding window + summarization for context retention
- **Security**: Input sanitization, prompt injection detection, content policy
- **Multi-Mode**: Student, Company Knowledge, and Expert modes

## Quick Start

### Prerequisites

- Python 3.12+
- [Ollama](https://ollama.ai) installed and running

### Installation

```bash
# Clone repository
git clone <repository-url>
cd CyberSec-AI-Tutor

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Ollama
ollama serve

# Pull required models
ollama pull mistral
ollama pull nomic-embed-text
```

### Running the Application

```bash
# Run Streamlit app
streamlit run app.py
```

The app will be available at http://localhost:8501

### Using Docker

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

The app will be available at http://localhost:8501

## Configuration

Configuration is managed via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_CHAT_MODEL` | `mistral` | Chat model name |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model name |
| `VECTOR_DB` | `chroma` | Vector database backend |
| `CHROMA_PERSIST_DIRECTORY` | `./data/chroma` | ChromaDB persistence path |
| `DOCUMENTS_DIR` | `./data/documents` | Documents directory |
| `CHUNK_SIZE` | `800` | Document chunk size |
| `CHUNK_OVERLAP` | `120` | Chunk overlap (must be < chunk_size) |
| `RETRIEVAL_K` | `8` | Number of chunks to retrieve |
| `FINAL_CONTEXT_K` | `4` | Final chunks for context (≤ retrieval_k) |
| `TEMPERATURE` | `0.2` | LLM temperature |
| `STREAMING` | `true` | Enable streaming responses |

## Document Ingestion

Add your documents to the `data/documents/` directory (or configured `DOCUMENTS_DIR`):

```
data/documents/
├── company/
│   ├── services.pdf
│   └── policies.docx
├── cybersecurity/
│   ├── network_security/
│   │   └── tcp_ip.md
│   └── linux/
│       └── iptables_guide.txt
```

Supported formats: PDF, TXT, MD, DOCX, HTML

### Ingest Documents

```bash
# Ingest new/changed documents
python scripts/ingest.py

# Force re-ingest all documents
python scripts/ingest.py --force

# Custom documents directory
python scripts/ingest.py --directory ./my_docs
```

The ingestion script:
- Tracks file hashes for incremental updates
- Automatically deletes stale chunks when files change
- Categorizes documents by directory structure

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Streamlit  │────▶│  LangGraph  │────▶│    RAG      │
│     UI      │     │  Workflow   │     │  Pipeline   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  ChromaDB   │◀───▶│  Embeddings │
                    │ Vector Store│     │  (Ollama)   │
                    └─────────────┘     └─────────────┘
```

### LangGraph Workflow

```
START → input_validation → intent_detection → query_rewriting
                              ↓
                      retrieval_decision ──▶ retrieve (if needed)
                              ↓
                         generation → citations → END
                              ↓
                      error_handler (on failure)
```

### Key Components

- **app/graph/**: LangGraph workflow and nodes
- **app/rag/**: RAG pipeline (ingestion, chunking, retrieval, reranking)
- **app/llm/**: Ollama client and embedding management
- **app/memory/**: Conversation memory with summarization
- **app/security/**: Input sanitization and content policy
- **app/prompts/**: Prompt templates for different modes
- **config/settings.py**: Pydantic Settings configuration

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test module
pytest tests/test_rag.py -v
pytest tests/test_memory.py -v
pytest tests/test_security.py -v
pytest tests/test_prompts.py -v
```

## Project Structure

```
CyberSec-AI-Tutor/
├── app/
│   ├── core/           # Logging, exceptions
│   ├── graph/          # LangGraph workflow & nodes
│   ├── llm/            # Ollama client, embeddings
│   ├── memory/         # Conversation memory, summarization
│   ├── prompts/        # Prompt templates
│   ├── rag/            # RAG pipeline components
│   ├── security/       # Sanitization, policy
│   └── ui/             # Streamlit components
├── config/
│   └── settings.py     # Application settings
├── scripts/
│   ├── ingest.py       # Document ingestion
│   └── reset_vectorstore.py  # Reset vector store
├── tests/              # Unit tests
├── data/
│   ├── documents/      # Source documents
│   └── chroma/         # Vector store
├── app.py              # Main Streamlit app
├── Dockerfile          # Docker image
├── docker-compose.yml  # Multi-service deployment
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Modes

| Mode | Description |
|------|-------------|
| **Student** | University-level explanations with analogies and examples |
| **Company Knowledge** | Focus on internal documentation and services |
| **Expert** | Deep technical detail, assumes proficiency |

## Security

- Input validation and sanitization
- Prompt injection detection
- Content policy for sensitive topics
- Local-only processing (no cloud APIs required)

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Submit a pull request

## Troubleshooting

### Ollama Connection Issues

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

### Model Not Found

```bash
# Pull the required models
ollama pull mistral
ollama pull nomic-embed-text
```

### Vector Store Issues

```bash
# Reset vector store
python scripts/reset_vectorstore.py

# Re-ingest documents
python scripts/ingest.py --force
```

### Port Conflicts

Change ports in `docker-compose.yml`:
```yaml
ports:
  - "8502:8501"  # Use 8502 instead of 8501
```