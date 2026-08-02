from typing import TypedDict
from app.retrieval import retriever
from app.services import LLM,memory,graph_metrics,_trim_memory,ratios
from app.config import settings

try:
    from langgraph.graph import StateGraph,START,END
except Exception:
    StateGraph=None; START='__start__'; END='__end__'

class State(TypedDict,total=False):
    question:str; conversation_id:str; top_k:int; sources:list; graph_data:list; answer:str; confidence:float; status:str

async def retrieve(s):
    hits=retriever.search(s['question'],s.get('top_k',8)); return {'sources':[{'source_id':c.source_id,'title':c.title,'page':c.page,'section':c.section,'score':score,'excerpt':c.text[:450],'text':c.text} for c,score in hits]}

def graph(s): return {'graph_data':graph_metrics() if 'gross margin' in s['question'].lower() else []}

def _looks_like_refusal(text:str)->bool:
    if not text:
        return True
    lowered=text.lower()
    refusal_phrases=(
        "i don't have any information",
        "i don’t have any information",
        "no information",
        "cannot provide",
        "can’t provide",
        "not enough information",
        "i'm sorry",
        "i am sorry",
    )
    return any(phrase in lowered for phrase in refusal_phrases)


def _build_evidence_answer(question,sources,graph_data):
    if not sources:
        return 'No indexed evidence matched that question yet. Upload a PDF and try again so the research index can be populated.'
    top_sources=sources[:3]
    details=[]
    for source in top_sources:
        text=source.get('text','') or ''
        metrics=ratios(text)
        if metrics:
            metrics_desc=', '.join(f'{k}={v}' for k,v in metrics.items())
            details.append(f"{source['title']} (p.{source.get('page','?')}): {metrics_desc}")
        else:
            excerpt=(text[:220]+'…') if len(text)>220 else text
            details.append(f"{source['title']} (p.{source.get('page','?')}): {excerpt}")
    base=f"I found {len(sources)} relevant passages for '{question}'. The strongest evidence is: " + '; '.join(details)
    if graph_data:
        base+=f" Graph comparison data was also included: {graph_data[:2]}"
    return base

async def answer(s):
    convo_memory=memory.get(s['conversation_id'],[])
    refs='\n\n'.join(f"[{i+1}] {x['title']} p.{x['page']}: {x['text']}" for i,x in enumerate(s.get('sources',[])))
    prompt=f"Question: {s['question']}\nPrior conversation: {convo_memory[-6:]}\nKnowledge graph: {s.get('graph_data',[])}\nEvidence:\n{refs}\nUse only evidence, cite [n], separate facts/calculations/inference, and say when evidence is insufficient. Do not provide personalized investment advice."
    llm=LLM()
    fallback_answer=_build_evidence_answer(s['question'],s.get('sources',[]),s.get('graph_data',[]))
    if not llm.client:
        text=fallback_answer
    else:
        try:
            text=await llm.complete(prompt)
            if _looks_like_refusal(text):
                text=fallback_answer
        except Exception:
            text=fallback_answer
    memory[s['conversation_id']]+=[{'role':'user','content':s['question']},{'role':'assistant','content':text}]; _trim_memory(s['conversation_id'])
    scores=[x['score'] for x in s.get('sources',[])]; confidence=max(0,min(1,sum(scores)/len(scores))) if scores else 0
    return {'answer':text,'confidence':confidence,'status':'needs_approval' if confidence<settings().human_approval_threshold else 'completed'}

class _SimpleWorkflow:
    async def ainvoke(self,state):
        state=dict(state)
        retrieved=await retrieve(state)
        graph_data=graph(state).get('graph_data',[])
        result=await answer({**state,**retrieved,'graph_data':graph_data})
        return {**state,**retrieved,**result,'graph_data':graph_data}

if StateGraph:
    g=StateGraph(State); g.add_node('retrieve',retrieve);g.add_node('graph',graph);g.add_node('answer',answer);g.add_edge(START,'retrieve');g.add_edge('retrieve','graph');g.add_edge('graph','answer');g.add_edge('answer',END);workflow=g.compile()
else:
    workflow=_SimpleWorkflow()
