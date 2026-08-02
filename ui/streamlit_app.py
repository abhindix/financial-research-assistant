import os,uuid,requests,pandas as pd,streamlit as st

def resolve_api_base():
    candidates=[os.getenv('API_URL'), 'http://127.0.0.1:8000/api/v1', 'http://127.0.0.1:8001/api/v1']
    for candidate in candidates:
        if not candidate:
            continue
        try:
            r=requests.get(f'{candidate}/health',timeout=1.5)
            if r.ok:
                return candidate
        except Exception:
            continue
    return candidates[0] or 'http://127.0.0.1:8000/api/v1'

API=st.session_state.get('api_base') or resolve_api_base()
st.session_state['api_base']=API

st.set_page_config(page_title='Financial Research Copilot',layout='wide');st.title('Enterprise Financial Research Assistant');st.caption('Hybrid RAG + Knowledge Graph • citations • memory • human review')
with st.sidebar:
    st.text_input('API base',API,key='api_base')
    f=st.file_uploader('Upload SEC filing, transcript, research PDF',type=['pdf'])
    if f and st.button('Index document'):
        r=requests.post(f'{st.session_state.api_base}/documents',files={'file':(f.name,f.getvalue(),'application/pdf')},timeout=300);st.write(r.json() if r.ok else r.text)
    cid=st.text_input('Conversation ID',str(uuid.uuid4())[:8])
q=st.text_area('Research question',placeholder='Which semiconductor companies have the highest gross margin over the last five years?')
if st.button('Research',type='primary') and q:
    with st.spinner('Retrieving, querying graph, and synthesizing...'):
        r=requests.post(f'{st.session_state.api_base}/ask',json={'question':q,'conversation_id':cid,'top_k':8},timeout=300)
    if not r.ok:st.error(r.text)
    else:
        d=r.json();st.subheader('Answer');st.markdown(d['answer']);a,b=st.columns(2);a.metric('Confidence',f"{d['confidence']:.0%}");b.metric('Review status',d['status'])
        if d.get('sources'):st.subheader('Sources');st.dataframe(pd.DataFrame(d['sources']),use_container_width=True)
        if d.get('graph_data'):st.subheader('Knowledge graph comparison');st.dataframe(pd.DataFrame(d['graph_data']),use_container_width=True)
