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
assert.match(html, /api\('open-external',\{uri:link\.href\}\)/);
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
const nativeActions = [];
const document = { activeElement: nodes.get('settings'), addEventListener(type, handler) { listeners[type] = handler; } };
let failSave = false;
const context = vm.createContext({
  document,
  window: {},
  $: id => nodes.get(id),
  api: async (action, body) => { nativeActions.push({ action, body }); if (failSave && action === 'key') throw Error('Save failed'); return {}; },
  loadRecommendations() {},
  uiText(node, value) { node.textContent = value; }, uiErrorText(node, error) { node.textContent = error.message; },
  searchCurrentTab() {}, setTab() {},
  selected: 'abcdefghijk',
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
assert.deepEqual(nativeActions.at(-1), { action: 'open-external', body: { uri: 'https://www.orbit.zone' } }, 'orbit.zone uses the bounded local HTTP action');
nodes.get('copy-video-link').onclick().then(() => {
assert.deepEqual(nativeActions.at(-1), { action: 'copy-link', body: { uri: 'https://www.youtube.com/watch?v=abcdefghijk' } }, 'copy action sends only the selected YouTube URL');

nodes.get('settings').onclick();
assert.equal(nodes.get('config').hidden, false);
assert.deepEqual(nativeActions.at(-1), { action: 'window-state', body: { state: 'settings' } }, 'opening Settings sends a bounded window-size request');
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
assert.deepEqual(nativeActions.at(-1), { action: 'window-state', body: { state: 'panel' } }, 'opening search sends panel height');
nodes.get('settings').onclick();
assert.deepEqual(nativeActions.at(-1), { action: 'window-state', body: { state: 'panel' } }, 'Settings preserves an open search panel height');
nodes.get('config-close').onclick();
assert.deepEqual(nativeActions.at(-1), { action: 'window-state', body: { state: 'panel' } }, 'closing Settings restores the search panel target');
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
assert.deepEqual(nativeActions.at(-1), { action: 'window-state', body: { state: 'idle' } }, 'closing an empty search panel requests compact idle height');
nodes.get('screen').hidden = false;
nodes.get('discovery').hidden = false;
listeners.keydown({ key: 'Escape', preventDefault() {} });
assert.deepEqual(nativeActions.at(-1), { action: 'window-state', body: { state: 'player' } }, 'closing the panel preserves the expanded player layout');
nodes.get('settings').onclick();
assert.deepEqual(nativeActions.at(-1), { action: 'window-state', body: { state: 'player' } }, 'Settings preserves an active player height');
nodes.get('config-close').onclick();
assert.deepEqual(nativeActions.at(-1), { action: 'window-state', body: { state: 'player' } }, 'closing Settings restores the active player target');

console.log('OK: YouTube settings are a fixed accessible modal; search results open as an outside-dismissible dropdown.');
}).catch(error => { console.error(error); process.exitCode = 1; });
}).catch(error => { console.error(error); process.exitCode = 1; });
