PREFIX ?= /usr/local
DESTDIR ?=
APPDIR = $(DESTDIR)$(PREFIX)/share/orbitz-youtube-desktop
.PHONY: install test
install:
	install -d "$(APPDIR)/app" "$(APPDIR)/i18n"
	install -m644 app/*.py app/index.html "$(APPDIR)/app/"
	install -m644 i18n/*.py i18n/*.json "$(APPDIR)/i18n/"
	install -Dm755 data/orbitz-youtube-desktop "$(DESTDIR)$(PREFIX)/bin/orbitz-youtube-desktop"
	install -Dm644 data/io.orbitz.YouTubeDesktop.desktop "$(DESTDIR)$(PREFIX)/share/applications/io.orbitz.YouTubeDesktop.desktop"
	install -Dm644 app/youtube.svg "$(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/io.orbitz.YouTubeDesktop.svg"
	install -Dm644 data/io.orbitz.YouTubeDesktop.metainfo.xml "$(DESTDIR)$(PREFIX)/share/metainfo/io.orbitz.YouTubeDesktop.metainfo.xml"
	install -Dm644 data/io.orbitz.YouTubeDesktop.gschema.xml "$(DESTDIR)$(PREFIX)/share/glib-2.0/schemas/io.orbitz.YouTubeDesktop.gschema.xml"
	install -Dm644 LICENSE "$(DESTDIR)$(PREFIX)/share/licenses/orbitz-youtube-desktop/LICENSE"
	glib-compile-schemas "$(DESTDIR)$(PREFIX)/share/glib-2.0/schemas"
test:
	GSETTINGS_BACKEND=memory python3 -m unittest discover -s tests -v
	@for test in tests/test_youtube_*.js; do node "$$test"; done
