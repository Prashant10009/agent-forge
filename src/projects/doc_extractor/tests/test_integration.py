import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2] / 'src' / 'projects' / 'doc_extractor'
sys.path.insert(0, str(ROOT))

from doc_extractor.pipeline import DocumentPipeline
from doc_extractor.models import Document

@pytest.fixture
def sample_document():
    return Document(
        id="test123",
        content="This is a test document.",
        metadata={"author": "tester"}
    )

def test_document_pipeline_integration(sample_document):
    pipeline = DocumentPipeline()
    processed_doc = pipeline.process(sample_document)
    
    assert processed_doc.id == "test123"
    assert len(processed_doc.content) > 0
    assert "author" in processed_doc.metadata
    assert processed_doc.metadata["author"] == "tester"
    assert hasattr(processed_doc, "processed_at")

def test_document_pipeline_handles_empty_document():
    pipeline = DocumentPipeline()
    processed = pipeline.process({})
    
    assert isinstance(processed, dict)
    assert "metadata" in processed
    assert "processed_at" in processed["metadata"]