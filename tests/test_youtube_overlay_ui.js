const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('app/index.html', 'utf8');
assert.match(html, /<header>[\s\S]*?<form id="search">[\s\S]*?<button id="settings"/);
assert.match(html, /<div id="discovery" hidden>[\s\S]*?id="results"[\s\S]*?id="view-tabs"/);
assert.match(html, /#discovery\{position:fixed/);
assert.match(html, /#discovery\[hidden\]\{display:none\}/);
assert.match(html, /<div id="config" class="modal-overlay" hidden role="dialog" aria-modal="true" aria-labelledby="config-title"/);
assert.match(html, /#config\.modal-overlay\{position:fixed/);
assert.match(html, /\.modal-body\{overflow-y:auto/);
assert.match(html, /#config select\{[^}]*appearance:none[^}]*background-color:#252d36[^}]*color:#eee/);
assert.match(html, /#config select option\{background-color:#252d36;color:#eee\}/);
assert.match(html, /button:focus,input:focus,select:focus\{outline:2px solid #77bff0\}/);
assert.match(html, /<a id="runner-brand" href="https:\/\/www\.orbit\.zone" target="_blank" rel="noopener">orbit\.zone<\/a>/);
assert.match(html, /#runner-brand\{position:absolute;right:14px;bottom:10px/);
assert.match(html, /messageHandlers\?\.orbitzOpenExternal/);
assert.match(html, /data-i18n-title="youtube\.copy_video_link"/);

const node = () => ({
  hidden: true, disabled: false, isConnected: true, offsetParent: {}, value: '', handlers: {}, attributes: {},
  focus() { document.activeElement = this; this.focused = true; },
  addEventListener(type, handler) { this.handlers[type] = handler; },
  setAttribute(key, value) { this.attributes[key] = value; },
  contains(target) { return this.children?.includes(target) || target === this; },
  querySelectorAll() { return focusables; },
});
const ids = ['settings', 'config', 'config-status', 'language', 'key', 'config-close', 'save', 'query', 'search', 'submit', 'discovery', 'screen', 'copy-video-link', 'player-action-status'];
const nodes = new Map(ids.map(id => [id, node()]));
const focusables = ['config-close', 'language', 'key', 'save', 'credential-link'].map(() => node());
nodes.get('config').contains = target => focusables.includes(target) || target === nodes.get('config');
nodes.get('config').querySelectorAll = () => focusables;
nodes.get('search').contains = target => target === nodes.get('query') || target === nodes.get('submit') || target === nodes.get('search');
nodes.get('discovery').contains = target => target === nodes.get('discovery') || target?.insideDiscovery === true;
nodes.get('config').hidden = true;
nodes.get('discovery').hidden = true;
const listeners = {};
const windowStates = [];
const externalRequests = [], copiedLinks = [];
const document = { activeElement: nodes.get('settings'), addEventListener(type, handler) { listeners[type] = handler; } };
let failSave = false;
const context = vm.createContext({
  document,
  window: { webkit: { messageHandlers: {
    orbitzWindow: { postMessage(state) { windowStates.push(state); } },
    orbitzOpenExternal: { postMessage(uri) { externalRequests.push(uri); } },
    orbitzCopyLink: { postMessage(uri) { copiedLinks.push(uri); } },
  } } },
  $: id => nodes.get(id),
  api: async () => { if (failSave) throw Error('Save failed'); return {}; },
  loadRecommendations() {},
  uiText(node, value) { node.textContent = value; }, uiErrorText(node, error) { node.textContent = error.message; },
  searchCurrentTab() {}, setTab() {},
  selected: 'abcdefghijk',
  bridgeToken: 'synthetic-token',
  uiLocale: 'pt-BR',
});
const start = html.indexOf("$('settings').onclick=()=>openSettings();");
const end = html.indexOf('function renderResults', start);
vm.runInContext(html.slice(start, end), context);
let externalClickPrevented = false;
listeners.click({
  target: { closest(selector) { assert.equal(selector, 'a[target="_blank"]'); return { href: 'https://www.orbit.zone' }; } },
  preventDefault() { externalClickPrevented = true; },
});
assert(externalClickPrevented, 'explicit outer links avoid WebKit popup routing');
assert.deepEqual(externalRequests, ['synthetic-token\nhttps://www.orbit.zone'], 'orbit.zone uses the authenticated native external-link bridge');
nodes.get('copy-video-link').onclick();
assert.deepEqual(copiedLinks, ['synthetic-token\nhttps://www.youtube.com/watch?v=abcdefghijk'], 'copy button authenticates its native clipboard bridge request');

nodes.get('settings').onclick();
assert.equal(nodes.get('config').hidden, false);
assert.equal(windowStates.at(-1), 'synthetic-token\nsettings', 'opening Settings sends an authenticated size request');
assert.equal(document.activeElement, nodes.get('key'), 'opening Settings focuses the API key field');
let prevented = false;
document.activeElement = focusables[focusables.length - 1];
listeners.keydown({ key: 'Tab', shiftKey: false, preventDefault() { prevented = true; } });
assert(prevented, 'Tab is trapped at the end of the modal');
assert.equal(document.activeElement, focusables[0]);
listeners.keydown({ key: 'Escape', preventDefault() {} });
assert.equal(nodes.get('config').hidden, true);
assert.equal(document.activeElement, nodes.get('settings'), 'closing restores focus to the opener');

nodes.get('settings').onclick();
nodes.get('save').onclick();
Promise.resolve().then(() => Promise.resolve()).then(() => {
  assert.equal(nodes.get('config').hidden, true, 'successful key save closes the modal');
  assert.equal(nodes.get('discovery').hidden, false, 'successful key save exposes status/results');
  nodes.get('settings').onclick();
  failSave = true;
  return nodes.get('save').onclick();
}).then(() => {
  assert.equal(nodes.get('config').hidden, false, 'failed key save leaves Settings open');
  assert.equal(nodes.get('config-status').hidden, false, 'save error is visible inside the modal');
  nodes.get('config-close').onclick();
  assert.equal(nodes.get('config').hidden, true);

nodes.get('query').handlers.focus();
assert.equal(nodes.get('discovery').hidden, false, 'search focus opens the dropdown');
assert.equal(windowStates.at(-1), 'synthetic-token\npanel', 'opening search sends authenticated panel height');
nodes.get('settings').onclick();
assert.equal(windowStates.at(-1), 'synthetic-token\npanel', 'Settings preserves an open search panel height');
nodes.get('config-close').onclick();
assert.equal(windowStates.at(-1), 'synthetic-token\npanel', 'closing Settings restores the search panel target');
listeners.pointerdown({ target: { insideDiscovery: true } });
assert.equal(nodes.get('discovery').hidden, false, 'interaction inside the dropdown keeps it open');
listeners.pointerdown({ target: {} });
assert.equal(nodes.get('discovery').hidden, true, 'an outside pointer interaction closes the dropdown');
nodes.get('discovery').hidden = false;
listeners.focusin({ target: {} });
assert.equal(nodes.get('discovery').hidden, true, 'keyboard focus outside closes the dropdown');
nodes.get('discovery').hidden = false;
listeners.keydown({ key: 'Escape', preventDefault() {} });
assert.equal(nodes.get('discovery').hidden, true, 'Escape closes the dropdown');
assert.equal(windowStates.at(-1), 'synthetic-token\nidle', 'closing an empty search panel requests authenticated compact idle height');
nodes.get('screen').hidden = false;
nodes.get('discovery').hidden = false;
listeners.keydown({ key: 'Escape', preventDefault() {} });
assert.equal(windowStates.at(-1), 'synthetic-token\nplayer', 'closing the panel preserves the authenticated expanded player layout');
nodes.get('settings').onclick();
assert.equal(windowStates.at(-1), 'synthetic-token\nplayer', 'Settings preserves an active player height');
nodes.get('config-close').onclick();
assert.equal(windowStates.at(-1), 'synthetic-token\nplayer', 'closing Settings restores the active player target');

console.log('OK: YouTube settings are a fixed accessible modal; search results open as an outside-dismissible dropdown.');
}).catch(error => { console.error(error); process.exitCode = 1; });
