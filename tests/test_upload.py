import asyncio
import tempfile
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from pypdf import PdfWriter

from types import SimpleNamespace

from app.main import app
from app.retrieval import Chunk, retriever
from app import services
from app.services import LLM, ingest_pdf
import app.workflow as workflow_module


def test_document_upload_returns_success_for_pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buffer = BytesIO()
    writer.write(buffer)
    pdf_bytes = buffer.getvalue()

    client = TestClient(app)
    response = client.post(
        "/api/v1/documents",
        files={"file": ("sample.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["title"] == "sample.pdf"
    assert "chunks" in payload


def test_upload_clears_previous_conversation_memory():
    services.memory["default"] = [{"role": "user", "content": "Earlier document said revenue was 999"}]

    client = TestClient(app)
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buffer = BytesIO()
    writer.write(buffer)
    pdf_bytes = buffer.getvalue()

    response = client.post(
        "/api/v1/documents",
        files={"file": ("fresh.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200, response.text
    assert services.memory["default"] == []


def test_retriever_replaces_prior_document_chunks_when_new_document_is_added():
    retriever.reset()
    retriever.add([Chunk("doc-1", "first.pdf", "Revenue 1000 Gross profit 400", 1, "page-1")])
    assert any("Revenue" in chunk.text for chunk, _ in retriever.search("revenue", k=3))

    retriever.reset()
    retriever.add([Chunk("doc-2", "second.pdf", "Net income 200 and cash flow 700", 1, "page-1")])
    hits = retriever.search("revenue", k=3)

    assert hits
    assert all("Revenue" not in chunk.text for chunk, _ in hits)
    assert any("Net income" in chunk.text for chunk, _ in hits)


def test_llm_fallback_uses_evidence_when_service_unavailable():
    response = asyncio.run(
        LLM().complete("Question: Which firm has the highest margin?\nEvidence:\n[1] sample.pdf p.1: Revenue 1000 Gross profit 400")
    )

    assert "evidence" in response.lower() or "information provided" in response.lower()
    assert "sample" in response.lower() or "margin" in response.lower()


def test_ingest_pdf_creates_searchable_content_for_blank_pages():
    with tempfile.NamedTemporaryFile(prefix="Alpha_Corp_2024_", suffix=".pdf", delete=False) as handle:
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        writer.write(handle)
        path = Path(handle.name)

    try:
        result = ingest_pdf(path)
        hits = retriever.search("Alpha Corp", k=5)
    finally:
        path.unlink(missing_ok=True)

    assert result["chunks"] >= 1
    assert any("Alpha" in chunk.text or "Alpha" in chunk.title for chunk, _ in hits)


def test_workflow_prefers_evidence_when_llm_refuses(monkeypatch):
    async def fake_complete(self, prompt):
        return "I’m sorry, but I don’t have any information on the company’s latest revenue or profit figures in the provided evidence."

    monkeypatch.setattr(LLM, "complete", fake_complete)
    monkeypatch.setattr(LLM, "__init__", lambda self: setattr(self, "client", object()) or setattr(self, "model", "fake-model"))

    result = asyncio.run(
        workflow_module.answer(
            {
                "question": "What were the latest revenue and profit figures?",
                "conversation_id": "demo",
                "sources": [
                    {
                        "source_id": "s1",
                        "title": "sample.pdf",
                        "page": 1,
                        "section": "doc",
                        "score": 0.9,
                        "excerpt": "Revenue 1000 Gross profit 400 Net income 200",
                        "text": "Revenue 1000 Gross profit 400 Net income 200",
                    }
                ],
                "graph_data": [],
            }
        )
    )

    assert "sample.pdf" in result["answer"]
    assert "Revenue" in result["answer"]


def test_ingest_pdf_handles_page_extraction_errors(monkeypatch):
    class _BrokenPage:
        def extract_text(self):
            raise RuntimeError("unexpected extraction failure")

    class _StubReader:
        def __init__(self, *args, **kwargs):
            self.pages = [_BrokenPage()]
            self.metadata = {"title": "SEC filing"}

    monkeypatch.setattr("app.services.PdfReader", _StubReader)

    with tempfile.NamedTemporaryFile(prefix="sec_filing_", suffix=".pdf", delete=False) as handle:
        handle.write(b"%PDF-1.4\n%fake")
        path = Path(handle.name)

    try:
        result = ingest_pdf(path)
    finally:
        path.unlink(missing_ok=True)

    assert result["chunks"] >= 1
    assert result["title"] == path.name
