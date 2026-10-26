"""Hosted support-demo core; no local accounts, databases, or Ollama access."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import threading
import time

ROOT = Path(__file__).resolve().parent.parent
MODEL = 'openai/gpt-oss-20b'
GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'
OWNERSHIP = {'alex':('DEMO-1001','DEMO-1002'), 'sam':('DEMO-1003',)}


class ProviderError(RuntimeError):
    pass


def groq_classify(question, api_key):
    import requests
    from .agent import routing_payload, SCHEMA
    if not api_key:
        raise ProviderError('AI is not configured. Direct order lookup and policy browsing remain available.')
    try:
        response = requests.post(GROQ_URL, headers={'Authorization':'Bearer '+api_key},
            json={'model':MODEL, 'messages':routing_payload(question)['messages'], 'temperature':0,
                  'max_completion_tokens':1024, 'reasoning_effort':'low',
                  'response_format':{'type':'json_schema','json_schema':{'name':'support_route','strict':True,'schema':SCHEMA}}}, timeout=(5,30))
        if response.status_code == 429:
            raise ProviderError('The AI provider quota is exhausted. Please try later; no paid fallback is used.')
        if response.status_code != 200:
            raise ProviderError('The AI provider is unavailable or access was denied. No prediction was produced.')
        body = response.json()
        result = json.loads(body['choices'][0]['message']['content'])
        if (not isinstance(result,dict) or set(result) != {'intent','order_id'}
                or result['intent'] not in SCHEMA['properties']['intent']['enum'] or not isinstance(result['order_id'],str)):
            raise ValueError('Invalid decision')
        return result
    except ProviderError:
        raise
    except (requests.RequestException, ValueError, KeyError, TypeError, IndexError):
        raise ProviderError('The AI provider failed or returned an invalid response. No answer was invented.') from None


class Budget:
    """Process-local call cap, not an account billing control or durable limiter."""
    def __init__(self):
        self.lock=threading.Lock(); self.day=''; self.count=0; self.last=0.0

    def reserve(self):
        with self.lock:
            today=datetime.now(timezone.utc).date().isoformat()
            if today != self.day: self.day=today; self.count=0
            now=time.monotonic()
            if self.count >= 100 or now-self.last < 3:
                raise ProviderError('The shared demo request limit has been reached. Please try later.')
            self.count+=1; self.last=now


class PolicySearch:
    def __init__(self):
        from fastembed import TextEmbedding
        from huggingface_hub import snapshot_download
        import onnxruntime
        onnxruntime.disable_telemetry_events()
        model_path=snapshot_download('Qdrant/all-MiniLM-L6-v2-onnx',
            revision='d13954661f83248295ba75c1ed411eef3b7b936e',cache_dir=str(ROOT/'.cache/fastembed'),
            allow_patterns=['model.onnx','config.json','tokenizer.json','tokenizer_config.json','special_tokens_map.json'])
        self.policies=json.loads((ROOT/'data/policies.json').read_text())
        self.model=TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2',threads=2,
                                 cache_dir=str(ROOT/'.cache/fastembed'),providers=['CPUExecutionProvider'], specific_model_path=model_path)
        self.vectors=list(self.model.embed([p['title']+'. '+p['text'] for p in self.policies]))
        self.lock=threading.Lock()

    def retrieve(self, question):
        from .embeddings import cosine
        tokens=set(re.findall('[a-z]+',question.lower()))
        matches=[p for p in self.policies if tokens.intersection(p['keywords'])]
        if matches: return matches,'keyword'
        with self.lock: vector=list(self.model.embed([question]))[0]
        ranked=sorted([(cosine(vector,v),p) for v,p in zip(self.vectors,self.policies)],key=lambda pair:pair[0],reverse=True)
        if ranked[0][0] >= .35 and ranked[0][0]-ranked[1][0] >= .06:
            return [ranked[0][1]],'semantic_fastembed'
        return [],'semantic_fastembed'


class DemoState:
    """One visitor's fictional workflow. Role selection is a simulation, not login."""
    def __init__(self):
        self.orders={o['order_id']:o for o in json.loads((ROOT/'data/orders.json').read_text())}
        self.requests=[]; self.audit=[]

    def lookup(self, username, order_id):
        order_id=order_id.strip().upper()
        if order_id not in OWNERSHIP.get(username,()): return None
        return copy.deepcopy(self.orders.get(order_id))

    def submit(self, username, order_id):
        order=self.lookup(username,order_id)
        if not order: return 'No accessible demo order was found.'
        if order['status'] != 'processing': return 'Only processing orders qualify for review.'
        if any(r['order_id']==order['order_id'] and r['state']=='pending' for r in self.requests):
            return 'This order already has a pending request.'
        if len(self.requests)>=25: return 'Session request limit reached. Reset the demo to continue.'
        row={'id':len(self.requests)+1,'order_id':order['order_id'],'state':'pending','customer':username}
        self.requests.append(row);self.audit.append({'request_id':row['id'],'event':'submitted','actor':username})
        return 'Submitted for review. The order is not cancelled.'

    def decide(self, request_id, action):
        if action not in ('approve','reject'): return 'Invalid decision.'
        row=next((r for r in self.requests if r['id']==request_id),None)
        if not row or row['state']!='pending': return 'Request is missing or already reviewed.'
        if action=='approve' and self.orders[row['order_id']]['status']!='processing':
            row['state']='blocked'
        else:
            row['state']='approved' if action=='approve' else 'rejected'
            if action=='approve': self.orders[row['order_id']]['status']='cancelled'
        self.audit.append({'request_id':request_id,'event':row['state'],'actor':'simulated reviewer'})
        return 'Request '+row['state']+'.'


def answer(question, username, state, classify, search):
    question=question.strip()
    if not question or len(question)>1000: return {'outcome':'invalid_input','message':'Enter a question of 1–1000 characters.'}
    decision=classify(question)
    intent=decision['intent']
    messages={'unsupported':'AI chat cannot perform refunds, cancellations, or address changes. Use the separate fictional review simulator.',
              'policy_missing':'The demo documents do not cover that policy. I cannot verify an answer.',
              'clarification':'Ask one question at a time: one order status or one store policy.'}
    if intent in messages: return {'outcome':intent,'message':messages[intent]}
    if intent=='policy':
        matches,method=search.retrieve(question)
        return {'outcome':'policy' if matches else 'policy_not_found','message':'Relevant source passages; these do not approve an individual action.' if matches else 'No sufficiently clear matching policy was found.',
                'citations':matches,'retrieval_method':method}
    ids=set(re.findall(r'\bDEMO-\d+\b',question.upper()))
    if len(ids)!=1: return {'outcome':'clarification','message':'Include exactly one demo order ID.'}
    order_id=decision['order_id'].strip().upper()
    if order_id not in ids: return {'outcome':'invalid_decision','message':'The model did not reliably identify the supplied order ID.'}
    order=state.lookup(username,order_id)
    if not order: return {'outcome':'not_found','message':'No accessible demo order was found.'}
    message=f"Your order {order_id} ({order['item']}) is {order['status']}."
    if order['tracking_id']: message+=' Demo tracking reference: '+order['tracking_id']+'.'
    return {'outcome':'found','message':message,'order':order,'source':'demo-orders:'+order_id}
