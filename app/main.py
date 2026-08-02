import re,tempfile,shutil,json
from pathlib import Path
from fastapi import FastAPI,UploadFile,File,HTTPException,Request,Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse,RedirectResponse,Response
from pydantic import BaseModel,Field
from prometheus_client import make_asgi_app,generate_latest,CONTENT_TYPE_LATEST
from app.config import settings
from app.retrieval import retriever
from app.services import ingest_pdf,LLM,memory
from app.workflow import workflow

_SAFE_FILENAME=re.compile(r'[^a-zA-Z0-9._-]')
def _sanitize(name:str)->str:
    """Strip path components and replace unsafe characters to prevent path traversal."""
    stem=Path(name).name                          # drop any directory parts (e.g. ../../evil)
    safe=_SAFE_FILENAME.sub('_',stem)[:200]       # allow only safe chars, cap length
    return safe or 'upload.pdf'

def _metrics_auth(request:Request):
    token=settings().metrics_token
    if token and request.headers.get('X-Metrics-Token')!=token:
        raise HTTPException(403,'Forbidden')

class Ask(BaseModel):
    question:str=Field(min_length=3,max_length=4000); conversation_id:str='default'; top_k:int=Field(8,ge=1,le=30)
app=FastAPI(title='Enterprise Financial Research Assistant',version='0.1.0')
app.add_middleware(CORSMiddleware,allow_origins=settings().cors_origins,allow_methods=['*'],allow_headers=['*'])
@app.get('/',include_in_schema=False)
def root():return RedirectResponse('/docs')
@app.get('/api/v1/health')
def health():return {'status':'ok','indexed_chunks':len(retriever.chunks)}
@app.post('/api/v1/documents')
async def documents(file:UploadFile=File(...)):
    if not file.filename or not file.filename.lower().endswith('.pdf'):raise HTTPException(400,'Only PDF files are supported')
    raw=await file.read(settings().max_upload_bytes+1)
    if len(raw)>settings().max_upload_bytes:raise HTTPException(413,f'File too large (max {settings().max_upload_bytes//1024//1024} MB)')
    safe_name=_sanitize(file.filename)
    with tempfile.NamedTemporaryFile(delete=False,suffix='.pdf',prefix='upload_') as f:f.write(raw);p=Path(f.name)
    try:
        named=p.with_name(safe_name); p.rename(named); p=named
        retriever.reset()
        memory.clear()
        result=ingest_pdf(p)
        return result
    finally:
        if p.exists() and p != Path(file.filename):
            p.unlink(missing_ok=True)
@app.post('/api/v1/ask')
async def ask(req:Ask):
    s=await workflow.ainvoke(req.model_dump()); return {'answer':s['answer'],'confidence':s['confidence'],'status':s['status'],'sources':[{k:v for k,v in x.items() if k!='text'} for x in s.get('sources',[])],'graph_data':s.get('graph_data',[])}
@app.post('/api/v1/ask/stream')
async def stream(req:Ask):
    hits=retriever.search(req.question,req.top_k); refs='\n\n'.join(f'[{i+1}] {c.title} p.{c.page}: {c.text}' for i,(c,_) in enumerate(hits))
    async def gen():
        yield 'data: '+json.dumps({'type':'sources','sources':[{'title':c.title,'page':c.page,'score':s} for c,s in hits]})+'\n\n'
        try:
            llm=LLM(); client=llm.client; model=llm.model
            if not client:
                yield 'data: '+json.dumps({'type':'token','content':'I could not contact the configured LLM service. The app will continue with the retrieved evidence only.'})+'\n\n'
            else:
                r=await client.chat.completions.create(model=model,messages=[{'role':'system','content':'You are a cautious financial research copilot.'},{'role':'user','content':f'Question: {req.question}\nEvidence:\n{refs}\nCite [n].'}],temperature=.1,stream=True)
                async for ch in r:
                    token=ch.choices[0].delta.content or ''
                    if token:yield 'data: '+json.dumps({'type':'token','content':token})+'\n\n'
            yield 'data: '+json.dumps({'type':'done'})+'\n\n'
        except Exception as e:yield 'data: '+json.dumps({'type':'error','message':str(e)})+'\n\n'
    return StreamingResponse(gen(),media_type='text/event-stream')
@app.get('/metrics',include_in_schema=False,dependencies=[Depends(_metrics_auth)])
def metrics():return Response(generate_latest(),media_type=CONTENT_TYPE_LATEST)
