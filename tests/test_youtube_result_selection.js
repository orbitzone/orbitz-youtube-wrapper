const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('app/index.html', 'utf8');
const start = html.indexOf('function renderResults(items)');
const end = html.indexOf('async function loadRecommendations', start);
assert(start >= 0 && end > start, 'result renderer is present');

const makeElement = tag => ({
  tag, children: [], append(...nodes) { this.children.push(...nodes); },
});
const results = { children: [], replaceChildren(...nodes) { this.children = nodes; }, append(node) { this.children.push(node); } };
const discovery = { hidden: false };
const actions = [];
const context = vm.createContext({
  document: { createElement: makeElement },
  $: id => id === 'results' ? results : discovery,
  uiPrune() {},
  uiRaw(node, value) { node.textContent = value; },
  closeDiscovery() { discovery.hidden = true; actions.push('close'); },
  play(id, title) { actions.push(['play', id, title]); },
});
vm.runInContext(html.slice(start, end), context);
vm.runInContext("renderResults([{id:'abcdefghijk',title:'Live result',channel:'Channel',thumbnail:'image'}])", context);
results.children[0].onclick();

assert.equal(discovery.hidden, true, 'selecting a result closes the overlay panel');
assert.deepEqual(actions, ['close', ['play', 'abcdefghijk', 'Live result']], 'the panel closes before playback starts');
console.log('OK: choosing a YouTube result closes the discovery panel before playback.');
