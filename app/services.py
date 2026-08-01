import hashlib,re
from collections import defaultdict
from pathlib import Path
from pypdf import PdfReader
from openai import AsyncOpenAI
from app.config import settings
from app.retrieval import Chunk,retriever
class LLM:
    def __init__(self):
        s=settings(); self.model=s.llm_model; self.client=AsyncOpenAI(base_url=s.llm_base_url,api_key=s.llm_api_key)
    async def complete(self,prompt):
        r=await self.client.chat.completions.create(model=self.model,messages=[{'role':'system','content':'You are a cautious enterprise financial research copilot.'},{'role':'user','content':prompt}],temperature=.1)
        return r.choices[0].message.content or ''
memory=defaultdict(list)
_MAX_MEMORY_CONVOS=500   # cap distinct conversation IDs kept in RAM
_MAX_MEMORY_TURNS=100    # cap messages per conversation (100 = 50 turns)
def _trim_memory(cid:str):
    """Evict oldest turns if a conversation grows too large; also evict oldest convos."""
    if len(memory[cid])>_MAX_MEMORY_TURNS:
        memory[cid]=memory[cid][-_MAX_MEMORY_TURNS:]
    if len(memory)>_MAX_MEMORY_CONVOS:
        oldest=next(iter(memory)); del memory[oldest]
def ratios(text):
    def grab(label):
        m=re.search(label+r'[^$]{0,30}\$?([\d,.]+)',text,re.I); return float(m.group(1).replace(',','')) if m else None
    rev,gp,ni=grab('revenue'),grab('gross profit'),grab('net income'); out={}
    if rev and gp:out['gross_margin_pct']=round(100*gp/rev,2)
    if rev and ni:out['net_margin_pct']=round(100*ni/rev,2)
    return out
def _extract_year(text):
    m=re.findall(r'\b(20\d{2}|19\d{2})\b',text)
    years=[int(y) for y in m if 1990<=int(y)<=2030]
    return max(set(years),key=years.count) if years else None
def _write_to_neo4j(sid,title,full_text,calc):
    try:
        from neo4j import GraphDatabase
        import logging
        s=settings(); driver=GraphDatabase.driver(s.neo4j_uri,auth=(s.neo4j_user,s.neo4j_password))
        driver.verify_connectivity()
        stem=Path(title).stem
        ticker=re.sub(r'[^A-Z0-9]','',stem.upper())[:8] or 'UNKNOWN'
        year=_extract_year(full_text) or 2024
        with driver.session() as session:
            session.run('MERGE (c:Company {ticker:$ticker}) SET c.name=$name,c.source_id=$sid',ticker=ticker,name=stem,sid=sid)
            for metric,value in calc.items():
                session.run(
                    'MATCH (c:Company {ticker:$ticker})'
                    ' MERGE (m:Metric {source_id:$sid,name:$metric,year:$year})'
                    ' SET m.value=$value'
                    ' MERGE (c)-[:REPORTED]->(m)',
                    ticker=ticker,sid=sid,metric=metric,year=year,value=value)
        driver.close()
        logging.getLogger(__name__).info('Neo4j: wrote Company(%s) with %d metrics',ticker,len(calc))
    except Exception as e:
        import logging; logging.getLogger(__name__).warning('Neo4j write skipped: %s',e)
def ingest_pdf(path:Path):
    sid=hashlib.sha256(path.read_bytes()).hexdigest()[:16]; reader=PdfReader(str(path)); chunks=[]; calc={}; full_text=[]
    for pno,page in enumerate(reader.pages,1):
        text=' '.join((page.extract_text() or '').split()); calc.update(ratios(text)); full_text.append(text)
        for i,start in enumerate(range(0,len(text),1020)):
            piece=text[max(0,start-180):start+1200]
            if piece:chunks.append(Chunk(sid,path.name,piece,pno,f'page-{pno}-chunk-{i}'))
    retriever.add(chunks)
    _write_to_neo4j(sid,path.name,' '.join(full_text),calc)
    return {'source_id':sid,'title':path.name,'pages':len(reader.pages),'chunks':len(chunks),'ratios':calc}
def graph_metrics(metric='gross_margin_pct',years=5):
    try:
        from neo4j import GraphDatabase
        s=settings(); driver=GraphDatabase.driver(s.neo4j_uri,auth=(s.neo4j_user,s.neo4j_password)); driver.verify_connectivity()
        query='MATCH (c:Company)-[:REPORTED]->(m:Metric {name:$metric}) WITH c,m ORDER BY m.year DESC WITH c,collect(m)[0..$years] AS ms RETURN c.ticker AS ticker,c.name AS company,reduce(t=0.0,x IN ms|t+x.value)/size(ms) AS average,[x IN ms|{year:x.year,value:x.value,source_id:x.source_id}] AS history ORDER BY average DESC'
        records,_,_=driver.execute_query(query,metric=metric,years=years,database_='neo4j'); driver.close(); return [dict(x) for x in records]
    except Exception:return []
