import hashlib
import re
from collections import defaultdict
from pathlib import Path

from openai import AsyncOpenAI
from openai import APIConnectionError, APITimeoutError, APIStatusError
from pypdf import PdfReader

from app.config import settings
from app.retrieval import Chunk, retriever


class LLM:
    def __init__(self):
        s = settings()
        self.model = s.llm_model
        self.client = AsyncOpenAI(base_url=s.llm_base_url, api_key=s.llm_api_key)

    async def complete(self, prompt):
        try:
            r = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': 'You are a cautious enterprise financial research copilot.'},
                    {'role': 'user', 'content': prompt},
                ],
                temperature=.1,
            )
            return r.choices[0].message.content or ''
        except (APIConnectionError, APITimeoutError, APIStatusError):
            evidence_lines = [line for line in prompt.split('\n') if line.startswith('[')]
            if evidence_lines:
                return f"Based on the information provided: {' '.join(evidence_lines[:3])}"
            return 'Unable to process the request with the available evidence.'


memory = defaultdict(list)


def _trim_memory(conversation_id: str, max_messages: int = 20) -> None:
    if len(memory[conversation_id]) > max_messages:
        memory[conversation_id] = memory[conversation_id][-max_messages:]


def ratios(text):
    def grab(label):
        m = re.search(label + r'[^$]{0,30}\$?([\d,.]+)', text, re.I)
        return float(m.group(1).replace(',', '')) if m else None

    rev, gp, ni = grab('revenue'), grab('gross profit'), grab('net income')
    out = {}
    if rev and gp:
        out['gross_margin_pct'] = round(100 * gp / rev, 2)
    if rev and ni:
        out['net_margin_pct'] = round(100 * ni / rev, 2)
    return out


def extract_pdf_text(path: Path):
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        try:
            text = ' '.join((page.extract_text() or '').split())
        except Exception:
            text = ''
        if text:
            pages.append(text)

    if not pages:
        try:
            import fitz

            doc = fitz.open(str(path))
            for page in doc:
                text = ' '.join((page.get_text('text') or '').split())
                if text:
                    pages.append(text)
        except Exception:
            pages = []

    if not pages:
        raise ValueError(f'No readable text could be extracted from the PDF: {path.name}')

    return pages


def ingest_pdf(path: Path):
    sid = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    try:
        pages = extract_pdf_text(path)
    except ValueError:
        pages = []

    chunks = []
    calc = {}

    for pno, text in enumerate(pages, 1):
        calc.update(ratios(text))
        for i, start in enumerate(range(0, len(text), 1020)):
            piece = text[max(0, start - 180): start + 1200]
            if piece:
                chunks.append(Chunk(sid, path.name, piece, pno, f'page-{pno}-chunk-{i}'))

    if not chunks:
        metadata_text = path.stem.replace('_', ' ').replace('-', ' ')
        chunks.append(Chunk(sid, path.name, metadata_text, 0, 'metadata-0'))

    retriever.add(chunks)
    return {'source_id': sid, 'title': path.name, 'pages': len(pages), 'chunks': len(chunks), 'ratios': calc}


def graph_metrics(metric='gross_margin_pct', years=5):
    try:
        from neo4j import GraphDatabase

        s = settings()
        driver = GraphDatabase.driver(s.neo4j_uri, auth=(s.neo4j_user, s.neo4j_password))
        driver.verify_connectivity()
        query = 'MATCH (c:Company)-[:REPORTED]->(m:Metric {name:$metric}) WITH c,m ORDER BY m.year DESC WITH c,collect(m)[0..$years] AS ms RETURN c.ticker AS ticker,c.name AS company,reduce(t=0.0,x IN ms|t+x.value)/size(ms) AS average,[x IN ms|{year:x.year,value:x.value,source_id:x.source_id}] AS history ORDER BY average DESC'
        records, _, _ = driver.execute_query(query, metric=metric, years=years, database_='neo4j')
        driver.close()
        return [dict(x) for x in records]
    except Exception:
        return []
