"""Frontend extraction contracts, with synthetic input and no network/GTK session."""
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
import urllib.parse
from unittest.mock import MagicMock, patch

YOUTUBE = Path(__file__).resolve().parents[1] / 'app'
sys.path.insert(0, str(YOUTUBE))
import youtube_api as api
import youtube_server as server


class YouTubeBoundaryTests(unittest.TestCase):
    def request(self, action, data=None, origin='http://127.0.0.1:1234', path=None):
        handler = object.__new__(server.make_handler('synthetic-token'))
        raw = json.dumps(data or {}).encode()
        handler.path = path or '/synthetic-token/' + action
        handler.headers = {'Origin': origin, 'Content-Length': str(len(raw))}
        handler.rfile = io.BytesIO(raw)
        handler.server = SimpleNamespace(server_port=1234, cache={})
        replies = []
        handler.reply = lambda *args: replies.append(args)
        handler.do_POST()
        return replies[-1], handler

    def test_loopback_origin_and_token_required_before_api(self):
        with patch.object(server, 'search') as search:
            self.assertEqual(self.request('search', {'query': 'test'}, origin='https://example.invalid')[0][0], 403)
            self.assertEqual(self.request('search', {'query': 'test'}, path='/wrong/search')[0][0], 403)
            search.assert_not_called()

    def test_search_and_missing_key_contract(self):
        items = [{'id': 'abcdefghijk', 'title': 'Synthetic'}]
        with patch.object(server, 'search', return_value=items) as search:
            reply, handler = self.request('search', {'query': 'test'})
            self.assertEqual(reply, (200, {'items': items}))
            self.assertEqual(handler.server.cache[('test', 'videos')][1], items)
            search.assert_called_once_with('test', 'videos')
        with patch.object(server, 'search', side_effect=api.MissingAPIKey('Configure')):
            reply, _ = self.request('search', {'query': 'test'})
            self.assertEqual(reply, (400, {'error': 'Configure', 'code': 'key_required'}))

    def test_search_modes_are_validated_and_cached_separately(self):
        items = [{'id': 'abcdefghijk', 'title': 'Synthetic'}]
        for mode in ('', None, [], {}, 'short', 'SHORT', 'livestream'):
            self.assertEqual(self.request('search', {'query': 'test', 'mode': mode})[0][0], 400)
        self.assertEqual(self.request('search', {'query': '   '})[0][0], 400)
        self.assertEqual(self.request('search', {'query': 'bad\nquery'})[0][0], 400)
        with patch.object(server, 'search', return_value=items) as search:
            reply, handler = self.request('search', {'query': '  test  ', 'mode': 'shorts'})
            self.assertEqual(reply, (200, {'items': items}))
            self.assertIn(('test', 'shorts'), handler.server.cache)
            search.assert_called_once_with('test', 'shorts')
        with patch.object(server, 'search', return_value=items) as search:
            reply, handler = self.request('search', {'query': 'live test', 'mode': 'live'})
            self.assertEqual(reply, (200, {'items': items}))
            self.assertIn(('live test', 'live'), handler.server.cache)
            search.assert_called_once_with('live test', 'live')

    def test_api_maps_search_modes_to_official_filters(self):
        response = MagicMock()
        response.read.return_value = b'{"items":[]}'
        response.__enter__.return_value = response
        with patch.object(api, 'read_key', return_value='synthetic-key'), patch.object(api.urllib.request, 'urlopen', return_value=response) as urlopen:
            api.search('test', 'videos')
            regular = urllib.parse.parse_qs(urllib.parse.urlparse(urlopen.call_args.args[0]).query)
            api.search('test', 'shorts')
            shorts = urllib.parse.parse_qs(urllib.parse.urlparse(urlopen.call_args.args[0]).query)
            api.search('test', 'live')
            live = urllib.parse.parse_qs(urllib.parse.urlparse(urlopen.call_args.args[0]).query)
        self.assertNotIn('videoDuration', regular)
        self.assertNotIn('eventType', regular)
        self.assertEqual(shorts.get('videoDuration'), ['short'])
        self.assertNotIn('eventType', shorts)
        self.assertEqual(live.get('eventType'), ['live'])
        self.assertNotIn('videoDuration', live)
        for options in (regular, shorts, live):
            self.assertEqual(options.get('videoEmbeddable'), ['true'])
        with self.assertRaises(ValueError):
            api.search('test', 'short')

    def test_invalid_requests_and_comment_cache(self):
        self.assertEqual(self.request('search', {'query': ''})[0][0], 400)
        self.assertEqual(self.request('comments', {'video': []})[0][0], 400)
        self.assertEqual(self.request('unknown')[0][0], 404)
        with patch.object(server, 'comments', return_value={'items': [], 'nextPage': ''}) as comments:
            reply, handler = self.request('comments', {'video': 'abcdefghijk'})
            self.assertEqual(reply[0], 200)
            self.assertIn(('abcdefghijk', ''), handler.server.comment_cache)
            comments.assert_called_once_with('abcdefghijk', '')

    def test_document_get_keeps_token_boundary(self):
        handler = object.__new__(server.make_handler('synthetic-token'))
        replies = []
        handler.reply = lambda *args: replies.append(args)
        handler.path = '/index.html'
        handler.do_GET()
        self.assertEqual(replies[-1], (404, {}))
        handler.path = '/synthetic-token/'
        handler.do_GET()
        self.assertEqual(replies[-1][0], 200)
        self.assertEqual(replies[-1][2], 'text/html')
        self.assertIn(b'<title>YouTube</title>', replies[-1][1])

    def test_local_key_permissions_and_validation(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(api, 'CONFIG', Path(folder) / 'youtube.json'):
            self.assertEqual(api.read_key(), '')
            with self.assertRaises(ValueError):
                api.save_key('invalid')
            key = 'synthetic_key_' + 'x' * 25
            api.save_key(key)
            self.assertEqual(api.read_key(), key)
            self.assertEqual(api.CONFIG.stat().st_mode & 0o777, 0o600)
            api.CONFIG.unlink()
            target = Path(folder) / 'target'
            target.write_text(json.dumps({'key': key}))
            api.CONFIG.symlink_to(target)
            self.assertEqual(api.read_key(), '')


if __name__ == '__main__':
    unittest.main()
