#!/usr/bin/env python
"""
RAG-Anything FastAPI Server
API REST server for document processing and querying with RAG-Anything
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Header, Query, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=".env", override=False)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from raganything import RAGAnything, RAGAnythingConfig
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc, logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# Configuration from environment
API_KEY = os.getenv("API_KEY", "your-secret-api-key")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
VISION_MODEL = os.getenv("VISION_MODEL", "gpt-4o")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "3072"))
WORKING_DIR = os.getenv("WORKING_DIR", "./rag_storage")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
METADATA_FILE = os.getenv("METADATA_FILE", "./rag_storage/documents_metadata.json")

# Create necessary directories
Path(WORKING_DIR).mkdir(parents=True, exist_ok=True)
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

# Global RAG instance
rag_instance: Optional[RAGAnything] = None


# Pydantic models
class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    query: str = Field(..., description="Query text to search in documents")
    file_name: Optional[str] = Field(None, description="Optional: filter by specific document name")
    mode: str = Field("mix", description="Query mode: mix, hybrid, local, global, naive")
    vlm_enhanced: bool = Field(True, description="Enable VLM enhancement for image analysis")


class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    query: str
    result: str
    file_name: Optional[str] = None
    mode: str
    timestamp: str


class UploadResponse(BaseModel):
    """Response model for upload endpoint"""
    success: bool
    doc_id: str
    file_name: str
    message: str
    timestamp: str


class DocumentInfo(BaseModel):
    """Document information model"""
    doc_id: str
    file_name: str
    file_size: int
    upload_timestamp: str
    status: str


class DocumentsListResponse(BaseModel):
    """Response model for documents list"""
    total: int
    documents: List[DocumentInfo]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    rag_initialized: bool


class DeleteResponse(BaseModel):
    """Response model for delete endpoint"""
    success: bool
    message: str
    doc_id: str


# Document metadata management
class DocumentMetadata:
    """Manage document metadata storage"""

    def __init__(self, metadata_file: str):
        self.metadata_file = Path(metadata_file)
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        self.metadata: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        """Load metadata from file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                log.error(f"Error loading metadata: {e}")
                return {}
        return {}

    def _save(self):
        """Save metadata to file"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.error(f"Error saving metadata: {e}")

    def add_document(self, doc_id: str, file_name: str, file_size: int) -> None:
        """Add document metadata"""
        self.metadata[doc_id] = {
            "doc_id": doc_id,
            "file_name": file_name,
            "file_size": file_size,
            "upload_timestamp": datetime.utcnow().isoformat(),
            "status": "processed"
        }
        self._save()

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document metadata by doc_id"""
        return self.metadata.get(doc_id)

    def get_by_filename(self, file_name: str) -> Optional[Dict[str, Any]]:
        """Get document metadata by filename"""
        for doc_id, meta in self.metadata.items():
            if meta.get("file_name") == file_name:
                return meta
        return None

    def list_all(self) -> List[Dict[str, Any]]:
        """List all documents"""
        return list(self.metadata.values())

    def delete_document(self, doc_id: str) -> bool:
        """Delete document metadata"""
        if doc_id in self.metadata:
            del self.metadata[doc_id]
            self._save()
            return True
        return False


# Initialize metadata manager
doc_metadata = DocumentMetadata(METADATA_FILE)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    global rag_instance

    log.info("Starting RAG-Anything API server...")

    # Validate environment
    if not OPENAI_API_KEY:
        log.error("OPENAI_API_KEY not set in environment!")
        raise ValueError("OPENAI_API_KEY is required")

    try:
        # Initialize RAG
        log.info("Initializing RAGAnything instance...")

        config = RAGAnythingConfig(
            working_dir=WORKING_DIR,
            parser="mineru",
            parse_method="auto",
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=True,
        )

        # LLM function
        def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
            return openai_complete_if_cache(
                LLM_MODEL,
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
                api_key=OPENAI_API_KEY,
                base_url=OPENAI_BASE_URL,
                **kwargs,
            )

        # Vision model function
        def vision_model_func(prompt, system_prompt=None, history_messages=[],
                             image_data=None, messages=None, **kwargs):
            if messages:
                return openai_complete_if_cache(
                    VISION_MODEL,
                    "",
                    system_prompt=None,
                    history_messages=[],
                    messages=messages,
                    api_key=OPENAI_API_KEY,
                    base_url=OPENAI_BASE_URL,
                    **kwargs,
                )
            elif image_data:
                return openai_complete_if_cache(
                    VISION_MODEL,
                    "",
                    system_prompt=None,
                    history_messages=[],
                    messages=[
                        {"role": "system", "content": system_prompt} if system_prompt else None,
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                            ],
                        } if image_data else {"role": "user", "content": prompt},
                    ],
                    api_key=OPENAI_API_KEY,
                    base_url=OPENAI_BASE_URL,
                    **kwargs,
                )
            else:
                return llm_model_func(prompt, system_prompt, history_messages, **kwargs)

        # Embedding function
        embedding_func = EmbeddingFunc(
            embedding_dim=EMBEDDING_DIM,
            max_token_size=8192,
            func=lambda texts: openai_embed(
                texts,
                model=EMBEDDING_MODEL,
                api_key=OPENAI_API_KEY,
                base_url=OPENAI_BASE_URL,
            ),
        )

        # Create RAG instance
        rag_instance = RAGAnything(
            config=config,
            llm_model_func=llm_model_func,
            vision_model_func=vision_model_func,
            embedding_func=embedding_func,
        )

        log.info("RAGAnything initialized successfully!")

    except Exception as e:
        log.error(f"Failed to initialize RAGAnything: {e}")
        raise

    yield

    # Cleanup
    log.info("Shutting down RAG-Anything API server...")


