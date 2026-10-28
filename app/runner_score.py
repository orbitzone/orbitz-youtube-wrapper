"""Persistent local high score for the Orbitz Runner mini game."""
import json
import os
from pathlib import Path
import secrets
import threading

CONFIG_ROOT = Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))
SCORE_FILE = CONFIG_ROOT/'orbitz-youtube-wrapper'/'runner.json'
MAX_SCORE = 2_147_483_647
_LOCK = threading.Lock()


def _read_best_score():
    try:
        fd = os.open(SCORE_FILE, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd) as stream:
            score = json.load(stream).get('best', 0)
        return score if type(score) is int and 0 <= score <= MAX_SCORE else 0
    except (OSError, ValueError, TypeError, AttributeError):
        return 0


def read_best_score():
    with _LOCK:
        return _read_best_score()


def save_best_score(score):
    if type(score) is not int or not 0 <= score <= MAX_SCORE:
        raise ValueError('Recorde inválido.')

    with _LOCK:
        current = _read_best_score()
        best = max(current, score)
        if best == current:
            return best

        SCORE_FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = SCORE_FILE.with_name('runner-' + secrets.token_hex(8) + '.tmp')
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(fd, 'w') as stream:
                os.fchmod(stream.fileno(), 0o600)
                json.dump({'best': best}, stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, SCORE_FILE)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
        return best
