# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RAG-Anything is an All-in-One Multimodal RAG (Retrieval-Augmented Generation) Framework built on top of LightRAG. It processes multimodal documents (PDFs, Office files, images, text) containing text, images, tables, equations, and other content types, then indexes them in a knowledge graph for intelligent retrieval.

**Core Technologies:**
- Built on [LightRAG](https://github.com/HKUDS/LightRAG) for graph-based RAG
- Uses MinerU or Docling parsers for document extraction
- Processes multimodal content with specialized processors
- Async-first architecture with Python 3.10+ and dataclasses

## Key Architecture Concepts

### 1. Mixin-Based Design Pattern

The `RAGAnything` class uses a mixin architecture where functionality is split across specialized mixins:

```python
@dataclass
class RAGAnything(QueryMixin, ProcessorMixin, BatchMixin):
    """Main class combining all functionality"""
```

**Mixins:**
- `QueryMixin` (raganything/query.py) - All query methods (text, multimodal, VLM-enhanced)
- `ProcessorMixin` (raganything/processor.py) - Document parsing and content insertion
- `BatchMixin` (raganything/batch.py) - Batch processing for multiple documents

**When modifying functionality:**
- Query-related changes go in `query.py`
- Document processing changes go in `processor.py`
- Batch operations go in `batch.py`
- Core initialization stays in `raganything.py`

### 2. Two-Stage Processing Pipeline

**Stage 1: Document Parsing**
```
Document → Parser (MinerU/Docling) → Content List
```
- Parsers extract structured content from documents
- Output is a normalized content list with type annotations
- Cached results stored in LightRAG KV storage

**Stage 2: Multimodal Content Processing**
```
Content List → Separate text/multimodal → Modal Processors → LightRAG
```
- Text content inserted directly into LightRAG
- Multimodal content (images, tables, equations) processed by specialized processors
- Each processor creates entities and relationships in the knowledge graph

### 3. Modal Processor System

Located in `raganything/modalprocessors.py`, processors handle specific content types:

- `ImageModalProcessor` - Vision model analysis of images
- `TableModalProcessor` - Structured table interpretation
- `EquationModalProcessor` - LaTeX equation parsing
- `GenericModalProcessor` - Base class for custom processors

**Processor Workflow:**
1. Receive multimodal content with context
2. Generate enhanced descriptions using LLM/vision models
3. Extract entities and create knowledge graph nodes
4. Link to parent document and surrounding content

### 4. Context-Aware Processing

`ContextExtractor` (in modalprocessors.py) provides surrounding content to processors:
- Extracts text from neighboring pages/chunks
- Includes headers, captions, footnotes
- Configurable window size and content filters
- Helps processors understand multimodal content in document context

### 5. Three Query Modes

1. **Pure Text Query** (`aquery()`): Standard LightRAG search
2. **VLM-Enhanced Query** (`aquery(vlm_enhanced=True)`): Automatically analyzes images in retrieved context
3. **Multimodal Query** (`aquery_with_multimodal()`): Queries with specific multimodal content

## Common Development Commands

### Setup and Installation

```bash
# Install with uv (recommended)
uv sync                              # Install base dependencies
uv sync --all-extras                 # Install all optional dependencies
UV_HTTP_TIMEOUT=120 uv sync          # If network timeouts occur

# Install with pip
pip install -e .                     # Editable install
pip install -e '.[all]'              # With all optional dependencies

# Verify MinerU installation
mineru --version
python -c "from raganything import RAGAnything; rag = RAGAnything(); print('✅ OK' if rag.check_parser_installation() else '❌ Issue')"
```

### Running Tests and Examples

```bash
# Run main example with a document
python examples/raganything_example.py path/to/document.pdf --api-key YOUR_KEY --parser mineru

# Test parsers (no API key needed)
python examples/office_document_test.py --file document.docx
python examples/image_format_test.py --file image.bmp
python examples/text_format_test.py --file document.md

# Check dependencies
python examples/office_document_test.py --check-libreoffice --file dummy
python examples/image_format_test.py --check-pillow --file dummy

# Modal processors example
python examples/modalprocessors_example.py --api-key YOUR_KEY

# Batch processing
python examples/batch_processing_example.py --folder ./documents --output ./output
```

### Running with uv

```bash
# Use uv run to execute in the virtual environment
uv run python examples/raganything_example.py --help
uv run python -m pytest tests/
```

## Code Structure and File Organization

```
raganything/
├── __init__.py              # Package exports (RAGAnything, RAGAnythingConfig)
├── raganything.py           # Main RAGAnything class with __post_init__
├── config.py                # RAGAnythingConfig dataclass with env var support
├── query.py                 # QueryMixin - all query methods
├── processor.py             # ProcessorMixin - document processing
├── batch.py                 # BatchMixin - batch operations
├── modalprocessors.py       # Modal processors and ContextExtractor
├── parser.py                # MineruParser and DoclingParser classes
├── batch_parser.py          # BatchParser for parallel processing
├── prompt.py                # PROMPTS dictionary with all templates
├── utils.py                 # Utility functions
├── enhanced_markdown.py     # Enhanced markdown conversion
└── base.py                  # Base classes and enums

examples/                    # Usage examples and tests
docs/                        # Additional documentation
```

## Important Implementation Details

### 1. Async/Await Pattern

All core methods are async with sync wrappers:

```python
async def aquery(self, query: str, mode: str = "hybrid", **kwargs):
    """Async query method"""
    # Implementation

def query(self, query: str, mode: str = "hybrid", **kwargs):
    """Sync wrapper"""
    loop = always_get_an_event_loop()
    return loop.run_until_complete(self.aquery(query, mode, **kwargs))
```

**Always implement async version first, then add sync wrapper.**

### 2. Configuration Management

Configuration uses dataclasses with environment variable fallbacks:

```python
@dataclass
class RAGAnythingConfig:
    working_dir: str = field(default=get_env_value("WORKING_DIR", "./rag_storage", str))
    parse_method: str = field(default=get_env_value("PARSE_METHOD", "auto", str))
```

**New config options should:**
- Use `get_env_value()` from lightrag.utils
- Have sensible defaults
- Be documented in env.example

### 3. Parser Selection

Two parsers available with different strengths:
- **MinerU**: Better for PDFs, images, OCR, GPU acceleration
- **Docling**: Better for Office documents, HTML

**Parser instantiation pattern:**
```python
if self.config.parser.lower() == "docling":
    parser = DoclingParser()
else:
    parser = MineruParser()
```

### 4. Cache Key Generation

Parse results and queries are cached using MD5 hashes:
- Parse cache: file path + mtime + config parameters
- Query cache: query + mode + multimodal content

**Cache stored in LightRAG KV storage** at namespace "parse_cache" and "multimodal_query_cache"

### 5. Content List Format

The standard format for processed content (output from parsers):

```python
[
    {"type": "text", "text": "content", "page_idx": 0},
    {"type": "image", "img_path": "/path/to/img.jpg", "image_caption": [...], "page_idx": 1},
    {"type": "table", "table_body": "markdown table", "table_caption": [...], "page_idx": 2},
    {"type": "equation", "latex": "formula", "text": "description", "page_idx": 3}
]
```

**Key points:**
- `page_idx` indicates page number (0-based)
- `img_path` must be absolute path
- All content preserves original document order

## Environment Variables

Key environment variables (see env.example for full list):

**Parser Configuration:**
- `PARSER` - Parser selection: "mineru" or "docling" (default: mineru)
- `PARSE_METHOD` - Parse method: "auto", "ocr", "txt" (default: auto)
- `OUTPUT_DIR` - Output directory for parsed documents (default: ./output)

**Multimodal Processing:**
- `ENABLE_IMAGE_PROCESSING` - Enable image processing (default: true)
- `ENABLE_TABLE_PROCESSING` - Enable table processing (default: true)
- `ENABLE_EQUATION_PROCESSING` - Enable equation processing (default: true)

**Context Extraction:**
- `CONTEXT_WINDOW` - Pages/chunks before and after (default: 1)
- `CONTEXT_MODE` - "page" or "chunk" (default: page)
- `MAX_CONTEXT_TOKENS` - Maximum context tokens (default: 2000)

**Batch Processing:**
- `MAX_CONCURRENT_FILES` - Concurrent file processing (default: 1)
- `RECURSIVE_FOLDER_PROCESSING` - Recursive folder scan (default: true)

## External Dependencies

**Required external tools:**
- **LibreOffice** - For Office document conversion (.doc, .docx, .ppt, .pptx, .xls, .xlsx)
  - Not a Python package, must be installed separately
  - Tested in `office_document_test.py --check-libreoffice`

**Optional Python packages (extras):**
- `[image]` - Pillow for BMP, TIFF, GIF, WebP support
- `[text]` - ReportLab for TXT, MD to PDF conversion
- `[markdown]` - Enhanced markdown conversion (markdown, weasyprint, pygments)
- `[all]` - All optional dependencies

## Common Patterns and Best Practices

### Adding a New Modal Processor

1. Create class inheriting from `GenericModalProcessor` in modalprocessors.py
2. Implement `process_multimodal_content()` method
3. Register in `get_processor_for_type()` in utils.py
4. Add processor initialization in `RAGAnything.__post_init__()`
5. Add prompt template to PROMPTS in prompt.py

### Adding Parser Support

1. Create parser class in parser.py inheriting from `Parser`
2. Implement `parse_document()` returning standard content list format
3. Add parser option in config.py
4. Update parser selection logic in processor.py
5. Add example/test in examples/

### Handling LLM/Vision Model Functions

Functions are passed as callables with specific signatures:

```python
# LLM model function
def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
    return openai_complete_if_cache("gpt-4o-mini", prompt, ...)

# Vision model function (must handle multiple formats)
def vision_model_func(prompt, system_prompt=None, history_messages=[],
                     image_data=None, messages=None, **kwargs):
    if messages:  # VLM-enhanced multimodal format
        return openai_complete_if_cache("gpt-4o", "", messages=messages, ...)
    elif image_data:  # Single image format
        # Build messages with image
    else:  # Fallback to text
        return llm_model_func(prompt, ...)
```

### Working with LightRAG Integration

RAGAnything wraps LightRAG, so:
- Access LightRAG instance via `self.lightrag`
- Can accept pre-initialized LightRAG instance via `lightrag=` parameter
- LightRAG storage accessed through `self.lightrag.key_string_value_json_storage_cls`
- Use LightRAG's async patterns and storage abstractions

### Error Handling

- Parser errors raise `MineruExecutionError` with return code and message
- Document processing errors logged but don't stop batch operations
- Cache errors are non-fatal (will reprocess if cache fails)

## Testing Considerations

- Parser tests should work without API keys (office_document_test.py, image_format_test.py)
- Full RAG tests require valid OpenAI API key or compatible endpoint
- Use small test documents to avoid long processing times
- Test both sync and async methods for new features
- Verify cache hit/miss behavior when testing query methods

## Package Publishing

The package is published to PyPI as `raganything`:
- Version defined in `raganything/__init__.py` as `__version__`
- Build configuration in pyproject.toml and setup.py
- Uses setuptools for building
- Supports extras for optional dependencies

## Related Projects

- **LightRAG** - Base RAG framework: https://github.com/HKUDS/LightRAG
- **MinerU** - Document parser: https://github.com/opendatalab/MinerU
- **VideoRAG** - Video RAG extension: https://github.com/HKUDS/VideoRAG