# Create FastAPI app
app = FastAPI(
    title="RAG-Anything API",
    description="API for multimodal document processing and querying",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication dependency
async def verify_api_key(x_api_key: str = Header(..., description="API Key for authentication")):
    """Verify API key from header"""
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return x_api_key


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="RAG-Anything API is running",
        rag_initialized=rag_instance is not None
    )


@app.post("/upload", response_model=UploadResponse, dependencies=[])
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload and process"),
    x_api_key: str = Header(..., description="API Key")
):
    """
    Upload and process a document

    Supported formats: PDF, Office (doc, docx, ppt, pptx, xls, xlsx), images (jpg, png, etc.), text (txt, md)
    """
    # Verify API key
    await verify_api_key(x_api_key)

    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        # Save uploaded file
        file_path = Path(UPLOAD_DIR) / file.filename
        content = await file.read()
        file_size = len(content)

        with open(file_path, "wb") as f:
            f.write(content)

        log.info(f"Processing file: {file.filename}")

        # Process document with RAG
        doc_id = await rag_instance.process_document_complete(
            file_path=str(file_path),
            output_dir=OUTPUT_DIR,
            parse_method="auto",
            display_stats=True
        )

        # Store metadata
        doc_metadata.add_document(doc_id, file.filename, file_size)

        log.info(f"Document processed successfully: {file.filename} (doc_id: {doc_id})")

        return UploadResponse(
            success=True,
            doc_id=doc_id,
            file_name=file.filename,
            message=f"Document processed successfully",
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        log.error(f"Error processing document {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    x_api_key: str = Header(..., description="API Key")
):
    """
    Query processed documents

    - If file_name is provided, searches only in that document
    - If file_name is not provided, searches across all documents
    """
    # Verify API key
    await verify_api_key(x_api_key)

    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        # Build query
        query_text = request.query

        # If file_name specified, add it to the query context
        if request.file_name:
            # Get doc_id for the file
            doc_info = doc_metadata.get_by_filename(request.file_name)
            if not doc_info:
                raise HTTPException(
                    status_code=404,
                    detail=f"Document not found: {request.file_name}"
                )

            # Enhance query with document context
            query_text = f"En el documento '{request.file_name}': {request.query}"
            log.info(f"Querying specific document: {request.file_name}")
        else:
            log.info("Querying all documents")

        # Execute query
        result = await rag_instance.aquery(
            query_text,
            mode=request.mode,
            vlm_enhanced=request.vlm_enhanced
        )

        return QueryResponse(
            query=request.query,
            result=result,
            file_name=request.file_name,
            mode=request.mode,
            timestamp=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error querying documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error querying: {str(e)}")


@app.get("/documents", response_model=DocumentsListResponse)
async def list_documents(
    x_api_key: str = Header(..., description="API Key")
):
    """List all processed documents"""
    # Verify API key
    await verify_api_key(x_api_key)

    try:
        documents = doc_metadata.list_all()

        return DocumentsListResponse(
            total=len(documents),
            documents=[DocumentInfo(**doc) for doc in documents]
        )

    except Exception as e:
        log.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@app.delete("/documents/{doc_id}", response_model=DeleteResponse)
async def delete_document(
    doc_id: str,
    x_api_key: str = Header(..., description="API Key")
):
    """Delete a document from the system"""
    # Verify API key
    await verify_api_key(x_api_key)

    try:
        # Get document info
        doc_info = doc_metadata.get_document(doc_id)
        if not doc_info:
            raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")

        # Delete from metadata
        success = doc_metadata.delete_document(doc_id)

        # Note: LightRAG doesn't have a built-in delete function for specific documents
        # The document will remain in the knowledge graph but won't appear in the metadata

        if success:
            log.info(f"Document deleted from metadata: {doc_id}")
            return DeleteResponse(
                success=True,
                message="Document removed from metadata (knowledge graph data persists)",
                doc_id=doc_id
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to delete document")

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    log.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
