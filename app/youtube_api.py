#!/usr/bin/python3
"""YouTube Data API access, local key and suggestion cache."""
import html
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))/'orbitz-youtube-desktop'/'youtube.json'


class MissingAPIKey(ValueError):
    pass


def read_key():
    try:
        fd=os.open(CONFIG,os.O_RDONLY|os.O_NOFOLLOW)
        with os.fdopen(fd) as stream:
            return json.loads(stream.read(4096)).get('key','')
    except (OSError,ValueError):
        return ''


def save_key(key):
    if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_-]{20,200}',key):
        raise ValueError('Formato da chave inválido.')
    CONFIG.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(CONFIG,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:
        os.fchmod(stream.fileno(),0o600)
        json.dump({'key':key},stream)


def search(query=None, mode='videos'):
    if not isinstance(mode,str) or mode not in ('videos','shorts','live'):
        raise ValueError('Filtro de busca inválido.')
    if query is not None and (not isinstance(query,str) or not 0<len(query.strip())<=300 or any(ord(char)<32 for char in query)):
        raise ValueError('Busca inválida.')
    key=read_key()
    if not key: raise MissingAPIKey('Configure uma chave da API ou cole um link do YouTube.')
    options=dict(part='snippet',type='video',maxResults=8,videoEmbeddable='true',key=key)
    if query is None:
        options.update(regionCode='BR',relevanceLanguage='pt',order='viewCount',
            publishedAfter=(datetime.now(timezone.utc)-timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ'))
    else:
        options['q']=query
        # The API's `short` bucket means videos under four minutes. It is the
        # closest official search filter; YouTube does not expose a Shorts-only
        # search parameter, so some returned videos may not be classified as Shorts.
        if mode=='shorts':options['videoDuration']='short'
        elif mode=='live':options['eventType']='live'
    params=urllib.parse.urlencode(options)
    endpoint='search'
    try:
        with urllib.request.urlopen('https://www.googleapis.com/youtube/v3/'+endpoint+'?'+params,timeout=10) as response:
            raw=response.read(262145)
        if len(raw)>262144: raise ValueError('Resposta muito grande.')
        data=json.loads(raw)
    except urllib.error.HTTPError as error:
        if error.code==403: raise ValueError('Consulta recusada: confira a chave, a ativação da API e a quota diária.') from None
        raise ValueError('O YouTube não conseguiu concluir a busca.') from None
    except (OSError,ValueError):
        raise ValueError('Não foi possível consultar o YouTube. Verifique a conexão.') from None
    items=[]
    for item in data.get('items',[])[:16]:
        identity=item.get('id',{}).get('videoId','')
        if not re.fullmatch(r'[\w-]{11}',identity):continue
        snippet=item.get('snippet',{})
        items.append(dict(id=identity,title=html.unescape(snippet.get('title',''))[:300],channel=html.unescape(snippet.get('channelTitle',''))[:200],thumbnail='https://i.ytimg.com/vi/'+identity+'/default.jpg'))
        if len(items)>=8:break
    return items


def recommendations():
    cache_path=Path(os.environ.get('XDG_CACHE_HOME',Path.home()/'.cache'))/'orbitz-youtube-desktop'/'youtube-suggestions.json'
    try:
        cached=json.loads(cache_path.read_text())
        if 0<=time.time()-cached['time']<21600 and isinstance(cached['items'],list) and cached['items']:
            return cached['items']
    except (OSError,ValueError,KeyError,TypeError):
        pass
    items=search()
    try:
        cache_path.parent.mkdir(parents=True,exist_ok=True)
        temporary=cache_path.with_name('youtube-suggestions-'+secrets.token_hex(8)+'.tmp')
        temporary.write_text(json.dumps({'time':time.time(),'items':items}))
        os.replace(temporary,cache_path)
    except OSError:
        pass
    return items


def comments(video, page=''):
    if not isinstance(video,str) or not re.fullmatch(r'[A-Za-z0-9_-]{11}',video):
        raise ValueError('Selecione um vídeo válido para ver os comentários.')
    if not isinstance(page,str) or len(page)>1024:
        raise ValueError('Página de comentários inválida.')
    key=read_key()
    if not key:raise MissingAPIKey('Configure uma chave da API para carregar os comentários.')
    options=dict(part='snippet',videoId=video,maxResults=20,order='relevance',textFormat='plainText',key=key)
    if page:options['pageToken']=page
    try:
        with urllib.request.urlopen('https://www.googleapis.com/youtube/v3/commentThreads?'+urllib.parse.urlencode(options),timeout=10) as response:
            raw=response.read(1048577)
        if len(raw)>1048576:raise ValueError('Resposta de comentários muito grande.')
        data=json.loads(raw)
    except urllib.error.HTTPError as error:
        try:reasons={item.get('reason') for item in json.loads(error.read(65536)).get('error',{}).get('errors',[])}
        except (OSError,ValueError,TypeError,AttributeError):reasons=set()
        if 'commentsDisabled' in reasons:raise ValueError('Os comentários estão desativados neste vídeo.') from None
        if reasons & {'quotaExceeded','dailyLimitExceeded'}:
            raise ValueError('A quota para carregar comentários foi excedida. A busca e a reprodução podem continuar funcionando.') from None
        if error.code==404:raise ValueError('Este vídeo não está disponível para consulta de comentários.') from None
        raise ValueError('O YouTube não permitiu carregar os comentários. Tente novamente mais tarde.') from None
    except (OSError,ValueError):
        raise ValueError('Não foi possível carregar os comentários. Verifique a conexão.') from None
    items=[]
    for item in data.get('items',[])[:20]:
        snippet=item.get('snippet',{}).get('topLevelComment',{}).get('snippet',{})
        items.append(dict(author=snippet.get('authorDisplayName','')[:200],text=snippet.get('textDisplay','')[:20000],
            likes=snippet.get('likeCount',0),published=snippet.get('publishedAt','')))
    return dict(items=items,nextPage=data.get('nextPageToken',''))
