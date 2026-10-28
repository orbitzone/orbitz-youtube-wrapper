"""Token-protected loopback HTTP boundary for the YouTube window."""
from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path
import time
from youtube_api import MissingAPIKey,save_key,search,recommendations,comments
from runner_score import read_best_score,save_best_score
from ui_language import ui

BASE = Path(__file__).resolve().parent

def make_handler(token):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def reply(self,status,body,kind='application/json'):
            raw=body if isinstance(body,bytes) else json.dumps(body,ensure_ascii=False).encode()
            self.send_response(status);self.send_header('Content-Type',kind+'; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('Referrer-Policy','strict-origin-when-cross-origin');self.end_headers();self.wfile.write(raw)
        def do_GET(self):
            if self.path!='/'+token+'/':self.reply(404,{});return
            self.reply(200,(BASE/'index.html').read_bytes(),'text/html')
        def do_POST(self):
            action=self.path.removeprefix('/'+token+'/')
            origin='http://127.0.0.1:'+str(self.server.server_port)
            if not self.path.startswith('/'+token+'/') or self.headers.get('Origin')!=origin:
                self.reply(403,{'error':'Origem inválida.'});return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=4096:raise ValueError('Requisição inválida.')
                data=json.loads(self.rfile.read(length))
                if not isinstance(data,dict):raise ValueError('Requisição inválida.')
                if action=='runner-score':
                    best=save_best_score(data['score']) if 'score' in data else read_best_score()
                    self.reply(200,{'best':best})
                elif action=='key':
                    save_key(data.get('key'));self.server.cache.clear();self.reply(200,{'saved':True})
                elif action=='language':
                    locale=data.get('locale')
                    if locale not in ('pt-BR','en-US'):raise ValueError('Idioma inválido.')
                    applied_locale=ui.set_locale(locale);self.reply(200,{'saved':True,'locale':applied_locale})
                elif action in ('window-state','open-external','copy-link'):
                    callback=getattr(self.server,'ui_actions',{}).get(action)
                    if callback is None:raise ValueError('Ação indisponível.')
                    callback(data)
                    self.reply(200,{'ok':True})
                elif action=='recommendations':
                    cache=self.server.cache.get(None)
                    if not cache or time.time()-cache[0]>900:
                        cache=(time.time(),recommendations());self.server.cache[None]=cache
                    self.reply(200,{'items':cache[1]})
                elif action=='comments':
                    video=data.get('video');page=data.get('page','')
                    # Validate before using user input as a cache key.
                    if not isinstance(video,str) or not isinstance(page,str):raise ValueError('Consulta de comentários inválida.')
                    cache_store=getattr(self.server,'comment_cache',{})
                    identity=(video,page);cached=cache_store.get(identity)
                    if not cached or time.time()-cached[0]>300:
                        cached=(time.time(),comments(video,page))
                        if len(cache_store)>=30:cache_store.clear()
                        cache_store[identity]=cached
                    self.server.comment_cache=cache_store
                    self.reply(200,cached[1])
                elif action=='search':
                    query=data.get('query')
                    mode=data.get('mode','videos')
                    if not isinstance(query,str) or not 0<len(query.strip())<=300 or any(ord(char)<32 for char in query):raise ValueError('Busca inválida.')
                    if not isinstance(mode,str) or mode not in ('videos','shorts','live','podcasts'):raise ValueError('Filtro de busca inválido.')
                    query=query.strip()
                    identity=(query,mode)
                    cache=self.server.cache.get(identity)
                    if not cache or time.time()-cache[0]>300:
                        cache=(time.time(),search(query,mode))
                        # Bound the in-memory cache while keeping distinct results
                        # for each query/mode pair and the recommendations entry.
                        self.server.cache={k:v for k,v in self.server.cache.items()
                            if k is None or (isinstance(k,tuple) and len(k)==2 and time.time()-v[0]<=300)}
                        if len(self.server.cache)>=40:
                            self.server.cache={k:v for k,v in self.server.cache.items() if k is None}
                        self.server.cache[identity]=cache
                    self.reply(200,{'items':cache[1]})
                else:self.reply(404,{})
            except (ValueError,TypeError,OSError,RuntimeError):
                import sys
                error=sys.exc_info()[1]
                self.reply(400,{'error':str(error)[:250],'code':'key_required' if isinstance(error,MissingAPIKey) else 'request_failed'})
    return Handler
