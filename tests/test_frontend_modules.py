"""Frontend extraction contracts, with synthetic input and no network/GTK session."""
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
import urllib.parse
from unittest.mock import MagicMock, patch

YOUTUBE = Path(__file__).resolve().parents[1] / 'app'
sys.path.insert(0, str(YOUTUBE))
import youtube_api as api
import youtube_server as server
import runner_score


class YouTubeBoundaryTests(unittest.TestCase):
    def request(self, action, data=None, origin='http://127.0.0.1:1234', path=None):
        handler = object.__new__(server.make_handler('synthetic-token'))
        raw = json.dumps(data if data is not None else {}).encode()
        handler.path = path or '/synthetic-token/' + action
        handler.headers = {'Origin': origin, 'Content-Length': str(len(raw))}
        handler.rfile = io.BytesIO(raw)
        handler.server = SimpleNamespace(server_port=1234, cache={}, ui_actions={})
        replies = []
        handler.reply = lambda *args: replies.append(args)
        handler.do_POST()
        return replies[-1], handler

    def test_loopback_origin_and_token_required_before_api(self):
        with patch.object(server, 'search') as search:
            self.assertEqual(self.request('search', {'query': 'test'}, origin='https://example.invalid')[0][0], 403)
            self.assertEqual(self.request('search', {'query': 'test'}, path='/wrong/search')[0][0], 403)
            search.assert_not_called()

    def test_json_body_must_be_an_object_before_dispatch(self):
        for data in (None, [], 'text', 4):
            reply, _ = self.request('search', data)
            self.assertEqual(reply[0], 400)

    def test_native_ui_actions_are_size_and_origin_bounded(self):
        called = []
        handler = object.__new__(server.make_handler('synthetic-token'))
        raw = json.dumps({'state': 'player'}).encode()
        handler.path = '/synthetic-token/window-state'
        handler.headers = {'Origin': 'http://127.0.0.1:1234', 'Content-Length': str(len(raw))}
        handler.rfile = io.BytesIO(raw)
        handler.server = SimpleNamespace(server_port=1234, cache={}, ui_actions={'window-state': called.append})
        replies = []
        handler.reply = lambda *args: replies.append(args)
        handler.do_POST()
        self.assertEqual(replies[-1], (200, {'ok': True}))
        self.assertEqual(called, [{'state': 'player'}])
        handler.headers['Content-Length'] = '4097'
        handler.do_POST()
        self.assertEqual(replies[-1][0], 400)

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
        with patch.object(server, 'search', return_value=items) as search:
            reply, handler = self.request('search', {'query': 'music', 'mode': 'podcasts'})
            self.assertEqual(reply, (200, {'items': items}))
            self.assertIn(('music', 'podcasts'), handler.server.cache)
            search.assert_called_once_with('music', 'podcasts')

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
            api.search('test', 'podcasts')
            podcasts = urllib.parse.parse_qs(urllib.parse.urlparse(urlopen.call_args.args[0]).query)
        self.assertNotIn('videoDuration', regular)
        self.assertNotIn('eventType', regular)
        self.assertEqual(shorts.get('videoDuration'), ['short'])
        self.assertNotIn('eventType', shorts)
        self.assertEqual(live.get('eventType'), ['live'])
        self.assertNotIn('videoDuration', live)
        self.assertEqual(podcasts.get('q'), ['podcast test'])
        for options in (regular, shorts, live, podcasts):
            self.assertEqual(options.get('videoEmbeddable'), ['true'])
        with self.assertRaises(ValueError):
            api.search('test', 'short')

    def test_language_setting_accepts_only_supported_locales(self):
        with patch.object(server.ui, 'set_locale', return_value='en-US') as set_locale:
            reply, _ = self.request('language', {'locale': 'en-US'})
            self.assertEqual(reply, (200, {'saved': True, 'locale': 'en-US'}))
            set_locale.assert_called_once_with('en-US')
            self.assertEqual(self.request('language', {'locale': 'fr-FR'})[0][0], 400)

    def test_language_change_waits_for_main_thread_settings_write(self):
        ui = server.ui
        previous_settings = ui._settings
        previous_locale = ui.get_locale()
        callbacks = []
        settings = SimpleNamespace(value='pt-BR')
        def save_string(key, value):
            self.assertEqual(key, 'ui-language')
            settings.value = value
            ui.refresh(value)
        settings.set_string = save_string
        fake_glib = SimpleNamespace(idle_add=lambda callback: callbacks.append(callback) or 17,
                                    source_remove=lambda source: None)
        fake_repository = SimpleNamespace(GLib=fake_glib)
        fake_gi = SimpleNamespace(repository=fake_repository)
        with patch.dict(sys.modules, {'gi': fake_gi, 'gi.repository': fake_repository}):
            ui._settings = settings
            result = []
            worker = threading.Thread(target=lambda: result.append(self.request('language', {'locale': 'en-US'})[0]))
            try:
                worker.start()
                deadline = time.monotonic() + 2
                while not callbacks and time.monotonic() < deadline:
                    time.sleep(0.001)
                self.assertTrue(callbacks, 'worker did not schedule the GTK main-thread update')
                callbacks.pop(0)()
                worker.join(2)
                self.assertFalse(worker.is_alive(), 'language request did not finish after the main-thread update')
                self.assertEqual(result, [(200, {'saved': True, 'locale': 'en-US'})])
                self.assertEqual(settings.value, 'en-US')
            finally:
                if worker.is_alive():
                    worker.join(2)
                ui._settings = previous_settings
                ui.refresh(previous_locale)

    def test_invalid_requests_and_comment_cache(self):
        self.assertEqual(self.request('search', {'query': ''})[0][0], 400)
        self.assertEqual(self.request('comments', {'video': []})[0][0], 400)
        self.assertEqual(self.request('unknown')[0][0], 404)
        with patch.object(server, 'comments', return_value={'items': [], 'nextPage': ''}) as comments:
            reply, handler = self.request('comments', {'video': 'abcdefghijk'})
            self.assertEqual(reply[0], 200)
            self.assertIn(('abcdefghijk', ''), handler.server.comment_cache)
            comments.assert_called_once_with('abcdefghijk', '')

    def test_runner_score_endpoint_reads_and_saves_valid_record(self):
        with patch.object(server, 'read_best_score', return_value=640), patch.object(server, 'save_best_score', return_value=900) as save:
            self.assertEqual(self.request('runner-score')[0], (200, {'best': 640}))
            self.assertEqual(self.request('runner-score', {'score': 900})[0], (200, {'best': 900}))
            save.assert_called_once_with(900)
        self.assertEqual(self.request('runner-score', {'score': -1})[0][0], 400)

    def test_runner_best_score_persists_atomically_and_never_decreases(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(runner_score, 'SCORE_FILE', Path(folder) / 'config' / 'runner.json'):
            self.assertEqual(runner_score.read_best_score(), 0)
            self.assertEqual(runner_score.save_best_score(1376), 1376)
            self.assertEqual(runner_score.read_best_score(), 1376)
            self.assertEqual(runner_score.save_best_score(42), 1376)
            self.assertEqual(runner_score.SCORE_FILE.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(ValueError):
                runner_score.save_best_score(True)
            with self.assertRaises(ValueError):
                runner_score.save_best_score(2_147_483_648)

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
        self.assertIn(b'<title>YouTube Wrapper - By Orbitz</title>', replies[-1][1])

    def test_local_key_permissions_and_validation(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(api, 'CONFIG', Path(folder) / 'new' / 'youtube.json'), patch.object(api, 'LEGACY_CONFIG', Path(folder) / 'old' / 'youtube.json'):
            self.assertEqual(api.read_key(), '')
            api.LEGACY_CONFIG.parent.mkdir()
            api.LEGACY_CONFIG.write_text(json.dumps({'key': 'legacy_key_' + 'x' * 25}))
            self.assertEqual(api.read_key(), 'legacy_key_' + 'x' * 25)
            api.CONFIG.parent.mkdir(parents=True)
            for malformed in ('[]', 'null', '"not-an-object"'):
                api.CONFIG.write_text(malformed)
                self.assertEqual(api.read_key(), 'legacy_key_' + 'x' * 25)
            with self.assertRaises(ValueError):
                api.save_key('invalid')
            key = 'synthetic_key_' + 'x' * 25
            api.save_key(key)
            self.assertEqual(api.read_key(), key)
            self.assertEqual(api.CONFIG.stat().st_mode & 0o777, 0o600)
            api.CONFIG.unlink()
            api.LEGACY_CONFIG.unlink()
            target = Path(folder) / 'target'
            target.write_text(json.dumps({'key': key}))
            api.CONFIG.symlink_to(target)
            self.assertEqual(api.read_key(), '')


if __name__ == '__main__':
    unittest.main()
