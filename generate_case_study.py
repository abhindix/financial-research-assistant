"""Generate portfolio_case_study.pdf for the Enterprise Financial Research Assistant."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

# ── Colour palette ────────────────────────────────────────────────────────────
NAVY   = colors.HexColor('#0A2342')
TEAL   = colors.HexColor('#1B7F79')
SILVER = colors.HexColor('#EAF0F6')
GREY   = colors.HexColor('#4A4A4A')
WHITE  = colors.white

OUTPUT = 'portfolio_case_study.pdf'

# ── Style helpers ─────────────────────────────────────────────────────────────
BASE = getSampleStyleSheet()

def style(name, parent='Normal', **kw):
    s = ParagraphStyle(name, parent=BASE[parent], **kw)
    return s

H1   = style('H1', 'Title',   fontSize=26, textColor=NAVY,  spaceAfter=6,
             fontName='Helvetica-Bold')
H2   = style('H2', 'Heading2', fontSize=15, textColor=TEAL,  spaceBefore=14,
             spaceAfter=4,  fontName='Helvetica-Bold')
H3   = style('H3', 'Heading3', fontSize=12, textColor=NAVY,  spaceBefore=8,
             spaceAfter=2,  fontName='Helvetica-Bold')
BODY = style('BODY', fontSize=10.5, textColor=GREY, leading=16,
             alignment=TA_JUSTIFY, spaceAfter=6)
MONO = style('MONO', fontSize=9.5, textColor=NAVY, leading=14,
             fontName='Courier', spaceAfter=4)
CAP  = style('CAP', fontSize=10, textColor=TEAL, spaceAfter=14,
             alignment=TA_CENTER, fontName='Helvetica-Oblique')
BULL = style('BULL', fontSize=10.5, textColor=GREY, leading=15,
             leftIndent=16, spaceAfter=3)

def h1(t):  return Paragraph(t, H1)
def h2(t):  return Paragraph(t, H2)
def h3(t):  return Paragraph(t, H3)
def p(t):   return Paragraph(t, BODY)
def cap(t): return Paragraph(t, CAP)
def mono(t):return Paragraph(t, MONO)
def bull(items):
    return [Paragraph(f'• &nbsp; {item}', BULL) for item in items]
def sp(n=8):return Spacer(1, n)
def hr():   return HRFlowable(width='100%', thickness=1, color=TEAL,
                               spaceAfter=6, spaceBefore=6)

def kv_table(rows, col_widths=(2.2*inch, 4.3*inch)):
    """Two-column key/value table with alternating row shading."""
    data = [[Paragraph(f'<b>{k}</b>', BULL), Paragraph(v, BODY)] for k, v in rows]
    t = Table(data, colWidths=col_widths)
    ts = TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), WHITE),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [WHITE, SILVER]),
        ('TEXTCOLOR', (0, 0), (0, -1), NAVY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#C5D8E8')),
    ])
    t.setStyle(ts)
    return t

def section_header(title):
    """Coloured section banner."""
    data = [[Paragraph(title, ParagraphStyle('BH', fontSize=13,
               textColor=WHITE, fontName='Helvetica-Bold'))]]
    t = Table(data, colWidths=[6.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t

# ── Document ──────────────────────────────────────────────────────────────────
def build():
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=letter,
        leftMargin=0.9*inch,
        rightMargin=0.9*inch,
        topMargin=0.85*inch,
        bottomMargin=0.85*inch,
        title='Portfolio Case Study – Enterprise Financial Research Assistant',
        author='Portfolio',
    )

    story = []

    # ── Cover ─────────────────────────────────────────────────────────────────
    story += [
        sp(30),
        h1('Enterprise Financial Research Assistant'),
        cap('Portfolio Case Study'),
        hr(),
        kv_table([
            ('Type',        'Full-stack AI / MLOps portfolio project'),
            ('Domain',      'Financial research · RAG · Knowledge graphs'),
            ('Stack',       'Python · FastAPI · LangGraph · Neo4j · Streamlit'),
            ('Deployment',  'Docker · Kubernetes · Prometheus / CI'),
        ]),
        sp(20),
    ]

    # ── 1. Executive Summary ──────────────────────────────────────────────────
    story += [
        section_header('1.  Executive Summary'),
        sp(6),
        p('This project demonstrates a production-grade <b>Retrieval-Augmented Generation (RAG)</b> '
          'platform that allows financial analysts to interrogate large collections of SEC filings, '
          'earnings call transcripts, and research PDFs using natural language. '
          'The system combines <i>dense vector search</i>, <i>BM25 sparse retrieval</i>, and a '
          '<i>Neo4j knowledge graph</i> to deliver cited, confidence-scored answers with full '
          'conversation memory — all deployable with a single <b>docker compose up</b>.'),
        sp(4),
        p('Key portfolio signals:'),
        *bull([
            'End-to-end AI pipeline: ingestion → retrieval → graph → synthesis → UI',
            'Hybrid retrieval fusing semantic vectors (all-MiniLM-L6-v2) and BM25 (RRF weighting 65/35)',
            'LangGraph stateful multi-step workflow with human-in-the-loop approval gate',
            'FastAPI REST + SSE streaming endpoints with Prometheus observability',
            'Streamlit analyst UI with file upload, conversation memory, and graph comparison tables',
        ]),
        sp(10),
    ]

    # ── 2. Problem Statement ──────────────────────────────────────────────────
    story += [
        section_header('2.  Problem Statement'),
        sp(6),
        p('Professional financial analysts spend hours manually reading PDFs to answer questions '
          'such as <i>"Which semiconductor companies had the highest gross margin over the last five years?"</i>. '
          'Generic LLMs hallucinate financial figures and cannot cite primary sources. '
          'Enterprise search tools are keyword-only and miss semantic intent.'),
        sp(4),
        p('This project targets three specific gaps:'),
        *bull([
            '<b>Evidence grounding:</b> every answer must be traceable to a page/chunk in a source document.',
            '<b>Structured data integration:</b> numerical metrics from filings should feed a queryable graph, '
            'not just float in unstructured text.',
            '<b>Trust & review:</b> low-confidence answers must be flagged for human approval before being acted on.',
        ]),
        sp(10),
    ]

    # ── 3. Architecture ───────────────────────────────────────────────────────
    story += [
        section_header('3.  System Architecture'),
        sp(6),
        p('The system is composed of four loosely-coupled layers:'),
        sp(4),
    ]

    arch_rows = [
        ('Ingestion layer',
         'PyPDF extracts text page-by-page. Pages are chunked with 180-token overlap '
         '(chunk size 1 200 chars). SHA-256 deduplication prevents re-indexing. '
         'Regex extractors pull gross margin and net margin ratios and persist them to Neo4j.'),
        ('Retrieval layer',
         'HybridRetriever encodes the query with sentence-transformers, performs a '
         'cosine-similarity dense search over a NumPy float32 matrix, then fuses scores '
         'with BM25Okapi (0.65 dense + 0.35 sparse). Results persist across restarts via '
         'chunks.json + vectors.npy.'),
        ('Orchestration layer',
         'A three-node LangGraph DAG (retrieve → graph → answer) manages state. '
         'The graph node enriches answers when the query mentions financial metrics '
         'such as "gross margin". Conversation history (capped at 100 messages / '
         '500 sessions) feeds the answer node for multi-turn coherence.'),
        ('Presentation layer',
         'FastAPI exposes /api/v1/documents (PDF upload), /api/v1/ask (JSON), and '
         '/api/v1/ask/stream (SSE). The Streamlit UI provides file upload, a research '
         'question text area, confidence gauge, cited sources table, and graph-comparison '
         'dataframe. Prometheus metrics are protected by an optional bearer token.'),
    ]
    story += [kv_table(arch_rows, (2.0*inch, 4.5*inch)), sp(10)]

    # ── 4. Technical Implementation ───────────────────────────────────────────
    story += [
        section_header('4.  Technical Implementation'),
        sp(6),
        h3('4.1  Hybrid Retrieval'),
        p('Combining dense and sparse signals captures both semantic similarity and '
          'exact keyword overlap — critical for financial terminology (e.g. "EBITDA", '
          'ticker symbols) where pure vector search can underperform.'),
        mono('score  =  0.65 × cosine_similarity(qv, dv)  +  0.35 × BM25_normalised(q, d)'),
        p('Both score components are normalised to [0, 1] before fusion. '
          'Top-<i>k</i> is configurable per request (default 8, max 30).'),
        sp(6),
        h3('4.2  LangGraph Workflow'),
        p('LangGraph provides a typed <b>StateGraph</b> that guarantees '
          'each node receives a validated state dict and propagates only the keys it '
          'mutates. The DAG is:'),
        *bull([
            '<b>retrieve</b> – runs hybrid search, populates <tt>sources</tt>',
            '<b>graph</b>    – queries Neo4j for metric history when relevant, populates <tt>graph_data</tt>',
            '<b>answer</b>   – calls the OpenAI-compatible LLM with evidence + memory, '
            'computes a confidence score, sets <tt>status</tt> to <tt>needs_approval</tt> '
            'if confidence < 0.55',
        ]),
        sp(6),
        h3('4.3  Knowledge Graph (Neo4j)'),
        p('Each ingested filing creates or updates <tt>Company</tt> and <tt>Metric</tt> nodes '
          'connected by <tt>[:REPORTED]</tt> edges. Cypher queries aggregate multi-year '
          'averages and return ranked comparisons:'),
        mono('MATCH (c:Company)-[:REPORTED]->(m:Metric {name:"gross_margin_pct"})'),
        mono('WITH c, m ORDER BY m.year DESC'),
        mono('RETURN c.ticker, reduce(t=0.0, x IN collect(m)[0..5] | t+x.value) / 5 AS avg5yr'),
        sp(6),
        h3('4.4  Security Controls'),
        *bull([
            'Filename sanitisation (path-traversal prevention) before any disk write',
            '50 MB upload cap enforced before any PDF parsing',
            'CORS origins are configurable (default open for local dev, lock down in prod)',
            'Prometheus /metrics endpoint protected by configurable bearer token',
            'No secrets committed; all credentials via .env / environment variables',
        ]),
        sp(10),
    ]

    # ── 5. Tech Stack ─────────────────────────────────────────────────────────
    story += [
        section_header('5.  Technology Stack'),
        sp(6),
        kv_table([
            ('Web framework',      'FastAPI 0.118+ with Pydantic v2 models and async handlers'),
            ('Orchestration',      'LangGraph 1.x — typed StateGraph, async nodes'),
            ('Embeddings',         'sentence-transformers all-MiniLM-L6-v2 (384-dim, float32)'),
            ('Sparse retrieval',   'rank-bm25 (BM25Okapi)'),
            ('LLM backend',        'OpenAI-compatible endpoint — LM Studio / any OpenAI-API server'),
            ('Graph database',     'Neo4j 6+ via official Python driver; bolt:// or neo4j+s://'),
            ('UI',                 'Streamlit 1.42+ — sidebar upload, metrics, source table, graph view'),
            ('Observability',      'Prometheus client — request counters, latency histograms'),
            ('Containerisation',   'Docker + docker-compose; Kubernetes manifests in /infra'),
            ('Testing / CI',       'pytest; GitHub Actions workflow'),
        ]),
        sp(10),
    ]

    # ── 6. Key Design Decisions ───────────────────────────────────────────────
    story += [
        section_header('6.  Key Design Decisions & Trade-offs'),
        sp(6),
        kv_table([
            ('Local vector store vs. hosted DB',
             'NumPy + BM25 removes external dependencies for local dev and demos. '
             'The README roadmap explicitly targets OpenSearch BM25 + k-NN for production, '
             'keeping the code path identical.'),
            ('LangGraph over plain chains',
             'The StateGraph makes retrieval, graph enrichment, and synthesis individually '
             'testable and replaceable without touching downstream nodes.'),
            ('Sentence-transformer over OpenAI embeddings',
             'Runs fully offline, deterministic, and free. Switch by changing one config key.'),
            ('In-process memory vs. Redis',
             'Dict-backed memory with LRU eviction (500 sessions, 100 turns each) is sufficient '
             'for demo scale; Redis checkpoint integration is pre-wired in config.'),
            ('Human-in-the-loop threshold',
             'Confidence < 0.55 returns status="needs_approval". Threshold is env-configurable '
             'to tune precision/recall trade-off per deployment context.'),
        ]),
        sp(10),
    ]

    # ── 7. Sample Workflow ────────────────────────────────────────────────────
    story += [
        section_header('7.  End-to-End Example Workflow'),
        sp(6),
        p('The following illustrates a typical analyst session:'),
        sp(4),
        *bull([
            'Analyst uploads <i>NVDA_2025_10K.pdf</i> via the sidebar. '
            'Ingest returns chunk count, page count, and extracted ratios '
            '(e.g. gross_margin_pct: 75.0).  The Company/Metric graph is updated.',
            'Analyst types: <i>"What drove NVIDIA\'s gross margin improvement in 2025?"</i>',
            'LangGraph <b>retrieve</b> node returns top-8 hybrid-scored chunks from the filing.',
            'LangGraph <b>graph</b> node detects "gross margin" → queries Neo4j for NVDA '
            'year-over-year metric history.',
            'LangGraph <b>answer</b> node synthesises both evidence streams, cites [n] '
            'references, and computes confidence = 0.72 → status = completed.',
            'The UI renders the answer with inline citations, a confidence badge, '
            'a sources dataframe, and a knowledge-graph comparison table.',
        ]),
        sp(10),
    ]

    # ── 8. Observability & Operations ─────────────────────────────────────────
    story += [
        section_header('8.  Observability & Operations'),
        sp(6),
        p('Production-readiness signals:'),
        *bull([
            '<b>Health endpoint:</b> GET /api/v1/health returns indexed chunk count for liveness/readiness probes.',
            '<b>Prometheus metrics:</b> request count, latency, error rate scraped by any standard collector.',
            '<b>Structured logging:</b> Neo4j write status, memory trim events, and errors are logged via '
            'Python\'s standard <tt>logging</tt> module for aggregation by CloudWatch / ELK.',
            '<b>Docker Compose:</b> single command spin-up of API + Streamlit + (optional) Neo4j.',
            '<b>Kubernetes manifests:</b> /infra directory contains deployment and service YAML.',
            '<b>CI pipeline:</b> GitHub Actions runs pytest on every push.',
        ]),
        sp(10),
    ]

    # ── 9. Production Roadmap ─────────────────────────────────────────────────
    story += [
        section_header('9.  Production Roadmap'),
        sp(6),
        p('This is an engineering portfolio MVP. The README documents the following '
          'production-hardening steps that would be required before institutional use:'),
        *bull([
            'Replace NumPy/BM25 with OpenSearch BM25 + k-NN and reciprocal-rank fusion',
            'Replace dict-backed memory with Redis-persisted LangGraph checkpoints',
            'Ingest structured XBRL facts from SEC EDGAR instead of regex ratio extraction',
            'Add OAuth 2.0 / OIDC, RBAC, document entitlements, and immutable audit logs',
            'Add encryption at rest and in transit, PII detection, and secrets management (Vault / AWS SM)',
            'Add source licences for Bloomberg/Reuters data; respect proprietary content terms',
            'Add evaluation datasets, retrieval quality metrics (MRR, nDCG), and hallucination checks',
            'Add load tests, canary deployments, and SLO alerting',
        ]),
        sp(10),
    ]

    # ── 10. Conclusion ────────────────────────────────────────────────────────
    story += [
        section_header('10.  Conclusion'),
        sp(6),
        p('This portfolio project demonstrates the ability to design and ship a complete '
          '<b>AI-powered research platform</b> from raw data ingestion through to a polished analyst UI — '
          'combining modern LLM orchestration (LangGraph), hybrid retrieval (dense + sparse), '
          'graph-structured domain knowledge (Neo4j), production API patterns (FastAPI + SSE), '
          'and cloud-native operations (Docker, Kubernetes, Prometheus, CI).'),
        sp(4),
        p('The codebase is intentionally minimal (≈ 200 lines of application code) yet production-shaped: '
          'each component is independently replaceable, security controls are explicit, and the README '
          'roadmap is honest about the gap between portfolio MVP and enterprise deployment.'),
        sp(4),
        p('<i>This is an engineering portfolio project, not an investment-advice product.</i>'),
        sp(20),
        hr(),
        cap('Enterprise Financial Research Assistant — Portfolio Case Study'),
    ]

    doc.build(story)
    print(f'Written: {OUTPUT}')


if __name__ == '__main__':
    build()
