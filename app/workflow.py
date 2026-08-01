from typing import TypedDict
from langgraph.graph import StateGraph,START,END
from app.retrieval import retriever
from app.services import LLM,memory,graph_metrics,_trim_memory
from app.config import settings
class State(TypedDict,total=False):
    question:str; conversation_id:str; top_k:int; sources:list; graph_data:list; answer:str; confidence:float; status:str
async def retrieve(s):
    hits=retriever.search(s['question'],s.get('top_k',8)); return {'sources':[{'source_id':c.source_id,'title':c.title,'page':c.page,'section':c.section,'score':score,'excerpt':c.text[:450],'text':c.text} for c,score in hits]}
def graph(s): return {'graph_data':graph_metrics() if 'gross margin' in s['question'].lower() else []}
async def answer(s):
    refs='\n\n'.join(f"[{i+1}] {x['title']} p.{x['page']}: {x['text']}" for i,x in enumerate(s.get('sources',[])))
    prompt=f"Question: {s['question']}\nPrior conversation: {memory[s['conversation_id']][-6:]}\nKnowledge graph: {s.get('graph_data',[])}\nEvidence:\n{refs}\nUse only evidence, cite [n], separate facts/calculations/inference, and say when evidence is insufficient. Do not provide personalized investment advice."
    text=await LLM().complete(prompt); memory[s['conversation_id']]+=[{'role':'user','content':s['question']},{'role':'assistant','content':text}]; _trim_memory(s['conversation_id'])
    scores=[x['score'] for x in s.get('sources',[])]; confidence=max(0,min(1,sum(scores)/len(scores))) if scores else 0
    return {'answer':text,'confidence':confidence,'status':'needs_approval' if confidence<settings().human_approval_threshold else 'completed'}
g=StateGraph(State); g.add_node('retrieve',retrieve);g.add_node('graph',graph);g.add_node('answer',answer);g.add_edge(START,'retrieve');g.add_edge('retrieve','graph');g.add_edge('graph','answer');g.add_edge('answer',END);workflow=g.compile()
