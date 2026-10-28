import importlib.util
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
YOUTUBE_DIR = ROOT / 'app'
sys.path.insert(0, str(YOUTUBE_DIR))
spec = importlib.util.spec_from_file_location('orbitz_youtube_wrapper', YOUTUBE_DIR / 'youtube-wrapper.py')
youtube_widget = importlib.util.module_from_spec(spec)
spec.loader.exec_module(youtube_widget)


class YouTubeWindowSizingTests(unittest.TestCase):
    def test_native_bridge_requires_the_current_session_token(self):
        payload = youtube_widget.bridge_payload
        self.assertEqual(payload('session-token\nsettings', 'session-token'), 'settings')
        for message in ('', 'settings', 'other-token\nsettings', '☃\nsettings',
                        'x' * 4097, 'session-token', None):
            self.assertIsNone(payload(message, 'session-token'))

    def test_flatpak_manifest_exposes_only_the_required_audio_socket(self):
        manifest = json.loads((ROOT / 'packaging/io.orbitz.YouTubeDesktop.json').read_text())
        permissions = manifest['finish-args']
        self.assertIn('--socket=pulseaudio', permissions)
        self.assertIn('--socket=x11', permissions)
        self.assertIn('--share=network', permissions)
        self.assertNotIn('--device=all', permissions)

    def test_flatpak_icon_has_square_canvas(self):
        icon = ET.parse(YOUTUBE_DIR / 'youtube.svg').getroot()
        self.assertEqual(icon.attrib['width'], icon.attrib['height'])
        view_box = icon.attrib['viewBox'].split()
        self.assertEqual(view_box[2], view_box[3])

    def test_external_link_bridge_rejects_untrusted_hosts_and_uri_forms(self):
        allowed = youtube_widget.is_allowed_external_uri
        for uri in (
            'https://www.youtube.com/watch?v=abcdefghijk',
            'https://www.orbit.zone/',
            'https://console.cloud.google.com/apis/credentials',
            'https://www.youtube.com:443/',
        ):
            self.assertTrue(allowed(uri), uri)
        for uri in (
            'https://attacker.example/',
            'https://www.youtube.com.attacker.example/',
            'https://www.youtube.com@attacker.example/',
            'https://user@www.youtube.com/',
            'https://www.youtube.com:444/',
            'https://www.youtube.com/redirect?q=https://attacker.example',
            'https://www.youtube.com/watch?v=abcdefghijk&feature=redirect',
            'https://console.cloud.google.com/redirect',
            'http://www.youtube.com/',
            'javascript:alert(1)',
            'not a URL',
        ):
            self.assertFalse(allowed(uri), uri)

    def test_idle_window_already_fits_four_search_results(self):
        height = youtube_widget.target_window_height
        self.assertEqual(height('idle', 1000), 520)
        self.assertEqual(height('settings', 1000), 320)
        self.assertLess(height('settings', 1000), height('idle', 1000))
        self.assertEqual(height('panel', 1000), height('idle', 1000))
        self.assertGreater(height('player', 1000), height('idle', 1000))

    def test_active_sizes_respect_workarea_with_a_small_monitor_floor(self):
        height = youtube_widget.target_window_height
        self.assertEqual(height('panel', 600), 520)
        self.assertEqual(height('panel', 500), 436)
        self.assertEqual(height('settings', 600), 320)
        self.assertEqual(height('player', 100), 96)
        self.assertEqual(height('player', 80), 80)

    def test_unknown_layout_state_is_rejected(self):
        with self.assertRaises(ValueError):
            youtube_widget.target_window_height('fullscreen', 1000)

    def test_manual_height_change_disables_auto_resize_but_programmatic_change_does_not(self):
        changed = youtube_widget.user_resized_from_target
        self.assertTrue(changed(500, 700))
        self.assertFalse(changed(700, 700))
        self.assertFalse(changed(500, 700, programmatic=True))

    def test_web_layout_stretches_idle_runner_and_grows_only_for_player(self):
        html = (YOUTUBE_DIR / 'index.html').read_text()
        self.assertIn('body{min-height:0;height:100%;display:flex;flex-direction:column;overflow:hidden}', html)
        self.assertIn('#screen{aspect-ratio:auto;height:clamp(220px,calc(100vh - 110px),2000px)', html)
        self.assertIn('#results button{align-items:center;min-height:80px}', html)
        self.assertIn("function windowLayoutState(){if(!$('config').hidden&&$('discovery').hidden&&$('screen').hidden)return 'settings';return $('discovery').hidden?($('screen').hidden?'idle':'player'):'panel'}", html)
        self.assertIn("const bridgeToken=location.pathname.split('/')[1]||''", html)
        self.assertIn("bridge.postMessage(bridgeToken+'\\n'+windowLayoutState())", html)
        self.assertIn("$('query').addEventListener('input',()=>{++sequence;$('submit').disabled=false;});", html)

    def test_youtube_iframe_fullscreen_is_enabled_in_webkit_and_handled_by_gtk(self):
        html = (YOUTUBE_DIR / 'index.html').read_text()
        source = (YOUTUBE_DIR / 'youtube-wrapper.py').read_text()
        self.assertIn("frame.allow='autoplay; encrypted-media; picture-in-picture; fullscreen';frame.allowFullscreen=true", html)
        self.assertIn("settings.set_property('enable-fullscreen',True)", source)
        self.assertNotIn("view.connect('enter-fullscreen'", source)
        self.assertNotIn("view.connect('leave-fullscreen'", source)
        self.assertIn("# Do not connect enter/leave-fullscreen: WebKit's default handlers", source)
        self.assertIn("content_manager.register_script_message_handler('orbitzOpenExternal')", source)
        self.assertIn("decision.ignore();return True", source)

    def test_copy_link_bridge_accepts_only_youtube_video_urls(self):
        html = (YOUTUBE_DIR / 'index.html').read_text()
        source = (YOUTUBE_DIR / 'youtube-wrapper.py').read_text()
        self.assertIn('id="copy-video-link" type="button" hidden', html)
        self.assertIn('header>button[hidden]{display:none}', html)
        self.assertNotIn('download-video', html)
        self.assertIn("onStateChange:event=>{$('copy-video-link').hidden=event.data!==1", html)
        self.assertIn("$('copy-video-link').hidden=true", html)
        self.assertIn("content_manager.register_script_message_handler('orbitzCopyLink')", source)
        self.assertIn("re.fullmatch(r'https://www\\.youtube\\.com/watch\\?v=[A-Za-z0-9_-]{11}',uri)", source)
        self.assertIn('clipboard.set_text(uri,-1)', source)

    def test_idle_runner_is_local_accessible_and_stops_when_playback_starts(self):
        html = (YOUTUBE_DIR / 'index.html').read_text()
        self.assertIn('<section id="runner"', html)
        self.assertIn('id="runner-canvas"', html)
        self.assertIn('function starterCacti()', html)
        self.assertIn('function resetObstacleSchedule()', html)
        self.assertIn('function scheduleNextObstacle()', html)
        self.assertIn('g.clusterRemaining=2+Math.floor(Math.random()*2)', html)
        self.assertIn('g.clusterAfterGroup=true', html)
        self.assertIn('(460-80*d)+Math.random()*(180-30*d)', html)
        self.assertIn('(100-20*d)+Math.random()*(50-10*d)', html)
        self.assertIn('g.obs=starterCacti()', html)
        self.assertIn('g.w*.45', html)
        self.assertIn('g.nextObstacleDistance=(340-40*g.difficulty)+Math.random()*(100-20*g.difficulty)', html)
        self.assertIn('g.obstacleDistance+=g.speed*dt', html)
        self.assertNotIn('Math.random()<dt*.58', html)
        self.assertIn('g.difficulty=Math.min(1,g.elapsed/120)', html)
        self.assertIn('g.speed=Math.min(560,250+g.score*.12+40*g.difficulty)', html)
        self.assertIn('(340-40*g.difficulty)+Math.random()*(100-20*g.difficulty)', html)
        self.assertIn('Math.random()<.55', html)
        self.assertIn('g.clusterRemaining=2+Math.floor(Math.random()*2)', html)
        self.assertIn('(100-20*d)+Math.random()*(50-10*d)', html)
        self.assertIn('(460-80*d)+Math.random()*(180-30*d)', html)
        self.assertIn("matchMedia('(prefers-reduced-motion: reduce)')", html)
        self.assertIn("requestAnimationFrame(tick)", html)
        self.assertIn('background:transparent', html)
        self.assertIn("ctx.createLinearGradient(x+5,y-68,x+54,y-5)", html)
        self.assertIn("ctx.fillStyle='#82c96c'", html)
        self.assertIn('Math.floor(g.score/2)%2', html)
        self.assertIn('Hand-drawn profile', html)
        self.assertIn('no projecting muzzle', html)
        self.assertIn('x+20,y-73+bob', html)
        self.assertIn('x+19,y-52+bob', html)
        self.assertIn('x+42,y-55+bob,4.1,5.5', html)
        self.assertIn('const armSwing=running?', html)
        self.assertIn('ctx.lineWidth=5;ctx.beginPath();if(running&&step)', html)
        self.assertIn('x+46,y-2', html)
        self.assertNotIn('arc(x+56+armSwing', html)
        self.assertNotIn("fillStyle='#a8f08b';ctx.beginPath();ctx.arc(x+", html)
        self.assertIn('function fireShot()', html)
        self.assertIn('g.fireTimer>=3', html)
        self.assertIn('g.bullets.push({x:sx,y:sy,vx,vy,life:2})', html)
        self.assertIn('g.explosions.push({x:hit.x+hit.w/2', html)
        self.assertIn('oldX-(o.x+g.speed*dt)<=o.w+6', html)
        self.assertIn('const p=Math.min(1,e.age/.42)', html)
        self.assertIn("ctx.fillStyle='#46515a'", html)
        jump_handler = html.split('function beginJump(e){', 1)[1].split('\nfunction finishJump', 1)[0]
        self.assertNotIn('fireShot()', jump_handler)
        self.assertIn('g.vy+=(g.jumpHeld?-420:1450)*dt', html)
        self.assertIn('g.vy=-350', html)
        self.assertIn('function finishJump(){if(!g.jumpHeld)return;g.jumpHeld=false;ensure()}', html)
        self.assertNotIn('held<140?', html)
        self.assertIn("document.addEventListener('keyup'", html)
        self.assertIn("document.addEventListener('pointerup'", html)
        self.assertIn('ctx.moveTo(x+20,y-11)', html)
        self.assertIn("if(oldH)g.y+=floor()-(oldH-34);else g.y=floor()", html)
        self.assertIn('g.speed*.34*dt', html)
        self.assertIn('g.speed*.045*dt', html)
        self.assertIn('started:false', html)
        self.assertIn("g.started&&!g.over&&!g.raf", html)
        self.assertIn("$('runner').hidden=true", html)
        self.assertIn('youtube.runner_help', html)

    def test_runner_focus_and_obstacle_types_preserve_game_rules(self):
        html = (YOUTUBE_DIR / 'index.html').read_text()
        self.assertNotIn('#runner-canvas:focus-visible', html)
        self.assertIn('function ufoReadyToSpawn(timeRemaining,activeCount){return timeRemaining<=0&&activeCount===0}', html)
        self.assertIn('ufoSpawnTimer:3', html)
        self.assertIn('ufoWasActive&&!g.ufos.length)g.ufoSpawnTimer=5', html)
        self.assertIn('else if(!g.ufos.length)g.ufoSpawnTimer-=dt', html)
        self.assertIn('before<2&&u.age>=2', html)
        self.assertIn('g.ufos=g.ufos.filter(u=>u.age<3)', html)
        self.assertIn('ufoReadyToSpawn(g.ufoSpawnTimer,g.ufos.length)', html)
        self.assertIn('nearestUfoCactus(g.obs,44+62)', html)
        self.assertIn('g.ufoLasers.push({x1:pose.x,y1:pose.y+8,x2:tx,y2:ty,age:0})', html)
        self.assertIn('ctx.rotate(p.tilt)', html)
        self.assertIn('ctx.drawImage(ufoSprite,-36,-18)', html)
        self.assertIn('now-g.last<1000/60', html)
        self.assertIn("api('runner-score',{})", html)
        self.assertIn("api('runner-score',{score:record})", html)
        self.assertIn("g.newRecord=isNewRunnerBest(record,g.best)", html)
        self.assertLess(html.index('g.newRecord=isNewRunnerBest(record,g.best)'), html.index("api('runner-score',{score:record})"))
        self.assertIn("uiTr('youtube.runner_new_record')", html)
        self.assertIn("roll<.16?'mosquito':roll<.43?'rock':'cactus'", html)
        self.assertIn("ctx.fillStyle='#33432f'", html)
        self.assertIn("if(o.type==='rock')", html)
        self.assertIn("roll<.16?'mosquito'", html)
        self.assertIn("altitude:type==='mosquito'?35:0", html)
        self.assertIn('function runnerHitsObstacle(obstacle,playerY,floorY)', html)
        self.assertIn('o.x-=g.speed*dt', html)

    def test_widget_requests_centered_initial_placement(self):
        source = (YOUTUBE_DIR / 'youtube-wrapper.py').read_text()
        self.assertIn('window.set_position(Gtk.WindowPosition.CENTER)', source)
        launcher = (ROOT / 'data' / 'orbitz-youtube-wrapper').read_text()
        self.assertIn('GDK_BACKEND=x11', launcher)
        self.assertIn('youtube-wrapper.py', launcher)


if __name__ == '__main__':
    unittest.main()
