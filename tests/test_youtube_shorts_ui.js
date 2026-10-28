const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('app/index.html', 'utf8');
const ui = html.split("let activeTab='videos'")[1].split("$('settings').onclick")[0];
const names = ['videos', 'shorts', 'live', 'podcasts', 'comments'];
const makeNode = () => ({
  hidden: false, tabIndex: -1, value: '', disabled: false, children: [], attributes: {},
  setAttribute(key, value) { this.attributes[key] = value; },
  replaceChildren(...children) { this.children = children; },
  append(child) { this.children.push(child); },
  focus() { this.focused = true; },
});
const nodes = new Map();
for (const id of [
  'results', 'comments', 'status', 'query', 'submit', 'comments-list', 'comments-more',
  'comments-status', 'view-tabs', 'search', ...names.map(name => `${name}-tab`),
]) nodes.set(id, makeNode());
nodes.get('query').value = 'Brasilia';
const requests = [];
const context = vm.createContext({
  $, api: async (action, body) => { requests.push({ action, body }); return { items: [] }; },
  videoId: () => '', renderResults() {}, uiPrune() {}, uiText(node, key) { node.uiKey = key; }, uiErrorText() {},
  loadRecommendations() {}, play() {},
});
function $(id) { return nodes.get(id); }
vm.runInContext("let selected='',sequence=0;let activeTab='videos'" + ui, context);

nodes.get('shorts-tab').onclick();
Promise.resolve().then(() => Promise.resolve()).then(() => {
  assert.equal(requests[0].action, 'search');
  assert.equal(requests[0].body.query, 'Brasilia');
  assert.equal(requests[0].body.mode, 'shorts');
  assert.equal(nodes.get('results').attributes['aria-labelledby'], 'shorts-tab');
  assert.equal(nodes.get('results').hidden, false);
  assert.equal(nodes.get('comments').hidden, true);
  assert.equal(nodes.get('status').hidden, false);
  assert.deepEqual(names.map(name => nodes.get(`${name}-tab`).tabIndex), [ -1, 0, -1, -1, -1 ]);

  nodes.get('query').value = '';
  nodes.get('live-tab').onclick();
  assert.equal(requests.length, 1, 'empty live query never requests unfiltered results');
  assert.equal(nodes.get('status').uiKey, 'youtube.live_search_hint');
  nodes.get('query').value = 'Brasilia';
  nodes.get('live-tab').onclick();
  return Promise.resolve().then(() => Promise.resolve());
}).then(() => {
  assert.equal(requests[1].action, 'search');
  assert.equal(requests[1].body.query, 'Brasilia');
  assert.equal(requests[1].body.mode, 'live');
  assert.equal(nodes.get('results').attributes['aria-labelledby'], 'live-tab');
  assert.deepEqual(names.map(name => nodes.get(`${name}-tab`).tabIndex), [ -1, -1, 0, -1, -1 ]);

  nodes.get('query').value = '';
  nodes.get('podcasts-tab').onclick();
  assert.equal(requests.length, 2, 'empty podcast query never requests generic results');
  assert.equal(nodes.get('status').uiKey, 'youtube.podcasts_search_hint');
  nodes.get('query').value = 'Brasilia';
  nodes.get('podcasts-tab').onclick();
  return Promise.resolve().then(() => Promise.resolve());
}).then(() => {
  assert.equal(requests[2].body.mode, 'podcasts');
  assert.equal(nodes.get('results').attributes['aria-labelledby'], 'podcasts-tab');
  assert.deepEqual(names.map(name => nodes.get(`${name}-tab`).tabIndex), [ -1, -1, -1, 0, -1 ]);

  let prevented = false;
  nodes.get('view-tabs').onkeydown({ key: 'ArrowDown', preventDefault() { prevented = true; } });
  assert(prevented);
  assert.equal(nodes.get('comments-tab').focused, true);
  assert.equal(nodes.get('comments-tab').attributes['aria-selected'], 'true');
  nodes.get('view-tabs').onkeydown({ key: 'Home', preventDefault() {} });
  assert.equal(nodes.get('videos-tab').focused, true);
  nodes.get('view-tabs').onkeydown({ key: 'End', preventDefault() {} });
  assert.equal(nodes.get('comments-tab').focused, true);
  console.log('OK: Shorts, Live and Podcasts send distinct modes; empty searches stay local; five-tab semantics and keyboard navigation hold.');
}).catch(error => { console.error(error); process.exitCode = 1; });

for (const locale of ['pt-BR', 'en-US']) {
  const catalog = JSON.parse(fs.readFileSync(`i18n/${locale}.json`, 'utf8'));
  assert.equal(catalog['youtube.shorts'], 'Shorts');
  assert(catalog['youtube.shorts_hint'].includes(locale === 'pt-BR' ? 'menos de 4 minutos' : 'under 4 minutes'));
  assert(catalog['youtube.shorts_search_hint'].includes(locale === 'pt-BR' ? 'Nem todos' : 'may not all'));
  assert.equal(catalog['youtube.live'], locale === 'pt-BR' ? 'Ao vivo' : 'Live');
  assert(catalog['youtube.live_search_hint'].includes(locale === 'pt-BR' ? 'transmissões ao vivo ativas' : 'active live broadcasts'));
  assert.equal(catalog['youtube.podcasts'], 'Podcasts');
  assert(catalog['youtube.podcasts_hint'].includes(locale === 'pt-BR' ? 'podcast' : 'podcast'));
  assert(catalog['youtube.podcasts_search_hint'].includes(locale === 'pt-BR' ? 'episódios de podcast' : 'podcast episodes'));
}
