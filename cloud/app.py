"""Public, fictional support sandbox. Does not expose the local Flask accounts."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import streamlit as st
from resolveai.hosted import DemoState, OWNERSHIP, Budget, PolicySearch, ProviderError, groq_classify, answer, ROOT, MODEL
import json

st.set_page_config(page_title='ResolveAI — Support demo',page_icon='💬',layout='centered')
st.title('ResolveAI')
st.caption('Fictional order support · public research demo')
st.info('Demo identities and reviewer roles below are simulations, not authenticated accounts. All actions affect only your current browser session. No real orders or payments exist.')
if 'demo' not in st.session_state: st.session_state.demo=DemoState()
if 'ai_calls' not in st.session_state: st.session_state.ai_calls=0

@st.cache_resource
def budget(): return Budget()

@st.cache_resource(show_spinner='Loading local CPU policy-search model…')
def search(): return PolicySearch()

class LazySearch:
    def retrieve(self, question):
        return search().retrieve(question)

def clear_result(): st.session_state.pop('answer',None)
username=st.radio('Simulated customer',['alex','sam'],horizontal=True,on_change=clear_result)
state=st.session_state.demo
st.caption('Accessible fictional orders: '+', '.join(OWNERSHIP[username]))

try:
    key=st.secrets.get('GROQ_API_KEY','')
    free_confirmed=st.secrets.get('GROQ_FREE_PLAN_CONFIRMED',False) is True
except Exception:
    key='';free_confirmed=False
ready=bool(key and free_confirmed)
st.caption('AI routing: Groq / '+MODEL+'. Policy embeddings: local CPU FastEmbed. No Ollama connection required.')
if not ready:
    st.warning('AI routing is not configured. The order form, policy reader, and review simulation still work without AI. The owner must configure a free-plan Groq key privately.')

with st.form('ask'):
    question=st.text_input('Ask about an order or policy',max_chars=1000,placeholder='Where is my order DEMO-1001?')
    ask=st.form_submit_button('Ask ResolveAI',disabled=not ready)
if ask:
    if not question.strip(): st.warning('Enter a question first.')
    elif st.session_state.ai_calls>=20: st.warning('This session has reached its 20-call limit. Direct lookup remains available.')
    else:
        try:
            budget().reserve()
            st.session_state.ai_calls+=1
            with st.spinner('Routing your question…'):
                result=answer(question,username,state,lambda q:groq_classify(q,key), LazySearch())
            st.session_state.answer=result
        except ProviderError as error: st.session_state.answer={'message':str(error)}
        except Exception: st.session_state.answer={'message':'The request or local search failed. No answer was invented; use direct lookup or the policy reader.'}
if 'answer' in st.session_state:
    result=st.session_state.answer
    st.subheader('Support response');st.write(result['message'])
    if result.get('source'): st.caption('Source: '+result['source'])
    for policy in result.get('citations',[]):
        st.markdown('**Source: '+policy['title']+'**');st.write(policy['text'])
    if result.get('retrieval_method'):st.caption('Search method: '+result['retrieval_method'])

with st.form('lookup'):
    order_id=st.text_input('Order ID',max_chars=40)
    lookup=st.form_submit_button('Check order — direct lookup, no AI')
if lookup:
    order=state.lookup(username,order_id)
    if order:
        st.success(f"{order['order_id']} · {order['item']} · {order['status']}")
        if order['tracking_id']:st.caption('Demo tracking reference: '+order['tracking_id'])
    else:st.warning('No accessible demo order was found.')

with st.expander('Read source policies — no AI required'):
    for policy in json.loads((ROOT/'data/policies.json').read_text()):
        st.subheader(policy['title']);st.write(policy['text'])

with st.expander('Cancellation review simulator — current session only'):
    st.write('Submitting creates a pending request. Only explicit simulated reviewer approval changes an eligible processing order. Selecting reviewer mode is not real authorization.')
    with st.form('cancel'):
        cancel_id=st.text_input('Order ID to submit',max_chars=40)
        submit=st.form_submit_button('Submit for review')
    if submit:
        st.write(state.submit(username,cancel_id));clear_result()
    reviewer=st.checkbox('Simulate reviewer role')
    for row in state.requests:
        st.write(f"Request #{row['id']} · {row['order_id']} · {row['state']}")
        if reviewer and row['state']=='pending':
            left,right=st.columns(2)
            for action,column in [('approve',left),('reject',right)]:
                if column.button(action.title(),key=f"{action}-{row['id']}"):
                    state.decide(row['id'],action);clear_result();st.rerun()
    if state.audit: st.write('Session audit events');st.json(state.audit)
    if st.button('Reset my fictional session'):
        st.session_state.demo=DemoState();clear_result();st.rerun()

st.markdown('[Source code and local architecture](https://github.com/rmudadla629/resolveai)')
st.caption('Use fictional data only. Your question is sent to Groq for routing; no real customer records are involved. Policy excerpts and order facts come from Python-controlled sources. No paid fallback. Free quotas and hosting availability apply. This public simulation differs from the password-protected local app; session state can disappear on disconnect or restart.')
