const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('app/index.html', 'utf8');
const tabsStart = html.indexOf("let activeTab='videos'");
const tabsEnd = html.indexOf('async function loadComments', tabsStart);
const recommendationsStart = html.indexOf('async function loadRecommendations', tabsEnd);
const recommendationsEnd = html.indexOf("$('query').addEventListener('input'", recommendationsStart);
const names = ['videos', 'shorts', 'live', 'podcasts', 'comments'];
const makeNode = () => ({
  hidden: false, value: '', disabled: false, tabIndex: -1, attributes: {},
  setAttribute(key, value) { this.attributes[key] = value; },
  replaceChildren() {},
});
const nodes = new Map(['results', 'comments', 'status', 'query', 'submit', 'comments-list', 'comments-more', 'comments-status', 'view-tabs', ...names.map(name => `${name}-tab`)].map(id => [id, makeNode()]));
let resolveRecommendations;
let rendered = 0;
const context = vm.createContext({
  $: id => nodes.get(id),
  api: () => new Promise(resolve => { resolveRecommendations = resolve; }),
  renderResults() { rendered++; }, uiPrune() {}, uiText(node, key) { node.status = key; }, uiErrorText() {},
  loadRecommendations() {}, loadComments() {}, searchCurrentTab() {}, play() {},
  setTimeout(callback) { callback(); return 1; }, clearTimeout() {},
});
vm.runInContext("let selected='',sequence=0;" + html.slice(tabsStart, tabsEnd) + html.slice(recommendationsStart, recommendationsEnd), context);

vm.runInContext("setTab('videos')", context);
assert.equal(typeof resolveRecommendations, 'function', 'the initial videos tab requests recommendations');
vm.runInContext("setTab('shorts')", context);
resolveRecommendations({ items: [{ id: 'stale' }] });
setImmediate(() => {
  assert.equal(rendered, 0, 'late recommendations cannot overwrite the selected Shorts tab');
  assert.equal(nodes.get('status').status, 'youtube.shorts_search_hint');
  console.log('OK: delayed recommendations are ignored after switching to another empty tab.');
});
