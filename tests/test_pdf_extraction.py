from pathlib import Path

import pymupdf

from app.services import extract_pdf_text, ingest_pdf


def _write_pdf(path: Path, text: str):
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 720), text, fontsize=12)
    doc.save(path)
    doc.close()


def test_extract_pdf_text_reads_plain_text(tmp_path):
    file_path = tmp_path / 'sample.pdf'
    sample = 'Revenue $10,000 Gross Profit $4,000 Net Income $1,500'
    _write_pdf(file_path, sample)

    pages = extract_pdf_text(file_path)

    assert pages
    assert 'Revenue' in pages[0]
    assert 'Gross Profit' in pages[0]


def test_ingest_pdf_handles_blank_pdf(tmp_path):
    file_path = tmp_path / 'blank.pdf'
    doc = pymupdf.open()
    doc.new_page(width=612, height=792)
    doc.save(file_path)
    doc.close()

    result = ingest_pdf(file_path)

    assert result['chunks'] >= 1
    assert result['title'] == 'blank.pdf'
